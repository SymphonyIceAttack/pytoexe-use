import socket
import threading
import json
import uuid
import time
import struct
import wave
import os
import tkinter as tk
from tkinter import scrolledtext, messagebox


# ============================================================
# CONFIGURAÇÃO
# ============================================================

DISCOVERY_PORT = 50000
MESSAGE_PORT = 50001

BUFFER_SIZE = 65536

MY_ID = str(uuid.uuid4())
MY_NAME = socket.gethostname()

running = True

# Computadores encontrados APENAS enquanto estiverem online
computers = {}

# Mensagens já recebidas
received_signals = set()


# ============================================================
# INTERFACE
# ============================================================

root = tk.Tk()
root.title("LUNA - Rede Local")
root.geometry("850x650")

titulo = tk.Label(
    root,
    text="LUNA • COMUNICAÇÃO LOCAL",
    font=("Arial", 18, "bold")
)
titulo.pack(pady=10)

status = tk.Label(
    root,
    text="Procurando computadores...",
    font=("Arial", 10)
)
status.pack()

lista = tk.Listbox(
    root,
    height=5,
    font=("Arial", 10)
)
lista.pack(fill="x", padx=15, pady=8)

chat = scrolledtext.ScrolledText(
    root,
    width=100,
    height=25,
    font=("Consolas", 10),
    state="disabled"
)
chat.pack(padx=15, pady=10)

frame = tk.Frame(root)
frame.pack(fill="x", padx=15)

entrada = tk.Entry(
    frame,
    font=("Arial", 12)
)
entrada.pack(
    side="left",
    fill="x",
    expand=True
)


# ============================================================
# MOSTRAR NO CHAT
# ============================================================

def mostrar(texto):

    def atualizar():

        chat.config(state="normal")

        chat.insert(
            tk.END,
            texto + "\n"
        )

        chat.see(tk.END)

        chat.config(state="disabled")

    root.after(
        0,
        atualizar
    )


# ============================================================
# ATUALIZAR LISTA
# ============================================================

def atualizar_lista():

    def atualizar():

        lista.delete(
            0,
            tk.END
        )

        for cid, computador in computers.items():

            lista.insert(
                tk.END,
                f"{computador['name']}  |  "
                f"{computador['ip']}  |  "
                f"ID: {cid[:8]}"
            )

        status.config(
            text=f"{len(computers)} computador(es) encontrado(s)"
        )

    root.after(
        0,
        atualizar
    )


# ============================================================
# DESCOBERTA
# ============================================================

def receber_descoberta():

    sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM
    )

    sock.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1
    )

    try:
        sock.bind(
            ("", DISCOVERY_PORT)
        )
    except Exception as erro:

        mostrar(
            f"[ERRO DISCOVERY] {erro}"
        )

        return

    while running:

        try:

            dados, endereco = sock.recvfrom(
                65535
            )

            mensagem = json.loads(
                dados.decode()
            )

            if mensagem.get("type") != "LUNA_DISCOVERY":
                continue

            computador_id = mensagem.get(
                "id"
            )

            if computador_id == MY_ID:
                continue

            computers[computador_id] = {
                "name": mensagem.get(
                    "name",
                    "Computador"
                ),
                "ip": endereco[0],
                "last_seen": time.time()
            }

            atualizar_lista()

        except Exception:
            pass


# ============================================================
# ENVIAR DESCOBERTA
# ============================================================

def enviar_descoberta():

    sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM
    )

    sock.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_BROADCAST,
        1
    )

    mensagem = {
        "type": "LUNA_DISCOVERY",
        "id": MY_ID,
        "name": MY_NAME
    }

    dados = json.dumps(
        mensagem
    ).encode()

    while running:

        try:

            sock.sendto(
                dados,
                (
                    "<broadcast>",
                    DISCOVERY_PORT
                )
            )

        except Exception:
            pass

        time.sleep(2)


# ============================================================
# ENVIO DE PACOTE
# ============================================================

def enviar_pacote(ip, cabecalho, dados):

    try:

        cliente = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        cliente.settimeout(10)

        cliente.connect(
            (
                ip,
                MESSAGE_PORT
            )
        )

        cabecalho_json = json.dumps(
            cabecalho
        ).encode("utf-8")

        # Primeiro envia tamanho do cabeçalho
        cliente.sendall(
            struct.pack(
                "!I",
                len(cabecalho_json)
            )
        )

        # Depois envia cabeçalho
        cliente.sendall(
            cabecalho_json
        )

        # Depois envia os dados
        if dados:
            cliente.sendall(
                dados
            )

        cliente.close()

        return True

    except Exception as erro:

        mostrar(
            f"[ERRO ENVIO] {erro}"
        )

        return False


