import customtkinter as ctk
from tkinter import messagebox, ttk
import csv
import os
import sys
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==========================================
# === НАСТРОЙКИ ФАЙЛА И ПУТЕЙ ===
# ==========================================

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FILE_NAME = os.path.join(BASE_DIR, "photo_orders.csv")

SENDER_EMAIL = "твой_email@gmail.com"
SENDER_PASSWORD = "твой_пароль_приложения"
SMTP_SERVER = "imap.gmail.com"  
SMTP_PORT = 465

ctk.set_appearance_mode("dark")  
ctk.set_default_color_theme("green")  

row_time_mapping = {}

# ==========================================
# === ФУНКЦИОНАЛЬНАЯ ЧАСТЬ ===
# ==========================================

def init_file():
    if not os.path.exists(FILE_NAME):
        with open(FILE_NAME, mode="w", encoding="utf-8-sig", newline="") as file:
            writer = csv.writer(file, delimiter=";")
            writer.writerow(["Дата и время", "Тип фото", "Количество", "Email клиента", "Статус"])

def load_orders_to_table():
    for row in tree.get_children():
        tree.delete(row)
        
    if not os.path.exists(FILE_NAME):
        return

    try:
        with open(FILE_NAME, mode="r", encoding="utf-8-sig") as file:
            reader = csv.reader(file, delimiter=";")
            header = next(reader)
            for row in reader:
                if len(row) >= 5:
                    full_time, photo_type, qty, email, status = row[0], row[1], row[2], row[3], row[4]
                    try:
                        time_obj = datetime.strptime(full_time, "%Y-%m-%d %H:%M:%S")
                        display_time = time_obj.strftime("%H:%M:%S")
                    except:
                        display_time = full_time
                    
                    # Добавляем пустое поле для таймера (оно заполнится само в update_timers)
                    item_id = tree.insert("", 0, values=(display_time, photo_type, f"{qty} шт.", email, status, ""))
                    row_time_mapping[item_id] = full_time
                    
                    if status == "Выполнено":
                        tree.item(item_id, tags=("completed",))
                    else:
                        tree.item(item_id, tags=("pending",))
    except Exception as e:
        print(f"Ошибка при загрузке данных: {e}")

def send_email_notification(to_email, photo_type, quantity):
    if not SENDER_EMAIL or "твой_email" in SENDER_EMAIL:
        return False
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = f"Ваш заказ в фотоателье готов!"
        body = f"Здравствуйте!\nБлагодарим за визит.\n\nЗаказ оформлен:\nУслуга: {photo_type}\nКоличество: {quantity} шт.\n\nХорошего дня!"
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        with smtplib.SMTP_SSL(SMTP_SERVER.replace("imap", "smtp"), SMTP_PORT) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        return True
    except:
        return False

def add_order():
    photo_type = type_segmented_button.get()
    
    quantity_str = qty_entry.get()
    if not quantity_str.isdigit():
        messagebox.showerror("Ошибка", "Пожалуйста, введите корректное число!")
        return
    quantity = int(quantity_str)
    if quantity <= 0:
        messagebox.showerror("Ошибка", "Количество должно быть больше нуля!")
        return

    client_email = email_entry.get().strip()
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_time = datetime.now().strftime("%H:%M:%S")
    initial_status = "В процессе"

    if client_email:
        if "@" not in client_email or "." not in client_email:
            messagebox.showerror("Ошибка", "Некорректный формат Email адреса!")
            return
        send_email_notification(client_email, photo_type, quantity)
    else:
        client_email = "-"

    try:
        with open(FILE_NAME, mode="a", encoding="utf-8-sig", newline="") as file:
            writer = csv.writer(file, delimiter=";")
            writer.writerow([current_time, photo_type, quantity, client_email, initial_status])
            
        item_id = tree.insert("", 0, values=(formatted_time, photo_type, f"{quantity} шт.", client_email, initial_status, ""))
        row_time_mapping[item_id] = current_time
        tree.item(item_id, tags=("pending",))
        
        qty_entry.delete(0, ctk.END)
        qty_entry.insert(0, "1")
        email_entry.delete(0, ctk.END)
        
    except Exception as e:
        messagebox.showerror("Ошибка файла", f"Не удалось сохранить заказ:\n{e}")

