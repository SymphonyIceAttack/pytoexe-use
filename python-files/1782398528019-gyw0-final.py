#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import json
import time
import socket
import logging
import threading
import warnings
import multiprocessing
import queue
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- CRITICAL DEPENDENCY VERIFICATION ---
try:
    import requests
    from tqdm import tqdm
except ImportError:
    print("\n[❌] Error: Missing dependencies. Run: pip install requests tqdm\n")
    sys.exit(1)

# Disable unverified SSL warnings
warnings.filterwarnings("ignore")

# =====================================================================
#                      GLOBAL CONFIGURATION AND VARIABLES
# =====================================================================
class Config:
    # Output Directories
    BASE_DIRECTORY = "Results"
    COUNTRIES_FOLDER = os.path.join(BASE_DIRECTORY, "classified_countries")
    LOG_FILE = os.path.join(BASE_DIRECTORY, "system_audit.log")
    
    # Telegram Bot Settings
    TELEGRAM_ACTIVE = True
    TELEGRAM_TOKEN = ""
    TELEGRAM_CHAT_ID = ""
    
    # Dynamic Execution Parameters
    SEARCH_PATTERN = "DVR"
    TARGET_FOLDER = ""
    
    # Communication queue between threads and TUI loop
    TUI_QUEUE = None
    
    # Network Configurations
    NETWORK_TIMEOUT = 3.0
    MAX_NETWORK_THREADS = 60
    CONNECTION_POOL = 100
    
    # Regular Expression for strict IPv4 capture
    IP_REGEX = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'

# --- ANSI COLORS FOR TECHNICAL CONSOLE ---
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    GRAY = "\033[90m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

# =====================================================================
#                      LOGGING SYSTEM AND BANNER
# =====================================================================
def set_window_title(title):
    """ IP CAM FUCKER 1.0v  |  cracked.st/nontop """
    if os.name == 'nt':
        import ctypes
        try:
            ctypes.windll.kernel32.SetConsoleTitleW(title)
        except:
            os.system(f'title {title}')
    else:
        sys.stdout.write(f"\x1b]2;{title}\x07")
        sys.stdout.flush()

