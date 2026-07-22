import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QMessageBox, QMenu, QAction
)
from PyQt5.QtGui import QPixmap, QImage, QClipboard, QDragEnterEvent, QDropEvent
from PyQt5.QtCore import Qt, QMimeData, QUrl

TOP_CROP = 120
BOTTOM_CROP = 130


class CropTool(QWidget):
    def __init__(self):
        super().__init__()
        self.original_pixmap = None       # 原图
        self.cropped_pixmap = None        # 裁切后的图片
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('固定尺寸截图切割工具')
        self.setFixedSize(500, 650)
        self.setAcceptDrops(True)  # 启用拖放

        layout = QVBoxLayout()
        layout.setSpacing(15)

        # 标题
        title = QLabel('📸 截图切割工具')
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet('font-size: 18px; font-weight: bold;')
        layout.addWidget(title)

        # 裁切参数提示
        info_label = QLabel(f'⚙️ 当前固定裁切：顶部 {TOP_CROP}px，底部 {BOTTOM_CROP}px')
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet('background: #f0f0f0; border-radius: 6px; padding: 8px;')
        layout.addWidget(info_label)

        # 上传区域（点击上传 + 提示）
        upload_layout = QVBoxLayout()
        self.upload_btn = QPushButton('📁 点击上传图片')
        self.upload_btn.setStyleSheet('''
            QPushButton {
                background: #eaf4ff;
                border: 2px dashed #007aff;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
                color: #007aff;
            }
            QPushButton:hover {
                background: #dcefff;
            }
        ''')
        self.upload_btn.clicked.connect(self.select_file)
        upload_layout.addWidget(self.upload_btn)

        paste_hint = QLabel('💡 也支持直接粘贴（Ctrl+V）或拖放图片到窗口')
        paste_hint.setAlignment(Qt.AlignCenter)
        paste_hint.setStyleSheet('color: #666; font-size: 12px;')
        upload_layout.addWidget(paste_hint)
        layout.addLayout(upload_layout)

        # 预览区域
        self.preview_label = QLabel('裁剪后预览会出现在这里')
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setFixedHeight(300)
        self.preview_label.setStyleSheet('''
            border: 2px solid #4CAF50;
            border-radius: 4px;
            background: #f9f9f9;
        ''')
        self.preview_label.setContextMenuPolicy(Qt.CustomContextMenu)
        self.preview_label.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.preview_label)

        # 保存按钮
        self.save_btn = QPushButton('📥 下载裁剪后的图片')
        self.save_btn.setEnabled(False)
        self.save_btn.setStyleSheet('''
            QPushButton {
                background: #007aff;
                color: white;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:disabled {
                background: #ccc;
            }
            QPushButton:hover:!disabled {
                background: #005bb5;
            }
        ''')
        self.save_btn.clicked.connect(self.save_image)
        layout.addWidget(self.save_btn)

        # 底部提示
        footer = QLabel('右键点击预览图可复制到剪贴板')
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet('color: #888; font-size: 11px;')
        layout.addWidget(footer)

        self.setLayout(layout)

    # 选择文件
    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, '选择图片', '', '图片文件 (*.png *.jpg *.jpeg *.bmp)'
        )
        if file_path:
            self.load_image(file_path)

    # 加载图片并裁剪
    def load_image(self, path):
        pixmap = QPixmap(path)
        if pixmap.isNull():
            QMessageBox.warning(self, '错误', '无法加载图片，请检查格式。')
            return
        self.process_pixmap(pixmap)

    # 裁剪逻辑
    def process_pixmap(self, pixmap):
        self.original_pixmap = pixmap
        w = pixmap.width()
        h = pixmap.height()
        new_h = h - TOP_CROP - BOTTOM_CROP
        if new_h <= 0:
            QMessageBox.warning(self, '裁剪失败', f'图片高度仅 {h}px，无法裁切 {TOP_CROP + BOTTOM_CROP}px。')
            self.cropped_pixmap = None
            self.preview_label.clear()
            self.preview_label.setText('图片高度不足，无法裁剪')
            self.save_btn.setEnabled(False)
            return

        # 裁剪：从 (0, TOP_CROP) 开始，取 w × new_h
        self.cropped_pixmap = pixmap.copy(0, TOP_CROP, w, new_h)

        # 显示预览（保持比例缩放至预览区域）
        preview_pixmap = self.cropped_pixmap.scaled(
            self.preview_label.width(), self.preview_label.height(),
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.preview_label.setPixmap(preview_pixmap)
        self.save_btn.setEnabled(True)

    # 右键菜单
    def show_context_menu(self, pos):
        if self.cropped_pixmap is None:
            return
        menu = QMenu()
        copy_action = QAction('📋 复制图片到剪贴板', self)
        copy_action.triggered.connect(self.copy_to_clipboard)
        menu.addAction(copy_action)
        menu.exec_(self.preview_label.mapToGlobal(pos))

    # 复制图片到剪贴板
    def copy_to_clipboard(self):
        if self.cropped_pixmap is None:
            return
        clipboard = QApplication.clipboard()
        clipboard.setPixmap(self.cropped_pixmap)
        self.show_status('图片已复制到剪贴板 ✅')

    # 保存图片
    def save_image(self):
        if self.cropped_pixmap is None:
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, '保存图片', 'cropped_image.png', 'PNG 图片 (*.png);;JPEG 图片 (*.jpg)'
        )
        if file_path:
            if self.cropped_pixmap.save(file_path):
                self.show_status('图片已保存 ✅')
            else:
                QMessageBox.warning(self, '保存失败', '无法保存图片，请检查路径权限。')

    # 状态提示（简易）
    def show_status(self, msg):
        QMessageBox.information(self, '提示', msg)

    # 拖放事件
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                self.load_image(file_path)
            else:
                QMessageBox.warning(self, '格式错误', '请拖入图片文件（png, jpg, bmp）。')

    # 键盘粘贴事件（Ctrl+V）
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_V and event.modifiers() == Qt.ControlModifier:
            clipboard = QApplication.clipboard()
            mime = clipboard.mimeData()
            if mime.hasImage():
                pixmap = clipboard.pixmap()
                if not pixmap.isNull():
                    self.process_pixmap(pixmap)
                    self.show_status('已粘贴并裁剪图片 ✅')
                    return
            elif mime.hasUrls():
                # 如果剪贴板是文件路径（例如从文件管理器复制）
                urls = mime.urls()
                if urls:
                    file_path = urls[0].toLocalFile()
                    if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                        self.load_image(file_path)
                        return
            QMessageBox.information(self, '提示', '剪贴板中没有可用的图片。')
        else:
            super().keyPressEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CropTool()
    window.show()
    sys.exit(app.exec_())