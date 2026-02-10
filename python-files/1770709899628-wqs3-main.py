import sys
import os
import json
import subprocess
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QLineEdit, QPushButton, QLabel,
                               QFileDialog, QTableWidget, QTableWidgetItem,
                               QComboBox, QHeaderView, QMessageBox)
from PySide6.QtCore import Qt

CONFIG_FILE = "service_manager_cfg.json"


class ServiceManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Управление объектами (Авто-имена команд)")
        self.resize(1100, 650)

        #Основной виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)

        #Настройка путей
        self.setup_header()

        #ТАБЛИЦА
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Имя объекта (ПК)", "IP / Адрес", "Тип запуска", "Команды (1-6)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.main_layout.addWidget(self.table)

        #НИЖНЯЯ ПАНЕЛЬ
        btn_layout = QHBoxLayout()
        self.btn_add_pc = QPushButton("Добавить строку (ПК)")
        self.btn_add_pc.clicked.connect(self.add_empty_row)

        self.btn_save = QPushButton("Сохранить конфигурацию")
        self.btn_save.clicked.connect(self.save_config)
        self.btn_save.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")

        btn_layout.addWidget(self.btn_add_pc)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_save)
        self.main_layout.addLayout(btn_layout)

        self.load_config()

    def get_cmd_name(self, path):

        if not path:
            return "Не выбрано"
        filename = os.path.basename(path)
        name, _ = os.path.splitext(filename)
        return name

    def setup_header(self):
        header_widget = QWidget()
        h_layout = QVBoxLayout(header_widget)
        h_layout.addWidget(QLabel("<b>Настройка команд (пути к bat-файлам):</b>"))

        grid = QHBoxLayout()
        self.script_edits = []
        self.name_labels = []  # Список меток для имен команд

        for i in range(6):
            v_box = QVBoxLayout()

            # Метка с именем
            lbl = QLabel("Команда " + str(i + 1))
            lbl.setStyleSheet("color: #7f8c8d; font-size: 11px;")
            self.name_labels.append(lbl)

            edit = QLineEdit()
            edit.setPlaceholderText(f"Путь...")
            edit.textChanged.connect(lambda text, idx=i: self.update_labels(idx, text))

            btn = QPushButton(f"Обзор {i + 1}")
            btn.clicked.connect(lambda ch, idx=i: self.select_script(idx))

            v_box.addWidget(lbl)
            v_box.addWidget(edit)
            v_box.addWidget(btn)
            grid.addLayout(v_box)
            self.script_edits.append(edit)

        h_layout.addLayout(grid)
        self.main_layout.addWidget(header_widget)

    def update_labels(self, idx, path):
        """Обновляет текст над полем ввода при изменении пути"""
        name = self.get_cmd_name(path)
        self.name_labels[idx].setText(f"ID {idx + 1}: {name}")
        #Обновляем подсказки в таблице
        for r in range(self.table.rowCount()):
            self.refresh_row_tooltips(r)

    def select_script(self, idx):
        file, _ = QFileDialog.getOpenFileName(self, "Выбор bat-файла", "", "Batch Files (*.bat)")
        if file:
            self.script_edits[idx].setText(file)

    def add_empty_row(self, data=None):
        row = self.table.rowCount()
        self.table.insertRow(row)

        self.table.setItem(row, 0, QTableWidgetItem(data["name"] if data else "Новый ПК"))
        self.table.setItem(row, 1, QTableWidgetItem(data["host"] if data else "127.0.0.1"))

        combo = QComboBox()
        combo.addItems(["Локально", "PsExec (Удаленно)", "Открыть папку"])
        if data: combo.setCurrentText(data.get("type", "Локально"))
        self.table.setCellWidget(row, 2, combo)

        #Контейнер для кнопок действий
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(4, 2, 4, 2)
        actions_layout.setSpacing(4)

        for i in range(6):
            btn = QPushButton(str(i + 1))
            btn.setFixedWidth(30)
            btn.clicked.connect(lambda ch, r=row, c=i: self.execute_command(r, c))
            actions_layout.addWidget(btn)

        self.table.setCellWidget(row, 3, actions_widget)
        self.refresh_row_tooltips(row)

    def refresh_row_tooltips(self, row_idx):

        container = self.table.cellWidget(row_idx, 3)
        if container:
            buttons = container.findChildren(QPushButton)
            for i, btn in enumerate(buttons):
                path = self.script_edits[i].text()
                btn.setToolTip(f"Запустить: {self.get_cmd_name(path)}")

    def execute_command(self, row_idx, script_idx):
        host = self.table.item(row_idx, 1).text()
        script_path = self.script_edits[script_idx].text()
        cmd_type = self.table.cellWidget(row_idx, 2).currentText()

        if not script_path or not os.path.exists(script_path):
            QMessageBox.warning(self, "Ошибка", "Файл не выбран или отсутствует по указанному пути!")
            return

        try:
            if cmd_type == "Локально":
                #Запуск с проверкой ошибок и паузой
                cmd = f'cmd /c "call "{script_path}" && (echo OK: {os.path.basename(script_path)} & timeout /t 5) || (color 4f & echo ERROR in script! & pause)"'
                subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)

            elif cmd_type == "PsExec (Удаленно)":
                cmd = f'psexec \\\\{host} -c "{script_path}"'
                subprocess.Popen(f'cmd /k "{cmd}"', creationflags=subprocess.CREATE_NEW_CONSOLE)

            elif cmd_type == "Открыть папку":
                os.startfile(os.path.dirname(script_path))

        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", str(e))

    def save_config(self):
        config = {
            "scripts": [e.text() for e in self.script_edits],
            "objects": []
        }
        for r in range(self.table.rowCount()):
            config["objects"].append({
                "name": self.table.item(r, 0).text(),
                "host": self.table.item(r, 1).text(),
                "type": self.table.cellWidget(r, 2).currentText()
            })
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        QMessageBox.information(self, "Готово", "Все пути и список ПК сохранены!")

    def load_config(self):
        if not os.path.exists(CONFIG_FILE): return
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                for i, path in enumerate(config.get("scripts", [])):
                    if i < 6:
                        self.script_edits[i].setText(path)
                        self.update_labels(i, path)
                for obj in config.get("objects", []):
                    self.add_empty_row(obj)
        except Exception as e:
            print(f"Ошибка загрузки: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = ServiceManager()
    window.show()
    sys.exit(app.exec())