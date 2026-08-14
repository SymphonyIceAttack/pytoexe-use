import tkinter as tk
from tkinter import messagebox
import shutil
import os
import tempfile
import time
import subprocess
import ctypes
import platform


# =========================================================
# MakuTweaker Lite v7
# =========================================================

root = tk.Tk()
root.title("MakuTweaker Lite v7")
root.geometry("430x820")
root.resizable(False, False)
root.configure(bg="#1e1e1e")


# =========================================================
# СОВРЕМЕННЫЙ ИНТЕРФЕЙС
# =========================================================

from tkinter import ttk

root = tk.Tk()
root.title("MakuTweaker Lite v7")
root.geometry("620x780")
root.minsize(560, 700)
root.configure(bg="#0f1117")

# Палитра
BG = "#0f1117"
CARD = "#171b24"
CARD_2 = "#1d2330"
TEXT = "#f4f7fb"
MUTED = "#8f9aaa"
ACCENT = "#00e5a0"
ACCENT_HOVER = "#00c98c"
BORDER = "#252c39"

style = ttk.Style()
style.theme_use("clam")
style.configure(
    "Modern.Vertical.TScrollbar",
    background=CARD_2,
    troughcolor=BG,
    bordercolor=BG,
    arrowcolor=MUTED
)

# Верхняя панель
header = tk.Frame(root, bg=BG)
header.pack(fill="x", padx=24, pady=(20, 8))

title = tk.Label(
    header,
    text="MakuTweaker",
    fg=TEXT,
    bg=BG,
    font=("Segoe UI", 22, "bold")
)
title.pack(anchor="w")

subtitle = tk.Label(
    header,
    text="Lite v7  •  системный центр управления Windows",
    fg=MUTED,
    bg=BG,
    font=("Segoe UI", 10)
)
subtitle.pack(anchor="w", pady=(2, 0))

# Карточка состояния
info_card = tk.Frame(
    root, bg=CARD, highlightthickness=1, highlightbackground=BORDER
)
info_card.pack(fill="x", padx=24, pady=(10, 12))

time_label = tk.Label(
    info_card,
    fg=ACCENT,
    bg=CARD,
    font=("Consolas", 25, "bold")
)
time_label.pack(anchor="w", padx=18, pady=(14, 0))

disk_label = tk.Label(
    info_card,
    fg=TEXT,
    bg=CARD,
    font=("Segoe UI", 10)
)
disk_label.pack(anchor="w", padx=18, pady=(2, 0))

status_label = tk.Label(
    info_card,
    text="●  Система готова",
    fg=ACCENT,
    bg=CARD,
    font=("Segoe UI", 10, "bold")
)
status_label.pack(anchor="w", padx=18, pady=(7, 14))

# Панель подсказки
hint = tk.Label(
    root,
    text="Выбери действие ниже  •  изменения выполняются только после подтверждения",
    fg=MUTED,
    bg=BG,
    font=("Segoe UI", 9)
)
hint.pack(anchor="w", padx=26, pady=(0, 6))

# Прокручиваемая область
outer = tk.Frame(root, bg=BG)
outer.pack(fill="both", expand=True, padx=18, pady=(0, 8))

canvas = tk.Canvas(outer, bg=BG, highlightthickness=0)
scrollbar = ttk.Scrollbar(
    outer, orient="vertical", command=canvas.yview,
    style="Modern.Vertical.TScrollbar"
)
content = tk.Frame(canvas, bg=BG)

content_window = canvas.create_window((0, 0), window=content, anchor="nw")

def _resize_content(event):
    canvas.itemconfigure(content_window, width=event.width)

def _update_scroll(event=None):
    canvas.configure(scrollregion=canvas.bbox("all"))

content.bind("<Configure>", _update_scroll)
canvas.bind("<Configure>", _resize_content)
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

def _wheel(event):
    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

canvas.bind_all("<MouseWheel>", _wheel)

def section(title_text):
    frame = tk.Frame(content, bg=BG)
    frame.pack(fill="x", padx=6, pady=(8, 4))

    tk.Label(
        frame,
        text=title_text.upper(),
        fg=MUTED,
        bg=BG,
        font=("Segoe UI", 9, "bold")
    ).pack(anchor="w", padx=4)

    line = tk.Frame(frame, bg=BORDER, height=1)
    line.pack(fill="x", padx=4, pady=(5, 2))
    return frame

