#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Программа для решения уравнения: ((f*256 + z)*256 + y + x*0.01) * k = a
Поддерживает дневной (a) и ночной (a1) тарифы - параллельные расчеты
"""

import os
import sys
import time

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def find_solutions_optimized_v2(a, k, tolerance=1.0):
    """
    Оптимизированная версия 2.0 (без NumPy, но быстрая)
    """
    solutions = []
    a_float = float(a)
    k_float = float(k)
    
    target_int = int(round(a_float))
    target_value = target_int / k_float
    
    print(f"\n🔍 Оптимизированный поиск V2 для a={a}, k={k}...")
    print(f"   Ищем совпадение с целым числом: {target_int}")
    start_time = time.time()
    
    # Предвычисляем все base_fz
    base_fz_cache = {}
    for f in range(256):
        for z in range(256):
            base_fz_cache[(f, z)] = (f * 256 + z) * 256
    
    total_iterations = 256 * 256 * 256
    iteration = 0
    last_percent = -1
    batch_size = 1000  # Размер пакета для вывода прогресса
    
    for f in range(256):
        for z in range(256):
            base_fz = base_fz_cache[(f, z)]
            
            # Оптимизация: вычисляем диапазон y, который может дать решение
            # x должен быть от 0 до 255, значит:
            # base_fz + y должно быть примерно равно target_value ± 2.55
            min_base = target_value - 2.55
            max_base = target_value + 2.55
            
            min_y = max(0, int(min_base - base_fz))
            max_y = min(255, int(max_base - base_fz) + 1)
            
            for y in range(min_y, max_y + 1):
                iteration += 1
                
                if iteration % batch_size == 0:
                    percent = (iteration * 100) // total_iterations
                    if percent != last_percent:
                        last_percent = percent
                        print(f"\r⏳ Прогресс: {percent}%", end="", flush=True)
                
                base_value = base_fz + y
                
                # Быстрое вычисление x
                x_float = (target_value - base_value) * 100
                x = int(round(x_float))
                
                if 0 <= x <= 255:
                    expr = base_value + x * 0.01
                    result = expr * k_float
                    result_int = int(round(result))
                    
                    diff = abs(result_int - target_int)
                    if diff <= tolerance:
                        solutions.append((x, y, z, f, result, diff))
    
    print("\r" + " " * 40 + "\r", end="")
    elapsed_time = time.time() - start_time
    print(f"✅ Поиск завершен за {elapsed_time:.2f} сек.")
    
    solutions.sort(key=lambda s: s[5])
    return solutions

def print_header():
    print("=" * 110)
    print("   ПРОГРАММА ДЛЯ ПОДБОРА ЗНАЧЕНИЙ X, Y, Z, F".center(110))
    print("   (С ПАРАЛЛЕЛЬНЫМ РАСЧЕТОМ ДНЕВНОГО И НОЧНОГО ТАРИФОВ)".center(110))
    print("=" * 110)

def print_dual_solution_table(solutions_day, solutions_night, a, a1, k):
    """Вывод таблицы с параллельными результатами для двух тарифов"""
    
    print("\n" + "═" * 110)
    print("   РЕЗУЛЬТАТЫ ПАРАЛЛЕЛЬНОГО РАСЧЕТА".center(110))
    print("═" * 110)
    
    # Вывод для дневного тарифа
    if not solutions_day:
        print("\n❌ ДНЕВНОЙ ТАРИФ: решений не найдено!")
    else:
        print(f"\n🌞 ДНЕВНОЙ ТАРИФ (a = {a}):")
        print(f"   Найдено решений: {len(solutions_day)}")
        
        show_count = min(len(solutions_day), 10)
        
        print("\n┌" + "─" * 98 + "┐")
        print("│ {:^4} │ {:^8} │ {:^8} │ {:^8} │ {:^8} │ {:^12} │ {:^15} │ {:^12} │".format(
            "№", "X", "Y", "Z", "F", "РЕЗУЛЬТАТ", "ЦЕЛОЕ (a)", "ОТКЛОНЕНИЕ"))
        print("├" + "─" * 4 + "┼" + "─" * 10 + "┼" + "─" * 10 + "┼" + "─" * 10 + "┼" + "─" * 10 + "┼" + "─" * 14 + "┼" + "─" * 17 + "┼" + "─" * 14 + "┤")
        
        target_int = int(round(a))
        
        for i, (x, y, z, f, result, diff) in enumerate(solutions_day[:show_count], 1):
            result_int = int(round(result))
            marker = "★" if diff == 0 else " "
            print("│ {:^4} │ {:^8} │ {:^8} │ {:^8} │ {:^8} │ {:>12.4f} │ {:>15} {:^1} │ {:>12.4f} │".format(
                i, x, y, z, f, result, result_int, marker, diff))
        
        if len(solutions_day) > show_count:
            print("│ {:^98} │".format(f"... и еще {len(solutions_day) - show_count} решений"))
        
        print("└" + "─" * 4 + "┴" + "─" * 10 + "┴" + "─" * 10 + "┴" + "─" * 10 + "┴" + "─" * 10 + "┴" + "─" * 14 + "┴" + "─" * 17 + "┴" + "─" * 14 + "┘")
        
        # Лучшее решение для дневного тарифа
        best_day = solutions_day[0]
        print(f"\n🏆 Лучшее решение для ДНЕВНОГО тарифа: x={best_day[0]}, y={best_day[1]}, z={best_day[2]}, f={best_day[3]}")
        print(f"   Результат: {best_day[4]:.4f}, отклонение: {best_day[5]}")
    
    # Вывод для ночного тарифа
    if not solutions_night:
        print("\n❌ НОЧНОЙ ТАРИФ: решений не найдено!")
    else:
        print(f"\n🌙 НОЧНОЙ ТАРИФ (a1 = {a1}):")
        print(f"   Найдено решений: {len(solutions_night)}")
        
        show_count = min(len(solutions_night), 10)
        
        print("\n┌" + "─" * 98 + "┐")
        print("│ {:^4} │ {:^8} │ {:^8} │ {:^8} │ {:^8} │ {:^12} │ {:^15} │ {:^12} │".format(
            "№", "X", "Y", "Z", "F", "РЕЗУЛЬТАТ", "ЦЕЛОЕ (a1)", "ОТКЛОНЕНИЕ"))
        print("├" + "─" * 4 + "┼" + "─" * 10 + "┼" + "─" * 10 + "┼" + "─" * 10 + "┼" + "─" * 10 + "┼" + "─" * 14 + "┼" + "─" * 17 + "┼" + "─" * 14 + "┤")
        
        target_int = int(round(a1))
        
        for i, (x, y, z, f, result, diff) in enumerate(solutions_night[:show_count], 1):
            result_int = int(round(result))
            marker = "★" if diff == 0 else " "
            print("│ {:^4} │ {:^8} │ {:^8} │ {:^8} │ {:^8} │ {:>12.4f} │ {:>15} {:^1} │ {:>12.4f} │".format(
                i, x, y, z, f, result, result_int, marker, diff))
        
        if len(solutions_night) > show_count:
            print("│ {:^98} │".format(f"... и еще {len(solutions_night) - show_count} решений"))
        
        print("└" + "─" * 4 + "┴" + "─" * 10 + "┴" + "─" * 10 + "┴" + "─" * 10 + "┴" + "─" * 10 + "┴" + "─" * 14 + "┴" + "─" * 17 + "┴" + "─" * 14 + "┘")
        
        # Лучшее решение для ночного тарифа
        best_night = solutions_night[0]
        print(f"\n🏆 Лучшее решение для НОЧНОГО тарифа: x={best_night[0]}, y={best_night[1]}, z={best_night[2]}, f={best_night[3]}")
        print(f"   Результат: {best_night[4]:.4f}, отклонение: {best_night[5]}")
    
    print("\n" + "═" * 110)

def main():
    while True:
        clear_screen()
        print_header()
        
        print("\n" + "─" * 110)
        
        try:
            # Ввод дневного тарифа a
            a_input = input("\n🌞 Введите значение a (дневной тариф): ").strip()
            if a_input.lower() in ['exit', 'quit', 'q', 'выход', '']:
                print("\n👋 До свидания!")
                break
            a_input = a_input.replace(',', '.')
            a = float(a_input)
            
            # Ввод ночного тарифа a1
            a1_input = input("🌙 Введите значение a1 (ночной тариф): ").strip()
            a1_input = a1_input.replace(',', '.')
            a1 = float(a1_input)
            
            # Ввод коэффициента k
            k_input = input("🔄 Введите коэффициент k (общий для обоих тарифов): ").strip()
            k_input = k_input.replace(',', '.')
            k = float(k_input)
            
            if k <= 0:
                print("\n⚠️  Ошибка: k должно быть положительным!")
                input("\n⏎ Нажмите Enter...")
                continue
            
            print("\n🔧 Выберите метод поиска:")
            print("   1. Оптимизированный V2 - 5-10 секунд")
            print("   2. Проверить конкретные значения")
            
            method = input("Ваш выбор (1/2) [по умолчанию 1]: ").strip() or "1"
            
            if method == "2":
                # Проверка конкретных значений
                try:
                    x = int(input("   x (0-255): "))
                    y = int(input("   y (0-255): "))
                    z = int(input("   z (0-255): "))
                    f = int(input("   f (0-255): "))
                    
                    if all(0 <= v <= 255 for v in [x, y, z, f]):
                        expr = (f * 256 + z) * 256 + y + x * 0.01
                        result_day = expr * k
                        result_night = expr * k
                        
                        print(f"\n📊 Результаты для x={x}, y={y}, z={z}, f={f}:")
                        print(f"   Выражение: {expr:.4f}")
                        print(f"\n   ДНЕВНОЙ ТАРИФ: {expr:.4f} * {k} = {result_day:.6f}")
                        print(f"   Целая часть: {int(round(result_day))}, целевая: {int(round(a))}, отклонение: {abs(int(round(result_day)) - int(round(a)))}")
                        print(f"\n   НОЧНОЙ ТАРИФ: {expr:.4f} * {k} = {result_night:.6f}")
                        print(f"   Целая часть: {int(round(result_night))}, целевая: {int(round(a1))}, отклонение: {abs(int(round(result_night)) - int(round(a1)))}")
                    else:
                        print("\n❌ Значения должны быть от 0 до 255!")
                except ValueError:
                    print("\n❌ Введите целые числа!")
            else:
                # Ввод допустимого отклонения
                tolerance_input = input("📏 Допустимое отклонение целой части [по умолчанию 1]: ").strip()
                tolerance = float(tolerance_input) if tolerance_input else 1.0
                
                # Параллельный поиск для обоих тарифов
                print(f"\n🔄 Выполняется параллельный расчет для обоих тарифов...")
                
                # Поиск для дневного тарифа
                solutions_day = find_solutions_optimized_v2(a, k, tolerance)
                
                # Поиск для ночного тарифа
                solutions_night = find_solutions_optimized_v2(a1, k, tolerance)
                
                # Вывод результатов
                print_dual_solution_table(solutions_day, solutions_night, a, a1, k)
            
        except ValueError:
            print("\n❌ Ошибка: введите корректные числа!")
        except KeyboardInterrupt:
            print("\n\n👋 До свидания!")
            break
        except Exception as e:
            print(f"\n❌ Ошибка: {e}")
        
        input("\n⏎ Нажмите Enter для продолжения...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 До свидания!")
        sys.exit(0)