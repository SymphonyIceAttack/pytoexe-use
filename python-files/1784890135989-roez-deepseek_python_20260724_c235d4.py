import pygame
import numpy as np
import struct
import sys
import os
import json
import threading
import time
from pathlib import Path
from collections import defaultdict
import tkinter as tk
from tkinter import filedialog, ttk

# Инициализация Pygame
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

# --- Константы DS ---
DS_SCREEN_WIDTH = 256
DS_SCREEN_HEIGHT = 192
SCALE = 2
WINDOW_WIDTH = DS_SCREEN_WIDTH * SCALE
WINDOW_HEIGHT = (DS_SCREEN_HEIGHT * 2) * SCALE

# --- Цвета для отладки ---
COLORS = {
    'WHITE': (255, 255, 255),
    'BLACK': (0, 0, 0),
    'RED': (255, 0, 0),
    'GREEN': (0, 255, 0),
    'BLUE': (0, 0, 255),
    'YELLOW': (255, 255, 0),
    'CYAN': (0, 255, 255),
    'MAGENTA': (255, 0, 255),
}

# --- Класс для эмуляции сенсорного экрана ---
class TouchScreen:
    def __init__(self):
        self.touched = False
        self.x = 0
        self.y = 0
        self.pressure = 0
        
    def update(self, mouse_pos, mouse_pressed):
        """Обновляет состояние тач-скрина"""
        if mouse_pressed[0]:
            # Проверяем, находится ли курсор на нижнем экране
            if mouse_pos[1] > DS_SCREEN_HEIGHT * SCALE:
                self.touched = True
                self.x = int(mouse_pos[0] / SCALE)
                self.y = int((mouse_pos[1] - DS_SCREEN_HEIGHT * SCALE) / SCALE)
                self.pressure = 1.0
                
                # Ограничиваем координаты
                self.x = max(0, min(DS_SCREEN_WIDTH - 1, self.x))
                self.y = max(0, min(DS_SCREEN_HEIGHT - 1, self.y))
            else:
                self.touched = False
                self.pressure = 0.0
        else:
            self.touched = False
            self.pressure = 0.0

# --- Класс для управления сохранениями ---
class SaveManager:
    def __init__(self, rom_name):
        self.rom_name = rom_name
        self.save_dir = "saves"
        os.makedirs(self.save_dir, exist_ok=True)
        
    def save_state(self, memory, arm9, arm7):
        """Сохраняет состояние игры"""
        save_data = {
            'memory': list(memory.ram),
            'arm9_regs': arm9.regs,
            'arm9_pc': arm9.pc,
            'arm9_sp': arm9.sp,
            'arm9_lr': arm9.lr,
            'arm7_regs': arm7.regs,
            'arm7_pc': arm7.pc,
            'arm7_sp': arm7.sp,
            'arm7_lr': arm7.lr,
            'timestamp': time.time()
        }
        
        filename = f"{self.save_dir}/{self.rom_name}_state.json"
        with open(filename, 'w') as f:
            json.dump(save_data, f)
        print(f"Сохранение создано: {filename}")
        
    def load_state(self, memory, arm9, arm7):
        """Загружает состояние игры"""
        filename = f"{self.save_dir}/{self.rom_name}_state.json"
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                save_data = json.load(f)
                
            memory.ram = bytearray(save_data['memory'])
            arm9.regs = save_data['arm9_regs']
            arm9.pc = save_data['arm9_pc']
            arm9.sp = save_data['arm9_sp']
            arm9.lr = save_data['arm9_lr']
            arm7.regs = save_data['arm7_regs']
            arm7.pc = save_data['arm7_pc']
            arm7.sp = save_data['arm7_sp']
            arm7.lr = save_data['arm7_lr']
            
            print(f"Сохранение загружено: {filename}")
            return True
        return False

# --- Класс для отладки ---
class Debugger:
    def __init__(self):
        self.breakpoints = set()
        self.step_mode = False
        self.running = True
        
    def add_breakpoint(self, address):
        """Добавляет точку останова"""
        self.breakpoints.add(address)
        
    def remove_breakpoint(self, address):
        """Удаляет точку останова"""
        if address in self.breakpoints:
            self.breakpoints.remove(address)
            
    def check_breakpoint(self, pc):
        """Проверяет, есть ли точка останова по адресу"""
        return pc in self.breakpoints

# --- Класс для эмуляции звука ---
class SoundProcessor:
    def __init__(self):
        self.sample_rate = 44100
        self.buffer_size = 1024
        self.sound_enabled = True
        
        # 16 звуковых каналов DS
        self.channels = [{
            'enabled': False,
            'frequency': 0,
            'volume': 0,
            'pan': 0,
            'waveform': None,
            'position': 0,
            'length': 0
        } for _ in range(16)]
        
        # Генерация базовых волн
        self.generate_waveforms()
        
    def generate_waveforms(self):
        """Генерирует базовые звуковые волны"""
        self.wave_square = np.sin(np.linspace(0, 4*np.pi, 256))
        self.wave_saw = np.linspace(-1, 1, 256)
        self.wave_triangle = np.abs(np.linspace(-1, 1, 256)) * 2 - 1
        self.wave_sine = np.sin(np.linspace(0, 2*np.pi, 256))
        
    def generate_sample(self):
        """Генерирует один звуковой сэмпл"""
        if not self.sound_enabled:
            return 0
            
        sample = 0
        for i, channel in enumerate(self.channels):
            if channel['enabled'] and channel['waveform'] is not None:
                # Простая генерация звука
                wave = channel['waveform']
                pos = int(channel['position']) % len(wave)
                sample += wave[pos] * channel['volume'] * 0.1
                channel['position'] += channel['frequency'] / self.sample_rate
                
        # Ограничиваем амплитуду
        return max(-1.0, min(1.0, sample))
        
    def get_audio_buffer(self, size):
        """Возвращает буфер звуковых данных"""
        buffer = np.zeros(size * 2, dtype=np.int16)
        for i in range(size):
            sample = self.generate_sample()
            buffer[i*2] = int(sample * 32767)
            buffer[i*2+1] = int(sample * 32767)
        return buffer

