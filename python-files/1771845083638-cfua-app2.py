"""
Calculator App - A modern calculator with standard functions
"""

import customtkinter as ctk
from tkinter import messagebox

# Configure appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Color scheme
COLORS = {
    "bg": "#1a1a2e",
    "display_bg": "#16213e",
    "button_bg": "#0f3460",
    "button_hover": "#1a4a7a",
    "operator": "#e94560",
    "operator_hover": "#ff6b6b",
    "equals": "#4ade80",
    "equals_hover": "#22c55e",
    "clear": "#f59e0b",
    "clear_hover": "#d97706",
    "text": "#eaeaea",
    "text_secondary": "#a0a0a0"
}

class CalculatorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window setup
        self.title("Calculator")
        self.geometry("350x500")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["bg"])

        # Calculator state
        self.current_expression = ""
        self.should_reset_display = False

        # Setup UI
        self.setup_ui()
        self.center_window()

    def center_window(self):
        """Center the window on screen"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def setup_ui(self):
        """Setup all UI components"""
        
        # Main container
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # Display
        self.display_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color=COLORS["display_bg"],
            corner_radius=10
        )
        self.display_frame.pack(fill="x", pady=(0, 15))

        self.display = ctk.CTkLabel(
            self.display_frame,
            text="0",
            font=("Helvetica", 32, "bold"),
            text_color=COLORS["text"],
            anchor="e",
            justify="right"
        )
        self.display.pack(fill="x", padx=15, pady=20)

        # Expression display
        self.expression_label = ctk.CTkLabel(
            self.display_frame,
            text="",
            font=("Helvetica", 12),
            text_color=COLORS["text_secondary"],
            anchor="e",
            justify="right"
        )
        self.expression_label.pack(fill="x", padx=15, pady=(0, 5))

        # Button grid
        self.button_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color="transparent"
        )
        self.button_frame.pack(fill="both", expand=True)

        # Button layout
        buttons = [
            ("C", 0, 0, "clear"), ("<-", 0, 1, "operator"), ("%", 0, 2, "operator"), ("/", 0, 3, "operator"),
            ("7", 1, 0, "number"), ("8", 1, 1, "number"), ("9", 1, 2, "number"), ("*", 1, 3, "operator"),
            ("4", 2, 0, "number"), ("5", 2, 1, "number"), ("6", 2, 2, "number"), ("-", 2, 3, "operator"),
            ("1", 3, 0, "number"), ("2", 3, 1, "number"), ("3", 3, 2, "number"), ("+", 3, 3, "operator"),
            ("+/-", 4, 0, "number"), ("0", 4, 1, "number"), (".", 4, 2, "number"), ("=", 4, 3, "equals")
        ]

        for btn_text, row, col, btn_type in buttons:
            self.create_button(btn_text, row, col, btn_type)

    def create_button(self, text, row, col, btn_type):
        """Create a calculator button"""
        
        if btn_type == "number":
            fg_color = COLORS["button_bg"]
            hover_color = COLORS["button_hover"]
            text_color = COLORS["text"]
            font = ("Helvetica", 20, "bold")
            command = lambda t=text: self.add_digit(t)
        elif btn_type == "operator":
            fg_color = COLORS["button_bg"]
            hover_color = COLORS["button_hover"]
            text_color = COLORS["operator"]
            font = ("Helvetica", 20, "bold")
            command = lambda t=text: self.add_operator(t)
        elif btn_type == "equals":
            fg_color = COLORS["equals"]
            hover_color = COLORS["equals_hover"]
            text_color = "#1a1a2e"
            font = ("Helvetica", 20, "bold")
            command = self.calculate
        elif btn_type == "clear":
            fg_color = COLORS["clear"]
            hover_color = COLORS["clear_hover"]
            text_color = "#1a1a2e"
            font = ("Helvetica", 18, "bold")
            command = self.clear

        if text == "<-":
            command = self.backspace
        if text == "+/-":
            command = self.toggle_sign

        btn = ctk.CTkButton(
            self.button_frame,
            text=text,
            font=font,
            fg_color=fg_color,
            hover_color=hover_color,
            text_color=text_color,
            height=55,
            corner_radius=10,
            command=command
        )
        btn.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        self.button_frame.rowconfigure(row, weight=1)
        self.button_frame.columnconfigure(col, weight=1)

    def add_digit(self, digit):
        """Add a digit to the expression"""
        if self.should_reset_display:
            self.current_expression = ""
            self.should_reset_display = False
        
        if self.current_expression == "0" and digit != ".":
            self.current_expression = digit
        else:
            self.current_expression += digit
        
        self.update_display()

    def add_operator(self, operator):
        """Add an operator to the expression"""
        if self.current_expression:
            self.current_expression += operator
            self.should_reset_display = False
            self.update_display()

    def calculate(self):
        """Calculate the result"""
        if not self.current_expression:
            return
        
        try:
            result = eval(self.current_expression)
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            self.expression_label.configure(text=self.current_expression + " =")
            self.current_expression = str(result)
            self.should_reset_display = True
            self.update_display()
        except ZeroDivisionError:
            messagebox.showerror("Error", "Cannot divide by zero!")
            self.current_expression = ""
            self.update_display()
        except Exception:
            messagebox.showerror("Error", "Invalid expression!")
            self.current_expression = ""
            self.update_display()

    def clear(self):
        """Clear the calculator"""
        self.current_expression = ""
        self.expression_label.configure(text="")
        self.should_reset_display = False
        self.update_display()

    def backspace(self):
        """Delete last character"""
        if self.current_expression:
            self.current_expression = self.current_expression[:-1]
            self.update_display()

    def toggle_sign(self):
        """Toggle the sign of the current number"""
        if self.current_expression:
            try:
                if self.current_expression.startswith("-"):
                    self.current_expression = self.current_expression[1:]
                else:
                    self.current_expression = "-" + self.current_expression
                self.update_display()
            except:
                pass

    def update_display(self):
        """Update the display"""
        display_text = self.current_expression if self.current_expression else "0"
        if len(display_text) > 15:
            display_text = display_text[:15] + "..."
        self.display.configure(text=display_text)


def main():
    app = CalculatorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
