# panaderia_mejorada.py
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
import math

# --------------------------------------------
# CLASE PARA MANEJAR LA BASE DE DATOS
# --------------------------------------------
class BaseDatos:
    def __init__(self):
        self.conexion = sqlite3.connect('panaderia.db')
        self.cursor = self.conexion.cursor()
        self.crear_tablas()
    
    def crear_tablas(self):
        # Tabla de categorías
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL
            )
        ''')
        
        # Insertar categorías por defecto si no existen
        categorias_default = ['Pan', 'Pasteles', 'Galletas', 'Bebidas']
        for cat in categorias_default:
            self.cursor.execute("INSERT OR IGNORE INTO categorias (nombre) VALUES (?)", (cat,))
        
        # Tabla de productos (ahora con categoría)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                categoria_id INTEGER,
                precio_compra REAL NOT NULL,
                precio_venta REAL NOT NULL,
                cantidad INTEGER NOT NULL,
                FOREIGN KEY (categoria_id) REFERENCES categorias (id)
            )
        ''')
        
        # Tabla de ventas
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                producto_id INTEGER NOT NULL,
                cantidad INTEGER NOT NULL,
                ganancia REAL NOT NULL,
                fecha TEXT NOT NULL,
                FOREIGN KEY (producto_id) REFERENCES productos (id)
            )
        ''')
        
        # Tabla para guardar la tasa del dólar
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS configuracion (
                clave TEXT PRIMARY KEY,
                valor TEXT NOT NULL
            )
        ''')
        
        # Insertar tasa por defecto si no existe
        self.cursor.execute("INSERT OR IGNORE INTO configuracion (clave, valor) VALUES (?, ?)", 
                           ('tasa_dolar', '40.0'))
        
        self.conexion.commit()
    
    def obtener_categorias(self):
        self.cursor.execute("SELECT id, nombre FROM categorias ORDER BY nombre")
        return self.cursor.fetchall()
    
    def obtener_tasa_dolar(self):
        self.cursor.execute("SELECT valor FROM configuracion WHERE clave = 'tasa_dolar'")
        resultado = self.cursor.fetchone()
        return float(resultado[0]) if resultado else 40.0
    
    def actualizar_tasa_dolar(self, nueva_tasa):
        self.cursor.execute("UPDATE configuracion SET valor = ? WHERE clave = 'tasa_dolar'", 
                           (str(nueva_tasa),))
        self.conexion.commit()
    
    def agregar_producto(self, nombre, categoria_id, compra, venta, cantidad):
        try:
            self.cursor.execute(
                "INSERT INTO productos (nombre, categoria_id, precio_compra, precio_venta, cantidad) VALUES (?, ?, ?, ?, ?)",
                (nombre, categoria_id, compra, venta, cantidad)
            )
            self.conexion.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def editar_producto(self, producto_id, nombre, categoria_id, compra, venta, cantidad):
        self.cursor.execute(
            "UPDATE productos SET nombre = ?, categoria_id = ?, precio_compra = ?, precio_venta = ?, cantidad = ? WHERE id = ?",
            (nombre, categoria_id, compra, venta, cantidad, producto_id)
        )
        self.conexion.commit()
        return True
    
    def eliminar_producto(self, producto_id):
        # Verificar si el producto tiene ventas asociadas
        self.cursor.execute("SELECT COUNT(*) FROM ventas WHERE producto_id = ?", (producto_id,))
        ventas = self.cursor.fetchone()[0]
        
        if ventas > 0:
            return False, "No se puede eliminar: el producto tiene ventas registradas"
        
        self.cursor.execute("DELETE FROM productos WHERE id = ?", (producto_id,))
        self.conexion.commit()
        return True, "Producto eliminado"
    
    def vender_producto(self, producto_id, cantidad_vender):
        self.cursor.execute("SELECT cantidad, precio_compra, precio_venta, nombre FROM productos WHERE id = ?", (producto_id,))
        producto = self.cursor.fetchone()
        
        if not producto:
            return "Producto no encontrado"
        
        stock_actual, precio_compra, precio_venta, nombre = producto
        
        if cantidad_vender > stock_actual:
            return f"Solo hay {stock_actual} unidades disponibles"
        
        ganancia_por_unidad = precio_venta - precio_compra
        ganancia_total = ganancia_por_unidad * cantidad_vender
        
        nuevo_stock = stock_actual - cantidad_vender
        self.cursor.execute("UPDATE productos SET cantidad = ? WHERE id = ?", (nuevo_stock, producto_id))
        
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute(
            "INSERT INTO ventas (producto_id, cantidad, ganancia, fecha) VALUES (?, ?, ?, ?)",
            (producto_id, cantidad_vender, ganancia_total, fecha_actual)
        )
        
        self.conexion.commit()
        return f"Venta exitosa! Ganancia: ${ganancia_total:.2f}"
    
    def buscar_productos(self, texto):
        self.cursor.execute('''
            SELECT p.id, p.nombre, c.nombre, p.precio_compra, p.precio_venta, p.cantidad 
            FROM productos p
            LEFT JOIN categorias c ON p.categoria_id = c.id
            WHERE p.nombre LIKE ? OR c.nombre LIKE ?
            ORDER BY p.nombre
        ''', (f'%{texto}%', f'%{texto}%'))
        return self.cursor.fetchall()
    
    def obtener_producto_por_id(self, producto_id):
        self.cursor.execute('''
            SELECT p.id, p.nombre, p.categoria_id, c.nombre, p.precio_compra, p.precio_venta, p.cantidad 
            FROM productos p
            LEFT JOIN categorias c ON p.categoria_id = c.id
            WHERE p.id = ?
        ''', (producto_id,))
        return self.cursor.fetchone()
    
    def total_vendido_y_ganancias(self, producto_id):
        self.cursor.execute(
            "SELECT SUM(cantidad), SUM(ganancia) FROM ventas WHERE producto_id = ?",
            (producto_id,)
        )
        resultado = self.cursor.fetchone()
        total_vendido = resultado[0] if resultado[0] else 0
        total_ganancia = resultado[1] if resultado[1] else 0
        return total_vendido, total_ganancia
    
    def obtener_todos_productos(self):
        self.cursor.execute('''
            SELECT p.id, p.nombre, c.nombre, p.precio_compra, p.precio_venta, p.cantidad 
            FROM productos p
            LEFT JOIN categorias c ON p.categoria_id = c.id
            ORDER BY p.nombre
        ''')
        return self.cursor.fetchall()
    
    def cerrar(self):
        self.conexion.close()

