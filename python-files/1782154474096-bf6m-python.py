import sys
import os
import json
from datetime import datetime
import psutil

# ============================================================
# kill-malware.py — Wazuh Active Response
# Tue le processus cible + tous ses descendants (récursif)
# ============================================================

# 0. Configuration du log
log_dir = r"C:\Program Files (x86)\ossec-agent\active-response"
log_file = os.path.join(log_dir, "kill-malware.log")

# Création du dossier et du fichier s'ils n'existent pas
if not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True)

if not os.path.exists(log_file):
    with open(log_file, "w", encoding="utf-8") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"=== kill-malware.log — créé le {timestamp} ===\n")
        f.write("---------------------------------------------------------------\n")


def write_log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")


# 1. Lecture stdin
try:
    input_json = sys.stdin.read()
except Exception as e:
    write_log(f"ERREUR : Impossible de lire stdin — {str(e)}")
    sys.exit(1)

if not input_json or input_json.strip() == "":
    write_log("ERREUR : stdin vide, aucune alerte reçue.")
    sys.exit(1)

# 2. Parse JSON
try:
    alert = json.loads(input_json)
except Exception as e:
    write_log(f"ERREUR : JSON invalide — {str(e)}")
    sys.exit(1)

# 3. Extraction du PID
try:
    pid_raw = alert["parameters"]["alert"]["data"]["win"]["eventdata"]["processId"]
except KeyError:
    write_log("ERREUR : PID introuvable dans l'alerte JSON.")
    sys.exit(1)

# 4. Conversion hex -> int (gère le format '0x...' ou '1234')
try:
    if str(pid_raw).startswith("0x"):
        pid_to_kill = int(pid_raw, 16)
    else:
        pid_to_kill = int(pid_raw)
except Exception as e:
    write_log(
        f"ERREUR : Conversion PID échouée pour valeur '{pid_raw}' — {str(e)}"
    )
    sys.exit(1)

# Récupérer le nom du processus cible pour le log
process_name = "inconnu"
try:
    proc = psutil.Process(pid_to_kill)
    process_name = proc.name()
except psutil.NoSuchProcess:
    pass

write_log(f">>> Déclenchement AR — PID cible : {pid_to_kill} ({process_name})")


# 5. Fonction récursive : tue tous les descendants
def kill_process_tree(parent_pid):
    try:
        parent = psutil.Process(parent_pid)
        # .children() récupère tous les sous-processus de manière récursive
        children = parent.children(recursive=True)

        for child in children:
            try:
                child_pid = child.pid
                child_name = child.name()
                child.kill()  # Équivalent de Stop-Process -Force
                write_log(f"  [ENFANT tué] PID {child_pid} ({child_name})")
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                write_log(f"  [ECHEC enfant] PID {child_pid} — {str(e)}")
    except psutil.NoSuchProcess:
        # Le processus parent n'existe déjà plus ou n'a pas d'enfants
        pass


# 6. Tuer les descendants
kill_process_tree(pid_to_kill)

# 7. Tuer le processus racine (Parent)
try:
    parent_proc = psutil.Process(pid_to_kill)
    parent_proc.kill()
    write_log(f"  [PARENT tué] PID {pid_to_kill} ({process_name})")
except psutil.NoSuchProcess:
    write_log(
        f"  [INFO parent] PID {pid_to_kill} déjà arrêté ou introuvable."
    )
except psutil.AccessDenied as e:
    write_log(f"  [ECHEC parent] PID {pid_to_kill} — {str(e)}")

write_log(f"<<< AR terminé pour PID {pid_to_kill}")
write_log("---------------------------------------------------------------\n")

sys.exit(0)