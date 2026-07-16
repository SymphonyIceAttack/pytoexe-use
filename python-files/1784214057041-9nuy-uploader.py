import os
import sys
import subprocess
import requests

# ===================== НАСТРОЙКИ ПОЛЬЗОВАТЕЛЯ =====================
API_TOKEN = "ВАШ_ТОКЕН_АРШИНА_ИЗ_ЛИЧНОГО_КАБИНЕТА"
# Серийный номер или отпечаток (Thumbprint) сертификата ЭЦП в КриптоПро
CERT_THUMBPRINT = "ХЭШ_ИЛИ_СЕРИЙНЫЙ_НОМЕР_СЕРТИФИКАТА" 
# Стандартный путь к утилите csptest от КриптоПро CSP
CSPTEST_PATH = r"C:\Program Files\Crypto Pro\CSP\csptest.exe"
# Официальный адрес API ФГИС Аршин для пакетной загрузки (v2)
ARSHIN_API_URL = "https://gost.ru"
# ==================================================================

def sign_file(file_path):
    """Создает отсоединенную подпись файла формата PKCS#7 / CMS через КриптоПро"""
    sig_path = file_path + ".sig"
    
    # Команда создания отсоединенной подписи ЭЦП
    cmd = [
        CSPTEST_PATH, "-sftp", 
        "-sign", "-detached", 
        "-in", file_path, 
        "-out", sig_path, 
        "-cert", CERT_THUMBPRINT
    ]
    
    try:
        # Выполняем команду скрыто, перехватывая вывод
        result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if os.path.exists(sig_path):
            print(f"[OK] Подпись успешно создана: {os.path.basename(sig_path)}")
            return sig_path
        else:
            print("[ERROR] Не удалось сгенерировать файл подписи.")
            sys.exit(1)
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode('cp866', errors='ignore')
        print(f"[ERROR] Ошибка КриптоПро CSP:\n{error_msg}")
        sys.exit(1)

def upload_to_arshin(file_path, sig_path):
    """Отправляет пару Файл + Подпись во ФГИС Аршин"""
    headers = {
        "Authorization": f"Bearer {API_TOKEN}"
    }
    
    # Готовим multipart/form-data вложение (XML файл и отсоединенная подпись)
    with open(file_path, "rb") as f_data, open(sig_path, "rb") as f_sig:
        files = {
            "file": (os.path.basename(file_path), f_data, "application/xml"),
            "sign": (os.path.basename(sig_path), f_sig, "application/octet-stream")
        }
        
        try:
            print("[INFO] Отправка пакета данных в Аршин...")
            response = requests.post(ARSHIN_API_URL, headers=headers, files=files)
            
            if response.status_code in:
                print(f"[SUCCESS] Пакет успешно доставлен!\nОтвет сервера: {response.text}")
            else:
                print(f"[ERROR] Сервер Аршина вернул ошибку {response.status_code}:\n{response.text}")
                sys.exit(1)
        except Exception as e:
            print(f"[ERROR] Ошибка сети при попытке связаться с Аршином: {e}")
            sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: uploader.py <полный_путь_к_xml>")
        sys.exit(1)
        
    target_file = sys.argv[1]
    if not os.path.exists(target_file):
        print(f"[ERROR] Целевой XML-файл не найден по пути: {target_file}")
        sys.exit(1)
        
    print(f"[INFO] Обработка файла: {os.path.basename(target_file)}")
    signature_file = sign_file(target_file)
    upload_to_arshin(target_file, signature_file)
