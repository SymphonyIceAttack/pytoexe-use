#!/usr/bin/env python3
"""
Educational Ransomware Simulator - DECRYPTOR + KILLER
For Cybersecurity Education Only
- Kills all running ghost processes
- Removes persistence
- Decrypts ALL .ben files
"""

import os
import sys
import time
import json
import base64
import struct
import signal
import getpass
import threading
from pathlib import Path

# ==================== CRYPTO IMPORTS ====================

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import hashes, padding
    from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.backends import default_backend
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("❌ Cryptography library not found!")
    print("Install with: pip install cryptography")
    sys.exit(1)

# ==================== WINDOWS IMPORTS ====================

if os.name == 'nt':
    try:
        import winreg
        import win32api
        import win32con
        import win32process
        import win32security
        import win32gui
        import win32event
        import psutil
        WIN_IMPORTS = True
    except ImportError:
        WIN_IMPORTS = False
        print("⚠️  Some Windows features may be limited")
        print("Install with: pip install pywin32 psutil")
else:
    import psutil
    WIN_IMPORTS = False


# ==================== EMBEDDED ENCRYPTED PRIVATE KEY ====================

ENCRYPTED_PRIVATE_KEY = """-----BEGIN ENCRYPTED PRIVATE KEY-----
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
-----END ENCRYPTED PRIVATE KEY-----"""


# ==================== CONFIGURATION ====================

class Config:
    ENC_EXTENSION = ".ben"
    GHOST_NAMES = ["svchost.exe", "WindowsUpdateService.exe", "MicrosoftEdgeUpdate.exe", "AdobeFlashPlayerUpdate.exe"]
    STATE_FILE = os.path.join(os.environ.get('TEMP', '.'), '.ghost_state.dat')
    MAX_ATTEMPTS = 3


# ==================== PROCESS KILLER ====================

class ProcessKiller:
    """Kills all running ghost processes"""
    
    @staticmethod
    def kill_all():
        """Kill ALL ghost processes"""
        killed = 0
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline']):
                try:
                    # Check by name
                    if proc.info['name'] and any(ghost in proc.info['name'].lower() for ghost in Config.GHOST_NAMES):
                        proc.kill()
                        killed += 1
                        print(f"  ✓ Killed: {proc.info['name']} (PID: {proc.info['pid']})")
                    
                    # Check by command line
                    elif proc.info['cmdline']:
                        cmd = ' '.join(proc.info['cmdline']).lower()
                        if 'encrypt' in cmd or 'ghost' in cmd or 'svchost' in cmd:
                            proc.kill()
                            killed += 1
                            print(f"  ✓ Killed: {proc.info['name']} (PID: {proc.info['pid']})")
                            
                except:
                    pass
        except:
            pass
        
        return killed


# ==================== PERSISTENCE REMOVER ====================

