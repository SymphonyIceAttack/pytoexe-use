import re
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from typing import Any, Dict, List, Tuple

class InterpreteurFrancais:
    """Interpréteur pour un langage de programmation en français"""
    
    def __init__(self):
        self.variables: Dict[str, Any] = {}
        self.fonctions: Dict[str, Dict[str, Any]] = {}
        self.sortie: List[str] = []
        
    def executer(self, code: str) -> str:
        """Exécute le code et retourne la sortie"""
        self.variables = {}
        self.fonctions = {}
        self.sortie = []
        
        lignes = [l.strip() for l in code.split('\n') if l.strip() and not l.strip().startswith('//')]
        i = 0
        
        try:
            while i < len(lignes):
                i = self.executer_ligne(lignes, i)
        except Exception as e:
            self.sortie.append(f"❌ Erreur ligne {i+1}: {str(e)}")
            return '\n'.join(self.sortie)
        
        return '\n'.join(self.sortie) if self.sortie else '✓ Programme exécuté avec succès'
    
    def executer_ligne(self, lignes: List[str], index: int) -> int:
        """Exécute une ligne et retourne l'index de la prochaine ligne"""
        ligne = lignes[index]
        
        if ligne.startswith('fonction '):
            return self.definir_fonction(lignes, index)
        elif ligne.startswith('variable ') or ligne.startswith('var '):
            self.definir_variable(ligne)
            return index + 1
        elif ligne.startswith('afficher('):
            self.afficher(ligne)
            return index + 1
        elif ligne.startswith('pour '):
            return self.executer_boucle(lignes, index)
        elif ligne.startswith('si '):
            return self.executer_condition(lignes, index)
        elif ligne.startswith('liste '):
            self.definir_liste(ligne)
            return index + 1
        elif '=' in ligne and '==' not in ligne:
            self.assigner_variable(ligne)
            return index + 1
        else:
            return index + 1
    
    def definir_fonction(self, lignes: List[str], index: int) -> int:
        """Définit une fonction"""
        match = re.match(r'fonction\s+(\w+)\s*\(([^)]*)\)', lignes[index])
        if not match:
            raise SyntaxError(f"Syntaxe de fonction invalide: {lignes[index]}")
        
        nom, params = match.groups()
        params_liste = [p.strip() for p in params.split(',')] if params else []
        
        # Trouver le corps de la fonction
        corps = []
        i = index + 1
        niveau_accolades = 1
        
        while i < len(lignes) and niveau_accolades > 0:
            ligne = lignes[i].strip()
            if ligne == '{':
                niveau_accolades += 1
            elif ligne == '}':
                niveau_accolades -= 1
                if niveau_accolades == 0:
                    break
            elif ligne not in ['{', '}']:
                corps.append(ligne)
            i += 1
        
        self.fonctions[nom] = {'params': params_liste, 'corps': corps}
        return i + 1
    
    def appeler_fonction(self, nom: str, args: List[Any]) -> Any:
        """Appelle une fonction"""
        if nom not in self.fonctions:
            raise NameError(f"Fonction '{nom}' non définie")
        
        fonction = self.fonctions[nom]
        vars_sauvegardees = self.variables.copy()
        
        # Assigner les paramètres
        for param, arg in zip(fonction['params'], args):
            self.variables[param] = arg
        
        # Exécuter le corps
        resultat = None
        for ligne in fonction['corps']:
            if ligne.startswith('retourner '):
                resultat = self.evaluer_expression(ligne[10:])
                break
            else:
                self.executer_ligne([ligne], 0)
        
        self.variables = vars_sauvegardees
        return resultat
    
    def definir_variable(self, ligne: str):
        """Définit une variable"""
        match = re.match(r'(?:variable|var)\s+(\w+)\s*=\s*(.+)', ligne)
        if not match:
            raise SyntaxError(f"Syntaxe de variable invalide: {ligne}")
        
        nom, expr = match.groups()
        self.variables[nom] = self.evaluer_expression(expr)
    
    def assigner_variable(self, ligne: str):
        """Assigne une valeur à une variable existante"""
        match = re.match(r'(\w+)\s*=\s*(.+)', ligne)
        if not match:
            raise SyntaxError(f"Syntaxe d'affectation invalide: {ligne}")
        
        nom, expr = match.groups()
        self.variables[nom] = self.evaluer_expression(expr)
    
    def definir_liste(self, ligne: str):
        """Définit une liste"""
        match = re.match(r'liste\s+(\w+)\s*=\s*\[([^\]]*)\]', ligne)
        if not match:
            raise SyntaxError(f"Syntaxe de liste invalide: {ligne}")
        
        nom, items = match.groups()
        liste = [self.evaluer_expression(item.strip()) for item in items.split(',')] if items.strip() else []
        self.variables[nom] = liste
    
    def afficher(self, ligne: str):
        """Affiche une valeur"""
        match = re.match(r'afficher\((.+)\)', ligne)
        if not match:
            raise SyntaxError(f"Syntaxe d'affichage invalide: {ligne}")
        
        valeur = self.evaluer_expression(match.group(1))
        self.sortie.append(str(valeur))
    
    def executer_boucle(self, lignes: List[str], index: int) -> int:
        """Exécute une boucle"""
        ligne = lignes[index]
        
        # Boucle numérique: pour i de 1 à 10
        if ' de ' in ligne and ' à ' in ligne:
            match = re.match(r'pour\s+(\w+)\s+de\s+(.+?)\s+à\s+(.+?)\s*\{?', ligne)
            if not match:
                raise SyntaxError(f"Syntaxe de boucle invalide: {ligne}")
            
            var_nom, debut_expr, fin_expr = match.groups()
            debut = int(self.evaluer_expression(debut_expr))
            fin = int(self.evaluer_expression(fin_expr))
            
            corps, fin_index = self.extraire_bloc(lignes, index)
            
            for i in range(debut, fin + 1):
                self.variables[var_nom] = i
                for ligne_corps in corps:
                    self.executer_ligne([ligne_corps], 0)
            
            return fin_index
        
        # Boucle sur liste: pour chaque element dans liste
        elif ' chaque ' in ligne and ' dans ' in ligne:
            match = re.match(r'pour\s+chaque\s+(\w+)\s+dans\s+(\w+)\s*\{?', ligne)
            if not match:
                raise SyntaxError(f"Syntaxe de boucle invalide: {ligne}")
            
            item_nom, liste_nom = match.groups()
            if liste_nom not in self.variables:
                raise NameError(f"Liste '{liste_nom}' non définie")
            
            liste = self.variables[liste_nom]
            if not isinstance(liste, list):
                raise TypeError(f"'{liste_nom}' n'est pas une liste")
            
            corps, fin_index = self.extraire_bloc(lignes, index)
            
            for item in liste:
                self.variables[item_nom] = item
                for ligne_corps in corps:
                    self.executer_ligne([ligne_corps], 0)
            
            return fin_index
        
        else:
            raise SyntaxError(f"Syntaxe de boucle non reconnue: {ligne}")
    
    def executer_condition(self, lignes: List[str], index: int) -> int:
        """Exécute une condition"""
        ligne = lignes[index]
        match = re.match(r'si\s+(.+?)\s*\{?', ligne)
        if not match:
            raise SyntaxError(f"Syntaxe de condition invalide: {ligne}")
        
        condition = self.evaluer_expression(match.group(1))
        corps, fin_index = self.extraire_bloc(lignes, index)
        
        if condition:
            for ligne_corps in corps:
                self.executer_ligne([ligne_corps], 0)
        
        return fin_index
    
    def extraire_bloc(self, lignes: List[str], index: int) -> Tuple[List[str], int]:
        """Extrait un bloc de code entre accolades"""
        corps = []
        i = index + 1
        niveau_accolades = 1
        
        while i < len(lignes) and niveau_accolades > 0:
            ligne = lignes[i].strip()
            if ligne == '{':
                niveau_accolades += 1
            elif ligne == '}':
                niveau_accolades -= 1
                if niveau_accolades == 0:
                    break
            elif ligne not in ['{', '}']:
                corps.append(ligne)
            i += 1
        
        return corps, i + 1
    
    def evaluer_expression(self, expr: str) -> Any:
        """Évalue une expression"""
        expr = expr.strip()
        
        # Chaînes de caractères
        if (expr.startswith('"') and expr.endswith('"')) or (expr.startswith("'") and expr.endswith("'")):
            return expr[1:-1]
        
        # Booléens
        if expr == 'vrai':
            return True
        if expr == 'faux':
            return False
        
        # Appel de fonction
        match_fonction = re.match(r'(\w+)\(([^)]*)\)', expr)
        if match_fonction:
            nom_fonction, args_str = match_fonction.groups()
            args = [self.evaluer_expression(a.strip()) for a in args_str.split(',')] if args_str.strip() else []
            return self.appeler_fonction(nom_fonction, args)
        
        # Opérateurs de comparaison (avant les opérateurs arithmétiques)
        if '==' in expr:
            gauche, droite = expr.split('==', 1)
            return self.evaluer_expression(gauche.strip()) == self.evaluer_expression(droite.strip())
        if '!=' in expr:
            gauche, droite = expr.split('!=', 1)
            return self.evaluer_expression(gauche.strip()) != self.evaluer_expression(droite.strip())
        if '>=' in expr:
            gauche, droite = expr.split('>=', 1)
            return self.evaluer_expression(gauche.strip()) >= self.evaluer_expression(droite.strip())
        if '<=' in expr:
            gauche, droite = expr.split('<=', 1)
            return self.evaluer_expression(gauche.strip()) <= self.evaluer_expression(droite.strip())
        if '>' in expr:
            gauche, droite = expr.split('>', 1)
            return self.evaluer_expression(gauche.strip()) > self.evaluer_expression(droite.strip())
        if '<' in expr:
            gauche, droite = expr.split('<', 1)
            return self.evaluer_expression(gauche.strip()) < self.evaluer_expression(droite.strip())
        
        # Opérateurs arithmétiques et concaténation
        # Addition et concaténation
        if '+' in expr and not expr.startswith('+'):
            parties = self.diviser_expression(expr, '+')
            if len(parties) > 1:
                resultats = [self.evaluer_expression(p) for p in parties]
                # Si au moins un élément est une chaîne, tout concaténer
                if any(isinstance(r, str) for r in resultats):
                    return ''.join(str(r) for r in resultats)
                # Sinon, additionner
                return sum(resultats)
        
        # Multiplication
        if '*' in expr:
            parties = self.diviser_expression(expr, '*')
            if len(parties) > 1:
                resultat = self.evaluer_expression(parties[0])
                for p in parties[1:]:
                    resultat *= self.evaluer_expression(p)
                return resultat
        
        # Division
        if '/' in expr:
            parties = self.diviser_expression(expr, '/')
            if len(parties) > 1:
                resultat = self.evaluer_expression(parties[0])
                for p in parties[1:]:
                    diviseur = self.evaluer_expression(p)
                    if diviseur == 0:
                        raise ZeroDivisionError("Division par zéro")
                    resultat /= diviseur
                return resultat
        
        # Soustraction
        if '-' in expr and not expr.startswith('-') and expr.count('-') > 0:
            parties = self.diviser_expression(expr, '-')
            if len(parties) > 1:
                resultat = self.evaluer_expression(parties[0])
                for p in parties[1:]:
                    resultat -= self.evaluer_expression(p)
                return resultat
        
        # Nombres
        try:
            if '.' in expr:
                return float(expr)
            return int(expr)
        except ValueError:
            pass
        
        # Variable
        if expr in self.variables:
            return self.variables[expr]
        
        raise NameError(f"Expression non reconnue: '{expr}'")
    
    def diviser_expression(self, expr: str, operateur: str) -> List[str]:
        """Divise une expression selon un opérateur, en respectant les chaînes"""
        parties = []
        partie_actuelle = ""
        dans_chaine = False
        char_chaine = None
        
        for i, char in enumerate(expr):
            if char in ['"', "'"]:
                if not dans_chaine:
                    dans_chaine = True
                    char_chaine = char
                elif char == char_chaine:
                    dans_chaine = False
                partie_actuelle += char
            elif char == operateur and not dans_chaine:
                if partie_actuelle.strip():
                    parties.append(partie_actuelle.strip())
                partie_actuelle = ""
            else:
                partie_actuelle += char
        
        if partie_actuelle.strip():
            parties.append(partie_actuelle.strip())
        
        return parties if len(parties) > 1 else [expr]


