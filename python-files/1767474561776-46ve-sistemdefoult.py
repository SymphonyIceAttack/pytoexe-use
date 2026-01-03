import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import os

def verificar_codigo():
    codigo_admin = 'SLAVA'
    codigo_defoult = 'KAWASAKI'
    if entrada_codigo.get() == codigo_admin:
        messagebox.showinfo('Acesso concedido', 'Welcome home')
        janela_senha.destroy()
        abrir_janela_texto(nivel='Admin')
#níveis de acesso
    elif entrada_codigo.get() == codigo_defoult:
        messagebox.showinfo('Acesso concedido', 'Lets work, welcome')
        abrir_janela_texto(nivel='defoult')

    else:
        messagebox.showerror("Acesso negado", "Código de acesso negado!")
#área de texto
def abrir_janela_texto(nivel):
    janela_texto = tk.Tk()
    janela_texto.title("Terminal CCM")
    janela_texto.configure(bg="black")
    janela_texto.overrideredirect(True)
    janela_texto.geometry(f"{janela_texto.winfo_screenwidth()}x{janela_texto.winfo_screenheight()}+0+0")

    configs = {
        'Admin':   {'bg': 'black',   'fg': '#00ff00', 'cursor': 'white', 'titulo': 'Admin CCM'},
        'defoult': {'bg': '#1a0000', 'fg': '#ff3333', 'cursor': 'red', 'titulo':'Defoult CCM'}
    }

    cor = configs[nivel]
    

    lbl_instrucao = tk.Label(janela_texto, text=cor['titulo'], font=('Consolas', 14, 'bold'),
                             bg=cor['bg'], fg=cor['fg'])
    lbl_instrucao.pack(pady=20)

    area_texto = tk.Text(janela_texto, font=('Consolas', 14),
                         bg=cor['bg'], fg=cor['fg'],
                         insertbackground=cor['cursor'],
                         relief='flat', undo=True)
    area_texto.pack(padx=30, pady=(0, 30), fill='both', expand=True)
    area_texto.focus()

    cod = str.maketrans({ 'a':'#', 'A':'#','b':'x', 'B':'x','c':'/', 'C':'/','d':'8', 'D':'8','e':'&', 'E':'&','f':'5', 'F':'5', 'g':'^', 'G':'^','h':'-', 'H':'-','i':'1', 'I':'1','j':'!', 'J':'!','k':'*', 'K':'*','l':';', 'L':';', 'm':'(', 'M':'(',
'n':'{', 'N':'{','o':'.', 'O':'.','p':'6', 'P':'6','q':'0', 'Q':'0','r':'+', 'R':'+','s':'>', 'S':'>','t':'<', 'T':'<','u':'_', 'U':'_','v':'3', 'V':'3','w':'?', 'W':'?','x':'c', 'X':'c','y':'7', 'Y':'7','z':')', 'Z':')'})

    def verificar_comando(event=None):
        texto = area_texto.get('1.0', 'end-1c')
        linhas = texto.splitlines()

        if texto.endswith('//cls'):
            area_texto.delete('1.0', tk.END)

        if texto.endswith('//done'):
            janela_texto.destroy()
            janela_senha.destroy()

        if texto.endswith('//key'):
            janela_texto.overrideredirect(False)

        if texto.endswith('//diskey'):
            janela_texto.overrideredirect(True)

        for i, l in enumerate(linhas):
            if l.strip().lower() == '//save':
                conteudo = linhas[:i]

                if not conteudo:
                    messagebox.showwarning('AVISO', 'Nada para salvar acima //save')
                    return

                codificado = '\n'.join(l.translate(cod) for l in conteudo)

                nome_arq = simpledialog.askstring('Salvar', 'Nome do arquivo:')
                if nome_arq:
                    nome_arq += ".txt"

                try:
                    with open(nome_arq, 'w', encoding='utf-8') as f:
                        f.write(codificado)
                        area_texto.insert('end', f'\n\n>Arquivo salvo como: {nome_arq}\n')

                    novo_texto = '\n'.join(linhas[i+1:])
                    area_texto.delete('1.0', 'end')
                    area.texto.insert('1.0', novo_texto)

                except:
                    messagebox.showerror('Error', 'Falha ao salvar arquivo')
                return

        if texto.endswith('//decod'):
            codificado(False)
  
    area_texto.bind('<KeyRelease>', verificar_comando)
    

    area_texto.insert('1.0', f'> Acesso concedido como nivel: {nivel.upper()}\n')
    area_texto.focus()
    janela_texto.mainloop()


#janela de senha
janela_senha = tk.Tk()
janela_senha.title('Código de Acesso')
janela_senha.geometry('400x300')
janela_senha.configure(bg='#111111')
janela_senha.resizable(False, False)

lbl_titulo = tk.Label(janela_senha, text='Insira o código de acesso:',
                      font=('Arial', 14), bg='#e0e0e0')
lbl_titulo.pack(pady=30)

entrada_codigo = tk.Entry(janela_senha, show="*", font=('Arial', 14), justify='center')
entrada_codigo.pack(pady=10)
entrada_codigo.focus()

btn_entrar = tk.Button(janela_senha, text="Entrar", font=('Arial', 12),
                       command=verificar_codigo).pack(pady=20)

#Protótipo de comandos





