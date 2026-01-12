import time

def main():
    print("=== ENTERPRISE LOG MONITOR ===")
    logfile = input("Log fájl elérési útja: ")

    print("\nDEMO mód – csak alap figyelés\n")

    try:
        with open(logfile, "r", encoding="utf-8") as f:
            lines = f.readlines()
            errors = [l for l in lines if "error" in l.lower()]
            print(f"Hibák száma: {len(errors)}")
    except:
        print("Nem sikerült megnyitni a fájlt.")
        return

    print("\nENTERPRISE verzió:")
    print("- valós idejű figyelés")
    print("- email / Slack riasztás")
    print("- incidens riport")
    print("- SLA statisztika")

    print("\nLicenc ár: 200 000 Ft / év")

    print("\nFizetés: Banki átutalás")
    print("IBAN: LT81 3250 0757 5026 3901")
    print("Közlemény: LOG_MONITOR_ENTERPRISE")

if __name__ == "__main__":
    main()