import pygame
import sys
import random
import math

# ��ʼ�� Pygame
pygame.init()

# --- ���� ---
SCREEN_WIDTH, SCREEN_HEIGHT = 1920, 1080  # ������Ļ�ߴ�
PET_IMAGE_NAME = "cat.png"  # ��ȷ��ͼƬ��һ��
INITIAL_SCALE = 0.5
MIN_SCALE = 0.2
MAX_SCALE = 2.0
FPS = 60

# --- ��ɫ���� ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BUBBLE_COLOR = (255, 255, 255, 230)  # ��͸����ɫ����

# --- ȫ�ֱ��� ---
screen = None
clock = None
pet_image_original = None
topmost = True

# --- �Ի��� ---
SPEECHES = [
    "��~", "���Ҹ��", "����ͷ��", "����...", 
    "�������~", "�����˷���", "�㵲��̫����", 
    "����С��ɣ�", "Zzz...", "��ʲô��~"
]

class DesktopPet:
    def __init__(self):
        global pet_image_original
        try:
            pet_image_original = pygame.image.load(PET_IMAGE_NAME).convert_alpha()
        except pygame.error:
            # ����Ҳ���ͼƬ��������ɫ�ķ���ռλ
            pet_image_original = pygame.Surface((100, 100), pygame.SRCALPHA)
            pygame.draw.rect(pet_image_original, (255, 0, 0, 200), (0, 0, 100, 100))
            pygame.draw.line(pet_image_original, BLACK, (0, 0), (100, 100), 3)
            pygame.draw.line(pet_image_original, BLACK, (100, 0), (0, 100), 3)

        self.scale = INITIAL_SCALE
        self.image = self._scale_image()
        self.rect = self.image.get_rect()
        
        # ��ʼλ�ã���Ļ���½ǣ�
        self.rect.x = SCREEN_WIDTH - self.rect.width - 50
        self.rect.y = SCREEN_HEIGHT - self.rect.height - 50
        
        # ����״̬
        self.dragging = False
        self.drag_offset = (0, 0)
        
        # ����״̬
        self.state = "idle"  # idle, jump, squish, shake
        self.anim_frame = 0
        self.base_y = self.rect.y
        self.velocity_y = 0
        
        # ����
        self.speech_text = ""
        self.show_speech = False
        self.speech_timer = 0

    def _scale_image(self):
        """���ݵ�ǰ���ű�������ͼƬ"""
        w = int(pet_image_original.get_width() * self.scale)
        h = int(pet_image_original.get_height() * self.scale)
        return pygame.transform.smoothscale(pet_image_original, (w, h))

    def handle_event(self, event):
        global topmost
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # ���
                if self.rect.collidepoint(event.pos):
                    self.dragging = True
                    self.drag_offset = (self.rect.x - event.pos[0], self.rect.y - event.pos[1])
                    self._trigger_interaction()
            
            elif event.button == 4:  # ������
                self.scale = min(self.scale * 1.08, MAX_SCALE)
                self.image = self._scale_image()
                self.rect.width = self.image.get_width()
                self.rect.height = self.image.get_height()
            
            elif event.button == 5:  # ������
                self.scale = max(self.scale * 0.92, MIN_SCALE)
                self.image = self._scale_image()
                self.rect.width = self.image.get_width()
                self.rect.height = self.image.get_height()

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_t:  # T���л��ö�
                topmost = not topmost
                pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.NOFRAME)
                self._set_topmost(topmost)
            elif event.key == pygame.K_ESCAPE:  # ESC�˳�
                pygame.quit()
                sys.exit()

    def _trigger_interaction(self):
        """�������������ͶԻ�"""
        self.state = random.choice(["jump", "squish", "shake"])
        self.anim_frame = 0
        self.speech_text = random.choice(SPEECHES)
        self.show_speech = True
        self.speech_timer = FPS * 2  # ��ʾ2��
        
        if self.state == "jump":
            self.velocity_y = -18
            self.base_y = self.rect.y

    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        
        # �϶��߼�
        if self.dragging:
            self.rect.x = mouse_pos[0] + self.drag_offset[0]
            self.rect.y = mouse_pos[1] + self.drag_offset[1]
            self.base_y = self.rect.y
        
        # �����߼�
        if self.state == "jump":
            self.velocity_y += 0.8  # ����
            self.rect.y += self.velocity_y
            if self.rect.y > self.base_y:
                self.rect.y = self.base_y
                self.state = "idle"
        elif self.state == "squish":
            self.anim_frame += 1
            if self.anim_frame > 15:
                self.state = "idle"
        elif self.state == "shake":
            self.anim_frame += 1
            if self.anim_frame > 20:
                self.state = "idle"

        # ���ݼ�ʱ
        if self.show_speech:
            self.speech_timer -= 1
            if self.speech_timer <= 0:
                self.show_speech = False

    def draw(self, surface):
        # ����״̬���Ƴ���
        draw_image = self.image.copy()
        
        if self.state == "squish":
            # ѹ��Ч��
            squish_h = int(draw_image.get_height() * 0.7)
            draw_image = pygame.transform.scale(draw_image, (draw_image.get_width(), squish_h))
            surface.blit(draw_image, (self.rect.x, self.rect.y + (self.image.get_height() - squish_h)))
        elif self.state == "shake":
            # ����Ч��
            offset_x = random.randint(-3, 3)
            offset_y = random.randint(-2, 2)
            surface.blit(draw_image, (self.rect.x + offset_x, self.rect.y + offset_y))
        else:
            surface.blit(draw_image, self.rect)

        # ��������
        if self.show_speech:
            self._draw_speech_bubble(surface)

    def _draw_speech_bubble(self, surface):
        font = pygame.font.SysFont("simhei", 20)
        text_surf = font.render(self.speech_text, True, BLACK)
        padding = 12
        bubble_w = text_surf.get_width() + padding * 2
        bubble_h = text_surf.get_height() + padding * 2
        
        # ����λ�ã�ͷ��ƫ�ң�
        bubble_x = self.rect.centerx - bubble_w // 2
        bubble_y = self.rect.top - bubble_h - 10
        
        # ��ֹ���ݷɳ���Ļ����
        if bubble_y < 0:
            bubble_y = self.rect.bottom + 10
        
        # ����Բ�Ǿ�������
        bubble_rect = pygame.Rect(bubble_x, bubble_y, bubble_w, bubble_h)
        pygame.draw.rect(surface, BUBBLE_COLOR, bubble_rect, border_radius=10)
        pygame.draw.rect(surface, BLACK, bubble_rect, 2, border_radius=10)
        
        # ����С����
        tip_points = [
            (self.rect.centerx, self.rect.top if bubble_y < self.rect.top else self.rect.bottom),
            (self.rect.centerx - 8, bubble_y + bubble_h // 2),
            (self.rect.centerx + 8, bubble_y + bubble_h // 2)
        ]
        pygame.draw.polygon(surface, BUBBLE_COLOR, tip_points)
        pygame.draw.polygon(surface, BLACK, tip_points, 2)
        
        surface.blit(text_surf, (bubble_x + padding, bubble_y + padding))

    def _set_topmost(self, enable):
        """�������ô����ö�������Windows��"""
        if sys.platform == 'win32':
            import ctypes
            hwnd = pygame.display.get_wm_info()['window']
            flags = ctypes.windll.user32.GetWindowLongPtrW(hwnd, -16)  # GWL_STYLE
            if enable:
                flags |= 0x00000008  # WS_EX_TOPMOST
            else:
                flags &= ~0x00000008
            ctypes.windll.user32.SetWindowLongPtrW(hwnd, -16, flags)
            ctypes.windll.user32.SetWindowPos(hwnd, -1 if enable else -2, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040)


def main():
    global screen, clock, topmost
    
    # �����ޱ߿�͸�����ֲ㴰��
    os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"
    
    # ����ȫ��͸���ı���
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.NOFRAME | pygame.SRCALPHA)
    pygame.display.set_caption("Desktop Pet")
    
    # ���ô���Ϊ͸��ɫ����ɫ����͸������
    if sys.platform == 'win32':
        import ctypes
        hwnd = pygame.display.get_wm_info()['window']
        # ���ô�����չ��ʽΪ�ֲ㴰�ڣ�Layered Window��
        ctypes.windll.user32.SetWindowLongPtrW(hwnd, -20, 0x00080000)  # GWL_EXSTYLE, WS_EX_LAYERED
        # ����͸���ȣ�0=ȫ͸����255=��͸����
        ctypes.windll.user32.SetLayeredWindowAttributes(hwnd, 0x00000000, 255, 0x02)  # LWA_COLORKEY
        # �����ö�
        ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040)  # SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE

    clock = pygame.time.Clock()
    pet = DesktopPet()
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            pet.handle_event(event)

        pet.update()
        
        # ���͸��ɫ�����룬������в�Ӱ��
        screen.fill((0, 0, 0, 0))  # RGBA, Alpha=0 ��ʾ��ȫ͸��
        
        pet.draw(screen)
        
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()