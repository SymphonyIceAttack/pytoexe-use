import re

def inverter_coordenadas(texto):
    pontos = re.split(r'\s+', texto.strip())
    pontos = [p for p in pontos if p]
    return " ".join(reversed(pontos))

print("Cole a lista de coordenadas e pressione ENTER duas vezes:")

linhas = []
while True:
    try:
        linha = input()
        if linha.strip() == "":
            break
        linhas.append(linha)
    except:
        break

entrada = " ".join(linhas)

resultado = inverter_coordenadas(entrada)

print("\nResultado:\n")
print(resultado)

input("\nPressione ENTER para sair...")