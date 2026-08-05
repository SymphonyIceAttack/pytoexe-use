# -*- coding: utf-8 -*-
"""
弈境五子棋 1.0（沉浸式自适应版）

功能：
- 人机对战：普通 / 中等 / 困难 / 噩梦四档 AI
- 双人本地对战
- 人机模式每局随机决定谁执黑先行
- 三种常见规则：自由规则、标准规则、连珠规则（黑方禁手）
- 悔棋、提示、落子编号、最后落子标记
- AI：威胁搜索 + 迭代加深 Negamax + Alpha-Beta 剪枝 + 置换表 + 启发式排序

运行：python 精美五子棋.py
依赖：仅 Python 标准库（建议 Python 3.9+）
"""

from __future__ import annotations

import math
import queue
import random
import threading
import time
import tkinter as tk
from dataclasses import dataclass
from tkinter import ttk
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


EMPTY = 0
BLACK = 1
WHITE = 2
BOARD_SIZE = 15
WIN_SCORE = 10**9
INF = 10**18
DIRECTIONS = ((1, 0), (0, 1), (1, 1), (1, -1))

RULE_FREESTYLE = "自由规则"
RULE_STANDARD = "标准规则"
RULE_RENJU = "连珠规则"

MODE_AI = "人机对战"
MODE_PVP = "双人对战"

DIFF_NORMAL = "普通"
DIFF_MEDIUM = "中等"
DIFF_HARD = "困难"
DIFF_NIGHTMARE = "噩梦"


@dataclass(frozen=True)
class Move:
    x: int
    y: int
    color: int


class SearchTimeout(Exception):
    pass


def opponent(color: int) -> int:
    return WHITE if color == BLACK else BLACK


def inside(x: int, y: int, size: int = BOARD_SIZE) -> bool:
    return 0 <= x < size and 0 <= y < size


def count_line(board: Sequence[Sequence[int]], x: int, y: int,
               color: int, dx: int, dy: int) -> int:
    total = 1
    nx, ny = x + dx, y + dy
    while inside(nx, ny, len(board)) and board[ny][nx] == color:
        total += 1
        nx += dx
        ny += dy
    nx, ny = x - dx, y - dy
    while inside(nx, ny, len(board)) and board[ny][nx] == color:
        total += 1
        nx -= dx
        ny -= dy
    return total


def is_win(board: Sequence[Sequence[int]], x: int, y: int,
           color: int, rules: str) -> bool:
    """判断最后一步是否获胜。"""
    lengths = [count_line(board, x, y, color, dx, dy) for dx, dy in DIRECTIONS]
    if rules == RULE_FREESTYLE:
        return any(n >= 5 for n in lengths)
    if rules == RULE_STANDARD:
        return any(n == 5 for n in lengths)
    # 连珠：黑方必须恰好五连，白方五连及以上均胜。
    if color == BLACK:
        return any(n == 5 for n in lengths)
    return any(n >= 5 for n in lengths)


def _segment_includes(a: int, b: int, target: int) -> bool:
    return min(a, b) <= target <= max(a, b)


def _has_open_four_in_direction(board: List[List[int]], origin: Tuple[int, int],
                                dx: int, dy: int) -> bool:
    """是否存在包含 origin 的连续活四（.XXXX.）。"""
    ox, oy = origin
    size = len(board)
    # 枚举活四起点相对 origin 的偏移。
    for start in range(-3, 1):
        coords = [(ox + (start + i) * dx, oy + (start + i) * dy) for i in range(4)]
        if not all(inside(x, y, size) and board[y][x] == BLACK for x, y in coords):
            continue
        if (ox, oy) not in coords:
            continue
        lx, ly = ox + (start - 1) * dx, oy + (start - 1) * dy
        rx, ry = ox + (start + 4) * dx, oy + (start + 4) * dy
        if (inside(lx, ly, size) and inside(rx, ry, size)
                and board[ly][lx] == EMPTY and board[ry][rx] == EMPTY):
            return True
    return False


def _winning_points_in_direction(board: List[List[int]], origin: Tuple[int, int],
                                 dx: int, dy: int) -> int:
    """统计此方向可一手形成黑方恰好五连的落点数量。"""
    ox, oy = origin
    size = len(board)
    wins = 0
    for step in range(-5, 6):
        x, y = ox + step * dx, oy + step * dy
        if not inside(x, y, size) or board[y][x] != EMPTY:
            continue
        board[y][x] = BLACK
        n = count_line(board, x, y, BLACK, dx, dy)
        # 形成的五连必须同时包含原落子。
        if n == 5:
            # 求连续段两端，确认 origin 在该段内。
            sx, sy = x, y
            while inside(sx - dx, sy - dy, size) and board[sy - dy][sx - dx] == BLACK:
                sx -= dx
                sy -= dy
            ex, ey = x, y
            while inside(ex + dx, ey + dy, size) and board[ey + dy][ex + dx] == BLACK:
                ex += dx
                ey += dy
            if ((dx == 0 or _segment_includes(sx, ex, ox))
                    and (dy == 0 or _segment_includes(sy, ey, oy))):
                wins += 1
        board[y][x] = EMPTY
    return wins


def forbidden_reason(board: List[List[int]], x: int, y: int) -> Optional[str]:
    """
    连珠规则黑方禁手判定。

    检查：长连、四四、三三。算法使用“落子后真实威胁”模拟，覆盖常见直线与跳形。
    调用时棋子应已临时放在 board[y][x]。
    """
    if board[y][x] != BLACK:
        return None

    lengths = [count_line(board, x, y, BLACK, dx, dy) for dx, dy in DIRECTIONS]
    if any(n >= 6 for n in lengths):
        return "长连禁手"

    # 黑方恰好五连优先成立，不再按三三/四四判禁。
    if any(n == 5 for n in lengths):
        return None

    four_directions = 0
    for dx, dy in DIRECTIONS:
        if _winning_points_in_direction(board, (x, y), dx, dy) > 0:
            four_directions += 1
    if four_directions >= 2:
        return "四四禁手"

    open_three_directions = 0
    size = len(board)
    for dx, dy in DIRECTIONS:
        # 已经构成“四”的方向不再重复计作“三”。
        if _winning_points_in_direction(board, (x, y), dx, dy) > 0:
            continue
        found = False
        # 若在同方向补一手能形成包含原落子的活四，则当前方向构成“活三威胁”。
        for step in range(-4, 5):
            tx, ty = x + step * dx, y + step * dy
            if not inside(tx, ty, size) or board[ty][tx] != EMPTY:
                continue
            board[ty][tx] = BLACK
            if not any(count_line(board, tx, ty, BLACK, ddx, ddy) >= 6
                       for ddx, ddy in DIRECTIONS):
                if _has_open_four_in_direction(board, (x, y), dx, dy):
                    found = True
            board[ty][tx] = EMPTY
            if found:
                break
        if found:
            open_three_directions += 1
    if open_three_directions >= 2:
        return "三三禁手"
    return None


def legal_move(board: List[List[int]], x: int, y: int,
               color: int, rules: str) -> Tuple[bool, Optional[str]]:
    if not inside(x, y, len(board)):
        return False, "超出棋盘"
    if board[y][x] != EMPTY:
        return False, "此处已有棋子"
    if rules == RULE_RENJU and color == BLACK:
        board[y][x] = BLACK
        reason = forbidden_reason(board, x, y)
        board[y][x] = EMPTY
        if reason:
            return False, reason
    return True, None


