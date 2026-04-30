import random
import string

letters = string.ascii_letters
digits = string.digits
symbols = '!@#$%^&*()_+-=[]{}|;:,.<>?'

all_characters = letters + digits + symbols

print("=== ГЕНЕРАТОР СЛУЧАЙНЫХ ПАРОЛЕЙ ===")
print()

while True:
    try:
        length = int(input("Введите длину пароля (от 8 до 20 символов): "))
        if 8 <= length <= 20:
            break
        else:
            print("Длина должна быть от 8 до 20 символов! Попробуйте снова.")
    except ValueError:
        print("Пожалуйста, введите число!")

while True:
    try:
        count = int(input("Сколько паролей сгенерировать? (1-10): "))
        if 1 <= count <= 10:
            break
        else:
            print("Количество должно быть от 1 до 10!")
    except ValueError:
        print("Пожалуйста, введите число!")

def generate_password(length):
    """Функция для генерации одного пароля"""
    password = ''
    for i in range(length):
        random_char = random.choice(all_characters)
        password += random_char
    return password

print("\n" + "="*40)
print("Ваши новые пароли:")
print("="*40)

for i in range(count):
    password = generate_password(length)
    print(f"Пароль {i+1}: {password}")

print("="*40)
print("Сохраните эти пароли в надежном месте!")
print("Не используйте один пароль для разных сайтов!")

input("\nНажмите Enter для выхода...")
