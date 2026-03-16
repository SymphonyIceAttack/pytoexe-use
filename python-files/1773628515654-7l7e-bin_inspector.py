import os
import shutil
import hashlib
import zlib
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

SERIAL_LENGTH = 9
TARGET_OFFSET = 0


def bytes_to_hex(data: bytes) -> str:
    return " ".join(f"{b:02X}" for b in data)


def file_hash(path: str, algo: str) -> str:
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def safe_ascii(data: bytes) -> str:
    return "".join(chr(b) if 32 <= b <= 126 else "." for b in data)


def inspect_bin(path: str) -> dict:
    if not os.path.isfile(path):
        raise FileNotFoundError("文件不存在")

    with open(path, "rb") as f:
        raw = f.read()

    size = len(raw)
    serial_bytes = raw[TARGET_OFFSET:TARGET_OFFSET + SERIAL_LENGTH]
    serial_ascii = safe_ascii(serial_bytes)

    head_len = min(64, size)
    tail_len = min(64, size)

    head = raw[:head_len]
    tail = raw[-tail_len:] if size else b""

    crc32_all = zlib.crc32(raw) & 0xFFFFFFFF
    crc32_without_last4 = None
    tail_last4_le = None
    tail_last4_be = None
    crc32_match_le = False
    crc32_match_be = False

    if size >= 4:
        body = raw[:-4]
        last4 = raw[-4:]
        crc32_without_last4 = zlib.crc32(body) & 0xFFFFFFFF
        tail_last4_le = int.from_bytes(last4, "little")
        tail_last4_be = int.from_bytes(last4, "big")
        crc32_match_le = crc32_without_last4 == tail_last4_le
        crc32_match_be = crc32_without_last4 == tail_last4_be

    return {
        "path": path,
        "size": size,
        "serial_ascii": serial_ascii,
        "serial_hex": bytes_to_hex(serial_bytes),
        "md5": file_hash(path, "md5"),
        "sha256": file_hash(path, "sha256"),
        "head_hex": bytes_to_hex(head),
        "head_ascii": safe_ascii(head),
        "tail_hex": bytes_to_hex(tail),
        "tail_ascii": safe_ascii(tail),
        "crc32_all": f"{crc32_all:08X}",
        "crc32_without_last4": None if crc32_without_last4 is None else f"{crc32_without_last4:08X}",
        "tail_last4_le": None if tail_last4_le is None else f"{tail_last4_le:08X}",
        "tail_last4_be": None if tail_last4_be is None else f"{tail_last4_be:08X}",
        "crc32_match_le": crc32_match_le,
        "crc32_match_be": crc32_match_be,
    }


def make_backup(path: str) -> str:
    if not os.path.isfile(path):
        raise FileNotFoundError("文件不存在")
    backup_path = path + ".bak"
    shutil.copy2(path, backup_path)
    return backup_path


def build_report(info: dict) -> str:
    lines = [
        "BIN 文件分析报告",
        "=" * 50,
        f"文件: {info['path']}",
        f"大小: {info['size']} bytes",
        "",
        f"偏移 0x00000000 的前 {SERIAL_LENGTH} 字节 ASCII: {info['serial_ascii']}",
        f"偏移 0x00000000 的前 {SERIAL_LENGTH} 字节 HEX  : {info['serial_hex']}",
        "",
        f"MD5    : {info['md5']}",
        f"SHA256 : {info['sha256']}",
        "",
        "文件头(前64字节以内)",
        f"HEX   : {info['head_hex']}",
        f"ASCII : {info['head_ascii']}",
        "",
        "文件尾(后64字节以内)",
        f"HEX   : {info['tail_hex']}",
        f"ASCII : {info['tail_ascii']}",
        "",
        "CRC32 检查",
        f"整文件 CRC32                : {info['crc32_all']}",
        f"除去最后4字节后的 CRC32     : {info['crc32_without_last4']}",
        f"最后4字节按小端解释         : {info['tail_last4_le']}",
        f"最后4字节按大端解释         : {info['tail_last4_be']}",
        f"是否匹配(小端)              : {info['crc32_match_le']}",
        f"是否匹配(大端)              : {info['crc32_match_be']}",
        "",
        "说明:",
        "1. 该工具只读分析，不修改 BIN 文件。",
        "2. 结果仅用于查看序列号、哈希和常见 CRC32 特征。",
    ]
    return "\n".join(lines)


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("BIN 只读分析工具")
        self.root.geometry("820x620")
        self.root.resizable(True, True)

        self.file_var = tk.StringVar()

        self.build_ui()

    def build_ui(self):
        top = tk.Frame(self.root)
        top.pack(fill="x", padx=10, pady=10)

        tk.Label(top, text="BIN 文件:").pack(side="left")
        tk.Entry(top, textvariable=self.file_var, width=70).pack(side="left", padx=8)
        tk.Button(top, text="选择文件", command=self.choose_file, width=12).pack(side="left")
        tk.Button(top, text="生成备份", command=self.backup_file, width=12).pack(side="left", padx=6)
        tk.Button(top, text="开始分析", command=self.run_inspect, width=12).pack(side="left")

        self.text = scrolledtext.ScrolledText(self.root, wrap="word", font=("Consolas", 10))
        self.text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        bottom = tk.Frame(self.root)
        bottom.pack(fill="x", padx=10, pady=(0, 10))

        tk.Button(bottom, text="导出报告", command=self.export_report, width=14).pack(side="left")

    def choose_file(self):
        path = filedialog.askopenfilename(
            title="选择 BIN 文件",
            filetypes=[("BIN files", "*.bin"), ("All files", "*.*")]
        )
        if path:
            self.file_var.set(path)

    def backup_file(self):
        path = self.file_var.get().strip()
        if not path:
            messagebox.showwarning("提示", "请先选择文件")
            return
        try:
            backup = make_backup(path)
            messagebox.showinfo("成功", f"备份已创建:\n{backup}")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def run_inspect(self):
        path = self.file_var.get().strip()
        if not path:
            messagebox.showwarning("提示", "请先选择文件")
            return
        try:
            info = inspect_bin(path)
            report = build_report(info)
            self.text.delete("1.0", tk.END)
            self.text.insert(tk.END, report)
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def export_report(self):
        content = self.text.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("提示", "请先执行分析")
            return

        save_path = filedialog.asksaveasfilename(
            title="保存报告",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not save_path:
            return

        try:
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("成功", f"报告已保存:\n{save_path}")
        except Exception as e:
            messagebox.showerror("错误", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()