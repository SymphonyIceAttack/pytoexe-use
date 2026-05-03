import random
import sys
import os
import time
import re

class Colors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BG_RED = "\033[41m"
    BOLD = "\033[1m"

class CityGame:
    def __init__(self, width=10, height=10):
        self.width = width
        self.height = height
        self.grid = [["空地" for _ in range(width)] for _ in range(height)]
        self.population = 100
        self.money = 1000
        self.turn = 1
        self.terrorists_active = False
        self.terrorist_location = None
        self.facilities = ["房屋", "企业", "警察局", "医院", "武装设施", "黑市", "纪念碑"]
        self.facility_costs = {
            "房屋": 100, "企业": 200, "警察局": 300, "医院": 300,
            "武装设施": 500, "黑市": 150, "纪念碑": 1000
        }
        self.facility_descriptions = {
            "房屋": "提供人口增长 +5人/回合",
            "企业": "提供税收 +100/回合",
            "警察局": "降低暴乱概率 -5%",
            "医院": "提供人口增长 +10人/回合",
            "武装设施": "降低暴乱概率 -10%，可镇压暴乱",
            "黑市": "提供利润 +300/回合，但增加暴乱风险",
            "纪念碑": "降低暴乱概率 -15%，提升城市形象"
        }
        self.latest_events = []
        self.build_history = []
        self.riot_history = []
        self.total_income = 0
        self.total_spent = 0
        self.total_pop_lost = 0

        if os.name == 'nt':
            os.system('color')

    def get_colored_facility(self, facility):
        colors = {
            "房屋": Colors.GREEN, "企业": Colors.YELLOW, "警察局": Colors.BLUE,
            "医院": Colors.CYAN, "武装设施": Colors.MAGENTA, "黑市": Colors.RED,
            "纪念碑": Colors.WHITE, "暴乱": Colors.BG_RED + Colors.WHITE, "空地": Colors.WHITE
        }
        return f"{colors.get(facility, '')}{facility}{Colors.RESET}" if facility in colors else facility

    def get_display_width(self, text):
        clean_text = re.sub(r'\[[0-9;]*m', '', text)
        width = 0
        for char in clean_text:
            if '\u4e00' <= char <= '\u9fff':
                width += 2
            else:
                width += 1
        return width

    def pad_string(self, text, target_width):
        current_width = self.get_display_width(text)
        padding = target_width - current_width
        if padding > 0:
            left_pad = padding // 2
            right_pad = padding - left_pad
            return " " * left_pad + text + " " * right_pad
        return text

    def add_log(self, msg, level="INFO"):
        if level == "CRITICAL":
            self.latest_events.append(f"{Colors.RED}[CRITICAL_ERR] 0x0000F: {msg}{Colors.RESET}")
        elif level == "WARNING":
            self.latest_events.append(f"{Colors.YELLOW}[SYS_WARNING] 0x000A1: {msg}{Colors.RESET}")
        else:
            self.latest_events.append(f"{Colors.CYAN}[SYS_INFO] {msg}{Colors.RESET}")

    def print_news_headline(self):
        """打印游戏结束新闻头条"""
        print("\n" * 2)

        total_buildings = sum(1 for row in self.grid for cell in row if cell != "空地")
        houses = sum(row.count("房屋") for row in self.grid)
        enterprises = sum(row.count("企业") for row in self.grid)
        police = sum(row.count("警察局") for row in self.grid)
        hospitals = sum(row.count("医院") for row in self.grid)
        military = sum(row.count("武装设施") for row in self.grid)
        black_markets = sum(row.count("黑市") for row in self.grid)
        monuments = sum(row.count("纪念碑") for row in self.grid)

        news_titles = [
            "【突发】城市管理者因严重失职被紧急撤职！",
            "【头条】城市陷入混乱，市长被罢免！",
            "【紧急】人口清零！城市管理系统崩溃！",
            "【震惊】治理无能导致城市灭亡！",
            "【号外】城市末日：管理者被撤职调查！"
        ]

        title = random.choice(news_titles)
        border = "=" * 60
        print(f"{Colors.BG_RED}{Colors.WHITE}{Colors.BOLD}")
        print(f"╔{border}╗")
        print(f"║{self.pad_string(' ', 60)}║")
        title_padded = self.pad_string(title, 58)
        print(f"║ {title_padded} ║")
        print(f"║{self.pad_string(' ', 60)}║")
        print(f"╠{border}╣")
        subtitle = "《城市日报》特别报道"
        subtitle_padded = self.pad_string(subtitle, 58)
        print(f"║ {subtitle_padded} ║")
        print(f"╠{border}╣")

        news_lines = [
            f"  据本台记者报道，第 {self.turn} 回合时，",
            f"  城市人口已彻底清零，城市管理系统",
            f"  陷入全面崩溃。",
            "",
            f"  经调查，该管理者在任期间：",
            f"  • 执政时长：{self.turn} 回合",
            f"  • 建造建筑：{total_buildings} 座",
            f"    - 房屋：{houses} 座",
            f"    - 企业：{enterprises} 座",
            f"    - 警察局：{police} 座",
            f"    - 医院：{hospitals} 座",
            f"    - 武装设施：{military} 座",
            f"    - 黑市：{black_markets} 座",
            f"    - 纪念碑：{monuments} 座",
            "",
            f"  • 总财政收入：{self.total_income}",
            f"  • 总财政支出：{self.total_spent}",
            f"  • 净财政状况：{self.total_income - self.total_spent}",
            f"  • 损失人口总数：{self.total_pop_lost} 人",
            f"  • 暴乱发生次数：{len(self.riot_history)} 次",
            "",
            "  市民评价：",
        ]

        if self.turn <= 3:
            evaluation = "【极差】上任即崩溃，堪称史上最短任期！"
        elif self.turn <= 10:
            evaluation = "【不合格】治理无能，民不聊生！"
        elif total_buildings < 5:
            evaluation = "【懒惰】几乎不建任何设施，尸位素餐！"
        elif black_markets > 3:
            evaluation = "【腐败】纵容黑市，腐败透顶！"
        elif monuments > 3 and houses < 3:
            evaluation = "【虚荣】只顾面子工程，不顾民生！"
        else:
            evaluation = "【遗憾】虽有努力，但终究功亏一篑。"

        news_lines.append(f"  {evaluation}")
        news_lines.append("")
        news_lines.append("  目前，该管理者已被撤职，")
        news_lines.append("  正在接受进一步调查...")

        for line in news_lines:
            display_width = self.get_display_width(line)
            if display_width < 58:
                line = line + " " * (58 - display_width)
            elif display_width > 58:
                line = line[:58]
            print(f"║ {line} ║")

        print(f"║{self.pad_string(' ', 60)}║")
        print(f"╚{border}╝")
        print(f"{Colors.RESET}")
        print(f"\n{Colors.YELLOW}游戏结束。感谢游玩城市管理终端。{Colors.RESET}\n")

    def process_command(self, command):
        parts = command.strip().split()
        if not parts:
            return True

        cmd = parts[0]

        if cmd == "/退出":
            return False

        elif cmd == "/帮助":
            print(f"{Colors.CYAN}=== 城市管理终端 v6.0 ==={Colors.RESET}")
            print("  /查询 <项目> (一切, 资金, 人口, 时间, 地图, 暴乱, 事件)")
            print("  /建造 <x> <y> <设施名> (房屋, 企业, 警察局, 医院, 武装设施, 黑市, 纪念碑)")
            print("  /摧毁 <x> <y>")
            print("  /镇压 <x> <y> (需要武装设施或警察局)")
            print("  /处决 <数量> (消耗人口，概率平息暴乱)")
            print("  /宣传 (花费200，增加人口并降低暴乱概率)")
            print("  /搜刮 (牺牲30人口，强制征收400，极易引发暴乱)")
            print("  /下一回合 (推进时间)")
            print("")
            print("设施说明：")
            for fac, desc in self.facility_descriptions.items():
                cost = self.facility_costs[fac]
                print(f"  {self.get_colored_facility(fac)}: {cost} - {desc}")
            return True

        elif cmd == "/查询":
            if len(parts) != 2:
                print(f"{Colors.RED}格式错误！正确格式: /查询 <项目>{Colors.RESET}")
                return True
            target = parts[1]

            if target in ["一切", "全部"]:
                print(f"\n{Colors.CYAN}=== 城市综合报告 ==={Colors.RESET}")
                print(f"当前时间: 第 {Colors.YELLOW}{self.turn}{Colors.RESET} 回合")
                print(f"当前经费: {Colors.YELLOW}{self.money}{Colors.RESET}")
                print(f"当前人口: {Colors.GREEN}{self.population}人{Colors.RESET}")

                if self.terrorists_active:
                    print(f"{Colors.RED}[CRITICAL_ERR] '柯林顿派' 正在 {self.terrorist_location} 区域活动！{Colors.RESET}")
                else:
                    print(f"{Colors.GREEN}[SYS_OK] 城市治安良好。{Colors.RESET}")

                if self.latest_events:
                    print(f"\n{Colors.CYAN}系统日志:{Colors.RESET}")
                    for ev in self.latest_events:
                        print(f" {ev}")

                self._print_map()

            elif target in ["资金", "经费"]:
                print(f"当前经费: {Colors.YELLOW}{self.money}{Colors.RESET}")
            elif target == "人口":
                print(f"当前人口: {Colors.GREEN}{self.population}人{Colors.RESET}")
            elif target in ["时间", "回合"]:
                print(f"当前时间: 第 {Colors.YELLOW}{self.turn}{Colors.RESET} 回合")
            elif target == "暴乱":
                if self.terrorists_active:
                    print(f"{Colors.RED}[CRITICAL_ERR] '柯林顿派' 正在 {self.terrorist_location} 区域活动！{Colors.RESET}")
                else:
                    print(f"{Colors.GREEN}[SYS_OK] 城市治安良好。{Colors.RESET}")
            elif target == "事件":
                for ev in self.latest_events:
                    print(f" {ev}")
            elif target == "地图":
                self._print_map()
            else:
                print(f"{Colors.RED}未知的查询项目！{Colors.RESET}")
            return True

        elif cmd == "/建造":
            if len(parts) != 4:
                print(f"{Colors.RED}格式错误！正确格式: /建造 <x> <y> <设施名>{Colors.RESET}")
                return True
            try:
                x, y = int(parts[1]), int(parts[2])
                facility = parts[3]
                if not (0 <= x < self.width and 0 <= y < self.height):
                    print(f"{Colors.RED}坐标超出范围！(0-9){Colors.RESET}")
                    return True
                if facility not in self.facilities:
                    print(f"{Colors.RED}未知设施！可用设施: {', '.join(self.facilities)}{Colors.RESET}")
                    return True
                if self.grid[y][x] != "空地":
                    print(f"{Colors.RED}该位置已有建筑！{Colors.RESET}")
                    return True
                cost = self.facility_costs[facility]
                if self.money < cost:
                    print(f"{Colors.RED}经费不足！需要 {cost}，当前仅有 {self.money}{Colors.RESET}")
                    return True

                self.money -= cost
                self.total_spent += cost
                self.grid[y][x] = facility
                self.build_history.append((self.turn, x, y, facility, cost))

                print(f"{Colors.GREEN}[SYS_OK] 在 ({x}, {y}) 建造了 {self.get_colored_facility(facility)}。{Colors.RESET}")
                print(f"{Colors.YELLOW}[财务] 扣除建造费用 {cost}，剩余经费 {self.money}。{Colors.RESET}")

                print(f"\n{Colors.CYAN}=== 建造后城市地图 ==={Colors.RESET}")
                self._print_map()

            except ValueError:
                print(f"{Colors.RED}坐标必须是整数！{Colors.RESET}")
            return True

        elif cmd == "/摧毁":
            if len(parts) != 3:
                print(f"{Colors.RED}格式错误！正确格式: /摧毁 <x> <y>{Colors.RESET}")
                return True
            try:
                x, y = int(parts[1]), int(parts[2])
                if not (0 <= x < self.width and 0 <= y < self.height):
                    print(f"{Colors.RED}坐标超出范围！(0-9){Colors.RESET}")
                    return True
                if self.grid[y][x] == "空地":
                    print(f"{Colors.RED}该位置已经是空地！{Colors.RESET}")
                    return True
                facility = self.grid[y][x]

                refund = self.facility_costs[facility] // 2
                self.money += refund
                self.total_income += refund
                self.grid[y][x] = "空地"

                print(f"{Colors.GREEN}[SYS_OK] 摧毁了 ({x}, {y}) 的 {self.get_colored_facility(facility)}。{Colors.RESET}")
                print(f"{Colors.YELLOW}[财务] 回收拆除费用 {refund}（原造价 {self.facility_costs[facility]} 的 50%），当前经费 {self.money}。{Colors.RESET}")

                print(f"\n{Colors.CYAN}=== 摧毁后城市地图 ==={Colors.RESET}")
                self._print_map()

            except ValueError:
                print(f"{Colors.RED}坐标必须是整数！{Colors.RESET}")
            return True

        elif cmd == "/镇压":
            if len(parts) != 3:
                print(f"{Colors.RED}格式错误！正确格式: /镇压 <x> <y>{Colors.RESET}")
                return True
            try:
                x, y = int(parts[1]), int(parts[2])
                if not self.terrorists_active or self.terrorist_location != (x, y):
                    print(f"{Colors.RED}[ERR] 目标位置未发现暴乱分子！{Colors.RESET}")
                    return True

                has_force = any(cell in ["武装设施", "警察局"] for row in self.grid for cell in row)
                if not has_force:
                    print(f"{Colors.RED}[ERR] 缺乏武装力量，镇压失败！{Colors.RESET}")
                    return True

                print(f"{Colors.GREEN}[SYS_OK] 镇压成功！'柯林顿派' 被击退！{Colors.RESET}")
                self.terrorists_active = False
                self.terrorist_location = None
            except ValueError:
                print(f"{Colors.RED}坐标必须是整数！{Colors.RESET}")
            return True

        elif cmd == "/处决":
            if len(parts) != 2:
                print(f"{Colors.RED}格式错误！正确格式: /处决 <数量>{Colors.RESET}")
                return True
            try:
                amount = int(parts[1])
                if amount <= 0:
                    print(f"{Colors.RED}处决数量必须大于0！{Colors.RESET}")
                    return True
                if amount > self.population:
                    print(f"{Colors.RED}[ERR] 人口不足！当前仅有 {self.population} 人{Colors.RESET}")
                    return True

                self.population -= amount
                self.total_pop_lost += amount
                print(f"{Colors.GREEN}[SYS_OK] 已处决 {amount} 人。{Colors.RESET}")
                if self.terrorists_active and random.random() < 0.5:
                    print(f"{Colors.GREEN}[SYS_OK] 残酷的手段震慑了暴徒，暴乱平息！{Colors.RESET}")
                    self.terrorists_active = False
                    self.terrorist_location = None
            except ValueError:
                print(f"{Colors.RED}数量必须是整数！{Colors.RESET}")
            return True

        elif cmd == "/宣传":
            if self.money < 200:
                print(f"{Colors.RED}[ERR] 经费不足，需要200，当前仅有 {self.money}！{Colors.RESET}")
                return True
            self.money -= 200
            self.total_spent += 200
            self.population += 20
            print(f"{Colors.GREEN}[SYS_OK] 宣传广播已启动。民众情绪稳定，人口增加。{Colors.RESET}")
            print(f"{Colors.YELLOW}[财务] 扣除宣传费用 200，剩余经费 {self.money}。{Colors.RESET}")
            return True

        elif cmd == "/搜刮":
            if self.population < 30:
                print(f"{Colors.RED}[ERR] 人口不足以承受搜刮！当前仅有 {self.population} 人{Colors.RESET}")
                return True
            self.population -= 30
            self.total_pop_lost += 30
            self.money += 400
            self.total_income += 400
            print(f"{Colors.YELLOW}[SYS_WARNING] 强制征收完成。获得400，失去30人口。民众怨声载道！{Colors.RESET}")
            print(f"{Colors.YELLOW}[财务] 当前经费 {self.money}，当前人口 {self.population}人。{Colors.RESET}")
            if not self.terrorists_active and random.random() < 0.6:
                self.trigger_riot()
            return True

        elif cmd == "/下一回合":
            if not self.end_turn():
                return False
            print(f"{Colors.CYAN}时间流逝... 当前已进入第 {self.turn} 回合。输入 /查询 事件 查看系统日志。{Colors.RESET}")
            return True

        else:
            print(f"{Colors.RED}未知指令！输入 /帮助 查看可用指令。{Colors.RESET}")
            return True

    def _print_map(self):
        print(f"\n{Colors.CYAN}城市地图 (10x10):{Colors.RESET}")

        cell_width = 10

        header = "   "
        for x in range(self.width):
            header += self.pad_string(str(x), cell_width) + " "
        print(header)

        for y in range(self.height):
            row_str = f"{y:2d} "
            for x in range(self.width):
                if self.terrorists_active and self.terrorist_location == (x, y):
                    colored_cell = self.get_colored_facility('暴乱')
                    padded_cell = self.pad_string(colored_cell, cell_width)
                    row_str += f"[{padded_cell}]"
                else:
                    cell = self.grid[y][x]
                    colored_cell = self.get_colored_facility(cell)
                    padded_cell = self.pad_string(colored_cell, cell_width)
                    row_str += f"[{padded_cell}]"
            print(row_str)
        print("")

    def trigger_riot(self):
        self.terrorists_active = True
        occupied = [(x, y) for y in range(self.height) for x in range(self.width) if self.grid[y][x] != "空地"]
        if occupied:
            self.terrorist_location = random.choice(occupied)
        else:
            self.terrorist_location = (random.randint(0, self.width-1), random.randint(0, self.height-1))
        self.riot_history.append((self.turn, self.terrorist_location))
        self.add_log("检测到未授权的武装集结！'柯林顿派' 发动了暴乱！", "CRITICAL")

    def end_turn(self):
        self.turn += 1
        self.latest_events = []

        houses = sum(row.count("房屋") for row in self.grid)
        enterprises = sum(row.count("企业") for row in self.grid)
        hospitals = sum(row.count("医院") for row in self.grid)
        black_markets = sum(row.count("黑市") for row in self.grid)
        monuments = sum(row.count("纪念碑") for row in self.grid)

        pop_growth = houses * 5 + hospitals * 10
        self.population += pop_growth
        if pop_growth > 0:
            self.add_log(f"人口自然增长 {pop_growth} 人。")

        income = enterprises * 100 + black_markets * 300 + self.population * 1
        self.money += income
        self.total_income += income
        if income > 0:
            self.add_log(f"本回合获得税收与利润共计 {income}。")

        if random.random() < 0.3:
            events_pool = [
                ("发现走私金库", "money", 300, "WARNING"),
                ("外来难民涌入", "population", 50, "WARNING"),
                ("未知瘟疫蔓延", "population", -30, "CRITICAL"),
                ("基础设施老化", "money", -200, "CRITICAL")
            ]
            ev_name, ev_type, ev_val, ev_level = random.choice(events_pool)
            if ev_type == "money":
                self.money += ev_val
                if ev_val > 0:
                    self.total_income += ev_val
                else:
                    self.total_spent += abs(ev_val)
                self.add_log(f"突发事件【{ev_name}】：经费变动 {ev_val}。", ev_level)
            else:
                self.population += ev_val
                if ev_val < 0:
                    self.total_pop_lost += abs(ev_val)
                self.add_log(f"突发事件【{ev_name}】：人口变动 {ev_val} 人。", ev_level)

        if not self.terrorists_active:
            police = sum(row.count("警察局") for row in self.grid)
            military = sum(row.count("武装设施") for row in self.grid)

            base_chance = 0.15 + (self.population / 5000) + (black_markets * 0.1)
            reduction = (police * 0.05) + (military * 0.1) + (monuments * 0.15)
            final_chance = max(0.05, base_chance - reduction)

            if random.random() < final_chance:
                self.trigger_riot()
        else:
            self.add_log("暴乱仍在持续！造成了经济损失和人员伤亡！", "CRITICAL")
            self.money -= 200
            self.total_spent += 200
            self.population -= 20
            self.total_pop_lost += 20

            tx, ty = self.terrorist_location
            if self.grid[ty][tx] != "空地" and random.random() < 0.4:
                destroyed_fac = self.grid[ty][tx]
                self.grid[ty][tx] = "空地"
                self.add_log(f"惨剧：暴徒摧毁了位于 ({tx}, {ty}) 的 {destroyed_fac}！", "CRITICAL")

        if self.money < 0: 
            self.money = 0

        if self.population <= 0:
            print(f"\n{Colors.BG_RED}{Colors.WHITE}[FATAL ERROR] 城市人口已清零。系统崩溃。游戏失败。{Colors.RESET}\n")
            self.print_news_headline()
            return False

        return True

    def run(self):
        print(f"{Colors.CYAN}系统启动中...{Colors.RESET}")
        time.sleep(0.5)
        print(f"欢迎来到城市管理终端。输入 {Colors.YELLOW}/帮助{Colors.RESET} 获取指令列表。")
        while True:
            try:
                cmd = input(f"{Colors.GREEN}root@city-admin:~#{Colors.RESET} ")
                if not self.process_command(cmd):
                    print(f"{Colors.CYAN}系统关闭。{Colors.RESET}")
                    break
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}检测到中断信号，正在退出...{Colors.RESET}")
                break
            except EOFError:
                print(f"\n{Colors.YELLOW}输入结束，正在退出...{Colors.RESET}")
                break

if __name__ == '__main__':
    game = CityGame()
    game.run()
