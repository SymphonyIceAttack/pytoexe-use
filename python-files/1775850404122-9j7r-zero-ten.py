import random
import os
import sys
import time

from colorama import init, Fore, Back, Style
init(autoreset=True)

# Моя цветовая схема
class Colors:
    GOLD = Fore.LIGHTYELLOW_EX
    CYAN = Fore.LIGHTCYAN_EX
    PURPLE = Fore.LIGHTMAGENTA_EX
    GREEN = Fore.LIGHTGREEN_EX
    RED = Fore.LIGHTRED_EX
    BLUE = Fore.LIGHTBLUE_EX
    WHITE = Fore.WHITE
    BG_DARK = Back.BLACK
    BOLD = Style.BRIGHT
    RESET = Style.RESET_ALL

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    clear_screen()
    print(f"{Colors.BG_DARK}{Colors.GOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BG_DARK}{Colors.GOLD}        🎲 {Colors.CYAN}УГАДАЙ ЧИСЛО {Colors.PURPLE}0-10{Colors.GOLD} 🎲{Colors.RESET}")
    print(f"{Colors.BG_DARK}{Colors.GOLD}{'='*60}{Colors.RESET}\n")

def animate_dots():
    for i in range(3):
        print(f"{Colors.CYAN}Загадываю число{'.' * (i+1)}{Colors.RESET}", end='\r')
        time.sleep(0.3)
    print(f"{Colors.GREEN}Число загадано!     {Colors.RESET}")

def print_stat_bar(current, total, width=40):
    filled = int(width * current / total)
    bar = f"{Colors.GREEN}{'█' * filled}{Colors.RED}{'░' * (width - filled)}{Colors.RESET}"
    print(f"{Colors.CYAN}Попытки: {bar} {current}/{total}{Colors.RESET}")

def get_hint(guess, secret):
    """Даёт подсказку с температурой"""
    diff = abs(guess - secret)
    if diff == 0:
        return f"{Colors.GREEN}🎯 ТОЧНО В ЦЕЛЬ!{Colors.RESET}"
    elif diff <= 2:
        return f"{Colors.GREEN}🔥 ГОРЯЧО! Очень близко!{Colors.RESET}"
    elif diff <= 4:
        return f"{Colors.CYAN}🌡️ ТЕПЛО! Уже рядом{Colors.RESET}"
    elif diff <= 7:
        return f"{Colors.BLUE}❄️ ХОЛОДНО! Далековато{Colors.RESET}"
    else:
        return f"{Colors.PURPLE}🧊 ЛЕДЯНОЙ ХОЛОД! Очень далеко{Colors.RESET}"

def play_game():
    print_header()
    
    print(f"{Colors.PURPLE}⭐ {Colors.WHITE}Компьютер загадал число от 0 до 10{Colors.PURPLE} ⭐{Colors.RESET}")
    print(f"{Colors.GOLD}🎯 {Colors.WHITE}У тебя 5 попыток{Colors.GOLD} 🎯{Colors.RESET}")
    print(f"{Colors.CYAN}💡 {Colors.WHITE}Я буду давать цветные подсказки{Colors.CYAN} 💡{Colors.RESET}\n")
    
    animate_dots()
    time.sleep(0.5)
    
    secret_number = random.randint(0, 10)
    attempts = 0
    max_attempts = 5
    
    while attempts < max_attempts:
        print(f"\n{Colors.BLUE}{'─'*60}{Colors.RESET}")
        print_stat_bar(attempts, max_attempts)
        
        try:
            print(f"\n{Colors.GOLD}Попытка {attempts + 1}/{max_attempts}{Colors.RESET}")
            guess = input(f"{Colors.CYAN}➜ Введи число от 0 до 10: {Colors.RESET}")
            guess = int(guess)
            
            if guess < 0 or guess > 10:
                print(f"{Colors.RED}❌ Ошибка! Только числа от 0 до 10!{Colors.RESET}")
                continue
            
            attempts += 1
            
            if guess == secret_number:
                # ПОБЕДА
                print(f"\n{Colors.GREEN}{'='*60}{Colors.RESET}")
                print(f"{Colors.GREEN}{Colors.BOLD}🎉 ПОЗДРАВЛЯЮ! ТЫ УГАДАЛ! 🎉{Colors.RESET}")
                print(f"{Colors.GOLD}✨ Загаданное число: {Colors.CYAN}{Colors.BOLD}{secret_number}{Colors.RESET}")
                print(f"{Colors.PURPLE}📊 Попыток использовано: {attempts}{Colors.RESET}")
                
                if attempts == 1:
                    print(f"{Colors.GOLD}🏆 НЕВЕРОЯТНО! С ПЕРВОЙ ПОПЫТКИ! 🏆{Colors.RESET}")
                elif attempts == 2:
                    print(f"{Colors.GREEN}🌟 БЛЕСТЯЩЕ!{Colors.RESET}")
                elif attempts == 3:
                    print(f"{Colors.CYAN}👍 ОТЛИЧНО!{Colors.RESET}")
                elif attempts == 4:
                    print(f"{Colors.PURPLE}😅 НУ БЫЛО БЛИЗКО!{Colors.RESET}")
                else:
                    print(f"{Colors.GOLD}🤔 В ПОСЛЕДНЮЮ СЕКУНДУ!{Colors.RESET}")
                
                print(f"{Colors.GREEN}{'='*60}{Colors.RESET}")
                return True
            else:
                # ПОДСКАЗКА
                if guess < secret_number:
                    print(f"\n{Colors.CYAN}📈 Загаданное число {Colors.GOLD}БОЛЬШЕ{Colors.RESET} {Colors.CYAN}чем {guess}{Colors.RESET}")
                else:
                    print(f"\n{Colors.PURPLE}📉 Загаданное число {Colors.GOLD}МЕНЬШЕ{Colors.RESET} {Colors.PURPLE}чем {guess}{Colors.RESET}")
                
                # Температурная подсказка
                print(get_hint(guess, secret_number))
                
                remaining = max_attempts - attempts
                if remaining > 0:
                    print(f"{Colors.BLUE}💪 Осталось попыток: {Colors.GOLD}{remaining}{Colors.RESET}")
                    
        except ValueError:
            print(f"{Colors.RED}❌ Ошибка! Введи целое число!{Colors.RESET}")
    
    # ПРОИГРЫШ
    print(f"\n{Colors.RED}{'='*60}{Colors.RESET}")
    print(f"{Colors.RED}{Colors.BOLD}😔 ИГРА ОКОНЧЕНА... ТЫ НЕ УГАДАЛ 😔{Colors.RESET}")
    print(f"{Colors.GOLD}🔢 Загаданное число: {Colors.CYAN}{Colors.BOLD}{secret_number}{Colors.RESET}")
    
    print(f"\n{Colors.PURPLE}💡 Вот все числа от 0 до 10:{Colors.RESET} ", end='')
    for i in range(11):
        if i == secret_number:
            print(f"{Colors.GREEN}[{i}]{Colors.RESET} ", end='')
        else:
            print(f"{Colors.RED}[{i}]{Colors.RESET} ", end='')
    print(f"\n{Colors.RED}{'='*60}{Colors.RESET}")
    return False

