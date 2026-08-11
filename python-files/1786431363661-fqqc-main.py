"""
YouTube Boost Ultra v1.0
========================
Визуальный симулятор / прототип инструмента для продвижения YouTube-каналов.
Все процессы являются имитацией и не выполняют реальных действий.

Стек: Python 3.10+, CustomTkinter
Автор: YouTube Boost Ultra Team
"""

import customtkinter as ctk
import threading
import time
import random
import re
from datetime import datetime


# ─────────────────────────── Цветовая палитра ───────────────────────────

COLORS = {
    "bg_dark":       "#0B132B",
    "bg_secondary":  "#1A1B2F",
    "bg_card":       "#151933",
    "accent":        "#00EBDE",
    "accent_hover":  "#00C4B8",
    "accent_blue":   "#0072FF",
    "accent_glow":   "#004FCC",
    "text_primary":  "#FFFFFF",
    "text_secondary":"#8D99AE",
    "text_muted":    "#4A5280",
    "error":         "#FF4C6A",
    "success":       "#00E676",
    "border":        "#1E2550",
    "input_bg":      "#0F1730",
    "log_bg":        "#080E24",
}


# ──────────────────── Сообщения для имитации процесса ────────────────────

PHASE_MESSAGES = {
    "init": [
        ("🔐 Инициализация защищённого канала связи...", 0.6),
        ("🌐 Подключение к распределённой прокси-сети (узлы: 847)...", 0.8),
        ("🛡️ Обход алгоритмов YouTube Anti-Bot v4.7...", 1.0),
        ("✅ Защита обойдена. Канал авторизован.", 0.5),
        ("📡 Синхронизация с серверами обработки данных...", 0.7),
        ("🔑 Генерация уникальных API-токенов сессий...", 0.6),
    ],
    "views": [
        ("👁️ Запуск модуля просмотров [ViewEngine v3.2]...", 0.5),
        ("⚙️ Генерация уникальных сессий просмотра...", 0.7),
        ("📊 Подача просмотров (пакет 1/5)... успешно: +{count}", 0.9),
        ("📊 Подача просмотров (пакет 2/5)... успешно: +{count}", 0.8),
        ("📊 Подача просмотров (пакет 3/5)... успешно: +{count}", 1.0),
        ("📊 Подача просмотров (пакет 4/5)... успешно: +{count}", 0.7),
        ("📊 Подача просмотров (пакет 5/5)... успешно: +{count}", 0.8),
        ("✅ Модуль просмотров завершён. Итого: +{total} просмотров.", 0.4),
    ],
    "subs": [
        ("👥 Запуск модуля подписчиков [SubEngine v2.8]...", 0.5),
        ("🧬 Создание уникальных профилей подписчиков...", 0.8),
        ("👤 Добавление живых подписчиков (волна 1/3)... успешно: +{count}", 1.0),
        ("👤 Добавление живых подписчиков (волна 2/3)... успешно: +{count}", 0.9),
        ("👤 Добавление живых подписчиков (волна 3/3)... успешно: +{count}", 0.8),
        ("✅ Модуль подписчиков завершён. Итого: +{total} подписчиков.", 0.4),
    ],
    "sync": [
        ("🔄 Синхронизация данных с серверами YouTube...", 1.2),
        ("📦 Верификация пакетов данных...", 0.8),
        ("🌍 Распределение метрик по регионам (GEO-балансировка)...", 0.7),
        ("📈 Обновление аналитики канала...", 0.6),
        ("✅ Синхронизация данных с серверами YouTube успешна.", 0.3),
        ("ℹ️ Изменения вступят в силу в Творческой студии в течение 5-10 минут.", 0.0),
    ],
}


# ────────────────────────── Валидация YouTube URL ────────────────────────

