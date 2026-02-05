import subprocess
import sys
import getpass

def run_command():
    # Формируем команду
    command = (
        'runas /user:6671_svc_installsoft /savecred '
        '"\\\\66027-app006\\Install\\AIS_NALOG_3\\ekp\\addons.cmd"'
    )
    
    try:
        # Запускаем команду
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            # Добавляем stdin для возможного ввода пароля
            input=''  # Пароль должен вводиться в отдельном окне runas
        )
        
        if result.stdout:
            print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode
        
    except Exception as e:
        print(f"Ошибка при выполнении команды: {e}")
        return 1

if __name__ == "__main__":
    print("Запуск с повышенными привилегиями...")
    exit_code = run_command()
    
    if exit_code == 0:
        print("Команда успешно выполнена!")
    else:
        print(f"Команда завершилась с кодом ошибки: {exit_code}")
    
    sys.exit(exit_code)