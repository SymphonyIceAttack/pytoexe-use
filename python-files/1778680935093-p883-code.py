# =========================================================
# УСТАНОВКА ЗАВИСИМОСТЕЙ:
# pip install pygame pygame_gui pyperclip
# =========================================================

import pygame
import pygame_gui
import json
import os
import sys
import string
import secrets
import pyperclip

# =========================================================
# НАСТРОЙКИ
# =========================================================

WIDTH = 800
HEIGHT = 500

pygame.init()

# JSON рядом с EXE
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

JSON_FILE = os.path.join(BASE_DIR, "passwords.json")

# =========================================================
# ГЕНЕРАТОР ПАРОЛЕЙ
# =========================================================

class PasswordGenerator:

    @staticmethod
    def generate(length=16):

        chars = (
            string.ascii_letters +
            string.digits +
            "!@#$%^&*()-_=+[]{}<>?"
        )

        while True:

            password = ''.join(
                secrets.choice(chars)
                for _ in range(length)
            )

            if (
                any(c.islower() for c in password) and
                any(c.isupper() for c in password) and
                any(c.isdigit() for c in password) and
                any(c in "!@#$%^&*()-_=+[]{}<>?" for c in password)
            ):
                return password


# =========================================================
# ХРАНИЛИЩЕ JSON
# =========================================================

class PasswordStorage:

    def __init__(self, filename):

        self.filename = filename
        self.data = {}

        self.load()

    def load(self):

        if not os.path.exists(self.filename):

            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump({}, f)

        try:

            with open(self.filename, "r", encoding="utf-8") as f:
                self.data = json.load(f)

        except json.JSONDecodeError:
            self.data = {}

    def save(self):

        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(
                self.data,
                f,
                indent=4,
                ensure_ascii=False
            )

    def add_account(self, service, login, password):

        self.data[service] = {
            "login": login,
            "password": password
        }

        self.save()

    def get_services(self):
        return list(self.data.keys())

    def get_account(self, service):
        return self.data.get(service)


# =========================================================
# ОСНОВНОЕ ПРИЛОЖЕНИЕ
# =========================================================

