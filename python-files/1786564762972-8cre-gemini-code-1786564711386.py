import os
import json
from datetime import datetime
import tkinter as tk
from tkinter import ttk, colorchooser

# Configuration directory for Apex CloudStudio auto-saves
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".apex_cloudstudio")
os.makedirs(CONFIG_DIR, exist_ok=True)
AUTOSAVE_HISTORY_PATH = os.path.join(CONFIG_DIR, "autosave_history.json")

class ApexCloudStudioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Apex CloudStudio - Real AutoSave Engine")
        self.root.geometry("1100x700")
        self.root.configure(bg="#0d1117")

        # Styling
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        self.active_app_id = None
        self.autosave_after_id = None

        # Main Layout Container
        self.main_container = tk.Frame(self.root, bg="#0d1117")
        self.main_container.pack(fill=tk.BOTH, expand=True)

        self.create_sidebar()
        self.create_content_area()
        self.show_view("apps")

    def create_sidebar(self):
        self.sidebar = tk.Frame(self.main_container, bg="#161b22", width=240)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        # Brand Header
        brand_frame = tk.Frame(self.sidebar, bg="#161b22", pady=20, padx=15)
        brand_frame.pack(fill=tk.X)
        
        logo_lbl = tk.Label(brand_frame, text="AX", bg="#1f6feb", fg="#ffffff", font=("Segoe UI", 12, "bold"), width=3, height=1)
        logo_lbl.pack(side=tk.LEFT, padx=(0, 10))

        title_lbl = tk.Label(brand_frame, text="Apex CloudStudio\nAutoSave Engine", bg="#161b22", fg="#c9d1d9", font=("Segoe UI", 10, "bold"), justify=tk.LEFT)
        title_lbl.pack(side=tk.LEFT)

        # Navigation Links
        nav_frame = tk.Frame(self.sidebar, bg="#161b22", padx=10, pady=10)
        nav_frame.pack(fill=tk.X)

        self.nav_apps_btn = tk.Button(nav_frame, text="⚡ Studio Applications", bg="#21262d", fg="#ffffff", relief=tk.FLAT, anchor="w", padx=10, pady=8, font=("Segoe UI", 10), command=lambda: self.show_view("apps"))
        self.nav_apps_btn.pack(fill=tk.X, pady=2)

        self.nav_recovery_btn = tk.Button(nav_frame, text="📂 AutoSave Recovery Hub", bg="#161b22", fg="#8b949e", relief=tk.FLAT, anchor="w", padx=10, pady=8, font=("Segoe UI", 10), command=lambda: self.show_view("autosaves"))
        self.nav_recovery_btn.pack(fill=tk.X, pady=2)

        # User Profile Footer
        profile_frame = tk.Frame(self.sidebar, bg="#161b22", pady=15, padx=15)
        profile_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        avatar_lbl = tk.Label(profile_frame, text="AC", bg="#238636", fg="#ffffff", font=("Segoe UI", 10, "bold"), width=3, height=1)
        avatar_lbl.pack(side=tk.LEFT, padx=(0, 10))

        user_info_frame = tk.Frame(profile_frame, bg="#161b22")
        user_info_frame.pack(side=tk.LEFT)
        tk.Label(user_info_frame, text="Apex Creator", bg="#161b22", fg="#c9d1d9", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Label(user_info_frame, text="Real AutoSave Active", bg="#161b22", fg="#8b949e", font=("Segoe UI", 8)).pack(anchor="w")

    def create_content_area(self):
        self.content_area = tk.Frame(self.main_container, bg="#0d1117")
        self.content_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Top Header Bar
        self.header_bar = tk.Frame(self.content_area, bg="#0d1117", padx=30, pady=20)
        self.header_bar.pack(fill=tk.X)

        self.header_title = tk.Label(self.header_bar, text="Apex CloudStudio Applications", bg="#0d1117", fg="#ffffff", font=("Segoe UI", 16, "bold"))
        self.header_title.pack(side=tk.LEFT)

        # Views Container
        self.views_container = tk.Frame(self.content_area, bg="#0d1117")
        self.views_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)

        # 1. Apps View
        self.apps_view = tk.Frame(self.views_container, bg="#0d1117")
        self.build_apps_grid(self.apps_view)

        # 2. AutoSave Recovery Hub View
        self.autosaves_view = tk.Frame(self.views_container, bg="#0d1117")
        self.build_autosaves_hub(self.autosaves_view)

    def show_view(self, view_name):
        self.nav_apps_btn.config(bg="#161b22", fg="#8b949e")
        self.nav_recovery_btn.config(bg="#161b22", fg="#8b949e")

        self.apps_view.pack_forget()
        self.autosaves_view.pack_forget()

        if view_name == "apps":
            self.nav_apps_btn.config(bg="#21262d", fg="#ffffff")
            self.header_title.config(text="Apex CloudStudio Applications")
            self.apps_view.pack(fill=tk.BOTH, expand=True)
        elif view_name == "autosaves":
            self.nav_recovery_btn.config(bg="#21262d", fg="#ffffff")
            self.header_title.config(text="Real AutoSave Recovery Hub")
            self.refresh_autosaves_hub()
            self.autosaves_view.pack(fill=tk.BOTH, expand=True)

    def build_apps_grid(self, parent):
        grid_frame = tk.Frame(parent, bg="#0d1117")
        grid_frame.pack(fill=tk.BOTH, expand=True)

        apps = [
            {"id": "nexuspad", "name": "NexusPad Writer", "code": "Np", "bg": "#1f6feb", "fg": "#ffffff", "desc": "Rich text document editor with instant background AutoSave history."},
            {"id": "prismraster", "name": "PrismRaster Canvas", "code": "Pr", "bg": "#8957e5", "fg": "#ffffff", "desc": "Freehand pixel paint workspace capturing state snapshots continuously."}
        ]

        for idx, app in enumerate(apps):
            card = tk.Frame(grid_frame, bg="#161b22", padx=20, pady=20, highlightbackground="#30363d", highlightthickness=1)
            card.grid(row=0, column=idx, padx=10, pady=10, sticky="nsew")

            top_row = tk.Frame(card, bg="#161b22")
            top_row.pack(fill=tk.X, pady=(0, 10))

            icon_lbl = tk.Label(top_row, text=app["code"], bg=app["bg"], fg=app["fg"], font=("Segoe UI", 11, "bold"), width=3, height=2)
            icon_lbl.pack(side=tk.LEFT, padx=(0, 12))

            details_frame = tk.Frame(top_row, bg="#161b22")
            details_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

            tk.Label(details_frame, text=app["name"], bg="#161b22", fg="#ffffff", font=("Segoe UI", 11, "bold")).pack(anchor="w")
            tk.Label(details_frame, text=app["desc"], bg="#161b22", fg="#8b949e", font=("Segoe UI", 9), wraplength=220, justify=tk.LEFT).pack(anchor="w", pady=(4, 0))

            action_btn = tk.Button(card, text="Launch App", bg="#238636", fg="#ffffff", relief=tk.FLAT, font=("Segoe UI", 9, "bold"), padx=15, pady=6, command=lambda aid=app["id"]: self.launch_workspace(aid))
            action_btn.pack(anchor="e", pady=(15, 0))

    def build_autosaves_hub(self, parent):
        tk.Label(parent, text="Apex CloudStudio automatically commits background session snapshots to local configuration storage.", bg="#0d1117", fg="#8b949e", font=("Segoe UI", 10)).pack(anchor="w", pady=(0, 15))
        
        self.hub_list_frame = tk.Frame(parent, bg="#0d1117")
        self.hub_list_frame.pack(fill=tk.BOTH, expand=True)

    def refresh_autosaves_hub(self):
        for widget in self.hub_list_frame.winfo_children():
            widget.destroy()

        history = []
        if os.path.exists(AUTOSAVE_HISTORY_PATH):
            try:
                with open(AUTOSAVE_HISTORY_PATH, "r") as f:
                    history = json.load(f)
            except Exception:
                history = []

        if not history:
            tk.Label(self.hub_list_frame, text="No auto-saved sessions recorded yet. Launch an app and start working!", bg="#0d1117", fg="#8b949e", font=("Segoe UI", 10)).pack(anchor="w")
            return

        for item in history:
            card = tk.Frame(self.hub_list_frame, bg="#161b22", padx=15, pady=12, highlightbackground="#30363d", highlightthickness=1)
            card.pack(fill=tk.X, pady=5)

            header_frame = tk.Frame(card, bg="#161b22")
            header_frame.pack(fill=tk.X)

            tk.Label(header_frame, text=item.get("app_name", "Studio App"), bg="#161b22", fg="#58a6ff", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
            tk.Label(header_frame, text=item.get("timestamp", ""), bg="#161b22", fg="#8b949e", font=("Segoe UI", 9)).pack(side=tk.RIGHT)

            tk.Label(card, text="Background AutoSave snapshot ready for immediate recovery.", bg="#161b22", fg="#8b949e", font=("Segoe UI", 9)).pack(anchor="w", pady=(4, 8))

            app_id = item.get("app_id")
            restore_btn = tk.Button(card, text="Recover Session", bg="#21262d", fg="#ffffff", relief=tk.FLAT, font=("Segoe UI", 8, "bold"), padx=10, pady=4, command=lambda aid=app_id: self.launch_workspace(aid))
            restore_btn.pack(anchor="w")

    def launch_workspace(self, app_id):
        self.active_app_id = app_id
        
        self.ws_window = tk.Toplevel(self.root)
        self.ws_window.title("Apex CloudStudio - Active Workspace")
        self.ws_window.geometry("950x600")
        self.ws_window.configure(bg="#0d1117")
        self.ws_window.protocol("WM_DELETE_WINDOW", self.close_workspace)

        # Workspace Header Bar
        ws_header = tk.Frame(self.ws_window, bg="#161b22", height=48, padx=20)
        ws_header.pack(fill=tk.X)
        ws_header.pack_propagate(False)

        app_name_text = "NexusPad Writer" if app_id == "nexuspad" else "PrismRaster Canvas"
        tk.Label(ws_header, text=app_name_text + " — Real AutoSave Active", bg="#161b22", fg="#ffffff", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)

        # Real AutoSave Live Status Indicator
        self.status_lbl = tk.Label(ws_header, text="🟢 All changes saved", bg="#21262d", fg="#3fb950", font=("Segoe UI", 9), padx=10)
        self.status_lbl.pack(side=tk.RIGHT, padx=15)

        tk.Button(ws_header, text="Exit App", bg="#da3633", fg="#ffffff", relief=tk.FLAT, font=("Segoe UI", 9), command=self.close_workspace).pack(side=tk.RIGHT)

        # Workspace Body
        self.ws_body = tk.Frame(self.ws_window, bg="#0d1117")
        self.ws_body.pack(fill=tk.BOTH, expand=True)

        saved_state = self.load_autosave_state(app_id)

        if app_id == "nexuspad":
            self.init_nexuspad_workspace(saved_state)
        elif app_id == "prismraster":
            self.init_prismraster_workspace(saved_state)

        # Start live background heartbeat (autosaves every 5 seconds)
        self.start_autosave_heartbeat()

    def close_workspace(self):
        if self.autosave_after_id:
            self.ws_window.after_cancel(self.autosave_after_id)
        if self.active_app_id:
            self.perform_autosave()
        self.active_app_id = None
        self.ws_window.destroy()

    def start_autosave_heartbeat(self):
        def heartbeat():
            if self.active_app_id:
                self.perform_autosave()
                self.autosave_after_id = self.ws_window.after(5000, heartbeat)
        self.autosave_after_id = self.ws_window.after(5000, heartbeat)

    def trigger_autosave(self):
        if self.active_app_id:
            self.perform_autosave()

    def perform_autosave(self):
        if not hasattr(self, 'status_lbl') or not self.status_lbl.winfo_exists():
            return

        self.status_lbl.config(text="⏳ Saving...", fg="#d29922")
        timestamp = datetime.now().strftime("%H:%M:%S")

        state_data = {
            "app_id": self.active_app_id,
            "app_name": "NexusPad Writer" if self.active_app_id == "nexuspad" else "PrismRaster Canvas",
            "timestamp": timestamp
        }

        if self.active_app_id == "nexuspad":
            state_data["text_content"] = self.np_text.get("1.0", tk.END)
        elif self.active_app_id == "prismraster":
            state_data["brush_color"] = self.pr_color
            state_data["brush_size"] = self.pr_size_scale.get()
            items = self.pr_canvas.find_all()
            coords_list = [self.pr_canvas.coords(item) for item in items]
            state_data["items"] = coords_list

        try:
            with open(os.path.join(CONFIG_DIR, f"autosave_{self.active_app_id}.json"), "w") as f:
                json.dump(state_data, f)

            history = []
            if os.path.exists(AUTOSAVE_HISTORY_PATH):
                with open(AUTOSAVE_HISTORY_PATH, "r") as f:
                    history = json.load(f)
            
            history = [h for h in history if h.get("app_id") != self.active_app_id]
            history.insert(0, state_data)
            if len(history) > 20:
                history.pop()

            with open(AUTOSAVE_HISTORY_PATH, "w") as f:
                json.dump(history, f)
        except Exception as e:
            print("AutoSave error:", e)

        def update_status_ui():
            if self.status_lbl.winfo_exists():
                self.status_lbl.config(text=f"🟢 Saved at {timestamp}", fg="#3fb950")
        self.ws_window.after(300, update_status_ui)

    def load_autosave_state(self, app_id):
        path = os.path.join(CONFIG_DIR, f"autosave_{app_id}.json")
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    # --- 1. NEXUSPAD WRITER WORKSPACE ---
    def init_nexuspad_workspace(self, saved_state):
        editor_frame = tk.Frame(self.ws_body, bg="#0d1117", padx=20, pady=20)
        editor_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(editor_frame, text="NexusPad Document Editor (AutoSave active on typing)", bg="#0d1117", fg="#8b949e", font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 8))

        self.np_text = tk.Text(editor_frame, bg="#161b22", fg="#c9d1d9", insertbackground="#ffffff", font=("Segoe UI", 11), padx=15, pady=15, relief=tk.FLAT)
        self.np_text.pack(fill=tk.BOTH, expand=True)

        if saved_state and "text_content" in saved_state:
            self.np_text.insert("1.0", saved_state["text_content"])

        # Trigger immediate background auto-save on keystrokes
        self.np_text.bind("<KeyRelease>", lambda e: self.trigger_autosave())

    # --- 2. PRISMRASTER CANVAS WORKSPACE ---
    def init_prismraster_workspace(self, saved_state):
        self.pr_color = "#1f6feb"

        sidebar = tk.Frame(self.ws_body, bg="#161b22", width=60)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        tk.Button(sidebar, text="🗑️", bg="#21262d", fg="#ffffff", relief=tk.FLAT, command=self.clear_prismraster).pack(pady=10, padx=10, fill=tk.X)

        canvas_container = tk.Frame(self.ws_body, bg="#0d1117")
        canvas_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.pr_canvas = tk.Canvas(canvas_container, bg="#161b22", width=650, height=450, cursor="crosshair")
        self.pr_canvas.pack(expand=True, padx=20, pady=20)

        self.pr_canvas.bind("<B1-Motion>", self.paint_prismraster)
        self.pr_canvas.bind("<ButtonRelease-1>", lambda e: self.trigger_autosave())

        props = tk.Frame(self.ws_body, bg="#161b22", width=260, padx=15, pady=15)
        props.pack(side=tk.RIGHT, fill=tk.Y)
        props.pack_propagate(False)

        tk.Label(props, text="Raster Options", bg="#161b22", fg="#ffffff", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 10))

        tk.Label(props, text="Brush Size", bg="#161b22", fg="#8b949e", font=("Segoe UI", 9)).pack(anchor="w")
        self.pr_size_scale = tk.Scale(props, from_=1, to=30, orient=tk.HORIZONTAL, bg="#21262d", fg="#ffffff", highlightthickness=0)
        self.pr_size_scale.set(10)
        self.pr_size_scale.pack(fill=tk.X, pady=(0, 15))

        tk.Button(props, text="🎨 Choose Color", bg="#21262d", fg="#ffffff", relief=tk.FLAT, command=self.choose_pr_color).pack(fill=tk.X, pady=5)

        if saved_state and "items" in saved_state:
            self.pr_color = saved_state.get("brush_color", "#1f6feb")
            self.pr_size_scale.set(saved_state.get("brush_size", 10))
            for coords in saved_state["items"]:
                if len(coords) >= 4:
                    self.pr_canvas.create_oval(coords[0], coords[1], coords[2], coords[3], fill=self.pr_color, outline=self.pr_color)

    def paint_prismraster(self, event):
        r = self.pr_size_scale.get()
        self.pr_canvas.create_oval(event.x - r, event.y - r, event.x + r, event.y + r, fill=self.pr_color, outline=self.pr_color)

    def clear_prismraster(self):
        self.pr_canvas.delete("all")
        self.trigger_autosave()

    def choose_pr_color(self):
        color_code = colorchooser.askcolor(title="Choose Brush Color")[1]
        if color_code:
            self.pr_color = color_code

if __name__ == "__main__":
    root = tk.Tk()
    app = ApexCloudStudioApp(root)
    root.mainloop()