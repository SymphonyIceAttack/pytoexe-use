# panaderia.py
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime

# --------------------------------------------
# CLASE PARA MANEJAR LA BASE DE DATOS
# --------------------------------------------
class BaseDatos:
    def __init__(self):
        self.conexion = sqlite3.connect('panaderia.db')
        self.cursor = self.conexion.cursor()
        self.crear_tablas()
    
    def crear_tablas(self):
        # Tabla de productos
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                precio_compra REAL NOT NULL,
                precio_venta REAL NOT NULL,
                cantidad INTEGER NOT NULL
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
        self.conexion.commit()
    
    def agregar_producto(self, nombre, compra, venta, cantidad):
        try:
            self.cursor.execute(
                "INSERT INTO productos (nombre, precio_compra, precio_venta, cantidad) VALUES (?, ?, ?, ?)",
                (nombre, compra, venta, cantidad)
            )
            self.conexion.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # Producto ya existe
    
    def vender_producto(self, producto_id, cantidad_vender):
        # Verificar stock
        self.cursor.execute("SELECT cantidad, precio_compra, precio_venta, nombre FROM productos WHERE id = ?", (producto_id,))
        producto = self.cursor.fetchone()
        
        if not producto:
            return "Producto no encontrado"
        
        stock_actual, precio_compra, precio_venta, nombre = producto
        
        if cantidad_vender > stock_actual:
            return f"Solo hay {stock_actual} unidades disponibles"
        
        # Calcular ganancia
        ganancia_por_unidad = precio_venta - precio_compra
        ganancia_total = ganancia_por_unidad * cantidad_vender
        
        # Actualizar stock
        nuevo_stock = stock_actual - cantidad_vender
        self.cursor.execute("UPDATE productos SET cantidad = ? WHERE id = ?", (nuevo_stock, producto_id))
        
        # Registrar venta
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute(
            "INSERT INTO ventas (producto_id, cantidad, ganancia, fecha) VALUES (?, ?, ?, ?)",
            (producto_id, cantidad_vender, ganancia_total, fecha_actual)
        )
        
        self.conexion.commit()
        return f"Venta exitosa! Ganancia: ${ganancia_total:.2f}"
    
    def buscar_producto(self, nombre):
        self.cursor.execute(
            "SELECT id, nombre, precio_compra, precio_venta, cantidad FROM productos WHERE nombre LIKE ?",
            (f"%{nombre}%",)
        )
        return self.cursor.fetchall()
    
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
        self.cursor.execute("SELECT id, nombre, precio_compra, precio_venta, cantidad FROM productos ORDER BY nombre")
        return self.cursor.fetchall()
    
    def cerrar(self):
        self.conexion.close()

