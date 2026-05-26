import tkinter as tk
from tkinter import messagebox
import serial
import serial.tools.list_ports
import time

class PrecisionStepperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Оптический калибратор вала")
        self.ser = None

        # --- Блок подключения ---
        conn_frame = tk.LabelFrame(root, text="Связь")
        conn_frame.pack(fill="x", padx=10, pady=5)
        
        self.port_var = tk.StringVar()
        ports = [p.device for p in serial.tools.list_ports.comports()]
        
        if ports:
            self.port_var.set(ports[0])
            
        tk.OptionMenu(conn_frame, self.port_var, *(ports if ports else ["No Ports"])).pack(side="left", padx=5)
        tk.Button(conn_frame, text="Подключить", command=self.connect).pack(side="left", padx=5)

        # --- Блок калибровки ---
        calib_frame = tk.LabelFrame(root, text="Настройки калибровки")
        calib_frame.pack(fill="x", padx=10, pady=5)

        # Сколько единиц счетчика дает 32 шага (1 оборот мотора до редуктора)
        tk.Label(calib_frame, text="Изменение счетчика за 32 шага:").grid(row=0, column=0, sticky="w")
        self.val_per_32 = tk.Entry(calib_frame)
        self.val_per_32.insert(0, "1.0")
        self.val_per_32.grid(row=0, column=1)

        tk.Label(calib_frame, text="Скорость (1-15):").grid(row=1, column=0, sticky="w")
        self.speed_entry = tk.Entry(calib_frame)
        self.speed_entry.insert(0, "12")
        self.speed_entry.grid(row=1, column=1)

        # --- Блок позиционирования ---
        pos_frame = tk.LabelFrame(root, text="Управление позицией")
        pos_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(pos_frame, text="Текущее значение:").grid(row=0, column=0)
        self.curr_val = tk.Entry(pos_frame)
        self.curr_val.insert(0, "0.0")
        self.curr_val.grid(row=0, column=1)

        tk.Label(pos_frame, text="Целевое значение:").grid(row=1, column=0)
        self.target_val = tk.Entry(pos_frame)
        self.target_val.insert(0, "10.0")
        self.target_val.grid(row=1, column=1)

        tk.Button(root, text="ВЫПОЛНИТЬ ПЕРЕМЕЩЕНИЕ", bg="green", fg="white", 
                  command=self.calculate_and_move, font=('Arial', 10, 'bold')).pack(pady=10)

    def connect(self):
        try:
            self.ser = serial.Serial(self.port_var.get(), 9600, timeout=1)
            time.sleep(2)
            messagebox.showinfo("OK", "Arduino готова")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def calculate_and_move(self):
        if not self.ser:
            messagebox.showwarning("!", "Нет связи")
            return

        try:
            delta_val = float(self.val_per_32.get())
            current = float(self.curr_val.get())
            target = float(self.target_val.get())
            speed = int(self.speed_entry.get())

            # --- МАТЕМАТИКА КАЛИБРОВКИ ---
            steps_to_go = int((target - current) * 32 / delta_val)

            # Отправка скорости
            self.ser.write(f"S{speed}\n".encode())
            time.sleep(0.1)
            
            # Отправка шагов
            self.ser.write(f"M{steps_to_go}\n".encode())

            # Ждем подтверждения
            response = self.ser.readline().decode().strip()
            if response == "OK":
                self.curr_val.delete(0, tk.END)
                self.curr_val.insert(0, str(target))
                messagebox.showinfo("Готово", f"Пройдено {steps_to_go} шагов")

        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректные числа")

if __name__ == "__main__":
    root = tk.Tk()
    app = PrecisionStepperApp(root)
    root.mainloop()