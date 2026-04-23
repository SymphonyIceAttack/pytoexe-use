import json
import os

DATA_FILE = "pizzeria_orders.json"

MENU_PIZZAS = {
    1: {"name": "Маргарита", "price": 350},
    2: {"name": "Пепперони", "price": 450},
    3: {"name": "Гавайская", "price": 400},
    4: {"name": "Четыре сыра", "price": 500},
    5: {"name": "Мясная", "price": 550}
}

STATUSES = {
    1: "принят",
    2: "готовится",
    3: "в доставке",
    4: "выполнен"
}

class PizzaOrder:
    def __init__(self, order_id, items, status="принят"):
        self.order_id = order_id
        self.items = items  # список номеров пицц (1-5)
        self.status = status
        self.total_price = self.calculate_total()

    def calculate_total(self):
        return sum(MENU_PIZZAS[pizza_num]["price"] for pizza_num in self.items)

    def to_dict(self):
        return {
            "order_id": self.order_id,
            "items": self.items,
            "status": self.status,
            "total_price": self.total_price
        }

    @staticmethod
    def from_dict(data):
        order = PizzaOrder(data["order_id"], data["items"], data["status"])
        order.total_price = data["total_price"]
        return order

def load_orders():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            orders_data = json.load(f)
            return [PizzaOrder.from_dict(data) for data in orders_data]
    return []

def save_orders(orders):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump([order.to_dict() for order in orders], f, ensure_ascii=False, indent=4)

def display_orders(orders):
    if not orders:
        print("Нет заказов.")
        return
    print("\n=== Список заказов ===")
    for order in orders:
        items_str = ', '.join(MENU_PIZZAS[num]["name"] for num in order.items)
        print(f"Заказ №{order.order_id} | Статус: {order.status} | Сумма: {order.total_price} руб.")
        print(f"Состав: {items_str}")
        print("-" * 40)

def select_pizzas_from_menu():
    items = []
    print("\nМеню пицц:")
    for key, val in MENU_PIZZAS.items():
        print(f"{key}. {val['name']} - {val['price']} руб.")

    while True:
        print("0. Завершить выбор")
        choice = input("Введите номер пиццы для добавления в заказ: ").strip()
        
        if choice == '0':
            break

        if choice.isdigit():
            num = int(choice)
            if num in MENU_PIZZAS:
                items.append(num)
                print(f"Добавлена {MENU_PIZZAS[num]['name']}")
            else:
                print("Неверный номер. Попробуйте снова.")
        else:
            print("Пожалуйста, введите число.")

    return items

def add_order(orders):
    order_id = max([o.order_id for o in orders], default=0) + 1
    
    print("\n=== Создание нового заказа ===")
    items = select_pizzas_from_menu()

    if items:
        new_order = PizzaOrder(order_id, items)
        orders.append(new_order)
        save_orders(orders)
        
        items_str = ', '.join(MENU_PIZZAS[num]["name"] for num in items)
        print(f"\nЗаказ №{order_id} добавлен!")
        print(f"Состав: {items_str}")
        print(f"Итоговая сумма: {new_order.total_price} руб.")
    else:
        print("Заказ не создан: не выбрано ни одной пиццы.")

def update_order_status(orders):
    display_orders(orders)
    
    try:
        order_id = int(input("\nВведите номер заказа для изменения статуса: ").strip())
        order = next((o for o in orders if o.order_id == order_id), None)
        
        if order:
            print("\nВыберите новый статус:")
            for key, val in STATUSES.items():
                print(f"{key}. {val}")
            
            while True:
                choice = input("Введите номер статуса: ").strip()
                if choice.isdigit():
                    num = int(choice)
                    if num in STATUSES:
                        new_status = STATUSES[num]
                        order.status = new_status
                        save_orders(orders)
                        print(f"Статус заказа №{order_id} обновлён на '{new_status}'.")
                        break
                    else:
                        print("Неверный номер статуса.")
                else:
                    print("Пожалуйста, введите число.")
        else:
            print("Заказ с таким номером не найден.")
            
    except ValueError:
        print("Некорректный ввод номера заказа.")

