import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QLabel, QGroupBox, QFormLayout, QScrollArea)
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtCore import Qt

class PersonalIntroWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("个人电子简介")
        self.setFixedSize(800, 900)  # 固定窗口大小，适配所有信息
        self.setWindowIcon(QIcon())  # 可替换为自定义图标
        
        # 主容器与布局
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # 1. 标题栏
        title_label = QLabel("个人电子简介")
        title_label.setFont(QFont("微软雅黑", 24, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        main_layout.addWidget(title_label)

        # 2. 基础信息分组
        basic_group = QGroupBox("📌 基础信息")
        basic_group.setFont(QFont("微软雅黑", 14, QFont.Bold))
        basic_layout = QFormLayout()
        basic_layout.setSpacing(15)
        basic_layout.setContentsMargins(20, 20, 20, 20)

        basic_info = {
            "昵称": "缃缘.",
            "性别": "女",
            "生日": "2011-05-31",
            "星座": "双子座",
            "年龄": "14岁",
            "所在地": "贵州",
            "家乡": "贵州",
            "IP属地": "贵州",
            "个人签名": "ygkycxksjhl°-∧-°",
            "QQ个性签名": "也许有一天 你不再记得我 不过没关系 我也打算把你忘..."
        }

        for key, value in basic_info.items():
            label = QLabel(f"{key}：")
            label.setFont(QFont("微软雅黑", 12))
            value_label = QLabel(value)
            value_label.setFont(QFont("微软雅黑", 12))
            value_label.setWordWrap(True)
            basic_layout.addRow(label, value_label)

        basic_group.setLayout(basic_layout)
        main_layout.addWidget(basic_group)

        # 3. 游戏账号分组（单独列出，按要求）
        game_group = QGroupBox("🎮 游戏账号")
        game_group.setFont(QFont("微软雅黑", 14, QFont.Bold))
        game_layout = QFormLayout()
        game_layout.setSpacing(15)
        game_layout.setContentsMargins(20, 20, 20, 20)

        game_accounts = {
            "和平精英": "若可以续缘",
            "王者荣耀": "若可以续缘"
        }

        for game, account in game_accounts.items():
            label = QLabel(f"{game}：")
            label.setFont(QFont("微软雅黑", 12))
            account_label = QLabel(account)
            account_label.setFont(QFont("微软雅黑", 12, QFont.Bold))
            game_layout.addRow(label, account_label)

        game_group.setLayout(game_layout)
        main_layout.addWidget(game_group)

        # 4. 社交账号分组
        social_group = QGroupBox("📱 社交账号")
        social_group.setFont(QFont("微软雅黑", 14, QFont.Bold))
        social_layout = QFormLayout()
        social_layout.setSpacing(15)
        social_layout.setContentsMargins(20, 20, 20, 20)

        social_info = {
            "快手昵称": "缃缘.",
            "快手号": "XNL2011531",
            "QQ昵称": "若可以续缘😭",
            "QQ号": "1978365119",
            "联系电话": "15772557427"
        }

        for key, value in social_info.items():
            label = QLabel(f"{key}：")
            label.setFont(QFont("微软雅黑", 12))
            value_label = QLabel(value)
            value_label.setFont(QFont("微软雅黑", 12))
            social_layout.addRow(label, value_label)

        social_group.setLayout(social_layout)
        main_layout.addWidget(social_group)

        # 5. 兴趣爱好分组
        hobby_group = QGroupBox("✨ 兴趣爱好")
        hobby_group.setFont(QFont("微软雅黑", 14, QFont.Bold))
        hobby_layout = QVBoxLayout()
        hobby_layout.setSpacing(10)
        hobby_layout.setContentsMargins(20, 20, 20, 20)

        hobbies = ["王者荣耀", "和平精英（吃鸡）", "本性乖"]
        hobby_text = " | ".join(hobbies)
        hobby_label = QLabel(hobby_text)
        hobby_label.setFont(QFont("微软雅黑", 12))
        hobby_label.setAlignment(Qt.AlignCenter)
        hobby_layout.addWidget(hobby_label)

        hobby_group.setLayout(hobby_layout)
        main_layout.addWidget(hobby_group)

        # 6. 底部署名
        footer_label = QLabel("感谢查看 ~")
        footer_label.setFont(QFont("微软雅黑", 14))
        footer_label.setAlignment(Qt.AlignCenter)
        footer_label.setStyleSheet("color: #7f8c8d; margin-top: 10px;")
        main_layout.addWidget(footer_label)

        # 滚动区域（适配小屏幕）
        scroll_area = QScrollArea()
        scroll_area.setWidget(main_widget)
        scroll_area.setWidgetResizable(True)
        self.setCentralWidget(scroll_area)

        # 全局样式美化
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QGroupBox {
                border: 2px solid #dee2e6;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px;
                color: #2c3e50;
            }
            QLabel {
                color: #2c3e50;
            }
        """)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PersonalIntroWindow()
    window.show()
    sys.exit(app.exec_())