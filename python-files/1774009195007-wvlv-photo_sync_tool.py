import os
import shutil
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QFileDialog,
    QVBoxLayout, QWidget, QLabel, QMessageBox, QProgressBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import sys

# 定义文件处理线程（避免界面卡顿）
class FileProcessThread(QThread):
    progress_update = pyqtSignal(int)  # 进度更新信号
    finished_signal = pyqtSignal(str)  # 完成信号
    error_signal = pyqtSignal(str)     # 错误信号

    def __init__(self, mode, source_path, jpg_folder=None, arw_source=None, arw_target=None):
        super().__init__()
        self.mode = mode  # 1: 分开存储  2: 同步ARW
        self.source_path = source_path
        self.jpg_folder = jpg_folder
        self.arw_source = arw_source
        self.arw_target = arw_target

    def run(self):
        try:
            if self.mode == 1:
                self.split_files()
            elif self.mode == 2:
                self.sync_arw()
        except Exception as e:
            self.error_signal.emit(f"处理出错：{str(e)}")

    # 功能1：分开存储JPG/ARW文件
    def split_files(self):
        # 创建目标文件夹
        jpg_target = os.path.join(self.source_path, "JPG_待筛选")
        arw_target = os.path.join(self.source_path, "ARW_原片")
        os.makedirs(jpg_target, exist_ok=True)
        os.makedirs(arw_target, exist_ok=True)

        # 获取所有文件
        all_files = [f for f in os.listdir(self.source_path) if os.path.isfile(os.path.join(self.source_path, f))]
        total_files = len(all_files)
        
        if total_files == 0:
            self.finished_signal.emit("源文件夹中未找到任何文件！")
            return

        # 遍历文件并分类
        processed = 0
        for file_name in all_files:
            file_ext = file_name.split('.')[-1].upper()
            file_path = os.path.join(self.source_path, file_name)
            
            if file_ext == "JPG":
                shutil.copy2(file_path, os.path.join(jpg_target, file_name))
            elif file_ext == "ARW":
                shutil.copy2(file_path, os.path.join(arw_target, file_name))
            
            processed += 1
            self.progress_update.emit(int(processed / total_files * 100))

        self.finished_signal.emit(f"分类完成！共处理 {processed} 个文件\nJPG文件已保存至：{jpg_target}\nARW文件已保存至：{arw_target}")

    # 功能2：根据筛选后的JPG同步ARW
    def sync_arw(self):
        # 创建ARW_已同步文件夹
        os.makedirs(self.arw_target, exist_ok=True)

        # 获取筛选后的JPG文件名（不含扩展名）
        jpg_files = []
        for f in os.listdir(self.jpg_folder):
            if f.lower().endswith('.jpg'):
                jpg_files.append(os.path.splitext(f)[0])

        if not jpg_files:
            self.finished_signal.emit("JPG_待筛选文件夹中未找到任何JPG文件！")
            return

        # 遍历ARW原片，同步同名文件
        total_arw = len([f for f in os.listdir(self.arw_source) if f.lower().endswith('.arw')])
        synced = 0
        processed = 0

        for file_name in os.listdir(self.arw_source):
            if file_name.lower().endswith('.arw'):
                file_base = os.path.splitext(file_name)[0]
                if file_base in jpg_files:
                    # 移动同名ARW文件
                    src_path = os.path.join(self.arw_source, file_name)
                    dst_path = os.path.join(self.arw_target, file_name)
                    shutil.move(src_path, dst_path)
                    synced += 1
                processed += 1
                self.progress_update.emit(int(processed / total_arw * 100))

        self.finished_signal.emit(f"同步完成！\n共找到 {len(jpg_files)} 个筛选后的JPG文件\n成功同步 {synced} 个ARW文件至：{self.arw_target}")

