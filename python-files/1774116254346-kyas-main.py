import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from tkinter import ttk
from dbfread import DBF
import os

field_config = []

def select_sql_folder():
    folder_path = filedialog.askdirectory()
    if folder_path:
        sql_folder_entry.delete(0, tk.END)
        sql_folder_entry.insert(0, folder_path)

def select_sql_file():
    pass  # Ya no se usa, ahora carpeta + nombre separados


def populate_field_tree(fields):
    for i in field_tree.get_children():
        field_tree.delete(i)
    for field in fields:
        field_tree.insert("", "end", values=(field['name'], field['type'], "Sí" if field['include'] else "No"))


def select_dbf_file():
    file_path = filedialog.askopenfilename(filetypes=[("DBF files", "*.dbf")])
    if file_path:
        dbf_entry.delete(0, tk.END)
        dbf_entry.insert(0, file_path)

        try:
            table = DBF(file_path, encoding='latin-1')
            global field_config
            field_config = []
            for field in table.fields:
                field_config.append({'name': field.name, 'type': 'TEXT', 'include': True})
            populate_field_tree(field_config)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el DBF: {e}")


def toggle_include_field():
    selected = field_tree.selection()
    if not selected:
        return
    item = selected[0]
    name, tipo, include = field_tree.item(item, 'values')
    for f in field_config:
        if f['name'] == name:
            f['include'] = not f['include']
            break
    populate_field_tree(field_config)


def set_type_field():
    selected = field_tree.selection()
    if not selected:
        return
    item = selected[0]
    name, tipo, include = field_tree.item(item, 'values')
    new_type = simpledialog.askstring("Tipo", f"Nuevo tipo para {name} (e.g. TEXT, INTEGER):", initialvalue=tipo)
    if new_type:
        for f in field_config:
            if f['name'] == name:
                f['type'] = new_type.strip().upper()
                break
        populate_field_tree(field_config)



def convert_dbf_to_sql():
    dbf_path = dbf_entry.get()
    sql_folder = sql_folder_entry.get()
    sql_name = sql_name_entry.get()
    
    if not dbf_path or not sql_folder or not sql_name:
        messagebox.showerror("Error", "Selecciona archivo DBF, carpeta SQL y nombre del archivo.")
        return
    
    sql_path = os.path.join(sql_folder, sql_name)
    if not sql_path.endswith('.sql'):
        sql_path += '.sql'
    
    if not field_config:
        messagebox.showerror("Error", "No hay campos cargados para convertir.")
        return
    
    try:
        table = DBF(dbf_path, encoding='latin-1')
        table_name = os.path.splitext(os.path.basename(dbf_path))[0]
        
        selected_fields = [f for f in field_config if f['include']]
        if not selected_fields:
            messagebox.showerror("Error", "Selecciona al menos un campo para insertar.")
            return

        with open(sql_path, 'w', encoding='latin-1') as f:
            # Crear tabla con tipos modificados
            fields_sql = [f"{f['name']} {f['type']}" for f in selected_fields]
            f.write(f"CREATE TABLE {table_name} (\n" + ",\n".join(fields_sql) + "\n);\n\n")
            
            # Insertar datos aplicando selección de campos
            for record in table:
                values = []
                for f in selected_fields:
                    value = record.get(f['name'])
                    if value is None:
                        values.append("NULL")
                    else:
                        escaped = str(value).replace("'", "''")
                        values.append(f"'{escaped}'")
                f.write(f"INSERT INTO {table_name} ({', '.join([f['name'] for f in selected_fields])}) VALUES ({', '.join(values)});\n")
            messagebox.showinfo("Éxito", f"Conversión completada. Archivo guardado en: {sql_path}")
    except Exception as e:
        messagebox.showerror("Error", f"Error durante la conversión: {str(e)}")

# Crear ventana principal
root = tk.Tk()
root.title("Conversor DBF a SQL")
root.resizable(True, True)

# Configurar expansión de filas y columnas
root.columnconfigure(1, weight=1)
root.rowconfigure(4, weight=1)

# Etiquetas y entradas
tk.Label(root, text="Archivo DBF:").grid(row=0, column=0, padx=10, pady=10)
dbf_entry = tk.Entry(root, width=50)
dbf_entry.grid(row=0, column=1, padx=10, pady=10)
tk.Button(root, text="Seleccionar", command=select_dbf_file).grid(row=0, column=2, padx=10, pady=10)

tk.Label(root, text="Carpeta SQL:").grid(row=1, column=0, padx=10, pady=10)
sql_folder_entry = tk.Entry(root, width=50)
sql_folder_entry.grid(row=1, column=1, padx=10, pady=10)
tk.Button(root, text="Seleccionar", command=select_sql_folder).grid(row=1, column=2, padx=10, pady=10)

tk.Label(root, text="Nombre archivo SQL:").grid(row=2, column=0, padx=10, pady=10)
sql_name_entry = tk.Entry(root, width=50)
sql_name_entry.grid(row=2, column=1, padx=10, pady=10)

# Botón convertir
convert_btn = tk.Button(root, text="Convertir", command=convert_dbf_to_sql)
convert_btn.grid(row=3, column=0, columnspan=3, pady=20)

# Configuración de Treeview para edición de campos
field_tree = ttk.Treeview(root, columns=("name", "type", "include"), show='headings', height=8)
field_tree.heading('name', text='Nombre de campo')
field_tree.heading('type', text='Tipo SQL')
field_tree.heading('include', text='Incluir')
field_tree.column('name', width=160)
field_tree.column('type', width=120)
field_tree.column('include', width=80)
field_tree.grid(row=4, column=0, columnspan=3, padx=10, pady=10, sticky='nsew')

# Botones de edición para selección de campo
edit_frame = tk.Frame(root)
edit_frame.grid(row=5, column=0, columnspan=3, pady=5)

tk.Button(edit_frame, text="Alternar Incluir", command=toggle_include_field).pack(side='left', padx=5)
tk.Button(edit_frame, text="Cambiar Tipo", command=set_type_field).pack(side='left', padx=5)

root.mainloop()


