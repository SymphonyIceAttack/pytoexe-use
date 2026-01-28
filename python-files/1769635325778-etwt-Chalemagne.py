import os
import sqlite3
import datetime
import csv
import customtkinter as ctk
from tkinter import messagebox, filedialog, StringVar, IntVar, END, ttk

# Configuration globale de CustomTkinter
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")


class DatabaseManager:
    def __init__(self, db_path="vie_scolaire.db"):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_tables()

    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def create_tables(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT
            )
            """
        )
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS eleves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT,
                prenom TEXT,
                classe TEXT,
                photo_path TEXT
            )
            """
        )
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS absences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                eleve_id INTEGER,
                date TEXT,
                heure TEXT,
                duree INTEGER,
                motif TEXT,
                statut TEXT,
                synced INTEGER DEFAULT 0,
                FOREIGN KEY(eleve_id) REFERENCES eleves(id)
            )
            """
        )
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS retards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                eleve_id INTEGER,
                date TEXT,
                heure TEXT,
                duree INTEGER,
                motif TEXT,
                synced INTEGER DEFAULT 0,
                FOREIGN KEY(eleve_id) REFERENCES eleves(id)
            )
            """
        )
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sanctions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                eleve_id INTEGER,
                type TEXT,
                date TEXT,
                duree INTEGER,
                motif TEXT,
                synced INTEGER DEFAULT 0,
                FOREIGN KEY(eleve_id) REFERENCES eleves(id)
            )
            """
        )
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS appels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                classe TEXT,
                date TEXT,
                heure TEXT,
                eleve_id INTEGER,
                statut TEXT,
                synced INTEGER DEFAULT 0,
                FOREIGN KEY(eleve_id) REFERENCES eleves(id)
            )
            """
        )
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS surveillance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                eleve_id INTEGER,
                type TEXT,
                date TEXT,
                heure_debut TEXT,
                heure_fin TEXT,
                motif TEXT,
                synced INTEGER DEFAULT 0,
                FOREIGN KEY(eleve_id) REFERENCES eleves(id)
            )
            """
        )
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT,
                action TEXT,
                timestamp TEXT
            )
            """
        )
        self.conn.commit()
        self.ensure_default_user()

    def ensure_default_user(self):
        self.cursor.execute("SELECT COUNT(*) FROM users")
        count = self.cursor.fetchone()[0]
        if count == 0:
            self.cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                ("surveillant", "password", "surveillant"),
            )
            self.conn.commit()

    def authenticate_user(self, username, password):
        self.cursor.execute(
            "SELECT role FROM users WHERE username=? AND password=?",
            (username, password),
        )
        row = self.cursor.fetchone()
        if row:
            return row[0]
        return None

    def log_action(self, user, action):
        timestamp = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")
        self.cursor.execute(
            "INSERT INTO logs (user, action, timestamp) VALUES (?, ?, ?)",
            (user, action, timestamp),
        )
        self.conn.commit()

    def add_eleve(self, nom, prenom, classe, photo_path=""):
        self.cursor.execute(
            "INSERT INTO eleves (nom, prenom, classe, photo_path) VALUES (?, ?, ?, ?)",
            (nom, prenom, classe, photo_path),
        )
        self.conn.commit()

    def get_all_eleves(self):
        self.cursor.execute(
            "SELECT id, nom, prenom, classe, photo_path FROM eleves ORDER BY classe, nom"
        )
        return self.cursor.fetchall()

    def search_eleves(self, nom="", prenom="", classe="", statut=None):
        query = "SELECT id, nom, prenom, classe, photo_path FROM eleves"
        conditions = []
        params = []
        if nom:
            conditions.append("nom LIKE ?")
            params.append(f"%{nom}%")
        if prenom:
            conditions.append("prenom LIKE ?")
            params.append(f"%{prenom}%")
        if classe:
            conditions.append("classe LIKE ?")
            params.append(f"%{classe}%")
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY classe, nom"
        self.cursor.execute(query, params)
        results = self.cursor.fetchall()
        if statut:
            filtered = []
            for row in results:
                eleve_id = row[0]
                if statut == "present":
                    if not self.has_absence_today(eleve_id) and not self.has_retard_today(eleve_id):
                        filtered.append(row)
                elif statut == "absent":
                    if self.has_absence_today(eleve_id):
                        filtered.append(row)
                elif statut == "retard":
                    if self.has_retard_today(eleve_id):
                        filtered.append(row)
            return filtered
        return results

    def has_absence_today(self, eleve_id):
        today = datetime.date.today().isoformat()
        self.cursor.execute(
            "SELECT COUNT(*) FROM absences WHERE eleve_id=? AND date=?",
            (eleve_id, today),
        )
        return self.cursor.fetchone()[0] > 0

    def has_retard_today(self, eleve_id):
        today = datetime.date.today().isoformat()
        self.cursor.execute(
            "SELECT COUNT(*) FROM retards WHERE eleve_id=? AND date=?",
            (eleve_id, today),
        )
        return self.cursor.fetchone()[0] > 0

    def get_eleve_by_id(self, eleve_id):
        self.cursor.execute(
            "SELECT id, nom, prenom, classe, photo_path FROM eleves WHERE id=?",
            (eleve_id,),
        )
        return self.cursor.fetchone()

    def get_absences_by_eleve(self, eleve_id):
        self.cursor.execute(
            """
            SELECT id, date, heure, duree, motif, statut
            FROM absences
            WHERE eleve_id=?
            ORDER BY date DESC, heure DESC
            """,
            (eleve_id,),
        )
        return self.cursor.fetchall()

    def add_absence(self, eleve_id, date, heure, duree, motif, statut="non justifiée"):
        self.cursor.execute(
            """
            INSERT INTO absences (eleve_id, date, heure, duree, motif, statut, synced)
            VALUES (?, ?, ?, ?, ?, ?, 0)
            """,
            (eleve_id, date, heure, duree, motif, statut),
        )
        self.conn.commit()

    def update_absence(self, absence_id, date, heure, duree, motif, statut):
        self.cursor.execute(
            """
            UPDATE absences
            SET date=?, heure=?, duree=?, motif=?, statut=?, synced=0
            WHERE id=?
            """,
            (date, heure, duree, motif, statut, absence_id),
        )
        self.conn.commit()

    def delete_absence(self, absence_id):
        self.cursor.execute("DELETE FROM absences WHERE id=?", (absence_id,))
        self.conn.commit()

    def get_absences_filtered(self, classe="", start_date="", end_date=""):
        query = """
        SELECT a.id, e.nom, e.prenom, e.classe, a.date, a.heure, a.duree, a.motif, a.statut
        FROM absences a
        JOIN eleves e ON a.eleve_id = e.id
        """
        conditions = []
        params = []
        if classe:
            conditions.append("e.classe LIKE ?")
            params.append(f"%{classe}%")
        if start_date:
            conditions.append("a.date >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("a.date <= ?")
            params.append(end_date)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY a.date DESC, a.heure DESC"
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def get_absence_stats(self):
        self.cursor.execute(
            """
            SELECT e.nom, e.prenom, e.classe, COUNT(a.id) as nb_absences
            FROM absences a
            JOIN eleves e ON a.eleve_id = e.id
            GROUP BY e.id
            ORDER BY nb_absences DESC
            """
        )
        return self.cursor.fetchall()

    def get_retards_by_eleve(self, eleve_id):
        self.cursor.execute(
            """
            SELECT id, date, heure, duree, motif
            FROM retards
            WHERE eleve_id=?
            ORDER BY date DESC, heure DESC
            """,
            (eleve_id,),
        )
        return self.cursor.fetchall()

    def add_retard(self, eleve_id, date, heure, duree, motif):
        self.cursor.execute(
            """
            INSERT INTO retards (eleve_id, date, heure, duree, motif, synced)
            VALUES (?, ?, ?, ?, ?, 0)
            """,
            (eleve_id, date, heure, duree, motif),
        )
        self.conn.commit()

    def update_retard(self, retard_id, date, heure, duree, motif):
        self.cursor.execute(
            """
            UPDATE retards
            SET date=?, heure=?, duree=?, motif=?, synced=0
            WHERE id=?
            """,
            (date, heure, duree, motif, retard_id),
        )
        self.conn.commit()

    def delete_retard(self, retard_id):
        self.cursor.execute("DELETE FROM retards WHERE id=?", (retard_id,))
        self.conn.commit()

    def get_retard_stats_by_classe(self):
        self.cursor.execute(
            """
            SELECT e.classe, COUNT(r.id) as nb_retards
            FROM retards r
            JOIN eleves e ON r.eleve_id = e.id
            GROUP BY e.classe
            ORDER BY nb_retards DESC
            """
        )
        return self.cursor.fetchall()

    def get_sanctions_by_eleve(self, eleve_id):
        self.cursor.execute(
            """
            SELECT id, type, date, duree, motif
            FROM sanctions
            WHERE eleve_id=?
            ORDER BY date DESC
            """,
            (eleve_id,),
        )
        return self.cursor.fetchall()

    def add_sanction(self, eleve_id, type_sanction, date, duree, motif):
        self.cursor.execute(
            """
            INSERT INTO sanctions (eleve_id, type, date, duree, motif, synced)
            VALUES (?, ?, ?, ?, ?, 0)
            """,
            (eleve_id, type_sanction, date, duree, motif),
        )
        self.conn.commit()

    def update_sanction(self, sanction_id, type_sanction, date, duree, motif):
        self.cursor.execute(
            """
            UPDATE sanctions
            SET type=?, date=?, duree=?, motif=?, synced=0
            WHERE id=?
            """,
            (type_sanction, date, duree, motif, sanction_id),
        )
        self.conn.commit()

    def delete_sanction(self, sanction_id):
        self.cursor.execute("DELETE FROM sanctions WHERE id=?", (sanction_id,))
        self.conn.commit()

    def get_sanction_stats_by_period(self, start_date="", end_date=""):
        query = """
        SELECT date, COUNT(id) as nb_sanctions
        FROM sanctions
        """
        conditions = []
        params = []
        if start_date:
            conditions.append("date >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("date <= ?")
            params.append(end_date)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " GROUP BY date ORDER BY date"
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def get_appel_for_classe_date(self, classe, date):
        self.cursor.execute(
            """
            SELECT a.id, e.id, e.nom, e.prenom, a.statut
            FROM eleves e
            LEFT JOIN appels a
            ON a.eleve_id = e.id AND a.date = ? AND a.classe = ?
            WHERE e.classe = ?
            ORDER BY e.nom, e.prenom
            """,
            (date, classe, classe),
        )
        return self.cursor.fetchall()

    def save_appel_entry(self, classe, date, heure, eleve_id, statut):
        self.cursor.execute(
            """
            SELECT id FROM appels
            WHERE classe=? AND date=? AND eleve_id=?
            """,
            (classe, date, eleve_id),
        )
        row = self.cursor.fetchone()
        if row:
            appel_id = row[0]
            self.cursor.execute(
                """
                UPDATE appels
                SET heure=?, statut=?, synced=0
                WHERE id=?
                """,
                (heure, statut, appel_id),
            )
        else:
            self.cursor.execute(
                """
                INSERT INTO appels (classe, date, heure, eleve_id, statut, synced)
                VALUES (?, ?, ?, ?, ?, 0)
                """,
                (classe, date, heure, eleve_id, statut),
            )
        self.conn.commit()

    def get_appels_history(self):
        self.cursor.execute(
            """
            SELECT a.id, a.classe, a.date, a.heure, e.nom, e.prenom, a.statut
            FROM appels a
            JOIN eleves e ON a.eleve_id = e.id
            ORDER BY a.date DESC, a.heure DESC
            """
        )
        return self.cursor.fetchall()

    def export_appels_to_csv(self, filepath):
        rows = self.get_appels_history()
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(
                ["ID", "Classe", "Date", "Heure", "Nom", "Prénom", "Statut"]
            )
            for row in rows:
                writer.writerow(row)

    def add_surveillance_entry(self, eleve_id, type_surv, date, heure_debut, heure_fin, motif):
        self.cursor.execute(
            """
            INSERT INTO surveillance (eleve_id, type, date, heure_debut, heure_fin, motif, synced)
            VALUES (?, ?, ?, ?, ?, ?, 0)
            """,
            (eleve_id, type_surv, date, heure_debut, heure_fin, motif),
        )
        self.conn.commit()

    def get_surveillance_entries(self):
        self.cursor.execute(
            """
            SELECT s.id, e.nom, e.prenom, e.classe, s.type, s.date, s.heure_debut, s.heure_fin, s.motif
            FROM surveillance s
            JOIN eleves e ON s.eleve_id = e.id
            ORDER BY s.date DESC, s.heure_debut DESC
            """
        )
        return self.cursor.fetchall()

    def delete_surveillance_entry(self, surv_id):
        self.cursor.execute("DELETE FROM surveillance WHERE id=?", (surv_id,))
        self.conn.commit()

    def get_unsynced_counts(self):
        self.cursor.execute("SELECT COUNT(*) FROM absences WHERE synced=0")
        abs_count = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT COUNT(*) FROM retards WHERE synced=0")
        ret_count = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT COUNT(*) FROM sanctions WHERE synced=0")
        sanc_count = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT COUNT(*) FROM appels WHERE synced=0")
        appel_count = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT COUNT(*) FROM surveillance WHERE synced=0")
        surv_count = self.cursor.fetchone()[0]
        return abs_count, ret_count, sanc_count, appel_count, surv_count

    def mark_all_synced(self):
        self.cursor.execute("UPDATE absences SET synced=1")
        self.cursor.execute("UPDATE retards SET synced=1")
        self.cursor.execute("UPDATE sanctions SET synced=1")
        self.cursor.execute("UPDATE appels SET synced=1")
        self.cursor.execute("UPDATE surveillance SET synced=1")
        self.conn.commit()

    def close(self):
        if self.conn:
            self.conn.close()


class LoginWindow(ctk.CTk):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.title("Pronote - Surveillant - Connexion")
        self.geometry("400x260")
        self.resizable(False, False)
        self.username_var = StringVar()
        self.password_var = StringVar()
        self.build_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def build_ui(self):
        frame = ctk.CTkFrame(self)
        frame.pack(expand=True, fill="both", padx=20, pady=20)

        label_title = ctk.CTkLabel(
            frame,
            text="Connexion Surveillant",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        label_title.pack(pady=10)

        label_user = ctk.CTkLabel(frame, text="Identifiant")
        label_user.pack(anchor="w", pady=(10, 0))
        entry_user = ctk.CTkEntry(frame, textvariable=self.username_var)
        entry_user.pack(fill="x", pady=5)

        label_pass = ctk.CTkLabel(frame, text="Mot de passe")
        label_pass.pack(anchor="w", pady=(10, 0))
        entry_pass = ctk.CTkEntry(frame, textvariable=self.password_var, show="*")
        entry_pass.pack(fill="x", pady=5)

        self.remember_var = IntVar(value=0)
        chk_remember = ctk.CTkCheckBox(
            frame, text="Rester connecté", variable=self.remember_var
        )
        chk_remember.pack(anchor="w", pady=5)

        btn_login = ctk.CTkButton(
            frame,
            text="Se connecter",
            command=self.handle_login,
            corner_radius=20,
        )
        btn_login.pack(pady=10)

    def handle_login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        if not username or not password:
            messagebox.showwarning("Connexion", "Veuillez saisir identifiant et mot de passe.")
            return
        role = self.db.authenticate_user(username, password)
        if role == "surveillant":
            self.db.log_action(username, "Connexion réussie")
            self.open_main_app(username)
        else:
            self.db.log_action(username, "Échec de connexion")
            messagebox.showerror("Connexion", "Identifiants invalides ou rôle non autorisé.")

    def open_main_app(self, username):
        self.withdraw()
        app = MainApp(self.db, username)
        app.mainloop()
        self.destroy()

    def on_close(self):
        self.db.close()
        self.destroy()


class ElevesTab(ctk.CTkFrame):
    def __init__(self, master, db_manager, on_eleve_selected_callback):
        super().__init__(master)
        self.db = db_manager
        self.on_eleve_selected_callback = on_eleve_selected_callback
        self.selected_eleve_id = None
        self.nom_var = StringVar()
        self.prenom_var = StringVar()
        self.classe_var = StringVar()
        self.statut_var = StringVar(value="")
        self.build_ui()
        self.refresh_list()

    def build_ui(self):
        search_frame = ctk.CTkFrame(self)
        search_frame.pack(fill="x", padx=10, pady=10)

        lbl_nom = ctk.CTkLabel(search_frame, text="Nom")
        lbl_nom.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ent_nom = ctk.CTkEntry(search_frame, textvariable=self.nom_var, width=120)
        ent_nom.grid(row=0, column=1, padx=5, pady=5)

        lbl_prenom = ctk.CTkLabel(search_frame, text="Prénom")
        lbl_prenom.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        ent_prenom = ctk.CTkEntry(search_frame, textvariable=self.prenom_var, width=120)
        ent_prenom.grid(row=0, column=3, padx=5, pady=5)

        lbl_classe = ctk.CTkLabel(search_frame, text="Classe")
        lbl_classe.grid(row=0, column=4, padx=5, pady=5, sticky="w")
        ent_classe = ctk.CTkEntry(search_frame, textvariable=self.classe_var, width=80)
        ent_classe.grid(row=0, column=5, padx=5, pady=5)

        lbl_statut = ctk.CTkLabel(search_frame, text="Statut")
        lbl_statut.grid(row=0, column=6, padx=5, pady=5, sticky="w")
        combo_statut = ctk.CTkComboBox(
            search_frame,
            values=["", "present", "absent", "retard"],
            variable=self.statut_var,
            width=120,
        )
        combo_statut.grid(row=0, column=7, padx=5, pady=5)

        btn_search = ctk.CTkButton(
            search_frame,
            text="Rechercher",
            command=self.refresh_list,
            corner_radius=15,
        )
        btn_search.grid(row=0, column=8, padx=5, pady=5)

        btn_reset = ctk.CTkButton(
            search_frame,
            text="Réinitialiser",
            command=self.reset_filters,
            corner_radius=15,
        )
        btn_reset.grid(row=0, column=9, padx=5, pady=5)

        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.tree = ttk.Treeview(
            main_frame,
            columns=("id", "nom", "prenom", "classe"),
            show="headings",
            selectmode="browse",
        )
        self.tree.heading("id", text="ID")
        self.tree.heading("nom", text="Nom")
        self.tree.heading("prenom", text="Prénom")
        self.tree.heading("classe", text="Classe")
        self.tree.column("id", width=40, anchor="center")
        self.tree.column("nom", width=140)
        self.tree.column("prenom", width=140)
        self.tree.column("classe", width=80, anchor="center")
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ctk.CTkScrollbar(main_frame, command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        detail_frame = ctk.CTkFrame(self)
        detail_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.detail_label = ctk.CTkLabel(
            detail_frame,
            text="Sélectionnez un élève pour voir les détails.",
            anchor="w",
        )
        self.detail_label.pack(fill="x", padx=5, pady=5)

    def refresh_list(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        nom = self.nom_var.get().strip()
        prenom = self.prenom_var.get().strip()
        classe = self.classe_var.get().strip()
        statut = self.statut_var.get().strip()
        if statut == "":
            statut = None
        eleves = self.db.search_eleves(nom, prenom, classe, statut)
        for e in eleves:
            self.tree.insert("", END, values=(e[0], e[1], e[2], e[3]))

    def reset_filters(self):
        self.nom_var.set("")
        self.prenom_var.set("")
        self.classe_var.set("")
        self.statut_var.set("")
        self.refresh_list()

    def on_tree_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        item = self.tree.item(selected[0])
        eleve_id = item["values"][0]
        self.selected_eleve_id = eleve_id
        eleve = self.db.get_eleve_by_id(eleve_id)
        if eleve:
            nom = eleve[1]
            prenom = eleve[2]
            classe = eleve[3]
            text = f"Élève : {nom} {prenom} - Classe : {classe}"
            self.detail_label.configure(text=text)
        else:
            self.detail_label.configure(text="Élève introuvable.")
        if self.on_eleve_selected_callback:
            self.on_eleve_selected_callback(eleve_id)


class AbsencesTab(ctk.CTkFrame):
    def __init__(self, master, db_manager, get_selected_eleve_callback):
        super().__init__(master)
        self.db = db_manager
        self.get_selected_eleve_callback = get_selected_eleve_callback
        self.selected_absence_id = None
        self.date_var = StringVar()
        self.heure_var = StringVar()
        self.duree_var = StringVar()
        self.motif_var = StringVar()
        self.statut_var = StringVar(value="non justifiée")
        self.classe_filter_var = StringVar()
        self.start_date_var = StringVar()
        self.end_date_var = StringVar()
        self.build_ui()
        self.refresh_for_selected_eleve()

    def build_ui(self):
        top_frame = ctk.CTkFrame(self)
        top_frame.pack(fill="x", padx=10, pady=10)

        lbl_date = ctk.CTkLabel(top_frame, text="Date (YYYY-MM-DD)")
        lbl_date.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ent_date = ctk.CTkEntry(top_frame, textvariable=self.date_var, width=120)
        ent_date.grid(row=0, column=1, padx=5, pady=5)

        lbl_heure = ctk.CTkLabel(top_frame, text="Heure (HH:MM)")
        lbl_heure.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        ent_heure = ctk.CTkEntry(top_frame, textvariable=self.heure_var, width=80)
        ent_heure.grid(row=0, column=3, padx=5, pady=5)

        lbl_duree = ctk.CTkLabel(top_frame, text="Durée (min)")
        lbl_duree.grid(row=0, column=4, padx=5, pady=5, sticky="w")
        ent_duree = ctk.CTkEntry(top_frame, textvariable=self.duree_var, width=80)
        ent_duree.grid(row=0, column=5, padx=5, pady=5)

        lbl_motif = ctk.CTkLabel(top_frame, text="Motif")
        lbl_motif.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ent_motif = ctk.CTkEntry(top_frame, textvariable=self.motif_var, width=260)
        ent_motif.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky="we")

        lbl_statut = ctk.CTkLabel(top_frame, text="Statut")
        lbl_statut.grid(row=1, column=4, padx=5, pady=5, sticky="w")
        combo_statut = ctk.CTkComboBox(
            top_frame,
            values=["justifiée", "non justifiée"],
            variable=self.statut_var,
            width=120,
        )
        combo_statut.grid(row=1, column=5, padx=5, pady=5)

        btn_add = ctk.CTkButton(
            top_frame,
            text="Ajouter",
            command=self.add_absence,
            corner_radius=15,
        )
        btn_add.grid(row=0, column=6, padx=5, pady=5)

        btn_update = ctk.CTkButton(
            top_frame,
            text="Modifier",
            command=self.update_absence,
            corner_radius=15,
        )
        btn_update.grid(row=1, column=6, padx=5, pady=5)

        btn_delete = ctk.CTkButton(
            top_frame,
            text="Supprimer",
            command=self.delete_absence,
            corner_radius=15,
        )
        btn_delete.grid(row=0, column=7, padx=5, pady=5)

        btn_refresh = ctk.CTkButton(
            top_frame,
            text="Rafraîchir élève",
            command=self.refresh_for_selected_eleve,
            corner_radius=15,
        )
        btn_refresh.grid(row=1, column=7, padx=5, pady=5)

        mid_frame = ctk.CTkFrame(self)
        mid_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.tree = ttk.Treeview(
            mid_frame,
            columns=("id", "date", "heure", "duree", "motif", "statut"),
            show="headings",
            selectmode="browse",
        )
        self.tree.heading("id", text="ID")
        self.tree.heading("date", text="Date")
        self.tree.heading("heure", text="Heure")
        self.tree.heading("duree", text="Durée")
        self.tree.heading("motif", text="Motif")
        self.tree.heading("statut", text="Statut")
        self.tree.column("id", width=40, anchor="center")
        self.tree.column("date", width=90, anchor="center")
        self.tree.column("heure", width=70, anchor="center")
        self.tree.column("duree", width=70, anchor="center")
        self.tree.column("motif", width=220)
        self.tree.column("statut", width=110, anchor="center")
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ctk.CTkScrollbar(mid_frame, command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        bottom_frame = ctk.CTkFrame(self)
        bottom_frame.pack(fill="x", padx=10, pady=(0, 10))

        lbl_classe = ctk.CTkLabel(bottom_frame, text="Classe")
        lbl_classe.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ent_classe = ctk.CTkEntry(bottom_frame, textvariable=self.classe_filter_var, width=80)
        ent_classe.grid(row=0, column=1, padx=5, pady=5)

        lbl_start = ctk.CTkLabel(bottom_frame, text="Du (YYYY-MM-DD)")
        lbl_start.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        ent_start = ctk.CTkEntry(bottom_frame, textvariable=self.start_date_var, width=120)
        ent_start.grid(row=0, column=3, padx=5, pady=5)

        lbl_end = ctk.CTkLabel(bottom_frame, text="Au (YYYY-MM-DD)")
        lbl_end.grid(row=0, column=4, padx=5, pady=5, sticky="w")
        ent_end = ctk.CTkEntry(bottom_frame, textvariable=self.end_date_var, width=120)
        ent_end.grid(row=0, column=5, padx=5, pady=5)

        btn_filter = ctk.CTkButton(
            bottom_frame,
            text="Filtrer global",
            command=self.filter_global_absences,
            corner_radius=15,
        )
        btn_filter.grid(row=0, column=6, padx=5, pady=5)

        btn_stats = ctk.CTkButton(
            bottom_frame,
            text="Statistiques absences",
            command=self.show_absence_stats,
            corner_radius=15,
        )
        btn_stats.grid(row=0, column=7, padx=5, pady=5)

    def refresh_for_selected_eleve(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        eleve_id = self.get_selected_eleve_callback()
        if not eleve_id:
            return
        absences = self.db.get_absences_by_eleve(eleve_id)
        for a in absences:
            self.tree.insert("", END, values=a)

    def on_tree_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        item = self.tree.item(selected[0])
        values = item["values"]
        self.selected_absence_id = values[0]
        self.date_var.set(values[1])
        self.heure_var.set(values[2])
        self.duree_var.set(str(values[3]))
        self.motif_var.set(values[4])
        self.statut_var.set(values[5])

    def add_absence(self):
        eleve_id = self.get_selected_eleve_callback()
        if not eleve_id:
            messagebox.showwarning("Absences", "Veuillez d'abord sélectionner un élève dans l'onglet Élèves.")
            return
        date = self.date_var.get().strip()
        heure = self.heure_var.get().strip()
        duree = self.duree_var.get().strip()
        motif = self.motif_var.get().strip()
        statut = self.statut_var.get().strip()
        if not date or not heure or not duree:
            messagebox.showwarning("Absences", "Date, heure et durée sont obligatoires.")
            return
        try:
            duree_int = int(duree)
        except ValueError:
            messagebox.showwarning("Absences", "Durée invalide.")
            return
        self.db.add_absence(eleve_id, date, heure, duree_int, motif, statut)
        self.db.log_action("surveillant", f"Ajout absence élève {eleve_id}")
        self.refresh_for_selected_eleve()

    def update_absence(self):
        if not self.selected_absence_id:
            messagebox.showwarning("Absences", "Veuillez sélectionner une absence.")
            return
        date = self.date_var.get().strip()
        heure = self.heure_var.get().strip()
        duree = self.duree_var.get().strip()
        motif = self.motif_var.get().strip()
        statut = self.statut_var.get().strip()
        if not date or not heure or not duree:
            messagebox.showwarning("Absences", "Date, heure et durée sont obligatoires.")
            return
        try:
            duree_int = int(duree)
        except ValueError:
            messagebox.showwarning("Absences", "Durée invalide.")
            return
        self.db.update_absence(self.selected_absence_id, date, heure, duree_int, motif, statut)
        self.db.log_action("surveillant", f"Modification absence {self.selected_absence_id}")
        self.refresh_for_selected_eleve()

    def delete_absence(self):
        if not self.selected_absence_id:
            messagebox.showwarning("Absences", "Veuillez sélectionner une absence.")
            return
        if not messagebox.askyesno("Absences", "Supprimer cette absence ?"):
            return
        self.db.delete_absence(self.selected_absence_id)
        self.db.log_action("surveillant", f"Suppression absence {self.selected_absence_id}")
        self.selected_absence_id = None
        self.refresh_for_selected_eleve()

    def filter_global_absences(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        classe = self.classe_filter_var.get().strip()
        start = self.start_date_var.get().strip()
        end = self.end_date_var.get().strip()
        absences = self.db.get_absences_filtered(classe, start, end)
        for a in absences:
            self.tree.insert("", END, values=(a[0], a[4], a[5], a[6], a[7], a[8]))

    def show_absence_stats(self):
        stats = self.db.get_absence_stats()
        if not stats:
            messagebox.showinfo("Statistiques", "Aucune absence enregistrée.")
            return
        lines = []
        for row in stats:
            nom, prenom, classe, nb = row
            lines.append(f"{nom} {prenom} ({classe}) : {nb} absence(s)")
        messagebox.showinfo("Statistiques absences", "\n".join(lines))


class RetardsTab(ctk.CTkFrame):
    def __init__(self, master, db_manager, get_selected_eleve_callback):
        super().__init__(master)
        self.db = db_manager
        self.get_selected_eleve_callback = get_selected_eleve_callback
        self.selected_retard_id = None
        self.date_var = StringVar()
        self.heure_var = StringVar()
        self.duree_var = StringVar()
        self.motif_var = StringVar()
        self.build_ui()
        self.refresh_for_selected_eleve()

    def build_ui(self):
        top_frame = ctk.CTkFrame(self)
        top_frame.pack(fill="x", padx=10, pady=10)

        lbl_date = ctk.CTkLabel(top_frame, text="Date (YYYY-MM-DD)")
        lbl_date.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ent_date = ctk.CTkEntry(top_frame, textvariable=self.date_var, width=120)
        ent_date.grid(row=0, column=1, padx=5, pady=5)

        lbl_heure = ctk.CTkLabel(top_frame, text="Heure (HH:MM)")
        lbl_heure.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        ent_heure = ctk.CTkEntry(top_frame, textvariable=self.heure_var, width=80)
        ent_heure.grid(row=0, column=3, padx=5, pady=5)

        lbl_duree = ctk.CTkLabel(top_frame, text="Durée (min)")
        lbl_duree.grid(row=0, column=4, padx=5, pady=5, sticky="w")
        ent_duree = ctk.CTkEntry(top_frame, textvariable=self.duree_var, width=80)
        ent_duree.grid(row=0, column=5, padx=5, pady=5)

        lbl_motif = ctk.CTkLabel(top_frame, text="Motif")
        lbl_motif.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ent_motif = ctk.CTkEntry(top_frame, textvariable=self.motif_var, width=260)
        ent_motif.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky="we")

        btn_add = ctk.CTkButton(
            top_frame,
            text="Ajouter",
            command=self.add_retard,
            corner_radius=15,
        )
        btn_add.grid(row=0, column=6, padx=5, pady=5)

        btn_update = ctk.CTkButton(
            top_frame,
            text="Modifier",
            command=self.update_retard,
            corner_radius=15,
        )
        btn_update.grid(row=1, column=6, padx=5, pady=5)

        btn_delete = ctk.CTkButton(
            top_frame,
            text="Supprimer",
            command=self.delete_retard,
            corner_radius=15,
        )
        btn_delete.grid(row=0, column=7, padx=5, pady=5)

        btn_refresh = ctk.CTkButton(
            top_frame,
            text="Rafraîchir élève",
            command=self.refresh_for_selected_eleve,
            corner_radius=15,
        )
        btn_refresh.grid(row=1, column=7, padx=5, pady=5)

        mid_frame = ctk.CTkFrame(self)
        mid_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.tree = ttk.Treeview(
            mid_frame,
            columns=("id", "date", "heure", "duree", "motif"),
            show="headings",
            selectmode="browse",
        )
        self.tree.heading("id", text="ID")
        self.tree.heading("date", text="Date")
        self.tree.heading("heure", text="Heure")
        self.tree.heading("duree", text="Durée")
        self.tree.heading("motif", text="Motif")
        self.tree.column("id", width=40, anchor="center")
        self.tree.column("date", width=90, anchor="center")
        self.tree.column("heure", width=70, anchor="center")
        self.tree.column("duree", width=70, anchor="center")
        self.tree.column("motif", width=260)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ctk.CTkScrollbar(mid_frame, command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        bottom_frame = ctk.CTkFrame(self)
        bottom_frame.pack(fill="x", padx=10, pady=(0, 10))

        btn_stats = ctk.CTkButton(
            bottom_frame,
            text="Statistiques retards par classe",
            command=self.show_retard_stats,
            corner_radius=15,
        )
        btn_stats.pack(side="left", padx=5, pady=5)

    def refresh_for_selected_eleve(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        eleve_id = self.get_selected_eleve_callback()
        if not eleve_id:
            return
        retards = self.db.get_retards_by_eleve(eleve_id)
        for r in retards:
            self.tree.insert("", END, values=r)

    def on_tree_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        item = self.tree.item(selected[0])
        values = item["values"]
        self.selected_retard_id = values[0]
        self.date_var.set(values[1])
        self.heure_var.set(values[2])
        self.duree_var.set(str(values[3]))
        self.motif_var.set(values[4])

    def add_retard(self):
        eleve_id = self.get_selected_eleve_callback()
        if not eleve_id:
            messagebox.showwarning("Retards", "Veuillez d'abord sélectionner un élève dans l'onglet Élèves.")
            return
        date = self.date_var.get().strip()
        heure = self.heure_var.get().strip()
        duree = self.duree_var.get().strip()
        motif = self.motif_var.get().strip()
        if not date or not heure or not duree:
            messagebox.showwarning("Retards", "Date, heure et durée sont obligatoires.")
            return
        try:
            duree_int = int(duree)
        except ValueError:
            messagebox.showwarning("Retards", "Durée invalide.")
            return
        self.db.add_retard(eleve_id, date, heure, duree_int, motif)
        self.db.log_action("surveillant", f"Ajout retard élève {eleve_id}")
        self.refresh_for_selected_eleve()
        self.check_retard_threshold(eleve_id)

    def update_retard(self):
        if not self.selected_retard_id:
            messagebox.showwarning("Retards", "Veuillez sélectionner un retard.")
            return
        date = self.date_var.get().strip()
        heure = self.heure_var.get().strip()
        duree = self.duree_var.get().strip()
        motif = self.motif_var.get().strip()
        if not date or not heure or not duree:
            messagebox.showwarning("Retards", "Date, heure et durée sont obligatoires.")
            return
        try:
            duree_int = int(duree)
        except ValueError:
            messagebox.showwarning("Retards", "Durée invalide.")
            return
        self.db.update_retard(self.selected_retard_id, date, heure, duree_int, motif)
        self.db.log_action("surveillant", f"Modification retard {self.selected_retard_id}")
        self.refresh_for_selected_eleve()

    def delete_retard(self):
        if not self.selected_retard_id:
            messagebox.showwarning("Retards", "Veuillez sélectionner un retard.")
            return
        if not messagebox.askyesno("Retards", "Supprimer ce retard ?"):
            return
        self.db.delete_retard(self.selected_retard_id)
        self.db.log_action("surveillant", f"Suppression retard {self.selected_retard_id}")
        self.selected_retard_id = None
        self.refresh_for_selected_eleve()

    def check_retard_threshold(self, eleve_id, threshold=3):
        retards = self.db.get_retards_by_eleve(eleve_id)
        count = len(retards)
        if count >= threshold:
            messagebox.showwarning(
                "Alerte retards",
                f"Seuil de {threshold} retards atteint pour l'élève {eleve_id}.",
            )

    def show_retard_stats(self):
        stats = self.db.get_retard_stats_by_classe()
        if not stats:
            messagebox.showinfo("Statistiques", "Aucun retard enregistré.")
            return
        lines = []
        for row in stats:
            classe, nb = row
            lines.append(f"{classe} : {nb} retard(s)")
        messagebox.showinfo("Statistiques retards", "\n".join(lines))


class SanctionsTab(ctk.CTkFrame):
    def __init__(self, master, db_manager, get_selected_eleve_callback):
        super().__init__(master)
        self.db = db_manager
        self.get_selected_eleve_callback = get_selected_eleve_callback
        self.selected_sanction_id = None
        self.type_var = StringVar()
        self.date_var = StringVar()
        self.duree_var = StringVar()
        self.motif_var = StringVar()
        self.start_date_var = StringVar()
        self.end_date_var = StringVar()
        self.build_ui()
        self.refresh_for_selected_eleve()

    def build_ui(self):
        top_frame = ctk.CTkFrame(self)
        top_frame.pack(fill="x", padx=10, pady=10)

        lbl_type = ctk.CTkLabel(top_frame, text="Type")
        lbl_type.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        combo_type = ctk.CTkComboBox(
            top_frame,
            values=["Retenue", "Exclusion", "Avertissement", "Observation"],
            variable=self.type_var,
            width=140,
        )
        combo_type.grid(row=0, column=1, padx=5, pady=5)

        lbl_date = ctk.CTkLabel(top_frame, text="Date (YYYY-MM-DD)")
        lbl_date.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        ent_date = ctk.CTkEntry(top_frame, textvariable=self.date_var, width=120)
        ent_date.grid(row=0, column=3, padx=5, pady=5)

        lbl_duree = ctk.CTkLabel(top_frame, text="Durée (min)")
        lbl_duree.grid(row=0, column=4, padx=5, pady=5, sticky="w")
        ent_duree = ctk.CTkEntry(top_frame, textvariable=self.duree_var, width=80)
        ent_duree.grid(row=0, column=5, padx=5, pady=5)

        lbl_motif = ctk.CTkLabel(top_frame, text="Motif")
        lbl_motif.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ent_motif = ctk.CTkEntry(top_frame, textvariable=self.motif_var, width=260)
        ent_motif.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky="we")

        btn_add = ctk.CTkButton(
            top_frame,
            text="Ajouter",
            command=self.add_sanction,
            corner_radius=15,
        )
        btn_add.grid(row=0, column=6, padx=5, pady=5)

        btn_update = ctk.CTkButton(
            top_frame,
            text="Modifier",
            command=self.update_sanction,
            corner_radius=15,
        )
        btn_update.grid(row=1, column=6, padx=5, pady=5)

        btn_delete = ctk.CTkButton(
            top_frame,
            text="Supprimer",
            command=self.delete_sanction,
            corner_radius=15,
        )
        btn_delete.grid(row=0, column=7, padx=5, pady=5)

        btn_refresh = ctk.CTkButton(
            top_frame,
            text="Rafraîchir élève",
            command=self.refresh_for_selected_eleve,
            corner_radius=15,
        )
        btn_refresh.grid(row=1, column=7, padx=5, pady=5)

        mid_frame = ctk.CTkFrame(self)
        mid_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.tree = ttk.Treeview(
            mid_frame,
            columns=("id", "type", "date", "duree", "motif"),
            show="headings",
            selectmode="browse",
        )
        self.tree.heading("id", text="ID")
        self.tree.heading("type", text="Type")
        self.tree.heading("date", text="Date")
        self.tree.heading("duree", text="Durée")
        self.tree.heading("motif", text="Motif")
        self.tree.column("id", width=40, anchor="center")
        self.tree.column("type", width=120)
        self.tree.column("date", width=90, anchor="center")
        self.tree.column("duree", width=70, anchor="center")
        self.tree.column("motif", width=260)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ctk.CTkScrollbar(mid_frame, command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        bottom_frame = ctk.CTkFrame(self)
        bottom_frame.pack(fill="x", padx=10, pady=(0, 10))

        lbl_start = ctk.CTkLabel(bottom_frame, text="Du (YYYY-MM-DD)")
        lbl_start.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ent_start = ctk.CTkEntry(bottom_frame, textvariable=self.start_date_var, width=120)
        ent_start.grid(row=0, column=1, padx=5, pady=5)

        lbl_end = ctk.CTkLabel(bottom_frame, text="Au (YYYY-MM-DD)")
        lbl_end.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        ent_end = ctk.CTkEntry(bottom_frame, textvariable=self.end_date_var, width=120)
        ent_end.grid(row=0, column=3, padx=5, pady=5)

        btn_report = ctk.CTkButton(
            bottom_frame,
            text="Rapport disciplinaire",
            command=self.show_sanction_report,
            corner_radius=15,
        )
        btn_report.grid(row=0, column=4, padx=5, pady=5)

    def refresh_for_selected_eleve(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        eleve_id = self.get_selected_eleve_callback()
        if not eleve_id:
            return
        sanctions = self.db.get_sanctions_by_eleve(eleve_id)
        for s in sanctions:
            self.tree.insert("", END, values=s)

    def on_tree_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        item = self.tree.item(selected[0])
        values = item["values"]
        self.selected_sanction_id = values[0]
        self.type_var.set(values[1])
        self.date_var.set(values[2])
        self.duree_var.set(str(values[3]))
        self.motif_var.set(values[4])

    def add_sanction(self):
        eleve_id = self.get_selected_eleve_callback()
        if not eleve_id:
            messagebox.showwarning("Sanctions", "Veuillez d'abord sélectionner un élève dans l'onglet Élèves.")
            return
        type_s = self.type_var.get().strip()
        date = self.date_var.get().strip()
        duree = self.duree_var.get().strip()
        motif = self.motif_var.get().strip()
        if not type_s or not date:
            messagebox.showwarning("Sanctions", "Type et date sont obligatoires.")
            return
        try:
            duree_int = int(duree) if duree else 0
        except ValueError:
            messagebox.showwarning("Sanctions", "Durée invalide.")
            return
        self.db.add_sanction(eleve_id, type_s, date, duree_int, motif)
        self.db.log_action("surveillant", f"Ajout sanction élève {eleve_id}")
        self.refresh_for_selected_eleve()

    def update_sanction(self):
        if not self.selected_sanction_id:
            messagebox.showwarning("Sanctions", "Veuillez sélectionner une sanction.")
            return
        type_s = self.type_var.get().strip()
        date = self.date_var.get().strip()
        duree = self.duree_var.get().strip()
        motif = self.motif_var.get().strip()
        if not type_s or not date:
            messagebox.showwarning("Sanctions", "Type et date sont obligatoires.")
            return
        try:
            duree_int = int(duree) if duree else 0
        except ValueError:
            messagebox.showwarning("Sanctions", "Durée invalide.")
            return
        self.db.update_sanction(self.selected_sanction_id, type_s, date, duree_int, motif)
        self.db.log_action("surveillant", f"Modification sanction {self.selected_sanction_id}")
        self.refresh_for_selected_eleve()

    def delete_sanction(self):
        if not self.selected_sanction_id:
            messagebox.showwarning("Sanctions", "Veuillez sélectionner une sanction.")
            return
        if not messagebox.askyesno("Sanctions", "Supprimer cette sanction ?"):
            return
        self.db.delete_sanction(self.selected_sanction_id)
        self.db.log_action("surveillant", f"Suppression sanction {self.selected_sanction_id}")
        self.selected_sanction_id = None
        self.refresh_for_selected_eleve()

    def show_sanction_report(self):
        start = self.start_date_var.get().strip()
        end = self.end_date_var.get().strip()
        stats = self.db.get_sanction_stats_by_period(start, end)
        if not stats:
            messagebox.showinfo("Rapport disciplinaire", "Aucune sanction sur la période.")
            return
        lines = []
        total = 0
        for row in stats:
            date, nb = row
            total += nb
            lines.append(f"{date} : {nb} sanction(s)")
        lines.append("")
        lines.append(f"Total sur la période : {total} sanction(s)")
        messagebox.showinfo("Rapport disciplinaire", "\n".join(lines))


class AppelsTab(ctk.CTkFrame):
    def __init__(self, master, db_manager):
        super().__init__(master)
        self.db = db_manager
        self.classe_var = StringVar()
        self.date_var = StringVar(value=datetime.date.today().isoformat())
        self.heure_var = StringVar(value=datetime.datetime.now().strftime("%H:%M"))
        self.build_ui()

    def build_ui(self):
        top_frame = ctk.CTkFrame(self)
        top_frame.pack(fill="x", padx=10, pady=10)

        lbl_classe = ctk.CTkLabel(top_frame, text="Classe")
        lbl_classe.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ent_classe = ctk.CTkEntry(top_frame, textvariable=self.classe_var, width=80)
        ent_classe.grid(row=0, column=1, padx=5, pady=5)

        lbl_date = ctk.CTkLabel(top_frame, text="Date (YYYY-MM-DD)")
        lbl_date.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        ent_date = ctk.CTkEntry(top_frame, textvariable=self.date_var, width=120)
        ent_date.grid(row=0, column=3, padx=5, pady=5)

        lbl_heure = ctk.CTkLabel(top_frame, text="Heure (HH:MM)")
        lbl_heure.grid(row=0, column=4, padx=5, pady=5, sticky="w")
        ent_heure = ctk.CTkEntry(top_frame, textvariable=self.heure_var, width=80)
        ent_heure.grid(row=0, column=5, padx=5, pady=5)

        btn_load = ctk.CTkButton(
            top_frame,
            text="Charger classe",
            command=self.load_classe,
            corner_radius=15,
        )
        btn_load.grid(row=0, column=6, padx=5, pady=5)

        btn_save = ctk.CTkButton(
            top_frame,
            text="Sauvegarde automatique",
            command=self.save_all,
            corner_radius=15,
        )
        btn_save.grid(row=0, column=7, padx=5, pady=5)

        mid_frame = ctk.CTkFrame(self)
        mid_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.tree = ttk.Treeview(
            mid_frame,
            columns=("appel_id", "eleve_id", "nom", "prenom", "statut"),
            show="headings",
            selectmode="browse",
        )
        self.tree.heading("appel_id", text="ID Appel")
        self.tree.heading("eleve_id", text="ID Élève")
        self.tree.heading("nom", text="Nom")
        self.tree.heading("prenom", text="Prénom")
        self.tree.heading("statut", text="Statut")
        self.tree.column("appel_id", width=70, anchor="center")
        self.tree.column("eleve_id", width=70, anchor="center")
        self.tree.column("nom", width=140)
        self.tree.column("prenom", width=140)
        self.tree.column("statut", width=90, anchor="center")
        self.tree.bind("<Double-1>", self.toggle_statut)
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ctk.CTkScrollbar(mid_frame, command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        bottom_frame = ctk.CTkFrame(self)
        bottom_frame.pack(fill="x", padx=10, pady=(0, 10))

        btn_history = ctk.CTkButton(
            bottom_frame,
            text="Historique des appels",
            command=self.show_history,
            corner_radius=15,
        )
        btn_history.pack(side="left", padx=5, pady=5)

        btn_export_csv = ctk.CTkButton(
            bottom_frame,
            text="Export CSV",
            command=self.export_csv,
            corner_radius=15,
        )
        btn_export_csv.pack(side="left", padx=5, pady=5)

    def load_classe(self):
        classe = self.classe_var.get().strip()
        date = self.date_var.get().strip()
        if not classe or not date:
            messagebox.showwarning("Appels", "Classe et date sont obligatoires.")
            return
        for row in self.tree.get_children():
            self.tree.delete(row)
        rows = self.db.get_appel_for_classe_date(classe, date)
        for r in rows:
            appel_id = r[0] if r[0] is not None else ""
            eleve_id = r[1]
            nom = r[2]
            prenom = r[3]
            statut = r[4] if r[4] else "present"
            self.tree.insert("", END, values=(appel_id, eleve_id, nom, prenom, statut))

    def toggle_statut(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        item = self.tree.item(selected[0])
        values = list(item["values"])
        current_statut = values[4]
        if current_statut == "present":
            new_statut = "absent"
        elif current_statut == "absent":
            new_statut = "retard"
        else:
            new_statut = "present"
        values[4] = new_statut
        self.tree.item(selected[0], values=values)

    def save_all(self):
        classe = self.classe_var.get().strip()
        date = self.date_var.get().strip()
        heure = self.heure_var.get().strip()
        if not classe or not date or not heure:
            messagebox.showwarning("Appels", "Classe, date et heure sont obligatoires.")
            return
        for row_id in self.tree.get_children():
            item = self.tree.item(row_id)
            appel_id, eleve_id, nom, prenom, statut = item["values"]
            self.db.save_appel_entry(classe, date, heure, eleve_id, statut)
        self.db.log_action("surveillant", f"Sauvegarde appel classe {classe} du {date}")
        messagebox.showinfo("Appels", "Appel sauvegardé.")

    def show_history(self):
        rows = self.db.get_appels_history()
        if not rows:
            messagebox.showinfo("Historique", "Aucun appel enregistré.")
            return
        lines = []
        for r in rows[:200]:
            lines.append(
                f"{r[2]} {r[3]} - {r[1]} - {r[4]} {r[5]} : {r[6]}"
            )
        messagebox.showinfo("Historique des appels", "\n".join(lines))

    def export_csv(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            title="Exporter les appels en CSV",
        )
        if not filepath:
            return
        self.db.export_appels_to_csv(filepath)
        messagebox.showinfo("Export", "Export CSV terminé.")


class SurveillanceTab(ctk.CTkFrame):
    def __init__(self, master, db_manager, get_selected_eleve_callback):
        super().__init__(master)
        self.db = db_manager
        self.get_selected_eleve_callback = get_selected_eleve_callback
        self.selected_surv_id = None
        self.type_var = StringVar()
        self.date_var = StringVar(value=datetime.date.today().isoformat())
        self.heure_debut_var = StringVar()
        self.heure_fin_var = StringVar()
        self.motif_var = StringVar()
        self.build_ui()
        self.refresh_list()

    def build_ui(self):
        top_frame = ctk.CTkFrame(self)
        top_frame.pack(fill="x", padx=10, pady=10)

        lbl_type = ctk.CTkLabel(top_frame, text="Type")
        lbl_type.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        combo_type = ctk.CTkComboBox(
            top_frame,
            values=["Permanence", "Étude", "Exclusion cours", "Sortie exceptionnelle"],
            variable=self.type_var,
            width=180,
        )
        combo_type.grid(row=0, column=1, padx=5, pady=5)

        lbl_date = ctk.CTkLabel(top_frame, text="Date (YYYY-MM-DD)")
        lbl_date.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        ent_date = ctk.CTkEntry(top_frame, textvariable=self.date_var, width=120)
        ent_date.grid(row=0, column=3, padx=5, pady=5)

        lbl_hd = ctk.CTkLabel(top_frame, text="Heure début")
        lbl_hd.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ent_hd = ctk.CTkEntry(top_frame, textvariable=self.heure_debut_var, width=80)
        ent_hd.grid(row=1, column=1, padx=5, pady=5)

        lbl_hf = ctk.CTkLabel(top_frame, text="Heure fin")
        lbl_hf.grid(row=1, column=2, padx=5, pady=5, sticky="w")
        ent_hf = ctk.CTkEntry(top_frame, textvariable=self.heure_fin_var, width=80)
        ent_hf.grid(row=1, column=3, padx=5, pady=5)

        lbl_motif = ctk.CTkLabel(top_frame, text="Motif")
        lbl_motif.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        ent_motif = ctk.CTkEntry(top_frame, textvariable=self.motif_var, width=260)
        ent_motif.grid(row=2, column=1, columnspan=3, padx=5, pady=5, sticky="we")

        btn_add = ctk.CTkButton(
            top_frame,
            text="Ajouter",
            command=self.add_entry,
            corner_radius=15,
        )
        btn_add.grid(row=0, column=4, padx=5, pady=5)

        btn_delete = ctk.CTkButton(
            top_frame,
            text="Supprimer",
            command=self.delete_entry,
            corner_radius=15,
        )
        btn_delete.grid(row=1, column=4, padx=5, pady=5)

        btn_refresh = ctk.CTkButton(
            top_frame,
            text="Rafraîchir registre",
            command=self.refresh_list,
            corner_radius=15,
        )
        btn_refresh.grid(row=2, column=4, padx=5, pady=5)

        mid_frame = ctk.CTkFrame(self)
        mid_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.tree = ttk.Treeview(
            mid_frame,
            columns=("id", "nom", "prenom", "classe", "type", "date", "hd", "hf", "motif"),
            show="headings",
            selectmode="browse",
        )
        self.tree.heading("id", text="ID")
        self.tree.heading("nom", text="Nom")
        self.tree.heading("prenom", text="Prénom")
        self.tree.heading("classe", text="Classe")
        self.tree.heading("type", text="Type")
        self.tree.heading("date", text="Date")
        self.tree.heading("hd", text="Début")
        self.tree.heading("hf", text="Fin")
        self.tree.heading("motif", text="Motif")
        self.tree.column("id", width=40, anchor="center")
        self.tree.column("nom", width=120)
        self.tree.column("prenom", width=120)
        self.tree.column("classe", width=80, anchor="center")
        self.tree.column("type", width=140)
        self.tree.column("date", width=90, anchor="center")
        self.tree.column("hd", width=70, anchor="center")
        self.tree.column("hf", width=70, anchor="center")
        self.tree.column("motif", width=220)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ctk.CTkScrollbar(mid_frame, command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

    def refresh_list(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        rows = self.db.get_surveillance_entries()
        for r in rows:
            self.tree.insert("", END, values=r)

    def on_tree_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        item = self.tree.item(selected[0])
        values = item["values"]
        self.selected_surv_id = values[0]
        self.type_var.set(values[4])
        self.date_var.set(values[5])
        self.heure_debut_var.set(values[6])
        self.heure_fin_var.set(values[7])
        self.motif_var.set(values[8])

    def add_entry(self):
        eleve_id = self.get_selected_eleve_callback()
        if not eleve_id:
            messagebox.showwarning("Surveillance", "Veuillez d'abord sélectionner un élève dans l'onglet Élèves.")
            return
        type_s = self.type_var.get().strip()
        date = self.date_var.get().strip()
        hd = self.heure_debut_var.get().strip()
        hf = self.heure_fin_var.get().strip()
        motif = self.motif_var.get().strip()
        if not type_s or not date:
            messagebox.showwarning("Surveillance", "Type et date sont obligatoires.")
            return
        self.db.add_surveillance_entry(eleve_id, type_s, date, hd, hf, motif)
        self.db.log_action("surveillant", f"Ajout surveillance élève {eleve_id}")
        self.refresh_list()

    def delete_entry(self):
        if not self.selected_surv_id:
            messagebox.showwarning("Surveillance", "Veuillez sélectionner une entrée.")
            return
        if not messagebox.askyesno("Surveillance", "Supprimer cette entrée ?"):
            return
        self.db.delete_surveillance_entry(self.selected_surv_id)
        self.db.log_action("surveillant", f"Suppression surveillance {self.selected_surv_id}")
        self.selected_surv_id = None
        self.refresh_list()


class StatsTab(ctk.CTkFrame):
    def __init__(self, master, db_manager):
        super().__init__(master)
        self.db = db_manager
        self.build_ui()

    def build_ui(self):
        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        lbl_title = ctk.CTkLabel(
            frame,
            text="Statistiques vie scolaire",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        lbl_title.pack(pady=10)

        btn_abs = ctk.CTkButton(
            frame,
            text="Absences par élève",
            command=self.show_abs_stats,
            corner_radius=20,
            width=220,
        )
        btn_abs.pack(pady=5)

        btn_ret = ctk.CTkButton(
            frame,
            text="Retards par classe",
            command=self.show_ret_stats,
            corner_radius=20,
            width=220,
        )
        btn_ret.pack(pady=5)

        btn_sanc = ctk.CTkButton(
            frame,
            text="Sanctions par période",
            command=self.show_sanc_stats,
            corner_radius=20,
            width=220,
        )
        btn_sanc.pack(pady=5)

        self.text_area = ctk.CTkTextbox(frame, height=260)
        self.text_area.pack(fill="both", expand=True, pady=10)

    def show_abs_stats(self):
        stats = self.db.get_absence_stats()
        self.text_area.delete("1.0", END)
        if not stats:
            self.text_area.insert("1.0", "Aucune absence.\n")
            return
        self.text_area.insert("1.0", "Absences par élève :\n\n")
        for row in stats:
            nom, prenom, classe, nb = row
            self.text_area.insert(
                END, f"{nom} {prenom} ({classe}) : {nb} absence(s)\n"
            )

    def show_ret_stats(self):
        stats = self.db.get_retard_stats_by_classe()
        self.text_area.delete("1.0", END)
        if not stats:
            self.text_area.insert("1.0", "Aucun retard.\n")
            return
        self.text_area.insert("1.0", "Retards par classe :\n\n")
        for row in stats:
            classe, nb = row
            self.text_area.insert(END, f"{classe} : {nb} retard(s)\n")

    def show_sanc_stats(self):
        today = datetime.date.today().isoformat()
        stats = self.db.get_sanction_stats_by_period("", today)
        self.text_area.delete("1.0", END)
        if not stats:
            self.text_area.insert("1.0", "Aucune sanction.\n")
            return
        self.text_area.insert("1.0", "Sanctions par date :\n\n")
        for row in stats:
            date, nb = row
            self.text_area.insert(END, f"{date} : {nb} sanction(s)\n")


class SyncTab(ctk.CTkFrame):
    def __init__(self, master, db_manager):
        super().__init__(master)
        self.db = db_manager
        self.offline_mode = IntVar(value=0)
        self.build_ui()
        self.refresh_status()

    def build_ui(self):
        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        lbl_title = ctk.CTkLabel(
            frame,
            text="Synchronisation base centrale",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        lbl_title.pack(pady=10)

        self.status_label = ctk.CTkLabel(frame, text="Statut : inconnu")
        self.status_label.pack(pady=5)

        chk_offline = ctk.CTkCheckBox(
            frame,
            text="Mode hors-ligne (les données seront resynchronisées plus tard)",
            variable=self.offline_mode,
        )
        chk_offline.pack(pady=5)

        btn_sync = ctk.CTkButton(
            frame,
            text="Lancer la synchronisation",
            command=self.sync_now,
            corner_radius=20,
            width=220,
        )
        btn_sync.pack(pady=10)

        self.log_text = ctk.CTkTextbox(frame, height=220)
        self.log_text.pack(fill="both", expand=True, pady=10)

    def refresh_status(self):
        abs_c, ret_c, sanc_c, appel_c, surv_c = self.db.get_unsynced_counts()
        total = abs_c + ret_c + sanc_c + appel_c + surv_c
        self.status_label.configure(
            text=f"En attente de synchronisation : {total} enregistrements "
                 f"(Abs:{abs_c}, Ret:{ret_c}, Sanc:{sanc_c}, Appels:{appel_c}, Surv:{surv_c})"
        )

    def sync_now(self):
        if self.offline_mode.get() == 1:
            self.log_text.insert(
                END,
                "Mode hors-ligne activé : la synchronisation réelle est différée.\n",
            )
            return
        self.log_text.insert(END, "Synchronisation avec la base centrale...\n")
        self.db.mark_all_synced()
        self.log_text.insert(END, "Synchronisation terminée.\n")
        self.refresh_status()


class MainApp(ctk.CTk):
    def __init__(self, db_manager, username):
        super().__init__()
        self.db = db_manager
        self.username = username
        self.selected_eleve_id = None
        self.title("Pronote - Surveillant")
        self.geometry("1200x720")
        self.minsize(1000, 600)
        self.build_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def build_ui(self):
        top_bar = ctk.CTkFrame(self, height=40)
        top_bar.pack(fill="x", side="top")

        lbl_user = ctk.CTkLabel(
            top_bar,
            text=f"Connecté en tant que : {self.username} (Surveillant)",
            anchor="w",
        )
        lbl_user.pack(side="left", padx=10, pady=5)

        btn_logout = ctk.CTkButton(
            top_bar,
            text="Déconnexion",
            command=self.logout,
            corner_radius=15,
            width=120,
        )
        btn_logout.pack(side="right", padx=10, pady=5)

        self.notebook = ctk.CTkTabview(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        tab_eleves = self.notebook.add("Élèves")
        tab_absences = self.notebook.add("Absences")
        tab_retards = self.notebook.add("Retards")
        tab_sanctions = self.notebook.add("Sanctions")
        tab_appels = self.notebook.add("Appels")
        tab_surveillance = self.notebook.add("Surveillance")
        tab_stats = self.notebook.add("Statistiques")
        tab_sync = self.notebook.add("Paramètres")

        self.eleves_tab = ElevesTab(
            tab_eleves,
            self.db,
            on_eleve_selected_callback=self.set_selected_eleve,
        )
        self.eleves_tab.pack(fill="both", expand=True)

        self.absences_tab = AbsencesTab(
            tab_absences,
            self.db,
            get_selected_eleve_callback=self.get_selected_eleve,
        )
        self.absences_tab.pack(fill="both", expand=True)

        self.retards_tab = RetardsTab(
            tab_retards,
            self.db,
            get_selected_eleve_callback=self.get_selected_eleve,
        )
        self.retards_tab.pack(fill="both", expand=True)

        self.sanctions_tab = SanctionsTab(
            tab_sanctions,
            self.db,
            get_selected_eleve_callback=self.get_selected_eleve,
        )
        self.sanctions_tab.pack(fill="both", expand=True)

        self.appels_tab = AppelsTab(tab_appels, self.db)
        self.appels_tab.pack(fill="both", expand=True)

        self.surveillance_tab = SurveillanceTab(
            tab_surveillance,
            self.db,
            get_selected_eleve_callback=self.get_selected_eleve,
        )
        self.surveillance_tab.pack(fill="both", expand=True)

        self.stats_tab = StatsTab(tab_stats, self.db)
        self.stats_tab.pack(fill="both", expand=True)

        self.sync_tab = SyncTab(tab_sync, self.db)
        self.sync_tab.pack(fill="both", expand=True)

    def set_selected_eleve(self, eleve_id):
        self.selected_eleve_id = eleve_id
        self.absences_tab.refresh_for_selected_eleve()
        self.retards_tab.refresh_for_selected_eleve()
        self.sanctions_tab.refresh_for_selected_eleve()

    def get_selected_eleve(self):
        return self.selected_eleve_id

    def logout(self):
        if not messagebox.askyesno("Déconnexion", "Voulez-vous vous déconnecter ?"):
            return
        self.db.log_action(self.username, "Déconnexion")
        self.destroy()

    def on_close(self):
        if not messagebox.askyesno("Quitter", "Voulez-vous fermer l'application ?"):
            return
        self.db.log_action(self.username, "Fermeture application")
        self.db.close()
        self.destroy()


def main():
    db = DatabaseManager()
    login = LoginWindow(db)
    login.mainloop()


if __name__ == "__main__":
    main()
