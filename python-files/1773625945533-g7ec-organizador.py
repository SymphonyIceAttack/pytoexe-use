import os
import shutil
import tkinter as tk
from tkinter import filedialog

fotos = [".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"]
videos = [".mp4", ".mkv", ".avi", ".mov", ".webm"]
documentos = [".pdf", ".txt", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"]
audio = [".mp3", ".wav", ".flac", ".ogg"]
compactados = [".zip", ".rar", ".7z", ".tar"]
programas = [".exe", ".msi", ".apk"]

pasta_escolhida = ""

def escolher_pasta():
    global pasta_escolhida
    pasta_escolhida = filedialog.askdirectory()
    label_pasta.config(text=pasta_escolhida)

def organizar():

    if pasta_escolhida == "":
        status.config(text="Escolha uma pasta primeiro")
        return

    status.config(text="Organizando arquivos...")
    janela.update()

    arquivos = os.listdir(pasta_escolhida)

    movidos = 0

    for arq in arquivos:

        caminho = os.path.join(pasta_escolhida, arq)

        if not os.path.isfile(caminho):
            continue

        nome, extensao = os.path.splitext(arq)
        extensao = extensao.lower()

        destino = "Outros"

        if extensao in fotos:
            destino = "Imagens"

        elif extensao in videos:
            destino = "Videos"

        elif extensao in documentos:
            destino = "Documentos"

        elif extensao in audio:
            destino = "Audio"

        elif extensao in compactados:
            destino = "Compactados"

        elif extensao in programas:
            destino = "Programas"

        pasta_destino = os.path.join(pasta_escolhida, destino)

        os.makedirs(pasta_destino, exist_ok=True)

        novo_caminho = os.path.join(pasta_destino, arq)

        shutil.move(caminho, novo_caminho)

        movidos += 1

    status.config(text=f"Organização concluída! {movidos} arquivos movidos")

janela = tk.Tk()
janela.title("Organizador de Arquivos")
janela.geometry("420x250")

botao = tk.Button(janela, text="Selecionar Pasta", command=escolher_pasta)
botao.pack(pady=10)

label_pasta = tk.Label(janela, text="Nenhuma pasta selecionada")
label_pasta.pack()

botao2 = tk.Button(janela, text="Organizar Arquivos", command=organizar)
botao2.pack(pady=15)

status = tk.Label(janela, text="Status: aguardando ação")
status.pack()

janela.mainloop()