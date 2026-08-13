import tkinter as tk
from tkinter import messagebox
import random
import sys
import subprocess
import os

# =====================================================
# EXE BUILDER
# =====================================================

if "--build-exe" in sys.argv:
    subprocess.run([
        sys.executable, "-m", "pip", "install", "pyinstaller"
    ])

    subprocess.run([
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "ChessGame",
        __file__
    ])

    print("EXE created in the 'dist' folder!")
    input("Press Enter...")
    sys.exit()


# =====================================================
# SETTINGS
# =====================================================

SIZE = 70

WHITE = "#F0D9B5"
BROWN = "#B58863"
GREEN = "#90EE90"

pieces = {
    "K": "♔", "Q": "♕", "R": "♖",
    "B": "♗", "N": "♘", "P": "♙",

    "k": "♚", "q": "♛", "r": "♜",
    "b": "♝", "n": "♞", "p": "♟"
}


# =====================================================
# BOARD
# =====================================================

board = [
    list("rnbqkbnr"),
    list("pppppppp"),
    list("........"),
    list("........"),
    list("........"),
    list("........"),
    list("PPPPPPPP"),
    list("RNBQKBNR")
]


# =====================================================
# WINDOW
# =====================================================

root = tk.Tk()
root.title("Offline Chess")

canvas = tk.Canvas(
    root,
    width=SIZE * 8,
    height=SIZE * 8
)

canvas.pack()

selected = None
game_over = False


# =====================================================
# DRAW BOARD
# =====================================================

def draw():

    canvas.delete("all")

    for r in range(8):

        for c in range(8):

            color = (
                WHITE
                if (r + c) % 2 == 0
                else BROWN
            )

            if selected == (r, c):
                color = GREEN

            canvas.create_rectangle(
                c * SIZE,
                r * SIZE,
                (c + 1) * SIZE,
                (r + 1) * SIZE,
                fill=color
            )

            piece = board[r][c]

            if piece != ".":

                canvas.create_text(
                    c * SIZE + SIZE / 2,
                    r * SIZE + SIZE / 2,
                    text=pieces[piece],
                    font=("Arial", 45)
                )


# =====================================================
# CHECK IF MOVE IS BASICALLY VALID
# =====================================================

def valid_move(sr, sc, er, ec):

    piece = board[sr][sc]

    target = board[er][ec]

    # Cannot capture own piece

    if target != ".":

        if target.isupper() == piece.isupper():
            return False

    dr = er - sr
    dc = ec - sc

    # Pawn

    if piece.upper() == "P":

        direction = -1 if piece.isupper() else 1

        if dc == 0 and target == ".":

            if dr == direction:
                return True

            if (
                dr == 2 * direction
                and (
                    sr == 6
                    if piece.isupper()
                    else sr == 1
                )
                and board[sr + direction][sc] == "."
            ):
                return True

        if abs(dc) == 1 and dr == direction:
            return target != "."

        return False

    # Knight

    if piece.upper() == "N":

        return (
            (abs(dr), abs(dc))
            in [(1, 2), (2, 1)]
        )

    # King

    if piece.upper() == "K":

        return (
            max(abs(dr), abs(dc)) == 1
        )

    # Rook

    if piece.upper() == "R":

        if dr != 0 and dc != 0:
            return False

        return clear_path(
            sr, sc, er, ec
        )

    # Bishop

    if piece.upper() == "B":

        if abs(dr) != abs(dc):
            return False

        return clear_path(
            sr, sc, er, ec
        )

    # Queen

    if piece.upper() == "Q":

        if not (
            dr == 0
            or dc == 0
            or abs(dr) == abs(dc)
        ):
            return False

        return clear_path(
            sr, sc, er, ec
        )

    return False


# =====================================================
# PATH CHECK
# =====================================================

def clear_path(sr, sc, er, ec):

    dr = (er - sr)

    if dr:
        dr = dr // abs(dr)

    dc = (ec - sc)

    if dc:
        dc = dc // abs(dc)

    r = sr + dr
    c = sc + dc

    while (r, c) != (er, ec):

        if board[r][c] != ".":
            return False

        r += dr
        c += dc

    return True


# =====================================================
# MAKE MOVE
# =====================================================

def move(sr, sc, er, ec):

    piece = board[sr][sc]

    board[er][ec] = piece

    board[sr][sc] = "."

    # Pawn promotion

    if piece == "P" and er == 0:
        board[er][ec] = "Q"

    if piece == "p" and er == 7:
        board[er][ec] = "q"


# =====================================================
# PLAYER CLICK
# =====================================================

def click(event):

    global selected

    if game_over:
        return

    r = event.y // SIZE
    c = event.x // SIZE

    # Select piece

    if selected is None:

        if (
            board[r][c] != "."
            and board[r][c].isupper()
        ):

            selected = (r, c)

        draw()

        return

    sr, sc = selected

    # Move

    if valid_move(
        sr, sc, r, c
    ):

        move(
            sr, sc, r, c
        )

        selected = None

        draw()

        # Computer turn

        root.after(
            300,
            computer_move
        )

    else:

        selected = None

        draw()


# =====================================================
# COMPUTER
# =====================================================

def computer_move():

    moves = []

    for sr in range(8):

        for sc in range(8):

            piece = board[sr][sc]

            if (
                piece != "."
                and piece.islower()
            ):

                for er in range(8):

                    for ec in range(8):

                        if valid_move(
                            sr, sc, er, ec
                        ):

                            moves.append(
                                (sr, sc, er, ec)
                            )

    if not moves:

        messagebox.showinfo(
            "Game Over",
            "You win!"
        )

        return

    # Prefer captures

    captures = []

    for move_data in moves:

        sr, sc, er, ec = move_data

        if board[er][ec] != ".":

            captures.append(
                move_data
            )

    if captures:

        chosen = random.choice(
            captures
        )

    else:

        chosen = random.choice(
            moves
        )

    move(*chosen)

    draw()


# =====================================================
# NEW GAME
# =====================================================

def new_game():

    global board, selected, game_over

    board = [
        list("rnbqkbnr"),
        list("pppppppp"),
        list("........"),
        list("........"),
        list("........"),
        list("........"),
        list("PPPPPPPP"),
        list("RNBQKBNR")
    ]

    selected = None
    game_over = False

    draw()


# =====================================================
# BUTTON
# =====================================================

button = tk.Button(
    root,
    text="New Game",
    font=("Arial", 12),
    command=new_game
)

button.pack(pady=8)


# =====================================================
# START
# =====================================================

canvas.bind(
    "<Button-1>",
    click
)

draw()

root.mainloop()
