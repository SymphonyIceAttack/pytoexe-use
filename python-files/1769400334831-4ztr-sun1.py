import time
import threading
import serial
import json
from pathlib import Path
from pynput import mouse, keyboard
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os
import sys
import ctypes
import sv_ttk

# --- Настройки ---
DEBUG = True  # Режим отладки
BAUD_RATE = 115200
SMOOTHING_VALUE = 3
CONFIG_FILE = os.path.join(os.path.expanduser("~"), "Documents", "recoil_config.json")
GUI_UPDATE_INTERVAL = 300

# --- Глобальные переменные для настроек ---
settings = {
    "PORT": 'COM3',
    "SENS": 0.6,
    "ADS_SENS": 0.8333,
    "FOV": 90.0,
    "THEME": "dark"
}

# --- Классы для управления оружием и модулями ---
class Attachment:
    def __init__(self, name, recoil_multiplier):
        self.name = name
        self.recoil_multiplier = recoil_multiplier
        self.custom_multiplier = recoil_multiplier  # Индивидуальный множитель
        self.enabled = False

    def toggle(self):
        self.enabled = not self.enabled
        return self.enabled
    
    def set_multiplier(self, value):
        self.custom_multiplier = value
        return self.custom_multiplier

class WeaponProfile:
    def __init__(self, name, crouch_pattern, standing_pattern, rpm, 
                 sensitivity=None, ads_sensitivity=None, fov=None):
        self.name = name
        self.crouch_recoil_x, self.crouch_recoil_y = crouch_pattern
        self.standing_recoil_x, self.standing_recoil_y = standing_pattern
        self.rpm = rpm
        self.time_between_shots = 60.0 / rpm
        
        # Используем глобальные настройки по умолчанию
        self.sensitivity = sensitivity if sensitivity is not None else settings["SENS"]
        self.ads_sensitivity = ads_sensitivity if ads_sensitivity is not None else settings["ADS_SENS"]
        self.fov = fov if fov is not None else settings["FOV"]
        
        self.update_move_multiplier()
        
        self.scopes = []
        self.attachments = []
        self.current_recoil_multiplier = 1.0
        self.active_scope = None
        self.scope_index = -1
    
    def update_move_multiplier(self):
        self.base_move_multiplier = -0.03 * self.sensitivity * self.ads_sensitivity * 3.6 * self.fov / 100
        self.current_move_multiplier = self.base_move_multiplier
    
    def add_scope(self, scope):
        self.scopes.append(scope)
    
    def add_attachment(self, attachment):
        self.attachments.append(attachment)
    
    def toggle_scope(self, index):
        """Переключает состояние прицела (включен/выключен)"""
        if index < 0 or index >= len(self.scopes):
            return None
            
        scope = self.scopes[index]
        
        # Переключаем состояние прицела
        scope.enabled = not scope.enabled
        
        # Если включаем прицел
        if scope.enabled:
            # Если был другой активный прицел - отключаем его
            if self.active_scope and self.active_scope != scope:
                self.active_scope.enabled = False
            self.active_scope = scope
            self.scope_index = index
        # Если отключаем прицел
        else:
            # Если отключаем текущий активный прицел
            if self.active_scope == scope:
                self.active_scope = None
                self.scope_index = -1
        
        return self.active_scope
    
    def set_scope(self, index):
        """Устанавливает прицел по индексу без изменения состояния"""
        if not self.scopes or index < 0 or index >= len(self.scopes):
            return None
            
        # Отключаем текущий активный прицел
        if self.active_scope:
            self.active_scope.enabled = False
            
        # Устанавливаем новый
        self.scope_index = index
        self.active_scope = self.scopes[self.scope_index] if index >= 0 else None
        
        return self.active_scope
    
    def update_attachment_effects(self):
        self.current_recoil_multiplier = 1.0
        
        if self.active_scope and self.active_scope.enabled:
            self.current_recoil_multiplier *= self.active_scope.custom_multiplier
        
        for attachment in self.attachments:
            if attachment.enabled:
                self.current_recoil_multiplier *= attachment.recoil_multiplier
    
    def get_active_scope_name(self):
        if self.active_scope and self.active_scope.enabled:
            return self.active_scope.name
        return "None"
    
    def get_active_attachments(self):
        active = []
        for attachment in self.attachments:
            if attachment.enabled:
                active.append(attachment.name)
        return active
    
    def get_config(self):
        return {
            "scope_index": self.scope_index,
            "scopes": [{
                "name": scope.name,
                "multiplier": scope.custom_multiplier,
                "enabled": scope.enabled
            } for scope in self.scopes],
            "silencer_enabled": self.attachments[0].enabled if len(self.attachments) > 0 else False,
            "laser_enabled": self.attachments[1].enabled if len(self.attachments) > 1 else False,
            "sensitivity": self.sensitivity,
            "ads_sensitivity": self.ads_sensitivity,
            "fov": self.fov
        }
    
    def apply_config(self, config):
        # Загружаем состояния прицелов
        if "scopes" in config:
            for i, scope_config in enumerate(config["scopes"]):
                if i < len(self.scopes):
                    self.scopes[i].custom_multiplier = scope_config.get("multiplier", self.scopes[i].recoil_multiplier)
                    self.scopes[i].enabled = scope_config.get("enabled", False)
        
        # Устанавливаем активный прицел
        if "scope_index" in config:
            scope_index = config["scope_index"]
            self.set_scope(scope_index)
            # Если прицел был включен в конфиге, активируем его
            if scope_index >= 0 and scope_index < len(self.scopes) and self.scopes[scope_index].enabled:
                self.active_scope = self.scopes[scope_index]
        
        # Загружаем состояния модулей
        if "silencer_enabled" in config and len(self.attachments) > 0:
            self.attachments[0].enabled = config["silencer_enabled"]
        
        if "laser_enabled" in config and len(self.attachments) > 1:
            self.attachments[1].enabled = config["laser_enabled"]
        
        # Загружаем специфичные для оружия настройки
        self.sensitivity = config.get("sensitivity", settings["SENS"])
        self.ads_sensitivity = config.get("ads_sensitivity", settings["ADS_SENS"])
        self.fov = config.get("fov", settings["FOV"])
        self.update_move_multiplier()
        
        self.update_attachment_effects()

