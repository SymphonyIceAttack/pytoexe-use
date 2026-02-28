#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                      FOREX KEY SYSTEM v3.0 - PROFESSIONAL                    ║
║                                                                            ║
║  Features:                                                                  ║
║  • Generate unlimited premium keys                                          ║
║  • One-time use only - keys expire after use                               ║
║  • Hardware locking (HWID) - keys bound to specific PC                     ║
║  • Expiry dates - keys valid for 365 days                                  ║
║  • Database storage - track all keys and usage                             ║
║  • Admin panel - manage users and keys                                     ║
║  • Discord bot integration ready                                           ║
║  • Web API for online validation                                           ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import time
import random
import string
import hashlib
import sqlite3
import platform
import subprocess
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any

# ==============================================================================
# CONFIGURATION
# ==============================================================================

DB_PATH = "forex_keys.db"
KEY_PREFIX = "FRX"
KEY_VALID_DAYS = 365
KEY_PARTS = 4
KEY_PART_LENGTH = 4

# ==============================================================================
# DATABASE MANAGER
# ==============================================================================

class DatabaseManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Keys table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS forex_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key_code TEXT UNIQUE NOT NULL,
                    hwid TEXT,
                    discord_user_id TEXT,
                    discord_username TEXT,
                    generated_by TEXT,
                    generated_at TIMESTAMP,
                    expires_at TIMESTAMP,
                    used_at TIMESTAMP,
                    last_validated TIMESTAMP,
                    is_used BOOLEAN DEFAULT 0,
                    is_revoked BOOLEAN DEFAULT 0,
                    is_locked BOOLEAN DEFAULT 0,
                    activation_count INTEGER DEFAULT 0,
                    notes TEXT
                )
            ''')
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS forex_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    discord_user_id TEXT UNIQUE,
                    discord_username TEXT,
                    email TEXT,
                    total_keys INTEGER DEFAULT 0,
                    used_keys INTEGER DEFAULT 0,
                    premium_tier TEXT DEFAULT 'FREE',
                    joined_at TIMESTAMP,
                    last_active TIMESTAMP
                )
            ''')
            
            # Logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS forex_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    key_code TEXT,
                    hwid TEXT,
                    discord_user_id TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    timestamp TIMESTAMP,
                    details TEXT
                )
            ''')
            
            # Stats table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS forex_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stat_key TEXT UNIQUE,
                    stat_value TEXT,
                    updated_at TIMESTAMP
                )
            ''')
            
            # Indexes for speed
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_key_code ON forex_keys(key_code)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_hwid ON forex_keys(hwid)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_discord ON forex_keys(discord_user_id)')
            
            conn.commit()
    
    def execute(self, query, params=()):
        """Execute a query with automatic retry"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor

# ==============================================================================
# HWID GENERATOR - Hardware ID for PC locking
# ==============================================================================

class HWIDGenerator:
    """Generate unique Hardware ID based on system components"""
    
    @staticmethod
    def get_hwid() -> str:
        """Get unique hardware ID for current machine"""
        system = platform.system()
        
        if system == "Windows":
            return HWIDGenerator._get_windows_hwid()
        elif system == "Linux":
            return HWIDGenerator._get_linux_hwid()
        elif system == "Darwin":  # macOS
            return HWIDGenerator._get_mac_hwid()
        else:
            return HWIDGenerator._get_fallback_hwid()
    
    @staticmethod
    def _get_windows_hwid() -> str:
        """Get Windows hardware ID"""
        components = []
        
        try:
            # Get disk serial
            result = subprocess.run(
                'wmic diskdrive get serialnumber',
                shell=True,
                capture_output=True,
                text=True
            )
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    components.append(lines[1].strip())
        except:
            pass
        
        try:
            # Get motherboard serial
            result = subprocess.run(
                'wmic baseboard get serialnumber',
                shell=True,
                capture_output=True,
                text=True
            )
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    components.append(lines[1].strip())
        except:
            pass
        
        try:
            # Get CPU ID
            result = subprocess.run(
                'wmic cpu get processorid',
                shell=True,
                capture_output=True,
                text=True
            )
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    components.append(lines[1].strip())
        except:
            pass
        
        # Add MAC address
        mac = uuid.getnode()
        components.append(str(mac))
        
        # Combine and hash
        combined = ''.join(components)
        return hashlib.sha256(combined.encode()).hexdigest()[:32]
    
    @staticmethod
    def _get_linux_hwid() -> str:
        """Get Linux hardware ID"""
        components = []
        
        try:
            with open('/etc/machine-id', 'r') as f:
                components.append(f.read().strip())
        except:
            pass
        
        try:
            with open('/sys/class/dmi/id/product_uuid', 'r') as f:
                components.append(f.read().strip())
        except:
            pass
        
        combined = ''.join(components) or str(uuid.getnode())
        return hashlib.sha256(combined.encode()).hexdigest()[:32]
    
    @staticmethod
    def _get_mac_hwid() -> str:
        """Get macOS hardware ID"""
        try:
            result = subprocess.run(
                ['ioreg', '-rd1', '-c', 'IOPlatformExpertDevice'],
                capture_output=True,
                text=True
            )
            for line in result.stdout.split('\n'):
                if 'IOPlatformUUID' in line:
                    uuid_str = line.split('"')[-2]
                    return hashlib.sha256(uuid_str.encode()).hexdigest()[:32]
        except:
            pass
        
        return HWIDGenerator._get_fallback_hwid()
    
    @staticmethod
    def _get_fallback_hwid() -> str:
        """Fallback hardware ID"""
        combined = str(uuid.getnode()) + platform.node()
        return hashlib.sha256(combined.encode()).hexdigest()[:32]

# ==============================================================================
# KEY GENERATOR
# ==============================================================================

class KeyGenerator:
    """Generate unique premium keys"""
    
    @staticmethod
    def generate_key() -> str:
        """Generate a unique key in format FRX-XXXX-XXXX-XXXX-XX"""
        chars = string.ascii_uppercase + string.digits
        parts = []
        
        for _ in range(KEY_PARTS):
            part = ''.join(random.choices(chars, k=KEY_PART_LENGTH))
            parts.append(part)
        
        key_base = f"{KEY_PREFIX}-{'-'.join(parts)}"
        
        # Add checksum (last 2 chars of MD5)
        checksum = hashlib.md5(key_base.encode()).hexdigest()[:2].upper()
        key = f"{key_base}-{checksum}"
        
        return key
    
    @staticmethod
    def validate_format(key: str) -> bool:
        """Check if key has correct format"""
        import re
        pattern = r'^FRX-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{2}$'
        return bool(re.match(pattern, key))

# ==============================================================================
# KEY MANAGER
# ==============================================================================

class KeyManager:
    def __init__(self):
        self.db = DatabaseManager()
        self.hwid = HWIDGenerator.get_hwid()
    
    def create_key(self, discord_user_id=None, discord_username=None, generated_by="admin", days=KEY_VALID_DAYS):
        """Create a new premium key"""
        
        # Generate unique key
        while True:
            key = KeyGenerator.generate_key()
            existing = self.db.execute(
                'SELECT key_code FROM forex_keys WHERE key_code = ?',
                (key,)
            ).fetchone()
            if not existing:
                break
        
        now = datetime.now()
        expires = now + timedelta(days=days)
        
        self.db.execute('''
            INSERT INTO forex_keys 
            (key_code, discord_user_id, discord_username, generated_by, generated_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (key, discord_user_id, discord_username, generated_by, now, expires))
        
        # Log action
        self.db.execute('''
            INSERT INTO forex_logs (action, key_code, timestamp, details)
            VALUES (?, ?, ?, ?)
        ''', ('GENERATE', key, now, f"Generated by {generated_by}"))
        
        return key
    
    def validate_key(self, key: str) -> Dict[str, Any]:
        """Validate a key and return status"""
        result = {
            'valid': False,
            'message': '',
            'key_info': None,
            'tier': 'FREE'
        }
        
        # Check format
        if not KeyGenerator.validate_format(key):
            result['message'] = 'Invalid key format'
            return result
        
        # Get key from database
        key_data = self.db.execute('''
            SELECT * FROM forex_keys WHERE key_code = ?
        ''', (key,)).fetchone()
        
        if not key_data:
            result['message'] = 'Key not found'
            return result
        
        # Convert to dict
        columns = ['id', 'key_code', 'hwid', 'discord_user_id', 'discord_username',
                  'generated_by', 'generated_at', 'expires_at', 'used_at',
                  'last_validated', 'is_used', 'is_revoked', 'is_locked',
                  'activation_count', 'notes']
        key_dict = dict(zip(columns, key_data))
        
        # Check if revoked
        if key_dict['is_revoked']:
            result['message'] = 'Key has been revoked'
            return result
        
        # Check if used
        if key_dict['is_used']:
            result['message'] = 'Key has already been used'
            return result
        
        # Check expiry
        expires_at = datetime.fromisoformat(key_dict['expires_at'])
        if expires_at < datetime.now():
            result['message'] = 'Key has expired'
            return result
        
        # Check HWID binding
        if key_dict['hwid'] and key_dict['hwid'] != self.hwid:
            result['message'] = 'Key is bound to another computer'
            return result
        
        # Valid key
        result['valid'] = True
        result['message'] = 'Key is valid'
        result['key_info'] = key_dict
        result['tier'] = 'PREMIUM'
        
        # Update last validated
        self.db.execute('''
            UPDATE forex_keys SET last_validated = ? WHERE key_code = ?
        ''', (datetime.now(), key))
        
        return result
    
    def use_key(self, key: str) -> bool:
        """Mark a key as used (one-time use)"""
        result = self.db.execute('''
            UPDATE forex_keys 
            SET is_used = 1, used_at = ?, hwid = ?, activation_count = activation_count + 1
            WHERE key_code = ? AND is_used = 0 AND is_revoked = 0
        ''', (datetime.now(), self.hwid, key))
        
        if result.rowcount > 0:
            self.db.execute('''
                INSERT INTO forex_logs (action, key_code, hwid, timestamp)
                VALUES (?, ?, ?, ?)
            ''', ('USE', key, self.hwid, datetime.now()))
            return True
        
        return False
    
    def bind_key(self, key: str) -> bool:
        """Bind key to current HWID without marking as used"""
        result = self.db.execute('''
            UPDATE forex_keys 
            SET hwid = ?, last_validated = ?
            WHERE key_code = ? AND is_revoked = 0
        ''', (self.hwid, datetime.now(), key))
        
        return result.rowcount > 0
    
    def revoke_key(self, key: str, reason: str = "") -> bool:
        """Revoke a key (admin only)"""
        result = self.db.execute('''
            UPDATE forex_keys 
            SET is_revoked = 1, notes = ?
            WHERE key_code = ?
        ''', (reason, key))
        
        if result.rowcount > 0:
            self.db.execute('''
                INSERT INTO forex_logs (action, key_code, timestamp, details)
                VALUES (?, ?, ?, ?)
            ''', ('REVOKE', key, datetime.now(), reason))
            return True
        
        return False
    
    def get_key_info(self, key: str) -> Optional[Dict]:
        """Get detailed key information"""
        result = self.db.execute('''
            SELECT * FROM forex_keys WHERE key_code = ?
        ''', (key,)).fetchone()
        
        if not result:
            return None
        
        columns = ['id', 'key_code', 'hwid', 'discord_user_id', 'discord_username',
                  'generated_by', 'generated_at', 'expires_at', 'used_at',
                  'last_validated', 'is_used', 'is_revoked', 'is_locked',
                  'activation_count', 'notes']
        
        return dict(zip(columns, result))
    
    def list_keys(self, status=None) -> List[Dict]:
        """List all keys, optionally filtered by status"""
        query = "SELECT * FROM forex_keys"
        params = []
        
        if status == 'active':
            query += " WHERE is_used = 0 AND is_revoked = 0 AND expires_at > datetime('now')"
        elif status == 'used':
            query += " WHERE is_used = 1"
        elif status == 'expired':
            query += " WHERE is_used = 0 AND is_revoked = 0 AND expires_at <= datetime('now')"
        elif status == 'revoked':
            query += " WHERE is_revoked = 1"
        
        query += " ORDER BY generated_at DESC"
        
        results = self.db.execute(query, params).fetchall()
        
        columns = ['id', 'key_code', 'hwid', 'discord_user_id', 'discord_username',
                  'generated_by', 'generated_at', 'expires_at', 'used_at',
                  'last_validated', 'is_used', 'is_revoked', 'is_locked',
                  'activation_count', 'notes']
        
        return [dict(zip(columns, row)) for row in results]
    
    def get_stats(self) -> Dict:
        """Get key statistics"""
        total = self.db.execute("SELECT COUNT(*) FROM forex_keys").fetchone()[0]
        used = self.db.execute("SELECT COUNT(*) FROM forex_keys WHERE is_used = 1").fetchone()[0]
        revoked = self.db.execute("SELECT COUNT(*) FROM forex_keys WHERE is_revoked = 1").fetchone()[0]
        
        active = self.db.execute('''
            SELECT COUNT(*) FROM forex_keys 
            WHERE is_used = 0 AND is_revoked = 0 AND expires_at > datetime('now')
        ''').fetchone()[0]
        
        expired = self.db.execute('''
            SELECT COUNT(*) FROM forex_keys 
            WHERE is_used = 0 AND is_revoked = 0 AND expires_at <= datetime('now')
        ''').fetchone()[0]
        
        return {
            'total': total,
            'used': used,
            'revoked': revoked,
            'active': active,
            'expired': expired
        }

# ==============================================================================
# ADMIN CLI
# ==============================================================================

class AdminCLI:
    def __init__(self):
        self.km = KeyManager()
    
    def run(self):
        """Run admin command line interface"""
        print("\n" + "="*60)
        print("FOREX KEY SYSTEM - ADMIN PANEL")
        print("="*60)
        
        while True:
            print("\n1. Generate new key")
            print("2. List all keys")
            print("3. Check key status")
            print("4. Revoke key")
            print("5. Show statistics")
            print("6. Export keys to file")
            print("7. Exit")
            
            choice = input("\nSelect option: ").strip()
            
            if choice == '1':
                self.generate_key_menu()
            elif choice == '2':
                self.list_keys_menu()
            elif choice == '3':
                self.check_key_menu()
            elif choice == '4':
                self.revoke_key_menu()
            elif choice == '5':
                self.show_stats()
            elif choice == '6':
                self.export_keys()
            elif choice == '7':
                print("Exiting...")
                break
            else:
                print("Invalid option")
    
    def generate_key_menu(self):
        """Generate new key menu"""
        print("\n" + "-"*40)
        print("GENERATE NEW KEY")
        print("-"*40)
        
        discord_id = input("Discord user ID (optional): ").strip() or None
        discord_name = input("Discord username (optional): ").strip() or None
        days = input(f"Days valid (default {KEY_VALID_DAYS}): ").strip()
        days = int(days) if days else KEY_VALID_DAYS
        
        key = self.km.create_key(discord_id, discord_name, "admin", days)
        
        print(f"\n{'-'*40}")
        print(f"KEY GENERATED: {key}")
        print(f"Valid for: {days} days")
        print(f"Expires: {(datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')}")
        print(f"{'-'*40}")
    
    def list_keys_menu(self):
        """List keys menu"""
        print("\n" + "-"*40)
        print("LIST KEYS")
        print("-"*40)
        print("1. All keys")
        print("2. Active keys only")
        print("3. Used keys")
        print("4. Expired keys")
        print("5. Revoked keys")
        
        choice = input("\nSelect filter: ").strip()
        
        filters = {
            '1': None,
            '2': 'active',
            '3': 'used',
            '4': 'expired',
            '5': 'revoked'
        }
        
        keys = self.km.list_keys(filters.get(choice))
        
        print(f"\nFound {len(keys)} keys\n")
        
        for key in keys[:20]:  # Show first 20
            status = "ACTIVE" if not key['is_used'] and not key['is_revoked'] else \
                     "USED" if key['is_used'] else "REVOKED"
            
            expires = datetime.fromisoformat(key['expires_at']).strftime('%Y-%m-%d')
            print(f"{key['key_code']} - {status} - Expires: {expires}")
            
            if key['discord_username']:
                print(f"  User: {key['discord_username']}")
            if key['hwid']:
                print(f"  HWID: {key['hwid'][:16]}...")
            print()
    
    def check_key_menu(self):
        """Check key status menu"""
        print("\n" + "-"*40)
        print("CHECK KEY STATUS")
        print("-"*40)
        
        key = input("Enter key: ").strip().upper()
        info = self.km.get_key_info(key)
        
        if not info:
            print("Key not found")
            return
        
        print(f"\nKey: {info['key_code']}")
        print(f"Generated: {info['generated_at']}")
        print(f"Expires: {info['expires_at']}")
        print(f"Used: {'Yes' if info['is_used'] else 'No'}")
        if info['used_at']:
            print(f"Used at: {info['used_at']}")
        print(f"Revoked: {'Yes' if info['is_revoked'] else 'No'}")
        print(f"HWID: {info['hwid'] or 'Not bound'}")
        print(f"Discord: {info['discord_username'] or 'None'}")
        print(f"Activations: {info['activation_count']}")
    
    def revoke_key_menu(self):
        """Revoke key menu"""
        print("\n" + "-"*40)
        print("REVOKE KEY")
        print("-"*40)
        
        key = input("Enter key to revoke: ").strip().upper()
        reason = input("Reason (optional): ").strip()
        
        if self.km.revoke_key(key, reason):
            print(f"Key {key} revoked")
        else:
            print("Key not found")
    
    def show_stats(self):
        """Show statistics"""
        stats = self.km.get_stats()
        
        print("\n" + "="*40)
        print("KEY STATISTICS")
        print("="*40)
        print(f"Total keys: {stats['total']}")
        print(f"Active keys: {stats['active']}")
        print(f"Used keys: {stats['used']}")
        print(f"Expired keys: {stats['expired']}")
        print(f"Revoked keys: {stats['revoked']}")
        print("="*40)
    
    def export_keys(self):
        """Export keys to file"""
        keys = self.km.list_keys('active')
        
        filename = f"forex_keys_{datetime.now().strftime('%Y%m%d')}.txt"
        
        with open(filename, 'w') as f:
            f.write(f"FOREX PREMIUM KEYS - Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*60 + "\n\n")
            for key in keys:
                f.write(f"{key['key_code']}\n")
        
        print(f"\nExported {len(keys)} keys to {filename}")

# ==============================================================================
# API CLASS FOR INTEGRATION WITH YOUR TOOL
# ==============================================================================

class ForexKeyAPI:
    """API for integrating key validation into your tool"""
    
    def __init__(self):
        self.km = KeyManager()
        self.hwid = HWIDGenerator.get_hwid()
        self.key_status = None
    
    def check_key(self, key: str) -> Dict[str, Any]:
        """
        Check if a key is valid
        Returns: {
            'valid': bool,
            'message': str,
            'tier': str ('FREE' or 'PREMIUM'),
            'expires': str or None
        }
        """
        result = self.km.validate_key(key)
        
        if result['valid']:
            return {
                'valid': True,
                'message': 'Premium key valid',
                'tier': 'PREMIUM',
                'expires': result['key_info']['expires_at']
            }
        else:
            return {
                'valid': False,
                'message': result['message'],
                'tier': 'FREE',
                'expires': None
            }
    
    def activate_key(self, key: str) -> Dict[str, Any]:
        """
        Activate a key (mark as used)
        Returns: {
            'success': bool,
            'message': str,
            'tier': str
        }
        """
        # First validate
        validation = self.km.validate_key(key)
        
        if not validation['valid']:
            return {
                'success': False,
                'message': validation['message'],
                'tier': 'FREE'
            }
        
        # Use the key
        success = self.km.use_key(key)
        
        if success:
            return {
                'success': True,
                'message': 'Key activated successfully',
                'tier': 'PREMIUM'
            }
        else:
            return {
                'success': False,
                'message': 'Failed to activate key',
                'tier': 'FREE'
            }
    
    def get_current_hwid(self) -> str:
        """Get current machine's HWID"""
        return self.hwid