# --- Расширенный загрузчик NDS ROM ---
class ExtendedNDSLoader:
    def __init__(self):
        self.rom_data = None
        self.header = {}
        self.banner_data = None
        self.icon_data = None
        
    def load_rom(self, filepath):
        """Загружает NDS файл и читает полный заголовок"""
        try:
            with open(filepath, 'rb') as f:
                self.rom_data = f.read()
                
            # Читаем полный заголовок NDS
            self.header = {
                'game_title': self.rom_data[0x00:0x0C].decode('ascii', errors='ignore').strip('\x00'),
                'game_code': self.rom_data[0x0C:0x10].decode('ascii', errors='ignore'),
                'maker_code': self.rom_data[0x10:0x12].decode('ascii', errors='ignore'),
                'unit_code': self.rom_data[0x12],
                'device_capacity': self.rom_data[0x13],
                'arm9_rom_offset': struct.unpack('<I', self.rom_data[0x20:0x24])[0],
                'arm9_entry_address': struct.unpack('<I', self.rom_data[0x24:0x28])[0],
                'arm9_ram_address': struct.unpack('<I', self.rom_data[0x28:0x2C])[0],
                'arm9_size': struct.unpack('<I', self.rom_data[0x2C:0x30])[0],
                'arm7_rom_offset': struct.unpack('<I', self.rom_data[0x30:0x34])[0],
                'arm7_entry_address': struct.unpack('<I', self.rom_data[0x34:0x38])[0],
                'arm7_ram_address': struct.unpack('<I', self.rom_data[0x38:0x3C])[0],
                'arm7_size': struct.unpack('<I', self.rom_data[0x3C:0x40])[0],
                'filename_offset': struct.unpack('<I', self.rom_data[0x40:0x44])[0],
                'filename_size': struct.unpack('<I', self.rom_data[0x44:0x48])[0],
                'icon_offset': struct.unpack('<I', self.rom_data[0x48:0x4C])[0],
                'icon_size': struct.unpack('<I', self.rom_data[0x4C:0x50])[0],
                'nitro_rom_offset': struct.unpack('<I', self.rom_data[0x50:0x54])[0],
                'nitro_rom_size': struct.unpack('<I', self.rom_data[0x54:0x58])[0],
                'arm9_overlay_offset': struct.unpack('<I', self.rom_data[0x58:0x5C])[0],
                'arm9_overlay_size': struct.unpack('<I', self.rom_data[0x5C:0x60])[0],
                'arm7_overlay_offset': struct.unpack('<I', self.rom_data[0x60:0x64])[0],
                'arm7_overlay_size': struct.unpack('<I', self.rom_data[0x64:0x68])[0],
                'card_control_1': struct.unpack('<I', self.rom_data[0x68:0x6C])[0],
                'card_control_2': struct.unpack('<I', self.rom_data[0x6C:0x70])[0],
                'banner_offset': struct.unpack('<I', self.rom_data[0x70:0x74])[0],
                'banner_size': struct.unpack('<I', self.rom_data[0x74:0x78])[0],
                'secure_area_crc': struct.unpack('<I', self.rom_data[0x7C:0x80])[0],
                'logo_rom_offset': struct.unpack('<I', self.rom_data[0x90:0x94])[0],
                'logo_size': struct.unpack('<I', self.rom_data[0x94:0x98])[0],
            }
            
            # Извлекаем баннер и иконку если есть
            if self.header['banner_offset'] and self.header['banner_size']:
                offset = self.header['banner_offset']
                size = min(self.header['banner_size'], 0x400)  # 1KB
                self.banner_data = self.rom_data[offset:offset+size]
                
            if self.header['icon_offset'] and self.header['icon_size']:
                offset = self.header['icon_offset']
                size = min(self.header['icon_size'], 0x2000)  # 8KB
                self.icon_data = self.rom_data[offset:offset+size]
                
            print(f"✅ Загружена игра: {self.header['game_title']}")
            print(f"📋 Код игры: {self.header['game_code']}")
            print(f"🏢 Производитель: {self.header['maker_code']}")
            print(f"🎯 ARM9 вход: 0x{self.header['arm9_entry_address']:08X}")
            print(f"💾 Размер ARM9: {self.header['arm9_size']} байт")
            print(f"💾 Размер ARM7: {self.header['arm7_size']} байт")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка загрузки ROM: {e}")
            return False
    
    def get_arm9_binary(self):
        """Извлекает бинарный код ARM9 из ROM"""
        offset = self.header['arm9_rom_offset']
        size = self.header['arm9_size']
        return self.rom_data[offset:offset+size]
    
    def get_arm7_binary(self):
        """Извлекает бинарный код ARM7 из ROM"""
        offset = self.header['arm7_rom_offset']
        size = self.header['arm7_size']
        return self.rom_data[offset:offset+size]
    
    def get_logo_data(self):
        """Извлекает логотип Nintendo из ROM"""
        if self.header['logo_rom_offset'] and self.header['logo_size']:
            offset = self.header['logo_rom_offset']
            size = self.header['logo_size']
            return self.rom_data[offset:offset+size]
        return None

