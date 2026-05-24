import sys
import os
import re
import urllib.parse
import webbrowser
import pandas as pd
import pdfplumber
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QPushButton, QLabel, QFileDialog, QMessageBox, QCheckBox,
                             QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit)
from PyQt5.QtCore import Qt

class SmartMatcherApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Интерактивная сверка недвижимости (v2. Диагностика)")
        self.resize(1000, 600)
        self.setStyleSheet("font-size: 14px;")

        self.pdf_path = ""
        self.excel_path = ""

        self.layout = QVBoxLayout()
        self.layout.setSpacing(10)

        self.label_info = QLabel("<b>Шаг 1:</b> Загрузите файлы для сверки", self)
        self.label_info.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.label_info)

        self.btn_pdf = QPushButton("📄 1. Выбрать PDF-файл (Выписка/Отчет)")
        self.btn_pdf.clicked.connect(self.select_pdf)
        self.layout.addWidget(self.btn_pdf)

        self.btn_excel = QPushButton("📊 2. Выбрать Excel/CSV-файл (Реестр)")
        self.btn_excel.clicked.connect(self.select_excel)
        self.layout.addWidget(self.btn_excel)

        self.cb_residential_only = QCheckBox("Искать ТОЛЬКО жилые помещения (Осторожно: может отсечь всё)")
        self.cb_residential_only.setChecked(False) # ТЕПЕРЬ ПО УМОЛЧАНИЮ ВЫКЛЮЧЕНО
        self.layout.addWidget(self.cb_residential_only)

        self.btn_run = QPushButton("🚀 3. Найти расхождения")
        self.btn_run.clicked.connect(self.run_comparison)
        self.btn_run.setEnabled(False)
        self.btn_run.setStyleSheet("background-color: #007BFF; color: white; font-weight: bold; padding: 10px;")
        self.layout.addWidget(self.btn_run)

        self.table = QTableWidget()
        self.table.setVisible(False)
        self.layout.addWidget(self.table)

        self.btn_export = QPushButton("💾 4. Сохранить итоговый результат в Excel")
        self.btn_export.clicked.connect(self.export_to_excel)
        self.btn_export.setVisible(False)
        self.btn_export.setStyleSheet("background-color: #28A745; color: white; font-weight: bold; padding: 10px;")
        self.layout.addWidget(self.btn_export)

        central_widget = QWidget()
        central_widget.setLayout(self.layout)
        self.setCentralWidget(central_widget)

    def select_pdf(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите PDF", "", "PDF Files (*.pdf)")
        if path:
            self.pdf_path = path
            self.btn_pdf.setText(f"📄 PDF: {os.path.basename(path)}")
            self.check_ready()

    def select_excel(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите Excel/CSV", "", "Table Files (*.xlsx *.xls *.csv)")
        if path:
            self.excel_path = path
            self.btn_excel.setText(f"📊 Таблица: {os.path.basename(path)}")
            self.check_ready()

    def check_ready(self):
        if self.pdf_path and self.excel_path:
            self.btn_run.setEnabled(True)

    def generate_sudact_link(self, query_text):
        base_url = "https://sudact.ru/regular/court/reshenya-reutovskii-gorodskoi-sud-moskovskaia-oblast/"
        query = " ".join(str(query_text).split())[:70] 
        encoded_query = urllib.parse.quote(query)
        return f"{base_url}?q={encoded_query}"

    def run_comparison(self):
        self.label_info.setText("⏳ Идет чтение PDF (может занять время, программа не зависла)...")
        QApplication.processEvents() # Чтобы интерфейс не зависал визуально

        # 1. Читаем PDF (Смягчили регулярное выражение)
        cadastral_pattern = re.compile(r'\d{2}:\d{2}:\d+:\d+')
        pdf_cads = set()
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        pdf_cads.update(cadastral_pattern.findall(text))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось прочитать PDF:\n{e}")
            self.label_info.setText("❌ Ошибка при чтении PDF.")
            return

        self.label_info.setText("⏳ Чтение таблицы Excel...")
        QApplication.processEvents()

        # 2. Читаем Excel
        try:
            if self.excel_path.endswith('.csv'):
                df_excel = pd.read_csv(self.excel_path, sep=None, engine='python')
            else:
                df_excel = pd.read_excel(self.excel_path)
        except Exception as e:
             QMessageBox.critical(self, "Ошибка", f"Не удалось прочитать таблицу:\n{e}")
             return

        # Ищем колонки
        cad_col = next((c for c in df_excel.columns if any(x in str(c).lower() for x in ['кадастр', 'кад.'])), None)
        addr_col = next((c for c in df_excel.columns if any(x in str(c).lower() for x in ['адрес', 'местоположение'])), None)
        type_col = next((c for c in df_excel.columns if any(x in str(c).lower() for x in ['назначение', 'наименование', 'вид'])), None)

        if not cad_col:
            QMessageBox.warning(self, "Внимание", "Колонка с кадастровым номером не найдена в Excel! Убедитесь, что она есть.")
            self.label_info.setText("❌ Ошибка структуры Excel.")
            return

        # Фильтр жилых помещений
        if self.cb_residential_only.isChecked() and type_col:
            df_excel = df_excel[df_excel[type_col].astype(str).str.contains('жил|квартир', case=False, na=False)]

        df_excel['Clean_Cad'] = df_excel[cad_col].astype(str).str.extract(r'(\d{2}:\d{2}:\d+:\d+)')
        
        excel_data = {}
        for _, row in df_excel.iterrows():
            cad = row['Clean_Cad']
            if pd.notna(cad):
                excel_data[cad] = {
                    'address': row[addr_col] if addr_col else "Не указан",
                    'type': row[type_col] if type_col else "Не указан"
                }

        excel_cadastrals = set(excel_data.keys())

        # --- ДИАГНОСТИКА ---
        QMessageBox.information(self, "Отчет о прочтении (Диагностика)", 
                                f"Успешно извлечено номеров из PDF: {len(pdf_cads)}\n"
                                f"Успешно извлечено номеров из Excel: {len(excel_cadastrals)}\n\n"
                                "Если где-то цифра 0, значит файл не прочитался правильно!")

        if len(pdf_cads) == 0 or len(excel_cadastrals) == 0:
            self.label_info.setText("⚠️ Сверка невозможна: один из файлов пуст или не читается.")
            return

        # 3. Сверка
        missing_in_pdf = excel_cadastrals - pdf_cads
        missing_in_excel = pdf_cads - excel_cadastrals

        discrepancies = []
        for cad in missing_in_pdf:
            addr = excel_data[cad]['address']
            discrepancies.append({
                "cad": cad, "addr": addr, "status": "Отсутствует в PDF",
                "link": self.generate_sudact_link(f"{cad} {addr}")
            })
        for cad in missing_in_excel:
            discrepancies.append({
                "cad": cad, "addr": "Неизвестно (только в PDF)", "status": "Отсутствует в Excel",
                "link": self.generate_sudact_link(cad)
            })

        if not discrepancies:
            QMessageBox.information(self, "Итог", "Расхождений не найдено! Списки полностью совпадают.")
            self.label_info.setText("✅ Расхождений нет.")
            return

        self.display_table(discrepancies)

    def display_table(self, data_list):
        self.label_info.setText(f"✅ Найдено расхождений: {len(data_list)}. Обработайте их в таблице ниже.")
        self.btn_run.setVisible(False)
        
        self.table.setVisible(True)
        self.btn_export.setVisible(True)

        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Кадастровый номер", "Адрес", "Откуда пропал", "Поиск в Суде", "Итог (Введите результат)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        self.table.setRowCount(len(data_list))
        
        for row, item in enumerate(data_list):
            item_cad = QTableWidgetItem(item['cad'])
            item_cad.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.table.setItem(row, 0, item_cad)

            item_addr = QTableWidgetItem(item['addr'])
            item_addr.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.table.setItem(row, 1, item_addr)

            item_status = QTableWidgetItem(item['status'])
            item_status.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.table.setItem(row, 2, item_status)
            
            btn_link = QPushButton("🔍 Искать дело")
            btn_link.setStyleSheet("background-color: #ffc107; font-weight: bold;")
            btn_link.clicked.connect(lambda ch, link=item['link']: webbrowser.open(link))
            self.table.setCellWidget(row, 3, btn_link)
            
            result_input = QLineEdit()
            result_input.setPlaceholderText("Например: Передано Иванову И.И.")
            self.table.setCellWidget(row, 4, result_input)

    def export_to_excel(self):
        save_path, _ = QFileDialog.getSaveFileName(self, "Сохранить результат", "Готовый_отчет.xlsx", "Excel Files (*.xlsx)")
        if not save_path:
            return

        rows = self.table.rowCount()
        export_data = []

        for row in range(rows):
            cad = self.table.item(row, 0).text()
            addr = self.table.item(row, 1).text()
            status = self.table.item(row, 2).text()
            
            input_widget = self.table.cellWidget(row, 4)
            user_text = input_widget.text() if input_widget else ""

            export_data.append({
                "Кадастровый номер": cad,
                "Адрес": addr,
                "Статус расхождения": status,
                "Решение суда (Ваш комментарий)": user_text
            })

        df = pd.DataFrame(export_data)
        df.to_excel(save_path, index=False)
        
        QMessageBox.information(self, "Готово", "Данные успешно выгружены в Excel!")
        
        if sys.platform == "win32":
            os.startfile(save_path)
        elif sys.platform == "darwin":
            os.system(f"open '{save_path}'")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SmartMatcherApp()
    window.show()
    sys.exit(app.exec_())