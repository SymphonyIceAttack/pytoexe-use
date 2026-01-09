import customtkinter as ctk
from pypresence import Presence
import threading
import time

rpc = None
running = False

def run_rpc():
    global rpc, running

    client_id = entry_client_id.get().strip()

    if not client_id:
        status_label.configure(
            text="❌ Chưa nhập CLIENT ID",
            text_color="red"
        )
        return

    try:
        rpc = Presence(client_id)
        rpc.connect()

        # ⚠️ BẮT BUỘC PHẢI UPDATE – nếu không Discord không hiện
        rpc.update(
            details="MAKE BY VYRONIX",
            state="VYRONIX ĐẸP TRAI NHẤT THẾ GIỚI"
        )

        running = True
        status_label.configure(
            text="✅ RPC đang chạy\nDiscord đã nhận activity",
            text_color="green"
        )

        # giữ process sống
        while running:
            time.sleep(1)

    except Exception as e:
        status_label.configure(
            text=f"❌ RPC lỗi:\n{e}",
            text_color="red"
        )

def on_accept():
    threading.Thread(target=run_rpc, daemon=True).start()

# ===== UI =====
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Discord RPC Status")
app.geometry("480x300")
app.resizable(False, False)

ctk.CTkLabel(
    app,
    text="Discord RPC Launcher",
    font=("Segoe UI", 20, "bold")
).pack(pady=15)

entry_client_id = ctk.CTkEntry(
    app,
    placeholder_text="Nhập Discord Application CLIENT ID"
)
entry_client_id.pack(padx=30, pady=10, fill="x")

ctk.CTkButton(
    app,
    text="Accept & Run",
    command=on_accept
).pack(pady=15)

status_label = ctk.CTkLabel(
    app,
    text="Nhập CLIENT ID rồi bấm Accept",
    wraplength=420,
    justify="center"
)
status_label.pack(pady=10)

app.mainloop()
