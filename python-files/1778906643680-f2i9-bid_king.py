#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
竞拍之王：艾哈迈德 快速约束枚举器

特点：
1. 每一回合可以追加任意多条信息；
2. 支持：总 / 红 / 橙 / 紫 / 蓝 / 绿 / 白 / 绿白；
3. 支持：数量、格数、均格、均价；
4. 支持：=, <=, >=, <, >；
5. 使用 bitset 动态规划，不再做 6 个颜色的暴力笛卡尔积枚举；
6. 通常在 max 109 72 或 max 120 200 级别下可在 1 秒内 run。

输入例子：
    总 数量 <= 109, 总 格数 = 72
    橙 均格 = 3.2
    紫 均格 = 3.33
    蓝 均价 = 1342.5
    绿白 数量 = 19
    run

说明：
- 均格：按“总格数 / 数量”四舍五入到 2 位小数后比较。
- 均价：只用来反推“数量是否可能”。例如 1342.5 会允许使 n * 1342.5 可由整数总价四舍五入得到的数量。
  若你已经确定蓝色数量就是 2，请直接追加：蓝 数量 = 2。
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN, ROUND_CEILING
from typing import Dict, List, Tuple, Iterable, Optional, Set
import re
import time
import unicodedata

# ===================== 可调参数 =====================
MAX_N_DEFAULT = 120       # 默认总藏品数量搜索上限
MAX_G_DEFAULT = 200       # 默认总格数搜索上限
MAX_SHOW_DEFAULT = 12     # 默认展示多少条样例路线
AVG_DIGITS = 2            # 游戏均格/均价通常按 2 位小数显示
KEEP_SPLITS = 3           # 每条绿白合计路线最多展示几个绿/白拆分样例

# 单色内部代号
COLOR_ORDER = ["o", "p", "b", "gw", "r"]
SINGLE_COLORS = ["o", "p", "b", "g", "w", "r"]
ZH = {
    "o": "橙", "p": "紫", "b": "蓝", "g": "绿", "w": "白", "r": "红", "gw": "绿白", "total": "总"
}

COLOR_ALIASES = {
    "总": "total", "全部": "total", "全体": "total", "本场": "total",
    "红": "r", "红色": "r", "红货": "r", "红色藏品": "r",
    "橙": "o", "橙色": "o", "橙色藏品": "o",
    "紫": "p", "紫色": "p", "紫色藏品": "p",
    "蓝": "b", "蓝色": "b", "蓝色藏品": "b",
    "绿": "g", "绿色": "g", "绿色藏品": "g",
    "白": "w", "白色": "w", "白色藏品": "w",
    "绿白": "gw", "绿白色": "gw", "绿色和白色": "gw", "绿和白": "gw", "绿、白": "gw", "绿+白": "gw",
}

METRIC_ALIASES = {
    "数量": "n", "件数": "n", "个数": "n", "藏品数量": "n", "总数量": "n",
    "格数": "g", "总格数": "g", "占格": "g", "占用格数": "g",
    "均格": "avg_g", "平均格数": "avg_g", "平均占格": "avg_g",
    "均价": "avg_price", "平均价": "avg_price", "平均价格": "avg_price",
}

OPS = {"=": "==", "＝": "==", "==": "==", "≤": "<=", "≥": ">=", "<=" : "<=", ">=" : ">=", "<": "<", ">": ">"}

# ===================== 基础工具 =====================

def get_str_width(text) -> int:
    """计算中文终端里的视觉宽度。"""
    width = 0
    for ch in str(text):
        width += 2 if unicodedata.east_asian_width(ch) in ("F", "W") else 1
    return width


def align_str(text, width: int, align: str = "left") -> str:
    text = str(text)
    fill = max(0, width - get_str_width(text))
    if align == "right":
        return " " * fill + text
    if align == "center":
        left = fill // 2
        return " " * left + text + " " * (fill - left)
    return text + " " * fill


def bit_values(bits: int) -> Iterable[int]:
    """把 bitset 里的所有 set bit 转成数值。"""
    while bits:
        lsb = bits & -bits
        yield lsb.bit_length() - 1
        bits ^= lsb


def bit_count(bits: int) -> int:
    return bits.bit_count()


def ceil_decimal(x: Decimal) -> int:
    return int(x.to_integral_value(rounding=ROUND_CEILING))


def D(x) -> Decimal:
    return Decimal(str(x))


