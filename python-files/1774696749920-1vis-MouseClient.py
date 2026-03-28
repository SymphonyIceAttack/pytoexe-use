import os
import sys
import random
import time
import ctypes
from datetime import datetime

# Set console title
ctypes.windll.kernel32.SetConsoleTitleW("Mouse Client - Cat & Mouse.io Mod Menu")

# Console settings
os.system("mode con: cols=85 lines=40")
os.system("color 0F")

class FakeModMenu:
    def __init__(self):
        self.modules = {
            "ESP": False,
            "SpeedHack": False,
            "Team Change": False,
            "Auto Dodge": False,
            "Auto Catch": False,
            "Auto Win": False,
            "Server Crash": False,
            "Fly Glitch": False,
            "B-Hop": False
        }
    
    def clear(self):
        os.system("cls")
    
    def print_ascii(self):
        """Print ASCII art"""
        print("\033[95m" + r"""
    ╔═══════════════════════════════════════════════════════════════════════════════════════════════════════╗
    ║                                                                                                       ║
    ║     ███╗   ███╗ ██████╗ ██╗   ██╗███████╗███████╗     ██████╗██╗     ██╗███████╗███╗   ██╗████████╗   ║
    ║     ████╗ ████║██╔═══██╗██║   ██║██╔════╝██╔════╝    ██╔════╝██║     ██║██╔════╝████╗  ██║╚══██╔══╝   ║
    ║     ██╔████╔██║██║   ██║██║   ██║███████╗█████╗      ██║     ██║     ██║█████╗  ██╔██╗ ██║   ██║      ║
    ║     ██║╚██╔╝██║██║   ██║██║   ██║╚════██║██╔══╝      ██║     ██║     ██║██╔══╝  ██║╚██╗██║   ██║      ║
    ║     ██║ ╚═╝ ██║╚██████╔╝╚██████╔╝███████║███████╗    ╚██████╗███████╗██║███████╗██║ ╚████║   ██║      ║
    ║     ╚═╝     ╚═╝ ╚═════╝  ╚═════╝ ╚══════╝╚══════╝     ╚═════╝╚══════╝╚═╝╚══════╝╚═╝  ╚═══╝   ╚═╝      ║
    ║                                                                                                       ║
    ║                                           Cat & Mouse.io                                              ║
    ║                                         MOUSE - CLIENT v1.2                                           ║
    ║                                                                                                       ║
    ║                                                                                                       ║
    ╚═══════════════════════════════════════════════════════════════════════════════════════════════════════╝
        \033[0m""")
    
    def print_menu(self):
        """Print clean menu"""
        print("\n" + "=" * 85)
        print("  🎮 ACTIVE MODULES".center(85))
        print("=" * 85)
        
        # Module list in two columns for better layout
        module_items = list(self.modules.items())
        mid = (len(module_items) + 1) // 2
        
        for i in range(mid):
            left_name, left_active = module_items[i]
            right_name, right_active = module_items[i + mid] if i + mid < len(module_items) else (None, None)
            
            left_status = "● ACTIVE" if left_active else "○ DISABLED"
            left_color = "\033[92m" if left_active else "\033[90m"
            
            left_line = f"  {left_name:<16} {left_color}{left_status}\033[0m"
            
            if right_name:
                right_status = "● ACTIVE" if right_active else "○ DISABLED"
                right_color = "\033[92m" if right_active else "\033[90m"
                right_line = f"  {right_name:<16} {right_color}{right_status}\033[0m"
                print(f"{left_line:<45} {right_line}")
            else:
                print(left_line)
        
        print("=" * 85)
        print("  📌 CONTROLS".center(85))
        print("=" * 85)
        print("    [1] ESP           [4] Auto Dodge     [7] Server Crash    [0] Exit")
        print("    [2] SpeedHack     [5] Auto Catch     [8] Fly Glitch")
        print("    [3] Team Change   [6] Auto Win       [9] B-Hop")
        print("=" * 85)
        print()
    
    def loading_animation(self, text, duration=1.0):
        print(f"\n{text}", end="")
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        for _ in range(int(duration * 15)):
            for frame in frames:
                print(f"\r{text} {frame}", end="")
                time.sleep(0.02)
        print(f"\r{text} ✅ DONE!   ")
    
    def fake_progress(self, hack_name):
        print(f"\n\033[93m[!] Injecting {hack_name}...\033[0m")
        for i in range(101):
            progress = "█" * (i // 5) + "░" * (20 - (i // 5))
            print(f"\r\033[92m[{progress}] {i}%\033[0m", end="")
            time.sleep(0.008)
        print(f"\n\033[92m✅ {hack_name} successfully activated!\033[0m")
    
    def fake_coords_scan(self):
        print("\n\033[96m[SCANNING] Searching for players in radius 100m...\033[0m")
        players = random.randint(3, 12)
        for i in range(players):
            x = random.randint(-500, 500)
            y = random.randint(-500, 500)
            team = random.choice(["Mouse 🐭", "Cat 🐱"])
            hp = random.randint(30, 100)
            print(f"  Player {i+1}: {team} | X:{x} Y:{y} | HP:{hp}")
            time.sleep(0.05)
        print(f"\n\033[92m✅ Found {players} players!\033[0m")
    
    def fake_speed_boost(self):
        print("\n\033[93m[SPEED HACK] Calibrating movement system...\033[0m")
        speeds = [5, 10, 15, 20, 25, 50, 100]
        for speed in speeds:
            print(f"  Current speed: {speed} units/sec")
            time.sleep(0.1)
        final_speed = random.randint(200, 999)
        print(f"\n\033[92m✅ Speed increased to {final_speed} units/sec!\033[0m")
    
    def fake_team_change(self):
        """Team change with user selection"""
        print("\n\033[93m[TEAM CHANGE] Select your team:\033[0m")
        print("  [1] Mouse 🐭")
        print("  [2] Cat 🐱")
        print()
        
        choice = input("Your choice (1-2): ").strip()
        
        if choice == "1":
            new_team = "Mouse 🐭"
        elif choice == "2":
            new_team = "Cat 🐱"
        else:
            print("\n\033[91mInvalid choice! Keeping current team.\033[0m")
            return
        
        self.loading_animation("  Changing team...", 0.8)
        print(f"\033[92m✅ Team changed to: {new_team}\033[0m")
        print("\033[90m  (Change will take effect after respawn)\033[0m")
    
    def fake_auto_dodge(self):
        print("\n\033[93m[AUTO DODGE] Activating neural evasion system...\033[0m")
        self.loading_animation("  Calibrating sensors", 0.8)
        rate = random.randint(85, 98)
        print(f"\033[92m✅ Auto Dodge activated! Efficiency: {rate}%\033[0m")
    
    def fake_auto_catch(self):
        print("\n\033[93m[AUTO CATCH] Searching for nearby mice...\033[0m")
        mice = random.randint(2, 8)
        self.loading_animation(f"  Found {mice} targets", 0.5)
        eff = random.randint(75, 95)
        print(f"\033[92m✅ Auto Catch configured! Efficiency: {eff}%\033[0m")
    
    def fake_auto_win(self):
        print("\n\033[93m[AUTO WIN] Injecting server logic...\033[0m")
        self.loading_animation("  Bypassing anti-cheat", 1)
        self.loading_animation("  Manipulating results", 0.8)
        print("\n\033[95m╔════════════════════════════════════════╗")
        print("║     🏆 VICTORY GUARANTEED 🏆          ║")
        print("╚════════════════════════════════════════╝\033[0m")
    
    def fake_server_crash(self):
        print("\n\033[91m╔════════════════════════════════════════════╗")
        print("║  ⚠️  SERVER CRASH - EXPLOIT ATTEMPT  ⚠️  ║")
        print("╚════════════════════════════════════════════╝\033[0m")
        print("\n\033[93m[!] Buffer overflow attack initiated...\033[0m")
        for i in range(5):
            hex_val = random.randint(1000, 9999)
            print(f"  Packet #{i+1}: [0x{hex_val:04X}] sent ✓")
            time.sleep(0.1)
        self.loading_animation("  Desynchronizing threads", 0.8)
        print("\033[91m[!!!] WARNING! Server may become unstable!\033[0m")
        print("\033[90m  (Restart the game if you experience issues)\033[0m")
    
    def fake_fly_glitch(self):
        print("\n\033[93m[FLY GLITCH] Disabling gravity...\033[0m")
        self.loading_animation("  Finding gravity value", 0.8)
        print("\033[96m  ████████████████████████ 100%\033[0m")
        print("\033[92m✅ Gravity disabled! Flight mode activated!\033[0m")
    
    def fake_bhop(self):
        print("\n\033[93m[B-HOP] Activating auto-jump...\033[0m")
        self.loading_animation("  Calibrating timings", 0.8)
        jumps = random.randint(15, 30)
        print(f"\033[92m✅ B-Hop activated! {jumps} jumps/sec\033[0m")
    
    def toggle_module(self, module_name):
        current = self.modules[module_name]
        self.modules[module_name] = not current
        
        if self.modules[module_name]:
            print(f"\n\033[92m[+] {module_name} ACTIVATED\033[0m")
            self.fake_progress(module_name)
            
            # Special effects
            effects = {
                "ESP": self.fake_coords_scan,
                "SpeedHack": self.fake_speed_boost,
                "Team Change": self.fake_team_change,
                "Auto Dodge": self.fake_auto_dodge,
                "Auto Catch": self.fake_auto_catch,
                "Auto Win": self.fake_auto_win,
                "Server Crash": self.fake_server_crash,
                "Fly Glitch": self.fake_fly_glitch,
                "B-Hop": self.fake_bhop
            }
            if module_name in effects:
                effects[module_name]()
        else:
            print(f"\n\033[91m[-] {module_name} DISABLED\033[0m")
            self.loading_animation("  Deactivating", 0.5)
        
        input("\n\033[90mPress ENTER to continue...\033[0m")
    
    def run(self):
        try:
            while True:
                self.clear()
                self.print_ascii()
                self.print_menu()
                
                choice = input("Select option (0-9): ")
                
                actions = {
                    "1": "ESP", "2": "SpeedHack", "3": "Team Change",
                    "4": "Auto Dodge", "5": "Auto Catch", "6": "Auto Win",
                    "7": "Server Crash", "8": "Fly Glitch", "9": "B-Hop",
                    "0": None
                }
                
                if choice == "0":
                    self.clear()
                    print("\n\033[92m╔════════════════════════════════════════╗")
                    print("║     ✅ Exiting Mouse Client. Thanks!       ║")
                    print("╚════════════════════════════════════════╝\033[0m")
                    time.sleep(2)
                    break
                elif choice in actions and actions[choice] is not None:
                    self.toggle_module(actions[choice])
                else:
                    print("\n\033[91mInvalid choice! Press ENTER to continue...\033[0m")
                    input()
                    
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    # Check for admin
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        if not is_admin:
            print("\033[91m[!] Recommended to run as administrator for better experience\033[0m")
            time.sleep(1)
    except:
        pass
    
    menu = FakeModMenu()
    menu.run()