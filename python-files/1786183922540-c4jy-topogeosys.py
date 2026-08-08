"""
TOPOGEOSYS 2026 v1.0
Sistema Topográfico Profissional

Desenvolvido por: Rodrigo Rocha
E-mail: rcruzoe4@gmail.com
Copyright © 2026 - Todos os direitos reservados
"""

import os
import sys
import json
import hashlib
import base64
import sqlite3
import time
import datetime
import uuid
import subprocess
import webbrowser
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# ============================================
# INFORMAÇÕES DO DESENVOLVEDOR
# ============================================

DESENVOLVEDOR = "Rodrigo Rocha"
EMAIL = "rcruzoe4@gmail.com"
VERSAO = "1.0"
ANO = "2026"
SOFTWARE = "TopoGeoSys 2026"

# ============================================
# SISTEMA DE LICENCIAMENTO
# ============================================

class LicenseManager:
    """Sistema de licenciamento profissional"""
    
    VERSAO_LIC = "1.0"
    ARQUIVO_LICENCA = "LICENSE.lic"
    ARQUIVO_REVOGADOS = "revogados.db"
    PERIODO_TESTE_DIAS = 30
    DIAS_AVISO = 5
    
    def __init__(self):
        self.hwid = self.obter_hwid()
        self.dados_licenca = None
        self.licenca_valida = False
        self.tipo_licenca = "TRIAL"
        self.dias_restantes = self.PERIODO_TESTE_DIAS
        
    def obter_hwid(self):
        """Obtém HWID único do computador"""
        try:
            dados = []
            
            # Nome do computador
            try:
                import socket
                hostname = socket.gethostname()
                dados.append(hostname)
            except:
                pass
            
            # Volume Serial
            try:
                import win32api
                volume = win32api.GetVolumeInformation("C:\\")[1]
                dados.append(str(volume))
            except:
                pass
            
            # MAC Address
            try:
                mac = uuid.getnode()
                dados.append(str(mac))
            except:
                pass
            
            # Processador
            try:
                result = subprocess.run(
                    ['wmic', 'cpu', 'get', 'ProcessorId'],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                linhas = result.stdout.strip().split('\n')
                if len(linhas) > 1:
                    processador = linhas[1].strip()
                    if processador:
                        dados.append(processador)
            except:
                pass
            
            # Placa-mãe
            try:
                result = subprocess.run(
                    ['wmic', 'baseboard', 'get', 'SerialNumber'],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                linhas = result.stdout.strip().split('\n')
                if len(linhas) > 1:
                    placa_mae = linhas[1].strip()
                    if placa_mae:
                        dados.append(placa_mae)
            except:
                pass
            
            dados_str = "|".join(dados)
            hash_obj = hashlib.sha256(dados_str.encode())
            hwid = hash_obj.hexdigest()[:32].upper()
            
            return hwid
            
        except:
            return hashlib.md5(str(uuid.uuid4()).encode()).hexdigest()[:32].upper()
    
    def validar_licenca(self, arquivo_licenca=None):
        """Valida a licença atual"""
        if not arquivo_licenca:
            arquivo_licenca = self.ARQUIVO_LICENCA
        
        if not os.path.exists(arquivo_licenca):
            return self._validar_teste()
        
        try:
            with open(arquivo_licenca, 'r') as f:
                dados_criptografados = f.read()
            
            dados_str = self._descriptografar(dados_criptografados)
            dados_licenca = json.loads(dados_str)
            
            dados_verificar = {k: v for k, v in dados_licenca.items() if k != "assinatura"}
            dados_str = json.dumps(dados_verificar, sort_keys=True)
            
            if not self._verificar_assinatura(dados_str, dados_licenca.get("assinatura")):
                self.licenca_valida = False
                self.tipo_licenca = "INVALIDO"
                return False
            
            if dados_licenca["hwid"] != self.hwid:
                self.licenca_valida = False
                self.tipo_licenca = "HWID_INVALIDO"
                return False
            
            data_validade = datetime.datetime.fromisoformat(dados_licenca["valida_ate"])
            if datetime.datetime.now() > data_validade:
                self.licenca_valida = False
                self.tipo_licenca = "EXPIRADA"
                return False
            
            self.dias_restantes = (data_validade - datetime.datetime.now()).days
            
            if self._esta_revogado(dados_licenca.get("id_unico")):
                self.licenca_valida = False
                self.tipo_licenca = "REVOGADA"
                return False
            
            self.dados_licenca = dados_licenca
            self.licenca_valida = True
            self.tipo_licenca = dados_licenca["tipo"]
            return True
            
        except Exception as e:
            self.licenca_valida = False
            self.tipo_licenca = "ERRO"
            return False
    
    def _validar_teste(self):
        """Valida período de teste"""
        arquivo_teste = "teste.dat"
        
        if not os.path.exists(arquivo_teste):
            dados_teste = {
                "primeiro_uso": datetime.datetime.now().isoformat(),
                "usos": 1
            }
            with open(arquivo_teste, 'w') as f:
                json.dump(dados_teste, f)
            
            self.licenca_valida = True
            self.tipo_licenca = "TRIAL"
            self.dias_restantes = self.PERIODO_TESTE_DIAS
            return True
        
        try:
            with open(arquivo_teste, 'r') as f:
                dados_teste = json.load(f)
            
            primeiro_uso = datetime.datetime.fromisoformat(dados_teste["primeiro_uso"])
            dias_usados = (datetime.datetime.now() - primeiro_uso).days
            self.dias_restantes = max(0, self.PERIODO_TESTE_DIAS - dias_usados)
            
            if dias_usados > self.PERIODO_TESTE_DIAS:
                self.licenca_valida = False
                self.tipo_licenca = "TRIAL_EXPIRADO"
                return False
            
            dados_teste["usos"] = dados_teste.get("usos", 0) + 1
            with open(arquivo_teste, 'w') as f:
                json.dump(dados_teste, f)
            
            self.licenca_valida = True
            self.tipo_licenca = "TRIAL"
            return True
            
        except:
            self.licenca_valida = False
            self.tipo_licenca = "ERRO"
            return False
    
    def _gerar_chave(self):
        """Gera chave de criptografia"""
        salt = b'topogeosys2026_salt_v1'
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.hwid.encode()))
        return key
    
    def _criptografar(self, dados):
        """Criptografa dados"""
        try:
            key = self._gerar_chave()
            f = Fernet(key)
            dados_bytes = dados.encode()
            criptografado = f.encrypt(dados_bytes)
            return base64.b64encode(criptografado).decode()
        except:
            return base64.b64encode(dados.encode()).decode()
    
    def _descriptografar(self, dados_criptografados):
        """Descriptografa dados"""
        try:
            key = self._gerar_chave()
            f = Fernet(key)
            dados_bytes = base64.b64decode(dados_criptografados)
            descriptografado = f.decrypt(dados_bytes)
            return descriptografado.decode()
        except:
            return base64.b64decode(dados_criptografados).decode()
    
    def _gerar_assinatura(self, dados):
        """Gera assinatura digital"""
        chave = self.hwid + "topogeosys2026_secret_key_rodrigo"
        return hashlib.sha256((dados + chave).encode()).hexdigest()
    
    def _verificar_assinatura(self, dados, assinatura):
        """Verifica assinatura"""
        assinatura_esperada = self._gerar_assinatura(dados)
        return assinatura == assinatura_esperada
    
    def _esta_revogado(self, id_licenca):
        """Verifica se licença está revogada"""
        if not os.path.exists(self.ARQUIVO_REVOGADOS):
            return False
        
        try:
            conn = sqlite3.connect(self.ARQUIVO_REVOGADOS)
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM revogados WHERE id = ?', (id_licenca,))
            resultado = cursor.fetchone()
            conn.close()
            return resultado is not None
        except:
            return False
    
    def get_info(self):
        """Retorna informações da licença"""
        info = {
            "status": self.tipo_licenca,
            "hwid": self.hwid,
            "valida": self.licenca_valida,
            "desenvolvedor": DESENVOLVEDOR,
            "email": EMAIL,
            "software": SOFTWARE,
            "versao": VERSAO
        }
        
        if self.dados_licenca:
            info["usuario"] = self.dados_licenca.get("usuario", "")
            info["valida_ate"] = self.dados_licenca.get("valida_ate", "")
            info["id_licenca"] = self.dados_licenca.get("id_unico", "")
        
        if self.tipo_licenca == "TRIAL":
            info["dias_restantes"] = self.dias_restantes
        
        return info
    
    def criar_licenca(self, hwid_cliente, dias_validade=365, tipo="FULL", usuario=None):
        """Cria nova licença (usado pelo gerador)"""
        dados_licenca = {
            "hwid": hwid_cliente,
            "tipo": tipo,
            "criada_em": datetime.datetime.now().isoformat(),
            "valida_ate": (datetime.datetime.now() + 
                          datetime.timedelta(days=dias_validade)).isoformat(),
            "usuario": usuario or "Cliente",
            "versao": self.VERSAO_LIC,
            "id_unico": str(uuid.uuid4()),
            "desenvolvedor": DESENVOLVEDOR
        }
        
        dados_str = json.dumps(dados_licenca, sort_keys=True)
        assinatura = self._gerar_assinatura(dados_str)
        dados_licenca["assinatura"] = assinatura
        
        return dados_licenca
    
    def salvar_licenca(self, dados_licenca, arquivo=None):
        """Salva licença em arquivo"""
        if not arquivo:
            arquivo = self.ARQUIVO_LICENCA
        
        dados_str = json.dumps(dados_licenca)
        dados_criptografados = self._criptografar(dados_str)
        
        with open(arquivo, 'w') as f:
            f.write(dados_criptografados)
        
        return True

