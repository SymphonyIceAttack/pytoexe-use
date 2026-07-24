import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import webbrowser
import os
import tempfile
import time

# Variables globales
donnees = None
chemin_fichier = None
resultats_par_produit = None


# ============  Insuffisances tolérées T (OIML R87:2016) ============
def get_T(Qnom, unite='g'):
    """
    Calcule T selon le Tableau 3 de la R87:2016
    Qnom : quantité nominale (dans l'unité spécifiée)
    unite : 'g', 'mL', 'L', 'longueur', 'surface', 'nombre'
    """
    if unite in ('g', 'mL'):
        if Qnom <= 50:
            return Qnom * 0.09
        elif Qnom <= 100:
            return 4.5
        elif Qnom <= 200:
            return Qnom * 0.045
        elif Qnom <= 300:
            return 9.0
        elif Qnom <= 500:
            return Qnom * 0.03
        elif Qnom <= 1000:
            return 15.0
        elif Qnom <= 10000:
            return Qnom * 0.015
        elif Qnom <= 15000:
            return 150.0
        elif Qnom <= 50000:
            return Qnom * 0.01
        else:
            return Qnom * 0.01
    elif unite == 'L':
        # Convertir en mL pour utiliser le tableau
        return get_T(Qnom * 1000, 'mL')
    elif unite == 'longueur':
        if Qnom <= 5:
            return 0.0
        else:
            return Qnom * 0.02
    elif unite == 'surface':
        return Qnom * 0.03
    elif unite == 'nombre':
        if Qnom <= 50:
            return 0.0
        else:
            return np.ceil(Qnom * 0.01)
    else:
        return Qnom * 0.05


def arrondir_T(T, Qnom, unite='g'):
    """
    Arrondi T selon les règles (R87:2016)
    """
    if unite in ('g', 'mL'):
        if Qnom <= 1000:
            return np.ceil(T * 10) / 10
        else:
            return np.ceil(T)
    elif unite == 'L':
        return arrondir_T(T, Qnom * 1000, 'mL')
    else:
        return T


def calculer_seuils(Qnom, unite='g'):
    """
    Retourne (T_arrondi, seuil_T1_sup, seuil_T2)
    """
    T = get_T(Qnom, unite)
    T_arrondi = arrondir_T(T, Qnom, unite)
    seuil_T1_sup = Qnom - T_arrondi
    seuil_T2 = Qnom - 2 * T_arrondi
    return T_arrondi, seuil_T1_sup, seuil_T2


# ============ TABLEAU 6 : Plan d'échantillonnage ============
def get_tableau6(N):
    """
    Retourne (n, nb_T1_autorise, FCE) selon Tableau 6 de R87:2016
    """
    if N <= 20:
        return (N, 0, None)
    elif N <= 40:
        return (32, 1, 0.22)
    elif N <= 60:
        return (35, 1, 0.30)
    elif N <= 80:
        return (47, 2, 0.25)
    elif N <= 100:
        return (49, 2, 0.28)
    elif N <= 200:
        return (64, 3, 0.27)
    elif N <= 300:
        return (67, 3, 0.29)
    elif N <= 400:
        return (81, 4, 0.26)
    elif N <= 500:
        return (81, 4, 0.27)
    elif N <= 656:
        return (98, 5, 0.24)
    elif N <= 1261:
        return (98, 5, 0.25)
    elif N <= 31094:
        return (98, 5, 0.26)
    elif N <= 100000:
        return (98, 5, 0.27)
    else:
        return (98, 5, 0.27)


# ============ Incertitudes ============
def calculer_incertitudes(valeurs, resolution, incert_etalonnage, n_mesures_etalon=1):
    """
    Calcule les incertitudes selon GUM
    - valeurs : liste des mesures (Qi)
    - resolution : résolution de la balance (g)
    - incert_etalonnage : incertitude-type d'étalonnage (g) (si donnée, sinon 0)
    - n_mesures_etalon : nombre de mesures utilisées pour l'étalonnage (par défaut 1)
    Retourne : u_moy, u_elargie, u_repeat, u_res, u_cal
    """
    n = len(valeurs)
    if n == 0:
        return 0, 0, 0, 0, 0

    # Écart-type de répétabilité (type A)
    s_repeat = np.std(valeurs, ddof=1) if n > 1 else 0

    # Incertitude due à la résolution (distribution rectangulaire)
    if resolution > 0:
        # résolution = plus petit échelon. On prend u = résolution / (2*sqrt(3)) si on considère que la résolution est l'intervalle total.
        # Souvent on utilise résolution / sqrt(12) si la résolution est l'écart entre deux valeurs.
        # Ici on adopte : u_res = resolution / (2 * sqrt(3))
        u_res = resolution / (2 * np.sqrt(3))
    else:
        u_res = 0

    # Incertitude d'étalonnage (type B) - fournie par le certificat
    u_cal = incert_etalonnage if incert_etalonnage > 0 else 0

    # Incertitude-type combinée sur la moyenne
    # u_moy = sqrt( (s_repeat/sqrt(n))^2 + u_res^2 + u_cal^2 )
    if n > 1:
        u_moy = np.sqrt((s_repeat / np.sqrt(n)) ** 2 + u_res ** 2 + u_cal ** 2)
    else:
        u_moy = np.sqrt(s_repeat ** 2 + u_res ** 2 + u_cal ** 2)

    # Incertitude élargie (k=2, 95% de confiance)
    u_elargie = 2 * u_moy

    return u_moy, u_elargie, s_repeat, u_res, u_cal


