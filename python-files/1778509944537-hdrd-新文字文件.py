import random

board = [[0,0,0],[0,0,0],[0,0,0]]

lines = [
    [(0,0),(0,1),(0,2)],
    [(1,0),(1,1),(1,2)],
    [(2,0),(2,1),(2,2)],
    [(0,0),(1,0),(2,0)],
    [(0,1),(1,1),(2,1)],
    [(0,2),(1,2),(2,2)],
    [(0,0),(1,1),(2,2)],
    [(0,2),(1,1),(2,0)]
]

def show():
   
    print("4B390044,\n棋盤：")
    for row in board:
        line = []
        for x in row:
            if x == 1:
                line.append("X")
            elif x == -1:
                line.append("O")
            else:
                line.append(".")
        print(" ".join(line))
    print()

def check():
    for line in lines:
        s = sum(board[r][c] for r,c in line)
        if s == 3:
            return "電腦(X)贏"
        if s == -3:
            return "玩家(O)贏"
    return None

def is_full():
    return all(board[r][c] != 0 for r in range(3) for c in range(3))

def player():
    while True:
        try:
            n = int(input("請輸入位置(1-9): "))
            if n < 1 or n > 9:
                print("❌ 請輸入1~9")
                continue

            r = (n-1)//3
            c = (n-1)%3

            if board[r][c] != 0:
                print("❌ 這格已被佔用")
                continue

            board[r][c] = -1
            break
        except:
            print("❌ 輸入錯誤")

def ai():
    for line in lines:
        if sum(board[r][c] for r,c in line) == 2:
            for r,c in line:
                if board[r][c] == 0:
                    board[r][c] = 1
                    return

    for line in lines:
        if sum(board[r][c] for r,c in line) == -2:
            for r,c in line:
                if board[r][c] == 0:
                    board[r][c] = 1
                    return

    if board[1][1] == 0:
        board[1][1] = 1
        return

    empty = [(r,c) for r in range(3) for c in range(3) if board[r][c] == 0]
    if empty:
        r,c = random.choice(empty)
        board[r][c] = 1

while True:
    show()

    player()
    if check():
        show()
        print(check())
        input("按 Enter 結束...")
        break
    if is_full():
        show()
        print("平手")
        input("按 Enter 結束...")
        break

    ai()
    if check():
        show()
        print(check())
        input("按 Enter 結束...")
        break
    if is_full():
        show()
        print("平手")
        input("按 Enter 結束...")
        break
