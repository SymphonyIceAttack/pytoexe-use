import time
import numpy as np
import pyautogui
from PIL import Image
import winsound
import tkinter as tk
from tkinter import messagebox, ttk
import threading
import sys
import os
import json
import cv2
from datetime import datetime
from collections import deque

class Zone:
    """Класс для хранения информации о зоне наблюдения"""
    def __init__(self, region, name=None):
        self.region = region  # (x, y, width, height)
        self.name = name or f"Зона {id(self)}"
        self.last_image = None
        self.change_count = 0
        self.enabled = True
        self.sensitivity = 1.0  # 0.1 - 2.0
        
    def to_dict(self):
        return {
            'region': self.region,
            'name': self.name,
            'enabled': self.enabled,
            'sensitivity': self.sensitivity
        }
    
    @classmethod
    def from_dict(cls, data):
        zone = cls(data['region'], data['name'])
        zone.enabled = data.get('enabled', True)
        zone.sensitivity = data.get('sensitivity', 1.0)
        return zone

class ScreenChangeDetector:
    def __init__(self):
        # Параметры
        self.zones = []  # Список зон наблюдения
        self.check_interval = 1.0  # секунды
        self.sound_frequency = 1000  # Гц
        self.sound_duration = 500  # мс
        self.sound_enabled = True
        self.global_sensitivity = 1.0  # Глобальная чувствительность (0.1 - 2.0)
        
        # Переменные для выбора области
        self.selecting = False
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        self.selection_rect = None
        
        # Настройки
        self.settings_file = "screen_change_detector_settings.json"
        self.load_settings()
        
        # История изменений для анализа
        self.change_history = deque(maxlen=100)
        
        print("=== Детектор изменений на экране (Мультизональный) ===")
        print("\nУправление:")
        print("  Q - выход")
        print("  S - добавить новую зону (выбор мышью)")
        print("  L - список зон")
        print("  D - удалить зону")
        print("  E - включить/выключить зону")
        print("  R - сбросить все зоны")
        print("  M - включить/выключить звук")
        print("  +/- - изменить интервал проверки")
        print("  F - изменить частоту звука")
        print("  T - изменить длительность звука")
        print("  V - изменить глобальную чувствительность")
        print("\nНажмите S для добавления зоны...")

    def load_settings(self):
        """Загрузка настроек из файла"""
        try:
            with open(self.settings_file, 'r') as f:
                settings = json.load(f)
            
            self.check_interval = settings.get('check_interval', 1.0)
            self.sound_frequency = settings.get('sound_frequency', 1000)
            self.sound_duration = settings.get('sound_duration', 500)
            self.sound_enabled = settings.get('sound_enabled', True)
            self.global_sensitivity = settings.get('global_sensitivity', 1.0)
            
            # Загрузка зон
            zones_data = settings.get('zones', [])
            self.zones = []
            for zone_data in zones_data:
                try:
                    zone = Zone.from_dict(zone_data)
                    self.zones.append(zone)
                except Exception as e:
                    print(f"⚠️ Ошибка загрузки зоны: {e}")
            
            print(f"✅ Настройки загружены ({len(self.zones)} зон)")
            for i, zone in enumerate(self.zones):
                print(f"   {i+1}. {zone.name}: {zone.region} (чувств: {zone.sensitivity})")
        except:
            print("ℹ️ Настройки не найдены, используются значения по умолчанию")

    def save_settings(self):
        """Сохранение настроек в файл"""
        settings = {
            'zones': [zone.to_dict() for zone in self.zones],
            'check_interval': self.check_interval,
            'sound_frequency': self.sound_frequency,
            'sound_duration': self.sound_duration,
            'sound_enabled': self.sound_enabled,
            'global_sensitivity': self.global_sensitivity
        }
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            print("✅ Настройки сохранены")
        except Exception as e:
            print(f"⚠️ Не удалось сохранить настройки: {e}")

    def select_region_with_gui(self, zone_name=None):
        """Выбор области с помощью GUI с прозрачным окном"""
        print("\n📐 Выбор области на экране:")
        print("  - Нажмите и удерживайте левую кнопку мыши")
        print("  - Перетащите для выбора области")
        print("  - Отпустите кнопку для подтверждения")
        print("  - Нажмите ESC или правую кнопку для отмены")
        
        self.selecting = False
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        
        # Создаём окно для выбора
        root = tk.Tk()
        root.title("Выбор области")
        root.attributes('-fullscreen', True)
        root.attributes('-topmost', True)
        root.attributes('-alpha', 0.3)
        root.configure(bg='black')
        
        canvas = tk.Canvas(root, bg='black', highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        
        rect = None
        selection_complete = False
        selection_canceled = False
        
        def on_mouse_down(event):
            nonlocal rect, selection_complete
            if selection_complete:
                return
            self.selecting = True
            self.start_x = event.x
            self.start_y = event.y
            self.end_x = event.x
            self.end_y = event.y
            
            if rect:
                canvas.delete(rect)
            rect = canvas.create_rectangle(
                self.start_x, self.start_y, self.end_x, self.end_y,
                outline='red', width=2, fill='', dash=(4, 4)
            )

        def on_mouse_move(event):
            nonlocal rect
            if not self.selecting or selection_complete:
                return
            self.end_x = event.x
            self.end_y = event.y
            
            if rect:
                canvas.delete(rect)
            rect = canvas.create_rectangle(
                self.start_x, self.start_y, self.end_x, self.end_y,
                outline='red', width=2, fill='', dash=(4, 4)
            )
            
            width = abs(self.end_x - self.start_x)
            height = abs(self.end_y - self.start_y)
            canvas.delete("size_text")
            canvas.create_text(
                min(self.start_x, self.end_x) + width//2,
                min(self.start_y, self.end_y) - 20,
                text=f"{width} x {height} пикс.",
                fill='white', font=('Arial', 12), tags="size_text"
            )

        def on_mouse_up(event):
            nonlocal selection_complete
            if not self.selecting or selection_complete:
                return
            self.selecting = False
            self.end_x = event.x
            self.end_y = event.y
            
            width = abs(self.end_x - self.start_x)
            height = abs(self.end_y - self.start_y)
            
            if width > 10 and height > 10:
                x1 = min(self.start_x, self.end_x)
                y1 = min(self.start_y, self.end_y)
                x2 = max(self.start_x, self.end_x)
                y2 = max(self.start_y, self.end_y)
                
                region = (x1, y1, x2 - x1, y2 - y1)
                selection_complete = True
                print(f"✅ Область выбрана: {region}")
                
                # Добавляем зону
                name = zone_name or f"Зона {len(self.zones) + 1}"
                zone = Zone(region, name)
                self.zones.append(zone)
                print(f"📌 Добавлена зона: {zone.name}")
                self.save_settings()
                root.quit()
            else:
                print("❌ Область слишком маленькая, попробуйте снова")
                if rect:
                    canvas.delete(rect)

        def on_key_press(event):
            nonlocal selection_canceled
            if event.keysym == 'Escape':
                selection_canceled = True
                print("❌ Выбор области отменён")
                root.quit()

        def on_right_click(event):
            nonlocal selection_canceled
            selection_canceled = True
            print("❌ Выбор области отменён")
            root.quit()

        canvas.bind('<Button-1>', on_mouse_down)
        canvas.bind('<B1-Motion>', on_mouse_move)
        canvas.bind('<ButtonRelease-1>', on_mouse_up)
        canvas.bind('<Button-3>', on_right_click)
        root.bind('<Key>', on_key_press)
        
        canvas.create_text(
            root.winfo_screenwidth() // 2, 30,
            text="Нажмите и перетащите мышью для выбора области",
            fill='white', font=('Arial', 14)
        )
        canvas.create_text(
            root.winfo_screenwidth() // 2, 60,
            text="ESC - отмена, ПКМ - отмена",
            fill='white', font=('Arial', 12)
        )
        
        root.mainloop()
        root.destroy()
        
        return not selection_canceled

    def select_region_with_opencv(self, zone_name=None):
        """Выбор области с помощью OpenCV"""
        try:
            print("\n📐 Выбор области на экране с помощью OpenCV")
            print("  - Нажмите и перетащите мышью для выбора области")
            print("  - Нажмите ENTER для подтверждения")
            print("  - Нажмите ESC для отмены")
            
            screenshot = pyautogui.screenshot()
            frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            roi = cv2.selectROI("Выбор области - нажмите ENTER для подтверждения", 
                               frame, False, False)
            cv2.destroyWindow("Выбор области - нажмите ENTER для подтверждения")
            
            if roi[2] > 10 and roi[3] > 10:
                region = (int(roi[0]), int(roi[1]), int(roi[2]), int(roi[3]))
                print(f"✅ Область выбрана: {region}")
                
                name = zone_name or f"Зона {len(self.zones) + 1}"
                zone = Zone(region, name)
                self.zones.append(zone)
                print(f"📌 Добавлена зона: {zone.name}")
                self.save_settings()
                return True
            else:
                print("❌ Область слишком маленькая или выбор отменён")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка при использовании OpenCV: {e}")
            return False

    def add_zone(self):
        """Добавление новой зоны"""
        name = input("Введите имя зоны (Enter для автоматического): ").strip()
        if not name:
            name = f"Зона {len(self.zones) + 1}"
        
        # Пробуем метод с OpenCV
        try:
            import cv2
            if self.select_region_with_opencv(name):
                return
        except:
            pass
        
        # Используем Tkinter
        self.select_region_with_gui(name)

    def list_zones(self):
        """Вывод списка зон"""
        if not self.zones:
            print("\n❌ Нет добавленных зон")
            return
        
        print("\n📋 Список зон:")
        print("-" * 60)
        for i, zone in enumerate(self.zones):
            status = "✓" if zone.enabled else "✗"
            x, y, w, h = zone.region
            print(f"{i+1:2}. [{status}] {zone.name}")
            print(f"     Область: ({x}, {y}) {w}x{h} пикс.")
            print(f"     Чувствительность: {zone.sensitivity:.1f}")
            print(f"     Изменений: {zone.change_count}")
        print("-" * 60)

    def delete_zone(self):
        """Удаление зоны"""
        if not self.zones:
            print("❌ Нет зон для удаления")
            return
        
        self.list_zones()
        try:
            choice = int(input("\nВведите номер зоны для удаления (0 - отмена): "))
            if 1 <= choice <= len(self.zones):
                deleted = self.zones.pop(choice - 1)
                print(f"✅ Зона '{deleted.name}' удалена")
                self.save_settings()
            elif choice == 0:
                print("Отмена")
            else:
                print("❌ Неверный номер")
        except ValueError:
            print("❌ Неверный ввод")

    def toggle_zone(self):
        """Включение/выключение зоны"""
        if not self.zones:
            print("❌ Нет зон")
            return
        
        self.list_zones()
        try:
            choice = int(input("\nВведите номер зоны для переключения (0 - отмена): "))
            if 1 <= choice <= len(self.zones):
                zone = self.zones[choice - 1]
                zone.enabled = not zone.enabled
                status = "включена" if zone.enabled else "выключена"
                print(f"✅ Зона '{zone.name}' {status}")
                self.save_settings()
            elif choice == 0:
                print("Отмена")
            else:
                print("❌ Неверный номер")
        except ValueError:
            print("❌ Неверный ввод")

    def set_zone_sensitivity(self):
        """Настройка чувствительности зоны"""
        if not self.zones:
            print("❌ Нет зон")
            return
        
        self.list_zones()
        try:
            choice = int(input("\nВведите номер зоны (0 - отмена): "))
            if 1 <= choice <= len(self.zones):
                zone = self.zones[choice - 1]
                try:
                    val = float(input(f"Введите чувствительность (0.1-2.0, текущая: {zone.sensitivity}): "))
                    if 0.1 <= val <= 2.0:
                        zone.sensitivity = val
                        print(f"✅ Чувствительность зоны '{zone.name}' установлена: {val}")
                        self.save_settings()
                    else:
                        print("❌ Значение должно быть от 0.1 до 2.0")
                except ValueError:
                    print("❌ Неверный ввод")
            elif choice == 0:
                print("Отмена")
            else:
                print("❌ Неверный номер")
        except ValueError:
            print("❌ Неверный ввод")

    def capture_screen(self, region=None):
        """Захват экрана в указанной области"""
        try:
            screenshot = pyautogui.screenshot(region=region)
            return np.array(screenshot)
        except Exception as e:
            print(f"❌ Ошибка захвата экрана: {e}")
            return None

    def compare_images(self, image1, image2, sensitivity=1.0):
        """Сравнение двух изображений с учетом чувствительности"""
        if image1 is None or image2 is None:
            return False
        
        # Приводим к одному размеру
        if image1.shape != image2.shape:
            return False
        
        # Сравнение пикселей
        diff = np.abs(image1.astype(np.int16) - image2.astype(np.int16))
        
        # Динамический порог на основе чувствительности
        # Чем выше чувствительность, тем ниже порог
        base_threshold = 30
        threshold = int(base_threshold / max(0.1, sensitivity))
        threshold = max(5, min(100, threshold))  # Ограничиваем порог
        
        diff_percentage = np.mean(diff > threshold) * 100
        
        # Минимальный процент изменений (также зависит от чувствительности)
        min_change_percent = max(0.5, 2.0 / sensitivity)
        min_change_percent = min(5.0, min_change_percent)  # Ограничиваем максимум
        
        return diff_percentage > min_change_percent

    def beep(self, frequency=None, duration=None):
        """Воспроизведение звукового сигнала"""
        if self.sound_enabled:
            try:
                freq = frequency or self.sound_frequency
                dur = duration or self.sound_duration
                winsound.Beep(freq, dur)
            except Exception as e:
                print(f"❌ Ошибка воспроизведения звука: {e}")

    def get_region_info(self):
        """Получение информации о текущих зонах"""
        if not self.zones:
            return "Нет зон"
        return f"{len(self.zones)} зон"

    def monitor(self):
        """Основной цикл мониторинга"""
        print("\n🔍 Запуск мониторинга...")
        print(f"   Зон: {len(self.zones)}")
        print(f"   Интервал: {self.check_interval} сек.")
        print(f"   Звук: {'Включён' if self.sound_enabled else 'Выключен'}")
        print(f"   Глобальная чувствительность: {self.global_sensitivity}")
        print("\nНажмите Q для выхода")
        print("Нажмите S для добавления зоны")
        print("-" * 50)
        
        if not self.zones:
            print("⚠️ Нет зон для мониторинга!")
            print("Добавьте зоны через меню.")
            input("Нажмите Enter для продолжения...")
            return
        
        # Инициализация изображений для зон
        for zone in self.zones:
            if zone.enabled:
                zone.last_image = self.capture_screen(zone.region)
                if zone.last_image is None:
                    print(f"⚠️ Не удалось захватить зону: {zone.name}")
                    zone.enabled = False
        
        # Переменные для статистики
        total_changes = 0
        start_time = time.time()
        zone_stats = {zone.name: 0 for zone in self.zones}
        
        while True:
            try:
                time.sleep(self.check_interval)
                
                changes_detected = False
                
                for zone in self.zones:
                    if not zone.enabled:
                        continue
                    
                    # Захват текущего изображения
                    current_image = self.capture_screen(zone.region)
                    if current_image is None:
                        continue
                    
                    # Сравнение с учетом индивидуальной чувствительности
                    effective_sensitivity = zone.sensitivity * self.global_sensitivity
                    if self.compare_images(zone.last_image, current_image, effective_sensitivity):
                        zone.change_count += 1
                        zone_stats[zone.name] += 1
                        total_changes += 1
                        changes_detected = True
                        
                        timestamp = datetime.now().strftime('%H:%M:%S')
                        print(f"[{timestamp}] 📢 Изменения в зоне: {zone.name} (#{zone.change_count})")
                        
                        # Разный звук для разных зон (отличаем по частоте)
                        freq_variation = (hash(zone.name) % 5 + 1) * 200
                        self.beep(frequency=self.sound_frequency + freq_variation)
                        
                        # Обновляем изображение
                        zone.last_image = current_image
                
                # Если изменений не было, обновляем изображения (адаптивный фон)
                if not changes_detected:
                    for zone in self.zones:
                        if zone.enabled:
                            current_image = self.capture_screen(zone.region)
                            if current_image is not None:
                                # Плавное обновление фона (быстрое привыкание)
                                if zone.last_image is not None:
                                    zone.last_image = cv2.addWeighted(zone.last_image, 0.7, current_image, 0.3, 0)
                                else:
                                    zone.last_image = current_image
                
            except KeyboardInterrupt:
                print("\n👋 Программа прервана пользователем")
                break
            except Exception as e:
                print(f"❌ Ошибка в цикле мониторинга: {e}")
                time.sleep(1)
        
        # Статистика
        elapsed = time.time() - start_time
        print("\n📊 Статистика:")
        print(f"   Всего изменений: {total_changes}")
        print(f"   Время работы: {elapsed:.1f} сек.")
        if elapsed > 0:
            print(f"   Частота: {total_changes / elapsed:.2f} изм./сек.")
        print("\n📊 Статистика по зонам:")
        for name, count in zone_stats.items():
            print(f"   {name}: {count} изменений")
        self.save_settings()

    def settings_menu(self):
        """Меню настроек"""
        while True:
            print("\n📐 Настройки:")
            print(f"  1 - Интервал проверки: {self.check_interval} сек.")
            print(f"  2 - Частота звука: {self.sound_frequency} Гц")
            print(f"  3 - Длительность звука: {self.sound_duration} мс")
            print(f"  4 - Звук: {'Включён' if self.sound_enabled else 'Выключен'}")
            print(f"  5 - Глобальная чувствительность: {self.global_sensitivity}")
            print(f"  6 - Управление зонами")
            print("  0 - Назад")
            
            choice = input("\nВаш выбор: ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                try:
                    val = float(input("Интервал (секунды, 0.1-10): "))
                    if 0.1 <= val <= 10:
                        self.check_interval = val
                        self.save_settings()
                        print(f"✅ Интервал установлен: {val} сек.")
                    else:
                        print("❌ Значение должно быть от 0.1 до 10")
                except:
                    print("❌ Неверный ввод")
            elif choice == '2':
                try:
                    val = int(input("Частота (Гц, 37-32767): "))
                    if 37 <= val <= 32767:
                        self.sound_frequency = val
                        self.save_settings()
                        print(f"✅ Частота установлена: {val} Гц")
                    else:
                        print("❌ Частота должна быть от 37 до 32767")
                except:
                    print("❌ Неверный ввод")
            elif choice == '3':
                try:
                    val = int(input("Длительность (мс, 100-2000): "))
                    if 100 <= val <= 2000:
                        self.sound_duration = val
                        self.save_settings()
                        print(f"✅ Длительность установлена: {val} мс")
                    else:
                        print("❌ Длительность должна быть от 100 до 2000")
                except:
                    print("❌ Неверный ввод")
            elif choice == '4':
                self.sound_enabled = not self.sound_enabled
                self.save_settings()
                print(f"🔊 Звук: {'Включён' if self.sound_enabled else 'Выключен'}")
            elif choice == '5':
                try:
                    val = float(input("Глобальная чувствительность (0.1-2.0, текущая: {self.global_sensitivity}): "))
                    if 0.1 <= val <= 2.0:
                        self.global_sensitivity = val
                        self.save_settings()
                        print(f"✅ Глобальная чувствительность: {val}")
                    else:
                        print("❌ Значение должно быть от 0.1 до 2.0")
                except:
                    print("❌ Неверный ввод")
            elif choice == '6':
                self.zone_management_menu()

    def zone_management_menu(self):
        """Меню управления зонами"""
        while True:
            print("\n📌 Управление зонами:")
            print(f"   Зон: {len(self.zones)}")
            print("  1 - Добавить зону")
            print("  2 - Список зон")
            print("  3 - Удалить зону")
            print("  4 - Включить/выключить зону")
            print("  5 - Настроить чувствительность зоны")
            print("  6 - Сбросить все зоны")
            print("  7 - Переименовать зону")
            print("  0 - Назад")
            
            choice = input("\nВаш выбор: ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                self.add_zone()
            elif choice == '2':
                self.list_zones()
            elif choice == '3':
                self.delete_zone()
            elif choice == '4':
                self.toggle_zone()
            elif choice == '5':
                self.set_zone_sensitivity()
            elif choice == '6':
                if messagebox.askyesno("Подтверждение", "Удалить все зоны?"):
                    self.zones.clear()
                    self.save_settings()
                    print("✅ Все зоны удалены")
            elif choice == '7':
                self.rename_zone()
            else:
                print("❌ Неверный выбор")

    def rename_zone(self):
        """Переименование зоны"""
        if not self.zones:
            print("❌ Нет зон")
            return
        
        self.list_zones()
        try:
            choice = int(input("\nВведите номер зоны (0 - отмена): "))
            if 1 <= choice <= len(self.zones):
                zone = self.zones[choice - 1]
                new_name = input(f"Новое имя (текущее: {zone.name}): ").strip()
                if new_name:
                    old_name = zone.name
                    zone.name = new_name
                    print(f"✅ Зона переименована: '{old_name}' -> '{new_name}'")
                    self.save_settings()
                else:
                    print("Отмена")
            elif choice == 0:
                print("Отмена")
            else:
                print("❌ Неверный номер")
        except ValueError:
            print("❌ Неверный ввод")

    def run_cli(self):
        """Интерактивный режим с управлением через консоль"""
        print("\n" + "="*50)
        print("ДЕТЕКТОР ИЗМЕНЕНИЙ НА ЭКРАНЕ (МУЛЬТИЗОНАЛЬНЫЙ)")
        print("="*50)
        
        while True:
            print("\n📋 Главное меню:")
            print(f"   Зон: {len(self.zones)}")
            print("  1 - Начать мониторинг")
            print("  2 - Управление зонами")
            print("  3 - Настройки")
            print("  0 - Выход")
            
            choice = input("\nВаш выбор: ").strip()
            
            if choice == '0':
                print("👋 До свидания!")
                self.save_settings()
                break
            elif choice == '1':
                self.monitor()
            elif choice == '2':
                self.zone_management_menu()
            elif choice == '3':
                self.settings_menu()
            else:
                print("❌ Неверный выбор. Попробуйте снова.")

def main():
    detector = ScreenChangeDetector()
    
    # Проверка аргументов командной строки
    if len(sys.argv) > 1:
        if sys.argv[1] == '--select':
            detector.add_zone()
            return
        elif sys.argv[1] == '--monitor':
            detector.monitor()
            return
        elif sys.argv[1] == '--list':
            detector.list_zones()
            return
    
    # Интерактивный режим
    detector.run_cli()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Программа прервана пользователем")
    except Exception as e:
        print(f"\n❌ Произошла ошибка: {e}")
        import traceback
        traceback.print_exc()
        input("Нажмите Enter для выхода...")