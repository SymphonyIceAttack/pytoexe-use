import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import xml.etree.ElementTree as ET
from xml.dom import minidom

class AddendaGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Generador de Addenda - Pilgrim's Pride")
        self.root.geometry("700x600")
        self.partidas = []
        
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
        frame_partidas = ttk.LabelFrame(self.root, text="Partidas", padding=10)
        frame_partidas.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Treeview para mostrar partidas
        self.tree = ttk.Treeview(frame_partidas, columns=("Pedido", "Posicion", "Referencia"), show="headings", height=8)
        self.tree.heading("Pedido", text="N° Pedido")
        self.tree.heading("Posicion", text="Posición")
        self.tree.heading("Referencia", text="Referencia")
        self.tree.pack(fill="both", expand=True)
        
        # Botones de partidas
        frame_botones = ttk.Frame(frame_partidas)
        frame_botones.pack(fill="x", pady=5)
        
        ttk.Button(frame_botones, text="➕ Agregar Partida", command=self.agregar_partida).pack(side="left", padx=5)
        ttk.Button(frame_botones, text="❌ Eliminar seleccionada", command=self.eliminar_partida).pack(side="left", padx=5)
        
        # Frame de resultado
        frame_resultado = ttk.LabelFrame(self.root, text="Addenda Generada", padding=10)
        frame_resultado.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.resultado_text = scrolledtext.ScrolledText(frame_resultado, height=10, wrap=tk.WORD)
        self.resultado_text.pack(fill="both", expand=True)
        
        # Botón generar
        ttk.Button(self.root, text="🚀 GENERAR ADDENDA", command=self.generar, width=30).pack(pady=10)
    
    def agregar_partida(self):
        ventana = tk.Toplevel(self.root)
        ventana.title("Nueva Partida")
        ventana.geometry("300x200")
        ventana.transient(self.root)
        ventana.grab_set()
        
        ttk.Label(ventana, text="Número de Pedido:").pack(pady=5)
        pedido_entry = ttk.Entry(ventana, width=30)
        pedido_entry.pack()
        
        ttk.Label(ventana, text="Posición:").pack(pady=5)
        posicion_entry = ttk.Entry(ventana, width=30)
        posicion_entry.pack()
        
        ttk.Label(ventana, text="Referencia:").pack(pady=5)
        referencia_entry = ttk.Entry(ventana, width=30)
        referencia_entry.pack()
        
        def guardar():
            pedido = pedido_entry.get().strip()
            posicion = posicion_entry.get().strip()
            referencia = referencia_entry.get().strip()
            
            if pedido and posicion and referencia:
                self.tree.insert("", "end", values=(pedido, posicion, referencia))
                ventana.destroy()
            else:
                messagebox.showwarning("Campos incompletos", "Todos los campos son obligatorios")
        
        ttk.Button(ventana, text="Guardar", command=guardar).pack(pady=10)
    
    def eliminar_partida(self):
        seleccion = self.tree.selection()
        if seleccion:
            self.tree.delete(seleccion)
    
    def generar_addenda_xml(self, proveedor, proceso, partidas):
        addenda = ET.Element("cfdi:Addenda")
        pilgrims = ET.SubElement(addenda, "Pilgrims")
        
        ET.SubElement(pilgrims, "Proveedor").text = proveedor
        ET.SubElement(pilgrims, "Proceso").text = proceso
        
        for p in partidas:
            partida = ET.SubElement(pilgrims, "Partida")
            partida.set("Pedido", p["pedido"])
            partida.set("Posicion", p["posicion"])
            ET.SubElement(partida, "Referencia").text = p["referencia"]
        
        # Formatear bonito
        rough = ET.tostring(addenda, encoding="utf-8")
        reparsed = minidom.parseString(rough)
        return reparsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")
    
    def generar(self):
        proveedor = self.proveedor_entry.get().strip()
        proceso = self.proceso_entry.get().strip()
        
        if not proveedor or not proceso:
            messagebox.showerror("Error", "Faltan datos del proveedor")
            return
        
        partidas = []
        for item in self.tree.get_children():
            valores = self.tree.item(item)["values"]
            partidas.append({
                "pedido": valores[0],
                "posicion": valores[1],
                "referencia": valores[2]
            })
        
        if not partidas:
            messagebox.showerror("Error", "Debes agregar al menos una partida")
            return
        
        try:
            xml_generado = self.generar_addenda_xml(proveedor, proceso, partidas)
            self.resultado_text.delete("1.0", tk.END)
            self.resultado_text.insert("1.0", xml_generado)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AddendaGeneratorApp(root)
    root.mainloop()