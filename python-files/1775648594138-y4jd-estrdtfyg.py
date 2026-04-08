#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Export all SQLite (.db) files in a directory into one Excel workbook.
GUI is implemented with PyQt6.  All heavy work runs in a QThread so the UI
stays responsive.

Requirements:
    - Python 3.11.x
    - openpyxl==3.1.2
    - PyQt6
"""

import os
import sys
import sqlite3

from openpyxl import Workbook
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QFileDialog,
    QMessageBox,
    QVBoxLayout,
    QHBoxLayout,
)


# --------------------------------------------------------------------------- #
#  Утилиты для работы с SQLite и Excel
# --------------------------------------------------------------------------- #


def safe_sheet_name(name: str) -> str:
    """
    Приводит имя листа к формату, допустимому Excel.
    Ограничивает длину 31 символом и заменяет запрещённые знаки.
    """
    illegal_chars = set(r":?*[]/")
    for ch in illegal_chars:
        name = name.replace(ch, "_")
    return name[:31]


def export_db_to_workbook(db_path: str, wb: Workbook) -> None:
    """Экспортирует все таблицы из одной SQLite‑базы в рабочую книгу."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    try:
        # Получаем список всех пользовательских таблиц
        cur.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        )
        tables = [row[0] for row in cur.fetchall()]

        if not tables:
            return

        base_name = os.path.splitext(os.path.basename(db_path))[0]

        for tbl in tables:
            safe_tbl = tbl.replace('"', '""')
            cur.execute(f'SELECT * FROM "{safe_tbl}";')

            headers = [desc[0] for desc in cur.description]
            ws = wb.create_sheet(title=safe_sheet_name(f"{base_name}_{tbl}"))
            ws.append(headers)

            for row in cur.fetchall():
                ws.append(row)
    finally:
        conn.close()


# --------------------------------------------------------------------------- #
#  Поток выполнения экспорта
# --------------------------------------------------------------------------- #


class ExportThread(QThread):
    progress = pyqtSignal(str)      # сообщение о ходе работы
    finished = pyqtSignal()         # завершение без ошибок
    error = pyqtSignal(str)         # сообщение об ошибке

    def __init__(self, folder: str, parent=None):
        super().__init__(parent)
        self.folder = folder

    def run(self):
        try:
            db_files = [
                f for f in os.listdir(self.folder)
                if f.lower().endswith(".db") and os.path.isfile(os.path.join(self.folder, f))
            ]

            if not db_files:
                self.error.emit("В каталоге нет файлов с расширением .db.")
                return

            wb = Workbook()
            # Удаляем автоматически созданный лист
            default_sheet = wb.active
            wb.remove(default_sheet)

            for i, db_name in enumerate(db_files, 1):
                db_path = os.path.join(self.folder, db_name)
                self.progress.emit(f"[{i}/{len(db_files)}] Обрабатываем: {db_name}")
                export_db_to_workbook(db_path, wb)

            output_file = os.path.join(self.folder, "merged_data.xlsx")
            wb.save(output_file)
            self.progress.emit(f"Готово! Файл сохранён как:\n{output_file}")
            self.finished.emit()

        except Exception as exc:
            self.error.emit(str(exc))


# --------------------------------------------------------------------------- #
#  Основное окно
# --------------------------------------------------------------------------- #


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SQLite → Excel (PyQt6)")
        self.resize(600, 400)
        self._create_ui()
        self.export_thread = None

    def _create_ui(self):
        layout = QVBoxLayout()

        # Путь к каталогу
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.browse_btn = QPushButton("Обзор")
        self.browse_btn.clicked.connect(self.select_folder)
        path_layout.addWidget(QLabel("Каталог:"))
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(self.browse_btn)

        # Кнопка запуска
        self.run_btn = QPushButton("Экспортировать в Excel")
        self.run_btn.clicked.connect(self.start_export)
        self.run_btn.setEnabled(False)  # пока путь не выбран

        # Поле вывода статуса
        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)

        layout.addLayout(path_layout)
        layout.addWidget(self.run_btn)
        layout.addWidget(QLabel("Статус:"))
        layout.addWidget(self.log_edit)

        self.setLayout(layout)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Выберите каталог с .db файлами", os.getcwd()
        )
        if folder:
            self.path_edit.setText(folder)
            self.run_btn.setEnabled(True)

    def start_export(self):
        folder = self.path_edit.text().strip()
        if not folder or not os.path.isdir(folder):
            QMessageBox.warning(self, "Ошибка", "Укажите корректный каталог.")
            return

        # Отключаем кнопку и очищаем лог
        self.run_btn.setEnabled(False)
        self.log_edit.clear()

        # Запускаем поток
        self.export_thread = ExportThread(folder)
        self.export_thread.progress.connect(self.append_log)
        self.export_thread.finished.connect(self.on_finished)
        self.export_thread.error.connect(self.on_error)
        self.export_thread.start()

    def append_log(self, message: str):
        self.log_edit.append(message)

    def on_finished(self):
        QMessageBox.information(self, "Готово", "Экспорт завершён без ошибок.")
        self.run_btn.setEnabled(True)

    def on_error(self, err_msg: str):
        QMessageBox.critical(self, "Ошибка экспорта", err_msg)
        self.log_edit.append(f"\nОшибка: {err_msg}")
        self.run_btn.setEnabled(True)


# --------------------------------------------------------------------------- #
#  Точка входа
# --------------------------------------------------------------------------- #

def main():
    app = QApplication(sys.argv)

    # Проверяем наличие нужной версии openpyxl
    try:
        import openpyxl

        if tuple(map(int, openpyxl.__version__.split("."))) < (3, 1, 2):
            raise RuntimeError("Нужна версия openpyxl>=3.1.2")
    except Exception as exc:
        QMessageBox.critical(
            None,
            "Зависимости",
            f"Не удалось проверить версию openpyxl.\n{exc}",
        )
        sys.exit(1)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
