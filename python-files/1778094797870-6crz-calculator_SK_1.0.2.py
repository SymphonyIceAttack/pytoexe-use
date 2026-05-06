# artifact_sum_calculator.py

# Цены на протоартефакты
PRICES = {
    "1": {"name": "Протоартефакт белый", "price": 3000},
    "2": {"name": "Протоартефакт зелёный", "price": 6000},
    "3": {"name": "Протоартефакт синий", "price": 10000},
    "4": {"name": "Протоартефакт розовый", "price": 23000},
}

def show_prices():
    """Показать цены"""
    print("\n" + "="*55)
    print("📋 ПРАЙС-ЛИСТ")
    print("="*55)
    for key, item in PRICES.items():
        print(f"  {key}. {item['name']:25} {item['price']:>6} руб/шт")
    print("="*55)

def format_number(num):
    """Форматирует число с разделителями"""
    return f"{num:,}".replace(",", " ")

def show_current_cart(quantities):
    """Показать текущую корзину"""
    print("\n📊 ВСЕГО:")
    print("-"*55)
    total = 0
    has_items = False
    
    for key, item in PRICES.items():
        qty = quantities[key]
        if qty > 0:
            has_items = True
            subtotal = item['price'] * qty
            total += subtotal
            print(f"  {item['name']:25} x{qty:>3} шт = {format_number(subtotal):>10} руб")
    
    if not has_items:
        print("  Пока ничего не добавлено")
    
    print("-"*55)
    print(f"  {'ИТОГОВАЯ СУММА:':<36} {format_number(total):>10} руб")
    print("="*55)
    return total

def main():
    # Словарь для хранения количества каждого артефакта
    quantities = {
        "1": 0,  # белый
        "2": 0,  # зелёный
        "3": 0,  # синий
        "4": 0,  # розовый
    }
    
    print("\n" + "🧮"*15)
    print("КАЛЬКУЛЯТОР СУММЫ ПРОТОАРТЕФАКТОВ")
    print("🧮"*15)
    
    print("\n💡 Этот калькулятор СКЛАДЫВАЕТ суммы разных артефактов")
    print("   Вы можете добавлять артефакты по одному или несколько раз")
    print("   Программа автоматически суммирует общую стоимость\n")
    
    while True:
        show_prices()
        total = show_current_cart(quantities)
        
        # Меню действий
        print("\n📌 ДОСТУПНЫЕ ДЕЙСТВИЯ:")
        print("   • 1, 2, 3, 4  - добавить артефакт")
        print("   • '+'          - увеличить последний артефакт на 1")
        print("   • '-'          - уменьшить последний артефакт на 1")
        print("   • 'r'          - обнулить всё")
        print("   • 'd N'        - удалить артефакт под номером N")
        print("   • 'q'          - завершить работу")
        
        choice = input("\n👉 Ваш выбор: ").lower().strip()
        
        # Выход
        if choice == 'q':
            if total > 0:
                print("\n" + "="*55)
                print("📋 ФИНАЛЬНЫЙ РАСЧЁТ:")
                print("="*55)
                for key, item in PRICES.items():
                    qty = quantities[key]
                    if qty > 0:
                        subtotal = item['price'] * qty
                        print(f"  {item['name']}: {qty} шт × {item['price']} руб = {format_number(subtotal)} руб")
                print("-"*55)
                print(f"  ВСЕГО К ОПЛАТЕ: {format_number(total)} руб")
                print("="*55)
            print("\n👋 До свидания!")
            break
        
        # Обнулить всё (бинды r)
        elif choice == 'r':
            for key in quantities:
                quantities[key] = 0
            print("\n✅ Всё обнулено!")
            continue
        
        # Удаление артефакта под номером N (бинды d N)
        elif choice.startswith('d'):
            parts = choice.split()
            if len(parts) == 2:
                try:
                    num = parts[1]
                    if num in PRICES:
                        if quantities[num] > 0:
                            print(f"\n✅ Удалён {PRICES[num]['name']} (было {quantities[num]} шт)")
                            quantities[num] = 0
                        else:
                            print(f"\n⚠️ {PRICES[num]['name']} и так не добавлен")
                    else:
                        print("\n❌ Неверный номер! Используйте 1, 2, 3 или 4")
                except:
                    print("\n❌ Ошибка! Используйте: d 1")
            else:
                print("\n❌ Формат: d [номер] (например: d 2)")
            continue
        
        # Увеличение последнего артефакта на 1 (бинды +)
        elif choice == '+':
            # Находим последний ненулевой артефакт
            last_key = None
            for key in ["4", "3", "2", "1"]:  # ищем с конца
                if quantities[key] > 0:
                    last_key = key
                    break
            
            if last_key:
                quantities[last_key] += 1
                print(f"\n✅ +1 {PRICES[last_key]['name']} (теперь {quantities[last_key]} шт)")
            else:
                print("\n⚠️ Сначала добавьте хотя бы один артефакт")
            continue
        
        # Уменьшение последнего артефакта на 1 (бинды -)
        elif choice == '-':
            last_key = None
            for key in ["4", "3", "2", "1"]:
                if quantities[key] > 0:
                    last_key = key
                    break
            
            if last_key and quantities[last_key] > 0:
                quantities[last_key] -= 1
                if quantities[last_key] == 0:
                    print(f"\n✅ {PRICES[last_key]['name']} удалён из корзины")
                else:
                    print(f"\n✅ -1 {PRICES[last_key]['name']} (теперь {quantities[last_key]} шт)")
            else:
                print("\n⚠️ Нечего уменьшать или артефактов нет")
            continue
        
        # Добавление артефакта (бинды 1, 2, 3, 4)
        elif choice in PRICES:
            try:
                qty = int(input(f"Сколько {PRICES[choice]['name']}? "))
                if qty <= 0:
                    print("❌ Количество должно быть больше 0!")
                    continue
                
                quantities[choice] += qty
                print(f"\n✅ Добавлено {qty} шт {PRICES[choice]['name']}")
                print(f"   Теперь {PRICES[choice]['name']}: {quantities[choice]} шт")
                
            except ValueError:
                print("❌ Ошибка! Введите целое число")
            continue
        
        else:
            print("❌ Неизвестная команда!")
            continue

if __name__ == "__main__":
    main()