def complete_order():
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showwarning("Внимание", "Пожалуйста, выберите заказ из списка!")
        return
    
    item_id = selected_item[0]
    current_values = tree.item(item_id, "values")
    
    if current_values[4] == "Выполнено":
        messagebox.showinfo("Инфо", "Этот заказ уже отмечен как выполненный.")
        return
    
    target_time = row_time_mapping.get(item_id)
    if not target_time:
        messagebox.showerror("Ошибка", "Не удалось найти заказ в базе данных.")
        return

    rows = []
    try:
        with open(FILE_NAME, mode="r", encoding="utf-8-sig") as file:
            reader = csv.reader(file, delimiter=";")
            header = next(reader)
            rows.append(header)
            for row in reader:
                if row[0] == target_time:
                    row[4] = "Выполнено"
                rows.append(row)
                
        with open(FILE_NAME, mode="w", encoding="utf-8-sig", newline="") as file:
            writer = csv.writer(file, delimiter=";")
            writer.writerows(rows)
            
        tree.item(item_id, values=(current_values[0], current_values[1], current_values[2], current_values[3], "Выполнено", "—"))
        tree.item(item_id, tags=("completed",))
        
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось обновить статус в файле:\n{e}")

def update_timers():
    """Каждую секунду обновляет значения таймеров для активных заказов."""
    now = datetime.now()
    
    for item_id in tree.get_children():
        values = tree.item(item_id, "values")
        if not values: continue
        
        status = values[4]
        # Если заказ выполнен, таймер не нужен
        if status == "Выполнено":
            tree.set(item_id, column="timer", value="—")
            continue
            
        creation_time_str = row_time_mapping.get(item_id)
        if not creation_time_str: continue
        
        try:
            # Превращаем строку из базы в объект времени
            creation_time = datetime.strptime(creation_time_str, "%Y-%m-%d %H:%M:%S")
            # Дедлайн = время создания + 30 минут
            deadline = creation_time + timedelta(minutes=30)
            remaining = deadline - now
            
            if remaining.total_seconds() > 0:
                # Если время еще есть, считаем минуты и секунды
                mins, secs = divmod(int(remaining.total_seconds()), 60)
                time_text = f"{mins:02d}:{secs:02d}"
                tree.set(item_id, column="timer", value=time_text)
                
                # Убеждаемся, что строка белая (если она была красной, но мы, например, перевели время)
                if "pending" not in tree.item(item_id, "tags"):
                    tree.item(item_id, tags=("pending",))
            else:
                # Если время истекло
                tree.set(item_id, column="timer", value="00:00 (!)")
                if "overdue" not in tree.item(item_id, "tags"):
                    tree.item(item_id, tags=("overdue",))
                    
        except Exception as e:
            pass

    # Запускаем эту же функцию снова через 1000 миллисекунд (1 секунду)
    app.after(1000, update_timers)


init_file()

# ==========================================
# === ГРАФИЧЕСКИЙ ИНТЕРФЕЙС ===
# ==========================================
app = ctk.CTk()
app.title("Учет заказов Фотоателье v5.0 (с таймером)")
app.geometry("700x820") # Немного расширили окно для новой колонки
app.resizable(False, False)

label_title = ctk.CTkLabel(app, text="НОВЫЙ ЗАКАЗ", font=("Roboto", 24, "bold"))
label_title.pack(pady=(15, 5))

frame_type = ctk.CTkFrame(app, fg_color="transparent")
frame_type.pack(pady=10, padx=25, fill="x")
ctk.CTkLabel(frame_type, text="1. Тип фотографии:", font=("Roboto", 14, "bold")).pack(anchor="w", pady=(0, 5))
type_segmented_button = ctk.CTkSegmentedButton(frame_type, values=["Паспорт", "Биометрик", "Америка"], font=("Roboto", 13), height=40)
type_segmented_button.set("Паспорт")
type_segmented_button.pack(fill="x")

