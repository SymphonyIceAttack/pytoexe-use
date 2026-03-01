import turtle
import random
import json
import os
import sys
import math

# ===================== 基础配置 =====================
turtle.title("醒狮科普小乐园")
turtle.setup(width=800, height=600)
turtle.bgcolor("#fff9f0")
turtle.colormode(255)
turtle.hideturtle()
turtle.tracer(0, 0)

# 常量定义
W, H = 800, 600
RED = "#d92121"
YELLOW = "#ffd700"
GREEN = "#008000"
BLACK = "#333333"
GRAY = "#e0e0e0"
WHITE = "#ffffff"
PINK = "#ffd1dc"
LIGHT_PINK = "#fff0f5"
RANK_FILE = "lion_rank.json"

# 字体定义
FONT_LARGE = ("黑体", 24, "bold")
FONT_MEDIUM = ("黑体", 16, "bold")
FONT_SMALL = ("黑体", 12, "normal")
FONT_XLARGE = ("黑体", 32, "bold")
FONT_XXLARGE = ("黑体", 36, "bold")

# ===================== 全局按钮管理 =====================
button_list = []


def register_button(btn_x, btn_y, btn_width, btn_height, callback):
    button_list.append({
        "x": btn_x, "y": btn_y, "width": btn_width, "height": btn_height, "callback": callback
    })


def global_click_handler(x, y):
    if not game.is_running:
        return
    for btn in button_list:
        x1 = btn["x"] - btn["width"]/2
        x2 = btn["x"] + btn["width"]/2
        y1 = btn["y"] - btn["height"]/2
        y2 = btn["y"] + btn["height"]/2
        if (x1 - 0.5) <= x <= (x2 + 0.5) and (y1 - 0.5) <= y <= (y2 + 0.5):
            execute_btn_callback(btn["callback"])
            return


def execute_btn_callback(callback):
    game.clear_timers()
    callback()

# ===================== 全局对象管理 =====================


class TurtleManager:
    def __init__(self):
        self.turtles = {}
        self.button_text_turtles = []
        self.option_turtles = []
        self.color_part_turtles = {}
        self._init_base_turtles()

    def _init_base_turtles(self):
        turtle_types = [
            "bg", "text_main", "text_tip", "text_rank", "text_score",
            "lion", "progress", "countdown", "decor", "lion_img"
        ]
        for turtle_type in turtle_types:
            self.turtles[turtle_type] = self._create_turtle()

    def _create_turtle(self):
        t = turtle.Turtle()
        t.hideturtle()
        t.penup()
        t.speed(0)
        t.color(BLACK)
        return t

    def get(self, turtle_type):
        if turtle_type not in self.turtles:
            self.turtles[turtle_type] = self._create_turtle()
        t = self.turtles[turtle_type]
        t.clear()
        t.penup()
        t.hideturtle()
        return t

    def get_new_button_text_turtle(self):
        t = self._create_turtle()
        self.button_text_turtles.append(t)
        return t

    def clear_all(self):
        for t in self.turtles.values():
            t.clear()
            t.penup()
            t.hideturtle()
        for t in self.button_text_turtles:
            t.clear()
            t.hideturtle()
        self.button_text_turtles = []
        self.option_turtles = []


turtle_manager = TurtleManager()

# ===================== 游戏状态管理 =====================


