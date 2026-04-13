import os
import sys
import shutil
import subprocess
import threading
import tempfile
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk

# ------------------------------------------------------------
# CONFIGURATIE
# ------------------------------------------------------------
USE_ONEFILE = False
DEBUG_CONSOLE = False
FORCE_TCL_TK_PATHS = True


def resource_path(relative_path):
    """Juiste paden voor PyInstaller (onefile of onedir)"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


LAUNCHER_TEMPLATE = '''import subprocess
import sys
import os
import traceback
import tempfile
import time
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk


def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def log_error(msg):
    try:
        log_path = os.path.join(tempfile.gettempdir(), "launcher_error.log")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{time.ctime()}: {msg}\\n")
    except:
        pass


def show_error(message):
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("ExeMaker Launcher", message)
    root.destroy()


def launch_target(target_filename):
    CREATE_NO_WINDOW = 0x08000000
    launcher_dir = os.path.dirname(sys.executable)
    target_path = os.path.join(launcher_dir, target_filename)
  
    if not os.path.exists(target_path):
        log_error(f"Doel EXE niet gevonden: {target_path}")
        show_error(f"Kan doelprogramma niet starten.\\nBestand niet gevonden:\\n{target_filename}")
        return False
  
    try:
        if sys.platform == 'win32':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0
            subprocess.Popen(
                [target_path],
                shell=False,
                creationflags=CREATE_NO_WINDOW,
                cwd=os.path.dirname(target_path),
                startupinfo=startupinfo
            )
        else:
            subprocess.Popen([target_path], shell=False, cwd=os.path.dirname(target_path))
        return True
    except Exception as e:
        log_error(f"Fout bij starten: {str(e)}\\n{traceback.format_exc()}")
        show_error(f"Kan doelprogramma niet starten.\\nFout: {str(e)}")
        return False


def show_splash_and_launch(target_filename, icon_filename):
    # Resource preload voor PyInstaller
    resource_path("splash.png")
    if icon_filename:
        resource_path(icon_filename)
   
    root = None
    try:
        root = tk.Tk()
        root.overrideredirect(True)
        
        # Eigen icoon op het venster (splash) en taakbalk
        if icon_filename:
            icon_path = resource_path(icon_filename)
            if os.path.exists(icon_path):
                try:
                    root.iconbitmap(icon_path)
                except:
                    pass
        
        splash_path = resource_path("splash.png")
        if os.path.exists(splash_path):
            img = Image.open(splash_path)
            width, height = img.size
            sw = root.winfo_screenwidth()
            sh = root.winfo_screenheight()
            x = (sw - width) // 2
            y = (sh - height) // 2
            root.geometry(f"{width}x{height}+{x}+{y}")
            
            photo = ImageTk.PhotoImage(img)
            label = tk.Label(root, image=photo)
            label.pack()
            root.update()
            
            start_time = time.time()
            while time.time() - start_time < 1.5:
                root.update()
                time.sleep(0.05)
            
            root.destroy()
            launch_target(target_filename)
        else:
            root.destroy()
            launch_target(target_filename)
    except Exception as e:
        log_error(f"Fout in splash/launch: {traceback.format_exc()}")
        if root:
            root.destroy()
        launch_target(target_filename)


if __name__ == "__main__":
    target_filename = r"{{TARGET_EXE_FILENAME}}"
    icon_filename = r"{{ICON_FILENAME}}"
    show_splash_and_launch(target_filename, icon_filename)
'''


class ModernTheme:
    @staticmethod
    def apply(style):
        style.theme_use('clam')
        style.configure('.', background='#1e1e2f', foreground='#ffffff', fieldbackground='#2d2d3a')
        style.configure('TLabel', background='#1e1e2f', foreground='#ffffff', font=('Segoe UI', 10))
        style.configure('TFrame', background='#1e1e2f')
        style.configure('TLabelframe', background='#1e1e2f', foreground='#ffffff', bordercolor='#3a3a4a')
        style.configure('TLabelframe.Label', background='#1e1e2f', foreground='#ffffff')
        style.configure('TButton', background='#2d2d3a', foreground='#ffffff', borderwidth=0, focusthickness=0, padding=6, font=('Segoe UI', 9))
        style.map('TButton', background=[('active', '#4a4a5a'), ('pressed', '#1e6f9f')])
        style.configure('Accent.TButton', background='#1e6f9f', foreground='white', font=('Segoe UI', 10, 'bold'))
        style.map('Accent.TButton', background=[('active', '#2a8bcf')])
        style.configure('TEntry', fieldbackground='#2d2d3a', foreground='#ffffff', borderwidth=1, focuscolor='#1e6f9f')
        style.configure('TProgressbar', background='#1e6f9f', troughcolor='#2d2d3a')
        style.configure('TCheckbutton', background='#1e1e2f', foreground='#ffffff')
        style.configure('TCombobox', fieldbackground='#2d2d3a', foreground='#ffffff', arrowcolor='white')


class SplashScreen:
    def __init__(self, parent, image_path, timeout=2000):
        self.parent = parent
        self.splash = tk.Toplevel(parent)
        self.splash.overrideredirect(True)
        img = Image.open(image_path)
        width, height = img.size
        sw = self.splash.winfo_screenwidth()
        sh = self.splash.winfo_screenheight()
        x = (sw - width) // 2
        y = (sh - height) // 2
        self.splash.geometry(f"{width}x{height}+{x}+{y}")
        self.photo = ImageTk.PhotoImage(img)
        tk.Label(self.splash, image=self.photo, bg='black').pack()
        self.splash.update()
        self.splash.after(timeout, self.close)

    def close(self):
        self.splash.destroy()
        self.parent.deiconify()


class ExeMaker:
    def __init__(self, root):
        self.root = root
        self.root.title("ExeMaker Pro - KRU66 2026")
        self.root.geometry("850x820")
        self.root.minsize(800, 770)
        self.root.withdraw()

        ModernTheme.apply(ttk.Style())

        # Eigen icoon voor het ExeMaker venster
        icon_file = resource_path("icon.ico")
        if os.path.exists(icon_file):
            try:
                self.root.iconbitmap(icon_file)
            except:
                pass

        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

        splash_img = resource_path("splash.png")
        if os.path.exists(splash_img):
            SplashScreen(root, splash_img, 2000)
        else:
            self.root.deiconify()

        self.target_exe = tk.StringVar()
        self.icon_path = tk.StringVar()
        self.splash_path = tk.StringVar()
        self.output_name = tk.StringVar(value="MijnProgramma")
        self.output_dir = tk.StringVar(value=os.path.join(os.getcwd(), "ExeMaker_Output"))
        self.create_shortcut = tk.BooleanVar(value=True)
        self.create_installer = tk.BooleanVar(value=False)
        self.inno_setup_path = tk.StringVar(value=r"C:\Program Files (x86)\Inno Setup 6\iscc.exe")
        self.install_dir_choice = tk.StringVar(value="Program Files (x86)")
        self.custom_install_dir = tk.StringVar(value="")
        self.build_in_progress = False

        self.create_widgets()

    def create_widgets(self):
        main = ttk.Frame(self.root, padding="20")
        main.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(main)
        header.grid(row=0, column=0, columnspan=2, sticky=tk.EW, pady=(0,20))
        ttk.Label(header, text="⚡ ExeMaker Pro - Installer Builder", font=('Segoe UI', 18, 'bold'), foreground='#1e6f9f').pack(side=tk.LEFT)
        ttk.Label(header, text="Maak EXE launcher of volledige setup", font=('Segoe UI', 10), foreground='#aaaaaa').pack(side=tk.LEFT, padx=(10,0))

        # Card 1 - Doelprogramma
        card1 = ttk.LabelFrame(main, text="📌 1. Doelprogramma (exe dat gestart moet worden)", padding="10")
        card1.grid(row=1, column=0, columnspan=2, sticky=tk.EW, pady=(0,15))
        ttk.Label(card1, text="Selecteer de .exe die gestart moet worden:").grid(row=0, column=0, sticky=tk.W, pady=(0,5))
        exe_frame = ttk.Frame(card1)
        exe_frame.grid(row=1, column=0, columnspan=2, sticky=tk.EW)
        ttk.Button(exe_frame, text="Bladeren...", command=self.select_target_exe).pack(side=tk.LEFT, padx=(0,10))
        self.exe_label = ttk.Label(exe_frame, text="Geen bestand gekozen", foreground='gray')
        self.exe_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        card1.columnconfigure(0, weight=1)

        # Card 2 - Uiterlijk (eigen icoon + splash)
        card2 = ttk.LabelFrame(main, text="🎨 2. Uiterlijk van de launcher", padding="10")
        card2.grid(row=2, column=0, columnspan=2, sticky=tk.EW, pady=(0,15))
        ttk.Label(card2, text="Icoon (.ico) voor de launcher (venster + taakbalk + exe):").grid(row=0, column=0, sticky=tk.W, pady=(0,5))
        icon_frame = ttk.Frame(card2)
        icon_frame.grid(row=1, column=0, columnspan=2, sticky=tk.EW, pady=(0,10))
        ttk.Button(icon_frame, text="Bladeren...", command=self.select_icon).pack(side=tk.LEFT, padx=(0,10))
        self.icon_label = ttk.Label(icon_frame, text="Geen icoon (standaard)", foreground='gray')
        self.icon_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Label(card2, text="Splash scherm (.png) - WORDT IN DE EXE INGEBOUWD:").grid(row=2, column=0, sticky=tk.W, pady=(5,5))
        splash_frame = ttk.Frame(card2)
        splash_frame.grid(row=3, column=0, columnspan=2, sticky=tk.EW)
        ttk.Button(splash_frame, text="Bladeren...", command=self.select_splash).pack(side=tk.LEFT, padx=(0,10))
        self.splash_label = ttk.Label(splash_frame, text="Geen splash (geen vertraging)", foreground='gray')
        self.splash_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        card2.columnconfigure(0, weight=1)

        # Card 3 - Output
        card3 = ttk.LabelFrame(main, text="💾 3. Output instellingen", padding="10")
        card3.grid(row=3, column=0, columnspan=2, sticky=tk.EW, pady=(0,15))
        ttk.Label(card3, text="Bestandsnaam (zonder .exe):").grid(row=0, column=0, sticky=tk.W, pady=(0,5))
        name_entry = ttk.Entry(card3, textvariable=self.output_name, width=30)
        name_entry.grid(row=0, column=1, sticky=tk.W, padx=(10,0))

        ttk.Label(card3, text="Opslagmap:").grid(row=1, column=0, sticky=tk.W, pady=(10,5))
        out_frame = ttk.Frame(card3)
        out_frame.grid(row=1, column=1, sticky=tk.EW, padx=(10,0))
        ttk.Button(out_frame, text="Bladeren...", command=self.select_output_dir).pack(side=tk.LEFT, padx=(0,10))
        self.out_label = ttk.Label(out_frame, text=self.output_dir.get(), foreground='white')
        self.out_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Checkbutton(card3, text="Maak snelkoppeling op bureaublad (alleen bij losse EXE)", variable=self.create_shortcut).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(10,0))
        ttk.Checkbutton(card3, text="🔧 Maak INSTALLATIEPAKKET (setup.exe) i.p.v. losse EXE", variable=self.create_installer, command=self.toggle_installer_options).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(5,0))

        self.installer_frame = ttk.Frame(card3)
        self.installer_frame.grid(row=4, column=0, columnspan=2, sticky=tk.EW, pady=(10,0))
        ttk.Label(self.installer_frame, text="Pad naar Inno Setup Compiler (iscc.exe):").grid(row=0, column=0, sticky=tk.W, pady=(0,5))
        inno_frame = ttk.Frame(self.installer_frame)
        inno_frame.grid(row=1, column=0, columnspan=2, sticky=tk.EW)
        ttk.Button(inno_frame, text="Bladeren...", command=self.select_inno_setup).pack(side=tk.LEFT, padx=(0,10))
        self.inno_label = ttk.Label(inno_frame, text=self.inno_setup_path.get(), foreground='white')
        self.inno_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Label(self.installer_frame, text="Doelmap voor installatie:").grid(row=2, column=0, sticky=tk.W, pady=(10,5))
        install_dir_frame = ttk.Frame(self.installer_frame)
        install_dir_frame.grid(row=3, column=0, columnspan=2, sticky=tk.EW, pady=(0,5))
        self.install_dir_combo = ttk.Combobox(install_dir_frame, textvariable=self.install_dir_choice,
                                              values=["Program Files (x86)", "Program Files", "Aangepast"],
                                              state="readonly", width=30)
        self.install_dir_combo.pack(side=tk.LEFT)
        self.install_dir_combo.bind("<<ComboboxSelected>>", self.on_install_dir_changed)

        self.custom_dir_frame = ttk.Frame(self.installer_frame)
        self.custom_dir_entry = ttk.Entry(self.custom_dir_frame, width=40, textvariable=self.custom_install_dir)
        self.custom_dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(self.custom_dir_frame, text="Bladeren...", command=self.select_custom_install_dir).pack(side=tk.LEFT, padx=(5,0))
        self.custom_dir_frame.grid(row=4, column=0, columnspan=2, sticky=tk.EW, pady=(5,0))
        self.custom_dir_frame.grid_remove()
        self.installer_frame.grid_remove()

        card3.columnconfigure(1, weight=1)

        self.progress = ttk.Progressbar(main, mode='indeterminate', length=400)
        self.progress.grid(row=5, column=0, sticky=tk.W, pady=(10,5))
        self.status_var = tk.StringVar(value="Klaar om te bouwen")
        status_label = ttk.Label(main, textvariable=self.status_var, font=('Segoe UI', 9), foreground='#aaaaaa')
        status_label.grid(row=6, column=0, sticky=tk.W)

        self.build_btn = ttk.Button(main, text="🚀 BOUW", command=self.start_build, style="Accent.TButton")
        self.build_btn.grid(row=5, column=1, rowspan=2, sticky=tk.E, padx=(10,0))

        copyright_frame = ttk.Frame(main)
        copyright_frame.grid(row=7, column=0, columnspan=2, sticky=tk.EW, pady=(20,0))
        ttk.Label(copyright_frame, text="© 2026 KRU66 - Alle rechten voorbehouden", font=('Segoe UI', 8), foreground='gray').pack(side=tk.RIGHT)

        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=0)

    def toggle_installer_options(self):
        if self.create_installer.get():
            self.installer_frame.grid()
        else:
            self.installer_frame.grid_remove()

    def on_install_dir_changed(self, event=None):
        if self.install_dir_choice.get() == "Aangepast":
            self.custom_dir_frame.grid()
        else:
            self.custom_dir_frame.grid_remove()

    def select_custom_install_dir(self):
        folder = filedialog.askdirectory(title="Selecteer installatiemap")
        if folder:
            self.custom_install_dir.set(folder)

    def select_target_exe(self):
        f = filedialog.askopenfilename(filetypes=[("Uitvoerbaar bestand", "*.exe")])
        if f:
            self.target_exe.set(f)
            self.exe_label.config(text=f, foreground='white')

    def select_icon(self):
        f = filedialog.askopenfilename(filetypes=[("Icoon", "*.ico")])
        if f:
            self.icon_path.set(f)
            self.icon_label.config(text=f, foreground='white')

    def select_splash(self):
        f = filedialog.askopenfilename(filetypes=[("PNG afbeelding", "*.png")])
        if f:
            self.splash_path.set(f)
            self.splash_label.config(text=f, foreground='white')

    def select_output_dir(self):
        d = filedialog.askdirectory()
        if d:
            self.output_dir.set(d)
            self.out_label.config(text=d)

    def select_inno_setup(self):
        f = filedialog.askopenfilename(filetypes=[("Uitvoerbaar bestand", "iscc.exe")])
        if f:
            self.inno_setup_path.set(f)
            self.inno_label.config(text=f)

    def start_build(self):
        if self.build_in_progress:
            messagebox.showwarning("Bezig", "Er wordt al een build uitgevoerd.")
            return
        if not self.target_exe.get():
            messagebox.showerror("Fout", "Selecteer een doel EXE bestand.")
            return
        if self.create_installer.get():
            if not os.path.exists(self.inno_setup_path.get()):
                messagebox.showerror("Fout", "Inno Setup Compiler (iscc.exe) niet gevonden.\nInstalleer Inno Setup of geef het juiste pad op.")
                return
            if self.install_dir_choice.get() == "Aangepast" and not self.custom_install_dir.get().strip():
                messagebox.showerror("Fout", "Voer een geldig pad in voor de aangepaste installatiemap.")
                return

        self.build_in_progress = True
        self.build_btn.config(state=tk.DISABLED, text="⚠️ Bezig...")
        self.progress.start(10)
        self.status_var.set("Bouwen... even geduld")
        threading.Thread(target=self.build, daemon=True).start()

    def build(self):
        if self.create_installer.get():
            self.build_installer()
        else:
            self.build_exe()

    # ========================================================
    # BUILD LOSSE EXE (met eigen icoon op venster + taakbalk)
    # ========================================================
    def build_exe(self):
        target = self.target_exe.get()
        target_filename = os.path.basename(target)
        source_folder = os.path.dirname(target)
        out_name = self.output_name.get().strip() or "MijnProgramma"
        out_dir = self.output_dir.get()
        os.makedirs(out_dir, exist_ok=True)

        icon = self.icon_path.get()
        icon_filename = os.path.basename(icon) if icon else ""
        splash = self.splash_path.get()

        script = LAUNCHER_TEMPLATE.replace("{{TARGET_EXE_FILENAME}}", target_filename)
        script = script.replace("{{ICON_FILENAME}}", icon_filename)

        temp_script = os.path.join(out_dir, f"_temp_{out_name}.py")
        with open(temp_script, "w", encoding="utf-8") as f:
            f.write(script)

        mode_flag = "--onefile" if USE_ONEFILE else "--onedir"
        console_flag = "--console" if DEBUG_CONSOLE else "--noconsole"
        icon_arg = f'--icon "{icon}"' if icon and os.path.exists(icon) else ""
        splash_arg = f'--add-data "{splash};."' if splash and os.path.exists(splash) else ""
        icon_data_arg = f'--add-data "{icon};."' if icon and os.path.exists(icon) else ""

        tcl_tk_args = ""
        if FORCE_TCL_TK_PATHS and sys.platform == 'win32':
            python_base = sys.prefix
            tcl_dir_candidate = os.path.join(python_base, 'tcl', 'tcl8.6')
            tk_dir_candidate = os.path.join(python_base, 'tcl', 'tk8.6')
            if os.path.isdir(tcl_dir_candidate):
                tcl_tk_args += f' --add-data "{tcl_dir_candidate};tcl"'
            if os.path.isdir(tk_dir_candidate):
                tcl_tk_args += f' --add-data "{tk_dir_candidate};tk"'
            if not os.path.isdir(tcl_dir_candidate):
                alt_tcl = os.path.join(python_base, 'Library', 'lib', 'tcl8.6')
                if os.path.isdir(alt_tcl):
                    tcl_tk_args += f' --add-data "{alt_tcl};tcl"'
            if not os.path.isdir(tk_dir_candidate):
                alt_tk = os.path.join(python_base, 'Library', 'lib', 'tk8.6')
                if os.path.isdir(alt_tk):
                    tcl_tk_args += f' --add-data "{alt_tk};tk"'

        cmd = (
            f'pyinstaller {mode_flag} {console_flag} --name "{out_name}" '
            f'--distpath "{out_dir}" --workpath "{out_dir}/build" --specpath "{out_dir}" '
            f'{icon_arg} {splash_arg} {icon_data_arg} {tcl_tk_args} '
            f'--hidden-import PIL --hidden-import PIL.ImageTk --hidden-import tkinter '
            f'--collect-all tkinter --collect-all PIL '
            f'--clean --noconfirm --noupx '
            f'--log-level=ERROR "{temp_script}"'
        )

        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=180)
            if result.returncode != 0:
                self.root.after(0, self.build_failed, f"PyInstaller fout:\n{result.stderr}")
                return

            os.remove(temp_script)
            shutil.rmtree(os.path.join(out_dir, "build"), ignore_errors=True)
            spec = os.path.join(out_dir, f"{out_name}.spec")
            if os.path.exists(spec):
                os.remove(spec)

            if USE_ONEFILE:
                exe_path = os.path.join(out_dir, f"{out_name}.exe")
                for item in os.listdir(source_folder):
                    s = os.path.join(source_folder, item)
                    d = os.path.join(out_dir, item)
                    if os.path.isdir(s):
                        shutil.copytree(s, d, dirs_exist_ok=True)
                    else:
                        shutil.copy2(s, d)
            else:
                exe_path = os.path.join(out_dir, out_name, f"{out_name}.exe")
                launcher_dir = os.path.dirname(exe_path)
                for item in os.listdir(source_folder):
                    s = os.path.join(source_folder, item)
                    d = os.path.join(launcher_dir, item)
                    if os.path.isdir(s):
                        shutil.copytree(s, d, dirs_exist_ok=True)
                    else:
                        shutil.copy2(s, d)

            shortcut_created = False
            if self.create_shortcut.get() and not USE_ONEFILE:
                desktop = os.path.join(os.path.expanduser("~"), "Desktop")
                shortcut_path = os.path.join(desktop, f"{out_name}.lnk")
                if self.create_windows_shortcut(exe_path, shortcut_path):
                    shortcut_created = True

            self.root.after(0, self.build_success, exe_path, shortcut_created, False)

        except Exception as e:
            self.root.after(0, self.build_failed, f"Fout: {str(e)}")

    # ========================================================
    # BUILD INSTALLER
    # ========================================================
    def build_installer(self):
        temp_build_dir = tempfile.mkdtemp(prefix="ExeMaker_")
        out_name = self.output_name.get().strip() or "MijnProgramma"
        icon = self.icon_path.get()
        icon_filename = os.path.basename(icon) if icon else ""
        splash = self.splash_path.get()
        target = self.target_exe.get()
        target_filename = os.path.basename(target)
        source_folder = os.path.dirname(target)

        script = LAUNCHER_TEMPLATE.replace("{{TARGET_EXE_FILENAME}}", target_filename)
        script = script.replace("{{ICON_FILENAME}}", icon_filename)

        temp_script = os.path.join(temp_build_dir, "launcher.py")
        with open(temp_script, "w", encoding="utf-8") as f:
            f.write(script)

        mode_flag = "--onedir"
        console_flag = "--noconsole"
        icon_arg = f'--icon "{icon}"' if icon and os.path.exists(icon) else ""
        splash_arg = f'--add-data "{splash};."' if splash and os.path.exists(splash) else ""
        icon_data_arg = f'--add-data "{icon};."' if icon and os.path.exists(icon) else ""

        tcl_tk_args = ""
        if FORCE_TCL_TK_PATHS and sys.platform == 'win32':
            python_base = sys.prefix
            tcl_dir_candidate = os.path.join(python_base, 'tcl', 'tcl8.6')
            tk_dir_candidate = os.path.join(python_base, 'tcl', 'tk8.6')
            if os.path.isdir(tcl_dir_candidate):
                tcl_tk_args += f' --add-data "{tcl_dir_candidate};tcl"'
            if os.path.isdir(tk_dir_candidate):
                tcl_tk_args += f' --add-data "{tk_dir_candidate};tk"'
            if not os.path.isdir(tcl_dir_candidate):
                alt_tcl = os.path.join(python_base, 'Library', 'lib', 'tcl8.6')
                if os.path.isdir(alt_tcl):
                    tcl_tk_args += f' --add-data "{alt_tcl};tcl"'
            if not os.path.isdir(tk_dir_candidate):
                alt_tk = os.path.join(python_base, 'Library', 'lib', 'tk8.6')
                if os.path.isdir(alt_tk):
                    tcl_tk_args += f' --add-data "{alt_tk};tk"'

        cmd = (
            f'pyinstaller {mode_flag} {console_flag} --name "{out_name}" '
            f'--distpath "{temp_build_dir}" --workpath "{temp_build_dir}/build" --specpath "{temp_build_dir}" '
            f'{icon_arg} {splash_arg} {icon_data_arg} {tcl_tk_args} '
            f'--hidden-import PIL --hidden-import PIL.ImageTk --hidden-import tkinter '
            f'--collect-all tkinter --collect-all PIL '
            f'--clean --noconfirm --noupx '
            f'--log-level=ERROR "{temp_script}"'
        )

        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=180)
            if result.returncode != 0:
                self.root.after(0, self.build_failed, f"Kan launcher niet bouwen:\n{result.stderr}")
                return

            launcher_exe_dir = os.path.join(temp_build_dir, out_name)
            launcher_exe = os.path.join(launcher_exe_dir, f"{out_name}.exe")
            if not os.path.exists(launcher_exe):
                self.root.after(0, self.build_failed, "Launcher EXE niet gevonden na build.")
                return

            temp_source = tempfile.mkdtemp(prefix="ExeMaker_Source_")
            launcher_dest_dir = os.path.join(temp_source, out_name)
            shutil.copytree(launcher_exe_dir, launcher_dest_dir)

            for item in os.listdir(source_folder):
                s = os.path.join(source_folder, item)
                d = os.path.join(launcher_dest_dir, item)
                if os.path.isdir(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, d)

            iss_path = os.path.join(self.output_dir.get(), f"{out_name}_setup.iss")
            setup_output = os.path.join(self.output_dir.get(), "Setup")
            os.makedirs(setup_output, exist_ok=True)

            iss_content = self.generate_inno_script(out_name, temp_source, icon, setup_output, launcher_subdir=out_name)
            with open(iss_path, "w", encoding="utf-8") as f:
                f.write(iss_content)

            iscc = self.inno_setup_path.get()
            compile_cmd = f'"{iscc}" "{iss_path}"'
            result = subprocess.run(compile_cmd, shell=True, capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                self.root.after(0, self.build_failed, f"Inno Setup fout:\n{result.stderr}")
                return

            setup_file = os.path.join(setup_output, f"{out_name}_Setup.exe")
            if os.path.exists(setup_file):
                self.root.after(0, self.build_success, setup_file, False, True)
            else:
                self.root.after(0, self.build_failed, "Setup.exe niet gevonden na compilatie.")

        except Exception as e:
            self.root.after(0, self.build_failed, f"Fout tijdens installer bouw: {str(e)}")
        finally:
            shutil.rmtree(temp_build_dir, ignore_errors=True)
            if 'temp_source' in locals():
                shutil.rmtree(temp_source, ignore_errors=True)

    def generate_inno_script(self, app_name, source_folder, icon_file, output_dir, launcher_subdir=""):
        choice = self.install_dir_choice.get()
        if choice == "Program Files":
            default_dir = "{pf}\\" + app_name
        elif choice == "Program Files (x86)":
            default_dir = "{pf32}\\" + app_name
        else:
            custom = self.custom_install_dir.get().strip()
            default_dir = custom + "\\" + app_name if custom else "{pf32}\\" + app_name

        icon_line = f'SetupIconFile="{icon_file}"' if icon_file and os.path.exists(icon_file) else ''
        files_source = f'"{source_folder}\\{launcher_subdir}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs'

        return f'''; Inno Setup Script gegenereerd door ExeMaker Pro
[Setup]
AppName={app_name}
AppVersion=1.0
DefaultDirName={default_dir}
DefaultGroupName={app_name}
UninstallDisplayIcon={{app}}\\{app_name}.exe
{icon_line}
OutputDir={output_dir}
OutputBaseFilename={app_name}_Setup
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=admin

[Files]
Source: {files_source}

[Icons]
Name: "{{group}}\\{app_name}"; Filename: "{{app}}\\{app_name}.exe"
Name: "{{group}}\\Deïnstalleer {app_name}"; Filename: "{{uninstallexe}}"
Name: "{{userdesktop}}\\{app_name}"; Filename: "{{app}}\\{app_name}.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Maak snelkoppeling op bureaublad"; GroupDescription: "Extra pictogrammen:"

[Run]
Filename: "{{app}}\\{app_name}.exe"; Description: "Start {app_name} nu"; Flags: postinstall nowait skipifsilent
'''

    def create_windows_shortcut(self, target_path, shortcut_path):
        try:
            ps_command = f'''
            $WScriptShell = New-Object -ComObject WScript.Shell
            $Shortcut = $WScriptShell.CreateShortcut("{shortcut_path}")
            $Shortcut.TargetPath = "{target_path}"
            $Shortcut.Save()
            '''
            subprocess.run(["powershell", "-Command", ps_command], shell=True, capture_output=True)
            return os.path.exists(shortcut_path)
        except:
            return False

    def build_success(self, output_path, shortcut_created, is_installer):
        self.progress.stop()
        self.build_in_progress = False
        self.build_btn.config(state=tk.NORMAL, text="🚀 BOUW")
        self.status_var.set("Gereed!")

        if is_installer:
            msg = f"Installatiepakket succesvol aangemaakt!\n{output_path}\n\nDe volledige inhoud van de map van het doelprogramma is mee verpakt."
        else:
            msg = f"EXE succesvol aangemaakt!\n{output_path}\n\nDe volledige inhoud van de map van het doelprogramma is mee verpakt."
            if shortcut_created:
                msg += "\n\nSnelkoppeling is op het bureaublad gezet."

        messagebox.showinfo("Succes", msg)
        os.startfile(os.path.dirname(output_path))

    def build_failed(self, error_msg):
        self.progress.stop()
        self.build_in_progress = False
        self.build_btn.config(state=tk.NORMAL, text="🚀 BOUW")
        self.status_var.set("Bouw mislukt")
        messagebox.showerror("Fout", error_msg)


if __name__ == "__main__":
    root = tk.Tk()
    app = ExeMaker(root)
    root.mainloop()