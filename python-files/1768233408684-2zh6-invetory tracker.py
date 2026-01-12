def main():
    print("=== INVENTORY TRACKER ===\n")
    products = {
        "Laptop": 12,
        "Monitor": 8,
        "Telefon": 25,
    }

    print("KÉSZLET LISTA:")
    for product, qty in products.items():
        print(f"{product}: {qty} db")

    print("\nDEMO verzió: alap készlet lista\n")

    print("PRO verzió:")
    print("- automatikus riasztások alacsony készletre")
    print("- havi forgalom riport")
    print("- CSV / Excel export")
    print("- többlépcsős felhasználói hozzáférés\n")

    print("Ár: 120 000 Ft / cég")
    print("Fizetés: Revolut")
    print("IBAN: LT81 3250 0757 5026 3901")
    print("Közlemény: INVENTORY_PRO")
    print("Kapcsolat: Business inquiry Telegram / Email")

if __name__ == "__main__":
    main()