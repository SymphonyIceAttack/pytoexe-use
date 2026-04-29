import pygame
import sys
import random
import math
import pickle
import os

pygame.init()
pygame.mixer.init() 

BASE_DIR = os.path.dirname(__file__)

def asset(path):
    return os.path.join(BASE_DIR, 'assets', path)

WIDTH, HEIGHT = 720, 360
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Spellbound')

pygame.display.set_icon(pygame.image.load(asset('logo.png')).convert_alpha())

clock = pygame.time.Clock()

lobby = asset('lobby.mp3')
game_music = asset('sm good.mp3')
survival_music = asset('survival.mp3')

volume = 100

pygame.mixer.music.load(lobby)
pygame.mixer.music.set_volume(volume/100)

running = True
menu = True
game = False
survival = False
gamemodes = False
levels = False
collection = False
editor = False
create = False
edit = False
shop = False
spells = False
audio = True
settings_tab = False

prev_tab = menu

fullscreen = False

class Camera:
    def __init__(self, world_w, world_h):
        self.offset = pygame.Vector2(0, 0)
        self.world_w = world_w
        self.world_h = world_h
        self.zoom = 1
        self.min_zoom, self.max_zoom = 0.2, 5

    def follow(self, target, width, height):
        scaled_w = WIDTH
        scaled_h = HEIGHT

        self.offset.x = target.rect.centerx - scaled_w / 2
        self.offset.y = target.rect.centery - scaled_h / 2

        max_x = width - scaled_w
        max_y = height - scaled_h

        self.offset.x = max(0, min(self.offset.x, max_x))
        self.offset.y = max(0, min(self.offset.y, max_y))
            
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        
        self.normal = pygame.transform.scale(pygame.image.load(asset('player.png')).convert_alpha(), (40, 40))
        self.image = self.normal
        self.rect = pygame.Rect(x, y, 40, 40)

        self.frames_right = [pygame.image.load(asset('player1.png')).convert_alpha(), pygame.image.load(asset('player2.png')).convert_alpha(), pygame.image.load(asset('player3.png')).convert_alpha(), pygame.image.load(asset('player4.png')).convert_alpha()]
        self.frames_left = [
            pygame.transform.flip(frame, True, False)
            for frame in self.frames_right
        ]

        self.punch_right = [pygame.image.load(asset('attack1.png')).convert_alpha(), pygame.image.load(asset('attack3.png')).convert_alpha()]
        self.punch_left = [
            pygame.transform.flip(frame, True, False)
            for frame in self.punch_right
        ]

        self.slash_rect = pygame.Rect(self.rect.x+20, self.rect.y, self.rect.width+40, self.rect.height)
        self.slash_right = [pygame.image.load(asset('slash1.png')).convert_alpha(), pygame.image.load(asset('slash2.png')).convert_alpha(), pygame.image.load(asset('slash3.png')).convert_alpha(), pygame.image.load(asset('slash4.png')).convert_alpha(), pygame.image.load(asset('slash5.png')).convert_alpha(), pygame.image.load(asset('slash6.png')).convert_alpha()]
        self.slash_left = [
            pygame.transform.flip(frame, True, False)
            for frame in self.slash_right
        ]
        self.slash_img = self.slash_right[0]

        self.burn_right = [pygame.image.load(asset('burn1.png')).convert_alpha(), pygame.image.load(asset('burn2.png')).convert_alpha(), pygame.image.load(asset('burn3.png')).convert_alpha(), pygame.image.load(asset('burn4.png')).convert_alpha(), pygame.image.load(asset('burn5.png')).convert_alpha(), pygame.image.load(asset('burn6.png')).convert_alpha()]
        self.burn_left = [
            pygame.transform.flip(frame, True, False)
            for frame in self.burn_right
        ]
        self.burn_img = self.burn_right[0]

        self.dash_right = [pygame.image.load(asset('dashing.png')).convert_alpha(), pygame.image.load(asset('dashing2.png')).convert_alpha()]
        self.dash_left = [
            pygame.transform.flip(frame, True, False)
            for frame in self.dash_right
        ]

        self.shields = [pygame.image.load(asset('shield1.png')).convert_alpha(), pygame.image.load(asset('shield2.png')).convert_alpha(), pygame.image.load(asset('shield3.png')).convert_alpha()]
        self.shield_img = self.shields[0]

        self.charge_right = [pygame.image.load(asset('charge1.png')).convert_alpha(), pygame.image.load(asset('charge2.png')).convert_alpha()]
        self.charge_left = [
            pygame.transform.flip(frame, True, False)
            for frame in self.charge_right
        ]

        self.climbing_img = [pygame.image.load(asset('climbing1.png')).convert_alpha(), pygame.image.load(asset('climbing2.png')).convert_alpha()]

        self.ishurt = False
        self.hurt_timer = 0
        self.hurt_duration = 10
        self.shield_timer = 0

        self.taken = False
        self.hand = None

        self.shakeX, self.shakeY = 0, 0

        self.spells = ['slash', 'fireball']
        self.rotation = ['slash', 'fireball']
        self.selected_spell = None
        self.curr_unlock = 'dash'

        self.lvl = 1
        self.coins = 0
        self.xp = 0
        self.ladders = 0
        self.reset()

    def reset(self):
        self.rect.x = 100
        self.rect.y = 200

        spellCooldowns = {'slash': 15,
         'fireball': 30,
         'dash': 30,
         'shield': 40,
         'laser': 40,
         'zap': 30,
         'heal': 60,
         'burn': 10,
         'freeze': 40,
         'poison': 50,
         'charge': 40,
         'teleport': 55,
         'ghost': 60,
         'hand': 10}

        self.frame_index = 0
        self.frame_index2 = 0
        self.animation_speed = 0.5

        self.speed = 10
        self.speed_timer = 0
        
        self.jump_power = 23
        self.gravity = 2.5
        self.fall_multiplier = 2.0
        self.terminal_velocity = 22
        
        self.vel_x = 0
        self.vel_y = 0

        self.on_ground = False
        self.jump_pressed = False
        self.flipped = False

        self.hp = 100
        self.regen = False
        self.frames_after_hurt = 0
        self.spikecooldown = 20
        
        self.ishurt = False
        self.hurt_timer = 0
        self.hurt_duration = 10
        self.shield_timer = 0

        self.taken = False
        self.hand = None

        self.shakeX, self.shakeY = 0, 0

        self.curr_spell = self.rotation[0]
        self.selected_spell = None
        self.dmg_red = 1

        self.attacking = False
        self.shield = False
        self.invis = False
        self.ghost_timer = 0
        self.dash_timer = 4
        self.tick = 0
        self.speed_boost = 0
        self.climbing = False
        self.carried = False

        self.platform = None

    def handle_input(self):
        keys = pygame.key.get_pressed()
        self.vel_x = 0

        if (keys[pygame.K_a] or keys[pygame.K_LEFT]) and not (player.attacking and (player.curr_spell == 'dash' or player.curr_spell == 'laser' or player.curr_spell == 'charge')):
            if self.rect.x > 0:
                self.vel_x = -self.speed
                self.flipped = True
        if (keys[pygame.K_d] or keys[pygame.K_RIGHT]) and not (player.attacking and (player.curr_spell == 'dash' or player.curr_spell == 'laser' or player.curr_spell == 'charge')):
            if self.rect.x < curr_level.width-40:
                self.vel_x = self.speed
                self.flipped = False

        if not self.climbing and (keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]) and not (player.attacking and (player.curr_spell == 'dash' or player.curr_spell == 'charge')):
            if self.on_ground and not self.jump_pressed:
                self.vel_y = -self.jump_power
                self.on_ground = False
                self.jump_pressed = True
                self.carried = False
                self.platform = None
            for l in ladders:
                if self.rect.colliderect(l):
                    self.climbing = True
                    
        if self.climbing and (keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]) and not (player.attacking and (player.curr_spell == 'dash' or player.curr_spell == 'charge')):
            self.rect.y += self.vel_y

        else:
            self.jump_pressed = False
            if self.climbing:
                self.climbing = False
                self.vel_y = 0
    def animate(self):
        if not (self.vel_x != 0 and self.on_ground):
            if self.ishurt:
                self.invis = False
                self.image.set_alpha(120)
                self.shakeX = random.randint(-4, 4)
                self.shakeY = random.randint(-4, 4)
                self.hurt_timer += 1

                self.regen = False
                self.frames_after_hurt = 0
                
                if self.hurt_timer >= self.hurt_duration:
                    self.hurt_timer = 0
                    self.shakeX, self.shakeY = 0, 0
                    self.ishurt = False
                    self.regen = True
            else:
                self.image.set_alpha(255)
            if not self.on_ground:
                self.image = pygame.transform.flip(self.frames_right[0], self.flipped, False)
            if self.attacking and player.curr_spell == 'slash':
                self.frame_index += self.animation_speed
                if self.frame_index >= len(self.punch_right):
                    self.frame_index = 0
                    self.attacking = False
                    spellCurrCooldowns[player.curr_spell] = 0
                frames = self.punch_right if not self.flipped else self.punch_left
                self.image = frames[int(self.frame_index)]
            if self.attacking and (player.curr_spell == 'fireball' or player.curr_spell == 'zap' or player.curr_spell == 'freeze' or player.curr_spell == 'poison' or player.curr_spell == 'hand'):
                if not self.frame_index > len(self.punch_right)-1:
                    self.frame_index += self.animation_speed
                if self.frame_index >= len(self.punch_right):
                    self.frame_index = 0
                frames = self.punch_right if not self.flipped else self.punch_left
                self.image = frames[int(self.frame_index)]
            if self.attacking and player.curr_spell == 'dash':
                self.dmg_red = 0.5
                self.dash_timer -= 1
                self.frame_index += self.animation_speed
                if self.frame_index >= len(self.dash_right):
                    self.frame_index = 0
                frames = self.dash_right if not self.flipped else self.dash_left
                self.image = frames[int(self.frame_index)]
                if self.dash_timer <= 0:
                    self.attacking = False
                    self.gravity = 2.5
                    self.dash_timer = 4
                    self.dmg_red = 1
                    spellCurrCooldowns[player.curr_spell] = 0
            if self.attacking and player.curr_spell == 'charge':
                self.dmg_red = 0.5
                self.dash_timer -= 1
                self.frame_index += self.animation_speed
                if self.frame_index >= len(self.charge_right):
                    self.frame_index = 0
                frames = self.charge_right if not self.flipped else self.charge_left
                self.image = frames[int(self.frame_index)]
                if self.dash_timer == 0:
                    self.attacking = False
                    self.gravity = 2.5
                    self.dmg_red = 1
                    self.dash_timer = 4
                    spellCurrCooldowns[player.curr_spell] = 0
            if self.shield:
                self.shield_timer += 1
                if self.shield_timer <= 3 and self.shield_timer < 28:
                    self.shield_img = self.shields[self.shield_timer-1]
                if self.shield_timer == 28:
                    self.shield_img = self.shields[1]
                if self.shield_timer == 29:
                    self.shield_img = self.shields[0]
                if self.shield_timer >= 30:
                    self.shield = False
                    self.shield_timer = 0
            if self.attacking and self.curr_spell == 'laser':
                frames = self.frames_right if not self.flipped else self.frames_left
                self.image = frames[0]
            if self.attacking and player.curr_spell == 'burn':
                self.frame_index += self.animation_speed
                if self.frame_index >= len(self.punch_right):
                    self.frame_index = 0
                    self.attacking = False
                    spellCurrCooldowns[player.curr_spell] = 0
                frames = self.punch_right if not self.flipped else self.punch_left
        if self.vel_x != 0 and self.on_ground:
            self.frame_index += self.animation_speed
            if self.frame_index >= len(self.frames_right):
                self.frame_index = 0
            frames = self.frames_right if not self.flipped else self.frames_left
            self.image = frames[int(self.frame_index)]
        if self.climbing and (keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]):
            self.frame_index += self.animation_speed
            if self.frame_index >= len(self.climbing_img):
                self.frame_index = 0
            self.image = self.climbing_img[int(self.frame_index)]

    def update(self, blocks):
        self.handle_input()

        if self.hp <= 0 or self.rect.y > 2000 or self.rect.y < 0:
            self.hp = 0
        
        if self.vel_x == 0:
            self.image = pygame.transform.flip(self.normal, self.flipped, False)
        self.image = pygame.transform.scale(self.image, (40, 40))

        self.spikecooldown += 1

        if self.attacking and player.curr_spell == 'dash':
            self.gravity = 0
            if self.flipped:
                self.vel_x = -20
            else:
                self.vel_x = 20

        if self.attacking and player.curr_spell == 'charge':
            self.gravity = 0
            if self.flipped:
                self.vel_x = -20
            else:
                self.vel_x = 20

        for e in enemies:
            if e.rect.colliderect(pygame.Rect(self.rect.x-6, self.rect.y-6, 52, 52)) and self.shield_timer <= 3 and self.shield and e.dmg_cooldown >= 6:
                e.knockback = True
                e.hp -= 4
                e.dmg_cooldown = 0
                return
        self.ladders = 0
        for l in ladders:
            if self.rect.colliderect(l):
                self.ladders += 1
        if self.ladders < 1:
            self.climbing = False


        if self.regen and survival and self.hp > 0:
            self.frames_after_hurt += 1
            if self.frames_after_hurt%45 == 0 and self.frames_after_hurt > 45:
                self.hp += 5
            if self.hp >= 100:
                self.regen = False
                self.frames_after_hurt = 0

        # Horizontal
        if not self.taken:
            self.rect.x += self.vel_x
            self.horizontal_collide(blocks)

            self.vel_y += self.gravity

        if not self.hand:
           self.taken = False
        if self.hand:
            self.taken = True
            
        if self.taken:
            dx = self.hand.rect.centerx - self.rect.centerx
            dy = self.hand.rect.centery - self.rect.centery

            distance = max(1, (dx**2 + dy**2) ** 0.5)

            # normalize direction
            self.vel_x = (dx / distance) * (self.hand.speed//2)
            self.vel_y = (dy / distance) * (self.hand.speed//2)

            self.rect.x += self.vel_x
            
            for block in blocks:
                if self.rect.colliderect(block):
                    self.taken = False
                    self.hand = None
                    self.attacking = False
                    spellCurrCooldowns[player.curr_spell] = 0
                    self.frame_index = 0
                    
            self.rect.y += self.vel_y

            for block in blocks:
                if self.rect.colliderect(block):
                    self.taken = False
                    if self.hand:
                        self.hand.kill()
                    self.attacking = False

            if not self.curr_spell == 'hand':
                self.taken = False

        if not self.attacking and self.hand:
            self.taken = False
            self.hand = None
            hands = pygame.sprite.Group()
            self.attacking = False
            spellCurrCooldowns[player.curr_spell] = 0
            self.frame_index = 0

        if self.vel_y > 0 and not self.climbing:  # fall faster than rise
            self.vel_y += self.gravity * (self.fall_multiplier - 1)

        if self.vel_y > self.terminal_velocity:
            self.vel_y = self.terminal_velocity

        if self.platform and not (self.rect.colliderect(self.platform.rect)
                                  or (self.rect.bottom == self.platform.rect.top and self.rect.x >= self.platform.rect.x-40 and self.rect.x <= self.platform.rect.right)):
            self.carried = False
            self.platform = None

        if self.climbing:
            self.image = self.climbing_img[int(self.frame_index%2)]
            self.vel_y = -3
        if not (self.attacking and player.curr_spell == 'laser') and not self.taken: 
            self.rect.y += self.vel_y
        self.on_ground = False
        if self.carried:
            self.on_ground = True
        if not self.taken:
            self.vertical_collide(blocks)

        if not self.flipped:
            self.slash_rect = pygame.Rect(self.rect.x+20, self.rect.y, self.rect.width, self.rect.height)

        elif self.flipped:
            self.slash_rect = pygame.Rect(self.rect.x-20, self.rect.y, self.rect.width, self.rect.height)

        self.animate()

    def horizontal_collide(self, blocks):

        # spikes
        for spike in spikes:
            if self.rect.colliderect(spike):
                if self.spikecooldown >= 20:
                    self.spikecooldown = 0
                    self.hp -= 10
                    self.ishurt = True

        # normal blocks
        for block in blocks:
            if self.rect.colliderect(block):

                self.carried = False

                if self.platform and self.vel_y < 0 and self.rect.y <= block.bottom:
                    self.platform.direction *= -1

                if self.climbing:
                    self.climbing = False
                    self.vel_y = 0
                    self.vel_x = 0

                if self.vel_x > 0:
                    self.rect.right = block.left
                    self.vel_x = 0

                elif self.vel_x < 0:
                    self.rect.left = block.right
                    self.vel_x = 0

                self.platform = None

        # moving platforms
        for m in movingBlocks:
            if self.rect.colliderect(m.rect):

                if self.vel_x > 0:
                    self.rect.right = m.rect.left
                    self.vel_x = 0

                elif self.vel_x < 0:
                    self.rect.left = m.rect.right
                    self.vel_x = 0

    def vertical_collide(self, blocks):

        # spikes
        for spike in spikes:
            if self.rect.colliderect(spike):
                if self.spikecooldown >= 20:
                    self.spikecooldown = 0
                    self.hp -= 10
                    self.ishurt = True

        # normal blocks
        for block in blocks:

            if self.climbing:
                self.climbing = False
                self.vel_y = 0
                self.vel_x = 0

            if self.rect.colliderect(block):
                if self.vel_y > 0:
                    self.rect.bottom = block.top
                    self.vel_y = 0
                    self.on_ground = True

                elif self.vel_y < 0:
                    if self.platform:
                        self.platform.direction *= -1
                    self.rect.top = block.bottom
                    self.vel_y = 0

        # moving platforms
        for m in movingBlocks:
            if self.rect.colliderect(m.rect):

                if self.vel_y >= 0:
                    self.rect.bottom = m.rect.top
                    self.carried = True
                    self.platform = m
                    self.vel_y = 0
                    self.on_ground = True
                    self.jump_pressed = False

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.frames = [
            pygame.image.load(asset('ghost_tl.png')).convert_alpha(),
            pygame.image.load(asset('ghost_bl.png')).convert_alpha(),
            pygame.image.load(asset('ghost_tr.png')).convert_alpha(),
            pygame.image.load(asset('ghost_br.png')).convert_alpha()
        ]
        
        self.zap = [
            pygame.image.load(asset('zapped1.png')).convert_alpha()
        ]

        self.zapped = False
        self.burned = False
        self.frozen = False
        self.poisoned = False
        self.confused = False
        self.tick = 0

        self.image = pygame.transform.scale(self.frames[0], (40, 40))
        self.rect = self.image.get_rect(topleft=(x, y))

        # ── ANIMATION ────────────────────────────────
        self.frame_index = 0
        self.anim_speed = 0.25

        # ── MOVEMENT ─────────────────────────────────
        self.vel_x = 0
        self.vel_y = 0

        self.target = player
        self.follow_distance = 35

        self.knockback = False
        self.knock_index = 0

        self.on_ground = False

        self.taken = False
        self.hand = None

        # ── AI ───────────────────────────────────────
        self.follow_range = 500
        self.jump_cooldown = 0

        self.attack_cooldown = 0
        self.dmg_cooldown = 6
        self.dmg_cooldown2 = 0
        self.hp = 20
        self.max_hp = 20

    # ────────────────────────────────────────────────
    def follow_target_entity(self):
        if not self.target:
            return

        dx = self.target.rect.centerx - self.rect.centerx
        dy = self.target.rect.centery - self.rect.centery

        distance = max(1, (dx**2 + dy**2) ** 0.5)

        # normalize direction
        self.vel_x = (dx / distance) * self.speed
        self.vel_y = (dy / distance) * self.speed

    def animate(self):
        if self.vel_x <= 0 and self.vel_y <= 0:
            self.image = self.frames[0]
        if self.vel_x < 0 and self.vel_y > 0:
            self.image = self.frames[1]
        if self.vel_x > 0 and self.vel_y < 0:
            self.image = self.frames[2]
        if self.vel_x > 0 and self.vel_y > 0:
            self.image = self.frames[3]

    # ────────────────────────────────────────────────
    def update(self, player, blocks, spikes):
        if self.knockback:
            self.knock_index += 1
            if self.knock_index > 4:
                self.knock_index = 0
                self.knockback = False
            if self.vel_x < 0:
                self.vel_x = 10
            else:
                self.vel_x = -10
        else:
            if not player.invis:
                self.follow_target_entity()
            else:
                if not self.taken:
                    self.vel_x, self.vel_y = 0, 0
                else:
                    self.rect.center = self.hand.rect.center
                
        self.attack_cooldown += 1
        self.dmg_cooldown += 1
        if self.zapped or self.burned:
            self.dmg_cooldown2 += 1
        else:
            self.dmg_cooldown2 = 0


        if self.rect.colliderect(player.rect) and self.attack_cooldown >= 30 and not player.shield:
            player.hp -= 10 * player.dmg_red
            player.ishurt = True
            if player.invis:
                spellCurrCooldowns['invis'] = 0
            self.attack_cooldown = 0
            player.invis = False

        if self.rect.colliderect(player.slash_rect) and self.dmg_cooldown >= 10 and spellCurrCooldowns[player.curr_spell] >= 10 and player.attacking and player.curr_spell == 'slash':
            self.hp -= 10
            self.dmg_cooldown = 0
            spellCurrCooldowns[player.curr_spell] = 0
            self.knockback = True

        if self.rect.colliderect(player.slash_rect) and self.dmg_cooldown >= 10 and spellCurrCooldowns[player.curr_spell] >= 10 and player.attacking and player.curr_spell == 'burn':
            self.hp -= 8
            self.dmg_cooldown = 0
            spellCurrCooldowns[player.curr_spell] = 0
            self.burned = True
            self.tick = 0
            self.knockback = True

        if self.rect.colliderect(player.rect) and self.dmg_cooldown >= 10 and spellCurrCooldowns[player.curr_spell] >= 10 and player.attacking and player.curr_spell == 'dash':
            self.hp -= 10
            self.dmg_cooldown = 0
            spellCurrCooldowns[player.curr_spell] = 0
            self.knockback = True
            self.dmg_red = 0.5

        if self.rect.colliderect(player.rect) and self.dmg_cooldown >= 10 and spellCurrCooldowns[player.curr_spell] >= 10 and player.attacking and player.curr_spell == 'charge':
            self.hp -= 8
            self.dmg_cooldown = 0
            self.zapped = True
            self.tick = 0
            player.speed *= 1.5
            player.speed_timer += 1
            spellCurrCooldowns[player.curr_spell] = 0
            self.knockback = True
            self.dmg_red = 0.5

        # Horizontal
        if not (self.zapped and self.dmg_cooldown2 >= 15) and not self.frozen:
            self.rect.x += self.vel_x

        if not self.frozen or not self.taken:
            self.rect.y += self.vel_y

        if self.rect.x != player.rect.x or self.rect.y != player.rect.y:
            self.animate()

        if self.target and hasattr(self.target, 'alive'):
            if not self.target.alive():
                self.target = player

        if self.hp <= 0:
            self.die()

        if not self.hand or len(hands) == 0:
            self.taken = False

        if self.taken:
            self.rect.center = self.hand.rect.center
            for block in blocks:
                if self.rect.colliderect(block):
                    self.taken = False
                    self.hand = None
                    spellCurrCooldowns[player.curr_spell] = 0
                    player.attacking = False
                    player.frame_index = 0

    def die(self):
        self.kill()

class Blob(Enemy):
    def __init__(self, x, y, speed=3):
        super().__init__(x, y)

        # ── SPRITES ─────────────────────────────────
        self.frames_right = [
            pygame.image.load(asset('blob1.png')).convert_alpha(),
            pygame.image.load(asset('blob2.png')).convert_alpha(),
        ]
        self.frames_left = [
            pygame.transform.flip(frame, True, False)
            for frame in self.frames_right
        ]

        self.zap = [
            pygame.image.load(asset('zapped1.png')).convert_alpha()
        ]

        self.zapped = False
        self.burned = False
        self.frozen = False
        self.poisoned = False
        self.confused = False
        self.tick = 0

        self.image = pygame.transform.scale(self.frames_right[0], (40, 40))
        self.rect = self.image.get_rect(topleft=(x, y))

        # ── ANIMATION ────────────────────────────────
        self.frame_index = 0
        self.anim_speed = 0.25
        self.flipped = False

        # ── MOVEMENT ─────────────────────────────────
        self.speed = speed
        self.vel_x = 0
        self.vel_y = 0

        self.jump_power = 14
        self.gravity = 1.6
        self.fall_multiplier = 2.0
        self.terminal_velocity = 22

        self.target = player
        self.follow_distance = 35

        self.knockback = False
        self.knock_index = 0

        self.on_ground = False

        self.taken = False
        self.hand = None

        # ── AI ───────────────────────────────────────
        self.follow_range = 500
        self.jump_cooldown = 0

        self.attack_cooldown = 0
        self.dmg_cooldown = 6
        self.dmg_cooldown2 = 0
        self.hp = 20
        self.max_hp = 20

    # ────────────────────────────────────────────────
    def follow_target_entity(self):
        target = self.target
        if not target:
            return

        dx = target.rect.centerx - self.rect.centerx

        if abs(dx) < 32:
            self.vel_x = 0
            return

        self.vel_x = self.speed if dx > 0 else -self.speed
        self.flipped = dx < 0

    # ────────────────────────────────────────────────
    def should_jump(self, blocks, spikes):
        if not self.on_ground or self.jump_cooldown > 0:
            return False

        direction = -1 if self.flipped else 1

        front_rect = pygame.Rect(
            self.rect.centerx + direction * (self.rect.width // 2),
            self.rect.bottom - 6,
            6,
            6
        )

        above_rect = pygame.Rect(
            front_rect.x - self.rect.width // 2,
            self.rect.top - self.rect.height,
            self.rect.width,
            self.rect.height
        )

        hit_front = any(front_rect.colliderect(block) for block in blocks)
        space_clear = not any(above_rect.colliderect(block) for block in blocks)

        spike_front = any(front_rect.colliderect(s) for s in spikes)

        return hit_front and space_clear and not spike_front
    # ────────────────────────────────────────────────
    def animate(self):
        if self.vel_x != 0 and self.on_ground:
            self.frame_index += self.anim_speed
            if self.frame_index >= len(self.frames_right):
                self.frame_index = 0
        else:
            self.frame_index = 0

        frames = self.frames_left if self.flipped else self.frames_right
        self.image = frames[int(self.frame_index)]

    # ────────────────────────────────────────────────
    def horizontal_collide(self, blocks):
        for block in blocks:
            if self.rect.colliderect(block):
                if self.vel_x > 0:
                    self.rect.right = block.left
                    self.knockback = False
                elif self.vel_x < 0:
                    self.rect.left = block.right
                    self.knockback = False

    def vertical_collide(self, blocks):
        for block in blocks:
            if self.rect.colliderect(block):
                if self.vel_y > 0:
                    self.rect.bottom = block.top
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0:
                    self.rect.top = block.bottom
                    self.vel_y = 0
                    
    def spike_ahead(self, spikes):
        direction = -1 if self.flipped else 1

        check_rect = pygame.Rect(
            self.rect.centerx + direction * (self.rect.width // 2),
            self.rect.bottom + 1,
            6,
            6
        )

        return any(check_rect.colliderect(spike.rect if hasattr(spike, 'rect') else spike)
                   for spike in spikes)

    def ground_ahead(self, blocks):
        direction = -1 if self.flipped else 1

        check_rect = pygame.Rect(
            self.rect.centerx + direction * (self.rect.width // 2) + direction * 4,
            self.rect.bottom + 2,
            6,
            6
        )

        return any(
            check_rect.colliderect(block.rect if hasattr(block, 'rect') else block)
            for block in blocks
        )

    # ────────────────────────────────────────────────
    def update(self, player, blocks, spikes):
        if self.knockback:
            self.knock_index += 1
            if self.knock_index > 4:
                self.knock_index = 0
                self.knockback = False
            if self.flipped:
                self.vel_x = 10
            else:
                self.vel_x = -10
        else:
            if not player.invis:
                self.follow_target_entity()
            else:
                if not self.taken:
                    self.vel_x, self.vel_y = 0, 0
                else:
                    self.rect.center = self.hand.rect.center
                
        self.attack_cooldown += 1
        self.dmg_cooldown += 1
        if self.zapped or self.burned:
            self.dmg_cooldown2 += 1
        else:
            self.dmg_cooldown2 = 0

        # Decide jump BEFORE moving
        if self.on_ground and self.jump_cooldown == 0:
            front_x = self.rect.right if self.vel_x > 0 else self.rect.left - 5
            # rectangle in front of feet
            front_rect = pygame.Rect(front_x, self.rect.bottom - 5, 5, 5)
            # rectangle above front to see if space is free
            above_rect = pygame.Rect(front_x, self.rect.top - self.rect.height, self.rect.width, self.rect.height)

            hit_front = any(front_rect.colliderect(block) for block in blocks)
            space_above = any(above_rect.colliderect(block) for block in blocks)

            if hit_front and not space_above:
                self.vel_y = -self.jump_power
                self.jump_cooldown = 15

        if self.rect.colliderect(player.rect) and self.attack_cooldown >= 60 and not player.shield:
            player.hp -= 10 * player.dmg_red
            player.ishurt = True
            if player.invis:
                spellCurrCooldowns['invis'] = 0
            self.attack_cooldown = 0
            player.invis = False

        if self.rect.colliderect(player.slash_rect) and self.dmg_cooldown >= 10 and spellCurrCooldowns[player.curr_spell] >= 10 and player.attacking and player.curr_spell == 'slash':
            self.hp -= 10
            self.dmg_cooldown = 0
            spellCurrCooldowns[player.curr_spell] = 0
            self.knockback = True
            
        if self.rect.colliderect(player.slash_rect) and self.dmg_cooldown >= 10 and spellCurrCooldowns[player.curr_spell] >= 10 and player.attacking and player.curr_spell == 'burn':
            self.hp -= 8
            self.dmg_cooldown = 0
            spellCurrCooldowns[player.curr_spell] = 0
            self.burned = True
            self.tick = 0
            self.knockback = True

        if self.rect.colliderect(player.rect) and self.dmg_cooldown >= 10 and spellCurrCooldowns[player.curr_spell] >= 10 and player.attacking and player.curr_spell == 'dash':
            self.hp -= 10
            self.dmg_cooldown = 0
            spellCurrCooldowns[player.curr_spell] = 0
            self.knockback = True
            self.dmg_red = 0.5

        if self.rect.colliderect(player.rect) and self.dmg_cooldown >= 10 and spellCurrCooldowns[player.curr_spell] >= 10 and player.attacking and player.curr_spell == 'charge':
            self.hp -= 8
            self.dmg_cooldown = 0
            self.zapped = True
            self.tick = 0
            player.speed *= 1.5
            player.speed_timer += 1
            spellCurrCooldowns[player.curr_spell] = 0
            self.knockback = True
            self.dmg_red = 0.5

        # Horizontal
        if not (self.zapped and self.dmg_cooldown2 >= 15) and not self.frozen:
            self.rect.x += self.vel_x
        self.horizontal_collide(blocks)

        # Gravity
        self.vel_y += self.gravity
        if self.vel_y > 0:
            self.vel_y += self.gravity * (self.fall_multiplier - 1)
        if self.vel_y > self.terminal_velocity:
            self.vel_y = self.terminal_velocity

        if not self.frozen or not self.taken:
            self.rect.y += self.vel_y
            
        self.on_ground = False
        self.vertical_collide(blocks)

        if self.rect.x != player.rect.x or self.rect.y != player.rect.y:
            self.animate()

        if self.target and hasattr(self.target, 'alive'):
            if not self.target.alive():
                self.target = player

        if self.hp <= 0:
            self.die()

        self.ground_ahead(blocks)

        if not self.hand or len(hands) == 0:
            self.taken = False

        if self.taken:
            self.rect.center = self.hand.rect.center
            for block in blocks:
                if self.rect.colliderect(block):
                    self.taken = False
                    self.hand = None
                    spellCurrCooldowns[player.curr_spell] = 0
                    player.attacking = False
                    player.frame_index = 0

    def die(self):
        self.kill()

class Ghost(Enemy):
    def __init__(self, x, y, speed=3):
        super().__init__(x, y)

        # ── SPRITES ─────────────────────────────────
        self.frames = [
            pygame.image.load(asset('ghost_tl.png')).convert_alpha(),
            pygame.image.load(asset('ghost_bl.png')).convert_alpha(),
            pygame.image.load(asset('ghost_tr.png')).convert_alpha(),
            pygame.image.load(asset('ghost_br.png')).convert_alpha()
        ]
        
        self.zap = [
            pygame.image.load(asset('zapped1.png')).convert_alpha()
        ]

        self.zapped = False
        self.burned = False
        self.frozen = False
        self.poisoned = False
        self.confused = False
        self.tick = 0

        self.image = pygame.transform.scale(self.frames[0], (40, 40))
        self.rect = self.image.get_rect(topleft=(x, y))

        # ── ANIMATION ────────────────────────────────
        self.frame_index = 0
        self.anim_speed = 0.25

        # ── MOVEMENT ─────────────────────────────────
        self.speed = speed
        self.vel_x = 0
        self.vel_y = 0

        self.target = player
        self.follow_distance = 35

        self.knockback = False
        self.knock_index = 0
        self.knock_dir = 'right'

        self.on_ground = False

        self.taken = False
        self.hand = None

        # ── AI ───────────────────────────────────────
        self.follow_dist = 400
        self.jump_cooldown = 0

        self.attack_cooldown = 0
        self.dmg_cooldown = 6
        self.dmg_cooldown2 = 0
        self.hp = 20
        self.max_hp = 20
        self.dir = 'tl'

    # ────────────────────────────────────────────────
    def follow_target_entity(self):
        if not self.target:
            return
        dx, dy = 0, 0
        if distance(self.rect.centerx, self.rect.centery, self.target.rect.centerx, self.target.rect.centery) <= self.follow_dist:
            dx = self.target.rect.centerx - self.rect.centerx
            dy = self.target.rect.centery - self.rect.centery

        dist = max(1, (dx**2 + dy**2) ** 0.5)

        if distance(self.rect.centerx, self.rect.centery, self.target.rect.centerx, self.target.rect.centery) <= self.follow_dist:
            self.vel_x = (dx / dist) * self.speed
            self.vel_y = (dy / dist) * self.speed
        else:
            self.vel_x, self.vel_y = 0, 0

    def animate(self):
        if self.vel_x <= 0 and self.vel_y <= 0:
            self.image = self.frames[0]
            self.dir = 'tl'
        if self.vel_x < 0 and self.vel_y > 0:
            self.image = self.frames[1]
            self.dir = 'bl'
        if self.vel_x > 0 and self.vel_y < 0:
            self.image = self.frames[2]
            self.dir = 'tr'
        if self.vel_x > 0 and self.vel_y > 0:
            self.image = self.frames[3]
            self.dir = 'br'

    # ────────────────────────────────────────────────
    def update(self, player, blocks, spikes):
        if self.knockback:
            self.knock_index += 1
            if self.knock_index > 4:
                self.knock_index = 0
                self.knockback = False
            if self.knock_index == 1:
                if self.dir == 'tl' or self.dir == 'bl':
                    self.knock_dir = 'right'
                else:
                    self.knock_dir = 'left'
            self.vel_x = 10 if self.knock_dir == 'right' else -10
        else:
            if not player.invis:
                self.follow_target_entity()
            else:
                if not self.taken:
                    self.vel_x, self.vel_y = 0, 0
                else:
                    self.rect.center = self.hand.rect.center
                
        self.attack_cooldown += 1
        self.dmg_cooldown += 1
        if self.zapped or self.burned:
            self.dmg_cooldown2 += 1
        else:
            self.dmg_cooldown2 = 0


        if self.rect.colliderect(player.rect) and self.attack_cooldown >= 60 and not player.shield:
            player.hp -= 10 * player.dmg_red
            player.ishurt = True
            if player.invis:
                spellCurrCooldowns['invis'] = 0
            self.attack_cooldown = 0
            player.invis = False

        if self.rect.colliderect(player.slash_rect) and self.dmg_cooldown >= 10 and spellCurrCooldowns[player.curr_spell] >= 10 and player.attacking and player.curr_spell == 'slash':
            self.hp -= 10
            self.dmg_cooldown = 0
            spellCurrCooldowns[player.curr_spell] = 0
            self.knockback = True

        if self.rect.colliderect(player.slash_rect) and self.dmg_cooldown >= 10 and spellCurrCooldowns[player.curr_spell] >= 10 and player.attacking and player.curr_spell == 'burn':
            self.hp -= 8
            self.dmg_cooldown = 0
            spellCurrCooldowns[player.curr_spell] = 0
            self.burned = True
            self.tick = 0
            self.knockback = True

        if self.rect.colliderect(player.rect) and self.dmg_cooldown >= 10 and spellCurrCooldowns[player.curr_spell] >= 10 and player.attacking and player.curr_spell == 'dash':
            self.hp -= 10
            self.dmg_cooldown = 0
            spellCurrCooldowns[player.curr_spell] = 0
            self.knockback = True
            self.dmg_red = 0.5

        if self.rect.colliderect(player.rect) and self.dmg_cooldown >= 10 and spellCurrCooldowns[player.curr_spell] >= 10 and player.attacking and player.curr_spell == 'charge':
            self.hp -= 8
            self.dmg_cooldown = 0
            self.zapped = True
            self.tick = 0
            player.speed *= 1.5
            player.speed_timer += 1
            spellCurrCooldowns[player.curr_spell] = 0
            self.knockback = True
            self.dmg_red = 0.5

        # Horizontal
        if not (self.zapped and self.dmg_cooldown2 >= 15) and not self.frozen and not player.invis:
            self.rect.x += self.vel_x

        if not self.frozen or not self.taken and not player.invis:
            self.rect.y += self.vel_y

        if self.rect.x != player.rect.x or self.rect.y != player.rect.y:
            self.animate()

        if self.target and hasattr(self.target, 'alive'):
            if not self.target.alive():
                self.target = player

        if self.hp <= 0:
            self.die()

        if not self.hand or len(hands) == 0:
            self.taken = False

        if self.taken:
            self.rect.center = self.hand.rect.center
            for block in blocks:
                if self.rect.colliderect(block):
                    self.taken = False
                    self.hand = None
                    spellCurrCooldowns[player.curr_spell] = 0
                    player.attacking = False
                    player.frame_index = 0

    def die(self):
        self.kill()

class Sniper(Enemy):
    def __init__(self, x, y, speed=3):
        super().__init__(x, y)

        # ── SPRITES ─────────────────────────────────
        self.frames = [
            pygame.image.load(asset('sniper.png')).convert_alpha(),
            pygame.image.load(asset('sniper2.png')).convert_alpha(),
            pygame.image.load(asset('sniper3.png')).convert_alpha(),
            pygame.image.load(asset('sniper4.png')).convert_alpha()
        ]
        
        self.zap = [
            pygame.image.load(asset('zapped1.png')).convert_alpha()
        ]

        self.zapped = False
        self.burned = False
        self.frozen = False
        self.poisoned = False
        self.confused = False
        self.tick = 0

        self.image = pygame.transform.scale(self.frames[0], (40, 40))
        self.rect = self.image.get_rect(topleft=(x, y))

        # ── ANIMATION ────────────────────────────────
        self.frame_index = 0
        self.anim_speed = 0.25

        # ── MOVEMENT ─────────────────────────────────
        self.vel_x = 0
        self.vel_y = 0

        self.target = player
        self.follow_distance = 35

        self.knockback = False
        self.knock_index = 0
        self.knock_dir = 'right'

        self.on_ground = False

        self.taken = False
        self.hand = None

        # ── AI ───────────────────────────────────────
        self.follow_dist = 300
        self.jump_cooldown = 0

        self.attack_cooldown = 0
        self.dmg_cooldown = 6
        self.dmg_cooldown2 = 0
        self.hp = 35
        self.max_hp = 35
        self.dir = 'tl'

    def horizontal_collide(self, blocks):
        for block in blocks:
            if self.rect.colliderect(block):
                if self.vel_x > 0:
                    self.rect.right = block.left
                    self.knockback = False
                elif self.vel_x < 0:
                    self.rect.left = block.right
                    self.knockback = False

    def vertical_collide(self, blocks):
        for block in blocks:
            if self.rect.colliderect(block):
                if self.vel_y > 0:
                    self.rect.bottom = block.top
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0:
                    self.rect.top = block.bottom
                    self.vel_y = 0

    def animate(self):
        if player.rect.x - self.rect.x <= 0 and player.rect.y - self.rect.y <= 0:
            self.image = self.frames[3]
            self.dir = 'tl'
        if player.rect.x - self.rect.x <= 0 and player.rect.y - self.rect.y >= 0:
            self.image = self.frames[2]
            self.dir = 'bl'
        if player.rect.x - self.rect.x >= 0 and player.rect.y - self.rect.y <= 0:
            self.image = self.frames[1]
            self.dir = 'tr'
        if player.rect.x - self.rect.x >= 0 and player.rect.y - self.rect.y >= 0:
            self.image = self.frames[0]
            self.dir = 'br'

    # ────────────────────────────────────────────────
    def update(self, player, blocks, spikes):
        if self.knockback:
            self.knock_index += 1
            if self.knock_index > 4:
                self.knock_index = 0
                self.knockback = False
            if self.knock_index == 1:
                if self.dir == 'tl' or self.dir == 'bl':
                    self.knock_dir = 'right'
                else:
                    self.knock_dir = 'left'
            self.vel_x = 0 if self.knock_dir == 'right' else 0
        else:
            if not self.taken:
                self.vel_x, self.vel_y = 0, 0
            else:
                self.rect.center = self.hand.rect.center
                
        self.attack_cooldown += 1
        self.dmg_cooldown += 1
        if self.zapped or self.burned:
            self.dmg_cooldown2 += 1
        else:
            self.dmg_cooldown2 = 0


        if self.attack_cooldown >= 90 and not player.invis:
            darts.add(Dart(self.rect.centerx, self.rect.centery, player.rect.x, player.rect.y))
            self.attack_cooldown = 0

        if self.rect.colliderect(player.slash_rect) and self.dmg_cooldown >= 10 and spellCurrCooldowns[player.curr_spell] >= 10 and player.attacking and player.curr_spell == 'slash':
            self.hp -= 10
            self.dmg_cooldown = 0
            spellCurrCooldowns[player.curr_spell] = 0
            self.knockback = True

        if self.rect.colliderect(player.slash_rect) and self.dmg_cooldown >= 10 and spellCurrCooldowns[player.curr_spell] >= 10 and player.attacking and player.curr_spell == 'burn':
            self.hp -= 8
            self.dmg_cooldown = 0
            spellCurrCooldowns[player.curr_spell] = 0
            self.burned = True
            self.tick = 0
            self.knockback = True

        if self.rect.colliderect(player.rect) and self.dmg_cooldown >= 10 and spellCurrCooldowns[player.curr_spell] >= 10 and player.attacking and player.curr_spell == 'dash':
            self.hp -= 10
            self.dmg_cooldown = 0
            spellCurrCooldowns[player.curr_spell] = 0
            self.knockback = True
            self.dmg_red = 0.5

        if self.rect.colliderect(player.rect) and self.dmg_cooldown >= 10 and spellCurrCooldowns[player.curr_spell] >= 10 and player.attacking and player.curr_spell == 'charge':
            self.hp -= 8
            self.dmg_cooldown = 0
            self.zapped = True
            self.tick = 0
            player.speed *= 1.5
            player.speed_timer += 1
            spellCurrCooldowns[player.curr_spell] = 0
            self.knockback = True
            self.dmg_red = 0.5

        # Horizontal
        if not (self.zapped and self.dmg_cooldown2 >= 15) and not self.frozen and distance(player.rect.x, player.rect.y, self.rect.x, self.rect.y) <= 200:
            self.rect.x += self.vel_x

        if not self.frozen or not self.taken and distance(player.rect.x, player.rect.y, self.rect.x, self.rect.y) <= self.follow_dist:
            self.rect.y += self.vel_y

        if self.rect.x != player.rect.x or self.rect.y != player.rect.y:
            self.animate()

        if self.target and hasattr(self.target, 'alive'):
            if not self.target.alive():
                self.target = player

        if self.hp <= 0:
            self.die()

        if not self.hand or len(hands) == 0:
            self.taken = False

        if self.taken:
            self.rect.center = self.hand.rect.center
            for block in blocks:
                if self.rect.colliderect(b):
                    self.taken = False
                    self.hand = None
                    spellCurrCooldowns[player.curr_spell] = 0
                    player.attacking = False
                    player.frame_index = 0

    def die(self):
        self.kill()

class Bomb(Enemy):
    def __init__(self, x, y, speed=6):
        super().__init__(x, y)

        # ── SPRITES ─────────────────────────────────
        self.frames_right = [
            pygame.image.load(asset('bomb1.png')).convert_alpha(),
            pygame.image.load(asset('bomb2.png')).convert_alpha(),
        ]
        self.frames_left = [
            pygame.transform.flip(frame, True, False)
            for frame in self.frames_right
        ]

        self.zap = [
            pygame.image.load(asset('zapped1.png')).convert_alpha()
        ]

        self.zapped = False
        self.burned = False
        self.frozen = False
        self.poisoned = False
        self.confused = False
        self.tick = 0

        self.image = pygame.transform.scale(self.frames_right[0], (40, 40))
        self.rect = self.image.get_rect(topleft=(x, y))

        # ── ANIMATION ────────────────────────────────
        self.frame_index = 0
        self.anim_speed = 0.25
        self.flipped = False

        # ── MOVEMENT ─────────────────────────────────
        self.speed = speed
        self.vel_x = 0
        self.vel_y = 0

        self.jump_power = 14
        self.gravity = 1.6
        self.fall_multiplier = 2.0
        self.terminal_velocity = 22

        self.target = player
        self.follow_distance = 35

        self.knockback = False
        self.knock_index = 0

        self.on_ground = False

        self.taken = False
        self.hand = None

        # ── AI ───────────────────────────────────────
        self.follow_range = 500
        self.jump_cooldown = 0

        self.attack_cooldown = 0
        self.dmg_cooldown = 6
        self.dmg_cooldown2 = 0
        self.hp = 20
        self.max_hp = 20

    # ────────────────────────────────────────────────
    def follow_target_entity(self):
        target = self.target
        if not target:
            return

        dx = target.rect.centerx - self.rect.centerx

        self.vel_x = self.speed if dx > 0 else -self.speed
        self.flipped = dx < 0

    # ────────────────────────────────────────────────
    def should_jump(self, blocks, spikes):
        if not self.on_ground or self.jump_cooldown > 0:
            return False

        direction = -1 if self.flipped else 1

        front_rect = pygame.Rect(
            self.rect.centerx + direction * (self.rect.width // 2),
            self.rect.bottom - 6,
            6,
            6
        )

        above_rect = pygame.Rect(
            front_rect.x - self.rect.width // 2,
            self.rect.top - self.rect.height,
            self.rect.width,
            self.rect.height
        )

        hit_front = any(front_rect.colliderect(block) for block in blocks)
        space_clear = not any(above_rect.colliderect(block) for block in blocks)

        spike_front = any(front_rect.colliderect(s) for s in spikes)

        return hit_front and space_clear and not spike_front
    # ────────────────────────────────────────────────
    def animate(self):
        if self.vel_x != 0 and self.on_ground:
            self.frame_index += self.anim_speed
            if self.frame_index >= len(self.frames_right):
                self.frame_index = 0
        else:
            self.frame_index = 0

        frames = self.frames_left if self.flipped else self.frames_right
        self.image = frames[int(self.frame_index)]

    # ────────────────────────────────────────────────
    def horizontal_collide(self, blocks):
        for block in blocks:
            if self.rect.colliderect(block):
                if self.vel_x > 0:
                    self.rect.right = block.left
                    self.knockback = False
                elif self.vel_x < 0:
                    self.rect.left = block.right
                    self.knockback = False

    def vertical_collide(self, blocks):
        for block in blocks:
            if self.rect.colliderect(block):
                if self.vel_y > 0:
                    self.rect.bottom = block.top
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0:
                    self.rect.top = block.bottom
                    self.vel_y = 0
                    
    def spike_ahead(self, spikes):
        direction = -1 if self.flipped else 1

        check_rect = pygame.Rect(
            self.rect.centerx + direction * (self.rect.width // 2),
            self.rect.bottom + 1,
            6,
            6
        )

        return any(check_rect.colliderect(spike.rect if hasattr(spike, 'rect') else spike)
                   for spike in spikes)

    def ground_ahead(self, blocks):
        direction = -1 if self.flipped else 1

        check_rect = pygame.Rect(
            self.rect.centerx + direction * (self.rect.width // 2) + direction * 4,
            self.rect.bottom + 2,
            6,
            6
        )

        return any(
            check_rect.colliderect(block.rect if hasattr(block, 'rect') else block)
            for block in blocks
        )

    # ────────────────────────────────────────────────
    def update(self, player, blocks, spikes):
        if self.knockback:
            self.knock_index += 1
            if self.knock_index > 4:
                self.knock_index = 0
                self.knockback = False
            if self.flipped:
                self.vel_x = 10
            else:
                self.vel_x = -10
        else:
            if not player.invis:
                self.follow_target_entity()
            else:
                if not self.taken:
                    self.vel_x, self.vel_y = 0, 0
                else:
                    self.rect.center = self.hand.rect.center
                
        self.attack_cooldown += 1
        self.dmg_cooldown += 1
        if self.zapped or self.burned:
            self.dmg_cooldown2 += 1
        else:
            self.dmg_cooldown2 = 0

        # Decide jump BEFORE moving
        if self.on_ground and self.jump_cooldown == 0:
            front_x = self.rect.right if self.vel_x > 0 else self.rect.left - 5
            # rectangle in front of feet
            front_rect = pygame.Rect(front_x, self.rect.bottom - 5, 5, 5)
            # rectangle above front to see if space is free
            above_rect = pygame.Rect(front_x, self.rect.top - self.rect.height, self.rect.width, self.rect.height)

            hit_front = any(front_rect.colliderect(block) for block in blocks)
            space_above = any(above_rect.colliderect(block) for block in blocks)

            if hit_front and not space_above:
                self.vel_y = -self.jump_power
                self.jump_cooldown = 15

        if self.rect.colliderect(player.rect) and self.attack_cooldown >= 60 and not player.shield:
            player.hp -= 30 * player.dmg_red
            player.ishurt = True
            if player.invis:
                spellCurrCooldowns['invis'] = 0
            self.die()
            explosions.add(Explosion(self.rect.x, self.rect.y))
            player.invis = False

        if self.rect.colliderect(player.slash_rect) and self.dmg_cooldown >= 10 and spellCurrCooldowns[player.curr_spell] >= 10 and player.attacking and player.curr_spell == 'slash':
            self.hp -= 10
            self.dmg_cooldown = 0
            spellCurrCooldowns[player.curr_spell] = 0
            self.knockback = True
            
        if self.rect.colliderect(player.slash_rect) and self.dmg_cooldown >= 10 and spellCurrCooldowns[player.curr_spell] >= 10 and player.attacking and player.curr_spell == 'burn':
            self.hp -= 8
            self.dmg_cooldown = 0
            spellCurrCooldowns[player.curr_spell] = 0
            self.burned = True
            self.tick = 0
            self.knockback = True

        if self.rect.colliderect(player.rect) and self.dmg_cooldown >= 10 and spellCurrCooldowns[player.curr_spell] >= 10 and player.attacking and player.curr_spell == 'dash':
            self.hp -= 10
            self.dmg_cooldown = 0
            spellCurrCooldowns[player.curr_spell] = 0
            self.knockback = True
            self.dmg_red = 0.5

        if self.rect.colliderect(player.rect) and self.dmg_cooldown >= 10 and spellCurrCooldowns[player.curr_spell] >= 10 and player.attacking and player.curr_spell == 'charge':
            self.hp -= 8
            self.dmg_cooldown = 0
            self.zapped = True
            self.tick = 0
            player.speed *= 1.5
            player.speed_timer += 1
            spellCurrCooldowns[player.curr_spell] = 0
            self.knockback = True
            self.dmg_red = 0.5

        # Horizontal
        if not (self.zapped and self.dmg_cooldown2 >= 15) and not self.frozen:
            self.rect.x += self.vel_x
        self.horizontal_collide(blocks)

        # Gravity
        self.vel_y += self.gravity
        if self.vel_y > 0:
            self.vel_y += self.gravity * (self.fall_multiplier - 1)
        if self.vel_y > self.terminal_velocity:
            self.vel_y = self.terminal_velocity

        if not self.frozen or not self.taken:
            self.rect.y += self.vel_y
            
        self.on_ground = False
        self.vertical_collide(blocks)

        if self.rect.x != player.rect.x or self.rect.y != player.rect.y:
            self.animate()

        if self.target and hasattr(self.target, 'alive'):
            if not self.target.alive():
                self.target = player

        if self.hp <= 0:
            self.die()

        self.ground_ahead(blocks)

        if not self.hand or len(hands) == 0:
            self.taken = False

        if self.taken:
            self.rect.center = self.hand.rect.center
            for block in blocks:
                if self.rect.colliderect(block):
                    self.taken = False
                    self.hand = None
                    spellCurrCooldowns[player.curr_spell] = 0
                    player.attacking = False
                    player.frame_index = 0

    def die(self):
        self.kill()

class BlobKing(Enemy):
    def __init__(self, x, y, speed=1):
        super().__init__(x, y)

        # ── SPRITES ─────────────────────────────────
        self.frames_right = [
            pygame.transform.scale(
                pygame.image.load(asset('king1.png')).convert_alpha(),
                (75, 75)
            ),
            pygame.transform.scale(
                pygame.image.load(asset('king2.png')).convert_alpha(),
                (75, 75)
            )
        ]
        self.frames_left = [
            pygame.transform.flip(frame, True, False)
            for frame in self.frames_right
        ]

        self.zap = [
            pygame.image.load(asset('zapped1.png')).convert_alpha()
        ]

        self.zapped = False
        self.burned = False
        self.frozen = False
        self.poisoned = False
        self.confused = False
        self.tick = 0

        self.rect = self.image.get_rect(topleft=(x, y))

        # ── ANIMATION ────────────────────────────────
        self.frame_index = 0
        self.anim_speed = 0.25
        self.flipped = False

        # ── MOVEMENT ─────────────────────────────────
        self.speed = speed
        self.vel_x = 0
        self.vel_y = 0

        self.jump_power = 14
        self.gravity = 1.6
        self.fall_multiplier = 2.0
        self.terminal_velocity = 22

        self.target = player
        self.follow_distance = 35

        self.knockback = False
        self.knock_index = 0

        self.on_ground = False

        self.taken = False
        self.hand = None

        # ── AI ───────────────────────────────────────
        self.follow_range = 500
        self.jump_cooldown = 0

        self.attack_cooldown = 0
        self.dmg_cooldown = 6
        self.dmg_cooldown2 = 0
        self.hp = 50
        self.max_hp = 50

        self.spawn_timer = 0

    # ────────────────────────────────────────────────
    def follow_target_entity(self):
        target = self.target
        if not target:
            return

        dx = target.rect.centerx - self.rect.centerx

        if abs(dx) < 32:
            self.vel_x = 0
            return

        self.vel_x = self.speed if dx > 0 else -self.speed
        self.flipped = dx < 0

    # ────────────────────────────────────────────────
    def should_jump(self, blocks, spikes):
        if not self.on_ground or self.jump_cooldown > 0:
            return False

        direction = -1 if self.flipped else 1

        front_rect = pygame.Rect(
            self.rect.centerx + direction * (self.rect.width // 2),
            self.rect.bottom - 6,
            6,
            6
        )

        above_rect = pygame.Rect(
            front_rect.x - self.rect.width // 2,
            self.rect.top - self.rect.height,
            self.rect.width,
            self.rect.height
        )

        hit_front = any(front_rect.colliderect(block) for block in blocks)
        space_clear = not any(above_rect.colliderect(block) for block in blocks)

        spike_front = any(front_rect.colliderect(s) for s in spikes)

        return hit_front and space_clear and not spike_front
    # ────────────────────────────────────────────────
    def animate(self):
        if self.vel_x != 0 and self.on_ground:
            self.frame_index += self.anim_speed
            if self.frame_index >= len(self.frames_right):
                self.frame_index = 0
        else:
            self.frame_index = 0

        frames = self.frames_left if self.flipped else self.frames_right
        self.image = frames[int(self.frame_index)]

    # ────────────────────────────────────────────────
    def horizontal_collide(self, blocks):
        for block in blocks:
            if self.rect.colliderect(block):
                if self.vel_x > 0:
                    self.rect.right = block.left
                    self.knockback = False
                elif self.vel_x < 0:
                    self.rect.left = block.right
                    self.knockback = False

    def vertical_collide(self, blocks):
        for block in blocks:
            if self.rect.colliderect(block):
                if self.vel_y > 0:
                    self.rect.bottom = block.top
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0:
                    self.rect.top = block.bottom
                    self.vel_y = 0
                    
    def spike_ahead(self, spikes):
        direction = -1 if self.flipped else 1

        check_rect = pygame.Rect(
            self.rect.centerx + direction * (self.rect.width // 2),
            self.rect.bottom + 1,
            6,
            6
        )

        return any(check_rect.colliderect(spike.rect if hasattr(spike, 'rect') else spike)
                   for spike in spikes)

    def ground_ahead(self, blocks):
        direction = -1 if self.flipped else 1

        check_rect = pygame.Rect(
            self.rect.centerx + direction * (self.rect.width // 2) + direction * 4,
            self.rect.bottom + 2,
            6,
            6
        )

        return any(
            check_rect.colliderect(block.rect if hasattr(block, 'rect') else block)
            for block in blocks
        )

    # ────────────────────────────────────────────────
    def update(self, player, blocks, spikes):
        self.rect.width, self.rect.height = 75, 75
        self.spawn_timer += 1
        if self.spawn_timer >= 180:
            enemies.add(Blob(self.rect.x, self.rect.y))
            self.spawn_timer = 0
        if self.knockback:
            self.knock_index += 1
            if self.knock_index > 4:
                self.knock_index = 0
                self.knockback = False
            if self.flipped:
                self.vel_x = 10
            else:
                self.vel_x = -10
        else:
            if not player.invis:
                self.follow_target_entity()
            else:
                if not self.taken:
                    self.vel_x, self.vel_y = 0, 0
                else:
                    self.rect.center = self.hand.rect.center
                
        self.attack_cooldown += 1
        self.dmg_cooldown += 1
        if self.zapped or self.burned:
            self.dmg_cooldown2 += 1
        else:
            self.dmg_cooldown2 = 0

        # Decide jump BEFORE moving
        if self.on_ground and self.jump_cooldown == 0:
            front_x = self.rect.right if self.vel_x > 0 else self.rect.left - 5
            # rectangle in front of feet
            front_rect = pygame.Rect(front_x, self.rect.bottom - 5, 5, 5)
            # rectangle above front to see if space is free
            above_rect = pygame.Rect(front_x, self.rect.top - self.rect.height, self.rect.width, self.rect.height)

            hit_front = any(front_rect.colliderect(block) for block in blocks)
            space_above = any(above_rect.colliderect(block) for block in blocks)

            if hit_front and not space_above:
                self.vel_y = -self.jump_power
                self.jump_cooldown = 15

        if self.rect.colliderect(player.rect) and self.attack_cooldown >= 60 and not player.shield:
            player.hp -= 10 * player.dmg_red
            player.ishurt = True
            if player.invis:
                spellCurrCooldowns['invis'] = 0
            self.attack_cooldown = 0
            player.invis = False

        if self.rect.colliderect(player.slash_rect) and self.dmg_cooldown >= 10 and spellCurrCooldowns[player.curr_spell] >= 10 and player.attacking and player.curr_spell == 'slash':
            self.hp -= 10
            self.dmg_cooldown = 0
            spellCurrCooldowns[player.curr_spell] = 0
            self.knockback = True
            
        if self.rect.colliderect(player.slash_rect) and self.dmg_cooldown >= 10 and spellCurrCooldowns[player.curr_spell] >= 10 and player.attacking and player.curr_spell == 'burn':
            self.hp -= 8
            self.dmg_cooldown = 0
            spellCurrCooldowns[player.curr_spell] = 0
            self.burned = True
            self.tick = 0
            self.knockback = True

        if self.rect.colliderect(player.rect) and self.dmg_cooldown >= 10 and spellCurrCooldowns[player.curr_spell] >= 10 and player.attacking and player.curr_spell == 'dash':
            self.hp -= 10
            self.dmg_cooldown = 0
            spellCurrCooldowns[player.curr_spell] = 0
            self.knockback = True
            self.dmg_red = 0.5

        if self.rect.colliderect(player.rect) and self.dmg_cooldown >= 10 and spellCurrCooldowns[player.curr_spell] >= 10 and player.attacking and player.curr_spell == 'charge':
            self.hp -= 8
            self.dmg_cooldown = 0
            self.zapped = True
            self.tick = 0
            player.speed *= 1.5
            player.speed_timer += 1
            spellCurrCooldowns[player.curr_spell] = 0
            self.knockback = True
            self.dmg_red = 0.5

        # Horizontal
        if not (self.zapped and self.dmg_cooldown2 >= 15) and not self.frozen:
            self.rect.x += self.vel_x
        self.horizontal_collide(blocks)

        # Gravity
        self.vel_y += self.gravity
        if self.vel_y > 0:
            self.vel_y += self.gravity * (self.fall_multiplier - 1)
        if self.vel_y > self.terminal_velocity:
            self.vel_y = self.terminal_velocity

        if not self.frozen or not self.taken:
            self.rect.y += self.vel_y
            
        self.on_ground = False
        self.vertical_collide(blocks)

        if self.rect.x != player.rect.x or self.rect.y != player.rect.y:
            self.animate()

        if self.target and hasattr(self.target, 'alive'):
            if not self.target.alive():
                self.target = player

        if self.hp <= 0:
            self.die()

        self.ground_ahead(blocks)

        if not self.hand or len(hands) == 0:
            self.taken = False

        if self.taken:
            self.rect.center = self.hand.rect.center
            for block in blocks:
                if self.rect.colliderect(block):
                    self.taken = False
                    self.hand = None
                    spellCurrCooldowns[player.curr_spell] = 0
                    player.attacking = False
                    player.frame_index = 0

    def die(self):
        self.kill()

def render_text_wrapped(text, font, color, max_width):
    words = text.split(' ')
    lines = []
    current_line = ''

    for word in words:
        test_line = current_line + word + ' '
        test_surface = font.render(test_line, True, color)

        if test_surface.get_width() > max_width:
            lines.append(current_line)
            current_line = word + ' '
        else:
            current_line = test_line

    lines.append(current_line)

    surfaces = [font.render(line, True, color) for line in lines]
    return surfaces

class Button:
    def __init__(self, x, y, width, height, text, font_size,
                 bg2_color=(70, 70, 90),
                 hover_color=(100, 100, 140),
                 text_color=(255, 255, 255)):

        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.Font(asset('ByteBounce.ttf'), font_size)
        self.bg2_color = bg2_color
        self.hover_color = hover_color
        self.text_color = text_color

        self.text_surfs = render_text_wrapped(text, self.font, text_color, self.rect.width)
        self.text_rect = self.text_surfs[0].get_rect(center=self.rect.center)

        self.clicked = False
        self.was_pressed = False  # previous frame mouse state

    def draw(self, screen):
        mouse_pos = pygame.mouse.get_pos()
        color = self.hover_color if self.rect.collidepoint(mouse_pos) else self.bg2_color
        pygame.draw.rect(screen, color, self.rect, border_radius=8)

        total_height = sum(s.get_height() for s in self.text_surfs)

        y_offset = self.rect.y + (self.rect.height - total_height) // 2

        for surf in self.text_surfs:
            text_rect = surf.get_rect(center=(self.rect.centerx, y_offset + surf.get_height() // 2))
            screen.blit(surf, text_rect)
            y_offset += surf.get_height()

    def isClicked(self):
        mouse_pressed = pygame.mouse.get_pressed()[0]
        mouse_over = self.rect.collidepoint(pygame.mouse.get_pos())

        # Only trigger on edge: just pressed this frame
        self.clicked = mouse_pressed and mouse_over and not self.was_pressed

        self.was_pressed = mouse_pressed
        return self.clicked

class ImgButton:
    def __init__(self, x, y, img, w=64, h=64, alpha=255):
        if isinstance(img, pygame.Surface):
            self.image = img
        else:
            self.image = pygame.transform.scale(pygame.image.load(img).convert_alpha(), (w, h))
        self.rect = self.image.get_rect(topleft=(x,y))
        self.alpha = alpha
        self.clicked = False

    def draw(self, screen):
        self.image.set_alpha(self.alpha)
        screen.blit(self.image, self.rect)

    def isClicked(self):
        if pygame.mouse.get_pressed()[0] and not self.clicked:
            if self.rect.collidepoint(pygame.mouse.get_pos()):
                self.clicked = True
                return True
        if not pygame.mouse.get_pressed()[0]:
            self.clicked = False
        return False


class Dart(pygame.sprite.Sprite):
    def __init__(self, x, y, x2, y2):
        super().__init__()
        self.frame = pygame.image.load(asset('dart.png'))
        self.image = self.frame
        self.rect = self.image.get_rect(center=(x,y))
        
        self.angle = math.degrees(math.atan2(-(y2-y),x2-x))
        self.angle2 = -math.degrees(math.atan2(y2-y,x2-x))
        self.direction = (pygame.Vector2(x2, y2) - (x, y)).normalize()

        self.speed = 11
        self.has_hit = False
        
        self.pos = (x, y)
        self.start_pos = (x, y)

    def update(self, blocks):
        self.image = pygame.transform.rotate(self.frame, self.angle)
        self.pos += self.direction * self.speed
        self.rect.center = self.pos

        if self.rect.colliderect(player.rect):
            self.kill()
            self.has_hit = True
            player.ishurt = True
            player.hp -= 15
            explosions.add(Explosion(self.rect.centerx, self.rect.centery))
            return

        for block in blocks:
            if self.has_hit:
                break
            if self.rect.colliderect(block):
                explosions.add(Explosion(self.rect.centerx, self.rect.centery))
                spellCurrCooldowns[player.curr_spell] = 0
                self.kill()
                
class Fireball(pygame.sprite.Sprite):
    def __init__(self, x, y, x2, y2):
        super().__init__()
        self.frames = [pygame.image.load(asset('fireball.png')), pygame.image.load(asset('fireball2.png'))]
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=(x,y))
        
        self.angle = math.degrees(math.atan2(-(y2-y),x2-x))
        self.angle2 = -math.degrees(math.atan2(y2-y,x2-x))
        self.direction = (pygame.Vector2(x2, y2) - (x, y)).normalize()
        
        self.frame_index = 0
        self.speed = 30
        self.has_hit = False
        
        self.pos = (x, y)
        self.start_pos = (x, y)

    def update(self, blocks):
        self.frame_index += 1
        if self.frame_index > 1:
            self.frame_index = 0
            
        image = self.frames[self.frame_index]
        self.image = pygame.transform.rotate(image, self.angle)
        self.pos += self.direction * self.speed
        self.rect.center = self.pos

        for e in enemies.copy():
            if self.has_hit:
                break
                
            if self.rect.colliderect(e.rect) and e.dmg_cooldown >= 10 and player.attacking:
                self.kill()
                self.has_hit = True
                spellCurrCooldowns[player.curr_spell] = 0
                player.attacking = False
                player.frame_index = 0
                e.dmg_cooldown = 0
                e.hp -= 8
                e.knockback = True
                explosions.add(Explosion(self.rect.centerx, self.rect.centery))
                return

        for block in blocks:
            if self.has_hit:
                break
            if self.rect.colliderect(block):
                explosions.add(Explosion(self.rect.centerx, self.rect.centery))
                spellCurrCooldowns[player.curr_spell] = 0
                player.attacking = False
                player.frame_index = 0
                self.kill()

        if distance(self.start_pos[0], self.start_pos[1], self.pos[0], self.pos[1]) >= 250:
            explosions.add(Explosion(self.rect.centerx, self.rect.centery))
            spellCurrCooldowns[player.curr_spell] = 0
            player.attacking = False
            player.frame_index = 0
            
            self.kill()

class Zap(pygame.sprite.Sprite):
    def __init__(self, x, y, x2, y2):
        super().__init__()
        self.frames = [pygame.image.load(asset('zap.png')), pygame.image.load(asset('zap2.png'))]
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=(x,y))
        
        self.angle = math.degrees(math.atan2(-(y2-y),x2-x))
        self.angle2 = -math.degrees(math.atan2(y2-y,x2-x))
        self.direction = (pygame.Vector2(x2, y2) - (x, y)).normalize()
        
        self.frame_index = 0
        self.speed = 40
        self.has_hit = False
        
        self.pos = (x, y)
        self.start_pos = (x, y)

    def update(self, blocks):
        self.frame_index += 1
        if self.frame_index > 1:
            self.frame_index = 0
            
        image = self.frames[self.frame_index]
        self.image = pygame.transform.rotate(image, self.angle)
        self.pos += self.direction * self.speed
        self.rect.center = self.pos

        for e in enemies:
            if self.has_hit:
                break
            if self.rect.colliderect(e.rect) and e.dmg_cooldown >= 10 and player.attacking:
                self.kill()
                e.dmg_cooldown = 0
                e.hp -= 6
                e.tick = 0
                e.zapped = True
                spellCurrCooldowns[player.curr_spell] = 0
                player.attacking = False
                player.frame_index = 0
                explosions.add(Explosion(self.rect.centerx, self.rect.centery))
                return

        for block in blocks:
            if self.rect.colliderect(block):
                explosions.add(Explosion(self.rect.centerx, self.rect.centery))
                spellCurrCooldowns[player.curr_spell] = 0
                player.attacking = False
                player.frame_index = 0
                self.kill()

        if distance(self.start_pos[0], self.start_pos[1], self.pos[0], self.pos[1]) >= 250:
            explosions.add(Explosion(self.rect.centerx, self.rect.centery))
            spellCurrCooldowns[player.curr_spell] = 0
            player.attacking = False
            player.frame_index = 0
            self.kill()

class Freeze(pygame.sprite.Sprite):
    def __init__(self, x, y, x2, y2):
        super().__init__()
        self.image = pygame.image.load(asset('freeze1.png'))
        self.rect = self.image.get_rect(center=(x,y))
        
        self.angle = math.degrees(math.atan2(-(y2-y),x2-x))
        self.angle2 = -math.degrees(math.atan2(y2-y,x2-x))
        self.direction = (pygame.Vector2(x2, y2) - (x, y)).normalize()
        
        self.frame_index = 0
        self.speed = 40
        self.has_hit = False
        
        self.pos = (x, y)
        self.start_pos = (x, y)

    def update(self, blocks):
        image = pygame.image.load(asset('freeze1.png'))
        self.image = pygame.transform.rotate(image, self.angle)
        self.pos += self.direction * self.speed
        self.rect.center = self.pos

        for e in enemies:
            if self.has_hit:
                break
            if self.rect.colliderect(e.rect) and e.dmg_cooldown >= 10 and player.attacking:
                explosions.add(Explosion(self.rect.centerx, self.rect.centery))
                self.kill()
                e.dmg_cooldown = 0
                e.hp -= 5
                e.tick = 0
                e.frozen = True
                spellCurrCooldowns[player.curr_spell] = 0
                player.attacking = False
                player.frame_index = 0
                return

        for block in blocks:
            if self.rect.colliderect(block):
                explosions.add(Explosion(self.rect.centerx, self.rect.centery))
                spellCurrCooldowns[player.curr_spell] = 0
                player.attacking = False
                player.frame_index = 0
                self.kill()

        if distance(self.start_pos[0], self.start_pos[1], self.pos[0], self.pos[1]) >= 250:
            explosions.add(Explosion(self.rect.centerx, self.rect.centery))
            spellCurrCooldowns[player.curr_spell] = 0
            player.attacking = False
            player.frame_index = 0
            self.kill()

class Poison(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.frames = [pygame.image.load(asset('bomb1.png')), pygame.image.load(asset('bomb2.png'))]
        self.bombs = [pygame.image.load(asset('gas1.png')), pygame.image.load(asset('gas2.png')), pygame.image.load(asset('gas3.png')), pygame.image.load(asset('gas4.png'))]
        self.image = self.frames[0]
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x, y
        self.start_rect = self.rect.copy()
        
        self.frame_index = 0
        self.timer = 0

    def update(self):
        self.timer += 1
        self.frame_index += 1

        if self.timer <= 20:
            image = self.frames[self.frame_index%2]
            self.image = image
            self.rect = self.start_rect

        if self.timer == 20:
            self.frame_index = 0
            image = self.bombs[self.frame_index]
            self.image = image
            self.rect.x = self.start_rect.x - 80
            self.rect.y = self.start_rect.y - 80
            self.rect.width, self.rect.height = 200, 120


        if self.timer > 20:
            self.frame_index += 1
            if self.frame_index > 3:
                self.kill()
                player.attacking = False
                spellCurrCooldowns[player.curr_spell] = 0
                self.timer = 0
            else:
                image = self.bombs[self.frame_index]
                self.image = image

        for e in enemies:  
            if self.rect.colliderect(e.rect) and e.dmg_cooldown >= 10 and self.timer >= 20:
                e.dmg_cooldown = 0
                e.hp -= 10
                e.knockback = True
                e.poisoned = True
                e.speed *= 0.5
                e.tick = 0
                return

class Hand(pygame.sprite.Sprite):
    def __init__(self, x, y, x2, y2):
        super().__init__()
        self.image = pygame.image.load(asset('hand.png'))
        self.rect = self.image.get_rect(center=(x,y))
        
        self.angle = math.degrees(math.atan2(-(y2-y),x2-x))
        self.angle2 = -math.degrees(math.atan2(y2-y,x2-x))
        self.direction = (pygame.Vector2(x2, y2) - (x, y)).normalize()
        self.image = pygame.transform.rotate(self.image, self.angle)
        
        self.frame_index = 0
        self.speed = 30
        self.has_hit = False
        self.flipped = False
        
        self.pos = (x, y)
        self.start_pos = (x, y)

    def update(self, blocks):
        self.frame_index += 1
        if self.frame_index > 1:
            self.frame_index = 0
            
        self.pos += self.direction * self.speed
        self.rect.center = self.pos

        for e in enemies.copy():
            if self.has_hit:
                break
                
            if self.rect.colliderect(e.rect) and player.attacking:
                self.has_hit = True
                player.frame_index = 0
                self.direction *= -0.5
                self.flipped = True
                selected = None
                for en in enemies:
                    if distance(e.rect.x, e.rect.y, en.rect.x, en.rect.y) < distance(e.rect.x, e.rect.y, e.target.rect.x, e.target.rect.y):
                        selected = en
                        e.hand = self
                        player.attacking = False
                if selected:
                    selected.taken = True
                return

        for block in blocks:
            if self.has_hit:
                break
            if self.rect.colliderect(block) and player.attacking:
                self.has_hit = True
                player.frame_index = 0
                self.direction *= 0
                self.flipped = True
                player.hand = self
                player.taken = True
                return

        if player.curr_spell != 'hand':
            spellCurrCooldowns[player.curr_spell] = 0
            player.attacking = False
            player.frame_index = 0
            self.kill()

        if self.flipped and distance(self.start_pos[0], self.start_pos[1], self.pos[0], self.pos[1]) <= 40:
            spellCurrCooldowns[player.curr_spell] = 0
            player.attacking = False
            player.frame_index = 0
            self.kill()

        if distance(self.start_pos[0], self.start_pos[1], self.pos[0], self.pos[1]) >= 300:
            spellCurrCooldowns[player.curr_spell] = 0
            player.attacking = False
            player.frame_index = 0
            self.kill()

            
class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.frames = [pygame.image.load(asset('explode.png')), pygame.image.load(asset('explode2.png')), pygame.image.load(asset('explode3.png')), pygame.image.load(asset('explode4.png')), pygame.image.load(asset('explode5.png'))]
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center = (x, y))
        self.index = 0
        
    def update(self):
        self.index += 1
        if self.index < 5:
            self.image = self.frames[self.index]
        else:
            self.kill()

class MovingBlock(pygame.sprite.Sprite):
    def __init__(self, x, y, move_x=0, move_y=0, speed=5):
        super().__init__()

        self.image = pygame.image.load(asset('moving_block.png'))
        self.rect = self.image.get_rect(topleft=(x, y))

        self.start_x = x
        self.start_y = y

        self.move_x = move_x
        self.move_y = move_y
        self.speed = speed
        self.direction = 1

        self.dx = 0
        self.dy = 0

    def update(self, player):

        old_x = self.rect.x
        old_y = self.rect.y

        # move platform
        if self.move_x:
            self.rect.x += self.speed * self.direction

        if self.move_y:
            self.rect.y += self.speed * self.direction


        for block in blocks:
            if self.rect.colliderect(block):
                self.direction *= -1

        for lava in lavas:
            if self.rect.colliderect(lava):
                self.direction *= -1

        # calculate movement delta
        self.dx = self.rect.x - old_x
        self.dy = self.rect.y - old_y

        collideBlocks = 0
        for block in blocks:
            if player.rect.colliderect(block):
                collideBlocks += 1

        for lava in lavas:
            if player.rect.colliderect(lava):
                collideBlocks += 1

        # carry player
        if player.platform == self:
            if collideBlocks == 0:
                if self.move_x:
                    player.rect.x += self.dx
                if self.move_y:
                    player.rect.y += self.dy
                player.rect.bottom = self.rect.top

class HorizontalScrollBar:
    def __init__(self, x, y, width, content_width, view_width):
        self.track_rect = pygame.Rect(x, y, width, 30)

        self.content_width = content_width
        self.view_width = view_width

        self.handle_width = max(
            int(width * (view_width / content_width)), 30
        )
        self.handle_rect = pygame.Rect(
            x, y, self.handle_width, 30
        )

        self.dragging = False
        self.scroll_offset = 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.handle_rect.collidepoint(event.pos):
                self.dragging = True
                self.mouse_offset = event.pos[0] - self.handle_rect.x

            # Mouse wheel (optional)
            if event.button == 4:
                self.move(-30)
            if event.button == 5:
                self.move(30)

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False

        if event.type == pygame.MOUSEMOTION and self.dragging:
            self.handle_rect.x = event.pos[0] - self.mouse_offset
            self.clamp()

    def move(self, amount):
        self.handle_rect.x += amount
        self.clamp()

    def clamp(self):
        min_x = self.track_rect.x
        max_x = self.track_rect.right - self.handle_width
        self.handle_rect.x = max(min_x, min(self.handle_rect.x, max_x))

        ratio = (self.handle_rect.x - min_x) / (max_x - min_x)
        self.scroll_offset = int(
            ratio * (self.content_width - self.view_width)
        )

    def draw(self, surface):
        pygame.draw.rect(surface, (60, 60, 60), self.track_rect)
        pygame.draw.rect(surface, (180, 180, 180), self.handle_rect)

class InputBox:
    def __init__(self, x, y, w, h, text='', font_size=30, input_type='normal'):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font_size = font_size
        self.font = pygame.font.Font(asset('ByteBounce.ttf'), self.font_size)

        self.active = False
        self.color_inactive = (80, 80, 80)
        self.color_active = (140, 140, 200)

        self.key_timer = 0
        self.key_delay = 2
        self.type = input_type

    def update(self):
        mouse = pygame.mouse.get_pos()
        mouse_click = pygame.mouse.get_pressed()[0]

        if mouse_click and self.rect.collidepoint(mouse):
            self.active = True

        if not self.active:
            return

        keys = pygame.key.get_pressed()

        self.key_timer += 1
        if self.key_timer < self.key_delay:
            return

        self.key_timer = 0

        if keys[pygame.K_BACKSPACE]:
            self.text = self.text[:-1]

        if keys[pygame.K_SPACE]:
            self.text += ' '

        # letters
        if not self.type == 'int':
            for i in range(26):
                if keys[pygame.K_a + i]:
                    self.text += chr(ord('a') + i)

        for i in range(10):
            if keys[pygame.K_0 + i]:
                self.text += str(i)
                
    def draw(self, screen):
        self.update()
        color = self.color_active if self.active else self.color_inactive
        pygame.draw.rect(screen, color, self.rect, border_radius=6)

        self.font_size = get_font_size(self.rect.width, self.text)
        self.font = pygame.font.Font(asset('ByteBounce.ttf'), self.font_size)
        text_surface = self.font.render(self.text, True, (255,255,255))
        screen.blit(text_surface, (self.rect.x + 5, self.rect.y + 5))

def distance(x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    
    dist = math.sqrt((dx**2) + (dy**2))
    return dist
        
def drawText(text, x, y, font_size, color):
    font = pygame.font.Font(asset('ByteBounce.ttf'), font_size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=(x, y))
    screen.blit(text_surface, text_rect)

def drawText2(text, x, y, font_size, color):
    font = pygame.font.Font(asset('ByteBounce.ttf'), font_size)
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, (x, y))

def get_solid_blocks(tilemap, tileset, tile_size):
    blocks = []
    for row_i, row in enumerate(tilemap):
        for col_i, tile in enumerate(row):
            if tile == 'spiker':
                tile_image = tileset.get(5)
                tile_image = pygame.transform.rotate(tile_image, 270)
                blocks.append(
                    pygame.Rect(
                        col_i * tile_size,
                        row_i * tile_size + (40-tile_image.convert_alpha().get_height()),
                        tile_image.get_width(),
                        tile_image.get_height()
                    )
                )
            if tile == 'spikel':
                tile_image = tileset.get(5)
                tile_image = pygame.transform.rotate(tile_image, 90)
                blocks.append(
                    pygame.Rect(
                        col_i * tile_size + (40-tile_image.convert_alpha().get_width()),
                        row_i * tile_size,
                        tile_image.get_width(),
                        tile_image.get_height()
                    )
                )
                
            if tile == 'spikeb':
                tile_image = tileset.get(5)
                tile_image = pygame.transform.rotate(tile_image, 180)
                blocks.append(
                    pygame.Rect(
                        col_i * tile_size,
                        row_i * tile_size,
                        tile_image.get_width(),
                        tile_image.get_height()
                    )
                )
            if (not tile == 0 and not tile == 6 and not tile == 3 and not tile == 'bg_rocks' and not tile == 'sniper' and not tile == 8 and not tile == 7 and not tile == 9 and not tile == 'lava_block'
                and not tile == 'start' and not tile == 'finish' and not tile == 'spiker' and not tile == 'spikel' and not tile == 'spikeb' and not tile == 4 and not tile == 'h_moving_block' and not tile == 'dirt_bg'
                and not tile == 'spawner'):  # solid
                tile_image = tileset.get(tile)
                blocks.append(
                    pygame.Rect(
                        col_i * tile_size + (40-tile_image.convert_alpha().get_width()),
                        row_i * tile_size + (40-tile_image.convert_alpha().get_height()),
                        tile_image.get_width(),
                        tile_image.get_height()
                    )
                )
    
    return blocks

def get_ladders(tilemap, tileset, tile_size):
    ladders = []
    return ladders

def get_spikes(tilemap, tileset, tile_size):
    spikes = []
    for row_i, row in enumerate(tilemap):
        for col_i, tile in enumerate(row):
            if tile == 5:
                tile_image = tileset.get(tile)
                spikes.append(
                    pygame.Rect(
                        col_i * tile_size + (40-tile_image.convert_alpha().get_width()),
                        row_i * tile_size + (40-tile_image.convert_alpha().get_height()),
                        tile_image.get_width(),
                        tile_image.get_height()
                    )
                )
            if tile == 'spiker':
                tile_image = tileset.get(5)
                tile_image = pygame.transform.rotate(tile_image, 270)
                spikes.append(
                    pygame.Rect(
                        col_i * tile_size,
                        row_i * tile_size + (40-tile_image.convert_alpha().get_height()),
                        tile_image.get_width(),
                        tile_image.get_height()
                    )
                )
            if tile == 'spikel':
                tile_image = tileset.get(5)
                tile_image = pygame.transform.rotate(tile_image, 90)
                spikes.append(
                    pygame.Rect(
                        col_i * tile_size + (40-tile_image.convert_alpha().get_width()),
                        row_i * tile_size,
                        tile_image.get_width(),
                        tile_image.get_height()
                    )
                )
                
            if tile == 'spikeb':
                tile_image = tileset.get(5)
                tile_image = pygame.transform.rotate(tile_image, 180)
                spikes.append(
                    pygame.Rect(
                        col_i * tile_size,
                        row_i * tile_size,
                        tile_image.get_width(),
                        tile_image.get_height()
                    )
                )

    return spikes

def get_lavadata(tilemap, tileset, tile_size):
    lavas = []
    for row_i, row in enumerate(tilemap):
        for col_i, tile in enumerate(row):
            if tile == 4:
                tile_image = lava_imgs[0]
                lavas.append(
                    pygame.Rect(
                        col_i * tile_size + (40-tile_image.convert_alpha().get_width()),
                        row_i * tile_size + 30,
                        tile_image.get_width(),
                        tile_image.get_height()
                    )
                )
            if tile == 'lava_block':
                tile_image = tileset.get(tile)
                lavas.append(
                    pygame.Rect(
                        col_i * tile_size + (40-tile_image.convert_alpha().get_width()),
                        row_i * tile_size + (40-tile_image.convert_alpha().get_height()),
                        tile_image.get_width(),
                        tile_image.get_height()
                    )
                )

    return lavas

def get_spikedata(spike_data):
    spikes = []

    for x, y, w, h in spike_data:
        spike_rect = pygame.Rect(x, y, w, h)
        spikes.append(spike_rect)

    return spikes


def rotate_around_pivot(image, rect, pivot, angle):
    # Rotate image
    rotated_image = pygame.transform.rotate(image, angle)

    # Vector from pivot to image center
    offset = pygame.math.Vector2(rect.center) - pivot

    # Rotate offset
    offset = offset.rotate(angle)

    # New center position
    rotated_rect = rotated_image.get_rect(center=pivot + offset)

    return rotated_image, rotated_rect


def get_end_point(start, target, distance=1000):
    direction = pygame.math.Vector2(target) - start
    if direction.length() == 0:
        return start
    return start + direction.normalize() * distance

def health_color(current, maximum):
    ratio = max(0, min(1, current / maximum))

    red   = int(255 * (1 - ratio))
    green = int(255 * ratio)
    blue  = 0

    return (red, green, blue)


torch1 = pygame.image.load(asset('torch1.png'))
torch2 = pygame.image.load(asset('torch2.png'))
torches = [torch1, torch2]
lava_imgs = [pygame.image.load(asset('lava1.png')), pygame.image.load(asset('lava2.png'))]
title = pygame.image.load(asset('title.png'))
t_index = 0

s = 'start'
f = 'finish'
a = 'spikel'
b = 'spikeb'
r = 'spiker'
n = 'sniper'
k = 'lava_block'
u = 'rocks'
t = 'top_rocks'
m = 'h_moving_block'
v = 'bg_rocks'
c = 'box'
g = 'grass'
d = 'dirt'
z = 'dirt_bg'
p = 'spawner'

def draw_tilemap(surface, tilemap, tileset, tile_size, offset_x=0, offset_y=0, zoom=1):
    global enemiesDrawn, movingBlocksDrawn, t_index

    t_index += 0.5

    for row_index, row in enumerate(tilemap):
        for col_index, tile_id in enumerate(row):
            
            x = col_index * tile_size*zoom
            y = row_index * tile_size*zoom
            
            if tileset == mapTiles:
                if tile_id is None or tile_id == s or tile_id == f or tile_id == 'spawner':
                    continue

                # enemies
                if tile_id == 6:
                    if not enemiesDrawn:
                        enemies.add(Blob(x, y))
                    continue

                if tile_id == 8:
                    if not enemiesDrawn:
                        enemies.add(Ghost(x, y))
                    continue

                if tile_id == n:
                    if not enemiesDrawn:
                        enemies.add(Sniper(x, y))
                    continue

                # torches
                if tile_id == 3:
                    img = torches[int(t_index) % 2]
                    surface.blit(img, (
                        x + (40 - img.get_width()) - offset_x,
                        y + (40 - img.get_height()) - offset_y
                    ))
                    continue

                # lava
                if tile_id == 4:
                    img = lava_imgs[int(t_index) % 2]
                    surface.blit(img, (
                        x + (40 - img.get_width()) - offset_x,
                        y + (40 - img.get_height()) - offset_y
                    ))
                    continue

                # rotated tiles
                if tile_id == a:
                    tile_image = pygame.transform.rotate(tileset.get(5), 90)
                    surface.blit(tile_image, (
                        x + (40 - tile_image.get_width()) - offset_x,
                        y - offset_y
                    ))
                    continue

                if tile_id == b:
                    tile_image = pygame.transform.rotate(tileset.get(5), 180)
                    surface.blit(tile_image, (
                        x - offset_x,
                        y - offset_y
                    ))
                    continue

                if tile_id == r:
                    tile_image = pygame.transform.rotate(tileset.get(5), 270)
                    surface.blit(tile_image, (
                        x - offset_x,
                        y + (40 - tile_image.get_height()) - offset_y
                    ))
                    continue

                if tile_id == 'h_moving_block':
                    if not movingBlocksDrawn:
                        movingBlocks.add(MovingBlock(x, y, move_x=400))
                    continue

                # moving platforms
                if tile_id == 9:
                    if not movingBlocksDrawn:
                        movingBlocks.add(MovingBlock(x, y, move_y=400))
                    continue

                if tile_id == 'bg_rocks':
                    tile_image = mapTilesEditor['bg_rocks']
                    surface.blit(tile_image, (
                        x - offset_x,
                        y - offset_y
                    ))
                    continue


                # normal tiles
                tile_image = tileset.get(tile_id)
                if tile_image:
                    surface.blit(tile_image, (
                        x + (40 - tile_image.get_width()) - offset_x,
                        y + (40 - tile_image.get_height()) - offset_y
                    ))
            if tileset == mapTilesEditor:
                world_x = col_index * tile_size
                world_y = row_index * tile_size

                screen_x = (world_x - offset_x) * zoom
                screen_y = (world_y - offset_y) * zoom

                if tile_id == 0:
                    continue

                # torch
                if tile_id == 3:
                    img = torches[int(t_index) % 2]
                    img = pygame.transform.scale(img, (img.get_width()*zoom, img.get_height()*zoom))
                    surface.blit(img, (
                        screen_x + (tile_size*zoom - img.get_width()),
                        screen_y + (tile_size*zoom - img.get_height())
                    ))
                    continue

                # lava
                if tile_id == 4:
                    img = lava_imgs[int(t_index) % 2]
                    img = pygame.transform.scale(img, (img.get_width()*zoom, img.get_height()*zoom))
                    surface.blit(img, (
                        screen_x + (tile_size*zoom - img.get_width()),
                        screen_y + (tile_size*zoom - img.get_height())
                    ))
                    continue

                # rotated tiles
                if tile_id == a:
                    tile_image = pygame.transform.rotate(tileset.get(5), 90)
                    tile_image = pygame.transform.scale(tile_image, (tile_image.get_width()*zoom, tile_image.get_height()*zoom))
                    surface.blit(tile_image, (
                        screen_x + (tile_size*zoom - tile_image.get_width()),
                        screen_y
                    ))
                    continue

                if tile_id == b:
                    tile_image = pygame.transform.rotate(tileset.get(5), 180)
                    tile_image = pygame.transform.scale(tile_image, (tile_image.get_width()*zoom, tile_image.get_height()*zoom))
                    surface.blit(tile_image, (
                        screen_x,
                        screen_y
                    ))
                    continue

                if tile_id == r:
                    tile_image = pygame.transform.rotate(tileset.get(5), 270)
                    tile_image = pygame.transform.scale(tile_image, (tile_image.get_width()*zoom, tile_image.get_height()*zoom))
                    surface.blit(tile_image, (
                        screen_x,
                        screen_y + (tile_size*zoom - tile_image.get_height())
                    ))
                    continue

                if tile_id == 9:
                    tile_image = tileset.get(9)
                    if tile_image:
                        tile_image = pygame.transform.scale(tile_image, (tile_image.get_width()*zoom, tile_image.get_height()*zoom))
                        surface.blit(tile_image, (
                            screen_x,
                            screen_y
                        ))
                    continue

                if tile_id == 'h_moving_block':
                    tile_image = tileset.get(9)
                    if tile_image:
                        tile_image = pygame.transform.scale(tile_image, (tile_image.get_width()*zoom, tile_image.get_height()*zoom))
                        surface.blit(tile_image, (
                            screen_x,
                            screen_y
                        ))
                    continue


                # normal tiles
                tile_image = tileset.get(tile_id)
                if tile_image:
                    tile_image = pygame.transform.scale(tile_image, (tile_image.get_width()*zoom, tile_image.get_height()*zoom))
                    surface.blit(tile_image, (
                        screen_x + (tile_size*zoom - tile_image.get_width()),
                        screen_y + (tile_size*zoom - tile_image.get_height())
                    ))

def get_font_size(button_width, text):
    return min(40, int(button_width / max(len(text), 1) * 1.8))

class Level:
    def __init__(self, tilemap3, name, bg, tilemap1=None, tilemap2=None, num=0):
        self.tilemap1 = tilemap1
        self.tilemap2 = tilemap2
        self.tilemap3 = tilemap3
        self.name = name
        self.num = num
        self.bg_path = bg
        self.width = len(self.tilemap3[0])*40
        self.height = len(self.tilemap3)*40
        self.start = None
        self.finish = None
        self.find_start()

    def find_start(self):
        if self.tilemap1:
            for row_index, row in enumerate(self.tilemap1):
                for col_index, tile_id in enumerate(row):
                    if tile_id is None:
                        continue
                    if tile_id == 'start':
                        x = col_index * 40
                        y = row_index * 40
                        start = (x, y-10)
                        self.start = start
                    if tile_id == 'finish':
                        x = col_index * 40
                        y = row_index * 40
                        finish = (x, y)
                        self.finish = finish
        if self.tilemap2:
            for row_index, row in enumerate(self.tilemap2):
                for col_index, tile_id in enumerate(row):
                    if tile_id is None:
                        continue
                    if tile_id == 'start':
                        x = col_index * 40
                        y = row_index * 40
                        start = (x, y-10)
                        self.start = start
                    if tile_id == 'finish':
                        x = col_index * 40
                        y = row_index * 40
                        finish = (x, y)
                        self.finish = finish
        for row_index, row in enumerate(self.tilemap3):
            for col_index, tile_id in enumerate(row):
                if tile_id is None:
                    continue
                if tile_id == 'start':
                    x = col_index * 40
                    y = row_index * 40
                    start = (x, y-10)
                    self.start = start
                if tile_id == 'finish':
                    x = col_index * 40
                    y = row_index * 40
                    finish = (x, y)
                    self.finish = finish

wave_on = False
curr_wave = 1
wave_timer = 180

class Spawner:
    def __init__(self, x, y, delay=200, max_enemies=5):
        self.x = x
        self.y = y

        self.delay = delay
        self.timer = 180

        self.max_enemies = max_enemies
        self.active = True

    def update(self):
        global curr_wave, wave_timer
        
        if not self.active:
            return

        # 🚫 Limit enemies globally
        if len(enemies) >= 10:
            return

        # 🚫 Limit enemies from THIS spawner
        nearby = self.count_nearby_enemies()

        if nearby >= self.max_enemies:
            return

        # 👾 Spawn
        if wave_timer <= 0:
            wave_on = True
            enemies_defeated = False

        if wave_timer <= 0 and len(enemies) > 0:
            player.hp = 0

    def spawn(self, enemy_spawn=None):
        # ❗ Optional: don’t spawn if player is too close
        dist = pygame.Vector2(self.x, self.y).distance_to(player.rect.center)

        # 🎲 Slight randomness so it's not robotic
        x = self.x
        y = self.y

        enemy_list = ['blob']
        if curr_wave > 3:
            enemy_list.append('ghost')
        if curr_wave > 5:
            enemy_list.append('sniper')
        if curr_wave > 8:
            enemy_list.append('bomb')
            

        # 🎲 Choose enemy type
        enemy_type = random.choice(enemy_list)

        if enemy_spawn:
            if enemy_spawn == 'blob':
                enemy = Blob(x, y)
            elif enemy_spawn == 'ghost':
                enemy = Ghost(x, y)
            elif enemy_spawn == 'sniper':
                enemy = Sniper(x, y)
            elif enemy_spawn == 'bomb':
                enemy = Bomb(x, y)
            elif enemy_spawn == 'blob_king':
                enemy = BlobKing(x, y)

        else:
            if enemy_type == 'blob':
                enemy = Blob(x, y)
            elif enemy_type == 'ghost':
                enemy = Ghost(x, y)
            elif enemy_type == 'sniper':
                enemy = Sniper(x, y)
            elif enemy_type == 'bomb':
                enemy = Bomb(x, y)

        enemies.add(enemy)
        wave_on = True

    def count_nearby_enemies(self):
        count = 0
        for e in enemies:
            if abs(e.rect.x - self.x) < 200 and abs(e.rect.y - self.y) < 200:
                count += 1
        return count


class SurvLevel:
    def __init__(self, tilemap, name, bg, num=0):
        self.tilemap = tilemap
        self.name = name
        self.num = num
        self.bg_path = bg
        self.width = len(self.tilemap[0])*40
        self.height = len(self.tilemap)*40
        self.start = None
        self.finish = None
        self.spawners = []
        self.find_start()
        self.find_spawners()

    def find_start(self):
        for row_index, row in enumerate(self.tilemap):
            for col_index, tile_id in enumerate(row):
                if tile_id is None:
                    continue
                if tile_id == 'start':
                    x = col_index * 40
                    y = row_index * 40
                    start = (x, y-10)
                    self.start = start
                if tile_id == 'finish':
                    x = col_index * 40
                    y = row_index * 40
                    finish = (x, y)
                    self.finish = finish

    def find_spawners(self):
        self.spawners = []
        for row_index, row in enumerate(self.tilemap):
            for col_index, tile_id in enumerate(row):
                if tile_id is None:
                    continue
                if tile_id == 'spawner':
                    x = col_index * 40
                    y = row_index * 40
                    spawner = Spawner(x, y)
                    self.spawners.append(spawner)

mapTiles = {
    1: pygame.image.load(asset('stone_bricks.png')),
    2: pygame.image.load(asset('b.png')),
    5: pygame.image.load(asset('spike.png')),
    7: pygame.image.load(asset('chain.png')),
    'lava_block': pygame.image.load(asset('lava_block.png')),
    'rocks': pygame.image.load(asset('rocks.png')),
    'box': pygame.image.load(asset('box.png')),
    'grass': pygame.image.load(asset('grass.png')),
    'dirt': pygame.image.load(asset('dirt.png')),
    'dirt_bg': pygame.image.load(asset('bg_dirt.png')),
    'top_rocks': pygame.image.load(asset('top_rocks.png'))
}

mapTilesEditor = {
    1: pygame.image.load(asset('stone_bricks.png')),
    2: pygame.image.load(asset('b.png')),
    5: pygame.image.load(asset('spike.png')),
    6: pygame.image.load(asset('blob1.png')),
    7: pygame.image.load(asset('chain.png')),
    9: pygame.image.load(asset('moving_block.png')),
    'lava_block': pygame.image.load(asset('lava_block.png')),
    'rocks': pygame.image.load(asset('rocks.png')),
    'top_rocks': pygame.image.load(asset('top_rocks.png')),
    'finish': pygame.image.load(asset('door.png')),
    'h_moving_block': pygame.image.load(asset('moving_block.png')),
    'start': pygame.image.load(asset('start.png')),
    'sniper': pygame.image.load(asset('sniper.png')),
    'box': pygame.image.load(asset('box.png')),
    'bg_rocks': pygame.image.load(asset('bg_rocks.png'))
}

mapImages = {
    1: pygame.image.load(asset('stone_bricks.png')),
    2: pygame.image.load(asset('b.png')),
    3: pygame.image.load(asset('torch1.png')),
    4: pygame.image.load(asset('lava1.png')),
    6: pygame.image.load(asset('blob1.png')),
    7: pygame.image.load(asset('chain.png')),
    8: pygame.image.load(asset('ghost_tr.png')),
    9: pygame.image.load(asset('moving_block.png')),
    'lava_block': pygame.image.load(asset('lava_block.png')),
    'rocks': pygame.image.load(asset('rocks.png')),
    'top_rocks': pygame.image.load(asset('top_rocks.png')),
    'finish': pygame.image.load(asset('door.png')),
    'h_moving_block': pygame.image.load(asset('moving_block.png')),
    'sniper': pygame.image.load(asset('sniper.png')),
    'start': pygame.image.load(asset('start.png')),
    5: pygame.image.load(asset('spike.png')),
    'spiker': pygame.transform.rotate(pygame.image.load(asset('spike.png')), 270),
    'spikeb': pygame.transform.rotate(pygame.image.load(asset('spike.png')), 180),
    'spikel': pygame.transform.rotate(pygame.image.load(asset('spike.png')), 90),
    'bg_rocks': pygame.image.load(asset('bg_rocks.png')),
    'box': pygame.image.load(asset('box.png'))
}


door_img1 = pygame.image.load(asset('door.png'))
door_img2 = pygame.image.load(asset('enter_door.png'))
door_img = door_img1

map1 = [
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,1,1,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1],
    [0,0,0,0,0,0,0,0,0,0,0,0,3,0,0,0,0,0,1,1,1],
    [0,0,3,0,0,0,0,3,0,0,0,0,0,0,0,6,0,f,1,1,1],
    [0,0,0,0,0,0,0,0,0,0,6,0,0,2,2,2,2,2,1,1,1],
    [0,0,s,0,0,0,0,0,2,2,2,2,2,1,1,1,1,1,1,1,1],
    [2,2,2,2,2,2,2,2,1,1,1,1,1,1,1,1,1,1,1,1,1]
]

map2 = [
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [0,0,0,0,0,0,7,0,0,7,0,0,7,0,7,8,0,f,1,1,1],
    [0,0,0,0,0,0,7,0,0,7,0,0,7,0,7,0,0,2,1,1,1],
    [0,0,3,0,0,0,7,3,0,7,0,3,7,0,7,3,0,0,1,1,1],
    [0,0,0,0,0,0,2,0,0,2,0,0,7,0,2,2,0,0,1,1,1],
    [0,0,0,2,0,0,1,0,6,1,0,2,2,0,1,6,0,0,1,1,1],
    [0,0,s,1,0,0,1,2,2,1,0,0,0,0,1,2,2,2,1,1,1],
    [2,2,2,1,5,5,5,5,5,5,5,5,5,5,5,5,5,5,1,1,1],
    [1,1,1,1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1,1,1]
]

map3 = [
    [1,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,f,8,8,0,0,0,0,7,0,0,0,7,0,0,7,0,7,0,1,1],
    [1,2,2,2,2,0,0,0,7,0,0,0,7,0,0,7,0,7,0,1,1],
    [1,0,0,0,0,0,0,0,7,0,3,0,7,0,0,7,3,7,0,1,1],
    [1,n,0,3,0,9,0,0,7,0,0,0,7,0,0,7,0,7,0,1,1],
    [1,2,0,0,0,0,2,2,2,0,0,0,7,0,0,7,0,7,0,1,1],
    [1,0,0,0,0,0,0,0,0,0,0,2,2,0,0,2,2,2,0,1,1],
    [1,5,5,5,5,5,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1],
    [1,1,1,1,1,1,r,0,0,5,5,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,b,0,0,a,1,1,r,0,0,0,0,0,0,0,n,1],
    [0,0,3,0,0,0,0,0,a,1,1,r,0,0,0,3,0,0,9,2,1],
    [0,0,0,0,0,2,0,0,0,b,b,0,0,2,0,0,0,2,2,1,1],
    [0,0,s,0,a,1,0,0,0,0,0,0,0,1,0,0,0,1,1,1,1],
    [2,2,2,2,2,1,2,2,2,2,2,2,2,1,4,4,4,1,1,1,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,k,k,k,1,1,1,1]
]

blank = [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
]

survival_map1 = [
    [0,0,0,0,0,0,1,1,1,1,0,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,1,1,1,1,0,7,0,0,0,7,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,7,0,7,0,0,7,0,0,0,7,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,7,0,7,0,0,7,0,p,0,7,0,0,0,0,p,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,7,0,7,0,0,c,c,c,c,c,0,0,0,0,g,g,g,g,g,0,0,0,0],
    [0,0,0,0,0,0,7,p,7,0,0,0,0,0,0,0,0,0,0,0,0,d,z,0,0,0,0,0,0],
    [0,0,0,0,0,0,c,c,c,0,0,0,0,0,0,0,0,0,0,0,0,d,z,0,0,0,0,g,g],
    [p,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,9,0,0,0,p,d,z,0,0,0,0,0,d],
    [g,g,g,g,0,0,0,0,0,0,0,0,0,0,0,0,g,g,g,g,g,d,g,g,0,0,0,0,d],
    [d,d,d,0,0,0,0,0,0,s,p,0,0,0,0,0,0,0,d,d,d,z,0,0,0,0,g,g,d],
    [z,z,0,0,0,0,g,g,g,g,g,g,g,g,0,0,0,0,0,z,z,z,0,0,0,0,z,z,d],
    [z,z,0,0,0,0,z,d,d,d,d,d,d,z,0,0,0,p,0,z,z,z,0,0,0,g,z,z,d],
    [g,g,g,g,p,0,z,z,z,z,z,z,z,z,z,0,p,g,g,g,g,z,0,0,0,d,g,g,g],
    [d,d,d,d,g,z,z,z,z,z,z,z,z,z,z,z,g,d,d,d,d,g,g,g,g,d,d,d,d],
    [d,d,d,d,d,g,z,z,z,z,z,z,z,z,z,g,d,d,d,d,d,d,d,d,d,d,d,d,d],
    [d,d,d,d,d,d,g,g,g,g,g,g,g,g,g,d,d,d,d,d,d,d,d,d,d,d,d,d,d]
]

survival_map2 = [
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [0,0,0,7,0,0,7,0,7,0,0,0,0,7,0,7,0,0,0,0,7,0,7,0,0,7,0,0,0],
    [0,0,0,7,0,0,7,0,7,0,0,0,0,7,0,7,0,0,0,0,7,0,7,0,0,7,0,0,0],
    [0,0,0,7,0,0,7,3,7,0,0,0,0,7,0,7,0,0,0,0,7,3,7,0,0,7,0,0,0],
    [0,3,0,7,0,0,7,p,7,0,0,0,0,7,3,7,0,0,0,0,7,p,7,0,0,7,0,3,0],
    [0,0,0,7,0,0,2,2,2,0,0,0,0,7,0,7,0,0,0,m,2,2,2,0,0,7,0,0,0],
    [0,0,p,7,0,0,7,0,7,0,0,0,0,7,0,7,0,0,0,0,7,0,7,0,0,7,p,0,0],
    [2,2,2,2,0,0,7,3,7,0,0,0,0,2,2,2,0,0,0,0,7,3,7,0,0,2,2,2,2],
    [0,0,0,0,0,0,7,0,7,0,0,0,0,7,0,7,0,0,0,0,7,0,7,0,0,0,0,0,0],
    [0,3,0,0,0,0,2,2,2,m,0,0,0,7,3,7,0,0,0,0,2,2,2,0,0,0,0,3,0],
    [0,0,p,0,0,0,0,0,0,0,0,0,0,7,0,7,0,0,0,0,0,0,0,0,0,p,0,0,0],
    [2,2,2,2,2,0,0,0,3,0,0,0,0,2,2,2,0,0,0,0,3,0,0,0,2,2,2,2,2],
    [1,1,1,1,0,0,0,p,0,0,0,0,0,0,0,0,0,0,0,0,p,0,0,0,0,1,1,1,1],
    [1,1,1,0,0,2,2,2,2,2,0,0,0,0,3,0,0,0,0,2,2,2,2,2,0,0,1,1,1],
    [1,1,1,0,0,0,1,1,1,0,0,0,0,p,s,0,0,0,0,0,1,1,1,0,0,0,1,1,1],
    [1,1,1,5,5,5,1,1,1,5,5,5,2,2,2,2,2,5,5,5,1,1,1,5,5,5,1,1,1]
]

survival_map3 = [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
]

sky = pygame.image.load(asset('sky.png'))
dungeon = pygame.image.load(asset('dungeon.png'))
rocks = pygame.image.load(asset('rocks_bg.png'))

sky_path = asset('sky.png')
dungeon_path = asset('dungeon.png')
rocks_tag = asset('rocks_bg.png')

maplevels = [Level(map1, '1', dungeon_path, num=1), Level(map2, '2', dungeon_path, num=2), Level(map3, '3', dungeon_path, num=3)]

survival_lvls = [SurvLevel(survival_map1, '1', sky_path), SurvLevel(survival_map2, '2', dungeon_path)]

curr_level = maplevels[0]

blocks = get_solid_blocks(curr_level.tilemap3, mapTiles, 40)
spikes = get_spikedata(get_spikes(curr_level.tilemap3, mapTiles, 40))
lavas = get_lavadata(curr_level.tilemap3, mapTiles, 40)
ladders = get_ladders(curr_level.tilemap3, mapTiles, 40)

enemies = pygame.sprite.Group()
fireballs = pygame.sprite.Group()
zaps = pygame.sprite.Group()
freezes = pygame.sprite.Group()
poisons = pygame.sprite.Group()
hands = pygame.sprite.Group()
darts = pygame.sprite.Group()
explosions = pygame.sprite.Group()
movingBlocks = pygame.sprite.Group()
enemiesDrawn = False
movingBlocksDrawn = False

camera = Camera(720, 360)

WORLD_WIDTH = len(map1[0]) * 40
WORLD_HEIGHT = len(map1) * 40

survival_high_score = 1

player = Player(100, 200)
players = pygame.sprite.Group(player)
paused_clicked = False

player_levels = []

paused = True
img = pygame.image.load(asset('square.png'))
avgX, avgY = 0, 0

settings_img = pygame.image.load(asset('settings.png'))

testing_level = False

playerSpells = ['slash', 'fireball', 'dash', 'shield', 'zap', 'heal', 'burn', 'freeze', 'poison', 'charge', 'ghost']
tiers = {'slash': 1,
         'fireball': 1,
         'dash': 1,
         'shield': 1,
         'zap': 2,
         'heal': 2,
         'burn': 2,
         'freeze': 3,
         'poison': 3,
         'charge': 3,
         'teleport': 3,
         'ghost': 4,}

spellCooldowns = {'slash': 15,
         'fireball': 30,
         'dash': 30,
         'shield': 40,
         'zap': 30,
         'heal': 60,
         'burn': 10,
         'freeze': 40,
         'poison': 65,
         'charge': 40,
         'ghost': 60}
resetCooldowns = {'slash': 0,
         'fireball': 0,
         'dash': 0,
         'shield': 0,
         'zap': 0,
         'heal': 0,
         'burn': 0,
         'freeze': 0,
         'poison': 0,
         'charge': 0,
         'ghost': 0}

spellCurrCooldowns = {'slash': 15,
         'fireball': 30,
         'dash': 30,
         'shield': 40,
         'zap': 30,
         'heal': 60,
         'burn': 10,
         'freeze': 40,
         'poison': 65,
         'charge': 40,
         'ghost': 60}

scrollbar = HorizontalScrollBar(
    x=0,
    y=330,
    width=720,
    content_width=2000,
    view_width=720
)

selected = pygame.image.load(asset('select.png'))
coin = pygame.image.load(asset('coins.png'))

silverOpen = False
goldOpen = False
diamondOpen = False

silverOpt = ['10 XP', 1, 2]
silverChances = [80, 15, 5]

goldOpt = ['25 XP', 1, 2, 3]
goldChances = [60, 15, 20, 5]

diamondOpt = ['50 XP', 2, 3, 4]
diamondChances = [60, 15, 20, 5]

beamX, beamY = 0, 0

laser_squares = []

level_selec = None

count = 0
curr_wave = 1

player.spells = playerSpells

buttons_created = False
selected_block = 'eraser'
erase_img = pygame.image.load(asset('eraser.png'))
undo_img = pygame.image.load(asset('undo.png'))

prev_tilemaps = []

def save():
    data = {
        'player_levels': player_levels,
        'volume': volume,
        'player_spells': player.spells,
        'player_coins': player.coins,
        'player_rotation': player.rotation,
        'curr_spell_unlock': player.curr_unlock,
        'level': player.lvl,
        'xp': player.xp,
        'shc': survival_high_score
        
    }

    with open('save.pkl', 'wb') as sve:
        pickle.dump(data, sve)


def load():
    global player_levels, volume, survival_high_score

    try:
        with open('save.pkl', 'rb') as sve:
            data = pickle.load(sve)
            player_levels = data['player_levels']
            volume = data['volume']
            player.spells = data['player_spells']
            player.coins = data['player_coins']
            player.rotation = data['player_rotation']
            player.curr_unlock = data['curr_spell_unlock']
            player.lvl = data['level']
            player.xp = data['xp']
            survival_high_score = data['shc']
            pygame.mixer.music.set_volume(volume/100)
    except Exception as e:
        print('Save load failed:', e)
        player_levels = []
        save()

load()

while running:

    fps = clock.get_fps()

    if audio:
        pygame.mixer.music.play(-1)

    if menu:
        screen.blit(dungeon, (0,0))
        audio = False
        
        screen.blit(title, (140, 30))

        play_button = Button(150, 150, 100, 60, 'Play', 30)
        play_button.draw(screen)

        coll_button = Button(270, 150, 150, 60, 'Collection', 30)
        coll_button.draw(screen)

        shop_button = Button(450, 150, 100, 60, 'Shop', 30)
        shop_button.draw(screen)

        spells_button = Button(400, 220, 150, 60, 'Spells', 30)
        spells_button.draw(screen)

        create_button = Button(200, 220, 150, 60, 'Create', 30)
        create_button.draw(screen)

        settings = ImgButton(WIDTH-60, 100, settings_img)
        settings.draw(screen)

        if play_button.isClicked():
            menu = False
            gamemodes = True
        if coll_button.isClicked():
            menu = False
            collection = True
            player.selected_spell = None
        if shop_button.isClicked():
            menu = False
            shop = True
        if spells_button.isClicked():
            menu = False
            spells = True
        if create_button.isClicked():
            menu = False
            editor = True
        if settings.isClicked():
            menu = False
            settings_tab = True
            prev_tab = menu
            volume_input = InputBox(200, 160, 50, 50, text=str(int(volume)), input_type = 'int')

    if settings_tab:
        pygame.draw.rect(screen, (42, 146, 238), (50, 50, 620, 260))
        drawText('Settings', WIDTH//2, 80, 60, (255, 255, 255))

        drawText2('Controls: WASD and Arrow Keys', 100, 110, 30, (255, 255, 255))
        drawText2('Volume:', 100, 170, 30, (255, 255, 255))

        volume_input.draw(screen)
        if len(volume_input.text) == 0:
            volume = 0
        elif int(volume_input.text) > 100:
            volume_input.text = '100'
            volume = 100
        else:
            volume = int(volume_input.text)
        pygame.mixer.music.set_volume(volume/100)
        
        back = Button(WIDTH-110, 60, 50, 50, '<', 30)
        back.draw(screen)
        if back.isClicked():
            settings_tab = False
            prev_tab = True

    if gamemodes:
        screen.blit(dungeon, (0,0))
        back = Button(10, 10, 50, 50, '<', 30)
        back.draw(screen)
        drawText('Choose a Gamemode', WIDTH//2, 50, 60, (255, 255, 255))
        
        main_button = Button(400, 220, 100, 100, 'Main Levels', 30)
        main_button.draw(screen)

        surv_button = Button(200, 220, 150, 60, 'Survival', 30)
        surv_button.draw(screen)

        drawText('Highscore: '+str(survival_high_score), 275, 180, 30, (255, 255, 255))

        if main_button.isClicked():
            gamemodes = False
            levels = True

        if surv_button.isClicked():
            gamemodes = False
            survival = True
            curr_wave = 1
            pygame.mixer.music.load(survival_music)
            pygame.mixer.music.play(-1)
            curr_level = random.choice(survival_lvls)
            curr_level.spawners = []
            curr_level.find_spawners()
            if curr_level.bg_path == sky_path:
                background = sky
            if curr_level.bg_path == dungeon_path:
                background = dungeon
            audio = True
            paused = False
            curr_wave = 1
            wave_timer = 180
            wave_on = False
            player.curr_spell = player.rotation[0]
            player.reset()
            player.rect.x, player.rect.y = curr_level.start
            blocks = get_solid_blocks(curr_level.tilemap, mapTiles, 40)
            spikes = get_spikedata(get_spikes(curr_level.tilemap, mapTiles, 40))
            lavas = get_lavadata(curr_level.tilemap, mapTiles, 40)
            ladders = get_ladders(curr_level.tilemap, mapTiles, 40)
            enemies_defeated = False
        
        if back.isClicked():
            gamemodes = False
            menu = True

    if editor:
        audio = False
        screen.blit(dungeon, (0,0))
        clear = Button(10, 10, 80, 50, 'Clear Levels', get_font_size(100, 'Clear Levels'))
        clear.draw(screen)
        back = Button(WIDTH-60, 10, 50, 50, '<', 30)
        back.draw(screen)
        drawText('Your Levels', WIDTH//2, 50, 60, (255, 255, 255))
        if not buttons_created:
            buttons = []
            for i in range(len(player_levels)+1):
                col = i % 6
                row = i // 6
                
                x = 10 + col * 115
                y = 120 + row * 115

                if i == 0:
                    buttons.append(Button(x, y, 100, 100, '+', 70))
                else:
                    lvl = player_levels[i-1]
                    buttons.append(
                        Button(x, y, 100, 100, lvl.name, get_font_size(100, lvl.name))
                    )
            buttons_created = True
        for button in buttons:
            button.draw(screen)
        for i in range(len(buttons)):
            if i != 0 and buttons[i].isClicked():
                editor = False
                create = True
                level_selec = i-1
                buttons_created = False
                name_input = InputBox(160, 10, 400, 70, text=player_levels[level_selec].name)
                delete_level = False
        if buttons[0].isClicked():
            col = (len(player_levels)+1) % 6
            row = (len(player_levels)+1) // 6
            x = 10 + col * 115
            y = 120 + row * 115
            player_levels.append(Level([[0 for i in range(50)] for i in range(50)], 'New Level', dungeon_path, tilemap1=[[0 for i in range(50)] for i in range(50)], tilemap2=[[0 for i in range(50)] for i in range(50)]))
            buttons.append(Button(x, y, 100, 100, 'New Level', get_font_size(100, 'New Level')))
        if back.isClicked():
            editor = False
            menu = True

    if create:
        audio = False
        screen.blit(dungeon, (0,0))
        if delete_level:
            pygame.draw.rect(screen, (42, 146, 238), (50, 50, 620, 260))
            drawText('Are you sure?', WIDTH//2, 100, 60, (255, 255, 255))
            no = Button(WIDTH//2-40, 150, 80, 50, 'No', 30)
            no.draw(screen)
            yes = Button(WIDTH//2-40, 210, 80, 50, 'Yes', 30)
            yes.draw(screen)
            if no.isClicked():
                delete_level = False
            if yes.isClicked():
                player_levels.remove(player_levels[level_selec])
                editor = True
                create = False
        else:
            delete = Button(10, 10, 80, 50, 'Delete', get_font_size(100, 'Delete'))
            delete.draw(screen)
            back = Button(95, 10, 50, 50, '<', 30)
            back.draw(screen)
            name_input.draw(screen)
            player_levels[level_selec].name = name_input.text
            edit_button = Button(285, 100, 150, 100, 'Edit', 60)
            edit_button.draw(screen)
            play_button = Button(285, 220, 150, 100, 'Play', 60)
            play_button.draw(screen)
            if back.isClicked():
                editor = True
                create = False
            if delete.isClicked():
                delete_level = True
            if edit_button.isClicked():
                edit = True
                create = False
                buttons_created = False
                camera.offset.x, camera.offset.y = 0, 0
                if player_levels[level_selec].bg_path == sky_path:
                    background = sky
                if player_levels[level_selec].bg_path == dungeon_path:
                    background = dungeon
                background_dim = (background.get_rect().width, background.get_rect().height)
                selected_x, selected_y = -60, -60
                layers = [1, 2, 3]
                active_layer = 3
                layer_buttons_drawn = False
                dragging = False
                undo_stack = []
                redo_stack = []
            if play_button.isClicked() and create:
                player_levels[level_selec].find_start()
                if player_levels[level_selec].start and player_levels[level_selec].finish:
                    testing_level = True

                    pygame.mixer.music.load(game_music)
                    pygame.mixer.music.play(-1)

                    curr_level = player_levels[level_selec]

                    if curr_level.bg_path == sky_path:
                        background = sky
                    if curr_level.bg_path == dungeon_path:
                        background = dungeon

                    audio = True
                    create = False
                    game = True
                    paused = False

                    player.curr_spell = player.rotation[0]
                    player.reset()
                    door_img = door_img1

                    player.rect.x, player.rect.y = curr_level.start

                    # ✅ FIX: reset camera
                    camera.offset.x = player.rect.x - WIDTH // 2
                    camera.offset.y = player.rect.y - HEIGHT // 2

                    # ✅ FIX: ensure correct player group
                    players.empty()
                    players.add(player)

                    blocks = get_solid_blocks(curr_level.tilemap3, mapTiles, 40)
                    blocks += get_solid_blocks(curr_level.tilemap2, mapTiles, 40)
                    blocks += get_solid_blocks(curr_level.tilemap1, mapTiles, 40)

                    spikes = get_spikedata(get_spikes(curr_level.tilemap3, mapTiles, 40))
                    spikes += get_spikedata(get_spikes(curr_level.tilemap2, mapTiles, 40))
                    spikes += get_spikedata(get_spikes(curr_level.tilemap1, mapTiles, 40))

                    lavas = get_lavadata(curr_level.tilemap3, mapTiles, 40)
                    lavas += get_lavadata(curr_level.tilemap2, mapTiles, 40)
                    lavas += get_lavadata(curr_level.tilemap1, mapTiles, 40)

                    ladders = get_ladders(curr_level.tilemap3, mapTiles, 40)

                    enemiesDrawn = False
                    movingBlocksDrawn = False

    if edit:
        clicked = False
        audio = False

        background_width = background_dim[0]*camera.zoom
        background_height = background_dim[1]*camera.zoom

        screen.fill((0, 0, 0))
        screen.blit(
        pygame.transform.scale(background, (background_width, background_height)),
            (-camera.offset.x * camera.zoom, -camera.offset.y * camera.zoom)
        )
                    
        if 1 in layers:
            draw_tilemap(screen, player_levels[level_selec].tilemap1, mapTilesEditor, 40, offset_x=camera.offset.x, offset_y=camera.offset.y, zoom=camera.zoom)
        if 2 in layers:
            draw_tilemap(screen, player_levels[level_selec].tilemap2, mapTilesEditor, 40, offset_x=camera.offset.x, offset_y=camera.offset.y, zoom=camera.zoom)
        if 3 in layers:
            draw_tilemap(screen, player_levels[level_selec].tilemap3, mapTilesEditor, 40, offset_x=camera.offset.x, offset_y=camera.offset.y, zoom=camera.zoom)
        pygame.draw.rect(screen, (240, 202, 144), (0, 260, 720, 100))
        
        sky_button = Button(10, 10, 60, 40, 'Sky', 25)
        sky_button.draw(screen)
        dungeon_button = Button(10, 60, 80, 40, 'Dungeon', 25)
        dungeon_button.draw(screen)

        collisions = 0
        
        mouseX, mouseY = pygame.mouse.get_pos()

        world_x = (mouseX / camera.zoom) + camera.offset.x
        world_y = (mouseY / camera.zoom) + camera.offset.y

        block_x = (world_x // 40) * 40
        block_y = (world_y // 40) * 40

        for event in pygame.event.get():
            if event.type == pygame.MOUSEWHEEL:
                # world position BEFORE zoom
                world_x_before = (mouseX / camera.zoom) + camera.offset.x
                world_y_before = (mouseY / camera.zoom) + camera.offset.y

                # change zoom
                zoom_factor = 1.1 if event.y > 0 else 0.9
                camera.zoom *= zoom_factor

                # clamp zoom
                camera.zoom = max(camera.min_zoom, min(camera.zoom, camera.max_zoom))

                # world position AFTER zoom
                world_x_after = (mouseX / camera.zoom) + camera.offset.x
                world_y_after = (mouseY / camera.zoom) + camera.offset.y

                # adjust offset so mouse stays on same tile
                camera.offset.x += (world_x_before - world_x_after)
                camera.offset.y += (world_y_before - world_y_after)

                block_x = (world_x_after // 40) * 40
                block_y = (world_y_after // 40) * 40

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    if undo_stack:
                        row, col, old_tile, new_tile, layer = undo_stack.pop()

                        if layer == 1:
                            tilemap = player_levels[level_selec].tilemap1
                        elif layer == 2:
                            tilemap = player_levels[level_selec].tilemap2
                        elif layer == 3:
                            tilemap = player_levels[level_selec].tilemap3

                        tilemap[row][col] = old_tile
                        redo_stack.append((row, col, old_tile, new_tile, layer))

                # ✅ REDO (Ctrl + Y)
                if event.key == pygame.K_y and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    if redo_stack:
                        row, col, old_tile, new_tile, layer = redo_stack.pop()

                        if layer == 1:
                            tilemap = player_levels[level_selec].tilemap1
                        elif layer == 2:
                            tilemap = player_levels[level_selec].tilemap2
                        elif layer == 3:
                            tilemap = player_levels[level_selec].tilemap3

                        tilemap[row][col] = new_tile
                        undo_stack.append((row, col, old_tile, new_tile, layer))

        keys = pygame.key.get_pressed()

        if pygame.mouse.get_pressed()[0] and not dragging and mouseY < 260 and mouseX < WIDTH-100:
            dragging = True
            last_mouse = (mouseX, mouseY)

        # stop dragging
        if not pygame.mouse.get_pressed()[0]:
            dragging = False

        if dragging:
            dx = mouseX - last_mouse[0]
            dy = mouseY - last_mouse[1]

            # adjust for zoom (VERY IMPORTANT)
            camera.offset.x -= dx / camera.zoom
            camera.offset.y -= dy / camera.zoom

            last_mouse = (mouseX, mouseY)
            
        # draw preview tile
        screen.blit(
            pygame.transform.scale(selected, (40*camera.zoom, 40*camera.zoom)),
            ((block_x - camera.offset.x)*camera.zoom, (block_y - camera.offset.y)*camera.zoom)
        )
        if not buttons_created:
            buttons = []
            i = 0
            for name, img in mapImages.items():
                col = i % 14
                row = i // 14
                x = 10 + col * 50
                y = 270 + row * 50
                buttons.append((ImgButton(x, y, img), name))
                i += 1
            buttons_created = True
            
        for button in buttons:
            button[0].draw(screen)
            if button[0].isClicked() and not clicked:
                selected_block = button[1]
                selected_x, selected_y = button[0].rect.x, button[0].rect.y
                collisions += 1
                clicked = True

        screen.blit(pygame.transform.scale(selected, (40, 40)), (selected_x, selected_y))
            
        back = Button(WIDTH-60, 10, 50, 50, '<', 30)
        back.draw(screen)

        eraser = ImgButton(WIDTH-60, 100, erase_img)
        eraser.draw(screen)

        clear = Button(500, 10, 130, 50, 'Clear Layer', 30)
        clear.draw(screen)

        drawText('Layers', WIDTH-50, 180, 30, (255, 255, 255))

        if not layer_buttons_drawn:
            layer_buttons = []
            for i in range(3):
                if i+1 in layers:
                    layer_buttons.append(Button(WIDTH-100+(i*30), 210, 30, 30, str(i+1), 30, bg2_color=(100, 100, 140)))
                else:
                    layer_buttons.append(Button(WIDTH-100+(i*30), 210, 30, 30, str(i+1), 30))
            layer_buttons_drawn = True

        for i in range(len(layer_buttons)):
            layer_buttons[i].draw(screen)
            if layer_buttons[i].isClicked() and not clicked:
                if i+1 in layers:
                    layers.remove(i+1)
                    layer_buttons[i].bg2_color = (70, 70, 90)
                    if layers:
                        active_layer = max(layers)
                else:
                    layers.append(i+1)
                    layer_buttons[i].bg2_color = (100, 100, 140)
                    if layers:
                        active_layer = max(layers)
                layers.sort()
                clicked = True
        
        if back.isClicked() and not clicked:
            edit = False
            create = True
            buttons = []
            buttons_created = False
            clicked = True
        if sky_button.isClicked() and not clicked:
            player_levels[level_selec].bg_path = sky_path
            background = sky
            collisions += 1
            clicked = True
        if dungeon_button.isClicked() and not clicked:
            player_levels[level_selec].bg_path = dungeon_path
            background = dungeon
            collisions += 1
            clicked = True
        if eraser.isClicked() and not clicked:
            selected_block = 'eraser'
            selected_x, selected_y = eraser.rect.x, eraser.rect.y
            collisions += 1
            clicked = True

        if collisions == 0 and pygame.mouse.get_pressed()[0] and not clicked and mouseX < WIDTH-100 and mouseY < 260:
            if layers:

                if active_layer == 1:
                    tilemap = player_levels[level_selec].tilemap1
                elif active_layer == 2:
                    tilemap = player_levels[level_selec].tilemap2
                elif active_layer == 3:
                    tilemap = player_levels[level_selec].tilemap3

                tile_size = 40

                # convert mouse → world
                world_x = (mouseX / camera.zoom) + camera.offset.x
                world_y = (mouseY / camera.zoom) + camera.offset.y

                # snap to grid (world space)
                grid_x = int(world_x // tile_size) * tile_size
                grid_y = int(world_y // tile_size) * tile_size

                # convert to tile indices
                col = grid_x // tile_size
                row = grid_y // tile_size
                
                if 0 <= row < len(tilemap) and 0 <= col < len(tilemap[0]):

                    old_tile = tilemap[row][col]

                    if selected_block != 'eraser':
                        new_tile = selected_block
                    else:
                        new_tile = 0

                    if old_tile != new_tile:
                        undo_stack.append((row, col, old_tile, new_tile, active_layer))
                        redo_stack.clear()

                        tilemap[row][col] = new_tile
        
    if levels:
        audio = False
        screen.blit(dungeon, (0,0))
        drawText('Main Levels', WIDTH//2, 50, 60, (255, 255, 255))
        lvlbuttons = []
        mouseX, mouseY = pygame.mouse.get_pos()
        mouse_buttons = pygame.mouse.get_pressed()

        back = Button(WIDTH-60, 10, 50, 50, '<', 30)
        back.draw(screen)
        
        for i in range(3):
            lvlbuttons.append(Button(10+(i*70), 100, 60, 60, str(i+1), 30, bg2_color=((141, 108, 218) if i+1 <= player.lvl else (100, 100, 100))))
        for i in range(3):
            lvlbuttons[i].draw(screen)
            if lvlbuttons[i].isClicked() and i+1 <= player.lvl:
                levels = False
                pygame.mixer.music.load(game_music)
                pygame.mixer.music.play(-1)
                curr_level = maplevels[i]
                if curr_level.bg_path == sky_path:
                    background = sky
                if curr_level.bg_path == dungeon_path:
                    background = dungeon
                audio = True
                game = True
                paused = False
                player.curr_spell = player.rotation[0]
                player.reset()
                door_img = door_img1
                player.rect.x, player.rect.y = curr_level.start
                blocks = get_solid_blocks(curr_level.tilemap3, mapTiles, 40)
                spikes = get_spikedata(get_spikes(curr_level.tilemap3, mapTiles, 40))
                lavas = get_lavadata(curr_level.tilemap3, mapTiles, 40)
                ladders = get_ladders(curr_level.tilemap3, mapTiles, 40)


        if back.isClicked():
            levels = False
            gamemodes = True

    if collection:
        audio = False
        screen.blit(dungeon, (0,0))
        drawText('Selected Spells', 200, 30, 60, (255, 255, 255))

        back = Button(WIDTH-60, 10, 50, 50, '<', 30)
        back.draw(screen)
        
        spell1 = ImgButton(10, 70, asset(''+str(player.rotation[0])+'_button.png'))
        spell1.draw(screen)

        spell2 = ImgButton(80, 70, asset(''+str(player.rotation[1])+'_button.png'))
        spell2.draw(screen)

        drawText('Spells', 200, 160, 60, (255, 255, 255))

        buttons = []

        for i in range(len(playerSpells)):
            if playerSpells[i] in player.spells:
                buttons.append(ImgButton(10+(i*70), 200, asset(''+str(playerSpells[i])+'_button.png')))
            else:
                buttons.append(ImgButton(10+(i*70), 200, asset(''+str(playerSpells[i])+'_button.png'), alpha=120))
            if i == 9:
                break

        for i in range(len(playerSpells)-10):
            if playerSpells[i+10] in player.spells:
                buttons.append(ImgButton(10+(i*70), 270, asset(''+str(playerSpells[i+10])+'_button.png')))
            else:
                buttons.append(ImgButton(10+(i*70), 270, asset(''+str(playerSpells[i+10])+'_button.png'), alpha=120))
            if i == 9:
                break

        for button in buttons:
            button.draw(screen)

        for i in range(len(buttons)):
            if player.selected_spell and playerSpells[i] == player.selected_spell:
                if i < 10:
                    screen.blit(selected, (10+(i*70), 200))
                else:
                    screen.blit(selected, (10+((i-10)*70), 270))

        if player.selected_spell != None and spell1.isClicked() and player.selected_spell != player.rotation[1]:
            player.rotation[0] = player.selected_spell
            player.selected_spell = None
        if player.selected_spell != None and spell2.isClicked() and player.selected_spell != player.rotation[0]:
            player.rotation[1] = player.selected_spell
            player.selected_spell = None
        for i in range(len(buttons)):
            if buttons[i].isClicked() and buttons[i].alpha == 255 and playerSpells[i] in player.spells:
                player.selected_spell = playerSpells[i]
        if back.isClicked():
            collection = False
            menu = True

    if shop:
        audio = False
        screen.blit(dungeon, (0,0))
        
        if silverOpen:
            index += 1
            if pos > -99:
                pos -= 3
            pygame.draw.rect(screen, (42, 146, 238), (50, 50, 620, 260))
            if result == '10 XP':
                drawText('10 XP', WIDTH//2, HEIGHT//2+pos, 50, (255, 255, 255))
            if result in playerSpells:
                screen.blit(pygame.image.load(asset(''+str(result)+'_button.png')), (WIDTH//2-48, HEIGHT//2-48+pos))
            screen.blit(pygame.image.load(asset('silver_chest2.png')), (WIDTH//2-50, HEIGHT//2-50))
            if index == 50:
                silverOpen = False

        elif goldOpen:
            index += 1
            if pos > -99:
                pos -= 3
            pygame.draw.rect(screen, (42, 146, 238), (50, 50, 620, 260))
            if result == '25 XP':
                drawText('25 XP', WIDTH//2, HEIGHT//2+pos, 50, (255, 255, 255))
            if result in playerSpells:
                screen.blit(pygame.image.load(asset(''+str(result)+'_button.png')), (WIDTH//2-48, HEIGHT//2-48+pos))
            screen.blit(pygame.image.load(asset('gold_chest2.png')), (WIDTH//2-50, HEIGHT//2-50))
            if index == 50:
                goldOpen = False

        elif diamondOpen:
            index += 1
            if pos > -99:
                pos -= 3
            pygame.draw.rect(screen, (42, 146, 238), (50, 50, 620, 260))
            if result == '50 XP':
                drawText('50 XP', WIDTH//2, HEIGHT//2+pos, 50, (255, 255, 255))
            if result in playerSpells:
                screen.blit(pygame.image.load(asset(''+str(result)+'_button.png')), (WIDTH//2-48, HEIGHT//2-48+pos))
            screen.blit(pygame.image.load(asset('diamond_chest2.png')), (WIDTH//2-50, HEIGHT//2-50))
            if index == 50:
                diamondOpen = False
            
        else:
            drawText('Shop', WIDTH//2, 30, 80, (255, 255, 255))

            screen.blit(coin, (10, 10))
            drawText2(str(player.coins), 52, 10, 40, (255, 255, 255))

            silver = ImgButton(50, 100, asset('silver_chest.png'))
            screen.blit(coin, (40, 180))
            drawText2('50', 82, 180, 40, ((255, 255, 255) if player.coins >= 50 else (238, 42, 42)))

            gold = ImgButton(WIDTH//2-50, 100, asset('gold_chest.png'))
            screen.blit(coin, (WIDTH//2-60, 180))
            drawText2('100', WIDTH//2-18, 180, 40, ((255, 255, 255) if player.coins >= 100 else (238, 42, 42)))

            diamond = ImgButton(570, 100, asset('diamond_chest.png'))
            screen.blit(coin, (560, 180))
            drawText2('200', 602, 180, 40, ((255, 255, 255) if player.coins >= 200 else (238, 42, 42)))

            silver.draw(screen)
            gold.draw(screen)
            diamond.draw(screen)

        back = Button(WIDTH-60, 10, 50, 50, '<', 30)
        back.draw(screen)
        
        if back.isClicked():
            shop = False
            menu = True
        if player.coins >= 50 and silver.isClicked() and not (silverOpen or goldOpen or diamondOpen):
            silverOpen = True
            index = 0
            pos = 0
            player.coins -= 50
            result = random.choices(silverOpt, weights=silverChances, k=1)[0]
            if result == 1:
                spellList = []
                for spell, tier in tiers.items():
                    if tier == 1 and spell not in player.spells:
                        spellList.append(spell)
                if spellList:
                    result = random.choice(spellList)
                else:
                    result = '10 XP'
            if result == 2:
                spellList = []
                for spell, tier in tiers.items():
                    if tier == 2 and spell not in player.spells:
                        spellList.append(spell)
                if spellList:
                    result = random.choice(spellList)
                else:
                    result = '10 XP'
            if result == '10 XP':
                player.xp += 10
            if result in playerSpells:
                player.spells.append(result)
        if player.coins >= 100 and gold.isClicked() and not (silverOpen or goldOpen or diamondOpen):
            goldOpen = True
            index = 0
            pos = 0
            player.coins -= 100
            result = random.choices(goldOpt, weights=goldChances, k=1)[0]
            if result == 1:
                spellList = []
                for spell, tier in tiers.items():
                    if tier == 1 and spell not in player.spells:
                        spellList.append(spell)
                if spellList:
                    result = random.choice(spellList)
                else:
                    result = '25 XP'
            if result == 2:
                spellList = []
                for spell, tier in tiers.items():
                    if tier == 2 and spell not in player.spells:
                        spellList.append(spell)
                if spellList:
                    result = random.choice(spellList)
                else:
                    result = '25 XP'
            if result == 3:
                spellList = []
                for spell, tier in tiers.items():
                    if tier == 3 and spell not in player.spells:
                        spellList.append(spell)
                if spellList:
                    result = random.choice(spellList)
                else:
                    result = '25 XP'
            if result == '25 XP':
                player.xp += 25
            if result in playerSpells:
                player.spells.append(result)
        if player.coins >= 200 and diamond.isClicked() and not (silverOpen or goldOpen or diamondOpen):
            diamondOpen = True
            index = 0
            pos = 0
            player.coins -= 200
            result = random.choices(diamondOpt, weights=diamondChances, k=1)[0]
            if result == 2:
                spellList = []
                for spell, tier in tiers.items():
                    if tier == 2 and spell not in player.spells:
                        spellList.append(spell)
                if spellList:
                    result = random.choice(spellList)
                else:
                    result = '50 XP'
            if result == 3:
                spellList = []
                for spell, tier in tiers.items():
                    if tier == 3 and spell not in player.spells:
                        spellList.append(spell)
                if spellList:
                    result = random.choice(spellList)
                else:
                    result = '50 XP'
            if result == 4:
                spellList = []
                for spell, tier in tiers.items():
                    if tier == 4 and spell not in player.spells:
                        spellList.append(spell)
                if spellList:
                    result = random.choice(spellList)
                else:
                    result = '50 XP'
            if result == '50 XP':
                player.xp += 50
            if result in playerSpells:
                player.spells.append(result)

    if spells:
        audio = False
        screen.blit(dungeon, (0,0))
        
        back = Button(WIDTH-60, 10, 50, 50, '<', 30)
        back.draw(screen)

        notUnlocked = [s for s in playerSpells if s not in player.spells]

        if player.curr_unlock and notUnlocked and player.curr_unlock in player.spells:
            player.curr_unlock = notUnlocked[0]

        for i in range(len(notUnlocked)):
            img = pygame.image.load(asset(''+str(notUnlocked[i])+'_button.png'))
            if notUnlocked[i] != player.curr_unlock:
                img.set_alpha(120)
            screen.blit(img, (WIDTH//2-48+(i*120) - scrollbar.scroll_offset, HEIGHT//2-48))
            drawText(str(notUnlocked[i].upper()), WIDTH//2+(i*120) - scrollbar.scroll_offset, HEIGHT//2-70, 40, (255, 255, 255))
            
        if player.curr_unlock:
            if tiers[player.curr_unlock] == 1:
                maxXp = 50
            if tiers[player.curr_unlock] == 2:
                maxXp = 100
            if tiers[player.curr_unlock] == 3:
                maxXp = 200
            if tiers[player.curr_unlock] == 4:
                maxXp = 400

        pygame.draw.rect(screen, (150, 150, 150), (WIDTH//2-48 - scrollbar.scroll_offset, HEIGHT//2+60, 96, 15))
        pygame.draw.rect(screen, (220, 220, 220), (WIDTH//2-48 - scrollbar.scroll_offset, HEIGHT//2+60, (96*(player.xp/maxXp) if player.xp <= maxXp else 96), 15))

        drawText(str(player.xp)+'/'+str(maxXp)+' XP', WIDTH//2 - scrollbar.scroll_offset, HEIGHT//2+90, 30, (255, 255, 255))

        if player.xp >= maxXp:
            get = Button(WIDTH//2-40 - scrollbar.scroll_offset, HEIGHT//2+120, 80, 30, 'Unlock', 20)
            get.draw(screen)


        scrollbar.draw(screen)

        if back.isClicked():
            spells = False
            menu = True
        if player.xp >= maxXp and get.isClicked():
            player.spells.append(player.curr_unlock)
            if len(notUnlocked) > 1:
                player.curr_unlock = notUnlocked[1]
            else:
                player.curr_unlock = None
            player.xp -= maxXp

        for event in pygame.event.get():
            scrollbar.handle_event(event)
    
    if game:
        audio = False
        
        screen.blit(background, (-camera.offset.x,-camera.offset.y))
        background_dim = (background.get_rect().width, background.get_rect().height)
        
        players.update(blocks)
        camera.follow(player, curr_level.width, curr_level.height)

        if curr_level.tilemap1:
            draw_tilemap(screen, curr_level.tilemap1, mapTiles, 40, offset_x=camera.offset.x, offset_y=camera.offset.y)
        if curr_level.tilemap2:
            draw_tilemap(screen, curr_level.tilemap2, mapTiles, 40, offset_x=camera.offset.x, offset_y=camera.offset.y)
        draw_tilemap(screen, curr_level.tilemap3, mapTiles, 40, offset_x=camera.offset.x, offset_y=camera.offset.y)
        screen.blit(door_img, (curr_level.finish[0]-camera.offset.x, curr_level.finish[1]-camera.offset.y))

        enemiesDrawn = True
        movingBlocksDrawn = True

        count += 1
        
        mouseX, mouseY = pygame.mouse.get_pos()
        keys = pygame.key.get_pressed()

        if paused_clicked:
            pygame.draw.rect(screen, (120, 52, 141), (160, 55, 400, 250))
            drawText('Paused', WIDTH//2, 100, 60, (255, 255, 255))
            if not testing_level:
                menu_button = Button(WIDTH//2-40, 150, 80, 60, 'Menu', 30)
                menu_button.draw(screen)
                continue_button = Button(WIDTH//2-60, 220, 120, 60, 'Continue', 30)
                continue_button.draw(screen)
                buttons = []
                buttons_created = False
                player.attacking = False
                if menu_button.isClicked():
                    player.reset()
                    enemies = pygame.sprite.Group()
                    movingBlocks = pygame.sprite.Group()
                    enemiesDrawn = False
                    movingBlocksDrawn = False
                    pygame.mixer.music.load(lobby)
                    pygame.mixer.music.play(-1)
                    audio = True
                    game = False
                    menu = True
                    paused_clicked = False
                if continue_button.isClicked():
                    paused = False
                    paused_clicked = False
                    pygame.mixer.music.unpause()
            else:
                edit_button = Button(WIDTH//2-40, 150, 80, 60, 'Edit', 30)
                edit_button.draw(screen)
                continue_button = Button(WIDTH//2-60, 220, 120, 60, 'Continue', 30)
                continue_button.draw(screen)
                buttons = []
                buttons_created = False
                player.attacking = False
                if edit_button.isClicked():
                    player.reset()
                    enemies = pygame.sprite.Group()
                    movingBlocks = pygame.sprite.Group()
                    enemiesDrawn = False
                    movingBlocksDrawn = False
                    pygame.mixer.music.load(lobby)
                    pygame.mixer.music.play(-1)
                    audio = True
                    game = False
                    edit = True
                    selected_x, selected_y = -60, -60
                    layers = [1, 2, 3]
                    active_layer = 3
                    layer_buttons_drawn = False
                    dragging = False
                    undo_stack = []
                    redo_stack = []
                    paused_clicked = False
                if continue_button.isClicked():
                    paused = False
                    paused_clicked = False
                    pygame.mixer.music.unpause()
    
        if not paused:
            pause_button = ImgButton(WIDTH-80, 10, asset('pause.png'))
            pause_button.draw(screen)

            if pause_button.isClicked():
                paused = True
                pygame.mixer.music.pause()
                paused_clicked = True
                
            if player.attacking and player.curr_spell == 'laser':
                i += 1
                pos = player.rect.center - (direction * 20)
                for j in range(18):
                    pos += direction * 20
                    rect = pygame.Rect(0, 0, 20, 20)
                    rect.center = pos
                    rect.x -= camera.offset.x
                    rect.y -= camera.offset.y
                    laser_squares.append(rect)
                if i >= 18:
                    player.attacking = False
                    laser_squares = []
                for e in enemies:
                    for s in laser_squares:
                        if e.rect.colliderect(s) and e.dmg_cooldown >= 6:
                            e.hp -= 2
                            e.dmg_cooldown = 0

                for s in laser_squares:
                    pygame.draw.rect(screen, (255, 20, 20), (s.x+count%2, s.y+count%2, s.width, s.height))
                
            enemies.update(player, blocks, spikes)
            fireballs.update(blocks)
            zaps.update(blocks)
            freezes.update(blocks)
            poisons.update()
            hands.update(blocks)
            darts.update(blocks)
            movingBlocks.update(player)
            explosions.update()

            if player.invis:
                player.image.set_alpha(120)
            else:
                player.image.set_alpha(255)

            barwidth = (spellCurrCooldowns[player.rotation[0]]/spellCooldowns[player.curr_spell])*100
            barwidth2 = (spellCurrCooldowns[player.rotation[1]]/spellCooldowns[player.curr_spell])*100

            if (spellCurrCooldowns[player.rotation[0]]/spellCooldowns[player.curr_spell])*100 > 100:
                barwidth = 100

            if (spellCurrCooldowns[player.rotation[1]]/spellCooldowns[player.curr_spell])*100 > 100:
                barwidth2 = 100

            barwidths = [barwidth, barwidth2]

            if player.speed_timer > 0:
                player.speed_timer += 1
                if player.speed_timer >= 15:
                    player.speed = 10
                    player.speed_timer = 0

            spellCurrCooldowns[player.curr_spell] += 1

            angle = math.degrees(math.atan2(-(mouseY+camera.offset.y-player.rect.y),mouseX+camera.offset.x-player.rect.x))

            if player.curr_spell == 'fireball' or player.curr_spell == 'freeze':
                line_img = pygame.image.load(asset('line.png'))
                line = pygame.transform.rotate(line_img, angle)
                line_x = player.rect.centerx
                line_y = player.rect.centery
                line_rect = line.get_rect(center = (line_x - camera.offset.x, line_y - camera.offset.y))
                screen.blit(line, line_rect)
            if player.curr_spell == 'zap':
                line_img = pygame.transform.scale(pygame.image.load(asset('line.png')), (500, 20))
                line = pygame.transform.rotate(line_img, angle)
                line_x = player.rect.centerx
                line_y = player.rect.centery
                line_rect = line.get_rect(center = (line_x - camera.offset.x, line_y - camera.offset.y))
                screen.blit(line, line_rect)
            if player.curr_spell == 'laser' and not player.attacking:
                line_img = pygame.transform.scale(pygame.image.load(asset('line.png')), (720, 20))
                line = pygame.transform.rotate(line_img, angle)
                line_x = player.rect.centerx
                line_y = player.rect.centery
                line_rect = line.get_rect(center = (line_x - camera.offset.x, line_y - camera.offset.y))
                screen.blit(line, line_rect)
            if player.curr_spell == 'teleport' and not player.attacking:
                line_img = pygame.transform.scale(pygame.image.load(asset('square.png')), (40, 40))
                line_rect = line_img.get_rect(center = (mouseX, mouseY))
                colliding = False
                for block in blocks:
                    if block.colliderect(line_rect):
                        colliding = True
                for s in spikes:
                    if s.colliderect(line_rect):
                        colliding = True
                if not colliding:
                    screen.blit(line_img, line_rect)
            if player.curr_spell == 'hand' and not player.attacking:
                line_img = pygame.transform.scale(pygame.image.load(asset('line.png')), (600, 32))
                line = pygame.transform.rotate(line_img, angle)
                line_x = player.rect.centerx
                line_y = player.rect.centery
                line_rect = line.get_rect(center = (line_x - camera.offset.x, line_y - camera.offset.y))
                screen.blit(line, line_rect)
            
            screen.blit(
                pygame.transform.scale(player.image, (40, 40)),
                (
                    player.rect.x - camera.offset.x + player.shakeX,
                    player.rect.y - camera.offset.y + player.shakeY
                )
            )
            for f in fireballs:
                screen.blit(f.image, (f.rect.x - camera.offset.x, f.rect.y - camera.offset.y))
            for z in zaps:
                screen.blit(z.image, (z.rect.x - camera.offset.x, z.rect.y - camera.offset.y))
            for fr in freezes:
                screen.blit(fr.image, (fr.rect.x - camera.offset.x, fr.rect.y - camera.offset.y))
            for p in poisons:
                screen.blit(p.image, (p.rect.x - camera.offset.x, p.rect.y - camera.offset.y))
            for h in hands:
                screen.blit(h.image, (h.rect.x - camera.offset.x, h.rect.y - camera.offset.y))
            for d in darts:
                screen.blit(d.image, (d.rect.x - camera.offset.x, d.rect.y - camera.offset.y))
            for m in movingBlocks:
                screen.blit(m.image, (m.rect.x - camera.offset.x, m.rect.y - camera.offset.y))
            for e in enemies:
                screen.blit(e.image, (e.rect.x - camera.offset.x, e.rect.y - camera.offset.y))
                pygame.draw.rect(screen, (100, 100, 100), (e.rect.x - camera.offset.x, e.rect.y - camera.offset.y - 15, 40, 10))
                pygame.draw.rect(screen, (129, 255, 146), (e.rect.x - camera.offset.x, e.rect.y - camera.offset.y - 15, 40*(e.hp/e.max_hp), 10))
                if e.zapped and e.dmg_cooldown2 >= 15:
                    e.tick += 1
                    e.dmg_cooldown2 = 0
                    e.hp -= 1
                    screen.blit(e.zap[0], (e.rect.x - camera.offset.x, e.rect.y - camera.offset.y))
                    if e.tick == 3:
                        e.zapped = False
                if e.burned and e.dmg_cooldown2 >= 15:
                    e.tick += 1
                    e.dmg_cooldown2 = 0
                    e.hp -= 1
                    screen.blit(pygame.image.load(asset('burn.png')), (e.rect.x - camera.offset.x, e.rect.y - camera.offset.y))
                    if e.tick == 3:
                        e.burned = False
                if e.frozen:
                    screen.blit(pygame.image.load(asset('ice.png')), (e.rect.x - camera.offset.x - 5, e.rect.y - camera.offset.y - 5))
                    e.tick += 1
                    if e.tick == 30:
                        e.tick = 0
                        e.frozen = False
                if e.poisoned and e.dmg_cooldown2 >= 30:
                    e.tick += 1
                    e.dmg_cooldown2 = 0
                    e.hp -= 1
                    screen.blit(pygame.image.load(asset('poisoned.png')), (e.rect.x - camera.offset.x, e.rect.y - camera.offset.y))
                    if e.tick == 3:
                        e.poisoned = False
                        e.speed *= 2
                        
            for e in explosions:
                screen.blit(
                    pygame.transform.scale(e.image, (40, 40)),
                    (
                        e.rect.x - camera.offset.x + player.shakeX,
                        e.rect.y - camera.offset.y + player.shakeY
                    )
                )

            spell1 = ImgButton(650, 220, asset(''+str(player.rotation[0])+'_button.png'))
            spell1.draw(screen)

            spell2 = ImgButton(650, 290, asset(''+str(player.rotation[1])+'_button.png'))
            spell2.draw(screen)

            if player.curr_spell == player.rotation[0]:
                screen.blit(selected, (650, 220))
            if player.curr_spell == player.rotation[1]:
                screen.blit(selected, (650, 290))

            if player.invis:
                player.ghost_timer += 1
                if player.ghost_timer >= 100:
                    player.invis = False
                    player.ghost_timer = 0
                    spellCurrCooldowns[player.curr_spell] = 0

            if player.attacking and player.curr_spell == 'heal':
                player.tick += 1
                if player.tick < 5:
                    screen.blit(pygame.image.load(asset('heal1.png')), (player.rect.x - camera.offset.x, player.rect.y - camera.offset.y))
                elif player.tick < 10:
                    screen.blit(pygame.image.load(asset('heal2.png')), (player.rect.x - camera.offset.x, player.rect.y - camera.offset.y))
                elif player.tick < 15:
                    screen.blit(pygame.image.load(asset('heal1.png')), (player.rect.x - camera.offset.x, player.rect.y - camera.offset.y))
                if player.tick >= 15:
                    player.attacking = False
                    spellCurrCooldowns[player.curr_spell] = 0
                    if player.hp < 100:
                        if player.hp > 70:
                            player.hp = 100
                        else:
                            player.hp += 30

            if pygame.mouse.get_pressed()[0]:
                if spell1.isClicked() and not player.attacking:
                    player.curr_spell = player.rotation[0]
                elif spell2.isClicked() and not player.attacking:
                    player.curr_spell = player.rotation[1]
                elif not (spell1.isClicked() or spell2.isClicked()) and not player.attacking:
                    if player.curr_spell == 'slash' and barwidths[player.rotation.index(player.curr_spell)] == 100:
                        player.frame_index = 0
                        player.frame_index2 = 0
                        player.attacking = True
                    if player.curr_spell == 'fireball' and barwidths[player.rotation.index(player.curr_spell)] == 100 and len(fireballs) < 1 and not player.attacking:
                        fireballs.add(Fireball(player.rect.centerx, player.rect.centery, mouseX+camera.offset.x, mouseY+camera.offset.y))
                        player.frame_index = 0
                        player.attacking = True
                        if (angle >= 90 and angle <= 180) or (angle <= -90 and angle >= -180):
                            player.flipped = True
                        else:
                            player.flipped = False
                    if player.curr_spell == 'dash' and barwidths[player.rotation.index(player.curr_spell)] == 100:
                        player.attacking = True
                    if player.curr_spell == 'shield' and barwidths[player.rotation.index(player.curr_spell)] == 100 and not player.shield:
                        player.shield = True
                        spellCurrCooldowns[player.curr_spell] = 0
                    if player.curr_spell == 'laser' and barwidths[player.rotation.index(player.curr_spell)] == 100 and not player.attacking:
                        player.attacking = True
                        spellCurrCooldowns[player.curr_spell] = 0
                        direction = (pygame.Vector2(mouseX+camera.offset.x, mouseY+camera.offset.y) - (player.rect.centerx, player.rect.centery)).normalize()
                        pos = player.rect.center - (direction * 20)
                        i = 0
                        if (angle >= 90 and angle <= 180) or (angle <= -90 and angle >= -180):
                            player.flipped = True
                        else:
                            player.flipped = False
                    if player.curr_spell == 'zap' and barwidths[player.rotation.index(player.curr_spell)] == 100 and len(zaps) < 1 and not player.attacking:
                        zaps.add(Zap(player.rect.centerx, player.rect.centery, mouseX+camera.offset.x, mouseY+camera.offset.y))
                        player.frame_index = 0
                        player.attacking = True
                        if (angle >= 90 and angle <= 180) or (angle <= -90 and angle >= -180):
                            player.flipped = True
                        else:
                            player.flipped = False
                    if player.curr_spell == 'heal' and barwidths[player.rotation.index(player.curr_spell)] == 100 and not player.attacking:
                        player.tick = 0
                        player.attacking = True
                    if player.curr_spell == 'burn' and barwidths[player.rotation.index(player.curr_spell)] == 100:
                        player.frame_index = 0
                        player.frame_index2 = 0
                        player.attacking = True
                    if player.curr_spell == 'freeze' and barwidths[player.rotation.index(player.curr_spell)] == 100 and len(freezes) < 1 and not player.attacking:
                        freezes.add(Freeze(player.rect.centerx, player.rect.centery, mouseX+camera.offset.x, mouseY+camera.offset.y))
                        player.frame_index = 0
                        player.attacking = True
                        if (angle >= 90 and angle <= 180) or (angle <= -90 and angle >= -180):
                            player.flipped = True
                        else:
                            player.flipped = False
                    if player.curr_spell == 'poison' and barwidths[player.rotation.index(player.curr_spell)] == 100 and not player.attacking:
                        poisons.add(Poison(player.rect.x, player.rect.y))
                        player.frame_index = 0
                        player.attacking = True
                    if player.curr_spell == 'charge' and barwidths[player.rotation.index(player.curr_spell)] == 100:
                        player.attacking = True
                        spellCurrCooldowns[player.curr_spell] = 0
                    if player.curr_spell == 'teleport' and barwidths[player.rotation.index(player.curr_spell)] == 100:
                        if not colliding:
                            img = player.image.copy()
                            img.set_alpha(120)
                            avgX = (mouseX+camera.offset.x + player.rect.x)//2
                            avgY = (mouseY+camera.offset.y + player.rect.y)//2
                            screen.blit(img, (avgX - camera.offset.x, avgY - camera.offset.y))
                            player.rect.center = mouseX, mouseY
                            spellCurrCooldowns[player.curr_spell] = 0
                    if player.curr_spell == 'ghost' and barwidths[player.rotation.index(player.curr_spell)] == 100 and not player.invis:
                        player.invis = True
                    if player.curr_spell == 'hand' and barwidths[player.rotation.index(player.curr_spell)] == 100 and len(hands) < 1 and not player.attacking:
                        hands.add(Hand(player.rect.centerx, player.rect.centery, mouseX, mouseY))
                        player.frame_index = 0
                        player.attacking = True
                        if (angle >= 90 and angle <= 180) or (angle <= -90 and angle >= -180):
                            player.flipped = True
                        else:
                            player.flipped = False

            if keys[pygame.K_1]:
                player.curr_spell = player.rotation[0]

            if keys[pygame.K_2]:
                player.curr_spell = player.rotation[1]

            if player.attacking and player.curr_spell == 'slash':
                player.frame_index2 += 1
                if player.frame_index2 >= len(player.slash_right)-1:
                    player.frame_index2 = 0
                player.slash_image = player.slash_left[player.frame_index2] if player.flipped else player.slash_right[player.frame_index2]
                screen.blit(
                    pygame.transform.scale(player.slash_image, (40, 40)),
                    (
                        player.slash_rect.x - camera.offset.x + player.shakeX,
                        player.slash_rect.y - camera.offset.y + player.shakeY
                    )
            )

            if player.attacking and player.curr_spell == 'burn':
                player.frame_index2 += 1
                if player.frame_index2 >= len(player.burn_right)-1:
                    player.frame_index2 = 0
                player.burn_image = player.burn_left[player.frame_index2] if player.flipped else player.burn_right[player.frame_index2]
                screen.blit(
                    pygame.transform.scale(player.burn_image, (40, 40)),
                    (
                        player.slash_rect.x - camera.offset.x + player.shakeX,
                        player.slash_rect.y - camera.offset.y + player.shakeY
                    )
            )

        if player.shield:
            screen.blit(player.shield_img, (player.rect.x-6-camera.offset.x, player.rect.y-6-camera.offset.y))

        pygame.draw.rect(screen, (100, 0, 0), (10, 50, 100, 30))
        pygame.draw.rect(screen, (255, 20, 20), (10, 50, barwidth, 30))
        pygame.draw.rect(screen, (100, 0, 0), (10, 90, 100, 30))
        pygame.draw.rect(screen, (255, 20, 20), (10, 90, barwidth2, 30))

        pygame.draw.rect(screen, (70, 70, 70), (10, 10, 210, 30))
        pygame.draw.rect(screen, health_color(player.hp, 100), (15, 15, player.hp*2, 20))
        drawText('HP: '+str(round(player.hp))+'/100', 115, 25, 20, (0, 0, 0))

        for l in lavas:
            if player.rect.colliderect(l):
                player.hp = 0

        if player.hp <= 0:
            paused = True
            pygame.draw.rect(screen, (120, 52, 141), (160, 55, 400, 250))
            drawText('You Died', WIDTH//2, 100, 60, (255, 255, 255))
            buttons = []
            buttons_created = False
            pygame.mixer.music.pause()
            if not testing_level:
                menu_button = Button(WIDTH//2-40, 150, 80, 60, 'Menu', 30)
                menu_button.draw(screen)
                retry_button = Button(WIDTH//2-40, 220, 80, 60, 'Retry', 30)
                retry_button.draw(screen)
                player.attacking = False
                if menu_button.isClicked():
                    player.reset()
                    enemies = pygame.sprite.Group()
                    movingBlocks = pygame.sprite.Group()
                    enemiesDrawn = False
                    movingBlocksDrawn = False
                    pygame.mixer.music.load(lobby)
                    pygame.mixer.music.play(-1)
                    audio = True
                    game = False
                    menu = True
                if retry_button.isClicked():
                    player.reset()
                    player.rect.x, player.rect.y = curr_level.start
                    enemies = pygame.sprite.Group()
                    movingBlocks = pygame.sprite.Group()
                    enemiesDrawn = False
                    movingBlocksDrawn = False
                    paused = False
                    pygame.mixer.music.unpause()
            else:
                edit_button = Button(WIDTH//2-40, 150, 80, 60, 'Editor', 25)
                edit_button.draw(screen)
                retry_button = Button(WIDTH//2-40, 220, 80, 60, 'Retry', 30)
                retry_button.draw(screen)
                player.attacking = False
                if edit_button.isClicked():
                    player.reset()
                    enemies = pygame.sprite.Group()
                    movingBlocks = pygame.sprite.Group()
                    enemiesDrawn = False
                    movingBlocksDrawn = False
                    pygame.mixer.music.load(lobby)
                    pygame.mixer.music.play(-1)
                    audio = True
                    game = False
                    edit = True
                    selected_x, selected_y = -60, -60
                    layers = [1, 2, 3]
                    active_layer = 3
                    layer_buttons_drawn = False
                    dragging = False
                    undo_stack = []
                    redo_stack = []
                if retry_button.isClicked():
                    player.reset()
                    door_img = door_img1
                    player.rect.x, player.rect.y = curr_level.start
                    enemies = pygame.sprite.Group()
                    movingBlocks = pygame.sprite.Group()
                    enemiesDrawn = False
                    movingBlocksDrawn = False
                    paused = False
                    pygame.mixer.music.unpause()
                        
        door_rect = (curr_level.finish[0], curr_level.finish[1], 40, 40)

        if len(enemies) <= 0:
            door_img = door_img2
            pygame.mixer.music.pause()
            if player.rect.colliderect(door_rect):
                paused = True
                pygame.draw.rect(screen, (120, 52, 141), (160, 55, 400, 250))
                drawText('You Win', WIDTH//2, 100, 60, (255, 255, 255))
                buttons = []
                buttons_created = False
                if not testing_level:
                    menu_button = Button(WIDTH//2-40, 150, 80, 60, 'Menu', 30)
                    menu_button.draw(screen)
                    retry_button = Button(WIDTH//2-40, 220, 80, 60, 'Retry', 30)
                    retry_button.draw(screen)
                    player.attacking = False
                    if menu_button.isClicked():
                        player.reset()
                        enemies = pygame.sprite.Group()
                        movingBlocks = pygame.sprite.Group()
                        enemiesDrawn = False
                        movingBlocksDrawn = False
                        pygame.mixer.music.load(lobby)
                        pygame.mixer.music.play(-1)
                        audio = True
                        game = False
                        menu = True
                        if curr_level.num == player.lvl:
                            player.lvl += 1
                    if retry_button.isClicked():
                        player.reset()
                        door_img = door_img1
                        player.lvl += 1
                        player.rect.x, player.rect.y = curr_level.start
                        enemies = pygame.sprite.Group()
                        movingBlocks = pygame.sprite.Group()
                        enemiesDrawn = False
                        movingBlocksDrawn = False
                        paused = False
                        if curr_level.num == player.lvl:
                            player.coins += 40+player.lvl*10
                            player.xp += 20+player.lvl*5
                            player.lvl += 1
                            pygame.mixer.music.unpause()
                            
                else:
                    edit_button = Button(WIDTH//2-40, 150, 80, 60, 'Editor', 25)
                    edit_button.draw(screen)
                    retry_button = Button(WIDTH//2-40, 220, 80, 60, 'Retry', 30)
                    retry_button.draw(screen)
                    player.attacking = False
                    if edit_button.isClicked():
                        player.reset()
                        enemies = pygame.sprite.Group()
                        movingBlocks = pygame.sprite.Group()
                        enemiesDrawn = False
                        movingBlocksDrawn = False
                        pygame.mixer.music.load(lobby)
                        pygame.mixer.music.play(-1)
                        audio = True
                        game = False
                        edit = True
                        selected_x, selected_y = -60, -60
                        layers = [1, 2, 3]
                        active_layer = 3
                        layer_buttons_drawn = False
                        dragging = False
                        undo_stack = []
                        redo_stack = []
                    if retry_button.isClicked():
                        player.reset()
                        door_img = door_img1
                        player.rect.x, player.rect.y = curr_level.start
                        enemies = pygame.sprite.Group()
                        movingBlocks = pygame.sprite.Group()
                        enemiesDrawn = False
                        movingBlocksDrawn = False
                        paused = False
                        pygame.mixer.music.unpause()

    if survival:
        audio = False
        
        screen.blit(background, (-camera.offset.x,-camera.offset.y))
        background_dim = (background.get_rect().width, background.get_rect().height)
        
        players.update(blocks)
        camera.follow(player, curr_level.width, curr_level.height)

        draw_tilemap(screen, curr_level.tilemap, mapTiles, 40, offset_x=camera.offset.x, offset_y=camera.offset.y)

        enemiesDrawn = True
        movingBlocksDrawn = True

        count += 1
        
        mouseX, mouseY = pygame.mouse.get_pos()
        keys = pygame.key.get_pressed()

        if paused_clicked:
            pygame.draw.rect(screen, (120, 52, 141), (160, 55, 400, 250))
            drawText('Paused', WIDTH//2, 100, 60, (255, 255, 255))
            if not testing_level:
                menu_button = Button(WIDTH//2-40, 150, 80, 60, 'Menu', 30)
                menu_button.draw(screen)
                continue_button = Button(WIDTH//2-60, 220, 120, 60, 'Continue', 30)
                continue_button.draw(screen)
                buttons = []
                buttons_created = False
                player.attacking = False
                if menu_button.isClicked():
                    player.reset()
                    enemies = pygame.sprite.Group()
                    movingBlocks = pygame.sprite.Group()
                    enemiesDrawn = False
                    movingBlocksDrawn = False
                    pygame.mixer.music.load(lobby)
                    pygame.mixer.music.play(-1)
                    audio = True
                    survival = False
                    menu = True
                    paused_clicked = False
                if continue_button.isClicked():
                    paused = False
                    paused_clicked = False
                    pygame.mixer.music.unpause()
            else:
                edit_button = Button(WIDTH//2-40, 150, 80, 60, 'Edit', 30)
                edit_button.draw(screen)
                continue_button = Button(WIDTH//2-60, 220, 120, 60, 'Continue', 30)
                continue_button.draw(screen)
                buttons = []
                buttons_created = False
                player.attacking = False
                if edit_button.isClicked():
                    player.reset()
                    enemies = pygame.sprite.Group()
                    movingBlocks = pygame.sprite.Group()
                    enemiesDrawn = False
                    movingBlocksDrawn = False
                    pygame.mixer.music.load(lobby)
                    pygame.mixer.music.play(-1)
                    audio = True
                    game = False
                    edit = True
                    selected_x, selected_y = -60, -60
                    layers = [1, 2, 3]
                    active_layer = 3
                    layer_buttons_drawn = False
                    dragging = False
                    undo_stack = []
                    redo_stack = []
                    paused_clicked = False
                if continue_button.isClicked():
                    paused = False
                    paused_clicked = False
        
        if not paused:
            wave_timer -= 1
            
            pause_button = ImgButton(WIDTH-80, 10, asset('pause.png'))
            pause_button.draw(screen)

            txt_color = (0, 0, 0) if background == sky else (255, 255, 255)

            if curr_wave > 0:
                drawText('Wave '+str(curr_wave), WIDTH//2, 35, 60, txt_color)
            drawText2('Next Wave in '+str(wave_timer//30), 10, 320, 30, txt_color)

            drawText('Highscore: '+str(survival_high_score), WIDTH//2, 80, 30, txt_color)

            if pause_button.isClicked():
                paused = True
                pygame.mixer.music.pause()
                paused_clicked = True
                
            if player.attacking and player.curr_spell == 'laser':
                i += 1
                pos = player.rect.center - (direction * 20)
                for j in range(18):
                    pos += direction * 20
                    rect = pygame.Rect(0, 0, 20, 20)
                    rect.center = pos
                    rect.x -= camera.offset.x
                    rect.y -= camera.offset.y
                    laser_squares.append(rect)
                if i >= 18:
                    player.attacking = False
                    laser_squares = []
                for e in enemies:
                    for s in laser_squares:
                        if e.rect.colliderect(s) and e.dmg_cooldown >= 6:
                            e.hp -= 2
                            e.dmg_cooldown = 0

                for s in laser_squares:
                    pygame.draw.rect(screen, (255, 20, 20), (s.x+count%2, s.y+count%2, s.width, s.height))
                
            enemies.update(player, blocks, spikes)
            fireballs.update(blocks)
            zaps.update(blocks)
            freezes.update(blocks)
            poisons.update()
            hands.update(blocks)
            darts.update(blocks)
            movingBlocks.update(player)
            explosions.update()

            if wave_timer == 0:
                if len(enemies) <= 0:
                    wave_timer = 1350 if curr_wave%5 != 0 else 1800
                    wave_on = True
                    spawners = curr_wave if curr_wave < len(curr_level.spawners) else len(curr_level.spawners)-1
                    random.shuffle(curr_level.spawners)
                    i = 0
                    for spawner in curr_level.spawners[:spawners]:
                        i += 1
                        if i == 1 and curr_wave % 5 == 0:
                            spawner.spawn(enemy_spawn='blob_king')
                        else:
                            spawner.spawn()
                else:
                    player.hp = 0
            
            for spawner in curr_level.spawners:
                spawner.update()

            if player.invis:
                player.image.set_alpha(120)
            else:
                player.image.set_alpha(255)

            barwidth = (spellCurrCooldowns[player.rotation[0]]/spellCooldowns[player.curr_spell])*100
            barwidth2 = (spellCurrCooldowns[player.rotation[1]]/spellCooldowns[player.curr_spell])*100

            if (spellCurrCooldowns[player.rotation[0]]/spellCooldowns[player.curr_spell])*100 > 100:
                barwidth = 100

            if (spellCurrCooldowns[player.rotation[1]]/spellCooldowns[player.curr_spell])*100 > 100:
                barwidth2 = 100

            barwidths = [barwidth, barwidth2]

            if player.speed_timer > 0:
                player.speed_timer += 1
                if player.speed_timer >= 15:
                    player.speed = 10
                    player.speed_timer = 0

            spellCurrCooldowns[player.curr_spell] += 1

            angle = math.degrees(math.atan2(-(mouseY+camera.offset.y-player.rect.y),mouseX+camera.offset.x-player.rect.x))

            if player.curr_spell == 'fireball' or player.curr_spell == 'freeze':
                line_img = pygame.image.load(asset('line.png'))
                line = pygame.transform.rotate(line_img, angle)
                line_x = player.rect.centerx
                line_y = player.rect.centery
                line_rect = line.get_rect(center = (line_x - camera.offset.x, line_y - camera.offset.y))
                screen.blit(line, line_rect)
            if player.curr_spell == 'zap':
                line_img = pygame.transform.scale(pygame.image.load(asset('line.png')), (500, 20))
                line = pygame.transform.rotate(line_img, angle)
                line_x = player.rect.centerx
                line_y = player.rect.centery
                line_rect = line.get_rect(center = (line_x - camera.offset.x, line_y - camera.offset.y))
                screen.blit(line, line_rect)
            if player.curr_spell == 'laser' and not player.attacking:
                line_img = pygame.transform.scale(pygame.image.load(asset('line.png')), (720, 20))
                line = pygame.transform.rotate(line_img, angle)
                line_x = player.rect.centerx
                line_y = player.rect.centery
                line_rect = line.get_rect(center = (line_x - camera.offset.x, line_y - camera.offset.y))
                screen.blit(line, line_rect)
            if player.curr_spell == 'teleport' and not player.attacking:
                line_img = pygame.transform.scale(pygame.image.load(asset('square.png')), (40, 40))
                line_rect = line_img.get_rect(center = (mouseX, mouseY))
                colliding = False
                for block in blocks:
                    if block.colliderect(line_rect):
                        colliding = True
                for s in spikes:
                    if s.colliderect(line_rect):
                        colliding = True
                if not colliding:
                    screen.blit(line_img, line_rect)
            if player.curr_spell == 'hand' and not player.attacking:
                line_img = pygame.transform.scale(pygame.image.load(asset('line.png')), (600, 32))
                line = pygame.transform.rotate(line_img, angle)
                line_x = player.rect.centerx
                line_y = player.rect.centery
                line_rect = line.get_rect(center = (line_x - camera.offset.x, line_y - camera.offset.y))
                screen.blit(line, line_rect)
            
            screen.blit(
                pygame.transform.scale(player.image, (40, 40)),
                (
                    player.rect.x - camera.offset.x + player.shakeX,
                    player.rect.y - camera.offset.y + player.shakeY
                )
            )
            for f in fireballs:
                screen.blit(f.image, (f.rect.x - camera.offset.x, f.rect.y - camera.offset.y))
            for z in zaps:
                screen.blit(z.image, (z.rect.x - camera.offset.x, z.rect.y - camera.offset.y))
            for fr in freezes:
                screen.blit(fr.image, (fr.rect.x - camera.offset.x, fr.rect.y - camera.offset.y))
            for p in poisons:
                screen.blit(p.image, (p.rect.x - camera.offset.x, p.rect.y - camera.offset.y))
            for h in hands:
                screen.blit(h.image, (h.rect.x - camera.offset.x, h.rect.y - camera.offset.y))
            for d in darts:
                screen.blit(d.image, (d.rect.x - camera.offset.x, d.rect.y - camera.offset.y))
            for m in movingBlocks:
                screen.blit(m.image, (m.rect.x - camera.offset.x, m.rect.y - camera.offset.y))
            for e in enemies:
                screen.blit(e.image, (e.rect.x - camera.offset.x, e.rect.y - camera.offset.y))
                pygame.draw.rect(screen, (100, 100, 100), (e.rect.x - camera.offset.x, e.rect.y - camera.offset.y - 15, e.rect.width, 10))
                pygame.draw.rect(screen, (129, 255, 146), (e.rect.x - camera.offset.x, e.rect.y - camera.offset.y - 15, e.rect.width*(e.hp/e.max_hp), 10))
                if e.zapped and e.dmg_cooldown2 >= 15:
                    e.tick += 1
                    e.dmg_cooldown2 = 0
                    e.hp -= 1
                    screen.blit(e.zap[0], (e.rect.x - camera.offset.x, e.rect.y - camera.offset.y))
                    if e.tick == 3:
                        e.zapped = False
                if e.burned and e.dmg_cooldown2 >= 15:
                    e.tick += 1
                    e.dmg_cooldown2 = 0
                    e.hp -= 1
                    screen.blit(pygame.image.load(asset('burn.png')), (e.rect.x - camera.offset.x, e.rect.y - camera.offset.y))
                    if e.tick == 3:
                        e.burned = False
                if e.frozen:
                    screen.blit(pygame.image.load(asset('ice.png')), (e.rect.x - camera.offset.x - 5, e.rect.y - camera.offset.y - 5))
                    e.tick += 1
                    if e.tick == 30:
                        e.tick = 0
                        e.frozen = False
                if e.poisoned and e.dmg_cooldown2 >= 30:
                    e.tick += 1
                    e.dmg_cooldown2 = 0
                    e.hp -= 1
                    screen.blit(pygame.image.load(asset('poisoned.png')), (e.rect.x - camera.offset.x, e.rect.y - camera.offset.y))
                    if e.tick == 3:
                        e.poisoned = False
                        e.speed *= 2
                if e.rect.y > curr_level.height or e.rect.x > curr_level.width or e.rect.y < 0 or e.rect.x < 0:
                    e.die()
                        
            for e in explosions:
                screen.blit(
                    pygame.transform.scale(e.image, (40, 40)),
                    (
                        e.rect.x - camera.offset.x + player.shakeX,
                        e.rect.y - camera.offset.y + player.shakeY
                    )
                )

            spell1 = ImgButton(650, 220, asset(''+str(player.rotation[0])+'_button.png'))
            spell1.draw(screen)

            spell2 = ImgButton(650, 290, asset(''+str(player.rotation[1])+'_button.png'))
            spell2.draw(screen)

            if player.curr_spell == player.rotation[0]:
                screen.blit(selected, (650, 220))
            if player.curr_spell == player.rotation[1]:
                screen.blit(selected, (650, 290))

            if player.invis:
                player.ghost_timer += 1
                if player.ghost_timer >= 100:
                    player.invis = False
                    player.ghost_timer = 0
                    spellCurrCooldowns[player.curr_spell] = 0

            if player.attacking and player.curr_spell == 'heal':
                player.tick += 1
                if player.tick < 5:
                    screen.blit(pygame.image.load(asset('heal1.png')), (player.rect.x - camera.offset.x, player.rect.y - camera.offset.y))
                elif player.tick < 10:
                    screen.blit(pygame.image.load(asset('heal2.png')), (player.rect.x - camera.offset.x, player.rect.y - camera.offset.y))
                elif player.tick < 15:
                    screen.blit(pygame.image.load(asset('heal1.png')), (player.rect.x - camera.offset.x, player.rect.y - camera.offset.y))
                if player.tick >= 15:
                    player.attacking = False
                    spellCurrCooldowns[player.curr_spell] = 0
                    if player.hp < 100:
                        if player.hp > 70:
                            player.hp = 100
                        else:
                            player.hp += 30

            if pygame.mouse.get_pressed()[0]:
                if spell1.isClicked() and not player.attacking:
                    player.curr_spell = player.rotation[0]
                elif spell2.isClicked() and not player.attacking:
                    player.curr_spell = player.rotation[1]
                elif not (spell1.isClicked() or spell2.isClicked()) and not player.attacking:
                    if player.curr_spell == 'slash' and barwidths[player.rotation.index(player.curr_spell)] == 100:
                        player.frame_index = 0
                        player.frame_index2 = 0
                        player.attacking = True
                    if player.curr_spell == 'fireball' and barwidths[player.rotation.index(player.curr_spell)] == 100 and len(fireballs) < 1 and not player.attacking:
                        fireballs.add(Fireball(player.rect.centerx, player.rect.centery, mouseX+camera.offset.x, mouseY+camera.offset.y))
                        player.frame_index = 0
                        player.attacking = True
                        if (angle >= 90 and angle <= 180) or (angle <= -90 and angle >= -180):
                            player.flipped = True
                        else:
                            player.flipped = False
                    if player.curr_spell == 'dash' and barwidths[player.rotation.index(player.curr_spell)] == 100:
                        player.attacking = True
                    if player.curr_spell == 'shield' and barwidths[player.rotation.index(player.curr_spell)] == 100 and not player.shield:
                        player.shield = True
                        spellCurrCooldowns[player.curr_spell] = 0
                    if player.curr_spell == 'laser' and barwidths[player.rotation.index(player.curr_spell)] == 100 and not player.attacking:
                        player.attacking = True
                        spellCurrCooldowns[player.curr_spell] = 0
                        direction = (pygame.Vector2(mouseX+camera.offset.x, mouseY+camera.offset.y) - (player.rect.centerx, player.rect.centery)).normalize()
                        pos = player.rect.center - (direction * 20)
                        i = 0
                        if (angle >= 90 and angle <= 180) or (angle <= -90 and angle >= -180):
                            player.flipped = True
                        else:
                            player.flipped = False
                    if player.curr_spell == 'zap' and barwidths[player.rotation.index(player.curr_spell)] == 100 and len(zaps) < 1 and not player.attacking:
                        zaps.add(Zap(player.rect.centerx, player.rect.centery, mouseX+camera.offset.x, mouseY+camera.offset.y))
                        player.frame_index = 0
                        player.attacking = True
                        if (angle >= 90 and angle <= 180) or (angle <= -90 and angle >= -180):
                            player.flipped = True
                        else:
                            player.flipped = False
                    if player.curr_spell == 'heal' and barwidths[player.rotation.index(player.curr_spell)] == 100 and not player.attacking:
                        player.tick = 0
                        player.attacking = True
                    if player.curr_spell == 'burn' and barwidths[player.rotation.index(player.curr_spell)] == 100:
                        player.frame_index = 0
                        player.frame_index2 = 0
                        player.attacking = True
                    if player.curr_spell == 'freeze' and barwidths[player.rotation.index(player.curr_spell)] == 100 and len(freezes) < 1 and not player.attacking:
                        freezes.add(Freeze(player.rect.centerx, player.rect.centery, mouseX+camera.offset.x, mouseY+camera.offset.y))
                        player.frame_index = 0
                        player.attacking = True
                        if (angle >= 90 and angle <= 180) or (angle <= -90 and angle >= -180):
                            player.flipped = True
                        else:
                            player.flipped = False
                    if player.curr_spell == 'poison' and barwidths[player.rotation.index(player.curr_spell)] == 100 and not player.attacking:
                        poisons.add(Poison(player.rect.x, player.rect.y))
                        player.frame_index = 0
                        player.attacking = True
                    if player.curr_spell == 'charge' and barwidths[player.rotation.index(player.curr_spell)] == 100:
                        player.attacking = True
                        spellCurrCooldowns[player.curr_spell] = 0
                    if player.curr_spell == 'teleport' and barwidths[player.rotation.index(player.curr_spell)] == 100:
                        if not colliding:
                            img = player.image.copy()
                            img.set_alpha(120)
                            avgX = (mouseX+camera.offset.x + player.rect.x)//2
                            avgY = (mouseY+camera.offset.y + player.rect.y)//2
                            screen.blit(img, (avgX - camera.offset.x, avgY - camera.offset.y))
                            player.rect.center = mouseX, mouseY
                            spellCurrCooldowns[player.curr_spell] = 0
                    if player.curr_spell == 'ghost' and barwidths[player.rotation.index(player.curr_spell)] == 100 and not player.invis:
                        player.invis = True
                    if player.curr_spell == 'hand' and barwidths[player.rotation.index(player.curr_spell)] == 100 and len(hands) < 1 and not player.attacking:
                        hands.add(Hand(player.rect.centerx, player.rect.centery, mouseX, mouseY))
                        player.frame_index = 0
                        player.attacking = True
                        if (angle >= 90 and angle <= 180) or (angle <= -90 and angle >= -180):
                            player.flipped = True
                        else:
                            player.flipped = False

            if keys[pygame.K_1]:
                player.curr_spell = player.rotation[0]

            if keys[pygame.K_2]:
                player.curr_spell = player.rotation[1]

            if player.attacking and player.curr_spell == 'slash':
                player.frame_index2 += 1
                if player.frame_index2 >= len(player.slash_right)-1:
                    player.frame_index2 = 0
                player.slash_image = player.slash_left[player.frame_index2] if player.flipped else player.slash_right[player.frame_index2]
                screen.blit(
                    pygame.transform.scale(player.slash_image, (40, 40)),
                    (
                        player.slash_rect.x - camera.offset.x + player.shakeX,
                        player.slash_rect.y - camera.offset.y + player.shakeY
                    )
            )

            if player.attacking and player.curr_spell == 'burn':
                player.frame_index2 += 1
                if player.frame_index2 >= len(player.burn_right)-1:
                    player.frame_index2 = 0
                player.burn_image = player.burn_left[player.frame_index2] if player.flipped else player.burn_right[player.frame_index2]
                screen.blit(
                    pygame.transform.scale(player.burn_image, (40, 40)),
                    (
                        player.slash_rect.x - camera.offset.x + player.shakeX,
                        player.slash_rect.y - camera.offset.y + player.shakeY
                    )
            )

        if player.shield:
            screen.blit(player.shield_img, (player.rect.x-6-camera.offset.x, player.rect.y-6-camera.offset.y))

        pygame.draw.rect(screen, (100, 0, 0), (10, 50, 100, 30))
        pygame.draw.rect(screen, (255, 20, 20), (10, 50, barwidth, 30))
        pygame.draw.rect(screen, (100, 0, 0), (10, 90, 100, 30))
        pygame.draw.rect(screen, (255, 20, 20), (10, 90, barwidth2, 30))

        pygame.draw.rect(screen, (70, 70, 70), (10, 10, 210, 30))
        pygame.draw.rect(screen, health_color(player.hp, 100), (15, 15, player.hp*2, 20))
        drawText('HP: '+str(round(player.hp))+'/100', 115, 25, 20, (0, 0, 0))

        for l in lavas:
            if player.rect.colliderect(l):
                player.hp = 0

        if wave_on and len(enemies) <= 0:
            enemies_defeated = True
            player.regen = False
            wave_on = False

        if enemies_defeated:
            curr_wave += 1
            if curr_wave > survival_high_score:
                survival_high_score = curr_wave
            wave_timer = 180
            enemies_defeated = False

        if player.hp <= 0:
            pygame.mixer.music.pause()
            wave_on = False
            paused = True
            pygame.draw.rect(screen, (120, 52, 141), (160, 55, 400, 250))
            drawText('You Died', WIDTH//2, 100, 60, (255, 255, 255))
            buttons = []
            buttons_created = False
            if not testing_level:
                menu_button = Button(WIDTH//2-40, 150, 80, 60, 'Menu', 30)
                menu_button.draw(screen)
                retry_button = Button(WIDTH//2-40, 220, 80, 60, 'Retry', 30)
                retry_button.draw(screen)
                player.attacking = False
                if menu_button.isClicked():
                    player.reset()
                    enemies = pygame.sprite.Group()
                    movingBlocks = pygame.sprite.Group()
                    enemiesDrawn = False
                    movingBlocksDrawn = False
                    pygame.mixer.music.load(lobby)
                    pygame.mixer.music.play(-1)
                    audio = True
                    survival = False
                    menu = True
                if retry_button.isClicked():
                    player.reset()
                    player.rect.x, player.rect.y = curr_level.start
                    enemies = pygame.sprite.Group()
                    movingBlocks = pygame.sprite.Group()
                    enemiesDrawn = False
                    movingBlocksDrawn = False
                    paused = False
                    curr_level.find_spawners()
                    curr_wave = 1
                    wave_timer = 180
                    wave_on = False
                    pygame.mixer.music.unpause()
            else:
                edit_button = Button(WIDTH//2-40, 150, 80, 60, 'Editor', 25)
                edit_button.draw(screen)
                retry_button = Button(WIDTH//2-40, 220, 80, 60, 'Retry', 30)
                retry_button.draw(screen)
                player.attacking = False
                if edit_button.isClicked():
                    player.reset()
                    enemies = pygame.sprite.Group()
                    movingBlocks = pygame.sprite.Group()
                    enemiesDrawn = False
                    movingBlocksDrawn = False
                    pygame.mixer.music.load(lobby)
                    pygame.mixer.music.play(-1)
                    audio = True
                    game = False
                    edit = True
                    selected_x, selected_y = -60, -60
                    layers = [1, 2, 3]
                    active_layer = 3
                    layer_buttons_drawn = False
                    dragging = False
                    undo_stack = []
                    redo_stack = []
                if retry_button.isClicked():
                    player.reset()
                    door_img = door_img1
                    player.rect.x, player.rect.y = curr_level.start
                    enemies = pygame.sprite.Group()
                    movingBlocks = pygame.sprite.Group()
                    enemiesDrawn = False
                    movingBlocksDrawn = False
                    paused = False
                    wave_on = False

    drawText2('FPS: '+str(int(fps)), WIDTH-100, HEIGHT-35, 30, (255, 255, 255))
    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.VIDEORESIZE:
            WIDTH, HEIGHT = event.w, event.h
            screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        #if event.type == pygame.KEYDOWN:
        #    if event.key == pygame.K_F11:
        #        fullscreen = not fullscreen

        #        if fullscreen:
        #            screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
        #        else:
        #            screen = pygame.display.set_mode((WIDTH, HEIGHT))

        #    elif event.key == pygame.K_ESCAPE:
        #        fullscreen = False
         
    clock.tick(30)
    save()

pygame.mixer.music.stop()
pygame.quit()
exit()
sys.exit()
