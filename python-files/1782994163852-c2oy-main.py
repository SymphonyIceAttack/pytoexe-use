import sys
import os
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                            QListWidget, QListWidgetItem, QMessageBox, 
                            QTextEdit, QMenuBar, QAction, QFileDialog, QSlider,
                            QCheckBox, QFrame, QSizePolicy, QToolButton)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSettings, QSize, QByteArray
from PyQt5.QtGui import QFont, QIcon, QColor, QTextCursor, QPainter, QPixmap, QCursor
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import QGraphicsDropShadowEffect
import requests
import socketio

ICON_SVGS = {
    'user': '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>''',
    'lock': '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>''',
    'eye': '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"/><circle cx="12" cy="12" r="3"/></svg>''',
    'eye-off': '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"/><path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"/><path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"/><line x1="2" x2="22" y1="2" y2="22"/></svg>''',
    'tv': '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="15" x="2" y="7" rx="2" ry="2"/><polyline points="17 2 12 7 7 2"/></svg>''',
    'refresh': '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/></svg>''',
    'pin': '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 17v5"/><path d="M9 10.76a2 2 0 0 1-1.11 1.79l-1.78.9A2 2 0 0 0 5 15.24V16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-.76a2 2 0 0 0-1.11-1.79l-1.78-.9A2 2 0 0 1 15 10.76V7a1 1 0 0 1 1-1 2 2 0 0 0 0-4H8a2 2 0 0 0 0 4 1 1 0 0 1 1 1z"/></svg>''',
    'arrow-right': '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>''',
    'logout': '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" x2="9" y1="12" y2="12"/></svg>''',
    'home': '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>''',
    'trash': '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>''',
    'type': '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 7 4 4 20 4 20 7"/><line x1="9" x2="15" y1="20" y2="20"/><line x1="12" x2="12" y1="4" y2="20"/></svg>''',
    'sun': '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg>''',
}

def create_icon(name, color="#64748b", size=18):
    """从SVG字符串创建QIcon"""
    svg_str = ICON_SVGS.get(name, '')
    if not svg_str:
        return QIcon()
    
    svg_str = svg_str.replace('currentColor', color)
    
    renderer = QSvgRenderer(QByteArray(svg_str.encode('utf-8')))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    
    return QIcon(pixmap)

def add_shadow(widget, blur_radius=20, x_offset=0, y_offset=4, color=QColor(0, 0, 0, 25)):
    """给控件添加阴影效果"""
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur_radius)
    shadow.setXOffset(x_offset)
    shadow.setYOffset(y_offset)
    shadow.setColor(color)
    widget.setGraphicsEffect(shadow)

