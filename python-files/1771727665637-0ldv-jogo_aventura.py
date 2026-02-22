python
import os
import time
import random

def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')

def digitar_devagar(texto):
    for char in texto:
        print(char, end='', flush=True)
        time.sleep(0.03)
    print()

def introducao():
    limpar_tela()
    print("=" * 50)
    print("         A LENDA DA FLORESTA ENCANTADA")
    print("=" * 50)
    time.sleep(1)
    digitar_devagar("\nVocê é um jovem aventureiro em busca da lendária Flor da Eternidade...")
    time.sleep(1)
    digitar_devagar("Dizem que quem a encontrar terá seu maior desejo realizado!")
    time.sleep(1)
    input("\nPressione ENTER para continuar...")

def primeira_decisao():
    limpar_tela()
    print("\nVocê está na entrada da floresta. O caminho se divide em dois:")
    print("1️⃣ - Pegar o caminho da esquerda, que parece mais iluminado")
    print("2️⃣ - Pegar o caminho da direita, que é mais escuro e misterioso")
    print("3️⃣ - Voltar para casa (desistir da aventura)")
    
    while True:
        escolha = input("\nQual caminho você escolhe? (1, 2 ou 3): ")
        if escolha == "1":
            return caminho_iluminado()
        elif escolha == "2":
            return caminho_escuro()
        elif escolha == "3":
            return desistir()
        else:
            print("Escolha inválida! Tente novamente.")

def caminho_iluminado():
    limpar_tela()
    digitar_devagar("Você segue pelo caminho iluminado...")
    time.sleep(1)
    digitar_devagar("De repente, encontra um riacho cristalino!")
    time.sleep(1)
    
    print("\nO que você faz?")
    print("1️⃣ - Beber a água do riacho")
    print("2️⃣ - Atravessar o riacho")
    print("3️⃣ - Voltar para a entrada da floresta")
    
    while True:
        escolha = input("\nSua escolha: ")
        if escolha == "1":
            return beber_agua()
        elif escolha == "2":
            return atravessar_riacho()
        elif escolha == "3":
            return primeira_decisao()
        else:
            print("Escolha inválida!")

def caminho_escuro():
    limpar_tela()
    digitar_devagar("Você adentra o caminho escuro...")
    time.sleep(1)
    digitar_devagar("De repente, ouve um barulho estranho vindo dos arbustos!")
    time.sleep(1)
    
    print("\nO que você faz?")
    print("1️⃣ - Investigar o barulho")
    print("2️⃣ - Correr o mais rápido possível")
    print("3️⃣ - Voltar para a entrada da floresta")
    
    while True:
        escolha = input("\nSua escolha: ")
        if escolha == "1":
            return investigar()
        elif escolha == "2":
            return correr()
        elif escolha == "3":
            return primeira_decisao()
        else:
            print("Escolha inválida!")

def beber_agua():
    limpar_tela()
    digitar_devagar("Você bebe da água cristalina...")
    time.sleep(1)
    digitar_devagar("É mágica! Você se sente revigorado e ganha energia!")
    time.sleep(1)
    digitar_devagar("Continuando sua jornada, você encontra a Flor da Eternidade!")
    time.sleep(1)
    final_feliz()

def atravessar_riacho():
    limpar_tela()
    digitar_devagar("Você tenta atravessar o riacho...")
    time.sleep(1)
    digitar_devagar("As pedras estão escorregadias e você cai na água!")
    time.sleep(1)
    if random.random() > 0.5:
        digitar_devagar("Por sorte, você consegue nadar até a outra margem!")
        digitar_devagar("Lá, encontra a Flor da Eternidade!")
        final_feliz()
    else:
        digitar_devagar("A correnteza está muito forte e você é levado...")
        digitar_devagar("Você acorda na entrada da floresta, molhado e confuso.")
        time.sleep(1)
        primeira_decisao()

def investigar():
    limpar_tela()
    digitar_devagar("Você se aproxima cautelosamente...")
    time.sleep(1)
    digitar_devagar("É um pequeno duende da floresta!")
    time.sleep(1)
    digitar_devagar("'Ajude-me! Perdi meu chapéu mágico' - diz o duende.")
    
    print("\nO que você faz?")
    print("1️⃣ - Ajudar o duende a encontrar o chapéu")
    print("2️⃣ - Ignorar e seguir em frente")
    
    escolha = input("\nSua escolha: ")
    if escolha == "1":
        return ajudar_duende()
    else:
        return ignorar_duende()

def ajudar_duende():
    limpar_tela()
    digitar_devagar("Você ajuda o duende a procurar o chapéu...")
    time.sleep(1)
    digitar_devagar("Encontra o chapéu perto de uma árvore!")
    time.sleep(1)
    digitar_devagar("O duende, agradecido, te dá uma poção mágica!")
    time.sleep(1)
    digitar_devagar("Com a poção, você consegue enxergar o caminho para a Flor da Eternidade!")
    final_feliz()

def ignorar_duende():
    limpar_tela()
    digitar_devagar("Você ignora o duende e segue seu caminho...")
    time.sleep(1)
    digitar_devagar("A floresta fica cada vez mais escura...")
    time.sleep(1)
    digitar_devagar("Você se perde e nunca encontra a saída...")
    final_triste()

def correr():
    limpar_tela()
    digitar_devagar("Você corre desesperadamente...")
    time.sleep(1)
    digitar_devagar("Tropeça em uma raiz e cai em um buraco!")
    time.sleep(1)
    digitar_devagar("Você acorda em casa, foi tudo um sonho...")
    final_triste()

def final_feliz():
    print("\n" + "=" * 50)
    print("         🎉 FELIZ FINAL! 🎉")
    print("=" * 50)
    digitar_devagar("\nVocê encontrou a Flor da Eternidade!")
    digitar_devagar("Seu desejo foi realizado e você se tornou uma lenda!")
    digitar_devagar("\nObrigado por jogar!")
    jogar_novamente()

def final_triste():
    print("\n" + "=" * 50)
    print("         😔 FIM DA AVENTURA 😔")
    print("=" * 50)
    digitar_devagar("\nSua jornada terminou de forma inesperada...")
    digitar_devagar("Tente novamente para um final diferente!")
    jogar_novamente()

def desistir():
    limpar_tela()
    digitar_devagar("Você decide voltar para casa...")
    time.sleep(1)
    digitar_devagar("Quem sabe um dia você terá coragem para tentar novamente?")
    jogar_novamente()

def jogar_novamente():
    print("\n" + "-" * 30)
    escolha = input("Deseja jogar novamente? (s/n): ").lower()
    if escolha == 's':
        main()
    else:
        limpar_tela()
        print("\nAté a próxima aventura! 👋")
        time.sleep(2)
        exit()

def main():
    introducao()
    primeira_decisao()

if __name__ == "__main__":
    main()