# --------------------------------------------
# CLASE DE LA CALCULADORA
# --------------------------------------------
class Calculadora:
    def __init__(self, parent, tasa_dolar):
        self.top = tk.Toplevel(parent)
        self.top.title("Calculadora")
        self.top.geometry("300x400")
        self.top.resizable(False, False)
        self.tasa_dolar = tasa_dolar
        
        self.crear_interfaz()
    
    def crear_interfaz(self):
        # Pantalla de la calculadora
        self.pantalla = tk.Entry(self.top, font=("Arial", 16), justify="right", bd=10)
        self.pantalla.grid(row=0, column=0, columnspan=4, sticky="nsew", padx=5, pady=5)
        self.pantalla.insert(0, "0")
        
        # Botones de números y operaciones
        botones = [
            '7', '8', '9', '/',
            '4', '5', '6', '*',
            '1', '2', '3', '-',
            '0', '.', '=', '+'
        ]
        
        # Frame para los botones
        frame_botones = tk.Frame(self.top)
        frame_botones.grid(row=1, column=0, columnspan=4, sticky="nsew")
        
        row = 0
        col = 0
        for i, boton in enumerate(botones):
            cmd = lambda x=boton: self.click(x)
            tk.Button(frame_botones, text=boton, command=cmd, width=5, height=2, font=("Arial", 12)).grid(row=row, column=col, padx=2, pady=2)
            col += 1
            if col > 3:
                col = 0
                row += 1
        
        # Botones especiales
        tk.Button(frame_botones, text="C", command=self.limpiar, bg="red", fg="white", width=5, height=2).grid(row=4, column=0, padx=2, pady=2)
        tk.Button(frame_botones, text="←", command=self.borrar, width=5, height=2).grid(row=4, column=1, padx=2, pady=2)
        
        # Frame para conversión
        frame_conversion = tk.Frame(self.top)
        frame_conversion.grid(row=2, column=0, columnspan=4, pady=10)
        
        tk.Label(frame_conversion, text="USD → Bs:", font=("Arial", 10)).grid(row=0, column=0, padx=5)
        self.entry_usd = tk.Entry(frame_conversion, width=10)
        self.entry_usd.grid(row=0, column=1, padx=5)
        tk.Button(frame_conversion, text="Convertir", command=self.convertir_usd_bs, bg="blue", fg="white").grid(row=0, column=2, padx=5)
        
        tk.Label(frame_conversion, text="Bs → USD:", font=("Arial", 10)).grid(row=1, column=0, padx=5)
        self.entry_bs = tk.Entry(frame_conversion, width=10)
        self.entry_bs.grid(row=1, column=1, padx=5)
        tk.Button(frame_conversion, text="Convertir", command=self.convertir_bs_usd, bg="green", fg="white").grid(row=1, column=2, padx=5)
        
        self.resultado_conversion = tk.Label(self.top, text="", font=("Arial", 10))
        self.resultado_conversion.grid(row=3, column=0, columnspan=4)
    
    def click(self, boton):
        actual = self.pantalla.get()
        
        if boton == '=':
            try:
                resultado = eval(actual)
                self.pantalla.delete(0, tk.END)
                self.pantalla.insert(0, str(resultado))
            except:
                self.pantalla.delete(0, tk.END)
                self.pantalla.insert(0, "Error")
        else:
            if actual == "0" or actual == "Error":
                self.pantalla.delete(0, tk.END)
                self.pantalla.insert(0, boton)
            else:
                self.pantalla.insert(tk.END, boton)
    
    def limpiar(self):
        self.pantalla.delete(0, tk.END)
        self.pantalla.insert(0, "0")
    
    def borrar(self):
        actual = self.pantalla.get()
        if len(actual) > 1:
            self.pantalla.delete(len(actual)-1, tk.END)
        else:
            self.pantalla.delete(0, tk.END)
            self.pantalla.insert(0, "0")
    
    def convertir_usd_bs(self):
        try:
            usd = float(self.entry_usd.get())
            bs = usd * self.tasa_dolar
            self.resultado_conversion.config(text=f"${usd:.2f} = Bs. {bs:.2f}")
        except:
            self.resultado_conversion.config(text="Error: Ingresa un número válido")
    
    def convertir_bs_usd(self):
        try:
            bs = float(self.entry_bs.get())
            usd = bs / self.tasa_dolar
            self.resultado_conversion.config(text=f"Bs. {bs:.2f} = ${usd:.2f}")
        except:
            self.resultado_conversion.config(text="Error: Ingresa un número válido")

