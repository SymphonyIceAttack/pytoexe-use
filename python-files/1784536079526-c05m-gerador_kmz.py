import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import threading
import simplekml
import numpy as np
from scipy.spatial import distance
from PIL import Image
import shutil
import zipfile
import tempfile
import webbrowser
from datetime import datetime

# Tentar importar OCR
try:
    import pytesseract
    import cv2
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    OCR_DISPONIVEL = True
except:
    OCR_DISPONIVEL = False

class GeradorKMZApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📍 Gerador Automatico de KMZ com OCR")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # Variaveis
        self.pasta_selecionada = ""
        self.resultados = []
        self.pontos_finais = []
        self.erros = []
        self.arquivo_kmz = ""
        
        self.criar_interface()
        
    def criar_interface(self):
        # Titulo
        titulo = tk.Label(self.root, text="📍 GERADOR AUTOMATICO DE KMZ", font=("Arial", 18, "bold"))
        titulo.pack(pady=10)
        
        subtitulo = tk.Label(self.root, text="Extrai coordenadas de imagens (OCR + Nome) e gera KMZ com fotos embutidas", font=("Arial", 10))
        subtitulo.pack(pady=5)
        
        # Frame para selecao da pasta
        frame_pasta = tk.Frame(self.root)
        frame_pasta.pack(pady=15, padx=20, fill="x")
        
        self.label_pasta = tk.Label(frame_pasta, text="Nenhuma pasta selecionada", bg="white", relief="sunken", anchor="w", font=("Arial", 9))
        self.label_pasta.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        btn_selecionar = tk.Button(frame_pasta, text="📁 Selecionar Pasta", command=self.selecionar_pasta, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"))
        btn_selecionar.pack(side="right")
        
        # Frame para botoes de acao
        frame_acoes = tk.Frame(self.root)
        frame_acoes.pack(pady=10)
        
        self.btn_processar = tk.Button(frame_acoes, text="🔍 Processar Imagens", command=self.processar_imagens, bg="#2196F3", fg="white", font=("Arial", 12, "bold"), state="disabled", width=20)
        self.btn_processar.pack(side="left", padx=5)
        
        self.btn_gerar_kmz = tk.Button(frame_acoes, text="📦 Gerar KMZ", command=self.gerar_kmz, bg="#FF9800", fg="white", font=("Arial", 12, "bold"), state="disabled", width=20)
        self.btn_gerar_kmz.pack(side="left", padx=5)
        
        self.btn_abrir = tk.Button(frame_acoes, text="📂 Abrir KMZ", command=self.abrir_kmz, bg="#9E9E9E", fg="white", font=("Arial", 10, "bold"), state="disabled", width=15)
        self.btn_abrir.pack(side="left", padx=5)
        
        # Barra de progresso
        self.progresso = ttk.Progressbar(self.root, orient="horizontal", length=700, mode="determinate")
        self.progresso.pack(pady=10, padx=20)
        
        # Area de log
        frame_log = tk.Frame(self.root)
        frame_log.pack(pady=10, padx=20, fill="both", expand=True)
        
        label_log = tk.Label(frame_log, text="📋 Log de Execucao:", font=("Arial", 10, "bold"))
        label_log.pack(anchor="w")
        
        self.log_text = scrolledtext.ScrolledText(frame_log, height=18, bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", 9))
        self.log_text.pack(fill="both", expand=True)
        
        # Cores para o log
        self.log_text.tag_config("info", foreground="#4FC3F7")
        self.log_text.tag_config("sucesso", foreground="#81C784")
        self.log_text.tag_config("erro", foreground="#E57373")
        self.log_text.tag_config("alerta", foreground="#FFB74D")
        self.log_text.tag_config("destaque", foreground="#CE93D8")
        self.log_text.tag_config("titulo", foreground="#FFFFFF", font=("Consolas", 10, "bold"))
        
        # Frame para botoes de ajuda
        frame_ajuda = tk.Frame(self.root)
        frame_ajuda.pack(pady=10)
        
        btn_ajuda = tk.Button(frame_ajuda, text="❓ Como usar", command=self.mostrar_ajuda, bg="#9E9E9E", fg="white", font=("Arial", 9))
        btn_ajuda.pack(side="left", padx=5)
        
        btn_limpar = tk.Button(frame_ajuda, text="🧹 Limpar log", command=self.limpar_log, bg="#607D8B", fg="white", font=("Arial", 9))
        btn_limpar.pack(side="left", padx=5)
        
        # Status do OCR
        if OCR_DISPONIVEL:
            self.log("🟢 OCR (Tesseract) disponivel! Vou ler texto das imagens.", "sucesso")
        else:
            self.log("🟡 Tesseract nao encontrado. Vou ler apenas do nome do ficheiro.", "alerta")
            self.log("   Para ativar OCR, instala o Tesseract em: https://github.com/UB-Mannheim/tesseract/wiki", "alerta")
        
        self.log("🟢 Aplicacao iniciada. Selecione uma pasta para comecar.", "info")
        
    def log(self, mensagem, tipo="info"):
        """Adiciona mensagem ao log com cor"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {mensagem}\n", tipo)
        self.log_text.see("end")
        self.root.update()
        
    def limpar_log(self):
        self.log_text.delete(1.0, tk.END)
        
    def selecionar_pasta(self):
        """Abre dialogo para selecionar pasta"""
        pasta = filedialog.askdirectory(title="Selecionar pasta com imagens")
        if pasta:
            self.pasta_selecionada = pasta
            self.label_pasta.config(text=pasta)
            self.btn_processar.config(state="normal")
            self.log(f"📁 Pasta selecionada: {pasta}", "info")
            
            # Contar imagens
            imagens = [f for f in os.listdir(pasta) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            self.log(f"📸 Encontradas {len(imagens)} imagens na pasta.", "info")
            
            if len(imagens) == 0:
                self.log("⚠️ Nenhuma imagem encontrada!", "alerta")
                
    def extrair_coordenadas(self, texto):
        """
        Extrai coordenadas de um texto usando expressoes regulares
        Suporta varios formatos e valida se esta dentro de Portugal
        """
        # Formato 1: 37.283627N 8.694865W
        padrao1 = r'(\d{2,3}\.\d+)[NnSs]\s*([\d.]+)[WwEe]'
        match = re.search(padrao1, texto)
        if match:
            try:
                lat = float(match.group(1))
                lon = float(match.group(2))
                if lon > 0:
                    lon = -lon
                if 36 <= lat <= 42 and -10 <= lon <= -6:
                    return lat, lon, "Decimal"
            except:
                pass
        
        # Formato 2: 37.283627, -8.694865
        padrao2 = r'(\d{2,3}\.\d+)[,\s]+([-]?\d{1,3}\.\d+)'
        match = re.search(padrao2, texto)
        if match:
            try:
                lat = float(match.group(1))
                lon = float(match.group(2))
                if lon > 0:
                    lon = -lon
                if 36 <= lat <= 42 and -10 <= lon <= -6:
                    return lat, lon, "Decimal"
            except:
                pass
        
        # Formato 3: 37°28'18.7"N 8°69'18.0"W (graus, minutos, segundos)
        padrao3 = r'(\d{2})[°]\s*(\d{2})[\']\s*([\d.]+)["][NnSs]\s*(\d{1,3})[°]\s*(\d{2})[\']\s*([\d.]+)["][WwEe]'
        match = re.search(padrao3, texto)
        if match:
            try:
                lat = float(match.group(1)) + float(match.group(2))/60 + float(match.group(3))/3600
                lon = float(match.group(4)) + float(match.group(5))/60 + float(match.group(6))/3600
                if lon > 0:
                    lon = -lon
                if 36 <= lat <= 42 and -10 <= lon <= -6:
                    return lat, lon, "GMS"
            except:
                pass
        
        # Formato 4: 37288337N 8695660W (sem pontos decimais)
        padrao4 = r'(\d{8,9})[NnSs]\s*(\d{7,8})[WwEe]'
        match = re.search(padrao4, texto)
        if match:
            try:
                lat_str = match.group(1)
                lon_str = match.group(2)
                if len(lat_str) >= 8:
                    lat = float(lat_str[:2] + '.' + lat_str[2:])
                else:
                    lat = float(lat_str[:1] + '.' + lat_str[1:])
                if len(lon_str) >= 7:
                    lon = -(float(lon_str[:1] + '.' + lon_str[1:]))
                else:
                    lon = -(float(lon_str[:1] + '.' + lon_str[1:]))
                if 36 <= lat <= 42 and -10 <= lon <= -6:
                    return lat, lon, "Compacto"
            except:
                pass
        
        return None, None, None
    
    def processar_imagens(self):
        """Processa todas as imagens da pasta selecionada"""
        if not self.pasta_selecionada:
            messagebox.showerror("Erro", "Selecione uma pasta primeiro!")
            return
        
        self.btn_processar.config(state="disabled")
        self.btn_gerar_kmz.config(state="disabled")
        self.progresso["value"] = 0
        
        self.log("\n" + "="*70, "destaque")
        self.log("🔍 INICIANDO PROCESSAMENTO...", "titulo")
        self.log("="*70, "destaque")
        
        # Executar em thread separada
        threading.Thread(target=self._processar_imagens_thread, daemon=True).start()
    
    def _processar_imagens_thread(self):
        """Thread de processamento"""
        try:
            self.resultados = []
            self.erros = []
            
            imagens = [f for f in os.listdir(self.pasta_selecionada) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            
            if not imagens:
                self.log("❌ Nenhuma imagem encontrada na pasta!", "erro")
                self.btn_processar.config(state="normal")
                return
            
            total = len(imagens)
            self.log(f"📸 Encontradas {total} imagens para processar.", "info")
            
            for i, ficheiro in enumerate(imagens, 1):
                caminho = os.path.join(self.pasta_selecionada, ficheiro)
                self.progresso["value"] = (i / total) * 50
                self.log(f"[{i}/{total}] Processando: {ficheiro}", "info")
                
                lat, lon, formato = None, None, None
                texto_extraido = ""
                
                # Tenta OCR se disponivel
                if OCR_DISPONIVEL:
                    try:
                        imagem = Image.open(caminho)
                        if imagem.width > 2000 or imagem.height > 2000:
                            imagem.thumbnail((2000, 2000))
                        texto_extraido = pytesseract.image_to_string(imagem, lang='por+eng')
                        lat, lon, formato = self.extrair_coordenadas(texto_extraido)
                        if lat is not None:
                            self.log(f"  📝 OCR: coordenada encontrada", "info")
                    except Exception as e:
                        self.log(f"  ⚠️ Erro no OCR: {str(e)[:50]}", "alerta")
                
                # Se nao encontrou, tenta pelo nome do ficheiro
                if lat is None:
                    lat, lon, formato = self.extrair_coordenadas(ficheiro)
                    if lat is not None:
                        self.log(f"  📝 Nome: coordenada encontrada", "info")
                
                if lat is not None and lon is not None:
                    self.resultados.append({
                        'nome': ficheiro,
                        'lat': lat,
                        'lon': lon,
                        'formato': formato,
                        'texto_ocr': texto_extraido[:300] if texto_extraido else ""
                    })
                    self.log(f"  ✅ Coordenada: {lat:.6f}, {lon:.6f} ({formato})", "sucesso")
                else:
                    self.erros.append({
                        'nome': ficheiro,
                        'motivo': "Sem coordenada"
                    })
                    self.log(f"  ⚠️ Nenhuma coordenada encontrada", "alerta")
            
            self.progresso["value"] = 100
            
            self.log("\n" + "="*70, "destaque")
            self.log(f"✅ Processamento concluido!", "sucesso")
            self.log(f"   📸 Imagens processadas: {total}", "info")
            self.log(f"   ✅ Com coordenadas: {len(self.resultados)}", "sucesso")
            self.log(f"   ⚠️ Sem coordenadas: {len(self.erros)}", "alerta" if len(self.erros) > 0 else "info")
            self.log("="*70, "destaque")
            
            if self.erros:
                self.log(f"\n📋 Ficheiros sem coordenada:", "alerta")
                for e in self.erros[:10]:
                    self.log(f"   • {e['nome']}", "alerta")
                if len(self.erros) > 10:
                    self.log(f"   ... e mais {len(self.erros) - 10} ficheiros", "alerta")
            
            # Detetar outliers
            if len(self.resultados) >= 3:
                self.detetar_outliers()
            else:
                self.log("ℹ️ Menos de 3 pontos. A gerar KMZ sem detecao de outliers.", "info")
                self.pontos_finais = self.resultados.copy()
                self.btn_gerar_kmz.config(state="normal")
            
            self.btn_processar.config(state="normal")
            
            if self.pontos_finais:
                self.log(f"\n✅ {len(self.pontos_finais)} pontos prontos para KMZ.", "sucesso")
                self.btn_gerar_kmz.config(state="normal")
            else:
                self.log("❌ Nenhum ponto valido encontrado!", "erro")
            
        except Exception as e:
            self.log(f"❌ Erro durante o processamento: {str(e)}", "erro")
            self.btn_processar.config(state="normal")
            self.progresso["value"] = 0
    
    def detetar_outliers(self):
        """Deteta pontos isolados usando o metodo MAD e pergunta ao utilizador"""
        if len(self.resultados) < 3:
            self.pontos_finais = self.resultados.copy()
            self.btn_gerar_kmz.config(state="normal")
            return
        
        coords = np.array([[p['lat'], p['lon']] for p in self.resultados])
        centro_lat = np.median(coords[:, 0])
        centro_lon = np.median(coords[:, 1])
        centro = np.array([centro_lat, centro_lon])
        distancias = distance.cdist([centro], coords)[0]
        
        mediana_distancias = np.median(distancias)
        mad = np.median(np.abs(distancias - mediana_distancias))
        limiar = 2.5 * mad if mad > 0 else 0.005
        
        self.log(f"\n📊 Analise de outliers:", "info")
        self.log(f"   • Centro do grupo: {centro_lat:.6f}, {centro_lon:.6f}", "info")
        self.log(f"   • Mediana das distancias: {mediana_distancias*111000:.0f} m", "info")
        self.log(f"   • Limiar de detecao: {limiar*111000:.0f} m", "info")
        
        self.outliers = []
        self.normais = []
        
        for i, ponto in enumerate(self.resultados):
            if distancias[i] > limiar:
                self.outliers.append(ponto)
                self.log(f"  ⚠️ ALERTA: {ponto['nome']} esta isolado! Distancia: {distancias[i]*111000:.0f} m", "alerta")
            else:
                self.normais.append(ponto)
        
        if self.outliers:
            self.log(f"\n⚠️ Encontrados {len(self.outliers)} ponto(s) isolado(s).", "alerta")
            self.root.after(0, self.perguntar_outliers)
        else:
            self.log("✅ Nenhum ponto isolado detectado.", "sucesso")
            self.pontos_finais = self.resultados.copy()
            self.btn_gerar_kmz.config(state="normal")
    
    def perguntar_outliers(self):
        """Mostra popup para decidir o que fazer com os outliers"""
        msg = f"Foram detectados {len(self.outliers)} ponto(s) isolado(s):\n\n"
        for o in self.outliers[:5]:
            msg += f"• {o['nome']}\n  ({o['lat']:.6f}, {o['lon']:.6f})\n"
        if len(self.outliers) > 5:
            msg += f"\n... e mais {len(self.outliers) - 5} pontos"
        
        msg += "\n\nDeseja incluir estes pontos no KMZ?"
        
        resposta = messagebox.askyesno("⚠️ Pontos Isolados Detectados", msg)
        
        if resposta:
            self.pontos_finais = self.resultados.copy()
            self.log("✅ Pontos isolados MANTIDOS no KMZ.", "info")
        else:
            self.pontos_finais = self.normais.copy()
            self.log(f"✅ Pontos isolados REMOVIDOS. {len(self.pontos_finais)} pontos restantes.", "info")
        
        self.btn_gerar_kmz.config(state="normal")
    
    def gerar_kmz(self):
        """Gera ficheiro KMZ com as imagens embutidas"""
        if not self.pontos_finais:
            messagebox.showerror("Erro", "Nao ha pontos para gerar o KMZ!")
            return
        
        caminho_kmz = filedialog.asksaveasfilename(
            defaultextension=".kmz",
            filetypes=[("KMZ files", "*.kmz"), ("All files", "*.*")],
            title="Guardar KMZ como"
        )
        
        if not caminho_kmz:
            return
        
        self.btn_gerar_kmz.config(state="disabled")
        self.progresso["value"] = 0
        
        try:
            self.log("\n" + "="*70, "destaque")
            self.log("📦 GERANDO KMZ...", "titulo")
            self.log("="*70, "destaque")
            
            temp_dir = tempfile.mkdtemp()
            kml_path = os.path.join(temp_dir, "document.kml")
            imagens_dir = os.path.join(temp_dir, "imagens")
            os.makedirs(imagens_dir, exist_ok=True)
            
            kml = simplekml.Kml()
            kml.document.name = "Pontos extraidos de imagens"
            kml.document.description = f"Gerado automaticamente em {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            
            total = len(self.pontos_finais)
            
            for i, ponto in enumerate(self.pontos_finais, 1):
                self.progresso["value"] = (i / total) * 80
                
                origem = os.path.join(self.pasta_selecionada, ponto['nome'])
                destino = os.path.join(imagens_dir, ponto['nome'])
                
                if os.path.exists(origem):
                    shutil.copy2(origem, destino)
                    self.log(f"  📸 [{i}/{total}] {ponto['nome']}", "info")
                else:
                    self.log(f"  ⚠️ Imagem nao encontrada: {ponto['nome']}", "alerta")
                    continue
                
                p = kml.newpoint()
                p.name = ponto['nome']
                p.description = f"""<![CDATA[
                    <img src="imagens/{ponto['nome']}" width="400"/><br/>
                    <b>Coordenada:</b> {ponto['lat']:.6f}, {ponto['lon']:.6f}<br/>
                    <b>Formato:</b> {ponto.get('formato', 'Desconhecido')}<br/>
                    <b>Data:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}
                ]]>"""
                p.coords = [(ponto['lon'], ponto['lat'])]
                p.style.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/pushpin/red-pushpin.png'
                p.style.iconstyle.scale = 1.0
            
            kml.save(kml_path)
            self.log(f"✅ KML gerado com {len(self.pontos_finais)} pontos.", "sucesso")
            
            self.progresso["value"] = 90
            self.log("📦 A criar ficheiro KMZ...", "info")
            
            with zipfile.ZipFile(caminho_kmz, 'w', zipfile.ZIP_DEFLATED) as kmz:
                kmz.write(kml_path, "document.kml")
                for f in os.listdir(imagens_dir):
                    caminho_imagem = os.path.join(imagens_dir, f)
                    kmz.write(caminho_imagem, f"imagens/{f}")
            
            shutil.rmtree(temp_dir)
            
            self.progresso["value"] = 100
            self.arquivo_kmz = caminho_kmz
            
            self.log("\n" + "="*70, "destaque")
            self.log(f"✅ KMZ GERADO COM SUCESSO!", "sucesso")
            self.log(f"   📁 Ficheiro: {caminho_kmz}", "info")
            self.log(f"   📸 Pontos: {len(self.pontos_finais)}", "info")
            self.log(f"   💾 Tamanho: ~{os.path.getsize(caminho_kmz) / (1024*1024):.1f} MB", "info")
            self.log("="*70, "destaque")
            
            self.btn_gerar_kmz.config(state="normal")
            self.btn_abrir.config(state="normal")
            
            messagebox.showinfo("Sucesso", f"KMZ gerado com sucesso!\n\n{caminho_kmz}\n\n{len(self.pontos_finais)} pontos incluidos.")
            
        except Exception as e:
            self.log(f"❌ Erro ao gerar KMZ: {str(e)}", "erro")
            self.btn_gerar_kmz.config(state="normal")
            self.progresso["value"] = 0
            messagebox.showerror("Erro", f"Erro ao gerar KMZ:\n{str(e)}")
    
    def abrir_kmz(self):
        """Abre a pasta onde esta o KMZ"""
        if self.arquivo_kmz and os.path.exists(self.arquivo_kmz):
            os.startfile(os.path.dirname(self.arquivo_kmz))
        else:
            messagebox.showerror("Erro", "Ficheiro KMZ nao encontrado!")
    
    def mostrar_ajuda(self):
        """Mostra janela de ajuda"""
        ajuda = """
📍 GERADOR AUTOMATICO DE KMZ

COMO USAR:

1. Clique em "Selecionar Pasta" e escolha a pasta com as imagens
2. Clique em "Processar Imagens" para extrair coordenadas
3. O programa vai detectar automaticamente pontos isolados
4. Escolha se quer manter ou remover os pontos isolados
5. Clique em "Gerar KMZ" para criar o ficheiro

FORMATOS DE COORDENADAS SUPORTADOS:
• 37.283627N 8.694865W
• 37°28'18.7"N 8°69'18.0"W
• 37.283627, -8.694865
• 37288337N 8695660W

O QUE E UM KMZ?
E um ficheiro que contem o KML + todas as imagens dentro.
Ao abrir no Google Earth, ve os pontos e as fotos nos baloes.

DICA: As coordenadas podem estar escritas em qualquer parte da imagem.
O programa usa OCR para ler o texto e extrair as coordenadas.

Para melhores resultados, use imagens com texto legivel e boa resolucao.
"""
        messagebox.showinfo("Como usar", ajuda)

def main():
    root = tk.Tk()
    app = GeradorKMZApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()