import requests

LICENSE_SERVER = "https://your-priv-server.com/check"

def analyze_document(text):
    # AI összefoglaló példa (demo logika)
    return text[:500] + " ... (PRO összefoglaló)"

def demo_features(text):
    print("DEMO mód - korlátozott funkció")
    print(analyze_document(text[:200]))

def pro_features(text):
    print("PRO mód - teljes AI elemzés")
    print(analyze_document(text))

license_key = input("Licenc kulcs (Enter = DEMO): ")

sample_text = "Ez egy példa dokumentum, amelyet az AI analizálni fog..."

if license_key:
    try:
        r = requests.post(LICENSE_SERVER, json={"license": license_key}, timeout=5)
        if r.status_code == 200 and r.json().get("valid"):
            pro_features(sample_text)
        else:
            demo_features(sample_text)
    except:
        print("Licenc szerver nem elérhető")
        demo_features(sample_text)
else:
    demo_features(sample_text)