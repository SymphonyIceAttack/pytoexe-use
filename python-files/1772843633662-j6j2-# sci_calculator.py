# sci_calculator.py
# Simple scientific calculator using Tkinter and a safe eval environment.

import tkinter as tk
import math
import re

# Allowed names for eval
SAFE_NAMES = {k: getattr(math, k) for k in (
    "sin cos tan asin acos atan sinh cosh tanh log log10 sqrt exp pow factorial pi e floor ceil degrees radians"
).split()}
SAFE_NAMES.update({
    "abs": abs,
    "round": round,
    "ln": math.log,  # ln(x) -> natural log
})

# Basic sanitization: allow digits, letters, operators, parentheses, dot, comma, whitespace
SAFE_RE = re.compile(r'^[0-9A-Za-z\s\.\+\-\*\/\^\(\)\,\%]*$')

class SciCalculator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Scientific Calculator")
        self.resizable(False, False)
        self._build_ui()

    def _build_ui(self):
        self.display = tk.Entry(self, font=("Consolas", 18), bd=4, relief="sunken", justify="right")
        self.display.grid(row=0, column=0, columnspan=6, sticky="nsew", padx=5, pady=5)
        btns = [
            ('7',1,0),('8',1,1),('9',1,2),('/',1,3),('sqrt',1,4),('pi',1,5),
            ('4',2,0),('5',2,1),('6',2,2),('*',2,3),('^',2,4),('e',2,5),
            ('1',3,0),('2',3,1),('3',3,2),('-',3,3),('(',3,4),(')',3,5),
            ('0',4,0),('.',4,1),('%',4,2),('+',4,3),('=',4,4),('C',4,5),
            ('sin',5,0),('cos',5,1),('tan',5,2),('log',5,3),('ln',5,4),('DEL',5,5),
            ('asin',6,0),('acos',6,1),('atan',6,2),('exp',6,3),('fact',6,4),('abs',6,5),
        ]
        for (text,r,c) in btns:
            cmd = (lambda t=text: self._on_button(t))
            b = tk.Button(self, text=text, width=6, height=2, command=cmd)
            b.grid(row=r, column=c, padx=2, pady=2)

        # keyboard bindings
        self.bind("<Return>", lambda e: self._evaluate())
        self.bind("<BackSpace>", lambda e: self._on_button("DEL"))
        self.bind("<Escape>", lambda e: self._on_button("C"))

    def _on_button(self, label):
        if label == "C":
            self.display.delete(0, tk.END)
        elif label == "DEL":
            s = self.display.get()
            self.display.delete(0, tk.END)
            self.display.insert(0, s[:-1])
        elif label == "=":
            self._evaluate()
        elif label == "sqrt":
            self._insert("sqrt(")
        elif label == "fact":
            self._insert("factorial(")
        else:
            self._insert(label)

    def _insert(self, txt):
        pos = self.display.index(tk.INSERT)
        self.display.insert(pos, txt)

    def _evaluate(self):
        expr = self.display.get().strip()
        if not expr:
            return
        # normalize common symbols
        expr = expr.replace('^', '**').replace('×', '*').replace('÷', '/')
        # replace percent: treat as /100
        expr = re.sub(r'(\d+(\.\d+)?)\s*%', r'(\1/100)', expr)
        # simple sanitization
        if not SAFE_RE.match(expr):
            self._show_error("Invalid characters")
            return
        try:
            # eval with restricted globals and allowed math names
            result = eval(expr, {"__builtins__": None}, SAFE_NAMES)
            self.display.delete(0, tk.END)
            self.display.insert(0, str(result))
        except Exception as e:
            self._show_error("Error")

    def _show_error(self, msg):
        self.display.delete(0, tk.END)
        self.display.insert(0, msg)

if __name__ == "__main__":
    app = SciCalculator()
    app.mainloop()