class PersistenceRemover:
    """Removes all persistence mechanisms"""
    
    @staticmethod
    def remove_all():
        """Remove ALL persistence"""
        removed = []
        
        # Windows registry
        if os.name == 'nt':
            try:
                import winreg
                
                reg_paths = [
                    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
                    (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
                ]
                
                for hive, path in reg_paths:
                    try:
                        key = winreg.OpenKey(hive, path, 0, winreg.KEY_SET_VALUE | winreg.KEY_READ)
                        
                        # Get all values
                        i = 0
                        while True:
                            try:
                                name, value, _ = winreg.EnumValue(key, i)
                                if any(ghost in name.lower() for ghost in ['update', 'edge', 'flash', 'svchost']):
                                    winreg.DeleteValue(key, name)
                                    removed.append(name)
                                    print(f"  ✓ Removed registry: {name}")
                                i += 1
                            except WindowsError:
                                break
                        
                        winreg.CloseKey(key)
                    except:
                        pass
            except:
                pass
            
            # Remove from startup folder
            try:
                startup = os.path.join(os.environ['APPDATA'], r'Microsoft\Windows\Start Menu\Programs\Startup')
                if os.path.exists(startup):
                    for file in os.listdir(startup):
                        if file.endswith('.bat') or file.endswith('.exe'):
                            if any(ghost in file.lower() for ghost in ['update', 'edge', 'flash']):
                                os.remove(os.path.join(startup, file))
                                removed.append(file)
                                print(f"  ✓ Removed startup: {file}")
            except:
                pass
        
        # Linux autostart
        else:
            try:
                autostart = os.path.join(os.path.expanduser('~'), '.config', 'autostart')
                if os.path.exists(autostart):
                    for file in os.listdir(autostart):
                        if 'update' in file.lower() or 'ghost' in file.lower():
                            os.remove(os.path.join(autostart, file))
                            removed.append(file)
                            print(f"  ✓ Removed autostart: {file}")
            except:
                pass
        
        return removed


# ==================== DECRYPTOR ====================

class Decryptor:
    """Handles file decryption"""
    
    def __init__(self, password):
        self.backend = default_backend()
        self.password = password
        self.private_key = None
        self.decrypted = 0
        self.failed = 0
        
        # Load private key
        self._load_private_key()
    
    def _load_private_key(self):
        """Load and decrypt private key with password"""
        try:
            self.private_key = serialization.load_pem_private_key(
                ENCRYPTED_PRIVATE_KEY.encode(),
                password=self.password.encode(),
                backend=self.backend
            )
            print("✅ Private key unlocked successfully!")
        except Exception as e:
            raise Exception("Wrong password or corrupted key")
    
    def decrypt_keys(self, encrypted_keys):
        """Decrypt session keys with private key"""
        try:
            combined = self.private_key.decrypt(
                encrypted_keys,
                asym_padding.OAEP(
                    mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            aes_key = combined[:32]
            chacha_key = combined[32:]
            return aes_key, chacha_key
        except:
            return None, None
    
    def decrypt_aes(self, data, key):
        """AES-256-CBC decryption"""
        iv = data[:16]
        ciphertext = data[16:]
        
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=self.backend)
        decryptor = cipher.decryptor()
        
        padded = decryptor.update(ciphertext) + decryptor.finalize()
        
        unpadder = padding.PKCS7(128).unpadder()
        return unpadder.update(padded) + unpadder.finalize()
    
    def decrypt_chacha(self, data, key):
        """ChaCha20 decryption"""
        nonce = data[:16]
        ciphertext = data[16:]
        
        algorithm = algorithms.ChaCha20(key, nonce)
        cipher = Cipher(algorithm, mode=None, backend=self.backend)
        decryptor = cipher.decryptor()
        
        return decryptor.update(ciphertext) + decryptor.finalize()
    
    def decrypt_file(self, filepath):
        """Decrypt a single .ben file"""
        try:
            with open(filepath, 'rb') as f:
                data = f.read()
            
            # Check header
            if len(data) < 9 or data[:5] != b'BENCF':
                return False
            
            # Extract components
            key_len = struct.unpack('<I', data[5:9])[0]
            
            if len(data) < 9 + key_len:
                return False
            
            encrypted_keys = data[9:9+key_len]
            encrypted_data = data[9+key_len:]
            
            # Decrypt session keys
            aes_key, chacha_key = self.decrypt_keys(encrypted_keys)
            if not aes_key or not chacha_key:
                return False
            
            # Decrypt data
            chacha_dec = self.decrypt_chacha(encrypted_data, chacha_key)
            final_data = self.decrypt_aes(chacha_dec, aes_key)
            
            # Restore original
            original_path = filepath[:-len(Config.ENC_EXTENSION)]
            with open(original_path, 'wb') as f:
                f.write(final_data)
            
            # Remove encrypted file
            os.remove(filepath)
            
            self.decrypted += 1
            return True
            
        except Exception as e:
            self.failed += 1
            return False


# ==================== FILE FINDER ====================

def find_all_ben_files():
    """Find ALL .ben files on ALL drives"""
    ben_files = []
    drives = []
    
    # Get all drives
    if os.name == 'nt':
        for letter in 'CDEFGHIJKLMNOPQRSTUVWXYZ':
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                drives.append(drive)
    else:
        drives = ['/']
    
    print("\n🔍 Scanning all drives for encrypted files...")
    
    for drive in drives:
        try:
            for root, dirs, files in os.walk(drive):
                for file in files:
                    if file.endswith(Config.ENC_EXTENSION):
                        ben_files.append(os.path.join(root, file))
        except:
            continue
    
    return ben_files


# ==================== CLEANUP ====================

def cleanup_state_files():
    """Remove all ghost state files"""
    removed = 0
    
    # Temp directory state files
    temp_dir = os.environ.get('TEMP', '.')
    for file in os.listdir(temp_dir):
        if file.startswith('.ghost_') or 'state' in file.lower():
            try:
                os.remove(os.path.join(temp_dir, file))
                removed += 1
            except:
                pass
    
    # Current directory
    for file in os.listdir('.'):
        if file.startswith('.ghost_') or file.endswith('.state'):
            try:
                os.remove(file)
                removed += 1
            except:
                pass
    
    return removed


# ==================== MAIN ====================

def main():
    """Main decryptor function"""
    
    print("\n" + "="*70)
    print("🔓 GHOST DECRYPTOR + KILLER")
    print("="*70)
    print("\nThis tool will:")
    print("  1. KILL all running ghost processes")
    print("  2. REMOVE all persistence")
    print("  3. DECRYPT all .ben files")
    print("  4. CLEAN UP state files")
    print("="*70)
    
    # Check dependencies
    if not CRYPTO_AVAILABLE:
        print("\n❌ Cryptography library not found!")
        sys.exit(1)
    
    # STEP 1: KILL PROCESSES
    print("\n🔪 STEP 1: Killing ghost processes...")
    killed = ProcessKiller.kill_all()
    print(f"  ✅ Killed {killed} processes")
    
    # STEP 2: REMOVE PERSISTENCE
    print("\n🗑️  STEP 2: Removing persistence...")
    removed = PersistenceRemover.remove_all()
    print(f"  ✅ Removed {len(removed)} persistence entries")
    
    # STEP 3: FIND ENCRYPTED FILES
    print("\n🔍 STEP 3: Finding encrypted files...")
    ben_files = find_all_ben_files()
    
    if not ben_files:
        print("  ❌ No .ben files found!")
    else:
        print(f"  ✅ Found {len(ben_files)} encrypted files")
        
        # Show sample
        if len(ben_files) > 5:
            print("\n  Sample files:")
            for f in ben_files[:5]:
                print(f"    • {os.path.basename(f)}")
            print(f"    • ... and {len(ben_files)-5} more")
    
    # STEP 4: GET PASSWORD
    print("\n🔑 STEP 4: Unlock private key")
    attempts = 0
    decryptor = None
    
    while attempts < Config.MAX_ATTEMPTS:
        if attempts > 0:
            print(f"\n⚠️  Attempt {attempts+1}/{Config.MAX_ATTEMPTS}")
        
        password = getpass.getpass("  Enter private key password: ")
        
        try:
            decryptor = Decryptor(password)
            break
        except:
            attempts += 1
            if attempts < Config.MAX_ATTEMPTS:
                print("  ❌ Wrong password. Try again.")
    
    if not decryptor:
        print("\n❌ Too many failed attempts. Exiting.")
        sys.exit(1)
    
    # STEP 5: DECRYPT FILES
    if ben_files:
        print("\n🔓 STEP 5: Decrypting files...")
        print("-" * 50)
        
        for i, filepath in enumerate(ben_files, 1):
            print(f"  [{i}/{len(ben_files)}] {os.path.basename(filepath)}")
            decryptor.decrypt_file(filepath)
            time.sleep(0.01)  # Small delay for visual
        
        print("-" * 50)
        print(f"\n✅ Successfully decrypted: {decryptor.decrypted}")
        print(f"❌ Failed: {decryptor.failed}")
    
    # STEP 6: CLEANUP
    print("\n🧹 STEP 6: Cleaning up state files...")
    cleaned = cleanup_state_files()
    print(f"  ✅ Removed {cleaned} state files")
    
    # FINAL
    print("\n" + "="*70)
    print("🎉 DECRYPTION COMPLETE!")
    print("="*70)
    print("\n✅ Ghost processes killed")
    print("✅ Persistence removed")
    print(f"✅ {decryptor.decrypted if decryptor else 0} files restored")
    print("✅ System cleaned")
    print("\n" + "="*70)
    
    input("\nPress Enter to exit...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Decryption cancelled")
        input("Press Enter to exit...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        input("Press Enter to exit...")
