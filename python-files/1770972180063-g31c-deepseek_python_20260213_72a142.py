#!/usr/bin/env python3
"""
Système de Protection PC Évolutif
Surveillance, détection et blocage des menaces
"""

import os
import sys
import psutil
import hashlib
import json
import time
import threading
import subprocess
import platform
import signal
from datetime import datetime, timedelta
from pathlib import Path
import winreg
import ctypes
import socket
import requests
from collections import defaultdict
import pickle
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ThreatDefender:
    def __init__(self):
        self.setup_logging()
        self.blacklist = self.load_blacklist()
        self.whitelist = self.load_whitelist()
        self.suspicious_processes = []
        self.process_history = defaultdict(list)
        self.scan_results = []
        self.protection_active = True
        
    def setup_logging(self):
        """Configuration du système de logging"""
        log_dir = Path.home() / "ThreatDefender_Logs"
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            filename=log_dir / f"protection_{datetime.now().strftime('%Y%m%d')}.log",
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

class ProcessMonitor:
    """Surveillance avancée des processus"""
    
    def __init__(self, defender):
        self.defender = defender
        self.suspicious_keywords = [
            'miner', 'crypto', 'bitcoin', 'monero', 'keylog', 
            'ransom', 'trojan', 'backdoor', 'spy', 'rat',
            'password', 'hack', 'exploit', 'inject'
        ]
        self.known_threats_hashes = self.load_threat_hashes()
        
    def load_threat_hashes(self):
        """Charger les hashs de menaces connues"""
        threats = {}
        threat_file = Path.home() / ".threat_defender" / "threat_hashes.json"
        if threat_file.exists():
            with open(threat_file, 'r') as f:
                threats = json.load(f)
        return threats
    
    def get_process_hash(self, process):
        """Calculer le hash d'un processus"""
        try:
            with open(process.exe(), 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except:
            return None
    
    def monitor_processes(self):
        """Surveillance continue des processus"""
        while self.defender.protection_active:
            try:
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 
                                                'memory_percent', 'connections',
                                                'create_time', 'exe']):
                    try:
                        self.analyze_process(proc)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                time.sleep(2)
            except Exception as e:
                self.defender.logger.error(f"Erreur monitoring: {e}")
    
    def analyze_process(self, proc):
        """Analyse approfondie d'un processus"""
        threats_found = []
        
        # Vérification du hash
        proc_hash = self.get_process_hash(proc)
        if proc_hash in self.known_threats_hashes:
            threats_found.append("THREAT_HASH")
            self.terminate_process(proc.pid, "Hash de menace connu")
        
        # Vérification du nom suspect
        proc_name = proc.info['name'].lower() if proc.info['name'] else ""
        for keyword in self.suspicious_keywords:
            if keyword in proc_name:
                threats_found.append(f"SUSPICIOUS_NAME_{keyword}")
                self.flag_process(proc.pid, f"Nom suspect: {keyword}")
        
        # Vérification CPU/mémoire anormale
        if proc.info['cpu_percent'] > 50:
            threats_found.append("HIGH_CPU")
            self.flag_process(proc.pid, f"CPU élevé: {proc.info['cpu_percent']}%")
        
        if proc.info['memory_percent'] > 20:
            threats_found.append("HIGH_MEMORY")
            self.flag_process(proc.pid, f"Mémoire élevée: {proc.info['memory_percent']}%")
        
        # Vérification des connexions réseau
        try:
            connections = proc.connections()
            if connections:
                for conn in connections:
                    if conn.status == 'ESTABLISHED':
                        if self.is_suspicious_connection(conn.raddr.ip):
                            threats_found.append("SUSPICIOUS_NETWORK")
                            self.terminate_process(proc.pid, f"Connexion suspecte à {conn.raddr.ip}")
        except:
            pass
        
        return threats_found
    
    def is_suspicious_connection(self, ip):
        """Vérifier si une IP est suspecte"""
        suspicious_ips = [
            '185.', '94.', '45.', '46.', '31.', 
            '193.', '195.', '212.', '213.', '217.'
        ]
        for suspicious in suspicious_ips:
            if ip.startswith(suspicious):
                return True
        return False
    
    def terminate_process(self, pid, reason):
        """Terminer un processus malveillant"""
        try:
            process = psutil.Process(pid)
            process.terminate()
            self.defender.logger.warning(f"Processus {pid} terminé: {reason}")
            
            # Force kill si nécessaire
            time.sleep(1)
            if psutil.pid_exists(pid):
                process.kill()
                self.defender.logger.warning(f"Processus {pid} kill forcé: {reason}")
        except Exception as e:
            self.defender.logger.error(f"Erreur terminaison {pid}: {e}")
    
    def flag_process(self, pid, reason):
        """Marquer un processus suspect"""
        if pid not in self.defender.suspicious_processes:
            self.defender.suspicious_processes.append(pid)
            self.defender.logger.info(f"Processus suspect {pid}: {reason}")

