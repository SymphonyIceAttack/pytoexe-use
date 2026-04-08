#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль экспорта всех таблиц из SQLite‑баз (*.db) в один Excel.
Требуется:
    - Python 3.11.x
    - openpyxl==3.1.2

Установка зависимостей (если ещё не установлена):
    pip install "openpyxl==3.1.2"

Запуск из каталога, где находятся .db файлы:
    python export_db_to_excel.py
"""

import os
import sqlite3
from openpyxl import Workbook


def safe_sheet_name(name: str) -> str:
    """
    Приводит имя листа к формату, допустимому Excel.
    Ограничивает длину 31 символом и заменяет запрещённые знаки.
    """
    illegal_chars = set(r':?*[]/')
    for ch in illegal_chars:
        name = name.replace(ch, '_')
    # В Excel имена листов ограничены 31 символом
    return name[:31]


def export_db(db_path: str, wb: Workbook) -> None:
    """
    Экспортирует все таблицы из указанной SQLite‑базы в рабочую книгу.
    """
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        # Получаем список таблиц
        cur.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        )
        tables = [row[0] for row in cur.fetchall()]

        if not tables:
            print(f"[{db_path}] Таблицы не найдены.")
            return

        base_name = os.path.splitext(os.path.basename(db_path))[0]

        for tbl in tables:
            # Создаём лист
            sheet_title = safe_sheet_name(f"{base_name}_{tbl}")
            ws = wb.create_sheet(title=sheet_title)

            # Получаем данные из таблицы (экранируем имя)
            safe_tbl = tbl.replace('"', '""')
            cur.execute(f'SELECT * FROM "{safe_tbl}";')

            # Заголовки
            headers = [desc[0] for desc in cur.description]
            ws.append(headers)

            # Данные строками
            for row in cur.fetchall():
                ws.append(row)

        print(f"[{db_path}] Экспортировано {len(tables)} таблиц.")
    except Exception as exc:
        print(f"Ошибка при работе с {db_path}: {exc}")
    finally:
        conn.close()


def main() -> None:
    # Находим все *.db файлы в текущем каталоге
    db_files = [
        f for f in os.listdir(".")
        if f.lower().endswith(".db") and os.path.isfile(f)
    ]

    if not db_files:
        print("В каталоге нет файлов с расширением .db.")
        return

    # Создаём новую книгу и удаляем автоматический лист
    workbook = Workbook()
    default_sheet = workbook.active
    workbook.remove(default_sheet)

    for db_file in db_files:
        export_db(db_file, workbook)

    output_path = "merged_data.xlsx"
    workbook.save(output_path)
    print(f"\nВсе данные сохранены в: {output_path}")


if __name__ == "__main__":
    main()
