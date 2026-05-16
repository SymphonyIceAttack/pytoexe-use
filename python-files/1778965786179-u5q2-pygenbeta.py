# PyGenBETA tradutor básico das falas da geração beta
# biblotecas importantes
import random
import pyttsx3
import winsound

# variáveis
frases = ["betinha", "farmar aura", "youtube", "pou"]

# código principal - linhas
print("  ---------")
print("--         --")
print("-  [] []    -")
print("-           -")
print("-  |        -")
print("-   --      -")
print("-------------")
print("Bem-vindo ao PyGenBETA! Aqui vc traduz frases da geração beta para o... PORTUGUÊS. Então,")

while True:
    winsound.Beep(2000, 500)
    opção = input("digite 1 para traduzir uma frase, 2 para o dicionário de palavras da geração beta e 3 para um exemplo de frase da geração beta. ")
    print("")
    if opção == "1":
        pyttsx3.speak("Digite a sua frase para ser traduzida...")
        frase = input("Digite a sua frase para ser traduzida... ")
        print("")
        frase = frase.lower()
        traducao = frase.replace("slk", "vc é louco")
        traducao = traducao.replace("farmar aura", "acumular muito estilo e popularidade")
        traducao = traducao.replace("farmei aura", "acumulei muito estilo e popularidade")
        traducao = traducao.replace("farmou aura", "acumulou muito estilo e popularidade")
        traducao = traducao.replace("farmarei aura", "acumularei muito estilo e popularidade")
        traducao = traducao.replace("farmo aura", "acumulo muito estilo e popularidade")
        traducao = traducao.replace("farma aura", "acumula muito estilo e popularidade")
        traducao = traducao.replace("betinha", "fracote")
        traducao = traducao.replace("67", "sixseven")
        traducao = traducao.replace("42", "four-two")
        traducao = traducao.replace("sabor","parecido com")
        winsound.Beep(2500, 500)
        print(f"Frase traduzida: {traducao}")
        print("")
        pyttsx3.speak(traducao)
    elif opção == "2":
        winsound.Beep(2300, 500)
        print("Dicionário:")
        print("1. slk = voce é louco, geralmente usado junto com [não compensa].")
        print("2. farmar aura = acumular muito estilo e popularidade, é como se vc fosse o chefe, o poderoso da turma, que todo mundo fica impressionado com vc.")
        print("3. betinha = fracote, auto-explicativo.")
        print("4. 67 = um meme sem sentido que todo mundo usa, por isso não tem tradução.")
        print("5. 42 = Uma brincadeira de uma Youtuber chamada Giuliana Mafra entre inscritos para 'derrotar' o 67, o que virou um meme viral e ela sofreu muitos hates.")
        print("6. sabor = uma coisa que é parecida com outra, mas apenas imita a outra coisa.")
        pyttsx3.speak("Aqui está o dicionário.")
    elif opção == "3":
        print("Aqui está um exemplo de frase da geração beta.")
        pyttsx3.speak("Aqui está um exemplo de frase da geração beta.")
        aleatorio = random.choice(frases)
        exemplo = "É SABOR"
        exemplo = f"{exemplo} {aleatorio}"
        print(exemplo)
        pyttsx3.speak(exemplo) 
    else:
        print("Resposta inválida.")
        pyttsx3.speak("Resposta inválida.")       