# ============================================
# IMPORTAR BIBLIOTECAS GRÁFICAS
# ============================================

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, scrolledtext
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    from matplotlib.figure import Figure
    BIBLIOTECAS_OK = True
except ImportError as e:
    BIBLIOTECAS_OK = False
    print(f"⚠️ Erro ao importar bibliotecas: {e}")
    print("Execute: pip install pandas numpy matplotlib openpyxl cryptography")

# ============================================
# CLASSE PRINCIPAL DO PROGRAMA
# ============================================

class TopoGeoSysApp:
    """Aplicativo principal TopoGeoSys 2026"""
    
    def __init__(self, root):
        self.root = root
        self.root.title(f"{SOFTWARE} v{VERSAO} - Desenvolvido por {DESENVOLVEDOR}")
        self.root.geometry("1280x750")
        
        try:
            self.root.iconbitmap('topo.ico')
        except:
            pass
        
        self.license_manager = LicenseManager()
        if not self._verificar_licenca_inicial():
            return
        
        self.projeto = {
            'nome': f'Projeto {datetime.datetime.now().strftime("%d/%m/%Y")}',
            'descricao': '',
            'data_criacao': datetime.datetime.now().isoformat(),
            'ultima_modificacao': datetime.datetime.now().isoformat(),
            'estacoes': [],
            'pontos': [],
            'curvas': [],
            'poligonais': [],
            'ajustes': {
                'aplicado': False,
                'metodo': 'Bowditch',
                'erro_linear': 0,
                'erro_angular': 0
            },
            'georreferenciamento': {
                'sistema': 'SIRGAS 2000',
                'fuso': 22,
                'meridiano_central': -45,
                'fator_escala': 0.9996,
                'datum': 'SIRGAS2000',
                'origem_x': 500000,
                'origem_y': 10000000
            },
            'area': 0,
            'perimetro': 0,
            'centroide': {'x': 0, 'y': 0}
        }
        
        self.config = {
            'cor_poligono': '#0a1628',
            'cor_pontos': '#e94560',
            'cor_curvas': '#2e7d32',
            'mostrar_grade': True,
            'mostrar_coordenadas': True,
            'unidade': 'm'
        }
        
        self.contador_pontos = 0
        self.contador_poligonais = 0
        self.contador_curvas = 0
        
        self.criar_interface()
        self.carregar_ultimo_projeto()
        self.atualizar_interface()
        
        self.root.bind('<Return>', lambda e: self.adicionar_estacao())
        self.root.bind('<Control-n>', lambda e: self.novo_projeto())
        self.root.bind('<Control-s>', lambda e: self.salvar_projeto())
        self.root.bind('<Control-o>', lambda e: self.abrir_projeto())
        
        self.atualizar_status(f"{SOFTWARE} pronto. Desenvolvido por {DESENVOLVEDOR}")
    
    # ============================================
    # VERIFICAÇÃO DE LICENÇA
    # ============================================
    
    def _verificar_licenca_inicial(self):
        """Verifica licença na inicialização"""
        if not self.license_manager.validar_licenca():
            return self._mostrar_dialogo_ativacao()
        
        info = self.license_manager.get_info()
        if info['status'] == 'TRIAL':
            dias = info.get('dias_restantes', 30)
            if dias <= 5:
                messagebox.showwarning(
                    "⚠️ Período de Teste",
                    f"Seu período de teste termina em {dias} dias.\n\n"
                    f"Adquira sua licença em: {EMAIL}"
                )
        
        return True
    
    def _mostrar_dialogo_ativacao(self):
        """Mostra diálogo de ativação"""
        janela = tk.Toplevel(self.root)
        janela.title(f"🔐 Ativação - {SOFTWARE}")
        janela.geometry("650x500")
        janela.transient(self.root)
        janela.grab_set()
        janela.resizable(False, False)
        
        janela.update_idletasks()
        x = (janela.winfo_screenwidth() // 2) - 325
        y = (janela.winfo_screenheight() // 2) - 250
        janela.geometry(f"+{x}+{y}")
        
        titulo = ttk.Label(janela, text=f"🔐 {SOFTWARE}", 
                          font=('Arial', 22, 'bold'))
        titulo.pack(pady=20)
        
        subtitulo = ttk.Label(janela, text=f"Sistema Topográfico Profissional\nDesenvolvido por {DESENVOLVEDOR}", 
                             font=('Arial', 11))
        subtitulo.pack(pady=5)
        
        frame_status = ttk.LabelFrame(janela, text="Status da Licença", padding=10)
        frame_status.pack(fill=tk.X, padx=20, pady=10)
        
        status_texto = tk.StringVar()
        status_label = ttk.Label(frame_status, textvariable=status_texto, 
                                font=('Arial', 11))
        status_label.pack()
        
        if self.license_manager.tipo_licenca == "TRIAL_EXPIRADO":
            status_texto.set("❌ PERÍODO DE TESTE EXPIRADO")
        else:
            status_texto.set("❌ SEM LICENÇA - Ative o programa para continuar")
        
        frame_hwid = ttk.LabelFrame(janela, text="ID do Computador", padding=10)
        frame_hwid.pack(fill=tk.X, padx=20, pady=10)
        
        hwid_text = tk.Entry(frame_hwid, font=('Courier', 10), justify='center')
        hwid_text.pack(fill=tk.X)
        hwid_text.insert(0, self.license_manager.hwid)
        hwid_text.config(state='readonly')
        
        btn_copiar = ttk.Button(frame_hwid, text="📋 Copiar HWID", 
                               command=lambda: self._copiar_hwid(hwid_text))
        btn_copiar.pack(pady=5)
        
        instrucoes = ttk.Label(janela, 
            text="1. Copie o HWID acima\n"
                 "2. Envie para: rcruzoe4@gmail.com\n"
                 "3. Aguarde o arquivo de licença\n"
                 "4. Selecione o arquivo abaixo",
            font=('Arial', 10))
        instrucoes.pack(pady=5)
        
        frame_ativar = ttk.LabelFrame(janela, text="Ativar Licença", padding=10)
        frame_ativar.pack(fill=tk.X, padx=20, pady=10)
        
        frame_arquivo = ttk.Frame(frame_ativar)
        frame_arquivo.pack(fill=tk.X, pady=5)
        
        self.entry_arquivo = ttk.Entry(frame_arquivo)
        self.entry_arquivo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        btn_buscar = ttk.Button(frame_arquivo, text="📂 Buscar", 
                               command=lambda: self._buscar_arquivo())
        btn_buscar.pack(side=tk.RIGHT, padx=5)
        
        btn_ativar = ttk.Button(frame_ativar, text="🔑 Ativar Licença", 
                               command=lambda: self._ativar_licenca(janela))
        btn_ativar.pack(pady=10)
        
        info_frame = ttk.Frame(janela)
        info_frame.pack(pady=10)
        
        ttk.Label(info_frame, text=f"Desenvolvedor: {DESENVOLVEDOR}", 
                 font=('Arial', 9)).pack()
        ttk.Label(info_frame, text=f"Contato: {EMAIL}", 
                 font=('Arial', 9)).pack()
        ttk.Label(info_frame, text=f"Versão: {VERSAO} | {ANO}", 
                 font=('Arial', 9)).pack()
        
        frame_botoes = ttk.Frame(janela)
        frame_botoes.pack(pady=15)
        
        btn_sair = ttk.Button(frame_botoes, text="✕ Sair", 
                             command=lambda: self._sair_sem_licenca(janela))
        btn_sair.pack(side=tk.LEFT, padx=5)
        
        btn_comprar = ttk.Button(frame_botoes, text="💰 Comprar Licença - R$ 297,00", 
                                command=lambda: self._comprar_licenca())
        btn_comprar.pack(side=tk.LEFT, padx=5)
        
        self.janela_ativacao = janela
        self.status_texto = status_texto
        
        janela.wait_window()
        return False
    
    def _copiar_hwid(self, entry):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.license_manager.hwid)
        messagebox.showinfo("Copiado", "HWID copiado para a área de transferência!")
    
    def _buscar_arquivo(self):
        arquivo = filedialog.askopenfilename(
            title="Selecione o arquivo de licença",
            filetypes=[("Arquivos de licença", "*.lic"), ("Todos os arquivos", "*.*")]
        )
        if arquivo:
            self.entry_arquivo.delete(0, tk.END)
            self.entry_arquivo.insert(0, arquivo)
    
    def _ativar_licenca(self, janela):
        arquivo = self.entry_arquivo.get().strip()
        if not arquivo:
            messagebox.showwarning("Aviso", "Selecione o arquivo de licença")
            return
        
        if not os.path.exists(arquivo):
            messagebox.showerror("Erro", "Arquivo não encontrado")
            return
        
        if self.license_manager.validar_licenca(arquivo):
            messagebox.showinfo("Sucesso", 
                f"🎉 {SOFTWARE} ativado com sucesso!\n\n"
                f"Desenvolvido por: {DESENVOLVEDOR}")
            janela.destroy()
            self.root.quit()
            self.root.destroy()
            os.execv(sys.executable, [sys.executable] + sys.argv)
        else:
            mensagens = {
                "HWID_INVALIDO": "❌ Esta licença não pertence a este computador",
                "EXPIRADA": "❌ Licença expirada",
                "REVOGADA": "❌ Licença revogada",
                "INVALIDO": "❌ Licença inválida",
                "ERRO": "❌ Erro na validação"
            }
            mensagem = mensagens.get(self.license_manager.tipo_licenca, "❌ Erro desconhecido")
            messagebox.showerror("Erro", mensagem)
    
    def _sair_sem_licenca(self, janela):
        if messagebox.askyesno("Confirmar", "Deseja realmente sair?"):
            janela.destroy()
            self.root.quit()
            sys.exit(0)
    
    def _comprar_licenca(self):
        webbrowser.open("https://topogeosys.com/comprar")
        messagebox.showinfo("Comprar Licença", 
            f"📞 Para adquirir sua licença:\n\n"
            f"📧 Envie um e-mail para: {EMAIL}\n"
            f"💰 Preço: R$ 297,00 (Licença Vitalícia)\n"
            f"✅ Inclui: Suporte e atualizações por 1 ano\n"
            f"👨‍💻 Desenvolvido por: {DESENVOLVEDOR}")
    
    # ============================================
    # CRIAÇÃO DA INTERFACE
    # ============================================
    
    def criar_interface(self):
        self.criar_menu()
        self.criar_toolbar()
        self.criar_status()
        self.criar_painel_entrada()
        self.criar_painel_metricas()
        self.criar_abas_principais()
        self.criar_rodape()
    
    def criar_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        arquivo_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='📁 Arquivo', menu=arquivo_menu)
        arquivo_menu.add_command(label='📄 Novo Projeto', command=self.novo_projeto, accelerator='Ctrl+N')
        arquivo_menu.add_command(label='📂 Abrir Projeto', command=self.abrir_projeto, accelerator='Ctrl+O')
        arquivo_menu.add_command(label='💾 Salvar Projeto', command=self.salvar_projeto, accelerator='Ctrl+S')
        arquivo_menu.add_separator()
        arquivo_menu.add_command(label='📥 Importar CSV', command=self.importar_csv)
        arquivo_menu.add_command(label='📤 Exportar CSV', command=self.exportar_csv)
        arquivo_menu.add_command(label='📐 Exportar DXF', command=self.exportar_dxf)
        arquivo_menu.add_separator()
        arquivo_menu.add_command(label='🖨️ Imprimir', command=self.imprimir)
        arquivo_menu.add_separator()
        arquivo_menu.add_command(label='❌ Sair', command=self.sair)
        
        editar_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='✏️ Editar', menu=editar_menu)
        editar_menu.add_command(label='🔧 Ajuste Bowditch', command=self.aplicar_ajuste)
        editar_menu.add_command(label='〰️ Gerar Curvas de Nível', command=self.gerar_curvas)
        editar_menu.add_separator()
        editar_menu.add_command(label='🗑️ Limpar Dados', command=self.limpar_dados)
        
        geo_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='🌍 Geo', menu=geo_menu)
        geo_menu.add_command(label='⚙️ Configurar Sistema', command=self.configurar_geo)
        geo_menu.add_command(label='📍 Coordenadas UTM', command=self.mostrar_utm)
        geo_menu.add_command(label='📊 Calcular Área', command=self.mostrar_area)
        
        relatorio_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='📊 Relatórios', menu=relatorio_menu)
        relatorio_menu.add_command(label='📋 Relatório Técnico', command=self.gerar_relatorio)
        relatorio_menu.add_command(label='📈 Gráfico da Planta', command=self.mostrar_grafico)
        relatorio_menu.add_command(label='📊 Estatísticas', command=self.mostrar_estatisticas)
        
        ajuda_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='❓ Ajuda', menu=ajuda_menu)
        ajuda_menu.add_command(label='📖 Manual do Usuário', command=self.mostrar_manual)
        ajuda_menu.add_command(label='📧 Contato', command=self.mostrar_contato)
        ajuda_menu.add_command(label='ℹ️ Sobre', command=self.mostrar_sobre)
    
    def criar_toolbar(self):
        """Cria a barra de ferramentas - CORRIGIDO"""
        toolbar = ttk.Frame(self.root, relief="raised", borderwidth=1)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)
        
        botoes = [
            ('📄 Novo', self.novo_projeto),
            ('📂 Abrir', self.abrir_projeto),
            ('💾 Salvar', self.salvar_projeto),
            ('|', None),
            ('➕ Adicionar', self.adicionar_estacao),
            ('🗑️ Remover', self.remover_ultima),
            ('|', None),
            ('🔧 Ajuste', self.aplicar_ajuste),
            ('〰️ Curvas', self.gerar_curvas),
            ('|', None),
            ('📊 Relatório', self.gerar_relatorio),
            ('📐 DXF', self.exportar_dxf)
        ]
        
        for texto, comando in botoes:
            if texto == '|':
                ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
            else:
                btn = ttk.Button(toolbar, text=texto, command=comando)
                btn.pack(side=tk.LEFT, padx=2)
        
        ttk.Label(toolbar, text=f"| {DESENVOLVEDOR} |").pack(side=tk.RIGHT, padx=5)
    
    def criar_status(self):
        self.status = ttk.Label(self.root, text='Pronto', relief=tk.SUNKEN, anchor=tk.W)
        self.status.pack(side=tk.BOTTOM, fill=tk.X)
    
    def criar_painel_entrada(self):
        frame = ttk.LabelFrame(self.root, text='📌 Adicionar Estação Topográfica', padding=10)
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(frame, text='ID:').grid(row=0, column=0, padx=5)
        self.entry_id = ttk.Entry(frame, width=10)
        self.entry_id.grid(row=0, column=1, padx=5)
        self.entry_id.focus()
        
        ttk.Label(frame, text='X (m):').grid(row=0, column=2, padx=5)
        self.entry_x = ttk.Entry(frame, width=12)
        self.entry_x.grid(row=0, column=3, padx=5)
        self.entry_x.insert(0, '0')
        
        ttk.Label(frame, text='Y (m):').grid(row=0, column=4, padx=5)
        self.entry_y = ttk.Entry(frame, width=12)
        self.entry_y.grid(row=0, column=5, padx=5)
        self.entry_y.insert(0, '0')
        
        ttk.Label(frame, text='Z (m):').grid(row=0, column=6, padx=5)
        self.entry_z = ttk.Entry(frame, width=12)
        self.entry_z.grid(row=0, column=7, padx=5)
        self.entry_z.insert(0, '0')
        
        ttk.Label(frame, text='Azimute (gr):').grid(row=1, column=0, padx=5, pady=5)
        self.entry_azimute = ttk.Entry(frame, width=12)
        self.entry_azimute.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text='Distância (m):').grid(row=1, column=2, padx=5, pady=5)
        self.entry_distancia = ttk.Entry(frame, width=12)
        self.entry_distancia.grid(row=1, column=3, padx=5, pady=5)
        
        ttk.Label(frame, text='Zenith (gr):').grid(row=1, column=4, padx=5, pady=5)
        self.entry_zenith = ttk.Entry(frame, width=12)
        self.entry_zenith.grid(row=1, column=5, padx=5, pady=5)
        self.entry_zenith.insert(0, '100')
        
        btn_adicionar = ttk.Button(frame, text='➕ Adicionar', command=self.adicionar_estacao)
        btn_adicionar.grid(row=1, column=6, padx=5, pady=5)
        
        btn_limpar = ttk.Button(frame, text='✖ Limpar', command=self.limpar_campos)
        btn_limpar.grid(row=1, column=7, padx=5, pady=5)
        
        dicas = ttk.Label(frame, 
            text="💡 Dica: Azimute em grados (0-400) | Zenith: 100 = horizontal | Use Enter para adicionar",
            font=('Arial', 9), foreground='#666')
        dicas.grid(row=2, column=0, columnspan=8, pady=5)
    
    def criar_painel_metricas(self):
        frame = ttk.Frame(self.root)
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.frame_area = ttk.LabelFrame(frame, text='📐 Área', padding=5)
        self.frame_area.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        self.label_area = ttk.Label(self.frame_area, text='0.000 m²', font=('Arial', 14, 'bold'))
        self.label_area.pack()
        
        self.frame_perimetro = ttk.LabelFrame(frame, text='📏 Perímetro', padding=5)
        self.frame_perimetro.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        self.label_perimetro = ttk.Label(self.frame_perimetro, text='0.000 m', font=('Arial', 14, 'bold'))
        self.label_perimetro.pack()
        
        self.frame_pontos = ttk.LabelFrame(frame, text='📍 Pontos', padding=5)
        self.frame_pontos.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        self.label_pontos = ttk.Label(self.frame_pontos, text='0', font=('Arial', 14, 'bold'))
        self.label_pontos.pack()
        
        self.frame_centroide = ttk.LabelFrame(frame, text='🎯 Centroide', padding=5)
        self.frame_centroide.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        self.label_centroide = ttk.Label(self.frame_centroide, text='X=0.000 Y=0.000', font=('Arial', 10))
        self.label_centroide.pack()
        
        self.frame_licenca = ttk.LabelFrame(frame, text='🔐 Licença', padding=5)
        self.frame_licenca.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        info = self.license_manager.get_info()
        if info['status'] == 'TRIAL':
            texto = f"🧪 Teste: {info.get('dias_restantes', 0)} dias"
        elif info['status'] == 'FULL':
            texto = "✅ Licença Vitalícia"
        else:
            texto = f"🔑 {info['status']}"
        
        self.label_licenca = ttk.Label(self.frame_licenca, text=texto, font=('Arial', 10))
        self.label_licenca.pack()
    
    def criar_abas_principais(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.tab_dados = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_dados, text='📋 Dados')
        self.criar_tabela_dados()
        
        self.tab_planta = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_planta, text='📍 Planta')
        self.criar_planta()
        
        self.tab_curvas = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_curvas, text='〰️ Curvas de Nível')
        self.criar_painel_curvas()
        
        self.tab_relatorio = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_relatorio, text='📊 Relatório')
        self.criar_painel_relatorio()
        
        self.tab_licenca = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_licenca, text='🔐 Licença')
        self.criar_painel_licenca()
    
    def criar_tabela_dados(self):
        frame = ttk.Frame(self.tab_dados)
        frame.pack(fill=tk.BOTH, expand=True)
        
        self.tree = ttk.Treeview(frame, columns=(
            'ID', 'X_Est', 'Y_Est', 'Z_Est', 'X_Ponto', 'Y_Ponto', 'Z_Ponto',
            'Azimute', 'Distancia', 'Zenith'
        ), show='headings', height=20)
        
        cabecalhos = [
            ('ID', 'ID', 60),
            ('X_Est', 'X Est.', 80),
            ('Y_Est', 'Y Est.', 80),
            ('Z_Est', 'Z Est.', 80),
            ('X_Ponto', 'X Ponto', 80),
            ('Y_Ponto', 'Y Ponto', 80),
            ('Z_Ponto', 'Z Ponto', 80),
            ('Azimute', 'Azimute', 80),
            ('Distancia', 'Dist.', 80),
            ('Zenith', 'Zenith', 80)
        ]
        
        for col, texto, largura in cabecalhos:
            self.tree.heading(col, text=texto)
            self.tree.column(col, width=largura, anchor='center')
        
        scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        frame_botoes = ttk.Frame(self.tab_dados)
        frame_botoes.pack(fill=tk.X, pady=5)
        
        ttk.Button(frame_botoes, text='🗑️ Remover Selecionado', 
                  command=self.remover_selecionado).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_botoes, text='📋 Copiar Dados', 
                  command=self.copiar_dados).pack(side=tk.LEFT, padx=5)
    
    def criar_planta(self):
        if not BIBLIOTECAS_OK:
            label = ttk.Label(self.tab_planta, 
                text="⚠️ Bibliotecas não instaladas.\nExecute: pip install pandas numpy matplotlib",
                font=('Arial', 12))
            label.pack(expand=True)
            return
        
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title('Planta Topográfica')
        self.ax.set_xlabel('X (m)')
        self.ax.set_ylabel('Y (m)')
        self.ax.grid(True, alpha=0.3)
        
        self.canvas = FigureCanvasTkAgg(self.fig, self.tab_planta)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        toolbar = NavigationToolbar2Tk(self.canvas, self.tab_planta)
        toolbar.update()
    
    def criar_painel_curvas(self):
        frame = ttk.Frame(self.tab_curvas)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        frame_controles = ttk.Frame(frame)
        frame_controles.pack(fill=tk.X, pady=5)
        
        ttk.Label(frame_controles, text='Intervalo (m):').pack(side=tk.LEFT, padx=5)
        self.entry_intervalo = ttk.Entry(frame_controles, width=10)
        self.entry_intervalo.pack(side=tk.LEFT, padx=5)
        self.entry_intervalo.insert(0, '1')
        
        ttk.Button(frame_controles, text='〰️ Gerar Curvas', 
                  command=self.gerar_curvas).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(frame_controles, text='🗑️ Limpar Curvas', 
                  command=self.limpar_curvas).pack(side=tk.LEFT, padx=5)
        
        self.lista_curvas = tk.Listbox(frame, height=15)
        self.lista_curvas.pack(fill=tk.BOTH, expand=True, pady=5)
    
    def criar_painel_relatorio(self):
        frame = ttk.Frame(self.tab_relatorio)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        frame_botoes = ttk.Frame(frame)
        frame_botoes.pack(fill=tk.X, pady=5)
        
        ttk.Button(frame_botoes, text='📋 Gerar Relatório', 
                  command=self.gerar_relatorio).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_botoes, text='💾 Salvar Relatório', 
                  command=self.salvar_relatorio).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_botoes, text='📋 Copiar', 
                  command=self.copiar_relatorio).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_botoes, text='🖨️ Imprimir', 
                  command=self.imprimir_relatorio).pack(side=tk.LEFT, padx=5)
        
        self.texto_relatorio = scrolledtext.ScrolledText(frame, height=20, font=('Courier', 10))
        self.texto_relatorio.pack(fill=tk.BOTH, expand=True)
    
    def criar_painel_licenca(self):
        frame = ttk.Frame(self.tab_licenca)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        ttk.Label(frame, text="🔐 INFORMAÇÕES DA LICENÇA", 
                 font=('Arial', 16, 'bold')).pack(pady=10)
        
        info = self.license_manager.get_info()
        
        infos = [
            ("Software", SOFTWARE),
            ("Versão", VERSAO),
            ("Desenvolvedor", DESENVOLVEDOR),
            ("Contato", EMAIL),
            ("Status", info['status']),
            ("HWID", info['hwid'])
        ]
        
        if info.get('usuario'):
            infos.append(("Usuário", info['usuario']))
        if info.get('valida_ate'):
            infos.append(("Válido até", info['valida_ate'][:10]))
        if info.get('dias_restantes') is not None and info['status'] == 'TRIAL':
            infos.append(("Dias restantes", str(info['dias_restantes'])))
        
        for i, (chave, valor) in enumerate(infos):
            row = ttk.Frame(frame)
            row.pack(fill=tk.X, pady=3)
            
            ttk.Label(row, text=f"{chave}:", font=('Arial', 10, 'bold'), width=15).pack(side=tk.LEFT)
            ttk.Label(row, text=valor, font=('Arial', 10)).pack(side=tk.LEFT)
        
        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)
        
        frame_botoes = ttk.Frame(frame)
        frame_botoes.pack(pady=10)
        
        ttk.Button(frame_botoes, text="📋 Copiar HWID", 
                  command=lambda: self._copiar_hwid_info()).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(frame_botoes, text="📧 Contatar Desenvolvedor", 
                  command=self.mostrar_contato).pack(side=tk.LEFT, padx=5)
        
        if info['status'] == 'TRIAL':
            ttk.Button(frame_botoes, text="💰 Comprar Licença", 
                      command=self._comprar_licenca).pack(side=tk.LEFT, padx=5)
    
    def criar_rodape(self):
        rodape = ttk.Label(self.root, 
            text=f"© {ANO} {SOFTWARE} - Desenvolvido por {DESENVOLVEDOR} | {EMAIL}",
            font=('Arial', 8), foreground='#666')
        rodape.pack(side=tk.BOTTOM, pady=2)
    
    def _copiar_hwid_info(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.license_manager.hwid)
        self.atualizar_status("HWID copiado para área de transferência!")
        messagebox.showinfo("Copiado", "HWID copiado com sucesso!")
    
    # ============================================
    # FUNÇÕES DE CÁLCULO
    # ============================================
    
    def adicionar_estacao(self):
        try:
            id_estacao = self.entry_id.get().strip()
            if not id_estacao:
                messagebox.showwarning('Aviso', 'Informe o ID da estação')
                return
            
            x = float(self.entry_x.get())
            y = float(self.entry_y.get())
            z = float(self.entry_z.get())
            azimute = float(self.entry_azimute.get())
            distancia = float(self.entry_distancia.get())
            zenith = float(self.entry_zenith.get())
            
            if distancia <= 0:
                messagebox.showwarning('Aviso', 'Distância deve ser maior que 0')
                return
            
            if azimute < 0 or azimute > 400:
                messagebox.showwarning('Aviso', 'Azimute deve estar entre 0 e 400 grados')
                return
            
            import math
            angulo_rad = math.radians(azimute * 0.9)
            zenith_rad = math.radians(zenith * 0.9)
            
            dist_horizontal = distancia * math.sin(zenith_rad)
            dz = distancia * math.cos(zenith_rad)
            
            px = x + dist_horizontal * math.sin(angulo_rad)
            py = y + dist_horizontal * math.cos(angulo_rad)
            pz = z + dz
            
            estacao = {
                'id': id_estacao,
                'x': x,
                'y': y,
                'z': z,
                'azimute': azimute,
                'distancia': distancia,
                'zenith': zenith
            }
            
            ponto = {
                'x': px,
                'y': py,
                'z': pz,
                'estacao_id': id_estacao
            }
            
            self.projeto['estacoes'].append(estacao)
            self.projeto['pontos'].append(ponto)
            self.contador_pontos += 1
            
            self.entry_id.delete(0, tk.END)
            self.entry_azimute.delete(0, tk.END)
            self.entry_distancia.delete(0, tk.END)
            self.entry_id.focus()
            
            self.atualizar_interface()
            self.atualizar_status(f'Ponto {id_estacao} adicionado! X={px:.3f}, Y={py:.3f}, Z={pz:.3f}')
            
        except ValueError as e:
            messagebox.showerror('Erro', f'Valor inválido: {e}')
    
    def remover_ultima(self):
        if not self.projeto['estacoes']:
            messagebox.showwarning('Aviso', 'Nenhuma estação para remover')
            return
        
        ultima = self.projeto['estacoes'][-1]['id']
        if messagebox.askyesno('Confirmar', f'Remover estação "{ultima}"?'):
            self.projeto['estacoes'].pop()
            self.projeto['pontos'].pop()
            self.contador_pontos -= 1
            self.atualizar_interface()
            self.atualizar_status(f'Estação {ultima} removida')
    
    def remover_selecionado(self):
        selecionado = self.tree.selection()
        if not selecionado:
            messagebox.showwarning('Aviso', 'Selecione um item para remover')
            return
        
        index = self.tree.index(selecionado[0])
        if index < len(self.projeto['estacoes']):
            id_estacao = self.projeto['estacoes'][index]['id']
            if messagebox.askyesno('Confirmar', f'Remover estação "{id_estacao}"?'):
                self.projeto['estacoes'].pop(index)
                self.projeto['pontos'].pop(index)
                self.contador_pontos -= 1
                self.atualizar_interface()
                self.atualizar_status(f'Estação {id_estacao} removida')
    
    def limpar_campos(self):
        self.entry_id.delete(0, tk.END)
        self.entry_x.delete(0, tk.END)
        self.entry_x.insert(0, '0')
        self.entry_y.delete(0, tk.END)
        self.entry_y.insert(0, '0')
        self.entry_z.delete(0, tk.END)
        self.entry_z.insert(0, '0')
        self.entry_azimute.delete(0, tk.END)
        self.entry_distancia.delete(0, tk.END)
        self.entry_zenith.delete(0, tk.END)
        self.entry_zenith.insert(0, '100')
        self.entry_id.focus()
    
    # ============================================
    # CÁLCULOS TOPOGRÁFICOS
    # ============================================
    
    def calcular_area(self):
        pontos = self.projeto['pontos']
        n = len(pontos)
        if n < 3:
            return 0
        
        area = 0
        for i in range(n - 1):
            area += pontos[i]['x'] * pontos[i+1]['y'] - pontos[i+1]['x'] * pontos[i]['y']
        return abs(area) / 2
    
    def calcular_perimetro(self):
        pontos = self.projeto['pontos']
        n = len(pontos)
        if n < 2:
            return 0
        
        perimetro = 0
        for i in range(n - 1):
            dx = pontos[i+1]['x'] - pontos[i]['x']
            dy = pontos[i+1]['y'] - pontos[i]['y']
            perimetro += math.sqrt(dx*dx + dy*dy)
        return perimetro
    
    def calcular_centroide(self):
        pontos = self.projeto['pontos']
        n = len(pontos)
        if n < 2:
            return {'x': 0, 'y': 0}
        
        sx = sum(p['x'] for p in pontos)
        sy = sum(p['y'] for p in pontos)
        return {'x': sx / n, 'y': sy / n}
    
    def aplicar_ajuste(self):
        import math
        estacoes = self.projeto['estacoes']
        pontos = self.projeto['pontos']
        n = len(estacoes)
        
        if n < 3:
            messagebox.showwarning('Aviso', 'Mínimo 3 pontos para ajuste')
            return
        
        if not messagebox.askyesno('Confirmar', 'Aplicar ajuste de Bowditch?'):
            return
        
        erro_x = 0
        erro_y = 0
        perimetro_total = 0
        
        for i in range(n - 1):
            dx = pontos[i+1]['x'] - pontos[i]['x']
            dy = pontos[i+1]['y'] - pontos[i]['y']
            erro_x += dx
            erro_y += dy
            perimetro_total += math.sqrt(dx*dx + dy*dy)
        
        erro_linear = math.sqrt(erro_x*erro_x + erro_y*erro_y)
        
        if perimetro_total == 0:
            messagebox.showerror('Erro', 'Perímetro total zero')
            return
        
        for i in range(n - 1):
            dist = math.sqrt(
                (pontos[i+1]['x'] - pontos[i]['x'])**2 +
                (pontos[i+1]['y'] - pontos[i]['y'])**2
            )
            correcao_x = -erro_x * (dist / perimetro_total)
            correcao_y = -erro_y * (dist / perimetro_total)
            
            pontos[i+1]['x'] += correcao_x
            pontos[i+1]['y'] += correcao_y
            
            if i + 1 < len(estacoes):
                estacoes[i+1]['x'] = pontos[i+1]['x']
                estacoes[i+1]['y'] = pontos[i+1]['y']
        
        self.projeto['ajustes']['aplicado'] = True
        self.projeto['ajustes']['erro_linear'] = erro_linear
        
        self.atualizar_interface()
        messagebox.showinfo('Sucesso', 
            f'Ajuste Bowditch aplicado!\nErro final: {erro_linear:.4f} m')
        self.atualizar_status(f'Ajuste aplicado. Erro: {erro_linear:.4f}m')
    
    def gerar_curvas(self):
        import math
        pontos = self.projeto['pontos']
        if len(pontos) < 3:
            messagebox.showwarning('Aviso', 'Mínimo 3 pontos para curvas')
            return
        
        try:
            intervalo = float(self.entry_intervalo.get())
            if intervalo <= 0:
                raise ValueError
        except:
            messagebox.showerror('Erro', 'Intervalo inválido')
            return
        
        z_min = min(p['z'] for p in pontos)
        z_max = max(p['z'] for p in pontos)
        
        curvas = []
        z_inicio = math.floor(z_min / intervalo) * intervalo
        z_fim = math.ceil(z_max / intervalo) * intervalo
        
        for z in range(int(z_inicio + intervalo), int(z_fim), int(intervalo)):
            curva = {'nivel': z, 'pontos': []}
            
            for i in range(len(pontos) - 1):
                p1 = pontos[i]
                p2 = pontos[i+1]
                
                if (p1['z'] <= z <= p2['z']) or (p2['z'] <= z <= p1['z']):
                    if p2['z'] != p1['z']:
                        t = (z - p1['z']) / (p2['z'] - p1['z'])
                        curva['pontos'].append({
                            'x': p1['x'] + t * (p2['x'] - p1['x']),
                            'y': p1['y'] + t * (p2['y'] - p1['y'])
                        })
            
            if curva['pontos']:
                curvas.append(curva)
        
        self.projeto['curvas'] = curvas
        self.contador_curvas = len(curvas)
        
        self.lista_curvas.delete(0, tk.END)
        for curva in curvas:
            self.lista_curvas.insert(tk.END, 
                f'Nível {curva["nivel"]:.2f}m - {len(curva["pontos"])} pontos')
        
        messagebox.showinfo('Sucesso', f'{len(curvas)} curvas geradas!')
        self.atualizar_status(f'{len(curvas)} curvas de nível geradas')
        self.atualizar_interface()
    
    def limpar_curvas(self):
        if self.projeto['curvas']:
            if messagebox.askyesno('Confirmar', 'Limpar todas as curvas?'):
                self.projeto['curvas'] = []
                self.lista_curvas.delete(0, tk.END)
                self.atualizar_status('Curvas removidas')
                self.atualizar_interface()
    
    # ============================================
    # GEORREFERENCIAMENTO
    # ============================================
    
    def configurar_geo(self):
        geo = self.projeto['georreferenciamento']
        
        janela = tk.Toplevel(self.root)
        janela.title('Georreferenciamento')
        janela.geometry('400x300')
        janela.transient(self.root)
        
        ttk.Label(janela, text='Sistema:').grid(row=0, column=0, padx=10, pady=10)
        entry_sistema = ttk.Entry(janela, width=30)
        entry_sistema.grid(row=0, column=1, padx=10, pady=10)
        entry_sistema.insert(0, geo['sistema'])
        
        ttk.Label(janela, text='Fuso UTM:').grid(row=1, column=0, padx=10, pady=10)
        entry_fuso = ttk.Entry(janela, width=30)
        entry_fuso.grid(row=1, column=1, padx=10, pady=10)
        entry_fuso.insert(0, str(geo['fuso']))
        
        ttk.Label(janela, text='Datum:').grid(row=2, column=0, padx=10, pady=10)
        entry_datum = ttk.Entry(janela, width=30)
        entry_datum.grid(row=2, column=1, padx=10, pady=10)
        entry_datum.insert(0, geo['datum'])
        
        def salvar_geo():
            try:
                geo['sistema'] = entry_sistema.get()
                geo['fuso'] = int(entry_fuso.get())
                geo['datum'] = entry_datum.get()
                janela.destroy()
                self.atualizar_status('Georreferenciamento atualizado')
                messagebox.showinfo('Sucesso', 'Configurações salvas!')
            except ValueError:
                messagebox.showerror('Erro', 'Fuso deve ser um número')
        
        ttk.Button(janela, text='💾 Salvar', command=salvar_geo).grid(row=3, column=0, columnspan=2, pady=20)
    
    def mostrar_utm(self):
        if not self.projeto['pontos']:
            messagebox.showwarning('Aviso', 'Nenhum ponto para converter')
            return
        
        geo = self.projeto['georreferenciamento']
        fator = 0.9996
        meridiano_central = -45 + (geo['fuso'] - 22) * 6
        
        texto = 'COORDENADAS UTM\n'
        texto += '=' * 60 + '\n'
        texto += f'Sistema: {geo["sistema"]}\n'
        texto += f'Fuso: {geo["fuso"]}\n'
        texto += f'Meridiano Central: {meridiano_central}°\n'
        texto += '=' * 60 + '\n\n'
        
        for i, p in enumerate(self.projeto['pontos']):
            x_utm = 500000 + p['x'] * fator
            y_utm = 10000000 + p['y'] * fator
            
            texto += f'P{i+1}:\n'
            texto += f'  X: {x_utm:.3f} m\n'
            texto += f'  Y: {y_utm:.3f} m\n\n'
        
        janela = tk.Toplevel(self.root)
        janela.title('Coordenadas UTM')
        janela.geometry('500x400')
        
        text_widget = scrolledtext.ScrolledText(janela, font=('Courier', 10))
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert('1.0', texto)
        text_widget.config(state=tk.DISABLED)
        
        ttk.Button(janela, text='📋 Copiar', 
            command=lambda: [janela.clipboard_clear(), janela.clipboard_append(texto)]).pack(pady=5)
    
    def mostrar_area(self):
        area = self.calcular_area()
        perimetro = self.calcular_perimetro()
        centroide = self.calcular_centroide()
        
        texto = f"""
📐 CÁLCULO DE ÁREA
{'=' * 40}

Área: {area:.3f} m²
Perímetro: {perimetro:.3f} m
Centroide: X={centroide['x']:.3f}, Y={centroide['y']:.3f}
Número de pontos: {len(self.projeto['pontos'])}

Desenvolvido por: {DESENVOLVEDOR}
        """
        messagebox.showinfo('📐 Área Calculada', texto)
    
    # ============================================
    # EXPORTAÇÕES
    # ============================================
    
    def exportar_csv(self):
        if not self.projeto['estacoes']:
            messagebox.showwarning('Aviso', 'Nenhum dado para exportar')
            return
        
        arquivo = filedialog.asksaveasfilename(
            defaultextension='.csv',
            filetypes=[('CSV files', '*.csv'), ('All files', '*.*')]
        )
        
        if not arquivo:
            return
        
        try:
            import csv
            with open(arquivo, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['ID', 'X_Est', 'Y_Est', 'Z_Est', 'X_Ponto', 'Y_Ponto', 'Z_Ponto',
                                'Azimute', 'Distancia', 'Zenith'])
                
                for i, e in enumerate(self.projeto['estacoes']):
                    p = self.projeto['pontos'][i]
                    writer.writerow([
                        e['id'], e['x'], e['y'], e['z'],
                        p['x'], p['y'], p['z'],
                        e['azimute'], e['distancia'], e['zenith']
                    ])
            
            messagebox.showinfo('Sucesso', f'Dados exportados para:\n{arquivo}')
            self.atualizar_status(f'CSV exportado: {os.path.basename(arquivo)}')
            
        except Exception as e:
            messagebox.showerror('Erro', f'Erro ao exportar: {e}')
    
    def importar_csv(self):
        arquivo = filedialog.askopenfilename(
            filetypes=[('CSV files', '*.csv'), ('All files', '*.*')]
        )
        
        if not arquivo:
            return
        
        try:
            import csv
            with open(arquivo, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                self.projeto['estacoes'] = []
                self.projeto['pontos'] = []
                self.contador_pontos = 0
                
                for row in reader:
                    estacao = {
                        'id': row['ID'],
                        'x': float(row['X_Est']),
                        'y': float(row['Y_Est']),
                        'z': float(row['Z_Est']),
                        'azimute': float(row['Azimute']),
                        'distancia': float(row['Distancia']),
                        'zenith': float(row['Zenith'])
                    }
                    
                    ponto = {
                        'x': float(row['X_Ponto']),
                        'y': float(row['Y_Ponto']),
                        'z': float(row['Z_Ponto']),
                        'estacao_id': row['ID']
                    }
                    
                    self.projeto['estacoes'].append(estacao)
                    self.projeto['pontos'].append(ponto)
                    self.contador_pontos += 1
            
            self.atualizar_interface()
            messagebox.showinfo('Sucesso', f'Importados {len(self.projeto["estacoes"])} pontos!')
            self.atualizar_status(f'CSV importado: {os.path.basename(arquivo)}')
            
        except Exception as e:
            messagebox.showerror('Erro', f'Erro ao importar: {e}')
    
    def exportar_dxf(self):
        if not self.projeto['pontos']:
            messagebox.showwarning('Aviso', 'Nenhum ponto para exportar')
            return
        
        arquivo = filedialog.asksaveasfilename(
            defaultextension='.dxf',
            filetypes=[('DXF files', '*.dxf'), ('All files', '*.*')]
        )
        
        if not arquivo:
            return
        
        try:
            with open(arquivo, 'w') as f:
                f.write('0\nSECTION\n2\nHEADER\n0\nENDSEC\n')
                f.write('0\nSECTION\n2\nENTITIES\n')
                
                pontos = self.projeto['pontos']
                
                for i in range(len(pontos) - 1):
                    f.write('0\nLINE\n8\nPOLIGONAL\n')
                    f.write(f'10\n{pontos[i]["x"]:.3f}\n')
                    f.write(f'20\n{pontos[i]["y"]:.3f}\n')
                    f.write(f'11\n{pontos[i+1]["x"]:.3f}\n')
                    f.write(f'21\n{pontos[i+1]["y"]:.3f}\n')
                
                if len(pontos) > 2:
                    f.write('0\nLINE\n8\nPOLIGONAL\n')
                    f.write(f'10\n{pontos[-1]["x"]:.3f}\n')
                    f.write(f'20\n{pontos[-1]["y"]:.3f}\n')
                    f.write(f'11\n{pontos[0]["x"]:.3f}\n')
                    f.write(f'21\n{pontos[0]["y"]:.3f}\n')
                
                for i, p in enumerate(pontos):
                    f.write('0\nPOINT\n8\nPONTOS\n')
                    f.write(f'10\n{p["x"]:.3f}\n')
                    f.write(f'20\n{p["y"]:.3f}\n')
                    if 'z' in p:
                        f.write(f'30\n{p["z"]:.3f}\n')
                
                f.write('0\nENDSEC\n0\nEOF\n')
            
            messagebox.showinfo('Sucesso', f'DXF exportado para:\n{arquivo}')
            self.atualizar_status(f'DXF exportado: {os.path.basename(arquivo)}')
            
        except Exception as e:
            messagebox.showerror('Erro', f'Erro ao exportar: {e}')
    
    # ============================================
    # RELATÓRIOS
    # ============================================
    
    def gerar_relatorio(self):
        if not self.projeto['estacoes']:
            messagebox.showwarning('Aviso', 'Nenhum dado para relatório')
            return
        
        texto = []
        texto.append('=' * 70)
        texto.append(f'  {SOFTWARE} - RELATÓRIO TÉCNICO')
        texto.append('=' * 70)
        texto.append('')
        texto.append(f'PROJETO: {self.projeto["nome"]}')
        texto.append(f'DATA: {datetime.datetime.now().strftime("%d/%m/%Y %H:%M")}')
        texto.append(f'DESENVOLVEDOR: {DESENVOLVEDOR}')
        texto.append(f'CONTATO: {EMAIL}')
        texto.append('')
        texto.append('-' * 70)
        texto.append('DADOS DE CAMPO')
        texto.append('-' * 70)
        texto.append('')
        texto.append('ID    | X Est.  | Y Est.  | Z Est.  | X Ponto | Y Ponto | Z Ponto | Azimute | Distância')
        texto.append('-' * 70)
        
        for i, e in enumerate(self.projeto['estacoes']):
            p = self.projeto['pontos'][i]
            texto.append(
                f'{e["id"]:5} | '
                f'{e["x"]:8.3f} | '
                f'{e["y"]:8.3f} | '
                f'{e["z"]:8.3f} | '
                f'{p["x"]:8.3f} | '
                f'{p["y"]:8.3f} | '
                f'{p["z"]:8.3f} | '
                f'{e["azimute"]:8.2f} | '
                f'{e["distancia"]:9.3f}'
            )
        
        area = self.calcular_area()
        perimetro = self.calcular_perimetro()
        centroide = self.calcular_centroide()
        
        texto.append('')
        texto.append('-' * 70)
        texto.append('MÉTRICAS')
        texto.append('-' * 70)
        texto.append(f'Área: {area:.3f} m²')
        texto.append(f'Perímetro: {perimetro:.3f} m')
        texto.append(f'Pontos: {len(self.projeto["pontos"])}')
        texto.append(f'Centroide: X={centroide["x"]:.3f}, Y={centroide["y"]:.3f}')
        
        if self.projeto['ajustes']['aplicado']:
            texto.append(f'Ajuste aplicado: Bowditch (Erro: {self.projeto["ajustes"]["erro_linear"]:.4f}m)')
        
        if self.projeto['curvas']:
            texto.append('')
            texto.append('-' * 70)
            texto.append('CURVAS DE NÍVEL')
            texto.append('-' * 70)
            for curva in self.projeto['curvas']:
                texto.append(f'Nível {curva["nivel"]:.2f}m: {len(curva["pontos"])} pontos')
        
        geo = self.projeto['georreferenciamento']
        texto.append('')
        texto.append('-' * 70)
        texto.append('GEORREFERENCIAMENTO')
        texto.append('-' * 70)
        texto.append(f'Sistema: {geo["sistema"]}')
        texto.append(f'Fuso: {geo["fuso"]}')
        texto.append(f'Datum: {geo["datum"]}')
        
        info = self.license_manager.get_info()
        texto.append('')
        texto.append('-' * 70)
        texto.append('LICENÇA')
        texto.append('-' * 70)
        texto.append(f'Status: {info["status"]}')
        if info.get('usuario'):
            texto.append(f'Usuário: {info["usuario"]}')
        if info.get('valida_ate'):
            texto.append(f'Válido até: {info["valida_ate"][:10]}')
        
        texto.append('')
        texto.append('=' * 70)
        texto.append(f'  {SOFTWARE} v{VERSAO} - Desenvolvido por {DESENVOLVEDOR}')
        texto.append(f'  Contato: {EMAIL}')
        texto.append('=' * 70)
        
        texto_final = '\n'.join(texto)
        
        self.texto_relatorio.delete('1.0', tk.END)
        self.texto_relatorio.insert('1.0', texto_final)
        self.notebook.select(self.tab_relatorio)
        
        self.atualizar_status('Relatório gerado')
    
    def salvar_relatorio(self):
        texto = self.texto_relatorio.get('1.0', tk.END)
        if not texto.strip():
            messagebox.showwarning('Aviso', 'Gere um relatório primeiro')
            return
        
        arquivo = filedialog.asksaveasfilename(
            defaultextension='.txt',
            filetypes=[('Text files', '*.txt'), ('All files', '*.*')]
        )
        
        if arquivo:
            with open(arquivo, 'w', encoding='utf-8') as f:
                f.write(texto)
            messagebox.showinfo('Sucesso', f'Relatório salvo em:\n{arquivo}')
    
    def copiar_relatorio(self):
        texto = self.texto_relatorio.get('1.0', tk.END)
        if texto.strip():
            self.root.clipboard_clear()
            self.root.clipboard_append(texto)
            self.atualizar_status('Relatório copiado para área de transferência')
    
    def imprimir_relatorio(self):
        texto = self.texto_relatorio.get('1.0', tk.END)
        if not texto.strip():
            messagebox.showwarning('Aviso', 'Gere um relatório primeiro')
            return
        
        janela = tk.Toplevel(self.root)
        janela.title('Impressão')
        janela.geometry('600x500')
        
        text = scrolledtext.ScrolledText(janela, font=('Courier', 10))
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text.insert('1.0', texto)
        text.config(state=tk.DISABLED)
        
        ttk.Button(janela, text='🖨️ Imprimir', 
            command=lambda: text.event_generate('<<Print>>')).pack(pady=5)
    
    # ============================================
    # ESTATÍSTICAS
    # ============================================
    
    def mostrar_estatisticas(self):
        n = len(self.projeto['pontos'])
        if n == 0:
            messagebox.showinfo('Estatísticas', 'Nenhum ponto cadastrado')
            return
        
        xs = [p['x'] for p in self.projeto['pontos']]
        ys = [p['y'] for p in self.projeto['pontos']]
        zs = [p['z'] for p in self.projeto['pontos']]
        
        stats = f"""
📊 ESTATÍSTICAS DO PROJETO
{'=' * 50}

Total de pontos: {n}
Total de estações: {len(self.projeto['estacoes'])}

COORDENADAS X:
  Mínimo: {min(xs):.3f}
  Máximo: {max(xs):.3f}
  Média: {sum(xs)/n:.3f}
  Amplitude: {max(xs) - min(xs):.3f}

COORDENADAS Y:
  Mínimo: {min(ys):.3f}
  Máximo: {max(ys):.3f}
  Média: {sum(ys)/n:.3f}
  Amplitude: {max(ys) - min(ys):.3f}

COORDENADAS Z:
  Mínimo: {min(zs):.3f}
  Máximo: {max(zs):.3f}
  Média: {sum(zs)/n:.3f}
  Amplitude: {max(zs) - min(zs):.3f}

Área: {self.calcular_area():.3f} m²
Perímetro: {self.calcular_perimetro():.3f} m

Curvas de nível: {len(self.projeto['curvas'])}
Ajuste aplicado: {'Sim' if self.projeto['ajustes']['aplicado'] else 'Não'}

{SOFTWARE} v{VERSAO} - {DESENVOLVEDOR}
"""
        messagebox.showinfo('📊 Estatísticas', stats)
    
    # ============================================
    # GRÁFICO
    # ============================================
    
    def mostrar_grafico(self):
        if not BIBLIOTECAS_OK:
            messagebox.showwarning('Aviso', 'Bibliotecas não instaladas')
            return
        
        if not self.projeto['pontos']:
            messagebox.showwarning('Aviso', 'Nenhum ponto para plotar')
            return
        
        fig = Figure(figsize=(10, 8))
        ax = fig.add_subplot(111)
        
        pontos = self.projeto['pontos']
        xs = [p['x'] for p in pontos]
        ys = [p['y'] for p in pontos]
        
        ax.plot(xs, ys, 'b-', linewidth=2, label='Poligonal')
        ax.plot([xs[-1], xs[0]], [ys[-1], ys[0]], 'b-', linewidth=2)
        ax.plot(xs, ys, 'ro', markersize=8, label='Pontos')
        
        for i, p in enumerate(pontos):
            estacao = self.projeto['estacoes'][i] if i < len(self.projeto['estacoes']) else None
            label = estacao['id'] if estacao else f'P{i+1}'
            ax.annotate(label, (p['x'], p['y']), 
                       xytext=(5, 5), textcoords='offset points',
                       fontsize=10, fontweight='bold')
        
        ax.set_title(f'Planta Topográfica - {self.projeto["nome"]}')
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')
        ax.grid(True, alpha=0.3)
        ax.axis('equal')
        ax.legend()
        
        area = self.calcular_area()
        ax.text(0.02, 0.98, f'Área: {area:.2f} m²', 
               transform=ax.transAxes, fontsize=12,
               verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        ax.text(0.98, 0.02, f'{SOFTWARE} - {DESENVOLVEDOR}', 
               transform=ax.transAxes, fontsize=8,
               horizontalalignment='right',
               verticalalignment='bottom',
               color='#666')
        
        plt.show()
    
    # ============================================
    # PROJETO
    # ============================================
    
    def novo_projeto(self):
        if self.projeto['estacoes']:
            if not messagebox.askyesno('Confirmar', 'Descartar dados atuais?'):
                return
        
        self.projeto = {
            'nome': f'Projeto {datetime.datetime.now().strftime("%d/%m/%Y")}',
            'descricao': '',
            'data_criacao': datetime.datetime.now().isoformat(),
            'ultima_modificacao': datetime.datetime.now().isoformat(),
            'estacoes': [],
            'pontos': [],
            'curvas': [],
            'poligonais': [],
            'ajustes': {'aplicado': False, 'metodo': 'Bowditch', 'erro_linear': 0, 'erro_angular': 0},
            'georreferenciamento': {
                'sistema': 'SIRGAS 2000',
                'fuso': 22,
                'meridiano_central': -45,
                'fator_escala': 0.9996,
                'datum': 'SIRGAS2000',
                'origem_x': 500000,
                'origem_y': 10000000
            },
            'area': 0,
            'perimetro': 0,
            'centroide': {'x': 0, 'y': 0}
        }
        
        self.contador_pontos = 0
        self.contador_curvas = 0
        
        self.limpar_campos()
        self.atualizar_interface()
        self.atualizar_status('Novo projeto criado')
    
    def salvar_projeto(self):
        arquivo = filedialog.asksaveasfilename(
            defaultextension='.topo',
            filetypes=[('TopoGeoSys Project', '*.topo'), ('All files', '*.*')]
        )
        
        if not arquivo:
            return
        
        try:
            dados = {
                'projeto': self.projeto,
                'config': self.config,
                'contador': self.contador_pontos,
                'versao': VERSAO,
                'desenvolvedor': DESENVOLVEDOR
            }
            
            with open(arquivo, 'w', encoding='utf-8') as f:
                json.dump(dados, f, indent=2, ensure_ascii=False)
            
            messagebox.showinfo('Sucesso', f'Projeto salvo em:\n{arquivo}')
            self.atualizar_status(f'Projeto salvo: {os.path.basename(arquivo)}')
            
        except Exception as e:
            messagebox.showerror('Erro', f'Erro ao salvar: {e}')
    
    def abrir_projeto(self):
        arquivo = filedialog.askopenfilename(
            filetypes=[('TopoGeoSys Project', '*.topo'), ('All files', '*.*')]
        )
        
        if not arquivo:
            return
        
        try:
            with open(arquivo, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            
            self.projeto = dados['projeto']
            self.config = dados.get('config', self.config)
            self.contador_pontos = dados.get('contador', 0)
            
            self.atualizar_interface()
            messagebox.showinfo('Sucesso', f'Projeto carregado:\n{arquivo}')
            self.atualizar_status(f'Projeto carregado: {os.path.basename(arquivo)}')
            
        except Exception as e:
            messagebox.showerror('Erro', f'Erro ao carregar: {e}')
    
    def carregar_ultimo_projeto(self):
        try:
            if os.path.exists('ultimo_projeto.topo'):
                with open('ultimo_projeto.topo', 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                self.projeto = dados['projeto']
                self.contador_pontos = dados.get('contador', 0)
                self.atualizar_interface()
        except:
            pass
    
    def limpar_dados(self):
        if not self.projeto['estacoes']:
            return
        
        if messagebox.askyesno('Confirmar', 'Limpar todos os dados?'):
            self.projeto['estacoes'] = []
            self.projeto['pontos'] = []
            self.projeto['curvas'] = []
            self.contador_pontos = 0
            self.contador_curvas = 0
            self.lista_curvas.delete(0, tk.END)
            self.atualizar_interface()
            self.atualizar_status('Dados limpos')
    
    # ============================================
    # INTERFACE - ATUALIZAÇÃO
    # ============================================
    
    def atualizar_interface(self):
        self.atualizar_tabela()
        self.atualizar_metricas()
        self.atualizar_planta()
        self.atualizar_curvas()
        self.atualizar_licenca()
    
    def atualizar_tabela(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for i, e in enumerate(self.projeto['estacoes']):
            p = self.projeto['pontos'][i]
            self.tree.insert('', 'end', values=(
                e['id'],
                f'{e["x"]:.3f}',
                f'{e["y"]:.3f}',
                f'{e["z"]:.3f}',
                f'{p["x"]:.3f}',
                f'{p["y"]:.3f}',
                f'{p["z"]:.3f}',
                f'{e["azimute"]:.2f}',
                f'{e["distancia"]:.3f}',
                f'{e["zenith"]:.2f}'
            ))
    
    def atualizar_metricas(self):
        area = self.calcular_area()
        perimetro = self.calcular_perimetro()
        centroide = self.calcular_centroide()
        n = len(self.projeto['pontos'])
        
        self.label_area.config(text=f'{area:.3f} m²')
        self.label_perimetro.config(text=f'{perimetro:.3f} m')
        self.label_pontos.config(text=f'{n}')
        self.label_centroide.config(text=f'X={centroide["x"]:.3f} Y={centroide["y"]:.3f}')
        
        self.projeto['area'] = area
        self.projeto['perimetro'] = perimetro
        self.projeto['centroide'] = centroide
    
    def atualizar_planta(self):
        if not BIBLIOTECAS_OK:
            return
        
        self.ax.clear()
        pontos = self.projeto['pontos']
        
        if not pontos:
            self.ax.text(0.5, 0.5, 'Adicione pontos para visualizar', 
                        ha='center', va='center', transform=self.ax.transAxes)
            self.ax.set_title('Planta Topográfica')
            self.canvas.draw()
            return
        
        xs = [p['x'] for p in pontos]
        ys = [p['y'] for p in pontos]
        
        self.ax.plot(xs, ys, 'b-', linewidth=2, label='Poligonal')
        self.ax.plot([xs[-1], xs[0]], [ys[-1], ys[0]], 'b-', linewidth=2)
        self.ax.plot(xs, ys, 'ro', markersize=6, label='Pontos')
        
        if self.projeto['curvas']:
            for curva in self.projeto['curvas']:
                if len(curva['pontos']) > 1:
                    cx = [p['x'] for p in curva['pontos']]
                    cy = [p['y'] for p in curva['pontos']]
                    self.ax.plot(cx, cy, 'g--', linewidth=1, alpha=0.7)
                    if len(cx) > 0:
                        self.ax.text(cx[-1], cy[-1], f'{curva["nivel"]:.1f}m', 
                                   fontsize=8, color='green')
        
        for i, p in enumerate(pontos):
            estacao = self.projeto['estacoes'][i] if i < len(self.projeto['estacoes']) else None
            label = estacao['id'] if estacao else f'P{i+1}'
            self.ax.annotate(label, (p['x'], p['y']), 
                           xytext=(5, 5), textcoords='offset points',
                           fontsize=8, fontweight='bold')
        
        area = self.calcular_area()
        self.ax.set_title(f'Planta Topográfica - Área: {area:.2f} m²')
        self.ax.set_xlabel('X (m)')
        self.ax.set_ylabel('Y (m)')
        self.ax.grid(True, alpha=0.3)
        self.ax.axis('equal')
        self.ax.legend()
        
        self.canvas.draw()
    
    def atualizar_curvas(self):
        self.lista_curvas.delete(0, tk.END)
        for curva in self.projeto['curvas']:
            self.lista_curvas.insert(tk.END, 
                f'Nível {curva["nivel"]:.2f}m - {len(curva["pontos"])} pontos')
    
    def atualizar_licenca(self):
        info = self.license_manager.get_info()
        
        if info['status'] == 'TRIAL':
            texto = f"🧪 Teste: {info.get('dias_restantes', 0)} dias"
        elif info['status'] == 'FULL':
            texto = "✅ Licença Vitalícia"
        elif info['status'] == 'CORPORATE':
            texto = "🏢 Licença Corporativa"
        else:
            texto = f"🔑 {info['status']}"
        
        self.label_licenca.config(text=texto)
    
    def atualizar_status(self, mensagem):
        self.status.config(text=mensagem)
        self.root.update()
    
    # ============================================
    # UTILITÁRIOS
    # ============================================
    
    def copiar_dados(self):
        texto = 'ID\tX_Est\tY_Est\tZ_Est\tX_Ponto\tY_Ponto\tZ_Ponto\tAzimute\tDistancia\tZenith\n'
        for i, e in enumerate(self.projeto['estacoes']):
            p = self.projeto['pontos'][i]
            texto += f'{e["id"]}\t{e["x"]:.3f}\t{e["y"]:.3f}\t{e["z"]:.3f}\t'
            texto += f'{p["x"]:.3f}\t{p["y"]:.3f}\t{p["z"]:.3f}\t'
            texto += f'{e["azimute"]:.2f}\t{e["distancia"]:.3f}\t{e["zenith"]:.2f}\n'
        
        self.root.clipboard_clear()
        self.root.clipboard_append(texto)
        self.atualizar_status('Dados copiados para área de transferência')
    
    def imprimir(self):
        self.atualizar_status('Imprimindo...')
        janela = tk.Toplevel(self.root)
        janela.title('Impressão - Tabela')
        janela.geometry('800x500')
        
        tree = ttk.Treeview(janela, columns=(
            'ID', 'X_Est', 'Y_Est', 'Z_Est', 'X_Ponto', 'Y_Ponto', 'Z_Ponto',
            'Azimute', 'Distancia', 'Zenith'
        ), show='headings', height=20)
        
        cabecalhos = [
            ('ID', 'ID', 60),
            ('X_Est', 'X Est.', 80),
            ('Y_Est', 'Y Est.', 80),
            ('Z_Est', 'Z Est.', 80),
            ('X_Ponto', 'X Ponto', 80),
            ('Y_Ponto', 'Y Ponto', 80),
            ('Z_Ponto', 'Z Ponto', 80),
            ('Azimute', 'Azimute', 80),
            ('Distancia', 'Dist.', 80),
            ('Zenith', 'Zenith', 80)
        ]
        
        for col, texto, largura in cabecalhos:
            tree.heading(col, text=texto)
            tree.column(col, width=largura, anchor='center')
        
        for i, e in enumerate(self.projeto['estacoes']):
            p = self.projeto['pontos'][i]
            tree.insert('', 'end', values=(
                e['id'],
                f'{e["x"]:.3f}',
                f'{e["y"]:.3f}',
                f'{e["z"]:.3f}',
                f'{p["x"]:.3f}',
                f'{p["y"]:.3f}',
                f'{p["z"]:.3f}',
                f'{e["azimute"]:.2f}',
                f'{e["distancia"]:.3f}',
                f'{e["zenith"]:.2f}'
            ))
        
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        ttk.Button(janela, text='🖨️ Imprimir', 
            command=lambda: tree.event_generate('<<Print>>')).pack(pady=5)
    
    def sair(self):
        if messagebox.askyesno('Confirmar', 'Deseja realmente sair?'):
            self.root.quit()
            sys.exit(0)
    
    # ============================================
    # AJUDA
    # ============================================
    
    def mostrar_manual(self):
        manual = f"""
📖 MANUAL DO USUÁRIO - {SOFTWARE} v{VERSAO}
{'=' * 60}

1. INTRODUÇÃO
   {SOFTWARE} é um sistema topográfico profissional
   desenvolvido por {DESENVOLVEDOR}.
   
2. COMO USAR
   • Adicione estações com ID, coordenadas, azimute e distância
   • O sistema calcula automaticamente as coordenadas dos pontos
   • Visualize a planta, curvas de nível e relatórios

3. FUNCIONALIDADES
   • Georreferenciamento (SIRGAS 2000, WGS84)
   • Ajuste de Bowditch
   • Curvas de nível
   • Exportação CSV/DXF
   • Relatórios técnicos
   • Gráficos interativos

4. ATALHOS DE TECLADO
   • Enter: Adicionar estação
   • Ctrl+N: Novo projeto
   • Ctrl+S: Salvar projeto
   • Ctrl+O: Abrir projeto

5. DICAS IMPORTANTES
   • Azimute em grados (0-400)
   • Zenith: 100 = horizontal
   • Use coordenadas iniciais X=0, Y=0

6. SUPORTE
   📧 {EMAIL}
   👨‍💻 {DESENVOLVEDOR}

{'=' * 60}
© {ANO} - Todos os direitos reservados
"""
        messagebox.showinfo('📖 Manual do Usuário', manual)
    
    def mostrar_contato(self):
        contato = f"""
📧 CONTATO DO DESENVOLVEDOR

Nome: {DESENVOLVEDOR}
E-mail: {EMAIL}
Software: {SOFTWARE} v{VERSAO}

SERVIÇOS OFERECIDOS:
✅ Suporte técnico
✅ Treinamento personalizado
✅ Desenvolvimento sob medida
✅ Consultoria topográfica

Para adquirir sua licença ou solicitar serviços,
entre em contato pelo e-mail acima.

© {ANO} - {DESENVOLVEDOR}
"""
        messagebox.showinfo('📧 Contato', contato)
    
    def mostrar_sobre(self):
        sobre = f"""
ℹ️ SOBRE O {SOFTWARE}

{SOFTWARE} v{VERSAO}
Sistema Topográfico Profissional

DESENVOLVEDOR: {DESENVOLVEDOR}
E-MAIL: {EMAIL}
ANO: {ANO}

CARACTERÍSTICAS:
✅ 100% Offline
✅ Sem limitações de arquivos
✅ Interface moderna
✅ Exportação para AutoCAD
✅ Curvas de nível
✅ Georreferenciamento
✅ Sistema de licenças

TECNOLOGIAS:
🐍 Python 3.x
🎨 Tkinter / Matplotlib
📊 Pandas / NumPy
🔐 Criptografia AES

© {ANO} - Todos os direitos reservados

Este software é protegido por direitos autorais e
leis de propriedade intelectual. A reprodução,
distribuição ou modificação não autorizada está
sujeita a penalidades civis e criminais.
"""
        messagebox.showinfo('ℹ️ Sobre', sobre)

# ============================================
# PONTO DE ENTRADA
# ============================================

def main():
    try:
        root = tk.Tk()
        app = TopoGeoSysApp(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror('Erro Fatal', f'Erro ao iniciar o programa:\n{e}')
        sys.exit(1)

if __name__ == '__main__':
    main()