import random
import tkinter as tk
from tkinter import messagebox, DISABLED, NORMAL

# ==================== 牌权值 & 配色常量【美术专用】 ====================
CARD_SCORE = {
    '3':3, '4':4, '5':5, '6':6, '7':7, '8':8, '9':9,
    '10':10, 'J':11, 'Q':12, 'K':13, 'A':14, '2':15,
    '小王':16, '大王':17
}
CARD_LIST = ['3','4','5','6','7','8','9','10','J','Q','K','A','2']

# 全局美术配色
BG_TABLE = "#235E35"       # 桌面深绿
FRAME_BG1 = "#F8F9FA"     # 玩家面板
FRAME_BG2 = "#FFF5F5"     # 电脑1面板
FRAME_BG3 = "#F5FBFF"     # 电脑2面板
CARD_RED = "#D92222"      # 红牌
CARD_BLACK = "#1A1A1A"    # 黑牌
BTN_MAIN = "#D4AF37"      # 金色主按钮
BTN_DANGER = "#E53935"
BTN_INFO = "#1976D2"
HIGHTLIGHT_BG = "#42A5F5"
TEXT_MAIN = "#1F2937"

# ==================== 工具函数 ====================
def get_score_list(cards):
    return [CARD_SCORE[c] for c in cards]
def sort_card_asc(card_list):
    return sorted(card_list, key=lambda x: CARD_SCORE[x])
def sort_card_desc(card_list):
    return sorted(card_list, key=lambda x: CARD_SCORE[x], reverse=True)

def is_king_bomb(cards): return sorted(cards) == ['大王','小王']
def is_bomb(cards): return len(cards)==4 and len(set(cards))==1
def is_single(cards): return len(cards)==1
def is_pair(cards): return len(cards)==2 and len(set(cards))==1
def is_three(cards): return len(cards)==3 and len(set(cards))==1

def is_three_one(cards):
    if len(cards)!=4:return False
    cnt = {c:cards.count(c) for c in set(cards)}
    return sorted(cnt.values(), reverse=True)[0] == 3
def is_three_two(cards):
    if len(cards)!=5:return False
    cnt = {c:cards.count(c) for c in set(cards)}
    return sorted(cnt.values(), reverse=True) == [3,2]

def is_shunzi(cards):
    if len(cards)<5 or len(set(cards))!=len(cards):return False
    s = sorted(get_score_list(cards))
    return s[-1]-s[0] == len(s)-1 and max(s)<15
def is_double_shun(cards):
    if len(cards)<6 or len(cards)%2!=0:return False
    cnt = {c:cards.count(c) for c in set(cards)}
    if not all(v==2 for v in cnt.values()):return False
    s = sorted([CARD_SCORE[k] for k in cnt.keys()])
    return s[-1]-s[0] == len(s)-1 and max(s)<15
def is_airplane_base(cards):
    if len(cards)<6 or len(cards)%3!=0:return False
    groups = []
    temp = []
    for c in sorted(cards, key=lambda x:CARD_SCORE[x]):
        temp.append(c)
        if len(temp)==3:
            if not is_three(temp):return False
            groups.append(temp[0])
            temp = []
    if len(groups)<2:return False
    sc = [CARD_SCORE[g] for g in groups]
    return max(sc)-min(sc) == len(sc)-1 and max(sc)<15

def get_card_type(cards):
    if is_king_bomb(cards):return "王炸"
    if is_bomb(cards):return "炸弹"
    if is_airplane_base(cards):return "飞机"
    if is_shunzi(cards):return "顺子"
    if is_double_shun(cards):return "连对"
    if is_three_two(cards):return "三带二"
    if is_three_one(cards):return "三带一"
    if is_three(cards):return "三张"
    if is_pair(cards):return "对子"
    if is_single(cards):return "单张"
    return "无效牌型"

def is_valid_card(cards):
    return get_card_type(cards) != "无效牌型"

