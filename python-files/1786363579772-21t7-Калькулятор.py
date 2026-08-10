import tkinter as tk

window = tk.Tk()
window.title("Калькулятор")
window.geometry("250x200")
window.resizable(False, False)
calkulator = ""

#Строки для вывода
label = tk.Label(
    window,
    text="",
    font=("Arial", 18),
    bg="white",
    anchor="e"
)
label.pack(expand=True, fill='both', padx=5, pady=5)

#Исполнение кнопок
def button1_click():
    global calkulator
    calkulator += "1"
    label.config(text=calkulator)

def button2_click():
    global calkulator
    calkulator += "2"
    label.config(text=calkulator)

def button3_click():
    global calkulator
    calkulator += "3"
    label.config(text=calkulator)

def button4_click():
    global calkulator
    calkulator += "4"
    label.config(text=calkulator)

def button5_click():
    global calkulator
    calkulator += "5"
    label.config(text=calkulator)

def button6_click():
    global calkulator
    calkulator += "6"
    label.config(text=calkulator)

def button7_click():
    global calkulator
    calkulator += "7"
    label.config(text=calkulator)

def button8_click():
    global calkulator
    calkulator += "8"
    label.config(text=calkulator)

def button9_click():
    global calkulator
    calkulator += "9"
    label.config(text=calkulator)

def button0_click():
    global calkulator
    calkulator += "0"
    label.config(text=calkulator)

def buttonDot_click():
    global calkulator
    calkulator += "."
    label.config(text=calkulator)

def buttonPlus_click():
    global calkulator
    calkulator += "+"
    label.config(text=calkulator)

def buttonSub_click():
    global calkulator
    calkulator += "-"
    label.config(text=calkulator)

def buttonMul_click():
    global calkulator
    calkulator += "*"
    label.config(text=calkulator)

def buttonDiv_click():
    global calkulator
    calkulator += "/"
    label.config(text=calkulator)

def buttonC_click():
    global calkulator
    calkulator = ""
    label.config(text=calkulator)

def buttonBackspace_click():
    global calkulator
    calkulator = calkulator[:-1]
    label.config(text=calkulator)

def buttonEq_click():
    global calkulator
    try:
        calkulator = str(eval(calkulator))
        label.config(text=calkulator)
    except:
        label.config(text="Ошибка")

# Прижимание кнопок к низу
button_frame = tk.Frame(window)
button_frame.pack(side='bottom', fill='x')

# Кнопки
btnC   = tk.Button(button_frame, text="C", width=5, command=buttonC_click, bg="DodgerBlue")
btnDiv = tk.Button(button_frame, text="/", width=5, command=buttonDiv_click, bg="SkyBlue")
btnMul = tk.Button(button_frame, text="*", width=5, command=buttonMul_click, bg="SkyBlue")
btnEq  = tk.Button(button_frame, text="=", width=5, command=buttonEq_click, bg="SkyBlue")

btn7   = tk.Button(button_frame, text="7", width=5, command=button7_click)
btn8   = tk.Button(button_frame, text="8", width=5, command=button8_click)
btn9   = tk.Button(button_frame, text="9", width=5, command=button9_click)
btnPlus = tk.Button(button_frame, text="+", width=5, command=buttonPlus_click, bg="SkyBlue")

btn4   = tk.Button(button_frame, text="4", width=5, command=button4_click)
btn5   = tk.Button(button_frame, text="5", width=5, command=button5_click)
btn6   = tk.Button(button_frame, text="6", width=5, command=button6_click)
btnSub = tk.Button(button_frame, text="-", width=5, command=buttonSub_click, bg="SkyBlue")

btn1   = tk.Button(button_frame, text="1", width=5, command=button1_click)
btn2   = tk.Button(button_frame, text="2", width=5, command=button2_click)
btn3   = tk.Button(button_frame, text="3", width=5, command=button3_click)
btnBackspace = tk.Button(button_frame, text="⌫", width=5, command=buttonBackspace_click, bg="DodgerBlue")

btn0   = tk.Button(button_frame, text="0", width=5, command=button0_click)
btnDot = tk.Button(button_frame, text=".", width=5, command=buttonDot_click)

# Вывод кнопок
btnC.grid(row=0, column=0, padx=2, pady=0, sticky="ew")
btnDiv.grid(row=0, column=1, padx=2, pady=0, sticky="ew")
btnMul.grid(row=0, column=2, padx=2, pady=0, sticky="ew")
btnEq.grid(row=0, column=3, padx=2, pady=0, sticky="ew")

btn7.grid(row=1, column=0, padx=2, pady=0, sticky="ew")
btn8.grid(row=1, column=1, padx=2, pady=0, sticky="ew")
btn9.grid(row=1, column=2, padx=2, pady=0, sticky="ew")
btnPlus.grid(row=1, column=3, padx=2, pady=0, sticky="ew")

btn4.grid(row=2, column=0, padx=2, pady=0, sticky="ew")
btn5.grid(row=2, column=1, padx=2, pady=0, sticky="ew")
btn6.grid(row=2, column=2, padx=2, pady=0, sticky="ew")
btnSub.grid(row=2, column=3, padx=2, pady=0, sticky="ew")

btn1.grid(row=3, column=0, padx=2, pady=0, sticky="ew")
btn2.grid(row=3, column=1, padx=2, pady=0, sticky="ew")
btn3.grid(row=3, column=2, padx=2, pady=0, sticky="ew")
btnBackspace.grid(row=3, column=3, padx=2, pady=0, sticky="ew")  # Backspace здесь

btn0.grid(row=4, column=0, padx=2, pady=0, sticky="ew")
btnDot.grid(row=4, column=1, padx=2, pady=0, sticky="ew")

# Настройка столбцов
for col in range(4):
    button_frame.grid_columnconfigure(col, weight=1)

window.mainloop()