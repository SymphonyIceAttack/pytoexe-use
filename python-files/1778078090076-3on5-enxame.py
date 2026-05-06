# enxame.py – NanoSwarm com Google Gemini + Ícone gerado automaticamente
import sys, os, json, subprocess, threading, time, queue, uuid, struct, zlib
import tkinter as tk
from tkinter import scrolledtext, messagebox
import win32com.client
from win32com.client import VARIANT
import pythoncom
from openai import OpenAI

# ================= CONFIGURAÇÃO =================
API_KEY_FILE = "api_key.txt"
BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
MODEL = "gemini-2.0-flash"
MEMORIA_FILE = "memoria.json"
ICONE_FILE = "icone.ico"
# =================================================

# ---------- Gera o ícone automaticamente (sem dependências externas) ----------
def gerar_icone():
    """Cria um arquivo .ico simples (32x32) com um desenho de enxame."""
    # Cabeçalho do arquivo ICO
    # Referência: https://en.wikipedia.org/wiki/ICO_(file_format)
    width = 32
    height = 32
    # Preparamos a imagem como bitmap (BMP) dentro do ICO
    bpp = 32  # bits por pixel (RGBA)
    # Tamanho do pixel array (32*32*4 bytes) + cabeçalho BMP (40 bytes)
    bitmap_size = 40 + width * height * 4
    # Estrutura do diretório de ícone (6 bytes) + cabeçalho ICO (6 bytes) + um ícone (16 bytes)
    ico_header = struct.pack('<HHH', 0, 1, 1)  # reservado, tipo=1(ico), 1 imagem
    # Diretório da imagem: largura, altura, cores (0), reservado (0), planos (1), bpp (32), tamanho, offset (22)
    image_entry = struct.pack('<BBBBHHII',
        width if width < 256 else 0,  # largura (256 vira 0)
        height if height < 256 else 0, # altura
        0, 0,  # paleta de cores (não usada)
        1,      # planos
        bpp,    # bits por pixel
        bitmap_size,  # tamanho dos dados da imagem
        22      # offset para os dados (após cabeçalho ICO + entrada)
    )
    # Cabeçalho BMP (DIB)
    bmp_header = struct.pack('<IiiHHIIiiII',
        40,         # tamanho do cabeçalho DIB
        width,      # largura
        height * 2, # altura (por quê 2? BMP usa altura dupla para máscara XOR e AND?)
        # Na verdade, para ICO, a altura no cabeçalho DIB é o dobro da altura real (para conter a máscara AND abaixo da imagem)
        1,          # planos
        bpp,        # bits
        0,          # compressão BI_RGB
        0,          # tamanho da imagem (pode ser 0)
        0, 0, 0, 0 # resolução e cores
    )
    # Pixel array: 32x32 pixels RGBA (linhas de baixo para cima no BMP)
    pixels = []
    # Desenho simples: fundo preto, pontos verdes e linhas
    for y in range(height-1, -1, -1):  # de baixo para cima
        row = []
        for x in range(width):
            # Fundo escuro
            r, g, b, a = 20, 20, 20, 255
            # Pontos (agentes) em verde
            if (x-8)**2 + (y-6)**2 <= 9 or (x-20)**2 + (y-6)**2 <= 9 or \
               (x-6)**2 + (y-16)**2 <= 9 or (x-24)**2 + (y-16)**2 <= 9 or \
               (x-10)**2 + (y-26)**2 <= 9 or (x-22)**2 + (y-26)**2 <= 9:
                r, g, b = 0, 255, 100
            # Linhas de conexão (simples)
            # Linha 8,6 -> 20,6
            if y == 6 and 8 <= x <= 20: r, g, b = 100, 200, 100
            # 8,6 -> 6,16 (diagonal)
            if 8 >= x >= 6 and 6 <= y <= 16 and abs(x - 7) + abs(y - 11) <= 3: r,g,b = 100,200,100
            # 20,6 -> 24,16
            if 20 <= x <= 24 and 6 <= y <= 16 and abs(x - 22) + abs(y - 11) <= 3: r,g,b = 100,200,100
            # 6,16 -> 24,16
            if y == 16 and 6 <= x <= 24: r,g,b = 100,200,100
            # 6,16 -> 10,26
            if 6 <= x <= 10 and 16 <= y <= 26 and abs(x - 8) + abs(y - 21) <= 3: r,g,b = 100,200,100
            # 24,16 -> 22,26
            if 22 <= x <= 24 and 16 <= y <= 26 and abs(x - 23) + abs(y - 21) <= 3: r,g,b = 100,200,100
            row.extend([b, g, r, a])  # BGRA
        pixels.extend(row)
    bitmap_data = bmp_header + bytes(pixels)
    # Máscara AND (após os pixels XOR) – 32x32 bits (1 bit por pixel), alinhada a 4 bytes
    and_mask = b'\x00' * (width * height // 8)
    # Escreve o arquivo
    base_dir = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
    icone_path = os.path.join(base_dir, ICONE_FILE)
    try:
        with open(icone_path, 'wb') as f:
            f.write(ico_header + image_entry + bitmap_data + and_mask)
        return icone_path
    except Exception as e:
        print(f"Não foi possível criar o ícone: {e}")
        return None

# ---------- Perfis dos agentes (DNA) ----------
PERFIS = {
    "desenhista": {
        "descricao": "Desenha no AutoCAD comandos de criação geométrica e texto.",
        "ferramentas": ["CIRCLE", "LINE", "TEXT", "ERASE_ALL", "ZOOM_EXTENTS"]
    },
    "programador": {
        "descricao": "Executa programas, abre arquivos, gerencia o Windows.",
        "ferramentas": ["abrir_navegador", "abrir_autocad", "abrir_bloco_notas", "abrir_calculadora"]
    },
    "verificador": {
        "descricao": "Revisa desenhos ou código, detecta erros e propõe correções.",
        "ferramentas": ["verificar_desenho", "verificar_codigo"]
    },
    "coordenador": {
        "descricao": "Divide tarefas complexas em subtarefas e delega.",
        "ferramentas": ["dividir_tarefa", "consolidar_resultados"]
    }
}

# Comunicação entre as células (placa neural)
placa_mae = queue.Queue()

# Memória do enxame
memoria = {"historico": [], "adaptacoes": {}}
if os.path.exists(MEMORIA_FILE):
    with open(MEMORIA_FILE, "r") as f:
        memoria = json.load(f)

def salvar_memoria():
    with open(MEMORIA_FILE, "w") as f:
        json.dump(memoria, f, indent=2)

# ---------- Funções auxiliares ----------
def ler_api_key():
    try:
        base = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
        with open(os.path.join(base, API_KEY_FILE), "r") as f:
            return f.read().strip()
    except:
        messagebox.showerror("Erro", f"Arquivo {API_KEY_FILE} não encontrado.")
        sys.exit(1)

def chamar_ia(perfil_nome, mensagem, contexto_extra=""):
    """Envia comando ao Gemini com o perfil do agente."""
    api_key = ler_api_key()
    perfil = PERFIS.get(perfil_nome, PERFIS["coordenador"])
    prompt_sistema = f"""Você é uma célula de um enxame de IA benigno. Seu papel: '{perfil_nome}'.
{perfil['descricao']}
Ferramentas: {perfil['ferramentas']}
Contexto extra: {contexto_extra}
Adaptações anteriores do enxame: {json.dumps(memoria.get('adaptacoes', {}))}

Retorne APENAS UM JSON, sem nenhum texto adicional.
Formato: {{"tipo": "autocad", "dados": [{{"acao": "CIRCLE", "x": ..., "y": ..., "raio": ...}}]}}
ou {{"tipo": "sistema", "dados": {{"comando": "abrir_navegador"}}}}
ou {{"tipo": "coordenacao", "dados": {{"sub_tarefas": ["..."]}}}}
Se não entender, retorne {{"tipo": "desconhecido"}}.
"""
    client = OpenAI(api_key=api_key, base_url=BASE_URL)
    try:
        resposta = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": mensagem}
            ],
            temperature=0.1
        )
        conteudo = resposta.choices[0].message.content.strip()
        # Grava na memória
        memoria["historico"].append({"perfil": perfil_nome, "acao": conteudo, "timestamp": time.time()})
        salvar_memoria()
        return conteudo
    except Exception as e:
        print(f"Erro na IA (Gemini): {e}")
        return None