class FileSystemGuard(FileSystemEventHandler):
    """Protection du système de fichiers"""
    
    def __init__(self, defender):
        self.defender = defender
        super().__init__()
        self.suspicious_extensions = [
            '.exe', '.vbs', '.bat', '.cmd', '.ps1', '.js', '.jar',
            '.scr', '.pif', '.cpl', '.hta', '.msi', '.docm', '.xlsm'
        ]
        self.ransomware_patterns = [
            '.encrypted', '.locked', '.crypt', '.ransom',
            '.zepto', '.cerber', '.locky'
        ]
        
    def on_created(self, event):
        """Détection de création de fichiers"""
        if not event.is_directory:
            self.scan_file(event.src_path)
    
    def on_modified(self, event):
        """Détection de modification de fichiers"""
        if not event.is_directory:
            if self.check_ransomware_pattern(event.src_path):
                self.quarantine_file(event.src_path)
    
    def scan_file(self, filepath):
        """Scanner un fichier"""
        filepath = Path(filepath)
        
        # Vérification extension
        if filepath.suffix.lower() in self.suspicious_extensions:
            self.analyze_executable(filepath)
        
        # Vérification signature
        if self.check_file_signature(filepath):
            self.quarantine_file(filepath)
    
    def analyze_executable(self, filepath):
        """Analyse d'un exécutable"""
        try:
            # Calcul hash
            with open(filepath, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            
            # Vérification base de données
            if file_hash in self.defender.blacklist:
                self.quarantine_file(filepath)
                self.defender.logger.warning(f"Fichier malveillant détecté: {filepath}")
        except Exception as e:
            self.defender.logger.error(f"Erreur analyse {filepath}: {e}")
    
    def quarantine_file(self, filepath):
        """Mettre en quarantaine un fichier"""
        try:
            quarantine_dir = Path.home() / "ThreatDefender_Quarantine"
            quarantine_dir.mkdir(exist_ok=True)
            
            new_path = quarantine_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filepath.name}"
            os.rename(filepath, new_path)
            
            self.defender.logger.warning(f"Fichier mis en quarantaine: {filepath} -> {new_path}")
        except Exception as e:
            self.defender.logger.error(f"Erreur quarantaine {filepath}: {e}")

class NetworkFirewall:
    """Protection réseau"""
    
    def __init__(self, defender):
        self.defender = defender
        self.blocked_ips = set()
        self.blocked_ports = {135, 137, 138, 139, 445, 3389, 22, 23, 80, 443}
        self.setup_windows_firewall()
    
    def setup_windows_firewall(self):
        """Configurer le pare-feu Windows"""
        if platform.system() == "Windows":
            for port in self.blocked_ports:
                try:
                    subprocess.run(
                        f'netsh advfirewall firewall add rule name="Block_Port_{port}" '
                        f'dir=in action=block protocol=TCP localport={port}',
                        shell=True, capture_output=True
                    )
                    self.defender.logger.info(f"Port {port} bloqué")
                except:
                    pass
    
    def monitor_network(self):
        """Surveillance réseau"""
        while self.defender.protection_active:
            try:
                connections = psutil.net_connections()
                for conn in connections:
                    if conn.status == 'ESTABLISHED':
                        self.check_connection(conn)
                time.sleep(5)
            except Exception as e:
                self.defender.logger.error(f"Erreur réseau: {e}")
    
    def check_connection(self, conn):
        """Vérifier une connexion"""
        if conn.raddr:
            ip = conn.raddr.ip
            port = conn.raddr.port
            
            if port in self.blocked_ports:
                self.block_connection(ip, port)
            
            if self.is_malicious_ip(ip):
                self.block_connection(ip, port)
    
    def block_connection(self, ip, port):
        """Bloquer une connexion"""
        if platform.system() == "Windows":
            try:
                subprocess.run(
                    f'netsh advfirewall firewall add rule name="Block_{ip}" '
                    f'dir=out action=block remoteip={ip}',
                    shell=True, capture_output=True
                )
                self.blocked_ips.add(ip)
                self.defender.logger.warning(f"IP bloquée: {ip}")
            except:
                pass

