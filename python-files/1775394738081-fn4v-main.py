import tkinter as tk
from tkinter import filedialog, messagebox
import numpy as np
import pickle
import os
import re
from collections import Counter
import threading
import time
from datetime import datetime

# Попробуем импортировать customtkinter для современного дизайна
try:
    import customtkinter as ctk
    USE_CUSTOM = True
except ImportError:
    USE_CUSTOM = False
    print("Для современного дизайна установите: pip install customtkinter")
    print("Используется стандартный tkinter...")

# ===================== НЕЙРОСЕТЬ =====================
class SimpleNeuralNetwork:
    def __init__(self, input_size=1000, hidden_size=500, output_size=1000):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        
        # Инициализация весов
        self.W1 = np.random.randn(input_size, hidden_size) * 0.01
        self.b1 = np.zeros((1, hidden_size))
        self.W2 = np.random.randn(hidden_size, output_size) * 0.01
        self.b2 = np.zeros((1, output_size))
        
        self.vocab = {}
        self.reverse_vocab = {}
        self.training_data = []
        self.network_name = "TextLearner AI"
        
    def sigmoid(self, x):
        return 1 / (1 + np.exp(-np.clip(x, -500, 500)))
    
    def sigmoid_derivative(self, x):
        return x * (1 - x)
    
    def forward(self, X):
        self.z1 = np.dot(X, self.W1) + self.b1
        self.a1 = self.sigmoid(self.z1)
        self.z2 = np.dot(self.a1, self.W2) + self.b2
        self.a2 = self.sigmoid(self.z2)
        return self.a2
    
    def backward(self, X, y, output, learning_rate=0.01):
        m = X.shape[0]
        dZ2 = output - y
        dW2 = np.dot(self.a1.T, dZ2) / m
        db2 = np.sum(dZ2, axis=0, keepdims=True) / m
        dZ1 = np.dot(dZ2, self.W2.T) * self.sigmoid_derivative(self.a1)
        dW1 = np.dot(X.T, dZ1) / m
        db1 = np.sum(dZ1, axis=0, keepdims=True) / m
        
        self.W2 -= learning_rate * dW2
        self.b2 -= learning_rate * db2
        self.W1 -= learning_rate * dW1
        self.b1 -= learning_rate * db1
        
    def train_step(self, X, y, lr=0.01):
        output = self.forward(X)
        loss = np.mean((output - y) ** 2)
        self.backward(X, y, output, lr)
        return loss
    
    def text_to_vector(self, text):
        words = re.findall(r'\w+', text.lower())[:50]
        vec = np.zeros(self.input_size)
        for i, word in enumerate(words):
            if word in self.vocab:
                vec[i % self.input_size] = self.vocab[word]
            else:
                vec[i % self.input_size] = hash(word) % 1000 / 1000.0
        return vec.reshape(1, -1)
    
    def build_vocab(self, texts):
        all_words = []
        for text in texts:
            words = re.findall(r'\w+', text.lower())
            all_words.extend(words)
        word_counts = Counter(all_words)
        for idx, (word, _) in enumerate(word_counts.most_common(self.input_size)):
            self.vocab[word] = idx / self.input_size
        return len(self.vocab)
    
    def save(self, path):
        with open(path, 'wb') as f:
            pickle.dump({
                'W1': self.W1, 'b1': self.b1,
                'W2': self.W2, 'b2': self.b2,
                'vocab': self.vocab,
                'training_data': self.training_data,
                'network_name': self.network_name
            }, f)
    
    def load(self, path):
        if os.path.exists(path):
            with open(path, 'rb') as f:
                data = pickle.load(f)
                self.W1 = data['W1']
                self.b1 = data['b1']
                self.W2 = data['W2']
                self.b2 = data['b2']
                self.vocab = data.get('vocab', {})
                self.training_data = data.get('training_data', [])
                self.network_name = data.get('network_name', "TextLearner AI")
            return True
        return False
    
    def generate_response(self, question):
        if not self.training_data:
            return "📭 Нейросеть еще не обучена. Загрузите текстовый файл и нажмите 'Обучение'"
        
        vec = self.text_to_vector(question)
        output = self.forward(vec)
        
        best_match = None
        best_score = -1
        
        for text in self.training_data:
            text_vec = self.text_to_vector(text[:200])
            text_output = self.forward(text_vec)
            score = np.dot(output.flatten(), text_output.flatten())
            if score > best_score:
                best_score = score
                best_match = text
        
        if best_match and best_score > 0.1:
            sentences = re.split(r'[.!?]+', best_match)
            question_words = set(re.findall(r'\w+', question.lower()))
            
            for sent in sentences:
                sent_words = set(re.findall(r'\w+', sent.lower()))
                if len(question_words & sent_words) > 0:
                    return sent.strip() + "."
            
            return best_match[:400] + "..."
        
        return "❓ Извините, я не нашел информации по вашему вопросу в обученных данных."

