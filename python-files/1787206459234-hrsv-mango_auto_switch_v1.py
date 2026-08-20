import time
import threading
from datetime import datetime

from pywinauto import Desktop

import pystray
from PIL import Image, ImageDraw


# ======================
# Настройки
# ======================

CHECK_INTERVAL = 0.5
AFTER_CONNECT_DELAY = 1
COOLDOWN = 30


running = True
last_transfer = 0


# ======================
# Лог
# ======================

def log(text):
    print(
        datetime.now().strftime("%H:%M:%S"),
        "-",
        text
    )


# ======================
# Поиск Mango
# ======================

def find_mango():

    for w in Desktop(backend="uia").windows():

        try:

            if "Mango Talker" in w.window_text():
                return w

        except:
            pass

    return None



# ======================
# Перевод звонка
# ======================

def transfer_call(mango):

    global last_transfer

    log("Перевод звонка")

    time.sleep(AFTER_CONNECT_DELAY)


    # первое Переключить

    for b in mango.descendants(control_type="Button"):

        try:

            if b.window_text() == "Переключить" and b.is_enabled():

                log("Первый клик")

                b.click_input()

                break

        except:
            pass


    time.sleep(1)



    # окно перевода

    dialog = None


    for item in mango.descendants():

        try:

            if item.window_text() == "Переключить вызов":

                dialog = item

                break

        except:
            pass


    if not dialog:
        log("Диалог не найден")
        return



    # выбор устройства

    for item in dialog.descendants():

        try:

            if item.element_info.control_type == "ListItem":

                log("Выбор телефона")

                item.click_input()

                break

        except:
            pass



    time.sleep(1)



    # подтверждение

    for b in dialog.descendants(control_type="Button"):

        try:

            if b.window_text() == "Переключить" and b.is_enabled():

                log("Подтверждение")

                b.click_input()

                last_transfer = time.time()

                log("Готово")

                return

        except:
            pass



# ======================
# Фоновый поток
# ======================

def worker():

    global running

    log("Mango Auto Switch запущен")


    while True:

        if running:

            try:

                mango = find_mango()


                if mango:


                    for b in mango.descendants(control_type="Button"):


                        try:


                            if b.window_text() == "Переключить":


                                if b.is_enabled():


                                    if time.time() - last_transfer > COOLDOWN:

                                        transfer_call(mango)


                                    break


                        except:
                            pass


            except Exception as e:

                log(str(e))


        time.sleep(CHECK_INTERVAL)



# ======================
# Значок в трее
# ======================

def create_image():

    img = Image.new(
        "RGB",
        (64,64),
        "green"
    )

    d = ImageDraw.Draw(img)

    d.text(
        (20,20),
        "M",
        fill="white"
    )

    return img



def toggle(icon, item):

    global running

    running = not running

    log(
        "Автоматизация: "
        + ("ВКЛ" if running else "ПАУЗА")
    )



def exit_app(icon, item):

    icon.stop()



menu = pystray.Menu(

    pystray.MenuItem(
        "Включить / Пауза",
        toggle
    ),

    pystray.MenuItem(
        "Выход",
        exit_app
    )

)



# запуск потока

threading.Thread(
    target=worker,
    daemon=True
).start()



icon = pystray.Icon(
    "Mango Auto Switch",
    create_image(),
    "Mango Auto Switch",
    menu
)


icon.run()