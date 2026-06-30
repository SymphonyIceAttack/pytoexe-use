#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
coord_converter.py

Утилита для конвертации координат Decimal ↔ DMS.

Новые возможности
-----------------
1. **Формат DMS** – вместо привычных символов °′″ используется
   апострофный вид: 55'45''20.88''' N, 37'37''3.36''' E
2. **Диалоговое окно выбора входного файла** – если параметр ``-f/--file`` не указан,
   открывается стандартный файловый диалог (Windows‑проводник / macOS‑Finder /
   Linux‑file‑dialog).
3. **Диалоговое окно выбора пути сохранения** – если параметр ``-o/--output`` не указан,
   после вычисления появляется диалог «Сохранить как…». При отмене диалога
   результат выводится в консоль.
4. **В выводе показываются исходные данные**, которые пользователь передал
   (в виде блока «Входные данные: …»).

"""

from __future__ import annotations
import re
import sys
import json
import argparse
from typing import List, Tuple, Union

# --------------------------------------------------------------
# 1️⃣  Преобразования Decimal ↔ DMS
# --------------------------------------------------------------


def _decimal_to_dms(value: float) -> Tuple[int, int, float]:
    """Decimal → (deg, minute, sec)."""
    abs_val = abs(value)
    deg = int(abs_val)
    minutes_full = (abs_val - deg) * 60
    minute = int(minutes_full)
    sec = (minutes_full - minute) * 60
    return deg, minute, sec


def _dms_to_decimal(deg: int, minute: int, sec: float, sign: int) -> float:
    """DMS → Decimal (sign = +1 для N/E, -1 для S/W)."""
    return sign * (deg + minute / 60 + sec / 3600)


# --------------------------------------------------------------
# 2️⃣  Форматирование и разбор строк DMS
# --------------------------------------------------------------

# При разборе допускаются любые из перечисленных форм:
#   55°45′20.88″ N
#   55 45 20.88 N
#   55'45''20.88''' N   (все равно будет распознано)
_DMS_REGEX = re.compile(
    r"""^\s*
        (?P<deg>-?\d+)[°\s']*          # градусы (может быть ° или ')
        (?P<min>\d+)[′'\s]*           # минуты (может быть ′ или ')
        (?P<sec>\d+(?:\.\d+)?)[″"\s]*  # секунды (может быть ″ или ")
        (?P<dir>[NSEW])?\s*           # направление (опционально)
        $""",
    re.VERBOSE | re.IGNORECASE,
)


def _format_dms(lat: float, lon: float, sec_precision: int = 2) -> str:
    """
    Форматирует одну пару (lat, lon) в строку вида:

        55'45''20.88''' N, 37'37''3.36''' E

    Три апострофа после секунд – требуемый «апострофный» вид.
    """
    # 1) Decimal → DMS
    lat_deg, lat_min, lat_sec = _decimal_to_dms(lat)
    lon_deg, lon_min, lon_sec = _decimal_to_dms(lon)

    # 2) Направление
    lat_dir = "N" if lat >= 0 else "S"
    lon_dir = "E" if lon >= 0 else "W"

    # 3) Округляем секунды
    lat_sec = round(lat_sec, sec_precision)
    lon_sec = round(lon_sec, sec_precision)

    # 4) Формируем строку в требуемом виде
    lat_str = f"{lat_deg}'{lat_min}''{lat_sec}''' {lat_dir}"
    lon_str = f"{lon_deg}'{lon_min}''{lon_sec}''' {lon_dir}"
    return f"{lat_str}, {lon_str}"


def _parse_dms_str(dms_str: str) -> Tuple[float, float]:
    """Строка DMS → (lat_decimal, lon_decimal)."""
    # Делим на две части (широта, долгота)
    if "," in dms_str:
        lat_part, lon_part = dms_str.split(",", 1)
    else:
        parts = dms_str.strip().split()
        if len(parts) >= 4:
            lat_part = " ".join(parts[:2])
            lon_part = " ".join(parts[2:4])
        else:
            raise ValueError(f"Не удалось разбить DMS‑строку: {dms_str}")

    def parse_one(part: str) -> float:
        m = _DMS_REGEX.match(part.strip())
        if not m:
            raise ValueError(f"Не удалось распознать DMS‑часть: '{part}'")
        deg = int(m.group("deg"))
        minute = int(m.group("min"))
        sec = float(m.group("sec"))
        direction = m.group("dir")
        sign = 1
        if direction:
            direction = direction.upper()
            if direction in ("S", "W"):
                sign = -1
        if deg < 0:                     # учёт знака внутри числа (например, -33°…)
            sign = -1
            deg = abs(deg)
        return _dms_to_decimal(deg, minute, sec, sign)

    lat = parse_one(lat_part)
    lon = parse_one(lon_part)
    return lat, lon


# --------------------------------------------------------------
# 3️⃣  Универсальные функции, принимающие «список» данных
# --------------------------------------------------------------

_InputType = Union[
    List[Tuple[float, float]],
    Tuple[float, float],
    str,
    List[str],
]


def _normalize_pairs(data: _InputType) -> List[Tuple[float, float]]:
    """Приводит любой поддерживаемый ввод к списку кортежей (lat, lon) в Decimal."""
    # 1) Один кортеж
    if isinstance(data, tuple):
        return [(float(data[0]), float(data[1]))]

    # 2) Список строк DMS
    if isinstance(data, list) and all(isinstance(el, str) for el in data):
        return [_parse_dms_str(s) for s in data]

    # 3) Строка (может содержать несколько пар)
    if isinstance(data, str):
        pairs = []
        for block in data.replace("\n", ";").split(";"):
            block = block.strip()
            if not block:
                continue
            nums = [float(x) for x in block.replace(",", " ").split()]
            if len(nums) != 2:
                raise ValueError(f"Неверный формат координат: '{block}'")
            pairs.append((nums[0], nums[1]))
        return pairs

    # 4) Список кортежей/списков из 2 чисел
    if isinstance(data, list):
        result = []
        for i, item in enumerate(data):
            if not (isinstance(item, (list, tuple)) and len(item) == 2):
                raise ValueError(f"Элемент #{i} не является парой координат")
            result.append((float(item[0]), float(item[1])))
        return result

    raise TypeError("Поддерживаются только list, tuple или str")


def to_dms(data: _InputType, sec_precision: int = 2) -> List[str]:
    """Decimal → список строк DMS (в апострофном виде)."""
    pairs = _normalize_pairs(data)
    return [_format_dms(lat, lon, sec_precision) for lat, lon in pairs]


def to_decimal(data: _InputType) -> List[Tuple[float, float]]:
    """DMS → список кортежей Decimal."""
    if isinstance(data, list) and all(isinstance(el, str) for el in data):
        return _normalize_pairs(data)
    return _normalize_pairs(data)


# --------------------------------------------------------------
# 4️⃣  Чтение файлов и авто‑определение режима
# --------------------------------------------------------------


def _read_file(path: str) -> str:
    """Считывает файл целиком и возвращает его содержимое."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _detect_mode(user_input: str) -> str:
    """Определяет, что передано: DMS‑строки или десятичные числа."""
    # Если встречается хотя бы один из символов, характерных для DMS,
    # считаем, что вход – DMS.
    if any(sym in user_input for sym in "°′″NSEWnsew'"):
        return "dms"
    return "dec"


