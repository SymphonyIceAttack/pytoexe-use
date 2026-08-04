#!/usr/bin/env python3
"""BAY 图自动化标记工具。

桌面模式：python 自动画贝图.py
命令行：python 自动画贝图.py 输入.pdf --rule "CMAU:#52C41A:region:port"
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import threading
import traceback
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Iterable

if TYPE_CHECKING:
    from pymupdf import Page as PdfPage
    from pymupdf import Point as PdfPoint
    from pymupdf import Rect as PdfRect

fitz = None


def ensure_fitz() -> None:
    """延迟加载 PyMuPDF，让密码窗口和主界面更快出现。"""
    global fitz
    if fitz is not None:
        return
    try:
        import fitz as fitz_module  # PyMuPDF
    except ImportError as error:
        raise RuntimeError("缺少 PyMuPDF。请运行：python -m pip install pymupdf") from error
    fitz = fitz_module


APP_NAME = "BAY图自动化"
DISCLAIMER_TEXT = "本工具学习使用 切勿用于工作，错误自己承担责任。"
EXPIRED_MESSAGE = "小朋友过期啦 别乱动"

# ==================== 打开密码在此处修改 ====================
OPEN_PASSWORD = "QW147258369."

# ==================== 结束有效期在此处修改 ====================
# 当前设置表示软件可使用到 2026-09-15 当天，次日开始过期。
EXPIRY_DATE = date(2026, 9, 15)

APP_TITLE = APP_NAME
PRESET_COLORS = [
    "#D9F7BE", "#FFF1A8", "#BFE7FF", "#FFD0D6", "#E4D5FF", "#FFD8A8",
    "#52C41A", "#D9A300", "#1677FF", "#D9363E", "#7C3AED", "#D96B00",
]
# 色弱辅助不只依赖颜色：前 8 条港口规则使用 8 种线型，第 9 条重新循环。
REGION_LINE_STYLES = (
    "solid",
    "long-dash",
    "short-dash",
    "dot",
    "dash-dot",
    "wave",
    "zigzag",
    "dash-double-dot",
)
PDF_LINE_DASHES = {
    "solid": None,
    "long-dash": "[8 3] 0",
    "short-dash": "[4 2] 0",
    "dot": "[0.8 2.6] 0",
    "dash-dot": "[7 2 1 2] 0",
    "dash-double-dot": "[7 2 1 2 1 2] 0",
}
TK_LINE_DASHES = {
    "solid": None,
    "long-dash": (10, 4),
    "short-dash": (5, 3),
    "dot": (2, 4),
    "dash-dot": (9, 3, 2, 3),
    "dash-double-dot": (9, 3, 2, 3, 2, 3),
}
MODE_LABELS = {
    "region": "分区描边",
    "cell-fill": "单格底色",
    "cell-outline": "单格描边",
    "text": "文字底色",
}
MATCH_LABELS = {"port": "港口代码", "contains": "包含文字"}
LEGEND_LABELS = {
    "top": "顶部空白处横向排列",
    "top-right": "右上角集中排列",
    "auto": "自动寻找空白位置",
}
SPECIAL_TYPE_GROUPS = (
    ("罐式箱", ("TK", "TH")),
    ("冷冻箱", ("RF", "RH")),
    ("开顶/框架/超限箱", ("OT", "PF", "PH", "FR", "FL", "FW", "FH", "PL")),
)
SPECIAL_TYPE_CODES = tuple(code for _, codes in SPECIAL_TYPE_GROUPS for code in codes)
ISO_PREFIX_TO_TYPE = {
    "220": "20GP", "22G": "20GP", "20D": "20GP",
    "250": "20HC", "25G": "20HC",
    "227": "20TK", "22T": "20TK", "257": "20TK", "25T": "20TK",
    "225": "20OT", "22U": "20OT", "255": "20OT", "25U": "20OT",
    "226": "20FR", "22P": "20FR",
    "223": "20RF", "22R": "20RF",
    "253": "20RH", "25R": "20RH",
    "2DG": "20OH",
    "420": "40GP", "42G": "40GP", "431": "40GP", "430": "40GP", "40D": "40GP",
    "450": "40HC", "45G": "40HC", "451": "40HC",
    "423": "40RF", "42R": "40RF",
    "453": "40RH", "45R": "40RH", "443": "40RH",
    "435": "40OT", "42U": "40OT", "455": "40OT", "45U": "40OT",
    "437": "40TK", "42T": "40TK",
    "436": "40FR", "42P": "40FR", "456": "40FR",
    "45P": "40FH",
    "46PW": "40FM", "4PPW": "40FW",
    "L20": "45GP", "L2G": "45GP",
    "L5G": "45HC", "951": "45HC",
    "LEG": "45OH", "5EGB": "45OH",
    "MOG": "48GP", "M0P": "48FR", "M7PW": "48FR",
    "PPG": "待审核",
}
ISO_TYPE_GROUPS = (
    ("20 尺", ("20GP", "20HC", "20TK", "20OT", "20FR", "20PH", "20PL", "20RF", "20RH", "20OH")),
    ("40 尺", ("40GP", "40HC", "40RF", "40RH", "40OT", "40TK", "40FR", "40PH", "40PL", "40FH", "40FM", "40FW")),
    ("45/48 尺", ("45GP", "45HC", "45OH", "48GP", "48FR", "待审核")),
)
ISO_TYPES = tuple(box_type for _, box_types in ISO_TYPE_GROUPS for box_type in box_types)
ATTRIBUTE_TO_ISO_TYPES = {
    "TK": ("20TK", "40TK"),
    "TH": ("20TK", "40TK"),
    "RF": ("20RF", "40RF"),
    "RH": ("20RH", "40RH"),
    "OT": ("20OT", "40OT"),
    "PF": ("20FR", "40FR", "40FM", "48FR"),
    "PH": ("20PH", "40PH"),
    "FR": ("20FR", "40FR", "40FM", "48FR"),
    "FL": ("20FR", "40FR", "40FM", "48FR"),
    "FW": ("40FW",),
    "FH": ("40FH",),
    "PL": ("20PL", "40PL"),
}
SPECIAL_LABEL_GROUPS = (
    ("罐式箱", {"TK", "TH"}, {"20TK", "40TK"}),
    ("冷冻箱", {"RF", "RH"}, {"20RF", "40RF", "20RH", "40RH"}),
    ("开顶箱", {"OT"}, {"20OT", "40OT"}),
    (
        "框架/超限箱",
        {"PF", "PH", "FR", "FL", "FW", "FH", "PL"},
        {"20FR", "20PH", "20PL", "40FR", "40PH", "40PL", "40FH", "40FM", "40FW", "48FR"},
    ),
)
SMART_SPECIAL_CATEGORIES = (
    ("tank", "油罐TK柜", "#7C3AED", ("TK", "TH"), ("20TK", "40TK")),
    ("reefer", "冷冻箱", "#1677FF", ("RF", "RH"), ("20RF", "40RF", "20RH", "40RH")),
    ("open-top", "OT柜", "#38BDF8", ("OT",), ("20OT", "40OT")),
    (
        "frame",
        "框架/超限箱",
        "#F97316",
        ("PF", "PH", "FR", "FL", "FW", "FH", "PL"),
        ("20FR", "20PH", "20PL", "40FR", "40PH", "40PL", "40FH", "40FM", "40FW", "48FR"),
    ),
)


def days_until_expiry(today: date | None = None) -> int:
    return (EXPIRY_DATE - (today or date.today())).days


def is_app_expired(today: date | None = None) -> bool:
    return days_until_expiry(today) < 0


def expiry_status_text(today: date | None = None) -> str:
    remaining = max(0, days_until_expiry(today))
    return f"有效期倒计时：{remaining} 天（截止 {EXPIRY_DATE:%Y-%m-%d}）"


def suggested_special_label(type_codes: Iterable[str], iso_types: Iterable[str]) -> str:
    selected_codes = {value.upper() for value in type_codes}
    selected_iso_types = {value.upper() for value in iso_types}
    labels = [
        label
        for label, codes, box_types in SPECIAL_LABEL_GROUPS
        if selected_codes.intersection(codes) or selected_iso_types.intersection(box_types)
    ]
    return "、".join(labels) if labels else "特殊柜"


def virtual_screen_bounds() -> tuple[int, int, int, int]:
    if sys.platform != "win32":
        raise RuntimeError("屏幕取色目前仅支持 Windows。")
    import ctypes

    user32 = ctypes.windll.user32
    return tuple(user32.GetSystemMetrics(index) for index in (76, 77, 78, 79))


def screen_cursor_position() -> tuple[int, int]:
    if sys.platform != "win32":
        raise RuntimeError("屏幕取色目前仅支持 Windows。")
    import ctypes

    class Point(ctypes.Structure):
        _fields_ = (("x", ctypes.c_long), ("y", ctypes.c_long))

    point = Point()
    if not ctypes.windll.user32.GetCursorPos(ctypes.byref(point)):
        raise OSError("无法读取鼠标位置。")
    return point.x, point.y


def screen_pixel_hex(x: int, y: int) -> str:
    if sys.platform != "win32":
        raise RuntimeError("屏幕取色目前仅支持 Windows。")
    import ctypes

    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32
    desktop_dc = user32.GetDC(0)
    if not desktop_dc:
        raise OSError("无法读取屏幕颜色。")
    try:
        color_ref = gdi32.GetPixel(desktop_dc, x, y)
    finally:
        user32.ReleaseDC(0, desktop_dc)
    if color_ref == -1:
        raise OSError("该位置无法取色。")
    red = color_ref & 0xFF
    green = (color_ref >> 8) & 0xFF
    blue = (color_ref >> 16) & 0xFF
    return f"#{red:02X}{green:02X}{blue:02X}"


_PORT_OCR_ENGINE = None


def recognize_port_color_table(image) -> list[CapturedPortRule]:
    """从框选截图中读取五位港口代码，并取文字所在色块的主色。"""
    try:
        import numpy as np
        from rapidocr_onnxruntime import RapidOCR
    except ImportError as error:
        raise RuntimeError(
            "缺少港口表识别组件。请运行：python -m pip install rapidocr-onnxruntime onnxruntime pillow"
        ) from error
    from collections import Counter

    global _PORT_OCR_ENGINE
    if _PORT_OCR_ENGINE is None:
        _PORT_OCR_ENGINE = RapidOCR()
    rgb_image = image.convert("RGB")
    result, _elapsed = _PORT_OCR_ENGINE(np.asarray(rgb_image))
    candidates: dict[str, tuple[float, float, CapturedPortRule]] = {}
    correction = str.maketrans({"0": "O", "1": "I"})
    for box, raw_text, confidence in result or []:
        token = re.sub(r"[^A-Z0-9]", "", str(raw_text).upper()).translate(correction)
        if not re.fullmatch(r"[A-Z]{5}", token) or float(confidence) < 0.65:
            continue
        xs = [float(point[0]) for point in box]
        ys = [float(point[1]) for point in box]
        left = max(0, int(min(xs)) - 5)
        top = max(0, int(min(ys)) - 3)
        right = min(rgb_image.width, int(max(xs)) + 12)
        bottom = min(rgb_image.height, int(max(ys)) + 3)
        pixels = [
            pixel
            for pixel in rgb_image.crop((left, top, right, bottom)).getdata()
            if max(pixel) >= 45 and sum(pixel) >= 120
        ]
        if pixels:
            red, green, blue = Counter(pixels).most_common(1)[0][0]
            if min(red, green, blue) > 242 and max(red, green, blue) - min(red, green, blue) < 8:
                continue
            color = f"#{red:02X}{green:02X}{blue:02X}"
        else:
            color = PRESET_COLORS[len(candidates) % len(PRESET_COLORS)]
        if token in {"TOTAL", "PORTS", "REMARK", "EMPTY"}:
            continue
        captured = CapturedPortRule(token, color.upper(), float(confidence))
        position = (min(ys), min(xs), captured)
        known = candidates.get(token)
        if known is None or captured.confidence > known[2].confidence:
            candidates[token] = position
    return [entry[2] for entry in sorted(candidates.values(), key=lambda value: (value[0], value[1]))]


@dataclass
class Rule:
    keyword: str
    color: str = "#52C41A"
    mode: str = "region"
    match_type: str = "port"
    rule_id: str = ""
    line_style: str = "solid"

    def normalized_keyword(self) -> str:
        value = self.keyword.strip()
        return value.rsplit("/", 1)[-1].strip() if self.match_type == "port" else value


@dataclass
class CapturedPortRule:
    code: str
    color: str
    confidence: float = 1.0


@dataclass
class SpecialRule:
    label: str
    container_numbers: list[str]
    color: str = "#D9363E"
    rule_id: str = ""
    type_codes: list[str] = field(default_factory=list)
    iso_types: list[str] = field(default_factory=list)
    secondary_color: str | None = None


@dataclass
class DetectedSpecialCategory:
    key: str
    default_label: str
    default_color: str
    type_codes: list[str]
    iso_types: list[str]
    count: int = 0
    detected_type_codes: list[str] = field(default_factory=list)
    detected_iso_types: list[str] = field(default_factory=list)


@dataclass
class BoxTypeInventory:
    known_counts: dict[str, int] = field(default_factory=dict)
    unknown_counts: dict[str, int] = field(default_factory=dict)
    container_cells: int = 0
    unreadable_cells: int = 0
    duplicate_cells: int = 0


@dataclass
class SpecialConflict:
    page_number: int
    cell: tuple[float, float, float, float]
    rule_ids: tuple[str, ...]
    rule_labels: tuple[str, ...]
    container_number: str = ""


@dataclass
class PageMark:
    page_number: int
    rule_id: str
    keyword: str
    color: str
    mode: str
    rects: list[tuple[float, float, float, float]] = field(default_factory=list)
    segments: list[tuple[float, float, float, float]] = field(default_factory=list)
    count: int = 1
    fallback: bool = False
    secondary_color: str | None = None
    line_style: str = "solid"


@dataclass
class Legend:
    keyword: str
    color: str
    rect: tuple[float, float, float, float]
    kind: str = "badge"
    secondary_color: str | None = None
    line_style: str = "solid"


@dataclass
class AnalysisResult:
    marks: dict[int, list[PageMark]]
    legends: dict[int, list[Legend]]
    counts: dict[str, int]
    total: int
    fallback_count: int
    vector_count: int
    region_count: int
    special_conflicts: list[SpecialConflict] = field(default_factory=list)
    extra_special_rules: list[SpecialRule] = field(default_factory=list)


def normalize_hex(value: str) -> str:
    value = value.strip().upper()
    if not value.startswith("#"):
        value = "#" + value
    if not re.fullmatch(r"#[0-9A-F]{6}", value):
        raise ValueError(f"无效颜色：{value}")
    return value


def rgb01(value: str) -> tuple[float, float, float]:
    value = normalize_hex(value)
    return tuple(int(value[index:index + 2], 16) / 255 for index in (1, 3, 5))


def validate_rules(rules: list[Rule], case_sensitive: bool, require: bool = True) -> None:
    if require and not rules:
        raise ValueError("请至少输入一条目标文字。")
    if len(rules) > 12:
        raise ValueError("最多可以添加 12 条标记规则。")
    seen: set[tuple[str, str]] = set()
    for index, rule in enumerate(rules, 1):
        rule.keyword = rule.keyword.strip()
        rule.color = normalize_hex(rule.color)
        rule.rule_id = rule.rule_id or f"rule-{index}"
        if not rule.keyword:
            raise ValueError(f"第 {index} 条规则没有填写目标文字。")
        if rule.mode not in MODE_LABELS or rule.match_type not in MATCH_LABELS:
            raise ValueError(f"第 {index} 条规则设置无效。")
        key_text = rule.normalized_keyword()
        key = (rule.match_type, key_text if case_sensitive else key_text.lower())
        if key in seen:
            raise ValueError(f"目标文字“{rule.keyword}”重复，请删除重复规则。")
        seen.add(key)


def parse_container_numbers(text: str) -> list[str]:
    normalized = text.upper().replace("－", "-")
    found = re.findall(r"(?<![A-Z0-9])(?:[A-Z]{4}[\s-]*\d{7}|\d{7})(?![A-Z0-9])", normalized)
    numbers: list[str] = []
    for value in found:
        value = re.sub(r"[^A-Z0-9]", "", value)
        if value not in numbers:
            numbers.append(value)
    return numbers


def validate_special_rules(rules: list[SpecialRule]) -> None:
    if len(rules) > 12:
        raise ValueError("最多可以添加 12 条特殊柜规则。")
    seen_ids: set[str] = set()
    for index, rule in enumerate(rules, 1):
        rule.label = rule.label.strip()
        rule.color = normalize_hex(rule.color)
        if rule.secondary_color:
            rule.secondary_color = normalize_hex(rule.secondary_color)
        rule.rule_id = rule.rule_id or f"special-{index}"
        rule.container_numbers = list(dict.fromkeys(re.sub(r"[^A-Z0-9]", "", value.upper()) for value in rule.container_numbers))
        rule.container_numbers = [value for value in rule.container_numbers if re.fullmatch(r"(?:[A-Z]{4}\d{7}|\d{7})", value)]
        rule.type_codes = list(dict.fromkeys(value.upper() for value in rule.type_codes if value.upper() in SPECIAL_TYPE_CODES))
        rule.iso_types = list(dict.fromkeys(value.upper() for value in rule.iso_types if value.upper() in ISO_TYPES))
        if not rule.label:
            raise ValueError(f"第 {index} 条特殊柜规则没有填写自定义文字。")
        if not rule.container_numbers and not rule.type_codes and not rule.iso_types:
            raise ValueError(f"特殊柜规则“{rule.label}”没有柜号或箱型代码。")
        if rule.rule_id in seen_ids:
            raise ValueError("特殊柜规则编号重复。")
        seen_ids.add(rule.rule_id)


def rect_tuple(rect: PdfRect) -> tuple[float, float, float, float]:
    return (float(rect.x0), float(rect.y0), float(rect.x1), float(rect.y1))


def rect_center(rect: PdfRect) -> PdfPoint:
    return fitz.Point((rect.x0 + rect.x1) / 2, (rect.y0 + rect.y1) / 2)


def find_text_matches(
    page: PdfPage,
    rule: Rule,
    case_sensitive: bool,
    padding: float,
    words: list[tuple],
    text_page,
) -> list[PdfRect]:
    keyword = rule.normalized_keyword()
    search_keywords = [keyword]
    if rule.match_type == "port" and re.fullmatch(r"[A-Za-z]{5}", keyword):
        short_keyword = keyword[-3:]
        comparable_short = short_keyword if case_sensitive else short_keyword.upper()
        has_independent_short_code = any(
            (str(word[4]).strip() if case_sensitive else str(word[4]).strip().upper()) == comparable_short
            for word in words
        )
        if has_independent_short_code:
            search_keywords.append(short_keyword)
    flags = fitz.TEXT_DEHYPHENATE | fitz.TEXT_PRESERVE_WHITESPACE
    accepted: list[PdfRect] = []
    for search_keyword in search_keywords:
        candidates = page.search_for(search_keyword, flags=flags, textpage=text_page)
        for candidate in candidates:
            center_x = (candidate.x0 + candidate.x1) / 2
            center_y = (candidate.y0 + candidate.y1) / 2
            overlapping_words = [
                word for word in words
                if word[0] < candidate.x1 + 0.5
                and word[2] > candidate.x0 - 0.5
                and word[1] < candidate.y1 + 0.5
                and word[3] > candidate.y0 - 0.5
            ]
            extracted = " ".join(str(word[4]) for word in overlapping_words).strip()
            if case_sensitive and extracted and search_keyword not in extracted:
                continue
            if rule.match_type == "port":
                containing = next((
                    word for word in overlapping_words
                    if word[0] - 0.5 <= center_x <= word[2] + 0.5
                    and word[1] - 0.5 <= center_y <= word[3] + 0.5
                ), None)
                token = str(containing[4]) if containing else extracted
                pattern = re.compile(
                    rf"(?<![A-Z0-9]){re.escape(search_keyword)}(?![A-Z0-9])",
                    0 if case_sensitive else re.I,
                )
                if not pattern.search(token or ""):
                    continue
            rect = fitz.Rect(candidate)
            rect.x0 -= padding
            rect.y0 -= padding
            rect.x1 += padding
            rect.y1 += padding
            rect &= page.rect
            if rect.width > 0 and rect.height > 0 and not any(same_cell(rect, known, tolerance=0.5) for known in accepted):
                accepted.append(rect)
    return accepted


def extract_vector_cells(page: PdfPage) -> list[PdfRect]:
    cells: dict[tuple[int, int, int, int], PdfRect] = {}
    page_area = page.rect.get_area()
    for drawing in page.get_drawings():
        rect = fitz.Rect(drawing["rect"])
        if rect.width < 12 or rect.height < 12 or rect.get_area() > page_area * 0.15:
            continue
        if rect.width > page.rect.width * 0.3 or rect.height > page.rect.height * 0.28:
            continue
        looks_closed = any(item[0] == "re" for item in drawing["items"]) or len(drawing["items"]) >= 3
        if not looks_closed:
            continue
        key = tuple(round(value * 2) for value in (rect.x0, rect.y0, rect.x1, rect.y1))
        cells[key] = rect
    return list(cells.values())


def cell_for_text(text_rect: PdfRect, cells: list[PdfRect]) -> PdfRect | None:
    center = rect_center(text_rect)
    candidates = []
    for cell in cells:
        if not cell.contains(center):
            continue
        if cell.width < text_rect.width * 1.18 or cell.height < text_rect.height * 1.75:
            continue
        candidates.append(cell)
    return min(candidates, key=lambda rect: rect.get_area()) if candidates else None


def same_cell(first: PdfRect, second: PdfRect, tolerance: float = 1.0) -> bool:
    return all(abs(a - b) <= tolerance for a, b in zip(first, second))


def dedupe_overlapping_cells(cells: list[PdfRect], overlap_threshold: float = 0.5) -> list[PdfRect]:
    """保留真实的小箱格，剔除读取页眉/网格后形成的重叠伪大格。"""
    accepted: list[tuple[int, PdfRect]] = []
    for original_index, cell in sorted(enumerate(cells), key=lambda item: item[1].get_area()):
        cell_area = max(0.01, cell.get_area())
        duplicate = False
        for _, known in accepted:
            intersection = cell & known
            if intersection.is_empty:
                continue
            smaller_area = min(cell_area, max(0.01, known.get_area()))
            if intersection.get_area() / smaller_area >= overlap_threshold:
                duplicate = True
                break
        if not duplicate:
            accepted.append((original_index, cell))
    return [cell for _, cell in sorted(accepted)]


def cells_adjacent(first: PdfRect, second: PdfRect, tolerance: float = 1.5) -> bool:
    vertical_overlap = min(first.y1, second.y1) - max(first.y0, second.y0)
    horizontal_overlap = min(first.x1, second.x1) - max(first.x0, second.x0)
    shared_vertical = min(abs(first.x1 - second.x0), abs(second.x1 - first.x0)) <= tolerance
    shared_horizontal = min(abs(first.y1 - second.y0), abs(second.y1 - first.y0)) <= tolerance
    return (shared_vertical and vertical_overlap > min(first.height, second.height) * 0.35) or (
        shared_horizontal and horizontal_overlap > min(first.width, second.width) * 0.35
    )


def connected_groups(cells: list[PdfRect]) -> list[list[PdfRect]]:
    groups: list[list[PdfRect]] = []
    remaining = set(range(len(cells)))
    while remaining:
        seed = remaining.pop()
        queue = [seed]
        group = [cells[seed]]
        while queue:
            current = queue.pop()
            neighbors = [index for index in remaining if cells_adjacent(cells[current], cells[index])]
            for index in neighbors:
                remaining.remove(index)
                queue.append(index)
                group.append(cells[index])
        groups.append(group)
    return groups


def merge_segments(segments: Iterable[tuple[float, float, float, float]], tolerance: float = 1.5) -> list[tuple[float, float, float, float]]:
    horizontal: dict[int, list[tuple[float, float, float]]] = {}
    vertical: dict[int, list[tuple[float, float, float]]] = {}
    for x1, y1, x2, y2 in segments:
        if abs(y1 - y2) <= tolerance:
            horizontal.setdefault(round((y1 + y2) / 2), []).append((min(x1, x2), max(x1, x2), (y1 + y2) / 2))
        else:
            vertical.setdefault(round((x1 + x2) / 2), []).append((min(y1, y2), max(y1, y2), (x1 + x2) / 2))
    output: list[tuple[float, float, float, float]] = []
    for ranges in horizontal.values():
        ranges.sort()
        start, end, axis = ranges[0]
        for next_start, next_end, _ in ranges[1:]:
            if next_start <= end + tolerance:
                end = max(end, next_end)
            else:
                output.append((start, axis, end, axis))
                start, end = next_start, next_end
        output.append((start, axis, end, axis))
    for ranges in vertical.values():
        ranges.sort()
        start, end, axis = ranges[0]
        for next_start, next_end, _ in ranges[1:]:
            if next_start <= end + tolerance:
                end = max(end, next_end)
            else:
                output.append((axis, start, axis, end))
                start, end = next_start, next_end
        output.append((axis, start, axis, end))
    return output


def perimeter_segments(cells: list[PdfRect]) -> list[tuple[float, float, float, float]]:
    exposed: list[tuple[float, float, float, float]] = []
    for index, cell in enumerate(cells):
        sides = [
            (cell.x0, cell.y0, cell.x1, cell.y0),
            (cell.x1, cell.y0, cell.x1, cell.y1),
            (cell.x0, cell.y1, cell.x1, cell.y1),
            (cell.x0, cell.y0, cell.x0, cell.y1),
        ]
        for side in sides:
            middle = fitz.Point((side[0] + side[2]) / 2, (side[1] + side[3]) / 2)
            internal = False
            for other_index, other in enumerate(cells):
                if index == other_index:
                    continue
                near_vertical = abs(side[0] - side[2]) < 0.1 and (
                    abs(side[0] - other.x0) <= 1.5 or abs(side[0] - other.x1) <= 1.5
                ) and other.y0 - 1 <= middle.y <= other.y1 + 1
                near_horizontal = abs(side[1] - side[3]) < 0.1 and (
                    abs(side[1] - other.y0) <= 1.5 or abs(side[1] - other.y1) <= 1.5
                ) and other.x0 - 1 <= middle.x <= other.x1 + 1
                if near_vertical or near_horizontal:
                    internal = True
                    break
            if not internal:
                exposed.append(side)
    return merge_segments(exposed)


def region_line_primitives(
    marks: list[PageMark],
    outline_width: float,
) -> list[tuple[PageMark, tuple[float, float, float, float]]]:
    """拆分共线边界；不同港口共边时平行排线，避免后画颜色覆盖前画颜色。"""
    entries: list[tuple[PageMark, str, float, float, float]] = []
    rule_order: dict[str, int] = {}
    assist_enabled = any(mark.mode == "region" and mark.line_style != "solid" for mark in marks)
    for mark in marks:
        if mark.mode != "region":
            continue
        rule_order.setdefault(mark.rule_id, len(rule_order))
        for x1, y1, x2, y2 in mark.segments:
            if abs(y1 - y2) <= 1.0:
                entries.append((mark, "h", (y1 + y2) / 2, min(x1, x2), max(x1, x2)))
            elif abs(x1 - x2) <= 1.0:
                entries.append((mark, "v", (x1 + x2) / 2, min(y1, y2), max(y1, y2)))

    groups: dict[tuple[str, int], list[tuple[PageMark, str, float, float, float]]] = {}
    for entry in entries:
        groups.setdefault((entry[1], round(entry[2] * 2)), []).append(entry)

    output: list[tuple[PageMark, tuple[float, float, float, float]]] = []
    spacing = max(3.2, outline_width * 1.8 + 1.0)
    def inward_sign(mark: PageMark, orientation: str, axis: float, middle: float) -> int:
        for values in mark.rects:
            cell = fitz.Rect(values)
            if orientation == "h" and cell.x0 - 1.0 <= middle <= cell.x1 + 1.0:
                if abs(axis - cell.y0) <= 2.0:
                    return 1
                if abs(axis - cell.y1) <= 2.0:
                    return -1
            if orientation == "v" and cell.y0 - 1.0 <= middle <= cell.y1 + 1.0:
                if abs(axis - cell.x0) <= 2.0:
                    return 1
                if abs(axis - cell.x1) <= 2.0:
                    return -1
        return 0

    for group in groups.values():
        breaks = sorted({round(value, 3) for entry in group for value in (entry[3], entry[4])})
        for start, end in zip(breaks, breaks[1:]):
            if end - start < 0.1:
                continue
            middle = (start + end) / 2
            active_by_rule: dict[str, tuple[PageMark, str, float, float, float]] = {}
            for entry in group:
                if entry[3] - 0.05 <= middle <= entry[4] + 0.05:
                    active_by_rule.setdefault(entry[0].rule_id, entry)
            active = sorted(active_by_rule.values(), key=lambda item: rule_order[item[0].rule_id])
            if not active:
                continue
            split_shared_edge = assist_enabled and len(active) > 1
            shared_axis = sum(entry[2] for entry in active) / len(active)
            for lane, entry in enumerate(active):
                sign = inward_sign(entry[0], entry[1], entry[2], middle) if assist_enabled else 0
                if sign:
                    axis = entry[2]
                elif split_shared_edge:
                    axis = shared_axis + (lane - (len(active) - 1) / 2) * spacing
                else:
                    axis = entry[2]
                coords = (start, axis, end, axis) if entry[1] == "h" else (axis, start, axis, end)
                output.append((entry[0], coords))
    return output


def region_inward_vector(
    mark: PageMark,
    coords: tuple[float, float, float, float],
) -> tuple[float, float] | None:
    x1, y1, x2, y2 = coords
    if abs(y1 - y2) <= 1.0:
        axis = (y1 + y2) / 2
        middle = (x1 + x2) / 2
        for values in mark.rects:
            cell = fitz.Rect(values)
            if cell.x0 - 1.0 <= middle <= cell.x1 + 1.0:
                if abs(axis - cell.y0) <= 2.0:
                    return (0.0, 1.0)
                if abs(axis - cell.y1) <= 2.0:
                    return (0.0, -1.0)
    elif abs(x1 - x2) <= 1.0:
        axis = (x1 + x2) / 2
        middle = (y1 + y2) / 2
        for values in mark.rects:
            cell = fitz.Rect(values)
            if cell.y0 - 1.0 <= middle <= cell.y1 + 1.0:
                if abs(axis - cell.x0) <= 2.0:
                    return (1.0, 0.0)
                if abs(axis - cell.x1) <= 2.0:
                    return (-1.0, 0.0)
    return None


def styled_line_paths(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    style: str,
    width: float,
    inward: tuple[float, float] | None = None,
) -> list[tuple[list[tuple[float, float]], str | None, float]]:
    """返回一条线型的折线路径、PDF虚线参数及实际线宽。"""
    dx = x2 - x1
    dy = y2 - y1
    length = math.hypot(dx, dy)
    if length < 0.05:
        return []
    ux, uy = dx / length, dy / length
    nx, ny = -uy, ux
    if inward and math.hypot(*inward) > 0.01:
        inward_length = math.hypot(*inward)
        offset_x, offset_y = inward[0] / inward_length, inward[1] / inward_length
        one_sided = True
    else:
        offset_x, offset_y = nx, ny
        one_sided = False

    def point(distance: float, offset: float = 0.0) -> tuple[float, float]:
        return (x1 + ux * distance + offset_x * offset, y1 + uy * distance + offset_y * offset)

    amplitude = max(0.9, min(1.5, width * 0.55)) if one_sided else max(1.15, min(2.2, width * 0.72))
    if style == "wave":
        cycles = max(1, round(length / 9.0))
        samples = max(8, cycles * 10)
        if one_sided:
            points = [
                point(
                    length * index / samples,
                    amplitude * (1 - math.cos(2 * math.pi * cycles * index / samples)) / 2,
                )
                for index in range(samples + 1)
            ]
        else:
            points = [
                point(length * index / samples, amplitude * math.sin(2 * math.pi * cycles * index / samples))
                for index in range(samples + 1)
            ]
        return [(points, None, max(0.8, width * 0.78))]

    if style == "zigzag":
        steps = max(2, round(length / 4.2))
        points = [point(0)]
        for index in range(1, steps):
            offset = amplitude if index % 2 else (0.0 if one_sided else -amplitude)
            points.append(point(length * index / steps, offset))
        points.append(point(length))
        return [(points, None, max(0.8, width * 0.72))]

    baseline_offset = max(0.75, width * 0.45) if one_sided else 0.0
    return [([point(0, baseline_offset), point(length, baseline_offset)], PDF_LINE_DASHES.get(style), width)]


def draw_pdf_styled_line(
    page: PdfPage,
    coords: tuple[float, float, float, float],
    style: str,
    color,
    width: float,
    opacity: float = 1.0,
    inward: tuple[float, float] | None = None,
) -> None:
    for points, dashes, line_width in styled_line_paths(*coords, style, width, inward):
        page.draw_polyline(
            [fitz.Point(x, y) for x, y in points],
            color=color,
            dashes=dashes,
            width=line_width,
            lineCap=1,
            lineJoin=0,
            stroke_opacity=opacity,
            overlay=True,
        )


def draw_canvas_styled_line(
    canvas,
    coords: tuple[float, float, float, float],
    style: str,
    color: str,
    width: float,
    scale: float,
    offset_x: float,
    offset_y: float,
    inward: tuple[float, float] | None = None,
) -> None:
    for points, _pdf_dashes, line_width in styled_line_paths(*coords, style, width, inward):
        canvas_points: list[tuple[float, float]] = []
        for x, y in points:
            canvas_points.append((offset_x + x * scale, offset_y + y * scale))
        options = {
            "fill": color,
            "width": max(1, line_width * scale),
            "capstyle": "round",
            "joinstyle": "round",
        }
        dash = TK_LINE_DASHES.get(style)
        if dash and len(canvas_points) == 2:
            start, end = canvas_points
            dx, dy = end[0] - start[0], end[1] - start[1]
            length = math.hypot(dx, dy)
            if length < 0.1:
                continue
            ux, uy = dx / length, dy / length
            pattern = [max(1.0, value * scale) for value in dash]
            distance = 0.0
            pattern_index = 0
            while distance < length:
                next_distance = min(length, distance + pattern[pattern_index % len(pattern)])
                if pattern_index % 2 == 0:
                    canvas.create_line(
                        start[0] + ux * distance,
                        start[1] + uy * distance,
                        start[0] + ux * next_distance,
                        start[1] + uy * next_distance,
                        **options,
                    )
                distance = next_distance
                pattern_index += 1
            continue
        flat_points = [value for point_values in canvas_points for value in point_values]
        canvas.create_line(*flat_points, **options)


def _occupancy_prefix(page: PdfPage, scale: float = 0.30) -> tuple[list[int], int, int, float]:
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), colorspace=fitz.csGRAY, alpha=False)
    raw = pix.samples
    width = pix.width
    height = pix.height
    stride = width + 1
    prefix = [0] * (stride * (height + 1))
    for y in range(height):
        row_total = 0
        source_offset = y * width
        target_offset = (y + 1) * stride
        previous_offset = y * stride
        for x in range(width):
            row_total += raw[source_offset + x] < 242
            prefix[target_offset + x + 1] = prefix[previous_offset + x + 1] + row_total
    return prefix, width, height, scale


def _area_is_free(prefix: list[int], width: int, height: int, x: int, y: int, w: int, h: int) -> bool:
    if x < 0 or y < 0 or x + w > width or y + h > height:
        return False
    stride = width + 1
    right = x + w
    bottom = y + h
    occupied_count = (
        prefix[bottom * stride + right]
        - prefix[y * stride + right]
        - prefix[bottom * stride + x]
        + prefix[y * stride + x]
    )
    return occupied_count == 0


def _overlaps_reserved(x: int, y: int, w: int, h: int, reserved: list[tuple[int, int, int, int]]) -> bool:
    return any(x < rx + rw and x + w > rx and y < ry + rh and y + h > ry for rx, ry, rw, rh in reserved)


def find_legends(
    page: PdfPage,
    rules: list[Rule],
    placement: str,
    special_rules: list[SpecialRule] | None = None,
) -> list[Legend]:
    items: list[tuple[str, str, str, str | None, str]] = []
    for rule in rules:
        label = re.sub(r"[^\x20-\x7E]", "", rule.normalized_keyword())[:24] or rule.normalized_keyword()[:12]
        kind = "region" if rule.mode == "region" else "badge"
        items.append((label, rule.color, kind, None, rule.line_style))
    for rule in special_rules or []:
        items.append((rule.label[:24], rule.color, "special", rule.secondary_color, "solid"))
    if not items:
        return []
    prefix, width, height, scale = _occupancy_prefix(page)
    legends: list[Legend] = []
    reserved: list[tuple[int, int, int, int]] = []
    for label, color, kind, secondary_color, line_style in sorted(items, key=lambda item: len(item[0]), reverse=True):
        visual_units = sum(2 if ord(character) > 127 else 1 for character in label)
        if kind == "special":
            badge_w = max(58.0, min(180.0, 24.0 + visual_units * 7.0))
        else:
            badge_w = max(44.0, min(100.0, 18.0 + visual_units * 7.2))
        badge_h = 24.0
        w = max(1, math.ceil((badge_w + 6) * scale))
        h = max(1, math.ceil((badge_h + 6) * scale))
        margin = max(2, math.ceil(10 * scale))
        max_y = height // 2 if placement in ("top", "top-right") else height - h - margin
        selected: tuple[int, int] | None = None
        for y in range(margin, max_y + 1):
            row_candidates: list[tuple[float, int]] = []
            for x in range(margin, width - w - margin + 1):
                if not _area_is_free(prefix, width, height, x, y, w, h) or _overlaps_reserved(x, y, w, h, reserved):
                    continue
                center_distance = abs(x + w / 2 - width / 2)
                right_distance = width - x - w
                if placement == "top-right":
                    row_score = right_distance * 1000 + center_distance
                else:
                    row_score = center_distance * 1000 + right_distance
                row_candidates.append((row_score, x))
            if row_candidates:
                _, x = min(row_candidates)
                selected = (x, y)
                break
        if selected:
            x, y = selected
        else:
            x = max(margin, width - w - margin)
            y = margin + len(legends) * (h + 1)
        reserved.append((max(0, x - 1), max(0, y - 1), w + 2, h + 2))
        rect = fitz.Rect(x / scale + 3, y / scale + 3, (x + w) / scale - 3, (y + h) / scale - 3)
        legends.append(Legend(label, color, rect_tuple(rect), kind, secondary_color, line_style))
    return legends


def normalized_cell_text(words: list[tuple], cell: PdfRect) -> str:
    parts: list[str] = []
    for word in words:
        center_x = (word[0] + word[2]) / 2
        center_y = (word[1] + word[3]) / 2
        if cell.x0 - 0.8 <= center_x <= cell.x1 + 0.8 and cell.y0 - 0.8 <= center_y <= cell.y1 + 0.8:
            parts.append(re.sub(r"[^A-Z0-9]", "", str(word[4]).upper()))
    return "".join(parts)


def iso_type_for_token(value: str) -> str | None:
    token = re.sub(r"\s+", "", value.strip().upper())
    if not re.fullmatch(r"[A-Z0-9]{4,5}", token):
        return None
    if token in ISO_TYPES:
        return token
    for prefix in sorted(ISO_PREFIX_TO_TYPE, key=len, reverse=True):
        if token.startswith(prefix):
            return ISO_PREFIX_TO_TYPE[prefix]
    return None


def token_attribute_codes(value: str) -> set[str]:
    token = re.sub(r"\s+", "", value.strip().upper())
    return {token} if token in SPECIAL_TYPE_CODES else set()


def cell_box_codes(words: list[tuple], cell: PdfRect) -> tuple[set[str], set[str]]:
    cell_words = []
    for word in words:
        center_x = (word[0] + word[2]) / 2
        center_y = (word[1] + word[3]) / 2
        if cell.x0 - 0.8 <= center_x <= cell.x1 + 0.8 and cell.y0 - 0.8 <= center_y <= cell.y1 + 0.8:
            cell_words.append(word)

    candidates = [str(word[4]) for word in cell_words]
    ordered_words = sorted(cell_words, key=lambda word: (word[5], word[6], word[7]))
    for first, second in zip(ordered_words, ordered_words[1:]):
        same_line = first[5] == second[5] and first[6] == second[6] and second[7] == first[7] + 1
        text_height = max(first[3] - first[1], second[3] - second[1])
        gap = second[0] - first[2]
        if same_line and -0.5 <= gap <= max(3.0, text_height * 0.6):
            candidates.append(f"{first[4]} {second[4]}")

    attribute_codes: set[str] = set()
    iso_types: set[str] = set()
    for candidate in candidates:
        attribute_codes.update(token_attribute_codes(candidate))
        iso_type = iso_type_for_token(candidate)
        if iso_type:
            iso_types.add(iso_type)
    return attribute_codes, iso_types


def numbered_vector_cells(words: list[tuple], cells: list[PdfRect]) -> list[PdfRect]:
    """返回含完整柜号或独立 7 位柜号数字的真实柜格。"""
    numbered_cells: list[PdfRect] = []
    for word in words:
        raw_token = str(word[4]).strip().upper()
        compact_token = re.sub(r"[^A-Z0-9]", "", raw_token)
        is_container_number = bool(
            re.fullmatch(r"\d{7}", raw_token)
            or re.fullmatch(r"[A-Z]{3}[UJZ]\d{7}", compact_token)
        )
        if not is_container_number:
            continue
        cell = cell_for_text(fitz.Rect(word[:4]), cells)
        if cell is not None and not any(same_cell(cell, known) for known in numbered_cells):
            numbered_cells.append(cell)
    return numbered_cells


def box_type_for_record_words(record_words: list[tuple]) -> tuple[str, bool] | None:
    """Read a box type from one PDF text record."""
    if not record_words:
        return None

    lines: dict[tuple[int, int], list[tuple]] = {}
    for word in record_words:
        lines.setdefault((word[5], word[6]), []).append(word)
    ordered_lines = sorted(lines.values(), key=lambda line: min(word[1] for word in line))
    number_line_indexes = []
    for index, line in enumerate(ordered_lines):
        if any(
            re.fullmatch(r"\d{7}", str(word[4]).strip())
            or re.fullmatch(r"[A-Z]{3}[UJZ]\d{7}", re.sub(r"[^A-Z0-9]", "", str(word[4]).upper()))
            for word in line
        ):
            number_line_indexes.append(index)
    candidate_indexes = [index + 1 for index in number_line_indexes if index + 1 < len(ordered_lines)]
    candidate_indexes.append(0)
    candidate_lines = [ordered_lines[index] for index in dict.fromkeys(candidate_indexes)]

    for line in candidate_lines:
        ordered = sorted(line, key=lambda word: (word[0], word[7]))
        candidates: list[tuple[float, str]] = [(word[0], str(word[4])) for word in ordered]
        for first, second in zip(ordered, ordered[1:]):
            text_height = max(first[3] - first[1], second[3] - second[1])
            gap = second[0] - first[2]
            consecutive = second[7] == first[7] + 1
            if consecutive and -0.5 <= gap <= max(3.0, text_height * 0.6):
                candidates.append((first[0], f"{first[4]} {second[4]}"))

        normalized_candidates: list[tuple[float, str, str | None]] = []
        for x, candidate in candidates:
            compact = re.sub(r"[^A-Z0-9]", "", candidate.upper())
            if compact:
                normalized_candidates.append((x, compact, iso_type_for_token(compact)))
        normalized_candidates.sort(key=lambda item: item[0])
        for _x, compact, known_type in normalized_candidates:
            if known_type:
                return known_type, True
            if (
                re.fullmatch(r"[A-Z0-9]{4}", compact)
                and re.search(r"[A-Z]", compact)
                and re.search(r"\d", compact)
            ):
                return compact, False
    return None


def box_type_for_cell(words: list[tuple], cell: PdfRect) -> tuple[str, bool] | None:
    """兼容两种贝图：首行简化箱型，或柜号下一行的 4 位 ISO 代码。"""
    cell_words = []
    for word in words:
        center_x = (word[0] + word[2]) / 2
        center_y = (word[1] + word[3]) / 2
        if cell.x0 - 0.8 <= center_x <= cell.x1 + 0.8 and cell.y0 - 0.8 <= center_y <= cell.y1 + 0.8:
            cell_words.append(word)
    if not cell_words:
        return None

    lines: dict[tuple[int, int], list[tuple]] = {}
    for word in cell_words:
        lines.setdefault((word[5], word[6]), []).append(word)
    ordered_lines = sorted(lines.values(), key=lambda line: min(word[1] for word in line))
    number_line_indexes = []
    for index, line in enumerate(ordered_lines):
        if any(
            re.fullmatch(r"\d{7}", str(word[4]).strip())
            or re.fullmatch(r"[A-Z]{3}[UJZ]\d{7}", re.sub(r"[^A-Z0-9]", "", str(word[4]).upper()))
            for word in line
        ):
            number_line_indexes.append(index)
    candidate_indexes = [index + 1 for index in number_line_indexes if index + 1 < len(ordered_lines)]
    candidate_indexes.append(0)
    candidate_lines = [ordered_lines[index] for index in dict.fromkeys(candidate_indexes)]

    for line in candidate_lines:
        ordered = sorted(line, key=lambda word: (word[0], word[7]))
        candidates: list[tuple[float, str]] = [(word[0], str(word[4])) for word in ordered]
        for first, second in zip(ordered, ordered[1:]):
            text_height = max(first[3] - first[1], second[3] - second[1])
            gap = second[0] - first[2]
            consecutive = second[7] == first[7] + 1
            if consecutive and -0.5 <= gap <= max(3.0, text_height * 0.6):
                candidates.append((first[0], f"{first[4]} {second[4]}"))

        normalized_candidates: list[tuple[float, str, str | None]] = []
        for x, candidate in candidates:
            compact = re.sub(r"[^A-Z0-9]", "", candidate.upper())
            if not compact:
                continue
            normalized_candidates.append((x, compact, iso_type_for_token(compact)))
        normalized_candidates.sort(key=lambda item: item[0])
        for _x, compact, known_type in normalized_candidates:
            if known_type:
                return known_type, True
            is_strict_unknown_code = bool(
                re.fullmatch(r"[A-Z0-9]{4}", compact)
                and re.search(r"[A-Z]", compact)
                and re.search(r"\d", compact)
            )
            if is_strict_unknown_code:
                return compact, False
    return None


def page_container_records(
    words: list[tuple],
    cells: list[PdfRect],
) -> list[tuple[str, tuple[str, bool] | None, PdfRect | None, int]]:
    """Find every container by seven consecutive digits, then read its local box type."""
    blocks: dict[int, list[tuple]] = {}
    for word in words:
        blocks.setdefault(int(word[5]), []).append(word)

    records: list[tuple[str, tuple[str, bool] | None, PdfRect | None, int]] = []
    for word in words:
        compact = re.sub(r"[^A-Z0-9]", "", str(word[4]).upper())
        number_match = re.fullmatch(r"(?:[A-Z]{3}[UJZ])?(\d{7})", compact)
        if not number_match:
            continue

        block_number = int(word[5])
        block_words = blocks.get(block_number, [])
        block_tokens = [re.sub(r"[^A-Z0-9]", "", str(value[4]).upper()) for value in block_words]
        owner_prefix = next((value for value in block_tokens if re.fullmatch(r"[A-Z]{3}[UJZ]", value)), None)
        cell = cell_for_text(fitz.Rect(word[:4]), cells)

        # Reject dates and header numbers unless a real cell or owner code confirms the record.
        if cell is None and owner_prefix is None and len(compact) == 7:
            continue

        digits = number_match.group(1)
        if len(compact) > 7:
            container_number = compact
        elif owner_prefix:
            container_number = owner_prefix + digits
        elif cell is not None:
            container_number = container_number_for_cell(words, cell) or digits
        else:
            container_number = digits

        cell_box_type = box_type_for_cell(words, cell) if cell is not None else None
        block_box_type = box_type_for_record_words(block_words) if owner_prefix or len(compact) > 7 else None
        box_type = cell_box_type
        if box_type is None or (block_box_type is not None and block_box_type[1] and not box_type[1]):
            box_type = block_box_type
        records.append((container_number, box_type, cell, block_number))
    return records


def scan_box_type_inventory(
    input_path: str | Path,
    progress: Callable[[int, int], None] | None = None,
) -> BoxTypeInventory:
    """统计本船真实柜格箱型；兼容首行箱型和柜号下一行 ISO 代码。"""
    ensure_fitz()
    document = fitz.open(str(input_path))
    if document.needs_pass:
        document.close()
        raise ValueError("暂不支持带密码的 PDF。")
    inventory = BoxTypeInventory()
    unique_containers: dict[str, tuple[str, bool] | None] = {}
    try:
        total_pages = document.page_count
        for page_index, page in enumerate(document):
            text_page = page.get_textpage(flags=fitz.TEXT_DEHYPHENATE | fitz.TEXT_PRESERVE_WHITESPACE)
            words = page.get_text("words", textpage=text_page, sort=False)
            cells = dedupe_overlapping_cells(extract_vector_cells(page))
            for container_number, box_type, _cell, _block_number in page_container_records(words, cells):
                unique_key = container_number[-7:]
                if unique_key in unique_containers:
                    inventory.duplicate_cells += 1
                    previous = unique_containers[unique_key]
                    if previous is None or (box_type is not None and box_type[1] and not previous[1]):
                        unique_containers[unique_key] = box_type
                    continue
                unique_containers[unique_key] = box_type
            if progress:
                progress(page_index + 1, total_pages)
    finally:
        document.close()
    inventory.container_cells = len(unique_containers)
    for box_type in unique_containers.values():
        if box_type is None:
            inventory.unreadable_cells += 1
            continue
        code, known = box_type
        target = inventory.known_counts if known else inventory.unknown_counts
        target[code] = target.get(code, 0) + 1
    return inventory


def scan_present_special_categories(
    input_path: str | Path,
    progress: Callable[[int, int], None] | None = None,
) -> list[DetectedSpecialCategory]:
    """只统计含真实柜号的贝位单元格，排除页眉和箱型汇总表。"""
    ensure_fitz()
    document = fitz.open(str(input_path))
    if document.needs_pass:
        document.close()
        raise ValueError("暂不支持带密码的 PDF。")
    categories = {
        key: DetectedSpecialCategory(key, label, color, list(type_codes), list(iso_types))
        for key, label, color, type_codes, iso_types in SMART_SPECIAL_CATEGORIES
    }
    found_codes = {key: set() for key in categories}
    found_iso_types = {key: set() for key in categories}
    matched_container_numbers = {key: set() for key in categories}
    try:
        total_pages = document.page_count
        for page_index, page in enumerate(document):
            text_page = page.get_textpage(flags=fitz.TEXT_DEHYPHENATE | fitz.TEXT_PRESERVE_WHITESPACE)
            words = page.get_text("words", textpage=text_page, sort=False)
            cells = dedupe_overlapping_cells(extract_vector_cells(page))
            blocks: dict[int, list[tuple]] = {}
            for word in words:
                blocks.setdefault(int(word[5]), []).append(word)

            for container_number, box_type, cell, block_number in page_container_records(words, cells):
                unique_key = container_number[-7:]
                if cell is not None:
                    cell_type_codes, cell_iso_types = cell_box_codes(words, cell)
                else:
                    cell_type_codes, cell_iso_types = set(), set()
                if box_type is not None and box_type[1]:
                    cell_iso_types.add(box_type[0])
                for block_word in blocks.get(block_number, []):
                    token = str(block_word[4])
                    cell_type_codes.update(token_attribute_codes(token))
                    iso_type = iso_type_for_token(token)
                    if iso_type:
                        cell_iso_types.add(iso_type)
                for key, category in categories.items():
                    matching_codes = set(category.type_codes).intersection(cell_type_codes)
                    matching_iso_types = set(category.iso_types).intersection(cell_iso_types)
                    if not matching_codes and not matching_iso_types:
                        continue
                    matched_container_numbers[key].add(unique_key)
                    found_codes[key].update(matching_codes)
                    found_iso_types[key].update(matching_iso_types)
            if progress:
                progress(page_index + 1, total_pages)
    finally:
        document.close()

    detected: list[DetectedSpecialCategory] = []
    for key, _label, _color, _codes, _iso_types in SMART_SPECIAL_CATEGORIES:
        category = categories[key]
        category.count = len(matched_container_numbers[key])
        if not category.count:
            continue
        category.detected_type_codes = sorted(found_codes[key])
        category.detected_iso_types = sorted(found_iso_types[key])
        detected.append(category)
    return detected


def container_number_for_cell(words: list[tuple], cell: PdfRect) -> str:
    cell_words = []
    for word in words:
        center_x = (word[0] + word[2]) / 2
        center_y = (word[1] + word[3]) / 2
        if cell.x0 - 0.8 <= center_x <= cell.x1 + 0.8 and cell.y0 - 0.8 <= center_y <= cell.y1 + 0.8:
            token = re.sub(r"[^A-Z0-9]", "", str(word[4]).upper())
            cell_words.append((word, token))
            if re.fullmatch(r"[A-Z]{3}[UJZ]\d{7}", token):
                return token

    prefixes = [(word, token) for word, token in cell_words if re.fullmatch(r"[A-Z]{3}[UJZ]", token)]
    numbers = [(word, token) for word, token in cell_words if re.fullmatch(r"\d{7}", token)]
    pairs: list[tuple[float, str]] = []
    for prefix_word, prefix in prefixes:
        for number_word, number in numbers:
            same_line = prefix_word[5] == number_word[5] and prefix_word[6] == number_word[6]
            word_distance = abs(number_word[7] - prefix_word[7])
            score = word_distance + (0 if same_line else 100)
            pairs.append((score, prefix + number))
    if pairs:
        return min(pairs, key=lambda item: item[0])[1]
    return numbers[0][1] if numbers else ""


def combined_conflict_rule(rules: list[SpecialRule]) -> SpecialRule:
    labels = list(dict.fromkeys(rule.label for rule in rules))
    rule_ids = list(dict.fromkeys(rule.rule_id for rule in rules))
    secondary_color = rules[-1].color if rules[-1].color != rules[0].color else None
    return SpecialRule(
        "并存：" + " + ".join(labels),
        [],
        rules[0].color,
        "conflict-coexist-" + "-".join(rule_ids),
        secondary_color=secondary_color,
    )


def dot_rect_for_cell(
    cell: PdfRect,
    words: list[tuple],
    reserved_dots: list[tuple[float, float, float, float]] | None = None,
) -> PdfRect | None:
    occupied: list[tuple[float, float, float, float]] = []
    for word in words:
        center_x = (word[0] + word[2]) / 2
        center_y = (word[1] + word[3]) / 2
        if cell.x0 <= center_x <= cell.x1 and cell.y0 <= center_y <= cell.y1:
            occupied.append((word[0] - 1.0, word[1] - 1.0, word[2] + 1.0, word[3] + 1.0))
    for x0, y0, x1, y1 in reserved_dots or []:
        if x0 < cell.x1 and x1 > cell.x0 and y0 < cell.y1 and y1 > cell.y0:
            occupied.append((x0 - 1.0, y0 - 1.0, x1 + 1.0, y1 + 1.0))
    maximum_radius = min(4.2, max(2.2, min(cell.width, cell.height) * 0.12))
    radii = [maximum_radius, maximum_radius * 0.85, maximum_radius * 0.7, 1.8]
    for radius in radii:
        margin = max(1.5, radius * 0.45)
        min_x = cell.x0 + margin + radius
        max_x = cell.x1 - margin - radius
        min_y = cell.y0 + margin + radius
        max_y = cell.y1 - margin - radius
        if min_x > max_x or min_y > max_y:
            continue
        step = max(1.4, radius * 0.7)
        candidates: list[tuple[float, float, float]] = []
        y = min_y
        while y <= max_y + 0.01:
            x = min_x
            while x <= max_x + 0.01:
                left, top, right, bottom = x - radius, y - radius, x + radius, y + radius
                if any(left < ox1 and right > ox0 and top < oy1 and bottom > oy0 for ox0, oy0, ox1, oy1 in occupied):
                    x += step
                    continue
                if occupied:
                    clearance = min(math.hypot(
                        max(ox0 - x, 0.0, x - ox1),
                        max(oy0 - y, 0.0, y - oy1),
                    ) for ox0, oy0, ox1, oy1 in occupied)
                else:
                    clearance = min(cell.width, cell.height)
                right_preference = (x - cell.x0) / max(1.0, cell.width) * 0.25
                candidates.append((clearance + right_preference, x, y))
                x += step
            y += step
        if candidates:
            _, x, y = max(candidates)
            return fitz.Rect(x - radius, y - radius, x + radius, y + radius)
    return None


def find_special_cells(
    page: PdfPage,
    rule: SpecialRule,
    words: list[tuple],
    text_page,
    cells: list[PdfRect],
) -> list[PdfRect]:
    located: list[PdfRect] = []
    target_digits = {value[-7:] for value in rule.container_numbers}
    if target_digits:
        for cell in cells:
            content = normalized_cell_text(words, cell)
            if any(digits in content for digits in target_digits):
                located.append(cell)
    if rule.type_codes or rule.iso_types:
        selected_codes = set(rule.type_codes)
        selected_iso_types = set(rule.iso_types)
        selected_attribute_iso_types = {
            iso_type
            for code in selected_codes
            for iso_type in ATTRIBUTE_TO_ISO_TYPES.get(code, ())
        }
        for cell in cells:
            attribute_codes, cell_iso_types = cell_box_codes(words, cell)
            matches_attribute = bool(
                selected_codes.intersection(attribute_codes)
                or selected_attribute_iso_types.intersection(cell_iso_types)
            )
            matches_iso = bool(selected_iso_types.intersection(cell_iso_types))
            if not matches_attribute and not matches_iso:
                continue
            if not any(same_cell(cell, known) for known in located):
                located.append(cell)
    return dedupe_overlapping_cells(located)


def analyze_pdf(
    input_path: str | Path,
    rules: list[Rule],
    *,
    special_rules: list[SpecialRule] | None = None,
    case_sensitive: bool = True,
    padding: float = 1.0,
    show_legends: bool = True,
    legend_placement: str = "top",
    special_conflict_mode: str = "first",
    custom_conflict_rule: SpecialRule | None = None,
    progress: Callable[[int, int], None] | None = None,
) -> AnalysisResult:
    ensure_fitz()
    special_rules = special_rules or []
    if special_conflict_mode not in {"first", "last", "coexist", "custom"}:
        raise ValueError("未知的特殊柜冲突处理方式。")
    if special_conflict_mode == "custom" and custom_conflict_rule is None:
        raise ValueError("自定义冲突处理缺少规则名称或颜色。")
    validate_rules(rules, case_sensitive, require=not special_rules)
    validate_special_rules(special_rules)
    if custom_conflict_rule:
        custom_conflict_rule.label = custom_conflict_rule.label.strip() or "冲突集装箱规则"
        custom_conflict_rule.color = normalize_hex(custom_conflict_rule.color)
    document = fitz.open(str(input_path))
    if document.needs_pass:
        document.close()
        raise ValueError("暂不支持带密码的 PDF。")
    marks: dict[int, list[PageMark]] = {}
    legends: dict[int, list[Legend]] = {}
    counts = {rule.rule_id: 0 for rule in [*rules, *special_rules]}
    fallback_count = vector_count = region_count = total = 0
    special_conflicts: list[SpecialConflict] = []
    extra_special_rules: dict[str, SpecialRule] = {}
    try:
        for page_index, page in enumerate(document):
            page_number = page_index + 1
            text_flags = fitz.TEXT_DEHYPHENATE | fitz.TEXT_PRESERVE_WHITESPACE
            text_page = page.get_textpage(flags=text_flags)
            page_words = page.get_text("words", textpage=text_page, sort=False)
            cells: list[PdfRect] | None = None
            page_marks: list[PageMark] = []
            matched_rules: list[Rule] = []
            matched_special_rules: list[SpecialRule] = []
            for rule in rules:
                text_rects = find_text_matches(page, rule, case_sensitive, padding, page_words, text_page)
                if not text_rects:
                    continue
                matched_rules.append(rule)
                counts[rule.rule_id] += len(text_rects)
                total += len(text_rects)
                if rule.mode == "text":
                    page_marks.append(PageMark(page_number, rule.rule_id, rule.normalized_keyword(), rule.color, "text", [rect_tuple(rect) for rect in text_rects], count=len(text_rects)))
                    continue
                if cells is None:
                    cells = extract_vector_cells(page)
                located: list[PdfRect] = []
                missing: list[PdfRect] = []
                for text_rect in text_rects:
                    cell = cell_for_text(text_rect, cells)
                    if cell is None:
                        missing.append(text_rect)
                    elif not any(same_cell(cell, known) for known in located):
                        located.append(cell)
                        vector_count += 1
                if missing:
                    fallback_count += len(missing)
                    page_marks.append(PageMark(page_number, rule.rule_id, rule.normalized_keyword(), rule.color, "text", [rect_tuple(rect) for rect in missing], count=len(missing), fallback=True))
                if rule.mode == "region":
                    for group in connected_groups(located):
                        segments = perimeter_segments(group)
                        if segments:
                            region_count += 1
                            page_marks.append(PageMark(
                                page_number,
                                rule.rule_id,
                                rule.normalized_keyword(),
                                rule.color,
                                "region",
                                rects=[rect_tuple(cell) for cell in group],
                                segments=segments,
                                count=len(group),
                                line_style=rule.line_style,
                            ))
                elif located:
                    page_marks.append(PageMark(page_number, rule.rule_id, rule.normalized_keyword(), rule.color, rule.mode, [rect_tuple(rect) for rect in located], count=len(located)))
            if special_rules:
                if cells is None:
                    cells = extract_vector_cells(page)
                reserved_special_dots: list[tuple[float, float, float, float]] = []
                cell_matches: list[tuple[PdfRect, list[SpecialRule]]] = []
                for special_rule in special_rules:
                    located = find_special_cells(page, special_rule, page_words, text_page, cells)
                    for cell in located:
                        known = next((entry for entry in cell_matches if same_cell(cell, entry[0])), None)
                        if known is None:
                            cell_matches.append((cell, [special_rule]))
                        elif all(rule.rule_id != special_rule.rule_id for rule in known[1]):
                            known[1].append(special_rule)

                resolved_dots: dict[str, tuple[SpecialRule, list[PdfRect]]] = {}
                for cell, matching_rules in cell_matches:
                    chosen_rule = matching_rules[0]
                    if len(matching_rules) > 1:
                        special_conflicts.append(SpecialConflict(
                            page_number,
                            rect_tuple(cell),
                            tuple(rule.rule_id for rule in matching_rules),
                            tuple(rule.label for rule in matching_rules),
                            container_number_for_cell(page_words, cell),
                        ))
                        if special_conflict_mode == "last":
                            chosen_rule = matching_rules[-1]
                        elif special_conflict_mode == "coexist":
                            chosen_rule = combined_conflict_rule(matching_rules)
                            extra_special_rules.setdefault(chosen_rule.rule_id, chosen_rule)
                        elif special_conflict_mode == "custom":
                            chosen_rule = custom_conflict_rule
                            extra_special_rules.setdefault(chosen_rule.rule_id, chosen_rule)

                    dot = dot_rect_for_cell(cell, page_words, reserved_special_dots)
                    if dot is None:
                        continue
                    reserved_special_dots.append(rect_tuple(dot))
                    if chosen_rule.rule_id not in resolved_dots:
                        resolved_dots[chosen_rule.rule_id] = (chosen_rule, [])
                    resolved_dots[chosen_rule.rule_id][1].append(dot)

                for chosen_rule, dots in resolved_dots.values():
                    if all(rule.rule_id != chosen_rule.rule_id for rule in matched_special_rules):
                        matched_special_rules.append(chosen_rule)
                    counts.setdefault(chosen_rule.rule_id, 0)
                    counts[chosen_rule.rule_id] += len(dots)
                    total += len(dots)
                    vector_count += len(dots)
                    page_marks.append(PageMark(
                        page_number,
                        chosen_rule.rule_id,
                        chosen_rule.label,
                        chosen_rule.color,
                        "dot",
                        [rect_tuple(rect) for rect in dots],
                        count=len(dots),
                        secondary_color=chosen_rule.secondary_color,
                    ))
            if page_marks:
                marks[page_number] = page_marks
                if show_legends or matched_special_rules:
                    legends[page_number] = find_legends(
                        page,
                        matched_rules if show_legends else [],
                        legend_placement,
                        matched_special_rules,
                    )
            if progress:
                progress(page_number, document.page_count)
    finally:
        document.close()
    return AnalysisResult(
        marks,
        legends,
        counts,
        total,
        fallback_count,
        vector_count,
        region_count,
        special_conflicts,
        list(extra_special_rules.values()),
    )


def draw_result_on_page(page: PdfPage, marks: list[PageMark], legends: list[Legend], opacity: float, outline_width: float) -> None:
    for mark, (x1, y1, x2, y2) in region_line_primitives(marks, outline_width):
        coords = (x1, y1, x2, y2)
        draw_pdf_styled_line(
            page,
            coords,
            mark.line_style,
            rgb01(mark.color),
            outline_width,
            opacity,
            region_inward_vector(mark, coords),
        )
    for mark in marks:
        color = rgb01(mark.color)
        if mark.mode == "region":
            continue
        if mark.mode == "dot":
            for values in mark.rects:
                dot = fitz.Rect(values)
                outline_color = rgb01(mark.secondary_color) if mark.secondary_color else color
                page.draw_oval(dot, color=outline_color, fill=color, width=1.5 if mark.secondary_color else 0.6, stroke_opacity=0.98, fill_opacity=0.98, overlay=True)
            continue
        for values in mark.rects:
            rect = fitz.Rect(values)
            if mark.mode == "cell-outline":
                page.draw_rect(rect, color=color, width=outline_width, stroke_opacity=opacity, overlay=True)
            else:
                page.draw_rect(rect, color=None, fill=color, fill_opacity=opacity, overlay=True)
    for legend in legends:
        rect = fitz.Rect(legend.rect)
        color = rgb01(legend.color)
        if legend.kind == "special":
            radius = min(5.0, rect.height * 0.23)
            center = fitz.Point(rect.x0 + radius + 2.0, (rect.y0 + rect.y1) / 2)
            outline_color = rgb01(legend.secondary_color) if legend.secondary_color else color
            page.draw_circle(center, radius, color=outline_color, fill=color, width=1.8 if legend.secondary_color else 0.8, overlay=True)
            font_size = min(11.5, rect.height * 0.52)
            baseline = rect.y0 + (rect.height + font_size * 0.72) / 2
            start = fitz.Point(rect.x0 + radius * 2 + 8.0, baseline)
            page.insert_text(start, legend.keyword, fontsize=font_size, fontname="china-s", color=color, overlay=True)
            page.insert_text(fitz.Point(start.x + 0.28, start.y), legend.keyword, fontsize=font_size, fontname="china-s", color=color, overlay=True)
            continue
        luminance = 0.2126 * color[0] + 0.7152 * color[1] + 0.0722 * color[2]
        text_color = (0.05, 0.14, 0.08) if luminance > 0.58 else (1, 1, 1)
        page.draw_rect(rect, color=text_color, fill=color, width=0.7, fill_opacity=0.96, stroke_opacity=0.65, overlay=True)
        label = re.sub(r"[^\x20-\x7E]", "?", legend.keyword)[:24]
        font_size = min(12.0, max(6.0, rect.width / max(2.0, len(label) * 0.62)))
        page.insert_textbox(rect, label, fontsize=font_size, fontname="helv", color=text_color, align=fitz.TEXT_ALIGN_CENTER, overlay=True)
        if legend.kind == "region":
            sample_y = rect.y1 - 2.3
            draw_pdf_styled_line(
                page,
                (rect.x0 + 3.0, sample_y, rect.x1 - 3.0, sample_y),
                legend.line_style,
                text_color,
                1.4,
            )


def export_pdf(
    input_path: str | Path,
    output_path: str | Path,
    result: AnalysisResult,
    *,
    opacity: float = 0.45,
    outline_width: float = 4.0,
) -> Path:
    ensure_fitz()
    document = fitz.open(str(input_path))
    try:
        for page_number, marks in result.marks.items():
            page = document[page_number - 1]
            draw_result_on_page(page, marks, result.legends.get(page_number, []), opacity, outline_width)
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        document.save(str(output), garbage=3, deflate=True)
        return output
    finally:
        document.close()


def result_summary(result: AnalysisResult, rules: list[Rule], special_rules: list[SpecialRule] | None = None) -> str:
    items = [f"{rule.normalized_keyword()} {result.counts.get(rule.rule_id, 0)}（{MODE_LABELS[rule.mode]}）" for rule in rules]
    items.extend(f"{rule.label} {result.counts.get(rule.rule_id, 0)}（特殊柜圆点）" for rule in special_rules or [])
    details = " · ".join(items)
    pages = "、".join(str(page) for page in sorted(result.marks)) or "无"
    suffix = f"；{result.fallback_count} 处退回文字底色" if result.fallback_count else ""
    return f"共 {result.total} 处 · {details}\n命中页码：{pages}；原始单元格定位 {result.vector_count} 处；分区 {result.region_count} 个{suffix}"


def parse_rule(value: str, index: int) -> Rule:
    parts = value.split(":")
    if len(parts) < 2:
        raise argparse.ArgumentTypeError("规则格式应为 文字:#颜色:方式:匹配")
    keyword = parts[0]
    color = parts[1] or PRESET_COLORS[index % len(PRESET_COLORS)]
    mode = parts[2] if len(parts) > 2 and parts[2] else "region"
    match_type = parts[3] if len(parts) > 3 and parts[3] else "port"
    line_style = REGION_LINE_STYLES[index % len(REGION_LINE_STYLES)] if mode == "region" else "solid"
    return Rule(keyword, color, mode, match_type, f"rule-{index + 1}", line_style)


def run_cli(args: argparse.Namespace) -> int:
    rules = [parse_rule(value, index) for index, value in enumerate(args.rule)]
    result = analyze_pdf(
        args.input,
        rules,
        case_sensitive=not args.ignore_case,
        padding=args.padding,
        show_legends=not args.no_legend,
        legend_placement=args.legend_placement,
        progress=lambda current, total: print(f"\r正在分析 {current}/{total}", end="", flush=True),
    )
    print()
    if result.total == 0:
        print("没有找到目标文字，未生成 PDF。", file=sys.stderr)
        return 2
    output = args.output or str(Path(args.input).with_name(Path(args.input).stem + "_港口分区标记.pdf"))
    export_pdf(args.input, output, result, opacity=args.opacity / 100, outline_width=args.outline_width)
    print(result_summary(result, rules))
    print(f"已生成：{Path(output).resolve()}")
    if args.report:
        report = {"summary": result_summary(result, rules), "counts": result.counts, "marks": {str(k): [asdict(mark) for mark in v] for k, v in result.marks.items()}}
        Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


class RuleRow:
    def __init__(self, app: "BayPlanApp", parent, index: int, rule: Rule | None = None):
        import tkinter as tk
        from tkinter import ttk

        self.app = app
        self.frame = ttk.Frame(parent)
        self.frame.columnconfigure(1, weight=1)
        self.index_label = ttk.Label(self.frame, text=str(index), width=2, anchor="center")
        self.index_label.grid(row=0, column=0, padx=(0, 4))
        self.keyword = tk.StringVar(value=rule.keyword if rule else "")
        self.match_type = tk.StringVar(value=MATCH_LABELS[rule.match_type if rule else "port"])
        self.mode = tk.StringVar(value=MODE_LABELS[rule.mode if rule else "region"])
        self.color = rule.color if rule else PRESET_COLORS[(index - 1) % len(PRESET_COLORS)]
        entry = ttk.Entry(self.frame, textvariable=self.keyword, width=12)
        entry.grid(row=0, column=1, sticky="ew", padx=2)
        match = ttk.Combobox(self.frame, textvariable=self.match_type, values=list(MATCH_LABELS.values()), state="readonly", width=8)
        match.grid(row=0, column=2, padx=2)
        mode = ttk.Combobox(self.frame, textvariable=self.mode, values=list(MODE_LABELS.values()), state="readonly", width=11)
        mode.grid(row=0, column=3, padx=2)
        self.color_button = tk.Button(self.frame, bg=self.color, width=3, relief="solid", bd=1, command=self.choose_color)
        self.color_button.grid(row=0, column=4, padx=3)
        ttk.Button(self.frame, text="×", width=3, command=lambda: app.remove_rule(self)).grid(row=0, column=5)
        for widget in (self.frame, entry, match, mode, self.color_button):
            widget.bind("<Button-1>", lambda _event, current=self: app.set_active_rule(current), add="+")
        entry.bind("<FocusIn>", lambda _event, current=self: app.set_active_rule(current), add="+")
        for variable in (self.keyword, self.match_type, self.mode):
            variable.trace_add("write", lambda *_: app.invalidate())

    def choose_color(self) -> None:
        from tkinter import colorchooser

        value = colorchooser.askcolor(self.color, title="选择标记颜色")[1]
        if value:
            self.color = value.upper()
            self.color_button.configure(bg=self.color)
            self.app.invalidate()

    def set_color(self, color: str) -> None:
        self.color = color
        self.color_button.configure(bg=color)
        self.app.invalidate()

    def to_rule(self, index: int) -> Rule | None:
        keyword = self.keyword.get().strip()
        if not keyword:
            return None
        mode = next(key for key, label in MODE_LABELS.items() if label == self.mode.get())
        match_type = next(key for key, label in MATCH_LABELS.items() if label == self.match_type.get())
        colorblind_lines = getattr(self.app, "colorblind_lines", None)
        line_style = (
            REGION_LINE_STYLES[(index - 1) % len(REGION_LINE_STYLES)]
            if mode == "region" and (colorblind_lines is None or colorblind_lines.get())
            else "solid"
        )
        return Rule(keyword, self.color, mode, match_type, f"rule-{index}", line_style)


class BayPlanApp:
    def __init__(self, root):
        import tkinter as tk
        from tkinter import ttk

        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1360x820")
        self.root.minsize(1080, 680)
        self.file_path: Path | None = None
        self.document = None
        self.current_page = 1
        self.result: AnalysisResult | None = None
        self.photo = None
        self.render_scale = 1.0
        self.busy = False
        self.rule_rows: list[RuleRow] = []
        self.active_rule_row: RuleRow | None = None
        self.special_rules: list[SpecialRule] = []
        self.next_special_id = 1

        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")

        topbar = ttk.Frame(root, padding=(14, 9))
        topbar.pack(fill="x")
        brand = ttk.Frame(topbar)
        brand.pack(side="left", fill="x", expand=True)
        ttk.Label(brand, text=APP_NAME, font=("Microsoft YaHei UI", 15, "bold")).pack(anchor="w")
        ttk.Label(brand, text=DISCLAIMER_TEXT, foreground="#B42318").pack(anchor="w", pady=(2, 0))
        topbar_status = ttk.Frame(topbar)
        topbar_status.pack(side="right")
        self.validity_label = ttk.Label(topbar_status, font=("Microsoft YaHei UI", 9, "bold"))
        self.validity_label.pack(anchor="e")
        self.file_summary = ttk.Label(topbar_status, text="尚未选择 PDF")
        self.file_summary.pack(anchor="e", pady=(3, 0))
        self.update_expiry_countdown()

        main = ttk.Panedwindow(root, orient="horizontal")
        main.pack(fill="both", expand=True)
        sidebar_host = ttk.Frame(main, width=455)
        viewer = ttk.Frame(main, padding=(8, 4, 12, 12))
        main.add(sidebar_host, weight=0)
        main.add(viewer, weight=1)
        sidebar_canvas = tk.Canvas(sidebar_host, width=445, highlightthickness=0, bg="#F0F0F0")
        sidebar_scroll = ttk.Scrollbar(sidebar_host, orient="vertical", command=sidebar_canvas.yview)
        sidebar_canvas.configure(yscrollcommand=sidebar_scroll.set)
        sidebar_scroll.pack(side="right", fill="y")
        sidebar_canvas.pack(side="left", fill="both", expand=True)
        sidebar = ttk.Frame(sidebar_canvas, padding=12)
        sidebar_window = sidebar_canvas.create_window((0, 0), window=sidebar, anchor="nw")
        sidebar.bind("<Configure>", lambda _: sidebar_canvas.configure(scrollregion=sidebar_canvas.bbox("all")))
        sidebar_canvas.bind("<Configure>", lambda event: sidebar_canvas.itemconfigure(sidebar_window, width=event.width))
        sidebar_canvas.bind("<Enter>", lambda _: sidebar_canvas.bind_all("<MouseWheel>", lambda event: sidebar_canvas.yview_scroll(int(-event.delta / 120), "units")))
        sidebar_canvas.bind("<Leave>", lambda _: sidebar_canvas.unbind_all("<MouseWheel>"))
        self._build_sidebar(sidebar)
        self._build_viewer(viewer)
        self.add_rule()
        self.update_navigation()

    def update_expiry_countdown(self) -> None:
        self.validity_label.configure(text=expiry_status_text())
        self.root.after(60_000, self.update_expiry_countdown)

    def _build_sidebar(self, parent) -> None:
        import tkinter as tk
        from tkinter import ttk

        ttk.Label(parent, text="文件", font=("Microsoft YaHei UI", 10, "bold")).pack(anchor="w")
        ttk.Button(parent, text="选择 PDF...", command=self.choose_pdf).pack(fill="x", pady=(5, 12))

        heading = ttk.Frame(parent)
        heading.pack(fill="x")
        ttk.Label(heading, text="标记规则", font=("Microsoft YaHei UI", 10, "bold")).pack(side="left")
        ttk.Label(heading, text="最多 12 条").pack(side="right")
        head = ttk.Frame(parent)
        head.pack(fill="x", pady=(5, 2))
        for text, width in (("", 2), ("港口/文字", 12), ("匹配", 8), ("标记", 11), ("颜色", 4), ("", 3)):
            ttk.Label(head, text=text, width=width, anchor="center").pack(side="left", padx=2)
        self.rule_frame = ttk.Frame(parent)
        self.rule_frame.pack(fill="x")
        rule_actions = ttk.Frame(parent)
        rule_actions.pack(fill="x", pady=(6, 8))
        ttk.Button(rule_actions, text="＋ 添加规则", command=self.add_rule).pack(side="left", fill="x", expand=True, padx=(0, 3))
        ttk.Button(rule_actions, text="框选采集港口颜色表", command=self.capture_port_color_table).pack(side="left", fill="x", expand=True, padx=(3, 0))

        palette = ttk.Frame(parent)
        palette.pack(fill="x", pady=(0, 8))
        palette_header = ttk.Frame(palette)
        palette_header.pack(fill="x")
        ttk.Label(palette_header, text="预设颜色").pack(side="left")
        self.screen_picker_button = ttk.Button(palette_header, text="屏幕取色", command=self.pick_screen_color)
        self.screen_picker_button.pack(side="right")
        swatches = ttk.Frame(palette)
        swatches.pack(fill="x", pady=(4, 0))
        for color in PRESET_COLORS:
            tk.Button(swatches, bg=color, width=2, height=1, bd=1, relief="solid", command=lambda c=color: self.apply_palette(c)).pack(side="left", padx=1)

        self.case_sensitive = tk.BooleanVar(value=True)
        ttk.Checkbutton(parent, text="区分大小写", variable=self.case_sensitive, command=self.invalidate).pack(anchor="w", pady=(0, 10))

        ttk.Separator(parent).pack(fill="x", pady=3)
        special_heading = ttk.Frame(parent)
        special_heading.pack(fill="x", pady=(7, 4))
        ttk.Label(special_heading, text="特殊柜标记", font=("Microsoft YaHei UI", 10, "bold")).pack(side="left")
        ttk.Label(special_heading, text="圆点 + 图例").pack(side="right")
        self.special_rule_frame = ttk.Frame(parent)
        self.special_rule_frame.pack(fill="x")
        special_actions = ttk.Frame(parent)
        special_actions.pack(fill="x", pady=(3, 3))
        ttk.Button(special_actions, text="＋ 添加特殊柜规则", command=self.open_special_rule_dialog).pack(
            side="left", fill="x", expand=True, padx=(0, 3)
        )
        self.smart_special_button = ttk.Button(
            special_actions,
            text="智能提取本船特殊柜箱型",
            command=self.detect_special_categories,
        )
        self.smart_special_button.pack(side="left", fill="x", expand=True, padx=(3, 0))
        self.box_type_stats_button = ttk.Button(
            parent,
            text="统计本船存在箱型及数量",
            command=self.show_box_type_statistics,
        )
        self.box_type_stats_button.pack(fill="x", pady=(0, 9))

        ttk.Separator(parent).pack(fill="x", pady=3)
        ttk.Label(parent, text="显示", font=("Microsoft YaHei UI", 10, "bold")).pack(anchor="w", pady=(7, 4))
        self.opacity = tk.DoubleVar(value=45)
        self.outline_width = tk.DoubleVar(value=4.0)
        self.padding = tk.DoubleVar(value=1.0)
        self._scale_field(parent, "颜色不透明度", self.opacity, 15, 85, 1, "%")
        self._scale_field(parent, "描边粗细", self.outline_width, 1, 6, 0.5, " pt")
        self.colorblind_lines = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            parent,
            text="色弱辅助：8种线型循环 + 共享边界双线",
            variable=self.colorblind_lines,
            command=self.invalidate,
        ).pack(anchor="w", pady=(4, 2))
        self._scale_field(parent, "文字底纹边距", self.padding, 0, 4, 0.5, " pt", invalidate=True)
        self.show_legends = tk.BooleanVar(value=True)
        ttk.Checkbutton(parent, text="页面颜色标识框", variable=self.show_legends, command=self.invalidate).pack(anchor="w", pady=(5, 3))
        self.legend_placement = tk.StringVar(value=LEGEND_LABELS["top"])
        legend_combo = ttk.Combobox(parent, textvariable=self.legend_placement, state="readonly", values=list(LEGEND_LABELS.values()))
        legend_combo.pack(fill="x")
        legend_combo.bind("<<ComboboxSelected>>", lambda _: self.invalidate())

        actions = ttk.Frame(parent)
        actions.pack(fill="x", pady=(5, 5))
        self.preview_button = ttk.Button(actions, text="查找并预览全部规则", command=self.preview)
        self.preview_button.pack(side="left", fill="x", expand=True, padx=(0, 3))
        self.export_button = ttk.Button(actions, text="生成 PDF", command=self.export)
        self.export_button.pack(side="left", fill="x", expand=True, padx=(3, 0))
        self.status = tk.Text(parent, height=6, wrap="word", relief="flat", bg="#F4F6F5", padx=8, pady=7)
        self.status.pack(fill="both", expand=True, pady=(5, 0))
        self.set_status("请选择一个可搜索的文字型 PDF。")

    def _scale_field(self, parent, label, variable, start, end, resolution, suffix, invalidate=False) -> None:
        import tkinter as tk
        from tkinter import ttk

        row = ttk.Frame(parent)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=label, width=14).pack(side="left")
        value_label = ttk.Label(row, width=7, anchor="e")
        value_label.pack(side="right")
        scale = ttk.Scale(row, variable=variable, from_=start, to=end)
        scale.pack(side="left", fill="x", expand=True)

        def changed(*_):
            raw = round(variable.get() / resolution) * resolution
            variable.set(raw)
            text = f"{raw:g}{suffix}"
            value_label.configure(text=text)
            if invalidate:
                self.invalidate()
            else:
                self.render_page()

        variable.trace_add("write", changed)
        value_label.configure(text=f"{variable.get():g}{suffix}")

    def _build_viewer(self, parent) -> None:
        from tkinter import ttk

        toolbar = ttk.Frame(parent)
        toolbar.pack(fill="x", pady=(0, 5))
        self.prev_button = ttk.Button(toolbar, text="‹", width=4, command=lambda: self.change_page(-1))
        self.prev_button.pack(side="left")
        self.page_label = ttk.Label(toolbar, text="0 / 0", width=12, anchor="center")
        self.page_label.pack(side="left")
        self.next_button = ttk.Button(toolbar, text="›", width=4, command=lambda: self.change_page(1))
        self.next_button.pack(side="left")
        self.match_label = ttk.Label(toolbar, text="未执行查找")
        self.match_label.pack(side="right")
        self.canvas = __import__("tkinter").Canvas(parent, bg="#DDE2E0", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda _: self.root.after(100, self.render_page))

    def add_rule(self) -> None:
        if len(self.rule_rows) >= 12:
            self.set_status("最多可以添加 12 条标记规则。")
            return
        row = RuleRow(self, self.rule_frame, len(self.rule_rows) + 1)
        row.frame.pack(fill="x", pady=2)
        self.rule_rows.append(row)
        self.set_active_rule(row)
        self.invalidate()

    def remove_rule(self, row: RuleRow) -> None:
        if row in self.rule_rows:
            row.frame.destroy()
            self.rule_rows.remove(row)
            for index, current in enumerate(self.rule_rows, 1):
                current.index_label.configure(text=str(index))
            if self.active_rule_row is row:
                self.set_active_rule(self.rule_rows[-1] if self.rule_rows else None)
            self.invalidate()

    def set_active_rule(self, row: RuleRow | None) -> None:
        self.active_rule_row = row
        for current in self.rule_rows:
            current.index_label.configure(foreground="#1677FF" if current is row else "")
        if hasattr(self, "screen_picker_button"):
            if row in self.rule_rows:
                self.screen_picker_button.configure(text=f"屏幕取色·{self.rule_rows.index(row) + 1}")
            else:
                self.screen_picker_button.configure(text="屏幕取色")

    def apply_palette(self, color: str) -> None:
        row = self.active_rule_row or (self.rule_rows[-1] if self.rule_rows else None)
        if row:
            row.set_color(color)

    def pick_screen_color(self) -> None:
        import tkinter as tk
        from tkinter import messagebox

        row = self.active_rule_row or (self.rule_rows[-1] if self.rule_rows else None)
        if row is None:
            return
        self.root.withdraw()
        picker = None

        def restore() -> None:
            nonlocal picker
            if picker is not None:
                try:
                    picker.grab_release()
                except tk.TclError:
                    pass
                picker.destroy()
                picker = None
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()

        def cancel(_event=None) -> None:
            restore()

        def choose(_event=None) -> None:
            try:
                x, y = screen_cursor_position()
                picker.withdraw()
                picker.update_idletasks()

                def sample() -> None:
                    try:
                        row.set_color(screen_pixel_hex(x, y))
                    except Exception as error:
                        restore()
                        messagebox.showerror("屏幕取色失败", str(error), parent=self.root)
                    else:
                        restore()

                self.root.after(100, sample)
            except Exception as error:
                restore()
                messagebox.showerror("屏幕取色失败", str(error), parent=self.root)

        try:
            left, top, width, height = virtual_screen_bounds()
            picker = tk.Toplevel(self.root)
            picker.overrideredirect(True)
            picker.geometry(f"{width}x{height}{left:+d}{top:+d}")
            picker.configure(bg="white", cursor="crosshair")
            picker.attributes("-topmost", True)
            picker.attributes("-alpha", 0.01)
            picker.bind("<Button-1>", choose)
            picker.bind("<Button-3>", cancel)
            picker.bind("<Escape>", cancel)
            picker.grab_set()
            picker.focus_force()
        except Exception as error:
            restore()
            messagebox.showerror("屏幕取色失败", str(error), parent=self.root)

    def capture_port_color_table(self) -> None:
        import tkinter as tk
        from tkinter import messagebox

        self.root.withdraw()
        picker = None
        canvas = None
        start: tuple[int, int] | None = None
        selection_id = None

        def restore() -> None:
            nonlocal picker
            if picker is not None:
                try:
                    picker.grab_release()
                except tk.TclError:
                    pass
                picker.destroy()
                picker = None
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()

        def cancel(_event=None) -> None:
            restore()

        def begin(event) -> None:
            nonlocal start, selection_id
            start = (event.x, event.y)
            if selection_id is not None:
                canvas.delete(selection_id)
            selection_id = canvas.create_rectangle(
                event.x,
                event.y,
                event.x,
                event.y,
                outline="#00E5FF",
                width=7,
            )

        def drag(event) -> None:
            if start is not None and selection_id is not None:
                canvas.coords(selection_id, start[0], start[1], event.x, event.y)

        def finish(event) -> None:
            if start is None:
                return
            x0, x1 = sorted((start[0], event.x))
            y0, y1 = sorted((start[1], event.y))
            if x1 - x0 < 40 or y1 - y0 < 30:
                messagebox.showwarning("框选范围太小", "请框住完整的港口代码和彩色单元格。", parent=picker)
                return
            screen_box = (left + x0, top + y0, left + x1, top + y1)
            picker.withdraw()
            picker.update_idletasks()

            def capture() -> None:
                try:
                    from PIL import ImageGrab

                    image = ImageGrab.grab(bbox=screen_box, all_screens=True)
                except Exception as error:
                    restore()
                    messagebox.showerror("港口表采集失败", str(error), parent=self.root)
                    return
                restore()
                self.set_busy(True, "正在识别框选区域中的五位港口代码和对应颜色...")

                def done(candidates: list[CapturedPortRule]) -> None:
                    self.set_busy(False)
                    if not candidates:
                        messagebox.showwarning(
                            "未识别到港口代码",
                            "框选区域内没有识别到五位英文字母港口代码。请缩小范围并完整框住彩色港口表。",
                            parent=self.root,
                        )
                        return
                    self.show_captured_port_rules(candidates)

                self._background(lambda: recognize_port_color_table(image), done)

            self.root.after(150, capture)

        try:
            left, top, width, height = virtual_screen_bounds()
            picker = tk.Toplevel(self.root)
            picker.overrideredirect(True)
            picker.geometry(f"{width}x{height}{left:+d}{top:+d}")
            picker.configure(bg="#101820", cursor="crosshair")
            picker.attributes("-topmost", True)
            picker.attributes("-alpha", 0.20)
            canvas = tk.Canvas(picker, bg="#101820", highlightthickness=0, cursor="crosshair")
            canvas.pack(fill="both", expand=True)
            canvas.create_rectangle(18, 18, 490, 58, fill="#001F2B", outline="#00E5FF", width=2)
            canvas.create_text(
                32,
                38,
                text="按住左键框选彩色港口表，松开后自动识别；Esc 或右键取消",
                fill="white",
                anchor="w",
                font=("Microsoft YaHei UI", 12, "bold"),
            )
            canvas.bind("<ButtonPress-1>", begin)
            canvas.bind("<B1-Motion>", drag)
            canvas.bind("<ButtonRelease-1>", finish)
            canvas.bind("<Button-3>", cancel)
            picker.bind("<Escape>", cancel)
            picker.grab_set()
            picker.focus_force()
        except Exception as error:
            restore()
            messagebox.showerror("港口表采集失败", str(error), parent=self.root)

    def show_captured_port_rules(self, candidates: list[CapturedPortRule]) -> None:
        import tkinter as tk
        from tkinter import colorchooser, messagebox, ttk

        dialog = tk.Toplevel(self.root)
        dialog.title("确认批量港口规则")
        dialog.geometry("620x560")
        dialog.minsize(540, 460)
        dialog.transient(self.root)
        dialog.grab_set()

        body = ttk.Frame(dialog, padding=16)
        body.pack(fill="both", expand=True)
        ttk.Label(body, text="已识别港口代码和色块", font=("Microsoft YaHei UI", 13, "bold")).pack(anchor="w")
        ttk.Label(body, text="可取消勾选、修正代码或点击色块改色；代码必须为五位英文字母。").pack(anchor="w", pady=(4, 10))

        list_host = ttk.Frame(body)
        list_host.pack(fill="both", expand=True)
        rows: list[tuple[tk.BooleanVar, tk.StringVar, dict[str, str]]] = []
        for index, candidate in enumerate(candidates[:12], 1):
            row = ttk.Frame(list_host)
            row.pack(fill="x", pady=3)
            selected = tk.BooleanVar(value=True)
            code = tk.StringVar(value=candidate.code)
            color_value = {"value": candidate.color}
            ttk.Checkbutton(row, variable=selected).pack(side="left")
            ttk.Label(row, text=str(index), width=3, anchor="center").pack(side="left")
            ttk.Entry(row, textvariable=code, width=12, font=("Consolas", 11, "bold")).pack(side="left", padx=(2, 8))
            color_button = tk.Button(row, bg=color_value["value"], width=7, relief="solid", bd=1)
            color_button.pack(side="left")

            def choose_color(target=color_value, button=color_button) -> None:
                value = colorchooser.askcolor(target["value"], title="选择港口颜色", parent=dialog)[1]
                if value:
                    target["value"] = value.upper()
                    button.configure(bg=target["value"])

            color_button.configure(command=choose_color)
            ttk.Label(row, text=f"OCR {candidate.confidence:.0%}").pack(side="left", padx=10)
            rows.append((selected, code, color_value))

        if len(candidates) > 12:
            ttk.Label(body, text=f"另有 {len(candidates) - 12} 条，因软件最多 12 条规则未列入。", foreground="#B42318").pack(anchor="w", pady=(5, 0))

        actions = ttk.Frame(body)
        actions.pack(fill="x", pady=(14, 0))

        def apply_rules() -> None:
            selected_rules: list[CapturedPortRule] = []
            invalid: list[str] = []
            for selected, code_var, color_value in rows:
                if not selected.get():
                    continue
                code = re.sub(r"[^A-Z]", "", code_var.get().upper())
                if not re.fullmatch(r"[A-Z]{5}", code):
                    invalid.append(code_var.get().strip() or "空白")
                    continue
                selected_rules.append(CapturedPortRule(code, color_value["value"]))
            if invalid:
                messagebox.showerror("港口代码格式错误", "以下内容不是五位英文字母：\n" + "、".join(invalid), parent=dialog)
                return
            if not selected_rules:
                messagebox.showwarning("没有选择规则", "请至少勾选一条港口规则。", parent=dialog)
                return
            added, updated, skipped = self.apply_captured_port_rules(selected_rules)
            dialog.destroy()
            messagebox.showinfo(
                "港口规则采集完成",
                f"新增 {added} 条，更新颜色 {updated} 条，因超过 12 条跳过 {skipped} 条。",
                parent=self.root,
            )

        ttk.Button(actions, text="取消", command=dialog.destroy).pack(side="right")
        ttk.Button(actions, text="添加所选规则", command=apply_rules).pack(side="right", padx=(0, 8))

    def apply_captured_port_rules(self, candidates: list[CapturedPortRule]) -> tuple[int, int, int]:
        existing = {
            row.keyword.get().strip().upper(): row
            for row in self.rule_rows
            if row.keyword.get().strip()
        }
        added = updated = skipped = 0
        last_row = None
        for candidate in candidates:
            row = existing.get(candidate.code)
            if row is not None:
                row.set_color(candidate.color)
                updated += 1
                last_row = row
                continue
            row = next((current for current in self.rule_rows if not current.keyword.get().strip()), None)
            if row is None:
                if len(self.rule_rows) >= 12:
                    skipped += 1
                    continue
                self.add_rule()
                row = self.rule_rows[-1]
            row.keyword.set(candidate.code)
            row.match_type.set(MATCH_LABELS["port"])
            row.mode.set(MODE_LABELS["region"])
            row.set_color(candidate.color)
            existing[candidate.code] = row
            added += 1
            last_row = row
        if last_row is not None:
            self.set_active_rule(last_row)
        self.invalidate()
        self.set_status(f"港口颜色表采集完成：新增 {added} 条，更新 {updated} 条，跳过 {skipped} 条。")
        return added, updated, skipped

    def refresh_special_rules(self) -> None:
        import tkinter as tk
        from tkinter import ttk

        for child in self.special_rule_frame.winfo_children():
            child.destroy()
        for rule in self.special_rules:
            row = ttk.Frame(self.special_rule_frame)
            row.pack(fill="x", pady=2)
            dot = tk.Canvas(row, width=18, height=18, highlightthickness=0, bg="#F0F0F0")
            dot.create_oval(3, 3, 15, 15, fill=rule.color, outline=rule.color)
            dot.pack(side="left", padx=(2, 5))
            ttk.Label(row, text=rule.label, font=("Microsoft YaHei UI", 9, "bold")).pack(side="left")
            criteria: list[str] = []
            if rule.container_numbers:
                criteria.append(f"{len(rule.container_numbers)} 柜号")
            if rule.type_codes:
                criteria.append(f"{len(rule.type_codes)} 属性码")
            if rule.iso_types:
                criteria.append(f"{len(rule.iso_types)} 箱型")
            ttk.Label(row, text=" · ".join(criteria)).pack(side="left", padx=8)
            ttk.Button(row, text="×", width=3, command=lambda current=rule: self.remove_special_rule(current)).pack(side="right")
            ttk.Button(row, text="编辑", width=5, command=lambda current=rule: self.open_special_rule_dialog(current)).pack(side="right", padx=3)

    def show_box_type_statistics(self) -> None:
        from tkinter import messagebox

        if not self.document or not self.file_path:
            messagebox.showinfo("统计本船箱型", "请先选择需要统计的 PDF。", parent=self.root)
            return
        source_path = Path(self.file_path)
        self.set_busy(True, "正在统计本船存在的箱型及数量...")

        def report_progress(page_number: int, total_pages: int) -> None:
            self.root.after(
                0,
                lambda current=page_number, total=total_pages: self.set_status(
                    f"正在统计本船箱型：第 {current} / {total} 页..."
                ),
            )

        def success(inventory: BoxTypeInventory) -> None:
            self.set_busy(False)
            self.open_box_type_statistics_dialog(inventory)

        self._background(
            lambda: scan_box_type_inventory(source_path, progress=report_progress),
            success,
        )

    def open_box_type_statistics_dialog(self, inventory: BoxTypeInventory) -> None:
        import tkinter as tk
        from tkinter import ttk

        dialog = tk.Toplevel(self.root)
        dialog.title("本船箱型及数量统计")
        dialog.geometry("600x560")
        dialog.minsize(520, 460)
        dialog.transient(self.root)
        dialog.grab_set()
        body = ttk.Frame(dialog, padding=16)
        body.pack(fill="both", expand=True)

        known_total = sum(inventory.known_counts.values())
        unknown_total = sum(inventory.unknown_counts.values())
        ttk.Label(body, text="本船箱型及数量", font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w")
        ttk.Label(
            body,
            text=(
                f"实际集装箱 {inventory.container_cells} 柜 · 已识别 {known_total} 柜 · "
                f"未知代码 {unknown_total} 柜 · 未提取 {inventory.unreadable_cells} 柜"
            ),
        ).pack(anchor="w", pady=(4, 2))
        if inventory.duplicate_cells:
            ttk.Label(
                body,
                text=f"重复柜格已去重 {inventory.duplicate_cells} 处（按柜号末 7 位全船去重）",
                foreground="#9A6700",
            ).pack(anchor="w", pady=(0, 10))
        else:
            ttk.Label(body, text="未发现重复柜格", foreground="#666666").pack(anchor="w", pady=(0, 10))

        table_host = ttk.Frame(body)
        table_host.pack(fill="both", expand=True)
        tree = ttk.Treeview(table_host, columns=("box_type", "count", "status"), show="headings", height=17)
        tree.heading("box_type", text="箱型代码")
        tree.heading("count", text="箱型数量")
        tree.heading("status", text="识别结果")
        tree.column("box_type", width=210, anchor="w")
        tree.column("count", width=100, anchor="center")
        tree.column("status", width=180, anchor="w")
        scrollbar = ttk.Scrollbar(table_host, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        tree.tag_configure("section", background="#E8E8E8", font=("Microsoft YaHei UI", 9, "bold"))
        tree.tag_configure("unknown", foreground="#B42318", font=("Microsoft YaHei UI", 9, "bold"))

        tree.insert("", "end", values=("已识别箱型", "", ""), tags=("section",))
        type_order = {box_type: index for index, box_type in enumerate(ISO_TYPES)}
        for box_type, count in sorted(
            inventory.known_counts.items(),
            key=lambda item: (type_order.get(item[0], len(type_order)), item[0]),
        ):
            tree.insert("", "end", values=(box_type, count, "已识别"))

        tree.insert("", "end", values=("未知箱型代码如下", "", ""), tags=("section",))
        if inventory.unknown_counts:
            for box_type, count in sorted(inventory.unknown_counts.items()):
                tree.insert("", "end", values=(box_type, count, "未知箱型代码"), tags=("unknown",))
        else:
            tree.insert("", "end", values=("未发现", 0, "无未知箱型"))

        if inventory.unreadable_cells:
            tree.insert(
                "",
                "end",
                values=("未提取到代码", inventory.unreadable_cells, "柜格内无符合格式的箱型代码"),
                tags=("unknown",),
            )

        report_lines = [
            "本船箱型及数量统计",
            f"实际集装箱：{inventory.container_cells}",
            f"重复柜格已去重：{inventory.duplicate_cells}",
            "",
            "已识别箱型：",
        ]
        report_lines.extend(
            f"{box_type}: {count}"
            for box_type, count in sorted(
                inventory.known_counts.items(),
                key=lambda item: (type_order.get(item[0], len(type_order)), item[0]),
            )
        )
        report_lines.extend(("", "未知箱型代码如下："))
        if inventory.unknown_counts:
            report_lines.extend(f"{box_type}: {count}" for box_type, count in sorted(inventory.unknown_counts.items()))
        else:
            report_lines.append("未发现")
        if inventory.unreadable_cells:
            report_lines.append(f"未提取到代码: {inventory.unreadable_cells}")

        actions = ttk.Frame(body)
        actions.pack(fill="x", pady=(12, 0))

        def copy_report() -> None:
            self.root.clipboard_clear()
            self.root.clipboard_append("\n".join(report_lines))
            self.set_status("本船箱型统计结果已复制到剪贴板。")

        ttk.Button(actions, text="关闭", command=dialog.destroy).pack(side="right")
        ttk.Button(actions, text="复制统计结果", command=copy_report).pack(side="right", padx=(0, 6))

    def detect_special_categories(self) -> None:
        from tkinter import messagebox

        if not self.document or not self.file_path:
            messagebox.showinfo("智能提取本船特殊柜箱型", "请先选择需要识别的 PDF。", parent=self.root)
            return
        if len(self.special_rules) >= 12:
            messagebox.showinfo("智能提取本船特殊柜箱型", "特殊柜规则已达到 12 条上限，请先删除或编辑现有规则。", parent=self.root)
            return
        source_path = Path(self.file_path)
        self.set_busy(True, "正在智能提取本船图中的特殊柜箱型...")

        def report_progress(page_number: int, total_pages: int) -> None:
            self.root.after(
                0,
                lambda current=page_number, total=total_pages: self.set_status(
                    f"正在智能提取特殊柜箱型：第 {current} / {total} 页..."
                ),
            )

        def success(detected: list[DetectedSpecialCategory]) -> None:
            self.set_busy(False)
            if not detected:
                self.set_status("未在含柜号的贝位单元格中识别到特殊箱型。")
                messagebox.showinfo(
                    "智能提取本船特殊柜箱型",
                    "未识别到罐式箱、冷冻箱、OT柜或框架/超限箱。",
                    parent=self.root,
                )
                return
            self.open_detected_special_dialog(detected)

        self._background(
            lambda: scan_present_special_categories(source_path, progress=report_progress),
            success,
        )

    def open_detected_special_dialog(self, detected: list[DetectedSpecialCategory]) -> None:
        import tkinter as tk
        from tkinter import colorchooser, messagebox, ttk

        dialog = tk.Toplevel(self.root)
        dialog.title("智能提取本船特殊柜箱型")
        dialog.geometry("780x430")
        dialog.minsize(700, 390)
        dialog.transient(self.root)
        dialog.grab_set()
        body = ttk.Frame(dialog, padding=16)
        body.pack(fill="both", expand=True)

        ttk.Label(
            body,
            text="已识别本船实际存在的特殊箱型。勾选需要添加的规则，名称和颜色可直接修改。",
            font=("Microsoft YaHei UI", 10, "bold"),
        ).pack(anchor="w", pady=(0, 12))

        table = ttk.Frame(body)
        table.pack(fill="both", expand=True)
        for column, text, width in ((0, "添加", 6), (1, "识别结果", 19), (2, "规则名称", 22), (3, "默认颜色", 10), (4, "状态", 18)):
            ttk.Label(table, text=text, width=width, anchor="w", font=("Microsoft YaHei UI", 9, "bold")).grid(
                row=0, column=column, sticky="ew", padx=4, pady=(0, 5)
            )
        table.columnconfigure(2, weight=1)

        rows: list[dict] = []
        for row_index, category in enumerate(detected, 1):
            overlapping_rules = [
                rule
                for rule in self.special_rules
                if set(rule.type_codes).intersection(category.type_codes)
                or set(rule.iso_types).intersection(category.iso_types)
            ]
            available = not overlapping_rules
            selected_var = tk.BooleanVar(value=available)
            label_var = tk.StringVar(value=category.default_label)
            color_value = {"value": category.default_color}
            check = ttk.Checkbutton(table, variable=selected_var)
            check.grid(row=row_index, column=0, sticky="w", padx=4, pady=7)
            if not available:
                check.configure(state="disabled")

            detected_values = [*category.detected_type_codes, *category.detected_iso_types]
            detail = "、".join(detected_values) if detected_values else "已匹配特殊属性"
            ttk.Label(table, text=f"{category.count} 柜：{detail}", wraplength=210).grid(
                row=row_index, column=1, sticky="w", padx=4, pady=7
            )
            name_entry = ttk.Entry(table, textvariable=label_var)
            name_entry.grid(row=row_index, column=2, sticky="ew", padx=4, pady=7)
            if not available:
                name_entry.configure(state="disabled")

            color_button = tk.Button(table, bg=color_value["value"], width=7, relief="solid", bd=1)
            color_button.grid(row=row_index, column=3, sticky="w", padx=4, pady=7)

            def choose_row_color(value=color_value, button=color_button) -> None:
                selected_color = colorchooser.askcolor(value["value"], title="选择特殊柜颜色", parent=dialog)[1]
                if selected_color:
                    value["value"] = selected_color.upper()
                    button.configure(bg=value["value"])

            color_button.configure(command=choose_row_color, state="normal" if available else "disabled")
            status_text = "可添加" if available else "已存在：" + "、".join(rule.label for rule in overlapping_rules)
            ttk.Label(table, text=status_text, foreground="#666666", wraplength=150).grid(
                row=row_index, column=4, sticky="w", padx=4, pady=7
            )
            rows.append({
                "category": category,
                "selected": selected_var,
                "label": label_var,
                "color": color_value,
                "available": available,
            })

        ttk.Separator(body).pack(fill="x", pady=(8, 10))
        ttk.Label(
            body,
            text="默认：油罐TK柜=紫色，冷冻箱=蓝色，OT柜=天蓝色，框架/超限箱=橙色。添加后仍可在主界面编辑。",
            foreground="#555555",
        ).pack(anchor="w")
        actions = ttk.Frame(body)
        actions.pack(fill="x", pady=(14, 0))

        def add_selected() -> None:
            selected_rows = [row for row in rows if row["available"] and row["selected"].get()]
            if not selected_rows:
                messagebox.showerror("无法添加", "请至少勾选一种已识别箱型。", parent=dialog)
                return
            if len(self.special_rules) + len(selected_rows) > 12:
                messagebox.showerror(
                    "无法添加",
                    f"最多 12 条特殊柜规则，当前还可添加 {max(0, 12 - len(self.special_rules))} 条。",
                    parent=dialog,
                )
                return
            prepared_rows = []
            for row in selected_rows:
                category = row["category"]
                label = row["label"].get().strip()
                if not label:
                    messagebox.showerror("无法添加", "规则名称不能为空。", parent=dialog)
                    return
                prepared_rows.append((category, label, normalize_hex(row["color"]["value"])))
            for category, label, color in prepared_rows:
                self.special_rules.append(SpecialRule(
                    label,
                    [],
                    color,
                    f"special-{self.next_special_id}",
                    list(category.type_codes),
                    list(category.iso_types),
                ))
                self.next_special_id += 1
            self.refresh_special_rules()
            self.invalidate()
            self.set_status(f"已根据本船箱型添加 {len(selected_rows)} 条特殊柜规则，可继续编辑名称和颜色。")
            dialog.destroy()

        ttk.Button(actions, text="取消", command=dialog.destroy).pack(side="right")
        ttk.Button(actions, text="勾选添加规则", command=add_selected).pack(side="right", padx=(0, 6))

    def open_special_rule_dialog(self, existing: SpecialRule | None = None) -> None:
        import tkinter as tk
        from tkinter import colorchooser, messagebox, ttk

        if existing is None and len(self.special_rules) >= 12:
            self.show_error(ValueError("最多可以添加 12 条特殊柜规则。"))
            return
        dialog = tk.Toplevel(self.root)
        dialog.title("编辑特殊柜规则" if existing else "添加特殊柜规则")
        dialog.geometry("680x720")
        dialog.minsize(600, 620)
        dialog.transient(self.root)
        dialog.grab_set()
        body = ttk.Frame(dialog, padding=16)
        body.pack(fill="both", expand=True)

        ttk.Label(body, text="自定义文字", font=("Microsoft YaHei UI", 9, "bold")).pack(anchor="w")
        label_var = tk.StringVar(value=existing.label if existing else "特殊柜")
        label_row = ttk.Frame(body)
        label_row.pack(fill="x", pady=(4, 12))
        label_entry = ttk.Entry(label_row, textvariable=label_var)
        label_entry.pack(side="left", fill="x", expand=True)
        auto_label_button = ttk.Button(label_row, text="按勾选自动填写")
        auto_label_button.pack(side="right", padx=(8, 0))

        color_value = {"value": existing.color if existing else "#D9363E"}
        color_row = ttk.Frame(body)
        color_row.pack(fill="x", pady=(0, 12))
        ttk.Label(color_row, text="圆点及图例颜色", font=("Microsoft YaHei UI", 9, "bold")).pack(side="left")
        color_button = tk.Button(color_row, bg=color_value["value"], width=7, relief="solid", bd=1)
        color_button.pack(side="right")

        def choose_color() -> None:
            value = colorchooser.askcolor(color_value["value"], title="选择特殊柜颜色", parent=dialog)[1]
            if value:
                color_value["value"] = value.upper()
                color_button.configure(bg=color_value["value"])

        color_button.configure(command=choose_color)

        iso_frame = ttk.LabelFrame(body, text="ISO 标准箱型（按贝图完整代码自动识别）", padding=8)
        iso_frame.pack(fill="x", pady=(0, 10))
        iso_vars = {box_type: tk.BooleanVar(value=bool(existing and box_type in existing.iso_types)) for box_type in ISO_TYPES}
        iso_row = 0
        for group_name, box_types in ISO_TYPE_GROUPS:
            ttk.Label(iso_frame, text=group_name, width=10).grid(row=iso_row, column=0, sticky="nw", padx=(0, 6), pady=2)
            for index, box_type in enumerate(box_types):
                ttk.Checkbutton(iso_frame, text=box_type, variable=iso_vars[box_type]).grid(
                    row=iso_row + index // 6,
                    column=1 + index % 6,
                    sticky="w",
                    padx=3,
                    pady=2,
                )
            iso_row += max(1, math.ceil(len(box_types) / 6))

        type_frame = ttk.LabelFrame(body, text="特殊属性代码（独立代码 + 20/40 尺 ISO 精确匹配）", padding=8)
        type_frame.pack(fill="x", pady=(0, 10))
        type_vars = {code: tk.BooleanVar(value=bool(existing and code in existing.type_codes)) for code in SPECIAL_TYPE_CODES}
        type_row = 0
        for group_name, codes in SPECIAL_TYPE_GROUPS:
            ttk.Label(type_frame, text=group_name, width=14).grid(row=type_row, column=0, sticky="w", padx=(0, 6), pady=2)
            for index, code in enumerate(codes):
                ttk.Checkbutton(type_frame, text=code, variable=type_vars[code]).grid(row=type_row, column=1 + index, sticky="w", padx=4, pady=2)
            type_row += 1

        def auto_fill_label() -> None:
            selected_codes = [code for code, variable in type_vars.items() if variable.get()]
            selected_box_types = [box_type for box_type, variable in iso_vars.items() if variable.get()]
            label_var.set(suggested_special_label(selected_codes, selected_box_types))
            label_entry.focus_set()
            label_entry.icursor("end")

        auto_label_button.configure(command=auto_fill_label)

        ttk.Label(body, text="指定特殊柜号（可选，每行一个；自动按末尾 7 位数字查找）", font=("Microsoft YaHei UI", 9, "bold")).pack(anchor="w")
        number_text = tk.Text(body, height=7, wrap="word", font=("Consolas", 10), undo=True)
        number_text.pack(fill="both", expand=True, pady=(4, 12))
        if existing:
            number_text.insert("1.0", "\n".join(existing.container_numbers))

        actions = ttk.Frame(body)
        actions.pack(fill="x")

        def save() -> None:
            label = label_var.get().strip()
            numbers = parse_container_numbers(number_text.get("1.0", "end"))
            selected_type_codes = [code for code, variable in type_vars.items() if variable.get()]
            selected_iso_types = [box_type for box_type, variable in iso_vars.items() if variable.get()]
            if not label:
                messagebox.showerror("无法保存", "请填写自定义文字。", parent=dialog)
                return
            if not numbers and not selected_type_codes and not selected_iso_types:
                messagebox.showerror("无法保存", "请至少勾选一种箱型、属性代码，或粘贴一个有效柜号。", parent=dialog)
                return
            if existing:
                existing.label = label
                existing.container_numbers = numbers
                existing.color = color_value["value"]
                existing.type_codes = selected_type_codes
                existing.iso_types = selected_iso_types
            else:
                self.special_rules.append(SpecialRule(
                    label,
                    numbers,
                    color_value["value"],
                    f"special-{self.next_special_id}",
                    selected_type_codes,
                    selected_iso_types,
                ))
                self.next_special_id += 1
            self.refresh_special_rules()
            self.invalidate()
            dialog.destroy()

        ttk.Button(actions, text="取消", command=dialog.destroy).pack(side="right")
        ttk.Button(actions, text="保存规则", command=save).pack(side="right", padx=(0, 6))
        label_entry.focus_set()

    def remove_special_rule(self, rule: SpecialRule) -> None:
        if rule in self.special_rules:
            self.special_rules.remove(rule)
            self.refresh_special_rules()
            self.invalidate()

    def collect_special_rules(self) -> list[SpecialRule]:
        rules = [SpecialRule(
            rule.label,
            list(rule.container_numbers),
            rule.color,
            rule.rule_id,
            list(rule.type_codes),
            list(rule.iso_types),
        ) for rule in self.special_rules]
        validate_special_rules(rules)
        return rules

    def collect_rules(self) -> list[Rule]:
        rules = [rule for index, row in enumerate(self.rule_rows, 1) if (rule := row.to_rule(index))]
        validate_rules(rules, self.case_sensitive.get(), require=False)
        return rules

    def choose_pdf(self) -> None:
        from tkinter import filedialog

        value = filedialog.askopenfilename(title="选择 PDF", filetypes=(("PDF 文件", "*.pdf"), ("所有文件", "*.*")))
        if value:
            self.load_pdf(Path(value))

    def load_pdf(self, path: Path) -> None:
        try:
            ensure_fitz()
            document = fitz.open(str(path))
            if document.needs_pass:
                document.close()
                raise ValueError("暂不支持带密码的 PDF。")
            if self.document:
                self.document.close()
            self.document = document
            self.file_path = path
            self.current_page = 1
            self.result = None
            self.file_summary.configure(text=f"{path.name} · {document.page_count} 页 · {path.stat().st_size / 1024:.0f} KB")
            self.set_status("PDF 已载入。填写目标文字后点击“查找并预览全部规则”。")
            self.update_navigation()
            self.render_page()
        except Exception as error:
            self.show_error(error)

    def invalidate(self) -> None:
        self.result = None
        self.match_label.configure(text="规则已修改，请重新查找")
        self.render_page()

    def set_status(self, message: str) -> None:
        self.status.configure(state="normal")
        self.status.delete("1.0", "end")
        self.status.insert("1.0", message)
        self.status.configure(state="disabled")

    def set_busy(self, value: bool, message: str = "") -> None:
        self.busy = value
        state = "disabled" if value or not self.document else "normal"
        self.preview_button.configure(state=state)
        self.export_button.configure(state=state)
        self.smart_special_button.configure(state=state)
        self.box_type_stats_button.configure(state=state)
        if message:
            self.set_status(message)
        self.root.configure(cursor="watch" if value else "")

    def show_error(self, error: Exception) -> None:
        from tkinter import messagebox

        self.set_busy(False)
        self.set_status(str(error))
        messagebox.showerror("处理失败", str(error), parent=self.root)

    def update_navigation(self) -> None:
        total = self.document.page_count if self.document else 0
        self.page_label.configure(text=f"{self.current_page} / {total}" if total else "0 / 0")
        self.prev_button.configure(state="normal" if total and self.current_page > 1 and not self.busy else "disabled")
        self.next_button.configure(state="normal" if total and self.current_page < total and not self.busy else "disabled")
        state = "normal" if total and not self.busy else "disabled"
        self.preview_button.configure(state=state)
        self.export_button.configure(state=state)
        self.smart_special_button.configure(state=state)
        self.box_type_stats_button.configure(state=state)

    def change_page(self, delta: int) -> None:
        if not self.document or self.busy:
            return
        self.current_page = max(1, min(self.document.page_count, self.current_page + delta))
        self.update_navigation()
        self.render_page()

    def _background(self, worker: Callable, success: Callable) -> None:
        def run():
            try:
                value = worker()
                self.root.after(0, lambda: success(value))
            except Exception as error:
                traceback.print_exc()
                self.root.after(0, lambda error=error: self.show_error(error))

        threading.Thread(target=run, daemon=True).start()

    def show_special_conflict_dialog(self, conflicts: list[SpecialConflict]) -> str | None:
        import tkinter as tk
        from tkinter import ttk

        dialog = tk.Toplevel(self.root)
        dialog.title("特殊箱规则冲突")
        dialog.geometry("760x560")
        dialog.minsize(660, 480)
        dialog.transient(self.root)
        dialog.grab_set()
        result = {"value": None}

        body = ttk.Frame(dialog, padding=16)
        body.pack(fill="both", expand=True)
        ttk.Label(body, text="该规则存在冲突 特殊箱", font=("Microsoft YaHei UI", 13, "bold"), foreground="#B42318").pack(anchor="w")
        ttk.Label(body, text=f"共 {len(conflicts)} 个单元格同时命中多条特殊柜规则。", font=("Microsoft YaHei UI", 9, "bold")).pack(anchor="w", pady=(5, 10))

        conflict_text = tk.Text(body, height=15, wrap="none", font=("Consolas", 10), relief="solid", bd=1)
        conflict_text.pack(fill="both", expand=True)
        seen_lines: set[str] = set()
        for conflict in conflicts:
            identifier = conflict.container_number or f"第{conflict.page_number}页 单元格({conflict.cell[0]:.0f},{conflict.cell[1]:.0f})"
            line = f"{identifier}    {'  <->  '.join(conflict.rule_labels)}"
            if line not in seen_lines:
                conflict_text.insert("end", line + "\n")
                seen_lines.add(line)
        conflict_text.configure(state="disabled")

        first_labels = list(dict.fromkeys(conflict.rule_labels[0] for conflict in conflicts))
        last_labels = list(dict.fromkeys(conflict.rule_labels[-1] for conflict in conflicts))
        first_name = "、".join(first_labels[:2]) + ("等" if len(first_labels) > 2 else "")
        last_name = "、".join(last_labels[:2]) + ("等" if len(last_labels) > 2 else "")

        buttons = ttk.Frame(body)
        buttons.pack(fill="x", pady=(14, 0))
        buttons.columnconfigure((0, 1), weight=1, uniform="conflict")

        def choose(value: str) -> None:
            result["value"] = value
            dialog.destroy()

        ttk.Button(buttons, text=f"第一条规则优先（{first_name}）", command=lambda: choose("first")).grid(row=0, column=0, sticky="ew", padx=(0, 5), pady=(0, 8))
        ttk.Button(buttons, text=f"最后一条规则优先（{last_name}）", command=lambda: choose("last")).grid(row=0, column=1, sticky="ew", padx=(5, 0), pady=(0, 8))
        ttk.Button(buttons, text="规则并存（合并为一个双色圆点）", command=lambda: choose("coexist")).grid(row=1, column=0, sticky="ew", padx=(0, 5))
        ttk.Button(buttons, text="自定义冲突规则", command=lambda: choose("custom")).grid(row=1, column=1, sticky="ew", padx=(5, 0))
        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
        dialog.wait_window()
        return result["value"]

    def show_custom_conflict_rule_dialog(self, conflicts: list[SpecialConflict]) -> SpecialRule | None:
        import tkinter as tk
        from tkinter import colorchooser, messagebox, ttk

        dialog = tk.Toplevel(self.root)
        dialog.title("自定义冲突集装箱规则")
        dialog.geometry("640x520")
        dialog.minsize(560, 440)
        dialog.transient(self.root)
        dialog.grab_set()
        result: dict[str, SpecialRule | None] = {"value": None}
        body = ttk.Frame(dialog, padding=16)
        body.pack(fill="both", expand=True)

        ttk.Label(body, text="自定义名称", font=("Microsoft YaHei UI", 9, "bold")).pack(anchor="w")
        label_var = tk.StringVar(value="冲突集装箱规则")
        ttk.Entry(body, textvariable=label_var).pack(fill="x", pady=(4, 12))

        color_value = {"value": "#FF8C00"}
        color_row = ttk.Frame(body)
        color_row.pack(fill="x", pady=(0, 12))
        ttk.Label(color_row, text="圆点及图例颜色", font=("Microsoft YaHei UI", 9, "bold")).pack(side="left")
        color_button = tk.Button(color_row, bg=color_value["value"], width=7, relief="solid", bd=1)
        color_button.pack(side="right")

        def choose_color() -> None:
            value = colorchooser.askcolor(color_value["value"], title="选择冲突规则颜色", parent=dialog)[1]
            if value:
                color_value["value"] = value.upper()
                color_button.configure(bg=color_value["value"])

        color_button.configure(command=choose_color)
        ttk.Label(body, text="以下存在冲突的集装箱箱号", font=("Microsoft YaHei UI", 9, "bold")).pack(anchor="w")
        number_text = tk.Text(body, height=12, wrap="none", font=("Consolas", 10), relief="solid", bd=1)
        number_text.pack(fill="both", expand=True, pady=(4, 12))
        numbers = list(dict.fromkeys(conflict.container_number for conflict in conflicts if conflict.container_number))
        if numbers:
            number_text.insert("1.0", "\n".join(numbers))
        else:
            number_text.insert("1.0", "未能从 PDF 提取完整柜号；仍会按冲突单元格应用。")
        number_text.configure(state="disabled")

        actions = ttk.Frame(body)
        actions.pack(fill="x")

        def apply() -> None:
            label = label_var.get().strip()
            if not label:
                messagebox.showerror("无法应用", "请填写自定义名称。", parent=dialog)
                return
            rule_id = f"conflict-custom-{self.next_special_id}"
            self.next_special_id += 1
            result["value"] = SpecialRule(label, numbers, color_value["value"], rule_id)
            dialog.destroy()

        ttk.Button(actions, text="取消", command=dialog.destroy).pack(side="right")
        ttk.Button(actions, text="应用冲突规则", command=apply).pack(side="right", padx=(0, 6))
        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
        dialog.wait_window()
        return result["value"]

    def preview(self) -> None:
        if self.busy or not self.file_path:
            return
        try:
            rules = self.collect_rules()
            special_rules = self.collect_special_rules()
            if not rules and not special_rules:
                raise ValueError("请至少添加一条普通标记规则或特殊柜规则。")
        except Exception as error:
            self.show_error(error)
            return
        case_sensitive = self.case_sensitive.get()
        padding = self.padding.get()
        show_legends = self.show_legends.get()
        legend_placement = next(key for key, label in LEGEND_LABELS.items() if label == self.legend_placement.get())
        def progress(current, total):
            self.root.after(0, lambda: self.set_status(f"正在处理第 {current} / {total} 页..."))

        def finish(result: AnalysisResult) -> None:
            self.result = result
            self.set_busy(False)
            self.update_navigation()
            summary_rules = [*special_rules, *result.extra_special_rules]
            summary = result_summary(result, rules, summary_rules)
            if result.special_conflicts:
                summary += f"\n特殊箱冲突 {len(result.special_conflicts)} 个；已保证每柜最多一个圆点。"
            self.set_status(summary if result.total else "未找到目标文字。请检查大小写或 PDF 文字编码。")
            self.match_label.configure(text=f"共 {result.total} 处")
            self.render_page()

        def start_analysis(mode: str = "first", custom_rule: SpecialRule | None = None, prompt_conflicts: bool = True) -> None:
            message = "正在查找并分析全部页面..." if prompt_conflicts else "正在按冲突选择重新计算..."
            self.set_busy(True, message)

            def worker():
                return analyze_pdf(
                    self.file_path,
                    rules,
                    special_rules=special_rules,
                    case_sensitive=case_sensitive,
                    padding=padding,
                    show_legends=show_legends,
                    legend_placement=legend_placement,
                    special_conflict_mode=mode,
                    custom_conflict_rule=custom_rule,
                    progress=progress,
                )

            def done(result: AnalysisResult) -> None:
                if prompt_conflicts and result.special_conflicts:
                    self.set_busy(False)
                    choice = self.show_special_conflict_dialog(result.special_conflicts)
                    if choice is None:
                        self.set_status("已取消特殊箱冲突处理，未更新预览。")
                        return
                    if choice == "first":
                        finish(result)
                        return
                    selected_custom_rule = None
                    if choice == "custom":
                        selected_custom_rule = self.show_custom_conflict_rule_dialog(result.special_conflicts)
                        if selected_custom_rule is None:
                            self.set_status("已取消自定义冲突规则，未更新预览。")
                            return
                    start_analysis(choice, selected_custom_rule, False)
                    return
                finish(result)

            self._background(worker, done)

        start_analysis()

    def export(self) -> None:
        if self.busy or not self.file_path:
            return
        if self.result is None:
            self.preview()
            self.set_status("请先完成查找预览，再点击生成 PDF。")
            return
        if not self.result.total:
            self.show_error(ValueError("没有找到目标文字，未生成 PDF。"))
            return
        from tkinter import filedialog

        default_name = self.file_path.stem + "_港口分区标记.pdf"
        value = filedialog.asksaveasfilename(title="生成 PDF", initialdir=str(self.file_path.parent), initialfile=default_name, defaultextension=".pdf", filetypes=(("PDF 文件", "*.pdf"),))
        if not value:
            return
        opacity = self.opacity.get() / 100
        outline_width = self.outline_width.get()
        self.set_busy(True, "正在生成新 PDF...")

        def worker():
            return export_pdf(self.file_path, value, self.result, opacity=opacity, outline_width=outline_width)

        def done(output):
            from tkinter import messagebox

            self.set_busy(False)
            self.update_navigation()
            self.set_status(f"已生成：{output}\n共匹配 {self.result.total} 处。")
            messagebox.showinfo("生成完成", f"已生成新 PDF：\n{output}", parent=self.root)

        self._background(worker, done)

    def render_page(self) -> None:
        if not self.document or self.busy:
            return
        try:
            page = self.document[self.current_page - 1]
            available_w = max(200, self.canvas.winfo_width() - 30)
            available_h = max(200, self.canvas.winfo_height() - 30)
            scale = min(2.0, available_w / page.rect.width, available_h / page.rect.height)
            self.render_scale = scale
            pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
            import tkinter as tk

            self.photo = tk.PhotoImage(data=pix.tobytes("png"))
            self.canvas.delete("all")
            offset_x = max(15, (self.canvas.winfo_width() - pix.width) / 2)
            offset_y = max(15, (self.canvas.winfo_height() - pix.height) / 2)
            self.canvas.create_image(offset_x, offset_y, image=self.photo, anchor="nw")
            self.canvas.create_rectangle(offset_x, offset_y, offset_x + pix.width, offset_y + pix.height, outline="#8B9490")
            if self.result:
                self._draw_preview(offset_x, offset_y, scale)
        except Exception:
            traceback.print_exc()

    def _draw_preview(self, offset_x: float, offset_y: float, scale: float) -> None:
        marks = self.result.marks.get(self.current_page, [])
        opacity = self.opacity.get() / 100
        for mark, (x1, y1, x2, y2) in region_line_primitives(marks, self.outline_width.get()):
            coords = (x1, y1, x2, y2)
            draw_canvas_styled_line(
                self.canvas,
                coords,
                mark.line_style,
                mark.color,
                self.outline_width.get(),
                scale,
                offset_x,
                offset_y,
                region_inward_vector(mark, coords),
            )
        for mark in marks:
            color = mark.color
            if mark.mode == "region":
                continue
            if mark.mode == "dot":
                for x0, y0, x1, y1 in mark.rects:
                    coords = (
                        offset_x + x0 * scale,
                        offset_y + y0 * scale,
                        offset_x + x1 * scale,
                        offset_y + y1 * scale,
                    )
                    self.canvas.create_oval(*coords, fill=color, outline=mark.secondary_color or color, width=2 if mark.secondary_color else 1)
                continue
            stipple = "gray50" if opacity < 0.6 else "gray25"
            for x0, y0, x1, y1 in mark.rects:
                coords = (offset_x + x0 * scale, offset_y + y0 * scale, offset_x + x1 * scale, offset_y + y1 * scale)
                if mark.mode == "cell-outline":
                    self.canvas.create_rectangle(*coords, outline=color, width=max(1, self.outline_width.get() * scale))
                else:
                    self.canvas.create_rectangle(*coords, outline="", fill=color, stipple=stipple)
        for legend in self.result.legends.get(self.current_page, []):
            x0, y0, x1, y1 = legend.rect
            coords = (offset_x + x0 * scale, offset_y + y0 * scale, offset_x + x1 * scale, offset_y + y1 * scale)
            if legend.kind == "special":
                radius = max(3, 4.5 * scale)
                center_x = coords[0] + radius + 2 * scale
                center_y = (coords[1] + coords[3]) / 2
                self.canvas.create_oval(center_x - radius, center_y - radius, center_x + radius, center_y + radius, fill=legend.color, outline=legend.secondary_color or legend.color, width=2 if legend.secondary_color else 1)
                self.canvas.create_text(center_x + radius + 5 * scale, center_y, text=legend.keyword[:24], fill=legend.color, anchor="w", font=("Microsoft YaHei UI", max(7, int(10 * scale)), "bold"))
                continue
            self.canvas.create_rectangle(*coords, fill=legend.color, outline="#244036")
            self.canvas.create_text((coords[0] + coords[2]) / 2, (coords[1] + coords[3]) / 2, text=legend.keyword[:24], font=("Arial", max(6, int(10 * scale))))
            if legend.kind == "region":
                draw_canvas_styled_line(
                    self.canvas,
                    (x0 + 3.0, y1 - 2.3, x1 - 3.0, y1 - 2.3),
                    legend.line_style,
                    "#FFFFFF",
                    1.4,
                    scale,
                    offset_x,
                    offset_y,
                )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=APP_NAME)
    parser.add_argument("input", nargs="?", help="输入 PDF；不填写时启动桌面窗口")
    parser.add_argument("--rule", action="append", default=[], help='规则："CMAU:#52C41A:region:port"')
    parser.add_argument("-o", "--output", help="输出 PDF 路径")
    parser.add_argument("--ignore-case", action="store_true", help="不区分大小写")
    parser.add_argument("--padding", type=float, default=1.0, help="文字底色边距（pt）")
    parser.add_argument("--opacity", type=float, default=45, help="颜色不透明度（15-85）")
    parser.add_argument("--outline-width", type=float, default=4.0, help="描边粗细（pt）")
    parser.add_argument("--no-legend", action="store_true", help="不生成页面颜色标识框")
    parser.add_argument("--legend-placement", choices=("top", "top-right", "auto"), default="top")
    parser.add_argument("--report", help="可选 JSON 分析报告路径")
    return parser


def request_startup_access(root) -> bool:
    from tkinter import messagebox, simpledialog

    while True:
        password = simpledialog.askstring(
            f"{APP_NAME} - 密码验证",
            "请输入打开密码：",
            show="*",
            parent=root,
        )
        if password is None:
            return False
        if password != OPEN_PASSWORD:
            messagebox.showerror(APP_NAME, "密码错误，请重新输入。", parent=root)
            continue
        if is_app_expired():
            messagebox.showwarning(APP_NAME, EXPIRED_MESSAGE, parent=root)
            return False
        return True


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.input:
        try:
            ensure_fitz()
        except RuntimeError as error:
            print(str(error), file=sys.stderr)
            return 1
        if not args.rule:
            parser.error("命令行模式至少需要一个 --rule")
        return run_cli(args)
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    root.withdraw()
    try:
        if not request_startup_access(root):
            root.destroy()
            return 0
        BayPlanApp(root)
        root.deiconify()
        root.mainloop()
        return 0
    except Exception as error:
        traceback.print_exc()
        messagebox.showerror("启动失败", str(error), parent=root)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
