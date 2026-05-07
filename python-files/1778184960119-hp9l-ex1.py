# ex1.py

import random

def rand_psw():
    # المجموعات المختلفة
    small_letters = "abcdefghijklmnopqrstuvwxyz"
    capital_letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    numbers = "0123456789"
    special_chars = "~!@#$%^&*"

    # اختيار طول عشوائي بين 10 و 20
    length = random.randint(10, 20)

    password = ""

    # توليد كلمة السر
    for i in range(length):

        # اختيار نوع الحرف بشكل متساوٍ
        choice_type = random.randint(1, 4)

        if choice_type == 1:
            password += random.choice(small_letters)

        elif choice_type == 2:
            password += random.choice(capital_letters)

        elif choice_type == 3:
            password += random.choice(numbers)

        else:
            password += random.choice(special_chars)

    return password


# استدعاء الدالة أكثر من مرة
print(rand_psw())
print(rand_psw())
print(rand_psw())
print(rand_psw())
print(rand_psw())
input("\n اضغط enter للخروج")
