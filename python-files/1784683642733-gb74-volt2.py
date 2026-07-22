import tkinter as tk

root = tk.Tk()
root.title("Volt")
root.geometry("600x400")
root.configure(bg="#5B21B6")
root.resizable(False, False)

frame = tk.Frame(root, bg="#5B21B6")
frame.place(relx=0.5, rely=0.5, anchor="center")

title = tk.Label(
    frame,
    text="VOLT",
    font=("Segoe UI", 30, "bold"),
    fg="white",
    bg="#5B21B6"
)
title.pack(pady=(0, 20))

message = tk.Label(
    frame,
    text="Please Share The Executor To 2 People To Unlock The Executor.",
    font=("Segoe UI", 14),
    fg="white",
    bg="#5B21B6"
)
message.pack(pady=(0, 25))


# ===== ADD SECOND SCRIPT HERE =====

SHARE_LINK = "https://github.com/opscriptss2/Volt-Executor"

link_label = tk.Label(
    frame,
    text="Share Link",
    font=("Segoe UI", 11, "bold"),
    fg="white",
    bg="#5B21B6"
)
link_label.pack()

link_box = tk.Entry(
    frame,
    width=50,
    font=("Segoe UI", 10),
    justify="center"
)
link_box.pack(pady=(5, 10))

link_box.insert(0, SHARE_LINK)
link_box.config(state="readonly")


def copy_link():
    root.clipboard_clear()
    root.clipboard_append(SHARE_LINK)
    root.update()

    copy_status.config(
        text="✓ Copied!",
        fg="#00FF66"
    )

    root.after(
        1500,
        lambda: copy_status.config(text="")
    )


copy_btn = tk.Button(
    frame,
    text="📋 Copy Link",
    command=copy_link,
    font=("Segoe UI", 11, "bold"),
    bg="#7C3AED",
    fg="white",
    relief="flat",
    cursor="hand2"
)
copy_btn.pack()


copy_status = tk.Label(
    frame,
    text="",
    font=("Segoe UI", 10),
    fg="white",
    bg="#5B21B6"
)
copy_status.pack(pady=(5, 15))


# ===== YOUR ORIGINAL CHECK CODE CONTINUES HERE =====

status = tk.Label(
    frame,
    text="",
    font=("Segoe UI", 13, "bold"),
    fg="white",
    bg="#5B21B6"
)
status.pack(pady=(0, 20))


def check():
    check_btn.config(state="disabled")

    frames = [
        "Checking",
        "Checking.",
        "Checking..",
        "Checking..."
    ]

    index = 0
    running = True

    def animate():
        nonlocal index, running

        if not running:
            return

        status.config(
            text=frames[index],
            fg="#00FF66"
        )

        index = (index + 1) % len(frames)
        root.after(350, animate)

    animate()

    def finish():
        nonlocal running

        running = False

        status.config(
            text="❌ Invalid please make sure they have downloaded and opened it",
            fg="#FF5555"
        )

        check_btn.config(state="normal")

    root.after(4000, finish)


check_btn = tk.Button(
    frame,
    text="CHECK",
    command=check,
    font=("Segoe UI", 14, "bold"),
    bg="#7C3AED",
    fg="white",
    activebackground="#8B5CF6",
    activeforeground="white",
    relief="flat",
    width=16,
    height=2,
    cursor="hand2"
)

check_btn.pack()


root.mainloop()
