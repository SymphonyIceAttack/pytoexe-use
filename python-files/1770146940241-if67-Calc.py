import tkinter as tk

root = tk.Tk()
root.title("Python Calculator")
root.geometry("350x420")
root.resizable(True, True)

expression = ""

def press(value):
    global expression
    expression += str(value)
    equation.set(expression)

def clear():
    global expression
    expression = ""
    equation.set("0")

def backspace():
    global expression
    expression = expression[:-1]
    equation.set(expression if expression else "0")

def equal():
    global expression
    try:
        result = str(eval(expression))
        equation.set(result)
        expression = result
    except:
        equation.set("Error")
        expression = ""

# display
equation = tk.StringVar(value="0")

display = tk.Entry(
    root,
    textvariable=equation,
    font=("Arial", 20),
    justify="right"
)
display.pack(fill="both", ipadx=8, ipady=15, padx=10, pady=10)

frame = tk.Frame(root)
frame.pack()

# 🔴 C button
tk.Button(
    frame, text="C",
    bg="red", fg="white",
    font=("Arial", 12, "bold"),
    width=5, height=2,
    command=clear
).grid(row=0, column=0, padx=5, pady=5)

# ⌫ Backspace
tk.Button(
    frame, text="⌫",
    bg="#FFB74D",
    font=("Arial", 12, "bold"),
    width=5, height=2,
    command=backspace
).grid(row=0, column=1, padx=5, pady=5)

# normal buttons
normal_buttons = [
    ("7", 1, 0), ("8", 1, 1), ("9", 1, 2),
    ("4", 2, 0), ("5", 2, 1), ("6", 2, 2),
    ("1", 3, 0), ("2", 3, 1), ("3", 3, 2),
    ("0", 4, 0), ("00", 4, 1)
]

# operator buttons (highlighted)
operator_buttons = [
    ("/", 1, 3),
    ("*", 2, 3),
    ("-", 3, 3),
    ("+", 4, 3),
    ("=", 4, 2)
]

for (text, row, col) in normal_buttons:
    tk.Button(
        frame, text=text,
        width=5, height=2,
        font=("Arial", 12),
        command=lambda t=text: press(t)
    ).grid(row=row, column=col, padx=5, pady=5)

for (text, row, col) in operator_buttons:
    if text == "=":
        tk.Button(
            frame, text=text,
            bg="#4CAF50", fg="white",
            font=("Arial", 14, "bold"),
            width=5, height=2,
            command=equal
        ).grid(row=row, column=col, padx=5, pady=5)
    else:
        tk.Button(
            frame, text=text,
            bg="#2196F3", fg="white",
            font=("Arial", 14, "bold"),
            width=5, height=2,
            command=lambda t=text: press(t)
        ).grid(row=row, column=col, padx=5, pady=5)

root.mainloop()