# --------------------------------------------
# CLASE PRINCIPAL DE LA INTERFAZ
# --------------------------------------------
class PanaderiaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Panadería")
        self.root.geometry("700x500")
        
        # Conectar a base de datos
        self.db = BaseDatos()
        
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
        archivo_menu.add_command(label="Salir", command=self.root.quit)
        
        # Menú Productos
        productos_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Productos", menu=productos_menu)
        productos_menu.add_command(label="Agregar Producto", command=self.mostrar_agregar)
        productos_menu.add_command(label="Ver Inventario", command=self.mostrar_inventario)
        
        # Menú Ventas
        ventas_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ventas", menu=ventas_menu)
        ventas_menu.add_command(label="Registrar Venta", command=self.mostrar_venta)
        ventas_menu.add_command(label="Buscar Producto", command=self.mostrar_buscar)
    
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
        tk.Label(frame, text="\nSeleccione una opción del menú para comenzar", font=("Arial", 12)).pack(pady=30)
    
    def mostrar_agregar(self):
        self.limpiar_pantalla()
        frame = tk.Frame(self.root, padx=20, pady=20)
        frame.pack(fill="both", expand=True)
        
        tk.Label(frame, text="➕ AGREGAR NUEVO PRODUCTO", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Formulario
        form_frame = tk.Frame(frame)
        form_frame.pack(pady=20)
        
        tk.Label(form_frame, text="Nombre del producto:").grid(row=0, column=0, sticky="w", pady=5)
        entry_nombre = tk.Entry(form_frame, width=30)
        entry_nombre.grid(row=0, column=1, pady=5)
        
        tk.Label(form_frame, text="Precio de compra ($):").grid(row=1, column=0, sticky="w", pady=5)
        entry_compra = tk.Entry(form_frame, width=30)
        entry_compra.grid(row=1, column=1, pady=5)
        
        tk.Label(form_frame, text="Precio de venta ($):").grid(row=2, column=0, sticky="w", pady=5)
        entry_venta = tk.Entry(form_frame, width=30)
        entry_venta.grid(row=2, column=1, pady=5)
        
        tk.Label(form_frame, text="Cantidad inicial:").grid(row=3, column=0, sticky="w", pady=5)
        entry_cantidad = tk.Entry(form_frame, width=30)
        entry_cantidad.grid(row=3, column=1, pady=5)
        
        def guardar():
            try:
                nombre = entry_nombre.get()
                compra = float(entry_compra.get())
                venta = float(entry_venta.get())
                cantidad = int(entry_cantidad.get())
                
                if self.db.agregar_producto(nombre, compra, venta, cantidad):
                    messagebox.showinfo("Éxito", f"Producto '{nombre}' agregado correctamente")
                    # Limpiar campos
                    entry_nombre.delete(0, tk.END)
                    entry_compra.delete(0, tk.END)
                    entry_venta.delete(0, tk.END)
                    entry_cantidad.delete(0, tk.END)
                else:
                    messagebox.showerror("Error", "Ya existe un producto con ese nombre")
            except ValueError:
                messagebox.showerror("Error", "Verifica que los números sean válidos")
        
        tk.Button(frame, text="Guardar Producto", command=guardar, bg="green", fg="white", padx=20, pady=5).pack(pady=20)
    
    def mostrar_venta(self):
        self.limpiar_pantalla()
        frame = tk.Frame(self.root, padx=20, pady=20)
        frame.pack(fill="both", expand=True)
        
        tk.Label(frame, text="💰 REGISTRAR VENTA", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Obtener productos para el combobox
        productos = self.db.obtener_todos_productos()
        nombres_productos = [f"{p[1]} (Stock: {p[4]})" for p in productos]
        ids_productos = [p[0] for p in productos]
        
        if not productos:
            tk.Label(frame, text="No hay productos registrados").pack(pady=20)
            return
        
        form_frame = tk.Frame(frame)
        form_frame.pack(pady=20)
        
        tk.Label(form_frame, text="Producto:").grid(row=0, column=0, sticky="w", pady=5)
        combo_producto = ttk.Combobox(form_frame, values=nombres_productos, width=40)
        combo_producto.grid(row=0, column=1, pady=5)
        combo_producto.current(0)
        
        tk.Label(form_frame, text="Cantidad a vender:").grid(row=1, column=0, sticky="w", pady=5)
        entry_cantidad = tk.Entry(form_frame, width=40)
        entry_cantidad.grid(row=1, column=1, pady=5)
        
        def realizar_venta():
            try:
                idx = combo_producto.current()
                if idx < 0:
                    messagebox.showerror("Error", "Selecciona un producto")
                    return
                
                producto_id = ids_productos[idx]
                cantidad = int(entry_cantidad.get())
                
                resultado = self.db.vender_producto(producto_id, cantidad)
                if "exitosa" in resultado:
                    messagebox.showinfo("Venta realizada", resultado)
                    entry_cantidad.delete(0, tk.END)
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
        
        # Buscador
        busqueda_frame = tk.Frame(frame)
        busqueda_frame.pack(pady=10)
        
        tk.Label(busqueda_frame, text="Nombre:").pack(side="left", padx=5)
        entry_buscar = tk.Entry(busqueda_frame, width=30)
        entry_buscar.pack(side="left", padx=5)
        
        resultado_text = scrolledtext.ScrolledText(frame, width=70, height=20, state="disabled")
        resultado_text.pack(pady=20, fill="both", expand=True)
        
        def buscar():
            nombre = entry_buscar.get()
            if not nombre:
                messagebox.showinfo("Info", "Escribe un nombre para buscar")
                return
            
            productos = self.db.buscar_producto(nombre)
            
            resultado_text.config(state="normal")
            resultado_text.delete(1.0, tk.END)
            
            if not productos:
                resultado_text.insert(tk.END, "❌ No se encontraron productos\n")
            else:
                for p in productos:
                    producto_id, nombre, compra, venta, stock = p
                    
                    # Obtener ventas totales de este producto
                    vendido, ganancia = self.db.total_vendido_y_ganancias(producto_id)
                    
                    resultado_text.insert(tk.END, f"📦 PRODUCTO: {nombre}\n")
                    resultado_text.insert(tk.END, f"   Precio compra: ${compra:.2f}\n")
                    resultado_text.insert(tk.END, f"   Precio venta: ${venta:.2f}\n")
                    resultado_text.insert(tk.END, f"   Stock actual: {stock}\n")
                    resultado_text.insert(tk.END, f"   Total vendido: {vendido} unidades\n")
                    resultado_text.insert(tk.END, f"💰 GANANCIA TOTAL: ${ganancia:.2f}\n")
                    resultado_text.insert(tk.END, "-" * 50 + "\n\n")
            
            resultado_text.config(state="disabled")
        
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
        
        # Crear tabla
        columnas = ("ID", "Producto", "Compra", "Venta", "Stock", "Valor Total")
        tree = ttk.Treeview(frame, columns=columnas, show="headings", height=15)
        
        # Definir encabezados
        tree.heading("ID", text="ID")
        tree.heading("Producto", text="Producto")
        tree.heading("Compra", text="Precio Compra")
        tree.heading("Venta", text="Precio Venta")
        tree.heading("Stock", text="Stock")
        tree.heading("Valor Total", text="Valor Total ($)")
        
        # Ajustar anchos
        tree.column("ID", width=50)
        tree.column("Producto", width=150)
        tree.column("Compra", width=100)
        tree.column("Venta", width=100)
        tree.column("Stock", width=80)
        tree.column("Valor Total", width=100)
        
        # Agregar datos
        for p in productos:
            valor_total = p[3] * p[4]  # precio_venta * cantidad
            tree.insert("", "end", values=(p[0], p[1], f"${p[2]:.2f}", f"${p[3]:.2f}", p[4], f"${valor_total:.2f}"))
        
        # Agregar scrollbar
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

# --------------------------------------------
# PUNTO DE ENTRADA DEL PROGRAMA
# --------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = PanaderiaApp(root)
    
    # Al cerrar, cerrar la base de datos
    def on_closing():
        app.db.cerrar()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
