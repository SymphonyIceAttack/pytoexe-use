import requests
import pandas as pd
import time
import os
import sys
import logging
import threading
import json
from datetime import datetime

# 尝试导入Windows通知库，失败则降级为纯控制台提醒
try:
    from win10toast_click import ToastNotifier
    TOAST_AVAILABLE = True
except ImportError:
    try:
        from win10toast import ToastNotifier
        TOAST_AVAILABLE = True
    except ImportError:
        TOAST_AVAILABLE = False

# ================= 全局路径自适应配置 =================
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TYPES_CACHE = os.path.join(BASE_DIR, "eve_cn_types_cache.csv")
LOG_FILE = os.path.join(BASE_DIR, "eve_toolkit.log")
WATCH_CONFIG = os.path.join(BASE_DIR, "price_watchlist.json")

ESI_BASE = "https://esi.evepc.163.com/latest"
LANGUAGE = "zh"
REQUEST_DELAY = 0.15
CACHE_VALID_HOURS = 24

# 常用国服星域ID映射 (支持中英文别名)
REGION_MAP = {
    "吉他": 10000002, "伏尔戈": 10000002, "the forge": 10000002,
    "多美": 10000030, "domain": 10000030,
    "萨沙": 10000054, "sashas": 10000054,
    "深渊": 10000070, "abyssal": 10000070,
}
DEFAULT_REGION_ID = 10000002

