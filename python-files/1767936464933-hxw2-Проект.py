import os
import pyscreenshot
import subprocess
import time
import webbrowser

#ФИО: [Чигаев Я. Г.]

#Путь к рабочему столу
desktop = os.path.join(os.environ['Ярослав'], 'Рабочий стол')
print(desktop)
#Путь к изображению
pictures = os.path.join(os.environ['Ярослав'], 'Изображения')
print(pictures)
#1 попытка запуска FTP-клиента для подключения к ftp.example.com
resl = subprocess.Popen('ftp -A ftp.example.com', shell=True)

#Первый скриншот всего экрана
image1 = pyscreenshot.grab()
#Сохранение первого скриншота на рабочий стол
image1.save (os.path.join(desktop, 'modified_ЧЯГ.png'))
#Второй скриншот всего экрана
image2 = pyscreenshot.grab()
#Сохранение второго скриншота в папку изображения
image2.save (os.path.join(pictures, 'modified_ЧЯГ.png'))

#Рикрол
webbrowser.open('https://www.youtube.com/watch?v=dQw4w9WgXcQ', new=0)

#Бесконечный цикл
while True:
    #Приостоновка программы на 360 секунд
    time.sleep(360)
    #Повторный запуск
    res = subprocess.check_output('ftp -A ftp.example.com', shell=True)