import os
import time
import subprocess
import ctypes
import sys
from pathlib import Path

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def show_error(message):
    ctypes.windll.user32.MessageBoxW(0, message, "Ошибка", 0x10)

def show_info(message):
    ctypes.windll.user32.MessageBoxW(0, message, "Информация", 0x40)

def check_process_exists(process_name):
    try:
        output = subprocess.check_output(
            ['tasklist', '/fi', f'imagename eq {process_name}'],
            text=True,
            stderr=subprocess.DEVNULL,
            encoding='utf-8',
            errors='ignore'
        )
        return process_name.lower() in output.lower()
    except:
        return False

def run_as_admin():
    if is_admin():
        return True
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    return False

def same_volume(p1: Path, p2: Path) -> bool:
    try:
        return p1.drive.lower() == p2.drive.lower()
    except:
        return False

def create_hardlink(link_path: Path, target_path: Path) -> bool:
    if link_path.exists() or link_path.is_symlink():
        try:
            link_path.unlink()
        except:
            pass
    try:
        CreateHardLinkW = ctypes.windll.kernel32.CreateHardLinkW
        CreateHardLinkW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_void_p]
        CreateHardLinkW.restype = ctypes.c_bool
        ok = CreateHardLinkW(str(link_path), str(target_path), None)
        if ok:
            return True
    except Exception:
        pass
    try:
        r = subprocess.run(f'cmd /c mklink /H "{str(link_path)}" "{str(target_path)}"', shell=True, capture_output=True, text=True)
        return r.returncode == 0
    except Exception:
        return False

def create_dir_junction(link_dir: Path, target_dir: Path) -> bool:
    if link_dir.exists():
        return False
    try:
        r = subprocess.run(f'cmd /c mklink /J "{str(link_dir)}" "{str(target_dir)}"', shell=True, capture_output=True, text=True)
        return r.returncode == 0
    except Exception:
        return False

def safe_rmdir(path: Path):
    try:
        if path.exists():
            subprocess.run(f'cmd /c rmdir /s /q "{str(path)}"', shell=True, capture_output=True)
    except:
        pass

def next_backup_name(base_dir: Path) -> Path:
    p = base_dir / "znxdlc"
    if not p.exists():
        return p
    i = 1
    while True:
        p = base_dir / f"znxdlc{i}"
        if not p.exists():
            return p
        i += 1

def ensure_parent(p: Path):
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
    except:
        pass

def next_audio_backup_name(sfx_dir: Path) -> Path:
    cand = sfx_dir / "znx.rpf"
    if not cand.exists():
        return cand
    i = 1
    while True:
        cand = sfx_dir / f"znx{i}.rpf"
        if not cand.exists():
            return cand
        i += 1