# ================= 统一日志配置 =================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ================= 价格监控模块 (后台线程+多星域) =================
class PriceMonitor:
    def __init__(self):
        self.running = False
        self.thread = None
        self.watchlist = []
        self.interval = 300
        self.load_config()
        self.toaster = ToastNotifier() if TOAST_AVAILABLE else None

    def load_config(self):
        if os.path.exists(WATCH_CONFIG):
            try:
                with open(WATCH_CONFIG, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.watchlist = data.get("items", [])
                    self.interval = data.get("interval", 300)
            except Exception as e:
                logger.error(f"[监控] ❌ 读取配置文件失败: {e}")

    def save_config(self):
        try:
            with open(WATCH_CONFIG, 'w', encoding='utf-8') as f:
                json.dump({"items": self.watchlist, "interval": self.interval}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"[监控] ❌ 保存配置文件失败: {e}")

    def send_alert(self, item_name, alert_type, current_price, threshold):
        msg = f"🚨 [{item_name}] {alert_type}! 当前: {current_price:,.2f} | 阈值: {threshold:,.2f}"
        print(f"\n\033[91m{msg}\033[0m\n")
        logger.warning(f"[监控] {msg}")
        if self.toaster:
            try:
                self.toaster.show_toast("EVE国服价格预警", msg, duration=10, threaded=True)
            except Exception:
                pass

    def _check_prices(self):
        logger.info(f"[监控] 🟢 价格监控已启动 (间隔:{self.interval}s | 监控:{len(self.watchlist)}个)")
        while self.running:
            if not self.watchlist:
                time.sleep(5); continue
            for item in self.watchlist.copy():
                if not self.running: break
                try:
                    region_id = item.get("region_id", DEFAULT_REGION_ID)
                    r = requests.get(f"{ESI_BASE}/markets/{region_id}/orders/", params={"type_id": item["id"]}, timeout=15)
                    r.raise_for_status()
                    orders = r.json()
                    
                    sell_orders = [o['price'] for o in orders if not o['is_buy_order']]
                    buy_orders = [o['price'] for o in orders if o['is_buy_order']]
                    min_sell = min(sell_orders) if sell_orders else None
                    max_buy = max(buy_orders) if buy_orders else None
                    
                    region_name = next((k for k, v in REGION_MAP.items() if v == region_id), str(region_id))
                    
                    if min_sell and "sell_below" in item and min_sell <= item["sell_below"]:
                        self.send_alert(f"{item['name']}({region_name})", "卖单跌破下限", min_sell, item["sell_below"])
                    if max_buy and "buy_above" in item and max_buy >= item["buy_above"]:
                        self.send_alert(f"{item['name']}({region_name})", "买单突破上限", max_buy, item["buy_above"])
                        
                    time.sleep(REQUEST_DELAY)
                except Exception as e:
                    logger.debug(f"[监控] ⚠️ 检查 {item.get('name')} 时出错: {e}")
                    time.sleep(1)
            for _ in range(self.interval):
                if not self.running: break
                time.sleep(1)

    def start(self):
        if self.running: print("⚠️ 监控已在运行中"); return
        self.running = True
        self.thread = threading.Thread(target=self._check_prices, daemon=True)
        self.thread.start()

    def stop(self):
        if not self.running: print("⚠️ 监控未启动"); return
        self.running = False
        if self.thread: self.thread.join(timeout=5)
        logger.info("[监控] 🔴 价格监控已停止")

    def add_item(self, type_id, name, sell_below=None, buy_above=None, region_id=None):
        rid = region_id or DEFAULT_REGION_ID
        # 按 (物品ID + 星域ID) 组合去重
        self.watchlist = [i for i in self.watchlist if not (i["id"] == type_id and i.get("region_id", DEFAULT_REGION_ID) == rid)]
        new_item = {"id": type_id, "name": name, "region_id": rid}
        if sell_below is not None: new_item["sell_below"] = sell_below
        if buy_above is not None: new_item["buy_above"] = buy_above
        if len(new_item) <= 3: print("⚠️ 至少需要设置一个阈值"); return
        self.watchlist.append(new_item)
        self.save_config()
        region_name = next((k for k, v in REGION_MAP.items() if v == rid), str(rid))
        print(f"✅ 已添加监控: {name} @ {region_name} (ID:{type_id})")

    def remove_item(self, type_id, region_id=None):
        rid = region_id or DEFAULT_REGION_ID
        before = len(self.watchlist)
        self.watchlist = [i for i in self.watchlist if not (i["id"] == type_id and i.get("region_id", DEFAULT_REGION_ID) == rid)]
        if len(self.watchlist) < before:
            self.save_config(); print(f"✅ 已移除监控 ID:{type_id} @ {rid}")
        else:
            print(f"⚠️ 未找到对应监控项")

    def show_list(self):
        if not self.watchlist: print("📭 当前无监控项"); return
        print("\n📋 当前监控列表:")
        print("-" * 70)
        for i, item in enumerate(self.watchlist, 1):
            region_name = next((k for k, v in REGION_MAP.items() if v == item.get("region_id", DEFAULT_REGION_ID)), str(item.get("region_id")))
            sell = f"卖≤{item['sell_below']:,.0f}" if 'sell_below' in item else "-"
            buy = f"买≥{item['buy_above']:,.0f}" if 'buy_above' in item else "-"
            print(f"  {i}. {item['name']} (ID:{item['id']}) @ {region_name} | {sell} | {buy}")
        print("-" * 70)

    def import_from_excel(self, file_path):
        if not os.path.exists(file_path): print(f"❌ 文件不存在: {file_path}"); return
        try: df = pd.read_excel(file_path)
        except Exception as e: print(f"❌ Excel读取失败: {e}"); return
        
        col_map = {
            '物品ID': 'id', 'type_id': 'id', 'id': 'id',
            '物品名称': 'name', 'name': 'name',
            '星域': 'region', 'region': 'region', '区域': 'region',
            '卖单阈值': 'sell_below', 'sell_below': 'sell_below', '最低卖价提醒': 'sell_below',
            '买单阈值': 'buy_above', 'buy_above': 'buy_above', '最高买价提醒': 'buy_above'
        }
        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
        if not {'id', 'name'}.issubset(df.columns):
            print(f"❌ Excel缺少必要列(物品ID, 物品名称)。当前列: {list(df.columns)}"); return

        success, skip = 0, 0
        for _, row in df.iterrows():
            try:
                tid = int(row['id']); name = str(row['name']).strip()
                sell_val = float(row['sell_below']) if pd.notna(row.get('sell_below')) else None
                buy_val = float(row['buy_above']) if pd.notna(row.get('buy_above')) else None
                
                region_raw = str(row.get('region', '')).strip().lower()
                parsed_region = REGION_MAP.get(region_raw, DEFAULT_REGION_ID)
                try: parsed_region = int(region_raw)
                except: pass
                
                if sell_val is None and buy_val is None: skip += 1; continue
                self.add_item(tid, name, sell_val, buy_val, parsed_region)
                success += 1
            except (ValueError, TypeError): skip += 1; continue
            
        print(f"\n✅ 导入完成! 成功: {success} 条 | 跳过: {skip} 条")
        if self.running: print("💡 监控运行中，新规则将在下一轮自动生效")

    def export_to_excel(self, file_path):
        if not self.watchlist: print("📭 监控列表为空，无需导出"); return False
        try:
            export_data = []
            for item in self.watchlist:
                region_name = next((k for k, v in REGION_MAP.items() if v == item.get("region_id", DEFAULT_REGION_ID)), str(item.get("region_id")))
                export_data.append({
                    "物品ID": item["id"], "物品名称": item["name"], "星域": region_name,
                    "卖单阈值": item.get("sell_below", ""), "买单阈值": item.get("buy_above", "")
                })
            df = pd.DataFrame(export_data)
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='监控列表', index=False)
                ws = writer.sheets['监控列表']
                for col in ws.columns:
                    max_len = max(len(str(cell.value or "")) for cell in col)
                    ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 35)
            print(f"\n✅ 已导出 {len(export_data)} 条至: {file_path}")
            return True
        except PermissionError: print(f"❌ 文件被占用，请关闭后重试"); return False
        except Exception as e: print(f"❌ 导出失败: {e}"); return False


