import tkinter as tk

# Window setup
width, height = 400, 300
root = tk.Tk()
root.title("Bouncy Ball Demo")
canvas = tk.Canvas(root, width=width, height=height, bg="white")
canvas.pack()

# Ball setup
ball_radius = 20
ball_x, ball_y = 50, 50
dx, dy = 4, 4
ball = canvas.create_oval(ball_x - ball_radius, ball_y - ball_radius,
                          ball_x + ball_radius, ball_y + ball_radius,
                          fill="red")

def move_ball():
    global ball_x, ball_y, dx, dy

    # Update ball position
    ball_x += dx
    ball_y += dy

    # Bounce off walls
    if ball_x - ball_radius <= 0 or ball_x + ball_radius >= width:
        dx = -dx
    if ball_y - ball_radius <= 0 or ball_y + ball_radius >= height:
        dy = -dy

    # Move ball on canvas
    canvas.coords(ball, ball_x - ball_radius, ball_y - ball_radius,
                        ball_x + ball_radius, ball_y + ball_radius)
    
    root.after(30, move_ball)  # ~33 FPS

move_ball()
root.mainloop()
