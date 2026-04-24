import socket
import threading
import tkinter as tk
import time

SERVER_IP = "192.168.1.100"
PORT = 5000

USERNAME = "ADMIN"
PASSWORD = "password"

# ألوان عصرية متناسقة
COLORS = {
    "bg": "#0f1419",
    "bg_gradient": "#1a1f2e",
    "card": "#1e2533",
    "card_hover": "#252d3d",
    "accent": "#00d9ff",
    "accent_dim": "#0099cc",
    "gold": "#ffb800",
    "success": "#00e676",
    "danger": "#ff5252",
    "text": "#ffffff",
    "text_dim": "#8b95a7",
    "border": "#2a3346",
    "input_bg": "#161b26",
}

sock = None
is_unlocked = False
root = None
time_left = 0
lock_container = None
user_entry = None
pass_entry = None
error_label = None
status_label = None
status_dot = None
clock_label = None


# ========== الاتصال ==========
def connect():
    global sock
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((SERVER_IP, PORT))
            hostname = socket.gethostname()
            sock.send(f"REGISTER|{hostname}\n".encode())
            update_status("متصل بالخادم", connected=True)
            threading.Thread(target=heartbeat, daemon=True).start()
            threading.Thread(target=listen, daemon=True).start()
            break
        except Exception:
            update_status("جاري إعادة الاتصال...", connected=False)
            time.sleep(3)


def heartbeat():
    global sock
    while True:
        try:
            sock.send("HEARTBEAT\n".encode())
            time.sleep(30)
        except Exception:
            break


def listen():
    global time_left
    while True:
        try:
            data = sock.recv(1024).decode().strip()
            if not data:
                break

            if data.startswith("START_PREPAID_"):
                paid = float(data.split("_")[2])
                total_seconds = int((paid / 5.0) * 3600)
                time_left = total_seconds
                root.after(0, unlock_screen)

            elif data.startswith("START_"):
                mins = int(data.split("_")[1])
                time_left = mins * 60
                root.after(0, unlock_screen)

            elif data == "STOP":
                time_left = 0
                root.after(0, lock_screen)

            elif data == "UNLOCK":
                time_left = 0
                root.after(0, unlock_screen)
        except Exception:
            update_status("فقد الاتصال بالخادم", connected=False)
            break


def update_status(text, connected=None):
    try:
        if status_label is not None:
            status_label.config(text=text)
        if status_dot is not None and connected is not None:
            status_dot.config(fg=COLORS["success"] if connected else COLORS["danger"])
    except Exception:
        pass


# ========== المؤقت والقفل ==========
def timer_loop():
    global time_left
    while True:
        if is_unlocked and time_left > 0:
            time_left -= 1
            if time_left <= 0:
                root.after(0, lock_screen)
        time.sleep(1)


def unlock_screen():
    """عند فتح الجهاز من الادمن: تختفي النافذة بالكامل"""
    global is_unlocked
    is_unlocked = True
    try:
        root.attributes("-fullscreen", False)
        root.attributes("-topmost", False)
        root.withdraw()
    except Exception:
        pass


def lock_screen():
    """قفل الشاشة وعرض حقل كلمة المرور"""
    global is_unlocked
    is_unlocked = False
    try:
        root.deiconify()
        root.attributes("-fullscreen", True)
        root.attributes("-topmost", True)
        root.lift()
        root.focus_force()
        if pass_entry is not None:
            pass_entry.delete(0, tk.END)
            pass_entry.focus()
        if error_label is not None:
            error_label.config(text="")
    except Exception:
        pass


def check_login():
    global error_label
    u = user_entry.get().strip().upper()
    p = pass_entry.get()
    if u == USERNAME and p == PASSWORD:
        unlock_screen()
    else:
        error_label.config(text="✕  اسم المستخدم أو كلمة المرور غير صحيحة")
        pass_entry.delete(0, tk.END)
        pass_entry.focus()
        # اهتزاز خفيف للتنبيه
        shake_window()


def shake_window():
    """تأثير اهتزاز عند الخطأ"""
    try:
        x, y = root.winfo_x(), root.winfo_y()
        for offset in (10, -10, 8, -8, 5, -5, 0):
            root.geometry(f"+{x + offset}+{y}")
            root.update()
            time.sleep(0.02)
    except Exception:
        pass


