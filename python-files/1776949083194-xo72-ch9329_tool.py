import serial
import time
import tkinter as tk
from tkinter import ttk, messagebox
import os
import threading  # 关键：导入线程模块

# ========== 配置 ==========
BAUDRATE = 9600
DEFAULT_DELAY_MS = 100
WUBI_FILE = "wubi.txt"
WUBI_DICT = {}
stop_flag = False  # 停止标志

# 加载五笔词库
def load_wubi_file():
    global WUBI_DICT
    WUBI_DICT.clear()
    if not os.path.exists(WUBI_FILE):
        return False
    try:
        with open(WUBI_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in lines:
            line = line.strip()
            if "=" in line:
                hz, code = line.split("=", 1)
                hz = hz.strip()
                code = code.strip()
                if hz and code:
                    WUBI_DICT[hz] = code
        return True
    except:
        return False

# CH9329校验和
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

ser = None

# 获取串口列表
def get_ports():
    import serial.tools.list_ports
    return [p.device for p in serial.tools.list_ports.comports()]

# 构造单键指令
def make_key_cmd(key_sc):
    frame = [0x57, 0xAB, 0x00, 0x02, 0x08,
             0x00, 0x00,0x00,0x00,0x00,0x00,0x00, key_sc]
    frame.append(checksum(frame))
    return bytes(frame)

# 获取延迟
def get_delay_sec():
    try:
        ms = int(delay_entry.get().strip())
        ms = max(ms, 1)
    except:
        ms = DEFAULT_DELAY_MS
        delay_entry.delete(0, tk.END)
        delay_entry.insert(0, str(DEFAULT_DELAY_MS))
    return ms / 1000

# 连接串口
def conn_serial():
    global ser
    port = port_cb.get()
    if not port:
        messagebox.showerror("错误","请选择串口")
        return
    try:
        ser = serial.Serial(port, BAUDRATE, timeout=0.5)
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        status_lab.config(text="✅ 已连接", foreground="green")
        send_btn.config(state="normal")
        stop_btn.config(state="disabled")
    except Exception as e:
        messagebox.showerror("连接失败", str(e))

# 断开串口
def dis_serial():
    global ser
    if ser and ser.is_open:
        ser.close()
    status_lab.config(text="未连接", foreground="gray")
    send_btn.config(state="disabled")
    stop_btn.config(state="disabled")

# 停止发送（立即响应）
def stop_send():
    global stop_flag
    stop_flag = True
    # 界面更新放到主线程
    root.after(0, lambda: stop_btn.config(state="disabled"))

# 纯单键发送
def send_key(c):
    if c not in KEY_CODE:
        return
    delay = get_delay_sec()
    cmd = make_key_cmd(KEY_CODE[c])
    ser.write(cmd)
    ser.flush()
    time.sleep(delay)
    ser.write(RELEASE_CMD)
    ser.flush()
    time.sleep(delay/2)

# 发送回车
def send_enter():
    send_key('\n')

# ========== 核心：子线程执行发送逻辑（界面不卡顿） ==========
def send_thread_func(txt):
    global stop_flag
    try:
        for ch in txt:
            if stop_flag:
                break
            
            # 英文字母：发送+回车
            if ch.lower() >= 'a' and ch.lower() <= 'z':
                send_key(ch.lower())
                send_enter()
            # 中文：五笔
            elif "\u4e00" <= ch <= "\u9fff":
                if ch in WUBI_DICT:
                    for w in WUBI_DICT[ch]:
                        send_key(w)
                    send_key(" ")
            # 数字/符号/回车
            else:
                send_key(ch)
    finally:
        # 发送结束/停止后，恢复按钮状态（主线程执行）
        if stop_flag:
            root.after(0, lambda: messagebox.showinfo("停止","已手动停止发送"))
        else:
            root.after(0, lambda: messagebox.showinfo("完成","发送完毕"))
        root.after(0, reset_buttons)

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
    
    # 启动子线程发送（关键：界面不卡）
    thread = threading.Thread(target=send_thread_func, args=(txt,), daemon=True)
    thread.start()

# 重载词库
def reload_dict():
    ok = load_wubi_file()
    if ok:
        messagebox.showinfo("成功","已加载五笔词库")
    else:
        messagebox.showerror("失败","未找到wubi.txt")

# ========== 界面 ==========
root = tk.Tk()
root.title("CH9329纯单键工具（子线程+不卡顿+秒停止）")
root.geometry("620x480")
load_wubi_file()

# 顶部栏
top_frame = ttk.Frame(root)
top_frame.pack(pady=10)
ttk.Label(top_frame, text="串口：").grid(row=0,column=0,padx=3)
port_cb = ttk.Combobox(top_frame, values=get_ports(), width=12)
port_cb.grid(row=0,column=1,padx=3)
if port_cb["values"]: port_cb.current(0)
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
delay_entry.insert(0, "100")

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

# 关闭窗口释放串口
def on_close():
    dis_serial()
    root.destroy()
root.protocol("WM_DELETE_WINDOW", on_close)

root.mainloop()