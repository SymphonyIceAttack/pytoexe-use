import math

def show_menu():
    print("=" * 60)
    print("КАЛЬКУЛЯТОРЫ ДЛЯ ТРУБОПРОВОДНЫХ РАБОТ")
    print("=" * 60)
    print("1. Расчет веса одного погонного метра трубы")
    print("2. Расчет площади наружной поверхности трубы")
    print("3. Расчет площади КОНУСА наружной поверхности трубы")
    print("4. Расчет объема трубы")
    print("5. Расчет кол-во метров трубной продукции из тонажа")
    print("6. Расчет объем котлована с откосами")
    print("7. Площадь обертывания трубы (1 вариант - для одной трубы)")
    print("8. Площадь обертывания труб (2 вариант - для 2-х и более труб)")
    print("0. Выход")
    print("=" * 60)

def calc_weight_per_meter():
    print("\n--- Расчет веса одного погонного метра трубы ---")
    D = float(input("Введите диаметр трубы (мм): "))
    t = float(input("Введите толщину стенки (мм): "))
    # Формула: вес = 0.02466 × t × (D - t)
    weight = 0.02466 * t * (D - t)
    print(f"Вес одного п.м.: {weight:.3f} кг")

def calc_surface_area():
    print("\n--- Расчет площади наружной поверхности трубы ---")
    D = float(input("Введите диаметр трубы (мм): "))
    L = float(input("Введите длину (м): "))
    # Формула: S = π × D × L / 1000
    area = math.pi * D * L / 1000
    print(f"Площадь, м2: {area:.3f}")

def calc_cone_area():
    print("\n--- Расчет площади КОНУСА наружной поверхности трубы ---")
    D = float(input("Введите диаметр основания конуса (мм): "))
    L = float(input("Введите высоту конуса (мм): "))
    # Формула боковой поверхности конуса: S = π × r × l
    r = D / 2
    l = math.sqrt(r**2 + L**2)  # образующая
    area = math.pi * r * l / 1000000  # перевод мм² в м²
    print(f"Площадь конуса, м2: {area:.6f}")
    print("(Примечание: формула для боковой поверхности конуса)")

def calc_pipe_volume():
    print("\n--- Расчет объема трубы ---")
    D = float(input("Введите диаметр трубы (мм): "))
    L = float(input("Введите длину участка (мм): "))
    # Формула: V = π × D² × L / 4 / 1000000 (в литрах)
    volume = math.pi * D**2 * L / 4 / 1000000
    print(f"Объем трубы: {volume:.3f} л")

def calc_meters_from_tonnage():
    print("\n--- Расчет кол-во метров трубной продукции из тонажа ---")
    tons = float(input("Введите кол-во тонн: "))
    weight_per_m = float(input("Введите вес 1 п.м. трубы (кг): "))
    # Формула: meters = tons × 1000 / weight_per_m
    meters = tons * 1000 / weight_per_m
    print(f"Кол-во метров: {meters:.3f} м")

def calc_trench_volume():
    print("\n--- Расчет объем котлована с откосами ---")
    a = float(input("Ширина котлована по дну (м): "))
    b = float(input("Длина котлована по дну (м): "))
    c = float(input("Ширина котлована по верху (м): "))
    d = float(input("Длина котлована по верху (м): "))
    h = float(input("Глубина котлована (м): "))
    # Формула усеченной пирамиды: V = h/6 × (S1 + S2 + 4×Sср)
    S1 = a * b
    S2 = c * d
    S_mid = ((a + c) / 2) * ((b + d) / 2)
    volume = h / 6 * (S1 + S2 + 4 * S_mid)
    print(f"Объем котлована: {volume:.3f} м³")

def calc_wrapping_area_1():
    print("\n--- Площадь обертывания трубы (1 вариант) ---")
    D = float(input("Введите диаметр трубы D (мм): "))
    t = float(input("Введите толщину изоляции t (мм): "))
    L = float(input("Введите длину участка изоляции L (м): "))
    
    # Sr - площадь обертывания (без изоляции)
    Sr = math.pi * D * L / 1000
    # Spi - площадь покровного слоя изоляции
    Spi = math.pi * (D + 2 * t) * L / 1000
    # Vi - объем изоляции
    Vi = math.pi * ((D/2 + t)**2 - (D/2)**2) * L / 1000000
    
    print(f"Sr (площадь обертывания): {Sr:.3f} м2")
    print(f"Spi (площадь покровного слоя): {Spi:.3f} м2")
    print(f"Vi (объем изоляции): {Vi:.3f} м3")

def calc_wrapping_area_2():
    print("\n--- Площадь обертывания труб (2 вариант - для 2-х и более труб) ---")
    D1 = float(input("D1 - диаметр крайних труб (м): "))
    D2 = float(input("D2 - диаметр внутренней трубы (м): "))
    M = float(input("M - расстояние между осями труб (м): "))
    t = float(input("t - толщина теплоизоляции (м): "))
    p = float(input("p - расстояние между трубами (м): "))
    L = float(input("Длина участка изоляции L (м): "))
    
    # Приближенные формулы для группы труб
    # Sr - площадь обертывания (периметр охвата × длина)
    # Для трех труб в ряд: периметр ≈ 2×M + π×D1
    perimeter = 2 * M + math.pi * D1
    Sr = perimeter * L
    
    # Spi - площадь покровного слоя с изоляцией
    D1_izol = D1 + 2 * t
    perimeter_izol = 2 * M + math.pi * D1_izol
    Spi = perimeter_izol * L
    
    # Vi - объем изоляции
    Vi = math.pi * ((D1/2 + t)**2 - (D1/2)**2) * L * 2 + \
         math.pi * ((D2/2 + t)**2 - (D2/2)**2) * L
    
    print(f"Sr (площадь обертывания): {Sr:.3f} м2")
    print(f"Spi (площадь покровного слоя): {Spi:.3f} м2")
    print(f"Vi (объем изоляции): {Vi:.3f} м3")
    print("(Примечание: формулы приближенные, уточните по проекту)")

def main():
    while True:
        show_menu()
        choice = input("Выберите калькулятор (0-8): ")
        
        if choice == '1':
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
        elif choice == '8':
            calc_wrapping_area_2()
        elif choice == '0':
            print("Выход из программы.")
            break
        else:
            print("Неверный выбор. Попробуйте снова.")
        
        input("\nНажмите Enter для продолжения...")

if __name__ == "__main__":
    main()