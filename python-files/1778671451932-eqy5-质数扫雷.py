import pygame, random, math
from functools import reduce
from collections import deque

pygame.init()

# 难度定义
DIFFICULTIES = {
    "Easy": {"size": (9,9), "mines": 10, "range": (2,11), "cell": 40},
    "Medium": {"size": (16,16), "mines": 40, "range": (2,14), "cell": 35},
    "Hard": {"size": (16,30), "mines": 80, "range": (2,18), "cell": 25}
}

class PrimeSweeper:
    def __init__(self, diff="Easy"):
        self.diff = diff
        cfg = DIFFICULTIES[diff]
        self.rows, self.cols = cfg["size"]
        self.mines = cfg["mines"]
        self.prime_range = cfg["range"]
        self.cell = cfg["cell"]
        self.w = self.cols * self.cell
        self.h = self.rows * self.cell + 40
        self.screen = pygame.display.set_mode((self.w, self.h))
        pygame.display.set_caption("Prime Minesweeper")
        self.font = pygame.font.Font(None, self.cell//2)
        self.mfont = pygame.font.Font(None, 20)
        self.bfont = pygame.font.Font(None, 36)
        self.reset()

    def reset(self):
        self.grid = [[False]*self.cols for _ in range(self.rows)]
        self.show = [['' for _ in range(self.cols)] for _ in range(self.rows)]
        self.state = [[0]*self.cols for _ in range(self.rows)]
        self.marked = set()
        self.over = False
        self.won = False
        self.input = ""
        self.active = None
        self.first = True
        self._gen()

    def _gen(self):
        primes = [n for n in range(*self.prime_range) if all(n%i for i in range(2,int(math.sqrt(n))+1)) and n>1]
        pos = [(x,y) for x in range(self.rows) for y in range(self.cols)]
        random.shuffle(pos)
        for x,y in pos[:self.mines]:
            self.grid[x][y] = True
            self.show[x][y] = str(random.choice(primes))
        self._calc()

    def _calc(self):
        dirs = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
        for x in range(self.rows):
            for y in range(self.cols):
                if not self.grid[x][y]:
                    vals = [self.show[x+dx][y+dy] for dx,dy in dirs if 0<=x+dx<self.rows and 0<=y+dy<self.cols and self.grid[x+dx][y+dy]]
                    if not vals: self.show[x][y] = " "
                    elif len(vals)==1: self.show[x][y] = f"*{vals[0]}"
                    else:
                        p = reduce(lambda a,b: a*int(b), vals, 1)
                        self.show[x][y] = str(p) if p!=1 else " "

    def _safe(self, cx, cy):
        for x in range(self.rows):
            for y in range(self.cols):
                if not self.grid[x][y] and (x,y)!=(cx,cy):
                    self.grid[cx][cy], self.grid[x][y] = False, True
                    self.show[x][y], self.show[cx][cy] = self.show[cx][cy], ""
                    self._calc()
                    return

    def _reveal(self, sx, sy):
        q = deque([(sx,sy)])
        v = set()
        while q:
            x,y = q.popleft()
            if (x,y) in v or self.grid[x][y]: continue
            v.add((x,y)); self.state[x][y] = 1
            if self.show[x][y] in ["", " "]:
                for dx,dy in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
                    nx, ny = x+dx, y+dy
                    if 0<=nx<self.rows and 0<=ny<self.cols:
                        q.append((nx,ny))

    def draw(self):
        self.screen.fill((245,245,245))
        # 菜单
        xp = 20
        for d in DIFFICULTIES:
            txt = self.mfont.render(d, True, (30,30,30))
            self.screen.blit(txt, (xp,10))
            xp += txt.get_width()+30
        # 格子
        for x in range(self.rows):
            for y in range(self.cols):
                r = pygame.Rect(y*self.cell, x*self.cell+40, self.cell, self.cell)
                if self.state[x][y]==0: col = (200,200,200)
                elif self.state[x][y]==2: col = (200,240,200)
                else: col = (255,255,255)
                pygame.draw.rect(self.screen, col, r)
                if (self.over or self.won) and self.grid[x][y]:
                    t = self.font.render(self.show[x][y], True, (255,100,100))
                    self.screen.blit(t, t.get_rect(center=r.center))
                elif self.state[x][y]==1:
                    if self.show[x][y] not in [""," "]:
                        t = self.font.render(self.show[x][y], True, (30,30,30))
                        self.screen.blit(t, t.get_rect(center=r.center))
                elif self.state[x][y]==2 and (x,y) in self.marked:
                    t = self.font.render(self.show[x][y], True, (0,150,0))
                    self.screen.blit(t, t.get_rect(center=r.center))
                pygame.draw.rect(self.screen, (180,180,180), r, 1)
        # 输入框
        if self.active:
            x,y = self.active
            s = pygame.Surface((self.w,self.h), pygame.SRCALPHA)
            s.fill((0,0,0,128)); self.screen.blit(s,(0,0))
            bs = self.cell*0.8
            br = pygame.Rect(y*self.cell+(self.cell-bs)/2, x*self.cell+40+(self.cell-bs)/2, bs, bs)
            pygame.draw.rect(self.screen, (255,255,255), br)
            pygame.draw.rect(self.screen, (0,0,0), br, 2)
            t = self.font.render(self.input, True, (0,0,0))
            self.screen.blit(t, t.get_rect(center=br.center))
        # 结束/胜利
        if self.over or self.won:
            s = pygame.Surface((self.w,self.h), pygame.SRCALPHA)
            s.fill((0,0,0,128) if self.over else (100,200,100,128))
            self.screen.blit(s,(0,0))
            msg = "Game Over! Click to Restart" if self.over else "You Win! Click to Restart"
            t = self.bfont.render(msg, True, (255,255,255))
            self.screen.blit(t, t.get_rect(center=(self.w//2, self.h//2-30)))
            btn = pygame.Rect(0,0,200,50)
            btn.center = (self.w//2, self.h//2+30)
            pygame.draw.rect(self.screen, (200,200,200), btn, border_radius=8)
            bt = self.mfont.render("Restart (R)", True, (0,0,0))
            self.screen.blit(bt, bt.get_rect(center=btn.center))
            self.restart_rect = btn
        else:
            self.restart_rect = None

    def click(self, pos, btn):
        if pos[1] < 40:
            xp = 20
            mx, my = pos
            for d in DIFFICULTIES:
                txt = self.mfont.render(d, True, (30,30,30))
                if xp <= mx <= xp+txt.get_width():
                    self.__init__(d)
                    return
                xp += txt.get_width()+30
            return
        if self.over or self.won:
            if self.restart_rect and self.restart_rect.collidepoint(pos):
                self.reset()
            return
        x = (pos[1]-40)//self.cell
        y = pos[0]//self.cell
        if not (0<=x<self.rows and 0<=y<self.cols): return
        if self.active and (x,y)!=self.active:
            self.active = None; self.input = ""; return
        if btn==1:
            if self.state[x][y]==0:
                if self.first:
                    self.first=False
                    if self.grid[x][y]: self._safe(x,y)
                    self._reveal(x,y)
                else:
                    if self.grid[x][y]: self.over=True; self.active=None; self.input=""
                    else: self._reveal(x,y)
        elif btn==3:
            if self.state[x][y]==0: self.active=(x,y); self.input=""

    def key(self, e):
        if e.key == pygame.K_r:
            self.reset()
        elif self.active and not self.over and not self.won:
            if e.key == pygame.K_RETURN:
                try:
                    if int(self.input)==int(self.show[self.active[0]][self.active[1]]) and self.grid[self.active[0]][self.active[1]]:
                        self.marked.add(self.active)
                        self.state[self.active[0]][self.active[1]]=2
                        if len(self.marked)==self.mines: self.won=True
                except: pass
                self.active=None; self.input=""
            elif e.key == pygame.K_ESCAPE: self.active=None; self.input=""
            elif e.key == pygame.K_BACKSPACE: self.input=self.input[:-1]
            elif e.unicode.isdigit() and len(self.input)<6: self.input+=e.unicode

    def run(self):
        clock = pygame.time.Clock()
        r_held = False
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT: return
                if e.type == pygame.MOUSEBUTTONDOWN: self.click(e.pos, e.button)
                if e.type == pygame.KEYDOWN: self.key(e)
            keys = pygame.key.get_pressed()
            if keys[pygame.K_r]:
                if not r_held: self.reset()
                r_held = True
            else: r_held = False
            self.draw()
            pygame.display.flip()
            clock.tick(30)

if __name__ == "__main__":
    PrimeSweeper().run()