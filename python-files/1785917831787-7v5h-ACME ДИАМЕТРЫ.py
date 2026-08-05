import math

class ACME_Thread_Calculator:
    def __init__(self):
        # Угол профиля в радианах (29°)
        self.angle_deg = 29
        self.angle_rad = math.radians(self.angle_deg)
        
    def calculate_thread(self, nominal_diameter, tpi, thread_type="external"):
        """
        Расчет параметров резьбы ACME
        
        Parameters:
        nominal_diameter (float): Номинальный диаметр в дюймах (например, 5.5)
        tpi (int): Количество витков на дюйм (например, 8)
        thread_type (str): Тип резьбы - "external" (наружная) или "internal" (внутренняя)
        """
        print("=" * 70)
        print(f"РАСЧЕТ ПАРАМЕТРОВ РЕЗЬБЫ ACME {nominal_diameter} - {tpi}")
        print(f"Тип резьбы: {'НАРУЖНАЯ' if thread_type == 'external' else 'ВНУТРЕННЯЯ'}")
        print("=" * 70)
        
        # Основные расчеты
        D = nominal_diameter  # Номинальный диаметр
        P = 1 / tpi  # Шаг резьбы
        
        # Константы для резьбы ACME (29°)
        h_nominal = 0.5 * P  # Номинальная высота профиля
        # Фактическая высота профиля с учетом допуска
        h = 0.5 * P + 0.01 if thread_type == "external" else 0.5 * P
        
        # Расчет диаметров для наружной резьбы
        if thread_type == "external":
            d = D  # Наружный диаметр заготовки
            d_i = d - P  # Диаметр по впадинам (минимальный)
            d_p = d - 0.5 * P  # Средний диаметр
            
            # Расчет для метода 3-х проволочек
            G_recommended = 0.51645 * P  # Рекомендуемый диаметр проволочек
            M = d_p + 4.9939 * G_recommended - 1.9334 * P  # Размер над проволочками
            
            # Результаты для наружной резьбы
            results = {
                "Наружный диаметр (заготовки)": d,
                "Диаметр по впадинам": d_i,
                "Средний диаметр": d_p,
                "Диаметр сверления": None,
                "Диаметр отверстия после нарезки": None,
            }
            
        # Расчет диаметров для внутренней резьбы
        else:  # internal
            D_nom = D  # Номинальный диаметр
            D_i_drill = D_nom - P  # Диаметр сверления (теоретический)
            D_i_drill_practical = D_nom - P + 0.005  # Практический диаметр сверления (+0.005")
            D_p = D_nom - 0.5 * P  # Средний диаметр
            D_i_internal = D_nom - 2 * h  # Диаметр отверстия после нарезки
            
            # Результаты для внутренней резьбы
            results = {
                "Наружный диаметр (номинальный)": D_nom,
                "Диаметр по впадинам": None,
                "Средний диаметр": D_p,
                "Диаметр сверления (теоретический)": D_i_drill,
                "Диаметр сверления (практический)": D_i_drill_practical,
                "Диаметр отверстия после нарезки": D_i_internal,
            }
        
        # Общие параметры для обоих типов
        common_params = {
            "Шаг резьбы (P)": P,
            "Витков на дюйм (TPI)": tpi,
            "Угол профиля": self.angle_deg,
            "Высота профиля (h)": h,
            "Ширина впадины/гребня (на ср.диам.)": 0.5 * P,
            "Радиус впадины (рекоменд.)": 0.125 * P,
        }
        
        # Вывод результатов
        print("\n" + "=" * 70)
        print("ОСНОВНЫЕ ПАРАМЕТРЫ:")
        print("=" * 70)
        
        # Вывод в дюймах
        print("\n--- В ДЮЙМАХ ---")
        for param, value in common_params.items():
            if value is not None:
                print(f"{param:40} : {value:.6f}\"")
        
        for param, value in results.items():
            if value is not None:
                print(f"{param:40} : {value:.6f}\"")
        
        # Вывод в миллиметрах
        print("\n--- В МИЛЛИМЕТРАХ (приблизительно) ---")
        for param, value in common_params.items():
            if value is not None:
                print(f"{param:40} : {value * 25.4:.4f} мм")
        
        for param, value in results.items():
            if value is not None:
                print(f"{param:40} : {value * 25.4:.4f} мм")
        
        # Дополнительная информация для наружной резьбы
        if thread_type == "external":
            print("\n" + "=" * 70)
            print("ДОПОЛНИТЕЛЬНО ДЛЯ НАРУЖНОЙ РЕЗЬБЫ:")
            print("=" * 70)
            print(f"Рекомендуемый диаметр проволочек для контроля: {G_recommended:.6f}\" ({G_recommended*25.4:.4f} мм)")
            print(f"Стандартный диаметр проволочек: {round(G_recommended, 4):.4f}\" ({round(G_recommended*25.4, 2):.2f} мм)")
            print(f"Расчетный размер M (над 3 проволочками): {M:.6f}\" ({M*25.4:.4f} мм)")
        
        # Дополнительная информация для внутренней резьбы
        else:
            print("\n" + "=" * 70)
            print("ДОПОЛНИТЕЛЬНО ДЛЯ ВНУТРЕННЕЙ РЕЗЬБЫ:")
            print("=" * 70)
            print("Рекомендуемый диапазон диаметра сверления:")
            print(f"  Минимальный: {D_i_drill:.6f}\" ({D_i_drill*25.4:.4f} мм)")
            print(f"  Практический: {D_i_drill_practical:.6f}\" ({D_i_drill_practical*25.4:.4f} мм)")
            print(f"  Максимальный (обычно): {D_i_drill + 0.01:.6f}\" ({(D_i_drill + 0.01)*25.4:.4f} мм)")
        
        # Общие рекомендации
        print("\n" + "=" * 70)
        print("ВАЖНЫЕ РЕКОМЕНДАЦИИ:")
        print("=" * 70)
        if thread_type == "external":
            print("1. Укажите класс допуска на чертеже (например: ACME 8 1/2-4-3c)")
            print("2. Диаметр заготовки делайте с учетом допуска (обычно больше номинала)")
            print("3. Для контроля используйте метод 3-х проволочек или резьбовые кольца")
            print("4. Рекомендуется выполнить радиус впадины для повышения прочности")
        else:
            print("1. Укажите класс допуска на чертеже (например: ACME 8 1/2-4-2G)")
            print("2. Диаметр сверления уточняйте по стандарту ASME B1.5 для выбранного класса")
            print("3. Для нарезки используйте метчики или резцы с правильным профилем 29°")
            print("4. Контролируйте средний диаметр калибрами-пробками GO/NO-GO")
        
        print("\nПримечание: Для ответственных применений всегда сверяйтесь")
        print("с таблицами допусков стандарта ASME B1.5!")
        print("=" * 70 + "\n")

