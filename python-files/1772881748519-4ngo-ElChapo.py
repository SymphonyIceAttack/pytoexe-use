import time 
import os
import sys

text = "Эль Чапо Зачем Ты Пытаешься Дотянуться До Прилавка Братан Зайка Вижу Смотришь На Меня"
words = text.split()

for i, word in enumerate(words):
    print(word, end= ' ', flush=True)
    if word == "Чапо" and i < len(words) - 1 and words[i + 1] == "Зачем":
        time.sleep(2)
    elif word == "Братан" and i < len(words) - 1 and words[i + 1] == "Зайка":
        time.sleep(2)
    else:
        time.sleep(0.5)

print()

input("Нажми Enter для выхода...")