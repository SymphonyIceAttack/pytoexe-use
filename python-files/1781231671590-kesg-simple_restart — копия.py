#!/usr/bin/env python3
"""
Скрипт для удаленной перезагрузки simplem2m сервисов через SSH
с использованием встроенного SSH ключа
"""

import paramiko
import time
import sys
import os
from io import StringIO
from typing import Optional, List, Tuple

class SimpleM2MRestarter:
    # Встроенный SSH приватный ключ
    SSH_PRIVATE_KEY = """-----BEGIN OPENSSH PRIVATE KEY-----
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
-----END OPENSSH PRIVATE KEY-----"""
    
    def __init__(self, host: str = "176.222.18.86", port: int = 22224, username: str = "admin"):
        """
        Инициализация SSH клиента с встроенным ключом
        
        Args:
            host: IP адрес сервера (176.222.18.86)
            port: SSH порт (22224)
            username: Имя пользователя (admin)
        """
        self.host = host
        self.port = port
        self.username = username
        self.client = None
        self.bin_dir = "/usr/home/admin/simplem2m/bin"
        
    def print_status(self, message: str, status: str = "INFO"):
        """Вывод статусного сообщения с временной меткой"""
        timestamp = time.strftime("%H:%M:%S")
        status_colors = {
            "INFO": "\033[36m",     # Cyan
            "SUCCESS": "\033[32m",  # Green
            "WARNING": "\033[33m",  # Yellow
            "ERROR": "\033[31m",    # Red
            "STEP": "\033[34m",     # Blue
            "PHASE": "\033[35m",    # Magenta
            "START": "\033[1;36m",  # Bold Cyan
            "COMPLETE": "\033[1;32m" # Bold Green
        }
        reset = "\033[0m"
        
        color = status_colors.get(status, "\033[36m")
        print(f"{color}[{timestamp}] [{status}] {message}{reset}")
    
    def connect(self) -> bool:
        """Установка SSH соединения с использованием встроенного ключа"""
        self.print_status(f"Подключение к {self.host}:{self.port} как {self.username}...")
        
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Создаем ключ из строки
            key_file = StringIO(self.SSH_PRIVATE_KEY)
            private_key = paramiko.RSAKey.from_private_key(key_file)
            
            # Подключаемся с ключом
            self.client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                pkey=private_key,
                timeout=30,
                look_for_keys=False,
                allow_agent=False,
                banner_timeout=60
            )
            
            self.print_status("✓ SSH подключение установлено успешно", "SUCCESS")
            
            # Проверяем домашнюю директорию
            self._check_home_directory()
            return True
            
        except paramiko.AuthenticationException:
            self.print_status("✗ Ошибка аутентификации. SSH ключ не принят.", "ERROR")
        except paramiko.SSHException as e:
            self.print_status(f"✗ Ошибка SSH: {e}", "ERROR")
        except Exception as e:
            self.print_status(f"✗ Ошибка подключения: {e}", "ERROR")
        
        return False
    
    def _check_home_directory(self):
        """Проверка домашней директории и пути к бинарникам"""
        self.print_status("Проверка домашней директории...")
        success, stdout, stderr = self._execute_simple_command("pwd")
        if success:
            self.print_status(f"Текущая директория: {stdout}")
        
        # Проверяем существование директории с бинарниками
        success, stdout, stderr = self._execute_simple_command(f"ls -la {self.bin_dir}")
        if success:
            self.print_status(f"Директория с бинарниками найдена: {self.bin_dir}", "SUCCESS")
        else:
            self.print_status(f"Директория {self.bin_dir} не найдена. Пробуем домашнюю директорию...", "WARNING")
            # Пробуем найти через домашнюю директорию
            success, stdout, stderr = self._execute_simple_command("cd && pwd")
            if success:
                home_dir = stdout.strip()
                self.bin_dir = f"{home_dir}/simplem2m/bin"
                self.print_status(f"Используем домашнюю директорию: {home_dir}", "INFO")
    
    def _execute_simple_command(self, command: str) -> Tuple[bool, str, str]:
        """Простое выполнение команды без дополнительного вывода"""
        try:
            stdin, stdout, stderr = self.client.exec_command(command, get_pty=True)
            exit_status = stdout.channel.recv_exit_status()
            stdout_text = stdout.read().decode('utf-8').strip()
            stderr_text = stderr.read().decode('utf-8').strip()
            return exit_status == 0, stdout_text, stderr_text
        except Exception:
            return False, "", ""
    
    def execute_command(self, command: str, description: str = "", show_output: bool = True) -> Tuple[bool, str, str]:
        """
        Выполнение команды на удаленном сервере
        
        Returns:
            (success, stdout, stderr)
        """
        if description:
            self.print_status(description)
        
        try:
            # Используем pty для корректной работы с интерактивными командами
            stdin, stdout, stderr = self.client.exec_command(command, get_pty=True)
            
            # Ждем завершения команды
            exit_status = stdout.channel.recv_exit_status()
            
            # Читаем вывод
            stdout_text = stdout.read().decode('utf-8').strip()
            stderr_text = stderr.read().decode('utf-8').strip()
            
            success = exit_status == 0
            
            if show_output:
                if stdout_text:
                    for line in stdout_text.split('\n'):
                        if line.strip():
                            print(f"    {line}")
                if stderr_text and not success:
                    for line in stderr_text.split('\n'):
                        if line.strip():
                            print(f"    \033[33m{line}\033[0m")
            
            return success, stdout_text, stderr_text
            
        except Exception as e:
            self.print_status(f"✗ Ошибка выполнения команды '{command}': {e}", "ERROR")
            return False, "", str(e)
    
    def check_processes(self, show_details: bool = True) -> List[Tuple[str, str]]:
        """Проверка запущенных процессов simplem2m"""
        self.print_status("Проверка запущенных процессов simplem2m...")
        
        success, stdout, stderr = self.execute_command(
            "ps aux | grep -E 'connsvr|connwrk[0-9]' | grep -v grep",
            "Поиск процессов simplem2m",
            show_output=show_details
        )
        
        processes = []
        if success and stdout:
            lines = stdout.split('\n')
            self.print_status(f"Найдено {len(lines)} процессов simplem2m", "INFO")
            
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) > 1:
                        pid = parts[1]
                        # Берем команду (обычно последний элемент или часть строки после 10-го элемента)
                        cmd_parts = line.split()
                        if len(cmd_parts) > 10:
                            command = ' '.join(cmd_parts[10:])
                        else:
                            command = cmd_parts[-1]
                        processes.append((pid, command))
                        
        return processes
    
    def kill_processes(self):
        """Завершение всех процессов simplem2m"""
        self.print_status("Завершение процессов simplem2m...", "STEP")
        
        # Получаем текущие процессы
        processes = self.check_processes(show_details=False)
        if not processes:
            self.print_status("Нет процессов simplem2m для завершения", "INFO")
            return
        
        self.print_status(f"Найдено {len(processes)} процессов для завершения", "INFO")
        
        # Сначала пробуем мягко завершить все процессы
        for pid, command in processes:
            self.print_status(f"Завершение '{command}' (PID: {pid})...")
            
            # Сначала мягкий сигнал
            success, stdout, stderr = self.execute_command(f"kill {pid}", show_output=False)
            if success:
                self.print_status(f"  ✓ Сигнал TERM отправлен PID {pid}", "SUCCESS")
            else:
                self.print_status(f"  ✗ Не удалось отправить TERM PID {pid}", "WARNING")
        
        # Даем время на завершение
        time.sleep(3)
        
        # Проверяем остались ли процессы и убиваем принудительно
        remaining = self.check_processes(show_details=False)
        if remaining:
            self.print_status(f"Осталось {len(remaining)} процессов. Принудительное завершение...", "WARNING")
            
            for pid, command in remaining:
                self.execute_command(f"kill -9 {pid}", show_output=False)
                self.print_status(f"  ⚡ SIGKILL отправлен PID {pid}", "WARNING")
            
            time.sleep(2)
        
        # Финальная проверка
        final_check = self.check_processes(show_details=False)
        if not final_check:
            self.print_status("✓ Все процессы simplem2m завершены", "SUCCESS")
        else:
            self.print_status(f"⚠ Осталось {len(final_check)} процессов после завершения", "WARNING")
            # Последняя попытка - используем pkill
            self.execute_command("pkill -9 -f 'connsvr|connwrk'", show_output=False)
            time.sleep(1)
    
    def cleanup_pid_files(self):
        """Очистка PID файлов"""
        self.print_status("Очистка PID файлов...", "STEP")
        
        pid_files = ['connsvr.pid', 'connwrk1.pid', 'connwrk2.pid']
        
        for pid_file in pid_files:
            # Используем более надежную проверку существования файла
            success, stdout, stderr = self.execute_command(
                f"cd {self.bin_dir} && test -f {pid_file} && echo 'EXISTS' || echo 'NOT_EXISTS'",
                f"Проверка существования файла {pid_file}",
                show_output=False
            )
            
            if success and "EXISTS" in stdout:
                # Удаляем файл
                success, stdout, stderr = self.execute_command(
                    f"cd {self.bin_dir} && rm -f {pid_file} && echo 'REMOVED' || echo 'FAILED'",
                    f"Удаление файла {pid_file}"
                )
                
                if success and "REMOVED" in stdout:
                    self.print_status(f"  ✓ Файл {pid_file} удален", "SUCCESS")
                else:
                    self.print_status(f"  ✗ Не удалось удалить файл {pid_file}", "ERROR")
                    # Пробуем с принудительным удалением
                    self.execute_command(f"cd {self.bin_dir} && rm -fv {pid_file}", show_output=False)
            else:
                self.print_status(f"  ⏭ Файл {pid_file} не существует", "INFO")
        
        # Дополнительная проверка - просмотр всех файлов в директории
        self.print_status("Проверка содержимого директории...", "INFO")
        self.execute_command(f"cd {self.bin_dir} && ls -la *.pid 2>/dev/null || echo 'No PID files found'",
                           "Список PID файлов в директории")
    
    def start_services(self):
        """Запуск сервисов"""
        self.print_status("Запуск сервисов...", "STEP")
        
        services = [
            ("connsvr", "./connsvr"),
            ("connwrk1", "./connwrk1"), 
            ("connwrk2", "./connwrk2")
        ]
        
        for name, command in services:
            self.print_status(f"Запуск {name}...")
            
            # Проверяем существование исполняемого файла
            success, stdout, stderr = self.execute_command(
                f"cd {self.bin_dir} && ls -la {name}",
                f"Поиск исполняемого файла {name}",
                show_output=False
            )
            
            if not success:
                self.print_status(f"  ✗ Исполняемый файл {name} не найден", "ERROR")
                continue
            
            # Запускаем сервис - исправленная команда для FreeBSD
            # Вместо nohup используем disown или запуск в фоне
            start_command = f"cd {self.bin_dir} && ./{name} > /dev/null 2>&1 &"
            success, stdout, stderr = self.execute_command(
                start_command,
                f"Запуск {name}: {start_command}"
            )
            
            if success:
                self.print_status(f"  ✓ Команда запуска {name} выполнена", "SUCCESS")
                # Проверяем, что процесс запустился
                time.sleep(1)
                check_success, check_stdout, check_stderr = self.execute_command(
                    f"ps aux | grep {name} | grep -v grep",
                    f"Проверка запуска {name}",
                    show_output=False
                )
                if check_success and check_stdout:
                    self.print_status(f"  ✓ {name} успешно запущен", "SUCCESS")
                else:
                    self.print_status(f"  ⚠ {name} возможно не запустился", "WARNING")
            else:
                self.print_status(f"  ✗ Ошибка запуска {name}", "ERROR")
                if stderr:
                    print(f"    \033[33mОшибка: {stderr}\033[0m")
                # Альтернативный способ запуска
                self.print_status(f"  Попытка альтернативного запуска {name}...", "INFO")
                alt_command = f"cd {self.bin_dir} && ./{name} &"
                self.execute_command(alt_command, f"Альтернативный запуск: {alt_command}")
            
            # Пауза между запусками
            time.sleep(2)
    
    def verify_restart(self):
        """Проверка успешности перезагрузки"""
        self.print_status("Проверка состояния сервисов...", "STEP")
        
        # Ждем для стабилизации
        time.sleep(5)
        
        processes = self.check_processes(show_details=True)
        
        if len(processes) >= 3:
            self.print_status(f"✓ Все сервисы запущены ({len(processes)} процессов)", "SUCCESS")
            
            # Выводим детальную информацию
            self.print_status("Детальная информация о процессах:", "INFO")
            for pid, command in processes:
                # Получаем дополнительную информацию о процессе
                success, stdout, stderr = self.execute_command(
                    f"ps -p {pid} -o pid,user,%cpu,%mem,vsz,rss,start,time,cmd 2>/dev/null || ps -p {pid} -o pid,user,pcpu,pmem,vsz,rss,start,time,comm",
                    show_output=False
                )
                if success and stdout:
                    print(f"    {stdout}")
                    
        elif len(processes) > 0:
            self.print_status(f"⚠ Запущено только {len(processes)} из 3 процессов", "WARNING")
        else:
            self.print_status("✗ Ни один сервис не запущен!", "ERROR")
    
    def disconnect(self):
        """Закрытие SSH соединения"""
        if self.client:
            self.client.close()
            self.print_status("Соединение закрыто", "INFO")
    
    def restart_services(self) -> bool:
        """Основной метод перезагрузки сервисов"""
        self.print_status("=" * 60, "START")
        self.print_status(f"ПЕРЕЗАГРУЗКА SIMPLEM2M НА {self.host}:{self.port}", "START")
        self.print_status("=" * 60, "START")
        
        try:
            # Подключаемся
            if not self.connect():
                return False
            
            steps = [
                ("Проверка текущих процессов", self.check_processes),
                ("Завершение процессов", self.kill_processes),
                ("Очистка PID файлов", self.cleanup_pid_files),
                ("Запуск сервисов", self.start_services),
                ("Проверка результата", self.verify_restart),
            ]
            
            for i, (description, method) in enumerate(steps, 1):
                self.print_status(f"\n[{i}/{len(steps)}] {description}", "PHASE")
                method()
                time.sleep(1)
            
            self.print_status("\n" + "=" * 60, "COMPLETE")
            self.print_status("ПЕРЕЗАГРУЗКА ЗАВЕРШЕНА", "COMPLETE")
            self.print_status("=" * 60, "COMPLETE")
            
            return True
            
        except Exception as e:
            self.print_status(f"✗ Критическая ошибка: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.disconnect()

def main():
    """Точка входа в программу"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Перезагрузка simplem2m сервисов через SSH с встроенным ключом',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s                         # Использование настроек по умолчанию
  %(prog)s --host 10.0.0.1         # Указание другого хоста
  %(prog)s --port 22              # Использование стандартного порта SSH
  %(prog)s --user root            # Использование пользователя root
        """
    )
    
    parser.add_argument('--host', default='176.222.18.86', help='IP адрес сервера (по умолчанию: 176.222.18.86)')
    parser.add_argument('--port', type=int, default=22224, help='SSH порт (по умолчанию: 22224)')
    parser.add_argument('--user', default='admin', help='Имя пользователя (по умолчанию: admin)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Подробный вывод')
    parser.add_argument('--bin-dir', help='Путь к директории с бинарниками (по умолчанию: /usr/home/admin/simplem2m/bin)')
    
    args = parser.parse_args()
    
    # Выводим информацию о подключении
    print("\033[1;36m" + "=" * 60 + "\033[0m")
    print("\033[1;36m" + "СКРИПТ ПЕРЕЗАГРУЗКИ SIMPLEM2M С ВСТРОЕННЫМ SSH КЛЮЧОМ" + "\033[0m")
    print("\033[1;36m" + "=" * 60 + "\033[0m")
    print(f"Сервер: {args.user}@{args.host}:{args.port}")
    print(f"Время: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Создаем и запускаем рестартер
    restarter = SimpleM2MRestarter(
        host=args.host,
        port=args.port,
        username=args.user
    )
    
    # Устанавливаем путь к бинарникам если указан
    if args.bin_dir:
        restarter.bin_dir = args.bin_dir
    
    # Запускаем перезагрузку
    success = restarter.restart_services()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    # Проверяем наличие необходимых библиотек
    try:
        import paramiko
    except ImportError:
        print("\033[31mОшибка: Не найдена библиотека paramiko.\033[0m")
        print("Установите её с помощью: pip install paramiko")
        sys.exit(1)
    
    main()
