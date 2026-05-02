import sys
import os
import subprocess
import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QPushButton, QGridLayout, QFrame,
                            QSystemTrayIcon, QMenu, QAction, QInputDialog, QActionGroup)
from PyQt5.QtCore import QTimer, Qt, QSize
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon

# ====================== 全局配置（运行时可修改，无需重启） ======================
# 周类型："holiday"（放假周）/ "adjust"（调休周）
CURRENT_WEEK_TYPE = "holiday"
# 时间矫正（单位：秒），正数=比实际时间快，负数=比实际时间慢
TIME_OFFSET = 0

# ====================== 作息时间表 ======================
# 周一（升旗日）作息
TIMETABLE_MONDAY = {
    1: ("07:50", "08:30"),
    2: ("08:50", "09:30"),
    3: ("09:35", "10:15"),
    4: ("10:25", "11:05"),
    5: ("11:15", "11:55"),
    6: ("14:30", "15:10"),
    7: ("15:20", "16:00")
}

# 周二到周五 通用作息
TIMETABLE_WEEKDAY = {
    1: ("08:00", "08:40"),
    2: ("08:50", "09:30"),
    3: ("09:35", "10:15"),
    4: ("10:25", "11:05"),
    5: ("11:15", "11:55"),
    6: ("14:30", "15:10"),
    7: ("15:20", "16:00")
}

# 放假周 周六周日作息（放假留空）
TIMETABLE_HOLIDAY_SAT = {}
TIMETABLE_HOLIDAY_SUN = {}

# 调休周 周六作息
TIMETABLE_ADJUST_SAT = {
    1: ("08:00", "08:40"),
    2: ("08:50", "09:30"),
    3: ("09:35", "10:15"),
    4: ("10:25", "11:05"),
    5: ("14:30", "15:10"),
    6: ("15:20", "16:00"),
    7: ("16:30", "17:15"),
    8: ("17:25", "18:10")
}

# 调休周 周日作息
TIMETABLE_ADJUST_SUN = {
    1: ("08:00", "08:40"),
    2: ("08:50", "09:30"),
    3: ("09:35", "10:15"),
    4: ("10:25", "11:05"),
    5: ("14:30", "15:10"),
    6: ("15:20", "16:00"),
    7: ("16:10", "16:50")
}

# ====================== 课表配置 ======================
# 周一课表（升旗日）
SCHEDULE_MONDAY = [
    "生物刘老师", "升旗", "英语张老师", "数学王老师", "体育",
    "语文张老师", "物理王老师"
]

# 周二课表
SCHEDULE_TUESDAY = [
    "英语张老师", "数学王老师", "数学王老师", "物理王老师",
    "生物刘老师", "化学申老师"
]

# 周三课表（政治历史非高考科目，已留空）
SCHEDULE_WEDNESDAY = [
    "化学申老师", "", "英语张老师", "", "数学王老师",
    "语文张老师", "物理王老师"
]

# 周四课表
SCHEDULE_THURSDAY = [
    "英语张老师", "物理王老师", "化学申老师", "语文张老师", "生物刘老师",
    "体育", "信息技术"
]

# 周五课表（地理非高考科目，已留空）
SCHEDULE_FRIDAY = [
    "英语张老师", "语文张老师", "数学王老师", "化学申老师", "物理王老师",
    "生物刘老师", ""
]

# 调休周 周六课表
SCHEDULE_ADJUST_SAT = [
    "化学申老师", "化学申老师", "数学王老师", "数学王老师",
    "生物刘老师", "生物刘老师", "英语张老师", "英语张老师"
]

# 调休周 周日课表（下午按周轮换，已标注）
SCHEDULE_ADJUST_SUN = [
    "物理王老师", "物理王老师", "语文张老师", "语文张老师",
    "语文张老师", "数学王老师", "英语张老师"  # 轮换：物理/化学/生物
]

