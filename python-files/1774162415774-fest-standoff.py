import tkinter as tk
from tkinter import ttk, messagebox
import pymem
import pymem.process
import psutil
import threading
import time

# --- ---
OFFSETS = {
    'PlayerManager': 135621384,      #
    'LocalPlayer': 0x70,             
    'Weaponry': 0x88,                
    'WeaponController': 0xA0,        
    'Ammo': 0x110,                   
    'SkinID': 0x18                   
}

class OverlordStable:
    def __init__(self, root):
        self.root = root
        self.root.title("OVERLORD STABLE")
        self.root.geometry("400x500")
        self.root.configure(bg="#0f0f0f")
        
        self.pm = None
        self.base = None
        self.is_running = False
        
        self.inf_ammo = tk.BooleanVar()
        self.skinchanger = tk.BooleanVar()
        self.setup_ui()

    def setup_ui(self):
        tk.Label(self.root, text="OVERLORD", font=("Impact", 30), fg="red", bg="#0f0f0f").pack(pady=10)
        
        self.proc_list = ttk.Combobox(self.root, state="readonly", font=("Arial", 10))
        self.proc_list.pack(padx=20, pady=10, fill="x")
        
        tk.Button(self.root, text="ОБНОВИТЬ СПИСОК", command=self.refresh).pack(pady=5)
        tk.Button(self.root, text="ЗАИНЖЕКТИТЬ", command=self.connect, bg="red", fg="white").pack(pady=5)
        
        # Функции
        frame = tk.LabelFrame(self.root, text=" Настройки ", bg="#0f0f0f", fg="white")
        frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        tk.Checkbutton(frame, text="Бесконечные патроны", variable=self.inf_ammo, bg="#0f0f0f", fg="red", selectcolor="black").pack(anchor="w", padx=10)
        tk.Checkbutton(frame, text="Скинчейнджер", variable=self.skinchanger, bg="#0f0f0f", fg="red", selectcolor="black").pack(anchor="w", padx=10)
        
        tk.Label(frame, text="ID Скина:", bg="#0f0f0f", fg="white").pack(side="left", padx=10)
        self.skin_entry = tk.Entry(frame, width=10)
        self.skin_entry.insert(0, "150")
        self.skin_entry.pack(side="left")

    def refresh(self):
        procs = [f"{p.info['name']} | PID: {p.info['pid']}" for p in psutil.process_iter(['pid', 'name']) if "HD-Player" in p.info['name'] or "BlueStacks" in p.info['name']]
        self.proc_list['values'] = procs

    def connect(self):
        try:
            selection = self.proc_list.get()
            pid = int(selection.split("PID: ")[1])
            self.pm = pymem.Pymem()
            self.pm.open_process_from_id(pid)
            
            #
            module = pymem.process.module_from_name(self.pm.process_handle, "libil2cpp.so")
            self.base = module.lpBaseOfDll
            self.is_running = True
            threading.Thread(target=self.work, daemon=True).start()
            messagebox.showinfo("OK", "Успешное подключение!")
        except Exception as e:
            messagebox.showerror("Error", f"Запусти от имени АДМИНИСТРАТОРА!\n{e}")

    def work(self):
        while self.is_running:
            try:
                # Читаем цепочку аккуратно
                p_mgr_ptr = self.pm.read_long(self.base + OFFSETS['PlayerManager'])
                static_fields = self.pm.read_long(p_mgr_ptr + 0x58)
                instance = self.pm.read_long(static_fields + 0xB8)
                local_player = self.pm.read_long(instance + OFFSETS['LocalPlayer'])
                
                if local_player:
                    weaponry = self.pm.read_long(local_player + OFFSETS['Weaponry'])
                    w_controller = self.pm.read_long(weaponry + OFFSETS['WeaponController'])
                    
                    if self.inf_ammo.get():
                        self.pm.write_int(w_controller + OFFSETS['Ammo'], 999)
                        
                    if self.skinchanger.get():
                        w_params = self.pm.read_long(w_controller + 0xA0)
                        self.pm.write_int(w_params + OFFSETS['SkinID'], int(self.skin_entry.get()))
            except:
                # Если адрес временно недоступен — просто ждем следующего цикла
                pass
            time.sleep(0.2)

if __name__ == "__main__":
    root = tk.Tk()
    OverlordStable(root)
    root.mainloop()
