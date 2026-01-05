import socket
import tkinter as tk
from tkinter import simpledialog

def mesaj_bekle():
    # Kendi IP adresini buraya yazmalısın
    host = '0.0.0.0' 
    port = 12345
    
    s = socket.socket()
    s.bind((host, port))
    s.listen(1)
    
    conn, addr = s.accept()
    while True:
        data = conn.recv(1024).decode()
        if not data: break
        
        # Ekranında soru kutusu açar
        root = tk.Tk()
        root.withdraw()
        cevap = simpledialog.askstring("Sistem Mesajı", data)
        root.destroy()
        
        # Cevabı sana geri gönderir
        conn.send(cevap.encode())

mesaj_bekle()