def initialize_environment():
    if not os.path.exists(Config.BASE_DIRECTORY):
        os.makedirs(Config.BASE_DIRECTORY)
    if not os.path.exists(Config.COUNTRIES_FOLDER):
        os.makedirs(Config.COUNTRIES_FOLDER)
        
    logging.basicConfig(
        filename=Config.LOG_FILE,
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    os.system('') # Enable ANSI support on Windows terminals

def show_banner():
    banner = f"""
{Colors.CYAN}{Colors.BOLD}  ██████╗ ██████╗████████╗██╗   ██╗    ███╗   ███╗ █████╗ ██████╗████████╗███████╗██████╗ 
 ██╔════╝██╔════╝╚══██╔══╝██║   ██║    ████╗ ████║██╔══██╗██╔══██╗╚══██╔══╝██╔════╝██╔══██╗
 ██║     ██║        ██║   ██║   ██║    ██╔████╔██║███████║██████╔╝   ██║   █████╗  ██████╔╝
 ██║     ██║        ██║   ╚██╗ ██╔╝    ██║╚██╔╝██║██╔══██║██╔══██╗   ██║   ██╔══╝  ██╔══██╗
 ╚██████╗╚██████╗   ██║    ╚████╔╝     ██║ ╚═╝ ██║██║  ██║██║  ██║   ██║   ███████╗██║  ██║
  ╚═════╝ ╚═════╝   ╚═╝     ╚═══╝      ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝
                    {Colors.YELLOW}--- INTEGRATED AUDIT FRAMEWORK V4.5 (TUI) ---{Colors.RESET}
    """
    print(banner)

def get_flag_emoji(country_code):
    """ Converts country initials (e.g., US) into its respective Flag Emoji """
    if not country_code or len(country_code) != 2:
        return "🏳️"
    try:
        return "".join(chr(127462 + ord(c) - 65) for c in country_code.upper())
    except:
        return "🏳️"

# =====================================================================
#                  NOTIFICATION MODULE (TELEGRAM)
# =====================================================================
class TelegramNotifier:
    def __init__(self):
        self.token = Config.TELEGRAM_TOKEN
        self.chat_id = Config.TELEGRAM_CHAT_ID
        self.active = Config.TELEGRAM_ACTIVE

    def send_message(self, text):
        if not self.active or not self.token or not self.chat_id:
            return False
        try:
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "HTML"
            }
            response = requests.post(url, json=payload, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logging.error(f"Error sending message to Telegram: {str(e)}")
            return False

    def send_document(self, file_path, description=""):
        if not self.active or not os.path.exists(file_path) or not self.token or not self.chat_id:
            return False
        try:
            url = f"https://api.telegram.org/bot{self.token}/sendDocument"
            data = {"chat_id": self.chat_id, "caption": description}
            with open(file_path, 'rb') as doc:
                files = {'document': doc}
                response = requests.post(url, data=data, files=files, timeout=15)
            return response.status_code == 200
        except Exception as e:
            logging.error(f"Error sending document to Telegram: {str(e)}")
            return False

# =====================================================================
#             LOCAL PROCESSING MODULE (MULTIPROCESSING)
# =====================================================================
def process_single_file(args):
    full_path, search_pattern = args
    local_results = set()
    try:
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if search_pattern.lower() in line.lower():
                    match = re.search(Config.IP_REGEX, line)
                    if match:
                        local_results.add((match.group(0), line.strip()))
    except Exception as e:
        logging.error(f"Error reading file {full_path}: {str(e)}")
    return list(local_results)


class ScoutEngine:
    def __init__(self, pattern):
        self.pattern = pattern
        self.extracted_targets = {}

    def run_local_scan(self, directory_path):
        if not directory_path or not os.path.isdir(directory_path):
            return False

        file_list = []
        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.endswith(('.txt', '.log')):
                    file_list.append(os.path.join(root, file))

        total_files = len(file_list)
        if total_files == 0:
            return False

        if Config.TUI_QUEUE:
            Config.TUI_QUEUE.put(("TOTAL_PROGRESS", total_files))

        tasks = [(path, self.pattern) for path in file_list]
        
        with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
            for idx, result in enumerate(pool.imap_unordered(process_single_file, tasks)):
                if Config.TUI_QUEUE and idx % 5 == 0:
                    Config.TUI_QUEUE.put(("SET_PROGRESS", idx))
                for ip, full_line in result:
                    if ip not in self.extracted_targets:
                        self.extracted_targets[ip] = full_line

        return len(self.extracted_targets) > 0

# =====================================================================
#             NETWORK INTEL MODULE (SHODAN & GEO-IP)
# =====================================================================
class NetworkIntelEngine:
    def __init__(self):
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=Config.CONNECTION_POOL, 
            pool_maxsize=Config.CONNECTION_POOL
        )
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)
        self.file_lock = threading.Lock()
        self.geo_cache = {}

    def query_shodan_db(self, ip):
        url = f"https://internetdb.shodan.io/{ip}"
        try:
            response = self.session.get(url, timeout=Config.NETWORK_TIMEOUT)
            if response.status_code == 200:
                data = response.json()
                return {
                    "ports": data.get("ports", []),
                    "vulnerabilities": data.get("vulns", []),
                    "tags": data.get("tags", [])
                }
        except:
            pass
        return None

    def get_geolocation(self, ip):
        if ip in self.geo_cache:
            return self.geo_cache[ip]

        url = f"http://ip-api.com/json/{ip}?fields=status,country,countryCode,isp,lat,lon"
        default_result = {"country": "Unknown", "countryCode": "UN", "isp": "Unknown", "lat": 0.0, "lon": 0.0}
        try:
            response = self.session.get(url, timeout=Config.NETWORK_TIMEOUT)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    res = {
                        "country": data.get("country", "Unknown"),
                        "countryCode": data.get("countryCode", "UN"),
                        "isp": data.get("isp", "Unknown"),
                        "lat": data.get("lat", 0.0),
                        "lon": data.get("lon", 0.0)
                    }
                    self.geo_cache[ip] = res
                    return res
        except:
            pass
        return default_result

    def evaluate_host(self, ip, original_line):
        shodan_data = self.query_shodan_db(ip)
        if not shodan_data:
            return None
            
        geo_data = self.get_geolocation(ip)
        return {
            "ip": ip,
            "line": original_line,
            "shodan": shodan_data,
            "geo": geo_data
        }

    def process_network_batch(self, targets_dict):
        valid_results = []
        item_list = list(targets_dict.items())
        
        if Config.TUI_QUEUE:
            Config.TUI_QUEUE.put(("TOTAL_PROGRESS", len(item_list)))
        
        with ThreadPoolExecutor(max_workers=Config.MAX_NETWORK_THREADS) as executor:
            futures = {executor.submit(self.evaluate_host, ip, line): ip for ip, line in item_list}
            
            for idx, fut in enumerate(as_completed(futures)):
                result = fut.result()
                if Config.TUI_QUEUE:
                    Config.TUI_QUEUE.put(("SET_PROGRESS", idx + 1))
                if result:
                    valid_results.append(result)
                    
        # --- ORDENAR LOS RESULTADOS AL FINALIZAR EL FILTRADO ASÍNCRONO ---
        def ip_sort_key(item):
            try:
                return tuple(map(int, item['ip'].split('.')))
            except:
                return (0, 0, 0, 0)
        
        valid_results.sort(key=ip_sort_key)
        
        # Enviar los resultados ya ordenados al guardado y al feed de Telegram/Consola
        for sorted_result in valid_results:
            self.save_by_country(sorted_result)
            if Config.TUI_QUEUE:
                Config.TUI_QUEUE.put(("RESULT", sorted_result))
                    
        return valid_results

    def save_by_country(self, element):
        """ Local file writer using the exact layout requested """
        clean_country = re.sub(r'[^\w]', '_', element['geo']['country']).strip()
        file_name = os.path.join(Config.COUNTRIES_FOLDER, f"{clean_country}.txt")
        
        vulns_list = element['shodan'].get('vulnerabilities', [])
        vulns_str = ", ".join(vulns_list) if vulns_list else "No"
        ports_str = ", ".join(map(str, element['shodan']['ports']))
        date_str = datetime.now().strftime("%d/%m/%Y")
        country_code = element['geo'].get('countryCode', 'UN').upper()
        
        save_text = (
            f"| IP: {element['ip']}\n"
            f"| VULN: {vulns_str}\n"
            f"| ISP: {element['geo']['isp']}\n"
            f"| OPEN PORTS: {ports_str}\n"
            f"| LOG:  {element['line']}\n"
            f"| COUNTRY:{country_code}\n"
            f"| DATE: {date_str}\n"
            f"{'-'*40}\n"
        )
        
        with self.file_lock:
            try:
                with open(file_name, "a", encoding="utf-8") as f:
                    f.write(save_text)
            except Exception as e:
                logging.error(f"Error writing to country file {file_name}: {str(e)}")

