import pygame
import random
import sys

# 初始化Pygame
pygame.init()

# 游戏配置
WIDTH = 10
HEIGHT = 20
BLOCK_SIZE = 30
GAME_WIDTH = WIDTH * BLOCK_SIZE
GAME_HEIGHT = HEIGHT * BLOCK_SIZE
NEXT_SIZE = 4 * BLOCK_SIZE
INFO_WIDTH = 200
SCREEN_WIDTH = GAME_WIDTH + INFO_WIDTH
SCREEN_HEIGHT = GAME_HEIGHT
FPS = 60

# 颜色定义 (RGB)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
CYAN = (0, 255, 255)
BLUE = (0, 0, 255)
ORANGE = (255, 165, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
PURPLE = (128, 0, 128)
RED = (255, 0, 0)

# 方块形状对应的颜色
SHAPE_COLORS = [
    CYAN,   # I
    YELLOW,  # O
    PURPLE,  # T
    ORANGE,  # L
    BLUE,   # J
    GREEN,  # S
    RED     # Z
]

# 方块形状 (4x4矩阵)
SHAPES = [
    [  # I
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [1, 1, 1, 1],
        [0, 0, 0, 0]
    ],
    [  # O
        [0, 0, 0, 0],
        [0, 1, 1, 0],
        [0, 1, 1, 0],
        [0, 0, 0, 0]
    ],
    [  # T
        [0, 0, 0, 0],
        [0, 1, 0, 0],
        [1, 1, 1, 0],
        [0, 0, 0, 0]
    ],
    [  # L
        [0, 0, 0, 0],
        [1, 0, 0, 0],
        [1, 1, 1, 0],
        [0, 0, 0, 0]
    ],
    [  # J
        [0, 0, 0, 0],
        [0, 0, 1, 0],
        [1, 1, 1, 0],
        [0, 0, 0, 0]
    ],
    [  # S
        [0, 0, 0, 0],
        [0, 1, 1, 0],
        [1, 1, 0, 0],
        [0, 0, 0, 0]
    ],
    [  # Z
        [0, 0, 0, 0],
        [1, 1, 0, 0],
        [0, 1, 1, 0],
        [0, 0, 0, 0]
    ]
]


class Tetris:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("俄罗斯方块")
        self.clock = pygame.time.Clock()
        # 尝试使用中文字体，如果失败则使用默认字体
        try:
            self.font = pygame.font.Font("C:/Windows/Fonts/simhei.ttf", 24)
            self.big_font = pygame.font.Font("C:/Windows/Fonts/simhei.ttf", 36)
        except:
            self.font = pygame.font.Font(None, 24)
            self.big_font = pygame.font.Font(None, 36)

        self.reset_game()

    def reset_game(self):
        """重置游戏状态"""
        # 游戏板 (HEIGHT x WIDTH)
        self.board = [[0 for _ in range(WIDTH)] for _ in range(HEIGHT)]
        self.score = 0
        self.game_over = False
        self.speed = 400  # 毫秒
        self.last_fall_time = pygame.time.get_ticks()
        self.fast_drop = False

        # 生成第一个方块
        self.next_shape_index = random.randint(0, 6)
        self.next_shape = [row[:] for row in SHAPES[self.next_shape_index]]
        self.spawn_new_shape()

    def spawn_new_shape(self):
        """生成新的当前方块"""
        self.current_shape_index = self.next_shape_index
        self.current_shape = [row[:]
                              for row in SHAPES[self.current_shape_index]]
        self.current_color = SHAPE_COLORS[self.current_shape_index]
        self.current_x = WIDTH // 2 - 2
        self.current_y = 0

        # 生成下一个方块
        self.next_shape_index = random.randint(0, 6)
        self.next_shape = [row[:] for row in SHAPES[self.next_shape_index]]

        # 检查是否碰撞（游戏结束）
        if self.check_collision(self.current_shape, self.current_x, self.current_y):
            self.game_over = True

    def check_collision(self, shape, offset_x, offset_y):
        """检查碰撞"""
        for i in range(4):
            for j in range(4):
                if shape[i][j] != 0:
                    x = offset_x + j
                    y = offset_y + i
                    if x < 0 or x >= WIDTH or y >= HEIGHT:
                        return True
                    if y >= 0 and self.board[y][x] != 0:
                        return True
        return False

    def merge_shape(self):
        """将当前方块合并到游戏板"""
        for i in range(4):
            for j in range(4):
                if self.current_shape[i][j] != 0:
                    x = self.current_x + j
                    y = self.current_y + i
                    if 0 <= y < HEIGHT and 0 <= x < WIDTH:
                        # 存储形状索引+1
                        self.board[y][x] = self.current_shape_index + 1

        self.clear_lines()
        self.spawn_new_shape()

    def clear_lines(self):
        """消除满行并更新分数"""
        lines_cleared = 0
        for i in range(HEIGHT - 1, -1, -1):
            if all(self.board[i][j] != 0 for j in range(WIDTH)):
                # 消除这一行
                del self.board[i]
                self.board.insert(0, [0 for _ in range(WIDTH)])
                lines_cleared += 1

        # 根据消除行数加分
        if lines_cleared > 0:
            points = {1: 100, 2: 300, 3: 500, 4: 800}
            self.score += points.get(lines_cleared, 0)

            # 每500分增加速度
            if self.score // 500 > (self.score - points.get(lines_cleared, 0)) // 500:
                if self.speed > 100:
                    self.speed -= 30

    def move_left(self):
        """向左移动"""
        if not self.check_collision(self.current_shape, self.current_x - 1, self.current_y):
            self.current_x -= 1

    def move_right(self):
        """向右移动"""
        if not self.check_collision(self.current_shape, self.current_x + 1, self.current_y):
            self.current_x += 1

    def rotate_shape(self):
        """旋转方块"""
        # 顺时针旋转
        rotated = [[self.current_shape[3 - j][i]
                    for j in range(4)] for i in range(4)]
        if not self.check_collision(rotated, self.current_x, self.current_y):
            self.current_shape = rotated

    def drop_down(self):
        """直接落下到底部"""
        while not self.check_collision(self.current_shape, self.current_x, self.current_y + 1):
            self.current_y += 1
        self.merge_shape()
        self.fast_drop = False

    def update(self):
        """更新游戏状态"""
        if self.game_over:
            return

        now = pygame.time.get_ticks()
        delay = 20 if self.fast_drop else self.speed

        if now - self.last_fall_time >= delay:
            if not self.check_collision(self.current_shape, self.current_x, self.current_y + 1):
                self.current_y += 1
            else:
                self.merge_shape()
                self.fast_drop = False
            self.last_fall_time = now

    def draw(self):
        """绘制游戏界面"""
        self.screen.fill(BLACK)

        # 绘制游戏区域边框
        pygame.draw.rect(self.screen, WHITE,
                         (0, 0, GAME_WIDTH, GAME_HEIGHT), 2)

        # 绘制已固定的方块
        for y in range(HEIGHT):
            for x in range(WIDTH):
                if self.board[y][x] != 0:
                    color = SHAPE_COLORS[self.board[y][x] - 1]
                    pygame.draw.rect(self.screen, color,
                                     (x * BLOCK_SIZE + 1, y * BLOCK_SIZE + 1,
                                      BLOCK_SIZE - 2, BLOCK_SIZE - 2))

        # 绘制当前活动的方块
        for i in range(4):
            for j in range(4):
                if self.current_shape[i][j] != 0:
                    x = (self.current_x + j) * BLOCK_SIZE
                    y = (self.current_y + i) * BLOCK_SIZE
                    pygame.draw.rect(self.screen, self.current_color,
                                     (x + 1, y + 1, BLOCK_SIZE - 2, BLOCK_SIZE - 2))

        # 绘制右侧信息面板
        info_x = GAME_WIDTH + 10

        # 得分
        score_text = self.font.render(f"得分: {self.score}", True, WHITE)
        self.screen.blit(score_text, (info_x, 50))

        # 速度等级
        speed_level = (400 - self.speed) // 30 + 1
        speed_text = self.font.render(f"速度: {speed_level}", True, WHITE)
        self.screen.blit(speed_text, (info_x, 90))

        # 下一个方块标题
        next_title = self.font.render("下一个方块:", True, WHITE)
        self.screen.blit(next_title, (info_x, 140))

        # 绘制下一个方块
        next_offset_x = info_x + 20
        next_offset_y = 180
        for i in range(4):
            for j in range(4):
                if self.next_shape[i][j] != 0:
                    color = SHAPE_COLORS[self.next_shape_index]
                    pygame.draw.rect(self.screen, color,
                                     (next_offset_x + j * BLOCK_SIZE,
                                      next_offset_y + i * BLOCK_SIZE,
                                      BLOCK_SIZE - 2, BLOCK_SIZE - 2))

        # 操作说明
        controls = [
            "操作说明:",
            "← → : 移动",
            "↑ : 旋转",
            "↓ : 加速下落",
            "空格 : 直接落下",
            "R : 重新开始",
            "ESC : 退出"
        ]
        for i, text in enumerate(controls):
            control_text = self.font.render(text, True, GRAY)
            self.screen.blit(control_text, (info_x, 320 + i * 25))

        # 游戏结束画面
        if self.game_over:
            # 半透明遮罩
            overlay = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
            overlay.set_alpha(128)
            overlay.fill(BLACK)
            self.screen.blit(overlay, (0, 0))

            # 游戏结束文字
            game_over_text = self.big_font.render("游戏结束", True, RED)
            text_rect = game_over_text.get_rect(
                center=(GAME_WIDTH // 2, GAME_HEIGHT // 2 - 30))
            self.screen.blit(game_over_text, text_rect)

            # 最终得分
            final_score_text = self.font.render(
                f"最终得分: {self.score}", True, WHITE)
            text_rect = final_score_text.get_rect(
                center=(GAME_WIDTH // 2, GAME_HEIGHT // 2 + 10))
            self.screen.blit(final_score_text, text_rect)

            # 重新开始提示
            restart_text = self.font.render("按 R 键重新开始", True, WHITE)
            text_rect = restart_text.get_rect(
                center=(GAME_WIDTH // 2, GAME_HEIGHT // 2 + 50))
            self.screen.blit(restart_text, text_rect)

        pygame.display.flip()

    def handle_events(self):
        """处理键盘事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False

                if event.key == pygame.K_r:
                    self.reset_game()
                    return True

                if self.game_over:
                    return True

                if event.key == pygame.K_LEFT:
                    self.move_left()
                elif event.key == pygame.K_RIGHT:
                    self.move_right()
                elif event.key == pygame.K_UP:
                    self.rotate_shape()
                elif event.key == pygame.K_DOWN:
                    self.fast_drop = True
                elif event.key == pygame.K_SPACE:
                    self.drop_down()

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_DOWN:
                    self.fast_drop = False

        return True

    def run(self):
        """主游戏循环"""
        running = True
        while running:
            running = self.handle_events()
            if not running:
                break

            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


def main():
    print("俄罗斯方块游戏启动！")
    print("使用方向键控制方块")
    print("按 R 重新开始，ESC 退出")

    game = Tetris()
    game.run()


if __name__ == "__main__":
    main()
