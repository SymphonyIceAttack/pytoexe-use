import pymem
import pymem.process
import math
import time
import keyboard
import win32api
import win32con
import struct
import os

# ========== КОНФИГ ==========
AIM_FOV = 150          # Дальность аима в пикселях
AIM_KEY = 'shift'      # Клавиша для аима
ESP_COLOR = (0, 255, 0)
TRIGGER_KEY = 'ctrl'   # Клавиша для триггербота

# ========== ПОДКЛЮЧЕНИЕ К ИГРЕ (ALKAD) ==========
try:
    # Alkad использует Rust.exe, а не RustClient.exe
    pm = pymem.Pymem("Rust.exe")
    print("[Ryzen] Alkad Rust найден!")
except pymem.exception.ProcessNotFound:
    try:
        pm = pymem.Pymem("RustClient.exe")
        print("[Ryzen] RustClient.exe найден (возможно, не Alkad)")
    except:
        print("[Ryzen] Ошибка: Rust не запущен!")
        exit()

base = pymem.process.module_from_name(pm.process_handle, 
                                        pm.process_name).lpBaseOfDll

# ========== СМЕЩЕНИЯ ДЛЯ ALKAD ==========
# В пиратских сборках смещения часто сдвинуты
# Эти значения - ПРИМЕР, нужно найти актуальные через Cheat Engine
OFFSETS = {
    "LocalPlayer": 0x00FFFFFF,   # Нужно обновить!
    "EntityList": 0x00EEEEEE,    # Нужно обновить!
    "ViewMatrix": 0x00ABCDEF,    # Нужно обновить!
    "Position": 0x30,
    "Health": 0x20,
    "Name": 0x10,
    "TeamID": 0x40,
}

# ========== ФУНКЦИИ ==========
def read_vec3(addr):
    """Чтение 3D координат"""
    try:
        data = pm.read_bytes(addr, 12)
        return struct.unpack('fff', data)
    except:
        return (0, 0, 0)

def get_view_matrix():
    """Получение матрицы камеры"""
    addr = base + OFFSETS["ViewMatrix"]
    try:
        return [pm.read_float(addr + i*4) for i in range(16)]
    except:
        return [0]*16

def get_local():
    """Получение данных локального игрока"""
    try:
        lp = pm.read_int(base + OFFSETS["LocalPlayer"])
        return {
            "pos": read_vec3(lp + OFFSETS["Position"]),
            "health": pm.read_int(lp + OFFSETS["Health"])
        }
    except:
        return {"pos": (0,0,0), "health": 0}

def get_entities():
    """Получение списка всех игроков"""
    try:
        elist = pm.read_int(base + OFFSETS["EntityList"])
        entities = []
        for i in range(32):
            ent = pm.read_int(elist + i*8)
            if ent and ent > 0x10000:
                try:
                    health = pm.read_int(ent + OFFSETS["Health"])
                    if 0 < health < 100:
                        entities.append({
                            "pos": read_vec3(ent + OFFSETS["Position"]),
                            "health": health,
                            "name": pm.read_string(ent + OFFSETS["Name"], 32) or f"Player{i}"
                        })
                except:
                    pass
        return entities
    except:
        return []

def world_to_screen(pos, vm, sw=1920, sh=1080):
    """3D -> 2D проекция"""
    x, y, z = pos
    clip_x = x*vm[0] + y*vm[4] + z*vm[8] + vm[12]
    clip_y = x*vm[1] + y*vm[5] + z*vm[9] + vm[13]
    clip_w = x*vm[3] + y*vm[7] + z*vm[11] + vm[15]
    
    if clip_w < 0.01:
        return None
    
    ndc_x = clip_x / clip_w
    ndc_y = clip_y / clip_w
    
    screen_x = (sw/2 * ndc_x) + (ndc_x + sw/2)
    screen_y = (sh/2 * ndc_y) + (ndc_y + sh/2)
    
    return (int(screen_x), int(screen_y))

def draw_esp():
    """Отрисовка ESP в консоли"""
    vm = get_view_matrix()
    local = get_local()
    ents = get_entities()
    
    os.system('cls')
    print("╔══════════════════════════════════════╗")
    print(f"║ [Ryzen] ALKAD RUST CHEAT             ║")
    print(f"║ Здоровье: {local['health']}                      ║")
    print(f"║ Игроков: {len(ents)}                           ║")
    print("╠══════════════════════════════════════╣")
    
    for e in ents:
        dx = e['pos'][0] - local['pos'][0]
        dz = e['pos'][2] - local['pos'][2]
        dist = int((dx*dx + dz*dz)**0.5)
        
        screen = world_to_screen(e['pos'], vm)
        if screen:
            print(f"║ 🎯 {e['name'][:12]:12} HP:{e['health']:3} {dist:4}м  ({screen[0]:4},{screen[1]:4}) ║")
    
    print("╚══════════════════════════════════════╝")
    print("Управление: SHIFT - аим | CTRL - триггер | END - выход")

def get_screen_center():
    return (1920//2, 1080//2)

def aim_at_target(target_screen_pos):
    """Наведение на цель"""
    center = get_screen_center()
    dx = target_screen_pos[0] - center[0]
    dy = target_screen_pos[1] - center[1]
    
    if abs(dx) > AIM_FOV or abs(dy) > AIM_FOV:
        return False
    
    # Плавное наведение
    win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, int(dx/4), int(dy/4), 0, 0)
    return True

def triggerbot(target_screen_pos):
    """Авто-выстрел при наведении"""
    center = get_screen_center()
    dx = abs(target_screen_pos[0] - center[0])
    dy = abs(target_screen_pos[1] - center[1])
    
    if dx < 15 and dy < 15:
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.02)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        return True
    return False

# ========== ГЛАВНЫЙ ЦИКЛ ==========
print("[Ryzen] Alkad чит запущен")
print("Поиск смещений...")
print("Если ничего не отображается - смещения неверные!")
print("Нужно найти актуальные через Cheat Engine")
time.sleep(2)

while True:
    if keyboard.is_pressed('end'):
        print("Выключение...")
        break
    
    draw_esp()
    
    vm = get_view_matrix()
    local = get_local()
    best_target = None
    best_dist = AIM_FOV
    
    # Поиск ближайшей цели
    for e in get_entities():
        screen = world_to_screen(e['pos'], vm)
        if screen:
            center = get_screen_center()
            dist = ((screen[0]-center[0])**2 + (screen[1]-center[1])**2)**0.5
            if dist < best_dist:
                best_dist = dist
                best_target = screen
    
    # Aimbot
    if keyboard.is_pressed(AIM_KEY) and best_target:
        aim_at_target(best_target)
    
    # Triggerbot
    if keyboard.is_pressed(TRIGGER_KEY) and best_target:
        triggerbot(best_target)
    
    time.sleep(0.05)