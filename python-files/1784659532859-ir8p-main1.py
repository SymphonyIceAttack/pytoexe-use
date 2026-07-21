import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Aether UI")
        self.geometry("930x580")
        self.minsize(820, 500)
        self.configure(fg_color="#050816")
        self._build_ui()

    def _build_ui(self):
        root = ctk.CTkFrame(self, corner_radius=30, fg_color="#0b1120", border_width=1, border_color="#24344f")
        root.pack(fill="both", expand=True, padx=22, pady=22)

        sidebar = ctk.CTkFrame(root, width=250, corner_radius=24, fg_color="#0f172a", border_width=1, border_color="#24344f")
        sidebar.pack(side="left", fill="y", padx=18, pady=18)

        ctk.CTkLabel(sidebar, text="Aether", text_color="#f8fafc", font=("Segoe UI", 28, "bold")).pack(anchor="w", padx=22, pady=(24, 4))
        ctk.CTkLabel(sidebar, text="Modern desktop experience", text_color="#8ba0bf", font=("Segoe UI", 12)).pack(anchor="w", padx=22, pady=(0, 26))

        for text in ["Overview", "Projects", "Workspace", "Settings"]:
            btn = ctk.CTkButton(
                sidebar,
                text=text,
                corner_radius=14,
                height=40,
                fg_color="#131d31",
                hover_color="#1e2b46",
                border_color="#334b6d",
                border_width=1,
                text_color="#e2e8f0",
            )
            btn.pack(fill="x", padx=18, pady=6)

        content = ctk.CTkFrame(root, corner_radius=24, fg_color="#09111f", border_width=1, border_color="#24344f")
        content.pack(side="right", fill="both", expand=True, padx=(0, 18), pady=18)

        hero = ctk.CTkFrame(content, corner_radius=22, fg_color="#101a2c", border_width=1, border_color="#2d4265")
        hero.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(hero, text="Welcome back", text_color="#f8fafc", font=("Segoe UI", 24, "bold")).pack(anchor="w", padx=22, pady=(18, 4))
        ctk.CTkLabel(hero, text="A polished, premium-looking interface with depth, contrast, and motion-ready polish.", text_color="#8fa3bf", font=("Segoe UI", 13)).pack(anchor="w", padx=22, pady=(0, 18))

        card = ctk.CTkFrame(hero, corner_radius=18, fg_color="#14233c", border_width=1, border_color="#3b5373")
        card.pack(fill="x", padx=18, pady=(0, 18))

        ctk.CTkLabel(card, text="Project name", text_color="#f8fafc", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=16, pady=(14, 6))
        self.name_entry = ctk.CTkEntry(card, placeholder_text="Design system", width=330, border_color="#4d6480", fg_color="#0a1020")
        self.name_entry.pack(fill="x", padx=16, pady=(0, 10))

        self.switch = ctk.CTkSwitch(card, text="Enable AI helper", text_color="#f8fafc", progress_color="#60a5fa")
        self.switch.pack(anchor="w", padx=16, pady=(0, 12))

        ctk.CTkButton(card, text="Create Project", corner_radius=12, height=40, fg_color="#60a5fa", hover_color="#4f8ef7", text_color="#08111d").pack(anchor="w", padx=16, pady=(0, 14))

        progress = ctk.CTkProgressBar(content, width=300, height=10, progress_color="#60a5fa", fg_color="#17243a")
        progress.pack(anchor="w", padx=20, pady=(4, 6))
        progress.set(0.84)

        ctk.CTkLabel(content, text="Sync progress: 84%", text_color="#60a5fa", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=20, pady=(0, 8))


if __name__ == "__main__":
    app = App()
    app.mainloop()
