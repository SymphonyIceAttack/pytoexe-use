from pathlib import Path
from datetime import datetime
import shutil
import sys
import zipfile


# ============================================================
# CONFIGURATION
# ============================================================

PROFILE_NAME = "vanilla-1.21"


# ============================================================
# DOSSIER THE HARPY EXPRESS
# ============================================================

# C:\Users\<Utilisateur>\Downloads\TheHarpyExpress

BASE_DIR = (
    Path.home()
    / "Downloads"
    / "TheHarpyExpress"
)


# ============================================================
# DOSSIERS LUNAR CLIENT
# ============================================================

LUNAR_PROFILE_DIR = (
    Path.home()
    / ".lunarclient"
    / "profiles"
    / PROFILE_NAME
)

DESTINATION_MODS_DIR = (
    LUNAR_PROFILE_DIR
    / "mods"
)

BACKUP_DIR = (
    LUNAR_PROFILE_DIR
    / "backups"
)


# ============================================================
# DOSSIER SOURCE DES MODS
# ============================================================

SOURCE_MODS_DIR = (
    BASE_DIR
    / "mods"
)


# ============================================================
# RECHERCHE DES MODS
# ============================================================

def get_mods(directory):

    if not directory.exists():
        return []

    return sorted(
        [
            file
            for file in directory.iterdir()
            if file.is_file()
            and file.suffix.lower() == ".jar"
        ],
        key=lambda file: file.name.lower()
    )


# ============================================================
# CRÉATION DE LA BACKUP
# ============================================================

def create_backup(old_mods):

    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    timestamp = datetime.now().strftime(
        "%Y-%m-%d_%H-%M-%S"
    )

    backup_file = (
        BACKUP_DIR
        / f"mods_backup_{timestamp}.zip"
    )

    with zipfile.ZipFile(
        backup_file,
        mode="w",
        compression=zipfile.ZIP_DEFLATED
    ) as archive:

        for mod in old_mods:

            archive.write(
                mod,
                arcname=mod.name
            )

    return backup_file


# ============================================================
# SUPPRESSION DES ANCIENS MODS
# ============================================================

def remove_old_mods(old_mods):

    for mod in old_mods:

        try:

            mod.unlink()

        except Exception as error:

            raise RuntimeError(
                f"Impossible de supprimer :\n"
                f"{mod}\n\n"
                f"Erreur : {error}"
            )


# ============================================================
# INSTALLATION DES NOUVEAUX MODS
# ============================================================

def install_new_mods(new_mods):

    DESTINATION_MODS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    for index, mod in enumerate(
        new_mods,
        start=1
    ):

        destination = (
            DESTINATION_MODS_DIR
            / mod.name
        )

        print(
            f"    [{index}/{len(new_mods)}] "
            f"{mod.name}"
        )

        shutil.copy2(
            mod,
            destination
        )


# ============================================================
# VÉRIFICATION DE L'INSTALLATION
# ============================================================

def verify_installation(new_mods):

    for mod in new_mods:

        destination = (
            DESTINATION_MODS_DIR
            / mod.name
        )

        if not destination.exists():

            raise RuntimeError(
                f"Le mod suivant n'a pas été installé :\n"
                f"{mod.name}"
            )

        if (
            destination.stat().st_size
            != mod.stat().st_size
        ):

            raise RuntimeError(
                f"Le fichier installé semble incorrect :\n"
                f"{mod.name}"
            )


# ============================================================
# INSTALLATION PRINCIPALE
# ============================================================

