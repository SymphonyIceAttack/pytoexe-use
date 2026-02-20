def calculate_print_cost():
    """
    Программа для расчета стоимости тиража изделия
    Стоимость доп. услуг указывается за каждое изделие и не участвует в расчете скидки
    """
    
    # ПАРАМЕТРЫ СКИДОК ДЛЯ ГИБКОЙ НАСТРОЙКИ
    # ========================================
    THRESHOLD_1 = 1000      # Первый порог тиража (шт.)
    THRESHOLD_2 = 3000      # Второй порог тиража (шт.) - МАКСИМАЛЬНЫЙ
    DISCOUNT_AT_THRESHOLD_1 = 50   # Скидка при первом пороге (%)
    DISCOUNT_AT_THRESHOLD_2 = 75   # Скидка при втором пороге (%) - МАКСИМАЛЬНАЯ
    # ========================================
    
    print("=" * 50)
    print("РАСЧЕТ СТОИМОСТИ ТИРАЖА ИЗДЕЛИЯ")
    print("=" * 50)
    
    # Ввод данных
    try:
        # Цена одного изделия
        price_per_item = float(input("Введите цену одного изделия (в рублях): "))
        if price_per_item <= 0:
            print("Ошибка: цена должна быть положительным числом!")
            return
        
        # Тираж
        quantity = int(input("Введите тираж (количество изделий): "))
        if quantity <= 0:
            print("Ошибка: тираж должен быть положительным числом!")
            return
        
        # Стоимость дополнительных услуг на одно изделие (без скидки)
        extra_per_item = float(input("Введите стоимость доп. услуг на одно изделие (в рублях): "))
        if extra_per_item < 0:
            print("Ошибка: стоимость доп. услуг не может быть отрицательной!")
            return
        
        # Расчет базовой стоимости (только изделия, без доп. услуг)
        base_cost = price_per_item * quantity
        print(f"\nБазовая стоимость тиража (изделия): {base_cost:.2f} руб.")
        
        # Расчет общей стоимости доп. услуг (без скидки)
        total_extra = extra_per_item * quantity
        print(f"Общая стоимость доп. услуг: {total_extra:.2f} руб.")
        
        # Расчет скидки в зависимости от тиража (ступенчатая система)
        discount = 0
        
        if quantity >= THRESHOLD_2:
            discount = DISCOUNT_AT_THRESHOLD_2
            print(f"Тираж от {THRESHOLD_2} шт. - скидка {discount}% (МАКСИМАЛЬНАЯ)")
        elif quantity >= THRESHOLD_1:
            # Для тиража от THRESHOLD_1 до THRESHOLD_2-1 рассчитываем прогрессивную скидку
            # Формула: DISCOUNT_AT_THRESHOLD_1% + (тираж - THRESHOLD_1) / (THRESHOLD_2 - THRESHOLD_1) * (DISCOUNT_AT_THRESHOLD_2 - DISCOUNT_AT_THRESHOLD_1)%
            discount_range = DISCOUNT_AT_THRESHOLD_2 - DISCOUNT_AT_THRESHOLD_1
            quantity_range = THRESHOLD_2 - THRESHOLD_1
            discount = DISCOUNT_AT_THRESHOLD_1 + ((quantity - THRESHOLD_1) / quantity_range) * discount_range
            print(f"Тираж {quantity} шт. - скидка {discount:.1f}%")
        elif quantity > 0:
            # Для тиража меньше THRESHOLD_1 - пропорциональная скидка до DISCOUNT_AT_THRESHOLD_1%
            discount = (quantity / THRESHOLD_1) * DISCOUNT_AT_THRESHOLD_1
            print(f"Тираж {quantity} шт. - скидка {discount:.1f}%")
        
        # Расчет стоимости изделий со скидкой
        discounted_cost = base_cost * (1 - discount / 100)
        
        # Итоговая стоимость (изделия со скидкой + доп. услуги без скидки)
        total_cost = discounted_cost + total_extra
        
        # Вывод результатов
        print("\n" + "=" * 50)
        print("РЕЗУЛЬТАТЫ РАСЧЕТА:")
        print("=" * 50)
        print(f"Цена одного изделия: {price_per_item:.2f} руб.")
        print(f"Стоимость доп. услуг на одно изделие: {extra_per_item:.2f} руб.")
        print(f"Тираж: {quantity} шт.")
        print(f"Общая стоимость доп. услуг: {total_extra:.2f} руб.")
        print(f"Скидка: {discount:.1f}%")
        print(f"Стоимость изделий со скидкой: {discounted_cost:.2f} руб.")
        print(f"ИТОГОВАЯ СТОИМОСТЬ: {total_cost:.2f} руб.")
        
        # Дополнительная информация
        print("\n" + "-" * 50)
        print("Справочная информация по скидкам:")
        print(f"• До {THRESHOLD_1} шт. - до {DISCOUNT_AT_THRESHOLD_1}% (пропорционально тиражу)")
        print(f"• {THRESHOLD_1} шт. - {DISCOUNT_AT_THRESHOLD_1}%")
        print(f"• От {THRESHOLD_1} до {THRESHOLD_2} шт. - от {DISCOUNT_AT_THRESHOLD_1}% до {DISCOUNT_AT_THRESHOLD_2}% (прогрессивно)")
        print(f"• {THRESHOLD_2} шт. и более - {DISCOUNT_AT_THRESHOLD_2}% (МАКСИМАЛЬНАЯ)")
        
        # Расчет средней стоимости за единицу с учетом всего
        if quantity > 0:
            cost_per_unit = total_cost / quantity
            print(f"\nСредняя стоимость за единицу с учетом всего: {cost_per_unit:.2f} руб.")
            print(f"(из них: изделие - {price_per_item:.2f} руб., доп. услуги - {extra_per_item:.2f} руб.)")
        
        # Спрашиваем, нужно ли подготовить информацию для клиента
        print("\n" + "-" * 50)
        print_for_client = input("Сформировать информацию для отправки клиенту? (да/нет): ").lower()
        
        if print_for_client in ['да', 'yes', 'y', 'д']:
            generate_client_info(price_per_item, extra_per_item, quantity, 
                               discount, discounted_cost, total_extra, total_cost,
                               THRESHOLD_1, THRESHOLD_2, DISCOUNT_AT_THRESHOLD_1, DISCOUNT_AT_THRESHOLD_2)
        
    except ValueError:
        print("Ошибка: введите корректные числовые значения!")
        return
    
    print("=" * 50)

