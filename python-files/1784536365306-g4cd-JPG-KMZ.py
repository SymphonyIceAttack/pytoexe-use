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
from datetime import datetime
import sys

# Tentar importar OCR
try:
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    OCR_DISPONIVEL = True
except:
    OCR_DISPONIVEL = False

class GeradorKMZApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gerador KMZ com OCR")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        self.pasta_selecionada = ""
        self.resultados = []
        self.pontos_finais = []
        self.erros = []
        self.arquivo_kmz = ""
        
        self.criar_interface()
        
    def criar_interface(self):
        titulo = tk.Label(self.root, text="GERADOR DE KMZ", font=("Arial", 18, "bold"))
        titulo.pack(pady=10)
        
        subtitulo = tk.Label(self.root, text="Extrai coordenadas de imagens (OCR + Nome) e gera KMZ com fotos", font=("Arial", 10))
        subtitulo.pack(pady=5)
        
        frame_pasta = tk.Frame(self.root)
        frame_pasta.pack(pady=15, padx=20, fill="x")
        
        self.label_pasta = tk.Label(frame_pasta, text="Nenhuma pasta selecionada", bg="white", relief="sunken", anchor="w")
        self.label_pasta.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        btn_selecionar = tk.Button(frame_pasta, text="Selecionar Pasta", command=self.selecionar_pasta, bg="#4CAF50", fg="white")
        btn_selecionar.pack(side="right")
        
        frame_acoes = tk.Frame(self.root)
        frame_acoes.pack(pady=10)
        
        self.btn_processar = tk.Button(frame_acoes, text="Processar Imagens", command=self.processar_imagens, bg="#2196F3", fg="white", state="disabled", width=20)
        self.btn_processar.pack(side="left", padx=5)
        
        self.btn_gerar_kmz = tk.Button(frame_acoes, text="Gerar KMZ", command=self.gerar_kmz, bg="#FF9800", fg="white", state="disabled", width=20)
        self.btn_gerar_kmz.pack(side="left", padx=5)
        
        self.btn_abrir = tk.Button(frame_acoes, text="Abrir KMZ", command=self.abrir_kmz, bg="#9E9E9E", fg="white", state="disabled", width=15)
        self.btn_abrir.pack(side="left", padx=5)
        
        self.progresso = ttk.Progressbar(self.root, orient="horizontal", length=700, mode="determinate")
        self.progresso.pack(pady=10, padx=20)
        
        frame_log = tk.Frame(self.root)
        frame_log.pack(pady=10, padx=20, fill="both", expand=True)
        
        label_log = tk.Label(frame_log, text="Log de Execucao:", font=("Arial", 10, "bold"))
        label_log.pack(anchor="w")
        
        self.log_text = scrolledtext.ScrolledText(frame_log, height=18, bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", 9))
        self.log_text.pack(fill="both", expand=True)
        
        self.log_text.tag_config("info", foreground="#4FC3F7")
        self.log_text.tag_config("sucesso", foreground="#81C784")
        self.log_text.tag_config("erro", foreground="#E57373")
        self.log_text.tag_config("alerta", foreground="#FFB74D")
        self.log_text.tag_config("destaque", foreground="#CE93D8")
        
        frame_ajuda = tk.Frame(self.root)
        frame_ajuda.pack(pady=10)
        
        btn_ajuda = tk.Button(frame_ajuda, text="Como usar", command=self.mostrar_ajuda, bg="#9E9E9E", fg="white")
        btn_ajuda.pack(side="left", padx=5)
        
        btn_limpar = tk.Button(frame_ajuda, text="Limpar log", command=self.limpar_log, bg="#607D8B", fg="white")
        btn_limpar.pack(side="left", padx=5)
        
        if OCR_DISPONIVEL:
            self.log("OCR disponivel!", "sucesso")
        else:
            self.log("Tesseract nao encontrado. Le apenas do nome do ficheiro.", "alerta")
        
        self.log("Aplicacao iniciada.", "info")
        
    def log(self, mensagem, tipo="info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {mensagem}\n", tipo)
        self.log_text.see("end")
        self.root.update()
        
    def limpar_log(self):
        self.log_text.delete(1.0, tk.END)
        
    def selecionar_pasta(self):
        pasta = filedialog.askdirectory(title="Selecionar pasta com imagens")
        if pasta:
            self.pasta_selecionada = pasta
            self.label_pasta.config(text=pasta)
            self.btn_processar.config(state="normal")
            self.log(f"Pasta: {pasta}", "info")
            imagens = [f for f in os.listdir(pasta) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            self.log(f"Encontradas {len(imagens)} imagens.", "info")
                
    def extrair_coordenadas(self, texto):
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
                    return lat, lon
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
                    return lat, lon
            except:
                pass
        
        # Formato 3: 37288337N 8695660W
        padrao3 = r'(\d{8,9})[NnSs]\s*(\d{7,8})[WwEe]'
        match = re.search(padrao3, texto)
        if match:
            try:
                lat_str = match.group(1)
                lon_str = match.group(2)
                lat = float(lat_str[:2] + '.' + lat_str[2:])
                lon = -(float(lon_str[:1] + '.' + lon_str[1:]))
                if 36 <= lat <= 42 and -10 <= lon <= -6:
                    return lat, lon
            except:
                pass
        
        return None, None
    
    def processar_imagens(self):
        if not self.pasta_selecionada:
            messagebox.showerror("Erro", "Selecione uma pasta!")
            return
        
        self.btn_processar.config(state="disabled")
        self.btn_gerar_kmz.config(state="disabled")
        self.progresso["value"] = 0
        
        self.log("\n" + "="*70, "destaque")
        self.log("INICIANDO PROCESSAMENTO...", "destaque")
        self.log("="*70, "destaque")
        
        threading.Thread(target=self._processar_imagens_thread, daemon=True).start()
    
    def _processar_imagens_thread(self):
        try:
            self.resultados = []
            self.erros = []
            
            imagens = [f for f in os.listdir(self.pasta_selecionada) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            
            if not imagens:
                self.log("Nenhuma imagem encontrada!", "erro")
                self.btn_processar.config(state="normal")
                return
            
            total = len(imagens)
            self.log(f"Encontradas {total} imagens.", "info")
            
            for i, ficheiro in enumerate(imagens, 1):
                caminho = os.path.join(self.pasta_selecionada, ficheiro)
                self.progresso["value"] = (i / total) * 50
                self.log(f"[{i}/{total}] {ficheiro}", "info")
                
                lat, lon = None, None
                
                if OCR_DISPONIVEL:
                    try:
                        imagem = Image.open(caminho)
                        if imagem.width > 2000 or imagem.height > 2000:
                            imagem.thumbnail((2000, 2000))
                        texto = pytesseract.image_to_string(imagem, lang='por+eng')
                        lat, lon = self.extrair_coordenadas(texto)
                        if lat is not None:
                            self.log(f"  OCR: encontrado", "info")
                    except:
                        pass
                
                if lat is None:
                    lat, lon = self.extrair_coordenadas(ficheiro)
                    if lat is not None:
                        self.log(f"  Nome: encontrado", "info")
                
                if lat is not None:
                    self.resultados.append({'nome': ficheiro, 'lat': lat, 'lon': lon})
                    self.log(f"  OK: {lat:.6f}, {lon:.6f}", "sucesso")
                else:
                    self.erros.append({'nome': ficheiro})
                    self.log(f"  Sem coordenadas", "alerta")
            
            self.progresso["value"] = 100
            
            self.log("\n" + "="*70, "destaque")
            self.log(f"Processamento concluido!", "sucesso")
            self.log(f"   Com coordenadas: {len(self.resultados)}", "sucesso")
            self.log(f"   Sem coordenadas: {len(self.erros)}", "alerta" if len(self.erros) > 0 else "info")
            self.log("="*70, "destaque")
            
            if len(self.resultados) >= 3:
                self.detetar_outliers()
            else:
                self.pontos_finais = self.resultados.copy()
                self.btn_gerar_kmz.config(state="normal")
            
            self.btn_processar.config(state="normal")
            
            if self.pontos_finais:
                self.btn_gerar_kmz.config(state="normal")
            
        except Exception as e:
            self.log(f"Erro: {str(e)}", "erro")
            self.btn_processar.config(state="normal")
            self.progresso["value"] = 0
    
    def detetar_outliers(self):
        if len(self.resultados) < 3:
            self.pontos_finais = self.resultados.copy()
            self.btn_gerar_kmz.config(state="normal")
            return
        
        coords = np.array([[p['lat'], p['lon']] for p in self.resultados])
        centro = np.median(coords, axis=0)
        dist = distance.cdist([centro], coords)[0]
        limiar = 2.5 * np.median(dist) if np.median(dist) > 0 else 0.005
        
        self.log(f"\nAnalise de outliers:", "info")
        self.log(f"   Limiar: {limiar*111000:.0f} m", "info")
        
        self.outliers = []
        self.normais = []
        
        for i, ponto in enumerate(self.resultados):
            if dist[i] > limiar:
                self.outliers.append(ponto)
                self.log(f"  ALERTA: {ponto['nome']} isolado! {dist[i]*111000:.0f} m", "alerta")
            else:
                self.normais.append(ponto)
        
        if self.outliers:
            self.log(f"\nEncontrados {len(self.outliers)} ponto(s) isolado(s).", "alerta")
            self.root.after(0, self.perguntar_outliers)
        else:
            self.log("Nenhum ponto isolado.", "sucesso")
            self.pontos_finais = self.resultados.copy()
            self.btn_gerar_kmz.config(state="normal")
    
    def perguntar_outliers(self):
        msg = f"Foram detectados {len(self.outliers)} ponto(s) isolado(s):\n\n"
        for o in self.outliers[:5]:
            msg += f"• {o['nome']}\n"
        if len(self.outliers) > 5:
            msg += f"\n... e mais {len(self.outliers) - 5} pontos"
        msg += "\n\nIncluir no KMZ?"
        
        if messagebox.askyesno("Pontos Isolados", msg):
            self.pontos_finais = self.resultados.copy()
            self.log("Mantidos.", "info")
        else:
            self.pontos_finais = self.normais.copy()
            self.log(f"Removidos. {len(self.pontos_finais)} restantes.", "info")
        
        self.btn_gerar_kmz.config(state="normal")
    
    def gerar_kmz(self):
        if not self.pontos_finais:
            messagebox.showerror("Erro", "Sem pontos!")
            return
        
        caminho_kmz = filedialog.asksaveasfilename(
            defaultextension=".kmz",
            filetypes=[("KMZ files", "*.kmz")],
            title="Guardar KMZ"
        )
        
        if not caminho_kmz:
            return
        
        self.btn_gerar_kmz.config(state="disabled")
        self.progresso["value"] = 0
        
        try:
            self.log("\n" + "="*70, "destaque")
            self.log("GERANDO KMZ...", "destaque")
            self.log("="*70, "destaque")
            
            temp_dir = tempfile.mkdtemp()
            kml_path = os.path.join(temp_dir, "document.kml")
            imagens_dir = os.path.join(temp_dir, "imagens")
            os.makedirs(imagens_dir, exist_ok=True)
            
            kml = simplekml.Kml()
            kml.document.name = "Pontos extraidos"
            
            total = len(self.pontos_finais)
            
            for i, ponto in enumerate(self.pontos_finais, 1):
                self.progresso["value"] = (i / total) * 80
                
                origem = os.path.join(self.pasta_selecionada, ponto['nome'])
                destino = os.path.join(imagens_dir, ponto['nome'])
                
                if os.path.exists(origem):
                    shutil.copy2(origem, destino)
                    self.log(f"[{i}/{total}] {ponto['nome']}", "info")
                else:
                    self.log(f"Imagem nao encontrada: {ponto['nome']}", "alerta")
                    continue
                
                p = kml.newpoint()
                p.name = ponto['nome']
                p.description = f'<img src="imagens/{ponto['nome']}" width="400"/><br/><b>Coordenada:</b> {ponto['lat']:.6f}, {ponto['lon']:.6f}'
                p.coords = [(ponto['lon'], ponto['lat'])]
            
            kml.save(kml_path)
            self.log(f"KML gerado.", "sucesso")
            
            self.progresso["value"] = 90
            self.log("Criando KMZ...", "info")
            
            with zipfile.ZipFile(caminho_kmz, 'w', zipfile.ZIP_DEFLATED) as kmz:
                kmz.write(kml_path, "document.kml")
                for f in os.listdir(imagens_dir):
                    kmz.write(os.path.join(imagens_dir, f), f"imagens/{f}")
            
            shutil.rmtree(temp_dir)
            
            self.progresso["value"] = 100
            self.arquivo_kmz = caminho_kmz
            
            self.log("\n" + "="*70, "destaque")
            self.log(f"KMZ GERADO!", "sucesso")
            self.log(f"   Ficheiro: {caminho_kmz}", "info")
            self.log(f"   Pontos: {len(self.pontos_finais)}", "info")
            self.log("="*70, "destaque")
            
            self.btn_gerar_kmz.config(state="normal")
            self.btn_abrir.config(state="normal")
            
            messagebox.showinfo("Sucesso", f"KMZ gerado!\n\n{caminho_kmz}\n\n{len(self.pontos_finais)} pontos.")
            
        except Exception as e:
            self.log(f"Erro: {str(e)}", "erro")
            self.btn_gerar_kmz.config(state="normal")
            self.progresso["value"] = 0
    
    def abrir_kmz(self):
        if self.arquivo_kmz and os.path.exists(self.arquivo_kmz):
            os.startfile(os.path.dirname(self.arquivo_kmz))
    
    def mostrar_ajuda(self):
        ajuda = """
GERADOR DE KMZ

1. Selecionar Pasta com imagens
2. Processar Imagens
3. Gerar KMZ

Formatos suportados:
• 37.283627N 8.694865W
• 37.283627, -8.694865
• 37288337N 8695660W
"""
        messagebox.showinfo("Como usar", ajuda)

def main():
    try:
        root = tk.Tk()
        app = GeradorKMZApp(root)
        root.mainloop()
    except Exception as e:
        print(f"Erro: {e}")
        input("Pressione Enter para sair...")

if __name__ == "__main__":
    main()