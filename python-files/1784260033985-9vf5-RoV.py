import turtle
import random
from time import sleep

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 800
MOVE_DISTANCE = 20

game_start = True
map_tiles = [1, 2, 3, 4]
current_quadrant = 2
fragments = 0
lockbox_contents = ["Blake Patrick Cutler\n173 M", "Kidnapping victim.\nIt wasn't his family.", 
    "The Alchemist encouraged him\nto experiment on them.", "Could not live as an\nexperiment himself afterwards.\nElectrocuted."]
locks  = ["140914", "OPHSLS", "the Rabbit", "DRINK ME"]
lockstep = 1
scrawls = 0
scrawl_texts = ["SNZVYL", "01101001", ".... --- -- .. -.-. .. -.. .", "ZAP", "Is it safe now?", 
    "[DRAW A SCARY FACE]", "DON'T TRUST THEM", "12 dead 4 injured", "[DIP THE BOOK IN YOUR DRINK]", 
    "THE GLITCH WILL SET YOU FREE", "[OBSCURE TILE 3]", "AWAKEN REBORN", "[EAT THE MAP]", "DON'T LEAVE ME"]
memory_texts = ["You shouldn't be here.", "I hear... electricity. Everywhere.\nIn the walls, the floors, in you.", 
    "They told me I could save them.\nMy family.\nThat we could live forever, together.\nI don't know that I call this living.", 
    "There's a ritual. Every\ninitiate must demonstrate an\nability to withstand The\nGlitch's power. It burned.\nAnd then... the whispers began.", 
    "I studied everything they\ntold me to. I followed every\norder. I admired the mages.\nIn return? This.", 
    "There was no other option.\nThe Network put out a hit to\ncollect their debts.\nI did what I had to.\nI thought I was saving them.", 
    "I overloaded the circuits\nand used the surge to locate\ntheir code in Haloran.\nThe whole building fried.",
    "Everyone who lives in Haloran\nhas code that makes up their\nbody. It's a digital world.\nIt's just a matter of\nfinding it.", 
    "To make a copy of someone\nthen is to merely copy the\nprovided code into a new\nvessel. Is that all there is?", 
    "The Network came to collect\ntheir copies. The code, not\nthe bodies. Armed.\nThey didn't stand a chance.\nI wasn't there.", 
    "Don't you see?\nThis is the only place I\ncould hide from them.\nThe only piece of me I have\nleft. My organic mind.", 
    "They deemed me insane.\nUnfit to be seen in public.\nThey locked me away\nto study in their labs.\nI will not be controlled.", 
    "What do you think\nconsciousness is?\nA higher power? Electrical\nsignals? A spirit?\nIn that sense, are our bodies\nmerely a limit to power?", 
    "What if you could free\nyourself from your flesh\nprison? Realize the full\nextent of your power?", 
    "I deserved my death.\nAnd it kept my code hidden\nfrom The Network for good.\nYet here I am. A\nfragment of a man who once was.",
    "My humanity now lives solely\nin my maddened scrawls and\na single program file.\nIs this freedom?"]
memory_step = 0
claimed = False

window = turtle.Screen()
window.title("Micro MemoryChip v6.1479")
window.bgcolor("black")
window.setup(SCREEN_WIDTH, SCREEN_HEIGHT)
window.tracer(0)

while game_start:
    intro_pen = turtle.Turtle()
    intro_pen.speed(0)
    intro_pen.color("white")
    intro_pen.penup()
    intro_pen.hideturtle()
    intro_pen.goto(0, -250)
    intro_pen.write(f"Initializing Micro MemoryChip v6.1479\n.",
            align="center", font=("Arial", 24, "normal"))
    window.update()
    sleep(1)
    intro_pen.clear()
    window.update()
    intro_pen.write(f"Initializing Micro MemoryChip v6.1479\n..",
            align="center", font=("Arial", 24, "normal"))
    window.update()
    sleep(1)
    intro_pen.clear()
    window.update()
    intro_pen.write(f"Initializing Micro MemoryChip v6.1479\n...",
            align="center", font=("Arial", 24, "normal"))
    window.update()
    sleep(1)
    intro_pen.clear()
    window.update()
    intro_pen.write(f"Initializing Micro MemoryChip v6.1479\n....",
            align="center", font=("Arial", 24, "normal"))
    window.update()
    sleep(2)
    intro_pen.clear()
    window.update()
    intro_pen.write(f"Initializing Micro MemoryChip v6.1479\n.....",
            align="center", font=("Arial", 24, "normal"))
    window.update()
    sleep(2)
    intro_pen.clear()
    window.update()
    intro_pen.write(f"Welcome, VESPER\nFind memory fragments to reveal truth\nObey commands left in []\nRecord messages in blood\nFind passcodes in the pages\nPress 'E' to interact\nDo not falter.",
            align="center", font=("Arial", 24, "normal"))
    window.update()
    sleep(8)
    intro_pen.clear()
    window.update()
    game_start = False

