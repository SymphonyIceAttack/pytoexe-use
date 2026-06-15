import turtle
import random
import time

# Настройка экрана
screen = turtle.Screen()
screen.setup(width=800, height=800)
screen.bgcolor("black")  # Меняем фон на черный, чтобы фейерверки выглядели ярко
screen.title("Для мамы")
screen.tracer(0)  # Включаем ручное обновление экрана для плавной анимации

# Создаем черепашку для сердца
t = turtle.Turtle()
t.hideturtle()
t.speed(0)


# Функция для рисования дуги сердца
def draw_curve():
    for _ in range(200):
        t.right(1)
        t.forward(2)


# Рисуем сердце
t.penup()
t.goto(0, -150)  # Сдвигаем ниже, чтобы освободить место для салюта
t.pendown()
t.color("crimson")
t.begin_fill()
t.fillcolor("crimson")
t.left(140)
t.forward(224)
draw_curve()
t.left(120)
draw_curve()
t.forward(224)
t.end_fill()

# Пишем текст
t.penup()
t.goto(0, -220)
t.color("white")
t.write(
    "С днём рождения, любимая мама!",
    align="center",
    font=("Arial", 22, "bold")
)
screen.update()

# --- КЛАСС ДЛЯ ФЕЙЕРВЕРКОВ ---
colors = ["#FF1493", "#00FFFF", "#FFD700", "#FF4500", "#00FF00", "#9400D3", "#FF00FF"]


class Firework:
    def __init__(self):
        # Случайная точка взрыва в верхней части экрана
        self.x = random.randint(-300, 300)
        self.y = random.randint(100, 320)
        self.color = random.choice(colors)
        self.particles = []

        # Создаем частицы («искры» салюта)
        for _ in range(36):
            p = turtle.Turtle()
            p.hideturtle()
            p.shape("circle")
            p.shapesize(0.2)
            p.color(self.color)
            p.penup()
            p.goto(self.x, self.y)
            # Случайное направление и скорость для каждой искры
            p.setheading(random.randint(0, 360))
            p.speed_val = random.uniform(2, 7)
            self.particles.append(p)

        self.lifetime = 40  # Время жизни одного залпа (кадры)

    def update(self):
        if self.lifetime > 0:
            for p in self.particles:
                p.forward(p.speed_val)
                p.dy = -0.15  # Сила тяжести (искры немного падают вниз)
                p.goto(p.xcor(), p.ycor() + p.dy)
                p.showturtle()
            self.lifetime -= 1
            return True
        else:
            # Прячем частицы, когда салют угас
            for p in self.particles:
                p.hideturtle()
                p.clear()
            return False


# Список активных фейерверков
fireworks = []

# Главный цикл анимации салюта
try:
    while True:
        # С вероятностью 10% создаем новый фейерверк в каждом кадре (максимум 5 одновременно)
        if random.random() < 0.1 and len(fireworks) < 5:
            fireworks.append(Firework())

        # Обновляем состояние каждого фейерверка
        for f in fireworks[:]:
            is_alive = f.update()
            if not is_alive:
                fireworks.remove(f)

        screen.update()
        time.sleep(0.03)  # Контроль скорости анимации
except turtle.Terminated:
    pass  # Игнорируем ошибку при закрытии окна мамой
