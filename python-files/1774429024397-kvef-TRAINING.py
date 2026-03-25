import random
import time
import os
import copy

RESET = "\033[0m"
GREEN = "\033[92m"

SCALE = 3


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def generate_cars():
    cars = []

    num_n = random.randint(2, 3)
    num_b = random.randint(2, 3)
    num_a = 15 - num_n - num_b

    types = (["Н"] * num_n) + (["Б"] * num_b) + (["А"] * num_a)
    random.shuffle(types)

    for i in range(15):
        car_type = types[i]
        distance = random.randint(40, 70)

        if car_type == "Б":
            speed = random.randint(300, 600)
        elif car_type == "Н":
            speed = random.randint(180, 300)
        else:
            if random.random() < 0.85:
                speed = 200
            else:
                speed = random.randint(220, 400)

        cars.append({
            "id": i + 1,
            "type": car_type,
            "distance": float(distance),
            "speed": speed
        })

    return cars


def update_distances(cars, delta_time):
    for car in cars:
        if car["distance"] > 0:
            car["distance"] -= (car["speed"] * delta_time * SCALE) / 1000
            if car["distance"] < 0:
                car["distance"] = 0


def print_table(cars, selected):
    clear()
    print(f"{'№':<5}{'Тип цели':<10}{'Дальность цели':<15}{'Скорость цели':<15}{'Пуск':<10}")
    print("-" * 60)

    for car in cars:
        launch_mark = "ПРОИЗВЕДЁН" if car["id"] in selected else ""

        line = f"{car['id']:<5}{car['type']:<10}{round(car['distance'],1):<15}{car['speed']:<15}{launch_mark:<10}"

        if car["id"] in selected:
            print(GREEN + line + RESET)
        else:
            print(line)


def get_correct_order(initial_cars):
    temp = []
    for c in initial_cars:
        t = (c["distance"] * 1000) / c["speed"]
        temp.append((c["id"], c["type"], t))

    priority = [x for x in temp if x[1] in ["Н", "Б"]]
    rest = [x for x in temp if x[1] == "А"]

    priority.sort(key=lambda x: x[2])
    rest.sort(key=lambda x: x[2])

    return [x[0] for x in priority + rest]


def play():
    cars = generate_cars()
    initial_cars = copy.deepcopy(cars)

    correct_order = get_correct_order(initial_cars)

    selected = []
    last_time = time.time()

    while len(selected) < 15:
        now = time.time()
        delta = now - last_time
        last_time = now

        update_distances(cars, delta)
        print_table(cars, selected)

        try:
            num = int(input("\nУничтожить: "))
        except:
            continue

        if num < 1 or num > 15 or num in selected:
            continue

        selected.append(num)

    print_table(cars, selected)

    print("\nТвой выбор:")
    print(selected)

    print("\nПравильный порядок:")
    print(correct_order)

    input("\nНажми Enter для выхода...")


if __name__ == "__main__":
    play()
