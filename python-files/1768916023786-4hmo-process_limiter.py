import sys
import psutil
import win32process
import win32api
import win32con
import win32job
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QLabel
)
from PySide6.QtCore import Qt

# ================== 黑色科技风样式 ==================
STYLE = """
QWidget {
    background-color: #0b0f14;
    color: #00f6ff;
    font-size: 14px;
}
QPushButton {
    background-color: #111820;
    border: 1px solid #00f6ff;
    padding: 8px;
}
QPushButton:hover {
    background-color: #00f6ff;
    color: #000;
}
QListWidget {
    background-color: #05080d;
    border: 1px solid #00f6ff;
}
"""

# ================== 主窗口 ==================
class ProcessLimiter(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("进程资源限制器")
        self.resize(500, 600)
        self.setStyleSheet(STYLE)

        layout = QVBoxLayout(self)

        self.label = QLabel("选择要限制的进程（可多选）")
        layout.addWidget(self.label)

        self.listWidget = QListWidget()
        self.listWidget.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(self.listWidget)

        self.btn_limit = QPushButton("开始限制")
        self.btn_restore = QPushButton("恢复默认")

        layout.addWidget(self.btn_limit)
        layout.addWidget(self.btn_restore)

        self.btn_limit.clicked.connect(self.limit_process)
        self.btn_restore.clicked.connect(self.restore_process)

        self.load_processes()

    def load_processes(self):
        self.listWidget.clear()
        for p in psutil.process_iter(['pid', 'name']):
            item = QListWidgetItem(f"{p.info['name']}  (PID {p.info['pid']})")
            item.setData(Qt.UserRole, p.info['pid'])
            self.listWidget.addItem(item)

    def limit_process(self):
        for item in self.listWidget.selectedItems():
            pid = item.data(Qt.UserRole)
            try:
                p = psutil.Process(pid)
                p.nice(psutil.IDLE_PRIORITY_CLASS)

                handle = win32api.OpenProcess(
                    win32con.PROCESS_ALL_ACCESS, False, pid
                )

                # 降低 IO 优先级
                win32process.SetPriorityClass(
                    handle, win32process.IDLE_PRIORITY_CLASS
                )

                # 内存限制（约 200MB）
                job = win32job.CreateJobObject(None, "")
                info = win32job.QueryInformationJobObject(
                    job, win32job.JobObjectExtendedLimitInformation
                )
                info['ProcessMemoryLimit'] = 200 * 1024 * 1024
                info['BasicLimitInformation']['LimitFlags'] = (
                    win32job.JOB_OBJECT_LIMIT_PROCESS_MEMORY
                )
                win32job.SetInformationJobObject(
                    job, win32job.JobObjectExtendedLimitInformation, info
                )
                win32job.AssignProcessToJobObject(job, handle)

            except Exception as e:
                print(f"无法限制 PID {pid}: {e}")

    def restore_process(self):
        for item in self.listWidget.selectedItems():
            pid = item.data(Qt.UserRole)
            try:
                p = psutil.Process(pid)
                p.nice(psutil.NORMAL_PRIORITY_CLASS)
            except:
                pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = ProcessLimiter()
    win.show()
    sys.exit(app.exec())