import tkinter as tk
from tkinter import messagebox

def add_task():
    task = entry.get()
    if task.strip() == "":
        messagebox.showwarning("Fehler", "Bitte gib eine Aufgabe ein.")
        return
    listbox.insert(tk.END, task)
    entry.delete(0, tk.END)

def delete_task():
    try:
        index = listbox.curselection()[0]
        listbox.delete(index)
    except:
        messagebox.showwarning("Fehler", "Bitte wähle eine Aufgabe aus.")

# Hauptfenster
root = tk.Tk()
root.title("Mini To-Do Liste")
root.geometry("300x400")

# Eingabefeld
entry = tk.Entry(root, font=("Arial", 12))
entry.pack(pady=10)

# Buttons
btn_add = tk.Button(root, text="Aufgabe hinzufügen", command=add_task)
btn_add.pack(pady=5)

btn_delete = tk.Button(root, text="Ausgewählte löschen", command=delete_task)
btn_delete.pack(pady=5)

# Listbox
listbox = tk.Listbox(root, font=("Arial", 12))
listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

root.mainloop()
