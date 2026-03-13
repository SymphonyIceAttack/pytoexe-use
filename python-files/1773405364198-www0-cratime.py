 import tkinter as tk
from tkinter import filedialog, messagebox
from docx import Document
import re
import os

# Funcție pentru eliminarea cratimelor greșite
def elimina_cratime(text):
    # Înlocuiește cratimele dintre litere care nu ar trebui să fie
    # Unicode cratime: \u2010, \u2011 și cratima simplă "-"
    text_corectat = re.sub(r'(\w)[\u2010\u2011-](\w)', r'\1\2', text)
    return text_corectat

# Funcție pentru procesarea fișierului
def proceseaza_fisier(path):
    try:
        document = Document(path)
        for paragraph in document.paragraphs:
            paragraph.text = elimina_cratime(paragraph.text)
        # Crează nume pentru fișierul nou
        folder, fisier = os.path.split(path)
        nume_nou = os.path.join(folder, "corectat_" + fisier)
        document.save(nume_nou)
        messagebox.showinfo("Succes!", f"Fișierul a fost corectat și salvat ca:\n{nume_nou}")
    except Exception as e:
        messagebox.showerror("Eroare", f"A apărut o problemă:\n{e}")

# Funcție pentru butonul "Selectează fișier"
def selecteaza_fisier():
    path = filedialog.askopenfilename(
        title="Selectează fișier Word",
        filetypes=[("Word Documents", "*.docx")]
    )
    if path:
        proceseaza_fisier(path)

# --- GUI ---
root = tk.Tk()
root.title("Eliminare cratime greșite")
root.geometry("400x150")
root.resizable(False, False)

label = tk.Label(root, text="Apasă butonul pentru a selecta fișierul Word:", font=("Arial", 12))
label.pack(pady=20)

btn_select = tk.Button(root, text="Selectează fișier", font=("Arial", 12), command=selecteaza_fisier)
btn_select.pack()

root.mainloop()
