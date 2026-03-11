import pyautogui
import keyboard
import time
import pyperclip

# 配置：只执行一轮 A B C D
answer_list = ["A", "B", "C", "D"]
current_index = 0
is_finished = False  # 发完一轮就锁定

def send_qq_msg(msg):
    """发送消息到QQ激活窗口"""
    pyperclip.copy(msg)
    pyautogui.hotkey("ctrl", "v")
    pyautogui.press("enter")
    time.sleep(0.1)

def start_listen():
    global current_index, is_finished
    last_text = ""
    
    print("=== QQ 自动抢答（一轮版）===")
    print("触发词：抢答开始")
    print("回复：A → B → C → D（发完即停）")
    print("按 ESC 退出\n")

    while True:
        # 退出键
        if keyboard.is_pressed("esc"):
            print("\n程序已退出")
            break

        # 发完一轮就不再响应
        if is_finished:
            time.sleep(0.2)
            continue

        try:
            now_text = pyperclip.paste().strip()

            # 检测关键词
            if now_text != last_text and "抢答开始" in now_text:
                char = answer_list[current_index]
                print(f"触发抢答 → 发送：{char}")

                send_qq_msg(char)

                # 下一个字母
                current_index += 1

                # 发完 D 就停止
                if current_index >= len(answer_list):
                    is_finished = True
                    print("✅ 一轮抢答完成，已停止响应")

                last_text = now_text

        except:
            pass

        time.sleep(0.2)

if __name__ == "__main__":
    start_listen()