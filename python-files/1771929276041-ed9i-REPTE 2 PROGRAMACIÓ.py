# SETUP INICIAL

import math
import time

# SALT DE CONSOLAR
def salt():
    print("\n" * 100)

# LECTURA DE NOMBRES
def lectura(text="Introdueix un nombre: "):
    while True:
        x = input(text).strip().lower()
        if x == "pi":
            return round(math.pi, 4)
        try:
            return float(x)
        except ValueError:
            print("Entrada no vàlida. Escriu un nombre.")

# SORTIDA DE MODE
def exitmode(ex, mode, calc):
    if ex == "0":
        salt()
        return mode
    else:
        if calc:
            print(MENU0)
        else:
            print(MENU1)
        return 0

# AFEGIR AL FITXER
def ftx_afegir(llista, calc):
    ftx = "operacions.txt"
    try:
        with open(ftx, "x", encoding="utf-8") as f:
            f.write("""[=====================]HISTORIAL D'OPERACIONS[=====================]  
-------|SUMES|-------


-------|RESTES|-------


--|MULTIPLICACIONS|--
                                                                                         
                                                                                             
-----|DIVISIONS|-----


---|PERCENTATGES|---


-|ARRELS QUADRADES|-


--|POTÈNCIES|--


--|FUNCIÓNS TRIGONOMÈTRIQUES|--


---|LOGARITME NEPERIÀ|---


""")
    except FileExistsError:
        pass
    with open(ftx, "r", encoding="utf-8") as f:
        linies = f.readlines()
    n_titol = None
    for n, linia in enumerate(linies):
        if f"|{llista}|" in linia.strip():
            n_titol = n
            break
    if n_titol is not None:
        ln_insertar = n_titol + 1
        linies.insert(ln_insertar, f"{calc}\n")
    with open(ftx, "w", encoding="utf-8") as f:
        f.writelines(linies)

# MENÚS
MENU0 = """[==========================================]CALCULADORA[==========================================]
Selecciona una opció:
    1) Sumar
    2) Resta
    3) Multiplicació
    4) Divisió
    5) Percentatge
    6) Arrel quadrada
    7) Potències

Alterna entre calculadora avançada i calculadora bàsica amb 0
Introdueix EXIT per sortir de la calculadora

Presiona ENTER al realitzar la selecció

"""

MENU1 = """[======================================]CALCULADORA AVANÇADA[======================================]
Selecciona una opció:
    1) Sumar
    2) Resta
    3) Multiplicació
    4) Divisió
    5) Percentatge
    6) Arrel quadrada
    7) Potències
    8) Funcions trigonomètriques
    9) Logaritme Neperià

Alterna entre calculadora avançada i calculadora bàsica amb 0
Introdueix EXIT per sortir de la calculadora

Presiona ENTER al realitzar la selecció

"""

print(MENU0)

calc = True
mode = 0

