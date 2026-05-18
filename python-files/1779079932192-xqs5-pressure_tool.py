import os
import re
import sys
import tarfile
import tempfile
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any

from PyQt5.QtCore import Qt, QThread, pyqtSignal, QRegularExpression
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QMessageBox,
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QTextEdit, QListWidget, QListWidgetItem, QSplitter, QFormLayout,
    QGroupBox, QGridLayout, QSpinBox, QStackedWidget, QDialog
)
from PyQt5.QtGui import QFont, QBrush, QColor, QTextCharFormat, QSyntaxHighlighter

from navigation_log_helper import NavigationLogHelper
from biz_log_helper import BizLogHelper
from collections import Counter

TS_RE = re.compile(r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s+\[(?P<lv>[A-Z]+)\]\s+(?P<msg>.*)$")

# 中台日志时间戳解析（支持两种格式：逗号或小数点分隔毫秒）
TS_BIZ_RE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})(?P<sep>[.,])(?P<frac>\d{3,6})"
)

def parse_any_ts(line: str) -> Optional[datetime]:
    """解析中台日志的时间戳格式"""
    m = TS_BIZ_RE.match(line)
    if not m:
        return None
    base = m.group("ts")
    frac = m.group("frac")[:6].ljust(6, "0")
    try:
        dt = datetime.strptime(base, "%Y-%m-%d %H:%M:%S")
        return dt.replace(microsecond=int(frac))
    except Exception:
        return None


