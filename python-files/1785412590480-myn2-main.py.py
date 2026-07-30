import json
from pathlib import Path
import pygame

pygame.init()

W, H = 1280, 720
FPS = 60
ROOT = Path(__file__).resolve().parent
BG = ROOT / "assets" / "backgrounds"
CH = ROOT / "assets" / "characters"
SAVE = ROOT / "saves" / "save.json"

C = {
    "white": (249, 249, 247),
    "muted": (190, 197, 205),
    "red": (226, 63, 48),
    "red2": (255, 91, 69),
    "dark": (14, 17, 22),
    "panel": (20, 24, 31),
    "line": (255, 255, 255, 45),
    "green": (102, 215, 145),
    "orange": (255, 174, 74),
    "blue": (104, 174, 255),
    "cream": (246, 228, 195),
    "paper": (232, 207, 169),
    "brown": (77, 48, 27),
    "gold": (206, 153, 84),
}


FONT_CACHE = {}


def font(size: int, bold: bool = False, role: str = "body") -> pygame.font.Font:
    key = (size, bold, role)
    if key in FONT_CACHE:
        return FONT_CACHE[key]

    families = {
        "display": ["georgia", "cambria", "timesnewroman"],
        "body": ["segoeui", "calibri", "arial"],
        "mono": ["consolas", "couriernew"],
    }

    selected = None
    for family in families.get(role, families["body"]):
        matched = pygame.font.match_font(family, bold=bold)
        if matched:
            selected = pygame.font.Font(matched, size)
            break

    if selected is None:
        selected = pygame.font.SysFont("arial", size, bold=bold)

    selected.set_bold(bold)
    FONT_CACHE[key] = selected
    return selected


def draw_text(
    surface,
    value,
    size,
    color,
    pos,
    center=False,
    bold=False,
    role="body",
    shadow=False,
    letter_spacing=0,
):
    selected_font = font(size, bold, role)

    if letter_spacing <= 0:
        image = selected_font.render(value, True, color)
        rect = image.get_rect()
        if center:
            rect.center = pos
        else:
            rect.topleft = pos

        if shadow:
            shadow_image = selected_font.render(value, True, (0, 0, 0))
            shadow_rect = rect.move(2, 3)
            shadow_image.set_alpha(115)
            surface.blit(shadow_image, shadow_rect)

        surface.blit(image, rect)
        return rect

    glyphs = [selected_font.render(char, True, color) for char in value]
    width = sum(glyph.get_width() for glyph in glyphs)
    width += max(0, len(glyphs) - 1) * letter_spacing
    height = max((glyph.get_height() for glyph in glyphs), default=size)

    image = pygame.Surface((width, height), pygame.SRCALPHA)
    x = 0
    for glyph in glyphs:
        image.blit(glyph, (x, 0))
        x += glyph.get_width() + letter_spacing

    rect = image.get_rect()
    if center:
        rect.center = pos
    else:
        rect.topleft = pos

    if shadow:
        shadow_surface = image.copy()
        shadow_surface.fill((0, 0, 0, 120), special_flags=pygame.BLEND_RGBA_MULT)
        surface.blit(shadow_surface, rect.move(2, 3))

    surface.blit(image, rect)
    return rect
    rect = image.get_rect()
    if center:
        rect.center = pos
    else:
        rect.topleft = pos
    surface.blit(image, rect)
    return rect


def wrap_text(value, max_width, text_font):
    words = value.split()
    lines, current = [], ""
    for word in words:
        test = word if not current else current + " " + word
        if text_font.size(test)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


