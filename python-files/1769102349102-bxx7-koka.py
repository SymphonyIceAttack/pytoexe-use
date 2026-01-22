import tkinter as tk
from math import sqrt, sin, cos, tan, log, pi, e

class AdvancedCalculator:
    def __init__(self, master):
        self.master = master
        master.title("Isuru Advanced Calculator for SFT")
        master.geometry("400x600")
        master.resizable(False, False)

        self.memory = 0
        self.expression = ""

        self.display = tk.Entry(master, font=("Arial", 24), borderwidth=2, relief="ridge")
        self.display.pack(fill="both", ipadx=8, pady=10, padx=10)

        self.create_buttons()

    def create_buttons(self):
        buttons = [
            ['7', '8', '9', '/', 'sqrt'],
            ['4', '5', '6', '*', '^'],
            ['1', '2', '3', '-', '%'],
            ['0', '.', '=', '+', 'log'],
            ['sin', 'cos', 'tan', 'pi', 'e'],
            ['MC', 'MR', 'M+', 'M-', 'C']
        ]

        for row_values in buttons:
            row_frame = tk.Frame(self.master)
            row_frame.pack(expand=True, fill="both")
            for val in row_values:
                b = tk.Button(row_frame, text=val, font=("Arial", 18), command=lambda x=val: self.on_click(x))
                b.pack(side="left", expand=True, fill="both")

    def on_click(self, char):
        try:
            if char == "=":
                self.expression = self.expression.replace("^", "**")
                result = eval(self.expression)
                self.display.delete(0, tk.END)
                self.display.insert(tk.END, str(result))
                self.expression = str(result)
            elif char == "C":
                self.expression = ""
                self.display.delete(0, tk.END)
            elif char == "MC":
                self.memory = 0
            elif char == "MR":
                self.display.delete(0, tk.END)
                self.display.insert(tk.END, str(self.memory))
                self.expression = str(self.memory)
            elif char == "M+":
                self.memory += eval(self.expression)
            elif char == "M-":
                self.memory -= eval(self.expression)
            elif char == "sqrt":
                self.expression = f"sqrt({self.expression})"
                self.display.delete(0, tk.END)
                self.display.insert(tk.END, self.expression)
            elif char in ["sin", "cos", "tan", "log", "pi", "e"]:
                if char == "pi":
                    self.expression += str(pi)
                elif char == "e":
                    self.expression += str(e)
                else:
                    self.expression = f"{char}({self.expression})"
                self.display.delete(0, tk.END)
                self.display.insert(tk.END, self.expression)
            else:
                self.expression += str(char)
                self.display.delete(0, tk.END)
                self.display.insert(tk.END, self.expression)
        except Exception as e:
            self.display.delete(0, tk.END)
            self.display.insert(tk.END, "Error")
            self.expression = ""

if __name__ == "__main__":
    root = tk.Tk()
    calc = AdvancedCalculator(root)
    root.mainloop()