# ================= 基础数据获取模块 =================
def fetch_all_types():
    all_types, page = [], 1
    logger.info("[物品] 🚀 开始获取全物品列表...")
    try:
        resp = requests.get(f"{ESI_BASE}/universe/types/", params={"page": page, "language": LANGUAGE}, timeout=30)
        resp.raise_for_status()
    except Exception as e: logger.error(f"[物品] ❌ 首页请求失败: {e}"); return []
    total_pages = int(resp.headers.get("X-Pages", 1)); all_types.extend(resp.json())
    for page in range(2, total_pages + 1):
        for retry in range(3):
            try:
                resp = requests.get(f"{ESI_BASE}/universe/types/", params={"page": page, "language": LANGUAGE}, timeout=30)
                resp.raise_for_status(); all_types.extend(resp.json()); time.sleep(REQUEST_DELAY); break
            except Exception as e:
                if retry < 2: time.sleep(5)
                else: logger.error(f"[物品] ❌ 第{page}页最终失败")
        if page % 100 == 0: logger.info(f"[物品] ⏳ 进度: {page}/{total_pages}")
    return all_types

def update_types(force=False):
    cache_exists = os.path.exists(TYPES_CACHE)
    need_fetch = force or not cache_exists
    if cache_exists and not force:
        hours = (time.time() - os.path.getmtime(TYPES_CACHE)) / 3600
        need_fetch = hours >= CACHE_VALID_HOURS
    if need_fetch:
        types_data = fetch_all_types()
        if types_data: pd.DataFrame(types_data).to_csv(TYPES_CACHE, index=False); logger.info("[物品] 💾 缓存已更新")
        elif cache_exists: logger.warning("[物品] ⚠️ 拉取失败，沿用旧缓存")
        else: logger.error("[物品] ❌ 首次拉取失败"); return False
    df = pd.read_csv(TYPES_CACHE)
    col_map = {'type_id': '物品ID', 'name': '物品名称', 'group_id': '分组ID', 'published': '是否上架市场'}
    result_df = df[[c for c in col_map if c in df.columns]].rename(columns=col_map)
    market_df = result_df[result_df['是否上架市场']==True].drop(columns=['是否上架市场'])
    try:
        out_path = os.path.join(BASE_DIR, "EVE国服物品列表.xlsx")
        with pd.ExcelWriter(out_path, engine='openpyxl') as w:
            market_df.to_excel(w, sheet_name='市场物品', index=False)
            result_df.to_excel(w, sheet_name='全部物品', index=False)
        logger.info(f"[物品] ✅ 表格已生成 (市场:{len(market_df)})"); return True
    except PermissionError: logger.error("[物品] ❌ Excel被占用"); return False

def query_market():
    if not os.path.exists(TYPES_CACHE): logger.error("[市场] ❌ 请先执行菜单1更新物品"); return False
    df_types = pd.read_csv(TYPES_CACHE)
    name_map = dict(zip(df_types['type_id'], df_types['name']))
    
    print("\nA.全星域拉取(吉他) | B.指定物品ID")
    choice = input("选择(默认A): ").strip().upper()
    target_ids = None
    if choice == 'B':
        raw = input("输入物品ID(逗号分隔): ").strip()
        try: target_ids = [int(x.strip()) for x in raw.split(",") if x.strip()]
        except: logger.error("[市场] ❌ ID格式错误"); return False
    
    orders = []
    if target_ids:
        for tid in target_ids:
            try:
                r = requests.get(f"{ESI_BASE}/markets/{DEFAULT_REGION_ID}/orders/", params={"type_id": tid}, timeout=30)
                orders.extend(r.json()); time.sleep(REQUEST_DELAY)
            except: pass
    else:
        page = 1
        while True:
            try:
                r = requests.get(f"{ESI_BASE}/markets/{DEFAULT_REGION_ID}/orders/", params={"page": page}, timeout=30)
                data = r.json()
                if not data: break
                orders.extend(data); time.sleep(REQUEST_DELAY); page += 1
            except: time.sleep(5)
    
    if not orders: logger.warning("[市场] ⚠️ 无订单"); return False
    df = pd.DataFrame(orders)
    sell = df[~df['is_buy_order']].groupby('type_id')['price'].min().reset_index(name='最低卖价')
    buy = df[df['is_buy_order']].groupby('type_id')['price'].max().reset_index(name='最高买价')
    price_df = pd.merge(sell, buy, on='type_id', how='outer')
    price_df.insert(0, '物品名称', price_df['type_id'].map(name_map))
    price_df = price_df.rename(columns={'type_id':'物品ID'}).sort_values(['物品名称','物品ID'], na_position='last')
    try:
        out_path = os.path.join(BASE_DIR, "EVE国服市场价格.xlsx")
        with pd.ExcelWriter(out_path, engine='openpyxl') as w:
            price_df.to_excel(w, sheet_name='市场价格', index=False)
        logger.info(f"[市场] ✅ 价格表已生成 ({len(price_df)}个物品)"); return True
    except PermissionError: logger.error("[市场] ❌ Excel被占用"); return False