# --- Расширенный интерпретатор ARM ---
class ExtendedARMInterpreter:
    def __init__(self, memory, is_arm9=True):
        self.regs = [0] * 16  # R0-R15
        self.sp = 0x03000000  # Stack Pointer
        self.lr = 0x00000000  # Link Register
        self.pc = 0x00000000  # Program Counter
        self.cpsr = 0x00000000  # Current Program Status Register
        self.spsr = 0x00000000  # Saved Program Status Register
        self.memory = memory
        self.is_arm9 = is_arm9
        self.running = True
        self.instruction_count = 0
        self.bios_loaded = False
        
        # Режимы процессора
        self.mode = 'USER'
        self.modes = {
            0b10000: 'USER',
            0b10001: 'FIQ',
            0b10010: 'IRQ',
            0b10011: 'SUPERVISOR',
            0b10111: 'ABORT',
            0b11011: 'UNDEFINED',
            0b11111: 'SYSTEM'
        }
        
        # Создаем BIOS
        self.create_bios()
        self.setup_interrupts()
        
    def create_bios(self):
        """Создает полный BIOS для загрузки игр"""
        bios_code = bytearray(0x8000)  # 32KB BIOS
        
        # Reset вектор (0x00000000)
        bios_code[0x00:0x04] = struct.pack('<I', 0xEA000007)  # B 0x1C
        
        # Undefined Instruction вектор (0x00000004)
        bios_code[0x04:0x08] = struct.pack('<I', 0xEA000006)  # B 0x18
        
        # SWI вектор (0x00000008)
        bios_code[0x08:0x0C] = struct.pack('<I', 0xEA000005)  # B 0x14
        
        # Prefetch Abort вектор (0x0000000C)
        bios_code[0x0C:0x10] = struct.pack('<I', 0xEA000004)  # B 0x10
        
        # Data Abort вектор (0x00000010)
        bios_code[0x10:0x14] = struct.pack('<I', 0xEA000003)  # B 0x0C
        
        # IRQ вектор (0x00000018)
        bios_code[0x18:0x1C] = struct.pack('<I', 0xE59FF018)  # LDR PC, [PC,#0x18]
        
        # FIQ вектор (0x0000001C)
        bios_code[0x1C:0x20] = struct.pack('<I', 0xE59FF014)  # LDR PC, [PC,#0x14]
        
        # Базовые прерывания
        bios_code[0x40:0x44] = struct.pack('<I', 0xE3A00000)  # MOV R0, #0
        bios_code[0x44:0x48] = struct.pack('<I', 0xE12FFF1E)  # BX LR
        
        # Функции BIOS для DS
        # SoftReset (0x0000)
        bios_code[0x0000:0x0004] = struct.pack('<I', 0xEA000005)  # B 0x14
        
        # RegisterRamReset (0x0004)
        bios_code[0x0004:0x0008] = struct.pack('<I', 0xE3A00000)  # MOV R0, #0
        bios_code[0x0008:0x000C] = struct.pack('<I', 0xE12FFF1E)  # BX LR
        
        # Halt (0x0008)
        bios_code[0x0008:0x000C] = struct.pack('<I', 0xEAFFFFFE)  # B .
        
        # Sleep (0x000C)
        bios_code[0x000C:0x0010] = struct.pack('<I', 0xEAFFFFFE)  # B .
        
        # IntrWait (0x0010)
        bios_code[0x0010:0x0014] = struct.pack('<I', 0xE3A00000)  # MOV R0, #0
        bios_code[0x0014:0x0018] = struct.pack('<I', 0xE12FFF1E)  # BX LR
        
        # VBlankIntrWait (0x0014)
        bios_code[0x0014:0x0018] = struct.pack('<I', 0xE3A00000)  # MOV R0, #0
        bios_code[0x0018:0x001C] = struct.pack('<I', 0xE12FFF1E)  # BX LR
        
        # Sqrt (0x0018)
        bios_code[0x0018:0x001C] = struct.pack('<I', 0xE3A00001)  # MOV R0, #1
        bios_code[0x001C:0x0020] = struct.pack('<I', 0xE12FFF1E)  # BX LR
        
        # Div (0x001C)
        bios_code[0x001C:0x0020] = struct.pack('<I', 0xE3A00001)  # MOV R0, #1
        bios_code[0x0020:0x0024] = struct.pack('<I', 0xE12FFF1E)  # BX LR
        
        # Регистрируем BIOS в памяти
        self.memory.write(0x00000000, bios_code)
        self.bios_loaded = True
        print("🧠 BIOS загружен")
        
    def setup_interrupts(self):
        """Настраивает обработку прерываний"""
        # Устанавливаем обработчики прерываний
        self.interrupt_handlers = {
            'VBLANK': 0x00000040,
            'HBLANK': 0x00000044,
            'TIMER0': 0x00000048,
            'TIMER1': 0x0000004C,
            'TIMER2': 0x00000050,
            'TIMER3': 0x00000054,
            'DMA0': 0x00000058,
            'DMA1': 0x0000005C,
            'DMA2': 0x00000060,
            'DMA3': 0x00000064,
            'KEYPAD': 0x00000068,
            'GBA_SLOT': 0x0000006C,
            'GBA_SPI': 0x00000070,
            'GBA_SERIAL': 0x00000074,
            'GBA_RTC': 0x00000078,
            'GBA_SOUND': 0x0000007C
        }

    def execute_arm_instruction(self, instruction):
        """Выполняет ARM инструкцию с расширенной поддержкой"""
        if instruction == 0x0:
            return
            
        # Определяем тип инструкции
        cond = (instruction >> 28) & 0xF
        if not self.check_condition(cond):
            return
            
        opcode = (instruction >> 24) & 0xFF
        opcode2 = (instruction >> 20) & 0xFF
        
        # Data Processing (MOV, ADD, SUB, CMP, etc.)
        if opcode2 & 0x80:
            self.execute_data_processing(instruction)
            
        # Load/Store
        elif opcode & 0x08:
            self.execute_load_store(instruction)
            
        # Branch
        elif opcode2 & 0x70 == 0x50:
            self.execute_branch(instruction)
            
        # Software Interrupt
        elif opcode2 == 0xF0:
            self.execute_swi(instruction)
            
        # Multiply
        elif opcode2 & 0xF0 == 0x90:
            self.execute_multiply(instruction)
            
        # Status Register Transfer
        elif opcode2 == 0x10:
            self.execute_status_transfer(instruction)
            
        # Coprocessor Instructions
        elif opcode == 0x0E:
            self.execute_coprocessor(instruction)
            
        # Exception Generating Instructions
        else:
            # Неизвестная инструкция
            pass

    def check_condition(self, cond):
        """Проверяет условие выполнения инструкции"""
        if cond == 0xE:  # AL (Always)
            return True
        elif cond == 0xF:  # NV (Never)
            return False
            
        # Получаем флаги состояния
        n = (self.cpsr >> 31) & 1
        z = (self.cpsr >> 30) & 1
        c = (self.cpsr >> 29) & 1
        v = (self.cpsr >> 28) & 1
        
        # Проверяем условие
        if cond == 0x0:  # EQ (Equal)
            return z == 1
        elif cond == 0x1:  # NE (Not Equal)
            return z == 0
        elif cond == 0x2:  # CS/HS (Carry Set)
            return c == 1
        elif cond == 0x3:  # CC/LO (Carry Clear)
            return c == 0
        elif cond == 0x4:  # MI (Minus)
            return n == 1
        elif cond == 0x5:  # PL (Plus)
            return n == 0
        elif cond == 0x6:  # VS (Overflow)
            return v == 1
        elif cond == 0x7:  # VC (No Overflow)
            return v == 0
        elif cond == 0x8:  # HI (Unsigned Higher)
            return c == 1 and z == 0
        elif cond == 0x9:  # LS (Unsigned Lower or Same)
            return c == 0 or z == 1
        elif cond == 0xA:  # GE (Greater or Equal)
            return n == v
        elif cond == 0xB:  # LT (Less Than)
            return n != v
        elif cond == 0xC:  # GT (Greater Than)
            return z == 0 and n == v
        elif cond == 0xD:  # LE (Less or Equal)
            return z == 1 or n != v
        return False

    def execute_data_processing(self, instruction):
        """Выполняет инструкции обработки данных"""
        opcode = (instruction >> 21) & 0xF
        dest = (instruction >> 12) & 0xF
        src1 = (instruction >> 16) & 0xF
        operand = self.get_operand(instruction)
        
        # Получаем значение первого операнда
        rn = self.regs[src1]
        
        # Выполняем операцию
        if opcode == 0x0:  # AND
            result = rn & operand
            self.update_flags(result, instruction)
            self.regs[dest] = result
        elif opcode == 0x1:  # EOR
            result = rn ^ operand
            self.update_flags(result, instruction)
            self.regs[dest] = result
        elif opcode == 0x2:  # SUB
            result = rn - operand
            self.update_flags(result, instruction)
            self.regs[dest] = result
        elif opcode == 0x3:  # RSB
            result = operand - rn
            self.update_flags(result, instruction)
            self.regs[dest] = result
        elif opcode == 0x4:  # ADD
            result = rn + operand
            self.update_flags(result, instruction)
            self.regs[dest] = result
        elif opcode == 0x5:  # ADC
            carry = (self.cpsr >> 29) & 1
            result = rn + operand + carry
            self.update_flags(result, instruction)
            self.regs[dest] = result
        elif opcode == 0x6:  # SBC
            carry = (self.cpsr >> 29) & 1
            result = rn - operand - (1 - carry)
            self.update_flags(result, instruction)
            self.regs[dest] = result
        elif opcode == 0x7:  # RSC
            carry = (self.cpsr >> 29) & 1
            result = operand - rn - (1 - carry)
            self.update_flags(result, instruction)
            self.regs[dest] = result
        elif opcode == 0x8:  # TST
            result = rn & operand
            self.update_flags(result, instruction)
        elif opcode == 0x9:  # TEQ
            result = rn ^ operand
            self.update_flags(result, instruction)
        elif opcode == 0xA:  # CMP
            result = rn - operand
            self.update_flags(result, instruction)
        elif opcode == 0xB:  # CMN
            result = rn + operand
            self.update_flags(result, instruction)
        elif opcode == 0xC:  # ORR
            result = rn | operand
            self.update_flags(result, instruction)
            self.regs[dest] = result
        elif opcode == 0xD:  # MOV
            result = operand
            self.update_flags(result, instruction)
            if dest == 15:  # PC
                self.pc = result - 4
            else:
                self.regs[dest] = result
        elif opcode == 0xE:  # BIC
            result = rn & ~operand
            self.update_flags(result, instruction)
            self.regs[dest] = result
        elif opcode == 0xF:  # MVN
            result = ~operand
            self.update_flags(result, instruction)
            if dest == 15:
                self.pc = result - 4
            else:
                self.regs[dest] = result

    def get_operand(self, instruction):
        """Получает операнд для инструкций данных"""
        if instruction & 0x02000000:  # Immediate
            immed = instruction & 0xFF
            rotate = ((instruction >> 8) & 0xF) * 2
            operand = (immed >> rotate) | (immed << (32 - rotate))
            return operand & 0xFFFFFFFF
        else:  # Register
            reg = instruction & 0xF
            shift_type = (instruction >> 5) & 0x3
            shift_amount = (instruction >> 7) & 0x1F
            
            value = self.regs[reg]
            
            if shift_amount == 0:
                return value
                
            if shift_type == 0:  # LSL
                return (value << shift_amount) & 0xFFFFFFFF
            elif shift_type == 1:  # LSR
                return (value >> shift_amount) & 0xFFFFFFFF
            elif shift_type == 2:  # ASR
                return (value >> shift_amount) | (value & 0x80000000)
            elif shift_type == 3:  # ROR
                return ((value >> shift_amount) | (value << (32 - shift_amount))) & 0xFFFFFFFF
            return value

    def execute_load_store(self, instruction):
        """Выполняет инструкции загрузки/сохранения"""
        dest = (instruction >> 12) & 0xF
        base = (instruction >> 16) & 0xF
        offset = instruction & 0xFFF
        address = self.regs[base]
        
        # Вычисляем адрес с учетом смещения
        if instruction & 0x01000000:  # Pre-indexed
            if instruction & 0x00800000:  # Add
                address += offset
            else:  # Subtract
                address -= offset
        
        if instruction & 0x00100000:  # Load
            if instruction & 0x00400000:  # Byte
                if dest != 15:
                    self.regs[dest] = self.memory.read_byte(address)
                else:
                    self.pc = self.memory.read_byte(address) - 4
            else:  # Word
                if dest != 15:
                    self.regs[dest] = self.memory.read_word(address)
                else:
                    self.pc = self.memory.read_word(address) - 4
        else:  # Store
            if instruction & 0x00400000:  # Byte
                self.memory.write_byte(address, self.regs[dest] & 0xFF)
            else:  # Word
                self.memory.write_word(address, self.regs[dest])
                
        # Post-indexed addressing
        if not (instruction & 0x01000000):
            if instruction & 0x00800000:
                self.regs[base] += offset
            else:
                self.regs[base] -= offset

    def execute_branch(self, instruction):
        """Выполняет инструкции перехода"""
        offset = instruction & 0x00FFFFFF
        if offset & 0x00800000:  # Negative
            offset |= 0xFF000000
            
        # B или BL
        if instruction & 0x00F00000 == 0x00B00000:  # BL
            self.lr = self.pc - 4
            self.pc += (offset << 2) - 4
        else:  # B
            self.pc += (offset << 2) - 4

    def execute_swi(self, instruction):
        """Выполняет программное прерывание"""
        swi_number = instruction & 0x00FFFFFF
        
        # Сохраняем состояние
        self.spsr = self.cpsr
        self.cpsr = (self.cpsr & 0xFFFFFFE0) | 0b10011  # Supervisor mode
        self.lr = self.pc - 4
        
        # Обработка SWI
        if swi_number == 0x0000:  # SoftReset
            self.pc = self.memory.read_word(0x00000000)
        elif swi_number == 0x0001:  # RegisterRamReset
            # Сброс регистров
            pass
        elif swi_number == 0x0002:  # Halt
            self.running = False
        elif swi_number == 0x0003:  # Sleep
            pass
        elif swi_number == 0x0004:  # IntrWait
            pass
        elif swi_number == 0x0005:  # VBlankIntrWait
            pass
        elif swi_number == 0x0006:  # Div
            self.regs[0] = self.regs[0] // self.regs[1]
            self.regs[1] = self.regs[0] % self.regs[1]
        elif swi_number == 0x0007:  # DivArm
            pass
        elif swi_number == 0x0008:  # Sqrt
            self.regs[0] = int(np.sqrt(self.regs[0]))
        else:
            # Неизвестный SWI - игнорируем
            pass
            
        self.pc = self.lr

    def execute_multiply(self, instruction):
        """Выполняет инструкции умножения"""
        dest = (instruction >> 16) & 0xF
        src1 = (instruction >> 8) & 0xF
        src2 = instruction & 0xF
        acc = (instruction >> 12) & 0xF
        
        if instruction & 0x00200000:  # MUL/MLA
            result = self.regs[src1] * self.regs[src2]
            if instruction & 0x00400000:  # MLA
                result += self.regs[acc]
            self.regs[dest] = result & 0xFFFFFFFF
            self.update_flags(result, instruction)

    def execute_status_transfer(self, instruction):
        """Выполняет передачу статусных регистров"""
        if instruction & 0x00400000:  # MRS
            dest = (instruction >> 12) & 0xF
            if instruction & 0x00200000:  # SPSR
                self.regs[dest] = self.spsr
            else:  # CPSR
                self.regs[dest] = self.cpsr
        else:  # MSR
            if instruction & 0x00200000:  # SPSR
                self.spsr = self.get_psr_operand(instruction)
            else:  # CPSR
                self.cpsr = self.get_psr_operand(instruction)

    def execute_coprocessor(self, instruction):
        """Выполняет инструкции сопроцессора"""
        # Для DS это в основном CDP, LDC, STC, MCR, MRC
        # Мы игнорируем их в базовой эмуляции
        pass

    def get_psr_operand(self, instruction):
        """Получает операнд для инструкций PSR"""
        if instruction & 0x02000000:  # Immediate
            return (instruction & 0xFF) << 8
        else:  # Register
            return self.regs[instruction & 0xF]

    def update_flags(self, result, instruction):
        """Обновляет флаги состояния если нужно"""
        if instruction & 0x00100000:  # S bit set
            if result == 0:
                self.cpsr |= 0x40000000  # Z flag
            else:
                self.cpsr &= ~0x40000000
            if result & 0x80000000:
                self.cpsr |= 0x80000000  # N flag
            else:
                self.cpsr &= ~0x80000000
            # C и V флаги требуют более сложного расчета
            # для упрощения мы их устанавливаем приблизительно
            self.cpsr |= 0x20000000  # C flag (Carry)
            self.cpsr &= ~0x10000000  # V flag (Overflow)

    def step(self):
        """Выполняет один шаг процессора"""
        if not self.running:
            return
            
        # Читаем инструкцию из памяти
        try:
            instruction = self.memory.read_word(self.pc)
        except:
            self.running = False
            return
            
        # Выполняем инструкцию
        self.execute_arm_instruction(instruction)
        self.pc += 4
        self.instruction_count += 1
        
        # Ограничиваем количество инструкций
        if self.instruction_count > 1000000:
            self.running = False

