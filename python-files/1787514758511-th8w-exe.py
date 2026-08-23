import tkinter as tk
from tkinter import messagebox
import random

class JogoDado:
    def __init__(self, root):
        self.root = root
        self.root.title("🎲 Jogo do Dado - 2 Jogadores")
        self.root.geometry("700x600")
        self.root.configure(bg='#2c3e50')
        
        # Configurações do jogo
        self.total_casas = 30
        self.posicao_jogador1 = 0
        self.posicao_jogador2 = 0
        self.vez = 1  # 1 = Jogador 1, 2 = Jogador 2
        self.jogo_ativo = True
        
        # Criar interface
        self.criar_interface()
        self.criar_tabuleiro()
        self.atualizar_tabuleiro()
        
    def criar_interface(self):
        # Título
        titulo = tk.Label(self.root, text="🎲 JOGO DO DADO", 
                         font=('Arial', 24, 'bold'), 
                         bg='#2c3e50', fg='#ecf0f1')
        titulo.pack(pady=10)
        
        # Frame principal
        self.frame_principal = tk.Frame(self.root, bg='#2c3e50')
        self.frame_principal.pack(pady=10)
        
        # Frame do tabuleiro (grid de casas)
        self.frame_tabuleiro = tk.Frame(self.frame_principal, bg='#34495e', padx=10, pady=10)
        self.frame_tabuleiro.pack()
        
        # Frame de informações
        self.frame_info = tk.Frame(self.root, bg='#2c3e50')
        self.frame_info.pack(pady=20)
        
        # Status do jogador
        self.label_status = tk.Label(self.frame_info, 
                                    text="🎯 Vez do Jogador 1", 
                                    font=('Arial', 16, 'bold'),
                                    bg='#2c3e50', fg='#ecf0f1')
        self.label_status.pack()
        
        # Posições
        self.label_posicoes = tk.Label(self.frame_info, 
                                      text="J1: Casa 0 | J2: Casa 0",
                                      font=('Arial', 14),
                                      bg='#2c3e50', fg='#bdc3c7')
        self.label_posicoes.pack(pady=5)
        
        # Frame do dado
        self.frame_dado = tk.Frame(self.root, bg='#2c3e50')
        self.frame_dado.pack(pady=10)
        
        # Display do dado
        self.label_dado = tk.Label(self.frame_dado, 
                                  text="⚀", 
                                  font=('Arial', 60),
                                  bg='#2c3e50', fg='#f1c40f')
        self.label_dado.pack(side=tk.LEFT, padx=20)
        
        # Botão de rolar dado
        self.btn_rolar = tk.Button(self.frame_dado, 
                                  text="🎲 ROLAR DADO", 
                                  font=('Arial', 14, 'bold'),
                                  bg='#3498db', fg='white',
                                  padx=20, pady=10,
                                  command=self.rolar_dado,
                                  cursor='hand2')
        self.btn_rolar.pack(side=tk.LEFT, padx=20)
        
        # Botão reiniciar
        self.btn_reiniciar = tk.Button(self.root, 
                                      text="🔄 NOVO JOGO", 
                                      font=('Arial', 12, 'bold'),
                                      bg='#e74c3c', fg='white',
                                      padx=15, pady=8,
                                      command=self.reiniciar_jogo,
                                      cursor='hand2')
        self.btn_reiniciar.pack(pady=10)
        
        # Legenda
        legenda = tk.Label(self.root, 
                          text="🔵 Jogador 1  |  🔴 Jogador 2",
                          font=('Arial', 12),
                          bg='#2c3e50', fg='#bdc3c7')
        legenda.pack(pady=5)
        
    def criar_tabuleiro(self):
        # Criar grid de casas (6 colunas x 5 linhas)
        self.casas = []
        colunas = 6
        linha_atual = 0
        
        # Criar labels para cada casa
        for i in range(self.total_casas):
            linha = i // colunas
            coluna = i % colunas
            
            # Alternar direção das linhas (cobra)
            if linha % 2 == 1:
                coluna = colunas - 1 - coluna
            
            # Cor da casa (alternando)
            cor = '#ecf0f1' if (i % 2 == 0) else '#bdc3c7'
            
            casa = tk.Label(self.frame_tabuleiro, 
                           text=str(i+1), 
                           font=('Arial', 10, 'bold'),
                           width=6, height=3,
                           bg=cor, fg='#2c3e50',
                           relief='raised', bd=2)
            casa.grid(row=linha, column=coluna, padx=3, pady=3)
            self.casas.append(casa)
            
    def atualizar_tabuleiro(self):
        # Resetar cores das casas
        for i, casa in enumerate(self.casas):
            cor = '#ecf0f1' if (i % 2 == 0) else '#bdc3c7'
            casa.configure(bg=cor, text=str(i+1))
        
        # Marcar posição do Jogador 1 (azul)
        if self.posicao_jogador1 < self.total_casas:
            self.casas[self.posicao_jogador1].configure(bg='#3498db', fg='white', 
                                                        text=f"{self.posicao_jogador1+1}\n🔵")
        
        # Marcar posição do Jogador 2 (vermelho)
        if self.posicao_jogador2 < self.total_casas:
            self.casas[self.posicao_jogador2].configure(bg='#e74c3c', fg='white',
                                                        text=f"{self.posicao_jogador2+1}\n🔴")
        
        # Se ambos na mesma casa, mostrar ambos
        if (self.posicao_jogador1 == self.posicao_jogador2 and 
            self.posicao_jogador1 < self.total_casas):
            self.casas[self.posicao_jogador1].configure(bg='#9b59b6', fg='white',
                                                        text=f"{self.posicao_jogador1+1}\n🔵🔴")
        
        # Atualizar label de posições
        self.label_posicoes.config(text=f"J1: Casa {self.posicao_jogador1+1} | J2: Casa {self.posicao_jogador2+1}")
        
    def rolar_dado(self):
        if not self.jogo_ativo:
            return
            
        # Sortear número do dado (1 a 6)
        numero = random.randint(1, 6)
        
        # Atualizar display do dado
        dados = {1: '⚀', 2: '⚁', 3: '⚂', 4: '⚃', 5: '⚄', 6: '⚅'}
        self.label_dado.config(text=dados[numero])
        
        # Mover jogador atual
        if self.vez == 1:
            self.posicao_jogador1 += numero
            if self.posicao_jogador1 >= self.total_casas:
                self.posicao_jogador1 = self.total_casas - 1
                self.finalizar_jogo(1)
                return
            self.label_status.config(text="🎯 Vez do Jogador 2", fg='#e74c3c')
            self.vez = 2
        else:
            self.posicao_jogador2 += numero
            if self.posicao_jogador2 >= self.total_casas:
                self.posicao_jogador2 = self.total_casas - 1
                self.finalizar_jogo(2)
                return
            self.label_status.config(text="🎯 Vez do Jogador 1", fg='#3498db')
            self.vez = 1
            
        # Atualizar tabuleiro
        self.atualizar_tabuleiro()
        
        # Verificar se alguém ganhou (se passar exatamente)
        if self.posicao_jogador1 == self.total_casas - 1:
            self.finalizar_jogo(1)
        elif self.posicao_jogador2 == self.total_casas - 1:
            self.finalizar_jogo(2)
    
    def finalizar_jogo(self, jogador):
        self.jogo_ativo = False
        self.btn_rolar.config(state='disabled')
        
        vencedor = f"Jogador {jogador}"
        cor = '#3498db' if jogador == 1 else '#e74c3c'
        
        messagebox.showinfo("🏆 FIM DE JOGO!", 
                           f"🎉 {vencedor} VENCEU! 🎉\n\n"
                           f"Jogador 1: Casa {self.posicao_jogador1+1}\n"
                           f"Jogador 2: Casa {self.posicao_jogador2+1}\n\n"
                           f"👏 Parabéns!")
        
        self.label_status.config(text=f"🏆 {vencedor} Venceu!", fg=cor)
    
    def reiniciar_jogo(self):
        self.posicao_jogador1 = 0
        self.posicao_jogador2 = 0
        self.vez = 1
        self.jogo_ativo = True
        self.btn_rolar.config(state='normal')
        self.label_dado.config(text="⚀")
        self.label_status.config(text="🎯 Vez do Jogador 1", fg='#3498db')
        self.atualizar_tabuleiro()

# Rodar o jogo
if __name__ == "__main__":
    root = tk.Tk()
    jogo = JogoDado(root)
    root.mainloop()