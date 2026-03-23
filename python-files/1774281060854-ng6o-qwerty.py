import tkinter as tk
from tkinter import messagebox, ttk
import time
from datetime import datetime
import socket
import os

class OrderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Управление заказами")
        self.root.geometry("1000x600")
        
        # Список для хранения заказов
        self.orders = []
        
        # Настройки Bluetooth принтера
        self.printer_address = None
        self.printer_channel = 1  # Обычно для принтеров используется канал 1
        
        # Создание интерфейса главного окна
        self.create_main_window()
        
    def create_main_window(self):
        # Верхняя панель с кнопками
        top_frame = tk.Frame(self.root)
        top_frame.pack(pady=10)
        
        add_btn = tk.Button(top_frame, text="Добавить товар", command=self.open_add_order_window, 
                           bg="green", fg="white", font=("Arial", 12))
        add_btn.pack(side=tk.LEFT, padx=5)
        
        # Кнопка для настройки принтера
        printer_btn = tk.Button(top_frame, text="Настройка принтера", command=self.configure_printer,
                               bg="blue", fg="white", font=("Arial", 12))
        printer_btn.pack(side=tk.LEFT, padx=5)
        
        # Создание таблицы для отображения заказов
        self.create_orders_table()
        
    def create_orders_table(self):
        # Создание фрейма для таблицы
        table_frame = tk.Frame(self.root)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Создание Treeview для отображения заказов
        columns = ('ID', 'Номер телефона', 'Номер заказа', 'Статус', 'Действие')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)
        
        # Настройка заголовков
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
        
        self.tree.column('ID', width=50)
        self.tree.column('Номер телефона', width=150)
        self.tree.column('Номер заказа', width=150)
        self.tree.column('Статус', width=100)
        self.tree.column('Действие', width=100)
        
        # Добавление полосы прокрутки
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Размещение элементов
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Привязка двойного клика
        self.tree.bind('<Double-Button-1>', self.on_order_double_click)
    
    def configure_printer(self):
        """Настройка Bluetooth принтера"""
        config_window = tk.Toplevel(self.root)
        config_window.title("Настройка принтера")
        config_window.geometry("400x250")
        
        tk.Label(config_window, text="MAC-адрес принтера:").pack(pady=5)
        mac_entry = tk.Entry(config_window, width=35)
        mac_entry.insert(0, self.printer_address or "")
        mac_entry.pack(pady=5)
        
        tk.Label(config_window, text="Пример: 00:11:22:33:44:55").pack()
        
        tk.Label(config_window, text="Bluetooth канал (обычно 1):").pack(pady=5)
        channel_entry = tk.Entry(config_window, width=10)
        channel_entry.insert(0, str(self.printer_channel))
        channel_entry.pack(pady=5)
        
        def save_printer():
            mac = mac_entry.get().strip()
            try:
                channel = int(channel_entry.get())
                if mac:
                    self.printer_address = mac
                    self.printer_channel = channel
                    messagebox.showinfo("Успех", "Настройки принтера сохранены!")
                    config_window.destroy()
                else:
                    messagebox.showwarning("Ошибка", "Введите MAC-адрес принтера")
            except ValueError:
                messagebox.showwarning("Ошибка", "Неверный номер канала")
        
        tk.Button(config_window, text="Сохранить", command=save_printer,
                 bg="green", fg="white").pack(pady=20)
        
        tk.Button(config_window, text="Тестовая печать", 
                 command=lambda: self.test_print(mac_entry.get(), int(channel_entry.get() or 1)),
                 bg="orange", fg="white").pack(pady=5)
    
    def test_print(self, mac_address, channel):
        """Тестовая печать"""
        if not mac_address:
            messagebox.showwarning("Ошибка", "Введите MAC-адрес принтера")
            return
        
        test_receipt = """
        ================================
            ТЕСТОВАЯ ПЕЧАТЬ
        ================================
        Дата: {}
        Принтер: {}
        Если вы видите этот текст,
        значит принтер настроен правильно!
        ================================
        """.format(datetime.now().strftime('%d.%m.%Y %H:%M:%S'), mac_address)
        
        if self.print_to_bluetooth(mac_address, channel, test_receipt):
            messagebox.showinfo("Успех", "Тестовая печать выполнена!")
        else:
            messagebox.showerror("Ошибка", "Не удалось выполнить печать")
    
    def print_to_bluetooth(self, mac_address, channel, receipt_text):
        """Печать через Bluetooth сокет"""
        try:
            # Создаем сокет Bluetooth (только на Windows 10+)
            # Для Windows используем специальный подход
            import subprocess
            
            # Сохраняем чек во временный файл
            temp_file = f"temp_receipt_{int(time.time())}.txt"
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(receipt_text)
            
            # Используем команду copy для отправки на Bluetooth принтер
            # (требуется предварительное сопряжение принтера в Windows)
            result = subprocess.run(
                f'copy "{temp_file}" "\\\\.\\{mac_address}"',
                shell=True,
                capture_output=True,
                text=True
            )
            
            # Удаляем временный файл
            os.remove(temp_file)
            
            if result.returncode == 0:
                return True
            else:
                # Если не получилось, сохраняем в файл
                self.save_receipt_to_file(receipt_text)
                return False
                
        except Exception as e:
            print(f"Ошибка печати: {e}")
            self.save_receipt_to_file(receipt_text)
            return False
    
    def print_receipt(self, order):
        """Печать чека"""
        receipt_text = self.format_receipt(order)
        
        # Если принтер настроен
        if self.printer_address:
            return self.print_to_bluetooth(self.printer_address, self.printer_channel, receipt_text)
        else:
            # Если принтер не настроен, сохраняем в файл
            self.save_receipt_to_file(receipt_text)
            messagebox.showinfo("Информа", "Чек сохранен в файл. Настройте принтер в меню 'Настройка принтера'")
            return True
    
    def format_receipt(self, order):
        """Форматирование чека"""
        now = datetime.now()
        
        receipt = f"""
{'='*32}
        ЧЕК ЗАКАЗА
{'='*32}
Дата: {now.strftime('%d.%m.%Y %H:%M:%S')}
Заказ №: {order['order_num']}
Телефон: {order['phone']}
Статус: {order['status']}
{'='*32}
Спасибо за покупку!
{'='*32}
        """
        return receipt
    
    def save_receipt_to_file(self, receipt_text):
        """Сохранение чека в файл"""
        filename = f"receipt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(receipt_text)
        print(f"Чек сохранен в файл: {filename}")
    
    def open_add_order_window(self):
        """Окно добавления заказа"""
        add_window = tk.Toplevel(self.root)
        add_window.title("Добавление заказа")
        add_window.geometry("400x400")
        
        tk.Label(add_window, text="Номер телефона:").pack(pady=5)
        phone_entry = tk.Entry(add_window, width=40)
        phone_entry.pack(pady=5)
        
        tk.Label(add_window, text="Номер заказа:").pack(pady=5)
        order_entry = tk.Entry(add_window, width=40)
        order_entry.pack(pady=5)
        
        tk.Label(add_window, text="Статус:").pack(pady=5)
        status_var = tk.StringVar(value="принят")
        status_combo = ttk.Combobox(add_window, textvariable=status_var, 
                                    values=["принят", "сделан", "доставлен"], 
                                    state="readonly", width=37)
        status_combo.pack(pady=5)
        
        def add_order():
            phone = phone_entry.get().strip()
            order_num = order_entry.get().strip()
            status = status_var.get()
            
            if not phone or not order_num:
                messagebox.showwarning("Предупреждение", "Пожалуйста, заполните все поля!")
                return
            
            order_id = len(self.orders) + 1
            order = {
                'order_id': order_id,
                'phone': phone,
                'order_num': order_num,
                'status': status
            }
            self.orders.append(order)
            
            # Добавление в таблицу с кнопкой
            item_id = self.tree.insert('', tk.END, values=(
                order_id, phone, order_num, status, "Закрыть"
            ))
            
            order['tree_item_id'] = item_id
            self.create_close_button(item_id, order_id)
            
            add_window.destroy()
            messagebox.showinfo("Успех", "Заказ успешно добавлен!")
        
        tk.Button(add_window, text="Добавить", command=add_order, 
                 bg="green", fg="white").pack(pady=20)
    
    def create_close_button(self, item_id, order_id):
        """Создание кнопки закрытия"""
        bbox = self.tree.bbox(item_id, column='Действие')
        if bbox:
            btn = tk.Button(self.root, text="Закрыть", 
                           command=lambda: self.close_order(order_id),
                           bg="orange", fg="white", font=("Arial", 9))
            btn.place(x=bbox[0] + 5, y=bbox[1] + 2, width=bbox[2] - 10, height=bbox[3] - 4)
            
            if not hasattr(self, 'buttons'):
                self.buttons = {}
            self.buttons[item_id] = btn
    
    def close_order(self, order_id):
        """Закрытие заказа и печать чека"""
        order = None
        order_index = None
        for i, o in enumerate(self.orders):
            if o.get('order_id') == order_id:
                order = o
                order_index = i
                break
        
        if order:
            if self.print_receipt(order):
                if order_index is not None:
                    del self.orders[order_index]
                if 'tree_item_id' in order:
                    if order['tree_item_id'] in getattr(self, 'buttons', {}):
                        self.buttons[order['tree_item_id']].destroy()
                        del self.buttons[order['tree_item_id']]
                    self.tree.delete(order['tree_item_id'])
                messagebox.showinfo("Успех", f"Заказ #{order['order_num']} закрыт и чек отправлен на печать!")
            else:
                if messagebox.askyesno("Ошибка печати", "Закрыть заказ без печати?"):
                    if order_index is not None:
                        del self.orders[order_index]
                    if 'tree_item_id' in order:
                        if order['tree_item_id'] in getattr(self, 'buttons', {}):
                            self.buttons[order['tree_item_id']].destroy()
                            del self.buttons[order['tree_item_id']]
                        self.tree.delete(order['tree_item_id'])
                    messagebox.showinfo("Успех", f"Заказ #{order['order_num']} закрыт")
    
    def on_order_double_click(self, event):
        """Редактирование заказа по двойному клику"""
        selected_item = self.tree.selection()
        if not selected_item:
            return
        
        item = selected_item[0]
        values = self.tree.item(item, 'values')
        
        order_index = None
        for i, order in enumerate(self.orders):
            if order.get('order_id') == int(values[0]):
                order_index = i
                break
        
        if order_index is not None:
            self.open_edit_order_window(order_index, item)
    
    def open_edit_order_window(self, order_index, tree_item):
        """Окно редактирования заказа"""
        order = self.orders[order_index]
        
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Редактирование заказа")
        edit_window.geometry("400x450")
        
        tk.Label(edit_window, text="Номер телефона:").pack(pady=5)
        phone_entry = tk.Entry(edit_window, width=40)
        phone_entry.insert(0, order['phone'])
        phone_entry.pack(pady=5)
        
        tk.Label(edit_window, text="Номер заказа:").pack(pady=5)
        order_entry = tk.Entry(edit_window, width=40)
        order_entry.insert(0, order['order_num'])
        order_entry.pack(pady=5)
        
        tk.Label(edit_window, text="Статус:").pack(pady=5)
        status_var = tk.StringVar(value=order['status'])
        status_combo = ttk.Combobox(edit_window, textvariable=status_var, 
                                    values=["принят", "сделан", "доставлен"], 
                                    state="readonly", width=37)
        status_combo.pack(pady=5)
        
        def save_changes():
            new_phone = phone_entry.get().strip()
            new_order_num = order_entry.get().strip()
            new_status = status_var.get()
            
            if not new_phone or not new_order_num:
                messagebox.showwarning("Предупреждение", "Заполните все поля!")
                return
            
            self.orders[order_index].update({
                'phone': new_phone,
                'order_num': new_order_num,
                'status': new_status
            })
            
            self.tree.item(tree_item, values=(
                order['order_id'], new_phone, new_order_num, new_status, "Закрыть"
            ))
            
            edit_window.destroy()
            messagebox.showinfo("Успех", "Заказ обновлен!")
        
        def delete_order():
            if messagebox.askyesno("Подтверждение", "Удалить заказ?"):
                if tree_item in getattr(self, 'buttons', {}):
                    self.buttons[tree_item].destroy()
                    del self.buttons[tree_item]
                del self.orders[order_index]
                self.tree.delete(tree_item)
                edit_window.destroy()
                messagebox.showinfo("Успех", "Заказ удален!")
        
        tk.Button(edit_window, text="Сохранить", command=save_changes,
                 bg="blue", fg="white").pack(pady=10)
        tk.Button(edit_window, text="Удалить", command=delete_order,
                 bg="red", fg="white").pack(pady=5)

def main():
    root = tk.Tk()
    app = OrderApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()