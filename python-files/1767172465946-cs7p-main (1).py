import tkinter as tk
from tkinter import ttk, messagebox
import ctypes
import time
import threading
import os
import subprocess

# --- API Windows pour les simulations ---
def set_cursor(x, y):
    ctypes.windll.user32.SetCursorPos(x, y)

def mouse_click():
    # simule un clic gauche (down = 2, up = 4)
    ctypes.windll.user32.mouse_event(2, 0, 0, 0, 0)
    time.sleep(0.05)
    ctypes.windll.user32.mouse_event(4, 0, 0, 0, 0)

def send_keys(text):
    # Utilisation de PowerShell pour envoyer des touches sans librairie externe
    # Cela permet de gérer les caractères spéciaux plus facilement
    powershell_cmd = f"Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait('{text}')"
    subprocess.run(["powershell", "-Command", powershell_cmd])

class MacroApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PyMacro Automator")
        self.root.geometry("500x600")
        self.root.resizable(False, False)
        
        # Style
        self.style = ttk.Style()
        self.style.configure("TButton", padding=5)
        
        self.actions = [] # Liste des dictionnaires d'actions
        
        self.setup_ui()

    def setup_ui(self):
        # Panneau principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Titre
        header = ttk.Label(main_frame, text="Configurateur de Macro", font=("Segoe UI", 14, "bold"))
        header.pack(pady=10)

        # Zone de liste
        list_frame = ttk.LabelFrame(main_frame, text="Séquence d'actions")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.tree = ttk.Treeview(list_frame, columns=("Action", "Détails"), show="headings", height=8)
        self.tree.heading("Action", text="Type d'action")
        self.tree.heading("Détails", text="Paramètres")
        self.tree.column("Action", width=120)
        self.tree.column("Détails", width=250)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Boutons d'ajout d'actions
        btn_frame = ttk.LabelFrame(main_frame, text="Ajouter une étape")
        btn_frame.pack(fill=tk.X, pady=10)

        grid_pad = {'padx': 5, 'pady': 5}
        ttk.Button(btn_frame, text="📍 Clic Souris", command=self.add_click_action).grid(row=0, column=0, **grid_pad)
        ttk.Button(btn_frame, text="⌨️ Taper Texte", command=self.add_text_action).grid(row=0, column=1, **grid_pad)
        ttk.Button(btn_frame, text="⏳ Attendre", command=self.add_wait_action).grid(row=1, column=0, **grid_pad)
        ttk.Button(btn_frame, text="🚀 Ouvrir App/Lien", command=self.add_launch_action).grid(row=1, column=1, **grid_pad)

        # Contrôles globaux
        ctrl_frame = ttk.Frame(main_frame)
        ctrl_frame.pack(fill=tk.X, pady=10)

        self.run_btn = tk.Button(ctrl_frame, text="▶ DÉMARRER LA MACRO", bg="#2ecc71", fg="white", 
                                font=("Segoe UI", 10, "bold"), command=self.start_macro_thread)
        self.run_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        ttk.Button(ctrl_frame, text="🗑 Vider", command=self.clear_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(ctrl_frame, text="❌ Supprimer", command=self.delete_selected).pack(side=tk.LEFT, padx=5)

        # Barre d'état
        self.status = ttk.Label(main_frame, text="Prêt", relief=tk.SUNKEN, anchor=tk.W)
        self.status.pack(fill=tk.X, side=tk.BOTTOM, pady=5)

    def add_click_action(self):
        # Fenêtre pour capturer les coordonnées
        capture_win = tk.Toplevel(self.root)
        capture_win.title("Capture de position")
        capture_win.geometry("300x150")
        
        label = ttk.Label(capture_win, text="Placez votre souris sur la cible.\nCapture automatique dans 5 secondes...", justify=tk.CENTER)
        label.pack(expand=True)
        
        def count_down(seconds):
            if seconds > 0:
                label.config(text=f"Placez votre souris...\nCapture dans {seconds}s")
                capture_win.after(1000, lambda: count_down(seconds-1))
            else:
                # Capture position
                class POINT(ctypes.Structure):
                    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
                pt = POINT()
                ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
                
                self.actions.append({"type": "click", "x": pt.x, "y": pt.y})
                self.tree.insert("", tk.END, values=("Clic Souris", f"X: {pt.x}, Y: {pt.y}"))
                capture_win.destroy()
        
        count_down(5)

    def add_text_action(self):
        text = self.simple_prompt("Saisie clavier", "Quel texte faut-il taper ?")
        if text:
            self.actions.append({"type": "text", "value": text})
            self.tree.insert("", tk.END, values=("Saisie Texte", text))

    def add_wait_action(self):
        sec = self.simple_prompt("Pause", "Combien de secondes d'attente ?")
        if sec:
            try:
                val = float(sec)
                self.actions.append({"type": "wait", "value": val})
                self.tree.insert("", tk.END, values=("Pause", f"{val} secondes"))
            except ValueError:
                messagebox.showerror("Erreur", "Veuillez entrer un nombre.")

    def add_launch_action(self):
        path = self.simple_prompt("Lancement", "Chemin de l'app ou URL (ex: notepad ou google.com)")
        if path:
            self.actions.append({"type": "launch", "value": path})
            self.tree.insert("", tk.END, values=("Lancement", path))

    def simple_prompt(self, title, msg):
        # Une petite boîte de dialogue rapide
        prompt = tk.Toplevel(self.root)
        prompt.title(title)
        prompt.geometry("300x120")
        ttk.Label(prompt, text=msg).pack(pady=5)
        entry = ttk.Entry(prompt, width=30)
        entry.pack(pady=5)
        entry.focus_set()
        
        res = {"value": None}
        def submit():
            res["value"] = entry.get()
            prompt.destroy()
        
        ttk.Button(prompt, text="Ajouter", command=submit).pack(pady=5)
        self.root.wait_window(prompt)
        return res["value"]

    def delete_selected(self):
        selected_item = self.tree.selection()
        if selected_item:
            for item in selected_item:
                index = self.tree.index(item)
                self.tree.delete(item)
                self.actions.pop(index)

    def clear_all(self):
        self.actions = []
        for item in self.tree.get_children():
            self.tree.delete(item)

    def start_macro_thread(self):
        if not self.actions:
            messagebox.showwarning("Attention", "La liste est vide !")
            return
        
        self.run_btn.config(state=tk.DISABLED, text="⏳ EXÉCUTION...")
        threading.Thread(target=self.execute_macro, daemon=True).start()

    def execute_macro(self):
        self.status.config(text="Démarrage dans 3 secondes...")
        time.sleep(3)
        
        try:
            for i, action in enumerate(self.actions):
                self.status.config(text=f"Action {i+1}/{len(self.actions)} en cours...")
                
                if action["type"] == "click":
                    set_cursor(action["x"], action["y"])
                    time.sleep(0.1)
                    mouse_click()
                elif action["type"] == "text":
                    send_keys(action["value"])
                elif action["type"] == "wait":
                    time.sleep(action["value"])
                elif action["type"] == "launch":
                    os.startfile(action["value"])
                
                time.sleep(0.5) # Petit délai de sécurité entre chaque action
                
            self.status.config(text="Macro terminée avec succès.")
            messagebox.showinfo("Succès", "L'automatisation est terminée.")
        except Exception as e:
            messagebox.showerror("Erreur macro", str(e))
        finally:
            self.run_btn.config(state=tk.NORMAL, text="▶ DÉMARRER LA MACRO")

if __name__ == "__main__":
    root = tk.Tk()
    app = MacroApp(root)
    root.mainloop()