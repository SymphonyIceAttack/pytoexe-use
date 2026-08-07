import turtle
import random
import time

# =============================================
# تنظیمات صفحه
# =============================================
screen = turtle.Screen()
screen.title("Cube Adventure - Multi Jump")
screen.bgcolor("skyblue")
screen.setup(700, 550)
screen.tracer(0)
screen.listen()

# =============================================
# کلاس بازیکن (مکعب با چشم‌های متحرک)
# =============================================
class Player(turtle.Turtle):
    def __init__(self):
        super().__init__()
        self.shape("square")
        self.color("blue")
        self.shapesize(1.5, 1.5)
        self.penup()
        self.goto(-200, -200)
        self.dy = 0
        self.on_ground = True
        self.is_upside_down = False
        self.max_jumps = 5          # حداکثر تعداد پرش در هوا
        self.jump_count = self.max_jumps  # پرش‌های باقی‌مانده
        
        # چشم‌ها
        self.eye1 = turtle.Turtle()
        self.eye1.shape("circle")
        self.eye1.color("white")
        self.eye1.penup()
        
        self.eye2 = turtle.Turtle()
        self.eye2.shape("circle")
        self.eye2.color("white")
        self.eye2.penup()
        
        self.pupil1 = turtle.Turtle()
        self.pupil1.shape("circle")
        self.pupil1.color("black")
        self.pupil1.shapesize(0.3, 0.3)
        self.pupil1.penup()
        
        self.pupil2 = turtle.Turtle()
        self.pupil2.shape("circle")
        self.pupil2.color("black")
        self.pupil2.shapesize(0.3, 0.3)
        self.pupil2.penup()
        
        self.update_eyes()
    
    def jump(self):
        """پرش چندگانه (تا ۵ بار متوالی)"""
        if self.on_ground:
            self.dy = 10
            self.on_ground = False
            self.jump_count = self.max_jumps - 1  # یک پرش استفاده شد
            self.flip()
        elif self.jump_count > 0 and not self.on_ground:
            self.dy = 9
            self.jump_count -= 1
            self.flip()
    
    def flip(self):
        self.is_upside_down = not self.is_upside_down
    
    def update(self):
        self.dy -= 0.6
        new_y = self.ycor() + self.dy
        self.sety(new_y)
        
        if self.ycor() <= -200:
            self.sety(-200)
            self.dy = 0
            self.on_ground = True
            self.jump_count = self.max_jumps  # شارژ کامل پرش‌ها
        
        self.update_eyes()
    
    def update_eyes(self):
        if self.is_upside_down:
            self.eye1.goto(self.xcor() - 8, self.ycor() - 8)
            self.eye2.goto(self.xcor() + 8, self.ycor() - 8)
            self.pupil1.goto(self.xcor() - 6, self.ycor() - 6)
            self.pupil2.goto(self.xcor() + 10, self.ycor() - 6)
        else:
            self.eye1.goto(self.xcor() - 8, self.ycor() + 8)
            self.eye2.goto(self.xcor() + 8, self.ycor() + 8)
            self.pupil1.goto(self.xcor() - 6, self.ycor() + 10)
            self.pupil2.goto(self.xcor() + 10, self.ycor() + 10)
    
    def get_jump_display(self):
        return f"Jumps: {self.jump_count}"

# =============================================
# کلاس‌های موانع و سکه
# =============================================
class Obstacle(turtle.Turtle):
    def __init__(self, x, y):
        super().__init__()
        self.shape("triangle")
        self.color("red")
        self.shapesize(1, 0.5)
        self.penup()
        self.goto(x, y)
    
    def move(self, speed):
        self.setx(self.xcor() - speed)

class Coin(turtle.Turtle):
    def __init__(self, x, y):
        super().__init__()
        self.shape("circle")
        self.color("gold")
        self.shapesize(0.6, 0.6)
        self.penup()
        self.goto(x, y)
        self.collected = False
    
    def move(self, speed):
        self.setx(self.xcor() - speed)

# =============================================
# توابع تولید
# =============================================
def create_obstacle():
    x = 350
    y = -200
    obs = Obstacle(x, y)
    obstacles.append(obs)

def create_coin():
    x = 350
    y = random.randint(-150, -50)
    coin = Coin(x, y)
    coins.append(coin)