# --- Глобальные переменные ---
script_enabled = False
left_button_pressed = False
right_button_pressed = False
crouch_key_pressed = False
recoil_active = False
ser = None
weapons = []
current_weapon_index = 0
last_message = "System ready"
app = None

# --- Функции для работы с конфигурацией ---
def save_config():
    config = {
        "script_enabled": script_enabled,
        "current_weapon_index": current_weapon_index,
        "global_settings": settings,
        "weapons": {}
    }
    
    for weapon in weapons:
        config["weapons"][weapon.name] = weapon.get_config()
    
    try:
        config_dir = os.path.dirname(CONFIG_FILE)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        last_message = f"Error saving config: {str(e)}"
        if app:
            app.update_status()
        return False

def load_config():
    global script_enabled, current_weapon_index, settings, last_message
    
    try:
        if not os.path.exists(CONFIG_FILE):
            return save_config()
        
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        
        script_enabled = config.get("script_enabled", False)
        current_weapon_index = config.get("current_weapon_index", 0)
        
        # Загружаем глобальные настройки
        global_settings = config.get("global_settings", {})
        settings["PORT"] = global_settings.get("PORT", 'COM3')
        settings["SENS"] = global_settings.get("SENS", 0.6)
        settings["ADS_SENS"] = global_settings.get("ADS_SENS", 0.8333)
        settings["FOV"] = global_settings.get("FOV", 90.0)
        settings["THEME"] = global_settings.get("THEME", "dark")
        
        for weapon in weapons:
            if weapon.name in config.get("weapons", {}):
                weapon_config = config["weapons"][weapon.name]
                weapon.apply_config(weapon_config)
        
        return True
    except Exception as e:
        last_message = f"Error loading config: {str(e)}"
        if app:
            app.update_status()
        return False

