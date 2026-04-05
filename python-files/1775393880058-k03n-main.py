import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
import numpy as np
import pickle
import os
import re
from collections import Counter
import threading
import time

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
        self.training_data = []  # Хранит текст для обучения
        
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
        """Преобразует текст в вектор для входа нейросети"""
        words = text.lower().split()[:50]
        vec = np.zeros(self.input_size)
        for i, word in enumerate(words):
            if word in self.vocab:
                vec[i % self.input_size] = self.vocab[word]
            else:
                vec[i % self.input_size] = hash(word) % 1000 / 1000.0
        return vec.reshape(1, -1)
    
    def build_vocab(self, texts):
        """Создает словарь из текстов"""
        all_words = []
        for text in texts:
            words = re.findall(r'\w+', text.lower())
            all_words.extend(words)
        word_counts = Counter(all_words)
        # Берем самые частые слова
        for idx, (word, _) in enumerate(word_counts.most_common(self.input_size)):
            self.vocab[word] = idx / self.input_size
        return len(self.vocab)
    
    def save(self, path):
        with open(path, 'wb') as f:
            pickle.dump({
                'W1': self.W1, 'b1': self.b1,
                'W2': self.W2, 'b2': self.b2,
                'vocab': self.vocab,
                'reverse_vocab': self.reverse_vocab,
                'training_data': self.training_data
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
                self.reverse_vocab = data.get('reverse_vocab', {})
                self.training_data = data.get('training_data', [])
            return True
        return False
    
    def generate_response(self, question):
        """Генерирует ответ на вопрос"""
        if not self.training_data:
            return "Нейросеть еще не обучена. Загрузите текстовый файл и нажмите 'Обучение'"
        
        vec = self.text_to_vector(question)
        output = self.forward(vec)
        
        # Ищем наиболее релевантный текст из обучающих данных
        best_match = None
        best_score = -1
        
        for text in self.training_data:
            text_vec = self.text_to_vector(text[:200])
            text_output = self.forward(text_vec)
            score = np.dot(output.flatten(), text_output.flatten())
            if score > best_score:
                best_score = score
                best_match = text
        
        # Если нашли похожий текст, возвращаем его
        if best_match and best_score > 0.1:
            # Ищем предложение, связанное с вопросом
            sentences = re.split(r'[.!?]+', best_match)
            question_words = set(re.findall(r'\w+', question.lower()))
            
            for sent in sentences:
                sent_words = set(re.findall(r'\w+', sent.lower()))
                if len(question_words & sent_words) > 0:
                    return sent.strip() + "."
            
            # Если нет точного совпадения, возвращаем начало
            return best_match[:300] + "..."
        
        return "Извините, я не нашел информации по вашему вопросу в обученных данных."

# ===================== ОБУЧЕНИЕ =====================
class Trainer:
    def __init__(self, model):
        self.model = model
        self.stop_training = False
        
    def train(self, texts, callback_progress, callback_stats, epochs=5):
        """Обучение нейросети на текстах"""
        self.stop_training = False
        
        # Подготовка данных
        all_text = " ".join(texts)
        sentences = re.split(r'[.!?;\n]+', all_text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        if len(sentences) < 2:
            callback_stats(0, 0, 0, "Недостаточно данных для обучения")
            return
        
        # Создаем словарь
        vocab_size = self.model.build_vocab(sentences)
        callback_stats(0, 0, 0, f"Словарь создан: {vocab_size} слов")
        
        # Создаем обучающие пары (предложение -> следующее предложение)
        train_pairs = []
        for i in range(len(sentences) - 1):
            input_vec = self.model.text_to_vector(sentences[i])
            target_vec = self.model.text_to_vector(sentences[i + 1])
            train_pairs.append((input_vec, target_vec))
        
        total_errors = 0
        total_epochs = epochs
        
        for epoch in range(epochs):
            if self.stop_training:
                callback_stats(epoch, total_errors, 0, "Обучение остановлено")
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
            
            callback_stats(epoch + 1, epoch_errors, accuracy, f"Эпоха {epoch+1}/{epochs}")
            time.sleep(0.1)  # Чтобы UI не зависал
        
        # Сохраняем тексты для поиска ответов
        self.model.training_data = sentences
        
        callback_stats(epochs, total_errors, 100, "Обучение завершено!")
        return True

# ===================== ГЛАВНОЕ ОКНО =====================
class NeuralChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("НейроЧат - Обучение на текстовом файле")
        self.root.geometry("900x700")
        self.root.configure(bg='#2c3e50')
        
        # Инициализация нейросети
        self.model = SimpleNeuralNetwork()
        self.trainer = Trainer(self.model)
        self.current_file = None
        
        # Загрузка сохраненной модели
        self.load_model()
        
        # Создание интерфейса
        self.create_widgets()
        
    def create_widgets(self):
        # Заголовок
        title_frame = tk.Frame(self.root, bg='#34495e', height=80)
        title_frame.pack(fill='x')
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame, text="🤖 НЕЙРОСЕТЬ ДЛЯ ОБУЧЕНИЯ НА ТЕКСТЕ", 
                               font=('Arial', 18, 'bold'), fg='white', bg='#34495e')
        title_label.pack(pady=20)
        
        # Название нейросети
        name_frame = tk.Frame(self.root, bg='#2c3e50')
        name_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(name_frame, text="Название нейросети:", font=('Arial', 12), 
                fg='white', bg='#2c3e50').pack(side='left')
        
        self.net_name = tk.Entry(name_frame, font=('Arial', 12), width=30)
        self.net_name.pack(side='left', padx=10)
        self.net_name.insert(0, "TextLearner AI")
        
        # Кнопки
        buttons_frame = tk.Frame(self.root, bg='#2c3e50')
        buttons_frame.pack(pady=10)
        
        self.chat_btn = tk.Button(buttons_frame, text="💬 ЧАТ", command=self.open_chat,
                                 font=('Arial', 14, 'bold'), bg='#27ae60', fg='white',
                                 width=15, height=2)
        self.chat_btn.pack(side='left', padx=10)
        
        self.train_btn = tk.Button(buttons_frame, text="📚 ОБУЧЕНИЕ", command=self.open_training,
                                  font=('Arial', 14, 'bold'), bg='#e67e22', fg='white',
                                  width=15, height=2)
        self.train_btn.pack(side='left', padx=10)
        
        # Статус
        self.status_label = tk.Label(self.root, text="Статус: Готов к работе", 
                                     font=('Arial', 10), fg='#bdc3c7', bg='#2c3e50')
        self.status_label.pack(pady=5)
        
    def load_model(self):
        if self.model.load("saved_model.pkl"):
            self.status_label.config(text="Статус: Модель загружена")
        else:
            self.status_label.config(text="Статус: Новая модель создана")
    
    def save_model(self):
        self.model.save("saved_model.pkl")
        self.status_label.config(text="Статус: Модель сохранена")
    
    def open_chat(self):
        chat_window = tk.Toplevel(self.root)
        chat_window.title("Чат с нейросетью - " + self.net_name.get())
        chat_window.geometry("700x600")
        chat_window.configure(bg='#ecf0f1')
        
        # Область сообщений
        self.chat_area = scrolledtext.ScrolledText(chat_window, wrap=tk.WORD, 
                                                    font=('Arial', 11), height=25)
        self.chat_area.pack(fill='both', expand=True, padx=10, pady=10)
        self.chat_area.insert(tk.END, "🤖 Нейросеть готова к диалогу!\n")
        self.chat_area.insert(tk.END, "💡 Задайте любой вопрос по обученным данным\n")
        self.chat_area.insert(tk.END, "-" * 50 + "\n\n")
        self.chat_area.config(state='disabled')
        
        # Поле ввода
        input_frame = tk.Frame(chat_window, bg='#ecf0f1')
        input_frame.pack(fill='x', padx=10, pady=10)
        
        self.question_entry = tk.Entry(input_frame, font=('Arial', 12))
        self.question_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        self.question_entry.bind('<Return>', lambda e: self.send_question())
        
        send_btn = tk.Button(input_frame, text="Отправить", command=self.send_question,
                            font=('Arial', 11), bg='#3498db', fg='white', padx=20)
        send_btn.pack(side='right')
        
        self.current_chat_window = chat_window
    
    def send_question(self):
        question = self.question_entry.get().strip()
        if not question:
            return
        
        self.question_entry.delete(0, tk.END)
        
        # Добавляем вопрос в чат
        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, f"\n👤 Вы: {question}\n", 'user')
        self.chat_area.insert(tk.END, "🤖 Нейросеть: ")
        self.chat_area.see(tk.END)
        self.chat_area.update()
        
        # Получаем ответ от нейросети
        answer = self.model.generate_response(question)
        
        self.chat_area.insert(tk.END, f"{answer}\n\n", 'bot')
        self.chat_area.see(tk.END)
        self.chat_area.config(state='disabled')
        
        # Настройка цветов
        self.chat_area.tag_config('user', foreground='#2c3e50', font=('Arial', 11, 'bold'))
        self.chat_area.tag_config('bot', foreground='#27ae60', font=('Arial', 11))
    
    def open_training(self):
        train_window = tk.Toplevel(self.root)
        train_window.title("Обучение нейросети")
        train_window.geometry("800x600")
        train_window.configure(bg='#ecf0f1')
        
        # Выбор файла
        file_frame = tk.Frame(train_window, bg='#ecf0f1')
        file_frame.pack(fill='x', padx=20, pady=10)
        
        self.file_label = tk.Label(file_frame, text="Файл не выбран", 
                                   font=('Arial', 10), bg='#ecf0f1', fg='#7f8c8d')
        self.file_label.pack(side='left', padx=(0, 10))
        
        select_btn = tk.Button(file_frame, text="Выбрать текстовый файл", 
                              command=self.select_file, bg='#3498db', fg='white')
        select_btn.pack(side='left')
        
        # Статистика обучения
        stats_frame = tk.LabelFrame(train_window, text="📊 Статистика обучения", 
                                    font=('Arial', 12, 'bold'), bg='white', padx=10, pady=10)
        stats_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        self.stats_text = scrolledtext.ScrolledText(stats_frame, font=('Arial', 10), 
                                                     height=15, width=70)
        self.stats_text.pack(fill='both', expand=True)
        
        # Прогресс
        self.progress_var = tk.DoubleVar()
        self.progress_bar = tk.ttk.Progressbar(train_window, variable=self.progress_var, 
                                               maximum=100, length=400)
        self.progress_bar.pack(pady=10)
        
        # Кнопка старта
        self.start_train_btn = tk.Button(train_window, text="Начать обучение", 
                                         command=self.start_training,
                                         font=('Arial', 12, 'bold'), bg='#e67e22', 
                                         fg='white', padx=30, pady=10)
        self.start_train_btn.pack(pady=10)
        
        self.stop_train_btn = tk.Button(train_window, text="Остановить обучение", 
                                        command=self.stop_training,
                                        font=('Arial', 12), bg='#e74c3c', 
                                        fg='white', padx=30, pady=10, state='disabled')
        self.stop_train_btn.pack(pady=5)
        
        self.current_train_window = train_window
    
    def select_file(self):
        filename = filedialog.askopenfilename(
            title="Выберите текстовый файл",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
        )
        if filename:
            self.current_file = filename
            self.file_label.config(text=f"Файл: {os.path.basename(filename)}", fg='#27ae60')
            
            # Показываем预览
            with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                preview = f.read(500)
            self.stats_text.insert(tk.END, f"📄 Файл загружен: {os.path.basename(filename)}\n")
            self.stats_text.insert(tk.END, f"📏 Размер: {os.path.getsize(filename)} байт\n")
            self.stats_text.insert(tk.END, f"📝 Превью:\n{preview}...\n\n")
            self.stats_text.see(tk.END)
    
    def start_training(self):
        if not self.current_file:
            messagebox.showwarning("Внимание", "Сначала выберите текстовый файл!")
            return
        
        self.start_train_btn.config(state='disabled')
        self.stop_train_btn.config(state='normal')
        self.stats_text.delete(1.0, tk.END)
        
        # Загрузка текста
        with open(self.current_file, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        
        # Разбиваем на части для обучения
        texts = [text[i:i+1000] for i in range(0, len(text), 1000)]
        
        def update_stats(epoch, errors, accuracy, message):
            self.stats_text.insert(tk.END, f"📈 {message}\n")
            self.stats_text.insert(tk.END, f"   Ошибок в эпохе: {errors}\n")
            self.stats_text.insert(tk.END, f"   Точность: {accuracy:.2f}%\n")
            self.stats_text.insert(tk.END, "-" * 40 + "\n")
            self.stats_text.see(tk.END)
            self.progress_var.set((epoch / 10) * 100 if epoch <= 10 else 100)
            self.root.update()
        
        def train_thread():
            self.trainer.train(texts, update_stats, update_stats, epochs=10)
            self.root.after(0, lambda: self.start_train_btn.config(state='normal'))
            self.root.after(0, lambda: self.stop_train_btn.config(state='disabled'))
            self.root.after(0, lambda: self.save_model())
            self.root.after(0, lambda: messagebox.showinfo("Готово", "Обучение завершено!"))
        
        threading.Thread(target=train_thread, daemon=True).start()
    
    def stop_training(self):
        self.trainer.stop_training = True
        self.stop_train_btn.config(state='disabled')
        self.stats_text.insert(tk.END, "⚠️ Остановка обучения...\n")

# ===================== ЗАПУСК =====================
if __name__ == "__main__":
    import tkinter.ttk as ttk
    root = tk.Tk()
    app = NeuralChatApp(root)
    root.mainloop()