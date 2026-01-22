import pygame
import sys

pygame.init()

WIDTH, HEIGHT = 720, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("中國象棋 · 米格魯兵")

BOARD_SIZE = 9
CELL = 70
OFFSET_X = 60
OFFSET_Y = 80

FONT = pygame.font.SysFont("msjh", 28)

WHITE = (245, 222, 179)
BLACK = (0, 0, 0)
RED = (180, 0, 0)

beagle_img = pygame.image.load("beagle_pawn.png")
beagle_img = pygame.transform.scale(beagle_img, (CELL-10, CELL-10))

board = [[None for _ in range(9)] for _ in range(10)]

for i in range(0, 9, 2):
    board[3][i] = "R_PAWN"
    board[6][i] = "B_PAWN"

selected = None
turn = "R"

def draw_board():
    screen.fill(WHITE)
    for i in range(10):
        pygame.draw.line(screen, BLACK,
            (OFFSET_X, OFFSET_Y + i * CELL),
            (OFFSET_X + 8 * CELL, OFFSET_Y + i * CELL), 2)
    for j in range(9):
        pygame.draw.line(screen, BLACK,
            (OFFSET_X + j * CELL, OFFSET_Y),
            (OFFSET_X + j * CELL, OFFSET_Y + 9 * CELL), 2)

def draw_pieces():
    for r in range(10):
        for c in range(9):
            piece = board[r][c]
            if piece:
                x = OFFSET_X + c * CELL
                y = OFFSET_Y + r * CELL
                if "PAWN" in piece:
                    screen.blit(beagle_img, (x+5, y+5))

def get_cell(pos):
    x, y = pos
    c = (x - OFFSET_X) // CELL
    r = (y - OFFSET_Y) // CELL
    if 0 <= r < 10 and 0 <= c < 9:
        return int(r), int(c)
    return None

def reset_game():
    global board, turn, selected
    board = [[None for _ in range(9)] for _ in range(10)]
    for i in range(0, 9, 2):
        board[3][i] = "R_PAWN"
        board[6][i] = "B_PAWN"
    turn = "R"
    selected = None

def draw_button():
    pygame.draw.rect(screen, RED, (260, 730, 200, 50))
    text = FONT.render("重新開始", True, WHITE)
    screen.blit(text, (320, 742))

while True:
    draw_board()
    draw_pieces()
    draw_button()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos

            if 260 <= mx <= 460 and 730 <= my <= 780:
                reset_game()

            cell = get_cell((mx, my))
            if cell:
                r, c = cell
                if selected:
                    sr, sc = selected
                    board[r][c] = board[sr][sc]
                    board[sr][sc] = None
                    selected = None
                    turn = "B" if turn == "R" else "R"
                else:
                    piece = board[r][c]
                    if piece and piece.startswith(turn):
                        selected = (r, c)

    pygame.display.flip()
