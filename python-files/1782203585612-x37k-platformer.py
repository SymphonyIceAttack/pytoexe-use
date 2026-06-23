import tkinter as tk

WIDTH = 800
HEIGHT = 500
GROUND_Y = 450
PLAYER_W = 30
PLAYER_H = 30
GRAVITY = 0.6
JUMP_VELOCITY = -12
MOVE_SPEED = 5

class Platformer:
    def __init__(self, root):
        self.root = root
        self.root.title("One File Platformer")
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="#1b1f2a", highlightthickness=0)
        self.canvas.pack()

        self.keys = set()
        self.running = True

        self.level = [
            (0, GROUND_Y, WIDTH, 50),
            (120, 380, 150, 20),
            (320, 320, 140, 20),
            (520, 260, 140, 20),
            (680, 200, 90, 20),
        ]
        self.goal = (730, 150, 30, 50)
        self.reset()

        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.bind("<KeyRelease>", self.on_key_release)
        self.root.bind("<r>", lambda event: self.reset())
        self.root.bind("<R>", lambda event: self.reset())

        self.loop()

    def reset(self):
        self.player_x = 50
        self.player_y = 380
        self.vx = 0
        self.vy = 0
        self.on_ground = False
        self.won = False
        self.message = "Arrow keys to move, Space to jump, R to restart"

    def on_key_press(self, event):
        self.keys.add(event.keysym)
        if event.keysym == "space" and self.on_ground and not self.won:
            self.vy = JUMP_VELOCITY
            self.on_ground = False
        if event.keysym in ("r", "R"):
            self.reset()

    def on_key_release(self, event):
        self.keys.discard(event.keysym)

    def rects_overlap(self, a, b):
        ax, ay, aw, ah = a
        bx, by, bw, bh = b
        return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by

    def move_and_collide(self):
        self.player_x += self.vx
        player = (self.player_x, self.player_y, PLAYER_W, PLAYER_H)
        for plat in self.level:
            if self.rects_overlap(player, plat):
                if self.vx > 0:
                    self.player_x = plat[0] - PLAYER_W
                elif self.vx < 0:
                    self.player_x = plat[0] + plat[2]
                player = (self.player_x, self.player_y, PLAYER_W, PLAYER_H)

        self.player_y += self.vy
        self.on_ground = False
        player = (self.player_x, self.player_y, PLAYER_W, PLAYER_H)
        for plat in self.level:
            if self.rects_overlap(player, plat):
                if self.vy > 0:
                    self.player_y = plat[1] - PLAYER_H
                    self.vy = 0
                    self.on_ground = True
                elif self.vy < 0:
                    self.player_y = plat[1] + plat[3]
                    self.vy = 0
                player = (self.player_x, self.player_y, PLAYER_W, PLAYER_H)

        self.player_x = max(0, min(WIDTH - PLAYER_W, self.player_x))
        if self.player_y > HEIGHT:
            self.reset()

    def update_logic(self):
        if self.won:
            self.vx = 0
            self.vy = 0
            return

        left = "Left" in self.keys or "a" in self.keys or "A" in self.keys
        right = "Right" in self.keys or "d" in self.keys or "D" in self.keys

        self.vx = 0
        if left:
            self.vx = -MOVE_SPEED
        if right:
            self.vx = MOVE_SPEED

        self.vy += GRAVITY
        if self.vy > 14:
            self.vy = 14

        self.move_and_collide()

        px, py = self.player_x, self.player_y
        gx, gy, gw, gh = self.goal
        if self.rects_overlap((px, py, PLAYER_W, PLAYER_H), self.goal):
            self.won = True
            self.message = "You win! Press R to restart"

    def draw(self):
        self.canvas.delete("all")

        self.canvas.create_text(
            12, 12,
            anchor="nw",
            fill="#d7e1ff",
            font=("Arial", 12),
            text=self.message,
        )

        for x, y, w, h in self.level:
            self.canvas.create_rectangle(x, y, x + w, y + h, fill="#4a5568", outline="")

        gx, gy, gw, gh = self.goal
        self.canvas.create_rectangle(gx, gy, gx + gw, gy + gh, fill="#f6ad55", outline="")
        self.canvas.create_text(gx + gw / 2, gy - 12, fill="#ffd79a", text="GOAL", font=("Arial", 10, "bold"))

        self.canvas.create_rectangle(
            self.player_x,
            self.player_y,
            self.player_x + PLAYER_W,
            self.player_y + PLAYER_H,
            fill="#63b3ed",
            outline="#bee3f8",
            width=2,
        )

        if self.won:
            self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#000000", outline="", stipple="gray25")
            self.canvas.create_text(
                WIDTH / 2,
                HEIGHT / 2,
                fill="#ffffff",
                text="YOU WIN!\nPress R to play again",
                font=("Arial", 24, "bold"),
                justify="center",
            )

    def loop(self):
        self.update_logic()
        self.draw()
        self.root.after(16, self.loop)


if __name__ == "__main__":
    root = tk.Tk()
    Platformer(root)
    root.mainloop()
