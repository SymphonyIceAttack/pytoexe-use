from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QGridLayout, QWidget, QVBoxLayout, QHBoxLayout
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
from PyQt6.QtCore import QFile, QTextStream, QIODevice



class Window(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setMinimumSize (500,500)
        self.setWindowTitle ("Мероприятия и экскурсии")
        self.setWindowIcon(QIcon("D:\Документы\Настя\проект\эмблема.png"))

        parentlayout = QGridLayout() #большой макет

        # "начинка" приложения
        self.l1 = QLabel("Мероприятия в Содружестве", alignment=Qt.AlignmentFlag.AlignHCenter)
        self.l1.setFixedHeight(50)
        font = self.font()
        font.setPointSize(25)
        font.setBold(False)
        self.l1.setFont(font)

        #window.setCentralWidget(l1)

        parentlayout.addWidget(self.l1)

        #текст файла
        file = QFile("D:\Documents\Anastasya\project\\file.txt")
        file.OpenModeFlag
        if not file.open(QIODevice.OpenModeFlag.ReadOnly | QIODevice.OpenModeFlag.Text):  
            print("не открыть")
        f= QTextStream(file) 

        
        #заголовок 
        line = f.readLine()
        self.l2 = QLabel(line, alignment=Qt.AlignmentFlag.AlignLeft)
        self.l2.setMaximumHeight(25)
        #window.setCentralWidget(l2)
        font = self.font()
        font.setPointSize(15)
        font.setBold(True)
        self.l2.setFont(font)


        parentlayout.addWidget(self.l2)

        #содержимое
        line2 = f.readAll()
        self.l3= QLabel(line2, alignment=Qt.AlignmentFlag.AlignLeft)
        font = self.font()
        font.setPointSize(10)
        font.setBold(False)
        self.l3.setFont(font)



        parentlayout.addWidget(self.l3)


        # кнопка на яндекс формы
        self.l4 = QLabel ("зарегистрироваться на мероприятие", alignment=Qt.AlignmentFlag.AlignBaseline)
        self.l4.setMaximumHeight(25)
        self.l4.setText('<a href="https://forms.yandex.ru/u/69712dec49af47ee8b983b08"> зарег на мероприятие </a>')
        parentlayout.addWidget(self.l4)
        self.l4.setOpenExternalLinks(True)

        #parentlayout.setRowMinimumHeight(1,200)

        self.setCentralWidget(self.l4)

        centreWidget = QWidget()

        centreWidget.setLayout(parentlayout)

        self.setCentralWidget(centreWidget)
    
        





app = QApplication([])
window = Window()


window.show ()
app.exec()