# --- Расширенный менеджер памяти ---
class ExtendedMemoryManager:
    def __init__(self):
        self.ram = bytearray(0x04000000)  # 64MB RAM
        self.rom = bytearray(0x01000000)  # 16MB ROM кэш
        self.vram = bytearray(0x01000000)  # 16MB VRAM
        self.oam = bytearray(0x00000400)   # 1KB OAM
        self.palette = bytearray(0x00000400)  # 1KB Palette
        self.wram = bytearray(0x00004000)  # 16KB WRAM
        self.iram = bytearray(0x00004000)  # 16KB IRAM
        self.bios = bytearray(0x00008000)  # 32KB BIOS
        
        # Карта памяти для быстрого доступа
        self.memory_map = {
            (0x00000000, 0x00008000): self.bios,
            (0x02000000, 0x04000000): self.ram,
            (0x03000000, 0x03004000): self.wram,
            (0x03800000, 0x03804000): self.iram,
            (0x05000000, 0x05000400): self.palette,
            (0x06000000, 0x07000000): self.vram,
            (0x07000000, 0x07000400): self.oam,
        }
        
        # Счетчики обращений для отладки
        self.access_count = defaultdict(int)
        
    def write(self, address, data):
        """Записывает данные в память"""
        if isinstance(data, (bytearray, bytes)):
            for i, byte in enumerate(data):
                self.write_byte(address + i, byte)
        else:
            self.write_word(address, data)
            
    def write_byte(self, address, value):
        """Записывает байт по адресу"""
        for (start, end), memory in self.memory_map.items():
            if start <= address < end:
                memory[address - start] = value & 0xFF
                self.access_count[address] += 1
                return
                
        # Игнорируем запись по недопустимому адресу
        pass
        
    def write_word(self, address, value):
        """Записывает 32-битное слово по адресу"""
        self.write_byte(address, value & 0xFF)
        self.write_byte(address + 1, (value >> 8) & 0xFF)
        self.write_byte(address + 2, (value >> 16) & 0xFF)
        self.write_byte(address + 3, (value >> 24) & 0xFF)
        
    def read_word(self, address):
        """Читает 32-битное слово по адресу"""
        return self.read_byte(address) | \
               (self.read_byte(address + 1) << 8) | \
               (self.read_byte(address + 2) << 16) | \
               (self.read_byte(address + 3) << 24)
               
    def read_byte(self, address):
        """Читает байт по адресу"""
        for (start, end), memory in self.memory_map.items():
            if start <= address < end:
                self.access_count[address] += 1
                return memory[address - start]
                
        # Возвращаем 0 для недопустимых адресов
        return 0
        
    def get_memory_stats(self):
        """Возвращает статистику использования памяти"""
        stats = {
            'total_accesses': sum(self.access_count.values()),
            'ram_usage': sum(1 for b in self.ram if b != 0) / len(self.ram),
            'vram_usage': sum(1 for b in self.vram if b != 0) / len(self.vram),
            'oam_usage': sum(1 for b in self.oam if b != 0) / len(self.oam),
        }
        return stats

