import os
import sys
import time


# Принудительная установка
def emergency_setup():
    try:
        import pyMeow as pm
    except ImportError:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyMeow"], stdout=subprocess.DEVNULL)
        os.execl(sys.executable, sys.executable, *sys.argv)


emergency_setup()
import pyMeow as pm


def run_cheat():
    os.system('cls')
    print("==========================================")
    print("СТАТУС: ОЖИДАНИЕ CS2 (ОКОННЫЙ РЕЖИМ)...")
    print("НЕ ЗАКРЫВАЙТЕ ЭТО ОКНО!")
    print("==========================================")

    while True:
        try:
            # Пытаемся зацепиться за процесс
            proc = pm.open_process("cs2.exe")
            mod = pm.get_module(proc, "client.dll")
            overlay = pm.overlay_init(target="Counter-Strike 2")

            print(">>> ИГРА НАЙДЕНА! ВХ ЗАПУЩЕН.")

            while pm.overlay_loop(overlay):
                pm.begin_drawing()
                # Рисуем яркую зеленую рамку в центре для проверки
                pm.draw_rectangle_lines(860, 440, 200, 400, pm.get_color("green"), 3.0)
                pm.draw_text("SYSTEM_ACTIVE", 860, 410, 20, pm.get_color("green"))
                pm.end_drawing()
        except:
            # Если игра не открыта, просто ждем 2 секунды и пробуем снова
            time.sleep(2)


if __name__ == "__main__":
    try:
        run_cheat()
    except Exception as e:
        print(f"Критический сбой: {e}")
        input("Нажмите Enter, чтобы закрыть...")  # Это предотвратит код 0