import tkinter as tk
import random

WIDTH = 800
HEIGHT = 600

root = tk.Tk()
root.title("Killer & Gadfly - Ultimate Mode")
canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="skyblue")
canvas.pack()

PLAYER_SPEED = 6
score = 0
lives = 3
level = "easy"
game_state = "menu"

objects = {}
loop_job = None
pressed_keys = set()
hit_cooldown = 0
killer_active_delay = 0


def random_pos_away_from_player(size=20):
    while True:
        x = random.randint(50, WIDTH-70)
        y = random.randint(70, HEIGHT-70)
        px1, py1, px2, py2 = canvas.coords(objects["player"])
        if abs(x - px1) > 80 and abs(y - py1) > 80:
            return x, y
def spawn_target():
    x, y = random_pos_away_from_player()
    canvas.coords(objects["target"], x, y, x+20, y+20)
def spawn_health():
    x, y = random_pos_away_from_player()
    canvas.coords(objects["health"], x, y, x+25, y+25)
def create_objects():
    canvas.delete("all")
    global objects
    objects = {
        "player": canvas.create_rectangle(390, 300, 410, 320, fill="green"),
        "killer": canvas.create_rectangle(380, 560, 400, 580, fill="maroon"),
        "target": canvas.create_rectangle(350, 250, 370, 270, fill="white"),
        "health": canvas.create_rectangle(200, 200, 225, 225, fill="pink"),

        "top": canvas.create_rectangle(380, 0, 400, 20, fill="red"),
        "bottom": canvas.create_rectangle(380, 580, 400, 600, fill="red"),
        "left": canvas.create_rectangle(0, 280, 20, 300, fill="red"),
        "right": canvas.create_rectangle(780, 280, 800, 300, fill="red"),
    }
    spawn_target()
    spawn_health()
def move_horizontal(obj, target_x, speed):
    x1, _, x2, _ = canvas.coords(obj)
    c = (x1 + x2) / 2
    if c < target_x: canvas.move(obj, speed, 0)
    elif c > target_x: canvas.move(obj, -speed, 0)
def move_vertical(obj, target_y, speed):
    _, y1, _, y2 = canvas.coords(obj)
    c = (y1 + y2) / 2
    if c < target_y: canvas.move(obj, 0, speed)
    elif c > target_y: canvas.move(obj, 0, -speed)
def move_towards(obj, target, speed):
    ox1, oy1, ox2, oy2 = canvas.coords(obj)
    tx1, ty1, tx2, ty2 = canvas.coords(target)

    cx = (ox1 + ox2) / 2
    cy = (oy1 + oy2) / 2
    tx = (tx1 + tx2) / 2
    ty = (ty1 + ty2) / 2

    if cx < tx: canvas.move(obj, speed, 0)
    if cx > tx: canvas.move(obj, -speed, 0)
    if cy < ty: canvas.move(obj, 0, speed)
    if cy > ty: canvas.move(obj, 0, -speed)
def wrap(obj):
    x1, y1, x2, y2 = canvas.coords(obj)
    if x2 < 0: canvas.move(obj, WIDTH, 0)
    elif x1 > WIDTH: canvas.move(obj, -WIDTH, 0)
    if y2 < 0: canvas.move(obj, 0, HEIGHT)
    elif y1 > HEIGHT: canvas.move(obj, 0, -HEIGHT)
def collide(a, b):
    ax1, ay1, ax2, ay2 = canvas.coords(a)
    bx1, by1, bx2, by2 = canvas.coords(b)
    return not (ax2 < bx1 or ax1 > bx2 or ay2 < by1 or ay1 > by2)
def draw_lives():
    for i in range(3):
        color = "red" if i < lives else "gray"
        canvas.create_rectangle(600 + i*40, 20, 630 + i*40, 50, fill=color, outline="black", tags="hud")
