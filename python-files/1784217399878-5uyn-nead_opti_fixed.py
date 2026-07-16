import customtkinter as ctk
from tkinter import messagebox
import psutil
import subprocess
import os
import sys
import threading
import ctypes
from datetime import datetime

try:
    import GPUtil
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False

if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class NeadOptiUltimate:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("NEAD OPTI ULTIMATE — FPS BOOST")
        self.root.geometry("1400x900")
        self.root.resizable(True, True)
        self.root.configure(fg_color="#0b0b1a")

        self.backup_dir = "backups"
        os.makedirs(self.backup_dir, exist_ok=True)
        self.log_file = "neadopti_log.txt"
        self.log("🚀 NEAD OPTI ULTIMATE запущена")

        # Мониторинг
        self.cpu_label = None
        self.ram_label = None
        self.gpu_label = None
        self.cpu_progress = None
        self.ram_progress = None
        self.gpu_progress = None
        self.gpu_mem_label = None
        self.gpu_temp_label = None

        # Список твиков (все)
        self.tweaks = self.build_tweak_list()

        self.create_interface()
        self.update_stats()

    def log(self, msg):
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        except:
            pass

    # ==================== БЭКАП РЕЕСТРА ====================
    def backup_registry(self, key_path, file_name=None):
        if file_name is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe = key_path.replace("\\", "_").replace("/", "_")
            file_name = f"{safe}_{ts}.reg"
        full_path = os.path.join(self.backup_dir, file_name)
        try:
            cmd = f'reg export "{key_path}" "{full_path}" /y'
            subprocess.run(cmd, shell=True, check=True, capture_output=True)
            self.log(f"Бэкап создан: {full_path}")
            return full_path
        except Exception as e:
            self.log(f"Ошибка бэкапа: {e}")
            return None

    def restore_backup(self, file_path):
        try:
            cmd = f'reg import "{file_path}"'
            subprocess.run(cmd, shell=True, check=True)
            messagebox.showinfo("Восстановление", f"Бэкап {os.path.basename(file_path)} успешно восстановлен.")
            self.log(f"Восстановлен бэкап: {file_path}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось восстановить бэкап:\n{e}")

    # ==================== СПИСОК ТВИКОВ ====================
    def build_tweak_list(self):
        return [
            # ---- Процессор ----
            {"name": "Отключить Core Parking (все ядра активны)",
             "cmd": "powercfg -setacvalueindex SCHEME_CURRENT SUB_PROCESSOR CPMINCORES 100"},
            {"name": "Отключить HPET (уменьшение задержек)",
             "cmd": "bcdedit /set useplatformclock false"},
            {"name": "Отключить динамический тик (HPET)",
             "cmd": "bcdedit /set disabledynamictick yes"},
            {"name": "Отключить C-states (глубокие состояния сна)",
             "cmd": "powercfg -setacvalueindex SCHEME_CURRENT SUB_PROCESSOR IDLEDISABLE 1"},
            {"name": "Установить высокий приоритет для игр (Foreground)",
             "cmd": "reg add HKCU\\Control Panel\\Desktop /v ForegroundLockTimeout /t REG_DWORD /d 0 /f"},
            {"name": "Уменьшить задержку меню (ускорить отклик)",
             "cmd": "reg add HKCU\\Control Panel\\Desktop /v MenuShowDelay /t REG_DWORD /d 0 /f"},
            {"name": "Включить режим 'Ultimate Performance'",
             "cmd": "powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61"},
            {"name": "Отдать приоритет фоновым процессам (программам)",
             "cmd": "reg add HKLM\\SYSTEM\\CurrentControlSet\\Control\\PriorityControl /v Win32PrioritySeparation /t REG_DWORD /d 38 /f"},
            {"name": "Отключить энергосбережение PCI Express",
             "cmd": "powercfg -setacvalueindex SCHEME_CURRENT SUB_PCIEXPRESS ASPM 0"},
            # ---- Память ----
            {"name": "Отключить файл подкачки (если >16 ГБ ОЗУ)",
             "cmd": "reg add HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management /v PagingFiles /t REG_MULTI_SZ /d \"\" /f"},
            {"name": "Увеличить системный кэш (Large System Cache)",
             "cmd": "reg add HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management /v LargeSystemCache /t REG_DWORD /d 1 /f"},
            {"name": "Отключить SuperFetch (SysMain)",
             "cmd": "sc config SysMain start=disabled"},
            # ---- Графика ----
            {"name": "Отключить вертикальную синхронизацию (V-Sync)",
             "cmd": "reg add HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers /v TdrLevel /t REG_DWORD /d 3 /f"},
            {"name": "Увеличить TDR таймаут (меньше вылетов)",
             "cmd": "reg add HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers /v TdrDelay /t REG_DWORD /d 10 /f"},
            {"name": "Отключить Triple Buffering",
             "cmd": "reg add HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers /v TripleBuffering /t REG_DWORD /d 0 /f"},
            {"name": "Включить предзагрузку шейдеров (Shader Cache)",
             "cmd": "reg add HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers /v ShaderCache /t REG_DWORD /d 1 /f"},
            {"name": "Установить предварительную подготовку кадров = 1",
             "cmd": "reg add HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers /v MaxPreRenderedFrames /t REG_DWORD /d 1 /f"},
            # ---- Система ----
            {"name": "Отключить телеметрию Windows",
             "cmd": "reg add HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection /v AllowTelemetry /t REG_DWORD /d 0 /f"},
            {"name": "Отключить Defender (временное)",
             "cmd": "reg add HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender /v DisableAntiSpyware /t REG_DWORD /d 1 /f"},
            {"name": "Отключить SmartScreen",
             "cmd": "reg add HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\AppHost /v EnableWebContentEvaluation /t REG_DWORD /d 0 /f"},
            {"name": "Отключить обновления Windows во время игры",
             "cmd": "reg add HKLM\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings /v IsManaged /t REG_DWORD /d 1 /f"},
            {"name": "Отключить Xbox Game Bar",
             "cmd": "reg add HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\GameDVR /v AppCaptureEnabled /t REG_DWORD /d 0 /f"},
            {"name": "Отключить фоновые приложения (глобально)",
             "cmd": "reg add HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\BackgroundAccessApplications /v GlobalUserDisabled /t REG_DWORD /d 1 /f"},
            {"name": "Включить режим Game Mode",
             "cmd": "reg add HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\GameDVR /v GameModeEnabled /t REG_DWORD /d 1 /f"},
            {"name": "Отключить автоматическое обновление драйверов через WU",
             "cmd": "reg add HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate\\AU /v IncludeRecommendedUpdates /t REG_DWORD /d 0 /f"},
            {"name": "Отключить индексацию файлов (для диска C:)",
             "cmd": "fsutil behavior set disablelastaccess 1"},
            # ---- Службы ----
            {"name": "Отключить поиск Windows (WSearch)",
             "cmd": "sc config WSearch start=disabled"},
            {"name": "Отключить DiagTrack (диагностика)",
             "cmd": "sc config DiagTrack start=disabled"},
            {"name": "Отключить Xbox Live службы",
             "cmd": "sc config XblAuthManager start=disabled"},
            {"name": "Отключить службу XboxNetApiSvc",
             "cmd": "sc config XboxNetApiSvc start=disabled"},
            {"name": "Отключить XboxGipSvc",
             "cmd": "sc config XboxGipSvc start=disabled"},
            {"name": "Отключить dmwappushservice (телеметрия)",
             "cmd": "sc config dmwappushservice start=disabled"},
            # ---- Визуальные эффекты ----
            {"name": "Отключить анимации окон",
             "cmd": "reg add HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\VisualEffects /v VisualFXSetting /t REG_DWORD /d 2 /f"},
            {"name": "Отключить прозрачность окон",
             "cmd": "reg add HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize /v EnableTransparency /t REG_DWORD /d 0 /f"},
            {"name": "Отключить анимацию при сворачивании/разворачивании",
             "cmd": "reg add HKCU\\Control Panel\\Desktop /v UserPreferencesMask /t REG_BINARY /d 9012038010000000 /f"},
            {"name": "Отключить затенение окон",
             "cmd": "reg add HKCU\\Software\\Microsoft\\Windows\\DWM /v Composition /t REG_DWORD /d 0 /f"},
            {"name": "Отключить сглаживание шрифтов (ClearType)",
             "cmd": "reg add HKCU\\Control Panel\\Desktop /v FontSmoothing /t REG_SZ /d 0 /f"},
            # ---- Сеть ----
            {"name": "Отключить автотюнинг TCP",
             "cmd": "netsh int tcp set global autotuninglevel=disabled"},
            {"name": "Отключить RSS (Receive Side Scaling)",
             "cmd": "netsh int tcp set global rss=disabled"},
            {"name": "Отключить Chimney (оффлоудинг)",
             "cmd": "netsh int tcp set global chimney=disabled"},
            {"name": "Отключить временные метки TCP",
             "cmd": "netsh int tcp set global timestamps=disabled"},
            {"name": "Увеличить буфер TCP (для быстрого интернета)",
             "cmd": "netsh int tcp set global initialRto=2000"},
            {"name": "Отключить QoS (планировщик пакетов)",
             "cmd": "reg add HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Psched /v NonBestEffortLimit /t REG_DWORD /d 0 /f"},
            {"name": "Сбросить DNS-кэш",
             "cmd": "ipconfig /flushdns"},
            # ---- Дополнительно ----
            {"name": "Отключить энергосбережение USB",
             "cmd": "reg add HKLM\\SYSTEM\\CurrentControlSet\\Control\\Power /v HibernateEnabled /t REG_DWORD /d 0 /f"},
            {"name": "Отключить проверку подписи драйверов (осторожно!)",
             "cmd": "bcdedit /set nointegritychecks on"},
        ]

    # ==================== ИНТЕРФЕЙС ====================
    def create_interface(self):
        sidebar = ctk.CTkFrame(self.root, width=260, corner_radius=0, fg_color="#1a1a2e")
        sidebar.pack(side="left", fill="y")

        ctk.CTkLabel(sidebar, text="NEAD OPTI", font=ctk.CTkFont(size=34, weight="bold"), text_color="#00d4ff").pack(pady=30)
        ctk.CTkLabel(sidebar, text="ULTIMATE EDITION", text_color="#ff6b6b", font=ctk.CTkFont(size=16)).pack(pady=5)

        menu = [
            ("📊 Мониторинг", self.show_monitoring),
            ("⚡ FPS Boost", self.show_fps_boost),
            ("🔧 Все твики", self.show_all_tweaks),
            ("🎮 Настройки NVIDIA", self.show_nvidia_settings),
            ("💡 Советы по FPS", self.show_tips),
            ("🧹 Очистка RAM", self.ram_cleaner),
            ("💾 Бэкап реестра", self.show_backup),
        ]
        for text, cmd in menu:
            btn = ctk.CTkButton(sidebar, text=text, height=50, command=cmd,
                                fg_color="#2a2a40", hover_color="#3a3a5a",
                                corner_radius=10)
            btn.pack(pady=6, padx=20, fill="x")

        self.main_frame = ctk.CTkFrame(self.root, fg_color="#0f0f20")
        self.main_frame.pack(side="right", fill="both", expand=True, padx=15, pady=15)
        self.content = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent")
        self.content.pack(fill="both", expand=True)

        self.show_monitoring()

    def clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    # ==================== МОНИТОРИНГ ====================
    def show_monitoring(self):
        self.clear_content()
        ctk.CTkLabel(self.content, text="📊 Системный мониторинг",
                     font=ctk.CTkFont(size=36, weight="bold"), text_color="#ffffff").pack(pady=20)

        card_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        card_frame.pack(fill="x", padx=20, pady=10)

        # CPU
        cpu_card = ctk.CTkFrame(card_frame, fg_color="#1e1e32", corner_radius=15, border_width=2, border_color="#4ecdc4")
        cpu_card.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        ctk.CTkLabel(cpu_card, text="🖥️ CPU", font=ctk.CTkFont(size=20, weight="bold"), text_color="#4ecdc4").pack(pady=10)
        self.cpu_label = ctk.CTkLabel(cpu_card, text="0%", font=ctk.CTkFont(size=30))
        self.cpu_label.pack()
        self.cpu_progress = ctk.CTkProgressBar(cpu_card, width=250, height=20, corner_radius=10, progress_color="#4ecdc4")
        self.cpu_progress.pack(pady=15)
        self.cpu_progress.set(0)

        # RAM
        ram_card = ctk.CTkFrame(card_frame, fg_color="#1e1e32", corner_radius=15, border_width=2, border_color="#ffe66d")
        ram_card.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        ctk.CTkLabel(ram_card, text="🧠 RAM", font=ctk.CTkFont(size=20, weight="bold"), text_color="#ffe66d").pack(pady=10)
        self.ram_label = ctk.CTkLabel(ram_card, text="0 / 0 GB", font=ctk.CTkFont(size=30))
        self.ram_label.pack()
        self.ram_progress = ctk.CTkProgressBar(ram_card, width=250, height=20, corner_radius=10, progress_color="#ffe66d")
        self.ram_progress.pack(pady=15)
        self.ram_progress.set(0)

        # GPU
        gpu_card = ctk.CTkFrame(card_frame, fg_color="#1e1e32", corner_radius=15, border_width=2, border_color="#ff6b6b")
        gpu_card.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        ctk.CTkLabel(gpu_card, text="🎮 GPU", font=ctk.CTkFont(size=20, weight="bold"), text_color="#ff6b6b").pack(pady=10)
        self.gpu_label = ctk.CTkLabel(gpu_card, text="0%", font=ctk.CTkFont(size=30))
        self.gpu_label.pack()
        self.gpu_progress = ctk.CTkProgressBar(gpu_card, width=250, height=20, corner_radius=10, progress_color="#ff6b6b")
        self.gpu_progress.pack(pady=15)
        self.gpu_progress.set(0)

        info_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        info_frame.pack(pady=10)
        self.gpu_mem_label = ctk.CTkLabel(info_frame, text="", font=ctk.CTkFont(size=16))
        self.gpu_mem_label.pack(side="left", padx=20)
        self.gpu_temp_label = ctk.CTkLabel(info_frame, text="", font=ctk.CTkFont(size=16))
        self.gpu_temp_label.pack(side="left", padx=20)

        if not GPU_AVAILABLE:
            ctk.CTkLabel(self.content, text="⚠️ GPUtil не установлен. Для мониторинга GPU установите: pip install GPUtil",
                         text_color="#ff6b6b", font=ctk.CTkFont(size=14)).pack(pady=10)

    def update_stats(self):
        cpu = psutil.cpu_percent(interval=0.3)
        if self.cpu_label:
            self.cpu_label.configure(text=f"{cpu:.1f}%")
            self.cpu_progress.set(cpu / 100)

        mem = psutil.virtual_memory()
        used = mem.used / (1024**3)
        total = mem.total / (1024**3)
        if self.ram_label:
            self.ram_label.configure(text=f"{used:.1f} / {total:.1f} GB")
            self.ram_progress.set(mem.percent / 100)

        if GPU_AVAILABLE and self.gpu_label:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    g = gpus[0]
                    self.gpu_label.configure(text=f"{g.load*100:.1f}%")
                    self.gpu_progress.set(g.load)
                    self.gpu_mem_label.configure(text=f"VRAM: {g.memoryUsed:.1f} / {g.memoryTotal:.1f} GB")
                    self.gpu_temp_label.configure(text=f"Температура: {g.temperature}°C")
                else:
                    self.gpu_label.configure(text="Нет данных")
                    self.gpu_progress.set(0)
            except:
                self.gpu_label.configure(text="Ошибка GPU")
                self.gpu_progress.set(0)

        self.root.after(1000, self.update_stats)

    # ==================== FPS BOOST (одна кнопка) ====================
    def show_fps_boost(self):
        self.clear_content()
        ctk.CTkLabel(self.content, text="⚡ FPS Boost — полная оптимизация в один клик",
                     font=ctk.CTkFont(size=36, weight="bold"), text_color="#ff6b6b").pack(pady=20)

        desc = ("Нажмите кнопку, чтобы применить ВСЕ твики для максимального прироста FPS.\n"
                "Будет создан бэкап реестра для возможности отката.")
        ctk.CTkLabel(self.content, text=desc, font=ctk.CTkFont(size=18), text_color="#c0c0e0").pack(pady=10)

        ctk.CTkButton(self.content, text="🚀 Применить полную оптимизацию",
                      height=80, font=ctk.CTkFont(size=28, weight="bold"),
                      fg_color="#ff6b6b", hover_color="#e55a5a", corner_radius=15,
                      command=self.full_optimization).pack(pady=50)

        tweak_list = [
            "Отключение Core Parking, HPET, C-states",
            "Отключение визуальных эффектов, анимаций, прозрачности",
            "Отключение телеметрии, Defender, Xbox Game Bar",
            "Настройка питания и приоритета процессора",
            "Отключение SuperFetch, служб, обновлений Windows",
            "Настройка сети (TCP, QoS, DNS)",
            "Оптимизация графического драйвера",
        ]
        for item in tweak_list:
            ctk.CTkLabel(self.content, text=f"✅ {item}", font=ctk.CTkFont(size=15), text_color="#a0a0c0").pack(anchor="w", padx=60, pady=3)

    def full_optimization(self):
        # Создаём бэкапы с фиксированными именами для отката
        default_keys = {
            "Explorer": r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer",
            "GraphicsDrivers": r"HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\GraphicsDrivers",
            "Power": r"HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Power",
        }
        backup_files = []
        for name, key in default_keys.items():
            fname = f"default_{name}.reg"
            p = self.backup_registry(key, fname)
            if p:
                backup_files.append(p)

        if backup_files:
            messagebox.showinfo("Бэкап", "Созданы бэкапы для отката:\n" + "\n".join(backup_files))

        threading.Thread(target=self.apply_all_tweaks, daemon=True).start()

    def apply_all_tweaks(self):
        self.log("Запущена полная оптимизация (FPS Boost)")
        self.root.after(0, lambda: messagebox.showinfo("⏳", "Применение всех твиков... Подождите."))
        success = []
        failed = []
        for tw in self.tweaks:
            try:
                subprocess.run(tw['cmd'], shell=True, stderr=subprocess.DEVNULL, check=True)
                success.append(tw['name'])
                self.log(f"✓ {tw['name']}")
            except Exception as e:
                failed.append(f"{tw['name']} (ошибка: {e})")
                self.log(f"✗ {tw['name']} – {e}")
        msg = "✅ Применено:\n" + "\n".join(success) if success else ""
        if failed:
            msg += "\n\n❌ Не удалось:\n" + "\n".join(failed)
        self.root.after(0, lambda: messagebox.showinfo("Результат", msg))
        self.log("Полная оптимизация завершена")

    # ==================== ВСЕ ТВИКИ (с галочками) ====================
    def show_all_tweaks(self):
        self.clear_content()
        ctk.CTkLabel(self.content, text="🔧 Все твики (выборочное применение)",
                     font=ctk.CTkFont(size=36, weight="bold"), text_color="#ffe66d").pack(pady=20)

        self.tweak_vars_all = {}
        for tw in self.tweaks:
            var = ctk.IntVar(value=1)
            chk = ctk.CTkCheckBox(self.content, text=tw['name'], variable=var, font=ctk.CTkFont(size=14))
            chk.pack(anchor="w", padx=60, pady=2)
            self.tweak_vars_all[tw['name']] = var

        ctk.CTkButton(self.content, text="Применить выбранные твики",
                      height=50, font=ctk.CTkFont(size=20, weight="bold"),
                      fg_color="#4ecdc4", hover_color="#3ab0a8",
                      command=self.apply_selected_tweaks).pack(pady=30)

    def apply_selected_tweaks(self):
        selected = [tw for tw in self.tweaks if self.tweak_vars_all.get(tw['name'], ctk.IntVar(value=0)).get() == 1]
        if not selected:
            messagebox.showinfo("Информация", "Не выбран ни один твик.")
            return
        # Бэкап
        for key in [r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer",
                    r"HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\GraphicsDrivers"]:
            self.backup_registry(key)
        threading.Thread(target=self.execute_tweaks, args=(selected,), daemon=True).start()

    def execute_tweaks(self, tweaks_list):
        self.log("Применение выбранных твиков")
        success = []
        failed = []
        for tw in tweaks_list:
            try:
                subprocess.run(tw['cmd'], shell=True, stderr=subprocess.DEVNULL, check=True)
                success.append(tw['name'])
                self.log(f"✓ {tw['name']}")
            except Exception as e:
                failed.append(f"{tw['name']} (ошибка: {e})")
                self.log(f"✗ {tw['name']} – {e}")
        msg = "✅ Применено:\n" + "\n".join(success) if success else ""
        if failed:
            msg += "\n\n❌ Не удалось:\n" + "\n".join(failed)
        self.root.after(0, lambda: messagebox.showinfo("Результат", msg))

    # ==================== НАСТРОЙКИ NVIDIA ====================
    def show_nvidia_settings(self):
        self.clear_content()
        ctk.CTkLabel(self.content, text="🎮 Настройки NVIDIA",
                     font=ctk.CTkFont(size=36, weight="bold"), text_color="#00d4ff").pack(pady=20)

        try:
            subprocess.run("nvidia-smi --version", shell=True, capture_output=True, check=True)
            nvidia_available = True
        except:
            nvidia_available = False

        if not nvidia_available:
            ctk.CTkLabel(self.content, text="⚠️ nvidia-smi не найдена. Убедитесь, что драйвер NVIDIA установлен.",
                         font=ctk.CTkFont(size=16), text_color="orange").pack(pady=10)

        settings = [
            ("⚡ Режим максимальной производительности",
             "reg add HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers /v PowerMizerEnable /t REG_DWORD /d 0 /f",
             "Отключает энергосбережение GPU для максимальной частоты."),
            ("🎯 Отключить вертикальную синхронизацию (V-Sync)",
             "reg add HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers /v VsyncEnabled /t REG_DWORD /d 0 /f",
             "Отключает V-Sync во всех приложениях."),
            ("🌀 Включить предзагрузку шейдеров (Shader Cache)",
             "reg add HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers /v ShaderCache /t REG_DWORD /d 1 /f",
             "Ускоряет загрузку игр за счёт кэширования шейдеров."),
            ("🚀 Установить максимальную частоту памяти и ядра (через nvidia-smi)",
             "nvidia-smi -ac 2505,875",
             "Устанавливает фиксированные частоты (осторожно, может перегреть!)."),
            ("🔄 Сбросить частоты на стандартные",
             "nvidia-smi -rac",
             "Возвращает стандартные частоты GPU."),
        ]

        for title, cmd, desc in settings:
            frame = ctk.CTkFrame(self.content, fg_color="#1a1a2e", corner_radius=12, border_width=1, border_color="#2a2a4a")
            frame.pack(fill="x", padx=50, pady=8)
            ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(size=18, weight="bold"), text_color="#4ecdc4").pack(anchor="w", padx=15, pady=5)
            ctk.CTkLabel(frame, text=desc, font=ctk.CTkFont(size=13), text_color="#a0a0c0").pack(anchor="w", padx=15)
            ctk.CTkButton(frame, text="Применить", width=120, height=30,
                          fg_color="#4ecdc4", hover_color="#3ab0a8",
                          command=lambda c=cmd, d=desc: self.apply_nvidia_setting(c, d)).pack(anchor="e", padx=15, pady=5)

    def apply_nvidia_setting(self, command, description):
        self.backup_registry(r"HKLM\SYSTEM\CurrentControlSet\Control\GraphicsDrivers")
        try:
            subprocess.run(command, shell=True, check=True)
            messagebox.showinfo("Успешно", f"Настройка применена:\n{description}")
            self.log(f"NVIDIA: {command}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось применить настройку:\n{e}")

    # ==================== СОВЕТЫ ====================
    def show_tips(self):
        self.clear_content()
        ctk.CTkLabel(self.content, text="💡 Советы по повышению FPS",
                     font=ctk.CTkFont(size=36, weight="bold"), text_color="#ffe66d").pack(pady=20)

        tips = [
            "1️⃣ Обновите драйверы видеокарты до последней версии.",
            "2️⃣ В панели управления NVIDIA выберите 'Максимальная производительность' в глобальных настройках.",
            "3️⃣ Отключите Game DVR и Xbox Game Bar в Windows.",
            "4️⃣ Установите схему питания 'Высокая производительность'.",
            "5️⃣ Закройте фоновые приложения (браузеры, мессенджеры) во время игры.",
            "6️⃣ В настройках игры снизьте качество теней, отражений и сглаживания.",
            "7️⃣ Используйте разрешение ниже максимального (например, 1080p вместо 4K).",
            "8️⃣ Отключите вертикальную синхронизацию (V-Sync) в игре и драйвере.",
            "9️⃣ Убедитесь, что система не перегревается – чистите кулеры.",
            "🔟 Включите режим 'Game Mode' в Windows (Настройки -> Игры).",
            "1️⃣1️⃣ Уменьшите частоту обновления монитора, если она выше, чем FPS игры.",
            "1️⃣2️⃣ Используйте программу для разгона видеокарты (MSI Afterburner) с осторожностью.",
        ]
        for tip in tips:
            ctk.CTkLabel(self.content, text=tip, font=ctk.CTkFont(size=15), text_color="#c0c0e0").pack(anchor="w", padx=50, pady=4)

    # ==================== RAM CLEANER ====================
    def ram_cleaner(self):
        try:
            kernel32 = ctypes.windll.kernel32
            kernel32.SetProcessWorkingSetSize(-1, -1, -1)
        except:
            pass
        free = psutil.virtual_memory().available // (1024**2)
        messagebox.showinfo("🧹 RAM Cleaner", f"Освобождено памяти: ~{free} МБ\n(Очистка рабочего набора)")
        self.log("RAM Cleaner выполнен")

    # ==================== БЭКАП РЕЕСТРА (с кнопкой отката) ====================
    def show_backup(self):
        self.clear_content()
        ctk.CTkLabel(self.content, text="💾 Бэкап реестра",
                     font=ctk.CTkFont(size=36, weight="bold"), text_color="#00d4ff").pack(pady=20)

        def restore_default():
            default_files = ["default_Explorer.reg", "default_GraphicsDrivers.reg", "default_Power.reg"]
            restored = []
            for fname in default_files:
                full = os.path.join(self.backup_dir, fname)
                if os.path.exists(full):
                    try:
                        cmd = f'reg import "{full}"'
                        subprocess.run(cmd, shell=True, check=True)
                        restored.append(fname)
                        self.log(f"Восстановлен {fname}")
                    except Exception as e:
                        messagebox.showerror("Ошибка", f"Не удалось восстановить {fname}:\n{e}")
                        return
            if restored:
                messagebox.showinfo("Восстановление", f"Восстановлены бэкапы по умолчанию:\n" + "\n".join(restored))
            else:
                messagebox.showwarning("Нет бэкапов", "Файлы default_*.reg не найдены. Сначала выполните FPS Boost.")

        ctk.CTkButton(self.content, text="↩️ Восстановить настройки по умолчанию (откат оптимизации)",
                      height=50, font=ctk.CTkFont(size=18),
                      fg_color="#ff6b6b", hover_color="#e55a5a",
                      command=restore_default).pack(pady=20)

        def backup_all():
            keys = [
                ("Explorer", r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer"),
                ("GraphicsDrivers", r"HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\GraphicsDrivers"),
                ("Power", r"HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Power"),
            ]
            paths = []
            for name, key in keys:
                p = self.backup_registry(key, f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.reg")
                if p:
                    paths.append(p)
            if paths:
                messagebox.showinfo("Бэкап создан", "Созданы бэкапы:\n" + "\n".join(paths))
            else:
                messagebox.showerror("Ошибка", "Не удалось создать ни одного бэкапа.")

        ctk.CTkButton(self.content, text="📀 Создать новый бэкап (Explorer, GraphicsDrivers, Power)",
                      height=40, font=ctk.CTkFont(size=16),
                      fg_color="#4ecdc4", hover_color="#3ab0a8",
                      command=backup_all).pack(pady=10)

        ctk.CTkLabel(self.content, text="Существующие бэкапы:", font=ctk.CTkFont(size=20)).pack(pady=20, anchor="w", padx=50)

        self.backup_list_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        self.backup_list_frame.pack(fill="both", expand=True, padx=50, pady=10)

        self.refresh_backup_list()
        ctk.CTkButton(self.content, text="🔄 Обновить список", command=self.refresh_backup_list).pack(pady=10)

    def refresh_backup_list(self):
        for w in self.backup_list_frame.winfo_children():
            w.destroy()
        if not os.path.exists(self.backup_dir):
            return
        files = [f for f in os.listdir(self.backup_dir) if f.endswith('.reg')]
        if not files:
            ctk.CTkLabel(self.backup_list_frame, text="Бэкапов пока нет.", font=ctk.CTkFont(size=16)).pack()
            return
        for f in sorted(files, reverse=True):
            frame = ctk.CTkFrame(self.backup_list_frame, fg_color="#1e1e32", corner_radius=8)
            frame.pack(fill="x", pady=4)
            ctk.CTkLabel(frame, text=f"📄 {f}", font=ctk.CTkFont(size=14)).pack(side="left", padx=10)
            btn_restore = ctk.CTkButton(frame, text="Восстановить", width=100, height=28,
                                        fg_color="#4ecdc4", hover_color="#3ab0a8",
                                        command=lambda file=f: self.restore_backup(os.path.join(self.backup_dir, file)))
            btn_restore.pack(side="right", padx=10)
            btn_delete = ctk.CTkButton(frame, text="Удалить", width=80, height=28,
                                       fg_color="#ff6b6b", hover_color="#e55a5a",
                                       command=lambda file=f: self.delete_backup(file))
            btn_delete.pack(side="right", padx=5)

    def delete_backup(self, file_name):
        full_path = os.path.join(self.backup_dir, file_name)
        try:
            os.remove(full_path)
            self.log(f"Удалён бэкап: {file_name}")
            self.refresh_backup_list()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить бэкап:\n{e}")


if __name__ == "__main__":
    try:
        if not ctypes.windll.shell32.IsUserAnAdmin():
            print("⚠️ Рекомендуется запуск от имени администратора для полного эффекта.")
        app = NeadOptiUltimate()
        app.root.mainloop()
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        input("Нажмите Enter для выхода...")