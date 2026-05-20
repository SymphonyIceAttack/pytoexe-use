import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
from datetime import datetime

# ==========================================
# БЛОК 1: КОНФИГУРАЦИЯ И ДИЗАЙН (UI CONFIG)
# ==========================================
# Используем неяркие, спокойные цвета для снижения нагрузки на глаза
BG_COLOR = "#2E3440"       # Темно-серый фон (стиль Nord)
FG_COLOR = "#D8DEE9"       # Светло-серый текст
ACCENT_COLOR = "#4C566A"   # Цвет кнопок и панелей
FONT_MAIN = ("Helvetica", 11)
FONT_TITLE = ("Helvetica", 14, "bold")

# ==========================================
# БЛОК 2: КРИПТОГРАФИЧЕСКОЕ ЯДРО (МОДЕЛЬ)
# ==========================================
class CryptoProvider:
    """
    Класс инкапсулирует криптографическую логику. 
    В демо-версии имитирует работу алгоритмов. В будущем здесь 
    будут вызовы функций из библиотеки pyGOST (ГОСТ Р 34.10-2012).
    """
    def __init__(self):
        self.keys_dir = "keys_storage"
        if not os.path.exists(self.keys_dir):
            os.makedirs(self.keys_dir)

    def generate_keypair(self, user_name):
        """Имитация генерации пары ключей (открытый и закрытый)"""
        # TODO: Заменить на генерацию кривой ГОСТ 34.10
        public_key_mock = f"-----BEGIN GOST PUBLIC KEY-----\n{user_name}_pub_mock_data\n-----END GOST PUBLIC KEY-----"
        private_key_mock = f"-----BEGIN GOST PRIVATE KEY-----\n{user_name}_priv_mock_data\n-----END GOST PRIVATE KEY-----"
        
        pub_path = os.path.join(self.keys_dir, f"{user_name}_public.pem")
        with open(pub_path, "w") as f:
            f.write(public_key_mock)
            
        return pub_path

    def encrypt_data(self, data_type, public_key_path, payload):
        """Имитация процесса шифрования открытым ключом адресата"""
        # TODO: Заменить на реальное шифрование (VKO GOST / KDF / MAC)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        encrypted_mock = f"[ENCRYPTED: {data_type}] | Key: {os.path.basename(public_key_path)} | Data: {payload[::-1]}"
        
        out_file = f"encrypted_message_{timestamp}.enc"
        with open(out_file, "w") as f:
            f.write(encrypted_mock)
        return out_file

    def decrypt_data(self, sender_name, encrypted_file_path):
        """Имитация процесса расшифрования своим закрытым ключом и проверки подписи отправителя"""
        # TODO: Заменить на ГОСТ-расшифрование
        try:
            with open(encrypted_file_path, "r") as f:
                data = f.read()
            # Имитация успешного расшифрования
            decrypted_mock = f"Расшифровано от {sender_name}:\nОригинал: {data[::-1].split(' :ataD ')[0]}"
            return decrypted_mock
        except Exception as e:
            return str(e)


