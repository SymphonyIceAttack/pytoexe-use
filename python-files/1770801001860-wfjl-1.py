import tkinter as tk
from tkinter import ttk
import keyboard
import json
import os
import pyautogui
import threading

class FishingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Fishing Bot")
        self.root.geometry("400x350")
        self.root.resizable(False, False)
        
        self.running = False
        self.area_changed = False
        self.selector_window = None
        self.area_coords = None
        self.auto_buy_bait = False
        self.water_point = None
        self.button_side = None
        self.selecting = False
        self.button_coords = {}
        self.fishing_rod = None
        self.bait_slot = None
        self.common_item = None
        
        self.load_settings()
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1 - Main
        self.tab1 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab1, text="Principal")
        self.setup_tab1()
        
        # Tab 2 - Settings
        self.tab2 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab2, text="Configurações")
        self.setup_tab2()
        
        # Register hotkeys
        keyboard.add_hotkey('F1', self.toggle_start_stop)
        keyboard.add_hotkey('F5', self.toggle_area)
        keyboard.add_hotkey('F4', self.exit_app)
        
        # Register number hotkeys for fishing rod and reset
        for i in range(1, 10):
            keyboard.add_hotkey(str(i), lambda num=i: self.on_number_press(num))
    
    def setup_tab1(self):
        # Iniciar/Parar Button
        self.start_stop_btn = ttk.Button(
            self.tab1, 
            text="Iniciar/Parar (F1)", 
            command=self.toggle_start_stop
        )
        self.start_stop_btn.pack(pady=10)
        
        # Mudar Área Button
        self.area_btn = ttk.Button(
            self.tab1, 
            text="Mudar Área (F5)", 
            command=self.toggle_area
        )
        self.area_btn.pack(pady=10)
        
        # Sair Button
        self.exit_btn = ttk.Button(
            self.tab1, 
            text="Sair (F4)", 
            command=self.exit_app
        )
        self.exit_btn.pack(pady=10)
        
        # Status Label
        self.status_label = ttk.Label(self.tab1, text="Status: Parado", foreground="red")
        self.status_label.pack(pady=5)
    
    def setup_tab2(self):
        # Vara de Pesca
        vara_frame = ttk.LabelFrame(self.tab2, text="1. Vara de Pesca", padding=10)
        vara_frame.pack(pady=10, padx=10, fill=tk.X)
        
        ttk.Label(vara_frame, text="Selecione (1-9):").pack(side=tk.LEFT, padx=5)
        self.fishing_rod_var = tk.StringVar(value=str(self.fishing_rod) if self.fishing_rod else "")
        vara_spinbox = ttk.Spinbox(vara_frame, from_=1, to=9, textvariable=self.fishing_rod_var, width=5)
        vara_spinbox.pack(side=tk.LEFT, padx=5)
        ttk.Button(vara_frame, text="Confirmar", command=self.set_fishing_rod).pack(side=tk.LEFT, padx=5)
        
        # Status da Vara
        self.fishing_rod_status = ttk.Label(vara_frame, text="Nenhuma vara selecionada", foreground="gray")
        self.fishing_rod_status.pack(side=tk.LEFT, padx=20)
        
        # Selecionar ponto de água Button
        water_frame = ttk.LabelFrame(self.tab2, text="2. Ponto de Água", padding=10)
        water_frame.pack(pady=10, padx=10, fill=tk.X)
        
        self.water_btn = ttk.Button(
            water_frame, 
            text="Selecionar Ponto de Água", 
            command=self.start_water_selection
        )
        self.water_btn.pack(side=tk.LEFT, padx=5)
        
        # Water point status label
        self.water_status = ttk.Label(water_frame, text="Nenhum ponto selecionado", foreground="gray")
        self.water_status.pack(side=tk.LEFT, padx=20)
        
        # Auto comprar iscas Checkbox
        bait_frame = ttk.LabelFrame(self.tab2, text="3. Configuração de Iscas", padding=10)
        bait_frame.pack(pady=10, padx=10, fill=tk.X)
        
        self.auto_buy_var = tk.BooleanVar(value=self.auto_buy_bait)
        self.auto_buy_check = ttk.Checkbutton(
            bait_frame,
            text="Auto Comprar Iscas",
            variable=self.auto_buy_var,
            command=self.toggle_auto_buy
        )
        self.auto_buy_check.pack(pady=5)
        
        # Slot de Isca
        slot_frame = ttk.Frame(bait_frame)
        slot_frame.pack(pady=5)
        ttk.Label(slot_frame, text="Slot de Isca (1-9):").pack(side=tk.LEFT, padx=5)
        self.bait_slot_var = tk.StringVar(value=str(self.bait_slot) if self.bait_slot else "")
        bait_spinbox = ttk.Spinbox(slot_frame, from_=1, to=9, textvariable=self.bait_slot_var, width=5)
        bait_spinbox.pack(side=tk.LEFT, padx=5)
        ttk.Button(slot_frame, text="Confirmar", command=self.set_bait_slot).pack(side=tk.LEFT, padx=5)
        
        # Frame para os botões de lado (inicialmente vazio)
        self.button_frame = ttk.Frame(bait_frame)
        self.button_frame.pack(pady=10)
        
        self.update_button_sides()
        
        # Item Comum
        common_frame = ttk.LabelFrame(self.tab2, text="4. Item Comum (Reset)", padding=10)
        common_frame.pack(pady=10, padx=10, fill=tk.X)
        
        ttk.Label(common_frame, text="Selecione (1-9):").pack(side=tk.LEFT, padx=5)
        self.common_item_var = tk.StringVar(value=str(self.common_item) if self.common_item else "")
        common_spinbox = ttk.Spinbox(common_frame, from_=1, to=9, textvariable=self.common_item_var, width=5)
        common_spinbox.pack(side=tk.LEFT, padx=5)
        ttk.Button(common_frame, text="Confirmar", command=self.set_common_item).pack(side=tk.LEFT, padx=5)
        
        # Status do Item Comum
        self.common_item_status = ttk.Label(common_frame, text="Nenhum item comum selecionado", foreground="gray")
        self.common_item_status.pack(side=tk.LEFT, padx=20)
    
    def set_fishing_rod(self):
        try:
            self.fishing_rod = int(self.fishing_rod_var.get())
            self.fishing_rod_status.config(text=f"Vara: {self.fishing_rod}", foreground="green")
            print(f"Vara de Pesca: {self.fishing_rod}")
            self.save_settings()
        except ValueError:
            print("Valor inválido para Vara de Pesca")
    
    def set_bait_slot(self):
        try:
            self.bait_slot = int(self.bait_slot_var.get())
            print(f"Slot de Isca: {self.bait_slot}")
            self.save_settings()
        except ValueError:
            print("Valor inválido para Slot de Isca")
    
    def set_common_item(self):
        try:
            self.common_item = int(self.common_item_var.get())
            self.common_item_status.config(text=f"Item: {self.common_item}", foreground="green")
            print(f"Item Comum: {self.common_item}")
            self.save_settings()
        except ValueError:
            print("Valor inválido para Item Comum")
    
    def on_number_press(self, number):
        if self.fishing_rod and number == self.fishing_rod:
            print(f"Tecla {number} pressionada - Selecionando Vara de Pesca {self.fishing_rod}")
            pyautogui.press(str(self.fishing_rod))
        
        if self.common_item and number == self.common_item:
            print(f"Tecla {number} pressionada - Resetando Pesca com Item Comum {self.common_item}")
            pyautogui.press(str(self.common_item))
    
    def toggle_auto_buy(self):
        self.auto_buy_bait = self.auto_buy_var.get()
        print(f"Auto Comprar Iscas: {'Ativado' if self.auto_buy_bait else 'Desativado'}")
        self.update_button_sides()
        self.save_settings()
    
    def update_button_sides(self):
        # Limpar frame anterior
        for widget in self.button_frame.winfo_children():
            widget.destroy()
        
        if self.auto_buy_bait:
            ttk.Label(self.button_frame, text="Selecione o botão de compra:").pack(pady=5)
            
            btn_frame = ttk.Frame(self.button_frame)
            btn_frame.pack()
            
            ttk.Button(
                btn_frame,
                text="Esquerda",
                command=lambda: self.start_button_selection("Esquerda")
            ).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(
                btn_frame,
                text="Meio",
                command=lambda: self.start_button_selection("Meio")
            ).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(
                btn_frame,
                text="Direita",
                command=lambda: self.start_button_selection("Direita")
            ).pack(side=tk.LEFT, padx=5)
            
            # Status label
            side_text = f"Botão: {self.button_side}" if self.button_side else "Nenhum botão selecionado"
            self.button_status = ttk.Label(self.button_frame, text=side_text, foreground="blue")
            self.button_status.pack(pady=5)
    
    def start_water_selection(self):
        if not self.fishing_rod:
            print("Erro: Primeiro selecione a Vara de Pesca!")
            return
        
        self.selecting = "water"
        self.root.withdraw()
        self.create_overlay()
        print("Clique no ponto de água desejado... (ESC para cancelar)")
        threading.Thread(target=self.wait_for_click, daemon=True).start()
    
    def start_button_selection(self, side):
        self.selecting = side
        self.root.withdraw()
        self.create_overlay()
        print(f"Clique no botão {side}... (ESC para cancelar)")
        threading.Thread(target=self.wait_for_click, daemon=True).start()
    
    def create_overlay(self):
        # Criar overlay transparente vermelho em toda a tela sem bordas
        self.overlay = tk.Toplevel(self.root)
        self.overlay.attributes('-alpha', 0.3)
        self.overlay.attributes('-topmost', True)
        self.overlay.overrideredirect(True)
        self.overlay.configure(bg='red')
        
        # Pegar tamanho da tela
        screen_width = self.overlay.winfo_screenwidth()
        screen_height = self.overlay.winfo_screenheight()
        
        self.overlay.geometry(f'{screen_width}x{screen_height}+0+0')
        
        # Label com instruções
        label = tk.Label(
            self.overlay,
            text="Clique no local desejado\n(ESC para cancelar)",
            bg='red',
            fg='white',
            font=('Arial', 16, 'bold')
        )
        label.pack(expand=True)
        
        # Bind para clique do mouse
        self.overlay.bind('<Button-1>', self.on_overlay_click)
        self.overlay.bind('<Escape>', lambda e: self.finish_selection())
    
    def on_overlay_click(self, event):
        x = self.overlay.winfo_pointerx()
        y = self.overlay.winfo_pointery()
        
        if self.selecting == "water":
            self.water_point = [x, y]
            if hasattr(self, 'water_status'):
                self.water_status.config(text=f"X={x}, Y={y}", foreground="green")
            print(f"Ponto de água selecionado: X={x}, Y={y}")
        else:
            # É um botão
            side_data = {
                "Esquerda": "left_button",
                "Meio": "middle_button",
                "Direita": "right_button"
            }
            
            button_key = side_data[self.selecting]
            self.button_coords[button_key] = [x, y]
            if hasattr(self, 'button_status'):
                self.button_status.config(text=f"Botão {self.selecting}: X={x}, Y={y}")
            print(f"Botão {self.selecting} selecionado: X={x}, Y={y}")
        
        self.save_settings()
        self.finish_selection()
    
    def wait_for_click(self):
        while self.selecting:
            keyboard.wait()
    
    def finish_selection(self):
        self.selecting = False
        if hasattr(self, 'overlay'):
            self.overlay.destroy()
        self.root.deiconify()
    
    def load_settings(self):
        if os.path.exists('Gfish.json'):
            with open('Gfish.json', 'r') as f:
                settings = json.load(f)
                self.area_coords = settings.get('area_coords', None)
                self.auto_buy_bait = settings.get('auto_buy_bait', False)
                self.button_side = settings.get('button_side', None)
                self.water_point = settings.get('water_point', None)
                self.button_coords = settings.get('button_coords', {})
                self.fishing_rod = settings.get('fishing_rod', None)
                self.bait_slot = settings.get('bait_slot', None)
                self.common_item = settings.get('common_item', None)
    
    def save_settings(self):
        settings = {
            'area_coords': self.area_coords,
            'auto_buy_bait': self.auto_buy_bait,
            'button_side': self.button_side,
            'water_point': self.water_point,
            'button_coords': self.button_coords,
            'fishing_rod': self.fishing_rod,
            'bait_slot': self.bait_slot,
            'common_item': self.common_item
        }
        with open('Gfish.json', 'w') as f:
            json.dump(settings, f, indent=4)
    
    def toggle_start_stop(self):
        self.running = not self.running
        status_text = "Status: Rodando" if self.running else "Status: Parado"
        status_color = "green" if self.running else "red"
        self.status_label.config(text=status_text, foreground=status_color)
        print(f"Iniciar/Parar: {status_text}")
    
    def toggle_area(self):
        if not self.area_changed:
            self.area_changed = True
            self.open_selector()
        else:
            self.area_changed = False
            if self.selector_window:
                self.selector_window.destroy()
                self.selector_window = None
    
    def open_selector(self):
        self.selector_window = tk.Toplevel(self.root)
        self.selector_window.attributes('-topmost', True)
        self.selector_window.title("Seletor de Área")
        self.selector_window.attributes('-alpha', 0.5)
        self.selector_window.configure(bg='red')
        
        if self.area_coords:
            x, y, w, h = self.area_coords
            self.selector_window.geometry(f"{w}x{h}+{x}+{y}")
        else:
            self.selector_window.geometry("300x300+100+100")
        
        canvas = tk.Canvas(self.selector_window, bg='red', highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        
        label = tk.Label(
            self.selector_window, 
            text="Redimensione a janela\nPressione F5 novamente para salvar", 
            bg='red', 
            fg='white',
            font=('Arial', 10)
        )
        label.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        
        self.selector_window.bind('<Configure>', lambda e: self.on_selector_configure())
    
    def on_selector_configure(self):
        if self.selector_window:
            x = self.selector_window.winfo_x()
            y = self.selector_window.winfo_y()
            w = self.selector_window.winfo_width()
            h = self.selector_window.winfo_height()
            self.area_coords = [x, y, w, h]
            self.save_settings()
    
    def exit_app(self):
        if self.selector_window:
            self.selector_window.destroy()
        if hasattr(self, 'overlay'):
            self.overlay.destroy()
        print("Aplicação fechando...")
        self.root.quit()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    gui = FishingGUI(root)
    root.mainloop()