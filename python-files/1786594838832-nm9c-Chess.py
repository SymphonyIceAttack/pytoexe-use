import tkinter as tk
from tkinter import messagebox
import sys
import os
import subprocess
import random

# ============================================================
# OFFLINE CHESS GAME + COMPUTER AI + EXE BUILDER
# ============================================================

# ------------------------------------------------------------
# EXE BUILDER
# ------------------------------------------------------------

def build_exe():
    print("=" * 55)
    print("             OFFLINE CHESS EXE BUILDER")
    print("=" * 55)

    print("\nInstalling/checking PyInstaller...")

    subprocess.run(
        [sys.executable, "-m", "pip", "install", "pyinstaller"],
        check=True
    )

    print("\nCreating ChessGame.exe...")

    subprocess.run([
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--windowed",
        "--clean",
        "--name",
        "ChessGame",
        os.path.abspath(__file__)
    ], check=True)

    exe = os.path.abspath(
        os.path.join("dist", "ChessGame.exe")
    )

    print("\n" + "=" * 55)
    print("             EXE CREATED SUCCESSFULLY")
    print("=" * 55)
    print("\nYour game is here:")
    print(exe)

    input("\nPress Enter to close...")


# Run:
# python chess.py --build-exe
if "--build-exe" in sys.argv:
    build_exe()
    sys.exit()


# ============================================================
# SETTINGS
# ============================================================

BOARD_SIZE = 8
SQUARE_SIZE = 80

LIGHT = "#F0D9B5"
DARK = "#B58863"
SELECTED = "#F7EC4F"
MOVE_COLOR = "#A9D18E"

# Computer plays BLACK
HUMAN = "w"
COMPUTER = "b"

# AI strength
# 2 = fast
# 3 = stronger
# 4 = much stronger but slower
AI_DEPTH = 3


# ============================================================
# CHESS PIECES
# ============================================================

PIECES = {
    "wK": "♔",
    "wQ": "♕",
    "wR": "♖",
    "wB": "♗",
    "wN": "♘",
    "wP": "♙",

    "bK": "♚",
    "bQ": "♛",
    "bR": "♜",
    "bB": "♝",
    "bN": "♞",
    "bP": "♟"
}


# ============================================================
# PIECE VALUES FOR COMPUTER AI
# ============================================================

VALUES = {
    "P": 100,
    "N": 320,
    "B": 330,
    "R": 500,
    "Q": 900,
    "K": 20000
}


# ============================================================
# CHESS GAME
# ============================================================