# --- Создание профилей оружия ---
def create_weapons():
    ak47_crouch_pattern = (
        [-0.000154824, 0.194862, 0.392001, 0.511897, 0.645919, 0.764742, 0.801947,
         0.804774, 0.907648, 0.906877, 0.870256, 0.900738, 0.841535, 0.903115,
         0.962317, 0.873101, 0.825863, 0.954904, 0.912344, 0.903819, 0.883716,
         0.943278, 0.913942, 0.857227, 0.935489, 0.909998, 0.936868, 0.91538,
         0.937147, 0.935447],
        [-1.35924, -1.3698, -1.36752, -1.36385, -1.36371, -1.34659, -1.3577,
         -1.33788, -1.33298, -1.33926, -1.33672, -1.33718, -1.32712, -1.32424,
         -1.33916, -1.31421, -1.36902, -1.38373, -1.3473, -1.35011, -1.40818,
         -1.34967, -1.38841, -1.33484, -1.35557, -1.37813, -1.35181, -1.34071,
         -1.35047, -1.32359]
    )
    ak47_standing_pattern = (
        [x * 2 for x in ak47_crouch_pattern[0]],
        [y * 2 for y in ak47_crouch_pattern[1]]
    )
    ak47 = WeaponProfile(
        name="AK-47",
        crouch_pattern=ak47_crouch_pattern,
        standing_pattern=ak47_standing_pattern,
        rpm=450
    )

    lr300_crouch_pattern = (
        [0.000462168,0.034426,-0.149605,-0.147039,0.0569801,0.0630838,0.196959,-0.108327,
        0.0968396,-0.175413,0.0389569,-0.0760862,-0.0554086,0.0397579,-0.116891,-0.130273,
        0.0264515,-0.0403351,0.052698,-0.0588954,-0.127954,-0.0103368,-0.0290586,-0.0309814,
        0.0342724,-0.053081,-0.0193513,0.1612,0.0459235,0.020249],
        [-1.237727448,-1.144310085,-1.123522866,-1.16982603,-1.185950853,-1.13696856,-1.173873366,
        -1.133846226,-1.097524521,-1.20294882,-1.107805068,-1.13839164,-1.105177797,-1.09091044,
        -1.028650464,-1.076927247,-1.090241713,-1.059846669,-1.14811803,-1.187485488,-1.115723664,
        -1.043712801,-1.075562658,-1.13741478,-1.081224828,-1.159009318,-1.08308448,-1.202353056,
        -1.158462495,-1.158462495]
    )
    lr300_standing_pattern = (
        [x * 2 for x in lr300_crouch_pattern[0]],
        [y * 2 for y in lr300_crouch_pattern[1]]
    )
    lr300 = WeaponProfile(
        name="LR300",
        crouch_pattern=lr300_crouch_pattern,
        standing_pattern=lr300_standing_pattern,
        rpm=500
    )
    
    sar_crouch_pattern = (
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [-0.90,-0.90,-0.90,-0.90,-0.90,-0.90,-0.90,-0.90,-0.90,-0.90,-0.90,-0.90,-0.90,-0.90,-0.90,-0.90]
    )
    sar_standing_pattern = (
        [x * 2 for x in sar_crouch_pattern[0]],
        [y * 2 for y in sar_crouch_pattern[1]]
    )
    sar = WeaponProfile(
        name="SAR",
        crouch_pattern=sar_crouch_pattern,
        standing_pattern=sar_standing_pattern,
        rpm=343
    )
        
    sks_crouch_pattern = (
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [-1.05,-1.05,-1.05,-1.05,-1.05,-1.05,-1.05,-1.05,-1.05,-1.05,-1.05,-1.05,-1.05,-1.05,-1.05,-1.05]
    )
    sks_standing_pattern = (
        [x * 2 for x in sks_crouch_pattern[0]],
        [y * 2 for y in sks_crouch_pattern[1]]
    )
    sks = WeaponProfile(
        name="SKS",
        crouch_pattern=sks_crouch_pattern,
        standing_pattern=sks_standing_pattern,
        rpm=400
    )
    
    thompson_crouch_pattern = (
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [-0.410422905,-0.407987991,-0.411750711,-0.416880432,-0.395337051,-0.410422905,-0.407135349,-0.410422905,-0.410422905,-0.403674732,-0.400900681,-0.410422905,-0.410422905,-0.410422905,-0.410422905,-0.418164822,-0.410422905,-0.410422905,-0.410422905,-0.410422905,-0.410422905,-0.410422905,-0.410422905,-0.410422905]
    )
    thompson_standing_pattern = (
        [x * 2 for x in thompson_crouch_pattern[0]],
        [y * 2 for y in thompson_crouch_pattern[1]]
    )
    thompson = WeaponProfile(
        name="THOMMY/SMG",
        crouch_pattern=thompson_crouch_pattern,
        standing_pattern=thompson_standing_pattern,
        rpm=462
    )
    p250_crouch_pattern = (
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [-0.6075,-0.6075,-0.6075,-0.6075,-0.6075,-0.6075,-0.6075,-0.6075,-0.6075,-0.6075]
    )
    p250_standing_pattern = (
        [x * 2 for x in p250_crouch_pattern[0]],
        [y * 2 for y in p250_crouch_pattern[1]]
    )
    p250 = WeaponProfile(
        name="P250",
        crouch_pattern=p250_crouch_pattern,
        standing_pattern=p250_standing_pattern,
        rpm=400
    )
    m92_crouch_pattern = (
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [-1.9,-1.9,-1.9,-1.9,-1.9,-1.9,-1.9,-1.9,-1.9,-1.9,-1.9,-1.9,-1.9,-1.9,-1.9]
    )
    m92_standing_pattern = (
        [x * 2 for x in m92_crouch_pattern[0]],
        [y * 2 for y in m92_crouch_pattern[1]]
    )
    m92 = WeaponProfile(
        name="M92",
        crouch_pattern=m92_crouch_pattern,
        standing_pattern=m92_standing_pattern,
        rpm=400
    )
    python_crouch_pattern = (
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [-3.5,-3.5,-3.5,-3.5,-3.5,-3.5]
    )
    python_standing_pattern = (
        [x * 2 for x in python_crouch_pattern[0]],
        [y * 2 for y in python_crouch_pattern[1]]
    )
    python = WeaponProfile(
        name="PYTHON",
        crouch_pattern=python_crouch_pattern,
        standing_pattern=python_standing_pattern,
        rpm=400
    )
    m39_crouch_pattern = (
        [0.54,0.54,0.54,0.54,0.54,0.54,0.54,0.54,0.54,0.54,0.54,0.54,0.54,0.54,0.54,0.54,0.54,0.54,0.54,0.54],
        [-0.95,-0.95,-0.95,-0.95,-0.95,-0.95,-0.95,-0.95,-0.95,-0.95,-0.95,-0.95,-0.95,-0.95,-0.95,-0.95,-0.95,-0.95,-0.95,-0.95]
    )
    m39_standing_pattern = (
        [x * 2 for x in m39_crouch_pattern[0]],
        [y * 2 for y in m39_crouch_pattern[1]]
    )
    m39 = WeaponProfile(
        name="M39",
        crouch_pattern=m39_crouch_pattern,
        standing_pattern=m39_standing_pattern,
        rpm=343
    )
    hlmg_crouch_pattern = (
        [0,-0.516458333,-0.516458333,-0.536458333,-0.536458333,-0.536458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333,-0.556458333],
        [-1.007375,-1.007375,-1.007375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375,-1.047375]
    )
    hlmg_standing_pattern = (
        [x * 2 for x in hlmg_crouch_pattern[0]],
        [y * 2 for y in hlmg_crouch_pattern[1]]
    )
    hlmg = WeaponProfile(
        name="HLMG",
        crouch_pattern=hlmg_crouch_pattern,
        standing_pattern=hlmg_standing_pattern,
        rpm=480
    )
    m249_crouch_pattern = (
        [0,0.39375,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525,0.525],
        [-0.81,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800,-1.0800]
    )
    m249_standing_pattern = (
        [x * 2 for x in m249_crouch_pattern[0]],
        [y * 2 for y in m249_crouch_pattern[1]]
    )
    m249= WeaponProfile(
        name="M249",
        crouch_pattern=m249_crouch_pattern,
        standing_pattern=m249_standing_pattern,
        rpm=500
    )
    mp5_crouch_pattern = (
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [-0.587624938,-0.587624938,-0.587624938,-0.587624938,-0.587624938,-0.587624938,-0.587624938,-0.587624938,-0.587624938,-0.587624938,-0.587624938,-0.587624938,-0.587624938,-0.587624938,-0.587624938,-0.587624938,-0.587624938,-0.587624938,-0.587624938,-0.587624938,-0.587624938,-0.587624938,-0.587624938,-0.577624938,-0.571624938,-0.567624938,-0.561624938,-0.557624938,-0.551624938]
    )
    mp5_standing_pattern = (
        [x * 2 for x in mp5_crouch_pattern[0]],
        [y * 2 for y in mp5_crouch_pattern[1]]
    )
    mp5= WeaponProfile(
        name="MP5",
        crouch_pattern=mp5_crouch_pattern,
        standing_pattern=mp5_standing_pattern,
        rpm=600
    )
    
    # Создаем список оружия
    weapons_list = [ak47, lr300, sar, sks, thompson, p250, m92, python, m39, hlmg, m249, mp5]
    
    # Добавляем прицелы и модули ко всем оружиям
    for weapon in weapons_list:
        # Добавляем прицелы
        scope1 = Attachment("Holo", 1.2)
        scope2 = Attachment("x8", 1.5)
        scope3 = Attachment("x16", 1.8)
        weapon.add_scope(scope1)
        weapon.add_scope(scope2)
        weapon.add_scope(scope3)
        
        # Добавляем модули
        silencer = Attachment("Silencer", 1.05)
        laser = Attachment("Laser", 0.95)
        weapon.add_attachment(silencer)
        weapon.add_attachment(laser)
        
        # Устанавливаем первый прицел по умолчанию
        weapon.set_scope(0)

    return weapons_list