def q2(x: Decimal) -> Decimal:
    """按游戏显示习惯：向下截断到 AVG_DIGITS 位小数。"""
    quantum = Decimal("1").scaleb(-AVG_DIGITS)  # 0.01
    return x.quantize(quantum, rounding=ROUND_DOWN)


def shown_ratio(num: int, den: int) -> Optional[Decimal]:
    if den <= 0:
        return None
    return q2(Decimal(num) / Decimal(den))


def eval_op(left, op: str, right) -> bool:
    """比较 Decimal / int。"""
    if not isinstance(left, Decimal):
        left = D(left)
    if not isinstance(right, Decimal):
        right = D(right)
    if op == "==": return left == right
    if op == "<=" : return left <= right
    if op == ">=" : return left >= right
    if op == "<": return left < right
    if op == ">": return left > right
    raise ValueError(f"未知比较符: {op}")


def avg_price_possible(n: int, target: Decimal) -> bool:
    """
    判断是否存在整数总价 P，使 floor_to_2(P/n) == target。
    使用游戏式截断：target <= P/n < target + 0.01。
    """
    if n <= 0:
        return False
    step = Decimal("1").scaleb(-AVG_DIGITS)  # 0.01
    lo = target * n
    hi = (target + step) * n
    p = ceil_decimal(lo)
    return Decimal(p) < hi


def convolve_g_bits(a: int, b: int, max_g: int) -> int:
    """格数 bitset 求和卷积：{x+y | x in A, y in B}。"""
    if a == 0 or b == 0:
        return 0
    mask = (1 << (max_g + 1)) - 1
    # 遍历 set bit 更少的一边，减少移位次数
    if bit_count(a) <= bit_count(b):
        small, large = a, b
    else:
        small, large = b, a
    out = 0
    while small:
        lsb = small & -small
        shift = lsb.bit_length() - 1
        out |= large << shift
        small ^= lsb
    return out & mask

# ===================== 规则结构 =====================

@dataclass(frozen=True)
class Rule:
    raw: str
    scope: str          # color / gw / total
    color: str          # o/p/b/g/w/r/gw/total
    metric: str         # n/g/avg_g/avg_price
    op: str             # ==/<=/>=/</>
    value: Decimal

    def pretty(self) -> str:
        metric_zh = {"n": "数量", "g": "格数", "avg_g": "均格", "avg_price": "均价"}[self.metric]
        return f"{ZH.get(self.color, self.color)} {metric_zh} {self.op} {self.value}"


def normalize_cmd(s: str) -> str:
    return (s.replace("，", ",")
             .replace("；", ";")
             .replace("：", ":")
             .replace("（", "(").replace("）", ")")
             .replace("≤", "<=").replace("≥", ">=")
             .replace("＝", "="))


def parse_rules(cmd: str) -> List[Rule]:
    """
    支持无空格输入：总藏品数量<=109 / 橙色格数=20 / 白色均格=23。
    一行可以含多条规则。
    """
    text = normalize_cmd(cmd)

    color_pat = r"绿\+白|绿色和白色|绿和白|绿、白|绿白色|绿白|红色藏品|橙色藏品|紫色藏品|蓝色藏品|绿色藏品|白色藏品|红货|红色|橙色|紫色|蓝色|绿色|白色|总|全部|全体|本场|红|橙|紫|蓝|绿|白"
    metric_pat = r"藏品数量|总数量|数量|件数|个数|占用格数|总格数|平均格数|平均占格|平均价格|平均价|格数|占格|均格|均价"
    op_pat = r"==|<=|>=|=|<|>"
    num_pat = r"-?\d+(?:\.\d+)?"
    pattern = re.compile(rf"({color_pat})\s*(?:的)?\s*({metric_pat})\s*({op_pat})\s*({num_pat})")

    rules: List[Rule] = []
    for m in pattern.finditer(text):
        color_raw, metric_raw, op_raw, val_raw = m.groups()
        color = COLOR_ALIASES[color_raw]
        metric = METRIC_ALIASES[metric_raw]
        op = OPS[op_raw]
        scope = "total" if color == "total" else ("gw" if color == "gw" else "color")
        value = Decimal(val_raw)
        rules.append(Rule(
            raw=m.group(0), scope=scope, color=color, metric=metric, op=op, value=value
        ))
    return rules

# ===================== 规则校验 =====================