while True:
    sel = input("   Introdueix: ")

    # CANVI MENÚ
    if sel == "0":
        salt()
        if calc:
            print(MENU1)
            calc = False
        else:
            print(MENU0)
            calc = True

    # SUMA
    elif sel == "1":
        salt()
        mode = 1
        while mode == 1:
            n1 = lectura("Introdueix el primer nombre: ")
            n2 = lectura("Introdueix el segon nombre: ")
            r = f"{n1} + {n2} = {n1 + n2}"
            ftx_afegir("SUMES", r)
            print(r)
            ex = input("Escriu 0 per seguir operant; 1 si vols sortir\n")
            mode = exitmode(ex, mode, calc)

    # RESTA
    elif sel == "2":
        salt()
        mode = 2
        while mode == 2:
            n1 = lectura("Introdueix el primer nombre: ")
            n2 = lectura("Introdueix el segon nombre: ")
            r = f"{n1} - {n2} = {n1 - n2}"
            ftx_afegir("RESTES", r)
            print(r)
            ex = input("Escriu 0 per seguir operant; 1 si vols sortir\n")
            mode = exitmode(ex, mode, calc)

    # MULTIPLICACIÓ
    elif sel == "3":
        salt()
        mode = 3
        while mode == 3:
            n1 = lectura("Introdueix el primer nombre: ")
            n2 = lectura("Introdueix el segon nombre: ")
            r = f"{n1} * {n2} = {n1 * n2}"
            ftx_afegir("MULTIPLICACIONS", r)
            print(r)
            ex = input("Escriu 0 per seguir operant; 1 si vols sortir\n")
            mode = exitmode(ex, mode, calc)

    # DIVISIÓ
    elif sel == "4":
        salt()
        mode = 4
        while mode == 4:
            n1 = lectura("Introdueix el primer nombre: ")
            n2 = lectura("Introdueix el segon nombre: ")
            if n2 == 0:
                print("\nError: divisió per zero. Torna-ho a intentar.\n")
                continue
            r = f"{n1} / {n2} = {n1 / n2}"
            ftx_afegir("DIVISIONS", r)
            print(r)
            ex = input("Escriu 0 per seguir operant; 1 si vols sortir\n")
            mode = exitmode(ex, mode, calc)

    # PERCENTATGE
    elif sel == "5":
        salt()
        mode = 5
        while mode == 5:
            mode5 = input("Calcular % d'un nombre (1) o treure % entre dos nombres (2): ")
            if mode5 == "1":
                n1 = lectura("Introdueix el percentatge a calcular (nombre): ")
                n2 = lectura("Introdueix el nombre el qual el percentatge s'aplicarà: ")
                r = f"{n1}% de {n2} = {(n1/100)*n2}"
            elif mode5 == "2":
                n1 = lectura("Introdueix el nombre del qual es treurà el percentatge: ")
                n2 = lectura("Introdueix el nombre amb el qual es treurà el percentatge: ")
                r = f"{n2} és el {(n2/n1)*100}% de {n1}"
            else:
                print("\nIntrodueix un valor correcte\n")
                continue
            ftx_afegir("PERCENTATGES", r)
            print(r)
            ex = input("Escriu 0 per seguir operant; 1 si vols sortir\n")
            mode = exitmode(ex, mode, calc)

    # ARREL QUADRADA
    elif sel == "6":
        salt()
        mode = 6
        while mode == 6:
            n1 = lectura("Introdueix un nombre: ")
            if n1 < 0:
                print("\nError: Arrel de números negatius. Torna-ho a intentar.\n")
                continue
            r = math.sqrt(n1)
            ftx_afegir("ARRELS QUADRADES", r)
            print(r)
            ex = input("Escriu 0 per seguir operant; 1 si vols sortir\n")
            mode = exitmode(ex, mode, calc)

    # POTÈNCIES
    elif sel == "7":
        salt()
        mode = 7
        while mode == 7:
            n1 = lectura("Introdueix el nombre base: ")
            n2 = lectura("Introdueix el nombre exponent: ")
            r = f"{n1} ^ {n2} = {n1 ** n2}"
            ftx_afegir("POTÈNCIES", r)
            print(r)
            ex = input("Escriu 0 per seguir operant; 1 si vols sortir\n")
            mode = exitmode(ex, mode, calc)

    # FUNCIONS TRIGONOMÈETRICAS
    elif sel == "8" and calc == False:
        salt()
        mode = 8
        while mode == 8:
            sincostan = input("Escriu 0 per SIN, 1 per COS i 2 per TAN: ").strip()
            if sincostan not in ("0", "1", "2"):
                print("Opció incorrecta.")
                continue
            n1 = lectura("Introdueix un nombre (en radians): ")
            if sincostan == "0":
                resultat = math.sin(n1)
                r = f"sin({n1}) = {resultat}"
            elif sincostan == "1":
                resultat = math.cos(n1)
                r = f"cos({n1}) = {resultat}"
            elif sincostan == "2":
                resultat = math.tan(n1)
                r = f"tan({n1}) = {resultat}"
            ftx_afegir("FUNCIÓNS TRIGONOMÈTRIQUES", r)
            print(r)
            ex = input("Escriu 0 per seguir operant; 1 si vols sortir\n")
            mode = exitmode(ex, mode, calc)

    # LOGARITME NEPERIÀ
    elif sel == "9" and calc == False:
        salt()
        mode = 9
        while mode == 9:
            n1 = lectura("Introdueix un nombre: ")
            if n1 <= 0:
                print("Error: el logaritme només existeix per nombres positius.")
                continue
            resultat = math.log(n1)
            r = f"ln({n1}) = {resultat}"
            ftx_afegir("LOGARITME NEPERIÀ", r)
            print(r)
            ex = input("Escriu 0 per seguir operant; 1 si vols sortir\n")
            mode = exitmode(ex, mode, calc)

    # FINALITZAR PROGRAMA
    elif sel == "EXIT":
        break

    # INPUT NO RECONEGUT
    else:
        print("Valor no reconegut, prova un altre cop")