# =====================================================================
#                 EXPORT AND REPORTING MODULE
# =====================================================================
class ReportGenerator:
    @staticmethod
    def create_kml_map(final_results):
        kml_path = os.path.join(Config.BASE_DIRECTORY, "infrastructure_map.kml")
        try:
            with open(kml_path, "w", encoding="utf-8") as f:
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write('<kml xmlns="http://www.opengis.net/kml/2.2">\n')
                f.write('<Document>\n')
                f.write(f'  <name>CCTV Infrastructure Audit Map</name>\n')
                for item in final_results:
                    lon = item['geo']['lon']
                    lat = item['geo']['lat']
                    if lat == 0.0 and lon == 0.0: continue
                    ports = ", ".join(map(str, item['shodan']['ports']))
                    f.write('  <Placemark>\n')
                    f.write(f'    <name>{item["ip"]}</name>\n')
                    f.write(f'    <description><![CDATA[<b>ISP:</b> {item["geo"]["isp"]}<br/><b>Ports:</b> {ports}]]></description>\n')
                    f.write('    <Point>\n')
                    f.write(f'      <coordinates>{lon},{lat},0</coordinates>\n')
                    f.write('    </Point>\n')
                    f.write('  </Placemark>\n')
                f.write('</Document>\n</kml>\n')
            return kml_path
        except:
            return None

    @staticmethod
    def compile_statistics(final_results, execution_time):
        total = len(final_results)
        countries = {}
        for item in final_results:
            p = item['geo']['country']
            countries[p] = countries.get(p, 0) + 1
        sorted_countries = sorted(countries.items(), key=lambda x: x[1], reverse=True)[:3]
        
        report = [
            "<b>📊 FINAL AUDIT SUMMARY REPORT</b>",
            f"Time elapsed: {execution_time:.2f} seconds",
            f"Total active mapped hosts: <code>{total}</code>\n",
            "<b>🌍 TOP COUNTRIES:</b>"
        ]
        for country, count in sorted_countries:
            report.append(f" • {country}: {count} devices")
        return "\n".join(report)

