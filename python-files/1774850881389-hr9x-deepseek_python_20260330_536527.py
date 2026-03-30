currency = input()
amount = float(input())

rates = {"USD": 75.5, "EUR": 80.2, "GBP": 90.1}

match currency:
    case "USD" | "EUR" | "GBP":
        rubles = amount * rates[currency]
        print(f"{amount} {currency} = {rubles:.2f} RUB")
    case _:
        print("Ошибка: неизвестная валюта")