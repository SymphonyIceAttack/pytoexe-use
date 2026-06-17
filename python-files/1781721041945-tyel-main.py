"""
Arzt Doku Assistent - FINAL v1.2 (mit GPU-Beschleunigung)
============================================================
Vollständig konfigurierte Hausarzt-Dokumentations-App mit:
- Whisper STT (lokal, tiny → large-v3) - CUDA für NVIDIA, CPU für andere
- Multi-Backend: Lokal (llama.cpp) + Ollama (Netzwerk mit Auto-Discovery)
- AUTOMATISCHE GPU-ERKENNUNG (NVIDIA/AMD/Intel via Vulkan + CUDA)
- Universal Reasoning Engine mit User-Override (100% zukunftssicher)
- Intelligente Reasoning-Filterung (Heuristik)
- BEIDE Textfelder editierbar (Transkript + strukturierte Doku)
- Pro_Medico JSON-Export (VOLL KONFIGURIERBAR, direkter Workflow)
- Clipboard-Fallback
- Material Design UI mit Light/Dark Theme
- Persistente Settings via QSettings

Build-Dependencies (Windows):
    pip install pynvml  # Für NVIDIA GPU-Detection

    # Vulkan SDK installieren: https://vulkan.lunarg.com/sdk/home#windows
    $env:CMAKE_ARGS="-DGGML_VULKAN=ON"
    $env:FORCE_CMAKE=1
    pip install --upgrade --force-reinstall llama-cpp-python --no-cache-dir

    pip install faster-whisper PyQt6 sounddevice numpy requests pyinstaller

Build-Befehl:
    pyinstaller --onefile --windowed --name "ArztDoku" main.py
"""

import sys
import threading
import gc
import time
import re
import warnings
import json
import os
import subprocess
import socket
import uuid
from pathlib import Path
from datetime import datetime
import numpy as np
import sounddevice as sd
import requests
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QPushButton,
                              QTextEdit, QWidget, QHBoxLayout, QLabel, QComboBox,
                              QFrame, QSizePolicy, QGraphicsDropShadowEffect,
                              QMessageBox, QSplitter, QFileDialog, QDialog,
                              QSlider, QSpinBox, QGroupBox, QFormLayout,
                              QScrollArea, QDoubleSpinBox, QPlainTextEdit, QCheckBox,
                              QLineEdit, QInputDialog)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QTimer, QSettings
from PyQt6.QtGui import QFont, QColor
from faster_whisper import WhisperModel
from llama_cpp import Llama

warnings.filterwarnings('ignore', message='.*n_ctx.*')

