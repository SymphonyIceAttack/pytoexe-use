import tkinter as tk

# Window setup
root = tk.Tk()
root.title("Blue Purple Calculator")
root.geometry("330x430")
root.configure(bg="#000000")

expression = ""

# Functions
def press(value):
    global expression
    expression += str(value)
    equation.set(expression)

def calculate():
    global expression
    try:
        result = str(eval(expression))
        equation.set(result)
        expression = result
    except:
        equation.set("Error")
        expression = ""

def clear():
    global expression
    expression = ""
    equation.set("")

def backspace():
    global expression
    expression = expression[:-1]
    equation.set(expression)

# Display
equation = tk.StringVar()

display = tk.Entry(
    root,
    textvariable=equation,
    font=("Arial", 22),
    bg="#111111",
    fg="#4da6ff",
    bd=0,
    justify="right"
)

display.pack(fill="both", padx=10, pady=15, ipady=15)

# Button frame
frame = tk.Frame(root, bg="#000000")
frame.pack()

# Button style
btn_style = {
    "font": ("Arial", 14),
    "width": 5,
    "height": 2,
    "bd": 0
}

buttons = [
('7',1,0), ('8',1,1), ('9',1,2), ('/',1,3),
('4',2,0), ('5',2,1), ('6',2,2), ('*',2,3),
('1',3,0), ('2',3,1), ('3',3,2), ('-',3,3),
('0',4,0), ('.',4,1), ('=',4,2), ('+',4,3),
]

for (text,row,col) in buttons:

    if text == "=":
        action = calculate
        color = "#7a3cff"

    elif text.isdigit() or text == ".":
        action = lambda x=text: press(x)
        color = "#1e90ff"

    else:
        action = lambda x=text: press(x)
        color = "#7a3cff"

    tk.Button(
        frame,
        text=text,
        command=action,
        bg=color,
        fg="white",
        activebackground="#4b0082",
        **btn_style
    ).grid(row=row, column=col, padx=6, pady=6)

# Bottom buttons
bottom = tk.Frame(root, bg="#000000")
bottom.pack(fill="x", padx=10, pady=10)

tk.Button(
    bottom,
    text="Clear",
    command=clear,
    bg="#4b0082",
    fg="white",
    font=("Arial",13),
    bd=0
).pack(side="left", expand=True, fill="x", padx=5)

tk.Button(
    bottom,
    text="⌫",
    command=backspace,
    bg="#1e90ff",
    fg="white",
    font=("Arial",13),
    bd=0
).pack(side="left", expand=True, fill="x", padx=5)

root.mainloop()