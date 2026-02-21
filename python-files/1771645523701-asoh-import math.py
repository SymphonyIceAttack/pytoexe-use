import math
import matplotlib.pyplot as plt

def dados_x():
    print("\n ===|| Medidas do vetor x||===")
    vetor_x = []
    medidas = int(input("\n===|| Digite a quantidade de medidas ||==="))

    while True:
        listinha = []
        
        while len(listinha) < medidas:
            a = input().replace(',','.')
            a_help = a.replace('.','').replace(',','')

            if a_help.isdigit():
                a = float(a) 
                listinha.append(a)
                continue

            elif a_help == 't':
                listinha.remove(len(listinha))
                continue

            elif a_help == 't' and len(listinha) == 0:
                print("\n===|| A lista não possiui itens suficiente || adicione ao menos um item para poder remover ||===")
                continue

            else:
                print("===|| Digite um número válido ||===")
                continue
        
        vetor_x.append(listinha)

        confirma = input("\n===|| Digite c para continuar ou s para sair ||=== ")

        confirma_help = confirma.replace(' ','')
        confirma_help = confirma.capitalize()

        if confirma_help == 'C':
            continue

        elif confirma_help == 'S':
            break

        else:
            print("\n===|| Digite uma opção válida ||===")
            continue
    print("\nVetor x = ",vetor_x)
    return vetor_x

def dados_y(vetor_x):
    vetor_y = []
    print("\n ===|| Medidas do vetor y ||===")

    while len(vetor_y) < len(vetor_x):
        a = input().replace(',','.')
        a_help = a.replace('.','').replace('-','')

        if a_help.isdigit():
            a = float(a)
            vetor_y.append(a)
            continue

        elif a_help == 't':
            vetor_y.remove(len(vetor_y))
            continue

        elif a_help == 't' and len(vetor_y) == 0:
            print("\n===|| A lista não possiui itens suficiente || adicione ao menos um item para poder remover ||===")
            continue

        else:
            print("\n===|| Digite um número válido ||===")
            continue

    print("\nVetor y = ",vetor_y)

    return vetor_y

def media(vetor_x):
    vetor_media = []
    i = 0

    while i < len(vetor_x):
        j = 0
        b = 0

        while j < len(vetor_x[i]):
            b += vetor_x[i][j]
            j += 1
        
        b = b / (len(vetor_x[i]))
        vetor_media.append(b)
        i += 1
    
    print(vetor_media)

    return vetor_media

def linearizar_x(vetor_x):
    vetx_lin =[]
    i = 0

    while i < len(vetor_x):
        j =0
        vet_help =[]
        while j < len(vetor_x[i]):
            vet_help.append(math.log(vetor_x[i][j]))
            j += 1
        
        vetx_lin.append(vet_help)
        i += 1
    return vetx_lin

def media_linear(vetx_lin):
    medvetxlin = media(vetx_lin)
    print(medvetxlin)

    return medvetxlin

def linearizar_y(vetor_y):
    vety_lin = []
    i = 0
    
    while i< len(vetor_y):
        vety_lin.append(math.log(vetor_y[i]))
        i += 1
    
    return vety_lin

def desvpad(vetorx,media):
    desvios = []
    i = 0

    while i < len(vetorx):
        j = 0
        a = 0
        while j < len(vetorx[i]):
            a += pow((media[i]-vetorx[i][j]),2)
            j += 1
        
        a /= len(vetorx[i])
        a = pow(a,(1/2))
        desvios.append(a)
        i+=1
    
    return desvios

def graf_linear():
    x,y = graf_normal()
    
    logx = linearizar_x(x)
    logy = linearizar_y(y)
    rlogx = media(logx)

    desvios = desvpad(logx, rlogx)

    
    plt.figure(1,figsize=(7,6))
    plt.plot(logx, logy, '-bo')
    plt.xlabel("Ln (massa)")
    plt.ylabel("Ln (tempo)")
    plt.title("GRÁFICO LINEARIZADO || M(t)")
    plt.grid(True)
    plt.errorbar(rlogx,logy,yerr= desvios)
    plt.errorbar(rlogx,logy,xerr= math.log(0.1))
    plt.show()

def graf_normal():

    x = dados_x()
    y = dados_y(x)
    desvios = desvpad(x,media(x))

    plt.figure(1,figsize=(7,6))
    plt.plot(media(x),y, '-bo')
    plt.xlabel("Ln (massa)")
    plt.ylabel("Ln (tempo)")
    plt.title("GRÁFICO LINEARIZADO || M(t)")
    plt.grid(True)
    plt.errorbar(media(x), y, yerr = desvios)
    plt.errorbar(media(x), y, xerr = 0.1)
    plt.show()

    return x ,y

graf_linear()
