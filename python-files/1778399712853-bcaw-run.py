import turtle
import random
import time

# ====================== 游戏初始化（纯代码，无任何文件）======================
win = turtle.Screen()
win.title("贪吃蛇 - 纯Python单文件版")
win.bgcolor("#1a1a1a")
win.setup(width=600, height=600)
win.tracer(0)

# 蛇头
head = turtle.Turtle()
head.speed(0)
head.shape("square")
head.color("#00ff00")
head.penup()
head.goto(0, 0)
head.direction = "stop"

# 食物
food = turtle.Turtle()
food.speed(0)
food.shape("circle")
food.color("#ff3333")
food.penup()
food.goto(0, 100)

# 蛇身体 & 分数
segments = []
score = 0

# 分数显示
pen = turtle.Turtle()
pen.speed(0)
pen.color("white")
pen.penup()
pen.hideturtle()
pen.goto(0, 260)
pen.write("分数: 0", align="center", font=("Arial", 24, "normal"))

# ====================== 移动控制 ======================


def move():
    if head.direction == "up":
        head.sety(head.ycor() + 20)
    if head.direction == "down":
        head.sety(head.ycor() - 20)
    if head.direction == "left":
        head.setx(head.xcor() - 20)
    if head.direction == "right":
        head.setx(head.xcor() + 20)


def go_up():
    if head.direction != "down":
        head.direction = "up"


def go_down():
    if head.direction != "up":
        head.direction = "down"


def go_left():
    if head.direction != "right":
        head.direction = "left"


def go_right():
    if head.direction != "left":
        head.direction = "right"


# 键盘绑定
win.listen()
win.onkeypress(go_up, "Up")
win.onkeypress(go_down, "Down")
win.onkeypress(go_left, "Left")
win.onkeypress(go_right, "Right")

# ====================== 游戏主循环 ======================
while True:
    win.update()
    time.sleep(0.14)

    # 撞墙死亡
    if head.xcor() > 290 or head.xcor() < -290 or head.ycor() > 290 or head.ycor() < -290:
        time.sleep(1)
        head.goto(0, 0)
        head.direction = "stop"
        for seg in segments:
            seg.goto(1000, 1000)
        segments.clear()
        score = 0
        pen.clear()
        pen.write(f"分数: {score}", align="center", font=("Arial", 24, "normal"))

    # 吃到食物
    if head.distance(food) < 20:
        x = random.randint(-280, 280)
        y = random.randint(-280, 280)
        food.goto(x, y)

        new_segment = turtle.Turtle()
        new_segment.speed(0)
        new_segment.shape("square")
        new_segment.color("#00cc00")
        new_segment.penup()
        segments.append(new_segment)

        score += 10
        pen.clear()
        pen.write(f"分数: {score}", align="center", font=("Arial", 24, "normal"))

    # 身体跟随
    for i in range(len(segments)-1, 0, -1):
        x = segments[i-1].xcor()
        y = segments[i-1].ycor()
        segments[i].goto(x, y)

    if len(segments) > 0:
        x = head.xcor()
        y = head.ycor()
        segments[0].goto(x, y)

    move()

    # 撞身体死亡
    for seg in segments:
        if seg.distance(head) < 20:
            time.sleep(1)
            head.goto(0, 0)
            head.direction = "stop"
            for seg in segments:
                seg.goto(1000, 1000)
            segments.clear()
            score = 0
            pen.clear()
            pen.write(f"分数: {score}", align="center",
                      font=("Arial", 24, "normal"))

win.mainloop()
