import pygame  
import sys  
import random  
  
pygame.init()  
  
# 初始化设置  
screen = pygame.display.set_mode((600, 300))  
pygame.display.set_caption("方块造物录")  
clock = pygame.time.Clock()  
  
# 加载素材  
beijing = pygame.image.load("素材\\背景.png")  
fangkuai = pygame.image.load("素材\\方块.png")  
renwu = pygame.image.load("素材\\人物.png")  
  
# 游戏参数  
GROUND_Y = 218  
player_x = 50  
player_y = GROUND_Y - renwu.get_height()  
player_speed = 5  
is_jumping = False  
jump_count = 10  
gravity = 1  
obstacles = []  
game_over = False  
score = 0  
font = pygame.font.SysFont(None, 36)  
  
# 生成初始障碍物  
for i in range(1):  
    obstacles.append({  
        'x': 300 + i * 600,  
        'width': fangkuai.get_width(),  
        'height': fangkuai.get_height()  
    })  
  
def draw_objects():  
    screen.blit(beijing, (0, 0))  
    # 绘制障碍物  
    for obstacle in obstacles:  
        screen.blit(fangkuai, (obstacle['x'], GROUND_Y - obstacle['height']))  
    # 绘制玩家  
    screen.blit(renwu, (player_x, player_y))  
    # 显示分数  
    score_text = font.render(f"score: {score}", True, (255, 255, 255))  
    screen.blit(score_text, (10, 10))  
    if game_over:  
        over_text = font.render("Game over! Press R to restart", True, (255, 0, 0))  
        screen.blit(over_text, (150, 150))  
  
def check_collision():  
    player_rect = pygame.Rect(player_x, player_y, renwu.get_width(), renwu.get_height())  
    for obstacle in obstacles:  
        obstacle_rect = pygame.Rect(obstacle['x'], GROUND_Y - obstacle['height'],   
                                  obstacle['width'], obstacle['height'])  
        if player_rect.colliderect(obstacle_rect):  
            return True  
    return False  
  
def reset_game():  
    global player_x, player_y, is_jumping, jump_count, obstacles, game_over, score  
    player_x = 50  
    player_y = GROUND_Y - renwu.get_height()  
    is_jumping = False  
    jump_count = 10  
    obstacles = []  
    for i in range(1):  
        obstacles.append({  
            'x': 300 + i * 600,  
            'width': fangkuai.get_width(),  
            'height': fangkuai.get_height()  
        })  
    game_over = False  
    score = 0  
  
# 游戏主循环  
while True:  
    for event in pygame.event.get():  
        if event.type == pygame.QUIT:  
            pygame.quit()  
            sys.exit()  
        elif event.type == pygame.KEYDOWN:  
            if event.key == pygame.K_SPACE and not is_jumping and not game_over:  
                is_jumping = True  
            elif event.key == pygame.K_r and game_over:  
                reset_game()  
  
    if not game_over:  
        # 移动障碍物  
        for obstacle in obstacles:  
            obstacle['x'] -= 5  
            if obstacle['x'] < -obstacle['width']:  
                obstacle['x'] = 600 + random.randint(0, 100)  
                score += 1  
          
        # 跳跃逻辑  
        if is_jumping:  
            if jump_count >= -10:  
                neg = 1  
                if jump_count < 0:  
                    neg = -1  
                player_y -= (jump_count ** 2) * 0.5 * neg  
                jump_count -= 1  
            else:  
                is_jumping = False  
                jump_count = 10  
                player_y = GROUND_Y - renwu.get_height()  
          
        # 检测碰撞  
        if check_collision():  
            game_over = True  
      
    # 绘制游戏  
    draw_objects()  
    pygame.display.flip()  
    clock.tick(60)  
