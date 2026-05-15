import pygame, sys, math, random, json, os
pygame.init()

W, H = 1000, 660
FPS = 60
SAVE_FILE = "savegame.json"
ARENA = pygame.Rect(50, 50, W-100, H-100)

WHITE=(255,255,255);BLACK=(0,0,0);RED=(220,50,50);YELLOW=(255,220,50)
ORANGE=(255,140,0);GRAY=(120,120,120);DGRAY=(50,50,50);BGCOL=(18,20,35)
PANELC=(28,30,50);ACCENT=(80,180,255);HGREEN=(60,210,100);HRED=(220,60,60)
TEAL=(50,200,180);GOLD=(255,200,0);PURPLE=(180,80,220);PINK=(255,100,180)

ENEMY_COLORS = [HRED,(255,120,0),(180,80,220),(255,100,180),(0,220,180)]

screen=pygame.display.set_mode((W,H))
pygame.display.set_caption("Gunfight Arena")
clock=pygame.time.Clock()
fBIG=pygame.font.SysFont("Arial",52,bold=True)
fMED=pygame.font.SysFont("Arial",30,bold=True)
fSM=pygame.font.SysFont("Arial",22)
fTINY=pygame.font.SysFont("Arial",16)

def rdraw(surf,color,rect,r=10,a=255):
    s=pygame.Surface((rect[2],rect[3]),pygame.SRCALPHA)
    pygame.draw.rect(s,(*color,a),(0,0,rect[2],rect[3]),border_radius=r)
    surf.blit(s,(rect[0],rect[1]))

