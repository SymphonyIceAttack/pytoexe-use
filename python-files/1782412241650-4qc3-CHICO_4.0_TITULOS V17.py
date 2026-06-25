import time
import pyautogui
import json
import os
import pandas as pd
from datetime import datetime

# Configurações de tempo ajustadas
TEMPO_PADRAO = 0.8  # Reduzido para 1.5 segundo conforme solicitado
TEMPO_LENTO = 2.5   # Mantido 3.0 segundos para os campos pesados

CONFIG_FILE = "configuracoes.json"
PLANILHA_PATH = r"C:\Users\elton\Desktop\DFLOG_TITULOS.xlsx"

def formatar_data(valor):
    try:
        dt = datetime.strptime(str(valor).strip(), '%Y-%m-%d')
        return dt.strftime('%d/%m/%Y')
    except:
        return str(valor)

def calibrar():
    campos = ["Titulo", "Parcela", "Fornecedor", "Data_Emissao", "Data_Vencimento", 
              "Especie_Conf1", "Especie_Conf2", "Portador_Conf1", "Portador_Conf2", 
              "Natureza_Conf1", "Natureza_Conf2", "Valor_Titulo", "Conta", 
              "Departamento", "Historico", "Confirma_1", "Confirma_2", "Salvar"]
    
    coords = {}
    print("\n--- INICIANDO CALIBRAÇÃO ---")
    for c in campos:
        input(f"Posicione o mouse em [{c}] e aperte ENTER...")
        x, y = pyautogui.position()
        coords[c] = {"x": x, "y": y}
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(coords, f)
    print("\n[OK] Calibração salva com sucesso!")
    input("Aperte ENTER para voltar ao menu...")

def executar():
    if not os.path.exists(CONFIG_FILE):
        print("\n[ERRO] Calibre primeiro!")
        return
        
    with open(CONFIG_FILE, 'r') as f:
        coords = json.load(f)
    
    df = pd.read_excel(PLANILHA_PATH)
    
    for i, linha in df.iterrows():
        print(f"Processando linha {i+1}...")
        
        def digitar(campo, valor, tempo=TEMPO_PADRAO):
            c = coords[campo]
            pyautogui.click(c["x"], c["y"])
            time.sleep(tempo)
            pyautogui.hotkey('ctrl', 'a')
            pyautogui.press('backspace')
            pyautogui.write(str(valor))
            time.sleep(tempo)

        def clicar(campo, tempo=TEMPO_PADRAO):
            c = coords[campo]
            pyautogui.click(c["x"], c["y"])
            time.sleep(tempo)

        # Preenchimento
        digitar("Titulo", linha["TITULO"])
        digitar("Parcela", linha["PARCELA"])
        digitar("Fornecedor", linha["FORNECEDOR"])
        digitar("Data_Emissao", formatar_data(linha["DATA DE EMISSÃO"]))
        digitar("Data_Vencimento", formatar_data(linha["DATA DE VENCIMENTO"]))
        
        # Cliques normais e especiais
        clicar("Especie_Conf1", TEMPO_PADRAO)
        clicar("Especie_Conf2", TEMPO_LENTO) # Espera 3.0 segundos
        
        clicar("Portador_Conf1", TEMPO_PADRAO)
        clicar("Portador_Conf2", TEMPO_LENTO) # Espera 3.0 segundos
        
        clicar("Natureza_Conf1", TEMPO_PADRAO)
        clicar("Natureza_Conf2", TEMPO_LENTO) # Espera 3.0 segundos
            
        digitar("Valor_Titulo", linha["VALOR DO TITULO"])
        digitar("Conta", linha["CONTA"])
        digitar("Departamento", linha["DEPARTAMENTO"])
        digitar("Historico", linha["HISTORICO"])
        
        # Cliques finais com o novo tempo padrão
        clicar("Confirma_1", TEMPO_PADRAO)
        clicar("Confirma_2", TEMPO_PADRAO)
        clicar("Salvar", TEMPO_PADRAO)

    print("\nProcesso finalizado!")
    input("Aperte ENTER para voltar ao menu...")

if __name__ == "__main__":
    while True:
        print("\n=== SISTEMA DE AUTOMAÇÃO DFLOG ===")
        print("1 - Calibrar")
        print("2 - Executar")
        print("0 - Sair")
        op = input("Escolha uma opção: ")
        if op == "1": calibrar()
        elif op == "2": executar()
        elif op == "0": break