def show_menu():
    global game_state
    game_state = "menu"
    canvas.delete("all")

    canvas.create_text(WIDTH/2, 120,text="Killer and Gadfly",fill="red", font=("Arial", 60, "bold"))
    b1 = tk.Button(root, text="Mudah", font=("Arial", 18), command=lambda: start_game("easy"))
    b2 = tk.Button(root, text="Normal", font=("Arial", 18),  command=lambda: start_game("normal"))
    b3 = tk.Button(root, text="Sulit", font=("Arial", 18), command=lambda: start_game("hard"))
    b4 = tk.Button(root, text="Cara Main", font=("Arial", 18), command=show_rules)
    b5 = tk.Button(root, text="Keluar", font=("Arial", 18),command=root.quit)

    canvas.create_window(WIDTH/2, 240, window=b4)
    canvas.create_window(WIDTH/2, 300, window=b1)
    canvas.create_window(WIDTH/2, 360, window=b2)
    canvas.create_window(WIDTH/2, 420, window=b3)
    canvas.create_window(WIDTH/2, 500, window=b5)
def show_rules():
    global game_state
    game_state = "rules"
    canvas.delete("all")

    # Judul tetap
    canvas.create_text( WIDTH/2, 60, text="CARA MAIN", fill="red",font=("Arial", 40, "bold"))

    # Panel container (biar rapi)
    panel = tk.Frame(root, bg="black")
    panel.place(x=120, y=120, width=560, height=380)

    rules_canvas = tk.Canvas(panel, bg="black", highlightthickness=0)
    rules_canvas.pack(side="left", fill="both", expand=True)

    scrollbar = tk.Scrollbar(panel, orient="vertical", command=rules_canvas.yview)
    scrollbar.pack(side="right", fill="y")

    rules_canvas.configure(yscrollcommand=scrollbar.set)

    inner = tk.Frame(rules_canvas, bg="black")
    rules_canvas.create_window((0, 0), window=inner, anchor="nw")

    text = (
        "🎮 CARA MAIN:\n\n"
        "Kamu = Kotak Hijau\n"
        "• Kotak Putih = +1 POIN\n"
        "• Kotak Pink = Tambah NYAWA (maks 3)\n"
        "• Gadfly Merah = Kurangi poin (tidak bisa kurang dari 0)\n"
        "• Killer = Kurangi NYAWA\n\n"
        "🔥 KEUNIKAN GAME\n"
        "• Killer aktif 2 detik setelah mulai\n"
        "• Saat player mati → respawn + killer delay 2 detik\n"
        "• Killer bisa mencuri:\n"
        "   - Kotak poin → hanya respawn\n"
        "   - Kotak nyawa → hanya respawn\n"
        "  (tanpa mempengaruhi player)\n\n"
        "⚙️ LEVEL SPEED\n"
        "Mudah  = Killer lebih lambat dari player\n"
        "Normal = Sama cepat\n"
        "Sulit  = 2x lebih cepat\n\n"
        "❤️ SISTEM NYAWA\n"
        "• Nyawa awal 3\n"
        "• Bisa bertambah jika < 3\n"
        "• Maksimal tetap 3\n\n"
        "⏸ PAUSE / RESUME\n"
        "• Pause = Tekan P\n"
        "• Lanjut = Tekan tombol apapun\n\n"
        "✨ Tips Bermain\n"
        "• Jangan terlalu dekat dengan killer saat awal aktif\n"
        "• Prioritaskan nyawa saat tinggal sedikit\n"
        "• Hati-hati gadfly 😈\n"
    )

    tk.Label(inner,text=text,font=("Arial", 18),fg="white", bg="black",justify="left",wraplength=520 ).pack(padx=15, pady=15)

    def resize(event):
        rules_canvas.configure(scrollregion=rules_canvas.bbox("all"))
    inner.bind("<Configure>", resize)

    # mouse scroll
    def scroll(event):
        rules_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    rules_canvas.bind_all("<MouseWheel>", scroll)

    # tombol kembali
    btn = tk.Button( root, text="Kembali ke Menu",font=("Arial", 18), command=lambda: (panel.destroy(), rules_canvas.unbind_all("<MouseWheel>"), show_menu()))
    canvas.create_window(WIDTH/2, HEIGHT - 60, window=btn)
def start_game(lv):
    global level, score, lives, hit_cooldown, killer_active_delay, game_state
    level = lv
    score = 0
    lives = 3
    hit_cooldown = 0
    killer_active_delay = 60
    create_objects()
    game_state = "ready"
    canvas.create_text(
        WIDTH/2,
        HEIGHT/2,
        text="BERSIAPLAH\n\nTekan tombol apapun untuk mulai",
        fill="black",
        font=("Arial", 36, "bold"),
        tags="ready"
    )
