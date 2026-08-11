import ctypes
import time
import tkinter as tk
from tkinter import messagebox
import threading

# =========================
# SETTINGS
# =========================

HOLD_TIME = 0.1
MOVE_AMOUNT = 0.1
MOVE_INTERVAL = 0.01

# =========================
# WINDOWS MOUSE INPUT
# =========================

user32 = ctypes.windll.user32

MOUSEEVENTF_MOVE = 0x0001
VK_LBUTTON = 0x01


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
    ]


class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_ulong),
        ("mi", MOUSEINPUT)
    ]


def move_mouse_relative(dx, dy):
    extra = ctypes.c_ulong(0)

    mouse_input = MOUSEINPUT(
        int(dx),
        int(dy),
        0,
        MOUSEEVENTF_MOVE,
        0,
        ctypes.pointer(extra)
    )

    input_data = INPUT(
        0,
        mouse_input
    )

    user32.SendInput(
        1,
        ctypes.byref(input_data),
        ctypes.sizeof(INPUT)
    )


# =========================
# MOUSE LOOP
# =========================

running = False


def mouse_loop():

    global running

    left_click_start = None
    movement_remainder = 0.0

    while running:

        left_down = user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000

        if left_down:

            if left_click_start is None:
                left_click_start = time.perf_counter()
                movement_remainder = 0.0

            held_time = time.perf_counter() - left_click_start

            if held_time >= HOLD_TIME:

                movement_remainder += MOVE_AMOUNT

                # Send a whole pixel when enough fractional
                # movement has accumulated.
                if movement_remainder >= 1.0:

                    pixels = int(movement_remainder)

                    move_mouse_relative(0, pixels)

                    movement_remainder -= pixels

                time.sleep(MOVE_INTERVAL)

        else:

            left_click_start = None
            movement_remainder = 0.0

            time.sleep(0.005)


# =========================
# GUI COLORS
# =========================

BG = "#080b10"
PANEL = "#11161e"
PANEL_LIGHT = "#171d27"
BORDER = "#293241"

TEXT = "#f4f7fb"
SUBTEXT = "#8994a5"

ACCENT = "#4f8cff"
ACCENT_HOVER = "#6ba0ff"

GREEN = "#3ddc84"
RED = "#ff5c6c"


# =========================
# GUI
# =========================

root = tk.Tk()

root.title("NoRecoil")
root.geometry("760x680")
root.minsize(760, 680)
root.resizable(True, True)
root.configure(bg=BG)


# =========================
# BUTTON HELPER
# =========================

def create_button(parent, text, command, bg, fg=TEXT, height=2):

    button = tk.Button(
        parent,
        text=text,
        command=command,
        font=("Segoe UI", 12, "bold"),
        bg=bg,
        fg=fg,
        activebackground=ACCENT_HOVER if bg == ACCENT else "#222a36",
        activeforeground=TEXT,
        relief="flat",
        bd=0,
        cursor="hand2",
        height=height
    )

    return button


# =========================
# START
# =========================

def start_program():

    global running

    if running:
        return

    try:
        new_hold_time = float(hold_entry.get())
        new_move_amount = float(move_entry.get())

        if new_hold_time < 0:
            raise ValueError

        if new_move_amount <= 0:
            raise ValueError

        global HOLD_TIME
        global MOVE_AMOUNT

        HOLD_TIME = new_hold_time
        MOVE_AMOUNT = new_move_amount

    except ValueError:

        messagebox.showerror(
            "Invalid Settings",
            "Please enter valid positive numbers."
        )

        return

    running = True

    status_label.config(
        text="●  RUNNING",
        fg=GREEN
    )

    start_button.config(
        text="RUNNING",
        state="disabled"
    )

    hold_entry.config(state="disabled")
    move_entry.config(state="disabled")

    threading.Thread(
        target=mouse_loop,
        daemon=True
    ).start()


# =========================
# STOP
# =========================

def stop_program():

    global running

    running = False

    status_label.config(
        text="●  READY",
        fg=SUBTEXT
    )

    start_button.config(
        text="START",
        state="normal"
    )

    hold_entry.config(state="normal")
    move_entry.config(state="normal")


# =========================
# SETTINGS
# =========================

