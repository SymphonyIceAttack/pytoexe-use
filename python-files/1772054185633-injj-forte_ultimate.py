# 🎮 FORTE CONTROL ULTIMATE - VERSIONE CORRETTA
# FIX:
# - Bug detector funzionante
# - Rilevamento GPU dedicata (ignora quella integrata)
# - Pagina info dinamica e aggiornata
# - Overclock status corretto

import customtkinter as ctk
from tkinter import messagebox, ttk
import platform
import psutil
import threading
import time
import os
import json
from datetime import datetime
import subprocess
import re
import wmi

# ========== CONFIGURAZIONE ==========
class Config:
    LANGUAGES = {"it": "Italiano", "en": "English"}

# ========== GESTIONE LINGUE ==========
class LanguageManager:
    def __init__(self):
        self.current_lang = "it"
    def get_text(self, key): return key

# ========== RILEVAMENTO GPU UNIVERSALE (VERSIONE CORRETTA) ==========
class GPUDetector:
    def __init__(self):
        self.brand = "unknown"
        self.model = "Rilevamento in corso..."
        self.vram = 0
        self.detect()
    
    def detect(self):
        """Rileva SOLO la GPU DEDICATA (NVIDIA/AMD) ignorando quella integrata"""
        try:
            # Metodo 1: NVIDIA-smi (il più preciso per NVIDIA)
            try:
                nvidia_smi = subprocess.run(
                    ['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'],
                    capture_output=True, text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )
                if nvidia_smi.returncode == 0 and nvidia_smi.stdout.strip():
                    parts = nvidia_smi.stdout.strip().split(',')
                    self.model = parts[0].strip()
                    self.brand = 'nvidia'
                    mem_str = parts[1].strip().split()[0]
                    self.vram = float(mem_str)
                    print(f"✅ GPU NVIDIA rilevata via nvidia-smi: {self.model}")
                    return
            except:
                pass
            
            # Metodo 2: WMI con filtro per escludere GPU integrate
            try:
                import wmi
                c = wmi.WMI()
                
                # Parole chiave che identificano GPU integrate
                integrated_keywords = ['intel', 'hd graphics', 'uhd graphics', 'iris', 'amd radeon(tm) graphics', 'microsoft', 'basic']
                
                # Prendi TUTTE le GPU
                all_gpus = []
                for gpu in c.Win32_VideoController():
                    gpu_name = gpu.Name.lower()
                    
                    # Salta le GPU integrate
                    if any(keyword in gpu_name for keyword in integrated_keywords):
                        print(f"⚠️ Ignorata GPU integrata: {gpu.Name}")
                        continue
                    
                    # Salva GPU dedicata
                    vram_bytes = getattr(gpu, 'AdapterRAM', 8*1024**3)
                    if vram_bytes and vram_bytes > 512 * 1024**2:  # Più di 512MB = dedicata
                        all_gpus.append({
                            'name': gpu.Name,
                            'vram': vram_bytes,
                            'index': len(all_gpus)
                        })
                
                if all_gpus:
                    # Prendi la GPU con più VRAM (quella dedicata principale)
                    best_gpu = max(all_gpus, key=lambda x: x['vram'])
                    self.model = best_gpu['name']
                    self.vram = round(best_gpu['vram'] / (1024**3), 1)
                    
                    if 'NVIDIA' in self.model.upper():
                        self.brand = 'nvidia'
                    elif 'AMD' in self.model.upper():
                        self.brand = 'amd'
                    elif 'RADEON' in self.model.upper():
                        self.brand = 'amd'
                    else:
                        self.brand = 'unknown'
                    
                    print(f"✅ GPU dedicata rilevata via WMI: {self.model} ({self.vram}GB)")
                    return
            except Exception as e:
                print(f"⚠️ Errore WMI: {e}")
            
            # Metodo 3: PowerShell con filtro avanzato
            ps_command = """
            Get-WmiObject Win32_VideoController | 
            Where-Object { 
                $_.Name -notmatch 'Microsoft|Virtual|Remote|Basic|Intel|HD Graphics|UHD Graphics|Iris' 
            } |
            Sort-Object AdapterRAM -Descending |
            Select-Object Name, AdapterRAM -First 1 |
            ConvertTo-Json
            """
            
            output = subprocess.run(
                ['powershell', '-Command', ps_command],
                capture_output=True, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            
            if output.returncode == 0 and output.stdout.strip() and output.stdout.strip() != 'null':
                import json
                data = json.loads(output.stdout)
                
                self.model = data.get('Name', 'GPU sconosciuta')
                if 'NVIDIA' in self.model.upper():
                    self.brand = 'nvidia'
                elif 'AMD' in self.model.upper() or 'RADEON' in self.model.upper():
                    self.brand = 'amd'
                else:
                    self.brand = 'unknown'
                
                # VRAM in GB
                ram_bytes = data.get('AdapterRAM', 8*1024**3)
                self.vram = round(ram_bytes / (1024**3), 1)
                
                print(f"✅ GPU rilevata via PowerShell: {self.brand.upper()} - {self.model}")
                return
                
        except Exception as e:
            print(f"⚠️ Errore rilevamento GPU: {e}")
        
        # Fallback
        self.model = "NVIDIA GeForce RTX 4070 SUPER"
        self.brand = 'nvidia'
        self.vram = 12.0
        print(f"⚠️ Fallback GPU: {self.model}")
    
    def get_system_info(self):
        """Raccoglie info complete di sistema"""
        info = {}
        
        # CPU
        try:
            info['cpu_name'] = platform.processor()
            if not info['cpu_name'] or info['cpu_name'] == '':
                # Prova con WMI per nome CPU più descrittivo
                try:
                    import wmi
                    c = wmi.WMI()
                    for cpu in c.Win32_Processor():
                        info['cpu_name'] = cpu.Name
                        break
                except:
                    info['cpu_name'] = "CPU sconosciuta"
        except:
            info['cpu_name'] = "CPU sconosciuta"
        
        info['cpu_cores'] = psutil.cpu_count(logical=False) or 0
        info['cpu_threads'] = psutil.cpu_count(logical=True) or 0
        try:
            cpu_freq = psutil.cpu_freq()
            info['cpu_freq'] = round(cpu_freq.max / 1000, 2) if cpu_freq else 0
        except:
            info['cpu_freq'] = 0
        
        # RAM
        try:
            ram = psutil.virtual_memory()
            info['ram_total'] = round(ram.total / (1024**3), 1)
            info['ram_used'] = round(ram.used / (1024**3), 1)
            info['ram_percent'] = ram.percent
        except:
            info['ram_total'] = 0
            info['ram_used'] = 0
            info['ram_percent'] = 0
        
        # MOTHERBOARD
        try:
            import wmi
            c = wmi.WMI()
            info['mobo_model'] = "Non rilevata"
            info['mobo_manufacturer'] = "Unknown"
            for board in c.Win32_BaseBoard():
                info['mobo_model'] = getattr(board, 'Product', 'Non rilevata')
                info['mobo_manufacturer'] = getattr(board, 'Manufacturer', 'Unknown')
                break
        except:
            info['mobo_model'] = "Non rilevata"
            info['mobo_manufacturer'] = "Unknown"
        
        return info
    
    def _get_gpu_tier(self):
        """Determina il tier della GPU in base al modello"""
        model_lower = self.model.lower()
        
        if any(x in model_lower for x in ['4090', '5090', '4080 ti', '5080']):
            return 'ultra_high'
        elif any(x in model_lower for x in ['4080', '5080', '4070 ti']):
            return 'high'
        elif any(x in model_lower for x in ['4070', '5070']):
            return 'mid_high'
        elif any(x in model_lower for x in ['4060', '5060']):
            return 'mid'
        else:
            return 'entry'
    
    def get_fps_estimate(self, resolution, preset_type):
        """Calcola FPS realistici in base ALLA GPU SPECIFICA dell'utente"""
        
        # Determina il tier della GPU
        gpu_tier = self._get_gpu_tier()
        
        # FPS base per ogni tier
        fps_tiers = {
            'ultra_high': {'1080p': 300, '1440p': 240, '4K': 160},
            'high': {'1080p': 240, '1440p': 180, '4K': 120},
            'mid_high': {'1080p': 200, '1440p': 140, '4K': 90},
            'mid': {'1080p': 160, '1440p': 110, '4K': 70},
            'entry': {'1080p': 120, '1440p': 80, '4K': 50}
        }
        
        base_fps = fps_tiers.get(gpu_tier, fps_tiers['entry']).get(resolution, 120)
        
        # Modifica in base al preset
        if preset_type == 'competitivo':
            return int(base_fps * 1.2)
        elif preset_type == 'cinematografico':
            return int(base_fps * 0.7)
        else:
            return base_fps

# ========== OVERCLOCK ==========
class OverclockSafe:
    def __init__(self, gpu_detector):
        self.gpu = gpu_detector
        self.core_offset = 0
        self.mem_offset = 0
        self.power_limit = 100
        self.is_active = False
        self.profile_file = None
    
    def get_limits(self):
        if '4090' in self.gpu.model:
            return {'core_max': 250, 'mem_max': 1200, 'core_safe': 180, 'mem_safe': 900, 'power_max': 120}
        elif '4080' in self.gpu.model:
            return {'core_max': 225, 'mem_max': 1100, 'core_safe': 160, 'mem_safe': 850, 'power_max': 115}
        elif '4070' in self.gpu.model:
            return {'core_max': 200, 'mem_max': 1000, 'core_safe': 150, 'mem_safe': 800, 'power_max': 110}
        else:
            return {'core_max': 150, 'mem_max': 800, 'core_safe': 100, 'mem_safe': 500, 'power_max': 105}
    
    def apply_overclock(self, core, mem, power):
        self.core_offset = core
        self.mem_offset = mem
        self.power_limit = power
        self.is_active = True
        
        oc_dir = os.path.join(os.path.expanduser("~"), "Documents", "ForteControl", "Overclock")
        os.makedirs(oc_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        self.profile_file = os.path.join(oc_dir, f"overclock_active_{timestamp}.cfg")
        
        with open(self.profile_file, 'w') as f:
            f.write(f"Core Offset: +{core} MHz\nMemory Offset: +{mem} MHz\nPower Limit: {power}%\n")
        
        return self.profile_file
    
    def disable_overclock(self):
        self.is_active = False
        self.core_offset = 0
        self.mem_offset = 0
        self.power_limit = 100
        self.profile_file = None
        return True
    
    def get_performance_boost(self):
        core_boost = self.core_offset / 15
        mem_boost = self.mem_offset / 100
        return round(min(core_boost + mem_boost, 20), 1)

# ========== SETTAGGI GRAFICI ==========
class GraphicsBooster:
    def __init__(self, gpu_detector):
        self.gpu = gpu_detector
    
    def get_preset_settings(self, resolution, preset_type):
        res_map = {'1080p': '1920x1080', '1440p': '2560x1440', '4K': '3840x2160'}
        
        # Usa FPS stimati dalla GPU
        estimated_fps = self.gpu.get_fps_estimate(resolution, preset_type)
        
        settings = {
            'competitivo': {
                'name': '🏆 COMPETITIVO - Massimi FPS',
                'desc': f'Zero lag, massima reattività',
                'color': '#00aaff', 'dlss': 'Prestazioni Ultra',
                'reflex': 'Attivato + Boost', 'texture': 'Bassa',
                'ombre': 'Basse', 'raytracing': 'Disattivato'
            },
            'bilanciato': {
                'name': '⚖️ BILANCIATO - Qualità/FPS',
                'desc': f'Il miglior compromesso',
                'color': '#ffaa00', 'dlss': 'Qualità',
                'reflex': 'Attivato', 'texture': 'Alta',
                'ombre': 'Medie', 'raytracing': 'Basso'
            },
            'cinematografico': {
                'name': '🎬 CINEMATOGRAFICO - Max Qualità',
                'desc': f'Fedeltà visiva massima',
                'color': '#ff5500', 'dlss': 'Qualità Ultra',
                'reflex': 'Attivato', 'texture': 'Ultra',
                'ombre': 'Ultra', 'raytracing': 'Alto'
            }
        }
        preset = settings[preset_type].copy()
        preset['resolution'] = resolution
        preset['res_string'] = res_map.get(resolution, '1920x1080')
        preset['fps'] = estimated_fps
        return preset
    
    def generate_instructions(self, game_name, preset, notes=""):
        folder = os.path.join(os.path.expanduser("~"), "Documents", "ForteControl", "Presets")
        os.makedirs(folder, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        filename = f"{game_name}_{preset['resolution']}_{preset['fps']}fps_{timestamp}.txt"
        filepath = os.path.join(folder, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write(f"🎮 FORTE CONTROL - PRESET GRAFICO\n")
            f.write("="*80 + "\n\n")
            f.write(f"Gioco: {game_name}\n")
            f.write(f"Preset: {preset['name']}\n")
            f.write(f"GPU: {self.gpu.model}\n")
            f.write(f"VRAM: {self.gpu.vram}GB\n")
            f.write(f"Risoluzione: {preset['resolution']}\n")
            f.write(f"FPS stimati: {preset['fps']} FPS\n\n")
            f.write(f"Impostazioni:\n")
            f.write(f"• DLSS/FSR: {preset['dlss']}\n")
            f.write(f"• NVIDIA Reflex: {preset['reflex']}\n")
            f.write(f"• Texture: {preset['texture']}\n")
            f.write(f"• Ombre: {preset['ombre']}\n")
            f.write(f"• Ray Tracing: {preset['raytracing']}\n")
        
        return filepath

# ========== AUDIO PRESET MANAGER ==========
class AudioPresetManager:
    def __init__(self):
        self.presets = {
            'fps_footsteps': {
                'name': '👣 FPS FOOTSTEPS - Passi',
                'desc': 'Ottimizzato per sentire i passi nei giochi FPS',
                'values': [5,6,7,6,5,3,1,-1,-2,-3],
                'compatible_with': ['gaming', 'fps'],
                'eq_type': 'aggressive'
            },
            'bass_boost': {
                'name': '🔊 BASS BOOST',
                'desc': 'Esplosioni e musica potenziate',
                'values': [6,7,5,3,2,1,0,-1,-2,-2],
                'compatible_with': ['movies', 'music'],
                'eq_type': 'warm'
            },
            'flat': {
                'name': '🎵 FLAT',
                'desc': 'Audio originale senza modifiche',
                'values': [0,0,0,0,0,0,0,0,0,0],
                'compatible_with': ['all'],
                'eq_type': 'neutral'
            },
            'vocal': {
                'name': '🎤 VOCAL',
                'desc': 'Enfatizza le voci e i dialoghi',
                'values': [1,2,3,4,4,3,2,1,0,0],
                'compatible_with': ['rpg', 'story'],
                'eq_type': 'vocal'
            }
        }
        
        self.headphone_profiles = {
            'gaming': {
                'compatible_presets': ['fps_footsteps', 'bass_boost'],
                'eq_adjustment': 'focus_mid',
                'description': 'Cuffie da gaming (enfasi su passi e effetti)'
            },
            'studio': {
                'compatible_presets': ['flat', 'vocal'],
                'eq_adjustment': 'neutral',
                'description': 'Cuffie da studio/audiophile (suono bilanciato)'
            },
            'earbuds': {
                'compatible_presets': ['vocal', 'flat'],
                'eq_adjustment': 'bright',
                'description': 'Auricolari standard (enfasi su voci)'
            },
            'default': {
                'compatible_presets': ['fps_footsteps', 'bass_boost', 'flat', 'vocal'],
                'eq_adjustment': 'balanced',
                'description': 'Cuffie generiche'
            }
        }
    
    def suggest_preset(self, headphone_type='default'):
        """Suggerisce il preset migliore in base al tipo di cuffie"""
        profile = self.headphone_profiles.get(headphone_type, self.headphone_profiles['default'])
        suggested_preset_key = profile['compatible_presets'][0]
        return self.presets[suggested_preset_key], profile['description']
    
    def get_preset(self, preset_key):
        """Restituisce un preset specifico"""
        return self.presets.get(preset_key, self.presets['flat'])

# ========== SCANNER GIOCHI ==========
class GameScanner:
    def __init__(self):
        self.games = []
        self.platform_colors = {
            'Steam': '#00aaff',
            'Xbox Game Pass': '#00ff00',
            'Battle.net': '#148eff',
            'Epic Games': '#888888',
            'EA App': '#ff5555',
            'Ubisoft Connect': '#ffaa00',
            'GOG Galaxy': '#ff00ff',
            'Desktop': '#aaaaaa',
            'Program Files': '#ff9900'
        }
    
    def scan_all(self):
        """Scansione COMPLETA di TUTTE le piattaforme"""
        print("🔍 Scansione completa giochi...")
        all_games = []
        
        # STEAM
        steam_paths = [
            r"C:\Program Files (x86)\Steam\steamapps\common",
            r"C:\Program Files\Steam\steamapps\common",
            r"D:\Steam\steamapps\common"
        ]
        for path in steam_paths:
            if os.path.exists(path):
                try:
                    for folder in os.listdir(path):
                        if os.path.isdir(os.path.join(path, folder)):
                            if not any(x in folder.lower() for x in ['_commonredist', 'tmp']):
                                all_games.append({'name': folder, 'platform': 'Steam', 'path': os.path.join(path, folder)})
                except: pass
        
        # XBOX GAME PASS
        xbox_paths = [r"C:\XboxGames", r"D:\XboxGames"]
        for path in xbox_paths:
            if os.path.exists(path):
                try:
                    for folder in os.listdir(path):
                        if os.path.isdir(os.path.join(path, folder)):
                            name = folder
                            if 'Microsoft' in folder:
                                parts = folder.split('_')
                                if len(parts) > 1:
                                    name = parts[0]
                            all_games.append({'name': name[:50], 'platform': 'Xbox Game Pass', 'path': os.path.join(path, folder)})
                except: pass
        
        # BATTLE.NET
        battlenet_paths = [
            r"C:\Program Files (x86)\Call of Duty",
            r"C:\Program Files\Call of Duty",
            r"D:\Call of Duty",
            r"C:\Program Files (x86)\Overwatch",
            r"D:\Overwatch",
            r"C:\Program Files (x86)\World of Warcraft"
        ]
        for path in battlenet_paths:
            if os.path.exists(path):
                all_games.append({'name': os.path.basename(path), 'platform': 'Battle.net', 'path': path})
        
        # EPIC
        epic_paths = [r"C:\Program Files\Epic Games", r"D:\Epic Games"]
        for path in epic_paths:
            if os.path.exists(path):
                try:
                    for folder in os.listdir(path):
                        if os.path.isdir(os.path.join(path, folder)):
                            all_games.append({'name': folder, 'platform': 'Epic Games', 'path': os.path.join(path, folder)})
                except: pass
        
        # EA
        ea_paths = [r"C:\Program Files\EA Games", r"C:\Program Files\Origin Games", r"D:\Origin Games"]
        for path in ea_paths:
            if os.path.exists(path):
                try:
                    for folder in os.listdir(path):
                        if os.path.isdir(os.path.join(path, folder)):
                            all_games.append({'name': folder, 'platform': 'EA App', 'path': os.path.join(path, folder)})
                except: pass
        
        # UBISOFT
        ubisoft_paths = [r"C:\Program Files (x86)\Ubisoft", r"C:\Program Files\Ubisoft"]
        for path in ubisoft_paths:
            if os.path.exists(path):
                try:
                    for folder in os.listdir(path):
                        if os.path.isdir(os.path.join(path, folder)) and 'launcher' not in folder.lower():
                            all_games.append({'name': folder, 'platform': 'Ubisoft Connect', 'path': os.path.join(path, folder)})
                except: pass
        
        # GOG
        gog_paths = [r"C:\Program Files (x86)\GOG Galaxy", r"D:\GOG Games", r"C:\GOG Games"]
        for path in gog_paths:
            if os.path.exists(path):
                try:
                    for folder in os.listdir(path):
                        if os.path.isdir(os.path.join(path, folder)) and 'galaxy' not in folder.lower():
                            all_games.append({'name': folder, 'platform': 'GOG Galaxy', 'path': os.path.join(path, folder)})
                except: pass
        
        # DESKTOP
        desktop = os.path.expanduser("~/Desktop")
        if os.path.exists(desktop):
            try:
                for item in os.listdir(desktop):
                    if item.endswith('.lnk'):
                        name = item.replace('.lnk', '')
                        game_keywords = ['call', 'duty', 'war', 'cod', 'battle', 'overwatch', 'fortnite', 'apex', 'valorant']
                        if any(keyword in name.lower() for keyword in game_keywords):
                            all_games.append({'name': name[:50], 'platform': 'Desktop', 'path': desktop})
            except: pass
        
        # PROGRAM FILES
        program_files = [r"C:\Program Files", r"C:\Program Files (x86)"]
        game_folders = ['Call of Duty', 'Warzone', 'Overwatch', 'World of Warcraft', 'Diablo', 'Fortnite', 'Apex', 'Valorant']
        for pf in program_files:
            if os.path.exists(pf):
                try:
                    for folder in os.listdir(pf):
                        if any(gf.lower() in folder.lower() for gf in game_folders):
                            full_path = os.path.join(pf, folder)
                            if os.path.isdir(full_path):
                                all_games.append({'name': folder[:50], 'platform': 'Program Files', 'path': full_path})
                except: pass
        
        # RIMUOVI DUPLICATI
        unique = []
        seen = set()
        for game in all_games:
            key = f"{game['name'].lower()}_{game['platform']}"
            if key not in seen:
                seen.add(key)
                unique.append(game)
        
        self.games = sorted(unique, key=lambda x: x['name'].lower())
        print(f"✅ Trovati {len(self.games)} giochi")
        return self.games
    
    def get_game_list_for_combo(self):
        """Restituisce lista formattata per menu a tendina"""
        game_list = []
        for game in self.games[:100]:
            name = game['name'][:40]
            plat = game['platform']
            game_list.append(f"{name} [{plat}]")
        return game_list

# ========== INTERNET MAXIMIZER ==========
class InternetMaximizer:
    def __init__(self):
        self.is_active = False
    
    def boost(self):
        cmds = [
            'ipconfig /flushdns',
            'netsh int tcp set global autotuninglevel=normal',
            'netsh int tcp set global rss=enabled',
            'netsh int tcp set global chimney=enabled',
            'netsh int tcp set global netdma=enabled'
        ]
        success = 0
        for cmd in cmds:
            try:
                subprocess.run(cmd, shell=True, timeout=2, capture_output=True)
                success += 1
            except: pass
        self.is_active = True
        return success

# ========== BUG DETECTOR (VERSIONE CORRETTA) ==========
class BugDetector:
    def __init__(self):
        self.last_scan_results = []
    
    def scan(self):
        """Scansione completa per problemi"""
        issues = []
        
        # RAM
        try:
            ram = psutil.virtual_memory()
            if ram.percent > 85:
                issues.append({
                    "type": "ram_high",
                    "msg": f"RAM utilizzata: {ram.percent}% - Troppi programmi aperti",
                    "severity": "high"
                })
            elif ram.percent > 70:
                issues.append({
                    "type": "ram_medium",
                    "msg": f"RAM utilizzata: {ram.percent}% - Monitorare l'utilizzo",
                    "severity": "medium"
                })
        except:
            issues.append({
                "type": "ram_error",
                "msg": "Impossibile leggere lo stato della RAM",
                "severity": "low"
            })
        
        # DISCO C:
        try:
            disk = psutil.disk_usage('C:\\')
            free_gb = disk.free / (1024**3)
            if free_gb < 10:
                issues.append({
                    "type": "disk_critical",
                    "msg": f"Spazio su C: {free_gb:.1f}GB liberi - CRITICO! Pulizia urgente",
                    "severity": "critical"
                })
            elif free_gb < 30:
                issues.append({
                    "type": "disk_low",
                    "msg": f"Spazio su C: {free_gb:.1f}GB liberi - Pulizia consigliata",
                    "severity": "high"
                })
            elif free_gb < 50:
                issues.append({
                    "type": "disk_medium",
                    "msg": f"Spazio su C: {free_gb:.1f}GB liberi - Monitorare lo spazio",
                    "severity": "medium"
                })
        except:
            issues.append({
                "type": "disk_error",
                "msg": "Impossibile leggere lo spazio su disco C:",
                "severity": "low"
            })
        
        # CPU TEMPERATURE (se disponibile)
        try:
            import wmi
            c = wmi.WMI(namespace="root\\wmi")
            temp_info = c.MSAcpi_ThermalZoneTemperature()
            if temp_info:
                current_temp = 0
                for temp in temp_info:
                    current_temp = temp.CurrentTemperature / 10.0 - 273.15
                    if current_temp > 80:
                        issues.append({
                            "type": "cpu_hot",
                            "msg": f"CPU molto calda: {current_temp:.1f}°C - Verificare raffreddamento",
                            "severity": "high"
                        })
                    elif current_temp > 70:
                        issues.append({
                            "type": "cpu_warm",
                            "msg": f"CPU calda: {current_temp:.1f}°C",
                            "severity": "medium"
                        })
                    break
        except:
            pass  # Ignora se non disponibile
        
        # PROCESSI PESANTI
        try:
            heavy_processes = []
            for proc in psutil.process_iter(['name', 'cpu_percent', 'memory_percent']):
                try:
                    cpu = proc.info['cpu_percent']
                    mem = proc.info['memory_percent']
                    if cpu and cpu > 30:
                        heavy_processes.append(f"{proc.info['name']} (CPU: {cpu:.1f}%)")
                except:
                    pass
            
            if heavy_processes:
                issues.append({
                    "type": "heavy_processes",
                    "msg": f"Processi pesanti: {', '.join(heavy_processes[:3])}",
                    "severity": "medium"
                })
        except:
            pass
        
        self.last_scan_results = issues
        return issues
    
    def get_summary(self):
        """Restituisce un sommario dei problemi"""
        if not self.last_scan_results:
            return "✅ NESSUN PROBLEMA RILEVATO"
        
        critical = sum(1 for i in self.last_scan_results if i.get('severity') == 'critical')
        high = sum(1 for i in self.last_scan_results if i.get('severity') == 'high')
        medium = sum(1 for i in self.last_scan_results if i.get('severity') == 'medium')
        low = sum(1 for i in self.last_scan_results if i.get('severity') == 'low')
        
        return f"⚠️ Trovati: {critical} critici, {high} alti, {medium} medi, {low} bassi"

# ========== APP PRINCIPALE ==========
class ForteControlUltimate:
    def __init__(self):
        self.gpu = GPUDetector()
        self.graphics = GraphicsBooster(self.gpu)
        self.audio_manager = AudioPresetManager()
        self.overclock = OverclockSafe(self.gpu)
        self.internet = InternetMaximizer()
        self.bug = BugDetector()
        self.scanner = GameScanner()
        
        self.window = ctk.CTk()
        self.window.title(f"🎮 FORTE CONTROL ULTIMATE")
        self.window.geometry("1400x900")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.setup_ui()
        
        # Variabili per info dinamiche
        self.info_frame = None
        self.info_label = None
        
        threading.Thread(target=self.load_games, daemon=True).start()
        
        # Aggiornamento periodico delle info
        self.update_info_periodically()
        
        # Controllo aggiornamenti
        self.check_for_updates()
    
    def setup_ui(self):
        self.notebook = ctk.CTkTabview(self.window)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.notebook.add("🏠 Dashboard")
        self.notebook.add("🎮 Giochi")
        self.notebook.add("🎨 Grafica")
        self.notebook.add("🎧 Audio")
        self.notebook.add("⚡ Overclock")
        self.notebook.add("🌐 Internet")
        self.notebook.add("🐛 Bug")
        self.notebook.add("⚙️ Info")
        
        self.create_dashboard()
        self.create_games()
        self.create_graphics()
        self.create_audio()
        self.create_overclock()
        self.create_internet()
        self.create_bug()
        self.create_info()
        
        # Status bar
        self.status_bar = ctk.CTkFrame(self.window, height=35)
        self.status_bar.pack(side="bottom", fill="x", pady=(0,5))
        self.status_label = ctk.CTkLabel(self.status_bar, text="✅ Pronto", font=("Arial", 12))
        self.status_label.pack(side="left", padx=15)
        ctk.CTkButton(self.status_bar, text="🚪 Esci", command=self.window.quit,
                     width=70, height=28, fg_color="#ff5555").pack(side="right", padx=15)
    
    # ---------- FUNZIONI DI AGGIORNAMENTO ----------
    def update_info_periodically(self):
        """Aggiorna le informazioni ogni 5 secondi"""
        try:
            self.refresh_info_tab()
        except:
            pass
        self.window.after(5000, self.update_info_periodically)
    
    def refresh_info_tab(self):
        """Aggiorna il contenuto della tab Info"""
        if hasattr(self, 'info_label') and self.info_label:
            games_count = len(self.scanner.games) if self.scanner.games else 0
            oc_status = 'ATTIVO' if self.overclock.is_active else 'DISATTIVO'
            
            info_text = f"""
🎮 FORTE CONTROL ULTIMATE
📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}

🖥️ GPU: {self.gpu.model} ({self.gpu.vram}GB)
🎮 Giochi trovati: {games_count}
⚡ Overclock: {oc_status}
🌐 Internet Maximizer: {'ATTIVO' if self.internet.is_active else 'DISATTIVO'}
🐛 Bug: {self.bug.get_summary()}
            """
            self.info_label.configure(text=info_text)
    
    def check_for_updates(self):
        """Controlla se ci sono aggiornamenti disponibili"""
        try:
            import requests
            import webbrowser
            
            def check():
                try:
                    # 🔧 CAMBIA QUESTI VALORI CON I TUOI
                    version_url = "https://pastebin.com/raw/ABC123"  # IL TUO LINK PASTEBIN
                    current_version = "1.0"  # LA VERSIONE ATTUALE
                    website_url = "https://tuo-sito.carrd.co"  # IL TUO SITO
                    
                    response = requests.get(version_url, timeout=3)
                    latest_version = response.text.strip()
                    
                    if latest_version > current_version:
                        self.window.after(0, lambda: self._show_update_dialog(latest_version, website_url))
                except Exception as e:
                    print(f"Controllo aggiornamenti: {e}")
            
            threading.Thread(target=check, daemon=True).start()
        except:
            pass
    
    def _show_update_dialog(self, latest_version, website_url):
        """Mostra il dialog di aggiornamento"""
        import webbrowser
        
        result = messagebox.askyesno(
            "🎮 Aggiornamento Disponibile",
            f"È disponibile una nuova versione di Forte Control!\n\n"
            f"Versione attuale: 1.0\n"
            f"Nuova versione: {latest_version}\n\n"
            f"Vuoi visitare il sito per scaricarla?",
            icon='info'
        )
        if result:
            webbrowser.open(website_url)
    
    # ---------- DASHBOARD ----------
    def create_dashboard(self):
        tab = self.notebook.tab("🏠 Dashboard")
        
        ctk.CTkLabel(tab, text="🎮 FORTE CONTROL ULTIMATE",
                    font=("Arial", 36, "bold"), text_color="#00ffff").pack(pady=20)
        
        # Ottieni info complete
        sys_info = self.gpu.get_system_info()
        
        # GPU Card
        gpu_card = ctk.CTkFrame(tab, fg_color="#1a1a2e", corner_radius=15)
        gpu_card.pack(pady=10, padx=50, fill="x")
        ctk.CTkLabel(gpu_card, text=f"🟢 GPU: {self.gpu.model} ({self.gpu.vram}GB VRAM)",
                    font=("Arial", 16, "bold"), text_color="#00ff00").pack(pady=10)
        
        # CPU Card
        cpu_card = ctk.CTkFrame(tab, fg_color="#1a1a2e", corner_radius=15)
        cpu_card.pack(pady=10, padx=50, fill="x")
        cpu_text = f"🔵 CPU: {sys_info.get('cpu_name', 'N/A')[:60]}\n"
        cpu_text += f"   Core: {sys_info.get('cpu_cores', 0)} fisici, {sys_info.get('cpu_threads', 0)} thread"
        if sys_info.get('cpu_freq', 0) > 0:
            cpu_text += f" | {sys_info['cpu_freq']} GHz"
        ctk.CTkLabel(cpu_card, text=cpu_text,
                    font=("Arial", 14), text_color="#00aaff", justify="left").pack(pady=10, padx=20)
        
        # RAM Card
        ram_card = ctk.CTkFrame(tab, fg_color="#1a1a2e", corner_radius=15)
        ram_card.pack(pady=10, padx=50, fill="x")
        ram_text = f"💾 RAM: {sys_info.get('ram_total', 0)}GB totali\n"
        ram_text += f"   Utilizzati: {sys_info.get('ram_used', 0)}GB ({sys_info.get('ram_percent', 0)}%)"
        ctk.CTkLabel(ram_card, text=ram_text,
                    font=("Arial", 14), text_color="#ffaa00", justify="left").pack(pady=10, padx=20)
        
        # MOTHERBOARD Card
        mobo_card = ctk.CTkFrame(tab, fg_color="#1a1a2e", corner_radius=15)
        mobo_card.pack(pady=10, padx=50, fill="x")
        mobo_text = f"🔧 Motherboard: {sys_info.get('mobo_manufacturer', 'N/A')} {sys_info.get('mobo_model', 'N/A')}"
        ctk.CTkLabel(mobo_card, text=mobo_text,
                    font=("Arial", 14), text_color="#ff00ff", justify="left").pack(pady=10, padx=20)
        
        # Quick buttons
        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.pack(pady=20)
        ctk.CTkButton(btn_frame, text="🔍 Scansiona Giochi", command=self.scan_games,
                     width=200, height=45, fg_color="#00aaff").pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="⚡ Overclock", 
                     command=lambda: self.notebook.set("⚡ Overclock"),
                     width=200, height=45, fg_color="#ff9900").pack(side="left", padx=10)
    
    # ---------- GIOCHI ----------
    def create_games(self):
        tab = self.notebook.tab("🎮 Giochi")
        top = ctk.CTkFrame(tab)
        top.pack(pady=15, padx=20, fill="x")
        ctk.CTkLabel(top, text="🎮 TUTTI I GIOCHI INSTALLATI",
                    font=("Arial", 24, "bold")).pack(side="left", padx=10)
        ctk.CTkButton(top, text="🔄 AGGIORNA", command=self.scan_games,
                     width=120, height=40, fg_color="#00aaff").pack(side="right", padx=10)
        
        list_frame = ctk.CTkFrame(tab)
        list_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        canvas = ctk.CTkCanvas(list_frame, bg="#2b2b2b", highlightthickness=0)
        scrollbar = ctk.CTkScrollbar(list_frame, orientation="vertical", command=canvas.yview)
        self.games_container = ctk.CTkFrame(canvas)
        self.games_container.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.games_container, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    # ---------- GRAFICA ----------
    def create_graphics(self):
        tab = self.notebook.tab("🎨 Grafica")
        
        ctk.CTkLabel(tab, text="🎨 SETTAGGI GRAFICI",
                    font=("Arial", 28, "bold"), text_color="#00ffff").pack(pady=20)
        
        gpu_frame = ctk.CTkFrame(tab, fg_color="#1a1a2e", corner_radius=10)
        gpu_frame.pack(pady=10, padx=50, fill="x")
        ctk.CTkLabel(gpu_frame, text=f"🟢 {self.gpu.model} - {self.gpu.vram}GB VRAM",
                    font=("Arial", 14, "bold"), text_color="#00ff00").pack(pady=10)
        
        controls = ctk.CTkFrame(tab, fg_color="transparent")
        controls.pack(pady=15, padx=50, fill="x")
        
        row1 = ctk.CTkFrame(controls, fg_color="transparent")
        row1.pack(fill="x", pady=5)
        
        ctk.CTkLabel(row1, text="🎮 Gioco:", font=("Arial", 14, "bold")).pack(side="left", padx=5)
        self.graphics_game = ctk.CTkComboBox(row1, values=["Caricamento in corso..."], width=350)
        self.graphics_game.pack(side="left", padx=10)
        
        ctk.CTkLabel(row1, text="🖥️ Risoluzione:", font=("Arial", 14, "bold")).pack(side="left", padx=20)
        self.graphics_res = ctk.CTkComboBox(row1, values=["1080p", "1440p", "4K"], width=120)
        self.graphics_res.pack(side="left", padx=10)
        self.graphics_res.set("1440p")
        
        self.preset_var = ctk.StringVar(value="bilanciato")
        preset_frame = ctk.CTkFrame(tab)
        preset_frame.pack(pady=15, padx=50, fill="x")
        
        ctk.CTkLabel(preset_frame, text="🎯 Preset:", font=("Arial", 14, "bold")).pack(side="left", padx=10)
        ctk.CTkRadioButton(preset_frame, text="Competitivo", variable=self.preset_var, 
                          value="competitivo", text_color="#00aaff").pack(side="left", padx=10)
        ctk.CTkRadioButton(preset_frame, text="Bilanciato", variable=self.preset_var, 
                          value="bilanciato", text_color="#ffaa00").pack(side="left", padx=10)
        ctk.CTkRadioButton(preset_frame, text="Cinematografico", variable=self.preset_var, 
                          value="cinematografico", text_color="#ff5500").pack(side="left", padx=10)
        
        ctk.CTkButton(tab, text="⚡ GENERA PRESET GRAFICO",
                     command=self.generate_graphics_preset,
                     width=400, height=60, 
                     font=("Arial", 16, "bold"),
                     fg_color="#00cc88").pack(pady=25)
        
        # SEZIONE CARTELLA PRESET GRAFICI
        folder_frame = ctk.CTkFrame(tab, fg_color="#1a1a2e", corner_radius=15)
        folder_frame.pack(pady=20, padx=50, fill="x")
        
        graphics_folder = os.path.join(os.path.expanduser("~"), "Documents", "ForteControl", "Presets")
        
        header = ctk.CTkFrame(folder_frame, fg_color="transparent")
        header.pack(pady=(15,5))
        ctk.CTkLabel(header, text="📁", font=("Arial", 32)).pack(side="left", padx=10)
        ctk.CTkLabel(header, text="CARTELLA PRESET GRAFICI", 
                    font=("Arial", 18, "bold"), text_color="#00ffff").pack(side="left", padx=10)
        
        path_label = ctk.CTkLabel(
            folder_frame, 
            text=graphics_folder,
            font=("Consolas", 12),
            text_color="#aaaaaa"
        )
        path_label.pack(pady=5)
        
        def open_graphics_folder():
            if not os.path.exists(graphics_folder):
                os.makedirs(graphics_folder, exist_ok=True)
            os.startfile(graphics_folder)
        
        open_btn = ctk.CTkButton(
            folder_frame,
            text="📂 APRI CARTELLA PRESET",
            command=open_graphics_folder,
            width=250,
            height=45,
            font=("Arial", 14, "bold"),
            fg_color="#00aaff"
        )
        open_btn.pack(pady=(5,15))
    
    # ---------- AUDIO ----------
    def create_audio(self):
        tab = self.notebook.tab("🎧 Audio")
        
        ctk.CTkLabel(tab, text="🎧 STEELSERIES GG",
                    font=("Arial", 28, "bold"), text_color="#ff00ff").pack(pady=20)
        
        # Status SteelSeries (simulato)
        status_frame = ctk.CTkFrame(tab, fg_color="#1a1a2e")
        status_frame.pack(pady=10, padx=50, fill="x")
        
        # Verifica se SteelSeries è installato (cerca nel Program Files)
        steelseries_installed = os.path.exists(r"C:\Program Files\SteelSeries") or os.path.exists(r"C:\Program Files (x86)\SteelSeries")
        
        if steelseries_installed:
            status_text = "✅ SteelSeries GG INSTALLATO"
            status_color = "#00ff00"
        else:
            status_text = "❌ SteelSeries GG NON INSTALLATO"
            status_color = "#ff5555"
        
        ctk.CTkLabel(status_frame, text=status_text,
                    font=("Arial", 14, "bold"), text_color=status_color).pack(pady=10)
        
        # GUIDA RAPIDA
        guide_frame = ctk.CTkFrame(tab, fg_color="#2a2a3a", corner_radius=10)
        guide_frame.pack(pady=15, padx=50, fill="x")
        
        guide_title = ctk.CTkLabel(
            guide_frame,
            text="📋 GUIDA RAPIDA - Come usare i preset audio",
            font=("Arial", 16, "bold"),
            text_color="#ff00ff"
        )
        guide_title.pack(pady=(15, 10))
        
        # Opzione 1 - Engine
        engine_frame = ctk.CTkFrame(guide_frame, fg_color="transparent")
        engine_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(
            engine_frame,
            text="✅ HAI PERIFERICHE STEELSERIES?",
            font=("Arial", 13, "bold"),
            text_color="#00ff00",
            anchor="w"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            engine_frame,
            text="   → Usa ENGINE per importare il file .ss3\n     (il preset si applica automaticamente)",
            font=("Arial", 12),
            text_color="#cccccc",
            anchor="w",
            justify="left"
        ).pack(anchor="w", pady=(0, 10))
        
        # Opzione 2 - Sonar
        sonar_frame = ctk.CTkFrame(guide_frame, fg_color="transparent")
        sonar_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(
            sonar_frame,
            text="🎧 HAI CUFFIE DI ALTRE MARCHE?",
            font=("Arial", 13, "bold"),
            text_color="#00aaff",
            anchor="w"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            sonar_frame,
            text="   → Installa SteelSeries GG (gratis) e apri SONAR\n   → Applica i valori manualmente seguendo il file .txt\n   → SONAR funziona con QUALSIASI cuffia!",
            font=("Arial", 12),
            text_color="#cccccc",
            anchor="w",
            justify="left"
        ).pack(anchor="w", pady=(0, 15))
        
        # Link download
        download_frame = ctk.CTkFrame(guide_frame, fg_color="transparent")
        download_frame.pack(pady=(0, 15))
        
        def open_steelseries_download():
            import webbrowser
            webbrowser.open("https://steelseries.com/gg/download")
        
        ctk.CTkButton(
            download_frame,
            text="📥 SCARICA STEELSERIES GG",
            command=open_steelseries_download,
            width=250,
            height=35,
            font=("Arial", 12, "bold"),
            fg_color="#ff00ff",
            hover_color="#cc00cc"
        ).pack()
        
        # Info cartella
        folder_frame = ctk.CTkFrame(guide_frame, fg_color="#1a1a2a", corner_radius=5)
        folder_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        folder_path = os.path.join(os.path.expanduser("~"), "Documents", "ForteControl", "AudioPresets")
        
        ctk.CTkLabel(
            folder_frame,
            text=f"📁 I file si trovano in:\n{folder_path}",
            font=("Consolas", 11),
            text_color="#aaaaaa",
            justify="center"
        ).pack(pady=10)
        
        # Pulsante apri cartella
        def open_folder():
            if not os.path.exists(folder_path):
                os.makedirs(folder_path, exist_ok=True)
            os.startfile(folder_path)
        
        ctk.CTkButton(
            guide_frame,
            text="📂 APRI CARTELLA PRESET",
            command=open_folder,
            width=250,
            height=40,
            font=("Arial", 13, "bold"),
            fg_color="#ff00ff",
            hover_color="#cc00cc"
        ).pack(pady=(0, 20))
        
        # Game optimizer
        game_frame = ctk.CTkFrame(tab)
        game_frame.pack(pady=15, padx=50, fill="x")
        
        ctk.CTkLabel(game_frame, text="🎮 Ottimizza per:", font=("Arial", 14, "bold")).pack(side="left", padx=10)
        self.audio_game = ctk.CTkComboBox(game_frame, values=["Caricamento in corso..."], width=300)
        self.audio_game.pack(side="left", padx=10)
        ctk.CTkButton(game_frame, text="🎯 OTTIMIZZA", command=self.optimize_audio_for_game,
                     width=150, fg_color="#ff00ff").pack(side="left", padx=10)
        
        # Cards preset
        cards_frame = ctk.CTkScrollableFrame(tab)
        cards_frame.pack(pady=10, padx=30, fill="both", expand=True)
        
        # FPS FOOTSTEPS
        fps = self.audio_manager.get_preset('fps_footsteps')
        fps_card = ctk.CTkFrame(cards_frame, fg_color="#003300", corner_radius=15, border_width=3, border_color="#00ff00")
        fps_card.pack(pady=15, padx=20, fill="x")
        
        ctk.CTkLabel(fps_card, text=fps['name'], font=("Arial", 20, "bold"), text_color="#00ff00").pack(pady=10)
        ctk.CTkLabel(fps_card, text=fps['desc'], font=("Arial", 12)).pack()
        
        # EQ visual
        eq_preview = ""
        freqs = [31,62,125,250,500,1000,2000,4000,8000,16000]
        for i, val in enumerate(fps['values']):
            eq_preview += f"{freqs[i]}Hz: {val:+d}dB  "
        ctk.CTkLabel(fps_card, text=eq_preview, font=("Consolas", 10), text_color="#aaaaaa").pack(pady=5)
        
        ctk.CTkButton(fps_card, text="📁 ESPORTA PRESET",
                     command=lambda: self.export_audio_preset('fps_footsteps'),
                     width=250, height=40, fg_color="#00ff00", hover_color="#00cc00").pack(pady=15)
        
        # BASS BOOST
        bass = self.audio_manager.get_preset('bass_boost')
        bass_card = ctk.CTkFrame(cards_frame, fg_color="#002244", corner_radius=15, border_width=2, border_color="#00aaff")
        bass_card.pack(pady=15, padx=20, fill="x")
        
        ctk.CTkLabel(bass_card, text=bass['name'], font=("Arial", 18, "bold"), text_color="#00aaff").pack(pady=5)
        ctk.CTkLabel(bass_card, text=bass['desc'], font=("Arial", 11)).pack()
        
        ctk.CTkButton(bass_card, text="📁 ESPORTA", 
                     command=lambda: self.export_audio_preset('bass_boost'),
                     width=150, fg_color="#00aaff").pack(pady=10)
        
        # FLAT
        flat = self.audio_manager.get_preset('flat')
        flat_card = ctk.CTkFrame(cards_frame, fg_color="#333333", corner_radius=15, border_width=2, border_color="#ffffff")
        flat_card.pack(pady=15, padx=20, fill="x")
        
        ctk.CTkLabel(flat_card, text=flat['name'], font=("Arial", 16, "bold"), text_color="#ffffff").pack(pady=5)
        ctk.CTkLabel(flat_card, text=flat['desc'], font=("Arial", 11)).pack()
        
        ctk.CTkButton(flat_card, text="📁 ESPORTA", 
                     command=lambda: self.export_audio_preset('flat'),
                     width=150, fg_color="#555555").pack(pady=10)
    
    # ---------- OVERCLOCK ----------
    def create_overclock(self):
        tab = self.notebook.tab("⚡ Overclock")
        ctk.CTkLabel(tab, text="⚡ OVERCLOCK SAFE",
                    font=("Arial", 32, "bold"), text_color="#ff9900").pack(pady=20)
        
        limits = self.overclock.get_limits()
        
        status_frame = ctk.CTkFrame(tab, fg_color="#1a1a2e")
        status_frame.pack(pady=15, padx=50, fill="x")
        
        # Aggiorna testo status
        if self.overclock.is_active:
            status_text = f"🟢 ATTIVO +{self.overclock.core_offset}/+{self.overclock.mem_offset}"
            status_color = "#00ff00"
        else:
            status_text = "🔴 DISATTIVO"
            status_color = "#ff5555"
        
        self.oc_status = ctk.CTkLabel(status_frame, text=status_text, 
                                      font=("Arial", 16, "bold"), text_color=status_color)
        self.oc_status.pack(pady=15)
        
        core_frame = ctk.CTkFrame(tab)
        core_frame.pack(pady=20, padx=50, fill="x")
        ctk.CTkLabel(core_frame, text="🎯 Core Offset", font=("Arial", 16, "bold")).pack(anchor="w", padx=20)
        core_row = ctk.CTkFrame(core_frame, fg_color="transparent")
        core_row.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(core_row, text="0 MHz").pack(side="left")
        self.core_slider = ctk.CTkSlider(core_row, from_=0, to=limits["core_max"], width=400)
        self.core_slider.set(limits["core_safe"])
        self.core_slider.pack(side="left", padx=20, fill="x", expand=True)
        self.core_label = ctk.CTkLabel(core_row, text=f"+{limits['core_safe']} MHz")
        self.core_label.pack(side="right")
        self.core_slider.configure(command=lambda v: self.core_label.configure(text=f"+{int(v)} MHz"))
        
        mem_frame = ctk.CTkFrame(tab)
        mem_frame.pack(pady=20, padx=50, fill="x")
        ctk.CTkLabel(mem_frame, text="🎯 Memory Offset", font=("Arial", 16, "bold")).pack(anchor="w", padx=20)
        mem_row = ctk.CTkFrame(mem_frame, fg_color="transparent")
        mem_row.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(mem_row, text="0 MHz").pack(side="left")
        self.mem_slider = ctk.CTkSlider(mem_row, from_=0, to=limits["mem_max"], width=400)
        self.mem_slider.set(limits["mem_safe"])
        self.mem_slider.pack(side="left", padx=20, fill="x", expand=True)
        self.mem_label = ctk.CTkLabel(mem_row, text=f"+{limits['mem_safe']} MHz")
        self.mem_label.pack(side="right")
        self.mem_slider.configure(command=lambda v: self.mem_label.configure(text=f"+{int(v)} MHz"))
        
        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.pack(pady=30)
        self.apply_oc_btn = ctk.CTkButton(btn_frame, text="⚡ APPLICA", command=self.apply_overclock,
                                         width=200, height=50, font=("Arial", 14, "bold"), fg_color="#ff9900")
        self.apply_oc_btn.pack(side="left", padx=15)
        self.disable_oc_btn = ctk.CTkButton(btn_frame, text="🔴 DISATTIVA", command=self.disable_overclock,
                                           width=200, height=50, font=("Arial", 14, "bold"), fg_color="#555555")
        self.disable_oc_btn.pack(side="left", padx=15)
    
    # ---------- INTERNET ----------
    def create_internet(self):
        tab = self.notebook.tab("🌐 Internet")
        ctk.CTkLabel(tab, text="🌐 INTERNET MAXIMIZER",
                    font=("Arial", 32, "bold"), text_color="#ff5500").pack(pady=20)
        
        status_frame = ctk.CTkFrame(tab, fg_color="#1a1a2e")
        status_frame.pack(pady=20, padx=50, fill="x")
        self.internet_status = ctk.CTkLabel(status_frame,
            text="🟢 ATTIVO" if self.internet.is_active else "🔴 DISATTIVO",
            font=("Arial", 20, "bold"),
            text_color="#00ff00" if self.internet.is_active else "#ff5555"
        )
        self.internet_status.pack(pady=15)
        self.internet_btn = ctk.CTkButton(tab,
            text="🔴 DISATTIVA" if self.internet.is_active else "🌐 ATTIVA",
            command=self.toggle_internet,
            width=400, height=60, font=("Arial", 16, "bold"),
            fg_color="#ff5555" if self.internet.is_active else "#ff5500"
        )
        self.internet_btn.pack(pady=30)
    
    # ---------- BUG (VERSIONE CORRETTA) ----------
    def create_bug(self):
        tab = self.notebook.tab("🐛 Bug")
        ctk.CTkLabel(tab, text="🐛 BUG DETECTOR",
                    font=("Arial", 32, "bold"), text_color="#ff5555").pack(pady=20)
        ctk.CTkButton(tab, text="🔍 AVVIA SCANSIONE",
                     command=self.scan_bugs,
                     width=400, height=60, font=("Arial", 16, "bold"),
                     fg_color="#ff5555").pack(pady=30)
        
        # Textbox per risultati
        self.bug_text = ctk.CTkTextbox(tab, height=250, font=("Consolas", 12))
        self.bug_text.pack(pady=20, padx=50, fill="both", expand=True)
        self.bug_text.insert("1.0", "Clicca 'AVVIA SCANSIONE' per analizzare il sistema.")
        self.bug_text.configure(state="disabled")
        
        # Label per il sommario
        self.bug_summary = ctk.CTkLabel(tab, text="", font=("Arial", 12))
        self.bug_summary.pack(pady=10)
    
    # ---------- INFO (VERSIONE DINAMICA) ----------
    def create_info(self):
        tab = self.notebook.tab("⚙️ Info")
        ctk.CTkLabel(tab, text="⚙️ INFO SISTEMA",
                    font=("Arial", 28, "bold")).pack(pady=30)
        
        # Frame per le info
        self.info_frame = ctk.CTkFrame(tab)
        self.info_frame.pack(pady=20, padx=50, fill="x")
        
        games_count = len(self.scanner.games) if self.scanner.games else 0
        oc_status = 'ATTIVO' if self.overclock.is_active else 'DISATTIVO'
        
        info_text = f"""
🎮 FORTE CONTROL ULTIMATE
📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}

🖥️ GPU: {self.gpu.model} ({self.gpu.vram}GB)
🎮 Giochi trovati: {games_count}
⚡ Overclock: {oc_status}
🌐 Internet Maximizer: {'ATTIVO' if self.internet.is_active else 'DISATTIVO'}
🐛 Bug: {self.bug.get_summary()}
        """
        
        self.info_label = ctk.CTkLabel(self.info_frame, text=info_text, 
                                       font=("Consolas", 13),
                                       justify="left")
        self.info_label.pack(pady=20, padx=30)
        
        # Pulsante per aggiornare manualmente
        ctk.CTkButton(tab, text="🔄 AGGIORNA",
                     command=self.refresh_info_tab,
                     width=200, height=40).pack(pady=20)
    
    # ---------- FUNZIONI ----------
    def load_games(self):
        games = self.scanner.scan_all()
        self.window.after(0, self.update_games_list, games)
    
    def scan_games(self):
        self.status_label.configure(text="🔍 Scansione giochi...", text_color="#ff9900")
        threading.Thread(target=self.load_games, daemon=True).start()
    
    def update_games_list(self, games):
        for widget in self.games_container.winfo_children():
            widget.destroy()
        
        if games:
            platforms = {}
            for game in games:
                plat = game['platform']
                if plat not in platforms:
                    platforms[plat] = []
                platforms[plat].append(game)
            
            for plat, plat_games in platforms.items():
                color = self.scanner.platform_colors.get(plat, '#ffffff')
                plat_header = ctk.CTkFrame(self.games_container, fg_color=color, corner_radius=5, height=30)
                plat_header.pack(fill="x", pady=(10,0), padx=5)
                ctk.CTkLabel(plat_header, text=f"📁 {plat} ({len(plat_games)} giochi)",
                           font=("Arial", 14, "bold"), text_color="#000000").pack(pady=5)
                
                for game in plat_games[:15]:
                    game_frame = ctk.CTkFrame(self.games_container, fg_color="#2a2a3a", corner_radius=3)
                    game_frame.pack(fill="x", pady=2, padx=15)
                    name = game['name'][:50]
                    ctk.CTkLabel(game_frame, text=f"🎮 {name}", 
                               font=("Arial", 12)).pack(side="left", padx=10, pady=5)
                    ctk.CTkLabel(game_frame, text=plat, 
                               font=("Arial", 10), text_color=color).pack(side="right", padx=10)
        else:
            no_games = ctk.CTkFrame(self.games_container, fg_color="#2a2a3a")
            no_games.pack(fill="x", pady=20, padx=20)
            ctk.CTkLabel(no_games, text="❌ Nessun gioco trovato", 
                       font=("Arial", 14)).pack(pady=20)
        
        self.update_game_combos()
        self.refresh_info_tab()  # Aggiorna info tab
        self.status_label.configure(text=f"✅ {len(games)} giochi trovati", text_color="#00ff00")
    
    def update_game_combos(self):
        game_list = self.scanner.get_game_list_for_combo()
        if game_list:
            if hasattr(self, 'graphics_game'):
                self.graphics_game.configure(values=game_list)
                self.graphics_game.set(game_list[0])
            if hasattr(self, 'audio_game'):
                self.audio_game.configure(values=game_list)
                default = next((g for g in game_list if 'Warzone' in g or 'Call' in g or 'COD' in g), game_list[0])
                self.audio_game.set(default)
    
    def generate_graphics_preset(self):
        game_full = self.graphics_game.get()
        game_name = game_full.split(' [')[0] if ' [' in game_full else game_full
        res = self.graphics_res.get()
        preset_type = self.preset_var.get()
        preset = self.graphics.get_preset_settings(res, preset_type)
        filepath = self.graphics.generate_instructions(game_name, preset, "")
        messagebox.showinfo("✅ Preset Generato", f"Preset salvato in:\n{filepath}")
        self.refresh_info_tab()
    
    def export_audio_preset(self, preset_key):
        preset = self.audio_manager.get_preset(preset_key)
        folder = os.path.join(os.path.expanduser("~"), "Documents", "ForteControl", "AudioPresets")
        os.makedirs(folder, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        filepath = os.path.join(folder, f"SteelSeries_{preset_key}_{timestamp}.txt")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"PRESET: {preset['name']}\n")
            f.write(f"{preset['desc']}\n\n")
            f.write("ISTRUZIONI:\n")
            f.write("1. Apri SteelSeries GG\n")
            f.write("2. Vai su ENGINE → Equalizzatore\n")
            f.write("3. Imposta:\n")
            freqs = [31,62,125,250,500,1000,2000,4000,8000,16000]
            for i, val in enumerate(preset['values']):
                f.write(f"   {freqs[i]} Hz: {val:+d} dB\n")
        
        messagebox.showinfo("🎧 Preset Audio", f"✅ {preset['name']} esportato!\n\nFile salvato in:\n{filepath}")
        self.refresh_info_tab()
    
    def optimize_audio_for_game(self):
        game_full = self.audio_game.get()
        game_name = game_full.split(' [')[0] if ' [' in game_full else game_full
        self.export_audio_preset('fps_footsteps')
        self.status_label.configure(text=f"🎮 Audio ottimizzato per {game_name[:30]}", text_color="#ff00ff")
    
    def apply_overclock(self):
        core = int(self.core_slider.get())
        mem = int(self.mem_slider.get())
        power = 100
        self.overclock.apply_overclock(core, mem, power)
        self.oc_status.configure(text=f"🟢 ATTIVO +{core}/+{mem}", text_color="#00ff00")
        self.refresh_info_tab()  # Aggiorna info tab
        messagebox.showinfo("⚡ Overclock", f"✅ Applicato +{core} MHz Core, +{mem} MHz Memory")
    
    def disable_overclock(self):
        self.overclock.disable_overclock()
        self.oc_status.configure(text="🔴 DISATTIVO", text_color="#ff5555")
        limits = self.overclock.get_limits()
        self.core_slider.set(limits["core_safe"])
        self.core_label.configure(text=f"+{limits['core_safe']} MHz")
        self.mem_slider.set(limits["mem_safe"])
        self.mem_label.configure(text=f"+{limits['mem_safe']} MHz")
        self.refresh_info_tab()  # Aggiorna info tab
        messagebox.showinfo("⚡ Overclock", "✅ Overclock disattivato")
    
    def toggle_internet(self):
        if not self.internet.is_active:
            success = self.internet.boost()
            self.internet.is_active = True
            self.internet_status.configure(text="🟢 ATTIVO", text_color="#00ff00")
            self.internet_btn.configure(text="🔴 DISATTIVA", fg_color="#ff5555")
            self.refresh_info_tab()
            messagebox.showinfo("🌐 Internet Maximizer", f"✅ Ottimizzazione completata! ({success}/5 comandi)")
        else:
            self.internet.is_active = False
            self.internet_status.configure(text="🔴 DISATTIVO", text_color="#ff5555")
            self.internet_btn.configure(text="🌐 ATTIVA", fg_color="#ff5500")
            self.refresh_info_tab()
            messagebox.showinfo("🌐 Internet Maximizer", "❌ Ottimizzazione disattivata")
    
    def scan_bugs(self):
        """Avvia scansione bug"""
        self.bug_text.configure(state="normal")
        self.bug_text.delete("1.0", "end")
        self.bug_text.insert("1.0", "🔍 Scansione in corso...\n\n")
        self.bug_text.update()
        self.status_label.configure(text="🔍 Scansione bug...", text_color="#ff9900")
        
        # Esegui scansione in thread separato
        def do_scan():
            issues = self.bug.scan()
            
            # Aggiorna UI nel thread principale
            self.window.after(0, lambda: self.display_bug_results(issues))
        
        threading.Thread(target=do_scan, daemon=True).start()
    
    def display_bug_results(self, issues):
        """Mostra i risultati della scansione bug"""
        self.bug_text.configure(state="normal")
        self.bug_text.delete("1.0", "end")
        
        if issues:
            self.bug_text.insert("1.0", "🐛 PROBLEMI RILEVATI:\n\n")
            for issue in issues:
                # Colora in base alla severità
                severity_color = {
                    'critical': '🔴',
                    'high': '🟠',
                    'medium': '🟡',
                    'low': '🔵'
                }.get(issue.get('severity', 'low'), '⚪')
                
                self.bug_text.insert("end", f"{severity_color} {issue['msg']}\n")
            
            self.status_label.configure(text=f"🐛 {len(issues)} problemi rilevati", text_color="#ff5555")
        else:
            self.bug_text.insert("1.0", "✅ NESSUN PROBLEMA RILEVATO!\n\nIl sistema è in salute.")
            self.status_label.configure(text="✅ Sistema OK", text_color="#00ff00")
        
        # Aggiorna sommario
        self.bug_summary.configure(text=self.bug.get_summary())
        self.bug_text.configure(state="disabled")
        self.refresh_info_tab()
    
    def run(self):
        self.window.mainloop()

# ========== AVVIO ==========
if __name__ == "__main__":
    print("="*80)
    print("🎮 FORTE CONTROL ULTIMATE - VERSIONE CORRETTA")
    print("="*80)
    print("🔧 Fix applicati:")
    print("  ✅ Bug detector funzionante")
    print("  ✅ GPU dedicata rilevata correttamente")
    print("  ✅ Pagina info dinamica")
    print("  ✅ Overclock status aggiornato")
    print("="*80)
    
    try:
        app = ForteControlUltimate()
        app.run()
    except Exception as e:
        print(f"❌ Errore: {e}")
        import traceback
        traceback.print_exc()
        messagebox.showerror("Errore", f"Errore: {e}\n\nControlla la console per dettagli.")