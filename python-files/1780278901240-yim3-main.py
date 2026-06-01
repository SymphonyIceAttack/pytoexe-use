import random, math
from tkinter import *
CANVAS_WIDTH, CANVAS_HEIGHT = 640, 480
CENTER_X, CENTER_Y = CANVAS_WIDTH / 2, CANVAS_HEIGHT / 2
HEART_COLOR = "#ff6781"
POINT_RADIUS = 3
FRAME_MS = 50

def heart(t, k=11):
    x = 16 * math.sin(t) ** 3 * k + CENTER_X
    y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)) * k + CENTER_Y
    return int(x), int(y)

class Heart:
    def __init__(self):
        self.t_values = [random.uniform(0, 2 * math.pi) for _ in range(800)]
        self.phase = 0.0
        self.base_scale = 11

    def update(self):
        self.phase += 0.08
        self.scale = self.base_scale + 2.5 * math.sin(self.phase * 1.3)

    def render(self, c):
        for t in self.t_values:
            x, y = heart(t + self.phase, self.scale)
            c.create_oval(
                x - POINT_RADIUS,
                y - POINT_RADIUS,
                x + POINT_RADIUS,
                y + POINT_RADIUS,
                width=0,
                fill=HEART_COLOR,
            )


def draw(root, canvas, heart_obj):
    canvas.delete("all")
    heart_obj.update()
    heart_obj.render(canvas)
    text_size = max(28, int(34 + 8 * math.sin(heart_obj.phase * 1.5)))
    canvas.create_text(
        CENTER_X,
        CENTER_Y,
        text="I ❤ YOU",
        fill="#ff6781",
        font=("Helvetica", text_size, "bold"),
    )
    root.after(FRAME_MS, draw, root, canvas, heart_obj)


if __name__ == '__main__':
    root = Tk()
    root.title("心意")
    root.geometry(f"{CANVAS_WIDTH}x{CANVAS_HEIGHT}")
    root.resizable(False, False)
    canvas = Canvas(root, bg='black', width=CANVAS_WIDTH, height=CANVAS_HEIGHT)
    canvas.pack()
    h = Heart()
    draw(root, canvas, h)
    root.mainloop()