def n_rule_ok(n: int, r: Rule) -> bool:
    if r.metric == "n":
        return eval_op(n, r.op, r.value)
    if r.metric == "avg_price":
        # 均价只可靠地约束“数量分母”。等式很有用；不等式在没有总价上下界时通常不提供有效约束。
        if n <= 0:
            return False
        if r.op == "==":
            return avg_price_possible(n, r.value)
        return True
    return True


def ng_rule_ok(n: int, g: int, r: Rule) -> bool:
    if r.metric == "g":
        return eval_op(g, r.op, r.value)
    if r.metric == "avg_g":
        if n <= 0:
            return False
        avg = shown_ratio(g, n)
        return eval_op(avg, r.op, r.value)
    return True


def rules_for(rules: List[Rule], scope: str, color: str) -> List[Rule]:
    if scope == "color":
        return [r for r in rules if r.scope == "color" and r.color == color]
    return [r for r in rules if r.scope == scope]


def candidate_ok(n: int, g: int, rs: List[Rule]) -> bool:
    for r in rs:
        if r.metric in ("n", "avg_price"):
            if not n_rule_ok(n, r):
                return False
        elif r.metric in ("g", "avg_g"):
            if not ng_rule_ok(n, g, r):
                return False
    return True

# ===================== Domain / DP =====================

Domain = Dict[int, int]  # n -> bitset of possible g


def infer_effective_max(rules: List[Rule], max_n: int, max_g: int) -> Tuple[int, int]:
    """从总数量/总格数上界或等式自动缩小搜索空间。"""
    eff_n, eff_g = max_n, max_g
    for r in rules:
        if r.scope == "total" and r.metric == "n" and r.op in ("==", "<=", "<"):
            v = int(r.value)
            eff_n = min(eff_n, v - 1 if r.op == "<" else v)
        if r.scope == "total" and r.metric == "g" and r.op in ("==", "<=", "<"):
            v = int(r.value)
            eff_g = min(eff_g, v - 1 if r.op == "<" else v)
    return max(0, eff_n), max(0, eff_g)


def build_single_color_domain(color: str, rules: List[Rule], max_n: int, max_g: int) -> Domain:
    """为一个单色构建所有合法 (数量, 格数)。"""
    rs = rules_for(rules, "color", color)
    domain: Domain = {}

    # 若有明确格数等式，可以大幅减少遍历
    exact_g_values: Optional[Set[int]] = None
    for r in rs:
        if r.metric == "g" and r.op == "==":
            v = int(r.value)
            exact_g_values = {v} if exact_g_values is None else exact_g_values & {v}

    for n in range(max_n + 1):
        # 先检查只依赖数量的规则
        ok_n = True
        for r in rs:
            if r.metric in ("n", "avg_price") and not n_rule_ok(n, r):
                ok_n = False
                break
        if not ok_n:
            continue

        if n == 0:
            g_iter = [0]
        else:
            # 每件藏品至少占 1 格
            if exact_g_values is not None:
                g_iter = [v for v in exact_g_values if n <= v <= max_g]
            else:
                g_iter = range(n, max_g + 1)

        bits = 0
        for g in g_iter:
            if candidate_ok(n, g, rs):
                bits |= 1 << g
        if bits:
            domain[n] = bits
    return domain


def combine_domains(domains: List[Domain], max_n: int, max_g: int) -> Domain:
    """把多个 group domain 合并成总和 domain。"""
    dp: Domain = {0: 1 << 0}
    for dom in domains:
        new: Domain = {}
        for n0, bits0 in dp.items():
            for n1, bits1 in dom.items():
                nt = n0 + n1
                if nt > max_n:
                    continue
                gbits = convolve_g_bits(bits0, bits1, max_g)
                if gbits:
                    new[nt] = new.get(nt, 0) | gbits
        dp = new
        if not dp:
            break
    return dp


def filter_domain_by_scope(domain: Domain, rules: List[Rule], scope: str, color: str, max_g: int) -> Domain:
    rs = rules_for(rules, scope, color)
    if not rs:
        return domain
    out: Domain = {}
    for n, bits in domain.items():
        # 数量/均价规则先剪掉整个 n
        bad_n = False
        for r in rs:
            if r.metric in ("n", "avg_price") and not n_rule_ok(n, r):
                bad_n = True
                break
        if bad_n:
            continue
        newbits = 0
        for g in bit_values(bits):
            if all(ng_rule_ok(n, g, r) for r in rs if r.metric in ("g", "avg_g")):
                newbits |= 1 << g
        if newbits:
            out[n] = newbits
    return out


