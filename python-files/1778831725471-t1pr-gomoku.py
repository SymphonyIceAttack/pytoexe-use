import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QMessageBox)
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor
from PyQt5.QtCore import Qt, QPoint

class GomokuBoard(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(520, 520)
        self.board = [[0 for _ in range(15)] for _ in range(15)]
        self.current_player = 1
        self.game_over = False
        self.winner = None
        self.winning_line = []

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        painter.setPen(QPen(Qt.black, 1, Qt.SolidLine))
        for i in range(1, 16):
            painter.drawLine(20, 20 + (i-1)*35, 500, 20 + (i-1)*35)
            painter.drawLine(20 + (i-1)*35, 20, 20 + (i-1)*35, 500)
        
        painter.setPen(QPen(Qt.black, 2, Qt.SolidLine))
        for i in [3, 7, 11]:
            for j in [3, 7, 11]:
                painter.drawEllipse(20 + i*35 - 4, 20 + j*35 - 4, 8, 8)
        
        for i in range(15):
            for j in range(15):
                if self.board[i][j] != 0:
                    x = 20 + j * 35
                    y = 20 + i * 35
                    if self.board[i][j] == 1:
                        painter.setBrush(QBrush(Qt.black))
                    else:
                        painter.setBrush(QBrush(Qt.white))
                    painter.setPen(QPen(Qt.black, 2))
                    painter.drawEllipse(x - 15, y - 15, 30, 30)
        
        if self.winning_line:
            painter.setPen(QPen(Qt.red, 3, Qt.SolidLine))
            for i in range(len(self.winning_line) - 1):
                x1 = 20 + self.winning_line[i][1] * 35
                y1 = 20 + self.winning_line[i][0] * 35
                x2 = 20 + self.winning_line[i+1][1] * 35
                y2 = 20 + self.winning_line[i+1][0] * 35
                painter.drawLine(x1, y1, x2, y2)

    def mousePressEvent(self, event):
        if self.game_over:
            return
        
        x = event.x()
        y = event.y()
        
        col = round((x - 20) / 35)
        row = round((y - 20) / 35)
        
        if 0 <= col < 15 and 0 <= row < 15:
            if self.board[row][col] == 0:
                self.board[row][col] = self.current_player
                self.update()
                
                if self.check_win(row, col):
                    self.game_over = True
                    self.winner = self.current_player
                    self.show_winner()
                else:
                    self.current_player = 2 if self.current_player == 1 else 1

    def check_win(self, row, col):
        directions = [
            (0, 1),   
            (1, 0),   
            (1, 1),   
            (1, -1)   
        ]
        
        for dx, dy in directions:
            line = [(row, col)]
            r, c = row + dx, col + dy
            while 0 <= r < 15 and 0 <= c < 15 and self.board[r][c] == self.current_player:
                line.append((r, c))
                r += dx
                c += dy
            
            r, c = row - dx, col - dy
            while 0 <= r < 15 and 0 <= c < 15 and self.board[r][c] == self.current_player:
                line.insert(0, (r, c))
                r -= dx
                c -= dy
            
            if len(line) >= 5:
                self.winning_line = line[:5]
                return True
        
        return False

    def show_winner(self):
        winner_text = "黑棋获胜！" if self.winner == 1 else "白棋获胜！"
        QMessageBox.information(self, "游戏结束", winner_text)

    def reset(self):
        self.board = [[0 for _ in range(15)] for _ in range(15)]
        self.current_player = 1
        self.game_over = False
        self.winner = None
        self.winning_line = []
        self.update()

class GomokuWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("五子棋")
        self.setFixedSize(600, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        title_label = QLabel("五子棋")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title_label)
        
        self.board = GomokuBoard()
        layout.addWidget(self.board)
        
        button_layout = QHBoxLayout()
        
        self.reset_button = QPushButton("重新开始")
        self.reset_button.clicked.connect(self.board.reset)
        button_layout.addWidget(self.reset_button)
        
        self.exit_button = QPushButton("退出")
        self.exit_button.clicked.connect(self.close)
        button_layout.addWidget(self.exit_button)
        
        layout.addLayout(button_layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GomokuWindow()
    window.show()
    sys.exit(app.exec_())