import math
import sys

# Стек истории для отмены (Ctrl+Z)
history_stack = []

def safe_input(prompt):
    """Ввод с поддержкой Ctrl+Z (Windows) или команды 'z' для отмены"""
    try:
        value = input(prompt)
        if value.strip().lower() == 'z':
            if history_stack:
                print(f"\n[Отмена: возвращено значение '{history_stack[-1]}']")
                return history_stack.pop()
            else:
                print("\n[История пуста, нечего отменять]")
                return safe_input(prompt)
        history_stack.append(value)
        return value
    except EOFError:  # Ctrl+Z на Windows
        if history_stack:
            print(f"\n[Ctrl+Z: отмена, возвращено значение '{history_stack[-1]}']")
            return history_stack.pop()
        else:
            print("\n[История пуста, нечего отменять]")
            return safe_input(prompt)

def get_float(prompt):
    """Получить число с поддержкой отмены и заменой запятой на точку"""
    while True:
        value = safe_input(prompt)
        if value is None:
            return None
        try:
            return float(value.replace(',', '.'))
        except ValueError:
            print("Ошибка: введите число (например: 10.5)")

def show_menu():
    print("\n" + "=" * 60)
    print("КАЛЬКУЛЯТОРЫ ДЛЯ ТРУБОПРОВОДНЫХ РАБОТ")
    print("=" * 60)
    print("1. Расчет веса одного погонного метра трубы")
    print("2. Расчет площади наружной поверхности трубы (для АКЗ)")
    print("3. Расчет площади КОНУСА наружной поверхности трубы")
    print("4. Расчет объема трубы")
    print("5. Расчет кол-во метров трубной продукции из тонажа")
    print("6. Расчет объем котлована с откосами")
    print("7. Площадь обертывания трубы (1 вариант - для одной трубы)")
    print("0. Выход")
    print("=" * 60)
    print("Подсказка: Ctrl+Z или команда 'z' - отмена последнего ввода")
    print("Числа вводить с точкой (например: 10.5)")

def calc_weight_per_meter():
    print("\n--- 1. Расчет веса одного погонного метра трубы ---")
    D = get_float("Введите диаметр трубы (мм): ")
    if D is None: return
    t = get_float("Введите толщину стенки (мм): ")
    if t is None: return
    weight = 0.02466 * t * (D - t)
    print(f"\nРезультат: Вес одного п.м. = {weight:.3f} кг")

def calc_surface_area():
    print("\n--- 2. Расчет площади наружной поверхности трубы (для АКЗ) ---")
    D = get_float("Введите диаметр трубы (мм): ")
    if D is None: return
    L = get_float("Введите длину (м, с точкой, например 10.5): ")
    if L is None: return
    area = math.pi * D * L / 1000
    print(f"\nРезультат: Площадь = {area:.3f} м2")

def calc_cone_area():
    print("\n--- 3. Расчет площади КОНУСА наружной поверхности трубы ---")
    D = get_float("Введите диаметр основания конуса (мм): ")
    if D is None: return
    L = get_float("Введите высоту конуса (мм): ")
    if L is None: return
    r = D / 2
    l = math.sqrt(r**2 + L**2)
    area = math.pi * r * l / 1000000
    print(f"\nРезультат: Площадь конуса = {area:.6f} м2")
    print("(формула для боковой поверхности конуса)")

def calc_pipe_volume():
    print("\n--- 4. Расчет объема трубы ---")
    D = get_float("Введите диаметр трубы (мм): ")
    if D is None: return
    L = get_float("Введите длину участка (мм): ")
    if L is None: return
    volume = math.pi * D**2 * L / 4 / 1000000
    print(f"\nРезультат: Объем трубы = {volume:.3f} л")

def calc_meters_from_tonnage():
    print("\n--- 5. Расчет кол-во метров трубной продукции из тонажа ---")
    tons = get_float("Введите кол-во тонн (с точкой, например 0.215): ")
    if tons is None: return
    weight_per_m = get_float("Введите вес 1 п.м. трубы (кг, с точкой): ")
    if weight_per_m is None: return
    meters = tons * 1000 / weight_per_m
    print(f"\nРезультат: Кол-во метров = {meters:.3f} м")

def calc_trench_volume():
    print("\n--- 6. Расчет объем котлована с откосами ---")
    a = get_float("Ширина котлована по дну (м, с точкой, например 13.0): ")
    if a is None: return
    b = get_float("Длина котлована по дну (м, с точкой, например 12.9): ")
    if b is None: return
    c = get_float("Ширина котлована по верху (м, с точкой, например 20.9): ")
    if c is None: return
    d = get_float("Длина котлована по верху (м, с точкой, например 20.8): ")
    if d is None: return
    h = get_float("Глубина котлована (м, с точкой, например 3.95): ")
    if h is None: return
    S1 = a * b
    S2 = c * d
    S_mid = ((a + c) / 2) * ((b + d) / 2)
    volume = h / 6 * (S1 + S2 + 4 * S_mid)
    print(f"\nРезультат: Объем котлована = {volume:.3f} м³")

def calc_wrapping_area_1():
    print("\n--- 7. Площадь обертывания трубы (1 вариант - для одной трубы) ---")
    D = get_float("Введите диаметр трубы D (мм): ")
    if D is None: return
    t = get_float("Введите толщину изоляции t (мм): ")
    if t is None: return
    L = get_float("Введите длину участка изоляции L (м, с точкой, например 65.3): ")
    if L is None: return
    
    Sr = math.pi * D * L / 1000
    Spi = math.pi * (D + 2 * t) * L / 1000
    Vi = math.pi * ((D/2 + t)**2 - (D/2)**2) * L / 1000000
    
    print(f"\nРезультаты:")
    print(f"  Sr (площадь обертывания): {Sr:.3f} м2")
    print(f"  Spi (площадь покровного слоя): {Spi:.3f} м2")
    print(f"  Vi (объем изоляции): {Vi:.3f} м3")

def main():
    while True:
        show_menu()
        choice = safe_input("\nВыберите калькулятор (0-7): ")
        
        if choice is None:
            continue
        if choice == '0':
            print("\nВыход из программы.")
            break
        elif choice == '1':
            calc_weight_per_meter()
        elif choice == '2':
            calc_surface_area()
        elif choice == '3':
            calc_cone_area()
        elif choice == '4':
            calc_pipe_volume()
        elif choice == '5':
            calc_meters_from_tonnage()
        elif choice == '6':
            calc_trench_volume()
        elif choice == '7':
            calc_wrapping_area_1()
        else:
            print("Неверный выбор. Попробуйте снова.")
        
        input("\nНажмите Enter для продолжения...")
        history_stack.clear()  # Очищаем историю между расчетами

if __name__ == "__main__":
    main()