def build_all_domains(rules: List[Rule], max_n: int, max_g: int) -> Tuple[Dict[str, Domain], Domain, List[Tuple[str, str, Domain]]]:
    """返回：单色 domains、最终 total domain、group domains。"""
    single = {c: build_single_color_domain(c, rules, max_n, max_g) for c in SINGLE_COLORS}

    # 绿白 group 先由绿 + 白合并，再用绿白规则过滤。
    gw_domain = combine_domains([single["g"], single["w"]], max_n, max_g)
    gw_domain = filter_domain_by_scope(gw_domain, rules, "gw", "gw", max_g)

    groups: List[Tuple[str, str, Domain]] = [
        ("橙", "o", single["o"]),
        ("紫", "p", single["p"]),
        ("蓝", "b", single["b"]),
        ("绿白", "gw", gw_domain),
        ("红", "r", single["r"]),
    ]

    total_domain = combine_domains([g[2] for g in groups], max_n, max_g)
    total_domain = filter_domain_by_scope(total_domain, rules, "total", "total", max_g)
    return single, total_domain, groups

# ===================== 摘要与样例路线 =====================

def count_states(domain: Domain) -> int:
    return sum(bit_count(bits) for bits in domain.values())


def domain_ng_pairs(domain: Domain) -> Iterable[Tuple[int, int]]:
    for n, bits in domain.items():
        for g in bit_values(bits):
            yield n, g


def possible_group_values(group_domain: Domain, rest_domain: Domain, final_domain: Domain, max_g: int) -> Tuple[Set[int], Set[int], Set[Tuple[int, int]]]:
    """某个 group 的 (n,g) 是否能和其余 group 拼成 final_domain。"""
    poss_n: Set[int] = set()
    poss_g: Set[int] = set()
    poss_ng: Set[Tuple[int, int]] = set()

    rest_items = list(rest_domain.items())
    for cn, cbits in group_domain.items():
        for cg in bit_values(cbits):
            ok = False
            for rn, rbits in rest_items:
                tn = cn + rn
                allowed = final_domain.get(tn, 0)
                if not allowed:
                    continue
                if ((rbits << cg) & allowed) != 0:
                    ok = True
                    break
            if ok:
                poss_n.add(cn)
                poss_g.add(cg)
                poss_ng.add((cn, cg))
    return poss_n, poss_g, poss_ng


def format_set_or_range(vals: Set[int], max_list: int = 20) -> str:
    if not vals:
        return "无"
    sv = sorted(vals)
    if len(sv) <= max_list:
        return "{" + ",".join(map(str, sv)) + "}"
    return f"{sv[0]}..{sv[-1]}（共{len(sv)}种）"



def possible_values_for_group_key(groups: List[Tuple[str, str, Domain]], final_domain: Domain, key: str, max_n: int, max_g: int) -> Tuple[Set[int], Set[int], Set[Tuple[int, int]]]:
    """返回某个 group 在所有可行全局解中的真实可能值。"""
    for i, (_name, k, dom) in enumerate(groups):
        if k == key:
            rest = combine_domains([g[2] for j, g in enumerate(groups) if j != i], max_n, max_g)
            return possible_group_values(dom, rest, final_domain, max_g)
    return set(), set(), set()


def ngs_by_n(ngs: Set[Tuple[int, int]]) -> Dict[int, Set[int]]:
    out: Dict[int, Set[int]] = {}
    for n, g in ngs:
        out.setdefault(n, set()).add(g)
    return out


def _detect_step(vals: List[int]) -> Optional[int]:
    if len(vals) < 2:
        return None
    step = vals[1] - vals[0]
    if step <= 0:
        return None
    if all(vals[i] - vals[i - 1] == step for i in range(1, len(vals))):
        return step
    return None


def _format_value_set(vals: Set[int], *, zero_allowed: bool = True, max_small: int = 8) -> str:
    """把数量/格数的可能集合压缩成“有用信息”。

    显示原则：
    - 单值：直接显示 6
    - 小集合：显示 {0,2,6}
    - 明显等差且步长>1：显示 13的倍数 或 4,8,...,32
    - 大段连续区间通常没实战信息：显示 ?
    """
    if not vals:
        return "无"
    sv = sorted(vals)
    if len(sv) == 1:
        return str(sv[0])
    if len(sv) <= max_small:
        return "{" + ",".join(map(str, sv)) + "}"

    step = _detect_step(sv)
    if step is not None:
        # 连续大范围，比如 0..38，信息量很低，直接 ?
        if step == 1:
            return "?"
        # 纯倍数结构最有用，比如 13,26,39...
        if sv[0] == step:
            return f"{step}的倍数≤{sv[-1]}"
        # 其他等差结构也保留
        return f"{sv[0]},{sv[1]},...,{sv[-1]}"

    # 非等差但数量不算太大，仍然给一点信息
    if len(sv) <= 16:
        return "{" + ",".join(map(str, sv)) + "}"
    return "?"


