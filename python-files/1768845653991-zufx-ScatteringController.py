import tkinter as tk
import serial
import time
import matplotlib.pyplot as plt
import pandas as pd
import threading

import numpy as np

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from pathlib import Path

RutaScattering = Path.home() / "Documents" / "Scattering"
RutaScattering.mkdir(parents=True, exist_ok=True)

# ============================================================
# Parámetros
MPGD = '20'
GradosD = '180'
PasosD = '1'
PuertoD= 'COM3'

GrafD = 'Prueba1'
CSVD = 'Datos_Prueba1'
RutaD = str(RutaScattering)

arduino = None  # para poder cerrar el puerto

# ============================================================
# Buffers para gráfica en tiempo real
tiempo_rt = []
det_rt = []

# ============================================================
# Toma de datos
def Scattering(d1, d2, d3, d4, nombre_grafica, nombre_csv, ruta, label_progreso, root):
    global arduino
    
    btn.config(bg="yellow")
    d3 = int(d2 / d3) 
    
    booleana = True
    PasosTotal = d3 * 4
    label_progreso.config(text="Progreso: 0 %")

    tiempo_rt.clear()
    det_rt.clear()

    try:
        arduino = serial.Serial(d4, 9600, timeout=2)
        time.sleep(2)

        mensaje = f"{d1},{d2},{d3}\n"
        arduino.write(mensaje.encode())

        polarizador = np.zeros(PasosTotal)
        grados = np.zeros(PasosTotal)
        mediciones = np.zeros(PasosTotal)
        errores = np.zeros(PasosTotal)
        Progreso = np.zeros(PasosTotal)

        i = 0
        while i < PasosTotal:
            linea = arduino.readline().decode().strip()
            if not linea:
                continue

            if linea == "STOP":
                label_progreso.config(text="Medición Cancelada")
                booleana = False
                break
            
            # Ruido de Fondo
            if linea == "BACK":
                label_progreso.config(text="Ruido de Fondo")
                angulosruido = []
                señalderuido = []

                for _ in range(d3):
                    linea_ruido = arduino.readline().decode().strip()
                    ang, ruido = linea_ruido.split(',')
                    angulosruido.append(float(ang))
                    señalderuido.append(float(ruido))

                plt.plot(angulosruido, señalderuido, color='black')
                plt.title(nombre_grafica + '_Ruido')
                plt.grid(True)
                plt.savefig(ruta + "\\" + nombre_grafica + '_Ruido.png', dpi=300)
                plt.show()
                
                # Guardar csv
                df = pd.DataFrame({
                    'Angulo':angulosruido,
                    'Detector': señalderuido
                })
                
                df.to_csv(f"{ruta}\\{nombre_csv}_Background.csv", index=True)
                continue
            
            #============================================================
            # Mediciones de scattering
            
            btn.config(bg="green")

            data = linea.split(',')
            if len(data) != 4:
                continue

            AngPol, AngDet, Det, Err = map(float, data)

            polarizador[i] = AngPol
            grados[i] = AngDet
            mediciones[i] = abs(Det)
            errores[i] = Err
            Progreso[i] = i

            # Gráfica en tiempo real
            tiempo_rt.append(i)
            det_rt.append(abs(Det))
            root.after(0, actualizar_grafica_rt)

            S = i * 100 / PasosTotal
            label_progreso.config(text=f"Progreso: {S:.2f} %")
            root.update_idletasks()

            i += 1
        
        # Finalizar todos los procesos
        if booleana == True:
            label_progreso.config(text="Progreso: 100 %")
        
        Plots(polarizador, grados, mediciones, errores, Progreso,
             d1, d2, d3, d4, nombre_grafica, nombre_csv, ruta, label_progreso)

    finally:
        btn.config(bg="red")
        if arduino and arduino.is_open:
            arduino.close()