def main():
    wins = 0
    losses = 0
    
    while True:
        result = play_game()
        
        if result:
            wins += 1
        else:
            losses += 1
        
        # СТАТИСТИКА
        print(f"\n{Colors.BLUE}{'─'*60}{Colors.RESET}")
        print(f"{Colors.GOLD}{Colors.BOLD}📊 СТАТИСТИКА{Colors.RESET}")
        print(f"{Colors.GREEN}  🏆 Побед: {wins}{Colors.RESET}")
        print(f"{Colors.RED}  💀 Поражений: {losses}{Colors.RESET}")
        
        total = wins + losses
        if total > 0:
            winrate = (wins / total) * 100
            if winrate >= 70:
                color = Colors.GREEN
                medal = "🏅 ОТЛИЧНО!"
            elif winrate >= 40:
                color = Colors.GOLD
                medal = "👍 НОРМАЛЬНО"
            else:
                color = Colors.RED
                medal = "😅 НУЖНО БОЛЬШЕ ТРЕНИРОВАТЬСЯ"
            
            print(f"{color}  📈 Процент побед: {winrate:.1f}% {medal}{Colors.RESET}")
        
        print(f"{Colors.PURPLE}  🎮 Всего игр: {total}{Colors.RESET}")
        print(f"{Colors.BLUE}{'─'*60}{Colors.RESET}")
        
        # ПОВТОР
        print(f"\n{Colors.GOLD}🔄 Хочешь сыграть еще?{Colors.RESET}")
        choice = input(f"{Colors.CYAN}➜ {Colors.GREEN}да{Colors.RESET}/{Colors.RED}нет{Colors.RESET}: ").lower()
        
        if choice not in ['да', 'lf', 'yes', 'y', 'д', '+', '1', 'конечно', 'ага']:
            print(f"\n{Colors.PURPLE}{Colors.BOLD}👋 СПАСИБО ЗА ИГРУ! ДО ВСТРЕЧИ! 👋{Colors.RESET}")
            print(f"{Colors.GOLD}🎮 Финальная статистика: {Colors.GREEN}{wins}{Colors.RESET} побед, {Colors.RED}{losses}{Colors.RESET} поражений")
            
            if total > 0:
                final_rate = (wins / total) * 100
                if final_rate == 100:
                    print(f"{Colors.GOLD}🏆 ИДЕАЛЬНАЯ ИГРА! ТЫ МАСТЕР! 🏆{Colors.RESET}")
                elif final_rate >= 80:
                    print(f"{Colors.GREEN}🌟 ТЫ ПРОФИ! 🌟{Colors.RESET}")
                elif final_rate >= 60:
                    print(f"{Colors.CYAN}👍 ХОРОШАЯ ИГРА!{Colors.RESET}")
                elif final_rate >= 40:
                    print(f"{Colors.PURPLE}🤔 НЕПЛОХО, НО МОЖНО ЛУЧШЕ{Colors.RESET}")
                else:
                    print(f"{Colors.RED}💪 В СЛЕДУЮЩИЙ РАЗ ПОЛУЧИТСЯ!{Colors.RESET}")
            break
        
        clear_screen()

if __name__ == "__main__":
    try:
        if sys.platform == "win32":
            os.system('chcp 65001 > nul')
            os.system('title УГАДАЙ ЧИСЛО 0-10 - 5 ПОПЫТОК')
        
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.GOLD}👋 Пока! Заходи еще!{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}Ошибка: {e}{Colors.RESET}")
        input("Нажми Enter...")