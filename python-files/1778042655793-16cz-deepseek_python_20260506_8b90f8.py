import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import xml.etree.ElementTree as ET
from xml.dom import minidom
import os
from datetime import datetime

class AddendaGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Generador de Addenda - Pilgrim's Pride")
        self.root.geometry("800x700")
        self.partidas = []
        self.xml_original_path = None
        self.xml_modificado_path = None
        
        self.setup_ui()
    
    def setup_ui(self):
        # Frame de datos fijos
        frame_fijos = ttk.LabelFrame(self.root, text="Datos del Proveedor", padding=10)
        frame_fijos.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(frame_fijos, text="Número de Proveedor:").grid(row=0, column=0, sticky="w")
        self.proveedor_entry = ttk.Entry(frame_fijos, width=20)
        self.proveedor_entry.grid(row=0, column=1, padx=5)
        self.proveedor_entry.insert(0, "427589")
        
        ttk.Label(frame_fijos, text="Proceso:").grid(row=1, column=0, sticky="w")
        self.proceso_entry = ttk.Entry(frame_fijos, width=20)
        self.proceso_entry.grid(row=1, column=1, padx=5)
        self.proceso_entry.insert(0, "01")
        
        # Frame de partidas
        frame_partidas = ttk.LabelFrame(self.root, text="Partidas (Productos/Servicios)", padding=10)
        frame_partidas.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Treeview para mostrar partidas
        self.tree = ttk.Treeview(frame_partidas, columns=("Pedido", "Posicion", "Referencia"), show="headings", height=6)
        self.tree.heading("Pedido", text="N° Pedido")
        self.tree.heading("Posicion", text="Posición")
        self.tree.heading("Referencia", text="Referencia")
        
        # Configurar anchos de columnas
        self.tree.column("Pedido", width=200)
        self.tree.column("Posicion", width=100)
        self.tree.column("Referencia", width=200)
        
        self.tree.pack(fill="both", expand=True)
        
        # Botones de partidas
        frame_botones = ttk.Frame(frame_partidas)
        frame_botones.pack(fill="x", pady=5)
        
        ttk.Button(frame_botones, text="➕ Agregar Partida", command=self.agregar_partida).pack(side="left", padx=2)
        ttk.Button(frame_botones, text="📋 Duplicar Partida", command=self.duplicar_partida).pack(side="left", padx=2)
        ttk.Button(frame_botones, text="✏️ Editar Partida", command=self.editar_partida).pack(side="left", padx=2)
        ttk.Button(frame_botones, text="❌ Eliminar", command=self.eliminar_partida).pack(side="left", padx=2)
        
        # Frame de selección de XML
        frame_xml = ttk.LabelFrame(self.root, text="Archivo CFDI (XML)", padding=10)
        frame_xml.pack(fill="x", padx=10, pady=5)
        
        self.xml_label = ttk.Label(frame_xml, text="No se ha seleccionado ningún archivo XML", foreground="gray")
        self.xml_label.pack(side="left", fill="x", expand=True)
        
        ttk.Button(frame_xml, text="📂 Seleccionar CFDI", command=self.seleccionar_xml).pack(side="right", padx=5)
        
        # Frame de resultado
        frame_resultado = ttk.LabelFrame(self.root, text="Addenda Generada (Vista previa)", padding=10)
        frame_resultado.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.resultado_text = scrolledtext.ScrolledText(frame_resultado, height=8, wrap=tk.WORD, font=("Consolas", 9))
        self.resultado_text.pack(fill="both", expand=True)
        
        # Botones de acción principales
        frame_acciones = ttk.Frame(self.root)
        frame_acciones.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(frame_acciones, text="🔍 Previsualizar Addenda", command=self.previsualizar, width=20).pack(side="left", padx=5)
        ttk.Button(frame_acciones, text="💾 Generar e Integrar al XML", command=self.integrar_al_xml, width=25).pack(side="left", padx=5)
        ttk.Button(frame_acciones, text="📋 Solo copiar Addenda", command=self.solo_copiar, width=20).pack(side="left", padx=5)
        
        # Label de estado
        self.status_label = ttk.Label(self.root, text="✅ Listo", foreground="green")
        self.status_label.pack(pady=5)
    
    def duplicar_partida(self):
        """Duplica la partida seleccionada para facilitar la captura"""
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Sin selección", "Selecciona una partida para duplicar")
            return
        
        # Obtener los valores de la partida seleccionada
        valores = self.tree.item(seleccion)["values"]
        pedido = valores[0]
        posicion = valores[1]
        referencia = valores[2]
        
        # Preguntar si quiere modificar algo antes de duplicar
        ventana = tk.Toplevel(self.root)
        ventana.title("Duplicar Partida")
        ventana.geometry("400x250")
        ventana.transient(self.root)
        ventana.grab_set()
        
        ttk.Label(ventana, text="Número de Pedido (puedes modificarlo):").pack(pady=5)
        pedido_entry = ttk.Entry(ventana, width=40)
        pedido_entry.insert(0, pedido)
        pedido_entry.pack()
        
        ttk.Label(ventana, text="Posición:").pack(pady=5)
        posicion_entry = ttk.Entry(ventana, width=40)
        posicion_entry.insert(0, posicion)
        posicion_entry.pack()
        
        ttk.Label(ventana, text="Referencia:").pack(pady=5)
        referencia_entry = ttk.Entry(ventana, width=40)
        referencia_entry.insert(0, referencia)
        referencia_entry.pack()
        
        def guardar_duplicado():
            nuevo_pedido = pedido_entry.get().strip()
            nueva_posicion = posicion_entry.get().strip()
            nueva_referencia = referencia_entry.get().strip()
            
            if nuevo_pedido and nueva_posicion and nueva_referencia:
                self.tree.insert("", "end", values=(nuevo_pedido, nueva_posicion, nueva_referencia))
                ventana.destroy()
                self.status_label.config(text=f"✅ Partida duplicada: {nueva_referencia}", foreground="green")
            else:
                messagebox.showwarning("Campos incompletos", "Todos los campos son obligatorios")
        
        ttk.Button(ventana, text="Duplicar", command=guardar_duplicado).pack(pady=10)
    
    def agregar_partida(self):
        ventana = tk.Toplevel(self.root)
        ventana.title("Nueva Partida")
        ventana.geometry("400x250")
        ventana.transient(self.root)
        ventana.grab_set()
        
        ttk.Label(ventana, text="Número de Pedido:").pack(pady=5)
        pedido_entry = ttk.Entry(ventana, width=40)
        pedido_entry.pack()
        
        ttk.Label(ventana, text="Posición:").pack(pady=5)
        posicion_entry = ttk.Entry(ventana, width=40)
        posicion_entry.pack()
        
        ttk.Label(ventana, text="Referencia:").pack(pady=5)
        referencia_entry = ttk.Entry(ventana, width=40)
        referencia_entry.pack()
        
        def guardar():
            pedido = str(pedido_entry.get().strip())  # Convertir a string explícitamente
            posicion = str(posicion_entry.get().strip())  # Convertir a string explícitamente
            referencia = str(referencia_entry.get().strip())  # Convertir a string explícitamente
            
            if pedido and posicion and referencia:
                self.tree.insert("", "end", values=(pedido, posicion, referencia))
                ventana.destroy()
                self.status_label.config(text=f"✅ Partida agregada: {referencia}", foreground="green")
            else:
                messagebox.showwarning("Campos incompletos", "Todos los campos son obligatorios")
        
        ttk.Button(ventana, text="Guardar", command=guardar).pack(pady=10)
    
    def editar_partida(self):
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Sin selección", "Selecciona una partida para editar")
            return
        
        valores = self.tree.item(seleccion)["values"]
        
        ventana = tk.Toplevel(self.root)
        ventana.title("Editar Partida")
        ventana.geometry("400x250")
        ventana.transient(self.root)
        ventana.grab_set()
        
        ttk.Label(ventana, text="Número de Pedido:").pack(pady=5)
        pedido_entry = ttk.Entry(ventana, width=40)
        pedido_entry.insert(0, valores[0])
        pedido_entry.pack()
        
        ttk.Label(ventana, text="Posición:").pack(pady=5)
        posicion_entry = ttk.Entry(ventana, width=40)
        posicion_entry.insert(0, valores[1])
        posicion_entry.pack()
        
        ttk.Label(ventana, text="Referencia:").pack(pady=5)
        referencia_entry = ttk.Entry(ventana, width=40)
        referencia_entry.insert(0, valores[2])
        referencia_entry.pack()
        
        def guardar():
            pedido = str(pedido_entry.get().strip())
            posicion = str(posicion_entry.get().strip())
            referencia = str(referencia_entry.get().strip())
            
            if pedido and posicion and referencia:
                self.tree.item(seleccion, values=(pedido, posicion, referencia))
                ventana.destroy()
                self.status_label.config(text=f"✅ Partida editada: {referencia}", foreground="green")
            else:
                messagebox.showwarning("Campos incompletos", "Todos los campos son obligatorios")
        
        ttk.Button(ventana, text="Guardar", command=guardar).pack(pady=10)
    
    def eliminar_partida(self):
        seleccion = self.tree.selection()
        if seleccion:
            if messagebox.askyesno("Confirmar", "¿Eliminar esta partida?"):
                self.tree.delete(seleccion)
                self.status_label.config(text="✅ Partida eliminada", foreground="green")
    
    def seleccionar_xml(self):
        archivo = filedialog.askopenfilename(
            title="Seleccionar CFDI XML",
            filetypes=[("Archivos XML", "*.xml"), ("Todos los archivos", "*.*")]
        )
        if archivo:
            self.xml_original_path = archivo
            self.xml_label.config(text=f"📄 {os.path.basename(archivo)}", foreground="blue")
            self.status_label.config(text=f"✅ XML seleccionado: {os.path.basename(archivo)}", foreground="green")
    
    def generar_addenda_xml(self):
        """Genera el nodo Addenda como string XML (todos los valores como string)"""
        proveedor = str(self.proveedor_entry.get().strip())
        proceso = str(self.proceso_entry.get().strip())
        
        if not proveedor or not proceso:
            messagebox.showerror("Error", "Faltan datos del proveedor")
            return None
        
        partidas = []
        for item in self.tree.get_children():
            valores = self.tree.item(item)["values"]
            partidas.append({
                "pedido": str(valores[0]),  # Forzar a string
                "posicion": str(valores[1]),  # Forzar a string
                "referencia": str(valores[2])  # Forzar a string
            })
        
        if not partidas:
            messagebox.showerror("Error", "Debes agregar al menos una partida")
            return None
        
        # Crear el XML manualmente para evitar problemas de serialización
        xml_lines = ['<cfdi:Addenda>']
        xml_lines.append('  <Pilgrims>')
        xml_lines.append(f'    <Proveedor>{proveedor}</Proveedor>')
        xml_lines.append(f'    <Proceso>{proceso}</Proceso>')
        
        for p in partidas:
            xml_lines.append(f'    <Partida Pedido="{p["pedido"]}" Posicion="{p["posicion"]}">')
            xml_lines.append(f'      <Referencia>{p["referencia"]}</Referencia>')
            xml_lines.append('    </Partida>')
        
        xml_lines.append('  </Pilgrims>')
        xml_lines.append('</cfdi:Addenda>')
        
        return '\n'.join(xml_lines)
    
    def previsualizar(self):
        """Muestra la addenda en el textbox"""
        addenda_xml = self.generar_addenda_xml()
        if addenda_xml:
            self.resultado_text.delete("1.0", tk.END)
            self.resultado_text.insert("1.0", addenda_xml)
            self.status_label.config(text="✅ Addenda generada (solo vista previa)", foreground="green")
    
    def solo_copiar(self):
        """Solo genera y copia la addenda al portapapeles"""
        addenda_xml = self.generar_addenda_xml()
        if addenda_xml:
            self.root.clipboard_clear()
            self.root.clipboard_append(addenda_xml)
            messagebox.showinfo("Copiado", "La addenda se ha copiado al portapapeles")
            self.status_label.config(text="✅ Addenda copiada al portapapeles", foreground="green")
    
    def integrar_al_xml(self):
        """Integra la addenda al XML seleccionado"""
        if not self.xml_original_path:
            messagebox.showerror("Error", "Primero selecciona un archivo CFDI XML")
            return
        
        addenda_xml_str = self.generar_addenda_xml()
        if not addenda_xml_str:
            return
        
        try:
            # Leer el XML original
            with open(self.xml_original_path, 'r', encoding='utf-8') as f:
                contenido = f.read()
            
            # Buscar si ya existe una addenda
            import re
            
            # Buscar y eliminar addenda existente
            patron_addenda = r'<cfdi:Addenda>.*?</cfdi:Addenda>\s*\n?'
            contenido_sin_addenda = re.sub(patron_addenda, '', contenido, flags=re.DOTALL)
            
            # Insertar la nueva addenda ANTES del cierre de </cfdi:Comprobante>
            # O justo después de <cfdi:Complemento> si existe
            if '</cfdi:Complemento>' in contenido_sin_addenda:
                # Insertar después del Complemento
                contenido_nuevo = contenido_sin_addenda.replace(
                    '</cfdi:Complemento>',
                    f'</cfdi:Complemento>\n\t{addenda_xml_str}'
                )
            else:
                # Insertar antes del cierre del Comprobante
                contenido_nuevo = contenido_sin_addenda.replace(
                    '</cfdi:Comprobante>',
                    f'\t{addenda_xml_str}\n</cfdi:Comprobante>'
                )
            
            # Guardar el archivo
            nombre_base = os.path.splitext(os.path.basename(self.xml_original_path))[0]
            fecha_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_salida = f"{nombre_base}_CON_ADDENDA_{fecha_hora}.xml"
            
            archivo_salida = filedialog.asksaveasfilename(
                title="Guardar XML con Addenda",
                defaultextension=".xml",
                initialfile=nombre_salida,
                filetypes=[("Archivos XML", "*.xml")]
            )
            
            if archivo_salida:
                with open(archivo_salida, 'w', encoding='utf-8') as f:
                    f.write(contenido_nuevo)
                
                self.xml_modificado_path = archivo_salida
                self.status_label.config(text=f"✅ ¡Éxito! XML guardado en: {os.path.basename(archivo_salida)}", foreground="green")
                
                if messagebox.askyesno("Completado", f"Archivo guardado en:\n{archivo_salida}\n\n¿Abrir ubicación?"):
                    os.startfile(os.path.dirname(archivo_salida))
            
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error: {e}")
            self.status_label.config(text="❌ Error al integrar", foreground="red")

if __name__ == "__main__":
    root = tk.Tk()
    app = AddendaGeneratorApp(root)
    root.mainloop()