def _display_from_by_n(by_n: Dict[int, Set[int]]) -> str:
    """实战显示规则。

    不是“没锁定就一律问号”。
    - 有小集合/倍数/等差结构：保留信息；
    - 只有完全大范围、连续、无明显约束时：才用 ?。

    四种基本形态：
    - 数量锁定，格数锁定：n/g
    - 数量锁定，格数未锁定但有信息：n/{g1,g2} 或 n/13的倍数≤...
    - 数量未锁定但有信息，格数锁定：{n1,n2}/g 或 ?/g
    - 二者都没有效信息：?/?
    """
    if not by_n:
        return "无"

    all_ns = set(by_n.keys())
    all_gs: Set[int] = set()
    for gs in by_n.values():
        all_gs.update(gs)

    # 红货为 0 的特殊情况：0件就必然0格。
    if all_ns == {0}:
        return "0/0"

    # 如果可能组合很少，而且不是“一个数量对应一堆格数”，直接展示精确组合。
    ngs = {(n, g) for n, gs in by_n.items() for g in gs}
    sorted_ngs = sorted(ngs)
    if len(ngs) <= 6 and not (len(all_ns) == 1 and len(all_gs) > 3):
        parts = [f"{n}/{g}" for n, g in sorted_ngs]
        return " 或 ".join(parts)

    # 中等数量的离散组合也全部保留；输出层会自动换行。
    if 6 < len(ngs) <= 12 and len(all_ns) > 1:
        parts = [f"{n}/{g}" for n, g in sorted_ngs]
        return " 或 ".join(parts)

    n_text = _format_value_set(all_ns)
    g_text = _format_value_set(all_gs)
    return f"{n_text}/{g_text}"


def fmt_ng_with_unknown(n: int, g: int, by_n: Dict[int, Set[int]]) -> str:
    """按全局可行范围显示。保留小集合/倍数信息；只有无信息才用 ?。"""
    return _display_from_by_n(by_n)


def format_ng_compact(ngs: Set[Tuple[int, int]], max_items: int = 8) -> str:
    """把 {(n,g)} 压缩成实战可读形式。"""
    if not ngs:
        return "无"
    return _display_from_by_n(ngs_by_n(ngs))


def build_display_maps(groups: List[Tuple[str, str, Domain]], final_domain: Domain, max_n: int, max_g: int) -> Dict[str, Dict[int, Set[int]]]:
    maps: Dict[str, Dict[int, Set[int]]] = {}
    for _name, key, _dom in groups:
        _ns, _gs, ngs = possible_values_for_group_key(groups, final_domain, key, max_n, max_g)
        maps[key] = ngs_by_n(ngs)
    return maps


def rules_mention_group(rules: List[Rule], key: str) -> bool:
    """用户是否直接输入过这个品质/合计品质的信息。总规则不算。"""
    if key == "gw":
        return any(r.scope == "gw" for r in rules)
    return any(r.scope == "color" and r.color == key for r in rules)


def summarize_groups(groups: List[Tuple[str, str, Domain]], final_domain: Domain, max_n: int, max_g: int) -> List[Tuple[str, str, str]]:
    """给每个 group 输出压缩后的可行 量/格。"""
    rows = []
    for i, (name, key, dom) in enumerate(groups):
        rest = combine_domains([g[2] for j, g in enumerate(groups) if j != i], max_n, max_g)
        _ns, _gs, ngs = possible_group_values(dom, rest, final_domain, max_g)
        rows.append((name, format_ng_compact(ngs), str(len(ngs))))
    return rows


def build_suffix(groups: List[Tuple[str, str, Domain]], max_n: int, max_g: int) -> List[Domain]:
    suffix: List[Domain] = [None] * (len(groups) + 1)  # type: ignore
    suffix[len(groups)] = {0: 1 << 0}
    for i in range(len(groups) - 1, -1, -1):
        suffix[i] = combine_domains([groups[i][2], suffix[i + 1]], max_n, max_g)
    return suffix


