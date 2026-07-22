#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows 桌面宠物程序
功能：透明窗口、可拖拽、点击互动、对话气泡、右键菜单、滚轮缩放
"""

import sys
import random
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QMenu, QAction, 
                             QVBoxLayout, QGraphicsOpacityEffect)
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QBrush, QPen
from PyQt5.QtCore import Qt, QTimer, QPoint, QPropertyAnimation, QRect, pyqtProperty


class BubbleWidget(QWidget):
    """对话气泡组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.text = ""
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.hide()
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide)
    
    def show_text(self, text, duration=2000):
        """显示气泡文字"""
        self.text = text
        # 计算文字宽度
        font = QFont("Microsoft YaHei", 10)
        metrics = self.fontMetrics()
        text_width = metrics.horizontalAdvance(text)
        text_height = metrics.height()
        self.setFixedSize(text_width + 30, text_height + 25)
        self.show()
        self.timer.start(duration)
    
    def paintEvent(self, event):
        """绘制气泡"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 气泡背景
        bubble_rect = QRect(0, 0, self.width(), self.height() - 10)
        painter.setBrush(QBrush(QColor(255, 255, 255, 240)))
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.drawRoundedRect(bubble_rect, 10, 10)
        
        # 气泡小尾巴
        tail_points = [
            QPoint(self.width() // 2 - 8, self.height() - 10),
            QPoint(self.width() // 2 + 8, self.height() - 10),
            QPoint(self.width() // 2, self.height())
        ]
        painter.setBrush(QBrush(QColor(255, 255, 255, 240)))
        painter.setPen(Qt.NoPen)
        painter.drawPolygon(*tail_points)
        
        # 文字
        painter.setPen(QColor(50, 50, 50))
        font = QFont("Microsoft YaHei", 10)
        painter.setFont(font)
        text_rect = QRect(15, 8, self.width() - 30, self.height() - 25)
        painter.drawText(text_rect, Qt.AlignCenter, self.text)


class DesktopPet(QWidget):
    """桌面宠物主窗口"""
    
    # 互动对话列表
    dialogues = [
        "喵~ 你好呀！",
        "摸摸头~",
        "好开心呀！",
        "陪我玩嘛~",
        "嘿嘿嘿",
        "你在干嘛呢？",
        "我超可爱的！",
        "喵呜~",
        "再来一次！",
        "舒服~",
        "举高高！",
        "哇哦~",
        "蹭蹭你~",
        "今天也要加油哦！",
        "我最乖啦~"
    ]
    
    def __init__(self):
        super().__init__()
        self.scale = 0.3  # 默认缩放比例
        self.is_topmost = True  # 是否置顶
        self.is_animating = False  # 是否正在播放动画
        self.current_anim = 0  # 当前动画索引
        self.drag_position = None  # 拖拽位置
        
        self.init_ui()
        self.init_animation()
    
    def init_ui(self):
        """初始化UI"""
        # 窗口设置：无边框、透明、置顶、工具窗口（不显示在任务栏）
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 加载图片
        self.original_pixmap = QPixmap("character_transparent.png")
        self.pixmap_label = QLabel(self)
        self.update_pixmap()
        
        # 对话气泡
        self.bubble = BubbleWidget()
        
        # 窗口大小
        self.resize(self.pixmap_label.sizeHint())
        
        # 初始位置（屏幕右下角）
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - self.width() - 50, screen.height() - self.height() - 100)
    
    def update_pixmap(self):
        """更新图片缩放"""
        scaled_pixmap = self.original_pixmap.scaled(
            int(self.original_pixmap.width() * self.scale),
            int(self.original_pixmap.height() * self.scale),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.pixmap_label.setPixmap(scaled_pixmap)
        self.pixmap_label.resize(scaled_pixmap.size())
        self.resize(scaled_pixmap.size())
    
    def init_animation(self):
        """初始化动画"""
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.animation_step)
        self.anim_frame = 0
        self.anim_type = None
        self.base_y = 0
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
        elif event.button() == Qt.RightButton:
            self.show_context_menu(event.globalPos())
            event.accept()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件（拖拽）"""
        if event.buttons() == Qt.LeftButton and self.drag_position:
            self.move(event.globalPos() - self.drag_position)
            self.update_bubble_position()
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton and self.drag_position:
            # 判断是点击还是拖拽
            if not self.is_animating:
                self.trigger_interaction()
            self.drag_position = None
            event.accept()
    
    def wheelEvent(self, event):
        """鼠标滚轮缩放"""
        delta = event.angleDelta().y()
        if delta > 0:
            self.scale = min(self.scale + 0.05, 1.0)
        else:
            self.scale = max(self.scale - 0.05, 0.1)
        self.update_pixmap()
        self.update_bubble_position()
        event.accept()
    
    def show_context_menu(self, pos):
        """显示右键菜单"""
        menu = QMenu(self)
        
        # 调整大小子菜单
        size_menu = menu.addMenu("调整大小")
        
        size_small = QAction("小", self)
        size_small.triggered.connect(lambda: self.set_scale(0.2))
        size_menu.addAction(size_small)
        
        size_medium = QAction("中", self)
        size_medium.triggered.connect(lambda: self.set_scale(0.35))
        size_menu.addAction(size_medium)
        
        size_large = QAction("大", self)
        size_large.triggered.connect(lambda: self.set_scale(0.5))
        size_menu.addAction(size_large)
        
        size_menu.addSeparator()
        
        size_custom = QAction("滚轮调整", self)
        size_custom.triggered.connect(lambda: None)
        size_menu.addAction(size_custom)
        
        # 置顶开关
        top_action = QAction("取消置顶" if self.is_topmost else "置顶显示", self)
        top_action.triggered.connect(self.toggle_topmost)
        menu.addAction(top_action)
        
        menu.addSeparator()
        
        # 退出
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(QApplication.quit)
        menu.addAction(quit_action)
        
        menu.exec_(pos)
    
    def set_scale(self, scale):
        """设置缩放比例"""
        self.scale = scale
        self.update_pixmap()
        self.update_bubble_position()
    
    def toggle_topmost(self):
        """切换置顶状态"""
        self.is_topmost = not self.is_topmost
        if self.is_topmost:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        self.show()
    
    def trigger_interaction(self):
        """触发互动"""
        if self.is_animating:
            return
        
        self.is_animating = True
        self.anim_frame = 0
        self.base_y = self.y()
        
        # 轮流切换动画类型
        anim_types = ["jump", "squash", "shake"]
        self.anim_type = anim_types[self.current_anim % len(anim_types)]
        self.current_anim += 1
        
        # 显示对话气泡
        self.show_random_dialogue()
        
        # 启动动画
        self.anim_timer.start(20)
    
    def show_random_dialogue(self):
        """显示随机对话"""
        text = random.choice(self.dialogues)
        self.update_bubble_position()
        self.bubble.show_text(text, 2000)
    
    def update_bubble_position(self):
        """更新气泡位置（在角色上方，不遮挡角色）"""
        bubble_x = self.x() + self.width() // 2 - self.bubble.width() // 2
        bubble_y = self.y() - self.bubble.height()
        self.bubble.move(bubble_x, bubble_y)
    
    def animation_step(self):
        """动画帧更新"""
        self.anim_frame += 1
        
        if self.anim_type == "jump":
            # 跳跃动画：先上后下
            total_frames = 30
            if self.anim_frame <= total_frames // 2:
                # 上升
                offset = -8 * (self.anim_frame ** 1.5)
            else:
                # 下降
                t = self.anim_frame - total_frames // 2
                offset = -8 * ((total_frames // 2) ** 1.5) + 8 * (t ** 1.5)
            
            self.move(self.x(), int(self.base_y + offset))
            
            if self.anim_frame >= total_frames:
                self.end_animation()
        
        elif self.anim_type == "squash":
            # 压扁回弹动画
            total_frames = 25
            if self.anim_frame <= 8:
                # 压扁
                scale_y = 1.0 - 0.2 * (self.anim_frame / 8)
                scale_x = 1.0 + 0.1 * (self.anim_frame / 8)
            elif self.anim_frame <= 18:
                # 回弹拉伸
                t = (self.anim_frame - 8) / 10
                scale_y = 0.8 + 0.3 * t
                scale_x = 1.1 - 0.1 * t
            else:
                # 恢复
                t = (self.anim_frame - 18) / 7
                scale_y = 1.1 - 0.1 * t
                scale_x = 1.0 + 0.0 * t
            
            self.apply_scale_transform(scale_x, scale_y)
            
            if self.anim_frame >= total_frames:
                self.update_pixmap()
                self.end_animation()
        
        elif self.anim_type == "shake":
            # 左右抖动
            total_frames = 24
            shake_amount = 8
            offset_x = shake_amount * (1 if self.anim_frame % 4 < 2 else -1)
            self.move(self.x() + offset_x - (offset_x if self.anim_frame > 1 else 0), self.y())
            
            if self.anim_frame >= total_frames:
                self.move(self.x(), self.base_y)
                self.end_animation()
    
    def apply_scale_transform(self, scale_x, scale_y):
        """应用缩放变换"""
        base_width = int(self.original_pixmap.width() * self.scale)
        base_height = int(self.original_pixmap.height() * self.scale)
        
        new_width = int(base_width * scale_x)
        new_height = int(base_height * scale_y)
        
        scaled_pixmap = self.original_pixmap.scaled(
            new_width, new_height,
            Qt.IgnoreAspectRatio,
            Qt.SmoothTransformation
        )
        self.pixmap_label.setPixmap(scaled_pixmap)
        self.pixmap_label.resize(new_width, new_height)
        
        # 保持底部对齐
        new_y = self.y() + base_height - new_height
        new_x = self.x() + (base_width - new_width) // 2
        self.setGeometry(new_x, new_y, new_width, new_height)
    
    def end_animation(self):
        """结束动画"""
        self.anim_timer.stop()
        self.is_animating = False
        self.move(self.x(), self.base_y)
        self.update_pixmap()
    
    def paintEvent(self, event):
        """绘制透明背景"""
        pass  # 图片由QLabel绘制，窗口背景透明
    
    def closeEvent(self, event):
        """关闭事件"""
        self.bubble.close()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    
    pet = DesktopPet()
    pet.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