class ApplicationLangageFrancais:
    """Application graphique pour le langage de programmation en français"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Langage de Programmation en Français")
        self.root.geometry("1200x700")
        self.root.configure(bg='#f0f0f0')
        
        self.interpreteur = InterpreteurFrancais()
        
        self.creer_interface()
        self.charger_exemple_defaut()
    
    def creer_interface(self):
        """Crée l'interface graphique"""
        
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        
        # En-tête
        header_frame = tk.Frame(self.root, bg='#2c3e50', height=80)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text="🇫🇷 Langage Français", 
                              font=('Arial', 24, 'bold'), fg='white', bg='#2c3e50')
        title_label.pack(side=tk.LEFT, padx=20, pady=15)
        
        subtitle_label = tk.Label(header_frame, text="Programmation intuitive en français", 
                                 font=('Arial', 12), fg='#bdc3c7', bg='#2c3e50')
        subtitle_label.pack(side=tk.LEFT, padx=0, pady=15)
        
        # Boutons d'en-tête
        btn_frame = tk.Frame(header_frame, bg='#2c3e50')
        btn_frame.pack(side=tk.RIGHT, padx=20)
        
        self.btn_executer = tk.Button(btn_frame, text="▶ Exécuter", 
                                      command=self.executer_code,
                                      bg='#27ae60', fg='white', 
                                      font=('Arial', 12, 'bold'),
                                      padx=20, pady=10, cursor='hand2',
                                      relief=tk.FLAT, borderwidth=0)
        self.btn_executer.pack(side=tk.LEFT, padx=5)
        
        self.btn_effacer = tk.Button(btn_frame, text="🗑 Effacer", 
                                     command=self.effacer_sortie,
                                     bg='#e74c3c', fg='white', 
                                     font=('Arial', 12, 'bold'),
                                     padx=20, pady=10, cursor='hand2',
                                     relief=tk.FLAT, borderwidth=0)
        self.btn_effacer.pack(side=tk.LEFT, padx=5)
        
        # Conteneur principal
        main_container = tk.Frame(self.root, bg='#f0f0f0')
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Panneau gauche (éditeur)
        left_panel = tk.Frame(main_container, bg='white', relief=tk.RAISED, borderwidth=2)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        editor_label = tk.Label(left_panel, text="📝 Éditeur de Code", 
                               font=('Arial', 14, 'bold'), bg='white', fg='#2c3e50')
        editor_label.pack(pady=10)
        
        # Zone de texte pour le code
        self.text_code = scrolledtext.ScrolledText(left_panel, 
                                                   font=('Consolas', 11),
                                                   wrap=tk.WORD,
                                                   bg='#282c34', fg='#abb2bf',
                                                   insertbackground='white',
                                                   selectbackground='#3e4451',
                                                   relief=tk.FLAT,
                                                   padx=10, pady=10)
        self.text_code.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Panneau droit
        right_panel = tk.Frame(main_container, bg='white')
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Notebook pour les onglets
        self.notebook = ttk.Notebook(right_panel)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Onglet Sortie
        tab_sortie = tk.Frame(self.notebook, bg='white')
        self.notebook.add(tab_sortie, text="📊 Sortie")
        
        self.text_sortie = scrolledtext.ScrolledText(tab_sortie, 
                                                     font=('Consolas', 11),
                                                     wrap=tk.WORD,
                                                     bg='#1e1e1e', fg='#00ff00',
                                                     relief=tk.FLAT,
                                                     padx=10, pady=10,
                                                     state=tk.DISABLED)
        self.text_sortie.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Onglet Exemples
        tab_exemples = tk.Frame(self.notebook, bg='white')
        self.notebook.add(tab_exemples, text="💡 Exemples")
        
        exemples_scroll = tk.Frame(tab_exemples, bg='white')
        exemples_scroll.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.creer_exemples(exemples_scroll)
        
        # Onglet Documentation
        tab_doc = tk.Frame(self.notebook, bg='white')
        self.notebook.add(tab_doc, text="📚 Documentation")
        
        self.creer_documentation(tab_doc)
        
        # Barre de statut
        self.status_bar = tk.Label(self.root, text="Prêt", 
                                   font=('Arial', 10), bg='#34495e', fg='white',
                                   anchor=tk.W, padx=10, pady=5)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def creer_exemples(self, parent):
        """Crée la section des exemples"""
        exemples = [
            ("Variables et Affichage", """variable nom = "Sophie"
variable age = 25
afficher("Bonjour " + nom)
afficher("Tu as " + age + " ans")"""),
            
            ("Fonctions", """fonction additionner(a, b) {
    retourner a + b
}

variable resultat = additionner(10, 5)
afficher("10 + 5 = " + resultat)"""),
            
            ("Boucles", """pour i de 1 à 5 {
    afficher("Tour " + i)
}

liste fruits = ["pomme", "banane", "orange"]
pour chaque fruit dans fruits {
    afficher("- " + fruit)
}"""),
            
            ("Conditions", """variable temperature = 25

si temperature > 20 {
    afficher("Il fait chaud!")
}

variable score = 85
si score > 80 {
    afficher("Excellent!")
}"""),
            
            ("Programme Complet", """fonction calculer_moyenne(a, b, c) {
    variable somme = a + b + c
    retourner somme / 3
}

variable moyenne = calculer_moyenne(15, 18, 16)
afficher("Moyenne: " + moyenne)

si moyenne > 15 {
    afficher("Très bien!")
}""")
        ]
        
        for titre, code in exemples:
            frame = tk.Frame(parent, bg='#ecf0f1', relief=tk.RAISED, borderwidth=1)
            frame.pack(fill=tk.X, pady=5)
            
            titre_label = tk.Label(frame, text=titre, font=('Arial', 11, 'bold'),
                                  bg='#ecf0f1', fg='#2c3e50', anchor=tk.W)
            titre_label.pack(fill=tk.X, padx=10, pady=5)
            
            btn = tk.Button(frame, text="📋 Charger cet exemple", 
                           command=lambda c=code: self.charger_exemple(c),
                           bg='#3498db', fg='white', cursor='hand2',
                           relief=tk.FLAT, padx=10, pady=5)
            btn.pack(padx=10, pady=5)
    
    def creer_documentation(self, parent):
        """Crée la documentation"""
        doc_text = scrolledtext.ScrolledText(parent, font=('Arial', 10),
                                             wrap=tk.WORD, bg='white',
                                             padx=15, pady=15)
        doc_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        documentation = """
📚 DOCUMENTATION DU LANGAGE FRANÇAIS

═══════════════════════════════════════════

🔹 VARIABLES
   Syntaxe: variable nom = valeur
   Exemple: variable age = 25
           variable nom = "Marie"

🔹 LISTES
   Syntaxe: liste nom = [element1, element2, ...]
   Exemple: liste nombres = [1, 2, 3, 4, 5]
           liste fruits = ["pomme", "banane"]

🔹 FONCTIONS
   Syntaxe: fonction nom(param1, param2) {
              // code
              retourner valeur
           }
   Exemple: fonction multiplier(a, b) {
              retourner a * b
           }

🔹 AFFICHAGE
   Syntaxe: afficher(expression)
   Exemple: afficher("Bonjour!")
           afficher(42)
           afficher("Résultat: " + resultat)

🔹 BOUCLE NUMÉRIQUE
   Syntaxe: pour variable de debut à fin {
              // code
           }
   Exemple: pour i de 1 à 10 {
              afficher(i)
           }

🔹 BOUCLE SUR LISTE
   Syntaxe: pour chaque element dans liste {
              // code
           }
   Exemple: liste noms = ["Alice", "Bob"]
           pour chaque nom dans noms {
              afficher(nom)
           }

🔹 CONDITIONS
   Syntaxe: si condition {
              // code
           }
   Exemple: si age > 18 {
              afficher("Majeur")
           }

🔹 OPÉRATEURS
   Arithmétiques: + - * /
   Comparaison: == != > < >= <=
   Concaténation: "texte" + variable

🔹 TYPES DE DONNÉES
   • Nombres: 42, 3.14
   • Chaînes: "texte", 'texte'
   • Booléens: vrai, faux
   • Listes: [1, 2, 3]

🔹 COMMENTAIRES
   Syntaxe: // commentaire
   Exemple: // Ceci est un commentaire
"""
        
        doc_text.insert('1.0', documentation)
        doc_text.config(state=tk.DISABLED)
    
    def charger_exemple(self, code):
        """Charge un exemple dans l'éditeur"""
        self.text_code.delete('1.0', tk.END)
        self.text_code.insert('1.0', code)
        self.notebook.select(0)  # Retour à l'onglet sortie
        self.status_bar.config(text="Exemple chargé")
    
    def charger_exemple_defaut(self):
        """Charge l'exemple par défaut"""
        code_defaut = """// Bienvenue dans le Langage Français!
// Cliquez sur "Exécuter" pour tester ce programme

fonction saluer(nom) {
    retourner "Bonjour " + nom + "!"
}

variable message = saluer("Marie")
afficher(message)

afficher("Comptage de 1 à 5:")
pour i de 1 à 5 {
    afficher("Numéro: " + i)
}

liste couleurs = ["rouge", "vert", "bleu"]
afficher("Mes couleurs préférées:")
pour chaque couleur dans couleurs {
    afficher("- " + couleur)
}"""
        self.charger_exemple(code_defaut)
    
    def executer_code(self):
        """Exécute le code de l'éditeur"""
        code = self.text_code.get('1.0', tk.END)
        self.status_bar.config(text="Exécution en cours...")
        self.root.update()
        
        try:
            resultat = self.interpreteur.executer(code)
            self.afficher_sortie(resultat)
            self.status_bar.config(text="✓ Exécution terminée")
        except Exception as e:
            self.afficher_sortie(f"❌ Erreur: {str(e)}")
            self.status_bar.config(text="✗ Erreur d'exécution")
    
    def afficher_sortie(self, texte):
        """Affiche le résultat dans la zone de sortie"""
        self.text_sortie.config(state=tk.NORMAL)
        self.text_sortie.delete('1.0', tk.END)
        self.text_sortie.insert('1.0', texte)
        self.text_sortie.config(state=tk.DISABLED)
        self.notebook.select(0)  # Afficher l'onglet sortie
    
    def effacer_sortie(self):
        """Efface la zone de sortie"""
        self.text_sortie.config(state=tk.NORMAL)
        self.text_sortie.delete('1.0', tk.END)
        self.text_sortie.config(state=tk.DISABLED)
        self.status_bar.config(text="Sortie effacée")


def main():
    """Fonction principale"""
    root = tk.Tk()
    app = ApplicationLangageFrancais(root)
    root.mainloop()


if __name__ == "__main__":
    main()
