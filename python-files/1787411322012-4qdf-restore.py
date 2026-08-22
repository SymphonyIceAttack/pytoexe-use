from pathlib import Path
import zipfile


PROFILE_NAME = "vanilla-1.21"

LUNAR_PROFILE_DIR = (
    Path.home()
    / ".lunarclient"
    / "profiles"
    / PROFILE_NAME
)

MODS_DIR = LUNAR_PROFILE_DIR / "mods"
BACKUP_DIR = LUNAR_PROFILE_DIR / "backups"


def get_backups():
    if not BACKUP_DIR.exists():
        return []

    return sorted(
        (
            file
            for file in BACKUP_DIR.iterdir()
            if file.is_file()
            and file.suffix.lower() == ".zip"
            and file.name.startswith("mods_backup_")
        ),
        key=lambda file: file.stat().st_mtime,
        reverse=True
    )


def get_current_mods():
    if not MODS_DIR.exists():
        return []

    return [
        file
        for file in MODS_DIR.iterdir()
        if file.is_file()
        and file.suffix.lower() == ".jar"
    ]


def remove_current_mods():
    mods = get_current_mods()

    for mod in mods:
        mod.unlink()

    return len(mods)


def get_backup_mods(backup):
    with zipfile.ZipFile(backup, "r") as archive:
        return [
            name
            for name in archive.namelist()
            if name.lower().endswith(".jar")
            and not Path(name).name == ""
        ]


def restore_backup(backup):
    MODS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with zipfile.ZipFile(backup, "r") as archive:

        for name in get_backup_mods(backup):

            filename = Path(name).name

            if not filename:
                continue

            destination = MODS_DIR / filename

            with archive.open(name, "r") as source:
                with destination.open("wb") as target:
                    target.write(source.read())


def verify_backup(backup):

    with zipfile.ZipFile(backup, "r") as archive:

        for name in get_backup_mods(backup):

            filename = Path(name).name
            destination = MODS_DIR / filename

            if not destination.exists():
                raise RuntimeError(
                    f"Fichier manquant : {filename}"
                )

            expected_size = archive.getinfo(name).file_size
            actual_size = destination.stat().st_size

            if actual_size != expected_size:
                raise RuntimeError(
                    f"Fichier incorrect : {filename}"
                )


def main():

    print()
    print("=" * 60)
    print("             THE HARPY EXPRESS")
    print("                   RESTORE")
    print("=" * 60)
    print()

    print("Profil cible :")
    print(PROFILE_NAME)

    print()
    print("Dossier mods :")
    print(MODS_DIR)

    print()
    print("Recherche de la backup...")

    backups = get_backups()

    if not backups:
        raise RuntimeError(
            "Aucune backup trouvée dans :\n"
            f"{BACKUP_DIR}"
        )

    backup = backups[0]

    print()
    print("Backup sélectionnée :")
    print(backup)

    backup_mods = get_backup_mods(backup)

    if not backup_mods:
        raise RuntimeError(
            "La backup ne contient aucun fichier .jar."
        )

    print()
    print(
        f"{len(backup_mods)} mod(s) à restaurer."
    )

    print()
    print("Suppression des mods actuels...")

    removed = remove_current_mods()

    print(
        f"{removed} mod(s) supprimé(s)."
    )

    print()
    print("Restauration de la backup...")

    restore_backup(backup)

    print()
    print("Vérification...")

    verify_backup(backup)

    print()
    print("Vérification réussie.")

    # La backup n'est supprimée QU'APRÈS
    # la vérification complète.

    backup.unlink()

    print()
    print("Backup supprimée.")

    print()
    print("=" * 60)
    print("          RESTAURATION RÉUSSIE")
    print("=" * 60)
    print()

    print(
        f"{len(backup_mods)} mod(s) restauré(s)."
    )

    print()
    print("Appuie sur Entrée pour fermer...")

    input()


if __name__ == "__main__":

    try:
        main()

    except Exception as error:

        print()
        print("=" * 60)
        print("          RESTAURATION ÉCHOUÉE")
        print("=" * 60)
        print()

        print(error)

        print()
        print(
            "La backup n'a PAS été supprimée."
        )

        print()
        print("Appuie sur Entrée pour fermer...")

        input()