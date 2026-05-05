import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import os
import platform
import subprocess
import shutil
import multiprocessing

class Windows99OS:
    def __init__(self, root):
        self.root = root
        self.show_boot_menu()

    def show_boot_menu(self):
        """Simulación del menú de arranque de Windows 10."""
        self.root.title("Windows Boot Manager")
        self.root.attributes('-fullscreen', True)
        self.boot_frame = tk.Frame(self.root, bg="#0078d7") # Azul Windows 10
        self.boot_frame.pack(fill="both", expand=True)

        # Título
        tk.Label(self.boot_frame, text="Choose an operating system", 
                 font=("Segoe UI Light", 24), bg="#0078d7", fg="white").pack(pady=(100, 20))

        # Opciones
        options_frame = tk.Frame(self.boot_frame, bg="#0078d7")
        options_frame.pack()

        self.create_boot_option(options_frame, "Windows 99 Professional", "System on partition C:", self.start_os_sequence)
        self.create_boot_option(options_frame, "Windows 10 Home (Host)", "Standard Windows Boot", self.root.quit)
        
        # Pie de página
        tk.Label(self.boot_frame, text="Change defaults or choose other options", 
                 font=("Segoe UI", 10), bg="#0078d7", fg="#aad1f0").pack(side="bottom", pady=40)

    def create_boot_option(self, parent, title, subtitle, command):
        btn = tk.Button(parent, bg="#1a8ad9", activebackground="#2b9be6", bd=0, 
                        command=command, cursor="hand2")
        btn.pack(pady=10, ipadx=100, ipady=10)
        
        lbl_title = tk.Label(btn, text=title, font=("Segoe UI", 14), bg="#1a8ad9", fg="white")
        lbl_title.pack(anchor="w", padx=10)
        lbl_sub = tk.Label(btn, text=subtitle, font=("Segoe UI", 9), bg="#1a8ad9", fg="#aad1f0")
        lbl_sub.pack(anchor="w", padx=10)
        
        # Hacer que los labels no bloqueen el clic del botón
        lbl_title.bind("<Button-1>", lambda e: command())
        lbl_sub.bind("<Button-1>", lambda e: command())

    def start_os_sequence(self):
        """Secuencia de carga antes de entrar al escritorio."""
        for widget in self.boot_frame.winfo_children():
            widget.destroy()
        
        # Logo de carga (Simulado)
        tk.Label(self.boot_frame, text="田", font=("Segoe MDL2 Assets", 80), 
                 bg="#0078d7", fg="white").place(relx=0.5, rely=0.4, anchor="center")
        
        spinner = tk.Label(self.boot_frame, text="Loading system files...", 
                          font=("Segoe UI", 12), bg="#0078d7", fg="white")
        spinner.place(relx=0.5, rely=0.6, anchor="center")

        # Esperar 2 segundos y arrancar el escritorio
        self.root.after(2000, self.setup_desktop)

    def setup_desktop(self):
        self.boot_frame.destroy()
        self.root.attributes('-fullscreen', False)
        self.root.geometry("1024x768")
        
        self.root.title("Windows 99 Professional")
        
        # Colores clásicos de Windows 9x
        self.bg_color = "#008080"  # Teal clásico
        self.taskbar_color = "#c0c0c0"
        self.btn_active = "#ffffff"
        self.btn_shadow = "#808080"
        
        self.root.configure(bg=self.bg_color)

        # Escritorio
        self.desktop = tk.Canvas(self.root, bg=self.bg_color, highlightthickness=0)
        self.desktop.pack(fill="both", expand=True)

        # Iconos del escritorio
        self.create_desktop_icon("My Computer", 20, 20, self.open_my_computer, "💻")
        self.create_desktop_icon("Internet Explorer", 20, 100, self.open_internet_explorer, "🌐")
        self.create_desktop_icon("File Explorer", 20, 180, self.open_file_explorer, "📁")
        self.create_desktop_icon("Network Setup", 20, 260, self.open_network_driver, "🔌")
        self.create_desktop_icon("APK System", 20, 340, self.open_apk_installer, "🤖")
        self.create_desktop_icon("Task Manager", 20, 420, self.open_task_manager, "📊")

        # Barra de tareas
        self.taskbar = tk.Frame(self.root, bg=self.taskbar_color, height=30, relief="raised", bd=2)
        self.taskbar.pack(side="bottom", fill="x")

        # Botón Inicio
        self.start_button = tk.Button(self.taskbar, text="Start", font=("MS Sans Serif", 8, "bold"),
                                    command=self.toggle_start_menu, relief="raised", bd=2)
        self.start_button.pack(side="left", padx=2, pady=2)

        # Reloj en la barra de tareas
        self.clock_frame = tk.Frame(self.taskbar, relief="sunken", bd=2, bg=self.taskbar_color)
        self.clock_frame.pack(side="right", padx=5, pady=2)
        self.clock_label = tk.Label(self.clock_frame, text="", bg=self.taskbar_color, font=("MS Sans Serif", 8))
        self.clock_label.pack(padx=5)
        
        # Menú de inicio (oculto al principio)
        self.start_menu = tk.Frame(self.root, bg=self.taskbar_color, relief="raised", bd=2)
        self.create_start_menu_items()
        
        self.update_clock()
        self.active_window = None

    def create_desktop_icon(self, text, x, y, command, icon_str="📄"):
        # Simulamos un icono con un Frame y un Label (sin imágenes externas)
        icon_frame = tk.Frame(self.desktop, bg=self.bg_color)
        
        icon_lbl = tk.Label(icon_frame, text=icon_str, font=("Segoe UI Emoji", 20), bg=self.bg_color, fg="white")
        icon_lbl.pack()
        
        label = tk.Label(icon_frame, text=text, fg="white", bg=self.bg_color, font=("MS Sans Serif", 8))
        label.pack()
        
        icon_frame.place(x=x, y=y)
        for widget in (icon_frame, icon_lbl, label):
            widget.bind("<Double-Button-1>", lambda e: command())

    def update_clock(self):
        now = datetime.now().strftime("%H:%M")
        self.clock_label.config(text=now)
        self.root.after(1000, self.update_clock)

    def toggle_start_menu(self):
        if self.start_menu.winfo_viewable():
            self.start_menu.place_forget()
        else:
            # Aparece justo arriba del botón inicio
            self.start_menu.place(x=0, y=self.root.winfo_height() - 230, width=150, height=200)
            self.start_menu.lift()

    def create_start_menu_items(self):
        items = [
            ("🌐 Internet Explorer", self.open_internet_explorer),
            ("📁 Windows Explorer", self.open_file_explorer),
            ("📊 Task Manager", self.open_task_manager),
            ("� Programs", None),
            ("📄 Documents", None),
            ("⚙️ Settings (Drivers)", self.open_network_driver),
            ("❓ Help", None),
            ("🏃 Run...", None),
            ("💻 Shutdown...", self.root.quit)
        ]
        for text, cmd in items:
            btn = tk.Button(self.start_menu, text=text, anchor="w", relief="flat", bg=self.taskbar_color, 
                          command=cmd if cmd else lambda t=text: print(f"Opening {t}"))
            btn.pack(fill="x")

    def create_window(self, title, content_func):
        # Ventana personalizada dentro del canvas
        win_frame = tk.Frame(self.desktop, bg=self.taskbar_color, relief="raised", bd=2)
        win_frame.place(x=150, y=100, width=400, height=300)

        # Barra de título
        title_bar = tk.Frame(win_frame, bg="#000080", height=20) # Azul marino clásico
        title_bar.pack(fill="x", side="top")
        
        title_label = tk.Label(title_bar, text=title, bg="#000080", fg="white", font=("MS Sans Serif", 8, "bold"))
        title_label.pack(side="left", padx=5)

        close_btn = tk.Button(title_bar, text="X", bg=self.taskbar_color, font=("MS Sans Serif", 7), 
                            command=win_frame.destroy, relief="raised", bd=1)
        close_btn.pack(side="right", padx=2, pady=2)

        # Área de contenido
        content_area = tk.Frame(win_frame, bg="white", relief="sunken", bd=2)
        content_area.pack(fill="both", expand=True, padx=2, pady=2)
        
        content_func(content_area)

        # Hacer la ventana arrastrable
        self.make_draggable(win_frame, title_bar)

    def make_draggable(self, window, handle):
        def start_move(event):
            window.x = event.x
            window.y = event.y
        def do_move(event):
            x = window.winfo_x() + event.x - window.x
            y = window.winfo_y() + event.y - window.y
            window.place(x=x, y=y)
        handle.bind("<Button-1>", start_move)
        handle.bind("<B1-Motion>", do_move)

    def open_my_computer(self):
        def content(area):
            tk.Label(area, text="C: (System)\n[|||||-----] 50% free", bg="white").pack(pady=20)
            tk.Label(area, text="A: (Floppy 3.5)", bg="white").pack()
        self.create_window("My Computer", content)

    def open_apk_installer(self):
        def content(area):
            area.configure(bg="black")
            log = tk.Text(area, bg="black", fg="#3DDC84", font=("Courier", 9), borderwidth=0)
            log.pack(fill="both", expand=True)
            log.insert("end", "C:\\> android_subsystem.exe --init\n")
            log.insert("end", "Loading VM kernel...\n")
            log.insert("end", "Waiting for ADB connection...\n\n")
            log.insert("end", "Drag an .apk file to install (SIMULATED)")
            
            btn_install = tk.Button(area, text="Install APK", command=lambda: messagebox.showinfo("ADB", "APK installed successfully!"))
            btn_install.pack(pady=5)
            
        self.create_window("APK Subsystem Console", content)

    def open_file_explorer(self):
        def content(area):
            frame = tk.Frame(area, bg="white")
            frame.pack(fill="both", expand=True)
            
            listbox = tk.Listbox(frame, bg="white", font=("MS Sans Serif", 9), borderwidth=0)
            listbox.pack(side="left", fill="both", expand=True)
            
            scrollbar = tk.Scrollbar(frame)
            scrollbar.pack(side="right", fill="y")
            
            listbox.config(yscrollcommand=scrollbar.set)
            scrollbar.config(command=listbox.yview)

            try:
                # Listar archivos reales del directorio actual
                files = os.listdir('.')
                for f in files:
                    prefix = "📁 " if os.path.isdir(f) else "📄 "
                    listbox.insert("end", f"{prefix} {f}")
            except Exception as e:
                listbox.insert("end", f"Error: {e}")
                
        self.create_window("Exploring - C:\\Windows99", content)

    def open_internet_explorer(self):
        def content(area):
            # Barra de herramientas
            tools = tk.Frame(area, bg=self.taskbar_color, bd=1, relief="raised")
            tools.pack(fill="x")
            
            tk.Button(tools, text="Complements", font=("MS Sans Serif", 7), 
                      command=lambda: messagebox.showinfo("IE Complements", "ActiveX: Enabled\nJava VM: v1.1.2")).pack(side="right")

            nav = tk.Frame(area, bg=self.taskbar_color)
            nav.pack(fill="x", pady=2)
            tk.Label(nav, text=" Address: ", bg=self.taskbar_color).pack(side="left")
            url_entry = tk.Entry(nav)
            url_entry.pack(side="left", fill="x", expand=True, padx=2)
            url_entry.insert(0, "http://www.google.com")

            browser = tk.Text(area, bg="white", font=("Times New Roman", 11), padx=10, pady=10)
            browser.pack(fill="both", expand=True)
            browser.insert("end", "Welcome to the World Wide Web!\n\nSearching for: Information...")
            
        self.create_window("Internet Explorer 4.0", content)

    def open_network_driver(self):
        def content(area):
            area.configure(bg="#f0f0f0")
            tk.Label(area, text="Network Hardware Wizard", font=("MS Sans Serif", 10, "bold"), bg="#f0f0f0").pack(pady=10)
            tk.Label(area, text="Adapter: Realtek RTL8139 Fast Ethernet\nDriver: Win99_NET.SYS v1.0\nStatus: Device working properly.", 
                     bg="#f0f0f0", justify="left").pack(padx=20)
            tk.Button(area, text="Update Driver", state="disabled").pack(pady=20)
        self.create_window("Device Manager - Network", content)

    def open_task_manager(self):
        def content(area):
            # Pestañas simuladas
            tabs = tk.Frame(area, bg=self.taskbar_color)
            tabs.pack(fill="x")
            tk.Button(tabs, text="Performance", relief="sunken", bd=1, font=("MS Sans Serif", 7)).pack(side="left")
            tk.Button(tabs, text="Processes", relief="raised", bd=1, font=("MS Sans Serif", 7)).pack(side="left")

            display = tk.Frame(area, bg="white", relief="sunken", bd=2)
            display.pack(fill="both", expand=True, padx=5, pady=5)

            # Obtener especificaciones reales
            try:
                # CPU
                cpu_name = platform.processor() or "Generic Processor"
                cores = multiprocessing.cpu_count()
                
                # RAM (Windows via WMIC)
                ram_gb = "Unknown"
                if platform.system() == "Windows":
                    out = subprocess.check_output(['wmic', 'computersystem', 'get', 'TotalPhysicalMemory']).decode()
                    ram_bytes = int(out.split()[1])
                    ram_gb = f"{round(ram_bytes / (1024**3), 2)} GB"

                # Disco
                total, used, free = shutil.disk_usage("/")
                disk_info = f"{round(total / (1024**3), 1)} GB"
                
                # OS Real
                os_real = f"{platform.system()} {platform.release()}"
            except:
                cpu_name, cores, ram_gb, disk_info, os_real = "Error", "?", "?", "?", "?"

            specs = [
                f"OS: {os_real}",
                f"CPU: {cpu_name}",
                f"Cores: {cores} logical processors",
                f"Memory: {ram_gb} RAM",
                f"System Disk: {disk_info} Total",
                "-"*30,
                "CPU Usage: [|||||-----] 45%",
                "MEM Usage: [||||-------] 32%"
            ]

            for line in specs:
                tk.Label(display, text=line, bg="white", font=("Courier", 9), anchor="w").pack(fill="x", padx=5)

        self.create_window("Windows Task Manager", content)

if __name__ == "__main__":
    root = tk.Tk()
    app = Windows99OS(root)
    root.mainloop()