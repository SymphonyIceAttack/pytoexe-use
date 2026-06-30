import tkinter as tk
root = tk.Tk()
root.geometry("500x800")
root.resizable(False, False)
root.title("выбор жизни")

label = tk.Label(root, text="глеб фембой?", width=500, height=20, bg="light blue" )
label.pack()

def on_batton_click():
    label.config(text="ну бля это логично")

button = tk.Button(root, text="глеб фембой", command=on_batton_click)
button.pack(pady=10)

def on_batton_click():
    label.config(text="ты чё даун блять? а ну сьебалась чурка ебаная")

button = tk.Button(root, text="нет", command=on_batton_click)
button.pack(pady=10)

def on_batton_click():
    label.config(text="коч коч братан туру туру ту")

button = tk.Button(root, text="хамам", command=on_batton_click)
button.pack(pady=10)

def on_batton_click():
    label.config(text="ты чё еблан?")

button = tk.Button(root, text="гаджет с легендарного стардропа", command=on_batton_click)
button.pack(pady=10)

def on_batton_click():
    label.config(text="вермишель")

button = tk.Button(root, text="какая нахуй микровалновка", command=on_batton_click)
button.pack(pady=10)

def on_batton_click():
    label.config(text="сикс с дедом из немецкого бункера справа от тешки")

button = tk.Button(root, text="67?", command=on_batton_click)
button.pack(pady=10)

def on_batton_click():
    label.config(text="дилдо динозавра")

button = tk.Button(root, text="что заказал степан на озоне?", command=on_batton_click)
button.pack(pady=10)

def on_batton_click():
    label.config(text="мама твоя")

button = tk.Button(root, text="создатель этой хуйни", command=on_batton_click)
button.pack(pady=10)

def on_batton_click():
    label.config(text="глеб весит: 1,5 × 10⁵³ кг а это в свою очередь 100000000000000000000000000000 тон")

button = tk.Button(root, text="сколько весит глеб", command=on_batton_click)
button.pack(pady=10)

def on_batton_click():
    label.config(text="а вы знали что титаник весил 3 309 142 857 тапочек")

button = tk.Button(root, text="интерестный факт", command=on_batton_click)
button.pack(pady=10)

label.pack()
root.mainloop()