def begin_play(event=None):
    global game_state
    if game_state == "ready":
        game_state = "playing"
        canvas.delete("ready")
        run_game()
def run_game():
    global score, lives, loop_job, game_state, hit_cooldown, killer_active_delay
    if game_state != "playing":
        return
    canvas.delete("hud")
    canvas.create_text(120, 40, text=f"Poin : {score}",fill="red", font=("Arial", 24, "bold"), tags="hud")
    draw_lives()

    player = objects["player"]
    killer = objects["killer"]

    wrap(player)

    px1, py1, px2, py2 = canvas.coords(player)
    player_x = (px1 + px2) / 2
    player_y = (py1 + py2) / 2

    if level == "easy":
        kspeed = int(PLAYER_SPEED * 0.6)
    elif level == "normal":
        kspeed = PLAYER_SPEED
    else:
        kspeed = PLAYER_SPEED * 2

    if killer_active_delay > 0:
        killer_active_delay -= 1
    else:
        move_towards(killer, player, kspeed)
    move_horizontal(objects["top"], player_x, 3)
    move_horizontal(objects["bottom"], player_x, 3)
    move_vertical(objects["left"], player_y, 3)
    move_vertical(objects["right"], player_y, 3)

    if collide(player, objects["target"]):
        score += 1
        spawn_target()
    if collide(player, objects["health"]):
        if lives < 3:
            lives += 1
            spawn_health()
    if collide(killer, objects["target"]):
        spawn_target()
    if collide(killer, objects["health"]):
        spawn_health()
    if hit_cooldown > 0:
        hit_cooldown -= 1
    if collide(player, killer) and hit_cooldown == 0 and killer_active_delay <= 0:
        lives -= 1
        hit_cooldown = 25
        killer_active_delay = 60
        reset_positions()
        if lives <= 0:
            show_end()
            return
    if (collide(player, objects["top"]) or
        collide(player, objects["bottom"]) or
        collide(player, objects["left"]) or
        collide(player, objects["right"])):
        if score > 0:
            score -= 1
    for key in pressed_keys:
        if key == "Up": canvas.move(player, 0, -PLAYER_SPEED)
        if key == "Down": canvas.move(player, 0, PLAYER_SPEED)
        if key == "Left": canvas.move(player, -PLAYER_SPEED, 0)
        if key == "Right": canvas.move(player, PLAYER_SPEED, 0)
    loop_job = root.after(30, run_game)
def reset_positions():
    canvas.coords(objects["player"], 390, 300, 410, 320)
    canvas.coords(objects["killer"], 380, 560, 400, 580)
def key_down(event):
    global game_state
    if game_state == "playing":
        pressed_keys.add(event.keysym)
        if event.keysym.lower() == "p":
            pause_game()
    elif game_state == "ready":
        begin_play()
    elif game_state == "pause":
        resume_any()
def key_up(event):
    if event.keysym in pressed_keys:
        pressed_keys.remove(event.keysym)
def pause_game():
    global game_state
    game_state = "pause"
    if loop_job:
        root.after_cancel(loop_job)
    canvas.create_text(WIDTH/2, HEIGHT/2,text="PAUSE\nTekan tombol apapun untuk lanjut",fill="yellow", font=("Arial", 36, "bold"), tags="pause")
def resume_any():
    global game_state
    if game_state == "pause":
        game_state = "playing"
        canvas.delete("pause")
        run_game()
def show_end():
    global game_state
    game_state = "end"
    canvas.delete("all")
    canvas.create_text(WIDTH/2, 200,text=f"Game Over!\nPoin : {score}",fill="white",  font=("Arial", 48), justify="center")

    again = tk.Button(root, text="Main Lagi", font=("Arial", 18), command=lambda: start_game(level))
    menu = tk.Button(root, text="Kembali ke Menu", font=("Arial", 18), command=show_menu)
    quitb = tk.Button(root, text="Keluar", font=("Arial", 18), command=root.quit)

    canvas.create_window(WIDTH/2, 330, window=again)
    canvas.create_window(WIDTH/2, 400, window=menu)
    canvas.create_window(WIDTH/2, 470, window=quitb)
root.bind("<KeyPress>", key_down)
root.bind("<KeyRelease>", key_up)

show_menu()
root.mainloop()