import tkinter as tk
import time
import threading

# ================== НАСТРОЙКИ ==================
ACTIVATION_KEY = "14823-qewqe"
TIMER_SECONDS = 10
WINDOWS_PER_MINUTE = 50
SAFE_MODE = True
WINDOW_WIDTH = 620
WINDOW_HEIGHT = 380
CORNER_RADIUS = 20
# ===============================================


def center_window(win, w, h):
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    x = (sw - w) // 2
    y = (sh - h) // 2
    win.geometry(f"{w}x{h}+{x}+{y}")


def rounded_rect(canvas, x1, y1, x2, y2, r, **kwargs):
    points = [
        x1+r, y1, x2-r, y1,
        x2, y1, x2, y1+r,
        x2, y2-r, x2, y2,
        x2-r, y2, x1+r, y2,
        x1, y2, x1, y2-r,
        x1, y1+r, x1, y1
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


class DeltaDesktop:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="black")

        center_window(self.root, WINDOW_WIDTH, WINDOW_HEIGHT)

        self.canvas = tk.Canvas(
            self.root,
            width=WINDOW_WIDTH,
            height=WINDOW_HEIGHT,
            bg="black",
            highlightthickness=0
        )
        self.canvas.pack()

        rounded_rect(
            self.canvas, 0, 0,
            WINDOW_WIDTH, WINDOW_HEIGHT,
            CORNER_RADIUS,
            fill="#0b0b0b",
            outline="#2b2b2b",
            width=2
        )

        self.create_ui()
        self.root.mainloop()

    def create_ui(self):
        frame = tk.Frame(self.root, bg="#0b0b0b")
        frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(
            frame,
            text="Введите ключ активации",
            fg="white",
            bg="#0b0b0b",
            font=("Segoe UI", 12)
        ).pack(pady=8)

        self.entry = tk.Entry(
            frame,
            width=36,
            bg="#1a1a1a",
            fg="white",
            relief="flat",
            font=("Segoe UI", 11)
        )
        self.entry.pack(ipady=6)

        tk.Button(
            frame,
            text="Активировать",
            bg="#1db954",
            fg="black",
            bd=0,
            font=("Segoe UI", 11),
            width=24,
            command=self.activate
        ).pack(pady=14)

    def activate(self):
        if self.entry.get() == ACTIVATION_KEY:
            self.root.destroy()
            FullScreenWindow()


class FullScreenWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="black")

        self.end_time = time.time() + TIMER_SECONDS

        self.top_text = tk.Label(
            self.root, text="точка",
            fg="white", bg="black",
            font=("Segoe UI", 28)
        )
        self.top_text.place(relx=0.5, rely=0.46, anchor="center")

        self.timer = tk.Label(
            self.root,
            fg="white", bg="black",
            font=("Segoe UI", 22)
        )
        self.timer.place(relx=0.5, rely=0.5, anchor="center")

        self.bottom_text = tk.Label(
            self.root, text="точка",
            fg="white", bg="black",
            font=("Segoe UI", 28)
        )
        self.bottom_text.place(relx=0.5, rely=0.54, anchor="center")

        self.update_timer()
        self.root.mainloop()

    def update_timer(self):
        remaining = int(self.end_time - time.time())
        if remaining <= 0:
            self.root.destroy()
            SpawnWindow()
            return

        self.timer.config(text=f"{remaining} сек")
        self.root.after(1000, self.update_timer)


class SpawnWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="black")

        size = 300
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{size}x{size}+{(sw-size)//2}+{(sh-size)//2}")

        self.spawned_windows = []
        self.running = True
        self.keys_pressed = set()

        self.root.bind("<KeyPress>", self.key_down)
        self.root.bind("<KeyRelease>", self.key_up)
        self.root.focus_force()

        threading.Thread(target=self.spawn_loop, daemon=True).start()
        self.root.mainloop()

    def key_down(self, e):
        self.keys_pressed.add(e.keysym.lower())
        if "i" in self.keys_pressed and "g" in self.keys_pressed:
            self.shutdown_all()

    def key_up(self, e):
        self.keys_pressed.discard(e.keysym.lower())

    def spawn_loop(self):
        interval = 60 / WINDOWS_PER_MINUTE
        while self.running:
            self.fake_explorer()
            time.sleep(interval)

    def fake_explorer(self):
        w = tk.Toplevel()
        w.title("window")
        w.geometry("400x400")
        tk.Label(
            w,
            text="window bro",
            font=("Segoe UI", 12)
        ).pack(expand=True)

        self.spawned_windows.append(w)

    def shutdown_all(self):
        self.running = False

        for w in self.spawned_windows:
            try:
                w.destroy()
            except:
                pass

        self.spawned_windows.clear()
        self.root.destroy()


DeltaDesktop()