class PasswordManagerApp:

    def __init__(self):

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Password Manager")

        self.clock = pygame.time.Clock()

        self.manager = pygame_gui.UIManager((WIDTH, HEIGHT))

        self.storage = PasswordStorage(JSON_FILE)

        self.running = True
        self.password_visible = False
        self.notification_timer = 0

        self.create_ui()

    # =====================================================
    # СОЗДАНИЕ UI
    # =====================================================

    def create_ui(self):

        # =================================================
        # ЛЕВАЯ ПАНЕЛЬ
        # =================================================

        self.left_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect((0, 0), (250, HEIGHT)),
            manager=self.manager
        )

        self.service_list = pygame_gui.elements.UISelectionList(
            relative_rect=pygame.Rect((10, 10), (230, 480)),
            item_list=self.storage.get_services(),
            manager=self.manager,
            container=self.left_panel
        )

        # =================================================
        # ПРАВАЯ ПАНЕЛЬ
        # =================================================

        self.right_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect((250, 0), (550, HEIGHT)),
            manager=self.manager
        )

        # Заголовок
        self.title = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((20, 15), (400, 40)),
            text="Менеджер Паролей",
            manager=self.manager,
            container=self.right_panel
        )

        # =================================================
        # СЕРВИС
        # =================================================

        self.service_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((20, 55), (100, 20)),
            text="Сервис",
            manager=self.manager,
            container=self.right_panel
        )

        self.service_hint = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((120, 55), (250, 20)),
            text="",
            manager=self.manager,
            container=self.right_panel
        )

        self.service_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((20, 80), (300, 40)),
            manager=self.manager,
            container=self.right_panel
        )

        # =================================================
        # ЛОГИН
        # =================================================

        self.login_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((20, 115), (100, 20)),
            text="Логин",
            manager=self.manager,
            container=self.right_panel
        )

        self.login_hint = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((90, 115), (250, 20)),
            text="",
            manager=self.manager,
            container=self.right_panel
        )

        self.login_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((20, 140), (300, 40)),
            manager=self.manager,
            container=self.right_panel
        )

        # =================================================
        # ПАРОЛЬ
        # =================================================

        self.password_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((20, 175), (100, 20)),
            text="Пароль",
            manager=self.manager,
            container=self.right_panel
        )

        self.password_hint = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((100, 175), (250, 20)),
            text="",
            manager=self.manager,
            container=self.right_panel
        )

        self.password_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((20, 200), (300, 40)),
            manager=self.manager,
            container=self.right_panel
        )

        self.password_input.set_text_hidden(True)

        # =================================================
        # КНОПКИ
        # =================================================

        self.generate_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((20, 260), (220, 45)),
            text="Сгенерировать пароль",
            manager=self.manager,
            container=self.right_panel
        )

        self.show_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((250, 260), (100, 45)),
            text="🙈",
            manager=self.manager,
            container=self.right_panel
        )

        self.copy_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((360, 260), (120, 45)),
            text="Скопировать",
            manager=self.manager,
            container=self.right_panel
        )

        self.save_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((20, 330), (220, 50)),
            text="Сохранить",
            manager=self.manager,
            container=self.right_panel
        )

        self.delete_file_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((260, 330), (220, 50)),
            text="Удалить запись",
            manager=self.manager,
            container=self.right_panel
        )

        # =================================================
        # УВЕДОМЛЕНИЯ
        # =================================================

        self.notification = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((20, 410), (450, 40)),
            text="",
            manager=self.manager,
            container=self.right_panel
        )

    # =====================================================
    # ОБНОВЛЕНИЕ СПИСКА
    # =====================================================

    def refresh_service_list(self):

        self.service_list.kill()

        self.service_list = pygame_gui.elements.UISelectionList(
            relative_rect=pygame.Rect((10, 10), (230, 480)),
            item_list=self.storage.get_services(),
            manager=self.manager,
            container=self.left_panel
        )

    # =====================================================
    # УВЕДОМЛЕНИЕ
    # =====================================================

    def show_notification(self, text):

        self.notification.set_text(text)
        self.notification_timer = pygame.time.get_ticks()

    # =====================================================
    # СОБЫТИЯ
    # =====================================================

    def handle_events(self, event):

        if event.type == pygame.QUIT:
            self.running = False

        # =================================================
        # КНОПКИ
        # =================================================

        if event.type == pygame_gui.UI_BUTTON_PRESSED:

            # Генерация пароля
            if event.ui_element == self.generate_button:

                length = secrets.choice(range(12, 21))

                password = PasswordGenerator.generate(length)

                self.password_input.set_text(password)

            # Показать/скрыть пароль
            elif event.ui_element == self.show_button:

                self.password_visible = not self.password_visible

                self.password_input.set_text_hidden(
                    not self.password_visible
                )

                if self.password_visible:
                    self.show_button.set_text("👁")
                else:
                    self.show_button.set_text("🙈")

            # Копирование
            elif event.ui_element == self.copy_button:

                password = self.password_input.get_text()

                if password:

                    pyperclip.copy(password)

                    self.show_notification(
                        "Пароль скопирован!"
                    )

            # Сохранение
            elif event.ui_element == self.save_button:

                service = self.service_input.get_text().strip()
                login = self.login_input.get_text().strip()
                password = self.password_input.get_text().strip()

                if not service or not login or not password:

                    self.show_notification(
                        "Заполните все поля!"
                    )

                    return

                self.storage.add_account(
                    service,
                    login,
                    password
                )

                self.refresh_service_list()

                self.show_notification(
                    "Пароль сохранён!"
                )

            # Удаление выбранной записи
            elif event.ui_element == self.delete_file_button:

                service = self.service_input.get_text().strip()

                if not service:
                    self.show_notification(
                        "Выберите запись!"
                    )

                    return

                try:

                    # Проверяем наличие записи
                    if service in self.storage.data:

                        # Удаляем запись
                        del self.storage.data[service]

                        # Сохраняем JSON
                        self.storage.save()

                        # Очищаем поля
                        self.service_input.set_text("")
                        self.login_input.set_text("")
                        self.password_input.set_text("")

                        # Обновляем список
                        self.refresh_service_list()

                        self.show_notification(
                            "Запись удалена!"
                        )

                    else:

                        self.show_notification(
                            "Запись не найдена!"
                        )

                except Exception as e:

                    self.show_notification(
                        f"Ошибка: {e}"
                    )

                except Exception as e:

                    self.show_notification(
                        f"Ошибка: {e}"
                    )

        # =================================================
        # ВЫБОР АККАУНТА
        # =================================================

        if event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:

            service_name = event.text

            account = self.storage.get_account(service_name)

            if account:

                self.service_input.set_text(service_name)
                self.login_input.set_text(account["login"])
                self.password_input.set_text(account["password"])

    # =====================================================
    # ОТРИСОВКА
    # =====================================================

    def draw(self):

        self.screen.fill((30, 30, 30))

        pygame.draw.line(
            self.screen,
            (60, 60, 60),
            (250, 0),
            (250, HEIGHT),
            2
        )

        self.manager.draw_ui(self.screen)

    # =====================================================
    # ЗАПУСК
    # =====================================================

    def run(self):

        while self.running:

            time_delta = self.clock.tick(60) / 1000.0

            for event in pygame.event.get():

                self.handle_events(event)

                self.manager.process_events(event)

            # Очистка уведомления
            if self.notification_timer != 0:

                current_time = pygame.time.get_ticks()

                if current_time - self.notification_timer > 3000:

                    self.notification.set_text("")
                    self.notification_timer = 0

            self.manager.update(time_delta)

            self.draw()

            pygame.display.update()

        pygame.quit()


# =========================================================
# ЗАПУСК
# =========================================================

if __name__ == "__main__":

    app = PasswordManagerApp()
    app.run()