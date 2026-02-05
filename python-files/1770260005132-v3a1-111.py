import pygame
import random
import sys

# 初始化 PyGame
pygame.init()

# 游戏常量
WIDTH, HEIGHT = 600, 600
GRID_SIZE = 20
GRID_WIDTH = WIDTH // GRID_SIZE
GRID_HEIGHT = HEIGHT // GRID_SIZE
FPS = 10

# 颜色定义
BACKGROUND = (15, 56, 15)
GRID_COLOR = (30, 80, 30)
SNAKE_HEAD = (50, 205, 50)
SNAKE_BODY = (34, 139, 34)
FOOD_COLOR = (220, 20, 60)
TEXT_COLOR = (255, 255, 255)
WALL_COLOR = (139, 69, 19)

# 方向常量
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

class Snake:
    def __init__(self):
        self.reset()
        
    def reset(self):
        # 蛇初始位置在屏幕中央
        self.length = 3
        self.positions = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
        self.direction = RIGHT
        self.score = 0
        self.grow_to = 3
        self.is_alive = True
        
    def get_head_position(self):
        return self.positions[0]
    
    def turn(self, point):
        # 防止蛇直接反向移动
        if self.length > 1 and (point[0] * -1, point[1] * -1) == self.direction:
            return
        else:
            self.direction = point
    
    def move(self):
        if not self.is_alive:
            return
            
        head = self.get_head_position()
        x, y = self.direction
        new_x = (head[0] + x) % GRID_WIDTH
        new_y = (head[1] + y) % GRID_HEIGHT
        new_head = (new_x, new_y)
        
        # 检查是否撞到自己
        if new_head in self.positions[1:]:
            self.is_alive = False
            return
            
        self.positions.insert(0, new_head)
        
        # 如果蛇需要增长
        if len(self.positions) > self.grow_to:
            self.positions.pop()
    
    def draw(self, surface):
        for i, p in enumerate(self.positions):
            # 蛇头用不同颜色
            color = SNAKE_HEAD if i == 0 else SNAKE_BODY
            
            # 绘制蛇身矩形
            rect = pygame.Rect(
                p[0] * GRID_SIZE, 
                p[1] * GRID_SIZE, 
                GRID_SIZE, GRID_SIZE
            )
            pygame.draw.rect(surface, color, rect)
            pygame.draw.rect(surface, (color[0]//2, color[1]//2, color[2]//2), rect, 1)
            
            # 绘制蛇眼睛（只在头部）
            if i == 0:
                # 根据方向确定眼睛位置
                eye_size = GRID_SIZE // 5
                if self.direction == RIGHT:
                    left_eye = (rect.right - eye_size*2, rect.top + eye_size*2)
                    right_eye = (rect.right - eye_size*2, rect.bottom - eye_size*2)
                elif self.direction == LEFT:
                    left_eye = (rect.left + eye_size, rect.top + eye_size*2)
                    right_eye = (rect.left + eye_size, rect.bottom - eye_size*2)
                elif self.direction == UP:
                    left_eye = (rect.left + eye_size*2, rect.top + eye_size)
                    right_eye = (rect.right - eye_size*2, rect.top + eye_size)
                else:  # DOWN
                    left_eye = (rect.left + eye_size*2, rect.bottom - eye_size)
                    right_eye = (rect.right - eye_size*2, rect.bottom - eye_size)
                
                pygame.draw.circle(surface, (255, 255, 255), left_eye, eye_size)
                pygame.draw.circle(surface, (255, 255, 255), right_eye, eye_size)
                pygame.draw.circle(surface, (0, 0, 0), left_eye, eye_size//2)
                pygame.draw.circle(surface, (0, 0, 0), right_eye, eye_size//2)
    
    def grow(self):
        self.grow_to += 1
        self.score += 10

class Food:
    def __init__(self):
        self.position = (0, 0)
        self.randomize_position()
    
    def randomize_position(self):
        self.position = (
            random.randint(0, GRID_WIDTH - 1),
            random.randint(0, GRID_HEIGHT - 1)
        )
    
    def draw(self, surface):
        rect = pygame.Rect(
            self.position[0] * GRID_SIZE,
            self.position[1] * GRID_SIZE,
            GRID_SIZE, GRID_SIZE
        )
        pygame.draw.rect(surface, FOOD_COLOR, rect)
        pygame.draw.rect(surface, (FOOD_COLOR[0]//2, FOOD_COLOR[1]//2, FOOD_COLOR[2]//2), rect, 1)
        
        # 添加一些细节使食物看起来像苹果
        stem_rect = pygame.Rect(
            rect.centerx - GRID_SIZE//10,
            rect.top - GRID_SIZE//4,
            GRID_SIZE//5,
            GRID_SIZE//4
        )
        pygame.draw.rect(surface, (139, 69, 19), stem_rect)
        
        leaf_rect = pygame.Rect(
            rect.centerx + GRID_SIZE//10,
            rect.top,
            GRID_SIZE//3,
            GRID_SIZE//6
        )
        pygame.draw.ellipse(surface, (50, 205, 50), leaf_rect)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Python 贪吃蛇")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('simhei', 25)
        self.big_font = pygame.font.SysFont('simhei', 50)
        self.snake = Snake()
        self.food = Food()
        self.speed = FPS
        self.game_over = False
        
    def draw_grid(self):
        for x in range(0, WIDTH, GRID_SIZE):
            pygame.draw.line(self.screen, GRID_COLOR, (x, 0), (x, HEIGHT), 1)
        for y in range(0, HEIGHT, GRID_SIZE):
            pygame.draw.line(self.screen, GRID_COLOR, (0, y), (WIDTH, y), 1)
    
    def draw_score(self):
        score_text = self.font.render(f'得分: {self.snake.score}', True, TEXT_COLOR)
        length_text = self.font.render(f'长度: {self.snake.grow_to}', True, TEXT_COLOR)
        self.screen.blit(score_text, (5, 5))
        self.screen.blit(length_text, (5, 35))
        
        # 绘制操作说明
        controls = [
            "方向键: 控制移动",
            "空格键: 暂停/继续",
            "R: 重新开始",
            "ESC: 退出游戏"
        ]
        
        for i, text in enumerate(controls):
            control_text = self.font.render(text, True, TEXT_COLOR)
            self.screen.blit(control_text, (WIDTH - control_text.get_width() - 10, 5 + i * 30))
    
    def draw_game_over(self):
        game_over_surface = self.big_font.render('游戏结束!', True, (255, 50, 50))
        score_surface = self.font.render(f'最终得分: {self.snake.score}', True, TEXT_COLOR)
        restart_surface = self.font.render('按 R 键重新开始', True, TEXT_COLOR)
        
        self.screen.blit(game_over_surface, 
                         (WIDTH//2 - game_over_surface.get_width()//2, HEIGHT//2 - 60))
        self.screen.blit(score_surface, 
                         (WIDTH//2 - score_surface.get_width()//2, HEIGHT//2))
        self.screen.blit(restart_surface, 
                         (WIDTH//2 - restart_surface.get_width()//2, HEIGHT//2 + 40))
    
    def check_collision(self):
        if self.snake.get_head_position() == self.food.position:
            self.snake.grow()
            self.food.randomize_position()
            
            # 确保食物不出现在蛇身上
            while self.food.position in self.snake.positions:
                self.food.randomize_position()
            
            # 每得100分增加一点速度
            if self.snake.score % 100 == 0:
                self.speed += 1
    
    def run(self):
        paused = False
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    elif event.key == pygame.K_r:
                        # 重新开始游戏
                        self.snake.reset()
                        self.food.randomize_position()
                        self.game_over = False
                        self.speed = FPS
                    elif event.key == pygame.K_SPACE:
                        # 暂停/继续游戏
                        paused = not paused
                    elif not paused and not self.game_over:
                        if event.key == pygame.K_UP:
                            self.snake.turn(UP)
                        elif event.key == pygame.K_DOWN:
                            self.snake.turn(DOWN)
                        elif event.key == pygame.K_LEFT:
                            self.snake.turn(LEFT)
                        elif event.key == pygame.K_RIGHT:
                            self.snake.turn(RIGHT)
            
            # 填充背景色
            self.screen.fill(BACKGROUND)
            
            # 绘制网格
            self.draw_grid()
            
            if not paused and not self.game_over:
                # 移动蛇
                self.snake.move()
                
                # 检查游戏结束
                if not self.snake.is_alive:
                    self.game_over = True
                
                # 检查食物碰撞
                self.check_collision()
            
            # 绘制食物和蛇
            self.food.draw(self.screen)
            self.snake.draw(self.screen)
            
            # 绘制分数
            self.draw_score()
            
            # 如果游戏结束，显示游戏结束画面
            if self.game_over:
                self.draw_game_over()
            
            # 如果游戏暂停，显示暂停文字
            if paused:
                pause_surface = self.big_font.render('游戏暂停', True, (255, 215, 0))
                self.screen.blit(pause_surface, 
                                 (WIDTH//2 - pause_surface.get_width()//2, HEIGHT//2))
                continue_surface = self.font.render('按空格键继续', True, TEXT_COLOR)
                self.screen.blit(continue_surface, 
                                 (WIDTH//2 - continue_surface.get_width()//2, HEIGHT//2 + 60))
            
            pygame.display.update()
            
            # 控制游戏速度
            if not paused:
                self.clock.tick(self.speed)
            else:
                self.clock.tick(5)

if __name__ == "__main__":
    game = Game()
    game.run()