# ============ Chargement des données ============
def charger_donnees():
    global donnees, chemin_fichier
    chemin_fichier = filedialog.askopenfilename(
        title="Choisir un fichier Excel",
        filetypes=(("Fichiers Excel", "*.xlsx *.xls"), ("Tous les fichiers", "*.*"))
    )
    if not chemin_fichier:
        messagebox.showwarning("Attention", "Aucun fichier sélectionné.")
        return

    try:
        donnees = pd.read_excel(chemin_fichier)

        # Colonnes obligatoires
        colonnes_requises = ['Nom_Produit', 'Numero_Lot', 'Qnom', 'Masse_brute', 'Tare']
        colonnes_manquantes = [col for col in colonnes_requises if col not in donnees.columns]

        if colonnes_manquantes:
            # Si Numero_Lot manque, on le crée avec 'N/A'
            if 'Numero_Lot' in colonnes_manquantes:
                donnees['Numero_Lot'] = 'N/A'
                colonnes_manquantes.remove('Numero_Lot')
            if colonnes_manquantes:
                messagebox.showerror("Erreur",
                                     f"Colonnes manquantes :\n{', '.join(colonnes_manquantes)}\n\nLe fichier doit contenir :\n- Nom_Produit\n- Numero_Lot\n- Qnom\n- Masse_brute\n- Tare")
                return

        # Conversion robuste des colonnes numériques
        for col in ['Masse_brute', 'Tare', 'Qnom']:
            donnees[col] = donnees[col].astype(str).str.replace(',', '.')
            donnees[col] = pd.to_numeric(donnees[col], errors='coerce')

        # Supprimer les lignes avec des NaN dans les colonnes critiques
        donnees = donnees.dropna(subset=['Masse_brute', 'Tare', 'Qnom'])

        # Calcul de Qi = Masse_brute - Tare (pour le contrôle non destructif)
        donnees['Qi'] = donnees['Masse_brute'] - donnees['Tare']
        donnees['Qi'] = donnees['Qi'].round(2)

        # Colonnes optionnelles
        if 'Unite' not in donnees.columns:
            donnees['Unite'] = 'g'
        if 'Type_Produit' not in donnees.columns:
            donnees['Type_Produit'] = 'solide'  # 'solide', 'liquide', 'liquide_avec_solide', 'congele'
        if 'Type_Controle' not in donnees.columns:
            donnees['Type_Controle'] = 'ND'  # 'ND' (non destructif) ou 'D' (destructif)
        if 'Taille_Lot' not in donnees.columns:
            donnees['Taille_Lot'] = None
        # Pour les liquides avec solide, masse égouttée
        if 'Masse_egouttee' not in donnees.columns:
            donnees['Masse_egouttee'] = None
        # Données de balance
        if 'Resolution' not in donnees.columns:
            donnees['Resolution'] = 0.0
        if 'Incertitude_Etalonnage' not in donnees.columns:
            donnees['Incertitude_Etalonnage'] = 0.0
        if 'Modele_Balance' not in donnees.columns:
            donnees['Modele_Balance'] = 'Inconnu'

        # Conversion des colonnes numériques optionnelles
        for col in ['Resolution', 'Incertitude_Etalonnage', 'Masse_egouttee']:
            if col in donnees.columns:
                donnees[col] = pd.to_numeric(donnees[col], errors='coerce').fillna(0)

        produits_uniques = donnees['Nom_Produit'].unique()
        messagebox.showinfo("Succès",
                            f"Fichier chargé avec succès !\n\n{len(donnees)} mesures trouvées\n{len(produits_uniques)} produits différents\n\nMasse nette calculée automatiquement (Qi = Masse_brute - Tare)")

    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de lire le fichier Excel :\n{e}")


# ============ Calcul de conformité ============
def calculer_conformite_produit(groupe, nom_produit, quantite_nominale, unite):
    """
    Calcule la conformité selon OIML R87:2016 avec incertitudes
    """
    # Récupération des informations du produit
    type_produit = groupe['Type_Produit'].iloc[0] if 'Type_Produit' in groupe.columns else 'solide'
    type_controle = groupe['Type_Controle'].iloc[0] if 'Type_Controle' in groupe.columns else 'ND'
    resolution = groupe['Resolution'].iloc[0] if 'Resolution' in groupe.columns else 0.0
    incert_etal = groupe['Incertitude_Etalonnage'].iloc[0] if 'Incertitude_Etalonnage' in groupe.columns else 0.0
    modele_balance = groupe['Modele_Balance'].iloc[0] if 'Modele_Balance' in groupe.columns else 'Inconnu'

    # Pour les produits avec liquide de couverture, on utilise la masse égouttée si disponible
    if type_produit == 'liquide_avec_solide' and 'Masse_egouttee' in groupe.columns:
        valeurs_egouttees = groupe['Masse_egouttee'].dropna().values
        if len(valeurs_egouttees) > 0:
            valeurs = valeurs_egouttees
            # On considère que c'est une mesure destructif (car on doit ouvrir le préemballage)
            type_controle = 'D'
        else:
            # Sinon on utilise Qi
            valeurs = groupe['Qi'].dropna().values
    else:
        # Pour les autres, on utilise Qi
        valeurs = groupe['Qi'].dropna().values

    n = len(valeurs)
    if n == 0:
        return None

    # Détermination du seuil de non-conformité (pour information)
    if type_produit == 'liquide':
        seuil_non_conforme = quantite_nominale * 0.85  # 85% pour liquides
    else:
        seuil_non_conforme = quantite_nominale * 0.90  # 90% pour solides

    # Calcul des seuils T1 et T2
    T_arrondi, seuil_T1_sup, seuil_T2 = calculer_seuils(quantite_nominale, unite)

    # Taille du lot
    if 'Taille_Lot' in groupe.columns and not groupe['Taille_Lot'].isnull().all():
        N = int(groupe['Taille_Lot'].iloc[0])
    else:
        N = n

    # Plan d'échantillonnage
    n_req, nb_T1_autorise, FCE = get_tableau6(N)

    # Statistiques
    moyenne = np.mean(valeurs)
    ecart_type = np.std(valeurs, ddof=1) if n > 1 else 0
    erreurs = valeurs - quantite_nominale
    eave = np.mean(erreurs)

    # Comptage T1 et T2
    nb_T1 = np.sum((valeurs >= seuil_T2) & (valeurs < seuil_T1_sup))
    nb_T2 = np.sum(valeurs < seuil_T2)

    # Essai moyenne
    if FCE is not None:
        moyenne_test = eave + (FCE * ecart_type)
        conformite_moyenne = moyenne_test >= 0
    else:
        conformite_moyenne = eave >= 0

    conformite_T1 = nb_T1 <= nb_T1_autorise
    conformite_T2 = nb_T2 == 0
    conforme = conformite_moyenne and conformite_T1 and conformite_T2

    # Taux de non-conformes
    non_conformes = np.sum(valeurs < seuil_non_conforme)
    taux_non_conformes = (non_conformes / n) * 100

    # Calcul des incertitudes
    u_moy, u_elargie, s_repeat, u_res, u_cal = calculer_incertitudes(valeurs, resolution, incert_etal)

    # Lots
    lots = groupe['Numero_Lot'].tolist() if 'Numero_Lot' in groupe.columns else ['N/A'] * n

    return {
        'produit': nom_produit,
        'conforme': conforme,
        'n_echantillons': n,
        'N_lot': N,
        'n_requis': n_req,
        'moyenne': float(moyenne),
        'eave': float(eave),
        'ecart_type': float(ecart_type),
        'quantite_nominale': float(quantite_nominale),
        'T': float(T_arrondi),
        'seuil_T1_sup': float(seuil_T1_sup),
        'seuil_T2': float(seuil_T2),
        'nb_T1': int(nb_T1),
        'nb_T1_autorise': int(nb_T1_autorise),
        'nb_T2': int(nb_T2),
        'FCE': FCE,
        'conformite_moyenne': conformite_moyenne,
        'conformite_T1': conformite_T1,
        'conformite_T2': conformite_T2,
        'taux_non_conformes': float(taux_non_conformes),
        'non_conformes': int(non_conformes),
        'seuil_tolerance': float(seuil_non_conforme),
        'min': float(np.min(valeurs)),
        'max': float(np.max(valeurs)),
        'mediane': float(np.median(valeurs)),
        'q1': float(np.percentile(valeurs, 25)),
        'q3': float(np.percentile(valeurs, 75)),
        'valeurs': valeurs,
        'lots': lots,
        'masse_brute': groupe['Masse_brute'].tolist(),
        'tare': groupe['Tare'].tolist(),
        'erreurs': erreurs.tolist(),
        # Informations supplémentaires
        'type_produit': type_produit,
        'type_controle': type_controle,
        'modele_balance': modele_balance,
        'resolution': resolution,
        'incert_etal': incert_etal,
        'u_moy': u_moy,
        'u_elargie': u_elargie,
        's_repeat': s_repeat,
        'u_res': u_res,
        'u_cal': u_cal,
        'unite': unite
    }