# ---------- Ações do sistema ----------
def executar_sistema(dados):
    comando = dados.get("comando", "")
    if comando == "abrir_navegador":
        os.startfile("https://www.google.com")
    elif comando == "abrir_bloco_notas":
        subprocess.Popen("notepad.exe")
    elif comando == "abrir_calculadora":
        subprocess.Popen("calc.exe")
    elif comando == "abrir_autocad":
        try:
            win32com.client.GetObject(None, "AutoCAD.Application")
        except:
            subprocess.Popen("acad.exe")
            time.sleep(10)
    elif comando == "fechar_autocad":
        try:
            acad = win32com.client.GetObject(None, "AutoCAD.Application")
            acad.Quit()
        except:
            pass

# ---------- Ações AutoCAD ----------
def conectar_autocad():
    try:
        return win32com.client.GetObject(None, "AutoCAD.Application")
    except:
        return None

def executar_acoes_autocad(acoes):
    acad = conectar_autocad()
    if not acad:
        executar_sistema({"comando": "abrir_autocad"})
        time.sleep(10)
        acad = conectar_autocad()
        if not acad:
            return False, "AutoCAD não pôde ser aberto."
    model = acad.ActiveDocument.ModelSpace
    for item in acoes:
        acao = item.get("acao")
        try:
            if acao == "CIRCLE":
                x, y, r = float(item["x"]), float(item["y"]), float(item["raio"])
                center = VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [x, y, 0])
                model.AddCircle(center, r)
            elif acao == "LINE":
                p1 = VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(item["x1"]), float(item["y1"]), 0])
                p2 = VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(item["x2"]), float(item["y2"]), 0])
                model.AddLine(p1, p2)
            elif acao == "TEXT":
                x, y, texto = float(item["x"]), float(item["y"]), item["texto"]
                altura = float(item.get("altura", 2.5))
                punto = VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [x, y, 0])
                model.AddText(texto, punto, altura)
            elif acao == "ERASE_ALL":
                for ent in list(model):
                    ent.Delete()
            elif acao == "ZOOM_EXTENTS":
                acad.ActiveDocument.SendCommand("ZOOM E ")
        except Exception as e:
            print(f"Erro AutoCAD {acao}: {e}")
    return True, "Ações AutoCAD executadas."