def update_order_items(orders):
    display_orders(orders)
    
    try:
        order_id = int(input("\nВведите номер заказа для изменения состава: ").strip())
        order = next((o for o in orders if o.order_id == order_id), None)
        
        if order:
            print("\nТекущий состав:")
            for num in order.items:
                print(f"- {MENU_PIZZAS[num]['name']}")
            
            print("\nВыберите новые позиции из меню:")
            new_items = select_pizzas_from_menu()
            
            if new_items:
                order.items = new_items
                order.total_price = order.calculate_total()
                save_orders(orders)
                print(f"\nСостав заказа №{order_id} обновлён. Новая сумма: {order.total_price} руб.")
            else:
                print("Состав не изменён.")
                
        else:
            print("Заказ не найден.")
            
    except ValueError:
        print("Некорректный ввод номера заказа.")

def main():
    orders = load_orders()
    
    while True:
        print("\n=== Пиццерия 'У Палыча' ===")
        print("1. Показать все заказы")
        print("2. Добавить новый заказ")
        print("3. Изменить статус заказа")
        print("4. Изменить состав заказа")
        print("5. Выйти")
        
        choice = input("Выберите действие (1-5): ").strip()
        
        if choice == '1':
            display_orders(orders)
        elif choice == '2':
            add_order(orders)
        elif choice == '3':
            update_order_status(orders)
        elif choice == '4':
            update_order_items(orders)
        elif choice == '5':
            print("До свидания!")
            break
        else:
            print("Неверный ввод, попробуйте снова (1-5).")

if __name__ == "__main__":
    main()import json
import os

DATA_FILE = "pizzeria_orders.json"

MENU_PIZZAS = {
    1: {"name": "Маргарита", "price": 350},
    2: {"name": "Пепперони", "price": 450},
    3: {"name": "Гавайская", "price": 400},
    4: {"name": "Четыре сыра", "price": 500},
    5: {"name": "Мясная", "price": 550}
}

STATUSES = {
    1: "принят",
    2: "готовится",
    3: "в доставке",
    4: "выполнен"
}

class PizzaOrder:
    def __init__(self, order_id, items, status="принят"):
        self.order_id = order_id
        self.items = items  # список номеров пицц (1-5)
        self.status = status
        self.total_price = self.calculate_total()

    def calculate_total(self):
        return sum(MENU_PIZZAS[pizza_num]["price"] for pizza_num in self.items)

    def to_dict(self):
        return {
            "order_id": self.order_id,
            "items": self.items,
            "status": self.status,
            "total_price": self.total_price
        }

    @staticmethod
    def from_dict(data):
        order = PizzaOrder(data["order_id"], data["items"], data["status"])
        order.total_price = data["total_price"]
        return order

def load_orders():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            orders_data = json.load(f)
            return [PizzaOrder.from_dict(data) for data in orders_data]
    return []

def save_orders(orders):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump([order.to_dict() for order in orders], f, ensure_ascii=False, indent=4)

def display_orders(orders):
    if not orders:
        print("Нет заказов.")
        return
    print("\n=== Список заказов ===")
    for order in orders:
        items_str = ', '.join(MENU_PIZZAS[num]["name"] for num in order.items)
        print(f"Заказ №{order.order_id} | Статус: {order.status} | Сумма: {order.total_price} руб.")
        print(f"Состав: {items_str}")
        print("-" * 40)

def select_pizzas_from_menu():
    items = []
    print("\nМеню пицц:")
    for key, val in MENU_PIZZAS.items():
        print(f"{key}. {val['name']} - {val['price']} руб.")

    while True:
        print("0. Завершить выбор")
        choice = input("Введите номер пиццы для добавления в заказ: ").strip()
        
        if choice == '0':
            break

        if choice.isdigit():
            num = int(choice)
            if num in MENU_PIZZAS:
                items.append(num)
                print(f"Добавлена {MENU_PIZZAS[num]['name']}")
            else:
                print("Неверный номер. Попробуйте снова.")
        else:
            print("Пожалуйста, введите число.")

    return items

