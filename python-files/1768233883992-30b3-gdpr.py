def main():
    print("=== GDPR PRE-CHECK TOOL ===\n")

    print("Ez a szoftver előzetes adatkezelési ellenőrzést végez.")

    questions = [
        "Tárol személyes adatot? (igen/nem): ",
        "Van adattörlési folyamat? (igen/nem): ",
        "Van hozzáférés-kezelés? (igen/nem): "
    ]

    score = 0
    for q in questions:
        if input(q).lower() == "igen":
            score += 1

    print(f"\nMegfelelőségi pontszám: {score}/3")

    print("\nENTERPRISE verzió:")
    print("- teljes GDPR riport")
    print("- kockázati besorolás")
    print("- jogi sablon dokumentumok")

    print("\nLicenc ár: 250 000 Ft")

    print("\nFizetés: Revolut banki átutalás")
    print("IBAN: LT81 3250 0757 5026 3901")
    print("Közlemény: GDPR_ENTERPRISE")

if __name__ == "__main__":
    main()