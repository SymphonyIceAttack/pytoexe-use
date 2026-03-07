import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import json
import os
from tkinter import font

class TimesheetPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Timesheet Pro 2026 - 16.50$/h")
        self.root.geometry("1300x700")
        
        # Données
        self.data_file = "heures.json"
        self.entries = []
        self.load_data()
        
        # Taux horaire fixe
        self.taux_horaire = 16.50
        
        # Style
        self.root.configure(bg='#f0f2f5')
        
        self.setup_ui()
        self.refresh_affichage()
    
    def setup_ui(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Titre
        title_label = tk.Label(main_frame, text="🍁 Timesheet Pro 2026", 
                                font=('Arial', 24, 'bold'), 
                                fg='#1a3e6f', bg='#f0f2f5')
        title_label.pack(pady=10)
        
        # Frame formulaire
        form_frame = tk.LabelFrame(main_frame, text="➕ Nouvelle entrée", 
                                    bg='white', fg='#1a3e6f', 
                                    font=('Arial', 12, 'bold'),
                                    padx=15, pady=15)
        form_frame.pack(fill=tk.X, pady=10)
        
        # Ligne 1 du formulaire
        row1 = tk.Frame(form_frame, bg='white')
        row1.pack(fill=tk.X, pady=5)
        
        tk.Label(row1, text="Année:", bg='white', width=8).pack(side=tk.LEFT, padx=5)
        self.annee_var = tk.StringVar(value="2026")
        ttk.Combobox(row1, textvariable=self.annee_var, values=[2026,2027,2028,2029,2030], 
                    width=10, state='readonly').pack(side=tk.LEFT, padx=5)
        
        tk.Label(row1, text="Mois:", bg='white', width=8).pack(side=tk.LEFT, padx=5)
        self.mois_var = tk.StringVar(value="3")
        ttk.Combobox(row1, textvariable=self.mois_var, 
                    values=[(i, f"{i:02d}") for i in range(1,13)], 
                    width=10, state='readonly').pack(side=tk.LEFT, padx=5)
        
        tk.Label(row1, text="Jour:", bg='white', width=8).pack(side=tk.LEFT, padx=5)
        self.jour_var = tk.StringVar(value="Dimanche")
        ttk.Combobox(row1, textvariable=self.jour_var, 
                    values=["Dimanche","Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi"], 
                    width=12, state='readonly').pack(side=tk.LEFT, padx=5)
        
        # Ligne 2 du formulaire
        row2 = tk.Frame(form_frame, bg='white')
        row2.pack(fill=tk.X, pady=5)
        
        tk.Label(row2, text="Début (h):", bg='white', width=10).pack(side=tk.LEFT, padx=5)
        self.debut_h = tk.StringVar(value="8")
        ttk.Combobox(row2, textvariable=self.debut_h, values=list(range(0,24)), width=5).pack(side=tk.LEFT)
        
        tk.Label(row2, text="min:", bg='white', width=5).pack(side=tk.LEFT)
        self.debut_m = tk.StringVar(value="30")
        ttk.Combobox(row2, textvariable=self.debut_m, values=[0,15,30,45], width=5).pack(side=tk.LEFT)
        
        tk.Label(row2, text="Fin (h):", bg='white', width=10).pack(side=tk.LEFT, padx=5)
        self.fin_h = tk.StringVar(value="18")
        ttk.Combobox(row2, textvariable=self.fin_h, values=list(range(0,24)), width=5).pack(side=tk.LEFT)
        
        tk.Label(row2, text="min:", bg='white', width=5).pack(side=tk.LEFT)
        self.fin_m = tk.StringVar(value="0")
        ttk.Combobox(row2, textvariable=self.fin_m, values=[0,15,30,45], width=5).pack(side=tk.LEFT)
        
        # Ligne 3
        row3 = tk.Frame(form_frame, bg='white')
        row3.pack(fill=tk.X, pady=5)
        
        tk.Label(row3, text="Pause (min):", bg='white', width=12).pack(side=tk.LEFT, padx=5)
        self.pause_var = tk.StringVar(value="30")
        ttk.Combobox(row3, textvariable=self.pause_var, values=[0,15,30,45,60], width=5).pack(side=tk.LEFT)
        
        tk.Label(row3, text="Avec qui:", bg='white', width=10).pack(side=tk.LEFT, padx=5)
        self.collab_var = tk.StringVar(value="Seul(e)")
        tk.Entry(row3, textvariable=self.collab_var, width=20).pack(side=tk.LEFT, padx=5)
        
        # Bouton Ajouter
        tk.Button(form_frame, text="➕ Ajouter cette journée", 
                 bg='#4361ee', fg='white', font=('Arial', 10, 'bold'),
                 command=self.ajouter_journee).pack(pady=10)
        
        # Frame pour les filtres
        filter_frame = tk.Frame(main_frame, bg='#f0f2f5')
        filter_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(filter_frame, text="🔍 Rechercher:", bg='#f0f2f5').pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.refresh_affichage())
        tk.Entry(filter_frame, textvariable=self.search_var, width=30).pack(side=tk.LEFT, padx=5)
        
        # Frame pour l'affichage des semaines (Canvas + Scrollbar)
        canvas_frame = tk.Frame(main_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, bg='white')
        scrollbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg='white')
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Frame pour les totaux généraux
        total_frame = tk.Frame(main_frame, bg='#1e3a5f', height=80)
        total_frame.pack(fill=tk.X, pady=10)
        
        self.total_label = tk.Label(total_frame, text="", 
                                     bg='#1e3a5f', fg='white', 
                                     font=('Arial', 14, 'bold'))
        self.total_label.pack(expand=True)
    
    def get_date_from_jour(self, annee, mois, jour_nom):
        """Trouve la première occurrence du jour dans le mois"""
        jours_map = {"Dimanche":0, "Lundi":1, "Mardi":2, "Mercredi":3,
                     "Jeudi":4, "Vendredi":5, "Samedi":6}
        jour_cible = jours_map[jour_nom]
        
        premier_jour = datetime(int(annee), int(mois), 1)
        
        # Trouver le premier jour correspondant
        for i in range(31):
            date_test = premier_jour + timedelta(days=i)
            if date_test.month != int(mois):
                break
            if date_test.weekday() == jour_cible:
                return date_test.strftime("%Y-%m-%d")
        return None
    
    def ajouter_journee(self):
        try:
            annee = self.annee_var.get()
            mois = self.mois_var.get()
            jour_nom = self.jour_var.get()
            debut_h = int(self.debut_h.get())
            debut_m = int(self.debut_m.get())
            fin_h = int(self.fin_h.get())
            fin_m = int(self.fin_m.get())
            pause = int(self.pause_var.get())
            collab = self.collab_var.get()
            
            # Obtenir la date
            date_str = self.get_date_from_jour(annee, mois, jour_nom)
            if not date_str:
                messagebox.showerror("Erreur", "Jour non trouvé dans ce mois")
                return
            
            # Calcul des heures
            debut = datetime.strptime(f"{date_str} {debut_h}:{debut_m}", "%Y-%m-%d %H:%M")
            fin = datetime.strptime(f"{date_str} {fin_h}:{fin_m}", "%Y-%m-%d %H:%M")
            
            if fin < debut:
                fin += timedelta(days=1)
            
            duree = (fin - debut).total_seconds() / 3600
            heures_travail = duree - (pause / 60)
            if heures_travail < 0:
                heures_travail = 0
            
            paye = heures_travail * self.taux_horaire
            
            # Créer l'entrée
            entry = {
                'jour': jour_nom,
                'date': date_str,
                'debut': f"{debut_h}h{debut_m:02d}",
                'fin': f"{fin_h}h{fin_m:02d}",
                'pause': pause,
                'heures': round(heures_travail, 2),
                'paye': round(paye, 2),
                'taux': self.taux_horaire,
                'collab': collab
            }
            
            self.entries.append(entry)
            self.save_data()
            self.refresh_affichage()
            
            # Reset form
            self.debut_h.set("8")
            self.debut_m.set("30")
            self.fin_h.set("18")
            self.fin_m.set("0")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur: {str(e)}")
    
    def get_week_number(self, date_str):
        """Retourne le numéro de semaine (format: 2026-W10)"""
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        # Calcul du numéro de semaine ISO
        return dt.strftime("%Y-W%W")
    
    def refresh_affichage(self):
        # Effacer l'affichage
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        # Grouper par semaine
        semaines = {}
        for entry in self.entries:
            semaine_key = self.get_week_number(entry['date'])
            if semaine_key not in semaines:
                semaines[semaine_key] = []
            semaines[semaine_key].append(entry)
        
        # Filtrer par recherche
        search = self.search_var.get().lower()
        
        # Trier les semaines
        semaines_triees = sorted(semaines.keys(), reverse=True)
        
        total_global_heures = 0
        total_global_paye = 0
        
        for semaine_key in semaines_triees:
            entries_semaine = semaines[semaine_key]
            
            # Filtrer
            if search:
                entries_semaine = [e for e in entries_semaine 
                                  if search in e['jour'].lower() 
                                  or search in e['date'] 
                                  or search in e['collab'].lower()]
                if not entries_semaine:
                    continue
            
            # Calculer les dates de début/fin de semaine
            year, week = semaine_key.split('-W')
            week_num = int(week)
            
            # Trouver le dimanche de cette semaine
            dimanche = datetime.strptime(f'{year}-{week_num}-0', "%Y-%W-%w")
            samedi = dimanche + timedelta(days=6)
            
            # En-tête semaine
            header_frame = tk.Frame(self.scrollable_frame, bg='#d0e2ff', height=50)
            header_frame.pack(fill=tk.X, pady=(20,5))
            
            tk.Label(header_frame, text=f"📆 Semaine {week_num}", 
                    bg='#d0e2ff', font=('Arial', 14, 'bold')).pack(side=tk.LEFT, padx=10)
            tk.Label(header_frame, 
                    text=f"{dimanche.strftime('%Y/%m/%d')} (dim) → {samedi.strftime('%Y/%m/%d')} (sam)",
                    bg='#d0e2ff', font=('Arial', 11)).pack(side=tk.LEFT, padx=20)
            
            # Tableau
            table_frame = tk.Frame(self.scrollable_frame, bg='white')
            table_frame.pack(fill=tk.X, pady=5)
            
            # En-têtes
            headers = ["Jour", "Date", "Début", "Fin", "Pause", "Heures", "Paye ($)", "Collaborateur", "Actions"]
            for i, h in enumerate(headers):
                tk.Label(table_frame, text=h, bg='#1a3e6f', fg='white', 
                        font=('Arial', 10, 'bold'), width=12 if i<8 else 10).grid(row=0, column=i, sticky='ew', padx=1, pady=1)
            
            # Lignes
            total_heures = 0
            total_paye = 0
            
            for i, entry in enumerate(entries_semaine):
                total_heures += entry['heures']
                total_paye += entry['paye']
                
                tk.Label(table_frame, text=entry['jour'], bg='white').grid(row=i+1, column=0, padx=2)
                tk.Label(table_frame, text=entry['date'], bg='white').grid(row=i+1, column=1, padx=2)
                tk.Label(table_frame, text=entry['debut'], bg='white').grid(row=i+1, column=2, padx=2)
                tk.Label(table_frame, text=entry['fin'], bg='white').grid(row=i+1, column=3, padx=2)
                tk.Label(table_frame, text=f"{entry['pause']} min", bg='white').grid(row=i+1, column=4, padx=2)
                tk.Label(table_frame, text=f"{entry['heures']:.2f}", bg='white').grid(row=i+1, column=5, padx=2)
                tk.Label(table_frame, text=f"{entry['paye']:.2f} $", bg='white', font=('Arial', 10, 'bold')).grid(row=i+1, column=6, padx=2)
                tk.Label(table_frame, text=entry['collab'], bg='white').grid(row=i+1, column=7, padx=2)
                
                # Boutons actions
                action_frame = tk.Frame(table_frame, bg='white')
                action_frame.grid(row=i+1, column=8)
                tk.Button(action_frame, text="✏️", command=lambda e=entry: self.modifier_entry(e),
                         font=('Arial', 8), bg='#f39c12', fg='white', width=3).pack(side=tk.LEFT, padx=1)
                tk.Button(action_frame, text="🗑️", command=lambda e=entry: self.supprimer_entry(e),
                         font=('Arial', 8), bg='#e74c3c', fg='white', width=3).pack(side=tk.LEFT, padx=1)
            
            # Total semaine
            total_frame = tk.Frame(self.scrollable_frame, bg='#e6f7ed')
            total_frame.pack(fill=tk.X, pady=5)
            
            tk.Label(total_frame, text=f"Total semaine {week_num}:", 
                    bg='#e6f7ed', font=('Arial', 11, 'bold')).pack(side=tk.LEFT, padx=10)
            tk.Label(total_frame, text=f"{total_heures:.2f} h", 
                    bg='#e6f7ed', font=('Arial', 11, 'bold')).pack(side=tk.LEFT, padx=20)
            tk.Label(total_frame, text=f"{total_paye:.2f} $", 
                    bg='#e6f7ed', font=('Arial', 11, 'bold'), fg='#27ae60').pack(side=tk.LEFT, padx=20)
            
            total_global_heures += total_heures
            total_global_paye += total_paye
        
        # Mettre à jour le total général
        self.total_label.config(text=f"💰 GRAND TOTAL: {total_global_heures:.2f} heures — {total_global_paye:.2f} $ CAD")
    
    def modifier_entry(self, entry):
        # Créer une fenêtre de modification
        mod_window = tk.Toplevel(self.root)
        mod_window.title("Modifier une journée")
        mod_window.geometry("400x500")
        
        # Remplir avec les valeurs actuelles
        tk.Label(mod_window, text="Année:").pack()
        annee_var = tk.StringVar(value=entry['date'][:4])
        tk.Entry(mod_window, textvariable=annee_var).pack()
        
        tk.Label(mod_window, text="Mois:").pack()
        mois_var = tk.StringVar(value=str(int(entry['date'][5:7])))
        tk.Entry(mod_window, textvariable=mois_var).pack()
        
        tk.Label(mod_window, text="Jour:").pack()
        jour_var = tk.StringVar(value=entry['jour'])
        ttk.Combobox(mod_window, textvariable=jour_var, 
                    values=["Dimanche","Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi"]).pack()
        
        # ... (autres champs)
        
        def save_mod():
            # Sauvegarder les modifications
            self.refresh_affichage()
            mod_window.destroy()
        
        tk.Button(mod_window, text="Sauvegarder", command=save_mod).pack()
    
    def supprimer_entry(self, entry):
        if messagebox.askyesno("Confirmation", "Supprimer cette journée ?"):
            self.entries.remove(entry)
            self.save_data()
            self.refresh_affichage()
    
    def save_data(self):
        with open(self.data_file, 'w') as f:
            json.dump(self.entries, f, indent=2)
    
    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    self.entries = json.load(f)
            except:
                self.entries = []
        else:
            self.entries = []

if __name__ == "__main__":
    root = tk.Tk()
    app = TimesheetPro(root)
    root.mainloop()