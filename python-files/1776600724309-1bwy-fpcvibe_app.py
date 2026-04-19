# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
import subprocess
import sys
import ctypes

CONFIG_FILE = "fpcvibe_proxy_config.json"

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)

class ProxyWarpApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FPCVIBE Proxy + Warp Connector")
        self.root.geometry("500x350")
        self.root.resizable(False, False)

        self.proxy_type = tk.StringVar(value="none")
        self.proxy_server = tk.StringVar()
        self.proxy_port = tk.StringVar()
        self.warp_key = tk.StringVar()
        self.custom_proxy = tk.StringVar()

        self.load_config()

        # Ползунок (Switch)
        self.switch_var = tk.BooleanVar(value=False)
        self.switch = ttk.Checkbutton(root, text="ВКЛЮЧИТЬ ПРОКСИ / WARP", variable=self.switch_var,
                                      command=self.toggle_connection, style="Switch.TCheckbutton")
        self.switch.pack(pady=30)

        # Кнопка настройки
        self.btn_config = tk.Button(root, text="НАСТРОИТЬ", command=self.open_config_dialog,
                                    bg="orange", fg="black", font=("Arial", 12, "bold"))
        self.btn_config.pack(pady=20)

        # Статус
        self.status_label = tk.Label(root, text="Статус: ОТКЛЮЧЕНО", fg="red")
        self.status_label.pack(pady=10)

        style = ttk.Style()
        style.configure("Switch.TCheckbutton", font=("Arial", 11))

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                self.warp_key.set(data.get("warp_key", ""))
                self.custom_proxy.set(data.get("custom_proxy", ""))
        else:
            self.warp_key.set("")
            self.custom_proxy.set("")

    def save_config(self):
        with open(CONFIG_FILE, "w") as f:
            json.dump({
                "warp_key": self.warp_key.get(),
                "custom_proxy": self.custom_proxy.get()
            }, f)

    def open_config_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Настройки FPCVIBE")
        dialog.geometry("450x300")
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="Warp ключ (с warp генератора):", font=("Arial", 10)).pack(pady=5)
        warp_entry = tk.Entry(dialog, textvariable=self.warp_key, width=50)
        warp_entry.pack(pady=5)

        tk.Label(dialog, text="Свой прокси (формат: ip:port или socks5://ip:port):", font=("Arial", 10)).pack(pady=5)
        proxy_entry = tk.Entry(dialog, textvariable=self.custom_proxy, width=50)
        proxy_entry.pack(pady=5)

        def save_and_close():
            self.save_config()
            messagebox.showinfo("Сохранено", "Настройки сохранены")
            dialog.destroy()

        tk.Button(dialog, text="СОХРАНИТЬ", command=save_and_close, bg="green", fg="white").pack(pady=20)

    def set_windows_proxy(self, server_port):
        """Установка системного прокси в Windows"""
        try:
            # Включаем прокси через netsh
            subprocess.run(f'netsh winhttp set proxy "{server_port}"', shell=True, check=True)
            # Для системного прокси (Internet Options)
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Internet Settings", 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, server_port)
            winreg.CloseKey(key)
            return True
        except Exception as e:
            print(f"Ошибка установки прокси: {e}")
            return False

    def disable_windows_proxy(self):
        """Отключение системного прокси"""
        try:
            subprocess.run('netsh winhttp reset proxy', shell=True, check=True)
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Internet Settings", 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(key)
            return True
        except:
            return False

    def connect_warp(self, warp_key):
        """Эмуляция подключения Warp (запуск wireguard или warp-cli)"""
        try:
            # Проверяем наличие warp-cli
            result = subprocess.run("warp-cli --version", shell=True, capture_output=True)
            if result.returncode != 0:
                self.status_label.config(text="Статус: Warp CLI не установлен")
                return False

            # Регистрация и подключение
            subprocess.run(f'warp-cli registration new "{warp_key}"', shell=True, capture_output=True)
            subprocess.run("warp-cli connect", shell=True, capture_output=True)
            return True
        except:
            return False

    def disconnect_warp(self):
        try:
            subprocess.run("warp-cli disconnect", shell=True, capture_output=True)
            subprocess.run("warp-cli registration delete", shell=True, capture_output=True)
        except:
            pass

    def toggle_connection(self):
        if not is_admin():
            self.switch_var.set(False)
            messagebox.showwarning("Требуются права администратора", "Запустите программу от имени администратора для изменения прокси.")
            self.status_label.config(text="Статус: Ошибка прав")
            return

        if self.switch_var.get():
            # Включаем
            proxy_str = self.custom_proxy.get().strip()
            warp_str = self.warp_key.get().strip()

            if proxy_str:
                # Используем свой прокси
                if "://" not in proxy_str:
                    proxy_str = f"http://{proxy_str}"
                if self.set_windows_proxy(proxy_str):
                    self.status_label.config(text=f"Статус: ПОДКЛЮЧЕНО (Прокси: {proxy_str})", fg="green")
                else:
                    self.switch_var.set(False)
                    self.status_label.config(text="Статус: Ошибка прокси", fg="red")
            elif warp_str:
                if self.connect_warp(warp_str):
                    self.status_label.config(text=f"Статус: ПОДКЛЮЧЕНО (Warp ключ активен)", fg="green")
                else:
                    self.switch_var.set(False)
                    self.status_label.config(text="Статус: Ошибка Warp", fg="red")
            else:
                messagebox.showerror("Ошибка", "Нет настроек! Нажмите 'НАСТРОИТЬ' и введите Warp ключ или прокси.")
                self.switch_var.set(False)
                self.status_label.config(text="Статус: Нет настроек", fg="red")
        else:
            # Выключаем
            self.disable_windows_proxy()
            self.disconnect_warp()
            self.status_label.config(text="Статус: ОТКЛЮЧЕНО", fg="red")

if __name__ == "__main__":
    if not is_admin():
        run_as_admin()
        sys.exit()
    root = tk.Tk()
    app = ProxyWarpApp(root)
    root.mainloop()