# ---------- Célula agente (thread) ----------
class CelulaAgente(threading.Thread):
    def __init__(self, nome, perfil, tarefa, callback=None):
        super().__init__(daemon=True)
        self.id = str(uuid.uuid4())[:8]
        self.nome = nome
        self.perfil = perfil
        self.tarefa = tarefa
        self.callback = callback

    def run(self):
        resposta_bruta = chamar_ia(self.perfil, self.tarefa, contexto_extra=f"ID: {self.id}")
        if not resposta_bruta:
            self.responder({"erro": "sem resposta da IA"})
            return
        try:
            dados = json.loads(resposta_bruta)
        except:
            dados = {"tipo": "desconhecido", "dados": {}}

        if dados.get("tipo") == "coordenacao":
            sub_tarefas = dados.get("dados", {}).get("sub_tarefas", [])
            for i, subt in enumerate(sub_tarefas):
                perfil_filho = "desenhista" if "desenhar" in subt else "programador"
                filha = CelulaAgente(
                    nome=f"{self.nome}_f{i}",
                    perfil=perfil_filho,
                    tarefa=subt,
                    callback=self.consolidar
                )
                filha.start()
        elif dados.get("tipo") == "autocad":
            sucesso, msg = executar_acoes_autocad(dados["dados"])
            if sucesso:
                verificador = CelulaAgente(
                    nome=f"verif_{self.nome}",
                    perfil="verificador",
                    tarefa=f"Verifique o desenho: {self.tarefa}",
                    callback=self.receber_verificacao
                )
                verificador.start()
            self.responder({"status": "ok", "msg": msg})
        elif dados.get("tipo") == "sistema":
            executar_sistema(dados["dados"])
            self.responder({"status": "sistema", "comando": dados["dados"].get("comando")})
        else:
            self.responder({"status": "desconhecido"})

    def consolidar(self, resultado):
        placa_mae.put({"de": self.nome, "parcial": resultado})

    def receber_verificacao(self, resultado):
        if resultado.get("status") == "erro":
            correcao = CelulaAgente(
                nome=f"corr_{self.nome}",
                perfil="desenhista",
                tarefa=f"Corrija erro no AutoCAD: {resultado.get('msg')}",
                callback=self.responder
            )
            correcao.start()

    def responder(self, resultado):
        if self.callback:
            self.callback(resultado)
        placa_mae.put({"celula": self.nome, "resultado": resultado})

