import numpy as np

def gauss_elimination(A, b):
    n = len(b)

    # Eliminación hacia adelante
    for k in range(n-1):
        if A[k][k] == 0:
            raise ValueError("Pivote cero, el método puede fallar")

        for i in range(k+1, n):
            factor = A[i][k] / A[k][k]
            for j in range(k, n):
                A[i][j] = A[i][j] - factor * A[k][j]
            b[i] = b[i] - factor * b[k]

    # Sustitución hacia atrás
    x = np.zeros(n)

    for i in range(n-1, -1, -1):
        suma = 0
        for j in range(i+1, n):
            suma += A[i][j] * x[j]

        x[i] = (b[i] - suma) / A[i][i]

    return x

n = int(input("Ingrese el número de ecuaciones: "))

A = np.zeros((n, n))
b = np.zeros(n)

print("\nIngrese la matriz A:")
for i in range(n):
    for j in range(n):
        A[i][j] = float(input(f"A[{i+1}][{j+1}]: "))

print("\nIngrese el vector b:")
for i in range(n):
    b[i] = float(input(f"b[{i+1}]: "))

# Resolver
solucion = gauss_elimination(A, b)

# Mostrar resultados
print("\nSolución del sistema:")
for i in range(n):
    print(f"x{i+1} = {solucion[i]}")
