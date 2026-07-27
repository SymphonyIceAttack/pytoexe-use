import tkinter as tk
import random

# ---------- Farben ----------
BG_COLOR = "#ccff99"
O_COLOR = "#ff0066"
X_COLOR = "#00AA77"
TITLE_BG = "#0a246a"       # klassisches XP-Blau für die Titelleiste
TITLE_FG = "#ffffff"
CLOSE_RED = "#e81123"

WIN_LINES = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),   # Reihen
    (0, 3, 6), (1, 4, 7), (2, 5, 8),   # Spalten
    (0, 4, 8), (2, 4, 6)               # Diagonalen
]


class TicTacToe(tk.Tk):
    def __init__(self):
        super().__init__()
        self.overrideredirect(True)  # kein Standard-Fensterrahmen -> eigener XP-Style Titelbalken
        self.geometry("420x500+400+200")
        self.configure(bg=BG_COLOR)
        self.resizable(False, False)

        self.mode = None          # "computer" oder "mensch"
        self.board = [""] * 9
        self.current_player = "X"
        self.game_over = False

        self._build_titlebar()
        self._build_container()
        self._show_menu()

        # Fenster mit der Maus verschiebbar machen (weil kein Standardrahmen mehr da ist)
        self._offset_x = 0
        self._offset_y = 0
        self.titlebar.bind("<Button-1>", self._start_move)
        self.titlebar.bind("<B1-Motion>", self._do_move)

    # ---------- Eigener XP-Titelbalken ----------
    def _build_titlebar(self):
        self.titlebar = tk.Frame(self, bg=TITLE_BG, height=30)
        self.titlebar.pack(side="top", fill="x")

        title_label = tk.Label(
            self.titlebar, text="Tic Tac Toe", bg=TITLE_BG, fg=TITLE_FG,
            font=("Tahoma", 10, "bold")
        )
        title_label.pack(side="left", padx=8)

        close_btn = tk.Button(
            self.titlebar, text="X", bg=CLOSE_RED, fg="white",
            font=("Tahoma", 10, "bold"), width=4, bd=0,
            activebackground="#ff4444", activeforeground="white",
            command=self.destroy, cursor="hand2"
        )
        close_btn.pack(side="right", padx=4, pady=3)

    def _start_move(self, event):
        self._offset_x = event.x
        self._offset_y = event.y

    def _do_move(self, event):
        x = self.winfo_pointerx() - self._offset_x
        y = self.winfo_pointery() - self._offset_y
        self.geometry(f"+{x}+{y}")

    # ---------- Container fuer wechselnde Ansichten ----------
    def _build_container(self):
        self.container = tk.Frame(self, bg=BG_COLOR)
        self.container.pack(fill="both", expand=True)

    def _clear_container(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    # ---------- Menü ----------
    def _show_menu(self):
        self._clear_container()

        tk.Label(
            self.container, text="Tic Tac Toe", bg=BG_COLOR, fg=X_COLOR,
            font=("Tahoma", 26, "bold")
        ).pack(pady=(60, 10))

        tk.Label(
            self.container, text="Wähle einen Modus", bg=BG_COLOR, fg="#333333",
            font=("Tahoma", 12)
        ).pack(pady=(0, 30))

        tk.Button(
            self.container, text="Gegen Computer", font=("Tahoma", 13, "bold"),
            bg=X_COLOR, fg="white", width=20, height=2, bd=0, cursor="hand2",
            command=lambda: self._start_game("computer")
        ).pack(pady=10)

        tk.Button(
            self.container, text="Gegen Mensch", font=("Tahoma", 13, "bold"),
            bg=O_COLOR, fg="white", width=20, height=2, bd=0, cursor="hand2",
            command=lambda: self._start_game("mensch")
        ).pack(pady=10)

    def _start_game(self, mode):
        self.mode = mode
        self.board = [""] * 9
        self.current_player = "X"
        self.game_over = False
        self._show_board()

    # ---------- Spielbrett ----------
    def _show_board(self):
        self._clear_container()

        self.status_label = tk.Label(
            self.container, text="Spieler X ist dran",
            bg=BG_COLOR, fg="#333333", font=("Tahoma", 13, "bold")
        )
        self.status_label.pack(pady=(15, 5))

        board_frame = tk.Frame(self.container, bg=BG_COLOR)
        board_frame.pack(pady=10)

        self.canvas_cells = []
        for i in range(9):
            canvas = tk.Canvas(
                board_frame, width=110, height=110, bg="white",
                highlightthickness=2, highlightbackground="#88aa55"
            )
            canvas.grid(row=i // 3, column=i % 3, padx=4, pady=4)
            canvas.bind("<Button-1>", lambda e, idx=i: self._on_cell_click(idx))
            self.canvas_cells.append(canvas)

        btn_frame = tk.Frame(self.container, bg=BG_COLOR)
        btn_frame.pack(pady=15)

        tk.Button(
            btn_frame, text="Neustart", font=("Tahoma", 11, "bold"),
            bg=X_COLOR, fg="white", width=12, bd=0, cursor="hand2",
            command=lambda: self._start_game(self.mode)
        ).grid(row=0, column=0, padx=5)

        tk.Button(
            btn_frame, text="Menü", font=("Tahoma", 11, "bold"),
            bg="#888888", fg="white", width=12, bd=0, cursor="hand2",
            command=self._show_menu
        ).grid(row=0, column=1, padx=5)

    def _draw_symbol(self, idx, symbol):
        canvas = self.canvas_cells[idx]
        canvas.delete("all")
        if symbol == "X":
            canvas.create_line(20, 20, 90, 90, fill=X_COLOR, width=8, capstyle="round")
            canvas.create_line(90, 20, 20, 90, fill=X_COLOR, width=8, capstyle="round")
        elif symbol == "O":
            canvas.create_oval(18, 18, 92, 92, outline=O_COLOR, width=8)

    # ---------- Spiellogik ----------
    def _on_cell_click(self, idx):
        if self.game_over or self.board[idx] != "":
            return
        self._place(idx, self.current_player)

        if self._check_end():
            return

        if self.mode == "computer" and self.current_player == "O" and not self.game_over:
            self.after(400, self._computer_move)

    def _place(self, idx, symbol):
        self.board[idx] = symbol
        self._draw_symbol(idx, symbol)
        self.current_player = "O" if symbol == "X" else "X"
        if not self.game_over:
            self.status_label.config(text=f"Spieler {self.current_player} ist dran")

    def _check_end(self):
        winner = self._get_winner()
        if winner:
            self.game_over = True
            self.status_label.config(text=f"Spieler {winner} hat gewonnen!")
            return True
        if "" not in self.board:
            self.game_over = True
            self.status_label.config(text="Unentschieden!")
            return True
        return False

    def _get_winner(self):
        for a, b, c in WIN_LINES:
            if self.board[a] and self.board[a] == self.board[b] == self.board[c]:
                return self.board[a]
        return None

    # ---------- Computergegner ----------
    def _computer_move(self):
        if self.game_over:
            return
        idx = self._best_move()
        if idx is not None:
            self._place(idx, "O")
            self._check_end()

    def _best_move(self):
        empty = [i for i, v in enumerate(self.board) if v == ""]
        if not empty:
            return None

        # 1. Gewinnzug finden
        for i in empty:
            b = self.board[:]
            b[i] = "O"
            if self._winner_of(b) == "O":
                return i

        # 2. Gegner blocken
        for i in empty:
            b = self.board[:]
            b[i] = "X"
            if self._winner_of(b) == "X":
                return i

        # 3. Mitte nehmen
        if 4 in empty:
            return 4

        # 4. Ecke nehmen
        corners = [i for i in (0, 2, 6, 8) if i in empty]
        if corners:
            return random.choice(corners)

        # 5. Zufälliger Zug
        return random.choice(empty)

    @staticmethod
    def _winner_of(board):
        for a, b, c in WIN_LINES:
            if board[a] and board[a] == board[b] == board[c]:
                return board[a]
        return None


if __name__ == "__main__":
    app = TicTacToe()
    app.mainloop()
