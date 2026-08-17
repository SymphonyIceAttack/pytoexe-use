import tkinter as tk
from tkinter import messagebox

# Chess board
board = [
    ["♜","♞","♝","♛","♚","♝","♞","♜"],
    ["♟","♟","♟","♟","♟","♟","♟","♟"],
    ["","","","","","","",""],
    ["","","","","","","",""],
    ["","","","","","","",""],
    ["","","","","","","",""],
    ["♙","♙","♙","♙","♙","♙","♙","♙"],
    ["♖","♘","♗","♕","♔","♗","♘","♖"]
]

white = "♙♖♘♗♕♔"
black = "♟♜♞♝♛♚"

turn = "White"
selected = None
game_over = False


# -------------------------
# Create window
# -------------------------

window = tk.Tk()
window.title("Simple Chess")


# -------------------------
# Display board
# -------------------------

buttons = []

def show_board():

    for r in range(8):
        for c in range(8):

            color = "white" if (r + c) % 2 == 0 else "gray"

            buttons[r][c].config(
                text=board[r][c],
                bg=color
            )

    if selected:
        r, c = selected
        buttons[r][c].config(bg="yellow")


# -------------------------
# Click a square
# -------------------------

def click(r, c):

    global selected
    global turn
    global game_over

    if game_over:
        return

    piece = board[r][c]

    # Select a piece
    if selected is None:

        if piece == "":
            return

        if turn == "White" and piece not in white:
            return

        if turn == "Black" and piece not in black:
            return

        selected = (r, c)
        show_board()

    # Move piece
    else:

        sr, sc = selected

        moving_piece = board[sr][sc]
        captured_piece = board[r][c]

        # Cannot capture own piece
        if captured_piece != "":

            if moving_piece in white and captured_piece in white:
                selected = None
                show_board()
                return

            if moving_piece in black and captured_piece in black:
                selected = None
                show_board()
                return

        # Move piece
        board[r][c] = moving_piece
        board[sr][sc] = ""

        selected = None

        # Check if king was captured
        if captured_piece == "♔":

            game_over = True
            show_board()

            messagebox.showinfo(
                "Game Over",
                "Black wins!"
            )

            return

        if captured_piece == "♚":

            game_over = True
            show_board()

            messagebox.showinfo(
                "Game Over",
                "White wins!"
            )

            return

        # Change turn
        if turn == "White":
            turn = "Black"
        else:
            turn = "White"

        label.config(text=turn + "'s Turn")

        show_board()


# -------------------------
# Create buttons
# -------------------------

for r in range(8):

    row = []

    for c in range(8):

        button = tk.Button(
            window,
            text=board[r][c],
            font=("Arial", 30),
            width=3,
            height=1,
            command=lambda r=r, c=c: click(r, c)
        )

        button.grid(row=r, column=c)

        row.append(button)

    buttons.append(row)


# -------------------------
# Turn label
# -------------------------

label = tk.Label(
    window,
    text="White's Turn",
    font=("Arial", 16)
)

label.grid(
    row=8,
    column=0,
    columnspan=8
)


# -------------------------
# Start
# -------------------------

show_board()

window.mainloop()
