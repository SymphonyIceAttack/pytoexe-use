
import tkinter as tk
from tkinter import simpledialog, messagebox
import json
import os

FILE = "grupo.json"
CLAVE = "1234"

# cargar datos
def cargar():
    if os.path.exists(FILE):
        with open(FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def guardar():
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(grupos, f, indent=2, ensure_ascii=False)

def actualizar_grupos():
    lista_grupos.delete(0, tk.END)
    for g in grupos:
        lista_grupos.insert(tk.END, f"{g} ({len(grupos[g])})")

def mostrar_nombres(evt=None):
    lista_nombres.delete(0, tk.END)
    seleccion = lista_grupos.curselection()
    if not seleccion:
        return
    g = list(grupos.keys())[seleccion[0]]
    for i,n in enumerate(grupos[g],1):
        lista_nombres.insert(tk.END,f"{i} {n}")

def copiar_nombre(evt):
    seleccion = lista_nombres.curselection()
    if not seleccion: return
    texto = lista_nombres.get(seleccion)
    nombre = texto.split(" ",1)[1]

    root.clipboard_clear()
    root.clipboard_append(nombre)

    if seleccion in marcados:
        lista_nombres.itemconfig(seleccion,{'bg':'white'})
        marcados.remove(seleccion)
    else:
        lista_nombres.itemconfig(seleccion,{'bg':'lightgreen'})
        marcados.add(seleccion)

def desmarcar():
    for i in range(lista_nombres.size()):
        lista_nombres.itemconfig(i,{'bg':'white'})
    marcados.clear()

def añadir_nombre():
    seleccion = lista_grupos.curselection()
    if not seleccion: return
    g = list(grupos.keys())[seleccion[0]]
    nombre = simpledialog.askstring("Añadir","Nombre:")
    if nombre:
        grupos[g].append(nombre)
        guardar()
        mostrar_nombres()
        actualizar_grupos()

def borrar_nombre():
    seleccion_g = lista_grupos.curselection()
    seleccion_n = lista_nombres.curselection()

    if not seleccion_g or not seleccion_n:
        return

    clave = simpledialog.askstring("Clave","Introduce clave:",show="*")
    if clave != CLAVE:
        messagebox.showerror("Error","Clave incorrecta")
        return

    g = list(grupos.keys())[seleccion_g[0]]
    i = seleccion_n[0]

    grupos[g].pop(i)
    guardar()
    mostrar_nombres()
    actualizar_grupos()

def subir():
    gsel = lista_grupos.curselection()
    nsel = lista_nombres.curselection()
    if not gsel or not nsel: return

    g = list(grupos.keys())[gsel[0]]
    i = nsel[0]

    if i>0:
        grupos[g][i],grupos[g][i-1] = grupos[g][i-1],grupos[g][i]
        guardar()
        mostrar_nombres()
        lista_nombres.select_set(i-1)

def bajar():
    gsel = lista_grupos.curselection()
    nsel = lista_nombres.curselection()
    if not gsel or not nsel: return

    g = list(grupos.keys())[gsel[0]]
    i = nsel[0]

    if i < len(grupos[g])-1:
        grupos[g][i],grupos[g][i+1] = grupos[g][i+1],grupos[g][i]
        guardar()
        mostrar_nombres()
        lista_nombres.select_set(i+1)

def copiar_grupo():
    gsel = lista_grupos.curselection()
    if not gsel: return
    g = list(grupos.keys())[gsel[0]]

    texto="\n".join(grupos[g])
    root.clipboard_clear()
    root.clipboard_append(texto)

def reagrupar():
    gsel = lista_grupos.curselection()
    if not gsel: return
    g = list(grupos.keys())[gsel[0]]

    grupos[g] = [n for n in grupos[g] if n.strip()!=""]
    guardar()
    mostrar_nombres()
    actualizar_grupos()

def nuevo_grupo():
    nombre = simpledialog.askstring("Nuevo grupo","Nombre grupo:")
    if nombre:
        grupos[nombre]=[]
        guardar()
        actualizar_grupos()

def borrar_grupo():
    gsel = lista_grupos.curselection()
    if not gsel: return

    clave = simpledialog.askstring("Clave","Introduce clave:",show="*")
    if clave != CLAVE:
        messagebox.showerror("Error","Clave incorrecta")
        return

    g = list(grupos.keys())[gsel[0]]
    del grupos[g]
    guardar()
    actualizar_grupos()
    lista_nombres.delete(0,tk.END)

def toggle_top():
    root.attributes("-topmost",var_top.get())

# GUI
root=tk.Tk()
root.title("GestorGrupos PRO")

grupos=cargar()
marcados=set()

frame=tk.Frame(root)
frame.pack(padx=10,pady=10)

lista_grupos=tk.Listbox(frame,width=25)
lista_grupos.grid(row=0,column=0,rowspan=10)
lista_grupos.bind("<<ListboxSelect>>",mostrar_nombres)

lista_nombres=tk.Listbox(frame,width=40)
lista_nombres.grid(row=0,column=1,rowspan=10)
lista_nombres.bind("<ButtonRelease-1>",copiar_nombre)

tk.Button(frame,text="➕ Añadir",command=añadir_nombre).grid(row=0,column=2)
tk.Button(frame,text="🗑 Borrar",command=borrar_nombre).grid(row=1,column=2)
tk.Button(frame,text="⬆ Subir",command=subir).grid(row=2,column=2)
tk.Button(frame,text="⬇ Bajar",command=bajar).grid(row=3,column=2)
tk.Button(frame,text="📋 Copiar grupo",command=copiar_grupo).grid(row=4,column=2)
tk.Button(frame,text="🔁 Reagrupar",command=reagrupar).grid(row=5,column=2)

tk.Button(frame,text="➕ Nuevo grupo",command=nuevo_grupo).grid(row=6,column=2)
tk.Button(frame,text="🗑 Borrar grupo",command=borrar_grupo).grid(row=7,column=2)

tk.Button(frame,text="🔄 Desmarcar todo",command=desmarcar).grid(row=8,column=2)

var_top=tk.BooleanVar()
tk.Checkbutton(frame,text="Siempre encima",variable=var_top,command=toggle_top).grid(row=9,column=2)

actualizar_grupos()

root.mainloop()