# =====================================================================
#               TEXT USER INTERFACE MODULE (TUI)
# =====================================================================
class AuditInterfaceTUI:
    def __init__(self):
        self.queue = queue.Queue()
        Config.TUI_QUEUE = self.queue
        self.total_progress_max = 100
        self.current_progress_val = 0

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def interactive_folder_selector(self, start_path="."):
        """ Permite navegar visualmente seleccionando carpetas numéricamente sin escribir rutas """
        current_path = os.path.abspath(start_path)
        while True:
            self.clear_terminal()
            show_banner()
            
            # Ocultamos la ruta larga interna imprimiendo solo el nombre base
            nombre_carpeta_actual = os.path.basename(current_path)
            if not nombre_carpeta_actual:
                nombre_carpeta_actual = current_path
            
            print(f"{Colors.BOLD}{Colors.CYAN}--- SELECCIÓN DE CARPETA DE TRABAJO ---{Colors.RESET}")
            print(f"{Colors.YELLOW}Ubicación actual:{Colors.RESET} 📂 {Colors.BOLD}{nombre_carpeta_actual}{Colors.RESET}\n")
            
            try:
                folders = [d for d in os.listdir(current_path) if os.path.isdir(os.path.join(current_path, d))]
                folders.sort()
            except Exception as e:
                print(f"{Colors.RED}[❌] Error al leer el directorio: {str(e)}{Colors.RESET}")
                folders = []
            
            print(f" [0] {Colors.GREEN}👉 CONFIRMAR Y SELECCIONAR: {nombre_carpeta_actual}{Colors.RESET}")
            print(f" [..] ⬅️ Volver a la carpeta anterior")
            print(f"{Colors.GRAY}{'-'*60}{Colors.RESET}")
            
            if not folders:
                print(f"      {Colors.GRAY}(No hay subcarpetas dentro de este directorio){Colors.RESET}")
            else:
                for idx, folder in enumerate(folders, start=1):
                    print(f" [{idx}] 📁 {folder}")
            
            print(f"\n{Colors.GRAY}{'-'*60}{Colors.RESET}")
            choice = input("Elige una opción (Número / '..'): ").strip()
            
            if choice == '0':
                return current_path
            elif choice == '..':
                current_path = os.path.dirname(current_path)
            elif choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(folders):
                    current_path = os.path.join(current_path, folders[idx])
                else:
                    print(f"{Colors.RED}[!] Número de carpeta inválido.{Colors.RESET}")
                    time.sleep(1)
            else:
                print(f"{Colors.RED}[!] Opción desconocida.{Colors.RESET}")
                time.sleep(1)

    def run_setup_menu(self):
        self.clear_terminal()
        show_banner()
        print(f"{Colors.BOLD}{Colors.CYAN}--- AUDIT ENVIRONMENT PARAMETERS SYSTEM ---{Colors.RESET}\n")
        
        # 1. Telegram Settings Configuration
        tg_toggle = input("Enable automated Telegram transmission stream? (y/n) [y]: ").strip().lower()
        if tg_toggle in ['', 'y', 'yes']:
            Config.TELEGRAM_ACTIVE = True
            while True:
                Config.TELEGRAM_TOKEN = input(" -> Enter Telegram Bot Token: ").strip()
                if Config.TELEGRAM_TOKEN: break
                print(f"{Colors.RED}[!] Token configuration field cannot be blank.{Colors.RESET}")
            while True:
                Config.TELEGRAM_CHAT_ID = input(" -> Enter Target Channel Chat ID: ").strip()
                if Config.TELEGRAM_CHAT_ID: break
                print(f"{Colors.RED}[!] Chat ID configuration field cannot be blank.{Colors.RESET}")
        else:
            Config.TELEGRAM_ACTIVE = False
            print(f"{Colors.YELLOW}[!] Telegram dynamic transmission disabled.{Colors.RESET}")
            
        print()
        # 2. Search Pattern Configuration
        pattern_input = input("Enter keyword Search Pattern criteria [DVR]: ").strip()
        if pattern_input:
            Config.SEARCH_PATTERN = pattern_input
            
        print()
        # 3. Path Folder Target Interactive Selector
        Config.TARGET_FOLDER = self.interactive_folder_selector(os.getcwd())
            
        self.execute_live_dashboard()

    def draw_text_progressbar(self):
        """ Render clean alphanumeric command line progressbar status line """
        bar_length = 30
        if self.total_progress_max <= 0:
            percent = 0
        else:
            percent = min(100, int((self.current_progress_val / self.total_progress_max) * 100))
            
        filled_length = int(bar_length * self.current_progress_val // self.total_progress_max)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        sys.stdout.write(f"\r{Colors.YELLOW}[Progress Bar]: |{bar}| {percent}% Processing...{Colors.RESET}")
        sys.stdout.flush()

    def execute_live_dashboard(self):
        self.clear_terminal()
        show_banner()
        print(f"{Colors.GREEN}{Colors.BOLD}[🚀] RUNNING AUDIT CORES AND INITIATING NETWORK INTEL PIPELINES...{Colors.RESET}\n")
        print(f"{Colors.GRAY}{'-'*70}{Colors.RESET}")
        
        # Dispatch processing routine execution thread
        threading.Thread(target=self.run_background_audit_process, daemon=True).start()
        
        # Loop orchestration listener directly bound onto primary thread
        self.process_queue_messages()

    def run_background_audit_process(self):
        start_time = time.time()
        initialize_environment()
        
        self.queue.put(("STATUS", "Phase 1: Deep scanning local directory storage chunks..."))
        scout = ScoutEngine(Config.SEARCH_PATTERN)
        
        if not scout.run_local_scan(Config.TARGET_FOLDER):
            self.queue.put(("STATUS", f"{Colors.RED}[❌] Critical: Scan stopped. No pattern hits located.{Colors.RESET}"))
            self.queue.put(("FINISHED", None))
            return
            
        self.queue.put(("STATUS", f"Phase 2: Extracted {len(scout.extracted_targets)} unique host nodes. Mapping intel..."))
        
        network_engine = NetworkIntelEngine()
        final_data = network_engine.process_network_batch(scout.extracted_targets)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        if final_data:
            kml_path = ReportGenerator.create_kml_map(final_data)
            dashboard_text = ReportGenerator.compile_statistics(final_data, total_time)
            
            # Print report console display
            print("\n\n" + f"{Colors.CYAN}" + "="*55 + f"{Colors.RESET}")
            print(dashboard_text.replace("<b>", "").replace("</b>", "").replace("<code>", "").replace("</code>", ""))
            print(f"{Colors.CYAN}" + "="*55 + f"{Colors.RESET}\n")
            
            if Config.TELEGRAM_ACTIVE:
                notifier = TelegramNotifier()
                notifier.send_message(dashboard_text)
                if kml_path:
                    notifier.send_document(kml_path, description="Global Infrastructure KML Location Layer Map")
                    
        self.queue.put(("STATUS", f"Processing streams terminated. Active hosts processed: {len(final_data)}"))
        self.queue.put(("FINISHED", None))

    def process_queue_messages(self):
        while True:
            try:
                msg_type, data = self.queue.get(timeout=0.1)
                
                if msg_type == "RESULT":
                    item = data
                    vulns_list = item['shodan'].get('vulnerabilities', [])
                    vulns_str = ", ".join(vulns_list) if vulns_list else "No"
                    ports_str = ", ".join(map(str, item['shodan']['ports']))
                    date_str = datetime.now().strftime("%d/%m/%Y")
                    country_code = item['geo'].get('countryCode', 'UN').upper()
                    
                    # 1. Core UI layout template
                    tui_format_text = (
                        f"\n{Colors.GREEN}| IP: {item['ip']}\n"
                        f"| VULN: {vulns_str}\n"
                        f"| ISP: {item['geo']['isp']}\n"
                        f"| OPEN PORTS: {ports_str}\n"
                        f"| LOG:  {item['line']}\n"
                        f"| COUNTRY:{country_code}\n"
                        f"| DATE: {date_str}\n"
                        f"{'-'*45}{Colors.RESET}\n"
                    )
                    sys.stdout.write(tui_format_text)
                    sys.stdout.flush()
                    
                    # 2. Strict live active Telegram notification formatting payload
                    if Config.TELEGRAM_ACTIVE:
                        flag_emoji = get_flag_emoji(country_code)
                        telegram_format_text = (
                            f"| IP: {item['ip']}\n"
                            f"| VULN: {vulns_str}\n"
                            f"| ISP: {item['geo']['isp']}\n"
                            f"| OPEN PORTS: {ports_str}\n"
                            f"| LOG:  {item['line']}\n"
                            f"| COUNTRY: {flag_emoji} ({country_code})\n"
                            f"| DATE: {date_str}\n"
                        )
                        notifier_inst = TelegramNotifier()
                        notifier_inst.send_message(telegram_format_text)
                        
                elif msg_type == "STATUS":
                    print(f"\n{Colors.CYAN}[System Status]: {data}{Colors.RESET}")
                elif msg_type == "TOTAL_PROGRESS":
                    self.total_progress_max = data
                    self.current_progress_val = 0
                elif msg_type == "SET_PROGRESS":
                    self.current_progress_val = data
                    self.draw_text_progressbar()
                elif msg_type == "FINISHED":
                    print(f"\n\n{Colors.GREEN}[+] Mission Success. Storage logs writing and transmissions completed.{Colors.RESET}\n")
                    sys.exit(0)
                    
            except queue.Empty:
                pass
            except KeyboardInterrupt:
                print(f"\n{Colors.RED}[!] Execution aborted by user interruption request.{Colors.RESET}")
                sys.exit(0)

# =====================================================================
#                         CORE ORCHESTRATOR
# =====================================================================
def main():
    # Establecer título estético para la barra de la ventana de Windows
    set_window_title("IP CAM FUCKER 1.0v  |  cracked.st/nontop")
    
    # Execute structural TUI loop workflows
    tui_app = AuditInterfaceTUI()
    tui_app.run_setup_menu()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()