class Assets:
    def __init__(self):
        self.cache = {}
        self.background_cache = {}
        self.grain = self._make_grain()
        self.dust = self._make_dust()

    def _make_grain(self):
        grain = pygame.Surface((W, H), pygame.SRCALPHA)
        pixels = pygame.PixelArray(grain)
        import random
        for _ in range(10000):
            x = random.randrange(W)
            y = random.randrange(H)
            value = random.choice((35, 45, 55, 65, 75))
            pixels[x, y] = (255, 255, 255, value)
        del pixels
        return grain

    def _make_dust(self):
        import random
        dust = []
        for _ in range(42):
            dust.append({
                "x": random.uniform(0, W),
                "y": random.uniform(0, H),
                "r": random.choice((1, 1, 1, 2)),
                "speed": random.uniform(2.0, 7.0),
                "alpha": random.randint(18, 55),
            })
        return dust

    def load(self, path, alpha=True):
        key = str(path)
        if key not in self.cache:
            image = pygame.image.load(path)
            self.cache[key] = image.convert_alpha() if alpha else image.convert()
        return self.cache[key]

    def background(self, name):
        if name in self.background_cache:
            return self.background_cache[name]

        source = self.load(BG / name, False)
        source_ratio = source.get_width() / source.get_height()
        target_ratio = W / H

        if source_ratio > target_ratio:
            crop_width = int(source.get_height() * target_ratio)
            left = (source.get_width() - crop_width) // 2
            source = source.subsurface(
                pygame.Rect(left, 0, crop_width, source.get_height())
            )
        elif source_ratio < target_ratio:
            crop_height = int(source.get_width() / target_ratio)
            top = (source.get_height() - crop_height) // 2
            source = source.subsurface(
                pygame.Rect(0, top, source.get_width(), crop_height)
            )

        image = pygame.transform.smoothscale(source, (W, H)).copy()

        # Mild optical blur: keeps the room recognizable but separates it
        # from dialogue text and character sprites.
        small = pygame.transform.smoothscale(image, (W // 3, H // 3))
        image = pygame.transform.smoothscale(small, (W, H))

        # Warm photographic grade: cool shadows, warm highlights.
        grade = pygame.Surface((W, H), pygame.SRCALPHA)
        grade.fill((16, 22, 34, 22))
        image.blit(grade, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        amber = pygame.Surface((W, H), pygame.SRCALPHA)
        amber.fill((48, 24, 4, 16))
        image.blit(amber, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        self.background_cache[name] = image
        return image

    def draw_atmosphere(self, surface, time_value):
        import math

        # Uniform warm ambience without visible beams or white stripes.
        warmth = pygame.Surface((W, H), pygame.SRCALPHA)
        warmth.fill((72, 34, 10, 12))
        surface.blit(warmth, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        # Soft upper glow with no hard edge.
        glow = pygame.Surface((W, H), pygame.SRCALPHA)
        pygame.draw.ellipse(
            glow,
            (255, 183, 101, 12),
            (-180, -180, W + 360, 390),
        )
        surface.blit(glow, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        # Floating dust gives the static backgrounds subtle life.
        dust_layer = pygame.Surface((W, H), pygame.SRCALPHA)
        for particle in self.dust:
            y = (
                particle["y"]
                - time_value * particle["speed"]
            ) % (H + 40) - 20
            x = particle["x"] + math.sin(
                time_value * 0.35 + particle["y"]
            ) * 7
            pygame.draw.circle(
                dust_layer,
                (255, 229, 190, particle["alpha"]),
                (int(x), int(y)),
                particle["r"],
            )
        surface.blit(dust_layer, (0, 0))

        # Quiet film grain.
        grain = self.grain.copy()
        grain.set_alpha(11 + int((math.sin(time_value * 9) + 1) * 2))
        surface.blit(grain, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)


    def character(self, name, max_width=500, max_height=535):
        image = self.load(CH / name, True)
        scale = min(max_width / image.get_width(), max_height / image.get_height())
        size = (int(image.get_width() * scale), int(image.get_height() * scale))
        return pygame.transform.smoothscale(image, size)


class Button:
    def __init__(self, rect, label, action, enabled=True):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.action = action
        self.enabled = enabled

    def handle(self, event):
        if (
            self.enabled
            and event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        ):
            self.action()

    def draw(self, surface):
        hovered = self.enabled and self.rect.collidepoint(pygame.mouse.get_pos())

        shadow_rect = self.rect.move(0, 4)
        shadow = pygame.Surface(shadow_rect.size, pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 82))
        surface.blit(shadow, shadow_rect.topleft)

        panel = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        panel.fill(
            (246, 224, 189, 238)
            if hovered
            else (234, 211, 174, 220)
        )
        surface.blit(panel, self.rect.topleft)

        pygame.draw.rect(
            surface,
            (110, 70, 31),
            self.rect,
            2,
            border_radius=4,
        )
        pygame.draw.rect(
            surface,
            (255, 246, 224, 90),
            self.rect.inflate(-8, -8),
            1,
            border_radius=2,
        )

        accent = C["red"] if hovered else (129, 86, 42)
        pygame.draw.line(
            surface,
            accent,
            (self.rect.x + 18, self.rect.y + 8),
            (self.rect.x + 18, self.rect.bottom - 8),
            3,
        )

        color = (37, 24, 15) if self.enabled else (118, 101, 84)

        if self.label in {"<", ">"}:
            cx, cy = self.rect.center
            size = 12
            if self.label == "<":
                points = [
                    (cx + size // 2, cy - size),
                    (cx - size // 2, cy),
                    (cx + size // 2, cy + size),
                ]
            else:
                points = [
                    (cx - size // 2, cy - size),
                    (cx + size // 2, cy),
                    (cx - size // 2, cy + size),
                ]
            pygame.draw.polygon(
                surface,
                C["red"] if hovered else color,
                points,
            )
        else:
            draw_text(
                surface,
                self.label,
                21,
                color,
                self.rect.center,
                center=True,
                bold=hovered,
                role="display",
                shadow=False,
            )

            if hovered:
                draw_text(
                    surface,
                    ">",
                    24,
                    C["red"],
                    (self.rect.right - 28, self.rect.centery),
                    center=True,
                    bold=True,
                    role="body",
                )



def default_state():
    return {
        "node": "intro_1",
        "stress": 0,
        "reputation": 0,
        "time": "09:59",
        "orders": 0,
        "money": 0,
        "coffee_used": 0,
        "achievements": [],
        "relationships": {
            "Антон": 0,
            "Ксюша": 0,
            "Катя": 0,
            "Альбина": 0,
            "Ангелина": 0,
            "Юлия Юрьевна": 0,
            "Иван Владимирович": 0,
        },
        "flags": {},
    }


def save_game(state):
    SAVE.parent.mkdir(exist_ok=True)
    SAVE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_game():
    try:
        state = json.loads(SAVE.read_text(encoding="utf-8"))
        base = default_state()
        base.update(state)
        base["relationships"].update(state.get("relationships", {}))
        base["achievements"] = list(state.get("achievements", []))
        base["flags"] = dict(state.get("flags", {}))
        return base
    except (OSError, json.JSONDecodeError):
        return None


def effect(
    *,
    stress=0,
    reputation=0,
    orders=0,
    money=0,
    achievement=None,
    relation=None,
    relation_delta=0,
    flag=None,
    flag_value=True,
    time=None,
):
    return {
        "stress": stress,
        "reputation": reputation,
        "orders": orders,
        "money": money,
        "achievement": achievement,
        "relation": relation,
        "relation_delta": relation_delta,
        "flag": flag,
        "flag_value": flag_value,
        "time": time,
    }


STORY = {
    "intro_1": {
        "bg": "street.png",
        "speaker": "",
        "text": "Глава 1. Понедельник начинается не с кофе.",
        "next": "intro_2",
        "time": "09:59",
    },
    "intro_2": {
        "bg": "street.png",
        "speaker": "",
        "text": "Перед тобой знакомая вывеска «Фотостудия AGFA». На асфальте лужи, в голове — ни одной рабочей мысли.",
        "next": "intro_3",
    },
    "intro_3": {
        "bg": "street.png",
        "speaker": "Внутренний голос",
        "text": "Главное — зайти уверенно. Будто ты не проверяла время каждые двадцать секунд.",
        "next": "hall_1",
    },
    "hall_1": {
        "bg": "main_hall.png",
        "speaker": "",
        "text": "Колокольчик над дверью звякает. Внутри уже работает половина студии.",
        "next": "anton_1",
        "time": "10:00",
    },
    "anton_1": {
        "bg": "main_hall.png",
        "speaker": "Антон",
        "char": "anton.png",
        "side": "right",
        "text": "Доброе утро. Хотя для некоторых оно, смотрю, началось только сейчас.",
        "choices": [
            {
                "text": "Я пришла вовремя. Часы спешат.",
                "next": "anton_bold",
                "effect": effect(
                    stress=2,
                    reputation=1,
                    relation="Антон",
                    relation_delta=1,
                    flag="anton_bold",
                ),
                "notice": "Антон оценил наглость.",
            },
            {
                "text": "Доброе утро, Антон.",
                "next": "anton_polite",
                "effect": effect(
                    reputation=2,
                    relation="Антон",
                    relation_delta=1,
                ),
                "notice": "Репутация +2",
            },
            {
                "text": "Молча пройти к рабочему месту.",
                "next": "anton_silent",
                "effect": effect(stress=-1),
                "notice": "Стресс −1",
            },
        ],
    },
    "anton_bold": {
        "bg": "main_hall.png",
        "speaker": "Антон",
        "char": "anton.png",
        "side": "right",
        "text": "Конечно. И клиенты не опаздывают — они просто приходят в другой день.",
        "next": "ksusha_1",
    },
    "anton_polite": {
        "bg": "main_hall.png",
        "speaker": "Антон",
        "char": "anton.png",
        "side": "right",
        "text": "Вот. Нормальный человек. Редкость в наше время.",
        "next": "ksusha_1",
    },
    "anton_silent": {
        "bg": "main_hall.png",
        "speaker": "",
        "text": "Ты применяешь древнюю рабочую технику: не спорить с человеком, который трудится здесь дольше оборудования.",
        "next": "ksusha_1",
    },
    "ksusha_1": {
        "bg": "main_hall.png",
        "speaker": "Ксюша",
        "char": "ksusha.png",
        "side": "left",
        "text": "Доброе утрооо! Сегодня точно будет прекрасный день!",
        "choices": [
            {
                "text": "Поддержать её оптимизм.",
                "next": "ksusha_support",
                "effect": effect(
                    stress=-1,
                    relation="Ксюша",
                    relation_delta=2,
                ),
                "notice": "Ксюша +2",
            },
            {
                "text": "Посмотреть на Антона.",
                "next": "ksusha_anton",
                "effect": effect(relation="Антон", relation_delta=1),
                "notice": "Антон всё понял без слов.",
            },
            {
                "text": "Не сглазь.",
                "next": "ksusha_warning",
                "effect": effect(stress=1),
                "notice": "Ксюша всё равно улыбается.",
            },
        ],
    },
    "ksusha_support": {
        "bg": "main_hall.png",
        "speaker": "Ксюша",
        "char": "ksusha.png",
        "side": "left",
        "text": "Вот! Я знала, что хоть кто-то здесь настроен нормально.",
        "next": "printer_sound",
    },
    "ksusha_anton": {
        "bg": "main_hall.png",
        "speaker": "Антон",
        "char": "anton.png",
        "side": "right",
        "text": "Не смотри на меня. Я уже давно ничего хорошего не жду.",
        "next": "printer_sound",
    },
    "ksusha_warning": {
        "bg": "main_hall.png",
        "speaker": "Ксюша",
        "char": "ksusha.png",
        "side": "left",
        "text": "Да ладно тебе. Что вообще может случиться?",
        "next": "printer_sound",
    },
    "printer_sound": {
        "bg": "printer_room.png",
        "speaker": "",
        "text": "Из комнаты с принтером раздаётся скрежет, после которого наступает подозрительная тишина.",
        "next": "printer_anton",
        "time": "10:06",
    },
    "printer_anton": {
        "bg": "printer_room.png",
        "speaker": "Антон",
        "char": "anton.png",
        "side": "right",
        "text": "Вот и первый оптимист закончился.",
        "choices": [
            {
                "text": "Перезапустить принтер самостоятельно.",
                "next": "printer_restart",
                "effect": effect(
                    stress=3,
                    reputation=2,
                    relation="Антон",
                    relation_delta=1,
                    flag="fixed_printer",
                ),
                "notice": "Стресс +3 | Репутация +2",
            },
            {
                "text": "Позвать Антона.",
                "next": "printer_call",
                "effect": effect(
                    reputation=-1,
                    relation="Антон",
                    relation_delta=-1,
                ),
                "notice": "Антон −1",
            },
            {
                "text": "Сказать принтеру: «Не начинай».",
                "next": "printer_talk",
                "effect": effect(stress=-2),
                "notice": "Стресс −2",
            },
        ],
    },
    "printer_restart": {
        "bg": "printer_room.png",
        "speaker": "",
        "text": "Ты выключаешь питание, ждёшь пять секунд и включаешь снова. Принтер задумывается, скрипит и оживает.",
        "next": "katya_intro",
    },
    "printer_call": {
        "bg": "printer_room.png",
        "speaker": "Антон",
        "char": "anton.png",
        "side": "right",
        "text": "Я чувствовал, что спокойно посидеть сегодня не дадут.",
        "next": "katya_intro",
    },
    "printer_talk": {
        "bg": "printer_room.png",
        "speaker": "Ксюша",
        "char": "ksusha.png",
        "side": "left",
        "text": "Мне кажется, он тебя услышал.",
        "next": "katya_intro",
    },
    "katya_intro": {
        "bg": "workplace.png",
        "speaker": "Катя",
        "char": "katya.png",
        "side": "right",
        "text": "На рабочем столе лежит заказ без подписи. Кто его принимал?",
        "choices": [
            {
                "text": "Помочь разобраться с заказом.",
                "next": "katya_help",
                "effect": effect(
                    reputation=1,
                    relation="Катя",
                    relation_delta=2,
                    flag="helped_katya",
                ),
                "notice": "Катя +2",
            },
            {
                "text": "Сказать, что впервые его видишь.",
                "next": "katya_neutral",
                "effect": effect(relation="Катя", relation_delta=0),
                "notice": "Катя ничего не сказала.",
            },
            {
                "text": "Предположить, что это Антон.",
                "next": "katya_blame",
                "effect": effect(
                    stress=-1,
                    relation="Антон",
                    relation_delta=-1,
                ),
                "notice": "Опасная версия.",
            },
        ],
    },
    "katya_help": {
        "bg": "workplace.png",
        "speaker": "Катя",
        "char": "katya.png",
        "side": "right",
        "text": "Ладно. Посмотри по времени создания файла, а я проверю журнал.",
        "next": "albina_intro",
    },
    "katya_neutral": {
        "bg": "workplace.png",
        "speaker": "Катя",
        "char": "katya.png",
        "side": "right",
        "text": "Понятно.",
        "next": "albina_intro",
    },
    "katya_blame": {
        "bg": "workplace.png",
        "speaker": "Антон",
        "char": "anton.png",
        "side": "left",
        "text": "Я всё слышу.",
        "next": "albina_intro",
    },
    "albina_intro": {
        "bg": "cutter_room.png",
        "speaker": "Альбина",
        "char": "albina.png",
        "side": "left",
        "text": "Кто-нибудь видел пачку матовой бумаги? Я её сюда положила.",
        "choices": [
            {
                "text": "Помочь поискать.",
                "next": "albina_help",
                "effect": effect(
                    stress=1,
                    relation="Альбина",
                    relation_delta=2,
                ),
                "notice": "Альбина +2",
            },
            {
                "text": "Указать на пачку прямо перед ней.",
                "next": "albina_found",
                "effect": effect(
                    stress=-1,
                    relation="Альбина",
                    relation_delta=1,
                ),
                "notice": "Неловкая пауза.",
            },
        ],
    },
    "albina_help": {
        "bg": "cutter_room.png",
        "speaker": "",
        "text": "Через минуту выясняется, что пачка всё это время лежала перед Альбиной.",
        "next": "albina_found",
    },
    "albina_found": {
        "bg": "cutter_room.png",
        "speaker": "Альбина",
        "char": "albina.png",
        "side": "left",
        "text": "А. Ну да. Спасибо.",
        "next": "angelina_intro",
    },
    "angelina_intro": {
        "bg": "laser_room.png",
        "speaker": "Ангелина",
        "char": "angelina.png",
        "side": "right",
        "text": "У лазера снова не закрывается крышка. Только не дёргай её резко.",
        "choices": [
            {
                "text": "Аккуратно проверить защёлку.",
                "next": "angelina_careful",
                "effect": effect(
                    reputation=2,
                    relation="Ангелина",
                    relation_delta=2,
                    flag="laser_checked",
                ),
                "notice": "Ангелина +2",
            },
            {
                "text": "Отойти от лазера подальше.",
                "next": "angelina_stepback",
                "effect": effect(stress=-1),
                "notice": "Разумное решение.",
            },
        ],
    },
    "angelina_careful": {
        "bg": "laser_room.png",
        "speaker": "Ангелина",
        "char": "angelina.png",
        "side": "right",
        "text": "Вот. Просто провод мешал. Хорошо, что ты не стала хлопать крышкой.",
        "next": "boss_arrival",
    },
    "angelina_stepback": {
        "bg": "laser_room.png",
        "speaker": "Ангелина",
        "char": "angelina.png",
        "side": "right",
        "text": "Тоже вариант. Сейчас сама посмотрю.",
        "next": "boss_arrival",
    },
    "boss_arrival": {
        "bg": "main_hall.png",
        "speaker": "",
        "text": "Входная дверь открывается. В студию заходят Юлия Юрьевна и Иван Владимирович.",
        "next": "yulia_intro",
        "time": "10:34",
    },
    "yulia_intro": {
        "bg": "main_hall.png",
        "speaker": "Юлия Юрьевна",
        "char": "yulia.png",
        "side": "left",
        "text": "Доброе утро. Всё спокойно?",
        "choices": [
            {
                "text": "Да, абсолютно.",
                "next": "yulia_lie",
                "effect": effect(
                    stress=2,
                    relation="Юлия Юрьевна",
                    relation_delta=0,
                ),
                "notice": "Ты сказала это слишком быстро.",
            },
            {
                "text": "Принтер бастовал, но мы справились.",
                "next": "yulia_honest",
                "effect": effect(
                    reputation=2,
                    relation="Юлия Юрьевна",
                    relation_delta=1,
                ),
                "notice": "Юлия Юрьевна +1",
            },
            {
                "text": "Посмотреть на Антона.",
                "next": "yulia_anton",
                "effect": effect(
                    relation="Антон",
                    relation_delta=-1,
                ),
                "notice": "Антон не оценил.",
            },
        ],
    },
    "yulia_lie": {
        "bg": "main_hall.png",
        "speaker": "Юлия Юрьевна",
        "char": "yulia.png",
        "side": "left",
        "text": "Хорошо. Тогда почему Антон стоит рядом с открытым принтером?",
        "next": "ivan_intro",
    },
    "yulia_honest": {
        "bg": "main_hall.png",
        "speaker": "Юлия Юрьевна",
        "char": "yulia.png",
        "side": "left",
        "text": "Главное, что справились.",
        "next": "ivan_intro",
    },
    "yulia_anton": {
        "bg": "main_hall.png",
        "speaker": "Антон",
        "char": "anton.png",
        "side": "right",
        "text": "Спасибо. Очень командная работа.",
        "next": "ivan_intro",
    },
    "ivan_intro": {
        "bg": "main_hall.png",
        "speaker": "Иван Владимирович",
        "char": "ivan.png",
        "side": "right",
        "text": "Ну, если всё работает — уже хорошо.",
        "next": "first_client",
    },
    "first_client": {
        "bg": "main_hall.png",
        "speaker": "",
        "text": "В этот момент появляется человек. Первый настоящий клиент уже стоит у стойки.",
        "next": "client_request",
        "time": "10:41",
    },
    "client_request": {
        "bg": "workplace.png",
        "speaker": "Клиент",
        "text": "Здравствуйте. Мне нужно эту фотографию напечатать два метра на три. Чтобы качество было идеальное.",
        "next": "client_file",
    },
    "client_file": {
        "bg": "workplace.png",
        "speaker": "",
        "text": "На экране открывается изображение 240×180 пикселей. Половину кадра закрывает палец.",
        "choices": [
            {
                "text": "Спокойно объяснить ограничения качества.",
                "next": "client_explain",
                "effect": effect(
                    stress=3,
                    reputation=3,
                    flag="client_honest",
                ),
                "notice": "Репутация +3",
            },
            {
                "text": "Сказать: «Попробовать можно всё».",
                "next": "client_try",
                "effect": effect(
                    stress=7,
                    reputation=-2,
                    flag="client_promised",
                ),
                "notice": "Ты только что создала себе проблему.",
            },
            {
                "text": "Медленно повернуться к Антону.",
                "next": "client_anton",
                "effect": effect(
                    stress=-2,
                    reputation=-1,
                    relation="Антон",
                    relation_delta=-1,
                ),
                "notice": "Антон −1",
            },
        ],
    },
    "client_explain": {
        "bg": "workplace.png",
        "speaker": "Клиент",
        "text": "То есть вы хотите сказать, что телефон у меня плохой?",
        "next": "client_answer",
    },
    "client_answer": {
        "bg": "workplace.png",
        "speaker": "",
        "text": "Ты глубоко вдыхаешь. Рабочий день официально начался.",
        "next": "chapter_end",
    },
    "client_try": {
        "bg": "workplace.png",
        "speaker": "",
        "text": "Клиент довольно кивает. Где-то в глубине студии Антон тяжело вздыхает, хотя разговора не слышал.",
        "next": "chapter_end",
    },
    "client_anton": {
        "bg": "workplace.png",
        "speaker": "Антон",
        "char": "anton.png",
        "side": "right",
        "text": "Нет. Даже не смотри на меня. Ты уже начала — ты и заканчивай.",
        "next": "chapter_end",
    },
    "chapter_end": {
        "bg": "main_hall.png",
        "speaker": "",
        "text": "10:47. До конца смены осталось примерно вечность.",
        "next": "chapter_summary",
        "time": "10:47",
    },
    "chapter_summary": {
        "bg": "main_hall.png",
        "speaker": "",
        "text": "Первый час смены пережит.",
        "next": "part2_start",
    },
    "part2_start": {
        "bg": "main_hall.png",
        "speaker": "",
        "text": "Но студия не успевает выдохнуть. Кто-то заходит снова.",
        "next": "passport_client",
        "time": "11:03",
    },
    "passport_client": {
        "bg": "workplace.png",
        "speaker": "Клиентка",
        "text": "Мне нужно фото на паспорт. Только сделайте красиво, как в жизни.",
        "choices": [
            {
                "text": "Объяснить, что паспортное фото должно соответствовать требованиям.",
                "next": "passport_rules",
                "effect": effect(
                    stress=2,
                    reputation=2,
                    orders=1,
                    money=450,
                    achievement="По ГОСТу",
                    flag="passport_honest",
                ),
                "notice": "Заказ +1 | 450 руб.",
            },
            {
                "text": "Пообещать убрать всё, что ей не нравится.",
                "next": "passport_magic",
                "effect": effect(
                    stress=6,
                    reputation=-1,
                    orders=1,
                    money=450,
                    flag="passport_promised",
                ),
                "notice": "Ты снова пообещала невозможное.",
            },
            {
                "text": "Позвать Катю — она выглядит серьёзнее.",
                "next": "passport_katya",
                "effect": effect(
                    relation="Катя",
                    relation_delta=-1,
                    stress=-1,
                ),
                "notice": "Катя −1",
            },
        ],
    },
    "passport_rules": {
        "bg": "workplace.png",
        "speaker": "Клиентка",
        "text": "То есть подбородок уменьшить вообще нельзя?",
        "next": "passport_finish",
    },
    "passport_magic": {
        "bg": "workplace.png",
        "speaker": "",
        "text": "Через десять минут список правок уже включает подбородок, нос, шею, волосы и «взгляд побогаче».",
        "next": "passport_finish",
    },
    "passport_katya": {
        "bg": "workplace.png",
        "speaker": "Катя",
        "char": "katya.png",
        "side": "right",
        "text": "Очень командно. Спасибо.",
        "next": "passport_finish",
    },
    "passport_finish": {
        "bg": "workplace.png",
        "speaker": "",
        "text": "Заказ отправлен в печать. Ты впервые за утро чувствуешь, что действительно работаешь.",
        "next": "flash_drive",
        "time": "11:26",
    },
    "flash_drive": {
        "bg": "workplace.png",
        "speaker": "Мужчина с флешкой",
        "text": "Тут фотографии. Они где-то внутри. Я не знаю где.",
        "choices": [
            {
                "text": "Открыть все 47 папок по очереди.",
                "next": "flash_search",
                "effect": effect(
                    stress=4,
                    reputation=2,
                    orders=1,
                    money=300,
                    achievement="Новый том (7)",
                ),
                "notice": "Заказ +1 | Терпение −4",
            },
            {
                "text": "Попросить клиента показать нужные файлы.",
                "next": "flash_client",
                "effect": effect(stress=1, reputation=1),
                "notice": "Разумный подход.",
            },
            {
                "text": "Позвать Ксюшу — она ещё улыбается.",
                "next": "flash_ksusha",
                "effect": effect(
                    relation="Ксюша",
                    relation_delta=-1,
                    stress=-2,
                ),
                "notice": "Ксюша всё ещё улыбается. Пока.",
            },
        ],
    },
    "flash_search": {
        "bg": "workplace.png",
        "speaker": "",
        "text": "Фотографии находятся в папке «Новая папка (3)» внутри «Документы» внутри «Новый том (7)».",
        "next": "calendar_order",
    },
    "flash_client": {
        "bg": "workplace.png",
        "speaker": "Мужчина с флешкой",
        "text": "А я не умею. Вы же специалист.",
        "next": "calendar_order",
    },
    "flash_ksusha": {
        "bg": "workplace.png",
        "speaker": "Ксюша",
        "char": "ksusha.png",
        "side": "left",
        "text": "Конечно, сейчас найдём! Наверное.",
        "next": "calendar_order",
    },
    "calendar_order": {
        "bg": "main_hall.png",
        "speaker": "Юлия Юрьевна",
        "char": "yulia.png",
        "side": "left",
        "text": "Нужно проверить макет календаря. Клиент заберёт его сегодня.",
        "choices": [
            {
                "text": "Сразу открыть и внимательно проверить даты.",
                "next": "calendar_check",
                "effect": effect(
                    stress=3,
                    reputation=3,
                    relation="Юлия Юрьевна",
                    relation_delta=2,
                    achievement="Февраль существует",
                    flag="calendar_checked",
                ),
                "notice": "Юлия Юрьевна +2",
            },
            {
                "text": "Сказать, что выглядит нормально.",
                "next": "calendar_skip",
                "effect": effect(
                    stress=-1,
                    reputation=-3,
                    relation="Юлия Юрьевна",
                    relation_delta=-2,
                    flag="calendar_missed",
                ),
                "notice": "Плохая идея сохранена.",
            },
        ],
    },
    "calendar_check": {
        "bg": "workplace.png",
        "speaker": "",
        "text": "В феврале обнаруживается тридцатое число. Ты исправляешь макет до печати.",
        "next": "anton_comment",
    },
    "calendar_skip": {
        "bg": "workplace.png",
        "speaker": "Катя",
        "char": "katya.png",
        "side": "right",
        "text": "Там в феврале тридцать дней.",
        "next": "anton_comment",
    },
    "anton_comment": {
        "bg": "main_hall.png",
        "speaker": "Антон",
        "char": "anton.png",
        "side": "right",
        "text": "Календарь с дополнительным днём — это уже премиальная версия.",
        "next": "coffee_break",
        "time": "12:18",
    },
    "coffee_break": {
        "bg": "main_hall.png",
        "speaker": "Ксюша",
        "char": "ksusha.png",
        "side": "left",
        "text": "Кто будет кофе? Я всем сделаю!",
        "choices": [
            {
                "text": "Согласиться на кофе.",
                "next": "coffee_yes",
                "effect": effect(
                    stress=-4,
                    relation="Ксюша",
                    relation_delta=1,
                    achievement="Кофе вместо терапии",
                ),
                "notice": "Стресс −4",
            },
            {
                "text": "Отказаться и продолжить работать.",
                "next": "coffee_no",
                "effect": effect(
                    reputation=1,
                    stress=2,
                    relation="Антон",
                    relation_delta=1,
                ),
                "notice": "Репутация +1 | Стресс +2",
            },
        ],
    },
    "coffee_yes": {
        "bg": "main_hall.png",
        "speaker": "",
        "text": "Кофе получается слишком сладким, но в данный момент это уже не имеет значения.",
        "next": "laser_order",
    },
    "coffee_no": {
        "bg": "main_hall.png",
        "speaker": "Антон",
        "char": "anton.png",
        "side": "right",
        "text": "Вот это зря. До обеда ещё далеко.",
        "next": "laser_order",
    },
    "laser_order": {
        "bg": "laser_room.png",
        "speaker": "Ангелина",
        "char": "angelina.png",
        "side": "right",
        "text": "Нужно выгравировать надпись на брелоке. Клиент написал её от руки.",
        "choices": [
            {
                "text": "Перезвонить и уточнить написание.",
                "next": "laser_call",
                "effect": effect(
                    stress=2,
                    reputation=3,
                    relation="Ангелина",
                    relation_delta=2,
                    orders=1,
                    money=650,
                    achievement="Сначала уточнить",
                ),
                "notice": "Заказ +1 | Ангелина +2",
            },
            {
                "text": "Расшифровать почерк самостоятельно.",
                "next": "laser_guess",
                "effect": effect(
                    stress=5,
                    reputation=-2,
                    orders=1,
                    money=650,
                    flag="wrong_engraving",
                ),
                "notice": "Риск принят.",
            },
        ],
    },
    "laser_call": {
        "bg": "laser_room.png",
        "speaker": "",
        "text": "Оказывается, там написано «Любимому дедушке», а не «Любимому Денису».",
        "next": "lunch_start",
    },
    "laser_guess": {
        "bg": "laser_room.png",
        "speaker": "Ангелина",
        "char": "angelina.png",
        "side": "right",
        "text": "Ты точно уверена, что его зовут Денис?",
        "next": "lunch_start",
    },
    "lunch_start": {
        "bg": "main_hall.png",
        "speaker": "",
        "text": "Наконец наступает обед. По крайней мере, так написано в расписании.",
        "next": "lunch_choice",
        "time": "13:07",
    },
    "lunch_choice": {
        "bg": "main_hall.png",
        "speaker": "",
        "text": "Куда потратить двадцать минут относительной свободы?",
        "choices": [
            {
                "text": "Поесть.",
                "next": "lunch_team",
                "effect": effect(
                    stress=-5,
                    relation="Антон",
                    relation_delta=1,
                    achievement="Коллективный обед",
                ),
                "notice": "Стресс −5",
            },
            {
                "text": "Остаться за компьютером и закончить заказы.",
                "next": "lunch_work",
                "effect": effect(
                    stress=4,
                    reputation=3,
                    achievement="Обед отменяется",
                ),
                "notice": "Репутация +3 | Стресс +4",
            },
        ],
    },
    "lunch_team": {
        "bg": "main_hall.png",
        "speaker": "Альбина",
        "char": "albina.png",
        "side": "left",
        "text": "Удивительно. Уже час дня, а никто ничего не сломал окончательно.",
        "next": "final_client",
    },
    "lunch_work": {
        "bg": "workplace.png",
        "speaker": "Катя",
        "char": "katya.png",
        "side": "right",
        "text": "Ты серьёзно решила работать во время обеда?",
        "next": "final_client",
    },
    "final_client": {
        "bg": "main_hall.png",
        "speaker": "",
        "text": "Ровно в тот момент, когда начинаешь жалеть, что не пошла на обед, дверь снова открывается.",
        "next": "urgent_client",
        "time": "13:19",
    },
    "urgent_client": {
        "bg": "workplace.png",
        "speaker": "Клиент",
        "text": "Мне очень срочно. Нужно было ещё вчера.",
        "choices": [
            {
                "text": "Принять заказ и назвать реальный срок.",
                "next": "urgent_real",
                "effect": effect(
                    stress=3,
                    reputation=3,
                    orders=1,
                    money=900,
                    achievement="Нужно было вчера",
                ),
                "notice": "Заказ +1 | 900 руб.",
            },
            {
                "text": "Пообещать сделать прямо сейчас.",
                "next": "urgent_now",
                "effect": effect(
                    stress=9,
                    reputation=-2,
                    orders=1,
                    money=900,
                ),
                "notice": "Стресс +9",
            },
            {
                "text": "Сказать, что обед — святое.",
                "next": "urgent_lunch",
                "effect": effect(
                    stress=-2,
                    reputation=-1,
                    relation="Антон",
                    relation_delta=2,
                    achievement="Личные границы",
                ),
                "notice": "Антон одобряет.",
            },
        ],
    },
    "urgent_real": {
        "bg": "workplace.png",
        "speaker": "Клиент",
        "text": "А побыстрее никак?",
        "next": "day_summary",
    },
    "urgent_now": {
        "bg": "workplace.png",
        "speaker": "",
        "text": "Обед остывает. Принтер греется. Ты начинаешь понимать Антона.",
        "next": "day_summary",
    },
    "urgent_lunch": {
        "bg": "main_hall.png",
        "speaker": "Антон",
        "char": "anton.png",
        "side": "right",
        "text": "Наконец-то кто-то это сказал.",
        "next": "day_summary",
    },
    "day_summary": {
        "bg": "main_hall.png",
        "speaker": "",
        "text": "Утренняя часть смены завершена.",
        "next": "afternoon_start",
        "time": "13:34",
    },
    "afternoon_start": {
        "bg": "main_hall.png",
        "speaker": "",
        "text": "После обеда студия на несколько минут затихает. Это выглядит подозрительно.",
        "next": "ivan_task",
        "time": "14:02",
    },
    "ivan_task": {
        "bg": "main_hall.png",
        "speaker": "Иван Владимирович",
        "char": "ivan.png",
        "side": "right",
        "text": "Нужно разобрать старые заказы на полке. Там уже никто не понимает, что чьё.",
        "choices": [
            {
                "text": "Сразу начать сортировать по датам и фамилиям.",
                "next": "archive_orderly",
                "effect": effect(
                    stress=3,
                    reputation=3,
                    relation="Иван Владимирович",
                    relation_delta=2,
                    achievement="Археолог фотопечати",
                ),
                "notice": "Иван Владимирович +2",
            },
            {
                "text": "Предложить сначала выбросить всё старше года.",
                "next": "archive_risky",
                "effect": effect(
                    stress=-1,
                    reputation=-2,
                    relation="Иван Владимирович",
                    relation_delta=-1,
                ),
                "notice": "Слишком смелое предложение.",
            },
        ],
    },
    "archive_orderly": {
        "bg": "main_hall.png",
        "speaker": "",
        "text": "Через двадцать минут находятся три забытых заказа, две чужие флешки и конверт с надписью «не потерять».",
        "next": "katya_secret",
    },
    "archive_risky": {
        "bg": "main_hall.png",
        "speaker": "Иван Владимирович",
        "char": "ivan.png",
        "side": "right",
        "text": "Нет. Сначала разберёмся, потом выбросим. Иначе завтра кто-нибудь обязательно придёт.",
        "next": "katya_secret",
    },
    "katya_secret": {
        "bg": "workplace.png",
        "speaker": "Катя",
        "char": "katya.png",
        "side": "right",
        "text": "Только никому не говори, но один из этих заказов лежит здесь ещё с зимы.",
        "choices": [
            {
                "text": "Пообещать молчать и помочь найти владельца.",
                "next": "katya_trust",
                "effect": effect(
                    relation="Катя",
                    relation_delta=3,
                    reputation=1,
                    achievement="Катя доверяет",
                ),
                "notice": "Катя +3",
            },
            {
                "text": "Спросить, почему она сама его не отдала.",
                "next": "katya_question",
                "effect": effect(
                    relation="Катя",
                    relation_delta=-1,
                ),
                "notice": "Катя закрылась.",
            },
        ],
    },
    "katya_trust": {
        "bg": "workplace.png",
        "speaker": "Катя",
        "char": "katya.png",
        "side": "right",
        "text": "Спасибо. Я нашла номер, но всё откладывала звонок.",
        "next": "photo_restore",
    },
    "katya_question": {
        "bg": "workplace.png",
        "speaker": "Катя",
        "char": "katya.png",
        "side": "right",
        "text": "Потому что не отдала.",
        "next": "photo_restore",
    },
    "photo_restore": {
        "bg": "workplace.png",
        "speaker": "Пожилая клиентка",
        "text": "Можно восстановить эту фотографию? Это единственный снимок моего отца.",
        "choices": [
            {
                "text": "Внимательно осмотреть снимок и честно обозначить возможности.",
                "next": "restore_honest",
                "effect": effect(
                    stress=3,
                    reputation=4,
                    orders=1,
                    money=1200,
                    achievement="Беречь память",
                ),
                "notice": "Заказ +1 | 1200 руб.",
            },
            {
                "text": "Сразу пообещать идеальный результат.",
                "next": "restore_promise",
                "effect": effect(
                    stress=8,
                    reputation=-2,
                    orders=1,
                    money=1200,
                ),
                "notice": "Обещание принято. Ответственность тоже.",
            },
        ],
    },
    "restore_honest": {
        "bg": "workplace.png",
        "speaker": "Пожилая клиентка",
        "text": "Главное, чтобы лицо осталось узнаваемым. Остальное не так важно.",
        "next": "afternoon_end",
    },
    "restore_promise": {
        "bg": "workplace.png",
        "speaker": "",
        "text": "Клиентка улыбается. Ты смотришь на глубокую трещину через всё лицо и перестаёшь улыбаться.",
        "next": "afternoon_end",
    },
    "afternoon_end": {
        "bg": "main_hall.png",
        "speaker": "",
        "text": "14:48. Впереди ещё половина смены.",
        "next": "delivery_problem",
        "time": "14:48",
    },
    "delivery_problem": {
        "bg": "main_hall.png",
        "speaker": "Альбина",
        "char": "albina.png",
        "side": "left",
        "text": "Курьер привёз коробку бумаги, но в накладной другой формат. Что делаем?",
        "choices": [
            {
                "text": "Сверить заказ и сразу позвонить поставщику.",
                "next": "delivery_call",
                "effect": effect(
                    stress=2,
                    reputation=3,
                    relation="Альбина",
                    relation_delta=2,
                    achievement="Накладная не врёт",
                ),
                "notice": "Репутация +3 | Альбина +2",
            },
            {
                "text": "Принять коробку — потом разберёмся.",
                "next": "delivery_accept",
                "effect": effect(
                    stress=-1,
                    reputation=-3,
                    flag="wrong_paper_accepted",
                ),
                "notice": "Проблема отложена, но не решена.",
            },
        ],
    },
    "delivery_call": {
        "bg": "main_hall.png",
        "speaker": "",
        "text": "Поставщик признаёт ошибку и обещает заменить бумагу сегодня же.",
        "next": "phone_print_order",
    },
    "delivery_accept": {
        "bg": "main_hall.png",
        "speaker": "Антон",
        "char": "anton.png",
        "side": "right",
        "text": "Отлично. Теперь у нас есть бумага, которая никому не нужна.",
        "next": "phone_print_order",
    },
    "phone_print_order": {
        "bg": "workplace.png",
        "speaker": "Клиентка",
        "text": "Мне нужно распечатать сто двадцать фотографий с телефона. Только там вперемешку снимки, скриншоты и дубли. Можно выбрать нормальные?",
        "choices": [
            {
                "text": "Помочь отобрать фотографии, убрать дубли и уточнить формат печати.",
                "next": "phone_print_sorted",
                "effect": effect(
                    stress=4,
                    reputation=4,
                    orders=1,
                    money=1800,
                    achievement="Без дублей",
                ),
                "notice": "Заказ +1 | 1800 руб.",
            },
            {
                "text": "Отправить в печать всё подряд, как есть.",
                "next": "phone_print_all",
                "effect": effect(
                    stress=6,
                    reputation=-2,
                    orders=1,
                    money=1800,
                ),
                "notice": "В очередь попали скриншоты и три одинаковых кота.",
            },
            {
                "text": "Попросить Ксюшу помочь клиентке с выбором файлов.",
                "next": "phone_print_ksusha",
                "effect": effect(
                    stress=-2,
                    relation="Ксюша",
                    relation_delta=2,
                    orders=1,
                    money=1800,
                ),
                "notice": "Ксюша +2",
            },
        ],
    },
    "phone_print_sorted": {
        "bg": "workplace.png",
        "speaker": "",
        "text": "После отбора остаётся восемьдесят семь фотографий. Размеры согласованы, дубли удалены, заказ уходит в печать.",
        "next": "machine_heat",
    },
    "phone_print_all": {
        "bg": "workplace.png",
        "speaker": "Катя",
        "char": "katya.png",
        "side": "right",
        "text": "Тут двадцать скриншотов переписки и фотография чека. Точно всё это печатаем?",
        "next": "machine_heat",
    },
    "phone_print_ksusha": {
        "bg": "workplace.png",
        "speaker": "Ксюша",
        "char": "ksusha.png",
        "side": "left",
        "text": "Так, одинаковые убираем, скриншоты не печатаем, а кота оставляем. Кот хороший.",
        "next": "machine_heat",
    },
    "machine_heat": {
        "bg": "printer_room.png",
        "speaker": "Ангелина",
        "char": "angelina.png",
        "side": "right",
        "text": "Большой принтер перегрелся. Если продолжить печать, он может остановиться совсем.",
        "choices": [
            {
                "text": "Поставить печать на паузу и предупредить клиентов о задержке.",
                "next": "machine_pause",
                "effect": effect(
                    stress=3,
                    reputation=2,
                    relation="Ангелина",
                    relation_delta=2,
                    achievement="Техника тоже устала",
                ),
                "notice": "Ангелина +2",
            },
            {
                "text": "Продолжить — заказов слишком много.",
                "next": "machine_push",
                "effect": effect(
                    stress=8,
                    reputation=-3,
                    flag="printer_overloaded",
                ),
                "notice": "Принтер это запомнил.",
            },
        ],
    },
    "machine_pause": {
        "bg": "printer_room.png",
        "speaker": "",
        "text": "После короткой паузы температура снижается, и печать удаётся продолжить без поломки.",
        "next": "boss_check",
    },
    "machine_push": {
        "bg": "printer_room.png",
        "speaker": "",
        "text": "Принтер печатает ещё два листа и останавливается с очень дорогим звуком.",
        "next": "boss_check",
    },
    "boss_check": {
        "bg": "main_hall.png",
        "speaker": "Юлия Юрьевна",
        "char": "yulia.png",
        "side": "left",
        "text": "Как прошла смена? Что-нибудь важное случилось?",
        "choices": [
            {
                "text": "Коротко и честно рассказать о проблемах.",
                "next": "boss_honest",
                "effect": effect(
                    reputation=3,
                    relation="Юлия Юрьевна",
                    relation_delta=2,
                    achievement="Без прикрас",
                ),
                "notice": "Юлия Юрьевна +2",
            },
            {
                "text": "Сказать, что всё прошло идеально.",
                "next": "boss_perfect",
                "effect": effect(
                    stress=3,
                    reputation=-2,
                    relation="Юлия Юрьевна",
                    relation_delta=-1,
                ),
                "notice": "Слишком подозрительно.",
            },
            {
                "text": "Пусть Антон рассказывает.",
                "next": "boss_anton",
                "effect": effect(
                    stress=-1,
                    relation="Антон",
                    relation_delta=-2,
                ),
                "notice": "Антон −2",
            },
        ],
    },
    "boss_honest": {
        "bg": "main_hall.png",
        "speaker": "Юлия Юрьевна",
        "char": "yulia.png",
        "side": "left",
        "text": "Хорошо, что говоришь сразу. Тогда завтра разберёмся с поставкой и принтером.",
        "next": "closing_time",
    },
    "boss_perfect": {
        "bg": "main_hall.png",
        "speaker": "Юлия Юрьевна",
        "char": "yulia.png",
        "side": "left",
        "text": "Именно поэтому из принтерной пахнет перегретым пластиком?",
        "next": "closing_time",
    },
    "boss_anton": {
        "bg": "main_hall.png",
        "speaker": "Антон",
        "char": "anton.png",
        "side": "right",
        "text": "Конечно. Я как раз мечтал подготовить полный отчёт.",
        "next": "closing_time",
    },
    "closing_time": {
        "bg": "main_hall.png",
        "speaker": "",
        "text": "До закрытия остаётся десять минут. В студии неожиданно тихо.",
        "next": "last_client",
        "time": "18:50",
    },
    "last_client": {
        "bg": "main_hall.png",
        "speaker": "",
        "text": "В 18:57 дверь открывается. На пороге появляется человек с пакетом фотографий.",
        "next": "last_client_request",
    },
    "last_client_request": {
        "bg": "workplace.png",
        "speaker": "Последний клиент",
        "text": "Здравствуйте. Я быстро. Тут всего двести фотографий, их нужно отсортировать и напечатать сегодня.",
        "choices": [
            {
                "text": "Спокойно объяснить, что заказ будет готов завтра.",
                "next": "last_tomorrow",
                "effect": effect(
                    reputation=3,
                    stress=2,
                    orders=1,
                    money=2400,
                    achievement="Мы уже закрываемся",
                ),
                "notice": "Заказ +1 | 2400 руб.",
            },
            {
                "text": "Согласиться остаться после закрытия.",
                "next": "last_overtime",
                "effect": effect(
                    reputation=2,
                    stress=12,
                    orders=1,
                    money=2400,
                    achievement="Сверхурочные",
                ),
                "notice": "Стресс +12",
            },
            {
                "text": "Посмотреть на часы и на Антона.",
                "next": "last_anton",
                "effect": effect(
                    stress=-2,
                    relation="Антон",
                    relation_delta=2,
                ),
                "notice": "Антон +2",
            },
        ],
    },
    "last_tomorrow": {
        "bg": "workplace.png",
        "speaker": "Последний клиент",
        "text": "Ладно. Но утром первым делом.",
        "next": "shift_result",
    },
    "last_overtime": {
        "bg": "workplace.png",
        "speaker": "",
        "text": "Коллеги молча смотрят на тебя. В их взглядах нет осуждения. Только усталость.",
        "next": "shift_result",
    },
    "last_anton": {
        "bg": "main_hall.png",
        "speaker": "Антон",
        "char": "anton.png",
        "side": "right",
        "text": "Заказ принимаем. Печатаем завтра. Сегодня мы уже не люди.",
        "next": "shift_result",
    },
    "shift_result": {
        "bg": "main_hall.png",
        "speaker": "",
        "text": "Смена окончена. Итоги появятся после следующего нажатия.",
        "next": "ending_router",
        "time": "19:04",
    },
    "ending_router": {
        "bg": "main_hall.png",
        "speaker": "",
        "text": "Ты выключаешь монитор и впервые за день слышишь тишину.",
        "next": None,
    },
}


ACHIEVEMENTS = [
    ("По ГОСТу", "Честно объяснить требования к фотографии на паспорт."),
    ("Новый том (7)", "Найти фотографии в глубинах клиентской флешки."),
    ("Февраль существует", "Заметить лишний день в календаре."),
    ("Кофе вместо терапии", "Согласиться на спасительный кофе."),
    ("Сначала уточнить", "Проверить надпись перед гравировкой."),
    ("Коллективный обед", "Поесть не вечером."),
    ("Обед отменяется", "Добровольно работать во время обеда."),
    ("Нужно было вчера", "Принять первый по-настоящему срочный заказ."),
    ("Личные границы", "Защитить законное право на обед."),
    ("Археолог фотопечати", "Разобрать залежи старых заказов."),
    ("Катя доверяет", "Получить редкий откровенный разговор с Катей."),
    ("Беречь память", "Принять важный заказ на восстановление фотографии."),
    ("Накладная не врёт", "Проверить поставку до приёмки."),
    ("Без дублей", "Подготовить большой заказ фотопечати без лишних файлов."),
    ("Техника тоже устала", "Вовремя остановить перегретый принтер."),
    ("Без прикрас", "Честно рассказать начальству о проблемах."),
    ("Мы уже закрываемся", "Установить реальный срок последнему клиенту."),
    ("Сверхурочные", "Добровольно остаться после закрытия."),
]


STAFF = [
    ("Антон", "anton.png", "Работает здесь дольше всех. Надёжен, опытен и периодически ворчит."),
    ("Ксюша", "ksusha.png", "Улыбчивая и очень оптимистичная. Иногда даже слишком."),
    ("Катя", "katya.png", "Серьёзная, спокойная и довольно скрытная."),
    ("Альбина", "albina.png", "Спокойная девушка, которая предпочитает не участвовать в драме."),
    ("Ангелина", "angelina.png", "Наблюдательная и аккуратная. Часто замечает проблему раньше остальных."),
    ("Юлия Юрьевна", "yulia.png", "Начальство. Сохраняет спокойствие даже посреди рабочего хаоса."),
    ("Иван Владимирович", "ivan.png", "Начальство. Не сохраняет спокойствие посреди рабочего хаоса."),
]


class Game:
    def __init__(self):
        pygame.display.set_caption("Фотостудия AGFA — Pixel Edition")
        self.screen = pygame.display.set_mode((W, H))
        self.clock = pygame.time.Clock()
        self.assets = Assets()
        self.running = True
        self.fullscreen = False
        self.scene = "menu"
        self.state = default_state()
        self.node = STORY["intro_1"]
        self.visible_chars = 0.0
        self.notice = ""
        self.notice_time = 0.0
        self.char_x = 0.0
        self.char_target = 0.0
        self.buttons = []
        self.staff_index = 0
        self.visual_time = 0.0
        self.transition_alpha = 255.0
        self.scene_title_time = 0.0
        self.open_menu()

    def open_menu(self):
        self.scene = "menu"
        self.buttons = [
            Button((390, 222, 500, 43), "Новая смена", self.new_game),
            Button(
                (390, 272, 500, 43),
                "Продолжить",
                self.continue_game,
                SAVE.exists(),
            ),
            Button((390, 322, 500, 43), "Коллектив", self.open_staff),
            Button((390, 372, 500, 43), "Достижения", self.open_achievements),
            Button((390, 422, 500, 43), "Полный экран", self.toggle_fullscreen),
            Button((390, 472, 500, 43), "Выход", self.quit),
        ]

    def new_game(self):
        self.state = default_state()
        self.open_node("intro_1")

    def continue_game(self):
        loaded = load_game()
        if loaded:
            self.state = loaded
            self.open_node(self.state.get("node", "intro_1"))

    def open_staff(self):
        self.scene = "staff"
        self.staff_index = 0
        self.buttons = [
            Button((70, 620, 250, 52), "Назад", self.open_menu),
            Button((890, 620, 140, 52), "<", self.staff_prev),
            Button((1050, 620, 140, 52), ">", self.staff_next),
        ]

    def open_achievements(self):
        self.scene = "achievements"
        self.buttons = [
            Button((70, 648, 230, 42), "Назад", self.open_menu),
        ]

    def unlock_achievement(self, name):
        if not name:
            return
        if name not in self.state["achievements"]:
            self.state["achievements"].append(name)
            self.notice = f"Достижение: {name}"
            self.notice_time = 3.2

    def staff_prev(self):
        self.staff_index = (self.staff_index - 1) % len(STAFF)

    def staff_next(self):
        self.staff_index = (self.staff_index + 1) % len(STAFF)

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        flags = pygame.FULLSCREEN if self.fullscreen else 0
        self.screen = pygame.display.set_mode((W, H), flags)

    def quit(self):
        self.running = False

    def apply_effect(self, data):
        if not data:
            return

        self.state["stress"] = max(
            0,
            self.state["stress"] + data.get("stress", 0),
        )
        self.state["reputation"] += data.get("reputation", 0)
        self.state["orders"] += data.get("orders", 0)
        self.state["money"] += data.get("money", 0)
        self.unlock_achievement(data.get("achievement"))

        relation = data.get("relation")
        if relation:
            self.state["relationships"][relation] = (
                self.state["relationships"].get(relation, 0)
                + data.get("relation_delta", 0)
            )

        if data.get("flag"):
            self.state["flags"][data["flag"]] = data.get("flag_value", True)

        if data.get("time"):
            self.state["time"] = data["time"]

    def open_node(self, key):
        self.state["node"] = key
        self.node = STORY[key]

        if self.node.get("time"):
            self.state["time"] = self.node["time"]

        self.visible_chars = 0.0
        self.scene = "game"
        self.transition_alpha = 255.0
        self.scene_title_time = 2.2

        side = self.node.get("side", "right")
        self.char_target = 755 if side == "right" else 25
        self.char_x = self.char_target + (130 if side == "right" else -130)

        self.build_choice_buttons()
        save_game(self.state)

    def build_choice_buttons(self):
        self.buttons = []
        choices = self.node.get("choices", [])
        if not choices:
            return

        start_y = 330
        for index, choice in enumerate(choices):
            self.buttons.append(
                Button(
                    (190, start_y + index * 72, 900, 58),
                    choice["text"],
                    lambda i=index: self.choose(i),
                )
            )

    def choose(self, index):
        choice = self.node["choices"][index]
        self.apply_effect(choice.get("effect"))

        if self.notice_time <= 0 or not self.notice.startswith("Достижение:"):
            self.notice = choice.get("notice", "")
            self.notice_time = 2.5

        self.open_node(choice["next"])

    def calculate_ending(self):
        stress = self.state["stress"]
        reputation = self.state["reputation"]
        orders = self.state["orders"]
        relationships = self.state["relationships"]

        if stress >= 35:
            return (
                "СМЕНА ПЕРЕЖИТА",
                "Ты справилась со всеми заказами, но домой уходишь на чистом упрямстве. Завтра нужен кофе. Очень много кофе.",
            )

        if reputation >= 18 and orders >= 6:
            return (
                "ЛУЧШИЙ РЕЗУЛЬТАТ",
                "Смена была хаотичной, но клиенты довольны, касса полна, а начальство явно запомнило твою работу.",
            )

        positive_relations = sum(
            1 for value in relationships.values() if value >= 2
        )
        if positive_relations >= 4:
            return (
                "КОМАНДНЫЙ ИГРОК",
                "Не все решения были идеальными, зато коллектив теперь воспринимает тебя как своего человека.",
            )

        if reputation < 0:
            return (
                "СЛОЖНЫЙ ПОНЕДЕЛЬНИК",
                "До увольнения далеко, но завтра лучше не обещать клиентам невозможное и проверять макеты внимательнее.",
            )

        return (
            "ОБЫЧНАЯ СМЕНА",
            "Ты закрываешь студию без катастрофы. Для понедельника это уже вполне достойный результат.",
        )

    def open_results(self):
        self.scene = "results"
        self.buttons = [
            Button((440, 585, 400, 56), "Вернуться в меню", self.open_menu),
        ]

    def advance(self):
        if self.node.get("choices"):
            return

        if self.visible_chars < len(self.node["text"]):
            self.visible_chars = len(self.node["text"])
            return

        next_node = self.node.get("next")
        if next_node is None:
            if self.state.get("node") == "ending_router":
                self.open_results()
            else:
                self.open_menu()
        else:
            self.open_node(next_node)

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.quit()
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
            self.toggle_fullscreen()
            return

        if self.scene in {"menu", "staff", "achievements", "results"}:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.open_menu()
                return

            for button in self.buttons:
                button.handle(event)
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.open_menu()
                return

            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.advance()
                return

            keys = {
                pygame.K_1: 0,
                pygame.K_2: 1,
                pygame.K_3: 2,
            }
            if (
                self.node.get("choices")
                and event.key in keys
                and keys[event.key] < len(self.buttons)
            ):
                self.choose(keys[event.key])
                return

        if self.node.get("choices"):
            for button in self.buttons:
                button.handle(event)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.advance()

    def update(self, dt):
        self.visual_time += dt
        self.transition_alpha = max(0.0, self.transition_alpha - 420 * dt)
        self.scene_title_time = max(0.0, self.scene_title_time - dt)

        if self.scene != "game":
            return

        self.visible_chars = min(
            len(self.node["text"]),
            self.visible_chars + 52 * dt,
        )
        self.notice_time = max(0.0, self.notice_time - dt)
        self.char_x += (
            self.char_target - self.char_x
        ) * min(1.0, dt * 9)

    def draw_corner_marks(self, rect, color=None, length=18, width=2):
        color = color or C["gold"]
        x, y, w, h = rect.x, rect.y, rect.w, rect.h

        pygame.draw.line(self.screen, color, (x, y), (x + length, y), width)
        pygame.draw.line(self.screen, color, (x, y), (x, y + length), width)

        pygame.draw.line(
            self.screen,
            color,
            (x + w, y),
            (x + w - length, y),
            width,
        )
        pygame.draw.line(
            self.screen,
            color,
            (x + w, y),
            (x + w, y + length),
            width,
        )

        pygame.draw.line(
            self.screen,
            color,
            (x, y + h),
            (x + length, y + h),
            width,
        )
        pygame.draw.line(
            self.screen,
            color,
            (x, y + h),
            (x, y + h - length),
            width,
        )

        pygame.draw.line(
            self.screen,
            color,
            (x + w, y + h),
            (x + w - length, y + h),
            width,
        )
        pygame.draw.line(
            self.screen,
            color,
            (x + w, y + h),
            (x + w, y + h - length),
            width,
        )

    def draw_scene_label(self):
        if self.scene_title_time <= 0:
            return

        alpha = int(min(255, self.scene_title_time * 180))
        label = pygame.Surface((330, 40), pygame.SRCALPHA)
        label.fill((18, 11, 7, min(205, alpha)))
        self.screen.blit(label, (30, 64))

        pygame.draw.line(
            self.screen,
            (*C["red"], min(255, alpha)),
            (30, 64),
            (30, 104),
            4,
        )

        title = self.node.get("speaker") or "ФОТОСТУДИЯ AGFA"
        draw_text(
            self.screen,
            title.upper(),
            14,
            (248, 224, 186),
            (48, 75),
            bold=True,
            role="mono",
            letter_spacing=1,
        )

    def draw_transition(self):
        if self.transition_alpha <= 0:
            return

        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((16, 10, 6, int(self.transition_alpha)))
        self.screen.blit(overlay, (0, 0))

    def draw_vignette(self):
        # Intentionally disabled: no black translucent borders at the sides.
        return


    def draw_menu(self):
        self.screen.blit(self.assets.background("main_hall.png"), (0, 0))
        self.assets.draw_atmosphere(self.screen, self.visual_time)

        wash = pygame.Surface((W, H), pygame.SRCALPHA)
        wash.fill((41, 22, 8, 78))
        self.screen.blit(wash, (0, 0))

        # Main framed composition inspired by vintage photo lab packaging.
        frame = pygame.Rect(170, 36, 940, 630)
        frame_surface = pygame.Surface(frame.size, pygame.SRCALPHA)
        frame_surface.fill((25, 15, 8, 145))
        self.screen.blit(frame_surface, frame.topleft)

        pygame.draw.rect(
            self.screen,
            (214, 168, 103),
            frame,
            2,
            border_radius=8,
        )
        self.draw_corner_marks(frame, (234, 189, 123), 24, 2)
        pygame.draw.rect(
            self.screen,
            (70, 40, 18),
            frame.inflate(-10, -10),
            1,
            border_radius=6,
        )

        draw_text(
            self.screen,
            "ФОТОСТУДИЯ",
            34,
            (245, 191, 120),
            (W // 2, 66),
            center=True,
            bold=True,
            role="display",
            shadow=True,
            letter_spacing=2,
        )
        draw_text(
            self.screen,
            "AGFA",
            88,
            (255, 245, 224),
            (W // 2, 132),
            center=True,
            bold=True,
            role="display",
            shadow=True,
            letter_spacing=1,
        )

        badge = pygame.Rect(W // 2 + 128, 106, 112, 48)
        pygame.draw.polygon(
            self.screen,
            C["red"],
            [
                (badge.centerx, badge.top),
                (badge.right, badge.centery),
                (badge.centerx, badge.bottom),
                (badge.left, badge.centery),
            ],
        )
        draw_text(
            self.screen,
            "AGFA",
            22,
            C["white"],
            badge.center,
            center=True,
            bold=True,
            role="body",
        )

        pygame.draw.line(
            self.screen,
            (239, 203, 150),
            (400, 186),
            (880, 186),
            2,
        )

        draw_text(
            self.screen,
            "VISUAL NOVEL | ONE WORKING DAY",
            12,
            (184, 148, 105),
            (W // 2, 195),
            center=True,
            role="mono",
            letter_spacing=1,
        )

        for button in self.buttons:
            button.draw(self.screen)

        # Decorative film perforations.
        for y in range(76, 630, 32):
            pygame.draw.rect(
                self.screen,
                (191, 144, 85),
                (184, y, 8, 16),
                1,
                border_radius=2,
            )
            pygame.draw.rect(
                self.screen,
                (191, 144, 85),
                (1088, y, 8, 16),
                1,
                border_radius=2,
            )

        quote_rect = pygame.Rect(290, 520, 700, 48)
        quote_surface = pygame.Surface(quote_rect.size, pygame.SRCALPHA)
        quote_surface.fill((8, 7, 5, 165))
        self.screen.blit(quote_surface, quote_rect.topleft)
        pygame.draw.rect(
            self.screen,
            (217, 170, 104),
            quote_rect,
            1,
            border_radius=4,
        )

        draw_text(
            self.screen,
            "«Каждый день — новые заказы, новые проблемы»",
            19,
            (255, 235, 204),
            quote_rect.center,
            center=True,
            role="display",
            shadow=True,
        )

        # Bottom status strip.
        strip = pygame.Rect(188, 592, 904, 45)
        strip_surface = pygame.Surface(strip.size, pygame.SRCALPHA)
        strip_surface.fill((12, 9, 6, 205))
        self.screen.blit(strip_surface, strip.topleft)
        pygame.draw.rect(
            self.screen,
            (189, 138, 72),
            strip,
            1,
            border_radius=3,
        )

        draw_text(
            self.screen,
            f"РЕПУТАЦИЯ {self.state['reputation']:+d}",
            15,
            (255, 207, 95),
            (215, 606),
            bold=True,
            role="mono",
        )
        draw_text(
            self.screen,
            f"СТРЕСС {self.state['stress']}",
            15,
            (255, 112, 77),
            (505, 606),
            bold=True,
            role="mono",
        )
        draw_text(
            self.screen,
            f"КОЛЛЕКТИВ  {sum(1 for v in self.state['relationships'].values() if v > 0)} / 7",
            15,
            (255, 230, 185),
            (745, 606),
            bold=True,
            role="mono",
        )

        draw_text(
            self.screen,
            "ЭТАП 12",
            12,
            (170, 142, 110),
            (1040, 674),
            role="mono",
            letter_spacing=1,
        )

        self.draw_vignette()

    def draw_staff(self):
        self.screen.blit(self.assets.background("main_hall.png"), (0, 0))
        self.assets.draw_atmosphere(self.screen, self.visual_time)

        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((8, 11, 16, 180))
        self.screen.blit(overlay, (0, 0))

        name, sprite, description = STAFF[self.staff_index]
        relation = self.state["relationships"].get(name, 0)

        draw_text(
            self.screen,
            "КОЛЛЕКТИВ",
            42,
            C["white"],
            (70, 52),
            bold=True,
        )
        draw_text(
            self.screen,
            f"{self.staff_index + 1} / {len(STAFF)}",
            18,
            C["muted"],
            (1120, 65),
        )

        card = pygame.Rect(60, 125, 1160, 455)
        panel = pygame.Surface(card.size, pygame.SRCALPHA)
        panel.fill((14, 18, 24, 228))
        self.screen.blit(panel, card.topleft)
        pygame.draw.rect(
            self.screen,
            (255, 255, 255, 35),
            card,
            1,
            border_radius=16,
        )
        pygame.draw.line(
            self.screen,
            C["red"],
            (610, 125),
            (610, 580),
            2,
        )

        image = self.assets.character(sprite, 450, 405)
        x = 85 + (490 - image.get_width()) // 2
        y = 150 + (390 - image.get_height())
        shadow = pygame.Surface((image.get_width() + 80, 40), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 95), shadow.get_rect())
        self.screen.blit(shadow, (x - 40, 520))
        self.screen.blit(image, (x, y))

        draw_text(
            self.screen,
            name,
            40,
            C["white"],
            (665, 175),
            bold=True,
        )
        draw_text(
            self.screen,
            f"Отношение: {relation:+d}",
            21,
            C["green"] if relation >= 0 else C["red2"],
            (668, 235),
            bold=True,
        )

        desc_font = font(26)
        y_desc = 300
        for line in wrap_text(description, 485, desc_font):
            self.screen.blit(
                desc_font.render(line, True, C["muted"]),
                (668, y_desc),
            )
            y_desc += 36

        for button in self.buttons:
            button.draw(self.screen)

        self.draw_vignette()

    def draw_achievements(self):
        self.screen.blit(self.assets.background("main_hall.png"), (0, 0))
        self.assets.draw_atmosphere(self.screen, self.visual_time)

        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((15, 10, 6, 205))
        self.screen.blit(overlay, (0, 0))

        draw_text(
            self.screen,
            "ДОСТИЖЕНИЯ",
            34,
            (255, 233, 196),
            (70, 38),
            bold=True,
            role="display",
            shadow=True,
            letter_spacing=1,
        )
        draw_text(
            self.screen,
            f"Открыто: {len(self.state['achievements'])} / {len(ACHIEVEMENTS)}",
            16,
            (211, 188, 155),
            (72, 84),
            role="mono",
        )

        columns = 3
        gap_x = 18
        gap_y = 12
        start_x = 58
        start_y = 118
        total_width = W - start_x * 2
        card_w = (total_width - gap_x * (columns - 1)) // columns

        rows = (len(ACHIEVEMENTS) + columns - 1) // columns
        available_h = 500
        card_h = max(58, min(78, (available_h - gap_y * (rows - 1)) // rows))

        for index, (name, description) in enumerate(ACHIEVEMENTS):
            column = index % columns
            row = index // columns

            rect = pygame.Rect(
                start_x + column * (card_w + gap_x),
                start_y + row * (card_h + gap_y),
                card_w,
                card_h,
            )

            unlocked = name in self.state["achievements"]

            shadow = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            shadow.fill((0, 0, 0, 60))
            self.screen.blit(shadow, (rect.x, rect.y + 3))

            panel = pygame.Surface(rect.size, pygame.SRCALPHA)
            panel.fill(
                (232, 210, 174, 232)
                if unlocked
                else (59, 44, 31, 215)
            )
            self.screen.blit(panel, rect.topleft)

            pygame.draw.rect(
                self.screen,
                (183, 123, 55) if unlocked else (112, 84, 58),
                rect,
                1,
                border_radius=5,
            )

            icon_x = rect.x + 20
            icon_y = rect.centery
            pygame.draw.circle(
                self.screen,
                C["red"] if unlocked else (111, 92, 76),
                (icon_x, icon_y),
                7,
            )

            draw_text(
                self.screen,
                name if unlocked else "Скрыто",
                17,
                (36, 24, 15) if unlocked else (211, 194, 171),
                (rect.x + 40, rect.y + 10),
                bold=True,
                role="display",
            )

            desc_font = font(13, False, "body")
            desc = description if unlocked else "Условие пока не выполнено."
            lines = wrap_text(desc, rect.w - 54, desc_font)

            max_lines = 2 if card_h >= 70 else 1
            for line_index, line in enumerate(lines[:max_lines]):
                rendered = desc_font.render(
                    line,
                    True,
                    (79, 58, 39) if unlocked else (170, 151, 130),
                )
                self.screen.blit(
                    rendered,
                    (rect.x + 40, rect.y + 34 + line_index * 17),
                )

        back = Button((70, 648, 230, 42), "Назад", self.open_menu)
        back.draw(self.screen)
        self.buttons = [back]

        self.draw_vignette()

    def draw_results(self):
        self.screen.blit(self.assets.background("main_hall.png"), (0, 0))
        self.assets.draw_atmosphere(self.screen, self.visual_time)

        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((8, 11, 16, 215))
        self.screen.blit(overlay, (0, 0))

        title, description = self.calculate_ending()

        draw_text(
            self.screen,
            "ИТОГИ СМЕНЫ",
            16,
            C["red"],
            (W // 2, 66),
            center=True,
            bold=True,
            role="mono",
            letter_spacing=3,
        )
        draw_text(
            self.screen,
            title,
            52,
            C["white"],
            (W // 2, 120),
            center=True,
            bold=True,
            role="display",
            shadow=True,
        )

        card = pygame.Rect(180, 190, 920, 330)
        panel = pygame.Surface(card.size, pygame.SRCALPHA)
        panel.fill((14, 18, 24, 235))
        self.screen.blit(panel, card.topleft)
        pygame.draw.rect(
            self.screen,
            (255, 255, 255, 35),
            card,
            1,
            border_radius=16,
        )

        stats = [
            ("Репутация", f"{self.state['reputation']:+d}", C["green"]),
            ("Стресс", str(self.state["stress"]), C["orange"]),
            ("Заказы", str(self.state["orders"]), C["blue"]),
            ("Касса", f"{self.state['money']} руб.", C["white"]),
        ]

        for index, (label, value, color) in enumerate(stats):
            x = 235 + index * 210
            draw_text(
                self.screen,
                label.upper(),
                15,
                C["muted"],
                (x, 225),
                bold=True,
            )
            draw_text(
                self.screen,
                value,
                32,
                color,
                (x, 255),
                bold=True,
            )

        desc_font = font(24)
        y = 345
        for line in wrap_text(description, 790, desc_font):
            self.screen.blit(
                desc_font.render(line, True, C["white"]),
                (245, y),
            )
            y += 34

        draw_text(
            self.screen,
            f"Достижения: {len(self.state['achievements'])} / {len(ACHIEVEMENTS)}",
            18,
            C["muted"],
            (245, 455),
        )

        stamp = pygame.Surface((180, 64), pygame.SRCALPHA)
        pygame.draw.rect(
            stamp,
            (197, 58, 43, 24),
            stamp.get_rect(),
            3,
            border_radius=5,
        )
        draw_text(
            stamp,
            "СМЕНА ЗАКРЫТА",
            18,
            (210, 62, 48),
            stamp.get_rect().center,
            center=True,
            bold=True,
            role="mono",
            letter_spacing=1,
        )
        rotated_stamp = pygame.transform.rotate(stamp, -7)
        self.screen.blit(rotated_stamp, (830, 420))

        for button in self.buttons:
            button.draw(self.screen)

        self.draw_vignette()

    def draw_game(self):
        self.screen.blit(
            self.assets.background(self.node["bg"]),
            (0, 0),
        )
        self.assets.draw_atmosphere(self.screen, self.visual_time)

        dim = pygame.Surface((W, H), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 22))
        self.screen.blit(dim, (0, 0))

        if self.node.get("char"):
            image = self.assets.character(self.node["char"])
            bob = int(2 * pygame.math.Vector2(0, 1).y)
            y = H - image.get_height() - 86 + bob

            # Warm rim-light separates the cutout from the background.
            rim = pygame.mask.from_surface(image).to_surface(
                setcolor=(255, 187, 104, 42),
                unsetcolor=(0, 0, 0, 0),
            )
            rim = pygame.transform.smoothscale(
                rim,
                (image.get_width() + 8, image.get_height() + 8),
            )

            shadow = pygame.Surface(
                (image.get_width() + 110, 44),
                pygame.SRCALPHA,
            )
            pygame.draw.ellipse(
                shadow,
                (0, 0, 0, 105),
                shadow.get_rect(),
            )
            self.screen.blit(
                shadow,
                (self.char_x - 55, H - 105),
            )
            self.screen.blit(rim, (self.char_x - 4, y - 4))
            self.screen.blit(image, (self.char_x, y))

        top = pygame.Surface((W, 48), pygame.SRCALPHA)
        top.fill((7, 9, 13, 224))
        self.screen.blit(top, (0, 0))
        pygame.draw.line(
            self.screen,
            (255, 255, 255, 24),
            (0, 47),
            (W, 47),
            1,
        )

        draw_text(
            self.screen,
            f"ПОНЕДЕЛЬНИК | {self.state['time']}",
            17,
            C["muted"],
            (22, 14),
            bold=True,
            role="mono",
        )
        draw_text(
            self.screen,
            f"ЗАКАЗЫ {self.state['orders']}",
            16,
            C["blue"],
            (720, 14),
            bold=True,
            role="mono",
        )
        draw_text(
            self.screen,
            f"КАССА {self.state['money']} руб.",
            16,
            C["white"],
            (825, 14),
            bold=True,
            role="mono",
        )
        draw_text(
            self.screen,
            f"РЕП. {self.state['reputation']:+d}",
            16,
            C["green"],
            (1010, 14),
            bold=True,
            role="mono",
        )
        draw_text(
            self.screen,
            f"СТРЕСС {self.state['stress']}",
            16,
            C["orange"],
            (1130, 14),
            bold=True,
            role="mono",
        )

        if self.node.get("choices"):
            overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            overlay.fill((4, 6, 9, 132))
            self.screen.blit(overlay, (0, 0))

            context_rect = pygame.Rect(135, 72, 1010, 220)
            context_surface = pygame.Surface(
                context_rect.size,
                pygame.SRCALPHA,
            )
            context_surface.fill((9, 12, 17, 238))
            self.screen.blit(context_surface, context_rect.topleft)

            pygame.draw.rect(
                self.screen,
                (255, 255, 255, 35),
                context_rect,
                1,
                border_radius=14,
            )
            pygame.draw.line(
                self.screen,
                C["red"],
                (context_rect.x, context_rect.y),
                (context_rect.x, context_rect.bottom),
                5,
            )

            if self.node["speaker"]:
                draw_text(
                    self.screen,
                    self.node["speaker"].upper(),
                    17,
                    C["red"],
                    (context_rect.x + 28, context_rect.y + 20),
                    bold=True,
                    role="mono",
                    letter_spacing=1,
                )

            prompt_font = font(25, False, "body")
            prompt_y = (
                context_rect.y + 58
                if self.node["speaker"]
                else context_rect.y + 30
            )

            for line in wrap_text(
                self.node["text"],
                context_rect.w - 60,
                prompt_font,
            ):
                self.screen.blit(
                    prompt_font.render(line, True, C["white"]),
                    (context_rect.x + 28, prompt_y),
                )
                prompt_y += 34

            draw_text(
                self.screen,
                "ВЫБЕРИ ДЕЙСТВИЕ",
                14,
                C["white"],
                (W // 2, 307),
                center=True,
                bold=True,
                role="mono",
                letter_spacing=2,
            )

            for button in self.buttons:
                button.draw(self.screen)
        else:
            rect = pygame.Rect(64, H - 194, W - 128, 142)

            shadow = pygame.Surface((rect.w + 18, rect.h + 18), pygame.SRCALPHA)
            shadow.fill((0, 0, 0, 72))
            self.screen.blit(shadow, (rect.x - 9, rect.y + 8))

            glass = pygame.Surface(rect.size, pygame.SRCALPHA)
            glass.fill((9, 12, 17, 232))
            self.screen.blit(glass, rect.topleft)

            pygame.draw.rect(
                self.screen,
                (255, 255, 255, 26),
                rect,
                1,
                border_radius=6,
            )
            pygame.draw.line(
                self.screen,
                C["red"],
                (rect.x, rect.y),
                (rect.x, rect.bottom),
                4,
            )
            self.draw_corner_marks(rect, (160, 119, 72), 14, 1)

            # Tiny photo-lab metadata line.
            draw_text(
                self.screen,
                f"AGFA / {self.state['time']} / FRAME {self.state['orders'] + 1:02d}",
                11,
                (137, 126, 112),
                (rect.right - 235, rect.y + 12),
                role="mono",
                letter_spacing=1,
            )

            if self.node["speaker"]:
                draw_text(
                    self.screen,
                    self.node["speaker"].upper(),
                    17,
                    C["red"],
                    (rect.x + 28, rect.y + 18),
                    bold=True,
                    role="mono",
                    letter_spacing=1,
                )

            dialogue_font = font(25, False, "body")
            y = rect.y + 51 if self.node["speaker"] else rect.y + 28
            shown = self.node["text"][: int(self.visible_chars)]

            for line in wrap_text(
                shown,
                rect.w - 60,
                dialogue_font,
            ):
                self.screen.blit(
                    dialogue_font.render(line, True, C["white"]),
                    (rect.x + 28, y),
                )
                y += 35

            draw_text(
                self.screen,
                "ENTER",
                14,
                C["muted"],
                (rect.right - 75, rect.bottom - 25),
                bold=True,
            )

        if self.notice_time > 0 and self.notice:
            notice_rect = pygame.Rect(W // 2 - 230, 65, 460, 42)
            notice_surface = pygame.Surface(
                notice_rect.size,
                pygame.SRCALPHA,
            )
            notice_surface.fill((12, 15, 20, 225))
            self.screen.blit(notice_surface, notice_rect)

            pygame.draw.rect(
                self.screen,
                C["red"],
                notice_rect,
                1,
                border_radius=6,
            )
            draw_text(
                self.screen,
                self.notice,
                18,
                C["white"],
                notice_rect.center,
                center=True,
                bold=True,
            )

        # Progress line: visual rhythm without clutter.
        progress = min(
            1.0,
            max(0.0, self.state["orders"] / 8.0),
        )
        pygame.draw.line(
            self.screen,
            (70, 48, 31),
            (0, H - 3),
            (W, H - 3),
            3,
        )
        pygame.draw.line(
            self.screen,
            C["red"],
            (0, H - 3),
            (int(W * progress), H - 3),
            3,
        )

        self.draw_scene_label()
        self.draw_vignette()
        self.draw_transition()

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                self.handle_event(event)

            self.update(dt)

            if self.scene == "menu":
                self.draw_menu()
            elif self.scene == "staff":
                self.draw_staff()
            elif self.scene == "achievements":
                self.draw_achievements()
            elif self.scene == "results":
                self.draw_results()
            else:
                self.draw_game()

            pygame.display.flip()

        pygame.quit()




# ---------------------------------------------------------------------------
# FINAL POLISH LAYER
# Keeps the complete story above, but replaces the presentation and fixes
# the remaining state/UI issues without duplicating the narrative data.
# ---------------------------------------------------------------------------

SHIFT_START = 10 * 60
SHIFT_END = 19 * 60
COFFEE_LIMIT = 3
COFFEE_STRESS_RELIEF = 4
COFFEE_MINUTES = 10


def _parse_time(value):
    try:
        hours, minutes = str(value).split(":", 1)
        return int(hours) * 60 + int(minutes)
    except (TypeError, ValueError):
        return SHIFT_START


def _format_time(total_minutes):
    total_minutes = max(0, int(total_minutes))
    return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"


def _safe_value(value):
    return (
        str(value)
        .replace("₽", "руб.")
        .replace("•", " | ")
        .replace("\u2028", " ")
        .replace("\u2029", " ")
    )


def polished_draw_text(
    surface,
    value,
    size,
    color,
    pos,
    center=False,
    bold=False,
    role="body",
    shadow=False,
    letter_spacing=0,
):
    value = _safe_value(value)
    selected_font = font(size, bold, role)

    if letter_spacing <= 0:
        image = selected_font.render(value, True, color)
    else:
        glyphs = [selected_font.render(char, True, color) for char in value]
        width = sum(glyph.get_width() for glyph in glyphs)
        width += max(0, len(glyphs) - 1) * letter_spacing
        height = max((glyph.get_height() for glyph in glyphs), default=size)
        image = pygame.Surface((max(1, width), max(1, height)), pygame.SRCALPHA)
        x = 0
        for glyph in glyphs:
            image.blit(glyph, (x, 0))
            x += glyph.get_width() + letter_spacing

    rect = image.get_rect()
    if center:
        rect.center = pos
    else:
        rect.topleft = pos

    if shadow:
        shadow_image = image.copy()
        shadow_image.fill((0, 0, 0, 145), special_flags=pygame.BLEND_RGBA_MULT)
        surface.blit(shadow_image, rect.move(2, 3))

    surface.blit(image, rect)
    return rect


draw_text = polished_draw_text


def polished_background(self, name):
    if name in self.background_cache:
        return self.background_cache[name]

    path = BG / name
    if not path.exists():
        fallback = pygame.Surface((W, H))
        fallback.fill((28, 31, 38))
        self.background_cache[name] = fallback
        return fallback

    source = self.load(path, False)
    source_ratio = source.get_width() / source.get_height()
    target_ratio = W / H

    if source_ratio > target_ratio:
        crop_width = int(source.get_height() * target_ratio)
        left = (source.get_width() - crop_width) // 2
        source = source.subsurface(pygame.Rect(left, 0, crop_width, source.get_height()))
    elif source_ratio < target_ratio:
        crop_height = int(source.get_width() / target_ratio)
        top = (source.get_height() - crop_height) // 2
        source = source.subsurface(pygame.Rect(0, top, source.get_width(), crop_height))

    # Keep the uploaded room art crisp. The previous downscale/upscale blur was
    # the main reason the backgrounds looked washed out.
    image = pygame.transform.smoothscale(source, (W, H)).copy()
    self.background_cache[name] = image
    return image


def polished_atmosphere(self, surface, time_value):
    # Static, subtle contrast treatment only: no dust, grain, beams or flicker.
    shade = pygame.Surface((W, H), pygame.SRCALPHA)
    pygame.draw.rect(shade, (5, 8, 13, 34), (0, 0, W, H))
    pygame.draw.rect(shade, (5, 8, 13, 28), (0, H - 250, W, 250))
    surface.blit(shade, (0, 0))


Assets.background = polished_background
Assets.draw_atmosphere = polished_atmosphere


def polished_button_draw(self, surface):
    hovered = self.enabled and self.rect.collidepoint(pygame.mouse.get_pos())

    shadow = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
    shadow.fill((0, 0, 0, 95))
    surface.blit(shadow, self.rect.move(0, 4).topleft)

    panel = pygame.Surface(self.rect.size, pygame.SRCALPHA)
    if not self.enabled:
        panel.fill((24, 28, 34, 190))
    elif hovered:
        panel.fill((45, 31, 34, 246))
    else:
        panel.fill((17, 21, 28, 236))
    surface.blit(panel, self.rect.topleft)

    border = C["red2"] if hovered else (255, 255, 255, 46)
    pygame.draw.rect(surface, border, self.rect, 2 if hovered else 1, border_radius=8)
    pygame.draw.rect(
        surface,
        C["red"] if self.enabled else (88, 91, 96),
        (self.rect.x, self.rect.y, 5, self.rect.h),
        border_radius=3,
    )

    if self.label in {"<", ">"}:
        cx, cy = self.rect.center
        direction = -1 if self.label == "<" else 1
        points = [
            (cx - 6 * direction, cy - 11),
            (cx + 6 * direction, cy),
            (cx - 6 * direction, cy + 11),
        ]
        pygame.draw.polygon(surface, C["red2"] if hovered else C["white"], points)
        return

    label = _safe_value(self.label)
    color = C["white"] if self.enabled else (126, 132, 140)
    text_font = font(21 if self.rect.w > 500 else 20, hovered, "body")
    lines = wrap_text(label, self.rect.w - 46, text_font)
    lines = lines[:2]
    line_height = text_font.get_linesize()
    total_height = len(lines) * line_height
    y = self.rect.centery - total_height // 2
    for line in lines:
        image = text_font.render(line, True, color)
        surface.blit(image, image.get_rect(center=(self.rect.centerx, y + line_height // 2)))
        y += line_height


Button.draw = polished_button_draw


def polished_open_menu(self):
    self.scene = "menu"
    self.buttons = [
        Button((770, 205, 420, 54), "Новая смена", self.new_game),
        Button((770, 270, 420, 54), "Продолжить", self.continue_game, SAVE.exists()),
        Button((770, 335, 420, 54), "Коллектив", self.open_staff),
        Button((770, 400, 420, 54), "Достижения", self.open_achievements),
        Button((770, 465, 420, 54), "Полный экран [F11]", self.toggle_fullscreen),
        Button((770, 530, 420, 54), "Выход", self.quit),
    ]


def polished_open_staff(self):
    self.scene = "staff"
    self.staff_index = 0
    self.buttons = [
        Button((68, 642, 230, 48), "Назад", self.open_menu),
        Button((920, 642, 100, 48), "<", self.staff_prev),
        Button((1035, 642, 100, 48), ">", self.staff_next),
    ]


def polished_open_achievements(self):
    self.scene = "achievements"
    self.buttons = [Button((68, 654, 230, 42), "Назад", self.open_menu)]


def polished_open_results(self):
    self.scene = "results"
    self.buttons = [Button((440, 620, 400, 54), "Вернуться в меню", self.open_menu)]


Game.open_menu = polished_open_menu
Game.open_staff = polished_open_staff
Game.open_achievements = polished_open_achievements
Game.open_results = polished_open_results


def polished_apply_effect(self, data):
    if not data:
        return

    self.state["stress"] = max(0, min(100, self.state.get("stress", 0) + data.get("stress", 0)))
    self.state["reputation"] = self.state.get("reputation", 0) + data.get("reputation", 0)
    self.state["orders"] = max(0, self.state.get("orders", 0) + data.get("orders", 0))
    self.state["money"] = max(0, self.state.get("money", 0) + data.get("money", 0))
    self.state.setdefault("coffee_used", 0)
    self.unlock_achievement(data.get("achievement"))

    relation = data.get("relation")
    if relation:
        value = self.state["relationships"].get(relation, 0) + data.get("relation_delta", 0)
        self.state["relationships"][relation] = max(-5, min(5, value))

    if data.get("flag"):
        self.state["flags"][data["flag"]] = data.get("flag_value", True)

    if data.get("time"):
        self.state["time"] = _format_time(max(_parse_time(self.state.get("time")), _parse_time(data["time"])))


def polished_open_node(self, key):
    self.state["node"] = key
    self.node = STORY[key]
    self.state.setdefault("coffee_used", 0)

    if self.node.get("time"):
        current = _parse_time(self.state.get("time", "09:59"))
        scheduled = _parse_time(self.node["time"])
        self.state["time"] = _format_time(max(current, scheduled))

    self.visible_chars = 0.0
    self.scene = "game"
    self.transition_alpha = 205.0
    self.scene_title_time = 1.4

    side = self.node.get("side", "right")
    self.char_target = 815 if side == "right" else 35
    self.char_x = self.char_target + (100 if side == "right" else -100)

    self.build_choice_buttons()
    save_game(self.state)


def polished_build_choice_buttons(self):
    self.buttons = []
    choices = self.node.get("choices", [])
    if not choices:
        return

    height = 62
    gap = 12
    total = len(choices) * height + max(0, len(choices) - 1) * gap
    start_y = 324 + max(0, (238 - total) // 2)

    for index, choice in enumerate(choices):
        self.buttons.append(
            Button(
                (160, start_y + index * (height + gap), 960, height),
                choice["text"],
                lambda i=index: self.choose(i),
            )
        )


Game.apply_effect = polished_apply_effect
Game.open_node = polished_open_node
Game.build_choice_buttons = polished_build_choice_buttons


def game_drink_coffee(self):
    used = int(self.state.get("coffee_used", 0))
    stress = int(self.state.get("stress", 0))
    current_time = _parse_time(self.state.get("time", "10:00"))

    if used >= COFFEE_LIMIT:
        self.notice = "Кофе закончился: три чашки за смену уже выпиты."
        self.notice_time = 2.8
        return
    if stress <= 0:
        self.notice = "Стресс уже на нуле. Кофе можно оставить на потом."
        self.notice_time = 2.8
        return
    if current_time >= 18 * 60 + 50:
        self.notice = "До закрытия десять минут. Кофе уже не успеет помочь."
        self.notice_time = 2.8
        return

    removed = min(COFFEE_STRESS_RELIEF, stress)
    self.state["stress"] = stress - removed
    self.state["coffee_used"] = used + 1
    self.state["time"] = _format_time(min(19 * 60 + 4, current_time + COFFEE_MINUTES))
    self.unlock_achievement("Кофе вместо терапии")
    self.notice = f"Кофе выпит: стресс -{removed}, время +{COFFEE_MINUTES} минут."
    self.notice_time = 3.0
    save_game(self.state)


Game.drink_coffee = game_drink_coffee


def polished_handle_event(self, event):
    if event.type == pygame.QUIT:
        self.quit()
        return

    if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
        self.toggle_fullscreen()
        return

    if self.scene in {"menu", "staff", "achievements", "results"}:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.open_menu()
            return
        for button in self.buttons:
            button.handle(event)
        return

    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            self.open_menu()
            return
        if event.key == pygame.K_c:
            self.drink_coffee()
            return
        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.advance()
            return

        key_map = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2}
        if self.node.get("choices") and event.key in key_map:
            index = key_map[event.key]
            if index < len(self.buttons):
                self.choose(index)
            return

    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        coffee_rect = pygame.Rect(1060, 10, 200, 38)
        if coffee_rect.collidepoint(event.pos):
            self.drink_coffee()
            return

    if self.node.get("choices"):
        for button in self.buttons:
            button.handle(event)
    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        self.advance()


Game.handle_event = polished_handle_event


def _draw_dim(surface, alpha=110):
    layer = pygame.Surface((W, H), pygame.SRCALPHA)
    layer.fill((5, 8, 13, alpha))
    surface.blit(layer, (0, 0))


def _draw_header(surface, title, subtitle=None):
    draw_text(surface, title, 36, C["white"], (68, 52), bold=True, role="body", shadow=True)
    pygame.draw.rect(surface, C["red"], (68, 101, 78, 5), border_radius=2)
    if subtitle:
        draw_text(surface, subtitle, 17, C["muted"], (68, 118), role="body")


def polished_draw_menu(self):
    self.screen.blit(self.assets.background("main_hall.png"), (0, 0))
    _draw_dim(self.screen, 155)

    # Left branding block.
    pygame.draw.rect(self.screen, (9, 13, 19, 222), (55, 54, 635, 610), border_radius=16)
    pygame.draw.rect(self.screen, (255, 255, 255, 34), (55, 54, 635, 610), 1, border_radius=16)
    pygame.draw.rect(self.screen, C["red"], (55, 54, 7, 610), border_radius=4)

    draw_text(self.screen, "ФОТОСТУДИЯ", 28, C["muted"], (95, 105), bold=True, role="body", letter_spacing=2)
    draw_text(self.screen, "AGFA", 104, C["white"], (88, 137), bold=True, role="body", shadow=True)

    # AGFA diamond mark drawn without external logo/font dependencies.
    diamond = [(520, 164), (567, 206), (520, 248), (473, 206)]
    pygame.draw.polygon(self.screen, C["red"], diamond)
    draw_text(self.screen, "AGFA", 18, C["white"], (520, 206), center=True, bold=True, role="body")

    draw_text(self.screen, "ИНТЕРАКТИВНАЯ РАБОЧАЯ СМЕНА", 17, C["white"], (96, 285), bold=True, role="mono", letter_spacing=1)
    draw_text(self.screen, "ПОНЕДЕЛЬНИК  |  10:00-19:00", 18, C["red2"], (96, 323), bold=True, role="mono")

    story_font = font(23, False, "body")
    y = 382
    description = (
        "Один полный день в фотостудии: клиенты, техника, срочные заказы, "
        "решения и отношения с коллективом. Каждый выбор влияет на итог смены."
    )
    for line in wrap_text(description, 515, story_font):
        self.screen.blit(story_font.render(line, True, C["white"]), (96, y))
        y += 32

    info = pygame.Rect(92, 535, 560, 82)
    pygame.draw.rect(self.screen, (25, 30, 38), info, border_radius=10)
    pygame.draw.rect(self.screen, (67, 73, 82), info, 1, border_radius=10)
    draw_text(self.screen, "УПРАВЛЕНИЕ", 13, C["red2"], (112, 552), bold=True, role="mono", letter_spacing=1)
    draw_text(self.screen, "ENTER - дальше   |   1-3 - выбор   |   C - кофе   |   F11 - экран", 16, C["muted"], (112, 579), role="body")

    for button in self.buttons:
        button.draw(self.screen)

    draw_text(self.screen, "FINAL EDITION", 12, (160, 166, 174), (1172, 686), role="mono", center=True)


def polished_draw_staff(self):
    self.screen.blit(self.assets.background("workplace.png"), (0, 0))
    _draw_dim(self.screen, 176)
    _draw_header(self.screen, "КОЛЛЕКТИВ", "Листай карточки и смотри, как меняются отношения за смену.")

    name, image_name, description = STAFF[self.staff_index]
    relation = self.state.get("relationships", {}).get(name, 0)

    card = pygame.Rect(68, 162, 1144, 438)
    pygame.draw.rect(self.screen, (10, 14, 20, 236), card, border_radius=16)
    pygame.draw.rect(self.screen, (62, 68, 77), card, 1, border_radius=16)
    pygame.draw.rect(self.screen, C["red"], (card.x, card.y, 7, card.h), border_radius=4)

    image = self.assets.character(image_name, max_width=370, max_height=390)
    image_x = card.x + 55 + (370 - image.get_width()) // 2
    image_y = card.bottom - image.get_height() - 18
    shadow = pygame.Surface((image.get_width() + 70, 34), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 120), shadow.get_rect())
    self.screen.blit(shadow, (image_x - 35, card.bottom - 38))
    self.screen.blit(image, (image_x, image_y))

    draw_text(self.screen, name.upper(), 39, C["white"], (535, 212), bold=True, role="body")
    draw_text(self.screen, f"КАРТОЧКА {self.staff_index + 1}/{len(STAFF)}", 13, C["red2"], (538, 266), bold=True, role="mono", letter_spacing=1)

    desc_font = font(23, False, "body")
    y = 312
    for line in wrap_text(description, 590, desc_font):
        self.screen.blit(desc_font.render(line, True, C["white"]), (538, y))
        y += 33

    draw_text(self.screen, "ОТНОШЕНИЯ", 14, C["muted"], (538, 415), bold=True, role="mono", letter_spacing=1)
    for index in range(11):
        value = index - 5
        x = 538 + index * 48
        active = (value <= relation if relation >= 0 else value >= relation and value <= 0)
        color = C["green"] if value > 0 else C["red"] if value < 0 else C["muted"]
        pygame.draw.rect(self.screen, color if active else (57, 63, 72), (x, 454, 34, 12), border_radius=6)
    draw_text(self.screen, f"{relation:+d}", 25, C["green"] if relation >= 0 else C["red2"], (1070, 436), bold=True, role="mono")

    draw_text(self.screen, "Хорошие отношения открывают более тёплые варианты финала.", 17, C["muted"], (538, 505), role="body")

    for button in self.buttons:
        button.draw(self.screen)


def polished_draw_achievements(self):
    self.screen.blit(self.assets.background("cutter_room.png"), (0, 0))
    _draw_dim(self.screen, 190)
    unlocked = set(self.state.get("achievements", []))
    _draw_header(self.screen, "ДОСТИЖЕНИЯ", f"Открыто {len(unlocked)} из {len(ACHIEVEMENTS)}")

    columns = 3
    card_w = 365
    card_h = 72
    start_x = 68
    start_y = 155
    gap_x = 28
    gap_y = 10

    for index, (name, description) in enumerate(ACHIEVEMENTS):
        col = index % columns
        row = index // columns
        rect = pygame.Rect(start_x + col * (card_w + gap_x), start_y + row * (card_h + gap_y), card_w, card_h)
        is_unlocked = name in unlocked
        fill = (24, 31, 40, 242) if is_unlocked else (15, 19, 25, 218)
        pygame.draw.rect(self.screen, fill, rect, border_radius=9)
        pygame.draw.rect(self.screen, C["red"] if is_unlocked else (66, 72, 81), rect, 2 if is_unlocked else 1, border_radius=9)

        icon_center = (rect.x + 31, rect.centery)
        pygame.draw.circle(self.screen, C["red"] if is_unlocked else (62, 68, 77), icon_center, 13)
        if is_unlocked:
            pygame.draw.line(self.screen, C["white"], (icon_center[0] - 6, icon_center[1]), (icon_center[0] - 1, icon_center[1] + 5), 3)
            pygame.draw.line(self.screen, C["white"], (icon_center[0] - 1, icon_center[1] + 5), (icon_center[0] + 7, icon_center[1] - 6), 3)

        draw_text(self.screen, name if is_unlocked else "Не открыто", 17, C["white"] if is_unlocked else C["muted"], (rect.x + 56, rect.y + 12), bold=is_unlocked, role="body")
        small = font(13, False, "body")
        shown_description = description if is_unlocked else "Продолжай смену и пробуй другие решения."
        lines = wrap_text(shown_description, rect.w - 72, small)[:2]
        y = rect.y + 38
        for line in lines:
            self.screen.blit(small.render(line, True, C["muted"]), (rect.x + 56, y))
            y += 16

    for button in self.buttons:
        button.draw(self.screen)


def polished_draw_results(self):
    self.screen.blit(self.assets.background("street.png"), (0, 0))
    _draw_dim(self.screen, 184)

    title, description = self.calculate_ending()
    card = pygame.Rect(120, 62, 1040, 530)
    pygame.draw.rect(self.screen, (9, 13, 19, 244), card, border_radius=18)
    pygame.draw.rect(self.screen, (65, 71, 80), card, 1, border_radius=18)
    pygame.draw.rect(self.screen, C["red"], (card.x, card.y, 8, card.h), border_radius=4)

    draw_text(self.screen, "СМЕНА 10:00-19:00 ЗАВЕРШЕНА", 14, C["red2"], (160, 100), bold=True, role="mono", letter_spacing=2)
    draw_text(self.screen, title, 43, C["white"], (160, 135), bold=True, role="body")

    desc_font = font(22, False, "body")
    y = 205
    for line in wrap_text(description, 880, desc_font):
        self.screen.blit(desc_font.render(line, True, C["muted"]), (160, y))
        y += 31

    metrics = [
        ("ЗАКАЗЫ", str(self.state.get("orders", 0)), C["blue"]),
        ("КАССА", f"{self.state.get('money', 0)} руб.", C["white"]),
        ("РЕПУТАЦИЯ", f"{self.state.get('reputation', 0):+d}", C["green"]),
        ("СТРЕСС", str(self.state.get("stress", 0)), C["orange"]),
    ]
    for index, (label, value, color) in enumerate(metrics):
        rect = pygame.Rect(160 + index * 225, 315, 205, 105)
        pygame.draw.rect(self.screen, (24, 29, 37), rect, border_radius=10)
        pygame.draw.rect(self.screen, (61, 67, 76), rect, 1, border_radius=10)
        draw_text(self.screen, label, 13, C["muted"], (rect.centerx, rect.y + 24), center=True, bold=True, role="mono", letter_spacing=1)
        draw_text(self.screen, value, 28, color, (rect.centerx, rect.y + 67), center=True, bold=True, role="body")

    relations = self.state.get("relationships", {})
    best = sorted(relations.items(), key=lambda item: item[1], reverse=True)[:3]
    best_text = " | ".join(f"{name}: {value:+d}" for name, value in best)
    draw_text(self.screen, "ЛУЧШИЕ ОТНОШЕНИЯ", 13, C["red2"], (160, 462), bold=True, role="mono", letter_spacing=1)
    draw_text(self.screen, best_text, 19, C["white"], (160, 491), role="body")
    draw_text(self.screen, f"Достижения: {len(self.state.get('achievements', []))}/{len(ACHIEVEMENTS)}   |   Кофе: {self.state.get('coffee_used', 0)}/{COFFEE_LIMIT}", 17, C["muted"], (160, 535), role="body")

    for button in self.buttons:
        button.draw(self.screen)


def _draw_character(self):
    if not self.node.get("char"):
        return

    image = self.assets.character(self.node["char"], max_width=420, max_height=505)
    y = H - image.get_height() - 58

    mask = pygame.mask.from_surface(image)
    outline = mask.to_surface(setcolor=(5, 8, 13, 185), unsetcolor=(0, 0, 0, 0))
    for dx, dy in ((-4, 0), (4, 0), (0, -4), (0, 4)):
        self.screen.blit(outline, (self.char_x + dx, y + dy))

    shadow = pygame.Surface((image.get_width() + 90, 36), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 120), shadow.get_rect())
    self.screen.blit(shadow, (self.char_x - 45, H - 87))
    self.screen.blit(image, (self.char_x, y))


def _draw_game_topbar(self):
    bar = pygame.Surface((W, 58), pygame.SRCALPHA)
    bar.fill((8, 12, 18, 246))
    self.screen.blit(bar, (0, 0))
    pygame.draw.line(self.screen, C["red"], (0, 57), (W, 57), 2)

    current = _parse_time(self.state.get("time", "10:00"))
    progress = max(0.0, min(1.0, (current - SHIFT_START) / (SHIFT_END - SHIFT_START)))

    draw_text(self.screen, "ПОНЕДЕЛЬНИК", 13, C["muted"], (18, 10), bold=True, role="mono", letter_spacing=1)
    draw_text(self.screen, self.state.get("time", "10:00"), 24, C["white"], (18, 27), bold=True, role="mono")

    pygame.draw.rect(self.screen, (48, 55, 65), (185, 28, 272, 8), border_radius=4)
    pygame.draw.rect(self.screen, C["red"], (185, 28, int(272 * progress), 8), border_radius=4)
    draw_text(self.screen, "10:00", 11, C["muted"], (185, 9), role="mono")
    draw_text(self.screen, "19:00", 11, C["muted"], (420, 9), role="mono")

    stats = [
        ("ЗАКАЗЫ", self.state.get("orders", 0), C["blue"], 490),
        ("КАССА", f"{self.state.get('money', 0)} руб.", C["white"], 610),
        ("РЕП.", f"{self.state.get('reputation', 0):+d}", C["green"], 790),
        ("СТРЕСС", self.state.get("stress", 0), C["orange"], 900),
    ]
    for label, value, color, x in stats:
        draw_text(self.screen, label, 11, C["muted"], (x, 9), bold=True, role="mono")
        draw_text(self.screen, value, 18, color, (x, 27), bold=True, role="mono")

    coffee_rect = pygame.Rect(1060, 10, 200, 38)
    hovered = coffee_rect.collidepoint(pygame.mouse.get_pos())
    used = self.state.get("coffee_used", 0)
    pygame.draw.rect(self.screen, (48, 31, 29) if hovered else (25, 29, 36), coffee_rect, border_radius=8)
    pygame.draw.rect(self.screen, C["red2"] if hovered else (255, 255, 255, 45), coffee_rect, 1, border_radius=8)
    draw_text(self.screen, f"КОФЕ {used}/{COFFEE_LIMIT}  [C]", 15, C["white"], coffee_rect.center, center=True, bold=True, role="mono")


def polished_draw_game(self):
    self.screen.blit(self.assets.background(self.node["bg"]), (0, 0))
    self.assets.draw_atmosphere(self.screen, self.visual_time)
    _draw_character(self)
    _draw_game_topbar(self)

    if self.node.get("choices"):
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((4, 7, 11, 118))
        self.screen.blit(overlay, (0, 0))

        context = pygame.Rect(100, 88, 1080, 190)
        pygame.draw.rect(self.screen, (9, 13, 19, 242), context, border_radius=14)
        pygame.draw.rect(self.screen, (66, 72, 81), context, 1, border_radius=14)
        pygame.draw.rect(self.screen, C["red"], (context.x, context.y, 6, context.h), border_radius=3)

        if self.node.get("speaker"):
            draw_text(self.screen, self.node["speaker"].upper(), 15, C["red2"], (context.x + 28, context.y + 20), bold=True, role="mono", letter_spacing=1)
            text_y = context.y + 55
        else:
            text_y = context.y + 28

        prompt_font = font(25, False, "body")
        for line in wrap_text(self.node["text"], context.w - 58, prompt_font):
            self.screen.blit(prompt_font.render(line, True, C["white"]), (context.x + 28, text_y))
            text_y += 34

        draw_text(self.screen, "ВЫБЕРИ ДЕЙСТВИЕ", 13, C["muted"], (W // 2, 300), center=True, bold=True, role="mono", letter_spacing=2)
        for button in self.buttons:
            button.draw(self.screen)
    else:
        rect = pygame.Rect(55, 525, 1170, 155)
        shadow = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 105))
        self.screen.blit(shadow, rect.move(0, 6).topleft)
        pygame.draw.rect(self.screen, (8, 12, 18, 242), rect, border_radius=12)
        pygame.draw.rect(self.screen, (65, 71, 80), rect, 1, border_radius=12)
        pygame.draw.rect(self.screen, C["red"], (rect.x, rect.y, 6, rect.h), border_radius=3)

        if self.node.get("speaker"):
            draw_text(self.screen, self.node["speaker"].upper(), 15, C["red2"], (rect.x + 28, rect.y + 18), bold=True, role="mono", letter_spacing=1)
            y = rect.y + 51
        else:
            y = rect.y + 28

        shown = self.node["text"][: int(self.visible_chars)]
        dialogue_font = font(25, False, "body")
        for line in wrap_text(shown, rect.w - 58, dialogue_font):
            self.screen.blit(dialogue_font.render(line, True, C["white"]), (rect.x + 28, y))
            y += 34

        draw_text(self.screen, "ENTER / КЛИК", 12, C["muted"], (rect.right - 125, rect.bottom - 28), bold=True, role="mono")

    if self.notice_time > 0 and self.notice:
        notice_rect = pygame.Rect(W // 2 - 270, 70, 540, 44)
        pygame.draw.rect(self.screen, (10, 14, 20, 244), notice_rect, border_radius=9)
        pygame.draw.rect(self.screen, C["red2"], notice_rect, 1, border_radius=9)
        draw_text(self.screen, self.notice, 17, C["white"], notice_rect.center, center=True, bold=True, role="body")

    # Shift progress at the very bottom, independent from the number of orders.
    current = _parse_time(self.state.get("time", "10:00"))
    progress = max(0.0, min(1.0, (current - SHIFT_START) / (SHIFT_END - SHIFT_START)))
    pygame.draw.rect(self.screen, (36, 42, 50), (0, H - 4, W, 4))
    pygame.draw.rect(self.screen, C["red"], (0, H - 4, int(W * progress), 4))

    self.draw_transition()


Game.draw_menu = polished_draw_menu
Game.draw_staff = polished_draw_staff
Game.draw_achievements = polished_draw_achievements
Game.draw_results = polished_draw_results
Game.draw_game = polished_draw_game



# ---------------------------------------------------------------------------
# PIXEL EDITION PRESENTATION LAYER
# ---------------------------------------------------------------------------

# Warmer, game-like palette matching the new pixel-art rooms.
C.update({
    "white": (255, 241, 204),
    "muted": (202, 184, 151),
    "red": (215, 78, 61),
    "red2": (255, 170, 70),
    "dark": (20, 24, 40),
    "panel": (31, 35, 53),
    "green": (125, 201, 125),
    "orange": (255, 184, 76),
    "blue": (116, 166, 207),
    "cream": (241, 211, 161),
    "paper": (224, 184, 126),
})


PIXEL_FONT_CACHE = {}


def pixel_font(size: int, bold: bool = False, role: str = "body"):
    # Monospaced system fonts retain Cyrillic support and read more like a game UI.
    key = (size, bold, role)
    if key in PIXEL_FONT_CACHE:
        return PIXEL_FONT_CACHE[key]

    candidates = ["dejavusansmono", "consolas", "couriernew", "liberationmono"]
    selected = None
    for family in candidates:
        matched = pygame.font.match_font(family, bold=bold)
        if matched:
            selected = pygame.font.Font(matched, size)
            break

    if selected is None:
        selected = pygame.font.SysFont("arial", size, bold=bold)

    selected.set_bold(bold)
    PIXEL_FONT_CACHE[key] = selected
    return selected


font = pixel_font


def pixel_draw_text(
    surface,
    value,
    size,
    color,
    pos,
    center=False,
    bold=False,
    role="body",
    shadow=False,
    letter_spacing=0,
):
    value = _safe_value(value)
    selected_font = font(size, bold, role)

    if letter_spacing <= 0:
        # No antialiasing: intentional sharp pixel edge.
        image = selected_font.render(value, False, color)
    else:
        glyphs = [selected_font.render(char, False, color) for char in value]
        width = sum(g.get_width() for g in glyphs) + max(0, len(glyphs)-1) * letter_spacing
        height = max((g.get_height() for g in glyphs), default=size)
        image = pygame.Surface((max(1, width), max(1, height)), pygame.SRCALPHA)
        x = 0
        for glyph in glyphs:
            image.blit(glyph, (x, 0))
            x += glyph.get_width() + letter_spacing

    rect = image.get_rect()
    if center:
        rect.center = pos
    else:
        rect.topleft = pos

    if shadow:
        shadow_image = image.copy()
        shadow_image.fill((0, 0, 0, 175), special_flags=pygame.BLEND_RGBA_MULT)
        surface.blit(shadow_image, rect.move(3, 3))

    surface.blit(image, rect)
    return rect


draw_text = pixel_draw_text


def pixel_background(self, name):
    if name in self.background_cache:
        return self.background_cache[name]

    path = BG / name
    if not path.exists():
        fallback = pygame.Surface((W, H))
        fallback.fill(C["dark"])
        self.background_cache[name] = fallback
        return fallback

    source = self.load(path, False)
    source_ratio = source.get_width() / source.get_height()
    target_ratio = W / H

    if source_ratio > target_ratio:
        crop_width = int(source.get_height() * target_ratio)
        left = (source.get_width() - crop_width) // 2
        source = source.subsurface(
            pygame.Rect(left, 0, crop_width, source.get_height())
        )
    elif source_ratio < target_ratio:
        crop_height = int(source.get_width() / target_ratio)
        top = (source.get_height() - crop_height) // 2
        source = source.subsurface(
            pygame.Rect(0, top, source.get_width(), crop_height)
        )

    # Deliberately use nearest-neighbour scaling.
    image = pygame.transform.scale(source, (W, H)).copy()
    self.background_cache[name] = image
    return image


def pixel_atmosphere(self, surface, time_value):
    # A single transparent shade only; no blur, grain or smooth effects.
    shade = pygame.Surface((W, H), pygame.SRCALPHA)
    shade.fill((12, 16, 31, 26))
    surface.blit(shade, (0, 0))


def pixel_character(self, name, max_width=430, max_height=510):
    image = self.load(CH / name, True)
    scale = min(max_width / image.get_width(), max_height / image.get_height())
    size = (
        max(1, int(image.get_width() * scale)),
        max(1, int(image.get_height() * scale)),
    )
    return pygame.transform.scale(image, size)


Assets.background = pixel_background
Assets.draw_atmosphere = pixel_atmosphere
Assets.character = pixel_character


def _pixel_box(surface, rect, fill=(27, 31, 48), border=(245, 202, 124), shadow=6):
    shadow_rect = rect.move(shadow, shadow)
    pygame.draw.rect(surface, (8, 10, 20), shadow_rect)
    pygame.draw.rect(surface, fill, rect)
    pygame.draw.rect(surface, border, rect, 3)
    pygame.draw.rect(surface, (97, 57, 49), rect.inflate(-8, -8), 1)


def pixel_button_draw(self, surface):
    hovered = self.enabled and self.rect.collidepoint(pygame.mouse.get_pos())

    shadow = self.rect.move(5, 5)
    pygame.draw.rect(surface, (8, 10, 18), shadow)

    if not self.enabled:
        fill = (63, 61, 68)
        border = (112, 103, 96)
        text_color = (157, 149, 139)
    elif hovered:
        fill = (255, 187, 87)
        border = (255, 235, 181)
        text_color = (34, 29, 37)
    else:
        fill = (231, 194, 137)
        border = (255, 229, 174)
        text_color = (44, 34, 38)

    pygame.draw.rect(surface, fill, self.rect)
    pygame.draw.rect(surface, border, self.rect, 3)
    pygame.draw.rect(surface, (122, 66, 54), self.rect.inflate(-8, -8), 1)

    if self.label in {"<", ">"}:
        cx, cy = self.rect.center
        if self.label == "<":
            pts = [(cx + 8, cy - 12), (cx - 8, cy), (cx + 8, cy + 12)]
        else:
            pts = [(cx - 8, cy - 12), (cx + 8, cy), (cx - 8, cy + 12)]
        pygame.draw.polygon(surface, text_color, pts)
        return

    label = _safe_value(self.label)
    text_font = font(20 if self.rect.w < 500 else 21, hovered, "body")
    lines = wrap_text(label, self.rect.w - 48, text_font)[:2]
    line_h = text_font.get_linesize()
    y = self.rect.centery - (len(lines) * line_h) // 2
    for line in lines:
        image = text_font.render(line, False, text_color)
        surface.blit(image, image.get_rect(center=(self.rect.centerx, y + line_h // 2)))
        y += line_h


Button.draw = pixel_button_draw


def pixel_draw_menu(self):
    self.screen.blit(self.assets.background("main_hall.png"), (0, 0))

    dim = pygame.Surface((W, H), pygame.SRCALPHA)
    dim.fill((10, 13, 27, 108))
    self.screen.blit(dim, (0, 0))

    title_box = pygame.Rect(56, 56, 650, 258)
    _pixel_box(self.screen, title_box, fill=(24, 27, 43), border=(255, 190, 93))

    draw_text(self.screen, "ФОТОСТУДИЯ", 26, (235, 182, 113), (92, 88), bold=True, role="mono")
    draw_text(self.screen, "AGFA", 91, C["white"], (88, 119), bold=True, role="mono", shadow=True)
    draw_text(self.screen, "НОВАЯ СМЕНА", 20, C["red2"], (94, 227), bold=True, role="mono")
    draw_text(self.screen, "10:00 - 19:00", 22, C["white"], (94, 260), bold=True, role="mono")

    note = pygame.Rect(56, 338, 650, 290)
    _pixel_box(self.screen, note, fill=(30, 32, 46), border=(155, 95, 71))
    lines = [
        "Один рабочий день в студии.",
        "Клиенты, срочные заказы, техника,",
        "коллеги, кофе и последствия решений.",
        "",
    ]
    y = 378
    for line in lines:
        draw_text(self.screen, line, 20, C["white"] if line else C["muted"], (92, y), role="body")
        y += 36

    # Menu caption.
    draw_text(self.screen, "ГЛАВНОЕ МЕНЮ", 15, C["muted"], (980, 164), center=True, bold=True, role="mono")
    for button in self.buttons:
        button.draw(self.screen)


def pixel_draw_game_topbar(self):
    bar = pygame.Rect(0, 0, W, 62)
    pygame.draw.rect(self.screen, (20, 23, 39), bar)
    pygame.draw.rect(self.screen, (255, 178, 75), (0, 59, W, 3))

    current = _parse_time(self.state.get("time", "10:00"))
    progress = max(0.0, min(1.0, (current - SHIFT_START) / (SHIFT_END - SHIFT_START)))

    draw_text(self.screen, "ПН", 13, C["muted"], (18, 9), bold=True, role="mono")
    draw_text(self.screen, self.state.get("time", "10:00"), 24, C["white"], (18, 27), bold=True, role="mono")

    pygame.draw.rect(self.screen, (59, 56, 76), (150, 28, 280, 10))
    pygame.draw.rect(self.screen, C["red2"], (150, 28, int(280 * progress), 10))
    pygame.draw.rect(self.screen, C["white"], (150, 28, 280, 10), 1)
    draw_text(self.screen, "10:00", 11, C["muted"], (150, 8), role="mono")
    draw_text(self.screen, "19:00", 11, C["muted"], (389, 8), role="mono")

    stats = [
        ("ЗАКАЗЫ", self.state.get("orders", 0), C["blue"], 465),
        ("КАССА", f"{self.state.get('money', 0)} руб.", C["white"], 590),
        ("РЕП.", f"{self.state.get('reputation', 0):+d}", C["green"], 785),
        ("СТРЕСС", self.state.get("stress", 0), C["orange"], 895),
    ]
    for label, value, color, x in stats:
        draw_text(self.screen, label, 11, C["muted"], (x, 8), bold=True, role="mono")
        draw_text(self.screen, value, 18, color, (x, 28), bold=True, role="mono")

    coffee_rect = pygame.Rect(1055, 10, 205, 40)
    hovered = coffee_rect.collidepoint(pygame.mouse.get_pos())
    pygame.draw.rect(self.screen, (92, 57, 55) if hovered else (38, 39, 52), coffee_rect)
    pygame.draw.rect(self.screen, C["red2"] if hovered else C["paper"], coffee_rect, 2)
    used = self.state.get("coffee_used", 0)
    draw_text(self.screen, f"КОФЕ {used}/{COFFEE_LIMIT} [C]", 14, C["white"], coffee_rect.center, center=True, bold=True, role="mono")


def pixel_draw_character(self):
    if not self.node.get("char"):
        return

    image = self.assets.character(self.node["char"], max_width=405, max_height=490)
    y = H - image.get_height() - 66

    # Crisp block shadow, not a blurred ellipse.
    shadow_rect = pygame.Rect(
        int(self.char_x + image.get_width() * 0.18),
        H - 95,
        int(image.get_width() * 0.66),
        17,
    )
    pygame.draw.rect(self.screen, (9, 11, 20, 125), shadow_rect)
    self.screen.blit(image, (int(self.char_x), int(y)))


def pixel_draw_game(self):
    self.screen.blit(self.assets.background(self.node["bg"]), (0, 0))
    self.assets.draw_atmosphere(self.screen, self.visual_time)
    pixel_draw_character(self)
    pixel_draw_game_topbar(self)

    if self.node.get("choices"):
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((9, 11, 25, 98))
        self.screen.blit(overlay, (0, 0))

        context = pygame.Rect(92, 86, 1096, 196)
        _pixel_box(self.screen, context, fill=(24, 27, 43), border=(255, 190, 93))

        if self.node.get("speaker"):
            draw_text(self.screen, self.node["speaker"].upper(), 15, C["red2"], (context.x + 26, context.y + 20), bold=True, role="mono")
            text_y = context.y + 58
        else:
            text_y = context.y + 30

        prompt_font = font(24, False, "body")
        for line in wrap_text(self.node["text"], context.w - 52, prompt_font):
            self.screen.blit(prompt_font.render(_safe_value(line), False, C["white"]), (context.x + 26, text_y))
            text_y += 34

        draw_text(self.screen, "ВЫБЕРИ ДЕЙСТВИЕ", 13, C["white"], (W // 2, 301), center=True, bold=True, role="mono")
        for button in self.buttons:
            button.draw(self.screen)
    else:
        rect = pygame.Rect(48, 518, 1184, 166)
        _pixel_box(self.screen, rect, fill=(24, 27, 43), border=(255, 190, 93))

        if self.node.get("speaker"):
            draw_text(self.screen, self.node["speaker"].upper(), 15, C["red2"], (rect.x + 27, rect.y + 19), bold=True, role="mono")
            y = rect.y + 55
        else:
            y = rect.y + 32

        shown = self.node["text"][: int(self.visible_chars)]
        dialogue_font = font(24, False, "body")
        for line in wrap_text(shown, rect.w - 58, dialogue_font):
            self.screen.blit(dialogue_font.render(_safe_value(line), False, C["white"]), (rect.x + 27, y))
            y += 34

        draw_text(self.screen, "ENTER / КЛИК", 12, C["muted"], (rect.right - 158, rect.bottom - 29), bold=True, role="mono")

    if self.notice_time > 0 and self.notice:
        notice_rect = pygame.Rect(W // 2 - 300, 72, 600, 46)
        _pixel_box(self.screen, notice_rect, fill=(37, 34, 48), border=C["red2"], shadow=4)
        draw_text(self.screen, self.notice, 16, C["white"], notice_rect.center, center=True, bold=True, role="body")

    current = _parse_time(self.state.get("time", "10:00"))
    progress = max(0.0, min(1.0, (current - SHIFT_START) / (SHIFT_END - SHIFT_START)))
    pygame.draw.rect(self.screen, (30, 33, 49), (0, H - 5, W, 5))
    pygame.draw.rect(self.screen, C["red2"], (0, H - 5, int(W * progress), 5))

    self.draw_transition()



Game.draw_menu = pixel_draw_menu
Game.draw_game = pixel_draw_game


def pixel_boot_loading(self):
    """Смешная псевдозагрузка перед главным меню."""
    messages = [
        (0,  "Запускаем студию..."),
        (9,  "Проверяем, пришла ли Ирина. Нет."),
        (33, "Будим принтер. Принтер сопротивляется."),
        (59, "Проверяем кофе... уровень критически низкий."),
        (71, "Иван Владимирович принимает ещё один срочный заказ..."),
        (82, "Клиент прислал макет. Макет в Word."),
        (97, "Ошибка: терпение не найдено."),
        (99, "Клиент попросил одну маленькую правку..."),
        (100, "Ладно. Работаем."),
    ]

    # Фиксированные ступени делают загрузку нарочито "подозрительной".
    checkpoints = [
        (0.00, 0),
        (1.50, 9),
        (3.00, 33),
        (4.50, 59),
        (6.00, 71),
        (7.50, 82),
        (9.00, 97),
        (10.50, 99),
        (12.00, 99),
        (13.50, 100),
    ]

    start = pygame.time.get_ticks() / 1000.0
    clock = pygame.time.Clock()
    skipped = False

    while self.running:
        now = pygame.time.get_ticks() / 1000.0
        elapsed = now - start

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
            if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_RETURN,
                pygame.K_SPACE,
                pygame.K_ESCAPE,
            ):
                if elapsed > 0.55:
                    skipped = True
            if event.type == pygame.MOUSEBUTTONDOWN and elapsed > 0.55:
                skipped = True

        if skipped:
            break

        progress = 0
        for index in range(len(checkpoints) - 1):
            t0, p0 = checkpoints[index]
            t1, p1 = checkpoints[index + 1]

            if elapsed >= t1:
                progress = p1
                continue

            if t0 <= elapsed < t1:
                # Плавно между контрольными точками, но зависаем на 99%.
                span = max(0.001, t1 - t0)
                local = (elapsed - t0) / span
                progress = int(p0 + (p1 - p0) * local)
                break

        if elapsed >= checkpoints[-1][0]:
            progress = 100

        self.screen.fill((17, 20, 33))

        # Пиксельная рамка.
        outer = pygame.Rect(115, 126, 1050, 472)
        pygame.draw.rect(self.screen, (8, 10, 18), outer.move(8, 8))
        pygame.draw.rect(self.screen, (31, 35, 53), outer)
        pygame.draw.rect(self.screen, (255, 190, 93), outer, 4)
        pygame.draw.rect(self.screen, (105, 62, 53), outer.inflate(-14, -14), 2)

        draw_text(
            self.screen,
            "ФОТОСТУДИЯ AGFA",
            42,
            C["white"],
            (W // 2, 181),
            center=True,
            bold=True,
            role="mono",
            shadow=True,
        )
        draw_text(
            self.screen,
            "ПОДГОТОВКА К РАБОЧЕМУ ДНЮ",
            17,
            C["red2"],
            (W // 2, 232),
            center=True,
            bold=True,
            role="mono",
        )

        # Выбираем текущую реплику по проценту.
        current_message = messages[0][1]
        for threshold, text in messages:
            if progress >= threshold:
                current_message = text

        msg_rect = pygame.Rect(210, 302, 860, 80)
        pygame.draw.rect(self.screen, (22, 25, 41), msg_rect)
        pygame.draw.rect(self.screen, (105, 62, 53), msg_rect, 2)

        message_font = font(22, False, "body")
        wrapped = wrap_text(current_message, msg_rect.w - 48, message_font)
        y = msg_rect.centery - (len(wrapped) * message_font.get_linesize()) // 2
        for line in wrapped:
            image = message_font.render(_safe_value(line), False, C["white"])
            self.screen.blit(
                image,
                image.get_rect(center=(msg_rect.centerx, y + message_font.get_linesize() // 2)),
            )
            y += message_font.get_linesize()

        # Прогресс-бар.
        bar = pygame.Rect(210, 416, 860, 46)
        pygame.draw.rect(self.screen, (10, 12, 22), bar)
        pygame.draw.rect(self.screen, (255, 228, 177), bar, 3)

        inner = bar.inflate(-10, -10)
        fill_width = int(inner.w * max(0, min(progress, 100)) / 100)
        if fill_width > 0:
            pygame.draw.rect(
                self.screen,
                C["red2"] if progress < 100 else C["green"],
                (inner.x, inner.y, fill_width, inner.h),
            )

        # Вертикальные пиксельные деления.
        for x in range(inner.x + 24, inner.right, 24):
            pygame.draw.line(
                self.screen,
                (31, 35, 53),
                (x, inner.y),
                (x, inner.bottom),
                2,
            )

        draw_text(
            self.screen,
            f"{progress}%",
            22,
            C["white"],
            (W // 2, 495),
            center=True,
            bold=True,
            role="mono",
        )

        if elapsed > 0.55 and progress < 100:
            draw_text(
                self.screen,
                "ENTER / КЛИК — пропустить бюрократию",
                13,
                C["muted"],
                (W // 2, 552),
                center=True,
                role="mono",
            )

        pygame.display.flip()

        if progress >= 100:
            pygame.time.delay(420)
            break

        clock.tick(60)


_original_pixel_run = Game.run


def pixel_run_with_loading(self):
    pixel_boot_loading(self)
    if self.running:
        _original_pixel_run(self)


Game.run = pixel_run_with_loading

if __name__ == "__main__":
    Game().run()
