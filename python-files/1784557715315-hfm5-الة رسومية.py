import tkinter as tk

# ----------------------------
# إعداد النافذة
# ----------------------------
root = tk.Tk()
root.title("Calculator")
root.geometry("360x560")
root.configure(bg="#1E1E1E")
root.resizable(False , False)

expression = ""

# ----------------------------
# شاشة العرض
# ----------------------------
display = tk.Entry(
    root,
    font=("Arial",28),
    bd=0,
    bg="#2B2B2B",
    fg="pink",
    justify="right"
)
display.pack(fill="both", padx=15, pady=20, ipady=20)

# ----------------------------
# الدوال
# ----------------------------
def press(value):
    global expression
    expression += str(value)
    display.delete(0, tk.END)
    display.insert(tk.END, expression)

def clear():
    global expression
    expression = ""
    display.delete(0, tk.END)

def backspace():
    global expression
    expression = expression[:-1]
    display.delete(0, tk.END)
    display.insert(tk.END, expression)

def calculate():
    global expression
    try:
        result = str(eval(expression))
        display.delete(0, tk.END)
        display.insert(tk.END, result)
        expression = result
    except:
        display.delete(0, tk.END)
        display.insert(tk.END, "Error")
        expression = ""

# ----------------------------
# إنشاء زر
# ----------------------------
def make_button(parent, text, command, bg, fg="white"):
    return tk.Button(
        parent,
        text=text,
        command=command,
        font=("Arial", 18, "bold"),
        bg=bg,
        fg=fg,
        relief="flat",
        activebackground="#555",
        activeforeground="white",
        width=5,
        height=2
    )

buttons = [
    ["C", "⌫", "%", "/"],
    ["7", "8", "9", "*"],
    ["4", "5", "6", "-"],
    ["1", "2", "3", "+"],
    ["0", ".", "="]
]

frame = tk.Frame(root, bg="#1E1E1E")
frame.pack(expand=True, fill="both", padx=10, pady=10)

for row in buttons:
    row_frame = tk.Frame(frame, bg="#1E1E1E")
    row_frame.pack(expand=True, fill="both")

    for btn in row:

        if btn == "C":
            button = make_button(row_frame, btn, clear, "#D32F2F")

        elif btn == "⌫":
            button = make_button(row_frame, btn, backspace, "#616161")

        elif btn == "=":
            button = make_button(row_frame, btn, calculate, "#FF9800")

        else:
            color = "#3A3A3A"
            if btn in ["+", "-", "*", "/", "%"]:
                color = "#1976D2"

            button = make_button(
                row_frame,
                btn,
                lambda x=btn: press(x),
                color
            )

        button.pack(side="left", expand=True, fill="both", padx=4, pady=4)

root.mainloop()