class ChessGame:

    def __init__(self, root):

        self.root = root

        self.root.title(
            "Offline Chess - Player vs Computer"
        )

        self.root.resizable(False, False)

        # -------------------------
        # Chess board
        # -------------------------

        self.canvas = tk.Canvas(
            root,
            width=BOARD_SIZE * SQUARE_SIZE,
            height=BOARD_SIZE * SQUARE_SIZE,
            highlightthickness=0
        )

        self.canvas.pack()

        # -------------------------
        # Status
        # -------------------------

        self.status = tk.Label(
            root,
            text="Your turn - White",
            font=("Arial", 16, "bold")
        )

        self.status.pack(pady=8)

        # -------------------------
        # Buttons
        # -------------------------

        button_frame = tk.Frame(root)
        button_frame.pack(pady=5)

        self.restart_button = tk.Button(
            button_frame,
            text="New Game",
            font=("Arial", 11),
            command=self.restart
        )

        self.restart_button.pack(
            side=tk.LEFT,
            padx=5
        )

        self.canvas.bind(
            "<Button-1>",
            self.click
        )

        self.restart()


    # ========================================================
    # CREATE BOARD
    # ========================================================

    def create_board(self):

        return [

            ["bR", "bN", "bB", "bQ",
             "bK", "bB", "bN", "bR"],

            ["bP"] * 8,

            [None] * 8,
            [None] * 8,
            [None] * 8,
            [None] * 8,

            ["wP"] * 8,

            ["wR", "wN", "wB", "wQ",
             "wK", "wB", "wN", "wR"]
        ]


    # ========================================================
    # RESTART
    # ========================================================

    def restart(self):

        self.board = self.create_board()

        self.turn = "w"

        self.selected = None

        self.game_over = False

        self.computer_thinking = False

        self.en_passant = None

        self.castling = {
            "wK": True,
            "wQ": True,
            "bK": True,
            "bQ": True
        }

        self.draw()

        self.status.config(
            text="Your turn - White"
        )


    # ========================================================
    # DRAW BOARD
    # ========================================================

    def draw(self):

        self.canvas.delete("all")

        legal = []

        if self.selected is not None:

            legal = self.pseudo_moves(
                self.selected,
                self.board
            )

        for row in range(8):

            for col in range(8):

                color = (
                    LIGHT
                    if (row + col) % 2 == 0
                    else DARK
                )

                if self.selected == (row, col):

                    color = SELECTED

                elif (row, col) in legal:

                    color = MOVE_COLOR

                x1 = col * SQUARE_SIZE
                y1 = row * SQUARE_SIZE

                x2 = x1 + SQUARE_SIZE
                y2 = y1 + SQUARE_SIZE

                self.canvas.create_rectangle(
                    x1,
                    y1,
                    x2,
                    y2,
                    fill=color,
                    outline=""
                )

                piece = self.board[row][col]

                if piece:

                    self.canvas.create_text(
                        x1 + SQUARE_SIZE // 2,
                        y1 + SQUARE_SIZE // 2,
                        text=PIECES[piece],
                        font=("Arial", 52)
                    )


    # ========================================================
    # MOUSE CLICK
    # ========================================================

    def click(self, event):

        if self.game_over:
            return

        if self.computer_thinking:
            return

        if self.turn != HUMAN:
            return

        col = event.x // SQUARE_SIZE
        row = event.y // SQUARE_SIZE

        if not (
            0 <= row < 8
            and 0 <= col < 8
        ):
            return

        # -------------------------
        # Select piece
        # -------------------------

        if self.selected is None:

            piece = self.board[row][col]

            if piece and piece[0] == HUMAN:

                self.selected = (row, col)

                self.draw()

            return

        # -------------------------
        # Move piece
        # -------------------------

        start = self.selected
        end = (row, col)

        if self.is_legal_move(start, end):

            self.make_move(start, end)

            self.selected = None

            self.draw()

            if not self.game_over:

                self.turn = COMPUTER

                self.status.config(
                    text="Computer is thinking..."
                )

                self.computer_thinking = True

                self.root.after(
                    200,
                    self.computer_move
                )

        else:

            # Select another own piece

            piece = self.board[row][col]

            if piece and piece[0] == HUMAN:

                self.selected = (row, col)

            else:

                self.selected = None

            self.draw()


    # ========================================================
    # OPPOSITE COLOR
    # ========================================================

    def opposite(self, color):

        return (
            "b"
            if color == "w"
            else "w"
        )


    # ========================================================
    # FIND KING
    # ========================================================

    def find_king(
        self,
        color,
        board=None
    ):

        if board is None:
            board = self.board

        for r in range(8):

            for c in range(8):

                if board[r][c] == color + "K":

                    return (r, c)

        return None


    # ========================================================
    # SQUARE ATTACKED
    # ========================================================

    def square_attacked(
        self,
        square,
        by_color,
        board=None
    ):

        if board is None:
            board = self.board

        target_r, target_c = square

        for r in range(8):

            for c in range(8):

                piece = board[r][c]

                if not piece:
                    continue

                if piece[0] != by_color:
                    continue

                kind = piece[1]

                # -------------------
                # PAWN ATTACKS
                # -------------------

                if kind == "P":

                    direction = (
                        -1
                        if by_color == "w"
                        else 1
                    )

                    if (
                        r + direction,
                        c - 1
                    ) == square:

                        return True

                    if (
                        r + direction,
                        c + 1
                    ) == square:

                        return True

                    continue

                # -------------------
                # KNIGHT
                # -------------------

                if kind == "N":

                    offsets = [
                        (-2, -1),
                        (-2, 1),
                        (-1, -2),
                        (-1, 2),
                        (1, -2),
                        (1, 2),
                        (2, -1),
                        (2, 1)
                    ]

                    for dr, dc in offsets:

                        if (
                            r + dr,
                            c + dc
                        ) == square:

                            return True

                    continue

                # -------------------
                # KING
                # -------------------

                if kind == "K":

                    if (
                        abs(r - target_r) <= 1
                        and abs(c - target_c) <= 1
                    ):

                        return True

                    continue

                # -------------------
                # SLIDING PIECES
                # -------------------

                directions = []

                if kind in ["B", "Q"]:

                    directions += [
                        (-1, -1),
                        (-1, 1),
                        (1, -1),
                        (1, 1)
                    ]

                if kind in ["R", "Q"]:

                    directions += [
                        (-1, 0),
                        (1, 0),
                        (0, -1),
                        (0, 1)
                    ]

                for dr, dc in directions:

                    nr = r + dr
                    nc = c + dc

                    while (
                        0 <= nr < 8
                        and 0 <= nc < 8
                    ):

                        if (
                            (nr, nc)
                            == square
                        ):

                            return True

                        if board[nr][nc] is not None:
                            break

                        nr += dr
                        nc += dc

        return False


    # ========================================================
    # CHECK
    # ========================================================

    def in_check(
        self,
        color,
        board=None
    ):

        king = self.find_king(
            color,
            board
        )

        if king is None:
            return True

        return self.square_attacked(
            king,
            self.opposite(color),
            board
        )


    # ========================================================
    # PSEUDO MOVES
    # ========================================================

    def pseudo_moves(
        self,
        pos,
        board,
        include_castling=True
    ):

        r, c = pos

        piece = board[r][c]

        if not piece:
            return []

        color = piece[0]
        kind = piece[1]

        moves = []


        # ====================================================
        # PAWN
        # ====================================================

        if kind == "P":

            direction = (
                -1
                if color == "w"
                else 1
            )

            start_row = (
                6
                if color == "w"
                else 1
            )

            nr = r + direction

            # Forward

            if (
                0 <= nr < 8
                and board[nr][c] is None
            ):

                moves.append(
                    (nr, c)
                )

                nr2 = r + 2 * direction

                if (
                    r == start_row
                    and board[nr2][c] is None
                ):

                    moves.append(
                        (nr2, c)
                    )

            # Capture

            for dc in [-1, 1]:

                nc = c + dc

                if (
                    0 <= nr < 8
                    and 0 <= nc < 8
                ):

                    target = board[nr][nc]

                    if (
                        target
                        and target[0] != color
                    ):

                        moves.append(
                            (nr, nc)
                        )

                    # En passant

                    if self.en_passant == (
                        nr,
                        nc
                    ):

                        moves.append(
                            (nr, nc)
                        )


        # ====================================================
        # KNIGHT
        # ====================================================

        elif kind == "N":

            offsets = [
                (-2, -1),
                (-2, 1),
                (-1, -2),
                (-1, 2),
                (1, -2),
                (1, 2),
                (2, -1),
                (2, 1)
            ]

            for dr, dc in offsets:

                nr = r + dr
                nc = c + dc

                if (
                    0 <= nr < 8
                    and 0 <= nc < 8
                ):

                    target = board[nr][nc]

                    if (
                        target is None
                        or target[0] != color
                    ):

                        moves.append(
                            (nr, nc)
                        )


        # ====================================================
        # BISHOP / ROOK / QUEEN
        # ====================================================

        elif kind in [
            "B",
            "R",
            "Q"
        ]:

            directions = []

            if kind in ["B", "Q"]:

                directions += [
                    (-1, -1),
                    (-1, 1),
                    (1, -1),
                    (1, 1)
                ]

            if kind in ["R", "Q"]:

                directions += [
                    (-1, 0),
                    (1, 0),
                    (0, -1),
                    (0, 1)
                ]

            for dr, dc in directions:

                nr = r + dr
                nc = c + dc

                while (
                    0 <= nr < 8
                    and 0 <= nc < 8
                ):

                    target = board[nr][nc]

                    if target is None:

                        moves.append(
                            (nr, nc)
                        )

                    else:

                        if target[0] != color:

                            moves.append(
                                (nr, nc)
                            )

                        break

                    nr += dr
                    nc += dc


        # ====================================================
        # KING
        # ====================================================

        elif kind == "K":

            for dr in [-1, 0, 1]:

                for dc in [-1, 0, 1]:

                    if (
                        dr == 0
                        and dc == 0
                    ):
                        continue

                    nr = r + dr
                    nc = c + dc

                    if (
                        0 <= nr < 8
                        and 0 <= nc < 8
                    ):

                        target = board[nr][nc]

                        if (
                            target is None
                            or target[0] != color
                        ):

                            moves.append(
                                (nr, nc)
                            )

            # ------------------------
            # CASTLING
            # ------------------------

            if (
                include_castling
                and not self.in_check(
                    color,
                    board
                )
            ):

                row = (
                    7
                    if color == "w"
                    else 0
                )

                # Kingside

                if self.castling[
                    color + "K"
                ]:

                    if (
                        board[row][5] is None
                        and board[row][6] is None
                        and not self.square_attacked(
                            (row, 5),
                            self.opposite(color),
                            board
                        )
                        and not self.square_attacked(
                            (row, 6),
                            self.opposite(color),
                            board
                        )
                    ):

                        moves.append(
                            (row, 6)
                        )

                # Queenside

                if self.castling[
                    color + "Q"
                ]:

                    if (
                        board[row][1] is None
                        and board[row][2] is None
                        and board[row][3] is None
                        and not self.square_attacked(
                            (row, 3),
                            self.opposite(color),
                            board
                        )
                        and not self.square_attacked(
                            (row, 2),
                            self.opposite(color),
                            board
                        )
                    ):

                        moves.append(
                            (row, 2
                        )

        return moves


    # ========================================================
    # MAKE TEMPORARY MOVE
    # ========================================================

    def copy_board(self, board):

        return [
            row[:]
            for row in board
        ]


    # ========================================================
    # APPLY MOVE TO BOARD
    # ========================================================

    def apply_move_to_board(
        self,
        board,
        start,
        end
    ):

        new_board = self.copy_board(
            board
        )

        sr, sc = start
        er, ec = end

        piece = new_board[sr][sc]

        new_board[sr][sc] = None

        new_board[er][ec] = piece

        # En passant

        if (
            piece
            and piece[1] == "P"
            and abs(ec - sc) == 1
            and board[er][ec] is None
        ):

            captured_row = (
                er + 1
                if piece[0] == "w"
                else er - 1
            )

            new_board[
                captured_row
            ][ec] = None

        # Promotion

        if (
            piece
            and piece[1] == "P"
            and er in [0, 7]
        ):

            new_board[er][ec] = (
                piece[0] + "Q"
            )

        # Castling

        if (
            piece
            and piece[1] == "K"
            and abs(ec - sc) == 2
        ):

            if ec == 6:

                rook = new_board[er][7]

                new_board[er][7] = None

                new_board[er][5] = rook

            elif ec == 2:

                rook = new_board[er][0]

                new_board[er][0] = None

                new_board[er][3] = rook

        return new_board


    # ========================================================
    # LEGAL MOVE
    # ========================================================

    def is_legal_move(
        self,
        start,
        end
    ):

        piece = self.board[
            start[0]
        ][start[1]]

        if not piece:
            return False

        if piece[0] != self.turn:
            return False

        if end not in self.pseudo_moves(
            start,
            self.board
        ):

            return False

        test_board = (
            self.apply_move_to_board(
                self.board,
                start,
                end
            )
        )

        return not self.in_check(
            self.turn,
            test_board
        )


    # ========================================================
    # ALL LEGAL MOVES
    # ========================================================

    def all_legal_moves(
        self,
        color,
        board=None
    ):

        if board is None:
            board = self.board

        moves = []

        old_turn = self.turn

        self.turn = color

        for r in range(8):

            for c in range(8):

                piece = board[r][c]

                if (
                    piece
                    and piece[0] == color
                ):

                    pseudo = self.pseudo_moves(
                        (r, c),
                        board
                    )

                    for end in pseudo:

                        test_board = (
                            self.apply_move_to_board(
                                board,
                                (r, c),
                                end
                            )
                        )

                        if not self.in_check(
                            color,
                            test_board
                        ):

                            moves.append(
                                ((r, c), end)
                            )

        self.turn = old_turn

        return moves


    # ========================================================
    # MAKE REAL MOVE
    # ========================================================

    def make_move(
        self,
        start,
        end
    ):

        sr, sc = start
        er, ec = end

        piece = self.board[sr][sc]

        captured = self.board[er][ec]

        # En passant

        if (
            piece[1] == "P"
            and self.en_passant == end
            and sc != ec
            and captured is None
        ):

            captured_row = (
                er + 1
                if piece[0] == "w"
                else er - 1
            )

            self.board[
                captured_row
            ][ec] = None

        self.board[sr][sc] = None

        self.board[er][ec] = piece

        # Castling rights

        if piece == "wK":

            self.castling["wK"] = False
            self.castling["wQ"] = False

        elif piece == "bK":

            self.castling["bK"] = False
            self.castling["bQ"] = False

        elif piece == "wR":

            if start == (7, 0):
                self.castling["wQ"] = False

            elif start == (7, 7):
                self.castling["wK"] = False

        elif piece == "bR":

            if start == (0, 0):
                self.castling["bQ"] = False

            elif start == (0, 7):
                self.castling["bK"] = False

        # Captured rook

        if captured == "wR":

            if end == (7, 0):
                self.castling["wQ"] = False

            elif end == (7, 7):
                self.castling["wK"] = False

        elif captured == "bR":

            if end == (0, 0):
                self.castling["bQ"] = False

            elif end == (0, 7):
                self.castling["bK"] = False

        # Castling move

        if (
            piece[1] == "K"
            and abs(ec - sc) == 2
        ):

            if ec == 6:

                rook = self.board[er][7]

                self.board[er][7] = None
                self.board[er][5] = rook

            elif ec == 2:

                rook = self.board[er][0]

                self.board[er][0] = None
                self.board[er][3] = rook

        # En passant square

        self.en_passant = None

        if (
            piece[1] == "P"
            and abs(er - sr) == 2
        ):

            self.en_passant = (
                (sr + er) // 2,
                sc
            )

        # Promotion

        if (
            piece[1] == "P"
            and er in [0, 7]
        ):

            if piece[0] == "w":

                choice = messagebox.askquestion(
                    "Pawn Promotion",
                    "Promote pawn to Queen?"
                )

                if choice == "yes":

                    self.board[er][ec] = "wQ"

                else:

                    self.board[er][ec] = "wR"

            else:

                self.board[er][ec] = "bQ"

        # Check game status

        opponent = self.opposite(
            piece[0]
        )

        legal = self.all_legal_moves(
            opponent
        )

        if not legal:

            self.game_over = True

            if self.in_check(
                opponent
            ):

                winner = (
                    "White"
                    if piece[0] == "w"
                    else "Black"
                )

                messagebox.showinfo(
                    "CHECKMATE",
                    winner + " wins!"
                )

            else:

                messagebox.showinfo(
                    "DRAW",
                    "The game is a stalemate."
                )

            return True

        return False


    # ========================================================
    # AI - BOARD EVALUATION
    # ========================================================

    def evaluate_board(
        self,
        board
    ):

        score = 0

        for row in board:

            for piece in row:

                if not piece:
                    continue

                value = VALUES[
                    piece[1]
                ]

                if piece[0] == "b":

                    score += value

                else:

                    score -= value

        return score


    # ========================================================
    # AI - MINIMAX
    # ========================================================

    def minimax(
        self,
        board,
        depth,
        maximizing
    ):

        if depth == 0:

            return (
                self.evaluate_board(board),
                None
            )

        color = (
            "b"
            if maximizing
            else "w"
        )

        moves = self.all_legal_moves(
            color,
            board
        )

        # Checkmate / stalemate

        if not moves:

            if self.in_check(
                color,
                board
            ):

                if maximizing:

                    return (
                        -1000000,
                        None
                    )

                return (
                    1000000,
                    None
                )

            return (0, None)

        best_move = None

        if maximizing:

            best_score = -float("inf")

            for move in moves:

                new_board = (
                    self.apply_move_to_board(
                        board,
                        move[0],
                        move[1]
                    )
                )

                score, _ = self.minimax(
                    new_board,
                    depth - 1,
                    False
                )

                if score > best_score:

                    best_score = score
                    best_move = move

            return (
                best_score,
                best_move
            )

        else:

            best_score = float("inf")

            for move in moves:

                new_board = (
                    self.apply_move_to_board(
                        board,
                        move[0],
                        move[1]
                    )
                )

                score, _ = self.minimax(
                    new_board,
                    depth - 1,
                    True
                )

                if score < best_score:

                    best_score = score
                    best_move = move

            return (
                best_score,
                best_move
            )


    # ========================================================
    # COMPUTER MOVE
    # ========================================================

    def computer_move(self):

        if self.game_over:

            self.computer_thinking = False

            return

        moves = self.all_legal_moves(
            COMPUTER
        )

        if not moves:

            self.computer_thinking = False

            return

        # Try minimax

        score, move = self.minimax(
            self.board,
            AI_DEPTH,
            True
        )

        # Safety fallback

        if move is None:

            move = random.choice(
                moves
            )

        self.make_move(
            move[0],
            move[1]
        )

        if not self.game_over:

            self.turn = HUMAN

            self.status.config(
                text="Your turn - White"
            )

        self.computer_thinking = False

        self.selected = None

        self.draw()


# ============================================================
# START GAME
# ============================================================

root = tk.Tk()

game = ChessGame(root)

root.mainloop()
