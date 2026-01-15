from ursina import *

app = Ursina()

# --- Window Settings ---
window.title = "3D Pen Jumper"
window.borderless = False
window.fps_counter.enabled = True
mouse.locked = True  # Lock mouse for camera control

# --- Player ---
pen = Entity(
    model='cylinder',
    color=color.blue,
    scale=(0.2, 2, 0.2),
    position=(0, 2, 0),
    collider='box'
)

# Physics variables
gravity = 9.8
bounce_strength = 7
velocity_y = 0
is_jumping = False

# --- Ground ---
ground = Entity(
    model='cube',
    color=color.gray,
    scale=(20, 1, 20),
    position=(0, 0, 0),
    collider='box'
)

# --- Platforms / Shelves ---
shelf_positions = [
    (0, 2, 5),
    (3, 4, 10),
    (-2, 6, 15),
    (2, 8, 20),
    (0, 10, 25)
]

shelves = []
for pos in shelf_positions:
    shelves.append(Entity(
        model='cube',
        color=color.orange,
        scale=(5, 0.5, 5),
        position=pos,
        collider='box'
    ))

# --- Goal ---
goal = Entity(
    model='sphere',
    color=color.gold,
    scale=2,
    position=(0, 12, 25),
    collider='sphere'
)

# --- Score Text ---
score = 0
score_text = Text(text=f"Score: {score}", position=(-0.85, 0.45), scale=2, color=color.white)

# --- Crosshair ---
crosshair = Entity(
    parent=camera.ui,
    model='quad',
    color=color.red,
    scale=(0.01, 0.01),
    position=(0, 0)  # Center of the screen
)

# --- Camera ---
camera.parent = pen
camera.position = (0, 5, -15)
camera.rotation_x = 10
camera.fov = 105  # Slightly higher FOV for wider view

# --- Update Function ---
win_text_shown = False

def update():
    global velocity_y, is_jumping, score, win_text_shown

    dt = time.dt

    # --- Mouse Look (3rd person style) ---
    mouse_sensitivity = 80  # Smooth control
    pen.rotation_y += mouse.velocity[0] * mouse_sensitivity
    camera.rotation_x -= mouse.velocity[1] * mouse_sensitivity
    camera.rotation_x = clamp(camera.rotation_x, -45, 45)  # Limit up/down

    # --- Movement ---
    move_speed = 10  # Faster movement
    forward = pen.forward * (held_keys['w'] - held_keys['s'])
    right = pen.right * (held_keys['d'] - held_keys['a'])
    pen.position += (forward + right) * move_speed * dt

    # --- Gravity ---
    velocity_y -= gravity * dt
    pen.y += velocity_y * dt

    # --- Collision ---
    hit_info = pen.intersects()
    if hit_info.hit:
        if velocity_y < 0:  # Falling
            pen.y = hit_info.world_point.y + pen.scale_y / 2
            velocity_y = 0
            is_jumping = False

        # --- Win Condition ---
        if hit_info.entity == goal and not win_text_shown:
            Text(text="YOU WIN!", scale=5, origin=(0,0), color=color.yellow)
            destroy(goal)
            win_text_shown = True

    # --- Jump / Bounce ---
    if held_keys['space'] and not is_jumping:
        velocity_y = bounce_strength
        is_jumping = True
        score += 1
        score_text.text = f"Score: {score}"

    # --- Fall Reset ---
    if pen.y < -10:
        pen.position = (0, 2, 0)
        velocity_y = 0
        is_jumping = False
        score = 0
        score_text.text = f"Score: {score}"

# --- Run App ---
app.run()
