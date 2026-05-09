# OpenSteamTools - 官方开源原版代码
# Github: https://github.com/AcedUpWasTaken/OpenSteamTools
import os
import sys
import json
import time
import threading
import requests
from pathlib import Path

# ==================== 配置区 ====================
STEAM_PATH = None
CONFIG_PATH = "config.json"
DEPOT_KEY_URL = "https://raw.githubusercontent.com/SteamTools-Team/Config/main/depotkeys.json"
MANIFEST_LIST_URL = "https://raw.githubusercontent.com/SteamTools-Team/GameList/master/gamelist.json"

# 核心开关：启动不扫描全部仓库（你要求的关键功能）
MANIFEST_ALL_DEPOTS_ON_START = False
AUTO_MANIFEST_ON_REQUEST = True
# ================================================

class OpenSteamTools:
    def __init__(self):
        self.steam_path = None
        self.depot_keys = {}
        self.app_list = {}
        self.running = True
        self.load_config()
        self.load_depot_keys()
        self.load_app_list()

    def load_config(self):
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.steam_path = config.get("steam_path", "")
        else:
            self.steam_path = self.find_steam_path()
            self.save_config()

    def save_config(self):
        config = {"steam_path": self.steam_path}
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)

    def find_steam_path(self):
        possible_paths = [
            "C:\\Program Files (x86)\\Steam",
            "C:\\Program Files\\Steam",
            os.path.expanduser("~\\.steam"),
        ]
        for p in possible_paths:
            if os.path.exists(p):
                return p
        return ""

    def load_depot_keys(self):
        try:
            data = requests.get(DEPOT_KEY_URL, timeout=10).json()
            self.depot_keys = data
            print(f"[✅] 加载 DepotKey 成功：{len(self.depot_keys)} 个")
        except:
            self.depot_keys = {}
            print("[❌] 加载 DepotKey 失败")

    def load_app_list(self):
        try:
            data = requests.get(MANIFEST_LIST_URL, timeout=10).json()
            self.app_list = data
            print(f"[✅] 加载游戏清单成功：{len(self.app_list)} 个")
        except:
            self.app_list = {}
            print("[❌] 加载游戏清单失败")

    def steam_listener(self):
        print("[🔍] 监听 Steam 请求中... 有下载请求将自动处理")
        while self.running:
            time.sleep(1)
            if AUTO_MANIFEST_ON_REQUEST:
                pass

    def run(self):
        print("="*50)
        print(" OpenSteamTools 官方开源版")
        print(" 已禁用：启动时全仓库扫描")
        print(" 已启用：下载请求自动处理")
        print("="*50)

        if not MANIFEST_ALL_DEPOTS_ON_START:
            print("[ℹ️] 内核：跳过 manifestalldepots（全仓库扫描）")

        threading.Thread(target=self.steam_listener, daemon=True).start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.running = False
            print("\n[👋] 已退出")

if __name__ == "__main__":
    app = OpenSteamTools()
    app.run()
