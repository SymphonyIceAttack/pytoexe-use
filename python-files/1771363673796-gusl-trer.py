def calculate_print_run_cost():
    """
    Программа для расчета стоимости тиража изделия
    """
    print("=" * 50)
    print("РАСЧЕТ СТОИМОСТИ ТИРАЖА ИЗДЕЛИЯ")
    print("=" * 50)
    
    # Константы
    MAX_DISCOUNT = 0.5  # Максимальная скидка 50%
    MAX_QUANTITY = 1000  # Максимальный тираж 1000 штук
    
    try:
        # Ввод данных
        base_price = float(input("Введите цену одного изделия (в рублях): "))
        if base_price <= 0:
            print("Ошибка: цена должна быть положительным числом!")
            return
            
        quantity = int(input("Введите тираж (количество изделий): "))
        if quantity <= 0:
            print("Ошибка: тираж должен быть положительным числом!")
            return
        elif quantity > MAX_QUANTITY:
            print(f"Предупреждение: максимальный тираж {MAX_QUANTITY} шт.")
            print(f"Будет выполнен расчет для {MAX_QUANTITY} шт.")
            quantity = MAX_QUANTITY
            
        coefficient = float(input("Введите коэффициент изменения цены (от 1 до 10): "))
        if coefficient < 1 or coefficient > 10:
            print("Ошибка: коэффициент должен быть от 1 до 10!")
            return
            
        # Расчет скидки
        # Используем нелинейную зависимость для гибкости
        discount = MAX_DISCOUNT * (quantity / MAX_QUANTITY) ** (1 / coefficient)
        
        # Применяем скидку
        discounted_price = base_price * (1 - discount)
        
        # Расчет общей стоимости
        total_cost = discounted_price * quantity
        
        # Вывод результатов
        print("\n" + "=" * 50)
        print("РЕЗУЛЬТАТЫ РАСЧЕТА:")
        print("=" * 50)
        print(f"Цена одного изделия: {base_price:.2f} руб.")
        print(f"Тираж: {quantity} шт.")
        print(f"Коэффициент изменения: {coefficient}")
        print(f"Скидка: {discount * 100:.1f}%")
        print(f"Цена со скидкой: {discounted_price:.2f} руб.")
        print(f"ИТОГОВАЯ СТОИМОСТЬ ТИРАЖА: {total_cost:.2f} руб.")
        
        # Дополнительная информация
        print("\n" + "-" * 50)
        print("СПРАВОЧНАЯ ИНФОРМАЦИЯ:")
        print(f"Максимальная возможная скидка: {MAX_DISCOUNT * 100}%")
        print(f"Максимальный тираж: {MAX_QUANTITY} шт.")
        
        # Показываем зависимость скидки от тиража
        if quantity < MAX_QUANTITY:
            print(f"\nПри увеличении тиража до {MAX_QUANTITY} шт.")
            max_discount_for_this_coef = MAX_DISCOUNT * (MAX_QUANTITY / MAX_QUANTITY) ** (1 / coefficient)
            max_price = base_price * (1 - max_discount_for_this_coef) * MAX_QUANTITY
            print(f"скидка составила бы {max_discount_for_this_coef * 100:.1f}%")
            print(f"а стоимость тиража: {max_price:.2f} руб.")
            
    except ValueError:
        print("Ошибка: введите корректные числовые значения!")
        return

def main():
    """Основная функция для запуска программы"""
    while True:
        calculate_print_run_cost()
        
        print("\n" + "-" * 50)
        choice = input("Хотите выполнить новый расчет? (да/нет): ").lower()
        if choice != 'да' and choice != 'yes' and choice != 'y':
            print("Программа завершена.")
            break
        print()

if __name__ == "__main__":
    main()