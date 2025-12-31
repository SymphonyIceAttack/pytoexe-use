import tkinter as tk
from tkinter import scrolledtext
import re

# --- LE DICTIONNAIRE ÉCLAIR COMPLET (PYTHON EN FRANÇAIS) ---
TRADUCTION = {
    # Structure et Contrôle
    'fonction': 'def', 'si': 'if', 'sinon_si': 'elif', 'sinon': 'else',
    'pour': 'for', 'tant_que': 'while', 'dans': 'in', 'renvoyer': 'return',
    'arreter': 'break', 'continuer': 'continue', 'passer': 'pass', 
    'produire': 'yield', 'classe': 'class', 'avec': 'with', 'en_tant_que': 'as',
    'essayer': 'try', 'intercepter': 'except', 'finalement': 'finally',
    'lever': 'raise', 'affirmer': 'assert', 'global': 'global', 'non_local': 'nonlocal',
    'supprimer': 'del', 'importer': 'import', 'depuis': 'from', 'lambda': 'lambda',

    # Logique et Valeurs
    'et': 'and', 'ou': 'or', 'pas': 'not', 'est': 'is',
    'Vrai': 'True', 'Faux': 'False', 'Rien': 'None',

    # Fonctions Natives (Built-ins)
    'afficher': 'print', 'saisir': 'input', 'longueur': 'len',
    'entier': 'int', 'decimal': 'float', 'texte': 'str', 'liste': 'list',
    'dictionnaire': 'dict', 'ensemble': 'set', 'booleen': 'bool',
    'intervalle': 'range', 'trié': 'sorted', 'maximum': 'max', 
    'minimum': 'min', 'somme': 'sum', 'type_de': 'type', 'énumérer': 'enumerate',
    'aide': 'help', 'ouvrir': 'open'
}

# Suggestions automatiques de structures
SUGGESTIONS_SUITE = {
    'fonction': ' nom_fonction(parametres):',
    'si': ' condition:',
    'pour': ' i dans intervalle(10):',
    'tant_que': ' condition:',
    'essayer': ':',
    'classe': ' MaClasse:',
    'afficher': '("Bonjour")',
    'sinon': ':',
    'sinon_si': ' condition:'
}

