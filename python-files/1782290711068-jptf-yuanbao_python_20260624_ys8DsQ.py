# -*- coding: utf-8 -*-
import sys
import os
import time
import datetime
import threading
import pandas as pd

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QLineEdit, QFileDialog, QVBoxLayout, QHBoxLayout,
    QProgressBar, QTextEdit, QMessageBox, QGroupBox, QSpinBox
)
from PyQt5.QtCore import pyqtSignal, QObject, QTimer

# ======================
# 配置
# ======================
KEYWORDS = [u"网办地址", u"网址", u"链接", u"URL", u"访问地址"]
DEFAULT_SAVE_DIR = os.path.join(os.path.expanduser(u"~"), u"Desktop")

STATUS_MAP = {
    200: u"正常访问",
    301: u"永久重定向",
    302: u"临时重定向",
    403: u"禁止访问",
    404: u"页面不存在",
    500: u"内部服务器错误",
    502: u"网关错误",
    503: u"服务不可用",
}

# ======================
# 信号
# ======================
class Signals(QObject):
    log = pyqtSignal(str)
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)


# ======================
# URL 检查（urllib 版）
# ======================
import urllib.request
import urllib.error

def check_url_urllib(url, timeout):
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = resp.getcode()
            msg = STATUS_MAP.get(code, u"未知状态码({})".format(code))
            return u"{} - {}".format(code, msg)
    except urllib.error.HTTPError as e:
        code = e.code
        msg = STATUS_MAP.get(code, u"HTTP错误")
        return u"{} - {}".format(code, msg)
    except urllib.error.URLError:
        return u"失败 - 无法连接"
    except Exception:
        return u"失败 - 访问超时"


# ======================
# 检查线程
# ======================
class CheckThread(threading.Thread):
    def __init__(self, df, col, timeout, retry, signals):
        super(CheckThread, self).__init__()
        self.df = df
        self.col = col
        self.timeout = timeout
        self.retry = retry
        self.signals = signals

    def run(self):
        total = len(self.df)
        results = []

        for idx, row in self.df.iterrows():
            url = str(row[self.col]).strip()
            if not url.startswith("http"):
                url = "http://" + url

            result = None
            for attempt in range(1, self.retry + 1):
                self.signals.log.emit(u"[{}次] {}".format(attempt, url))
                result = check_url_urllib(url, self.timeout)
                if u"失败" not in result:
                    break
                time.sleep(1)

            results.append(result)
            self.signals.progress.emit(int((idx + 1) / total * 100))

        self.df[u"网址检查结果"] = results
        self.signals.finished.emit(u"检查完成")


# ======================
# 主窗口
# ======================
class MainWindow(QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle(u"政务服务网址批量检查系统（定时版）")
        self.resize(850, 600)
        self.signals = Signals()
        self.init_ui()
        self.start_timer()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # ---- Excel ----
        file_group = QGroupBox(u"Excel 文件")
        h1 = QHBoxLayout()
        self.file_input = QLineEdit()
        btn_file = QPushButton(u"选择文件")
        btn_file.clicked.connect(self.select_file)
        h1.addWidget(self.file_input)
        h1.addWidget(btn_file)
        file_group.setLayout(h1)

        # ---- 参数 ----
        param_group = QGroupBox(u"检查参数")
        h2 = QHBoxLayout()

        h2.addWidget(QLabel(u"超时(秒)："))
        self.timeout_input = QLineEdit("10")
        h2.addWidget(self.timeout_input)

        h2.addWidget(QLabel(u"失败重试次数："))
        self.retry_input = QSpinBox()
        self.retry_input.setValue(3)
        h2.addWidget(self.retry_input)

        h2.addWidget(QLabel(u"保存目录："))
        self.save_input = QLineEdit(DEFAULT_SAVE_DIR)
        btn_save = QPushButton(u"选择")
        btn_save.clicked.connect(self.select_dir)
        h2.addWidget(self.save_input)
        h2.addWidget(btn_save)
        param_group.setLayout(h2)

        # ---- 定时 ----
        timer_group = QGroupBox(u"定时任务（每天自动执行）")
        h3 = QHBoxLayout()
        h3.addWidget(QLabel(u"每日执行时间："))
        self.hour_input = QSpinBox()
        self.hour_input.setRange(0, 23)
        self.hour_input.setValue(9)
        self.minute_input = QSpinBox()
        self.minute_input.setRange(0, 59)
        self.minute_input.setValue(0)
        h3.addWidget(self.hour_input)
        h3.addWidget(QLabel(u"时"))
        h3.addWidget(self.minute_input)
        h3.addWidget(QLabel(u"分"))
        timer_group.setLayout(h3)

        # ---- 进度 / 日志 ----
        self.progress = QProgressBar()
        self.progress.setValue(0)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)

        # ---- 按钮 ----
        btn_start = QPushButton(u"立即开始检查")
        btn_start.clicked.connect(self.start_check)

        main_layout.addWidget(file_group)
        main_layout.addWidget(param_group)
        main_layout.addWidget(timer_group)
        main_layout.addWidget(self.progress)
        main_layout.addWidget(QLabel(u"检查日志："))
        main_layout.addWidget(self.log_output)
        main_layout.addWidget(btn_start)

        self.setLayout(main_layout)

        self.signals.log.connect(self.log_output.append)
        self.signals.progress.connect(self.progress.setValue)
        self.signals.finished.connect(self.on_finished)

    # ====================
    # 功能方法
    # ====================
    def select_file(self):
        file_, _ = QFileDialog.getOpenFileName(
            self, u"选择Excel文件", "", u"Excel Files (*.xlsx *.xls)"
        )
        if file_:
            self.file_input.setText(file_)

    def select_dir(self):
        d = QFileDialog.getExistingDirectory(self, u"选择保存目录")
        if d:
            self.save_input.setText(d)

    def find_url_column(self, df):
        for col in df.columns:
            for kw in KEYWORDS:
                if kw in col:
                    return col
        raise ValueError(u"未找到网址列")

    def start_check(self):
        file_ = self.file_input.text()
        if not file_:
            QMessageBox.warning(self, u"提示", u"请选择Excel文件")
            return

        df = pd.read_excel(file_)
        col = self.find_url_column(df)
        timeout = int(self.timeout_input.text())
        retry = self.retry_input.value()

        self.progress.setValue(0)
        self.log_output.clear()

        self.thread = CheckThread(
            df, col, timeout, retry, self.signals
        )
        self.thread.start()

    def on_finished(self, msg):
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        file_name = u"{} 政务服务网址检查结果.xlsx".format(today)
        save_path = os.path.join(self.save_input.text(), file_name)
        self.thread.df.to_excel(save_path, index=False)

        QMessageBox.information(self, u"完成", u"结果已保存：\n{}".format(save_path))
        os.startfile(save_path)

    # ====================
    # 定时任务
    # ====================
    def start_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_schedule)
        self.timer.start(60 * 1000)

    def check_schedule(self):
        now = datetime.datetime.now()
        target = datetime.datetime(
            now.year, now.month, now.day,
            self.hour_input.value(),
            self.minute_input.value()
        )

        if now.hour == target.hour and now.minute == target.minute:
            if not hasattr(self, "last_run") or self.last_run != now.date():
                self.last_run = now.date()
                self.signals.log.emit(u"⏰ 定时任务触发")
                self.start_check()


# ======================
# 启动
# ======================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())