
import random

import os

symbols = "qwertyuiopasdfghjklzxcvbnm1234567890QWERTYUIOPASDFGHJKLZXCVBN"
sy = int(input("введи длинну пароля"))
password = ""
for i in range(sy):
   password = password + random.choice(symbols)

os.system("cls" if os.name == "nt" else "clear")
print("="*40)
print("твой пароль:", password)
print("="*40)

input("нажми ебаный Enter,что бы выйти,а не то я удалю папку system32")


