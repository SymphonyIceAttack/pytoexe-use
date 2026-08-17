import chess

# -----------------------------
# SETTINGS
# -----------------------------

board = chess.Board()

# Simple piece values for computer
VALUE = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}


# -----------------------------
# DISPLAY BOARD
# -----------------------------

def show_board():

    print("\n" + "=" * 45)
    print("                 CHESS")
    print("=" * 45)

    print("       A   B   C   D   E   F   G   H")
    print("     +---+---+---+---+---+---+---+---+")

    for rank in range(8, 0, -1):

        print(f"  {rank}  |", end="")

        for file in range(8):

            square = chess.square(file, rank - 1)
            piece = board.piece_at(square)

            if piece:
                symbol = piece.symbol()
            else:
                symbol = " "

            print(f" {symbol} |", end="")

        print(f"  {rank}")
        print("     +---+---+---+---+---+---+---+---+")

    print("       A   B   C   D   E   F   G   H")

    print("\nWhite: UPPERCASE")
    print("Black: lowercase")

    if board.is_check():
        print("\n*** CHECK! ***")

    print()


# -----------------------------
# EVALUATE POSITION
# -----------------------------

def evaluate():

    score = 0

    for piece_type in VALUE:

        score += (
            len(board.pieces(piece_type, chess.WHITE))
            * VALUE[piece_type]
        )

        score -= (
            len(board.pieces(piece_type, chess.BLACK))
            * VALUE[piece_type]
        )

    return score


# -----------------------------
# MINIMAX AI
# -----------------------------

def minimax(depth, maximizing):

    if depth == 0 or board.is_game_over():
        return evaluate()

    moves = list(board.legal_moves)

    if maximizing:

        best = -999999

        for move in moves:

            board.push(move)

            score = minimax(
                depth - 1,
                False
            )

            board.pop()

            best = max(best, score)

        return best

    else:

        best = 999999

        for move in moves:

            board.push(move)

            score = minimax(
                depth - 1,
                True
            )

            board.pop()

            best = min(best, score)

        return best


# -----------------------------
# COMPUTER MOVE
# -----------------------------

def computer_move():

    print("\nComputer is thinking...")

    best_move = None
    best_score = 999999

    moves = list(board.legal_moves)

    for move in moves:

        board.push(move)

        score = minimax(
            2,
            True
        )

        board.pop()

        if score < best_score:

            best_score = score
            best_move = move

    board.push(best_move)

    print("Computer played:", best_move)


# -----------------------------
# GAME STATUS
# -----------------------------

def game_finished():

    if board.is_checkmate():

        print("\n" + "=" * 45)
        print("              CHECKMATE")
        print("=" * 45)

        if board.turn == chess.WHITE:
            print("Computer wins!")
        else:
            print("You win!")

        return True

    if board.is_stalemate():

        print("\nDRAW - STALEMATE")
        return True

    if board.is_insufficient_material():

        print("\nDRAW - INSUFFICIENT MATERIAL")
        return True

    if board.is_fivefold_repetition():

        print("\nDRAW - REPETITION")
        return True

    if board.is_seventyfive_moves():

        print("\nDRAW - 75 MOVE RULE")
        return True

    return False


# -----------------------------
# PLAYER MOVE
# -----------------------------

def player_move(command):

    parts = command.lower().split()

    if len(parts) != 2:
        print("Use: e2 e4")
        return False

    try:

        start = chess.parse_square(parts[0])
        end = chess.parse_square(parts[1])

    except ValueError:

        print("Invalid square.")
        return False

    piece = board.piece_at(start)

    if piece is None:

        print("There is no piece there.")
        return False

    if piece.color != chess.WHITE:

        print("You can only move White pieces.")
        return False

    move = chess.Move(
        start,
        end
    )

    # Automatic queen promotion
    if (
        piece.piece_type == chess.PAWN
        and chess.square_rank(end) in [0, 7]
    ):

        move = chess.Move(
            start,
            end,
            promotion=chess.QUEEN
        )

    if move not in board.legal_moves:

        print("Illegal chess move.")
        return False

    board.push(move)

    return True


# -----------------------------
# MAIN GAME
# -----------------------------

print("""
=============================================
              PYTHON CHESS
=============================================

You are WHITE.
Computer is BLACK.

Enter moves like:

    e2 e4
    g1 f3
    e1 g1       <- castling

Commands:

    moves       Show legal moves
    history     Show move history
    undo        Undo last player/computer move
    quit        Exit game

=============================================
""")

while True:

    show_board()

    if game_finished():
        break

    command = input("Your move > ").strip()

    if command.lower() == "quit":
        print("Game closed.")
        break

    # Show legal moves
    if command.lower() == "moves":

        print("\nLegal moves:")

        moves = list(board.legal_moves)

        for i in range(0, len(moves), 8):

            print(
                " ".join(
                    str(m)
                    for m in moves[i:i + 8]
                )
            )

        continue

    # Show history
    if command.lower() == "history":

        print("\nMove history:")

        for i, move in enumerate(
            board.move_stack,
            start=1
        ):

            print(
                f"{i}. {move}"
            )

        continue

    # Undo
    if command.lower() == "undo":

        if len(board.move_stack) >= 2:

            board.pop()
            board.pop()

            print("Last two moves undone.")

        else:

            print("Nothing to undo.")

        continue

    # Player move
    if not player_move(command):
        continue

    # Check game
    if game_finished():
        show_board()
        break

    # Computer
    computer_move()

    if game_finished():
        show_board()
        break