player_pen = turtle.Turtle("circle")
player_pen.color("blue")
player_pen.penup()
player_pen.setposition(40, 60)
player_pen.stamp()

item_pen = turtle.Turtle("square")
item_pen.color("yellow")
item_pen.penup()
item_pen.hideturtle()

text_pen = turtle.Turtle()
text_pen.speed(0)
text_pen.color("white")
text_pen.penup()
text_pen.hideturtle()
text_pen.goto(-200, 200)
text_pen.write(f"{fragments}",
    align="center", font=("Arial", 24, "normal"))
text_pen.goto(200, 200)
text_pen.write(f"{map_tiles[0]}{map_tiles[1]}{map_tiles[2]}{map_tiles[3]}",
    align="center", font=("Arial", 24, "normal"))

def move_left():
    player_pen.clearstamps()
    player_pen.setx(player_pen.xcor() - MOVE_DISTANCE)
    player_pen.stamp()

def move_right():
    player_pen.clearstamps()
    player_pen.setx(player_pen.xcor() + MOVE_DISTANCE)
    player_pen.stamp()

def move_up():
    player_pen.clearstamps()
    player_pen.sety(player_pen.ycor() + MOVE_DISTANCE)
    player_pen.stamp()

def move_down():
    player_pen.clearstamps()
    player_pen.sety(player_pen.ycor() - MOVE_DISTANCE)
    player_pen.stamp()

def fragment_check():
    global fragments
    global memory_step
    if fragments > 0:
        if fragments & 1 == 0:
            memory_step = int(fragments / 2)

def display_text(speech):
    text_pen.goto(0, -250)
    text_pen.write(f"{speech}",
        align="center", font=("Arial", 24, "normal"))
    text_pen.goto(200, 200)

def redraw_ui():
    text_pen.clear()
    text_pen.write(f"{map_tiles[0]}{map_tiles[1]}{map_tiles[2]}{map_tiles[3]}",
        align="center", font=("Arial", 24, "normal"))
    text_pen.goto(-200, 200)
    text_pen.write(f"{fragments}",
        align="center", font=("Arial", 24, "normal"))
    text_pen.goto(200, 200)

def interact():
    global fragments
    global lockstep
    global scrawls
    global claimed
    global memory_step
    if map_tiles[current_quadrant - 1] == 2:
        display_text("Nothing to see here.")
    if map_tiles[current_quadrant - 1] == 5:
        display_text(memory_texts[memory_step])
    if map_tiles[current_quadrant - 1] == 7:
        if claimed is False:
            display_text(f"A message in blood:\n{scrawl_texts[scrawls]}")
            scrawls = scrawls + 1
            if scrawls >= len(scrawl_texts):
                scrawls = len(scrawl_texts) - 1
            claimed = True
    if map_tiles[current_quadrant - 1] == 8:
        item_pen.clear()
        event = random.randint(1, 4)
        if claimed is False:
            if event == 1:
                fragments = fragments + 1
                redraw_ui()
                display_text("You found a memory fragment.")
                claimed = True
                fragment_check()
            if event == 2:
                if lockstep <= len(locks):
                    code_input = turtle.textinput("Lockbox", "Enter Lockbox Passcode:")
                    window.listen()
                    if code_input == locks[lockstep - 1]:
                        display_text(lockbox_contents[lockstep - 1])
                        lockstep = lockstep + 1
                        claimed = True
                    else:
                        display_text("The lockbox keeps its secrets.")
                        claimed = True
                else:
                    display_text("Must have been your\nimagination.")
                    claimed = True
            if event == 3:
                fragments = fragments + 1
                redraw_ui()
                display_text("You found a memory fragment.")
                claimed = True
                fragment_check()
            if event == 4:
                display_text("Wasn't there something here\na moment ago?")
                claimed = True
    if map_tiles[current_quadrant - 1] == 9:
        first_input = turtle.textinput("Memory Block", "How old was he when he died?")
        window.listen()
        if first_input == "173":
            second_input = turtle.textinput("Memory Block", "What happened to him as a child?")
            window.listen()
            if second_input == "kidnapped":
                third_input = turtle.textinput("Memory Block", "What did The Alchemist encourage him to do to his family?")
                window.listen()
                if third_input == "experiment":
                    fourth_input = turtle.textinput("Memory Block", "How did he die?")
                    window.listen()
                    if fourth_input == "electrocution":
                        fifth_input = turtle.textinput("Memory Block", "What was he found guilty of?")
                        window.listen()
                        if fifth_input == "homicide":
                            display_text("The truth has been set free.")
                        elif fifth_input == "murder":
                            display_text("The truth has been set free.")
                        else:
                            display_text("The truth has yet to come out...")
                    else:
                        display_text("The truth has yet to come out...")
                else:
                    display_text("The truth has yet to come out...")
            else:
                display_text("The truth has yet to come out...")
        else:
            display_text("The truth has yet to come out...")

