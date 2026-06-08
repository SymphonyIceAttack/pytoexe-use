import time
import requests
from datetime import datetime, time as dt_time
import logging

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = "8848816077:AAFJInDqahjHOKuF6rZc4IwFMsXTMlweHi4"       # Токен вашего Telegram бота
CHAT_ID = "6464336595"           # ID чата (пользователя или группы)
TARGET_TIMES = [
    dt_time(8, 30),  # 8:30
    dt_time(8, 35),  # 8:35
    dt_time(8, 40),  # 8:40
    dt_time(8, 45)   # 8:45
]

# ---------- НАСТРОЙКИ ПРОКСИ ----------
USE_PROXY = True                   # Использовать прокси?
PROXY_TYPE = "http"                # http, https или socks5
PROXY_HOST = "87.120.187.129"   # Адрес прокси-сервера
PROXY_PORT = 22851                  # Порт прокси
PROXY_USER = None                  # Логин (если требуется аутентификация)
PROXY_PASS = None                  # Пароль
# -------------------------------------
# ================================

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_proxy_dict():
    """Формирует словарь прокси для requests в зависимости от типа."""
    if not USE_PROXY:
        return None

    if PROXY_USER and PROXY_PASS:
        auth = f"{PROXY_USER}:{PROXY_PASS}@"
    else:
        auth = ""

        if PROXY_TYPE in ("http", "https"):
            proxy_url = f"{PROXY_TYPE}://{auth}{PROXY_HOST}:{PROXY_PORT}"
            return {
                "http": proxy_url,
                "https": proxy_url
            }
        elif PROXY_TYPE == "socks5":
            # Для SOCKS5 нужна библиотека 'requests[socks]' (pip install requests[socks])
            proxy_url = f"socks5://{auth}{PROXY_HOST}:{PROXY_PORT}"
            return {
                "http": proxy_url,
                "https": proxy_url
            }
        else:
            logging.warning(f"Неподдерживаемый тип прокси: {PROXY_TYPE}. Прокси не используется.")
            return None

        def send_telegram(message):
            """Отправляет сообщение в Telegram через API бота с поддержкой прокси."""
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": CHAT_ID,
                "text": message,
                "parse_mode": "HTML"
            }
            proxies = get_proxy_dict()
            try:
                if proxies:
                    response = requests.post(url, json=payload, proxies=proxies, timeout=10)
                else:
                    response = requests.post(url, json=payload, timeout=10)
                    response.raise_for_status()
                    logging.info("Сообщение успешно отправлено: %s", message)
                except Exception as e:
                    logging.error("Ошибка при отправке сообщения: %s", e)

                    def is_computer_active():
                        """Проверка активности компьютера (всегда True, так как программа запущена)."""
                        return True

                    def need_to_send_now():
                        """Определяет, нужно ли отправить уведомление в текущий момент."""
                        now = datetime.now()
                        current_time = now.time()
                        for target in TARGET_TIMES:
                            diff = abs(
                                (current_time.hour - target.hour) * 3600 +
                                (current_time.minute - target.minute) * 60 +
                                (current_time.second - target.second)
                            )
                            if diff <= 30:
                                return True
                            return False

                        def main():
                            logging.info("Программа мониторинга запущена. Ожидание целевого времени...")
                            last_sent = {}

                            while True:
                                now = datetime.now()
                                if need_to_send_now():
                                    current_key = now.replace(second=0, microsecond=0)
                                    if last_sent.get(current_key) != current_key:
                                        if is_computer_active():
                                            send_telegram(
                                                f"✅ <b>Отстук</b>\n"
                                                f"ВБ Молодых Строителей 2 - Открыт в {now.strftime('%H:%M:%S')}"
                                            )
                                        else:
                                            send_telegram(
                                                f"⚠️ <b>Неактивность</b>\n"
                                                f"ВБ Молодых Строителей 2 - Не удалось получить информацию в {now.strftime('%H:%M:%S')}"
                                            )
                                            last_sent[current_key] = current_key
                                            time.sleep(60)

                                            if __name__ == "__main__":
                                                try:
                                                    main()
                                                except KeyboardInterrupt:
                                                    logging.info("Программа остановлена пользователем.")
                                                except Exception as e:
                                                    logging.critical("Необработанная ошибка: %s", e)