# =========================================================
# ИНФОРМАЦИЯ О ДИСКЕ
# =========================================================

def update_info():

    time_label.config(
        text=time.strftime("%H:%M")
    )

    try:
        total, used, free = shutil.disk_usage("C:/")

        disk_label.config(
            text=(
                f"Диск C: {free / (1024 ** 3):.1f} ГБ "
                f"свободно из {total / (1024 ** 3):.1f} ГБ"
            )
        )

    except:
        disk_label.config(
            text="Информация о диске недоступна"
        )

    root.after(1000, update_info)


# =========================================================
# TEMP
# =========================================================

def clean_temp():

    temp_dir = tempfile.gettempdir()
    deleted = 0

    try:

        for name in os.listdir(temp_dir):

            path = os.path.join(
                temp_dir,
                name
            )

            try:

                if os.path.isfile(path) or os.path.islink(path):
                    os.remove(path)
                    deleted += 1

                elif os.path.isdir(path):
                    shutil.rmtree(path)
                    deleted += 1

            except:
                pass

    except:
        pass

    status_label.config(
        text=f"●  Temp очищен: {deleted} объектов"
    )

    messagebox.showinfo(
        "Очистка Temp",
        f"Удалено объектов: {deleted}"
    )


# =========================================================
# ОЧИСТКА ДИСКА
# =========================================================

def clean_disk_c():

    subprocess.Popen(
        ["cleanmgr.exe", "/d", "C:"],
        creationflags=subprocess.CREATE_NO_WINDOW
    )

    status_label.config(
        text="●  Запущена очистка диска C:"
    )


# =========================================================
# DNS
# =========================================================