# ============================================================
# 🎮 GPU AUTO-DETECTION (NVIDIA/AMD/Intel)
# ============================================================
class GPUDetector:
    """Erkennt verfügbare GPUs und entscheidet das optimale Backend."""

    @staticmethod
    def detect_nvidia():
        """Prüft ob NVIDIA GPU mit CUDA verfügbar ist."""
        # Methode 1: pynvml (präzise)
        try:
            import pynvml
            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()
            pynvml.nvmlShutdown()
            return device_count > 0
        except ImportError:
            pass
        except Exception:
            return False

        # Methode 2: torch CUDA-Check (Fallback)
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            pass

        # Methode 3: Umgebungsvariablen/Prozess-Check
        try:
            result = subprocess.run(
                ['nvidia-smi'],
                capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except:
            pass

        return False

    @staticmethod
    def detect_vulkan():
        """Prüft ob Vulkan verfügbar ist (AMD, Intel, NVIDIA)."""
        # Methode 1: vulkaninfo CLI (am zuverlässigsten)
        try:
            result = subprocess.run(
                ['vulkaninfo', '--summary'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # Methode 2: Windows-spezifisch (vulkan-1.dll)
        if sys.platform == 'win32':
            try:
                import ctypes
                ctypes.WinDLL('vulkan-1.dll')
                return True
            except:
                pass

        # Methode 3: Linux/Mac - libvulkan
        else:
            try:
                import ctypes
                ctypes.CDLL('libvulkan.so.1')
                return True
            except:
                pass

        return False

    @staticmethod
    def get_nvidia_gpu_name():
        """Gibt den Namen der NVIDIA GPU zurück."""
        try:
            import pynvml
            pynvml.nvmlInit()
            if pynvml.nvmlDeviceGetCount() > 0:
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                name = pynvml.nvmlDeviceGetName(handle)
                if isinstance(name, bytes):
                    name = name.decode('utf-8')
                pynvml.nvmlShutdown()
                return name
        except:
            pass

        # Fallback: nvidia-smi parsen
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().split('\n')[0]
        except:
            pass

        return "NVIDIA GPU"

    @staticmethod
    def get_vulkan_gpu_name():
        """Gibt den Namen der Vulkan-GPU zurück."""
        try:
            result = subprocess.run(
                ['vulkaninfo', '--summary'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                # Parse deviceName aus Output
                for line in result.stdout.split('\n'):
                    if 'deviceName' in line:
                        return line.split('=')[-1].strip()
        except:
            pass
        return "Vulkan GPU"

    @staticmethod
    def get_gpu_info():
        """Gibt vollständige Info über erkannte GPUs zurück."""
        info = {
            'nvidia_cuda': False,
            'vulkan': False,
            'gpu_name': 'CPU',
            'gpu_vendor': 'None',
            'recommendation': 'cpu',
            'whisper_device': 'cpu',
            'whisper_compute': 'int8',
            'llm_gpu_layers': 0
        }

        # 1. NVIDIA CUDA prüfen
        if GPUDetector.detect_nvidia():
            info['nvidia_cuda'] = True
            info['gpu_name'] = GPUDetector.get_nvidia_gpu_name()
            info['gpu_vendor'] = 'NVIDIA'
            info['recommendation'] = 'cuda'
            info['whisper_device'] = 'cuda'
            info['whisper_compute'] = 'float16'
            info['llm_gpu_layers'] = -1  # Alle Layer auf GPU

        # 2. Vulkan prüfen (für AMD/Intel oder NVIDIA-Fallback)
        if GPUDetector.detect_vulkan():
            info['vulkan'] = True
            if not info['nvidia_cuda']:
                info['gpu_name'] = GPUDetector.get_vulkan_gpu_name()
                # Vendor aus Namen raten
                name_lower = info['gpu_name'].lower()
                if 'amd' in name_lower or 'radeon' in name_lower:
                    info['gpu_vendor'] = 'AMD'
                elif 'intel' in name_lower or 'arc' in name_lower or 'uhd' in name_lower:
                    info['gpu_vendor'] = 'Intel'
                else:
                    info['gpu_vendor'] = 'Vulkan'

                info['recommendation'] = 'vulkan'
                info['whisper_device'] = 'cpu'  # Whisper hat kein Vulkan
                info['whisper_compute'] = 'int8'
                info['llm_gpu_layers'] = -1  # Alle Layer auf GPU via Vulkan

        return info

# ============================================================
# MATERIAL DESIGN THEMES
# ============================================================
LIGHT_THEME = """
QMainWindow { background-color: #f8f9fa; }
QWidget#centralWidget { background-color: #f8f9fa; }
QLabel { color: #202124; font-family: 'Segoe UI', 'Roboto', sans-serif; }
QLabel#titleLabel { color: #1a73e8; font-size: 20px; font-weight: 600; }
QLabel#timerLabel { color: #202124; font-size: 24px; font-weight: 400; font-family: 'Roboto Mono', 'Consolas', monospace; }
QLabel#statusLabel { color: #5f6368; font-size: 11px; }
QLabel#cardTitle { color: #202124; font-size: 13px; font-weight: 600; margin-bottom: 4px; }
QLabel#recIndicator { color: #ea4335; font-size: 11px; font-weight: 600; }
QLabel#backendBadge { background-color: #e8f0fe; color: #1a73e8; border-radius: 4px; padding: 2px 8px; font-size: 11px; font-weight: 600; }
QLabel#backendBadgeOllama { background-color: #e6f4ea; color: #137333; border-radius: 4px; padding: 2px 8px; font-size: 11px; font-weight: 600; }
QLabel#backendBadgeOffline { background-color: #fce8e6; color: #c5221f; border-radius: 4px; padding: 2px 8px; font-size: 11px; font-weight: 600; }
QLabel#strategyBadge { background-color: #fef7e0; color: #b06000; border-radius: 4px; padding: 2px 8px; font-size: 11px; font-weight: 500; }
QLabel#strategyBadgeOverride { background-color: #fce8e6; color: #c5221f; border-radius: 4px; padding: 2px 8px; font-size: 11px; font-weight: 600; }
QLabel#gpuBadge { background-color: #e6f4ea; color: #137333; border-radius: 4px; padding: 2px 8px; font-size: 11px; font-weight: 600; }
QLabel#gpuBadgeCPU { background-color: #f1f3f4; color: #5f6368; border-radius: 4px; padding: 2px 8px; font-size: 11px; font-weight: 500; }
QTextEdit { background-color: #ffffff; color: #202124; border: 1px solid #dadce0; border-radius: 8px; padding: 16px; font-family: 'Segoe UI', 'Roboto', sans-serif; font-size: 14px; line-height: 1.6; selection-background-color: #1a73e8; }
QPlainTextEdit { background-color: #ffffff; color: #202124; border: 1px solid #dadce0; border-radius: 8px; padding: 12px; font-family: 'Consolas', monospace; font-size: 11px; }
QPushButton { background-color: #ffffff; color: #1a73e8; border: 1px solid #dadce0; border-radius: 20px; padding: 8px 20px; font-weight: 500; font-size: 13px; font-family: 'Segoe UI', 'Roboto', sans-serif; }
QPushButton:hover { background-color: #f1f3f4; border-color: #bdc1c6; }
QPushButton:pressed { background-color: #e8eaed; }
QPushButton:disabled { background-color: #f8f9fa; color: #9aa0a6; border-color: #e8eaed; }
QPushButton#primaryButton { background-color: #1a73e8; color: #ffffff; border: none; border-radius: 20px; padding: 10px 24px; font-size: 14px; font-weight: 500; }
QPushButton#primaryButton:hover { background-color: #1557b0; }
QPushButton#primaryButton:pressed { background-color: #174ea6; }
QPushButton#primaryButton[recording="true"] { background-color: #ea4335; }
QPushButton#primaryButton[recording="true"]:hover { background-color: #d33b2c; }
QPushButton#iconButton { background-color: transparent; border: none; border-radius: 50%; padding: 4px; min-width: 24px; min-height: 24px; max-width: 24px; max-height: 24px; font-size: 14px; }
QPushButton#iconButton:hover { background-color: #e8eaed; }
QPushButton#debugButton { background-color: #ffffff; color: #1a73e8; border: 1px solid #dadce0; border-radius: 8px; padding: 8px 16px; font-weight: 500; font-size: 12px; text-align: left; }
QPushButton#debugButton:hover { background-color: #f1f3f4; }
QComboBox { background-color: #ffffff; color: #202124; border: 1px solid #dadce0; border-radius: 8px; padding: 8px 12px; font-family: 'Segoe UI', 'Roboto', sans-serif; font-size: 13px; min-width: 200px; }
QComboBox:hover { border-color: #1a73e8; }
QComboBox::drop-down { border: none; width: 30px; }
QComboBox QAbstractItemView { background-color: #ffffff; color: #202124; border: 1px solid #dadce0; selection-background-color: #f1f3f4; selection-color: #1a73e8; outline: none; }
QFrame#headerCard { background-color: #ffffff; border-radius: 12px; padding: 12px 16px; }
QFrame#statusBar { background-color: #ffffff; border-top: 1px solid #dadce0; padding: 4px 8px; }
QSplitter::handle { background-color: #dadce0; }
QSplitter::handle:horizontal { width: 2px; }
QGroupBox { border: 1px solid #dadce0; border-radius: 8px; margin-top: 12px; padding-top: 16px; font-weight: 600; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
QCheckBox { color: #202124; font-size: 13px; spacing: 8px; }
QCheckBox::indicator { width: 18px; height: 18px; }
QLineEdit { background-color: #ffffff; color: #202124; border: 1px solid #dadce0; border-radius: 6px; padding: 6px 10px; font-size: 13px; font-family: 'Segoe UI', 'Roboto', sans-serif; }
QLineEdit:focus { border-color: #1a73e8; }
QLineEdit:disabled { background-color: #f1f3f4; color: #9aa0a6; }
"""

DARK_THEME = """
QMainWindow { background-color: #1f1f1f; }
QWidget#centralWidget { background-color: #1f1f1f; }
QLabel { color: #e8eaed; font-family: 'Segoe UI', 'Roboto', sans-serif; }
QLabel#titleLabel { color: #8ab4f8; font-size: 20px; font-weight: 600; }
QLabel#timerLabel { color: #e8eaed; font-size: 24px; font-weight: 400; font-family: 'Roboto Mono', 'Consolas', monospace; }
QLabel#statusLabel { color: #9aa0a6; font-size: 11px; }
QLabel#cardTitle { color: #e8eaed; font-size: 13px; font-weight: 600; margin-bottom: 4px; }
QLabel#recIndicator { color: #f28b82; font-size: 11px; font-weight: 600; }
QLabel#backendBadge { background-color: #1a3a5c; color: #8ab4f8; border-radius: 4px; padding: 2px 8px; font-size: 11px; font-weight: 600; }
QLabel#backendBadgeOllama { background-color: #1b3a2f; color: #81c995; border-radius: 4px; padding: 2px 8px; font-size: 11px; font-weight: 600; }
QLabel#backendBadgeOffline { background-color: #3c1f1e; color: #f28b82; border-radius: 4px; padding: 2px 8px; font-size: 11px; font-weight: 600; }
QLabel#strategyBadge { background-color: #3a2e10; color: #fdd663; border-radius: 4px; padding: 2px 8px; font-size: 11px; font-weight: 500; }
QLabel#strategyBadgeOverride { background-color: #3c1f1e; color: #f28b82; border-radius: 4px; padding: 2px 8px; font-size: 11px; font-weight: 600; }
QLabel#gpuBadge { background-color: #1b3a2f; color: #81c995; border-radius: 4px; padding: 2px 8px; font-size: 11px; font-weight: 600; }
QLabel#gpuBadgeCPU { background-color: #3c4043; color: #9aa0a6; border-radius: 4px; padding: 2px 8px; font-size: 11px; font-weight: 500; }
QTextEdit { background-color: #2d2d2d; color: #e8eaed; border: 1px solid #3c4043; border-radius: 8px; padding: 16px; font-family: 'Segoe UI', 'Roboto', sans-serif; font-size: 14px; line-height: 1.6; selection-background-color: #8ab4f8; }
QPlainTextEdit { background-color: #2d2d2d; color: #e8eaed; border: 1px solid #3c4043; border-radius: 8px; padding: 12px; font-family: 'Consolas', monospace; font-size: 11px; }
QPushButton { background-color: #2d2d2d; color: #8ab4f8; border: 1px solid #3c4043; border-radius: 20px; padding: 8px 20px; font-weight: 500; font-size: 13px; font-family: 'Segoe UI', 'Roboto', sans-serif; }
QPushButton:hover { background-color: #3c4043; }
QPushButton:pressed { background-color: #535353; }
QPushButton:disabled { background-color: #1f1f1f; color: #5f6368; border-color: #3c4043; }
QPushButton#primaryButton { background-color: #8ab4f8; color: #202124; border: none; border-radius: 20px; padding: 10px 24px; font-size: 14px; font-weight: 500; }
QPushButton#primaryButton:hover { background-color: #aecbfa; }
QPushButton#primaryButton:pressed { background-color: #d2e3fc; }
QPushButton#primaryButton[recording="true"] { background-color: #f28b82; color: #202124; }
QPushButton#primaryButton[recording="true"]:hover { background-color: #ee675c; }
QPushButton#iconButton { background-color: transparent; border: none; border-radius: 50%; padding: 4px; min-width: 24px; min-height: 24px; max-width: 24px; max-height: 24px; font-size: 14px; }
QPushButton#iconButton:hover { background-color: #3c4043; }
QPushButton#debugButton { background-color: #2d2d2d; color: #8ab4f8; border: 1px solid #3c4043; border-radius: 8px; padding: 8px 16px; font-weight: 500; font-size: 12px; text-align: left; }
QPushButton#debugButton:hover { background-color: #3c4043; }
QComboBox { background-color: #2d2d2d; color: #e8eaed; border: 1px solid #3c4043; border-radius: 8px; padding: 8px 12px; font-family: 'Segoe UI', 'Roboto', sans-serif; font-size: 13px; min-width: 200px; }
QComboBox:hover { border-color: #8ab4f8; }
QComboBox::drop-down { border: none; width: 30px; }
QComboBox QAbstractItemView { background-color: #2d2d2d; color: #e8eaed; border: 1px solid #3c4043; selection-background-color: #3c4043; selection-color: #8ab4f8; outline: none; }
QFrame#headerCard { background-color: #2d2d2d; border-radius: 12px; padding: 12px 16px; }
QFrame#statusBar { background-color: #2d2d2d; border-top: 1px solid #3c4043; padding: 4px 8px; }
QSplitter::handle { background-color: #3c4043; }
QSplitter::handle:horizontal { width: 2px; }
QGroupBox { border: 1px solid #3c4043; border-radius: 8px; margin-top: 12px; padding-top: 16px; font-weight: 600; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #8ab4f8; }
QCheckBox { color: #e8eaed; font-size: 13px; spacing: 8px; }
QCheckBox::indicator { width: 18px; height: 18px; }
QLineEdit { background-color: #2d2d2d; color: #e8eaed; border: 1px solid #3c4043; border-radius: 6px; padding: 6px 10px; font-size: 13px; font-family: 'Segoe UI', 'Roboto', sans-serif; }
QLineEdit:focus { border-color: #8ab4f8; }
QLineEdit:disabled { background-color: #1f1f1f; color: #5f6368; }
"""

DEFAULT_SYSTEM_PROMPT = """Du bist ein erfahrener medizinischer Dokumentationsassistent in einer deutschsprachigen Hausarztpraxis.

WICHTIGE REGELN:
- Antworte AUSSCHLIESSLICH AUF DEUTSCH.
- Verwende präzise medizinische Fachsprache.
- Keine englischen Begriffe, keine Übersetzungen.
- Keine Einleitungen, keine Erklärungen, kein Markdown (keine ** oder ###).

Deine Aufgabe: Verstehe den rohen, fehlerhaften Spracherkennungstext, rekonstruiere den medizinischen Sinn und formuliere ihn neu als professionelle hausärztliche Dokumentation.

Antworte NUR mit der strukturierten Dokumentation in exakt diesem Format (jede Überschrift gefolgt von einer Leerzeile und dem Text):

Anamnese:

[Vollständiger Anamnesetext auf Deutsch]

Befund:

[Vollständiger Befundtext auf Deutsch]

Diagnose:

[Diagnose(n) auf Deutsch]

Therapie:

[Therapieempfehlung auf Deutsch]"""

DEFAULT_PROMEDICO_MAPPING = [
    {'key': 'Anamnese',   'title': 'Anamnese',   'plnr': '', 'enabled': True},
    {'key': 'Befund',     'title': 'Befund',     'plnr': '', 'enabled': True},
    {'key': 'Diagnose',   'title': '',           'plnr': '', 'enabled': False},
    {'key': 'Therapie',   'title': 'Therapie',   'plnr': '', 'enabled': True},
    {'key': 'Prozedere',  'title': 'Prozedere',  'plnr': '', 'enabled': True},
    {'key': 'Medikation', 'title': 'Medikation', 'plnr': '', 'enabled': True},
]

# ============================================================
# 🧠 REASONING-STRATEGIE-ENGINE
# ============================================================
class ReasoningStrategies:
    MODEL_CATEGORIES = {
        'native_reasoner': ['qwen3', 'deepseek-r1', 'deepseek_r1', 'qwq', 'sky-t1', 't1-'],
        'cot_needed': ['gemma', 'llama', 'mistral', 'phi', 'nemotron', 'yi-', 'internlm', 'command-r'],
        'no_reasoning': ['tiny', '0.5b', '0.6b', '0.8b', '1b']
    }

    @classmethod
    def detect_model_type(cls, model_name):
        if not model_name:
            return 'unknown'
        name = model_name.lower()
        for keyword in cls.MODEL_CATEGORIES['native_reasoner']:
            if keyword in name:
                return 'native_reasoner'
        for keyword in cls.MODEL_CATEGORIES['cot_needed']:
            if keyword in name:
                return 'cot_needed'
        for keyword in cls.MODEL_CATEGORIES['no_reasoning']:
            if keyword in name:
                return 'no_reasoning'
        return 'unknown'

    @classmethod
    def get_effective_strategy(cls, model_name, strategy_override):
        if strategy_override == "💭 CoT erzwingen":
            return 'cot'
        elif strategy_override == "🧠 Nativ erzwingen":
            return 'native'
        elif strategy_override == "⚡ Deaktivieren":
            return 'none'

        model_type = cls.detect_model_type(model_name)
        if model_type == 'native_reasoner':
            return 'native'
        elif model_type == 'cot_needed':
            return 'cot'
        elif model_type == 'no_reasoning':
            return 'none'
        else:
            return 'cot'

    @classmethod
    def get_cot_injection(cls, effective_strategy, reasoning_mode):
        if reasoning_mode.startswith("Deaktiviert"):
            return ""
        if effective_strategy == 'none':
            return ""
        elif effective_strategy == 'native':
            if reasoning_mode.startswith("Intern") or reasoning_mode.startswith("Sichtbar"):
                return "/think\n\n"
            return ""
        elif effective_strategy == 'cot':
            if reasoning_mode.startswith("Intern") or reasoning_mode.startswith("Sichtbar"):
                return (
                    "WICHTIGE ANWEISUNG ZUM NACHDENKEN:\n"
                    "Bevor du die strukturierte Dokumentation erstellst, "
                    "denke gründlich über den medizinischen Text nach. "
                    "Analysiere die Symptome, ziehe Schlüsse und plane die Struktur.\n\n"
                    "Schreibe deine Überlegungen ZUERST in </think> Tags. "
                    "Sei dabei ausführlich und medizinisch präzise.\n\n"
                    "ERST NACH dem schließenden </think> Tag "
                    "folgt die eigentliche strukturierte Dokumentation.\n\n"
                    "Format:\n"
                    "</think>\n"
                    "[Deine ausführliche medizinische Analyse auf Deutsch]\n"
                    "</think>\n\n"
                    "Anamnese:\n\n"
                    "[...]\n\n"
                )
            return ""
        return ""

    @classmethod
    def get_display_text(cls, effective_strategy, is_override):
        if effective_strategy == 'native':
            text = "🧠 Nativ"
        elif effective_strategy == 'cot':
            text = "💭 CoT"
        else:
            text = "⚡ Kein"
        if is_override:
            text += " ⚙️"
        return text

# ============================================================
# OLLAMA CLIENT
# ============================================================
class OllamaClient:
    DEFAULT_PORT = 11434
    DISCOVERY_TIMEOUT = 1.0

    def __init__(self, host=None):
        self.host = host
        self.base_url = None
        self.available_models = []
        self.connected = False

    def set_host(self, host):
        if host and not host.startswith('http'):
            host = f"http://{host}"
        self.host = host
        self.base_url = host
        return self.test_connection()

    def test_connection(self):
        if not self.base_url:
            self.connected = False
            return False
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=3)
            if response.status_code == 200:
                self.connected = True
                return True
        except:
            pass
        self.connected = False
        return False

    def discover_local(self):
        candidates = [
            f"http://localhost:{self.DEFAULT_PORT}",
            f"http://127.0.0.1:{self.DEFAULT_PORT}",
        ]
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            own_ip = s.getsockname()[0]
            s.close()
            subnet = '.'.join(own_ip.split('.')[:3])
            for i in range(1, 21):
                ip = f"{subnet}.{i}"
                if ip != own_ip:
                    candidates.append(f"http://{ip}:{self.DEFAULT_PORT}")
        except:
            pass
        candidates.extend(["http://ollama.local:11434", "http://ollama:11434"])

        found_hosts = []
        for host in candidates:
            try:
                response = requests.get(f"{host}/api/tags", timeout=self.DISCOVERY_TIMEOUT)
                if response.status_code == 200:
                    found_hosts.append(host)
                    if len(found_hosts) >= 1:
                        break
            except:
                pass
        return found_hosts

    def list_models(self):
        if not self.connected or not self.base_url:
            return []
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                self.available_models = [m['name'] for m in models]
                return self.available_models
        except Exception as e:
            print(f"Fehler beim Abrufen der Modelle: {e}")
        return []

    def chat_completion(self, messages, model, temperature=0.4, top_p=0.92,
                       max_tokens=2048, n_ctx=4096):
        if not self.connected or not self.base_url:
            raise ConnectionError("Keine Verbindung")

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
                "num_predict": max_tokens,
                "num_ctx": n_ctx,
            }
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=300
            )
            if response.status_code != 200:
                raise Exception(f"Ollama Fehler: {response.status_code}")

            data = response.json()
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": data.get("message", {}).get("content", ""),
                    }
                }]
            }
        except requests.Timeout:
            raise Exception("Timeout")
        except requests.RequestException as e:
            raise Exception(f"Netzwerkfehler: {e}")

    def get_info(self):
        if not self.connected:
            return "Nicht verbunden"
        return f"Verbunden mit {self.base_url} ({len(self.available_models)} Modelle)"