def calculer_conformite():
    global donnees, resultats_par_produit
    if donnees is None:
        messagebox.showwarning("Attention", "Veuillez d'abord charger un fichier Excel.")
        return

    try:
        resultats_par_produit = []
        avertissements = []

        for produit, groupe in donnees.groupby('Nom_Produit'):
            quantite_nominale = groupe['Qnom'].iloc[0]
            unite = groupe['Unite'].iloc[0] if 'Unite' in groupe.columns else 'g'
            resultat = calculer_conformite_produit(groupe, produit, quantite_nominale, unite)
            if resultat:
                resultats_par_produit.append(resultat)
                if resultat['n_echantillons'] < resultat['n_requis'] and resultat['N_lot'] > 20:
                    avertissements.append(
                        f"Produit '{produit}' : N={resultat['N_lot']}, n={resultat['n_echantillons']} < {resultat['n_requis']} requis"
                    )

        if not resultats_par_produit:
            messagebox.showwarning("Attention", "Aucun résultat calculé")
            return

        if avertissements:
            messagebox.showwarning("Attention échantillonnage",
                                   "Certains échantillons sont trop petits :\n\n" + "\n".join(avertissements))

        afficher_resultats_global()
    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur pendant le calcul :\n{str(e)}")


# ============ Affichage des résultats ============
def afficher_resultats_global():
    """Affiche une fenêtre avec les résultats de tous les produits"""
    fenetre_resultats = tk.Toplevel()
    fenetre_resultats.title("Rapport de Conformité R87:2016")
    fenetre_resultats.geometry("1300x850")

    cadre_principal = tk.Frame(fenetre_resultats)
    cadre_principal.pack(fill=tk.BOTH, expand=True)

    canvas = tk.Canvas(cadre_principal)
    scrollbar = tk.Scrollbar(cadre_principal, orient="vertical", command=canvas.yview)
    cadre_scrollable = tk.Frame(canvas)

    cadre_scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=cadre_scrollable, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # En-tête
    tk.Label(cadre_scrollable, text="RAPPORT DE CONFORMITÉ (OIML R87:2016)",
             font=("Arial", 18, "bold"), fg="blue").pack(pady=20)
    tk.Label(cadre_scrollable, text=f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
             font=("Arial", 10)).pack()
    tk.Label(cadre_scrollable, text="Contrôle des produits préemballés",
             font=("Arial", 12)).pack(pady=5)

    # Résumé global
    nb_conformes = sum(1 for r in resultats_par_produit if r['conforme'])
    cadre_resume = tk.Frame(cadre_scrollable, relief=tk.RIDGE, borderwidth=2, bg='lightyellow')
    cadre_resume.pack(fill=tk.X, padx=20, pady=10)

    tk.Label(cadre_resume, text="RÉSUMÉ GLOBAL", font=("Arial", 14, "bold"), bg='lightyellow').pack(pady=10)
    tk.Label(cadre_resume,
             text=f"✅ Produits conformes: {nb_conformes}/{len(resultats_par_produit)} ({nb_conformes / len(resultats_par_produit) * 100:.1f}%)",
             font=("Arial", 12), fg="green", bg='lightyellow').pack()
    tk.Label(cadre_resume,
             text=f"❌ Produits non conformes: {len(resultats_par_produit) - nb_conformes}/{len(resultats_par_produit)} ({(len(resultats_par_produit) - nb_conformes) / len(resultats_par_produit) * 100:.1f}%)",
             font=("Arial", 12), fg="red", bg='lightyellow').pack()

    # Tableau des résultats (avec colonnes supplémentaires)
    cadre_tableau = tk.LabelFrame(cadre_scrollable, text="Détail par produit", font=("Arial", 12, "bold"), padx=10, pady=10)
    cadre_tableau.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

    columns = ('Produit', 'Qn', 'Unité', 'N', 'n', 'T', 'Moyenne', 'eave', 'Écart-type',
               'T1', 'T2', 'U (k=2)', 'Taux NC', 'Statut')

    tree = ttk.Treeview(cadre_tableau, columns=columns, show='headings', height=15)

    for col in columns:
        tree.heading(col, text=col)

    col_widths = {'Produit': 150, 'Qn': 60, 'Unité': 50, 'N': 50, 'n': 50, 'T': 60,
                  'Moyenne': 80, 'eave': 70, 'Écart-type': 80,
                  'T1': 60, 'T2': 50, 'U (k=2)': 70, 'Taux NC': 70, 'Statut': 120}

    for col in columns:
        tree.column(col, width=col_widths.get(col, 80))

    for r in resultats_par_produit:
        statut = "✓ CONFORME" if r['conforme'] else "✗ NON CONFORME"
        couleur = 'green' if r['conforme'] else 'red'

        if not r['conforme']:
            causes = []
            if not r['conformite_moyenne']:
                causes.append("Moyenne")
            if not r['conformite_T1']:
                causes.append(f"T1 ({r['nb_T1']}>{r['nb_T1_autorise']})")
            if not r['conformite_T2']:
                causes.append(f"T2 ({r['nb_T2']}>0)")
            statut = f"✗ NON CONFORME ({', '.join(causes)})"

        tree.insert('', 'end', values=(
            r['produit'],
            f"{r['quantite_nominale']:.0f}",
            r.get('unite', 'g'),
            r['N_lot'],
            f"{r['n_echantillons']}/{r['n_requis']}",
            f"{r['T']:.1f}",
            f"{r['moyenne']:.2f}",
            f"{r['eave']:.2f}",
            f"{r['ecart_type']:.3f}",
            f"{r['nb_T1']}/{r['nb_T1_autorise']}",
            r['nb_T2'],
            f"{r['u_elargie']:.3f}",
            f"{r['taux_non_conformes']:.1f}%",
            statut
        ), tags=(couleur,))

    tree.tag_configure('green', foreground='green')
    tree.tag_configure('red', foreground='red')

    scrollbar_tree = ttk.Scrollbar(cadre_tableau, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscrollcommand=scrollbar_tree.set)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar_tree.pack(side=tk.RIGHT, fill=tk.Y)

    # Boutons
    frame_boutons = tk.Frame(cadre_scrollable)
    frame_boutons.pack(pady=20)

    def voir_detail():
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner un produit")
            return
        item = tree.item(selection[0])
        nom_produit = item['values'][0]
        resultat = next((r for r in resultats_par_produit if r['produit'] == nom_produit), None)
        if resultat:
            afficher_detail_produit(resultat)

    tk.Button(frame_boutons, text="🔍 Voir détail du produit", command=voir_detail,
              font=("Arial", 11), bg="#3498db", fg="white", padx=20, pady=5).pack(side=tk.LEFT, padx=10)

    tk.Button(frame_boutons, text="📄 Générer rapport complet", command=generer_rapport_complet,
              font=("Arial", 11), bg="#e67e22", fg="white", padx=20, pady=5).pack(side=tk.LEFT, padx=10)

    tk.Button(frame_boutons, text="🖨️ Imprimer", command=imprimer_rapport_multi,
              font=("Arial", 11), bg="#1abc9c", fg="white", padx=20, pady=5).pack(side=tk.LEFT, padx=10)

    tk.Button(frame_boutons, text="📊 Voir détails mesures", command=afficher_tableau_mesures,
              font=("Arial", 11), bg="#9b59b6", fg="white", padx=20, pady=5).pack(side=tk.LEFT, padx=10)

    tk.Button(frame_boutons, text="Fermer", command=fenetre_resultats.destroy,
              font=("Arial", 11), bg="gray", fg="white", padx=20, pady=5).pack(side=tk.LEFT, padx=10)


