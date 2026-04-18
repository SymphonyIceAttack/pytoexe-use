import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import subprocess
import os
import sys
import threading
import ctypes

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    try:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        return True
    except:
        return False

class VPNInstallerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("VashInvestor VPN")
        self.root.geometry("420x500")
        self.root.resizable(False, False)
        self.root.configure(bg="#0D1117")
        
        if not is_admin():
            response = messagebox.askyesno("Права администратора", "Перезапустить с правами администратора?", icon='warning')
            if response:
                if run_as_admin():
                    self.root.destroy()
                    sys.exit(0)
            self.root.destroy()
            sys.exit(1)
        
        self.SERVER_ADDRESS = "vpn.vashinvestor.ru"
        self.CONNECTION_NAME = "VashInvestor"
        self.CERT_PASSWORD = "Investor19051981"
        
        self.cert_path = tk.StringVar()
        self.status_text = tk.StringVar(value="Готов")
        self.existing_connections = []
        self.existing_certificates = []
        
        self.check_all()
        self.create_widgets()
    
    def check_all(self):
        self.check_existing_certificates()
        self.check_existing_connections()
    
    def check_existing_certificates(self):
        try:
            ps_script = '''
$certs = @()
Get-ChildItem -Path "Cert:\\CurrentUser\\My","Cert:\\LocalMachine\\My" -ErrorAction SilentlyContinue | ForEach-Object {
    if ($_.Subject -like "*vpn.vashinvestor.ru*" -or $_.Subject -like "*vashinvestor*") {
        $certs += @{Thumbprint=$_.Thumbprint; Store=if($_.PSPath -like "*LocalMachine*"){"LocalMachine"}else{"CurrentUser"}}
    }
}
if ($certs.Count -gt 0) { ConvertTo-Json -InputObject $certs -Compress } else { "None" }
'''
            result = subprocess.run(["powershell.exe", "-NoProfile", "-Command", ps_script], capture_output=True, text=True, timeout=10, creationflags=subprocess.CREATE_NO_WINDOW)
            if result.returncode == 0 and result.stdout.strip() and result.stdout.strip() != "None":
                import json
                try:
                    certs = json.loads(result.stdout.strip())
                    self.existing_certificates = certs if isinstance(certs, list) else [certs]
                except:
                    self.existing_certificates = []
            else:
                self.existing_certificates = []
        except:
            self.existing_certificates = []
    
    def check_existing_connections(self):
        try:
            ps_script = f'Get-VpnConnection | Where-Object {{$_.ServerAddress -eq "{self.SERVER_ADDRESS}"}} | Select-Object Name | ConvertTo-Json'
            result = subprocess.run(["powershell.exe", "-NoProfile", "-Command", ps_script], capture_output=True, text=True, timeout=10, creationflags=subprocess.CREATE_NO_WINDOW)
            if result.returncode == 0 and result.stdout.strip():
                import json
                try:
                    conns = json.loads(result.stdout.strip())
                    if conns:
                        self.existing_connections = conns if isinstance(conns, list) else [conns]
                except:
                    self.existing_connections = []
        except:
            self.existing_connections = []
    
    def cleanup_vashinvestor_only(self):
        if self.existing_connections:
            for conn in self.existing_connections:
                name = conn.get('Name', '') if isinstance(conn, dict) else getattr(conn, 'Name', '')
                if name:
                    subprocess.run(["powershell.exe", "-NoProfile", "-Command", f'Remove-VpnConnection -Name "{name}" -Force'], capture_output=True, timeout=5, creationflags=subprocess.CREATE_NO_WINDOW)
        
        if self.existing_certificates:
            for cert in self.existing_certificates:
                thumbprint = cert.get('Thumbprint', '') if isinstance(cert, dict) else getattr(cert, 'Thumbprint', '')
                store = cert.get('Store', 'CurrentUser') if isinstance(cert, dict) else getattr(cert, 'Store', 'CurrentUser')
                store_path = "Cert:\\LocalMachine\\My" if store == "LocalMachine" else "Cert:\\CurrentUser\\My"
                if thumbprint:
                    subprocess.run(["powershell.exe", "-NoProfile", "-Command", f'Get-ChildItem -Path "{store_path}" | Where-Object {{$_.Thumbprint -eq "{thumbprint}"}} | Remove-Item -Force'], capture_output=True, timeout=5, creationflags=subprocess.CREATE_NO_WINDOW)
        
        return True
    
    def create_widgets(self):
        main = tk.Frame(self.root, bg="#0D1117")
        main.pack(fill="both", expand=True, padx=20, pady=15)
        
        # Заголовок
        tk.Label(main, text="🔒 VashInvestor VPN", font=("Segoe UI", 14, "bold"), fg="#3FB950", bg="#0D1117").pack(pady=(0, 5))
        tk.Label(main, text="IKEv2 Certificate Installation", font=("Segoe UI", 9), fg="#8B949E", bg="#0D1117").pack()
        
        # Карточка
        card = tk.Frame(main, bg="#161B22")
        card.pack(pady=15, fill="x")
        inner = tk.Frame(card, bg="#161B22")
        inner.pack(pady=12, padx=15, fill="x")
        
        # Статус
        if self.existing_certificates:
            tk.Label(inner, text=f"📜 Сертификатов VashInvestor: {len(self.existing_certificates)}", font=("Segoe UI", 9), fg="#D29922", bg="#161B22").pack(anchor="w")
        else:
            tk.Label(inner, text="📜 Сертификатов VashInvestor нет", font=("Segoe UI", 9), fg="#3FB950", bg="#161B22").pack(anchor="w")
        
        if self.existing_connections:
            tk.Label(inner, text=f"🔗 VPN подключений: {len(self.existing_connections)}", font=("Segoe UI", 9), fg="#D29922", bg="#161B22").pack(anchor="w", pady=(5,0))
        else:
            tk.Label(inner, text="🔗 VPN подключений нет", font=("Segoe UI", 9), fg="#3FB950", bg="#161B22").pack(anchor="w", pady=(5,0))
        
        if self.existing_certificates or self.existing_connections:
            tk.Label(inner, text="⚠ Удалится только VashInvestor", font=("Segoe UI", 8), fg="#F85149", bg="#161B22").pack(anchor="w", pady=(10,0))
            tk.Label(inner, text="✓ Личные сертификаты сохранятся", font=("Segoe UI", 8), fg="#3FB950", bg="#161B22").pack(anchor="w")
        
        # Сервер
        tk.Label(inner, text="Сервер", font=("Segoe UI", 9), fg="#8B949E", bg="#161B22").pack(anchor="w", pady=(12,0))
        tk.Label(inner, text=self.SERVER_ADDRESS, font=("Segoe UI", 10, "bold"), fg="#C9D1D9", bg="#161B22").pack(anchor="w", pady=(2,10))
        
        # Сертификат
        tk.Label(inner, text="Сертификат", font=("Segoe UI", 9), fg="#8B949E", bg="#161B22").pack(anchor="w")
        
        cert_frame = tk.Frame(inner, bg="#161B22")
        cert_frame.pack(fill="x", pady=(2,0))
        
        self.cert_path_label = tk.Label(cert_frame, text="Не выбран", font=("Segoe UI", 9), fg="#C9D1D9", bg="#161B22", anchor="w")
        self.cert_path_label.pack(side="left", fill="x", expand=True)
        tk.Button(cert_frame, text="Обзор", command=self.browse_certificate, bg="#21262D", fg="#C9D1D9", font=("Segoe UI", 9), relief="flat", cursor="hand2", padx=8).pack(side="right")
        
        # Пароль
        pass_frame = tk.Frame(inner, bg="#161B22")
        pass_frame.pack(fill="x", pady=(8,0))
        tk.Label(pass_frame, text="Пароль", font=("Segoe UI", 9), fg="#8B949E", bg="#161B22").pack(side="left")
        tk.Label(pass_frame, text="✓ Вшит", font=("Segoe UI", 9), fg="#3FB950", bg="#161B22").pack(side="right")
        
        # Кнопка
        btn_text = "Переустановить" if (self.existing_certificates or self.existing_connections) else "Установить VPN"
        self.install_btn = tk.Button(main, text=btn_text, command=self.start_installation, bg="#238636", fg="#FFFFFF", font=("Segoe UI", 11, "bold"), relief="flat", cursor="hand2", pady=8)
        self.install_btn.pack(pady=12, fill="x")
        
        # Статус
        status_frame = tk.Frame(main, bg="#0D1117", height=30)
        status_frame.pack(fill="x")
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(status_frame, textvariable=self.status_text, font=("Segoe UI", 9), fg="#8B949E", bg="#0D1117")
        self.status_label.pack()
        self.progress = ttk.Progressbar(status_frame, mode='indeterminate', length=200)
        
    def browse_certificate(self):
        filename = filedialog.askopenfilename(title="Выберите сертификат", filetypes=[("Certificate files", "*.p12 *.pfx"), ("All files", "*.*")])
        if filename:
            self.cert_path.set(filename)
            name = os.path.basename(filename)
            self.cert_path_label.config(text=name[:25] + "..." if len(name) > 25 else name, fg="#3FB950")
            self.status_text.set("Сертификат выбран")
    
    def start_installation(self):
        if not self.cert_path.get():
            messagebox.showerror("Ошибка", "Выберите сертификат!")
            return
        
        if self.existing_certificates or self.existing_connections:
            if not messagebox.askyesno("Подтверждение", "Удалить старые данные VashInvestor?\n\nЛичные сертификаты НЕ пострадают.", icon='question'):
                return
        
        self.install_btn.config(state="disabled", text="Установка...", bg="#21262D")
        self.progress.pack(pady=(5,0))
        self.progress.start(10)
        self.status_text.set("Очистка...")
        
        threading.Thread(target=self.run_installation, daemon=True).start()
    
    def run_installation(self):
        try:
            self.cleanup_vashinvestor_only()
            self.root.after(0, self.status_text.set, "Установка сертификата...")
            
            cert_path = self.cert_path.get().replace('\\', '\\\\')
            
            ps_script = f'''
$pwd = ConvertTo-SecureString -String "{self.CERT_PASSWORD}" -AsPlainText -Force
Import-PfxCertificate -FilePath "{cert_path}" -CertStoreLocation "Cert:\\LocalMachine\\My" -Password $pwd -Exportable:$false
Add-VpnConnection -Name "{self.CONNECTION_NAME}" -ServerAddress "{self.SERVER_ADDRESS}" -TunnelType Ikev2 -AuthenticationMethod MachineCertificate -EncryptionLevel Maximum -SplitTunneling -AllUserConnection -Force
'''
            temp_script = os.path.join(os.environ['TEMP'], 'vpn_setup.ps1')
            with open(temp_script, 'w', encoding='utf-8-sig') as f:
                f.write(ps_script)
            
            result = subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", temp_script], capture_output=True, text=True, timeout=60, creationflags=subprocess.CREATE_NO_WINDOW)
            os.remove(temp_script)
            
            success = result.returncode == 0 or "already exists" in result.stderr.lower()
            self.root.after(0, self.installation_done, success, result.stderr if not success else None)
        except Exception as e:
            self.root.after(0, self.installation_done, False, str(e))
    
    def installation_done(self, success, error_msg=None):
        self.progress.stop()
        self.progress.pack_forget()
        
        if success:
            self.status_text.set("✓ Готово!")
            self.status_label.config(fg="#3FB950")
            self.install_btn.config(state="normal", text="✓ Готово", bg="#238636")
            self.check_all()
            messagebox.showinfo("Успех", "VPN VashInvestor настроен!\n\nНажмите на значок сети в трее для подключения.")
        else:
            self.status_text.set("✗ Ошибка")
            self.status_label.config(fg="#F85149")
            self.install_btn.config(state="normal", text="Попробовать снова", bg="#DA3633")
            messagebox.showerror("Ошибка", f"{error_msg[:300] if error_msg else 'Неизвестная ошибка'}")
    
    def run(self):
        self.root.update_idletasks()
        w, h = self.root.winfo_width(), self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f'{w}x{h}+{x}+{y}')
        self.root.mainloop()

if __name__ == "__main__":
    app = VPNInstallerApp()
    app.run()