class StartupProtection:
    """Protection au démarrage"""
    
    def __init__(self, defender):
        self.defender = defender
        
    def scan_startup(self):
        """Scanner les programmes au démarrage"""
        if platform.system() == "Windows":
            self.scan_windows_startup()
    
    def scan_windows_startup(self):
        """Scanner démarrage Windows"""
        startup_paths = [
            Path(os.environ['APPDATA']) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup",
            Path("C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs\\Startup")
        ]
        
        # Registry keys
        registry_keys = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunOnce")
        ]
        
        # Scan registry
        for hkey, key in registry_keys:
            try:
                with winreg.OpenKey(hkey, key) as reg_key:
                    i = 0
                    while True:
                        try:
                            name, value, _ = winreg.EnumValue(reg_key, i)
                            self.analyze_registry_entry(name, value)
                            i += 1
                        except WindowsError:
                            break
            except:
                pass
    
    def analyze_registry_entry(self, name, value):
        """Analyser une entrée de registre"""
        suspicious_keywords = ['update', 'helper', 'svc', 'service', 'crypto', 'miner']
        
        for keyword in suspicious_keywords:
            if keyword in name.lower() or keyword in value.lower():
                self.defender.logger.warning(f"Entrée démarrage suspecte: {name} -> {value}")

class PerformanceOptimizer:
    """Optimisation des performances"""
    
    def __init__(self, defender):
        self.defender = defender
        
    def clean_temp_files(self):
        """Nettoyer les fichiers temporaires"""
        temp_paths = [
            Path(os.environ.get('TEMP', '')),
            Path(os.environ.get('TMP', '')),
            Path("C:\\Windows\\Temp"),
            Path.home() / "AppData" / "Local" / "Temp"
        ]
        
        for temp_path in temp_paths:
            if temp_path.exists():
                self.clean_directory(temp_path)
    
    def clean_directory(self, directory, days_old=7):
        """Nettoyer un répertoire"""
        cutoff_time = time.time() - (days_old * 86400)
        
        for item in directory.glob('*'):
            try:
                if item.is_file():
                    if item.stat().st_mtime < cutoff_time:
                        item.unlink()
                        self.defender.logger.info(f"Fichier supprimé: {item}")
            except:
                pass
    
    def optimize_memory(self):
        """Optimiser la mémoire"""
        if platform.system() == "Windows":
            try:
                kernel32 = ctypes.windll.kernel32
                kernel32.SetProcessWorkingSetSize(-1, -1, -1)
            except:
                pass