def install():

    print()
    print("=" * 65)
    print("                 THE HARPY EXPRESS")
    print("=" * 65)
    print()

    print("Profil cible :")
    print(PROFILE_NAME)

    print()
    print("Dossier cible :")
    print(DESTINATION_MODS_DIR)

    print()
    print("Dossier source :")
    print(SOURCE_MODS_DIR)

    print()

    # ========================================================
    # ÉTAPE 1 : RECHERCHE DES NOUVEAUX MODS
    # ========================================================

    print("[1/5] Recherche des nouveaux mods...")
    print()

    if not BASE_DIR.exists():

        raise RuntimeError(
            "Le dossier TheHarpyExpress est introuvable :\n\n"
            f"{BASE_DIR}"
        )

    if not SOURCE_MODS_DIR.exists():

        raise RuntimeError(
            "Le dossier 'mods' est introuvable :\n\n"
            f"{SOURCE_MODS_DIR}"
        )

    new_mods = get_mods(
        SOURCE_MODS_DIR
    )

    if not new_mods:

        raise RuntimeError(
            "Aucun fichier .jar n'a été trouvé dans :\n\n"
            f"{SOURCE_MODS_DIR}"
        )

    print(
        f"{len(new_mods)} nouveau(x) mod(s) trouvé(s)."
    )

    print()

    # ========================================================
    # ÉTAPE 2 : PRÉPARATION DU PROFIL
    # ========================================================

    print("[2/5] Préparation du profil Lunar Client...")
    print()

    LUNAR_PROFILE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    DESTINATION_MODS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print(
        "Profil prêt."
    )

    print()

    # ========================================================
    # ÉTAPE 3 : BACKUP DES ANCIENS MODS
    # ========================================================

    print("[3/5] Sauvegarde des anciens mods...")
    print()

    old_mods = get_mods(
        DESTINATION_MODS_DIR
    )

    backup_file = None

    if old_mods:

        print(
            f"{len(old_mods)} ancien(s) mod(s) trouvé(s)."
        )

        print()
        print(
            "Création de la sauvegarde ZIP..."
        )

        backup_file = create_backup(
            old_mods
        )

        if not backup_file.exists():

            raise RuntimeError(
                "La sauvegarde n'a pas été créée."
            )

        print()
        print(
            "Sauvegarde créée :"
        )

        print(
            backup_file
        )

        print()
        print(
            "Suppression des anciens mods..."
        )

        remove_old_mods(
            old_mods
        )

        print(
            "Anciens mods supprimés."
        )

    else:

        print(
            "Aucun ancien mod trouvé."
        )

    print()

    # ========================================================
    # ÉTAPE 4 : INSTALLATION
    # ========================================================

    print("[4/5] Installation des nouveaux mods...")
    print()

    install_new_mods(
        new_mods
    )

    print()

    # ========================================================
    # ÉTAPE 5 : VÉRIFICATION
    # ========================================================

    print("[5/5] Vérification de l'installation...")
    print()

    verify_installation(
        new_mods
    )

    print(
        "Tous les mods ont été vérifiés avec succès."
    )

    print()

    # ========================================================
    # RÉSUMÉ
    # ========================================================

    print("=" * 65)
    print("                 INSTALLATION RÉUSSIE")
    print("=" * 65)
    print()

    print(
        f"{len(new_mods)} mod(s) installé(s)."
    )

    print()
    print(
        "Dossier final :"
    )

    print(
        DESTINATION_MODS_DIR
    )

    if backup_file:

        print()
        print(
            "Backup disponible ici :"
        )

        print(
            backup_file
        )

    print()
    print(
        "Le dossier TheHarpyExpress "
        "n'a pas été modifié."
    )

    print()
    print(
        "Tu peux maintenant utiliser Restore.exe "
        "pour revenir à l'installation précédente."
    )


# ============================================================
# PROGRAMME PRINCIPAL
# ============================================================

def main():

    try:

        install()

        print()
        print(
            "Installation terminée."
        )

    except Exception as error:

        print()
        print("=" * 65)
        print("                 INSTALLATION ÉCHOUÉE")
        print("=" * 65)
        print()

        print(
            str(error)
        )

        print()
        print(
            "Aucun nettoyage automatique n'a été effectué."
        )

    print()
    input(
        "Appuie sur Entrée pour fermer..."
    )


# ============================================================
# LANCEMENT
# ============================================================

if __name__ == "__main__":
    main()