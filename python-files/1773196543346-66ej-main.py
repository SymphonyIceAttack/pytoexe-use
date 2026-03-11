import sys
import os
import winreg
import subprocess
import ctypes
from typing import Dict, List, Callable, Tuple
import customtkinter as ctk
from CTkToolTip import CTkToolTip  # для подсказок (опционально)

# ========== НАСТРОЙКИ ВНЕШНЕГО ВИДА ==========
ctk.set_appearance_mode("dark")  # по умолчанию тёмная тема
ctk.set_default_color_theme("green")  # акцентный цвет

# ========== ПРОВЕРКА ПРАВ АДМИНИСТРАТОРА ==========
def is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Перезапустить текущий скрипт с правами администратора"""
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )
    sys.exit()

# ========== КЛАССЫ ДЛЯ ТВИКОВ ==========
class Tweaker:
    """Базовый класс для твика"""
    def __init__(self, name: str, description: str, category: str):
        self.name = name
        self.description = description
        self.category = category
        self.status = False  # False = не применён (красный), True = применён (зелёный)

    def check(self) -> bool:
        """Должен вернуть True, если твик уже активен в системе"""
        raise NotImplementedError

    def apply(self) -> bool:
        """Применить твик (должен вернуть True при успехе)"""
        raise NotImplementedError

    def revert(self) -> bool:
        """Откатить твик (вернуть исходное состояние)"""
        raise NotImplementedError

# ========== РЕАЛИЗАЦИИ КОНКРЕТНЫХ ТВИКОВ ==========
class DisableDefender(Tweaker):
    def __init__(self):
        super().__init__(
            "Отключить Защитник Windows",
            "Отключает Microsoft Defender через реестр (требуется перезагрузка)",
            "Безопасность"
        )

    def check(self) -> bool:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                 r"SOFTWARE\Policies\Microsoft\Windows Defender",
                                 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, "DisableAntiSpyware")
            winreg.CloseKey(key)
            return value == 1
        except FileNotFoundError:
            return False
        except Exception:
            return False

    def apply(self) -> bool:
        try:
            key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE,
                                   r"SOFTWARE\Policies\Microsoft\Windows Defender")
            winreg.SetValueEx(key, "DisableAntiSpyware", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            return True
        except Exception:
            return False

    def revert(self) -> bool:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                 r"SOFTWARE\Policies\Microsoft\Windows Defender",
                                 0, winreg.KEY_WRITE)
            winreg.DeleteValue(key, "DisableAntiSpyware")
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            return True  # уже удалено
        except Exception:
            return False

class DisableTelemetry(Tweaker):
    def __init__(self):
        super().__init__(
            "Отключить телеметрию",
            "Запрещает сбор диагностических данных (Windows 10/11)",
            "Конфиденциальность"
        )

    def check(self) -> bool:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                 r"SOFTWARE\Policies\Microsoft\Windows\DataCollection",
                                 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, "AllowTelemetry")
            winreg.CloseKey(key)
            return value == 0
        except FileNotFoundError:
            return False
        except Exception:
            return False

    def apply(self) -> bool:
        try:
            key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE,
                                   r"SOFTWARE\Policies\Microsoft\Windows\DataCollection")
            winreg.SetValueEx(key, "AllowTelemetry", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(key)
            return True
        except Exception:
            return False

    def revert(self) -> bool:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                 r"SOFTWARE\Policies\Microsoft\Windows\DataCollection",
                                 0, winreg.KEY_WRITE)
            winreg.DeleteValue(key, "AllowTelemetry")
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            return True
        except Exception:
            return False

class DisableUAC(Tweaker):
    def __init__(self):
        super().__init__(
            "Отключить UAC",
            "Устанавливает уровень UAC в 0 (никогда не уведомлять)",
            "Система"
        )

    def check(self) -> bool:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                 r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System",
                                 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, "EnableLUA")
            winreg.CloseKey(key)
            return value == 0
        except FileNotFoundError:
            return False
        except Exception:
            return False

    def apply(self) -> bool:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                 r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System",
                                 0, winreg.KEY_WRITE)
            winreg.SetValueEx(key, "EnableLUA", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(key)
            return True
        except Exception:
            return False

    def revert(self) -> bool:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                 r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System",
                                 0, winreg.KEY_WRITE)
            winreg.SetValueEx(key, "EnableLUA", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            return True
        except Exception:
            return False

class ShowHiddenFiles(Tweaker):
    def __init__(self):
        super().__init__(
            "Показывать скрытые файлы",
            "Включает отображение скрытых и системных файлов в Проводнике",
            "Проводник"
        )

    def check(self) -> bool:
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
                                 0, winreg.KEY_READ)
            hidden, _ = winreg.QueryValueEx(key, "Hidden")
            superhidden, _ = winreg.QueryValueEx(key, "ShowSuperHidden")
            winreg.CloseKey(key)
            return hidden == 1 and superhidden == 1
        except Exception:
            return False

    def apply(self) -> bool:
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
                                 0, winreg.KEY_WRITE)
            winreg.SetValueEx(key, "Hidden", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "ShowSuperHidden", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            # Обновить Проводник
            subprocess.run("taskkill /f /im explorer.exe", shell=True, capture_output=True)
            subprocess.run("start explorer.exe", shell=True)
            return True
        except Exception:
            return False

    def revert(self) -> bool:
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
                                 0, winreg.KEY_WRITE)
            winreg.SetValueEx(key, "Hidden", 0, winreg.REG_DWORD, 2)  # 2 = не показывать
            winreg.SetValueEx(key, "ShowSuperHidden", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(key)
            subprocess.run("taskkill /f /im explorer.exe", shell=True, capture_output=True)
            subprocess.run("start explorer.exe", shell=True)
            return True
        except Exception:
            return False

class DisableBingSearch(Tweaker):
    def __init__(self):
        super().__init__(
            "Отключить Bing в поиске",
            "Убирает поиск Bing из меню Пуск (Windows 10/11)",
            "Конфиденциальность"
        )

    def check(self) -> bool:
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Search",
                                 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, "BingSearchEnabled")
            winreg.CloseKey(key)
            return value == 0
        except FileNotFoundError:
            return False
        except Exception:
            return False

    def apply(self) -> bool:
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                                   r"Software\Microsoft\Windows\CurrentVersion\Search")
            winreg.SetValueEx(key, "BingSearchEnabled", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(key)
            return True
        except Exception:
            return False

    def revert(self) -> bool:
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Search",
                                 0, winreg.KEY_WRITE)
            winreg.DeleteValue(key, "BingSearchEnabled")
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            return True
        except Exception:
            return False

class DisableAdsInStartMenu(Tweaker):
    def __init__(self):
        super().__init__(
            "Отключить рекламу в меню Пуск",
            "Отключает показ рекомендованных приложений",
            "Конфиденциальность"
        )

    def check(self) -> bool:
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager",
                                 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, "SystemPaneSuggestionsEnabled")
            winreg.CloseKey(key)
            return value == 0
        except FileNotFoundError:
            return False
        except Exception:
            return False

    def apply(self) -> bool:
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                                   r"Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager")
            winreg.SetValueEx(key, "SystemPaneSuggestionsEnabled", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(key)
            return True
        except Exception:
            return False

    def revert(self) -> bool:
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager",
                                 0, winreg.KEY_WRITE)
            winreg.DeleteValue(key, "SystemPaneSuggestionsEnabled")
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            return True
        except Exception:
            return False

# Добавим ещё несколько твиков для полноты
class DisableGameBar(Tweaker):
    def __init__(self):
        super().__init__(
            "Отключить игровую панель",
            "Отключает запись игр и Game Bar",
            "Система"
        )

    def check(self) -> bool:
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\GameDVR",
                                 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, "AppCaptureEnabled")
            winreg.CloseKey(key)
            return value == 0
        except FileNotFoundError:
            return False
        except Exception:
            return False

    def apply(self) -> bool:
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                                   r"Software\Microsoft\Windows\CurrentVersion\GameDVR")
            winreg.SetValueEx(key, "AppCaptureEnabled", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(key)
            return True
        except Exception:
            return False

    def revert(self) -> bool:
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\GameDVR",
                                 0, winreg.KEY_WRITE)
            winreg.DeleteValue(key, "AppCaptureEnabled")
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            return True
        except Exception:
            return False

class DisableCortana(Tweaker):
    def __init__(self):
        super().__init__(
            "Отключить Cortana",
            "Отключает голосового помощника Cortana",
            "Конфиденциальность"
        )

    def check(self) -> bool:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                 r"SOFTWARE\Policies\Microsoft\Windows\Windows Search",
                                 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, "AllowCortana")
            winreg.CloseKey(key)
            return value == 0
        except FileNotFoundError:
            return False
        except Exception:
            return False

    def apply(self) -> bool:
        try:
            key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE,
                                   r"SOFTWARE\Policies\Microsoft\Windows\Windows Search")
            winreg.SetValueEx(key, "AllowCortana", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(key)
            return True
        except Exception:
            return False

    def revert(self) -> bool:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                 r"SOFTWARE\Policies\Microsoft\Windows\Windows Search",
                                 0, winreg.KEY_WRITE)
            winreg.DeleteValue(key, "AllowCortana")
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            return True
        except Exception:
            return False

class DisableOneDrive(Tweaker):
    def __init__(self):
        super().__init__(
            "Отключить OneDrive",
            "Удаляет OneDrive из Проводника и автозагрузки",
            "Система"
        )

    def check(self) -> bool:
        # Проверяем, отключен ли OneDrive через политики
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                 r"SOFTWARE\Policies\Microsoft\Windows\OneDrive",
                                 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, "DisableFileSyncNGSC")
            winreg.CloseKey(key)
            return value == 1
        except FileNotFoundError:
            return False
        except Exception:
            return False

    def apply(self) -> bool:
        try:
            key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE,
                                   r"SOFTWARE\Policies\Microsoft\Windows\OneDrive")
            winreg.SetValueEx(key, "DisableFileSyncNGSC", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            return True
        except Exception:
            return False

    def revert(self) -> bool:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                 r"SOFTWARE\Policies\Microsoft\Windows\OneDrive",
                                 0, winreg.KEY_WRITE)
            winreg.DeleteValue(key, "DisableFileSyncNGSC")
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            return True
        except Exception:
            return False

# ========== ГЛАВНОЕ ОКНО ПРИЛОЖЕНИЯ ==========
class Windows11TweakerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Проверка прав администратора
        if not is_admin():
            run_as_admin()
            return

        self.title("Windows 11 Tweaker")
        self.geometry("1200x700")
        self.minsize(900, 600)

        # Список всех доступных твиков
        self.all_tweaks: List[Tweaker] = [
            DisableDefender(),
            DisableTelemetry(),
            DisableUAC(),
            ShowHiddenFiles(),
            DisableBingSearch(),
            DisableAdsInStartMenu(),
            DisableGameBar(),
            DisableCortana(),
            DisableOneDrive(),
        ]

        # Категории для бокового меню (уникальные)
        self.categories = sorted(set(t.category for t in self.all_tweaks))

        # Текущая выбранная категория (None = все)
        self.current_category = None
        self.search_text = ""

        # Словарь для хранения виджетов твиков (ключ - имя твика)
        self.tweak_widgets: Dict[str, Dict] = {}

        # Настройка сетки
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ========== БОКОВОЕ МЕНЮ ==========
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nswe")
        self.sidebar.grid_rowconfigure(5, weight=1)  # чтобы кнопка темы была внизу

        # Логотип / название
        self.logo_label = ctk.CTkLabel(
            self.sidebar, text="Windows 11\nTweaker", font=ctk.CTkFont(size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Кнопки категорий
        self.category_buttons = []
        # Кнопка "Все"
        btn_all = ctk.CTkButton(
            self.sidebar, text="Все", command=lambda: self.filter_by_category(None)
        )
        btn_all.grid(row=1, column=0, padx=20, pady=5)
        self.category_buttons.append(btn_all)

        for i, cat in enumerate(self.categories, start=2):
            btn = ctk.CTkButton(
                self.sidebar, text=cat, command=lambda c=cat: self.filter_by_category(c)
            )
            btn.grid(row=i, column=0, padx=20, pady=5)
            self.category_buttons.append(btn)

        # Переключатель темы (внизу)
        self.theme_switch = ctk.CTkSwitch(
            self.sidebar, text="Светлая тема", command=self.toggle_theme,
            onvalue="light", offvalue="dark"
        )
        self.theme_switch.grid(row=100, column=0, padx=20, pady=20, sticky="s")

        # ========== ОСНОВНАЯ ОБЛАСТЬ ==========
        self.main_area = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nswe", padx=10, pady=10)
        self.main_area.grid_columnconfigure(0, weight=1)
        self.main_area.grid_rowconfigure(1, weight=1)

        # Строка поиска
        self.search_entry = ctk.CTkEntry(
            self.main_area, placeholder_text="Поиск твиков..."
        )
        self.search_entry.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        self.search_entry.bind("<KeyRelease>", self.on_search)

        # Область со списком твиков (скроллируемая)
        self.tweaks_frame = ctk.CTkScrollableFrame(self.main_area, label_text="Список твиков")
        self.tweaks_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nswe")
        self.tweaks_frame.grid_columnconfigure(0, weight=1)

        # Первоначальное сканирование статусов и отображение
        self.scan_all_statuses()
        self.display_tweaks()

    def scan_all_statuses(self):
        """Проверяет текущее состояние каждого твика в системе"""
        for tweak in self.all_tweaks:
            tweak.status = tweak.check()

    def display_tweaks(self):
        """Отображает твики согласно фильтрам (категория, поиск)"""
        # Очистить предыдущие виджеты
        for widget in self.tweaks_frame.winfo_children():
            widget.destroy()
        self.tweak_widgets.clear()

        # Фильтрация
        filtered = self.all_tweaks
        if self.current_category:
            filtered = [t for t in filtered if t.category == self.current_category]
        if self.search_text:
            filtered = [t for t in filtered if self.search_text.lower() in t.name.lower() or self.search_text.lower() in t.description.lower()]

        # Создание виджетов для каждого твика
        for tweak in filtered:
            frame = ctk.CTkFrame(self.tweaks_frame)
            frame.grid(row=len(self.tweak_widgets), column=0, padx=5, pady=5, sticky="ew")
            frame.grid_columnconfigure(1, weight=1)

            # Индикатор статуса (кружок)
            status_color = "#2EF01A" if tweak.status else "#FF4D4D"
            status_label = ctk.CTkLabel(
                frame, text="●", text_color=status_color, font=ctk.CTkFont(size=20)
            )
            status_label.grid(row=0, column=0, padx=(10, 5), pady=10)

            # Название и описание
            text_frame = ctk.CTkFrame(frame, fg_color="transparent")
            text_frame.grid(row=0, column=1, padx=5, pady=5, sticky="w")
            text_frame.grid_columnconfigure(0, weight=1)

            name_label = ctk.CTkLabel(
                text_frame, text=tweak.name, font=ctk.CTkFont(size=14, weight="bold"),
                anchor="w"
            )
            name_label.grid(row=0, column=0, sticky="w")

            desc_label = ctk.CTkLabel(
                text_frame, text=tweak.description, font=ctk.CTkFont(size=12),
                text_color="gray", anchor="w"
            )
            desc_label.grid(row=1, column=0, sticky="w")

            # Кнопка действия
            action_text = "Откатить" if tweak.status else "Применить"
            action_btn = ctk.CTkButton(
                frame, text=action_text, width=100,
                command=lambda t=tweak: self.toggle_tweak(t)
            )
            action_btn.grid(row=0, column=2, padx=10, pady=10)

            # Сохраняем ссылки на виджеты для обновления
            self.tweak_widgets[tweak.name] = {
                "frame": frame,
                "status_label": status_label,
                "action_btn": action_btn
            }

    def filter_by_category(self, category):
        """Фильтр по выбранной категории"""
        self.current_category = category
        self.display_tweaks()

    def on_search(self, event=None):
        """Обработка ввода поиска"""
        self.search_text = self.search_entry.get()
        self.display_tweaks()

    def toggle_tweak(self, tweak: Tweaker):
        """Применить или откатить твик, затем обновить интерфейс"""
        if tweak.status:
            success = tweak.revert()
        else:
            success = tweak.apply()

        if success:
            # Обновляем статус
            tweak.status = tweak.check()  # перепроверяем (может быть, изменения вступили не сразу, но для простоты считаем успех)
            # Обновляем соответствующие виджеты
            if tweak.name in self.tweak_widgets:
                w = self.tweak_widgets[tweak.name]
                new_color = "#2EF01A" if tweak.status else "#FF4D4D"
                w["status_label"].configure(text_color=new_color)
                w["action_btn"].configure(text="Откатить" if tweak.status else "Применить")
        else:
            # Можно показать ошибку
            ctk.CTkMessageBox(title="Ошибка", message=f"Не удалось {'откатить' if tweak.status else 'применить'} твик.")

    def toggle_theme(self):
        """Переключение между тёмной и светлой темой"""
        if self.theme_switch.get() == "light":
            ctk.set_appearance_mode("light")
        else:
            ctk.set_appearance_mode("dark")

# ========== ЗАПУСК ПРИЛОЖЕНИЯ ==========
if __name__ == "__main__":
    app = Windows11TweakerApp()
    app.mainloop()