class LogViewerDialog(QDialog):
    """独立的日志查看对话框，支持更大的显示空间"""
    def __init__(self, parent=None, title="日志查看器", log_type="nav"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(1600, 900)  # 更大的默认尺寸
        self.log_type = log_type  # 'nav', 'biz', or 'pressure'
        self.main_window = parent  # 保存主窗口引用
        self.all_lines = []  # 存储所有行，用于搜索
        self.current_file_path = ""  # 当前文件路径
        
        main_layout = QVBoxLayout(self)
        
        # 顶部控制栏
        ctrl_row = QHBoxLayout()
        ctrl_row.addWidget(QLabel("前N行"))
        self.spin_before = QSpinBox()
        self.spin_before.setRange(0, 5000)
        self.spin_before.setValue(100)
        ctrl_row.addWidget(self.spin_before)
        
        ctrl_row.addWidget(QLabel("后M行"))
        self.spin_after = QSpinBox()
        self.spin_after.setRange(0, 5000)
        self.spin_after.setValue(10)
        ctrl_row.addWidget(self.spin_after)
        
        # 同步按钮
        btn_sync = QPushButton("应用新设置")
        btn_sync.setToolTip("使用新的前N/后M设置重新加载日志")
        btn_sync.clicked.connect(self.reload_with_new_settings)
        ctrl_row.addWidget(btn_sync)
        
        ctrl_row.addStretch(1)
        main_layout.addLayout(ctrl_row)
        
        # 文件路径显示
        path_row = QHBoxLayout()
        path_row.addWidget(QLabel("日志文件:"))
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        path_row.addWidget(self.path_edit, 1)
        main_layout.addLayout(path_row)
        
        # 搜索功能区域
        search_group = QGroupBox("🔍 搜索功能")
        search_layout = QVBoxLayout(search_group)
        
        # 时间戳搜索
        ts_search_row = QHBoxLayout()
        ts_search_row.addWidget(QLabel("时间戳:"))
        self.ts_search_edit = QLineEdit()
        self.ts_search_edit.setPlaceholderText("YYYY-MM-DD HH:MM:SS,mmm")
        ts_search_row.addWidget(self.ts_search_edit, 1)
        
        btn_ts_search = QPushButton("时间戳定位")
        btn_ts_search.setToolTip("跳转到指定时间戳附近")
        btn_ts_search.clicked.connect(self.search_by_timestamp)
        ts_search_row.addWidget(btn_ts_search)
        search_layout.addLayout(ts_search_row)
        
        # 关键词搜索
        keyword_search_row = QHBoxLayout()
        keyword_search_row.addWidget(QLabel("关键词:"))
        self.keyword_search_edit = QLineEdit()
        self.keyword_search_edit.setPlaceholderText("输入关键词（支持正则表达式）")
        self.keyword_search_edit.returnPressed.connect(self.search_by_keyword)
        keyword_search_row.addWidget(self.keyword_search_edit, 1)
        
        btn_keyword_search = QPushButton("关键词搜索")
        btn_keyword_search.setToolTip("搜索包含关键词的行")
        btn_keyword_search.clicked.connect(self.search_by_keyword)
        keyword_search_row.addWidget(btn_keyword_search)
        
        btn_clear_search = QPushButton("清除高亮")
        btn_clear_search.setToolTip("清除搜索结果高亮")
        btn_clear_search.clicked.connect(self.clear_search_highlight)
        keyword_search_row.addWidget(btn_clear_search)
        
        search_layout.addLayout(keyword_search_row)
        
        # 搜索结果显示
        self.search_result_label = QLabel("")
        self.search_result_label.setStyleSheet("color: #1976D2; font-weight: bold;")
        search_layout.addWidget(self.search_result_label)
        
        main_layout.addWidget(search_group)
        
        # 提示信息
        self.hint_label = QLabel("")
        self.hint_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        main_layout.addWidget(self.hint_label)
        
        # 日志文本区域
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        font = QFont("Monospace")
        font.setStyleHint(QFont.TypeWriter)
        self.text_edit.setFont(font)
        main_layout.addWidget(self.text_edit, 1)
        
        # 添加语法高亮
        self.highlighter = LogHighlighter(self.text_edit.document())
        
        # 底部按钮
        btn_row = QHBoxLayout()
        btn_copy = QPushButton("复制全部内容")
        btn_copy.clicked.connect(self.copy_all_content)
        btn_row.addWidget(btn_copy)
        
        btn_close = QPushButton("关闭")
        btn_close.clicked.connect(self.close)
        btn_row.addWidget(btn_close)
        btn_row.addStretch(1)
        main_layout.addLayout(btn_row)
    
    def set_log_content(self, text: str, file_path: str = "", hint: str = "", all_lines: List[str] = None):
        """设置日志内容"""
        self.text_edit.setPlainText(text)
        if file_path:
            self.path_edit.setText(file_path)
            self.current_file_path = file_path
        if hint:
            self.hint_label.setText(hint)
        if all_lines is not None:
            self.all_lines = all_lines
        else:
            # 如果没有提供all_lines，从text中解析
            self.all_lines = text.splitlines()
    
    def copy_all_content(self):
        """复制全部日志内容"""
        QApplication.clipboard().setText(self.text_edit.toPlainText())
        QMessageBox.information(self, "提示", "已复制到剪贴板")
    
    def reload_with_new_settings(self):
        """使用新的前N/后M设置重新加载"""
        if not self.main_window:
            return
        
        # 获取当前显示的时间戳（从hint中提取或从主窗口获取）
        # 这里简化处理，提示用户手动输入时间戳或使用主窗口的最新选择
        QMessageBox.information(self, "提示", 
            "请在'时间戳'框中输入时间戳后点击'时间戳定位'，\n"
            "或在主窗口中重新选择失败项后再次弹出窗口。")
    
    def search_by_timestamp(self):
        """按时间戳搜索并定位"""
        ts_str = self.ts_search_edit.text().strip()
        if not ts_str:
            QMessageBox.warning(self, "提示", "请输入时间戳")
            return
        
        if not self.main_window:
            QMessageBox.warning(self, "错误", "主窗口引用丢失")
            return
        
        # 解析时间戳
        target_dt = self.main_window._parse_custom_timestamp(ts_str)
        if not target_dt:
            QMessageBox.warning(self, "提示", "时间戳格式不正确，请使用格式：YYYY-MM-DD HH:MM:SS,mmm")
            return
        
        if not self.all_lines:
            QMessageBox.warning(self, "提示", "日志内容为空")
            return
        
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            
            # 在all_lines中查找最接近的时间戳
            best_idx = -1
            best_dt = None
            min_diff = float('inf')
            
            for idx, line in enumerate(self.all_lines):
                dt = parse_ts(line)
                if dt:
                    diff = abs((dt - target_dt).total_seconds())
                    if diff < min_diff:
                        min_diff = diff
                        best_idx = idx
                        best_dt = dt
            
            if best_idx == -1:
                QMessageBox.information(self, "提示", f"未找到时间戳接近 {ts_str} 的日志行")
                return
            
            # 计算显示范围
            before_n = self.spin_before.value()
            after_m = self.spin_after.value()
            start_idx = max(0, best_idx - before_n)
            end_idx = min(len(self.all_lines), best_idx + after_m + 1)
            
            # 提取并显示
            display_lines = self.all_lines[start_idx:end_idx]
            display_text = "\n".join(display_lines)
            
            self.text_edit.setPlainText(display_text)
            
            # 更新提示
            hit_ts_str = self.main_window._fmt_dt_ms(best_dt) if best_dt else "N/A"
            hint = f"时间戳定位：{ts_str} | 实际命中：{hit_ts_str} | 行号：{best_idx + 1} | 显示范围：{start_idx + 1}-{end_idx}"
            self.hint_label.setText(hint)
            self.search_result_label.setText(f"✅ 找到时间戳：{hit_ts_str}（第 {best_idx + 1} 行）")
            
            # 滚动到中间位置
            cursor = self.text_edit.textCursor()
            cursor.setPosition(len("\n".join(display_lines[:before_n])))
            self.text_edit.setTextCursor(cursor)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"搜索失败：{str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            QApplication.restoreOverrideCursor()
    
    def search_by_keyword(self):
        """按关键词搜索"""
        keyword = self.keyword_search_edit.text().strip()
        if not keyword:
            QMessageBox.warning(self, "提示", "请输入关键词")
            return
        
        if not self.all_lines:
            QMessageBox.warning(self, "提示", "日志内容为空")
            return
        
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            
            # 尝试作为正则表达式
            try:
                pattern = re.compile(keyword, re.IGNORECASE)
            except re.error:
                # 如果不是合法的正则，退化为普通字符串匹配
                pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            
            # 查找所有匹配的行
            matched_lines = []
            for idx, line in enumerate(self.all_lines):
                if pattern.search(line):
                    matched_lines.append((idx, line))
            
            if not matched_lines:
                self.search_result_label.setText(f"❌ 未找到包含 '{keyword}' 的行")
                QMessageBox.information(self, "提示", f"未找到包含 '{keyword}' 的日志行")
                return
            
            # 显示所有匹配行（限制最多500行，避免卡顿）
            max_display = 500
            if len(matched_lines) > max_display:
                display_text = f"找到 {len(matched_lines)} 条匹配结果，显示前 {max_display} 条：\n\n"
                display_text += "\n".join([f"[行{idx+1}] {line}" for idx, line in matched_lines[:max_display]])
                display_text += f"\n\n... 还有 {len(matched_lines) - max_display} 条结果未显示"
            else:
                display_text = f"找到 {len(matched_lines)} 条匹配结果：\n\n"
                display_text += "\n".join([f"[行{idx+1}] {line}" for idx, line in matched_lines])
            
            self.text_edit.setPlainText(display_text)
            
            # 更新提示
            self.hint_label.setText(f"关键词搜索：'{keyword}' | 匹配行数：{len(matched_lines)}")
            self.search_result_label.setText(f"✅ 找到 {len(matched_lines)} 条匹配结果")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"搜索失败：{str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            QApplication.restoreOverrideCursor()
    
    def clear_search_highlight(self):
        """清除搜索结果，恢复原始显示"""
        if hasattr(self, '_original_text'):
            self.text_edit.setPlainText(self._original_text)
            self.search_result_label.setText("")
            self.hint_label.setText("")
            QMessageBox.information(self, "提示", "已恢复到原始日志内容")
        else:
            QMessageBox.information(self, "提示", "没有可清除的搜索结果")
    
    def reload_by_timestamp(self):
        """按时间戳重新加载日志"""
        if not self.main_window:
            return
        
        # 压测日志也支持时间戳查询了
        ts_str = self.custom_ts_edit.text().strip()
        if not ts_str:
            QMessageBox.warning(self, "提示", "请输入时间戳")
            return
        
        # 调用主窗口的方法重新加载
        target_dt = self.main_window._parse_custom_timestamp(ts_str)
        if not target_dt:
            QMessageBox.warning(self, "提示", "时间戳格式不正确，请使用格式：YYYY-MM-DD HH:MM:SS,mmm")
            return
        
        before_n = self.spin_before.value()
        after_m = self.spin_after.value()
        
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            
            if self.log_type == "nav":
                # 导航日志
                helper = self.main_window.nav_helper
                if helper is None:
                    nav_root = self.main_window.get_nav_root_dir()
                    if not nav_root:
                        QMessageBox.warning(self, "错误", "未找到导航日志目录")
                        return
                    self.main_window.nav_helper = NavigationLogHelper(nav_root)
                    helper = self.main_window.nav_helper
                
                helper.build_index(force=False)
                picked = helper.pick_best_file_for_dt(target_dt)
                if not picked:
                    QMessageBox.warning(self, "错误", "未找到合适的日志文件")
                    return
                
                picked_path = picked.path if hasattr(picked, "path") else picked
                text, hit_idx, hit_ts, all_lines = helper.extract_context(
                    picked_path, target_dt, before_n, after_m
                )
                
                hint = f"自定义时间戳：{self.main_window._fmt_dt_ms(target_dt)} | 实际命中：{self.main_window._fmt_dt_ms(hit_ts) if hit_ts else 'N/A'}"
                self.set_log_content(text, str(picked_path), hint, all_lines)
                
            elif self.log_type == "biz":
                # 中台日志
                helper = self.main_window.biz_helper
                if helper is None:
                    biz_root = self.main_window.get_biz_root_dir()
                    if not biz_root:
                        QMessageBox.warning(self, "错误", "未找到中台日志目录")
                        return
                    self.main_window.biz_helper = BizLogHelper(biz_root)
                    helper = self.main_window.biz_helper
                
                helper.build_index(force=False)
                picked = helper.pick_best_file_for_dt(target_dt)
                if not picked:
                    QMessageBox.warning(self, "错误", "未找到合适的日志文件")
                    return
                
                text, hit_idx, hit_ts, all_lines = helper.extract_context(
                    picked.path, target_dt, before_n, after_m
                )
                
                hint = f"自定义时间戳：{self.main_window._fmt_dt_ms(target_dt)} | 实际命中：{self.main_window._fmt_dt_ms(hit_ts) if hit_ts else 'N/A'}"
                self.set_log_content(text, picked.path, hint, all_lines)
                
            elif self.log_type == "pressure":
                # 压测日志 - 使用新的搜索方法
                QMessageBox.information(self, "提示", "请使用上方的'时间戳定位'功能进行时间戳搜索")
                return
            
            QMessageBox.information(self, "成功", "日志已重新加载")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载失败：{str(e)}")
        finally:
            QApplication.restoreOverrideCursor()

START_RE = re.compile(r"开始回充压测，最大尝试次数\s*:\s*(\d+)")
ROUND_RE = re.compile(r"经过第(?P<round>\d+)轮测试,\s*数据统计如下")
RATE_RE = re.compile(r"(?P<n>[123])次成功率\s*\|\s*(?P<rate>\d+(?:\.\d+)?)")
BEGIN_TEST_RE = re.compile(r"Begin a new recharge test")
DOCK50_RE = re.compile(r"Docking state from navigation:\s*50")
DOCK_STATE_RE = re.compile(r"Docking state from navigation:\s*(\d+)")
DOCK_FAIL_RE = re.compile(r"Docking fail,\s*fail count:\s*(\d+)")
TIMEOUT_RE = re.compile(r"Recharge time out, changing to IDLE,change fail count to 3")
BIZ_FAIL_RE = re.compile(r"\bfail(?:ed|ure)?\b", re.IGNORECASE)   # 只算真正的 fail/failed/failure
BIZ_KEY_RE  = re.compile(
    r"\b(error|warn|warning|interrupt|fail(?:ed|ure)?)\b|"
    r"Docking Start|Docking Stop|\bstop docking\b|"
    r"\bonLostLocation\b|send slam idle|"
    r"preDockCheck|won't dock because of lift up|\blift up\b",
    re.IGNORECASE
)

# 新增：中台日志相关正则
BIZ_DOCKING_START_RE = re.compile(r"Docking Start", re.IGNORECASE)
BIZ_SEND_DOCK_ORDER_RE = re.compile(r"send dock order.*param\s+\{\"count\":\s*(\d+)\}", re.IGNORECASE)  # 提取count
BIZ_DOCKING_START_COUNT_RE = re.compile(r'"count"\s*:\s*(\d+)', re.IGNORECASE)  # 用于提取 count 参数
BIZ_DOCKING_SUCCESS_RE = re.compile(r"Docking Success", re.IGNORECASE)
BIZ_DOCKING_FAILED_RE = re.compile(r"Docking Failed", re.IGNORECASE)
BIZ_DOCKING_STOP_RE = re.compile(r"Docking Stop", re.IGNORECASE)
BIZ_DOCK_STATUS_1_RE = re.compile(r"dock status is 1", re.IGNORECASE)
BIZ_RECV_DOCK_STATUS_1_RE = re.compile(r"recv dock status 1", re.IGNORECASE)  # 新增：匹配 recv dock status 1
BIZ_DOCK_ERROR_RE = re.compile(r"dock error (\d+)", re.IGNORECASE)
BIZ_RECV_DOCK_RESP_RE = re.compile(r"recv dock resp (\d+)", re.IGNORECASE)

def parse_ts(line: str) -> Optional[datetime]:
    m = TS_RE.match(line)
    if not m:
        return None
    try:
        return datetime.strptime(m.group("ts"), "%Y-%m-%d %H:%M:%S,%f")
    except Exception:
        return None

@dataclass
class FinalStats:
    round_no: int
    rate1: Optional[float]
    rate2: Optional[float]
    rate3: Optional[float]

@dataclass
class AttemptRecord:
    """记录每次回充尝试的详细信息"""
    attempt_no: int  # 第几次尝试（从count字段获取）
    start_ts: Optional[datetime]  # Docking Start 时间戳
    end_ts: Optional[datetime]  # 结束时间戳（Success/Failed/Stop）
    result: str  # "success", "failed", "stopped"
    error_code: Optional[int] = None  # 错误码（失败时）
    dock_status_1_seen: bool = False  # 是否看到过 dock status 1（充上电）
    is_slip: bool = False  # 是否为溜坡（充上电后又失败）

@dataclass
class TaskRecord:
    """记录一个完整的回充任务"""
    task_id: int  # 任务ID
    start_ts: Optional[datetime]  # 任务开始时间
    end_ts: Optional[datetime]  # 任务结束时间
    attempts: List[AttemptRecord]  # 所有尝试记录
    final_result: str  # "success", "failed", "stopped"
    success_at_attempt: Optional[int] = None  # 第几次尝试成功（1/2/3），失败则为None
    slip_count: int = 0  # 溜坡次数

@dataclass
class FailureRecord:
    test_index: int
    start_line: int
    end_line: int
    first_ts: Optional[datetime]

    max_fail_count: int
    max_fail_ts: Optional[datetime]
    reason: str
    reason_seq: str

    dock50_count: int
    dock34_count: int

    state_by_count: Dict[int, Optional[int]]
    state_ts_by_count: Dict[int, Optional[datetime]]
    timeout_ts_by_count: Dict[int, Optional[datetime]]

    recharge_state_ts: Optional[datetime] = None  # Change to RECHARGE state 的时间戳

    biz_reason: Optional[str] = None      # 比如：定位失败/MCU失败/导航失败/中台未知
    biz_file: Optional[str] = None        # 命中的 log.?
    biz_fail_lines_5min: Optional[str] = None  # 5分钟内fail行（可选存前几行，避免太大）
    
    # 新增：每次尝试的详细记录
    attempts: List[AttemptRecord] = None  # 该次测试的所有尝试记录
    
    # 新增：溜坡统计
    slip_count: int = 0  # 溜坡次数

class LogLocator:
    @staticmethod
    def extract_tar(tar_path: str) -> str:
        tar_path = os.path.abspath(tar_path)
        base = os.path.basename(tar_path).replace(".tar.gz", "")
        out_root = os.path.join(tempfile.gettempdir(), "pressure_tool_extract")
        os.makedirs(out_root, exist_ok=True)

        out_dir = os.path.join(out_root, "{}_{}".format(base, datetime.now().strftime("%Y%m%d_%H%M%S")))
        os.makedirs(out_dir, exist_ok=True)

        with tarfile.open(tar_path, "r:gz") as tf:
            tf.extractall(out_dir)
        return out_dir

    @staticmethod
    def find_test_charge_log(extract_dir: str) -> Optional[str]:
        extract_dir = os.path.abspath(extract_dir)

        candidates = list(Path(extract_dir).glob("**/data/log/navigation/navigation/test_charge.log"))
        if candidates:
            return str(candidates[0])

        for p in Path(extract_dir).rglob("test_charge.log"):
            return str(p)

        return None

class PressureParser:
    def __init__(self, log_path: str):
        self.log_path = log_path

    def _iter_lines(self):
        with open(self.log_path, "r", encoding="utf-8", errors="ignore") as f:
            for idx, line in enumerate(f):
                yield idx, line.rstrip("\n")

    def find_latest_start(self) -> Tuple[Optional[int], Optional[datetime]]:
        latest_dt = None
        latest_idx = None
        for idx, line in self._iter_lines():
            if "开始回充压测" not in line:
                continue
            if not START_RE.search(line):
                continue
            dt = parse_ts(line)
            if dt is None:
                continue
            if latest_dt is None or dt > latest_dt:
                latest_dt = dt
                latest_idx = idx
        return latest_idx, latest_dt

    def parse_final_stats(self, start_idx: int) -> Optional[FinalStats]:
        last_round = None
        last_round_line = None

        lines_cache: List[Tuple[int, str]] = []
        for idx, line in self._iter_lines():
            if idx < start_idx:
                continue
            lines_cache.append((idx, line))
            m = ROUND_RE.search(line)
            if m:
                last_round = int(m.group("round"))
                last_round_line = idx

        if last_round is None or last_round_line is None:
            return None

        rate1 = None
        rate2 = None
        rate3 = None

        in_range = False
        for idx, line in lines_cache:
            if idx < last_round_line:
                continue
            if "成功率统计如下" in line:
                in_range = True
                continue
            if in_range:
                m = RATE_RE.search(line)
                if m:
                    n = int(m.group("n"))
                    val = float(m.group("rate"))
                    if n == 1:
                        rate1 = val
                    elif n == 2:
                        rate2 = val
                    elif n == 3:
                        rate3 = val

        return FinalStats(round_no=last_round, rate1=rate1, rate2=rate2, rate3=rate3)

class FailureAnalyzer:
    LOOKAHEAD = 6
    FAIL_STATES = {50, 34, 18}

    @staticmethod
    def _reason_from_state_code(state: Optional[int]) -> str:
        if state == 50:
            return "盲走失败"
        if state == 34:
            return "识别失败"
        if state == 18:
            return "两点导航失败"
        return "未知"

    def __init__(self, parser: PressureParser, biz_helper: Optional[BizLogHelper] = None):
        self.parser = parser
        self.biz_helper = biz_helper

    def _analyze_biz_log_for_test(self, test_start_ts: datetime, test_end_ts: datetime) -> Tuple[List[AttemptRecord], int]:
        """
        分析中台日志，统计该次测试的每次尝试成功率和溜坡次数
        
        Returns:
            (attempts, slip_count): 尝试记录列表和溜坡次数
        """
        if not self.biz_helper or not test_start_ts:
            print(f"[DEBUG] biz_helper={self.biz_helper is not None}, test_start_ts={test_start_ts}")
            return [], 0
        
        attempts: List[AttemptRecord] = []
        slip_count = 0
        
        try:
            # 获取测试时间段内的中台日志文件
            picked = self.biz_helper.pick_best_file_for_dt(test_start_ts)
            if not picked:
                print(f"[DEBUG] 未找到中台日志文件 for {test_start_ts}")
                return [], 0
            
            print(f"[DEBUG] 选中中台日志文件: {picked.path}")
            print(f"[DEBUG] 文件时间范围: {picked.start_dt} ~ {picked.end_dt}")
            
            # 提取窗口时间段的日志（大幅扩大时间窗口以确保覆盖）
            time_span_minutes = max(30, int((test_end_ts - test_start_ts).total_seconds() / 60) + 20)
            print(f"[DEBUG] 提取时间窗口: {test_start_ts} ~ (+{time_span_minutes}分钟)")
            
            window_lines = self.biz_helper.extract_window_lines(
                picked.path, test_start_ts, 
                minutes=time_span_minutes
            )
            
            print(f"[DEBUG] 共提取 {len(window_lines)} 行日志")
            
            # ====== 状态追踪 ======
            recent_dock_status_1_ts: Optional[datetime] = None
            current_attempt_no = 0
            waiting_for_count = False
            pending_start_ts: Optional[datetime] = None
            
            for line_idx, line in enumerate(window_lines):
                dt = parse_any_ts(line)
                
                # 检测 Docking Start
                if BIZ_DOCKING_START_RE.search(line):
                    waiting_for_count = True
                    pending_start_ts = dt
                    print(f"[DEBUG] 检测到 Docking Start at line {line_idx}, ts={dt}, 等待 count 参数...")
                    continue
                
                # 如果在等待 count 参数，尝试从当前行提取
                if waiting_for_count:
                    m_count = BIZ_DOCKING_START_COUNT_RE.search(line)
                    if m_count:
                        current_attempt_no = int(m_count.group(1))
                        waiting_for_count = False
                        
                        attempt = AttemptRecord(
                            attempt_no=current_attempt_no,
                            start_ts=pending_start_ts or dt,
                            end_ts=None,
                            result="pending",
                            error_code=None,
                            dock_status_1_seen=False,
                            is_slip=False
                        )
                        attempts.append(attempt)
                        print(f"[DEBUG] ✓ 创建尝试 #{current_attempt_no} at line {line_idx}, ts={pending_start_ts}")
                        
                        # 检查是否在同一行或下一行就有 dock status 1
                        if recent_dock_status_1_ts and pending_start_ts:
                            if (recent_dock_status_1_ts >= pending_start_ts and 
                                (dt - recent_dock_status_1_ts).total_seconds() < 60):
                                attempt.dock_status_1_seen = True
                                print(f"[DEBUG]   继承之前的 dock status 1")
                    else:
                        # 如果接下来几行都没有 count，超时则放弃等待
                        if line_idx > 0 and dt and pending_start_ts:
                            if (dt - pending_start_ts).total_seconds() > 5:
                                waiting_for_count = False
                                print(f"[DEBUG] ✗ 等待 count 超时，放弃")
                    continue
                
                # 检测 dock status 1（充上电）- 两种格式
                if BIZ_DOCK_STATUS_1_RE.search(line) or BIZ_RECV_DOCK_STATUS_1_RE.search(line):
                    recent_dock_status_1_ts = dt
                    print(f"[DEBUG] ✓✓✓ 检测到 dock status 1 at line {line_idx}, ts={dt}")
                    
                    # 更新当前尝试的状态
                    if attempts and attempts[-1].result == "pending":
                        attempts[-1].dock_status_1_seen = True
                        print(f"[DEBUG]   标记尝试 #{attempts[-1].attempt_no} 已充过电")
                    continue
                
                # 检测 Docking Success
                if BIZ_DOCKING_SUCCESS_RE.search(line):
                    print(f"[DEBUG] ✅✅✅ 检测到 Docking Success at line {line_idx}, ts={dt}")
                    
                    if attempts and attempts[-1].result == "pending":
                        attempts[-1].end_ts = dt
                        attempts[-1].result = "success"
                    
                    recent_dock_status_1_ts = None
                    continue
                
                # 检测 Docking Failed
                if BIZ_DOCKING_FAILED_RE.search(line):
                    print(f"[DEBUG] ❌❌❌ 检测到 Docking Failed at line {line_idx}, ts={dt}")
                    print(f"[DEBUG]   recent_dock_status_1_ts={recent_dock_status_1_ts}")
                    
                    is_slip = (recent_dock_status_1_ts is not None)
                    
                    if is_slip:
                        slip_count += 1
                        print(f"[DEBUG] 🛷🛷🛷🛷🛷 检测到溜坡! 充电时间={recent_dock_status_1_ts}, 失败时间={dt}")
                        print(f"[DEBUG]   时间差={(dt - recent_dock_status_1_ts).total_seconds():.1f}秒")
                    
                    if attempts and attempts[-1].result == "pending":
                        attempts[-1].end_ts = dt
                        attempts[-1].result = "failed"
                        attempts[-1].is_slip = is_slip
                        
                        # 提取错误码
                        m_error = BIZ_DOCK_ERROR_RE.search(line)
                        if m_error:
                            attempts[-1].error_code = int(m_error.group(1))
                            print(f"[DEBUG]   错误码: {attempts[-1].error_code}")
                    else:
                        anon_attempt = AttemptRecord(
                            attempt_no=current_attempt_no if current_attempt_no > 0 else 0,
                            start_ts=recent_dock_status_1_ts or dt,
                            end_ts=dt,
                            result="failed",
                            error_code=None,
                            dock_status_1_seen=(recent_dock_status_1_ts is not None),
                            is_slip=is_slip
                        )
                        
                        m_error = BIZ_DOCK_ERROR_RE.search(line)
                        if m_error:
                            anon_attempt.error_code = int(m_error.group(1))
                        
                        attempts.append(anon_attempt)
                        print(f"[DEBUG] 创建匿名失败记录")
                    
                    recent_dock_status_1_ts = None
                    continue
                
                # 检测 Docking Stop
                if BIZ_DOCKING_STOP_RE.search(line):
                    print(f"[DEBUG] ⏹⏹⏹ 检测到 Docking Stop at line {line_idx}, ts={dt}")
                    
                    is_slip = (recent_dock_status_1_ts is not None)
                    
                    if is_slip:
                        slip_count += 1
                        print(f"[DEBUG] 🛷🛷🛷 检测到溜坡(Stop)! 充电时间={recent_dock_status_1_ts}, 停止时间={dt}")
                    
                    if attempts and attempts[-1].result == "pending":
                        attempts[-1].end_ts = dt
                        attempts[-1].result = "stopped"
                        attempts[-1].is_slip = is_slip
                    else:
                        anon_attempt = AttemptRecord(
                            attempt_no=current_attempt_no if current_attempt_no > 0 else 0,
                            start_ts=recent_dock_status_1_ts or dt,
                            end_ts=dt,
                            result="stopped",
                            error_code=None,
                            dock_status_1_seen=(recent_dock_status_1_ts is not None),
                            is_slip=is_slip
                        )
                        attempts.append(anon_attempt)
                    
                    recent_dock_status_1_ts = None
                    continue
            
            # 清理未完成的尝试
            for attempt in attempts:
                if attempt.result == "pending":
                    attempt.result = "unknown"
        
        except Exception as e:
            print(f"[ERROR] 分析中台日志失败: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"[DEBUG] ===== 中台日志分析完成 =====")
        print(f"[DEBUG] 总尝试数: {len(attempts)}")
        print(f"[DEBUG] 溜坡次数: {slip_count}")
        for i, att in enumerate(attempts):
            slip_mark = " 🛷" if att.is_slip else ""
            print(f"[DEBUG]   尝试#{att.attempt_no}: {att.result} (充过电={att.dock_status_1_seen}){slip_mark}")
        
        return attempts, slip_count

    def analyze_all_slips_in_biz_log(self, biz_helper=None) -> List[Dict]:
        """
        直接扫描整个中台日志文件，找出所有溜坡案例，不依赖测试段划分
        
        Args:
            biz_helper: BizLogHelper 实例，用于获取日志文件列表
            
        Returns:
            溜坡案例列表，每个案例包含详细信息
        """
        slips = []
        
        if not biz_helper:
            print(f"[WARN] 未提供 biz_helper，无法扫描中台日志")
            return slips
        
        try:
            # 确保索引已建立
            if not biz_helper._indexed:
                biz_helper.build_index()
            
            print(f"[INFO] ===== 开始全量扫描中台日志寻找溜坡 =====")
            print(f"[INFO] 共找到 {len(biz_helper._files)} 个日志文件")
            
            # 遍历所有日志文件
            for file_info in biz_helper._files:
                if not file_info.path or not os.path.exists(file_info.path):
                    continue
                
                print(f"[INFO] 扫描文件: {file_info.path}")
                print(f"[INFO]   时间范围: {file_info.start_dt} ~ {file_info.end_dt}")
                
                recent_dock_status_1_ts: Optional[datetime] = None
                recent_dock_status_1_line: Optional[int] = None
                current_docking_start_ts: Optional[datetime] = None
                current_docking_start_line: Optional[int] = None
                current_count: Optional[int] = None
                
                with open(file_info.path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_idx, line in enumerate(f, 1):
                        dt = parse_any_ts(line)
                        if dt is None:
                            continue
                        
                        # 检测 Docking Start
                        if BIZ_DOCKING_START_RE.search(line):
                            current_docking_start_ts = dt
                            current_docking_start_line = line_idx
                            
                            # 尝试提取 count
                            count_match = re.search(r'"count"\s*:\s*(\d+)', line)
                            if count_match:
                                current_count = int(count_match.group(1))
                            else:
                                current_count = None
                            
                            print(f"[SLIP_SCAN] Line {line_idx}: Docking Start at {dt}, count={current_count}")
                            continue
                        
                        # 检测 dock status 1
                        if BIZ_DOCK_STATUS_1_RE.search(line):
                            recent_dock_status_1_ts = dt
                            recent_dock_status_1_line = line_idx
                            print(f"[SLIP_SCAN] Line {line_idx}: dock status 1 at {dt}")
                            continue
                        
                        # 检测 Docking Failed
                        if BIZ_DOCKING_FAILED_RE.search(line):
                            if recent_dock_status_1_ts is not None:
                                # 发现溜坡！
                                time_diff = (dt - recent_dock_status_1_ts).total_seconds()
                                
                                slip_info = {
                                    'file': file_info.path,
                                    'line_idx': line_idx,
                                    'timestamp': dt,
                                    'docking_start_line': current_docking_start_line,
                                    'docking_start_ts': current_docking_start_ts,
                                    'charge_line': recent_dock_status_1_line,
                                    'charge_ts': recent_dock_status_1_ts,
                                    'fail_line': line_idx,
                                    'fail_ts': dt,
                                    'time_to_charge': (recent_dock_status_1_ts - current_docking_start_ts).total_seconds() if current_docking_start_ts else None,
                                    'time_to_fail': time_diff,
                                    'count': current_count
                                }
                                
                                slips.append(slip_info)
                                print(f"[SLIP_SCAN] 🛷🛷🛷 发现溜坡 #{len(slips)}!")
                                print(f"[SLIP_SCAN]   文件: {file_info.path}")
                                print(f"[SLIP_SCAN]   Docking Start: Line {current_docking_start_line} at {current_docking_start_ts}")
                                print(f"[SLIP_SCAN]   Charge (status 1): Line {recent_dock_status_1_line} at {recent_dock_status_1_ts}")
                                print(f"[SLIP_SCAN]   Failed: Line {line_idx} at {dt}")
                                print(f"[SLIP_SCAN]   充电耗时: {slip_info['time_to_charge']:.1f}s, 保持充电: {time_diff:.1f}s")
                            
                            # 重置状态
                            recent_dock_status_1_ts = None
                            recent_dock_status_1_line = None
                            continue
                        
                        # 检测 Docking Success（重置状态）
                        if BIZ_DOCKING_SUCCESS_RE.search(line):
                            if recent_dock_status_1_ts is not None:
                                print(f"[SLIP_SCAN] Line {line_idx}: Docking Success (正常回充成功)")
                            recent_dock_status_1_ts = None
                            recent_dock_status_1_line = None
                            continue
        
        except Exception as e:
            print(f"[ERROR] 全量扫描中台日志失败: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"[INFO] ===== 全量扫描完成 =====")
        print(f"[INFO] 共发现 {len(slips)} 次溜坡")
        
        return slips

    def analyze_success_rate_from_biz_log(self, biz_helper=None, start_dt=None) -> Optional[FinalStats]:
        """
        重构版：基于中台日志统计成功率（完全重写，逻辑更清晰）

        核心逻辑：
        1. 以 count=1 的 Docking Start 作为任务开始
        2. 追踪每次尝试（count=1/2/3）
        3. 任务结束条件：Success / Stop / count=3的Failed
        4. 统计成功率和溜坡

        Args:
            biz_helper: BizLogHelper 实例
            start_dt: 压测开始时间，只分析此时间之后的日志
        """
        if not biz_helper:
            print("[WARN] biz_helper 为空，无法统计成功率")
            return None

        print(f"\n{'='*80}")
        print(f"📊 开始基于中台日志统计成功率（重构版v2）...")
        if start_dt:
            print(f"⏰ 过滤时间：只分析 {start_dt} 之后的日志")
        print(f"{'='*80}")

        all_tasks: List[TaskRecord] = []
        current_task: Optional[TaskRecord] = None
        current_attempt: Optional[AttemptRecord] = None
        recent_dock_status_1_ts: Optional[datetime] = None
        task_id_counter = 0

        try:
            # 遍历所有中台日志文件
            for file_info in biz_helper._files:
                if not file_info.path or not os.path.exists(file_info.path):
                    continue

                print(f"[SCAN] 扫描文件: {file_info.path}")

                with open(file_info.path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_idx, line in enumerate(f, 1):
                        dt = parse_any_ts(line)
                        if dt is None:
                            continue

                        # 时间过滤：只处理 start_dt 之后的日志
                        if start_dt and dt < start_dt:
                            continue

                        # 检测 Docking Start（标记任务可能开始，但需要等待send dock order来确认count）
                        if BIZ_DOCKING_START_RE.search(line):
                            # 只是标记，不立即创建任务，等待send dock order
                            print(f"[SCAN] 检测到 Docking Start at {dt}")
                            continue

                        # 检测 send dock order（提取count参数，创建任务/尝试）
                        m_send_dock = BIZ_SEND_DOCK_ORDER_RE.search(line)
                        if m_send_dock:
                            count = int(m_send_dock.group(1))
                            print(f"[SCAN] send dock order, count={count}")

                            # count=1 表示新任务开始
                            if count == 1:
                                # 如果有未完成的任务，先结束它（标记为失败）
                                if current_task and current_task.final_result == "pending":
                                    current_task.final_result = "failed"
                                    current_task.end_ts = dt
                                    all_tasks.append(current_task)
                                    print(f"[SCAN]   任务#{current_task.task_id} 未正常结束，标记为失败")

                                # 创建新任务
                                task_id_counter += 1
                                current_task = TaskRecord(
                                    task_id=task_id_counter,
                                    start_ts=dt,
                                    end_ts=None,
                                    attempts=[],
                                    final_result="pending",
                                    success_at_attempt=None,
                                    slip_count=0
                                )
                                recent_dock_status_1_ts = None
                                print(f"[SCAN] 任务#{task_id_counter} 开始")

                            # 创建新的尝试记录
                            if current_task:
                                current_attempt = AttemptRecord(
                                    attempt_no=count,
                                    start_ts=dt,
                                    end_ts=None,
                                    result="pending",
                                    error_code=None,
                                    dock_status_1_seen=False,
                                    is_slip=False
                                )
                                current_task.attempts.append(current_attempt)
                                print(f"[SCAN]   尝试#{count} 开始")

                            continue

                        # 检测 dock status 1（充上电）
                        if BIZ_DOCK_STATUS_1_RE.search(line) or BIZ_RECV_DOCK_STATUS_1_RE.search(line):
                            recent_dock_status_1_ts = dt
                            if current_attempt:
                                current_attempt.dock_status_1_seen = True
                                print(f"[SCAN]   充上电")
                            continue

                        # 检测 Docking Success
                        if BIZ_DOCKING_SUCCESS_RE.search(line):
                            if current_task and current_attempt:
                                current_attempt.end_ts = dt
                                current_attempt.result = "success"
                                current_task.end_ts = dt
                                current_task.final_result = "success"
                                current_task.success_at_attempt = current_attempt.attempt_no
                                all_tasks.append(current_task)
                                print(f"[SCAN] ✅ 任务#{current_task.task_id} 成功（第{current_attempt.attempt_no}次）")
                                current_task = None
                                current_attempt = None
                                recent_dock_status_1_ts = None
                            continue

                        # 检测 Docking Failed
                        if BIZ_DOCKING_FAILED_RE.search(line):
                            if current_attempt:
                                m_error = BIZ_DOCK_ERROR_RE.search(line)
                                current_attempt.error_code = int(m_error.group(1)) if m_error else None
                                current_attempt.end_ts = dt
                                current_attempt.result = "failed"

                                # 检查是否溜坡
                                if recent_dock_status_1_ts:
                                    current_attempt.is_slip = True
                                    if current_task:
                                        current_task.slip_count += 1
                                    print(f"[SCAN]   🛷 溜坡！")
                                    recent_dock_status_1_ts = None

                                print(f"[SCAN]   ❌ 尝试#{current_attempt.attempt_no} 失败")

                                # 如果是第3次失败，任务结束
                                if current_attempt.attempt_no >= 3 and current_task:
                                    current_task.end_ts = dt
                                    current_task.final_result = "failed"
                                    all_tasks.append(current_task)
                                    print(f"[SCAN] ❌ 任务#{current_task.task_id} 失败（3次均失败）")
                                    current_task = None
                                    current_attempt = None
                            continue

                        # 检测 Docking Stop
                        if BIZ_DOCKING_STOP_RE.search(line):
                            if current_task and current_attempt:
                                current_attempt.end_ts = dt
                                current_attempt.result = "stopped"
                                current_task.end_ts = dt
                                current_task.final_result = "stopped"
                                all_tasks.append(current_task)
                                print(f"[SCAN] ⏹ 任务#{current_task.task_id} 停止")
                                current_task = None
                                current_attempt = None
                                recent_dock_status_1_ts = None
                            continue

            # 处理最后未完成的任务
            if current_task and current_task.final_result == "pending":
                current_task.final_result = "failed"
                all_tasks.append(current_task)

        except Exception as e:
            print(f"[ERROR] 统计失败: {e}")
            import traceback
            traceback.print_exc()
            return None

        # 统计成功率
        total = len(all_tasks)
        if total == 0:
            print("[WARN] 未找到任何任务")
            return None

        success_1st = len([t for t in all_tasks if t.success_at_attempt == 1])
        success_2nd = len([t for t in all_tasks if t.success_at_attempt == 2])
        success_3rd = len([t for t in all_tasks if t.success_at_attempt == 3])
        total_slips = sum(t.slip_count for t in all_tasks)

        rate1 = (success_1st / total * 100)
        rate2 = ((success_1st + success_2nd) / total * 100)
        rate3 = ((success_1st + success_2nd + success_3rd) / total * 100)

        print(f"\n{'='*80}")
        print(f"📊 统计结果")
        print(f"{'='*80}")
        print(f"总任务数: {total}")
        print(f"第1次成功: {success_1st} 个 → 1次成功率: {rate1:.2f}%")
        print(f"第2次成功: {success_2nd} 个 → 2次成功率: {rate2:.2f}%")
        print(f"第3次成功: {success_3rd} 个 → 3次成功率: {rate3:.2f}%")
        print(f"🛷 总溜坡次数: {total_slips}")
        print(f"{'='*80}\n")

        return FinalStats(round_no=0, rate1=round(rate1, 2), rate2=round(rate2, 2), rate3=round(rate3, 2))

    def analyze_all_tasks_from_biz_log(self, biz_helper=None, start_dt=None) -> List[FailureRecord]:
        """
        重构版：基于中台日志分析所有回充任务，生成失败列表

        策略：复用 analyze_success_rate_from_biz_log 的逻辑，获取所有任务后筛选失败的

        Args:
            biz_helper: BizLogHelper 实例
            start_dt: 压测开始时间，只分析此时间之后的日志
        """
        if not biz_helper:
            print("[WARN] biz_helper 为空，无法分析中台日志")
            return []

        print(f"\n{'='*80}")
        print(f"🔍 开始基于中台日志分析所有回充任务（重构版）...")
        if start_dt:
            print(f"⏰ 过滤时间：只分析 {start_dt} 之后的日志")
        print(f"{'='*80}")

        all_tasks: List[TaskRecord] = []
        current_task: Optional[TaskRecord] = None
        current_attempt: Optional[AttemptRecord] = None
        recent_dock_status_1_ts: Optional[datetime] = None
        task_id_counter = 0

        try:
            # 遍历所有中台日志文件
            for file_info in biz_helper._files:
                if not file_info.path or not os.path.exists(file_info.path):
                    continue

                print(f"[TASK_SCAN] 扫描文件: {file_info.path}")

                with open(file_info.path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_idx, line in enumerate(f, 1):
                        dt = parse_any_ts(line)
                        if dt is None:
                            continue

                        # 时间过滤：只处理 start_dt 之后的日志
                        if start_dt and dt < start_dt:
                            continue

                        # 检测 send dock order（提取count参数）
                        m_send_dock = BIZ_SEND_DOCK_ORDER_RE.search(line)
                        if m_send_dock:
                            count = int(m_send_dock.group(1))

                            # count=1 表示新任务开始
                            if count == 1:
                                if current_task and current_task.final_result == "pending":
                                    current_task.final_result = "failed"
                                    current_task.end_ts = dt
                                    all_tasks.append(current_task)

                                task_id_counter += 1
                                current_task = TaskRecord(
                                    task_id=task_id_counter,
                                    start_ts=dt,
                                    end_ts=None,
                                    attempts=[],
                                    final_result="pending",
                                    success_at_attempt=None,
                                    slip_count=0
                                )
                                recent_dock_status_1_ts = None

                            if current_task:
                                current_attempt = AttemptRecord(
                                    attempt_no=count,
                                    start_ts=dt,
                                    end_ts=None,
                                    result="pending",
                                    error_code=None,
                                    dock_status_1_seen=False,
                                    is_slip=False
                                )
                                current_task.attempts.append(current_attempt)
                            continue

                        # 检测 dock status 1
                        if BIZ_DOCK_STATUS_1_RE.search(line) or BIZ_RECV_DOCK_STATUS_1_RE.search(line):
                            recent_dock_status_1_ts = dt
                            if current_attempt:
                                current_attempt.dock_status_1_seen = True
                            continue

                        # 检测 Docking Success
                        if BIZ_DOCKING_SUCCESS_RE.search(line):
                            if current_task and current_attempt:
                                current_attempt.end_ts = dt
                                current_attempt.result = "success"
                                current_task.end_ts = dt
                                current_task.final_result = "success"
                                current_task.success_at_attempt = current_attempt.attempt_no
                                all_tasks.append(current_task)
                                current_task = None
                                current_attempt = None
                                recent_dock_status_1_ts = None
                            continue

                        # 检测 Docking Failed
                        if BIZ_DOCKING_FAILED_RE.search(line):
                            if current_attempt:
                                m_error = BIZ_DOCK_ERROR_RE.search(line)
                                current_attempt.error_code = int(m_error.group(1)) if m_error else None
                                current_attempt.end_ts = dt
                                current_attempt.result = "failed"

                                if recent_dock_status_1_ts:
                                    current_attempt.is_slip = True
                                    if current_task:
                                        current_task.slip_count += 1
                                    recent_dock_status_1_ts = None

                                if current_attempt.attempt_no >= 3 and current_task:
                                    current_task.end_ts = dt
                                    current_task.final_result = "failed"
                                    all_tasks.append(current_task)
                                    current_task = None
                                    current_attempt = None
                            continue

                        # 检测 Docking Stop
                        if BIZ_DOCKING_STOP_RE.search(line):
                            if current_task and current_attempt:
                                current_attempt.end_ts = dt
                                current_attempt.result = "stopped"
                                current_task.end_ts = dt
                                current_task.final_result = "stopped"
                                all_tasks.append(current_task)
                                current_task = None
                                current_attempt = None
                                recent_dock_status_1_ts = None
                            continue

            # 处理最后未完成的任务
            if current_task and current_task.final_result == "pending":
                current_task.final_result = "failed"
                all_tasks.append(current_task)

        except Exception as e:
            print(f"[ERROR] 分析失败: {e}")
            import traceback
            traceback.print_exc()
            return []

        # 筛选失败的任务并转换为 FailureRecord
        failures: List[FailureRecord] = []
        for task in all_tasks:
            if task.final_result in ("failed", "stopped"):
                failure_rec = self._convert_task_to_failure_record(task)
                failures.append(failure_rec)

        print(f"\n{'='*80}")
        print(f"✅ 分析完成")
        print(f"总任务数: {len(all_tasks)}")
        print(f"失败任务数: {len(failures)}")
        print(f"{'='*80}\n")

        return failures

    def _convert_task_to_failure_record(self, task: TaskRecord) -> FailureRecord:
        """将 TaskRecord 转换为 FailureRecord（保持兼容性）"""
        # 确定失败原因（基于每次尝试的结果）
        if task.final_result == "stopped":
            reason = "Docking Stop"
            reason_seq = "STOP"
        else:
            # 构建详细的失败原因
            attempt_reasons = []
            for attempt in task.attempts:
                if attempt.result == "failed":
                    if attempt.error_code:
                        attempt_reasons.append(f"第{attempt.attempt_no}次:错误码{attempt.error_code}")
                    else:
                        attempt_reasons.append(f"第{attempt.attempt_no}次:失败")
                elif attempt.result == "stopped":
                    attempt_reasons.append(f"第{attempt.attempt_no}次:停止")

            reason = " | ".join(attempt_reasons) if attempt_reasons else f"{len(task.attempts)}次尝试均失败"
            reason_seq = "FAILx" + str(len(task.attempts))

        # 提取错误码序列
        error_codes = []
        for attempt in task.attempts:
            if attempt.error_code:
                error_codes.append(str(attempt.error_code))
            elif attempt.result == "failed":
                error_codes.append("?")

        if error_codes:
            reason_seq += "(" + ",".join(error_codes) + ")"

        # 构建 state_by_count（兼容旧格式，存储错误码）
        state_by_count = {}
        state_ts_by_count = {}
        for attempt in task.attempts:
            if attempt.result == "failed":
                # 使用错误码作为state，如果没有错误码则使用50
                state_by_count[attempt.attempt_no] = attempt.error_code if attempt.error_code else 50
                state_ts_by_count[attempt.attempt_no] = attempt.end_ts

        return FailureRecord(
            test_index=task.task_id,
            start_line=0,
            end_line=0,
            first_ts=task.start_ts,
            max_fail_count=len(task.attempts),
            max_fail_ts=task.end_ts,
            reason=reason,
            reason_seq=reason_seq,
            dock50_count=len([a for a in task.attempts if a.result == "failed"]),
            dock34_count=0,
            state_by_count=state_by_count,
            state_ts_by_count=state_ts_by_count,
            timeout_ts_by_count={},
            recharge_state_ts=task.start_ts,
            biz_reason=reason,  # 使用详细的失败原因
            biz_file=None,
            biz_fail_lines_5min=None,
            attempts=task.attempts,
            slip_count=task.slip_count
        )

    def analyze(self, start_idx: int) -> List[FailureRecord]:
        failures: List[FailureRecord] = []

        in_seg = False
        test_index = 0

        seg_start = 0
        seg_end = 0
        seg_first_ts: Optional[datetime] = None
        seg_last_ts: Optional[datetime] = None  # 记录测试结束时间戳

        last_fail_state: Optional[int] = None
        last_fail_state_ts: Optional[datetime] = None

        recharge_state_ts: Optional[datetime] = None

        dock50_count = 0
        dock34_count = 0

        reason_by_count: Dict[int, str] = {}
        state_by_count: Dict[int, Optional[int]] = {}
        state_ts_by_count: Dict[int, Optional[datetime]] = {}
        timeout_ts_by_count: Dict[int, Optional[datetime]] = {}
        max_fail_count = 0

        pending: Optional[Dict[str, Any]] = None  # {"count":int, "line":int}

        def commit_fail(count: int, state: Optional[int], state_dt: Optional[datetime], line_idx: int):
            nonlocal max_fail_count, pending
            reason_by_count[count] = self._reason_from_state_code(state)
            state_by_count[count] = state
            state_ts_by_count[count] = state_dt
            if count > max_fail_count:
                max_fail_count = count
            pending = {"count": count, "line": line_idx}

        def overwrite_pending_with_state(state: Optional[int], state_dt: Optional[datetime]):
            nonlocal pending
            if not pending:
                return
            c = pending["count"]
            reason_by_count[c] = self._reason_from_state_code(state)
            state_by_count[c] = state
            state_ts_by_count[c] = state_dt
            pending = None

        def commit_timeout_as_fail3(timeout_dt: Optional[datetime]):
            nonlocal max_fail_count, pending
            pending = None
            if 3 not in reason_by_count:
                reason_by_count[3] = "未知"
                state_by_count[3] = None
                state_ts_by_count[3] = None
                timeout_ts_by_count[3] = timeout_dt
                if 3 > max_fail_count:
                    max_fail_count = 3

        def finalize_segment():
            nonlocal in_seg, pending
            if not in_seg:
                return

            pending = None
            
            # ====== 关键修改：无论是否失败，都分析中台日志 ======
            print(f"[DEBUG] ========== 测试段 #{test_index} 结束 ==========")
            print(f"[DEBUG] 行范围: {seg_start} ~ {seg_end}")
            print(f"[DEBUG] 时间范围: {seg_first_ts} ~ {seg_last_ts}")
            print(f"[DEBUG] max_fail_count: {max_fail_count}")
            print(f"[DEBUG] dock50_count: {dock50_count}, dock34_count: {dock34_count}")
            print(f"[DEBUG] state_by_count: {state_by_count}")

            # 分析中台日志，获取每次尝试的详细记录和溜坡统计
            attempts = []
            slip_count = 0
            if seg_first_ts and seg_last_ts:
                print(f"[DEBUG] 开始分析中台日志...")
                print(f"[DEBUG]   将搜索时间范围: {seg_first_ts} ~ {seg_last_ts}")
                attempts, slip_count = self._analyze_biz_log_for_test(seg_first_ts, seg_last_ts)
                print(f"[DEBUG] Test #{test_index}: 检测到 {slip_count} 次溜坡, {len(attempts)} 次尝试")
                
                # 如果有溜坡，详细打印
                if slip_count > 0:
                    print(f"[DEBUG] 🎯🎯🎯 发现溜坡！测试段 #{test_index}")
                    for att in attempts:
                        if att.is_slip:
                            print(f"[DEBUG]   - 尝试#{att.attempt_no}: 充过电={att.dock_status_1_seen}, 结果={att.result}")
            
            if max_fail_count >= 3:
                parts: List[str] = []
                for n in range(1, max_fail_count + 1):
                    parts.append(f"{n}次{reason_by_count.get(n, '未知')}")
                reason_seq = "，".join(parts)

                final_reason = reason_by_count.get(max_fail_count, "未知")
                if final_reason == "未知":
                    for n in range(max_fail_count, 0, -1):
                        r = reason_by_count.get(n, "未知")
                        if r != "未知":
                            final_reason = r
                            break

                # 如果是"纯timeout合成3 + 没有任何state码"，给一个更明确的提示
                has_any_state = any((state_by_count.get(k) is not None) for k in (1, 2, 3))
                if (timeout_ts_by_count.get(3) is not None) and (not has_any_state) and recharge_state_ts:
                    final_reason = "回充超时(无错误码，需查中台biz日志)"

                max_ts = state_ts_by_count.get(max_fail_count)
                if not max_ts:
                    max_ts = timeout_ts_by_count.get(max_fail_count)

                failures.append(FailureRecord(
                    test_index=test_index,
                    start_line=seg_start,
                    end_line=seg_end,
                    first_ts=seg_first_ts,

                    max_fail_count=max_fail_count,
                    max_fail_ts=max_ts,
                    reason=final_reason,
                    reason_seq=reason_seq,

                    dock50_count=dock50_count,
                    dock34_count=dock34_count,

                    state_by_count=dict(state_by_count),
                    state_ts_by_count=dict(state_ts_by_count),
                    timeout_ts_by_count=dict(timeout_ts_by_count),

                    recharge_state_ts=recharge_state_ts,
                    
                    attempts=attempts,
                    slip_count=slip_count,
                ))
                
                print(f"[DEBUG] >>> 已添加失败记录到列表，溜坡数={slip_count}")
            else:
                print(f"[DEBUG] >>> 该测试段 max_fail_count={max_fail_count} < 3，未添加到失败列表（但已分析中台日志）")
                if slip_count > 0:
                    print(f"[DEBUG] ⚠️  警告：该段有 {slip_count} 次溜坡但未计入失败列表！")

            in_seg = False

        for idx, line in self.parser._iter_lines():
            if idx < start_idx:
                continue

            dt = parse_ts(line)

            if BEGIN_TEST_RE.search(line):
                finalize_segment()

                in_seg = True
                test_index += 1
                seg_start = idx
                seg_end = idx
                seg_first_ts = dt
                seg_last_ts = dt  # 初始化结束时间

                last_fail_state = None
                last_fail_state_ts = None
                recharge_state_ts = None

                dock50_count = 0
                dock34_count = 0

                reason_by_count = {}
                state_by_count = {}
                state_ts_by_count = {}
                timeout_ts_by_count = {}
                max_fail_count = 0
                pending = None
                continue

            if not in_seg:
                continue

            seg_end = idx
            if dt:
                seg_last_ts = dt  # 更新最后时间戳

            # 记录 Change to RECHARGE state 时间戳
            if "Change to RECHARGE state" in line:
                recharge_state_ts = dt

            # state 行（只用失败态更新 last_fail_state，并且只允许失败态覆盖 pending）
            ms = DOCK_STATE_RE.search(line)
            if ms:
                state = int(ms.group(1))
                if state in self.FAIL_STATES:
                    last_fail_state = state
                    last_fail_state_ts = dt

                    if state == 50:
                        dock50_count += 1
                    elif state == 34:
                        dock34_count += 1

                    if pending and (idx - pending["line"] <= self.LOOKAHEAD):
                        overwrite_pending_with_state(state, dt)
                    else:
                        pending = None
                else:
                    if pending and (idx - pending["line"] > self.LOOKAHEAD):
                        pending = None
                continue

            # fail count 行
            mf = DOCK_FAIL_RE.search(line)
            if mf:
                pending = None

                c = int(mf.group(1))
                commit_fail(count=c, state=last_fail_state, state_dt=last_fail_state_ts, line_idx=idx)
                continue

            # timeout 合成 3
            if TIMEOUT_RE.search(line):
                commit_timeout_as_fail3(timeout_dt=dt)
                continue

        finalize_segment()
        return failures

class AnalyzeWorker(QThread):
    progress = pyqtSignal(str)
    done = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(self, tar_path: str, thresholds: Dict[str, str]):
        super().__init__()
        self.tar_path = tar_path
        self.thresholds = thresholds

    def run(self):
        try:
            self.progress.emit("1) 解压中 ...")
            extract_dir = LogLocator.extract_tar(self.tar_path)

            self.progress.emit("2) 定位 test_charge.log ...")
            log_path = LogLocator.find_test_charge_log(extract_dir)
            if not log_path:
                raise RuntimeError("未找到 test_charge.log（固定路径与递归搜索均失败）")

            self.progress.emit(f"找到日志：{log_path}")
            parser = PressureParser(log_path)

            self.progress.emit("3) 查找最新一次压测起点 ...")
            start_idx, start_dt = parser.find_latest_start()
            if start_idx is None:
                raise RuntimeError("未找到“开始回充压测，最大尝试次数”作为起点")

            self.progress.emit(f"最新压测起点：第 {start_idx} 行，时间 {start_dt}")

            self.progress.emit("4) 解析最终统计 ...")
            final_stats = parser.parse_final_stats(start_idx)
            if not final_stats:
                raise RuntimeError("未解析到最终统计（未找到“经过第xx轮测试”段）")

            t1 = float(self.thresholds["rate1"])
            t2 = float(self.thresholds["rate2"])
            t3 = float(self.thresholds["rate3"])
            pass_ok = (
                final_stats.rate1 is not None and final_stats.rate2 is not None and final_stats.rate3 is not None
                and final_stats.rate1 >= t1 and final_stats.rate2 >= t2 and final_stats.rate3 >= t3
            )

            self.progress.emit("5) 分析中台日志...")

            # 先查找并初始化中台日志 helper
            biz_dir = None
            biz_helper = None
            for p in Path(extract_dir).glob("**/data/log/biz"):
                biz_dir = str(p)
                break

            if not biz_dir:
                raise RuntimeError("未找到中台日志目录：**/data/log/biz")

            self.progress.emit("5.1) 初始化中台日志助手...")
            biz_helper = BizLogHelper(biz_dir)
            biz_helper.build_index(force=False)

            # 创建分析器（只传入biz_helper，不需要parser）
            analyzer = FailureAnalyzer(parser, biz_helper)

            # 基于中台日志统计成功率（从压测开始时间之后）
            self.progress.emit("5.2) 基于中台日志统计成功率...")
            final_stats = analyzer.analyze_success_rate_from_biz_log(biz_helper=biz_helper, start_dt=start_dt)

            if not final_stats:
                raise RuntimeError("中台日志成功率统计失败")

            # 计算是否通过
            t1 = float(self.thresholds["rate1"])
            t2 = float(self.thresholds["rate2"])
            t3 = float(self.thresholds["rate3"])
            pass_ok = (
                final_stats.rate1 is not None and final_stats.rate2 is not None and final_stats.rate3 is not None
                and final_stats.rate1 >= t1 and final_stats.rate2 >= t2 and final_stats.rate3 >= t3
            )

            # 基于中台日志分析失败任务（从压测开始时间之后）
            self.progress.emit("5.3) 基于中台日志分析失败任务...")
            failures = analyzer.analyze_all_tasks_from_biz_log(biz_helper=biz_helper, start_dt=start_dt)

            self.progress.emit(f"分析完成：成功率={final_stats.rate1}/{final_stats.rate2}/{final_stats.rate3}%, 失败任务={len(failures)}个")
            self.done.emit({
                "extract_dir": extract_dir,
                "log_path": log_path,
                "start_idx": start_idx,
                "start_dt": start_dt,
                "final_stats": final_stats,
                "pass_ok": pass_ok,
                "failures": failures,
            })
        except Exception as e:
            self.failed.emit(str(e))

class FailLineHighlighter(QSyntaxHighlighter):
    """
    把包含 fail 的整行染红（大小写不敏感）。
    你给的例子 relocate failed / onRelocateFailed 都会命中。
    """
    def __init__(self, document):
        super().__init__(document)

        self.fmt_fail = QTextCharFormat()
        self.fmt_fail.setForeground(QColor("red"))
        self.fmt_fail.setFontWeight(QFont.Bold)

        # 整行匹配：只要这一行出现 fail（不区分大小写），整行染红
        self.re_fail_line = QRegularExpression(r"^.*fail.*$", QRegularExpression.CaseInsensitiveOption)

    def highlightBlock(self, text: str):
        if self.re_fail_line.match(text).hasMatch():
            self.setFormat(0, len(text), self.fmt_fail)

class LogHighlighter(QSyntaxHighlighter):
    """
    行级高亮优先级：ERROR > INTERRUPT > WARNING/WARN > FAIL
    另外对关键短语做背景色高亮（不抢前景色）。
    """
    def __init__(self, document):
        super().__init__(document)

        self.fmt_error = QTextCharFormat()
        self.fmt_error.setForeground(QColor("#FF4500"))  # 橙红
        self.fmt_error.setFontWeight(QFont.Bold)

        self.fmt_interrupt = QTextCharFormat()
        self.fmt_interrupt.setForeground(QColor("#C2185B"))  # 紫红
        self.fmt_interrupt.setFontWeight(QFont.Bold)

        self.fmt_warn = QTextCharFormat()
        self.fmt_warn.setForeground(QColor("#FFA500"))  # 橙
        self.fmt_warn.setFontWeight(QFont.Bold)

        self.fmt_fail = QTextCharFormat()
        self.fmt_fail.setForeground(QColor("red"))
        self.fmt_fail.setFontWeight(QFont.Bold)

        # 背景高亮（用于关键短语）
        self.fmt_kw = QTextCharFormat()
        self.fmt_kw.setBackground(QColor("#FFF59D"))  # 淡黄
        self.fmt_kw.setFontWeight(QFont.Bold)

        self.re_error = QRegularExpression(r"^.*\bERROR\b.*$", QRegularExpression.CaseInsensitiveOption)
        self.re_interrupt = QRegularExpression(r"^.*\bInterrupt\b.*$", QRegularExpression.CaseInsensitiveOption)
        self.re_warn  = QRegularExpression(r"^.*\b(WARN|WARNING)\b.*$", QRegularExpression.CaseInsensitiveOption)
        self.re_fail  = QRegularExpression(r"^.*fail.*$", QRegularExpression.CaseInsensitiveOption)

        self.keyword_patterns = [
            QRegularExpression(r"Change to RECHARGE state", QRegularExpression.CaseInsensitiveOption),
            QRegularExpression(r"Docking Start", QRegularExpression.CaseInsensitiveOption),
            QRegularExpression(r"Docking Stop", QRegularExpression.CaseInsensitiveOption),
            QRegularExpression(r"\bstop docking\b", QRegularExpression.CaseInsensitiveOption),
            QRegularExpression(r"\bInterrupt\b", QRegularExpression.CaseInsensitiveOption),
            QRegularExpression(r"\bonLostLocation\b", QRegularExpression.CaseInsensitiveOption),
            QRegularExpression(r"send slam idle", QRegularExpression.CaseInsensitiveOption),
            QRegularExpression(r"preDockCheck", QRegularExpression.CaseInsensitiveOption),
            QRegularExpression(r"won't dock because of lift up", QRegularExpression.CaseInsensitiveOption),
            QRegularExpression(r"\blift up\b", QRegularExpression.CaseInsensitiveOption),
        ]

    def highlightBlock(self, text: str):
        # 行级：先决定整行前景色（优先级）
        if self.re_error.match(text).hasMatch():
            self.setFormat(0, len(text), self.fmt_error)
        elif self.re_interrupt.match(text).hasMatch():
            self.setFormat(0, len(text), self.fmt_interrupt)
        elif self.re_warn.match(text).hasMatch():
            self.setFormat(0, len(text), self.fmt_warn)
        elif self.re_fail.match(text).hasMatch():
            self.setFormat(0, len(text), self.fmt_fail)

        # 关键词：再叠加背景色高亮
        for re_kw in self.keyword_patterns:
            it = re_kw.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), self.fmt_kw)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("回充压测结果自动分析工具 (PyQt5)")
        self.resize(1100, 750)

        self.tar_path = None
        self.last_result = None
        self.worker = None

        self.extract_root = None
        self.nav_helper: Optional[NavigationLogHelper] = None
        self.biz_helper: Optional[BizLogHelper] = None

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # 顶部工具栏
        top = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("选择 log_*.tar.gz ...")
        btn_choose = QPushButton("选择压缩包")
        btn_analyze = QPushButton("开始分析")
        btn_view_pressure = QPushButton("📄 查看压测日志")
        btn_choose.clicked.connect(self.on_choose)
        btn_analyze.clicked.connect(self.on_analyze)
        btn_view_pressure.clicked.connect(self.on_view_pressure_log)
        top.addWidget(QLabel("压缩包："))
        top.addWidget(self.path_edit, 1)
        top.addWidget(btn_choose)
        top.addWidget(btn_analyze)
        top.addWidget(btn_view_pressure)
        main_layout.addLayout(top)

        th_box = QGroupBox("通过标准（可改）")
        th_form = QFormLayout(th_box)
        self.th1 = QLineEdit("95")
        self.th2 = QLineEdit("99")
        self.th3 = QLineEdit("99")
        th_form.addRow("1次成功率 ≥", self.th1)
        th_form.addRow("2次成功率 ≥", self.th2)
        th_form.addRow("3次成功率 ≥", self.th3)
        main_layout.addWidget(th_box)

        splitter = QSplitter(Qt.Horizontal)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        self.summary = QTextEdit()
        self.summary.setReadOnly(True)
        left_layout.addWidget(QLabel("分析过程 / 摘要："))
        left_layout.addWidget(self.summary, 1)

        right = QWidget()
        right_layout = QVBoxLayout(right)

        self.failure_list = QListWidget()
        right_layout.addWidget(QLabel("失败列表（基于中台日志，显示每次尝试的错误码）："))
        right_layout.addWidget(self.failure_list, 1)

        # ====== 播包时间戳面板 ======
        self.ts_group = QGroupBox("播包时间戳（Docking state 行时间戳，可直接复制）")
        ts_grid = QGridLayout(self.ts_group)

        ts_grid.addWidget(QLabel("次数"), 0, 0)
        ts_grid.addWidget(QLabel("错误码(state)"), 0, 1)
        ts_grid.addWidget(QLabel("时间戳"), 0, 2)
        ts_grid.addWidget(QLabel("操作"), 0, 3)

        self.ts_code_labels = {}
        self.ts_edits = {}
        self.ts_copy_btns = {}
        self.ts_nav_btns = {}
        self.ts_biz_btns = {}

        for i, n in enumerate([1, 2, 3], start=1):
            ts_grid.addWidget(QLabel(f"第{n}次"), i, 0)

            code_lb = QLabel("-")
            code_lb.setTextInteractionFlags(Qt.TextSelectableByMouse)
            self.ts_code_labels[n] = code_lb
            ts_grid.addWidget(code_lb, i, 1)

            edit = QLineEdit()
            edit.setReadOnly(True)
            self.ts_edits[n] = edit
            ts_grid.addWidget(edit, i, 2)

            btn_copy = QPushButton("复制")
            btn_copy.clicked.connect(lambda _, k=n: self.copy_small_fail_ts(k))
            self.ts_copy_btns[n] = btn_copy

            btn_nav = QPushButton("导航日志")
            btn_nav.clicked.connect(lambda _, k=n: self.show_nav_log_for_small_fail(k))
            btn_nav.setMaximumWidth(90)
            self.ts_nav_btns[n] = btn_nav

            btn_box = QHBoxLayout()
            w = QWidget()
            w.setLayout(btn_box)
            btn_box.setContentsMargins(0, 0, 0, 0)
            btn_box.addWidget(btn_copy)
            btn_box.addWidget(btn_nav)

            ts_grid.addWidget(w, i, 3)
        
        row = 4
        ts_grid.addWidget(QLabel("RECHARGE"), row, 0)
        self.recharge_code_lb = QLabel("Change to RECHARGE state")
        self.recharge_code_lb.setTextInteractionFlags(Qt.TextSelectableByMouse)
        ts_grid.addWidget(self.recharge_code_lb, row, 1)

        self.recharge_edit = QLineEdit()
        self.recharge_edit.setReadOnly(True)
        ts_grid.addWidget(self.recharge_edit, row, 2)

        self.btn_show_biz_ts = QPushButton("中台日志")
        self.btn_show_biz_ts.clicked.connect(self.show_biz_log_for_current_failure)
        ts_grid.addWidget(self.btn_show_biz_ts, row, 3)

        # timeout
        row = 5
        ts_grid.addWidget(QLabel("Timeout"), row, 0)
        self.timeout_code_lb = QLabel("timeout")
        self.timeout_code_lb.setTextInteractionFlags(Qt.TextSelectableByMouse)
        ts_grid.addWidget(self.timeout_code_lb, row, 1)

        self.timeout_edit = QLineEdit()
        self.timeout_edit.setReadOnly(True)
        ts_grid.addWidget(self.timeout_edit, row, 2)

        self.btn_copy_timeout = QPushButton("复制")
        self.btn_copy_timeout.clicked.connect(self.copy_timeout_ts)
        ts_grid.addWidget(self.btn_copy_timeout, row, 3)

        # max_ts
        row = 6
        ts_grid.addWidget(QLabel("max_ts"), row, 0)
        self.max_code_lb = QLabel("-")
        self.max_code_lb.setTextInteractionFlags(Qt.TextSelectableByMouse)
        ts_grid.addWidget(self.max_code_lb, row, 1)

        self.max_ts_edit = QLineEdit()
        self.max_ts_edit.setReadOnly(True)
        ts_grid.addWidget(self.max_ts_edit, row, 2)

        self.btn_copy_max = QPushButton("复制")
        self.btn_copy_max.clicked.connect(self.copy_max_ts)
        ts_grid.addWidget(self.btn_copy_max, row, 3)

        # copy all
        row = 7
        self.btn_copy_all = QPushButton("复制全部(1/2/3/timeout/max)")
        self.btn_copy_all.clicked.connect(self.copy_all_ts)
        ts_grid.addWidget(self.btn_copy_all, row, 2, 1, 2)

        right_layout.addWidget(self.ts_group)
        
        # ====== 新增：溜坡统计和尝试详情面板 ======
        self.attempt_group = QGroupBox("🛷 溜坡统计 & 尝试详情（基于中台日志分析）")
        attempt_vbox = QVBoxLayout(self.attempt_group)
        
        # 溜坡统计
        self.slip_label = QLabel("溜坡次数: 0")
        self.slip_label.setStyleSheet("font-weight: bold; color: #FF6F00; font-size: 14px;")
        attempt_vbox.addWidget(self.slip_label)
        
        # 尝试详情表格
        self.attempt_table = QTextEdit()
        self.attempt_table.setReadOnly(True)
        self.attempt_table.setFont(QFont("Monospace", 9))
        self.attempt_table.setMaximumHeight(200)
        attempt_vbox.addWidget(QLabel("每次尝试详情:"))
        attempt_vbox.addWidget(self.attempt_table)
        
        right_layout.addWidget(self.attempt_group)

        btns = QHBoxLayout()
        self.btn_play = QPushButton("播包（对选中失败）")
        self.btn_play.clicked.connect(self.on_play)
        btns.addWidget(self.btn_play)
        btns.addStretch(1)
        right_layout.addLayout(btns)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter, 3)

        self.failure_list.currentItemChanged.connect(self.on_failure_item_changed)

        # ====== 底部：日志片段面板（可切换：导航/中台）======
        self.detail_group = QGroupBox("日志片段（可切换：导航 / 中台biz）")
        detail_vbox = QVBoxLayout(self.detail_group)

        # 切换按钮行（左右切换）+ 弹出窗口按钮
        switch_row = QHBoxLayout()
        self.btn_show_nav = QPushButton("← 导航日志")
        self.btn_show_biz = QPushButton("中台日志 →")
        self.btn_show_nav.clicked.connect(lambda: self.switch_detail_panel("nav"))
        self.btn_show_biz.clicked.connect(lambda: self.switch_detail_panel("biz"))
        switch_row.addWidget(self.btn_show_nav)
        switch_row.addWidget(self.btn_show_biz)
        
        switch_row.addStretch(1)
        
        # 新增：弹出窗口按钮
        btn_popup = QPushButton("📋 弹出独立窗口")
        btn_popup.setToolTip("在独立大窗口中查看当前日志")
        btn_popup.clicked.connect(self.show_log_in_popup)
        switch_row.addWidget(btn_popup)
        
        detail_vbox.addLayout(switch_row)

        # 公共控制：前N/后M（两种日志共用）
        ctrl_row = QHBoxLayout()
        ctrl_row.addWidget(QLabel("前N行"))
        self.spin_before = QSpinBox()
        self.spin_before.setRange(0, 2000)
        self.spin_before.setValue(100)
        ctrl_row.addWidget(self.spin_before)

        ctrl_row.addWidget(QLabel("后M行"))
        self.spin_after = QSpinBox()
        self.spin_after.setRange(0, 2000)
        self.spin_after.setValue(10)
        ctrl_row.addWidget(self.spin_after)

        ctrl_row.addStretch(1)
        detail_vbox.addLayout(ctrl_row)

        self.detail_stack = QStackedWidget()
        detail_vbox.addWidget(self.detail_stack, 1)

        # --- page 1: nav ---
        self.nav_page = QWidget()
        nav_vbox = QVBoxLayout(self.nav_page)

        self.nav_hint_label = QLabel("")
        self.nav_hint_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        nav_vbox.addWidget(self.nav_hint_label)

        nav_path_row = QHBoxLayout()
        nav_path_row.addWidget(QLabel("导航命中文件:"))
        self.nav_path_edit = QLineEdit()
        self.nav_path_edit.setReadOnly(True)
        nav_path_row.addWidget(self.nav_path_edit)
        nav_vbox.addLayout(nav_path_row)

        # 新增：导航日志时间戳输入行
        nav_ts_row = QHBoxLayout()
        nav_ts_row.addWidget(QLabel("自定义时间戳:"))
        self.nav_custom_ts_edit = QLineEdit()
        self.nav_custom_ts_edit.setPlaceholderText("YYYY-MM-DD HH:MM:SS,mmm")
        nav_ts_row.addWidget(self.nav_custom_ts_edit, 1)
        
        btn_nav_load = QPushButton("加载日志")
        btn_nav_load.clicked.connect(self.on_load_nav_log_by_ts)
        nav_ts_row.addWidget(btn_nav_load)
        nav_vbox.addLayout(nav_ts_row)

        self.nav_text = QTextEdit()
        self.nav_text.setReadOnly(True)
        font = QFont("Monospace")
        font.setStyleHint(QFont.TypeWriter)
        self.nav_text.setFont(font)
        nav_vbox.addWidget(self.nav_text, 1)
        self.nav_highlighter = LogHighlighter(self.nav_text.document())
        # self.biz_fail_highlighter = FailLineHighlighter(self.biz_text.document())

        # --- page 2: biz ---
        self.biz_page = QWidget()
        biz_vbox = QVBoxLayout(self.biz_page)

        self.biz_hint_label = QLabel("")
        self.biz_hint_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        biz_vbox.addWidget(self.biz_hint_label)

        biz_path_row = QHBoxLayout()
        biz_path_row.addWidget(QLabel("中台命中文件:"))
        self.biz_path_edit = QLineEdit()
        self.biz_path_edit.setReadOnly(True)
        biz_path_row.addWidget(self.biz_path_edit)
        biz_vbox.addLayout(biz_path_row)

        # 新增：中台日志时间戳输入行
        biz_ts_row = QHBoxLayout()
        biz_ts_row.addWidget(QLabel("自定义时间戳:"))
        self.biz_custom_ts_edit = QLineEdit()
        self.biz_custom_ts_edit.setPlaceholderText("YYYY-MM-DD HH:MM:SS,mmm")
        biz_ts_row.addWidget(self.biz_custom_ts_edit, 1)
        
        btn_biz_load = QPushButton("加载日志")
        btn_biz_load.clicked.connect(self.on_load_biz_log_by_ts)
        biz_ts_row.addWidget(btn_biz_load)
        biz_vbox.addLayout(biz_ts_row)

        self.biz_text = QTextEdit()
        self.biz_text.setReadOnly(True)
        self.biz_text.setFont(font)
        biz_vbox.addWidget(self.biz_text, 1)
        self.biz_highlighter = LogHighlighter(self.biz_text.document())

        self.detail_stack.addWidget(self.nav_page)
        self.detail_stack.addWidget(self.biz_page)

        # 默认显示导航页
        self.switch_detail_panel("nav")

        # 高度
        self.detail_group.setMinimumHeight(450)
        self.nav_text.setMinimumHeight(380)
        self.biz_text.setMinimumHeight(380)

        main_layout.addWidget(self.detail_group, 2)

        self.statusBar().showMessage("就绪")

    # ---------- 基础工具 ----------

    def log(self, s: str):
        self.summary.append(s)

    def _fmt_dt_ms(self, d: Optional[datetime]) -> str:
        if not d:
            return ""
        return d.strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]

    def _copy_text(self, s: str):
        QApplication.clipboard().setText(s or "")

    def _clear_ts_panel(self):
        for n in (1, 2, 3):
            self.ts_code_labels[n].setText("-")
            self.ts_edits[n].setText("")
        self.timeout_edit.setText("")
        self.max_ts_edit.setText("")
        self.max_code_lb.setText("-")
        self.recharge_edit.setText("")

    def _set_ts_action_buttons_enabled(self, enabled: bool):
        for d in (self.ts_copy_btns, self.ts_nav_btns, self.ts_biz_btns):
            for b in d.values():
                b.setEnabled(enabled)
        self.btn_copy_timeout.setEnabled(enabled)
        self.btn_copy_max.setEnabled(enabled)
        self.btn_copy_all.setEnabled(enabled)

    def switch_detail_panel(self, which: str):
        if which == "nav":
            self.detail_stack.setCurrentWidget(self.nav_page)
            self.btn_show_nav.setEnabled(False)
            self.btn_show_biz.setEnabled(True)
        else:
            self.detail_stack.setCurrentWidget(self.biz_page)
            self.btn_show_nav.setEnabled(True)
            self.btn_show_biz.setEnabled(False)

    def show_log_in_popup(self):
        """在独立弹窗中显示当前日志"""
        # 判断当前显示的是哪个面板
        current_widget = self.detail_stack.currentWidget()
        
        if current_widget == self.nav_page:
            log_type = "nav"
            title = "导航日志 - 独立查看窗口"
            text_content = self.nav_text.toPlainText()
            file_path = self.nav_path_edit.text()
            hint = self.nav_hint_label.text()
            # 注意：主窗口的 nav_text 没有保存 all_lines，所以弹窗中搜索功能受限
            # 如果需要完整搜索，建议重新从文件加载
        elif current_widget == self.biz_page:
            log_type = "biz"
            title = "中台biz日志 - 独立查看窗口"
            text_content = self.biz_text.toPlainText()
            file_path = self.biz_path_edit.text()
            hint = self.biz_hint_label.text()
            # 同样，biz_text 也没有保存 all_lines
        else:
            QMessageBox.warning(self, "提示", "当前没有可显示的日志内容")
            return
        
        if not text_content or text_content.strip() == "":
            QMessageBox.information(self, "提示", "当前日志内容为空，请先加载日志")
            return
        
        # 创建并显示独立窗口
        dialog = LogViewerDialog(self, title=title, log_type=log_type)
        dialog.set_log_content(text_content, file_path, hint)
        
        # 同步前N/后M设置
        dialog.spin_before.setValue(self.spin_before.value())
        dialog.spin_after.setValue(self.spin_after.value())
        
        # 提示用户关于搜索功能的限制
        if log_type in ("nav", "biz"):
            dialog.search_result_label.setText("⚠️ 注意：从主窗口弹出的日志可能不支持完整搜索功能，建议使用时间戳输入框重新加载")
        
        dialog.exec_()

    def on_choose(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择压缩包", "", "tar.gz (*.tar.gz);;All (*.*)")
        if path:
            self.tar_path = path
            self.path_edit.setText(path)

    def on_view_pressure_log(self):
        """查看压测日志（test_charge.log）"""
        tar_path = self.path_edit.text().strip()
        if not tar_path or not os.path.exists(tar_path):
            QMessageBox.warning(self, "提示", "请先选择有效的 .tar.gz 文件")
            return
        
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            
            # 1. 解压文件（如果还没解压过）
            if not hasattr(self, 'extract_root') or not self.extract_root:
                self.statusBar().showMessage("正在解压...", 3000)
                QApplication.processEvents()
                self.extract_root = LogLocator.extract_tar(tar_path)
            
            # 2. 定位 test_charge.log
            self.statusBar().showMessage("正在定位压测日志...", 3000)
            QApplication.processEvents()
            log_path = LogLocator.find_test_charge_log(self.extract_root)
            
            if not log_path:
                QMessageBox.warning(self, "错误", "未找到 test_charge.log 文件")
                return
            
            # 3. 读取日志内容
            self.statusBar().showMessage("正在读取日志内容...", 3000)
            QApplication.processEvents()
            
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                all_lines = f.readlines()
            
            # 保存完整行列表用于搜索
            all_lines_stripped = [line.rstrip('\n') for line in all_lines]
            content = "\n".join(all_lines_stripped)
            
            # 4. 统计信息
            line_count = len(all_lines_stripped)
            file_size_mb = os.path.getsize(log_path) / (1024 * 1024)
            
            hint = f"压测日志 | 总行数: {line_count} | 文件大小: {file_size_mb:.2f} MB"
            
            # 5. 在独立窗口中显示
            dialog = LogViewerDialog(self, title="压测日志 (test_charge.log)", log_type="pressure")
            dialog.set_log_content(content, log_path, hint, all_lines_stripped)
            dialog.spin_before.setValue(100)  # 默认值
            dialog.spin_after.setValue(10)
            
            QApplication.restoreOverrideCursor()
            dialog.exec_()
            
        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, "错误", f"查看压测日志失败：{str(e)}")
            import traceback
            traceback.print_exc()

    def on_analyze(self):
        tar_path = self.path_edit.text().strip()
        if not tar_path or not os.path.exists(tar_path):
            QMessageBox.warning(self, "提示", "请先选择有效的 .tar.gz 文件")
            return

        self.summary.clear()
        self.failure_list.clear()
        self.last_result = None
        self._clear_ts_panel()
        self.nav_text.clear()
        self.biz_text.clear()
        self.nav_hint_label.setText("")
        self.biz_hint_label.setText("")
        self.nav_path_edit.clear()
        self.biz_path_edit.clear()

        thresholds = {"rate1": self.th1.text().strip(),
                      "rate2": self.th2.text().strip(),
                      "rate3": self.th3.text().strip()}

        self.worker = AnalyzeWorker(tar_path, thresholds)
        self.worker.progress.connect(self.log)
        self.worker.failed.connect(self.on_failed)
        self.worker.done.connect(self.on_done)
        self.worker.start()

    def on_failed(self, msg: str):
        QMessageBox.critical(self, "分析失败", msg)
        self.log(f"[ERROR] {msg}")

    def _find_dir_under_extract(self, pattern: str) -> Optional[str]:
        """
        pattern 示例：'**/data/log/navigation/navigation' 或 '**/data/log/biz'
        """
        root = getattr(self, "extract_root", None)
        if not root:
            return None
        candidates = list(Path(root).glob(pattern))
        if candidates:
            return str(candidates[0])
        return None

    def get_nav_root_dir(self) -> Optional[str]:
        return self._find_dir_under_extract("**/data/log/navigation/navigation")

    def get_biz_root_dir(self) -> Optional[str]:
        return self._find_dir_under_extract("**/data/log/biz")

    # ---------- 分析结果展示 ----------

    def on_done(self, result: Dict[str, Any]):
        self.last_result = result
        self.extract_root = result.get("extract_dir")

        nav_root = self.get_nav_root_dir()
        self.nav_helper = NavigationLogHelper(nav_root) if nav_root else None

        biz_root = self.get_biz_root_dir()
        self.biz_helper = BizLogHelper(biz_root) if biz_root else None

        fs: FinalStats = result["final_stats"]
        pass_ok = result["pass_ok"]

        self.log("\n=== 最终统计 ===")
        self.log(f"轮次：{fs.round_no}")
        self.log(f"1次成功率：{fs.rate1}")
        self.log(f"2次成功率：{fs.rate2}")
        self.log(f"3次成功率：{fs.rate3}")
        judge = "通过" if pass_ok else "不通过"
        color = "green" if pass_ok else "red"
        self.log(f"判定：<span style='color:{color}; font-weight:600'>{judge}</span>")

        btn = QMessageBox.question(
            self,
            "是否继续分析失败原因？",
            f"最终判定：{'通过' if pass_ok else '不通过'}\n是否继续分析失败原因并列出失败项？",
            QMessageBox.Yes | QMessageBox.No
        )
        if btn == QMessageBox.No:
            self.log("用户选择不继续失败原因分析。")
            self.append_final_summary(result, [])   # <= 加这一行
            return

        failures: List[FailureRecord] = result["failures"]

        self.log("\n=== 失败原因分析结果 ===")
        self.log(f"识别到失败条目数：{len(failures)}")
        
        # 调试：打印 slip_count 统计
        total_slips_debug = sum(getattr(f, 'slip_count', 0) for f in failures)
        slip_failures_debug = [f for f in failures if getattr(f, 'slip_count', 0) > 0]
        self.log(f"[DEBUG UI] 总溜坡次数: {total_slips_debug}")
        self.log(f"[DEBUG UI] 发生溜坡的测试数: {len(slip_failures_debug)}")
        if slip_failures_debug:
            for f in slip_failures_debug[:5]:  # 只显示前5个
                self.log(f"[DEBUG UI]   test#{f.test_index}: slip_count={f.slip_count}, attempts={len(f.attempts) if f.attempts else 0}")

        self.failure_list.clear()

        def fmt_dt(d):
            if not d:
                return "N/A"
            return d.strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]

        for f in failures:
            # 构建每次尝试的详细信息（基于中台日志）
            attempt_details = []
            if hasattr(f, 'attempts') and f.attempts:
                for attempt in f.attempts:
                    if attempt.result == "failed":
                        error_info = f"错误码{attempt.error_code}" if attempt.error_code else "未知错误"
                        slip_mark = "🛷" if attempt.is_slip else ""
                        attempt_details.append(f"第{attempt.attempt_no}次:{error_info}{slip_mark}")
                    elif attempt.result == "stopped":
                        attempt_details.append(f"第{attempt.attempt_no}次:停止")
                    elif attempt.result == "success":
                        attempt_details.append(f"第{attempt.attempt_no}次:成功")

            detail_str = " | ".join(attempt_details) if attempt_details else "无详情"

            recharge_ts = fmt_dt(getattr(f, "recharge_state_ts", None))

            # 溜坡统计
            slip_info = ""
            if hasattr(f, 'slip_count') and f.slip_count > 0:
                slip_info = f" | 🛷溜坡={f.slip_count}次"

            text = (f"[{f.reason}] test#{f.test_index} "
                    f"开始={fmt_dt(f.first_ts)} 结束={fmt_dt(f.max_fail_ts)} "
                    f"| {detail_str}{slip_info}")

            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, f)

            # 失败项红色
            item.setForeground(QBrush(QColor("red")))

            self.failure_list.addItem(item)
        
        self.append_final_summary(result, failures)

        if not failures:
            QMessageBox.information(self, "结果", "未识别到失败条目。")
    def append_final_summary(self, result: Dict[str, Any], failures: List[FailureRecord]):
        fs: FinalStats = result["final_stats"]
        pass_ok: bool = result["pass_ok"]

        t1 = self.th1.text().strip()
        t2 = self.th2.text().strip()
        t3 = self.th3.text().strip()

        judge = "通过" if pass_ok else "不通过"
        judge_color = "green" if pass_ok else "red"

        # 失败原因分布
        reason_list = [f.reason or "未知" for f in failures]
        counter = Counter(reason_list)
        
        # 新增：溜坡统计
        total_slip_count = sum(getattr(f, 'slip_count', 0) for f in failures)
        slip_failures = [f for f in failures if getattr(f, 'slip_count', 0) > 0]

        # 拼一个简短的 Top 列表（避免摘要太长）
        top_items = failures[:300]
        top_lines = []
        for f in top_items:
            recharge_ts = self._fmt_dt_ms(getattr(f, "recharge_state_ts", None))
            max_ts = self._fmt_dt_ms(getattr(f, "max_fail_ts", None))
            slip_info = f" | 溜坡={getattr(f, 'slip_count', 0)}" if getattr(f, 'slip_count', 0) > 0 else ""
            
            # 尝试详情
            attempt_info = ""
            if hasattr(f, 'attempts') and f.attempts:
                success_count = sum(1 for a in f.attempts if a.result == "success")
                failed_count = sum(1 for a in f.attempts if a.result == "failed")
                stopped_count = sum(1 for a in f.attempts if a.result == "stopped")
                attempt_info = f" | 尝试:{len(f.attempts)}次(S{success_count}/F{failed_count}/X{stopped_count})"
            
            top_lines.append(
                f"test#{f.test_index} | {f.reason} | max_ts={max_ts} | RECHARGE={recharge_ts}{attempt_info}{slip_info}"
            )

        # reasons html
        if counter:
            reasons_html = "<br>".join([f"{k}：{v}" for k, v in counter.most_common()])
        else:
            reasons_html = "无"
        
        # 溜坡统计 HTML
        slip_html = ""
        if total_slip_count > 0:
            slip_html = f"""
    <div style="margin-top:6px; font-weight:700; color:#FF6F00;">🛷 溜坡统计：</div>
    <div style="margin-left:10px;">总溜坡次数：<span style="color:red; font-weight:700;">{total_slip_count}</span></div>
    <div style="margin-left:10px;">发生溜坡的测试数：<span style="color:red; font-weight:700;">{len(slip_failures)}</span></div>
    """

        top_html = "<br>".join(top_lines) if top_lines else "无"

        html = f"""
    <hr>
    <div style="font-weight:700;">=== 总结 ===</div>
    <div>轮次：{fs.round_no}</div>
    <div>成功率：1次={fs.rate1}（阈值≥{t1}） / 2次={fs.rate2}（阈值≥{t2}） / 3次={fs.rate3}（阈值≥{t3}）</div>
    <div>判定：<span style="color:{judge_color}; font-weight:800;">{judge}</span></div>
    <div>失败条目数：<span style="color:red; font-weight:700;">{len(failures)}</span></div>
    {slip_html}
    <div style="margin-top:6px; font-weight:700;">失败原因分布：</div>
    <div style="margin-left:10px;">{reasons_html}</div>
    <div style="margin-top:6px; font-weight:700;">Top失败条目（最多300条）：</div>
    <div style="margin-left:10px; font-family:Monospace;">{top_html}</div>
    """
        self.log(html)

    def on_play(self):

        # 添加查看压测日志的按钮到摘要区域
        btn_pressure = QPushButton("📄 查看完整压测日志 (test_charge.log)")
        btn_pressure.clicked.connect(self.on_view_pressure_log)
        btn_pressure.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        # 创建一个容器来放置按钮
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.addWidget(btn_pressure)
        btn_layout.addStretch(1)
        btn_layout.setContentsMargins(10, 5, 10, 5)
        
        # 将按钮容器添加到 summary 中
        # 由于 QTextEdit 不能直接嵌入 widget，我们在后面单独处理
        # 这里改为在左侧面板底部添加按钮

        left = QWidget()
        left_layout = QVBoxLayout(left)
        self.summary = QTextEdit()
        self.summary.setReadOnly(True)
        left_layout.addWidget(QLabel("分析过程 / 摘要："))
        left_layout.addWidget(self.summary, 1)
        
        # 添加查看压测日志的按钮
        btn_pressure_log = QPushButton("📄 查看完整压测日志")
        btn_pressure_log.setToolTip("在独立窗口中查看 test_charge.log 完整内容")
        btn_pressure_log.clicked.connect(self.on_view_pressure_log)
        btn_pressure_log.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        left_layout.addWidget(btn_pressure_log)

    def on_play(self):
        item = self.failure_list.currentItem()
        if not item:
            QMessageBox.information(self, "提示", "请先在失败列表中选中一条")
            return

        f: FailureRecord = item.data(Qt.UserRole)
        ret = QMessageBox.question(
            self,
            "播包确认？",
            f"该条目：test#{f.test_index}\n需要播包确认原因。\n是否执行播包命令？\n\n"
            "cd ~/auto_studio/mower_log_analysis/\npython3 main.py",
            QMessageBox.Yes | QMessageBox.No
        )
        if ret != QMessageBox.Yes:
            return

        cmd = "cd ~/auto_studio/mower_log_analysis/ && python3 main.py"
        try:
            subprocess.Popen(["bash", "-lc", cmd])
            self.log(f"已执行播包命令：{cmd}")
        except Exception as e:
            QMessageBox.critical(self, "执行失败", str(e))

    # ---------- 时间戳面板 ----------

    def on_failure_item_changed(self, current, previous):
        if not current:
            self._clear_ts_panel()
            self._clear_attempt_panel()
            return
        rec: FailureRecord = current.data(Qt.UserRole)
        if not rec:
            self._clear_ts_panel()
            self._clear_attempt_panel()
            return

        for n in (1, 2, 3):
            st = rec.state_by_count.get(n, None)
            st_ts = rec.state_ts_by_count.get(n, None)
            if st_ts:
                self.ts_code_labels[n].setText(str(st) if st is not None else "?")
                self.ts_edits[n].setText(self._fmt_dt_ms(st_ts))
            else:
                self.ts_code_labels[n].setText("?")
                self.ts_edits[n].setText("")

        to_ts = rec.timeout_ts_by_count.get(3, None)
        self.timeout_edit.setText(self._fmt_dt_ms(to_ts))

        self.max_ts_edit.setText(self._fmt_dt_ms(getattr(rec, "max_fail_ts", None)))
        self.max_code_lb.setText(getattr(rec, "reason", "-") or "-")
        self.recharge_edit.setText(self._fmt_dt_ms(getattr(rec, "recharge_state_ts", None)))
        
        # 新增：显示溜坡统计和尝试详情
        self._update_attempt_panel(rec)
    
    def _clear_attempt_panel(self):
        """清空尝试详情面板"""
        self.slip_label.setText("溜坡次数: 0")
        self.attempt_table.clear()
    
    def _update_attempt_panel(self, rec: FailureRecord):
        """更新尝试详情面板"""
        # 显示溜坡次数
        slip_count = getattr(rec, 'slip_count', 0)
        if slip_count > 0:
            self.slip_label.setText(f"🛷 溜坡次数: {slip_count}")
            self.slip_label.setStyleSheet("font-weight: bold; color: red; font-size: 14px;")
        else:
            self.slip_label.setText("🛷 溜坡次数: 0")
            self.slip_label.setStyleSheet("font-weight: bold; color: #FF6F00; font-size: 14px;")
        
        # 显示每次尝试详情
        attempts = getattr(rec, 'attempts', None)
        if not attempts:
            self.attempt_table.setPlainText("暂无中台日志分析数据")
            return
        
        lines = []
        lines.append(f"{'序号':<6} {'结果':<10} {'错误码':<8} {'充上电':<8} {'溜坡':<6} {'开始时间'}")
        lines.append("-" * 80)
        
        for attempt in attempts:
            result_str = {
                "success": "✅成功",
                "failed": "❌失败",
                "stopped": "⏹停止",
                "pending": "⏳进行中",
                "unknown": "❓未知"
            }.get(attempt.result, attempt.result)
            
            error_code_str = str(attempt.error_code) if attempt.error_code is not None else "-"
            dock_status_str = "✓是" if attempt.dock_status_1_seen else "✗否"
            slip_str = "🛷是" if attempt.is_slip else "否"
            start_ts_str = self._fmt_dt_ms(attempt.start_ts) if attempt.start_ts else "N/A"
            
            lines.append(f"{attempt.attempt_no:<6} {result_str:<10} {error_code_str:<8} {dock_status_str:<8} {slip_str:<6} {start_ts_str}")
        
        # 统计信息
        success_count = sum(1 for a in attempts if a.result == "success")
        failed_count = sum(1 for a in attempts if a.result == "failed")
        stopped_count = sum(1 for a in attempts if a.result == "stopped")
        slip_attempts = sum(1 for a in attempts if a.is_slip)
        
        lines.append("-" * 80)
        lines.append(f"总计: {len(attempts)}次尝试 | 成功:{success_count} | 失败:{failed_count} | 停止:{stopped_count} | 溜坡:{slip_attempts}")
        
        self.attempt_table.setPlainText("\n".join(lines))

    def copy_small_fail_ts(self, n: int):
        self._copy_text(self.ts_edits[n].text())

    def copy_timeout_ts(self):
        self._copy_text(self.timeout_edit.text())

    def copy_max_ts(self):
        self._copy_text(self.max_ts_edit.text())

    def copy_all_ts(self):
        lines = []
        for n in (1, 2, 3):
            ts = self.ts_edits[n].text().strip()
            code = self.ts_code_labels[n].text().strip()
            lines.append(f"{n}:{ts if ts else 'N/A'} (state={code})")
        to_ts = self.timeout_edit.text().strip()
        if to_ts:
            lines.append(f"timeout:{to_ts}")
        max_ts = self.max_ts_edit.text().strip()
        if max_ts:
            lines.append(f"max_ts:{max_ts} ({self.max_code_lb.text().strip()})")
        self._copy_text("\n".join(lines))

    # ---------- 导航日志展示 ----------

    def _dt_to_nav_dt(self, dt: datetime) -> datetime:
        return dt

    def show_nav_log_for_small_fail(self, n: int):
        self._set_ts_action_buttons_enabled(False)
        self.switch_detail_panel("nav")

        def ui_tip(s: str):
            self.nav_hint_label.setText(s)
            self.statusBar().showMessage(s, 5000)
            QApplication.processEvents()

        try:
            item = self.failure_list.currentItem()
            if not item:
                ui_tip("未选择失败项")
                return
            rec: FailureRecord = item.data(Qt.UserRole)
            if not rec:
                ui_tip("失败项数据为空")
                return

            end_dt = rec.state_ts_by_count.get(n) or rec.timeout_ts_by_count.get(n)
            if not end_dt:
                ui_tip(f"第{n}次没有可用时间戳（state_ts/timeout_ts均为空）")
                return

            if n == 1:
                start_dt = rec.first_ts
            else:
                start_dt = rec.state_ts_by_count.get(n - 1) or rec.timeout_ts_by_count.get(n - 1) or rec.first_ts

            if not start_dt:
                ui_tip("无法确定本次范围起点（first_ts为空）")
                return

            helper = self.nav_helper
            if helper is None:
                nav_root = self.get_nav_root_dir()
                if not nav_root:
                    ui_tip("未找到导航日志目录：**/data/log/navigation/navigation")
                    return
                self.nav_helper = NavigationLogHelper(nav_root)
                helper = self.nav_helper

            before_n = int(self.spin_before.value())
            after_m = int(self.spin_after.value())

            QApplication.setOverrideCursor(Qt.WaitCursor)
            try:
                ui_tip("正在建立导航日志索引（读取文件头/尾时间戳）...")
                if hasattr(helper, "build_index"):
                    helper.build_index(force=False)

                ui_tip("正在选择最合适的 log_info_file 文件...")
                picked = helper.pick_best_file_for_dt(self._dt_to_nav_dt(end_dt))
                if not picked:
                    ui_tip("未找到合适的 log_info_file 文件")
                    return

                picked_path = picked.path if hasattr(picked, "path") else picked
                self.nav_path_edit.setText(str(picked_path))

                ui_tip("正在读取文件并定位时间戳，截取上下文...")
                text, hit_idx, hit_ts, all_lines = helper.extract_context(
                    picked_path, self._dt_to_nav_dt(end_dt), before_n, after_m
                )

                ui_tip("正在渲染到面板...")
                self.nav_text.setPlainText(text)

                state_code = rec.state_by_count.get(n)
                hint = f"范围：{self._fmt_dt_ms(start_dt)} -> {self._fmt_dt_ms(end_dt)}"

                if state_code == 34:
                    ui_tip("正在分析：是否疑似相机无数据（size=0）...")
                    left0, right0 = helper.scan_camera_zero_in_range(
                        all_lines, self._dt_to_nav_dt(start_dt), self._dt_to_nav_dt(end_dt)
                    )
                    hint += f" | 相机size=0统计：left0={left0}, right0={right0}"

                ui_tip(hint)
            finally:
                QApplication.restoreOverrideCursor()

        finally:
            self._set_ts_action_buttons_enabled(True)

    def _parse_custom_timestamp(self, ts_str: str) -> Optional[datetime]:
        """解析用户输入的时间戳字符串"""
        if not ts_str or not ts_str.strip():
            return None
        
        ts_str = ts_str.strip()
        
        # 尝试多种格式
        formats = [
            "%Y-%m-%d %H:%M:%S,%f",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(ts_str, fmt)
                return dt
            except ValueError:
                continue
        
        return None

    def on_load_nav_log_by_ts(self):
        """根据自定义时间戳加载导航日志"""
        ts_str = self.nav_custom_ts_edit.text().strip()
        if not ts_str:
            QMessageBox.warning(self, "提示", "请输入时间戳")
            return
        
        target_dt = self._parse_custom_timestamp(ts_str)
        if not target_dt:
            QMessageBox.warning(self, "提示", "时间戳格式不正确，请使用格式：YYYY-MM-DD HH:MM:SS,mmm")
            return
        
        self._set_ts_action_buttons_enabled(False)
        self.switch_detail_panel("nav")

        def ui_tip(s: str):
            self.nav_hint_label.setText(s)
            self.statusBar().showMessage(s, 5000)
            QApplication.processEvents()

        try:
            helper = self.nav_helper
            if helper is None:
                nav_root = self.get_nav_root_dir()
                if not nav_root:
                    ui_tip("未找到导航日志目录：**/data/log/navigation/navigation")
                    return
                self.nav_helper = NavigationLogHelper(nav_root)
                helper = self.nav_helper

            before_n = int(self.spin_before.value())
            after_m = int(self.spin_after.value())

            QApplication.setOverrideCursor(Qt.WaitCursor)
            try:
                ui_tip("正在建立导航日志索引...")
                if hasattr(helper, "build_index"):
                    helper.build_index(force=False)

                ui_tip("正在选择最合适的 log_info_file 文件...")
                picked = helper.pick_best_file_for_dt(target_dt)
                if not picked:
                    ui_tip("未找到合适的 log_info_file 文件")
                    return

                picked_path = picked.path if hasattr(picked, "path") else picked
                self.nav_path_edit.setText(str(picked_path))

                ui_tip("正在读取文件并定位时间戳，截取上下文...")
                text, hit_idx, hit_ts, all_lines = helper.extract_context(
                    picked_path, target_dt, before_n, after_m
                )

                ui_tip("正在渲染到面板...")
                self.nav_text.setPlainText(text)

                hint = f"自定义时间戳：{self._fmt_dt_ms(target_dt)} | 实际命中：{self._fmt_dt_ms(hit_ts) if hit_ts else 'N/A'}"
                ui_tip(hint)
            finally:
                QApplication.restoreOverrideCursor()

        finally:
            self._set_ts_action_buttons_enabled(True)

    # ---------- 中台biz日志展示 ----------

    def show_biz_log_for_small_fail(self, n: int):
        self._set_ts_action_buttons_enabled(False)
        self.switch_detail_panel("biz")

        def ui_tip(s: str):
            self.biz_hint_label.setText(s)
            self.statusBar().showMessage(s, 5000)
            QApplication.processEvents()

        try:
            item = self.failure_list.currentItem()
            if not item:
                ui_tip("未选择失败项")
                return
            rec: FailureRecord = item.data(Qt.UserRole)
            if not rec:
                ui_tip("失败项数据为空")
                return

            recharge_dt = getattr(rec, "recharge_state_ts", None)
            if not recharge_dt:
                ui_tip("该条失败记录未捕获到 'Change to RECHARGE state' 时间戳，无法定位中台日志")
                return

            helper = self.biz_helper
            if helper is None:
                biz_root = self.get_biz_root_dir()
                if not biz_root:
                    ui_tip("未找到中台日志目录：**/data/log/biz")
                    return
                self.biz_helper = BizLogHelper(biz_root)
                helper = self.biz_helper

            before_n = int(self.spin_before.value())
            after_m = int(self.spin_after.value())

            QApplication.setOverrideCursor(Qt.WaitCursor)
            try:
                ui_tip("正在建立中台biz日志索引...")
                helper.build_index(force=False)

                ui_tip("正在选择最合适的 biz log.* 文件...")
                picked = helper.pick_best_file_for_dt(recharge_dt)
                if not picked:
                    ui_tip("未找到合适的 biz log.* 文件")
                    return

                self.biz_path_edit.setText(picked.path)

                ui_tip("提取 RECHARGE 后 5分钟窗口(全量)...")
                window_lines = helper.extract_window_lines(picked.path, recharge_dt, minutes=3)

                seg = helper.find_nearest_start_stop_pair(window_lines)
                biz_reason = helper.infer_reason(window_lines)

                # 全量窗口打印（你要求“这些都要打印出来”）
                window_block = (
                    "===== RECHARGE后3分钟窗口(全量) =====\n"
                    + "\n".join(window_lines)
                    + "\n\n"
                )

                seg_block = ""
                if seg.found_pair and seg.lines:
                    seg_block = (
                        "===== RECHARGE后5分钟：最近一对 Docking Start/Stop 区间（重点看这里） =====\n"
                        + "\n".join(seg.lines)
                        + "\n\n"
                    )
                else:
                    seg_block = "===== RECHARGE后5分钟：未找到 Docking Start/Stop 成对区间 =====\n\n"

                reason_block = f"===== 归因 =====\n{biz_reason}\n\n" if biz_reason else ""

                fail_lines = [ln for ln in window_lines if re.search(r"fail", ln, re.IGNORECASE)]
                fail_block = ""
                if fail_lines:
                    decorated = []
                    for ln in fail_lines[:200]:
                        tag = helper.classify_fail_line(ln)
                        decorated.append(f"[{tag}] {ln}" if tag else ln)
                    fail_block = "===== RECHARGE后5分钟 fail 行（最多200行） =====\n" + "\n".join(decorated) + "\n\n"

                ui_tip("截取锚点上下文(前N后M)...")
                text, hit_idx, hit_ts, all_lines = helper.extract_context(
                    picked.path, recharge_dt, before_n, after_m
                )
                context_block = "===== RECHARGE锚点上下文（前N后M） =====\n" + text

                ui_tip("渲染到面板...")
                self.biz_text.setPlainText(reason_block + seg_block + fail_block + window_block + context_block)

                ui_tip(
                    f"锚点：{self._fmt_dt_ms(recharge_dt)} | "
                    f"窗口行数(5min)={len(window_lines)} | "
                    f"Docking段={'有' if (seg.found_pair and seg.lines) else '无'} | "
                    f"biz_reason={biz_reason or '-'}"
                )
            finally:
                QApplication.restoreOverrideCursor()
        finally:
            self._set_ts_action_buttons_enabled(True)

    def show_biz_log_for_current_failure(self):
        self.switch_detail_panel("biz")

        def ui_tip(s: str):
            self.biz_hint_label.setText(s)
            self.statusBar().showMessage(s, 5000)
            QApplication.processEvents()

        item = self.failure_list.currentItem()
        if not item:
            ui_tip("未选择失败项")
            return
        rec = item.data(Qt.UserRole)
        if not rec:
            ui_tip("失败项数据为空")
            return
        if not rec.recharge_state_ts:
            ui_tip("该条失败记录无 RECHARGE 时间戳")
            return

        helper = getattr(self, "biz_helper", None)
        if helper is None:
            biz_root = self.get_biz_root_dir()
            if not biz_root:
                ui_tip("未找到中台日志目录：**/data/log/biz")
                return
            self.biz_helper = BizLogHelper(biz_root)
            helper = self.biz_helper

        before_n = int(self.spin_before.value())
        after_m = int(self.spin_after.value())

        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            helper.build_index(force=False)

            picked = helper.pick_best_file_for_dt(rec.recharge_state_ts)
            if not picked:
                ui_tip("未找到合适的 biz log.* 文件")
                return

            self.biz_path_edit.setText(picked.path)

            text, hit_idx, hit_ts, all_lines = helper.extract_context(
                picked.path, rec.recharge_state_ts, before_n, after_m
            )

            # 这里也可以把之前分析时存的 fail_lines_5min 放在顶部（如果有）
            # 5分钟窗口全量
            window_lines = helper.extract_window_lines(picked.path, rec.recharge_state_ts, minutes=5)

            # Docking段 + 归因
            seg = helper.find_nearest_start_stop_pair(window_lines)
            biz_reason = helper.infer_reason(window_lines)

            reason_block = f"===== 归因(按Docking段判定) =====\n{biz_reason}\n\n" if biz_reason else ""
            seg_block = ""
            if seg.found_pair and seg.lines:
                seg_block = (
                    "===== RECHARGE后5分钟：最近一对 Docking Start/Stop 区间（重点看这里） =====\n"
                    + "\n".join(seg.lines) + "\n\n"
                )
            else:
                seg_block = "===== RECHARGE后5分钟：未找到 Docking Start/Stop 成对区间 =====\n\n"

            # 缓存关键行
            head = ""
            if getattr(rec, "biz_fail_lines_5min", None):
                head = "===== RECHARGE后5分钟 关键行(缓存：error/warn/interrupt/fail/stop docking) =====\n" + rec.biz_fail_lines_5min + "\n\n"

            # 窗口全量（你要"这些都打印出来"就看这里）
            window_block = "===== RECHARGE后5分钟窗口(全量) =====\n" + "\n".join(window_lines) + "\n\n"

            # 上下文（前N后M，包含锚点之前很多行，避免你再误会）
            context_block = "===== RECHARGE锚点上下文(前N后M，包含锚点之前行属正常) =====\n" + text

            self.biz_text.setPlainText(reason_block + seg_block + head + window_block + context_block)
            ui_tip(f"锚点：{self._fmt_dt_ms(rec.recharge_state_ts)} | biz_reason={getattr(rec,'biz_reason',None)}")
        finally:
            QApplication.restoreOverrideCursor()

    def on_load_biz_log_by_ts(self):
        """根据自定义时间戳加载中台日志"""
        ts_str = self.biz_custom_ts_edit.text().strip()
        if not ts_str:
            QMessageBox.warning(self, "提示", "请输入时间戳")
            return
        
        target_dt = self._parse_custom_timestamp(ts_str)
        if not target_dt:
            QMessageBox.warning(self, "提示", "时间戳格式不正确，请使用格式：YYYY-MM-DD HH:MM:SS,mmm")
            return
        
        self._set_ts_action_buttons_enabled(False)
        self.switch_detail_panel("biz")

        def ui_tip(s: str):
            self.biz_hint_label.setText(s)
            self.statusBar().showMessage(s, 5000)
            QApplication.processEvents()

        try:
            helper = self.biz_helper
            if helper is None:
                biz_root = self.get_biz_root_dir()
                if not biz_root:
                    ui_tip("未找到中台日志目录：**/data/log/biz")
                    return
                self.biz_helper = BizLogHelper(biz_root)
                helper = self.biz_helper

            before_n = int(self.spin_before.value())
            after_m = int(self.spin_after.value())

            QApplication.setOverrideCursor(Qt.WaitCursor)
            try:
                ui_tip("正在建立中台biz日志索引...")
                helper.build_index(force=False)

                ui_tip("正在选择最合适的 biz log.* 文件...")
                picked = helper.pick_best_file_for_dt(target_dt)
                if not picked:
                    ui_tip("未找到合适的 biz log.* 文件")
                    return

                self.biz_path_edit.setText(picked.path)

                ui_tip("正在读取文件并定位时间戳，截取上下文...")
                text, hit_idx, hit_ts, all_lines = helper.extract_context(
                    picked.path, target_dt, before_n, after_m
                )

                ui_tip("正在渲染到面板...")
                self.biz_text.setPlainText(text)

                hint = f"自定义时间戳：{self._fmt_dt_ms(target_dt)} | 实际命中：{self._fmt_dt_ms(hit_ts) if hit_ts else 'N/A'}"
                ui_tip(hint)
            finally:
                QApplication.restoreOverrideCursor()

        finally:
            self._set_ts_action_buttons_enabled(True)

def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()