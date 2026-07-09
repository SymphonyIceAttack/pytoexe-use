import time
import webbrowser
import psutil

def mq_function():
    print("маме привет от одноразового прикола!")

def monitor_dota():
    print("Начинаем постоянный мониторинг Dota...")
    webbrowser.open("https://www.google.com/search?q=милые+котики")
    print("Котики открыты!")

    CHECK_INTERVAL = 5          # проверка каждые 5 секунд
    GABEN_INTERVAL = 15 * 60    # 15 минут

    last_gaben_time = 0
    dota_was_running = False

    try:
        while True:
            dota_running = any(
                'dota' in p.info['name'].lower()
                for p in psutil.process_iter(['name'])
                if p.info['name']
            )

            now = time.time()

            if dota_running:
                if not dota_was_running:
                    # Только что запустилась – открываем сразу
                    webbrowser.open("https://www.google.com/search?q=габен пидор")
                    print("Dota запущена — Габен открыт!")
                    last_gaben_time = now
                else:
                    # Уже работала – проверяем интервал
                    if now - last_gaben_time >= GABEN_INTERVAL:
                        webbrowser.open("https://www.google.com/search?q=габен играет с хуем")
                        print("Прошло 15 минут — Габен снова открыт!")
                        last_gaben_time = now
                dota_was_running = True
            else:
                if dota_was_running:
                    print("Dota закрыта.")
                dota_was_running = False
                last_gaben_time = 0   # сброс таймера

            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        print("\nМониторинг остановлен.")
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    mq_function()
    monitor_dota()