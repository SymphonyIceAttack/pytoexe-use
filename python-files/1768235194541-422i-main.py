# main.py
import requests
from cryptography.fernet import Fernet

OWNER_EMAIL = "istvanmajsai70@gmail.com"
OWNER_PHONE = "+36 30 626 0688"
OWNER_IBAN = "LT81 3250 0757 5026 3901"

def demo():
    print("DEMO verzió: korlátozott funkciók")
    print("PRO verzió vásárlásához írj az email-re:", OWNER_EMAIL)

def run_pro(license_key):
    r = requests.post("https://YOUR_SERVER/api/check_license", json={"license": license_key})
    if r.status_code != 200:
        print("❌ Érvénytelen licenc")
        return
    key = r.json()["decrypt_key"]
    cipher = Fernet(key.encode())
    with open("pro.enc", "rb") as f:
        exec(cipher.decrypt(f.read()), {})

if __name__ == "__main__":
    choice = input("DEMO vagy PRO? (D/P): ").upper()
    if choice == "D":
        demo()
    else:
        lic = input("Írd be a licenc kulcsot: ")
        run_pro(lic)