# ===================== ОБУЧЕНИЕ =====================
class Trainer:
    def __init__(self, model):
        self.model = model
        self.stop_training = False
        
    def train(self, texts, callback_stats, epochs=5):
        self.stop_training = False
        
        all_text = " ".join(texts)
        sentences = re.split(r'[.!?;\n]+', all_text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        if len(sentences) < 2:
            callback_stats(0, 0, 0, "Недостаточно данных для обучения")
            return False
        
        vocab_size = self.model.build_vocab(sentences)
        callback_stats(0, 0, 0, f"📚 Словарь создан: {vocab_size} слов")
        
        train_pairs = []
        for i in range(len(sentences) - 1):
            input_vec = self.model.text_to_vector(sentences[i])
            target_vec = self.model.text_to_vector(sentences[i + 1])
            train_pairs.append((input_vec, target_vec))
        
        total_errors = 0
        
        for epoch in range(epochs):
            if self.stop_training:
                callback_stats(epoch, total_errors, 0, "⏹️ Обучение остановлено")
                break
                
            epoch_errors = 0
            epoch_loss = 0
            
            for input_vec, target_vec in train_pairs:
                loss = self.model.train_step(input_vec, target_vec, lr=0.05)
                epoch_loss += loss
                if loss > 0.5:
                    epoch_errors += 1
            
            total_errors += epoch_errors
            accuracy = (1 - epoch_errors / len(train_pairs)) * 100 if train_pairs else 0
            
            callback_stats(epoch + 1, epoch_errors, accuracy, f"🎯 Эпоха {epoch+1}/{epochs}")
            time.sleep(0.05)
        
        self.model.training_data = sentences
        callback_stats(epochs, total_errors, 100, "✅ Обучение завершено!")
        return True

# ===================== СОВРЕМЕННЫЙ ИНТЕРФЕЙС =====================
class ModernNeuralChat:
    def __init__(self):
        # Настройка внешнего вида
        if USE_CUSTOM:
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("blue")
            self.root = ctk.CTk()
        else:
            self.root = tk.Tk()
        
        self.root.title("NeuroChat AI - Платформа обучения нейросетей")
        self.root.geometry("1100x700")
        self.root.minsize(900, 600)
        
        # Цвета для стандартного tkinter
        self.colors = {
            'bg': '#1a1a2e',
            'sidebar': '#16213e',
            'card': '#0f3460',
            'accent': '#e94560',
            'text': '#eeeeee',
            'text_secondary': '#a0a0a0',
            'success': '#27ae60',
            'warning': '#f39c12',
            'error': '#e74c3c'
        }
        
        if not USE_CUSTOM:
            self.root.configure(bg=self.colors['bg'])
        
        # Инициализация
        self.model = SimpleNeuralNetwork()
        self.trainer = Trainer(self.model)
        self.current_file = None
        
        # Загрузка модели
        self.load_model()
        
        # Создание интерфейса
        self.create_interface()
        
    def load_model(self):
        if self.model.load("saved_model.pkl"):
            self.model_loaded = True
        else:
            self.model_loaded = False
    
    def save_model(self):
        self.model.save("saved_model.pkl")
    
    def create_interface(self):
        if USE_CUSTOM:
            self.create_custom_interface()
        else:
            self.create_standard_interface()
    
    def create_custom_interface(self):
        # Боковая панель
        self.sidebar = ctk.CTkFrame(self.root, width=280, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        # Логотип
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(pady=30)
        
        logo_label = ctk.CTkLabel(logo_frame, text="🧠", font=("Segoe UI", 48))
        logo_label.pack()
        
        title_label = ctk.CTkLabel(logo_frame, text="NeuroChat AI", 
                                   font=("Segoe UI", 20, "bold"))
        title_label.pack()
        
        subtitle_label = ctk.CTkLabel(logo_frame, text="Нейросетевая платформа", 
                                      font=("Segoe UI", 12), text_color="gray")
        subtitle_label.pack()
        
        # Название нейросети
        name_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        name_frame.pack(pady=20, padx=20, fill="x")
        
        name_label = ctk.CTkLabel(name_frame, text="Название сети", 
                                  font=("Segoe UI", 12))
        name_label.pack(anchor="w")
        
        self.net_name_entry = ctk.CTkEntry(name_frame, placeholder_text="Введите название")
        self.net_name_entry.pack(fill="x", pady=(5, 0))
        self.net_name_entry.insert(0, self.model.network_name)
        
        # Кнопки
        buttons_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        buttons_frame.pack(pady=20, padx=20, fill="x")
        
        self.chat_btn = ctk.CTkButton(buttons_frame, text="💬 Чат", 
                                      command=self.open_chat,
                                      height=45, font=("Segoe UI", 14, "bold"),
                                      fg_color="#27ae60", hover_color="#2ecc71")
        self.chat_btn.pack(fill="x", pady=5)
        
        self.train_btn = ctk.CTkButton(buttons_frame, text="📚 Обучение", 
                                       command=self.open_training,
                                       height=45, font=("Segoe UI", 14, "bold"),
                                       fg_color="#e67e22", hover_color="#f39c12")
        self.train_btn.pack(fill="x", pady=5)
        
        # Статус
        status_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        status_frame.pack(side="bottom", pady=20, padx=20, fill="x")
        
        self.status_indicator = ctk.CTkLabel(status_frame, text="🟢", 
                                             font=("Segoe UI", 16))
        self.status_indicator.pack(side="left")
        
        self.status_label = ctk.CTkLabel(status_frame, text="Готов к работе", 
                                         font=("Segoe UI", 11))
        self.status_label.pack(side="left", padx=5)
        
        # Основная область
        self.main_area = ctk.CTkFrame(self.root, corner_radius=10)
        self.main_area.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        # Приветственный экран
        self.show_welcome()
    
    def create_standard_interface(self):
        # Верхняя панель
        top_frame = tk.Frame(self.root, bg=self.colors['sidebar'], height=80)
        top_frame.pack(fill="x")
        top_frame.pack_propagate(False)
        
        title_label = tk.Label(top_frame, text="🧠 NeuroChat AI", 
                               font=("Segoe UI", 24, "bold"), 
                               fg=self.colors['text'], bg=self.colors['sidebar'])
        title_label.pack(side="left", padx=30, pady=20)
        
        subtitle_label = tk.Label(top_frame, text="Нейросетевая платформа обучения", 
                                  font=("Segoe UI", 11), 
                                  fg=self.colors['text_secondary'], bg=self.colors['sidebar'])
        subtitle_label.pack(side="left", padx=10)
        
        # Боковая панель
        sidebar = tk.Frame(self.root, bg=self.colors['sidebar'], width=260)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        
        # Название нейросети
        name_frame = tk.Frame(sidebar, bg=self.colors['sidebar'])
        name_frame.pack(pady=20, padx=15, fill="x")
        
        tk.Label(name_frame, text="Название нейросети", 
                font=("Segoe UI", 10), fg=self.colors['text_secondary'], 
                bg=self.colors['sidebar']).pack(anchor="w")
        
        self.net_name_entry = tk.Entry(name_frame, font=("Segoe UI", 12), 
                                       bg=self.colors['card'], fg=self.colors['text'],
                                       insertbackground=self.colors['text'], relief="flat")
        self.net_name_entry.pack(fill="x", pady=(5, 0), ipady=8)
        self.net_name_entry.insert(0, self.model.network_name)
        
        # Кнопки
        btn_frame = tk.Frame(sidebar, bg=self.colors['sidebar'])
        btn_frame.pack(pady=20, padx=15, fill="x")
        
        self.chat_btn = tk.Button(btn_frame, text="💬 Чат", command=self.open_chat,
                                 font=("Segoe UI", 12, "bold"), bg='#27ae60', 
                                 fg='white', relief="flat", cursor="hand2")
        self.chat_btn.pack(fill="x", pady=5, ipady=10)
        
        self.train_btn = tk.Button(btn_frame, text="📚 Обучение", command=self.open_training,
                                  font=("Segoe UI", 12, "bold"), bg='#e67e22', 
                                  fg='white', relief="flat", cursor="hand2")
        self.train_btn.pack(fill="x", pady=5, ipady=10)
        
        # Статус
        status_frame = tk.Frame(sidebar, bg=self.colors['sidebar'])
        status_frame.pack(side="bottom", pady=20, padx=15, fill="x")
        
        self.status_label = tk.Label(status_frame, text="● Готов к работе", 
                                     font=("Segoe UI", 10), fg='#27ae60', 
                                     bg=self.colors['sidebar'])
        self.status_label.pack()
        
        # Основная область
        self.main_area = tk.Frame(self.root, bg=self.colors['bg'])
        self.main_area.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        self.show_welcome()
    
    def show_welcome(self):
        self.clear_main_area()
        
        if USE_CUSTOM:
            welcome_frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
            welcome_frame.pack(expand=True)
            
            icon_label = ctk.CTkLabel(welcome_frame, text="🤖", font=("Segoe UI", 80))
            icon_label.pack(pady=20)
            
            title_label = ctk.CTkLabel(welcome_frame, text="Добро пожаловать в NeuroChat AI", 
                                       font=("Segoe UI", 28, "bold"))
            title_label.pack()
            
            desc_label = ctk.CTkLabel(welcome_frame, 
                                     text="Интеллектуальная нейросеть для обучения на текстовых данных",
                                     font=("Segoe UI", 14), text_color="gray")
            desc_label.pack(pady=10)
            
            info_frame = ctk.CTkFrame(welcome_frame, fg_color="transparent")
            info_frame.pack(pady=30)
            
            for text in ["📁 Загрузите текстовый файл", "🎓 Обучите нейросеть", "💬 Начните диалог"]:
                item = ctk.CTkLabel(info_frame, text=text, font=("Segoe UI", 12))
                item.pack(pady=5)
        else:
            welcome_frame = tk.Frame(self.main_area, bg=self.colors['bg'])
            welcome_frame.pack(expand=True)
            
            icon_label = tk.Label(welcome_frame, text="🤖", font=("Segoe UI", 80), 
                                 fg=self.colors['accent'], bg=self.colors['bg'])
            icon_label.pack(pady=20)
            
            title_label = tk.Label(welcome_frame, text="Добро пожаловать в NeuroChat AI", 
                                  font=("Segoe UI", 28, "bold"), 
                                  fg=self.colors['text'], bg=self.colors['bg'])
            title_label.pack()
            
            desc_label = tk.Label(welcome_frame, 
                                 text="Интеллектуальная нейросеть для обучения на текстовых данных",
                                 font=("Segoe UI", 14), fg=self.colors['text_secondary'], 
                                 bg=self.colors['bg'])
            desc_label.pack(pady=10)
            
            info_frame = tk.Frame(welcome_frame, bg=self.colors['bg'])
            info_frame.pack(pady=30)
            
            for text in ["📁 Загрузите текстовый файл", "🎓 Обучите нейросеть", "💬 Начните диалог"]:
                item = tk.Label(info_frame, text=text, font=("Segoe UI", 12), 
                               fg=self.colors['text_secondary'], bg=self.colors['bg'])
                item.pack(pady=5)
    
    def clear_main_area(self):
        for widget in self.main_area.winfo_children():
            widget.destroy()
    
    def open_chat(self):
        self.clear_main_area()
        
        if USE_CUSTOM:
            # Верхняя панель чата
            chat_header = ctk.CTkFrame(self.main_area, height=60, corner_radius=0)
            chat_header.pack(fill="x", padx=0, pady=0)
            
            header_title = ctk.CTkLabel(chat_header, text=f"💬 Чат с {self.net_name_entry.get()}", 
                                        font=("Segoe UI", 18, "bold"))
            header_title.pack(side="left", padx=20, pady=15)
            
            # Область сообщений
            self.chat_frame = ctk.CTkScrollableFrame(self.main_area, fg_color="transparent")
            self.chat_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Приветственное сообщение
            self.add_chat_message("system", f"Привет! Я {self.net_name_entry.get()}. Чем могу помочь?")
            
            # Панель ввода
            input_frame = ctk.CTkFrame(self.main_area, height=80, corner_radius=0)
            input_frame.pack(fill="x", side="bottom")
            
            self.message_entry = ctk.CTkEntry(input_frame, placeholder_text="Введите сообщение...", 
                                              font=("Segoe UI", 13), height=45)
            self.message_entry.pack(side="left", fill="x", expand=True, padx=(20, 10), pady=15)
            self.message_entry.bind("<Return>", lambda e: self.send_message())
            
            send_btn = ctk.CTkButton(input_frame, text="Отправить", command=self.send_message,
                                    width=100, height=45, fg_color="#27ae60")
            send_btn.pack(side="right", padx=(0, 20), pady=15)
        else:
            # Верхняя панель
            chat_header = tk.Frame(self.main_area, bg=self.colors['sidebar'], height=60)
            chat_header.pack(fill="x")
            chat_header.pack_propagate(False)
            
            header_title = tk.Label(chat_header, text=f"💬 Чат с {self.net_name_entry.get()}", 
                                   font=("Segoe UI", 16, "bold"), fg=self.colors['text'], 
                                   bg=self.colors['sidebar'])
            header_title.pack(side="left", padx=20, pady=15)
            
            # Область сообщений
            self.chat_frame = tk.Frame(self.main_area, bg=self.colors['bg'])
            self.chat_frame.pack(fill="both", expand=True)
            
            self.chat_canvas = tk.Canvas(self.chat_frame, bg=self.colors['bg'], highlightthickness=0)
            scrollbar = tk.Scrollbar(self.chat_frame, orient="vertical", command=self.chat_canvas.yview)
            self.chat_scrollable = tk.Frame(self.chat_canvas, bg=self.colors['bg'])
            
            self.chat_scrollable.bind("<Configure>", lambda e: self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all")))
            self.chat_canvas.create_window((0, 0), window=self.chat_scrollable, anchor="nw")
            self.chat_canvas.configure(yscrollcommand=scrollbar.set)
            
            self.chat_canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            self.add_chat_message("system", f"Привет! Я {self.net_name_entry.get()}. Чем могу помочь?")
            
            # Панель ввода
            input_frame = tk.Frame(self.main_area, bg=self.colors['sidebar'], height=80)
            input_frame.pack(fill="x", side="bottom")
            input_frame.pack_propagate(False)
            
            self.message_entry = tk.Entry(input_frame, font=("Segoe UI", 12), 
                                         bg=self.colors['card'], fg=self.colors['text'],
                                         insertbackground=self.colors['text'], relief="flat")
            self.message_entry.pack(side="left", fill="x", expand=True, padx=(20, 10), pady=15, ipady=10)
            self.message_entry.bind("<Return>", lambda e: self.send_message())
            
            send_btn = tk.Button(input_frame, text="Отправить", command=self.send_message,
                                font=("Segoe UI", 11, "bold"), bg='#27ae60', fg='white',
                                relief="flat", cursor="hand2")
            send_btn.pack(side="right", padx=(0, 20), pady=15, ipadx=20, ipady=8)
    
    def add_chat_message(self, sender, message):
        if USE_CUSTOM:
            msg_frame = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
            msg_frame.pack(fill="x", padx=20, pady=10)
            
            if sender == "user":
                align = "e"
                bg_color = "#27ae60"
                text_color = "white"
                icon = "👤"
            elif sender == "bot":
                align = "w"
                bg_color = "#0f3460"
                text_color = "white"
                icon = "🤖"
            else:
                align = "center"
                bg_color = "#e67e22"
                text_color = "white"
                icon = "ℹ️"
            
            if align != "center":
                container = ctk.CTkFrame(msg_frame, fg_color="transparent")
                container.pack(anchor=align)
                
                bubble = ctk.CTkFrame(container, fg_color=bg_color, corner_radius=15)
                bubble.pack(padx=5, pady=5)
                
                msg_label = ctk.CTkLabel(bubble, text=f"{icon} {message}", 
                                        font=("Segoe UI", 12), text_color=text_color,
                                        wraplength=500, justify="left")
                msg_label.pack(padx=15, pady=10)
            else:
                msg_label = ctk.CTkLabel(msg_frame, text=message, 
                                        font=("Segoe UI", 11, "italic"),
                                        text_color="gray")
                msg_label.pack()
            
            self.chat_frame._parent_canvas.yview_moveto(1)
        else:
            msg_frame = tk.Frame(self.chat_scrollable, bg=self.colors['bg'])
            msg_frame.pack(fill="x", padx=20, pady=5)
            
            if sender == "user":
                text_color = "#27ae60"
                icon = "👤"
                justify = "right"
            elif sender == "bot":
                text_color = "#3498db"
                icon = "🤖"
                justify = "left"
            else:
                text_color = "#e67e22"
                icon = "ℹ️"
                justify = "center"
            
            msg_label = tk.Label(msg_frame, text=f"{icon} {message}", 
                                font=("Segoe UI", 11), fg=text_color, 
                                bg=self.colors['bg'], wraplength=500, justify=justify)
            msg_label.pack(anchor=justify)
            
            self.chat_canvas.yview_moveto(1)
    
    def send_message(self):
        question = self.message_entry.get().strip()
        if not question:
            return
        
        self.message_entry.delete(0, tk.END)
        self.add_chat_message("user", question)
        
        # Имитация печати
        self.add_chat_message("system", "🤔 Думаю...")
        
        def get_response():
            time.sleep(0.5)
            answer = self.model.generate_response(question)
            self.root.after(0, lambda: self.update_bot_response(answer))
        
        threading.Thread(target=get_response, daemon=True).start()
    
    def update_bot_response(self, answer):
        # Удаляем сообщение "Думаю..."
        if USE_CUSTOM:
            for widget in self.chat_frame.winfo_children():
                if hasattr(widget, 'winfo_children'):
                    for child in widget.winfo_children():
                        if hasattr(child, 'winfo_children'):
                            for subchild in child.winfo_children():
                                if hasattr(subchild, 'cget') and subchild.cget("text") == "🤔 Думаю...":
                                    widget.destroy()
        else:
            for widget in self.chat_scrollable.winfo_children():
                for child in widget.winfo_children():
                    if child.cget("text") == "🤔 Думаю...":
                        widget.destroy()
        
        self.add_chat_message("bot", answer)
    
    def open_training(self):
        self.clear_main_area()
        
        if USE_CUSTOM:
            # Заголовок
            header = ctk.CTkFrame(self.main_area, height=60, corner_radius=0)
            header.pack(fill="x")
            
            title_label = ctk.CTkLabel(header, text="📚 Обучение нейросети", 
                                       font=("Segoe UI", 18, "bold"))
            title_label.pack(side="left", padx=20, pady=15)
            
            # Контент
            content_frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
            content_frame.pack(fill="both", expand=True, padx=30, pady=20)
            
            # Выбор файла
            file_card = ctk.CTkFrame(content_frame, corner_radius=15)
            file_card.pack(fill="x", pady=10)
            
            file_title = ctk.CTkLabel(file_card, text="Выбор файла для обучения", 
                                      font=("Segoe UI", 14, "bold"))
            file_title.pack(anchor="w", padx=20, pady=(15, 5))
            
            self.file_label = ctk.CTkLabel(file_card, text="Файл не выбран", 
                                           font=("Segoe UI", 12), text_color="gray")
            self.file_label.pack(anchor="w", padx=20)
            
            select_btn = ctk.CTkButton(file_card, text="📂 Выбрать текстовый файл", 
                                       command=self.select_file,
                                       fg_color="#3498db", hover_color="#2980b9")
            select_btn.pack(anchor="w", padx=20, pady=(10, 15))
            
            # Статистика
            stats_card = ctk.CTkFrame(content_frame, corner_radius=15)
            stats_card.pack(fill="both", expand=True, pady=10)
            
            stats_title = ctk.CTkLabel(stats_card, text="📊 Статистика обучения", 
                                       font=("Segoe UI", 14, "bold"))
            stats_title.pack(anchor="w", padx=20, pady=(15, 10))
            
            self.stats_text = ctk.CTkTextbox(stats_card, font=("Consolas", 11))
            self.stats_text.pack(fill="both", expand=True, padx=20, pady=(0, 15))
            
            # Прогресс
            self.progress_bar = ctk.CTkProgressBar(content_frame, height=20)
            self.progress_bar.pack(fill="x", pady=10)
            self.progress_bar.set(0)
            
            # Кнопки
            btn_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            btn_frame.pack(fill="x", pady=10)
            
            self.start_btn = ctk.CTkButton(btn_frame, text="🚀 Начать обучение", 
                                           command=self.start_training,
                                           fg_color="#27ae60", hover_color="#2ecc71",
                                           height=45, font=("Segoe UI", 14, "bold"))
            self.start_btn.pack(side="left", padx=5)
            
            self.stop_btn = ctk.CTkButton(btn_frame, text="⏹️ Остановить", 
                                          command=self.stop_training,
                                          fg_color="#e74c3c", hover_color="#c0392b",
                                          height=45, state="disabled")
            self.stop_btn.pack(side="left", padx=5)
        else:
            # Стандартная версия
            header = tk.Frame(self.main_area, bg=self.colors['sidebar'], height=60)
            header.pack(fill="x")
            header.pack_propagate(False)
            
            title_label = tk.Label(header, text="📚 Обучение нейросети", 
                                  font=("Segoe UI", 16, "bold"), 
                                  fg=self.colors['text'], bg=self.colors['sidebar'])
            title_label.pack(side="left", padx=20, pady=15)
            
            # Контент
            content_frame = tk.Frame(self.main_area, bg=self.colors['bg'])
            content_frame.pack(fill="both", expand=True, padx=30, pady=20)
            
            # Выбор файла
            file_frame = tk.LabelFrame(content_frame, text="Выбор файла", 
                                       font=("Segoe UI", 12, "bold"),
                                       fg=self.colors['text'], bg=self.colors['card'],
                                       bd=0, padx=10, pady=10)
            file_frame.pack(fill="x", pady=10)
            
            self.file_label = tk.Label(file_frame, text="Файл не выбран", 
                                      font=("Segoe UI", 11), fg=self.colors['text_secondary'],
                                      bg=self.colors['card'])
            self.file_label.pack(side="left", padx=10)
            
            select_btn = tk.Button(file_frame, text="Выбрать файл", 
                                  command=self.select_file,
                                  bg='#3498db', fg='white', font=("Segoe UI", 10),
                                  relief="flat", cursor="hand2")
            select_btn.pack(side="right", padx=10)
            
            # Статистика
            stats_frame = tk.LabelFrame(content_frame, text="Статистика", 
                                        font=("Segoe UI", 12, "bold"),
                                        fg=self.colors['text'], bg=self.colors['card'],
                                        bd=0, padx=10, pady=10)
            stats_frame.pack(fill="both", expand=True, pady=10)
            
            self.stats_text = tk.Text(stats_frame, font=("Consolas", 10), 
                                      bg=self.colors['bg'], fg=self.colors['text'],
                                      relief="flat", wrap=tk.WORD)
            self.stats_text.pack(fill="both", expand=True)
            
            # Кнопки
            btn_frame = tk.Frame(content_frame, bg=self.colors['bg'])
            btn_frame.pack(fill="x", pady=10)
            
            self.start_btn = tk.Button(btn_frame, text="Начать обучение", 
                                      command=self.start_training,
                                      bg='#27ae60', fg='white', font=("Segoe UI", 12, "bold"),
                                      relief="flat", cursor="hand2")
            self.start_btn.pack(side="left", padx=5, ipadx=20, ipady=8)
            
            self.stop_btn = tk.Button(btn_frame, text="Остановить", 
                                     command=self.stop_training,
                                     bg='#e74c3c', fg='white', font=("Segoe UI", 12),
                                     relief="flat", cursor="hand2", state="disabled")
            self.stop_btn.pack(side="left", padx=5, ipadx=20, ipady=8)
    
    def select_file(self):
        filename = filedialog.askopenfilename(
            title="Выберите текстовый файл",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
        )
        if filename:
            self.current_file = filename
            self.file_label.config(text=f"📄 {os.path.basename(filename)}")
            
            with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                preview = f.read(500)
            
            self.stats_text.insert("end", f"✅ Файл загружен: {os.path.basename(filename)}\n")
            self.stats_text.insert("end", f"📏 Размер: {os.path.getsize(filename)} байт\n")
            self.stats_text.insert("end", f"📝 Превью:\n{preview}...\n\n")
            self.stats_text.see("end")
    
    def start_training(self):
        if not self.current_file:
            if USE_CUSTOM:
                messagebox.showwarning("Внимание", "Сначала выберите текстовый файл!")
            else:
                messagebox.showwarning("Внимание", "Сначала выберите текстовый файл!")
            return
        
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        
        # Обновляем название сети
        self.model.network_name = self.net_name_entry.get()
        
        # Загрузка текста
        with open(self.current_file, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        
        texts = [text[i:i+1000] for i in range(0, len(text), 1000)]
        
        def update_stats(epoch, errors, accuracy, message):
            self.stats_text.insert("end", f"{message}\n")
            if epoch > 0:
                self.stats_text.insert("end", f"   📊 Ошибок: {errors}\n")
                self.stats_text.insert("end", f"   📈 Точность: {accuracy:.2f}%\n")
            self.stats_text.insert("end", "-" * 50 + "\n")
            self.stats_text.see("end")
            
            if USE_CUSTOM:
                self.progress_bar.set((epoch / 10) if epoch <= 10 else 1)
            self.root.update()
        
        def train_thread():
            self.trainer.train(texts, update_stats, epochs=10)
            self.root.after(0, lambda: self.start_btn.configure(state="normal"))
            self.root.after(0, lambda: self.stop_btn.configure(state="disabled"))
            self.root.after(0, self.save_model)
            self.root.after(0, lambda: messagebox.showinfo("Готово", "Обучение завершено!"))
        
        threading.Thread(target=train_thread, daemon=True).start()
    
    def stop_training(self):
        self.trainer.stop_training = True
        self.stop_btn.configure(state="disabled")
        self.stats_text.insert("end", "⚠️ Остановка обучения...\n")
    
    def run(self):
        self.root.mainloop()

# ===================== ЗАПУСК =====================
if __name__ == "__main__":
    app = ModernNeuralChat()
    app.run()