# ====================== 老师常用软件配置 ======================
TEACHER_SOFTWARE = {
    "语文张老师": [
        ("希沃白板5", r"C:\Program Files (x86)\Seewo\EasiNote5\EasiNote5.exe"),
        ("Word", r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE"),
        ("PPT", r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE"),
        ("浏览器", r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        ("酷狗音乐", r"C:\Program Files (x86)\Kugou\KugouMusic\KugouMusic.exe"),
        ("计算器", "calc.exe")
    ],
    "数学王老师": [
        ("希沃白板5", r"C:\Program Files (x86)\Seewo\EasiNote5\EasiNote5.exe"),
        ("几何画板", r"C:\Program Files\GeoGebra\GeoGebra.exe"),
        ("PPT", r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE"),
        ("Excel", r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE"),
        ("浏览器", r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        ("计算器", "calc.exe")
    ],
    "英语张老师": [
        ("希沃白板5", r"C:\Program Files (x86)\Seewo\EasiNote5\EasiNote5.exe"),
        ("PPT", r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE"),
        ("浏览器", r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        ("网易有道词典", r"C:\Program Files (x86)\Youdao\Dict\YoudaoDict.exe"),
        ("酷狗音乐", r"C:\Program Files (x86)\Kugou\KugouMusic\KugouMusic.exe"),
        ("计算器", "calc.exe")
    ],
    "物理王老师": [
        ("希沃白板5", r"C:\Program Files (x86)\Seewo\EasiNote5\EasiNote5.exe"),
        ("PPT", r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE"),
        ("浏览器", r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        ("计算器", "calc.exe"),
        ("此电脑", "explorer.exe")
    ],
    "化学申老师": [
        ("希沃白板5", r"C:\Program Files (x86)\Seewo\EasiNote5\EasiNote5.exe"),
        ("PPT", r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE"),
        ("浏览器", r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        ("计算器", "calc.exe"),
        ("此电脑", "explorer.exe")
    ],
    "生物刘老师": [
        ("希沃白板5", r"C:\Program Files (x86)\Seewo\EasiNote5\EasiNote5.exe"),
        ("PPT", r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE"),
        ("浏览器", r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        ("计算器", "calc.exe"),
        ("此电脑", "explorer.exe")
    ],
    "升旗": [],
    "体育": [],
    "信息技术": [],
    "": []
}

# 默认软件
DEFAULT_SOFTWARE = [
    ("希沃白板5", r"C:\Program Files (x86)\Seewo\EasiNote5\EasiNote5.exe"),
    ("PPT", r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE"),
    ("Word", r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE"),
    ("浏览器", r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    ("计算器", "calc.exe"),
    ("此电脑", "explorer.exe")
]
# ====================== 配置结束 ======================

class ClassDesktop(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_teacher = "欢迎使用班级桌面"
        self.initUI()
        self.initTimer()
        self.initTray()
        
    def initUI(self):
        self.setWindowTitle("班级智能桌面")
        self.showFullScreen()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setStyleSheet("background-color: #2C3E50; color: white;")
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 左侧时间面板
        left_panel = QWidget()
        left_panel.setStyleSheet("background-color: #34495E;")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setAlignment(Qt.AlignCenter)
        
        self.time_label = QLabel()
        self.time_label.setFont(QFont("Microsoft YaHei", 120, QFont.Bold))
        self.time_label.setAlignment(Qt.AlignCenter)
        
        self.date_label = QLabel()
        self.date_label.setFont(QFont("Microsoft YaHei", 36))
        self.date_label.setAlignment(Qt.AlignCenter)
        
        left_layout.addWidget(self.time_label)
        left_layout.addWidget(self.date_label)
        
        # 右侧面板
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(40, 40, 40, 40)
        right_layout.setSpacing(30)
        
        self.greeting_label = QLabel("欢迎使用班级智能桌面")
        self.greeting_label.setFont(QFont("Microsoft YaHei", 48, QFont.Bold))
        self.greeting_label.setAlignment(Qt.AlignCenter)
        self.greeting_label.setStyleSheet("color: #3498DB;")
        
        self.software_frame = QFrame()
        self.software_frame.setStyleSheet("background-color: #2C3E50; border-radius: 10px;")
        self.software_layout = QGridLayout(self.software_frame)
        self.software_layout.setSpacing(20)
        self.update_software_buttons()
        
        # 底部按钮
        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        
        desktop_btn = QPushButton("返回系统桌面")
        desktop_btn.setFont(QFont("Microsoft YaHei", 24))
        desktop_btn.setFixedHeight(80)
        desktop_btn.setStyleSheet("""
            QPushButton {background-color: #27AE60; border-radius: 10px; color: white;}
            QPushButton:hover {background-color: #2ECC71;}
        """)
        desktop_btn.clicked.connect(self.show_desktop)
        
        usb_btn = QPushButton("打开U盘")
        usb_btn.setFont(QFont("Microsoft YaHei", 24))
        usb_btn.setFixedHeight(80)
        usb_btn.setStyleSheet("""
            QPushButton {background-color: #F39C12; border-radius: 10px; color: white;}
            QPushButton:hover {background-color: #F1C40F;}
        """)
        usb_btn.clicked.connect(self.open_usb)
        
        shutdown_btn = QPushButton("关闭电脑")
        shutdown_btn.setFont(QFont("Microsoft YaHei", 24))
        shutdown_btn.setFixedHeight(80)
        shutdown_btn.setStyleSheet("""
            QPushButton {background-color: #E74C3C; border-radius: 10px; color: white;}
            QPushButton:hover {background-color: #C0392B;}
        """)
        shutdown_btn.clicked.connect(self.shutdown_computer)
        
        bottom_layout.addWidget(desktop_btn, 2)
        bottom_layout.addStretch(1)
        bottom_layout.addWidget(usb_btn, 1)
        bottom_layout.addWidget(shutdown_btn, 1)
        
        right_layout.addWidget(self.greeting_label)
        right_layout.addWidget(self.software_frame, 1)
        right_layout.addWidget(bottom_widget)
        
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 2)
        
        self.update_time()
        
    def initTimer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        
        self.schedule_timer = QTimer(self)
        self.schedule_timer.timeout.connect(self.check_schedule)
        self.schedule_timer.start(60000)
        
        self.check_schedule()
        
    def initTray(self):
        # 创建系统托盘图标
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon.fromTheme("application-x-executable"))
        self.tray_icon.setToolTip("班级智能桌面")
        
        # 创建托盘菜单
        tray_menu = QMenu()
        
        # 显示主窗口
        show_action = QAction("显示主界面", self)
        show_action.triggered.connect(self.showNormal)
        tray_menu.addAction(show_action)
        
        tray_menu.addSeparator()
        
        # 周模式切换
        self.holiday_action = QAction("切换为放假周", self)
        self.holiday_action.setCheckable(True)
        self.holiday_action.setChecked(CURRENT_WEEK_TYPE == "holiday")
        self.holiday_action.triggered.connect(lambda: self.switch_week_type("holiday"))
        
        self.adjust_action = QAction("切换为调休周", self)
        self.adjust_action.setCheckable(True)
        self.adjust_action.setChecked(CURRENT_WEEK_TYPE == "adjust")
        self.adjust_action.triggered.connect(lambda: self.switch_week_type("adjust"))
        
        week_group = QActionGroup(self)
        week_group.addAction(self.holiday_action)
        week_group.addAction(self.adjust_action)
        
        tray_menu.addAction(self.holiday_action)
        tray_menu.addAction(self.adjust_action)
        
        tray_menu.addSeparator()
        
        # 时间矫正
        time_offset_action = QAction("设置时间矫正(秒)", self)
        time_offset_action.triggered.connect(self.set_time_offset)
        tray_menu.addAction(time_offset_action)
        
        tray_menu.addSeparator()
        
        # 退出程序
        exit_action = QAction("退出程序", self)
        exit_action.triggered.connect(QApplication.quit)
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
        # 点击托盘图标显示主窗口
        self.tray_icon.activated.connect(self.tray_activated)
        
    def tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.showNormal()
            
    def switch_week_type(self, week_type):
        global CURRENT_WEEK_TYPE
        CURRENT_WEEK_TYPE = week_type
        self.check_schedule()
        self.tray_icon.showMessage("提示", f"已切换为{'放假周' if week_type == 'holiday' else '调休周'}", QSystemTrayIcon.Information, 2000)
        
    def set_time_offset(self):
        global TIME_OFFSET
        value, ok = QInputDialog.getInt(self, "时间矫正设置", 
                                       "输入矫正值(秒)\n正数=比实际时间快\n负数=比实际时间慢",
                                       TIME_OFFSET, -3600, 3600, 1)
        if ok:
            TIME_OFFSET = value
            self.update_time()
            self.check_schedule()
            self.tray_icon.showMessage("提示", f"时间矫正已设置为 {value} 秒", QSystemTrayIcon.Information, 2000)
        
    def get_corrected_time(self):
        # 获取矫正后的时间
        return datetime.datetime.now() + datetime.timedelta(seconds=TIME_OFFSET)
        
    def update_time(self):
        now = self.get_corrected_time()
        self.time_label.setText(now.strftime("%H:%M"))
        self.date_label.setText(now.strftime("%Y年%m月%d日 星期%w").replace("星期0", "星期日"))
        
    def check_schedule(self):
        now = self.get_corrected_time()
        weekday = now.isoweekday()
        current_time = now.strftime("%H:%M")
        
        # 选择对应的作息和课表
        if weekday == 1:
            timetable = TIMETABLE_MONDAY
            schedule = SCHEDULE_MONDAY
        elif 2 <= weekday <= 5:
            timetable = TIMETABLE_WEEKDAY
            schedule = [SCHEDULE_TUESDAY, SCHEDULE_WEDNESDAY, 
                       SCHEDULE_THURSDAY, SCHEDULE_FRIDAY][weekday-2]
        elif weekday == 6:
            if CURRENT_WEEK_TYPE == "adjust":
                timetable = TIMETABLE_ADJUST_SAT
                schedule = SCHEDULE_ADJUST_SAT
            else:
                timetable = TIMETABLE_HOLIDAY_SAT
                schedule = []
        else:
            if CURRENT_WEEK_TYPE == "adjust":
                timetable = TIMETABLE_ADJUST_SUN
                schedule = SCHEDULE_ADJUST_SUN
            else:
                timetable = TIMETABLE_HOLIDAY_SUN
                schedule = []
        
        # 检查当前课程
        for lesson, (start, end) in timetable.items():
            if start <= current_time <= end:
                if lesson <= len(schedule):
                    self.current_teacher = schedule[lesson-1]
                    self.update_greeting()
                    self.update_software_buttons()
                return
                
        # 非上课时间
        if CURRENT_WEEK_TYPE == "holiday" and weekday >= 6:
            self.current_teacher = "周末愉快"
        else:
            self.current_teacher = "课间休息"
        self.update_greeting()
        
    def update_greeting(self):
        now = self.get_corrected_time()
        hour = now.hour
        
        if hour < 12:
            greeting = "上午好"
        elif hour < 18:
            greeting = "下午好"
        else:
            greeting = "晚上好"
            
        if self.current_teacher in ["课间休息", "周末愉快", "升旗", "体育", "信息技术", ""]:
            self.greeting_label.setText(self.current_teacher if self.current_teacher else "课间休息")
        else:
            self.greeting_label.setText(f"{self.current_teacher}，{greeting}！")
            
    def update_software_buttons(self):
        for i in reversed(range(self.software_layout.count())): 
            self.software_layout.itemAt(i).widget().setParent(None)
            
        software_list = TEACHER_SOFTWARE.get(self.current_teacher, DEFAULT_SOFTWARE)
        if not software_list:
            software_list = DEFAULT_SOFTWARE
            
        for i, (name, path) in enumerate(software_list):
            btn = QPushButton(name)
            btn.setFont(QFont("Microsoft YaHei", 20))
            btn.setFixedSize(200, 100)
            btn.setStyleSheet("""
                QPushButton {background-color: #3498DB; border-radius: 10px; color: white;}
                QPushButton:hover {background-color: #2980B9;}
            """)
            btn.clicked.connect(lambda checked, p=path: self.run_software(p))
            
            row = i // 3
            col = i % 3
            self.software_layout.addWidget(btn, row, col, Qt.AlignCenter)
            
    def run_software(self, path):
        try:
            if os.path.exists(path) or path in ["calc.exe", "explorer.exe", "notepad.exe"]:
                subprocess.Popen(path, shell=True)
        except Exception as e:
            print(f"启动软件失败: {e}")
            
    def show_desktop(self):
        os.system("powershell.exe -Command \"(New-Object -ComObject Shell.Application).ToggleDesktop()\"")
        self.showMinimized()
        
    def open_usb(self):
        subprocess.Popen("explorer.exe shell:MyComputerFolder", shell=True)
        
    def shutdown_computer(self):
        os.system("shutdown /s /t 60")
        
    def closeEvent(self, event):
        # 关闭主窗口时最小化到托盘
        event.ignore()
        self.hide()
        self.tray_icon.showMessage("提示", "程序已最小化到任务栏托盘", QSystemTrayIcon.Information, 2000)
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.showMinimized()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # 确保程序只有一个实例运行
    app.setQuitOnLastWindowClosed(False)
    window = ClassDesktop()
    window.show()
    sys.exit(app.exec_())
