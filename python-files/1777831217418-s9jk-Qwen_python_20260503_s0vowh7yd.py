import sys
import io
import re

def normalize(text):
    """Приводит ответ к единому формату для проверки"""
    return text.strip().lower().replace(',', ' ').replace(';', ' ').replace('.', '')

def run_test():
    print("="*50)
    print("ПРОВЕРОЧНАЯ РАБОТА: ОСНОВЫ PYTHON (9 КЛАСС)")
    print("Введите ответы аккуратно. Регистр и лишние пробелы игнорируются.")
    print("="*50)
    
    score = 0
    max_score = 15

    # ================= ЧАСТЬ 1 =================
    print("\n🔹 ЧАСТЬ 1. ТЕСТОВЫЕ ЗАДАНИЯ (по 1 баллу)")
    
    q1 = input("1. Кто является создателем языка Python? (а/б/в/г) → ").strip().lower()
    if q1 in ['б', 'b', '2']: score += 1

    q2 = input("2. Как называется режим IDLE, где программа записывается в .py и выполняется целиком? (а/б/в/г) → ").strip().lower()
    if q2 in ['б', 'b', '2']: score += 1

    q3 = input("3. Какое значение принимает d = 10 < 5? (а/б/в/г) → ").strip().lower()
    if q3 in ['г', 'g', 'false', 'ложь', '4']: score += 1

    q4 = input("4. Какая операция возвращает целое частное от деления? (а/б/в/г) → ").strip().lower()
    if q4 in ['б', 'b', '//', '2']: score += 1

    q5 = input("5. Различаются ли в Python прописные и строчные буквы в именах переменных? (да/нет) → ").strip().lower()
    if 'нет' in q5 or 'no' in q5: score += 1

    # ================= ЧАСТЬ 2 =================
    print("\n🔹 ЧАСТЬ 2. ИМЕНА И ТИПЫ ДАННЫХ (4 балла)")
    
    q6 = input("6. Введите номера ПРАВИЛЬНЫХ имён через пробел (1.polnaja_summa 2.2as 3.and 4._k1 5.Domby&Son) → ").strip().lower()
    # Ожидаем "1 4" в любом порядке
    parts = normalize(q6).split()
    if {'1', '4'} <= set(parts) and len(parts) == 2: score += 1
    elif {'1', '4'}.issubset(set(parts)): score += 0.5 # Частичный балл

    q7 = input("7. Типы данных для: a=25, b='Book', c=3.14, d=(5>2). Введите 4 типа через пробел → ").strip().lower()
    parts = normalize(q7).split()
    expected = ['int', 'str', 'float', 'bool']
    if parts == expected: score += 1
    elif len(parts) == 4 and all(p in expected for p in parts): score += 0.5

    q8 = input("8. Какой тип результата даёт операция деления '/'? (int/float/str/bool) → ").strip().lower()
    if q8 == 'float': score += 1

    # ================= ЧАСТЬ 3 =================
    print("\n🔹 ЧАСТЬ 3. НАЙДИ И ИСПРАВЬ ОШИБКУ (3 балла)")
    
    print("9. Дано: s = 2as")
    q9 = input("   Как исправить? Введите правильный вариант присваивания → ").strip()
    # Проверяем, что имя не начинается с цифры и это валидное присваивание
    if re.match(r"^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*=", q9): score += 1
    
    print("10. Дано: x = 7; y = 2; res = x / y  # требуется целое число")
    q10 = input("    Как исправить оператор присваивания? Введите строку → ").strip()
    if '//' in q10 and not '/' in q10.replace('//', ''): score += 1

    print("11. Дано: age = input(...); print('Возраст: ' + (age + 1))")
    q11 = input("    Введите исправленную строку вывода print → ").strip()
    # Проверяем наличие преобразования типов
    if ('int(' in q11 or 'str(' in q11) and ('age' in q11): score += 1

    # ================= ЧАСТЬ 4 =================
    print("\n🔹 ЧАСТЬ 4. ПРАКТИКА В IDLE (3 балла)")
    print("💡 Запустите ваш код в IDLE, протестируйте и введите РЕЗУЛЬТАТЫ работы программ.")
    
    # Задача А
    print("Задача А. Ввод: 12 и 5. Какое должно быть на экране? (сумма, разность, целая часть деления)")
    q12 = input("   Введите 3 числа через пробел → ").strip()
    if '17' in q12 and '7' in q12 and '2' in q12: score += 1.5

    # Задача Б
    print("Задача Б. Ввод: 15. Что выведет программа? (True/False/1/0)")
    q13 = input("   Введите результат → ").strip().lower()
    if 'true' in q13 or '1' in q13: score += 1.5

    # ================= ИТОГИ =================
    print("\n" + "="*50)
    print("📊 РЕЗУЛЬТАТЫ ПРОВЕРКИ")
    print(f"✅ Набрано баллов: {score} из {max_score}")
    
    if score >= 13: grade = 5
    elif score >= 10: grade = 4
    elif score >= 7: grade = 3
    else: grade = 2
    
    print(f"🏆 Итоговая оценка: {grade}")
    print("="*50)
    print("💡 Примечание для учителя: Часть 4 проверяется по результатам выполнения в IDLE.")
    print("   Для полной автоматической проверки кода рекомендуется использовать систему тестирования или ручную проверку логики.")

if __name__ == "__main__":
    try:
        run_test()
    except KeyboardInterrupt:
        print("\n⚠️ Тест прерван учеником.")
    except Exception as e:
        print(f"\n❌ Произошла ошибка: {e}")