def show_settings():

    settings_window = tk.Toplevel(root)

    settings_window.title("Settings")
    settings_window.geometry("620x500")
    settings_window.resizable(False, False)
    settings_window.configure(bg=BG)

    # ---------- HEADER ----------

    header = tk.Frame(
        settings_window,
        bg=BG
    )

    header.pack(
        fill="x",
        padx=45,
        pady=(35, 20)
    )

    tk.Label(
        header,
        text="SETTINGS",
        font=("Segoe UI", 26, "bold"),
        bg=BG,
        fg=TEXT
    ).pack(anchor="w")

    tk.Label(
        header,
        text="Configure your mouse control parameters",
        font=("Segoe UI", 10),
        bg=BG,
        fg=SUBTEXT
    ).pack(
        anchor="w",
        pady=(4, 0)
    )

    # ---------- SETTINGS PANEL ----------

    panel = tk.Frame(
        settings_window,
        bg=PANEL,
        highlightbackground=BORDER,
        highlightthickness=1
    )

    panel.pack(
        padx=45,
        fill="both",
        expand=True
    )

    # ---------- HOLD TIME ----------

    tk.Label(
        panel,
        text="HOLD TIME",
        font=("Segoe UI", 12, "bold"),
        bg=PANEL,
        fg=TEXT
    ).place(
        x=35,
        y=40
    )

    tk.Label(
        panel,
        text="Time required before movement begins",
        font=("Segoe UI", 9),
        bg=PANEL,
        fg=SUBTEXT
    ).place(
        x=35,
        y=68
    )

    hold_entry_window = tk.Entry(
        panel,
        font=("Segoe UI", 12),
        bg=PANEL_LIGHT,
        fg=TEXT,
        insertbackground=TEXT,
        relief="flat",
        justify="center"
    )

    hold_entry_window.insert(
        0,
        str(HOLD_TIME)
    )

    hold_entry_window.place(
        x=390,
        y=42,
        width=130,
        height=35
    )

    # ---------- MOVE AMOUNT ----------

    tk.Label(
        panel,
        text="MOVE AMOUNT",
        font=("Segoe UI", 12, "bold"),
        bg=PANEL,
        fg=TEXT
    ).place(
        x=35,
        y=125
    )

    tk.Label(
        panel,
        text="Amount of movement applied per interval",
        font=("Segoe UI", 9),
        bg=PANEL,
        fg=SUBTEXT
    ).place(
        x=35,
        y=153
    )

    move_entry_window = tk.Entry(
        panel,
        font=("Segoe UI", 12),
        bg=PANEL_LIGHT,
        fg=TEXT,
        insertbackground=TEXT,
        relief="flat",
        justify="center"
    )

    move_entry_window.insert(
        0,
        str(MOVE_AMOUNT)
    )

    move_entry_window.place(
        x=390,
        y=127,
        width=130,
        height=35
    )

    # ---------- INTERVAL ----------

    tk.Label(
        panel,
        text="MOVE INTERVAL",
        font=("Segoe UI", 12, "bold"),
        bg=PANEL,
        fg=TEXT
    ).place(
        x=35,
        y=210
    )

    tk.Label(
        panel,
        text="Fixed system interval",
        font=("Segoe UI", 9),
        bg=PANEL,
        fg=SUBTEXT
    ).place(
        x=35,
        y=238
    )

    tk.Label(
        panel,
        text=str(MOVE_INTERVAL),
        font=("Segoe UI", 12, "bold"),
        bg=PANEL_LIGHT,
        fg=SUBTEXT
    ).place(
        x=390,
        y=212,
        width=130,
        height=35
    )

    # ---------- SAVE ----------

    def save_settings():

        global HOLD_TIME
        global MOVE_AMOUNT

        try:

            new_hold = float(
                hold_entry_window.get()
            )

            new_move = float(
                move_entry_window.get()
            )

            if new_hold < 0 or new_move <= 0:
                raise ValueError

            HOLD_TIME = new_hold
            MOVE_AMOUNT = new_move

            hold_entry.delete(
                0,
                tk.END
            )

            hold_entry.insert(
                0,
                str(HOLD_TIME)
            )

            move_entry.delete(
                0,
                tk.END
            )

            move_entry.insert(
                0,
                str(MOVE_AMOUNT)
            )

            settings_window.destroy()

        except ValueError:

            messagebox.showerror(
                "Invalid Settings",
                "Please enter valid positive numbers.",
                parent=settings_window
            )

    save_button = create_button(
        settings_window,
        "SAVE CHANGES",
        save_settings,
        ACCENT,
        height=2
    )

    save_button.pack(
        side="left",
        padx=(45, 8),
        pady=25,
        fill="x",
        expand=True
    )

    cancel_button = create_button(
        settings_window,
        "CANCEL",
        settings_window.destroy,
        PANEL_LIGHT,
        fg=TEXT,
        height=2
    )

    cancel_button.pack(
        side="right",
        padx=(8, 45),
        pady=25,
        fill="x",
        expand=True
    )


# =========================
# EXIT
# =========================

def exit_program():

    global running

    running = False
    root.destroy()


def on_close():

    global running

    running = False
    root.destroy()


# =========================
# HEADER
# =========================

header = tk.Frame(
    root,
    bg=BG
)

header.pack(
    fill="x",
    padx=60,
    pady=(55, 20)
)

tk.Label(
    header,
    text="MOUSE CONTROL",
    font=("Segoe UI", 38, "bold"),
    bg=BG,
    fg=TEXT
).pack(
    anchor="w"
)

tk.Label(
    header,
    text="PRECISION INPUT CONTROL",
    font=("Segoe UI", 11, "bold"),
    bg=BG,
    fg=ACCENT
).pack(
    anchor="w",
    pady=(5, 0)
)

