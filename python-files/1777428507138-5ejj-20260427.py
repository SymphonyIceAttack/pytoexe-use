import sys
import cv2
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QPushButton,
                             QLabel, QVBoxLayout, QHBoxLayout, QFileDialog,
                             QMessageBox, QProgressBar, QSplitter, QFrame,
                             QScrollArea, QDialog, QVBoxLayout as QVBoxLayoutDialog)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QImage, QFont
import torch
import os
import time
from datetime import datetime
from PIL import Image

# 设置环境变量
os.environ['TORCH_HOME'] = os.path.expanduser('~/.cache/torch')

# 导入人脸识别库
try:
    from facenet_pytorch import MTCNN, InceptionResnetV1
except ImportError:
    print("正在安装 facenet-pytorch...")
    os.system('pip install facenet-pytorch -i https://pypi.tuna.tsinghua.edu.cn/simple')
    from facenet_pytorch import MTCNN, InceptionResnetV1


class RecognitionWorker(QThread):
    """后台识别线程"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(list, list, float, list, list)
    error = pyqtSignal(str)

    def __init__(self, target_feature, group_img, device, mtcnn, resnet):
        super().__init__()
        self.target_feature = target_feature
        self.group_img = group_img
        self.device = device
        self.mtcnn = mtcnn
        self.resnet = resnet

    def extract_face_feature(self, face_img):
        """提取人脸特征向量"""
        try:
            # 调整到160x160
            face_resized = cv2.resize(face_img, (160, 160))
            # 归一化并转换为tensor
            face_tensor = torch.from_numpy(face_resized).permute(2, 0, 1).float() / 255.0
            face_tensor = face_tensor.unsqueeze(0).to(self.device)

            # 提取特征
            with torch.no_grad():
                feature = self.resnet(face_tensor).cpu().numpy()[0]

            # L2归一化
            feature = feature / (np.linalg.norm(feature) + 1e-8)
            return feature
        except Exception as e:
            return None

    def run(self):
        try:
            self.progress.emit("正在检测人脸...")

            # 检测集体照中的所有脸
            boxes, probs, landmarks = self.mtcnn.detect(self.group_img, landmarks=True)

            if boxes is None or len(boxes) == 0:
                self.finished.emit([], [], 0.0, [], [])
                return

            self.progress.emit(f"检测到 {len(boxes)} 张人脸，正在提取特征...")

            # 提取集体照中所有人脸的特征和图像
            group_features = []
            valid_boxes = []
            face_images = []  # 保存人脸图像用于放大显示

            for i, box in enumerate(boxes):
                x1, y1, x2, y2 = box.astype(int)
                h, w = self.group_img.shape[:2]

                # 确保边界框在图像范围内
                x1 = max(0, min(x1, w - 1))
                y1 = max(0, min(y1, h - 1))
                x2 = max(x1 + 1, min(x2, w))
                y2 = max(y1 + 1, min(y2, h))

                # 提取人脸区域
                face_roi = self.group_img[y1:y2, x1:x2].copy()

                if face_roi.size == 0:
                    continue

                # 保存人脸图像
                face_images.append(face_roi)

                # 确保是RGB格式
                if len(face_roi.shape) == 2:
                    face_roi = cv2.cvtColor(face_roi, cv2.COLOR_GRAY2RGB)
                elif face_roi.shape[2] == 4:
                    face_roi = cv2.cvtColor(face_roi, cv2.COLOR_BGRA2RGB)

                # 提取特征
                feature = self.extract_face_feature(face_roi)
                if feature is not None:
                    group_features.append(feature)
                    valid_boxes.append([x1, y1, x2, y2])

            if len(group_features) == 0:
                self.finished.emit([], [], 0.0, [], [])
                return

            self.progress.emit("正在计算相似度...")

            # 计算余弦相似度
            similarities = []
            for feat in group_features:
                cos_sim = np.dot(self.target_feature, feat)
                cos_sim = np.clip(cos_sim, -1.0, 1.0)
                normalized_sim = 0.5 + 0.5 * cos_sim
                similarities.append(normalized_sim)

            best_similarity = max(similarities) if similarities else 0.0

            self.finished.emit(valid_boxes, similarities, best_similarity, face_images, [])

        except Exception as e:
            self.error.emit(str(e))
        finally:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()


class FaceZoomDialog(QDialog):
    """人脸放大查看对话框"""

    def __init__(self, face_image, similarity, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔍 人脸放大查看")
        self.setMinimumSize(400, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #2c3e50;
            }
            QLabel {
                color: #ecf0f1;
                font-size: 14px;
            }
        """)

        layout = QVBoxLayoutDialog(self)

        # 标题
        title_label = QLabel("目标人物放大视图")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #3498db; padding: 10px;")
        layout.addWidget(title_label)

        # 放大的人脸图片
        self.face_label = QLabel()
        self.face_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.face_label.setMinimumSize(350, 350)
        self.face_label.setStyleSheet("""
            border: 2px solid #3498db;
            background-color: #34495e;
            border-radius: 10px;
            padding: 10px;
        """)

        # 放大显示人脸
        if face_image is not None:
            # 放大到300x300
            h, w = face_image.shape[:2]
            scale = min(300 / w, 300 / h)
            new_w = int(w * scale)
            new_h = int(h * scale)
            face_big = cv2.resize(face_image, (new_w, new_h))

            # 转换为QPixmap
            h, w, ch = face_big.shape
            bytes_per_line = ch * w
            qt_img = QImage(face_big.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_img)
            self.face_label.setPixmap(pixmap)

        layout.addWidget(self.face_label)

        # 相似度信息
        info_label = QLabel(f"识别相似度: {similarity:.1%}")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #27ae60; padding: 10px;")
        layout.addWidget(info_label)

        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)


