import os
import sys
import shutil
import ctypes
import subprocess
import threading
import winreg
import hashlib
import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog, ttk
import uuid
import platform
import json
import re
from datetime import datetime
import tempfile

# --- ПРОВЕРКА ПРАВ АДМИНИСТРАТОРА ---
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

# --- СИСТЕМА HWID ---
class HWIDSystem:
    def __init__(self):
        self.app_data = os.path.join(os.environ['APPDATA'], 'SystemCleaner')
        if not os.path.exists(self.app_data):
            os.makedirs(self.app_data)
        
        self.hwid_file = os.path.join(self.app_data, "system.dat")
        
    def get_hwid(self):
        """Генерация уникального HWID на основе железа"""
        machine_id = str(uuid.getnode())
        processor = platform.processor()
        system = platform.system()
        
        try:
            motherboard = subprocess.check_output(
                'wmic baseboard get serialnumber', 
                shell=True
            ).decode().split('\n')[1].strip()
        except:
            motherboard = "UNKNOWN"
        
        try:
            disk_serial = subprocess.check_output(
                'wmic diskdrive get serialnumber',
                shell=True
            ).decode().split('\n')[1].strip()
        except:
            disk_serial = "UNKNOWN"
        
        hwid_string = f"{machine_id}|{processor}|{motherboard}|{disk_serial}|{system}"
        hwid_hash = hashlib.sha256(hwid_string.encode()).hexdigest()
        
        return hwid_hash
    
    def save_hwid(self, hwid):
        try:
            with open(self.hwid_file, 'w', encoding='utf-8') as f:
                encrypted = ''.join(chr(ord(c) ^ 0x55) for c in hwid)
                f.write(encrypted)
            
            try:
                ctypes.windll.kernel32.SetFileAttributesW(self.hwid_file, 2)
            except:
                pass
            
            return True
        except Exception as e:
            print(f"Ошибка сохранения HWID: {e}")
            return False
    
    def load_hwid(self):
        try:
            if not os.path.exists(self.hwid_file):
                return None
            
            with open(self.hwid_file, 'r', encoding='utf-8') as f:
                encrypted = f.read()
                decrypted = ''.join(chr(ord(c) ^ 0x55) for c in encrypted)
                return decrypted
        except:
            return None
    
    def reset_hwid(self):
        try:
            if os.path.exists(self.hwid_file):
                os.remove(self.hwid_file)
            return True
        except:
            return False
    
    def verify(self):
        current_hwid = self.get_hwid()
        saved_hwid = self.load_hwid()
        
        if saved_hwid is None:
            self.save_hwid(current_hwid)
            return True, "ПЕРВЫЙ ЗАПУСК: HWID ЗАРЕГИСТРИРОВАН"
        
        if current_hwid == saved_hwid:
            return True, "HWID ПОДТВЕРЖДЕН"
        else:
            return False, "ОШИБКА: ЖЕЛЕЗО НЕ СОВПАДАЕТ!"

