import pygame
import random
import sys
import os

# ==================== 初始化部分 ====================
pygame.init()
pygame.mixer.init()

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 🔧 修改：场地大小不变，保持 480x700
SCREEN_WIDTH, SCREEN_HEIGHT = 500, 500
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("飞机大战 - 仅图片放大版")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)

clock = pygame.time.Clock()
FPS = 60

# ==================== 素材尺寸配置（仅图片放大10倍） ====================
# 🔧 修改：仅图片放大10倍，其他保持原样
PLAYER_SIZE = (80, 160)      # 玩家飞机尺寸（放大10倍）
ENEMY_SIZE = (40, 80)       # 敌机尺寸（放大10倍）
BULLET_SIZE = (16, 32)      # 子弹尺寸（放大10倍）
EXPLOSION_SIZE = (0, 0)   # 爆炸效果尺寸（放大10倍）
BACKGROUND_SIZE = (SCREEN_WIDTH, SCREEN_HEIGHT)  # 背景图尺寸（不变）

# ==================== 图片加载函数（仅放大图片） ====================
def load_image(path, default_color=(0, 0, 0), target_size=None, keep_aspect=True):
    """
    加载图片 - 支持自动缩放
    """
    # 先创建默认 Surface
    if target_size:
        default_surface = pygame.Surface(target_size)
    else:
        default_surface = pygame.Surface((160, 320))
    default_surface.fill(default_color)
    
    # 检查文件是否存在
    full_path = os.path.join(SCRIPT_DIR, path)
    if not os.path.exists(full_path):
        print(f"⚠️ 图片未找到：{path}")
        return default_surface
    
    # 尝试加载图片
    try:
        image = pygame.image.load(full_path)
        
        # 获取文件扩展名
        ext = os.path.splitext(full_path)[1].lower()
        
        # 根据格式处理颜色模式
        if ext == '.png':
            image = image.convert_alpha()
        elif ext in ['.jpg', '.jpeg']:
            image = image.convert_rgb()
        else:
            image = image.convert()
        
        # 如果目标尺寸比原图大，等比例放大
        if target_size:
            img_rect = image.get_rect()
            # 如果原图比目标尺寸小，等比例放大
            if img_rect.width < target_size[0] or img_rect.height < target_size[1]:
                scale = max(target_size[0] / img_rect.width, target_size[1] / img_rect.height)
                new_width = int(img_rect.width * scale)
                new_height = int(img_rect.height * scale)
                image = pygame.transform.scale(image, (new_width, new_height))
            # 如果原图比目标尺寸大，等比例缩小
            else:
                scale = min(target_size[0] / img_rect.width, target_size[1] / img_rect.height)
                new_width = int(img_rect.width * scale)
                new_height = int(img_rect.height * scale)
                image = pygame.transform.scale(image, (new_width, new_height))
        
        return image
        
    except Exception as e:
        print(f"⚠️ 加载失败：{e}")
        return default_surface

# ==================== 音效加载函数 ====================
def load_sound(path):
    """加载音效文件"""
    try:
        full_path = os.path.join(SCRIPT_DIR, path)
        if os.path.exists(full_path):
            return pygame.mixer.Sound(full_path)
        else:
            print(f"⚠️ 音效未找到：{path}")
            return None
    except:
        return None

# ==================== 玩家飞机类（仅图片放大，速度不变） ====================
class Player(pygame.sprite.Sprite):
    """玩家控制的飞机 - 图片放大10倍，速度不变"""
    def __init__(self):
        super().__init__()
        self.image = load_image('images/1.png', GREEN, PLAYER_SIZE)
        self.rect = self.image.get_rect()
        
        # 初始位置在屏幕底部中央
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 50
        
        # 🔧 修改：速度保持原样（8）
        self.speed = 8
        self.hp = 3
        self.shoot_sound = load_sound('sounds/shoot.wav')
    
    def update(self):
        """处理玩家移动 - 只响应键盘，不会自动下落"""
        keys = pygame.key.get_pressed()
        
        # 左移（不超出左边界）
        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
        # 右移（不超出右边界）
        if keys[pygame.K_RIGHT] and self.rect.right < SCREEN_WIDTH:
            self.rect.x += self.speed
        # 上移（不超出上边界）
        if keys[pygame.K_UP] and self.rect.top > 0:
            self.rect.y -= self.speed
        # 下移（不超出下边界）
        if keys[pygame.K_DOWN] and self.rect.bottom < SCREEN_HEIGHT:
            self.rect.y += self.speed
    
    def shoot(self):
        """发射子弹"""
        if self.shoot_sound:
            self.shoot_sound.play()
        return Bullet(self.rect.centerx, self.rect.top)

# ==================== 子弹类（仅图片放大，速度不变） ====================
class Bullet(pygame.sprite.Sprite):
    """玩家发射的子弹 - 图片放大10倍，速度不变"""
    def __init__(self, x, y):
        super().__init__()
        self.image = load_image('images/bullet.png', YELLOW, BULLET_SIZE)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        # 🔧 修改：速度保持原样（-10）
        self.speed = -10
    
    def update(self):
        """更新子弹位置"""
        self.rect.y += self.speed
        if self.rect.bottom < 0:
            self.kill()