class LoginWindow(QWidget):
    """登录窗口"""
    login_success = pyqtSignal(dict)
    
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setWindowTitle("登录 - 千盈助播")
        self.setGeometry(100, 100, 420, 520)
        self.setMinimumSize(380, 480)
        self.center()
        
        try:
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ico.ico")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
            else:
                import sys
                if hasattr(sys, '_MEIPASS'):
                    icon_path = os.path.join(sys._MEIPASS, "ico.ico")
                    if os.path.exists(icon_path):
                        self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            pass
        
        self.settings = QSettings("QYZB", "助播提词器")
        self.is_logging_in = False
        self.password_visible = False
        
        self.setStyleSheet("""
            LoginWindow {
                background-color: #f1f5f9;
            }
            QLabel {
                font-family: '微软雅黑', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            #cardWidget {
                background-color: #ffffff;
                border-radius: 16px;
            }
            #titleLabel {
                color: #0f172a;
                font-size: 24px;
                font-weight: bold;
            }
            #subtitleLabel {
                color: #64748b;
                font-size: 14px;
                font-weight: normal;
            }
            #inputContainer {
                background-color: #ffffff;
                border: 1.5px solid #e2e8f0;
                border-radius: 10px;
            }
            #inputContainer:focus {
                border: 1.5px solid #2563eb;
            }
            #inputField {
                background-color: transparent;
                border: none;
                padding: 0px;
                font-size: 14px;
                color: #1e293b;
            }
            #inputField:focus {
                border: none;
                outline: none;
            }
            #iconBtn {
                background-color: transparent;
                border: none;
                padding: 0px;
            }
            #iconBtn:hover {
                background-color: transparent;
            }
            #loginBtn {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px 24px;
                font-size: 15px;
                font-weight: 600;
            }
            #loginBtn:hover {
                background-color: #1d4ed8;
            }
            #loginBtn:pressed {
                background-color: #1e40af;
            }
            #loginBtn:disabled {
                background-color: #93c5fd;
                color: #dbeafe;
            }
            QCheckBox {
                color: #475569;
                font-size: 13px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1.5px solid #cbd5e1;
                border-radius: 4px;
                background-color: white;
            }
            QCheckBox::indicator:hover {
                border-color: #2563eb;
            }
            QCheckBox::indicator:checked {
                background-color: #2563eb;
                border-color: #2563eb;
                image: none;
            }
            #errorLabel {
                color: #dc2626;
                background: #fef2f2;
                border: 1px solid #fecaca;
                padding: 10px 12px;
                border-radius: 8px;
                font-size: 13px;
            }
            #copyrightLabel {
                color: #94a3b8;
                font-size: 12px;
                font-weight: normal;
            }
            #fieldLabel {
                color: #334155;
                font-size: 13px;
                font-weight: 500;
            }
        """)
        
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(40, 40, 40, 40)
        outer_layout.setSpacing(0)
        
        card = QWidget()
        card.setObjectName("cardWidget")
        add_shadow(card, blur_radius=40, y_offset=8, color=QColor(0, 0, 0, 20))
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(36, 36, 36, 32)
        card_layout.setSpacing(0)
        
        title_label = QLabel("千盈房产助播")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(title_label)
        
        subtitle_label = QLabel("登录您的账号以继续")
        subtitle_label.setObjectName("subtitleLabel")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setContentsMargins(0, 6, 0, 28)
        card_layout.addWidget(subtitle_label)
        
        form_layout = QVBoxLayout()
        form_layout.setSpacing(16)
        
        username_label = QLabel("用户名")
        username_label.setObjectName("fieldLabel")
        form_layout.addWidget(username_label)
        
        username_container = QWidget()
        username_container.setObjectName("inputContainer")
        username_container.setFixedHeight(44)
        username_layout = QHBoxLayout(username_container)
        username_layout.setContentsMargins(12, 0, 12, 0)
        username_layout.setSpacing(10)
        
        user_icon_label = QLabel()
        user_icon_label.setPixmap(create_icon('user', '#94a3b8', 18).pixmap(18, 18))
        user_icon_label.setFixedSize(18, 18)
        username_layout.addWidget(user_icon_label)
        
        self.username_input = QLineEdit()
        self.username_input.setObjectName("inputField")
        self.username_input.setPlaceholderText("请输入用户名")
        self.username_input.setAttribute(Qt.WA_MacShowFocusRect, False)
        username_layout.addWidget(self.username_input, 1)
        
        form_layout.addWidget(username_container)
        
        password_label = QLabel("密码")
        password_label.setObjectName("fieldLabel")
        form_layout.addWidget(password_label)
        
        password_container = QWidget()
        password_container.setObjectName("inputContainer")
        password_container.setFixedHeight(44)
        password_layout = QHBoxLayout(password_container)
        password_layout.setContentsMargins(12, 0, 8, 0)
        password_layout.setSpacing(10)
        
        lock_icon_label = QLabel()
        lock_icon_label.setPixmap(create_icon('lock', '#94a3b8', 18).pixmap(18, 18))
        lock_icon_label.setFixedSize(18, 18)
        password_layout.addWidget(lock_icon_label)
        
        self.password_input = QLineEdit()
        self.password_input.setObjectName("inputField")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("请输入密码")
        self.password_input.setAttribute(Qt.WA_MacShowFocusRect, False)
        password_layout.addWidget(self.password_input, 1)
        
        self.toggle_password_btn = QPushButton()
        self.toggle_password_btn.setObjectName("iconBtn")
        self.toggle_password_btn.setIcon(create_icon('eye', '#64748b', 18))
        self.toggle_password_btn.setIconSize(QSize(18, 18))
        self.toggle_password_btn.setFixedSize(32, 32)
        self.toggle_password_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_password_btn.clicked.connect(self.toggle_password_visibility)
        password_layout.addWidget(self.toggle_password_btn)
        
        form_layout.addWidget(password_container)
        
        card_layout.addLayout(form_layout)
        
        options_layout = QHBoxLayout()
        options_layout.setContentsMargins(0, 14, 0, 22)
        self.remember_checkbox = QCheckBox("记住密码")
        self.remember_checkbox.setCursor(Qt.PointingHandCursor)
        options_layout.addWidget(self.remember_checkbox)
        options_layout.addStretch()
        card_layout.addLayout(options_layout)
        
        self.login_button = QPushButton("登 录")
        self.login_button.setObjectName("loginBtn")
        self.login_button.setFixedHeight(46)
        self.login_button.setCursor(Qt.PointingHandCursor)
        self.login_button.clicked.connect(self.login)
        card_layout.addWidget(self.login_button)
        
        self.error_label = QLabel("")
        self.error_label.setObjectName("errorLabel")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setVisible(False)
        self.error_label.setContentsMargins(0, 14, 0, 0)
        card_layout.addWidget(self.error_label)
        
        card_layout.addStretch()
        
        copyright_label = QLabel("千盈房产 © 2026")
        copyright_label.setObjectName("copyrightLabel")
        copyright_label.setAlignment(Qt.AlignCenter)
        copyright_label.setContentsMargins(0, 16, 0, 0)
        card_layout.addWidget(copyright_label)
        
        outer_layout.addWidget(card)
        outer_layout.addStretch()
        
        self.load_saved_credentials()
        self.username_input.setFocus()
        
        self.username_input.textChanged.connect(lambda: self.update_container_border(username_container, self.username_input))
        self.password_input.textChanged.connect(lambda: self.update_container_border(password_container, self.password_input))
        self.username_input.installEventFilter(self)
        self.password_input.installEventFilter(self)
        
        self.username_container = username_container
        self.password_container = password_container
    
    def eventFilter(self, obj, event):
        if event.type() == event.FocusIn:
            if obj == self.username_input:
                self.username_container.setStyleSheet("#inputContainer { border: 1.5px solid #2563eb; border-radius: 10px; background-color: #ffffff; }")
            elif obj == self.password_input:
                self.password_container.setStyleSheet("#inputContainer { border: 1.5px solid #2563eb; border-radius: 10px; background-color: #ffffff; }")
        elif event.type() == event.FocusOut:
            if obj == self.username_input:
                self.username_container.setStyleSheet("#inputContainer { border: 1.5px solid #e2e8f0; border-radius: 10px; background-color: #ffffff; }")
            elif obj == self.password_input:
                self.password_container.setStyleSheet("#inputContainer { border: 1.5px solid #e2e8f0; border-radius: 10px; background-color: #ffffff; }")
        return super().eventFilter(obj, event)
    
    def update_container_border(self, container, input_field):
        pass
    
    def toggle_password_visibility(self):
        """切换密码可见性"""
        self.password_visible = not self.password_visible
        if self.password_visible:
            self.password_input.setEchoMode(QLineEdit.Normal)
            self.toggle_password_btn.setIcon(create_icon('eye-off', '#64748b', 18))
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
            self.toggle_password_btn.setIcon(create_icon('eye', '#64748b', 18))
    
    def load_saved_credentials(self):
        """加载保存的账号密码"""
        remember = self.settings.value("remember_password", False, type=bool)
        if remember:
            username = self.settings.value("username", "", type=str)
            password = self.settings.value("password", "", type=str)
            self.username_input.setText(username)
            self.password_input.setText(password)
            self.remember_checkbox.setChecked(True)
    
    def save_credentials(self):
        """保存账号密码"""
        if self.remember_checkbox.isChecked():
            self.settings.setValue("remember_password", True)
            self.settings.setValue("username", self.username_input.text().strip())
            self.settings.setValue("password", self.password_input.text().strip())
        else:
            self.settings.setValue("remember_password", False)
            self.settings.remove("username")
            self.settings.remove("password")
    
    def center(self):
        """窗口居中"""
        screen = QApplication.desktop().screenGeometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)
    
    def login(self):
        """登录验证"""
        if self.is_logging_in:
            return
        
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        if not username or not password:
            self.error_label.setText("用户名和密码不能为空")
            self.error_label.setVisible(True)
            return
        
        self.error_label.setVisible(False)
        self.is_logging_in = True
        self.login_button.setText("登录中...")
        self.login_button.setEnabled(False)
        
        QTimer.singleShot(50, self.do_login)
    
    def do_login(self):
        """执行登录请求"""
        try:
            username = self.username_input.text().strip()
            password = self.password_input.text().strip()
            
            response = requests.post(
                f"{self.app.API_BASE_URL}/room/login",
                data={"username": username, "password": password},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                allow_redirects=False
            )
            
            if response.status_code == 302:
                session = requests.Session()
                session.cookies = response.cookies
                
                user_info_response = session.get(f"{self.app.API_BASE_URL}/api/user/info")
                if user_info_response.status_code == 200:
                    user_data = user_info_response.json()
                    if user_data.get("success"):
                        user_info = user_data.get("data")
                        user_info["session"] = session
                        self.save_credentials()
                        self.login_success.emit(user_info)
                        self.close()
                        return
            
            self.error_label.setText("登录失败，请检查用户名和密码")
            self.error_label.setVisible(True)
        except Exception as e:
            self.error_label.setText(f"登录失败: {str(e)}")
            self.error_label.setVisible(True)
        finally:
            self.is_logging_in = False
            self.login_button.setText("登 录")
            self.login_button.setEnabled(True)