# ============================================================
# ENVIAR TEXTO
# ============================================================

def enviar_texto():

    texto = entrada.get().strip()

    if not texto:
        return

    if not computers:

        messagebox.showwarning(
            "Luna",
            "Nenhum computador foi encontrado."
        )

        return

    selecionado = lista.curselection()

    if not selecionado:

        messagebox.showwarning(
            "Luna",
            "Selecione um computador para enviar."
        )

        return

    nomes = list(computers.keys())

    computador_id = nomes[
        selecionado[0]
    ]

    computador = computers[
        computador_id
    ]

    sinal = str(
        uuid.uuid4()
    )

    cabecalho = {

        "protocol": "LUNA",

        "type": "TEXT",

        "signal": sinal,

        "sender_id": MY_ID,

        "sender_name": MY_NAME,

        "receiver_id": computador_id,

        "timestamp": time.time(),

        "length": len(
            texto.encode("utf-8")
        )
    }

    dados = texto.encode(
        "utf-8"
    )

    sucesso = enviar_pacote(
        computador["ip"],
        cabecalho,
        dados
    )

    if sucesso:

        mostrar(
            f"Você → {computador['name']}: "
            f"{texto}"
        )

        entrada.delete(
            0,
            tk.END
        )


# ============================================================
# RECEBER EXATAMENTE N BYTES
# ============================================================

def receber_bytes(cliente, quantidade):

    dados = b""

    while len(dados) < quantidade:

        parte = cliente.recv(
            min(
                BUFFER_SIZE,
                quantidade - len(dados)
            )
        )

        if not parte:
            break

        dados += parte

    return dados


# ============================================================
# SERVIDOR
# ============================================================

def servidor():

    server = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    server.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1
    )

    try:

        server.bind(
            ("", MESSAGE_PORT)
        )

        server.listen(20)

    except Exception as erro:

        mostrar(
            f"[ERRO SERVIDOR] {erro}"
        )

        return

    mostrar(
        f"[LUNA] Servidor iniciado. ID: {MY_ID}"
    )

    while running:

        try:

            cliente, endereco = server.accept()

            threading.Thread(
                target=processar_conexao,
                args=(cliente,),
                daemon=True
            ).start()

        except Exception:
            pass


# ============================================================
# PROCESSAR MENSAGEM RECEBIDA
# ============================================================

def processar_conexao(cliente):

    try:

        # Tamanho do cabeçalho
        tamanho_bytes = receber_bytes(
            cliente,
            4
        )

        if len(tamanho_bytes) != 4:
            cliente.close()
            return

        tamanho = struct.unpack(
            "!I",
            tamanho_bytes
        )[0]

        cabecalho_bytes = receber_bytes(
            cliente,
            tamanho
        )

        cabecalho = json.loads(
            cabecalho_bytes.decode(
                "utf-8"
            )
        )

        tipo = cabecalho.get(
            "type"
        )

        sinal = cabecalho.get(
            "signal"
        )

        # Evita processar o mesmo sinal duas vezes
        if sinal in received_signals:

            cliente.close()
            return

        received_signals.add(
            sinal
        )

        tamanho_dados = cabecalho.get(
            "length",
            0
        )

        dados = receber_bytes(
            cliente,
            tamanho_dados
        )

        nome = cabecalho.get(
            "sender_name",
            "Computador"
        )

        # ----------------------------------------------------
        # TEXTO
        # ----------------------------------------------------

        if tipo == "TEXT":

            texto = dados.decode(
                "utf-8"
            )

            mostrar(
                f"{nome}: {texto}"
            )

        # ----------------------------------------------------
        # ÁUDIO
        # ----------------------------------------------------

        elif tipo == "AUDIO":

            nome_arquivo = (
                f"audio_{sinal}.wav"
            )

            caminho = os.path.join(
                os.getcwd(),
                nome_arquivo
            )

            with open(
                caminho,
                "wb"
            ) as arquivo:

                arquivo.write(
                    dados
                )

            mostrar(
                f"{nome}: 🎤 ÁUDIO RECEBIDO"
            )

            mostrar(
                f"Arquivo: {nome_arquivo}"
            )

            # Reproduzir automaticamente
            try:

                import winsound

                winsound.PlaySound(
                    caminho,
                    winsound.SND_FILENAME
                )

            except Exception:

                mostrar(
                    "Áudio salvo para reprodução."
                )

        # ----------------------------------------------------
        # OUTRO TIPO
        # ----------------------------------------------------

        else:

            mostrar(
                f"{nome}: "
                f"Sinal recebido: {tipo}"
            )

    except Exception as erro:

        mostrar(
            f"[ERRO RECEBENDO] {erro}"
        )

    finally:

        cliente.close()