class FaceRecognitionSystem(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("人脸识别系统 - 精准识别目标人物")
        self.setMinimumSize(1400, 850)

        # 设置窗口样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2c3e50;
            }
            QLabel {
                color: #ecf0f1;
            }
        """)

        # 初始化设备
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"使用设备: {self.device}")

        # 初始化变量
        self.models_loaded = False
        self.target_feature = None
        self.target_face_img = None
        self.group_img = None
        self.worker = None
        self.mtcnn = None
        self.resnet = None
        self.current_result_img = None
        self.current_zoomed_face = None
        self.current_similarity = 0

        self.init_ui()

        # 延迟加载模型
        QTimer.singleShot(500, self.load_models)

    def load_models(self):
        """加载模型"""
        try:
            self.status_label.setText("正在加载模型，请稍候...")
            self.status_label.setStyleSheet("color: #f39c12; padding: 8px; font-size: 12px;")
            QApplication.processEvents()

            # 初始化MTCNN
            self.mtcnn = MTCNN(
                keep_all=True,
                device=self.device,
                min_face_size=60,
                thresholds=[0.7, 0.8, 0.8],
                post_process=True
            )

            # 加载FaceNet模型
            self.resnet = InceptionResnetV1(pretrained='vggface2').eval().to(self.device)

            self.models_loaded = True
            self.status_label.setText("✅ 模型加载成功，可以开始使用")
            self.status_label.setStyleSheet("color: #27ae60; padding: 8px; font-size: 12px;")

            # 启用按钮
            self.btn_upload_single.setEnabled(True)

            print("模型加载完成")

        except Exception as e:
            error_msg = str(e)
            print(f"模型加载失败: {error_msg}")
            self.status_label.setText(f"❌ 模型加载失败: {error_msg[:50]}...")
            self.status_label.setStyleSheet("color: #e74c3c; padding: 8px; font-size: 12px;")
            QMessageBox.critical(self, "错误", f"模型加载失败：{error_msg}\n\n请重新启动程序。")

    def init_ui(self):
        """初始化UI界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 标题
        title_label = QLabel("🎯 人脸识别系统")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #ecf0f1; padding: 10px;")
        main_layout.addWidget(title_label)

        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧面板 - 单人照
        left_widget = QWidget()
        left_widget.setStyleSheet("background-color: #34495e; border-radius: 10px;")
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(10)
        left_layout.setContentsMargins(15, 15, 15, 15)

        # 标题
        left_title = QLabel("📸 步骤一：上传目标人物照片")
        left_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #3498db;")
        left_layout.addWidget(left_title)

        # 图片显示区域
        self.single_photo_label = QLabel()
        self.single_photo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.single_photo_label.setMinimumSize(350, 400)
        self.single_photo_label.setStyleSheet("""
            border: 2px dashed #7f8c8d;
            background-color: #2c3e50;
            border-radius: 8px;
        """)
        self.single_photo_label.setText("📷 暂无照片\n点击下方按钮上传")
        left_layout.addWidget(self.single_photo_label)

        # 按钮
        self.btn_upload_single = QPushButton("📁 上传照片")
        self.btn_upload_single.clicked.connect(self.upload_single_photo)
        self.btn_upload_single.setEnabled(False)
        self.btn_upload_single.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
            }
        """)
        left_layout.addWidget(self.btn_upload_single)

        left_layout.addStretch()

        # 右侧面板 - 集体照
        right_widget = QWidget()
        right_widget.setStyleSheet("background-color: #34495e; border-radius: 10px;")
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(10)
        right_layout.setContentsMargins(15, 15, 15, 15)

        # 标题
        right_title = QLabel("👥 步骤二：上传集体照并识别")
        right_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #3498db;")
        right_layout.addWidget(right_title)

        # 图片显示区域
        self.group_photo_label = QLabel()
        self.group_photo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.group_photo_label.setMinimumSize(600, 450)
        self.group_photo_label.setStyleSheet("""
            border: 2px dashed #7f8c8d;
            background-color: #2c3e50;
            border-radius: 8px;
        """)
        self.group_photo_label.setText("📷 暂无照片\n点击下方按钮上传")
        right_layout.addWidget(self.group_photo_label)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #7f8c8d;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 5px;
            }
        """)
        right_layout.addWidget(self.progress_bar)

        # 按钮行
        btn_layout = QHBoxLayout()

        self.btn_upload_group = QPushButton("📁 上传集体照")
        self.btn_upload_group.clicked.connect(self.upload_group_photo)
        self.btn_upload_group.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)

        self.btn_recognize = QPushButton("🔍 开始识别")
        self.btn_recognize.setEnabled(False)
        self.btn_recognize.clicked.connect(self.recognize_target)
        self.btn_recognize.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
            }
        """)

        btn_layout.addWidget(self.btn_upload_group)
        btn_layout.addWidget(self.btn_recognize)
        right_layout.addLayout(btn_layout)

        # 保存结果按钮
        self.btn_save = QPushButton("💾 保存识别结果")
        self.btn_save.clicked.connect(self.save_result)
        self.btn_save.setEnabled(False)
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 5px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
            }
        """)
        right_layout.addWidget(self.btn_save)

        # 放大人脸预览区域
        zoom_frame = QFrame()
        zoom_frame.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                border-radius: 8px;
                margin-top: 10px;
            }
        """)
        zoom_layout = QVBoxLayout(zoom_frame)

        zoom_title = QLabel("🔍 目标人脸放大预览 (双击可查看大图)")
        zoom_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        zoom_title.setStyleSheet("font-size: 12px; color: #3498db; padding: 5px;")
        zoom_layout.addWidget(zoom_title)

        self.zoom_preview_label = QLabel()
        self.zoom_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.zoom_preview_label.setMinimumHeight(150)
        self.zoom_preview_label.setStyleSheet("""
            border: 1px solid #3498db;
            background-color: #34495e;
            border-radius: 8px;
        """)
        self.zoom_preview_label.setText("识别后自动显示\n放大的人脸")
        self.zoom_preview_label.mouseDoubleClickEvent = self.on_zoom_double_click
        zoom_layout.addWidget(self.zoom_preview_label)

        right_layout.addWidget(zoom_frame)

        right_layout.addStretch()

        # 添加左右面板到分割器
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([450, 750])

        main_layout.addWidget(splitter)

        # 状态栏
        self.status_label = QLabel("⚪ 系统就绪，等待加载模型...")
        self.status_label.setStyleSheet("color: #ecf0f1; padding: 8px; font-size: 12px; background-color: #2c3e50;")
        main_layout.addWidget(self.status_label)

    def load_image_safe(self, file_path):
        """安全地加载图片"""
        try:
            img = Image.open(file_path)
            img = img.convert('RGB')
            img_np = np.array(img)
            return img_np
        except Exception as e1:
            try:
                img = cv2.imread(file_path)
                if img is not None:
                    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    return img_rgb
            except Exception as e2:
                print(f"加载图片失败: {e1}, {e2}")
                return None

    def upload_single_photo(self):
        """上传单人照"""
        if not self.models_loaded:
            QMessageBox.warning(self, "错误", "模型未加载完成，请稍候再试")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择目标人物照片", "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.PNG *.JPG *.JPEG)"
        )

        if not file_path:
            return

        try:
            if not os.path.exists(file_path):
                QMessageBox.warning(self, "错误", f"文件不存在：{file_path}")
                return

            img_rgb = self.load_image_safe(file_path)

            if img_rgb is None:
                QMessageBox.warning(self, "错误", "无法读取图片文件，请检查文件格式")
                return

            self.display_image(self.single_photo_label, img_rgb)

            self.status_label.setText("正在提取人脸特征...")
            self.status_label.setStyleSheet("color: #f39c12; padding: 8px; font-size: 12px;")
            QApplication.processEvents()

            boxes, probs = self.mtcnn.detect(img_rgb)

            if boxes is None or len(boxes) == 0:
                QMessageBox.warning(self, "错误", "未检测到人脸！\n请确保照片中包含清晰的人脸")
                self.status_label.setText("❌ 未检测到人脸")
                self.target_feature = None
                self.btn_recognize.setEnabled(False)
                return

            if probs is not None:
                best_idx = np.argmax(probs)
            else:
                areas = [(box[2] - box[0]) * (box[3] - box[1]) for box in boxes]
                best_idx = np.argmax(areas)

            best_box = boxes[best_idx]
            x1, y1, x2, y2 = best_box.astype(int)

            h, w = img_rgb.shape[:2]
            x1 = max(0, min(x1, w - 1))
            y1 = max(0, min(y1, h - 1))
            x2 = max(x1 + 1, min(x2, w))
            y2 = max(y1 + 1, min(y2, h))

            self.target_face_img = img_rgb[y1:y2, x1:x2].copy()

            face_resized = cv2.resize(self.target_face_img, (160, 160))
            face_tensor = torch.from_numpy(face_resized).permute(2, 0, 1).float() / 255.0
            face_tensor = face_tensor.unsqueeze(0).to(self.device)

            with torch.no_grad():
                feature = self.resnet(face_tensor).cpu().numpy()[0]

            self.target_feature = feature / (np.linalg.norm(feature) + 1e-8)

            img_with_box = img_rgb.copy()
            cv2.rectangle(img_with_box, (x1, y1), (x2, y2), (0, 255, 0), 3)
            cv2.putText(img_with_box, "Target Face", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            self.display_image(self.single_photo_label, img_with_box)

            self.status_label.setText("✅ 人脸特征提取成功，可以上传集体照")
            self.status_label.setStyleSheet("color: #27ae60; padding: 8px; font-size: 12px;")

            if self.group_img is not None:
                self.btn_recognize.setEnabled(True)

        except Exception as e:
            error_msg = str(e)
            print(f"处理失败: {error_msg}")
            QMessageBox.critical(self, "错误", f"处理失败：{error_msg}")

    def upload_group_photo(self):
        """上传集体照"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择集体照片", "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.PNG *.JPG *.JPEG)"
        )

        if not file_path:
            return

        try:
            if not os.path.exists(file_path):
                QMessageBox.warning(self, "错误", f"文件不存在：{file_path}")
                return

            img_rgb = self.load_image_safe(file_path)

            if img_rgb is None:
                QMessageBox.warning(self, "错误", "无法读取图片文件，请检查文件格式")
                return

            self.group_img = img_rgb
            self.display_image(self.group_photo_label, self.group_img)

            self.btn_recognize.setEnabled(self.target_feature is not None and self.models_loaded)
            self.btn_save.setEnabled(False)
            self.status_label.setText("✅ 集体照已上传，点击「开始识别」")
            self.status_label.setStyleSheet("color: #27ae60; padding: 8px; font-size: 12px;")

            # 清空之前的放大预览
            self.zoom_preview_label.setText("识别后自动显示\n放大的人脸")
            self.zoom_preview_label.setPixmap(QPixmap())
            self.current_zoomed_face = None

        except Exception as e:
            error_msg = str(e)
            print(f"处理失败: {error_msg}")
            QMessageBox.critical(self, "错误", f"处理失败：{error_msg}")

    def recognize_target(self):
        """开始识别目标人物"""
        if self.target_feature is None:
            QMessageBox.warning(self, "提示", "请先上传目标人物照片")
            return

        if self.group_img is None:
            QMessageBox.warning(self, "提示", "请先上传集体照")
            return

        if self.mtcnn is None or self.resnet is None:
            QMessageBox.warning(self, "错误", "模型未加载，无法进行识别")
            return

        self.btn_recognize.setEnabled(False)
        self.btn_upload_single.setEnabled(False)
        self.btn_upload_group.setEnabled(False)
        self.btn_save.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        self.worker = RecognitionWorker(self.target_feature, self.group_img, self.device, self.mtcnn, self.resnet)
        self.worker.progress.connect(self.on_recognition_progress)
        self.worker.finished.connect(self.on_recognition_finished)
        self.worker.error.connect(self.on_recognition_error)
        self.worker.start()

    def on_recognition_progress(self, message):
        self.status_label.setText(f"🔄 {message}")
        self.status_label.setStyleSheet("color: #f39c12; padding: 8px; font-size: 12px;")
        QApplication.processEvents()

    def on_recognition_finished(self, boxes, similarities, best_similarity, face_images, _):
        self.progress_bar.setVisible(False)
        self.btn_recognize.setEnabled(True)
        self.btn_upload_single.setEnabled(True)
        self.btn_upload_group.setEnabled(True)

        if len(boxes) == 0:
            self.status_label.setText("❌ 集体照中未检测到人脸")
            self.status_label.setStyleSheet("color: #e74c3c; padding: 8px; font-size: 12px;")
            QMessageBox.information(self, "提示", "集体照中未检测到任何人脸")
            return

        # 复制原图用于标注
        result_img = self.group_img.copy()

        # 找到最相似的人脸
        best_idx = np.argmax(similarities)
        best_similarity = similarities[best_idx]
        best_box = boxes[best_idx]

        # 保存放大的人脸
        if best_idx < len(face_images):
            self.current_zoomed_face = face_images[best_idx]
            self.current_similarity = best_similarity

            # 在预览区域显示放大的人脸
            if self.current_zoomed_face is not None:
                # 放大预览图（150x150）
                h, w = self.current_zoomed_face.shape[:2]
                scale = min(150 / w, 150 / h)
                new_w = int(w * scale)
                new_h = int(h * scale)
                preview_face = cv2.resize(self.current_zoomed_face, (new_w, new_h))

                h, w, ch = preview_face.shape
                bytes_per_line = ch * w
                qt_img = QImage(preview_face.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                pixmap = QPixmap.fromImage(qt_img)
                self.zoom_preview_label.setPixmap(pixmap)
                self.zoom_preview_label.setText("")

        # 阈值
        THRESHOLD = 0.65

        # 用深色框标记最相似的人（深蓝色边框）
        x1, y1, x2, y2 = best_box

        # 绘制多层深色边框（深蓝色渐变效果）
        colors = [(0, 0, 139), (0, 0, 159), (0, 0, 179), (0, 0, 199)]
        for i, color in enumerate(colors):
            offset = i * 2
            cv2.rectangle(result_img, (x1 - offset, y1 - offset),
                          (x2 + offset, y2 + offset), color, 3)

        # 主边框
        cv2.rectangle(result_img, (x1, y1), (x2, y2), (0, 0, 255), 4)

        # 添加标签背景和文字
        if best_similarity >= THRESHOLD:
            label = f"✓ TARGET PERSON - {best_similarity:.1%}"
            bg_color = (0, 0, 139)  # 深蓝色背景
            text_color = (255, 255, 255)  # 白色文字
        else:
            label = f"BEST MATCH - {best_similarity:.1%}"
            bg_color = (139, 0, 0)  # 深红色背景
            text_color = (255, 255, 255)  # 白色文字

        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        thickness = 2
        (text_w, text_h), baseline = cv2.getTextSize(label, font, font_scale, thickness)

        # 背景矩形
        cv2.rectangle(result_img, (x1, y1 - text_h - 10), (x1 + text_w + 10, y1), bg_color, -1)
        cv2.putText(result_img, label, (x1 + 5, y1 - 8), font, font_scale, text_color, thickness)

        # 显示结果
        self.display_image(self.group_photo_label, result_img)
        self.current_result_img = result_img
        self.btn_save.setEnabled(True)

        # 更新状态栏
        if best_similarity >= THRESHOLD:
            self.status_label.setText(f"✅ 识别成功！找到目标人物，相似度: {best_similarity:.1%} (深蓝色框标注)")
            self.status_label.setStyleSheet("color: #27ae60; padding: 8px; font-size: 12px; font-weight: bold;")
        else:
            self.status_label.setText(f"⚠️ 未找到高度匹配的人物，最高相似度: {best_similarity:.1%} (深红色框标注)")
            self.status_label.setStyleSheet("color: #f39c12; padding: 8px; font-size: 12px;")

    def on_recognition_error(self, error_msg):
        self.progress_bar.setVisible(False)
        self.btn_recognize.setEnabled(True)
        self.btn_upload_single.setEnabled(True)
        self.btn_upload_group.setEnabled(True)
        self.status_label.setText(f"❌ 识别出错: {error_msg[:50]}")
        self.status_label.setStyleSheet("color: #e74c3c; padding: 8px; font-size: 12px;")
        QMessageBox.critical(self, "错误", f"识别出错：{error_msg}")

    def on_zoom_double_click(self, event):
        """双击放大预览区域打开放大窗口"""
        if self.current_zoomed_face is not None:
            dialog = FaceZoomDialog(self.current_zoomed_face, self.current_similarity, self)
            dialog.exec()

    def save_result(self):
        """保存识别结果"""
        if self.current_result_img is None:
            QMessageBox.warning(self, "提示", "没有可保存的识别结果")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"recognition_result_{timestamp}.jpg"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存识别结果", default_name, "Image Files (*.jpg *.png)"
        )

        if file_path:
            save_img = cv2.cvtColor(self.current_result_img, cv2.COLOR_RGB2BGR)
            cv2.imwrite(file_path, save_img)
            self.status_label.setText(f"✅ 结果已保存: {os.path.basename(file_path)}")
            self.status_label.setStyleSheet("color: #27ae60; padding: 8px; font-size: 12px;")
            QMessageBox.information(self, "成功", f"识别结果已保存到：\n{file_path}")

    def display_image(self, label, img_rgb):
        """在QLabel上显示图片"""
        try:
            h, w = img_rgb.shape[:2]

            label_width = label.width() if label.width() > 100 else 600
            label_height = label.height() if label.height() > 100 else 450

            scale_w = label_width / w
            scale_h = label_height / h
            scale = min(scale_w, scale_h, 1.0)

            new_w = int(w * scale)
            new_h = int(h * scale)

            img_resized = cv2.resize(img_rgb, (new_w, new_h))

            h, w, ch = img_resized.shape
            bytes_per_line = ch * w
            qt_img = QImage(img_resized.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)

            label.setPixmap(QPixmap.fromImage(qt_img))

        except Exception as e:
            print(f"显示图片错误: {e}")

    def closeEvent(self, event):
        """关闭事件"""
        if self.worker is not None and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait(3000)
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = FaceRecognitionSystem()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()