# ============================================================
# 🎮 BACKEND MANAGER (MIT GPU-SUPPORT)
# ============================================================
class BackendManager:
    def __init__(self):
        self.local_model = None
        self.local_model_path = None
        self.ollama = OllamaClient()
        self.current_backend = None
        self.current_model_name = None
        # GPU-Detection beim Initialisieren
        print("🔍 Erkenne GPU...")
        self.gpu_info = GPUDetector.get_gpu_info()
        self._log_gpu_info()

    def _log_gpu_info(self):
        """Gibt GPU-Info beim Start aus."""
        gi = self.gpu_info
        print(f"  GPU: {gi['gpu_name']}")
        print(f"  Vendor: {gi['gpu_vendor']}")
        print(f"  NVIDIA CUDA: {'✅' if gi['nvidia_cuda'] else '❌'}")
        print(f"  Vulkan: {'✅' if gi['vulkan'] else '❌'}")
        print(f"  Empfehlung: {gi['recommendation'].upper()}")
        print(f"  Whisper: device={gi['whisper_device']}, compute={gi['whisper_compute']}")
        print(f"  LLM GPU-Layers: {gi['llm_gpu_layers']}")

    def load_local_model(self, model_path, n_ctx=4096, n_threads=8):
        """Lädt Modell mit automatischer GPU-Nutzung (Vulkan für alle, CUDA als Bonus)."""
        if self.local_model is not None:
            del self.local_model
            gc.collect()

        n_gpu_layers = self.gpu_info['llm_gpu_layers']

        try:
            self.local_model = Llama(
                model_path=model_path,
                n_ctx=n_ctx,
                n_threads=n_threads,
                n_gpu_layers=n_gpu_layers,  # 🔥 GPU-POWER!
                verbose=False
            )
            self.local_model_path = model_path
            self.current_backend = 'local'
            self.current_model_name = os.path.basename(model_path)

            if n_gpu_layers != 0:
                print(f"✅ LLM läuft auf GPU: {self.gpu_info['gpu_name']} (via {self.gpu_info['recommendation'].upper()})")
            else:
                print(f"⚠️ LLM läuft auf CPU (keine GPU erkannt)")

        except Exception as e:
            # Fallback auf CPU wenn GPU-Init fehlschlägt
            print(f"⚠️ GPU-Init fehlgeschlagen ({e}), fallback auf CPU")
            try:
                self.local_model = Llama(
                    model_path=model_path,
                    n_ctx=n_ctx,
                    n_threads=n_threads,
                    n_gpu_layers=0,
                    verbose=False
                )
                self.local_model_path = model_path
                self.current_backend = 'local'
                self.current_model_name = os.path.basename(model_path)
            except Exception as e2:
                raise RuntimeError(f"Modell konnte nicht geladen werden: {e2}")

    def connect_ollama(self, host):
        success = self.ollama.set_host(host)
        if success:
            self.ollama.list_models()
            self.current_backend = 'ollama'
            return True
        return False

    def discover_ollama(self):
        return self.ollama.discover_local()

    def chat(self, messages, temperature=0.4, top_p=0.92, max_tokens=2048, n_ctx=4096):
        if self.current_backend == 'ollama' and self.ollama.connected:
            try:
                return self.ollama.chat_completion(
                    messages=messages,
                    model=self.current_model_name,
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=max_tokens,
                    n_ctx=n_ctx
                )
            except Exception as e:
                if self.local_model is not None:
                    print(f"Ollama Fehler, Fallback: {e}")
                    self.current_backend = 'local'
                    self.current_model_name = os.path.basename(self.local_model_path)
                    return self._chat_local(messages, max_tokens, temperature, top_p)
                raise
        elif self.current_backend == 'local' and self.local_model is not None:
            return self._chat_local(messages, max_tokens, temperature, top_p)
        raise RuntimeError("Kein Backend konfiguriert")

    def _chat_local(self, messages, max_tokens, temperature, top_p):
        return self.local_model.create_chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stream=False
        )

# ============================================================
# REASONING FILTER
# ============================================================
class ReasoningFilter:
    REASONING_TAGS = [
        'think', 'thinking', 'thought', 'reasoning', 'reason',
        'denken', 'denkprozess', 'überlegung', 'ueberlegung',
        'internal', 'internal_thought', 'reflection',
        'system_thought', 'chain_of_thought', 'cot'
    ]

    MEDICAL_ANSWER_MARKERS = [
        r'\bAnamnese\s*:', r'\bBefund\s*:', r'\bDiagnose\s*:',
        r'\bTherapie\s*:', r'\bProzedere\s*:', r'\bMedikation\s*:',
        r'\bVerdachtsdiagnose\s*:', r'\bEpikrise\s*:',
        r'\bPatient(?:in)?\s+(?:berichtet|klagt|stellt sich vor)',
        r'\b(?:RR|Blutdruck)\s*\d+\s*/\s*\d+',
        r'\b\d+\s*(?:mmHg|mg|ml|°C|bpm|/min)\b',
        r'\b(?:Auskultation|Palpation|Inspektion)\b',
        r'\b(?:Herztöne|Lunge|Abdomen)\b',
    ]

    @classmethod
    def extract_and_clean(cls, text):
        if not text:
            return "", ""
        text = text.replace('&lt;', '<').replace('&gt;', '>')
        text = text.replace('&amp;', '&').replace('&quot;', '"')

        thinking_parts = []

        for tag in cls.REASONING_TAGS:
            pattern = rf'<{tag}>(.*?)</{tag}>'
            matches = re.findall(pattern, text, flags=re.IGNORECASE | re.DOTALL)
            if matches:
                thinking_parts.extend([m.strip() for m in matches if m.strip()])
                text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)

        for tag in cls.REASONING_TAGS:
            open_pattern = rf'<{tag}>'
            if re.search(open_pattern, text, flags=re.IGNORECASE):
                open_match = re.search(rf'<{tag}>([\s\S]*)', text, flags=re.IGNORECASE)
                if open_match:
                    potential_reasoning = open_match.group(1).strip()
                    earliest_marker_pos = len(potential_reasoning)
                    for marker in cls.MEDICAL_ANSWER_MARKERS:
                        match = re.search(marker, potential_reasoning, flags=re.IGNORECASE)
                        if match and match.start() < earliest_marker_pos:
                            earliest_marker_pos = match.start()
                    threshold = len(potential_reasoning) * 0.7
                    if earliest_marker_pos < threshold and earliest_marker_pos > 50:
                        actual_reasoning = potential_reasoning[:earliest_marker_pos].strip()
                        actual_answer = potential_reasoning[earliest_marker_pos:].strip()
                        if actual_reasoning:
                            thinking_parts.append(actual_reasoning)
                        text = re.sub(rf'<{tag}>[\s\S]*', actual_answer, text, flags=re.IGNORECASE)
                    else:
                        thinking_parts.append(potential_reasoning)
                        text = re.sub(rf'<{tag}>[\s\S]*', '', text, flags=re.IGNORECASE)

        for tag in cls.REASONING_TAGS:
            text = re.sub(rf'</{tag}>', '', text, flags=re.IGNORECASE)

        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'^\s*\n+', '', text)
        text = re.sub(r'^###\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)

        thinking_content = "\n\n---\n\n".join([t for t in thinking_parts if t])
        return text.strip(), thinking_content

    @classmethod
    def get_raw_diagnostic(cls, output_obj):
        diag = {
            "has_reasoning_content": False,
            "reasoning_content": "",
            "content": "",
            "full_message_structure": "",
            "message_keys": []
        }
        try:
            if 'choices' in output_obj and output_obj['choices']:
                choice = output_obj['choices'][0]
                message = choice.get('message', {})
                diag["message_keys"] = list(message.keys())
                diag["full_message_structure"] = json.dumps(list(message.keys()), indent=2)
                diag["content"] = message.get('content', '') or ''
                for key in ['reasoning_content', 'reasoning', 'thought', 'internal_thought']:
                    if key in message and message[key]:
                        diag["has_reasoning_content"] = True
                        diag["reasoning_content"] = message[key]
                        break
        except Exception as e:
            diag["error"] = str(e)
        return diag

# ============================================================
# 🏥 PRO_MEDICO EXPORTER
# ============================================================
class ProMedicoExporter:
    KNOWN_VERSIONS = ['1.0']

    @staticmethod
    def parse_documentation_sections(text):
        section_patterns = [
            'Anamnese', 'Befund', 'Diagnose', 'Diagnosen', 'Therapie',
            'Prozedere', 'Medikation', 'Epikrise', 'Verdachtsdiagnose'
        ]
        pattern = r'^(?:\*\*|###)?\s*(' + '|'.join(section_patterns) + r')\s*(?:\*\*)?:'

        lines = text.split('\n')
        sections = {}
        current_section = None
        current_content = []

        for line in lines:
            match = re.match(pattern, line.strip(), re.IGNORECASE)
            if match:
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = match.group(1)
                current_content = []
            elif current_section:
                current_content.append(line)

        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content).strip()

        if 'Diagnosen' in sections and 'Diagnose' not in sections:
            sections['Diagnose'] = sections.pop('Diagnosen')

        return sections

    @staticmethod
    def build_json(patient_id, sections_data, mapping, api_version="1.0"):
        sections = []
        exported_titles = []
        skipped_sections = []

        for section_key, content in sections_data.items():
            if not content.strip():
                continue

            mapping_entry = None
            for m in mapping:
                if m['key'].lower() == section_key.lower():
                    mapping_entry = m
                    break

            if not mapping_entry or not mapping_entry.get('enabled', False):
                skipped_sections.append(section_key)
                continue

            plnr = mapping_entry.get('plnr', '').strip()
            title = mapping_entry.get('title', '').strip()

            if not plnr and not title:
                skipped_sections.append(section_key)
                continue

            section_obj = {"content": content.strip()}

            if plnr:
                try:
                    section_obj["plnr"] = int(plnr)
                    exported_titles.append(f"{section_key} → plnr:{plnr}")
                except ValueError:
                    section_obj["title"] = title
                    exported_titles.append(f"{section_key} → {title} (plnr ungültig)")
            else:
                section_obj["title"] = title
                exported_titles.append(f"{section_key} → {title}")

            sections.append(section_obj)

        json_data = {
            "version": api_version,
            "patient_id": patient_id,
            "sections": sections
        }

        return json_data, exported_titles, skipped_sections

    @staticmethod
    def validate_json(json_data):
        errors = []

        if not isinstance(json_data, dict):
            errors.append("JSON muss ein Objekt sein")
            return False, errors, []

        if 'version' not in json_data:
            errors.append("Feld 'version' fehlt")
        elif not isinstance(json_data['version'], str):
            errors.append("'version' muss String sein")

        if 'patient_id' not in json_data:
            errors.append("Feld 'patient_id' fehlt")
        elif not isinstance(json_data['patient_id'], str):
            errors.append("'patient_id' muss String sein")
        elif not json_data['patient_id'].strip():
            errors.append("'patient_id' darf nicht leer sein")

        if 'sections' not in json_data:
            errors.append("Feld 'sections' fehlt")
        elif not isinstance(json_data['sections'], list):
            errors.append("'sections' muss Array sein")
        elif len(json_data['sections']) == 0:
            errors.append("'sections' muss mindestens einen Eintrag haben")
        else:
            for i, section in enumerate(json_data['sections']):
                if not isinstance(section, dict):
                    errors.append(f"Section {i}: Muss Objekt sein")
                    continue
                if 'content' not in section:
                    errors.append(f"Section {i}: 'content' fehlt")
                elif not section['content'].strip():
                    errors.append(f"Section {i}: 'content' ist leer")

                has_plnr = 'plnr' in section
                has_title = 'title' in section

                if not has_plnr and not has_title:
                    errors.append(f"Section {i}: 'plnr' ODER 'title' erforderlich")

                if has_plnr and not isinstance(section['plnr'], int):
                    errors.append(f"Section {i}: 'plnr' muss Integer sein")

                if has_title and not isinstance(section['title'], str):
                    errors.append(f"Section {i}: 'title' muss String sein")

        warnings = []
        if 'version' in json_data:
            if json_data['version'] not in ProMedicoExporter.KNOWN_VERSIONS:
                warnings.append(
                    f"Version '{json_data['version']}' ist nicht offiziell bekannt."
                )

        return len(errors) == 0, errors, warnings

    @staticmethod
    def write_json_file(json_data, import_dir, auto_create=False):
        is_valid, errors, warnings = ProMedicoExporter.validate_json(json_data)
        if not is_valid:
            raise ValueError("JSON-Validierung fehlgeschlagen:\n" + "\n".join(errors))

        import_path = Path(import_dir)

        if not import_path.exists():
            if auto_create:
                try:
                    import_path.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    raise PermissionError(f"Konnte Verzeichnis nicht erstellen: {e}")
            else:
                raise FileNotFoundError(f"Verzeichnis existiert nicht: {import_dir}")

        if not import_path.is_dir():
            raise NotADirectoryError(f"Pfad ist kein Verzeichnis: {import_dir}")

        filename = f"arzt_doku_{uuid.uuid4().hex[:8]}.json"
        filepath = import_path / filename

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
        except PermissionError:
            raise PermissionError(f"Keine Schreibrechte auf: {import_dir}")
        except Exception as e:
            raise IOError(f"Fehler beim Schreiben: {e}")

        return filepath, filename, warnings

