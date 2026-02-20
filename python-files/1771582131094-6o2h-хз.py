#!/usr/bin/env python3
"""
Multi-function Antivirus (Educational Project)
-----------------------------------------------
Features:
- Signature scanning (hash + string patterns)
- Heuristic analysis
- Real-time folder monitoring
- Quarantine manager
- Central logging
- Signature updates (simulated)

Dependencies: pip install watchdog
"""

import os
import sys
import hashlib
import json
import shutil
import logging
import time
import requests
from pathlib import Path
from datetime import datetime
from threading import Thread
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# ==================== CONFIGURATION ====================
SIGNATURE_FILE = "signatures.json"          # Local signature database
QUARANTINE_DIR = "quarantine"                # Folder for suspicious files
LOG_FILE = "antivirus.log"                    # Activity log
SCAN_DIRS = ["C:\\Users\\Public", "C:\\Temp"] if os.name == 'nt' else ["/tmp", os.path.expanduser("~")]
SUSPICIOUS_EXTENSIONS = [".exe", ".scr", ".bat", ".vbs", ".ps1", ".js", ".jar"]
HEURISTIC_PATTERNS = ["eval(", "base64_decode", "CreateObject", "WScript.Shell", "PowerShell -Enc"]
UPDATE_URL = "https://example.com/signatures.json"   # Replace with real URL

# ==================== LOGGING SETUP ====================
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(message)s")
console.setFormatter(formatter)
logging.getLogger().addHandler(console)

# ==================== SIGNATURE DATABASE ====================
class SignatureDB:
    """Manages the signature database (hashes and string patterns)."""
    def __init__(self, sig_file):
        self.sig_file = sig_file
        self.hashes = set()          # SHA-256 hashes of known malware
        self.patterns = []            # String patterns for simple heuristic

    def load(self):
        """Load signatures from JSON file."""
        if os.path.exists(self.sig_file):
            try:
                with open(self.sig_file, 'r') as f:
                    data = json.load(f)
                self.hashes = set(data.get("hashes", []))
                self.patterns = data.get("patterns", [])
                logging.info(f"Loaded {len(self.hashes)} hash signatures and {len(self.patterns)} patterns.")
            except Exception as e:
                logging.error(f"Failed to load signatures: {e}")

    def save(self):
        """Save signatures to JSON file."""
        data = {"hashes": list(self.hashes), "patterns": self.patterns}
        with open(self.sig_file, 'w') as f:
            json.dump(data, f, indent=4)
        logging.info("Signatures saved.")

    def add_signature(self, file_path, patterns=None):
        """Add a file's hash to the database, optionally add patterns."""
        file_hash = compute_file_hash(file_path)
        if file_hash:
            self.hashes.add(file_hash)
            logging.info(f"Added hash {file_hash} from {file_path}")
        if patterns:
            self.patterns.extend(patterns)
        self.save()

    def update_from_server(self):
        """Download latest signatures from a remote server (simulated)."""
        try:
            # Simulate download - replace with real requests.get() in production
            # response = requests.get(UPDATE_URL)
            # data = response.json()
            # self.hashes = set(data.get("hashes", []))
            # self.patterns = data.get("patterns", [])
            logging.info("Signature update simulated (no real download).")
            self.save()
        except Exception as e:
            logging.error(f"Update failed: {e}")

# ==================== UTILITY FUNCTIONS ====================
def compute_file_hash(file_path, algorithm="sha256"):
    """Compute hash of a file."""
    hash_obj = hashlib.new(algorithm)
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except Exception as e:
        logging.debug(f"Hash failed for {file_path}: {e}")
        return None

def is_suspicious_extension(file_path):
    """Check if file has a suspicious extension."""
    ext = os.path.splitext(file_path)[1].lower()
    return ext in SUSPICIOUS_EXTENSIONS

def heuristic_scan(file_path):
    """Scan file content for suspicious patterns (simple heuristic)."""
    try:
        with open(file_path, 'r', errors='ignore') as f:
            content = f.read()
        for pattern in HEURISTIC_PATTERNS:
            if pattern in content:
                return True, pattern
    except Exception:
        pass
    return False, None