# --- Функция сглаживания движений ---
def smooth_move(target_dx, target_dy, duration):
    step_dx = target_dx / SMOOTHING_VALUE
    step_dy = target_dy / SMOOTHING_VALUE
    step_duration = duration / SMOOTHING_VALUE
    moved_dx, moved_dy = 0, 0
    
    for _ in range(SMOOTHING_VALUE):
        move_x = round(step_dx * (_ + 1) - moved_dx)
        move_y = round(step_dy * (_ + 1) - moved_dy)
        command = f"#{int(move_x):+03d}{int(move_y):+03d}\n"
        try:
            if ser:
                ser.write(command.encode())
        except serial.SerialException:
            break
        moved_dx += move_x
        moved_dy += move_y
        time.sleep(step_duration)

# --- Функция контроля отдачи ---
def recoil_control():
    global recoil_active, last_message
    while True:
        try:
            current_weapon = weapons[current_weapon_index]
            if script_enabled and current_weapon and left_button_pressed and right_button_pressed and not recoil_active:
                recoil_active = True
                
                current_weapon.update_attachment_effects()
                
                if crouch_key_pressed:
                    recoil_x = current_weapon.crouch_recoil_x
                    recoil_y = current_weapon.crouch_recoil_y
                else:
                    recoil_x = current_weapon.standing_recoil_x
                    recoil_y = current_weapon.standing_recoil_y
                
                for i in range(len(recoil_x)): 
                    if not (left_button_pressed and right_button_pressed):
                        break
                    
                    dx = recoil_x[i] * current_weapon.current_recoil_multiplier
                    dy = recoil_y[i] * current_weapon.current_recoil_multiplier
                    
                    dx = dx / current_weapon.current_move_multiplier
                    dy = dy / current_weapon.current_move_multiplier
                    
                    smooth_move(dx, dy, current_weapon.time_between_shots)
                
                recoil_active = False
            time.sleep(0.01)
        except Exception as e:
            last_message = f"Recoil error: {str(e)}"
            if app:
                app.update_status()
            time.sleep(1)

# --- Обработчик событий мыши ---
def on_click(x, y, button, pressed):
    global left_button_pressed, right_button_pressed
    if button == mouse.Button.left:
        left_button_pressed = pressed
    elif button == mouse.Button.right:
        right_button_pressed = pressed

# --- Обработчик событий клавиатуры ---
def on_press(key):
    global crouch_key_pressed, current_weapon_index, last_message
    
    try:
        # Приседание
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl:
            crouch_key_pressed = True
        
        # Выбор оружия на Num0-Num9
        if hasattr(key, 'vk'):
            # Num0 = 96, Num1 = 97, ..., Num9 = 105
            if 96 <= key.vk <= 105:
                weapon_index = key.vk - 96
                if weapon_index < len(weapons):
                    select_weapon(weapon_index)
    except Exception as e:
        last_message = f"Key error: {str(e)}"
        if app:
            app.update_status()