class GameState:
    def __init__(self):
        self.name = "小狮子"
        self.level = "normal"
        self.score = 0
        self.q_idx = 0
        self.countdown = 15
        self.text_idx = 0
        self.text_pause = False
        self.sound = True
        self.wrong = []
        self.rank = self.load_rank()
        self.timers = []
        self.is_running = True
        self.lion_animation_timer = None

    def load_rank(self):
        if os.path.exists(RANK_FILE):
            try:
                with open(RANK_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data if isinstance(data, list) else []
            except:
                return []
        return []

    def save_rank(self):
        try:
            rank_dict = {}
            all_records = self.rank.copy()
            all_records.append({"name": self.name, "score": self.score})
            for item in all_records:
                if isinstance(item, dict) and "name" in item and "score" in item:
                    name = item["name"].strip()
                    score = int(item["score"])
                    if name not in rank_dict or score > rank_dict[name]:
                        rank_dict[name] = score
            self.rank = [{"name": k, "score": v} for k, v in sorted(
                rank_dict.items(), key=lambda x: x[1], reverse=True)[:10]]
            with open(RANK_FILE, "w", encoding="utf-8") as f:
                json.dump(self.rank, f, ensure_ascii=False, indent=2)
        except:
            pass

    def add_score(self, points=1):
        self.score += points

    def clear_timers(self):
        for timer_id in self.timers:
            try:
                turtle.ontimer(None, timer_id)
            except:
                pass
        self.timers = []
        if self.lion_animation_timer:
            try:
                turtle.ontimer(None, self.lion_animation_timer)
            except:
                pass
        self.lion_animation_timer = None
        self.countdown = 15

    def add_timer(self, timer_id):
        if timer_id not in self.timers and self.is_running:
            self.timers.append(timer_id)

    def set_lion_animation_timer(self, timer_id):
        self.lion_animation_timer = timer_id

    def stop_game(self):
        self.is_running = False
        self.clear_timers()


game = GameState()

# ===================== 绘制工具函数 =====================


def draw_bg_style2():
    """绘制图2风格背景：浅底色+黄色祥云+花卉"""
    bg = turtle_manager.get("bg")
    bg.clear()
    bg.penup()
    bg.goto(-W//2, H//2)
    bg.pendown()
    bg.color("#fff9f0")
    bg.fillcolor("#fff9f0")
    bg.begin_fill()
    for _ in range(2):
        bg.forward(W)
        bg.left(90)
        bg.forward(H)
        bg.left(90)
    bg.end_fill()
    bg.penup()

    pattern = turtle_manager.get("decor")
    pattern.color("#fff2cc")
    pattern.pensize(2)
    # 左上角祥云
    pattern.goto(-380, 220)
    pattern.pendown()
    pattern.circle(60, 180)
    pattern.left(90)
    pattern.circle(60, -180)
    pattern.penup()
    # 右上角祥云
    pattern.goto(380, 220)
    pattern.pendown()
    pattern.circle(60, 180)
    pattern.left(90)
    pattern.circle(60, -180)
    pattern.penup()
    # 左下角祥云
    pattern.goto(-380, -220)
    pattern.pendown()
    pattern.circle(60, 180)
    pattern.left(90)
    pattern.circle(60, -180)
    pattern.penup()
    # 右下角祥云
    pattern.goto(380, -220)
    pattern.pendown()
    pattern.circle(60, 180)
    pattern.left(90)
    pattern.circle(60, -180)
    pattern.penup()

    # 花卉装饰
    pattern.color("#ffb6c1")
    pattern.pensize(1)
    # 左侧花朵
    pattern.goto(-350, 0)
    pattern.pendown()
    pattern.fillcolor("#ffd1dc")
    pattern.begin_fill()
    for _ in range(5):
        pattern.forward(30)
        pattern.left(72)
    pattern.end_fill()
    pattern.penup()
    # 右侧花朵
    pattern.goto(350, 0)
    pattern.pendown()
    pattern.fillcolor("#ffd1dc")
    pattern.begin_fill()
    for _ in range(5):
        pattern.forward(30)
        pattern.left(72)
    pattern.end_fill()
    pattern.penup()

    turtle.update()


def draw_lion_image_corner(x, y, size=120):
    """绘制图3风格醒狮（放在右下角）"""
    lion_img = turtle_manager.get("lion_img")
    lion_img.clear()
    lion_img.penup()
    lion_img.goto(x, y)
    lion_img.color(RED)
    lion_img.pensize(3)

    # 狮头（红金配色，匹配图3）
    lion_img.goto(x, y)
    lion_img.pendown()
    lion_img.fillcolor("#ff4444")
    lion_img.begin_fill()
    lion_img.circle(size)
    lion_img.end_fill()
    lion_img.penup()

    # 白色绒毛边缘
    lion_img.color(WHITE)
    lion_img.pensize(6)
    for angle in range(0, 360, 25):
        lion_img.goto(x + size * 0.85 * math.cos(math.radians(angle)),
                      y + size * 0.85 * math.sin(math.radians(angle)))
        lion_img.pendown()
        lion_img.forward(20)
        lion_img.penup()

    # 眼睛（大而有神）
    for ex in [x-40, x+40]:
        lion_img.goto(ex, y + size - 25)
        lion_img.pendown()
        lion_img.fillcolor(WHITE)
        lion_img.begin_fill()
        lion_img.circle(20)
        lion_img.end_fill()
        lion_img.penup()
        lion_img.goto(ex, y + size - 22)
        lion_img.pendown()
        lion_img.fillcolor(BLACK)
        lion_img.begin_fill()
        lion_img.circle(10)
        lion_img.end_fill()
        lion_img.penup()
        # 眼白高光
        lion_img.goto(ex + 7, y + size - 17)
        lion_img.pendown()
        lion_img.fillcolor(WHITE)
        lion_img.begin_fill()
        lion_img.circle(5)
        lion_img.end_fill()
        lion_img.penup()

    # 鼻子（红色绒球+金色装饰）
    lion_img.goto(x - 25, y + size - 50)
    lion_img.pendown()
    lion_img.fillcolor("#ff4444")
    lion_img.begin_fill()
    for _ in range(3):
        lion_img.forward(50)
        lion_img.left(120)
    lion_img.end_fill()
    lion_img.penup()
    # 金色装饰
    lion_img.color(YELLOW)
    lion_img.pensize(3)
    lion_img.goto(x - 20, y + size - 45)
    lion_img.pendown()
    lion_img.forward(40)
    lion_img.penup()
    lion_img.goto(x, y + size - 55)
    lion_img.pendown()
    lion_img.forward(25)
    lion_img.penup()

    # 嘴巴（微笑弧线）
    lion_img.color(RED)
    lion_img.pensize(4)
    lion_img.goto(x - 45, y + 15)
    lion_img.pendown()
    lion_img.setheading(-60)
    lion_img.circle(50, 120)
    lion_img.penup()

    # 鬃毛（白色波浪纹+金色流苏）
    lion_img.color(WHITE)
    lion_img.pensize(5)
    for i in range(6):
        lion_img.goto(x - size + 15 + i*25, y - size + 15)
        lion_img.pendown()
        lion_img.setheading(90)
        lion_img.circle(12, 180)
        lion_img.penup()
    # 金色流苏
    lion_img.color(YELLOW)
    lion_img.pensize(2)
    for i in range(8):
        lion_img.goto(x - size + 20 + i*15, y - size + 20)
        lion_img.pendown()
        lion_img.setheading(-90)
        lion_img.forward(30)
        lion_img.penup()

    turtle.update()


def draw_lion(x, y, size=30, color=RED):
    lion = turtle_manager.get("lion")
    if not game.is_running:
        return lion
    lion.color(color)
    lion.pensize(2)
    lion.goto(x, y)
    lion.pendown()
    lion.fillcolor(PINK)
    lion.begin_fill()
    lion.circle(size)
    lion.end_fill()
    lion.penup()
    for ex in [x-10, x+10]:
        lion.goto(ex, y+20)
        lion.pendown()
        lion.fillcolor(WHITE)
        lion.begin_fill()
        lion.circle(6)
        lion.end_fill()
        lion.penup()
        lion.goto(ex, y+23)
        lion.pendown()
        lion.dot(5, BLACK)
        lion.penup()
    lion.goto(x-15, y+5)
    lion.pendown()
    lion.setheading(-60)
    lion.circle(15, 120)
    lion.penup()
    for angle in range(0, 360, 45):
        lion.goto(x, y)
        lion.setheading(angle)
        lion.forward(size+5)
        lion.pendown()
        lion.forward(10)
        lion.penup()
    for ex in [x-18, x+18]:
        lion.goto(ex, y-5)
        lion.pendown()
        lion.fillcolor("#ffb6c1")
        lion.begin_fill()
        lion.circle(8)
        lion.end_fill()
        lion.penup()
    turtle.update()
    return lion


def animate_lion(x, y):
    if not game.is_running:
        return
    game.clear_timers()
    lion = draw_lion(x, y, 40)
    delta = [random.randint(-1, 1), random.randint(-1, 1)]
    max_x, max_y = 20, 15
    animation_count = 0
    max_animation = 60

    def swing():
        nonlocal animation_count
        if not game.is_running or animation_count >= max_animation:
            return
        try:
            dx, dy = delta
            if abs(dx) > max_x:
                delta[0] = -dx * 0.8
            if abs(dy) > max_y:
                delta[1] = -dy * 0.8
            lion.clear()
            draw_lion(x + delta[0], y + delta[1], 40)
            delta[0] += random.randint(-1, 1) * 0.5
            delta[1] += random.randint(-1, 1) * 0.4
            animation_count += 1
            if game.is_running and animation_count < max_animation:
                timer_id = turtle.ontimer(swing, 60)
                game.set_lion_animation_timer(timer_id)
        except:
            return
    swing()
    return lion


def create_button(text, x, y, callback, width=120, height=40):
    """仅保留文字，无任何框体"""
    if not game.is_running:
        return None
    btn_text = turtle_manager.get_new_button_text_turtle()
    btn_text.color(RED)
    btn_text.goto(x, y - 3)
    btn_text.write(text, align="center", font=FONT_MEDIUM)
    register_button(x, y, width, height, callback)
    turtle.update()
    return None


def clear_screen():
    if not game.is_running:
        return
    global button_list
    game.clear_timers()
    turtle_manager.clear_all()
    button_list = []
    for key in ["a", "b", "c", "d"]:
        turtle.onkey(None, key)
    turtle.listen()
    turtle.update()

# ===================== 核心功能 =====================


def input_name():
    clear_screen()
    draw_bg_style2()
    # 右下角添加图3醒狮
    draw_lion_image_corner(280, -200, 120)
    title = turtle_manager.get("text_main")
    title.clear()
    title.color(RED)
    title.goto(0, 180)
    title.write("请输入你的名字", align="center", font=FONT_LARGE)
    turtle.update()
    turtle.ontimer(show_name_input, 100)


def show_name_input():
    try:
        name = turtle.textinput("醒狮科普小乐园", "请输入你的名字（最多8个字）：")
        if name and name.strip() and len(name.strip()) <= 8:
            game.name = name.strip()
        else:
            game.name = "小狮子"
    except:
        game.name = "小狮子"
    turtle.tracer(1)
    home()
    turtle.update()


def sound_toggle():
    if not game.is_running:
        return
    game.sound = not game.sound
    tip = turtle_manager.get("text_tip")
    tip.clear()
    tip.color(BLACK)
    tip.goto(350, -250)
    tip.write("🔊 音效已开启" if game.sound else "🔇 音效已关闭",
              align="center", font=FONT_MEDIUM)
    turtle.update()
    timer_id = turtle.ontimer(lambda: tip.clear(), 3000)
    game.add_timer(timer_id)


def show_ranking():
    if not game.is_running:
        return
    clear_screen()
    draw_bg_style2()
    title = turtle_manager.get("text_main")
    title.clear()
    title.color(RED)
    title.goto(0, 220)
    title.write("醒狮文化答题排行榜", align="center", font=FONT_LARGE)
    if not game.rank:
        empty = turtle_manager.get("text_rank")
        empty.clear()
        empty.color(BLACK)
        empty.goto(0, 80)
        empty.write("暂无答题记录，快来挑战吧！", align="center", font=FONT_MEDIUM)
    else:
        y = 120
        medals = ["🏆", "🥈", "🥉"]
        for i, item in enumerate(game.rank[:8]):
            if y < -100:
                break
            rank_t = turtle_manager.get_new_button_text_turtle()
            rank_t.color(BLACK)
            rank_t.goto(-250, y)
            rank_t.write(f"{medals[i] if i < 3 else f'第{i+1}名'}：{item['name']}",
                         align="left", font=("黑体", 14, "bold"))
            score_t = turtle_manager.get_new_button_text_turtle()
            score_t.color(RED)
            score_t.goto(150, y)
            score_t.write(f"{item['score']}分",
                          align="right", font=("黑体", 14, "bold"))
            y -= 30
    create_button("返回首页", 0, -200, home, 140, 45)
    turtle.update()


def color_game():
    if not game.is_running:
        return
    clear_screen()
    draw_bg_style2()
    title = turtle_manager.get("text_main")
    title.clear()
    title.color(RED)
    title.goto(0, 230)
    title.write("醒狮涂色小游戏", align="center", font=FONT_LARGE)
    draw_lion(0, 50, 90, BLACK)
    colors = [("红色", RED), ("黄色", YELLOW), ("绿色", GREEN),
              ("黑色", BLACK), ("重置", "white")]
    x = -280

    def color_handler(color):
        def handler():
            if not game.is_running:
                return
            lion_t = turtle_manager.get("lion")
            lion_t.clear()
            draw_lion(0, 50, 90, color if color != "white" else BLACK)
            tip = turtle_manager.get("text_tip")
            tip.clear()
            tip.color(BLACK)
            tip.goto(0, -180)
            tip.write(f"已选择{name}为醒狮涂色！", align="center", font=FONT_MEDIUM)
            turtle.ontimer(lambda: tip.clear(), 1500)
        return handler
    for name, color in colors:
        create_button(name, x, -160, color_handler(color), 90, 40)
        x += 130
    tip = turtle_manager.get("text_tip")
    tip.clear()
    tip.color(BLACK)
    tip.goto(0, -210)
    tip.write("点击颜色按钮为醒狮涂色，体验传统文化之美", align="center", font=FONT_SMALL)
    create_button("返回首页", 0, -260, home, 140, 45)
    turtle.update()


def show_tip(tip_type):
    if not game.is_running:
        return
    tip = turtle_manager.get("text_tip")
    tip.clear()
    tip.goto(0, -200)
    tip_configs = {
        "right": (GREEN, "🎉 回答正确！"),
        "wrong": (RED, "❌ 回答错误！"),
        "time": ("#ff8c00", "⏰ 时间到啦！")
    }
    color, text = tip_configs.get(tip_type, (BLACK, ""))
    tip.color(color)
    tip.write(text, align="center", font=("黑体", 20, "bold"))
    turtle.update()
    timer_id = turtle.ontimer(lambda: tip.clear(), 2000)
    game.add_timer(timer_id)


def draw_progress_bar(current, total):
    if not game.is_running:
        return
    prog = turtle_manager.get("progress")
    prog.clear()
    prog.color(GRAY)
    prog.goto(-300, -250)
    prog.pendown()
    prog.fillcolor("#f5f5f5")
    prog.begin_fill()
    radius = 12
    prog.forward(radius)
    prog.circle(radius, 90)
    prog.forward(25 - 2*radius)
    prog.circle(radius, 90)
    prog.forward(600 - 2*radius)
    prog.circle(radius, 90)
    prog.forward(25 - 2*radius)
    prog.circle(radius, 90)
    prog.forward(radius)
    prog.end_fill()
    prog.penup()
    progress = min(current / total, 1.0)
    prog.color(RED)
    prog.goto(-300, -250)
    prog.pendown()
    prog.fillcolor(RED)
    prog.begin_fill()
    if progress > 0:
        fill_width = 600 * progress
        if fill_width <= 2*radius:
            prog.circle(radius)
        else:
            prog.forward(radius)
            prog.circle(radius, 90)
            prog.forward(25 - 2*radius)
            prog.circle(radius, 90)
            prog.forward(fill_width - 2*radius)
            if fill_width < 600:
                prog.circle(radius, 90)
                prog.forward(25 - 2*radius)
                prog.circle(radius, 90)
                prog.forward(radius)
            else:
                prog.forward(600 - 2*radius)
                prog.circle(radius, 90)
                prog.forward(25 - 2*radius)
                prog.circle(radius, 90)
                prog.forward(radius)
    prog.end_fill()
    prog.penup()
    txt = turtle_manager.get("text_tip")
    txt.clear()
    txt.color(BLACK)
    txt.goto(0, -270)
    txt.write(f"进度：{current}/{total}", align="center", font=FONT_MEDIUM)
    turtle.update()


def countdown_timer():
    if not game.is_running:
        return
    ct = turtle_manager.get("countdown")
    ct.clear()
    if game.countdown > 5:
        color = RED
    elif game.countdown > 3:
        color = "#ff6666"
    else:
        color = "#ff3333"
    ct.color(color)
    ct.goto(300, 245)
    ct.write(f"{game.countdown}", align="center", font=FONT_LARGE)
    ct.goto(300, 225)
    ct.write("秒", align="center", font=FONT_SMALL)
    if game.countdown > 0:
        game.countdown -= 1
        timer_id = turtle.ontimer(countdown_timer, 1000)
        game.add_timer(timer_id)
    else:
        show_tip("time")
        q_list = get_question_list()
        if game.q_idx < len(q_list):
            q = q_list[game.q_idx]
            fb = turtle_manager.get("text_main")
            fb.clear()
            fb.color(RED)
            fb.goto(0, -150)
            fb.write(f"超时！正确答案是{q['ans']}～{q['exp']}",
                     align="center", font=FONT_MEDIUM)
            game.wrong.append({
                "q": q['q'], "u_ans": "未作答", "c_ans": q['ans'], "exp": q['exp']
            })
            game.q_idx += 1
        if game.is_running:
            timer_id = turtle.ontimer(next_question, 2500)
            game.add_timer(timer_id)
    turtle.update()


def check_answer(selected):
    if not game.is_running:
        return
    q_list = get_question_list()
    if game.q_idx >= len(q_list):
        return
    q = q_list[game.q_idx]
    fb = turtle_manager.get("text_main")
    fb.clear()
    fb.goto(0, -150)
    if selected == q['ans']:
        game.add_score()
        show_tip("right")
        fb.color(GREEN)
        fb.write(f"✅ 正确！{q['exp']}", align="center", font=FONT_MEDIUM)
    else:
        show_tip("wrong")
        fb.color(RED)
        fb.write(f"❌ 错误！正确答案是{q['ans']}～{q['exp']}",
                 align="center", font=FONT_MEDIUM)
        game.wrong.append({
            "q": q['q'], "u_ans": selected, "c_ans": q['ans'], "exp": q['exp']
        })
    turtle.update()
    game.q_idx += 1
    if game.is_running:
        timer_id = turtle.ontimer(next_question, 2500)
        game.add_timer(timer_id)


def get_question_list():
    if game.level == "easy":
        return questions["easy"].copy()
    elif game.level == "hard":
        return questions["easy"] + questions["normal"] + questions["hard"]
    return questions["easy"] + questions["normal"]


def next_question():
    if not game.is_running:
        return
    q_list = get_question_list()
    if game.q_idx < len(q_list):
        game.countdown = 15 if game.level != "hard" else 10
        show_question()
    else:
        game.save_rank()
        clear_screen()
        draw_bg_style2()
        rt = turtle_manager.get("text_main")
        rt.clear()
        rt.color(RED)
        rt.goto(0, 120)
        rt.write(f"🎉 答题完成！{game.name}的得分：", align="center", font=FONT_LARGE)
        st = turtle_manager.get("text_score")
        st.clear()
        st.color(RED)
        st.goto(0, 50)
        st.write(f"{game.score} / {len(q_list)}",
                 align="center", font=("黑体", 48, "bold"))
        lt = turtle_manager.get("text_tip")
        lt.clear()
        lt.goto(0, 0)
        rate = game.score / len(q_list) if len(q_list) > 0 else 0
        ratings = [
            (1.0, "#ff8c00", "🏆 太棒了！你是醒狮文化小专家～"),
            (0.8, GREEN, "🌟 非常优秀！继续保持～"),
            (0.6, GREEN, "👍 不错哦！继续了解醒狮文化吧～"),
            (0.0, RED, "💪 加油！多了解醒狮文化会更棒～")
        ]
        for min_rate, color, text in ratings:
            if rate >= min_rate:
                lt.color(color)
                lt.write(text, align="center", font=FONT_LARGE)
                break

        def review_wrong():
            if not game.is_running:
                return
            clear_screen()
            draw_bg_style2()
            title = turtle_manager.get("text_main")
            title.clear()
            title.color(RED)
            title.goto(0, 200)
            title.write("错题复盘", align="center", font=FONT_LARGE)
            if not game.wrong:
                nw = turtle_manager.get("text_tip")
                nw.clear()
                nw.color(GREEN)
                nw.goto(0, 80)
                nw.write("🎉 恭喜！你没有答错任何题目～", align="center", font=FONT_LARGE)
            else:
                y = 150
                for i, wq in enumerate(game.wrong[:5]):
                    if y < -150:
                        break
                    q_t = turtle_manager.get_new_button_text_turtle()
                    q_t.color(BLACK)
                    q_t.goto(-350, y)
                    q_t.write(f"{i+1}. {wq['q']}",
                              align="left", font=FONT_MEDIUM)
                    a_t = turtle_manager.get_new_button_text_turtle()
                    a_t.color(RED)
                    a_t.goto(-350, y-25)
                    a_t.write(
                        f"你的答案：{wq['u_ans']} | 正确答案：{wq['c_ans']} | {wq['exp']}", align="left", font=FONT_SMALL)
                    y -= 60
            create_button("返回首页", 0, -200, home, 140, 45)
            turtle.update()
        y = -40
        buttons = [
            ("重新答题", reset_quiz),
            ("查看排行榜", show_ranking),
            ("错题复盘", review_wrong),
            ("返回首页", home)
        ]
        for text, func in buttons:
            create_button(text, 0, y, func, 160, 50)
            y -= 70
        turtle.update()


def show_question():
    if not game.is_running:
        return
    clear_screen()
    draw_bg_style2()
    q_list = get_question_list()
    if game.q_idx >= len(q_list):
        next_question()
        return
    q = q_list[game.q_idx]
    info = turtle_manager.get("text_tip")
    info.clear()
    info.color(RED)
    info.goto(-350, 250)
    info.write(f"难度：{game.level} | 第{game.q_idx+1}/{len(q_list)}题 | 得分：{game.score}",
               align="left", font=FONT_MEDIUM)
    qt = turtle_manager.get("text_main")
    qt.clear()
    qt.color(BLACK)
    qt.goto(0, 180)
    qt.write(q['q'], align="center", font=("黑体", 20, "bold"))
    countdown_timer()
    y_positions = [120, 60, 0, -60]
    for key in ["a", "b", "c", "d"]:
        turtle.onkey(None, key)
    for i, (opt, y) in enumerate(zip(q['opt'], y_positions)):
        if i >= 4:
            break
        letter = opt[0]
        width = 300 if len(opt) > 6 else 280
        create_button(opt, 0, y, lambda l=letter: check_answer(l), width, 50)
        turtle.onkey(lambda l=letter: check_answer(l), letter.lower())
    draw_progress_bar(game.q_idx + 1, len(q_list))
    turtle.listen()
    turtle.update()


def reset_quiz():
    if not game.is_running:
        return
    game.clear_timers()
    game.q_idx = 0
    game.score = 0
    game.countdown = 15
    game.wrong = []
    show_question()


def select_difficulty(level):
    if not game.is_running:
        return
    game.level = level
    reset_quiz()


def science_page():
    if not game.is_running:
        return
    clear_screen()
    draw_bg_style2()
    animate_lion(0, 150)
    title = turtle_manager.get("text_main")
    title.clear()
    title.color(RED)
    title.goto(0, 230)
    title.write("醒狮文化科普", align="center", font=FONT_LARGE)
    buttons = [
        ("暂停/继续", -300, -220, lambda: toggle_text_play()),
        ("跳过文字", -160, -220, lambda: skip_text()),
        ("音效开关", -20, -220, sound_toggle),
        ("开始答题", 120, -220, lambda: show_difficulty_select()),
        ("返回首页", 260, -220, home)
    ]
    for text, x, y, func in buttons:
        create_button(text, x, y, func, 120, 40)
    txt = turtle_manager.get("text_main")
    txt.clear()
    txt.color(BLACK)
    txt.penup()

    def display_line():
        if not game.is_running:
            return
        if game.text_idx < len(science_text) and not game.text_pause:
            y = 200 - game.text_idx * 25
            if y > -180:
                txt.goto(-350, y)
                txt.write(science_text[game.text_idx],
                          align="left", font=FONT_MEDIUM)
            game.text_idx += 1
            if game.is_running:
                timer_id = turtle.ontimer(display_line, 800)
                game.add_timer(timer_id)
        elif game.text_idx >= len(science_text):
            tip = turtle_manager.get("text_tip")
            tip.clear()
            tip.color(GREEN)
            tip.goto(300, -200)
            tip.write("✅ 阅读完毕，点击开始答题", align="center", font=FONT_MEDIUM)
    display_line()
    turtle.update()


def toggle_text_play():
    if not game.is_running:
        return
    game.text_pause = not game.text_pause
    tip = turtle_manager.get("text_tip")
    tip.clear()
    tip.color(BLACK)
    tip.goto(-300, -200)
    tip.write("⏸ 文字播放已暂停" if game.text_pause else "▶ 文字播放已继续",
              align="center", font=FONT_MEDIUM)
    if not game.text_pause:
        txt = turtle_manager.get("text_main")
        txt.color(BLACK)

        def continue_play():
            if not game.is_running:
                return
            if game.text_idx < len(science_text) and not game.text_pause:
                y = 200 - game.text_idx * 25
                if y > -180:
                    txt.goto(-350, y)
                    txt.write(science_text[game.text_idx],
                              align="left", font=FONT_MEDIUM)
                game.text_idx += 1
                if game.is_running:
                    timer_id = turtle.ontimer(continue_play, 800)
                    game.add_timer(timer_id)
        continue_play()
    turtle.update()
    timer_id = turtle.ontimer(lambda: tip.clear(), 3000)
    game.add_timer(timer_id)


def skip_text():
    if not game.is_running:
        return
    game.text_idx = len(science_text)
    tip = turtle_manager.get("text_tip")
    tip.clear()
    tip.color(BLACK)
    tip.goto(-180, -200)
    tip.write("⏭ 已跳过文字内容", align="center", font=FONT_MEDIUM)
    timer_id = turtle.ontimer(lambda: tip.clear(), 3000)
    game.add_timer(timer_id)


def show_difficulty_select():
    if not game.is_running:
        return
    clear_screen()
    draw_bg_style2()
    title = turtle_manager.get("text_main")
    title.clear()
    title.color(RED)
    title.goto(0, 180)
    title.write("选择答题难度", align="center", font=FONT_LARGE)
    difficulties = [("简单", "easy", "#90ee90"),
                    ("中等", "normal", YELLOW), ("困难", "hard", "#ff9999")]
    y = 80
    for name, level, color in difficulties:
        create_button(
            name, 0, y, lambda l=level: select_difficulty(l), 220, 60)
        y -= 100
    create_button("返回首页", 0, -140, home, 140, 45)
    turtle.update()


def home():
    if not game.is_running:
        return
    clear_screen()
    draw_bg_style2()
    # 右下角添加图3醒狮
    draw_lion_image_corner(280, -200, 120)
    turtle.tracer(1)
    wel = turtle_manager.get("text_main")
    wel.clear()
    wel.color(RED)
    wel.goto(0, 230)
    wel.write(f"欢迎{game.name}！", align="center", font=FONT_XLARGE)
    wel.goto(0, 180)
    wel.write("醒狮科普小乐园", align="center", font=FONT_XXLARGE)
    button_configs = [
        ("了解醒狮文化", 100, science_page),
        ("醒狮涂色游戏", 20, color_game),
        ("查看排行榜", -60, show_ranking),
        ("更换用户名", -140, input_name)
    ]
    for text, y, func in button_configs:
        create_button(text, 0, y, func, 220, 60)
    create_button("音效开关", 300, -230, sound_toggle, 120, 40)
    turtle.update()


# ===================== 游戏数据 =====================
science_text = [
    "醒狮是中国民间传统表演艺术，起源于三国时期，",
    "盛行于岭南地区，至今已有近2000年历史。",
    "",
    "最初，醒狮是为了驱邪避凶，后来逐渐演变为",
    "庆祝佳节、开业庆典的重要仪式。",
    "",
    "常见醒狮场合：",
    "• 春节拜年  • 元宵灯会  • 店铺开业",
    "• 婚礼庆典  • 大型活动开幕",
    "",
    "醒狮颜色寓意：",
    "• 红色 → 吉祥喜庆  • 黄色 → 尊贵繁荣",
    "• 绿色 → 生机勃勃  • 黑色 → 勇猛无畏",
    "",
    "醒狮表演融合武术、舞蹈、音乐等元素，",
    "通过腾跃、扑跳、甩头等动作，",
    "传递积极向上的精神，被誉为「南狮」。"
]

questions = {
    "easy": [
        {"q": "醒狮起源于哪个时期？", "opt": ["A. 唐朝", "B. 三国时期", "C. 宋朝",
                                    "D. 明朝"], "ans": "B", "exp": "醒狮起源于三国时期，至今近2000年历史～"},
        {"q": "哪种颜色的醒狮象征吉祥喜庆？", "opt": [
            "A. 红色", "B. 黄色", "C. 绿色", "D. 黑色"], "ans": "A", "exp": "红色醒狮象征吉祥喜庆，黄色代表尊贵繁荣～"}
    ],
    "normal": [
        {"q": "醒狮主要盛行于我国哪个地区？", "opt": [
            "A. 华北", "B. 岭南", "C. 西北", "D. 东北"], "ans": "B", "exp": "醒狮盛行于岭南地区，也被称为「南狮」～"},
        {"q": "醒狮最初的用途是什么？", "opt": [
            "A. 娱乐观众", "B. 驱邪避凶", "C. 庆祝丰收", "D. 传递消息"], "ans": "B", "exp": "醒狮最初为驱邪避凶，后演变为庆祝仪式～"},
        {"q": "醒狮又被称为什么？", "opt": [
            "A. 北狮", "B. 南狮", "C. 舞狮", "D. 瑞狮"], "ans": "B", "exp": "醒狮盛行于岭南，也被称为南狮～"}
    ],
    "hard": [
        {"q": "以下哪个场合不适合醒狮表演？", "opt": [
            "A. 春节拜年", "B. 新店开业", "C. 生日派对", "D. 元宵灯会"], "ans": "C", "exp": "醒狮多用于传统节庆，生日派对一般不涉及～"},
        {"q": "醒狮表演融合了以下哪些元素？", "opt": [
            "A. 武术", "B. 唱歌", "C. 书法", "D. 绘画"], "ans": "A", "exp": "醒狮表演融合了武术、舞蹈、音乐等元素～"}
    ]
}

# ===================== 程序入口 =====================
if __name__ == "__main__":
    try:
        turtle.onscreenclick(global_click_handler)
        turtle.tracer(1, 0)
        input_name()
        turtle.done()
    except Exception as e:
        game.stop_game()
        clear_screen()
        err = turtle_manager.get("text_main")
        err.color("#ff0000")
        err.goto(0, 0)
        err.write(f"运行出错：{str(e)}", align="center", font=FONT_MEDIUM)
        turtle.update()
        turtle.done()
