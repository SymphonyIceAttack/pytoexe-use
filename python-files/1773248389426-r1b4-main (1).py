/import sympy as sp

def basic_calculator():
    print("\nBasic Calculator")
    expression = input("Enter a math expression (example: 2+3*4): ")
    
    try:
        result = sp.sympify(expression)
        print("Result:", result)
    except:
        print("Invalid expression")

def solve_equation():
    print("\nEquation Solver")
    x = sp.symbols('x')
    
    equation = input("Enter equation in form (example: 2*x+5=15): ")
    
    try:
        left, right = equation.split("=")
        eq = sp.Eq(sp.sympify(left), sp.sympify(right))
        solution = sp.solve(eq, x)
        print("Solution:", solution)
    except:
        print("Invalid equation format")

def derivative():
    print("\nDerivative Calculator")
    x = sp.symbols('x')
    
    func = input("Enter function (example: x**2 + 3*x): ")
    
    try:
        derivative = sp.diff(func, x)
        print("Derivative:", derivative)
    except:
        print("Invalid function")

def integral():
    print("\nIntegral Calculator")
    x = sp.symbols('x')
    
    func = input("Enter function (example: x**2): ")
    
    try:
        integral = sp.integrate(func, x)
        print("Integral:", integral)
    except:
        print("Invalid function")

def menu():
    while True:
        print("\n===== Student Math Solver App =====")
        print("1. Basic Calculator")
        print("2. Solve Equation")
        print("3. Derivative")
        print("4. Integral")
        print("5. Exit")
        
        choice = input("Choose option: ")

        if choice == "1":
            basic_calculator()
        elif choice == "2":
            solve_equation()
        elif choice == "3":
            derivative()
        elif choice == "4":
            integral()
        elif choice == "5":
            print("Goodbye!")
            break
        else:
            print("Invalid option")

menu()