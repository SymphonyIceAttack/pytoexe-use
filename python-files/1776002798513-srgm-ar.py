import os
import sys
import time
import random
import threading
import subprocess

class BitcoinTerminal:
    def __init__(self):
        self.rub_balance = 0.0
        self.mining_active = False
        self.installing_active = False
    
    def create_window(self):
        script_path = os.path.abspath(__file__)
        
        if os.name == 'nt': # Windows
            subprocess.Popen(f'start cmd /c "mode con: cols=50 lines=19 && python {script_path}"', shell=True)
            sys.exit(0)
        else: # Linux/Mac
            terminals = [
                ['gnome-terminal', '--geometry=50x19', '--', 'python3', script_path],
                ['xterm', '-geometry', '50x19', '-e', 'python3', script_path],
                ['konsole', '--geometry', '50x19', '-e', 'python3', script_path],
                ['xfce4-terminal', '--geometry', '50x19', '-e', 'python3', script_path]
            ]
            
            for terminal in terminals:
                try:
                    subprocess.Popen(terminal)
                    sys.exit(0)
                except FileNotFoundError:
                    continue
            
            self.set_window_size()
    
    def set_window_size(self):
        if os.name == 'nt':
            os.system('mode con: cols=50 lines=19')
        else:
            os.system('printf "\033[8;19;50t"')
    
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def install_process(self):
        if self.installing_active:
            return
        
        self.installing_active = True
        total_time = 60 # 1 минута
        
        for i in range(total_time + 1):
            if not self.installing_active:
                break
            percent = int((i / total_time) * 100)
            bar_length = 30
            filled = int(bar_length * (i / total_time))
            bar = '█' * filled + '░' * (bar_length - filled)
            print(f"\r\033[37m[{bar}] {percent}%\033[0m", end="", flush=True)
            time.sleep(1)
        
        if self.installing_active:
            print("\n\n\033[92mГотово!\033[0m\n")
        
        self.installing_active = False
    
    def mining_process(self):
        if self.mining_active:
            return
        
        self.mining_active = True
        total_time = 120 # 2 минуты
        
        for i in range(total_time + 1):
            if not self.mining_active:
                break
            percent = int((i / total_time) * 100)
            bar_length = 30
            filled = int(bar_length * (i / total_time))
            bar = '█' * filled + '░' * (bar_length - filled)
            print(f"\r\033[37m[{bar}] {percent}%\033[0m", end="", flush=True)
            time.sleep(1)
        
        if self.mining_active:
            print("\n")
            rub_earned = random.randint(50, 500)
            self.rub_balance += rub_earned
            print(f"\033[92mДобыто: {rub_earned} RUB\033[0m\n")
        
        self.mining_active = False
    
    def run(self):
        if len(sys.argv) == 1 or sys.argv[1] != '--window-created':
            self.create_window()
            return
        
        self.set_window_size()
        self.clear_screen()
        
        while True:
            if self.mining_active or self.installing_active:
                time.sleep(0.5)
                continue
            
            cmd = input("\033[94march@~$\033[0m ").strip().lower()
            
            if cmd == "pkg":
                install_thread = threading.Thread(target=self.install_process, daemon=True)
                install_thread.start()
                install_thread.join()
                
            elif cmd == "apt":
                mining_thread = threading.Thread(target=self.mining_process, daemon=True)
                mining_thread.start()
                mining_thread.join()
                
            elif cmd in ["exit", "quit"]:
                print("\n")
                sys.exit(0)

if __name__ == "__main__":
    try:
        terminal = BitcoinTerminal()
        terminal.run()
    except KeyboardInterrupt:
        print("\n")
        sys.exit(0)

