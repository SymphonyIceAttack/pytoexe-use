import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

if os.name != "nt":
    print("этот скрипт рассчитан на windows.")
    sys.exit(1)

try:
    import winreg
except Exception:
    winreg = None

import ctypes
from ctypes import wintypes


menu_template = (
    "выбери действие:\n"
    "1) открыть файл заставки cs2\n"
    "2) восстановить из бэкапа\n"
    "3) туториал\n"
    "4) выход\n\n"
    "бэкап: {status}"
)

tutorial_text = (
    "тутор:\n\n"
    "1) пункт 1 открывает папку с интро-файлами и создаёт бэкап\n"
    "2) в папке ищи: intro и intro720p (оч редко intro720)\n"
    "3) сделай своё видео и на любом сайте конвертируй его из mp4 в webm\n"
    "4) замени файлы intro и intro720p на свои (важно: название оставь таким же \"intro\" и \"intro720p\")\n"
    "5) готово, наслаждайся"
)

folderid_downloads = "{374de290-123f-4565-9164-39c4925e467b}"


def clear_screen():
    os.system("cls")


def pause_to_menu():
    print()
    print("нажмите enter чтобы вернуться в меню")
    input()


def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def _quote_arg(arg):
    arg = str(arg)
    if not arg:
        return '""'
    if any(ch in arg for ch in (" ", "\t", '"')):
        return '"' + arg.replace('"', '\\"') + '"'
    return arg


def relaunch_as_admin(extra_args):
    exe = None
    params = ""

    argv0 = Path(sys.argv[0]).resolve()
    base_args = [a for a in sys.argv[1:] if not a.startswith("--auto_action=")]
    full_args = base_args + list(extra_args)

    if argv0.suffix.lower() in (".py", ".pyw"):
        exe = sys.executable
        params = " ".join([_quote_arg(str(argv0))] + [_quote_arg(a) for a in full_args])
    else:
        exe = str(argv0)
        params = " ".join([_quote_arg(a) for a in full_args])

    try:
        rc = ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, params, None, 1)
        return rc > 32
    except Exception:
        return False


def ensure_admin_for_restore():
    if is_admin():
        return True

    if any(a.startswith("--auto_action=restore") for a in sys.argv[1:]):
        print("нужны права администратора. восстановление отменено.")
        return False

    print("нужны права администратора. запрашиваю...")
    ok = relaunch_as_admin(["--auto_action=restore"])
    if not ok:
        print("не удалось запросить права администратора.")
        return False

    sys.exit(0)


class guid(ctypes.Structure):
    _fields_ = [
        ("data1", wintypes.DWORD),
        ("data2", wintypes.WORD),
        ("data3", wintypes.WORD),
        ("data4", wintypes.BYTE * 8),
    ]


def _guid_from_string(guid_string):
    import uuid

    u = uuid.UUID(guid_string.strip("{}"))
    data4 = (wintypes.BYTE * 8).from_buffer_copy(u.bytes[8:])
    return guid(u.fields[0], u.fields[1], u.fields[2], data4)


def get_downloads_dir():
    try:
        shell32 = ctypes.windll.shell32
        ole32 = ctypes.windll.ole32

        fid = _guid_from_string(folderid_downloads)
        p_path = ctypes.c_wchar_p()

        hr = shell32.SHGetKnownFolderPath(ctypes.byref(fid), 0, 0, ctypes.byref(p_path))
        if hr != 0:
            raise OSError(hr)

        try:
            path = Path(p_path.value)
        finally:
            ole32.CoTaskMemFree(p_path)

        if path.exists():
            return path
    except Exception:
        pass

    return Path.home() / "downloads"


def read_reg_str(root, subkey, name):
    if winreg is None:
        return None
    try:
        with winreg.OpenKey(root, subkey) as k:
            val, _vtype = winreg.QueryValueEx(k, name)
            if isinstance(val, str) and val.strip():
                return val
    except Exception:
        return None
    return None


def get_steam_install_path():
    candidates = []

    sp = read_reg_str(winreg.HKEY_CURRENT_USER, r"software\valve\steam", "steampath") if winreg else None
    if sp:
        candidates.append(sp)

    ip = read_reg_str(winreg.HKEY_LOCAL_MACHINE, r"software\wow6432node\valve\steam", "installpath") if winreg else None
    if ip:
        candidates.append(ip)

    candidates.extend([
        r"c:\program files (x86)\steam",
        r"c:\program files\steam",
    ])

    for p in candidates:
        p2 = str(p).replace("/", "\\")
        pp = Path(p2)
        if (pp / "steam.exe").exists():
            return pp
    return None


def _unescape_vdf_path(s):
    return s.replace("\\\\", "\\")


