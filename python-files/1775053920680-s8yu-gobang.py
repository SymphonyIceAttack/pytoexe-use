import pygame
import sys
import numpy as np

# ===================== 常量设置 =====================
# 棋盘尺寸（标准15路五子棋）
BOARD_SIZE = 15
CELL_SIZE = 40       # 每个格子大小
WINDOW_WIDTH = BOARD_SIZE * CELL_SIZE
WINDOW_HEIGHT = BOARD_SIZE * CELL_SIZE

# 颜色定义
BG_COLOR = (218, 175, 111)    # 棋盘背景色
LINE_COLOR = (0, 0, 0)        # 棋盘线色
BLACK_CHESS = (0, 0, 0)       # 黑棋
WHITE_CHESS = (255, 255, 255) # 白棋
HINT_COLOR = (255, 0, 0)      # 提示点

# 棋子类型
EMPTY = 0
BLACK = 1
WHITE = 2

# ===================== 核心：AI评分表（五子棋核心逻辑） =====================
# 评分越高，优先级越高，AI优先选择高分位置
SCORE_TABLE = {
    (0, 1, 0, 0, 0): 1,    # 眠一
    (0, 1, 1, 0, 0): 10,   # 眠二
    (0, 1, 1, 1, 0): 100,  # 活三
    (0, 1, 1, 1, 1): 1000, # 冲四
    (1, 1, 1, 1, 1): 10000,# 五连（胜利）
    (0, 2, 0, 0, 0): 1,
    (0, 2, 2, 0, 0): 10,
    (0, 2, 2, 2, 0): 100,
    (0, 2, 2, 2, 2): 1000,
    (2, 2, 2, 2, 2): 10000,
}

# ===================== 游戏核心类 =====================
class GobangAI:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("五子棋AI对战")
        self.clock = pygame.time.Clock()
        # 初始化棋盘：0=空，1=黑，2=白
        self.board = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=int)
        self.current_player = BLACK  # 黑棋先手（人类）
        self.game_over = False
        # 模式切换：True=AI对战，False=人类VS AI
        self.ai_vs_ai = False

    # 绘制棋盘
    def draw_board(self):
        self.screen.fill(BG_COLOR)
        # 画横线竖线
        for i in range(BOARD_SIZE):
            pygame.draw.line(self.screen, LINE_COLOR, 
                            (CELL_SIZE//2, CELL_SIZE//2 + i*CELL_SIZE),
                            (WINDOW_WIDTH - CELL_SIZE//2, CELL_SIZE//2 + i*CELL_SIZE), 1)
            pygame.draw.line(self.screen, LINE_COLOR, 
                            (CELL_SIZE//2 + i*CELL_SIZE, CELL_SIZE//2),
                            (CELL_SIZE//2 + i*CELL_SIZE, WINDOW_HEIGHT - CELL_SIZE//2), 1)
        pygame.display.update()

    # 绘制棋子
    def draw_chess(self, row, col, color):
        center_x = col * CELL_SIZE + CELL_SIZE//2
        center_y = row * CELL_SIZE + CELL_SIZE//2
        pygame.draw.circle(self.screen, color, (center_x, center_y), CELL_SIZE//2 - 2)
        pygame.display.update()

    # 判断落子是否合法
    def is_valid_move(self, row, col):
        return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE and self.board[row][col] == EMPTY

    # 判断胜负（横、竖、左斜、右斜）
    def check_win(self, row, col, player):
        # 横
        count = 0
        for c in range(BOARD_SIZE):
            if self.board[row][c] == player:
                count +=1
                if count ==5: return True
            else: count =0
        # 纵向
        count =0
        for r in range(BOARD_SIZE):
            if self.board[r][col] == player:
                count +=1
                if count ==5: return True
            else: count =0
        # 左上-右下
        count =0
        start_row = row - min(row, col)
        start_col = col - min(row, col)
        while start_row < BOARD_SIZE and start_col < BOARD_SIZE:
            if self.board[start_row][start_col] == player:
                count +=1
                if count ==5: return True
            else: count =0
            start_row +=1
            start_col +=1
        # 右上-左下
        count =0
        start_row = row + min(BOARD_SIZE-1-row, col)
        start_col = col - min(BOARD_SIZE-1-row, col)
        while start_row >=0 and start_col < BOARD_SIZE:
            if self.board[start_row][start_col] == player:
                count +=1
                if count ==5: return True
            else: count =0
            start_row -=1
            start_col +=1
        return False

    # AI评分函数（核心）
    def evaluate_point(self, row, col, player):
        temp_board = self.board.copy()
        temp_board[row][col] = player
        max_score = 0
        # 遍历四个方向
        directions = [(0,1),(1,0),(1,1),(1,-1)]
        for dr, dc in directions:
            line = []
            for i in range(-4,5):
                r = row + dr*i
                c = col + dc*i
                if 0<=r<BOARD_SIZE and 0<=c<BOARD_SIZE:
                    line.append(temp_board[r][c])
                else:
                    line.append(-1)
            # 匹配评分表
            for i in range(len(line)-4):
                key = tuple(line[i:i+5])
                if key in SCORE_TABLE:
                    max_score = max(max_score, SCORE_TABLE[key])
        return max_score

    # AI寻找最佳落子点
    def ai_best_move(self, ai_color):
        best_score = -1
        best_pos = (7,7) # 默认中心
        # 遍历所有空位打分
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if self.board[row][col] == EMPTY:
                    # 攻击分 + 防守分（攻防一体）
                    score = self.evaluate_point(row, col, ai_color) + self.evaluate_point(row, col, 3-ai_color)
                    if score > best_score:
                        best_score = score
                        best_pos = (row, col)
        return best_pos

    # 落子
    def move(self, row, col, player):
        if self.is_valid_move(row, col) and not self.game_over:
            self.board[row][col] = player
            color = BLACK_CHESS if player == BLACK else WHITE_CHESS
            self.draw_chess(row, col, color)
            # 判定胜利
            if self.check_win(row, col, player):
                self.game_over = True
                print(f"{'黑棋' if player==BLACK else '白棋'}获胜！")
            # 切换玩家
            self.current_player = WHITE if self.current_player == BLACK else BLACK

    # 游戏主循环
    def run(self):
        self.draw_board()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                # 人类落子（黑棋）
                if not self.ai_vs_ai and self.current_player == BLACK and not self.game_over:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        x, y = pygame.mouse.get_pos()
                        col = x // CELL_SIZE
                        row = y // CELL_SIZE
                        self.move(row, col, BLACK)

            # AI落子（白棋 / AIVSAI模式）
            if not self.game_over:
                if self.ai_vs_ai:
                    # AI互相对战
                    pygame.time.delay(500)
                    ai_color = self.current_player
                    row, col = self.ai_best_move(ai_color)
                    self.move(row, col, ai_color)
                else:
                    # 人类VS AI：AI执白
                    if self.current_player == WHITE:
                        pygame.time.delay(500)
                        row, col = self.ai_best_move(WHITE)
                        self.move(row, col, WHITE)

            self.clock.tick(30)

# ===================== 启动游戏 =====================
if __name__ == "__main__":
    game = GobangAI()
    game.run()