def afficher_tableau_mesures():
    """Affiche un tableau détaillé de toutes les mesures"""
    fenetre_mesures = tk.Toplevel()
    fenetre_mesures.title("Détail des mesures par échantillon")
    fenetre_mesures.geometry("1200x650")

    cadre = tk.Frame(fenetre_mesures)
    cadre.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    tk.Label(cadre, text="DÉTAIL DES MESURES PAR ÉCHANTILLON", font=("Arial", 14, "bold"), fg="blue").pack(pady=10)

    columns = ('N°', 'Produit', 'Lot', 'Qn', 'Unité', 'Masse brute', 'Tare', 'Qi net', 'Erreur', 'Seuil T2', 'Conforme')

    tree = ttk.Treeview(cadre, columns=columns, show='headings', height=20)

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=90)

    tree.column('Produit', width=130)
    tree.column('Lot', width=100)
    tree.column('Unité', width=50)

    for idx, row in donnees.iterrows():
        qnom = row['Qnom']
        unite = row.get('Unite', 'g')
        qi = row['Qi']
        erreur = qi - qnom

        T_arrondi, seuil_T1_sup, seuil_T2 = calculer_seuils(qnom, unite)

        if qi < seuil_T2:
            statut_ech = "❌ T2"
        elif qi < seuil_T1_sup:
            statut_ech = "⚠️ T1"
        else:
            statut_ech = "✅ Conforme"

        tree.insert('', 'end', values=(
            idx + 1,
            row['Nom_Produit'],
            row['Numero_Lot'],
            f"{qnom:.1f}",
            unite,
            f"{row['Masse_brute']:.1f}",
            f"{row['Tare']:.1f}",
            f"{qi:.1f}",
            f"{erreur:+.1f}",
            f"{seuil_T2:.1f}",
            statut_ech
        ))

    scrollbar = ttk.Scrollbar(cadre, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)

    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    tk.Button(cadre, text="Fermer", command=fenetre_mesures.destroy,
              font=("Arial", 11), bg="gray", fg="white", padx=20, pady=5).pack(pady=10)


