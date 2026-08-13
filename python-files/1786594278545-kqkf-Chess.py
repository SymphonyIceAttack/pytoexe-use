import tkinter as tk
from tkinter import messagebox

# -----------------------------
# Chess Game - Python + Tkinter
# -----------------------------

BOARD_SIZE = 8
SQUARE_SIZE = 80

LIGHT = "#F0D9B5"
DARK = "#B58863"
SELECTED = "#F7EC4F"

PIECES = {
    "wK": "♔", "wQ": "♕", "wR": "♖",
    "wB": "♗", "wN": "♘", "wP": "♙",
    "bK": "♚", "bQ": "♛", "bR": "♜",
    "bB": "♝", "bN": "♞", "bP": "♟"
}


class ChessGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Chess")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(
            root,
            width=BOARD_SIZE * SQUARE_SIZE,
            height=BOARD_SIZE * SQUARE_SIZE
        )
        self.canvas.pack()

        self.status = tk.Label(
            root,
            text="White's turn",
            font=("Arial", 16, "bold")
        )
        self.status.pack(pady=8)

        self.restart_button = tk.Button(
            root,
            text="Restart Game",
            font=("Arial", 12),
            command=self.restart
        )
        self.restart_button.pack(pady=5)

        self.restart()

        self.canvas.bind("<Button-1>", self.click)

    # -----------------------------
    # Initial board
    # -----------------------------
    def create_board(self):
        return [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bP"] * 8,
            [None] * 8,
            [None] * 8,
            [None] * 8,
            [None] * 8,
            ["wP"] * 8,
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]
        ]

    # -----------------------------
    # Restart
    # -----------------------------
    def restart(self):
        self.board = self.create_board()
        self.turn = "w"
        self.selected = None
        self.game_over = False
        self.castling = {
            "wK": True,
            "wQ": True,
            "bK": True,
            "bQ": True
        }
        self.en_passant = None
        self.draw()

    # -----------------------------
    # Draw board
    # -----------------------------
    def draw(self):
        self.canvas.delete("all")

        for row in range(8):
            for col in range(8):
                color = LIGHT if (row + col) % 2 == 0 else DARK

                if self.selected == (row, col):
                    color = SELECTED

                x1 = col * SQUARE_SIZE
                y1 = row * SQUARE_SIZE
                x2 = x1 + SQUARE_SIZE
                y2 = y1 + SQUARE_SIZE

                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
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

        self.status.config(
            text=f"{'White' if self.turn == 'w' else 'Black'}'s turn"
        )

    # -----------------------------
    # Mouse click
    # -----------------------------
    def click(self, event):
        if self.game_over:
            return

        col = event.x // SQUARE_SIZE
        row = event.y // SQUARE_SIZE

        if not (0 <= row < 8 and 0 <= col < 8):
            return

        if self.selected is None:
            piece = self.board[row][col]

            if piece and piece[0] == self.turn:
                self.selected = (row, col)
                self.draw()

        else:
            start = self.selected
            end = (row, col)

            if self.is_legal_move(start, end):
                self.make_move(start, end)

            self.selected = None
            self.draw()

    # -----------------------------
    # Check color
    # -----------------------------
    def opposite(self, color):
        return "b" if color == "w" else "w"

    # -----------------------------
    # Find king
    # -----------------------------
    def find_king(self, color, board=None):
        if board is None:
            board = self.board

        for r in range(8):
            for c in range(8):
                if board[r][c] == color + "K":
                    return (r, c)

        return None

    # -----------------------------
    # Check if square attacked
    # -----------------------------
    def square_attacked(self, square, by_color, board=None):
        if board is None:
            board = self.board

        target_r, target_c = square

        for r in range(8):
            for c in range(8):
                piece = board[r][c]

                if not piece or piece[0] != by_color:
                    continue

                moves = self.pseudo_moves(
                    (r, c),
                    board,
                    include_castling=False
                )

                if square in moves:
                    return True

        return False

    # -----------------------------
    # Is king in check?
    # -----------------------------
    def in_check(self, color, board=None):
        king = self.find_king(color, board)

        if king is None:
            return True

        return self.square_attacked(
            king,
            self.opposite(color),
            board
        )

    # -----------------------------
    # Pseudo legal moves
    # -----------------------------
    def pseudo_moves(self, pos, board, include_castling=True):
        r, c = pos
        piece = board[r][c]

        if not piece:
            return []

        color = piece[0]
        kind = piece[1]
        moves = []

        # Pawn
        if kind == "P":
            direction = -1 if color == "w" else 1
            start_row = 6 if color == "w" else 1

            nr = r + direction

            if 0 <= nr < 8 and board[nr][c] is None:
                moves.append((nr, c))

                nr2 = r + 2 * direction

                if (
                    r == start_row
                    and board[nr2][c] is None
                ):
                    moves.append((nr2, c))

            for dc in [-1, 1]:
                nc = c + dc
                nr = r + direction

                if 0 <= nr < 8 and 0 <= nc < 8:
                    target = board[nr][nc]

                    if target and target[0] != color:
                        moves.append((nr, nc))

                    if self.en_passant == (nr, nc):
                        moves.append((nr, nc))

        # Knight
        elif kind == "N":
            offsets = [
                (-2, -1), (-2, 1),
                (-1, -2), (-1, 2),
                (1, -2), (1, 2),
                (2, -1), (2, 1)
            ]

            for dr, dc in offsets:
                nr = r + dr
                nc = c + dc

                if 0 <= nr < 8 and 0 <= nc < 8:
                    target = board[nr][nc]

                    if target is None or target[0] != color:
                        moves.append((nr, nc))

        # Bishop / Rook / Queen
        elif kind in ["B", "R", "Q"]:

            directions = []

            if kind in ["B", "Q"]:
                directions += [
                    (-1, -1), (-1, 1),
                    (1, -1), (1, 1)
                ]

            if kind in ["R", "Q"]:
                directions += [
                    (-1, 0), (1, 0),
                    (0, -1), (0, 1)
                ]

            for dr, dc in directions:
                nr = r + dr
                nc = c + dc

                while 0 <= nr < 8 and 0 <= nc < 8:
                    target = board[nr][nc]

                    if target is None:
                        moves.append((nr, nc))
                    else:
                        if target[0] != color:
                            moves.append((nr, nc))
                        break

                    nr += dr
                    nc += dc

        # King
        elif kind == "K":
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:

                    if dr == 0 and dc == 0:
                        continue

                    nr = r + dr
                    nc = c + dc

                    if 0 <= nr < 8 and 0 <= nc < 8:
                        target = board[nr][nc]

                        if target is None or target[0] != color:
                            moves.append((nr, nc))

            # Castling
            if include_castling and not self.in_check(color, board):
                row = 7 if color == "w" else 0

                # Kingside
                if self.castling[color + "K"]:
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
                        moves.append((row, 6))

                # Queenside
                if self.castling[color + "Q"]:
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
                        moves.append((row, 2))

        return moves

    # -----------------------------
    # Legal move
    # -----------------------------
    def is_legal_move(self, start, end):
        piece = self.board[start[0]][start[1]]

        if not piece or piece[0] != self.turn:
            return False

        if end not in self.pseudo_moves(start, self.board):
            return False

        test_board = [row[:] for row in self.board]

        sr, sc = start
        er, ec = end

        moving_piece = test_board[sr][sc]
        test_board[sr][sc] = None
        test_board[er][ec] = moving_piece

        # En passant simulation
        if (
            moving_piece[1] == "P"
            and self.en_passant == end
            and sc != ec
            and self.board[er][ec] is None
        ):
            captured_row = er + (1 if moving_piece[0] == "w" else -1)
            test_board[captured_row][ec] = None

        return not self.in_check(self.turn, test_board)

    # -----------------------------
    # Make move
    # -----------------------------
    def make_move(self, start, end):
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
            captured_row = er + (1 if piece[0] == "w" else -1)
            self.board[captured_row][ec] = None

        self.board[sr][sc] = None
        self.board[er][ec] = piece

        # Update castling rights
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

        # Rook captured
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
        if piece[1] == "K" and abs(ec - sc) == 2:
            if ec == 6:
                rook = self.board[er][7]
                self.board[er][7] = None
                self.board[er][5] = rook

            elif ec == 2:
                rook = self.board[er][0]
                self.board[er][0] = None
                self.board[er][3] = rook

        # En passant target
        self.en_passant = None

        if piece[1] == "P" and abs(er - sr) == 2:
            self.en_passant = ((sr + er) // 2, sc)

        # Pawn promotion
        if piece[1] == "P" and er in [0, 7]:
            self.promote(er, ec, piece[0])

        # Change turn
        self.turn = self.opposite(self.turn)

        # Checkmate / stalemate
        if self.is_checkmate(self.turn):
            self.game_over = True

            winner = "White" if self.turn == "b" else "Black"

            messagebox.showinfo(
                "Checkmate!",
                f"{winner} wins!"
            )

        elif self.is_stalemate(self.turn):
            self.game_over = True

            messagebox.showinfo(
                "Draw",
                "Stalemate!"
            )

        elif self.in_check(self.turn):
            self.status.config(
                text=f"{'White' if self.turn == 'w' else 'Black'} is in CHECK!"
            )

    # -----------------------------
    # Promotion
    # -----------------------------
    def promote(self, row, col, color):
        choice = messagebox.askquestion(
            "Pawn Promotion",
            "Promote to Queen?\n\n"
            "YES = Queen\n"
            "NO = Rook"
        )

        if choice == "yes":
            self.board[row][col] = color + "Q"
        else:
            self.board[row][col] = color + "R"

    # -----------------------------
    # Get all legal moves
    # -----------------------------
    def all_legal_moves(self, color):
        moves = []

        for r in range(8):
            for c in range(8):

                piece = self.board[r][c]

                if piece and piece[0] == color:

                    for move in self.pseudo_moves(
                        (r, c),
                        self.board
                    ):
                        if self.is_legal_move(
                            (r, c),
                            move
                        ):
                            moves.append(
                                ((r, c), move)
                            )

        return moves

    # -----------------------------
    # Checkmate
    # -----------------------------
    def is_checkmate(self, color):
        return (
            self.in_check(color)
            and len(self.all_legal_moves(color)) == 0
        )

    # -----------------------------
    # Stalemate
    # -----------------------------
    def is_stalemate(self, color):
        return (
            not self.in_check(color)
            and len(self.all_legal_moves(color)) == 0
        )


# -----------------------------
# Run Game
# -----------------------------

root = tk.Tk()
game = ChessGame(root)
root.mainloop()
