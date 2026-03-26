import tkinter as tk

class Calculator:
    def __init__(self, root):
        self.root = root
        self.root.title("blue Calculator")
        self.root.geometry("330x430")

        self.display = tk.Entry(root, font=("Arial", 20), justify="right")
        self.display.grid(row=0, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

        buttons = [
            'S', '8', '9', '/',
            'P', 'M', '6', '*',
            '1', '2', '3', '-',
            '0', '.', '=', '+'
        ]

        row = 1
        col = 0
        for button in buttons:
            tk.Button(root, text=button, font=("Arial", 18), command=lambda b=button: self.on_button_click(b)).grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            col += 1
            if col > 3:
                col = 0
                row += 1

        tk.Button(root, text="C", font=("Arial", 18), command=self.clear).grid(row=row, column=0, columnspan=4, padx=5, pady=5, sticky="nsew")

        self.expression = ""

    def on_button_click(self, char):
        if char == '=':
            if self.expression == "S+M+S+P":
                result = "skriv med skriv på"
            else:
                try:
                    result = str(eval(self.expression))
                except:
                    result = "nei ikke sånn din idiot!!!"
                    self.expression = ""
            self.display.delete(0, tk.END)
            self.display.insert(tk.END, result)
            self.expression = result
        else:
            self.expression += char
            self.display.delete(0, tk.END)
            self.display.insert(tk.END, self.expression)

    def clear(self):
        self.expression = ""
        self.display.delete(0, tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    calc = Calculator(root)
    root.mainloop()

    def clear(self):
        self.expression = ""
        self.display.delete(0, tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    calc = Calculator(root)
    root.mainloop()