def main():
    if not run_as_admin():
        return

    base_dir = Path(sys.executable).parent
    update_dir = base_dir / "update"
    redux_file = update_dir / "update.rpf"
    path_file = base_dir / "gtav_path.txt"
    gunpack_dir = base_dir / "gunpack" / "dlcpacks"
    audio_sfx_dir = base_dir / "audio" / "sfx"

    if not path_file.exists():
        show_error("Файл gtav_path.txt не найден")
        return

    if not update_dir.exists() or not redux_file.exists():
        show_error("Неверно вложен редукс")
        return

    try:
        with open(path_file, 'r', encoding='utf-8') as f:
            target_path = f.read().strip().strip('"')
        target_dir = Path(target_path)
        original_file = target_dir / "update.rpf"
        backup_file = target_dir / "znx.rpf"
    except Exception as e:
        show_error(f"Ошибка чтения пути: {str(e)}")
        return

    redux_file = redux_file.resolve()
    original_file = original_file.resolve()
    backup_file = backup_file.resolve()
    target_dir = target_dir.resolve()

    if not same_volume(redux_file, original_file):
        show_error(
            "zloader не находится на том же диске с GTA V\n\n"
            f"GTAV: {original_file.drive}...\n"
            f"Redux: {redux_file.drive}...\n\n"
        )
        return

    game_orig = target_dir.parent
    game_dlc_orig = target_dir / "x64" / "dlcpacks"
    game_audio_sfx = game_orig / "x64" / "audio" / "sfx"

    local_dlc_names = []
    if gunpack_dir.exists():
        for p in gunpack_dir.iterdir():
            if p.is_dir():
                local_dlc_names.append(p.name)

    local_audio_files = []
    if audio_sfx_dir.exists():
        for p in audio_sfx_dir.iterdir():
            if p.is_file() and p.suffix.lower() == ".rpf":
                local_audio_files.append(p.name)

    print("Ожидаю запуска GTAV...")

    eac_launched = False
    gta_running = False
    dlc_swaps = []
    created_dlc = 0
    audio_actions = []

    try:
        while True:
            if not eac_launched and check_process_exists("EACLauncher.exe"):
                eac_launched = True
                try:
                    if backup_file.exists():
                        try:
                            backup_file.unlink()
                        except:
                            pass
                    if original_file.exists() or original_file.is_symlink():
                        try:
                            if original_file.is_symlink():
                                original_file.unlink()
                            else:
                                original_file.rename(backup_file)
                        except Exception as e:
                            show_error(f"Не удалось инициализировать редукс: {e}")
                            return
                    if not create_hardlink(original_file, redux_file):
                        try:
                            if original_file.exists() or original_file.is_symlink():
                                original_file.unlink()
                        except:
                            pass
                        try:
                            if backup_file.exists() and not original_file.exists():
                                backup_file.rename(original_file)
                        except:
                            pass
                        show_error("Не удалось инициализировать редукс")
                        return

                    if game_dlc_orig.exists() and local_dlc_names:
                        for name in local_dlc_names:
                            src_orig = (gunpack_dir / name).resolve()
                            dst_orig = (game_dlc_orig / name).resolve()
                            if not src_orig.exists() or not src_orig.is_dir():
                                continue
                            if not dst_orig.exists() or not dst_orig.is_dir():
                                continue
                            stage_dir = (game_dlc_orig / (name + ".znxstage")).resolve()
                            if stage_dir.exists():
                                safe_rmdir(stage_dir)
                            try:
                                stage_dir.mkdir(parents=True, exist_ok=True)
                            except:
                                continue
                            ok_stage = True
                            for r, _, files in os.walk(dst_orig):
                                for fn in files:
                                    orig = Path(r) / fn
                                    rel = orig.relative_to(dst_orig)
                                    stg = stage_dir / rel
                                    ensure_parent(stg)
                                    if not create_hardlink(stg, orig):
                                        ok_stage = False
                                        break
                                if not ok_stage:
                                    break
                            if not ok_stage:
                                safe_rmdir(stage_dir)
                                continue
                            for r, _, files in os.walk(src_orig):
                                for fn in files:
                                    modf = Path(r) / fn
                                    rel = modf.relative_to(src_orig)
                                    stg = stage_dir / rel
                                    ensure_parent(stg)
                                    if stg.exists() or stg.is_symlink():
                                        try:
                                            stg.unlink()
                                        except:
                                            pass
                                    if not create_hardlink(stg, modf):
                                        ok_stage = False
                                        break
                                if not ok_stage:
                                    break
                            if not ok_stage:
                                safe_rmdir(stage_dir)
                                continue
                            bk = next_backup_name(game_dlc_orig)
                            try:
                                dst_orig.rename(bk)
                                stage_dir.rename(dst_orig)
                                dlc_swaps.append((dst_orig, bk))
                                created_dlc += 1
                            except:
                                try:
                                    if stage_dir.exists():
                                        safe_rmdir(stage_dir)
                                except:
                                    pass

                    if game_audio_sfx.exists() and local_audio_files:
                        for fname in local_audio_files:
                            src_file = (audio_sfx_dir / fname).resolve()
                            dst_file = (game_audio_sfx / fname).resolve()
                            if not dst_file.exists() or not dst_file.is_file():
                                continue
                            bk = next_audio_backup_name(game_audio_sfx)
                            try:
                                dst_file.rename(bk)
                            except:
                                continue
                            if create_hardlink(dst_file, src_file):
                                audio_actions.append((dst_file, bk))
                            else:
                                try:
                                    if dst_file.exists():
                                        dst_file.unlink()
                                except:
                                    pass
                                try:
                                    if bk.exists() and not dst_file.exists():
                                        bk.rename(dst_file)
                                except:
                                    pass

                    if created_dlc > 0:
                        print("Редукс и ганпак успешно инициализированы")
                    else:
                        print("Редукс успешно инициализирован")
                    if audio_actions:
                        print("Пак звуков успешно инициализирован")

                except Exception:
                    try:
                        if original_file.exists() or original_file.is_symlink():
                            original_file.unlink()
                    except:
                        pass
                    try:
                        if backup_file.exists() and not original_file.exists():
                            backup_file.rename(original_file)
                    except:
                        pass
                    for dst, bk in reversed(dlc_swaps):
                        try:
                            if dst.exists():
                                safe_rmdir(dst)
                        except:
                            pass
                        try:
                            if bk.exists() and not dst.exists():
                                bk.rename(dst)
                        except:
                            pass
                    for dst_f, bk_f in reversed(audio_actions):
                        try:
                            if dst_f.exists():
                                dst_f.unlink()
                        except:
                            pass
                        try:
                            if bk_f.exists() and not dst_f.exists():
                                bk_f.rename(dst_f)
                        except:
                            pass
                    return

            if eac_launched and not gta_running and check_process_exists("GTA5.exe"):
                gta_running = True

            if gta_running and not check_process_exists("GTA5.exe"):
                try:
                    if original_file.exists() or original_file.is_symlink():
                        try:
                            original_file.unlink()
                        except:
                            pass
                    if backup_file.exists():
                        backup_file.rename(original_file)

                    if dlc_swaps:
                        for dst, bk in reversed(dlc_swaps):
                            try:
                                if dst.exists():
                                    safe_rmdir(dst)
                            except:
                                pass
                            try:
                                if bk.exists() and not dst.exists():
                                    bk.rename(dst)
                            except:
                                pass
                        print("Редукс и ганпак успешно утилизированы")
                    else:
                        print("Редукс успешно утилизирован")

                    if audio_actions:
                        for dst_f, bk_f in reversed(audio_actions):
                            try:
                                if dst_f.exists():
                                    dst_f.unlink()
                            except:
                                pass
                            try:
                                if bk_f.exists() and not dst_f.exists():
                                    bk_f.rename(dst_f)
                            except:
                                pass
                        print("Пак звуков успешно утилизирован")

                    break
                except Exception:
                    return

            time.sleep(0.5)

    except KeyboardInterrupt:
        try:
            if original_file.exists() or original_file.is_symlink():
                try:
                    original_file.unlink()
                except:
                    pass
            if backup_file.exists():
                backup_file.rename(original_file)

            if dlc_swaps:
                for dst, bk in reversed(dlc_swaps):
                    try:
                        if dst.exists():
                            safe_rmdir(dst)
                    except:
                        pass
                    try:
                        if bk.exists() and not dst.exists():
                            bk.rename(dst)
                    except:
                        pass
                print("Редукс и ганпак успешно утилизированы")
            else:
                print("Редукс успешно утилизирован")

            if audio_actions:
                for dst_f, bk_f in reversed(audio_actions):
                    try:
                        if dst_f.exists():
                            dst_f.unlink()
                    except:
                        pass
                    try:
                        if bk_f.exists() and not dst_f.exists():
                            bk_f.rename(dst_f)
                    except:
                        pass
                print("Пак звуков успешно утилизирован")
        except Exception:
            pass

    print("Нажмите любую клавишу для выхода...")
    os.system("pause >nul")

if __name__ == "__main__":
    main()
