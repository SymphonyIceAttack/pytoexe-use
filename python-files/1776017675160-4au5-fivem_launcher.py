import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json
import subprocess
from pathlib import Path

class FiveMLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("FiveM Auto Citizen Launcher")
        self.root.geometry("900x600")
        
        # Configuración por defecto
        self.config_file = "launcher_config.json"
        self.load_config()
        
        # Variables
        self.citizen_path = tk.StringVar(value=self.config.get("citizen_path", ""))
        self.mods_path = tk.StringVar(value=self.config.get("mods_path", ""))
        self.background_image = None
        self.bg_label = None
        
        # Crear interfaz
        self.setup_ui()
        self.load_background()
        
    def setup_ui(self):
        # Frame principal con scroll
        self.canvas = tk.Canvas(self.root)
        self.scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Estilo
        style = ttk.Style()
        style.theme_use('clam')
        
        # Título
        title_frame = ttk.Frame(self.scrollable_frame)
        title_frame.pack(fill="x", padx=20, pady=10)
        
        title_label = ttk.Label(title_frame, text="🚗 FiveM Auto Citizen Launcher", 
                                font=("Arial", 20, "bold"))
        title_label.pack()
        
        # Frame para fondo
        self.bg_frame = ttk.Frame(self.scrollable_frame)
        self.bg_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Botón para cambiar fondo
        bg_button_frame = ttk.Frame(self.scrollable_frame)
        bg_button_frame.pack(fill="x", padx=20, pady=5)
        
        ttk.Button(bg_button_frame, text="🖼️ Cambiar Foto de Fondo", 
                  command=self.change_background).pack()
        
        # Frame para configuración de ciudadano
        citizen_frame = ttk.LabelFrame(self.scrollable_frame, text="📁 Importar Citizen", 
                                      padding=10)
        citizen_frame.pack(fill="x", padx=20, pady=10)
        
        ttk.Label(citizen_frame, text="Ruta del Citizen:").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(citizen_frame, textvariable=self.citizen_path, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(citizen_frame, text="Buscar", command=lambda: self.select_folder("citizen")).grid(row=0, column=2)
        
        # Frame para mods
        mods_frame = ttk.LabelFrame(self.scrollable_frame, text="📦 Importar Mods (Opcional)", 
                                   padding=10)
        mods_frame.pack(fill="x", padx=20, pady=10)
        
        ttk.Label(mods_frame, text="Ruta de Mods:").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(mods_frame, textvariable=self.mods_path, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(mods_frame, text="Buscar", command=lambda: self.select_folder("mods")).grid(row=0, column=2)
        
        # Botones de acción
        actions_frame = ttk.Frame(self.scrollable_frame)
        actions_frame.pack(fill="x", padx=20, pady=10)
        
        ttk.Button(actions_frame, text="✅ Cambiar Citizen y Abrir FiveM", 
                  command=self.change_and_launch, style="Accent.TButton").pack(fill="x", pady=5)
        
        # Buscar más citizens
        search_frame = ttk.LabelFrame(self.scrollable_frame, text="🔍 Buscar más Citizens", 
                                     padding=10)
        search_frame.pack(fill="x", padx=20, pady=10)
        
        self.search_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.search_var, width=50).pack(fill="x", pady=5)
        ttk.Button(search_frame, text="Buscar Citizens", command=self.search_citizens).pack(pady=5)
        
        self.search_results = tk.Listbox(search_frame, height=5)
        self.search_results.pack(fill="x", pady=5)
        
        ttk.Button(search_frame, text="Seleccionar Citizen de la lista", 
                  command=self.select_from_list).pack(pady=5)
        
        # Pack canvas y scrollbar
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
    def load_background(self):
        """Cargar imagen de fondo guardada"""
        bg_path = self.config.get("background_path", "")
        if bg_path and os.path.exists(bg_path):
            self.set_background(bg_path)
            
    def set_background(self, image_path):
        """Establecer imagen de fondo"""
        try:
            from PIL import Image, ImageTk
            
            # Cargar y redimensionar imagen
            img = Image.open(image_path)
            
            # Obtener tamaño de la ventana
            window_width = self.root.winfo_width() if self.root.winfo_width() > 1 else 900
            window_height = self.root.winfo_height() if self.root.winfo_height() > 1 else 600
            
            # Redimensionar manteniendo aspect ratio
            img_ratio = img.width / img.height
            window_ratio = window_width / window_height
            
            if window_ratio > img_ratio:
                new_height = window_height
                new_width = int(new_height * img_ratio)
            else:
                new_width = window_width
                new_height = int(new_width / img_ratio)
            
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Crear imagen para tkinter
            self.background_image = ImageTk.PhotoImage(img)
            
            # Si ya hay un label, destruirlo
            if self.bg_label:
                self.bg_label.destroy()
            
            # Crear nuevo label con la imagen
            self.bg_label = tk.Label(self.scrollable_frame, image=self.background_image)
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            
            # Mover el label al fondo
            self.bg_label.lower()
            
            # Guardar en configuración
            self.config["background_path"] = image_path
            self.save_config()
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la imagen: {str(e)}")
    
    def change_background(self):
        """Cambiar imagen de fondo"""
        file_path = filedialog.askopenfilename(
            title="Seleccionar imagen de fondo",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.gif *.bmp"), 
                      ("Todos los archivos", "*.*")]
        )
        if file_path:
            self.set_background(file_path)
    
    def select_folder(self, folder_type):
        """Seleccionar carpeta para Citizen o Mods"""
        folder_path = filedialog.askdirectory(title=f"Seleccionar carpeta de {folder_type}")
        if folder_path:
            if folder_type == "citizen":
                self.citizen_path.set(folder_path)
                self.config["citizen_path"] = folder_path
            else:
                self.mods_path.set(folder_path)
                self.config["mods_path"] = folder_path
            self.save_config()
    
    def find_fivem_path(self):
        """Encontrar la ruta de FiveM"""
        possible_paths = [
            "C:\\Users\\" + os.getlogin() + "\\AppData\\Local\\FiveM\\FiveM.exe",
            "C:\\Program Files\\FiveM\\FiveM.exe",
            "C:\\Program Files (x86)\\FiveM\\FiveM.exe"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None
    
    def find_citizen_folder(self):
        """Encontrar la carpeta Citizen de FiveM"""
        appdata = os.path.expanduser("~\\AppData\\Local\\FiveM\\FiveM.app\\citizen")
        return appdata if os.path.exists(appdata) else None
    
    def change_and_launch(self):
        """Cambiar el Citizen y lanzar FiveM"""
        if not self.citizen_path.get():
            messagebox.showwarning("Advertencia", "Por favor selecciona una carpeta Citizen")
            return
        
        try:
            # Encontrar carpeta Citizen de FiveM
            citizen_dest = self.find_citizen_folder()
            
            if not citizen_dest:
                # Crear directorio si no existe
                citizen_dest = os.path.expanduser("~\\AppData\\Local\\FiveM\\FiveM.app\\citizen")
                os.makedirs(citizen_dest, exist_ok=True)
            
            # Copiar carpeta Citizen
            if os.path.exists(citizen_dest):
                # Hacer backup del citizen original
                backup_path = citizen_dest + "_backup"
                if not os.path.exists(backup_path):
                    shutil.copytree(citizen_dest, backup_path)
                
                # Eliminar citizen actual
                shutil.rmtree(citizen_dest)
            
            # Copiar nuevo citizen
            shutil.copytree(self.citizen_path.get(), citizen_dest)
            
            # Copiar mods si existen
            if self.mods_path.get() and os.path.exists(self.mods_path.get()):
                mods_dest = os.path.expanduser("~\\AppData\\Local\\FiveM\\FiveM.app\\mods")
                if os.path.exists(mods_dest):
                    shutil.rmtree(mods_dest)
                shutil.copytree(self.mods_path.get(), mods_dest)
            
            # Lanzar FiveM
            fivem_path = self.find_fivem_path()
            if fivem_path and os.path.exists(fivem_path):
                subprocess.Popen([fivem_path])
                messagebox.showinfo("Éxito", "Citizen cambiado exitosamente y FiveM lanzado")
            else:
                messagebox.showwarning("Advertencia", "Citizen cambiado pero no se encontró FiveM.exe")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al cambiar Citizen: {str(e)}")
    
    def search_citizens(self):
        """Buscar carpetas Citizen en el sistema"""
        search_term = self.search_var.get().lower()
        if not search_term:
            messagebox.showwarning("Advertencia", "Ingresa un término de búsqueda")
            return
        
        self.search_results.delete(0, tk.END)
        
        # Buscar en carpetas comunes
        search_paths = [
            "C:\\",
            os.path.expanduser("~\\Desktop"),
            os.path.expanduser("~\\Downloads"),
            os.path.expanduser("~\\Documents")
        ]
        
        found_folders = []
        
        for search_path in search_paths:
            if os.path.exists(search_path):
                for root, dirs, files in os.walk(search_path):
                    for dir_name in dirs:
                        if search_term in dir_name.lower():
                            full_path = os.path.join(root, dir_name)
                            # Verificar si parece ser una carpeta Citizen válida
                            if os.path.exists(os.path.join(full_path, "game")):
                                found_folders.append(full_path)
                            break  # No buscar más profundo en esta carpeta
        
        for folder in found_folders[:10]:  # Limitar a 10 resultados
            self.search_results.insert(tk.END, folder)
        
        if not found_folders:
            self.search_results.insert(tk.END, "No se encontraron resultados")
    
    def select_from_list(self):
        """Seleccionar citizen de la lista"""
        selection = self.search_results.curselection()
        if selection:
            selected_path = self.search_results.get(selection[0])
            if selected_path != "No se encontraron resultados":
                self.citizen_path.set(selected_path)
                self.config["citizen_path"] = selected_path
                self.save_config()
                messagebox.showinfo("Éxito", f"Citizen seleccionado: {selected_path}")
    
    def load_config(self):
        """Cargar configuración guardada"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            except:
                self.config = {}
        else:
            self.config = {}
    
    def save_config(self):
        """Guardar configuración"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

def main():
    root = tk.Tk()
    app = FiveMLauncher(root)
    root.mainloop()

if __name__ == "__main__":
    main()