prices = {
    1: 3400,     
    2: 6000,     
    3: 10400,   
    4: 23000     
}

names = {
    1: "Протоартефакт белый",
    2: "Протоартефакт зелёный",
    3: "Протоартефакт синий",
    4: "Протоартефакт розовый"
}

print("\n=== КАЛЬКУЛЯТОР ПРОТОАРТЕФАКТОВ (НОВЫЕ ЦЕНЫ) ===\n")
print("1. Белый  - 3 400 руб/шт")
print("2. Зелёный - 6 000 руб/шт")
print("3. Синий   - 10 400 руб/шт")
print("4. Розовый - 23 000 руб/шт")

while True:
    try:
        choice = int(input("\nВыберите артефакт (1-4): "))
        if choice not in prices:
            print("Ошибка! Введите число от 1 до 4.")
            continue
        
        quantity = int(input("Введите количество: "))
        if quantity <= 0:
            print("Ошибка! Количество должно быть больше 0.")
            continue
        
        total = prices[choice] * quantity
        
        print("\n" + "-"*45)
        print(f"{names[choice]}")
        print(f"Цена: {prices[choice]:>6} руб/шт")
        print(f"Количество: {quantity:>6} шт")
        print(f"ИТОГО: {total:>8} руб")
        print("-"*45)
        
        again = input("\nПосчитать ещё? (да/нет): ").lower()
        if again not in ['да', 'д', 'yes', 'y']:
            print("\nСпасибо за использование!")
            break
            
    except ValueError:
        print("Ошибка! Введите число.")
        