# --- Расширенный графический процессор ---
class ExtendedGraphicsProcessor:
    def __init__(self, memory):
        self.memory = memory
        self.screen_top = np.zeros((DS_SCREEN_HEIGHT, DS_SCREEN_WIDTH, 3), dtype=np.uint8)
        self.screen_bottom = np.zeros((DS_SCREEN_HEIGHT, DS_SCREEN_WIDTH, 3), dtype=np.uint8)
        self.bg_layers = [np.zeros((DS_SCREEN_HEIGHT, DS_SCREEN_WIDTH, 3), dtype=np.uint8) for _ in range(4)]
        self.sprite_layer = np.zeros((DS_SCREEN_HEIGHT, DS_SCREEN_WIDTH, 3), dtype=np.uint8)
        
        # Режимы отображения
        self.display_modes = {
            'top': 0,  # 0-3 для разных режимов
            'bottom': 0
        }
        
        # Параметры рендеринга
        self.bg_enabled = [True, True, True, True]
        self.sprite_enabled = True
        self.blend_mode = 0  # 0: normal, 1: alpha, 2: additive
        
    def render(self):
        """Рендерит оба экрана"""
        # Сбрасываем буферы
        self.screen_top.fill(0)
        self.screen_bottom.fill(0)
        
        # Рендерим фоновые слои для верхнего экрана
        for i in range(4):
            if self.bg_enabled[i]:
                self.render_bg_layer(i, self.screen_top)
                
        # Рендерим спрайты для верхнего экрана
        if self.sprite_enabled:
            self.render_sprites(self.screen_top)
            
        # Копируем на нижний экран (для простоты)
        self.screen_bottom = self.screen_top.copy()
        
        # Применяем эффекты
        self.apply_effects()
        
        return self.screen_top, self.screen_bottom
        
    def render_bg_layer(self, layer, screen):
        """Рендерит фоновый слой"""
        # Простой рендеринг из VRAM
        vram = self.memory.vram
        for y in range(DS_SCREEN_HEIGHT):
            for x in range(DS_SCREEN_WIDTH):
                idx = (y * DS_SCREEN_WIDTH + x) * 2
                if idx + 1 < len(vram):
                    pixel = (vram[idx] | (vram[idx + 1] << 8))
                    r = ((pixel >> 11) & 0x1F) * 8
                    g = ((pixel >> 6) & 0x1F) * 8
                    b = ((pixel >> 1) & 0x1F) * 8
                    
                    # Простое наложение слоев
                    if layer == 0:
                        screen[y][x] = [r, g, b]
                    elif layer == 1:
                        screen[y][x] = [r//2 + screen[y][x][0]//2,
                                       g//2 + screen[y][x][1]//2,
                                       b//2 + screen[y][x][2]//2]
                        
    def render_sprites(self, screen):
        """Рендерит спрайты из OAM"""
        oam = self.memory.oam
        for i in range(0, len(oam), 8):
            if i + 7 >= len(oam):
                break
                
            # Читаем атрибуты спрайта
            attr0 = (oam[i] | (oam[i+1] << 8))
            attr1 = (oam[i+2] | (oam[i+3] << 8))
            attr2 = (oam[i+4] | (oam[i+5] << 8))
            
            if not (attr0 & 0x0200):  # Невидимый
                continue
                
            x = attr1 & 0x1FF
            y = attr0 & 0xFF
            
            # Простое отображение квадратов
            size = 8 << ((attr0 >> 14) & 0x3)
            color = attr2 & 0x3F
            
            if 0 <= x < DS_SCREEN_WIDTH and 0 <= y < DS_SCREEN_HEIGHT:
                for dy in range(size):
                    for dx in range(size):
                        sx = x + dx
                        sy = y + dy
                        if 0 <= sx < DS_SCREEN_WIDTH and 0 <= sy < DS_SCREEN_HEIGHT:
                            # Используем цвет из палитры
                            pal_idx = color * 2
                            if pal_idx + 1 < len(self.memory.palette):
                                pixel = (self.memory.palette[pal_idx] | 
                                        (self.memory.palette[pal_idx + 1] << 8))
                                r = ((pixel >> 11) & 0x1F) * 8
                                g = ((pixel >> 6) & 0x1F) * 8
                                b = ((pixel >> 1) & 0x1F) * 8
                                # Накладываем спрайт поверх фона
                                if screen[sy][sx][0] == 0 and screen[sy][sx][1] == 0 and screen[sy][sx][2] == 0:
                                    screen[sy][sx] = [r, g, b]
                                    
    def apply_effects(self):
        """Применяет визуальные эффекты"""
        # Простые эффекты для демонстрации
        if self.blend_mode == 1:  # Alpha blending
            for y in range(DS_SCREEN_HEIGHT):
                for x in range(DS_SCREEN_WIDTH):
                    alpha = (x + y) / (DS_SCREEN_WIDTH + DS_SCREEN_HEIGHT)
                    self.screen_top[y][x] = [int(c * (1 + alpha) / 2) for c in self.screen_top[y][x]]
                    self.screen_bottom[y][x] = [int(c * (1 - alpha) / 2) for c in self.screen_bottom[y][x]]

# --- GUI для выбора ROM ---
class ROMSelector:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Nintendo DS Эмулятор - Выбор ROM")
        self.root.geometry("600x400")
        self.root.resizable(False, False)
        
        # Стиль
        style = ttk.Style()
        style.theme_use('clam')
        
        # Заголовок
        title = tk.Label(self.root, text="Nintendo DS Эмулятор", 
                        font=('Arial', 20, 'bold'))
        title.pack(pady=20)
        
        # Инструкция
        instruction = tk.Label(self.root, text="Выберите ROM файл для загрузки", 
                              font=('Arial', 12))
        instruction.pack(pady=10)
        
        # Кнопка выбора файла
        select_btn = tk.Button(self.root, text="Выбрать ROM файл", 
                               command=self.select_rom,
                               font=('Arial', 12), bg='#4CAF50', fg='white',
                               padx=20, pady=10)
        select_btn.pack(pady=20)
        
        # Поле для отображения пути
        self.path_var = tk.StringVar()
        self.path_var.set("ROM не выбран")
        path_label = tk.Label(self.root, textvariable=self.path_var, 
                             font=('Arial', 10), wraplength=500)
        path_label.pack(pady=10)
        
        # Информация об игре
        self.info_text = tk.Text(self.root, height=8, width=70, 
                                font=('Arial', 10))
        self.info_text.pack(pady=10)
        self.info_text.insert('1.0', "Информация об игре появится здесь...")
        self.info_text.config(state='disabled')
        
        # Кнопка запуска
        self.start_btn = tk.Button(self.root, text="Запустить игру", 
                                   command=self.start_emulator,
                                   font=('Arial', 14), bg='#2196F3', fg='white',
                                   padx=30, pady=10, state='disabled')
        self.start_btn.pack(pady=10)
        
        self.selected_rom = None
        
    def select_rom(self):
        """Открывает диалог выбора файла"""
        filetypes = [
            ('NDS ROM files', '*.nds'),
            ('All files', '*.*')
        ]
        filename = filedialog.askopenfilename(title='Выберите ROM файл',
                                            filetypes=filetypes)
        if filename:
            self.selected_rom = filename
            self.path_var.set(f"Выбран: {os.path.basename(filename)}")
            self.start_btn.config(state='normal')
            self.load_rom_info(filename)
            
    def load_rom_info(self, filename):
        """Загружает информацию о ROM"""
        try:
            with open(filename, 'rb') as f:
                data = f.read()
                
            # Читаем заголовок
            title = data[0x00:0x0C].decode('ascii', errors='ignore').strip('\x00')
            code = data[0x0C:0x10].decode('ascii', errors='ignore')
            maker = data[0x10:0x12].decode('ascii', errors='ignore')
            arm9_off = struct.unpack('<I', data[0x20:0x24])[0]
            arm9_size = struct.unpack('<I', data[0x2C:0x30])[0]
            arm7_off = struct.unpack('<I', data[0x30:0x34])[0]
            arm7_size = struct.unpack('<I', data[0x3C:0x40])[0]
            
            info = f"""
📌 Название: {title}
📋 Код: {code}
🏢 Производитель: {maker}
📁 Размер: {len(data) / 1024 / 1024:.2f} MB
💾 ARM9: {arm9_size / 1024:.2f} KB (offset: 0x{arm9_off:X})
💾 ARM7: {arm7_size / 1024:.2f} KB (offset: 0x{arm7_off:X})
"""
            self.info_text.config(state='normal')
            self.info_text.delete('1.0', tk.END)
            self.info_text.insert('1.0', info)
            self.info_text.config(state='disabled')
            
        except Exception as e:
            self.info_text.config(state='normal')
            self.info_text.delete('1.0', tk.END)
            self.info_text.insert('1.0', f"Ошибка чтения ROM: {e}")
            self.info_text.config(state='disabled')
            
    def start_emulator(self):
        """Запускает эмулятор с выбранным ROM"""
        if self.selected_rom:
            self.root.destroy()
            run_emulator(self.selected_rom)

# --- Основной класс эмулятора ---
class ExtendedDSEmulator:
    def __init__(self):
        self.memory = ExtendedMemoryManager()
        self.loader = ExtendedNDSLoader()
        self.gpu = ExtendedGraphicsProcessor(self.memory)
        self.touch = TouchScreen()
        self.sound = SoundProcessor()
        self.debugger = Debugger()
        self.save_manager = None
        
        self.arm9 = None
        self.arm7 = None
        self.running = True
        self.rom_loaded = False
        self.paused = False
        self.fast_forward = False
        self.speed = 1.0
        
        # Статистика
        self.frame_count = 0
        self.fps = 0
        self.last_fps_update = time.time()
        self.fps_counter = 0
        
        # Настройка экрана
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Nintendo DS Эмулятор v2.0")
        
        # Шрифты для отображения информации
        self.font_small = pygame.font.Font(None, 16)
        self.font_medium = pygame.font.Font(None, 24)
        self.font_large = pygame.font.Font(None, 32)
        
        # Иконка для окна (создаем из пикселей)
        self.create_window_icon()
        
    def create_window_icon(self):
        """Создает иконку окна"""
        icon_size = 32
        icon = pygame.Surface((icon_size, icon_size))
        icon.fill((0, 0, 0))
        
        # Рисуем простой логотип DS
        pygame.draw.rect(icon, (0, 0, 255), (5, 5, 22, 22), 2)
        pygame.draw.rect(icon, (0, 0, 255), (8, 8, 16, 16), 1)
        pygame.draw.line(icon, (255, 0, 0), (10, 10), (22, 22), 2)
        pygame.draw.line(icon, (255, 0, 0), (22, 10), (10, 22), 2)
        
        pygame.display.set_icon(icon)
        
    def load_game(self, rom_path):
        """Загружает игру и настраивает процессоры"""
        if not self.loader.load_rom(rom_path):
            return False
            
        # Получаем бинарный код
        arm9_code = self.loader.get_arm9_binary()
        arm7_code = self.loader.get_arm7_binary()
        
        # Загружаем код в память
        arm9_addr = self.loader.header['arm9_ram_address']
        arm7_addr = self.loader.header['arm7_ram_address']
        
        self.memory.write(arm9_addr, arm9_code)
        self.memory.write(arm7_addr, arm7_code)
        
        # Создаем процессоры
        self.arm9 = ExtendedARMInterpreter(self.memory, True)
        self.arm9.pc = self.loader.header['arm9_entry_address']
        
        self.arm7 = ExtendedARMInterpreter(self.memory, False)
        self.arm7.pc = self.loader.header['arm7_entry_address']
        
        # Создаем менеджер сохранений
        game_name = self.loader.header['game_title'].strip()
        if not game_name:
            game_name = os.path.basename(rom_path).replace('.nds', '')
        self.save_manager = SaveManager(game_name)
        
        self.rom_loaded = True
        print("✅ Игра успешно загружена!")
        
        # Загружаем сохранение если есть
        if self.save_manager.load_state(self.memory, self.arm9, self.arm7):
            print("💾 Сохранение восстановлено")
            
        return True
        
    def handle_events(self):
        """Обрабатывает события ввода"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_F1:
                    self.reset_game()
                elif event.key == pygame.K_F2:
                    self.save_state()
                elif event.key == pygame.K_F3:
                    self.load_state()
                elif event.key == pygame.K_F4:
                    self.paused = not self.paused
                elif event.key == pygame.K_F5:
                    self.fast_forward = not self.fast_forward
                elif event.key == pygame.K_F6:
                    self.sound.sound_enabled = not self.sound.sound_enabled
                elif event.key == pygame.K_F7:
                    self.toggle_debug()
                elif event.key == pygame.K_F8:
                    self.toggle_fps()
                    
    def save_state(self):
        """Сохраняет текущее состояние игры"""
        if self.save_manager and self.arm9 and self.arm7:
            self.save_manager.save_state(self.memory, self.arm9, self.arm7)
            
    def load_state(self):
        """Загружает сохраненное состояние игры"""
        if self.save_manager and self.arm9 and self.arm7:
            self.save_manager.load_state(self.memory, self.arm9, self.arm7)
            
    def reset_game(self):
        """Перезапускает текущую игру"""
        if self.rom_loaded:
            print("🔄 Перезапуск игры...")
            arm9_code = self.loader.get_arm9_binary()
            arm7_code = self.loader.get_arm7_binary()
            
            arm9_addr = self.loader.header['arm9_ram_address']
            arm7_addr = self.loader.header['arm7_ram_address']
            
            self.memory.write(arm9_addr, arm9_code)
            self.memory.write(arm7_addr, arm7_code)
            
            self.arm9 = ExtendedARMInterpreter(self.memory, True)
            self.arm9.pc = self.loader.header['arm9_entry_address']
            
            self.arm7 = ExtendedARMInterpreter(self.memory, False)
            self.arm7.pc = self.loader.header['arm7_entry_address']
            
    def toggle_debug(self):
        """Включает/выключает отладку"""
        self.debugger.running = not self.debugger.running
        
    def toggle_fps(self):
        """Включает/выключает отображение FPS"""
        # Просто переключаем отображение информации
        pass
        
    def get_input_state(self):
        """Получает состояние кнопок"""
        keys = pygame.key.get_pressed()
        mouse = pygame.mouse.get_pressed()
        mouse_pos = pygame.mouse.get_pos()
        
        # Обновляем тач-скрин
        self.touch.update(mouse_pos, mouse)
        
        # Карта клавиш
        key_map = {
            pygame.K_z: 0,  # A
            pygame.K_x: 1,  # B
            pygame.K_c: 2,  # X
            pygame.K_v: 3,  # Y
            pygame.K_RETURN: 4,  # Start
            pygame.K_RSHIFT: 5,  # Select
            pygame.K_a: 6,  # L
            pygame.K_s: 7,  # R
            pygame.K_UP: 8,
            pygame.K_DOWN: 9,
            pygame.K_LEFT: 10,
            pygame.K_RIGHT: 11,
        }
        
        # Создаем битовую маску клавиш
        input_state = 0
        for key, bit in key_map.items():
            if keys[key]:
                input_state |= (1 << bit)
                
        # Добавляем тач-скрин
        if self.touch.touched:
            input_state |= (1 << 12)
            
        return input_state
        
    def render_frame(self):
        """Рендерит один кадр"""
        # Получаем состояние кнопок
        input_state = self.get_input_state()
        
        # Обновляем звук
        if self.sound.sound_enabled:
            audio_buffer = self.sound.get_audio_buffer(256)
            # В реальном эмуляторе здесь была бы отправка звука
            # pygame.mixer.sound.Sound(audio_buffer).play()
        
        # Рендерим графику
        top, bottom = self.gpu.render()
        
        # Конвертируем для Pygame
        surf_top = pygame.surfarray.make_surface(top.swapaxes(0, 1))
        surf_bottom = pygame.surfarray.make_surface(bottom.swapaxes(0, 1))
        
        # Масштабируем
        surf_top = pygame.transform.scale(surf_top, (DS_SCREEN_WIDTH * SCALE, DS_SCREEN_HEIGHT * SCALE))
        surf_bottom = pygame.transform.scale(surf_bottom, (DS_SCREEN_WIDTH * SCALE, DS_SCREEN_HEIGHT * SCALE))
        
        # Отображаем
        self.screen.fill((0, 0, 0))
        self.screen.blit(surf_top, (0, 0))
        self.screen.blit(surf_bottom, (0, DS_SCREEN_HEIGHT * SCALE))
        
        # Отображаем информацию
        self.draw_overlay()
        
        # Обновляем FPS
        self.fps_counter += 1
        if time.time() - self.last_fps_update >= 1.0:
            self.fps = self.fps_counter
            self.fps_counter = 0
            self.last_fps_update = time.time()
            
        return True
        
    def draw_overlay(self):
        """Рисует информацию поверх экрана"""
        # FPS
        fps_text = self.font_small.render(f"FPS: {self.fps}", True, COLORS['WHITE'])
        self.screen.blit(fps_text, (10, 10))
        
        if self.paused:
            pause_text = self.font_large.render("PAUSED", True, COLORS['RED'])
            self.screen.blit(pause_text, (WINDOW_WIDTH//2 - pause_text.get_width()//2, WINDOW_HEIGHT//2 - 50))
            
        if self.fast_forward:
            ff_text = self.font_medium.render("FAST FORWARD", True, COLORS['YELLOW'])
            self.screen.blit(ff_text, (WINDOW_WIDTH - ff_text.get_width() - 10, 10))
            
        # Информация о загруженной игре
        if self.rom_loaded:
            game_title = self.loader.header['game_title'].strip()
            if game_title:
                title_text = self.font_small.render(game_title, True, COLORS['WHITE'])
                self.screen.blit(title_text, (10, 30))
                
        # Информация о клавишах
        controls = [
            "ESC: Выход",
            "F1: Перезапуск",
            "F2: Сохранить",
            "F3: Загрузить",
            "F4: Пауза",
            "F5: Перемотка",
            "F6: Звук"
        ]
        y_pos = WINDOW_HEIGHT - len(controls) * 20 - 10
        for control in controls:
            text = self.font_small.render(control, True, COLORS['WHITE'])
            self.screen.blit(text, (WINDOW_WIDTH - text.get_width() - 10, y_pos))
            y_pos += 20
            
        # Статус тач-скрина
        if self.touch.touched:
            touch_text = self.font_small.render(f"Touch: ({self.touch.x}, {self.touch.y})", True, COLORS['CYAN'])
            self.screen.blit(touch_text, (10, DS_SCREEN_HEIGHT * SCALE + 10))
            
        # Статус звука
        sound_status = "Звук: Вкл" if self.sound.sound_enabled else "Звук: Выкл"
        sound_text = self.font_small.render(sound_status, True, COLORS['GREEN'] if self.sound.sound_enabled else COLORS['RED'])
        self.screen.blit(sound_text, (10, DS_SCREEN_HEIGHT * SCALE + 30))
        
    def run(self):
        """Главный цикл эмуляции"""
        clock = pygame.time.Clock()
        
        while self.running:
            # Обработка событий
            self.handle_events()
            
            if not self.paused and self.rom_loaded:
                # Выполняем инструкции
                steps_per_frame = 100 if not self.fast_forward else 1000
                
                for _ in range(steps_per_frame):
                    if self.arm9 and self.arm9.running:
                        self.arm9.step()
                    if self.arm7 and self.arm7.running:
                        self.arm7.step()
                        
                # Рендерим кадр
                self.render_frame()
                self.frame_count += 1
                
            else:
                # Если игра не загружена или на паузе
                self.render_idle_screen()
                
            pygame.display.flip()
            
            # Ограничиваем FPS
            if not self.fast_forward:
                clock.tick(60)
            else:
                clock.tick(120)
                
        pygame.quit()
        sys.exit()
        
    def render_idle_screen(self):
        """Рендерит экран ожидания"""
        self.screen.fill((20, 20, 40))
        
        if not self.rom_loaded:
            text1 = self.font_large.render("Загрузите ROM файл", True, COLORS['WHITE'])
            text2 = self.font_medium.render("Используйте GUI для выбора игры", True, COLORS['GRAY'])
            text3 = self.font_small.render("Нажмите ESC для выхода", True, COLORS['DARKGRAY'])
            
            self.screen.blit(text1, (WINDOW_WIDTH//2 - text1.get_width()//2, WINDOW_HEIGHT//2 - 60))
            self.screen.blit(text2, (WINDOW_WIDTH//2 - text2.get_width()//2, WINDOW_HEIGHT//2))
            self.screen.blit(text3, (WINDOW_WIDTH//2 - text3.get_width()//2, WINDOW_HEIGHT//2 + 40))
        else:
            text1 = self.font_large.render("Игра на паузе", True, COLORS['WHITE'])
            text2 = self.font_medium.render("Нажмите F4 для продолжения", True, COLORS['GRAY'])
            
            self.screen.blit(text1, (WINDOW_WIDTH//2 - text1.get_width()//2, WINDOW_HEIGHT//2 - 30))
            self.screen.blit(text2, (WINDOW_WIDTH//2 - text2.get_width()//2, WINDOW_HEIGHT//2 + 20))
            
            # Показываем информацию об игре
            if self.rom_loaded:
                game_title = self.loader.header['game_title'].strip()
                if game_title:
                    title_text = self.font_small.render(f"Текущая игра: {game_title}", True, COLORS['GRAY'])
                    self.screen.blit(title_text, (WINDOW_WIDTH//2 - title_text.get_width()//2, WINDOW_HEIGHT//2 + 70))

# --- Функция запуска эмулятора ---
def run_emulator(rom_path=None):
    """Запускает эмулятор с указанным ROM"""
    emulator = ExtendedDSEmulator()
    
    if rom_path and os.path.exists(rom_path):
        emulator.load_game(rom_path)
    else:
        # Показываем экран выбора ROM
        print("🔍 ROM не указан, запускаем GUI...")
        
    emulator.run()

# --- Запуск программы ---
def main():
    """Главная функция"""
    print("=" * 60)
    print("   🎮 Nintendo DS Эмулятор v2.0")
    print("=" * 60)
    print("\nУправление:")
    print("  ESC - Выход")
    print("  F1  - Перезапуск игры")
    print("  F2  - Сохранить состояние")
    print("  F3  - Загрузить состояние")
    print("  F4  - Пауза")
    print("  F5  - Перемотка (Fast Forward)")
    print("  F6  - Вкл/Выкл звук")
    print("  F7  - Вкл/Выкл отладку")
    print("\nКлавиши управления:")
    print("  Z - A     X - B")
    print("  C - X     V - Y")
    print("  Enter - Start    RShift - Select")
    print("  A - L     S - R")
    print("  Стрелки - D-Pad")
    print("\n" + "=" * 60)
    
    # Проверяем аргументы командной строки
    if len(sys.argv) > 1:
        rom_path = sys.argv[1]
        if os.path.exists(rom_path):
            run_emulator(rom_path)
            return
        else:
            print(f"❌ Файл {rom_path} не найден")
            
    # Запускаем GUI
    try:
        selector = ROMSelector()
        selector.root.mainloop()
    except:
        # Если GUI не работает, запускаем эмулятор напрямую
        run_emulator()

if __name__ == "__main__":
    main()