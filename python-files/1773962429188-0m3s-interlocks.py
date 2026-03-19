import tkinter as tk
from tkinter import ttk, messagebox
import csv
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('TkAgg')  # Para integrar con tkinter
from collections import Counter, defaultdict
import os
import sys

# Intentamos importar seaborn para gráficos más bonitos (opcional)
try:
    import seaborn as sns
    SEABORN_AVAILABLE = True
except ImportError:
    SEABORN_AVAILABLE = False

# Archivo CSV donde se guardan los registros
CSV_FILE = "interlocks.csv"
TIPOS_INTERLOCK = [
    "Puerta",
    "Radiación",
    "Agua",
    "Temperatura",
    "Vacío",
    "Dosimetría",
    "Colisión",
    "Otro"
]

def inicializar_csv():
    """Crea el archivo CSV con cabeceras si no existe."""
    if not os.path.isfile(CSV_FILE):
        with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Fecha", "Hora", "Tipo", "Descripción", "Técnico"])

def guardar_registro(fecha, hora, tipo, descripcion, tecnico):
    """Guarda un nuevo registro en el CSV."""
    with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([fecha, hora, tipo, descripcion, tecnico])

def cargar_registros():
    """
    Lee todo el CSV y devuelve una lista de diccionarios.
    Si el archivo no existe, retorna lista vacía.
    """
    registros = []
    try:
        with open(CSV_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                registros.append(row)
    except FileNotFoundError:
        pass
    return registros

def filtrar_por_mes(registros, mes, año):
    """Filtra registros por mes y año."""
    filtrados = []
    for r in registros:
        try:
            fecha = datetime.strptime(r['Fecha'], "%Y-%m-%d")
            if fecha.month == mes and fecha.year == año:
                filtrados.append(r)
        except (ValueError, KeyError):
            continue
    return filtrados

def contar_por_tipo(registros):
    """Devuelve un Counter con tipos y frecuencias."""
    return Counter(r['Tipo'] for r in registros)

def contar_por_dia(registros):
    """Devuelve un diccionario {dia: {tipo: frecuencia}} y total por día."""
    por_dia = defaultdict(Counter)
    for r in registros:
        dia = r['Fecha']  # formato YYYY-MM-DD
        por_dia[dia][r['Tipo']] += 1
    return por_dia

def grafico_barras(contador, mes, año, tipo_grafico='barras'):
    """Muestra gráfico de barras o pastel con estilo mejorado."""
    if not contador:
        messagebox.showinfo("Sin datos", f"No hay registros para {mes}/{año}")
        return

    tipos = list(contador.keys())
    frecuencias = list(contador.values())

    # Configurar estilo
    if SEABORN_AVAILABLE:
        sns.set_style("whitegrid")
        paleta = sns.color_palette("husl", len(tipos))
    else:
        plt.style.use('ggplot')
        paleta = plt.cm.tab20.colors

    fig, ax = plt.subplots(figsize=(10, 6))

    if tipo_grafico == 'barras':
        ax.bar(tipos, frecuencias, color=paleta, edgecolor='black', linewidth=1.2)
        ax.set_ylabel("Frecuencia", fontsize=12)
        ax.set_xlabel("Tipo de Interlock", fontsize=12)
        # Añadir números encima de las barras
        for i, v in enumerate(frecuencias):
            ax.text(i, v + 0.1, str(v), ha='center', fontsize=10, fontweight='bold')
    else:  # pastel
        # Si hay muchas categorías con poca frecuencia, agrupar "Otros"
        if len(tipos) > 6:
            # Ordenar por frecuencia y tomar los 5 mayores, el resto como "Otros"
            ordenado = sorted(contador.items(), key=lambda x: x[1], reverse=True)
            principales = ordenado[:5]
            otros = sum(x[1] for x in ordenado[5:])
            if otros > 0:
                principales.append(("Otros", otros))
            tipos = [x[0] for x in principales]
            frecuencias = [x[1] for x in principales]
        ax.pie(frecuencias, labels=tipos, autopct='%1.1f%%', startangle=90,
               colors=paleta, wedgeprops={'edgecolor': 'white', 'linewidth': 1})
        ax.set_ylabel('')  # eliminar etiqueta del eje y

    ax.set_title(f"Interlocks reportados en {mes}/{año}", fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.show()

def grafico_barras_apiladas_por_dia(por_dia, mes, año):
    """Muestra un gráfico de barras apiladas por día."""
    if not por_dia:
        messagebox.showinfo("Sin datos", f"No hay registros para {mes}/{año}")
        return

    # Obtener todos los tipos únicos presentes en el mes
    tipos_unicos = set()
    for counter in por_dia.values():
        tipos_unicos.update(counter.keys())
    tipos_unicos = sorted(tipos_unicos)

    # Preparar datos: días ordenados y matrices de frecuencias
    dias = sorted(por_dia.keys())
    frecuencias_por_tipo = {tipo: [] for tipo in tipos_unicos}
    for dia in dias:
        for tipo in tipos_unicos:
            frecuencias_por_tipo[tipo].append(por_dia[dia].get(tipo, 0))

    # Crear gráfico de barras apiladas
    fig, ax = plt.subplots(figsize=(12, 6))
    bottom = [0] * len(dias)
    x = range(len(dias))

    if SEABORN_AVAILABLE:
        paleta = sns.color_palette("husl", len(tipos_unicos))
    else:
        paleta = plt.cm.tab20.colors

    for i, tipo in enumerate(tipos_unicos):
        ax.bar(x, frecuencias_por_tipo[tipo], bottom=bottom, label=tipo, color=paleta[i % len(paleta)], edgecolor='white')
        bottom = [b + f for b, f in zip(bottom, frecuencias_por_tipo[tipo])]

    ax.set_xlabel("Día", fontsize=12)
    ax.set_ylabel("Frecuencia", fontsize=12)
    ax.set_title(f"Interlocks por día - {mes}/{año}", fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([d[-2:] for d in dias], rotation=45)  # mostrar solo día
    ax.legend(title="Tipo", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.show()

class Aplicacion:
    def __init__(self, root):
        self.root = root
        self.root.title("Registro de Interlocks - Acelerador Lineal")
        self.root.geometry("750x500")
        self.root.minsize(700, 450)

        # Variables para el formulario
        self.tipo_var = tk.StringVar()
        self.descripcion_var = tk.StringVar()
        self.tecnico_var = tk.StringVar()
        self.fecha_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.hora_var = tk.StringVar(value=datetime.now().strftime("%H:%M"))

        # Variables para reportes
        self.mes_var = tk.StringVar()
        self.año_var = tk.StringVar()
        self.tipo_grafico_var = tk.StringVar(value="barras")

        inicializar_csv()

        # Crear pestañas
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Pestaña de registro
        self.frame_registro = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_registro, text="Registro")
        self.crear_pestania_registro()

        # Pestaña de reportes
        self.frame_reportes = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_reportes, text="Reportes")
        self.crear_pestania_reportes()

        # Pestaña de datos
        self.frame_datos = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_datos, text="Ver Datos")
        self.crear_pestania_datos()

    def crear_pestania_registro(self):
        frame = self.frame_registro
        padding = {'padx': 10, 'pady': 5}

        # Fecha
        ttk.Label(frame, text="Fecha (YYYY-MM-DD):").grid(row=0, column=0, sticky=tk.W, **padding)
        ttk.Entry(frame, textvariable=self.fecha_var, width=15).grid(row=0, column=1, sticky=tk.W, **padding)
        ttk.Button(frame, text="Hoy", command=self.poner_fecha_hoy).grid(row=0, column=2, **padding)

        # Hora
        ttk.Label(frame, text="Hora (HH:MM):").grid(row=1, column=0, sticky=tk.W, **padding)
        ttk.Entry(frame, textvariable=self.hora_var, width=10).grid(row=1, column=1, sticky=tk.W, **padding)
        ttk.Button(frame, text="Ahora", command=self.poner_hora_ahora).grid(row=1, column=2, **padding)

        # Tipo
        ttk.Label(frame, text="Tipo de Interlock:*").grid(row=2, column=0, sticky=tk.W, **padding)
        combo_tipo = ttk.Combobox(frame, textvariable=self.tipo_var, values=TIPOS_INTERLOCK, state="readonly", width=20)
        combo_tipo.grid(row=2, column=1, sticky=tk.W, **padding)
        combo_tipo.current(0)

        # Descripción
        ttk.Label(frame, text="Descripción:").grid(row=3, column=0, sticky=tk.W, **padding)
        ttk.Entry(frame, textvariable=self.descripcion_var, width=40).grid(row=3, column=1, columnspan=2, sticky=tk.W, **padding)

        # Técnico
        ttk.Label(frame, text="Técnico:").grid(row=4, column=0, sticky=tk.W, **padding)
        ttk.Entry(frame, textvariable=self.tecnico_var, width=40).grid(row=4, column=1, columnspan=2, sticky=tk.W, **padding)

        # Botón guardar
        ttk.Button(frame, text="Guardar Registro", command=self.guardar).grid(row=5, column=0, columnspan=3, pady=20)

        # Mensaje de campos obligatorios
        ttk.Label(frame, text="* Campo obligatorio", font=('Arial', 8, 'italic')).grid(row=6, column=0, columnspan=3, sticky=tk.W)

    def poner_fecha_hoy(self):
        self.fecha_var.set(datetime.now().strftime("%Y-%m-%d"))

    def poner_hora_ahora(self):
        self.hora_var.set(datetime.now().strftime("%H:%M"))

    def crear_pestania_reportes(self):
        frame = self.frame_reportes
        padding = {'padx': 10, 'pady': 5}

        # Selección de mes y año
        ttk.Label(frame, text="Mes (1-12):").grid(row=0, column=0, sticky=tk.W, **padding)
        meses = [str(i) for i in range(1, 13)]
        combo_mes = ttk.Combobox(frame, textvariable=self.mes_var, values=meses, state="readonly", width=5)
        combo_mes.grid(row=0, column=1, sticky=tk.W, **padding)
        combo_mes.current(datetime.now().month - 1)

        ttk.Label(frame, text="Año:").grid(row=1, column=0, sticky=tk.W, **padding)
        años = [str(datetime.now().year - i) for i in range(5)]  # últimos 5 años
        combo_año = ttk.Combobox(frame, textvariable=self.año_var, values=años, state="readonly", width=6)
        combo_año.grid(row=1, column=1, sticky=tk.W, **padding)
        combo_año.current(0)

        # Tipo de gráfico
        ttk.Label(frame, text="Tipo de gráfico:").grid(row=2, column=0, sticky=tk.W, **padding)
        ttk.Radiobutton(frame, text="Barras", variable=self.tipo_grafico_var, value="barras").grid(row=2, column=1, sticky=tk.W, **padding)
        ttk.Radiobutton(frame, text="Pastel", variable=self.tipo_grafico_var, value="pastel").grid(row=2, column=2, sticky=tk.W, **padding)

        # Botones
        ttk.Button(frame, text="Ver gráfico mensual", command=self.mostrar_reporte_mensual).grid(row=3, column=0, columnspan=3, pady=10)
        ttk.Button(frame, text="Ver distribución por día", command=self.mostrar_reporte_diario).grid(row=4, column=0, columnspan=3, pady=5)

        # Separador
        ttk.Separator(frame, orient='horizontal').grid(row=5, column=0, columnspan=3, sticky=tk.EW, pady=15)

        # Opción de exportar
        ttk.Label(frame, text="Exportar gráfico actual (después de generarlo)").grid(row=6, column=0, columnspan=3, pady=5)
        ttk.Button(frame, text="Guardar gráfico como PNG", command=self.guardar_grafico).grid(row=7, column=0, columnspan=3, pady=5)

    def crear_pestania_datos(self):
        frame = self.frame_datos
        padding = {'padx': 10, 'pady': 5}

        # Filtro de mes/año para la tabla
        ttk.Label(frame, text="Mostrar datos de:").grid(row=0, column=0, sticky=tk.W, **padding)
        self.mes_tabla_var = tk.StringVar(value=str(datetime.now().month))
        self.año_tabla_var = tk.StringVar(value=str(datetime.now().year))
        meses = [str(i) for i in range(1, 13)]
        combo_mes_tabla = ttk.Combobox(frame, textvariable=self.mes_tabla_var, values=meses, state="readonly", width=5)
        combo_mes_tabla.grid(row=0, column=1, **padding)
        años = [str(datetime.now().year - i) for i in range(5)]
        combo_año_tabla = ttk.Combobox(frame, textvariable=self.año_tabla_var, values=años, state="readonly", width=6)
        combo_año_tabla.grid(row=0, column=2, **padding)
        ttk.Button(frame, text="Cargar", command=self.cargar_tabla).grid(row=0, column=3, **padding)

        # Treeview para mostrar los registros
        columnas = ('Fecha', 'Hora', 'Tipo', 'Descripción', 'Técnico')
        self.tree = ttk.Treeview(frame, columns=columnas, show='headings', height=15)
        for col in columnas:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor=tk.CENTER)
        self.tree.column('Descripción', width=200)
        self.tree.grid(row=1, column=0, columnspan=4, pady=10, padx=5, sticky=tk.NSEW)

        # Scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.grid(row=1, column=4, sticky=tk.NS)
        self.tree.configure(yscrollcommand=scrollbar.set)

        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

    def guardar(self):
        tipo = self.tipo_var.get()
        if not tipo:
            messagebox.showerror("Error", "Debes seleccionar un tipo de interlock")
            return
        fecha = self.fecha_var.get()
        hora = self.hora_var.get()
        desc = self.descripcion_var.get()
        tec = self.tecnico_var.get()
        # Validar formato de fecha (simple)
        try:
            datetime.strptime(fecha, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "Formato de fecha incorrecto. Use YYYY-MM-DD")
            return
        guardar_registro(fecha, hora, tipo, desc, tec)
        messagebox.showinfo("Éxito", "Registro guardado correctamente")
        # Limpiar campos opcionales
        self.descripcion_var.set("")
        self.tecnico_var.set("")

    def mostrar_reporte_mensual(self):
        try:
            mes = int(self.mes_var.get())
            año = int(self.año_var.get())
        except (ValueError, TypeError):
            messagebox.showerror("Error", "Selecciona mes y año válidos")
            return
        registros = cargar_registros()
        filtrados = filtrar_por_mes(registros, mes, año)
        contador = contar_por_tipo(filtrados)
        # Guardar el último contador para posible exportación
        self.ultimo_contador = contador
        self.ultimo_mes = mes
        self.ultimo_año = año
        grafico_barras(contador, mes, año, self.tipo_grafico_var.get())

    def mostrar_reporte_diario(self):
        try:
            mes = int(self.mes_var.get())
            año = int(self.año_var.get())
        except (ValueError, TypeError):
            messagebox.showerror("Error", "Selecciona mes y año válidos")
            return
        registros = cargar_registros()
        filtrados = filtrar_por_mes(registros, mes, año)
        por_dia = contar_por_dia(filtrados)
        grafico_barras_apiladas_por_dia(por_dia, mes, año)

    def guardar_grafico(self):
        """Guarda el último gráfico generado como PNG."""
        if hasattr(self, 'ultimo_contador'):
            # Volver a generar el gráfico y guardarlo
            tipos = list(self.ultimo_contador.keys())
            frecuencias = list(self.ultimo_contador.values())
            fig, ax = plt.subplots(figsize=(10,6))
            ax.bar(tipos, frecuencias, color='skyblue', edgecolor='black')
            ax.set_title(f"Interlocks {self.ultimo_mes}/{self.ultimo_año}")
            filename = f"reporte_{self.ultimo_año}_{self.ultimo_mes}.png"
            fig.savefig(filename, dpi=150, bbox_inches='tight')
            plt.close(fig)
            messagebox.showinfo("Éxito", f"Gráfico guardado como {filename}")
        else:
            messagebox.showwarning("Aviso", "Primero genera un gráfico mensual")

    def cargar_tabla(self):
        """Carga los registros del mes seleccionado en la tabla."""
        try:
            mes = int(self.mes_tabla_var.get())
            año = int(self.año_tabla_var.get())
        except ValueError:
            messagebox.showerror("Error", "Mes o año inválido")
            return
        registros = cargar_registros()
        filtrados = filtrar_por_mes(registros, mes, año)
        # Limpiar tabla
        for row in self.tree.get_children():
            self.tree.delete(row)
        # Insertar filas
        for r in filtrados:
            self.tree.insert('', tk.END, values=(
                r.get('Fecha', ''),
                r.get('Hora', ''),
                r.get('Tipo', ''),
                r.get('Descripción', ''),
                r.get('Técnico', '')
            ))

if __name__ == "__main__":
    root = tk.Tk()
    app = Aplicacion(root)
    root.mainloop()