import os
import json
import time
import tkinter as tk
from tkinter import filedialog
from datetime import datetime
import pandas as pd
import pyautogui

# Configuração de segurança do PyAutoGUI
pyautogui.FAILSAFE = True

CONFIG_FILE = "configuracoes.json"
# Inicializamos sem um caminho fixo, permitindo busca
PLANILHA_PATH = "" 
TEMPO_ESPERA = 2

CAMPOS_CALIBRACAO = [
    "Fornecedor", "Conhecimento", "Serie", "Entrada", "Valor", "Vencimento",
    "Base_COFINS", "Aliq_COFINS", "CST_PIS_COFINS", "Base_PIS", "Aliq_PIS",
    "Confirmar_1", "Confirmar_2", "Confirmar_3", "Confirmar_4",
    "Conta", "Departamento", "Confirmar_5", "Salvar"
]

def selecionar_arquivo():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Selecione a Planilha de CTe",
        filetypes=[("Arquivos Excel", "*.xlsx *.xls")]
    )
    root.destroy()
    return file_path

def carregar_configuracoes():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar configurações: {e}")
    return {}

def salvar_configuracoes(config):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        print(f"\nConfigurações salvas com sucesso em '{CONFIG_FILE}'!")
    except Exception as e:
        print(f"Erro ao salvar configurações: {e}")

def calibrar_campos():
    print("\n=== MODO DE CALIBRAÇÃO ===")
    print("Instruções: Posicione o mouse sobre o campo indicado e pressione ENTER para capturar a coordenada.")
    input("Pressione ENTER para começar...")
    
    coordenadas = {}
    for campo in CAMPOS_CALIBRACAO:
        print(f"\nPosicione o mouse sobre o campo: [{campo}]")
        input("Pressione ENTER para capturar...")
        x, y = pyautogui.position()
        coordenadas[campo] = {"x": x, "y": y}
        print(f"Capturado: X={x}, Y={y}")
        
    salvar_configuracoes(coordenadas)

def preencher_campo(coordenadas, campo, valor):
    if campo not in coordenadas:
        print(f"Aviso: Campo '{campo}' não calibrado.")
        return False
    
    x = coordenadas[campo]["x"]
    y = coordenadas[campo]["y"]
    
    pyautogui.click(x, y)
    time.sleep(0.3)
    
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.press('backspace')
    
    if valor is not None and str(valor).strip() != "" and str(valor).lower() != "nan":
        pyautogui.write(str(valor), interval=0.02)
    
    time.sleep(TEMPO_ESPERA)
    return True

def clicar_campo(coordenadas, campo):
    if campo not in coordenadas:
        print(f"Aviso: Botão/Campo '{campo}' não calibrado.")
        return False
    
    x = coordenadas[campo]["x"]
    y = coordenadas[campo]["y"]
    pyautogui.click(x, y)
    time.sleep(TEMPO_ESPERA)
    return True

def formatar_valor_excel(valor):
    if valor is None or str(valor).strip() == "" or str(valor).lower() == "nan":
        return ""
    try:
        if isinstance(valor, (int, float)):
            return f"{valor:.2f}".replace('.', ',')
        return str(valor).strip()
    except:
        return str(valor)

def formatar_data_sem_barras(valor_data):
    if valor_data is None or str(valor_data).strip() == "" or str(valor_data).lower() == "nan":
        return ""
    try:
        if isinstance(valor_data, datetime) or hasattr(valor_data, 'strftime'):
            return valor_data.strftime("%d%m%Y")
        return "".join(filter(str.isdigit, str(valor_data)))
    except:
        return str(valor_data)

def executar_automacao():
    caminho = selecionar_arquivo()
    if not caminho:
        print("Nenhum arquivo selecionado.")
        return

    coordenadas = carregar_configuracoes()
    if not coordenadas:
        print("\n[ERRO] Nenhuma calibração encontrada! Por favor, execute a opção 1 (Calibrar) primeiro.")
        return

    print(f"\nLendo dados da planilha: {caminho}...")
    try:
        df = pd.read_excel(caminho)
    except Exception as e:
        print(f"Erro ao ler a planilha: {e}")
        return

    print(f"Total de linhas encontradas para processar: {len(df)}")
    print("A automação começará em 5 segundos. Mude para a janela do sistema destino!")
    for i in range(5, 0, -1):
        print(f"{i}...")
        time.sleep(1)

    for index, linha in df.iterrows():
        print(f"\nProcessando linha {index + 1}/{len(df)}...")
        
        vencimento_limpo = formatar_data_sem_barras(linha.get("Vencimento", ""))
        
        preencher_campo(coordenadas, "Fornecedor", linha.get("Fornecedor", ""))
        preencher_campo(coordenadas, "Conhecimento", linha.get("Conhecimento", ""))
        preencher_campo(coordenadas, "Serie", linha.get("Serie", ""))
        
        pyautogui.press('tab')
        time.sleep(TEMPO_ESPERA)
        pyautogui.press('enter')
        time.sleep(TEMPO_ESPERA)
        
        preencher_campo(coordenadas, "Entrada", vencimento_limpo)
        
        valor_formatado = formatar_valor_excel(linha.get("Valor", ""))
        preencher_campo(coordenadas, "Valor", valor_formatado)
        
        preencher_campo(coordenadas, "Vencimento", vencimento_limpo)
        
        base_cofins = formatar_valor_excel(linha.get("Base_COFINS", ""))
        preencher_campo(coordenadas, "Base_COFINS", base_cofins)
        
        preencher_campo(coordenadas, "Aliq_COFINS", "7,60")
        preencher_campo(coordenadas, "CST_PIS_COFINS", linha.get("CST_PIS_COFINS", ""))
        
        base_pis = formatar_valor_excel(linha.get("Base_PIS", ""))
        preencher_campo(coordenadas, "Base_PIS", base_pis)
        
        preencher_campo(coordenadas, "Aliq_PIS", "1,65")
        
        clicar_campo(coordenadas, "Confirmar_1")
        clicar_campo(coordenadas, "Confirmar_2")
        clicar_campo(coordenadas, "Confirmar_3")
        clicar_campo(coordenadas, "Confirmar_4")
        
        preencher_campo(coordenadas, "Conta", "5141")
        preencher_campo(coordenadas, "Departamento", "101")
        
        clicar_campo(coordenadas, "Confirmar_5")
        clicar_campo(coordenadas, "Salvar")
        
        print(f"Linha {index + 1} concluída com sucesso.")

    print("\n=== AUTOMAÇÃO FINALIZADA ===")

def main():
    while True:
        print("\n" + "="*30)
        print("      MENU DE AUTOMAÇÃO CTe")
        print("="*30)
        print("1 - Calibrar")
        print("2 - Selecionar Planilha e Executar")
        print("0 - Sair")
        print("="*30)
        
        opcao = input("Escolha uma opção: ").strip()
        
        if opcao == "1":
            calibrar_campos()
        elif opcao == "2":
            executar_automacao()
        elif opcao == "0":
            print("Saindo...")
            break
        else:
            print("Opção inválida! Tente novamente.")

if __name__ == "__main__":
    main()