# ==========================================
# БЛОК 3: ГРАФИЧЕСКИЙ ИНТЕРФЕЙС (VIEW & CONTROLLER)
# ==========================================
class CryptoApp(tk.Tk):
    def __init__(self, crypto_provider):
        super().__init__()
        self.crypto = crypto_provider
        
        # Настройка главного окна
        self.title("АРМ Связиста - Криптографический модуль (Демо)")
        self.geometry("650x450")
        self.configure(bg=BG_COLOR)
        self.resizable(False, False)

        # Настройка стилей для ttk виджетов (вкладки, комбобоксы)
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background=BG_COLOR, borderwidth=0)
        style.configure('TNotebook.Tab', background=ACCENT_COLOR, foreground=FG_COLOR, font=FONT_MAIN, padding=[10, 5])
        style.map('TNotebook.Tab', background=[('selected', '#5E81AC')]) # Цвет активной вкладки
        style.configure('TFrame', background=BG_COLOR)
        style.configure('TLabel', background=BG_COLOR, foreground=FG_COLOR, font=FONT_MAIN)
        style.configure('TButton', background=ACCENT_COLOR, foreground=FG_COLOR, font=FONT_MAIN)
        style.configure('TCombobox', fieldbackground=BG_COLOR, background=ACCENT_COLOR, foreground="black")

        # Создание вкладок (режимов работы)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        # Инициализация фреймов для каждого режима
        self.init_encryption_tab()
        self.init_decryption_tab()
        self.init_key_transfer_tab()

    # ------------------------------------------
    # БЛОК 3.1: РЕЖИМ ШИФРОВАНИЯ
    # ------------------------------------------
    def init_encryption_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text='Шифрование')

        # Выбор типа данных
        ttk.Label(tab, text="Тип данных для шифрования:").grid(row=0, column=0, sticky="w", padx=20, pady=(20, 5))
        self.data_type_var = tk.StringVar(value="Радиоданные")
        data_types = ["Шифр", "Радиоданные", "Совмещенные данные"]
        ttk.Combobox(tab, textvariable=self.data_type_var, values=data_types, state="readonly", width=30).grid(row=0, column=1, padx=20, pady=(20, 5))

        # Выбор открытого ключа адресата
        ttk.Label(tab, text="Открытый ключ адресата:").grid(row=1, column=0, sticky="w", padx=20, pady=10)
        self.pub_key_path_var = tk.StringVar(value="Не выбран...")
        ttk.Label(tab, textvariable=self.pub_key_path_var, foreground="#A3BE8C").grid(row=1, column=1, sticky="w", padx=20, pady=10)
        ttk.Button(tab, text="Выбрать файл ключа", command=self.select_public_key).grid(row=1, column=2, padx=10, pady=10)

        # Поле ввода данных
        ttk.Label(tab, text="Текст для шифрования:").grid(row=2, column=0, sticky="nw", padx=20, pady=10)
        self.enc_text_area = tk.Text(tab, height=8, width=45, bg=ACCENT_COLOR, fg=FG_COLOR, font=FONT_MAIN, insertbackground=FG_COLOR)
        self.enc_text_area.grid(row=2, column=1, columnspan=2, padx=20, pady=10)

        # Кнопка выполнения
        ttk.Button(tab, text="Зашифровать и Сохранить", command=self.process_encryption).grid(row=3, column=1, pady=20)

    def select_public_key(self):
        filepath = filedialog.askopenfilename(title="Выберите открытый ключ", filetypes=[("PEM Files", "*.pem"), ("All Files", "*.*")])
        if filepath:
            self.pub_key_path_var.set(filepath)

    def process_encryption(self):
        pub_key = self.pub_key_path_var.get()
        data_type = self.data_type_var.get()
        payload = self.enc_text_area.get("1.0", tk.END).strip()

        if pub_key == "Не выбран..." or not payload:
            messagebox.showwarning("Ошибка", "Выберите ключ адресата и введите данные!")
            return

        out_file = self.crypto.encrypt_data(data_type, pub_key, payload)
        messagebox.showinfo("Успех", f"Данные зашифрованы и сохранены в файл:\n{out_file}")
        self.enc_text_area.delete("1.0", tk.END)

    # ------------------------------------------
    # БЛОК 3.2: РЕЖИМ РАСШИФРОВАНИЯ
    # ------------------------------------------
    def init_decryption_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text='Расшифрование')

        # Выбор абонента
        ttk.Label(tab, text="Абонент (Отправитель):").grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))
        self.sender_var = tk.StringVar()
        ttk.Entry(tab, textvariable=self.sender_var, width=32).grid(row=0, column=1, padx=20, pady=(20, 10))

        # Выбор зашифрованного файла
        ttk.Label(tab, text="Зашифрованный файл:").grid(row=1, column=0, sticky="w", padx=20, pady=10)
        self.enc_file_path_var = tk.StringVar(value="Не выбран...")
        ttk.Label(tab, textvariable=self.enc_file_path_var, foreground="#A3BE8C").grid(row=1, column=1, sticky="w", padx=20, pady=10)
        ttk.Button(tab, text="Выбрать файл", command=self.select_encrypted_file).grid(row=1, column=2, padx=10, pady=10)

        # Вывод результата
        ttk.Label(tab, text="Результат расшифрования:").grid(row=2, column=0, sticky="nw", padx=20, pady=10)
        self.dec_text_area = tk.Text(tab, height=8, width=45, bg=ACCENT_COLOR, fg=FG_COLOR, font=FONT_MAIN, state=tk.DISABLED)
        self.dec_text_area.grid(row=2, column=1, columnspan=2, padx=20, pady=10)

        # Кнопка выполнения
        ttk.Button(tab, text="Расшифровать", command=self.process_decryption).grid(row=3, column=1, pady=20)

    def select_encrypted_file(self):
        filepath = filedialog.askopenfilename(title="Выберите зашифрованный файл", filetypes=[("Encrypted Files", "*.enc"), ("All Files", "*.*")])
        if filepath:
            self.enc_file_path_var.set(filepath)

    def process_decryption(self):
        sender = self.sender_var.get().strip()
        enc_file = self.enc_file_path_var.get()

        if not sender or enc_file == "Не выбран...":
            messagebox.showwarning("Ошибка", "Укажите отправителя и выберите файл!")
            return

        result = self.crypto.decrypt_data(sender, enc_file)
        
        self.dec_text_area.config(state=tk.NORMAL)
        self.dec_text_area.delete("1.0", tk.END)
        self.dec_text_area.insert("1.0", result)
        self.dec_text_area.config(state=tk.DISABLED)

    # ------------------------------------------
    # БЛОК 3.3: РЕЖИМ ПЕРЕДАЧИ ОТКРЫТОГО КЛЮЧА
    # ------------------------------------------
    def init_key_transfer_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text='Передача открытого ключа')

        ttk.Label(tab, text="Формирование открытого ключа для обмена", font=FONT_TITLE).pack(pady=(30, 10))
        ttk.Label(tab, text="Введите идентификатор узла/абонента (например: Пост_Альфа):").pack(pady=5)
        
        self.node_name_var = tk.StringVar()
        ttk.Entry(tab, textvariable=self.node_name_var, width=40).pack(pady=10)

        ttk.Button(tab, text="Сгенерировать ключи", command=self.generate_keys).pack(pady=20)
        
        self.key_status_label = ttk.Label(tab, text="", foreground="#EBCB8B")
        self.key_status_label.pack(pady=10)

    def generate_keys(self):
        node_name = self.node_name_var.get().strip()
        if not node_name:
            messagebox.showwarning("Ошибка", "Введите идентификатор узла!")
            return
            
        pub_path = self.crypto.generate_keypair(node_name)
        self.key_status_label.config(text=f"Ключи успешно сгенерированы!\nОткрытый ключ для передачи сохранен по пути:\n{os.path.abspath(pub_path)}")


# ==========================================
# БЛОК 4: ТОЧКА ВХОДА (MAIN)
# ==========================================
if __name__ == "__main__":
    # Инициализация крипто-ядра
    provider = CryptoProvider()
    
    # Запуск графического интерфейса
    app = CryptoApp(provider)
    app.mainloop()