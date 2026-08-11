import ctypes
import os
import sys

# Прячем консоль намертво
if sys.platform == "win32":
  try:
    ctypes.windll.user32.ShowWindow(
        ctypes.windll.kernel32.GetConsoleWindow(), 0
    )
  except:
    pass

import glob
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Попытка импортировать библиотеку для глобальных горячих клавиш
try:
  import keyboard
except ImportError:
  keyboard = None


def resource_path(relative_path):
  """Возвращает путь к файлу с учетом папки Core"""
  try:
    base_path = sys._MEIPASS
  except Exception:
    base_path = os.path.abspath(".")
  return os.path.join(base_path, "Core", relative_path)


class ModernAntivirusApp:

  def __init__(self, root):
    self.root = root
    self.root.title("NexusCore Security // Ultimate Edition")
    self.root.geometry("980x650")
    self.root.minsize(850, 550)

    # Переменная состояния уведомлений внутри приложения
    self.notifications_enabled = tk.BooleanVar(value=True)

    # Кастомная киберпанк/хакерская палитра
    self.colors = {
        "bg": "#0d1117",
        "panel": "#161b22",
        "border": "#30363d",
        "accent": "#2ea043",
        "accent_hover": "#3fb950",
        "text": "#c9d1d9",
        "text_muted": "#8b949e",
        "danger": "#f85149",
        "danger_hover": "#da3633",
        "warning": "#d29922",
    }

    self.root.configure(bg=self.colors["bg"])
    self.setup_styles()
    self.create_nav_bar()

    self.content_container = tk.Frame(self.root, bg=self.colors["bg"])
    self.content_container.pack(fill=tk.BOTH, expand=True)

    # При старте открываем аварийный пульт
    self.show_general_tab()

    # Запускаем фоновый слушатель секретной комбинации клавиш
    self.init_global_hotkey()

  def setup_styles(self):
    style = ttk.Style()
    style.theme_use("clam")

    style.configure(
        "Custom.TCombobox",
        fieldbackground=self.colors["panel"],
        background=self.colors["panel"],
        foreground=self.colors["text"],
        darkcolor=self.colors["border"],
        lightcolor=self.colors["border"],
        bordercolor=self.colors["border"],
        arrowcolor=self.colors["accent"],
    )
    style.map(
        "Custom.TCombobox",
        fieldbackground=[("readonly", self.colors["panel"])],
        foreground=[("readonly", self.colors["text"])],
    )

  def create_nav_bar(self):
    nav_frame = tk.Frame(
        self.root, bg=self.colors["panel"], height=50, bd=0, highlightthickness=0
    )
    nav_frame.pack(fill=tk.X, side=tk.TOP)
    nav_frame.pack_propagate(False)

    logo_label = tk.Label(
        nav_frame,
        text="  NEXUS SECURE  ",
        bg=self.colors["panel"],
        fg=self.colors["accent"],
        font=("Consolas", 11, "bold"),
    )
    logo_label.pack(side=tk.LEFT, padx=10)

    self.nav_buttons = {}

    tabs = [
        ("Общие (Авария)", self.show_general_tab),
        ("Сканер", self.show_scanner_tab),
        ("Процессы (Монитор)", self.show_monitor_tab),
        ("Анти-Антивирус", self.show_antiav_tab),
        ("Карантин", self.show_quarantine_tab),
        ("Уведомление о угрозе", self.show_notification_tab),
    ]

    for name, cmd in tabs:
      btn = tk.Button(
          nav_frame,
          text=name,
          bg=self.colors["panel"],
          fg=self.colors["text_muted"],
          activebackground=self.colors["border"],
          activeforeground=self.colors["text"],
          bd=0,
          font=("Consolas", 9, "bold"),
          padx=10,
          command=cmd,
      )
      btn.pack(side=tk.LEFT, fill=tk.Y)
      self.nav_buttons[name] = btn

  def update_active_nav(self, active_name):
    for name, btn in self.nav_buttons.items():
      if name == active_name:
        btn.config(fg=self.colors["accent"], font=("Consolas", 9, "bold"))
      else:
        btn.config(fg=self.colors["text_muted"], font=("Consolas", 9))

  def clear_content(self):
    for widget in self.content_container.winfo_children():
      widget.destroy()

  # --- СЕКРЕТНАЯ КОМБИНАЦИЯ ---
  def init_global_hotkey(self):
    if keyboard is not None:
      try:
        keyboard.add_hotkey("ctrl+alt+shift+q", self.trigger_emergency_hotkey)
      except Exception as e:
        print(f"Не удалось зарегистрировать глобальный хоткей: {e}")

  def trigger_emergency_hotkey(self):
    self.root.deiconify()
    self.root.lift()
    self.root.attributes("-topmost", True)
    self.root.after(1000, lambda: self.root.attributes("-topmost", False))
    self.show_general_tab()

  # --- ВКЛАДКА 0: ОБЩИЕ (АВАРИЙНЫЙ ПУЛЬТ) ---
  def show_general_tab(self):
    self.clear_content()
    self.update_active_nav("Общие (Авария)")

    frame = tk.Frame(self.content_container, bg=self.colors["bg"])
    frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)

    tk.Label(
        frame,
        text="ЭКСТРЕННЫЙ АВАРИЙНЫЙ ПУЛЬТ ЗАЩИТЫ",
        bg=self.colors["bg"],
        fg=self.colors["danger"],
        font=("Consolas", 13, "bold"),
    ).pack(anchor=tk.W, pady=(0, 2))

    tk.Label(
        frame,
        text=(
            "Секретный хоткей для вызова: [Ctrl + Alt + Shift + Q] (работает"
            " всегда)"
        ),
        bg=self.colors["bg"],
        fg=self.colors["accent"],
        font=("Consolas", 9, "bold"),
    ).pack(anchor=tk.W, pady=(0, 15))

    grid_frame = tk.Frame(frame, bg=self.colors["bg"])
    grid_frame.pack(fill=tk.BOTH, expand=True)

    btn_del_last = tk.Button(
        grid_frame,
        text="🗑 Удалить последний\nзапущенный файл",
        bg=self.colors["panel"],
        fg=self.colors["danger"],
        bd=1,
        relief="solid",
        font=("Consolas", 10, "bold"),
        command=self.emergency_delete_last_file,
    )
    btn_del_last.grid(
        row=0, column=0, sticky="nsew", padx=8, pady=8, ipady=12
    )

    btn_taskmgr = tk.Button(
        grid_frame,
        text="⚡ Запустить\nДиспетчер задач",
        bg=self.colors["panel"],
        fg=self.colors["warning"],
        bd=1,
        relief="solid",
        font=("Consolas", 10, "bold"),
        command=self.emergency_open_taskmgr,
    )
    btn_taskmgr.grid(row=0, column=1, sticky="nsew", padx=8, pady=8, ipady=12)

    btn_safemode = tk.Button(
        grid_frame,
        text="🛡 Безопасный режим\n(Safe Mode)",
        bg=self.colors["panel"],
        fg=self.colors["text"],
        bd=1,
        relief="solid",
        font=("Consolas", 10, "bold"),
        command=self.emergency_safe_mode,
    )
    btn_safemode.grid(row=1, column=0, sticky="nsew", padx=8, pady=8, ipady=12)

    btn_reboot = tk.Button(
        grid_frame,
        text="🔄 Перезагрузка\nсистемы",
        bg=self.colors["panel"],
        fg=self.colors["warning"],
        bd=1,
        relief="solid",
        font=("Consolas", 10, "bold"),
        command=self.emergency_reboot,
    )
    btn_reboot.grid(row=1, column=1, sticky="nsew", padx=8, pady=8, ipady=12)

    btn_shutdown = tk.Button(
        grid_frame,
        text="🛑 ВЫКЛЮЧИТЬ КОМПЬЮТЕР (АВАРИЯ)",
        bg=self.colors["danger"],
        fg="#ffffff",
        bd=0,
        font=("Consolas", 11, "bold"),
        command=self.emergency_shutdown,
    )
    btn_shutdown.grid(
        row=2, column=0, columnspan=2, sticky="nsew", padx=8, pady=12, ipady=12
    )

    grid_frame.columnconfigure(0, weight=1)
    grid_frame.columnconfigure(1, weight=1)

  # --- ВКЛАДКА 1: СКАНЕР (Связано с C++ ядром) ---
  def show_scanner_tab(self):
    self.clear_content()
    self.update_active_nav("Сканер")

    frame = tk.Frame(self.content_container, bg=self.colors["bg"])
    frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    top_panel = tk.Frame(frame, bg=self.colors["bg"])
    top_panel.pack(fill=tk.X, pady=(0, 12))

    self.path_entry = tk.Entry(
        top_panel,
        bg=self.colors["panel"],
        fg=self.colors["text"],
        font=("Consolas", 10),
        bd=1,
        relief="solid",
        highlightthickness=1,
        highlightbackground=self.colors["border"],
        highlightcolor=self.colors["accent"],
        insertbackground="white",
    )
    self.path_entry.pack(
        side=tk.LEFT, fill=tk.X, expand=True, ipady=6, padx=(0, 10)
    )

    browse_btn = tk.Button(
        top_panel,
        text="Выбрать...",
        bg=self.colors["panel"],
        fg=self.colors["text"],
        bd=1,
        relief="solid",
        font=("Consolas", 9),
        padx=12,
        command=self.browse_folder,
    )
    browse_btn.pack(side=tk.LEFT, padx=(0, 6))

    full_pc_btn = tk.Button(
        top_panel,
        text="Весь ПК (C:\\)",
        bg=self.colors["panel"],
        fg=self.colors["warning"],
        bd=1,
        relief="solid",
        font=("Consolas", 9, "bold"),
        padx=10,
        command=self.select_full_pc,
    )
    full_pc_btn.pack(side=tk.LEFT, padx=(0, 10))

    scan_btn = tk.Button(
        top_panel,
        text="ЗАПУСК",
        bg=self.colors["accent"],
        fg="#ffffff",
        bd=0,
        font=("Consolas", 9, "bold"),
        padx=18,
        command=self.start_scan,
    )
    scan_btn.pack(side=tk.LEFT, ipady=3)

    filter_panel = tk.Frame(frame, bg=self.colors["bg"])
    filter_panel.pack(fill=tk.X, pady=(0, 15))

    tk.Label(
        filter_panel,
        text="Режим анализа:",
        bg=self.colors["bg"],
        fg=self.colors["text_muted"],
        font=("Consolas", 9),
    ).pack(side=tk.LEFT, padx=(0, 10))

    self.file_type_var = tk.StringVar(value="Все файлы (*.*)")
    file_types_combobox = ttk.Combobox(
        filter_panel,
        textvariable=self.file_type_var,
        values=[
            "Все файлы (*.*)",
            "Только исполняемые (.exe, .bat, .cmd)",
            "Скрипты и документы",
        ],
        state="readonly",
        width=35,
        style="Custom.TCombobox",
    )
    file_types_combobox.pack(side=tk.LEFT)

    save_log_btn = tk.Button(
        filter_panel,
        text="Сохранить отчет",
        bg=self.colors["panel"],
        fg=self.colors["text_muted"],
        bd=1,
        relief="solid",
        font=("Consolas", 8),
        padx=8,
        command=self.save_scan_log,
    )
    save_log_btn.pack(side=tk.RIGHT)

    log_frame = tk.Frame(
        frame,
        bg=self.colors["panel"],
        bd=1,
        relief="solid",
        highlightbackground=self.colors["border"],
    )
    log_frame.pack(fill=tk.BOTH, expand=True)

    self.log_text = tk.Text(
        log_frame,
        bg=self.colors["panel"],
        fg=self.colors["accent"],
        font=("Consolas", 10),
        bd=0,
        highlightthickness=0,
        insertbackground="white",
    )
    self.log_text.pack(
        side=tk.LEFT, fill=tk.BOTH, expand=True, padx=12, pady=12
    )

    scrollbar = ttk.Scrollbar(
        log_frame, orient="vertical", command=self.log_text.yview
    )
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    self.log_text.configure(yscrollcommand=scrollbar.set)

    self.log_text.insert(
        tk.END,
        "[System] Secure Core инициализирован. C++ Движок готов к работе.\n",
    )

  # --- ВКЛАДКА 2: МОНИТОР ПРОЦЕССОВ ---
  def show_monitor_tab(self):
    self.clear_content()
    self.update_active_nav("Процессы (Монитор)")

    frame = tk.Frame(self.content_container, bg=self.colors["bg"])
    frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    top_m_panel = tk.Frame(frame, bg=self.colors["bg"])
    top_m_panel.pack(fill=tk.X, pady=(0, 10))

    tk.Label(
        top_m_panel,
        text="Активные процессы системы (Анализ памяти)",
        bg=self.colors["bg"],
        fg=self.colors["text"],
        font=("Consolas", 11, "bold"),
    ).pack(side=tk.LEFT)

    refresh_btn = tk.Button(
        top_m_panel,
        text="Обновить список",
        bg=self.colors["panel"],
        fg=self.colors["accent"],
        bd=1,
        relief="solid",
        font=("Consolas", 9),
        padx=10,
        command=self.load_processes,
    )
    refresh_btn.pack(side=tk.RIGHT)

    tree_frame = tk.Frame(frame, bg=self.colors["panel"])
    tree_frame.pack(fill=tk.BOTH, expand=True)

    self.proc_tree = ttk.Treeview(
        tree_frame, columns=("PID", "Name"), show="headings", height=15
    )
    self.proc_tree.heading("PID", text="PID (ID процесса)")
    self.proc_tree.heading("Name", text="Имя процесса / Исполняемый файл")
    self.proc_tree.column("PID", width=120, anchor=tk.CENTER)
    self.proc_tree.column("Name", width=550, anchor=tk.W)

    p_scroll = ttk.Scrollbar(
        tree_frame, orient="vertical", command=self.proc_tree.yview
    )
    self.proc_tree.configure(yscrollcommand=p_scroll.set)

    self.proc_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    p_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    self.load_processes()

  # --- ВКЛАДКА 3: АНТИ-АНТИВИРУС ---
  def show_antiav_tab(self):
    self.clear_content()
    self.update_active_nav("Анти-Антивирус")

    frame = tk.Frame(self.content_container, bg=self.colors["bg"])
    frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)

    tk.Label(
        frame,
        text="ПОИСК И УПРАВЛЕНИЕ ПОСТОРОННИМИ АНТИВИРУСАМИ",
        bg=self.colors["bg"],
        fg=self.colors["warning"],
        font=("Consolas", 12, "bold"),
    ).pack(anchor=tk.W, pady=(0, 5))

    tk.Label(
        frame,
        text=(
            "Здесь можно обнаружить установленные сторонние защитные ПО"
            " (Касперский, 360, Avast и др.), выключить их процессы, удалить"
            " либо открыть их папку."
        ),
        bg=self.colors["bg"],
        fg=self.colors["text_muted"],
        font=("Consolas", 9),
    ).pack(anchor=tk.W, pady=(0, 15))

    control_panel = tk.Frame(frame, bg=self.colors["bg"])
    control_panel.pack(fill=tk.X, pady=(0, 10))

    scan_av_btn = tk.Button(
        control_panel,
        text="🔍 Сканировать систему на другие антивирусы",
        bg=self.colors["panel"],
        fg=self.colors["accent"],
        bd=1,
        relief="solid",
        font=("Consolas", 9, "bold"),
        padx=12,
        command=self.scan_for_other_antiviruses,
    )
    scan_av_btn.pack(side=tk.LEFT)

    av_frame = tk.Frame(frame, bg=self.colors["panel"])
    av_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

    self.av_tree = ttk.Treeview(
        av_frame, columns=("Name", "Status", "Path"), show="headings", height=8
    )
    self.av_tree.heading("Name", text="Имя защитника / Программы")
    self.av_tree.heading("Status", text="Статус в системе")
    self.av_tree.heading("Path", text="Путь к исполняемому файлу / папке")

    self.av_tree.column("Name", width=180, anchor=tk.W)
    self.av_tree.column("Status", width=130, anchor=tk.CENTER)
    self.av_tree.column("Path", width=380, anchor=tk.W)

    av_scroll = ttk.Scrollbar(
        av_frame, orient="vertical", command=self.av_tree.yview
    )
    self.av_tree.configure(yscrollcommand=av_scroll.set)

    self.av_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    av_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    actions_panel = tk.Frame(frame, bg=self.colors["bg"])
    actions_panel.pack(fill=tk.X)

    btn_kill_av = tk.Button(
        actions_panel,
        text="⚡ Выключить / Завершить",
        bg=self.colors["panel"],
        fg=self.colors["warning"],
        bd=1,
        relief="solid",
        font=("Consolas", 9),
        padx=10,
        command=self.action_kill_av,
    )
    btn_kill_av.pack(side=tk.LEFT, padx=(0, 10))

    btn_open_folder = tk.Button(
        actions_panel,
        text="📁 Зайти (Открыть папку)",
        bg=self.colors["panel"],
        fg=self.colors["text"],
        bd=1,
        relief="solid",
        font=("Consolas", 9),
        padx=10,
        command=self.action_open_av_folder,
    )
    btn_open_folder.pack(side=tk.LEFT, padx=(0, 10))

    btn_delete_av = tk.Button(
        actions_panel,
        text="🗑 Удалить",
        bg=self.colors["panel"],
        fg=self.colors["danger"],
        bd=1,
        relief="solid",
        font=("Consolas", 9),
        padx=10,
        command=self.action_delete_av,
    )
    btn_delete_av.pack(side=tk.LEFT)

    self.scan_for_other_antiviruses()

  # --- ВКЛАДКА 4: КАРАНТИН ---
  def show_quarantine_tab(self):
    self.clear_content()
    self.update_active_nav("Карантин")

    frame = tk.Frame(self.content_container, bg=self.colors["bg"])
    frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    tk.Label(
        frame,
        text="Хранилище изолированных угроз пусто",
        bg=self.colors["bg"],
        fg=self.colors["text_muted"],
        font=("Consolas", 11),
    ).pack(pady=80)

  # --- ВКЛАДКА 5: УВЕДОМЛЕНИЕ О УГРОЗЕ (НОВАЯ) ---
  def show_notification_tab(self):
    self.clear_content()
    self.update_active_nav("Уведомление о угрозе")

    frame = tk.Frame(self.content_container, bg=self.colors["bg"])
    frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)

    tk.Label(
        frame,
        text="НАСТРОЙКА УВЕДОМЛЕНИЙ ОБ УГРОЗАХ",
        bg=self.colors["bg"],
        fg=self.colors["accent"],
        font=("Consolas", 12, "bold"),
    ).pack(anchor=tk.W, pady=(0, 10))

    tk.Label(
        frame,
        text=(
            "Здесь вы можете подтвердить и управлять отображением"
            " предупреждений\nпри обнаружении подозрительных элементов в"
            " системе."
        ),
        bg=self.colors["bg"],
        fg=self.colors["text_muted"],
        font=("Consolas", 10),
        justify="left",
    )
    frame_desc_height = 5  # отступ для красоты
    frame_desc = tk.Frame(frame, bg=self.colors["bg"], height=frame_desc_height)
    frame_desc.pack(anchor=tk.W, pady=(0, 10))

    # Чекбокс подтверждения уведомлений
    chk_notif = tk.Checkbutton(
        frame,
        text="Разрешить и показывать уведомления о защите",
        variable=self.notifications_enabled,
        command=self.on_notification_toggle,
        bg=self.colors["bg"],
        fg=self.colors["text"],
        selectcolor=self.colors["panel"],
        activebackground=self.colors["bg"],
        activeforeground=self.colors["accent"],
        font=("Consolas", 10, "bold"),
    )
    chk_notif.pack(anchor=tk.W, pady=(0, 15))

    self.notif_status_lbl = tk.Label(
        frame,
        text="",
        bg=self.colors["bg"],
        fg=self.colors["accent"],
        font=("Consolas", 9),
    )
    self.notif_status_lbl.pack(anchor=tk.W)

  def on_notification_toggle(self):
    status = (
        "включены" if self.notifications_enabled.get() else "отключены"
    )
    self.notif_status_lbl.config(text=f"[✓] Уведомления теперь {status}")

  # --- ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ И ЛОГИКА ---
  def load_processes(self):
    for item in self.proc_tree.get_children():
      self.proc_tree.delete(item)
    try:
      output = subprocess.check_output(
          ["tasklist", "/FO", "CSV", "/NH"], text=True, errors="ignore"
      )
      for line in output.splitlines():
        parts = line.replace('"', "").split(",")
        if len(parts) >= 2:
          self.proc_tree.insert("", tk.END, values=(parts[1], parts[0]))
    except Exception as e:
      self.proc_tree.insert("", tk.END, values=("ERR", str(e)))

  def scan_for_other_antiviruses(self):
    for item in self.av_tree.get_children():
      self.av_tree.delete(item)

    known_targets = {
        "Kaspersky (AVP)": "avp.exe",
        "360 Total Security": "360tstit.exe",
        "Avast Antivirus": "avastui.exe",
        "Malwarebytes": "mbam.exe",
        "ESET NOD32": "egui.exe",
        "Avira Antivirus": "avguard.exe",
        "Dr.Web": "dwengine.exe",
    }

    try:
      running_procs = subprocess.check_output(
          ["tasklist", "/FO", "CSV", "/NH"], text=True, errors="ignore"
      ).lower()

      found_count = 0
      for name, exe in known_targets.items():
        status = "Не обнаружен"
        path_info = "В памяти не найден"

        if exe in running_procs:
          status = "Активен (Запущен)"
          path_info = f"Процесс: {exe}"
          found_count += 1

        self.av_tree.insert("", tk.END, values=(name, status, path_info))

      if found_count == 0:
        self.av_tree.insert(
            "",
            tk.END,
            values=(
                "Конкуренты не найдены",
                "Чисто",
                "Активных чужих антивирусов нет",
            ),
        )
    except Exception as e:
      self.av_tree.insert("", tk.END, values=("Ошибка сканирования", "ERR", str(e)))

  def action_kill_av(self):
    selected = self.av_tree.selection()
    if not selected:
      messagebox.showerror(
          "Ошибка", "Выберите элемент из списка для выключения!"
      )
      return
    item = self.av_tree.item(selected)
    vals = item["values"]
    if vals:
      av_name = vals[0]
      path_info = str(vals[2])
      if "Процесс: " in path_info:
        exe_name = path_info.replace("Процесс: ", "").strip()
        if messagebox.askyesno(
            "Подтверждение", f"Принудительно завершить процесс {exe_name}?"
        ):
          os.system(f"taskkill /f /im {exe_name}")
          messagebox.showinfo("Успех", f"Процесс {exe_name} завершен!")
          self.scan_for_other_antiviruses()
      else:
        messagebox.showinfo("Инфо", f"Защитник {av_name} сейчас не запущен.")

  def action_open_av_folder(self):
    selected = self.av_tree.selection()
    if not selected:
      messagebox.showerror("Ошибка", "Выберите элемент из списка!")
      return
    try:
      pf = os.environ.get("ProgramFiles", "C:\\Program Files")
      os.startfile(pf)
    except Exception as e:
      messagebox.showerror("Ошибка", f"Не удалось открыть папку: {e}")

  def action_delete_av(self):
    selected = self.av_tree.selection()
    if not selected:
      messagebox.showerror("Ошибка", "Выберите антивирус для удаления!")
      return
    item = self.av_tree.item(selected)
    vals = item["values"]
    if vals:
      av_name = vals[0]
      if messagebox.askyesno(
          "Внимание",
          f"Вызвать средство удаления для {av_name} через панель управления?",
      ):
        os.system("control appwiz.cpl")

  def browse_folder(self):
    folder_selected = filedialog.askdirectory()
    if folder_selected:
      self.path_entry.delete(0, tk.END)
      self.path_entry.insert(0, folder_selected)

  def select_full_pc(self):
    self.path_entry.delete(0, tk.END)
    self.path_entry.insert(0, "C:\\")

  def save_scan_log(self):
    log_content = self.log_text.get("1.0", tk.END)
    file_path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
        initialfile="NexusScan_Report.txt",
    )
    if file_path:
      try:
        with open(file_path, "w", encoding="utf-8") as f:
          f.write(log_content)
        messagebox.showinfo("Успех", "Отчет сканирования сохранен!")
      except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}")

  def start_scan(self):
    target_path = self.path_entry.get()
    if not target_path:
      messagebox.showerror("Ошибка", "Укажите путь для сканирования!")
      return

    self.log_text.insert(
        tk.END, f"\n[~] Запуск сканирования через C++ ядро: {target_path}...\n"
    )
    self.log_text.see(tk.END)

    exe_name = resource_path("CoreGuard.exe")
    if not os.path.exists(exe_name):
      self.log_text.insert(
          tk.END, f"[!] Ошибка: CoreGuard.exe не найден по пути:\n{exe_name}\n"
      )
      return

    try:
      creationflags = 0
      if sys.platform == "win32":
        creationflags = subprocess.CREATE_NO_WINDOW

      process = subprocess.Popen(
          [exe_name, target_path, self.file_type_var.get()],
          stdout=subprocess.PIPE,
          stderr=subprocess.STDOUT,
          text=True,
          creationflags=creationflags,
      )

      def read_output():
        for line in process.stdout:
          self.log_text.insert(tk.END, line)
          self.log_text.see(tk.END)

      threading.Thread(target=read_output, daemon=True).start()
    except Exception as e:
      self.log_text.insert(tk.END, f"[!] Ошибка запуска ядра: {str(e)}\n")

  def emergency_shutdown(self):
    if messagebox.askyesno("Внимание", "Выключить компьютер немедленно?"):
      os.system("shutdown /s /f /t 0")

  def emergency_reboot(self):
    if messagebox.askyesno("Внимание", "Перезагрузить компьютер?"):
      os.system("shutdown /r /f /t 0")

  def emergency_open_taskmgr(self):
    try:
      subprocess.Popen("taskmgr.exe")
    except Exception as e:
      messagebox.showerror("Ошибка", f"Не удалось открыть Диспетчер: {e}")

  def emergency_safe_mode(self):
    if messagebox.askyesno("Безопасный режим", "Перезагрузить ПК в Safe Mode?"):
      try:
        os.system("bcdedit /set {current} safemode network")
        os.system("shutdown /r /f /t 0")
      except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось включить Safe Mode: {e}")

  def emergency_delete_last_file(self):
    try:
      user_profile = os.environ.get("USERPROFILE", "C:\\Users\\Default")
      downloads_path = os.path.join(user_profile, "Downloads")
      desktop_path = os.path.join(user_profile, "Desktop")

      all_files = []
      for p in [downloads_path, desktop_path]:
        if os.path.exists(p):
          for f in glob.glob(os.path.join(p, "*.*")):
            if os.path.isfile(f):
              all_files.append((f, os.path.getmtime(f)))

      if not all_files:
        messagebox.showinfo("Инфо", "Недавние файлы не найдены.")
        return

      all_files.sort(key=lambda x: x[1], reverse=True)
      last_file = all_files[0][0]

      if messagebox.askyesno(
          "Удаление угрозы", f"Удалить последний файл:\n{last_file}?"
      ):
        file_name = os.path.basename(last_file)
        os.system(f"taskkill /f /im {file_name}")
        os.remove(last_file)
        messagebox.showinfo("Успех", f"Файл {file_name} уничтожен!")
    except Exception as e:
      messagebox.showerror("Ошибка", f"Не удалось удалить файл: {e}")


if __name__ == "__main__":
  root = tk.Tk()
  app = ModernAntivirusApp(root)
  root.mainloop()