import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import json
import os
from datetime import datetime

DB_FILE = "vie_scolaire_data.json"
LOG_FILE = "journal_vie_scolaire.log"


# ===================== GESTION DES DONNÉES =====================

def charger_donnees():
    if not os.path.exists(DB_FILE):
        return {
            "settings": {
                "etablissement": "Collège Charlemagne",
                "autosave_interval_sec": 60
            },
            "eleves": {}
        }
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Sécuriser la présence des clés
        if "settings" not in data:
            data["settings"] = {
                "etablissement": "Collège Charlemagne",
                "autosave_interval_sec": 60
            }
        if "eleves" not in data:
            data["eleves"] = {}
        return data
    except Exception:
        return {
            "settings": {
                "etablissement": "Collège Charlemagne",
                "autosave_interval_sec": 60
            },
            "eleves": {}
        }


def sauvegarder_donnees(data):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        messagebox.showerror("Erreur sauvegarde", f"Impossible de sauvegarder les données : {e}")


def log_action(message):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            ts = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            f.write(f"[{ts}] {message}\n")
    except Exception:
        pass


# ===================== CLASSE APPLICATION =====================

class VieScolaireApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Vie scolaire - Surveillant (version complète)")
        self.root.geometry("1100x650")
        self.root.resizable(False, False)

        self.data = charger_donnees()
        self.eleve_selectionne_id = None
        self.font_main = ("Segoe UI", 9)

        self.creer_menu()
        self.creer_interface()
        self.rafraichir_liste_eleves()
        self.mettre_a_jour_horloge()
        self.programmer_autosave()

    # ----------------- MENU -----------------

    def creer_menu(self):
        menubar = tk.Menu(self.root)

        menu_fichier = tk.Menu(menubar, tearoff=0)
        menu_fichier.add_command(label="Sauvegarder", command=self.action_sauvegarder)
        menu_fichier.add_command(label="Exporter TXT", command=self.action_export_txt)
        menu_fichier.add_command(label="Exporter CSV", command=self.action_export_csv)
        menu_fichier.add_separator()
        menu_fichier.add_command(label="Quitter", command=self.root.quit)
        menubar.add_cascade(label="Fichier", menu=menu_fichier)

        menu_edition = tk.Menu(menubar, tearoff=0)
        menu_edition.add_command(label="Ajouter élève", command=self.action_ajouter_eleve)
        menu_edition.add_command(label="Modifier élève", command=self.action_modifier_eleve)
        menu_edition.add_command(label="Supprimer élève", command=self.action_supprimer_eleve)
        menubar.add_cascade(label="Édition", menu=menu_edition)

        menu_vie = tk.Menu(menubar, tearoff=0)
        menu_vie.add_command(label="Marquer absence", command=self.action_marquer_absence)
        menu_vie.add_command(label="Marquer retard", command=self.action_marquer_retard)
        menu_vie.add_command(label="Ajouter sanction", command=self.action_ajouter_sanction)
        menu_vie.add_command(label="Statistiques", command=self.action_statistiques)
        menubar.add_cascade(label="Vie scolaire", menu=menu_vie)

        menu_outils = tk.Menu(menubar, tearoff=0)
        menu_outils.add_command(label="Paramètres", command=self.action_parametres)
        menubar.add_cascade(label="Outils", menu=menu_outils)

        menu_aide = tk.Menu(menubar, tearoff=0)
        menu_aide.add_command(label="À propos", command=self.action_a_propos)
        menubar.add_cascade(label="Aide", menu=menu_aide)

        self.root.config(menu=menubar)

    # ----------------- INTERFACE -----------------

    def creer_interface(self):
        # Haut
        frame_top = tk.Frame(self.root, bd=2, relief=tk.RIDGE)
        frame_top.pack(side=tk.TOP, fill=tk.X)

        self.label_titre = tk.Label(
            frame_top,
            text=f"Logiciel de vie scolaire - {self.data['settings'].get('etablissement', 'Établissement')}",
            font=("Segoe UI", 11, "bold")
        )
        self.label_titre.pack(side=tk.LEFT, padx=10, pady=5)

        self.label_datetime = tk.Label(frame_top, text="", font=("Segoe UI", 9))
        self.label_datetime.pack(side=tk.RIGHT, padx=10)

        # Gauche
        frame_left = tk.Frame(self.root, bd=2, relief=tk.RIDGE)
        frame_left.pack(side=tk.LEFT, fill=tk.Y)

        frame_actions = tk.LabelFrame(frame_left, text="Actions", font=self.font_main)
        frame_actions.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        tk.Button(frame_actions, text="Ajouter élève", width=20, command=self.action_ajouter_eleve).pack(padx=5, pady=2)
        tk.Button(frame_actions, text="Modifier élève", width=20, command=self.action_modifier_eleve).pack(padx=5, pady=2)
        tk.Button(frame_actions, text="Supprimer élève", width=20, command=self.action_supprimer_eleve).pack(padx=5, pady=2)

        tk.Label(frame_actions, text="").pack(pady=2)

        tk.Button(frame_actions, text="Marquer absence", width=20, command=self.action_marquer_absence).pack(padx=5, pady=2)
        tk.Button(frame_actions, text="Marquer retard", width=20, command=self.action_marquer_retard).pack(padx=5, pady=2)
        tk.Button(frame_actions, text="Ajouter sanction", width=20, command=self.action_ajouter_sanction).pack(padx=5, pady=2)

        tk.Label(frame_actions, text="").pack(pady=2)

        tk.Button(frame_actions, text="Consulter dossier", width=20, command=self.action_consulter_dossier).pack(padx=5, pady=2)
        tk.Button(frame_actions, text="Statistiques", width=20, command=self.action_statistiques).pack(padx=5, pady=2)

        tk.Label(frame_actions, text="").pack(pady=2)

        tk.Button(frame_actions, text="Sauvegarder", width=20, command=self.action_sauvegarder).pack(padx=5, pady=2)

        # Fiche élève
        frame_fiche = tk.LabelFrame(frame_left, text="Fiche élève", font=self.font_main)
        frame_fiche.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.var_nom = tk.StringVar()
        self.var_prenom = tk.StringVar()
        self.var_classe = tk.StringVar()
        self.var_date_naissance = tk.StringVar()
        self.var_regime = tk.StringVar()

        tk.Label(frame_fiche, text="Nom :", anchor="w").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        tk.Entry(frame_fiche, textvariable=self.var_nom, width=25).grid(row=0, column=1, padx=5, pady=2)

        tk.Label(frame_fiche, text="Prénom :", anchor="w").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        tk.Entry(frame_fiche, textvariable=self.var_prenom, width=25).grid(row=1, column=1, padx=5, pady=2)

        tk.Label(frame_fiche, text="Classe :", anchor="w").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        tk.Entry(frame_fiche, textvariable=self.var_classe, width=10).grid(row=2, column=1, padx=5, pady=2, sticky="w")

        tk.Label(frame_fiche, text="Date de naissance :", anchor="w").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        tk.Entry(frame_fiche, textvariable=self.var_date_naissance, width=12).grid(row=3, column=1, padx=5, pady=2, sticky="w")

        tk.Label(frame_fiche, text="Régime :", anchor="w").grid(row=4, column=0, sticky="w", padx=5, pady=2)
        tk.Entry(frame_fiche, textvariable=self.var_regime, width=15).grid(row=4, column=1, padx=5, pady=2, sticky="w")

        # Centre : recherche + tableau élèves
        frame_center = tk.Frame(self.root, bd=2, relief=tk.RIDGE)
        frame_center.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        frame_recherche = tk.Frame(frame_center)
        frame_recherche.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        tk.Label(frame_recherche, text="Recherche (nom/prénom) :").pack(side=tk.LEFT)
        self.var_recherche = tk.StringVar()
        entry_recherche = tk.Entry(frame_recherche, textvariable=self.var_recherche, width=30)
        entry_recherche.pack(side=tk.LEFT, padx=5)
        entry_recherche.bind("<KeyRelease>", lambda e: self.rafraichir_liste_eleves())

        tk.Label(frame_recherche, text="Classe :").pack(side=tk.LEFT, padx=5)
        self.var_filtre_classe = tk.StringVar()
        entry_classe = tk.Entry(frame_recherche, textvariable=self.var_filtre_classe, width=10)
        entry_classe.pack(side=tk.LEFT)
        entry_classe.bind("<KeyRelease>", lambda e: self.rafraichir_liste_eleves())

        tk.Label(frame_recherche, text="Min absences :").pack(side=tk.LEFT, padx=5)
        self.var_min_abs = tk.StringVar()
        entry_min_abs = tk.Entry(frame_recherche, textvariable=self.var_min_abs, width=5)
        entry_min_abs.pack(side=tk.LEFT)
        entry_min_abs.bind("<KeyRelease>", lambda e: self.rafraichir_liste_eleves())

        tk.Button(frame_recherche, text="Réinitialiser", command=self.reinitialiser_filtres).pack(side=tk.LEFT, padx=10)

        frame_liste = tk.LabelFrame(frame_center, text="Liste des élèves", font=self.font_main)
        frame_liste.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)

        colonnes = ("id", "nom", "prenom", "classe", "absences", "retards", "sanctions")
        self.tree_eleves = ttk.Treeview(frame_liste, columns=colonnes, show="headings", height=15)
        self.tree_eleves.heading("id", text="ID")
        self.tree_eleves.heading("nom", text="Nom")
        self.tree_eleves.heading("prenom", text="Prénom")
        self.tree_eleves.heading("classe", text="Classe")
        self.tree_eleves.heading("absences", text="Absences")
        self.tree_eleves.heading("retards", text="Retards")
        self.tree_eleves.heading("sanctions", text="Sanctions")

        self.tree_eleves.column("id", width=40, anchor="center")
        self.tree_eleves.column("nom", width=130)
        self.tree_eleves.column("prenom", width=130)
        self.tree_eleves.column("classe", width=70, anchor="center")
        self.tree_eleves.column("absences", width=80, anchor="center")
        self.tree_eleves.column("retards", width=80, anchor="center")
        self.tree_eleves.column("sanctions", width=80, anchor="center")

        self.tree_eleves.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.tree_eleves.bind("<<TreeviewSelect>>", self.on_select_eleve)

        scrollbar_eleves = tk.Scrollbar(frame_liste, orient=tk.VERTICAL, command=self.tree_eleves.yview)
        scrollbar_eleves.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_eleves.config(yscrollcommand=scrollbar_eleves.set)

        # Bas : historique
        frame_bottom = tk.LabelFrame(self.root, text="Historique de l'élève sélectionné", font=self.font_main)
        frame_bottom.pack(side=tk.BOTTOM, fill=tk.BOTH, padx=5, pady=5)

        frame_abs = tk.LabelFrame(frame_bottom, text="Absences", font=self.font_main)
        frame_abs.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.listbox_absences = tk.Listbox(frame_abs, width=40, height=8)
        self.listbox_absences.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar_abs = tk.Scrollbar(frame_abs, orient=tk.VERTICAL, command=self.listbox_absences.yview)
        scrollbar_abs.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox_absences.config(yscrollcommand=scrollbar_abs.set)

        frame_ret = tk.LabelFrame(frame_bottom, text="Retards", font=self.font_main)
        frame_ret.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.listbox_retards = tk.Listbox(frame_ret, width=40, height=8)
        self.listbox_retards.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar_ret = tk.Scrollbar(frame_ret, orient=tk.VERTICAL, command=self.listbox_retards.yview)
        scrollbar_ret.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox_retards.config(yscrollcommand=scrollbar_ret.set)

        frame_san = tk.LabelFrame(frame_bottom, text="Sanctions", font=self.font_main)
        frame_san.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.listbox_sanctions = tk.Listbox(frame_san, width=40, height=8)
        self.listbox_sanctions.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar_san = tk.Scrollbar(frame_san, orient=tk.VERTICAL, command=self.listbox_sanctions.yview)
        scrollbar_san.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox_sanctions.config(yscrollcommand=scrollbar_san.set)

    # ----------------- HORLOGE & AUTOSAVE -----------------

    def mettre_a_jour_horloge(self):
        maintenant = datetime.now().strftime("%d/%m/%Y - %H:%M:%S")
        self.label_datetime.config(text=maintenant)
        self.root.after(1000, self.mettre_a_jour_horloge)

    def programmer_autosave(self):
        interval = self.data["settings"].get("autosave_interval_sec", 60)
        try:
            interval = int(interval)
        except ValueError:
            interval = 60
        if interval < 10:
            interval = 10
        self.root.after(interval * 1000, self.autosave_tick)

    def autosave_tick(self):
        sauvegarder_donnees(self.data)
        log_action("Autosauvegarde effectuée")
        self.programmer_autosave()

    # ----------------- UTILITAIRES -----------------

    def reinitialiser_filtres(self):
        self.var_recherche.set("")
        self.var_filtre_classe.set("")
        self.var_min_abs.set("")
        self.rafraichir_liste_eleves()

    def rafraichir_liste_eleves(self):
        for row in self.tree_eleves.get_children():
            self.tree_eleves.delete(row)

        recherche = self.var_recherche.get().strip().lower()
        filtre_classe = self.var_filtre_classe.get().strip().lower()
        min_abs_str = self.var_min_abs.get().strip()
        min_abs = 0
        if min_abs_str.isdigit():
            min_abs = int(min_abs_str)

        eleves_trie = sorted(
            self.data["eleves"].items(),
            key=lambda x: (x[1].get("classe", ""), x[1].get("nom", ""), x[1].get("prenom", ""))
        )

        for eid, e in eleves_trie:
            nom = e.get("nom", "")
            prenom = e.get("prenom", "")
            classe = e.get("classe", "")
            nb_abs = len(e.get("absences", []))
            nb_ret = len(e.get("retards", []))
            nb_san = len(e.get("sanctions", [])) if "sanctions" in e else 0

            if recherche:
                if recherche not in nom.lower() and recherche not in prenom.lower():
                    continue

            if filtre_classe:
                if filtre_classe not in classe.lower():
                    continue

            if nb_abs < min_abs:
                continue

            self.tree_eleves.insert(
                "",
                tk.END,
                values=(eid, nom, prenom, classe, nb_abs, nb_ret, nb_san)
            )

    def vider_fiche(self):
        self.var_nom.set("")
        self.var_prenom.set("")
        self.var_classe.set("")
        self.var_date_naissance.set("")
        self.var_regime.set("")
        self.eleve_selectionne_id = None
        self.listbox_absences.delete(0, tk.END)
        self.listbox_retards.delete(0, tk.END)
        self.listbox_sanctions.delete(0, tk.END)

    def charger_fiche_eleve(self, eid):
        e = self.data["eleves"].get(eid)
        if not e:
            return
        self.eleve_selectionne_id = eid
        self.var_nom.set(e.get("nom", ""))
        self.var_prenom.set(e.get("prenom", ""))
        self.var_classe.set(e.get("classe", ""))
        self.var_date_naissance.set(e.get("date_naissance", ""))
        self.var_regime.set(e.get("regime", ""))

        self.listbox_absences.delete(0, tk.END)
        for abs_ in e.get("absences", []):
            date = abs_.get("date", "")
            motif = abs_.get("motif", "")
            self.listbox_absences.insert(tk.END, f"{date} - {motif}")

        self.listbox_retards.delete(0, tk.END)
        for ret in e.get("retards", []):
            date = ret.get("date", "")
            heure = ret.get("heure", "")
            motif = ret.get("motif", "")
            self.listbox_retards.insert(tk.END, f"{date} {heure} - {motif}")

        self.listbox_sanctions.delete(0, tk.END)
        for san in e.get("sanctions", []):
            date = san.get("date", "")
            type_s = san.get("type", "")
            motif = san.get("motif", "")
            self.listbox_sanctions.insert(tk.END, f"{date} [{type_s}] - {motif}")

    # ----------------- ÉVÉNEMENTS -----------------

    def on_select_eleve(self, event):
        selection = self.tree_eleves.selection()
        if not selection:
            return
        item = self.tree_eleves.item(selection[0])
        eid = str(item["values"][0])
        self.charger_fiche_eleve(eid)

    # ----------------- ACTIONS ÉLÈVES -----------------

    def action_ajouter_eleve(self):
        nom = self.var_nom.get().strip()
        prenom = self.var_prenom.get().strip()
        classe = self.var_classe.get().strip()
        date_n = self.var_date_naissance.get().strip()
        regime = self.var_regime.get().strip()

        if not nom or not prenom or not classe:
            messagebox.showwarning("Champs manquants", "Nom, prénom et classe sont obligatoires.")
            return

        if self.data["eleves"]:
            max_id = max(int(i) for i in self.data["eleves"].keys())
            new_id = str(max_id + 1)
        else:
            new_id = "1"

        self.data["eleves"][new_id] = {
            "nom": nom,
            "prenom": prenom,
            "classe": classe,
            "date_naissance": date_n,
            "regime": regime,
            "absences": [],
            "retards": [],
            "sanctions": []
        }

        sauvegarder_donnees(self.data)
        log_action(f"Ajout élève : {nom} {prenom} (ID {new_id}, classe {classe})")
        self.rafraichir_liste_eleves()
        messagebox.showinfo("Élève ajouté", f"Élève ajouté avec l'ID {new_id}")

    def action_modifier_eleve(self):
        if not self.eleve_selectionne_id:
            messagebox.showwarning("Aucun élève", "Veuillez sélectionner un élève dans la liste.")
            return

        nom = self.var_nom.get().strip()
        prenom = self.var_prenom.get().strip()
        classe = self.var_classe.get().strip()
        date_n = self.var_date_naissance.get().strip()
        regime = self.var_regime.get().strip()

        if not nom or not prenom or not classe:
            messagebox.showwarning("Champs manquants", "Nom, prénom et classe sont obligatoires.")
            return

        e = self.data["eleves"].get(self.eleve_selectionne_id)
        if not e:
            messagebox.showerror("Erreur", "Élève introuvable.")
            return

        e["nom"] = nom
        e["prenom"] = prenom
        e["classe"] = classe
        e["date_naissance"] = date_n
        e["regime"] = regime

        sauvegarder_donnees(self.data)
        log_action(f"Modification élève ID {self.eleve_selectionne_id}")
        self.rafraichir_liste_eleves()
        messagebox.showinfo("Modifié", "Les informations de l'élève ont été mises à jour.")

    def action_supprimer_eleve(self):
        if not self.eleve_selectionne_id:
            messagebox.showwarning("Aucun élève", "Veuillez sélectionner un élève à supprimer.")
            return

        e = self.data["eleves"].get(self.eleve_selectionne_id)
        if not e:
            messagebox.showerror("Erreur", "Élève introuvable.")
            return

        rep = messagebox.askyesno("Confirmation", f"Supprimer l'élève {e['nom']} {e['prenom']} et tout son historique ?")
        if not rep:
            return

        log_action(f"Suppression élève : {e['nom']} {e['prenom']} (ID {self.eleve_selectionne_id})")
        del self.data["eleves"][self.eleve_selectionne_id]
        sauvegarder_donnees(self.data)
        self.eleve_selectionne_id = None
        self.vider_fiche()
        self.rafraichir_liste_eleves()
        messagebox.showinfo("Supprimé", "Élève supprimé.")

    # ----------------- ACTIONS ABSENCES / RETARDS / SANCTIONS -----------------

    def action_marquer_absence(self):
        if not self.eleve_selectionne_id:
            messagebox.showwarning("Aucun élève", "Veuillez sélectionner un élève.")
            return

        fen = tk.Toplevel(self.root)
        fen.title("Marquer une absence")
        fen.geometry("320x220")
        fen.resizable(False, False)

        tk.Label(fen, text="Date (JJ/MM/AAAA) :").pack(pady=5)
        var_date = tk.StringVar(value=datetime.now().strftime("%d/%m/%Y"))
        tk.Entry(fen, textvariable=var_date).pack()

        tk.Label(fen, text="Motif :").pack(pady=5)
        var_motif = tk.StringVar()
        tk.Entry(fen, textvariable=var_motif, width=35).pack()

        def valider():
            date = var_date.get().strip()
            motif = var_motif.get().strip()
            if not date or not motif:
                messagebox.showwarning("Champs manquants", "Date et motif sont obligatoires.")
                return
            e = self.data["eleves"].get(self.eleve_selectionne_id)
            if not e:
                messagebox.showerror("Erreur", "Élève introuvable.")
                return
            e["absences"].append({"date": date, "motif": motif})
            sauvegarder_donnees(self.data)
            log_action(f"Absence pour ID {self.eleve_selectionne_id} le {date}")
            self.charger_fiche_eleve(self.eleve_selectionne_id)
            self.rafraichir_liste_eleves()
            messagebox.showinfo("OK", "Absence enregistrée.")
            fen.destroy()

        tk.Button(fen, text="Enregistrer", command=valider).pack(pady=10)

    def action_marquer_retard(self):
        if not self.eleve_selectionne_id:
            messagebox.showwarning("Aucun élève", "Veuillez sélectionner un élève.")
            return

        fen = tk.Toplevel(self.root)
        fen.title("Marquer un retard")
        fen.geometry("320x250")
        fen.resizable(False, False)

        tk.Label(fen, text="Date (JJ/MM/AAAA) :").pack(pady=5)
        var_date = tk.StringVar(value=datetime.now().strftime("%d/%m/%Y"))
        tk.Entry(fen, textvariable=var_date).pack()

        tk.Label(fen, text="Heure d'arrivée (HH:MM) :").pack(pady=5)
        var_heure = tk.StringVar()
        tk.Entry(fen, textvariable=var_heure).pack()

        tk.Label(fen, text="Motif :").pack(pady=5)
        var_motif = tk.StringVar()
        tk.Entry(fen, textvariable=var_motif, width=35).pack()

        def valider():
            date = var_date.get().strip()
            heure = var_heure.get().strip()
            motif = var_motif.get().strip()
            if not date or not heure or not motif:
                messagebox.showwarning("Champs manquants", "Tous les champs sont obligatoires.")
                return
            e = self.data["eleves"].get(self.eleve_selectionne_id)
            if not e:
                messagebox.showerror("Erreur", "Élève introuvable.")
                return
            e["retards"].append({"date": date, "heure": heure, "motif": motif})
            sauvegarder_donnees(self.data)
            log_action(f"Retard pour ID {self.eleve_selectionne_id} le {date} à {heure}")
            self.charger_fiche_eleve(self.eleve_selectionne_id)
            self.rafraichir_liste_eleves()
            messagebox.showinfo("OK", "Retard enregistré.")
            fen.destroy()

        tk.Button(fen, text="Enregistrer", command=valider).pack(pady=10)

    def action_ajouter_sanction(self):
        if not self.eleve_selectionne_id:
            messagebox.showwarning("Aucun élève", "Veuillez sélectionner un élève.")
            return

        fen = tk.Toplevel(self.root)
        fen.title("Ajouter une sanction")
        fen.geometry("340x260")
        fen.resizable(False, False)

        tk.Label(fen, text="Type de sanction :").pack(pady=5)
        var_type = tk.StringVar()
        combo_type = ttk.Combobox(fen, textvariable=var_type, values=["Punition", "Retenue", "Avertissement", "Exclusion"], state="readonly")
        combo_type.pack()

        tk.Label(fen, text="Date (JJ/MM/AAAA) :").pack(pady=5)
        var_date = tk.StringVar(value=datetime.now().strftime("%d/%m/%Y"))
        tk.Entry(fen, textvariable=var_date).pack()

        tk.Label(fen, text="Motif :").pack(pady=5)
        var_motif = tk.StringVar()
        tk.Entry(fen, textvariable=var_motif, width=35).pack()

        def valider():
            type_s = var_type.get().strip()
            date = var_date.get().strip()
            motif = var_motif.get().strip()
            if not type_s or not date or not motif:
                messagebox.showwarning("Champs manquants", "Type, date et motif sont obligatoires.")
                return
            e = self.data["eleves"].get(self.eleve_selectionne_id)
            if not e:
                messagebox.showerror("Erreur", "Élève introuvable.")
                return
            if "sanctions" not in e:
                e["sanctions"] = []
            e["sanctions"].append({"type": type_s, "date": date, "motif": motif})
            sauvegarder_donnees(self.data)
            log_action(f"Sanction {type_s} pour ID {self.eleve_selectionne_id} le {date}")
            self.charger_fiche_eleve(self.eleve_selectionne_id)
            self.rafraichir_liste_eleves()
            messagebox.showinfo("OK", "Sanction enregistrée.")
            fen.destroy()

        tk.Button(fen, text="Enregistrer", command=valider).pack(pady=10)

    # ----------------- DOSSIER & STATS -----------------

    def action_consulter_dossier(self):
        if not self.eleve_selectionne_id:
            messagebox.showwarning("Aucun élève", "Veuillez sélectionner un élève.")
            return

        e = self.data["eleves"].get(self.eleve_selectionne_id)
        if not e:
            messagebox.showerror("Erreur", "Élève introuvable.")
            return

        fen = tk.Toplevel(self.root)
        fen.title("Dossier élève")
        fen.geometry("500x500")
        fen.resizable(False, False)

        tk.Label(fen, text=f"{e.get('nom', '')} {e.get('prenom', '')}", font=("Segoe UI", 11, "bold")).pack(pady=5)
        tk.Label(fen, text=f"Classe : {e.get('classe', '')}").pack()
        tk.Label(fen, text=f"Date de naissance : {e.get('date_naissance', '')}").pack()
        tk.Label(fen, text=f"Régime : {e.get('regime', '')}").pack()

        nb_abs = len(e.get("absences", []))
        nb_ret = len(e.get("retards", []))
        nb_san = len(e.get("sanctions", []))

        tk.Label(fen, text=f"Absences : {nb_abs} | Retards : {nb_ret} | Sanctions : {nb_san}", pady=5).pack()

        frame_hist = tk.Frame(fen)
        frame_hist.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        text_hist = tk.Text(frame_hist, wrap="word")
        text_hist.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = tk.Scrollbar(frame_hist, orient=tk.VERTICAL, command=text_hist.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_hist.config(yscrollcommand=scrollbar.set)

        text_hist.insert(tk.END, "=== ABSENCES ===\n")
        for abs_ in e.get("absences", []):
            text_hist.insert(tk.END, f"- {abs_.get('date', '')} : {abs_.get('motif', '')}\n")

        text_hist.insert(tk.END, "\n=== RETARDS ===\n")
        for ret in e.get("retards", []):
            text_hist.insert(tk.END, f"- {ret.get('date', '')} {ret.get('heure', '')} : {ret.get('motif', '')}\n")

        text_hist.insert(tk.END, "\n=== SANCTIONS ===\n")
        for san in e.get("sanctions", []):
            text_hist.insert(tk.END, f"- {san.get('date', '')} [{san.get('type', '')}] : {san.get('motif', '')}\n")

        text_hist.config(state="disabled")

        def exporter_dossier():
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Fichiers texte", "*.txt")],
                title="Exporter le dossier"
            )
            if not filename:
                return
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"Dossier élève - {self.data['settings'].get('etablissement', '')}\n\n")
                    f.write(f"Nom : {e.get('nom', '')}\n")
                    f.write(f"Prénom : {e.get('prenom', '')}\n")
                    f.write(f"Classe : {e.get('classe', '')}\n")
                    f.write(f"Date de naissance : {e.get('date_naissance', '')}\n")
                    f.write(f"Régime : {e.get('regime', '')}\n\n")
                    f.write(f"Absences : {nb_abs}\nRetards : {nb_ret}\nSanctions : {nb_san}\n\n")
                    f.write("=== ABSENCES ===\n")
                    for abs_ in e.get("absences", []):
                        f.write(f"- {abs_.get('date', '')} : {abs_.get('motif', '')}\n")
                    f.write("\n=== RETARDS ===\n")
                    for ret in e.get("retards", []):
                        f.write(f"- {ret.get('date', '')} {ret.get('heure', '')} : {ret.get('motif', '')}\n")
                    f.write("\n=== SANCTIONS ===\n")
                    for san in e.get("sanctions", []):
                        f.write(f"- {san.get('date', '')} [{san.get('type', '')}] : {san.get('motif', '')}\n")
                messagebox.showinfo("Export", "Dossier exporté avec succès.")
            except Exception as ex:
                messagebox.showerror("Erreur export", f"Erreur lors de l'export : {ex}")

        tk.Button(fen, text="Exporter dossier", command=exporter_dossier).pack(pady=5)
        tk.Button(fen, text="Fermer", command=fen.destroy).pack(pady=5)

    def action_statistiques(self):
        stats_fen = tk.Toplevel(self.root)
        stats_fen.title("Statistiques")
        stats_fen.geometry("600x450")
        stats_fen.resizable(False, False)

        tk.Label(stats_fen, text="Statistiques de vie scolaire", font=("Segoe UI", 10, "bold")).pack(pady=5)

        frame_abs = tk.LabelFrame(stats_fen, text="Absences par classe")
        frame_abs.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        listbox_abs_stats = tk.Listbox(frame_abs, width=50, height=8)
        listbox_abs_stats.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar1 = tk.Scrollbar(frame_abs, orient=tk.VERTICAL, command=listbox_abs_stats.yview)
        scrollbar1.pack(side=tk.RIGHT, fill=tk.Y)
        listbox_abs_stats.config(yscrollcommand=scrollbar1.set)

        abs_par_classe = {}
        for e in self.data["eleves"].values():
            classe = e.get("classe", "NC")
            nb_abs = len(e.get("absences", []))
            abs_par_classe[classe] = abs_par_classe.get(classe, 0) + nb_abs

        for classe, nb in sorted(abs_par_classe.items()):
            listbox_abs_stats.insert(tk.END, f"Classe {classe} : {nb} absence(s)")

        frame_ret = tk.LabelFrame(stats_fen, text="Élèves les plus en retard")
        frame_ret.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        listbox_ret_stats = tk.Listbox(frame_ret, width=50, height=8)
        listbox_ret_stats.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar2 = tk.Scrollbar(frame_ret, orient=tk.VERTICAL, command=listbox_ret_stats.yview)
        scrollbar2.pack(side=tk.RIGHT, fill=tk.Y)
        listbox_ret_stats.config(yscrollcommand=scrollbar2.set)

        ret_par_eleve = []
        for e in self.data["eleves"].values():
            nb_ret = len(e.get("retards", []))
            if nb_ret > 0:
                ret_par_eleve.append((nb_ret, e.get("nom", ""), e.get("prenom", ""), e.get("classe", "")))

        ret_par_eleve.sort(reverse=True, key=lambda x: x[0])

        for nb_ret, nom, prenom, classe in ret_par_eleve[:20]:
            listbox_ret_stats.insert(tk.END, f"{nom} {prenom} ({classe}) : {nb_ret} retard(s)")

        frame_san = tk.LabelFrame(stats_fen, text="Élèves les plus sanctionnés")
        frame_san.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        listbox_san_stats = tk.Listbox(frame_san, width=50, height=8)
        listbox_san_stats.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar3 = tk.Scrollbar(frame_san, orient=tk.VERTICAL, command=listbox_san_stats.yview)
        scrollbar3.pack(side=tk.RIGHT, fill=tk.Y)
        listbox_san_stats.config(yscrollcommand=scrollbar3.set)

        san_par_eleve = []
        for e in self.data["eleves"].values():
            nb_san = len(e.get("sanctions", []))
            if nb_san > 0:
                san_par_eleve.append((nb_san, e.get("nom", ""), e.get("prenom", ""), e.get("classe", "")))

        san_par_eleve.sort(reverse=True, key=lambda x: x[0])

        for nb_san, nom, prenom, classe in san_par_eleve[:20]:
            listbox_san_stats.insert(tk.END, f"{nom} {prenom} ({classe}) : {nb_san} sanction(s)")

    # ----------------- PARAMÈTRES, EXPORT, AIDE -----------------

    def action_parametres(self):
        fen = tk.Toplevel(self.root)
        fen.title("Paramètres")
        fen.geometry("350x200")
        fen.resizable(False, False)

        tk.Label(fen, text="Nom de l'établissement :").pack(pady=5)
        var_eta = tk.StringVar(value=self.data["settings"].get("etablissement", ""))
        tk.Entry(fen, textvariable=var_eta, width=35).pack()

        tk.Label(fen, text="Intervalle autosauvegarde (sec) :").pack(pady=5)
        var_auto = tk.StringVar(value=str(self.data["settings"].get("autosave_interval_sec", 60)))
        tk.Entry(fen, textvariable=var_auto, width=10).pack()

        def valider():
            eta = var_eta.get().strip()
            auto = var_auto.get().strip()
            if not eta:
                messagebox.showwarning("Champs manquants", "Le nom de l'établissement est obligatoire.")
                return
            if not auto.isdigit():
                messagebox.showwarning("Valeur invalide", "L'intervalle doit être un nombre de secondes.")
                return
            self.data["settings"]["etablissement"] = eta
            self.data["settings"]["autosave_interval_sec"] = int(auto)
            sauvegarder_donnees(self.data)
            self.label_titre.config(text=f"Logiciel de vie scolaire - {eta}")
            log_action("Modification des paramètres")
            messagebox.showinfo("Paramètres", "Paramètres enregistrés.")
            fen.destroy()

        tk.Button(fen, text="Enregistrer", command=valider).pack(pady=10)

    def action_export_txt(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Fichiers texte", "*.txt")],
            title="Exporter les données (TXT)"
        )
        if not filename:
            return
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"Export vie scolaire - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write(f"{self.data['settings'].get('etablissement', '')}\n\n")
                for eid, e in sorted(self.data["eleves"].items(), key=lambda x: (x[1].get("classe", ""), x[1].get("nom", ""))):
                    f.write(f"[{eid}] {e.get('nom', '')} {e.get('prenom', '')} - {e.get('classe', '')}\n")
                    f.write(f"  Absences : {len(e.get('absences', []))} | Retards : {len(e.get('retards', []))} | Sanctions : {len(e.get('sanctions', []))}\n\n")
            log_action("Export TXT")
            messagebox.showinfo("Export", "Export TXT réalisé.")
        except Exception as ex:
            messagebox.showerror("Erreur export", f"Erreur lors de l'export TXT : {ex}")

    def action_export_csv(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Fichiers CSV", "*.csv")],
            title="Exporter les données (CSV)"
        )
        if not filename:
            return
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("ID;Nom;Prénom;Classe;Absences;Retards;Sanctions\n")
                for eid, e in sorted(self.data["eleves"].items(), key=lambda x: (x[1].get("classe", ""), x[1].get("nom", ""))):
                    nb_abs = len(e.get("absences", []))
                    nb_ret = len(e.get("retards", []))
                    nb_san = len(e.get("sanctions", []))
                    f.write(f"{eid};{e.get('nom', '')};{e.get('prenom', '')};{e.get('classe', '')};{nb_abs};{nb_ret};{nb_san}\n")
            log_action("Export CSV")
            messagebox.showinfo("Export", "Export CSV réalisé.")
        except Exception as ex:
            messagebox.showerror("Erreur export", f"Erreur lors de l'export CSV : {ex}")

    def action_sauvegarder(self):
        sauvegarder_donnees(self.data)
        log_action("Sauvegarde manuelle")
        messagebox.showinfo("Sauvegarde", "Données sauvegardées.")

    def action_a_propos(self):
        messagebox.showinfo(
            "À propos",
            "Logiciel de vie scolaire (prototype)\n"
            "Gestion élèves, absences, retards, sanctions\n"
            "Style administratif simple."
        )


# ===================== MAIN =====================

def main():
    root = tk.Tk()
    app = VieScolaireApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
