
import os
import shutil
import subprocess
import tkinter as tk
from tkinter import messagebox
from datetime import datetime

def reset_anydesk():
    try:
        # Encerrar AnyDesk
        subprocess.run("taskkill /f /im AnyDesk.exe", shell=True)

        path = os.path.join(os.getenv("APPDATA"), "AnyDesk")

        if os.path.exists(path):
            shutil.rmtree(path)
            log_operacao("Pasta removida com sucesso.")
            messagebox.showinfo("Nuvix Computadores", "Reset realizado com sucesso.\nA pasta AnyDesk foi removida.")
        else:
            log_operacao("Pasta não encontrada.")
            messagebox.showwarning("Nuvix Computadores", "A pasta AnyDesk não foi encontrada.")
    except Exception as e:
        log_operacao(f"Erro: {e}")
        messagebox.showerror("Nuvix Computadores", f"Ocorreu um erro:\n{e}")

def log_operacao(mensagem):
    log_path = os.path.join(os.getenv("APPDATA"), "Nuvix_Reset_Log.txt")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} - {mensagem}\n")

# Interface
janela = tk.Tk()
janela.title("Nuvix Computadores - Reset Seguro AnyDesk")
janela.geometry("420x220")
janela.resizable(False, False)

titulo = tk.Label(janela, text="NUVIX COMPUTADORES", font=("Arial", 16, "bold"))
titulo.pack(pady=10)

subtitulo = tk.Label(janela, text="Ferramenta Profissional de Reset AnyDesk", font=("Arial", 10))
subtitulo.pack()

descricao = tk.Label(janela, text="Esta ferramenta encerra o AnyDesk\n e remove a pasta de configuração do usuário.", justify="center")
descricao.pack(pady=15)

botao = tk.Button(janela, text="Executar Reset Seguro", font=("Arial", 11, "bold"), width=25, height=2, command=reset_anydesk)
botao.pack(pady=10)

rodape = tk.Label(janela, text="© Nuvix Computadores", font=("Arial", 8))
rodape.pack(side="bottom", pady=5)

janela.mainloop()
