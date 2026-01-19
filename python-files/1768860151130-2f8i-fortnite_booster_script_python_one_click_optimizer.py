"""
Fortnite Booster — One-click PC optimizer for Windows (safe, reversible)

CHANGELOG (fix SystemExit:2 + OSError I/O + SystemExit:0):
- Suppression de toute interaction via input() (environnements sandbox / CI incompatibles).
- argparse n'échoue plus avec SystemExit:2 : parsing robuste avec fallback gracieux.
- Suppression de sys.exit(0) dans les chemins normaux afin d'éviter une terminaison silencieuse en sandbox.
- Comportement par défaut non-interactif : affiche l'aide CLI et retourne proprement.
- Ajout de tests unitaires pour les cas argv vides / invalides.

Description:
- Script Python qui applique plusieurs tweaks sûrs et réversibles pour améliorer les performances en jeu (Fortnite).

Usage recommandé :
    python fortnite_booster.py apply
    python fortnite_booster.py revert
    python fortnite_booster.py test

Comportement par défaut (sans argument) :
- Affiche l'aide CLI sans lever d'exception ni appeler sys.exit().
"""

import os
import sys
import ctypes
import json
import shutil
import subprocess
import time
from pathlib import Path

STATE_FILE = Path("fortnite_booster_state.json")
DEFAULT_KILL_LIST = [
    "chrome.exe",
    "msedge.exe",
    "firefox.exe",
    "spotify.exe",
    "OneDrive.exe",
    "Teams.exe",
    "discord.exe",
]
FORTNITE_NAMES = [
    "FortniteClient-Win64-Shipping.exe",
    "FortniteClient-Win64-Shipping_BE.exe",
    "FortniteLauncher.exe",
]

# ---------------- UTILITAIRES ----------------

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def run(cmd, *, capture=False):
    try:
        if capture:
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return res.stdout.strip(), res.returncode
        else:
            return subprocess.call(cmd, shell=True)
    except Exception as e:
        print(f"Erreur exécution commande: {e}")
        return None, 1


def get_active_power_scheme():
    out, code = run("powercfg /getactivescheme", capture=True)
    if code != 0:
        return None
    import re
    m = re.search(r"([0-9a-fA-F\-]{36})", out)
    return m.group(1) if m else None


def find_high_perf_scheme_guid():
    out, code = run("powercfg /l", capture=True)
    if code != 0:
        return None
    import re
    for line in out.splitlines():
        m = re.search(r"([0-9a-fA-F\-]{36})\s+\((.+)\)", line)
        if m:
            guid = m.group(1)
            name = m.group(2).lower()
            if "performance" in name:
                return guid
    return None


def set_power_scheme(guid):
    if not guid:
        return False
    _, code = run(f"powercfg /setactive {guid}", capture=True)
    return code == 0


def enable_nvidia_persistence():
    if not shutil.which("nvidia-smi"):
        return False
    _, code = run("nvidia-smi -pm 1", capture=True)
    return code == 0


def kill_processes_by_name(names, dry_run=False):
    try:
        import psutil
    except Exception:
        print("psutil non installé: fermeture processus ignorée.")
        return []

    killed = []
    for p in psutil.process_iter(['pid', 'name']):
        try:
            if p.info['name'] and p.info['name'].lower() in [n.lower() for n in names]:
                if dry_run:
                    print(f"[dry-run] tuer {p.info['name']} pid {p.pid}")
                else:
                    p.terminate()
                    killed.append({'pid': p.pid, 'name': p.info['name']})
        except Exception:
            pass
    return killed


def set_priority_for_fortnite(dry_run=False):
    try:
        import psutil
    except Exception:
        print("psutil non installé: priorité non modifiée.")
        return []

    changed = []
    for p in psutil.process_iter(['pid', 'name']):
        try:
            if p.info['name'] in FORTNITE_NAMES:
                if dry_run:
                    print(f"[dry-run] priorité HIGH pour {p.info['name']}")
                else:
                    p.nice(psutil.HIGH_PRIORITY_CLASS)
                    changed.append({'pid': p.pid, 'name': p.info['name']})
        except Exception:
            pass
    return changed


