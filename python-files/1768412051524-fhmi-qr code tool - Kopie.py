import pygame
import qrcode
import sys
from io import BytesIO
import pyperclip
import os

pygame.init()

# ---------------- Window ----------------
WIDTH, HEIGHT = 740, 640
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("QR Code Generator")

# ---------------- Fonts ----------------
font = pygame.font.SysFont(None, 28)
big_font = pygame.font.SysFont(None, 36)

# ---------------- Colors ----------------
WHITE = (255, 255, 255)
GRAY = (160, 160, 160)
GREEN = (80, 200, 120)

# ---------------- Images ----------------
script_dir = os.path.dirname(os.path.abspath(__file__))
background_image_path = os.path.join(script_dir, "background-gradient-lights.jpg")
bg_image = pygame.image.load(background_image_path).convert()
bg_image = pygame.transform.smoothscale(bg_image, (WIDTH, HEIGHT))

# ---------------- QR Settings ----------------
QR_SIZE = 320
qr_target_pos = (210, 230)  # final QR position
qr_current_y = HEIGHT  # start off-screen at bottom
qr_surface = None
qr_animation_speed = 600  # pixels per second

# ---------------- Input Box ----------------
input_rect = pygame.Rect(50, 95, 640, 46)
active = False
text = ""
cursor_pos = 0
scroll_x = 0
cursor_visible = True
cursor_timer = 0
BLINK_SPEED = 0.5

# ---------------- Buttons ----------------
clear_btn = pygame.Rect(50, 155, 120, 36)

# ---------------- Status ----------------
status_msg = "Click box → type or paste link → ENTER"
status_color = GRAY

clock = pygame.time.Clock()

# ---------------- QR Generator ----------------
def generate_qr(data):
    """Generate smooth QR code surface."""
    global status_msg, status_color
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=20,
        border=4
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    surface = pygame.image.load(buffer).convert_alpha()
    surface = pygame.transform.smoothscale(surface, (QR_SIZE, QR_SIZE))

    status_msg = "QR code generated"
    status_color = GREEN
    return surface

# ---------------- Main Loop ----------------
running = True
while running:
    dt = clock.tick(60) / 1000  # delta time in seconds

    # --- Draw background ---
    screen.blit(bg_image, (0, 0))

    # --- Cursor blink ---
    cursor_timer += dt
    if cursor_timer >= BLINK_SPEED:
        cursor_visible = not cursor_visible
        cursor_timer = 0

    # --- Events ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            active = input_rect.collidepoint(event.pos)
            if clear_btn.collidepoint(event.pos):
                text = ""
                cursor_pos = 0
                qr_surface = None
                qr_current_y = HEIGHT
                status_msg = "Cleared"
                status_color = GRAY

        if event.type == pygame.KEYDOWN and active:
            if event.key == pygame.K_RETURN and text.strip():
                qr_surface = generate_qr(text.strip())
                qr_current_y = HEIGHT  # start animation from bottom
            elif event.key == pygame.K_BACKSPACE:
                if cursor_pos > 0:
                    text = text[:cursor_pos-1] + text[cursor_pos:]
                    cursor_pos -= 1
            elif event.key == pygame.K_DELETE:
                if cursor_pos < len(text):
                    text = text[:cursor_pos] + text[cursor_pos+1:]
            elif event.key == pygame.K_LEFT:
                cursor_pos = max(0, cursor_pos - 1)
            elif event.key == pygame.K_RIGHT:
                cursor_pos = min(len(text), cursor_pos + 1)
            elif event.key == pygame.K_v and pygame.key.get_mods() & pygame.KMOD_CTRL:
                paste = pyperclip.paste()
                text = text[:cursor_pos] + paste + text[cursor_pos:]
                cursor_pos += len(paste)
            else:
                if event.unicode and len(event.unicode) == 1:
                    text = text[:cursor_pos] + event.unicode + text[cursor_pos:]
                    cursor_pos += 1

    # --- Title ---
    screen.blit(big_font.render("QR Code Generator", True, WHITE), (50, 40))

    # --- Input Box ---
    pygame.draw.rect(
        screen,
        (110, 170, 255) if active else (200, 200, 200),
        input_rect,
        2,
        border_radius=6
    )

    # --- Render Text ---
    before_cursor = font.render(text[:cursor_pos], True, WHITE)
    full_text = font.render(text, True, WHITE)
    max_width = input_rect.width - 20

    if before_cursor.get_width() - scroll_x > max_width:
        scroll_x = before_cursor.get_width() - max_width
    elif before_cursor.get_width() - scroll_x < 0:
        scroll_x = before_cursor.get_width()

    screen.blit(
        full_text,
        (input_rect.x + 10 - scroll_x, input_rect.y + 12)
    )

    # --- Caret ---
    if active and cursor_visible:
        caret_x = input_rect.x + 10 + before_cursor.get_width() - scroll_x
        pygame.draw.line(
            screen,
            WHITE,
            (caret_x, input_rect.y + 10),
            (caret_x, input_rect.y + 36),
            2
        )

    # --- Clear Button ---
    pygame.draw.rect(screen, (80, 80, 80), clear_btn)
    screen.blit(font.render("Clear", True, WHITE),
                (clear_btn.x + 32, clear_btn.y + 8))

    # --- Status ---
    screen.blit(font.render(status_msg, True, status_color), (200, 160))

    # --- Animate QR Code ---
    if qr_surface:
        # Move QR code upwards smoothly
        if qr_current_y > qr_target_pos[1]:
            qr_current_y -= qr_animation_speed * dt
            if qr_current_y < qr_target_pos[1]:
                qr_current_y = qr_target_pos[1]
        screen.blit(qr_surface, (qr_target_pos[0], int(qr_current_y)))

    pygame.display.flip()

pygame.quit()
sys.exit()
