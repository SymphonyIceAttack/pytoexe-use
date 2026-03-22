import tkinter as tk
from datetime import datetime
import win32print

# ---------------- PRODUCTOS ----------------

productos_comida = {
    "PAPAS PORCION":200,
    "PAPAS CHEDDAR PANCETA":350,
    "PANCHO COMUN":120,
    "PANCHO MUZZA":180,
    "PIZZA MUZZA":350,
    "PIZZA CON GUSTO":450,
    "PIZZA BOMBA":680,
    "HAMBURGUESA CLASICA":320,
    "HAMBURGUESA COMPLETA":400,
    "MILANESA AL PAN":380,
    "CHORIZO AL PAN":200,
    "PROMO 2 HAMBURGUESAS":600,
    "PROMO 2 PIZZAS MUZZA":600
}

productos_bebidas = {
    "REFRESCO 600ML":100,
    "REFRESCO 1.5L":200,
    "REFRESCO 2.25L":250,
    "AGUA 600ML":100,
    "AGUA 1.75L":150,
    "AGUA 2.5L":180,
    "AGUA SABORIZADA VITALE 600ML":100,
    "AGUA SABORIZADA VITALE 1.5L":200,
    "CERVEZA SIN ALCOHOL / MALTA":120,
    "NORTEÑA LATA":120,
    "PATRICIA LATA":140,
    "STELLA LATA":160,
    "PATRICIA 1L":250,
    "ZILLERTAL 1L":280,
    "STELLA ARTOIS 1L":300,
    "AMARGA C/CORTE":150,
    "FERNET C/CORTE":200,
    "JHONNY ROJO C/CORTE":220,
    "MONSTER":150,
    "VINO 1L":180,
    "HIELO":150,
    "PROMO 2 NORTEÑA":200,
    "PROMO PATRICIA 2L":450
}

productos = {}
productos.update(productos_comida)
productos.update(productos_bebidas)

# ---------------- VARIABLES ----------------

pedido = {}
observaciones = {}

numero_ticket = 1
total_vendido = 0
ventas_productos = {}

# ---------------- IMPRESION ----------------

def imprimir_ticket(texto):

    impresora = win32print.GetDefaultPrinter()
    hPrinter = win32print.OpenPrinter(impresora)

    try:
        win32print.StartDocPrinter(hPrinter, 1, ("Ticket", None, "RAW"))
        win32print.StartPagePrinter(hPrinter)

        inicio = b'\x1b\x40'
        inicio += b'\x1b\x61\x01'

        win32print.WritePrinter(hPrinter, inicio + texto.encode("cp850"))

        win32print.EndPagePrinter(hPrinter)
        win32print.EndDocPrinter(hPrinter)

    finally:
        win32print.ClosePrinter(hPrinter)


def centrar(texto):

    ancho = 48
    margen = 4

    return " " * margen + texto.center(ancho - margen * 2) + "\n"

# ---------------- PEDIDOS ----------------

def agregar(prod):

    pedido[prod] = pedido.get(prod, 0) + 1

    if prod not in observaciones:
        observaciones[prod] = []

    observaciones[prod].append("")

    actualizar()

def quitar(prod):

    if prod in pedido:

        pedido[prod] -= 1

        if pedido[prod] <= 0:

            del pedido[prod]
            del observaciones[prod]

        else:

            observaciones[prod].pop()

    actualizar()

def limpiar():

    pedido.clear()
    observaciones.clear()

    actualizar()

# ---------------- ACTUALIZAR PANTALLA ----------------

def actualizar():

    texto = ""
    total = 0

    for prod, cant in pedido.items():

        precio = productos[prod]

        for i in range(cant):

            obs = ""

            if observaciones[prod][i]:
                obs = f" ({observaciones[prod][i]})"

            texto += f"{prod} x1{obs} = ${precio}\n"

            total += precio

    visor.config(text=texto)

    total_label.config(text=f"$ {total}")

# ---------------- OBSERVACIONES ----------------

def agregar_observacion(prod):

    if prod not in productos_comida:
        return

    def guardar():

        texto = entry.get()

        if texto:

            for i in range(len(observaciones[prod])):

                if not observaciones[prod][i]:

                    observaciones[prod][i] = texto
                    break

        top.destroy()

        actualizar()

    top = tk.Toplevel()

    tk.Label(top, text="Observación").pack(pady=5)

    entry = tk.Entry(top, width=40)
    entry.pack(pady=5)

    tk.Button(top, text="Guardar", command=guardar).pack()