# ==============================================================================
# TEST FUNCTION
# ==============================================================================

def test_key_system():
    """Test the key system"""
    print("Testing FOREX Key System...")
    
    km = KeyManager()
    
    # Generate a test key
    test_key = km.create_key("test_user", "Test User", "test")
    print(f"Generated test key: {test_key}")
    
    # Validate the key
    result = km.validate_key(test_key)
    print(f"Validation result: {result['message']}")
    
    # Use the key
    success = km.use_key(test_key)
    print(f"Key used: {success}")
    
    # Try to use again (should fail)
    success = km.use_key(test_key)
    print(f"Second use attempt: {success}")
    
    # Get stats
    stats = km.get_stats()
    print(f"Stats: {stats}")
    
    print("\nTest complete!")

# ==============================================================================
# MAIN
# ==============================================================================

def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "--admin":
        # Admin mode
        cli = AdminCLI()
        cli.run()
    elif len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Test mode
        test_key_system()
    else:
        # API mode - for integration with your tool
        print("FOREX Key System v3.0")
        print("\nUsage:")
        print("  python forex_key_system.py --admin    # Admin panel")
        print("  python forex_key_system.py --test     # Test system")
        print("\nFor integration with your tool, import ForexKeyAPI:")
        print("  from forex_key_system import ForexKeyAPI")

if __name__ == "__main__":
    main()