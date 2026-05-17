import tkinter as tk
from tkinter import messagebox, ttk
import random
import json
from dataclasses import dataclass
from typing import List, Tuple, Optional
import numpy as np

# ==================== Криптографическое ядро (Схема Шамира) ====================

@dataclass
class Share:
    """Класс для хранения одной доли секрета (x, y)"""
    x: int
    y: int

class ShamirSecretSharing:
    """
    Реализация пороговой схемы разделения секрета Шамира (2 из 3).
    Работает в простом числовом поле (по модулю простого числа).
    """
    def __init__(self, threshold: int = 2, total_shares: int = 3, prime: int = 999999937):
        """
        :param threshold: минимальное количество долей для восстановления (k)
        :param total_shares: общее количество долей (n)
        :param prime: простое число (должно быть больше максимального секрета и всех коэффициентов)
        """
        self.threshold = threshold
        self.total_shares = total_shares
        self.prime = prime

    def _mod(self, value: int) -> int:
        """Корректное взятие по модулю простого числа"""
        return value % self.prime

    def split_secret(self, secret: int) -> List[Share]:
        """
        Разделение секрета на доли.
        Генерируем полином степени (threshold - 1): f(x) = secret + a1*x + a2*x^2 + ... + a_{k-1}*x^{k-1}
        Для threshold=2 это линейная функция: f(x) = secret + a1*x
        """
        # Генерируем случайные коэффициенты (a1...a_{k-1})
        coefficients = [random.randint(1, self.prime - 1) for _ in range(self.threshold - 1)]

        shares = []
        for x_i in range(1, self.total_shares + 1):
            # Вычисляем f(x_i)
            y_i = secret
            for power, coeff in enumerate(coefficients, start=1):
                y_i = (y_i + coeff * (x_i ** power)) % self.prime
            shares.append(Share(x_i, y_i))

        return shares

    def reconstruct_secret(self, shares: List[Share]) -> Optional[int]:
        """
        Восстановление секрета из долей (интерполяция Лагранжа в поле по модулю prime).
        Возвращает секрет или None, если долей недостаточно.
        """
        if len(shares) < self.threshold:
            return None

        # Берем только первые threshold долей
        shares = shares[:self.threshold]
        secret = 0

        for i, share_i in enumerate(shares):
            # Вычисляем базисный полином Лагранжа L_i(0)
            numerator = 1
            denominator = 1
            for j, share_j in enumerate(shares):
                if i != j:
                    numerator = (numerator * (-share_j.x)) % self.prime
                    denominator = (denominator * (share_i.x - share_j.x)) % self.prime

            # Находим обратное к denominator по модулю prime
            lagrange_coeff = (numerator * pow(denominator, -1, self.prime)) % self.prime
            secret = (secret + share_i.y * lagrange_coeff) % self.prime

        return secret

# ==================== Основное приложение ====================

class SecretSharingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Пороговый протокол разделения секрета (2 из 3)")
        self.root.geometry("700x600")
        self.root.resizable(False, False)

        # Параметры протокола
        self.sss = ShamirSecretSharing(threshold=2, total_shares=3)
        self.current_shares: List[Share] = []
        self.reconstructed_secret: Optional[int] = None

        # Состояние режима: False = Отправитель (белый), True = Злоумышленник (красный)
        self.attacker_mode = False

        # Создаем интерфейс
        self.create_widgets()
        self.update_ui_mode()

    def create_widgets(self):
        """Создание всех элементов интерфейса"""
        # ===== Верхняя панель с кнопкой режима =====
        top_frame = tk.Frame(self.root, height=50)
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        top_frame.pack_propagate(False)

        # Кнопка переключения режима (в правом верхнем углу)
        self.mode_btn = tk.Button(
            top_frame,
            text="Злоумышленник",
            command=self.toggle_mode,
            font=("Arial", 10, "bold"),
            bg="#ffcccc",  # светло-красный
            activebackground="#ff9999",
            width=15,
            height=1
        )
        self.mode_btn.pack(side=tk.RIGHT, padx=5, pady=5)

        # Заголовок
        title_label = tk.Label(
            top_frame,
            text="Пороговый протокол (2 из 3)",
            font=("Arial", 14, "bold")
        )
        title_label.pack(side=tk.LEFT, padx=10)

        # ===== Основная рабочая область =====
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # --- Панель ввода секрета ---
        self.input_frame = tk.LabelFrame(self.main_frame, text="Ввод секрета", font=("Arial", 10, "bold"))
        self.input_frame.pack(fill=tk.X, pady=5)

        tk.Label(self.input_frame, text="Секрет (целое число):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.secret_entry = tk.Entry(self.input_frame, width=20)
        self.secret_entry.grid(row=0, column=1, padx=5, pady=5)
        self.secret_entry.insert(0, "1234")  # Пример секрета

        self.split_btn = tk.Button(self.input_frame, text="Сгенерировать секреты (3 шт.)", command=self.split_secret)
        self.split_btn.grid(row=0, column=2, padx=10, pady=5)

        # --- Отображение сгенерированных долей ---
        self.shares_frame = tk.LabelFrame(self.main_frame, text="Сгенерированные секреты (x, y)", font=("Arial", 10, "bold"))
        self.shares_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Текстовое поле для долей
        self.shares_text = tk.Text(self.shares_frame, height=4, width=50, state=tk.DISABLED, font=("Courier", 10))
        self.shares_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Скроллбар для текстового поля
        scrollbar = tk.Scrollbar(self.shares_frame, command=self.shares_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.shares_text.config(yscrollcommand=scrollbar.set)

        # --- Панель восстановления секрета ---
        self.reconstruct_frame = tk.LabelFrame(self.main_frame, text="Восстановление секрета", font=("Arial", 10, "bold"))
        self.reconstruct_frame.pack(fill=tk.X, pady=5)

        tk.Label(self.reconstruct_frame, text="Выберите доли для восстановления (минимум 2):").grid(row=0, column=0, padx=5, pady=5, columnspan=3, sticky="w")

        # Переменные для чекбоксов долей (теперь 3 штуки)
        self.share_vars = []
        self.share_checkboxes = []
        for i in range(3):
            var = tk.BooleanVar()
            self.share_vars.append(var)
            cb = tk.Checkbutton(self.reconstruct_frame, text=f"Секрет {i+1}", variable=var, command=self.update_selection)
            cb.grid(row=1, column=i, padx=20, pady=2, sticky="w")
            self.share_checkboxes.append(cb)

        self.reconstruct_btn = tk.Button(self.reconstruct_frame, text="Восстановить секрет", command=self.reconstruct_secret, state=tk.DISABLED)
        self.reconstruct_btn.grid(row=2, column=0, columnspan=3, pady=10)

        # --- Результат восстановления ---
        self.result_frame = tk.LabelFrame(self.main_frame, text="Результат", font=("Arial", 10, "bold"))
        self.result_frame.pack(fill=tk.X, pady=5)

        self.result_label = tk.Label(self.result_frame, text="Секрет не восстановлен", font=("Arial", 11), fg="blue")
        self.result_label.pack(pady=10)

        # --- Статус режима ---
        self.status_label = tk.Label(
            self.main_frame,
            text="Режим: Отправитель",
            font=("Arial", 9, "italic"),
            fg="gray"
        )
        self.status_label.pack(side=tk.BOTTOM, anchor="se", pady=5)

    def get_colors_for_mode(self):
        """Возвращает цвета для текущего режима"""
        if self.attacker_mode:
            return {
                'bg': '#ffd0d0',  # Светло-красный фон для main_frame
                'frame_bg': '#ffc0c0',  # Чуть темнее для фреймов
                'text_bg': '#fff0f0',  # Очень светлый для текстовых полей
                'btn_bg': '#ffb6b6',  # Для кнопок
                'result_fg': '#8b0000',  # Темно-красный для результата
                'status_text': 'Режим: Злоумышленник (красный интерфейс)'
            }
        else:
            return {
                'bg': 'white',
                'frame_bg': '#f0f0f0',
                'text_bg': 'white',
                'btn_bg': '#f0f0f0',
                'result_fg': 'blue',
                'status_text': 'Режим: Отправитель (белый интерфейс)'
            }

    def update_ui_mode(self):
        """Обновляет интерфейс при смене режима"""
        colors = self.get_colors_for_mode()
        
        # Обновляем фон основного фрейма и всех дочерних элементов
        self.main_frame.config(bg=colors['bg'])
        
        # Обновляем фреймы
        for frame in [self.input_frame, self.shares_frame, self.reconstruct_frame, self.result_frame]:
            frame.config(bg=colors['frame_bg'])
            # Обновляем фон всех Label внутри фреймов
            for child in frame.winfo_children():
                if isinstance(child, (tk.Label, tk.Checkbutton)):
                    if not isinstance(child, tk.LabelFrame):
                        child.config(bg=colors['frame_bg'])
                elif isinstance(child, tk.Frame):
                    child.config(bg=colors['frame_bg'])
        
        # Обновляем текстовое поле
        self.shares_text.config(bg=colors['text_bg'])
        
        # Обновляем кнопки (кроме кнопки режима)
        self.split_btn.config(bg=colors['btn_bg'])
        self.reconstruct_btn.config(bg=colors['btn_bg'])
        
        # Обновляем чекбоксы
        for cb in self.share_checkboxes:
            cb.config(bg=colors['frame_bg'])
        
        # Обновляем цвет результата
        self.result_label.config(fg=colors['result_fg'])
        
        # Обновляем статус
        self.status_label.config(text=colors['status_text'])
        
        # Меняем текст и цвет кнопки режима
        if self.attacker_mode:
            self.mode_btn.config(text="Отправитель", bg="#ff6666", activebackground="#ff4444", fg="white")
        else:
            self.mode_btn.config(text="Злоумышленник", bg="#f0f0f0", activebackground="#e0e0e0", fg="black")

        # Если включен режим злоумышленника - показываем предупреждение
        if self.attacker_mode:
            messagebox.showinfo("Режим злоумышленника",
                              "Вы вошли в режим злоумышленника.\n"
                              "В этом режиме можно попытаться восстановить секрет\n"
                              "с недостаточным количеством долей или подделать данные.\n\n",
                              parent=self.root)

    def toggle_mode(self):
        """Переключение между режимами Отправитель / Злоумышленник"""
        self.attacker_mode = not self.attacker_mode
        self.update_ui_mode()
        # Обновляем состояние кнопки восстановления при смене режима
        self.update_selection()

    def split_secret(self):
        """Обработчик кнопки 'Сгенерировать доли'"""
        try:
            secret = int(self.secret_entry.get())

            # Генерируем доли
            self.current_shares = self.sss.split_secret(secret)

            # Отображаем доли в текстовом поле
            self.shares_text.config(state=tk.NORMAL)
            self.shares_text.delete(1.0, tk.END)
            for i, share in enumerate(self.current_shares, 1):
                self.shares_text.insert(tk.END, f"Секрет {i}: x={share.x}, y={share.y}\n")
            self.shares_text.config(state=tk.DISABLED)

            # Сбрасываем чекбоксы
            for var in self.share_vars:
                var.set(False)

            # Включаем кнопку восстановления, если есть доли
            self.reconstruct_btn.config(state=tk.NORMAL)

            messagebox.showinfo("Успех", "3 Секрета успешно сгенерировано!")

        except ValueError:
            messagebox.showerror("Ошибка", "Введите целое число")

    def update_selection(self):
        """Обновляет состояние кнопки восстановления в зависимости от выбранных секретов"""
        selected = sum(1 for var in self.share_vars if var.get())
        
        # В режиме злоумышленника кнопка всегда активна (можно выбрать даже 1 долю)
        if self.attacker_mode:
            self.reconstruct_btn.config(state=tk.NORMAL)
        else:
            # В обычном режиме нужно минимум 2 доли
            if selected >= 2:
                self.reconstruct_btn.config(state=tk.NORMAL)
            else:
                self.reconstruct_btn.config(state=tk.DISABLED)

    def reconstruct_secret(self):
        """Обработчик кнопки 'Восстановить секрет'"""
        # Собираем выбранные доли
        selected_shares = []
        for i, var in enumerate(self.share_vars):
            if var.get() and i < len(self.current_shares):
                selected_shares.append(self.current_shares[i])

        # Проверяем, есть ли выбранные доли
        if len(selected_shares) == 0:
            messagebox.showwarning("Предупреждение", "Выберите хотя бы один секрет")
            return

        # ОСОБЫЙ СЛУЧАЙ: Злоумышленник выбрал только 1 долю
        if self.attacker_mode and len(selected_shares) == 1:
            # Пытаемся восстановить с одной долей (всегда неудачно)
            secret = self.sss.reconstruct_secret(selected_shares)  # Вернет None
            
            # Издевательское сообщение для злоумышленника
            self.result_label.config(
                text="Одного секрета недостаточно\n"
                    ,
                fg="darkred",
                font=("Arial", 10, "bold")
            )
            
            # Показываем издевательское сообщение
            messagebox.showinfo("Ошибка перехвата", "Получить секрет не удалось")

            return

        # В режиме злоумышленника с 2+ долями
        if self.attacker_mode and len(selected_shares) >= 2:
            secret = self.sss.reconstruct_secret(selected_shares)
            original = int(self.secret_entry.get()) if self.secret_entry.get().isdigit() else None
            
            if secret is not None:
                if original and secret == original:
                    self.result_label.config(
                        text=f"🔴 Злоумышленник успешно восстановил секрет: {secret} 🔴",
                        fg="darkred",
                        font=("Arial", 11, "bold")
                    )
                    messagebox.showinfo("Результат", "Злоумышленник успешно восстановил секрет!")
                else:
                    self.result_label.config(
                        text=f"⚠️ Злоумышленник получил неверный секрет: {secret} ⚠️",
                        fg="#8b0000",
                        font=("Arial", 11)
                    )
                    messagebox.showwarning("Результат", "Злоумышленник получил неверный секрет!")
            else:
                self.result_label.config(
                    text="❌ Ошибка восстановления в режиме злоумышленника",
                    fg="darkred"
                )
                messagebox.showerror("Ошибка", "Не удалось восстановить секрет")
            return

        # Обычный режим (отправитель) с 2+ долями
        if len(selected_shares) < 2:
            messagebox.showwarning("Предупреждение", "Выберите минимум 2 секрета")
            return

        secret = self.sss.reconstruct_secret(selected_shares)
        original = int(self.secret_entry.get()) if self.secret_entry.get().isdigit() else None

        if secret is not None:
            if original and secret == original:
                self.result_label.config(
                    text=f"✅ Секрет успешно восстановлен: {secret} ✅",
                    fg="green",
                    font=("Arial", 11, "bold")
                )
                messagebox.showinfo("Успех", "Секрет успешно восстановлен!")
            else:
                self.result_label.config(
                    text=f"❌ Ошибка: получен неверный секрет {secret}",
                    fg="red"
                )
                messagebox.showerror("Ошибка", "Секрет не совпадает! Возможна атака.")
        else:
            self.result_label.config(
                text="❌ Ошибка восстановления",
                fg="red"
            )
            messagebox.showerror("Ошибка", "Не удалось восстановить секрет")

# ==================== Запуск приложения ====================

if __name__ == "__main__":
    root = tk.Tk()
    app = SecretSharingApp(root)
    root.mainloop()