class EclairUltraIDE:
    def __init__(self, root):
        self.root = root
        self.root.title("Éclair Ultra IDE - Le Python Complet en Français")
        self.root.geometry("1100x850")
        self.root.configure(bg="#1e1e1e")

        # --- Interface ---
        self.zone_texte = scrolledtext.ScrolledText(root, height=25, font=("Consolas", 12), 
                                                   bg="#1e1e1e", fg="#d4d4d4", insertbackground="white", undo=True)
        self.zone_texte.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        self.zone_sortie = scrolledtext.ScrolledText(root, height=12, font=("Consolas", 11), 
                                                    bg="#000000", fg="#80ff80", state=tk.DISABLED)
        self.zone_sortie.pack(padx=10, pady=5, fill=tk.BOTH)

        self.btn_run = tk.Button(root, text="▶ EXÉCUTER LE CODE", command=self.executer_code, 
                                 bg="#007acc", fg="white", font=("Arial", 10, "bold"), padx=20)
        self.btn_run.pack(pady=10)

        # --- Événements ---
        self.suggestion_box = None
        self.zone_texte.bind("<KeyRelease>", self.sur_touche_relachee)
        self.zone_texte.bind("<KeyPress-Tab>", self.utiliser_suggestion_clavier)
        self.zone_texte.bind("<KeyPress-Return>", self.auto_indentation)

        # Tags de couleur
        self.zone_texte.tag_config("keyword", fg="#569cd6")
        self.zone_texte.tag_config("string", fg="#ce9178")
        self.zone_texte.tag_config("comment", fg="#6a9955")

    def lister_commandes(self):
        """La fonction qui sera appelée dans l'IDE pour afficher l'aide"""
        print("\n--- 📜 TOUTES LES COMMANDES ÉCLAIR RÉPERTORIÉES ---")
        colonnes = 3
        mots = sorted(TRADUCTION.keys())
        for i in range(0, len(mots), colonnes):
            ligne = mots[i:i+colonnes]
            print("  • " + "  • ".join(f"{m:<15}" for m in ligne))
        print("---------------------------------------------------\n")

    def auto_indentation(self, event):
        ligne_actuelle = self.zone_texte.index(tk.INSERT).split('.')[0]
        contenu_ligne = self.zone_texte.get(f"{ligne_actuelle}.0", tk.INSERT)
        if contenu_ligne.strip().endswith(':'):
            indent = re.match(r"^\s*", contenu_ligne).group(0)
            self.zone_texte.insert(tk.INSERT, "\n" + indent + "    ")
            return "break"

    def sur_touche_relachee(self, event):
        self.colorer_syntaxe()
        if event.keysym in ("Up", "Down", "Escape", "Return"): return
        
        curseur = self.zone_texte.index(tk.INSERT)
        debut_ligne = curseur.split('.')[0] + ".0"
        texte_avant = self.zone_texte.get(debut_ligne, curseur)

        m_suite = re.search(r"(\w+)\s$", texte_avant)
        m_auto = re.search(r"(\w+)$", texte_avant)

        if m_suite and m_suite.group(1) in SUGGESTIONS_SUITE:
            self.afficher_suggestions([SUGGESTIONS_SUITE[m_suite.group(1)]])
        elif m_auto:
            props = [m for m in TRADUCTION.keys() if m.startswith(m_auto.group(1)) and m != m_auto.group(1)]
            if props: self.afficher_suggestions(props)
            else: self.detruire_suggestions()
        else:
            self.detruire_suggestions()

    def afficher_suggestions(self, liste):
        if not self.suggestion_box:
            self.suggestion_box = tk.Listbox(self.root, font=("Consolas", 10), bg="#333333", fg="#ffffff", borderwidth=0)
            self.suggestion_box.bind("<<ListboxSelect>>", self.utiliser_suggestion_souris)
        self.suggestion_box.delete(0, tk.END)
        for s in liste: self.suggestion_box.insert(tk.END, s)
        pos = self.zone_texte.bbox(tk.INSERT)
        if pos: self.suggestion_box.place(x=pos[0] + 20, y=pos[1] + 50)

    def detruire_suggestions(self):
        if self.suggestion_box:
            self.suggestion_box.destroy()
            self.suggestion_box = None

    def utiliser_suggestion_souris(self, event):
        if self.suggestion_box:
            sel = self.suggestion_box.curselection()
            if sel:
                self.inserer_choix(self.suggestion_box.get(sel[0]))
                self.zone_texte.focus_set()

    def utiliser_suggestion_clavier(self, event):
        if self.suggestion_box:
            self.inserer_choix(self.suggestion_box.get(tk.ACTIVE))
            return "break"

    def inserer_choix(self, choix):
        if choix.startswith(" "): self.zone_texte.insert(tk.INSERT, choix.strip())
        else:
            self.zone_texte.delete("insert -1c wordstart", tk.INSERT)
            self.zone_texte.insert(tk.INSERT, choix)
        self.detruire_suggestions()

    def colorer_syntaxe(self):
        content = self.zone_texte.get("1.0", tk.END)
        for tag in ["keyword", "string", "comment"]: self.zone_texte.tag_remove(tag, "1.0", tk.END)
        for mot in TRADUCTION.keys():
            for m in re.finditer(rf'\b{mot}\b', content):
                self.zone_texte.tag_add("keyword", f"1.0 + {m.start()} chars", f"1.0 + {m.end()} chars")
        for m in re.finditer(r'#.*', content):
            self.zone_texte.tag_add("comment", f"1.0 + {m.start()} chars", f"1.0 + {m.end()} chars")

    def executer_code(self):
        code_eclair = self.zone_texte.get("1.0", tk.END)
        # Ajout de la commande lister_commandes()
        code_eclair = code_eclair.replace("lister_commandes()", "lister_commandes_eclair()")
        
        code_python = code_eclair
        # Trier par longueur décroissante pour éviter de remplacer 'si' dans 'sinon'
        for fr in sorted(TRADUCTION.keys(), key=len, reverse=True):
            code_python = re.sub(rf'\b{fr}\b', TRADUCTION[fr], code_python)

        self.zone_sortie.config(state=tk.NORMAL)
        self.zone_sortie.delete("1.0", tk.END)
        import sys, io
        f = io.StringIO()
        sys.stdout = f
        try:
            # Injection de la fonction d'aide dans l'environnement d'exécution
            exec(code_python, {"lister_commandes_eclair": self.lister_commandes, "__builtins__": __builtins__})
            self.zone_sortie.insert(tk.END, f.getvalue())
        except Exception as e:
            self.zone_sortie.insert(tk.END, f"ERREUR : {str(e)}")
        sys.stdout = sys.__stdout__
        self.zone_sortie.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = EclairUltraIDE(root)
    # Code de bienvenue
    app.zone_texte.insert("1.0", "# Tape lister_commandes() pour voir tout le dictionnaire\nlister_commandes()\n\nfonction saluer():\n    afficher('Bienvenue dans Éclair Ultra !')\n\nsaluer()")
    root.mainloop()