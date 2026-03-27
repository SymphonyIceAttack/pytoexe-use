import pygame
import json
import os

# Копируем твою логику из config.py
pygame.display.init()
info = pygame.display.Info()
SCREEN_WIDTH = info.current_w
SCREEN_HEIGHT = info.current_h

if SCREEN_HEIGHT > SCREEN_WIDTH:
    SCREEN_WIDTH, SCREEN_HEIGHT = SCREEN_HEIGHT, SCREEN_WIDTH

# Настройки редактора
DEFAULT_SLOT_WIDTH = 60
DEFAULT_SLOT_HEIGHT = 60
SLOT_COLOR = (100, 100, 150)
SELECTED_COLOR = (200, 100, 100)
TEXT_COLOR = (255, 255, 255)
BG_COLOR = (30, 30, 30)
DEFAULT_FONT_SIZE = 16
SAVE_DIR = "D:/ui_redactor_pozition"  # Папка для сохранения

# Создаём папку, если её нет
os.makedirs(SAVE_DIR, exist_ok=True)

class Slot:
    def __init__(self, x, y, slot_id, width=DEFAULT_SLOT_WIDTH, height=DEFAULT_SLOT_HEIGHT, shape="rect", thickness=5):
        self.rect = pygame.Rect(x, y, width, height)
        self.id = slot_id
        self.dragging = False
        self.shape = shape
        self.thickness = thickness

    def draw(self, screen, font, selected):
        color = SELECTED_COLOR if selected else SLOT_COLOR
        center = (self.rect.centerx, self.rect.centery)
        radius = min(self.rect.width, self.rect.height) // 2
        
        if self.shape == "rect":
            pygame.draw.rect(screen, color, self.rect)
            pygame.draw.rect(screen, (200, 200, 200), self.rect, 2)
        elif self.shape == "circle":
            pygame.draw.circle(screen, color, center, radius)
            pygame.draw.circle(screen, (200, 200, 200), center, radius, 2)
        elif self.shape == "ring":
            pygame.draw.circle(screen, color, center, radius)
            inner_radius = max(1, radius - self.thickness)
            pygame.draw.circle(screen, BG_COLOR, center, inner_radius)
            pygame.draw.circle(screen, (200, 200, 200), center, radius, 2)
        
        # ID слота
        id_text = font.render(str(self.id), True, TEXT_COLOR)
        screen.blit(id_text, (self.rect.x + 5, self.rect.y + 5))
        
        # Координаты
        coord_text = font.render(f"({self.rect.x}, {self.rect.y})", True, TEXT_COLOR)
        screen.blit(coord_text, (self.rect.x + 5, self.rect.y + self.rect.height - 20))
        
        # Размеры и толщина
        if self.shape == "ring":
            size_text = font.render(f"{self.rect.width}x{self.rect.height} th:{self.thickness}", True, TEXT_COLOR)
        else:
            size_text = font.render(f"{self.rect.width}x{self.rect.height}", True, TEXT_COLOR)
        screen.blit(size_text, (self.rect.x + 5, self.rect.y + self.rect.height - 40))

class TextObject:
    def __init__(self, x, y, text_id, text="", font_size=DEFAULT_FONT_SIZE):
        self.x = x
        self.y = y
        self.id = text_id
        self.text = text
        self.font_size = font_size
        self.dragging = False

    def draw(self, screen, font, selected):
        text_font = pygame.font.Font(None, self.font_size)
        text_surf = text_font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surf.get_rect(topleft=(self.x, self.y))
        
        if selected:
            pygame.draw.rect(screen, SELECTED_COLOR, text_rect.inflate(10, 10), 2)
        
        screen.blit(text_surf, (self.x, self.y))
        
        # Координаты текста
        coord_text = font.render(f"({self.x}, {self.y})", True, TEXT_COLOR)
        screen.blit(coord_text, (self.x, self.y + text_rect.height + 5))
        
        # Размер шрифта
        size_text = font.render(f"font:{self.font_size}", True, TEXT_COLOR)
        screen.blit(size_text, (self.x, self.y + text_rect.height + 25))