# --------------------------------------------------------------
# 5️⃣  Диалоговые окна (tkinter)
# --------------------------------------------------------------


def _choose_file_via_dialog() -> str | None:
    """Открывает диалог «Открыть файл» и возвращает выбранный путь, либо None."""
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError:
        return None

    root = tk.Tk()
    root.withdraw()
    root.update()

    file_path = filedialog.askopenfilename(
        title="Выберите файл с координатами",
        filetypes=[
            ("Текстовые файлы", "*.txt *.csv"),
            ("JSON‑файлы", "*.json"),
            ("Все файлы", "*.*"),
        ],
    )
    root.destroy()
    return file_path if file_path else None


def _choose_save_via_dialog(default_name: str = "result.txt") -> str | None:
    """
    Открывает диалог «Сохранить как…» и возвращает путь для записи.
    Если пользователь отменил диалог – возвращается None.
    """
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError:
        return None

    root = tk.Tk()
    root.withdraw()
    root.update()

    save_path = filedialog.asksaveasfilename(
        title="Сохранить результат",
        defaultextension=".txt",
        initialfile=default_name,
        filetypes=[
            ("Текстовые файлы", "*.txt"),
            ("Все файлы", "*.*"),
        ],
    )
    root.destroy()
    return save_path if save_path else None


# --------------------------------------------------------------
# 5️⃣  Обработка «сырого» ввода
# --------------------------------------------------------------


def _process_raw(raw: str, mode: str) -> Tuple[str, List[str]]:
    """
    Преобразует сырые данные ``raw`` в требуемый вывод.
    Возвращает кортеж ``(target_mode, lines)``:
        target_mode = 'dms' → строки DMS,
        target_mode = 'dec' → десятичные координаты.
    """
    target_mode = mode if mode != "auto" else _detect_mode(raw)

    if target_mode == "dec":
        # Попытка интерпретировать как JSON‑массив кортежей
        try:
            data = json.loads(raw.replace("'", '"'))
        except json.JSONDecodeError:
            data = raw
        result = to_dms(data)
        return "dms", result
    else:                                   # DMS → Decimal
        lines = [ln.strip() for ln in raw.replace("\n", ";").split(";") if ln.strip()]
        result = to_decimal(lines)
        out = [f"{lat:.7f}, {lon:.7f}" for lat, lon in result]
        return "dec", out


