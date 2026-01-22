import flet as ft
import random
import time

# --- НАСТРОЙКИ БОТА (СЛОВАРЬ ОТВЕТОВ) ---
# Сюда можно добавлять новые вопросы и ответы
RESPONSES = {
    "пасхалко": "Ты наткнулся на пасхалку №1 🥚",
    "зачем создан этот чат": "Для общения и тестов нейросети.",
    "создатель": "tg: t.me/GeniusAI_info",
    "67": "Ты ребёнок!?",
    "кто ты": "Я... я GeniusAI, твой виртуальный помощник.",
    "1488": "Ты наткнулся на пасхалку №2 🚀",
    "привет": "Привет! Рад тебя видеть.",
    "как дела": "У меня нет чувств, но мои алгоритмы работают стабильно!",
}

def main(page: ft.Page):
    # --- НАСТРОЙКИ ОКНА ---
    page.title = "GeniusAI"
    page.theme_mode = ft.ThemeMode.DARK  # Темная тема как на скриншоте
    page.padding = 0
    page.window_width = 400
    page.window_height = 700
    
    # Цвета (под стиль ChatGPT)
    BG_COLOR = "#1e1e1e" # Темно-серый фон
    BOT_BUBBLE_COLOR = "#2e2e2e" # Пузырь бота
    USER_BUBBLE_COLOR = "#005c4b" # Пузырь пользователя (зеленоватый/синий)
    
    page.bgcolor = BG_COLOR

    # Генерируем API ключ при запуске
    generated_api_key = random.randint(1000, 9999)
    user_name = "User"
    
    # Переменные состояния
    current_state = "auth" # auth, name, chat

    # --- ЭЛЕМЕНТЫ ИНТЕРФЕЙСА ---
    
    chat_list = ft.ListView(
        expand=True, 
        spacing=10, 
        padding=20, 
        auto_scroll=True
    )

    msg_field = ft.TextField(
        hint_text="Введите API ключ...",
        border_radius=20,
        filled=True,
        expand=True,
        bgcolor="#2b2d31",
        on_submit=lambda e: send_message_click(e)
    )

    # Функция добавления сообщения в чат
    def add_message(text, is_user=False):
        alignment = ft.MainAxisAlignment.END if is_user else ft.MainAxisAlignment.START
        bubble_color = USER_BUBBLE_COLOR if is_user else BOT_BUBBLE_COLOR
        avatar = ft.Icon(ft.icons.PERSON, color="white") if is_user else ft.Image(src="https://img.icons8.com/ios-filled/50/FFFFFF/chatgpt.png", width=25, height=25, color="white")
        
        # Если это бот, используем иконку робота/gpt, если нет иконки - ставим заглушку
        if not is_user:
             avatar_container = ft.Container(
                 content=ft.Icon(ft.icons.SMART_TOY_OUTLINED, color="white"),
                 padding=5
             )
        else:
             avatar_container = ft.Container(width=0) # Скрываем аватар для юзера для минимализма

        chat_row = ft.Row(
            controls=[
                avatar_container if not is_user else ft.Container(),
                ft.Container(
                    content=ft.Text(text, size=16, color="white"),
                    bgcolor=bubble_color,
                    border_radius=ft.border_radius.only(
                        top_left=15, top_right=15, 
                        bottom_left=15 if is_user else 0, 
                        bottom_right=0 if is_user else 15
                    ),
                    padding=12,
                    constraints=ft.BoxConstraints(max_width=300),
                ),
            ],
            alignment=alignment,
            vertical_alignment=ft.CrossAxisAlignment.START
        )
        chat_list.controls.append(chat_row)
        page.update()

    # Основная логика обработки ввода
    def process_input(text):
        nonlocal current_state, user_name

        if current_state == "auth":
            try:
                key = int(text)
                if key == generated_api_key:
                    add_message(f"API Key {key} принят!", is_user=False)
                    add_message("Как тебя зовут?", is_user=False)
                    current_state = "name"
                    msg_field.hint_text = "Напиши своё имя..."
                    msg_field.value = ""
                else:
                    add_message("Неверный ключ! Попробуй еще раз.", is_user=False)
            except ValueError:
                add_message("Ключ должен быть числом.", is_user=False)

        elif current_state == "name":
            user_name = text
            add_message(f"Приятно познакомиться, {user_name}!", is_user=False)
            add_message("Задавай вопросы.", is_user=False)
            current_state = "chat"
            msg_field.hint_text = "Сообщение..."
            msg_field.value = ""

        elif current_state == "chat":
            # Нормализуем текст
            query = text.lower().strip()
            
            # Логика ответов
            response_text = ""
            
            # Секретные команды из вашего кода
            if query == "ilk":
                response_text = "⚠️ Access permission granted. Error detected..."
            elif query == "create":
                # В GUI сложно делать вложенные input, упростим логику
                response_text = "Для доступа к Creator Mode введите пароль: 'ILK pass'"
            elif query == "ilk pass":
                response_text = "Creator: roma_ILK | PassKey: ILK"
            elif query == user_name.lower():
                response_text = "Да, это отличное имя!"
            elif query == "что по api":
                response_text = f"Твой ключ: {generated_api_key} — работает отлично!"
            elif query in RESPONSES:
                response_text = RESPONSES[query]
            else:
                response_text = "Чтобы ваш вопрос добавили, напишите 'создатель' (или я пока не знаю ответа)."
            
            # Имитация задержки печати (как у живого ИИ)
            time.sleep(0.3) 
            add_message(response_text, is_user=False)
            msg_field.value = ""

        page.update()

    def send_message_click(e):
        if msg_field.value:
            text = msg_field.value
            msg_field.value = ""
            
            # Сразу показываем сообщение пользователя
            if current_state == "chat":
                add_message(text, is_user=True)
            elif current_state == "name":
                 add_message(text, is_user=True)
            
            # Обрабатываем логику
            process_input(text)
            msg_field.focus()
            page.update()

    # --- СБОРКА ИНТЕРФЕЙСА ---
    
    # Верхняя панель (AppBar) как на картинке
    app_bar = ft.Container(
        content=ft.Row([
            ft.Icon(ft.icons.ARROW_BACK, color="white"),
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.icons.SMART_TOY, color="white", size=30),
                    ft.Text("GeniusAI", size=20, weight=ft.FontWeight.BOLD, color="white"),
                ]),
                expand=True
            ),
            ft.Icon(ft.icons.MORE_VERT, color="white")
        ]),
        padding=ft.padding.symmetric(horizontal=15, vertical=10),
        bgcolor="#1e1e1e", # Цвет шапки
    )

    # Нижняя панель ввода
    input_bar = ft.Container(
        content=ft.Row([
            msg_field,
            ft.IconButton(icon=ft.icons.SEND, icon_color="blue", on_click=send_message_click)
        ]),
        padding=10,
        bgcolor="#1e1e1e"
    )

    # Вывод на экран
    page.add(
        ft.Column(
            [
                app_bar,
                ft.Divider(height=1, color="grey"),
                chat_list,
                input_bar
            ],
            expand=True,
            spacing=0
        )
    )

    # --- СТАРТОВАЯ ЛОГИКА ---
    # Показываем API ключ пользователю (имитация вашего принта в консоль)
    # В реальном приложении ключ обычно присылают на почту, но мы выведем его в чат первым сообщением
    add_message(f"--- ВАШ API KEY: {generated_api_key} ---", is_user=False)
    add_message("Пожалуйста, введите ваш API Key для входа:", is_user=False)

ft.app(target=main)