import turtle
import random

# -------------------------
# Set up the screen
# -------------------------

wn = turtle.Screen()
wn.title("Snake Game")
wn.bgcolor("blue")
wn.setup(width=700, height=700)
wn.tracer(0)


# -------------------------
# Create the snake head
# -------------------------

head = turtle.Turtle()
head.speed(0)
head.shape("circle")
head.color("green")
head.penup()
head.goto(0, 0)
head.direction = "up"


# -------------------------
# Create the food
# -------------------------

food = turtle.Turtle()
food.speed(0)
food.shape("circle")
food.color("red")
food.penup()
food.goto(100, 100)


# -------------------------
# Create snake body
# -------------------------

segments = []


# -------------------------
# Game variables
# -------------------------

game_over = False


# -------------------------
# GAME OVER text
# -------------------------

game_over_text = turtle.Turtle()
game_over_text.speed(0)
game_over_text.color("white")
game_over_text.penup()
game_over_text.hideturtle()


# -------------------------
# TRY AGAIN text
# -------------------------

try_again_text = turtle.Turtle()
try_again_text.speed(0)
try_again_text.color("yellow")
try_again_text.penup()
try_again_text.hideturtle()


# -------------------------
# Create clickable button
# -------------------------

try_again_button = turtle.Turtle()
try_again_button.speed(0)
try_again_button.shape("square")
try_again_button.color("yellow")
try_again_button.penup()
try_again_button.shapesize(
    stretch_wid=1.5,
    stretch_len=5
)
try_again_button.goto(0, -30)

# Hide the button until game over
try_again_button.hideturtle()


# -------------------------
# Movement functions
# -------------------------

def go_up():
    if head.direction != "down" and not game_over:
        head.direction = "up"


def go_down():
    if head.direction != "up" and not game_over:
        head.direction = "down"


def go_left():
    if head.direction != "right" and not game_over:
        head.direction = "left"


def go_right():
    if head.direction != "left" and not game_over:
        head.direction = "right"


# -------------------------
# Keyboard controls
# -------------------------

wn.listen()

wn.onkeypress(go_up, "Up")
wn.onkeypress(go_down, "Down")
wn.onkeypress(go_left, "Left")
wn.onkeypress(go_right, "Right")


# -------------------------
# Move the snake
# -------------------------

def move():

    global game_over

    # Stop if game is over
    if game_over:
        return


    # -------------------------
    # Move snake body
    # -------------------------

    for index in range(len(segments) - 1, 0, -1):

        x = segments[index - 1].xcor()
        y = segments[index - 1].ycor()

        segments[index].goto(x, y)


    # Move first body segment
    if len(segments) > 0:

        segments[0].goto(
            head.xcor(),
            head.ycor()
        )


    # -------------------------
    # Move the snake head
    # -------------------------

    if head.direction == "up":
        head.sety(head.ycor() + 20)

    if head.direction == "down":
        head.sety(head.ycor() - 20)

    if head.direction == "left":
        head.setx(head.xcor() - 20)

    if head.direction == "right":
        head.setx(head.xcor() + 20)


    # -------------------------
    # Check if snake eats food
    # -------------------------

    if head.distance(food) < 20:

        # Put food in random position

        x = random.randint(-330, 330)
        y = random.randint(-330, 330)

        food.goto(x, y)


        # Create new snake segment

        new_segment = turtle.Turtle()
        new_segment.speed(0)
        new_segment.shape("circle")
        new_segment.color("lightgreen")
        new_segment.penup()

        segments.append(new_segment)


    # -------------------------
    # Check if snake hits wall
    # -------------------------

    if (
        head.xcor() > 340
        or head.xcor() < -340
        or head.ycor() > 340
        or head.ycor() < -340
    ):

        # Game over

        game_over = True
        head.direction = "stop"

        # Hide food

        food.hideturtle()


        # -------------------------
        # Show GAME OVER
        # -------------------------

        game_over_text.goto(0, 50)

        game_over_text.write(
            "GAME OVER!",
            align="center",
            font=("Arial", 30, "bold")
        )


        # -------------------------
        # Show TRY AGAIN text
        # -------------------------

        try_again_text.goto(0, -30)

        try_again_text.write(
            "TRY AGAIN",
            align="center",
            font=("Arial", 20, "bold")
        )


        # -------------------------
        # Show clickable button
        # -------------------------

        try_again_button.showturtle()


    else:

        # Continue moving

        wn.ontimer(move, 100)


    # Update screen

    wn.update()


# -------------------------
# Restart the game
# -------------------------

def restart_game(x, y):

    global game_over

    # Only restart when game is over

    if game_over:

        # Remove all snake body segments

        for segment in segments:
            segment.goto(1000, 1000)

        segments.clear()


        # Reset snake head

        head.goto(0, 0)
        head.direction = "up"


        # Reset food

        food.goto(100, 100)
        food.showturtle()


        # Hide GAME OVER text

        game_over_text.clear()

        # Hide TRY AGAIN text

        try_again_text.clear()

        # Hide button

        try_again_button.hideturtle()


        # Reset game

        game_over = False


        # Start game again

        move()


# -------------------------
# Make the button clickable
# -------------------------

try_again_button.onclick(restart_game)


# -------------------------
# Start the game
# -------------------------

move()


# -------------------------
# Keep game running
# -------------------------

wn.mainloop()