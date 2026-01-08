"""
FISHIT PY - Terminal Fishing Idle Game
Main Entry Point
"""

import os
import sys
import time
from game.ui import UI
from game.player import Player
from game.fishing import FishingSystem
from game.shop import Shop
from game.save import SaveSystem

class Game:
    def __init__(self):
        self.ui = UI()
        self.save_system = SaveSystem()
        self.player = None
        self.fishing = None
        self.shop = None
        self.running = True
        self.auto_fishing_active = False
        
    def start(self):
        """Initialize game"""
        self.ui.clear_screen()
        self.ui.show_title()
        
        # Load or create new game
        if self.save_system.save_exists():
            options = ["Continue", "New Game"]
            choice = self.ui.show_menu("GAME START", options, show_header_text=False)
            
            if choice is None:
                return
            elif choice == 0:
                self.load_game()
            else:
                self.new_game()
        else:
            self.new_game()
        
        self.fishing = FishingSystem(self.player)
        self.shop = Shop(self.player)
        
        self.main_loop()
    
    def new_game(self):
        """Create new player"""
        self.ui.clear_screen()
        name = input(f"{self.ui.CYAN}Enter your fisher name: {self.ui.RESET}")
        self.player = Player(name)
        self.ui.print_success(f"Welcome, {name}!")
        time.sleep(1)
    
    def load_game(self):
        """Load saved game"""
        self.player = self.save_system.load()
        if self.player:
            self.ui.print_success(f"Welcome back, {self.player.name}!")
            time.sleep(1)
        else:
            self.ui.print_error("Failed to load. Starting new game.")
            self.new_game()
    
    def main_loop(self):
        """Main game loop"""
        while self.running:
            choice = self.show_main_menu()
            
            if choice is None:
                continue
            elif choice == 0:
                self.fishing_action()
            elif choice == 1:
                self.auto_fishing_mode()
            elif choice == 2:
                self.shop_menu()
            elif choice == 3:
                self.show_collection()
            elif choice == 4:
                self.show_stats()
            elif choice == 5:
                self.save_and_exit()
    
    def show_main_menu(self):
        """Display main menu with arrow navigation"""
        self.ui.clear_screen()
        self.ui.show_header("MAIN MENU")
        
        print(f"\n{self.ui.YELLOW}Fisher: {self.player.name}{self.ui.RESET}")
        print(f"{self.ui.YELLOW}Level: {self.player.level} | Gold: {self.player.gold}g{self.ui.RESET}")
        print(f"{self.ui.CYAN}Area: {self.player.current_area}{self.ui.RESET}")
        print(f"{self.ui.MAGENTA}Bait: {self.player.bait_equipped} ({self.player.get_bait_count()}){self.ui.RESET}")
        
        options = [
            "🎣 Cast Once",
            "🔄 Auto Fishing",
            "🏪 Shop & Upgrades",
            "📖 Fish Collection",
            "📊 Stats & Achievements",
            "💾 Save & Exit"
        ]
        
        return self.ui.show_menu("", options, show_header_text=False)
    
    def fishing_action(self):
        """Execute single fishing action"""
        self.ui.clear_screen()
        self.ui.show_header("FISHING")
        
        # Check bait
        if not self.player.has_bait():
            self.ui.print_error(f"No {self.player.bait_equipped} left! Buy more bait from the shop.")
            input(f"\n{self.ui.CYAN}Press Enter to continue...{self.ui.RESET}")
            return
        
        # Use bait
        self.player.use_bait()
        
        result = self.fishing.cast()
        
        # Animate casting
        self.ui.animate_typing("Casting line", dots=3)
        time.sleep(0.8)
        self.ui.animate_typing("Waiting", dots=3)
        time.sleep(result['wait_time'])
        
        # Reveal catch
        print(f"\n{self.ui.GREEN}!! You got something !!{self.ui.RESET}\n")
        time.sleep(0.5)
        
        fish = result['fish']
        self.ui.show_fish_catch(fish)
        
        # Update player
        self.player.add_fish(fish)
        self.player.add_gold(result['gold'])
        self.player.add_exp(result['exp'])
        
        # Check level up
        if self.player.check_level_up():
            self.ui.show_level_up(self.player.level)
        
        # Auto save
        self.save_system.save(self.player)
        
        input(f"\n{self.ui.CYAN}Press Enter to continue...{self.ui.RESET}")
    
    def auto_fishing_mode(self):
        """Auto fishing mode - continuous fishing"""
        self.ui.clear_screen()
        self.ui.show_header("AUTO FISHING MODE")
        
        if not self.player.has_bait():
            self.ui.print_error(f"No {self.player.bait_equipped} left! Buy more bait from the shop.")
            input(f"\n{self.ui.CYAN}Press Enter to continue...{self.ui.RESET}")
            return
        
        print(f"\n{self.ui.YELLOW}Auto fishing will continue until bait runs out.{self.ui.RESET}")
        print(f"{self.ui.YELLOW}Press Ctrl+C to stop at any time.{self.ui.RESET}\n")
        
        input(f"{self.ui.CYAN}Press Enter to start auto fishing...{self.ui.RESET}")
        
        self.auto_fishing_active = True
        fish_caught = 0
        total_gold = 0
        total_exp = 0
        
        legendary_count = 0
        mythic_count = 0
        
        try:
            while self.auto_fishing_active:
                # Check bait
                if not self.player.has_bait():
                    self.ui.clear_screen()
                    print(f"\n{self.ui.RED}Out of {self.player.bait_equipped}!{self.ui.RESET}")
                    print(f"\n{self.ui.YELLOW}Auto Fishing Summary:{self.ui.RESET}")
                    print(f"  Fish Caught: {fish_caught}")
                    print(f"  Gold Earned: {total_gold}g")
                    print(f"  EXP Gained: {total_exp}")
                    if legendary_count > 0:
                        print(f"  {self.ui.YELLOW}Legendary: {legendary_count}{self.ui.RESET}")
                    if mythic_count > 0:
                        print(f"  {self.ui.RED}Mythic: {mythic_count}{self.ui.RESET}")
                    break
                
                # Use bait
                self.player.use_bait()
                
                # Cast
                result = self.fishing.cast()
                fish = result['fish']
                
                # Update counters
                fish_caught += 1
                total_gold += result['gold']
                total_exp += result['exp']
                
                if fish['rarity'] == 'Legendary':
                    legendary_count += 1
                elif fish['rarity'] == 'Mythic':
                    mythic_count += 1
                
                # Update player
                self.player.add_fish(fish)
                self.player.add_gold(result['gold'])
                self.player.add_exp(result['exp'])
                
                # Check level up
                level_up = self.player.check_level_up()
                
                # Display compact info
                self.ui.clear_screen()
                self.ui.show_header("AUTO FISHING ACTIVE")
                
                print(f"\n{self.ui.CYAN}Bait: {self.player.bait_equipped} ({self.player.get_bait_count()} left){self.ui.RESET}")
                print(f"{self.ui.YELLOW}Level: {self.player.level} | Gold: {self.player.gold}g{self.ui.RESET}\n")
                
                # Show last catch with color
                color = self.ui.get_rarity_color(fish['rarity'])
                print(f"{color}Caught: {fish['name']} [{fish['rarity']}] +{result['gold']}g{self.ui.RESET}")
                
                # Show summary
                print(f"\n{self.ui.CYAN}Session Stats:{self.ui.RESET}")
                print(f"  Total Caught: {fish_caught}")
                print(f"  Gold Earned: {total_gold}g")
                print(f"  EXP Gained: {total_exp}")
                if legendary_count > 0:
                    print(f"  {self.ui.YELLOW}Legendary: {legendary_count}{self.ui.RESET}")
                if mythic_count > 0:
                    print(f"  {self.ui.RED}Mythic: {mythic_count}{self.ui.RESET}")
                
                if level_up:
                    print(f"\n{self.ui.YELLOW}✨ LEVEL UP! Now level {self.player.level}! ✨{self.ui.RESET}")
                
                print(f"\n{self.ui.RED}Press Ctrl+C to stop{self.ui.RESET}")
                
                # Wait based on fishing speed
                wait_time = result['wait_time']
                time.sleep(wait_time)
                
                # Auto save every 10 fish
                if fish_caught % 10 == 0:
                    self.save_system.save(self.player)
        
        except KeyboardInterrupt:
            self.ui.clear_screen()
            print(f"\n{self.ui.YELLOW}Auto fishing stopped!{self.ui.RESET}")
            print(f"\n{self.ui.CYAN}Session Summary:{self.ui.RESET}")
            print(f"  Fish Caught: {fish_caught}")
            print(f"  Gold Earned: {total_gold}g")
            print(f"  EXP Gained: {total_exp}")
            if legendary_count > 0:
                print(f"  {self.ui.YELLOW}Legendary: {legendary_count}{self.ui.RESET}")
            if mythic_count > 0:
                print(f"  {self.ui.RED}Mythic: {mythic_count}{self.ui.RESET}")
        
        finally:
            self.auto_fishing_active = False
            # Final save
            self.save_system.save(self.player)
            input(f"\n{self.ui.CYAN}Press Enter to continue...{self.ui.RESET}")
    
    def shop_menu(self):
        """Shop menu with arrow navigation"""
        while True:
            self.ui.clear_screen()
            self.ui.show_header("SHOP & UPGRADES")
            
            print(f"\n{self.ui.YELLOW}Gold: {self.player.gold}g{self.ui.RESET}")
            print(f"{self.ui.YELLOW}Level: {self.player.level}{self.ui.RESET}")
            
            options = [
                "🎣 Fishing Rods",
                "🪱 Buy Baits",
                "⚙️  Reels",
                "🍀 Luck Charms",
                "🗺️  Unlock Areas",
                "📍 Change Fishing Area",
                "💼 Manage Baits",
                "⬅️  Back to Main Menu"
            ]
            
            choice = self.ui.show_menu("", options, show_header_text=False)
            
            if choice is None or choice == 7:
                break
            elif choice == 0:
                self.shop.show_rods()
            elif choice == 1:
                self.shop.show_bait_shop()
            elif choice == 2:
                self.shop.show_reels()
            elif choice == 3:
                self.shop.show_charms()
            elif choice == 4:
                self.shop.show_areas_shop()
            elif choice == 5:
                self.shop.change_area()
            elif choice == 6:
                self.shop.manage_baits()
    
    def show_collection(self):
        """Show fish collection"""
        self.ui.clear_screen()
        self.ui.show_header("FISH COLLECTION")
        
        if not self.player.collection:
            print(f"\n{self.ui.YELLOW}No fish caught yet!{self.ui.RESET}")
        else:
            for fish_name, data in sorted(self.player.collection.items()):
                rarity = data['rarity']
                count = data['count']
                color = self.ui.get_rarity_color(rarity)
                print(f"{color}• {fish_name}{self.ui.RESET} [{rarity}] x{count}")
        
        print(f"\n{self.ui.CYAN}Total Species: {len(self.player.collection)}{self.ui.RESET}")
        print(f"{self.ui.CYAN}Total Fish Caught: {self.player.total_fish}{self.ui.RESET}")
        
        input(f"\n{self.ui.CYAN}Press Enter to continue...{self.ui.RESET}")
    
    def show_stats(self):
        """Show player stats"""
        self.ui.clear_screen()
        self.ui.show_header("PLAYER STATS")
        
        print(f"\n{self.ui.YELLOW}Name:{self.ui.RESET} {self.player.name}")
        print(f"{self.ui.YELLOW}Level:{self.ui.RESET} {self.player.level}")
        print(f"{self.ui.YELLOW}EXP:{self.ui.RESET} {self.player.exp}/{self.player.exp_needed}")
        print(f"{self.ui.YELLOW}Gold:{self.ui.RESET} {self.player.gold}g")
        print(f"{self.ui.YELLOW}Total Fish:{self.ui.RESET} {self.player.total_fish}")
        print(f"{self.ui.YELLOW}Current Area:{self.ui.RESET} {self.player.current_area}")
        print(f"{self.ui.YELLOW}Current Rod:{self.ui.RESET} {self.player.rod}")
        print(f"{self.ui.YELLOW}Current Bait:{self.ui.RESET} {self.player.bait_equipped} ({self.player.get_bait_count()})")
        print(f"{self.ui.YELLOW}Total Luck:{self.ui.RESET} {self.player.get_total_luck():.2f}x")
        
        print(f"\n{self.ui.CYAN}--- ACHIEVEMENTS ---{self.ui.RESET}")
        if self.player.achievements:
            for ach in self.player.achievements:
                print(f"{self.ui.GREEN}✓{self.ui.RESET} {ach}")
        else:
            print(f"{self.ui.YELLOW}No achievements yet!{self.ui.RESET}")
        
        input(f"\n{self.ui.CYAN}Press Enter to continue...{self.ui.RESET}")
    
    def save_and_exit(self):
        """Save and exit game"""
        self.ui.clear_screen()
        self.ui.show_loading("Saving game", duration=1)
        self.save_system.save(self.player)
        self.ui.print_success("Game saved!")
        print(f"\n{self.ui.YELLOW}Thanks for playing FISHIT PY!{self.ui.RESET}")
        time.sleep(2)
        self.running = False

if __name__ == "__main__":
    game = Game()
    try:
        game.start()
    except KeyboardInterrupt:
        print("\n\nGame interrupted. Saving...")
        if game.player:
            game.save_system.save(game.player)
        print("Goodbye!")