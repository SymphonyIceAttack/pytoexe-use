#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gtp4zen.py - Python 移植版本
原 C++ 项目: gtp4zen (zen.dll 的 GTP 桥接器)
支持 Zen6 和 Zen7 的 DLL 接口
"""

import sys
import os
import argparse
import ctypes
from ctypes import wintypes, c_void_p, c_int, c_float, c_bool, c_char_p
import time
import datetime
import threading
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Tuple, Optional

# ---------------------------- 全局变量 ----------------------------
g_zenver = 7                # 默认 Zen7
g_threads = 4               # 线程数，稍后根据 CPU 核数更新
g_maxtime = 10              # 每手最大思考时间（秒）
g_strength = 10000          # 最大模拟步数
g_logfile = ""              # 日志文件路径
g_debug = False             # 是否输出调试信息到 stderr
g_think_interval = 1000     # 思考间隔（毫秒）

# ---------------------------- 辅助函数 ----------------------------
def get_compiled_time() -> int:
    """返回程序启动时的时间戳（模拟原 C++ 的编译时间）"""
    return int(time.time())

def get_compile_strtime() -> str:
    """返回当前时间字符串（模拟原 C++ 的编译时间字符串）"""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def ansi2num(ch: str) -> int:
    """将 GTP 坐标字母（A-Z 跳过 I）转换为 0-based 索引"""
    axes = "ABCDEFGHJKLMNOPQRSTUVWXYZ"
    try:
        return axes.index(ch.upper())
    except ValueError:
        return -1

def num2ansi(x: int, y: int, boardsize: int) -> str:
    """将 0-based 坐标转换为 GTP 坐标字符串（如 'Q16'）"""
    if not (0 <= x < boardsize and 0 <= y < boardsize):
        return ""
    axes = "ABCDEFGHJKLMNOPQRSTUVWXYZ"
    return f"{axes[x]}{boardsize - y}"

def logprintf(msg: str):
    """写日志到文件（如果 g_logfile 非空）"""
    if not g_logfile:
        return
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    with open(g_logfile, 'a', encoding='utf-8') as f:
        f.write(f"{now} | {msg}\n")

def get_module_file_path() -> str:
    """获取当前可执行文件所在目录"""
    return os.path.dirname(os.path.abspath(sys.argv[0]))

# ---------------------------- GTP 抽象基类 ----------------------------
class CGtp(ABC):
    @abstractmethod
    def load(self, zen_dll_path: str, lua_engine_path: str) -> bool:
        pass

    @abstractmethod
    def unload(self) -> bool:
        pass

    @abstractmethod
    def list_commands(self) -> str:
        pass

    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def version(self) -> str:
        pass

    @abstractmethod
    def protocol_version(self) -> str:
        pass

    @abstractmethod
    def clear_board(self) -> str:
        pass

    @abstractmethod
    def boardsize(self, size: int) -> str:
        pass

    @abstractmethod
    def komi(self, k: float) -> str:
        pass

    @abstractmethod
    def free_handicap(self, posarray: List[str]) -> str:
        pass

    @abstractmethod
    def winrate(self) -> str:
        pass

    @abstractmethod
    def undo(self) -> str:
        pass

    @abstractmethod
    def play(self, color: str, position: str) -> str:
        pass

    @abstractmethod
    def genmove(self, color: str) -> str:
        pass

    @abstractmethod
    def time_settings(self, main_time: int, byo_yomi_time: int, byo_yomi_stones: int) -> str:
        pass

    @abstractmethod
    def time_left(self, color: str, time_sec: int, stones: int) -> str:
        pass

# ---------------------------- Zen6 实现 ----------------------------
class Zen6Gtp(CGtp):
    def __init__(self):
        self.dll = None          # ctypes.CDLL 对象
        self.boardsize = 19
        self.cur_movenum = 0
        self.maintime = datetime.datetime.now() + datetime.timedelta(days=365)
        self.lefttime = datetime.datetime.now() + datetime.timedelta(days=365)
        self.winrate_str = ""
        self.lua_state = None    # 可选，原 C++ 使用了 lua，这里忽略（可自行扩展）

    def _load_functions(self):
        """加载 zen.dll 中的导出函数（基于 Zen6 的修饰名）"""
        self.dll.ZenClearBoard.argtypes = []
        self.dll.ZenClearBoard.restype = None

        self.dll.ZenGetNextColor.argtypes = []
        self.dll.ZenGetNextColor.restype = c_int

        self.dll.ZenGetTopMoveInfo.argtypes = [c_int, ctypes.POINTER(c_int), ctypes.POINTER(c_int),
                                               ctypes.POINTER(c_int), ctypes.POINTER(c_float),
                                               c_char_p, c_int]
        self.dll.ZenGetTopMoveInfo.restype = None

        self.dll.ZenInitialize.argtypes = [c_char_p]
        self.dll.ZenInitialize.restype = None

        self.dll.ZenIsInitialized.argtypes = []
        self.dll.ZenIsInitialized.restype = c_bool

        self.dll.ZenIsThinking.argtypes = []
        self.dll.ZenIsThinking.restype = c_bool

        self.dll.ZenPass.argtypes = [c_int]
        self.dll.ZenPass.restype = None

        self.dll.ZenPlay.argtypes = [c_int, c_int, c_int]
        self.dll.ZenPlay.restype = c_bool

        self.dll.ZenSetBoardSize.argtypes = [c_int]
        self.dll.ZenSetBoardSize.restype = None

        self.dll.ZenSetKomi.argtypes = [c_float]
        self.dll.ZenSetKomi.restype = None

        self.dll.ZenSetMaxTime.argtypes = [c_float]
        self.dll.ZenSetMaxTime.restype = None

        self.dll.ZenSetNumberOfSimulations.argtypes = [c_int]
        self.dll.ZenSetNumberOfSimulations.restype = None

        self.dll.ZenSetNumberOfThreads.argtypes = [c_int]
        self.dll.ZenSetNumberOfThreads.restype = None

        self.dll.ZenSetAmafWeightFactor.argtypes = [c_float]
        self.dll.ZenSetAmafWeightFactor.restype = None

        self.dll.ZenSetPriorWeightFactor.argtypes = [c_float]
        self.dll.ZenSetPriorWeightFactor.restype = None

        self.dll.ZenSetDCNN.argtypes = [c_bool]
        self.dll.ZenSetDCNN.restype = None

        self.dll.ZenStartThinking.argtypes = [c_int]
        self.dll.ZenStartThinking.restype = None

        self.dll.ZenStopThinking.argtypes = []
        self.dll.ZenStopThinking.restype = None

        self.dll.ZenUndo.argtypes = [c_int]
        self.dll.ZenUndo.restype = c_bool

    def load(self, zen_dll_path: str, lua_engine_path: str) -> bool:
        self.unload()
        # 加载 DLL
        self.dll = ctypes.CDLL(zen_dll_path)
        if not self.dll:
            logprintf("load zen.dll failed")
            return False
        logprintf("dll加载正常")

        # 加载函数
        try:
            self.dll.ZenClearBoard = self.dll["?ZenClearBoard@@YAXXZ"]
            self.dll.ZenGetNextColor = self.dll["?ZenGetNextColor@@YAHXZ"]
            self.dll.ZenGetTopMoveInfo = self.dll["?ZenGetTopMoveInfo@@YAXHAAH00AAMPADH@Z"]
            self.dll.ZenInitialize = self.dll["?ZenInitialize@@YAXPBD@Z"]
            self.dll.ZenIsInitialized = self.dll["?ZenIsInitialized@@YA_NXZ"]
            self.dll.ZenIsThinking = self.dll["?ZenIsThinking@@YA_NXZ"]
            self.dll.ZenPass = self.dll["?ZenPass@@YAXH@Z"]
            self.dll.ZenPlay = self.dll["?ZenPlay@@YA_NHHH@Z"]
            self.dll.ZenSetBoardSize = self.dll["?ZenSetBoardSize@@YAXH@Z"]
            self.dll.ZenSetKomi = self.dll["?ZenSetKomi@@YAXM@Z"]
            self.dll.ZenSetMaxTime = self.dll["?ZenSetMaxTime@@YAXM@Z"]
            self.dll.ZenSetNumberOfSimulations = self.dll["?ZenSetNumberOfSimulations@@YAXH@Z"]
            self.dll.ZenSetNumberOfThreads = self.dll["?ZenSetNumberOfThreads@@YAXH@Z"]
            self.dll.ZenSetAmafWeightFactor = self.dll["?ZenSetAmafWeightFactor@@YAXM@Z"]
            self.dll.ZenSetPriorWeightFactor = self.dll["?ZenSetPriorWeightFactor@@YAXM@Z"]
            self.dll.ZenSetDCNN = self.dll["?ZenSetDCNN@@YAX_N@Z"]
            self.dll.ZenStartThinking = self.dll["?ZenStartThinking@@YAXH@Z"]
            self.dll.ZenStopThinking = self.dll["?ZenStopThinking@@YAXXZ"]
            self.dll.ZenUndo = self.dll["?ZenUndo@@YA_NH@Z"]
            self._load_functions()
        except AttributeError as e:
            logprintf(f"函数定位失败: {e}")
            return False

        # 初始化引擎
        self.dll.ZenInitialize(b"")
        self.dll.ZenSetBoardSize(self.boardsize)
        self.dll.ZenSetKomi(6.5)
        self.dll.ZenSetNumberOfThreads(g_threads)
        self.dll.ZenSetNumberOfSimulations(99999999)
        self.dll.ZenSetMaxTime(float(g_maxtime))
        self.dll.ZenSetAmafWeightFactor(1.0)
        self.dll.ZenSetPriorWeightFactor(1.0)
        self.dll.ZenSetDCNN(True)
        self.dll.ZenClearBoard()
        is_init = self.dll.ZenIsInitialized()
        logprintf(f"zen.dll(zen6) initialize {'success' if is_init else 'failed'}")
        return is_init

    def unload(self) -> bool:
        if self.dll:
            # 不需要显式 FreeLibrary，ctypes 会在对象销毁时处理
            self.dll = None
        return True

    def list_commands(self) -> str:
        return "= list_commands\nname\nversion\nprotocol_version\nquit\nclear_board\nboardsize\nkomi\n" \
               "set_free_handicap\nplace_free_handicap\nwinrate\nundo\nplay\ngenmove\ntime_settings\ntime_left\n"

    def name(self) -> str:
        return "= Gtp4Zen(zen6)\n"

    def version(self) -> str:
        return "= v0.3.3\n"

    def protocol_version(self) -> str:
        return "= 2\n"

    def clear_board(self) -> str:
        logprintf("clear_board()")
        self.dll.ZenClearBoard()
        self.cur_movenum = 0
        self.maintime = datetime.datetime.now() + datetime.timedelta(days=365)
        self.lefttime = datetime.datetime.now() + datetime.timedelta(days=365)
        return "= \n"

    def boardsize(self, size: int) -> str:
        logprintf(f"boardsize({size})")
        if size in (9, 11, 13, 19):
            self.boardsize = size
            self.dll.ZenSetBoardSize(size)
            return "= \n"
        else:
            return "? unknown boardsize\n"

    def komi(self, k: float) -> str:
        logprintf(f"komi({k:.2f})")
        # 原 C++ 中还有 lua 获取 komi 的逻辑，这里省略，直接设置
        if 0 <= k <= 300:
            self.dll.ZenSetKomi(k)
            return "= \n"
        else:
            return "? komi range from 0 to 300, mostly 6.5 or 7.5\n"

    def free_handicap(self, posarray: List[str]) -> str:
        logprintf("set_free_handicap()/place_free_handicap()")
        for pos in posarray:
            self.play("b", pos)
        return "= \n"

    def winrate(self) -> str:
        return f"= {self.winrate_str}\n"

    def play(self, color: str, position: str) -> str:
        logprintf(f"play({color},{position})")
        color_low = color.lower()
        if color_low not in ("b", "w"):
            return "? error parameter\n"
        c = 2 if color_low == "w" else 1  # GTP4ZEN_COLOR_WHITE=1? 原代码中 white=1, black=2，这里根据 play 调用反推
        # 实际 ZenPlay 参数: (x, y, color) 其中 color 1=白? 需确认。原 C++ 中直接传递了 GTP4ZEN_COLOR_XXX
        # 为保险，我们使用原定义：白色=1，黑色=2（见 stdafx.h）
        self.cur_movenum += 1

        pos_up = position.upper()
        if pos_up == "PASS":
            self.dll.ZenPass(c)
            return "= \n"
        if pos_up == "RESIGN":
            return "= \n"
        if len(position) < 2 or len(position) > 3:
            return "? error parameter\n"

        x = ansi2num(position[0])
        if x < 0:
            return "? error parameter\n"
        try:
            y = int(position[1:])
        except ValueError:
            return "? error parameter\n"
        if not (1 <= y <= self.boardsize):
            return "? error parameter\n"
        y = self.boardsize - y

        self.winrate_str = ""
        ok = self.dll.ZenPlay(x, y, c)
        return "= \n" if ok else "? error parameter\n"

    def _find_best_move(self, debug: bool) -> Tuple[str, int, int, int, float]:
        """查询最佳选点，返回 (坐标字符串, x, y, 模拟步数, 胜率)"""
        x = c_int(-1)
        y = c_int(-1)
        sim = c_int(-1)
        w = c_float(0.0)
        s = ctypes.create_string_buffer(256)
        for i in range(5):   # 从4到0
            self.dll.ZenGetTopMoveInfo(i, ctypes.byref(x), ctypes.byref(y),
                                       ctypes.byref(sim), ctypes.byref(w), s, 99)
            if debug and g_debug and x.value >= 0 and y.value >= 0:
                coord = num2ansi(x.value, y.value, self.boardsize)
                print(f"{coord:10} Weight: {w.value*100:05.2f}    {s.value.decode()}", file=sys.stderr)
            if i == 0:
                if b"pass" in s.value:
                    return ("pass", x.value, y.value, sim.value, w.value)
                if x.value >= 0 and y.value >= 0 and sim.value >= 0:
                    coord = num2ansi(x.value, y.value, self.boardsize)
                    return (coord, x.value, y.value, sim.value, w.value)
                else:
                    return ("resign", x.value, y.value, sim.value, w.value)
        return ("", -1, -1, -1, 0.0)

    def _genmove(self, color: str, max_time_ms: int, strength: int) -> str:
        logprintf(f"__genmove({color}, {max_time_ms}ms, {strength}step)")
        c = 2 if color.lower() == "w" else 1
        self.dll.ZenStartThinking(c)
        start = datetime.datetime.now()
        x = y = sim = -1
        w = 0.0
        reason = ""
        while True:
            if not self.dll.ZenIsThinking():
                reason = "zen stop thinking"
                break
            elapsed = (datetime.datetime.now() - start).total_seconds() * 1000
            if elapsed >= max_time_ms:
                reason = "thinking time out"
                break
            time.sleep(g_think_interval / 1000.0)
            _, x, y, sim, w = self._find_best_move(True)
            logprintf("......")
            if g_debug:
                print("......", file=sys.stderr)
                sys.stderr.flush()
            if sim >= strength:
                reason = "thinking strength out"
                break
        self.dll.ZenStopThinking()
        result, x, y, sim, w = self._find_best_move(True)
        elapsed = (datetime.datetime.now() - start).total_seconds() * 1000
        logprintf(f"{reason}: {result}({x},{y}), max_time: {max_time_ms}ms, strength: {strength}, elapsed: {elapsed:.0f}ms")
        self.play(color, result)
        self.winrate_str = f"{w*100:.2f}"
        return f"= {result}\n"

    def genmove(self, color: str) -> str:
        now = datetime.datetime.now()
        left_ms = int((self.lefttime - now).total_seconds() * 1000)
        logprintf("------------------------>>>")
        logprintf(f"genmove({color})")
        # 原 C++ 中有 lua 计算时间，这里简化为固定逻辑
        if left_ms >= 180000:
            result = self._genmove(color, g_maxtime * 1000, g_strength)
        elif left_ms >= 90000:
            result = self._genmove(color, 2000, g_strength)
        else:
            result = self._genmove(color, 100, g_strength)
        logprintf("------------------------<<<")
        return result

    def undo(self) -> str:
        logprintf("undo()")
        self.dll.ZenUndo(1)
        return "= \n"

    def time_settings(self, main_time: int, byo_yomi_time: int, byo_yomi_stones: int) -> str:
        logprintf(f"time_settings({main_time}, {byo_yomi_time}, {byo_yomi_stones})")
        self.maintime = datetime.datetime.now() + datetime.timedelta(seconds=main_time)
        return "= \n"

    def time_left(self, color: str, time_sec: int, stones: int) -> str:
        logprintf(f"time_left({color}, {time_sec}, {stones})")
        self.lefttime = datetime.datetime.now() + datetime.timedelta(seconds=time_sec)
        return "= \n"

# ---------------------------- Zen7 实现 ----------------------------
class Zen7Gtp(Zen6Gtp):
    """Zen7 与 Zen6 主要差异是导出的函数名和个别函数不同"""
    def _load_functions(self):
        # Zen7 没有 ZenSetAmafWeightFactor 和 ZenSetPriorWeightFactor，但有 ZenSetPnLevel, ZenSetPnWeight
        self.dll.ZenClearBoard.argtypes = []
        self.dll.ZenClearBoard.restype = None
        self.dll.ZenGetNextColor.argtypes = []
        self.dll.ZenGetNextColor.restype = c_int
        self.dll.ZenGetTopMoveInfo.argtypes = [c_int, ctypes.POINTER(c_int), ctypes.POINTER(c_int),
                                               ctypes.POINTER(c_int), ctypes.POINTER(c_float),
                                               c_char_p, c_int]
        self.dll.ZenGetTopMoveInfo.restype = None
        self.dll.ZenInitialize.argtypes = [c_char_p]
        self.dll.ZenInitialize.restype = None
        self.dll.ZenIsInitialized.argtypes = []
        self.dll.ZenIsInitialized.restype = c_bool
        self.dll.ZenIsThinking.argtypes = []
        self.dll.ZenIsThinking.restype = c_bool
        self.dll.ZenPass.argtypes = [c_int]
        self.dll.ZenPass.restype = None
        self.dll.ZenPlay.argtypes = [c_int, c_int, c_int]
        self.dll.ZenPlay.restype = c_bool
        self.dll.ZenSetBoardSize.argtypes = [c_int]
        self.dll.ZenSetBoardSize.restype = None
        self.dll.ZenSetKomi.argtypes = [c_float]
        self.dll.ZenSetKomi.restype = None
        self.dll.ZenSetMaxTime.argtypes = [c_float]
        self.dll.ZenSetMaxTime.restype = None
        self.dll.ZenSetNumberOfSimulations.argtypes = [c_int]
        self.dll.ZenSetNumberOfSimulations.restype = None
        self.dll.ZenSetNumberOfThreads.argtypes = [c_int]
        self.dll.ZenSetNumberOfThreads.restype = None
        self.dll.ZenSetPnLevel.argtypes = [c_int]
        self.dll.ZenSetPnLevel.restype = None
        self.dll.ZenSetPnWeight.argtypes = [c_float]
        self.dll.ZenSetPnWeight.restype = None
        self.dll.ZenStartThinking.argtypes = [c_int]
        self.dll.ZenStartThinking.restype = None
        self.dll.ZenStopThinking.argtypes = []
        self.dll.ZenStopThinking.restype = None
        self.dll.ZenUndo.argtypes = [c_int]
        self.dll.ZenUndo.restype = c_bool

    def load(self, zen_dll_path: str, lua_engine_path: str) -> bool:
        self.unload()
        self.dll = ctypes.CDLL(zen_dll_path)
        if not self.dll:
            logprintf("load zen.dll failed")
            return False
        logprintf("dll加载正常")
        try:
            self.dll.ZenClearBoard = self.dll["?ZenClearBoard@@YAXXZ"]
            self.dll.ZenGetNextColor = self.dll["?ZenGetNextColor@@YAHXZ"]
            self.dll.ZenGetTopMoveInfo = self.dll["?ZenGetTopMoveInfo@@YAXHAAH00AAMPADH@Z"]
            self.dll.ZenInitialize = self.dll["?ZenInitialize@@YAXPBD@Z"]
            self.dll.ZenIsInitialized = self.dll["?ZenIsInitialized@@YA_NXZ"]
            self.dll.ZenIsThinking = self.dll["?ZenIsThinking@@YA_NXZ"]
            self.dll.ZenPass = self.dll["?ZenPass@@YAXH@Z"]
            self.dll.ZenPlay = self.dll["?ZenPlay@@YA_NHHH@Z"]
            self.dll.ZenSetBoardSize = self.dll["?ZenSetBoardSize@@YAXH@Z"]
            self.dll.ZenSetKomi = self.dll["?ZenSetKomi@@YAXM@Z"]
            self.dll.ZenSetMaxTime = self.dll["?ZenSetMaxTime@@YAXM@Z"]
            self.dll.ZenSetNumberOfSimulations = self.dll["?ZenSetNumberOfSimulations@@YAXH@Z"]
            self.dll.ZenSetNumberOfThreads = self.dll["?ZenSetNumberOfThreads@@YAXH@Z"]
            self.dll.ZenSetPnLevel = self.dll["?ZenSetPnLevel@@YAXH@Z"]
            self.dll.ZenSetPnWeight = self.dll["?ZenSetPnWeight@@YAXM@Z"]
            self.dll.ZenStartThinking = self.dll["?ZenStartThinking@@YAXH@Z"]
            self.dll.ZenStopThinking = self.dll["?ZenStopThinking@@YAXXZ"]
            self.dll.ZenUndo = self.dll["?ZenUndo@@YA_NH@Z"]
            self._load_functions()
        except AttributeError as e:
            logprintf(f"函数定位失败: {e}")
            return False

        self.dll.ZenInitialize(b"")
        self.dll.ZenSetBoardSize(self.boardsize)
        self.dll.ZenSetKomi(6.5)
        self.dll.ZenSetNumberOfThreads(g_threads)
        self.dll.ZenSetNumberOfSimulations(99999999)
        self.dll.ZenSetMaxTime(float(g_maxtime))
        self.dll.ZenClearBoard()
        is_init = self.dll.ZenIsInitialized()
        logprintf(f"zen.dll(zen7) initialize {'success' if is_init else 'failed'}")
        return is_init

    def name(self) -> str:
        return "= Gtp4Zen(zen7)\n"

# ---------------------------- 主程序 ----------------------------
def play_zen(gtp: CGtp):
    """GTP 主循环"""
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            cmd = parts[0].lower()
            result = ""

            if cmd == "list_commands":
                result = gtp.list_commands()
            elif cmd == "name":
                result = gtp.name()
            elif cmd == "version":
                result = gtp.version()
            elif cmd == "protocol_version":
                result = gtp.protocol_version()
            elif cmd == "quit":
                break
            elif cmd == "clear_board":
                result = gtp.clear_board()
            elif cmd == "boardsize" and len(parts) >= 2:
                result = gtp.boardsize(int(parts[1]))
            elif cmd == "komi" and len(parts) >= 2:
                result = gtp.komi(float(parts[1]))
            elif cmd == "play" and len(parts) >= 3:
                result = gtp.play(parts[1], parts[2])
            elif cmd == "genmove" and len(parts) >= 2:
                result = gtp.genmove(parts[1])
            elif cmd in ("place_free_handicap", "set_free_handicap") and len(parts) >= 2:
                result = gtp.free_handicap(parts[1:])
            elif cmd == "winrate":
                result = gtp.winrate()
            elif cmd == "undo":
                result = gtp.undo()
            elif cmd == "time_settings" and len(parts) >= 4:
                result = gtp.time_settings(int(parts[1]), int(parts[2]), int(parts[3]))
            elif cmd == "time_left" and len(parts) >= 4:
                result = gtp.time_left(parts[1], int(parts[2]), int(parts[3]))
            else:
                result = "? unknown command\n"

            sys.stdout.write(result)
            sys.stdout.flush()
            logprintf(f"command: {line}")
            logprintf(f"result: {result.strip()}")
        except (KeyboardInterrupt, EOFError):
            break

def main():
    global g_threads, g_maxtime, g_strength, g_logfile, g_debug, g_think_interval, g_zenver

    parser = argparse.ArgumentParser(description="gtp4zen - Python port")
    parser.add_argument("-z", "--zenversion", type=int, choices=[6,7], default=7, help="Zen DLL version (6 or 7)")
    parser.add_argument("-t", "--threads", type=int, default=os.cpu_count() or 4, help="Number of threads")
    parser.add_argument("-T", "--maxtime", type=int, default=10, help="Max time per move (seconds)")
    parser.add_argument("-s", "--strength", type=int, default=10000, help="Max simulations per move")
    parser.add_argument("-l", "--logfile", type=str, default="", help="Log file path")
    parser.add_argument("-L", "--logfilenametime", action="store_true", help="Add timestamp to log filename")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug output")
    parser.add_argument("-i", "--ithink", type=int, default=1000, help="Thinking interval (ms)")

    args = parser.parse_args()

    g_zenver = args.zenversion
    g_threads = args.threads
    g_maxtime = args.maxtime
    g_strength = args.strength
    g_debug = args.debug
    g_think_interval = args.ithink

    # 日志文件名处理
    logfile = args.logfile
    if args.logfilenametime and logfile:
        ts = datetime.datetime.now().strftime("_%Y-%m-%d_%H-%M-%S")
        p = Path(logfile)
        stem = p.stem
        suffix = p.suffix
        logfile = p.parent / f"{stem}{ts}{suffix}"
        g_logfile = str(logfile)
    else:
        g_logfile = logfile

    print(f"gtp4zen (Python port) compile: {get_compile_strtime()}", file=sys.stderr)
    print(f"CPU cores: {g_threads}", file=sys.stderr)
    print(f"Zen version: {g_zenver}", file=sys.stderr)
    print(f"Threads: {g_threads}", file=sys.stderr)
    print(f"Max time: {g_maxtime}s", file=sys.stderr)
    print(f"Strength: {g_strength}", file=sys.stderr)

    base_path = get_module_file_path()
    zen_dll = os.path.join(base_path, "zen.dll")
    lua_engine = os.path.join(base_path, "gtp4zen.lua")

    if not os.path.isfile(zen_dll):
        print(f"ERROR: {zen_dll} not found", file=sys.stderr)
        logprintf("ERROR: zen.dll not exist?")
        return

    gtp = None
    if g_zenver == 6:
        gtp = Zen6Gtp()
    else:
        gtp = Zen7Gtp()

    if gtp.load(zen_dll, lua_engine):
        play_zen(gtp)
        gtp.unload()

if __name__ == "__main__":
    main()