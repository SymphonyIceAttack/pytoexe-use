import sys
import os
import json
from datetime import datetime, date
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class BudgetApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # Создаем папку для данных, если её нет
        self.data_dir = os.path.join(os.path.expanduser("~"), "PersonalBudget")
        os.makedirs(self.data_dir, exist_ok=True)
        self.data_file = os.path.join(self.data_dir, "budget_data.json")
        
        self.transactions = []
        self.categories = ["Еда", "Транспорт", "Жилье", "Развлечения", "Здоровье", "Одежда", "Образование", "Другое"]
        self.load_data()
        self.init_ui()
        
    def init_ui(self):
        try:
            self.setWindowTitle("Личный Бюджет")
            self.setGeometry(100, 100, 1100, 650)
            
            # Упрощенный стиль для лучшей совместимости
            self.setStyleSheet("""
                QMainWindow { background-color: #f0f8f0; }
                QWidget { font-family: Arial, sans-serif; font-size: 13px; }
                QPushButton {
                    background-color: #2ecc71;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #27ae60; }
                QPushButton:pressed { background-color: #229954; }
                QLineEdit, QComboBox, QDateEdit {
                    padding: 6px;
                    border: 1px solid #bdc3c7;
                    border-radius: 3px;
                    background-color: white;
                }
                QLineEdit:focus, QComboBox:focus, QDateEdit:focus {
                    border: 1px solid #2ecc71;
                }
                QTableWidget {
                    background-color: white;
                    border: 1px solid #bdc3c7;
                    alternate-background-color: #f8f9fa;
                }
                QHeaderView::section {
                    background-color: #ecf0f1;
                    padding: 8px;
                    font-weight: bold;
                }
                QTabWidget::pane { border: 1px solid #bdc3c7; background: white; }
                QTabBar::tab {
                    background: #ecf0f1;
                    padding: 8px 16px;
                    margin-right: 2px;
                }
                QTabBar::tab:selected { background: #2ecc71; color: white; }
                QGroupBox {
                    border: 1px solid #bdc3c7;
                    border-radius: 4px;
                    margin-top: 10px;
                    background: white;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px;
                }
            """)
            
            # Центральный виджет
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            main_layout = QHBoxLayout(central_widget)
            
            # Левая панель
            left_panel = QWidget()
            left_layout = QVBoxLayout(left_panel)
            left_layout.setSpacing(10)
            
            # Форма добавления транзакции
            form_group = QGroupBox("Новая транзакция")
            form_layout = QFormLayout(form_group)
            
            self.type_combo = QComboBox()
            self.type_combo.addItems(["Доход", "Расход"])
            
            self.amount_edit = QLineEdit()
            self.amount_edit.setPlaceholderText("0.00")
            
            self.category_combo = QComboBox()
            self.category_combo.addItems(self.categories)
            
            self.description_edit = QLineEdit()
            self.description_edit.setPlaceholderText("Описание")
            
            self.date_edit = QDateEdit()
            self.date_edit.setDate(QDate.currentDate())
            self.date_edit.setDisplayFormat("dd.MM.yyyy")
            
            add_btn = QPushButton("➕ Добавить")
            add_btn.clicked.connect(self.add_transaction)
            
            form_layout.addRow("Тип:", self.type_combo)
            form_layout.addRow("Сумма (₽):", self.amount_edit)
            form_layout.addRow("Категория:", self.category_combo)
            form_layout.addRow("Описание:", self.description_edit)
            form_layout.addRow("Дата:", self.date_edit)
            form_layout.addRow(add_btn)
            
            # Статистика
            stats_group = QGroupBox("Финансовая сводка")
            stats_layout = QVBoxLayout(stats_group)
            
            self.income_label = QLabel("Доходы: 0.00 ₽")
            self.income_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            
            self.expense_label = QLabel("Расходы: 0.00 ₽")
            self.expense_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            
            self.balance_label = QLabel("Баланс: 0.00 ₽")
            self.balance_label.setStyleSheet("color: #3498db; font-weight: bold; font-size: 16px;")
            
            stats_layout.addWidget(self.income_label)
            stats_layout.addWidget(self.expense_label)
            stats_layout.addWidget(self.balance_label)
            stats_layout.addStretch()
            
            # Быстрые кнопки
            quick_btns = QWidget()
            quick_layout = QVBoxLayout(quick_btns)
            
            export_btn = QPushButton("📤 Экспорт данных")
            export_btn.clicked.connect(self.export_data)
            
            clear_btn = QPushButton("🗑️ Очистить все")
            clear_btn.setStyleSheet("background-color: #e74c3c;")
            clear_btn.clicked.connect(self.clear_all_data)
            
            quick_layout.addWidget(export_btn)
            quick_layout.addWidget(clear_btn)
            
            # Добавляем виджеты в левую панель
            left_layout.addWidget(form_group)
            left_layout.addWidget(stats_group)
            left_layout.addWidget(quick_btns)
            left_layout.addStretch()
            
            # Правая панель с вкладками
            right_panel = QTabWidget()
            
            # Вкладка 1: Транзакции
            transactions_tab = QWidget()
            trans_layout = QVBoxLayout(transactions_tab)
            
            # Панель управления таблицей
            table_controls = QHBoxLayout()
            
            filter_label = QLabel("Фильтр:")
            self.filter_combo = QComboBox()
            self.filter_combo.addItems(["Все", "Доходы", "Расходы"] + self.categories)
            self.filter_combo.currentTextChanged.connect(self.update_transactions_table)
            
            delete_btn = QPushButton("🗑️ Удалить выбранное")
            delete_btn.clicked.connect(self.delete_selected)
            delete_btn.setStyleSheet("background-color: #e74c3c;")
            
            table_controls.addWidget(filter_label)
            table_controls.addWidget(self.filter_combo)
            table_controls.addStretch()
            table_controls.addWidget(delete_btn)
            
            # Таблица транзакций
            self.table = QTableWidget()
            self.table.setColumnCount(5)
            self.table.setHorizontalHeaderLabels(["Дата", "Тип", "Категория", "Сумма", "Описание"])
            self.table.horizontalHeader().setStretchLastSection(True)
            self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            
            trans_layout.addLayout(table_controls)
            trans_layout.addWidget(self.table)
            
            # Вкладка 2: Аналитика
            analytics_tab = QWidget()
            analytics_layout = QVBoxLayout(analytics_tab)
            
            self.analytics_text = QTextEdit()
            self.analytics_text.setReadOnly(True)
            self.analytics_text.setMinimumHeight(300)
            
            analytics_layout.addWidget(QLabel("📈 Анализ расходов"))
            analytics_layout.addWidget(self.analytics_text)
            
            # Вкладка 3: Категории
            categories_tab = QWidget()
            categories_layout = QVBoxLayout(categories_tab)
            
            categories_info = QTextEdit()
            categories_info.setReadOnly(True)
            categories_info.setText(
                "💰 Категории расходов:\n\n"
                "• Еда - продукты питания, кафе, рестораны\n"
                "• Транспорт - бензин, такси, общественный транспорт\n"
                "• Жилье - аренда, коммунальные услуги\n"
                "• Развлечения - кино, концерты, хобби\n"
                "• Здоровье - медицина, спорт, витамины\n"
                "• Одежда - одежда, обувь, аксессуары\n"
                "• Образование - курсы, книги\n"
                "• Другое - прочие расходы\n\n"
                "💡 Совет: Регулярно проверяйте расходы по категориям!"
            )
            
            categories_layout.addWidget(categories_info)
            
            # Добавляем вкладки
            right_panel.addTab(transactions_tab, "📋 Транзакции")
            right_panel.addTab(analytics_tab, "📊 Аналитика")
            right_panel.addTab(categories_tab, "🏷️ Категории")
            
            # Добавляем панели в главный макет
            main_layout.addWidget(left_panel, 1)
            main_layout.addWidget(right_panel, 2)
            
            # Обновляем интерфейс
            self.update_ui()
            
        except Exception as e:
            print(f"Ошибка инициализации UI: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать интерфейс: {e}")
            
    def add_transaction(self):
        try:
            amount_text = self.amount_edit.text().replace(',', '.').strip()
            if not amount_text:
                QMessageBox.warning(self, "Ошибка", "Введите сумму!")
                return
                
            amount = float(amount_text)
            if amount <= 0:
                QMessageBox.warning(self, "Ошибка", "Сумма должна быть больше 0!")
                return
                
            description = self.description_edit.text().strip()
            if not description:
                description = "Без описания"
                
            transaction = {
                "id": len(self.transactions) + 1,
                "date": self.date_edit.date().toString("yyyy-MM-dd"),
                "type": self.type_combo.currentText(),
                "category": self.category_combo.currentText(),
                "amount": round(amount, 2),
                "description": description
            }
            
            self.transactions.append(transaction)
            self.save_data()
            self.update_ui()
            
            # Сброс полей ввода
            self.amount_edit.clear()
            self.description_edit.clear()
            
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Введите корректную сумму!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить транзакцию: {e}")
            
    def update_ui(self):
        try:
            self.update_transactions_table()
            self.update_statistics()
            self.update_analytics()
        except Exception as e:
            print(f"Ошибка обновления UI: {e}")
            
    def update_transactions_table(self):
        try:
            filter_text = self.filter_combo.currentText()
            
            # Фильтрация транзакций
            filtered = self.transactions
            if filter_text == "Доходы":
                filtered = [t for t in self.transactions if t["type"] == "Доход"]
            elif filter_text == "Расходы":
                filtered = [t for t in self.transactions if t["type"] == "Расход"]
            elif filter_text != "Все":
                filtered = [t for t in self.transactions if t["category"] == filter_text]
            
            self.table.setRowCount(len(filtered))
            
            for i, transaction in enumerate(filtered):
                # Дата
                date_item = QTableWidgetItem(transaction["date"])
                
                # Тип
                type_item = QTableWidgetItem(transaction["type"])
                if transaction["type"] == "Доход":
                    type_item.setForeground(QColor("#27ae60"))
                else:
                    type_item.setForeground(QColor("#e74c3c"))
                
                # Категория
                category_item = QTableWidgetItem(transaction["category"])
                
                # Сумма
                amount_item = QTableWidgetItem(f"{transaction['amount']:.2f} ₽")
                amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if transaction["type"] == "Доход":
                    amount_item.setForeground(QColor("#27ae60"))
                else:
                    amount_item.setForeground(QColor("#e74c3c"))
                
                # Описание
                desc_item = QTableWidgetItem(transaction["description"])
                
                self.table.setItem(i, 0, date_item)
                self.table.setItem(i, 1, type_item)
                self.table.setItem(i, 2, category_item)
                self.table.setItem(i, 3, amount_item)
                self.table.setItem(i, 4, desc_item)
            
            self.table.resizeColumnsToContents()
            
        except Exception as e:
            print(f"Ошибка обновления таблицы: {e}")
            
    def update_statistics(self):
        try:
            total_income = sum(t["amount"] for t in self.transactions if t["type"] == "Доход")
            total_expense = sum(t["amount"] for t in self.transactions if t["type"] == "Расход")
            balance = total_income - total_expense
            
            self.income_label.setText(f"Доходы: {total_income:.2f} ₽")
            self.expense_label.setText(f"Расходы: {total_expense:.2f} ₽")
            self.balance_label.setText(f"Баланс: {balance:.2f} ₽")
            
        except Exception as e:
            print(f"Ошибка обновления статистики: {e}")
            
    def update_analytics(self):
        try:
            if not self.transactions:
                self.analytics_text.setText("Нет данных для анализа")
                return
                
            analytics = "📊 ФИНАНСОВЫЙ АНАЛИЗ\n\n"
            
            # Общая статистика
            total_income = sum(t["amount"] for t in self.transactions if t["type"] == "Доход")
            total_expense = sum(t["amount"] for t in self.transactions if t["type"] == "Расход")
            
            analytics += f"Всего доходов: {total_income:.2f} ₽\n"
            analytics += f"Всего расходов: {total_expense:.2f} ₽\n"
            analytics += f"Текущий баланс: {total_income - total_expense:.2f} ₽\n\n"
            
            if total_income > 0:
                savings_rate = ((total_income - total_expense) / total_income) * 100
                analytics += f"Норма сбережений: {savings_rate:.1f}%\n"
                
                if savings_rate < 0:
                    analytics += "⚠️  Ваши расходы превышают доходы!\n"
                elif savings_rate < 10:
                    analytics += "💡  Старайтесь откладывать больше\n"
                elif savings_rate < 20:
                    analytics += "👍  Хороший уровень сбережений\n"
                else:
                    analytics += "🎉  Отличные сбережения!\n"
            
            # Анализ по категориям расходов
            analytics += "\n📋 РАСХОДЫ ПО КАТЕГОРИЯМ:\n\n"
            
            expense_by_category = {}
            for t in self.transactions:
                if t["type"] == "Расход":
                    expense_by_category[t["category"]] = expense_by_category.get(t["category"], 0) + t["amount"]
            
            if expense_by_category:
                for category, amount in sorted(expense_by_category.items(), key=lambda x: x[1], reverse=True):
                    if total_expense > 0:
                        percent = (amount / total_expense) * 100
                        analytics += f"• {category}: {amount:.2f} ₽ ({percent:.1f}%)\n"
                    else:
                        analytics += f"• {category}: {amount:.2f} ₽\n"
                
                # Находим самую затратную категорию
                top_category = max(expense_by_category.items(), key=lambda x: x[1])
                analytics += f"\n💸 Самые большие расходы: {top_category[0]} ({top_category[1]:.2f} ₽)\n"
            
            self.analytics_text.setText(analytics)
            
        except Exception as e:
            print(f"Ошибка обновления аналитики: {e}")
            
    def delete_selected(self):
        try:
            selected_rows = set()
            for item in self.table.selectedItems():
                selected_rows.add(item.row())
            
            if not selected_rows:
                QMessageBox.warning(self, "Внимание", "Выберите строки для удаления")
                return
                
            reply = QMessageBox.question(
                self, "Подтверждение",
                f"Удалить {len(selected_rows)} транзакций?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Получаем даты выбранных транзакций для идентификации
                dates_to_delete = []
                for row in sorted(selected_rows, reverse=True):
                    date_item = self.table.item(row, 0)
                    if date_item:
                        dates_to_delete.append(date_item.text())
                
                # Удаляем транзакции
                self.transactions = [t for t in self.transactions if t["date"] not in dates_to_delete]
                
                # Обновляем ID
                for i, t in enumerate(self.transactions, 1):
                    t["id"] = i
                
                self.save_data()
                self.update_ui()
                QMessageBox.information(self, "Успех", "Транзакции удалены!")
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось удалить транзакции: {e}")
            
    def clear_all_data(self):
        try:
            if not self.transactions:
                QMessageBox.information(self, "Информация", "Нет данных для очистки")
                return
                
            reply = QMessageBox.question(
                self, "Подтверждение",
                "УДАЛИТЬ ВСЕ ДАННЫЕ?\nЭто действие нельзя отменить!",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.transactions = []
                self.save_data()
                self.update_ui()
                QMessageBox.information(self, "Успех", "Все данные удалены!")
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось очистить данные: {e}")
            
    def export_data(self):
        try:
            if not self.transactions:
                QMessageBox.warning(self, "Внимание", "Нет данных для экспорта")
                return
                
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Экспорт данных",
                os.path.join(self.data_dir, "budget_export.json"),
                "JSON файлы (*.json);;Текстовые файлы (*.txt)"
            )
            
            if file_path:
                if file_path.endswith('.json'):
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(self.transactions, f, ensure_ascii=False, indent=2)
                else:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write("Дата\tТип\tКатегория\tСумма\tОписание\n")
                        for t in self.transactions:
                            f.write(f"{t['date']}\t{t['type']}\t{t['category']}\t{t['amount']}\t{t['description']}\n")
                
                QMessageBox.information(self, "Успех", f"Данные экспортированы в:\n{file_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось экспортировать данные: {e}")
            
    def save_data(self):
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.transactions, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения: {e}")
            
    def load_data(self):
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.transactions = json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки: {e}")
            self.transactions = []

def main():
    try:
        app = QApplication(sys.argv)
        app.setStyle('Fusion')  # Более современный стиль
        
        window = BudgetApp()
        window.show()
        
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        QMessageBox.critical(None, "Ошибка", f"Не удалось запустить программу:\n{e}")
        
        # Создаем простое окно с ошибкой
        simple_app = QApplication([])
        error_window = QWidget()
        layout = QVBoxLayout(error_window)
        layout.addWidget(QLabel(f"Ошибка запуска: {e}"))
        layout.addWidget(QLabel("Убедитесь, что установлен PyQt5: pip install pyqt5"))
        error_window.show()
        simple_app.exec_()

if __name__ == "__main__":
    main()