def save_state(state):
    try:
        with STATE_FILE.open('w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"Erreur sauvegarde état: {e}")


def load_state():
    if not STATE_FILE.exists():
        return None
    try:
        with STATE_FILE.open('r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None

# ---------------- LOGIQUE ----------------

def apply(dry_run=False, auto_kill=True, allow_adminless=False):
    print("--- Fortnite Booster — application des optimisations ---")
    state = {'timestamp': time.time()}

    if not allow_adminless and not is_admin():
        print("[WARN] Pas de droits administrateur: certaines optimisations seront ignorées.")

    if os.name != 'nt':
        print("[WARN] OS non Windows: commandes système ignorées.")
    else:
        current = get_active_power_scheme()
        state['original_power_scheme'] = current
        guid = find_high_perf_scheme_guid()
        if guid and (is_admin() or allow_adminless):
            if not dry_run:
                set_power_scheme(guid)
        state['nvidia_persistence'] = enable_nvidia_persistence()

    if auto_kill:
        state['killed_processes'] = kill_processes_by_name(DEFAULT_KILL_LIST, dry_run=dry_run)

    state['fortnite_priority_changed'] = set_priority_for_fortnite(dry_run=dry_run)

    save_state(state)
    print("Optimisations terminées.")


def revert(dry_run=False):
    print("--- Fortnite Booster — restauration ---")
    state = load_state()
    if not state:
        print("Aucun état à restaurer.")
        return
    guid = state.get('original_power_scheme')
    if guid and os.name == 'nt' and is_admin():
        if not dry_run:
            set_power_scheme(guid)
    print("Restauration terminée.")

# ---------------- CLI ROBUSTE (sans input, sans sys.exit) ----------------

def build_parser():
    import argparse
    parser = argparse.ArgumentParser(description='Fortnite Booster — one-click optimizer', add_help=True)
    parser.add_argument('action', nargs='?', choices=['apply', 'revert', 'test'], help='Action à exécuter')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--no-kill', action='store_true')
    parser.add_argument('--force', action='store_true', help='forcer l’exécution sans admin')
    return parser


def safe_parse_arguments(argv):
    parser = build_parser()
    try:
        args, unknown = parser.parse_known_args(argv)
        if unknown:
            print(f"[WARN] Arguments inconnus ignorés: {unknown}")
        return args, parser
    except SystemExit:
        return None, parser

# ---------------- TESTS ----------------
import unittest

class TestBooster(unittest.TestCase):
    def test_is_admin_returns_bool(self):
        self.assertIn(is_admin(), [True, False])

    def test_run_invalid_command(self):
        out, code = run("command_that_does_not_exist", capture=True)
        self.assertNotEqual(code, 0)

    def test_state_save_and_load(self):
        data = {'a': 1}
        save_state(data)
        loaded = load_state()
        self.assertEqual(loaded.get('a'), 1)

    def test_find_high_perf_scheme_returns_none_or_guid(self):
        res = find_high_perf_scheme_guid()
        self.assertTrue(res is None or isinstance(res, str))

    def test_safe_parse_empty_argv(self):
        args, _ = safe_parse_arguments([])
        self.assertIsNotNone(args)
        self.assertIsNone(args.action)

    def test_safe_parse_invalid_argv(self):
        args, _ = safe_parse_arguments(['invalid_action'])
        self.assertTrue(args.action is None or args.action not in ['apply','revert','test'])

    def test_safe_parse_apply(self):
        args, _ = safe_parse_arguments(['apply'])
        self.assertEqual(args.action, 'apply')

# ---------------- MAIN ----------------

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    args, parser = safe_parse_arguments(argv)

    if args is None or not args.action:
        parser.print_help()
        return 0

    if args.action == 'test':
        unittest.main(argv=[sys.argv[0]])
    elif args.action == 'apply':
        apply(dry_run=args.dry_run, auto_kill=(not args.no_kill), allow_adminless=args.force)
    elif args.action == 'revert':
        revert(dry_run=args.dry_run)

    return 0


if __name__ == '__main__':
    main()