# ================= 交互菜单系统 =================
monitor = PriceMonitor()

def monitor_menu():
    while True:
        status = "🟢 运行中" if monitor.running else "🔴 已停止"
        print(f"\n--- 价格监控 ({status}) ---")
        print("  1. 启动/停止监控")
        print("  2. 添加单个监控项")
        print("  3. 移除监控项")
        print("  4. 查看监控列表")
        print("  5. 修改检查间隔")
        print("  6. 📥 从Excel批量导入")
        print("  7. 📤 导出监控列表到Excel")
        print("  0. 返回主菜单")
        c = input("选择: ").strip()

        if c == '1': 
            if monitor.running: monitor.stop()
            else: monitor.start()
        elif c == '2':
            try:
                tid = int(input("物品ID: ").strip())
                name = input("物品名称: ").strip()
                region_input = input(f"星域(留空默认吉他,支持中文如'多美'): ").strip()
                region_id = DEFAULT_REGION_ID
                if region_input:
                    parsed = REGION_MAP.get(region_input.lower())
                    if parsed: region_id = parsed
                    else:
                        try: region_id = int(region_input)
                        except: print(f"⚠️ 无法识别'{region_input}'，已使用默认吉他")
                sell = input("卖单低于此价提醒(留空跳过): ").strip()
                buy = input("买单高于此价提醒(留空跳过): ").strip()
                monitor.add_item(tid, name, float(sell) if sell else None, float(buy) if buy else None, region_id)
            except ValueError: print("⚠️ 输入格式错误")
        elif c == '3':
            try: 
                tid = int(input("要移除的物品ID: ").strip())
                region_input = input("所在星域(留空默认吉他): ").strip()
                rid = DEFAULT_REGION_ID
                if region_input:
                    parsed = REGION_MAP.get(region_input.lower())
                    if parsed: rid = parsed
                    else:
                        try: rid = int(region_input)
                        except: pass
                monitor.remove_item(tid, rid)
            except: print("⚠️ 请输入有效数字")
        elif c == '4': monitor.show_list()
        elif c == '5':
            try:
                sec = int(input("新间隔(秒,建议≥300): ").strip())
                monitor.interval = max(60, sec); monitor.save_config()
                print(f"✅ 间隔已设为 {monitor.interval}秒")
            except: print("⚠️ 无效输入")
        elif c == '6':
            default_path = os.path.join(BASE_DIR, "price_watchlist_import.xlsx")
            path = input(f"Excel路径(回车使用默认): ").strip() or default_path
            monitor.import_from_excel(path)
        elif c == '7':
            default_export = os.path.join(BASE_DIR, "price_watchlist_export.xlsx")
            path = input(f"导出路径(回车使用默认): ").strip() or default_export
            monitor.export_to_excel(path)
        elif c == '0': break
        else: print("⚠️ 无效输入")
        if c != '0': input("\n按回车键继续...")

def show_menu():
    print("\n" + "=" * 45)
    print("       EVE 国服数据工具箱 v3.0")
    print("=" * 45)
    print("  1. 更新物品列表")
    print("  2. 查询市场价格")
    print("  3. 💰 价格监控管理 (支持多星域)")
    print("  4. 强制刷新物品缓存")
    print("  0. 退出程序")
    print("-" * 45)

def main():
    logger.info("EVE国服数据工具箱 v3.0 启动")
    while True:
        show_menu()
        choice = input("请选择 [0-4]: ").strip()
        if choice == '1': update_types(force=False)
        elif choice == '2': query_market()
        elif choice == '3': monitor_menu()
        elif choice == '4': update_types(force=True)
        elif choice == '0': monitor.stop(); logger.info("程序正常退出"); break
        else: print("⚠️ 无效输入")
        input("\n按回车键返回主菜单...")

if __name__ == "__main__":
    main()