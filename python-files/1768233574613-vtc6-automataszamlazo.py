# DEMO verzió
def invoice_demo():
    print("DEMO: Számla generálása példa adatokkal")
    print("Összeg: 100 €")

# PRO verzió
def invoice_pro(client, items, iban="LT81 3250 0757 5026 3901"):
    total = sum(items.values())
    print(f"Számla {client} részére")
    for item, price in items.items():
        print(f"{item}: {price} €")
    print(f"Összesen: {total} €")
    print(f"Fizetés IBAN: {iban}")