def suffix_has(suffix_dom: Domain, n: int, g: int) -> bool:
    return n in suffix_dom and ((suffix_dom[n] >> g) & 1) == 1


def sorted_total_targets(final_domain: Domain, limit_states: int = 300) -> List[Tuple[int, int]]:
    """优先挑总数量小、总格数小的 target 用来生成样例，避免极端输出。"""
    targets = []
    for n in sorted(final_domain.keys()):
        for g in bit_values(final_domain[n]):
            targets.append((n, g))
            if len(targets) >= limit_states:
                return targets
    return targets


def find_gw_splits(gw_n: int, gw_g: int, green_domain: Domain, white_domain: Domain, limit: int = KEEP_SPLITS) -> List[Tuple[int, int, int, int]]:
    """给一个绿白合计，找几个具体的 绿(n,g)+白(n,g) 拆分。"""
    out = []
    for gn, gbits in green_domain.items():
        wn = gw_n - gn
        if wn not in white_domain:
            continue
        wbits = white_domain[wn]
        for gg in bit_values(gbits):
            wg = gw_g - gg
            if wg >= 0 and ((wbits >> wg) & 1):
                out.append((gn, gg, wn, wg))
                if len(out) >= limit:
                    return out
    return out


def generate_examples(groups: List[Tuple[str, str, Domain]], final_domain: Domain, single_domains: Dict[str, Domain], max_n: int, max_g: int, limit: int) -> List[Dict[str, Tuple[int, int]]]:
    """从 final_domain 反向生成少量完整样例路线。

    样例生成时把红货放在最前面，这样可以尽快覆盖红货数量不同的代表路线；
    但样例仍然只是可能世界，不是结论。
    """
    example_groups = sorted(groups, key=lambda item: 0 if item[1] == "r" else 1)
    suffix = build_suffix(example_groups, max_n, max_g)
    examples: List[Dict[str, Tuple[int, int]]] = []

    def dfs(idx: int, rem_n: int, rem_g: int, path: Dict[str, Tuple[int, int]]):
        if len(examples) >= limit:
            return
        if idx == len(example_groups):
            if rem_n == 0 and rem_g == 0:
                if "gw" in path:
                    gw_n, gw_g = path["gw"]
                    splits = find_gw_splits(gw_n, gw_g, single_domains["g"], single_domains["w"], 1)
                    if splits:
                        gn, gg, wn, wg = splits[0]
                        path = dict(path)
                        path["g"] = (gn, gg)
                        path["w"] = (wn, wg)
                examples.append(dict(path))
            return

        _, key, dom = example_groups[idx]
        for n in sorted(dom.keys()):
            if n > rem_n:
                continue
            bits = dom[n] & ((1 << (rem_g + 1)) - 1)
            for g in bit_values(bits):
                rn, rg = rem_n - n, rem_g - g
                if suffix_has(suffix[idx + 1], rn, rg):
                    path[key] = (n, g)
                    dfs(idx + 1, rn, rg, path)
                    path.pop(key, None)
                    if len(examples) >= limit:
                        return

    for tn, tg in sorted_total_targets(final_domain, limit_states=1000):
        dfs(0, tn, tg, {})
        if len(examples) >= limit:
            break
    return examples


def print_rules(rules: List[Rule]):
    if not rules:
        print("  （空）")
        return
    for i, r in enumerate(rules, 1):
        print(f"  {i}. {r.pretty()}    [原文: {r.raw}]")


def wrap_candidate_text(text: str, width: int = 76) -> List[str]:
    """把长候选串分成多行，避免塞进表格一格里。"""
    s = str(text)
    if get_str_width(s) <= width:
        return [s]

    # 优先按“或”切候选组合，其次按逗号切集合/等差提示。
    if " 或 " in s:
        parts = s.split(" 或 ")
        sep = " 或 "
    elif "," in s:
        parts = s.split(",")
        sep = ","
    else:
        return [s]

    lines: List[str] = []
    cur = ""
    for part in parts:
        part = part.strip()
        candidate = part if not cur else cur + sep + part
        if get_str_width(candidate) <= width:
            cur = candidate
        else:
            if cur:
                lines.append(cur)
            cur = part
    if cur:
        lines.append(cur)
    return lines