# ---------------- IMPRIMIR ----------------

def imprimir():

    global total_vendido, ventas_productos

    if not pedido:
        return

    agrupado = {}

    for prod, cant in pedido.items():

        for i in range(cant):

            obs = observaciones[prod][i]

            clave = (prod, obs)

            agrupado[clave] = agrupado.get(clave, 0) + 1

    detalle_cliente = ""
    detalle_cocina = ""
    detalle_bebidas = ""

    total_dinero = 0

    for (prod, obs), cant in agrupado.items():

        precio = productos[prod]

        subtotal = precio * cant

        obs_txt = f" ({obs})" if obs else ""

        if prod in productos_bebidas:
            detalle_bebidas += f"{prod:<30} x{cant}\n"
        else:
            detalle_cocina += f"{prod:<30} x{cant}{obs_txt}\n"

        detalle_cliente += f"{prod:<30} x{cant} ${subtotal:>5}{obs_txt}\n"

        ventas_productos[prod] = ventas_productos.get(prod, 0) + cant

        total_dinero += subtotal

    # COCINA

    texto = centrar("CAPRICHO")
    texto += centrar("TICKET COCINA")

    texto += "-"*48+"\n"
    texto += detalle_cocina
    texto += "-"*48+"\n"

    texto += centrar(f"NUMERO {numero_ticket}")

    texto += "\n\n\n\n"
    texto += "\x1dV\x00"

    imprimir_ticket(texto)

    # CLIENTE

    texto = centrar("CAPRICHO")
    texto += centrar("TICKET CLIENTE")

    texto += "-"*48+"\n"
    texto += detalle_cliente
    texto += "-"*48+"\n"

    texto += f"TOTAL: ${total_dinero}\n"

    texto += datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"\n"

    texto += centrar("GRACIAS POR SU COMPRA")

    texto += "\n\n\n\n"
    texto += "\x1dV\x00"

    imprimir_ticket(texto)

    # BEBIDAS

    if detalle_bebidas:

        texto = centrar("CAPRICHO")
        texto += centrar("TICKET BEBIDAS")

        texto += "-"*48+"\n"
        texto += detalle_bebidas
        texto += "-"*48+"\n"

        texto += datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"\n"

        texto += "\n\n\n\n"
        texto += "\x1dV\x00"

        imprimir_ticket(texto)

    total_vendido += total_dinero

    total_vendido_label.config(text=f"Total vendido: ${total_vendido}")

    limpiar()

# ---------------- CIERRE CAJA ----------------

def cierre_caja():

    global total_vendido, ventas_productos

    texto = centrar("CAPRICHO")
    texto += centrar("CIERRE DE CAJA")

    texto += "-"*48+"\n"

    texto += f"TOTAL VENDIDO: ${total_vendido}\n"

    texto += "-"*48+"\n"

    for prod, cant in ventas_productos.items():

        texto += f"{prod:<30} x{cant}\n"

    texto += "-"*48+"\n"

    texto += datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    texto += "\n\n\n\n"
    texto += "\x1dV\x00"

    imprimir_ticket(texto)

    total_vendido = 0
    ventas_productos = {}

    total_vendido_label.config(text="Total vendido: $0")

# ---------------- NUMEROS TICKET ----------------

def seleccionar_numero(n):

    global numero_ticket

    numero_ticket = n

    numero_label.config(text=f"Número seleccionado: {numero_ticket}")

# ---------------- INTERFAZ ----------------

ventana = tk.Tk()
ventana.title("Sistema de Tickets")
ventana.geometry("1450x820")

barra_superior = tk.Frame(ventana)
barra_superior.pack(fill="x")

total_vendido_label = tk.Label(barra_superior,
                               text="Total vendido: $0",
                               font=("Arial",18,"bold"),
                               bg="lightblue",
                               padx=20,
                               pady=10)

total_vendido_label.pack(side="right", padx=20)

contenedor = tk.Frame(ventana)
contenedor.pack(pady=25)

col_comidas = tk.Frame(contenedor)
col_comidas.pack(side="left", padx=20)

col_bebidas = tk.Frame(contenedor)
col_bebidas.pack(side="left", padx=20)

