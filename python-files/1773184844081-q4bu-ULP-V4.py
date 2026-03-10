import os
import time
import sys
from prettytable import PrettyTable

# Colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def loading_animation(text):
    for i in range(3):
        sys.stdout.write(f"\r{CYAN}{text}{'.' * (i+1)}{RESET}   ")
        sys.stdout.flush()
        time.sleep(0.4)
    sys.stdout.write("\r" + " " * (len(text) + 4) + "\r")

def extract_credentials(file_path):
    credentials = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            url, username, password = None, None, None
            for line in f:
                line = line.strip()
                if line.lower().startswith('url:'):
                    url = line[4:].strip()
                elif line.lower().startswith(('username:', 'user:')):
                    username = line.split(':', 1)[1].strip()
                elif line.lower().startswith(('password:', 'pass:')):
                    password = line.split(':', 1)[1].strip()

                if url and username and password:
                    combo = f"{url}:{username}:{password}"
                    credentials.append(combo)
                    print(f"{GREEN}[ U L P ]{RESET} {combo}")
                    url, username, password = None, None, None
    except Exception:
        pass
    return credentials

def find_and_convert_passwords(root_folder, output_file):
    total_credentials = 0
    total_lines_processed = 0
    start_time = time.time()

    loading_animation("Ulp Make...")

    with open(output_file, 'w', encoding='utf-8') as out_f:
        for dirpath, _, filenames in os.walk(root_folder):
            for file in filenames:
                file_lower = file.lower()
                if (file_lower.endswith('.txt') and 'password' in file_lower) or file_lower == 'all passwords.txt':
                    file_path = os.path.join(dirpath, file)
                    creds = extract_credentials(file_path)
                    for cred in creds:
                        out_f.write(cred + '\n')
                    total_credentials += len(creds)

                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as fcount:
                            total_lines_processed += sum(1 for _ in fcount)
                    except Exception:
                        pass

    duration = time.time() - start_time
    lines_per_second = total_lines_processed / duration if duration > 0 else 0

    table = PrettyTable()
    table.field_names = ["Metric", "Value"]
    table.add_row(["Total Credentials", total_credentials])
    table.add_row(["Total Lines Processed", total_lines_processed])
    table.add_row(["Time Taken (seconds)", f"{duration:.2f}"])
    table.add_row(["Speed (lines/sec)", f"{lines_per_second:,.0f}"])
    table.add_row(["Output File", output_file])

    print(f"\n{YELLOW}Scan Completed!{RESET}")
    print(table)

if __name__ == "__main__":
    clear_screen()
    print(f"""
{GREEN}███████╗██╗   ██╗██╗     ██████╗ 
╚══███╔╝██║   ██║██║     ██╔══██╗
  ███╔╝ ██║   ██║██║     ██████╔╝
 ███╔╝  ██║   ██║██║     ██╔═══╝ 
███████╗╚██████╔╝███████╗██║     
╚══════╝ ╚═════╝ ╚══════╝╚═╝     {RESET}
    """)

    folder_path = input(f"{CYAN}Enter the folder path to scan: {RESET}").strip()
    output_file = input(f"{CYAN}Enter the output file name (e.g., results.txt): {RESET}").strip()

    if os.path.isdir(folder_path):
        find_and_convert_passwords(folder_path, output_file)
    else:
        print(f"{RED}❌ Invalid path. Please check and try again.{RESET}")
