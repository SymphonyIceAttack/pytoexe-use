import pygame
from sys import exit
from random import choice, randint

BEDROOM = 0
KITCHEN = 1
GAMEROOM = 2
FLAPPYBIRD = 3
MINIGAMEOVER = 4
SLEEP = 5

DEFAULT = 9
NOTENOUGHMONEY = 10
DRAG = 11
class Pou(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image1 = pygame.image.load("graphics/happy_pou.png")
        self.image2 = pygame.image.load("graphics/sad_pou.png")
        self.image3 = pygame.image.load("graphics/sick_pou.png")
        self.image4 = pygame.image.load("graphics/sleep_pou.png")

        self.image1 = pygame.transform.scale_by(self.image1,10.0)
        self.image2 = pygame.transform.scale_by(self.image2,10.0)
        self.image3 = pygame.transform.scale_by(self.image3,10.0)
        self.image4 = pygame.transform.scale_by(self.image4,10.0)

        self.image = pygame.image.load("graphics/happy_pou.png")
        self.image = pygame.transform.scale_by(self.image,10.0)
        self.rect = self.image.get_rect(center = (400,450))
    def change_appereance(self):
        global hunger
        if current_state == SLEEP:
            self.image = self.image4
        else:
            if hunger >= 255:
                self.image = self.image1
            elif hunger < 255 and hunger >= 125:
                self.image = self.image2
            elif hunger < 125 and hunger >= 0:
                self.image = self.image3
        
    def update(self):
        self.change_appereance()

class Button(pygame.sprite.Sprite):
    def __init__(self,type,pos,text):
        super().__init__()
        self.type = type
        self.pos = pos
        self.text = text

        if type == "RightArrow":
            self.image = pygame.image.load("graphics/right_arrow.png")
            self.image = pygame.transform.scale_by(self.image, 5.0)
            self.rect = self.image.get_rect(center = (pos))
        if type == "LeftArrow":
            self.image = pygame.image.load("graphics/right_arrow.png")
            self.image = pygame.transform.scale_by(self.image, 5.0)
            self.image = pygame.transform.flip(self.image, True, False)
            self.rect = self.image.get_rect(center = (pos))
        if type == "Box":
            self.image = pygame.Surface((200,100), pygame.SRCALPHA)
            self.image.fill("White")
            text_surf = my_font.render(text,False,"Black")
            self.image.blit(text_surf, (25,25))
            self.rect = self.image.get_rect(center = pos)
            
    def press(self):
        global current_state, last_done, screen, energy, coin, hunger, food_state
        mouse_pos = pygame.mouse.get_pos()
        mouse_button = pygame.mouse.get_pressed()
        if mouse_button[0]:
            if self.rect.collidepoint(mouse_pos):
                if self.type == "Box" and self.text == "Play" and energy > 0:
                    current_state = FLAPPYBIRD
                    screen = pygame.display.set_mode((1600,800))

                if self.type == "Box" and self.text == "Sleep":
                    right_now = pygame.time.get_ticks()
                    current_time = right_now - last_done
                    if current_time >= 500:
                        last_done = pygame.time.get_ticks()
                        if current_state == BEDROOM and energy < 510:
                            current_state = SLEEP
                        else:
                            current_state = BEDROOM
                
                if self.type == "Box" and self.text == "Food":
                    right_now = pygame.time.get_ticks()
                    current_time = right_now - last_done
                    if current_time >= 500:
                        last_done = pygame.time.get_ticks()
                        if coin >= 10:
                            food_state = DRAG
                            coin -= 10
                            if hunger <= 460:
                                hunger += 50
                            else:
                                hunger = 510
                        else:
                            food_state = NOTENOUGHMONEY

                if self.type == "RightArrow" or self.type == "LeftArrow":
                    right_now = pygame.time.get_ticks()
                    current_time = right_now - last_done
                    if current_time >= 500:
                        last_done = pygame.time.get_ticks()
                        if self.type == "RightArrow":
                            if current_state == 2:
                                current_state = 0
                            else:
                                current_state += 1
                        if self.type == "LeftArrow":
                            if current_state == 0:
                                current_state = 2
                            else:
                                current_state -= 1
    def update(self):
        self.press()

class Text(pygame.sprite.Sprite):
    def __init__(self,type,pos, text):
        super().__init__()
        self.type = type
        self.pos = pos
        self.text = text
        if self.type == "Text":
            self.image = my_font.render(text,False,"Black")
            self.rect = self.image.get_rect(center = pos)
        if self.type == "SmallText":
            self.image = small_font.render(text, False, "Black")
            self.rect = self.image.get_rect(center = pos)

class Bar(pygame.sprite.Sprite):
    def __init__(self,type):
        super().__init__()
        self.type = type
        self.color = (0,255,0)

        if type == "Hunger":
            self.image = pygame.Surface((102,25))
            self.image.fill(self.color)
            self.rect = self.image.get_rect(topleft = (200,50))
        if type == "Energy":
            self.image = pygame.Surface((102,25))
            self.image.fill(self.color)
            self.rect = self.image.get_rect(topleft = (500,50))
        if type == "Coin":
            self.image = pygame.image.load("graphics/coin.png")
            self.image = pygame.transform.scale_by(self.image, 5.0)
            self.rect = self.image.get_rect(topleft = (650,40))
    def bar_change(self):
        global hunger, energy
        if self.type == "Hunger":
            if hunger >= 255:
                red = abs(hunger - 510)
                self.color = (red, 255, 0)
            elif hunger > 1:
                green = hunger
                self.color = (255, green, 0)
            elif hunger <= 0:
                pygame.quit()
                exit()
            self.image = pygame.Surface((hunger/5, 25))
            self.image.fill(self.color)
        if self.type == "Energy":
            if energy >= 255:
                red = abs(energy - 510)
                self.color = (red, 255, 0)
            elif energy > 1:
                green = energy
                self.color = (255, green, 0)
            self.image = pygame.Surface((energy/5, 25))
            self.image.fill(self.color)
    def update(self):
        self.bar_change()

class Obstacles(pygame.sprite.Sprite):
    def __init__(self, type, pos):
        super().__init__()
        self.type = type
        self.pos = pos

        self.can_score = True

        if self.type == "Cloud":
            self.image = pygame.Surface((200,100))
            self.image.fill("White")
            self.rect = self.image.get_rect(topleft = pos)
        if self.type == "Obstacle":
            self.image = pygame.Surface((50,1000))
            self.image.fill("#00A531")
            self.rect = self.image.get_rect(topleft = self.pos)
    
    def move(self):
        if self.type == "Cloud":
            self.rect.x -= 2
        elif self.type == "Obstacle":
            self.rect.x -= 5
        if self.rect.right <= 0:
            self.kill()
    def update(self):
        global score
        self.move()
        if self.rect.left < 200 and self.can_score:
            score += 0.5
            self.can_score = False

def lose_hunger(last_done):
    global hunger
    right_now = pygame.time.get_ticks()
    current_time = right_now - last_done
    if current_time >= 500:
        hunger -= 1
        last_done = pygame.time.get_ticks()
    return last_done
    
def lose_energy(last_done):
    global energy
    right_now = pygame.time.get_ticks()
    current_time = right_now - last_done
    if current_time >= 250:
        if current_state == FLAPPYBIRD:
            energy -= 1
            last_done = pygame.time.get_ticks()
        elif current_state == SLEEP:
            energy += 1
            last_done = pygame.time.get_ticks()
    return last_done
    
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.image.load("graphics/happy_pou.png")
        self.image = pygame.transform.scale_by(self.image, 3.0)
        self.rect = self.image.get_rect(topleft = (200,300))

        self.y_speed = 0
    def player_input(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.y_speed = -20
    def collision(self, obstacles):
        global current_state, flappybird_reset
        for obstacle in obstacles:
            if self.rect.colliderect(obstacle.rect):
                flappybird_reset = True
                current_state = MINIGAMEOVER
    def update(self):
        global current_state, flappybird_reset
        self.player_input(events)
        self.collision(obstacle_group)
        self.y_speed += 1
        self.rect.y += self.y_speed
        if self.rect.bottom >= 800 or self.rect.top <= 0:
            flappybird_reset = True
            current_state = MINIGAMEOVER



pygame.init()
screen = pygame.display.set_mode((800,800))
pygame.display.set_caption("Pou")
clock = pygame.time.Clock()
my_font = pygame.font.Font("font/Pixeltype.ttf",100)
small_font = pygame.font.Font("font/Pixeltype.ttf", 50)
current_state = 0
food_state = DEFAULT
last_done = pygame.time.get_ticks()
last_hunger_done = pygame.time.get_ticks()
last_energy_done = pygame.time.get_ticks()
hunger = 510
energy = 510
score = 0
flappybird_reset = False
coin = 10

pou_group = pygame.sprite.GroupSingle()
pou_group.add(Pou())

button_group = pygame.sprite.Group()

button_group.add(Button("RightArrow",(675,400),""))
button_group.add(Button("LeftArrow",(100,400),""))

food_button_group = pygame.sprite.GroupSingle()
food_button_group.add(Button("Box",(400,725), "Food"))

sleep_button_group = pygame.sprite.GroupSingle()
sleep_button_group.add(Button("Box",(400,725), "Sleep"))

play_button_group = pygame.sprite.GroupSingle()
play_button_group.add(Button("Box",(400,725), "Play"))

bedroom_text = pygame.sprite.GroupSingle()
bedroom_text.add(Text("Text",(400,200), "Bedroom"))

kitchen_text = pygame.sprite.GroupSingle()
kitchen_text.add(Text("Text",(400,200), "Kitchen"))

gameroom_text = pygame.sprite.GroupSingle()
gameroom_text.add(Text("Text",(400,200), "Game Room"))

hunger_text = pygame.sprite.GroupSingle()
hunger_text.add(Text("SmallText",(125,70),"Hunger: "))

energy_text = pygame.sprite.GroupSingle()
energy_text.add(Text("SmallText",(425,70),"Energy: "))

obstacle_group = pygame.sprite.Group()

player_group = pygame.sprite.GroupSingle()
player_group.add(Player())

bar_group = pygame.sprite.Group()
bar_group.add(Bar("Hunger"))
bar_group.add(Bar("Energy"))
bar_group.add(Bar("Coin"))

cloud_event = pygame.USEREVENT + 1
pygame.time.set_timer(cloud_event, 5000)

obstacle_event = pygame.USEREVENT + 2
pygame.time.set_timer(obstacle_event, 2000)

while True:
    events = pygame.event.get()
    for event in events:
        if current_state == FLAPPYBIRD:
            if event.type == cloud_event:
                obstacle_group.add(Obstacles("Cloud",(1600,choice([100,125,150,175,200,225,250,275,300]))))
            if event.type == obstacle_event:
                rand_obstacle_pos = randint(0,400)
                obstacle_group.add(Obstacles("Obstacle",(1600,rand_obstacle_pos + 300)))
                obstacle_group.add(Obstacles("Obstacle",(1600,rand_obstacle_pos - 1000)))
        if current_state == MINIGAMEOVER:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    current_state = FLAPPYBIRD
                    coin += int(final_score)
                    player_group.add(Player())
                if event.key == pygame.K_RETURN:
                    current_state = GAMEROOM
                    coin += int(final_score)
                    player_group.add(Player())
                    screen = pygame.display.set_mode((800,800))
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
    if current_state == BEDROOM:
        screen.fill("#00C0C0")
        bedroom_text.draw(screen)
        hunger_text.draw(screen)
        energy_text.draw(screen)
        button_group.draw(screen)
        button_group.update()
        sleep_button_group.draw(screen)
        sleep_button_group.update()
        pou_group.draw(screen)
        pou_group.update()
        bar_group.draw(screen)
        bar_group.update()
        rect = pygame.Rect(195,45,110,35)
        pygame.draw.rect(screen,"Black",rect,5)
        energy_rect = pygame.Rect(495,45,110,35)
        pygame.draw.rect(screen,"Black",energy_rect,5)
        button_rect = pygame.Rect(300,675,200,100)
        pygame.draw.rect(screen,"Black",button_rect,5)

        coin_surf = small_font.render(f"{coin}",False,"Black")
        coin_rect = coin_surf.get_rect(topleft = (700,50))
        screen.blit(coin_surf,coin_rect)

    elif current_state == SLEEP:
        if energy >= 510:
            energy = 510
            current_state = BEDROOM
        screen.fill("#00C0C0")
        bedroom_text.draw(screen)
        hunger_text.draw(screen)
        energy_text.draw(screen)
        sleep_button_group.draw(screen)
        sleep_button_group.update()
        pou_group.draw(screen)
        pou_group.update()
        bar_group.draw(screen)
        bar_group.update()
        rect = pygame.Rect(195,45,110,35)
        pygame.draw.rect(screen,"Black",rect,5)
        energy_rect = pygame.Rect(495,45,110,35)
        pygame.draw.rect(screen,"Black",energy_rect,5)
        button_rect = pygame.Rect(300,675,200,100)
        pygame.draw.rect(screen,"Black",button_rect,5)

        shade = pygame.Surface((800,800), pygame.SRCALPHA)
        shade.fill((66,66,66,160))
        shade_rect = shade.get_rect(topleft = (0,0))
        screen.blit(shade,shade_rect)

        last_energy_done = lose_energy(last_energy_done)

    elif current_state == KITCHEN:
        screen.fill("#CC0000")
        kitchen_text.draw(screen)
        hunger_text.draw(screen)
        energy_text.draw(screen)
        pou_group.draw(screen)
        pou_group.update()
        button_group.draw(screen)
        button_group.update()
        food_button_group.draw(screen)
        food_button_group.update()
        bar_group.draw(screen)
        bar_group.update()
        rect2 = pygame.Rect(195,45,110,35)
        pygame.draw.rect(screen,"Black",rect2,5)
        energy_rect2 = pygame.Rect(495,45,110,35)
        pygame.draw.rect(screen,"Black",energy_rect,5)
        button_rect2 = pygame.Rect(300,675,200,100)
        pygame.draw.rect(screen,"Black",button_rect2,5)

        if food_state == DEFAULT:
            food_surf = small_font.render("10 coins",False,"Black")
            food_surf2 = small_font.render("for a banana",False,"Black")
        elif food_state == DRAG:
            food_surf = small_font.render("You gave pou",False,"Black")
            food_surf2 = small_font.render("a banana",False,"Black")
        elif food_state == NOTENOUGHMONEY:
            if coin >= 10:
                food_state = DEFAULT
            else:
                food_surf = small_font.render("Not enough",False,"Black")
                food_surf2 = small_font.render("money",False,"Black")
        food_rect = food_surf.get_rect(topleft = (550,700))
        screen.blit(food_surf,food_rect)
        food_rect2 = food_surf2.get_rect(topleft = (550,750))
        screen.blit(food_surf2,food_rect2)

        coin_surf = small_font.render(f"{coin}",False,"Black")
        coin_rect = coin_surf.get_rect(topleft = (700,50))
        screen.blit(coin_surf,coin_rect)
        
    elif current_state == GAMEROOM:
        screen.fill("#1DAF00FF")
        gameroom_text.draw(screen)
        hunger_text.draw(screen)
        energy_text.draw(screen)
        pou_group.draw(screen)
        pou_group.update()
        button_group.draw(screen)
        button_group.update()
        play_button_group.draw(screen)
        play_button_group.update()
        bar_group.draw(screen)
        bar_group.update()
        rect3 = pygame.Rect(195,45,110,35)
        pygame.draw.rect(screen,"Black",rect3,5)
        energy_rect3 = pygame.Rect(495,45,110,35)
        pygame.draw.rect(screen,"Black",energy_rect3,5)
        button_rect3 = pygame.Rect(300,675,200,100)
        pygame.draw.rect(screen,"Black",button_rect3,5)

        coin_surf = small_font.render(f"{coin}",False,"Black")
        coin_rect = coin_surf.get_rect(topleft = (700,50))
        screen.blit(coin_surf,coin_rect)

    elif current_state == FLAPPYBIRD:
        if energy > 0:
            screen.fill("#00ACE0")
            obstacle_group.draw(screen)
            obstacle_group.update()
            player_group.draw(screen)
            player_group.update()
            score_text = my_font.render(f"Score: {int(score)}",False,"Black")
            score_text_rect = score_text.get_rect(topleft = (1300,75))
            screen.blit(score_text,score_text_rect)
            last_energy_done = lose_energy(last_energy_done)
        else:
            current_state = GAMEROOM
            coin += int(final_score)
            player_group.add(Player())
            screen = pygame.display.set_mode((800,800))

    
    elif current_state == MINIGAMEOVER:
        screen.fill("#00A8A0")
        message1_text = my_font.render(f"{int(final_score)} coins gained",False,"Black")
        message1_text_rect = message1_text.get_rect(center = (800,200))
        screen.blit(message1_text,message1_text_rect)

        message2_text = my_font.render("Press Space To Play Again",False,"Black")
        message2_text_rect = message2_text.get_rect(center = (800,400))
        screen.blit(message2_text,message2_text_rect)

        message3_text = my_font.render("Press Enter To Go To Game Toom",False,"Black")
        message3_text_rect = message3_text.get_rect(center = (800,600))
        screen.blit(message3_text,message3_text_rect)

    if flappybird_reset == True:
        final_score = score
        score = 0
        obstacle_group.empty()
        player_group.empty()
        flappybird_reset = False

    last_hunger_done = lose_hunger(last_hunger_done)

    pygame.display.update()
    clock.tick(60)