def print_summary(rows: List[Tuple[str, str, str]]):
    print("\n[关键范围摘要：? 表示暂无有效约束；小集合/倍数会保留]")
    print("=" * 72)
    for name, ng_text, k in rows:
        print(f"\n【{name}】  可行(n,g)数：{k}")
        lines = wrap_candidate_text(ng_text, width=68)
        if not lines:
            print("  可能量/格：无")
        else:
            print(f"  可能量/格：{lines[0]}")
            for line in lines[1:]:
                print(f"              {line}")
    print("\n" + "=" * 72)

def fmt_ng(path: Dict[str, Tuple[int, int]], key: str) -> str:
    if key not in path:
        return "?"
    n, g = path[key]
    return f"{n}/{g}"


def print_examples(examples: List[Dict[str, Tuple[int, int]]], display_maps: Dict[str, Dict[int, Set[int]]], limit: int):
    if not examples:
        print("\n[代表可能世界] 无")
        return

    examples = sorted(
        examples,
        key=lambda path: (
            path.get("r", (10**9, 10**9))[0],
            path.get("gw", (10**9, 10**9))[0],
            path.get("o", (10**9, 10**9))[0],
            path.get("p", (10**9, 10**9))[0],
            path.get("b", (10**9, 10**9))[0],
        ),
    )

    seen = set()
    signatures: List[Tuple[str, str, str, str, str, str]] = []
    for path in examples:
        row_texts = []
        for key in ["o", "p", "b", "gw", "r"]:
            n, g = path.get(key, (0, 0))
            row_texts.append(fmt_ng_with_unknown(n, g, display_maps.get(key, {})))
        total_n = sum(path.get(k, (0, 0))[0] for k in ["o", "p", "b", "g", "w", "r"])
        signature = tuple(row_texts + [str(total_n)])
        if signature not in seen:
            seen.add(signature)
            signatures.append(signature)
        if len(signatures) >= limit:
            break

    if not signatures:
        print("\n[代表可能世界] 无可展示路线。")
        return

    # 如果所有代表路线都只是重复上方的大块摘要，就不要再塞进一张宽表。
    if len(signatures) == 1 and any(get_str_width(x) > 22 for x in signatures[0]):
        print("\n[代表可能世界]")
        print("  当前未知项较多，代表路线只会重复上方摘要，已省略宽表。")
        print("  补充某个品质的数量/格数后，这里会重新显示具体路线。")
        return

    print("\n[代表可能世界：已合并重复未知项]")
    print("=" * 72)
    labels = ["橙", "紫", "蓝", "绿白", "红", "总数量"]
    for i, sig in enumerate(signatures, 1):
        print(f"\n# {i}")
        for label, value in zip(labels, sig):
            lines = wrap_candidate_text(value, width=62)
            print(f"  {label:<4}: {lines[0]}")
            for line in lines[1:]:
                print(f"        {line}")
    print("\n" + "=" * 72)


def print_red_conclusion(red_ns: Set[int], red_gs: Set[int], red_ngs: Set[Tuple[int, int]]):
    print("\n[红货结论]")
    if not red_ngs:
        print("  当前规则下没有可行的红货组合。")
        return

    by_n = ngs_by_n(red_ngs)
    print(f"  红货可能量/格：{format_ng_compact(red_ngs)}")

    if len(by_n) == 1:
        n = next(iter(by_n))
        gs = by_n[n]
        if n == 0:
            print("  ✅ 当前规则下可以确定：没有红货。")
        elif len(gs) == 1:
            print(f"  ✅ 红货已锁定：{n}/{next(iter(gs))}")
        else:
            print(f"  ✅ 红货数量已锁定：{n} 件；格数未锁定，记作 {n}/?。")
        return

    if 0 in by_n:
        print("  ⚠️ 数量还没锁死：当前规则仍允许红货为 0。")
    else:
        print(f"  ✅ 当前规则可确定至少有 {min(by_n)} 件红货。")

    print("  提示：如果你已经从价格/画面确认某个品质数量，请补充如“紫数量=6”，红货会立刻收窄。")