# ============================================================
# DIAGNOSE-DIALOG
# ============================================================
class DiagnosisDialog(QDialog):
    def __init__(self, raw_output, cleaned_output, thinking, diagnostic_info, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔍 KI-Output Diagnose")
        self.resize(800, 700)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Vollständige Analyse der letzten KI-Antwort."))

        struct_label = QLabel("📋 Message-Struktur:")
        struct_label.setStyleSheet("font-weight: bold; font-size: 13px; margin-top: 8px;")
        layout.addWidget(struct_label)

        struct_text = QPlainTextEdit()
        struct_text.setReadOnly(True)
        struct_text.setMaximumHeight(80)
        struct_info = f"""Verfügbare Felder: {', '.join(diagnostic_info.get('message_keys', []))}
Has reasoning_content field: {diagnostic_info.get('has_reasoning_content', False)}"""
        struct_text.setPlainText(struct_info)
        layout.addWidget(struct_text)

        for label_text, content, height in [
            ("🧠 reasoning_content (API-Feld):", diagnostic_info.get('reasoning_content', '(leer)') or '(leer)', 120),
            ("🔎 Extrahiertes Reasoning:", thinking if thinking else '(kein Reasoning)', 120),
            ("✅ Finaler Output:", cleaned_output if cleaned_output else '(leer)', 200),
        ]:
            lbl = QLabel(label_text)
            lbl.setStyleSheet("font-weight: bold; font-size: 13px; margin-top: 8px;")
            layout.addWidget(lbl)
            txt = QPlainTextEdit()
            txt.setReadOnly(True)
            txt.setMaximumHeight(height)
            txt.setPlainText(content)
            layout.addWidget(txt)

        close_btn = QPushButton("Schließen")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

# ============================================================
# SETTINGS DIALOG (MIT GPU-INFO)
# ============================================================
class SettingsDialog(QDialog):
    def __init__(self, settings, parent_app=None):
        super().__init__(parent_app)
        self.setWindowTitle("⚙️ Einstellungen")
        self.resize(560, 980)
        self.settings = settings
        self.parent_app = parent_app

        layout = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # === 🎮 GPU INFO (NEU!) ===
        gpu_info_group = QGroupBox("🎮 GPU-Beschleunigung (automatisch erkannt)")
        gpu_info_layout = QVBoxLayout(gpu_info_group)

        if self.parent_app:
            gi = self.parent_app.backend_manager.gpu_info

            # Status-Emoji
            if gi['recommendation'] == 'cuda':
                status_icon = "🚀"
                status_text = "NVIDIA CUDA aktiv - maximale Performance"
            elif gi['recommendation'] == 'vulkan':
                status_icon = "⚡"
                status_text = f"Vulkan aktiv ({gi['gpu_vendor']}) - gute Performance"
            else:
                status_icon = "💻"
                status_text = "CPU-Modus - keine GPU erkannt"

            gpu_text = QLabel(
                f"{status_icon} <b>Status:</b> {status_text}<br><br>"
                f"<b>Erkannte GPU:</b> {gi['gpu_name']}<br>"
                f"<b>Hersteller:</b> {gi['gpu_vendor']}<br>"
                f"<b>NVIDIA CUDA:</b> {'✅ Verfügbar' if gi['nvidia_cuda'] else '❌ Nicht verfügbar'}<br>"
                f"<b>Vulkan (Universal):</b> {'✅ Verfügbar' if gi['vulkan'] else '❌ Nicht verfügbar'}<br><br>"
                f"<b>LLM-Backend:</b> {gi['recommendation'].upper()} ({gi['llm_gpu_layers']} GPU-Layers)<br>"
                f"<b>Whisper-Backend:</b> {gi['whisper_device'].upper()} ({gi['whisper_compute']})"
            )
            gpu_text.setWordWrap(True)
            gpu_text.setTextFormat(Qt.TextFormat.RichText)
            gpu_text.setStyleSheet("padding: 8px; background-color: #f1f3f4; border-radius: 4px;")
            gpu_info_layout.addWidget(gpu_text)

            help_lbl = QLabel(
                "ℹ️ <b>Unterstützte GPUs:</b><br>"
                "• <b>NVIDIA</b> (CUDA): Schnellste Option für LLM + Whisper<br>"
                "• <b>AMD</b> (Vulkan): Gute LLM-Performance, Whisper auf CPU<br>"
                "• <b>Intel Arc/iGPU</b> (Vulkan): Gute LLM-Performance, Whisper auf CPU<br><br>"
                "Die GPU wird <b>automatisch beim Start</b> erkannt und genutzt. "
                "Bei Problemen fällt die App automatisch auf CPU zurück."
            )
            help_lbl.setWordWrap(True)
            help_lbl.setStyleSheet("font-size: 11px; color: #5f6368; padding: 4px; margin-top: 4px;")
            help_lbl.setTextFormat(Qt.TextFormat.RichText)
            gpu_info_layout.addWidget(help_lbl)
        else:
            gpu_info_layout.addWidget(QLabel("Keine App-Referenz"))

        scroll_layout.addWidget(gpu_info_group)

        # === AKTUELLES MODELL INFO ===
        model_info_group = QGroupBox("🎯 Aktuelles Modell & Strategie")
        model_info_layout = QVBoxLayout(model_info_group)

        if self.parent_app:
            bm = self.parent_app.backend_manager
            model_name = bm.current_model_name or "Keins geladen"
            auto_type = ReasoningStrategies.detect_model_type(model_name)
            override = settings.value('reasoning_strategy', '🔄 Automatisch')
            effective = ReasoningStrategies.get_effective_strategy(model_name, override)
            is_override = override != "🔄 Automatisch"
            display = ReasoningStrategies.get_display_text(effective, is_override)

            info_text = QLabel(
                f"<b>Modell:</b> {model_name}<br>"
                f"<b>Erkannt:</b> {auto_type}<br>"
                f"<b>Aktiv:</b> {display}"
            )
            info_text.setWordWrap(True)
            model_info_layout.addWidget(info_text)

            help_map = {
                'native': "✅ Modell denkt nativ",
                'cot': "💡 Reasoning via Chain-of-Thought (User-Prompt)",
                'none': "⚡ Kein Reasoning aktiviert"
            }
            help_label = QLabel(help_map.get(effective, ""))
            help_label.setWordWrap(True)
            help_label.setStyleSheet("font-size: 11px; color: #5f6368; padding: 6px; background-color: #f1f3f4; border-radius: 4px; margin-top: 4px;")
            model_info_layout.addWidget(help_label)

        scroll_layout.addWidget(model_info_group)

        # === REASONING-STRATEGIE ===
        strategy_group = QGroupBox("🎲 Reasoning-Strategie")
        strategy_layout = QFormLayout(strategy_group)

        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems([
            "🔄 Automatisch", "💭 CoT erzwingen",
            "🧠 Nativ erzwingen", "⚡ Deaktivieren"
        ])
        current_strategy = settings.value('reasoning_strategy', '🔄 Automatisch')
        idx = self.strategy_combo.findText(current_strategy)
        if idx >= 0:
            self.strategy_combo.setCurrentIndex(idx)

        strategy_help = QLabel(
            "• 🔄 Automatisch: App erkennt Modelltyp (empfohlen)\n"
            "• 💭 CoT erzwingen: Für Gemma, Llama, Mistral, etc.\n"
            "• 🧠 Nativ erzwingen: Für Qwen3, DeepSeek-R1\n"
            "• ⚡ Deaktivieren: Schnellste Antwort"
        )
        strategy_help.setWordWrap(True)
        strategy_help.setStyleSheet("font-size: 11px; color: #5f6368; padding: 4px;")

        strategy_layout.addRow("Strategie:", self.strategy_combo)
        strategy_layout.addRow(strategy_help)
        scroll_layout.addWidget(strategy_group)

        # === OLLAMA BACKEND ===
        backend_group = QGroupBox("🌐 Netzwerk Backend (Ollama)")
        backend_layout = QVBoxLayout(backend_group)

        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("Server-URL:"))
        self.ollama_url_input = QComboBox()
        self.ollama_url_input.setEditable(True)
        current_url = settings.value('ollama_url', 'http://localhost:11434')
        self.ollama_url_input.addItem(current_url)
        url_history = settings.value('ollama_url_history', [])
        if isinstance(url_history, list):
            for url in url_history:
                if url and url != current_url and self.ollama_url_input.findText(url) == -1:
                    self.ollama_url_input.addItem(url)
        url_layout.addWidget(self.ollama_url_input, stretch=1)
        backend_layout.addLayout(url_layout)

        btn_layout = QHBoxLayout()
        self.btn_discover = QPushButton("🔍 Suchen")
        self.btn_discover.clicked.connect(self._discover_servers)
        btn_layout.addWidget(self.btn_discover)

        self.btn_connect = QPushButton("🔗 Verbinden")
        self.btn_connect.clicked.connect(self._connect_to_server)
        btn_layout.addWidget(self.btn_connect)

        self.btn_disconnect = QPushButton("⛔ Trennen")
        self.btn_disconnect.clicked.connect(self._disconnect_server)
        btn_layout.addWidget(self.btn_disconnect)
        backend_layout.addLayout(btn_layout)

        self.backend_status_label = QLabel("Status: Wird geladen...")
        self.backend_status_label.setStyleSheet("font-size: 11px; margin-top: 6px;")
        backend_layout.addWidget(self.backend_status_label)

        self._update_backend_status()
        scroll_layout.addWidget(backend_group)

        # === REASONING MODUS ===
        reasoning_group = QGroupBox("🧠 Reasoning-Modus")
        reasoning_layout = QFormLayout(reasoning_group)

        self.reasoning_combo = QComboBox()
        self.reasoning_combo.addItems([
            "Intern gefiltert (empfohlen)",
            "Deaktiviert (/no_think)",
            "Sichtbar (Thinking bleibt im Text)"
        ])
        current_reasoning = settings.value('reasoning_mode', 'Intern gefiltert (empfohlen)')
        idx = self.reasoning_combo.findText(current_reasoning)
        if idx >= 0:
            self.reasoning_combo.setCurrentIndex(idx)

        reasoning_help = QLabel(
            "• Intern gefiltert: Modell denkt, Output bleibt sauber\n"
            "• Deaktiviert: Kein Reasoning\n"
            "• Sichtbar: Thinking wird in Doku angezeigt"
        )
        reasoning_help.setWordWrap(True)
        reasoning_help.setStyleSheet("font-size: 11px; color: #5f6368; padding: 4px;")
        reasoning_layout.addRow("Modus:", self.reasoning_combo)
        reasoning_layout.addRow(reasoning_help)
        scroll_layout.addWidget(reasoning_group)

        # === KI-PARAMETER ===
        ai_group = QGroupBox("⚙️ KI-Parameter")
        ai_layout = QFormLayout(ai_group)

        self.temp_slider = QDoubleSpinBox()
        self.temp_slider.setRange(0.0, 2.0)
        self.temp_slider.setSingleStep(0.1)
        self.temp_slider.setDecimals(2)
        self.temp_slider.setValue(settings.value('temperature', 0.4, type=float))
        ai_layout.addRow("Temperature:", self.temp_slider)

        self.top_p_slider = QDoubleSpinBox()
        self.top_p_slider.setRange(0.0, 1.0)
        self.top_p_slider.setSingleStep(0.05)
        self.top_p_slider.setDecimals(2)
        self.top_p_slider.setValue(settings.value('top_p', 0.92, type=float))
        ai_layout.addRow("Top-P:", self.top_p_slider)

        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(256, 16384)
        self.max_tokens_spin.setSingleStep(256)
        self.max_tokens_spin.setValue(settings.value('max_tokens', 4096, type=int))
        ai_layout.addRow("Max. Tokens:", self.max_tokens_spin)

        self.n_ctx_spin = QSpinBox()
        self.n_ctx_spin.setRange(1024, 32768)
        self.n_ctx_spin.setSingleStep(512)
        self.n_ctx_spin.setValue(settings.value('n_ctx', 4096, type=int))
        ai_layout.addRow("Kontext (n_ctx):", self.n_ctx_spin)

        scroll_layout.addWidget(ai_group)

        # === WHISPER ===
        whisper_group = QGroupBox("🎤 Spracherkennung (Whisper)")
        whisper_layout = QFormLayout(whisper_group)

        self.whisper_combo = QComboBox()
        self.whisper_combo.addItems(["tiny", "base", "small", "medium", "large-v3"])
        current_whisper = settings.value('whisper_model', 'small')
        idx = self.whisper_combo.findText(current_whisper)
        if idx >= 0:
            self.whisper_combo.setCurrentIndex(idx)
        whisper_layout.addRow("Modell:", self.whisper_combo)

        self.beam_size_spin = QSpinBox()
        self.beam_size_spin.setRange(1, 10)
        self.beam_size_spin.setValue(settings.value('beam_size', 1, type=int))
        whisper_layout.addRow("Beam Size:", self.beam_size_spin)

        vad_active = settings.value('vad_filter', True, type=bool)
        self.vad_filter_check = QPushButton("✅" if vad_active else "❌")
        self.vad_filter_check.setCheckable(True)
        self.vad_filter_check.setChecked(vad_active)
        self.vad_filter_check.clicked.connect(lambda: self.vad_filter_check.setText("✅" if self.vad_filter_check.isChecked() else "❌"))
        whisper_layout.addRow("VAD-Filter:", self.vad_filter_check)

        scroll_layout.addWidget(whisper_group)

        # === 🏥 PRO_MEDICO INTEGRATION ===
        promedico_group = QGroupBox("🏥 Pro_Medico Integration (JSON-Import)")
        promedico_layout = QVBoxLayout(promedico_group)

        self.promedico_checkbox = QCheckBox("Pro_Medico JSON-Import aktivieren")
        self.promedico_checkbox.setChecked(settings.value('promedico_enabled', False, type=bool))
        self.promedico_checkbox.toggled.connect(self._toggle_promedico_settings)
        promedico_layout.addWidget(self.promedico_checkbox)

        dir_label = QLabel("📁 Import-Verzeichnis (in Pro_Medico konfiguriert):")
        dir_label.setStyleSheet("font-weight: bold; margin-top: 8px;")
        promedico_layout.addWidget(dir_label)

        dir_layout = QHBoxLayout()
        self.promedico_dir_input = QLineEdit()
        self.promedico_dir_input.setText(settings.value('promedico_import_dir', ''))
        self.promedico_dir_input.setPlaceholderText("z.B. C:\\Pro_Medico\\Import\\")
        dir_layout.addWidget(self.promedico_dir_input, stretch=1)

        self.btn_browse_dir = QPushButton("📁")
        self.btn_browse_dir.setMaximumWidth(40)
        self.btn_browse_dir.clicked.connect(self._browse_promedico_dir)
        dir_layout.addWidget(self.btn_browse_dir)
        promedico_layout.addLayout(dir_layout)

        self.promedico_auto_create = QCheckBox(
            "Import-Verzeichnis automatisch erstellen wenn nicht vorhanden"
        )
        self.promedico_auto_create.setChecked(settings.value('promedico_auto_create', False, type=bool))
        promedico_layout.addWidget(self.promedico_auto_create)

        version_label = QLabel("🔢 API-Version (Schnittstellen-Version):")
        version_label.setStyleSheet("font-weight: bold; margin-top: 12px;")
        promedico_layout.addWidget(version_label)

        version_layout = QHBoxLayout()
        self.promedico_version_input = QLineEdit()
        self.promedico_version_input.setText(settings.value('promedico_api_version', '1.0'))
        self.promedico_version_input.setPlaceholderText("1.0")
        self.promedico_version_input.setMaximumWidth(100)
        version_layout.addWidget(self.promedico_version_input)
        version_layout.addStretch()
        promedico_layout.addLayout(version_layout)

        version_help = QLabel(
            "ℹ️ <b>API-Version</b> der Pro_Medico Schnittstelle.<br>"
            "• <b>Aktuell (Stand 2026):</b> <code>1.0</code><br>"
            "• Ändere dies nur wenn Pro_Medico eine neue Version herausgibt"
        )
        version_help.setWordWrap(True)
        version_help.setStyleSheet("font-size: 11px; color: #5f6368; padding: 6px; background-color: #f1f3f4; border-radius: 4px; margin-top: 4px;")
        version_help.setTextFormat(Qt.TextFormat.RichText)
        promedico_layout.addWidget(version_help)

        patient_help = QLabel(
            "ℹ️ <b>Patienten-ID Format:</b><br>"
            "• Nur Patient: <code>43</code><br>"
            "• Patient + Schein: <code>43_12345</code><br>"
            "Die zuletzt verwendete ID wird automatisch vorgeschlagen."
        )
        patient_help.setWordWrap(True)
        patient_help.setStyleSheet("font-size: 11px; padding: 6px; background-color: #f1f3f4; border-radius: 4px; margin-top: 8px;")
        patient_help.setTextFormat(Qt.TextFormat.RichText)
        promedico_layout.addWidget(patient_help)

        mapping_header = QLabel("🔗 Section-Mapping (JSON-Felder pro Abschnitt):")
        mapping_header.setStyleSheet("font-weight: bold; margin-top: 12px;")
        promedico_layout.addWidget(mapping_header)

        mapping_help = QLabel(
            "Für jede Section: <b>title</b> (String) und optional <b>plnr</b> "
            "(Integer = Praxisleistungs-Nummer).<br>"
            "Wenn plnr gesetzt → hat Priorität. Wenn beide leer → wird nicht exportiert.<br>"
            "<b>title</b> muss exakt der Praxisleistung in Pro_Medico entsprechen."
        )
        mapping_help.setWordWrap(True)
        mapping_help.setStyleSheet("font-size: 11px; color: #5f6368; padding: 4px; margin-bottom: 8px;")
        promedico_layout.addWidget(mapping_help)

        current_mapping_json = settings.value('promedico_section_mapping', '')
        if current_mapping_json:
            try:
                current_mapping = json.loads(current_mapping_json)
            except:
                current_mapping = DEFAULT_PROMEDICO_MAPPING
        else:
            current_mapping = DEFAULT_PROMEDICO_MAPPING

        self.mapping_inputs = {}
        mapping_form = QFormLayout()
        mapping_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        for entry in current_mapping:
            key = entry['key']

            input_container = QWidget()
            input_layout = QHBoxLayout(input_container)
            input_layout.setContentsMargins(0, 0, 0, 0)
            input_layout.setSpacing(4)

            checkbox = QCheckBox()
            checkbox.setChecked(entry.get('enabled', True))
            checkbox.setMaximumWidth(20)
            input_layout.addWidget(checkbox)

            title_input = QLineEdit()
            title_input.setText(entry.get('title', ''))
            title_input.setPlaceholderText(f"title z.B. '{key}'")
            input_layout.addWidget(title_input, stretch=2)

            plnr_input = QLineEdit()
            plnr_input.setText(entry.get('plnr', ''))
            plnr_input.setPlaceholderText("plnr")
            plnr_input.setMaximumWidth(80)
            input_layout.addWidget(plnr_input, stretch=1)

            self.mapping_inputs[key] = {
                'checkbox': checkbox,
                'title': title_input,
                'plnr': plnr_input
            }

            mapping_form.addRow(f"{key}:", input_container)

        promedico_layout.addLayout(mapping_form)

        diagnose_warn = QLabel(
            "⚠️ <b>Diagnose:</b> Laut Pro_Medico-Dokumentation können Diagnosen und "
            "Ziffern <b>NICHT</b> importiert werden (standardmäßig deaktiviert)."
        )
        diagnose_warn.setWordWrap(True)
        diagnose_warn.setStyleSheet("font-size: 11px; color: #c5221f; padding: 6px; background-color: #fce8e6; border-radius: 4px; margin-top: 8px;")
        diagnose_warn.setTextFormat(Qt.TextFormat.RichText)
        promedico_layout.addWidget(diagnose_warn)

        pm_info = QLabel(
            "ℹ️ <b>Setup:</b><br>"
            "1. Pro_Medico: Terminal → Medizintechnik → Datei-Import → JSON-Import aktivieren<br>"
            "2. Import-Verzeichnis dort festlegen<br>"
            "3. <b>Pro_Medico neu starten</b><br>"
            "4. Hier gleiches Verzeichnis + Mapping eintragen<br>"
            "5. 📤 Button → Patient-ID eingeben → automatischer Import<br><br>"
            "ℹ️ <b>Doppelimport-Schutz:</b> Pro_Medico verschiebt importierte Dateien "
            "automatisch in ein Archiv."
        )
        pm_info.setWordWrap(True)
        pm_info.setStyleSheet("font-size: 11px; padding: 6px; background-color: #e8f0fe; border-radius: 4px; margin-top: 8px;")
        pm_info.setTextFormat(Qt.TextFormat.RichText)
        promedico_layout.addWidget(pm_info)

        is_enabled = self.promedico_checkbox.isChecked()
        self.promedico_dir_input.setEnabled(is_enabled)
        self.btn_browse_dir.setEnabled(is_enabled)
        self.promedico_auto_create.setEnabled(is_enabled)
        self.promedico_version_input.setEnabled(is_enabled)
        for inputs in self.mapping_inputs.values():
            inputs['checkbox'].setEnabled(is_enabled)
            inputs['title'].setEnabled(is_enabled)
            inputs['plnr'].setEnabled(is_enabled)

        scroll_layout.addWidget(promedico_group)

        # === SYSTEM PROMPT ===
        prompt_group = QGroupBox("📝 System Prompt")
        prompt_layout = QVBoxLayout(prompt_group)

        self.prompt_edit = QTextEdit()
        self.prompt_edit.setMinimumHeight(100)
        self.prompt_edit.setPlainText(settings.value('system_prompt', DEFAULT_SYSTEM_PROMPT))
        self.prompt_edit.setFont(QFont('Consolas', 10))
        prompt_layout.addWidget(self.prompt_edit)

        reset_btn = QPushButton("↩️ Auf Standard zurücksetzen")
        reset_btn.clicked.connect(lambda: self.prompt_edit.setPlainText(DEFAULT_SYSTEM_PROMPT))
        prompt_layout.addWidget(reset_btn)

        scroll_layout.addWidget(prompt_group)

        # === DEBUG-OPTIONEN ===
        debug_group = QGroupBox("🐛 Debug-Optionen")
        debug_layout = QVBoxLayout(debug_group)

        self.debug_checkbox = QCheckBox("RAW-Output loggen (debug_log.txt)")
        self.debug_checkbox.setChecked(settings.value('debug_mode', False, type=bool))
        debug_layout.addWidget(self.debug_checkbox)

        btn_reasoning = QPushButton("🧠  Letztes Reasoning anzeigen")
        btn_reasoning.setObjectName("debugButton")
        btn_reasoning.clicked.connect(self._show_parent_reasoning)
        debug_layout.addWidget(btn_reasoning)

        btn_diagnose = QPushButton("🔍  Diagnose-Fenster öffnen")
        btn_diagnose.setObjectName("debugButton")
        btn_diagnose.clicked.connect(self._show_parent_diagnosis)
        debug_layout.addWidget(btn_diagnose)

        btn_log = QPushButton("📋  Debug-Log öffnen")
        btn_log.setObjectName("debugButton")
        btn_log.clicked.connect(self._open_debug_log)
        debug_layout.addWidget(btn_log)

        scroll_layout.addWidget(debug_group)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # === ACTION BUTTONS ===
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Speichern & Schließen")
        save_btn.clicked.connect(self.save_and_close)
        save_btn.setDefault(True)
        cancel_btn = QPushButton("Abbrechen")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def _toggle_promedico_settings(self, enabled):
        self.promedico_dir_input.setEnabled(enabled)
        self.btn_browse_dir.setEnabled(enabled)
        self.promedico_auto_create.setEnabled(enabled)
        self.promedico_version_input.setEnabled(enabled)
        for inputs in self.mapping_inputs.values():
            inputs['checkbox'].setEnabled(enabled)
            inputs['title'].setEnabled(enabled)
            inputs['plnr'].setEnabled(enabled)

    def _browse_promedico_dir(self):
        dir_path = QFileDialog.getExistingDirectory(
            self, "Pro_Medico Import-Verzeichnis auswählen",
            self.promedico_dir_input.text() or ""
        )
        if dir_path:
            self.promedico_dir_input.setText(dir_path)

    def _update_backend_status(self):
        if not self.parent_app:
            return
        bm = self.parent_app.backend_manager
        if bm.current_backend == 'ollama' and bm.ollama.connected:
            info = bm.ollama.get_info()
            models = ', '.join(bm.ollama.available_models[:3])
            if len(bm.ollama.available_models) > 3:
                models += f" (+{len(bm.ollama.available_models)-3})"
            self.backend_status_label.setText(f"✅ {info}\nModelle: {models}")
            self.backend_status_label.setStyleSheet("font-size: 11px; margin-top: 6px; color: #137333;")
        elif bm.current_backend == 'local':
            self.backend_status_label.setText(f"🏠 Lokal: {bm.current_model_name or 'nicht geladen'}")
            self.backend_status_label.setStyleSheet("font-size: 11px; margin-top: 6px; color: #1a73e8;")
        else:
            self.backend_status_label.setText("⚠️ Kein Backend")
            self.backend_status_label.setStyleSheet("font-size: 11px; margin-top: 6px; color: #c5221f;")

    def _discover_servers(self):
        self.btn_discover.setEnabled(False)
        self.btn_discover.setText("🔍 Suche...")
        QApplication.processEvents()
        if self.parent_app:
            hosts = self.parent_app.backend_manager.discover_ollama()
            if hosts:
                for host in hosts:
                    if self.ollama_url_input.findText(host) == -1:
                        self.ollama_url_input.insertItem(0, host)
                self.ollama_url_input.setCurrentIndex(0)
                self.backend_status_label.setText(f"✅ {len(hosts)} Server gefunden")
                self.backend_status_label.setStyleSheet("font-size: 11px; margin-top: 6px; color: #137333;")
            else:
                self.backend_status_label.setText("❌ Keine Server gefunden")
                self.backend_status_label.setStyleSheet("font-size: 11px; margin-top: 6px; color: #c5221f;")
        self.btn_discover.setEnabled(True)
        self.btn_discover.setText("🔍 Suchen")

    def _connect_to_server(self):
        url = self.ollama_url_input.currentText().strip()
        if not url:
            QMessageBox.warning(self, "Fehler", "Bitte URL eingeben.")
            return
        self.btn_connect.setEnabled(False)
        QApplication.processEvents()
        if self.parent_app:
            success = self.parent_app.backend_manager.connect_ollama(url)
            if success:
                history = self.settings.value('ollama_url_history', [])
                if not isinstance(history, list):
                    history = []
                if url in history:
                    history.remove(url)
                history.insert(0, url)
                history = history[:5]
                self.settings.setValue('ollama_url_history', history)
                self.settings.setValue('ollama_url', url)
                self._update_backend_status()
                self.parent_app.refresh_model_combobox()
            else:
                QMessageBox.warning(self, "Fehler", f"Verbindung zu {url} fehlgeschlagen.")
                self.backend_status_label.setText("❌ Verbindung fehlgeschlagen")
                self.backend_status_label.setStyleSheet("font-size: 11px; margin-top: 6px; color: #c5221f;")
        self.btn_connect.setEnabled(True)

    def _disconnect_server(self):
        if self.parent_app:
            self.parent_app.backend_manager.ollama.connected = False
            self.parent_app.backend_manager.ollama.base_url = None
            if self.parent_app.backend_manager.local_model is not None:
                self.parent_app.backend_manager.current_backend = 'local'
                self.parent_app.backend_manager.current_model_name = os.path.basename(
                    self.parent_app.backend_manager.local_model_path
                )
            self._update_backend_status()
            self.parent_app.refresh_model_combobox()

    def _show_parent_reasoning(self):
        if self.parent_app:
            self.parent_app.show_thinking_popup(from_settings=True)

    def _show_parent_diagnosis(self):
        if self.parent_app:
            self.parent_app.show_diagnosis(from_settings=True)

    def _open_debug_log(self):
        if not self.parent_app:
            return
        log_path = self.parent_app.debug_log_path
        if not os.path.exists(log_path):
            QMessageBox.information(self, "Debug-Log", "Datei existiert noch nicht.")
            return
        try:
            if sys.platform == 'win32':
                os.startfile(log_path)
            elif sys.platform == 'darwin':
                subprocess.call(['open', log_path])
            else:
                subprocess.call(['xdg-open', log_path])
        except Exception as e:
            QMessageBox.warning(self, "Fehler", str(e))

    def save_and_close(self):
        self.settings.setValue('reasoning_strategy', self.strategy_combo.currentText())
        self.settings.setValue('ollama_url', self.ollama_url_input.currentText().strip())
        self.settings.setValue('reasoning_mode', self.reasoning_combo.currentText())

        self.settings.setValue('temperature', self.temp_slider.value())
        self.settings.setValue('top_p', self.top_p_slider.value())
        self.settings.setValue('max_tokens', self.max_tokens_spin.value())
        self.settings.setValue('n_ctx', self.n_ctx_spin.value())

        self.settings.setValue('whisper_model', self.whisper_combo.currentText())
        self.settings.setValue('beam_size', self.beam_size_spin.value())
        self.settings.setValue('vad_filter', self.vad_filter_check.isChecked())

        self.settings.setValue('system_prompt', self.prompt_edit.toPlainText())
        self.settings.setValue('debug_mode', self.debug_checkbox.isChecked())

        self.settings.setValue('promedico_enabled', self.promedico_checkbox.isChecked())
        self.settings.setValue('promedico_import_dir', self.promedico_dir_input.text().strip())
        self.settings.setValue('promedico_auto_create', self.promedico_auto_create.isChecked())
        self.settings.setValue('promedico_api_version', self.promedico_version_input.text().strip() or '1.0')

        mapping = []
        for key, inputs in self.mapping_inputs.items():
            mapping.append({
                'key': key,
                'title': inputs['title'].text().strip(),
                'plnr': inputs['plnr'].text().strip(),
                'enabled': inputs['checkbox'].isChecked()
            })
        self.settings.setValue('promedico_section_mapping', json.dumps(mapping, ensure_ascii=False))

        self.settings.sync()
        self.accept()

