import sys
import os
import platform
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout,
    QPushButton, QLabel, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer

# 你的网络共享路径（保持不变）
TARGET_FOLDER = r"\\file.himile.com\共享磁盘\豪迈制造\深海装备市场经营部\GYY2-B-(深海装备市场经营部)经营数据"

class SharedFolderOpener(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        QTimer.singleShot(300, self.open_target_folder)

    def initUI(self):
        self.setWindowTitle('打开经营数据共享文件夹')
        self.setGeometry(200, 200, 360, 160)
        main_layout = QVBoxLayout()

        title_label = QLabel('深海装备市场经营部\n经营数据共享文件夹')
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size:15px; font-weight:bold; margin:15px;")
        main_layout.addWidget(title_label)

        open_btn = QPushButton('打开共享文件夹')
        open_btn.setStyleSheet("padding:9px; font-size:14px;")
        open_btn.clicked.connect(self.open_target_folder)
        main_layout.addWidget(open_btn)

        self.setLayout(main_layout)

    def open_target_folder(self):
        try:
            if platform.system() == 'Windows':
                os.startfile(TARGET_FOLDER)
            else:
                os.startfile(TARGET_FOLDER)

            # 延迟关闭窗口，保证资源管理器正常打开
            QTimer.singleShot(500, self.close)
        except Exception as e:
            QMessageBox.warning(self, '打开失败', 
                f'无法打开共享文件夹\n请检查：\n1. 网络是否正常\n2. 是否有权限\n3. VPN 是否连接')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SharedFolderOpener()
    window.show()
    sys.exit(app.exec_())