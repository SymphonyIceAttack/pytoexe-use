import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
from datetime import datetime
import uuid
import random

DATA_FILE = "students.json"

# ===================== SAUVEGARDE =====================

def save(students):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(students, f, indent=4, ensure_ascii=False)

def load():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# ===================== LOGIN =====================

class Login:
    def __init__(self, root):
        self.root = root
        root.title("Connexion")
        root.geometry("300x180")

        tk.Label(root, text="Identifiant").pack()
        self.user = tk.Entry(root)
        self.user.pack()

        tk.Label(root, text="Mot de passe").pack()
        self.pwd = tk.Entry(root, show="*")
        self.pwd.pack()

        tk.Button(root, text="Connexion", command=self.check).pack(pady=10)

    def check(self):
        if self.user.get() == "Khalis" and self.pwd.get() == "admin123":
            self.root.destroy()
            App()
        else:
            messagebox.showerror("Erreur", "Identifiants incorrects")

# ===================== APPLICATION =====================

class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Gestion scolaire")
        self.root.geometry("900x500")

        self.students = load()

        self.create_ui()
        self.refresh()

        self.root.mainloop()

    # ---------------- UI ----------------

    def create_ui(self):
        top = tk.Frame(self.root)
        top.pack(fill="x")

        tk.Button(top, text="➕ Ajouter", command=self.add).pack(side="left")
        tk.Button(top, text="🗑️ Supprimer", command=self.delete).pack(side="left")
        tk.Button(top, text="🪪 Badger", command=self.badge).pack(side="left")
        tk.Button(top, text="⏰ Retard", command=self.add_delay).pack(side="left")
        tk.Button(top, text="🎓 Gérer un élève", command=self.manage).pack(side="left")
        tk.Button(top, text="🧪 Démo", command=self.demo).pack(side="left")

        self.tree = ttk.Treeview(self.root, columns=("prenom", "statut", "retards"), show="headings")
        self.tree.heading("prenom", text="Prénom")
        self.tree.heading("statut", text="Statut")
        self.tree.heading("retards", text="Retards")
        self.tree.pack(fill="both", expand=True)

        self.tree.bind("<Return>", lambda e: self.manage())

    # ---------------- UTIL ----------------

    def get_selected(self):
        sid = self.tree.focus()
        if not sid:
            messagebox.showwarning("Attention", "Sélectionne un élève")
            return None
        return sid

    # ---------------- ÉLÈVES ----------------

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for sid, s in self.students.items():
            self.tree.insert("", "end", iid=sid, values=(
                s["prenom"],
                s["statut"],
                len(s["retards"])
            ))

    def add(self):
        nom = simpledialog.askstring("Nom", "Nom")
        prenom = simpledialog.askstring("Prénom", "Prénom")
        if nom and prenom:
            sid = str(uuid.uuid4())
            self.students[sid] = {
                "nom": nom,
                "prenom": prenom,
                "statut": "absent",
                "historique": [],
                "retards": []
            }
            save(self.students)
            self.refresh()

    def delete(self):
        sid = self.get_selected()
        if not sid:
            return
        if messagebox.askyesno("Confirmation", "Supprimer cet élève ?"):
            del self.students[sid]
            save(self.students)
            self.refresh()

    # ---------------- BADGE ----------------

    def badge(self):
        sid = self.get_selected()
        if not sid:
            return
        self.students[sid]["statut"] = "présent"
        self.students[sid]["historique"].append({
            "type": "présence",
            "date": str(datetime.now())
        })
        save(self.students)
        self.refresh()

    # ---------------- RETARDS ----------------

    def add_delay(self):
        sid = self.get_selected()
        if not sid:
            return
        justified = messagebox.askyesno("Retard", "Retard justifié ?")
        self.students[sid]["retards"].append({
            "date": str(datetime.now()),
            "justifié": justified
        })
        save(self.students)
        self.refresh()

    # ---------------- GESTION ÉLÈVE ----------------

    def manage(self):
        sid = self.get_selected()
        if not sid:
            return

        s = self.students[sid]

        win = tk.Toplevel(self.root)
        win.title(f"{s['nom']} {s['prenom']}")
        win.geometry("400x400")

        lbl = tk.Label(win, text=f"Statut : {s['statut']}", font=("Arial", 12))
        lbl.pack()

        def set_statut(value):
            s["statut"] = value
            save(self.students)
            lbl.config(text=f"Statut : {value}")
            self.refresh()

        tk.Button(win, text="Présent", command=lambda: set_statut("présent")).pack()
        tk.Button(win, text="Absent", command=lambda: set_statut("absent")).pack()

        tk.Label(win, text="Historique").pack()
        txt = tk.Text(win)
        txt.pack(fill="both", expand=True)

        for h in s["historique"]:
            txt.insert("end", f"{h['type']} - {h['date']}\n")
        for r in s["retards"]:
            txt.insert("end", f"Retard ({'justifié' if r['justifié'] else 'non'}) - {r['date']}\n")

    # ---------------- DÉMO ----------------

    def demo(self):
        for _ in range(5):
            sid = str(uuid.uuid4())
            self.students[sid] = {
                "nom": random.choice(["Martin", "Durand", "Petit"]),
                "prenom": random.choice(["Lucas", "Emma", "Noah"]),
                "statut": "absent",
                "historique": [],
                "retards": []
            }
        save(self.students)
        self.refresh()

# ===================== LANCEMENT =====================

if __name__ == "__main__":
    root = tk.Tk()
    Login(root)
    root.mainloop()
