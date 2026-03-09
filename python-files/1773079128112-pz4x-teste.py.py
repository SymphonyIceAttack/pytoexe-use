import keyboard
import time
import threading
import tkinter as tk

ativo = False
tecla = "e"

def loop_macro():
    global ativo
    while True:
        if ativo:
            keyboard.press_and_release(tecla)
            time.sleep(0.2)
        else:
            time.sleep(0.1)

def ligar():
    global ativo
    ativo = True
    status_label.config(text="Status: ON", fg="green")

def desligar():
    global ativo
    ativo = False
    status_label.config(text="Status: OFF", fg="red")

def definir_tecla():
    global tecla
    tecla = entry_tecla.get()
    tecla_label.config(text=f"Tecla selecionada: {tecla}")

# interface
janela = tk.Tk()
janela.title("Macro Hotkey")
janela.geometry("300x200")

entry_tecla = tk.Entry(janela)
entry_tecla.pack(pady=5)

btn_definir = tk.Button(janela, text="Definir tecla", command=definir_tecla)
btn_definir.pack()

tecla_label = tk.Label(janela, text="Tecla selecionada: e")
tecla_label.pack(pady=5)

btn_on = tk.Button(janela, text="ON", command=ligar, bg="green")
btn_on.pack(pady=5)

btn_off = tk.Button(janela, text="OFF", command=desligar, bg="red")
btn_off.pack(pady=5)

status_label = tk.Label(janela, text="Status: OFF", fg="red")
status_label.pack(pady=10)

threading.Thread(target=loop_macro, daemon=True).start()

janela.mainloop()