def afficher_detail_produit(resultat):
    """Affiche les détails d'un produit spécifique avec incertitudes"""
    fenetre_detail = tk.Toplevel()
    fenetre_detail.title(f"Détail - {resultat['produit']}")
    fenetre_detail.geometry("1050x850")

    cadre = tk.Frame(fenetre_detail)
    cadre.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    # En-tête
    statut = "CONFORME ✅" if resultat['conforme'] else "NON CONFORME ❌"
    couleur = "green" if resultat['conforme'] else "red"

    tk.Label(cadre, text=f"Produit: {resultat['produit']}", font=("Arial", 16, "bold")).pack(pady=10)
    tk.Label(cadre, text=f"Statut: {statut}", font=("Arial", 14, "bold"), fg=couleur).pack(pady=5)

    # Informations
    frame_info = tk.Frame(cadre)
    frame_info.pack(pady=20)

    causes_rejet = []
    if not resultat['conformite_moyenne']:
        causes_rejet.append("❌ Moyenne insuffisante")
    if not resultat['conformite_T1']:
        causes_rejet.append(f"❌ T1: {resultat['nb_T1']} > {resultat['nb_T1_autorise']} autorisé")
    if not resultat['conformite_T2']:
        causes_rejet.append(f"❌ T2: {resultat['nb_T2']} > 0 autorisé")

    causes_text = "\n".join(causes_rejet) if causes_rejet else "✅ Tous les critères sont satisfaits"

    # Construction du texte d'information
    infos = f"""
    ╔═══════════════════════════════════════════════════════════════════════════╗
    ║         RAPPORT DE CONFORMITÉ OIML R87:2016                             ║
    ╠═══════════════════════════════════════════════════════════════════════════╣
    ║  📦 PRODUIT                                                             ║
    ║  ├─ Nom: {resultat['produit']}
    ║  ├─ Quantité nominale (Qn): {resultat['quantite_nominale']:.0f} {resultat.get('unite', 'g')}
    ║  ├─ Type de produit: {resultat.get('type_produit', 'solide')}
    ║  └─ Type de contrôle: {'Destructif' if resultat.get('type_controle') == 'D' else 'Non destructif'}
    ╠═══════════════════════════════════════════════════════════════════════════╣
    ║  📊 ÉCHANTILLONNAGE                                                     ║
    ║  ├─ Taille du lot (N): {resultat['N_lot']}
    ║  ├─ Taille échantillon (n): {resultat['n_echantillons']}
    ║  └─ n requis: {resultat['n_requis']}
    ╠═══════════════════════════════════════════════════════════════════════════╣
    ║  📈 STATISTIQUES                                                         ║
    ║  ├─ Moyenne: {resultat['moyenne']:.2f} {resultat.get('unite', 'g')}
    ║  ├─ Erreur moyenne (eave): {resultat['eave']:+.2f} {resultat.get('unite', 'g')}
    ║  ├─ Écart-type (s): {resultat['ecart_type']:.3f} {resultat.get('unite', 'g')}
    ║  ├─ Médiane: {resultat['mediane']:.2f} {resultat.get('unite', 'g')}
    ║  ├─ Minimum: {resultat['min']:.2f} {resultat.get('unite', 'g')}
    ║  └─ Maximum: {resultat['max']:.2f} {resultat.get('unite', 'g')}
    ╠═══════════════════════════════════════════════════════════════════════════╣
    ║  ⚖️ INSUFFISANCE TOLÉRÉE (T)                                            ║
    ║  ├─ T (tolérance): {resultat['T']:.1f} {resultat.get('unite', 'g')}
    ║  ├─ Seuil T1: [{resultat['seuil_T2']:.1f} ; {resultat['seuil_T1_sup']:.1f}[
    ║  └─ Seuil T2: < {resultat['seuil_T2']:.1f} {resultat.get('unite', 'g')}
    ╠═══════════════════════════════════════════════════════════════════════════╣
    ║  📋 CRITÈRES DE CONFORMITÉ                                              ║
    ║  ├─ Essai moyenne (eave ≥ 0): {'✅' if resultat['conformite_moyenne'] else '❌'}
    ║  ├─ Essai T1: {resultat['nb_T1']} ≤ {resultat['nb_T1_autorise']} autorisé {'✅' if resultat['conformite_T1'] else '❌'}
    ║  ├─ Essai T2: {resultat['nb_T2']} = 0 {'✅' if resultat['conformite_T2'] else '❌'}
    ║  └─ Taux de non-conformes: {resultat['taux_non_conformes']:.1f}%
    ╠═══════════════════════════════════════════════════════════════════════════╣
    ║  📐 INCERTITUDES DE MESURE (GUM)                                       ║
    ║  ├─ Balance: {resultat.get('modele_balance', 'Inconnu')}
    ║  ├─ Résolution: {resultat.get('resolution', 0):.3f} {resultat.get('unite', 'g')}
    ║  ├─ Incertitude d'étalonnage (u_cal): {resultat.get('u_cal', 0):.4f} {resultat.get('unite', 'g')}
    ║  ├─ Incertitude de répétabilité (s_repeat): {resultat.get('s_repeat', 0):.4f} {resultat.get('unite', 'g')}
    ║  ├─ Incertitude due à la résolution (u_res): {resultat.get('u_res', 0):.4f} {resultat.get('unite', 'g')}
    ║  ├─ Incertitude-type combinée sur la moyenne (u_moy): {resultat.get('u_moy', 0):.4f} {resultat.get('unite', 'g')}
    ║  └─ Incertitude élargie (k=2, 95%): {resultat.get('u_elargie', 0):.4f} {resultat.get('unite', 'g')}
    ╠═══════════════════════════════════════════════════════════════════════════╣
    ║  📌 DÉCISION                                                            ║
    ║  {causes_text}
    ║  ─────────────────────────────────────────────────────────────────────────
    ║  🔴 Décision finale: {statut}
    ╚═══════════════════════════════════════════════════════════════════════════╝
    """

    tk.Label(frame_info, text=infos, font=("Courier", 9), justify=tk.LEFT).pack()

    # Graphique avec incertitude
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5))

    # Histogramme avec barres d'incertitude sur la moyenne
    ax1.hist(resultat['valeurs'], bins=min(10, resultat['n_echantillons']), edgecolor='black', alpha=0.7, color='skyblue')
    ax1.axvline(resultat['quantite_nominale'], color='red', linestyle='--', label=f'Qn: {resultat["quantite_nominale"]:.0f}', linewidth=2)
    ax1.axvline(resultat['moyenne'], color='green', linestyle='--', label=f'Moy: {resultat["moyenne"]:.1f}', linewidth=2)
    # Barre d'incertitude sur la moyenne
    ax1.errorbar(resultat['moyenne'], 0, xerr=resultat['u_elargie'], color='green', capsize=5, label=f'U(k=2) ±{resultat["u_elargie"]:.2f}')
    ax1.axvline(resultat['seuil_T2'], color='orange', linestyle=':', label=f'Seuil T2: {resultat["seuil_T2"]:.0f}', linewidth=2)
    ax1.axvline(resultat['seuil_T1_sup'], color='purple', linestyle=':', label=f'Seuil T1: {resultat["seuil_T1_sup"]:.0f}', linewidth=2)
    ax1.set_xlabel(f'Masse nette ({resultat.get("unite", "g")})')
    ax1.set_ylabel('Fréquence')
    ax1.set_title('Distribution des mesures')
    ax1.legend(fontsize=8)
    ax1.grid(True, alpha=0.3)

    # Boîte à moustaches
    bp = ax2.boxplot([resultat['valeurs']], vert=True, patch_artist=True)
    bp['boxes'][0].set_facecolor('lightblue')
    ax2.axhline(resultat['quantite_nominale'], color='red', linestyle='--', label='Qn', linewidth=2)
    ax2.axhline(resultat['moyenne'], color='green', linestyle='--', label='Moyenne', linewidth=2)
    ax2.axhline(resultat['seuil_T2'], color='orange', linestyle=':', label='Seuil T2', linewidth=2)
    ax2.axhline(resultat['seuil_T1_sup'], color='purple', linestyle=':', label='Seuil T1', linewidth=2)
    ax2.set_ylabel(f'Masse nette ({resultat.get("unite", "g")})')
    ax2.set_title('Boîte à moustaches')
    ax2.set_xticklabels([resultat['produit']])
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()

    canvas_graph = FigureCanvasTkAgg(fig, cadre)
    canvas_graph.draw()
    canvas_graph.get_tk_widget().pack(fill=tk.BOTH, expand=True, pady=10)

    # Nettoyage de la figure
    def on_close():
        plt.close(fig)
        fenetre_detail.destroy()

    fenetre_detail.protocol("WM_DELETE_WINDOW", on_close)

    # Tableau des lots
    tk.Label(cadre, text="Détail par lot:", font=("Arial", 12, "bold")).pack(pady=10)
    frame_tableau = tk.Frame(cadre)
    frame_tableau.pack(fill=tk.BOTH, expand=True)

    columns = ('Lot', 'Qn', 'Masse brute', 'Tare', 'Qi net', 'Erreur', 'Type erreur')
    tree = ttk.Treeview(frame_tableau, columns=columns, show='headings', height=5)

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=100)
    tree.column('Lot', width=120)

    donnees_produit = donnees[donnees['Nom_Produit'] == resultat['produit']]
    for idx, row in donnees_produit.iterrows():
        qi = row['Qi']
        erreur = qi - resultat['quantite_nominale']

        if qi < resultat['seuil_T2']:
            type_erreur = "❌ T2"
        elif qi < resultat['seuil_T1_sup']:
            type_erreur = "⚠️ T1"
        else:
            type_erreur = "✅ Conforme"

        tree.insert('', 'end', values=(
            row['Numero_Lot'],
            f"{row['Qnom']:.0f}",
            f"{row['Masse_brute']:.1f}",
            f"{row['Tare']:.1f}",
            f"{qi:.1f}",
            f"{erreur:+.1f}",
            type_erreur
        ))

    tree.pack(fill=tk.BOTH, expand=True)

    tk.Button(cadre, text="Fermer", command=on_close,
              font=("Arial", 11), bg="gray", fg="white", padx=20, pady=5).pack(pady=10)


