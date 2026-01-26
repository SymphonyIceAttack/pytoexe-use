import sys
import os
import random
import time
import torch
from torchvision import transforms
from PIL import Image, ImageDraw
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QFont, QPalette, QColor

# 设备配置
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

# 图像预处理
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])


class DetectionThread(QThread):
    update_progress = pyqtSignal(str)
    finished = pyqtSignal(list, list, float)

    def __init__(self, model, disease_folder, pest_folder, num_samples):
        super().__init__()
        self.model = model
        self.disease_folder = disease_folder
        self.pest_folder = pest_folder
        self.num_samples = num_samples

    def run(self):
        start_time = time.time()

        # 获取病害图片
        disease_imgs = []
        if os.path.exists(self.disease_folder):
            for f in os.listdir(self.disease_folder):
                if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff')):
                    disease_imgs.append(os.path.join(self.disease_folder, f))

        # 获取虫害图片
        pest_imgs = []
        if os.path.exists(self.pest_folder):
            for f in os.listdir(self.pest_folder):
                if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff')):
                    pest_imgs.append(os.path.join(self.pest_folder, f))

        # 随机选择
        random.shuffle(disease_imgs)
        random.shuffle(pest_imgs)

        disease_results = []
        pest_results = []

        # 处理病害
        for i, path in enumerate(disease_imgs[:self.num_samples]):
            result = self.predict_image(path, 0)
            if result:
                disease_results.append(result)
            self.update_progress.emit(f"病害检测: {i + 1}/{min(self.num_samples, len(disease_imgs))}")

        # 处理虫害
        for i, path in enumerate(pest_imgs[:self.num_samples]):
            result = self.predict_image(path, 1)
            if result:
                pest_results.append(result)
            self.update_progress.emit(f"虫害检测: {i + 1}/{min(self.num_samples, len(pest_imgs))}")

        elapsed_time = time.time() - start_time
        self.finished.emit(disease_results, pest_results, elapsed_time)

    def predict_image(self, img_path, true_label):
        try:
            img = Image.open(img_path).convert('RGB')
            img_tensor = transform(img).unsqueeze(0).to(DEVICE)

            with torch.no_grad():
                output = self.model(img_tensor)
                predicted = torch.argmax(output, dim=1).item()
                probabilities = torch.softmax(output, dim=1)[0]
                confidence = probabilities[predicted].item() * 100

            return {
                'image': img,
                'path': img_path,
                'predicted': predicted,  # 0:病害, 1:虫害
                'true': true_label,
                'confidence': confidence,
                'correct': predicted == true_label,
                'filename': os.path.basename(img_path)
            }
        except Exception as e:
            print(f"预测错误 {img_path}: {e}")
            return None


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.model = None
        self.disease_folder = ""
        self.pest_folder = ""
        self.model_loaded = False
        self.all_results = []  # 存储所有检测结果
        self.current_index = 0  # 当前显示图片的索引
        self.detection_time = 0  # 检测用时

        # 加载模型
        if self.load_model():
            self.init_ui()
        else:
            sys.exit(1)

    def load_model(self):
        """加载模型"""
        try:
            model_path = 'checkpoints/MN4/final_model.pth'
            print(f"正在加载模型: {model_path}")
            self.model = torch.load(model_path, map_location=DEVICE)
            self.model.eval()
            print("✓ 模型加载成功")
            self.model_loaded = True
            return True
        except Exception as e:
            print(f"模型加载失败: {e}")
            # 如果默认路径不存在，让用户选择
            options = QFileDialog.Options()
            model_file, _ = QFileDialog.getOpenFileName(
                self, "选择模型文件", "",
                "PyTorch模型文件 (*.pth *.pt);;所有文件 (*)",
                options=options
            )

            if not model_file:
                QMessageBox.critical(self, "错误", "必须选择模型文件!")
                self.model_loaded = False
                return False

            try:
                print(f"正在加载模型: {model_file}")
                self.model = torch.load(model_file, map_location=DEVICE)
                self.model.eval()
                print("✓ 模型加载成功")
                self.model_loaded = True
                return True
            except Exception as e2:
                QMessageBox.critical(self, "错误", f"加载模型失败:\n{str(e2)}")
                self.model_loaded = False
                return False

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("基于MobileNetV2的植物病虫害检测系统")
        self.setGeometry(100, 100, 1600, 900)

        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f5ff;
            }
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 2px solid #d1d9e6;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px 0 10px;
                color: #2c3e50;
            }
            QPushButton {
                background-color: #4a6fa5;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #3d5a80;
            }
            QPushButton:disabled {
                background-color: #b8c2cc;
            }
            QPushButton#startBtn {
                background-color: #28a745;
                font-size: 14px;
            }
            QPushButton#startBtn:hover {
                background-color: #218838;
            }
            QPushButton#saveBtn {
                background-color: #17a2b8;
            }
            QPushButton#saveBtn:hover {
                background-color: #138496;
            }
            QPushButton#exitBtn {
                background-color: #dc3545;
            }
            QPushButton#exitBtn:hover {
                background-color: #c82333;
            }
            QLabel {
                padding: 6px;
                font-size: 12px;
            }
            QSpinBox, QComboBox, QLineEdit {
                padding: 8px;
                border: 1px solid #d1d9e6;
                border-radius: 5px;
                font-size: 12px;
                background-color: white;
            }
            QTextEdit, QListWidget {
                border: 1px solid #d1d9e6;
                border-radius: 5px;
                font-size: 12px;
                padding: 8px;
                background-color: white;
            }
            QProgressBar {
                border: 1px solid #d1d9e6;
                border-radius: 5px;
                text-align: center;
                font-size: 12px;
            }
            QProgressBar::chunk {
                background-color: #4a6fa5;
                border-radius: 5px;
            }
        """)

        # 主部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 创建垂直布局，包含标题和主要内容
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # ========== 标题栏 ==========
        title_widget = QWidget()
        title_widget.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
            }
        """)
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)

        # 添加左侧占位
        title_layout.addStretch()

        # 添加标题标签（居中）
        title_label = QLabel("基于MobileNetV2的植物病虫害检测系统")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 26px;
                font-weight: bold;
                padding: 20px;
                letter-spacing: 2px;
                font-family: "Microsoft YaHei", "SimHei", sans-serif;
            }
        """)
        title_layout.addWidget(title_label)

        # 添加右侧占位
        title_layout.addStretch()

        # 将标题栏添加到主布局
        main_layout.addWidget(title_widget)

        # ========== 主要内容区域 ==========
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(20, 20, 20, 20)

        # ========== 左半部分 ==========
        left_widget = QWidget()
        left_widget.setMaximumWidth(500)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(15)

        # 1. 模型导入模块
        model_group = QGroupBox("🔧 模型导入")
        model_layout = QVBoxLayout()

        self.model_path_label = QLabel("模型路径: checkpoints/MN4/final_model.pth")
        self.model_path_label.setWordWrap(True)
        self.model_path_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #f8f9fa;
                border-radius: 5px;
                border: 1px solid #e9ecef;
            }
        """)

        model_btn = QPushButton("重新选择模型")
        model_btn.clicked.connect(self.reload_model)

        model_layout.addWidget(self.model_path_label)
        model_layout.addWidget(model_btn)
        model_group.setLayout(model_layout)
        left_layout.addWidget(model_group)

        # 2. 文件导入模块
        file_group = QGroupBox("📁 文件导入")
        file_layout = QVBoxLayout()

        # 病害文件夹
        disease_layout = QHBoxLayout()
        disease_label = QLabel("病害文件夹:")
        self.disease_path_label = QLabel("未选择")
        self.disease_path_label.setStyleSheet("color: #6c757d;")
        disease_btn = QPushButton("选择")
        disease_btn.clicked.connect(lambda: self.select_folder('病害'))
        disease_layout.addWidget(disease_label)
        disease_layout.addWidget(self.disease_path_label, 1)
        disease_layout.addWidget(disease_btn)

        # 虫害文件夹
        pest_layout = QHBoxLayout()
        pest_label = QLabel("虫害文件夹:")
        self.pest_path_label = QLabel("未选择")
        self.pest_path_label.setStyleSheet("color: #6c757d;")
        pest_btn = QPushButton("选择")
        pest_btn.clicked.connect(lambda: self.select_folder('虫害'))
        pest_layout.addWidget(pest_label)
        pest_layout.addWidget(self.pest_path_label, 1)
        pest_layout.addWidget(pest_btn)

        # 样本数量
        sample_layout = QHBoxLayout()
        sample_label = QLabel("每类样本数:")
        self.sample_spin = QSpinBox()
        self.sample_spin.setRange(1, 50)
        self.sample_spin.setValue(6)
        sample_layout.addWidget(sample_label)
        sample_layout.addWidget(self.sample_spin, 1)

        file_layout.addLayout(disease_layout)
        file_layout.addLayout(pest_layout)
        file_layout.addLayout(sample_layout)
        file_group.setLayout(file_layout)
        left_layout.addWidget(file_group)

        # 3. 检测结果模块
        result_group = QGroupBox("📊 检测结果")
        result_layout = QVBoxLayout()

        # 用时
        time_layout = QHBoxLayout()
        time_label = QLabel("用时:")
        self.time_label = QLabel("0.00 秒")
        self.time_label.setStyleSheet("font-weight: bold; color: #007bff;")
        time_layout.addWidget(time_label)
        time_layout.addWidget(self.time_label, 1)

        # 目标数目
        count_layout = QHBoxLayout()
        count_label = QLabel("目标数目:")
        self.count_label = QLabel("0")
        self.count_label.setStyleSheet("font-weight: bold; color: #007bff;")
        count_layout.addWidget(count_label)
        count_layout.addWidget(self.count_label, 1)

        # 类型
        type_layout = QHBoxLayout()
        type_label = QLabel("类型:")
        self.type_label = QLabel("-")
        self.type_label.setStyleSheet("font-weight: bold;")
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_label, 1)

        # 置信度
        conf_layout = QHBoxLayout()
        conf_label = QLabel("置信度:")
        self.conf_label = QLabel("-")
        self.conf_label.setStyleSheet("font-weight: bold;")
        conf_layout.addWidget(conf_label)
        conf_layout.addWidget(self.conf_label, 1)

        # 目标位置
        pos_layout = QHBoxLayout()
        pos_label = QLabel("目标位置:")
        self.pos_label = QLabel("-")
        self.pos_label.setWordWrap(True)
        pos_layout.addWidget(pos_label)
        pos_layout.addWidget(self.pos_label, 1)

        result_layout.addLayout(time_layout)
        result_layout.addLayout(count_layout)
        result_layout.addLayout(type_layout)
        result_layout.addLayout(conf_layout)
        result_layout.addLayout(pos_layout)
        result_group.setLayout(result_layout)
        left_layout.addWidget(result_group)

        # 4. 操作模块
        operation_group = QGroupBox("⚙️ 操作")
        operation_layout = QVBoxLayout()

        # 开始检测按钮
        self.detect_btn = QPushButton("开始检测")
        self.detect_btn.clicked.connect(self.start_detection)
        self.detect_btn.setObjectName("startBtn")
        self.detect_btn.setEnabled(False)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)

        # 保存按钮
        self.save_btn = QPushButton("保存结果")
        self.save_btn.clicked.connect(self.save_results)
        self.save_btn.setObjectName("saveBtn")
        self.save_btn.setEnabled(False)

        # 退出按钮
        exit_btn = QPushButton("退出系统")
        exit_btn.clicked.connect(self.close)
        exit_btn.setObjectName("exitBtn")

        operation_layout.addWidget(self.detect_btn)
        operation_layout.addWidget(self.progress_bar)
        operation_layout.addWidget(self.save_btn)
        operation_layout.addWidget(exit_btn)
        operation_group.setLayout(operation_layout)
        left_layout.addWidget(operation_group)

        # 添加伸缩空间
        left_layout.addStretch()

        # ========== 右半部分 ==========
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(15)

        # 1. 检测图片区域
        image_group = QGroupBox("🖼️ 检测图片")
        image_layout = QVBoxLayout()

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumHeight(400)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 3px dashed #dee2e6;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        self.image_label.setText("请先开始检测")

        # 图片导航按钮
        nav_layout = QHBoxLayout()
        nav_layout.addStretch()

        self.prev_btn = QPushButton("◀ 上一张")
        self.prev_btn.clicked.connect(self.show_prev_image)
        self.prev_btn.setEnabled(False)

        self.next_btn = QPushButton("下一张 ▶")
        self.next_btn.clicked.connect(self.show_next_image)
        self.next_btn.setEnabled(False)

        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.next_btn)
        nav_layout.addStretch()

        image_layout.addWidget(self.image_label)
        image_layout.addLayout(nav_layout)
        image_group.setLayout(image_layout)
        right_layout.addWidget(image_group)

        # 2. 检测结果与位置信息
        info_group = QGroupBox("📝 检测结果与位置信息")
        info_layout = QVBoxLayout()

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMaximumHeight(150)
        self.result_text.setText("检测结果将显示在这里")

        # 详细信息表格
        self.detail_table = QTableWidget()
        self.detail_table.setColumnCount(5)
        self.detail_table.setHorizontalHeaderLabels(["文件名", "预测类型", "实际类型", "置信度", "结果"])
        self.detail_table.horizontalHeader().setStretchLastSection(True)
        self.detail_table.setMaximumHeight(150)

        info_layout.addWidget(QLabel("检测详情:"))
        info_layout.addWidget(self.result_text)
        info_layout.addWidget(QLabel("所有检测结果:"))
        info_layout.addWidget(self.detail_table)
        info_group.setLayout(info_layout)
        right_layout.addWidget(info_group)

        # ========== 将左右两部分添加到内容布局 ==========
        content_layout.addWidget(left_widget)
        content_layout.addWidget(right_widget, 1)

        # ========== 将内容区域添加到主布局 ==========
        main_layout.addWidget(content_widget, 1)

    def reload_model(self):
        """重新选择模型"""
        options = QFileDialog.Options()
        model_file, _ = QFileDialog.getOpenFileName(
            self, "选择模型文件", "",
            "PyTorch模型文件 (*.pth *.pt);;所有文件 (*)",
            options=options
        )

        if model_file:
            try:
                print(f"正在加载模型: {model_file}")
                self.model = torch.load(model_file, map_location=DEVICE)
                self.model.eval()
                print("✓ 模型加载成功")
                self.model_path_label.setText(f"模型路径: {model_file}")
                QMessageBox.information(self, "成功", "模型重新加载成功!")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载模型失败:\n{str(e)}")

    def select_folder(self, folder_type):
        """选择文件夹"""
        folder = QFileDialog.getExistingDirectory(self, f"选择{folder_type}文件夹")
        if folder:
            if folder_type == '病害':
                self.disease_folder = folder
                self.disease_path_label.setText(os.path.basename(folder))
                self.disease_path_label.setStyleSheet("color: #28a745; font-weight: bold;")
            else:
                self.pest_folder = folder
                self.pest_path_label.setText(os.path.basename(folder))
                self.pest_path_label.setStyleSheet("color: #dc3545; font-weight: bold;")

            # 检查是否可以开始检测
            if self.disease_folder and self.pest_folder:
                self.detect_btn.setEnabled(True)

    def start_detection(self):
        """开始检测"""
        if not self.disease_folder or not self.pest_folder:
            QMessageBox.warning(self, "警告", "请先选择病害和虫害文件夹")
            return

        # 重置显示
        self.image_label.setText("检测中...")
        self.result_text.setText("检测中，请稍候...")
        self.detail_table.setRowCount(0)

        # 启用进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.status_label = QLabel("检测中...")

        self.detect_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)

        # 创建线程
        self.thread = DetectionThread(
            self.model,
            self.disease_folder,
            self.pest_folder,
            self.sample_spin.value()
        )

        self.thread.update_progress.connect(self.update_progress)
        self.thread.finished.connect(self.show_results)
        self.thread.start()

    def update_progress(self, msg):
        """更新进度"""
        self.result_text.setText(f"状态: {msg}")

        # 简单模拟进度
        if "病害" in msg:
            current = int(msg.split(":")[1].split("/")[0])
            total = int(msg.split("/")[1])
            progress = int((current / total) * 50)
            self.progress_bar.setValue(progress)
        elif "虫害" in msg:
            current = int(msg.split(":")[1].split("/")[0])
            total = int(msg.split("/")[1])
            progress = 50 + int((current / total) * 50)
            self.progress_bar.setValue(progress)

    def show_results(self, disease_results, pest_results, elapsed_time):
        """显示结果"""
        # 保存检测时间和结果
        self.detection_time = elapsed_time
        self.all_results = disease_results + pest_results

        # 更新左侧信息
        self.time_label.setText(f"{elapsed_time:.2f} 秒")
        self.count_label.setText(str(len(self.all_results)))

        # 启用导航按钮
        if len(self.all_results) > 0:
            self.prev_btn.setEnabled(True)
            self.next_btn.setEnabled(True)
            self.save_btn.setEnabled(True)

            # 显示第一张图片
            self.current_index = 0
            self.show_current_image()

        # 更新详情表格
        self.update_detail_table()

        # 隐藏进度条
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)

        self.detect_btn.setEnabled(True)

        # 更新统计信息
        total = len(self.all_results)
        correct = sum(1 for r in self.all_results if r['correct'])
        accuracy = (correct / total * 100) if total > 0 else 0

        disease_correct = sum(1 for r in disease_results if r['correct'])
        pest_correct = sum(1 for r in pest_results if r['correct'])

        result_text = f"""
        ✅ 检测完成！

        检测统计:
        - 总用时: {elapsed_time:.2f}秒
        - 总图片数: {total}张
        - 病害正确: {disease_correct}/{len(disease_results)}张
        - 虫害正确: {pest_correct}/{len(pest_results)}张
        - 总体准确率: {accuracy:.2f}%
        """

        self.result_text.setText(result_text)

    def show_current_image(self):
        """显示当前图片"""
        if 0 <= self.current_index < len(self.all_results):
            result = self.all_results[self.current_index]

            # 显示图片
            self.display_image(self.image_label, result)

            # 更新左侧信息
            self.update_left_info(result)

    def display_image(self, label, result):
        """显示图片结果"""
        try:
            img = result['image']
            draw = ImageDraw.Draw(img)

            # 边框颜色和宽度
            if result['correct']:
                border_color = (46, 204, 113)  # 绿色，正确
            else:
                border_color = (231, 76, 60)  # 红色，错误

            border_width = 8  # 增加边框宽度，使其更明显

            # 绘制边框
            for i in range(border_width):
                draw.rectangle(
                    [i, i, img.width - i - 1, img.height - i - 1],
                    outline=border_color,
                    width=1
                )

            # 转换为QPixmap
            img_rgb = img.convert("RGB")
            data = img_rgb.tobytes("raw", "RGB")
            qimage = QImage(data, img_rgb.width, img_rgb.height, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimage).scaled(
                600, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )

            label.setPixmap(pixmap)

        except Exception as e:
            print(f"图片显示错误: {e}")
            label.setText("❌ 显示错误")
            label.setStyleSheet("""
                QLabel {
                    color: #e74c3c;
                    font-weight: bold;
                    border: 2px dashed #e74c3c;
                    border-radius: 5px;
                }
            """)

    def update_left_info(self, result):
        """更新左侧信息"""
        # 类型
        pred_type = "病害" if result['predicted'] == 0 else "虫害"
        true_type = "病害" if result['true'] == 0 else "虫害"

        # 设置颜色
        if result['correct']:
            color = "#28a745"  # 绿色
            result_text = "正确"
        else:
            color = "#dc3545"  # 红色
            result_text = "错误"

        self.type_label.setText(f"{pred_type} ({result_text})")
        self.type_label.setStyleSheet(f"font-weight: bold; color: {color};")

        # 置信度
        self.conf_label.setText(f"{result['confidence']:.1f}%")
        if result['confidence'] >= 90:
            self.conf_label.setStyleSheet("font-weight: bold; color: #28a745;")
        elif result['confidence'] >= 70:
            self.conf_label.setStyleSheet("font-weight: bold; color: #ffc107;")
        else:
            self.conf_label.setStyleSheet("font-weight: bold; color: #dc3545;")

        # 目标位置
        self.pos_label.setText(result['path'])

    def update_detail_table(self):
        """更新详情表格"""
        self.detail_table.setRowCount(len(self.all_results))

        for i, result in enumerate(self.all_results):
            # 文件名
            filename_item = QTableWidgetItem(result['filename'])

            # 预测类型
            pred_type = "病害" if result['predicted'] == 0 else "虫害"
            pred_item = QTableWidgetItem(pred_type)

            # 实际类型
            true_type = "病害" if result['true'] == 0 else "虫害"
            true_item = QTableWidgetItem(true_type)

            # 置信度
            conf_item = QTableWidgetItem(f"{result['confidence']:.1f}%")

            # 结果
            if result['correct']:
                result_item = QTableWidgetItem("✓ 正确")
                result_item.setForeground(QColor(40, 167, 69))  # 绿色
            else:
                result_item = QTableWidgetItem("✗ 错误")
                result_item.setForeground(QColor(220, 53, 69))  # 红色

            # 设置项到表格
            self.detail_table.setItem(i, 0, filename_item)
            self.detail_table.setItem(i, 1, pred_item)
            self.detail_table.setItem(i, 2, true_item)
            self.detail_table.setItem(i, 3, conf_item)
            self.detail_table.setItem(i, 4, result_item)

        # 调整列宽
        self.detail_table.resizeColumnsToContents()

    def show_prev_image(self):
        """显示上一张图片"""
        if self.current_index > 0:
            self.current_index -= 1
            self.show_current_image()

    def show_next_image(self):
        """显示下一张图片"""
        if self.current_index < len(self.all_results) - 1:
            self.current_index += 1
            self.show_current_image()

    def save_results(self):
        """保存结果"""
        if not self.all_results:
            QMessageBox.warning(self, "警告", "没有检测结果可以保存")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存结果", "detection_results.txt", "文本文件 (*.txt)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("病虫害检测结果报告\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(f"检测时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"检测用时: {self.detection_time:.2f}秒\n")
                    f.write(f"总图片数: {len(self.all_results)}\n\n")

                    # 统计信息
                    correct = sum(1 for r in self.all_results if r['correct'])
                    accuracy = (correct / len(self.all_results) * 100) if self.all_results else 0

                    f.write(f"正确识别数: {correct}\n")
                    f.write(f"总体准确率: {accuracy:.2f}%\n\n")

                    f.write("详细检测结果:\n")
                    f.write("-" * 50 + "\n")

                    for i, result in enumerate(self.all_results):
                        pred_type = "病害" if result['predicted'] == 0 else "虫害"
                        true_type = "病害" if result['true'] == 0 else "虫害"
                        result_text = "正确" if result['correct'] else "错误"

                        f.write(f"{i + 1}. {result['filename']}\n")
                        f.write(f"   预测类型: {pred_type}\n")
                        f.write(f"   实际类型: {true_type}\n")
                        f.write(f"   置信度: {result['confidence']:.1f}%\n")
                        f.write(f"   结果: {result_text}\n")
                        f.write(f"   文件路径: {result['path']}\n\n")

                QMessageBox.information(self, "成功", f"结果已保存到:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败:\n{str(e)}")


def main():
    app = QApplication(sys.argv)

    # 设置应用程序样式
    app.setStyle("Fusion")

    # 设置调色板
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(240, 245, 255))
    palette.setColor(QPalette.WindowText, QColor(44, 62, 80))
    palette.setColor(QPalette.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.AlternateBase, QColor(248, 249, 250))
    palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
    palette.setColor(QPalette.ToolTipText, QColor(44, 62, 80))
    palette.setColor(QPalette.Text, QColor(44, 62, 80))
    palette.setColor(QPalette.Button, QColor(74, 111, 165))
    palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
    palette.setColor(QPalette.Highlight, QColor(74, 111, 165))
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)

    # 创建主窗口
    window = MainWindow()

    # 如果模型加载成功，显示窗口
    if window.model_loaded:
        window.show()
        sys.exit(app.exec_())
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()