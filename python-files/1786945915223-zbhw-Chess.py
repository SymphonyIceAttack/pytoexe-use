import tkinter as tk
from tkinter import messagebox
import chess
import random


# -----------------------------
# SETTINGS
# -----------------------------

SQUARE_SIZE = 75

LIGHT = "#F0D9B5"
DARK = "#B58863"
SELECTED = "#FFD700"
MOVE_COLOR = "#90EE90"

PIECES = {
    "P": "♙",
    "N": "♘",
    "B": "♗",
    "R": "♖",
    "Q": "♕",
    "K": "♔",

    "p": "♟",
    "n": "♞",
    "b": "♝",
    "r": "♜",
    "q": "♛",
    "k": "♚"
}


# -----------------------------
# CHESS GAME
# -----------------------------

class ChessGame:

    def __init__(self, window):

        self.window = window
        self.window.title("Python Chess")

        self.board = chess.Board()

        # White = human
        # Black = computer
        self.computer = True

        self.selected_square = None

        self.buttons = {}

        # -------------------------
        # Title
        # -------------------------

        self.title = tk.Label(
            window,
            text="♟ Python Chess ♟",
            font=("Arial", 22, "bold")
        )

        self.title.pack(pady=10)

        # -------------------------
        # Status
        # -------------------------

        self.status = tk.Label(
            window,
            text="White's Turn",
            font=("Arial", 16, "bold")
        )

        self.status.pack()

        # -------------------------
        # Board
        # -------------------------

        self.board_frame = tk.Frame(window)

        self.board_frame.pack(pady=10)

        self.create_board()

        # -------------------------
        # Restart button
        # -------------------------

        self.restart = tk.Button(
            window,
            text="New Game",
            font=("Arial", 14),
            command=self.new_game
        )

        self.restart.pack(pady=10)

        self.update_board()


    # -----------------------------
    # CREATE BOARD
    # -----------------------------

    def create_board(self):

        for row in range(8):

            for col in range(8):

                button = tk.Button(
                    self.board_frame,
                    font=("Arial", 38),
                    width=2,
                    height=1,
                    relief="flat",
                    command=lambda r=row, c=col:
                    self.square_clicked(r, c)
                )

                button.grid(
                    row=row,
                    column=col
                )

                self.buttons[(row, col)] = button


    # -----------------------------
    # DISPLAY BOARD
    # -----------------------------

    def update_board(self):

        for row in range(8):

            for col in range(8):

                square = chess.square(col, 7 - row)

                piece = self.board.piece_at(square)

                if piece:
                    text = PIECES[piece.symbol()]
                else:
                    text = ""

                color = (
                    LIGHT
                    if (row + col) % 2 == 0
                    else DARK
                )

                self.buttons[(row, col)].config(
                    text=text,
                    bg=color
                )

        # Highlight selected piece

        if self.selected_square is not None:

            row = 7 - chess.square_rank(
                self.selected_square
            )

            col = chess.square_file(
                self.selected_square
            )

            self.buttons[(row, col)].config(
                bg=SELECTED
            )

        # Highlight legal moves

        if self.selected_square is not None:

            for move in self.board.legal_moves:

                if move.from_square == self.selected_square:

                    row = 7 - chess.square_rank(
                        move.to_square
                    )

                    col = chess.square_file(
                        move.to_square
                    )

                    self.buttons[(row, col)].config(
                        bg=MOVE_COLOR
                    )


    # -----------------------------
    # CLICK SQUARE
    # -----------------------------

    def square_clicked(self, row, col):

        # Game already finished
        if self.board.is_game_over():
            return

        # Computer's turn
        if self.board.turn == chess.BLACK:
            return

        square = chess.square(
            col,
            7 - row
        )

        # -------------------------
        # Select piece
        # -------------------------

        if self.selected_square is None:

            piece = self.board.piece_at(square)

            if piece is None:
                return

            # Only select White pieces
            if piece.color != chess.WHITE:
                return

            self.selected_square = square

            self.update_board()

            return

        # -------------------------
        # Try move
        # -------------------------

        move = chess.Move(
            self.selected_square,
            square
        )

        # Promotion
        piece = self.board.piece_at(
            self.selected_square
        )

        if (
            piece
            and piece.piece_type == chess.PAWN
            and chess.square_rank(square) in [0, 7]
        ):

            move = chess.Move(
                self.selected_square,
                square,
                promotion=chess.QUEEN
            )

        # Check legal move

        if move in self.board.legal_moves:

            self.board.push(move)

            self.selected_square = None

            self.update_board()

            if self.check_game_over():
                return

            self.status.config(
                text="Computer's Turn"
            )

            # Computer move
            self.window.after(
                500,
                self.computer_move
            )

        else:

            # Select another White piece
            piece = self.board.piece_at(square)

            if piece and piece.color == chess.WHITE:

                self.selected_square = square

                self.update_board()

            else:

                self.selected_square = None

                self.update_board()


    # -----------------------------
    # COMPUTER MOVE
    # -----------------------------

    def computer_move(self):

        if self.board.is_game_over():
            return

        legal_moves = list(
            self.board.legal_moves
        )

        if not legal_moves:
            return

        # Simple computer:
        # chooses a random legal move

        move = random.choice(
            legal_moves
        )

        self.board.push(move)

        self.update_board()

        if self.check_game_over():
            return

        self.status.config(
            text="White's Turn"
        )


    # -----------------------------
    # CHECK GAME STATUS
    # -----------------------------

    def check_game_over(self):

        if self.board.is_checkmate():

            if self.board.turn == chess.WHITE:

                message = "Checkmate!\nBlack wins!"

            else:

                message = "Checkmate!\nWhite wins!"

            messagebox.showinfo(
                "Game Over",
                message
            )

            self.status.config(
                text="Game Over"
            )

            return True


        if self.board.is_stalemate():

            messagebox.showinfo(
                "Game Over",
                "Draw by stalemate!"
            )

            self.status.config(
                text="Draw"
            )

            return True


        if self.board.is_insufficient_material():

            messagebox.showinfo(
                "Game Over",
                "Draw!\nInsufficient material."
            )

            self.status.config(
                text="Draw"
            )

            return True


        if self.board.is_fivefold_repetition():

            messagebox.showinfo(
                "Game Over",
                "Draw by repetition!"
            )

            self.status.config(
                text="Draw"
            )

            return True


        if self.board.is_seventyfive_moves():

            messagebox.showinfo(
                "Game Over",
                "Draw by 75-move rule!"
            )

            self.status.config(
                text="Draw"
            )

            return True


        # Check

        if self.board.is_check():

            if self.board.turn == chess.WHITE:

                self.status.config(
                    text="White is in CHECK!"
                )

            else:

                self.status.config(
                    text="Black is in CHECK!"
                )

        return False


    # -----------------------------
    # NEW GAME
    # -----------------------------

    def new_game(self):

        self.board = chess.Board()

        self.selected_square = None

        self.status.config(
            text="White's Turn"
        )

        self.update_board()


# -----------------------------
# START PROGRAM
# -----------------------------

window = tk.Tk()

game = ChessGame(window)

window.mainloop()