def add_order(orders):
    order_id = max([o.order_id for o in orders], default=0) + 1
    
    print("\n=== Создание нового заказа ===")
    items = select_pizzas_from_menu()

    if items:
        new_order = PizzaOrder(order_id, items)
        orders.append(new_order)
        save_orders(orders)
        
        items_str = ', '.join(MENU_PIZZAS[num]["name"] for num in items)
        print(f"\nЗаказ №{order_id} добавлен!")
        print(f"Состав: {items_str}")
        print(f"Итоговая сумма: {new_order.total_price} руб.")
    else:
        print("Заказ не создан: не выбрано ни одной пиццы.")

def update_order_status(orders):
    display_orders(orders)
    
    try:
        order_id = int(input("\nВведите номер заказа для изменения статуса: ").strip())
        order = next((o for o in orders if o.order_id == order_id), None)
        
        if order:
            print("\nВыберите новый статус:")
            for key, val in STATUSES.items():
                print(f"{key}. {val}")
            
            while True:
                choice = input("Введите номер статуса: ").strip()
                if choice.isdigit():
                    num = int(choice)
                    if num in STATUSES:
                        new_status = STATUSES[num]
                        order.status = new_status
                        save_orders(orders)
                        print(f"Статус заказа №{order_id} обновлён на '{new_status}'.")
                        break
                    else:
                        print("Неверный номер статуса.")
                else:
                    print("Пожалуйста, введите число.")
        else:
            print("Заказ с таким номером не найден.")
            
    except ValueError:
        print("Некорректный ввод номера заказа.")

def update_order_items(orders):
    display_orders(orders)
    
    try:
        order_id = int(input("\nВведите номер заказа для изменения состава: ").strip())
        order = next((o for o in orders if o.order_id == order_id), None)
        
        if order:
            print("\nТекущий состав:")
            for num in order.items:
                print(f"- {MENU_PIZZAS[num]['name']}")
            
            print("\nВыберите новые позиции из меню:")
            new_items = select_pizzas_from_menu()
            
            if new_items:
                order.items = new_items
                order.total_price = order.calculate_total()
                save_orders(orders)
                print(f"\nСостав заказа №{order_id} обновлён. Новая сумма: {order.total_price} руб.")
            else:
                print("Состав не изменён.")
                
        else:
            print("Заказ не найден.")
            
    except ValueError:
        print("Некорректный ввод номера заказа.")

def main():
    orders = load_orders()
    
    while True:
        print("\n=== Пиццерия 'У Палыча' ===")
        print("1. Показать все заказы")
        print("2. Добавить новый заказ")
        print("3. Изменить статус заказа")
        print("4. Изменить состав заказа")
        print("5. Выйти")
        
        choice = input("Выберите действие (1-5): ").strip()
        
        if choice == '1':
            display_orders(orders)
        elif choice == '2':
            add_order(orders)
        elif choice == '3':
            update_order_status(orders)
        elif choice == '4':
            update_order_items(orders)
        elif choice == '5':
            print("До свидания!")
            break
        else:
            print("Неверный ввод, попробуйте снова (1-5).")

if __name__ == "__main__":
    main()import json
import os

DATA_FILE = "pizzeria_orders.json"

MENU_PIZZAS = {
    1: {"name": "Маргарита", "price": 350},
    2: {"name": "Пепперони", "price": 450},
    3: {"name": "Гавайская", "price": 400},
    4: {"name": "Четыре сыра", "price": 500},
    5: {"name": "Мясная", "price": 550}
}

STATUSES = {
    1: "принят",
    2: "готовится",
    3: "в доставке",
    4: "выполнен"
}

class PizzaOrder:
    def __init__(self, order_id, items, status="принят"):
        self.order_id = order_id
        self.items = items  # список номеров пицц (1-5)
        self.status = status
        self.total_price = self.calculate_total()

    def calculate_total(self):
        return sum(MENU_PIZZAS[pizza_num]["price"] for pizza_num in self.items)

    def to_dict(self):
        return {
            "order_id": self.order_id,
            "items": self.items,
            "status": self.status,
            "total_price": self.total_price
        }

    @staticmethod
    def from_dict(data):
        order = PizzaOrder(data["order_id"], data["items"], data["status"])
        order.total_price = data["total_price"]
        return order

def load_orders():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            orders_data = json.load(f)
            return [PizzaOrder.from_dict(data) for data in orders_data]
    return []

def save_orders(orders):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump([order.to_dict() for order in orders], f, ensure_ascii=False, indent=4)

