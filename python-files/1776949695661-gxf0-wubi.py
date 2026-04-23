import serial
import time
import tkinter as tk
from tkinter import ttk, messagebox
import os
import threading
import sys  # 新增：处理PyInstaller打包后的路径

# ========== 配置 ==========
BAUDRATE = 9600
DEFAULT_DELAY_MS = 100
# 适配PyInstaller打包后的路径（优先当前目录，无则找打包后的临时目录）
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS  # PyInstaller打包后的临时目录
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WUBI_FILE = os.path.join(BASE_DIR, "wubi.txt")

WUBI_DICT = {}
stop_flag = False  # 停止标志
ser = None  # 串口对象

# 加载五笔词库（兼容3.7+，异常捕获更明确）
def load_wubi_file():
    global WUBI_DICT
    WUBI_DICT.clear()
    if not os.path.exists(WUBI_FILE):
        return False
    try:
        with open(WUBI_FILE, "r", encoding="utf-8") as f:
            for line in f:  # 逐行读取，降低内存占用（3.7+推荐）
                line = line.strip()
                if not line or "=" not in line:
                    continue
                hz, code = line.split("=", 1)
                hz = hz.strip()
                code = code.strip()
                if hz and code:
                    WUBI_DICT[hz] = code
        return True
    except Exception as e:  # 明确捕获异常（3.7+规范）
        print(f"加载词库失败: {e}")
        return False

# CH9329校验和（无改动，兼容3.7+）
def checksum(data):
    return sum(data) & 0xFF

# 全按键释放指令
BASE_RELEASE = [0x57, 0xAB, 0x00, 0x02, 0x08, 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00]
RELEASE_CMD = bytes(BASE_RELEASE + [checksum(BASE_RELEASE)])

# 纯单键扫描码（无Shift）
KEY_CODE = {
    # 字母
    'a':0x04,'b':0x05,'c':0x06,'d':0x07,'e':0x08,'f':0x09,'g':0x0A,
    'h':0x0B,'i':0x0C,'j':0x0D,'k':0x0E,'l':0x0F,'m':0x10,'n':0x11,
    'o':0x12,'p':0x13,'q':0x14,'r':0x15,'s':0x16,'t':0x17,'u':0x18,
    'v':0x19,'w':0x1A,'x':0x1B,'y':0x1C,'z':0x1D,
    # 数字
    '0':0x27,'1':0x1E,'2':0x1F,'3':0x20,'4':0x21,'5':0x22,
    '6':0x23,'7':0x24,'8':0x25,'9':0x26,
    # 纯单键符号
    ' ':0x2C, '-':0x2D, '=':0x2E, '[':0x2F, ']':0x30, '\\':0x31,
    ';':0x33, '\'':0x34, '`':0x35, ',':0x36, '.':0x37, '/':0x38,
    # 回车
    '\n':0x28
}

# 获取串口列表（兼容3.7+，优化异常处理）
def get_ports():
    try:
        import serial.tools.list_ports
        return [p.device for p in serial.tools.list_ports.comports()]
    except ImportError:
        messagebox.showerror("依赖缺失", "未找到pyserial库，请安装：pip install pyserial")
        return []
    except Exception as e:
        messagebox.showerror("获取串口失败", str(e))
        return []

# 构造单键指令（无改动）
def make_key_cmd(key_sc):
    frame = [0x57, 0xAB, 0x00, 0x02, 0x08,
             0x00, 0x00,0x00,0x00,0x00,0x00,0x00, key_sc]
    frame.append(checksum(frame))
    return bytes(frame)

# 获取延迟（3.7+优化类型处理）
def get_delay_sec():
    try:
        ms = int(delay_entry.get().strip())
        ms = max(ms, 1)  # 防止输入0或负数
    except (ValueError, TypeError):  # 明确捕获类型错误
        ms = DEFAULT_DELAY_MS
        # 主线程安全更新UI（3.7+规范）
        delay_entry.delete(0, tk.END)
        delay_entry.insert(0, str(DEFAULT_DELAY_MS))
    return ms / 1000.0  # 确保浮点型

# 连接串口（优化3.7+的资源管理）
def conn_serial():
    global ser
    port = port_cb.get()
    if not port:
        messagebox.showerror("错误","请选择串口")
        return
    try:
        # 关闭已有连接（防止重复连接）
        if ser and ser.is_open:
            ser.close()
        # 3.7+支持的参数写法
        ser = serial.Serial(
            port=port,
            baudrate=BAUDRATE,
            timeout=0.5,
            write_timeout=0.5  # 新增写超时，避免卡死
        )
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        status_lab.config(text="✅ 已连接", foreground="green")
        send_btn.config(state="normal")
        stop_btn.config(state="disabled")
    except Exception as e:
        messagebox.showerror("连接失败", f"错误信息：{str(e)}")

# 断开串口（优化资源释放）
def dis_serial():
    global ser
    if ser and ser.is_open:
        try:
            ser.write(RELEASE_CMD)  # 断开前释放所有按键
            ser.flush()
        except:
            pass
        ser.close()
    ser = None  # 置空，避免野指针
    status_lab.config(text="未连接", foreground="gray")
    send_btn.config(state="disabled")
    stop_btn.config(state="disabled")

# 停止发送（立即响应）
def stop_send():
    global stop_flag
    stop_flag = True
    # 主线程更新UI（3.7+推荐after方法）
    root.after(0, lambda: stop_btn.config(state="disabled"))