def scan_file(file_path, sig_db):
    """Perform all scans on a single file. Return (is_malicious, reason)."""
    # 1. Hash check
    file_hash = compute_file_hash(file_path)
    if file_hash and file_hash in sig_db.hashes:
        return True, f"Hash match: {file_hash}"

    # 2. Heuristic: suspicious extension
    if is_suspicious_extension(file_path):
        return True, "Suspicious extension"

    # 3. Heuristic: content patterns
    found, pattern = heuristic_scan(file_path)
    if found:
        return True, f"Heuristic pattern: {pattern}"

    return False, "Clean"

# ==================== QUARANTINE HANDLER ====================
class Quarantine:
    """Move suspicious files to quarantine and restore them if needed."""
    def __init__(self, quarantine_dir):
        self.quarantine_dir = quarantine_dir
        os.makedirs(quarantine_dir, exist_ok=True)

    def quarantine_file(self, file_path, reason=""):
        """Move file to quarantine folder with metadata."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = os.path.basename(file_path)
            dest_name = f"{timestamp}_{base_name}"
            dest_path = os.path.join(self.quarantine_dir, dest_name)

            shutil.move(file_path, dest_path)
            # Save metadata
            meta = {
                "original_path": file_path,
                "reason": reason,
                "timestamp": timestamp
            }
            meta_path = dest_path + ".meta"
            with open(meta_path, 'w') as f:
                json.dump(meta, f)

            logging.info(f"Quarantined {file_path} -> {dest_path} ({reason})")
        except Exception as e:
            logging.error(f"Quarantine failed for {file_path}: {e}")

    def restore_file(self, quarantined_path):
        """Restore file from quarantine to its original location."""
        try:
            meta_path = quarantined_path + ".meta"
            with open(meta_path, 'r') as f:
                meta = json.load(f)
            original = meta["original_path"]
            shutil.move(quarantined_path, original)
            os.remove(meta_path)
            logging.info(f"Restored {quarantined_path} to {original}")
        except Exception as e:
            logging.error(f"Restore failed: {e}")

    def list_quarantine(self):
        """List all files currently in quarantine."""
        files = []
        for item in os.listdir(self.quarantine_dir):
            if item.endswith(".meta"):
                continue
            full = os.path.join(self.quarantine_dir, item)
            meta_file = full + ".meta"
            if os.path.exists(meta_file):
                with open(meta_file, 'r') as f:
                    meta = json.load(f)
                files.append((full, meta))
        return files

# ==================== SCANNER ENGINE ====================
class Scanner:
    """Handles on-demand scanning of files/directories."""
    def __init__(self, sig_db, quarantine):
        self.sig_db = sig_db
        self.quarantine = quarantine

    def scan_file(self, file_path, auto_quarantine=True):
        """Scan a single file and optionally quarantine if malicious."""
        malicious, reason = scan_file(file_path, self.sig_db)
        if malicious:
            logging.warning(f"MALICIOUS: {file_path} - {reason}")
            if auto_quarantine:
                self.quarantine.quarantine_file(file_path, reason)
        else:
            logging.info(f"CLEAN: {file_path}")
        return malicious

    def scan_directory(self, directory, auto_quarantine=True):
        """Recursively scan a directory."""
        count = 0
        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                if self.scan_file(file_path, auto_quarantine):
                    count += 1
        logging.info(f"Directory scan finished. Found {count} malicious files.")
        return count

# ==================== REAL-TIME MONITOR ====================
class MonitorHandler(FileSystemEventHandler):
    """Handles file system events for real-time protection."""
    def __init__(self, scanner):
        self.scanner = scanner

    def on_created(self, event):
        if not event.is_directory:
            self.scanner.scan_file(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self.scanner.scan_file(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self.scanner.scan_file(event.dest_path)

class RealTimeMonitor:
    """Runs a background thread that watches directories."""
    def __init__(self, scanner, paths_to_watch):
        self.scanner = scanner
        self.paths = paths_to_watch
        self.observer = Observer()

    def start(self):
        for path in self.paths:
            if os.path.exists(path):
                self.observer.schedule(MonitorHandler(self.scanner), path, recursive=True)
                logging.info(f"Watching: {path}")
        self.observer.start()

    def stop(self):
        self.observer.stop()
        self.observer.join()

# ==================== MAIN APPLICATION ====================
class AntiVirusApp:
    def __init__(self):
        self.sig_db = SignatureDB(SIGNATURE_FILE)
        self.sig_db.load()
        self.quarantine = Quarantine(QUARANTINE_DIR)
        self.scanner = Scanner(self.sig_db, self.quarantine)
        self.monitor = None

    def update_signatures(self):
        """Download and update signature database."""
        logging.info("Updating signatures...")
        self.sig_db.update_from_server()
        self.sig_db.load()  # reload after update

    def full_scan(self):
        """Scan all configured directories."""
        logging.info("Starting full system scan...")
        total = 0
        for d in SCAN_DIRS:
            if os.path.exists(d):
                total += self.scanner.scan_directory(d)
        logging.info(f"Full scan completed. Total threats: {total}")

    def quick_scan(self, path):
        """Scan a specific path."""
        if os.path.isfile(path):
            self.scanner.scan_file(path)
        elif os.path.isdir(path):
            self.scanner.scan_directory(path)
        else:
            logging.error(f"Path not found: {path}")

    def start_realtime(self):
        """Start real-time protection in a background thread."""
        self.monitor = RealTimeMonitor(self.scanner, SCAN_DIRS)
        self.monitor.start()

    def stop_realtime(self):
        if self.monitor:
            self.monitor.stop()
            self.monitor = None

    def show_quarantine(self):
        """List quarantined items."""
        files = self.quarantine.list_quarantine()
        if not files:
            print("Quarantine is empty.")
        else:
            for path, meta in files:
                print(f"{path} -> original: {meta['original_path']} reason: {meta['reason']}")

    def restore_from_quarantine(self, quarantined_path):
        self.quarantine.restore_file(quarantined_path)

    def add_sample_to_db(self, file_path):
        """Add a malicious sample to the signature DB."""
        self.sig_db.add_signature(file_path)

    def menu(self):
        """Simple CLI menu."""
        while True:
            print("\n=== Multi-Function Antivirus ===")
            print("1. Update signatures")
            print("2. Full system scan")
            print("3. Quick scan (file/folder)")
            print("4. Start real-time monitoring")
            print("5. Stop real-time monitoring")
            print("6. List quarantine")
            print("7. Restore from quarantine")
            print("8. Add sample to database")
            print("9. Exit")
            choice = input("Select option: ").strip()

            if choice == '1':
                self.update_signatures()
            elif choice == '2':
                self.full_scan()
            elif choice == '3':
                path = input("Enter path: ").strip()
                self.quick_scan(path)
            elif choice == '4':
                self.start_realtime()
                print("Real-time monitoring started in background.")
            elif choice == '5':
                self.stop_realtime()
                print("Real-time monitoring stopped.")
            elif choice == '6':
                self.show_quarantine()
            elif choice == '7':
                path = input("Enter full path of quarantined file: ").strip()
                self.restore_from_quarantine(path)
            elif choice == '8':
                path = input("Enter path of malicious sample: ").strip()
                self.add_sample_to_db(path)
            elif choice == '9':
                self.stop_realtime()
                print("Goodbye!")
                break

if __name__ == "__main__":
    # Check admin rights (optional)
    if os.name == 'nt':
        import ctypes
        if not ctypes.windll.shell32.IsUserAnAdmin():
            print("Warning: Some features may require administrator privileges.")
    else:
        if os.geteuid() != 0:
            print("Warning: Running without root may limit some features.")

    app = AntiVirusApp()
    app.menu()