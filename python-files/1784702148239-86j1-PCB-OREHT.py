import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QFileDialog,
                             QComboBox, QMessageBox, QProgressBar, QTextEdit)
from PyQt6.QtCore import Qt
import pandas as pd


class XLSXProcessor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.file_path = None
        self.df = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Обработка заказов РЭХТ')
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Выбор файла
        file_layout = QHBoxLayout()
        self.file_label = QLabel('Файл не выбран')
        self.file_label.setStyleSheet('color: gray;')
        file_layout.addWidget(self.file_label)

        self.btn_select_file = QPushButton('Выбрать файл')
        self.btn_select_file.clicked.connect(self.select_file)
        file_layout.addWidget(self.btn_select_file)
        layout.addLayout(file_layout)

        # Выбор столбца
        column_layout = QHBoxLayout()
        column_layout.addWidget(QLabel('Столбец с артикулом:'))
        self.column_combo = QComboBox()
        self.column_combo.setEnabled(False)
        column_layout.addWidget(self.column_combo)
        layout.addLayout(column_layout)

        # Прогресс бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Лог
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        layout.addWidget(self.log_text)

        # Кнопки обработки
        btn_layout = QHBoxLayout()
        self.btn_process = QPushButton('Обработать')
        self.btn_process.clicked.connect(self.process_file)
        self.btn_process.setEnabled(False)
        btn_layout.addWidget(self.btn_process)

        self.btn_save = QPushButton('Сохранить как...')
        self.btn_save.clicked.connect(self.save_file)
        self.btn_save.setEnabled(False)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)

        self.log('Готов к работе. Выберите XLSX или XLS файл.')

    def log(self, message):
        self.log_text.append(message)

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 'Выберите Excel файл', '',
            'Excel файлы (*.xlsx *.xls);;Все файлы (*)'
        )

        if file_path:
            self.file_path = file_path
            self.file_label.setText(os.path.basename(file_path))
            self.file_label.setStyleSheet('color: black;')

            try:
                # Определяем движок по расширению файла
                ext = os.path.splitext(file_path)[1].lower()
                if ext == '.xls':
                    # Старый формат XLS требует xlrd
                    self.df = pd.read_excel(file_path, engine='xlrd')
                    self.log('Файл загружен как XLS (старый формат)')
                else:
                    # XLSX использует openpyxl
                    self.df = pd.read_excel(file_path, engine='openpyxl')
                    self.log('Файл загружен как XLSX')

                self.column_combo.clear()
                self.column_combo.addItems(self.df.columns.tolist())
                self.column_combo.setEnabled(True)
                self.btn_process.setEnabled(True)
                self.log(f'Найдено столбцов: {len(self.df.columns)}, строк: {len(self.df)}')
            except ImportError as e:
                QMessageBox.critical(self, 'Ошибка',
                                     f'Не установлена необходимая библиотека:\n{str(e)}\n\n'
                                     'Установите: pip install xlrd')
                self.log(f'Ошибка импорта: {str(e)}')
            except Exception as e:
                QMessageBox.critical(self, 'Ошибка', f'Не удалось загрузить файл:\n{str(e)}')
                self.log(f'Ошибка загрузки: {str(e)}')

    def process_article(self, article):
        """Обработка артикула:
        1. Убираем звёздочки
        2. Оставляем только часть до запятой (первый артикул)
        3. Добавляем префикс 'РСВ-'
        """
        if pd.isna(article):
            return article

        article = str(article).strip()
        if not article:
            return article

        # 1. Убираем звёздочки
        article = article.replace('*', '')

        # 2. Оставляем только первый артикул (до запятой)
        if ',' in article:
            article = article.split(',')[0].strip()

        # 3. Добавляем префикс РСВ-
        article = f'РСВ-{article}'

        return article

    def process_file(self):
        if self.df is None:
            return

        column_name = self.column_combo.currentText()
        if not column_name:
            QMessageBox.warning(self, 'Предупреждение', 'Выберите столбец с артикулом')
            return

        self.log(f'Начинаю обработку столбца: {column_name}')
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(self.df))

        try:
            processed_count = 0
            for idx, row in self.df.iterrows():
                self.df.at[idx, column_name] = self.process_article(row[column_name])
                processed_count += 1
                self.progress_bar.setValue(processed_count)
                QApplication.processEvents()

            self.log(f'Обработка завершена. Обработано строк: {processed_count}')
            self.btn_save.setEnabled(True)
            self.progress_bar.setVisible(False)

            QMessageBox.information(self, 'Успех', f'Файл успешно обработан!\nОбработано строк: {processed_count}')

        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка при обработке:\n{str(e)}')
            self.log(f'Ошибка обработки: {str(e)}')
            self.progress_bar.setVisible(False)

    def save_file(self):
        if self.df is None:
            return

        # Предлагаем сохранить в XLSX (современный формат)
        # Если нужно сохранить в XLS - нужен xlwt, но он ограничен (65536 строк)
        default_name = 'обработанный_файл.xlsx'

        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, 'Сохранить файл', default_name,
            'Excel XLSX (*.xlsx);;Excel XLS (старый формат) (*.xls)'
        )

        if file_path:
            try:
                ext = os.path.splitext(file_path)[1].lower()

                if ext == '.xls':
                    # Старый формат XLS через xlwt
                    self.df.to_excel(file_path, index=False, engine='xlwt')
                    self.log('Файл сохранен в формате XLS')
                else:
                    # XLSX через openpyxl (по умолчанию)
                    self.df.to_excel(file_path, index=False, engine='openpyxl')
                    self.log('Файл сохранен в формате XLSX')

                self.log(f'Путь: {file_path}')
                QMessageBox.information(self, 'Успех', 'Файл успешно сохранен!')
            except ImportError as e:
                QMessageBox.critical(self, 'Ошибка',
                                     f'Не установлена необходимая библиотека:\n{str(e)}\n\n'
                                     'Для XLS установите: pip install xlwt')
                self.log(f'Ошибка импорта: {str(e)}')
            except Exception as e:
                QMessageBox.critical(self, 'Ошибка', f'Не удалось сохранить файл:\n{str(e)}')
                self.log(f'Ошибка сохранения: {str(e)}')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = XLSXProcessor()
    window.show()
    sys.exit(app.exec())