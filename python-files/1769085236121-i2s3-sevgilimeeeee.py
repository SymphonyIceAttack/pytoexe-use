import tkinter as tk

def hayir_basildi():
    global evet_boyut
    evet_boyut += 5
    evet_buton.config(font=("Arial", evet_boyut))

def evet_basildi():
    soru_label.config(text="💖 Ben de seni çok seviyorum 💖")
    hayir_buton.pack_forget()
    evet_buton.pack_forget()

pencere = tk.Tk()
pencere.title("Sana Bir Sorum Var ❤️")
pencere.geometry("400x300")

soru_label = tk.Label(pencere, text="Beni seviyor musun? 😳", font=("Arial", 16))
soru_label.pack(pady=20)

evet_boyut = 12

evet_buton = tk.Button(pencere, text="Evet 💕", font=("Arial", evet_boyut), command=evet_basildi)
evet_buton.pack(side="left", padx=40, pady=40)

hayir_buton = tk.Button(pencere, text="Hayır 🙄", font=("Arial", 12), command=hayir_basildi)
hayir_buton.pack(side="right", padx=40, pady=40)

pencere.mainloop()