def can_beat(last_cards, now_cards):
    if not is_valid_card(now_cards):return False
    t1, t2 = get_card_type(last_cards), get_card_type(now_cards)
    if t2=="王炸":return True
    if t1=="王炸":return False
    if t2=="炸弹" and t1!="炸弹":return True
    if t1=="炸弹" and t2!="炸弹":return False
    if t1!=t2:return False

    if t1=="对子": return CARD_SCORE[now_cards[0]] > CARD_SCORE[last_cards[0]]
    if t1 in ["单张","三张","顺子","连对"]: return max(get_score_list(now_cards))>max(get_score_list(last_cards))
    if t1 in ["三带一","三带二"]:
        d1 = {c:last_cards.count(c) for c in set(last_cards)}
        d2 = {c:now_cards.count(c) for c in set(now_cards)}
        k1 = [k for k,v in d1.items() if v>=3][0]
        k2 = [k for k,v in d2.items() if v>=3][0]
        return CARD_SCORE[k2]>CARD_SCORE[k1]
    return False

def create_poker():
    poker = []
    for num in CARD_LIST: poker += [num]*4
    poker.extend(["小王","大王"])
    random.shuffle(poker)
    return poker

# ==================== 主程序【美术美化版】 ====================
class DoudizhuGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("欢乐斗地主 | 美术美化版")
        self.root.geometry("1450x820")
        self.root.resizable(False, False)
        self.root.configure(bg=BG_TABLE)

        # 游戏数据
        self.poker = create_poker()
        self.p1 = sort_card_desc(self.poker[:17])
        self.p2 = sort_card_desc(self.poker[17:34])
        self.p3 = sort_card_desc(self.poker[34:51])
        self.bottom = self.poker[51:]
        self.name_list = ["你", "电脑一号", "电脑二号"]
        self.lord_idx = 0
        self.turn = 0
        self.last_play = []
        self.last_play_idx = -1
        self.pass_count = 0
        self.select_index = []
        self.card_buttons = {}
        self.game_start = False

        self.init_ui()
        self.refresh_all_ui()

    def init_ui(self):
        # 顶部标题栏
        top_frame = tk.Frame(self.root, bg="#1A472A", height=90)
        top_frame.pack(fill=tk.X, padx=8, pady=8)
        title = tk.Label(top_frame, text="🏆 欢乐斗地主 经典版", font=("微软雅黑", 26, "bold"),
                         bg="#1A472A", fg="#FFD700")
        title.pack(pady=12)

        # 公共信息栏
        info_frame = tk.Frame(self.root, bg="#306B42", bd=0)
        info_frame.pack(fill=tk.X, padx=12, pady=6)
        self.bottom_text = tk.Label(info_frame, text="🎴 底牌：未解锁", font=("微软雅黑", 13),
                                    bg="#306B42", fg="white")
        self.bottom_text.pack(side=tk.LEFT, padx=30, pady=8)
        self.tip_text = tk.Label(info_frame, text="📢 请点击【开始游戏】", font=("微软雅黑", 13),
                                 bg="#306B42", fg="#FFEE58")
        self.tip_text.pack(side=tk.RIGHT, padx=30, pady=8)

        # 三名玩家 三栏布局
        container = tk.Frame(self.root, bg=BG_TABLE)
        container.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

        # 1. 玩家自己 左侧面板
        self.frame_me = tk.Frame(container, bg=FRAME_BG1, bd=4, relief=tk.RIDGE)
        self.frame_me.grid(row=0, column=0, padx=8, sticky="nsew")
        tk.Label(self.frame_me, text="👤 我方玩家", font=("微软雅黑", 18, "bold"),
                 bg=FRAME_BG1, fg=TEXT_MAIN).pack(pady=8)
        self.identity_me = tk.Label(self.frame_me, text="身份：待定", font=("微软雅黑", 12), bg=FRAME_BG1)
        self.identity_me.pack()
        tk.Label(self.frame_me, text="🃏 本局出牌", font=("微软雅黑", 12), bg=FRAME_BG1).pack(pady=3)
        self.out_me = tk.Label(self.frame_me, text="暂无出牌", font=("微软雅黑", 11),
                               bg="white", width=22, height=4, relief=tk.SUNKEN)
        self.out_me.pack(pady=6)
        tk.Label(self.frame_me, text="🎴 我的手牌", font=("微软雅黑", 12), bg=FRAME_BG1).pack(pady=3)
        self.card_frame_me = tk.Frame(self.frame_me, bg=FRAME_BG1)
        self.card_frame_me.pack(pady=8, fill=tk.X)

        # 2. 电脑一号 中间面板
        self.frame_ai1 = tk.Frame(container, bg=FRAME_BG2, bd=4, relief=tk.RIDGE)
        self.frame_ai1.grid(row=0, column=1, padx=8, sticky="nsew")
        tk.Label(self.frame_ai1, text="🤖 电脑一号", font=("微软雅黑", 18, "bold"),
                 bg=FRAME_BG2, fg=TEXT_MAIN).pack(pady=8)
        self.identity_ai1 = tk.Label(self.frame_ai1, text="身份：待定", font=("微软雅黑", 12), bg=FRAME_BG2)
        self.identity_ai1.pack()
        tk.Label(self.frame_ai1, text="🃏 本局出牌", font=("微软雅黑", 12), bg=FRAME_BG2).pack(pady=3)
        self.out_ai1 = tk.Label(self.frame_ai1, text="暂无出牌", font=("微软雅黑", 11),
                                bg="white", width=22, height=4, relief=tk.SUNKEN)
        self.out_ai1.pack(pady=6)
        self.count_ai1 = tk.Label(self.frame_ai1, text="剩余手牌：17 张", font=("微软雅黑", 12), bg=FRAME_BG2)
        self.count_ai1.pack(pady=12)

        # 3. 电脑二号 右侧面板
        self.frame_ai2 = tk.Frame(container, bg=FRAME_BG3, bd=4, relief=tk.RIDGE)
        self.frame_ai2.grid(row=0, column=2, padx=8, sticky="nsew")
        tk.Label(self.frame_ai2, text="🤖 电脑二号", font=("微软雅黑", 18, "bold"),
                 bg=FRAME_BG3, fg=TEXT_MAIN).pack(pady=8)
        self.identity_ai2 = tk.Label(self.frame_ai2, text="身份：待定", font=("微软雅黑", 12), bg=FRAME_BG3)
        self.identity_ai2.pack()
        tk.Label(self.frame_ai2, text="🃏 本局出牌", font=("微软雅黑", 12), bg=FRAME_BG3).pack(pady=3)
        self.out_ai2 = tk.Label(self.frame_ai2, text="暂无出牌", font=("微软雅黑", 11),
                                bg="white", width=22, height=4, relief=tk.SUNKEN)
        self.out_ai2.pack(pady=6)
        self.count_ai2 = tk.Label(self.frame_ai2, text="剩余手牌：17 张", font=("微软雅黑", 12), bg=FRAME_BG3)
        self.count_ai2.pack(pady=12)

        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)
        container.grid_columnconfigure(2, weight=1)

        # 底部操作按钮区【美术按钮】
        btn_box = tk.Frame(self.root, bg=BG_TABLE)
        btn_box.pack(pady=15)

        self.btn_start = tk.Button(btn_box, text="🎮 开始游戏", command=self.start_game,
                                    width=12, height=2, font=("微软雅黑",11,"bold"),
                                    bg=BTN_MAIN, fg="white", relief=tk.RAISED)
        self.btn_rob = tk.Button(btn_box, text="👑 抢地主", command=self.rob,
                                  width=10, height=2, font=("微软雅黑",11),
                                  bg="#FF9800", fg="white", state=DISABLED)
        self.btn_no_rob = tk.Button(btn_box, text="❌ 不抢", command=self.no_rob,
                                     width=10, height=2, font=("微软雅黑",11),
                                     bg="#78909C", fg="white", state=DISABLED)
        self.btn_play = tk.Button(btn_box, text="🃏 出牌", command=self.send_card,
                                   width=10, height=2, font=("微软雅黑",11,"bold"),
                                   bg=BTN_INFO, fg="white", state=DISABLED)
        self.btn_pass = tk.Button(btn_box, text="⏸️ 不出(Pass)", command=self.do_pass,
                                   width=12, height=2, font=("微软雅黑",11),
                                   bg=BTN_DANGER, fg="white", state=DISABLED)
        self.btn_clear = tk.Button(btn_box, text="🧹 清空选牌", command=self.clear_sel,
                                    width=10, height=2, font=("微软雅黑",11),
                                    bg="#EEEEEE", state=DISABLED)

        self.btn_start.grid(row=0,column=0,padx=6)
        self.btn_rob.grid(row=0,column=1,padx=6)
        self.btn_no_rob.grid(row=0,column=2,padx=6)
        self.btn_play.grid(row=0,column=3,padx=6)
        self.btn_pass.grid(row=0,column=4,padx=6)
        self.btn_clear.grid(row=0,column=5,padx=6)

    # 刷新全部界面
    def refresh_all_ui(self):
        # 身份刷新
        self.identity_me.config(text=f"身份：{'🏆地主' if self.lord_idx==0 else '🌾农民'}")
        self.identity_ai1.config(text=f"身份：{'🏆地主' if self.lord_idx==1 else '🌾农民'}")
        self.identity_ai2.config(text=f"身份：{'🏆地主' if self.lord_idx==2 else '🌾农民'}")

        # 手牌数量
        self.count_ai1.config(text=f"剩余手牌：{len(self.p2)} 张")
        self.count_ai2.config(text=f"剩余手牌：{len(self.p3)} 张")

        # 出牌区域
        empty = "暂无出牌"
        if self.last_play_idx == 0:
            self.out_me.config(text=f"{' '.join(self.last_play)}\n【{get_card_type(self.last_play)}】")
            self.out_ai1.config(text=empty)
            self.out_ai2.config(text=empty)
        elif self.last_play_idx == 1:
            self.out_ai1.config(text=f"{' '.join(self.last_play)}\n【{get_card_type(self.last_play)}】")
            self.out_me.config(text=empty)
            self.out_ai2.config(text=empty)
        elif self.last_play_idx == 2:
            self.out_ai2.config(text=f"{' '.join(self.last_play)}\n【{get_card_type(self.last_play)}】")
            self.out_me.config(text=empty)
            self.out_ai1.config(text=empty)
        else:
            self.out_me.config(text=empty)
            self.out_ai1.config(text=empty)
            self.out_ai2.config(text=empty)

        self.refresh_my_card()

    # 美化卡牌渲染（红黑花色、圆角、立体）
    def refresh_my_card(self):
        for w in self.card_frame_me.winfo_children():
            w.destroy()
        self.card_buttons.clear()
        self.select_index.clear()
        self.p1 = sort_card_desc(self.p1)

        for idx, name in enumerate(self.p1):
            # 红牌 / 黑牌区分
            if name in ["J","Q","K","A","2"] or name == "小王" or name == "大王":
                color = CARD_RED
            else:
                color = CARD_BLACK

            btn = tk.Button(
                self.card_frame_me,
                text=name,
                width=5, height=3,
                font=("微软雅黑", 11, "bold"),
                fg=color,
                bg="white",
                relief=tk.RIDGE,
                bd=2
            )
            btn.grid(row=0, column=idx, padx=2)
            self.card_buttons[idx] = btn
            btn.config(command=lambda i=idx:self.click_card(i))

    def click_card(self, idx):
        if not self.game_start: return
        btn = self.card_buttons[idx]
        if idx in self.select_index:
            self.select_index.remove(idx)
            btn.config(bg="white")
        else:
            self.select_index.append(idx)
            btn.config(bg=HIGHTLIGHT_BG, fg="white")

    def clear_sel(self):
        self.select_index.clear()
        for btn in self.card_buttons.values():
            btn.config(bg="white")

    # 游戏流程
    def start_game(self):
        self.game_start = True
        self.btn_start.config(state=DISABLED)
        self.btn_rob.config(state=NORMAL)
        self.btn_no_rob.config(state=NORMAL)
        self.tip_text.config(text="请选择：抢地主 / 不抢")
        messagebox.showinfo("游戏开始", "欢迎进入斗地主\n请选择是否抢地主！")

    def rob(self):
        self.lord_idx = 0
        self.rob_finish()
    def no_rob(self):
        self.lord_idx = 1 if random.random()>0.5 else 2
        self.rob_finish()

    def rob_finish(self):
        if self.lord_idx == 0:
            self.p1.extend(self.bottom)
        elif self.lord_idx == 1:
            self.p2.extend(self.bottom)
        else:
            self.p3.extend(self.bottom)

        self.btn_rob.config(state=DISABLED)
        self.btn_no_rob.config(state=DISABLED)
        self.btn_play.config(state=NORMAL)
        self.btn_pass.config(state=NORMAL)
        self.btn_clear.config(state=NORMAL)
        self.bottom_text.config(text=f"🎴 底牌：{' '.join(self.bottom)}")
        self.turn = self.lord_idx
        self.last_play = []
        self.last_play_idx = -1
        self.pass_count = 0
        self.tip_text.config(text="游戏进行中，请出牌")
        self.refresh_all_ui()
        self.game_loop()

    # 出牌
    def send_card(self):
        if not self.select_index:
            messagebox.showwarning("提示", "请先选中手牌！")
            return
        cards = [self.p1[i] for i in sorted(self.select_index, reverse=True)]
        if not is_valid_card(cards):
            messagebox.showerror("错误", "❌ 无效牌型，无法出牌！")
            return
        if self.last_play and not can_beat(self.last_play, cards):
            messagebox.showerror("错误", "❌ 无法压过上家手牌！")
            return

        for i in sorted(self.select_index, reverse=True):
            del self.p1[i]
        self.last_play = cards
        self.last_play_idx = 0
        self.pass_count = 0
        self.clear_sel()
        self.refresh_all_ui()

        if self.check_win(): return
        self.turn = 1
        self.game_loop()

    # Pass
    def do_pass(self):
        if self.last_play_idx == self.turn:
            messagebox.showwarning("提示", "⚠️ 你是出牌方，不能Pass！")
            return
        self.pass_count += 1
        if self.pass_count >= 2:
            self.last_play = []
            self.pass_count = 0
            self.turn = self.last_play_idx
            if self.turn == 0:
                self.tip_text.config(text="✅ 对手全部Pass，你获得出牌权！")
                messagebox.showinfo("牌权重置", "两名对手全部Pass\n轮到你自由出牌！")
        else:
            self.turn = (self.turn + 1) % 3
        self.refresh_all_ui()
        self.game_loop()

    # 智能AI 优先小牌
    def ai_play(self, hand):
        small = sort_card_asc(hand)
        if not self.last_play:
            for c in small:
                if c not in ["2","小王","大王"]:
                    return [c]
            for i in range(len(small)-1):
                if small[i]==small[i+1] and small[i]!="2":
                    return [small[i], small[i+1]]
            return [small[0]]

        last_t = get_card_type(self.last_play)
        target = max(get_score_list(self.last_play))
        if last_t == "单张":
            for c in small:
                if CARD_SCORE[c]>target and c not in ["2","小王","大王"]:
                    return [c]
        if last_t == "对子":
            for i in range(len(small)-1):
                if small[i]==small[i+1] and CARD_SCORE[small[i]]>target:
                    return [small[i], small[i+1]]
        for i in range(len(small)-3):
            if is_bomb(small[i:i+4]):
                return small[i:i+4]
        return []

    def run_ai(self, idx):
        hand = self.p2 if idx==1 else self.p3
        play = self.ai_play(hand)
        if play:
            for c in play:
                hand.remove(c)
            self.last_play = play
            self.last_play_idx = idx
            self.pass_count = 0
        else:
            self.pass_count += 1

        self.refresh_all_ui()
        if self.check_win(): return
        if self.pass_count >= 2:
            self.last_play = []
            self.pass_count = 0
            self.turn = self.last_play_idx
            if self.turn == 0:
                self.tip_text.config(text="✅ 对手全部Pass，你获得出牌权！")
                messagebox.showinfo("牌权重置", "两名对手全部Pass\n轮到你自由出牌！")
        else:
            self.turn = (self.turn + 1) % 3
        self.game_loop()

    def game_loop(self):
        if self.turn == 0:
            return
        self.root.after(800, lambda:self.run_ai(self.turn))

    def check_win(self):
        if len(self.p1)==0 or len(self.p2)==0 or len(self.p3)==0:
            win_idx = 0 if len(self.p1)==0 else 1 if len(self.p2)==0 else 2
            res = "🏆地主胜利！" if win_idx==self.lord_idx else "🌾农民胜利！"
            messagebox.showinfo("游戏结束", f"{self.name_list[win_idx]} 出完所有手牌\n{res}")
            self.root.quit()
            return True
        return False

if __name__ == "__main__":
    root = tk.Tk()
    app = DoudizhuGUI(root)
    root.mainloop()