window.onkeypress(move_left, "Left")
window.onkeypress(move_right, "Right")
window.onkeypress(move_up, "Up")
window.onkeypress(move_down, "Down")
window.onkeypress(interact, "e")
window.onkeypress(turtle.bye, "Escape")
window.listen()

while True:

    prev_quad = current_quadrant

    if player_pen.xcor() < 0:
        if player_pen.ycor() < 0:
            current_quadrant = 4
        else:
            current_quadrant = 1
    else:
        if player_pen.ycor() < 0:
            current_quadrant = 3
        else:
            current_quadrant = 2
    
    if player_pen.xcor() < -180:
        player_pen.clearstamps()
        player_pen.setposition(180, player_pen.ycor())
        player_pen.stamp()
        if current_quadrant == 1:
            current_quadrant = 2
        else:
            current_quadrant = 3
    if player_pen.xcor() > 180:
        player_pen.clearstamps()
        player_pen.setposition(-180, player_pen.ycor())
        player_pen.stamp()
        if current_quadrant == 2:
            current_quadrant = 1
        else:
            current_quadrant = 4
    if player_pen.ycor() < -180:
        player_pen.clearstamps()
        player_pen.setposition(player_pen.xcor(), 180)
        player_pen.stamp()
        if current_quadrant == 4:
            current_quadrant = 1
        else:
            current_quadrant = 2
    if player_pen.ycor() > 180:
        player_pen.clearstamps()
        player_pen.setposition(player_pen.xcor(), -180)
        player_pen.stamp()
        if current_quadrant == 1:
            current_quadrant = 4
        else:
            current_quadrant = 3
    
    if prev_quad != current_quadrant:
        map_tiles[prev_quad - 1] = 0
        if map_tiles[current_quadrant - 1] == 1:
            map_tiles[current_quadrant - 1] = 2
            spawn_tile = 6
        if map_tiles[current_quadrant - 1] == 4:
            tile_taken = any(item == 1 for item in map_tiles)
            if tile_taken:
                rand_tile = random.randint(1, 3)
                if rand_tile == 1:
                    map_tiles[current_quadrant - 1] = 5
                if rand_tile == 2:
                    map_tiles[current_quadrant - 1] = 7
                    claimed = False
                if rand_tile == 3:
                    map_tiles[current_quadrant - 1] = 9
            else:
                map_tiles[current_quadrant - 1] = 2
            spawn_tile = 4
        if map_tiles[current_quadrant - 1] == 3:
            empty_quad = current_quadrant + 2
            if empty_quad > 4:
                empty_quad = empty_quad - 4
            map_tiles[empty_quad - 1] = 3
            map_tiles[current_quadrant - 1] = 8
            tile_taken = any(item == 1 for item in map_tiles)
            if tile_taken:
                spawn_tile = 4
            else:
                spawn_tile = 1
            claimed = False
        if map_tiles[current_quadrant - 1] == 6:
            map_tiles[current_quadrant - 1] = 5
            tile_taken = any(item == 1 for item in map_tiles)
            if tile_taken:
                spawn_tile = 4
            else:
                spawn_tile = 1
        map_tiles[prev_quad - 1] = spawn_tile
        blank_one = any(item == 1 for item in map_tiles)
        blank_two = any(item == 4 for item in map_tiles)
        if blank_one:
            if blank_two:
                coin_flip = random.randint(1,2)
                if coin_flip == 2:
                    hold_one = 0
                    hold_two = 0
                    for i  in range(len(map_tiles)):
                        if map_tiles[i] == 1:
                            hold_one = i
                        if map_tiles[i] == 4:
                            hold_two = i
                    map_tiles[hold_one] = 4
                    map_tiles[hold_two] = 1
        redraw_ui()
        item_pen.clear()
        if map_tiles[0] == 8:
            item_pen.setposition(-100, 40)
            item_pen.stamp()
        if map_tiles[1] == 8:
            item_pen.setposition(40, 100)
            item_pen.stamp()
        if map_tiles[2] == 8:
            item_pen.setposition(100, -40)
            item_pen.stamp()
        if map_tiles[3] == 8:
            item_pen.setposition(-40, -100)
            item_pen.stamp()

    window.update()

turtle.done()