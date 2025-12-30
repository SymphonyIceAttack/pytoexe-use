import tkinter as tk
from tkinter import messagebox
import random

class FakeVirusLock:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("⚠ ВНИМАНИЕ! СИСТЕМА ЗАБЛОКИРОВАНА ⚠")
        
        # Не на весь экран
        self.window.geometry("800x500")
        self.window.resizable(False, False)
        
        # Центрируем окно
        self.window.eval('tk::PlaceWindow . center')
        
        # Стиль
        self.window.configure(bg='black')
        
        # Создаем элементы
        self.create_widgets()
        
        # Шуточные сообщения
        self.messages = [
            "Обнаружен вирус: MEMZ.TROJAN",
            "Шифрование файлов... 0%",
            "Подключение к серверу хакеров...",
            "Ваш пароль был отправлен в darknet",
            "Не волнуйтесь, это всего лишь шутка! :)"
        ]
        
        # Запускаем анимацию
        self.animate_text()
        
        # Можно закрыть Alt+F4 или крестиком
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)
        self.window.bind('<Escape>', lambda e: self.close_window())
        
    def create_widgets(self):
        # Заголовок
        title = tk.Label(
            self.window,
            text="🚨 СИСТЕМА ЗАБЛОКИРОВАНА 🚨",
            font=("Arial", 32, "bold"),
            fg="red",
            bg="black"
        )
        title.pack(pady=30)
        
        # Изображение замка (текстовое)
        lock_label = tk.Label(
            self.window,
            text="🔒",
            font=("Arial", 64),
            fg="yellow",
            bg="black"
        )
        lock_label.pack()
        
        # Предупреждение
        warning = tk.Label(
            self.window,
            text="Ваша система была заблокирована из-за подозрительной активности.\n\n"
                 "Для разблокировки введите пароль в поле ниже и нажмите 'Разблокировать'.\n"
                 "Любой пароль подойдет!",
            font=("Arial", 14),
            fg="white",
            bg="black",
            justify="center"
        )
        warning.pack(pady=20)
        
        # Контейнер для поля ввода
        input_frame = tk.Frame(self.window, bg="black")
        input_frame.pack(pady=10)
        
        # Поле ввода пароля
        self.password_entry = tk.Entry(
            input_frame,
            font=("Arial", 18),
            width=30,
            show="*",
            bg="#222",
            fg="#0f0",
            insertbackground="#0f0"
        )
        self.password_entry.pack(side=tk.LEFT, padx=5)
        self.password_entry.focus()
        
        # Кнопка разблокировки
        unlock_btn = tk.Button(
            input_frame,
            text="Разблокировать",
            font=("Arial", 14, "bold"),
            bg="green",
            fg="white",
            command=self.unlock,
            relief="raised",
            padx=20
        )
        unlock_btn.pack(side=tk.LEFT, padx=5)
        
        # Область с меняющимся текстом
        self.scrolling_text = tk.Label(
            self.window,
            text="",
            font=("Courier", 12),
            fg="#0f0",
            bg="black",
            height=3
        )
        self.scrolling_text.pack(pady=10)
        
        # Подсказка внизу
        hint = tk.Label(
            self.window,
            text="Это шуточная программа. Ничего не заблокировано!\n"
                 "Можно закрыть через Alt+F4, Escape или крестик.",
            font=("Arial", 10),
            fg="#aaa",
            bg="black",
            justify="center"
        )
        hint.pack(pady=20)
        
    def animate_text(self):
        """Анимированный текст для вида"""
        if hasattr(self, 'text_index'):
            self.text_index = (self.text_index + 1) % len(self.messages)
        else:
            self.text_index = 0
        
        message = self.messages[self.text_index]
        
        # Добавляем "загрузку" к сообщению
        dots = "." * ((self.text_index % 3) + 1)
        display_text = f"> {message}{dots}"
        
        self.scrolling_text.config(text=display_text)
        
        # Случайное мигание
        if random.random() > 0.7:
            self.scrolling_text.config(fg="red")
            self.window.after(100, lambda: self.scrolling_text.config(fg="#0f0"))
        
        # Повторяем каждые 1.5 секунды
        self.window.after(1500, self.animate_text)
    
    def unlock(self):
        """Любой пароль работает!"""
        password = self.password_entry.get()
        if password == "":
            messagebox.showinfo("Внимание", "Введите любой пароль! Даже пустой!")
        else:
            # Создаем новое окно с "успешной разблокировкой"
            success = tk.Toplevel(self.window)
            success.title("Успех!")
            success.geometry("400x200")
            success.configure(bg="green")
            
            # Центрируем
            success.eval(f'tk::PlaceWindow {str(success)} center')
            
            tk.Label(
                success,
                text="✅ СИСТЕМА РАЗБЛОКИРОВАНА! ✅",
                font=("Arial", 20, "bold"),
                fg="white",
                bg="green"
            ).pack(pady=30)
            
            tk.Label(
                success,
                text=f"Пароль '{password}' принят!\n\n"
                     "Это была всего лишь шутка!\n"
                     "Нажмите OK для выхода.",
                font=("Arial", 12),
                fg="white",
                bg="green",
                justify="center"
            ).pack(pady=10)
            
            tk.Button(
                success,
                text="OK",
                font=("Arial", 14),
                bg="white",
                fg="green",
                command=lambda: [success.destroy(), self.window.destroy()],
                width=10
            ).pack(pady=20)
            
            success.transient(self.window)
            success.grab_set()
    
    def close_window(self):
        """Закрытие окна с подтверждением (шуточным)"""
        response = messagebox.askyesno(
            "Подтверждение",
            "Вы уверены, что хотите закрыть?\n"
            "(На самом деле можно, это же шутка!)"
        )
        if response:
            self.window.destroy()
    
    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    # Шуточное предупреждение при запуске
    print("=" * 60)
    print("Запускается ШУТОЧНАЯ программа 'Винлокер'")
    print("Она не наносит вред системе и легко закрывается!")
    print("=" * 60)
    
    app = FakeVirusLock()
    app.run()