# ============ Génération de rapport HTML ============
def generer_rapport_complet():
    """Génère un rapport HTML complet avec incertitudes"""
    if not resultats_par_produit:
        messagebox.showwarning("Attention", "Veuillez d'abord calculer la conformité")
        return

    try:
        nb_conformes = sum(1 for r in resultats_par_produit if r['conforme'])

        rapport_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Rapport de Conformité OIML R87:2016</title>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; }}
                h2 {{ color: #34495e; margin-top: 30px; background: #ecf0f1; padding: 10px; }}
                .conforme {{ color: green; font-weight: bold; }}
                .non-conforme {{ color: red; font-weight: bold; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 10px; text-align: center; }}
                th {{ background-color: #3498db; color: white; }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }}
                .header {{ background-color: #2c3e50; color: white; padding: 20px; text-align: center; }}
                .footer {{ margin-top: 50px; text-align: center; font-size: 12px; }}
                .summary {{ background-color: #e8f4f8; padding: 15px; margin: 20px 0; border-radius: 5px; }}
                .info-produit {{ background-color: #f9f9f9; padding: 10px; margin: 10px 0; border-left: 4px solid #3498db; }}
                .incertitude {{ background-color: #fff3cd; padding: 10px; margin: 10px 0; border-left: 4px solid #ffc107; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1 style="color: white;">Rapport de Conformité OIML R87:2016</h1>
                <p>Contrôle métrologique des produits préemballés</p>
                <p>Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
            </div>
            <div class="summary">
                <h2>Résumé global</h2>
                <p>📊 Total produits contrôlés: <strong>{len(resultats_par_produit)}</strong></p>
                <p>✅ Produits conformes: <strong class="conforme">{nb_conformes}</strong> ({nb_conformes / len(resultats_par_produit) * 100:.1f}%)</p>
                <p>❌ Produits non conformes: <strong class="non-conforme">{len(resultats_par_produit) - nb_conformes}</strong> ({(len(resultats_par_produit) - nb_conformes) / len(resultats_par_produit) * 100:.1f}%)</p>
            </div>

            <h2>Détail par produit</h2>
            <table>
                <thead>
                    <tr>
                        <th>Produit</th>
                        <th>Qn</th>
                        <th>Unité</th>
                        <th>N</th>
                        <th>n</th>
                        <th>T</th>
                        <th>Moyenne</th>
                        <th>eave</th>
                        <th>Écart-type</th>
                        <th>T1</th>
                        <th>T2</th>
                        <th>U (k=2)</th>
                        <th>Statut</th>
                    </tr>
                </thead>
                <tbody>
        """

        for r in resultats_par_produit:
            statut_class = "conforme" if r['conforme'] else "non-conforme"
            statut_text = "CONFORME" if r['conforme'] else "NON CONFORME"
            rapport_html += f"""
                    <tr>
                        <td>{r['produit']}</td>
                        <td>{r['quantite_nominale']:.0f}</td>
                        <td>{r.get('unite', 'g')}</td>
                        <td>{r['N_lot']}</td>
                        <td>{r['n_echantillons']}</td>
                        <td>{r['T']:.1f}</td>
                        <td>{r['moyenne']:.2f}</td>
                        <td>{r['eave']:+.2f}</td>
                        <td>{r['ecart_type']:.3f}</td>
                        <td>{r['nb_T1']}/{r['nb_T1_autorise']}</td>
                        <td>{r['nb_T2']}</td>
                        <td>{r['u_elargie']:.3f}</td>
                        <td class="{statut_class}">{statut_text}</td>
                    </tr>
            """
        rapport_html += """
                </tbody>
            </table>

            <h2>Incertitudes de mesure</h2>
            <table>
                <thead>
                    <tr>
                        <th>Produit</th>
                        <th>Balance</th>
                        <th>Résolution</th>
                        <th>u_cal</th>
                        <th>s_repeat</th>
                        <th>u_res</th>
                        <th>u_moy</th>
                        <th>U (k=2)</th>
                    </tr>
                </thead>
                <tbody>
        """
        for r in resultats_par_produit:
            rapport_html += f"""
                    <tr>
                        <td>{r['produit']}</td>
                        <td>{r.get('modele_balance', 'Inconnu')}</td>
                        <td>{r.get('resolution', 0):.3f}</td>
                        <td>{r.get('u_cal', 0):.4f}</td>
                        <td>{r.get('s_repeat', 0):.4f}</td>
                        <td>{r.get('u_res', 0):.4f}</td>
                        <td>{r.get('u_moy', 0):.4f}</td>
                        <td>{r.get('u_elargie', 0):.4f}</td>
                    </tr>
            """
        rapport_html += """
                </tbody>
            </table>

            <h2>Détail des critères de conformité</h2>
            <table>
                <thead>
                    <tr>
                        <th>Produit</th>
                        <th>Essai moyenne</th>
                        <th>Essai T1</th>
                        <th>Essai T2</th>
                        <th>Décision</th>
                    </tr>
                </thead>
                <tbody>
        """
        for r in resultats_par_produit:
            moyenne_ok = "✅ OK" if r['conformite_moyenne'] else "❌ KO"
            t1_ok = f"✅ OK ({r['nb_T1']} ≤ {r['nb_T1_autorise']})" if r['conformite_T1'] else f"❌ KO ({r['nb_T1']} > {r['nb_T1_autorise']})"
            t2_ok = "✅ OK (0)" if r['conformite_T2'] else f"❌ KO ({r['nb_T2']} > 0)"
            decision = "✅ CONFORME" if r['conforme'] else "❌ NON CONFORME"
            rapport_html += f"""
                    <tr>
                        <td>{r['produit']}</td>
                        <td>{moyenne_ok}</td>
                        <td>{t1_ok}</td>
                        <td>{t2_ok}</td>
                        <td>{decision}</td>
                    </tr>
            """
        rapport_html += """
                </tbody>
            </table>

            <div class="info-produit">
                <strong>📋 Méthode de calcul OIML R87:2016 :</strong><br>
                - Masse nette (Qi) = Masse_brute - Tare (contrôle non destructif)<br>
                - Insuffisance tolérée T selon Tableau 3<br>
                - Essai T1: (Qn - 2T) ≤ Qi < (Qn - T)<br>
                - Essai T2: Qi < (Qn - 2T)<br>
                - Essai moyenne: eave + (FCE × s) ≥ 0<br>
                - Incertitudes calculées selon GUM (k=2, 95% de confiance)
            </div>
            <div class="incertitude">
                <strong>📐 Incertitudes de mesure :</strong><br>
                - <strong>u_cal</strong> : incertitude d'étalonnage de la balance<br>
                - <strong>s_repeat</strong> : écart-type de répétabilité (type A)<br>
                - <strong>u_res</strong> : incertitude due à la résolution<br>
                - <strong>u_moy</strong> : incertitude-type combinée sur la moyenne<br>
                - <strong>U (k=2)</strong> : incertitude élargie (95% de confiance)
            </div>
            <div class="footer">
                <p>Rapport généré automatiquement - Application Métrologique OIML R87:2016</p>
            </div>
        </body>
        </html>
        """

        nom_fichier = f"rapport_r87_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(nom_fichier, 'w', encoding='utf-8') as f:
            f.write(rapport_html)

        webbrowser.open('file://' + os.path.realpath(nom_fichier))
        messagebox.showinfo("Succès", f"Rapport généré: {nom_fichier}")

    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur: {str(e)}")


def imprimer_rapport_multi():
    """Version imprimable du rapport"""
    if not resultats_par_produit:
        messagebox.showwarning("Attention", "Veuillez d'abord calculer la conformité")
        return

    fd, temp_path = tempfile.mkstemp(suffix='.html', prefix='rapport_r87_')
    os.close(fd)

    nb_conformes = sum(1 for r in resultats_par_produit if r['conforme'])

    rapport_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Rapport R87:2016</title>
        <meta charset="UTF-8">
        <style>
            @media print {{ body {{ margin: 0; padding: 20px; }} .no-print {{ display: none; }} }}
            body {{ font-family: Arial, sans-serif; }}
            h1 {{ color: #2c3e50; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: center; }}
            th {{ background-color: #3498db; color: white; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .conforme {{ color: green; }}
            .non-conforme {{ color: red; }}
        </style>
    </head>
    <body>
        <div class="no-print" style="text-align: center; margin-bottom: 20px;">
            <button onclick="window.print();">🖨️ Imprimer</button>
            <button onclick="window.close();">❌ Fermer</button>
        </div>
        <div class="header">
            <h1>Rapport de Conformité OIML R87:2016</h1>
            <p>Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
        </div>
        <h2>Résumé</h2>
        <p>Total produits: {len(resultats_par_produit)}</p>
        <p>Conformes: {nb_conformes}</p>
        <p>Non conformes: {len(resultats_par_produit) - nb_conformes}</p>

        <h2>Détail par produit</h2>
        <table>
            <tr><th>Produit</th><th>Qn</th><th>Unité</th><th>n</th><th>T</th><th>Moyenne</th><th>eave</th><th>T1</th><th>T2</th><th>U(k=2)</th><th>Statut</th></tr>
    """
    for r in resultats_par_produit:
        statut_class = "conforme" if r['conforme'] else "non-conforme"
        statut_text = "CONFORME" if r['conforme'] else "NON CONFORME"
        rapport_html += f"""
            <tr>
                <td>{r['produit']}</td>
                <td>{r['quantite_nominale']:.0f}</td>
                <td>{r.get('unite', 'g')}</td>
                <td>{r['n_echantillons']}</td>
                <td>{r['T']:.1f}</td>
                <td>{r['moyenne']:.2f}</td>
                <td>{r['eave']:+.2f}</td>
                <td>{r['nb_T1']}/{r['nb_T1_autorise']}</td>
                <td>{r['nb_T2']}</td>
                <td>{r['u_elargie']:.3f}</td>
                <td class="{statut_class}">{statut_text}</td>
            </tr>
        """
    rapport_html += """
        </table>
        <div class="footer"><p>Conforme à OIML R87:2016</p></div>
    </body>
    </html>
    """
    with open(temp_path, 'w', encoding='utf-8') as f:
        f.write(rapport_html)

    webbrowser.open('file://' + os.path.realpath(temp_path))

    def supprimer_fichier():
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except:
            pass
    # Supprimer après 5 secondes
    try:
        root.after(5000, supprimer_fichier)
    except:
        pass


# ============ Interface principale ============
root = tk.Tk()
root.title("Application Métrologique OIML R87:2016")
root.geometry("800x650")

# En-tête
title = tk.Label(root, text="Contrôle de Conformité OIML R87:2016", font=("Arial", 18, "bold"), fg="#2c3e50")
title.pack(pady=20)

description = tk.Label(root,
                       text="Application dédiée au contrôle métrologique des produits préemballés\n"
                            "Conforme à la Recommandation OIML R87:2016\n"
                            "Intègre les types de contrôle, produits liquides et incertitudes de mesure",
                       font=("Arial", 11), fg="#7f8c8d", justify=tk.CENTER)
description.pack(pady=5)

# Cadre des boutons
cadre_boutons = tk.Frame(root)
cadre_boutons.pack(pady=30)

btn1 = tk.Button(cadre_boutons, text="📂 Importer données Excel", command=charger_donnees,
                 font=("Arial", 12), bg="#3498db", fg="white", padx=20, pady=10, width=35)
btn1.pack(pady=10)

btn2 = tk.Button(cadre_boutons, text="🔬 Calculer Conformité (OIML R87:2016)", command=calculer_conformite,
                 font=("Arial", 12), bg="#2ecc71", fg="white", padx=20, pady=10, width=35)
btn2.pack(pady=10)

btn3 = tk.Button(cadre_boutons, text="❌ Quitter", command=root.quit,
                 font=("Arial", 12), bg="#e74c3c", fg="white", padx=20, pady=10, width=35)
btn3.pack(pady=10)

# Instructions
info_frame = tk.LabelFrame(root, text="Format du fichier Excel attendu", font=("Arial", 11, "bold"))
info_frame.pack(fill=tk.X, padx=20, pady=20)

info_text = """
Colonnes obligatoires:
• Nom_Produit : Nom du produit
• Numero_Lot : Numéro de lot (ou 'N/A' si absent)
• Qnom : Quantité nominale (dans l'unité spécifiée)
• Masse_brute : Masse brute mesurée (g)
• Tare : Masse de l'emballage (g)

Colonnes optionnelles:
• Taille_Lot : Taille du lot N (sinon N = n)
• Unite : 'g', 'mL', 'L', 'longueur', 'surface', 'nombre' (par défaut 'g')
• Type_Produit : 'solide', 'liquide', 'liquide_avec_solide', 'congele' (défaut 'solide')
• Type_Controle : 'ND' (non destructif) ou 'D' (destructif) (défaut 'ND')
• Masse_egouttee : Masse égouttée pour les produits en liquide de couverture (g)
• Resolution : Résolution de la balance (g)
• Incertitude_Etalonnage : Incertitude-type d'étalonnage (g)
• Modele_Balance : Modèle de la balance

Calculs automatiques:
• Qi = Masse_brute - Tare (ou Masse_egouttee si présent)
• T selon Tableau 3
• n, FCE, nb_T1_autorise
• Essais moyenne, T1, T2
• Incertitudes (type A, B, combinée, élargie)
"""
tk.Label(info_frame, text=info_text, font=("Arial", 10), justify=tk.LEFT, fg="#555").pack(pady=10)

# Pied de page
footer = tk.Label(root, text="© Laboratoire de Métrologie - OIML R87:2016",
                  font=("Arial", 9), fg="gray")
footer.pack(side=tk.BOTTOM, pady=10)

root.mainloop()