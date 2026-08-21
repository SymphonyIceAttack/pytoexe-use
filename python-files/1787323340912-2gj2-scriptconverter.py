import base64
import json
from pathlib import Path
import sys
import uuid


def decode_custom_b64(text: str) -> str:
    if not text:
        return ""
    b64_str = text.replace("[_]", "/")
    b64_str += "=" * ((4 - len(b64_str) % 4) % 4)
    for enc in ("utf-8", "cp1251"):
        try:
            return base64.b64decode(b64_str).decode(enc)
        except Exception:
            continue
    return text


def parse_track(track_str: str) -> list:
    if not track_str.strip():
        return []
    motions = []
    for item in track_str.strip().split(";"):
        if not item.strip():
            continue
        p = item.split(",")
        if len(p) >= 14:
            motions.append(
                {
                    "drive": int(p[0]),
                    "type": int(p[1]),
                    "repeat": max(1, int(p[2])),
                    "delay": int(p[3]),
                    "startType": int(p[4]) & 0xFF,
                    "arg1": int(p[5]),
                    "arg2": int(p[6]),
                    "arg3": int(p[7]),
                    "vMax": int(p[8]),
                    "startPos": int(p[9]),
                    "targetPos": int(p[10]),
                    "tAcc": int(p[11]),
                    "tDec": int(p[12]),
                    "offset": max(50, int(p[13])),
                }
            )
    return motions


def read_file_text(file_path: Path) -> str:
    for enc in ("utf-8", "cp1251", "latin1"):
        try:
            return file_path.read_text(encoding=enc)
        except Exception:
            continue
    return file_path.read_text(encoding="utf-8", errors="replace")


def convert_file(file_path: Path, output_dir: Path):
    content = read_file_text(file_path)
    actions_raw = {}

    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("***") or line.startswith("["):
            continue
        if "=" not in line:
            continue

        key_part, val_part = line.split("=", 1)
        if "/:" not in key_part:
            continue

        idx_str, field = key_part.split("/:", 1)
        try:
            idx = int(idx_str)
        except ValueError:
            continue

        if idx not in actions_raw:
            actions_raw[idx] = {}

        actions_raw[idx][field] = val_part

    if not actions_raw:
        print(f"⚠️ Пропущен файл (нет секций действий): {file_path.name}")
        return

    actions = []
    for idx in sorted(actions_raw.keys()):
        raw = actions_raw[idx]
        flags = int(raw.get("flags", 0))

        actions.append(
            {
                "name": decode_custom_b64(raw.get("name", "")),
                "description": decode_custom_b64(raw.get("description", "")),
                "autoTrack": bool(flags & 1),
                "leftBwdSeq": bool(flags & 2),
                "rightBwdSeq": bool(flags & 4),
                "leftTrack": parse_track(raw.get("left_track", "")),
                "rightTrack": parse_track(raw.get("right_track", "")),
            }
        )

    # Генерируем уникальный UUID для нового HMI
    file_uuid = str(uuid.uuid4())

    # Срезаем старый префикс вроде 665903_, если он есть
    clean_name = file_path.stem
    if "_" in clean_name and clean_name.split("_")[0].isdigit():
        clean_name = clean_name.split("_", 1)[1]

    out_obj = {
        "uuid": file_uuid,
        "actions": actions,
    }

    # Имя файла по строгому регламенту: <UUID>_<Название>.json
    out_filename = f"{file_uuid}_{clean_name}.json"
    out_file = output_dir / out_filename

    out_file.write_text(
        json.dumps(out_obj, ensure_ascii=False, indent=4), encoding="utf-8"
    )
    print(f"✅ Сконвертирован: {file_path.name} -> {out_filename}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        src_dir = Path(sys.argv[1])
        out_dir = Path(
            sys.argv[2] if len(sys.argv) > 2 else src_dir / "converted_json"
        )
    else:
        import tkinter as tk
        from tkinter import filedialog

        root_tk = tk.Tk()
        root_tk.withdraw()

        print("Выберите папку со старыми файлами спектаклей...")
        selected_folder = filedialog.askdirectory(
            title="Выберите папку со старыми спектаклями (*.scene)"
        )

        if not selected_folder:
            print("Отменено пользователем.")
            sys.exit(0)

        src_dir = Path(selected_folder)
        out_dir = src_dir / "converted_json"

    out_dir.mkdir(parents=True, exist_ok=True)

    # Ищем файлы *.scene, *.txt, *.scn, *.ini
    extensions = ("*.scene", "*.SCENE", "*.txt", "*.scn", "*.ini")
    files_to_convert = []
    for ext in extensions:
        files_to_convert.extend(src_dir.glob(ext))

    # Убираем возможные дубликаты
    files_to_convert = list(set(files_to_convert))

    if not files_to_convert:
        print(f"⚠️ В папке {src_dir} не найдено файлов сценариев (*.scene).")
    else:
        for f in files_to_convert:
            convert_file(f, out_dir)
        print(f"\n🎉 Готово! Все JSON сохранены в: {out_dir}")

    input("\nНажмите Enter для выхода...")