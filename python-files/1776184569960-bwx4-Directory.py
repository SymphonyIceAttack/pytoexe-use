import os
import csv
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from datetime import datetime

# ---------------- CONFIG ----------------
EXTENSIONES = {
    "Word": (".doc", ".docx"),
    "Excel": (".xls", ".xlsx"),
    "PowerPoint": (".ppt", ".pptx")
}

# Carpetas del sistema a excluir (comparación exacta por nombre)
EXCLUIR = {
    "Windows", "Program Files", "Program Files (x86)", "ProgramData",
    "System32", "SysWOW64", "$Recycle.Bin", "System Volume Information",
    "Recovery", "MSOCache", "Config.Msi", "Boot", "PerfLogs"
}

# ---------------- FUNCIONES AUXILIARES ----------------
def es_excluida(ruta):
    """Retorna True si algún componente de la ruta está en EXCLUIR."""
    partes = ruta.split(os.sep)
    return any(p in EXCLUIR for p in partes)

def formatear_tamano(tamano_bytes):
    for unidad in ['B', 'KB', 'MB', 'GB']:
        if tamano_bytes < 1024.0:
            return f"{tamano_bytes:.1f} {unidad}"
        tamano_bytes /= 1024.0
    return f"{tamano_bytes:.1f} TB"

# ---------------- ESCÁNER ----------------
class Escaner:
    def __init__(self, ruta_inicial, callback_archivo, callback_fin):
        self.ruta_inicial = ruta_inicial
        self.callback_archivo = callback_archivo
        self.callback_fin = callback_fin
        self.detener = threading.Event()

    def ejecutar(self):
        try:
            self._escanear(self.ruta_inicial)
        except Exception as e:
            print(f"Error en escaneo: {e}")
        finally:
            self.callback_fin()

    def _escanear(self, ruta):
        if self.detener.is_set():
            return
        try:
            with os.scandir(ruta) as it:
                for entrada in it:
                    if self.detener.is_set():
                        return
                    if es_excluida(entrada.path):
                        continue
                    if entrada.is_dir(follow_symlinks=False):
                        self._escanear(entrada.path)
                    elif entrada.is_file(follow_symlinks=False):
                        ext = os.path.splitext(entrada.name)[1].lower()
                        for tipo, extensiones in EXTENSIONES.items():
                            if ext in extensiones:
                                try:
                                    stat = entrada.stat()
                                    info = {
                                        "nombre": entrada.name,
                                        "ruta": entrada.path,
                                        "tamano": formatear_tamano(stat.st_size),
                                        "tamano_bytes": stat.st_size,
                                        "modificado": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                                    }
                                    self.callback_archivo(tipo, info)
                                except (PermissionError, OSError):
                                    pass
                                break
        except PermissionError:
            pass