def parse_libraryfolders_vdf(vdf_path):
    try:
        text = vdf_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []

    paths = []

    for m in re.finditer(r'"path"\s*"([^"]+)"', text, flags=re.IGNORECASE):
        paths.append(Path(_unescape_vdf_path(m.group(1))))

    if not paths:
        for m in re.finditer(r'^\s*"\d+"\s*"([^"]+)"\s*$', text, flags=re.MULTILINE):
            val = m.group(1)
            if ":\\" in val or val.startswith("\\\\"):
                paths.append(Path(_unescape_vdf_path(val)))

    uniq = []
    seen = set()
    for p in paths:
        try:
            rp = p.resolve()
        except Exception:
            rp = p
        key = str(rp).lower()
        if key not in seen and p.exists():
            seen.add(key)
            uniq.append(p)
    return uniq


def get_steam_library_paths():
    libs = []
    steam = get_steam_install_path()
    if steam and steam.exists():
        libs.append(steam)

        vdf1 = steam / "steamapps" / "libraryfolders.vdf"
        vdf2 = steam / "config" / "libraryfolders.vdf"

        for vdf in (vdf1, vdf2):
            if vdf.exists():
                libs.extend(parse_libraryfolders_vdf(vdf))

    uniq = []
    seen = set()
    for p in libs:
        try:
            rp = p.resolve()
        except Exception:
            rp = p
        key = str(rp).lower()
        if key not in seen and p.exists():
            seen.add(key)
            uniq.append(p)
    return uniq


def parse_installdir_from_acf(acf_path):
    try:
        text = acf_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None
    m = re.search(r'"installdir"\s*"([^"]+)"', text, flags=re.IGNORECASE)
    return m.group(1).strip() if m else None


def find_cs2_videos_dir():
    libs = get_steam_library_paths()

    for lib in libs:
        steamapps = lib / "steamapps"
        manifest = steamapps / "appmanifest_730.acf"
        if manifest.exists():
            installdir = parse_installdir_from_acf(manifest)
            if installdir:
                cand = steamapps / "common" / installdir / "game" / "csgo" / "panorama" / "videos"
                if cand.is_dir():
                    return cand

    for lib in libs:
        common = lib / "steamapps" / "common"
        if not common.is_dir():
            continue
        try:
            for game_dir in common.iterdir():
                if not game_dir.is_dir():
                    continue
                cand = game_dir / "game" / "csgo" / "panorama" / "videos"
                if cand.is_dir():
                    if (cand / "intro.webm").exists() or (cand / "intro720p.webm").exists() or (cand / "intro").exists():
                        return cand
        except Exception:
            continue

    return None


def open_in_explorer(path):
    try:
        subprocess.Popen(["explorer", str(path)])
    except Exception:
        pass


def pick_file_by_stem(folder, stem):
    direct = [folder / stem, folder / f"{stem}.webm"]
    for p in direct:
        if p.exists() and p.is_file():
            return p

    try:
        for p in folder.iterdir():
            if p.is_file() and p.stem.lower() == stem.lower():
                return p
    except Exception:
        return None
    return None


def find_intro_files(folder):
    intro = pick_file_by_stem(folder, "intro")
    intro720p = pick_file_by_stem(folder, "intro720p")
    intro720 = pick_file_by_stem(folder, "intro720")

    return {
        "intro": intro,
        "intro720p": intro720p,
        "intro720": intro720,
    }


def _backup_folder_ok(folder):
    if not folder or not Path(folder).is_dir():
        return False
    files = find_intro_files(Path(folder))
    has_intro = files["intro"] is not None
    has_720 = (files["intro720p"] is not None) or (files["intro720"] is not None)
    return has_intro and has_720


def backup_ok(backup_dir):
    if not backup_dir.is_dir():
        return False

    if _backup_folder_ok(backup_dir):
        return True

    versions_dir = backup_dir / "versions"
    if not versions_dir.is_dir():
        return False

    try:
        for d in versions_dir.iterdir():
            if d.is_dir() and _backup_folder_ok(d):
                return True
    except Exception:
        return False

    return False


def get_latest_backup_source(backup_dir):
    if not backup_dir.is_dir():
        return None

    versions_dir = backup_dir / "versions"
    candidates = []

    if versions_dir.is_dir():
        try:
            for d in versions_dir.iterdir():
                if d.is_dir() and _backup_folder_ok(d):
                    candidates.append(d)
        except Exception:
            pass

    if candidates:
        candidates.sort(key=lambda p: p.name, reverse=True)
        return candidates[0]

    if _backup_folder_ok(backup_dir):
        return backup_dir

    return None