# =============================================
# رویدادها
# =============================================
def jump_click(x, y):
    player.jump()

def move_left():
    player.setx(player.xcor() - 6)

def move_right():
    player.setx(player.xcor() + 6)

def restart_game():
    turtle.bye()

screen.onclick(jump_click)
screen.onkey(move_left, "Left")
screen.onkey(move_right, "Right")
screen.onkey(move_left, "a")
screen.onkey(move_right, "d")
screen.onkey(restart_game, "r")
screen.onkey(restart_game, "R")

# =============================================
# زمین
# =============================================
ground = turtle.Turtle()
ground.penup()
ground.goto(-350, -200)
ground.pendown()
ground.color("green")
ground.pensize(20)
ground.forward(700)
ground.hideturtle()

# =============================================
# متغیرهای بازی
# =============================================
player = Player()
obstacles = []
coins = []
score = 0
level = 1
speed = 5
spawn_timer = 0
spawn_delay = 60
game_over = False

# =============================================
# نمایش امتیاز، سطح و تعداد پرش‌ها
# =============================================
score_pen = turtle.Turtle()
score_pen.penup()
score_pen.hideturtle()
score_pen.goto(-300, 230)
score_pen.color("white")
score_pen.write(f"Score: {score}  Level: {level}", font=("Arial", 16, "bold"))

jump_pen = turtle.Turtle()
jump_pen.penup()
jump_pen.hideturtle()
jump_pen.goto(250, 230)
jump_pen.color("yellow")
jump_pen.write(f"Jumps: {player.jump_count}", font=("Arial", 16, "bold"))

# =============================================
# حلقه اصلی بازی
# =============================================
while not game_over:
    screen.update()
    
    # به‌روزرسانی بازیکن
    player.update()
    
    # تولید موانع و سکه
    spawn_timer += 1
    if spawn_timer >= spawn_delay:
        spawn_timer = 0
        if random.random() < 0.7:
            create_obstacle()
        if random.random() < 0.4:
            create_coin()
    
    # حرکت موانع
    for obs in obstacles[:]:
        obs.move(speed)
        if obs.xcor() < -350:
            obs.hideturtle()
            obstacles.remove(obs)
    
    # حرکت سکه‌ها
    for coin in coins[:]:
        coin.move(speed)
        if coin.xcor() < -350:
            coin.hideturtle()
            coins.remove(coin)
    
    # برخورد با موانع
    for obs in obstacles:
        if (abs(player.xcor() - obs.xcor()) < 20 and
            abs(player.ycor() - obs.ycor()) < 20):
            game_over = True
            break
    
    # جمع‌آوری سکه
    for coin in coins[:]:
        if not coin.collected:
            if (abs(player.xcor() - coin.xcor()) < 20 and
                abs(player.ycor() - coin.ycor()) < 20):
                coin.collected = True
                coin.hideturtle()
                coins.remove(coin)
                score += 50
                if random.random() < 0.5:
                    player.flip()
                else:
                    player.dy = 7
    
    # افزایش امتیاز
    score += 1
    
    # افزایش سطح
    new_level = score // 120 + 1
    if new_level > level:
        level = new_level
        speed += 1.2
        spawn_delay = max(25, spawn_delay - 6)
    
    # به‌روزرسانی نمایشگرها
    score_pen.clear()
    score_pen.write(f"Score: {score}  Level: {level}", font=("Arial", 16, "bold"))
    
    jump_pen.clear()
    jump_pen.write(f"Jumps: {player.jump_count}", font=("Arial", 16, "bold"))
    
    time.sleep(0.015)

# =============================================
# صفحه Game Over
# =============================================
game_over_pen = turtle.Turtle()
game_over_pen.hideturtle()
game_over_pen.penup()
game_over_pen.color("red")
game_over_pen.goto(0, 0)
game_over_pen.write("GAME OVER", align="center", font=("Arial", 40, "bold"))
game_over_pen.goto(0, -40)
game_over_pen.color("white")
game_over_pen.write(f"Score: {score}  Level: {level}", align="center", font=("Arial", 20, "bold"))
game_over_pen.goto(0, -80)
game_over_pen.color("yellow")
game_over_pen.write("Press R to restart", align="center", font=("Arial", 16, "bold"))

turtle.done()