def solve_and_print(rules: List[Rule], max_n_user: int, max_g_user: int, show_limit: int):
    t0 = time.perf_counter()
    max_n, max_g = infer_effective_max(rules, max_n_user, max_g_user)
    single, final_domain, groups = build_all_domains(rules, max_n, max_g)
    dt = time.perf_counter() - t0

    print(f"\n[run] 实际搜索上限: {max_n}件 / {max_g}格；耗时 {dt:.4f}s")
    total_states = count_states(final_domain)
    if total_states == 0:
        print("\n[警告] 当前规则没有任何可行解。请检查：")
        print("  1) 是否把均格/均价写错；")
        print("  2) 总数量/总格数是否过小；")
        print("  3) 绿白规则是否和单独绿/白规则冲突。")
        return

    print(f"[可行总状态] {total_states} 个不同的 总数量/总格数 状态。")

    unconstrained = [ZH[k] for k in ["o", "p", "b", "gw"] if not rules_mention_group(rules, k)]
    if unconstrained:
        print(f"[提醒] 这些品质/合计没有直接输入信息：{', '.join(unconstrained)}。")
        print("       程序不会把它们当成 0；样例中的 0 只是一种可能世界。")

    rows = summarize_groups(groups, final_domain, max_n, max_g)
    print_summary(rows)

    red_ns, red_gs, red_ngs = possible_values_for_group_key(groups, final_domain, "r", max_n, max_g)
    print_red_conclusion(red_ns, red_gs, red_ngs)

    display_maps = build_display_maps(groups, final_domain, max_n, max_g)
    raw_example_limit = min(max(show_limit * 80, show_limit), 5000)
    examples = generate_examples(groups, final_domain, single, max_n, max_g, raw_example_limit)
    print_examples(examples, display_maps, show_limit)


def print_help():
    print("""
[输入规则格式]
  颜色 指标 符号 数值

[颜色]
  总 / 红 / 橙 / 紫 / 蓝 / 绿 / 白 / 绿白

[指标]
  数量 / 格数 / 均格 / 均价

[符号]
  =  <=  >=  <  >

[例子]
  总数量<=109
  总格数=72, 绿白数量=19
  橙均格=3.2
  紫 均格 = 3.33
  蓝 均价 = 1342.5
  橙 格数 = 20
  白 数量 >= 2

[命令]
  run 或 r              执行推演
  del 2                 删除第 2 条规则
  clear                 清空规则
  max 109 72            设置搜索上限为 109 件 / 72 格
  show 20               每次 run 展示 20 条样例路线
  rules                 查看当前规则
  help                  查看帮助
  exit                  退出
""")


def main():
    rules: List[Rule] = []
    max_n = MAX_N_DEFAULT
    max_g = MAX_G_DEFAULT
    show_limit = MAX_SHOW_DEFAULT

    print("=== 竞拍之王：艾哈迈德 快速约束枚举器 ===")
    print("输入 help 查看格式；输入 run 执行。建议已知总格数时先输入：总格数=72 或 max 109 72。")

    while True:
        print("\n" + "-" * 58)
        print(f"[上限] {max_n}件 / {max_g}格；[展示] {show_limit}条样例；[规则数] {len(rules)}")
        cmd = input(">>> ").strip()
        if not cmd:
            continue
        low = normalize_cmd(cmd).strip().lower()

        if low in ("exit", "quit", "q"):
            break
        if low in ("help", "h", "?"):
            print_help()
            continue
        if low in ("rules", "rule", "ls"):
            print_rules(rules)
            continue
        if low in ("run", "r"):
            solve_and_print(rules, max_n, max_g, show_limit)
            continue
        if low == "clear":
            rules.clear()
            print(">> 已清空规则。")
            continue
        if low.startswith("del "):
            try:
                idx = int(low.split()[1]) - 1
                if 0 <= idx < len(rules):
                    old = rules.pop(idx)
                    print(f">> 已删除：{old.pretty()}")
                else:
                    print(">> 序号不存在。")
            except Exception:
                print(">> 格式错误：例如 del 2")
            continue
        if low.startswith("max "):
            try:
                _, n_str, g_str = low.split()
                max_n, max_g = int(n_str), int(g_str)
                print(f">> 已设置搜索上限：{max_n}件 / {max_g}格。")
            except Exception:
                print(">> 格式错误：例如 max 109 72")
            continue
        if low.startswith("show "):
            try:
                show_limit = max(1, int(low.split()[1]))
                print(f">> 每次 run 将展示 {show_limit} 条样例路线。")
            except Exception:
                print(">> 格式错误：例如 show 20")
            continue

        new_rules = parse_rules(cmd)
        if new_rules:
            rules.extend(new_rules)
            print(f">> 成功加入 {len(new_rules)} 条规则：")
            for r in new_rules:
                print(f"   - {r.pretty()}")
        else:
            print(">> 没识别到规则。输入 help 看例子。")


if __name__ == "__main__":
    main()