def block_key(event):
    return "break"


def keep_on_top():
    try:
        if not is_unlocked and root.winfo_exists():
            root.lift()
            root.attributes("-topmost", True)
    except Exception:
        pass
    root.after(700, keep_on_top)


def update_clock():
    try:
        if clock_label is not None and not is_unlocked:
            clock_label.config(text=time.strftime("%H:%M  |  %A  %d/%m/%Y"))
    except Exception:
        pass
    root.after(1000, update_clock)


# ========== الواجهة ==========
def build_lock_ui():
    global lock_container, user_entry, pass_entry, error_label
    global status_label, status_dot, clock_label

    # خلفية رئيسية
    lock_container = tk.Frame(root, bg=COLORS["bg"])
    lock_container.pack(fill="both", expand=True)

    # الساعة في الأعلى
    top_bar = tk.Frame(lock_container, bg=COLORS["bg"], height=60)
    top_bar.pack(fill="x", pady=(20, 0))
    top_bar.pack_propagate(False)

    clock_label = tk.Label(
        top_bar,
        text="",
        font=("Segoe UI", 14),
        fg=COLORS["text_dim"],
        bg=COLORS["bg"],
    )
    clock_label.pack(side="left", padx=30)

    # حالة الاتصال أعلى اليمين
    conn_frame = tk.Frame(top_bar, bg=COLORS["bg"])
    conn_frame.pack(side="right", padx=30)

    status_dot = tk.Label(
        conn_frame,
        text="●",
        font=("Segoe UI", 16),
        fg=COLORS["danger"],
        bg=COLORS["bg"],
    )
    status_dot.pack(side="right", padx=(8, 0))

    status_label = tk.Label(
        conn_frame,
        text="جاري الاتصال...",
        font=("Segoe UI", 11),
        fg=COLORS["text_dim"],
        bg=COLORS["bg"],
    )
    status_label.pack(side="right")

    # المنطقة المركزية - بطاقة تسجيل الدخول
    center_wrapper = tk.Frame(lock_container, bg=COLORS["bg"])
    center_wrapper.place(relx=0.5, rely=0.5, anchor="center")

    # شعار / أيقونة قفل بشكل دائرة
    icon_canvas = tk.Canvas(
        center_wrapper,
        width=110,
        height=110,
        bg=COLORS["bg"],
        highlightthickness=0,
    )
    icon_canvas.pack(pady=(0, 20))
    # دائرة خارجية متوهجة
    icon_canvas.create_oval(5, 5, 105, 105, outline=COLORS["accent"], width=3)
    icon_canvas.create_oval(20, 20, 90, 90, fill=COLORS["card"], outline=COLORS["accent_dim"], width=1)
    # رمز قفل
    icon_canvas.create_rectangle(43, 52, 67, 78, fill=COLORS["accent"], outline="")
    icon_canvas.create_arc(38, 30, 72, 64, start=0, extent=180, style="arc", outline=COLORS["accent"], width=4)
    icon_canvas.create_oval(52, 60, 58, 66, fill=COLORS["bg"], outline="")

    # اسم المقهى
    tk.Label(
        center_wrapper,
        text="مقهى فور جي نت",
        font=("Segoe UI", 36, "bold"),
        fg=COLORS["gold"],
        bg=COLORS["bg"],
    ).pack(pady=(0, 8))

    # شريط فاصل ذهبي
    sep = tk.Frame(center_wrapper, bg=COLORS["gold"], height=3, width=80)
    sep.pack(pady=(0, 15))

    # رسالة القفل
    tk.Label(
        center_wrapper,
        text="الجهاز مقفل",
        font=("Segoe UI", 18, "bold"),
        fg=COLORS["text"],
        bg=COLORS["bg"],
    ).pack()

    tk.Label(
        center_wrapper,
        text="يرجى التواصل مع الكاشير لتفعيل الجهاز",
        font=("Segoe UI", 12),
        fg=COLORS["text_dim"],
        bg=COLORS["bg"],
    ).pack(pady=(4, 30))

    # بطاقة تسجيل الدخول
    card = tk.Frame(center_wrapper, bg=COLORS["card"], padx=40, pady=30)
    card.pack()

    tk.Label(
        card,
        text="تسجيل دخول الموظف",
        font=("Segoe UI", 13, "bold"),
        fg=COLORS["accent"],
        bg=COLORS["card"],
    ).pack(pady=(0, 20))

    # حقل اسم المستخدم
    tk.Label(
        card,
        text="اسم المستخدم",
        font=("Segoe UI", 10),
        fg=COLORS["text_dim"],
        bg=COLORS["card"],
        anchor="e",
    ).pack(fill="x", pady=(0, 4))

    user_entry = tk.Entry(
        card,
        font=("Segoe UI", 14),
        width=28,
        justify="center",
        bg=COLORS["input_bg"],
        fg=COLORS["text"],
        insertbackground=COLORS["accent"],
        relief="flat",
        bd=0,
    )
    user_entry.pack(ipady=10, pady=(0, 16))

    # حقل كلمة المرور
    tk.Label(
        card,
        text="كلمة المرور",
        font=("Segoe UI", 10),
        fg=COLORS["text_dim"],
        bg=COLORS["card"],
        anchor="e",
    ).pack(fill="x", pady=(0, 4))

    pass_entry = tk.Entry(
        card,
        font=("Segoe UI", 14),
        width=28,
        show="●",
        justify="center",
        bg=COLORS["input_bg"],
        fg=COLORS["text"],
        insertbackground=COLORS["accent"],
        relief="flat",
        bd=0,
    )
    pass_entry.pack(ipady=10, pady=(0, 12))

    # رسالة الخطأ
    error_label = tk.Label(
        card,
        text="",
        font=("Segoe UI", 10, "bold"),
        fg=COLORS["danger"],
        bg=COLORS["card"],
    )
    error_label.pack(pady=(0, 12))

    # زر الدخول
    login_btn = tk.Button(
        card,
        text="دخول",
        font=("Segoe UI", 13, "bold"),
        bg=COLORS["accent"],
        fg=COLORS["bg"],
        activebackground=COLORS["accent_dim"],
        activeforeground=COLORS["bg"],
        width=24,
        bd=0,
        relief="flat",
        cursor="hand2",
        command=check_login,
        pady=12,
    )
    login_btn.pack()

    # تأثير hover للزر
    def on_hover(e):
        login_btn.config(bg=COLORS["accent_dim"])

    def on_leave(e):
        login_btn.config(bg=COLORS["accent"])

    login_btn.bind("<Enter>", on_hover)
    login_btn.bind("<Leave>", on_leave)

    # شريط سفلي
    footer = tk.Frame(lock_container, bg=COLORS["bg"], height=50)
    footer.pack(side="bottom", fill="x")
    footer.pack_propagate(False)

    tk.Label(
        footer,
        text="© برمجة وتصميم — أبورباب الحضرمي",
        font=("Segoe UI", 9),
        fg=COLORS["text_dim"],
        bg=COLORS["bg"],
    ).pack(pady=15)

    user_entry.bind("<Return>", lambda e: pass_entry.focus())
    pass_entry.bind("<Return>", lambda e: check_login())

    user_entry.focus()


def create_kiosk():
    global root

    root = tk.Tk()
    root.title("Cafe Client")
    root.attributes("-fullscreen", True)
    root.configure(bg=COLORS["bg"])
    root.attributes("-topmost", True)
    root.lift()

    root.protocol("WM_DELETE_WINDOW", lambda: None)

    # منع اختصارات الهروب
    for key in (
        "<Alt-F4>",
        "<Alt-Tab>",
        "<Control-Escape>",
        "<Escape>",
        "<F11>",
        "<Control-w>",
        "<Control-W>",
        "<Alt-space>",
    ):
        root.bind_all(key, block_key)

    build_lock_ui()
    keep_on_top()
    update_clock()

    threading.Thread(target=connect, daemon=True).start()
    threading.Thread(target=timer_loop, daemon=True).start()

    root.mainloop()


if __name__ == "__main__":
    create_kiosk()