# ============================================================
# GRAVAR ÁUDIO
# ============================================================

def gravar_audio():

    try:

        import sounddevice as sd

    except ImportError:

        messagebox.showerror(
            "Luna",
            "Instale primeiro:\n\npip install sounddevice"
        )

        return

    if not computers:

        messagebox.showwarning(
            "Luna",
            "Nenhum computador encontrado."
        )

        return

    selecionado = lista.curselection()

    if not selecionado:

        messagebox.showwarning(
            "Luna",
            "Selecione o computador que receberá o áudio."
        )

        return

    nomes = list(computers.keys())

    computador_id = nomes[
        selecionado[0]
    ]

    computador = computers[
        computador_id
    ]

    # Janela pequena
    janela = tk.Toplevel(
        root
    )

    janela.title(
        "Gravar áudio"
    )

    janela.geometry(
        "300x180"
    )

    tk.Label(
        janela,
        text="Gravando por 5 segundos...",
        font=("Arial", 12)
    ).pack(
        pady=20
    )

    root.update()

    try:

        sample_rate = 44100

        canais = 1

        duracao = 5

        audio = sd.rec(
            int(
                duracao *
                sample_rate
            ),
            samplerate=sample_rate,
            channels=canais,
            dtype="int16"
        )

        sd.wait()

        sinal = str(
            uuid.uuid4()
        )

        arquivo_temporario = (
            f"temp_{sinal}.wav"
        )

        with wave.open(
            arquivo_temporario,
            "wb"
        ) as wav:

            wav.setnchannels(
                canais
            )

            wav.setsampwidth(
                2
            )

            wav.setframerate(
                sample_rate
            )

            wav.writeframes(
                audio.tobytes()
            )

        with open(
            arquivo_temporario,
            "rb"
        ) as arquivo:

            dados = arquivo.read()

        os.remove(
            arquivo_temporario
        )

        cabecalho = {

            "protocol": "LUNA",

            "type": "AUDIO",

            "signal": sinal,

            "sender_id": MY_ID,

            "sender_name": MY_NAME,

            "receiver_id": computador_id,

            "timestamp": time.time(),

            "length": len(dados)
        }

        sucesso = enviar_pacote(
            computador["ip"],
            cabecalho,
            dados
        )

        if sucesso:

            mostrar(
                f"Você → {computador['name']}: "
                f"🎤 Áudio enviado"
            )

    except Exception as erro:

        messagebox.showerror(
            "Erro no áudio",
            str(erro)
        )

    janela.destroy()


# ============================================================
# BOTÕES
# ============================================================

botao_texto = tk.Button(
    frame,
    text="ENVIAR TEXTO",
    command=enviar_texto
)

botao_texto.pack(
    side="right",
    padx=5
)

botao_audio = tk.Button(
    frame,
    text="🎤 ÁUDIO",
    command=gravar_audio
)

botao_audio.pack(
    side="right",
    padx=5
)

entrada.bind(
    "<Return>",
    lambda evento: enviar_texto()
)


# ============================================================
# LIMPAR COMPUTADORES OFFLINE
# ============================================================

def limpar_offline():

    agora = time.time()

    remover = []

    for cid, computador in list(
        computers.items()
    ):

        if agora - computador[
            "last_seen"
        ] > 8:

            remover.append(
                cid
            )

    for cid in remover:

        del computers[cid]

    atualizar_lista()

    root.after(
        3000,
        limpar_offline
    )


# ============================================================
# INICIAR
# ============================================================

mostrar(
    "======================================"
)

mostrar(
    "       LUNA LOCAL NETWORK"
)

mostrar(
    "======================================"
)

mostrar(
    f"Nome: {MY_NAME}"
)

mostrar(
    f"ID: {MY_ID}"
)

mostrar(
    "Procurando computadores na rede..."
)

threading.Thread(
    target=receber_descoberta,
    daemon=True
).start()

threading.Thread(
    target=enviar_descoberta,
    daemon=True
).start()

threading.Thread(
    target=servidor,
    daemon=True
).start()

root.after(
    3000,
    limpar_offline
)


# ============================================================
# FECHAR
# ============================================================

def fechar():

    global running

    running = False

    root.destroy()


root.protocol(
    "WM_DELETE_WINDOW",
    fechar
)

root.mainloop()
