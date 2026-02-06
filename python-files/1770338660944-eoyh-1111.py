import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

# ==================== 核心配置 ====================
OFFSET_VERSION = 0x4010   # 版本号位置
MAGIC_OLE = b'\xD0\xCF\x11\xE0'
XOR_KEY = 0xAA 

# 智能标记 (写在文件末尾，用于识别是否已注毒)
POISON_TAG = b'_GHOST_MODE_ACTIVATED_' 

# 版本对应表
VERSION_MAP = {
    # === 🟢 智能恢复区 ===
    # 智能逻辑：检测到有毒才解毒，没毒只改版本
    "🟢 2016 (智能恢复)": (18000, b'\x50\x46\x00\x00'),
    "🟢 2024 (智能恢复)": (26000, b'\x90\x65\x00\x00'),
    "🟢 2026 (智能恢复)": (28000, b'\x60\x6D\x00\x00'),
    "🟢 2027 (智能恢复)": (29000, b'\x48\x71\x00\x00'),
    "🟢 2028 (智能恢复)": (30000, b'\x30\x75\x00\x00'),
    
    # === 💀 验证测试区 ===
    # 强制注毒，用于验证效果
    "💀 验证模式 (版本2024 + 强制剧毒)": (26000, b'\x90\x65\x00\x00'),
    
    # === 🟣 未来陷阱区 ===
    # 强制注毒
    "🟣 2026 (伪装2026 + 强制剧毒)": (28000, b'\x60\x6D\x00\x00'),
    "🟣 2028 (伪装2028 + 强制剧毒)": (30000, b'\x30\x75\x00\x00')
}

BACKUP_ROOT_NAME = "_Backup_Originals"

class MaxFakerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("3ds Max 伪装器 v12.0 (智能防误伤版)")
        self.root.geometry("600x680")
        
        self.target_folder = os.path.dirname(os.path.abspath(__file__))

        # === 界面 ===
        frame_top = tk.Frame(root, pady=10)
        frame_top.pack(fill="x")
        tk.Label(frame_top, text="📂 扫描目录:", fg="gray").pack()
        tk.Label(frame_top, text=self.target_folder, fg="blue", wraplength=580).pack()

        frame_select = tk.LabelFrame(root, text="🛡️ 模式选择", font=("微软雅黑", 10, "bold"))
        frame_select.pack(pady=5, padx=15, fill="x")

        self.selected_ver = tk.StringVar()
        self.selected_ver.set("🟣 2028 (伪装2028 + 强制剧毒)")

        for ver_name in VERSION_MAP.keys():
            color = "black"
            if "伪装" in ver_name: color = "#673AB7"
            if "验证" in ver_name: color = "#D32F2F"
            if "恢复" in ver_name: color = "#4CAF50"
            
            rb = ttk.Radiobutton(frame_select, text=ver_name, variable=self.selected_ver, value=ver_name)
            rb.pack(anchor="w", padx=20, pady=3)

        info_text = (
            "✨ v12.0 智能升级：\n"
            "1. 【智能防误伤】：\n"
            "   选 '恢复' 模式时，程序会自动检测文件是否真的被毒过。\n"
            "   - 如果是干净文件 -> 只改版本号，不碰数据 (安全！)。\n"
            "   - 如果是中毒文件 -> 自动解毒。\n"
            "2. 【状态标记】：\n"
            "   注毒时会在文件末尾添加隐形标签，确保识别准确。"
        )
        tk.Label(frame_select, text=info_text, fg="#009688", justify="left", font=("微软雅黑", 8)).pack(pady=5, padx=10)

        btn_run = tk.Button(root, text="执行智能处理", bg="#009688", fg="white", 
                            font=("微软雅黑", 12, "bold"), command=self.run_process)
        btn_run.pack(pady=10, ipadx=40)

        self.log_area = scrolledtext.ScrolledText(root, height=10, state='disabled', font=("Consolas", 9))
        self.log_area.pack(padx=15, pady=5, fill="both", expand=True)

    def log(self, message):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')
        self.root.update()

    def fix_header_force(self, f):
        f.seek(0)
        header = f.read(4)
        if header != MAGIC_OLE:
            f.seek(0)
            data = f.read(8)
            decrypted = bytes([b ^ 0xFF for b in data]) 
            if decrypted[:4] == MAGIC_OLE:
                f.seek(0)
                f.write(decrypted)
                return "✨ 头已修复"
        return ""

    def check_is_poisoned(self, f):
        """ 检查文件末尾是否有毒药标签 """
        try:
            f.seek(-len(POISON_TAG), 2) # 倒数移动
            tag = f.read(len(POISON_TAG))
            return tag == POISON_TAG
        except:
            return False

    def carpet_bombing_smart(self, f, mode):
        """ 智能地毯式处理 """
        
        is_already_poisoned = self.check_is_poisoned(f)

        # === 逻辑判断 ===
        if mode == 'inject': # 意图：注毒
            if is_already_poisoned:
                return "⏭ 已有毒(跳过)" # 防止重复注毒导致解毒
            
            # 执行注毒
            self._apply_xor(f)
            # 打上标签
            f.seek(0, 2)
            f.write(POISON_TAG)
            return "💉 已注毒(加标)"

        elif mode == 'cure': # 意图：解毒
            if not is_already_poisoned:
                return "✨ 原本干净(跳过)" # 关键！防止误伤正常文件
            
            # 执行解毒
            self._apply_xor(f)
            # 撕掉标签 (截断文件)
            f.seek(0, 2)
            current_size = f.tell()
            new_size = current_size - len(POISON_TAG)
            f.truncate(new_size)
            return "💊 已解毒(去标)"
            
        return "未知操作"

    def _apply_xor(self, f):
        """ 实际执行异或操作 (仅内部调用) """
        f.seek(0, 2)
        file_size = f.tell()
        # 如果有标签，处理范围要排除标签
        if self.check_is_poisoned(f):
            file_size -= len(POISON_TAG)

        start_offset = 0x5000 
        step = 4096 
        bomb_size = 64 
        
        current_pos = start_offset
        while current_pos < file_size:
            f.seek(current_pos)
            data = f.read(bomb_size)
            if len(data) > 0:
                processed_data = bytes([b ^ XOR_KEY for b in data])
                f.seek(current_pos)
                f.write(processed_data)
            current_pos += step

    def run_process(self):
        choice = self.selected_ver.get()
        target_ver_num, target_bytes = VERSION_MAP[choice]
        
        # 判定意图
        intent_mode = 'inject' if ("剧毒" in choice) else 'cure'

        self.log("=" * 50)
        self.log(f"开始... 目标: {choice}")
        self.log("=" * 50)

        count = 0
        
        for root, dirs, files in os.walk(self.target_folder):
            if BACKUP_ROOT_NAME in root: continue

            for filename in files:
                if filename.lower().endswith(".max"):
                    file_path = os.path.join(root, filename)
                    
                    try:
                        status_msg = []
                        with open(file_path, 'r+b') as f:
                            # 1. 修复头
                            header_msg = self.fix_header_force(f)
                            if header_msg: status_msg.append(header_msg)

                            # 2. 改版本
                            f.seek(OFFSET_VERSION)
                            f.write(target_bytes)
                            
                            # 3. 智能注毒/解毒
                            msg = self.carpet_bombing_smart(f, intent_mode)
                            status_msg.append(msg)

                        action = "☠️ 加密" if intent_mode == 'inject' else "🍀 恢复"
                        extra = f" | {' '.join(status_msg)}" if status_msg else ""
                        self.log(f"[{action}] {filename}{extra}")
                        count += 1

                    except Exception as e:
                        self.log(f"❌ {filename}: {e}")

        messagebox.showinfo("完成", f"处理结束！共 {count} 个文件。\n\n✅ 智能模式已生效：\n现在你可以放心点击'恢复'，\n绝对不会把干净的文件搞坏了！")

if __name__ == "__main__":
    root = tk.Tk()
    app = MaxFakerApp(root)
    root.mainloop()