def main():
    calculator = ACME_Thread_Calculator()
    
    print("КАЛЬКУЛЯТОР ПАРАМЕТРОВ РЕЗЬБЫ ACME (29°)")
    print("=" * 70)
    
    while True:
        try:
            print("\nВведите параметры резьбы:")
            print("(Для выхода введите 'q')")
            
            # Ввод номинального диаметра
            diam_input = input("Номинальный диаметр (дюймы, например: 5.5, 8.5, 2.25): ").strip()
            if diam_input.lower() == 'q':
                break
            
            # Преобразование ввода с дробями
            if '/' in diam_input:
                # Обработка дробей типа 5 1/2
                if ' ' in diam_input:
                    whole, fraction = diam_input.split()
                    num, denom = map(int, fraction.split('/'))
                    nominal_diameter = float(whole) + num / denom
                else:
                    num, denom = map(int, diam_input.split('/'))
                    nominal_diameter = num / denom
            else:
                nominal_diameter = float(diam_input)
            
            # Ввод TPI
            tpi_input = input("Количество витков на дюйм (TPI, например: 8, 4, 10): ").strip()
            if tpi_input.lower() == 'q':
                break
            tpi = int(tpi_input)
            
            # Выбор типа резьбы
            thread_type = input("Тип резьбы (1 - наружная, 2 - внутренняя): ").strip()
            if thread_type.lower() == 'q':
                break
            
            thread_type = "external" if thread_type == "1" else "internal"
            
            # Выполнение расчета
            calculator.calculate_thread(nominal_diameter, tpi, thread_type)
            
            # Предложение нового расчета
            again = input("\nВыполнить новый расчет? (y/n): ").strip().lower()
            if again != 'y':
                break
                
        except ValueError as e:
            print(f"Ошибка ввода! Проверьте правильность введенных данных. Ошибка: {e}")
        except ZeroDivisionError:
            print("Ошибка: TPI не может быть равен 0!")
        except Exception as e:
            print(f"Произошла ошибка: {e}")

if __name__ == "__main__":
    main()