import tkinter as tk
from datetime import datetime, timedelta

def calculate():
    try:
        mins = int(entry.get())
        base = datetime.strptime("00:00:00", "%H:%M:%S") + timedelta(minutes=mins)

        t1 = (base - timedelta(seconds=90)).strftime("%H:%M:%S")
        t2 = (base - timedelta(seconds=60)).strftime("%H:%M:%S")
        t3 = (base - timedelta(seconds=30)).strftime("%H:%M:%S")

        l1.config(text=t1)
        l2.config(text=f"{t2}  prepare trade")
        l3.config(text=f"{t3}  go trade")
    except:
        l1.config(text="Invalid")
        l2.config(text="")
        l3.config(text="")

def zoom(val):
    size = int(val)
    for w in widgets:
        w.config(font=("Arial", size))

root = tk.Tk()
root.title("Trade Timer")
root.geometry("360x260")

tk.Label(root, text="Enter Minutes").pack(pady=5)

entry = tk.Entry(root, justify="center")
entry.pack()

tk.Button(root, text="Calculate", command=calculate).pack(pady=5)

l1 = tk.Label(root)
l1.pack()
l2 = tk.Label(root)
l2.pack()
l3 = tk.Label(root)
l3.pack()

tk.Scale(root, from_=10, to=24, orient="horizontal", command=zoom).pack(fill="x", padx=10)

widgets = [entry, l1, l2, l3]

root.mainloop()
