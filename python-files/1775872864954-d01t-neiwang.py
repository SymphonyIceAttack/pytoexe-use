import sys
import os
import platform
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout,
    QPushButton, QLabel, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer

# 目标共享文件夹路径
TARGET_FOLDER = r"\\file.himile.com\共享磁盘\豪迈制造\深海装备市场经营部\GYY2-B-(深海装备市场经营部)经营数据"

class SharedFolderOpener(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        # 程序启动后自动尝试打开文件夹
        QTimer.singleShot(500, self.open_target_folder)

    def initUI(self):
        # 极简窗口设置
        self.setWindowTitle('经营数据文件夹')
        self.setGeometry(200, 200, 350, 150)
        main_layout = QVBoxLayout()
        
        # 仅保留核心标题
        title_label = QLabel('深海装备经营数据文件夹')
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 20px;")
        main_layout.addWidget(title_label)
        
        # 手动打开按钮（极简样式）
        open_btn = QPushButton('打开文件夹')
        open_btn.setStyleSheet("padding: 8px; font-size: 14px;")
        open_btn.clicked.connect(self.open_target_folder)
        main_layout.addWidget(open_btn)
        
        self.setLayout(main_layout)

    def open_target_folder(self):
        """核心打开逻辑：成功无提示，失败仅极简提示"""
        # 基础路径校验
        if not os.path.exists(TARGET_FOLDER) or not os.path.isdir(TARGET_FOLDER):
            QMessageBox.critical(self, '错误', '打开失败')
            return
        
        # 打开文件夹（成功无提示，直接调系统打开文件夹窗口）
        try:
            if platform.system() == 'Windows':
                os.startfile(TARGET_FOLDER)
                # 打开成功后自动关闭程序窗口（可选，如需保留窗口可删除这行）
                self.close()
            elif platform.system() == 'Darwin':
                os.system(f'open "{TARGET_FOLDER}"')
                self.close()
            else:
                os.system(f'xdg-open "{TARGET_FOLDER}"')
                self.close()
        except Exception:
            QMessageBox.critical(self, '错误', '打开失败')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SharedFolderOpener()
    window.show()
    sys.exit(app.exec_())