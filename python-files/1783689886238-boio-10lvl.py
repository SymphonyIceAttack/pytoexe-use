import webbrowser
import time

# Список всех ваших ссылок
urls = [
    "https://steamcommunity.com/market/listings/753/730-Anarchist",
    "https://steamcommunity.com/market/listings/753/730-Balkan",
    "https://steamcommunity.com/market/listings/753/730-FBI",
    "https://steamcommunity.com/market/listings/753/730-IDF",
    "https://steamcommunity.com/market/listings/753/730-SWAT",
    "https://steamcommunity.com/market/listings/753/1169040-Cavelings",
    "https://steamcommunity.com/market/listings/753/1169040-Cryo%20Queen",
    "https://steamcommunity.com/market/listings/753/1169040-Elder",
    "https://steamcommunity.com/market/listings/753/1169040-Pirate%20Captain",
    "https://steamcommunity.com/market/listings/753/1169040-Stabby%20Bush",
    "https://steamcommunity.com/market/listings/753/1169040-Ascended%20Wizard"
]

def open_links():
    for url in urls:
        webbrowser.open_new_tab(url)
        # Небольшая задержка, чтобы браузер не "поперхнулся" открытием 11 вкладок сразу
        time.sleep(0.5)

if __name__ == "__main__":
    open_links()
    