def tc(surf,text,font,col,cx,cy):
    t=font.render(text,True,col)
    surf.blit(t,(cx-t.get_width()//2,cy-t.get_height()//2))

def hbar(surf,x,y,w,h,val,mxv,col):
    pygame.draw.rect(surf,DGRAY,(x,y,w,h),border_radius=5)
    fw=int(w*max(0,val)/mxv)
    if fw>0: pygame.draw.rect(surf,col,(x,y,fw,h),border_radius=5)
    pygame.draw.rect(surf,WHITE,(x,y,w,h),2,border_radius=5)

def make_btn(surf,lbl,font,col,cx,cy,bw=270,bh=42):
    mx,my=pygame.mouse.get_pos()
    r=pygame.Rect(cx-bw//2,cy-bh//2,bw,bh)
    hov=r.collidepoint(mx,my)
    bg=tuple(c//2 for c in col) if hov else tuple(c//4 for c in col)
    rdraw(surf,bg,r,10)
    pygame.draw.rect(surf,col,r,2,border_radius=10)
    tc(surf,lbl,font,WHITE if hov else col,cx,cy)
    return r

class Toast:
    def __init__(self): self.msg=""; self.t=0
    def show(self,msg,f=140): self.msg=msg; self.t=f
    def update(self): self.t=max(0,self.t-1)
    def draw(self,surf):
        if not self.t: return
        a=min(255,self.t*4)
        s=pygame.Surface((340,44),pygame.SRCALPHA)
        pygame.draw.rect(s,(30,170,110,a),(0,0,340,44),border_radius=10)
        pygame.draw.rect(s,(255,255,255,a),(0,0,340,44),2,border_radius=10)
        t=fSM.render(self.msg,True,(255,255,255))
        s.blit(t,(170-t.get_width()//2,22-t.get_height()//2))
        surf.blit(s,(W//2-170,H-68))

class Bullet:
    SPD=11;RAD=5
    def __init__(self,x,y,ang,owner):
        self.x=float(x);self.y=float(y)
        self.dx=math.cos(ang)*self.SPD;self.dy=math.sin(ang)*self.SPD
        self.owner=owner;self.alive=True
    def update(self,obs):
        self.x+=self.dx;self.y+=self.dy
        if not(52<self.x<W-52 and 52<self.y<H-52):self.alive=False;return
        for o in obs:
            if o.rect.collidepoint(self.x,self.y):self.alive=False;return
    def draw(self,surf):
        c=YELLOW if self.owner=="player" else ORANGE
        pygame.draw.circle(surf,c,(int(self.x),int(self.y)),self.RAD)
        pygame.draw.circle(surf,WHITE,(int(self.x),int(self.y)),self.RAD,1)

class Obstacle:
    def __init__(self,x,y,w,h): self.rect=pygame.Rect(x,y,w,h)
    def draw(self,surf):
        rdraw(surf,(55,60,88),self.rect,6)
        pygame.draw.rect(surf,ACCENT,self.rect,2,border_radius=6)

class Particle:
    def __init__(self,x,y,col):
        self.x=float(x);self.y=float(y);self.col=col
        self.vx=random.uniform(-3,3);self.vy=random.uniform(-4,0)
        self.life=random.randint(15,35);self.ml=self.life
    def update(self): self.x+=self.vx;self.y+=self.vy;self.vy+=0.2;self.life-=1
    def draw(self,surf):
        a=int(255*self.life/self.ml);r=max(1,int(4*self.life/self.ml))
        s=pygame.Surface((r*2,r*2),pygame.SRCALPHA)
        pygame.draw.circle(s,(*self.col,a),(r,r),r)
        surf.blit(s,(int(self.x)-r,int(self.y)-r))

# PowerUp levels: bullets count -> (label, colour)
PU_LEVELS = {2:("x2",(80,220,255)), 3:("x3",(255,200,50)), 5:("x5",(220,80,255))}

class PowerUp:
    RAD = 18
    LIFETIME = 600   # frames before despawn
    COLLECT_DIST = 30

    def __init__(self, x, y, count):
        self.x=float(x); self.y=float(y)
        self.count=count
        self.label, self.col = PU_LEVELS[count]
        self.alive=True
        self.age=0
        self.bob_offset=random.uniform(0, math.pi*2)   # random phase

    def update(self):
        self.age+=1
        if self.age>=self.LIFETIME: self.alive=False

    def collect_check(self, player):
        if math.hypot(player.x-self.x, player.y-self.y) < self.COLLECT_DIST+player.SZ//2:
            self.alive=False
            return True
        return False

    def draw(self, surf):
        t = self.age / FPS
        bob = math.sin(t*3 + self.bob_offset) * 5
        cx, cy = int(self.x), int(self.y + bob)
        pulse = 0.5 + 0.5*math.sin(t*4 + self.bob_offset)
        glow_r = int(self.RAD + 10 + pulse*8)
        # outer glow rings
        for i in range(3, 0, -1):
            a = int(40*i*pulse)
            gr = glow_r + i*5
            gs = pygame.Surface((gr*2, gr*2), pygame.SRCALPHA)
            pygame.draw.circle(gs, (*self.col, a), (gr, gr), gr)
            surf.blit(gs, (cx-gr, cy-gr))
        # spinning ring
        for i in range(8):
            ang = t*2 + i*math.pi/4
            rx = cx + int(math.cos(ang)*(self.RAD+4))
            ry = cy + int(math.sin(ang)*(self.RAD+4))
            pygame.draw.circle(surf, self.col, (rx, ry), 3)
        # main circle
        pygame.draw.circle(surf, (30,30,50), (cx,cy), self.RAD)
        pygame.draw.circle(surf, self.col, (cx,cy), self.RAD, 3)
        # label text
        lbl = fSM.render(self.label, True, self.col)
        surf.blit(lbl, (cx-lbl.get_width()//2, cy-lbl.get_height()//2))
        # lifetime bar underneath
        frac = 1 - self.age/self.LIFETIME
        bw = self.RAD*2
        pygame.draw.rect(surf, DGRAY, (cx-self.RAD, cy+self.RAD+4, bw, 4), border_radius=2)
        fw = int(bw*frac)
        if fw>0:
            pygame.draw.rect(surf, self.col, (cx-self.RAD, cy+self.RAD+4, fw, 4), border_radius=2)

class Character:
    SZ=28;SPD=4;HP=100;FD=22
    def __init__(self,x,y,col,is_player=True):
        self.x=float(x);self.y=float(y);self.col=col;self.is_player=is_player
        self.hp=self.HP;self.bullets=[];self.ft=0;self.alive=True
        self.angle=0.0;self.parts=[]
    @property
    def rect(self): return pygame.Rect(int(self.x)-self.SZ//2,int(self.y)-self.SZ//2,self.SZ,self.SZ)
    def move(self,dx,dy,obs,others):
        nx=self.x+dx*self.SPD;ny=self.y+dy*self.SPD
        nr=pygame.Rect(int(nx)-self.SZ//2,int(ny)-self.SZ//2,self.SZ,self.SZ)
        if not ARENA.contains(nr): return
        for o in obs:
            if nr.colliderect(o.rect): return
        for other in others:
            if nr.colliderect(other): return
        self.x,self.y=nx,ny
    def shoot(self, bullet_count=1):
        if self.ft<=0:
            owner="player" if self.is_player else "enemy"
            if bullet_count==1:
                self.bullets.append(Bullet(self.x,self.y,self.angle,owner))
            else:
                # spread angles symmetrically around aim angle
                spread = 0.18   # radians between each bullet
                offsets=[]
                if bullet_count%2==1:  # odd: centre + symmetric pairs
                    offsets=[0]+[s*spread*i for i in range(1,(bullet_count+1)//2) for s in(-1,1)]
                else:  # even: symmetric pairs, no centre
                    offsets=[s*spread*(i+0.5) for i in range(bullet_count//2) for s in(-1,1)]
                offsets=offsets[:bullet_count]
                for off in offsets:
                    self.bullets.append(Bullet(self.x,self.y,self.angle+off,owner))
            self.ft=self.FD
    def hit(self,dmg):
        self.hp=max(0,self.hp-dmg)
        if self.hp==0: self.alive=False
        for _ in range(8): self.parts.append(Particle(self.x,self.y,RED))
    def update(self,obs):
        self.ft=max(0,self.ft-1)
        for b in self.bullets[:]:
            b.update(obs)
            if not b.alive: self.bullets.remove(b)
        for p in self.parts[:]:
            p.update()
            if p.life<=0: self.parts.remove(p)
    def draw(self,surf):
        r=self.SZ//2;cx,cy=int(self.x),int(self.y)
        pygame.draw.circle(surf,self.col,(cx,cy),r)
        pygame.draw.circle(surf,WHITE,(cx,cy),r,2)
        gx=cx+int(math.cos(self.angle)*(r+9));gy=cy+int(math.sin(self.angle)*(r+9))
        pygame.draw.line(surf,WHITE,(cx,cy),(gx,gy),4)
        pygame.draw.circle(surf,YELLOW,(gx,gy),4)
        for ao in(-0.45,0.45):
            ex=cx+int(math.cos(self.angle+ao)*10);ey=cy+int(math.sin(self.angle+ao)*10)
            pygame.draw.circle(surf,WHITE,(ex,ey),4);pygame.draw.circle(surf,BLACK,(ex,ey),2)
        for b in self.bullets: b.draw(surf)
        for p in self.parts: p.draw(surf)

class Enemy(Character):
    SZ=28;SPD=2.4;HP=100;FD=55
    def __init__(self,x,y,col=None):
        super().__init__(x,y,col or HRED,False)
        self.mvt=0;self.mdx=0;self.mdy=0
    @staticmethod
    def _los(x1,y1,x2,y2,obs):
        def c2(ax,ay,bx,by): return ax*by-ay*bx
        def hit(p1,p2,p3,p4):
            d1=c2(p4[0]-p3[0],p4[1]-p3[1],p1[0]-p3[0],p1[1]-p3[1])
            d2=c2(p4[0]-p3[0],p4[1]-p3[1],p2[0]-p3[0],p2[1]-p3[1])
            d3=c2(p2[0]-p1[0],p2[1]-p1[1],p3[0]-p1[0],p3[1]-p1[1])
            d4=c2(p2[0]-p1[0],p2[1]-p1[1],p4[0]-p1[0],p4[1]-p1[1])
            return((d1>0)!=(d2>0))and((d3>0)!=(d4>0))
        for o in obs:
            tl=(o.rect.left,o.rect.top);tr=(o.rect.right,o.rect.top)
            br=(o.rect.right,o.rect.bottom);bl=(o.rect.left,o.rect.bottom)
            for a,b in[(tl,tr),(tr,br),(br,bl),(bl,tl)]:
                if hit((x1,y1),(x2,y2),a,b): return True
        return False
    def ai_update(self,player,obs,others):
        px,py=player.x,player.y
        self.angle=math.atan2(py-self.y,px-self.x)
        dist=math.hypot(px-self.x,py-self.y)
        can_see=not self._los(self.x,self.y,px,py,obs)
        other_rects=[o.rect for o in others if o is not self]
        if can_see:
            if self.ft<=0: self.shoot()
            if dist>260: self.move(math.cos(self.angle),math.sin(self.angle),obs,other_rects+[player.rect])
            elif dist<160: self.move(-math.cos(self.angle),-math.sin(self.angle),obs,other_rects+[player.rect])
            else:
                sa=self.angle+math.pi/2
                self.move(math.cos(sa)*0.6,math.sin(sa)*0.6,obs,other_rects+[player.rect])
        else:
            if self.ft<=0 and random.random()<0.25: self.shoot()
            self.mvt-=1
            if self.mvt<=0:
                a=random.uniform(0,2*math.pi)
                self.mdx=math.cos(a);self.mdy=math.sin(a);self.mvt=random.randint(25,55)
            self.move(self.mdx,self.mdy,obs,other_rects+[player.rect])

def make_obs():
    return[Obstacle(W//2-45,H//2-65,90,130),Obstacle(230,190,90,32),
           Obstacle(660,370,90,32),Obstacle(290,420,32,90),Obstacle(660,155,32,90)]

ENEMY_SPAWNS=[(W-130,H//2),(W-130,H//2-110),(W-130,H//2+110),(W-200,H//2-60),(W-200,H//2+60)]

class Game:
    def __init__(self):
        self.rtw=5;self.pw=0;self.ew=0
        self.num_enemies=1;self.sel_rounds=5;self.sel_enemies=1
        self.state="menu";self.obs=make_obs()
        self._new_round()
        self._menu_btns=[];self._pause_btns=[];self._go_btns=[]
        self.toast=Toast();self._arrow_y=0;self._earrow_y=0

    def _new_round(self):
        self.player=Character(130,H//2,ACCENT)
        self.enemies=[Enemy(ENEMY_SPAWNS[i][0],ENEMY_SPAWNS[i][1],ENEMY_COLORS[i%len(ENEMY_COLORS)])
                      for i in range(self.num_enemies)]
        self.rw=None;self.ret=0
        self.bullet_count=1        # player current bullet power level
        self.pu_flash=0            # flash timer on collect
        self.powerups=[]           # active power-up items
        self.pu_spawn_timer=180    # first spawn after 3 s
        self._spawn_powerup()

    def save(self):
        with open(SAVE_FILE,"w") as f:
            json.dump({"pw":self.pw,"ew":self.ew,"rtw":self.rtw,"ne":self.num_enemies},f)
        self.toast.show("  Game Saved!")

    def load(self):
        if not os.path.exists(SAVE_FILE): self.toast.show("  No save file found!"); return
        with open(SAVE_FILE) as f: d=json.load(f)
        self.pw=d.get("pw",0);self.ew=d.get("ew",0)
        self.rtw=d.get("rtw",5);self.num_enemies=d.get("ne",1)
        self.sel_rounds=self.rtw;self.sel_enemies=self.num_enemies
        self._new_round();self.state="playing";self.toast.show("  Game Loaded!")

    def _spawn_powerup(self):
        # pick a random arena position away from walls and obstacles
        for _ in range(30):
            x=random.randint(ARENA.left+40, ARENA.right-40)
            y=random.randint(ARENA.top+40, ARENA.bottom-40)
            pr=pygame.Rect(x-PowerUp.RAD,y-PowerUp.RAD,PowerUp.RAD*2,PowerUp.RAD*2)
            if any(pr.colliderect(o.rect) for o in self.obs): continue
            count=random.choice([2,3,5])
            self.powerups.append(PowerUp(x,y,count))
            break

    def restart(self):
        self.pw=0;self.ew=0;self._new_round();self.state="playing"

    def update(self):
        self.toast.update()
        if self.state=="round_end":
            self.ret-=1
            if self.ret<=0:
                if self.pw>=self.rtw or self.ew>=self.rtw: self.state="game_over"
                else: self._new_round();self.state="playing"
            return
        if self.state!="playing": return
        keys=pygame.key.get_pressed()
        dx=(keys[pygame.K_d]or keys[pygame.K_RIGHT])-(keys[pygame.K_a]or keys[pygame.K_LEFT])
        dy=(keys[pygame.K_s]or keys[pygame.K_DOWN])-(keys[pygame.K_w]or keys[pygame.K_UP])
        if dx or dy:
            ln=math.hypot(dx,dy) or 1
            self.player.move(dx/ln,dy/ln,self.obs,[e.rect for e in self.enemies])
        mx,my=pygame.mouse.get_pos()
        self.player.angle=math.atan2(my-self.player.y,mx-self.player.x)
        if pygame.mouse.get_pressed()[0] or keys[pygame.K_SPACE]: self.player.shoot(self.bullet_count)
        # power-up spawn timer
        self.pu_spawn_timer-=1
        if self.pu_spawn_timer<=0 and len(self.powerups)<3:
            self._spawn_powerup()
            self.pu_spawn_timer=random.randint(300,480)   # 5-8 s
        # update power-ups and check collection
        for pu in self.powerups[:]:
            pu.update()
            if not pu.alive: self.powerups.remove(pu); continue
            if pu.collect_check(self.player):
                self.powerups.remove(pu)
                self.bullet_count=pu.count
                self.pu_flash=90
                self.toast.show(f"  BULLET UPGRADE: {pu.label}  x{pu.count} shots!", 150)
        if self.pu_flash>0: self.pu_flash-=1
        self.player.update(self.obs)
        for e in self.enemies:
            if not e.alive:
                e.bullets.clear()   # remove bullets from dead enemies immediately
                continue
            e.ai_update(self.player,self.obs,self.enemies)
            e.update(self.obs)
            if not self.player.alive: continue
            for b in e.bullets[:]:
                if b.alive and self.player.rect.collidepoint(b.x,b.y):
                    self.player.hit(10);b.alive=False
        for b in self.player.bullets[:]:
            for e in self.enemies:
                if b.alive and e.alive and e.rect.collidepoint(b.x,b.y):
                    e.hit(10);b.alive=False
        alive_enemies=[e for e in self.enemies if e.alive]
        # only trigger round end once, and only if enemies list is populated
        if self.rw is None and self.enemies:
            if not self.player.alive:
                self.ew+=1;self.rw="enemy";self.ret=160;self.state="round_end"
            elif not alive_enemies:
                self.pw+=1;self.rw="player";self.ret=160;self.state="round_end"

    def event(self,ev):
        if ev.type==pygame.KEYDOWN:
            k=ev.key
            if self.state=="playing":
                if k in(pygame.K_ESCAPE,pygame.K_p): self.state="paused"
            elif self.state=="paused":
                if k in(pygame.K_ESCAPE,pygame.K_p): self.state="playing"
                elif k==pygame.K_r: self.restart()
                elif k==pygame.K_s: self.save()
                elif k==pygame.K_m: self.state="menu"
            elif self.state=="game_over":
                if k==pygame.K_r: self.restart()
                elif k==pygame.K_m: self.state="menu"
                elif k==pygame.K_q: pygame.quit();sys.exit()
            elif self.state=="menu":
                if k==pygame.K_LEFT: self.sel_rounds=max(1,self.sel_rounds-1)
                if k==pygame.K_RIGHT: self.sel_rounds=min(20,self.sel_rounds+1)
        if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
            mp=ev.pos
            if self.state=="menu":
                ay=self._arrow_y
                if pygame.Rect(W//2-120,ay-22,44,44).collidepoint(mp): self.sel_rounds=max(1,self.sel_rounds-1)
                if pygame.Rect(W//2+76,ay-22,44,44).collidepoint(mp): self.sel_rounds=min(20,self.sel_rounds+1)
                eay=self._earrow_y
                if pygame.Rect(W//2-120,eay-22,44,44).collidepoint(mp): self.sel_enemies=max(1,self.sel_enemies-1)
                if pygame.Rect(W//2+76,eay-22,44,44).collidepoint(mp): self.sel_enemies=min(5,self.sel_enemies+1)
                for lbl,r in self._menu_btns:
                    if r.collidepoint(mp):
                        if "START" in lbl: self.rtw=self.sel_rounds;self.num_enemies=self.sel_enemies;self.restart()
                        elif "LOAD" in lbl: self.load()
                        elif "QUIT" in lbl: pygame.quit();sys.exit()
            elif self.state=="paused":
                for lbl,r in self._pause_btns:
                    if r.collidepoint(mp):
                        if "Resume" in lbl: self.state="playing"
                        elif "Restart" in lbl: self.restart()
                        elif "Save" in lbl: self.save()
                        elif "Menu" in lbl: self.state="menu"
            elif self.state=="game_over":
                for lbl,r in self._go_btns:
                    if r.collidepoint(mp):
                        if "Again" in lbl: self.restart()
                        elif "Menu" in lbl: self.state="menu"
                        elif "Quit" in lbl: pygame.quit();sys.exit()

    # ── draw ─────────────────────────────────────────────────
    def _arena(self):
        # Solid boundary walls
        wall_col=(40,44,72); border_col=(90,160,255); glow_col=(50,100,200)
        # Draw outer walls as thick solid rects
        pygame.draw.rect(screen,wall_col,(0,0,W,50))       # top
        pygame.draw.rect(screen,wall_col,(0,H-50,W,50))    # bottom
        pygame.draw.rect(screen,wall_col,(0,0,50,H))       # left
        pygame.draw.rect(screen,wall_col,(W-50,0,50,H))    # right
        # Glowing inner edge
        pygame.draw.rect(screen,border_col,(50,50,W-100,H-100),4,border_radius=4)
        pygame.draw.rect(screen,glow_col,(53,53,W-106,H-106),2,border_radius=4)
        # Arena floor
        rdraw(screen,(22,25,44),(50,50,W-100,H-100),4)
        # Grid lines
        for gx in range(ARENA.left+80,ARENA.right,80):
            pygame.draw.line(screen,(33,36,58),(gx,ARENA.top),(gx,ARENA.bottom))
        for gy in range(ARENA.top+80,ARENA.bottom,80):
            pygame.draw.line(screen,(33,36,58),(ARENA.left,gy),(ARENA.right,gy))
        # Corner markers
        for cx,cy in[(50,50),(W-50,50),(50,H-50),(W-50,H-50)]:
            pygame.draw.circle(screen,(90,160,255),(cx,cy),7)
            pygame.draw.circle(screen,WHITE,(cx,cy),3)

    def _hud(self):
        # Player health
        rdraw(screen,PANELC,(8,8,230,40),8)
        hbar(screen,12,16,222,24,self.player.hp,100,HGREEN)
        label = "PLAYER" if self.player.alive else "DEAD"
        col = WHITE if self.player.alive else HRED
        screen.blit(fTINY.render(f"{label}  {max(0,self.player.hp)}/100",True,col),(14,21))
        # Enemy health bars (stacked on right)
        for i,e in enumerate(self.enemies):
            by=8+i*32
            rdraw(screen,PANELC,(W-238,by,230,28),6)
            bar_col=e.col if e.alive else DGRAY
            hbar(screen,W-234,by+4,222,20,e.hp,100,bar_col)
            status="" if e.alive else " [DEAD]"
            t=fTINY.render(f"ENEMY{i+1}{status}  {max(0,e.hp)}/100",True,e.col if e.alive else GRAY)
            screen.blit(t,(W-230,by+6))
        tc(screen,f"{self.pw}  vs  {self.ew}",fMED,GOLD,W//2,26)
        t=fTINY.render(f"First to {self.rtw} wins | {self.num_enemies} enem{'y' if self.num_enemies==1 else 'ies'}",True,GRAY)
        screen.blit(t,(W//2-t.get_width()//2,46))
        for i,h in enumerate(["WASD=Move","Mouse=Aim","LMB/SPACE=Shoot","ESC/P=Pause"]):
            screen.blit(fTINY.render(h,True,GRAY),(8,H-18-i*17))
        # Player death overlay warning
        if not self.player.alive and self.state=="round_end":
            s=pygame.Surface((W,H),pygame.SRCALPHA)
            s.fill((180,0,0,30))
            screen.blit(s,(0,0))

    def _draw_selector(self,label,val,cx,cy):
        tc(screen,label,fSM,GRAY,cx,cy-28)
        pygame.draw.polygon(screen,ACCENT,[(cx-78,cy),(cx-54,cy-18),(cx-54,cy+18)])
        pygame.draw.polygon(screen,ACCENT,[(cx+78,cy),(cx+54,cy-18),(cx+54,cy+18)])
        tc(screen,str(val),fBIG,GOLD,cx,cy)
        return cy

    def draw(self):
        screen.fill(BGCOL)
        if self.state=="menu": self._draw_menu()
        elif self.state in("playing","paused","round_end"):
            self._arena()
            for o in self.obs: o.draw(screen)
            # draw enemies (alive = normal, dead = X marker)
            for e in self.enemies:
                if e.alive:
                    e.draw(screen)
                else:
                    cx,cy=int(e.x),int(e.y)
                    pygame.draw.line(screen,HRED,(cx-16,cy-16),(cx+16,cy+16),5)
                    pygame.draw.line(screen,HRED,(cx+16,cy-16),(cx-16,cy+16),5)
                    pygame.draw.circle(screen,HRED,(cx,cy),18,2)
            # draw player (alive = normal, dead = X marker)
            if self.player.alive:
                self.player.draw(screen)
            else:
                cx,cy=int(self.player.x),int(self.player.y)
                pygame.draw.line(screen,HGREEN,(cx-16,cy-16),(cx+16,cy+16),5)
                pygame.draw.line(screen,HGREEN,(cx+16,cy-16),(cx-16,cy+16),5)
                pygame.draw.circle(screen,HGREEN,(cx,cy),18,2)
            self._hud()
            self.toast.draw(screen)
            if self.state=="round_end": self._draw_round_end()
            if self.state=="paused": self._draw_pause()
        elif self.state=="game_over": self._draw_go()

    def _draw_menu(self):
        s=pygame.Surface((W,H),pygame.SRCALPHA)
        pygame.draw.circle(s,(80,120,255,28),(W//2,H//2),360)
        screen.blit(s,(0,0))
        tc(screen,"GUNFIGHT ARENA",fBIG,ACCENT,W//2,95)
        tc(screen,"2D Top-Down Shooter",fSM,GRAY,W//2,150)
        pw,ph=460,410;px=W//2-pw//2;py=175
        rdraw(screen,PANELC,(px,py,pw,ph),16)
        pygame.draw.rect(screen,ACCENT,(px,py,pw,ph),2,border_radius=16)
        # rounds selector
        ary=py+80
        self._arrow_y=ary
        self._draw_selector("Rounds to Win",self.sel_rounds,W//2,ary)
        # enemies selector
        eay=py+170
        self._earrow_y=eay
        self._draw_selector("Number of Enemies",self.sel_enemies,W//2,eay)
        # buttons
        self._menu_btns=[]
        for lbl,col,cy in[("  START GAME",HGREEN,py+255),("  LOAD GAME",ACCENT,py+310),("  QUIT",HRED,py+365)]:
            r=make_btn(screen,lbl,fSM,col,W//2,cy,300,42)
            self._menu_btns.append((lbl,r))
        tc(screen,"WASD=Move | Mouse=Aim | LMB/SPACE=Shoot | ESC/P=Pause",fTINY,GRAY,W//2,H-14)

    def _draw_round_end(self):
        ov=pygame.Surface((W,H),pygame.SRCALPHA);ov.fill((0,0,0,145));screen.blit(ov,(0,0))
        msg,col=("ROUND WIN!",HGREEN) if self.rw=="player" else ("ROUND LOST!",HRED)
        tc(screen,msg,fBIG,col,W//2,H//2-30)
        tc(screen,f"Score  {self.pw} : {self.ew}",fMED,WHITE,W//2,H//2+30)
        secs=max(1,self.ret//60+1)
        tc(screen,f"Next round in {secs}s...",fSM,GRAY,W//2,H//2+75)

    def _draw_pause(self):
        ov=pygame.Surface((W,H),pygame.SRCALPHA);ov.fill((0,0,0,165));screen.blit(ov,(0,0))
        bw,bh=380,360;bx=W//2-bw//2;by=H//2-bh//2
        rdraw(screen,PANELC,(bx,by,bw,bh),18)
        pygame.draw.rect(screen,ACCENT,(bx,by,bw,bh),2,border_radius=18)
        tc(screen,"PAUSED",fBIG,ACCENT,W//2,by+52)
        tc(screen,"Press ESC or P to resume",fTINY,GRAY,W//2,by+90)
        self._pause_btns=[]
        for i,(lbl,col) in enumerate([("Resume  [ESC/P]",HGREEN),("Restart  [R]",GOLD),("Save Game  [S]",TEAL),("Main Menu  [M]",GRAY)]):
            cy=by+138+i*54
            r=make_btn(screen,lbl,fSM,col,W//2,cy,300,44)
            self._pause_btns.append((lbl,r))

    def _draw_go(self):
        bw,bh=480,340;bx=W//2-bw//2;by=H//2-bh//2
        rdraw(screen,PANELC,(bx,by,bw,bh),18)
        pygame.draw.rect(screen,ACCENT,(bx,by,bw,bh),3,border_radius=18)
        if self.pw>=self.rtw: tc(screen,"YOU WIN!",fBIG,HGREEN,W//2,by+60)
        else: tc(screen,"YOU LOSE!",fBIG,HRED,W//2,by+60)
        tc(screen,f"Final Score:  {self.pw} — {self.ew}",fMED,WHITE,W//2,by+120)
        self._go_btns=[]
        for i,(lbl,col) in enumerate([("Play Again",GOLD),("Main Menu",ACCENT),("Quit",HRED)]):
            cy=by+190+i*56
            r=make_btn(screen,lbl,fSM,col,W//2,cy,260,44)
            self._go_btns.append((lbl,r))
        self.toast.draw(screen)

def main():
    game=Game()
    while True:
        clock.tick(FPS)
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT: pygame.quit();sys.exit()
            game.event(ev)
        game.update()
        game.draw()
        pygame.display.flip()

if __name__=="__main__":
    main()
