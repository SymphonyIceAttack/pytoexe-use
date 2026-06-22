from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController

app = Ursina(vsync=True)
window.fps_counter.enabled = True

# ========== СОЗДАЕМ ИГРОКА С ВОЗМОЖНОСТЬЮ СМЕНЫ ВИДА ==========
player = FirstPersonController()
player.camera_pov = 'first'  # 'first' или 'third'

# Сохраняем оригинальную позицию камеры
original_camera_pos = camera.position
original_camera_rotation = camera.rotation

Sky()

blocks = {}
doors = {}
world_size = 10

class Block(Button):
    def __init__(self, pos):
        super().__init__(
            parent=scene,
            position=pos,
            model='cube',
            texture='grass.png',
            color=color.white,
            collider='box'
        )
        self.pos = pos
        blocks[pos] = self
    
    def input(self, key):
        if self.hovered:
            if key == 'left mouse down':
                p = (round(self.x + mouse.normal[0]), 
                     round(self.y + mouse.normal[1]), 
                     round(self.z + mouse.normal[2]))
                if p not in blocks and p not in doors:
                    Block(p)
            if key == 'right mouse down':
                blocks.pop(self.pos, None)
                destroy(self)

class Door:
    def __init__(self, pos):
        self.pos = pos
        self.is_open = False
        
        self.bottom = Button(
            parent=scene,
            position=pos,
            model='cube',
            texture='white_cube',
            color=color.rgb(139, 69, 19),
            collider='box',
            scale=(1, 1, 0.2)
        )
        
        self.top = Button(
            parent=scene,
            position=(pos[0], pos[1] + 1, pos[2]),
            model='cube',
            texture='white_cube',
            color=color.rgb(139, 69, 19),
            collider='box',
            scale=(1, 1, 0.2)
        )
        
        self.wall = Entity(
            parent=scene,
            position=(pos[0], pos[1] + 0.5, pos[2]),
            model='cube',
            collider='box',
            visible=False,
            scale=(1, 1, 0.1)
        )
        
        self.handle = Entity(
            parent=self.top,
            model='sphere',
            color=color.yellow,
            position=(0.4, 0, 0.15),
            scale=0.08
        )
        
        doors[pos] = self
    
    def toggle(self):
        self.is_open = not self.is_open
        
        if self.is_open:
            self.bottom.rotation_y = 90
            self.top.rotation_y = 90
            self.wall.enabled = False
            self.bottom.color = color.rgb(180, 120, 80)
            self.top.color = color.rgb(180, 120, 80)
            print("Дверь открыта 🚪")
        else:
            self.bottom.rotation_y = 0
            self.top.rotation_y = 0
            self.wall.enabled = True
            self.bottom.color = color.rgb(139, 69, 19)
            self.top.color = color.rgb(139, 69, 19)
            print("Дверь закрыта 🚪")
    
    def remove(self):
        destroy(self.bottom)
        destroy(self.top)
        destroy(self.handle)
        destroy(self.wall)
        doors.pop(self.pos, None)

# ========== СОЗДАЕМ МИР ==========
print("Создание мира...")
for x in range(world_size):
    for z in range(world_size):
        Block((x, 0, z))

# Тестовые двери
Door((5, 1, 5))
Door((7, 1, 5))

print("\n=== УПРАВЛЕНИЕ ===")
print("WASD - движение")
print("Мышь - осмотр")
print("V - переключить вид (1-е/3-е лицо)")
print("F - открыть/закрыть дверь")
print("E - режим двери")
print("ЛКМ - поставить блок")
print("ПКМ - убрать блок")

door_mode = False
third_person = False

def input(key):
    global door_mode, third_person
    
    # ========== ПЕРЕКЛЮЧЕНИЕ ВИДА ==========
    if key == 'v':
        third_person = not third_person
        
        if third_person:
            # Вид от третьего лица
            camera.parent = player
            camera.position = (0, 3, -8)  # Сзади и сверху
            camera.rotation = (15, 0, 0)   # Немного сверху
            player.cursor.visible = False
            mouse.locked = False
            print("👤 Вид от третьего лица")
        else:
            # Вид от первого лица
            camera.parent = player
            camera.position = (0, 1.8, 0)  # На уровне глаз
            camera.rotation = (0, 0, 0)
            player.cursor.visible = True
            mouse.locked = True
            print("👁️ Вид от первого лица")
    
    # ========== ОТКРЫТИЕ ДВЕРИ ==========
    if key == 'f' and mouse.hovered_entity:
        for door_pos, door in list(doors.items()):
            if mouse.hovered_entity in [door.bottom, door.top, door.handle, door.wall]:
                door.toggle()
                break
    
    # ========== РЕЖИМ ДВЕРИ ==========
    if key == 'e':
        door_mode = not door_mode
        print(f"Режим двери: {'ВКЛ' if door_mode else 'ВЫКЛ'}")
    
    if door_mode and mouse.hovered_entity:
        if key == 'left mouse down':
            if mouse.hovered_entity in blocks.values():
                pos = mouse.hovered_entity.position
                door_pos = (round(pos[0]), round(pos[1] + 1), round(pos[2]))
                if (pos not in doors and door_pos not in doors and 
                    pos not in blocks and door_pos not in blocks):
                    Door(pos)
                    print("Дверь поставлена! 🚪")
        
        if key == 'right mouse down':
            for door_pos, door in list(doors.items()):
                if mouse.hovered_entity in [door.bottom, door.top, door.handle, door.wall]:
                    door.remove()
                    print("Дверь убрана! 🚪")
                    break

# ========== ОПТИМИЗАЦИЯ ==========
camera.clip_plane_far = 50
from panda3d.core import AntialiasAttrib
base.render.set_antialias(AntialiasAttrib.MNone)

def update():
    p = player.position
    
    # Скрываем дальние блоки
    for pos, block in list(blocks.items()):
        dist = (pos[0]-p[0])**2 + (pos[2]-p[2])**2
        block.visible = dist < 400
    
    # Скрываем дальние двери
    for pos, door in list(doors.items()):
        dist = (pos[0]-p[0])**2 + (pos[2]-p[2])**2
        door.bottom.visible = dist < 400
        door.top.visible = dist < 400
        door.handle.visible = dist < 400
    
    # Если вид от третьего лица - камера следит за игроком
    if third_person:
        # Плавное слежение
        camera.position = player.position + (0, 3, -8)
        camera.look_at(player.position + (0, 1, 0))

app.run()