def is_valid_youtube_url(url: str) -> bool:
    """Проверяет, содержит ли строка допустимый формат YouTube-ссылки."""
    patterns = [
        r'(https?://)?(www\.)?youtube\.com/watch\?v=[\w-]+',
        r'(https?://)?(www\.)?youtube\.com/channel/[\w-]+',
        r'(https?://)?(www\.)?youtube\.com/@[\w.-]+',
        r'(https?://)?(www\.)?youtube\.com/shorts/[\w-]+',
        r'(https?://)?youtu\.be/[\w-]+',
        r'(https?://)?(www\.)?youtube\.com/c/[\w-]+',
    ]
    return any(re.match(p, url.strip()) for p in patterns)


# ───────────────────── Кастомный диалог ошибки ───────────────────────────

class ErrorDialog(ctk.CTkToplevel):
    """Стильное окно ошибки в стиле приложения."""

    def __init__(self, parent, title: str, message: str):
        super().__init__(parent)
        self.title(title)
        self.geometry("420x220")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["bg_dark"])
        self.transient(parent)
        self.grab_set()

        # Центрируем относительно родительского окна
        self.after(10, self._center, parent)

        # Иконка ошибки
        icon_label = ctk.CTkLabel(
            self, text="⚠️", font=("Segoe UI Emoji", 42),
            text_color=COLORS["error"],
        )
        icon_label.pack(pady=(24, 8))

        # Текст ошибки
        msg_label = ctk.CTkLabel(
            self, text=message,
            font=("Segoe UI", 14),
            text_color=COLORS["text_primary"],
            wraplength=360,
        )
        msg_label.pack(pady=(0, 16))

        # Кнопка ОК
        ok_btn = ctk.CTkButton(
            self, text="Понятно", width=140, height=36,
            font=("Segoe UI Semibold", 13),
            fg_color=COLORS["error"],
            hover_color="#CC3D55",
            corner_radius=10,
            command=self.destroy,
        )
        ok_btn.pack(pady=(0, 16))

    def _center(self, parent):
        self.update_idletasks()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        px, py = parent.winfo_x(), parent.winfo_y()
        w, h = self.winfo_width(), self.winfo_height()
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        self.geometry(f"+{x}+{y}")


# ───────────────────────── Основное приложение ───────────────────────────

