import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ================= CONFIG =================
USUARIO = "gabriel.schandler"
SENHA = "Adm@2025"

URL_LOGIN = "http://192.168.15.201/crm/login.php"
URL_PAGINA = "http://192.168.15.201/crm/index.php?codmodulo=147"

# Nome das campanhas (AGORA CORRETO)
CAMPANHAS = [
    "HotLine",
    "Perda e Roubo",
    "Receptivo Lojista",
    "SAC Geral"
]

# ================= FUNÇÕES =================

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def tempo_para_segundos(t):
    try:
        h, m, s = map(int, t.split(":"))
        return h * 3600 + m * 60 + s
    except:
        return 0

def segundos_para_tempo(seg):
    h = seg // 3600
    m = (seg % 3600) // 60
    s = seg % 60
    return f"{h:02}:{m:02}:{s:02}"

def limpar_checkboxes(driver):
    checkboxes = driver.find_elements(By.CLASS_NAME, "chk_ids_campanha")
    for cb in checkboxes:
        if cb.is_selected():
            driver.execute_script("arguments[0].click();", cb)
    time.sleep(1)

def selecionar_campanha(driver, wait, nome):
    log(f"🎯 Selecionando: {nome}")

    # Abrir seletor
    wait.until(EC.element_to_be_clickable((By.ID, "btn_ids_campanha"))).click()
    time.sleep(1)

    # Esperar grid abrir
    wait.until(EC.presence_of_element_located((By.ID, "grid_l_ids_campanha")))

    # Limpar seleção anterior
    limpar_checkboxes(driver)

    # Encontrar linha pelo nome da campanha
    linha = driver.find_element(By.XPATH, f"//td[@title='{nome}']/parent::tr")

    checkbox = linha.find_element(By.XPATH, ".//input[@type='checkbox']")
    driver.execute_script("arguments[0].click();", checkbox)

    time.sleep(1)

    # Clicar selecionar
    wait.until(EC.element_to_be_clickable((By.ID, "d_btn_sel_ids_campanha"))).click()
    time.sleep(1)

def pegar_tma(driver, wait):
    """
    🔴 AQUI FOI CORRIGIDO
    Agora pega qualquer valor no formato 00:00:00 na tabela
    """

    time.sleep(2)

    elementos = driver.find_elements(By.XPATH, "//td[contains(text(),':')]")

    for el in elementos:
        texto = el.text.strip()

        # Verifica formato de tempo
        if texto.count(":") == 2 and len(texto) <= 8:
            return texto

    raise Exception("TMA não encontrado")

# ================= AUTOMAÇÃO =================

def executar():

    log("🚀 Iniciando automação")

    options = Options()
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    wait = WebDriverWait(driver, 60)

    try:
        # LOGIN
        log("🔐 Login")
        driver.get(URL_LOGIN)

        wait.until(EC.presence_of_element_located((By.ID, "l_login"))).send_keys(USUARIO)
        driver.find_element(By.ID, "l_senha").send_keys(SENHA)

        driver.execute_script("enviarDados();")
        wait.until(EC.url_contains("index.php"))

        log("✅ Logado")

        driver.get(URL_PAGINA)
        time.sleep(2)

        tmas = []

        # LOOP CAMPANHAS
        for campanha in CAMPANHAS:

            selecionar_campanha(driver, wait, campanha)

            # Buscar
            wait.until(EC.element_to_be_clickable((By.ID, "btn_pesquisar"))).click()
            time.sleep(3)

            try:
                tma = pegar_tma(driver, wait)
                log(f"⏱ TMA: {tma}")
                tmas.append(tempo_para_segundos(tma))
            except Exception as e:
                log(f"❌ Erro TMA: {e}")
                tmas.append(0)

            time.sleep(1)

        # MÉDIA
        media = sum(tmas) // len(tmas)
        media_formatada = segundos_para_tempo(media)

        print("\n" + "="*40)
        print(f"📈 MÉDIA TMA: {media_formatada}")
        print("="*40 + "\n")

    finally:
        driver.quit()

    input("Pressione ENTER para fechar...")


# EXECUTAR
if __name__ == "__main__":
    executar()