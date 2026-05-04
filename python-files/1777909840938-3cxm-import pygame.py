from ursina import *

app = Ursina()

window.title = "Mini Minecraft 3D"

# simple player
player = FirstPersonController()

# create ground blocks
blocks = []

for x in range(-10, 11):
    for z in range(-10, 11):
        block = Button(
            parent=scene,
            position=(x, 0, z),
            model='cube',
            color=color.green,
            origin_y=0.5,
            scale=1
        )
        blocks.append(block)

# place / destroy blocks
def input(key):
    if key == 'left mouse down' and mouse.hovered_entity:
        destroy(mouse.hovered_entity)

    if key == 'right mouse down' and mouse.hovered_entity:
        pos = mouse.hovered_entity.position + mouse.normal
        Button(
            parent=scene,
            position=pos,
            model='cube',
            color=color.brown,
            origin_y=0.5,
            scale=1
        )

app.run()