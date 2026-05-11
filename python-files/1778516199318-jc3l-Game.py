import random


class StockMarketGame:
    def __init__(self):
        self.balance = 10000.0
        self.goal = 100000.0
        self.max_days = 35
        self.stocks = {
            "APPLE": 2100.0, "GOOGLE": 2800.0, "TESLA": 1200.0, "BTC": 45000.0,
            "ETH": 7500.0, "SAMSUNG": 1500.0, "LADA": 100.0, "NESTLE": 700.0,
            "BMW": 5000.0, "MERCEDES": 9000.0, "YANDEX": 1400.0, "OPPO": 900.0,
            "NINTENDO": 8000.0, "MICROSOFT": 9100.0, "NIKE": 3700.0, "NETFLIX": 670.0,
            "DISNEY": 3950.0, "TOYOTA": 750.0, "SONY": 7200.0, "COCA-COLA": 5400.0
        }
        self.portfolio = {name: 0 for name in self.stocks}
        self.day = 1

        # Цвета (ANSI-последовательности)
        self.G = '\033[92m'  # Зеленый
        self.R = '\033[91m'  # Красный
        self.Y = '\033[93m'  # Желтый
        self.B = '\033[94m'  # Синий
        self.END = '\033[0m'  # Сброс

    def update_prices(self):
        for stock in self.stocks:
            change = random.uniform(-0.15, 0.3)
            self.stocks[stock] = round(self.stocks[stock] * (1 + change), 2)

    def get_total_worth(self):
        assets_value = sum(self.portfolio[s] * self.stocks[s] for s in self.portfolio)
        return self.balance + assets_value

    def show_status(self):
        total = self.get_total_worth()
        print(f"\n{self.B}=" * 50)
        print(
            f" ДЕНЬ {self.day}/{self.max_days} | Капитал: {self.G}${total:,.2f}{self.B} | Цель: {self.Y}${self.goal:,.0f}")
        print(f" Наличные: ${self.balance:,.2f}")
        print("=" * 50 + self.END)

        owned = {k: v for k, v in self.portfolio.items() if v > 0}
        if owned:
            print(f"{self.Y}Ваш портфель:{self.END} {owned}")

        print(f"\nЦЕНЫ АКЦИЙ:")
        stock_list = list(self.stocks.items())
        for i in range(0, len(stock_list), 2):
            s1, p1 = stock_list[i]
            s2, p2 = stock_list[i + 1] if i + 1 < len(stock_list) else ("", 0)

            part1 = f" {s1:<12} {self.G}${p1:>9.2f}{self.END}"
            part2 = f" | {s2:<12} {self.G}${p2:>9.2f}{self.END}" if s2 else ""
            print(f"{part1}{part2}")

    def run(self):
        print(f"{self.Y}ДОБРО ПОЖАЛОВАТЬ В СИМУЛЯТОР БИРЖИ{self.END}")

        while self.day <= self.max_days:
            self.show_status()

            if self.get_total_worth() >= self.goal:
                print(f"\n{self.G}*** ПОБЕДА! Цель достигнута! ***{self.END}")
                break

            inp = input(f"\nДействие (buy [ко] [кол] / sell [ко] [кол] / next / exit): ").lower().split()
            if not inp: continue

            cmd = inp[0]
            if cmd == "exit": break
            if cmd == "next":
                self.update_prices()
                self.day += 1
                continue

            try:
                symbol, qty = inp[1].upper(), int(inp[2])
                if cmd == "buy":
                    cost = self.stocks[symbol] * qty
                    if cost <= self.balance:
                        self.balance -= cost
                        self.portfolio[symbol] += qty
                        print(f"{self.G}Куплено!{self.END}")
                    else:
                        print(f"{self.R}Недостаточно денег!{self.END}")
                elif cmd == "sell":
                    if self.portfolio.get(symbol, 0) >= qty:
                        self.balance += self.stocks[symbol] * qty
                        self.portfolio[symbol] -= qty
                        print(f"{self.G}Продано!{self.END}")
                    else:
                        print(f"{self.R}У вас нет столько акций!{self.END}")
            except (IndexError, ValueError, KeyError):
                print(f"{self.R}Ошибка! Пример: buy APPLE 10{self.END}")

        final = self.get_total_worth()
        print(f"\nКонец игры. Финальный счет: ${final:,.2f}")


if __name__ == "__main__":
    game = StockMarketGame()
    game.run()