# ==================== 敌机类（仅图片放大，速度不变） ====================
class Enemy(pygame.sprite.Sprite):
    """从上方落下的敌机 - 图片放大10倍，速度不变"""
    def __init__(self, enemy_type=1):
        super().__init__()
        
        if enemy_type == 1:
            self.image = load_image('images/2.png', RED, ENEMY_SIZE)
            # 🔧 修改：速度保持原样（2-4）
            self.speed = random.randrange(2, 4)
            self.score = 10
        else:
            self.image = load_image('images/3.png', RED, ENEMY_SIZE)
            # 🔧 修改：速度保持原样（4-7）
            self.speed = random.randrange(4, 7)
            self.score = 20
        
        self.rect = self.image.get_rect()
        self.rect.x = random.randrange(0, SCREEN_WIDTH - self.rect.width)
        self.rect.y = random.randrange(-100, -40)
    
    def update(self):
        """更新敌机位置"""
        self.rect.y += self.speed
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

# ==================== 爆炸效果类（仅图片放大） ====================
class Explosion(pygame.sprite.Sprite):
    """爆炸动画效果 - 图片放大10倍"""
    def __init__(self, x, y):
        super().__init__()
        self.images = []
        for i in range(1, 5):
            img = load_image(f'images/21{i}.png', RED, EXPLOSION_SIZE)
            if img:
                self.images.append(img)
        
        if not self.images:
            self.images = [pygame.Surface(EXPLOSION_SIZE)]
            self.images[0].fill(RED)
        
        self.frame = 0
        self.timer = 0
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
    
    def update(self):
        """更新爆炸动画"""
        self.timer += 1
        if self.timer >= 5:
            self.frame = (self.frame + 1) % len(self.images)
            self.image = self.images[self.frame]
            self.timer = 0
        if self.frame >= len(self.images) - 1:
            self.kill()

# ==================== 游戏辅助函数 ====================
def create_sprites():
    """创建所有游戏精灵"""
    all_sprites = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    bullets = pygame.sprite.Group()
    
    player = Player()
    all_sprites.add(player)
    
    # 创建混合类型的敌机（初始4个）
    for i in range(4):
        enemy_type = 1 if i < 2 else 2
        enemy = Enemy(enemy_type=enemy_type)
        enemy.rect.y = random.randrange(-300, -50)
        all_sprites.add(enemy)
        enemies.add(enemy)
    
    return all_sprites, enemies, bullets, player

def draw_score(screen, score, font, player):
    """在屏幕上绘制分数和生命值"""
    score_text = font.render(f"分数：{score}", True, WHITE)
    hp_text = font.render(f"生命：{player.hp}", True, WHITE)
    screen.blit(score_text, (10, 10))
    screen.blit(hp_text, (10, 40))

def game_over_screen(screen, score, font):
    """显示游戏结束界面"""
    font_large = pygame.font.Font(None, 74)
    
    texts = [
        (font_large.render("游戏结束", True, RED), (SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 - 50)),
        (font.render(f"最终分数：{score}", True, WHITE), (SCREEN_WIDTH//2 - 80, SCREEN_HEIGHT//2)),
        (font.render("按 R 重新开始", True, WHITE), (SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 + 50)),
        (font.render("按 Q 退出", True, WHITE), (SCREEN_WIDTH//2 - 60, SCREEN_HEIGHT//2 + 90))
    ]
    
    for text, pos in texts:
        screen.blit(text, pos)
    pygame.display.flip()
    
    while True:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return True
                if event.key == pygame.K_q:
                    return False

# ==================== 游戏主循环 ====================
def main():
    """游戏主函数"""
    all_sprites, enemies, bullets, player = create_sprites()
    
    score = 0
    font = pygame.font.Font(None, 36)  # 字体保持原样
    spawn_timer = 0
    running = True
    game_over = False
    
    bgm = load_sound('sounds/bgm.mp3')
    if bgm:
        bgm.play(-1)
    
    while running:
        clock.tick(FPS)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not game_over:
                    bullet = player.shoot()
                    all_sprites.add(bullet)
                    bullets.add(bullet)
        
        if not game_over:
            spawn_timer += 1
            # 敌机生成频率保持原样（500帧）
            if spawn_timer >= 50:
                enemy_type = random.choice([1, 2])
                enemy = Enemy(enemy_type=enemy_type)
                all_sprites.add(enemy)
                enemies.add(enemy)
                spawn_timer = 0
            
            all_sprites.update()
            
            # 检测子弹击中敌机
            for hit in pygame.sprite.groupcollide(enemies, bullets, True, True):
                score += hit.score
                all_sprites.add(Explosion(hit.rect.centerx, hit.rect.centery))
            
            # 检测敌机撞击玩家
            for hit in pygame.sprite.spritecollide(player, enemies, True):
                player.hp -= 1
                all_sprites.add(Explosion(player.rect.centerx, player.rect.centery))
                if player.hp <= 0:
                    game_over = True
        
        screen.fill(BLACK)
        all_sprites.draw(screen)
        draw_score(screen, score, font, player)
        pygame.display.flip()
    
    if game_over:
        if not game_over_screen(screen, score, font):
            running = False
    
    pygame.quit()
    sys.exit()

# ==================== 程序入口 ====================
if __name__ == "__main__":
    main()