def display_orders(orders):
    if not orders:
        print("Нет заказов.")
        return
    print("\n=== Список заказов ===")
    for order in orders:
        items_str = ', '.join(MENU_PIZZAS[num]["name"] for num in order.items)
        print(f"Заказ №{order.order_id} | Статус: {order.status} | Сумма: {order.total_price} руб.")
        print(f"Состав: {items_str}")
        print("-" * 40)

def select_pizzas_from_menu():
    items = []
    print("\nМеню пицц:")
    for key, val in MENU_PIZZAS.items():
        print(f"{key}. {val['name']} - {val['price']} руб.")

    while True:
        print("0. Завершить выбор")
        choice = input("Введите номер пиццы для добавления в заказ: ").strip()
        
        if choice == '0':
            break

        if choice.isdigit():
            num = int(choice)
            if num in MENU_PIZZAS:
                items.append(num)
                print(f"Добавлена {MENU_PIZZAS[num]['name']}")
            else:
                print("Неверный номер. Попробуйте снова.")
        else:
            print("Пожалуйста, введите число.")

    return items

def add_order(orders):
    order_id = max([o.order_id for o in orders], default=0) + 1
    
    print("\n=== Создание нового заказа ===")
    items = select_pizzas_from_menu()

    if items:
        new_order = PizzaOrder(order_id, items)
        orders.append(new_order)
        save_orders(orders)
        
        items_str = ', '.join(MENU_PIZZAS[num]["name"] for num in items)
        print(f"\nЗаказ №{order_id} добавлен!")
        print(f"Состав: {items_str}")
        print(f"Итоговая сумма: {new_order.total_price} руб.")
    else:
        print("Заказ не создан: не выбрано ни одной пиццы.")

def update_order_status(orders):
    display_orders(orders)
    
    try:
        order_id = int(input("\nВведите номер заказа для изменения статуса: ").strip())
        order = next((o for o in orders if o.order_id == order_id), None)
        
        if order:
            print("\nВыберите новый статус:")
            for key, val in STATUSES.items():
                print(f"{key}. {val}")
            
            while True:
                choice = input("Введите номер статуса: ").strip()
                if choice.isdigit():
                    num = int(choice)
                    if num in STATUSES:
                        new_status = STATUSES[num]
                        order.status = new_status
                        save_orders(orders)
                        print(f"Статус заказа №{order_id} обновлён на '{new_status}'.")
                        break
                    else:
                        print("Неверный номер статуса.")
                else:
                    print("Пожалуйста, введите число.")
        else:
            print("Заказ с таким номером не найден.")
            
    except ValueError:
        print("Некорректный ввод номера заказа.")

def update_order_items(orders):
    display_orders(orders)
    
    try:
        order_id = int(input("\nВведите номер заказа для изменения состава: ").strip())
        order = next((o for o in orders if o.order_id == order_id), None)
        
        if order:
            print("\nТекущий состав:")
            for num in order.items:
                print(f"- {MENU_PIZZAS[num]['name']}")
            
            print("\nВыберите новые позиции из меню:")
            new_items = select_pizzas_from_menu()
            
            if new_items:
                order.items = new_items
                order.total_price = order.calculate_total()
                save_orders(orders)
                print(f"\nСостав заказа №{order_id} обновлён. Новая сумма: {order.total_price} руб.")
            else:
                print("Состав не изменён.")
                
        else:
            print("Заказ не найден.")
            
    except ValueError:
        print("Некорректный ввод номера заказа.")

def main():
    orders = load_orders()
    
    while True:
        print("\n=== Пиццерия 'У Арсения' ===")
        print("1. Показать все заказы")
        print("2. Добавить новый заказ")
        print("3. Изменить статус заказа")
        print("4. Изменить состав заказа")
        print("5. Выйти")
        
        choice = input("Выберите действие (1-5): ").strip()
        
        if choice == '1':
            display_orders(orders)
        elif choice == '2':
            add_order(orders)
        elif choice == '3':
            update_order_status(orders)
        elif choice == '4':
            update_order_items(orders)
        elif choice == '5':
            print("До свидания!")
            break
        else:
            print("Неверный ввод, попробуйте снова (1-5).")

if __name__ == "__main__":
    main()