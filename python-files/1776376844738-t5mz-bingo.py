import tkinter as tk
from tkinter import messagebox
import math

# ─── Paleta de colores ────────────────────────────────────────────────────────
BG_GRAD_START   = "#0f0c29"
BG_GRAD_MID     = "#302b63"
BG_GRAD_END     = "#24243e"

CARD_NORMAL     = "#1565C0"   # azul
CARD_MARKED     = "#C62828"   # rojo
CARD_TEXT       = "#FFFFFF"
CARD_BORDER     = "#0D47A1"
CARD_BORDER_MK  = "#B71C1C"

CTRL_BG         = "#1a1a2e"
CTRL_ACCENT     = "#4f46e5"
CTRL_ACCENT_HOV = "#6366f1"
CTRL_INPUT_BG   = "#16213e"
CTRL_INPUT_FG   = "#ffffff"
CTRL_BTN_FG     = "#ffffff"
CTRL_TITLE_FG   = "#e2e8f0"
CTRL_SUBTITLE   = "#94a3b8"
CTRL_BADGE_BG   = "#0f3460"
CTRL_BADGE_FG   = "#e2e8f0"
CTRL_DEL_BG     = "#7f1d1d"
CTRL_DEL_HOV    = "#991b1b"

BOARD_W = 1920
BOARD_H = 1080
CTRL_W  = 960
CTRL_H  = 1080


