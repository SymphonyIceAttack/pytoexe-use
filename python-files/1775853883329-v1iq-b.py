import os
import sys
import time
import random
import threading

class BitcoinTerminal:
    def __init__(self):
        self.btc_balance = 0.0
        self.mining_active = False
        self.updating_active = False
    
    def set_window_size(self):
        # Установка размера окна 80x24
        if os.name == 'nt': # Windows
            os.system(f'mode con: cols=80 lines=24')
        else: # Linux/Mac
            os.system(f'printf "\033[8;24;80t"')
    
    def set_background(self):
        # Установка серого фона
        if os.name == 'nt': # Windows
            os.system('color 70') # 7=серый фон, 0=черный текст
        else: # Linux/Mac
            os.system('printf "\033[48;5;245m"') # Серый фон
            os.system('printf "\033[37m"') # Белый текст
            os.system('clear')
    
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def generate_hash(self):
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*"
        return ''.join(random.choice(chars) for _ in range(8))
    
    def mining_process(self):
        if self.mining_active:
            return
        
        self.mining_active = True
        total_time = 180
        
        
        for i in range(total_time + 1):
            if not self.mining_active:
                break
            hash_key = self.generate_hash()
            percent = int((i / total_time) * 100)
            bar_length = 30
            filled = int(bar_length * (i / total_time))
            bar = '█' * filled + '░' * (bar_length - filled)
            print(f"\r\033[33mHash:\033[0m{hash_key} \033[92m[{bar}] {percent}%\033[0m", end="", flush=True)
            time.sleep(1)
        
        if self.mining_active:
            print("\n")
            mbtc_earned = random.randint(1, 35)
            self.btc_balance += mbtc_earned / 1000.0
            print(f"\033[93mMainni: {mbtc_earned} mBTC\033[0m\n")
        
        self.mining_active = False
    
    def update_process(self):
        if self.updating_active:
            return
        
        self.updating_active = True
        total_time = 30
        
        print("\n\033[92mUPDATE\033[0m\n")
        
        for i in range(total_time + 1):
            if not self.updating_active:
                break
            percent = int((i / total_time) * 100)
            bar_length = 30
            filled = int(bar_length * (i / total_time))
            bar = '█' * filled + '░' * (bar_length - filled)
            print(f"\r\033[92mUpdate:\033[0m [{i}/{total_time}] \033[92m[{bar}] {percent}%\033[0m", end="", flush=True)
            time.sleep(1)
        
        if self.updating_active:
            print("\n\n\033[92mcomplete!\033[0m\n")
        
        self.updating_active = False
    
    def sell_btc(self):
        if self.btc_balance <= 0:
            print("\n\033[91mno BTC!\033[0m\n")
            time.sleep(1)
            return
        
        mbtc_to_sell = self.btc_balance * 1000
        earnings = random.randint(1, 500)
        
        print(f"\n\033[92msell:\033[0m {mbtc_to_sell:.2f} mBTC")
        time.sleep(1)
        print(f"\033[92mearned:\033[0m £{earnings}\n")
        
        self.btc_balance = 0
    
    def run(self):
        # Установка размера окна и фона
        self.set_window_size()
        time.sleep(0.1) # Небольшая задержка для применения размера
        self.set_background()
        self.clear_screen()
        
        # Приветственное сообщение
        print("\033[37m" + "="*80)
        print(" " * 30 + "RG&B TERMINAL")
        print("="*80 + "\033[0m")
        
        while True:
            if self.mining_active or self.updating_active:
                time.sleep(0.5)
                continue
            
            cmd = input("\033[95mmac@~$\033[0m ").strip().lower()
            
            if cmd == "btc m":
                mining_thread = threading.Thread(target=self.mining_process, daemon=True)
                mining_thread.start()
                mining_thread.join()
                
            elif cmd == "update":
                update_thread = threading.Thread(target=self.update_process, daemon=True)
                update_thread.start()
                update_thread.join()
                
            elif cmd == "sbtc":
                self.sell_btc()
                
            elif cmd in ["exit", "quit"]:
                # Сброс цвета перед выходом
                if os.name != 'nt':
                    os.system('printf "\033[0m"')
                print("\n")
                sys.exit(0)

if __name__ == "__main__":
    try:
        terminal = BitcoinTerminal()
        terminal.run()
    except KeyboardInterrupt:
        if os.name != 'nt':
            os.system('printf "\033[0m"')
        print("\n")
        sys.exit(0)