# ============================================================
# Función para todos los plots
def Plots(polarizador,grados,mediciones,errores,Progreso,d1, d2, d3, d4, nombre_grafica, nombre_csv, ruta, label_progreso,):
    mediciones1, mediciones2, mediciones3, mediciones4 = np.split(mediciones,4)
    errores1, errores2, errores3, errores4 = np.split(errores,4)
    ang1, ang2, ang3, ang4 = np.split(grados,4)
    
    colores = ['red', 'blue', 'yellow', 'green']

    # Gráficas
    plt.scatter(ang1, mediciones1, label='Pol: 0',color = colores[0])
    plt.scatter(ang2, mediciones2, label='Pol: 45',color = colores[1])
    plt.scatter(ang3, mediciones3, label='Pol: 90',color = colores[2])
    plt.scatter(ang4, mediciones4, label='Pol: 135',color = colores[3])
    plt.legend()
    plt.grid(True)
    plt.title('Scattering')
    plt.xlabel('Ángulo')
    plt.ylabel('Intensidad')
    plt.yscale('log')
    plt.savefig(ruta + "\\" + nombre_grafica + '_Resultados1.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Graficas por separado
    fig, axs = plt.subplots(2, 2, figsize=(10, 8))

    datos = [mediciones1, mediciones2, mediciones3, mediciones4]
    angulos = [0, 45, 90, 135]
    
    for ax, data, ang, col in zip(axs.flat, datos, angulos, colores):
        ax.plot(ang1, data, color=col)
        ax.set_title(f'Pol: {ang}°')
        ax.grid(True)
        
    plt.tight_layout()
    plt.suptitle('Scattering por separado')
    plt.savefig(ruta + "\\" + nombre_grafica + '_Resultados2.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Gráfica de Errores
    fig, axs = plt.subplots(2, 2, figsize=(10, 8))
    
    datos = [errores1, errores2, errores3, errores4]
    
    for ax, data, ang, col in zip(axs.flat, datos, angulos, colores):
        ax.scatter(ang1, data, color=col)
        ax.set_title(f'Pol: {ang}°')
        ax.grid(True)
        ax.set_yscale('log')
    
    plt.tight_layout()
    plt.suptitle('Gráfica de error')
    plt.savefig(ruta + "\\"+ nombre_grafica + '_Error.png', dpi=300, bbox_inches='tight')
    plt.show()

    # Proceso paso a paso
    plt.plot(Progreso, mediciones)
    plt.grid(True)
    plt.title('Detección')
    plt.xlabel('Pasos')
    plt.ylabel('Intensidad')
    plt.yscale('log')
    plt.savefig(ruta + "\\" + nombre_grafica + '_Detección.png', dpi=300, bbox_inches='tight')
    plt.show()

    # Guardar csv
    df = pd.DataFrame({
        'Polarizador': polarizador,
        'Ángulo': grados,
        'Detector': mediciones,
        'Error': errores
    })
    
    df.to_csv(f"{ruta}\\{nombre_csv}.csv", index=True)

# ============================================================
# Interfaz
def ejecutar_Scattering():
    hilo = threading.Thread(
        target=Scattering,
        args=(
            int(entry1.get()),
            int(entry2.get()),
            int(entry3.get()),
            entry4.get(),
            entry_grafica.get(),
            entry_csv.get(),
            entry_ruta.get(),
            label_progreso,
            root
        ),
        daemon=True
    )
    hilo.start()

# Ventana
root = tk.Tk()
root.resizable(False, False)
root.title("Control de Scattering")

# Titulo
tk.Label(
    root,
    text="Control de Scattering",
    font=("Arial", 16, "bold")
).grid(row=0, column=0, columnspan=4, pady=10)

# Gráfica en tiempo real mostrada en la interfaz
fig_rt = Figure(figsize=(6, 3), dpi=100)
ax_rt = fig_rt.add_subplot(111)
ax_rt.set_xlabel("Tiempo")
ax_rt.set_ylabel("Detección")
ax_rt.grid(True)
fig_rt.subplots_adjust(bottom=0.25)

linea_rt, = ax_rt.plot([], [], 'o-')

def actualizar_grafica_rt():
    linea_rt.set_data(tiempo_rt, det_rt)
    ax_rt.relim()
    ax_rt.autoscale_view()
    canvas_rt.draw()

canvas_rt = FigureCanvasTkAgg(fig_rt, master=root)
canvas_rt.get_tk_widget().grid(row=1, column=0, columnspan=4, padx=10, pady=5)

# ============================================================
# Entradas
tk.Label(root, text="Mediciones/grado").grid(row=2, column=0, sticky="e")
tk.Label(root, text="Grados de Recorrido").grid(row=3, column=0, sticky="e")
tk.Label(root, text="Salto").grid(row=4, column=0, sticky="e")
tk.Label(root, text="Puerto").grid(row=5, column=0, sticky="e")

entry1 = tk.Entry(root)
entry2 = tk.Entry(root)
entry3 = tk.Entry(root)
entry4 = tk.Entry(root)

entry1.insert(0, MPGD)
entry2.insert(0, GradosD)
entry3.insert(0, PasosD)
entry4.insert(0, PuertoD)

entry1.grid(row=2, column=1)
entry2.grid(row=3, column=1)
entry3.grid(row=4, column=1)
entry4.grid(row=5, column=1)

# Entrada para el archivo y las graficas
tk.Label(root, text="Rótulo").grid(row=6, column=0, sticky="e")
tk.Label(root, text="Título CSV").grid(row=7, column=0, sticky="e")

entry_grafica = tk.Entry(root)
entry_csv = tk.Entry(root)

entry_grafica.insert(0, GrafD)
entry_csv.insert(0, CSVD)

entry_grafica.grid(row=6, column=1)
entry_csv.grid(row=7, column=1)

# Ruta de guardado
tk.Label(root, text="Ruta de guardado").grid(row=8, column=0, sticky="e", padx=5)

entry_ruta = tk.Entry(root, width=42)
entry_ruta.insert(0, RutaD)
entry_ruta.grid(row=8, column=1, columnspan=2, sticky="w", padx=5)

# Indicador de progreso
label_progreso = tk.Label(root, text="Progreso: 0 %")
label_progreso.grid(row=9, column=0, columnspan=4, pady=10)

btn = tk.Button(root, text="Iniciar Datos", bg='red', command=ejecutar_Scattering)
btn.grid(row=10, column=0, columnspan=4, pady=10)

root.mainloop()