class BingoApp:
    def __init__(self):
        self.marked = set()
        self.history = []

        # ── Ventana de controles ──────────────────────────────────────────────
        self.ctrl_win = tk.Tk()
        self.ctrl_win.title("BINGO — Panel de Control")
        self.ctrl_win.geometry(f"{CTRL_W}x{CTRL_H}")
        self.ctrl_win.resizable(True, True)
        self.ctrl_win.configure(bg=CTRL_BG)
        self.ctrl_win.protocol("WM_DELETE_WINDOW", self.on_close)

        # ── Ventana del talonario ─────────────────────────────────────────────
        self.board_win = tk.Toplevel(self.ctrl_win)
        self.board_win.title("BINGO — Talonario")
        self.board_win.geometry(f"{BOARD_W}x{BOARD_H}")
        self.board_win.resizable(True, True)
        self.board_win.configure(bg=BG_GRAD_START)
        self.board_win.protocol("WM_DELETE_WINDOW", self.on_close)

        self._build_board_ui()
        self._build_ctrl_ui()

        # Sincronizar cierre
        self.ctrl_win.after(100, self._position_windows)

    def _position_windows(self):
        sw = self.ctrl_win.winfo_screenwidth()
        sh = self.ctrl_win.winfo_screenheight()
        # Panel de control centrado
        cx = (sw - CTRL_W) // 2
        cy = (sh - CTRL_H) // 2
        self.ctrl_win.geometry(f"{CTRL_W}x{CTRL_H}+{cx}+{cy}")
        # Talonario centrado en pantalla secundaria (o desplazado)
        bx = max(0, (sw - BOARD_W) // 2)
        by = max(0, (sh - BOARD_H) // 2)
        self.board_win.geometry(f"{BOARD_W}x{BOARD_H}+{bx}+{by}")

    # ─────────────────────────────────────────────────────────────────────────
    #  TALONARIO
    # ─────────────────────────────────────────────────────────────────────────
    def _build_board_ui(self):
        win = self.board_win

        # Canvas para fondo degradado
        self.board_canvas = tk.Canvas(win, highlightthickness=0, bg=BG_GRAD_START)
        self.board_canvas.pack(fill="both", expand=True)
        self.board_canvas.bind("<Configure>", self._redraw_board)

        # Frame contenedor sobre el canvas
        self.board_frame = tk.Frame(self.board_canvas, bg=BG_GRAD_START)
        self.board_canvas.create_window(0, 0, anchor="nw", window=self.board_frame,
                                        tags="container")

        self.board_frame.bind("<Configure>", self._on_frame_configure)

        self._build_grid()

    def _on_frame_configure(self, event):
        self.board_canvas.configure(scrollregion=self.board_canvas.bbox("all"))
        # Centrar el frame en el canvas
        cw = self.board_canvas.winfo_width()
        fw = self.board_frame.winfo_width()
        x = max(0, (cw - fw) // 2)
        self.board_canvas.coords("container", x, 20)

    def _redraw_board(self, event=None):
        w = self.board_canvas.winfo_width()
        h = self.board_canvas.winfo_height()
        self._draw_gradient(self.board_canvas, w, h)
        # Recentrar
        fw = self.board_frame.winfo_reqwidth()
        x = max(0, (w - fw) // 2)
        self.board_canvas.coords("container", x, 20)

    def _draw_gradient(self, canvas, w, h):
        canvas.delete("grad")
        steps = 60
        for i in range(steps):
            t = i / steps
            if t < 0.5:
                r = self._lerp_color(BG_GRAD_START, BG_GRAD_MID, t * 2)
            else:
                r = self._lerp_color(BG_GRAD_MID, BG_GRAD_END, (t - 0.5) * 2)
            y0 = int(h * i / steps)
            y1 = int(h * (i + 1) / steps)
            canvas.create_rectangle(0, y0, w, y1, fill=r, outline=r, tags="grad")
        canvas.tag_lower("grad")

    def _lerp_color(self, c1, c2, t):
        def hx(c):
            c = c.lstrip("#")
            return tuple(int(c[i:i+2], 16) for i in (0, 2, 4))
        r1, g1, b1 = hx(c1)
        r2, g2, b2 = hx(c2)
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _build_grid(self):
        for w in self.board_frame.winfo_children():
            w.destroy()
        self.cells = {}

        COLS = 10
        ROWS = 9
        CELL_W = 160
        CELL_H = 100
        FONT_N = ("Segoe UI", 34, "bold")

        for i, num in enumerate(range(1, 91)):
            row = i // COLS
            col = i % COLS
            bg = CARD_MARKED if num in self.marked else CARD_NORMAL
            border = CARD_BORDER_MK if num in self.marked else CARD_BORDER

            outer = tk.Frame(self.board_frame, bg=border, padx=2, pady=2)
            outer.grid(row=row, column=col, padx=4, pady=4)

            inner = tk.Frame(outer, bg=bg, width=CELL_W, height=CELL_H)
            inner.pack_propagate(False)
            inner.pack()

            lbl = tk.Label(inner, text=str(num), bg=bg, fg=CARD_TEXT,
                           font=FONT_N, anchor="center")
            lbl.place(relx=0.5, rely=0.5, anchor="center")

            self.cells[num] = (outer, inner, lbl, border)

    def _update_cell(self, num):
        if num not in self.cells:
            return
        outer, inner, lbl, _ = self.cells[num]
        if num in self.marked:
            bg = CARD_MARKED
            border = CARD_BORDER_MK
        else:
            bg = CARD_NORMAL
            border = CARD_BORDER
        outer.configure(bg=border)
        inner.configure(bg=bg)
        lbl.configure(bg=bg)
        self.cells[num] = (outer, inner, lbl, border)

    # ─────────────────────────────────────────────────────────────────────────
    #  PANEL DE CONTROLES
    # ─────────────────────────────────────────────────────────────────────────
    def _build_ctrl_ui(self):
        win = self.ctrl_win

        # Canvas fondo degradado
        self.ctrl_canvas = tk.Canvas(win, highlightthickness=0, bg=CTRL_BG)
        self.ctrl_canvas.pack(fill="both", expand=True)
        self.ctrl_canvas.bind("<Configure>", self._redraw_ctrl_bg)

        self.ctrl_overlay = tk.Frame(self.ctrl_canvas, bg=CTRL_BG)
        self.ctrl_canvas.create_window(0, 0, anchor="nw",
                                       window=self.ctrl_overlay, tags="overlay")
        self.ctrl_overlay.bind("<Configure>",
                               lambda e: self.ctrl_canvas.coords(
                                   "overlay",
                                   max(0, (self.ctrl_canvas.winfo_width()
                                           - self.ctrl_overlay.winfo_reqwidth()) // 2),
                                   0))

        self._build_ctrl_content()

    def _redraw_ctrl_bg(self, event=None):
        w = self.ctrl_canvas.winfo_width()
        h = self.ctrl_canvas.winfo_height()
        self._draw_gradient(self.ctrl_canvas, w, h)
        self.ctrl_canvas.tag_lower("grad")
        fw = self.ctrl_overlay.winfo_reqwidth()
        x = max(0, (w - fw) // 2)
        self.ctrl_canvas.coords("overlay", x, 0)

    def _build_ctrl_content(self):
        f = self.ctrl_overlay
        f.configure(bg="", highlightthickness=0)
        PAD = 40

        # ── Título ────────────────────────────────────────────────────────────
        title_frame = tk.Frame(f, bg="#00000000")
        title_frame.pack(pady=(60, 4))

        tk.Label(title_frame, text="🎱  BINGO",
                 font=("Segoe UI", 72, "bold"),
                 fg="#ffffff", bg=CTRL_BG).pack()

        tk.Label(f, text="Panel de Control",
                 font=("Segoe UI", 18),
                 fg=CTRL_SUBTITLE, bg=CTRL_BG).pack(pady=(0, 40))

        # ── Separador ─────────────────────────────────────────────────────────
        sep = tk.Frame(f, height=1, width=500, bg="#4f46e5")
        sep.pack(pady=(0, 40))

        # ── Contador marcados ─────────────────────────────────────────────────
        self.badge_var = tk.StringVar(value="0 / 90  marcados")
        badge_lbl = tk.Label(f, textvariable=self.badge_var,
                             font=("Segoe UI", 14, "bold"),
                             fg=CTRL_BADGE_FG, bg=CTRL_BADGE_BG,
                             padx=24, pady=8)
        badge_lbl.pack(pady=(0, 30))
        badge_lbl.configure(relief="flat", bd=0)

        # ── Input + botón Enviar ──────────────────────────────────────────────
        input_frame = tk.Frame(f, bg=CTRL_BG)
        input_frame.pack(pady=(0, 16))

        tk.Label(input_frame, text="Número (1–90)",
                 font=("Segoe UI", 13), fg=CTRL_SUBTITLE,
                 bg=CTRL_BG).grid(row=0, column=0, columnspan=2,
                                  pady=(0, 8))

        self.num_var = tk.StringVar()
        self.entry = tk.Entry(input_frame, textvariable=self.num_var,
                              font=("Segoe UI", 28, "bold"),
                              width=6, justify="center",
                              bg=CTRL_INPUT_BG, fg=CTRL_INPUT_FG,
                              insertbackground=CTRL_INPUT_FG,
                              relief="flat", bd=0,
                              highlightthickness=2,
                              highlightbackground=CTRL_ACCENT,
                              highlightcolor=CTRL_ACCENT_HOV)
        self.entry.grid(row=1, column=0, padx=(0, 12), ipady=14)
        self.entry.bind("<Return>", lambda e: self.mark_number())
        self.entry.focus()

        self.btn_send = tk.Button(input_frame, text="✔  Marcar",
                                  font=("Segoe UI", 16, "bold"),
                                  fg=CTRL_BTN_FG, bg=CTRL_ACCENT,
                                  activebackground=CTRL_ACCENT_HOV,
                                  activeforeground="#fff",
                                  relief="flat", bd=0,
                                  padx=28, pady=14,
                                  cursor="hand2",
                                  command=self.mark_number)
        self.btn_send.grid(row=1, column=1)
        self._hover(self.btn_send, CTRL_ACCENT, CTRL_ACCENT_HOV)

        # ── Botón Borrar último ───────────────────────────────────────────────
        self.btn_undo = tk.Button(f, text="↩  Borrar último número",
                                  font=("Segoe UI", 14),
                                  fg=CTRL_BTN_FG, bg=CTRL_DEL_BG,
                                  activebackground=CTRL_DEL_HOV,
                                  activeforeground="#fff",
                                  relief="flat", bd=0,
                                  padx=24, pady=12,
                                  cursor="hand2",
                                  command=self.undo_last)
        self.btn_undo.pack(pady=(0, 30))
        self._hover(self.btn_undo, CTRL_DEL_BG, CTRL_DEL_HOV)

        # ── Botón Reiniciar ───────────────────────────────────────────────────
        self.btn_reset = tk.Button(f, text="⟳  Reiniciar partida",
                                   font=("Segoe UI", 13),
                                   fg="#94a3b8", bg="#1e293b",
                                   activebackground="#334155",
                                   activeforeground="#fff",
                                   relief="flat", bd=0,
                                   padx=20, pady=10,
                                   cursor="hand2",
                                   command=self.reset_all)
        self.btn_reset.pack(pady=(0, 40))

        # ── Separador ─────────────────────────────────────────────────────────
        sep2 = tk.Frame(f, height=1, width=500, bg="#334155")
        sep2.pack(pady=(0, 20))

        # ── Últimos números marcados ──────────────────────────────────────────
        tk.Label(f, text="Últimos números marcados",
                 font=("Segoe UI", 13, "bold"),
                 fg=CTRL_SUBTITLE, bg=CTRL_BG).pack(pady=(0, 12))

        self.history_frame = tk.Frame(f, bg=CTRL_BG)
        self.history_frame.pack(pady=(0, 20))

        self.status_var = tk.StringVar(value="")
        self.status_lbl = tk.Label(f, textvariable=self.status_var,
                                   font=("Segoe UI", 13),
                                   fg="#f87171", bg=CTRL_BG)
        self.status_lbl.pack()

        self._refresh_history_display()

    def _hover(self, btn, normal, hover):
        btn.bind("<Enter>", lambda e: btn.configure(bg=hover))
        btn.bind("<Leave>", lambda e: btn.configure(bg=normal))

    # ─────────────────────────────────────────────────────────────────────────
    #  LÓGICA
    # ─────────────────────────────────────────────────────────────────────────
    def mark_number(self):
        raw = self.num_var.get().strip()
        self.status_var.set("")
        if not raw.isdigit():
            self.status_var.set("⚠ Ingresá un número válido")
            return
        n = int(raw)
        if not (1 <= n <= 90):
            self.status_var.set("⚠ El número debe estar entre 1 y 90")
            return
        if n in self.marked:
            self.status_var.set(f"⚠ El {n} ya fue marcado")
            return

        self.marked.add(n)
        self.history.append(n)
        self._update_cell(n)
        self.num_var.set("")
        self.entry.focus()
        self._refresh_badge()
        self._refresh_history_display()

    def undo_last(self):
        if not self.history:
            self.status_var.set("No hay números para borrar")
            return
        n = self.history.pop()
        self.marked.discard(n)
        self._update_cell(n)
        self.status_var.set(f"Se borró el número {n}")
        self._refresh_badge()
        self._refresh_history_display()

    def reset_all(self):
        if not messagebox.askyesno("Reiniciar",
                                   "¿Reiniciar la partida? Se borrarán todos los números marcados."):
            return
        self.marked.clear()
        self.history.clear()
        self._build_grid()
        self._refresh_badge()
        self._refresh_history_display()
        self.status_var.set("Partida reiniciada")

    def _refresh_badge(self):
        self.badge_var.set(f"{len(self.marked)} / 90  marcados")

    def _refresh_history_display(self):
        for w in self.history_frame.winfo_children():
            w.destroy()

        recent = self.history[-10:][::-1]
        for i, n in enumerate(recent):
            alpha = 1.0 - i * 0.07
            # Simular opacidad con mezcla de colores
            bg = self._lerp_color(CTRL_BG, CARD_MARKED, max(0.15, alpha * 0.4))
            lbl = tk.Label(self.history_frame, text=str(n),
                           font=("Segoe UI", 15, "bold"),
                           fg="#ffffff", bg=bg,
                           width=4, pady=4, relief="flat")
            lbl.pack(side="left", padx=4)

    def on_close(self):
        self.ctrl_win.destroy()

    def run(self):
        self.ctrl_win.mainloop()


if __name__ == "__main__":
    app = BingoApp()
    app.run()
