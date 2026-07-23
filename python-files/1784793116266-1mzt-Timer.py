import tkinter as tk
import time

# Section durations (minutes) – total = 60 min
DURATIONS = [6, 2, 5, 1, 7, 5, 5, 1, 6, 7, 1, 1, 3, 6, 4]
DURATIONS_SEC = [d * 60 for d in DURATIONS]
TOTAL_SEC = sum(DURATIONS_SEC)

# Full headings
HEADINGS = [
    "1. Strengths & Weaknesses",
    "2. Fundamentals",
    "3. Vocabulary",
    "4. Adv. Language 1",
    "5. MGP1",
    "6. Agility 1",
    "7. Correct Homework",
    "8. Adv. Language 2",
    "9. Agility 2",
    "10. MGP2",
    "11. Set Homework",
    "12. Adv. Language 3",
    "13. Speaking Activity",
    "14. Review",
    "15. Agility 3"
]

class LessonTimer:
    def __init__(self, root):
        self.root = root
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.92)          # almost opaque, still a little transparency
        self.root.geometry("560x150+100+100")         # initial expanded size

        # Drag
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.root.bind("<Button-1>", self.start_drag)
        self.root.bind("<B1-Motion>", self.drag)
        self.root.bind("<ButtonRelease-1>", self.stop_drag)

        # State
        self.running = False
        self.elapsed = 0
        self.current_section = 0
        self.collapsed = False

        self.build_ui()
        self.update()

    def build_ui(self):
        # Main container – light background, dark text
        self.main = tk.Frame(self.root, bg="#f0f0f0")
        self.main.pack(fill=tk.BOTH, expand=True)

        # Use grid for easy collapse of lower rows
        self.main.grid_rowconfigure(0, weight=0)
        self.main.grid_rowconfigure(1, weight=0)
        self.main.grid_rowconfigure(2, weight=0)
        self.main.grid_rowconfigure(3, weight=0)
        self.main.grid_rowconfigure(4, weight=0)
        self.main.grid_columnconfigure(0, weight=1)

        # ---- Row 0: Canvas (bar) - always visible ----
        self.canvas = tk.Canvas(self.main, height=32, bg="#e0e0e0", highlightthickness=1, highlightbackground="#cccccc")
        self.canvas.grid(row=0, column=0, padx=8, pady=(8, 2), sticky="ew")

        # Draw sections: transparent with black borders
        self.section_rects = []
        x = 0
        width = self.canvas.winfo_width() if self.canvas.winfo_width() > 1 else 540
        for dur in DURATIONS_SEC:
            frac = dur / TOTAL_SEC
            rect_width = frac * width
            rect = self.canvas.create_rectangle(
                x, 0, x + rect_width, 32,
                fill="",
                outline="black",
                width=1
            )
            self.section_rects.append(rect)
            x += rect_width

        # Red progress line
        self.progress_line = self.canvas.create_line(0, 0, 0, 32, fill="red", width=3)

        # Bind click on canvas to toggle expand (when collapsed)
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        # ---- Row 1: Current heading (dark text) ----
        self.heading_current = tk.Label(
            self.main,
            text="Ready",
            font=("Arial", 14, "bold"),
            fg="#222222",
            bg="#f0f0f0"
        )
        self.heading_current.grid(row=1, column=0, pady=(4, 0), sticky="w", padx=10)

        # ---- Row 2: Next heading (smaller, gray) ----
        self.heading_next = tk.Label(
            self.main,
            text="Next: —",
            font=("Arial", 10),
            fg="#555555",
            bg="#f0f0f0"
        )
        self.heading_next.grid(row=2, column=0, pady=(0, 2), sticky="w", padx=10)

        # ---- Row 3: Time display ----
        self.time_label = tk.Label(
            self.main,
            text="00:00 / 60:00",
            font=("Arial", 9),
            fg="#333333",
            bg="#f0f0f0"
        )
        self.time_label.grid(row=3, column=0, pady=(0, 2), sticky="w", padx=10)

        # ---- Row 4: Buttons ----
        self.btn_frame = tk.Frame(self.main, bg="#f0f0f0")
        self.btn_frame.grid(row=4, column=0, pady=3, sticky="ew", padx=10)

        tk.Button(self.btn_frame, text="▶ Start", command=self.start,
                  width=6, font=("Arial", 8), bg="#d0d0d0", fg="black").pack(side=tk.LEFT, padx=3)
        tk.Button(self.btn_frame, text="⟳ Reset", command=self.reset,
                  width=6, font=("Arial", 8), bg="#d0d0d0", fg="black").pack(side=tk.LEFT, padx=3)
        tk.Button(self.btn_frame, text="⏹ End", command=self.end,
                  width=6, font=("Arial", 8), bg="#d0d0d0", fg="black").pack(side=tk.LEFT, padx=3)
        tk.Button(self.btn_frame, text="▼ Collapse", command=self.toggle_collapse,
                  width=8, font=("Arial", 8), bg="#d0d0d0", fg="black").pack(side=tk.LEFT, padx=3)
        tk.Button(self.btn_frame, text="✕ Exit", command=self.exit_app,
                  width=6, font=("Arial", 8), bg="#d0d0d0", fg="black").pack(side=tk.LEFT, padx=3)

        # Bind resize event to redraw sections
        self.canvas.bind("<Configure>", self.on_canvas_resize)

    def on_canvas_resize(self, event):
        width = event.width
        x = 0
        for i, dur in enumerate(DURATIONS_SEC):
            frac = dur / TOTAL_SEC
            rect_width = frac * width
            self.canvas.coords(self.section_rects[i], x, 0, x + rect_width, 32)
            x += rect_width
        self.update_line()

    # ---- Canvas click (to expand when collapsed) ----
    def on_canvas_click(self, event):
        if self.collapsed:
            self.toggle_collapse()

    # ---- Expand / Collapse ----
    def toggle_collapse(self):
        self.collapsed = not self.collapsed
        if self.collapsed:
            # Hide lower rows
            self.heading_current.grid_remove()
            self.heading_next.grid_remove()
            self.time_label.grid_remove()
            self.btn_frame.grid_remove()
            # Shrink window height (only canvas row + padding)
            self.root.geometry("560x50")   # adjust as needed
            # Change collapse button text (it's in btn_frame which is hidden, but we can change when expanded again)
        else:
            # Show rows
            self.heading_current.grid()
            self.heading_next.grid()
            self.time_label.grid()
            self.btn_frame.grid()
            # Restore original height
            self.root.geometry("560x150")
        # Update the collapse button text (it's in btn_frame, only accessible when expanded)
        # We'll update it when the button is re-created? Actually we can keep reference to button widget.
        # We'll store the button reference.
        if hasattr(self, 'collapse_btn'):
            self.collapse_btn.config(text="▲ Expand" if self.collapsed else "▼ Collapse")

    # ---- Drag ----
    def start_drag(self, event):
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def drag(self, event):
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy
        self.root.geometry(f"+{x}+{y}")

    def stop_drag(self, event):
        pass

    # ---- Controls ----
    def start(self):
        if not self.running:
            self.running = True
            self.start_time = time.time() - self.elapsed

    def reset(self):
        self.running = False
        self.elapsed = 0
        self.current_section = 0
        self.update_display()

    def end(self):
        self.running = False
        self.elapsed = TOTAL_SEC
        self.current_section = len(DURATIONS_SEC) - 1
        self.update_display()

    def exit_app(self):
        self.root.destroy()

    # ---- Update loop ----
    def update(self):
        if self.running:
            self.elapsed = time.time() - self.start_time
            if self.elapsed >= TOTAL_SEC:
                self.elapsed = TOTAL_SEC
                self.running = False
            self.update_display()
        self.root.after(50, self.update)

    def update_display(self):
        self.update_line()
        self.update_headings()
        self.update_time()

    def update_line(self):
        frac = min(self.elapsed / TOTAL_SEC, 1.0)
        width = self.canvas.winfo_width()
        if width <= 1:
            width = 540
        x_pos = frac * width
        self.canvas.coords(self.progress_line, x_pos, 0, x_pos, 32)

    def update_headings(self):
        # Find current section
        cum = 0
        idx = 0
        for i, dur in enumerate(DURATIONS_SEC):
            if self.elapsed < cum + dur:
                idx = i
                break
            cum += dur
        else:
            idx = len(DURATIONS_SEC) - 1
        self.current_section = idx

        # Current with duration
        dur_min = DURATIONS[idx]
        self.heading_current.config(text=f"{HEADINGS[idx]} – {dur_min} min")

        # Next
        if idx + 1 < len(HEADINGS):
            self.heading_next.config(text=f"Next: {HEADINGS[idx+1]} – {DURATIONS[idx+1]} min")
        else:
            self.heading_next.config(text="End of lesson")

    def update_time(self):
        em = int(self.elapsed // 60)
        es = int(self.elapsed % 60)
        tm = int(TOTAL_SEC // 60)
        ts = int(TOTAL_SEC % 60)
        self.time_label.config(text=f"{em:02d}:{es:02d} / {tm:02d}:{ts:02d}")

if __name__ == "__main__":
    root = tk.Tk()
    app = LessonTimer(root)
    root.mainloop()