def ensure_videos_dir_interactive():
    found = find_cs2_videos_dir()
    if found:
        return found

    print("не удалось автоматически найти папку с интро.")
    print(r"вставь полный путь до папки ...\game\csgo\panorama\videos и нажми enter:")
    user_path = input().strip().strip('"')
    if not user_path:
        return None
    p = Path(user_path)
    return p if p.is_dir() else None


def action_open_and_backup():
    videos_dir = ensure_videos_dir_interactive()
    if not videos_dir:
        print("папка не найдена.")
        return

    open_in_explorer(videos_dir)

    files = find_intro_files(videos_dir)
    src_intro = files["intro"]
    src_720 = files["intro720p"] or files["intro720"]

    if not src_intro or not src_720:
        print("не нашёл файлы intro / intro720p (или intro720) в папке.")
        return

    downloads = get_downloads_dir()
    backup_dir = downloads / "cs2.intro.backup"
    backup_dir.mkdir(parents=True, exist_ok=True)

    had_backup = backup_ok(backup_dir)

    versions_dir = backup_dir / "versions"
    versions_dir.mkdir(parents=True, exist_ok=True)

    t = time.localtime()
    ts = f"{t.tm_year % 100:02d}-{t.tm_mon:02d}-{t.tm_mday:02d}_{t.tm_hour:02d}-{t.tm_min:02d}-{t.tm_sec:02d}"
    version_dir = versions_dir / ts
    i = 1
    while version_dir.exists():
        version_dir = versions_dir / f"{ts}_{i}"
        i += 1
    version_dir.mkdir(parents=True, exist_ok=True)

    try:
        shutil.copy2(src_intro, version_dir / src_intro.name)
        shutil.copy2(src_720, version_dir / src_720.name)

        shutil.copy2(src_intro, backup_dir / src_intro.name)
        shutil.copy2(src_720, backup_dir / src_720.name)

        if had_backup:
            print("папка открыта. бэкап обновлён (создана новая версия).")
        else:
            print("папка открыта. бэкап создан.")
    except PermissionError:
        print("нет прав на копирование. запусти скрипт от имени администратора.")
    except Exception as e:
        print(f"ошибка при создании бэкапа: {e}")


def action_restore():
    downloads = get_downloads_dir()
    backup_dir = downloads / "cs2.intro.backup"

    if not backup_dir.is_dir():
        print("бэкап не найден.")
        return

    source_dir = get_latest_backup_source(backup_dir)
    if not source_dir:
        print("бэкап повреждён или неполный.")
        return

    print("точно восстановить из бэкапа? (y/n)")
    ans = input().strip().lower()
    if ans != "y":
        print("отменено.")
        return

    if not ensure_admin_for_restore():
        return

    bfiles = find_intro_files(source_dir)
    b_intro = bfiles["intro"]
    b_720 = bfiles["intro720p"] or bfiles["intro720"]

    if not b_intro or not b_720:
        print("бэкап повреждён или неполный.")
        return

    videos_dir = ensure_videos_dir_interactive()
    if not videos_dir:
        print("папка не найдена.")
        return

    vfiles = find_intro_files(videos_dir)

    dest_intro = vfiles["intro"] or (videos_dir / b_intro.name)

    if vfiles["intro720p"]:
        dest_720 = vfiles["intro720p"]
    elif vfiles["intro720"]:
        dest_720 = vfiles["intro720"]
    else:
        dest_720 = videos_dir / b_720.name

    try:
        shutil.copy2(b_intro, dest_intro)
        shutil.copy2(b_720, dest_720)
        print("восстановлено из бэкапа.")
    except PermissionError:
        print("нет прав на запись в папку игры. запусти скрипт от имени администратора.")
    except Exception as e:
        print(f"ошибка при восстановлении: {e}")


def main():
    downloads = get_downloads_dir()
    backup_dir = downloads / "cs2.intro.backup"

    auto_action = None
    for a in sys.argv[1:]:
        if a.startswith("--auto_action="):
            auto_action = a.split("=", 1)[1].strip().lower()

    if auto_action == "restore":
        clear_screen()
        action_restore()
        pause_to_menu()

    while True:
        status = "есть" if backup_ok(backup_dir) else "отсутствует"

        clear_screen()
        print(menu_template.format(status=status))
        choice = input().strip()

        if choice == "1":
            clear_screen()
            action_open_and_backup()
            pause_to_menu()
        elif choice == "2":
            clear_screen()
            action_restore()
            pause_to_menu()
        elif choice == "3":
            clear_screen()
            print(tutorial_text)
            pause_to_menu()
        elif choice == "4":
            clear_screen()
            return
        else:
            clear_screen()
            print("неверный выбор.")
            pause_to_menu()


if __name__ == "__main__":
    main()
