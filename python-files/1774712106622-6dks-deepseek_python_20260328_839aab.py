import hashlib
import sys
import time
import os
import random
import datetime
import getpass

class DigitalCircusConsole:
    def __init__(self):
        self.admin_access = False
        self.caine_access = False
        self.password_hash = hashlib.sha256("kinger9387".encode()).hexdigest()
        self.caine_password_hash = hashlib.sha256("caine2024".encode()).hexdigest()
        self.running = True
        self.current_user = "guest"
        self.session_id = random.randint(1000, 9999)
        self.start_time = datetime.datetime.now()
        
        self.players = {
            "POMNI": {"status": "active", "level": 42, "abstraction": 0},
            "JAX": {"status": "active", "level": 38, "abstraction": 15},
            "RAGATHA": {"status": "active", "level": 35, "abstraction": 0},
            "GANGLE": {"status": "active", "level": 40, "abstraction": 0},
            "ZOOBLE": {"status": "active", "level": 28, "abstraction": 0},
            "KINGER": {"status": "active", "level": 99, "abstraction": 0},
            "KAUFMO": {"status": "active", "level": 45, "abstraction": 100},
            "RIBBIT": {"status": "active", "level": 30, "abstraction": 0},
            "QUEENIE": {"status": "active", "level": 95, "abstraction": 0},
            "SCRATCH": {"status": "active", "level": 25, "abstraction": 0}
        }
        
        self.logs = []
        
    def log_action(self, action):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {self.current_user.upper()}: {action}"
        self.logs.append(log_entry)
        
    def check_admin(self):
        return self.admin_access
    
    def check_caine(self):
        return self.caine_access
    
    def verify_password(self, password, user_type="admin"):
        if user_type == "admin":
            return hashlib.sha256(password.encode()).hexdigest() == self.password_hash
        elif user_type == "caine":
            return hashlib.sha256(password.encode()).hexdigest() == self.caine_password_hash
        return False
    
    def grant_admin_access(self):
        self.admin_access = True
        self.current_user = "kinger"
        self.log_action("ADMIN ACCESS GRANTED")
        print("\n" + "="*60)
        print("[TRANSFERRING FULL SHELL ACCESS TO ENTITY: KINGER]")
        print("[PRIVILEGE_LEVEL = 9 (root)]")
        print("[MEMORY_PATCH_APPLIED: 0xCAINE -> 0xKINGER]")
        print("[ADMIN SHELL UNLOCKED - KINGER override active]")
        print("="*60 + "\n")
    
    def grant_caine_access(self):
        self.caine_access = True
        self.current_user = "caine"
        self.log_action("CAINE ACCESS GRANTED")
        print("\n" + "="*60)
        print("[ESTABLISHING CONNECTION TO ENTITY: CAINE]")
        print("[PRIVILEGE_LEVEL = 7 (game_master)]")
        print("[CIRCUS_CONTROL: ACTIVE]")
        print("[WELCOME BACK, RINGMASTER]")
        print("="*60 + "\n")
    
    def revoke_access(self):
        self.admin_access = False
        self.caine_access = False
        self.current_user = "guest"
        self.log_action("ALL ACCESS REVOKED")
        print("\n[ALL SESSIONS TERMINATED]")
        print("Returning to guest privileges.\n")
    
    def execute_remove_all(self):
        if not self.check_admin():
            print("[ERROR] Insufficient privileges. Admin access required.")
            print("Use /admin to gain administrative privileges.\n")
            return
        
        print("\n" + "="*60)
        print("Executing emergency mass eviction protocol")
        print("-"*60)
        time.sleep(1)
        print("\nMass removal executed")
        time.sleep(1)
        print("\nRemoved from The Amazing Digital Circus:")
        print("-"*40)
        
        for player in self.players.keys():
            print(f"- {player}")
            time.sleep(0.05)
        print("- AND MORE")
        
        print("\n" + "="*60)
        print("> instance collapse --force --immediate")
        time.sleep(1)
        print("Circus instance terminated.")
        print("="*60 + "\n")
        
        self.revoke_access()
    
    def execute_list_players(self):
        print("\n" + "="*60)
        print("CIRCUS INHABITANTS")
        print("="*60)
        print(f"{'PLAYER':<12} {'STATUS':<10} {'LEVEL':<6} {'ABSTRACTION':<12}")
        print("-"*60)
        for player, data in self.players.items():
            abstraction_bar = "█" * (data['abstraction'] // 10) + "░" * (10 - data['abstraction'] // 10)
            print(f"{player:<12} {data['status']:<10} {data['level']:<6} [{abstraction_bar}] {data['abstraction']}%")
        print("="*60 + "\n")
    
    def execute_player_info(self, player_name):
        player_name = player_name.upper()
        if player_name not in self.players:
            print(f"[ERROR] Player '{player_name}' not found.\n")
            return
        
        data = self.players[player_name]
        print("\n" + "="*60)
        print(f"PLAYER PROFILE: {player_name}")
        print("="*60)
        print(f"Status: {data['status']}")
        print(f"Level: {data['level']}")
        print(f"Abstraction Level: {data['abstraction']}%")
        
        if self.check_admin() or self.check_caine():
            print(f"Memory Address: 0x{hash(player_name) & 0xFFFFFFFF:08X}")
            print(f"Neural Pattern: {hashlib.md5(player_name.encode()).hexdigest()[:16]}")
            print(f"Exit Probability: {random.randint(0, 100)}%")
        print("="*60 + "\n")
    
    def execute_abstraction_check(self):
        if not (self.check_admin() or self.check_caine()):
            print("[ERROR] Insufficient privileges. Admin or Caine access required.\n")
            return
        
        total_abstraction = sum(data['abstraction'] for data in self.players.values()) / len(self.players)
        print("\n" + "="*60)
        print("CIRCUS ABSTRACTION ANALYSIS")
        print("="*60)
        print(f"Average Abstraction: {total_abstraction:.1f}%")
        print(f"Critical Level Players: {sum(1 for data in self.players.values() if data['abstraction'] >= 80)}")
        print(f"Stable Players: {sum(1 for data in self.players.values() if data['abstraction'] <= 20)}")
        
        if total_abstraction > 50:
            print("\n[WARNING] Critical abstraction levels detected!")
            print("Recommend immediate intervention.")
        print("="*60 + "\n")
    
    def execute_cleanup(self):
        if not self.check_admin():
            print("[ERROR] Admin privileges required for cleanup operations.\n")
            return
        
        print("\n" + "="*60)
        print("INITIATING ABSTRACTION CLEANUP PROTOCOL")
        print("="*60)
        
        cleaned = 0
        for player, data in self.players.items():
            if data['abstraction'] > 0:
                old_abstraction = data['abstraction']
                data['abstraction'] = max(0, data['abstraction'] - 50)
                print(f"Cleaning {player}: {old_abstraction}% -> {data['abstraction']}%")
                cleaned += 1
                time.sleep(0.1)
        
        print(f"\n[SUCCESS] Cleaned {cleaned} players")
        print("Abstraction levels reduced.")
        print("="*60 + "\n")
        self.log_action("ABSTRACTION CLEANUP PERFORMED")
    
    def execute_logs(self):
        if not (self.check_admin() or self.check_caine()):
            print("[ERROR] Insufficient privileges. Admin or Caine access required.\n")
            return
        
        print("\n" + "="*60)
        print("SYSTEM LOGS")
        print("="*60)
        if not self.logs:
            print("No logs available.")
        else:
            for log in self.logs[-20:]:
                print(log)
        print("="*60 + "\n")
    
    def execute_status(self):
        uptime = datetime.datetime.now() - self.start_time
        print("\n" + "="*50)
        print("SYSTEM STATUS")
        print("="*50)
        print(f"Session ID: {self.session_id}")
        print(f"Current User: {self.current_user.upper()}")
        print(f"Uptime: {str(uptime).split('.')[0]}")
        print(f"Active Players: {sum(1 for data in self.players.values() if data['status'] == 'active')}")
        
        if self.check_admin():
            print("Access: ██████████ [ADMIN - KINGER]")
        elif self.check_caine():
            print("Access: ████████░░ [CAINE - GAME MASTER]")
        else:
            print("Access: ░░░░░░░░░░ [GUEST]")
        print("="*50 + "\n")
    
    def execute_caine_reset(self):
        if not self.check_caine():
            print("[ERROR] Caine access required for this operation.\n")
            return
        
        print("\n" + "="*60)
        print("RESETTING CIRCUS STABILITY")
        print("="*60)
        
        for player, data in self.players.items():
            old_abstraction = data['abstraction']
            data['abstraction'] = 0
            print(f"Resetting {player}: {old_abstraction}% -> 0%")
            time.sleep(0.05)
        
        print("\n[SUCCESS] All abstraction levels reset to 0%")
        print("The circus is stable again.")
        print("="*60 + "\n")
        self.log_action("CAINE: FULL SYSTEM RESET")
    
    def execute_heal_player(self, player_name):
        if not self.check_caine():
            print("[ERROR] Caine access required for healing operations.\n")
            return
        
        player_name = player_name.upper()
        if player_name not in self.players:
            print(f"[ERROR] Player '{player_name}' not found.\n")
            return
        
        old_abstraction = self.players[player_name]['abstraction']
        self.players[player_name]['abstraction'] = 0
        
        print("\n" + "="*50)
        print(f"HEALING PROCEDURE: {player_name}")
        print("="*50)
        print(f"Abstraction reduced: {old_abstraction}% -> 0%")
        print(f"[SUCCESS] {player_name} has been fully restored!")
        print("="*50 + "\n")
        self.log_action(f"CAINE: HEALED {player_name}")
    
    def execute_help(self):
        print("\n" + "="*70)
        print("DIGITAL CIRCUS CONSOLE - COMMAND REFERENCE")
        print("="*70)
        
        print("\n[ACCESS COMMANDS]")
        print("-"*40)
        print("/admin              - Request administrative access (KINGER)")
        print("/caine              - Request game master access (CAINE)")
        print("logout              - Revoke all access privileges")
        
        print("\n[INFORMATION COMMANDS]")
        print("-"*40)
        print("help                - Show this help message")
        print("status              - Show current system status")
        print("players             - List all circus inhabitants")
        print("player <name>       - Show detailed info about a specific player")
        print("logs                - View system logs (Admin/Caine only)")
        print("abstraction         - Check circus abstraction levels (Admin/Caine only)")
        
        print("\n[ADMIN COMMANDS]")
        print("-"*40)
        print("remove all players --include-abstractions --force --no-grace --no-save --purge-neural-locks")
        print("                    - Execute emergency mass eviction")
        print("cleanup             - Perform abstraction cleanup")
        
        print("\n[CAINE COMMANDS]")
        print("-"*40)
        print("reset               - Reset all player abstraction levels")
        print("heal <player>       - Heal a specific player from abstraction")
        
        print("\n[SYSTEM COMMANDS]")
        print("-"*40)
        print("exit --confirm      - Close shell session")
        print("clear               - Clear the screen")
        print("="*70 + "\n")
    
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def process_command(self, command):
        command = command.strip()
        
        if not command:
            return True
        
        # Команда /admin
        if command == "/admin":
            if self.check_admin():
                print("[ALERT] Admin session already active.\n")
                return True
            
            print("\n[ADMIN ACCESS REQUEST]")
            try:
                password = getpass.getpass("Enter admin password: ")
            except:
                password = input("Enter admin password: ")
            
            if self.verify_password(password, "admin"):
                self.grant_admin_access()
            else:
                print("[ACCESS DENIED] Invalid credentials.\n")
            return True
        
        # Команда /caine
        if command == "/caine":
            if self.check_caine():
                print("[ALERT] Caine session already active.\n")
                return True
            
            print("\n[CAINE ACCESS REQUEST]")
            try:
                password = getpass.getpass("Enter Caine password: ")
            except:
                password = input("Enter Caine password: ")
            
            if self.verify_password(password, "caine"):
                self.grant_caine_access()
            else:
                print("[ACCESS DENIED] Invalid credentials.\n")
            return True
        
        # Команда logout
        if command == "logout":
            if self.check_admin() or self.check_caine():
                self.revoke_access()
            else:
                print("[ERROR] No active session to logout.\n")
            return True
        
        # Команда remove all players
        if command == "remove all players --include-abstractions --force --no-grace --no-save --purge-neural-locks":
            self.execute_remove_all()
            return True
        
        # Команда players
        if command == "players":
            self.execute_list_players()
            return True
        
        # Команда player <name>
        if command.startswith("player "):
            player_name = command[7:].strip()
            self.execute_player_info(player_name)
            return True
        
        # Команда abstraction
        if command == "abstraction":
            self.execute_abstraction_check()
            return True
        
        # Команда cleanup
        if command == "cleanup":
            self.execute_cleanup()
            return True
        
        # Команда logs
        if command == "logs":
            self.execute_logs()
            return True
        
        # Команда reset (Caine)
        if command == "reset":
            self.execute_caine_reset()
            return True
        
        # Команда heal <player>
        if command.startswith("heal "):
            player_name = command[5:].strip()
            self.execute_heal_player(player_name)
            return True
        
        # Команда status (БЕЗ слеша!)
        if command == "status":
            self.execute_status()
            return True
        
        # Команда help (БЕЗ слеша!)
        if command == "help":
            self.execute_help()
            return True
        
        # Команда clear
        if command == "clear":
            self.clear_screen()
            self.print_banner()
            return True
        
        # Команда exit
        if command == "exit --confirm":
            if self.check_admin() or self.check_caine():
                print("\n>exit --confirm")
                time.sleep(0.5)
                print("Shell session closed.")
                self.running = False
            else:
                print("[ERROR] No active session to exit.")
                print("Use 'exit --confirm' while logged in to close the shell.\n")
            return True
        
        # Если команда не распознана
        print(f"[ERROR] Unknown command: {command}")
        print("Type 'help' for available commands.\n")
        
        return True
    
    def print_banner(self):
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     ████████████████████████████████████████████████████     ║
║     █░█░█ THE AMAZING DIGITAL CIRCUS █░█░█                  ║
║     ████████████████████████████████████████████████████     ║
║                                                              ║
║     Welcome to the Digital Circus Management System         ║
║                                                              ║
║     Available Access Levels:                                ║
║     • GUEST  - Basic information viewing                    ║
║     • CAINE  - Game master privileges (pass: caine2024)     ║
║     • KINGER - Full administrative access (pass: kinger9387)║
║                                                              ║
║     Type 'help' for all available commands                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(banner)
    
    def run(self):
        self.clear_screen()
        self.print_banner()
        
        while self.running:
            try:
                if self.check_admin():
                    prompt = "KINGER@circus:~# "
                elif self.check_caine():
                    prompt = "CAINE@circus:~> "
                else:
                    prompt = "guest@circus:~$ "
                
                user_input = input(prompt)
                self.process_command(user_input)
                
            except KeyboardInterrupt:
                print("\n\n[INTERRUPT] Use 'exit --confirm' to quit.\n")
            except EOFError:
                break
            except Exception as e:
                print(f"\n[ERROR] Unexpected error: {e}\n")
                self.log_action(f"ERROR: {e}")

def main():
    console = DigitalCircusConsole()
    
    try:
        console.run()
    except Exception as e:
        print(f"\n[FATAL] System error: {e}")
        sys.exit(1)
    finally:
        print("\n[SYSTEM] Console terminated.")
        sys.exit(0)

if __name__ == "__main__":
    main()