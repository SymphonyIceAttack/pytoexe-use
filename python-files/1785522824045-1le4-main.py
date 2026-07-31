import json

FILE_NAME = "shopping.json"

def load_shopping_list():
    """��������� ������ ������� �� JSON-�����."""
    try:
        with open(FILE_NAME, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        print("���� �� ������. �������� ������ ������.")
        return []
    except json.JSONDecodeError:
        print("������ � ������� JSON. �������� ������ ������.")
        return []

def save_shopping_list(shopping_list):
    """��������� ������ ������� � JSON-����."""
    with open(FILE_NAME, "w", encoding="utf-8") as file:
        json.dump(shopping_list, file, ensure_ascii=False, indent=2)
    print("��������� ��������� � ����.")

def show_shopping_list(shopping_list):
    """������� ������ ������� �� �����."""
    if not shopping_list:
        print("������ ������� ����.")
        return
    
    print("\n������ �������:")
    for i, item in enumerate(shopping_list, start=1):
        name = item.get("name", "��� ��������")
        quantity = item.get("quantity", 0)
        print(f"{i}. {name} � {quantity} ��.")
    print()

def add_product(shopping_list):
    """��������� ����� ������� � ������ ����� ���� ������������."""
    name = input("������� �������� ��������: ").strip()
    if not name:
        print("�������� �� ����� ���� ������.")
        return
    
    while True:
        quantity_str = input("������� ����������: ").strip()
        if quantity_str.isdigit():
            quantity = int(quantity_str)
            break
        else:
            print("����������, ������� ����� �����.")
    
    new_item = {"name": name, "quantity": quantity}
    shopping_list.append(new_item)
    print(f"������� '{name}' �������� � ������.\n")

def main():
    shopping_list = load_shopping_list()
    
    while True:
        print("����:")
        print("1. �������� ������ �������")
        print("2. �������� �������")
        print("3. ��������� � �����")
        
        choice = input("�������� �������� (1/2/3): ").strip()
        
        if choice == "1":
            show_shopping_list(shopping_list)
        elif choice == "2":
            add_product(shopping_list)
        elif choice == "3":
            save_shopping_list(shopping_list)
            print("��������� ���������.")
            break
        else:
            print("�������� �����. ���������� �����.\n")

if __name__ == "__main__":
    main()
