import subprocess
import sys

def run_as_with_savecred():
    # Команда runas с сохранением учетных данных
    command = [
        'runas',
        '/user:6671_svc_installsoft',
        '/savecred',
        r'"\\66027-app006\Install\AIS_NALOG_3\ekp\addons.cmd"'
    ]
    
    try:
        print(f"Выполняем команду: {' '.join(command)}")
        print("При первом запуске введите пароль для пользователя 6671_svc_installsoft")
        print("Пароль будет сохранен для последующих запусков (/savecred)")
        
        # Запускаем команду
        result = subprocess.run(command, 
                               shell=True,  # Важно для корректной работы с runas
                               capture_output=True,
                               text=True,
                               encoding='cp866')  # Кодировка для русской Windows
        
        # Выводим результат
        if result.stdout:
            print("Вывод команды:", result.stdout)
        if result.stderr:
            print("Ошибки:", result.stderr)
        print("Код завершения:", result.returncode)
        
    except Exception as e:
        print(f"Ошибка при выполнении команды: {e}")

# Запускаем функцию
if __name__ == "__main__":
    run_as_with_savecred()