def input_dialog(screen, font, prompt):
    """Диалог ввода текста. Возвращает введённую строку или None при отмене."""
    input_text = ""
    active = True
    input_rect = pygame.Rect(SCREEN_WIDTH//2 - 200, SCREEN_HEIGHT//2 - 30, 400, 40)
    bg_rect = pygame.Rect(SCREEN_WIDTH//2 - 250, SCREEN_HEIGHT//2 - 80, 500, 120)
    
    while active:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return input_text
                elif event.key == pygame.K_ESCAPE:
                    return None
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                else:
                    if event.unicode and event.unicode.isprintable():
                        input_text += event.unicode
        
        # Затемнение фона
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        # Фон диалога
        pygame.draw.rect(screen, (50, 50, 50), bg_rect)
        pygame.draw.rect(screen, (200, 200, 200), bg_rect, 2)
        
        # Текст запроса
        prompt_text = font.render(prompt, True, (255, 255, 255))
        screen.blit(prompt_text, (bg_rect.x + 10, bg_rect.y + 10))
        
        # Поле ввода
        pygame.draw.rect(screen, (80, 80, 80), input_rect)
        pygame.draw.rect(screen, (200, 200, 200), input_rect, 2)
        
        # Введённый текст
        input_surface = font.render(input_text + ("|" if (pygame.time.get_ticks() // 500) % 2 else ""), True, (255, 255, 255))
        screen.blit(input_surface, (input_rect.x + 5, input_rect.y + 5))
        
        pygame.display.flip()
        pygame.time.delay(50)

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("UI Editor - Slots & Text")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 18)
    
    slots = []
    texts = []
    next_slot_id = 1
    next_text_id = 1
    selected_type = None
    selected_index = -1
    dragging = False
    drag_offset_x = 0
    drag_offset_y = 0
    
    resize_mode = "scale"
    text_edit_mode = False
    editing_text_index = -1
    
    current_slot_width = DEFAULT_SLOT_WIDTH
    current_slot_height = DEFAULT_SLOT_HEIGHT
    current_shape = "rect"
    current_thickness = 5
    current_font_size = DEFAULT_FONT_SIZE
    
    running = True
    while running:
        screen.fill(BG_COLOR)
        
        for x in range(0, SCREEN_WIDTH, 20):
            pygame.draw.line(screen, (50, 50, 50), (x, 0), (x, SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT, 20):
            pygame.draw.line(screen, (50, 50, 50), (0, y), (SCREEN_WIDTH, y))
        
        for i, slot in enumerate(slots):
            slot.draw(screen, font, selected_type == "slot" and i == selected_index)
        
        for i, text_obj in enumerate(texts):
            text_obj.draw(screen, font, selected_type == "text" and i == selected_index)
        
        inst_lines = [
            "Клик: выбрать | Перетаскивание: двигать",
            "1: масштаб | 2: высота | 3: ширина | 4: толщина | 5: размер текста",
            "R: прямоугольник | K: круг | V: кольцо",
            "T: создать текст | Enter: редактировать выбранный текст",
            "Delete: удалить | C: создать слот | S: сохранить (с именем) | Esc: выход"
        ]
        if text_edit_mode:
            inst_lines.insert(0, "✏️ РЕДАКТИРОВАНИЕ ТЕКСТА (Enter - сохранить, Esc - отмена)")
        
        for j, line in enumerate(inst_lines):
            color = (255, 200, 100) if "РЕДАКТИРОВАНИЕ" in line else (180, 180, 180)
            text = font.render(line, True, color)
            screen.blit(text, (10, 10 + j * 20))
        
        mode_text = font.render(f"Режим: {resize_mode.upper()}", True, (180, 180, 180))
        screen.blit(mode_text, (SCREEN_WIDTH - 200, 10))
        shape_text = font.render(f"Форма: {current_shape.upper()}", True, (200, 200, 100))
        screen.blit(shape_text, (SCREEN_WIDTH - 200, 40))
        
        mx, my = pygame.mouse.get_pos()
        mouse_text = font.render(f"Mouse: ({mx}, {my})", True, (180, 180, 180))
        screen.blit(mouse_text, (SCREEN_WIDTH - 200, 70))
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.KEYDOWN:
                if text_edit_mode:
                    if event.key == pygame.K_RETURN:
                        text_edit_mode = False
                        selected_type = "text"
                        selected_index = editing_text_index
                        editing_text_index = -1
                        print("✅ Текст сохранён")
                    elif event.key == pygame.K_ESCAPE:
                        text_edit_mode = False
                        selected_type = "text"
                        selected_index = editing_text_index
                        editing_text_index = -1
                        print("❌ Редактирование отменено")
                    elif event.key == pygame.K_BACKSPACE:
                        if editing_text_index >= 0 and texts:
                            texts[editing_text_index].text = texts[editing_text_index].text[:-1]
                    else:
                        if event.unicode and event.unicode.isprintable():
                            if editing_text_index >= 0 and texts:
                                texts[editing_text_index].text += event.unicode
                else:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_1:
                        resize_mode = "scale"
                    elif event.key == pygame.K_2:
                        resize_mode = "height"
                    elif event.key == pygame.K_3:
                        resize_mode = "width"
                    elif event.key == pygame.K_4:
                        resize_mode = "thickness"
                    elif event.key == pygame.K_5:
                        resize_mode = "font_size"
                    elif event.key == pygame.K_r:
                        current_shape = "rect"
                    elif event.key == pygame.K_k:
                        current_shape = "circle"
                    elif event.key == pygame.K_v:
                        current_shape = "ring"
                    elif event.key == pygame.K_t:
                        # Создать текст
                        texts.append(TextObject(mx, my, next_text_id, "", current_font_size))
                        next_text_id += 1
                        print(f"✅ Создан текст {next_text_id-1}")
                    elif event.key == pygame.K_c:
                        slots.append(Slot(mx - current_slot_width//2, my - current_slot_height//2, next_slot_id,
                                          current_slot_width, current_slot_height, current_shape, current_thickness))
                        next_slot_id += 1
                    elif event.key == pygame.K_t:
                        texts.append(TextObject(mx, my, next_text_id, "", current_font_size))
                        next_text_id += 1
                        print(f"✅ Создан текст {next_text_id-1}")
                    elif event.key == pygame.K_s:
                        # Диалог ввода имени
                        name = input_dialog(screen, font, "Введите имя файла (без расширения):")
                        if name:
                            filename = f"{name}_slot_coords.json"
                            filepath = os.path.join(SAVE_DIR, filename)
                            data = {
                                "slots": {slot.id: {
                                    "x": slot.rect.x, "y": slot.rect.y,
                                    "width": slot.rect.width, "height": slot.rect.height,
                                    "shape": slot.shape, "thickness": slot.thickness
                                } for slot in slots},
                                "texts": {text.id: {
                                    "x": text.x, "y": text.y,
                                    "text": text.text, "font_size": text.font_size
                                } for text in texts}
                            }
                            with open(filepath, "w") as f:
                                json.dump(data, f, indent=4)
                            print(f"✅ Сохранено: {filepath}")
                    elif event.key == pygame.K_DELETE:
                        if selected_type == "slot" and selected_index >= 0 and selected_index < len(slots):
                            slots.pop(selected_index)
                            selected_index = -1
                            selected_type = None
                        elif selected_type == "text" and selected_index >= 0 and selected_index < len(texts):
                            texts.pop(selected_index)
                            selected_index = -1
                            selected_type = None
                    elif event.key == pygame.K_RETURN:
                        if selected_type == "text" and selected_index >= 0 and selected_index < len(texts):
                            text_edit_mode = True
                            editing_text_index = selected_index
                            selected_type = None
                            selected_index = -1
                            print(f"✏️ Редактируем текст {texts[editing_text_index].id}")
            
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not text_edit_mode:
                for i, slot in enumerate(slots):
                    if slot.rect.collidepoint(mx, my):
                        selected_type = "slot"
                        selected_index = i
                        dragging = True
                        drag_offset_x = slot.rect.x - mx
                        drag_offset_y = slot.rect.y - my
                        break
                else:
                    for i, text_obj in enumerate(texts):
                        text_font = pygame.font.Font(None, text_obj.font_size)
                        text_surf = text_font.render(text_obj.text, True, TEXT_COLOR)
                        text_rect = text_surf.get_rect(topleft=(text_obj.x, text_obj.y))
                        if text_rect.collidepoint(mx, my):
                            selected_type = "text"
                            selected_index = i
                            dragging = True
                            drag_offset_x = text_obj.x - mx
                            drag_offset_y = text_obj.y - my
                            break
                    else:
                        selected_type = None
                        selected_index = -1
            
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                dragging = False
            
            elif event.type == pygame.MOUSEMOTION and dragging and selected_index >= 0 and not text_edit_mode:
                if selected_type == "slot":
                    slots[selected_index].rect.x = mx + drag_offset_x
                    slots[selected_index].rect.y = my + drag_offset_y
                elif selected_type == "text":
                    texts[selected_index].x = mx + drag_offset_x
                    texts[selected_index].y = my + drag_offset_y
            
            elif event.type == pygame.MOUSEWHEEL and selected_index >= 0 and not text_edit_mode:
                delta = event.y * 5
                if selected_type == "slot":
                    slot = slots[selected_index]
                    if resize_mode == "scale":
                        new_w = slot.rect.width + delta
                        new_h = slot.rect.height + delta
                        if new_w >= 20 and new_h >= 20:
                            slot.rect.width = new_w
                            slot.rect.height = new_h
                    elif resize_mode == "width":
                        new_w = slot.rect.width + delta
                        if new_w >= 20:
                            slot.rect.width = new_w
                    elif resize_mode == "height":
                        new_h = slot.rect.height + delta
                        if new_h >= 20:
                            slot.rect.height = new_h
                    elif resize_mode == "thickness" and slot.shape == "ring":
                        new_th = slot.thickness + delta
                        if new_th >= 1 and new_th <= min(slot.rect.width, slot.rect.height) // 2:
                            slot.thickness = new_th
                elif selected_type == "text" and resize_mode == "font_size":
                    new_size = texts[selected_index].font_size + event.y
                    if new_size >= 8:
                        texts[selected_index].font_size = new_size
    
    pygame.quit()

if __name__ == "__main__":
    main()