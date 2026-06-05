import os
import sys
import subprocess
import datetime

print("=" * 60)
print("АНТИВИРУСНЫЙ ПОМОЩНИК - ДИАГНОСТИКА")
print("=" * 60)
print("\nЭтот скрипт проверит подозрительные места в системе")
print("и создаст отчёт. Он НЕ удаляет файлы автоматически.\n")

# Создаём файл отчёта
report_filename = f"antivirus_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

def write_report(text):
    with open(report_filename, "a", encoding="utf-8") as f:
        f.write(text + "\n")
    print(text)

write_report("=" * 60)
write_report("ОТЧЁТ О ДИАГНОСТИКЕ СИСТЕМЫ")
write_report(f"Дата: {datetime.datetime.now()}")
write_report("=" * 60)

# 1. Проверка автозагрузки
write_report("\n[1] ПОДОЗРИТЕЛЬНАЯ АВТОЗАГРУЗКА:")
autostart_paths = [
    os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"),
    os.path.expandvars(r"%USERPROFILE%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup"),
]

for path in autostart_paths:
    if os.path.exists(path):
        files = os.listdir(path)
        suspicious = [f for f in files if f.endswith(('.exe', '.bat', '.vbs', '.ps1', '.cmd'))]
        for s in suspicious:
            write_report(f"  - {path}\\{s}")

# 2. Проверка временных папок
write_report("\n[2] ПРОВЕРКА ВРЕМЕННЫХ ПАПОК:")
temp_paths = [
    os.environ.get("TEMP", ""),
    os.environ.get("TMP", ""),
    r"C:\Windows\Temp",
]

for path in temp_paths:
    if path and os.path.exists(path):
        try:
            exe_files = [f for f in os.listdir(path) if f.endswith('.exe')]
            if exe_files:
                write_report(f"  В {path}: {', '.join(exe_files[:5])}")
        except:
            pass

# 3. Проверка процессов
write_report("\n[3] ЗАПУЩЕННЫЕ ПРОЦЕССЫ (подозрительные):")
suspicious_names = ['miner', 'crypto', 'bitcoin', 'eth', 'xmrig', 'kworker', 'svchost_fake']
try:
    result = subprocess.run(['tasklist'], capture_output=True, text=True, encoding='cp866')
    for line in result.stdout.split('\n'):
        for susp in suspicious_names:
            if susp.lower() in line.lower():
                write_report(f"  {line.strip()}")
except:
    write_report("  Не удалось получить список процессов")

# 4. Проверка hosts файла
write_report("\n[4] ПРОВЕРКА HOSTS ФАЙЛА:")
hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
if os.path.exists(hosts_path):
    try:
        with open(hosts_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if '127.0.0.1' in content and not content.count('#') > 20:
                suspicious_lines = [l.strip() for l in content.split('\n') if '127.0.0.1' in l and 'localhost' not in l.lower()]
                if suspicious_lines:
                    write_report("  Подозрительные записи:")
                    for line in suspicious_lines[:10]:
                        write_report(f"    {line}")
    except:
        write_report("  Не удалось прочитать hosts")

# 5. Заключение
write_report("\n" + "=" * 60)
write_report("ЧТО ДЕЛАТЬ ДАЛЬШЕ:")
write_report("=" * 60)
write_report("1. Скачай и установи: Kaspersky Virus Removal Tool (бесплатно)")
write_report("2. Скачай и установи: Malwarebytes Anti-Malware (бесплатная версия)")
write_report("3. Запусти полное сканирование в безопасном режиме")
write_report("4. После удаления вируса - переустанови DirectX и драйверы видеокарты")
write_report("5. Проверь целостность системных файлов: sfc /scannow")

print("\n" + "=" * 60)
print(f"✅ Отчёт сохранён: {report_filename}")
print("=" * 60)
print("\n📌 Отправь этот файл другу или посмотри его содержимое.")
print("📌 Это НЕ вирус и НЕ удаляет файлы - только диагностика.")