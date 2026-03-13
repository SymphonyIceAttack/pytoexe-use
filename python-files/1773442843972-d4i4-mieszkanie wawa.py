import requests
from bs4 import BeautifulSoup
import time
from win10toast_click import ToastNotifier
import webbrowser

toaster = ToastNotifier()

MIN_M2 = 45
MAX_PRICE_M2 = 20000
CHECK_INTERVAL = 20 * 60  # co 20 minut

AREAS = [
    "Muranów", "Nowolipki", "Nowe Miasto",
    "Śródmieście Północne", "Plac Bankowy",
    "Aleja Solidarności", "Wola"
]

URLS = [
    "https://www.otodom.pl/pl/oferty/sprzedaz/mieszkanie/warszawa",
    "https://www.olx.pl/nieruchomosci/mieszkania/sprzedaz/warszawa/",
    "https://gratka.pl/nieruchomosci/mieszkania/warszawa/sprzedaz"
]

seen_links = set()

def notify(title, message, link):
    def callback():
        webbrowser.open(link)
    toaster.show_toast(title, message, duration=10, threaded=True, callback_on_click=callback)

def parse_price(text):
    try:
        return int(text.replace(" ", "").replace("zł", "").replace("PLN",""))
    except:
        return None

def check_area(text):
    for a in AREAS:
        if a.lower() in text.lower():
            return True
    return False

def scrape_otodom():
    results = []
    try:
        r = requests.get(URLS[0])
        soup = BeautifulSoup(r.text, "html.parser")
        offers = soup.select("a")
        for o in offers:
            link = o.get("href")
            if link and "/oferta/" in link and link not in seen_links:
                results.append(link)
    except:
        pass
    return results

def analyze_offer(link):
    try:
        r = requests.get(link)
        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.text
        if not check_area(text):
            return None
        metraz = None
        price = None
        for line in text.split("\n"):
            if "m²" in line and not metraz:
                try:
                    metraz = float(line.split("m²")[0].split()[-1])
                except:
                    pass
            if "zł" in line and not price:
                price = parse_price(line)
        if not metraz or not price:
            return None
        price_m2 = price / metraz
        if metraz < MIN_M2 or price_m2 > MAX_PRICE_M2:
            return None
        ownership = "nieznane"
        if "pełna własność" in text.lower():
            ownership = "pełna własność"
        if "spółdzielcze" in text.lower():
            ownership = "spółdzielcze"
        agency = "agencja"
        if "bezpośrednio" in text.lower():
            agency = "prywatne"
        return {
            "metraz": metraz,
            "price": price,
            "price_m2": int(price_m2),
            "ownership": ownership,
            "seller": agency
        }
    except:
        return None

while True:
    for link in scrape_otodom():
        data = analyze_offer(link)
        if data:
            seen_links.add(link)
            message = f"{data['metraz']} m², {data['price']} zł, {data['price_m2']} zł/m²\n{data['seller']}, {data['ownership']}"
            notify("Nowe mieszkanie Warszawa", message, link)
    time.sleep(CHECK_INTERVAL)