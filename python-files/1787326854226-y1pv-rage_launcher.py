import tkinter as tk
from tkinter import ttk, filedialog
from datetime import datetime
from pathlib import Path
import subprocess
import sys


# ============================================================
# RAGE DEVELOPMENT PORTAL
# Fictional GTA VI development launcher / UI prop
# ============================================================

WINDOW_WIDTH = 760
WINDOW_HEIGHT = 560

BG = "#202020"
PANEL = "#1a1a1a"
BORDER = "#383838"
TEXT = "#d2d2d2"
MUTED = "#777777"
DARK = "#101010"
BUTTON = "#b5b5b5"


# ============================================================
# PATHS
# ============================================================

# Folder containing this launcher
SCRIPT_DIR = Path(__file__).resolve().parent

# GTA VI menu Python file
GAME_MENU = SCRIPT_DIR / "gta_vi_menu.py"


class RageLauncher(tk.Tk):

    def __init__(self):
        super().__init__()

        # ----------------------------------------------------
        # REAL WINDOWS TITLE BAR
        # ----------------------------------------------------

        self.title("RAGE Development Portal v.2.0.21")

        self.geometry(
            f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}"
        )

        self.minsize(
            700,
            500
        )

        self.configure(
            bg=BG
        )

        # ----------------------------------------------------
        # VARIABLES
        # ----------------------------------------------------

        self.configuration = tk.StringVar(
            value="Development"
        )

        self.debug_tools = tk.BooleanVar(
            value=False
        )

        self.skip_intro = tk.BooleanVar(
            value=False
        )

        self.disable_online = tk.BooleanVar(
            value=True
        )

        self.status_text = tk.StringVar(
            value="Ready"
        )

        # Keep logo alive
        self.logo_image = None

        # ----------------------------------------------------
        # STYLE
        # ----------------------------------------------------

        self.setup_styles()

        # ----------------------------------------------------
        # BUILD UI
        # ----------------------------------------------------

        self.build_interface()

        # ----------------------------------------------------
        # INITIAL CONSOLE
        # ----------------------------------------------------

        self.log_message(
            "Launcher initialized."
        )

        self.log_message(
            "Loading project configuration..."
        )

        self.log_message(
            "Checking build files..."
        )

        if GAME_MENU.exists():

            self.log_message(
                "Game executable target found."
            )

        else:

            self.log_message(
                "Warning: game menu target not found."
            )

        self.log_message(
            "Ready."
        )

        self.update_clock()

    # ========================================================
    # STYLING
    # ========================================================

    def setup_styles(self):

        style = ttk.Style(self)

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Dev.TCombobox",

            background=DARK,
            foreground=TEXT,

            fieldbackground=DARK,

            bordercolor=BORDER,
            lightcolor=BORDER,
            darkcolor=BORDER,

            arrowcolor=MUTED
        )

        style.map(
            "Dev.TCombobox",

            fieldbackground=[
                ("readonly", DARK)
            ],

            foreground=[
                ("readonly", TEXT)
            ]
        )

    # ========================================================
    # MAIN INTERFACE
    # ========================================================

    def build_interface(self):

        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        header = tk.Frame(
            self,
            bg=BG
        )

        header.pack(
            fill="x",
            padx=30,
            pady=(24, 0)
        )

        # ----------------------------------------------------
        # HEADER CONTENT
        # ----------------------------------------------------

        header_content = tk.Frame(
            header,
            bg=BG
        )

        header_content.pack(
            anchor="w"
        )

        # ----------------------------------------------------
        # LOGO
        # ----------------------------------------------------

        self.logo_label = tk.Label(
            header_content,
            bg=BG
        )

        self.logo_label.pack(
            side="left",
            anchor="center"
        )

        self.load_logo()

        # ----------------------------------------------------
        # TITLE NEXT TO LOGO
        # ----------------------------------------------------

        title_frame = tk.Frame(
            header_content,
            bg=BG
        )

        title_frame.pack(
            side="left",
            padx=(18, 0),
            anchor="center"
        )

        tk.Label(
            title_frame,

            text="Grand Theft Auto VI",

            bg=BG,
            fg="#eeeeee",

            font=(
                "Segoe UI",
                17,
                "bold"
            )
        ).pack(
            anchor="w"
        )

        tk.Label(
            title_frame,

            text="Development Build",

            bg=BG,
            fg=MUTED,

            font=(
                "Segoe UI",
                9
            )
        ).pack(
            anchor="w",
            pady=(2, 0)
        )

        tk.Label(
            title_frame,

            text="v.1.0.245",

            bg=BG,
            fg="#5f5f5f",

            font=(
                "Consolas",
                8
            )
        ).pack(
            anchor="w",
            pady=(3, 0)
        )

        # ----------------------------------------------------
        # CHANGE LOGO
        # ----------------------------------------------------

        tk.Button(
            header,

            text=" ",

            command=self.choose_logo,

            bg=BG,
            fg="#666666",

            activebackground=BG,
            activeforeground="#aaaaaa",

            relief="flat",
            bd=0,

            font=(
                "Segoe UI",
                8
            ),

            cursor="hand2"
        ).pack(
            anchor="w",
            pady=(5, 0)
        )

        # ----------------------------------------------------
        # SEPARATOR
        # ----------------------------------------------------

        self.separator(
            pady=(14, 0)
        )

        # ----------------------------------------------------
        # BUILD INFORMATION
        # ----------------------------------------------------

        build_frame = self.panel(
            "BUILD"
        )

        build_frame.pack(
            fill="x",
            padx=30,
            pady=(16, 0)
        )

        self.info_row(
            build_frame,
            "Build",
            "1.0.245"
        )

        self.info_row(
            build_frame,
            "Branch",
            "main"
        )

        self.info_row(
            build_frame,
            "Platform",
            "Win64"
        )

        self.info_row(
            build_frame,
            "Renderer",
            "Vulkan"
        )

        # ----------------------------------------------------
        # BUILD CONFIGURATION
        # ----------------------------------------------------

        config = self.panel(
            "BUILD CONFIGURATION"
        )

        config.pack(
            fill="x",
            padx=30,
            pady=(15, 0)
        )

        row = tk.Frame(
            config,
            bg=PANEL
        )

        row.pack(
            fill="x",
            padx=12,
            pady=(8, 5)
        )

        tk.Label(
            row,

            text="Configuration",

            width=17,
            anchor="w",

            bg=PANEL,
            fg=MUTED,

            font=(
                "Segoe UI",
                9
            )
        ).pack(
            side="left"
        )

        combo = ttk.Combobox(
            row,

            textvariable=self.configuration,

            values=[
                "Development",
                "Test",
                "Shipping"
            ],

            state="readonly",

            width=23,

            style="Dev.TCombobox"
        )

        combo.pack(
            side="left"
        )

        # ----------------------------------------------------
        # CHECKBOXES
        # ----------------------------------------------------

        self.checkbox(
            config,
            "Enable Debug Tools",
            self.debug_tools
        )

        self.checkbox(
            config,
            "Skip Intro",
            self.skip_intro
        )

        self.checkbox(
            config,
            "Disable Online",
            self.disable_online
        )

        # ----------------------------------------------------
        # LAUNCH AREA
        # ----------------------------------------------------

        launch_area = tk.Frame(
            self,

            bg=PANEL,

            highlightbackground=BORDER,
            highlightthickness=1
        )

        launch_area.pack(
            fill="x",
            padx=30,
            pady=(15, 0)
        )

        self.launch_button = tk.Button(
            launch_area,

            text="LAUNCH GAME",

            command=self.launch,

            bg=BUTTON,
            fg="#111111",

            activebackground="#d0d0d0",
            activeforeground="#111111",

            relief="flat",
            bd=0,

            padx=24,
            pady=8,

            font=(
                "Segoe UI",
                9,
                "bold"
            ),

            cursor="hand2"
        )

        self.launch_button.pack(
            side="left",
            padx=14,
            pady=14
        )

        tk.Label(
            launch_area,

            text="Status:",

            bg=PANEL,
            fg=MUTED,

            font=(
                "Segoe UI",
                9
            )
        ).pack(
            side="left"
        )

        tk.Label(
            launch_area,

            textvariable=self.status_text,

            bg=PANEL,
            fg="#aaaaaa",

            font=(
                "Segoe UI",
                9
            )
        ).pack(
            side="left",
            padx=(4, 0)
        )

        # ----------------------------------------------------
        # CONSOLE
        # ----------------------------------------------------

        console = tk.Frame(
            self,

            bg=DARK,

            highlightbackground=BORDER,
            highlightthickness=1
        )

        console.pack(
            fill="both",
            expand=True,

            padx=30,
            pady=(15, 0)
        )

        tk.Label(
            console,

            text="LAUNCHER CONSOLE",

            bg=DARK,
            fg=MUTED,

            font=(
                "Segoe UI",
                8,
                "bold"
            )
        ).pack(
            anchor="w",
            padx=11,
            pady=(8, 4)
        )

        self.console = tk.Text(
            console,

            bg=DARK,
            fg="#707070",

            insertbackground="#777777",

            relief="flat",
            bd=0,

            font=(
                "Consolas",
                9
            ),

            height=5,

            state="disabled"
        )

        self.console.pack(
            fill="both",
            expand=True,

            padx=10,
            pady=(0, 8)
        )

        # ----------------------------------------------------
        # FOOTER
        # ----------------------------------------------------

        footer = tk.Frame(
            self,

            bg="#252525",

            height=32
        )

        footer.pack(
            fill="x",
            pady=(15, 0)
        )

        tk.Label(
            footer,

            text="RAGE 9.0.0  |  PC  |  Internal Build",

            bg="#252525",
            fg="#606060",

            font=(
                "Segoe UI",
                8
            )
        ).pack(
            side="left",
            padx=12,
            pady=8
        )

        self.clock = tk.Label(
            footer,

            bg="#252525",
            fg="#606060",

            font=(
                "Consolas",
                8
            )
        )

        self.clock.pack(
            side="right",
            padx=12
        )

    # ========================================================
    # LOGO LOADING
    # ========================================================

    def load_logo(self):

        # Look beside launcher first
        local_logo = (
            SCRIPT_DIR /
            "gta6_logo.png"
        )

        if local_logo.exists():

            self.set_logo(
                local_logo
            )

            return

        # Look in Downloads
        downloads = (
            Path.home() /
            "Downloads"
        )

        possible_files = [
            "gta6_logo.png",
            "gta_vi_logo.png",
            "GTAVI.png",
            "GTA6.png",
            "gta6.png"
        ]

        for filename in possible_files:

            path = downloads / filename

            if path.exists():

                self.set_logo(
                    path
                )

                return

        # Fallback
        self.logo_label.configure(
            text="GTAVI",

            fg="#eeeeee",

            font=(
                "Segoe UI",
                18,
                "bold"
            )
        )

    def set_logo(self, path):

        try:

            image = tk.PhotoImage(
                file=str(path)
            )

            max_width = 420
            max_height = 130

            width = image.width()
            height = image.height()

            scale_x = max(
                1,
                (width + max_width - 1)
                // max_width
            )

            scale_y = max(
                1,
                (height + max_height - 1)
                // max_height
            )

            scale = max(
                scale_x,
                scale_y
            )

            if scale > 1:

                image = image.subsample(
                    scale,
                    scale
                )

            self.logo_image = image

            self.logo_label.configure(
                image=self.logo_image,
                text=""
            )

        except Exception as error:

            self.logo_label.configure(
                text="GTAVI",

                fg="#eeeeee",

                font=(
                    "Segoe UI",
                    18,
                    "bold"
                )
            )

            self.log_message(
                f"Logo load failed: {error}"
            )

    def choose_logo(self):

        path = filedialog.askopenfilename(
            title="Select GTA VI Logo",

            initialdir=str(
                Path.home() /
                "Downloads"
            ),

            filetypes=[
                (
                    "PNG Images",
                    "*.png"
                ),
                (
                    "GIF Images",
                    "*.gif"
                ),
                (
                    "All Files",
                    "*.*"
                )
            ]
        )

        if path:

            self.set_logo(
                Path(path)
            )

            self.log_message(
                "Logo loaded."
            )

    # ========================================================
    # UI HELPERS
    # ========================================================

    def panel(self, title):

        frame = tk.Frame(
            self,

            bg=PANEL,

            highlightbackground=BORDER,
            highlightthickness=1
        )

        tk.Label(
            frame,

            text=title,

            bg=PANEL,
            fg=MUTED,

            font=(
                "Segoe UI",
                8,
                "bold"
            )
        ).pack(
            anchor="w",
            padx=12,
            pady=(9, 5)
        )

        return frame

    def info_row(
        self,
        parent,
        label,
        value
    ):

        row = tk.Frame(
            parent,
            bg=PANEL
        )

        row.pack(
            fill="x",
            padx=12,
            pady=2
        )

        tk.Label(
            row,

            text=label,

            width=17,
            anchor="w",

            bg=PANEL,
            fg=MUTED,

            font=(
                "Segoe UI",
                9
            )
        ).pack(
            side="left"
        )

        tk.Label(
            row,

            text=value,

            bg=PANEL,
            fg=TEXT,

            font=(
                "Segoe UI",
                9
            )
        ).pack(
            side="left"
        )

    def checkbox(
        self,
        parent,
        text,
        variable
    ):

        tk.Checkbutton(
            parent,

            text=text,

            variable=variable,

            bg=PANEL,
            fg="#999999",

            activebackground=PANEL,
            activeforeground="#bbbbbb",

            selectcolor=DARK,

            anchor="w",

            font=(
                "Segoe UI",
                9
            )
        ).pack(
            fill="x",
            padx=12,
            pady=2
        )

    def separator(
        self,
        pady=(0, 0)
    ):

        tk.Frame(
            self,

            bg=BORDER,

            height=1
        ).pack(
            fill="x",
            padx=30,
            pady=pady
        )

    # ========================================================
    # CONSOLE
    # ========================================================

    def log_message(
        self,
        message
    ):

        timestamp = datetime.now().strftime(
            "%H:%M:%S"
        )

        self.console.configure(
            state="normal"
        )

        self.console.insert(
            "end",

            f"[{timestamp}] {message}\n"
        )

        self.console.see(
            "end"
        )

        self.console.configure(
            state="disabled"
        )

    # ========================================================
    # LAUNCH GAME MENU
    # ========================================================

    def launch(self):

        # Prevent double-clicking
        self.launch_button.configure(
            state="disabled"
        )

        self.status_text.set(
            "Launching..."
        )

        self.log_message(
            "Preparing runtime..."
        )

        self.after(
            400,

            lambda: self.log_message(
                "Mounting game data..."
            )
        )

        self.after(
            850,

            lambda: self.log_message(
                "Initializing RAGE runtime..."
            )
        )

        self.after(
            1300,

            lambda: self.log_message(
                "Loading configuration: "
                + self.configuration.get()
            )
        )

        self.after(
            1700,

            self.start_game_menu
        )

    def start_game_menu(self):

        # ----------------------------------------------------
        # CHECK FILE EXISTS
        # ----------------------------------------------------

        if not GAME_MENU.exists():

            self.log_message(
                "ERROR: gta_vi_menu.py not found."
            )

            self.status_text.set(
                "Launch failed"
            )

            self.launch_button.configure(
                state="normal"
            )

            return

        # ----------------------------------------------------
        # START GTA VI MENU
        # ----------------------------------------------------

        try:

            self.log_message(
                "Starting game process..."
            )

            subprocess.Popen(
                [
                    sys.executable,
                    str(GAME_MENU)
                ],

                cwd=str(
                    SCRIPT_DIR
                )
            )

            self.log_message(
                "Process started."
            )

            self.status_text.set(
                "Process started"
            )

        except Exception as error:

            self.log_message(
                f"ERROR: {error}"
            )

            self.status_text.set(
                "Launch failed"
            )

        finally:

            self.launch_button.configure(
                state="normal"
            )

    # ========================================================
    # CLOCK
    # ========================================================

    def update_clock(self):

        self.clock.configure(
            text=datetime.now().strftime(
                "%H:%M:%S"
            )
        )

        self.after(
            1000,
            self.update_clock
        )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    launcher = RageLauncher()

    launcher.mainloop()
