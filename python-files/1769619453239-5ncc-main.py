import sys
import os
import re
from PyQt5 import uic  # или from PyQt6 import uic
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog  # Импортируем QFileDialog!
from PyQt5 import QtCore, QtGui, QtWidgets
def is_valid_unix_path(path: str) -> bool:
    pattern = r'^[a-zA-Z]:\\(?:[^\\/:*?"<>|\r\n]+\\)*[^\\/:*?"<>|\r\n]*$'  # Начинается с /, затем сегменты через /
    return re.match(pattern, path) is not None

from PyQt5 import QtCore, QtGui, QtWidgets
class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1041, 791)
        MainWindow.setMinimumSize(QtCore.QSize(840, 630))

        # Центральный виджет
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        # Основной вертикальный макет
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSpacing(10)

        # === Верхняя секция: строка с полем ввода и кнопкой ===
        self.gridLayoutWidget = QtWidgets.QWidget()
        self.gridLayoutWidget.setObjectName("gridLayoutWidget")

        self.gridLayout = QtWidgets.QGridLayout(self.gridLayoutWidget)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setSpacing(5)

        # Поле ввода (textEdit_2)
        self.textEdit_2 = QtWidgets.QTextEdit()
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setVerticalStretch(0)
        self.textEdit_2.setSizePolicy(sizePolicy)
        self.textEdit_2.setMaximumHeight(20)  # Фиксированная высота
        font = QtGui.QFont()
        font.setPointSize(10)
        self.textEdit_2.setFont(font)
        self.textEdit_2.setObjectName("textEdit_2")
        self.gridLayout.addWidget(self.textEdit_2, 0, 0, 1, 1)

        # Кнопка (pushButton_2)
        self.pushButton_2 = QtWidgets.QPushButton()
        self.pushButton_2.setObjectName("pushButton_2")
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        self.pushButton_2.setSizePolicy(sizePolicy)
        self.gridLayout.addWidget(self.pushButton_2, 0, 1, 1, 1)

        # Метка "Ищем из файла:"
        self.label_6 = QtWidgets.QLabel()
        self.label_6.setObjectName("label_6")
        self.gridLayout.addWidget(self.label_6, 1, 0, 1, 2)

        # Добавляем верхнюю секцию в основной макет
        self.verticalLayout.addWidget(self.gridLayoutWidget)

        # Метка "Всего файлов:" (над верхней секцией)
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setObjectName("label_2")
        self.verticalLayout.insertWidget(0, self.label_2)


        # === Нижняя секция: два текстовых браузера ===
        self.gridLayoutWidget_2 = QtWidgets.QWidget()
        self.gridLayoutWidget_2.setObjectName("gridLayoutWidget_2")

        self.gridLayout_2 = QtWidgets.QGridLayout(self.gridLayoutWidget_2)
        self.gridLayout_2.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_2.setSpacing(10)

        # Метка "Найдено:"
        self.label_4 = QtWidgets.QLabel()
        self.label_4.setObjectName("label_4")
        self.gridLayout_2.addWidget(self.label_4, 0, 0, 1, 1)

        # Метка "Не найдено:"
        self.label_5 = QtWidgets.QLabel()
        self.label_5.setObjectName("label_5")
        self.gridLayout_2.addWidget(self.label_5, 0, 1, 1, 1)

        # Текстовый браузер (слева)
        self.textBrowser = QtWidgets.QTextBrowser()
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.textBrowser.setSizePolicy(sizePolicy)
        self.textBrowser.setObjectName("textBrowser")
        self.gridLayout_2.addWidget(self.textBrowser, 1, 0, 1, 1)

        # Текстовый браузер (справа)
        self.textBrowser_2 = QtWidgets.QTextBrowser()
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.textBrowser_2.setSizePolicy(sizePolicy)
        self.textBrowser_2.setObjectName("textBrowser_2")
        self.gridLayout_2.addWidget(self.textBrowser_2, 1, 1, 1, 1)

        # Растягиваем колонки (левая и правая — поровну)
        self.gridLayout_2.setColumnStretch(0, 1)
        self.gridLayout_2.setColumnStretch(1, 1)
        # Растягиваем строку с браузерами (основной объём)
        self.gridLayout_2.setRowStretch(1, 1)

        # Добавляем нижнюю секцию в основной макет (с растяжением)
        self.verticalLayout.addWidget(self.gridLayoutWidget_2, stretch=1)

        MainWindow.setCentralWidget(self.centralwidget)

        # Меню и статусбар
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1041, 21))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)

        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.pushButton_2.setText(_translate("MainWindow", "Обзор"))
        self.label_6.setText(_translate("MainWindow", "Всего файлов:"))
        self.label_4.setText(_translate("MainWindow", "Найдено:"))
        self.label_5.setText(_translate("MainWindow", "Не найдено:"))
        self.label_2.setText(_translate("MainWindow", "Ищем из файла::"))


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.pushButton_2.clicked.connect(self.browse_file)
    def browse_file(self):
        """Обработчик кнопки: выбор .txt-файла и чтение его содержимого"""
        # Открываем диалог выбора файла
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите текстовый файл",
            "",
            "Текстовые файлы (*.txt);;Все файлы (*)"
        )
        if file_path:
            # Помещаем путь в QTextEdit (как в вашем интерфейсе)
            self.textEdit_2.setText(file_path)
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    data = content.split("\n")
                    c, ex, nex = 0,0,0
                    for i in data:
                        if is_valid_unix_path(i): c += 1                     
                    not_exist = []
                    exist = []
                    for i in data:
                        if not os.path.isfile(i):
                            not_exist.append(i)
                            nex += 1
                        else:
                            ex += 1
                            exist.append(i)
                    self.label_6.setText(f"Всего файлов: {c}")    
                    self.label_4.setText(f"Найдено: {ex}")    
                    self.label_5.setText(f"Не найдено: {nex}")    
                    self.textBrowser.setPlainText('\n'.join(exist))
                    self.textBrowser_2.setPlainText('\n'.join(not_exist))
                    print('\n'.join(not_exist))
            except Exception as e:
                self.textBrowser.setPlainText(f"Ошибка при чтении файла:\n{str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())