import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

CLIENT_PATH = Path(r"C:\WoT_Polygon\client\World_of_Tanks")
EXE_NAME = "WorldOfTanks.exe"
VERSION = "0.8.2"
RES_MODS_PATH = CLIENT_PATH / "res_mods" / VERSION
CONFIG_PATH = CLIENT_PATH / "res" / "scripts_config.xml"
MY_MODS_PATH = Path(r"C:\WoT_Polygon\sources")

def backup_config(config_path):
    backup = config_path.with_suffix(".xml.bak")
    if not backup.exists():
        shutil.copy2(config_path, backup)
        print(f"��������� �����: {backup}")

def enable_training_room(config_path):
    try:
        tree = ET.parse(config_path)
        root = tree.getroot()
        changed = False

        elem = root.find(".//disableTrainingRoom")
        if elem is not None:
            if elem.text == "true":
                elem.text = "false"
                changed = True
                print("������������� ������� �������.")
        else:
            elem = root.find(".//trainingRoomEnabled")
            if elem is not None:
                if elem.text == "false":
                    elem.text = "true"
                    changed = True
                    print("������������� ������� �������.")
            else:
                print("��� ��� ��������� �������� �� ������.")

        if changed:
            tree.write(config_path, encoding="utf-8", xml_declaration=True)
    except Exception as e:
        print(f"������ ��������� �������: {e}")

def copy_mods(source, destination):
    if not source.exists():
        print(f"����� {source} �� �������.")
        return
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)
    print("���� �����������.")

def launch_game():
    exe_path = CLIENT_PATH / EXE_NAME
    if not exe_path.exists():
        print(f"���� {exe_path} �� ������.")
        return False
    try:
        subprocess.Popen([str(exe_path)], cwd=str(CLIENT_PATH))
        print("���� ��������.")
        return True
    except Exception as e:
        print(f"������ �������: {e}")
        return False

def restore_backup(config_path):
    backup = config_path.with_suffix(".xml.bak")
    if backup.exists():
        shutil.copy2(backup, config_path)
        print("������ ������������.")
    else:
        print("��������� ����� �� �������.")

def show_menu():
    print("\n" + "=" * 50)
    print("          ������� ������� �������� (0.8.2)")
    print("=" * 50)
    print("1. ��������� �������")
    print("2. ��������� ������ ������")
    print("3. ������������ ������")
    print("4. �����")
    print("=" * 50)

def main():
    while True:
        show_menu()
        choice = input("�������� ��������: ").strip()
        if choice == "1":
            if CONFIG_PATH.exists():
                backup_config(CONFIG_PATH)
                enable_training_room(CONFIG_PATH)
            copy_mods(MY_MODS_PATH, RES_MODS_PATH)
            launch_game()
        elif choice == "2":
            launch_game()
        elif choice == "3":
            restore_backup(CONFIG_PATH)
        elif choice == "4":
            print("�����.")
            break
        else:
            print("�������� �����.")

if name == "main":
    main()