def on_release(key):
    global crouch_key_pressed
    if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl:
        crouch_key_pressed = False

# --- GUI-ориентированные функции управления ---
def toggle_script():
    global script_enabled, last_message
    script_enabled = not script_enabled
    last_message = f"Script {'ENABLED' if script_enabled else 'DISABLED'}"
    if app:
        app.update_status()
    save_config()

def select_weapon(index):
    global current_weapon_index, last_message
    if 0 <= index < len(weapons):
        current_weapon_index = index
        last_message = f"Selected: {weapons[current_weapon_index].name}"
        if app:
            app.weapon_name.configure(text=weapons[current_weapon_index].name)
            app.update_scopes()
            app.update_attachments()
            app.update_status()
        save_config()

def next_weapon():
    select_weapon((current_weapon_index + 1) % len(weapons))

def prev_weapon():
    select_weapon((current_weapon_index - 1) % len(weapons))

def toggle_scope(index):
    global last_message
    weapon = weapons[current_weapon_index]
    scope = weapon.toggle_scope(index)
    
    if scope and scope.enabled:
        last_message = f"{weapon.name}: Sight -> {scope.name}"
    else:
        last_message = f"{weapon.name}: Sight -> Off"
    
    if app:
        app.update_scopes()
        app.update_status()
    save_config()

def toggle_attachment(attachment_index):
    global last_message
    weapon = weapons[current_weapon_index]
    if attachment_index < len(weapon.attachments):
        attachment = weapon.attachments[attachment_index]
        state = attachment.toggle()
        weapon.update_attachment_effects()
        status = "ON" if state else "OFF"
        last_message = f"{weapon.name}: {attachment.name} -> {status}"
        if app:
            btn = app.attachment_btns[attachment_index]
            text = f"{attachment.name} {'✅' if state else '❌'}"
            btn.configure(
                text=text,
                style="Attachment.TButton" if state else "TButton"
            )
            app.update_status()
        save_config()

def update_weapon_settings(sens=None, ads_sens=None, fov=None):
    weapon = weapons[current_weapon_index]
    if sens is not None:
        weapon.sensitivity = sens
    if ads_sens is not None:
        weapon.ads_sensitivity = ads_sens
    if fov is not None:
        weapon.fov = fov
    
    weapon.update_move_multiplier()
    save_config()

def update_global_settings(port=None, sens=None, ads_sens=None, fov=None):
    global settings
    
    if port is not None:
        settings["PORT"] = port
    
    if sens is not None:
        settings["SENS"] = sens
    
    if ads_sens is not None:
        settings["ADS_SENS"] = ads_sens
    
    if fov is not None:
        settings["FOV"] = fov
    
    # Обновляем настройки для всех оружий
    for weapon in weapons:
        if sens is not None:
            weapon.sensitivity = sens
        if ads_sens is not None:
            weapon.ads_sensitivity = ads_sens
        if fov is not None:
            weapon.fov = fov
        weapon.update_move_multiplier()
    
    save_config()
    return True

def reconnect_serial():
    global ser, last_message
    try:
        if ser:
            ser.close()
        ser = serial.Serial(settings["PORT"], BAUD_RATE, timeout=1)
        last_message = f"Connected to {settings['PORT']} at {BAUD_RATE} baud"
        return True
    except serial.SerialException as e:
        last_message = f"Error: Cannot open port {settings['PORT']}: {e}"
        ser = None
        return False

def toggle_theme():
    global settings
    settings["THEME"] = "light" if settings["THEME"] == "dark" else "dark"
    
    # Применяем новую тему
    if settings["THEME"] == "light":
        sv_ttk.use_light_theme()
    else:
        sv_ttk.use_dark_theme()
        
    save_config()
    if app:
        app.update_ui_theme()

