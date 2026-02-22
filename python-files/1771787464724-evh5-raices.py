import cmath

while True:
    print("SOLUCION DE ECUACIONES CUADRATICAS")
    print("Ecuacion en su forma general: ax^2 + bx + c = 0")
    print("-" * 20)

    a = float(input("Ingrese el valor de a: "))
    b = float(input("Ingrese el valor de b: "))
    c = float(input("Ingrese el valor de c: "))

    if a == 0:
        print("Error: No es ecuacion cuadratica")
    else:
        d = b**2 - 4*a*c
        
        if d == 0:  #Caso 1
            print("La ecuacion tiene una sola raiz real")
            x = -b/(2*a)
            print(f"x = {x:.3f}")
            
        elif d > 0:  # CASO 2
            print("La ecuacion tiene dos raices reales")
            x1 = (-b + d**0.5)/(2*a)
            x2 = (-b - d**0.5)/(2*a)
            print(f"x1 = {x1:.3f}")
            print(f"x2 = {x2:.3f}")
            
        else:  # CASO 3
            print("La ecuacion tiene raices complejas conjugadas")
            x1 = (-b + cmath.sqrt(d))/(2*a)
            x2 = (-b - cmath.sqrt(d))/(2*a)
            print(f"x1 = {x1:.3f}")
            print(f"x2 = {x2:.3f}")
    
    print("-" * 20)
    resp = input("¿Desea resolver otra ecuacion? (si/no): ")
    if resp.lower() != 'si':
        break

print("Programa terminado")