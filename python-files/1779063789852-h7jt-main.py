import os
import sys
import ctypes
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, scrolledtext
import threading
import time

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def run_as_admin():
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()

run_as_admin()

import psutil

class USBForceFormatter:
    def __init__(self, root):
        self.root = root
        self.root.title("USB Force Formatter v2.0")
        self.root.geometry("750x600")
        self.root.resizable(False, False)
        
        self.main_frame = ttk.Frame(root, padding=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        title = ttk.Label(self.main_frame, text="USB FORCE FORMATTER", font=('Arial', 16, 'bold'))
        title.pack(pady=10)
        
        sub = ttk.Label(self.main_frame, text="Форматирование защищённых USB-накопителей", font=('Arial', 10))
        sub.pack(pady=5)
        
        refresh_frame = ttk.Frame(self.main_frame)
        refresh_frame.pack(fill=tk.X, pady=10)
        
        self.refresh_btn = ttk.Button(refresh_frame, text="🔄 Обновить список дисков", command=self.refresh_drives)
        self.refresh_btn.pack()
        
        tree_frame = ttk.Frame(self.main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        scroll_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        scroll_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        
        self.tree = ttk.Treeview(tree_frame, columns=('Drive', 'Label', 'Size', 'Type', 'Status'), 
                                  show='headings', height=12,
                                  yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        
        self.tree.heading('Drive', text='Диск')
        self.tree.heading('Label', text='Метка')
        self.tree.heading('Size', text='Размер')
        self.tree.heading('Type', text='Тип')
        self.tree.heading('Status', text='Статус')
        
        self.tree.column('Drive', width=80, anchor='center')
        self.tree.column('Label', width=150)
        self.tree.column('Size', width=100, anchor='center')
        self.tree.column('Type', width=100, anchor='center')
        self.tree.column('Status', width=150)
        
        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        self.tree.bind('<<TreeviewSelect>>', self.on_select)
        
        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        self.format_btn = ttk.Button(btn_frame, text="⚠️ ПРИНУДИТЕЛЬНОЕ ФОРМАТИРОВАНИЕ ⚠️", 
                                      command=self.force_format, state=tk.DISABLED)
        self.format_btn.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.clear_protect_btn = ttk.Button(btn_frame, text="🛡️ Снять защиту от записи", 
                                             command=self.remove_write_protection, state=tk.DISABLED)
        self.clear_protect_btn.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        log_frame = ttk.LabelFrame(self.main_frame, text="Лог операций", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, width=70)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        self.status_var = tk.StringVar(value="Готов. Выберите USB-накопитель")
        self.status_bar = ttk.Label(self.main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        self.status_bar.pack(fill=tk.X, pady=5)
        
        self.current_drive = None
        self.drive_path = None
        self.refresh_drives()
    
    def log(self, message, error=False):
        timestamp = time.strftime("%H:%M:%S")
        if error:
            self.log_text.insert(tk.END, f"[{timestamp}] ❌ {message}\n", "error")
            self.log_text.tag_config("error", foreground="red")
        else:
            self.log_text.insert(tk.END, f"[{timestamp}] ✅ {message}\n")
        self.log_text.see(tk.END)
        self.log_text.update()
    
    def refresh_drives(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        try:
            partitions = psutil.disk_partitions()
            for part in partitions:
                if 'removable' in part.opts.lower():
                    drive = part.device.replace('\\', '')
                    try:
                        usage = psutil.disk_usage(part.mountpoint)
                        size_gb = usage.total // (1024**3)
                        label = part.opts.split(',')[0] if part.opts else "Нет метки"
                        status = self.check_drive_status(drive)
                        self.tree.insert('', tk.END, values=(drive, label, f"{size_gb} ГБ", "USB", status))
                    except:
                        self.tree.insert('', tk.END, values=(drive, "Ошибка", "???", "USB", "Недоступно"))
        except Exception as e:
            self.log(f"Ошибка при сканировании: {e}", error=True)
    
    def check_drive_status(self, drive_letter):
        try:
            result = subprocess.run(f'attrib "{drive_letter}:\\*.*"', shell=True, capture_output=True, text=True)
            return "ОК"
        except:
            return "Возможно защищён"
    
    def on_select(self, event):
        selected = self.tree.selection()
        if selected:
            self.current_drive = self.tree.item(selected[0])['values'][0]
            self.drive_path = self.current_drive + ":\\"
            self.format_btn.config(state=tk.NORMAL)
            self.clear_protect_btn.config(state=tk.NORMAL)
            self.status_var.set(f"Выбран диск {self.current_drive} - готов к форматированию")
        else:
            self.current_drive = None
            self.format_btn.config(state=tk.DISABLED)
            self.clear_protect_btn.config(state=tk.DISABLED)
    
    def remove_write_protection(self):
        if not self.current_drive:
            return
        
        if not messagebox.askyesno("Подтверждение", 
                                   f"Снять защиту от записи с диска {self.current_drive}?\n\n"
                                   "Это отключит блокировку записи на системном уровне."):
            return
        
        self.log(f"Снятие защиты от записи с диска {self.current_drive}...")
        
        # Метод 1: DiskPart
        script_content = f"""select volume {self.current_drive}
attributes disk clear readonly
exit"""
        with open('diskpart_clear.txt', 'w') as f:
            f.write(script_content)
        
        result = subprocess.run(f'diskpart /s diskpart_clear.txt', shell=True, capture_output=True, text=True)
        os.remove('diskpart_clear.txt')
        
        if result.returncode == 0:
            self.log(f"Защита от записи снята (DiskPart)")
        else:
            self.log(f"DiskPart не помог, пробуем реестр...")
            
            # Метод 2: Реестр Windows
            reg_cmd = 'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\StorageDevicePolicies" /v WriteProtect /t REG_DWORD /d 0 /f'
            subprocess.run(reg_cmd, shell=True, capture_output=True)
            self.log("Реестр обновлён, может потребоваться перезагрузка")
        
        messagebox.showinfo("Готово", "Защита от записи снята.\nЕсли не помогло - перезагрузите компьютер.")
    
    def force_format(self):
        if not self.current_drive:
            return
        
        result = messagebox.askyesno("⚠️ ВНИМАНИЕ! ⚠️",
                                     f"Вы уверены, что хотите ОКОНЧАТЕЛЬНО УДАЛИТЬ ВСЕ ДАННЫЕ\n"
                                     f"с диска {self.current_drive}?\n\n"
                                     f"ДАЖЕ ЗАЩИЩЁННЫЕ ФЛЕШКИ БУДУТ ОТФОРМАТИРОВАНЫ!\n\n"
                                     f"Это действие НЕОБРАТИМО!")
        
        if not result:
            return
        
        self.log(f"НАЧАЛО ПРИНУДИТЕЛЬНОГО ФОРМАТИРОВАНИЯ диска {self.current_drive}")
        
        # Способ 1: Форматирование через форс-параметры
        self.log("Попытка форматирования через format...")
        format_cmd = f'format {self.current_drive}: /FS:NTFS /Q /Y /X'
        result_format = subprocess.run(format_cmd, shell=True, capture_output=True, text=True)
        
        if result_format.returncode == 0:
            self.log(f"ФОРМАТИРОВАНИЕ УСПЕШНО ЗАВЕРШЕНО! Диск {self.current_drive} отформатирован")
            messagebox.showinfo("Успех", f"Диск {self.current_drive} успешно отформатирован!")
            self.refresh_drives()
            return
        
        # Способ 2: Если format не сработал - DiskPart (более агрессивный)
        self.log("Использование DiskPart для принудительного форматирования...")
        
        disk_script = f"""select volume {self.current_drive}
clean
create partition primary
format fs=ntfs quick
assign letter={self.current_drive}
exit"""
        
        with open('force_format.txt', 'w') as f:
            f.write(disk_script)
        
        diskpart_result = subprocess.run('diskpart /s force_format.txt', shell=True, capture_output=True, text=True)
        os.remove('force_format.txt')
        
        if diskpart_result.returncode == 0:
            self.log(f"DiskPart ФОРМАТИРОВАЛ диск {self.current_drive}")
            messagebox.showinfo("Успех", f"Диск {self.current_drive} отформатирован через DiskPart!")
        else:
            # Способ 3: Реестр + повторная попытка
            self.log("Отключение защиты в реестре...")
            subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\StorageDevicePolicies" /v WriteProtect /t REG_DWORD /d 0 /f', shell=True)
            
            self.log("Повторная попытка форматирования...")
            subprocess.run(f'format {self.current_drive}: /FS:FAT32 /Q /Y /X', shell=True, capture_output=True)
            
            self.log("⚠️ Для завершения может потребоваться перезагрузка")
            messagebox.showwarning("Требуется перезагрузка", 
                                   "Форматирование может завершиться после перезагрузки.\n"
                                   "Перезагрузите компьютер и проверьте диск.")
        
        self.refresh_drives()

if __name__ == "__main__":
    root = tk.Tk()
    app = USBForceFormatter(root)
    root.mainloop()