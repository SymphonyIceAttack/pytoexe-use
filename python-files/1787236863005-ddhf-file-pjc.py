import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import sqlite3
import os
class GestionChequesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GESTION DES CHEQUES 102 DEPARTEMENT CCP ORAN")
        self.root.geometry("950x900")
        self.root.resizable(True, True)
        
        # Couleurs Algerie Poste - Bleu et Jaune
        self.COULEUR_BLEU = "#0047AB"  # Bleu Algerie Poste
        self.COULEUR_JAUNE = "#FFD700"  # Jaune Algerie Poste
        self.COULEUR_BLEU_CLAIR = "#1E90FF"
        self.COULEUR_FOND = "#F0F8FF"
        
        # Configuration de la base de données
        self.configurer_base_de_donnees()
        
        # ID actuel pour modification
        self.id_actuel = None
        
        # Créer l'interface
        self.creer_widgets()
        
        # Charger les données
        self.charger_tous_les_cheques()
        
    def configurer_base_de_donnees(self):
        """Initialiser SQLite"""
        self.conn = sqlite3.connect('cheques_ccp_oran.db')
        self.cursor = self.conn.cursor()
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS cheques (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_lot TEXT(10),
                ccp_organisme TEXT(8),
                cle TEXT(2),
                intitule_organisme TEXT(30),
                numero_serie_cheque TEXT(12),
                montant_global REAL,
                date_reception TEXT,
                date_debit TEXT,
                observation TEXT(40)
            )
        ''')
        self.conn.commit()
        
    def creer_widgets(self):
        # Style personnalisé
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configurer les styles avec les couleurs Algerie Poste
        style.configure('TFrame', background=self.COULEUR_FOND)
        style.configure('TLabel', background=self.COULEUR_FOND, font=('Arial', 10))
        style.configure('TButton', font=('Arial', 10, 'bold'))
        style.configure('Header.TLabel', background=self.COULEUR_BLEU, 
                       foreground=self.COULEUR_JAUNE, font=('Arial', 16, 'bold'))
        style.configure('Field.TLabel', background=self.COULEUR_FOND, 
                       font=('Arial', 10, 'bold'))
        
        # Cadre principal
        self.cadre_principal = tk.Frame(self.root, bg=self.COULEUR_FOND)
        self.cadre_principal.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # En-tête avec couleur
        cadre_entete = tk.Frame(self.cadre_principal, bg=self.COULEUR_BLEU, height=120)
        cadre_entete.pack(fill=tk.X, pady=(0, 20))
        cadre_entete.pack_propagate(False)
        
        # Logo Algerie Poste
        self.cadre_logo = tk.Frame(cadre_entete, bg=self.COULEUR_BLEU)
        self.cadre_logo.pack(side=tk.LEFT, padx=20, pady=10)
        self.charger_logo()
        
        # Titre
        titre = tk.Label(cadre_entete, 
                        text="GESTION DES CHEQUES\n102 DEPARTEMENT CCP ORAN",
                        bg=self.COULEUR_BLEU, fg=self.COULEUR_JAUNE,
                        font=('Arial', 18, 'bold'), justify=tk.CENTER)
        titre.pack(side=tk.LEFT, expand=True)
        
        # Cadre formulaire
        cadre_formulaire = tk.Frame(self.cadre_principal, bg=self.COULEUR_FOND)
        cadre_formulaire.pack(fill=tk.X, padx=20, pady=10)
        
        # Configuration grille
        cadre_formulaire.columnconfigure(1, weight=1)
        
        ligne = 0
        
        # Ligne 1: NUMERO DE LOT
        self.creer_etiquette(cadre_formulaire, ligne, "NUMERO DE LOT:")
        self.var_numero_lot = tk.StringVar()
        self.creer_entree_numerique(cadre_formulaire, ligne, self.var_numero_lot, 10)
        ligne += 1
        
        # Ligne 2: CCP ORGANISME et CLE sur même ligne
        self.creer_etiquette(cadre_formulaire, ligne, "CCP ORGANISME:")
        
        cadre_ccp = tk.Frame(cadre_formulaire, bg=self.COULEUR_FOND)
        cadre_ccp.grid(row=ligne, column=1, sticky=tk.W, padx=5, pady=5)
        
        self.var_ccp = tk.StringVar()
        entree_ccp = tk.Entry(cadre_ccp, textvariable=self.var_ccp, width=12,
                             font=('Arial', 11), bd=2, relief=tk.GROOVE)
        entree_ccp.pack(side=tk.LEFT)
        
        tk.Label(cadre_ccp, text="  CLÉ:", bg=self.COULEUR_FOND, 
                font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        
        self.var_cle = tk.StringVar()
        entree_cle = tk.Entry(cadre_ccp, textvariable=self.var_cle, width=5,
                             font=('Arial', 11), bd=2, relief=tk.GROOVE)
        entree_cle.pack(side=tk.LEFT, padx=5)
        
        # Validation
        entree_ccp.config(validate='key', 
                         validatecommand=(self.root.register(self.valider_longueur), '%P', 8))
        entree_cle.config(validate='key', 
                         validatecommand=(self.root.register(self.valider_numerique), '%P', 2))
        ligne += 1
        
        # Ligne 3: INTITULE ORGANISME
        self.creer_etiquette(cadre_formulaire, ligne, "INTITULE ORGANISME:")
        self.var_intitule = tk.StringVar()
        self.creer_entree(cadre_formulaire, ligne, self.var_intitule, 30)
        ligne += 1
        
        # Ligne 4: NUMERO SERIE DE CHEQUE
        self.creer_etiquette(cadre_formulaire, ligne, "NUMERO SERIE DE CHEQUE:")
        self.var_numero_serie = tk.StringVar()
        self.creer_entree_numerique(cadre_formulaire, ligne, self.var_numero_serie, 12)
        ligne += 1
        
        # Ligne 5: MONTANT GLOBAL DU CHEQUE
        self.creer_etiquette(cadre_formulaire, ligne, "MONTANT GLOBAL DU CHEQUE:")
        self.var_montant = tk.StringVar()
        entree_montant = tk.Entry(cadre_formulaire, textvariable=self.var_montant, 
                                  width=20, font=('Arial', 11), bd=2, relief=tk.GROOVE)
        entree_montant.grid(row=ligne, column=1, sticky=tk.W, padx=5, pady=5)
        tk.Label(cadre_formulaire, text="DA (Dinars)", bg=self.COULEUR_FOND, 
                font=('Arial', 10)).grid(row=ligne, column=2, sticky=tk.W)
        ligne += 1
        
        # Ligne 6: DATE RECEPTION avec calendrier
        self.creer_etiquette(cadre_formulaire, ligne, "DATE RECEPTION:")
        self.var_date_reception = tk.StringVar()
        cal_reception = DateEntry(cadre_formulaire, textvariable=self.var_date_reception,
                                  width=15, background=self.COULEUR_BLEU,
                                  foreground=self.COULEUR_JAUNE, borderwidth=2,
                                  date_pattern='dd/mm/yyyy', font=('Arial', 10))
        cal_reception.grid(row=ligne, column=1, sticky=tk.W, padx=5, pady=5)
        ligne += 1
        
        # Ligne 7: DATE DEBIT avec calendrier
        self.creer_etiquette(cadre_formulaire, ligne, "DATE DEBIT:")
        self.var_date_debit = tk.StringVar()
        cal_debit = DateEntry(cadre_formulaire, textvariable=self.var_date_debit,
                             width=15, background=self.COULEUR_BLEU,
                             foreground=self.COULEUR_JAUNE, borderwidth=2,
                             date_pattern='dd/mm/yyyy', font=('Arial', 10))
        cal_debit.grid(row=ligne, column=1, sticky=tk.W, padx=5, pady=5)
        ligne += 1
        
        # Ligne 8: OBSERVATION
        self.creer_etiquette(cadre_formulaire, ligne, "OBSERVATION:")
        self.var_observation = tk.StringVar()
        self.creer_entree(cadre_formulaire, ligne, self.var_observation, 40)
        ligne += 1
        
        # Cadre boutons avec couleur
        cadre_boutons = tk.Frame(self.cadre_principal, bg=self.COULEUR_BLEU, 
                                bd=3, relief=tk.RIDGE)
        cadre_boutons.pack(fill=tk.X, padx=20, pady=15)
        
        boutons = [
            ("Enregistrer", self.enregistrer, self.COULEUR_JAUNE, self.COULEUR_BLEU),
            ("Imprimer", self.imprimer, self.COULEUR_JAUNE, self.COULEUR_BLEU),
            ("Rechercher", self.rechercher, self.COULEUR_JAUNE, self.COULEUR_BLEU),
            ("Modifier", self.modifier, self.COULEUR_JAUNE, self.COULEUR_BLEU),
            ("Supprimer", self.supprimer, "#FF6B6B", "white"),
            ("Effacer", self.effacer, self.COULEUR_JAUNE, self.COULEUR_BLEU),
        ]
        
        for texte, commande, bg, fg in boutons:
            btn = tk.Button(cadre_boutons, text=texte, command=commande,
                          bg=bg, fg=fg, font=('Arial', 10, 'bold'),
                          width=12, cursor='hand2', bd=2, relief=tk.RAISED)
            btn.pack(side=tk.LEFT, padx=8, pady=10)
        
        # Cadre recherche par plage de dates
        cadre_recherche = tk.LabelFrame(self.cadre_principal, 
                                       text=" RECHERCHE PAR PLAGE DE DATES ",
                                       bg=self.COULEUR_FOND, fg=self.COULEUR_BLEU,
                                       font=('Arial', 11, 'bold'), bd=3)
        cadre_recherche.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(cadre_recherche, text="Du:", bg=self.COULEUR_FOND, 
                font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        
        self.var_date_debut = tk.StringVar()
        cal_debut = DateEntry(cadre_recherche, textvariable=self.var_date_debut,
                             width=12, background=self.COULEUR_BLEU,
                             foreground=self.COULEUR_JAUNE, date_pattern='dd/mm/yyyy')
        cal_debut.pack(side=tk.LEFT, padx=5)
        
        tk.Label(cadre_recherche, text="Au:", bg=self.COULEUR_FOND, 
                font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=(15, 5))
        
        self.var_date_fin = tk.StringVar()
        cal_fin = DateEntry(cadre_recherche, textvariable=self.var_date_fin,
                           width=12, background=self.COULEUR_BLEU,
                           foreground=self.COULEUR_JAUNE, date_pattern='dd/mm/yyyy')
        cal_fin.pack(side=tk.LEFT, padx=5)
        
        tk.Button(cadre_recherche, text="Rechercher Plage", 
                 command=self.rechercher_plage,
                 bg=self.COULEUR_JAUNE, fg=self.COULEUR_BLEU,
                 font=('Arial', 10, 'bold'), cursor='hand2').pack(side=tk.LEFT, padx=15)
        
        tk.Button(cadre_recherche, text="Imprimer Résultats", 
                 command=self.imprimer_resultats,
                 bg=self.COULEUR_BLEU, fg=self.COULEUR_JAUNE,
                 font=('Arial', 10, 'bold'), cursor='hand2').pack(side=tk.LEFT, padx=5)
        
        # Tableau des résultats
        cadre_tableau = tk.Frame(self.cadre_principal, bg=self.COULEUR_FOND)
        cadre_tableau.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Style du treeview
        style.configure("Custom.Treeview", 
                       background=self.COULEUR_FOND,
                       foreground="black",
                       fieldbackground=self.COULEUR_FOND,
                       font=('Arial', 9))
        style.configure("Custom.Treeview.Heading",
                       background=self.COULEUR_BLEU,
                       foreground=self.COULEUR_JAUNE,
                       font=('Arial', 10, 'bold'))
        
        colonnes = ('lot', 'ccp', 'intitule', 'serie', 'montant', 'reception', 'debit', 'obs')
        self.arbre = ttk.Treeview(cadre_tableau, columns=colonnes, show='headings',
                                  height=10, style="Custom.Treeview")
        
        self.arbre.heading('lot', text='N° LOT')
        self.arbre.heading('ccp', text='CCP/CLÉ')
        self.arbre.heading('intitule', text='INTITULÉ')
        self.arbre.heading('serie', text='N° SÉRIE')
        self.arbre.heading('montant', text='MONTANT (DA)')
        self.arbre.heading('reception', text='DATE RÉCEPTION')
        self.arbre.heading('debit', text='DATE DÉBIT')
        self.arbre.heading('obs', text='OBSERVATION')
        
        self.arbre.column('lot', width=80)
        self.arbre.column('ccp', width=80)
        self.arbre.column('intitule', width=150)
        self.arbre.column('serie', width=100)
        self.arbre.column('montant', width=100)
        self.arbre.column('reception', width=100)
        self.arbre.column('debit', width=100)
        self.arbre.column('obs', width=120)
        
        scrollbar = ttk.Scrollbar(cadre_tableau, orient=tk.VERTICAL, command=self.arbre.yview)
        self.arbre.configure(yscrollcommand=scrollbar.set)
        
        self.arbre.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.arbre.bind('<<TreeviewSelect>>', self.sur_selection)
        
        # Barre d'état
        self.barre_etat = tk.Label(self.cadre_principal, 
                                  text="Prêt - Sélectionnez un chèque pour modifier ou supprimer",
                                  bg=self.COULEUR_BLEU, fg=self.COULEUR_JAUNE,
                                  font=('Arial', 9), anchor=tk.W)
        self.barre_etat.pack(fill=tk.X, side=tk.BOTTOM)
        
    def creer_etiquette(self, parent, ligne, texte):
        """Créer une étiquette en gras et majuscules"""
        lbl = tk.Label(parent, text=texte, bg=self.COULEUR_FOND,
                      font=('Arial', 10, 'bold'))
        lbl.grid(row=ligne, column=0, sticky=tk.W, pady=8, padx=5)
        
    def creer_entree(self, parent, ligne, var, max_chars):
        """Créer une entrée standard"""
        entree = tk.Entry(parent, textvariable=var, width=35,
                         font=('Arial', 11), bd=2, relief=tk.GROOVE)
        entree.grid(row=ligne, column=1, sticky=tk.W, padx=5, pady=5)
        entree.config(validate='key', 
                     validatecommand=(self.root.register(self.valider_longueur), '%P', max_chars))
        
    def creer_entree_numerique(self, parent, ligne, var, max_chars):
        """Créer une entrée numérique"""
        entree = tk.Entry(parent, textvariable=var, width=20,
                         font=('Arial', 11), bd=2, relief=tk.GROOVE)
        entree.grid(row=ligne, column=1, sticky=tk.W, padx=5, pady=5)
        entree.config(validate='key', 
                     validatecommand=(self.root.register(self.valider_numerique), '%P', max_chars))
        
    def valider_numerique(self, valeur, max_chars):
        """Validation numérique"""
        if len(valeur) > int(max_chars):
            return False
        return valeur.isdigit() or valeur == ""
    
    def valider_longueur(self, valeur, max_chars):
        """Validation longueur"""
        return len(valeur) <= int(max_chars)
    
    def charger_logo(self):
        """Charger le logo Algerie Poste"""
        try:
            chemins = ['algerie_poste_logo.png', 'algerie_poste_logo.jpg', 
                      'logo_algerie_poste.png', 'logo.png']
            for chemin in chemins:
                if os.path.exists(chemin):
                    image = Image.open(chemin)
                    image = image.resize((120, 80), Image.Resampling.LANCZOS)
                    self.photo_logo = ImageTk.PhotoImage(image)
                    lbl = tk.Label(self.cadre_logo, image=self.photo_logo, bg=self.COULEUR_BLEU)
                    lbl.pack()
                    return
            # Logo par défaut
            lbl = tk.Label(self.cadre_logo, text="ALGERIE\nPOSTE", bg=self.COULEUR_BLEU,
                          fg=self.COULEUR_JAUNE, font=('Arial', 14, 'bold'))
            lbl.pack()
        except Exception as e:
            lbl = tk.Label(self.cadre_logo, text="ALGERIE\nPOSTE", bg=self.COULEUR_BLEU,
                          fg=self.COULEUR_JAUNE, font=('Arial', 14, 'bold'))
            lbl.pack()
    
    def enregistrer(self):
        """Enregistrer un chèque"""
        try:
            # Validation
            if not self.var_numero_lot.get():
                messagebox.showwarning("Validation", "Le numéro de lot est obligatoire!")
                return
                
            montant = 0.0
            try:
                montant = float(self.var_montant.get().replace(',', '.'))
            except:
                pass
            
            donnees = (
                self.var_numero_lot.get()[:10],
                self.var_ccp.get()[:8],
                self.var_cle.get()[:2],
                self.var_intitule.get()[:30],
                self.var_numero_serie.get()[:12],
                montant,
                self.var_date_reception.get(),
                self.var_date_debit.get(),
                self.var_observation.get()[:40]
            )
            
            if self.id_actuel:
                self.cursor.execute('''
                    UPDATE cheques SET numero_lot=?, ccp_organisme=?, cle=?,
                    intitule_organisme=?, numero_serie_cheque=?, montant_global=?,
                    date_reception=?, date_debit=?, observation=?
                    WHERE id=?
                ''', donnees + (self.id_actuel,))
                msg = "Chèque modifié avec succès!"
            else:
                self.cursor.execute('''
                    INSERT INTO cheques VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', donnees)
                msg = "Chèque enregistré avec succès!"
            
            self.conn.commit()
            messagebox.showinfo("Succès", msg)
            self.effacer()
            self.charger_tous_les_cheques()
            self.barre_etat.config(text=msg)
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Échec: {str(e)}")
    
    def imprimer(self):
        """Imprimer le chèque actuel"""
        if not self.var_numero_lot.get():
            messagebox.showwarning("Attention", "Veuillez d'abord sélectionner ou saisir un chèque")
            return
            
        contenu = f"""
{'='*70}
           ALGERIE POSTE - GESTION DES CHEQUES
           102 DEPARTEMENT CCP ORAN
{'='*70}

NUMERO DE LOT:              {self.var_numero_lot.get()}
CCP ORGANISME:              {self.var_ccp.get()}          CLÉ: {self.var_cle.get()}
INTITULE ORGANISME:         {self.var_intitule.get()}
NUMERO SERIE DE CHEQUE:     {self.var_numero_serie.get()}
MONTANT GLOBAL DU CHEQUE:   {self.var_montant.get()} DA
DATE RECEPTION:             {self.var_date_reception.get()}
DATE DEBIT:                 {self.var_date_debit.get()}
OBSERVATION:                {self.var_observation.get()}

{'='*70}
Imprimé le: {datetime.now().strftime('%d/%m/%Y %H:%M')}
"""
        self.afficher_apercu(contenu, "Imprimer Chèque")
    
    def imprimer_resultats(self):
        """Imprimer tous les résultats affichés"""
        items = self.arbre.get_children()
        if not items:
            messagebox.showinfo("Information", "Aucun résultat à imprimer")
            return
        
        contenu = f"""
{'='*90}
           ALGERIE POSTE - GESTION DES CHEQUES
           102 DEPARTEMENT CCP ORAN
           LISTE DES CHEQUES
{'='*90}

{'N° LOT':<12}{'CCP/CLÉ':<12}{'INTITULÉ':<20}{'N° SÉRIE':<15}{'MONTANT':<12}{'DATE REC.':<12}{'DATE DÉB.':<12}
{'-'*90}
"""
        total = 0
        for item in items:
            vals = self.arbre.item(item)['values']
            try:
                montant = float(str(vals[4]).replace(',', '.'))
                total += montant
            except:
                montant = 0
            
            contenu += f"{str(vals[0]):<12}{str(vals[1]):<12}{str(vals[2])[:18]:<20}{str(vals[3]):<15}{str(vals[4]):<12}{str(vals[5]):<12}{str(vals[6]):<12}\n"
        
        contenu += f"{'-'*90}\n"
        contenu += f"{'TOTAL:':<72}{total:,.2f} DA\n"
        contenu += f"{'='*90}\n"
        contenu += f"Nombre de chèques: {len(items)}                    Imprimé le: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
        
        self.afficher_apercu(contenu, "Imprimer Liste des Chèques")
    
    def afficher_apercu(self, contenu, titre):
        """Afficher l'aperçu avant impression"""
        fenetre = tk.Toplevel(self.root)
        fenetre.title(titre)
        fenetre.geometry("700x600")
        
        texte = tk.Text(fenetre, wrap=tk.NONE, padx=10, pady=10,
                       font=('Courier', 10))
        texte.pack(fill=tk.BOTH, expand=True)
        
        scrollbar_h = ttk.Scrollbar(fenetre, orient=tk.HORIZONTAL, command=texte.xview)
        texte.configure(xscrollcommand=scrollbar_h.set)
        scrollbar_h.pack(fill=tk.X)
        
        texte.insert('1.0', contenu)
        texte.config(state=tk.DISABLED)
        
        btn_cadre = tk.Frame(fenetre)
        btn_cadre.pack(pady=10)
        
        tk.Button(btn_cadre, text="Enregistrer en TXT", 
                 command=lambda: self.sauvegarder_txt(contenu),
                 bg=self.COULEUR_BLEU, fg=self.COULEUR_JAUNE,
                 font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_cadre, text="Fermer", command=fenetre.destroy,
                 bg="#FF6B6B", fg="white", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
    
    def sauvegarder_txt(self, contenu):
        """Sauvegarder dans un fichier texte"""
        fichier = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Fichiers texte", "*.txt")]
        )
        if fichier:
            with open(fichier, 'w', encoding='utf-8') as f:
                f.write(contenu)
            messagebox.showinfo("Succès", f"Sauvegardé dans: {fichier}")
    
    def rechercher(self):
        """Rechercher des chèques"""
        fenetre = tk.Toplevel(self.root)
        fenetre.title("Rechercher")
        fenetre.geometry("400x150")
        fenetre.transient(self.root)
        
        tk.Label(fenetre, text="Rechercher (N° Lot, CCP, ou Intitulé):",
                font=('Arial', 10)).pack(pady=10)
        
        var = tk.StringVar()
        entree = tk.Entry(fenetre, textvariable=var, width=40, font=('Arial', 11))
        entree.pack(pady=5)
        entree.focus()
        
        def lancer_recherche():
            terme = var.get()
            self.cursor.execute('''
                SELECT * FROM cheques WHERE 
                numero_lot LIKE ? OR ccp_organisme LIKE ? OR 
                intitule_organisme LIKE ? OR numero_serie_cheque LIKE ?
            ''', (f'%{terme}%', f'%{terme}%', f'%{terme}%', f'%{terme}%'))
            
            resultats = self.cursor.fetchall()
            self.afficher_resultats(resultats)
            fenetre.destroy()
            
            self.barre_etat.config(text=f"Recherche: {len(resultats)} résultat(s) trouvé(s)")
        
        tk.Button(fenetre, text="Rechercher", command=lancer_recherche,
                 bg=self.COULEUR_BLEU, fg=self.COULEUR_JAUNE,
                 font=('Arial', 10, 'bold')).pack(pady=10)
        
        fenetre.bind('<Return>', lambda e: lancer_recherche())
    
    def rechercher_plage(self):
        """Rechercher par plage de dates"""
        debut = self.var_date_debut.get()
        fin = self.var_date_fin.get()
        
        if not debut or not fin:
            messagebox.showwarning("Attention", "Veuillez sélectionner les deux dates")
            return
        
        self.cursor.execute('''
            SELECT * FROM cheques WHERE date_reception BETWEEN ? AND ?
        ''', (debut, fin))
        
        resultats = self.cursor.fetchall()
        self.afficher_resultats(resultats)
        self.barre_etat.config(text=f"Plage de dates: {len(resultats)} chèque(s) trouvé(s)")
    
    def afficher_resultats(self, resultats):
        """Afficher les résultats dans le tableau"""
        for item in self.arbre.get_children():
            self.arbre.delete(item)
        
        for ligne in resultats:
            ccp_cle = f"{ligne[2]}/{ligne[3]}" if ligne[3] else ligne[2]
            self.arbre.insert('', tk.END, values=(
                ligne[1], ccp_cle, ligne[4], ligne[5],
                f"{ligne[6]:,.2f}" if ligne[6] else "0.00",
                ligne[7], ligne[8], ligne[9]
            ), tags=(ligne[0],))
    
    def charger_tous_les_cheques(self):
        """Charger tous les chèques"""
        self.cursor.execute('SELECT * FROM cheques ORDER BY id DESC')
        self.afficher_resultats(self.cursor.fetchall())
    
    def sur_selection(self, event):
        """Gérer la sélection"""
        selection = self.arbre.selection()
        if selection:
            item = self.arbre.item(selection[0])
            self.id_actuel = item['tags'][0] if item['tags'] else None
    
    def modifier(self):
        """Charger pour modification"""
        if not self.id_actuel:
            messagebox.showwarning("Attention", "Veuillez sélectionner un chèque dans la liste")
            return
        
        self.cursor.execute('SELECT * FROM cheques WHERE id=?', (self.id_actuel,))
        row = self.cursor.fetchone()
        
        if row:
            self.var_numero_lot.set(row[1])
            self.var_ccp.set(row[2])
            self.var_cle.set(row[3])
            self.var_intitule.set(row[4])
            self.var_numero_serie.set(row[5])
            self.var_montant.set(str(row[6]) if row[6] else "")
            self.var_date_reception.set(row[7])
            self.var_date_debit.set(row[8])
            self.var_observation.set(row[9])
            self.barre_etat.config(text=f"Modification du chèque N° {row[1]}")
    
    def supprimer(self):
        """Supprimer un chèque"""
        if not self.id_actuel:
            messagebox.showwarning("Attention", "Veuillez sélectionner un chèque à supprimer")
            return
        
        if messagebox.askyesno("Confirmation", "Supprimer ce chèque définitivement ?"):
            self.cursor.execute('DELETE FROM cheques WHERE id=?', (self.id_actuel,))
            self.conn.commit()
            messagebox.showinfo("Succès", "Chèque supprimé")
            self.effacer()
            self.charger_tous_les_cheques()
    
    def effacer(self):
        """Effacer le formulaire"""
        self.var_numero_lot.set('')
        self.var_ccp.set('')
        self.var_cle.set('')
        self.var_intitule.set('')
        self.var_numero_serie.set('')
        self.var_montant.set('')
        self.var_date_reception.set('')
        self.var_date_debit.set('')
        self.var_observation.set('')
        self.id_actuel = None
        self.arbre.selection_clear()
        self.barre_etat.config(text="Formulaire réinitialisé - Prêt pour nouvelle saisie")

# Installation des dépendances si nécessaire
def verifier_dependances():
    try:
        from tkcalendar import DateEntry
    except ImportError:
        print("Installation de tkcalendar...")
        import subprocess
        subprocess.check_call(['pip', 'install', 'tkcalendar'])
        print("tkcalendar installé. Veuillez relancer l'application.")
        exit()

if __name__ == "__main__":
    # verifier_dependances()  # Décommenter si tkcalendar n'est pas installé
    
    root = tk.Tk()
    app = GestionChequesApp(root)
    root.mainloop()