# 纯单键发送（优化3.7+的异常处理）
def send_key(c):
    if c not in KEY_CODE or not ser or not ser.is_open:
        return
    delay = get_delay_sec()
    try:
        cmd = make_key_cmd(KEY_CODE[c])
        ser.write(cmd)
        ser.flush()
        time.sleep(delay)
        ser.write(RELEASE_CMD)
        ser.flush()
        time.sleep(delay/2)
    except Exception as e:
        print(f"发送按键失败: {e}")
        stop_send()  # 发送失败自动停止

# 发送回车（封装）
def send_enter():
    send_key('\n')

# 子线程发送逻辑（3.7+优化线程安全）
def send_thread_func(txt):
    global stop_flag
    try:
        for ch in txt:
            if stop_flag:
                break
            # 英文字母：发送+回车
            if ch.lower() in KEY_CODE and ch.lower() >= 'a' and ch.lower() <= 'z':
                send_key(ch.lower())
                send_enter()
            # 中文：五笔
            elif "\u4e00" <= ch <= "\u9fff":
                if ch in WUBI_DICT:
                    for w in WUBI_DICT[ch]:
                        if stop_flag:
                            break
                        send_key(w)
                    send_key(" ")
            # 数字/符号/回车
            elif ch in KEY_CODE:
                send_key(ch)
    finally:
        # 主线程更新UI（避免线程安全问题）
        def update_ui():
            if stop_flag:
                messagebox.showinfo("停止","已手动停止发送")
            else:
                messagebox.showinfo("完成","发送完毕")
            reset_buttons()
        root.after(0, update_ui)

# 重置按钮状态
def reset_buttons():
    send_btn.config(state="normal")
    stop_btn.config(state="disabled")

# 启动发送（开子线程，不阻塞界面）
def do_send():
    global stop_flag
    stop_flag = False  # 重置停止标志
    
    if not ser or not ser.is_open:
        messagebox.showerror("提示","请先连接串口")
        return
    txt = text_area.get("1.0", tk.END).strip()
    if not txt:
        messagebox.showwarning("提示","请输入内容")
        return

    # 禁用发送，启用停止
    send_btn.config(state="disabled")
    stop_btn.config(state="normal")
    
    # 3.7+推荐使用daemon=True（主线程退出时子线程自动退出）
    thread = threading.Thread(
        target=send_thread_func,
        args=(txt,),
        daemon=True
    )
    thread.start()

# 重载词库
def reload_dict():
    ok = load_wubi_file()
    if ok:
        messagebox.showinfo("成功",f"已加载五笔词库，共{len(WUBI_DICT)}个词条")
    else:
        messagebox.showerror("失败",f"未找到或加载失败：{WUBI_FILE}")

# ========== 界面（3.7+优化） ==========
if __name__ == "__main__":  # 打包必备：避免重复执行
    root = tk.Tk()
    root.title("CH9329纯单键工具（Python3.7+兼容版）")
    root.geometry("620x480")
    root.resizable(False, False)  # 固定窗口大小（可选）
    
    # 提前加载词库
    load_wubi_file()

    # 顶部栏
    top_frame = ttk.Frame(root)
    top_frame.pack(pady=10)
    ttk.Label(top_frame, text="串口：").grid(row=0,column=0,padx=3)
    port_cb = ttk.Combobox(top_frame, values=get_ports(), width=12)
    port_cb.grid(row=0,column=1,padx=3)
    if port_cb["values"]:
        port_cb.current(0)
    ttk.Button(top_frame, text="连接", command=conn_serial).grid(row=0,column=2,padx=3)
    ttk.Button(top_frame, text="断开", command=dis_serial).grid(row=0,column=3,padx=3)
    ttk.Button(top_frame, text="重载词库", command=reload_dict).grid(row=0,column=4,padx=3)
    status_lab = ttk.Label(top_frame, text="未连接", foreground="gray")
    status_lab.grid(row=0,column=5,padx=6)

    # 延迟设置
    delay_frame = ttk.Frame(root)
    delay_frame.pack(pady=5)
    ttk.Label(delay_frame, text="按键延迟(毫秒)：").pack(side="left", padx=5)
    delay_entry = ttk.Entry(delay_frame, width=10)
    delay_entry.pack(side="left")
    delay_entry.insert(0, str(DEFAULT_DELAY_MS))

    # 输入区
    ttk.Label(root, text="输入内容（纯单键：字母/数字/,-=[]\\;',./`/回车）：").pack(anchor="w", padx=15)
    text_area = tk.Text(root, font=("微软雅黑",11), width=72, height=12)
    text_area.pack(padx=15, pady=5)

    # 按钮区
    btn_frame = ttk.Frame(root)
    btn_frame.pack(pady=8)
    send_btn = ttk.Button(btn_frame, text="一键发送打字", command=do_send, state="disabled")
    send_btn.grid(row=0,column=0,padx=10)
    stop_btn = ttk.Button(btn_frame, text="⏹ 停止发送", command=stop_send, state="disabled")
    stop_btn.grid(row=0,column=1,padx=10)

    # 关闭窗口释放串口（3.7+优化）
    def on_close():
        dis_serial()
        root.quit()  # 先退出主循环
        root.destroy()  # 再销毁窗口
    
    root.protocol("WM_DELETE_WINDOW", on_close)
    
    # 主循环（3.7+规范）
    try:
        root.mainloop()
    except KeyboardInterrupt:
        on_close()