# --- GUI приложение с Sun Valley Theme ---
class RecoilControlApp:
    def __init__(self, root):
        self.root = root
        
        # Установка размеров окна
        self.root.geometry("620x520")
        self.root.minsize(700, 520)  # Минимальный размер окна
        self.root.resizable(True, True)
        
        # Основные фреймы
        main_panel = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        main_panel.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Левая панель - оружие
        self.left_panel = ttk.Frame(main_panel)
        main_panel.add(self.left_panel, weight=1)
        
        # Правая панель - настройки и статус
        self.right_panel = ttk.Frame(main_panel)
        main_panel.add(self.right_panel, weight=1)
        
        self.status_frame = ttk.Frame(root)
        self.status_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Создаем стили для цветовых схем
        self.style = ttk.Style()
        self.style.configure("Bordered.TFrame", borderwidth=1, relief="solid")
        
        # --- Левая панель: Оружие и модули ---
        # Заголовок с именем пользователя
        self.user_label = ttk.Label(
            self.left_panel, 
            text="@maximix2009kid", 
            font=("Segoe UI", 12, "bold")
        )
        self.user_label.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        # Weapon Profiles
        self.weapon_label = ttk.Label(
            self.left_panel, 
            text="WEAPON PROFILES", 
            font=("Segoe UI", 11, "bold")
        )
        self.weapon_label.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        # Панель выбора оружия
        weapon_select_frame = ttk.Frame(self.left_panel)
        weapon_select_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(
            weapon_select_frame,
            text="◀",
            command=prev_weapon,
            width=3
        ).pack(side=tk.LEFT, padx=5)
        
        # Название оружия
        self.weapon_name = ttk.Label(
            weapon_select_frame, 
            text=weapons[current_weapon_index].name, 
            font=("Segoe UI", 12, "bold")
        )
        self.weapon_name.pack(side=tk.LEFT, padx=5, expand=True)
        
        ttk.Button(
            weapon_select_frame,
            text="▶",
            command=next_weapon,
            width=3
        ).pack(side=tk.RIGHT, padx=5)
        
        # Панель прицелов
        scopes_frame = ttk.LabelFrame(self.left_panel, text="SIGHTS", padding=10)
        scopes_frame.pack(fill=tk.X, padx=10, pady=10, ipadx=5, ipady=5)
        
        self.scope_btns = []
        for i, scope in enumerate(weapons[current_weapon_index].scopes):
            btn_frame = ttk.Frame(scopes_frame)
            btn_frame.pack(fill=tk.X, padx=5, pady=5)
            
            # Иконка прицела
            icon_label = ttk.Label(btn_frame, text="🔭", font=("Arial", 14))
            icon_label.pack(side=tk.LEFT, padx=5)
            
            # Основная кнопка прицела
            btn = ttk.Button(
                btn_frame,
                text=scope.name,
                command=lambda idx=i: toggle_scope(idx),
                width=10
            )
            btn.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            self.scope_btns.append(btn)
            
            # Кнопка настройки множителя
            config_btn = ttk.Button(
                btn_frame,
                text="⚙️",
                command=lambda idx=i: self.configure_scope(idx),
                width=2
            )
            config_btn.pack(side=tk.RIGHT, padx=5)
        
        # Панель модулей
        attachments_frame = ttk.LabelFrame(self.left_panel, text="ATTACHMENTS", padding=10)
        attachments_frame.pack(fill=tk.X, padx=10, pady=10, ipadx=5, ipady=5)
        
        self.attachment_btns = []
        for i, attachment in enumerate(weapons[current_weapon_index].attachments):
            btn_frame = ttk.Frame(attachments_frame)
            btn_frame.pack(fill=tk.X, padx=5, pady=5)
            
            # Иконка модуля
            icon_label = ttk.Label(btn_frame, text="⚙️", font=("Arial", 14))
            icon_label.pack(side=tk.LEFT, padx=5)
            
            btn = ttk.Button(
                btn_frame,
                text=f"{attachment.name} {'✅' if attachment.enabled else '❌'}",
                command=lambda idx=i: toggle_attachment(idx),
                width=15
            )
            btn.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            self.attachment_btns.append(btn)
        
        # --- Правая панель: Настройки и статус ---
        # Кнопки управления в правой панели
        control_frame = ttk.Frame(self.right_panel)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Кнопка переключения темы
        self.theme_btn = ttk.Button(
            control_frame,
            text="☀️" if settings["THEME"] == "dark" else "🌙",
            command=toggle_theme,
            width=3
        )
        self.theme_btn.pack(side=tk.RIGHT, padx=5)
        
        # Кнопка включения/выключения
        self.toggle_btn = ttk.Button(
            control_frame,
            text="DISABLED",
            command=toggle_script,
            width=10
        )
        self.toggle_btn.pack(side=tk.RIGHT, padx=10)
        
        # Settings & Status
        self.settings_label = ttk.Label(
            self.right_panel, 
            text="SETTINGS & STATUS", 
            font=("Segoe UI", 11, "bold")
        )
        self.settings_label.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        # Карточки настроек
        settings_card = ttk.LabelFrame(self.right_panel, text="Configuration", padding=10)
        settings_card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10, ipadx=5, ipady=5)
        
        # Сетка настроек
        settings_grid = ttk.Frame(settings_card)
        settings_grid.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Индикатор подключения - с обводкой
        connection_frame = ttk.Frame(settings_grid, style="Bordered.TFrame")
        connection_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
        ttk.Label(connection_frame, text="Status:", font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=5)
        self.connection_status = ttk.Label(
            connection_frame,
            text="●",
            font=("Arial", 14, "bold"),
            foreground="#4CAF50" if ser and ser.is_open else "#F44336"
        )
        self.connection_status.pack(side=tk.LEFT, padx=5)
        self.connection_text = ttk.Label(
            connection_frame,
            text="Connected" if ser and ser.is_open else "Disconnected",
            font=("Segoe UI", 10)
        )
        self.connection_text.pack(side=tk.LEFT, padx=2)
        
        # Настройка порта - с обводкой
        port_frame = ttk.Frame(settings_grid, style="Bordered.TFrame")
        port_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        ttk.Label(port_frame, text="PORT:", font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=5)
        self.port_value = ttk.Label(port_frame, text=settings["PORT"], font=("Segoe UI", 10))
        self.port_value.pack(side=tk.LEFT, padx=5)
        ttk.Button(
            port_frame,
            text="✏️",
            command=lambda: self.edit_setting("PORT", "Serial Port", settings["PORT"])
        ).pack(side=tk.RIGHT, padx=5)
        
        # Настройка чувствительности - с обводкой
        sens_frame = ttk.Frame(settings_grid, style="Bordered.TFrame")
        sens_frame.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
        ttk.Label(sens_frame, text="SENS:", font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=5)
        self.sens_value = ttk.Label(sens_frame, text=f"{settings['SENS']:.2f}", font=("Segoe UI", 10))
        self.sens_value.pack(side=tk.LEFT, padx=5)
        ttk.Button(
            sens_frame,
            text="✏️",
            command=lambda: self.edit_setting("SENS", "Sensitivity", settings["SENS"])
        ).pack(side=tk.RIGHT, padx=5)
        
        # Настройка ADS чувствительности - с обводкой
        ads_frame = ttk.Frame(settings_grid, style="Bordered.TFrame")
        ads_frame.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")
        ttk.Label(ads_frame, text="ADS_SENS:", font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=5)
        self.ads_value = ttk.Label(ads_frame, text=f"{settings['ADS_SENS']:.4f}", font=("Segoe UI", 10))
        self.ads_value.pack(side=tk.LEFT, padx=5)
        ttk.Button(
            ads_frame,
            text="✏️",
            command=lambda: self.edit_setting("ADS_SENS", "ADS Sensitivity", settings["ADS_SENS"])
        ).pack(side=tk.RIGHT, padx=5)
        
        # Настройка FOV - с обводкой
        fov_frame = ttk.Frame(settings_grid, style="Bordered.TFrame")
        fov_frame.grid(row=2, column=1, padx=5, pady=5, sticky="nsew")
        ttk.Label(fov_frame, text="FOV:", font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=5)
        self.fov_value = ttk.Label(fov_frame, text=f"{settings['FOV']:.1f}", font=("Segoe UI", 10))
        self.fov_value.pack(side=tk.LEFT, padx=5)
        ttk.Button(
            fov_frame,
            text="✏️",
            command=lambda: self.edit_setting("FOV", "Field of View", settings["FOV"])
        ).pack(side=tk.RIGHT, padx=5)
        
        # Кнопка переподключения - с обводкой
        reconnect_frame = ttk.Frame(settings_grid, style="Bordered.TFrame")
        reconnect_frame.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
        # Центрируем кнопку
        self.reconnect_btn = ttk.Button(
            reconnect_frame,
            text="Reconnect Device",
            command=self.reconnect_device,
            width=15
        )
        self.reconnect_btn.pack(pady=5, anchor="center")
        
        # Статус бар
        self.status_var = tk.StringVar(value=last_message)
        self.status_bar = ttk.Label(
            self.status_frame, 
            textvariable=self.status_var, 
            font=("Segoe UI", 9),
            anchor=tk.CENTER
        )
        self.status_bar.pack(fill=tk.X, padx=10, pady=5)
        
        # Настройка сетки
        settings_grid.columnconfigure(0, weight=1)
        settings_grid.columnconfigure(1, weight=1)
        settings_grid.rowconfigure(0, weight=1)
        settings_grid.rowconfigure(1, weight=1)
        settings_grid.rowconfigure(2, weight=1)
        settings_grid.rowconfigure(3, weight=1)
        
        # Применяем тему после создания всех виджетов
        self.update_ui_theme()
        
        # Обновление статуса
        self.update_status()
        self.root.after(GUI_UPDATE_INTERVAL, self.update_status)
    
    def update_ui_theme(self):
        # Определяем цвета в зависимости от темы
        if settings["THEME"] == "dark":
            text_color = "white"
            border_color = "white"
            sv_ttk.use_dark_theme()
        else:
            text_color = "black"
            border_color = "black"
            sv_ttk.use_light_theme()
        
        # Обновляем цвет текста для всех виджетов
        widgets = [
            self.user_label, self.weapon_label, self.weapon_name,
            self.settings_label, self.port_value, self.sens_value,
            self.ads_value, self.fov_value, self.connection_text,
            self.status_bar
        ]
        
        for widget in widgets:
            widget.configure(foreground=text_color)
        
        # Обновляем цвет обводки для фреймов
        self.style.configure("Bordered.TFrame", bordercolor=border_color)
        
        # Обновляем кнопку переключения скрипта
        if script_enabled:
            self.toggle_btn.configure(style="Accent.TButton")
        else:
            self.toggle_btn.configure(style="")
        
        # Обновляем тему кнопки
        self.theme_btn.configure(text="☀️" if settings["THEME"] == "dark" else "🌙")
        
        # Обновляем все элементы интерфейса
        self.root.update()
    
    def configure_scope(self, scope_index):
        """Настройка множителя для конкретного прицела"""
        weapon = weapons[current_weapon_index]
        if scope_index < 0 or scope_index >= len(weapon.scopes):
            return
            
        scope = weapon.scopes[scope_index]
        
        # Запрашиваем новое значение у пользователя
        new_value = simpledialog.askfloat(
            "Scope Multiplier",
            f"Enter multiplier for {scope.name}:",
            initialvalue=scope.custom_multiplier,
            minvalue=0.1,
            maxvalue=30.0,
            parent=self.root
        )
        
        if new_value is not None:
            scope.set_multiplier(new_value)
            weapon.update_attachment_effects()
            
            global last_message
            last_message = f"{weapon.name}: {scope.name} multiplier set to {new_value:.2f}"
            
            # Обновляем отображение
            self.update_scopes()
            self.update_status()
            save_config()
    
    def update_scopes(self):
        weapon = weapons[current_weapon_index]
        for i, scope in enumerate(weapon.scopes):
            if i < len(self.scope_btns):
                btn = self.scope_btns[i]
                
                # Добавляем отображение множителя
                multiplier_text = f" ({scope.custom_multiplier:.2f})"
                
                # Добавляем индикатор состояния
                state_indicator = " ✅" if scope.enabled else " ❌"
                
                # Обновляем текст кнопки
                btn.configure(text=f"{scope.name}{multiplier_text}{state_indicator}")
                
                # Обновляем стиль кнопки
                if scope.enabled:
                    btn.configure(style="Accent.TButton")
                else:
                    btn.configure(style="TButton")
    
    def update_attachments(self):
        weapon = weapons[current_weapon_index]
        for i, attachment in enumerate(weapon.attachments):
            if i < len(self.attachment_btns):
                btn = self.attachment_btns[i]
                text = f"{attachment.name} {'✅' if attachment.enabled else '❌'}"
                btn.configure(text=text)
    
    def update_status(self):
        # Обновляем кнопку переключения
        if script_enabled:
            self.toggle_btn.configure(text="ENABLED", style="Accent.TButton")
        else:
            self.toggle_btn.configure(text="DISABLED", style="")
        
        # Обновляем статус подключения
        if ser and ser.is_open:
            self.connection_status.configure(foreground="#4CAF50")
            self.connection_text.configure(text="Connected")
        else:
            self.connection_status.configure(foreground="#F44336")
            self.connection_text.configure(text="Disconnected")
        
        # Обновляем значения настроек
        self.port_value.configure(text=settings["PORT"])
        self.sens_value.configure(text=f"{settings['SENS']:.2f}")
        self.ads_value.configure(text=f"{settings['ADS_SENS']:.4f}")
        self.fov_value.configure(text=f"{settings['FOV']:.1f}")
        
        # Обновляем статус бар
        self.status_var.set(last_message)
        
        # Планируем следующее обновление
        self.root.after(GUI_UPDATE_INTERVAL, self.update_status)
    
    def edit_setting(self, setting_name, display_name, current_value):
        # Запрос нового значения у пользователя
        new_value = simpledialog.askstring(
            f"Edit {display_name}",
            f"Enter new value for {display_name}:",
            initialvalue=str(current_value),
            parent=self.root
        )
        
        if new_value is not None:
            try:
                # Преобразование в правильный тип данных
                if setting_name in ["SENS", "ADS_SENS", "FOV"]:
                    new_value = float(new_value)
                
                # Обновление глобальных настроек
                if setting_name == "PORT":
                    update_global_settings(port=new_value)
                elif setting_name == "SENS":
                    update_global_settings(sens=new_value)
                elif setting_name == "ADS_SENS":
                    update_global_settings(ads_sens=new_value)
                elif setting_name == "FOV":
                    update_global_settings(fov=new_value)
                
                last_message = f"{display_name} updated to {new_value}"
                self.update_status()
            except ValueError:
                last_message = f"Invalid value for {display_name}"
                self.update_status()
    
    def reconnect_device(self):
        if reconnect_serial():
            last_message = f"Reconnected to {settings['PORT']}"
        else:
            last_message = f"Failed to reconnect to {settings['PORT']}"
        self.update_status()

