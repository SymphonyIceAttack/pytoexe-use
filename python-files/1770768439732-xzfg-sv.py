import tkinter as tk

# Crear ventana principal
root = tk.Tk()
root.title("San Valentín 💘")
root.geometry("500x300")
root.resizable(False, False)

# Tamaños iniciales
size_no = 14
size_yes = 14

def click_no():
    global size_no, size_yes

    if size_no > 1:
        size_no -= 2
        size_yes += 2

        btn_no.config(font=("Arial", size_no))
        btn_yes.config(font=("Arial", size_yes))

        if size_no <= 2:
            btn_no.pack_forget()

def click_yes():
    for widget in root.winfo_children():
        widget.destroy()

    canvas = tk.Canvas(root, width=500, height=300, bg="white")
    canvas.pack()

    canvas.create_text(
        250, 80,
        text="TE AMOO MI AMOOR",
        fill="red",
        font=("Arial", 36, "bold")
    )

    # Corazón izquierdo
    canvas.create_oval(150, 120, 200, 170, fill="red", outline="red")
    canvas.create_oval(180, 120, 230, 170, fill="red", outline="red")
    canvas.create_polygon(150, 150, 230, 150, 190, 220, fill="red")

    # Corazón derecho
    canvas.create_oval(270, 120, 320, 170, fill="red", outline="red")
    canvas.create_oval(300, 120, 350, 170, fill="red", outline="red")
    canvas.create_polygon(270, 150, 350, 150, 310, 220, fill="red")

# Texto de la pregunta
label = tk.Label(
    root,
    text="Noa Bande, quieres ser mi Valentín? 💘",
    font=("Arial", 18)
)
label.pack(pady=30)

# Botones
frame = tk.Frame(root)
frame.pack()

btn_no = tk.Button(
    frame,
    text="NO",
    font=("Arial", size_no),
    command=click_no
)
btn_no.pack(side="left", padx=20)

btn_yes = tk.Button(
    frame,
    text="SÍ",
    font=("Arial", size_yes),
    command=click_yes
)
btn_yes.pack(side="right", padx=20)

root.mainloop()
