import tkinter as tk
from tkinter import messagebox, ttk

class SnilsCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("Расчет контрольных чисел СНИЛС")
        self.root.geometry("500x350")
        self.root.resizable(False, False)
        
        # Настройка стилей
        style = ttk.Style()
        style.theme_use('clam')
        
        # Основной фрейм
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Заголовок
        title_label = ttk.Label(main_frame, text="Расчет контрольных чисел СНИЛС", 
                                 font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Фрейм для ввода
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=10)
        
        # Поле ввода номера
        ttk.Label(input_frame, text="Введите 9 цифр номера СНИЛС:", 
                 font=('Arial', 10)).pack(anchor=tk.W)
        
        self.number_entry = ttk.Entry(input_frame, width=30, font=('Arial', 12))
        self.number_entry.pack(fill=tk.X, pady=(5, 10))
        self.number_entry.bind('<KeyRelease>', self.validate_input)
        
        # Кнопка расчета
        self.calc_button = ttk.Button(input_frame, text="Рассчитать контрольные числа", 
                                      command=self.calculate_snils)
        self.calc_button.pack(pady=10)
        
        # Фрейм для результата
        result_frame = ttk.LabelFrame(main_frame, text="Результат", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Поле для вывода результата
        self.result_text = tk.Text(result_frame, height=4, width=40, 
                                   font=('Arial', 11), wrap=tk.WORD)
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        # Добавляем прокрутку для текстового поля
        scrollbar = ttk.Scrollbar(self.result_text, command=self.result_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.config(yscrollcommand=scrollbar.set)
        
        # Нижняя часть с информацией об авторе
        footer_frame = ttk.Frame(root)
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        
        author_label = ttk.Label(footer_frame, 
                                 text="Автор: Заблоцких А.Г. zablotsky@96.sfr.gov.ru",
                                 font=('Arial', 9, 'italic'),
                                 foreground='gray')
        author_label.pack()
        
    def validate_input(self, event=None):
        """Валидация ввода - только цифры и ограничение длины"""
        value = self.number_entry.get()
        # Удаляем все нецифровые символы
        if value:
            filtered = ''.join(filter(str.isdigit, value))
            # Ограничиваем длину до 9 символов
            if len(filtered) > 9:
                filtered = filtered[:9]
            if filtered != value:
                self.number_entry.delete(0, tk.END)
                self.number_entry.insert(0, filtered)
    
    def calculate_control_sum(self, number):
        """Расчет контрольной суммы СНИЛС"""
        # Преобразуем строку в список цифр
        digits = [int(d) for d in str(number)]
        
        # Проверяем, что у нас 9 цифр
        if len(digits) != 9:
            return None, "Ошибка: требуется ровно 9 цифр"
        
        # Вычисляем контрольную сумму по алгоритму
        total = 0
        for i, digit in enumerate(digits):
            total += digit * (9 - i)
        
        # Определяем контрольное число
        if total < 100:
            control = total
        elif total == 100 or total == 101:
            control = 0
        else:
            remainder = total % 101
            if remainder < 100:
                control = remainder
            else:
                control = 0
        
        return control, None
    
    def calculate_snils(self):
        """Основная функция расчета"""
        number = self.number_entry.get().strip()
        
        # Проверка на пустой ввод
        if not number:
            messagebox.showwarning("Предупреждение", "Введите номер СНИЛС")
            return
        
        # Проверка на длину
        if len(number) != 9:
            messagebox.showwarning("Предупреждение", "Номер должен содержать ровно 9 цифр")
            return
        
        # Проверка на цифры
        if not number.isdigit():
            messagebox.showwarning("Предупреждение", "Номер должен содержать только цифры")
            return
        
        # Расчет контрольной суммы
        control, error = self.calculate_control_sum(number)
        
        if error:
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(1.0, error)
            self.result_text.tag_configure("error", foreground="red")
            self.result_text.tag_add("error", "1.0", "end")
        else:
            # Форматирование результата
            formatted_number = f"{number[:3]}-{number[3:6]}-{number[6:9]}"
            control_formatted = f"{control:02d}"
            
            result = f"Введенный номер: {formatted_number}\n"
            result += f"Рассчитанное контрольное число: {control_formatted}\n"
            result += f"Полный СНИЛС: {formatted_number} {control_formatted}"
            
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(1.0, result)
            
            # Подсветка результата
            self.result_text.tag_configure("success", foreground="green", font=('Arial', 11, 'bold'))
            self.result_text.tag_add("success", "2.0", "end-1c")

def main():
    root = tk.Tk()
    app = SnilsCalculator(root)
    
    # Центрирование окна на экране
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()

if __name__ == "__main__":
    main()