# ============================================================
# WORKER SIGNALS
# ============================================================
class WorkerSignals(QObject):
    status = pyqtSignal(str)
    result = pyqtSignal(str)
    live_transcript = pyqtSignal(str)
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal()

# ============================================================
# MAIN APPLICATION
# ============================================================
class ArztApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🏥 Arzt Doku Assistent")
        self.resize(1200, 750)

        self.app_dir = os.path.dirname(os.path.abspath(__file__))
        self.debug_log_path = os.path.join(self.app_dir, "debug_log.txt")

        self.settings = QSettings("HausarztApp", "ArztDoku")
        self.load_settings()

        self.is_dark_mode = self.settings.value('dark_mode', False, type=bool)
        self.setStyleSheet(DARK_THEME if self.is_dark_mode else LIGHT_THEME)

        self.signals = WorkerSignals()
        self.signals.status.connect(self.set_status)
        self.signals.result.connect(self.show_result)
        self.signals.live_transcript.connect(self.update_live_transcript)
        self.signals.recording_started.connect(self.on_recording_start)
        self.signals.recording_stopped.connect(self.on_recording_stop)

        self.is_recording = False
        self.audio_frames = []
        self.recording_start_time = 0
        self.paused_elapsed = 0

        # Backend Manager mit GPU-Detection initialisieren
        self.backend_manager = BackendManager()

        self.last_thinking = ""
        self.last_raw_output = ""
        self.last_cleaned_output = ""
        self.last_diagnostic = {}
        self.last_effective_strategy = "none"

        self.whisper = None

        self.setup_ui()

        self.stopwatch_timer = QTimer(self)
        self.stopwatch_timer.timeout.connect(self.update_stopwatch)

        self.set_status("Bereit. Initialisiere Backends...")
        self.initialize_backends()

    def load_settings(self):
        self.temperature = self.settings.value('temperature', 0.4, type=float)
        self.top_p = self.settings.value('top_p', 0.92, type=float)
        self.max_tokens = self.settings.value('max_tokens', 4096, type=int)
        self.n_ctx = self.settings.value('n_ctx', 4096, type=int)
        self.whisper_model = self.settings.value('whisper_model', 'small')
        self.beam_size = self.settings.value('beam_size', 1, type=int)
        self.vad_filter = self.settings.value('vad_filter', True, type=bool)
        self.system_prompt = self.settings.value('system_prompt', DEFAULT_SYSTEM_PROMPT)
        self.reasoning_mode = self.settings.value('reasoning_mode', 'Intern gefiltert (empfohlen)')
        self.reasoning_strategy = self.settings.value('reasoning_strategy', '🔄 Automatisch')
        self.debug_mode = self.settings.value('debug_mode', False, type=bool)
        self.ollama_url = self.settings.value('ollama_url', 'http://localhost:11434')

        self.promedico_enabled = self.settings.value('promedico_enabled', False, type=bool)
        self.promedico_import_dir = self.settings.value('promedico_import_dir', '')
        self.promedico_auto_create = self.settings.value('promedico_auto_create', False, type=bool)
        self.promedico_api_version = self.settings.value('promedico_api_version', '1.0')
        self.last_patient_id = self.settings.value('last_patient_id', '')

        mapping_json = self.settings.value('promedico_section_mapping', '')
        if mapping_json:
            try:
                self.promedico_mapping = json.loads(mapping_json)
            except:
                self.promedico_mapping = DEFAULT_PROMEDICO_MAPPING
        else:
            self.promedico_mapping = DEFAULT_PROMEDICO_MAPPING

    def setup_ui(self):
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # === HEADER ===
        header_card = QFrame()
        header_card.setObjectName("headerCard")
        self.add_shadow(header_card)
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(20, 12, 20, 12)
        header_layout.setSpacing(16)

        title = QLabel("🏥 Arzt Doku")
        title.setObjectName("titleLabel")
        header_layout.addWidget(title)
        header_layout.addSpacing(20)

        model_label = QLabel("Modell:")
        header_layout.addWidget(model_label)

        self.model_combo = QComboBox()
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
        header_layout.addWidget(self.model_combo, stretch=1)

        self.btn_load_model = QPushButton("📁 Lokal")
        self.btn_load_model.setToolTip("Lokales GGUF-Modell laden")
        self.btn_load_model.clicked.connect(self.load_custom_model)
        header_layout.addWidget(self.btn_load_model)

        header_layout.addStretch()

        # GPU-Badge (NEU!)
        self.gpu_badge = QLabel("💻")
        self.gpu_badge.setObjectName("gpuBadgeCPU")
        self.gpu_badge.setToolTip("GPU-Status")
        header_layout.addWidget(self.gpu_badge)
        header_layout.addSpacing(8)

        self.strategy_badge = QLabel("🔄")
        self.strategy_badge.setObjectName("strategyBadge")
        self.strategy_badge.setToolTip("Aktive Reasoning-Strategie")
        header_layout.addWidget(self.strategy_badge)
        header_layout.addSpacing(8)

        self.backend_badge = QLabel("Lokal")
        self.backend_badge.setObjectName("backendBadge")
        header_layout.addWidget(self.backend_badge)
        header_layout.addSpacing(8)

        self.rec_indicator = QLabel("")
        self.rec_indicator.setObjectName("recIndicator")
        header_layout.addWidget(self.rec_indicator)

        self.timer_label = QLabel("00:00")
        self.timer_label.setObjectName("timerLabel")
        header_layout.addWidget(self.timer_label)
        header_layout.addSpacing(12)

        self.btn_record = QPushButton("🎙️  Aufnahme")
        self.btn_record.setObjectName("primaryButton")
        self.btn_record.clicked.connect(self.toggle_recording)
        header_layout.addWidget(self.btn_record)
        header_layout.addSpacing(12)

        self.btn_theme = QPushButton("🌙" if not self.is_dark_mode else "☀️")
        self.btn_theme.setObjectName("iconButton")
        self.btn_theme.setToolTip("Theme wechseln")
        self.btn_theme.clicked.connect(self.toggle_theme)
        header_layout.addWidget(self.btn_theme)

        main_layout.addWidget(header_card)

        # === MAIN CONTENT ===
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 16, 20, 16)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)
        transcript_label = QLabel("📝 Transkript (editierbar)")
        transcript_label.setObjectName("cardTitle")
        left_layout.addWidget(transcript_label)
        self.text_live = QTextEdit()
        self.text_live.setReadOnly(False)
        self.text_live.setPlaceholderText(
            "Hier erscheint der Rohtext.\n"
            "Du kannst hier auch direkt Text eintippen.\n"
            "Danach auf '🧠 Neu strukturieren' klicken."
        )
        self.text_live.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        left_layout.addWidget(self.text_live, stretch=1)
        splitter.addWidget(left_panel)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)
        result_label = QLabel("✅ Strukturierte Dokumentation (editierbar)")
        result_label.setObjectName("cardTitle")
        right_layout.addWidget(result_label)
        self.text_result = QTextEdit()
        self.text_result.setReadOnly(False)
        self.text_result.setPlaceholderText(
            "Hier erscheint die strukturierte Doku.\n"
            "Du kannst den Text hier bearbeiten, löschen oder ergänzen,\n"
            "bevor du ihn an Pro_Medico sendest oder kopierst."
        )
        self.text_result.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        right_layout.addWidget(self.text_result, stretch=1)
        splitter.addWidget(right_panel)

        splitter.setSizes([480, 720])
        content_layout.addWidget(splitter, stretch=1)

        # === ACTION BUTTONS ===
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self.btn_restructure = QPushButton("🧠  Neu strukturieren")
        self.btn_restructure.setToolTip("Strukturiert den aktuellen Transkript-Inhalt")
        self.btn_restructure.clicked.connect(self.restructure_current_text)
        self.btn_restructure.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_restructure.setMinimumHeight(44)
        btn_row.addWidget(self.btn_restructure)

        self.btn_copy = QPushButton("📋  Kopieren")
        self.btn_copy.clicked.connect(self.copy_to_clipboard)
        self.btn_copy.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_copy.setMinimumHeight(44)
        btn_row.addWidget(self.btn_copy)

        self.btn_promedico = QPushButton("📤  Pro_Medico")
        self.btn_promedico.setToolTip("Dokumentation an Pro_Medico senden (JSON-Export)")
        self.btn_promedico.clicked.connect(self.export_to_promedico)
        self.btn_promedico.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_promedico.setMinimumHeight(44)
        btn_row.addWidget(self.btn_promedico)

        self.btn_clear = QPushButton("🗑️  Löschen")
        self.btn_clear.clicked.connect(self.clear_all)
        self.btn_clear.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_clear.setMinimumHeight(44)
        btn_row.addWidget(self.btn_clear)

        content_layout.addLayout(btn_row)
        main_layout.addWidget(content_widget, stretch=1)

        # === STATUS BAR ===
        self.status_bar = QFrame()
        self.status_bar.setObjectName("statusBar")
        status_layout = QHBoxLayout(self.status_bar)
        status_layout.setContentsMargins(8, 2, 8, 2)
        status_layout.setSpacing(6)

        self.status_label = QLabel("Bereit")
        self.status_label.setObjectName("statusLabel")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()

        self.btn_settings = QPushButton("⚙️")
        self.btn_settings.setObjectName("iconButton")
        self.btn_settings.setToolTip("Einstellungen öffnen")
        self.btn_settings.clicked.connect(self.open_settings)
        status_layout.addWidget(self.btn_settings)

        main_layout.addWidget(self.status_bar)

        # GPU-Badge initial aktualisieren
        self._update_gpu_badge()

    def _update_gpu_badge(self):
        """Aktualisiert den GPU-Badge im Header."""
        gi = self.backend_manager.gpu_info

        if gi['recommendation'] == 'cuda':
            self.gpu_badge.setText(f"🚀 {gi['gpu_vendor']}")
            self.gpu_badge.setObjectName("gpuBadge")
            tooltip = f"🚀 NVIDIA CUDA aktiv\nGPU: {gi['gpu_name']}\n\nLLM + Whisper auf GPU\nMaximale Performance!"
        elif gi['recommendation'] == 'vulkan':
            self.gpu_badge.setText(f"⚡ {gi['gpu_vendor']}")
            self.gpu_badge.setObjectName("gpuBadge")
            tooltip = f"⚡ Vulkan aktiv\nGPU: {gi['gpu_name']}\n\nLLM auf GPU, Whisper auf CPU\nGute Performance!"
        else:
            self.gpu_badge.setText("💻 CPU")
            self.gpu_badge.setObjectName("gpuBadgeCPU")
            tooltip = "💻 CPU-Modus\nKeine GPU erkannt\n\nFallback-Modus aktiv"

        self.gpu_badge.setToolTip(tooltip)
        self.gpu_badge.style().unpolish(self.gpu_badge)
        self.gpu_badge.style().polish(self.gpu_badge)

    def initialize_backends(self):
        self.load_whisper()

        default_local = "./SHODAN.gguf"
        if os.path.exists(default_local):
            try:
                self.backend_manager.load_local_model(default_local, n_ctx=self.n_ctx)
            except Exception as e:
                self.set_status(f"Lokales Modell Fehler: {e}")

        saved_url = self.ollama_url
        if saved_url:
            threading.Thread(target=self._auto_connect_ollama, args=(saved_url,), daemon=True).start()

        self.refresh_model_combobox()

    def _auto_connect_ollama(self, url):
        try:
            self.signals.status.emit(f"Versuche Ollama ({url})...")
            success = self.backend_manager.connect_ollama(url)
            if success:
                self.signals.status.emit(f"✅ Ollama verbunden: {url}")
            else:
                self.signals.status.emit("Ollama nicht erreichbar.")
            QTimer.singleShot(0, self.refresh_model_combobox)
        except Exception as e:
            self.signals.status.emit(f"Ollama-Fehler: {e}")

    def refresh_model_combobox(self):
        self.model_combo.blockSignals(True)
        current = self.model_combo.currentText()
        self.model_combo.clear()

        if self.backend_manager.local_model_path:
            local_name = f"🏠 {os.path.basename(self.backend_manager.local_model_path)} (Lokal)"
            self.model_combo.addItem(local_name, {"type": "local", "path": self.backend_manager.local_model_path})

        if self.backend_manager.ollama.connected and self.backend_manager.ollama.available_models:
            self.model_combo.addItem("── Ollama Server ──", {"type": "separator"})
            for model_name in self.backend_manager.ollama.available_models:
                display_name = f"🌐 {model_name} (Ollama)"
                self.model_combo.addItem(display_name, {"type": "ollama", "model": model_name})
        else:
            self.model_combo.addItem("── Ollama nicht verbunden ──", {"type": "separator"})

        if current:
            idx = self.model_combo.findText(current)
            if idx >= 0:
                self.model_combo.setCurrentIndex(idx)
            else:
                self.model_combo.setCurrentIndex(0)
        elif self.model_combo.count() > 0:
            self.model_combo.setCurrentIndex(0)

        self.model_combo.blockSignals(False)
        self._update_backend_badge()
        self.on_model_changed(self.model_combo.currentText())

    def _update_backend_badge(self):
        bm = self.backend_manager
        if bm.current_backend == 'ollama' and bm.ollama.connected:
            self.backend_badge.setText(f"🌐 {bm.current_model_name}")
            self.backend_badge.setObjectName("backendBadgeOllama")
        elif bm.current_backend == 'local' and bm.local_model is not None:
            self.backend_badge.setText(f"🏠 {bm.current_model_name}")
            self.backend_badge.setObjectName("backendBadge")
        else:
            self.backend_badge.setText("⚠️ Kein Backend")
            self.backend_badge.setObjectName("backendBadgeOffline")

        self.backend_badge.style().unpolish(self.backend_badge)
        self.backend_badge.style().polish(self.backend_badge)

        self._update_strategy_badge()

    def _update_strategy_badge(self):
        model_name = self.backend_manager.current_model_name or ""
        effective = ReasoningStrategies.get_effective_strategy(model_name, self.reasoning_strategy)
        self.last_effective_strategy = effective

        is_override = self.reasoning_strategy != "🔄 Automatisch"
        display = ReasoningStrategies.get_display_text(effective, is_override)

        self.strategy_badge.setText(display)

        if is_override:
            self.strategy_badge.setObjectName("strategyBadgeOverride")
            tooltip = f"Aktive Strategie: {display}\n\n⚠️ Manueller Override aktiv\nGewählt: {self.reasoning_strategy}\nErkannt: {ReasoningStrategies.detect_model_type(model_name)}"
        else:
            self.strategy_badge.setObjectName("strategyBadge")
            tooltip = f"Aktive Strategie: {display}\n\nAutomatisch erkannt: {ReasoningStrategies.detect_model_type(model_name)}"

        self.strategy_badge.setToolTip(tooltip)
        self.strategy_badge.style().unpolish(self.strategy_badge)
        self.strategy_badge.style().polish(self.strategy_badge)

    def on_model_changed(self, text):
        idx = self.model_combo.currentIndex()
        if idx < 0:
            return
        data = self.model_combo.itemData(idx)
        if not data or data.get('type') == 'separator':
            return

        if data['type'] == 'local':
            if self.backend_manager.local_model_path != data['path'] or self.backend_manager.local_model is None:
                self.set_status("Lade lokales Modell...")
                try:
                    self.backend_manager.load_local_model(data['path'], n_ctx=self.n_ctx)
                    self.set_status(f"✅ Bereit: {os.path.basename(data['path'])}")
                except Exception as e:
                    self.set_status(f"Fehler: {e}")
            else:
                self.backend_manager.current_backend = 'local'
                self.backend_manager.current_model_name = os.path.basename(data['path'])
                self.set_status(f"✅ Bereit: {os.path.basename(data['path'])}")

        elif data['type'] == 'ollama':
            if self.backend_manager.ollama.connected:
                self.backend_manager.current_backend = 'ollama'
                self.backend_manager.current_model_name = data['model']
                self.set_status(f"✅ Bereit: {data['model']} (Ollama)")
            else:
                self.set_status("⚠️ Ollama nicht verbunden.")

        self._update_backend_badge()

    def load_custom_model(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "GGUF-Modell auswählen", "",
            "GGUF Dateien (*.gguf);;Alle Dateien (*)"
        )
        if file_path:
            self.set_status(f"Lade {os.path.basename(file_path)}...")
            try:
                self.backend_manager.load_local_model(file_path, n_ctx=self.n_ctx)
                self.refresh_model_combobox()
                self.set_status(f"✅ Bereit: {os.path.basename(file_path)}")
            except Exception as e:
                self.set_status(f"Fehler: {e}")
                QMessageBox.critical(self, "Fehler", f"Fehler: {e}")

    def show_thinking_popup(self, from_settings=False):
        if not self.last_thinking:
            QMessageBox.information(self, "🧠 Kein Reasoning", "Kein Reasoning-Text gefunden.")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("🧠 Interner Denkprozess")
        dialog.resize(700, 500)
        layout = QVBoxLayout(dialog)
        text = QPlainTextEdit()
        text.setReadOnly(True)
        text.setPlainText(self.last_thinking)
        layout.addWidget(text)
        close_btn = QPushButton("Schließen")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        dialog.exec()

    def show_diagnosis(self, from_settings=False):
        if not self.last_raw_output:
            QMessageBox.information(self, "🔍 Keine Daten", "Noch keine Analyse durchgeführt.")
            return
        dialog = DiagnosisDialog(
            self.last_raw_output, self.last_cleaned_output,
            self.last_thinking, self.last_diagnostic, self
        )
        dialog.exec()

    def log_debug(self, content_text, reasoning_text, diagnostic_info):
        if not self.debug_mode:
            return
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            backend_info = f"{self.backend_manager.current_backend}:{self.backend_manager.current_model_name}"
            with open(self.debug_log_path, "a", encoding="utf-8") as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"[{timestamp}] Backend: {backend_info}\n")
                f.write(f"Strategie-Override: {self.reasoning_strategy}\n")
                f.write(f"Effektive Strategie: {self.last_effective_strategy}\n")
                f.write(f"Reasoning-Modus: {self.reasoning_mode}\n")
                f.write(f"Message-Felder: {', '.join(diagnostic_info.get('message_keys', []))}\n")
                f.write(f"Has reasoning_content: {diagnostic_info.get('has_reasoning_content', False)}\n")
                f.write(f"\n--- reasoning_content ---\n{diagnostic_info.get('reasoning_content', '')}\n")
                f.write(f"\n--- content (RAW) ---\n{content_text}\n")
                f.write(f"\n--- Extrahiertes Reasoning ---\n{reasoning_text}\n")
                f.write(f"{'='*80}\n\n")
        except Exception as e:
            print(f"Debug-Log Fehler: {e}")

    def open_settings(self):
        dialog = SettingsDialog(self.settings, parent_app=self)
        if dialog.exec():
            old_whisper = self.whisper_model
            old_n_ctx = self.n_ctx

            self.load_settings()

            if old_whisper != self.whisper_model:
                self.set_status(f"Whisper geändert. Lade {self.whisper_model}...")
                self.load_whisper()

            if old_n_ctx != self.n_ctx and self.backend_manager.local_model is not None:
                self.set_status("Kontext geändert...")
                try:
                    self.backend_manager.load_local_model(
                        self.backend_manager.local_model_path, n_ctx=self.n_ctx
                    )
                except Exception as e:
                    self.set_status(f"Fehler: {e}")

            self.refresh_model_combobox()
            self.set_status("✅ Einstellungen gespeichert.")

    def add_shadow(self, widget, blur=16, offset=3, alpha=25):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(blur)
        shadow.setColor(QColor(0, 0, 0, alpha))
        shadow.setOffset(0, offset)
        widget.setGraphicsEffect(shadow)

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.settings.setValue('dark_mode', self.is_dark_mode)
        if self.is_dark_mode:
            self.setStyleSheet(DARK_THEME)
            self.btn_theme.setText("☀️")
        else:
            self.setStyleSheet(LIGHT_THEME)
            self.btn_theme.setText("🌙")
        self.add_shadow(self.findChild(QFrame, "headerCard"))

    def load_whisper(self):
        """Lädt Whisper mit automatischer GPU/CPU-Wahl."""
        self.set_status(f"Lade Whisper ({self.whisper_model})...")
        if self.whisper is not None:
            del self.whisper
            gc.collect()

        # GPU-Info aus BackendManager holen
        gi = self.backend_manager.gpu_info
        device = gi['whisper_device']
        compute_type = gi['whisper_compute']

        try:
            self.whisper = WhisperModel(
                self.whisper_model,
                device=device,
                compute_type=compute_type,
                cpu_threads=8
            )
            if device == 'cuda':
                self.set_status(f"✅ Whisper auf CUDA ({self.whisper_model}, {compute_type})")
            else:
                self.set_status(f"Whisper auf CPU ({self.whisper_model}, {compute_type})")
        except Exception as e:
            # Fallback auf CPU wenn GPU fehlschlägt
            print(f"⚠️ Whisper GPU-Init fehlgeschlagen ({e}), fallback auf CPU")
            self.whisper = WhisperModel(
                self.whisper_model,
                device="cpu",
                compute_type="int8",
                cpu_threads=8
            )
            self.set_status(f"Whisper auf CPU ({self.whisper_model}, int8)")

    def format_time(self, seconds):
        return f"{int(seconds)//60:02d}:{int(seconds)%60:02d}"

    def update_stopwatch(self):
        if self.is_recording:
            self.timer_label.setText(self.format_time(
                self.paused_elapsed + (time.time() - self.recording_start_time)))

    def on_recording_start(self):
        self.btn_record.setText("⏹️  Stoppen")
        self.btn_record.setProperty("recording", True)
        self.btn_record.style().unpolish(self.btn_record)
        self.btn_record.style().polish(self.btn_record)
        self.text_live.clear()
        self.text_result.clear()
        self.rec_indicator.setText("● REC")
        self.recording_start_time = time.time()
        self.stopwatch_timer.start(100)

    def on_recording_stop(self):
        self.btn_record.setText("🎙️  Aufnahme")
        self.btn_record.setProperty("recording", False)
        self.btn_record.style().unpolish(self.btn_record)
        self.btn_record.style().polish(self.btn_record)
        self.stopwatch_timer.stop()
        self.paused_elapsed += (time.time() - self.recording_start_time)
        self.rec_indicator.setText("")

    def toggle_recording(self):
        if not self.is_recording:
            self.is_recording = True
            self.audio_frames = []
            self.signals.recording_started.emit()
            self.set_status("🔴 Aufnahme läuft...")
            threading.Thread(target=self.record_audio, daemon=True).start()
        else:
            self.is_recording = False
            self.signals.recording_stopped.emit()
            self.set_status("Verarbeite Audio...")

    def record_audio(self):
        def callback(indata, frames, time_status, status):
            if self.is_recording:
                self.audio_frames.append(indata.copy())
        try:
            with sd.InputStream(samplerate=16000, channels=1, dtype='float32',
                               blocksize=1600, callback=callback):
                while self.is_recording:
                    sd.sleep(100)
        except Exception as e:
            self.signals.status.emit(f"Audio-Fehler: {e}")
            self.is_recording = False
            self.signals.recording_stopped.emit()
            return
        threading.Thread(target=self.process_audio, daemon=True).start()

    def restructure_current_text(self):
        raw_text = self.text_live.toPlainText().strip()
        if not raw_text:
            self.set_status("⚠️ Kein Text.")
            QMessageBox.information(self, "Kein Text", "Das Transkript-Feld ist leer.")
            return
        self.btn_restructure.setEnabled(False)
        self.btn_restructure.setText("⏳ Strukturiere...")
        threading.Thread(
            target=self._run_restructure, args=(raw_text,), daemon=True
        ).start()

    def _build_messages(self, raw_text, source_label=""):
        model_info = self.backend_manager.current_model_name or "unbekannt"
        effective_strategy = ReasoningStrategies.get_effective_strategy(
            model_info, self.reasoning_strategy
        )
        self.last_effective_strategy = effective_strategy

        cot_injection = ReasoningStrategies.get_cot_injection(
            effective_strategy, self.reasoning_mode
        )

        base_user_prompt = f"""Roher Transkript-Text{source_label}:
{raw_text}

Rekonstruiere und strukturiere ihn frei. Antworte AUSSCHLIESSLICH AUF DEUTSCH. Verwende EXAKT dieses Format mit Leerzeile nach jeder Überschrift:

Anamnese:

[Hier den vollständigen Anamnesetext schreiben]

Befund:

[Hier den vollständigen Befundtext schreiben]

Diagnose:

[Hier die Diagnose(n) schreiben]

Therapie:

[Hier die Therapieempfehlung schreiben]"""

        if cot_injection:
            user_prompt = cot_injection + "\n" + base_user_prompt
        else:
            user_prompt = base_user_prompt

        effective_prompt = self.get_effective_system_prompt()

        return [
            {"role": "system", "content": effective_prompt},
            {"role": "user", "content": user_prompt}
        ]

    def _run_restructure(self, raw_text):
        try:
            backend_info = self.backend_manager.current_backend
            model_info = self.backend_manager.current_model_name or "unbekannt"
            effective = ReasoningStrategies.get_effective_strategy(model_info, self.reasoning_strategy)
            strategy_display = ReasoningStrategies.get_display_text(effective, self.reasoning_strategy != "🔄 Automatisch")
            self.signals.status.emit(f"🧠 Strukturiere ({model_info}, {strategy_display})...")

            messages = self._build_messages(raw_text)

            try:
                output = self.backend_manager.chat(
                    messages=messages, temperature=self.temperature,
                    top_p=self.top_p, max_tokens=self.max_tokens, n_ctx=self.n_ctx
                )
            except Exception as e:
                self.signals.status.emit(f"Backend-Fehler: {e}")
                return

            diagnostic_info = ReasoningFilter.get_raw_diagnostic(output)
            api_reasoning = diagnostic_info.get('reasoning_content', '') or ''
            content_text = diagnostic_info.get('content', '') or ''

            self.last_raw_output = content_text
            self.last_diagnostic = diagnostic_info

            if api_reasoning and api_reasoning.strip():
                final_text = content_text
                thinking_text = api_reasoning.strip()
                cleaned_content, extra_thinking = ReasoningFilter.extract_and_clean(content_text)
                if cleaned_content:
                    final_text = cleaned_content
                if extra_thinking:
                    thinking_text += "\n\n---\n\n" + extra_thinking
            else:
                final_text, thinking_text = ReasoningFilter.extract_and_clean(content_text)

            self.last_thinking = thinking_text
            self.last_cleaned_output = final_text
            self.log_debug(content_text, thinking_text, diagnostic_info)

            if self.reasoning_mode.startswith("Sichtbar") and thinking_text:
                display_text = f"🧠 REASONING:\n{thinking_text}\n\n{'='*50}\n\n📋 DOKUMENTATION:\n{final_text}"
            else:
                display_text = final_text

            del output
            gc.collect()

            self.signals.result.emit(display_text)
            self.signals.status.emit(f"✅ via {backend_info} abgeschlossen.")

        except Exception as e:
            self.signals.status.emit(f"Fehler: {e}")
            import traceback
            traceback.print_exc()
        finally:
            QTimer.singleShot(0, self._reset_restructure_button)

    def _reset_restructure_button(self):
        self.btn_restructure.setEnabled(True)
        self.btn_restructure.setText("🧠  Neu strukturieren")

    def get_effective_system_prompt(self):
        base_prompt = self.system_prompt
        if self.reasoning_mode.startswith("Deaktiviert"):
            return "/no_think\n\n" + base_prompt
        return base_prompt

    def process_audio(self):
        try:
            if not self.audio_frames:
                self.signals.status.emit("Keine Audio-Daten.")
                return

            self.signals.status.emit(f"Transkribiere ({self.whisper_model})...")
            audio_np = np.concatenate(self.audio_frames, axis=0).flatten()

            segments, _ = self.whisper.transcribe(
                audio_np, language="de", vad_filter=self.vad_filter,
                vad_parameters=dict(min_silence_duration_ms=500),
                beam_size=self.beam_size, word_timestamps=False
            )
            raw_text = "".join([s.text for s in segments]).strip()

            del audio_np, segments
            self.audio_frames = []
            gc.collect()

            if not raw_text:
                self.signals.status.emit("Kein Text erkannt.")
                return

            self.signals.live_transcript.emit(raw_text)

            backend_info = self.backend_manager.current_backend
            model_info = self.backend_manager.current_model_name or "unbekannt"
            effective = ReasoningStrategies.get_effective_strategy(model_info, self.reasoning_strategy)
            strategy_display = ReasoningStrategies.get_display_text(effective, self.reasoning_strategy != "🔄 Automatisch")
            self.signals.status.emit(f"Transkribiert. KI ({model_info}, {strategy_display}) strukturiert...")

            messages = self._build_messages(raw_text, source_label=" (fehlerhaft)")

            try:
                output = self.backend_manager.chat(
                    messages=messages, temperature=self.temperature,
                    top_p=self.top_p, max_tokens=self.max_tokens, n_ctx=self.n_ctx
                )
            except Exception as e:
                self.signals.status.emit(f"Backend-Fehler: {e}")
                return

            diagnostic_info = ReasoningFilter.get_raw_diagnostic(output)
            api_reasoning = diagnostic_info.get('reasoning_content', '') or ''
            content_text = diagnostic_info.get('content', '') or ''

            self.last_raw_output = content_text
            self.last_diagnostic = diagnostic_info

            if api_reasoning and api_reasoning.strip():
                final_text = content_text
                thinking_text = api_reasoning.strip()
                cleaned_content, extra_thinking = ReasoningFilter.extract_and_clean(content_text)
                if cleaned_content:
                    final_text = cleaned_content
                if extra_thinking:
                    thinking_text += "\n\n---\n\n" + extra_thinking
            else:
                final_text, thinking_text = ReasoningFilter.extract_and_clean(content_text)

            self.last_thinking = thinking_text
            self.last_cleaned_output = final_text
            self.log_debug(content_text, thinking_text, diagnostic_info)

            if self.reasoning_mode.startswith("Sichtbar") and thinking_text:
                display_text = f"🧠 REASONING:\n{thinking_text}\n\n{'='*50}\n\n📋 DOKUMENTATION:\n{final_text}"
            else:
                display_text = final_text

            del output
            gc.collect()

            self.signals.result.emit(display_text)

            if thinking_text:
                char_count = len(thinking_text)
                if self.reasoning_mode.startswith("Intern"):
                    self.signals.status.emit(f"✅ via {backend_info}. Reasoning ({char_count} Z.) gefiltert.")
                else:
                    self.signals.status.emit(f"✅ via {backend_info}.")
            else:
                self.signals.status.emit(f"✅ via {backend_info}.")

        except Exception as e:
            self.signals.status.emit(f"Fehler: {e}")
            import traceback
            traceback.print_exc()

    def update_live_transcript(self, text):
        current = self.text_live.toPlainText()
        if not current or text.startswith(current):
            self.text_live.setPlainText(text)

    def show_result(self, text):
        self.text_result.setPlainText(text)

    def set_status(self, text):
        self.status_label.setText(text)

    def copy_to_clipboard(self):
        text = self.text_result.toPlainText()
        if not text:
            self.set_status("Kein Text.")
            return
        if "📋 DOKUMENTATION:" in text:
            text = text.split("📋 DOKUMENTATION:", 1)[1].strip()
        QApplication.clipboard().setText(text)
        self.set_status("✓ In Zwischenablage kopiert.")

    # ============================================================
    # 🏥 PRO_MEDICO EXPORT
    # ============================================================
    def export_to_promedico(self):
        """Exportiert die strukturierte Dokumentation als JSON zu Pro_Medico."""

        if not self.promedico_enabled:
            response = QMessageBox.question(
                self, "Pro_Medico nicht konfiguriert",
                "Die Pro_Medico Integration ist noch nicht eingerichtet.\n\n"
                "Möchtest du jetzt die Einstellungen öffnen?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if response == QMessageBox.StandardButton.Yes:
                self.open_settings()
            return

        if not self.promedico_import_dir:
            QMessageBox.critical(
                self, "Kein Import-Verzeichnis",
                "Bitte konfiguriere das Import-Verzeichnis in den ⚙️ Einstellungen."
            )
            self.open_settings()
            return

        import_path = Path(self.promedico_import_dir)
        if not import_path.exists():
            if self.promedico_auto_create:
                try:
                    import_path.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    QMessageBox.critical(
                        self, "Verzeichnis konnte nicht erstellt werden",
                        f"Fehler: {e}"
                    )
                    return
            else:
                response = QMessageBox.question(
                    self, "Verzeichnis nicht gefunden",
                    f"Das Import-Verzeichnis existiert nicht:\n{self.promedico_import_dir}\n\n"
                    f"Möchtest du es jetzt erstellen?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if response == QMessageBox.StandardButton.Yes:
                    try:
                        import_path.mkdir(parents=True, exist_ok=True)
                    except Exception as e:
                        QMessageBox.critical(self, "Fehler", f"Konnte Verzeichnis nicht erstellen:\n{e}")
                        return
                else:
                    return

        text = self.text_result.toPlainText()
        if not text:
            QMessageBox.warning(self, "Kein Text", "Keine Dokumentation zum Exportieren.")
            return

        if "📋 DOKUMENTATION:" in text:
            text = text.split("📋 DOKUMENTATION:", 1)[1].strip()

        sections_data = ProMedicoExporter.parse_documentation_sections(text)

        if not sections_data:
            QMessageBox.warning(
                self, "Keine Abschnitte",
                "Konnte keine strukturierten Abschnitte erkennen.\n\n"
                "Stelle sicher dass die Doku Standard-Überschriften enthält."
            )
            return

        patient_id, ok = QInputDialog.getText(
            self,
            "Pro_Medico Export - Patienten-ID",
            "Bitte die Patienten-ID aus Pro_Medico eingeben:\n\n"
            "• Nur Patient: z.B. '43'\n"
            "• Patient + Schein: z.B. '43_12345'\n\n"
            "(ohne Schein-ID wird automatisch der Primärschein verwendet)",
            text=self.last_patient_id
        )

        if not ok or not patient_id.strip():
            return

        patient_id = patient_id.strip()

        try:
            json_data, exported_titles, skipped_sections = ProMedicoExporter.build_json(
                patient_id, sections_data, self.promedico_mapping,
                self.promedico_api_version
            )
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim JSON-Bau: {e}")
            return

        if not json_data['sections']:
            QMessageBox.warning(
                self, "Nichts zu exportieren",
                "Keine Abschnitte zum Exportieren konfiguriert.\n\n"
                "Überprüfe das Section-Mapping in den Einstellungen."
            )
            return

        is_valid, errors, warnings = ProMedicoExporter.validate_json(json_data)
        if not is_valid:
            QMessageBox.critical(
                self, "JSON-Validierung fehlgeschlagen",
                "Das generierte JSON ist nicht valide:\n\n" + "\n".join(errors)
            )
            return

        try:
            filepath, filename, write_warnings = ProMedicoExporter.write_json_file(
                json_data, self.promedico_import_dir, auto_create=self.promedico_auto_create
            )
        except PermissionError:
            QMessageBox.critical(
                self, "Keine Schreibrechte",
                f"Keine Schreibrechte auf:\n{self.promedico_import_dir}"
            )
            return
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Schreiben: {e}")
            return

        self.last_patient_id = patient_id
        self.settings.setValue('last_patient_id', patient_id)

        success_msg = (
            f"✅ <b>Dokumentation erfolgreich an Pro_Medico gesendet!</b><br><br>"
            f"📁 <b>Datei:</b> {filename}<br>"
            f"👤 <b>Patient:</b> {patient_id}<br>"
            f"🔢 <b>API-Version:</b> {self.promedico_api_version}<br>"
            f"📝 <b>Exportierte Abschnitte:</b><br>"
        )
        for title in exported_titles:
            success_msg += f"&nbsp;&nbsp;&nbsp;• {title}<br>"

        success_msg += (
            f"<br>Pro_Medico importiert die Daten innerhalb weniger Sekunden automatisch.<br>"
            f"Protokoll: <i>Sys → Intern → Protokolle → Datei-Import</i>"
        )

        if skipped_sections:
            success_msg += f"<br><br>⚠️ <b>Nicht exportiert:</b> {', '.join(skipped_sections)}"
            if 'Diagnose' in skipped_sections:
                success_msg += "<br>📋 Bitte <b>Diagnose manuell</b> in Pro_Medico eingeben."

        QMessageBox.information(self, "✅ Export erfolgreich", success_msg)
        self.set_status(f"✅ An Pro_Medico gesendet (Patient {patient_id}, v{self.promedico_api_version})")

    def clear_all(self):
        if self.is_recording:
            self.toggle_recording()
        self.text_live.clear()
        self.text_result.clear()
        self.paused_elapsed = 0
        self.timer_label.setText("00:00")
        self.audio_frames = []
        self.last_thinking = ""
        self.last_raw_output = ""
        self.last_cleaned_output = ""
        self.last_diagnostic = {}
        gc.collect()
        self.set_status("Alles gelöscht.")

# ============================================================
# ENTRY POINT
# ============================================================
def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = ArztApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
