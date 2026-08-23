import tkinter as tk
from tkinter import messagebox
import random
import time
import threading

class JogoDadoCompleto:
    def __init__(self, root):
        self.root = root
        self.root.title("🎲 Jogo do Dado - 2 Jogadores")
        self.root.geometry("1100x700")
        self.root.configure(bg='#1a1a2e')
        self.root.resizable(False, False)
        
        # Configurações do jogo
        self.total_casas = 20
        self.posicao_jogador1 = 0
        self.posicao_jogador2 = 0
        self.vez = 1
        self.jogo_ativo = False
        self.dado_rodando = False
        
        # Cores
        self.cores = {
            'bg': '#1a1a2e',
            'j1': '#00d4ff',
            'j2': '#ff6b6b',
            'casa_normal': '#16213e',
            'casa_destaque': '#0f3460',
            'texto': '#ffffff'
        }
        
        self.criar_interface()
        
    def criar_interface(self):
        # Frame principal
        frame_principal = tk.Frame(self.root, bg=self.cores['bg'])
        frame_principal.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Título
        titulo = tk.Label(frame_principal, text="🎲 JOGO DO DADO", 
                         font=('Arial', 28, 'bold'), 
                         bg=self.cores['bg'], fg='#f1c40f')
        titulo.grid(row=0, column=0, columnspan=3, pady=10)
        
        # ----- LADO ESQUERDO - JOGADOR 1 -----
        frame_j1 = tk.Frame(frame_principal, bg='#0f3460', relief='ridge', bd=3)
        frame_j1.grid(row=1, column=0, padx=15, pady=10, sticky='n')
        
        tk.Label(frame_j1, text="JOGADOR 1", font=('Arial', 16, 'bold'),
                bg='#0f3460', fg=self.cores['j1']).pack(pady=10)
        
        tk.Label(frame_j1, text="Nome:", font=('Arial', 12),
                bg='#0f3460', fg=self.cores['texto']).pack()
        
        self.nome_j1 = tk.Entry(frame_j1, font=('Arial', 14), width=20,
                                bg='#16213e', fg='white', insertbackground='white')
        self.nome_j1.pack(pady=5, padx=10)
        
        tk.Label(frame_j1, text=f"Posição: Casa 0", font=('Arial', 12),
                bg='#0f3460', fg=self.cores['texto']).pack(pady=5)
        
        self.status_j1 = tk.Label(frame_j1, text="⏳ Aguardando...", font=('Arial', 11),
                                 bg='#0f3460', fg='#95a5a6')
        self.status_j1.pack(pady=5)
        
        # Botão do Jogador 1
        self.btn_j1 = tk.Button(frame_j1, text="🎲 JOGAR DADO", 
                               font=('Arial', 12, 'bold'),
                               bg='#00d4ff', fg='#1a1a2e',
                               width=15, height=2,
                               command=self.jogar_dado,
                               state='disabled',
                               cursor='hand2')
        self.btn_j1.pack(pady=15, padx=10)
        
        # ----- CENTRO - TABULEIRO E DADO -----
        frame_central = tk.Frame(frame_principal, bg=self.cores['bg'])
        frame_central.grid(row=1, column=1, padx=20)
        
        # Tabuleiro (20 casas em formato de retângulo)
        self.frame_tabuleiro = tk.Frame(frame_central, bg='#0f3460', padx=15, pady=15)
        self.frame_tabuleiro.pack()
        
        self.criar_tabuleiro()
        
        # Display do dado central
        self.frame_dado = tk.Frame(frame_central, bg='#1a1a2e')
        self.frame_dado.pack(pady=10)
        
        self.label_dado = tk.Label(self.frame_dado, text="⚀", 
                                   font=('Arial', 80),
                                   bg='#1a1a2e', fg='#f1c40f')
        self.label_dado.pack()
        
        self.label_vez = tk.Label(frame_central, text="🔴 Clique em 'JOGAR DADO' para começar",
                                 font=('Arial', 14, 'bold'),
                                 bg='#1a1a2e', fg='#f1c40f')
        self.label_vez.pack(pady=5)
        
        # ----- LADO DIREITO - JOGADOR 2 -----
        frame_j2 = tk.Frame(frame_principal, bg='#0f3460', relief='ridge', bd=3)
        frame_j2.grid(row=1, column=2, padx=15, pady=10, sticky='n')
        
        tk.Label(frame_j2, text="JOGADOR 2", font=('Arial', 16, 'bold'),
                bg='#0f3460', fg=self.cores['j2']).pack(pady=10)
        
        tk.Label(frame_j2, text="Nome:", font=('Arial', 12),
                bg='#0f3460', fg=self.cores['texto']).pack()
        
        self.nome_j2 = tk.Entry(frame_j2, font=('Arial', 14), width=20,
                                bg='#16213e', fg='white', insertbackground='white')
        self.nome_j2.pack(pady=5, padx=10)
        
        tk.Label(frame_j2, text=f"Posição: Casa 0", font=('Arial', 12),
                bg='#0f3460', fg=self.cores['texto']).pack(pady=5)
        
        self.status_j2 = tk.Label(frame_j2, text="⏳ Aguardando...", font=('Arial', 11),
                                 bg='#0f3460', fg='#95a5a6')
        self.status_j2.pack(pady=5)
        
        # Botão do Jogador 2
        self.btn_j2 = tk.Button(frame_j2, text="🎲 JOGAR DADO", 
                               font=('Arial', 12, 'bold'),
                               bg='#ff6b6b', fg='#1a1a2e',
                               width=15, height=2,
                               command=self.jogar_dado,
                               state='disabled',
                               cursor='hand2')
        self.btn_j2.pack(pady=15, padx=10)
        
        # Botão Reiniciar
        btn_reiniciar = tk.Button(frame_principal, text="🔄 NOVO JOGO", 
                                 font=('Arial', 14, 'bold'),
                                 bg='#e74c3c', fg='white',
                                 width=15, height=1,
                                 command=self.reiniciar_jogo,
                                 cursor='hand2')
        btn_reiniciar.grid(row=2, column=0, columnspan=3, pady=15)
        
        # Vincular evento de mudança nos campos de nome
        self.nome_j1.bind('<KeyRelease>', self.verificar_nomes)
        self.nome_j2.bind('<KeyRelease>', self.verificar_nomes)
        
        # Atualizar posições
        self.atualizar_posicoes()
        
    def criar_tabuleiro(self):
        """Cria 20 casas em formato de retângulo (5x4)"""
        self.casas = []
        linhas = 4
        colunas = 5
        
        for i in range(self.total_casas):
            linha = i // colunas
            coluna = i % colunas
            
            # Alternar direção (serpentina)
            if linha % 2 == 1:
                coluna = colunas - 1 - coluna
            
            # Número da casa
            num_casa = i + 1
            
            casa = tk.Label(self.frame_tabuleiro, 
                           text=str(num_casa), 
                           font=('Arial', 10, 'bold'),
                           width=8, height=3,
                           bg=self.cores['casa_normal'],
                           fg='white',
                           relief='ridge', bd=2)
            casa.grid(row=linha, column=coluna, padx=4, pady=4)
            self.casas.append(casa)
    
    def verificar_nomes(self, event=None):
        """Verifica se ambos os nomes foram preenchidos"""
        nome1 = self.nome_j1.get().strip()
        nome2 = self.nome_j2.get().strip()
        
        if nome1 and nome2:
            self.btn_j1.config(state='normal')
            self.btn_j2.config(state='normal')
            if not self.jogo_ativo:
                self.label_vez.config(text=f"🎯 {nome1} começa!", fg='#00d4ff')
                self.status_j1.config(text="🎯 Sua vez!", fg='#00d4ff')
                self.status_j2.config(text="⏳ Aguardando...", fg='#95a5a6')
                self.jogo_ativo = True
                self.vez = 1
                self.btn_j2.config(state='disabled')
        else:
            self.btn_j1.config(state='disabled')
            self.btn_j2.config(state='disabled')
            self.label_vez.config(text="⚠️ Preencha os nomes dos dois jogadores!", fg='#e74c3c')
            self.jogo_ativo = False
    
    def jogar_dado(self):
        """Função principal para jogar o dado"""
        if self.dado_rodando or not self.jogo_ativo:
            return
        
        # Verificar se é a vez do jogador correto
        nome1 = self.nome_j1.get().strip()
        nome2 = self.nome_j2.get().strip()
        
        if self.vez == 1:
            if self.btn_j1['state'] == 'disabled':
                return
            jogador_atual = nome1
            cor = self.cores['j1']
            self.btn_j1.config(state='disabled')
        else:
            if self.btn_j2['state'] == 'disabled':
                return
            jogador_atual = nome2
            cor = self.cores['j2']
            self.btn_j2.config(state='disabled')
        
        # Desabilitar ambos os botões durante animação
        self.btn_j1.config(state='disabled')
        self.btn_j2.config(state='disabled')
        self.dado_rodando = True
        
        # Animar o dado
        self.animar_dado(jogador_atual, cor)
    
    def animar_dado(self, jogador, cor):
        """Anima o dado rodando antes de mostrar o resultado"""
        dados = ['⚀', '⚁', '⚂', '⚃', '⚄', '⚅']
        
        def animar():
            # Rodar o dado por 1.5 segundos
            for _ in range(20):
                numero_anim = random.randint(1, 6)
                self.label_dado.config(text=dados[numero_anim-1])
                self.root.update()
                time.sleep(0.08)
            
            # Resultado final
            numero_final = random.randint(1, 6)
            self.label_dado.config(text=dados[numero_final-1])
            
            # Processar movimento
            self.processar_movimento(jogador, numero_final, cor)
        
        # Executar animação em thread separada
        threading.Thread(target=animar, daemon=True).start()
    
    def processar_movimento(self, jogador, numero, cor):
        """Processa o movimento do jogador"""
        if self.vez == 1:
            self.posicao_jogador1 += numero
            if self.posicao_jogador1 >= self.total_casas:
                self.posicao_jogador1 = self.total_casas - 1
                self.finalizar_jogo(1)
                return
            self.vez = 2
            self.status_j1.config(text=f"✅ Andou {numero} casas!", fg='#2ecc71')
            self.status_j2.config(text="🎯 Sua vez!", fg='#ff6b6b')
            self.label_vez.config(text=f"🎯 Vez de {self.nome_j2.get().strip()}", fg='#ff6b6b')
            self.btn_j2.config(state='normal')
        else:
            self.posicao_jogador2 += numero
            if self.posicao_jogador2 >= self.total_casas:
                self.posicao_jogador2 = self.total_casas - 1
                self.finalizar_jogo(2)
                return
            self.vez = 1
            self.status_j2.config(text=f"✅ Andou {numero} casas!", fg='#2ecc71')
            self.status_j1.config(text="🎯 Sua vez!", fg='#00d4ff')
            self.label_vez.config(text=f"🎯 Vez de {self.nome_j1.get().strip()}", fg='#00d4ff')
            self.btn_j1.config(state='normal')
        
        # Atualizar tabuleiro
        self.atualizar_posicoes()
        self.dado_rodando = False
        
        # Verificar se alguém ganhou (casa 20)
        if self.posicao_jogador1 == self.total_casas - 1:
            self.finalizar_jogo(1)
        elif self.posicao_jogador2 == self.total_casas - 1:
            self.finalizar_jogo(2)
    
    def atualizar_posicoes(self):
        """Atualiza o tabuleiro com as posições dos jogadores"""
        # Resetar cores das casas
        for i, casa in enumerate(self.casas):
            casa.configure(bg=self.cores['casa_normal'], 
                          fg='white',
                          text=str(i+1))
        
        # Marcar posição do Jogador 1
        if self.posicao_jogador1 < self.total_casas:
            self.casas[self.posicao_jogador1].configure(bg='#00d4ff', fg='#1a1a2e',
                                                        text=f"{self.posicao_jogador1+1}\n🔵")
        
        # Marcar posição do Jogador 2
        if self.posicao_jogador2 < self.total_casas:
            self.casas[self.posicao_jogador2].configure(bg='#ff6b6b', fg='#1a1a2e',
                                                        text=f"{self.posicao_jogador2+1}\n🔴")
        
        # Se ambos na mesma casa
        if (self.posicao_jogador1 == self.posicao_jogador2 and 
            self.posicao_jogador1 < self.total_casas):
            self.casas[self.posicao_jogador1].configure(bg='#9b59b6', fg='white',
                                                        text=f"{self.posicao_jogador1+1}\n🔵🔴")
        
        # Atualizar labels de posição
        for widget in self.root.winfo_children():
            for frame in widget.winfo_children():
                if isinstance(frame, tk.Frame):
                    for child in frame.winfo_children():
                        if isinstance(child, tk.Label) and 'Posição:' in child.cget('text'):
                            if 'JOGADOR 1' in str(child.master.winfo_children()):
                                child.config(text=f"Posição: Casa {self.posicao_jogador1+1}")
                            elif 'JOGADOR 2' in str(child.master.winfo_children()):
                                child.config(text=f"Posição: Casa {self.posicao_jogador2+1}")
    
    def finalizar_jogo(self, jogador):
        """Finaliza o jogo com vitória"""
        self.jogo_ativo = False
        self.dado_rodando = False
        self.btn_j1.config(state='disabled')
        self.btn_j2.config(state='disabled')
        
        nome1 = self.nome_j1.get().strip()
        nome2 = self.nome_j2.get().strip()
        
        vencedor = nome1 if jogador == 1 else nome2
        cor = '#00d4ff' if jogador == 1 else '#ff6b6b'
        
        self.label_vez.config(text=f"🏆 {vencedor} VENCEU! 🏆", fg='#f1c40f')
        
        if jogador == 1:
            self.status_j1.config(text="🏆 VENCEDOR!", fg='#f1c40f')
            self.status_j2.config(text="😢 Perdeu...", fg='#95a5a6')
        else:
            self.status_j2.config(text="🏆 VENCEDOR!", fg='#f1c40f')
            self.status_j1.config(text="😢 Perdeu...", fg='#95a5a6')
        
        messagebox.showinfo("🏆 FIM DE JOGO!", 
                           f"🎉 {vencedor} VENCEU! 🎉\n\n"
                           f"{nome1}: Casa {self.posicao_jogador1+1}\n"
                           f"{nome2}: Casa {self.posicao_jogador2+1}\n\n"
                           f"👏 Parabéns, {vencedor}!")
    
    def reiniciar_jogo(self):
        """Reinicia o jogo completamente"""
        self.posicao_jogador1 = 0
        self.posicao_jogador2 = 0
        self.vez = 1
        self.jogo_ativo = False
        self.dado_rodando = False
        
        self.label_dado.config(text="⚀")
        self.btn_j1.config(state='disabled')
        self.btn_j2.config(state='disabled')
        self.status_j1.config(text="⏳ Aguardando...", fg='#95a5a6')
        self.status_j2.config(text="⏳ Aguardando...", fg='#95a5a6')
        self.label_vez.config(text="⚠️ Preencha os nomes dos dois jogadores!", fg='#e74c3c')
        
        # Limpar campos
        self.nome_j1.delete(0, tk.END)
        self.nome_j2.delete(0, tk.END)
        
        self.atualizar_posicoes()

# Executar o jogo
if __name__ == "__main__":
    root = tk.Tk()
    jogo = JogoDadoCompleto(root)
    root.mainloop()