class YouTubeBoostApp(ctk.CTk):
    """Главное окно приложения YouTube Boost Ultra."""

    APP_TITLE = "YouTube Boost Ultra v1.0"
    WINDOW_SIZE = "780x720"

    def __init__(self):
        super().__init__()

        # ── Настройки окна ──
        self.title(self.APP_TITLE)
        self.geometry(self.WINDOW_SIZE)
        self.minsize(700, 650)
        self.configure(fg_color=COLORS["bg_dark"])
        ctk.set_appearance_mode("dark")

        # Состояние
        self._is_running = False
        self._total_views = 0
        self._total_subs = 0

        # ── Построение интерфейса ──
        self._build_ui()

        # Центрируем окно на экране
        self.after(50, self._center_window)

    # ──────────────────────── UI Builder ─────────────────────────────────

    def _build_ui(self):
        """Собирает весь пользовательский интерфейс."""

        # Основной контейнер с отступами
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=28, pady=20)

        # ── 1. Заголовок ──
        self._build_header(container)

        # ── 2. Разделитель ──
        sep = ctk.CTkFrame(container, height=1, fg_color=COLORS["border"])
        sep.pack(fill="x", pady=(12, 20))

        # ── 3. Поле ввода URL ──
        self._build_url_input(container)

        # ── 4. Кнопка действия ──
        self._build_action_button(container)

        # ── 5. Статистика ──
        self._build_stats_panel(container)

        # ── 6. Прогресс-бар ──
        self._build_progress(container)

        # ── 7. Лог-консоль ──
        self._build_log_console(container)

        # ── 8. Футер ──
        self._build_footer(container)

    def _build_header(self, parent):
        """Заголовок приложения."""
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.pack(fill="x")

        # Иконка
        icon = ctk.CTkLabel(
            header_frame, text="🚀",
            font=("Segoe UI Emoji", 32),
        )
        icon.pack(side="left", padx=(0, 12))

        # Название
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(side="left", fill="x", expand=True)

        title = ctk.CTkLabel(
            title_frame, text=self.APP_TITLE,
            font=("Segoe UI Bold", 24),
            text_color=COLORS["text_primary"],
            anchor="w",
        )
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            title_frame,
            text="Платформа продвижения YouTube-каналов • Premium Edition",
            font=("Segoe UI", 12),
            text_color=COLORS["text_secondary"],
            anchor="w",
        )
        subtitle.pack(anchor="w")

        # Версия badge
        badge = ctk.CTkLabel(
            header_frame, text=" PREMIUM ",
            font=("Segoe UI Bold", 10),
            text_color=COLORS["bg_dark"],
            fg_color=COLORS["accent"],
            corner_radius=6,
            width=70, height=24,
        )
        badge.pack(side="right", padx=(0, 4))

    def _build_url_input(self, parent):
        """Поле ввода URL с описанием."""

        # Лейбл
        label = ctk.CTkLabel(
            parent, text="📎  Целевой URL",
            font=("Segoe UI Semibold", 13),
            text_color=COLORS["text_secondary"],
            anchor="w",
        )
        label.pack(fill="x", pady=(0, 6))

        # Рамка для поля ввода
        input_frame = ctk.CTkFrame(
            parent, fg_color=COLORS["input_bg"],
            corner_radius=12, border_width=2,
            border_color=COLORS["border"],
        )
        input_frame.pack(fill="x", pady=(0, 4))

        self.url_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Введите URL видео или YouTube-канала...",
            font=("Segoe UI", 14),
            text_color=COLORS["text_primary"],
            placeholder_text_color=COLORS["text_muted"],
            fg_color="transparent",
            border_width=0,
            height=46,
        )
        self.url_entry.pack(fill="x", padx=12, pady=4)

        # Привязка: при фокусе рамка подсвечивается
        self.url_entry.bind("<FocusIn>",
            lambda e: input_frame.configure(border_color=COLORS["accent"]))
        self.url_entry.bind("<FocusOut>",
            lambda e: input_frame.configure(border_color=COLORS["border"]))

    def _build_action_button(self, parent):
        """Главная кнопка действия."""
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(16, 4))

        self.action_btn = ctk.CTkButton(
            btn_frame,
            text="⚡  Н А К Р У Т И Т Ь",
            font=("Segoe UI Bold", 16),
            text_color=COLORS["text_primary"],
            fg_color=COLORS["accent_blue"],
            hover_color=COLORS["accent_glow"],
            corner_radius=14,
            height=52,
            command=self._on_boost_click,
        )
        self.action_btn.pack(fill="x")

    def _build_stats_panel(self, parent):
        """Панель быстрой статистики."""
        stats_frame = ctk.CTkFrame(
            parent, fg_color=COLORS["bg_card"],
            corner_radius=12, border_width=1,
            border_color=COLORS["border"],
        )
        stats_frame.pack(fill="x", pady=(16, 4))

        inner = ctk.CTkFrame(stats_frame, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)
        inner.columnconfigure((0, 1, 2), weight=1)

        # Просмотры
        self._stat_views = self._make_stat_card(inner, "👁️ Просмотры", "0", 0)
        # Подписчики
        self._stat_subs = self._make_stat_card(inner, "👥 Подписчики", "0", 1)
        # Статус
        self._stat_status = self._make_stat_card(inner, "📡 Статус", "Ожидание", 2)

    def _make_stat_card(self, parent, title: str, value: str, col: int):
        """Создаёт одну карточку статистики и возвращает лейбл значения."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=0, column=col, sticky="nsew", padx=8)

        t_label = ctk.CTkLabel(
            frame, text=title,
            font=("Segoe UI", 11),
            text_color=COLORS["text_secondary"],
        )
        t_label.pack()

        v_label = ctk.CTkLabel(
            frame, text=value,
            font=("Segoe UI Bold", 18),
            text_color=COLORS["accent"],
        )
        v_label.pack(pady=(2, 0))

        return v_label

    def _build_progress(self, parent):
        """Прогресс-бар."""
        self.progress_label = ctk.CTkLabel(
            parent, text="Прогресс: 0%",
            font=("Segoe UI", 11),
            text_color=COLORS["text_secondary"],
            anchor="w",
        )
        self.progress_label.pack(fill="x", pady=(12, 4))

        self.progress_bar = ctk.CTkProgressBar(
            parent, height=10,
            fg_color=COLORS["bg_card"],
            progress_color=COLORS["accent"],
            corner_radius=5,
        )
        self.progress_bar.pack(fill="x")
        self.progress_bar.set(0)

    def _build_log_console(self, parent):
        """Консоль логов."""
        log_label = ctk.CTkLabel(
            parent, text="📋  Журнал операций",
            font=("Segoe UI Semibold", 13),
            text_color=COLORS["text_secondary"],
            anchor="w",
        )
        log_label.pack(fill="x", pady=(16, 6))

        self.log_text = ctk.CTkTextbox(
            parent, height=160,
            font=("Consolas", 12),
            fg_color=COLORS["log_bg"],
            text_color=COLORS["text_secondary"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border"],
            wrap="word",
            state="disabled",
        )
        self.log_text.pack(fill="both", expand=True)

    def _build_footer(self, parent):
        """Нижний футер."""
        footer = ctk.CTkLabel(
            parent,
            text="© 2026 YouTube Boost Ultra  •  Все данные защищены 256-bit шифрованием",
            font=("Segoe UI", 10),
            text_color=COLORS["text_muted"],
        )
        footer.pack(pady=(10, 0))

    # ──────────────────── Утилиты UI ─────────────────────────────────────

    def _center_window(self):
        """Центрирует окно на экране."""
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _log(self, message: str):
        """Добавляет сообщение в лог-консоль (потокобезопасно через after)."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}]  {message}\n"

        def _append():
            self.log_text.configure(state="normal")
            self.log_text.insert("end", line)
            self.log_text.see("end")
            self.log_text.configure(state="disabled")

        self.after(0, _append)

    def _set_progress(self, value: float):
        """Обновляет прогресс-бар (0.0 — 1.0)."""
        def _update():
            self.progress_bar.set(value)
            self.progress_label.configure(text=f"Прогресс: {int(value * 100)}%")
        self.after(0, _update)

    def _set_stat(self, label: ctk.CTkLabel, value: str):
        """Обновляет значение статистики."""
        self.after(0, lambda: label.configure(text=value))

    def _set_button_state(self, enabled: bool):
        """Включает/выключает кнопку действия."""
        def _update():
            if enabled:
                self.action_btn.configure(
                    state="normal",
                    text="⚡  Н А К Р У Т И Т Ь",
                    fg_color=COLORS["accent_blue"],
                )
            else:
                self.action_btn.configure(
                    state="disabled",
                    text="⏳  В процессе...",
                    fg_color=COLORS["text_muted"],
                )
        self.after(0, _update)

    # ─────────────────── Логика «накрутки» ───────────────────────────────

    def _on_boost_click(self):
        """Обработчик нажатия главной кнопки."""
        url = self.url_entry.get().strip()

        if not url:
            ErrorDialog(
                self, "Ошибка ввода",
                "Пожалуйста, введите ссылку на видео или канал YouTube."
            )
            return

        if not is_valid_youtube_url(url):
            ErrorDialog(
                self, "Некорректная ссылка",
                "Введённая ссылка не соответствует формату YouTube.\n"
                "Пример: https://youtube.com/watch?v=dQw4w9WgXcQ"
            )
            return

        # Всё ок — запускаем процесс в отдельном потоке
        self._is_running = True
        self._total_views = 0
        self._total_subs = 0
        self._set_button_state(False)

        # Очищаем лог
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

        thread = threading.Thread(target=self._boost_process, args=(url,), daemon=True)
        thread.start()

    def _boost_process(self, url: str):
        """Основной процесс имитации накрутки (выполняется в фоновом потоке)."""
        total_steps = (
            len(PHASE_MESSAGES["init"])
            + len(PHASE_MESSAGES["views"])
            + len(PHASE_MESSAGES["subs"])
            + len(PHASE_MESSAGES["sync"])
        )
        current_step = 0

        self._set_stat(self._stat_status, "Работает...")
        self._log(f"🎯 Цель: {url}")
        self._log("─" * 50)

        # ── Фаза 1: Инициализация ──
        for msg, delay in PHASE_MESSAGES["init"]:
            self._log(msg)
            current_step += 1
            self._set_progress(current_step / total_steps)
            time.sleep(delay + random.uniform(0.1, 0.4))

        self._log("─" * 50)

        # ── Фаза 2: Просмотры ──
        view_counts = [
            random.randint(1800, 3200),
            random.randint(2500, 4000),
            random.randint(3000, 5500),
            random.randint(2000, 3800),
            random.randint(1500, 2800),
        ]
        view_idx = 0
        for msg_template, delay in PHASE_MESSAGES["views"]:
            if "{count}" in msg_template:
                count = view_counts[view_idx]
                self._total_views += count
                msg = msg_template.format(count=f"{count:,}".replace(",", " "))
                view_idx += 1
            elif "{total}" in msg_template:
                msg = msg_template.format(total=f"{self._total_views:,}".replace(",", " "))
            else:
                msg = msg_template

            self._log(msg)
            self._set_stat(self._stat_views, f"{self._total_views:,}".replace(",", " "))
            current_step += 1
            self._set_progress(current_step / total_steps)
            time.sleep(delay + random.uniform(0.1, 0.5))

        self._log("─" * 50)

        # ── Фаза 3: Подписчики ──
        sub_counts = [
            random.randint(300, 600),
            random.randint(400, 700),
            random.randint(200, 500),
        ]
        sub_idx = 0
        for msg_template, delay in PHASE_MESSAGES["subs"]:
            if "{count}" in msg_template:
                count = sub_counts[sub_idx]
                self._total_subs += count
                msg = msg_template.format(count=f"{count:,}".replace(",", " "))
                sub_idx += 1
            elif "{total}" in msg_template:
                msg = msg_template.format(total=f"{self._total_subs:,}".replace(",", " "))
            else:
                msg = msg_template

            self._log(msg)
            self._set_stat(self._stat_subs, f"{self._total_subs:,}".replace(",", " "))
            current_step += 1
            self._set_progress(current_step / total_steps)
            time.sleep(delay + random.uniform(0.1, 0.5))

        self._log("─" * 50)

        # ── Фаза 4: Синхронизация ──
        for msg, delay in PHASE_MESSAGES["sync"]:
            self._log(msg)
            current_step += 1
            self._set_progress(current_step / total_steps)
            time.sleep(delay + random.uniform(0.1, 0.3))

        # ── Завершение ──
        self._set_progress(1.0)
        self._set_stat(self._stat_status, "Завершено ✅")
        self._log("─" * 50)
        self._log("🏁 Процесс завершён успешно!")
        self._log(
            f"📊 Итого: +{self._total_views:,} просмотров, "
            f"+{self._total_subs:,} подписчиков".replace(",", " ")
        )
        self._is_running = False
        self._set_button_state(True)


# ──────────────────────── Точка входа ────────────────────────────────────

if __name__ == "__main__":
    app = YouTubeBoostApp()
    app.mainloop()
