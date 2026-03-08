import pygame
import random

# 初始化游戏
pygame.init()

# 设置游戏窗口
WIDTH, HEIGHT = 800, 600
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("贪吃蛇游戏")

# 定义颜色
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# 定义蛇和食物的大小
BLOCK_SIZE = 20

# 定义蛇的移动方向
UP = 0
DOWN = 1
LEFT = 2
RIGHT = 3

# 绘制蛇和食物
def draw_snake(snake):
    for block in snake:
        pygame.draw.rect(SCREEN, GREEN, (block[0], block[1], BLOCK_SIZE, BLOCK_SIZE))

def draw_food(food):
    pygame.draw.rect(SCREEN, RED, (food[0], food[1], BLOCK_SIZE, BLOCK_SIZE))

# 主游戏循环
def main():
    clock = pygame.time.Clock()
    running = True
    snake = [[WIDTH // 2, HEIGHT // 2]]
    food = [random.randint(0, (WIDTH - BLOCK_SIZE) // BLOCK_SIZE) * BLOCK_SIZE,
            random.randint(0, (HEIGHT - BLOCK_SIZE) // BLOCK_SIZE) * BLOCK_SIZE]
    direction = RIGHT

    while running:
        SCREEN.fill(WHITE)
        draw_snake(snake)
        draw_food(food)
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP and direction != DOWN:
                    direction = UP
                elif event.key == pygame.K_DOWN and direction != UP:
                    direction = DOWN
                elif event.key == pygame.K_LEFT and direction != RIGHT:
                    direction = LEFT
                elif event.key == pygame.K_RIGHT and direction != LEFT:
                    direction = RIGHT

        head_x, head_y = snake[0]
        if direction == UP:
            new_head = [head_x, head_y - BLOCK_SIZE]
        elif direction == DOWN:
            new_head = [head_x, head_y + BLOCK_SIZE]
        elif direction == LEFT:
            new_head = [head_x - BLOCK_SIZE, head_y]
        elif direction == RIGHT:
            new_head = [head_x + BLOCK_SIZE, head_y]

        snake.insert(0, new_head)

        if new_head == food:
            food = [random.randint(0, (WIDTH - BLOCK_SIZE) // BLOCK_SIZE) * BLOCK_SIZE,
                    random.randint(0, (HEIGHT - BLOCK_SIZE) // BLOCK_SIZE) * BLOCK_SIZE]
        else:
            snake.pop()

        if (new_head[0] < 0 or new_head[0] >= WIDTH or
                new_head[1] < 0 or new_head[1] >= HEIGHT or
                new_head in snake[1:]):
            running = False

        clock.tick(10)

    pygame.quit()

if __name__ == "__main__":
    main()
