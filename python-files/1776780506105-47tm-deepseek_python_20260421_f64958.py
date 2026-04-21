import tkinter as tk
import random
import time

def efecto_bug_visual():
    # Pantalla completa negra
    root = tk.Tk()
    root.attributes('-fullscreen', True)
    root.attributes('-topmost', True)
    root.configure(bg='black')
    root.overrideredirect(True)  # Sin bordes

    # Crear muchas etiquetas con caracteres aleatorios
    labels = []
    for _ in range(50):
        texto = "".join(random.choice(["█", "▒", "░", "▓", "0", "1", "@", "#"]) for _ in range(random.randint(3, 12)))
        lbl = tk.Label(root, text=texto, font=("Courier", random.randint(10, 30)),
                       fg=random.choice(["lime", "red", "cyan", "white", "yellow", "magenta"]),
                       bg="black")
        x = random.randint(0, root.winfo_screenwidth())
        y = random.randint(0, root.winfo_screenheight())
        lbl.place(x=x, y=y)
        labels.append(lbl)

    # Animación caótica durante 6 segundos
    start = time.time()
    while time.time() - start < 6:
        for lbl in labels:
            lbl.place(x=random.randint(0, root.winfo_screenwidth()),
                      y=random.randint(0, root.winfo_screenheight()))
            lbl.config(fg=random.choice(["lime", "red", "cyan", "white", "yellow", "magenta"]))
        root.update()
        time.sleep(0.04)

    # Cerrar y volver a la normalidad
    root.destroy()

if __name__ == "__main__":
    efecto_bug_visual()