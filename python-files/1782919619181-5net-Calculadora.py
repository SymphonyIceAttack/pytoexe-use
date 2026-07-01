def CEP():
    while True:
        P1 = input("¿que quieres hacer? (suma, resta, multiplicación, división, media, potencia, raiz cuadrada, porcentaje) ")
        a = int(input("primer numero: "))
        b = int(input("segundo numero: "))
        c = int(input("tercer numero: "))
        d = int(input("cuarto numero: "))
        e = int(input("quinto numero: "))
        if P1 == "suma":
            print(a + b + c + d + e)
            VVR = input("Volver a calcular? (Y/N)\n")
            if VVR == "N":
                break
                exit()
        elif P1 == "resta":
            print(a - b - c - d - e)
            VVR = input("Volver a calcular? (Y/N)\n")
            if VVR == "N":
                break
                exit()
        elif P1 == "multiplicación":
            print(a * b * c * d * e)
            VVR = input("Volver a calcular? (Y/N)\n")
            if VVR == "N":
                break
                exit()
        elif P1 == "división":
            print(a / b / c / d / e)
            VVR = input("Volver a calcular? (Y/N)\n")
            if VVR == "N":
                break
                exit() 
        elif P1 == "media":
            print((a + b + c + d + e) / 5)
            VVR = input("Volver a calcular? (Y/N)\n")
            if VVR == "N":
                break
                exit()
        elif P1 == "potencia":
            print(a ** b)
            VVR = input("Volver a calcular? (Y/N)\n")
            if VVR == "N":
                break
                exit()
        elif P1 == "raiz cuadrada":
            print(a ** 0.5)
            VVR = input("Volver a calcular? (Y/N)\n")
            if VVR == "N":
                break
                exit()
        elif P1 == "porcentaje":
            print(a / 100 * b)
            VVR = input("Volver a calcular? (Y/N)\n")
            if VVR == "N":
                break
                exit()
        else:
            print("operación no valida")
CEP()
            
