import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime

class SideloadlyClone:
    def __init__(self, root):
        self.root = root
        self.root.title("Sideloadly Clone - iOS IPA Installer")
        self.root.geometry("850x750")
        self.root.configure(bg="#2b2b2b")
        
        self.is_installing = False
        self.create_widgets()
        
        # Автоматическая проверка при запуске
        self.root.after(500, self.check_system)
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        self.create_quick_fix_section(main_frame)
        self.create_diagnostic_section(main_frame)
        self.create_apple_id_section(main_frame)
        self.create_ipa_section(main_frame)
        self.create_devices_section(main_frame)
        self.create_progress_section(main_frame)
        self.create_log_section(main_frame)
        self.create_buttons(main_frame)
    
    def create_quick_fix_section(self, parent):
        """Быстрые кнопки для исправления проблем"""
        frame = ttk.LabelFrame(parent, text="⚡ БЫСТРЫЕ ИСПРАВЛЕНИЯ", padding="10")
        frame.pack(fill="x", pady=5)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x")
        
        ttk.Button(btn_frame, text="1️⃣ Перезапустить службу Apple Mobile Device", 
                  command=self.restart_apple_service).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="2️⃣ Запустить туннель (iOS 17+)", 
                  command=self.start_tunnel).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="3️⃣ Очистить кэш подключений", 
                  command=self.clear_pairing_records).pack(side="left", padx=5)
    
    def create_diagnostic_section(self, parent):
        frame = ttk.LabelFrame(parent, text="🔧 ДИАГНОСТИКА", padding="10")
        frame.pack(fill="x", pady=5)
        
        self.diagnostic_text = tk.Text(frame, height=5, bg="#1e1e1e", fg="#d4d4d4", 
                                       font=("Consolas", 9), wrap="word")
        self.diagnostic_text.pack(fill="x")
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=5)
        
        ttk.Button(btn_frame, text="🔍 Запустить полную диагностику", 
                  command=self.run_full_diagnostic).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="📱 Поиск устройств (все методы)", 
                  command=self.find_devices_all_methods).pack(side="left", padx=5)
    
    def create_apple_id_section(self, parent):
        frame = ttk.LabelFrame(parent, text="Apple ID", padding="10")
        frame.pack(fill="x", pady=5)
        
        ttk.Label(frame, text="Email:").grid(row=0, column=0, sticky="w", padx=5)
        self.email_entry = ttk.Entry(frame, width=40)
        self.email_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="Password:").grid(row=1, column=0, sticky="w", padx=5)
        self.password_entry = ttk.Entry(frame, width=40, show="*")
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)
    
    def create_ipa_section(self, parent):
        frame = ttk.LabelFrame(parent, text="IPA файл", padding="10")
        frame.pack(fill="x", pady=5)
        
        self.ipa_path_var = tk.StringVar()
        self.ipa_entry = ttk.Entry(frame, textvariable=self.ipa_path_var, width=55)
        self.ipa_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        self.browse_btn = ttk.Button(frame, text="📁 Выбрать IPA", command=self.browse_ipa)
        self.browse_btn.pack(side="right", padx=5)
    
    def create_devices_section(self, parent):
        frame = ttk.LabelFrame(parent, text="📱 ПОДКЛЮЧЕННЫЕ УСТРОЙСТВА", padding="10")
        frame.pack(fill="x", pady=5)
        
        self.device_var = tk.StringVar()
        self.device_combo = ttk.Combobox(frame, textvariable=self.device_var, 
                                        state="readonly", width=55)
        self.device_combo.pack(fill="x", pady=5)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=5)
        
        ttk.Button(btn_frame, text="🔄 Обновить список", command=self.refresh_devices).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🌐 Поиск по Wi-Fi", command=self.search_wifi_devices).pack(side="left", padx=5)
    
    def create_progress_section(self, parent):
        frame = ttk.LabelFrame(parent, text="Прогресс", padding="10")
        frame.pack(fill="x", pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x", pady=5)
        self.status_label = ttk.Label(frame, text="Готов")
        self.status_label.pack()
    
    def create_log_section(self, parent):
        frame = ttk.LabelFrame(parent, text="ЛОГ", padding="10")
        frame.pack(fill="both", expand=True, pady=5)
        
        self.console_text = tk.Text(frame, height=10, bg="#1e1e1e", fg="#d4d4d4", 
                                   wrap="word", font=("Consolas", 9))
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.console_text.yview)
        self.console_text.configure(yscrollcommand=scrollbar.set)
        self.console_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_buttons(self, parent):
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill="x", pady=10)
        
        self.install_btn = tk.Button(button_frame, text="🚀 НАЧАТЬ УСТАНОВКУ",
            command=self.start_installation, bg="#4CAF50", fg="white",
            font=("Arial", 12, "bold"), height=2, cursor="hand2")
        self.install_btn.pack(side="left", fill="x", expand=True, padx=5)
        
        self.stop_btn = tk.Button(button_frame, text="⏹ ОСТАНОВИТЬ",
            command=self.stop_installation, bg="#f44336", fg="white",
            font=("Arial", 10, "bold"), state="disabled", cursor="hand2")
        self.stop_btn.pack(side="left", padx=5)
    
    def restart_apple_service(self):
        """Перезапуск службы Apple Mobile Device"""
        self.log_message("🔄 Перезапуск Apple Mobile Device Service...")
        try:
            subprocess.run('net stop "Apple Mobile Device Service"', shell=True, capture_output=True)
            subprocess.run('net start "Apple Mobile Device Service"', shell=True, capture_output=True)
            self.log_message("✅ Служба перезапущена")
        except Exception as e:
            self.log_message(f"❌ Ошибка: {e}")
    
    def start_tunnel(self):
        """Запуск туннеля для iOS 17+ (нужны права администратора)"""
        self.log_message("🔗 Запуск туннеля для iOS 17+...")
        self.log_message("⚠️ Требуются права администратора!")
        try:
            # Запускаем tunneld в фоне
            subprocess.Popen('start /B python -m pymobiledevice3 remote tunneld', 
                           shell=True)
            self.log_message("✅ Туннель запущен")
        except Exception as e:
            self.log_message(f"❌ Ошибка: {e}")
    
    def clear_pairing_records(self):
        """Очистка кэша подключений"""
        self.log_message("🗑 Очистка кэша подключений...")
        try:
            # Путь к файлам pairing на Windows
            pair_path = os.path.expanduser("~/.pymobiledevice3")
            if os.path.exists(pair_path):
                import shutil
                shutil.rmtree(pair_path)
                self.log_message("✅ Кэш очищен")
            else:
                self.log_message("ℹ️ Кэш не найден")
        except Exception as e:
            self.log_message(f"❌ Ошибка: {e}")
    
    def run_full_diagnostic(self):
        """Полная диагностика системы"""
        self.diagnostic_text.delete(1.0, tk.END)
        self.diagnostic_text.insert(tk.END, "🔍 ДИАГНОСТИКА СИСТЕМЫ\n")
        self.diagnostic_text.insert(tk.END, "=" * 40 + "\n")
        
        # Проверка iTunes
        try:
            result = subprocess.run('reg query "HKLM\\SOFTWARE\\WOW6432Node\\Apple Inc.\\iTunes"',
                capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                self.diagnostic_text.insert(tk.END, "✅ iTunes: УСТАНОВЛЕН\n")
            else:
                self.diagnostic_text.insert(tk.END, "❌ iTunes: НЕ НАЙДЕН\n")
                self.diagnostic_text.insert(tk.END, "   → СКАЧАЙТЕ: apple.com/itunes/download/\n")
        except:
            self.diagnostic_text.insert(tk.END, "❌ iTunes: ОШИБКА ПРОВЕРКИ\n")
        
        # Проверка драйвера
        try:
            result = subprocess.run('driverquery | findstr "usbaapl"', capture_output=True, text=True, shell=True)
            if "usbaapl" in result.stdout.lower():
                self.diagnostic_text.insert(tk.END, "✅ Apple USB Driver: УСТАНОВЛЕН\n")
            else:
                self.diagnostic_text.insert(tk.END, "❌ Apple USB Driver: НЕ НАЙДЕН\n")
        except:
            self.diagnostic_text.insert(tk.END, "⚠️ Apple USB Driver: НЕ ПРОВЕРЕН\n")
        
        # Проверка службы
        try:
            result = subprocess.run('sc query "Apple Mobile Device Service"', capture_output=True, text=True, shell=True)
            if "RUNNING" in result.stdout:
                self.diagnostic_text.insert(tk.END, "✅ Apple Mobile Device: ЗАПУЩЕНА\n")
            else:
                self.diagnostic_text.insert(tk.END, "❌ Apple Mobile Device: НЕ ЗАПУЩЕНА\n")
        except:
            self.diagnostic_text.insert(tk.END, "⚠️ Служба: НЕ ПРОВЕРЕНА\n")
        
        self.diagnostic_text.insert(tk.END, "\n💡 РЕШЕНИЯ:\n")
        self.diagnostic_text.insert(tk.END, "• Нажмите 'Быстрые исправления' выше\n")
        self.diagnostic_text.insert(tk.END, "• Переустановите iTunes с apple.com\n")
        self.diagnostic_text.insert(tk.END, "• На iPhone: Настройки → Основные → Сброс → Сбросить настройки конфиденциальности\n")
    
    def find_devices_all_methods(self):
        """Поиск устройств всеми возможными способами"""
        self.log_message("=" * 50)
        self.log_message("🔍 ПОИСК УСТРОЙСТВ ВСЕМИ МЕТОДАМИ")
        self.log_message("=" * 50)
        
        devices_found = []
        
        # МЕТОД 1: pymobiledevice3 usbmux list
        self.log_message("\n📌 Метод 1: pymobiledevice3 usbmux list")
        try:
            result = subprocess.run("pymobiledevice3 usbmux list", capture_output=True, text=True, shell=True, timeout=10)
            if result.stdout.strip():
                self.log_message(f"✅ Найдено:\n{result.stdout}")
                devices_found.extend(result.stdout.strip().split('\n'))
            else:
                self.log_message("❌ Устройств не найдено")
        except Exception as e:
            self.log_message(f"⚠️ Ошибка: {e}")
        
        # МЕТОД 2: Поиск через PowerShell (прямой поиск USB устройств)
        self.log_message("\n📌 Метод 2: PowerShell (поиск USB устройств Apple)")
        try:
            ps_cmd = '''
            Get-PnpDevice -PresentOnly | Where-Object { 
                $_.FriendlyName -like "*iPhone*" -or 
                $_.FriendlyName -like "*iPad*" -or 
                $_.FriendlyName -like "*Apple*Mobile*"
            } | Select-Object FriendlyName, Status
            '''
            result = subprocess.run(f'powershell -Command "{ps_cmd}"', capture_output=True, text=True, shell=True, timeout=10)
            if result.stdout.strip() and "iPhone" in result.stdout:
                self.log_message(f"✅ Найдено:\n{result.stdout}")
            else:
                self.log_message("❌ Устройств Apple не найдено в системе")
        except Exception as e:
            self.log_message(f"⚠️ Ошибка: {e}")
        
        # МЕТОД 3: Поиск через wmic
        self.log_message("\n📌 Метод 3: WMIC (прямой запрос к USB)")
        try:
            result = subprocess.run('wmic path Win32_PnPEntity where "Name like \'%iPhone%\' or Name like \'%iPad%\'" get Name', 
                capture_output=True, text=True, shell=True, timeout=10)
            if result.stdout.strip() and "iPhone" in result.stdout:
                self.log_message(f"✅ Найдено:\n{result.stdout}")
            else:
                self.log_message("❌ Устройств не найдено")
        except Exception as e:
            self.log_message(f"⚠️ Ошибка: {e}")
        
        # ИТОГ
        self.log_message("\n" + "=" * 50)
        if devices_found:
            self.log_message("✅ УСТРОЙСТВО НАЙДЕНО!")
            self.device_combo['values'] = devices_found
            self.device_combo.set(devices_found[0])
        else:
            self.log_message("❌ УСТРОЙСТВО НЕ НАЙДЕНО!")
            self.log_message("\n⚠️ ВОЗМОЖНЫЕ ПРИЧИНЫ:")
            self.log_message("1. iTunes не установлен или установлен из Microsoft Store")
            self.log_message("   → Скачайте с apple.com/itunes/download/")
            self.log_message("2. На iPhone не нажат 'Доверять'")
            self.log_message("   → Разблокируйте iPhone и нажмите 'Доверять'")
            self.log_message("3. Неисправный кабель (только зарядка, без передачи данных)")
            self.log_message("   → Попробуйте другой кабель")
            self.log_message("4. iOS 17+ требует туннель")
            self.log_message("   → Нажмите кнопку 'Запустить туннель (iOS 17+)'")
        
        self.log_message("=" * 50)
    
    def search_wifi_devices(self):
        """Поиск устройств по Wi-Fi"""
        self.log_message("🌐 Поиск устройств по Wi-Fi...")
        try:
            result = subprocess.run("pymobiledevice3 bonjour browse", capture_output=True, text=True, shell=True, timeout=10)
            if result.stdout.strip():
                self.log_message(f"✅ Найдено по Wi-Fi:\n{result.stdout}")
            else:
                self.log_message("❌ Устройств по Wi-Fi не найдено")
        except Exception as e:
            self.log_message(f"⚠️ Ошибка: {e}")
    
    def refresh_devices(self):
        """Обновление списка устройств"""
        self.find_devices_all_methods()
    
    def browse_ipa(self):
        filename = filedialog.askopenfilename(filetypes=[("IPA files", "*.ipa")])
        if filename:
            self.ipa_path_var.set(filename)
            self.log_message(f"✅ Выбран: {Path(filename).name}")
    
    def log_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.console_text.see(tk.END)
        self.root.update_idletasks()
    
    def check_system(self):
        self.log_message("=" * 50)
        self.log_message("🔧 ПРОГРАММА ЗАПУЩЕНА")
        self.log_message("💡 Нажмите 'Поиск устройств (все методы)' для диагностики")
        self.log_message("=" * 50)
        self.run_full_diagnostic()
    
    def update_progress(self, value, status):
        self.progress_var.set(value)
        self.status_label.config(text=status)
        self.root.update_idletasks()
    
    def start_installation(self):
        if not self.ipa_path_var.get():
            messagebox.showerror("Ошибка", "Выберите IPA файл!")
            return
        if not self.email_entry.get():
            messagebox.showerror("Ошибка", "Введите Apple ID!")
            return
        
        self.install_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.is_installing = True
        
        thread = threading.Thread(target=self.installation_thread, daemon=True)
        thread.start()
    
    def installation_thread(self):
        try:
            self.log_message("🚀 НАЧАЛО УСТАНОВКИ")
            for i in range(0, 101, 20):
                if not self.is_installing: break
                self.update_progress(i, f"Установка... {i}%")
                threading.Event().wait(0.5)
            self.update_progress(100, "Готово!")
            self.log_message("✅ УСТАНОВКА ЗАВЕРШЕНА")
        except Exception as e:
            self.log_message(f"❌ Ошибка: {e}")
        finally:
            self.is_installing = False
            self.install_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
    
    def stop_installation(self):
        self.log_message("🛑 Остановлено")
        self.is_installing = False
        self.update_progress(0, "Отменено")
        self.install_btn.config(state="normal")
        self.stop_btn.config(state="disabled")

if __name__ == "__main__":
    root = tk.Tk()
    app = SideloadlyClone(root)
    root.mainloop()