# 主窗口界面
class PhotoSyncTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("照片筛选同步工具")
        self.setFixedSize(500, 300)
        self.source_path = ""
        self.init_ui()

    def init_ui(self):
        # 布局设置
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        self.setCentralWidget(central_widget)

        # 选择文件夹按钮
        self.select_btn = QPushButton("选择源文件夹")
        self.select_btn.clicked.connect(self.select_source_folder)
        layout.addWidget(self.select_btn, alignment=Qt.AlignCenter)

        # 源文件夹路径显示
        self.path_label = QLabel("未选择文件夹")
        self.path_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.path_label)

        # 功能按钮1：分开存储JPG/ARW
        self.split_btn = QPushButton("分开储存JPG/ARW")
        self.split_btn.clicked.connect(self.start_split_files)
        self.split_btn.setEnabled(False)
        layout.addWidget(self.split_btn, alignment=Qt.AlignCenter)

        # 功能按钮2：同步ARW
        self.sync_btn = QPushButton("根据筛选后的JPG同步ARW")
        self.sync_btn.clicked.connect(self.start_sync_arw)
        self.sync_btn.setEnabled(False)
        layout.addWidget(self.sync_btn, alignment=Qt.AlignCenter)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # 状态提示
        self.status_label = QLabel("就绪")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

    # 选择源文件夹
    def select_source_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择源文件夹")
        if folder:
            self.source_path = folder
            self.path_label.setText(f"源文件夹：{folder}")
            self.split_btn.setEnabled(True)
            self.sync_btn.setEnabled(True)
            self.status_label.setText("已选择文件夹，可开始操作")

    # 启动分开存储线程
    def start_split_files(self):
        self.split_btn.setEnabled(False)
        self.sync_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("正在分类文件...")

        # 创建线程
        self.thread = FileProcessThread(mode=1, source_path=self.source_path)
        self.thread.progress_update.connect(self.progress_bar.setValue)
        self.thread.finished_signal.connect(self.on_process_finished)
        self.thread.error_signal.connect(self.on_process_error)
        self.thread.start()

    # 启动同步ARW线程
    def start_sync_arw(self):
        # 检查必要文件夹是否存在
        jpg_folder = os.path.join(self.source_path, "JPG_待筛选")
        arw_source = os.path.join(self.source_path, "ARW_原片")
        arw_target = os.path.join(self.source_path, "ARW_已同步")

        if not os.path.exists(jpg_folder):
            QMessageBox.warning(self, "警告", "未找到JPG_待筛选文件夹，请先执行「分开储存JPG/ARW」操作！")
            return
        if not os.path.exists(arw_source):
            QMessageBox.warning(self, "警告", "未找到ARW_原片文件夹，请先执行「分开储存JPG/ARW」操作！")
            return

        self.split_btn.setEnabled(False)
        self.sync_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("正在同步ARW文件...")

        # 创建线程
        self.thread = FileProcessThread(
            mode=2,
            source_path=self.source_path,
            jpg_folder=jpg_folder,
            arw_source=arw_source,
            arw_target=arw_target
        )
        self.thread.progress_update.connect(self.progress_bar.setValue)
        self.thread.finished_signal.connect(self.on_process_finished)
        self.thread.error_signal.connect(self.on_process_error)
        self.thread.start()

    # 处理完成回调
    def on_process_finished(self, msg):
        self.progress_bar.setValue(100)
        self.status_label.setText("操作完成")
        self.split_btn.setEnabled(True)
        self.sync_btn.setEnabled(True)
        QMessageBox.information(self, "提示", msg)
        self.progress_bar.setVisible(False)

    # 错误处理回调
    def on_process_error(self, msg):
        self.status_label.setText("操作出错")
        self.split_btn.setEnabled(True)
        self.sync_btn.setEnabled(True)
        QMessageBox.critical(self, "错误", msg)
        self.progress_bar.setVisible(False)

# 程序入口
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PhotoSyncTool()
    window.show()
    sys.exit(app.exec_())