def clean_dns():

    try:

        subprocess.run(
            ["ipconfig", "/flushdns"],
            creationflags=subprocess.CREATE_NO_WINDOW,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        status_label.config(
            text="●  DNS-кэш очищен"
        )

        messagebox.showinfo(
            "DNS",
            "DNS-кэш успешно очищен."
        )

    except Exception as e:

        messagebox.showerror(
            "Ошибка",
            str(e)
        )


# =========================================================
# WINDOWS UPDATE
# =========================================================

def clean_windows_update():

    answer = messagebox.askyesno(
        "Windows Update",
        "Очистить кэш скачанных обновлений?\n\n"
        "Установленные обновления удаляться не будут."
    )

    if not answer:
        return

    try:

        subprocess.run(
            ["net", "stop", "wuauserv"],
            creationflags=subprocess.CREATE_NO_WINDOW,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        folder = r"C:\Windows\SoftwareDistribution\Download"

        deleted = 0

        if os.path.exists(folder):

            for name in os.listdir(folder):

                path = os.path.join(
                    folder,
                    name
                )

                try:

                    if os.path.isfile(path):
                        os.remove(path)
                        deleted += 1

                    elif os.path.isdir(path):
                        shutil.rmtree(path)
                        deleted += 1

                except:
                    pass

        subprocess.run(
            ["net", "start", "wuauserv"],
            creationflags=subprocess.CREATE_NO_WINDOW,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        status_label.config(
            text="●  Windows Update очищен"
        )

        messagebox.showinfo(
            "Готово",
            f"Удалено объектов: {deleted}"
        )

    except Exception as e:

        messagebox.showerror(
            "Ошибка",
            "Возможно, нужны права администратора.\n\n"
            + str(e)
        )


# =========================================================
# КЭШ ЭСКИЗОВ
# =========================================================

def clean_thumbnails():

    local = os.environ.get("LOCALAPPDATA")

    if not local:
        return

    folder = os.path.join(
        local,
        "Microsoft",
        "Windows",
        "Explorer"
    )

    deleted = 0

    if os.path.exists(folder):

        for name in os.listdir(folder):

            if name.lower().startswith("thumbcache"):

                path = os.path.join(
                    folder,
                    name
                )

                try:

                    os.remove(path)
                    deleted += 1

                except:
                    pass

    status_label.config(
        text=f"●  Эскизы: удалено {deleted} файлов"
    )

    messagebox.showinfo(
        "Кэш эскизов",
        f"Удалено файлов: {deleted}"
    )


# =========================================================
# КОРЗИНА
# =========================================================

def empty_recycle_bin():

    if not messagebox.askyesno(
        "Корзина",
        "Очистить корзину?"
    ):
        return

    try:

        ctypes.windll.shell32.SHEmptyRecycleBinW(
            None,
            None,
            0
        )

        status_label.config(
            text="●  Корзина очищена"
        )

        messagebox.showinfo(
            "Готово",
            "Корзина очищена."
        )

    except Exception as e:

        messagebox.showerror(
            "Ошибка",
            str(e)
        )


# =========================================================
# АВТОЗАГРУЗКА
# =========================================================

def open_startup():

    try:

        subprocess.Popen(
            [
                "explorer.exe",
                "shell:startup"
            ]
        )

        status_label.config(
            text="●  Открыта папка автозагрузки"
        )

    except Exception as e:

        messagebox.showerror(
            "Ошибка",
            str(e)
        )


def open_task_manager_startup():

    try:

        subprocess.Popen(
            ["taskmgr"],
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        status_label.config(
            text="●  Открыт Диспетчер задач"
        )

    except Exception as e:

        messagebox.showerror(
            "Ошибка",
            str(e)
        )


# =========================================================
# ИНФОРМАЦИЯ О ПК
# =========================================================

def show_pc_info():

    try:

        cpu = platform.processor()

        if not cpu:
            cpu = "Не определён"

        ram = shutil.disk_usage("C:")

        memory_result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory"
            ],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        try:

            memory_bytes = int(
                memory_result.stdout.strip()
            )

            ram_gb = memory_bytes / (1024 ** 3)

        except:

            ram_gb = 0

        info = (
            f"Windows: {platform.system()} {platform.release()}\n"
            f"Версия: {platform.version()}\n"
            f"Архитектура: {platform.machine()}\n\n"
            f"CPU: {cpu}\n"
            f"RAM: {ram_gb:.1f} ГБ\n\n"
            f"Python: {platform.python_version()}"
        )

        messagebox.showinfo(
            "Информация о ПК",
            info
        )

    except Exception as e:

        messagebox.showerror(
            "Ошибка",
            str(e)
        )


# =========================================================
# ПРОВЕРКА WINDOWS
# =========================================================

def system_check():

    answer = messagebox.askyesno(
        "Проверка Windows",
        "Запустить проверку системных файлов?\n\n"
        "Windows выполнит SFC /scannow.\n"
        "Процесс может занять некоторое время."
    )

    if not answer:
        return

    status_label.config(
        text="●  Проверка Windows запущена..."
    )

    root.update()

    try:

        subprocess.Popen(
            [
                "cmd.exe",
                "/k",
                "sfc /scannow"
            ]
        )

        status_label.config(
            text="●  SFC запущен"
        )

    except Exception as e:

        messagebox.showerror(
            "Ошибка",
            str(e)
        )


# =========================================================
# DISM
# =========================================================

def dism_check():

    answer = messagebox.askyesno(
        "DISM",
        "Запустить проверку образа Windows?\n\n"
        "Команда:\n"
        "DISM /Online /Cleanup-Image /RestoreHealth\n\n"
        "Это может занять много времени."
    )

    if not answer:
        return

    status_label.config(
        text="●  DISM запущен..."
    )

    root.update()

    try:

        subprocess.Popen(
            [
                "cmd.exe",
                "/k",
                "DISM /Online /Cleanup-Image /RestoreHealth"
            ]
        )

    except Exception as e:

        messagebox.showerror(
            "Ошибка",
            str(e)
        )


# =========================================================
# СЕТЬ
# =========================================================

def network_reset():

    answer = messagebox.askyesno(
        "Сброс сети",
        "Выполнить сброс сетевого стека?\n\n"
        "Будут выполнены:\n"
        "• очистка DNS\n"
        "• сброс Winsock\n"
        "• сброс TCP/IP\n\n"
        "После этого может потребоваться перезагрузка."
    )

    if not answer:
        return

    try:

        commands = [
            ["ipconfig", "/flushdns"],
            ["netsh", "winsock", "reset"],
            ["netsh", "int", "ip", "reset"]
        ]

        for command in commands:

            subprocess.run(
                command,
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

        status_label.config(
            text="●  Сетевой стек сброшен"
        )

        messagebox.showinfo(
            "Готово",
            "Сброс сети выполнен.\n\n"
            "Рекомендуется перезагрузить ПК."
        )

    except Exception as e:

        messagebox.showerror(
            "Ошибка",
            "Может потребоваться запуск от администратора.\n\n"
            + str(e)
        )


# =========================================================
# ОЧИСТКА БЫСТРАЯ
# =========================================================

def quick_clean():

    answer = messagebox.askyesno(
        "Быстрая очистка",
        "Очистить Temp, DNS и кэш эскизов?"
    )

    if not answer:
        return

    clean_temp_silent()

    try:

        subprocess.run(
            ["ipconfig", "/flushdns"],
            creationflags=subprocess.CREATE_NO_WINDOW,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    except:
        pass

    clean_thumbnails_silent()

    status_label.config(
        text="●  Быстрая очистка завершена"
    )

    messagebox.showinfo(
        "Готово",
        "Очистка завершена."
    )


def clean_temp_silent():

    folder = tempfile.gettempdir()

    try:

        for name in os.listdir(folder):

            path = os.path.join(
                folder,
                name
            )

            try:

                if os.path.isfile(path) or os.path.islink(path):
                    os.remove(path)

                elif os.path.isdir(path):
                    shutil.rmtree(path)

            except:
                pass

    except:
        pass


def clean_thumbnails_silent():

    local = os.environ.get("LOCALAPPDATA")

    if not local:
        return

    folder = os.path.join(
        local,
        "Microsoft",
        "Windows",
        "Explorer"
    )

    if not os.path.exists(folder):
        return

    for name in os.listdir(folder):

        if name.lower().startswith("thumbcache"):

            try:

                os.remove(
                    os.path.join(folder, name)
                )

            except:
                pass


# =========================================================
# ИНСТРУМЕНТЫ
# =========================================================

def open_temp():

    os.startfile(
        tempfile.gettempdir()
    )


def open_taskmgr():

    subprocess.Popen(
        ["taskmgr"],
        creationflags=subprocess.CREATE_NO_WINDOW
    )


def restart_explorer():

    subprocess.run(
        ["taskkill", "/f", "/im", "explorer.exe"],
        creationflags=subprocess.CREATE_NO_WINDOW,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    time.sleep(1)

    subprocess.Popen(
        ["explorer.exe"],
        creationflags=subprocess.CREATE_NO_WINDOW
    )

    status_label.config(
        text="●  Explorer перезапущен"
    )


def lock_pc():

    subprocess.Popen(
        [
            "rundll32.exe",
            "user32.dll,LockWorkStation"
        ],
        creationflags=subprocess.CREATE_NO_WINDOW
    )


def restart_pc():

    if messagebox.askyesno(
        "Перезагрузка",
        "Точно перезагрузить компьютер?"
    ):

        subprocess.Popen(
            ["shutdown", "/r", "/t", "0"],
            creationflags=subprocess.CREATE_NO_WINDOW
        )


def open_downloads():

    folder = os.path.join(
        os.path.expanduser("~"),
        "Downloads"
    )

    if os.path.exists(folder):
        os.startfile(folder)
    else:
        messagebox.showerror(
            "Ошибка",
            "Папка Загрузки не найдена."
        )


# =========================================================
# СКРИНШОТ
# =========================================================

def make_screenshot():

    desktop = os.path.join(
        os.path.expanduser("~"),
        "Desktop"
    )

    path = os.path.join(
        desktop,
        f"screenshot_{int(time.time())}.png"
    )

    cmd = (
        "Add-Type -AssemblyName System.Windows.Forms; "
        "Add-Type -AssemblyName System.Drawing; "
        "$screen=[System.Windows.Forms.Screen]::PrimaryScreen; "
        "$bmp=New-Object Drawing.Bitmap("
        "$screen.Bounds.Width,"
        "$screen.Bounds.Height"
        "); "
        "$g=[Drawing.Graphics]::FromImage($bmp); "
        "$g.CopyFromScreen("
        "$screen.Bounds.X,"
        "$screen.Bounds.Y,"
        "0,0,"
        "$bmp.Size"
        "); "
        f"$bmp.Save('{path}'); "
        "$g.Dispose();"
        "$bmp.Dispose();"
    )

    try:

        subprocess.run(
            ["powershell", "-command", cmd],
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        status_label.config(
            text="●  Скриншот сохранён"
        )

        messagebox.showinfo(
            "Скриншот",
            f"Сохранён на рабочий стол:\n{path}"
        )

    except Exception as e:

        messagebox.showerror(
            "Ошибка",
            str(e)
        )


# =========================================================
# РЕДАКТОР РЕЕСТРА
# =========================================================

def open_regedit():
    try:
        # Запускаем Regedit через UAC с запросом прав администратора.
        result = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            "regedit.exe",
            None,
            None,
            1
        )

        if result <= 32:
            raise RuntimeError(f"Windows не смогла запустить Regedit (код {result})")

        status_label.config(text="●  Редактор реестра открыт от администратора")

    except Exception as e:
        messagebox.showerror(
            "Ошибка",
            "Не удалось открыть Regedit с правами администратора.\\n\\n"
            + str(e)
        )


# =========================================================
# КНОПКИ
# =========================================================

def make_btn(text, command, accent=False):
    holder = tk.Frame(
        content,
        bg=CARD,
        highlightthickness=1,
        highlightbackground=BORDER
    )
    holder.pack(fill="x", padx=6, pady=4)

    button = tk.Button(
        holder,
        text=text,
        command=command,
        bg=CARD,
        fg=TEXT,
        activebackground=CARD_2,
        activeforeground=TEXT,
        relief="flat",
        bd=0,
        font=("Segoe UI", 10, "bold"),
        anchor="w",
        padx=18,
        pady=12,
        cursor="hand2",
        highlightthickness=0
    )
    button.pack(fill="x")

    def enter(_):
        button.configure(
            bg=CARD_2,
            fg=ACCENT if accent else TEXT
        )

    def leave(_):
        button.configure(
            bg=CARD,
            fg=TEXT
        )

    button.bind("<Enter>", enter)
    button.bind("<Leave>", leave)
    return holder


section("Очистка")

make_btn("⚡  Быстрая очистка", quick_clean, True)
make_btn("🧹  Очистить Temp", clean_temp)
make_btn("🧹  Очистить диск C", clean_disk_c)
make_btn("🪟  Очистить Windows Update", clean_windows_update)
make_btn("🌐  Очистить DNS-кэш", clean_dns)
make_btn("🖼️  Очистить кэш эскизов", clean_thumbnails)
make_btn("🧺  Очистить корзину", empty_recycle_bin)


section("Система")

make_btn("🚀  Автозагрузка Windows", open_startup)
make_btn("🧠  Информация о ПК", show_pc_info)
make_btn("🩺  Проверка системных файлов", system_check)
make_btn("🔧  Восстановление Windows (DISM)", dism_check)
make_btn("🌐  Сброс сетевых компонентов", network_reset)
make_btn("📝  Открыть regedit", open_regedit)


section("Инструменты")

make_btn("📂  Открыть Temp", open_temp)
make_btn("📊  Диспетчер задач", open_taskmgr)
make_btn("🔄  Перезапустить Explorer", restart_explorer)
make_btn("📸  Скриншот рабочего стола", make_screenshot)
make_btn("📥  Открыть Загрузки", open_downloads)
make_btn("🔒  Заблокировать ПК", lock_pc)
make_btn("🔄  Перезагрузить ПК", restart_pc)

# Нижняя подпись
tk.Label(
    content,
    text="MakuTweaker Lite  •  готов к работе",
    fg="#596273",
    bg=BG,
    font=("Segoe UI", 9)
).pack(pady=(14, 20))

# =========================================================
# ЗАПУСК
# =========================================================

update_info()
root.mainloop()