def generate_client_info(price_per_item, extra_per_item, quantity, 
                        discount, discounted_cost, total_extra, total_cost,
                        THRESHOLD_1, THRESHOLD_2, DISCOUNT_AT_THRESHOLD_1, DISCOUNT_AT_THRESHOLD_2):
    """
    Генерация информации для клиента
    """
    
    print("\n" + "=" * 50)
    print("ПОДГОТОВКА ИНФОРМАЦИИ ДЛЯ КЛИЕНТА")
    print("=" * 50)
    
    # Ввод дополнительной информации от пользователя
    item_name = input("Введите название изделия (например, 'Визитки'): ").strip()
    
    # Проверка на наличие дополнительных услуг
    extra_name = ""
    if extra_per_item > 0:
        extra_name = input("Введите название дополнительных услуг (например, 'Ламинация'): ").strip()
        if not extra_name:
            extra_name = "Дополнительные услуги"
    
    # Формирование текста для клиента с информацией о скидках
    discount_info = ""
    if quantity >= THRESHOLD_2:
        discount_info = f"МАКСИМАЛЬНАЯ СКИДКА {DISCOUNT_AT_THRESHOLD_2}% (для тиража от {THRESHOLD_2} шт.)"
    elif quantity >= THRESHOLD_1:
        discount_info = f"ПРОГРЕССИВНАЯ СКИДКА {discount:.1f}% (при тираже от {THRESHOLD_1} до {THRESHOLD_2} шт.)"
    else:
        discount_info = f"СКИДКА {discount:.1f}% (пропорционально тиражу до {THRESHOLD_1} шт.)"
    
    client_text = f"""
{"=" * 60}
                 КОММЕРЧЕСКОЕ ПРЕДЛОЖЕНИЕ
{"=" * 60}

Уважаемый клиент!

Мы подготовили для вас расчет стоимости тиража.

{"-" * 60}
ДЕТАЛИ ЗАКАЗА:
{"-" * 60}
• Изделие: {item_name}
• Тираж: {quantity} шт."""

    if extra_per_item > 0 and extra_name:
        client_text += f"""
• Дополнительные услуги: {extra_name}"""

    client_text += f"""

{"-" * 60}
РАСЧЕТ СТОИМОСТИ:
{"-" * 60}
• Стоимость одного изделия: {price_per_item:.2f} руб.
• Стоимость всех изделий: {price_per_item * quantity:.2f} руб."""

    if extra_per_item > 0:
        client_text += f"""
• Стоимость дополнительных услуг (за шт.): {extra_per_item:.2f} руб.
• Общая стоимость дополнительных услуг: {total_extra:.2f} руб."""

    client_text += f"""
• {discount_info}
• Стоимость изделий с учетом скидки: {discounted_cost:.2f} руб.

{"-" * 60}
ИТОГОВАЯ СТОИМОСТЬ ЗАКАЗА:
{"-" * 60}
{total_cost:.2f} руб. ({total_cost / quantity:.2f} руб. за единицу)
{"=" * 60}

Дополнительная информация:
• В расчет включена прогрессивная система скидок в зависимости от тиража
• Дополнительные услуги оплачиваются без скидки
• Стоимость указана в рублях, включая НДС

Система скидок:
• До {THRESHOLD_1} шт. - до {DISCOUNT_AT_THRESHOLD_1}% (пропорционально тиражу)
• {THRESHOLD_1} шт. - {DISCOUNT_AT_THRESHOLD_1}%
• От {THRESHOLD_1} до {THRESHOLD_2} шт. - от {DISCOUNT_AT_THRESHOLD_1}% до {DISCOUNT_AT_THRESHOLD_2}% (прогрессивно)
• {THRESHOLD_2} шт. и более - {DISCOUNT_AT_THRESHOLD_2}% (МАКСИМАЛЬНАЯ)

С уважением,
Ваша типография

{"=" * 60}
"""
    
    # Вывод текста для клиента
    print("\n" + client_text)
    
    # Спрашиваем, сохранить ли в файл
    save_to_file = input("Сохранить расчет в текстовый файл? (да/нет): ").lower()
    if save_to_file in ['да', 'yes', 'y', 'д']:
        # Создаем безопасное имя файла
        filename = f"raschet_{item_name.lower().replace(' ', '_')}_{quantity}шт.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(client_text)
        print(f"✅ Расчет сохранен в файл: {filename}")

def main():
    """Основная функция для запуска программы"""
    
    while True:
        calculate_print_cost()
        
        # Спрашиваем, хочет ли пользователь выполнить еще один расчет
        answer = input("\nХотите выполнить еще один расчет? (да/нет): ").lower()
        if answer not in ['да', 'yes', 'y', 'д']:
            print("Программа завершена. Спасибо за использование!")
            break
        print("\n" * 2)

if __name__ == "__main__":
    main()