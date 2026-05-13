import os
import shutil
import subprocess
import sys
import winreg
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import ctypes
import time
import stat

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def force_delete(path):
    """Абсолютно гарантированное удаление"""
    try:
        if os.path.exists(path):
            os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
            if os.path.isfile(path):
                os.remove(path)
            else:
                shutil.rmtree(path, ignore_errors=False)
            return True
    except:
        try:
            if os.path.isfile(path):
                subprocess.run(f'del /f /q "{path}"', shell=True, capture_output=True)
            else:
                subprocess.run(f'rmdir /s /q "{path}"', shell=True, capture_output=True)
            return True
        except:
            pass
    return False

class AppRemover:
    def __init__(self, root):
        self.root = root
        self.root.title("Полный удалятор - ROJECT MODE")
        self.root.geometry("800x600")
        self.root.attributes('-topmost', True)
        
        bg_color = "#1a1a1a"
        fg_color = "#ffffff"
        btn_color = "#8b0000"
        
        self.root.configure(bg=bg_color)
        
        title = tk.Label(root, text="УНИЧТОЖИТЕЛЬ ПРИЛОЖЕНИЙ", font=("Arial", 18, "bold"), 
                        fg=btn_color, bg=bg_color)
        title.pack(pady=15)
        
        search_frame = tk.Frame(root, bg=bg_color)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(search_frame, text="Поиск:", fg=fg_color, bg=bg_color).pack(side=tk.LEFT, padx=5)
        self.search_entry = tk.Entry(search_frame, width=40, font=("Arial", 10))
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind('<KeyRelease>', self.filter_apps)
        
        list_frame = tk.Frame(root, bg=bg_color)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=("Arial", 11),
                                   bg="#2d2d2d", fg=fg_color, selectbackground=btn_color,
                                   selectforeground=fg_color, height=20)
        self.listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)
        
        self.status_label = tk.Label(root, text="Готов к уничтожению", fg="green", bg=bg_color, font=("Arial", 10))
        self.status_label.pack(pady=5)
        
        btn_frame = tk.Frame(root, bg=bg_color)
        btn_frame.pack(pady=15)
        
        self.delete_btn = tk.Button(btn_frame, text="🔥 УДАЛИТЬ ПОЛНОСТЬЮ 🔥", bg=btn_color, fg=fg_color,
                                    font=("Arial", 14, "bold"), width=35, height=2,
                                    command=self.delete_selected)
        self.delete_btn.pack(pady=5)
        
        refresh_btn = tk.Button(btn_frame, text="🔄 Обновить список", command=self.load_apps,
                                 font=("Arial", 10), width=20, height=1)
        refresh_btn.pack(pady=5)
        
        self.progress = ttk.Progressbar(root, mode='indeterminate', length=600)
        self.progress.pack(pady=10)
        
        self.apps = []
        self.filtered_apps = []
        self.load_apps()
    
    def get_installed_apps(self):
        apps = {}
        reg_paths = [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
        ]
        
        for reg_path in reg_paths:
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path, 0, winreg.KEY_READ)
                for i in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        subkey = winreg.OpenKey(key, subkey_name, 0, winreg.KEY_READ)
                        try:
                            name, _ = winreg.QueryValueEx(subkey, "DisplayName")
                            if name and name.strip():
                                if name not in apps:
                                    apps[name] = subkey_name
                        except:
                            pass
                        winreg.CloseKey(subkey)
                    except:
                        pass
                winreg.CloseKey(key)
            except:
                pass
        
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", 0, winreg.KEY_READ)
            for i in range(winreg.QueryInfoKey(key)[0]):
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    subkey = winreg.OpenKey(key, subkey_name, 0, winreg.KEY_READ)
                    try:
                        name, _ = winreg.QueryValueEx(subkey, "DisplayName")
                        if name and name.strip():
                            if name not in apps:
                                apps[name] = subkey_name
                    except:
                        pass
                    winreg.CloseKey(subkey)
                except:
                    pass
            winreg.CloseKey(key)
        except:
            pass
        
        return sorted(list(apps.keys()))
    
    def load_apps(self):
        self.delete_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Загрузка списка приложений...", fg="orange")
        self.root.update()
        
        def load():
            self.apps = self.get_installed_apps()
            self.filtered_apps = self.apps.copy()
            self.root.after(0, self.update_list)
        
        threading.Thread(target=load, daemon=True).start()
    
    def update_list(self):
        self.listbox.delete(0, tk.END)
        for app in self.filtered_apps:
            self.listbox.insert(tk.END, app)
        self.status_label.config(text=f"Найдено приложений: {len(self.filtered_apps)} | Выбери цель", fg="green")
        self.delete_btn.config(state=tk.NORMAL)
    
    def filter_apps(self, event=None):
        search = self.search_entry.get().lower()
        if search:
            self.filtered_apps = [app for app in self.apps if search in app.lower()]
        else:
            self.filtered_apps = self.apps.copy()
        self.update_list()
    
    def find_and_kill_processes(self, app_name):
        try:
            output = subprocess.run(f'tasklist /FI "IMAGENAME eq {app_name}*" /FO CSV /NH', 
                                   shell=True, capture_output=True, text=True)
            for line in output.stdout.split('\n'):
                if line.strip():
                    proc_name = line.split(',')[0].strip('"')
                    if proc_name and proc_name != "INFO":
                        try:
                            subprocess.run(f'taskkill /F /IM "{proc_name}"', shell=True, capture_output=True)
                        except:
                            pass
        except:
            pass
    
    def remove_registry(self, app_name):
        reg_paths = [
            f"SOFTWARE\\{app_name}",
            f"SOFTWARE\\Wow6432Node\\{app_name}",
            f"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{app_name}",
        ]
        
        for reg_path in reg_paths:
            try:
                winreg.DeleteKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
            except:
                pass
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, reg_path)
            except:
                pass
    
    def delete_app_completely(self, app_name):
        results = {"folders": 0, "files": 0, "reg": 0, "errors": 0}
        
        self.find_and_kill_processes(app_name)
        time.sleep(1)
        
        search_paths = [
            "C:\\Program Files",
            "C:\\Program Files (x86)",
            os.path.expanduser("~\\AppData\\Local"),
            os.path.expanduser("~\\AppData\\Roaming"),
            os.path.expanduser("~\\AppData\\LocalLow"),
            "C:\\ProgramData",
            os.environ.get('TEMP', 'C:\\Windows\\Temp'),
            "C:\\Windows\\Temp",
        ]
        
        for search_path in search_paths:
            if not os.path.exists(search_path):
                continue
            
            try:
                for item in os.listdir(search_path):
                    full_path = os.path.join(search_path, item)
                    if app_name.lower() in item.lower():
                        if force_delete(full_path):
                            if os.path.isfile(full_path):
                                results["files"] += 1
                            else:
                                results["folders"] += 1
            except:
                results["errors"] += 1
        
        self.remove_registry(app_name)
        results["reg"] = 1
        
        return results
    
    def delete_selected(self):
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("Ошибка", "Выбери приложение для удаления!")
            return
        
        app_name = self.listbox.get(selection[0])
        
        result = messagebox.askyesno(
            "ПОДТВЕРЖДЕНИЕ", 
            f"Вы уверены что хотите удалить:\n\n{app_name}\n\n"
            f"ВСЕ файлы и папки связанные с этим приложением будут УНИЧТОЖЕНЫ!",
            icon='warning'
        )
        
        if not result:
            return
        
        self.delete_btn.config(state=tk.DISABLED)
        self.search_entry.config(state=tk.DISABLED)
        self.progress.start()
        self.status_label.config(text=f"Уничтожение {app_name}...", fg="red")
        self.root.update()
        
        def delete_thread():
            try:
                results = self.delete_app_completely(app_name)
                self.root.after(0, self.delete_complete, app_name, results)
            except Exception as e:
                self.root.after(0, self.delete_error, str(e))
        
        threading.Thread(target=delete_thread, daemon=True).start()
    
    def delete_complete(self, app_name, results):
        self.progress.stop()
        self.search_entry.config(state=tk.NORMAL)
        
        messagebox.showinfo(
            "ГОТОВО", 
            f"✅ Приложение уничтожено!\n\n"
            f"Удалено папок: {results['folders']}\n"
            f"Удалено файлов: {results['files']}\n"
            f"Очищено реестра: {results['reg']}\n\n"
            f"Приложение полностью удалено."
        )
        
        self.load_apps()
    
    def delete_error(self, error):
        self.progress.stop()
        self.search_entry.config(state=tk.NORMAL)
        self.delete_btn.config(state=tk.NORMAL)
        messagebox.showerror("Ошибка", f"Произошла ошибка:\n{error}")

if __name__ == "__main__":
    if not is_admin():
        messagebox.showwarning("ВНИМАНИЕ", "Запусти программу от имени АДМИНИСТРАТОРА!\n\nЗакрой программу и запусти снова через 'Запуск от имени администратора'")
        sys.exit()
    
    root = tk.Tk()
    app = AppRemover(root)
    root.mainloop()