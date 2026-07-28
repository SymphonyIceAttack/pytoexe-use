import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os

try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

class PowerBIHelperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Power BI Data Prepper - Asistente de ETL")
        self.root.geometry("750x600")
        self.root.configure(padx=15, pady=15)
        
        self.df = None # Aquí guardaremos los datos originales
        self.df_clean = None # Aquí guardaremos los datos limpios
        self.file_name = ""

        self.setup_ui()

    def setup_ui(self):
        if not PANDAS_AVAILABLE:
            tk.Label(self.root, text="⚠️ Faltan librerías requeridas.\nInstala: pip install pandas openpyxl", fg="red", font=("Arial", 12)).pack(pady=50)
            return

        # Título principal
        ttk.Label(self.root, text="📊 Preparador de Datos para Power BI", font=("Helvetica", 16, "bold")).pack(pady=(0, 15))

        # Crear sistema de pestañas
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        # --- Pestaña 1: Carga de Datos ---
        self.tab_load = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_load, text="1. Cargar Archivo")
        self.build_load_tab()

        # --- Pestaña 2: Limpieza y Normalización ---
        self.tab_clean = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_clean, text="2. Limpieza (ETL)")
        self.build_clean_tab()

        # --- Pestaña 3: Exportar y Extras BI ---
        self.tab_export = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_export, text="3. Exportar a BI")
        self.build_export_tab()

    def build_load_tab(self):
        frame = ttk.LabelFrame(self.tab_load, text="Selección de Origen de Datos", padding=15)
        frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(frame, text="Soporta: Excel (.xlsx, .xls), CSV y JSON").pack(anchor="w", pady=(0, 10))
        
        ttk.Button(frame, text="📂 Buscar Archivo", command=self.load_file).pack(anchor="w")
        self.lbl_file = ttk.Label(frame, text="Ningún archivo seleccionado", foreground="gray")
        self.lbl_file.pack(anchor="w", pady=(5, 10))

        # Vista previa
        ttk.Label(self.tab_load, text="Vista Previa de los Datos (Primeras 5 filas):", font=("", 10, "bold")).pack(anchor="w", padx=10, pady=(10, 0))
        
        # Usamos un widget Text con fuente monoespaciada para la vista previa
        self.text_preview = tk.Text(self.tab_load, height=15, wrap="none", font=("Courier", 9))
        
        # Scrollbars para la vista previa
        scroll_y = ttk.Scrollbar(self.tab_load, orient="vertical", command=self.text_preview.yview)
        scroll_x = ttk.Scrollbar(self.tab_load, orient="horizontal", command=self.text_preview.xview)
        self.text_preview.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        
        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        self.text_preview.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=(0, 10))

    def load_file(self):
        filepath = filedialog.askopenfilename(
            title="Seleccionar datos",
            filetypes=[("Archivos de Datos", "*.csv *.xlsx *.xls *.json"), ("Todos", "*.*")]
        )
        if not filepath: return

        self.lbl_file.config(text=filepath)
        self.file_name = os.path.basename(filepath)
        _, ext = os.path.splitext(filepath)

        try:
            # Detectar formato y cargar con Pandas
            if ext.lower() == '.csv':
                # Intentamos separar por coma, si falla por punto y coma (muy común en español)
                try:
                    self.df = pd.read_csv(filepath)
                except:
                    self.df = pd.read_csv(filepath, sep=';', encoding='latin1')
            elif ext.lower() in ['.xlsx', '.xls']:
                self.df = pd.read_excel(filepath)
            elif ext.lower() == '.json':
                self.df = pd.read_json(filepath)
            else:
                messagebox.showerror("Error", "Formato no soportado.")
                return

            self.df_clean = self.df.copy()
            self.update_preview(self.df)
            messagebox.showinfo("Éxito", f"Archivo cargado correctamente.\nFilas: {self.df.shape[0]}\nColumnas: {self.df.shape[1]}")
            
            # Cambiar a la pestaña de limpieza automáticamente
            self.notebook.select(self.tab_clean)

        except Exception as e:
            messagebox.showerror("Error de Lectura", f"No se pudo leer el archivo:\n{str(e)}")

    def update_preview(self, dataframe):
        self.text_preview.delete(1.0, tk.END)
        if dataframe is not None:
            # Mostrar resumen y las primeras filas
            info = f"--- INFO DEL DATASET ---\nFilas: {dataframe.shape[0]} | Columnas: {dataframe.shape[1]}\n"
            info += f"Columnas: {', '.join(dataframe.columns.tolist())}\n\n"
            info += dataframe.head(10).to_string()
            self.text_preview.insert(tk.END, info)

    def build_clean_tab(self):
        frame = ttk.LabelFrame(self.tab_clean, text="Opciones de Normalización (Selecciona las necesarias)", padding=15)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Variables para los checkboxes
        self.chk_cols = tk.BooleanVar(value=True)
        self.chk_dups = tk.BooleanVar(value=True)
        self.chk_dates = tk.BooleanVar(value=True)
        self.null_action = tk.StringVar(value="fill_zero")

        # 1. Columnas
        ttk.Checkbutton(frame, text="Normalizar Nombres de Columnas (Recomendado para DAX)\n(Convierte 'Nombre Cliente' a 'nombre_cliente', quita acentos/símbolos)", variable=self.chk_cols).pack(anchor="w", pady=5)
        
        # 2. Duplicados
        ttk.Checkbutton(frame, text="Eliminar Filas Exactamente Duplicadas", variable=self.chk_dups).pack(anchor="w", pady=5)
        
        # 3. Fechas
        ttk.Checkbutton(frame, text="Intentar convertir columnas de texto a formato Fecha Automáticamente", variable=self.chk_dates).pack(anchor="w", pady=5)

        # 4. Nulos
        ttk.Label(frame, text="\n¿Qué hacer con los valores vacíos (Nulos/NaN)?").pack(anchor="w")
        ttk.Radiobutton(frame, text="Dejarlos como están (Power BI los leerá como (Blank))", variable=self.null_action, value="ignore").pack(anchor="w")
        ttk.Radiobutton(frame, text="Llenar números con 0 y textos con 'Sin Datos'", variable=self.null_action, value="fill_zero").pack(anchor="w")
        ttk.Radiobutton(frame, text="Eliminar cualquier fila que tenga un dato vacío", variable=self.null_action, value="drop").pack(anchor="w")

        ttk.Button(frame, text="⚙️ Aplicar Limpieza", command=self.apply_cleaning).pack(pady=20)

    def apply_cleaning(self):
        if self.df is None:
            messagebox.showwarning("Atención", "Primero debes cargar un archivo en la Pestaña 1.")
            return

        try:
            # Trabajar sobre una copia limpia
            temp_df = self.df.copy()

            # 1. Normalizar Columnas
            if self.chk_cols.get():
                temp_df.columns = (
                    temp_df.columns
                    .str.strip() # Quitar espacios a los lados
                    .str.lower() # Minúsculas
                    .str.replace(' ', '_') # Espacios por guiones bajos
                    .str.replace(r'[^\w\s]', '', regex=True) # Quitar caracteres especiales
                )

            # 2. Eliminar Duplicados
            if self.chk_dups.get():
                temp_df = temp_df.drop_duplicates()

            # 3. Manejar Nulos
            action = self.null_action.get()
            if action == "fill_zero":
                # Separa numéricos de no numéricos
                num_cols = temp_df.select_dtypes(include=[np.number]).columns
                obj_cols = temp_df.select_dtypes(exclude=[np.number]).columns
                temp_df[num_cols] = temp_df[num_cols].fillna(0)
                temp_df[obj_cols] = temp_df[obj_cols].fillna("Sin Datos")
            elif action == "drop":
                temp_df = temp_df.dropna()

            # 4. Convertir Fechas Automáticamente
            if self.chk_dates.get():
                for col in temp_df.columns:
                    if temp_df[col].dtype == 'object': # Si es texto
                        try:
                            # Intenta convertir, si no puede, lo ignora (errors='ignore')
                            converted = pd.to_datetime(temp_df[col], errors='coerce')
                            # Si más del 50% no es nulo después de convertir, asumimos que sí era una fecha
                            if converted.notna().sum() > (len(converted) * 0.5):
                                temp_df[col] = converted
                        except:
                            pass

            self.df_clean = temp_df
            
            # Mostrar resumen de cambios
            filas_orig = self.df.shape[0]
            filas_nuevas = self.df_clean.shape[0]
            msg = f"Limpieza completada.\n\nFilas antes: {filas_orig}\nFilas ahora: {filas_nuevas}"
            if filas_orig != filas_nuevas:
                msg += f" (Se eliminaron {filas_orig - filas_nuevas} filas)"
            
            messagebox.showinfo("Éxito", msg)
            self.update_preview(self.df_clean)
            self.notebook.select(self.tab_export)

        except Exception as e:
            messagebox.showerror("Error en Limpieza", f"Ocurrió un error:\n{str(e)}")

    def build_export_tab(self):
        frame = ttk.LabelFrame(self.tab_export, text="Exportar Datos Listos para Power BI", padding=15)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Label(frame, text="Guarda tu base de datos limpia para importarla en Power BI:").pack(anchor="w", pady=(0, 10))
        
        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill="x", pady=5)
        
        ttk.Button(btn_frame, text="💾 Guardar como CSV Limpio", command=lambda: self.export_data('csv')).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="💾 Guardar como Excel Limpio", command=lambda: self.export_data('xlsx')).pack(side="left", padx=5)

        ttk.Separator(frame, orient="horizontal").pack(fill="x", pady=20)

        # UTILIDAD EXTRA PARA POWER BI: La Tabla Calendario
        ttk.Label(frame, text="⭐️ Herramienta Extra: Generar Tabla Calendario (Dim_Date)", font=("", 10, "bold")).pack(anchor="w")
        ttk.Label(frame, text="En Power BI siempre necesitas una tabla de fechas. Esta opción crea una tabla\ncon Días, Meses, Años basándose en las fechas de tus datos actuales.", justify="left").pack(anchor="w", pady=5)
        
        ttk.Button(frame, text="📅 Generar y Guardar Dim_Calendario.csv", command=self.generate_date_table).pack(anchor="w", pady=5)

    def export_data(self, format_type):
        if self.df_clean is None:
            messagebox.showwarning("Atención", "No hay datos para exportar. Carga un archivo primero.")
            return

        def_ext = f".{format_type}"
        filepath = filedialog.asksaveasfilename(
            title="Guardar Datos Limpios",
            defaultextension=def_ext,
            initialfile=f"Limpio_{self.file_name.split('.')[0]}{def_ext}",
            filetypes=[(f"Archivo {format_type.upper()}", f"*{def_ext}")]
        )

        if not filepath: return

        try:
            if format_type == 'csv':
                # utf-8-sig es excelente para que Excel y PowerBI lean bien los acentos
                self.df_clean.to_csv(filepath, index=False, encoding='utf-8-sig') 
            elif format_type == 'xlsx':
                self.df_clean.to_excel(filepath, index=False)
                
            messagebox.showinfo("Éxito", f"Datos exportados correctamente a:\n{filepath}\n\n¡Listos para Power BI!")
        except Exception as e:
            messagebox.showerror("Error al Guardar", str(e))

    def generate_date_table(self):
        if self.df_clean is None:
            messagebox.showwarning("Atención", "Carga tus datos primero para detectar el rango de fechas.")
            return

        # Buscar columnas de fecha en el dataframe
        date_columns = self.df_clean.select_dtypes(include=['datetime64']).columns
        
        if len(date_columns) == 0:
            messagebox.showwarning("Atención", "No se detectaron columnas de fecha en tus datos limpios. Asegúrate de marcar la opción de convertir fechas en la Pestaña 2 y aplicarla.")
            return

        try:
            # Encontrar la fecha mínima y máxima entre todas las columnas de fecha
            min_date = self.df_clean[date_columns].min().min()
            max_date = self.df_clean[date_columns].max().max()

            # Crear rango de fechas (Desde el 1 de enero del año mínimo, hasta el 31 de dic del año máximo)
            start_date = pd.Timestamp(year=min_date.year, month=1, day=1)
            end_date = pd.Timestamp(year=max_date.year, month=12, day=31)

            # Generar dataframe de fechas
            date_range = pd.date_range(start=start_date, end=end_date)
            calendar_df = pd.DataFrame({'Fecha': date_range})

            # Añadir columnas útiles para DAX/Power BI
            calendar_df['Año'] = calendar_df['Fecha'].dt.year
            calendar_df['Mes_Num'] = calendar_df['Fecha'].dt.month
            calendar_df['Mes_Nombre'] = calendar_df['Fecha'].dt.month_name(locale='es_ES.utf8') if hasattr(calendar_df['Fecha'].dt.month_name, 'locale') else calendar_df['Fecha'].dt.month_name()
            calendar_df['Trimestre'] = 'Q' + calendar_df['Fecha'].dt.quarter.astype(str)
            calendar_df['Día_Num'] = calendar_df['Fecha'].dt.day
            calendar_df['Día_Semana'] = calendar_df['Fecha'].dt.day_name(locale='es_ES.utf8') if hasattr(calendar_df['Fecha'].dt.day_name, 'locale') else calendar_df['Fecha'].dt.day_name()
            calendar_df['Es_FinDeSemana'] = calendar_df['Fecha'].dt.dayofweek.isin([5, 6]).astype(int)

            filepath = filedialog.asksaveasfilename(
                title="Guardar Tabla Calendario",
                defaultextension=".csv",
                initialfile="Dim_Calendario.csv",
                filetypes=[("Archivo CSV", "*.csv")]
            )

            if filepath:
                calendar_df.to_csv(filepath, index=False, encoding='utf-8-sig')
                messagebox.showinfo("Éxito", f"Tabla Calendario generada desde {start_date.year} hasta {end_date.year}.\n\n¡Cárgala en Power BI y márcala como 'Tabla de Fechas'!")

        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error generando el calendario:\n{str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    if 'clam' in style.theme_names():
        style.theme_use('clam')
    app = PowerBIHelperApp(root)
    root.mainloop()