class RoomsWindow(QWidget):
    """房间选择窗口"""
    room_selected = pyqtSignal(dict)
    
    def __init__(self, app, user_info):
        super().__init__()
        self.app = app
        self.user_info = user_info
        self.setWindowTitle("选择助播室 - 千盈助播")
        self.setGeometry(100, 100, 500, 580)
        self.setMinimumSize(440, 520)
        self.center()
        
        try:
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ico.ico")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
            else:
                import sys
                if hasattr(sys, '_MEIPASS'):
                    icon_path = os.path.join(sys._MEIPASS, "ico.ico")
                    if os.path.exists(icon_path):
                        self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            pass
        
        self.setStyleSheet("""
            RoomsWindow {
                background-color: #f1f5f9;
            }
            QLabel {
                font-family: '微软雅黑', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            #headerBar {
                background-color: #ffffff;
                border-bottom: 1px solid #e2e8f0;
            }
            #pageTitle {
                color: #0f172a;
                font-size: 20px;
                font-weight: bold;
            }
            #pageSubtitle {
                color: #64748b;
                font-size: 13px;
                font-weight: normal;
            }
            #usernameLabel {
                color: #1e293b;
                font-size: 14px;
                font-weight: 600;
            }
            #userRoleLabel {
                color: #94a3b8;
                font-size: 12px;
                font-weight: normal;
            }
            #logoutBtn {
                background-color: #f8fafc;
                color: #475569;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 8px 14px;
                font-size: 13px;
                font-weight: 500;
            }
            #logoutBtn:hover {
                background-color: #f1f5f9;
                color: #1e293b;
                border-color: #cbd5e1;
            }
            #logoutBtn:pressed {
                background-color: #e2e8f0;
            }
            #sectionTitle {
                color: #0f172a;
                font-size: 16px;
                font-weight: 600;
            }
            #countBadge {
                color: #2563eb;
                background-color: #dbeafe;
                border-radius: 10px;
                padding: 2px 10px;
                font-size: 12px;
                font-weight: 500;
            }
            #roomsList {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                outline: none;
            }
            #roomsList::item {
                padding: 0px;
                border-bottom: 1px solid #f1f5f9;
            }
            #roomsList::item:hover {
                background-color: #f8fafc;
            }
            #roomsList::item:selected {
                background-color: #eff6ff;
                outline: none;
            }
            #roomsList:focus {
                outline: none;
                border: 1px solid #2563eb;
            }
            #roomItemWidget {
                background-color: transparent;
            }
            #roomName {
                color: #1e293b;
                font-size: 15px;
                font-weight: 600;
            }
            #roomDesc {
                color: #64748b;
                font-size: 12px;
                font-weight: normal;
            }
            #roomIconBg {
                background-color: #eff6ff;
                border-radius: 8px;
            }
            #primaryBtn {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 24px;
                font-size: 14px;
                font-weight: 600;
            }
            #primaryBtn:hover {
                background-color: #1d4ed8;
            }
            #primaryBtn:pressed {
                background-color: #1e40af;
            }
            #primaryBtn:disabled {
                background-color: #93c5fd;
                color: #dbeafe;
            }
            #secondaryBtn {
                background-color: #ffffff;
                color: #334155;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                padding: 10px 18px;
                font-size: 14px;
                font-weight: 500;
            }
            #secondaryBtn:hover {
                background-color: #f8fafc;
                border-color: #cbd5e1;
            }
            #secondaryBtn:pressed {
                background-color: #f1f5f9;
            }
            #bottomBar {
                background-color: #ffffff;
                border-top: 1px solid #e2e8f0;
            }
        """)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        header_bar = QWidget()
        header_bar.setObjectName("headerBar")
        header_layout = QHBoxLayout(header_bar)
        header_layout.setContentsMargins(24, 18, 24, 18)
        header_layout.setSpacing(16)
        
        title_group = QVBoxLayout()
        title_group.setSpacing(2)
        
        page_title = QLabel("选择助播室")
        page_title.setObjectName("pageTitle")
        title_group.addWidget(page_title)
        
        page_subtitle = QLabel("选择一个房间开始直播提词")
        page_subtitle.setObjectName("pageSubtitle")
        title_group.addWidget(page_subtitle)
        
        header_layout.addLayout(title_group)
        header_layout.addStretch()
        
        user_group = QHBoxLayout()
        user_group.setSpacing(12)
        
        user_text_group = QVBoxLayout()
        user_text_group.setSpacing(2)
        user_text_group.setContentsMargins(0, 0, 0, 0)
        
        username = user_info.get('nickname') or user_info.get('username') or user_info.get('name') or '用户'
        username_label = QLabel(username)
        username_label.setObjectName("usernameLabel")
        username_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        user_text_group.addWidget(username_label)
        
        user_role_label = QLabel("已登录")
        user_role_label.setObjectName("userRoleLabel")
        user_role_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        user_text_group.addWidget(user_role_label)
        
        user_group.addLayout(user_text_group)
        
        logout_btn = QPushButton()
        logout_btn.setObjectName("logoutBtn")
        logout_btn.setIcon(create_icon('logout', '#64748b', 16))
        logout_btn.setIconSize(QSize(16, 16))
        logout_btn.setText(" 退出")
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.clicked.connect(self.logout)
        user_group.addWidget(logout_btn)
        
        header_layout.addLayout(user_group)
        main_layout.addWidget(header_bar)
        
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(24, 20, 24, 20)
        content_layout.setSpacing(14)
        
        section_header = QHBoxLayout()
        section_header.setSpacing(10)
        
        section_title = QLabel("助播室列表")
        section_title.setObjectName("sectionTitle")
        section_header.addWidget(section_title)
        
        self.count_badge = QLabel("加载中")
        self.count_badge.setObjectName("countBadge")
        self.count_badge.setAlignment(Qt.AlignCenter)
        self.count_badge.setFixedHeight(20)
        section_header.addWidget(self.count_badge)
        
        section_header.addStretch()
        content_layout.addLayout(section_header)
        
        list_container = QWidget()
        list_container_layout = QVBoxLayout(list_container)
        list_container_layout.setContentsMargins(0, 0, 0, 0)
        add_shadow(list_container, blur_radius=24, y_offset=4, color=QColor(0, 0, 0, 15))
        
        self.rooms_list = QListWidget()
        self.rooms_list.setObjectName("roomsList")
        self.rooms_list.setCursor(Qt.PointingHandCursor)
        self.rooms_list.setItemDelegate(None)
        self.rooms_list.setSpacing(0)
        self.rooms_list.itemDoubleClicked.connect(self.select_room)
        list_container_layout.addWidget(self.rooms_list)
        
        content_layout.addWidget(list_container, 1)
        main_layout.addLayout(content_layout, 1)
        
        bottom_bar = QWidget()
        bottom_bar.setObjectName("bottomBar")
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(24, 14, 24, 14)
        bottom_layout.setSpacing(12)
        
        refresh_button = QPushButton()
        refresh_button.setObjectName("secondaryBtn")
        refresh_button.setIcon(create_icon('refresh', '#64748b', 16))
        refresh_button.setIconSize(QSize(16, 16))
        refresh_button.setText(" 刷新")
        refresh_button.setFixedHeight(42)
        refresh_button.setCursor(Qt.PointingHandCursor)
        refresh_button.clicked.connect(self.load_rooms)
        bottom_layout.addWidget(refresh_button)
        
        bottom_layout.addStretch()
        
        self.select_button = QPushButton()
        self.select_button.setObjectName("primaryBtn")
        self.select_button.setIcon(create_icon('arrow-right', '#ffffff', 16))
        self.select_button.setLayoutDirection(Qt.RightToLeft)
        self.select_button.setIconSize(QSize(16, 16))
        self.select_button.setText("进入助播室  ")
        self.select_button.setFixedHeight(42)
        self.select_button.setMinimumWidth(160)
        self.select_button.setCursor(Qt.PointingHandCursor)
        self.select_button.clicked.connect(self.select_room)
        self.select_button.setEnabled(False)
        bottom_layout.addWidget(self.select_button)
        
        main_layout.addWidget(bottom_bar)
        
        self.setLayout(main_layout)
        self.load_rooms()
        self.rooms_list.itemSelectionChanged.connect(self.on_item_selected)
    
    def center(self):
        """窗口居中"""
        screen = QApplication.desktop().screenGeometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)
    
    def load_rooms(self):
        """加载房间列表"""
        try:
            session = self.user_info.get("session")
            response = session.get(f"{self.app.API_BASE_URL}/room")
            
            import re
            rooms_data = []
            
            room_pattern = re.compile(r'<div class="room-card">.*?<h3>(.*?)</h3>.*?<p>(.*?)</p>.*?<a href="/room/(\d+)"', re.DOTALL)
            matches = room_pattern.findall(response.text)
            
            for match in matches:
                name, description, room_id = match
                rooms_data.append({
                    "id": int(room_id),
                    "name": name.strip(),
                    "description": description.strip()
                })
            
            self.rooms_list.clear()
            
            for room in rooms_data:
                item = QListWidgetItem()
                item.setData(Qt.UserRole, room)
                item.setSizeHint(QSize(0, 64))
                
                item_widget = QWidget()
                item_widget.setObjectName("roomItemWidget")
                item_layout = QHBoxLayout(item_widget)
                item_layout.setContentsMargins(16, 12, 16, 12)
                item_layout.setSpacing(12)
                
                icon_bg = QWidget()
                icon_bg.setObjectName("roomIconBg")
                icon_bg.setFixedSize(40, 40)
                icon_layout = QVBoxLayout(icon_bg)
                icon_layout.setContentsMargins(0, 0, 0, 0)
                icon_layout.setAlignment(Qt.AlignCenter)
                
                icon_label = QLabel()
                icon_label.setPixmap(create_icon('tv', '#2563eb', 20).pixmap(20, 20))
                icon_label.setAlignment(Qt.AlignCenter)
                icon_layout.addWidget(icon_label)
                
                item_layout.addWidget(icon_bg)
                
                text_group = QVBoxLayout()
                text_group.setSpacing(2)
                text_group.setContentsMargins(0, 0, 0, 0)
                
                name_label = QLabel(room['name'])
                name_label.setObjectName("roomName")
                text_group.addWidget(name_label)
                
                desc_label = QLabel(room['description'])
                desc_label.setObjectName("roomDesc")
                text_group.addWidget(desc_label)
                
                item_layout.addLayout(text_group, 1)
                
                arrow_label = QLabel()
                arrow_label.setPixmap(create_icon('arrow-right', '#cbd5e1', 16).pixmap(16, 16))
                arrow_label.setAlignment(Qt.AlignCenter)
                item_layout.addWidget(arrow_label)
                
                self.rooms_list.addItem(item)
                self.rooms_list.setItemWidget(item, item_widget)
            
            self.count_badge.setText(f"共 {len(rooms_data)} 个")
            
            if rooms_data:
                self.rooms_list.setCurrentRow(0)
        except Exception as e:
            self.count_badge.setText("加载失败")
            QMessageBox.critical(self, "错误", f"加载房间列表失败: {str(e)}")
    
    def on_item_selected(self):
        """当选择列表项时"""
        selected_items = self.rooms_list.selectedItems()
        self.select_button.setEnabled(len(selected_items) > 0)
    
    def select_room(self):
        """选择房间"""
        selected_items = self.rooms_list.selectedItems()
        if not selected_items:
            return
        
        selected_item = selected_items[0]
        room = selected_item.data(Qt.UserRole)
        self.room_selected.emit(room)
        self.close()
    
    def logout(self):
        """退出登录"""
        reply = QMessageBox.question(self, "确认退出", "确定要退出登录吗？",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.app.show_login_window()
            self.close()

class SocketIOThread(QThread):
    """Socket.io线程"""
    new_message = pyqtSignal(dict)
    status_updated = pyqtSignal(str)
    
    def __init__(self, session, room_id, api_base_url):
        super().__init__()
        self.session = session
        self.room_id = room_id
        self.api_base_url = api_base_url
        self.sio = None
        self.running = True
    
    def run(self):
        """运行Socket.io连接"""
        try:
            print("Socket.io线程开始运行")
            
            # 初始化Socket.io客户端
            self.sio = socketio.Client()
            
            @self.sio.event
            def connect():
                print("Socket.io连接成功")
                self.status_updated.emit("已连接")
                # 认证
                print("发送认证请求")
                self.sio.emit('authenticate', 'token')
                # 加入房间，尝试使用数字和字符串两种格式
                room_id_str = str(self.room_id)
                room_id_int = int(self.room_id)
                print(f"尝试加入房间 (字符串): {room_id_str}")
                self.sio.emit('joinRoom', room_id_str)
                
                print(f"尝试加入房间 (数字): {room_id_int}")
                self.sio.emit('joinRoom', room_id_int)
                
                self.status_updated.emit(f"已加入房间 {room_id_str}")
            
            @self.sio.event
            def message(data):
                print(f"收到新消息: {data}")
                self.new_message.emit(data)
            
            @self.sio.event
            def disconnect():
                print("Socket.io连接断开")
                self.status_updated.emit("已断开")
            
            @self.sio.event
            def error(data):
                print(f"Socket.io错误: {data}")
                self.status_updated.emit(f"错误: {data}")
            
            # 连接到服务器
            print(f"连接到Socket.io服务器: {self.api_base_url}")
            
            # 尝试不同的传输方式
            try:
                print("尝试使用websocket和polling传输方式")
                self.sio.connect(self.api_base_url, transports=['websocket', 'polling'])
            except Exception as e:
                print(f"连接失败: {str(e)}")
                # 尝试使用完整的WebSocket URL
                ws_url = self.api_base_url.replace('http', 'ws')
                print(f"尝试使用WebSocket URL: {ws_url}")
                try:
                    self.sio.connect(ws_url, transports=['websocket'])
                except Exception as e2:
                    print(f"WebSocket连接失败: {str(e2)}")
                    self.status_updated.emit(f"连接失败: {str(e2)}")
                    return
            
            # 保持线程运行
            print("Socket.io线程进入等待状态")
            while self.running:
                try:
                    self.sio.wait()
                except Exception as e:
                    print(f"Socket.io wait错误: {str(e)}")
                    # 继续运行
                    pass
        except Exception as e:
            print(f"Socket.io线程错误: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def stop(self):
        """停止Socket.io连接"""
        self.running = False
        if self.sio:
            self.sio.disconnect()
        self.wait()

class TeleprompterWindow(QMainWindow):
    """提词器窗口"""
    back_to_rooms = pyqtSignal()
    
    def __init__(self, app, user_info, room):
        super().__init__()
        self.app = app
        self.user_info = user_info
        self.room = room
        self.is_stay_on_top = True
        self.setWindowTitle(f"{room['name']} - 提词器")
        self.setGeometry(100, 100, 800, 550)
        self.setMinimumSize(600, 400)
        self.center()
        
        try:
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ico.ico")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
            else:
                import sys
                if hasattr(sys, '_MEIPASS'):
                    icon_path = os.path.join(sys._MEIPASS, "ico.ico")
                    if os.path.exists(icon_path):
                        self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            pass
        
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2a2a2a;
            }
            QLabel {
                font-family: '微软雅黑', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                color: #ffffff;
                font-size: 13px;
            }
            QPushButton {
                background-color: #3a3a3a;
                color: white;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px 14px;
                font-family: '微软雅黑', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
                border-color: #666666;
            }
            QPushButton:pressed {
                background-color: #333333;
            }
            QPushButton#stayOnTopBtn {
                background-color: #0078d4;
                border-color: #0078d4;
            }
            QPushButton#stayOnTopBtn:hover {
                background-color: #106ebe;
            }
            QPushButton#stayOnTopBtn:off {
                background-color: #3a3a3a;
                border-color: #555555;
            }
            QPushButton#stayOnTopBtn:off:hover {
                background-color: #4a4a4a;
            }
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #444444;
                border-radius: 6px;
                font-family: '微软雅黑', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            QSlider::groove:horizontal {
                border: none;
                height: 4px;
                background: #444444;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #0078d4;
                border: none;
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover {
                background: #106ebe;
            }
            QScrollBar:vertical {
                background: #333333;
                width: 10px;
            }
            QScrollBar::handle:vertical {
                background: #666666;
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #888888;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        
        top_bar = QHBoxLayout()
        
        left_buttons = QHBoxLayout()
        left_buttons.setSpacing(6)
        
        back_button = QPushButton("重选房间")
        back_button.clicked.connect(self.back_to_rooms.emit)
        left_buttons.addWidget(back_button)
        
        refresh_button = QPushButton("刷新消息")
        refresh_button.clicked.connect(self.refresh_messages)
        left_buttons.addWidget(refresh_button)
        
        clear_button = QPushButton("清除助播记录")
        clear_button.clicked.connect(self.clear_messages)
        left_buttons.addWidget(clear_button)
        
        top_bar.addLayout(left_buttons)
        top_bar.addStretch()
        
        right_buttons = QHBoxLayout()
        right_buttons.setSpacing(8)
        
        self.status_label = QLabel("● 连接中")
        self.status_label.setStyleSheet("color: #ffaa00; font-size: 12px;")
        right_buttons.addWidget(self.status_label)
        
        self.stay_on_top_btn = QPushButton("📌 置顶")
        self.stay_on_top_btn.setObjectName("stayOnTopBtn")
        self.stay_on_top_btn.setCheckable(True)
        self.stay_on_top_btn.setChecked(True)
        self.stay_on_top_btn.clicked.connect(self.toggle_stay_on_top)
        right_buttons.addWidget(self.stay_on_top_btn)
        
        top_bar.addLayout(right_buttons)
        layout.addLayout(top_bar)
        
        self.messages_text = QTextEdit()
        self.messages_text.setReadOnly(True)
        self.font_size = 18
        self.font = QFont("微软雅黑", self.font_size)
        self.messages_text.setFont(self.font)
        self.messages_text.setLineWrapMode(QTextEdit.WidgetWidth)
        layout.addWidget(self.messages_text, 1)
        
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(20)
        
        font_group = QHBoxLayout()
        font_group.setSpacing(8)
        font_size_label = QLabel("字号:")
        font_size_label.setStyleSheet("color: #888; font-size: 12px;")
        font_group.addWidget(font_size_label)
        
        self.font_size_slider = QSlider(Qt.Horizontal)
        self.font_size_slider.setMinimum(12)
        self.font_size_slider.setMaximum(60)
        self.font_size_slider.setValue(self.font_size)
        self.font_size_slider.setFixedWidth(160)
        self.font_size_slider.valueChanged.connect(self.on_font_size_changed)
        font_group.addWidget(self.font_size_slider)
        
        self.font_size_value = QLabel(str(self.font_size))
        self.font_size_value.setStyleSheet("color: #aaa; font-size: 12px; min-width: 24px;")
        font_group.addWidget(self.font_size_value)
        
        bottom_bar.addLayout(font_group)
        
        opacity_group = QHBoxLayout()
        opacity_group.setSpacing(8)
        opacity_label = QLabel("透明度:")
        opacity_label.setStyleSheet("color: #888; font-size: 12px;")
        opacity_group.addWidget(opacity_label)
        
        self.opacity = 1.0
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setMinimum(30)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(int(self.opacity * 100))
        self.opacity_slider.setFixedWidth(160)
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)
        opacity_group.addWidget(self.opacity_slider)
        
        self.opacity_value = QLabel(f"{int(self.opacity * 100)}%")
        self.opacity_value.setStyleSheet("color: #aaa; font-size: 12px; min-width: 32px;")
        opacity_group.addWidget(self.opacity_value)
        
        bottom_bar.addLayout(opacity_group)
        bottom_bar.addStretch()
        
        layout.addLayout(bottom_bar)
        
        self.displayed_messages = set()
        self.load_initial_messages()
        
        print(f"初始化Socket.io线程，房间ID: {room['id']}")
        
        try:
            self.socket_thread = SocketIOThread(self.user_info.get("session"), room['id'], self.app.API_BASE_URL)
            self.socket_thread.new_message.connect(self.handle_new_message)
            self.socket_thread.status_updated.connect(self.update_status)
            
            print("启动Socket.io线程")
            self.socket_thread.start()
            
            print("Socket.io线程已启动")
        except Exception as e:
            print(f"启动Socket.io线程失败: {str(e)}")
    
    def toggle_stay_on_top(self):
        """切换窗口置顶状态"""
        self.is_stay_on_top = self.stay_on_top_btn.isChecked()
        if self.is_stay_on_top:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            self.stay_on_top_btn.setText("📌 置顶")
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
            self.stay_on_top_btn.setText("📌 取消置顶")
        self.show()
    
    def center(self):
        """窗口居中"""
        screen = QApplication.desktop().screenGeometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)
    
    def load_initial_messages(self, clear_existing=False):
        """加载初始消息"""
        try:
            session = self.user_info.get("session")
            if not session:
                print("会话不存在")
                return
            
            # 尝试不同的API接口获取消息
            api_urls = [
                f"{self.app.API_BASE_URL}/admin/api/room/{self.room['id']}/messages",
                f"{self.app.API_BASE_URL}/api/room/{self.room['id']}/messages",
                f"{self.app.API_BASE_URL}/room/{self.room['id']}/messages"
            ]
            
            response = None
            for api_url in api_urls:
                try:
                    print(f"尝试获取消息: {api_url}")
                    response = session.get(api_url)
                    print(f"响应状态码: {response.status_code}")
                    if response.status_code == 200:
                        break
                except Exception as e:
                    print(f"API调用失败: {str(e)}")
                    continue
            
            if response and response.status_code == 200:
                print("获取消息成功")
                data = response.json()
                print(f"响应数据: {data}")
                if data.get('success'):
                    messages = data['data']
                    print(f"获取到 {len(messages)} 条消息")
                    # 按时间排序
                    messages.sort(key=lambda x: x.get('created_at', ''))
                    
                    # 清空现有消息
                    if clear_existing:
                        self.messages_text.clear()
                        self.displayed_messages.clear()
                    
                    # 显示消息
                    for message in messages:
                        message_id = message.get('id')
                        if not message_id or message_id not in self.displayed_messages:
                            if message_id:
                                self.displayed_messages.add(message_id)
                            self.add_message(message, False)
            else:
                print("获取消息失败")
        except Exception as e:
            print(f"加载初始消息失败: {str(e)}")
    
    def refresh_messages(self):
        """刷新消息"""
        self.load_initial_messages(clear_existing=True)
    
    def add_message(self, message, is_new=False):
        """添加消息"""
        # 尝试从不同的键获取用户名，优先使用nickname
        username = message.get('nickname', message.get('username', message.get('user', message.get('name', '未知用户'))))
        content = message.get('content', message.get('message', ''))
        created_at = message.get('createdAt', message.get('created_at', ''))
        
        # 格式化时间为 "2026/4/10 20:27:09" 格式（年/月/日 时:分:秒）
        formatted_time = ''
        if created_at:
            try:
                import datetime
                import pytz
                # 检查是否为ISO格式时间
                if 'T' in created_at and ('Z' in created_at or '+' in created_at):
                    # 解析ISO格式时间
                    dt = datetime.datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    # 转换为本地时间
                    local_tz = pytz.timezone('Asia/Shanghai')
                    dt = dt.replace(tzinfo=pytz.UTC).astimezone(local_tz)
                    # 格式化为 YYYY/MM/DD HH:MM
                    temp_time = dt.strftime('%Y/%m/%d %H:%M')
                    # 拆分日期和时间部分
                    date_part, time_part = temp_time.split(' ')
                    # 拆分日期为组件并转换为整数以移除前导零
                    year, month, day = map(int, date_part.split('/'))
                    # 重新格式化日期，不带前导零
                    formatted_date = f"{year}/{month}/{day}"
                    # 组合回完整时间
                    formatted_time = f"{formatted_date} {time_part}"
                else:
                    # 尝试解析非ISO格式时间
                    try:
                        # 尝试解析 "2026/4/10 20:32:05" 格式
                        dt = datetime.datetime.strptime(created_at, '%Y/%m/%d %H:%M:%S')
                        # 格式化为 YYYY/MM/DD HH:MM
                        temp_time = dt.strftime('%Y/%m/%d %H:%M')
                        # 拆分日期和时间部分
                        date_part, time_part = temp_time.split(' ')
                        # 拆分日期为组件并转换为整数以移除前导零
                        year, month, day = map(int, date_part.split('/'))
                        # 重新格式化日期，不带前导零
                        formatted_date = f"{year}/{month}/{day}"
                        # 组合回完整时间
                        formatted_time = f"{formatted_date} {time_part}"
                    except:
                        # 如果解析失败，直接使用原始时间
                        formatted_time = created_at
            except ImportError:
                # 如果pytz未安装，使用本地时间
                try:
                    import datetime
                    # 检查是否为ISO格式时间
                    if 'T' in created_at and ('Z' in created_at or '+' in created_at):
                        # 解析ISO格式时间
                        dt = datetime.datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        # 格式化为 YYYY/MM/DD HH:MM
                        temp_time = dt.strftime('%Y/%m/%d %H:%M')
                        # 拆分日期和时间部分
                        date_part, time_part = temp_time.split(' ')
                        # 拆分日期为组件并转换为整数以移除前导零
                        year, month, day = map(int, date_part.split('/'))
                        # 重新格式化日期，不带前导零
                        formatted_date = f"{year}/{month}/{day}"
                        # 组合回完整时间
                        formatted_time = f"{formatted_date} {time_part}"
                    else:
                        # 尝试解析非ISO格式时间
                        try:
                            # 尝试解析 "2026/4/10 20:32:05" 格式
                            dt = datetime.datetime.strptime(created_at, '%Y/%m/%d %H:%M:%S')
                            # 格式化为 YYYY/MM/DD HH:MM
                            temp_time = dt.strftime('%Y/%m/%d %H:%M')
                            # 拆分日期和时间部分
                            date_part, time_part = temp_time.split(' ')
                            # 拆分日期为组件并转换为整数以移除前导零
                            year, month, day = map(int, date_part.split('/'))
                            # 重新格式化日期，不带前导零
                            formatted_date = f"{year}/{month}/{day}"
                            # 组合回完整时间
                            formatted_time = f"{formatted_date} {time_part}"
                        except:
                            # 如果解析失败，直接使用原始时间
                            formatted_time = created_at
                except:
                    # 如果解析失败，使用原始时间
                    formatted_time = created_at
            except:
                # 如果解析失败，使用原始时间
                formatted_time = created_at
        
        # 插入消息（分别处理时间、昵称和内容）
        cursor = self.messages_text.textCursor()
        
        # 插入时间（保持白色，固定14px字体）
        if formatted_time:
            time_text = f"[{formatted_time}] "
            time_format = cursor.charFormat()
            time_format.setForeground(QColor(255, 255, 255))  # 白色
            time_font = QFont("微软雅黑", 14)
            time_format.setFont(time_font)
            cursor.setCharFormat(time_format)
            cursor.insertText(time_text)
        
        # 插入昵称（保持白色，使用当前字体大小）
        nickname_text = f"{username}: "
        nickname_format = cursor.charFormat()
        nickname_format.setForeground(QColor(255, 255, 255))  # 白色
        nickname_font = QFont("微软雅黑", self.font_size)
        nickname_format.setFont(nickname_font)
        cursor.setCharFormat(nickname_format)
        cursor.insertText(nickname_text)
        
        # 插入内容（如果是新消息，后续会闪烁，使用当前字体大小）
        content_format = cursor.charFormat()
        content_format.setForeground(QColor(255, 255, 255))  # 白色
        content_font = QFont("微软雅黑", self.font_size)
        content_format.setFont(content_font)
        cursor.setCharFormat(content_format)
        cursor.insertText(f"{content}\n")
        
        # 如果是新消息，设置红色闪烁效果（只对内容部分）
        if is_new:
            # 定义闪烁函数
            def flash_message(counter=0):
                if counter < 6:  # 闪烁6次
                    # 创建新的光标，确保能够正确操作
                    current_cursor = self.messages_text.textCursor()
                    # 移动到文本末尾
                    current_cursor.movePosition(QTextCursor.End)
                    # 向上移动一行（到新插入的消息行）
                    current_cursor.movePosition(QTextCursor.Up)
                    
                    # 找到内容部分的起始位置（跳过时间和昵称）
                    line_text = current_cursor.block().text()
                    if formatted_time:
                        # 跳过时间部分 "[2026/4/10 20:47] "
                        time_end = line_text.find("]") + 2
                        # 跳过昵称部分 "刘豪: "
                        nickname_end = line_text.find(":", time_end) + 2
                        # 选择内容部分
                        current_cursor.movePosition(QTextCursor.StartOfBlock)
                        current_cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor, nickname_end)
                        current_cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
                    else:
                        # 跳过昵称部分 "刘豪: "
                        nickname_end = line_text.find(":") + 2
                        # 选择内容部分
                        current_cursor.movePosition(QTextCursor.StartOfBlock)
                        current_cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor, nickname_end)
                        current_cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
                    
                    # 切换颜色
                    char_format = current_cursor.charFormat()
                    if counter % 2 == 0:
                        # 红色
                        char_format.setForeground(QColor(255, 0, 0))  # 红色
                    else:
                        # 白色
                        char_format.setForeground(QColor(255, 255, 255))  # 白色
                    current_cursor.setCharFormat(char_format)
                    # 继续闪烁
                    QTimer.singleShot(300, lambda: flash_message(counter + 1))
                else:
                    # 最终恢复白色
                    current_cursor = self.messages_text.textCursor()
                    # 移动到文本末尾
                    current_cursor.movePosition(QTextCursor.End)
                    # 向上移动一行（到新插入的消息行）
                    current_cursor.movePosition(QTextCursor.Up)
                    
                    # 找到内容部分的起始位置（跳过时间和昵称）
                    line_text = current_cursor.block().text()
                    if formatted_time:
                        # 跳过时间部分 "[2026/4/10 20:47] "
                        time_end = line_text.find("]") + 2
                        # 跳过昵称部分 "刘豪: "
                        nickname_end = line_text.find(":", time_end) + 2
                        # 选择内容部分
                        current_cursor.movePosition(QTextCursor.StartOfBlock)
                        current_cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor, nickname_end)
                        current_cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
                    else:
                        # 跳过昵称部分 "刘豪: "
                        nickname_end = line_text.find(":") + 2
                        # 选择内容部分
                        current_cursor.movePosition(QTextCursor.StartOfBlock)
                        current_cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor, nickname_end)
                        current_cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
                    
                    char_format = current_cursor.charFormat()
                    char_format.setForeground(QColor(255, 255, 255))  # 白色
                    current_cursor.setCharFormat(char_format)
            
            # 开始闪烁
            flash_message()
        
        # 滚动到底部
        self.messages_text.ensureCursorVisible()
    
    def clear_messages(self):
        """清空消息"""
        try:
            session = self.user_info.get("session")
            response = session.delete(f"{self.app.API_BASE_URL}/api/rooms/{self.room['id']}/messages")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    # 清空本地显示
                    self.messages_text.clear()
                    self.displayed_messages.clear()
                    QMessageBox.information(self, "成功", "清理成功")
                else:
                    QMessageBox.warning(self, "失败", f"清空聊天记录失败: {data.get('message')}")
            else:
                QMessageBox.warning(self, "失败", f"清空聊天记录失败，状态码: {response.status_code}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"清空聊天记录失败: {str(e)}")
    
    def on_font_size_changed(self, value):
        """字体大小滑动条变化"""
        self.font_size = value
        self.font = QFont("微软雅黑", self.font_size)
        
        # 更新消息框的默认字体（影响新插入的文本）
        self.messages_text.setFont(self.font)
        
        # 更新所有现有文本的字体大小
        cursor = self.messages_text.textCursor()
        cursor.select(QTextCursor.Document)
        char_format = cursor.charFormat()
        char_format.setFont(self.font)
        cursor.setCharFormat(char_format)
        
        # 更新显示的字体大小值
        self.font_size_value.setText(str(value))
    
    def on_opacity_changed(self, value):
        """透明度滑动条变化"""
        self.opacity = value / 100.0
        self.setWindowOpacity(self.opacity)
        self.opacity_value.setText(f"{value}%")
    
    def handle_new_message(self, message):
        """处理新消息"""
        # 检查消息是否已显示
        message_id = message.get('id')
        if not message_id or message_id not in self.displayed_messages:
            if message_id:
                self.displayed_messages.add(message_id)
            # 添加消息并标记为新消息，使其闪烁
            self.add_message(message, True)
    
    def update_status(self, status):
        """更新Socket.io状态"""
        if "已连接" in status or "已加入" in status:
            self.status_label.setText(f"● {status}")
            self.status_label.setStyleSheet("color: #4ade80; font-size: 12px;")
        elif "断开" in status or "失败" in status or "错误" in status:
            self.status_label.setText(f"● {status}")
            self.status_label.setStyleSheet("color: #f87171; font-size: 12px;")
        else:
            self.status_label.setText(f"● {status}")
            self.status_label.setStyleSheet("color: #ffaa00; font-size: 12px;")
    

    
    def closeEvent(self, event):
        """关闭事件"""
        # 停止Socket.io线程
        if hasattr(self, 'socket_thread'):
            self.socket_thread.stop()
        event.accept()

class QYZBApp:
    """助播提词器应用"""
    API_BASE_URL = "https://zb.infowe.site"
    
    def __init__(self):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("千盈助播提词器")
        self.app.setOrganizationName("千盈房产")
        
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ico.ico")
        if os.path.exists(icon_path):
            self.app.setWindowIcon(QIcon(icon_path))
        
        self.user_info = None
        self.current_room = None
        self.login_window = None
        self.rooms_window = None
        self.teleprompter_window = None
        
        self.show_login_window()
        
        sys.exit(self.app.exec_())
    
    def show_login_window(self):
        """显示登录窗口"""
        if self.rooms_window:
            self.rooms_window.close()
        if self.teleprompter_window:
            self.teleprompter_window.close()
        
        self.login_window = LoginWindow(self)
        self.login_window.login_success.connect(self.on_login_success)
        self.login_window.show()
    
    def on_login_success(self, user_info):
        """登录成功处理"""
        self.user_info = user_info
        self.show_rooms_window()
    
    def show_rooms_window(self):
        """显示房间选择窗口"""
        if self.login_window:
            self.login_window.close()
        if self.teleprompter_window:
            self.teleprompter_window.close()
        
        self.rooms_window = RoomsWindow(self, self.user_info)
        self.rooms_window.room_selected.connect(self.on_room_selected)
        self.rooms_window.show()
    
    def on_room_selected(self, room):
        """房间选择处理"""
        self.current_room = room
        self.show_teleprompter_window()
    
    def show_teleprompter_window(self):
        """显示提词器窗口"""
        if self.rooms_window:
            self.rooms_window.close()
        
        self.teleprompter_window = TeleprompterWindow(self, self.user_info, self.current_room)
        self.teleprompter_window.back_to_rooms.connect(self.show_rooms_window)
        self.teleprompter_window.show()

if __name__ == "__main__":
    app = QYZBApp()