# ---------------- INTERFAZ PRINCIPAL ----------------
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Unidad de Análisis e Inteligencia Mediática")
        self.root.geometry("1300x700")
        self.root.configure(bg="#1e1e1e")

        self.data = {t: [] for t in EXTENSIONES}
        self.escaner = None
        self.actualizacion_pendiente = False
        self.filtro_texto = ""

        # ----- FONDO CON LOGOTIPO -----
        try:
            # Cargar la imagen que el usuario proporcionó (debe llamarse "logo.png" o cambiar el nombre)
            img = Image.open("logo.png")
            # Redimensionar para que cubra toda la ventana (se puede ajustar)
            img = img.resize((1300, 700), Image.Resampling.LANCZOS)
            # Aplicar transparencia para no molestar la lectura (valor 80 = más transparente)
            img.putalpha(80)
            self.bg_img = ImageTk.PhotoImage(img)
            # Label de fondo que se expande con la ventana
            self.bg_label = tk.Label(root, image=self.bg_img, bg="#1e1e1e")
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            # Enviar al fondo (detrás de todos los demás widgets)
            self.bg_label.lower()
        except Exception as e:
            print(f"No se pudo cargar el logotipo: {e}")
            # Si no hay imagen, el fondo queda gris oscuro (no crítico)

        # ----- FRAME SUPERIOR (botones, etc.) -----
        top = tk.Frame(root, bg="#1e1e1e", bd=0)
        top.pack(fill="x", pady=10)

        self.ruta_var = tk.StringVar()
        entry = tk.Entry(top, textvariable=self.ruta_var, width=80, bg="#2b2b2b", fg="white")
        entry.pack(side="left", padx=10)

        btn_carpeta = tk.Button(top, text="📁 Carpeta", command=self.seleccionar_carpeta, bg="#444", fg="white")
        btn_carpeta.pack(side="left")

        btn_escanear = tk.Button(top, text="▶ Escanear", command=self.iniciar_escaneo, bg="#007acc", fg="white")
        btn_escanear.pack(side="left", padx=5)

        self.btn_detener = tk.Button(top, text="⏹ Detener", command=self.detener_escaneo, bg="#aa3333", fg="white", state="disabled")
        self.btn_detener.pack(side="left")

        btn_exportar = tk.Button(top, text="💾 Exportar CSV", command=self.exportar_csv, bg="#2b6a2b", fg="white")
        btn_exportar.pack(side="left", padx=5)

        # ----- FILTRO -----
        frame_filtro = tk.Frame(root, bg="#1e1e1e")
        frame_filtro.pack(fill="x", pady=5)
        tk.Label(frame_filtro, text="Filtrar por nombre:", bg="#1e1e1e", fg="white").pack(side="left", padx=10)
        self.filtro_entry = tk.Entry(frame_filtro, bg="#2b2b2b", fg="white", width=40)
        self.filtro_entry.pack(side="left")
        self.filtro_entry.bind("<KeyRelease>", self.aplicar_filtro)

        # ----- BARRA DE PROGRESO Y ESTADO -----
        self.progress = ttk.Progressbar(root, mode="indeterminate")
        self.progress.pack(fill="x", padx=10, pady=5)
        self.estado_label = tk.Label(root, text="Listo", bg="#1e1e1e", fg="#aaaaaa")
        self.estado_label.pack()

        # ----- CONTADORES -----
        frame_contadores = tk.Frame(root, bg="#1e1e1e")
        frame_contadores.pack(pady=5)
        self.labels_contador = {}
        for i, t in enumerate(EXTENSIONES):
            lbl = tk.Label(frame_contadores, text=f"{t}: 0", fg="white", bg="#1e1e1e", font=("Segoe UI", 10, "bold"))
            lbl.grid(row=0, column=i, padx=20)
            self.labels_contador[t] = lbl

        # ----- TABLAS (TREEVIEW) -----
        frame_tablas = tk.Frame(root, bg="#1e1e1e")
        frame_tablas.pack(fill="both", expand=True)

        self.treeviews = {}
        for i, t in enumerate(EXTENSIONES):
            f = tk.Frame(frame_tablas, bg="#1e1e1e")
            f.grid(row=0, column=i, sticky="nsew", padx=5, pady=5)

            tk.Label(f, text=t, bg="#1e1e1e", fg="white", font=("Segoe UI", 11, "bold")).pack(anchor="w")

            tree_frame = tk.Frame(f)
            tree_frame.pack(fill="both", expand=True)
            scroll = ttk.Scrollbar(tree_frame)
            scroll.pack(side="right", fill="y")

            tree = ttk.Treeview(tree_frame, columns=("nombre", "ruta", "tamano", "modificado"), show="headings", yscrollcommand=scroll.set)
            tree.heading("nombre", text="Nombre", command=lambda col="nombre", t=t: self.ordenar_por_columna(t, col))
            tree.heading("ruta", text="Ruta", command=lambda col="ruta", t=t: self.ordenar_por_columna(t, col))
            tree.heading("tamano", text="Tamaño", command=lambda col="tamano_bytes", t=t: self.ordenar_por_columna(t, col))
            tree.heading("modificado", text="Modificado", command=lambda col="modificado", t=t: self.ordenar_por_columna(t, col))

            tree.column("nombre", width=200)
            tree.column("ruta", width=350)
            tree.column("tamano", width=80)
            tree.column("modificado", width=130)
            tree.pack(side="left", fill="both", expand=True)
            scroll.config(command=tree.yview)

            tree.bind("<Double-1>", self.abrir_archivo)
            tree.bind("<Button-3>", self.menu_contextual)
            self.treeviews[t] = tree

        for i in range(3):
            frame_tablas.columnconfigure(i, weight=1)

        # Variables para ordenamiento
        self.orden_columna = {}
        self.orden_reverso = {}

        # Ajustar fondo al redimensionar la ventana
        self.root.bind("<Configure>", self.redimensionar_fondo)

    def redimensionar_fondo(self, event=None):
        """Redimensiona la imagen de fondo cuando se cambia el tamaño de la ventana."""
        if hasattr(self, 'bg_img') and self.bg_img:
            try:
                nueva_imagen = Image.open("logo.png")
                nueva_imagen = nueva_imagen.resize((self.root.winfo_width(), self.root.winfo_height()), Image.Resampling.LANCZOS)
                nueva_imagen.putalpha(80)
                self.bg_img = ImageTk.PhotoImage(nueva_imagen)
                self.bg_label.config(image=self.bg_img)
            except:
                pass

    def seleccionar_carpeta(self):
        path = filedialog.askdirectory()
        if path:
            self.ruta_var.set(path)

    def iniciar_escaneo(self):
        ruta = self.ruta_var.get()
        if not ruta:
            messagebox.showwarning("Aviso", "Selecciona una carpeta primero.")
            return
        if not os.path.exists(ruta):
            messagebox.showerror("Error", "La ruta no existe.")
            return

        for t in EXTENSIONES:
            self.data[t] = []
            self.treeviews[t].delete(*self.treeviews[t].get_children())
            self.labels_contador[t].config(text=f"{t}: 0")

        self.progress.start()
        self.estado_label.config(text="Escaneando...", fg="yellow")
        self.btn_detener.config(state="normal")

        self.escaner = Escaner(ruta, self.recibir_archivo, self.escaneo_terminado)
        threading.Thread(target=self.escaner.ejecutar, daemon=True).start()

    def detener_escaneo(self):
        if self.escaner:
            self.escaner.detener.set()
            self.estado_label.config(text="Cancelando...", fg="orange")

    def escaneo_terminado(self):
        self.progress.stop()
        self.btn_detener.config(state="disabled")
        if self.escaner and self.escaner.detener.is_set():
            self.estado_label.config(text="Escaneo cancelado", fg="red")
        else:
            total = sum(len(v) for v in self.data.values())
            self.estado_label.config(text=f"Completado. Total archivos: {total}", fg="lightgreen")
        self.escaner = None

    def recibir_archivo(self, tipo, info):
        self.data[tipo].append(info)
        if not self.actualizacion_pendiente:
            self.actualizacion_pendiente = True
            self.root.after(100, self._actualizar_ui_diferida)

    def _actualizar_ui_diferida(self):
        for tipo, lista in self.data.items():
            self._refrescar_tabla(tipo)
            self.labels_contador[tipo].config(text=f"{tipo}: {len(lista)}")
        self.actualizacion_pendiente = False

    def _refrescar_tabla(self, tipo):
        tree = self.treeviews[tipo]
        tree.delete(*tree.get_children())
        filtro = self.filtro_texto.lower()
        datos = self.data[tipo]
        if filtro:
            datos = [d for d in datos if filtro in d["nombre"].lower()]
        col = self.orden_columna.get(tipo)
        if col:
            reverso = self.orden_reverso.get(tipo, False)
            datos.sort(key=lambda x: x.get(col, ""), reverse=reverso)
        for d in datos:
            tree.insert("", "end", values=(d["nombre"], d["ruta"], d["tamano"], d["modificado"]), tags=(d["ruta"],))

    def aplicar_filtro(self, event=None):
        self.filtro_texto = self.filtro_entry.get()
        for t in EXTENSIONES:
            self._refrescar_tabla(t)

    def ordenar_por_columna(self, tipo, columna):
        if self.orden_columna.get(tipo) == columna:
            self.orden_reverso[tipo] = not self.orden_reverso.get(tipo, False)
        else:
            self.orden_columna[tipo] = columna
            self.orden_reverso[tipo] = False
        self._refrescar_tabla(tipo)

    def abrir_archivo(self, event):
        tree = event.widget
        seleccion = tree.selection()
        if seleccion:
            item = seleccion[0]
            ruta = tree.item(item, "tags")[0]
            try:
                os.startfile(ruta)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir:\n{ruta}\n{e}")

    def menu_contextual(self, event):
        tree = event.widget
        item = tree.identify_row(event.y)
        if item:
            tree.selection_set(item)
            ruta = tree.item(item, "tags")[0]
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label="Abrir", command=lambda: os.startfile(ruta))
            menu.add_command(label="Abrir ubicación", command=lambda: os.startfile(os.path.dirname(ruta)))
            menu.add_command(label="Copiar ruta", command=lambda: self.root.clipboard_append(ruta))
            menu.post(event.x_root, event.y_root)

    def exportar_csv(self):
        if not any(self.data.values()):
            messagebox.showinfo("Exportar", "No hay datos para exportar.")
            return
        archivo = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not archivo:
            return
        try:
            with open(archivo, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["Tipo", "Nombre", "Ruta completa", "Tamaño", "Modificado"])
                for tipo, lista in self.data.items():
                    for info in lista:
                        writer.writerow([tipo, info["nombre"], info["ruta"], info["tamano"], info["modificado"]])
            messagebox.showinfo("Exportar", f"Exportado correctamente a:\n{archivo}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar:\n{e}")

# ---------------- MAIN ----------------
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()