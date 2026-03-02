import os
import re
import shutil
import time
import logging
from datetime import datetime
import pdfplumber
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import ctypes

# Bloqueo para que no se abra doble instancia
mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "Global\\ALSPV_MONITOR_MUTEX")
if ctypes.windll.kernel32.GetLastError() == 183:
    exit(0)

# Rutas
DESCARGAS = os.path.join(os.path.expanduser("~"), "Downloads")
DESTINO = os.path.join(os.path.expanduser("~"), "Desktop", "Incidencias_ALSPV")
os.makedirs(DESTINO, exist_ok=True)

LOG_PATH = os.path.join(DESTINO, "monitor.log")

logging.basicConfig(filename=LOG_PATH, level=logging.INFO, format="%(asctime)s - %(message)s")

CADENA_ORIGEN = "varwwwwashnet.sat-on.comwebfotosParte"

def limpiar(texto):
    texto = re.sub(r'[\\/*?:"<>|]', "", texto)
    texto = texto.strip().replace(" ", "_")
    return texto

def eliminar_duplicados(nombre):
    partes = nombre.split("_")
    resultado = []
    for p in partes:
        if p and p not in resultado:
            resultado.append(p)
    return "_".join(resultado)

def esperar_archivo_completo(ruta):
    tamaño_anterior = -1
    while True:
        tamaño_actual = os.path.getsize(ruta)
        if tamaño_actual == tamaño_anterior:
            return True
        tamaño_anterior = tamaño_actual
        time.sleep(0.5)

def procesar_pdf(ruta_pdf):
    try:
        esperar_archivo_completo(ruta_pdf)
        temp_pdf = os.path.join(DESTINO, "temp.pdf")
        shutil.copy2(ruta_pdf, temp_pdf)

        with pdfplumber.open(temp_pdf) as pdf:
            texto = pdf.pages[0].extract_text()

        lineas = texto.split("\n")

        alspv = next((w for l in lineas if "ALSPV" in l
                      for w in l.split() if w.startswith("ALSPV")), "ALSPV-000")

        primera_linea = ""
        ciudad = ""
        capturando = False

        for linea in lineas:
            if "Dirección de actuación" in linea:
                capturando = True
                continue
            if capturando:
                if not primera_linea:
                    primera_linea = linea.strip()
                match = re.search(r'\b\d{5}\b', linea)
                if match:
                    ciudad = linea[match.end():].strip()
                    break

        tecnico = next((l.split("Técnico :")[-1].strip()
                        for l in reversed(lineas) if "Técnico :" in l), "")

        fecha = datetime.now().strftime("%d-%m-%Y")

        nombre = f"{alspv}_{primera_linea}_{ciudad}_{tecnico}_{fecha}"
        nombre = eliminar_duplicados(limpiar(nombre))

        ruta_final = os.path.join(DESTINO, nombre + ".pdf")

        contador = 1
        while os.path.exists(ruta_final):
            ruta_final = os.path.join(DESTINO, f"{nombre}_{contador}.pdf")
            contador += 1

        os.rename(temp_pdf, ruta_final)
        os.remove(ruta_pdf)

        logging.info(f"Procesado: {nombre}")

    except Exception as e:
        logging.info(f"Error procesando {ruta_pdf}: {e}")

class Monitor(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".pdf"):
            if CADENA_ORIGEN in event.src_path:
                procesar_pdf(event.src_path)

if __name__ == "__main__":
    observer = Observer()
    observer.schedule(Monitor(), DESCARGAS, recursive=False)
    observer.start()
    logging.info("Monitor ALSPV iniciado.")

    try:
        while True:
            time.sleep(10)  # mínima CPU
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
