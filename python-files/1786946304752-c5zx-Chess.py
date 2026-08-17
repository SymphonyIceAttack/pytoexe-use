import tkinter as tk
from tkinter import messagebox
import chess
import random

# -------------------------
# Setup
# -------------------------

root = tk.Tk()
root.title("Simple Chess")

game = chess.Board()
selected = None

pieces = {
    "P": "♙", "N": "♘", "B": "♗",
    "R": "♖", "Q": "♕", "K": "♔",
    "p": "♟", "n": "♞", "b": "♝",
    "r": "♜", "q": "♛", "k": "♚"
}

buttons = []


# -------------------------
# Draw board
# -------------------------

def draw():

    for r in range(8):
        for c in range(8):

            square = chess.square(c, 7-r)
            piece = game.piece_at(square)

            text = pieces[piece.symbol()] if piece else ""

            color = "#F0D9B5" if (r+c) % 2 == 0 else "#B58863"

            buttons[r][c].config(
                text=text,
                bg=color
            )

    # Highlight selected square
    if selected is not None:

        r = 7 - chess.square_rank(selected)
        c = chess.square_file(selected)

        buttons[r][c].config(bg="yellow")


# -------------------------
# Click board
# -------------------------

def click(r, c):

    global selected

    # Don't play after game ends
    if game.is_game_over():
        return

    # Computer's turn
    if game.turn == chess.BLACK:
        return

    square = chess.square(c, 7-r)

    # Select a white piece
    if selected is None:

        piece = game.piece_at(square)

        if piece and piece.color == chess.WHITE:
            selected = square
            draw()

        return

    # Create move
    move = chess.Move(selected, square)

    # Pawn promotion to Queen
    piece = game.piece_at(selected)

    if piece and piece.piece_type == chess.PAWN:
        if chess.square_rank(square) in [0, 7]:
            move = chess.Move(
                selected,
                square,
                promotion=chess.QUEEN
            )

    # Make legal move
    if move in game.legal_moves:

        game.push(move)
        selected = None
        draw()

        if check_game():
            return

        # Computer plays
        root.after(500, computer)

    else:

        selected = None
        draw()


# -------------------------
# Computer
# -------------------------

def computer():

    if game.is_game_over():
        return

    moves = list(game.legal_moves)

    if moves:
        move = random.choice(moves)
        game.push(move)

    draw()
    check_game()


# -------------------------
# Check game result
# -------------------------

def check_game():

    if game.is_checkmate():

        winner = "Black" if game.turn == chess.WHITE else "White"

        messagebox.showinfo(
            "Game Over",
            "Checkmate!\n" + winner + " wins!"
        )

        return True

    if game.is_stalemate():

        messagebox.showinfo(
            "Game Over",
            "Draw by stalemate!"
        )

        return True

    if game.is_insufficient_material():

        messagebox.showinfo(
            "Game Over",
            "Draw!"
        )

        return True

    if game.is_check():

        if game.turn == chess.WHITE:
            status.config(text="White is in CHECK!")
        else:
            status.config(text="Black is in CHECK!")

    else:

        if game.turn == chess.WHITE:
            status.config(text="White's Turn")
        else:
            status.config(text="Black's Turn")

    return False


# -------------------------
# New game
# -------------------------

def new_game():

    global game, selected

    game = chess.Board()
    selected = None

    status.config(text="White's Turn")

    draw()


# -------------------------
# Create board
# -------------------------

for r in range(8):

    row = []

    for c in range(8):

        b = tk.Button(
            root,
            font=("Arial", 32),
            width=2,
            height=1,
            command=lambda r=r, c=c: click(r, c)
        )

        b.grid(row=r, column=c)

        row.append(b)

    buttons.append(row)


# -------------------------
# Status
# -------------------------

status = tk.Label(
    root,
    text="White's Turn",
    font=("Arial", 16, "bold")
)

status.grid(
    row=8,
    column=0,
    columnspan=8
)


# -------------------------
# New Game button
# -------------------------

tk.Button(
    root,
    text="New Game",
    font=("Arial", 14),
    command=new_game
).grid(
    row=9,
    column=0,
    columnspan=8,
    pady=10
)


draw()

root.mainloop()
