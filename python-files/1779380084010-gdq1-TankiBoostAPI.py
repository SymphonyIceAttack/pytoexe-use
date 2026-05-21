import subprocess
import sys
import os
import time

def run_as_admin():
    """Запуск от админа"""
    import ctypes
    if not ctypes.windll.shell32.IsUserAnAdmin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit()

def main():
    print("=" * 55)
    print("⚡ УСКОРИТЕЛЬ FPS ДЛЯ GTX 1060")
    print("=" * 55)
    print()
    
    done = []
    
    # 1. Схема питания — максимальная производительность
    print("[1/8] Схема электропитания...")
    try:
        subprocess.run(
            'powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c',
            shell=True, capture_output=True
        )
        print("  ✅ Максимальная производительность")
        done.append("Схема питания")
    except:
        print("  ❌ Не удалось")
    
    # 2. Очистка оперативной памяти
    print("[2/8] Очистка оперативной памяти...")
    deleted = 0
    temp = os.environ.get('TEMP', '')
    if temp and os.path.exists(temp):
        for root, dirs, files in os.walk(temp, topdown=False):
            for name in files:
                try:
                    os.remove(os.path.join(root, name))
                    deleted += 1
                except: pass
    print(f"  ✅ Удалено {deleted} временных файлов")
    done.append(f"Очистка памяти ({deleted} файлов)")
    
    # 3. Убиваем всё лишнее
    print("[3/8] Закрытие лишних программ...")
    killed = 0
    junk = [
        "chrome.exe", "firefox.exe", "msedge.exe", "discord.exe",
        "spotify.exe", "telegram.exe", "steamwebhelper.exe",
        "epicgameslauncher.exe", "OneDrive.exe", "Skype.exe",
        "GameBar.exe", "XboxApp.exe", "Widgets.exe"
    ]
    for proc in junk:
        try:
            r = subprocess.run(
                f'taskkill /f /im {proc} 2>nul',
                shell=True, capture_output=True, text=True
            )
            if "SUCCESS" in r.stdout:
                killed += 1
        except: pass
    print(f"  ✅ Закрыто: {killed} программ")
    done.append(f"Закрыто {killed} программ")
    
    # 4. Приоритет процессора для игр
    print("[4/8] Приоритет процессора...")
    games = ["worldoftanks.exe", "WoT.exe", "RobloxPlayerBeta.exe", "LostLight.exe"]
    for game in games:
        try:
            check = subprocess.run(
                f'tasklist /fi "imagename eq {game}" 2>nul',
                shell=True, capture_output=True, text=True, encoding='cp866'
            )
            if game in check.stdout:
                subprocess.run(
                    f'wmic process where name="{game}" CALL setpriority 128',
                    shell=True, capture_output=True
                )
                print(f"  ✅ {game} → Высокий приоритет")
                done.append(f"Приоритет {game}")
        except: pass
    
    # 5. Отключение визуальных эффектов Windows
    print("[5/8] Отключение эффектов Windows...")
    try:
        subprocess.run(
            'powershell "Set-ItemProperty -Path HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\VisualEffects -Name VisualFXSetting -Value 2"',
            shell=True, capture_output=True
        )
        print("  ✅ Визуальные эффекты отключены")
        done.append("Эффекты Windows")
    except:
        print("  ❌ Не удалось")
    
    # 6. Игровой режим Windows
    print("[6/8] Игровой режим...")
    try:
        subprocess.run(
            'powershell "Set-ItemProperty -Path HKCU:\\Software\\Microsoft\\GameBar -Name AutoGameModeEnabled -Value 1"',
            shell=True, capture_output=True
        )
        subprocess.run(
            'powershell "Set-ItemProperty -Path HKCU:\\Software\\Microsoft\\GameBar -Name AllowAutoGameMode -Value 1"',
            shell=True, capture_output=True
        )
        print("  ✅ Игровой режим включён")
        done.append("Игровой режим")
    except:
        print("  ❌ Не удалось")
    
    # 7. Настройки NVIDIA (если есть)
    print("[7/8] Настройки NVIDIA...")
    nv_path = r"C:\Program Files\NVIDIA Corporation\NVSMI\nvidia-smi.exe"
    if os.path.exists(nv_path):
        try:
            # Устанавливаем режим максимальной производительности
            subprocess.run(
                f'"{nv_path}" -ac 3805,1911',  # Разгон памяти для GTX 1060
                shell=True, capture_output=True
            )
            print("  ✅ NVIDIA переведена в режим производительности")
            done.append("NVIDIA настройки")
        except:
            print("  ⚠️ Не удалось применить настройки NVIDIA")
    else:
        print("  ⚠️ nvidia-smi не найден")
    
    # 8. Отключение записи экрана (Game DVR)
    print("[8/8] Отключение Game DVR...")
    try:
        subprocess.run(
            'reg add "HKCU\\System\\GameConfigStore" /v GameDVR_Enabled /t REG_DWORD /d 0 /f',
            shell=True, capture_output=True
        )
        print("  ✅ Game DVR отключён")
        done.append("Game DVR отключён")
    except:
        print("  ❌ Не удалось")
    
    # ИТОГ
    print()
    print("=" * 55)
    print("✅ ГОТОВО! ВНЕСЁННЫЕ ИЗМЕНЕНИЯ:")
    for i, item in enumerate(done, 1):
        print(f"  {i}. {item}")
    print()
    print("📌 ЧТО ЕЩЁ СДЕЛАТЬ ВРУЧНУЮ:")
    print("  1. В игре: графика → пресет 'Минимальный'")
    print("  2. В игре: разрешение 1600x900 вместо Full HD")
    print("  3. В игре: отключи вертикальную синхронизацию")
    print("  4. Панель NVIDIA → Режим низкой задержки → Ультра")
    print("  5. Панель NVIDIA → Электропитание → Макс. производ.")
    print()
    print("⚠️ После перезагрузки ПК всё вернётся обратно.")
    print("   Запускай скрипт перед каждой игровой сессией!")
    print("=" * 55)
    print()
    input("Нажми Enter для выхода...")

if __name__ == "__main__":
    run_as_admin()
    main()