class GomokuAI:
    """带迭代加深、Alpha-Beta、置换表与威胁排序的五子棋 AI。"""

    def __init__(self, size: int = BOARD_SIZE) -> None:
        self.size = size
        rng = random.Random(20260730)
        self.zobrist = [
            [[rng.getrandbits(64) for _ in range(3)] for _ in range(size)]
            for _ in range(size)
        ]
        self.tt: Dict[Tuple[int, int, str], Tuple[int, int, str, Optional[Tuple[int, int]]]] = {}
        self.deadline = 0.0
        self.nodes = 0
        self.rules = RULE_FREESTYLE
        self.max_branch = 12

    def _hash_board(self, board: Sequence[Sequence[int]]) -> int:
        h = 0
        for y, row in enumerate(board):
            for x, color in enumerate(row):
                if color:
                    h ^= self.zobrist[y][x][color]
        return h

    def _time_check(self) -> None:
        self.nodes += 1
        if self.nodes % 256 == 0 and time.perf_counter() >= self.deadline:
            raise SearchTimeout

    def choose_move(self, board: List[List[int]], color: int,
                    difficulty: str, rules: str) -> Optional[Tuple[int, int]]:
        self.rules = rules
        self.nodes = 0
        occupied = sum(cell != EMPTY for row in board for cell in row)
        if occupied == 0:
            c = self.size // 2
            openings = [(c, c), (c - 1, c), (c + 1, c), (c, c - 1), (c, c + 1)]
            legal = [p for p in openings if legal_move(board, p[0], p[1], color, rules)[0]]
            return random.choice(legal or [(c, c)])

        candidates = self._ordered_candidates(board, color, limit=18)
        if not candidates:
            return None

        # 先找立即获胜。
        wins = []
        for x, y in candidates:
            if not legal_move(board, x, y, color, rules)[0]:
                continue
            board[y][x] = color
            if is_win(board, x, y, color, rules):
                wins.append((x, y))
            board[y][x] = EMPTY
        if wins:
            return random.choice(wins)

        # 再堵对方一步胜点。
        foe = opponent(color)
        blocks = []
        for x, y in self._candidate_cells(board, radius=2):
            if board[y][x] != EMPTY:
                continue
            ok, _ = legal_move(board, x, y, foe, rules)
            if not ok:
                continue
            board[y][x] = foe
            won = is_win(board, x, y, foe, rules)
            board[y][x] = EMPTY
            if won and legal_move(board, x, y, color, rules)[0]:
                blocks.append((x, y))
        if blocks:
            return max(blocks, key=lambda p: self._move_order_score(board, p[0], p[1], color))

        if difficulty == DIFF_NORMAL:
            ranked = [(self._move_order_score(board, x, y, color), (x, y))
                      for x, y in candidates
                      if legal_move(board, x, y, color, rules)[0]]
            ranked.sort(reverse=True)
            if not ranked:
                return None
            # 普通难度保留一定随机性，但不会完全乱下。
            pool = ranked[:min(5, len(ranked))]
            weights = [max(1.0, (len(pool) - i) ** 2) for i in range(len(pool))]
            return random.choices([p for _, p in pool], weights=weights, k=1)[0]

        if  difficulty == DIFF_MEDIUM:
            time_limit = 0.9
            max_depth = 2
            self.max_branch = 10
        elif difficulty == DIFF_HARD:
            time_limit = 0.3 if occupied < 8 else 2.6
            max_depth = 4 if occupied < 28 else 3
            self.max_branch = 14

        else:
            time_limit = 0.3 if occupied < 8 else 6.8
            max_depth = 5 if occupied < 24 else 4
            self.max_branch = 18

        self.deadline = time.perf_counter() + time_limit
        self.tt.clear()
        root_hash = self._hash_board(board)
        best_move = candidates[0]

        for depth in range(1, max_depth + 1):
            try:
                score, move = self._root_search(board, color, depth, root_hash)
                if move is not None:
                    best_move = move
                if abs(score) >= WIN_SCORE - 1000:
                    break
            except SearchTimeout:
                break
        return best_move

    def _root_search(self, board: List[List[int]], color: int, depth: int,
                     board_hash: int) -> Tuple[int, Optional[Tuple[int, int]]]:
        alpha, beta = -INF, INF
        best_score = -INF
        best_move: Optional[Tuple[int, int]] = None
        candidates = self._ordered_candidates(board, color, self.max_branch)
        tt_entry = self.tt.get((board_hash, color, self.rules))
        if tt_entry and tt_entry[3] in candidates:
            candidates.remove(tt_entry[3])
            candidates.insert(0, tt_entry[3])

        for x, y in candidates:
            self._time_check()
            ok, _ = legal_move(board, x, y, color, self.rules)
            if not ok:
                continue
            board[y][x] = color
            nh = board_hash ^ self.zobrist[y][x][color]
            if is_win(board, x, y, color, self.rules):
                score = WIN_SCORE
            else:
                score = -self._negamax(board, opponent(color), depth - 1,
                                       -beta, -alpha, nh, (x, y, color), 1)
            board[y][x] = EMPTY
            if score > best_score:
                best_score, best_move = score, (x, y)
            alpha = max(alpha, score)
        return best_score, best_move

    def _negamax(self, board: List[List[int]], player: int, depth: int,
                 alpha: int, beta: int, board_hash: int,
                 last_move: Tuple[int, int, int], ply: int) -> int:
        self._time_check()
        lx, ly, last_color = last_move
        if is_win(board, lx, ly, last_color, self.rules):
            return -WIN_SCORE + ply
        if depth <= 0:
            return self._evaluate(board, player)

        key = (board_hash, player, self.rules)
        original_alpha = alpha
        entry = self.tt.get(key)
        preferred = None
        if entry and entry[0] >= depth:
            e_depth, e_score, flag, preferred = entry
            if flag == "EXACT":
                return e_score
            if flag == "LOWER":
                alpha = max(alpha, e_score)
            elif flag == "UPPER":
                beta = min(beta, e_score)
            if alpha >= beta:
                return e_score

        moves = self._ordered_candidates(board, player, self.max_branch)
        if preferred in moves:
            moves.remove(preferred)
            moves.insert(0, preferred)
        if not moves:
            return 0

        best = -INF
        best_move = None
        for x, y in moves:
            ok, _ = legal_move(board, x, y, player, self.rules)
            if not ok:
                continue
            board[y][x] = player
            nh = board_hash ^ self.zobrist[y][x][player]
            score = -self._negamax(board, opponent(player), depth - 1,
                                   -beta, -alpha, nh, (x, y, player), ply + 1)
            board[y][x] = EMPTY
            if score > best:
                best, best_move = score, (x, y)
            alpha = max(alpha, score)
            if alpha >= beta:
                break

        if best == -INF:
            best = 0
        flag = "EXACT"
        if best <= original_alpha:
            flag = "UPPER"
        elif best >= beta:
            flag = "LOWER"
        self.tt[key] = (depth, best, flag, best_move)
        return best

    def _candidate_cells(self, board: Sequence[Sequence[int]], radius: int = 2) -> List[Tuple[int, int]]:
        occupied = [(x, y) for y in range(self.size) for x in range(self.size)
                    if board[y][x] != EMPTY]
        if not occupied:
            c = self.size // 2
            return [(c, c)]
        cells = set()
        for x, y in occupied:
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if inside(nx, ny, self.size) and board[ny][nx] == EMPTY:
                        cells.add((nx, ny))
        return list(cells)

    def _ordered_candidates(self, board: List[List[int]], color: int,
                            limit: int) -> List[Tuple[int, int]]:
        cells = self._candidate_cells(board, radius=2)
        center = self.size // 2
        ranked = []
        for x, y in cells:
            if not legal_move(board, x, y, color, self.rules)[0]:
                continue
            score = self._move_order_score(board, x, y, color)
            score -= int((abs(x - center) + abs(y - center)) * 2)
            ranked.append((score, random.random(), (x, y)))
        ranked.sort(reverse=True)
        return [p for _, __, p in ranked[:limit]]

    def _shape_score(self, board: Sequence[Sequence[int]], x: int, y: int,
                     color: int, dx: int, dy: int) -> Tuple[int, int, int]:
        """返回（连续长度，开放端数，近线跳形加分）。"""
        size = self.size
        left = 0
        nx, ny = x - dx, y - dy
        while inside(nx, ny, size) and board[ny][nx] == color:
            left += 1
            nx -= dx
            ny -= dy
        open_left = inside(nx, ny, size) and board[ny][nx] == EMPTY

        right = 0
        nx, ny = x + dx, y + dy
        while inside(nx, ny, size) and board[ny][nx] == color:
            right += 1
            nx += dx
            ny += dy
        open_right = inside(nx, ny, size) and board[ny][nx] == EMPTY
        length = 1 + left + right
        opens = int(open_left) + int(open_right)

        # 识别一步内的跳形，例如 XX.X、X.XX。
        jump = 0
        for sign in (-1, 1):
            ax, ay = x + sign * dx, y + sign * dy
            bx, by = x + sign * 2 * dx, y + sign * 2 * dy
            cx, cy = x + sign * 3 * dx, y + sign * 3 * dy
            if (inside(ax, ay, size) and inside(bx, by, size)
                    and board[ay][ax] == EMPTY and board[by][bx] == color):
                jump += 1
                if inside(cx, cy, size) and board[cy][cx] == color:
                    jump += 1
        return length, opens, jump

    @staticmethod
    def _shape_value(length: int, opens: int, jump: int) -> int:
        if length >= 5:
            return 80_000_000
        if length == 4:
            return 3_000_000 if opens == 2 else (350_000 if opens == 1 else 0)
        if length == 3:
            base = 120_000 if opens == 2 else (14_000 if opens == 1 else 0)
            return base + jump * 8_000
        if length == 2:
            base = 3_500 if opens == 2 else (500 if opens == 1 else 0)
            return base + jump * 1_200
        return 80 * opens + jump * 220

    def _move_order_score(self, board: List[List[int]], x: int, y: int,
                          color: int) -> int:
        if board[y][x] != EMPTY:
            return -INF
        attack_values = []
        defend_values = []
        foe = opponent(color)
        for dx, dy in DIRECTIONS:
            attack_values.append(self._shape_value(*self._shape_score(board, x, y, color, dx, dy)))
            defend_values.append(self._shape_value(*self._shape_score(board, x, y, foe, dx, dy)))
        attack_values.sort(reverse=True)
        defend_values.sort(reverse=True)
        score = sum(attack_values) + int(sum(defend_values) * 0.92)
        # 多方向威胁组合远强于单线普通形。
        if len(attack_values) >= 2:
            score += attack_values[0] * min(2, attack_values[1] // 10_000)
        if len(defend_values) >= 2:
            score += defend_values[0] * min(2, defend_values[1] // 10_000)
        return score

    def _all_lines(self, board: Sequence[Sequence[int]]) -> Iterable[List[int]]:
        n = self.size
        for y in range(n):
            yield list(board[y])
        for x in range(n):
            yield [board[y][x] for y in range(n)]
        for start_x in range(n):
            line = []
            x, y = start_x, 0
            while inside(x, y, n):
                line.append(board[y][x])
                x += 1
                y += 1
            if len(line) >= 5:
                yield line
        for start_y in range(1, n):
            line = []
            x, y = 0, start_y
            while inside(x, y, n):
                line.append(board[y][x])
                x += 1
                y += 1
            if len(line) >= 5:
                yield line
        for start_x in range(n):
            line = []
            x, y = start_x, 0
            while inside(x, y, n):
                line.append(board[y][x])
                x -= 1
                y += 1
            if len(line) >= 5:
                yield line
        for start_y in range(1, n):
            line = []
            x, y = n - 1, start_y
            while inside(x, y, n):
                line.append(board[y][x])
                x -= 1
                y += 1
            if len(line) >= 5:
                yield line

    def _line_value(self, line: Sequence[int], color: int) -> int:
        foe = opponent(color)
        text = "#" + "".join("X" if c == color else "." if c == EMPTY else "O" for c in line) + "#"
        patterns = (
            ("XXXXX", 30_000_000),
            (".XXXX.", 1_500_000),
            ("OXXXX.", 180_000), (".XXXXO", 180_000),
            (".XXX.X.", 210_000), (".XX.XX.", 210_000), (".X.XXX.", 210_000),
            (".XXX.", 70_000),
            (".XX.X.", 55_000), (".X.XX.", 55_000),
            ("OXXX..", 8_000), ("..XXXO", 8_000),
            (".XX..", 2_000), ("..XX.", 2_000),
            (".X.X.", 1_600),
        )
        score = 0
        for pattern, value in patterns:
            start = 0
            while True:
                idx = text.find(pattern, start)
                if idx < 0:
                    break
                score += value
                start = idx + 1
        return score

    def _evaluate(self, board: Sequence[Sequence[int]], perspective: int) -> int:
        foe = opponent(perspective)
        own = 0
        enemy = 0
        for line in self._all_lines(board):
            own += self._line_value(line, perspective)
            enemy += self._line_value(line, foe)
        return own - int(enemy * 1.08)


class GomokuApp:
    BG = "#10151f"
    PANEL = "#171f2d"
    PANEL_2 = "#202b3d"
    TEXT = "#eef4ff"
    MUTED = "#95a3b8"
    ACCENT = "#5b8cff"
    ACCENT_HOVER = "#79a1ff"
    GOLD = "#f1c56b"
    BOARD_LIGHT = "#e8bd79"
    BOARD_DARK = "#c88946"
    GRID = "#5a3820"
    DANGER = "#ff6b72"
    SUCCESS = "#62d6a6"

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("弈境 1.0 · 五子棋")
        self.root.configure(bg=self.BG)
        self.root.minsize(720, 640)
        self._maximize_window()
        self._layout_mode = ""
        self._layout_after_id = None
        self.menu_open = False
        self.ui_scale = self._detect_ui_scale()
        # 菜单单独放大：Pydroid/Android 的 Tk 字体经常比桌面端偏小。
        self.menu_scale = max(1.15, min(1.60, self.ui_scale * 1.05))
        self._apply_tk_scaling()

        self.board: List[List[int]] = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.history: List[Move] = []
        self.current = BLACK
        self.game_over = False
        self.ai_thinking = False
        self.ai_color: Optional[int] = None
        self.human_color: Optional[int] = None
        self.hover: Optional[Tuple[int, int]] = None
        self.hint_cell: Optional[Tuple[int, int]] = None
        self.game_token = 0
        self.ai_queue: "queue.Queue[Tuple[int, Optional[Tuple[int, int]], str]]" = queue.Queue()
        self.hint_queue: "queue.Queue[Tuple[int, Optional[Tuple[int, int]], str]]" = queue.Queue()

        self.mode_var = tk.StringVar(value=MODE_AI)
        self.diff_var = tk.StringVar(value=DIFF_MEDIUM)
        self.rule_var = tk.StringVar(value=RULE_FREESTYLE)
        self.number_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="准备开始")
        self.detail_var = tk.StringVar(value="人机对战 · 中等 · 自由规则")
        self.black_name_var = tk.StringVar(value="玩家")
        self.white_name_var = tk.StringVar(value="AI")
        self.black_state_var = tk.StringVar(value="● 黑方")
        self.white_state_var = tk.StringVar(value="○ 白方")

        self._setup_styles()
        self._build_ui()
        self._bind_keys()
        self.root.bind("<Configure>", self._on_root_configure, add="+")
        self.root.after(80, self._poll_ai_queue)
        self.root.after(120, self._apply_responsive_layout)
        self.new_game()


    def _detect_ui_scale(self) -> float:
        sw = max(720, self.root.winfo_screenwidth())
        sh = max(640, self.root.winfo_screenheight())
        short = min(sw, sh)
        if short >= 1100:
            return 1.55
        if short >= 900:
            return 1.38
        if short >= 760:
            return 1.22
        return 1.0

    def _apply_tk_scaling(self) -> None:
        """放大高分屏上的 ttk / 原生控件。"""
        try:
            self.root.tk.call("tk", "scaling", round(min(1.60, 1.15 * self.ui_scale), 2))
        except tk.TclError:
            pass

    def _maximize_window(self) -> None:
        """跨 Windows/Linux/Pydroid 尽量占满可用屏幕。"""
        self.root.update_idletasks()
        try:
            self.root.state("zoomed")
            return
        except tk.TclError:
            pass
        try:
            self.root.attributes("-zoomed", True)
            return
        except tk.TclError:
            pass
        sw = max(720, self.root.winfo_screenwidth())
        sh = max(640, self.root.winfo_screenheight())
        self.root.geometry(f"{sw}x{sh}+0+0")

    def _on_root_configure(self, event: tk.Event) -> None:
        if event.widget is not self.root:
            return
        if self._layout_after_id is not None:
            try:
                self.root.after_cancel(self._layout_after_id)
            except tk.TclError:
                pass
        self._layout_after_id = self.root.after(90, self._apply_responsive_layout)

    def _apply_responsive_layout(self) -> None:
        """棋盘与快捷栏横竖自适应；设置是独立浮层，不再撑出长黑区域。"""
        self._layout_after_id = None
        if not hasattr(self, "main_frame"):
            return
        w = max(1, self.main_frame.winfo_width())
        h = max(1, self.main_frame.winfo_height())
        portrait = h > w * 1.02
        self._layout_mode = "portrait" if portrait else "landscape"

        # 清理旧布局后重新放置。
        self.board_shell.place_forget()
        self.quick_bar.place_forget()

        if portrait:
            # 竖屏：棋盘占上部，快捷操作压缩到下方，不再出现贯穿全屏的黑色空栏。
            quick_h = min(0.22, max(0.16, 230 / max(h, 1)))
            self.board_shell.place(relx=0, rely=0, relwidth=1, relheight=1-quick_h)
            self.quick_bar.place(relx=0, rely=1-quick_h, relwidth=1, relheight=quick_h)
            self._layout_quick_bar(portrait=True)
        else:
            # 横屏：右侧保留紧凑快捷栏，棋盘尽可能大。
            quick_w = min(0.22, max(0.17, 320 / max(w, 1)))
            self.board_shell.place(relx=0, rely=0, relwidth=1-quick_w, relheight=1)
            self.quick_bar.place(relx=1-quick_w, rely=0, relwidth=quick_w, relheight=1)
            self._layout_quick_bar(portrait=False)

        if self.menu_open:
            self.menu_shade.place(relx=0, rely=0, relwidth=1, relheight=1)
            if portrait:
                # 只包住设置内容，避免下面留下大块黑色空白。
                self.panel.place(relx=0.04, rely=0.08, relwidth=0.92, relheight=0.70)
            else:
                panel_ratio = 0.44 if w / max(h, 1) < 1.6 else 0.38
                self.panel.place(relx=1-panel_ratio-0.02, rely=0.07,
                                 relwidth=panel_ratio, relheight=0.86)
            self.panel.lift()
            # 设置已打开时隐藏齿轮，避免按钮压在菜单上。
            self.gear_canvas.place_forget()
        else:
            self.panel.place_forget()
            self.menu_shade.place_forget()
            gear_size = max(58, int(64 * self.ui_scale))
            margin = max(12, int(16 * self.ui_scale))
            # 齿轮放在棋盘区域右上角，不覆盖快捷栏。
            board_right = w if portrait else int(w * (1-quick_w))
            self.gear_canvas.place(x=board_right-gear_size-margin, y=margin,
                                   width=gear_size, height=gear_size)
            self.gear_canvas.tk.call("raise", self.gear_canvas._w)
            self._draw_gear_icon()

        self.root.after_idle(self._center_menu_content)
        self.root.after_idle(self.draw_board)

    def toggle_menu(self) -> None:
        self.menu_open = not self.menu_open
        self._apply_responsive_layout()

    def close_menu(self, _event=None) -> None:
        if self.menu_open:
            self.menu_open = False
            self._apply_responsive_layout()

    def _draw_gear_icon(self) -> None:
        """用 Canvas 自绘齿轮，避免 Android 缺少齿轮字符字体。"""
        if not hasattr(self, "gear_canvas"):
            return
        c = self.gear_canvas
        c.delete("all")
        w = max(1, c.winfo_width())
        h = max(1, c.winfo_height())
        cx, cy = w / 2, h / 2
        r = min(w, h) * 0.25
        c.create_oval(2, 2, w - 2, h - 2, fill=self.PANEL,
                      outline="#41516a", width=max(1, int(self.ui_scale)))
        # 八个齿。
        for i in range(8):
            a = math.radians(i * 45)
            x1 = cx + math.cos(a) * r * 0.92
            y1 = cy + math.sin(a) * r * 0.92
            x2 = cx + math.cos(a) * r * 1.42
            y2 = cy + math.sin(a) * r * 1.42
            c.create_line(x1, y1, x2, y2, fill=self.TEXT,
                          width=max(3, int(5 * self.ui_scale)), capstyle="projecting")
        c.create_oval(cx-r, cy-r, cx+r, cy+r, fill=self.TEXT, outline="")
        c.create_oval(cx-r*0.42, cy-r*0.42, cx+r*0.42, cy+r*0.42,
                      fill=self.PANEL, outline="")

    def _font(self, size: int, weight: str = "normal") -> Tuple[str, int, str]:
        scaled = max(8, int(round(size * self.ui_scale)))
        return ("Microsoft YaHei UI", scaled, weight)

    def _menu_font(self, size: int, weight: str = "normal") -> Tuple[str, int, str]:
        """菜单专用字体，比棋盘标题更大，兼顾 Android 高分屏。"""
        scaled = max(11, int(round(size * self.menu_scale)))
        return ("Microsoft YaHei UI", scaled, weight)

    def _m(self, value: int) -> int:
        """菜单尺寸缩放。"""
        return max(1, int(round(value * self.menu_scale)))

    def _refresh_menu_scrollregion(self) -> None:
        """同步菜单滚动范围；内容不足时自然居中，内容过长时可滚动。"""
        if not hasattr(self, "menu_canvas"):
            return
        self.menu_canvas.update_idletasks()
        cw = max(1, self.menu_canvas.winfo_width())
        ch = max(1, self.menu_canvas.winfo_height())
        req_h = max(1, self.menu_content.winfo_reqheight())
        self.menu_canvas.itemconfigure(self.menu_window, width=max(1, cw - self._m(26)))
        offset = max(0, (ch - req_h) // 2)
        self.menu_canvas.coords(self.menu_window, cw // 2, offset)
        self.menu_canvas.configure(scrollregion=(0, 0, cw, max(ch, req_h + offset)))

    def _on_menu_mousewheel(self, event: tk.Event) -> None:
        if not self.menu_open or not hasattr(self, "menu_canvas"):
            return
        delta = -1 if getattr(event, "delta", 0) > 0 else 1
        self.menu_canvas.yview_scroll(delta * 3, "units")

    def _center_menu_content(self) -> None:
        """设置内容在浮层中居中，不让竖屏产生长空白。"""
        if not hasattr(self, "menu_content"):
            return
        self.menu_content.place_configure(relx=0.5, rely=0.5, anchor="center", relwidth=0.90)

    def _setup_styles(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TCheckbutton", background=self.PANEL, foreground=self.TEXT,
                        font=self._menu_font(12), indicatorcolor=self.PANEL_2,
                        padding=self._m(3))
        style.map("TCheckbutton", background=[("active", self.PANEL)],
                  foreground=[("active", self.TEXT)],
                  indicatorcolor=[("selected", self.ACCENT)])

    def _build_ui(self) -> None:
        header = tk.Frame(self.root, bg=self.BG, height=int(72 * self.ui_scale))
        header.pack(fill="x", padx=24, pady=(16, 8))
        header.pack_propagate(False)
        tk.Label(header, text="弈境", fg=self.TEXT, bg=self.BG,
                 font=self._font(26, "bold")).pack(side="left")
        tk.Label(header, text="GOMOKU  1.0", fg=self.ACCENT, bg=self.BG,
                 font=("Segoe UI", max(10, int(11 * self.ui_scale)), "bold")).pack(side="left", padx=(10, 0), pady=(10, 0))
        tk.Label(header, text="静心落子 · 智慧博弈", fg=self.MUTED, bg=self.BG,
                 font=self._font(10)).pack(side="right", pady=(10, 0))

        main = tk.Frame(self.root, bg=self.BG)
        main.pack(fill="both", expand=True, padx=24, pady=(0, 22))
        self.main_frame = main

        self.board_shell = tk.Frame(main, bg="#0b1018", highlightthickness=1,
                                    highlightbackground="#2b374a")
        self.canvas = tk.Canvas(self.board_shell, bg=self.BOARD_LIGHT, highlightthickness=0,
                                cursor="hand2")
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)
        self.canvas.bind("<Configure>", lambda _e: self.draw_board())
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Leave>", self._on_leave)
        self.canvas.bind("<Button-1>", self._on_click)

        # 右侧/底部快捷栏：阵容与对局操作不放进设置。
        self.quick_bar = tk.Frame(main, bg=self.PANEL, highlightthickness=1,
                                  highlightbackground="#2b374a")
        self.quick_content = tk.Frame(self.quick_bar, bg=self.PANEL)
        tk.Label(self.quick_content, textvariable=self.status_var, bg=self.PANEL,
                 fg=self.TEXT, anchor="w", font=self._menu_font(16, "bold")).pack(fill="x")
        tk.Label(self.quick_content, textvariable=self.detail_var, bg=self.PANEL,
                 fg=self.MUTED, anchor="w", font=self._menu_font(10)).pack(fill="x", pady=(self._m(2), self._m(5)))
        self.quick_players = tk.Frame(self.quick_content, bg=self.PANEL)
        self.quick_players.pack(fill="x")
        self.black_card = self._player_card(self.quick_players, self.black_state_var, self.black_name_var, True)
        self.white_card = self._player_card(self.quick_players, self.white_state_var, self.white_name_var, False)
        self.quick_controls = tk.Frame(self.quick_content, bg=self.PANEL)
        self.quick_controls.pack(fill="x", pady=(self._m(7), 0))
        self.main_action_button = self._button(self.quick_controls, "新对局", self._main_action, primary=True)
        self.main_action_button.pack(fill="x", pady=(0, self._m(6)))
        self.quick_button_row = tk.Frame(self.quick_controls, bg=self.PANEL)
        self.quick_button_row.pack(fill="x")
        self.undo_button = self._button(self.quick_button_row, "悔棋", self.request_undo)
        self.undo_button.pack(side="left", fill="x", expand=True, padx=(0, self._m(4)))
        self.hint_button = self._button(self.quick_button_row, "提示", self.request_hint)
        self.hint_button.pack(side="left", fill="x", expand=True, padx=(self._m(4), 0))

        # 设置遮罩与独立设置面板。
        self.menu_shade = tk.Frame(main, bg="#080c12", cursor="hand2")
        self.menu_shade.bind("<Button-1>", self.close_menu)
        self.panel = tk.Frame(main, bg=self.PANEL, highlightthickness=2,
                              highlightbackground="#41516a")
        self.gear_canvas = tk.Canvas(main, bg=self.BG, highlightthickness=0, cursor="hand2")
        self.gear_canvas.bind("<Button-1>", lambda _e: self.toggle_menu())
        self.gear_canvas.bind("<Configure>", lambda _e: self._draw_gear_icon())

        content = tk.Frame(self.panel, bg=self.PANEL)
        self.menu_content = content
        content.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.90)

        title_row = tk.Frame(content, bg=self.PANEL)
        title_row.pack(fill="x", pady=(0, self._m(8)))
        tk.Label(title_row, text="对局设置", bg=self.PANEL, fg=self.TEXT,
                 anchor="w", font=self._menu_font(20, "bold")).pack(side="left")
        tk.Button(title_row, text="关闭  ×", command=self.close_menu,
                  bd=0, relief="flat", cursor="hand2", bg=self.PANEL_2,
                  fg=self.TEXT, activebackground="#2b3a51", activeforeground="white",
                  font=self._menu_font(13, "bold"), padx=self._m(12),
                  pady=self._m(7)).pack(side="right")

        self._separator(content)
        self._section_title(content, "对局模式")
        self.mode_buttons = self._segmented(content, [MODE_AI, MODE_PVP], self.mode_var,
                                            self._on_settings_change)
        self._section_title(content, "AI 强度")
        self.diff_buttons = self._segmented(content,
                                            [DIFF_NORMAL, DIFF_MEDIUM, DIFF_HARD, DIFF_NIGHTMARE],
                                            self.diff_var, self._on_settings_change)
        self._section_title(content, "棋局规则（点击选择）")
        self.rule_buttons = self._rule_options(content)
        option_row = tk.Frame(content, bg=self.PANEL)
        option_row.pack(fill="x", pady=(self._m(8), self._m(2)))
        ttk.Checkbutton(option_row, text="显示落子编号", variable=self.number_var,
                        command=self.draw_board).pack(side="left")

    def _layout_quick_bar(self, portrait: bool) -> None:
        """根据方向重排快捷栏，让竖屏保持紧凑。"""
        self.quick_content.place_forget()
        if portrait:
            self.quick_content.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.94)
            # 竖屏隐藏过长的阵容卡，只显示精简状态；避免底部栏过高。
            self.quick_players.pack_forget()
            self.quick_controls.pack(fill="x", pady=(self._m(5), 0))
        else:
            self.quick_content.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.88)
            if not self.quick_players.winfo_manager():
                self.quick_players.pack(fill="x", before=self.quick_controls)
            self.quick_controls.pack(fill="x", pady=(self._m(7), 0))

    def _separator(self, parent: tk.Widget) -> None:
        tk.Frame(parent, bg="#2b374a", height=1).pack(
            fill="x", padx=self._m(3), pady=self._m(5))

    def _section_title(self, parent: tk.Widget, text: str) -> None:
        tk.Label(parent, text=text, bg=self.PANEL, fg=self.MUTED,
                 anchor="w", font=self._menu_font(12, "bold")).pack(
                     fill="x", padx=self._m(2), pady=(self._m(3), self._m(4)))

    def _segmented(self, parent: tk.Widget, values: List[str], variable: tk.StringVar,
                   command) -> List[tk.Button]:
        frame = tk.Frame(parent, bg=self.PANEL_2)
        frame.pack(fill="x", padx=self._m(2))
        buttons = []
        for value in values:
            btn = tk.Button(frame, text=value, bd=0, relief="flat", cursor="hand2",
                            font=self._menu_font(13, "bold"), padx=self._m(7), pady=self._m(7),
                            command=lambda v=value: self._set_segment(variable, v, command))
            btn.pack(side="left", fill="x", expand=True, padx=1, pady=1)
            buttons.append(btn)
        self.root.after_idle(lambda: self._refresh_segment(buttons, values, variable.get()))
        return buttons

    def _rule_options(self, parent: tk.Widget) -> List[tk.Button]:
        """用三块大按钮代替小下拉框，平板上无需眯眼选择规则。"""
        frame = tk.Frame(parent, bg=self.PANEL)
        frame.pack(fill="x", padx=self._m(2))
        options = [
            (RULE_FREESTYLE, "五连及以上获胜"),
            (RULE_STANDARD, "必须恰好五连"),
            (RULE_RENJU, "黑方三三、四四、长连禁手"),
        ]
        buttons: List[tk.Button] = []
        for value, description in options:
            btn = tk.Button(
                frame, text=f"{value}  ·  {description}", anchor="w", justify="left",
                bd=0, relief="flat", cursor="hand2",
                font=self._menu_font(13, "bold"), padx=self._m(12), pady=self._m(7),
                command=lambda v=value: self._set_rule(v))
            btn.pack(fill="x", pady=self._m(2))
            buttons.append(btn)
        self.root.after_idle(self._refresh_rule_buttons)
        return buttons

    def _set_rule(self, value: str) -> None:
        self.rule_var.set(value)
        self._refresh_rule_buttons()
        self._on_settings_change()

    def _refresh_rule_buttons(self) -> None:
        if not hasattr(self, "rule_buttons"):
            return
        values = [RULE_FREESTYLE, RULE_STANDARD, RULE_RENJU]
        for btn, value in zip(self.rule_buttons, values):
            active = value == self.rule_var.get()
            btn.configure(
                bg=self.ACCENT if active else self.PANEL_2,
                fg="white" if active else self.TEXT,
                activebackground=self.ACCENT_HOVER if active else "#2b3a51",
                activeforeground="white",
                highlightthickness=1,
                highlightbackground=self.ACCENT if active else "#2b374a")

    def _set_segment(self, variable: tk.StringVar, value: str, command) -> None:
        variable.set(value)
        command()

    def _refresh_segment(self, buttons: List[tk.Button], values: List[str], selected: str) -> None:
        for btn, value in zip(buttons, values):
            active = value == selected
            btn.configure(bg=self.ACCENT if active else self.PANEL_2,
                          fg="white" if active else self.MUTED,
                          activebackground=self.ACCENT_HOVER if active else "#28364b",
                          activeforeground="white")

    def _player_card(self, parent: tk.Widget, state_var: tk.StringVar,
                     name_var: tk.StringVar, black: bool) -> tk.Frame:
        card = tk.Frame(parent, bg=self.PANEL_2, highlightthickness=1,
                        highlightbackground="#2b374a")
        card.pack(fill="x", pady=self._m(2))
        stone_size = self._m(30)
        stone = tk.Canvas(card, width=stone_size, height=stone_size,
                          bg=self.PANEL_2, highlightthickness=0)
        stone.pack(side="left", padx=(self._m(11), self._m(8)), pady=self._m(5))
        inset = max(5, int(stone_size * 0.15))
        edge = stone_size - inset
        if black:
            stone.create_oval(inset, inset, edge, edge, fill="#101318", outline="#49515f", width=1)
            stone.create_oval(int(stone_size * 0.28), int(stone_size * 0.22),
                              int(stone_size * 0.46), int(stone_size * 0.40),
                              fill="#4b5360", outline="")
        else:
            stone.create_oval(inset, inset, edge, edge, fill="#f2f4f7", outline="#aeb7c4", width=1)
            stone.create_oval(int(stone_size * 0.28), int(stone_size * 0.22),
                              int(stone_size * 0.46), int(stone_size * 0.40),
                              fill="#ffffff", outline="")
        info = tk.Frame(card, bg=self.PANEL_2)
        info.pack(side="left", fill="both", expand=True, pady=self._m(4))
        tk.Label(info, textvariable=state_var, bg=self.PANEL_2, fg=self.MUTED,
                 anchor="w", font=self._menu_font(10)).pack(fill="x")
        tk.Label(info, textvariable=name_var, bg=self.PANEL_2, fg=self.TEXT,
                 anchor="w", font=self._menu_font(13, "bold")).pack(fill="x")
        return card

    def _button(self, parent: tk.Widget, text: str, command,
                primary: bool = False) -> tk.Button:
        bg = self.ACCENT if primary else self.PANEL_2
        active = self.ACCENT_HOVER if primary else "#2b3a51"
        return tk.Button(parent, text=text, command=command, bd=0, relief="flat",
                         cursor="hand2", bg=bg, fg="white" if primary else self.TEXT,
                         activebackground=active, activeforeground="white",
                         font=self._menu_font(14, "bold"),
                         padx=self._m(12), pady=self._m(10),
                         highlightthickness=1,
                         highlightbackground=self.ACCENT if primary else "#34445d",
                         highlightcolor=self.ACCENT_HOVER, takefocus=False)

    def _show_modal(self, title: str, message: str, confirm_text: str,
                    on_confirm, cancel_text: Optional[str] = "取消") -> None:
        """完全自绘的无边框弹窗，避开 Android/Pydroid 系统标题栏乱码。"""
        if getattr(self, "_modal", None) is not None:
            try:
                if self._modal.winfo_exists():
                    self._modal.lift()
                    return
            except tk.TclError:
                pass

        dialog = tk.Toplevel(self.root)
        self._modal = dialog
        dialog.withdraw()
        dialog.overrideredirect(True)
        dialog.configure(bg="#56647a")
        try:
            dialog.attributes("-topmost", True)
        except tk.TclError:
            pass
        dialog.transient(self.root)

        scale = max(1.0, self.menu_scale)
        width = min(max(int(430 * scale), 430), max(430, self.root.winfo_width() - 40))
        height = int(260 * scale)
        outer = tk.Frame(dialog, bg="#56647a", padx=2, pady=2)
        outer.pack(fill="both", expand=True)
        body = tk.Frame(outer, bg=self.PANEL)
        body.pack(fill="both", expand=True)

        header = tk.Frame(body, bg=self.PANEL_2, height=max(46, int(48 * scale)))
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text=title, bg=self.PANEL_2, fg=self.TEXT,
                 font=self._menu_font(14, "bold"), anchor="w").pack(
                     side="left", fill="both", expand=True, padx=self._m(12))

        def close() -> None:
            try:
                dialog.grab_release()
            except tk.TclError:
                pass
            try:
                dialog.destroy()
            except tk.TclError:
                pass
            self._modal = None

        close_btn = tk.Button(header, text="×", command=close, bd=0, relief="flat",
                              bg=self.PANEL_2, fg=self.TEXT,
                              activebackground=self.DANGER, activeforeground="white",
                              font=self._menu_font(18, "bold"), padx=self._m(12))
        close_btn.pack(side="right", fill="y")

        content = tk.Frame(body, bg=self.PANEL)
        content.pack(fill="both", expand=True, padx=self._m(18), pady=self._m(15))
        tk.Label(content, text=message, bg=self.PANEL, fg=self.TEXT,
                 justify="left", anchor="nw", wraplength=max(320, width-self._m(70)),
                 font=self._menu_font(14)).pack(fill="both", expand=True)

        actions = tk.Frame(content, bg=self.PANEL)
        actions.pack(fill="x", pady=(self._m(14), 0))
        if cancel_text:
            self._button(actions, cancel_text, close).pack(
                side="left", fill="x", expand=True, padx=(0, self._m(5)))

        def confirm() -> None:
            close()
            self.root.after(20, on_confirm)

        self._button(actions, confirm_text, confirm, primary=True).pack(
            side="left", fill="x", expand=True,
            padx=((self._m(5) if cancel_text else 0), 0))

        self.root.update_idletasks()
        rw, rh = self.root.winfo_width(), self.root.winfo_height()
        rx, ry = self.root.winfo_rootx(), self.root.winfo_rooty()
        x = rx + max(0, (rw - width) // 2)
        y = ry + max(0, (rh - height) // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        dialog.deiconify()
        dialog.lift()
        try:
            dialog.grab_set()
        except tk.TclError:
            pass
        dialog.focus_force()
        dialog.bind("<Escape>", lambda _e: close())
        dialog.bind("<Return>", lambda _e: confirm())

    def _show_notice(self, title: str, message: str, button_text: str = "确定",
                     on_confirm=lambda: None) -> None:
        self._show_modal(title, message, button_text, on_confirm, cancel_text=None)

    def request_undo(self) -> None:
        if self.mode_var.get() == MODE_PVP and self.history and not self.ai_thinking:
            player = self.black_name_var.get() if self.current == BLACK else self.white_name_var.get()
            self._show_modal(
                "确认悔棋",
                f"{player} 请求撤回上一手。\n确认后将立即恢复到上一回合。",
                "确认悔棋", self.undo)
        else:
            self.undo()

    def request_hint(self) -> None:
        if self.mode_var.get() == MODE_PVP and not self.game_over and not self.ai_thinking:
            player = self.black_name_var.get() if self.current == BLACK else self.white_name_var.get()
            self._show_modal(
                "确认提示",
                f"{player} 请求查看当前局面的推荐落点。\n提示可能影响公平对局，是否继续？",
                "查看提示", self.show_hint)
        else:
            self.show_hint()

    def _bind_keys(self) -> None:
        self.root.bind("<Escape>", self.close_menu)
        self.root.bind("<Key-n>", lambda _e: self._main_action())
        self.root.bind("<Key-N>", lambda _e: self._main_action())
        self.root.bind("<Key-u>", lambda _e: self.request_undo())
        self.root.bind("<Key-U>", lambda _e: self.request_undo())
        self.root.bind("<Key-h>", lambda _e: self.request_hint())
        self.root.bind("<Key-H>", lambda _e: self.request_hint())

    def _refresh_main_action(self) -> None:
        if not hasattr(self, "main_action_button"):
            return
        if self.mode_var.get() == MODE_PVP and not self.game_over:
            self.main_action_button.configure(text="认输", command=self._main_action,
                                              bg=self.DANGER, activebackground="#ff858b")
        else:
            self.main_action_button.configure(text="新对局", command=self._main_action,
                                              bg=self.ACCENT, activebackground=self.ACCENT_HOVER)

    def _main_action(self) -> None:
        if self.mode_var.get() == MODE_PVP and not self.game_over:
            player = self.black_name_var.get() if self.current == BLACK else self.white_name_var.get()
            self._show_modal(
                "确认认输",
                f"{player} 确定要认输吗？\n确认后本局立即结束，对方获胜。",
                "确认认输", self.surrender)
        else:
            self.new_game()

    def surrender(self) -> None:
        if self.mode_var.get() != MODE_PVP or self.game_over:
            return
        loser = self.black_name_var.get() if self.current == BLACK else self.white_name_var.get()
        winner = self.white_name_var.get() if self.current == BLACK else self.black_name_var.get()
        self.game_over = True
        self.status_var.set(f"{loser} 认输 · {winner} 获胜")
        self._update_player_cards()
        self._refresh_main_action()

    def _on_settings_change(self) -> None:
        self._refresh_segment(self.mode_buttons, [MODE_AI, MODE_PVP], self.mode_var.get())
        self._refresh_segment(self.diff_buttons, [DIFF_NORMAL, DIFF_MEDIUM, DIFF_HARD, DIFF_NIGHTMARE], self.diff_var.get())
        self._refresh_rule_buttons()
        state = "normal" if self.mode_var.get() == MODE_AI else "disabled"
        for btn in self.diff_buttons:
            btn.configure(state=state)
        self.new_game()

    def new_game(self) -> None:
        self.game_token += 1
        self.board = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.history.clear()
        self.current = BLACK
        self.game_over = False
        self.ai_thinking = False
        self.hover = None
        self.hint_cell = None

        mode = self.mode_var.get()
        rules = self.rule_var.get()
        if mode == MODE_AI:
            # 随机决定玩家或 AI 执黑；黑方固定先行。
            self.ai_color = random.choice([BLACK, WHITE])
            self.human_color = opponent(self.ai_color)
            self.black_name_var.set("AI" if self.ai_color == BLACK else "玩家")
            self.white_name_var.set("AI" if self.ai_color == WHITE else "玩家")
            self.detail_var.set(f"{mode} · {self.diff_var.get()} · {rules}")
        else:
            self.ai_color = None
            self.human_color = None
            self.black_name_var.set("玩家一")
            self.white_name_var.set("玩家二")
            self.detail_var.set(f"{mode} · {rules}")
        self._update_status()
        self._refresh_main_action()
        self.draw_board()
        if mode == MODE_AI and self.ai_color == BLACK:
            self.root.after(350, self._start_ai_turn)

    def _board_geometry(self) -> Tuple[float, float, float, float]:
        w = max(200, self.canvas.winfo_width())
        h = max(200, self.canvas.winfo_height())
        pad = max(16, min(w, h) * 0.035)
        side = min(w, h) - 2 * pad
        gap = side / (BOARD_SIZE - 1)
        ox = (w - side) / 2
        # 竖屏棋盘区域顶部对齐；横屏保持居中。
        oy = pad if getattr(self, "_layout_mode", "landscape") == "portrait" else (h - side) / 2
        return ox, oy, gap, side

    def draw_board(self) -> None:
        if not hasattr(self, "canvas"):
            return
        c = self.canvas
        c.delete("all")
        w = max(1, c.winfo_width())
        h = max(1, c.winfo_height())

        # 低成本木纹渐变。
        bands = 50
        for i in range(bands):
            t = i / max(1, bands - 1)
            r = int(232 * (1 - t) + 200 * t)
            g = int(189 * (1 - t) + 137 * t)
            b = int(121 * (1 - t) + 70 * t)
            y0 = h * i / bands
            y1 = h * (i + 1) / bands + 1
            c.create_rectangle(0, y0, w, y1, fill=f"#{r:02x}{g:02x}{b:02x}", outline="")
        grain_offsets = (-2, 1, -1, 2)
        for i in range(18):
            yy = (i * 47 + 19) % max(h, 1)
            c.create_line(0, yy, w, yy + grain_offsets[i % len(grain_offsets)],
                          fill="#b8783e", width=1, stipple="gray50")

        ox, oy, gap, side = self._board_geometry()
        # 棋盘边缘与网格。
        c.create_rectangle(ox - gap * 0.45, oy - gap * 0.45,
                           ox + side + gap * 0.45, oy + side + gap * 0.45,
                           outline="#7c4c26", width=2)
        for i in range(BOARD_SIZE):
            x = ox + i * gap
            y = oy + i * gap
            c.create_line(ox, y, ox + side, y, fill=self.GRID, width=1)
            c.create_line(x, oy, x, oy + side, fill=self.GRID, width=1)

        for sx, sy in ((3, 3), (11, 3), (7, 7), (3, 11), (11, 11)):
            x, y = ox + sx * gap, oy + sy * gap
            r = max(2.4, gap * 0.095)
            c.create_oval(x - r, y - r, x + r, y + r, fill=self.GRID, outline="")

        # 悬停预览与提示。
        if (self.hover and not self.game_over and not self.ai_thinking
                and self.board[self.hover[1]][self.hover[0]] == EMPTY):
            x, y = self.hover
            ok, _ = legal_move(self.board, x, y, self.current, self.rule_var.get())
            if ok:
                self._draw_stone(x, y, self.current, ghost=True)
        if self.hint_cell and self.board[self.hint_cell[1]][self.hint_cell[0]] == EMPTY:
            hx, hy = self.hint_cell
            px, py = ox + hx * gap, oy + hy * gap
            rr = gap * 0.28
            c.create_oval(px - rr, py - rr, px + rr, py + rr,
                          outline=self.ACCENT, width=3, dash=(4, 3))

        for idx, move in enumerate(self.history, start=1):
            self._draw_stone(move.x, move.y, move.color, number=idx)

        if self.history:
            last = self.history[-1]
            px, py = ox + last.x * gap, oy + last.y * gap
            rr = max(3, gap * 0.09)
            marker = "#ff6b72" if last.color == BLACK else "#d74752"
            c.create_oval(px - rr, py - rr, px + rr, py + rr, fill=marker, outline="")

    def _draw_stone(self, bx: int, by: int, color: int,
                    ghost: bool = False, number: Optional[int] = None) -> None:
        c = self.canvas
        ox, oy, gap, _ = self._board_geometry()
        x, y = ox + bx * gap, oy + by * gap
        r = gap * 0.43
        if ghost:
            fill = "#2e333b" if color == BLACK else "#f7f7f7"
            c.create_oval(x-r, y-r, x+r, y+r, fill=fill, outline="", stipple="gray50")
            return
        # 阴影
        c.create_oval(x-r+2.4, y-r+3.5, x+r+2.4, y+r+3.5,
                      fill="#6b472e", outline="", stipple="gray50")
        if color == BLACK:
            c.create_oval(x-r, y-r, x+r, y+r, fill="#14171d", outline="#050608", width=1)
            c.create_oval(x-r*0.55, y-r*0.65, x-r*0.05, y-r*0.15,
                          fill="#4c535e", outline="")
            num_color = "#dfe6f1"
        else:
            c.create_oval(x-r, y-r, x+r, y+r, fill="#f1f3f6", outline="#a5abb5", width=1)
            c.create_oval(x-r*0.58, y-r*0.68, x-r*0.05, y-r*0.15,
                          fill="#ffffff", outline="")
            num_color = "#303641"
        if number is not None and self.number_var.get():
            c.create_text(x, y, text=str(number), fill=num_color,
                          font=self._font(max(7, int(gap * 0.22)), "bold"))

    def _pixel_to_cell(self, px: float, py: float) -> Optional[Tuple[int, int]]:
        ox, oy, gap, _ = self._board_geometry()
        x = round((px - ox) / gap)
        y = round((py - oy) / gap)
        if not inside(x, y):
            return None
        cx, cy = ox + x * gap, oy + y * gap
        if math.hypot(px - cx, py - cy) <= gap * 0.48:
            return x, y
        return None

    def _on_motion(self, event: tk.Event) -> None:
        cell = self._pixel_to_cell(event.x, event.y)
        if cell != self.hover:
            self.hover = cell
            self.draw_board()

    def _on_leave(self, _event: tk.Event) -> None:
        self.hover = None
        self.draw_board()

    def _on_click(self, event: tk.Event) -> None:
        if self.game_over or self.ai_thinking:
            return
        if self.mode_var.get() == MODE_AI and self.current != self.human_color:
            return
        cell = self._pixel_to_cell(event.x, event.y)
        if cell is None:
            return
        self._play_move(cell[0], cell[1])

    def _play_move(self, x: int, y: int) -> bool:
        ok, reason = legal_move(self.board, x, y, self.current, self.rule_var.get())
        if not ok:
            self.status_var.set(reason or "无法落子")
            self.root.bell()
            return False
        color = self.current
        self.board[y][x] = color
        self.history.append(Move(x, y, color))
        self.hint_cell = None
        self.draw_board()

        if is_win(self.board, x, y, color, self.rule_var.get()):
            self.game_over = True
            winner = self.black_name_var.get() if color == BLACK else self.white_name_var.get()
            self.status_var.set(f"{winner} 获胜")
            self._update_player_cards()
            self._refresh_main_action()
            return True
        if len(self.history) >= BOARD_SIZE * BOARD_SIZE:
            self.game_over = True
            self.status_var.set("和棋")
            self._refresh_main_action()
            return True

        self.current = opponent(self.current)
        self._update_status()
        if self.mode_var.get() == MODE_AI and self.current == self.ai_color:
            self.root.after(160, self._start_ai_turn)
        return True

    def _start_ai_turn(self) -> None:
        if (self.game_over or self.ai_thinking or self.mode_var.get() != MODE_AI
                or self.current != self.ai_color):
            return
        self.ai_thinking = True
        self.status_var.set("AI 正在思考…")
        self._update_player_cards()
        token = self.game_token
        board_copy = [row[:] for row in self.board]
        color = int(self.ai_color)
        difficulty = self.diff_var.get()
        rules = self.rule_var.get()

        def worker() -> None:
            try:
                engine = GomokuAI(BOARD_SIZE)
                move = engine.choose_move(board_copy, color, difficulty, rules)
                self.ai_queue.put((token, move, ""))
            except Exception as exc:  # 避免后台线程异常导致界面卡死
                self.ai_queue.put((token, None, f"AI 异常：{exc}"))

        threading.Thread(target=worker, daemon=True).start()

    def _poll_ai_queue(self) -> None:
        try:
            while True:
                token, move, error = self.ai_queue.get_nowait()
                if token != self.game_token:
                    continue
                self.ai_thinking = False
                if error:
                    self.status_var.set(error)
                    self._update_player_cards()
                    continue
                if move is None:
                    self.status_var.set("AI 无合法落点")
                    self.game_over = True
                    self._refresh_main_action()
                    continue
                # 用户可能在 AI 计算期间新开了对局，token 已排除这种情况。
                self._play_move(move[0], move[1])
        except queue.Empty:
            pass
        self.root.after(80, self._poll_ai_queue)

    def _update_status(self) -> None:
        if self.game_over:
            self._update_player_cards()
            return
        name = self.black_name_var.get() if self.current == BLACK else self.white_name_var.get()
        side = "黑方" if self.current == BLACK else "白方"
        self.status_var.set(f"{name} 落子 · {side}")
        self._update_player_cards()
        self._refresh_main_action()

    def _update_player_cards(self) -> None:
        black_active = not self.game_over and self.current == BLACK
        white_active = not self.game_over and self.current == WHITE
        self.black_state_var.set("● 黑方 · 行棋中" if black_active else "● 黑方")
        self.white_state_var.set("○ 白方 · 行棋中" if white_active else "○ 白方")
        self.black_card.configure(highlightbackground=self.ACCENT if black_active else self.PANEL_2)
        self.white_card.configure(highlightbackground=self.ACCENT if white_active else self.PANEL_2)

    def undo(self) -> None:
        # 真人模式的确认只在 request_undo() 中弹出一次。
        # 这里直接执行撤回，避免确认后再次调用旧确认函数而无响应。
        if self.ai_thinking:
            # 使正在计算的结果失效。
            self.game_token += 1
            self.ai_thinking = False
        if not self.history:
            self.status_var.set("暂无可悔棋步数")
            return
        self.game_over = False
        steps = 1
        if self.mode_var.get() == MODE_AI:
            # 尽量回到玩家行动前；开局 AI 只下一手时则退一手。
            steps = 2 if len(self.history) >= 2 else 1
        for _ in range(min(steps, len(self.history))):
            move = self.history.pop()
            self.board[move.y][move.x] = EMPTY
        self.current = BLACK if len(self.history) % 2 == 0 else WHITE
        self.hint_cell = None
        self._update_status()
        self._refresh_main_action()
        self.draw_board()
        if self.mode_var.get() == MODE_AI and self.current == self.ai_color:
            self.root.after(220, self._start_ai_turn)

    def show_hint(self) -> None:
        if self.game_over or self.ai_thinking:
            return
        # 真人模式的确认只在 request_hint() 中弹出一次。
        # 确认后直接进入分析，避免重复确认和未定义旧函数导致无响应。
        token = self.game_token
        board_copy = [row[:] for row in self.board]
        color = self.current
        rules = self.rule_var.get()
        self.status_var.set("正在分析提示…")
        self.ai_thinking = True

        def worker() -> None:
            try:
                # 提示固定用中等强度，兼顾质量与速度。
                engine = GomokuAI(BOARD_SIZE)
                move = engine.choose_move(board_copy, color, DIFF_MEDIUM, rules)
                self.hint_queue.put((token, move, ""))
            except Exception as exc:
                self.hint_queue.put((token, None, f"提示异常：{exc}"))

        # 提示使用独立队列，避免与 AI 自动落子消息互相抢占。
        def poll_hint() -> None:
            try:
                while True:
                    t, move, error = self.hint_queue.get_nowait()
                    if t != token:
                        continue
                    self.ai_thinking = False
                    if error:
                        self.status_var.set(error)
                    else:
                        self.hint_cell = move
                        self._update_status()
                    self.draw_board()
                    return
            except queue.Empty:
                pass
            if token == self.game_token and self.ai_thinking:
                self.root.after(70, poll_hint)

        threading.Thread(target=worker, daemon=True).start()
        self.root.after(70, poll_hint)


def main() -> None:
    root = tk.Tk()
    try:
        root.tk.call("tk", "scaling", 1.1)
    except tk.TclError:
        pass
    GomokuApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
