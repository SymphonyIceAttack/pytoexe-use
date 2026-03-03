import sys
import os
import time
import ctypes
import osrparse
from pynput import mouse, keyboard
import win32gui
import win32con
import win32api
import win32com.client

# --- DPI 感知 ---
try:
    ctypes.windll.user32.SetProcessDPIAware()
except:
    pass

# --- 設定參數 ---
FIXED_SCALE = 2.2 
song_offset = 1000 
OFFSET_STEP = 10  # 10ms 微調

def find_osu_hwnd():
    """找到 osu! 視窗控制代碼"""
    hwnds = []
    def enum_cb(hwnd, lParam):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title.startswith("osu!"):
                lParam.append(hwnd)
        return True
    win32gui.EnumWindows(enum_cb, hwnds)
    return hwnds[0] if hwnds else None

def logical_to_screen(hwnd, lx, ly):
    """將遊戲邏輯座標轉為螢幕像素座標"""
    try:
        client_rect = win32gui.GetClientRect(hwnd)
        client_w, client_h = client_rect[2], client_rect[3]
        playfield_w = 512 * FIXED_SCALE
        playfield_h = 384 * FIXED_SCALE
        offset_x = (client_w - playfield_w) / 2
        offset_y = (client_h - playfield_h) / 2
        client_tl = win32gui.ClientToScreen(hwnd, (0, 0))
        sx = client_tl[0] + offset_x + lx * FIXED_SCALE
        sy = client_tl[1] + offset_y + ly * FIXED_SCALE
        return int(sx), int(sy)
    except:
        return 0, 0

# --- 全局狀態 ---
start_flag = False
stop_flag = False

def on_press(key):
    global start_flag, stop_flag, song_offset
    try:
        if key == keyboard.Key.home:
            start_flag = True
        elif key == keyboard.Key.end:
            stop_flag = True
            print(f"\n[已停止] 目前額外延遲 Offset: {song_offset}ms")
        elif key == keyboard.Key.page_up:
            song_offset += OFFSET_STEP
            print(f"[調整] Offset +{OFFSET_STEP}ms -> 動作變慢，當前: {song_offset}ms")
        elif key == keyboard.Key.page_down:
            song_offset -= OFFSET_STEP
            print(f"[調整] Offset -{OFFSET_STEP}ms -> 動作變快，當前: {song_offset}ms")
    except: pass

# --- 主程式 ---
if __name__ == "__main__":
    print("========================================")
    print("   Osu! Replay Bot - 終極絲滑版")
    print("   (含插值優化、10ms微調、自訂等待)")
    print("========================================")

    if len(sys.argv) > 1:
        osr_path = sys.argv[1].strip().strip('"')
    else:
        osr_path = input("請將 .osr 檔案拖入此視窗，並按回車: ").strip().strip('"')
    
    if not os.path.exists(osr_path):
        print("錯誤：檔案路徑不存在！"); time.sleep(3); sys.exit()

    print(f"\n[1/3] 正在解析: {os.path.basename(osr_path)}")
    try:
        replay = osrparse.Replay.from_path(osr_path)
    except Exception as e:
        print(f"解析失敗: {e}"); input(); sys.exit()
    
    # 預計算累計時間，用於絲滑插值
    events = replay.replay_data
    processed_events = []
    total_ms = 0
    for e in events:
        total_ms += e.time_delta
        processed_events.append({'t': total_ms, 'x': e.x, 'y': e.y, 'k': e.keys})
        
    dt_mode = input("是否開啟 DT 模式？(y/n): ").lower() == 'y'
    wait_for_space = input("Enter后是否等待2s按空白键？(y/n): ").lower() == 'y'
    
    offset_val = input(f"初始 Offset (毫秒, 預設 {song_offset}): ").strip()
    if offset_val: song_offset = int(offset_val)

    hwnd = find_osu_hwnd()
    if not hwnd:
        print("未找到 osu! 視窗！"); input(); sys.exit()

    print("\n[就緒] 腳本已激活。")
    print(" -> HOME 開始 | END 停止")
    print(f" -> PGUP +{OFFSET_STEP}ms | PGDN -{OFFSET_STEP}ms")
    
    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    while True:
        while not start_flag: time.sleep(0.1)
        start_flag, stop_flag = False, False
        
        m_ctrl, k_ctrl = mouse.Controller(), keyboard.Controller()
        
        # 1. 預備第一幀位置
        first_e = processed_events[0]
        fsx, fsy = logical_to_screen(hwnd, first_e['x'], first_e['y'])
        m_ctrl.position = (fsx, fsy)
        
        # 2. 激活視窗並啟動
        shell = win32com.client.Dispatch("WScript.Shell")
        shell.SendKeys('%') 
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.3)
        
        print(">>> 按下 Enter...")
        win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0); time.sleep(0.05)
        win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
        
        if wait_for_space:
            print(">>> 等待 2.0 秒按下空白鍵...")
            time.sleep(2.0) 
            win32api.keybd_event(win32con.VK_SPACE, 0, 0, 0); time.sleep(0.05)
            win32api.keybd_event(win32con.VK_SPACE, 0, win32con.KEYEVENTF_KEYUP, 0)

        # 3. 絲滑重放開始
        start_time = time.perf_counter() * 1000 + song_offset
        idx = 0
        prev_keys = 0
        event_count = len(processed_events)

        print(f">>> 正在重放 (Offset: {song_offset}ms)...")
        try:
            while idx < event_count - 1:
                if stop_flag: break
                
                # 計算當前應該在的時間進度
                now = (time.perf_counter() * 1000) - start_time
                if dt_mode: now *= 1.5  # DT 模式下時間流逝快 1.5 倍

                # 尋找當前時間落在錄像的哪個區間
                while idx < event_count - 1 and now > processed_events[idx+1]['t']:
                    idx += 1
                
                curr_e = processed_events[idx]
                next_e = processed_events[idx+1]
                
                # --- 絲滑插值計算 ---
                time_gap = next_e['t'] - curr_e['t']
                if time_gap > 0:
                    # 計算目前時間在區間內的百分比 (0.0 ~ 1.0)
                    ratio = (now - curr_e['t']) / time_gap
                    ratio = max(0, min(1, ratio))
                    # 根據比例算出中間座標
                    interp_x = curr_e['x'] + (next_e['x'] - curr_e['x']) * ratio
                    interp_y = curr_e['y'] + (next_e['y'] - curr_e['y']) * ratio
                else:
                    interp_x, interp_y = curr_e['x'], curr_e['y']

                sx, sy = logical_to_screen(hwnd, interp_x, interp_y)
                m_ctrl.position = (sx, sy)

                # 按鍵處理 (只在跨越數據點時檢查，避免頻繁發送 API 調用)
                k = curr_e['k']
                if k != prev_keys:
                    m1 = bool(k & 1) or bool(k & 4)
                    pm1 = bool(prev_keys & 1) or bool(prev_keys & 4)
                    x_k = bool(k & 2) or bool(k & 8)
                    px_k = bool(prev_keys & 2) or bool(prev_keys & 8)
                    
                    if m1 != pm1: m_ctrl.press(mouse.Button.left) if m1 else m_ctrl.release(mouse.Button.left)
                    if x_k != px_k: k_ctrl.press('x') if x_k else k_ctrl.release('x')
                    prev_keys = k
                
                # 極短休眠確保高刷新率且不吃爆 CPU
                time.sleep(0.001)

        except Exception as err:
            print(f"運行異常: {err}")
        finally:
            m_ctrl.release(mouse.Button.left)
            k_ctrl.release('x')
            print("<<< 重放結束。")