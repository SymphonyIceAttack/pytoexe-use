import requests
import time
import json
from pathlib import Path


# ------------------------ KONFIGURACJA ------------------------

CONFIG_FILE = Path("config.json")
LOGIN_URL = "https://vitay.pl/login"

# -------------------------------------------------------------


def load_config():
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(
            f"Nie znaleziono pliku: {CONFIG_FILE}"
        )

    with open(CONFIG_FILE, "r", encoding="utf-8") as file:
        config = json.load(file)

    required = [
        "username",
        "password",
        "api_key_2captcha"
    ]

    for key in required:
        if key not in config:
            raise ValueError(
                f"Brakuje pola '{key}' w config.json"
            )

    return config


def solve_recaptcha(site_key: str, page_url: str, api_key: str) -> str:
    """Rozwiązuje reCAPTCHA v2 przez 2captcha.com"""

    send_payload = {
        "key": api_key,
        "method": "userrecaptcha",
        "googlekey": site_key,
        "pageurl": page_url,
        "json": 1
    }

    send_resp = requests.post(
        "http://2captcha.com/in.php",
        data=send_payload,
        timeout=30
    )

    send_data = send_resp.json()

    if send_data["status"] != 1:
        raise Exception(
            f"Błąd wysyłania captcha: {send_data['request']}"
        )

    captcha_id = send_data["request"]

    print(f"Captcha wysłana, ID: {captcha_id}. Czekam...")

    for _ in range(30):
        time.sleep(2)

        get_payload = {
            "key": api_key,
            "action": "get",
            "id": captcha_id,
            "json": 1
        }

        get_resp = requests.get(
            "http://2captcha.com/res.php",
            params=get_payload,
            timeout=30
        )

        get_data = get_resp.json()

        if get_data["status"] == 1:
            print("Captcha rozwiązana.")
            return get_data["request"]

        if get_data["request"] == "CAPCHA_NOT_READY":
            continue

        raise Exception(
            f"Błąd: {get_data['request']}"
        )

    raise TimeoutError(
        "Przekroczono czas oczekiwania na captchę."
    )


def login():
    config = load_config()

    username = config["username"]
    password = config["password"]
    api_key_2captcha = config["api_key_2captcha"]

    session = requests.Session()

    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36"
        ),
        "Content-Type": "application/json"
    })

    print("Pobieranie strony logowania...")

    resp = session.get(
        LOGIN_URL,
        timeout=30
    )

    resp.raise_for_status()

    FORM_KEY = "JhQmdFJmJfex3seV"

    SITE_KEY = (
        "recaptcha-f979c2ff515d921c34af9bd2aee8ef076b719d03"
    )

    captcha_response = solve_recaptcha(
        SITE_KEY,
        LOGIN_URL,
        api_key_2captcha
    )

    payload = {
        "form_key": FORM_KEY,
        "username": username,
        "password": password,
        "g-recaptcha-response": captcha_response,
        "token": captcha_response
    }

    print("Wysyłanie żądania logowania...")

    login_resp = session.post(
        LOGIN_URL,
        json=payload,
        timeout=30
    )

    if login_resp.status_code == 200:
        try:
            data = login_resp.json()

            print(
                "Odpowiedź serwera:",
                json.dumps(data, indent=2, ensure_ascii=False)
            )

            if data.get("success"):
                print("Zalogowano pomyślnie!")
            else:
                print(
                    "Logowanie nieudane:",
                    data.get("message", "brak komunikatu")
                )

        except ValueError:
            print(
                "Odpowiedź nie jest JSON:",
                login_resp.text[:500]
            )

    else:
        print(
            f"Błąd HTTP {login_resp.status_code}: "
            f"{login_resp.text[:500]}"
        )


if __name__ == "__main__":
    login()