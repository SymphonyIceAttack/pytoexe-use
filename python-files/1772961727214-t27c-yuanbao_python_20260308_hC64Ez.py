import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QTextEdit, 
                               QFileDialog, QMessageBox, QFontDialog, QColorDialog)
from PySide6.QtGui import QAction, QKeySequence, QTextCharFormat, QFont, QIcon
from PySide6.QtCore import Qt, QSettings


class Notepad(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 初始化设置
        self.settings = QSettings("MyCompany", "SimpleNotepad")
        
        # 当前文件路径
        self.current_file = None
        
        # 初始化UI
        self.init_ui()
        
        # 恢复窗口设置
        self.read_settings()
        
    def init_ui(self):
        """初始化用户界面"""
        # 设置窗口属性
        self.setWindowTitle("记事本")
        self.setGeometry(300, 200, 800, 600)
        
        # 创建中央文本编辑部件
        self.text_edit = QTextEdit()
        self.setCentralWidget(self.text_edit)
        
        # 创建菜单栏
        self.create_menus()
        
        # 创建状态栏
        self.statusBar().showMessage("就绪")
        
        # 连接文本变化信号
        self.text_edit.textChanged.connect(self.text_changed)
        
    def create_menus(self):
        """创建菜单"""
        # 文件菜单
        file_menu = self.menuBar().addMenu("文件(&F)")
        
        # 新建
        new_action = QAction("新建(&N)", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.setStatusTip("创建新文档")
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)
        
        # 打开
        open_action = QAction("打开(&O)...", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.setStatusTip("打开现有文档")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        # 保存
        save_action = QAction("保存(&S)", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.setStatusTip("保存当前文档")
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        # 另存为
        save_as_action = QAction("另存为(&A)...", self)
        save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_as_action.setStatusTip("将文档另存为新文件")
        save_as_action.triggered.connect(self.save_as_file)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        # 退出
        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.setStatusTip("退出应用")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = self.menuBar().addMenu("编辑(&E)")
        
        # 撤销
        undo_action = QAction("撤销(&U)", self)
        undo_action.setShortcut(QKeySequence.Undo)
        undo_action.setStatusTip("撤销上次操作")
        undo_action.triggered.connect(self.text_edit.undo)
        edit_menu.addAction(undo_action)
        
        # 重做
        redo_action = QAction("重做(&R)", self)
        redo_action.setShortcut(QKeySequence.Redo)
        redo_action.setStatusTip("重做上次撤销的操作")
        redo_action.triggered.connect(self.text_edit.redo)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        # 剪切
        cut_action = QAction("剪切(&T)", self)
        cut_action.setShortcut(QKeySequence.Cut)
        cut_action.setStatusTip("剪切选中文本")
        cut_action.triggered.connect(self.text_edit.cut)
        edit_menu.addAction(cut_action)
        
        # 复制
        copy_action = QAction("复制(&C)", self)
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.setStatusTip("复制选中文本")
        copy_action.triggered.connect(self.text_edit.copy)
        edit_menu.addAction(copy_action)
        
        # 粘贴
        paste_action = QAction("粘贴(&P)", self)
        paste_action.setShortcut(QKeySequence.Paste)
        paste_action.setStatusTip("粘贴剪贴板内容")
        paste_action.triggered.connect(self.text_edit.paste)
        edit_menu.addAction(paste_action)
        
        # 全选
        select_all_action = QAction("全选(&A)", self)
        select_all_action.setShortcut(QKeySequence.SelectAll)
        select_all_action.setStatusTip("选择所有文本")
        select_all_action.triggered.connect(self.text_edit.selectAll)
        edit_menu.addAction(select_all_action)
        
        edit_menu.addSeparator()
        
        # 查找
        find_action = QAction("查找(&F)...", self)
        find_action.setShortcut(QKeySequence.Find)
        find_action.setStatusTip("在文档中查找文本")
        find_action.triggered.connect(self.find_text)
        edit_menu.addAction(find_action)
        
        # 替换
        replace_action = QAction("替换(&R)...", self)
        replace_action.setShortcut(QKeySequence("Ctrl+H"))
        replace_action.setStatusTip("查找并替换文本")
        replace_action.triggered.connect(self.replace_text)
        edit_menu.addAction(replace_action)
        
        # 格式菜单
        format_menu = self.menuBar().addMenu("格式(&O)")
        
        # 字体
        font_action = QAction("字体(&F)...", self)
        font_action.setStatusTip("设置字体")
        font_action.triggered.connect(self.set_font)
        format_menu.addAction(font_action)
        
        # 颜色
        color_action = QAction("颜色(&C)...", self)
        color_action.setStatusTip("设置文本颜色")
        color_action.triggered.connect(self.set_color)
        format_menu.addAction(color_action)
        
        format_menu.addSeparator()
        
        # 自动换行
        wrap_action = QAction("自动换行(&W)", self, checkable=True)
        wrap_action.setChecked(True)
        wrap_action.setStatusTip("切换文本自动换行")
        wrap_action.triggered.connect(self.toggle_wrap)
        format_menu.addAction(wrap_action)
        
        # 视图菜单
        view_menu = self.menuBar().addMenu("视图(&V)")
        
        # 缩放
        zoom_in_action = QAction("放大(&I)", self)
        zoom_in_action.setShortcut(QKeySequence.ZoomIn)
        zoom_in_action.setStatusTip("放大文本")
        zoom_in_action.triggered.connect(self.zoom_in)
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction("缩小(&O)", self)
        zoom_out_action.setShortcut(QKeySequence.ZoomOut)
        zoom_out_action.setStatusTip("缩小文本")
        zoom_out_action.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out_action)
        
        reset_zoom_action = QAction("重置缩放(&R)", self)
        reset_zoom_action.setShortcut(QKeySequence("Ctrl+0"))
        reset_zoom_action.setStatusTip("重置缩放级别")
        reset_zoom_action.triggered.connect(self.reset_zoom)
        view_menu.addAction(reset_zoom_action)
        
        # 帮助菜单
        help_menu = self.menuBar().addMenu("帮助(&H)")
        
        # 关于
        about_action = QAction("关于(&A)...", self)
        about_action.setStatusTip("关于此应用")
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def new_file(self):
        """创建新文件"""
        if self.maybe_save():
            self.text_edit.clear()
            self.current_file = None
            self.setWindowTitle("记事本 - 新文件")
            self.statusBar().showMessage("新文件已创建")
    
    def open_file(self):
        """打开文件"""
        if self.maybe_save():
            file_name, _ = QFileDialog.getOpenFileName(
                self, "打开文件", "", "文本文件 (*.txt);;所有文件 (*)"
            )
            
            if file_name:
                try:
                    with open(file_name, 'r', encoding='utf-8') as file:
                        self.text_edit.setText(file.read())
                    
                    self.current_file = file_name
                    self.setWindowTitle(f"记事本 - {os.path.basename(file_name)}")
                    self.statusBar().showMessage(f"已打开: {file_name}")
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"无法打开文件:\n{str(e)}")
    
    def save_file(self):
        """保存文件"""
        if self.current_file:
            self.save_to_file(self.current_file)
        else:
            self.save_as_file()
    
    def save_as_file(self):
        """另存文件"""
        file_name, _ = QFileDialog.getSaveFileName(
            self, "另存为", "", "文本文件 (*.txt);;所有文件 (*)"
        )
        
        if file_name:
            self.save_to_file(file_name)
    
    def save_to_file(self, file_name):
        """保存内容到指定文件"""
        try:
            with open(file_name, 'w', encoding='utf-8') as file:
                file.write(self.text_edit.toPlainText())
            
            self.current_file = file_name
            self.setWindowTitle(f"记事本 - {os.path.basename(file_name)}")
            self.statusBar().showMessage(f"已保存: {file_name}")
            return True
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法保存文件:\n{str(e)}")
            return False
    
    def maybe_save(self):
        """检查是否需要保存"""
        if self.text_edit.document().isModified():
            reply = QMessageBox.question(
                self, "确认", "文档已更改，是否保存更改？",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Yes:
                return self.save_file()
            elif reply == QMessageBox.No:
                return True
            else:
                return False
        
        return True
    
    def set_font(self):
        """设置字体"""
        font, ok = QFontDialog.getFont(self.text_edit.font(), self)
        if ok:
            self.text_edit.setFont(font)
    
    def set_color(self):
        """设置文本颜色"""
        color = QColorDialog.getColor()
        if color.isValid():
            # 为选中的文本设置颜色
            cursor = self.text_edit.textCursor()
            if cursor.hasSelection():
                format = QTextCharFormat()
                format.setForeground(color)
                cursor.mergeCharFormat(format)
            else:
                # 如果没有选中文本，设置后续文本的颜色
                self.text_edit.setTextColor(color)
    
    def toggle_wrap(self):
        """切换自动换行"""
        if self.text_edit.lineWrapMode() == QTextEdit.WidgetWidth:
            self.text_edit.setLineWrapMode(QTextEdit.NoWrap)
        else:
            self.text_edit.setLineWrapMode(QTextEdit.WidgetWidth)
    
    def zoom_in(self):
        """放大文本"""
        self.text_edit.zoomIn(1)
    
    def zoom_out(self):
        """缩小文本"""
        self.text_edit.zoomOut(1)
    
    def reset_zoom(self):
        """重置缩放"""
        self.text_edit.zoomOut(100)  # 重置到默认大小
    
    def find_text(self):
        """查找文本"""
        from PySide6.QtWidgets import QInputDialog
        
        text, ok = QInputDialog.getText(self, "查找", "查找内容:")
        if ok and text:
            # 简单查找实现
            cursor = self.text_edit.textCursor()
            content = self.text_edit.toPlainText()
            search_from = cursor.position()
            
            # 从当前位置开始查找
            found_pos = content.find(text, search_from)
            
            if found_pos == -1 and search_from > 0:
                # 如果没找到，从开头再找
                found_pos = content.find(text, 0)
            
            if found_pos != -1:
                cursor.setPosition(found_pos)
                cursor.setPosition(found_pos + len(text), QTextCursor.KeepAnchor)
                self.text_edit.setTextCursor(cursor)
                self.text_edit.setFocus()
                self.statusBar().showMessage(f"找到 '{text}'")
            else:
                self.statusBar().showMessage(f"未找到 '{text}'")
    
    def replace_text(self):
        """替换文本"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
        
        dialog = QDialog(self)
        dialog.setWindowTitle("查找和替换")
        dialog.resize(300, 150)
        
        layout = QVBoxLayout(dialog)
        
        # 查找字段
        find_layout = QHBoxLayout()
        find_label = QLabel("查找:")
        self.find_field = QLineEdit()
        find_layout.addWidget(find_label)
        find_layout.addWidget(self.find_field)
        layout.addLayout(find_layout)
        
        # 替换字段
        replace_layout = QHBoxLayout()
        replace_label = QLabel("替换为:")
        self.replace_field = QLineEdit()
        replace_layout.addWidget(replace_label)
        replace_layout.addWidget(self.replace_field)
        layout.addLayout(replace_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        find_button = QPushButton("查找下一个")
        replace_button = QPushButton("替换")
        replace_all_button = QPushButton("全部替换")
        close_button = QPushButton("关闭")
        
        find_button.clicked.connect(self.find_next)
        replace_button.clicked.connect(self.replace_next)
        replace_all_button.clicked.connect(self.replace_all)
        close_button.clicked.connect(dialog.accept)
        
        button_layout.addWidget(find_button)
        button_layout.addWidget(replace_button)
        button_layout.addWidget(replace_all_button)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    def find_next(self):
        """查找下一个"""
        if hasattr(self, 'find_field') and self.find_field.text():
            self.find_text_in_document(self.find_field.text())
    
    def replace_next(self):
        """替换下一个"""
        if (hasattr(self, 'find_field') and hasattr(self, 'replace_field') and 
            self.find_field.text() and self.replace_field.text()):
            cursor = self.text_edit.textCursor()
            if cursor.hasSelection() and cursor.selectedText() == self.find_field.text():
                cursor.insertText(self.replace_field.text())
            
            self.find_next()
    
    def replace_all(self):
        """全部替换"""
        if (hasattr(self, 'find_field') and hasattr(self, 'replace_field') and 
            self.find_field.text() and self.replace_field.text()):
            content = self.text_edit.toPlainText()
            new_content = content.replace(self.find_field.text(), self.replace_field.text())
            self.text_edit.setPlainText(new_content)
    
    def find_text_in_document(self, text):
        """在文档中查找文本"""
        cursor = self.text_edit.textCursor()
        content = self.text_edit.toPlainText()
        search_from = cursor.position()
        
        found_pos = content.find(text, search_from)
        
        if found_pos == -1 and search_from > 0:
            found_pos = content.find(text, 0)
        
        if found_pos != -1:
            cursor.setPosition(found_pos)
            cursor.setPosition(found_pos + len(text), QTextCursor.KeepAnchor)
            self.text_edit.setTextCursor(cursor)
            self.text_edit.setFocus()
            self.statusBar().showMessage(f"找到 '{text}'")
        else:
            self.statusBar().showMessage(f"未找到 '{text}'")
    
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(self, "关于记事本", 
                         "简单记事本\n\n"
                         "使用 PySide6 构建的简单文本编辑器\n"
                         "© 2026 记事本应用")
    
    def text_changed(self):
        """文本变化时更新状态"""
        if self.text_edit.document().isModified():
            file_name = os.path.basename(self.current_file) if self.current_file else "新文件"
            self.setWindowTitle(f"记事本 - {file_name} *")
    
    def closeEvent(self, event):
        """关闭事件处理"""
        if self.maybe_save():
            self.write_settings()
            event.accept()
        else:
            event.ignore()
    
    def write_settings(self):
        """保存窗口设置"""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
    
    def read_settings(self):
        """读取窗口设置"""
        if self.settings.contains("geometry"):
            self.restoreGeometry(self.settings.value("geometry"))
        if self.settings.contains("windowState"):
            self.restoreState(self.settings.value("windowState"))


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("简单记事本")
    
    # 设置应用样式
    app.setStyle("Fusion")
    
    notepad = Notepad()
    notepad.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()