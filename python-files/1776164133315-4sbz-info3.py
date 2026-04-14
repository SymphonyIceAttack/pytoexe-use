import tkinter as tk
import socket
import getpass
import sys

# --- "Хак": перенаправляем вывод в файл, чтобы скрыть консоль ---
# Это может помочь онлайн-компиляторам не показывать чёрное окно.
sys.stdout = open('output.log', 'w')
sys.stderr = open('error.log', 'w')

# --- Функция для сбора и отображения информации ---
def show_info():
    try:
        # Получаем данные о системе
        hostname = socket.gethostname()
        username = getpass.getuser()
        ip_address = socket.gethostbyname(hostname)

        # Вставляем данные в окно, заменяя старые
        label_hostname.config(text=hostname)
        label_username.config(text=username)
        label_ip.config(text=ip_address)

    except Exception as e:
        # В случае ошибки выводим её текст
        label_hostname.config(text="Ошибка при получении данных")
        # Так как вывод в файл, в окне мы ошибку не увидим, 
        # но она будет записана в error.log

# --- Создание главного окна ---
root = tk.Tk()
root.title("Системная информация")
root.geometry("350x220") 
root.resizable(False, False) # Запрещаем изменять размер окна

font_style = ("Arial", 12)

# --- Создаем и размещаем виджеты (элементы окна) ---
tk.Label(root, text="🖥 Информация о вашем ПК", font=("Arial", 14, "bold")).pack(pady=10)

tk.Label(root, text="Имя компьютера:", font=font_style).pack(anchor="w", padx=30)
label_hostname = tk.Label(root, text="Загрузка...", font=font_style, fg="blue")
label_hostname.pack(pady=(0, 10))

tk.Label(root, text="Имя пользователя:", font=font_style).pack(anchor="w", padx=30)
label_username = tk.Label(root, text="Загрузка...", font=font_style, fg="blue")
label_username.pack(pady=(0, 10))

tk.Label(root, text="IP-адрес:", font=font_style).pack(anchor="w", padx=30)
label_ip = tk.Label(root, text="Загрузка...", font=font_style, fg="blue")
label_ip.pack(pady=(0, 15))

btn_get = tk.Button(root, text="Получить данные", command=show_info, font=("Arial", 12), bg="#4CAF50", fg="white")
btn_get.pack(pady=5)

btn_close = tk.Button(root, text="Закрыть", command=root.destroy, font=("Arial", 12), bg="#f44336", fg="white")
btn_close.pack(pady=5)

# Запускаем окно
root.mainloop()