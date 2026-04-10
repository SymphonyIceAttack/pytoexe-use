import random

while True:
    while True:
        a = random.randint(1, 6)
        b = random.randint(1, 6)
        c = random.randint(1, 6)
        d = random.randint(1, 6)
        
        # Считаем количество единиц
        единицы = [a, b, c, d].count(1)
        
        if единицы >= 2:
            print("Выпало две или больше единиц! Перебрасываем...")
            continue  # перебрасываем все кубики
        else:
            break  # хороший бросок, выходим из внутреннего цикла
    
    минимальное = min(a, b, c, d)
    статы = a + b + c + d - минимальное
    
    print(a, b, c, d)
    print("твои статы:", статы)
    print("-" * 30)
    
    ответ = input("Бросить ещё? (да/нет): ")
    if ответ == "нет":
        break