class ThreatDefenderComplete:
    """Système de protection complet"""
    
    def __init__(self):
        self.defender = ThreatDefender()
        self.process_monitor = ProcessMonitor(self.defender)
        self.file_guard = FileSystemGuard(self.defender)
        self.network_firewall = NetworkFirewall(self.defender)
        self.startup_protection = StartupProtection(self.defender)
        self.performance_optimizer = PerformanceOptimizer(self.defender)
        
        self.observer = Observer()
        self.running = False
        
    def start(self):
        """Démarrer tous les services de protection"""
        self.running = True
        
        print("🚀 Démarrage du système de protection PC...")
        self.defender.logger.info("Système de protection démarré")
        
        # Surveillance processus
        process_thread = threading.Thread(
            target=self.process_monitor.monitor_processes,
            daemon=True
        )
        process_thread.start()
        
        # Surveillance fichiers
        self.observer.schedule(
            self.file_guard,
            str(Path.home()),
            recursive=True
        )
        self.observer.start()
        
        # Surveillance réseau
        network_thread = threading.Thread(
            target=self.network_firewall.monitor_network,
            daemon=True
        )
        network_thread.start()
        
        # Scan démarrage
        self.startup_protection.scan_startup()
        
        # Optimisation périodique
        self.schedule_maintenance()
        
        print("✅ Protection active!")
        print("📁 Logs: ~/ThreatDefender_Logs/")
        print("🛡️ Quarantaine: ~/ThreatDefender_Quarantine/")
        
        self.menu_interface()
    
    def schedule_maintenance(self):
        """Planifier la maintenance"""
        def maintenance_job():
            while self.running:
                time.sleep(3600)  # Toutes les heures
                self.performance_optimizer.clean_temp_files()
                self.performance_optimizer.optimize_memory()
        
        maintenance_thread = threading.Thread(
            target=maintenance_job,
            daemon=True
        )
        maintenance_thread.start()
    
    def menu_interface(self):
        """Interface utilisateur"""
        while self.running:
            print("\n" + "="*50)
            print("🛡️  THREAT DEFENDER - Protection Active")
            print("="*50)
            print("1. Scanner les processus actifs")
            print("2. Afficher les menaces détectées")
            print("3. Nettoyage système")
            print("4. Liste blanche/Liste noire")
            print("5. Configurer la protection")
            print("6. Quitter")
            print("="*50)
            
            choice = input("\nChoix: ")
            
            if choice == "1":
                self.scan_all()
            elif choice == "2":
                self.show_threats()
            elif choice == "3":
                self.clean_system()
            elif choice == "4":
                self.manage_lists()
            elif choice == "5":
                self.configure_protection()
            elif choice == "6":
                self.stop()
                break
    
    def scan_all(self):
        """Scan complet du système"""
        print("\n🔍 Scan système en cours...")
        
        # Scan processus
        print("Scan des processus...")
        for proc in psutil.process_iter():
            self.process_monitor.analyze_process(proc)
        
        # Scan fichiers sensibles
        print("Scan des dossiers système...")
        sensitive_dirs = [
            Path(os.environ.get('TEMP', '')),
            Path.home() / "Downloads",
            Path.home() / "Desktop"
        ]
        
        for directory in sensitive_dirs:
            if directory.exists():
                for file in directory.glob('*'):
                    self.file_guard.scan_file(str(file))
        
        print("✅ Scan terminé!")
    
    def show_threats(self):
        """Afficher les menaces détectées"""
        print("\n📋 Menaces détectées:")
        with open(self.defender.logger.handlers[0].baseFilename, 'r') as f:
            logs = f.readlines()
            threats = [log for log in logs if 'WARNING' in log]
            
            if threats:
                for threat in threats[-10:]:
                    print(threat.strip())
            else:
                print("Aucune menace détectée")
    
    def clean_system(self):
        """Nettoyer le système"""
        print("\n🧹 Nettoyage système...")
        self.performance_optimizer.clean_temp_files()
        self.performance_optimizer.optimize_memory()
        print("✅ Nettoyage terminé!")
    
    def manage_lists(self):
        """Gérer listes blanche/noire"""
        print("\n📋 Gestion des listes")
        print("1. Ajouter à la liste blanche")
        print("2. Ajouter à la liste noire")
        print("3. Afficher les listes")
        
        subchoice = input("Choix: ")
        # Implémentation gestion listes...
    
    def configure_protection(self):
        """Configurer la protection"""
        print("\n⚙️ Configuration")
        print("1. Activer/Désactiver surveillance réseau")
        print("2. Activer/Désactiver surveillance fichiers")
        print("3. Activer/Désactiver optimisation auto")
        # Implémentation configuration...
    
    def stop(self):
        """Arrêter la protection"""
        self.running = False
        self.defender.protection_active = False
        self.observer.stop()
        self.observer.join()
        print("\n👋 Protection arrêtée")
        self.defender.logger.info("Système de protection arrêté")

def install_requirements():
    """Installer les dépendances nécessaires"""
    requirements = [
        'psutil',
        'watchdog',
        'requests'
    ]
    
    for req in requirements:
        try:
            __import__(req)
        except ImportError:
            print(f"Installation de {req}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", req])

if __name__ == "__main__":
    print("🛡️  THREAT DEFENDER - Installation et Démarrage")
    
    # Installation des dépendances
    install_requirements()
    
    # Vérification des droits administrateur
    if platform.system() == "Windows":
        if ctypes.windll.shell32.IsUserAnAdmin():
            print("✅ Droits administrateur OK")
        else:
            print("⚠️  Certaines fonctionnalités nécessitent les droits admin")
    
    # Démarrage de la protection
    protector = ThreatDefenderComplete()
    
    try:
        protector.start()
    except KeyboardInterrupt:
        protector.stop()