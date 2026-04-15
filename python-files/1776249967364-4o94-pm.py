import tkinter as tk
import math

def hisobla():
    nums = entry.get().split()
    result = []
    
    for num in nums:
        x = int(num)
        kv = x**2
        ildiz = int(math.sqrt(kv))
        
        if ildiz * ildiz == kv:
            result.append(x)
    
    label.config(text=f"Natija: {result}")

root = tk.Tk()
root.title("33-masala")

entry = tk.Entry(root, width=30)
entry.pack()

btn = tk.Button(root, text="Hisobla", command=hisobla)
btn.pack()

label = tk.Label(root, text="")
label.pack()

root.mainloop()