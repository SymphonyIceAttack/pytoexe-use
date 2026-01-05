import tkinter as tk
import random

WIDTH, HEIGHT = 520, 580
PLAY_W, PLAY_H = 520, 520
SIZE = 20
BG = "#0f172a"       # dark blue
GRID = "#1e293b"
SNAKE_HEAD = "#22c55e"
SNAKE_BODY = "#16a34a"
FOOD = "#ef4444"
TEXT = "#e5e7eb"

class SnakeGame:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Snake Game")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)

        # Top bar
        self.top = tk.Frame(self.root, bg=BG)
        self.top.pack(fill="x", pady=6)

        self.title = tk.Label(self.top, text="🐍 Snake Game", fg=TEXT, bg=BG,
                              font=("Arial", 18, "bold"))
        self.title.pack(side="left", padx=12)

        self.score_var = tk.StringVar(value="Score: 0")
        self.score_lbl = tk.Label(self.top, textvariable=self.score_var,
                                  fg=TEXT, bg=BG, font=("Arial", 14))
        self.score_lbl.pack(side="right", padx=12)

        # Canvas
        self.canvas = tk.Canvas(self.root, width=PLAY_W, height=PLAY_H,
                                bg=BG, highlightthickness=0)
        self.canvas.pack(padx=10, pady=10)

        # Controls
        self.controls = tk.Frame(self.root, bg=BG)
        self.controls.pack(pady=6)

        tk.Button(self.controls, text="Restart", command=self.restart,
                  bg="#22c55e", fg="black", font=("Arial", 12, "bold"),
                  relief="flat", padx=16, pady=6).pack()

        self.root.bind("<Up>", lambda e: self.set_dir("Up"))
        self.root.bind("<Down>", lambda e: self.set_dir("Down"))
        self.root.bind("<Left>", lambda e: self.set_dir("Left"))
        self.root.bind("<Right>", lambda e: self.set_dir("Right"))

        self.restart()
        self.root.mainloop()

    def restart(self):
        self.direction = "Right"
        self.snake = [(100, 100), (80, 100), (60, 100)]
        self.food = self.new_food()
        self.score = 0
        self.running = True
        self.score_var.set("Score: 0")
        self.draw()
        self.tick()

    def new_food(self):
        x = random.randrange(0, PLAY_W, SIZE)
        y = random.randrange(0, PLAY_H, SIZE)
        return (x, y)

    def set_dir(self, d):
        opp = {"Up":"Down","Down":"Up","Left":"Right","Right":"Left"}
        if d != opp[self.direction]:
            self.direction = d

    def tick(self):
        if not self.running:
            return

        hx, hy = self.snake[0]
        if self.direction == "Up": hy -= SIZE
        if self.direction == "Down": hy += SIZE
        if self.direction == "Left": hx -= SIZE
        if self.direction == "Right": hx += SIZE

        new = (hx, hy)

        if hx < 0 or hx >= PLAY_W or hy < 0 or hy >= PLAY_H or new in self.snake:
            self.game_over()
            return

        self.snake.insert(0, new)

        if new == self.food:
            self.score += 1
            self.score_var.set(f"Score: {self.score}")
            self.food = self.new_food()
        else:
            self.snake.pop()

        self.draw()
        self.root.after(90, self.tick)

    def draw_grid(self):
        for i in range(0, PLAY_W, SIZE):
            self.canvas.create_line(i, 0, i, PLAY_H, fill=GRID)
        for i in range(0, PLAY_H, SIZE):
            self.canvas.create_line(0, i, PLAY_W, i, fill=GRID)

    def draw(self):
        self.canvas.delete("all")
        self.draw_grid()

        # Food (circle)
        fx, fy = self.food
        self.canvas.create_oval(fx+3, fy+3, fx+SIZE-3, fy+SIZE-3, fill=FOOD, outline="")

        # Snake
        for i, (x, y) in enumerate(self.snake):
            color = SNAKE_HEAD if i == 0 else SNAKE_BODY
            self.canvas.create_rectangle(x+1, y+1, x+SIZE-1, y+SIZE-1,
                                         fill=color, outline="")

    def game_over(self):
        self.running = False
        self.canvas.create_rectangle(60, 200, PLAY_W-60, 320, fill="#020617", outline="")
        self.canvas.create_text(PLAY_W//2, 240, text="Game Over",
                                fill=TEXT, font=("Arial", 26, "bold"))
        self.canvas.create_text(PLAY_W//2, 280, text="Press Restart to play again",
                                fill=TEXT, font=("Arial", 14))

SnakeGame()