frame_inputs = ctk.CTkFrame(app, fg_color="transparent")
frame_inputs.pack(pady=10, padx=25, fill="x")

frame_qty = ctk.CTkFrame(frame_inputs, fg_color="transparent")
frame_qty.pack(side="left", padx=(0, 20))
ctk.CTkLabel(frame_qty, text="2. Кол-во (шт):", font=("Roboto", 14, "bold")).pack(anchor="w", pady=(0, 5))
qty_entry = ctk.CTkEntry(frame_qty, font=("Roboto", 16, "bold"), width=80, height=40, justify="center")
qty_entry.insert(0, "1")
qty_entry.pack()

frame_email = ctk.CTkFrame(frame_inputs, fg_color="transparent")
frame_email.pack(side="left", fill="x", expand=True)
ctk.CTkLabel(frame_email, text="3. Email клиента (опционально):", font=("Roboto", 14, "bold")).pack(anchor="w", pady=(0, 5))
email_entry = ctk.CTkEntry(frame_email, font=("Roboto", 14), placeholder_text="example@mail.com", height=40)
email_entry.pack(fill="x")

add_button = ctk.CTkButton(app, text="ДОБАВИТЬ И СОХРАНИТЬ ЗАКАЗ", font=("Roboto", 16, "bold"), height=50, corner_radius=8, command=add_order)
add_button.pack(pady=20, padx=25, fill="x")

frame_list = ctk.CTkFrame(app, corner_radius=10)
frame_list.pack(pady=5, padx=25, fill="both", expand=True)

ctk.CTkLabel(frame_list, text="Список задач:", font=("Roboto", 13, "bold")).pack(pady=(10, 5))

style = ttk.Style()
style.theme_use("default")
style.configure("Treeview", background="#FFFFFF", foreground="#000000", rowheight=32, fieldbackground="#FFFFFF", font=("Roboto", 11))
style.configure("Treeview.Heading", font=("Roboto", 11, "bold"), background="#E0E0E0", foreground="#000000")
style.map("Treeview", background=[('selected', '#1f538d')], foreground=[('selected', '#FFFFFF')])

# Добавили колонку timer
columns = ("time", "type", "qty", "email", "status", "timer")
tree = ttk.Treeview(frame_list, columns=columns, show="headings", style="Treeview")

tree.heading("time", text="Время")
tree.heading("type", text="Тип фото")
tree.heading("qty", text="Кол-во")
tree.heading("email", text="Email")
tree.heading("status", text="Статус")
tree.heading("timer", text="Таймер") # Заголовок новой колонки

tree.column("time", width=70, anchor="center")
tree.column("type", width=100, anchor="center")
tree.column("qty", width=60, anchor="center")
tree.column("email", width=130, anchor="w")
tree.column("status", width=90, anchor="center")
tree.column("timer", width=80, anchor="center") # Ширина новой колонки

# Настройка цветов для статусов
tree.tag_configure("completed", background="#D4EDDA", foreground="#155724") # Нежно-зеленый
tree.tag_configure("pending", background="#FFFFFF", foreground="#000000")   # Белый
tree.tag_configure("overdue", background="#F8D7DA", foreground="#721C24")   # Тревожно-красный для просроченных

scrollbar = ttk.Scrollbar(frame_list, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=scrollbar.set)

tree.pack(side="left", fill="both", expand=True, padx=(15, 0), pady=(0, 15))
scrollbar.pack(side="right", fill="y", padx=(0, 15), pady=(0, 15))

complete_button = ctk.CTkButton(app, text="✔  ОТМЕТИТЬ КАК ВЫПОЛНЕННЫЙ", fg_color="#28A745", hover_color="#218838",
                              font=("Roboto", 15, "bold"), height=50, corner_radius=8, command=complete_order)
complete_button.pack(pady=20, padx=25, fill="x")

# --- ЗАГРУЗКА И ЗАПУСК ---
load_orders_to_table()
update_timers() # Запускаем тиканье таймера

app.mainloop()