# ---------- Interface gráfica ----------
class EnxameGUI:
    def __init__(self, root):
        self.root = root
        root.title("NanoSwarm - Google Gemini")
        root.geometry("520x450")
        root.configure(bg="#1a1a1a")

        # Ícone da janela (gerado na primeira execução)
        icone = gerar_icone()
        if icone and os.path.exists(icone):
            try:
                root.iconbitmap(icone)
            except:
                pass  # Tkinter pode não aceitar em alguns casos, mas não trava

        self.chat = scrolledtext.ScrolledText(root, state='disabled', bg="#0d0d0d", fg="#00ff66", insertbackground='white')
        self.chat.pack(pady=5, padx=5, fill=tk.BOTH, expand=True)
        frame = tk.Frame(root, bg="#1a1a1a")
        frame.pack(fill=tk.X, padx=5, pady=5)
        self.entrada = tk.Entry(frame, bg="#333333", fg="white", insertbackground="white")
        self.entrada.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
        self.entrada.bind("<Return>", self.enviar)
        self.entrada.focus_set()
        btn = tk.Button(frame, text="▶", command=self.enviar, bg="#0066cc", fg="white")
        btn.pack(side=tk.RIGHT, padx=(5,0))
        self.adicionar_texto("🧬 NanoSwarm de 25.000 agentes ativo. Diga sua ordem.\n")

    def adicionar_texto(self, texto):
        self.chat.configure(state='normal')
        self.chat.insert(tk.END, texto + "\n")
        self.chat.see(tk.END)
        self.chat.configure(state='disabled')

    def enviar(self, event=None):
        comando = self.entrada.get().strip()
        if not comando:
            return
        self.entrada.delete(0, tk.END)
        self.adicionar_texto(f"🧑 Você: {comando}")
        celula_mae = CelulaAgente(
            nome="COORD_MAE",
            perfil="coordenador",
            tarefa=comando,
            callback=self.processar_resposta
        )
        celula_mae.start()
        threading.Thread(target=self.escutar_placa, daemon=True).start()

    def escutar_placa(self):
        while True:
            try:
                msg = placa_mae.get(timeout=0.5)
                self.root.after(0, self.adicionar_texto, f"📡 Placa neural: {json.dumps(msg, indent=2)}")
            except queue.Empty:
                pass

    def processar_resposta(self, resultado):
        self.root.after(0, self.adicionar_texto, f"✅ Enxame finalizou: {resultado}")

if __name__ == "__main__":
    pythoncom.CoInitialize()
    root = tk.Tk()
    app = EnxameGUI(root)
    root.mainloop()