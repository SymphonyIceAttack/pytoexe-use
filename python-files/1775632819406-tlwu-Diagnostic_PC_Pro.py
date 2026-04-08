# ==============================================
# OUTIL DIAGNOSTIC PC - VERSION ENTREPRISE FINALE
# ==============================================
# pip install psutil rich fpdf customtkinter requests matplotlib

import psutil
import platform
import socket
import subprocess
import hashlib
import requests
import threading
import time
import os
from fpdf import FPDF
import customtkinter as ctk
import matplotlib.pyplot as plt

API_KEY = "METS_TA_CLE_VIRUSTOTAL_ICI"
rapport = []
score = 100
mode_client = True  # True = rapport clean, False = mode technicien détaillé

# ================= UTILITAIRES =================
def hash_file(path):
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except:
        return None

def check_virustotal(hash_value):
    global score
    url = f"https://www.virustotal.com/api/v3/files/{hash_value}"
    headers = {"x-apikey": API_KEY}
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            data = r.json()
            malicious = data['data']['attributes']['last_analysis_stats']['malicious']
            if malicious > 0:
                rapport.append(f"Malware détecté: {hash_value}")
                score -= 20
    except:
        pass

# ================= SCAN PROCESS =================
def process_scan():
    global score
    for proc in psutil.process_iter(['pid','name','exe','cpu_percent']):
        try:
            if proc.info['cpu_percent'] > 80:
                rapport.append(f"Process suspect CPU: {proc.info['name']}")
                score -= 5

            exe = proc.info['exe']
            if exe:
                h = hash_file(exe)
                if h:
                    check_virustotal(h)
        except:
            pass

# ================= DRIVERS =================
def drivers_check():
    try:
        result = subprocess.check_output("driverquery", shell=True)
        rapport.append("Drivers récupérés")
        if not mode_client:
            rapport.append(result.decode())
    except:
        rapport.append("Erreur drivers")

# ================= DISQUE =================
def disk_smart():
    try:
        result = subprocess.check_output("wmic diskdrive get status", shell=True)
        data = result.decode()
        rapport.append(data)
    except:
        rapport.append("SMART non dispo")

def disk_benchmark():
    start = time.time()
    with open("test.tmp", "wb") as f:
        f.write(b"0" * 10000000)
    end = time.time()
    os.remove("test.tmp")
    rapport.append(f"Ecriture disque: {round(end-start,2)}s")

# ================= RESEAU =================
def port_scan():
    open_ports = []
    for port in range(1,1024):
        s = socket.socket()
        s.settimeout(0.2)
        if s.connect_ex(("127.0.0.1", port)) == 0:
            open_ports.append(port)
        s.close()
    rapport.append(f"Ports ouverts: {open_ports}")

def detect_services():
    services = {22:"SSH",80:"HTTP",443:"HTTPS",3389:"RDP"}
    for port, name in services.items():
        s = socket.socket()
        s.settimeout(0.5)
        if s.connect_ex(("127.0.0.1", port)) == 0:
            rapport.append(f"Service détecté: {name}")
        s.close()

# ================= EVENT LOGS =================
def analyze_event_logs():
    try:
        result = subprocess.check_output("wevtutil qe System /c:10 /rd:true /f:text", shell=True)
        logs = result.decode(errors='ignore')
        rapport.append("Derniers logs système:")
        if not mode_client:
            rapport.append(logs)
    except:
        rapport.append("Impossible d'analyser logs")

# ================= PERSISTENCE MALWARE =================
def check_registry_persistence():
    try:
        result = subprocess.check_output("reg query HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run", shell=True)
        data = result.decode()
        rapport.append("Vérification persistence malware (registry)")
        if not mode_client:
            rapport.append(data)
    except:
        rapport.append("Erreur registry")

# ================= SCAN USB =================
def scan_usb():
    for drive in psutil.disk_partitions():
        if 'removable' in drive.opts:
            rapport.append(f"Scan USB: {drive.device}")

# ================= DASHBOARD GRAPHIQUE =================
def plot_dashboard():
    cpu = psutil.cpu_percent(interval=1, percpu=True)
    ram = psutil.virtual_memory().percent

    plt.figure(figsize=(5,3))
    plt.bar(range(len(cpu)), cpu)
    plt.title('CPU Usage %')
    plt.show(block=False)

    plt.figure(figsize=(5,3))
    plt.bar([0], [ram])
    plt.title('RAM Usage %')
    plt.show(block=False)

# ================= PDF =================
def export_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0,10,"RAPPORT DIAGNOSTIC ENTREPRISE",ln=True)

    pdf.set_font("Arial", size=10)
    pdf.cell(0,10,f"Score santé: {score}/100",ln=True)

    for line in rapport:
        pdf.cell(0,5,line,ln=True)

    pdf.output("rapport_entreprise_final.pdf")

# ================= SCAN COMPLET =================
def full_scan():
    rapport.clear()
    process_scan()
    drivers_check()
    disk_smart()
    disk_benchmark()
    port_scan()
    detect_services()
    analyze_event_logs()
    check_registry_persistence()
    scan_usb()
    plot_dashboard()
    export_pdf()

# ================= UI =================
ctk.set_appearance_mode("dark")
app = ctk.CTk()
app.title("Diagnostic PC Entreprise")
app.geometry("700x550")

label = ctk.CTkLabel(app, text="Outil Diagnostic PC Entreprise", font=("Arial",20))
label.pack(pady=20)

progress = ctk.CTkProgressBar(app)
progress.pack(pady=10)
progress.set(0)


def start_scan():
    def run():
        steps = [process_scan, drivers_check, disk_smart, disk_benchmark, port_scan, detect_services, analyze_event_logs, check_registry_persistence, scan_usb, plot_dashboard]
        for i, step in enumerate(steps):
            step()
            progress.set((i+1)/len(steps))
        export_pdf()
    threading.Thread(target=run).start()

btn = ctk.CTkButton(app, text="SCAN COMPLET", command=start_scan)
btn.pack(pady=20)

# ================= MODE CLIENT / TECHNICIEN =================
def toggle_mode():
    global mode_client
    mode_client = not mode_client
    if mode_client:
        btn_mode.configure(text="Mode Client")
    else:
        btn_mode.configure(text="Mode Technicien")

btn_mode = ctk.CTkButton(app, text="Mode Client", command=toggle_mode)
btn_mode.pack(pady=10)

app.mainloop()