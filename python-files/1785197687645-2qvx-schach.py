# -*- coding: utf-8 -*-
"""
Schach fuer Windows - eigenstaendiges Spiel mit eigener Engine.
Enthaelt: 2D-Brett (Holzoptik), Figuren in Marmor-Optik, Mensch-vs-Mensch
und Mensch-vs-Computer, Zugliste mit Navigation, Rueckgaengig/Wiederholen,
Partie-Analyse nach Spielende, Speichern der Statistik als .txt.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import datetime
import os

from chess_engine import (
    ChessState, ChessAI, to_san, analyze_game, square_name,
    WHITE, BLACK, opponent, LearningMemory, train_self_play, LEARN_PLIES,
)
from tkinter import simpledialog

# ---------- Farben ----------
TITLE_BG = "#ffffff"        # weisse Menueleiste, wie gewuenscht
TITLE_FG = "#222222"
CLOSE_RED = "#e81123"
APP_BG = "#f4f1ea"

LIGHT_SQ = "#e8c99b"        # helles Holz
DARK_SQ = "#8b5a2b"         # dunkles Holz
SELECT_COLOR = "#ffef5c"
MOVE_HINT_COLOR = "#5c9c5c"
CHECK_COLOR = "#e05a5a"

WHITE_PIECE_FILL = "#f7f5f0"     # helle Marmor-Optik
WHITE_PIECE_OUTLINE = "#555555"
BLACK_PIECE_FILL = "#2b2b2e"     # dunkle Marmor-Optik
BLACK_PIECE_OUTLINE = "#9a9a9a"

UNICODE_PIECES = {
    "K": "\u2654", "Q": "\u2655", "R": "\u2656", "B": "\u2657", "N": "\u2658", "P": "\u2659",
    "k": "\u265A", "q": "\u265B", "r": "\u265C", "b": "\u265D", "n": "\u265E", "p": "\u265F",
}

SQUARE_SIZE = 64
BOARD_PIXELS = SQUARE_SIZE * 8

DIFFICULTIES = {"Leicht": 2, "Mittel": 3, "Schwer": 4}


class ChessApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.overrideredirect(True)
        self.geometry("980x700+250+80")
        self.configure(bg=APP_BG)
        self.resizable(False, False)

        self.state_ = None
        self.ai = None
        self.memory = LearningMemory()  # persistenter Lernspeicher (schach_lernen.json)
        self.mode = None            # "computer" oder "mensch"
        self.human_color = WHITE
        self.selected_sq = None
        self.legal_targets = []
        self.view_ptr = 0           # wie viele Zuege aus der Historie aktuell sichtbar sind
        self.game_over_shown = False

        self._build_titlebar()
        self.container = tk.Frame(self, bg=APP_BG)
        self.container.pack(fill="both", expand=True)

        self._offset_x = 0
        self._offset_y = 0
        self.titlebar.bind("<Button-1>", self._start_move)
        self.titlebar.bind("<B1-Motion>", self._do_move)

        self._show_menu()

    # ---------- Fensterrahmen ----------
    def _build_titlebar(self):
        self.titlebar = tk.Frame(self, bg=TITLE_BG, height=32)
        self.titlebar.pack(side="top", fill="x")
        tk.Label(
            self.titlebar, text="Schach", bg=TITLE_BG, fg=TITLE_FG,
            font=("Tahoma", 11, "bold")
        ).pack(side="left", padx=10)
        close_btn = tk.Button(
            self.titlebar, text="X", bg=CLOSE_RED, fg="white",
            font=("Tahoma", 10, "bold"), width=4, bd=0,
            activebackground="#ff4444", activeforeground="white",
            command=self.destroy, cursor="hand2"
        )
        close_btn.pack(side="right", padx=4, pady=3)

    def _start_move(self, event):
        self._offset_x, self._offset_y = event.x, event.y

    def _do_move(self, event):
        x = self.winfo_pointerx() - self._offset_x
        y = self.winfo_pointery() - self._offset_y
        self.geometry(f"+{x}+{y}")

    def _clear_container(self):
        for w in self.container.winfo_children():
            w.destroy()

    def _open_training_dialog(self):
        n = simpledialog.askinteger(
            "Training", "Wie viele Partien soll die KI gegen sich selbst spielen?\n"
                        "(mehr Partien = längeres Training, z. B. 20-50)",
            initialvalue=20, minvalue=1, maxvalue=300, parent=self
        )
        if not n:
            return

        win = tk.Toplevel(self)
        win.title("Training läuft...")
        win.geometry("360x120")
        win.configure(bg="#ffffff")
        win.transient(self)
        label = tk.Label(win, text="Training startet...", bg="#ffffff", font=("Tahoma", 11))
        label.pack(pady=20)
        detail = tk.Label(win, text="", bg="#ffffff", fg="#666666", font=("Tahoma", 9))
        detail.pack()

        def progress(g, total, result):
            label.config(text=f"Partie {g} von {total} gespielt")
            detail.config(text=f"Letztes Ergebnis: {result}")
            win.update_idletasks()

        train_self_play(self.memory, num_games=n, depth=2, analyze_depth=1, progress_callback=progress)
        win.destroy()
        messagebox.showinfo(
            "Training fertig",
            f"{n} Trainingspartien gespielt.\nInsgesamt trainierte Partien: {self.memory.games_trained}"
        )
        self._show_menu()

    # ---------- Menue ----------
    def _show_menu(self):
        self._clear_container()
        tk.Label(
            self.container, text="Schach", bg=APP_BG, fg="#333333",
            font=("Georgia", 32, "bold")
        ).pack(pady=(50, 10))
        tk.Label(
            self.container, text="Wähle einen Modus", bg=APP_BG, fg="#555555",
            font=("Tahoma", 12)
        ).pack(pady=(0, 25))

        self.mode_var = tk.StringVar(value="mensch")
        mode_frame = tk.Frame(self.container, bg=APP_BG)
        mode_frame.pack(pady=5)
        tk.Radiobutton(
            mode_frame, text="Mensch gegen Mensch", variable=self.mode_var, value="mensch",
            bg=APP_BG, font=("Tahoma", 11), command=self._toggle_difficulty
        ).pack(anchor="w", pady=3)
        tk.Radiobutton(
            mode_frame, text="Mensch gegen Computer", variable=self.mode_var, value="computer",
            bg=APP_BG, font=("Tahoma", 11), command=self._toggle_difficulty
        ).pack(anchor="w", pady=3)

        self.diff_frame = tk.Frame(self.container, bg=APP_BG)
        self.diff_frame.pack(pady=15)
        tk.Label(self.diff_frame, text="Schwierigkeit:", bg=APP_BG, font=("Tahoma", 10)).grid(row=0, column=0, padx=5)
        self.diff_var = tk.StringVar(value="Mittel")
        for i, d in enumerate(DIFFICULTIES):
            tk.Radiobutton(
                self.diff_frame, text=d, variable=self.diff_var, value=d,
                bg=APP_BG, font=("Tahoma", 10)
            ).grid(row=0, column=i + 1, padx=5)
        self._set_diff_state("disabled")

        self.color_frame = tk.Frame(self.container, bg=APP_BG)
        self.color_frame.pack(pady=5)
        tk.Label(self.color_frame, text="Deine Farbe:", bg=APP_BG, font=("Tahoma", 10)).grid(row=0, column=0, padx=5)
        self.color_var = tk.StringVar(value="Weiß")
        tk.Radiobutton(self.color_frame, text="Weiß", variable=self.color_var, value="Weiß",
                        bg=APP_BG, font=("Tahoma", 10)).grid(row=0, column=1, padx=5)
        tk.Radiobutton(self.color_frame, text="Schwarz", variable=self.color_var, value="Schwarz",
                        bg=APP_BG, font=("Tahoma", 10)).grid(row=0, column=2, padx=5)

        tk.Button(
            self.container, text="Spiel starten", font=("Tahoma", 13, "bold"),
            bg="#4a7a4a", fg="white", width=18, height=2, bd=0, cursor="hand2",
            command=self._start_game
        ).pack(pady=15)

        tk.Button(
            self.container, text="KI trainieren (Selbstspiel)", font=("Tahoma", 10),
            bg="#3a6ea5", fg="white", width=24, bd=0, cursor="hand2",
            command=self._open_training_dialog
        ).pack(pady=(0, 10))
        tk.Label(
            self.container,
            text=f"Bisher trainierte Partien: {self.memory.games_trained}",
            bg=APP_BG, fg="#777777", font=("Tahoma", 9)
        ).pack()

    def _toggle_difficulty(self):
        self._set_diff_state("normal" if self.mode_var.get() == "computer" else "disabled")

    def _set_diff_state(self, state):
        for child in self.diff_frame.winfo_children():
            try:
                child.configure(state=state)
            except tk.TclError:
                pass

    def _start_game(self):
        self.mode = self.mode_var.get()
        self.human_color = WHITE if self.color_var.get() == "Weiß" else BLACK
        depth = DIFFICULTIES[self.diff_var.get()]
        self.ai = ChessAI(depth=depth)
        self.state_ = ChessState()
        self.selected_sq = None
        self.legal_targets = []
        self.view_ptr = 0
        self.game_over_shown = False
        self._show_board_screen()
        if self.mode == "computer" and self.human_color == BLACK:
            self.after(400, self._computer_turn)

    # ---------- Spielbildschirm ----------
    def _show_board_screen(self):
        self._clear_container()

        main = tk.Frame(self.container, bg=APP_BG)
        main.pack(fill="both", expand=True, padx=10, pady=10)

        left = tk.Frame(main, bg=APP_BG)
        left.pack(side="left", padx=(0, 10))

        self.status_label = tk.Label(
            left, text="", bg=APP_BG, fg="#333333", font=("Tahoma", 13, "bold")
        )
        self.status_label.pack(pady=(0, 6))

        self.canvas = tk.Canvas(left, width=BOARD_PIXELS + 30, height=BOARD_PIXELS + 30,
                                 bg=APP_BG, highlightthickness=0)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self._on_board_click)

        right = tk.Frame(main, bg=APP_BG, width=280)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        tk.Label(right, text="Züge", bg=APP_BG, font=("Tahoma", 12, "bold")).pack(anchor="w")
        list_frame = tk.Frame(right, bg=APP_BG)
        list_frame.pack(fill="both", expand=True, pady=5)
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        self.move_listbox = tk.Listbox(
            list_frame, yscrollcommand=scrollbar.set, font=("Consolas", 11),
            activestyle="dotbox"
        )
        self.move_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.move_listbox.yview)
        self.move_listbox.bind("<<ListboxSelect>>", self._on_move_select)

        nav = tk.Frame(right, bg=APP_BG)
        nav.pack(pady=6)
        tk.Button(nav, text="|<", width=4, command=self._nav_start).grid(row=0, column=0, padx=2)
        tk.Button(nav, text="<", width=4, command=self._nav_back).grid(row=0, column=1, padx=2)
        tk.Button(nav, text=">", width=4, command=self._nav_forward).grid(row=0, column=2, padx=2)
        tk.Button(nav, text=">|", width=4, command=self._nav_end).grid(row=0, column=3, padx=2)

        ctrl = tk.Frame(right, bg=APP_BG)
        ctrl.pack(pady=10, fill="x")
        tk.Button(ctrl, text="Neustart", bg="#4a7a4a", fg="white", bd=0,
                  command=self._start_game).pack(fill="x", pady=2)
        tk.Button(ctrl, text="Zurück zum Menü", bg="#888888", fg="white", bd=0,
                  command=self._show_menu).pack(fill="x", pady=2)
        self.analyze_btn = tk.Button(ctrl, text="Partie analysieren", bg="#3a6ea5", fg="white", bd=0,
                                      state="disabled", command=self._show_analysis)
        self.analyze_btn.pack(fill="x", pady=2)
        tk.Button(ctrl, text="Statistik als TXT speichern", bg="#a5763a", fg="white", bd=0,
                  command=self._save_stats).pack(fill="x", pady=2)

        self._redraw_board()
        self._update_status()

    # ---------- Brett zeichnen ----------
    def _redraw_board(self):
        self.canvas.delete("all")
        board = self.state_.board
        king_in_check_sq = None
        if self.state_.in_check(self.state_.turn):
            king_in_check_sq = self.state_.find_king(self.state_.turn)

        for r in range(8):
            for c in range(8):
                x0 = c * SQUARE_SIZE + 15
                y0 = (7 - r) * SQUARE_SIZE + 15
                x1, y1 = x0 + SQUARE_SIZE, y0 + SQUARE_SIZE
                color = LIGHT_SQ if (r + c) % 2 == 1 else DARK_SQ
                if self.selected_sq == (r, c):
                    color = SELECT_COLOR
                self.canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="")
                if king_in_check_sq == (r, c):
                    self.canvas.create_rectangle(x0, y0, x1, y1, outline=CHECK_COLOR, width=4)

                piece = board[r][c]
                if piece:
                    is_white = piece.isupper()
                    fill = WHITE_PIECE_FILL if is_white else BLACK_PIECE_FILL
                    outline = WHITE_PIECE_OUTLINE if is_white else BLACK_PIECE_OUTLINE
                    cx, cy = x0 + SQUARE_SIZE / 2, y0 + SQUARE_SIZE / 2
                    glyph = UNICODE_PIECES[piece]
                    # Pseudo-Kontur fuer Marmor-Look: Umriss leicht versetzt, dann Fuellung
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        self.canvas.create_text(cx + dx, cy + dy, text=glyph,
                                                 font=("Segoe UI Symbol", 40), fill=outline)
                    self.canvas.create_text(cx, cy, text=glyph, font=("Segoe UI Symbol", 40), fill=fill)

                if (r, c) in self.legal_targets:
                    cx, cy = x0 + SQUARE_SIZE / 2, y0 + SQUARE_SIZE / 2
                    self.canvas.create_oval(cx - 10, cy - 10, cx + 10, cy + 10,
                                             fill=MOVE_HINT_COLOR, outline="")

        for c in range(8):
            self.canvas.create_text(c * SQUARE_SIZE + 15 + SQUARE_SIZE / 2, BOARD_PIXELS + 22,
                                     text="abcdefgh"[c], font=("Tahoma", 9), fill="#555555")
        for r in range(8):
            self.canvas.create_text(6, (7 - r) * SQUARE_SIZE + 15 + SQUARE_SIZE / 2,
                                     text=str(r + 1), font=("Tahoma", 9), fill="#555555")

    def _update_status(self):
        if self.state_.is_checkmate():
            winner = "Schwarz" if self.state_.turn == WHITE else "Weiß"
            self.status_label.config(text=f"Schachmatt! {winner} gewinnt.")
            self._on_game_over()
        elif self.state_.is_stalemate():
            self.status_label.config(text="Patt – Unentschieden.")
            self._on_game_over()
        else:
            player = "Weiß" if self.state_.turn == WHITE else "Schwarz"
            check_txt = " (Schach!)" if self.state_.in_check(self.state_.turn) else ""
            self.status_label.config(text=f"{player} ist am Zug{check_txt}")

    def _on_game_over(self):
        if not self.game_over_shown:
            self.game_over_shown = True
            self.analyze_btn.config(state="normal")
            self._learn_from_finished_game()

    def _learn_from_finished_game(self):
        if self.mode != "computer" or not self.state_.history:
            return
        computer_color = opponent(self.human_color)
        san_history = [getattr(m, "san", "?") for m, _snap in self.state_.history]

        if self.state_.is_checkmate():
            winner = opponent(self.state_.turn)  # wer zuletzt gezogen hat, hat matt gesetzt
            result_value = 1.0 if winner == computer_color else -1.0
        else:
            result_value = 0.0  # Patt / Remis

        analysis = analyze_game(self.state_.history, depth=1)
        mistakes = {}
        penalty_map = {"Ungenauigkeit": 0.3, "Fehler": 0.6, "Grober Fehler": 1.0}
        for r in analysis:
            if r["mover"] == computer_color:
                penalty = penalty_map.get(r["tag"], 0.0)
                if penalty:
                    mistakes[r["ply"] - 1] = penalty

        self.memory.update_from_game(san_history, computer_color, result_value, mistakes)
        self.memory.save()

    # ---------- Zugliste ----------
    def _refresh_move_list(self):
        self.move_listbox.delete(0, tk.END)
        entries = []
        buffer = None
        for i, (move, _snap) in enumerate(self.state_.history):
            san = getattr(move, "san", None) or "?"
            if i % 2 == 0:
                buffer = f"{i // 2 + 1}. {san}"
            else:
                buffer += f"   {san}"
                entries.append(buffer)
                buffer = None
        if buffer:
            entries.append(buffer)
        for e in entries:
            self.move_listbox.insert(tk.END, e)
        self.move_listbox.yview_moveto(1.0)

    # ---------- Interaktion Brett ----------
    def _on_board_click(self, event):
        if self.state_.redo_stack:
            return  # im Wiedergabe-Modus keine neuen Zuege erlauben
        if self.state_.is_checkmate() or self.state_.is_stalemate():
            return
        if self.mode == "computer" and self.state_.turn != self.human_color:
            return

        col = (event.x - 15) // SQUARE_SIZE
        row = 7 - (event.y - 15) // SQUARE_SIZE
        if not (0 <= row <= 7 and 0 <= col <= 7):
            return

        piece = self.state_.board[row][col]
        if self.selected_sq is None:
            if piece and self._piece_color(piece) == self.state_.turn:
                self.selected_sq = (row, col)
                self.legal_targets = [
                    (m.tr, m.tc) for m in self.state_.legal_moves()
                    if (m.fr, m.fc) == (row, col)
                ]
        else:
            if (row, col) == self.selected_sq:
                self.selected_sq = None
                self.legal_targets = []
            elif piece and self._piece_color(piece) == self.state_.turn:
                self.selected_sq = (row, col)
                self.legal_targets = [
                    (m.tr, m.tc) for m in self.state_.legal_moves()
                    if (m.fr, m.fc) == (row, col)
                ]
            elif (row, col) in self.legal_targets:
                self._make_human_move(self.selected_sq, (row, col))
                self.selected_sq = None
                self.legal_targets = []
            else:
                self.selected_sq = None
                self.legal_targets = []

        self._redraw_board()

    @staticmethod
    def _piece_color(piece):
        return WHITE if piece.isupper() else BLACK

    def _make_human_move(self, frm, to):
        candidates = [
            m for m in self.state_.legal_moves()
            if (m.fr, m.fc) == frm and (m.tr, m.tc) == to
        ]
        if not candidates:
            return
        move = candidates[0]
        if move.promotion and move.promotion != "Q":
            for m in candidates:
                if m.promotion == "Q":
                    move = m
                    break
        legal_before = self.state_.legal_moves()
        move.san = to_san(self.state_, move, legal_before)
        self.state_.make_move(move, record=True)
        self._after_move()

    def _after_move(self):
        self._refresh_move_list()
        self._redraw_board()
        self._update_status()
        if self.mode == "computer" and not self.state_.is_checkmate() and not self.state_.is_stalemate():
            if self.state_.turn != self.human_color:
                self.after(300, self._computer_turn)

    def _computer_turn(self):
        if self.state_.is_checkmate() or self.state_.is_stalemate():
            return
        legal_before = self.state_.legal_moves()
        san_prefix = [getattr(m, "san", "?") for m, _snap in self.state_.history]
        move, _score = self.ai.choose_move(self.state_, memory=self.memory, san_prefix=san_prefix)
        if move is None:
            return
        move.san = to_san(self.state_, move, legal_before)
        self.state_.make_move(move, record=True)
        self._after_move()

    # ---------- Navigation (Wiedergabe) ----------
    def _apply_view(self, target_index):
        current = len(self.state_.history)
        if target_index < current:
            for _ in range(current - target_index):
                self.state_.undo()
        elif target_index > current:
            for _ in range(target_index - current):
                self.state_.redo()
        self.selected_sq = None
        self.legal_targets = []
        self._redraw_board()
        self._update_status()
        total = len(self.state_.history) + len(self.state_.redo_stack)
        if len(self.state_.history) < total:
            player = "Weiß" if self.state_.turn == WHITE else "Schwarz"
            self.status_label.config(text=f"Wiedergabe – {player} war am Zug (→ 'Ende' zum Weiterspielen)")

    def _nav_start(self):
        self._apply_view(0)

    def _nav_back(self):
        self._apply_view(max(0, len(self.state_.history) - 1))

    def _nav_forward(self):
        total = len(self.state_.history) + len(self.state_.redo_stack)
        self._apply_view(min(total, len(self.state_.history) + 1))

    def _nav_end(self):
        total = len(self.state_.history) + len(self.state_.redo_stack)
        self._apply_view(total)

    def _on_move_select(self, _event):
        sel = self.move_listbox.curselection()
        if not sel:
            return
        row_idx = sel[0]
        target_index = min((row_idx + 1) * 2, len(self.state_.history) + len(self.state_.redo_stack))
        self._apply_view(target_index)

    # ---------- Analyse ----------
    def _show_analysis(self):
        report = analyze_game(self.state_.history, depth=2)

        win = tk.Toplevel(self)
        win.title("Partie-Analyse")
        win.geometry("480x520")
        win.configure(bg="#ffffff")

        tk.Label(win, text="Analyse der Partie", font=("Tahoma", 14, "bold"), bg="#ffffff").pack(pady=10)
        tk.Label(win, text="(einfache Analyse durch die eingebaute Engine, keine Profi-Datenbank)",
                 font=("Tahoma", 8), fg="#777777", bg="#ffffff").pack()

        text = tk.Text(win, font=("Consolas", 10), wrap="word")
        text.pack(fill="both", expand=True, padx=10, pady=10)

        text.tag_config("grob", foreground="#c0392b")
        text.tag_config("fehler", foreground="#d68910")
        text.tag_config("ungenau", foreground="#7d6608")
        text.tag_config("ok", foreground="#333333")

        white_mistakes = 0
        black_mistakes = 0
        for r in report:
            spieler = "Weiß" if r["mover"] == WHITE else "Schwarz"
            line = f"Zug {r['ply']:>3} ({spieler}): {r['san']:<8}"
            if r["tag"]:
                line += f"  -> {r['tag']} (~{r['diff']} cp)\n"
                tag = {"Grober Fehler": "grob", "Fehler": "fehler", "Ungenauigkeit": "ungenau"}[r["tag"]]
                if r["tag"] in ("Grober Fehler", "Fehler"):
                    if r["mover"] == WHITE:
                        white_mistakes += 1
                    else:
                        black_mistakes += 1
            else:
                line += "\n"
                tag = "ok"
            text.insert(tk.END, line, tag)

        text.insert(tk.END, f"\nZusammenfassung:\nWeiß: {white_mistakes} nennenswerte Fehler\n"
                             f"Schwarz: {black_mistakes} nennenswerte Fehler\n")
        text.config(state="disabled")
        self._last_analysis = report

    # ---------- Statistik speichern ----------
    def _save_stats(self):
        folder = filedialog.askdirectory(title="Ordner zum Speichern wählen")
        if not folder:
            return

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"schachpartie_{timestamp}.txt"
        path = os.path.join(folder, filename)

        result = "Läuft noch"
        if self.state_.is_checkmate():
            result = "1-0 (Weiß gewinnt)" if self.state_.turn == BLACK else "0-1 (Schwarz gewinnt)"
        elif self.state_.is_stalemate():
            result = "1/2-1/2 (Patt)"

        lines = []
        lines.append("Schachpartie - Statistik")
        lines.append(f"Datum: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        lines.append(f"Modus: {'Mensch vs. Computer' if self.mode == 'computer' else 'Mensch vs. Mensch'}")
        if self.mode == "computer":
            lines.append(f"Schwierigkeit: {self.diff_var.get()}")
            lines.append(f"Mensch spielte: {'Weiß' if self.human_color == WHITE else 'Schwarz'}")
        lines.append(f"Ergebnis: {result}")
        lines.append("")
        lines.append("Zugliste:")
        for i, (move, _snap) in enumerate(self.state_.history):
            san = getattr(move, "san", "?")
            prefix = f"{i // 2 + 1}." if i % 2 == 0 else "   "
            sep = "\n" if i % 2 == 1 else " "
            lines.append(f"{prefix} {san}" if i % 2 == 0 else f"{san}")
        # sauberer neu zusammenbauen (Zugpaare je Zeile)
        move_lines = []
        buf = ""
        for i, (move, _snap) in enumerate(self.state_.history):
            san = getattr(move, "san", "?")
            if i % 2 == 0:
                buf = f"{i // 2 + 1}. {san}"
            else:
                buf += f"  {san}"
                move_lines.append(buf)
                buf = ""
        if buf:
            move_lines.append(buf)

        report_lines = []
        if getattr(self, "_last_analysis", None):
            report_lines.append("")
            report_lines.append("Analyse (Fehler-Erkennung):")
            for r in self._last_analysis:
                if r["tag"]:
                    spieler = "Weiß" if r["mover"] == WHITE else "Schwarz"
                    report_lines.append(f"  Zug {r['ply']} ({spieler}) {r['san']}: {r['tag']} (~{r['diff']} cp)")

        content = "\n".join(
            lines[:6] + [""] + move_lines + report_lines
        )
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Gespeichert", f"Statistik gespeichert unter:\n{path}")
        except OSError as e:
            messagebox.showerror("Fehler", f"Konnte Datei nicht speichern:\n{e}")


if __name__ == "__main__":
    app = ChessApp()
    app.mainloop()
