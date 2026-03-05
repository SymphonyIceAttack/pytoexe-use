import customtkinter as ctk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import tkinter as tk
from tkinter import messagebox
import threading

# Configure CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ------------------------------------------------------------
# MÉTODOS NUMÉRICOS (implementados do zero)
# ------------------------------------------------------------
def bissecao(f, a, b, tol=1e-5, max_iter=100):
    """Método da Bissecção"""
    if f(a) * f(b) >= 0:
        return None, 0, [], [], "Erro: f(a) e f(b) devem ter sinais opostos."
    
    iteracoes = []
    erro_atual = float('inf')
    x_medio = a
    
    for i in range(1, max_iter + 1):
        x_anterior = x_medio
        x_medio = (a + b) / 2
        fx = f(x_medio)
        
        if i > 1:
            erro_atual = abs(x_medio - x_anterior)
        else:
            erro_atual = abs(b - a)
            
        iteracoes.append((i, x_medio, fx, erro_atual))
        
        if erro_atual < tol:
            break
            
        if f(a) * fx < 0:
            b = x_medio
        else:
            a = x_medio
    
    return x_medio, i, [it[3] for it in iteracoes], iteracoes, ""

def newton_raphson(f, df, x0, tol=1e-5, max_iter=100):
    """Método de Newton-Raphson"""
    iteracoes = []
    x = x0
    erro_atual = float('inf')
    
    for i in range(1, max_iter + 1):
        fx = f(x)
        dfx = df(x)
        
        if dfx == 0:
            return None, i, [], [], "Derivada zero. Método interrompido."
            
        x_novo = x - fx / dfx
        erro_atual = abs(x_novo - x)
        iteracoes.append((i, x, fx, erro_atual))
        
        if erro_atual < tol:
            x = x_novo
            break
            
        x = x_novo
    
    return x, i, [it[3] for it in iteracoes], iteracoes, ""

def secante(f, x0, x1, tol=1e-5, max_iter=100):
    """Método da Secante"""
    iteracoes = []
    x_ant = x0
    x_atual = x1
    
    for i in range(1, max_iter + 1):
        f_ant = f(x_ant)
        f_atual = f(x_atual)
        
        if f_atual - f_ant == 0:
            return None, i, [], [], "Divisão por zero. Método interrompido."
            
        x_prox = x_atual - f_atual * (x_atual - x_ant) / (f_atual - f_ant)
        erro_atual = abs(x_prox - x_atual)
        iteracoes.append((i, x_atual, f_atual, erro_atual))
        
        if erro_atual < tol:
            x_atual = x_prox
            break
            
        x_ant, x_atual = x_atual, x_prox
    
    return x_atual, i, [it[3] for it in iteracoes], iteracoes, ""

# ------------------------------------------------------------
# DEFINIÇÃO DOS PROBLEMAS
# ------------------------------------------------------------
def f1(x):
    return 150*x - 0.05*x**2 - 20000 - 80*x - 150*np.sqrt(x)

def df1(x):
    return 70 - 0.1*x - 75/np.sqrt(x)

def f2(Q):
    return -40000000 / Q**2 + 3 * (Q/2)**0.2

def df2(Q):
    return 80000000 / Q**3 + 0.3 * (Q/2)**(-0.8)

def f3(mu):
    return 1/(mu - 20) - 0.25

def df3(mu):
    return -1/(mu - 20)**2

def f4(x):
    return x * (400 - 25 * np.log(x)) - 15000

def df4(x):
    return 375 - 25 * np.log(x)

def f5(b):
    return 10 * (100 ** b) - 4

def df5(b):
    return 10 * (100 ** b) * np.log(100)

problemas = [
    {
        "nome": "1 - Ponto de Equilíbrio",
        "descricao": "150x - 0.05x² - 20000 - 80x - 150√x = 0",
        "f": f1,
        "df": df1,
        "intervalo": (100, 500),
        "x0_newton": 300,
        "x0_secante": (100, 200)
    },
    {
        "nome": "2 - Lote Ótimo",
        "descricao": "-40000000/Q² + 3(Q/2)^0.2 = 0",
        "f": f2,
        "df": df2,
        "intervalo": (100, 1000),
        "x0_newton": 500,
        "x0_secante": (100, 200)
    },
    {
        "nome": "3 - Teoria das Filas",
        "descricao": "1/(μ-20) - 0.25 = 0",
        "f": f3,
        "df": df3,
        "intervalo": (21, 50),
        "x0_newton": 30,
        "x0_secante": (21, 25)
    },
    {
        "nome": "4 - Custo de Transporte",
        "descricao": "x(400 - 25 ln(x)) - 15000 = 0",
        "f": f4,
        "df": df4,
        "intervalo": (10, 100),
        "x0_newton": 50,
        "x0_secante": (10, 20)
    },
    {
        "nome": "5 - Curva de Aprendizagem",
        "descricao": "10(100^b) - 4 = 0",
        "f": f5,
        "df": df5,
        "intervalo": (-1, 0),
        "x0_newton": -0.5,
        "x0_secante": (-0.9, -0.1)
    }
]

class NumericalMethodsGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configure window
        self.title("Métodos Numéricos - Calculadora de Raízes")
        self.geometry("1400x800")
        
        # Initialize variables
        self.current_problem = 0
        self.current_method = "Bissecção"  # Initialize before creating UI
        
        # Create main container
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Create sidebar
        self.create_sidebar()
        
        # Create main content area
        self.create_main_content()
        
        # Load first problem by default
        self.load_problem(0)
        
    def create_sidebar(self):
        """Create the sidebar with problem selection"""
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(6, weight=1)
        
        # Title
        title = ctk.CTkLabel(
            self.sidebar, 
            text="Problemas", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Problem selection buttons
        self.problem_buttons = []
        for i, prob in enumerate(problemas):
            btn = ctk.CTkButton(
                self.sidebar,
                text=prob["nome"],
                command=lambda idx=i: self.load_problem(idx),
                fg_color="transparent" if i != 0 else None,
                border_width=1,
                anchor="w",
                height=40
            )
            btn.grid(row=i+1, column=0, padx=20, pady=5, sticky="ew")
            self.problem_buttons.append(btn)
        
        # Settings section
        settings_frame = ctk.CTkFrame(self.sidebar)
        settings_frame.grid(row=7, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        ctk.CTkLabel(
            settings_frame, 
            text="Configurações", 
            font=ctk.CTkFont(weight="bold", size=16)
        ).pack(pady=(10, 5))
        
        # Tolerance
        tol_frame = ctk.CTkFrame(settings_frame)
        tol_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(tol_frame, text="Tolerância:").pack(side="left")
        self.tolerance_var = tk.StringVar(value="1e-5")
        ctk.CTkEntry(tol_frame, textvariable=self.tolerance_var, width=100).pack(side="right")
        
        # Max iterations
        iter_frame = ctk.CTkFrame(settings_frame)
        iter_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(iter_frame, text="Max Iterações:").pack(side="left")
        self.max_iter_var = tk.StringVar(value="100")
        ctk.CTkEntry(iter_frame, textvariable=self.max_iter_var, width=100).pack(side="right")
        
        # Theme toggle
        self.theme_switch = ctk.CTkSwitch(
            settings_frame,
            text="Modo Claro",
            command=self.toggle_theme,
            onvalue="light",
            offvalue="dark"
        )
        self.theme_switch.pack(pady=10)
        
    def create_main_content(self):
        """Create the main content area with tabs and plot"""
        self.main_content = ctk.CTkFrame(self)
        self.main_content.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.main_content.grid_columnconfigure(0, weight=1)
        self.main_content.grid_rowconfigure(2, weight=1)
        
        # Top frame with method selection
        self.create_method_tabs()
        
        # Middle frame with input parameters
        self.create_input_frame()
        
        # Bottom frame with plot and results
        self.create_plot_frame()
        
    def create_method_tabs(self):
        """Create tabs for different numerical methods"""
        self.tab_frame = ctk.CTkFrame(self.main_content)
        self.tab_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        
        self.method_var = tk.StringVar(value="Bissecção")
        
        methods = ["Bissecção", "Newton-Raphson", "Secante"]
        for i, method in enumerate(methods):
            btn = ctk.CTkButton(
                self.tab_frame,
                text=method,
                command=lambda m=method: self.select_method(m),
                fg_color="#2b2b2b" if method != "Bissecção" else "#1f538d",
                hover_color="#1f538d",
                width=150,
                height=40
            )
            btn.grid(row=0, column=i, padx=5, pady=10)
            self.problem_buttons.append(btn)  # This line is problematic, let's fix it
            
    def create_input_frame(self):
        """Create input frame for method parameters"""
        self.input_frame = ctk.CTkFrame(self.main_content)
        self.input_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        # Problem info
        self.problem_label = ctk.CTkLabel(
            self.input_frame,
            text="",
            font=ctk.CTkFont(size=14, weight="bold"),
            wraplength=600
        )
        self.problem_label.grid(row=0, column=0, columnspan=4, padx=10, pady=5, sticky="w")
        
        # Parameter inputs
        self.param_frame = ctk.CTkFrame(self.input_frame)
        self.param_frame.grid(row=1, column=0, columnspan=4, padx=10, pady=5, sticky="ew")
        
        # These will be updated when method changes
        self.param_entries = []
        
        # Calculate button
        self.calc_button = ctk.CTkButton(
            self.input_frame,
            text="Calcular Raiz",
            command=self.calculate_root,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.calc_button.grid(row=2, column=0, columnspan=4, padx=10, pady=10)
        
    def create_plot_frame(self):
        """Create frame for plot and results"""
        self.plot_frame = ctk.CTkFrame(self.main_content)
        self.plot_frame.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        self.plot_frame.grid_columnconfigure(0, weight=1)
        self.plot_frame.grid_rowconfigure(0, weight=1)
        
        # Create matplotlib figure
        self.figure = Figure(figsize=(8, 5), dpi=100)
        self.ax = self.figure.add_subplot(111)
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.figure, self.plot_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        # Results frame with scrollbar
        self.results_container = ctk.CTkFrame(self.plot_frame)
        self.results_container.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        
        self.results_textbox = ctk.CTkTextbox(
            self.results_container,
            height=200,
            font=ctk.CTkFont(family="Courier", size=11)
        )
        self.results_textbox.pack(fill="both", expand=True, padx=5, pady=5)
        
    def update_input_fields(self):
        """Update input fields based on selected method"""
        # Clear existing entries
        for widget in self.param_frame.winfo_children():
            widget.destroy()
        
        self.param_entries = []
        
        if self.current_method == "Bissecção":
            # Interval inputs
            ctk.CTkLabel(self.param_frame, text="Intervalo [a, b]:").grid(row=0, column=0, padx=5, pady=5)
            
            self.a_entry = ctk.CTkEntry(self.param_frame, width=100)
            self.a_entry.grid(row=0, column=1, padx=5, pady=5)
            
            self.b_entry = ctk.CTkEntry(self.param_frame, width=100)
            self.b_entry.grid(row=0, column=2, padx=5, pady=5)
            
            # Set default values from current problem
            a, b = problemas[self.current_problem]["intervalo"]
            self.a_entry.delete(0, "end")
            self.a_entry.insert(0, str(a))
            self.b_entry.delete(0, "end")
            self.b_entry.insert(0, str(b))
            
        elif self.current_method == "Newton-Raphson":
            # Initial guess
            ctk.CTkLabel(self.param_frame, text="Chute inicial x0:").grid(row=0, column=0, padx=5, pady=5)
            
            self.x0_entry = ctk.CTkEntry(self.param_frame, width=100)
            self.x0_entry.grid(row=0, column=1, padx=5, pady=5)
            
            # Set default value
            x0 = problemas[self.current_problem]["x0_newton"]
            self.x0_entry.delete(0, "end")
            self.x0_entry.insert(0, str(x0))
            
        elif self.current_method == "Secante":
            # Two initial guesses
            ctk.CTkLabel(self.param_frame, text="Chutes iniciais:").grid(row=0, column=0, padx=5, pady=5)
            
            self.x0_sec_entry = ctk.CTkEntry(self.param_frame, width=100)
            self.x0_sec_entry.grid(row=0, column=1, padx=5, pady=5)
            
            self.x1_sec_entry = ctk.CTkEntry(self.param_frame, width=100)
            self.x1_sec_entry.grid(row=0, column=2, padx=5, pady=5)
            
            # Set default values
            x0, x1 = problemas[self.current_problem]["x0_secante"]
            self.x0_sec_entry.delete(0, "end")
            self.x0_sec_entry.insert(0, str(x0))
            self.x1_sec_entry.delete(0, "end")
            self.x1_sec_entry.insert(0, str(x1))
    
    def select_method(self, method):
        """Handle method selection"""
        self.current_method = method
        self.update_input_fields()
        
        # Update button styles
        for widget in self.tab_frame.winfo_children():
            if isinstance(widget, ctk.CTkButton):
                if widget.cget("text") == method:
                    widget.configure(fg_color="#1f538d")
                else:
                    widget.configure(fg_color="#2b2b2b")
        
    def load_problem(self, idx):
        """Load selected problem"""
        self.current_problem = idx
        
        # Update button styles
        for i, btn in enumerate(self.problem_buttons):
            if i == idx:
                btn.configure(fg_color="#1f538d")
            else:
                btn.configure(fg_color="transparent")
        
        # Update problem description
        prob = problemas[idx]
        self.problem_label.configure(
            text=f"{prob['nome']}\n{prob['descricao']}"
        )
        
        # Update input fields with new default values
        self.update_input_fields()
        
        # Clear previous results
        self.results_textbox.delete("1.0", "end")
        self.ax.clear()
        self.canvas.draw()
        
    def calculate_root(self):
        """Execute selected numerical method"""
        try:
            tol = float(self.tolerance_var.get())
            max_iter = int(self.max_iter_var.get())
            prob = problemas[self.current_problem]
            
            result = None
            iterations = 0
            errors = []
            iter_data = []
            error_msg = ""
            
            if self.current_method == "Bissecção":
                a = float(self.a_entry.get())
                b = float(self.b_entry.get())
                result, iterations, errors, iter_data, error_msg = bissecao(
                    prob['f'], a, b, tol, max_iter
                )
                
            elif self.current_method == "Newton-Raphson":
                x0 = float(self.x0_entry.get())
                result, iterations, errors, iter_data, error_msg = newton_raphson(
                    prob['f'], prob['df'], x0, tol, max_iter
                )
                
            elif self.current_method == "Secante":
                x0 = float(self.x0_sec_entry.get())
                x1 = float(self.x1_sec_entry.get())
                result, iterations, errors, iter_data, error_msg = secante(
                    prob['f'], x0, x1, tol, max_iter
                )
            
            if error_msg:
                messagebox.showerror("Erro", error_msg)
                return
            
            if result is not None and iter_data:
                # Display results
                self.display_results(result, iterations, errors[-1] if errors else 0, iter_data)
                
                # Update plot
                self.update_plot(prob['f'], prob['intervalo'], result)
            else:
                messagebox.showwarning("Aviso", "Método não convergiu.")
                
        except ValueError as e:
            messagebox.showerror("Erro de entrada", f"Valor inválido: {str(e)}")
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro: {str(e)}")
    
    def display_results(self, root, iterations, final_error, iter_data):
        """Display calculation results"""
        self.results_textbox.delete("1.0", "end")
        
        result_text = f"🔍 RESULTADOS DA {self.current_method.upper()}\n"
        result_text += "=" * 60 + "\n\n"
        result_text += f"📌 Raiz encontrada: {root:.10f}\n"
        result_text += f"📊 Número de iterações: {iterations}\n"
        result_text += f"🎯 Erro final: {final_error:.2e}\n\n"
        result_text += "📋 DETALHES DAS ITERAÇÕES:\n"
        result_text += "-" * 70 + "\n"
        result_text += f"{'Iter':^6} {'x':^20} {'f(x)':^20} {'Erro':^20}\n"
        result_text += "-" * 70 + "\n"
        
        # Show first 5 and last 5 iterations
        if len(iter_data) > 10:
            for it in iter_data[:5]:
                result_text += f"{it[0]:^6} {it[1]:^20.10f} {it[2]:^20.10f} {it[3]:^20.10f}\n"
            result_text += f"{'...':^6} {'...':^20} {'...':^20} {'...':^20}\n"
            for it in iter_data[-5:]:
                result_text += f"{it[0]:^6} {it[1]:^20.10f} {it[2]:^20.10f} {it[3]:^20.10f}\n"
        else:
            for it in iter_data:
                result_text += f"{it[0]:^6} {it[1]:^20.10f} {it[2]:^20.10f} {it[3]:^20.10f}\n"
        
        self.results_textbox.insert("1.0", result_text)
    
    def update_plot(self, f, interval, root):
        """Update the plot with function and root"""
        self.ax.clear()
        
        x_vals = np.linspace(interval[0], interval[1], 500)
        y_vals = f(x_vals)
        
        self.ax.plot(x_vals, y_vals, 'b-', linewidth=2, label='f(x)')
        self.ax.axhline(0, color='gray', linewidth=1, linestyle='--', alpha=0.7)
        self.ax.axvline(root, color='red', linewidth=1, linestyle=':', alpha=0.5)
        self.ax.plot(root, f(root), 'ro', markersize=10, label=f'Raiz = {root:.6f}')
        
        self.ax.set_title(f"Função - {problemas[self.current_problem]['nome']}", fontsize=14, fontweight='bold')
        self.ax.set_xlabel('x', fontsize=12)
        self.ax.set_ylabel('f(x)', fontsize=12)
        self.ax.grid(True, linestyle=':', alpha=0.6)
        self.ax.legend(fontsize=11)
        self.ax.tick_params(labelsize=10)
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def toggle_theme(self):
        """Toggle between light and dark mode"""
        if self.theme_switch.get() == "light":
            ctk.set_appearance_mode("light")
        else:
            ctk.set_appearance_mode("dark")

if __name__ == "__main__":
    app = NumericalMethodsGUI()
    app.mainloop()