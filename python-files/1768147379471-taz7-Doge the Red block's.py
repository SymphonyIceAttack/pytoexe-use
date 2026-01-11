import tkinter as tk
import random

WIDTH = 400
HEIGHT = 500

root = tk.Tk()
root.title("Ultra Light Dodger")

canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="black")
canvas.pack()

player = canvas.create_rectangle(180, 450, 220, 480, fill="blue")
enemies = []
score = 0

score_text = canvas.create_text(10, 10, anchor="nw", fill="white", text="Score: 0")

def move_left(event):
    canvas.move(player, -20, 0)

def move_right(event):
    canvas.move(player, 20, 0)

def spawn_enemy():
    x = random.randint(0, WIDTH - 30)
    enemy = canvas.create_rectangle(x, 0, x+30, 30, fill="red")
    enemies.append(enemy)

def game_loop():
    global score

    if random.randint(1, 15) == 1:
        spawn_enemy()

    for enemy in enemies[:]:
        canvas.move(enemy, 0, 10)
        if canvas.coords(enemy)[1] > HEIGHT:
            canvas.delete(enemy)
            enemies.remove(enemy)
            score += 1
            canvas.itemconfig(score_text, text=f"Score: {score}")

        if canvas.coords(enemy) and canvas.coords(player):
            ex1, ey1, ex2, ey2 = canvas.coords(enemy)
            px1, py1, px2, py2 = canvas.coords(player)
            if ex1 < px2 and ex2 > px1 and ey1 < py2 and ey2 > py1:
                canvas.create_text(200, 250, fill="white", text="GAME OVER", font=("Arial", 24))
                return

    root.after(50, game_loop)

root.bind("<Left>", move_left)
root.bind("<Right>", move_right)

game_loop()
root.mainloop()
