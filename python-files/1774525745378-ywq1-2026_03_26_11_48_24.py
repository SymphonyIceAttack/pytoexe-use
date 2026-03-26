import requests
from bs4 import BeautifulSoup

urls = [
    "https://support.kaspersky.ru/b2c/ru",
    "https://support.kaspersky.com/fr/b2c/dz",
    "https://support.kaspersky.com/fr/b2c/ga"
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

for url in urls:
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        links = soup.find_all("a", attrs={"data-name": True})
        data_names = [link.get("data-name") for link in links if link.get("data-name")]
        
        if data_names:
            print(f"{url} - {' | '.join(data_names)}")
        else:
            print(f"{url} - не найдено")
    except requests.exceptions.RequestException as e:
        print(f"{url} - ошибка: {e}")