import turtle as t
import time as ti
import random as r
from multiprocessing.resource_sharer import stop
import tkinter as tk
import pygame






pygame.init()





wn = tk.Tk()
wn.geometry("450x450")
wn.title("Launcher")
ht = tk.Button(wn, text="Выход", command=exit)
ht.pack(pady=17)
bt = tk.Button(wn, text="Запуск игры", command=wn.destroy)
bt.pack(pady=20)
wn.mainloop()




screen = t.Screen()
screen.bgcolor("cyan")
screen.setup(width=800, height=600)
screen.tracer(0)

a = 10
b = 20
c = 0

score_turtle = t.Turtle()
score_turtle.hideturtle()
score_turtle.penup()
score_turtle.goto(-350, 250)
score_turtle.color("black")


def update_score():
    score_turtle.clear()
    score_turtle.write(f"Счет: {c}", font=("Arial", 20, "normal"))


update_score()

player = t.Turtle()
player.color("black")
player.shape("turtle")
player.penup()
player.speed(0)
player.goto(0, -150)

enemies = []

for i in range(5):
    enemy1 = t.Turtle()
    enemy1.color("red")
    enemy1.shape("turtle")
    enemy1.penup()
    enemy1.speed(0)
    enemy1.goto(r.randint(-350, 350), r.randint(-200, 200))
    enemy1.setheading(r.randint(0, 360))
    enemies.append({
        "turtle666": enemy1,
        "dx": r.uniform(-3, 3),
        "dy": r.uniform(-3, 3),
    })


bad = []

def bad1_bonus():
    bad1 = t.Turtle()
    bad1 .color("Red")
    bad1 .shape("circle")
    bad1 .shapesize(0.7)
    bad1.penup()
    bad1 .speed(0)
    bad1 .goto(r.randint(-350, 350), r.randint(-200, 200))
    return bad1




bonuses = []


def create_bonus():
    bonuses1 = t.Turtle()
    bonuses1.color("Yellow")
    bonuses1.shape("circle")
    bonuses1.shapesize(0.5)
    bonuses1.penup()
    bonuses1.speed(0)
    bonuses1.goto(r.randint(-350, 350), r.randint(-200, 200))
    return bonuses1


bonused = []


def create_bonused():
    bonusec1 = t.Turtle()
    bonusec1.color("Green")
    bonusec1.shape("circle")
    bonusec1.shapesize(1.3)
    bonusec1.penup()
    bonusec1.speed(0)
    bonusec1.goto(r.randint(-350, 350), r.randint(-200, 200))
    bonusec1.create_time = ti.time()
    return bonusec1


for i in range(1):
    bonused.append(create_bonused())


for i in range(12):
    bad.append(bad1_bonus())

for i in range(7):
    bonuses.append(create_bonus())


def up():
    player.forward(10)


def right():
    player.right(10)


def left():
    player.left(10)


def secret():
    print("Такой кнопки нету!!")


def se():
    print("Ваш счет:", c)


def check_collisions():
    global c

    if c > 50:
        for i in range(10):
            enemy1 = t.Turtle()
            enemy1.color("red")
            enemy1.shape("turtle")
            enemy1.penup()
            enemy1.speed(0)
            enemy1.goto(r.randint(-350, 350), r.randint(-200, 200))
            enemy1.setheading(r.randint(0, 360))
            enemies.append({
                "turtle666": enemy1,
                "dx": r.uniform(-3, 3),
                "dy": r.uniform(-3, 3),
            })


    for bonusek in bonused[:]:
        if player.distance(bonusek) < 20:
            bonusek.goto(41567989, 34567890)
            c += 20
            print("+ 20 баллов")
            update_score()

        current_time = ti.time()
        if current_time - bonusek.create_time > 3:
            bonusek.goto(r.randint(-350, 350), r.randint(-200, 200))
            bonusek.create_time = current_time

    if abs(player.xcor()) > 380 or abs(player.ycor()) > 280:
        player.goto(0, 0)
        c -= 5
        print("Вы вышли за границу")

        update_score()

    for enemy in enemies:
        if player.distance(enemy["turtle666"]) < 20:
            player.goto(0, 0)
            enemy["turtle666"].goto(r.randint(-350, 350), r.randint(-200, 200))
            enemy["dx"] = r.uniform(-3, 3)
            enemy["dy"] = r.uniform(-3, 3)
            c -= 10
            print("Столкновение с врагом -10")
            update_score()

    for bonus in bonuses[:]:
        if player.distance(bonus) < 20:
            bonus.goto(41567989, 34567890)
            bonuses.remove(bonus)
            c += 10
            print("+10 баллов")
            update_score()

        if len(bonuses) < 7:
            new_bonus = create_bonus()
            bonuses.append(new_bonus)

    for bad1 in bad[:]:
        if player.distance(bad1) < 20:
            bad1.goto(41567989, 34567890)
            bad.remove(bad1)
            c -= 10
            print("-10 баллов")
            update_score()

        if len(bonuses) < 5:
            new_bonus = bad1_bonus()
            bad1.append(new_bonus)


screen.listen()
screen.onkeypress(up, "w")
screen.onkeypress(right, "d")
screen.onkeypress(left, "a")
screen.onkeypress(secret, "s")
screen.onkeypress(se, "r")

while True:
    for enemy in enemies:
        x, y = enemy["turtle666"].position()
        dx, dy = enemy["dx"], enemy["dy"]

        if abs(x + dx) > 380:
            enemy["dx"] *= -1
        if abs(y + dy) > 280:
            enemy["dy"] *= -1

        if r.random() < 0.02:
            enemy["dx"] = r.uniform(-3, 3)
            enemy["dy"] = r.uniform(-3, 3)

        enemy["turtle666"].setx(x + enemy["dx"])
        enemy["turtle666"].sety(y + enemy["dy"])
        enemy["turtle666"].setheading(enemy["turtle666"].towards(x + enemy["dx"] * 10, y + enemy["dy"] * 10))

    check_collisions()
    screen.update()
    ti.sleep(0.02)