import sys
import os
import tkinter as tk
from tkinter import ttk
import platform
import psutil
import GPUtil
import socket
from datetime import datetime
import threading

# ========== ХАК ДЛЯ СКРЫТИЯ КОНСОЛИ (РАБОТАЕТ ТОЛЬКО НА WINDOWS) ==========
if sys.platform == 'win32':
    import ctypes
    # Прячем консольное окно
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
# =========================================================================

def get_size(bytes, suffix="B"):
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < 1024:
            return f"{bytes:.1f}{unit}{suffix}"
        bytes /= 1024
    return f"{bytes:.1f}PB{suffix}"

def load_info():
    info = {}
    
    # ОС
    info["OS"] = f"{platform.system()} {platform.release()}"
    info["Computer Name"] = socket.gethostname()
    info["Architecture"] = platform.machine()
    
    # CPU
    info["CPU"] = platform.processor() or "Не определён"
    cpu_freq = psutil.cpu_freq()
    if cpu_freq:
        info["CPU Frequency"] = f"{cpu_freq.current:.0f} MHz"
    info["Cores (Physical)"] = str(psutil.cpu_count(logical=False))
    info["Cores (Logical)"] = str(psutil.cpu_count(logical=True))
    info["CPU Usage"] = f"{psutil.cpu_percent(interval=0.5)}%"
    
    # RAM
    mem = psutil.virtual_memory()
    info["Total RAM"] = get_size(mem.total)
    info["Used RAM"] = f"{get_size(mem.used)} ({mem.percent}%)"
    info["Free RAM"] = get_size(mem.available)
    
    # GPU
    try:
        gpus = GPUtil.getGPUs()
        if gpus:
            gpu = gpus[0]
            info["GPU"] = gpu.name
            info["GPU Memory"] = f"{gpu.memoryUsed} MB / {gpu.memoryTotal} MB"
            info["GPU Load"] = f"{gpu.load*100:.0f}%"
            info["GPU Temp"] = f"{gpu.temperature}°C"
        else:
            info["GPU"] = "Не найдена"
    except:
        info["GPU"] = "Ошибка чтения (требуется NVIDIA)"
    
    # Disks
    disks_text = ""
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disks_text += f"{part.device} ({part.mountpoint}) — {get_size(usage.total)} ({usage.percent}% занято)\n"
        except:
            pass
    info["Disks"] = disks_text.strip()
    
    # Uptime
    boot = datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.now() - boot
    days = uptime.days
    hours = uptime.seconds // 3600
    minutes = (uptime.seconds % 3600) // 60
    info["Uptime"] = f"{days}d {hours}h {minutes}m (since {boot.strftime('%Y-%m-%d %H:%M')})"
    
    return info

class PCInfoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("System Info by Dreadware")
        self.root.geometry("750x650")
        self.root.minsize(700, 600)
        self.root.configure(bg="#0d0d0f")
        
        # Иконка (если есть, можно добавить, но без неё норм)
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass
        
        # Стили
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#0d0d0f")
        style.configure("TLabel", background="#0d0d0f", foreground="#e0e0e0", font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"), foreground="#c41e1e")
        style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"), foreground="#ffffff")
        style.configure("Info.TLabel", font=("Consolas", 9), foreground="#b8b8c8")
        style.configure("TNotebook", background="#0d0d0f", borderwidth=0)
        style.configure("TNotebook.Tab", background="#1a1a1f", foreground="#e0e0e0", padding=[12, 4])
        style.map("TNotebook.Tab", background=[("selected", "#2a2a30")])
        
        # Главный фрейм
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Заголовок
        title = ttk.Label(main_frame, text="DREADWARE SYSTEM ANALYZER", style="Title.TLabel")
        title.pack(pady=(0, 20))
        
        # Notebook (вкладки)
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Вкладки
        self.tab_summary = ttk.Frame(notebook)
        self.tab_details = ttk.Frame(notebook)
        self.tab_disks = ttk.Frame(notebook)
        notebook.add(self.tab_summary, text="📊 Summary")
        notebook.add(self.tab_details, text="⚙️ Details")
        notebook.add(self.tab_disks, text="💾 Storage")
        
        # Текстовые виджеты для вывода
        self.summary_text = tk.Text(self.tab_summary, wrap=tk.WORD, bg="#0d0d0f", fg="#e0e0e0", 
                                    font=("Consolas", 11), relief=tk.FLAT, padx=15, pady=15,
                                    selectbackground="#c41e1e", borderwidth=0)
        self.summary_text.pack(fill=tk.BOTH, expand=True)
        
        self.details_text = tk.Text(self.tab_details, wrap=tk.WORD, bg="#0d0d0f", fg="#e0e0e0",
                                    font=("Consolas", 10), relief=tk.FLAT, padx=15, pady=15,
                                    selectbackground="#c41e1e", borderwidth=0)
        self.details_text.pack(fill=tk.BOTH, expand=True)
        
        self.disks_text = tk.Text(self.tab_disks, wrap=tk.WORD, bg="#0d0d0f", fg="#e0e0e0",
                                  font=("Consolas", 10), relief=tk.FLAT, padx=15, pady=15,
                                  selectbackground="#c41e1e", borderwidth=0)
        self.disks_text.pack(fill=tk.BOTH, expand=True)
        
        # Кнопка обновления
        refresh_btn = tk.Button(main_frame, text="⟳ UPDATE", command=self.refresh,
                                bg="#c41e1e", fg="white", font=("Segoe UI", 10, "bold"),
                                relief=tk.FLAT, padx=20, pady=8, cursor="hand2",
                                activebackground="#8b0000", activeforeground="white")
        refresh_btn.pack(pady=(15, 0))
        
        # Статусная строка
        self.status = ttk.Label(main_frame, text="Ready", font=("Segoe UI", 8), foreground="#888888")
        self.status.pack(pady=(10, 0))
        
        # Загружаем информацию
        self.refresh()
    
    def refresh(self):
        self.status.config(text="Loading system info...")
        self.root.update()
        
        # Запускаем в отдельном потоке, чтобы окно не зависло
        thread = threading.Thread(target=self._load_and_display)
        thread.daemon = True
        thread.start()
    
    def _load_and_display(self):
        info = load_info()
        
        # Формируем summary
        summary = f"""
╔══════════════════════════════════════════════════════════╗
║                    SYSTEM SUMMARY                        ║
╚══════════════════════════════════════════════════════════╝

💻 OS:              {info.get('OS', 'N/A')}
🏷️  Computer Name:   {info.get('Computer Name', 'N/A')}
🖥️  Architecture:    {info.get('Architecture', 'N/A')}

⚡ CPU:             {info.get('CPU', 'N/A')}
🔢 Cores:           {info.get('Cores (Physical)', 'N/A')} physical, {info.get('Cores (Logical)', 'N/A')} logical
📈 CPU Usage:       {info.get('CPU Usage', 'N/A')}

🧠 RAM Total:       {info.get('Total RAM', 'N/A')}
📉 RAM Used:        {info.get('Used RAM', 'N/A')}
✅ RAM Free:        {info.get('Free RAM', 'N/A')}

🎮 GPU:             {info.get('GPU', 'N/A')}
🌡️  GPU Temp:        {info.get('GPU Temp', 'N/A')}
⚡ GPU Load:        {info.get('GPU Load', 'N/A')}

⏱️  Uptime:          {info.get('Uptime', 'N/A')}
        """
        
        # Детали
        details = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                       DETAILED INFO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

OPERATING SYSTEM
  System:      {info.get('OS', 'N/A')}
  Hostname:    {info.get('Computer Name', 'N/A')}
  Arch:        {info.get('Architecture', 'N/A')}

PROCESSOR (CPU)
  Model:       {info.get('CPU', 'N/A')}
  Frequency:   {info.get('CPU Frequency', 'N/A')}
  Physical cores: {info.get('Cores (Physical)', 'N/A')}
  Logical cores:  {info.get('Cores (Logical)', 'N/A')}
  Current load:   {info.get('CPU Usage', 'N/A')}

MEMORY (RAM)
  Total:       {info.get('Total RAM', 'N/A')}
  Used:        {info.get('Used RAM', 'N/A')}
  Available:   {info.get('Free RAM', 'N/A')}

GRAPHICS (GPU)
  Name:        {info.get('GPU', 'N/A')}
  Memory:      {info.get('GPU Memory', 'N/A')}
  Load:        {info.get('GPU Load', 'N/A')}
  Temperature: {info.get('GPU Temp', 'N/A')}

SYSTEM UPTIME
  {info.get('Uptime', 'N/A')}
        """
        
        # Диски
        disks_content = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                       STORAGE DEVICES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{info.get('Disks', 'No disks found')}
        """
        
        # Обновляем текстовые поля в главном потоке
        self.root.after(0, self._update_texts, summary, details, disks_content)
    
    def _update_texts(self, summary, details, disks_content):
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(tk.END, summary)
        
        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(tk.END, details)
        
        self.disks_text.delete(1.0, tk.END)
        self.disks_text.insert(tk.END, disks_content)
        
        self.status.config(text="Last update: " + datetime.now().strftime("%H:%M:%S"))

if __name__ == "__main__":
    root = tk.Tk()
    app = PCInfoApp(root)
    root.mainloop()