panel_der = tk.Frame(contenedor)
panel_der.pack(side="left", padx=35)

# ---------------- COMIDAS ----------------

tk.Label(col_comidas,text="COMIDAS",font=("Arial",16,"bold")).pack(pady=10)

for prod,precio in productos_comida.items():

    fila=tk.Frame(col_comidas)
    fila.pack(pady=3)

    tk.Label(fila,text=prod,width=22,anchor="w",font=("Arial",12,"bold")).pack(side="left")
    tk.Label(fila,text=f"${precio}",bg="yellow",width=6).pack(side="left")
    tk.Button(fila,text="+",width=4,command=lambda p=prod:agregar(p)).pack(side="left")
    tk.Button(fila,text="-",width=4,command=lambda p=prod:quitar(p)).pack(side="left")
    tk.Button(fila,text="Obs",command=lambda p=prod:agregar_observacion(p)).pack(side="left")

# ---------------- BEBIDAS (1 COLUMNA con scroll y botones visibles) ----------------

tk.Label(col_bebidas,text="BEBIDAS",font=("Arial",16,"bold")).pack(pady=10)

canvas_bebidas = tk.Canvas(col_bebidas, width=420, height=550)
scrollbar_bebidas = tk.Scrollbar(col_bebidas, orient="vertical", command=canvas_bebidas.yview)
canvas_bebidas.configure(yscrollcommand=scrollbar_bebidas.set)

scrollbar_bebidas.pack(side="right", fill="y")
canvas_bebidas.pack(side="left", fill="both", expand=True)

frame_bebidas = tk.Frame(canvas_bebidas)
canvas_bebidas.create_window((0,0), window=frame_bebidas, anchor="nw")

def actualizar_scroll(event):
    canvas_bebidas.configure(scrollregion=canvas_bebidas.bbox("all"))

frame_bebidas.bind("<Configure>", actualizar_scroll)

for prod, precio in productos_bebidas.items():
    fila = tk.Frame(frame_bebidas)
    fila.pack(pady=2, anchor="w", padx=(0,20))  # padding derecho para que el botón - no quede tapado
    tk.Label(fila,text=prod,width=30,anchor="w",font=("Arial",12,"bold")).pack(side="left")
    tk.Label(fila,text=f"${precio}",bg="lightblue",width=6).pack(side="left")
    tk.Button(fila,text="+",width=4,command=lambda p=prod:agregar(p)).pack(side="left")
    tk.Button(fila,text="-",width=4,command=lambda p=prod:quitar(p)).pack(side="left")

# ---------------- PEDIDO ----------------

tk.Label(panel_der,text="PEDIDO",font=("Arial",16)).pack()

visor=tk.Label(panel_der,text="",justify="left",
               font=("Courier",13),
               bg="white",
               width=38,
               height=8,
               anchor="nw")

visor.pack(pady=8)

numero_label=tk.Label(panel_der,text="Número seleccionado: 1",
                      font=("Arial",15),
                      bg="lightgray")

numero_label.pack(pady=4,fill="x")

# BOTONERA 1-21

botonera=tk.Frame(panel_der)
botonera.pack(pady=6)

for n in range(1,22):

    tk.Button(botonera,
              text=str(n),
              width=4,
              font=("Arial",12,"bold"),
              command=lambda x=n:seleccionar_numero(x)
              ).grid(row=(n-1)//7,column=(n-1)%7,padx=2,pady=2)

# TOTAL

tk.Label(panel_der,text="TOTAL",font=("Arial",14)).pack()

total_label=tk.Label(panel_der,text="$ 0",
                     font=("Arial",22,"bold"),
                     bg="red",
                     fg="white",
                     width=8)

total_label.pack(pady=5)

# BOTONES

acciones=tk.Frame(panel_der)
acciones.pack(pady=5)

tk.Button(acciones,text="IMPRIMIR",
          bg="green",fg="white",
          width=12,height=2,
          command=imprimir).pack(side="left",padx=5)

tk.Button(acciones,text="BORRAR",
          bg="red",fg="white",
          width=12,height=2,
          command=limpiar).pack(side="left",padx=5)

tk.Button(acciones,text="CIERRE CAJA",
          bg="blue",fg="white",
          width=12,height=2,
          command=cierre_caja).pack(side="left",padx=5)

ventana.mainloop()