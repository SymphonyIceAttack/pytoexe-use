#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Безоконный лаунчер для рабочего стола Windows.
Отображает все ярлыки (.lnk) с рабочего стола в виде прокручиваемого списка.
Запуск выбранного ярлыка – клавиша Enter, выход – Esc.
Дополнительно: клик мыши для выбора, колёсико для прокрутки.
"""

import sys
import os
import glob
import ctypes
import pygame

# --- Скрыть консольное окно на Windows (эффект "без окон") ---
if sys.platform == 'win32':
    try:
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except Exception:
        pass

# --- Настройки интерфейса ---
BACKGROUND_COLOR = (0, 0, 0)          # чёрный фон
TEXT_COLOR = (255, 255, 255)          # белый текст
SELECTION_COLOR = (70, 130, 200)      # подсветка выбранного элемента
SELECTION_BORDER_COLOR = (255, 215, 0) # золотая рамка
TITLE_COLOR = (100, 200, 255)         # голубой цвет заголовка
HELP_COLOR = (180, 180, 180)          # серый для подсказок

FONT_SIZE = 32
LINE_PADDING = 10                     # отступ между строками
TITLE_HEIGHT = 80
HELP_HEIGHT = 60
SCROLL_SPEED = 3                      # строк на прокрутку колёсиком


def get_desktop_path():
    """Возвращает путь к папке рабочего стола текущего пользователя."""
    # Стандартный способ – работает для всех локализаций (фактический путь Desktop)
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    if os.path.isdir(desktop):
        return desktop
    # Альтернативный способ через переменную окружения
    alt = os.environ.get("USERPROFILE", "")
    if alt:
        alt_desktop = os.path.join(alt, "Desktop")
        if os.path.isdir(alt_desktop):
            return alt_desktop
    raise RuntimeError("Не удалось найти папку рабочего стола.")


def collect_shortcuts(desktop_path):
    """Возвращает список кортежей (полный_путь_к_lnk, отображаемое_имя)."""
    items = []
    lnk_files = glob.glob(os.path.join(desktop_path, "*.lnk"))
    for lnk in lnk_files:
        name = os.path.splitext(os.path.basename(lnk))[0]
        items.append((lnk, name))
    # Сортируем по имени ярлыка
    items.sort(key=lambda x: x[1].lower())
    return items


def draw_ui(screen, font, items, current_idx, scroll_offset, max_visible):
    """
    Отрисовывает весь интерфейс:
    - заголовок
    - список ярлыков с прокруткой
    - подсказки
    """
    screen.fill(BACKGROUND_COLOR)
    width, height = screen.get_size()

    # --- Заголовок ---
    title_surf = font.render("★ ЛАУНЧЕР ЯРЛЫКОВ ★", True, TITLE_COLOR)
    title_rect = title_surf.get_rect(center=(width // 2, TITLE_HEIGHT // 2))
    screen.blit(title_surf, title_rect)

    # --- Рисуем список ---
    start_y = TITLE_HEIGHT + 20
    line_height = FONT_SIZE + LINE_PADDING
    # Ограничиваем отображаемые индексы
    visible_items = items[scroll_offset:scroll_offset + max_visible]

    for i, (_, display_name) in enumerate(visible_items):
        y = start_y + i * line_height
        # Проверяем, выбран ли этот элемент
        is_selected = (scroll_offset + i == current_idx)
        text_surf = font.render(display_name, True, TEXT_COLOR)
        text_rect = text_surf.get_rect(topleft=(50, y))

        if is_selected:
            # Рисуем прямоугольник подсветки
            padding = 10
            rect_width = width - 100
            rect_height = line_height
            rect_x = 50 - padding // 2
            rect_y = y - (line_height - FONT_SIZE) // 2 - 2
            selection_rect = pygame.Rect(rect_x, rect_y, rect_width, rect_height)
            pygame.draw.rect(screen, SELECTION_COLOR, selection_rect, border_radius=8)
            pygame.draw.rect(screen, SELECTION_BORDER_COLOR, selection_rect, width=2, border_radius=8)
        screen.blit(text_surf, text_rect)

    # --- Подсказки внизу ---
    help_y = height - HELP_HEIGHT
    controls = [
        "↑/↓ / Колёсико: навигация",
        "Enter: запуск ярлыка",
        "R: обновить список",
        "Esc: выход"
    ]
    help_font = pygame.font.SysFont(None, int(FONT_SIZE * 0.7))
    for i, line in enumerate(controls):
        help_surf = help_font.render(line, True, HELP_COLOR)
        help_rect = help_surf.get_rect(topleft=(30, help_y + i * 25))
        screen.blit(help_surf, help_rect)

    # Если ярлыков нет – выводим сообщение
    if not items:
        msg_font = pygame.font.SysFont(None, FONT_SIZE)
        msg = msg_font.render("Нет ярлыков (*.lnk) на рабочем столе", True, (255, 100, 100))
        msg_rect = msg.get_rect(center=(width // 2, height // 2))
        screen.blit(msg, msg_rect)

    pygame.display.flip()


def main():
    # Инициализация pygame
    pygame.init()
    # Полноэкранный режим (без оконных рамок)
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("Desktop Launcher")
    clock = pygame.time.Clock()

    # Шрифт
    try:
        font = pygame.font.SysFont("segoeui", FONT_SIZE)  # предпочтительный шрифт Windows
    except:
        font = pygame.font.SysFont(None, FONT_SIZE)

    # Получаем путь к рабочему столу и список ярлыков
    try:
        desktop_path = get_desktop_path()
        shortcuts = collect_shortcuts(desktop_path)
    except Exception as e:
        print(f"Ошибка доступа к рабочему столу: {e}")
        shortcuts = []

    # Переменные состояния
    current_idx = 0 if shortcuts else -1
    scroll_offset = 0
    running = True

    # Параметры отображения списка
    screen_height = screen.get_height()
    line_height = FONT_SIZE + LINE_PADDING
    max_visible = (screen_height - TITLE_HEIGHT - HELP_HEIGHT - 40) // line_height
    if max_visible < 1:
        max_visible = 1

    def refresh_shortcuts():
        """Перечитывает ярлыки с рабочего стола."""
        nonlocal shortcuts, current_idx, scroll_offset
        try:
            new_items = collect_shortcuts(desktop_path)
            shortcuts = new_items
            if shortcuts:
                if current_idx >= len(shortcuts):
                    current_idx = len(shortcuts) - 1
                if current_idx < 0:
                    current_idx = 0
            else:
                current_idx = -1
            # Корректируем scroll_offset, чтобы выбранный элемент был виден
            if current_idx < scroll_offset:
                scroll_offset = current_idx
            elif current_idx >= scroll_offset + max_visible:
                scroll_offset = current_idx - max_visible + 1
            if scroll_offset < 0:
                scroll_offset = 0
        except Exception as e:
            print(f"Ошибка обновления: {e}")

    def launch_selected():
        """Запускает выбранный ярлык через os.startfile."""
        if shortcuts and 0 <= current_idx < len(shortcuts):
            lnk_path = shortcuts[current_idx][0]
            try:
                os.startfile(lnk_path)
            except Exception as e:
                # Визуально сообщим об ошибке (выведем на экран на секунду)
                err_font = pygame.font.SysFont(None, 40)
                err_msg = err_font.render(f"Ошибка запуска: {e}", True, (255, 100, 100))
                err_rect = err_msg.get_rect(center=(screen.get_width() // 2, screen.get_height() - 40))
                screen.blit(err_msg, err_rect)
                pygame.display.flip()
                pygame.time.wait(800)

    # Основной цикл
    while running:
        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_UP:
                    if shortcuts and current_idx > 0:
                        current_idx -= 1
                        if current_idx < scroll_offset:
                            scroll_offset = current_idx
                elif event.key == pygame.K_DOWN:
                    if shortcuts and current_idx < len(shortcuts) - 1:
                        current_idx += 1
                        if current_idx >= scroll_offset + max_visible:
                            scroll_offset = current_idx - max_visible + 1
                elif event.key == pygame.K_PAGEUP:
                    if shortcuts:
                        current_idx = max(0, current_idx - max_visible)
                        if current_idx < scroll_offset:
                            scroll_offset = current_idx
                elif event.key == pygame.K_PAGEDOWN:
                    if shortcuts:
                        current_idx = min(len(shortcuts) - 1, current_idx + max_visible)
                        if current_idx >= scroll_offset + max_visible:
                            scroll_offset = current_idx - max_visible + 1
                elif event.key == pygame.K_HOME:
                    if shortcuts:
                        current_idx = 0
                        scroll_offset = 0
                elif event.key == pygame.K_END:
                    if shortcuts:
                        current_idx = len(shortcuts) - 1
                        scroll_offset = max(0, len(shortcuts) - max_visible)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    launch_selected()
                elif event.key == pygame.K_r or event.key == pygame.K_R:
                    refresh_shortcuts()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # левая кнопка – выбор элемента
                    mouse_x, mouse_y = event.pos
                    # Определяем, на какой элемент списка попал курсор
                    start_y = TITLE_HEIGHT + 20
                    for i in range(max_visible):
                        if scroll_offset + i >= len(shortcuts):
                            break
                        y_rect = start_y + i * line_height
                        # Область клика по строке (расширенная)
                        rect = pygame.Rect(40, y_rect - 10, screen.get_width() - 80, line_height)
                        if rect.collidepoint(mouse_x, mouse_y):
                            current_idx = scroll_offset + i
                            break
                elif event.button == 4:  # колёсико вверх
                    if shortcuts and current_idx > 0:
                        delta = max(1, min(SCROLL_SPEED, current_idx))
                        current_idx = max(0, current_idx - delta)
                        if current_idx < scroll_offset:
                            scroll_offset = max(0, current_idx)
                elif event.button == 5:  # колёсико вниз
                    if shortcuts and current_idx < len(shortcuts) - 1:
                        delta = max(1, min(SCROLL_SPEED, len(shortcuts) - 1 - current_idx))
                        current_idx = min(len(shortcuts) - 1, current_idx + delta)
                        if current_idx >= scroll_offset + max_visible:
                            scroll_offset = min(len(shortcuts) - max_visible, current_idx - max_visible + 1)
            # Поддержка pygame 2+ MOUSEWHEEL events (более новое API)
            elif event.type == pygame.MOUSEWHEEL:
                if shortcuts:
                    delta = event.y  # +1 вверх, -1 вниз
                    if delta > 0:  # вверх
                        current_idx = max(0, current_idx - SCROLL_SPEED)
                        if current_idx < scroll_offset:
                            scroll_offset = max(0, current_idx)
                    elif delta < 0:  # вниз
                        current_idx = min(len(shortcuts) - 1, current_idx + SCROLL_SPEED)
                        if current_idx >= scroll_offset + max_visible:
                            scroll_offset = min(len(shortcuts) - max_visible, current_idx - max_visible + 1)

        # Ограничиваем scroll_offset допустимыми границами
        if shortcuts:
            max_offset = max(0, len(shortcuts) - max_visible)
            scroll_offset = max(0, min(scroll_offset, max_offset))
            # Синхронизация, если current_idx вне видимости
            if current_idx < scroll_offset:
                scroll_offset = current_idx
            elif current_idx >= scroll_offset + max_visible:
                scroll_offset = current_idx - max_visible + 1
            scroll_offset = max(0, min(scroll_offset, max_offset))

        # Отрисовка
        draw_ui(screen, font, shortcuts, current_idx, scroll_offset, max_visible)
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()