# --------------------------------------------
# CLASE PRINCIPAL DE LA INTERFAZ
# --------------------------------------------
class PanaderiaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Panadería - Bs/$")
        self.root.geometry("900x700")
        
        # Conectar a base de datos
        self.db = BaseDatos()
        self.tasa_dolar = self.db.obtener_tasa_dolar()
        
        # Variables para búsqueda en tiempo real
        self.busqueda_var = tk.StringVar()
        self.busqueda_var.trace('w', self.buscar_en_tiempo_real)
        
        # Crear menú principal
        self.crear_menu()
        
        # Mostrar pantalla de inicio
        self.mostrar_inicio()
    
    def crear_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Menú Archivo
        archivo_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=archivo_menu)
        archivo_menu.add_command(label="Inicio", command=self.mostrar_inicio)
        archivo_menu.add_separator()
        archivo_menu.add_command(label="Configurar Tasa Dólar", command=self.configurar_tasa)
        archivo_menu.add_separator()
        archivo_menu.add_command(label="Salir", command=self.root.quit)
        
        # Menú Productos
        productos_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Productos", menu=productos_menu)
        productos_menu.add_command(label="Agregar Producto", command=self.mostrar_agregar)
        productos_menu.add_command(label="Ver Inventario", command=self.mostrar_inventario)
        productos_menu.add_command(label="Editar/Eliminar", command=self.mostrar_editar_eliminar)
        
        # Menú Ventas
        ventas_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ventas", menu=ventas_menu)
        ventas_menu.add_command(label="Registrar Venta", command=self.mostrar_venta)
        ventas_menu.add_command(label="Buscar Producto", command=self.mostrar_buscar)
        
        # Menú Herramientas
        herramientas_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Herramientas", menu=herramientas_menu)
        herramientas_menu.add_command(label="Calculadora", command=self.abrir_calculadora)
    
    def abrir_calculadora(self):
        Calculadora(self.root, self.tasa_dolar)
    
    def configurar_tasa(self):
        dialogo = tk.Toplevel(self.root)
        dialogo.title("Configurar Tasa del Dólar")
        dialogo.geometry("300x150")
        dialogo.resizable(False, False)
        
        tk.Label(dialogo, text=f"Tasa actual: Bs. {self.tasa_dolar:.2f}", font=("Arial", 12)).pack(pady=10)
        tk.Label(dialogo, text="Nueva tasa (Bs/$):").pack()
        
        entry_tasa = tk.Entry(dialogo)
        entry_tasa.pack(pady=5)
        entry_tasa.insert(0, str(self.tasa_dolar))
        
        def guardar_tasa():
            try:
                nueva_tasa = float(entry_tasa.get())
                if nueva_tasa <= 0:
                    messagebox.showerror("Error", "La tasa debe ser positiva")
                    return
                
                self.db.actualizar_tasa_dolar(nueva_tasa)
                self.tasa_dolar = nueva_tasa
                messagebox.showinfo("Éxito", f"Tasa actualizada a Bs. {nueva_tasa:.2f}")
                dialogo.destroy()
            except ValueError:
                messagebox.showerror("Error", "Ingresa un número válido")
        
        tk.Button(dialogo, text="Guardar", command=guardar_tasa, bg="green", fg="white").pack(pady=10)
    
    def limpiar_pantalla(self):
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Frame) and widget != self.root:
                widget.destroy()
    
    def mostrar_inicio(self):
        self.limpiar_pantalla()
        frame = tk.Frame(self.root, padx=20, pady=20)
        frame.pack(expand=True)
        
        tk.Label(frame, text="🥖 PANADERÍA 🥐", font=("Arial", 24, "bold")).pack(pady=20)
        tk.Label(frame, text="Sistema de Control de Inventario y Ventas", font=("Arial", 14)).pack()
        tk.Label(frame, text=f"Tasa del Dólar: Bs. {self.tasa_dolar:.2f}", font=("Arial", 12, "bold"), fg="blue").pack(pady=10)
        tk.Label(frame, text="\nSeleccione una opción del menú para comenzar", font=("Arial", 12)).pack(pady=30)
    
    def mostrar_agregar(self):
        self.limpiar_pantalla()
        frame = tk.Frame(self.root, padx=20, pady=20)
        frame.pack(fill="both", expand=True)
        
        tk.Label(frame, text="➕ AGREGAR NUEVO PRODUCTO", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Obtener categorías
        categorias = self.db.obtener_categorias()
        
        # Formulario
        form_frame = tk.Frame(frame)
        form_frame.pack(pady=20)
        
        tk.Label(form_frame, text="Nombre del producto:").grid(row=0, column=0, sticky="w", pady=5)
        entry_nombre = tk.Entry(form_frame, width=30)
        entry_nombre.grid(row=0, column=1, pady=5)
        
        tk.Label(form_frame, text="Categoría:").grid(row=1, column=0, sticky="w", pady=5)
        categoria_var = tk.StringVar()
        combo_categoria = ttk.Combobox(form_frame, textvariable=categoria_var, values=[c[1] for c in categorias], width=27)
        combo_categoria.grid(row=1, column=1, pady=5)
        if categorias:
            combo_categoria.current(0)
        
        tk.Label(form_frame, text="Precio de compra (Bs):").grid(row=2, column=0, sticky="w", pady=5)
        entry_compra = tk.Entry(form_frame, width=30)
        entry_compra.grid(row=2, column=1, pady=5)
        
        tk.Label(form_frame, text="Precio de venta (Bs):").grid(row=3, column=0, sticky="w", pady=5)
        entry_venta = tk.Entry(form_frame, width=30)
        entry_venta.grid(row=3, column=1, pady=5)
        
        # Mostrar precios en dólares
        lbl_precio_usd = tk.Label(form_frame, text="", fg="blue")
        lbl_precio_usd.grid(row=4, column=1, sticky="w")
        
        def actualizar_precios_usd(*args):
            try:
                compra_bs = float(entry_compra.get()) if entry_compra.get() else 0
                venta_bs = float(entry_venta.get()) if entry_venta.get() else 0
                compra_usd = compra_bs / self.tasa_dolar
                venta_usd = venta_bs / self.tasa_dolar
                lbl_precio_usd.config(text=f"(${compra_usd:.2f} / ${venta_usd:.2f} USD)")
            except:
                lbl_precio_usd.config(text="")
        
        entry_compra.bind('<KeyRelease>', actualizar_precios_usd)
        entry_venta.bind('<KeyRelease>', actualizar_precios_usd)
        
        tk.Label(form_frame, text="Cantidad inicial:").grid(row=5, column=0, sticky="w", pady=5)
        entry_cantidad = tk.Entry(form_frame, width=30)
        entry_cantidad.grid(row=5, column=1, pady=5)
        
        def guardar():
            try:
                nombre = entry_nombre.get()
                if not nombre:
                    messagebox.showerror("Error", "El nombre es obligatorio")
                    return
                
                # Obtener ID de categoría
                categoria_nombre = categoria_var.get()
                categoria_id = None
                for cat in categorias:
                    if cat[1] == categoria_nombre:
                        categoria_id = cat[0]
                        break
                
                compra = float(entry_compra.get())
                venta = float(entry_venta.get())
                cantidad = int(entry_cantidad.get())
                
                if compra <= 0 or venta <= 0 or cantidad < 0:
                    messagebox.showerror("Error", "Los valores deben ser positivos")
                    return
                
                if venta <= compra:
                    if not messagebox.askyesno("Advertencia", "El precio de venta es menor o igual al de compra. ¿Continuar?"):
                        return
                
                if self.db.agregar_producto(nombre, categoria_id, compra, venta, cantidad):
                    messagebox.showinfo("Éxito", f"Producto '{nombre}' agregado correctamente")
                    entry_nombre.delete(0, tk.END)
                    entry_compra.delete(0, tk.END)
                    entry_venta.delete(0, tk.END)
                    entry_cantidad.delete(0, tk.END)
                else:
                    messagebox.showerror("Error", "Ya existe un producto con ese nombre")
            except ValueError:
                messagebox.showerror("Error", "Verifica que los números sean válidos")
        
        tk.Button(frame, text="Guardar Producto", command=guardar, bg="green", fg="white", padx=20, pady=5).pack(pady=20)
    
    def mostrar_editar_eliminar(self):
        self.limpiar_pantalla()
        frame = tk.Frame(self.root, padx=20, pady=20)
        frame.pack(fill="both", expand=True)
        
        tk.Label(frame, text="✏️ EDITAR / ELIMINAR PRODUCTOS", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Buscador en tiempo real
        busqueda_frame = tk.Frame(frame)
        busqueda_frame.pack(fill="x", pady=10)
        
        tk.Label(busqueda_frame, text="Buscar:").pack(side="left", padx=5)
        entry_buscar = tk.Entry(busqueda_frame, textvariable=self.busqueda_var, width=40)
        entry_buscar.pack(side="left", padx=5)
        tk.Label(busqueda_frame, text="(escribe para buscar en tiempo real)", font=("Arial", 9), fg="gray").pack(side="left")
        
        # Frame para la lista de productos
        lista_frame = tk.Frame(frame)
        lista_frame.pack(fill="both", expand=True, pady=10)
        
        # Treeview para mostrar productos
        columnas = ("ID", "Producto", "Categoría", "Compra", "Venta", "Stock")
        self.tree_editar = ttk.Treeview(lista_frame, columns=columnas, show="headings", height=12)
        
        self.tree_editar.heading("ID", text="ID")
        self.tree_editar.heading("Producto", text="Producto")
        self.tree_editar.heading("Categoría", text="Categoría")
        self.tree_editar.heading("Compra", text="Compra (Bs)")
        self.tree_editar.heading("Venta", text="Venta (Bs)")
        self.tree_editar.heading("Stock", text="Stock")
        
        self.tree_editar.column("ID", width=50)
        self.tree_editar.column("Producto", width=150)
        self.tree_editar.column("Categoría", width=100)
        self.tree_editar.column("Compra", width=80)
        self.tree_editar.column("Venta", width=80)
        self.tree_editar.column("Stock", width=60)
        
        scrollbar = ttk.Scrollbar(lista_frame, orient="vertical", command=self.tree_editar.yview)
        self.tree_editar.configure(yscrollcommand=scrollbar.set)
        
        self.tree_editar.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.tree_editar.bind('<Double-Button-1>', self.abrir_editor)
        
        # Frame para botones
        botones_frame = tk.Frame(frame)
        botones_frame.pack(pady=10)
        
        tk.Button(botones_frame, text="Editar seleccionado", command=self.abrir_editor_seleccionado, 
                 bg="blue", fg="white", padx=20, pady=5).pack(side="left", padx=5)
        tk.Button(botones_frame, text="Eliminar seleccionado", command=self.eliminar_seleccionado, 
                 bg="red", fg="white", padx=20, pady=5).pack(side="left", padx=5)
        tk.Button(botones_frame, text="Actualizar lista", command=self.actualizar_lista_editar, 
                  bg="gray", fg="white", padx=20, pady=5).pack(side="left", padx=5)
        
        # Cargar productos iniciales
        self.actualizar_lista_editar()
    
    def actualizar_lista_editar(self, productos=None):
        # Limpiar treeview
        for item in self.tree_editar.get_children():
            self.tree_editar.delete(item)
        
        if productos is None:
            productos = self.db.obtener_todos_productos()
        
        for p in productos:
            valores = (p[0], p[1], p[2], f"{p[3]:.2f}", f"{p[4]:.2f}", p[5])
            self.tree_editar.insert("", "end", values=valores)
    
    def buscar_en_tiempo_real(self, *args):
        texto = self.busqueda_var.get()
        if texto:
            resultados = self.db.buscar_productos(texto)
            self.actualizar_lista_editar(resultados)
        else:
            self.actualizar_lista_editar()
    
    def abrir_editor_seleccionado(self):
        seleccion = self.tree_editar.selection()
        if not seleccion:
            messagebox.showwarning("Seleccionar", "Por favor, selecciona un producto")
            return
        
        item = self.tree_editar.item(seleccion[0])
        producto_id = item['values'][0]
        self.abrir_editor(None, producto_id)
    
    def abrir_editor(self, event, producto_id=None):
        if producto_id is None:
            seleccion = self.tree_editar.selection()
            if not seleccion:
                return
            item = self.tree_editar.item(seleccion[0])
            producto_id = item['values'][0]
        
        # Obtener datos del producto
        producto = self.db.obtener_producto_por_id(producto_id)
        if not producto:
            messagebox.showerror("Error", "Producto no encontrado")
            return
        
        # Crear ventana de edición
        editor = tk.Toplevel(self.root)
        editor.title(f"Editar: {producto[1]}")
        editor.geometry("400x350")
        editor.resizable(False, False)
        
        # Obtener categorías
        categorias = self.db.obtener_categorias()
        
        # Formulario
        frame = tk.Frame(editor, padx=20, pady=20)
        frame.pack(fill="both", expand=True)
        
        tk.Label(frame, text="Nombre:").grid(row=0, column=0, sticky="w", pady=5)
        entry_nombre = tk.Entry(frame, width=30)
        entry_nombre.grid(row=0, column=1, pady=5)
        entry_nombre.insert(0, producto[1])
        
        tk.Label(frame, text="Categoría:").grid(row=1, column=0, sticky="w", pady=5)
        categoria_var = tk.StringVar()
        combo_categoria = ttk.Combobox(frame, textvariable=categoria_var, values=[c[1] for c in categorias], width=27)
        combo_categoria.grid(row=1, column=1, pady=5)
        
        # Seleccionar categoría actual
        for i, cat in enumerate(categorias):
            if cat[0] == producto[2]:
                combo_categoria.current(i)
                break
        
        tk.Label(frame, text="Precio compra (Bs):").grid(row=2, column=0, sticky="w", pady=5)
        entry_compra = tk.Entry(frame, width=30)
        entry_compra.grid(row=2, column=1, pady=5)
        entry_compra.insert(0, str(producto[4]))
        
        tk.Label(frame, text="Precio venta (Bs):").grid(row=3, column=0, sticky="w", pady=5)
        entry_venta = tk.Entry(frame, width=30)
        entry_venta.grid(row=3, column=1, pady=5)
        entry_venta.insert(0, str(producto[5]))
        
        tk.Label(frame, text="Stock:").grid(row=4, column=0, sticky="w", pady=5)
        entry_stock = tk.Entry(frame, width=30)
        entry_stock.grid(row=4, column=1, pady=5)
        entry_stock.insert(0, str(producto[6]))
        
        # Mostrar precios en dólares
        lbl_precio_usd = tk.Label(frame, text="", fg="blue")
        lbl_precio_usd.grid(row=5, column=1, sticky="w")
        
        def actualizar_precios_usd(*args):
            try:
                compra_bs = float(entry_compra.get()) if entry_compra.get() else 0
                venta_bs = float(entry_venta.get()) if entry_venta.get() else 0
                compra_usd = compra_bs / self.tasa_dolar
                venta_usd = venta_bs / self.tasa_dolar
                lbl_precio_usd.config(text=f"(${compra_usd:.2f} / ${venta_usd:.2f} USD)")
            except:
                lbl_precio_usd.config(text="")
        
        entry_compra.bind('<KeyRelease>', actualizar_precios_usd)
        entry_venta.bind('<KeyRelease>', actualizar_precios_usd)
        actualizar_precios_usd()
        
        def guardar_cambios():
            try:
                nombre = entry_nombre.get()
                if not nombre:
                    messagebox.showerror("Error", "El nombre es obligatorio")
                    return
                
                categoria_nombre = categoria_var.get()
                categoria_id = None
                for cat in categorias:
                    if cat[1] == categoria_nombre:
                        categoria_id = cat[0]
                        break
                
                compra = float(entry_compra.get())
                venta = float(entry_venta.get())
                stock = int(entry_stock.get())
                
                if compra <= 0 or venta <= 0 or stock < 0:
                    messagebox.showerror("Error", "Los valores deben ser positivos")
                    return
                
                self.db.editar_producto(producto_id, nombre, categoria_id, compra, venta, stock)
                messagebox.showinfo("Éxito", "Producto actualizado correctamente")
                editor.destroy()
                self.actualizar_lista_editar()
                
            except ValueError:
                messagebox.showerror("Error", "Verifica que los números sean válidos")
        
        tk.Button(frame, text="Guardar Cambios", command=guardar_cambios, 
                 bg="green", fg="white", padx=20, pady=5).grid(row=6, column=0, columnspan=2, pady=20)
    
    def eliminar_seleccionado(self):
        seleccion = self.tree_editar.selection()
        if not seleccion:
            messagebox.showwarning("Seleccionar", "Por favor, selecciona un producto")
            return
        
        item = self.tree_editar.item(seleccion[0])
        producto_nombre = item['values'][1]
        producto_id = item['values'][0]
        
        if messagebox.askyesno("Confirmar eliminación", f"¿Estás seguro de eliminar '{producto_nombre}'?"):
            exito, mensaje = self.db.eliminar_producto(producto_id)
            if exito:
                messagebox.showinfo("Éxito", mensaje)
                self.actualizar_lista_editar()
            else:
                messagebox.showerror("Error", mensaje)
    
    def mostrar_venta(self):
        self.limpiar_pantalla()
        frame = tk.Frame(self.root, padx=20, pady=20)
        frame.pack(fill="both", expand=True)
        
        tk.Label(frame, text="💰 REGISTRAR VENTA", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Obtener productos
        productos = self.db.obtener_todos_productos()
        
        if not productos:
            tk.Label(frame, text="No hay productos registrados").pack(pady=20)
            return
        
        form_frame = tk.Frame(frame)
        form_frame.pack(pady=20)
        
        tk.Label(form_frame, text="Producto:").grid(row=0, column=0, sticky="w", pady=5)
        self.combo_venta = ttk.Combobox(form_frame, values=[f"{p[1]} (Stock: {p[5]}) - {p[2]}" for p in productos], width=50)
        self.combo_venta.grid(row=0, column=1, pady=5)
        if productos:
            self.combo_venta.current(0)
        
        # Guardar IDs de productos para referencia
        self.productos_ids = [p[0] for p in productos]
        
        tk.Label(form_frame, text="Cantidad a vender:").grid(row=1, column=0, sticky="w", pady=5)
        entry_cantidad = tk.Entry(form_frame, width=50)
        entry_cantidad.grid(row=1, column=1, pady=5)
        
        # Mostrar precios en USD
        lbl_precios_usd = tk.Label(form_frame, text="", fg="blue")
        lbl_precios_usd.grid(row=2, column=1, sticky="w")
        
        def actualizar_precios_venta(*args):
            try:
                idx = self.combo_venta.current()
                if idx >= 0:
                    producto = productos[idx]
                    venta_bs = producto[4]
                    venta_usd = venta_bs / self.tasa_dolar
                    lbl_precios_usd.config(text=f"Precio: Bs. {venta_bs:.2f} | ${venta_usd:.2f} USD")
            except:
                lbl_precios_usd.config(text="")
        
        self.combo_venta.bind('<<ComboboxSelected>>', actualizar_precios_venta)
        actualizar_precios_venta()
        
        def realizar_venta():
            try:
                idx = self.combo_venta.current()
                if idx < 0:
                    messagebox.showerror("Error", "Selecciona un producto")
                    return
                
                producto_id = self.productos_ids[idx]
                cantidad = int(entry_cantidad.get())
                
                resultado = self.db.vender_producto(producto_id, cantidad)
                if "exitosa" in resultado:
                    messagebox.showinfo("Venta realizada", resultado)
                    entry_cantidad.delete(0, tk.END)
                    # Actualizar lista de productos
                    productos_nuevos = self.db.obtener_todos_productos()
                    self.combo_venta['values'] = [f"{p[1]} (Stock: {p[5]}) - {p[2]}" for p in productos_nuevos]
                    self.productos_ids = [p[0] for p in productos_nuevos]
                    actualizar_precios_venta()
                else:
                    messagebox.showerror("Error", resultado)
            except ValueError:
                messagebox.showerror("Error", "La cantidad debe ser un número entero")
        
        tk.Button(frame, text="Vender", command=realizar_venta, bg="blue", fg="white", padx=20, pady=5).pack(pady=20)
    
    def mostrar_buscar(self):
        self.limpiar_pantalla()
        frame = tk.Frame(self.root, padx=20, pady=20)
        frame.pack(fill="both", expand=True)
        
        tk.Label(frame, text="🔍 BUSCAR PRODUCTO", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Buscador en tiempo real
        busqueda_frame = tk.Frame(frame)
        busqueda_frame.pack(pady=10)
        
        tk.Label(busqueda_frame, text="Nombre o categoría:").pack(side="left", padx=5)
        entry_buscar = tk.Entry(busqueda_frame, width=30)
        entry_buscar.pack(side="left", padx=5)
        
        resultado_text = scrolledtext.ScrolledText(frame, width=80, height=25, state="disabled")
        resultado_text.pack(pady=20, fill="both", expand=True)
        
        def buscar():
            texto = entry_buscar.get()
            if not texto:
                messagebox.showinfo("Info", "Escribe algo para buscar")
                return
            
            productos = self.db.buscar_productos(texto)
            
            resultado_text.config(state="normal")
            resultado_text.delete(1.0, tk.END)
            
            if not productos:
                resultado_text.insert(tk.END, "❌ No se encontraron productos\n")
            else:
                for p in productos:
                    producto_id, nombre, categoria, compra, venta, stock = p
                    
                    # Obtener ventas totales
                    vendido, ganancia = self.db.total_vendido_y_ganancias(producto_id)
                    
                    # Calcular en USD
                    compra_usd = compra / self.tasa_dolar
                    venta_usd = venta / self.tasa_dolar
                    ganancia_usd = ganancia / self.tasa_dolar
                    
                    resultado_text.insert(tk.END, f"📦 PRODUCTO: {nombre}\n")
                    resultado_text.insert(tk.END, f"   Categoría: {categoria}\n")
                    resultado_text.insert(tk.END, f"   Precio compra: Bs. {compra:.2f} | ${compra_usd:.2f}\n")
                    resultado_text.insert(tk.END, f"   Precio venta: Bs. {venta:.2f} | ${venta_usd:.2f}\n")
                    resultado_text.insert(tk.END, f"   Stock actual: {stock}\n")
                    resultado_text.insert(tk.END, f"   Total vendido: {vendido} unidades\n")
                    resultado_text.insert(tk.END, f"💰 GANANCIA TOTAL: Bs. {ganancia:.2f} | ${ganancia_usd:.2f}\n")
                    resultado_text.insert(tk.END, "-" * 70 + "\n\n")
            
            resultado_text.config(state="disabled")
        
        def buscar_tiempo_real(event):
            if entry_buscar.get():
                buscar()
        
        entry_buscar.bind('<KeyRelease>', buscar_tiempo_real)
        
        tk.Button(busqueda_frame, text="Buscar", command=buscar).pack(side="left", padx=5)
        tk.Button(busqueda_frame, text="Limpiar", command=lambda: entry_buscar.delete(0, tk.END)).pack(side="left", padx=5)
    
    def mostrar_inventario(self):
        self.limpiar_pantalla()
        frame = tk.Frame(self.root, padx=20, pady=20)
        frame.pack(fill="both", expand=True)
        
        tk.Label(frame, text="📊 INVENTARIO COMPLETO", font=("Arial", 16, "bold")).pack(pady=10)
        
        productos = self.db.obtener_todos_productos()
        
        if not productos:
            tk.Label(frame, text="No hay productos en el inventario").pack(pady=20)
            return
        
        # Frame para la tabla
        tabla_frame = tk.Frame(frame)
        tabla_frame.pack(fill="both", expand=True)
        
        # Crear tabla
        columnas = ("ID", "Producto", "Categoría", "Compra", "Venta", "Stock", "Valor Total")
        tree = ttk.Treeview(tabla_frame, columns=columnas, show="headings", height=15)
        
        tree.heading("ID", text="ID")
        tree.heading("Producto", text="Producto")
        tree.heading("Categoría", text="Categoría")
        tree.heading("Compra", text="Compra (Bs)")
        tree.heading("Venta", text="Venta (Bs)")
        tree.heading("Stock", text="Stock")
        tree.heading("Valor Total", text="Valor Total ($)")
        
        tree.column("ID", width=50)
        tree.column("Producto", width=150)
        tree.column("Categoría", width=100)
        tree.column("Compra", width=80)
        tree.column("Venta", width=80)
        tree.column("Stock", width=60)
        tree.column("Valor Total", width=100)
        
        # Agregar datos
        for p in productos:
            valor_total_bs = p[4] * p[5]  # precio_venta * cantidad
            valor_total_usd = valor_total_bs / self.tasa_dolar
            tree.insert("", "end", values=(
                p[0], p[1], p[2], 
                f"{p[3]:.2f}", f"{p[4]:.2f}", 
                p[5], f"${valor_total_usd:.2f}"
            ))
        
        scrollbar = ttk.Scrollbar(tabla_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Resumen
        resumen_frame = tk.Frame(frame)
        resumen_frame.pack(fill="x", pady=10)
        
        total_productos = len(productos)
        total_stock = sum(p[5] for p in productos)
        valor_inventario_bs = sum(p[4] * p[5] for p in productos)
        valor_inventario_usd = valor_inventario_bs / self.tasa_dolar
        
        tk.Label(resumen_frame, text=f"Total productos: {total_productos} | Stock total: {total_stock} unidades", 
                font=("Arial", 10, "bold")).pack()
        tk.Label(resumen_frame, text=f"Valor inventario: Bs. {valor_inventario_bs:.2f} | ${valor_inventario_usd:.2f} USD", 
                font=("Arial", 10, "bold"), fg="blue").pack()

# --------------------------------------------
# PUNTO DE ENTRADA
# --------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = PanaderiaApp(root)
    
    def on_closing():
        app.db.cerrar()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()