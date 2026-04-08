import tkinter as tk
from tkinter import ttk, messagebox
import string

# ==================== CONFIGURACIÓN INICIAL ====================
# Listas de validación
FRUTAS_VALIDAS = {'manzana', 'banana', 'naranja', 'uva', 'kiwi',
                  'fresa', 'mango', 'piña', 'sandía', 'melón'}
MESES_VALIDOS = {'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
                 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'}
LETRAS_VALIDAS = set(string.ascii_lowercase)

# Estructura de datos: 4 conjuntos editables + Answer
conjuntos = {
    "Números": set(),
    "Letras": set(),
    "Frutas": set(),
    "Meses": set()
}
answer = set()

# ==================== FUNCIONES DE VALIDACIÓN ====================
def validar_elemento(tipo, valor):
    """Retorna (es_valido, valor_procesado, mensaje_error)."""
    valor = valor.strip()
    if not valor:
        return False, None, "El valor no puede estar vacío."

    if tipo == "Números":
        try:
            num = int(valor)
            return True, num, ""
        except ValueError:
            return False, None, "Debe ser un número entero (ej: 5, -3)."

    elif tipo == "Letras":
        if len(valor) == 1 and valor.isalpha():
            return True, valor.lower(), ""
        else:
            return False, None, "Debe ser exactamente una letra (a-z, A-Z)."

    elif tipo == "Frutas":
        valor_lower = valor.lower()
        # Buscar coincidencia exacta ignorando mayúsculas
        for fruta in FRUTAS_VALIDAS:
            if fruta.lower() == valor_lower:
                return True, fruta, ""  # Devolvemos la forma canónica
        return False, None, f"Fruta no válida. Opciones: {', '.join(sorted(FRUTAS_VALIDAS))}"

    elif tipo == "Meses":
        valor_lower = valor.lower()
        for mes in MESES_VALIDOS:
            if mes.lower() == valor_lower:
                return True, mes, ""
        return False, None, f"Mes no válido. Opciones: {', '.join(sorted(MESES_VALIDOS))}"
    else:
        return False, None, "Tipo desconocido."

# ==================== FUNCIONES DE INTERFAZ ====================
def actualizar_vista_conjuntos():
    """Refresca la visualización de los 4 conjuntos (chips) y el combo de operandos."""
    # Limpiar frame de chips
    for widget in frame_chips.winfo_children():
        widget.destroy()

    for nombre, conjunto in conjuntos.items():
        # Título del conjunto
        lbl = tk.Label(frame_chips, text=f"{nombre}:", font=FUENTE_NEGRITA,
                       bg=COLOR_FONDO, fg=COLOR_PRIMARIO)
        lbl.pack(anchor="w", pady=(10, 2))

        chip_container = tk.Frame(frame_chips, bg=COLOR_FONDO)
        chip_container.pack(fill="x", padx=10)

        if not conjunto:
            lbl_vacio = tk.Label(chip_container, text="(vacío)", font=FUENTE_CHIP,
                                 bg=COLOR_FONDO, fg=COLOR_TEXTO_CLARO)
            lbl_vacio.pack(side="left")
        else:
            for elem in sorted(conjunto, key=lambda x: str(x)):
                chip = tk.Label(chip_container, text=str(elem),
                                bg=COLOR_CHIP, fg=COLOR_TEXTO_CHIP,
                                font=FUENTE_CHIP, padx=8, pady=2,
                                relief="flat", borderwidth=0)
                chip.pack(side="left", padx=2, pady=2)

    # Actualizar las opciones de los combobox de operandos (por si cambiaron nombres)
    nombres = list(conjuntos.keys()) + ["Answer"]
    combo_a['values'] = nombres
    combo_b['values'] = nombres
    if combo_a.get() not in nombres:
        combo_a.current(0)
    if combo_b.get() not in nombres:
        combo_b.current(1)

def actualizar_lista_edicion():
    """Muestra los elementos del conjunto seleccionado en el editor."""
    tipo = combo_tipo_editar.get()
    if not tipo:
        return
    conjunto_actual = conjuntos[tipo]
    # Limpiar lista
    listbox_elementos.delete(0, tk.END)
    for elem in sorted(conjunto_actual, key=lambda x: str(x)):
        listbox_elementos.insert(tk.END, str(elem))

def agregar_elemento():
    """Agrega un elemento al conjunto actualmente seleccionado en el editor."""
    tipo = combo_tipo_editar.get()
    if not tipo:
        messagebox.showwarning("Atención", "Selecciona un tipo de conjunto para editar.")
        return

    valor = entry_elemento.get()
    es_valido, valor_proc, error = validar_elemento(tipo, valor)
    if not es_valido:
        lbl_estado.config(text=f"Error: {error}")
        return

    conjunto = conjuntos[tipo]
    if valor_proc in conjunto:
        lbl_estado.config(text=f"El elemento '{valor_proc}' ya existe en {tipo}.")
    else:
        conjunto.add(valor_proc)
        entry_elemento.delete(0, tk.END)
        actualizar_lista_edicion()
        actualizar_vista_conjuntos()
        lbl_estado.config(text=f"Elemento '{valor_proc}' agregado a {tipo}.")

def eliminar_elemento():
    """Elimina el elemento seleccionado en la lista del editor."""
    tipo = combo_tipo_editar.get()
    if not tipo:
        return
    seleccion = listbox_elementos.curselection()
    if not seleccion:
        messagebox.showinfo("Información", "Selecciona un elemento de la lista para eliminar.")
        return

    elemento_str = listbox_elementos.get(seleccion[0])
    # Convertir al tipo adecuado para eliminar del conjunto
    if tipo == "Números":
        elemento = int(elemento_str)
    else:
        elemento = elemento_str

    conjuntos[tipo].discard(elemento)
    actualizar_lista_edicion()
    actualizar_vista_conjuntos()
    lbl_estado.config(text=f"Elemento '{elemento_str}' eliminado de {tipo}.")

def limpiar_conjunto_actual():
    """Vacía completamente el conjunto seleccionado en el editor."""
    tipo = combo_tipo_editar.get()
    if not tipo:
        return
    if messagebox.askyesno("Confirmar", f"¿Eliminar todos los elementos de {tipo}?"):
        conjuntos[tipo].clear()
        actualizar_lista_edicion()
        actualizar_vista_conjuntos()
        lbl_estado.config(text=f"Conjunto {tipo} vaciado.")

# ==================== OPERACIONES ====================
def obtener_conjunto(nombre):
    if nombre == "Answer":
        return answer
    return conjuntos[nombre]

def formatear_conjunto(conjunto):
    if not conjunto:
        return "∅"
    return ", ".join(str(e) for e in sorted(conjunto, key=lambda x: str(x)))

def actualizar_resultado():
    texto = formatear_conjunto(answer)
    if not answer:
        lbl_resultado_valor.config(text="∅ (conjunto vacío)")
    else:
        lbl_resultado_valor.config(text=texto)

    # Chips de Answer
    for widget in frame_resultado_chips.winfo_children():
        widget.destroy()
    for elem in sorted(answer, key=lambda x: str(x)):
        chip = tk.Label(frame_resultado_chips, text=str(elem),
                        bg=COLOR_CHIP_ANSWER, fg=COLOR_TEXTO_CHIP_ANSWER,
                        font=FUENTE_CHIP, padx=8, pady=2,
                        relief="flat", borderwidth=0)
        chip.pack(side="left", padx=2, pady=2)

def calcular():
    global answer
    nom_a = combo_a.get()
    nom_b = combo_b.get()
    operacion = combo_op.get()

    if not nom_a or not nom_b or not operacion:
        lbl_estado.config(text="Selecciona ambos conjuntos y una operación.")
        return

    set_a = obtener_conjunto(nom_a)
    set_b = obtener_conjunto(nom_b)

    try:
        if operacion == "Unión":
            resultado = set_a | set_b
        elif operacion == "Intersección":
            resultado = set_a & set_b
        elif operacion == "Diferencia (A - B)":
            resultado = set_a - set_b
        elif operacion == "Diferencia Simétrica":
            resultado = set_a ^ set_b
        else:
            resultado = set()
    except Exception as e:
        resultado = set()
        lbl_estado.config(text=f"Error inesperado: {e}")

    answer = resultado
    actualizar_resultado()
    lbl_estado.config(text="Operación realizada con éxito.")

def limpiar_answer():
    global answer
    answer = set()
    actualizar_resultado()
    lbl_estado.config(text="Answer limpiado.")

def copiar_answer():
    ventana.clipboard_clear()
    ventana.clipboard_append(formatear_conjunto(answer))
    lbl_estado.config(text="Resultado copiado al portapapeles.")

# ==================== INTERFAZ GRÁFICA ====================
ventana = tk.Tk()
ventana.title("Calculadora de Conjuntos - Editable")
ventana.geometry("900x700")
ventana.minsize(800, 650)
ventana.configure(bg="#f5f7fa")

# Colores y fuentes
COLOR_FONDO = "#f5f7fa"
COLOR_PRIMARIO = "#2c3e50"
COLOR_SECUNDARIO = "#3498db"
COLOR_BOTON = "#ecf0f1"
COLOR_CHIP = "#dfe6e9"
COLOR_TEXTO_CHIP = "#2d3436"
COLOR_CHIP_ANSWER = "#74b9ff"
COLOR_TEXTO_CHIP_ANSWER = "#2d3436"
COLOR_TEXTO_OSCURO = "#2c3e50"
COLOR_TEXTO_CLARO = "#636e72"

FUENTE_DEFECTO = ("Segoe UI", 10)
FUENTE_NEGRITA = ("Segoe UI", 10, "bold")
FUENTE_TITULO = ("Segoe UI", 12, "bold")
FUENTE_CHIP = ("Segoe UI", 9)

# Estilos ttk
style = ttk.Style()
style.theme_use("clam")
style.configure("TFrame", background=COLOR_FONDO)
style.configure("TLabel", background=COLOR_FONDO, font=FUENTE_DEFECTO, foreground=COLOR_TEXTO_OSCURO)
style.configure("TButton", font=FUENTE_DEFECTO, background=COLOR_BOTON, foreground=COLOR_TEXTO_OSCURO)
style.map("TButton", background=[("active", COLOR_SECUNDARIO), ("pressed", COLOR_PRIMARIO)],
          foreground=[("active", "white"), ("pressed", "white")])
style.configure("TCombobox", fieldbackground="white", font=FUENTE_DEFECTO)
style.configure("TLabelframe", background=COLOR_FONDO, font=FUENTE_NEGRITA, foreground=COLOR_PRIMARIO)
style.configure("TLabelframe.Label", background=COLOR_FONDO, foreground=COLOR_PRIMARIO)
style.configure("Accent.TButton", font=FUENTE_NEGRITA, background=COLOR_SECUNDARIO, foreground="white")
style.map("Accent.TButton", background=[("active", "#2980b9")])

# Contenedor principal
main_container = ttk.Frame(ventana, padding="20")
main_container.pack(fill=tk.BOTH, expand=True)

# ========== PANEL SUPERIOR: OPERANDOS ==========
frame_operandos = ttk.LabelFrame(main_container, text="Operandos y operación", padding="15")
frame_operandos.pack(fill=tk.X, pady=(0, 15))

ttk.Label(frame_operandos, text="Conjunto A:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
combo_a = ttk.Combobox(frame_operandos, state="readonly", width=18)
combo_a.grid(row=0, column=1, padx=5, pady=5)

ttk.Label(frame_operandos, text="Conjunto B:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
combo_b = ttk.Combobox(frame_operandos, state="readonly", width=18)
combo_b.grid(row=1, column=1, padx=5, pady=5)

ttk.Label(frame_operandos, text="Operación:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
combo_op = ttk.Combobox(frame_operandos,
                        values=["Unión", "Intersección", "Diferencia (A - B)", "Diferencia Simétrica"],
                        state="readonly", width=22)
combo_op.grid(row=2, column=1, padx=5, pady=5)
combo_op.current(0)

frame_botones_op = ttk.Frame(frame_operandos)
frame_botones_op.grid(row=3, column=0, columnspan=2, pady=15)
btn_calcular = ttk.Button(frame_botones_op, text="Calcular", command=calcular, style="Accent.TButton")
btn_calcular.pack(side=tk.LEFT, padx=5)

# ========== PANEL MEDIO: VISUALIZACIÓN Y EDITOR ==========
# Panel izquierdo: visualización de todos los conjuntos
frame_vista = ttk.LabelFrame(main_container, text="Conjuntos actuales", padding="10")
frame_vista.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

canvas = tk.Canvas(frame_vista, bg=COLOR_FONDO, highlightthickness=0)
scrollbar = ttk.Scrollbar(frame_vista, orient="vertical", command=canvas.yview)
scrollable_frame = ttk.Frame(canvas, style="TFrame")

scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

frame_chips = ttk.Frame(scrollable_frame, style="TFrame")
frame_chips.pack(fill="both", expand=True)

# Panel derecho: editor de conjuntos
frame_editor = ttk.LabelFrame(main_container, text="Editor de conjuntos", padding="15")
frame_editor.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

ttk.Label(frame_editor, text="Tipo de conjunto a editar:").pack(anchor="w", pady=(0, 5))
combo_tipo_editar = ttk.Combobox(frame_editor, values=list(conjuntos.keys()),
                                 state="readonly", width=20)
combo_tipo_editar.pack(fill=tk.X, pady=(0, 15))
combo_tipo_editar.bind("<<ComboboxSelected>>", lambda e: actualizar_lista_edicion())

ttk.Label(frame_editor, text="Agregar elemento:").pack(anchor="w")
entry_elemento = ttk.Entry(frame_editor, font=FUENTE_DEFECTO)
entry_elemento.pack(fill=tk.X, pady=(5, 5))
entry_elemento.bind("<Return>", lambda e: agregar_elemento())

frame_botones_edit = ttk.Frame(frame_editor)
frame_botones_edit.pack(fill=tk.X, pady=(0, 10))
btn_agregar = ttk.Button(frame_botones_edit, text="Agregar", command=agregar_elemento)
btn_agregar.pack(side=tk.LEFT, padx=2)
btn_eliminar = ttk.Button(frame_botones_edit, text="Eliminar seleccionado", command=eliminar_elemento)
btn_eliminar.pack(side=tk.LEFT, padx=2)
btn_limpiar = ttk.Button(frame_botones_edit, text="Vaciar conjunto", command=limpiar_conjunto_actual)
btn_limpiar.pack(side=tk.LEFT, padx=2)

ttk.Label(frame_editor, text="Elementos actuales:").pack(anchor="w", pady=(10, 5))
listbox_elementos = tk.Listbox(frame_editor, height=8, font=FUENTE_DEFECTO,
                               selectbackground=COLOR_SECUNDARIO, relief="flat")
listbox_elementos.pack(fill=tk.BOTH, expand=True)

# ========== PANEL INFERIOR: ANSWER ==========
frame_resultado = ttk.LabelFrame(main_container, text="Resultado (Answer)", padding="15")
frame_resultado.pack(side=tk.BOTTOM, fill=tk.X, pady=(15, 0))

frame_res_contenido = ttk.Frame(frame_resultado)
frame_res_contenido.pack(fill=tk.X, pady=5)

ttk.Label(frame_res_contenido, text="Answer = ", font=FUENTE_NEGRITA).pack(side=tk.LEFT)
lbl_resultado_valor = ttk.Label(frame_res_contenido, text="∅ (conjunto vacío)",
                                font=FUENTE_DEFECTO, foreground=COLOR_TEXTO_CLARO)
lbl_resultado_valor.pack(side=tk.LEFT, padx=(5, 20))

frame_resultado_chips = tk.Frame(frame_res_contenido, bg=COLOR_FONDO)
frame_resultado_chips.pack(side=tk.LEFT, fill=tk.X, expand=True)

frame_botones_answer = ttk.Frame(frame_resultado)
frame_botones_answer.pack(fill=tk.X, pady=(5, 0))
btn_limpiar_answer = ttk.Button(frame_botones_answer, text="Limpiar Answer", command=limpiar_answer)
btn_limpiar_answer.pack(side=tk.LEFT, padx=5)
btn_copiar_answer = ttk.Button(frame_botones_answer, text="Copiar al portapapeles", command=copiar_answer)
btn_copiar_answer.pack(side=tk.LEFT, padx=5)

# Barra de estado
lbl_estado = ttk.Label(main_container, text="Listo. Puedes editar los conjuntos y luego operar.",
                       font=("Segoe UI", 9), foreground=COLOR_TEXTO_CLARO)
lbl_estado.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))

# Inicialización
combo_tipo_editar.current(0)
actualizar_lista_edicion()
actualizar_vista_conjuntos()
actualizar_resultado()
combo_a.current(0)
combo_b.current(1)

# Scroll con rueda
def _on_mousewheel(event):
    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
canvas.bind_all("<MouseWheel>", _on_mousewheel)

ventana.mainloop()