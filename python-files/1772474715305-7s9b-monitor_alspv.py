import os
import shutil
import time
import re
from datetime import datetime
import pdfplumber  # pip install pdfplumber

descargas = r"C:\Users\Javier Sousa\Downloads"
destino = r"C:\Users\Javier Sousa\Desktop\ALSPV'S Incidencias"
cadena_origen = "varwwwwashnet.sat-on.comwebfotosParte"

os.makedirs(destino, exist_ok=True)

def limpiar_nombre(nombre):
    nombre = re.sub(r'[\\/*?:"<>|]', "_", nombre)
    nombre = nombre.strip().replace(" ", "_")
    return nombre

def eliminar_duplicados_bloques(texto):
    partes = texto.split("_")
    resultado = []
    vistos = set()

    for parte in partes:
        parte = parte.strip()
        if parte and parte not in vistos:
            resultado.append(parte)
            vistos.add(parte)

    return "_".join(resultado)

def archivo_terminado(ruta):
    tamaño_anterior = -1
    for _ in range(10):
        if not os.path.exists(ruta):
            return False
        tamaño_actual = os.path.getsize(ruta)
        if tamaño_actual == tamaño_anterior:
            return True
        tamaño_anterior = tamaño_actual
        time.sleep(1)
    return False

def procesar_pdf(ruta_pdf):

    if not archivo_terminado(ruta_pdf):
        return

    temp_pdf = os.path.join(destino, "temp.pdf")

    try:
        shutil.copy2(ruta_pdf, temp_pdf)
    except:
        return

    try:
        with pdfplumber.open(temp_pdf) as pdf:
            texto = pdf.pages[0].extract_text()

        lineas = texto.split("\n")

        # -------- ALSPV --------
        num_parte = "ALSPV-000"
        for linea in lineas:
            if "ALSPV" in linea:
                partes = linea.split()
                for p in partes:
                    if p.startswith("ALSPV"):
                        num_parte = p.strip()
                        break
                break

        # -------- DIRECCIÓN --------
        primera_linea = ""
        ciudad = ""
        capturando = False

        for linea in lineas:
            if "Dirección de actuación" in linea:
                capturando = True
                continue

            if capturando:
                if primera_linea == "":
                    primera_linea = linea.strip()

                match = re.search(r'\b\d{5}\b', linea)
                if match:
                    ciudad_linea = linea[match.end():].strip()
                    ciudad_match = re.search(r'[A-ZÁÉÍÓÚÑ\.]+', ciudad_linea)
                    if ciudad_match:
                        ciudad = ciudad_match.group(0)
                    break

        # -------- TÉCNICO --------
        tecnico = ""
        for linea in reversed(lineas):
            if "Técnico :" in linea:
                tecnico = linea.split("Técnico :")[-1].strip()
                break

        # -------- LIMPIAR --------
        primera_linea = limpiar_nombre(primera_linea)
        ciudad = limpiar_nombre(ciudad)
        tecnico = limpiar_nombre(tecnico)

        fecha = datetime.now().strftime("%d-%m-%Y")

        nombre_base = f"{num_parte}_{primera_linea}_{ciudad}_{tecnico}_{fecha}"
        nombre_base = eliminar_duplicados_bloques(nombre_base)

        nombre_final = nombre_base + ".pdf"
        ruta_final = os.path.join(destino, nombre_final)

        contador = 1
        base, ext = os.path.splitext(ruta_final)
        while os.path.exists(ruta_final):
            ruta_final = f"{base}_{contador}{ext}"
            contador += 1

        os.rename(temp_pdf, ruta_final)
        os.remove(ruta_pdf)

        print("Procesado correctamente:", nombre_final)

    except Exception as e:
        print("Error procesando:", e)
        if os.path.exists(temp_pdf):
            os.remove(temp_pdf)

print("Sistema automático iniciado...")

while True:
    for archivo in os.listdir(descargas):
        if archivo.endswith(".pdf") and cadena_origen in archivo:
            ruta = os.path.join(descargas, archivo)
            procesar_pdf(ruta)
    time.sleep(1)
