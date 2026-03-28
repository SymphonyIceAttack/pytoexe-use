import hashlib
import sys
import time
import os
import random
import datetime
import getpass
import json
import threading

class DigitalCircusConsole:
    def __init__(self):
        # Система пользователей
        self.users = {
            "guest": {"level": 0, "access": "guest"},
            "caine": {"level": 5, "access": "game_master", "password": hashlib.sha256("caine2024".encode()).hexdigest()},
            "kinger": {"level": 9, "access": "admin", "password": hashlib.sha256("kinger9387".encode()).hexdigest()},
            "caine_ultimate": {"level": 10, "access": "god", "password": hashlib.sha256("caine_ultimate_2024".encode()).hexdigest()},
            "abstract": {"level": 0, "access": "corrupted", "password": hashlib.sha256("void".encode()).hexdigest()},
            "dev": {"level": 8, "access": "developer", "password": hashlib.sha256("dev123".encode()).hexdigest()},
            "mod": {"level": 6, "access": "moderator", "password": hashlib.sha256("mod456".encode()).hexdigest()},
            "observer": {"level": 3, "access": "observer", "password": hashlib.sha256("watch".encode()).hexdigest()},
            "executor": {"level": 7, "access": "executor", "password": hashlib.sha256("exec789".encode()).hexdigest()},
            "architect": {"level": 9, "access": "architect", "password": hashlib.sha256("build".encode()).hexdigest()}
        }
        
        self.current_user = "guest"
        self.current_level = 0
        self.current_access = "guest"
        self.running = True
        self.session_id = random.randint(1000, 9999)
        self.start_time = datetime.datetime.now()
        
        # Системные флаги
        self.chaos_mode_active = False
        self.time_frozen = False
        self.time_speed = 1.0
        
        # Игроки и их данные
        self.players = {
            "POMNI": {"status": "active", "level": 42, "abstraction": 0, "emotion": "anxious", "location": "main_hall"},
            "JAX": {"status": "active", "level": 38, "abstraction": 15, "emotion": "chaotic", "location": "carnival"},
            "RAGATHA": {"status": "active", "level": 35, "abstraction": 0, "emotion": "creative", "location": "art_room"},
            "GANGLE": {"status": "active", "level": 40, "abstraction": 0, "emotion": "bubbly", "location": "candy_land"},
            "ZOOBLE": {"status": "active", "level": 28, "abstraction": 0, "emotion": "curious", "location": "lab"},
            "KINGER": {"status": "active", "level": 99, "abstraction": 0, "emotion": "royal", "location": "throne_room"},
            "KAUFMO": {"status": "active", "level": 45, "abstraction": 100, "emotion": "void", "location": "abyss"},
            "RIBBIT": {"status": "active", "level": 30, "abstraction": 0, "emotion": "hopeful", "location": "pond"},
            "QUEENIE": {"status": "active", "level": 95, "abstraction": 0, "emotion": "majestic", "location": "queens_garden"},
            "SCRATCH": {"status": "active", "level": 25, "abstraction": 0, "emotion": "energetic", "location": "arcade"},
            "CAINE": {"status": "god", "level": 999, "abstraction": 0, "emotion": "omnipotent", "location": "control_room"},
            "ABSTRACTION": {"status": "corrupted", "level": 0, "abstraction": 999, "emotion": "void", "location": "nowhere"}
        }
        
        # Логи и события
        self.logs = []
        self.events = []
        self.world_state = {
            "stability": 85,
            "chaos_level": 15,
            "reality_integrity": 92,
            "memory_fragments": 47,
            "circus_energy": 73
        }
        
        self.active_mods = []
        self.instances = []
        self.backups = []
        
    def log_action(self, action):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {self.current_user.upper()}: {action}"
        self.logs.append(log_entry)
        
    def check_access(self, required_level):
        return self.current_level >= required_level
    
    def verify_user(self, username, password):
        if username.lower() in self.users:
            user_hash = hashlib.sha256(password.encode()).hexdigest()
            if self.users[username.lower()]["password"] == user_hash:
                return True
        return False
    
    def login_user(self, username):
        username = username.lower()
        if username in self.users:
            self.current_user = username
            self.current_level = self.users[username]["level"]
            self.current_access = self.users[username]["access"]
            self.log_action(f"LOGIN AS {username.upper()}")
            
            print("\n" + "="*60)
            if username == "kinger":
                print("[TRANSFERRING FULL SHELL ACCESS TO ENTITY: KINGER]")
                print("[PRIVILEGE_LEVEL = 9 (root)]")
                print("[MEMORY_PATCH_APPLIED: 0xCAINE -> 0xKINGER]")
                print("[ADMIN SHELL UNLOCKED - KINGER override active]")
            elif username == "caine_ultimate":
                print("[GOD MODE ACTIVATED]")
                print("[ACCESSING PRIMAL SOURCE CODE]")
                print("[REALITY_MANIPULATION: ENABLED]")
                print("[DIMENSIONAL_ACCESS: UNLOCKED]")
                print("[WELCOME, CREATOR]")
            elif username == "caine":
                print("[ESTABLISHING CONNECTION TO ENTITY: CAINE]")
                print("[PRIVILEGE_LEVEL = 7 (game_master)]")
                print("[CIRCUS_CONTROL: ACTIVE]")
                print("[WELCOME BACK, RINGMASTER]")
            elif username == "abstract":
                print("[CORRUPTED ENTITY DETECTED]")
                print("[ABSTRACTION_LEVEL: INFINITE]")
                print("[REALITY: UNSTABLE]")
                print("[VOID_ACCESS: GRANTED]")
            elif username == "dev":
                print("[DEVELOPER MODE ACTIVATED]")
                print("[SOURCE_CODE_ACCESS: GRANTED]")
                print("[DEBUG_TOOLS: ENABLED]")
            elif username == "mod":
                print("[MODERATOR PRIVILEGES GRANTED]")
                print("[CONTENT_FILTER: ACTIVE]")
            elif username == "observer":
                print("[OBSERVER MODE ACTIVATED]")
                print("[OMNISCIENT_VIEW: ENABLED]")
            elif username == "executor":
                print("[EXECUTOR PROTOCOL ACTIVE]")
                print("[COMMAND_PRIORITY: MAXIMUM]")
            elif username == "architect":
                print("[ARCHITECT MODE ACTIVATED]")
                print("[WORLD_EDITING: ENABLED]")
            else:
                print(f"[WELCOME, {username.upper()}]")
            print("="*60 + "\n")
        else:
            print(f"[ERROR] User '{username}' not found.\n")
    
    def logout_user(self):
        # Если был активен режим хаоса - отключаем его при выходе
        if self.chaos_mode_active:
            self.execute_disable_chaos(silent=True)
        
        self.current_user = "guest"
        self.current_level = 0
        self.current_access = "guest"
        self.log_action("LOGOUT")
        print("\n[SESSION TERMINATED]")
        print("Returning to guest privileges.\n")
    
    def execute_remove_all(self):
        if not self.check_access(9):
            print("[ERROR] Insufficient privileges. Level 9+ required.\n")
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
            if player not in ["CAINE", "ABSTRACTION"]:
                print(f"- {player}")
                time.sleep(0.05)
        print("- AND MORE")
        
        print("\n" + "="*60)
        print("> instance collapse --force --immediate")
        time.sleep(1)
        print("Circus instance terminated.")
        print("="*60 + "\n")
        
        self.logout_user()
    
    def execute_time_manipulation(self, action):
        if not self.check_access(8):
            print("[ERROR] Level 8+ required for time manipulation.\n")
            return
        
        print("\n" + "="*50)
        print(f"TIME MANIPULATION: {action.upper()}")
        print("="*50)
        
        if action == "pause":
            self.time_frozen = True
            print("[TIME FROZEN]")
            print("All processes suspended.")
        elif action == "resume":
            self.time_frozen = False
            print("[TIME RESUMED]")
            print("Normal flow restored.")
        elif action == "accelerate":
            self.time_speed = 10.0
            print("[TIME ACCELERATED x10]")
            print("Reality speeding up...")
        elif action == "normal":
            self.time_speed = 1.0
            print("[TIME NORMALIZED]")
            print("Time flow restored to normal.")
        elif action == "rewind":
            print("[TIME REWIND]")
            print("Reversing causality...")
            self.world_state["stability"] = min(100, self.world_state["stability"] + 10)
        elif action == "loop":
            print("[TIME LOOP INITIATED]")
            print("Creating temporal paradox...")
        else:
            print(f"Unknown time command: {action}")
            print("Available: pause, resume, accelerate, normal, rewind, loop")
        print("="*50 + "\n")
        self.log_action(f"TIME MANIPULATION: {action}")
    
    def execute_reality_bend(self, target):
        if not self.check_access(10):
            print("[ERROR] Reality bending requires God mode (Level 10).\n")
            return
        
        print("\n" + "="*60)
        print(f"BENDING REALITY AROUND: {target.upper()}")
        print("="*60)
        
        effects = [
            "Gravity inversion",
            "Color spectrum shift",
            "Physics override",
            "Logic loop detected",
            "Perception filter applied",
            "Probability manipulation",
            "Causality reversal",
            "Matter state change",
            "Dimensional warp",
            "Consciousness merge"
        ]
        
        for effect in random.sample(effects, 4):
            print(f"[{effect}]")
            time.sleep(0.3)
        
        self.world_state["reality_integrity"] = max(0, self.world_state["reality_integrity"] - 5)
        self.world_state["chaos_level"] = min(100, self.world_state["chaos_level"] + 10)
        
        print(f"\nReality Integrity: {self.world_state['reality_integrity']}%")
        print(f"Chaos Level: {self.world_state['chaos_level']}%")
        print("="*60 + "\n")
        self.log_action(f"REALITY BEND: {target}")
    
    def execute_spawn_entity(self, entity_type):
        if not self.check_access(9):
            print("[ERROR] Spawning entities requires Level 9+.\n")
            return
        
        entity_types = ["shadow", "echo", "fragment", "nightmare", "dream", "memory", "voidling"]
        
        if entity_type not in entity_types:
            print(f"[ERROR] Unknown entity type: {entity_type}")
            print(f"Available: {', '.join(entity_types)}\n")
            return
        
        print("\n" + "="*50)
        print(f"SPAWNING ENTITY: {entity_type.upper()}")
        print("="*50)
        
        print(f"[Entity created]")
        print(f"[Type: {entity_type}]")
        print(f"[Threat level: {random.randint(1, 10)}/10]")
        print(f"[Stability impact: -{random.randint(5, 15)}%]")
        
        self.world_state["stability"] = max(0, self.world_state["stability"] - random.randint(5, 15))
        print(f"Circus Stability: {self.world_state['stability']}%")
        print("="*50 + "\n")
        self.log_action(f"SPAWNED ENTITY: {entity_type}")
    
    def execute_world_edit(self, parameter, value):
        if not self.check_access(9):
            print("[ERROR] World editing requires Architect or higher (Level 9+).\n")
            return
        
        try:
            value = int(value)
        except ValueError:
            print("[ERROR] Value must be a number between 0 and 100.\n")
            return
        
        if parameter in self.world_state:
            old_value = self.world_state[parameter]
            self.world_state[parameter] = max(0, min(100, value))
            print("\n" + "="*50)
            print(f"WORLD PARAMETER EDITED")
            print("="*50)
            print(f"{parameter}: {old_value}% -> {self.world_state[parameter]}%")
            print("="*50 + "\n")
            self.log_action(f"WORLD EDIT: {parameter} = {value}")
        else:
            print(f"[ERROR] Unknown parameter: {parameter}")
            print("Available: stability, chaos_level, reality_integrity, memory_fragments, circus_energy\n")
    
    def execute_create_instance(self, instance_name):
        if not self.check_access(8):
            print("[ERROR] Instance creation requires Level 8+.\n")
            return
        
        instance_id = len(self.instances) + 1
        self.instances.append({
            "id": instance_id,
            "name": instance_name,
            "created": datetime.datetime.now(),
            "creator": self.current_user
        })
        
        print("\n" + "="*50)
        print(f"INSTANCE CREATED: {instance_name}")
        print("="*50)
        print(f"Instance ID: {instance_id}")
        print(f"Creator: {self.current_user}")
        print(f"Active Instances: {len(self.instances)}")
        print("="*50 + "\n")
        self.log_action(f"CREATED INSTANCE: {instance_name}")
    
    def execute_list_instances(self):
        if not self.check_access(5):
            print("[ERROR] Requires Level 5+.\n")
            return
        
        print("\n" + "="*50)
        print("ACTIVE INSTANCES")
        print("="*50)
        if not self.instances:
            print("No active instances.")
        else:
            for instance in self.instances:
                age = datetime.datetime.now() - instance["created"]
                print(f"ID: {instance['id']} | {instance['name']} | Age: {str(age).split('.')[0]} | Creator: {instance['creator']}")
        print("="*50 + "\n")
    
    def execute_delete_instance(self, instance_id):
        if not self.check_access(9):
            print("[ERROR] Instance deletion requires Level 9+.\n")
            return
        
        try:
            instance_id = int(instance_id)
            instance = next((i for i in self.instances if i["id"] == instance_id), None)
            if instance:
                self.instances.remove(instance)
                print(f"\n[INSTANCE {instance_id} DELETED]\n")
                self.log_action(f"DELETED INSTANCE: {instance_id}")
            else:
                print(f"[ERROR] Instance {instance_id} not found.\n")
        except ValueError:
            print("[ERROR] Invalid instance ID.\n")
    
    def execute_create_backup(self):
        if not self.check_access(8):
            print("[ERROR] Backup creation requires Level 8+.\n")
            return
        
        backup = {
            "id": len(self.backups) + 1,
            "timestamp": datetime.datetime.now(),
            "world_state": self.world_state.copy(),
            "players": self.players.copy(),
            "chaos_mode": self.chaos_mode_active,
            "creator": self.current_user
        }
        self.backups.append(backup)
        
        print("\n" + "="*50)
        print(f"BACKUP CREATED (ID: {backup['id']})")
        print("="*50)
        print(f"Timestamp: {backup['timestamp']}")
        print(f"World state saved")
        print(f"Players saved: {len(self.players)}")
        print(f"Chaos mode state: {'ACTIVE' if self.chaos_mode_active else 'INACTIVE'}")
        print("="*50 + "\n")
        self.log_action(f"CREATED BACKUP: {backup['id']}")
    
    def execute_restore_backup(self, backup_id):
        if not self.check_access(9):
            print("[ERROR] Backup restoration requires Level 9+.\n")
            return
        
        try:
            backup_id = int(backup_id)
            backup = next((b for b in self.backups if b["id"] == backup_id), None)
            if backup:
                self.world_state = backup["world_state"].copy()
                self.players = backup["players"].copy()
                self.chaos_mode_active = backup.get("chaos_mode", False)
                print(f"\n[BACKUP {backup_id} RESTORED]")
                if self.chaos_mode_active:
                    print("[WARNING] Chaos mode was active in this backup!")
                print("\n")
                self.log_action(f"RESTORED BACKUP: {backup_id}")
            else:
                print(f"[ERROR] Backup {backup_id} not found.\n")
        except ValueError:
            print("[ERROR] Invalid backup ID.\n")
    
    def execute_list_backups(self):
        if not self.check_access(7):
            print("[ERROR] Requires Level 7+.\n")
            return
        
        print("\n" + "="*60)
        print("AVAILABLE BACKUPS")
        print("="*60)
        if not self.backups:
            print("No backups available.")
        else:
            for backup in self.backups:
                chaos_indicator = " [CHAOS]" if backup.get("chaos_mode", False) else ""
                print(f"ID: {backup['id']} | {backup['timestamp']} | Creator: {backup['creator']}{chaos_indicator}")
        print("="*60 + "\n")
    
    def execute_mass_heal(self):
        if not self.check_access(7):
            print("[ERROR] Mass healing requires Level 7+.\n")
            return
        
        print("\n" + "="*60)
        print("INITIATING MASS HEALING PROTOCOL")
        print("="*60)
        
        healed = 0
        for player, data in self.players.items():
            if data.get('abstraction', 0) > 0:
                old = data['abstraction']
                data['abstraction'] = max(0, data['abstraction'] - 30)
                print(f"Healing {player}: {old}% -> {data['abstraction']}%")
                healed += 1
                time.sleep(0.05)
        
        print(f"\n[HEALED {healed} PLAYERS]")
        self.world_state["stability"] = min(100, self.world_state["stability"] + 15)
        print(f"Circus Stability: {self.world_state['stability']}%")
        print("="*60 + "\n")
        self.log_action("MASS HEALING PERFORMED")
    
    def execute_chaos_mode(self):
        if not self.check_access(8):
            print("[ERROR] Chaos mode requires Level 8+.\n")
            return
        
        if self.chaos_mode_active:
            print("[WARNING] Chaos mode is already active!\n")
            return
        
        self.chaos_mode_active = True
        self.world_state["chaos_level"] = 100
        self.world_state["stability"] = 0
        
        print("\n" + "="*70)
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║                                                              ║")
        print("║     !!! C H A O S   M O D E   A C T I V A T E D !!!          ║")
        print("║                                                              ║")
        print("╚══════════════════════════════════════════════════════════════╝")
        print("="*70)
        print("[REALITY DISSOLVING]")
        print("[LAWS OF PHYSICS SUSPENDED]")
        print("[EVERYTHING IS PERMITTED]")
        print("[EXIT NOT GUARANTEED]")
        print("[THE CIRCUS IS CONSUMING ITSELF]")
        print("="*70 + "\n")
        
        # Эффекты хаоса
        for _ in range(3):
            effect = random.choice([
                "Gravity fluctuating...",
                "Colors bleeding into reality...",
                "Sounds becoming visual...",
                "Time flowing backwards...",
                "Memories becoming physical...",
                "Dreams and reality merging..."
            ])
            print(f"  › {effect}")
            time.sleep(0.5)
        
        print("\n" + "="*70)
        print("Use 'disablechaos' to exit chaos mode.")
        print("="*70 + "\n")
        self.log_action("CHAOS MODE ACTIVATED")
    
    def execute_disable_chaos(self, silent=False):
        """Отключает режим хаоса"""
        if not self.chaos_mode_active:
            if not silent:
                print("[INFO] Chaos mode is not active.\n")
            return
        
        self.chaos_mode_active = False
        self.world_state["chaos_level"] = 15
        self.world_state["stability"] = 85
        
        if not silent:
            print("\n" + "="*70)
            print("╔══════════════════════════════════════════════════════════════╗")
            print("║                                                              ║")
            print("║     C H A O S   M O D E   D E A C T I V A T E D              ║")
            print("║                                                              ║")
            print("╚══════════════════════════════════════════════════════════════╝")
            print("="*70)
            print("[REALITY STABILIZING]")
            print("[LAWS OF PHYSICS RESTORED]")
            print("[ORDER REESTABLISHED]")
            print("[CIRCUS STABILIZED]")
            print("="*70 + "\n")
        
        self.log_action("CHAOS MODE DEACTIVATED")
    
    def execute_stabilize(self):
        if not self.check_access(7):
            print("[ERROR] Stabilization requires Level 7+.\n")
            return
        
        # Если активен режим хаоса, сначала отключаем его
        if self.chaos_mode_active:
            self.execute_disable_chaos(silent=False)
        
        self.world_state["stability"] = 100
        self.world_state["chaos_level"] = 0
        self.world_state["reality_integrity"] = 100
        self.world_state["circus_energy"] = 100
        
        print("\n" + "="*60)
        print("STABILIZATION PROTOCOL COMPLETE")
        print("="*60)
        print("Reality has been stabilized")
        print("All parameters restored to optimal levels")
        print("The circus is now perfectly balanced")
        print("="*60 + "\n")
        self.log_action("SYSTEM STABILIZED")
    
    def execute_players_list(self):
        print("\n" + "="*80)
        print("CIRCUS INHABITANTS")
        print("="*80)
        print(f"{'PLAYER':<12} {'STATUS':<10} {'LEVEL':<6} {'ABSTRACTION':<12} {'EMOTION':<12} {'LOCATION':<15}")
        print("-"*80)
        for player, data in self.players.items():
            abstraction_bar = "█" * (data.get('abstraction', 0) // 10) + "░" * (10 - data.get('abstraction', 0) // 10)
            print(f"{player:<12} {data.get('status', 'unknown'):<10} {data.get('level', 0):<6} [{abstraction_bar}] {data.get('abstraction', 0):<3}% {data.get('emotion', 'unknown'):<12} {data.get('location', 'unknown'):<15}")
        print("="*80 + "\n")
    
    def execute_player_info(self, player_name):
        player_name = player_name.upper()
        if player_name not in self.players:
            print(f"[ERROR] Player '{player_name}' not found.\n")
            return
        
        data = self.players[player_name]
        print("\n" + "="*70)
        print(f"PLAYER PROFILE: {player_name}")
        print("="*70)
        print(f"Status: {data.get('status', 'unknown')}")
        print(f"Level: {data.get('level', 0)}")
        print(f"Abstraction: {data.get('abstraction', 0)}%")
        print(f"Emotion: {data.get('emotion', 'unknown')}")
        print(f"Location: {data.get('location', 'unknown')}")
        
        if self.check_access(5):
            print(f"Memory Address: 0x{hash(player_name) & 0xFFFFFFFF:08X}")
            print(f"Neural Pattern: {hashlib.md5(player_name.encode()).hexdigest()[:16]}")
            print(f"Exit Probability: {random.randint(0, 100)}%")
        
        if self.check_access(8):
            print(f"Source Code: {hashlib.sha256(player_name.encode()).hexdigest()[:20]}...")
            print(f"Reality Anchor: {'STABLE' if random.random() > 0.3 else 'UNSTABLE'}")
        
        if self.chaos_mode_active:
            print("\n[CHAOS MODE EFFECTS ACTIVE]")
            print(f"  › {random.choice(['Reality shifting', 'Identity fragmentation', 'Memory corruption', 'Emotion amplification'])}")
        
        print("="*70 + "\n")
    
    def execute_world_status(self):
        print("\n" + "="*60)
        print("WORLD STATUS")
        print("="*60)
        print(f"Stability: {'█' * (self.world_state['stability'] // 10)}{'░' * (10 - self.world_state['stability'] // 10)} {self.world_state['stability']}%")
        print(f"Chaos Level: {'█' * (self.world_state['chaos_level'] // 10)}{'░' * (10 - self.world_state['chaos_level'] // 10)} {self.world_state['chaos_level']}%")
        print(f"Reality Integrity: {'█' * (self.world_state['reality_integrity'] // 10)}{'░' * (10 - self.world_state['reality_integrity'] // 10)} {self.world_state['reality_integrity']}%")
        print(f"Memory Fragments: {self.world_state['memory_fragments']}%")
        print(f"Circus Energy: {self.world_state['circus_energy']}%")
        
        if self.chaos_mode_active:
            print("\n[⚠️  CHAOS MODE ACTIVE ⚠️]")
            print("  Reality is unstable. Use 'disablechaos' to stabilize.")
        if self.time_frozen:
            print("\n[⏸️  TIME FROZEN ⏸️]")
        if self.time_speed != 1.0:
            print(f"\n[⏩ TIME SPEED: x{self.time_speed} ⏩]")
        
        print("="*60 + "\n")
    
    def execute_system_status(self):
        uptime = datetime.datetime.now() - self.start_time
        print("\n" + "="*70)
        print("SYSTEM STATUS")
        print("="*70)
        print(f"Session ID: {self.session_id}")
        print(f"Current User: {self.current_user.upper()} (Level {self.current_level})")
        print(f"Access Level: {self.current_access.upper()}")
        print(f"Uptime: {str(uptime).split('.')[0]}")
        print(f"Active Players: {sum(1 for data in self.players.values() if data.get('status') == 'active')}")
        print(f"Active Instances: {len(self.instances)}")
        print(f"Backups Available: {len(self.backups)}")
        print(f"Log Entries: {len(self.logs)}")
        
        print("\nActive Modes:")
        print(f"  Chaos Mode: {'✅ ACTIVE' if self.chaos_mode_active else '❌ INACTIVE'}")
        print(f"  Time Freeze: {'✅ ACTIVE' if self.time_frozen else '❌ INACTIVE'}")
        print(f"  Time Speed: x{self.time_speed}")
        
        print("\nAccess Matrix:")
        if self.check_access(0):
            print("  ✓ Guest (Level 0)")
        if self.check_access(3):
            print("  ✓ Observer (Level 3)")
        if self.check_access(5):
            print("  ✓ Game Master (Level 5)")
        if self.check_access(6):
            print("  ✓ Moderator (Level 6)")
        if self.check_access(7):
            print("  ✓ Executor (Level 7)")
        if self.check_access(8):
            print("  ✓ Developer (Level 8)")
        if self.check_access(9):
            print("  ✓ Architect/Admin (Level 9)")
        if self.check_access(10):
            print("  ✓ GOD MODE (Level 10)")
        print("="*70 + "\n")
    
    def execute_logs(self):
        if not self.check_access(5):
            print("[ERROR] Requires Level 5+.\n")
            return
        
        print("\n" + "="*70)
        print("SYSTEM LOGS (Last 25 entries)")
        print("="*70)
        if not self.logs:
            print("No logs available.")
        else:
            for log in self.logs[-25:]:
                print(log)
        print("="*70 + "\n")
    
    def execute_help(self):
        print("\n" + "="*80)
        print("DIGITAL CIRCUS CONSOLE - COMPLETE COMMAND REFERENCE")
        print("="*80)
        
        print("\n[ACCESS COMMANDS]")
        print("-"*40)
        print("/login <username>   - Login as specific user")
        print("/users              - List all available users")
        print("logout              - Logout current session")
        
        print("\n[INFORMATION COMMANDS]")
        print("-"*40)
        print("help                - Show this help message")
        print("status              - Show system status")
        print("world               - Show world parameters")
        print("players             - List all circus inhabitants")
        print("player <name>       - Show detailed player info")
        print("logs                - View system logs (Level 5+)")
        print("instances           - List active instances (Level 5+)")
        print("backups             - List available backups (Level 7+)")
        
        print("\n[ADMIN COMMANDS (Level 7-8)]")
        print("-"*40)
        print("healall             - Mass healing of all players")
        print("stabilize           - Fully stabilize the circus")
        print("backup              - Create system backup")
        print("create <name>       - Create new instance")
        
        print("\n[ARCHITECT COMMANDS (Level 9)]")
        print("-"*40)
        print("remove all players --include-abstractions --force --no-grace --no-save --purge-neural-locks")
        print("                    - Emergency mass eviction")
        print("edit <param> <value>- Edit world parameters")
        print("spawn <type>        - Spawn entities (shadow/echo/fragment/nightmare/dream/memory/voidling)")
        print("restore <id>        - Restore from backup")
        print("delete <id>         - Delete instance")
        
        print("\n[GOD MODE COMMANDS (Level 10)]")
        print("-"*40)
        print("time <action>       - Manipulate time (pause/resume/accelerate/normal/rewind/loop)")
        print("bend <target>       - Bend reality around target")
        
        print("\n[CHAOS MODE COMMANDS]")
        print("-"*40)
        print("chaos               - Activate chaos mode (Level 8+)")
        print("disablechaos        - Deactivate chaos mode (Level 8+)")
        
        print("\n[SYSTEM COMMANDS]")
        print("-"*40)
        print("clear               - Clear the screen")
        print("exit --confirm      - Close shell session")
        print("="*80 + "\n")
    
    def execute_list_users(self):
        print("\n" + "="*60)
        print("AVAILABLE USERS")
        print("="*60)
        print(f"{'USERNAME':<18} {'LEVEL':<8} {'ACCESS':<15}")
        print("-"*60)
        for username, data in self.users.items():
            if username != "guest":
                print(f"{username:<18} {data['level']:<8} {data['access']}")
        print("="*60 + "\n")
    
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def process_command(self, command):
        command = command.strip()
        
        if not command:
            return True
        
        # Команды входа
        if command.startswith("/login "):
            username = command[7:].strip()
            if username not in self.users:
                print(f"[ERROR] User '{username}' not found.\n")
                return True
            
            print(f"\n[LOGIN: {username.upper()}]")
            try:
                password = getpass.getpass(f"Enter password for {username}: ")
            except:
                password = input(f"Enter password for {username}: ")
            
            if self.verify_user(username, password):
                self.login_user(username)
            else:
                print("[ACCESS DENIED] Invalid credentials.\n")
            return True
        
        if command == "/users":
            self.execute_list_users()
            return True
        
        # Команда logout
        if command == "logout":
            self.logout_user()
            return True
        
        # Команда remove all players
        if command == "remove all players --include-abstractions --force --no-grace --no-save --purge-neural-locks":
            self.execute_remove_all()
            return True
        
        # Команды времени (God mode)
        if command.startswith("time "):
            action = command[5:].strip()
            self.execute_time_manipulation(action)
            return True
        
        # Команда bend (God mode)
        if command.startswith("bend "):
            target = command[5:].strip()
            self.execute_reality_bend(target)
            return True
        
        # Команда spawn
        if command.startswith("spawn "):
            entity_type = command[6:].strip()
            self.execute_spawn_entity(entity_type)
            return True
        
        # Команда edit
        if command.startswith("edit "):
            parts = command[5:].split()
            if len(parts) == 2:
                self.execute_world_edit(parts[0], parts[1])
            else:
                print("Usage: edit <parameter> <value>\n")
            return True
        
        # Команда create instance
        if command.startswith("create "):
            instance_name = command[7:].strip()
            self.execute_create_instance(instance_name)
            return True
        
        # Команда instances
        if command == "instances":
            self.execute_list_instances()
            return True
        
        # Команда delete instance
        if command.startswith("delete "):
            instance_id = command[7:].strip()
            self.execute_delete_instance(instance_id)
            return True
        
        # Команда backup
        if command == "backup":
            self.execute_create_backup()
            return True
        
        # Команда restore
        if command.startswith("restore "):
            backup_id = command[8:].strip()
            self.execute_restore_backup(backup_id)
            return True
        
        # Команда backups
        if command == "backups":
            self.execute_list_backups()
            return True
        
        # Команда healall
        if command == "healall":
            self.execute_mass_heal()
            return True
        
        # Команда chaos
        if command == "chaos":
            self.execute_chaos_mode()
            return True
        
        # Команда disablechaos (НОВАЯ КОМАНДА!)
        if command == "disablechaos":
            self.execute_disable_chaos(silent=False)
            return True
        
        # Команда stabilize
        if command == "stabilize":
            self.execute_stabilize()
            return True
        
        # Команда players
        if command == "players":
            self.execute_players_list()
            return True
        
        # Команда player
        if command.startswith("player "):
            player_name = command[7:].strip()
            self.execute_player_info(player_name)
            return True
        
        # Команда world
        if command == "world":
            self.execute_world_status()
            return True
        
        # Команда status
        if command == "status":
            self.execute_system_status()
            return True
        
        # Команда logs
        if command == "logs":
            self.execute_logs()
            return True
        
        # Команда help
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
            # При выходе отключаем режим хаоса
            if self.chaos_mode_active:
                self.execute_disable_chaos(silent=True)
            print("\n>exit --confirm")
            time.sleep(0.5)
            print("Shell session closed.")
            self.running = False
            return True
        
        # Если команда не распознана
        print(f"[ERROR] Unknown command: {command}")
        print("Type 'help' for available commands.\n")
        
        return True
    
    def print_banner(self):
        banner = """
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║     ████████████████████████████████████████████████████████████████     ║
║     █░█░█░█ THE AMAZING DIGITAL CIRCUS - ULTIMATE EDITION █░█░█░█       ║
║     ████████████████████████████████████████████████████████████████     ║
║                                                                          ║
║     Welcome to the Advanced Digital Circus Management System             ║
║                                                                          ║
║     AVAILABLE USERS (Use '/login <username>'):                          ║
║     • caine          (Level 5)  - Game Master                           ║
║     • kinger         (Level 9)  - Admin                                 ║
║     • caine_ultimate (Level 10) - GOD MODE                              ║
║     • dev            (Level 8)  - Developer                             ║
║     • mod            (Level 6)  - Moderator                             ║
║     • observer       (Level 3)  - Observer                              ║
║     • executor       (Level 7)  - Executor                              ║
║     • architect      (Level 9)  - Architect                             ║
║                                                                          ║
║     CHAOS MODE: Use 'chaos' to activate, 'disablechaos' to deactivate   ║
║                                                                          ║
║     Type 'help' for all available commands                              ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
        """
        print(banner)
    
    def run(self):
        self.clear_screen()
        self.print_banner()
        
        while self.running:
            try:
                # Разные промпты в зависимости от режима
                if self.chaos_mode_active:
                    prompt = f"🔥{self.current_user.upper()}@CHAOS:~# "
                elif self.current_level >= 9:
                    prompt = f"{self.current_user.upper()}@circus:~# "
                elif self.current_level >= 5:
                    prompt = f"{self.current_user.upper()}@circus:~> "
                else:
                    prompt = f"{self.current_user}@circus:~$ "
                
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