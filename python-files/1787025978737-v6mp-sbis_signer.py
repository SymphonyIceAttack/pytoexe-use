"""
СБИС Подпись — клиент для удалённого подписания
Проверяет сервер раз в минуту, подписывает через КриптоПро.
При первом запуске — выбор сертификата.
"""
import json
import subprocess
import time
import requests
from pathlib import Path
from tkinter import Tk, Label, Entry, Button, Listbox, messagebox, StringVar

APP_DIR = Path(__file__).parent
CERT_FILE = APP_DIR / "cert.txt"
KEY_FILE = APP_DIR / "key.txt"
SERVER_URL = "https://krut.space/api/signer"


def get_cert_list():
    """Получить список сертификатов из хранилища Windows"""
    result = subprocess.run(
        ['certutil', '-store', '-user', 'My'],
        capture_output=True, text=True
    )
    certs = []
    for line in result.stdout.split('\n'):
        if 'Серийный номер' in line or 'Serial Number' in line:
            certs.append(line.strip())
    return certs


def sign_hash(hash_hex):
    """Подписать хеш через КриптоПро"""
    cert_idx = int(CERT_FILE.read_text().strip()) if CERT_FILE.exists() else 0
    
    result = subprocess.run(
        ['cryptcp', '-signf', '-hash', 'sha256', '-base64', '-nochain', '-der',
         '-certnum', str(cert_idx), hash_hex],
        capture_output=True, text=True, timeout=30
    )
    
    sig = result.stdout
    if 'PKCS7' in sig:
        sig = sig.split('BEGIN PKCS7')[1].split('END PKCS7')[0].strip()
    return sig


def poll_server(key):
    """Проверить, есть ли работа"""
    try:
        resp = requests.post(f"{SERVER_URL}/poll", json={"key": key}, timeout=10)
        return resp.json()
    except Exception as e:
        print(f"Ошибка опроса: {e}")
        return {'has_work': False}


def submit_signature(key, request_id, signature):
    """Отправить подпись на сервер"""
    try:
        requests.post(f"{SERVER_URL}/submit", json={
            "key": key,
            "request_id": request_id,
            "signature": signature
        }, timeout=10)
        return True
    except Exception as e:
        print(f"Ошибка отправки: {e}")
        return False


def main_loop():
    """Основной цикл — опрос каждые 60 секунд"""
    key = KEY_FILE.read_text().strip()
    print(f"Сервис запущен. Опрос каждые 60 секунд.")
    
    while True:
        data = poll_server(key)
        
        if data.get('has_work'):
            print(f"Получен запрос {data['request_id']}")
            try:
                signature = sign_hash(data['hash'])
                if submit_signature(key, data['request_id'], signature):
                    print(f"Запрос {data['request_id']} подписан и отправлен")
                else:
                    print(f"Не удалось отправить подпись для {data['request_id']}")
            except Exception as e:
                print(f"Ошибка подписания: {e}")
        
        time.sleep(60)


def main_gui():
    """Окно первичной настройки"""
    root = Tk()
    root.title("СБИС Подпись — настройка")
    root.geometry("650x500")
    
    # API-ключ
    Label(root, text="API-ключ:", font=("Arial", 10)).pack(pady=5)
    key_var = StringVar(value=KEY_FILE.read_text().strip() if KEY_FILE.exists() else '')
    Entry(root, textvariable=key_var, font=("Arial", 10), width=50).pack(pady=5)
    
    # Сертификат
    Label(root, text="Выберите сертификат:", font=("Arial", 12)).pack(pady=10)
    
    certs = get_cert_list()
    if not certs:
        messagebox.showerror("Ошибка", "Сертификаты не найдены в хранилище Windows")
        root.destroy()
        return
    
    listbox = Listbox(root, width=90, height=15)
    listbox.pack(pady=10)
    for i, cert in enumerate(certs):
        listbox.insert('end', f"{i}: {cert}")
    
    def on_start():
        key = key_var.get().strip()
        if not key:
            messagebox.showerror("Ошибка", "Введите API-ключ")
            return
        
        idx = listbox.curselection()
        if not idx:
            messagebox.showerror("Ошибка", "Выберите сертификат")
            return
        
        KEY_FILE.write_text(key)
        CERT_FILE.write_text(str(idx[0]))
        
        root.destroy()
        main_loop()
    
    Button(root, text="Запустить", command=on_start, bg="green", fg="white", 
           font=("Arial", 14)).pack(pady=10)
    
    root.mainloop()


if __name__ == '__main__':
    if CERT_FILE.exists() and KEY_FILE.exists():
        # Уже настроено — запускаем сразу
        main_loop()
    else:
        # Первый запуск — показываем окно настройки
        main_gui()
