import tkinter as tk
from tkinter import messagebox
import random

class ApprendreSouris:
    def __init__(self):
        self.fenetre = tk.Tk()
        self.fenetre.title("🎮 Atelier Souris - Exercices Interactifs")
        self.fenetre.geometry("1000x700")
        self.fenetre.configure(bg='#2c3e50')
        
        # Variables d'état
        self.exercice_actuel = None
        self.en_jeu = False
        
        # Variables pour l'exercice de vitesse
        self.clics_reussis = 0
        self.clics_rate = 0
        self.cibles_gauche_restantes = 0
        self.cibles_droit_restantes = 0
        self.type_cible_actuelle = None
        self.cible_id = None
        self.temps_restant = 0
        self.timer_id = None
        self.apparition_id = None
        
        self.creer_interface()
        
    def creer_interface(self):
        # Titre principal
        titre = tk.Label(
            self.fenetre,
            text="🐭 MAÎTRISE DE LA SOURIS 🖱️",
            font=('Arial', 28, 'bold'),
            bg='#2c3e50',
            fg='#ecf0f1'
        )
        titre.pack(pady=20)
        
        # Frame principal divisé en deux
        frame_principal = tk.Frame(self.fenetre, bg='#2c3e50')
        frame_principal.pack(expand=True, fill='both', padx=20, pady=10)
        
        # Panneau de gauche - Menu des exercices
        frame_menu = tk.Frame(frame_principal, bg='#34495e', width=250)
        frame_menu.pack(side='left', fill='y', padx=(0, 10))
        frame_menu.pack_propagate(False)
        
        tk.Label(
            frame_menu,
            text="📋 EXERCICES",
            font=('Arial', 16, 'bold'),
            bg='#34495e',
            fg='#ecf0f1'
        ).pack(pady=15)
        
        # Boutons des exercices
        exercices = [
            ("🖱️ Clic Gauche", self.exercice_clic_gauche),
            ("🖱️ Clic Droit", self.exercice_clic_droit),
            ("🖱️ Double Clic", self.exercice_double_clic),
            ("✋ Glisser-Déposer", self.exercice_glisser_deposer),
            ("⬆️ Roulette Haut", self.exercice_roulette_haut),
            ("⬇️ Roulette Bas", self.exercice_roulette_bas),
            ("⚡ Vitesse (20s)", self.exercice_vitesse),
        ]
        
        for texte, commande in exercices:
            btn = tk.Button(
                frame_menu,
                text=texte,
                command=commande,
                bg='#3498db',
                fg='white',
                font=('Arial', 12),
                padx=20,
                pady=10,
                relief='flat',
                width=20
            )
            btn.pack(pady=5)
            btn.bind('<Enter>', lambda e, b=btn: b.configure(bg='#2980b9'))
            btn.bind('<Leave>', lambda e, b=btn: b.configure(bg='#3498db'))
        
        # Zone de jeu (droite)
        frame_jeu = tk.Frame(frame_principal, bg='#ecf0f1', relief='sunken', bd=3)
        frame_jeu.pack(side='right', expand=True, fill='both')
        
        # Zone d'exercice
        self.zone_exercice = tk.Canvas(
            frame_jeu,
            bg='white',
            highlightthickness=0,
            cursor='hand2'
        )
        self.zone_exercice.pack(expand=True, fill='both', padx=10, pady=10)
        
        # Barre d'information
        frame_info = tk.Frame(self.fenetre, bg='#34495e', height=80)
        frame_info.pack(fill='x', padx=20, pady=10)
        
        # Instructions
        self.instruction_label = tk.Label(
            frame_info,
            text="Choisis un exercice dans le menu",
            font=('Arial', 12),
            bg='#34495e',
            fg='#ecf0f1'
        )
        self.instruction_label.pack(side='left', padx=20)
        
        # Statistiques pour l'exercice de vitesse
        self.stats_frame = tk.Frame(frame_info, bg='#34495e')
        self.stats_frame.pack(side='right', padx=20)
        
        self.stats_reussis = tk.Label(
            self.stats_frame,
            text="✅: 0",
            font=('Arial', 14, 'bold'),
            bg='#34495e',
            fg='#2ecc71'
        )
        self.stats_reussis.pack(side='left', padx=10)
        
        self.stats_rate = tk.Label(
            self.stats_frame,
            text="❌: 0",
            font=('Arial', 14, 'bold'),
            bg='#34495e',
            fg='#e74c3c'
        )
        self.stats_rate.pack(side='left', padx=10)
        
        self.stats_restantes = tk.Label(
            self.stats_frame,
            text="🎯: 0",
            font=('Arial', 14, 'bold'),
            bg='#34495e',
            fg='#f1c40f'
        )
        self.stats_restantes.pack(side='left', padx=10)
        
        self.timer_label = tk.Label(
            self.stats_frame,
            text="⏱️: 20s",
            font=('Arial', 14, 'bold'),
            bg='#34495e',
            fg='#3498db'
        )
        self.timer_label.pack(side='left', padx=10)
        
        # Lier les événements
        self.zone_exercice.bind('<Button-1>', self.on_clic_gauche)
        self.zone_exercice.bind('<Button-3>', self.on_clic_droit)
        
    def reset_exercice(self):
        """Réinitialise la zone d'exercice"""
        # Arrêter tous les timers
        if self.timer_id:
            self.fenetre.after_cancel(self.timer_id)
            self.timer_id = None
        if self.apparition_id:
            self.fenetre.after_cancel(self.apparition_id)
            self.apparition_id = None
            
        self.zone_exercice.delete("all")
        self.en_jeu = False
        
        # Réinitialiser les statistiques
        self.stats_reussis.config(text="✅: 0")
        self.stats_rate.config(text="❌: 0")
        self.stats_restantes.config(text="🎯: 0")
        self.timer_label.config(text="⏱️: 20s")
        
    # Exercices de base (simplifiés pour se concentrer sur l'exercice de vitesse)
    def exercice_clic_gauche(self):
        self.reset_exercice()
        self.instruction_label.config(text="Exercice Clic Gauche - Clique sur les carrés bleus")
        self.zone_exercice.create_text(400, 250, text="Exercice Clic Gauche", font=('Arial', 20))
        
    def exercice_clic_droit(self):
        self.reset_exercice()
        self.instruction_label.config(text="Exercice Clic Droit - Clique droit sur les cercles rouges")
        self.zone_exercice.create_text(400, 250, text="Exercice Clic Droit", font=('Arial', 20))
        
    def exercice_double_clic(self):
        self.reset_exercice()
        self.instruction_label.config(text="Exercice Double Clic")
        self.zone_exercice.create_text(400, 250, text="Exercice Double Clic", font=('Arial', 20))
        
    def exercice_glisser_deposer(self):
        self.reset_exercice()
        self.instruction_label.config(text="Exercice Glisser-Déposer")
        self.zone_exercice.create_text(400, 250, text="Exercice Glisser-Déposer", font=('Arial', 20))
        
    def exercice_roulette_haut(self):
        self.reset_exercice()
        self.instruction_label.config(text="Exercice Roulette Haut")
        self.zone_exercice.create_text(400, 250, text="Exercice Roulette Haut", font=('Arial', 20))
        
    def exercice_roulette_bas(self):
        self.reset_exercice()
        self.instruction_label.config(text="Exercice Roulette Bas")
        self.zone_exercice.create_text(400, 250, text="Exercice Roulette Bas", font=('Arial', 20))
    
    # EXERCICE DE VITESSE CORRIGÉ
    def exercice_vitesse(self):
        self.reset_exercice()
        self.exercice_actuel = "vitesse"
        self.en_jeu = True
        
        # Initialisation des variables
        self.clics_reussis = 0
        self.clics_rate = 0
        self.cibles_gauche_restantes = 5  # 5 cibles clic gauche
        self.cibles_droit_restantes = 5    # 5 cibles clic droit
        self.cibles_totales = 10
        self.temps_restant = 20  # 20 secondes
        self.cible_id = None
        
        # Mise à jour de l'affichage
        self.instruction_label.config(
            text="⚡ VITESSE - Clique GAUCHE sur les carrés bleus, DROIT sur les cercles rouges !"
        )
        self.mettre_a_jour_affichage()
        
        # Démarrer le timer
        self.mettre_a_jour_timer()
        
        # Créer la première cible
        self.creer_cible()
    
    def mettre_a_jour_affichage(self):
        """Met à jour tous les affichages"""
        self.stats_reussis.config(text=f"✅: {self.clics_reussis}")
        self.stats_rate.config(text=f"❌: {self.clics_rate}")
        restantes = self.cibles_gauche_restantes + self.cibles_droit_restantes
        self.stats_restantes.config(text=f"🎯: {restantes}")
        self.timer_label.config(text=f"⏱️: {self.temps_restant}s")
    
    def mettre_a_jour_timer(self):
        """Gère le compte à rebours"""
        if self.en_jeu and self.temps_restant > 0:
            self.temps_restant -= 1
            self.timer_label.config(text=f"⏱️: {self.temps_restant}s")
            
            if self.temps_restant > 0:
                self.timer_id = self.fenetre.after(1000, self.mettre_a_jour_timer)
            else:
                self.fin_exercice()
    
    def creer_cible(self):
        """Crée une nouvelle cible"""
        if not self.en_jeu:
            return
            
        # Vérifier s'il reste des cibles
        restantes = self.cibles_gauche_restantes + self.cibles_droit_restantes
        if restantes <= 0 or self.temps_restant <= 0:
            return
        
        # Supprimer l'ancienne cible si elle existe
        if self.cible_id:
            self.zone_exercice.delete(self.cible_id)
        
        # Choisir le type de cible
        if self.cibles_gauche_restantes > 0 and self.cibles_droit_restantes > 0:
            self.type_cible_actuelle = random.choice(['gauche', 'droit'])
        elif self.cibles_gauche_restantes > 0:
            self.type_cible_actuelle = 'gauche'
        else:
            self.type_cible_actuelle = 'droit'
        
        # Position aléatoire
        x = random.randint(100, 700)
        y = random.randint(100, 450)
        
        # Créer la cible selon son type
        if self.type_cible_actuelle == 'gauche':
            self.cible_id = self.zone_exercice.create_rectangle(
                x-30, y-30, x+30, y+30,
                fill='#3498db',
                outline='#2980b9',
                width=3,
                tags="cible"
            )
            texte = "GAUCHE"
        else:
            self.cible_id = self.zone_exercice.create_oval(
                x-30, y-30, x+30, y+30,
                fill='#e74c3c',
                outline='#c0392b',
                width=3,
                tags="cible"
            )
            texte = "DROIT"
        
        # Ajouter le texte
        self.zone_exercice.create_text(
            x, y,
            text=texte,
            fill='white',
            font=('Arial', 12, 'bold'),
            tags="cible"
        )
        
        # Mettre à jour l'affichage
        self.mettre_a_jour_affichage()
        
        # Programmer la prochaine cible dans 2 secondes
        if self.en_jeu and self.temps_restant > 0:
            self.apparition_id = self.fenetre.after(2000, self.creer_cible)
    
    def on_clic_gauche(self, event):
        """Gestionnaire du clic gauche"""
        if not self.en_jeu or self.exercice_actuel != "vitesse":
            return
            
        # Vérifier si on clique sur une cible
        x, y = event.x, event.y
        items = self.zone_exercice.find_overlapping(x-5, y-5, x+5, y+5)
        
        cible_trouvee = False
        for item in items:
            if "cible" in self.zone_exercice.gettags(item):
                cible_trouvee = True
                break
        
        if cible_trouvee and self.cible_id:
            if self.type_cible_actuelle == 'gauche':
                # Bon clic
                self.clics_reussis += 1
                self.cibles_gauche_restantes -= 1
                
                # Supprimer la cible
                self.zone_exercice.delete(self.cible_id)
                self.cible_id = None
                
                # Feedback visuel
                self.zone_exercice.create_text(
                    x, y-40,
                    text="✅ BRAVO !",
                    fill='#2ecc71',
                    font=('Arial', 14, 'bold'),
                    tags="feedback"
                )
                self.fenetre.after(300, lambda: self.zone_exercice.delete("feedback"))
                
                # Vérifier si toutes les cibles sont faites
                if self.cibles_gauche_restantes + self.cibles_droit_restantes == 0:
                    self.fin_exercice(reussite=True)
            else:
                # Mauvais clic
                self.clics_rate += 1
                
                # Feedback visuel
                self.zone_exercice.create_text(
                    x, y-40,
                    text="❌ MAUVAIS BOUTON !",
                    fill='#e74c3c',
                    font=('Arial', 14, 'bold'),
                    tags="feedback"
                )
                self.fenetre.after(300, lambda: self.zone_exercice.delete("feedback"))
            
            self.mettre_a_jour_affichage()
    
    def on_clic_droit(self, event):
        """Gestionnaire du clic droit"""
        if not self.en_jeu or self.exercice_actuel != "vitesse":
            return
            
        # Vérifier si on clique sur une cible
        x, y = event.x, event.y
        items = self.zone_exercice.find_overlapping(x-5, y-5, x+5, y+5)
        
        cible_trouvee = False
        for item in items:
            if "cible" in self.zone_exercice.gettags(item):
                cible_trouvee = True
                break
        
        if cible_trouvee and self.cible_id:
            if self.type_cible_actuelle == 'droit':
                # Bon clic
                self.clics_reussis += 1
                self.cibles_droit_restantes -= 1
                
                # Supprimer la cible
                self.zone_exercice.delete(self.cible_id)
                self.cible_id = None
                
                # Feedback visuel
                self.zone_exercice.create_text(
                    x, y-40,
                    text="✅ BRAVO !",
                    fill='#2ecc71',
                    font=('Arial', 14, 'bold'),
                    tags="feedback"
                )
                self.fenetre.after(300, lambda: self.zone_exercice.delete("feedback"))
                
                # Vérifier si toutes les cibles sont faites
                if self.cibles_gauche_restantes + self.cibles_droit_restantes == 0:
                    self.fin_exercice(reussite=True)
            else:
                # Mauvais clic
                self.clics_rate += 1
                
                # Feedback visuel
                self.zone_exercice.create_text(
                    x, y-40,
                    text="❌ MAUVAIS BOUTON !",
                    fill='#e74c3c',
                    font=('Arial', 14, 'bold'),
                    tags="feedback"
                )
                self.fenetre.after(300, lambda: self.zone_exercice.delete("feedback"))
            
            self.mettre_a_jour_affichage()
    
    def fin_exercice(self, reussite=False):
        """Termine l'exercice et affiche les résultats"""
        self.en_jeu = False
        
        # Supprimer la cible
        if self.cible_id:
            self.zone_exercice.delete(self.cible_id)
            self.cible_id = None
        
        # Calculer la précision
        total_clics = self.clics_reussis + self.clics_rate
        precision = 0
        if total_clics > 0:
            precision = (self.clics_reussis / total_clics) * 100
        
        # Afficher les résultats
        resultat = f"🎯 RÉSULTATS FINAUX 🎯\n\n"
        resultat += f"✅ Clics réussis : {self.clics_reussis}/10\n"
        resultat += f"❌ Clics ratés : {self.clics_rate}\n"
        resultat += f"📊 Précision : {precision:.1f}%\n\n"
        
        if self.clics_reussis == 10:
            resultat += "🏆 PARFAIT ! Tu as cliqué sur toutes les cibles ! 🏆"
        elif self.clics_reussis >= 7:
            resultat += "🌟 TRÈS BIEN ! Continue comme ça ! 🌟"
        elif self.clics_reussis >= 5:
            resultat += "👍 PAS MAL ! Encore un effort ! 👍"
        else:
            resultat += "💪 Continue à t'entraîner ! 💪"
        
        self.zone_exercice.create_text(
            400, 250,
            text=resultat,
            fill='#2c3e50',
            font=('Arial', 18, 'bold'),
            justify='center'
        )
        
        # Réinitialiser l'affichage des statistiques
        self.mettre_a_jour_affichage()
    
    def demarrer(self):
        self.fenetre.mainloop()

# Lancer le programme
if __name__ == "__main__":
    app = ApprendreSouris()
    app.demarrer()