# --- Основная функция ---
def main():
    global weapons, ser, app, last_message, settings, DEBUG
    
    # Скрыть консоль в Windows
    if sys.platform == "win32" and not DEBUG:
        try:
            whnd = ctypes.windll.kernel32.GetConsoleWindow()
            if whnd:
                ctypes.windll.user32.ShowWindow(whnd, 0)
        except:
            pass
    
    # Инициализация оружия
    weapons = create_weapons()
    
    # Загружаем или создаем конфигурацию
    if not load_config():
        save_config()
    
    # Инициализация последовательного порта
    try:
        ser = serial.Serial(settings["PORT"], BAUD_RATE, timeout=1)
        last_message = f"Connected to {settings['PORT']} at {BAUD_RATE} baud"
    except serial.SerialException as e:
        last_message = f"Error: Cannot open port {settings['PORT']}: {e}"
        ser = None
    
    # Создаем GUI
    root = tk.Tk()
    root.title("Sun Project")
    
    # Применяем тему ДО создания элементов интерфейса
    if settings["THEME"] == "light":
        sv_ttk.use_light_theme()
    else:
        sv_ttk.use_dark_theme()
    
    app = RecoilControlApp(root)
    
    # Запуск обработчиков событий
    mouse_listener = mouse.Listener(on_click=on_click)
    keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    mouse_listener.start()
    keyboard_listener.start()
    
    # Запуск потока контроля отдачи
    recoil_thread = threading.Thread(target=recoil_control, daemon=True)
    recoil_thread.start()
    
    # Обработчик закрытия окна
    def on_closing():
        save_config()
        root.destroy()
        os._exit(0)
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()