tk.Label(
    header,
    text="Configure and control your mouse movement with precision.",
    font=("Segoe UI", 10),
    bg=BG,
    fg=SUBTEXT
).pack(
    anchor="w",
    pady=(8, 0)
)


# =========================
# STATUS CARD
# =========================

status_card = tk.Frame(
    root,
    bg=PANEL,
    highlightbackground=BORDER,
    highlightthickness=1
)

status_card.pack(
    padx=60,
    fill="x",
    pady=(10, 20)
)

tk.Label(
    status_card,
    text="STATUS",
    font=("Segoe UI", 9, "bold"),
    bg=PANEL,
    fg=SUBTEXT
).pack(
    anchor="w",
    padx=25,
    pady=(18, 2)
)

status_label = tk.Label(
    status_card,
    text="●  READY",
    font=("Segoe UI", 15, "bold"),
    bg=PANEL,
    fg=SUBTEXT
)

status_label.pack(
    anchor="w",
    padx=25,
    pady=(0, 18)
)


# =========================
# QUICK SETTINGS
# =========================

settings_card = tk.Frame(
    root,
    bg=PANEL,
    highlightbackground=BORDER,
    highlightthickness=1
)

settings_card.pack(
    padx=60,
    fill="x",
    pady=(0, 20)
)


tk.Label(
    settings_card,
    text="QUICK SETTINGS",
    font=("Segoe UI", 9, "bold"),
    bg=PANEL,
    fg=SUBTEXT
).pack(
    anchor="w",
    padx=25,
    pady=(18, 12)
)


# HOLD TIME

hold_row = tk.Frame(
    settings_card,
    bg=PANEL
)

hold_row.pack(
    fill="x",
    padx=25,
    pady=5
)

tk.Label(
    hold_row,
    text="Hold Time",
    font=("Segoe UI", 11, "bold"),
    bg=PANEL,
    fg=TEXT,
    width=20,
    anchor="w"
).pack(
    side="left"
)

hold_entry = tk.Entry(
    hold_row,
    font=("Segoe UI", 11),
    bg=PANEL_LIGHT,
    fg=TEXT,
    insertbackground=TEXT,
    relief="flat",
    justify="center"
)

hold_entry.insert(
    0,
    str(HOLD_TIME)
)

hold_entry.pack(
    side="right",
    ipadx=15,
    ipady=7
)


# MOVE AMOUNT

move_row = tk.Frame(
    settings_card,
    bg=PANEL
)

move_row.pack(
    fill="x",
    padx=25,
    pady=5
)

tk.Label(
    move_row,
    text="Move Amount",
    font=("Segoe UI", 11, "bold"),
    bg=PANEL,
    fg=TEXT,
    width=20,
    anchor="w"
).pack(
    side="left"
)

move_entry = tk.Entry(
    move_row,
    font=("Segoe UI", 11),
    bg=PANEL_LIGHT,
    fg=TEXT,
    insertbackground=TEXT,
    relief="flat",
    justify="center"
)

move_entry.insert(
    0,
    str(MOVE_AMOUNT)
)

move_entry.pack(
    side="right",
    ipadx=15,
    ipady=7
)


tk.Label(
    settings_card,
    text="Move Interval is fixed at 0.01",
    font=("Segoe UI", 9),
    bg=PANEL,
    fg=SUBTEXT
).pack(
    anchor="w",
    padx=25,
    pady=(8, 18)
)


# =========================
# BUTTONS
# =========================

button_frame = tk.Frame(
    root,
    bg=BG
)

button_frame.pack(
    padx=60,
    fill="x"
)


start_button = create_button(
    button_frame,
    "START",
    start_program,
    ACCENT,
    height=2
)

start_button.pack(
    side="left",
    fill="x",
    expand=True,
    padx=(0, 7)
)


settings_button = create_button(
    button_frame,
    "SETTINGS",
    show_settings,
    PANEL_LIGHT,
    height=2
)

settings_button.pack(
    side="left",
    fill="x",
    expand=True,
    padx=7
)


stop_button = create_button(
    button_frame,
    "STOP",
    stop_program,
    PANEL_LIGHT,
    fg=RED,
    height=2
)

stop_button.pack(
    side="left",
    fill="x",
    expand=True,
    padx=7
)


exit_button = create_button(
    button_frame,
    "EXIT",
    exit_program,
    PANEL_LIGHT,
    fg=RED,
    height=2
)

exit_button.pack(
    side="left",
    fill="x",
    expand=True,
    padx=(7, 0)
)


# =========================
# FOOTER
# =========================

tk.Label(
    root,
    text="Hold LEFT CLICK to activate  •  CTRL+C is not required",
    font=("Segoe UI", 9),
    bg=BG,
    fg=SUBTEXT
).pack(
    pady=22
)


# =========================
# CLOSE HANDLER
# =========================

root.protocol(
    "WM_DELETE_WINDOW",
    on_close
)


# =========================
# START GUI
# =========================

root.mainloop()