# --------------------------------------------------------------
# 6️⃣  Основная логика программы
# --------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Конвертер координат Decimal ↔ DMS",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "-f",
        "--file",
        metavar="FILE",
        help=(
            "Путь к файлу с координатами. Если не указан – откроется диалог выбора файла."
        ),
    )
    parser.add_argument(
        "-m",
        "--mode",
        choices=["auto", "dec", "dms"],
        default="auto",
        help=(
            "Явный режим обработки:\n"
            "  dec – входные данные – десятичные координаты;\n"
            "  dms – входные данные – строки DMS;\n"
            "  auto – определить автоматически (по умолчанию)."
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="OUT",
        help=(
            "Путь к файлу, куда записать результат. "
            "Если не указан – появится диалог «Сохранить как…». "
            "Отмена диалога → вывод в консоль."
        ),
    )
    args = parser.parse_args()

    # ----------------------------------------------------------
    # 1️⃣  Получаем входные данные (файл, диалог или stdin)
    # ----------------------------------------------------------
    if args.file:
        raw_input = _read_file(args.file)
    else:
        # Открываем диалоговое окно «Открыть файл»
        chosen = _choose_file_via_dialog()
        if chosen:
            raw_input = _read_file(chosen)
        else:
            # Пользователь закрыл диалог – читаем из stdin
            print(
                "Введите координаты вручную (или нажмите Ctrl‑D / Ctrl‑Z + Enter для завершения):"
            )
            raw_input = sys.stdin.read().strip()

    if not raw_input:
        sys.exit("Ввод пустой – программа завершена.")

    # ----------------------------------------------------------
    # 2️⃣  Преобразуем данные
    # ----------------------------------------------------------
    try:
        target_mode, out_lines = _process_raw(raw_input, args.mode)
    except Exception as exc:
        sys.stderr.write(f"Ошибка при обработке данных: {exc}\n")
        sys.exit(1)

    # ----------------------------------------------------------
    # 3️⃣  Формируем окончательный вывод
    # ----------------------------------------------------------
    header = "→ DMS:" if target_mode == "dms" else "→ Decimal:"

    # Блок «Входные данные» – выводим то, что пользователь подал.
    # Если входные данные слишком длинные, показываем только первые 500 символов
    # (это удобно при работе с большими файлами).
    max_len = 500
    shown_input = raw_input if len(raw_input) <= max_len else raw_input[:max_len] + "…"

    output_text = (
        f"Входные данные:\n{shown_input}\n\n"
        f"{header}\n" + "\n".join(out_lines)
    )

    # ----------------------------------------------------------
    # 4️⃣  Сохраняем результат
    # ----------------------------------------------------------
    if args.output:
        # Пользователь явно указал путь к файлу
        save_path = args.output
    else:
        # Открываем диалог «Сохранить как…»
        save_path = _choose_save_via_dialog(default_name="result.txt")

    if save_path:
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(output_text + "\n")
        print(f"Результат записан в файл: {save_path}")
    else:
        # Диалог отменён – выводим в консоль
        print(output_text)


# --------------------------------------------------------------
# Вспомогательные функции для диалогов
# --------------------------------------------------------------

def _choose_file_via_dialog() -> str | None:
    """Открывает диалог «Открыть файл» и возвращает выбранный путь, либо None."""
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError:
        return None

    root = tk.Tk()
    root.withdraw()
    root.update()

    file_path = filedialog.askopenfilename(
        title="Выберите файл с координатами",
        filetypes=[
            ("Текстовые файлы", "*.txt *.csv"),
            ("JSON‑файлы", "*.json"),
            ("Все файлы", "*.*"),
        ],
    )
    root.destroy()
    return file_path if file_path else None


def _choose_save_via_dialog(default_name: str = "result.txt") -> str | None:
    """
    Открывает диалог «Сохранить как…» и возвращает путь для записи.
    Если пользователь отменил диалог – возвращается None.
    """
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError:
        return None

    root = tk.Tk()
    root.withdraw()
    root.update()

    save_path = filedialog.asksaveasfilename(
        title="Сохранить результат",
        defaultextension=".txt",
        initialfile=default_name,
        filetypes=[
            ("Текстовые файлы", "*.txt"),
            ("Все файлы", "*.*"),
        ],
    )
    root.destroy()
    return save_path if save_path else None


if __name__ == "__main__":
    main()