# --- СИСТЕМА АУТЕНТИФИКАЦИИ ---
class AuthSystem:
    def __init__(self):
        self.app_data = os.path.join(os.environ['APPDATA'], 'SystemCleaner')
        if not os.path.exists(self.app_data):
            os.makedirs(self.app_data)
        
        self.users_file = os.path.join(self.app_data, "users.db")
        self.session_file = os.path.join(self.app_data, "session.dat")
        
        self.admin_email = "admin@cleaner.sys"
        self.admin_password = "admin123"
        
        self.init_admin()
        
    def init_admin(self):
        users = self.load_users()
        if self.admin_email not in users:
            users[self.admin_email] = {
                'password_hash': self.hash_password(self.admin_password),
                'username': 'Administrator',
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'last_login': None,
                'is_admin': True,
                'is_blocked': False,
                'hwid': None
            }
            self.save_users(users)
    
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def validate_email(self, email):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def load_users(self):
        try:
            if not os.path.exists(self.users_file):
                return {}
            
            if not os.access(self.users_file, os.R_OK):
                print(f"Нет прав на чтение файла: {self.users_file}")
                return {}
            
            with open(self.users_file, 'r', encoding='utf-8') as f:
                encrypted_data = f.read()
                
                if not encrypted_data:
                    return {}
                
                decrypted = ''.join(chr(ord(c) ^ 0xAA) for c in encrypted_data)
                return json.loads(decrypted)
        except json.JSONDecodeError as e:
            print(f"Ошибка JSON: {e}")
            return {}
        except Exception as e:
            print(f"Ошибка загрузки пользователей: {e}")
            return {}
    
    def save_users(self, users_data):
        try:
            json_data = json.dumps(users_data, indent=2, ensure_ascii=False)
            encrypted = ''.join(chr(ord(c) ^ 0xAA) for c in json_data)
            
            temp_file = os.path.join(self.app_data, f"users_temp_{os.getpid()}.db")
            
            try:
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(encrypted)
                
                if os.path.exists(self.users_file):
                    try:
                        os.chmod(self.users_file, 0o777)
                    except:
                        pass
                    
                    try:
                        os.remove(self.users_file)
                    except PermissionError:
                        backup = os.path.join(
                            self.app_data,
                            f"users_old_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                        )
                        os.rename(self.users_file, backup)
                
                os.rename(temp_file, self.users_file)
                
                try:
                    ctypes.windll.kernel32.SetFileAttributesW(self.users_file, 2)
                except:
                    pass
                
                return True
                
            except Exception as e:
                print(f"Ошибка записи файла: {e}")
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except:
                        pass
                return False
                
        except Exception as e:
            print(f"Ошибка сохранения: {e}")
            return False
    
    def register_user(self, email, password, username):
        try:
            users = self.load_users()
            
            if email in users:
                return False, "Email уже зарегистрирован!"
            
            users[email] = {
                'password_hash': self.hash_password(password),
                'username': username,
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'last_login': None,
                'is_admin': False,
                'is_blocked': False,
                'hwid': None
            }
            
            if self.save_users(users):
                return True, "Регистрация успешна!"
            else:
                return False, "Ошибка сохранения данных!"
        except Exception as e:
            print(f"Ошибка регистрации: {e}")
            return False, f"Ошибка: {str(e)}"
    
    def login_user(self, email, password, current_hwid=None):
        try:
            users = self.load_users()
            
            if email not in users:
                return False, "Email не найден!"
            
            user = users[email]
            
            if user.get('is_blocked', False):
                return False, "Аккаунт заблокирован администратором!"
            
            if user['password_hash'] != self.hash_password(password):
                return False, "Неверный пароль!"
            
            if current_hwid and not user.get('is_admin', False):
                if user['hwid'] is None:
                    users[email]['hwid'] = current_hwid
                elif user['hwid'] != current_hwid:
                    return False, "HWID не совпадает! Обратитесь к администратору."
            
            users[email]['last_login'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.save_users(users)
            
            self.save_session(email, user['username'], user.get('is_admin', False))
            
            return True, user['username']
        except Exception as e:
            print(f"Ошибка входа: {e}")
            return False, f"Ошибка: {str(e)}"
    
    def save_session(self, email, username, is_admin=False):
        try:
            session_data = json.dumps({
                'email': email,
                'username': username,
                'is_admin': is_admin,
                'login_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            encrypted = ''.join(chr(ord(c) ^ 0x55) for c in session_data)
            
            with open(self.session_file, 'w', encoding='utf-8') as f:
                f.write(encrypted)
            
            try:
                ctypes.windll.kernel32.SetFileAttributesW(self.session_file, 2)
            except:
                pass
            
            return True
        except Exception as e:
            print(f"Ошибка сохранения сессии: {e}")
            return False
    
    def load_session(self):
        try:
            if not os.path.exists(self.session_file):
                return None
            
            with open(self.session_file, 'r', encoding='utf-8') as f:
                encrypted = f.read()
                decrypted = ''.join(chr(ord(c) ^ 0x55) for c in encrypted)
                return json.loads(decrypted)
        except:
            return None
    
    def logout(self):
        try:
            if os.path.exists(self.session_file):
                try:
                    os.chmod(self.session_file, 0o777)
                except:
                    pass
                os.remove(self.session_file)
            return True
        except:
            return False
    
    def get_user_info(self, email):
        users = self.load_users()
        return users.get(email, None)
    
    def is_admin(self, email):
        user = self.get_user_info(email)
        return user.get('is_admin', False) if user else False
    
    def block_user(self, admin_email, target_email):
        if not self.is_admin(admin_email):
            return False, "Недостаточно прав!"
        
        users = self.load_users()
        
        if target_email not in users:
            return False, "Пользователь не найден!"
        
        if users[target_email].get('is_admin', False):
            return False, "Нельзя заблокировать администратора!"
        
        users[target_email]['is_blocked'] = True
        
        if self.save_users(users):
            return True, f"Пользователь {target_email} заблокирован"
        return False, "Ошибка сохранения"
    
    def unblock_user(self, admin_email, target_email):
        if not self.is_admin(admin_email):
            return False, "Недостаточно прав!"
        
        users = self.load_users()
        
        if target_email not in users:
            return False, "Пользователь не найден!"
        
        users[target_email]['is_blocked'] = False
        
        if self.save_users(users):
            return True, f"Пользователь {target_email} разблокирован"
        return False, "Ошибка сохранения"
    
    def reset_password(self, admin_email, target_email, new_password):
        if not self.is_admin(admin_email):
            return False, "Недостаточно прав!"
        
        users = self.load_users()
        
        if target_email not in users:
            return False, "Пользователь не найден!"
        
        users[target_email]['password_hash'] = self.hash_password(new_password)
        
        if self.save_users(users):
            return True, f"Пароль для {target_email} сброшен"
        return False, "Ошибка сохранения"
    
    def reset_user_hwid(self, admin_email, target_email):
        if not self.is_admin(admin_email):
            return False, "Недостаточно прав!"
        
        users = self.load_users()
        
        if target_email not in users:
            return False, "Пользователь не найден!"
        
        users[target_email]['hwid'] = None
        
        if self.save_users(users):
            return True, f"HWID для {target_email} сброшен"
        return False, "Ошибка сохранения"
    
    def delete_user(self, admin_email, target_email):
        if not self.is_admin(admin_email):
            return False, "Недостаточно прав!"
        
        users = self.load_users()
        
        if target_email not in users:
            return False, "Пользователь не найден!"
        
        if users[target_email].get('is_admin', False):
            return False, "Нельзя удалить администратора!"
        
        del users[target_email]
        
        if self.save_users(users):
            return True, f"Пользователь {target_email} удалён"
        return False, "Ошибка сохранения"
    
    def get_all_users(self):
        return self.load_users()
    
    def make_admin(self, admin_email, target_email):
        if not self.is_admin(admin_email):
            return False, "Недостаточно прав!"
        
        users = self.load_users()
        
        if target_email not in users:
            return False, "Пользователь не найден!"
        
        users[target_email]['is_admin'] = True
        users[target_email]['hwid'] = None
        
        if self.save_users(users):
            return True, f"{target_email} назначен администратором"
        return False, "Ошибка сохранения"

# --- АДМИН ПАНЕЛЬ ---
class AdminPanel:
    def __init__(self, parent, auth_system, admin_email):
        self.auth_system = auth_system
        self.admin_email = admin_email
        
        self.window = tk.Toplevel(parent)
        self.window.title("Админ-панель")
        self.window.geometry("900x600")
        self.window.configure(bg="#0a0a0a")
        self.window.resizable(True, True)
        
        self.center_window()
        
        header = tk.Frame(self.window, bg="#1a1a1a", height=60)
        header.pack(fill=tk.X)
        
        tk.Label(
            header,
            text="⚙️ ПАНЕЛЬ АДМИНИСТРАТОРА",
            bg="#1a1a1a",
            fg="#ff1744",
            font=("Arial", 16, "bold")
        ).pack(pady=15)
        
        main_frame = tk.Frame(self.window, bg="#0a0a0a")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        left_panel = tk.Frame(main_frame, bg="#1a1a1a")
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        tk.Label(
            left_panel,
            text="ПОЛЬЗОВАТЕЛИ",
            bg="#1a1a1a",
            fg="white",
            font=("Arial", 12, "bold")
        ).pack(pady=10)
        
        columns = ('Email', 'Имя', 'Статус', 'Роль', 'HWID')
        self.tree = ttk.Treeview(left_panel, columns=columns, show='headings', height=15)
        
        self.tree.heading('Email', text='Email')
        self.tree.heading('Имя', text='Имя')
        self.tree.heading('Статус', text='Статус')
        self.tree.heading('Роль', text='Роль')
        self.tree.heading('HWID', text='HWID')
        
        self.tree.column('Email', width=200)
        self.tree.column('Имя', width=120)
        self.tree.column('Статус', width=100)
        self.tree.column('Роль', width=80)
        self.tree.column('HWID', width=100)
        
        scrollbar = ttk.Scrollbar(left_panel, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        right_panel = tk.Frame(main_frame, bg="#1a1a1a", width=250)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y)
        right_panel.pack_propagate(False)
        
        tk.Label(
            right_panel,
            text="ДЕЙСТВИЯ",
            bg="#1a1a1a",
            fg="white",
            font=("Arial", 12, "bold")
        ).pack(pady=15)
        
        btn_style = {
            'width': 20,
            'height': 2,
            'font': ('Arial', 10),
            'cursor': 'hand2',
            'relief': tk.FLAT
        }
        
        tk.Button(
            right_panel,
            text="🔄 Обновить список",
            command=self.refresh_users,
            bg="#00ff41",
            fg="black",
            **btn_style
        ).pack(pady=5, padx=10)
        
        tk.Button(
            right_panel,
            text="🔒 Заблокировать",
            command=self.block_selected,
            bg="#ff9800",
            fg="white",
            **btn_style
        ).pack(pady=5, padx=10)
        
        tk.Button(
            right_panel,
            text="🔓 Разблокировать",
            command=self.unblock_selected,
            bg="#4caf50",
            fg="white",
            **btn_style
        ).pack(pady=5, padx=10)
        
        tk.Button(
            right_panel,
            text="🔑 Сбросить пароль",
            command=self.reset_password_selected,
            bg="#2196f3",
            fg="white",
            **btn_style
        ).pack(pady=5, padx=10)
        
        tk.Button(
            right_panel,
            text="💻 Сбросить HWID",
            command=self.reset_hwid_selected,
            bg="#9c27b0",
            fg="white",
            **btn_style
        ).pack(pady=5, padx=10)
        
        tk.Button(
            right_panel,
            text="⭐ Сделать админом",
            command=self.make_admin_selected,
            bg="#ffc107",
            fg="black",
            **btn_style
        ).pack(pady=5, padx=10)
        
        tk.Button(
            right_panel,
            text="🗑️ Удалить",
            command=self.delete_selected,
            bg="#f44336",
            fg="white",
            **btn_style
        ).pack(pady=5, padx=10)
        
        info_frame = tk.Frame(right_panel, bg="#0a0a0a")
        info_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10, padx=10)
        
        self.info_label = tk.Label(
            info_frame,
            text="Выберите пользователя",
            bg="#0a0a0a",
            fg="#888",
            font=("Arial", 8),
            wraplength=220,
            justify=tk.LEFT
        )
        self.info_label.pack()
        
        self.refresh_users()
        self.tree.bind('<<TreeviewSelect>>', self.on_select)
    
    def center_window(self):
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
    
    def refresh_users(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        users = self.auth_system.get_all_users()
        
        for email, data in users.items():
            status = "🔒 Заблокирован" if data.get('is_blocked', False) else "✅ Активен"
            role = "👑 Админ" if data.get('is_admin', False) else "👤 Юзер"
            hwid_status = "✅" if data.get('hwid') else "❌"
            
            self.tree.insert('', tk.END, values=(
                email,
                data['username'],
                status,
                role,
                hwid_status
            ))
        
        total = len(users)
        blocked = sum(1 for u in users.values() if u.get('is_blocked', False))
        admins = sum(1 for u in users.values() if u.get('is_admin', False))
        
        self.info_label.config(
            text=f"Всего: {total}\nАктивных: {total - blocked}\nЗаблокированных: {blocked}\nАдминов: {admins}"
        )
    
    def get_selected_email(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите пользователя!")
            return None
        
        item = self.tree.item(selected[0])
        return item['values'][0]
    
    def on_select(self, event):
        email = self.get_selected_email()
        if email:
            user = self.auth_system.get_user_info(email)
            if user:
                hwid_text = user.get('hwid', 'Не установлен')[:16] + '...' if user.get('hwid') else 'Не установлен'
                info = f"📧 {email}\n👤 {user['username']}\n📅 Создан: {user['created_at']}\n🕒 Вход: {user.get('last_login', 'Никогда')}\n💻 HWID: {hwid_text}"
                self.info_label.config(text=info)
    
    def block_selected(self):
        email = self.get_selected_email()
        if not email:
            return
        
        success, msg = self.auth_system.block_user(self.admin_email, email)
        
        if success:
            messagebox.showinfo("Успех", msg)
            self.refresh_users()
        else:
            messagebox.showerror("Ошибка", msg)
    
    def unblock_selected(self):
        email = self.get_selected_email()
        if not email:
            return
        
        success, msg = self.auth_system.unblock_user(self.admin_email, email)
        
        if success:
            messagebox.showinfo("Успех", msg)
            self.refresh_users()
        else:
            messagebox.showerror("Ошибка", msg)
    
    def reset_password_selected(self):
        email = self.get_selected_email()
        if not email:
            return
        
        new_password = simpledialog.askstring(
            "Новый пароль",
            f"Введите новый пароль для {email}:",
            show='●'
        )
        
        if not new_password or len(new_password) < 6:
            messagebox.showerror("Ошибка", "Пароль должен содержать минимум 6 символов!")
            return
        
        success, msg = self.auth_system.reset_password(self.admin_email, email, new_password)
        
        if success:
            messagebox.showinfo("Успех", f"{msg}\n\nНовый пароль: {new_password}")
        else:
            messagebox.showerror("Ошибка", msg)
    
    def reset_hwid_selected(self):
        email = self.get_selected_email()
        if not email:
            return
        
        confirm = messagebox.askyesno(
            "Подтверждение",
            f"Сбросить HWID для {email}?"
        )
        
        if not confirm:
            return
        
        success, msg = self.auth_system.reset_user_hwid(self.admin_email, email)
        
        if success:
            messagebox.showinfo("Успех", msg)
            self.refresh_users()
        else:
            messagebox.showerror("Ошибка", msg)
    
    def make_admin_selected(self):
        email = self.get_selected_email()
        if not email:
            return
        
        confirm = messagebox.askyesno(
            "Подтверждение",
            f"Назначить {email} администратором?"
        )
        
        if not confirm:
            return
        
        success, msg = self.auth_system.make_admin(self.admin_email, email)
        
        if success:
            messagebox.showinfo("Успех", msg)
            self.refresh_users()
        else:
            messagebox.showerror("Ошибка", msg)
    
    def delete_selected(self):
        email = self.get_selected_email()
        if not email:
            return
        
        confirm = messagebox.askyesno(
            "Подтверждение",
            f"УДАЛИТЬ пользователя {email}?\n\nЭто действие необратимо!"
        )
        
        if not confirm:
            return
        
        success, msg = self.auth_system.delete_user(self.admin_email, email)
        
        if success:
            messagebox.showinfo("Успех", msg)
            self.refresh_users()
        else:
            messagebox.showerror("Ошибка", msg)

# --- ОКНО АВТОРИЗАЦИИ ---
class AuthWindow:
    def __init__(self, auth_system, hwid_system):
        self.auth_system = auth_system
        self.hwid_system = hwid_system
        self.authenticated = False
        self.username = None
        self.email = None
        self.is_admin = False
        self.attempts = 0
        self.max_attempts = 5
        
        self.root = tk.Tk()
        self.root.title("Система аутентификации")
        self.root.geometry("500x650")
        self.root.configure(bg="#0a0a0a")
        self.root.resizable(False, False)
        
        self.center_window()
        
        session = self.auth_system.load_session()
        if session:
            self.show_session_choice(session)
        else:
            self.show_login_screen()
    
    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def show_session_choice(self, session):
        self.clear_screen()
        
        tk.Label(
            self.root,
            text="👤 АКТИВНАЯ СЕССИЯ",
            bg="#0a0a0a",
            fg="#00ff41",
            font=("Arial", 18, "bold")
        ).pack(pady=30)
        
        info_frame = tk.Frame(self.root, bg="#1a1a1a")
        info_frame.pack(pady=20, padx=40, fill=tk.X)
        
        tk.Label(
            info_frame,
            text=f"Пользователь: {session['username']}",
            bg="#1a1a1a",
            fg="white",
            font=("Arial", 12)
        ).pack(pady=5)
        
        tk.Label(
            info_frame,
            text=f"Email: {session['email']}",
            bg="#1a1a1a",
            fg="#888",
            font=("Arial", 10)
        ).pack(pady=5)
        
        role_text = "👑 Администратор" if session.get('is_admin', False) else "👤 Пользователь"
        tk.Label(
            info_frame,
            text=f"Роль: {role_text}",
            bg="#1a1a1a",
            fg="#00ff41" if session.get('is_admin', False) else "#888",
            font=("Arial", 10)
        ).pack(pady=5)
        
        tk.Button(
            self.root,
            text="ПРОДОЛЖИТЬ",
            command=lambda: self.continue_session(session),
            bg="#00ff41",
            fg="black",
            font=("Arial", 12, "bold"),
            width=20,
            height=2,
            cursor="hand2"
        ).pack(pady=15)
        
        tk.Button(
            self.root,
            text="ВЫЙТИ И СМЕНИТЬ АККАУНТ",
            command=self.logout_and_login,
            bg="#ff1744",
            fg="white",
            font=("Arial", 11),
            width=25,
            height=2,
            cursor="hand2"
        ).pack(pady=5)
    
    def continue_session(self, session):
        self.authenticated = True
        self.username = session['username']
        self.email = session['email']
        self.is_admin = session.get('is_admin', False)
        self.root.destroy()
    
    def logout_and_login(self):
        self.auth_system.logout()
        self.show_login_screen()
    
    def show_login_screen(self):
        self.clear_screen()
        
        tk.Label(
            self.root,
            text="🔐 ВХОД В СИСТЕМУ",
            bg="#0a0a0a",
            fg="#ff1744",
            font=("Arial", 20, "bold")
        ).pack(pady=30)
        
        tk.Label(
            self.root,
            text="Админ: admin@cleaner.sys / admin123",
            bg="#0a0a0a",
            fg="#666",
            font=("Arial", 8)
        ).pack(pady=5)
        
        tk.Label(
            self.root,
            text="Email:",
            bg="#0a0a0a",
            fg="white",
            font=("Arial", 11)
        ).pack(pady=(20, 5))
        
        self.email_entry = tk.Entry(
            self.root,
            width=35,
            font=("Arial", 12),
            bg="#1a1a1a",
            fg="white",
            insertbackground="white"
        )
        self.email_entry.pack(pady=5)
        self.email_entry.focus()
        
        tk.Label(
            self.root,
            text="Пароль:",
            bg="#0a0a0a",
            fg="white",
            font=("Arial", 11)
        ).pack(pady=(15, 5))
        
        self.password_entry = tk.Entry(
            self.root,
            show="●",
            width=35,
            font=("Arial", 12),
            bg="#1a1a1a",
            fg="white",
            insertbackground="white"
        )
        self.password_entry.pack(pady=5)
        
        tk.Button(
            self.root,
            text="ВОЙТИ",
            command=self.login,
            bg="#ff1744",
            fg="white",
            font=("Arial", 13, "bold"),
            width=25,
            height=2,
            cursor="hand2"
        ).pack(pady=15)
        
        tk.Label(
            self.root,
            text="Нет аккаунта?",
            bg="#0a0a0a",
            fg="#666",
            font=("Arial", 9)
        ).pack(pady=(20, 5))
        
        tk.Button(
            self.root,
            text="ЗАРЕГИСТРИРОВАТЬСЯ",
            command=self.show_register_screen,
            bg="#333",
            fg="white",
            font=("Arial", 10),
            width=25,
            cursor="hand2",
            relief=tk.FLAT
        ).pack()
        
        self.password_entry.bind("<Return>", lambda e: self.login())
    
    def login(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        
        if not email or not password:
            messagebox.showwarning("Ошибка", "Заполните все поля!")
            return
        
        if not self.auth_system.validate_email(email):
            messagebox.showerror("Ошибка", "Неверный формат email!")
            return
        
        current_hwid = self.hwid_system.get_hwid()
        success, message = self.auth_system.login_user(email, password, current_hwid)
        
        if success:
            user_info = self.auth_system.get_user_info(email)
            self.authenticated = True
            self.username = message
            self.email = email
            self.is_admin = user_info.get('is_admin', False)
            
            role = "Администратор" if self.is_admin else "Пользователь"
            messagebox.showinfo("Успех", f"Добро пожаловать, {message}!\n\nРоль: {role}")
            self.root.destroy()
        else:
            self.attempts += 1
            remaining = self.max_attempts - self.attempts
            
            if remaining > 0:
                messagebox.showerror(
                    "Ошибка входа",
                    f"{message}\n\nОсталось попыток: {remaining}"
                )
                self.password_entry.delete(0, tk.END)
            else:
                messagebox.showerror(
                    "Доступ заблокирован",
                    "Превышено количество попыток!"
                )
                sys.exit()
    
    def show_register_screen(self):
        self.clear_screen()
        
        tk.Label(
            self.root,
            text="📝 РЕГИСТРАЦИЯ",
            bg="#0a0a0a",
            fg="#00ff41",
            font=("Arial", 20, "bold")
        ).pack(pady=30)
        
        tk.Label(
            self.root,
            text="Имя пользователя:",
            bg="#0a0a0a",
            fg="white",
            font=("Arial", 11)
        ).pack(pady=(10, 5))
        
        self.username_entry = tk.Entry(
            self.root,
            width=35,
            font=("Arial", 12),
            bg="#1a1a1a",
            fg="white",
            insertbackground="white"
        )
        self.username_entry.pack(pady=5)
        self.username_entry.focus()
        
        tk.Label(
            self.root,
            text="Email:",
            bg="#0a0a0a",
            fg="white",
            font=("Arial", 11)
        ).pack(pady=(15, 5))
        
        self.reg_email_entry = tk.Entry(
            self.root,
            width=35,
            font=("Arial", 12),
            bg="#1a1a1a",
            fg="white",
            insertbackground="white"
        )
        self.reg_email_entry.pack(pady=5)
        
        tk.Label(
            self.root,
            text="Пароль (минимум 6 символов):",
            bg="#0a0a0a",
            fg="white",
            font=("Arial", 11)
        ).pack(pady=(15, 5))
        
        self.reg_password_entry = tk.Entry(
            self.root,
            show="●",
            width=35,
            font=("Arial", 12),
            bg="#1a1a1a",
            fg="white",
            insertbackground="white"
        )
        self.reg_password_entry.pack(pady=5)
        
        tk.Label(
            self.root,
            text="Подтвердите пароль:",
            bg="#0a0a0a",
            fg="white",
            font=("Arial", 11)
        ).pack(pady=(15, 5))
        
        self.reg_confirm_entry = tk.Entry(
            self.root,
            show="●",
            width=35,
            font=("Arial", 12),
            bg="#1a1a1a",
            fg="white",
            insertbackground="white"
        )
        self.reg_confirm_entry.pack(pady=5)
        
        tk.Button(
            self.root,
            text="СОЗДАТЬ АККАУНТ",
            command=self.register,
            bg="#00ff41",
            fg="black",
            font=("Arial", 13, "bold"),
            width=25,
            height=2,
            cursor="hand2"
        ).pack(pady=20)
        
        tk.Label(
            self.root,
            text="Уже есть аккаунт?",
            bg="#0a0a0a",
            fg="#666",
            font=("Arial", 9)
        ).pack(pady=(10, 5))
        
        tk.Button(
            self.root,
            text="ВОЙТИ",
            command=self.show_login_screen,
            bg="#333",
            fg="white",
            font=("Arial", 10),
            width=25,
            cursor="hand2",
            relief=tk.FLAT
        ).pack()
        
        self.reg_confirm_entry.bind("<Return>", lambda e: self.register())
    
    def register(self):
        username = self.username_entry.get().strip()
        email = self.reg_email_entry.get().strip()
        password = self.reg_password_entry.get()
        confirm = self.reg_confirm_entry.get()
        
        if not username or not email or not password:
            messagebox.showwarning("Ошибка", "Заполните все поля!")
            return
        
        if len(username) < 3:
            messagebox.showerror("Ошибка", "Имя должно содержать минимум 3 символа!")
            return
        
        if not self.auth_system.validate_email(email):
            messagebox.showerror("Ошибка", "Неверный формат email!")
            return
        
        if len(password) < 6:
            messagebox.showerror("Ошибка", "Пароль должен содержать минимум 6 символов!")
            return
        
        if password != confirm:
            messagebox.showerror("Ошибка", "Пароли не совпадают!")
            return
        
        success, message = self.auth_system.register_user(email, password, username)
        
        if success:
            messagebox.showinfo(
                "Успех",
                f"Регистрация завершена!\n\nТеперь вы можете войти в систему."
            )
            self.show_login_screen()
        else:
            messagebox.showerror("Ошибка регистрации", message)
    
    def show(self):
        self.root.mainloop()
        return self.authenticated, self.username, self.email, self.is_admin

# --- ОСНОВНОЙ КЛАСС ---
class SystemCleaner:
    def __init__(self, root, username, email, is_admin):
        self.root = root
        self.username = username
        self.email = email
        self.is_admin = is_admin
        self.root.title(f"System Cleaner v3.0 - {username}")
        self.root.geometry("1000x700")
        self.root.configure(bg="#0a0a0a")
        
        self.auth_system = AuthSystem()
        
        top_panel = tk.Frame(root, bg="#1a1a1a", height=40)
        top_panel.pack(fill=tk.X)
        
        if self.is_admin:
            tk.Button(
                top_panel,
                text="⚙️ Админ-панель",
                command=self.open_admin_panel,
                bg="#ff9800",
                fg="white",
                font=("Arial", 9, "bold"),
                relief=tk.FLAT,
                cursor="hand2"
            ).pack(side=tk.LEFT, padx=10, pady=5)
        
        tk.Button(
            top_panel,
            text="🚪 Выйти",
            command=self.logout,
            bg="#ff1744",
            fg="white",
            font=("Arial", 9),
            relief=tk.FLAT,
            cursor="hand2"
        ).pack(side=tk.RIGHT, padx=10, pady=5)
        
        role_text = "👑 ADMIN" if is_admin else "👤 USER"
        role_color = "#ff9800" if is_admin else "#00ff41"
        
        tk.Label(
            top_panel,
            text=f"{role_text} | {username}",
            bg="#1a1a1a",
            fg=role_color,
            font=("Arial", 10, "bold")
        ).pack(side=tk.LEFT, padx=15)
        
        tk.Label(
            root,
            text="SYSTEM ARTIFACT CLEANER",
            bg="#0a0a0a",
            fg="white",
            font=("Arial", 20, "bold")
        ).pack(pady=30)
        
        tk.Label(
            root,
            text="Введите название программы:",
            bg="#0a0a0a",
            fg="#ccc",
            font=("Arial", 12)
        ).pack(pady=10)
        
        self.entry = tk.Entry(
            root,
            width=50,
            font=("Arial", 14),
            bg="#1a1a1a",
            fg="white",
            insertbackground="white"
        )
        self.entry.pack(pady=10, ipady=5)
        self.entry.focus()
        
        tk.Button(
            root,
            text="🔥 НАЧАТЬ ОЧИСТКУ 🔥",
            command=self.start_cleaning,
            bg="#ff1744",
            fg="white",
            font=("Arial", 14, "bold"),
            height=2,
            width=30,
            cursor="hand2"
        ).pack(pady=20)
        
        self.log_area = scrolledtext.ScrolledText(
            root,
            width=100,
            height=20,
            bg="#0d0d0d",
            fg="#00ff41",
            font=("Consolas", 10)
        )
        self.log_area.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        self.log(f"Добро пожаловать, {username}!")
        self.log(f"Email: {email}")
        self.log(f"Роль: {'Администратор' if is_admin else 'Пользователь'}")
        self.log("-" * 80)
    
    def open_admin_panel(self):
        AdminPanel(self.root, self.auth_system, self.email)
    
    def logout(self):
        if messagebox.askyesno("Выход", "Вы уверены?"):
            self.auth_system.logout()
            self.root.destroy()
            sys.exit()
    
    def log(self, text):
        self.log_area.insert(tk.END, text + "\n")
        self.log_area.see(tk.END)
    
    def start_cleaning(self):
        name = self.entry.get().strip()
        if len(name) < 2:
            messagebox.showwarning("Ошибка", "Введите название программы!")
            return
        
        self.log(f"\n[!] Запуск очистки для: {name}")
        self.log("[!] Функционал очистки активирован")

# --- ТОЧКА ВХОДА ---
if __name__ == "__main__":
    try:
        app_data = os.path.join(os.environ['APPDATA'], 'SystemCleaner')
        if not os.path.exists(app_data):
            os.makedirs(app_data)
        
        auth_system = AuthSystem()
        hwid_system = HWIDSystem()
        
        auth_window = AuthWindow(auth_system, hwid_system)
        authenticated, username, email, is_admin = auth_window.show()
        
        if authenticated:
            root = tk.Tk()
            app = SystemCleaner(root, username, email, is_admin)
            root.mainloop()
        else:
            sys.exit()
    except Exception as e:
        messagebox.showerror("Критическая ошибка", str(e))
        import traceback
        traceback.print_exc()
        sys.exit(1)