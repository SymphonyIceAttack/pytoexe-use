import sys
import os
import re
import shutil
import patoolib
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QFileDialog, 
                             QLineEdit, QTextEdit, QProgressBar, QDialog,
                             QInputDialog, QMessageBox, QGroupBox, QCheckBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QMimeData
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QFont, QIcon

class PasswordDialog(QDialog):
    def __init__(self, archive_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle("需要密码")
        self.setGeometry(100, 100, 400, 150)
        self.password = None
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"压缩包 [{archive_name}] 已加密，请输入密码："))
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("输入密码...")
        layout.addWidget(self.password_input)
        
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("跳过")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def get_password(self):
        return self.password_input.text()

class ExtractWorker(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(bool, str)
    password_signal = pyqtSignal(str, object)  # archive_path, callback
    
    def __init__(self, file_paths, output_dir, auto_rename, recursive, parent=None):
        super().__init__(parent)
        self.file_paths = file_paths
        self.output_dir = output_dir
        self.auto_rename = auto_rename
        self.recursive = recursive
        self.password_cache = {}
        self.is_running = True
        
    def run(self):
        try:
            total = len(self.file_paths)
            for idx, file_path in enumerate(self.file_paths):
                if not self.is_running:
                    break
                self.process_file(file_path)
                self.progress_signal.emit(int((idx + 1) / total * 100))
            self.finished_signal.emit(True, "处理完成")
        except Exception as e:
            self.finished_signal.emit(False, str(e))
    
    def process_file(self, file_path):
        path = Path(file_path)
        self.log_signal.emit(f"正在处理: {path.name}")
        
        # 自动重命名伪装文件
        if self.auto_rename and path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.mp4']:
            new_path = path.with_suffix('.zip')
            try:
                shutil.copy2(file_path, new_path)
                self.log_signal.emit(f"  已将 {path.suffix} 伪装文件复制为 {new_path.name}")
                path = new_path
                file_path = str(new_path)
            except Exception as e:
                self.log_signal.emit(f"  错误: 无法复制文件 - {e}")
                return
        
        # 检测分卷压缩文件
        if self.is_volume_file(path):
            self.handle_volume_extract(file_path)
        else:
            self.extract_archive(file_path, self.output_dir)
    
    def is_volume_file(self, path):
        """检测是否为分卷压缩文件"""
        name = path.name.lower()
        # RAR分卷: .part1.rar, .part01.rar, .part001.rar
        if re.search(r'\.part\d+\.rar$', name):
            return True
        # ZIP分卷: .z01, .z02... 或 .zip, .z01...
        if re.search(r'\.z\d+$', name):
            return True
        # 7z分卷: .7z.001, .7z.002...
        if re.search(r'\.7z\.\d+$', name):
            return True
        return False
    
    def get_volume_main_file(self, path):
        """获取分卷的主文件"""
        name = path.name.lower()
        parent = path.parent
        
        # RAR分卷: 找 .part1.rar
        if '.part' in name and name.endswith('.rar'):
            # 返回第一个分卷
            match = re.search(r'(.*?)\.part\d+\.rar$', name)
            if match:
                base = match.group(1)
                # 找 part1 或 part01 或 part001
                for part_file in parent.glob(f"{base}.part*.rar"):
                    if 'part1' in part_file.name.lower():
                        return part_file
                return path
        
        # ZIP分卷: 找 .zip 文件
        if name.endswith('.zip') or re.search(r'\.z\d+$', name):
            base = re.sub(r'\.z(ip|\d+)$', '', name)
            zip_file = parent / f"{base}.zip"
            if zip_file.exists():
                return zip_file
        
        # 7z分卷: 找 .7z.001
        if '.7z.' in name:
            base = re.sub(r'\.7z\.\d+$', '', name)
            first_part = parent / f"{base}.7z.001"
            if first_part.exists():
                return first_part
        
        return path
    
    def handle_volume_extract(self, file_path):
        """处理分卷解压"""
        path = Path(file_path)
        main_file = self.get_volume_main_file(path)
        
        if main_file != path:
            self.log_signal.emit(f"  检测到分卷压缩，使用主文件: {main_file.name}")
        
        self.extract_archive(str(main_file), self.output_dir)
    
    def extract_archive(self, archive_path, output_dir):
        """解压单个压缩包"""
        archive_name = Path(archive_path).name
        
        try:
            # 尝试无密码解压
            try:
                patoolib.extract_archive(archive_path, outdir=output_dir, verbosity=-1)
                self.log_signal.emit(f"  ✓ 解压成功: {archive_name}")
            except Exception as e:
                if "password" in str(e).lower() or "encrypted" in str(e).lower():
                    # 需要密码
                    password = self.get_password(archive_name)
                    if password:
                        patoolib.extract_archive(archive_path, outdir=output_dir, 
                                               verbosity=-1, password=password)
                        self.log_signal.emit(f"  ✓ 使用密码解压成功: {archive_name}")
                    else:
                        self.log_signal.emit(f"  ✗ 跳过加密文件: {archive_name}")
                        return
                else:
                    raise e
            
            # 递归解压
            if self.recursive:
                self.recursive_extract(output_dir)
                
        except Exception as e:
            self.log_signal.emit(f"  ✗ 解压失败 {archive_name}: {str(e)}")
    
    def get_password(self, archive_name):
        """获取密码（带缓存）"""
        if archive_name in self.password_cache:
            return self.password_cache[archive_name]
        
        # 使用信号在主线程显示密码对话框
        result = {"password": None, "done": False}
        
        def callback(pwd):
            result["password"] = pwd
            result["done"] = True
        
        self.password_signal.emit(archive_name, callback)
        
        # 等待用户输入（这里简化处理，实际应该使用事件循环）
        import time
        while not result["done"]:
            time.sleep(0.1)
        
        if result["password"]:
            self.password_cache[archive_name] = result["password"]
        return result["password"]
    
    def recursive_extract(self, directory):
        """递归解压目录中的压缩包"""
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_lower = file.lower()
                if any(file_lower.endswith(ext) for ext in ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2']):
                    full_path = os.path.join(root, file)
                    self.log_signal.emit(f"  发现嵌套压缩包: {file}")
                    self.extract_archive(full_path, root)

class DropArea(QLabel):
    dropped = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText("\n\n📁 拖拽文件到此处\n\n支持：ZIP, RAR, 7Z, TAR, GZ 及伪装文件(JPG/PNG/MP4)\n")
        self.setStyleSheet("""
            QLabel {
                border: 3px dashed #aaa;
                border-radius: 10px;
                background-color: #f0f0f0;
                font-size: 14px;
                color: #555;
                padding: 20px;
            }
            QLabel:hover {
                background-color: #e0e0e0;
                border-color: #888;
            }
        """)
        self.setAcceptDrops(True)
        self.setMinimumHeight(150)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("""
                QLabel {
                    border: 3px solid #4CAF50;
                    border-radius: 10px;
                    background-color: #E8F5E9;
                    font-size: 14px;
                    color: #2E7D32;
                    padding: 20px;
                }
            """)
    
    def dragLeaveEvent(self, event):
        self.setStyleSheet("""
            QLabel {
                border: 3px dashed #aaa;
                border-radius: 10px;
                background-color: #f0f0f0;
                font-size: 14px;
                color: #555;
                padding: 20px;
            }
        """)
    
    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet("""
            QLabel {
                border: 3px dashed #aaa;
                border-radius: 10px;
                background-color: #f0f0f0;
                font-size: 14px;
                color: #555;
                padding: 20px;
            }
        """)
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        self.dropped.emit(files)

class SmartExtractor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("智能解压工具 Smart Extractor")
        self.setGeometry(100, 100, 800, 600)
        self.worker = None
        self.init_ui()
    
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 拖拽区域
        self.drop_area = DropArea()
        self.drop_area.dropped.connect(self.handle_dropped_files)
        layout.addWidget(self.drop_area)
        
        # 设置区域
        settings_group = QGroupBox("设置选项")
        settings_layout = QVBoxLayout()
        
        # 输出目录选择
        dir_layout = QHBoxLayout()
        self.output_dir = QLineEdit()
        self.output_dir.setPlaceholderText("默认：与压缩包同目录")
        dir_btn = QPushButton("选择解压目录")
        dir_btn.clicked.connect(self.select_output_dir)
        dir_layout.addWidget(QLabel("输出目录:"))
        dir_layout.addWidget(self.output_dir)
        dir_layout.addWidget(dir_btn)
        settings_layout.addLayout(dir_layout)
        
        # 选项复选框
        self.auto_rename_cb = QCheckBox("自动将 .jpg/.png/.mp4 伪装文件改为 .zip 并解压")
        self.auto_rename_cb.setChecked(True)
        settings_layout.addWidget(self.auto_rename_cb)
        
        self.recursive_cb = QCheckBox("递归解压（解压后再解压内部压缩包）")
        self.recursive_cb.setChecked(True)
        settings_layout.addWidget(self.recursive_cb)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # 进度条
        self.progress = QProgressBar()
        layout.addWidget(self.progress)
        
        # 日志区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setPlaceholderText("日志将显示在这里...")
        layout.addWidget(self.log_text)
        
        # 控制按钮
        btn_layout = QHBoxLayout()
        clear_btn = QPushButton("清空日志")
        clear_btn.clicked.connect(self.log_text.clear)
        btn_layout.addWidget(clear_btn)
        
        self.start_btn = QPushButton("开始解压")
        self.start_btn.clicked.connect(self.start_extraction)
        self.start_btn.setEnabled(False)
        btn_layout.addWidget(self.start_btn)
        
        layout.addLayout(btn_layout)
        
        self.pending_files = []
    
    def select_output_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择解压目录")
        if dir_path:
            self.output_dir.setText(dir_path)
    
    def handle_dropped_files(self, files):
        valid_extensions = ('.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', 
                           '.jpg', '.jpeg', '.png', '.mp4', '.z01', '.z02')
        
        valid_files = [f for f in files if f.lower().endswith(valid_extensions)]
        
        if not valid_files:
            QMessageBox.warning(self, "警告", "请拖入有效的压缩文件或伪装文件！")
            return
        
        self.pending_files = valid_files
        self.log_text.append(f"已添加 {len(valid_files)} 个文件到队列")
        for f in valid_files:
            self.log_text.append(f"  - {os.path.basename(f)}")
        self.start_btn.setEnabled(True)
    
    def start_extraction(self):
        if not self.pending_files:
            return
        
        output_dir = self.output_dir.text() or None
        
        self.worker = ExtractWorker(
            self.pending_files,
            output_dir,
            self.auto_rename_cb.isChecked(),
            self.recursive_cb.isChecked()
        )
        self.worker.log_signal.connect(self.update_log)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.finished_signal.connect(self.extraction_finished)
        self.worker.password_signal.connect(self.show_password_dialog)
        
        self.start_btn.setEnabled(False)
        self.drop_area.setEnabled(False)
        self.worker.start()
    
    def update_log(self, message):
        self.log_text.append(message)
    
    def update_progress(self, value):
        self.progress.setValue(value)
    
    def extraction_finished(self, success, message):
        self.start_btn.setEnabled(True)
        self.drop_area.setEnabled(True)
        if success:
            self.log_text.append("\n✅ 所有任务处理完成！")
            QMessageBox.information(self, "完成", "解压任务已完成！")
        else:
            QMessageBox.critical(self, "错误", f"处理过程中出错：{message}")
        self.progress.setValue(0)
        self.pending_files = []
    
    def show_password_dialog(self, archive_name, callback):
        """在主线程显示密码对话框"""
        dialog = PasswordDialog(archive_name, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            callback(dialog.get_password())
        else:
            callback(None)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # 设置应用程序字体
    font = QFont("Microsoft YaHei", 9)
    app.setFont(font)
    
    window = SmartExtractor()
    window.show()
    sys.exit(app.exec())
