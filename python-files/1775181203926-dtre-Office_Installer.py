import os
import subprocess
import time
import shutil
import requests
import re
import sys
import ctypes
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from bs4 import BeautifulSoup

# Executar como administrador
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()

run_as_admin()

class OfficeInstaller:
    def __init__(self, root):
        self.root = root
        self.root.title("Office Installer Pro")
        self.root.geometry("700x600")
        self.root.resizable(False, False)
        
        # Cores
        self.bg_color = "#1a1a2e"
        self.fg_color = "#eeeeee"
        self.accent_color = "#0f3460"
        self.success_color = "#00b894"
        self.warning_color = "#e17055"
        self.progress_color = "#0984e3"
        
        # Configurar estilo
        self.root.configure(bg=self.bg_color)
        self.setup_styles()
        
        # Variáveis
        self.pasta_office = ""
        self.cancelado = False
        
        # Criar interface
        self.create_widgets()
        
        # Iniciar processo em thread separada
        self.root.after(100, self.start_installation)
    
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure("TLabel", background=self.bg_color, foreground=self.fg_color, font=("Segoe UI", 10))
        style.configure("TFrame", background=self.bg_color)
        style.configure("Header.TLabel", font=("Segoe UI", 18, "bold"), foreground=self.accent_color)
        style.configure("Title.TLabel", font=("Segoe UI", 12, "bold"))
        style.configure("Success.TLabel", foreground=self.success_color)
        style.configure("Warning.TLabel", foreground=self.warning_color)
        
        style.configure("TProgressbar", thickness=20, troughcolor=self.bg_color, background=self.progress_color)
        
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=10)
        style.map("TButton", background=[("active", self.accent_color)])
    
    def create_widgets(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = ttk.Label(main_frame, text="📦 OFFICE INSTALLER PRO", style="Header.TLabel")
        title_label.pack(pady=(0, 10))
        
        # Subtítulo
        subtitle_label = ttk.Label(main_frame, text="Instalação automática do Microsoft Office", style="TLabel")
        subtitle_label.pack(pady=(0, 30))
        
        # Frame de progresso
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Barra de progresso
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', style="TProgressbar")
        self.progress_bar.pack(fill=tk.X)
        
        # Label de passo atual
        self.step_label = ttk.Label(progress_frame, text="Inicializando...", style="Title.TLabel")
        self.step_label.pack(pady=(10, 0))
        
        # Área de log
        log_frame = ttk.LabelFrame(main_frame, text="📋 Log de Instalação", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        self.log_area = scrolledtext.ScrolledText(log_frame, height=12, bg="#2d2d3d", fg=self.fg_color, 
                                                   font=("Consolas", 9), wrap=tk.WORD)
        self.log_area.pack(fill=tk.BOTH, expand=True)
        
        # Frame de botões
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        self.close_button = ttk.Button(button_frame, text="Fechar", command=self.close_app, state=tk.DISABLED)
        self.close_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        self.cancel_button = ttk.Button(button_frame, text="Cancelar", command=self.cancel_installation)
        self.cancel_button.pack(side=tk.RIGHT)
        
        # Status
        self.status_label = ttk.Label(main_frame, text="✅ Pronto para iniciar", style="Success.TLabel")
        self.status_label.pack(pady=(10, 0))
    
    def log_message(self, message, level="info"):
        """Adiciona mensagem ao log com cor"""
        self.log_area.insert(tk.END, f"{message}\n")
        self.log_area.see(tk.END)
        
        # Cores para diferentes níveis
        if level == "error":
            self.log_area.tag_add("error", f"end-2l", "end-1l")
            self.log_area.tag_config("error", foreground=self.warning_color)
        elif level == "success":
            self.log_area.tag_add("success", f"end-2l", "end-1l")
            self.log_area.tag_config("success", foreground=self.success_color)
        
        self.root.update_idletasks()
    
    def update_progress(self, value, step_text):
        """Atualiza barra de progresso e passo atual"""
        self.progress_bar['value'] = value
        self.step_label.config(text=step_text)
        self.root.update_idletasks()
    
    def baixar_mediafire(self, url, destino, step_num, total_steps):
        """Baixa arquivo do MediaFire com múltiplos métodos"""
        try:
            self.log_message(f"Baixando de: {url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # Primeiro, obter a página
            session = requests.Session()
            response = session.get(url, headers=headers)
            
            # Procurar o link de download de várias formas
            download_url = None
            
            # Método 1: Procurar pelo botão de download
            soup = BeautifulSoup(response.text, 'html.parser')
            download_btn = soup.find('a', {'id': 'downloadButton'})
            if download_btn and download_btn.get('href'):
                download_url = download_btn.get('href')
            
            # Método 2: Procurar no JavaScript
            if not download_url:
                match = re.search(r'window\.location\.href\s*=\s*["\']([^"\']+)["\']', response.text)
                if match:
                    download_url = match.group(1)
            
            # Método 3: Procurar por links diretos
            if not download_url:
                match = re.search(r'https?://(?:download|www\d*)\.mediafire\.com/[^\s"\'<>]+', response.text)
                if match:
                    download_url = match.group(0)
            
            # Método 4: Usar regex mais abrangente
            if not download_url:
                match = re.search(r'href=["\'](https?://[^"\']+\.exe[^"\']*)["\']', response.text)
                if match:
                    download_url = match.group(1)
            
            if download_url:
                self.log_message(f"Link encontrado, iniciando download...")
                
                # Baixar com progresso
                response = session.get(download_url, stream=True, headers=headers)
                total_size = int(response.headers.get('content-length', 0))
                
                with open(destino, 'wb') as f:
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        if self.cancelado:
                            return False
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (step_num - 1 + (downloaded / total_size)) / total_steps * 100
                            self.progress_bar['value'] = progress
                            self.root.update_idletasks()
                
                # Verificar se o arquivo foi baixado
                if os.path.exists(destino) and os.path.getsize(destino) > 0:
                    self.log_message(f"✓ Download concluído: {os.path.basename(destino)} ({os.path.getsize(destino)/1024/1024:.2f} MB)", "success")
                    return True
                else:
                    self.log_message(f"✗ Arquivo vazio ou corrompido", "error")
                    return False
            else:
                self.log_message(f"✗ Não foi possível extrair link do MediaFire", "error")
                self.log_message(f"Tentando método alternativo...")
                
                # Método alternativo: Usar o serviço de download direto
                return self.baixar_alternativo(url, destino, step_num, total_steps)
                
        except Exception as e:
            self.log_message(f"✗ Erro no download: {str(e)}", "error")
            return self.baixar_alternativo(url, destino, step_num, total_steps)
    
    def baixar_alternativo(self, url, destino, step_num, total_steps):
        """Método alternativo usando a API do MediaFire"""
        try:
            # Extrair o file ID da URL
            file_id_match = re.search(r'/file/([a-zA-Z0-9]+)/', url)
            if file_id_match:
                file_id = file_id_match.group(1)
                api_url = f"https://www.mediafire.com/api/1.5/file/get_info.php?quick_key={file_id}&response_format=json"
                
                response = requests.get(api_url)
                data = response.json()
                
                if 'response' in data and 'file_info' in data['response']:
                    download_url = data['response']['file_info']['direct_download_link']
                    
                    self.log_message(f"Usando API, iniciando download...")
                    
                    # Baixar arquivo
                    response = requests.get(download_url, stream=True)
                    total_size = int(response.headers.get('content-length', 0))
                    
                    with open(destino, 'wb') as f:
                        downloaded = 0
                        for chunk in response.iter_content(chunk_size=8192):
                            if self.cancelado:
                                return False
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                progress = (step_num - 1 + (downloaded / total_size)) / total_steps * 100
                                self.progress_bar['value'] = progress
                                self.root.update_idletasks()
                    
                    if os.path.exists(destino) and os.path.getsize(destino) > 0:
                        self.log_message(f"✓ Download concluído via API", "success")
                        return True
                
            return False
        except:
            return False
    
    def cancel_installation(self):
        """Cancela a instalação"""
        if messagebox.askyesno("Cancelar", "Tem certeza que deseja cancelar a instalação?"):
            self.cancelado = True
            self.log_message("⚠ Instalação cancelada pelo usuário", "error")
            self.status_label.config(text="⚠ Instalação cancelada", style="Warning.TLabel")
            self.cancel_button.config(state=tk.DISABLED)
            self.close_button.config(state=tk.NORMAL)
    
    def close_app(self):
        """Fecha o aplicativo"""
        self.root.quit()
        self.root.destroy()
    
    def start_installation(self):
        """Inicia o processo de instalação em thread separada"""
        thread = threading.Thread(target=self.install_process)
        thread.daemon = True
        thread.start()
    
    def install_process(self):
        """Processo principal de instalação"""
        total_steps = 6
        current_step = 0
        
        try:
            # Step 1: Desinstalar Office
            current_step += 1
            self.update_progress((current_step-1)/total_steps*100, f"Passo {current_step}/{total_steps}: Desinstalando Office...")
            self.log_message("="*50)
            self.log_message("INICIANDO INSTALAÇÃO AUTOMÁTICA")
            self.log_message("="*50)
            self.log_message("[1/6] Desinstalando produtos Office existentes...")
            
            result = subprocess.run(['powershell', '-Command', 
                'Get-WmiObject -Class Win32_Product | Where-Object {$_.Name -like "*Office*"} | ForEach-Object { $_.Uninstall() }'],
                capture_output=True, text=True)
            
            self.log_message("✓ Desinstalação do Office iniciada", "success")
            time.sleep(3)
            
            # Step 2: Criar pasta
            current_step += 1
            self.update_progress((current_step-1)/total_steps*100, f"Passo {current_step}/{total_steps}: Criando pasta...")
            self.log_message("[2/6] Criando pasta na área de trabalho...")
            
            desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")
            self.pasta_office = os.path.join(desktop, "office(don't delete)")
            os.makedirs(self.pasta_office, exist_ok=True)
            
            self.log_message(f"✓ Pasta criada: {self.pasta_office}", "success")
            
            # Step 3: Baixar XML
            current_step += 1
            self.update_progress((current_step-1)/total_steps*100, f"Passo {current_step}/{total_steps}: Baixando configuração...")
            self.log_message("[3/6] Baixando arquivo de configuração XML...")
            
            xml_path = os.path.join(self.pasta_office, "Configuração.xml")
            if not self.baixar_mediafire("https://www.mediafire.com/file/7ro4gva8f8f2dxd/Configuração.xml/file", xml_path, current_step, total_steps):
                raise Exception("Falha no download do XML")
            
            # Step 4: Baixar ODT
            current_step += 1
            self.update_progress((current_step-1)/total_steps*100, f"Passo {current_step}/{total_steps}: Baixando Office Deployment Tool...")
            self.log_message("[4/6] Baixando Office Deployment Tool...")
            
            odt_exe = os.path.join(self.pasta_office, "officedeploymenttool.exe")
            if not self.baixar_mediafire("https://www.mediafire.com/file/eqidgouzbuzrngm/officedeploymenttool_19725-20126.exe/file", odt_exe, current_step, total_steps):
                raise Exception("Falha no download do ODT")
            
            # Step 5: Extrair ODT
            current_step += 1
            self.update_progress((current_step-1)/total_steps*100, f"Passo {current_step}/{total_steps}: Extraindo arquivos...")
            self.log_message("[5/6] Extraindo Office Deployment Tool...")
            
            # Executar extração silenciosa
            subprocess.run([odt_exe, "/quiet", "/extract:" + self.pasta_office], 
                         cwd=self.pasta_office, shell=True, capture_output=True)
            time.sleep(3)
            
            # Procurar setup.exe
            setup_exe = None
            for arquivo in os.listdir(self.pasta_office):
                if arquivo.lower() == "setup.exe":
                    setup_exe = os.path.join(self.pasta_office, arquivo)
                    break
            
            if setup_exe and os.path.exists(setup_exe):
                self.log_message("✓ Setup.exe encontrado", "success")
                
                # Step 6: Instalar Office
                current_step += 1
                self.update_progress((current_step-1)/total_steps*100, f"Passo {current_step}/{total_steps}: Instalando Office...")
                self.log_message("[6/6] Instalando Microsoft Office...")
                self.log_message("⏳ Isso pode levar vários minutos. Aguarde...")
                
                result = subprocess.run([setup_exe, "/configure", "Configuração.xml"], 
                                      cwd=self.pasta_office, 
                                      capture_output=True, 
                                      text=True)
                
                # Concluído
                self.update_progress(100, "Instalação Concluída!")
                self.log_message("="*50)
                self.log_message("✅ INSTALAÇÃO CONCLUÍDA COM SUCESSO!", "success")
                self.log_message("="*50)
                self.log_message("O Microsoft Office foi instalado corretamente!")
                
                self.status_label.config(text="✅ Instalação concluída com sucesso!", style="Success.TLabel")
                self.cancel_button.config(state=tk.DISABLED)
                self.close_button.config(state=tk.NORMAL)
                
                messagebox.showinfo("Sucesso", "Office instalado com sucesso!\n\nClique em OK para fechar.")
            else:
                raise Exception("Setup.exe não encontrado após extração")
                
        except Exception as e:
            self.log_message(f"❌ ERRO: {str(e)}", "error")
            self.status_label.config(text=f"❌ Erro: {str(e)}", style="Warning.TLabel")
            self.cancel_button.config(state=tk.DISABLED)
            self.close_button.config(state=tk.NORMAL)
            messagebox.showerror("Erro", f"Falha na instalação:\n{str(e)}")

if __name__ == "__main__":
    # Instalar BeautifulSoup se não tiver
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "beautifulsoup4"])
        from bs4 import BeautifulSoup
    
    root = tk.Tk()
    app = OfficeInstaller(root)
    root.mainloop()