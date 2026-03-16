import os
import shutil
import hashlib
import zlib
import struct
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from tkinter import simpledialog

SERIAL_LENGTH = 9
TARGET_OFFSET = 0


def bytes_to_hex(data: bytes) -> str:
    return " ".join(f"{b:02X}" for b in data)


def hex_to_bytes(hex_str: str) -> bytes:
    """将十六进制字符串转换为字节"""
    # 移除空格和0x前缀
    hex_str = hex_str.replace(" ", "").replace("0x", "").replace("0X", "")
    if len(hex_str) % 2 != 0:
        hex_str = "0" + hex_str
    return bytes.fromhex(hex_str)


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


def calculate_crc32(data: bytes) -> int:
    return zlib.crc32(data) & 0xFFFFFFFF


def make_backup(path: str) -> str:
    if not os.path.isfile(path):
        raise FileNotFoundError("文件不存在")
    backup_path = path + ".bak"
    shutil.copy2(path, backup_path)
    return backup_path


def read_bin_file(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def write_bin_file(path: str, data: bytes):
    with open(path, "wb") as f:
        f.write(data)


class BinEditor:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("BIN 文件编辑器")
        self.root.geometry("900x700")
        self.root.resizable(True, True)

        self.file_path = None
        self.file_data = None
        self.original_data = None
        self.backup_path = None

        self.build_ui()

    def build_ui(self):
        # 顶部工具栏
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill="x", padx=10, pady=10)

        tk.Label(top_frame, text="BIN 文件:").pack(side="left")
        self.file_var = tk.StringVar()
        tk.Entry(top_frame, textvariable=self.file_var, width=60).pack(side="left", padx=8)
        tk.Button(top_frame, text="选择文件", command=self.choose_file, width=10).pack(side="left")
        tk.Button(top_frame, text="加载", command=self.load_file, width=8).pack(side="left", padx=5)
        tk.Button(top_frame, text="备份", command=self.create_backup, width=8).pack(side="left")

        # 标签页
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)

        # 标签页1: 十六进制编辑器
        self.hex_frame = tk.Frame(self.notebook)
        self.notebook.add(self.hex_frame, text="十六进制编辑")

        # 标签页2: 序列号编辑
        self.serial_frame = tk.Frame(self.notebook)
        self.notebook.add(self.serial_frame, text="序列号编辑")

        # 标签页3: CRC32处理
        self.crc_frame = tk.Frame(self.notebook)
        self.notebook.add(self.crc_frame, text="CRC32处理")

        # 标签页4: 信息查看
        self.info_frame = tk.Frame(self.notebook)
        self.notebook.add(self.info_frame, text="文件信息")

        # 构建各个标签页的UI
        self.build_hex_editor()
        self.build_serial_editor()
        self.build_crc_editor()
        self.build_info_viewer()

        # 底部按钮
        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(fill="x", padx=10, pady=10)

        tk.Button(bottom_frame, text="保存修改", command=self.save_file,
                  bg="lightblue", width=12).pack(side="left", padx=5)
        tk.Button(bottom_frame, text="另存为", command=self.save_as_file,
                  width=10).pack(side="left", padx=5)
        tk.Button(bottom_frame, text="撤销修改", command=self.revert_changes,
                  width=10).pack(side="left", padx=5)
        tk.Button(bottom_frame, text="刷新显示", command=self.refresh_display,
                  width=10).pack(side="left", padx=5)

    def build_hex_editor(self):
        # 偏移量输入
        offset_frame = tk.Frame(self.hex_frame)
        offset_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(offset_frame, text="偏移量 (十六进制):").pack(side="left")
        self.offset_var = tk.StringVar(value="0")
        tk.Entry(offset_frame, textvariable=self.offset_var, width=10).pack(side="left", padx=5)

        tk.Label(offset_frame, text="长度:").pack(side="left", padx=(10, 0))
        self.length_var = tk.StringVar(value="16")
        tk.Entry(offset_frame, textvariable=self.length_var, width=8).pack(side="left", padx=5)

        tk.Button(offset_frame, text="读取", command=self.read_hex_data,
                  width=8).pack(side="left", padx=5)

        # 十六进制数据显示
        text_frame = tk.Frame(self.hex_frame)
        text_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # 当前数据
        tk.Label(text_frame, text="当前数据:").pack(anchor="w")
        self.hex_text = scrolledtext.ScrolledText(text_frame, height=8, font=("Consolas", 10))
        self.hex_text.pack(fill="x", pady=5)

        # 新数据输入
        tk.Label(text_frame, text="新数据 (十六进制，空格可选):").pack(anchor="w")
        self.new_hex_text = scrolledtext.ScrolledText(text_frame, height=8, font=("Consolas", 10))
        self.new_hex_text.pack(fill="x", pady=5)

        # 操作按钮
        btn_frame = tk.Frame(text_frame)
        btn_frame.pack(fill="x", pady=5)

        tk.Button(btn_frame, text="替换数据", command=self.replace_data,
                  bg="lightgreen", width=12).pack(side="left", padx=5)
        tk.Button(btn_frame, text="插入数据", command=self.insert_data,
                  width=12).pack(side="left", padx=5)
        tk.Button(btn_frame, text="删除数据", command=self.delete_data,
                  width=12).pack(side="left", padx=5)

    def build_serial_editor(self):
        # 序列号编辑
        frame = tk.Frame(self.serial_frame)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Label(frame, text="当前序列号 (偏移 0):").pack(anchor="w")
        self.serial_display = tk.Text(frame, height=3, font=("Consolas", 12))
        self.serial_display.pack(fill="x", pady=5)

        tk.Label(frame, text="新序列号 (ASCII):").pack(anchor="w", pady=(10, 0))
        self.new_serial = tk.Entry(frame, font=("Consolas", 12), width=30)
        self.new_serial.pack(anchor="w", pady=5)

        tk.Label(frame, text="新序列号 (十六进制):").pack(anchor="w")
        self.new_serial_hex = tk.Entry(frame, font=("Consolas", 12), width=30)
        self.new_serial_hex.pack(anchor="w", pady=5)

        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill="x", pady=10)

        tk.Button(btn_frame, text="更新序列号(ASCII)", command=self.update_serial_ascii,
                  bg="lightgreen", width=20).pack(side="left", padx=5)
        tk.Button(btn_frame, text="更新序列号(HEX)", command=self.update_serial_hex,
                  width=20).pack(side="left", padx=5)
        tk.Button(btn_frame, text="读取当前序列号", command=self.read_serial,
                  width=15).pack(side="left", padx=5)

    def build_crc_editor(self):
        frame = tk.Frame(self.crc_frame)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # CRC信息显示
        self.crc_info = scrolledtext.ScrolledText(frame, height=10, font=("Consolas", 10))
        self.crc_info.pack(fill="x", pady=5)

        # CRC操作
        op_frame = tk.Frame(frame)
        op_frame.pack(fill="x", pady=10)

        tk.Button(op_frame, text="计算当前CRC32", command=self.calculate_crc,
                  width=15).pack(side="left", padx=5)
        tk.Button(op_frame, text="更新CRC32(小端)", command=self.update_crc_le,
                  bg="lightgreen", width=20).pack(side="left", padx=5)
        tk.Button(op_frame, text="更新CRC32(大端)", command=self.update_crc_be,
                  width=20).pack(side="left", padx=5)
        tk.Button(op_frame, text="清除最后4字节", command=self.clear_last_4bytes,
                  width=15).pack(side="left", padx=5)

        # 说明
        tk.Label(frame, text="说明: CRC32通常存储在文件最后4字节，以小端格式存储",
                 fg="blue").pack(anchor="w", pady=5)

    def build_info_viewer(self):
        frame = tk.Frame(self.info_frame)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.info_text = scrolledtext.ScrolledText(frame, font=("Consolas", 10))
        self.info_text.pack(fill="both", expand=True)

        tk.Button(frame, text="刷新信息", command=self.refresh_info,
                  width=15).pack(pady=5)

    def choose_file(self):
        path = filedialog.askopenfilename(
            title="选择 BIN 文件",
            filetypes=[("BIN files", "*.bin"), ("All files", "*.*")]
        )
        if path:
            self.file_var.set(path)

    def load_file(self):
        path = self.file_var.get().strip()
        if not path:
            messagebox.showwarning("提示", "请先选择文件")
            return

        try:
            self.file_path = path
            self.file_data = bytearray(read_bin_file(path))
            self.original_data = self.file_data.copy()
            self.file_var.set(path)

            messagebox.showinfo("成功", f"文件已加载，大小: {len(self.file_data)} 字节")
            self.refresh_display()
            self.read_serial()
            self.calculate_crc()
            self.refresh_info()
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def create_backup(self):
        if not self.file_path:
            messagebox.showwarning("提示", "请先加载文件")
            return

        try:
            self.backup_path = make_backup(self.file_path)
            messagebox.showinfo("成功", f"备份已创建:\n{self.backup_path}")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def read_hex_data(self):
        if self.file_data is None:
            messagebox.showwarning("提示", "请先加载文件")
            return

        try:
            offset = int(self.offset_var.get(), 16)
            length = int(self.length_var.get())

            if offset < 0 or offset >= len(self.file_data):
                messagebox.showerror("错误", "偏移量超出文件范围")
                return

            end = min(offset + length, len(self.file_data))
            data = self.file_data[offset:end]

            hex_str = bytes_to_hex(data)
            self.hex_text.delete("1.0", tk.END)
            self.hex_text.insert(tk.END, hex_str)

            ascii_str = safe_ascii(data)
            self.hex_text.insert(tk.END, f"\n\nASCII: {ascii_str}")

        except ValueError:
            messagebox.showerror("错误", "偏移量必须是有效的十六进制数")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def replace_data(self):
        if self.file_data is None:
            messagebox.showwarning("提示", "请先加载文件")
            return

        try:
            offset = int(self.offset_var.get(), 16)
            new_hex = self.new_hex_text.get("1.0", tk.END).strip()

            if not new_hex:
                messagebox.showwarning("提示", "请输入要替换的数据")
                return

            new_data = hex_to_bytes(new_hex)

            if offset < 0 or offset >= len(self.file_data):
                messagebox.showerror("错误", "偏移量超出文件范围")
                return

            end = offset + len(new_data)
            if end > len(self.file_data):
                if not messagebox.askyesno("确认", "新数据将超出文件末尾，是否扩展文件？"):
                    return
                # 扩展文件
                self.file_data.extend([0] * (end - len(self.file_data)))

            self.file_data[offset:offset + len(new_data)] = new_data

            messagebox.showinfo("成功", f"已在偏移 0x{offset:X} 替换 {len(new_data)} 字节")
            self.read_hex_data()
            self.refresh_info()

        except ValueError as e:
            messagebox.showerror("错误", f"无效的十六进制数据: {str(e)}")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def insert_data(self):
        if self.file_data is None:
            messagebox.showwarning("提示", "请先加载文件")
            return

        try:
            offset = int(self.offset_var.get(), 16)
            new_hex = self.new_hex_text.get("1.0", tk.END).strip()

            if not new_hex:
                messagebox.showwarning("提示", "请输入要插入的数据")
                return

            new_data = hex_to_bytes(new_hex)

            if offset < 0 or offset > len(self.file_data):
                messagebox.showerror("错误", "偏移量超出文件范围")
                return

            # 插入数据
            self.file_data[offset:offset] = new_data

            messagebox.showinfo("成功", f"已在偏移 0x{offset:X} 插入 {len(new_data)} 字节")
            self.read_hex_data()
            self.refresh_info()

        except ValueError as e:
            messagebox.showerror("错误", f"无效的十六进制数据: {str(e)}")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def delete_data(self):
        if self.file_data is None:
            messagebox.showwarning("提示", "请先加载文件")
            return

        try:
            offset = int(self.offset_var.get(), 16)
            length = int(self.length_var.get())

            if offset < 0 or offset >= len(self.file_data):
                messagebox.showerror("错误", "偏移量超出文件范围")
                return

            end = min(offset + length, len(self.file_data))
            del_count = end - offset

            # 删除数据
            del self.file_data[offset:end]

            messagebox.showinfo("成功", f"已在偏移 0x{offset:X} 删除 {del_count} 字节")
            self.read_hex_data()
            self.refresh_info()

        except ValueError:
            messagebox.showerror("错误", "无效的数字")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def read_serial(self):
        if self.file_data is None:
            return

        try:
            offset = TARGET_OFFSET
            serial_bytes = self.file_data[offset:offset + SERIAL_LENGTH]

            ascii_str = safe_ascii(serial_bytes)
            hex_str = bytes_to_hex(serial_bytes)

            self.serial_display.delete("1.0", tk.END)
            self.serial_display.insert(tk.END,
                                        f"ASCII: {ascii_str}\n"
                                        f"HEX: {hex_str}\n"
                                        f"长度: {len(serial_bytes)} 字节")

        except Exception as e:
            messagebox.showerror("错误", str(e))

    def update_serial_ascii(self):
        if self.file_data is None:
            messagebox.showwarning("提示", "请先加载文件")
            return

        new_serial = self.new_serial.get().strip()
        if not new_serial:
            messagebox.showwarning("提示", "请输入新序列号")
            return

        if len(new_serial) > SERIAL_LENGTH:
            if not messagebox.askyesno("确认",
                                       f"序列号长度({len(new_serial)})超过预设长度({SERIAL_LENGTH})，是否继续？"):
                return

        try:
            serial_bytes = new_serial.encode('ascii')
            offset = TARGET_OFFSET

            # 确保文件足够大
            if offset + len(serial_bytes) > len(self.file_data):
                self.file_data.extend([0] * (offset + len(serial_bytes) - len(self.file_data)))

            self.file_data[offset:offset + len(serial_bytes)] = serial_bytes

            messagebox.showinfo("成功", f"序列号已更新为: {new_serial}")
            self.read_serial()

        except UnicodeEncodeError:
            messagebox.showerror("错误", "序列号只能包含ASCII字符")

    def update_serial_hex(self):
        if self.file_data is None:
            messagebox.showwarning("提示", "请先加载文件")
            return

        new_hex = self.new_serial_hex.get().strip()
        if not new_hex:
            messagebox.showwarning("提示", "请输入十六进制序列号")
            return

        try:
            serial_bytes = hex_to_bytes(new_hex)
            offset = TARGET_OFFSET

            # 确保文件足够大
            if offset + len(serial_bytes) > len(self.file_data):
                self.file_data.extend([0] * (offset + len(serial_bytes) - len(self.file_data)))

            self.file_data[offset:offset + len(serial_bytes)] = serial_bytes

            messagebox.showinfo("成功", f"序列号(HEX)已更新")
            self.read_serial()

        except ValueError as e:
            messagebox.showerror("错误", f"无效的十六进制数据: {str(e)}")

    def calculate_crc(self):
        if self.file_data is None:
            return

        data = bytes(self.file_data)
        crc32_all = calculate_crc32(data)

        info = f"整文件 CRC32: {crc32_all:08X}\n"

        if len(data) >= 4:
            body = data[:-4]
            last4 = data[-4:]
            crc32_without_last4 = calculate_crc32(body)

            tail_last4_le = int.from_bytes(last4, "little")
            tail_last4_be = int.from_bytes(last4, "big")

            info += f"除去最后4字节后的 CRC32: {crc32_without_last4:08X}\n"
            info += f"最后4字节(小端): {tail_last4_le:08X}\n"
            info += f"最后4字节(大端): {tail_last4_be:08X}\n"
            info += f"是否匹配(小端): {crc32_without_last4 == tail_last4_le}\n"
            info += f"是否匹配(大端): {crc32_without_last4 == tail_last4_be}\n"
        else:
            info += "文件太小，无法进行CRC32匹配检查\n"

        self.crc_info.delete("1.0", tk.END)
        self.crc_info.insert(tk.END, info)

    def update_crc_le(self):
        if self.file_data is None:
            messagebox.showwarning("提示", "请先加载文件")
            return

        if len(self.file_data) < 4:
            messagebox.showerror("错误", "文件太小，无法添加CRC32")
            return

        # 计算除最后4字节外的CRC32
        body = bytes(self.file_data[:-4])
        crc = calculate_crc32(body)

        # 以小端格式写入最后4字节
        self.file_data[-4:] = crc.to_bytes(4, 'little')

        messagebox.showinfo("成功", f"CRC32已更新(小端): {crc:08X}")
        self.calculate_crc()

    def update_crc_be(self):
        if self.file_data is None:
            messagebox.showwarning("提示", "请先加载文件")
            return

        if len(self.file_data) < 4:
            messagebox.showerror("错误", "文件太小，无法添加CRC32")
            return

        # 计算除最后4字节外的CRC32
        body = bytes(self.file_data[:-4])
        crc = calculate_crc32(body)

        # 以大端格式写入最后4字节
        self.file_data[-4:] = crc.to_bytes(4, 'big')

        messagebox.showinfo("成功", f"CRC32已更新(大端): {crc:08X}")
        self.calculate_crc()

    def clear_last_4bytes(self):
        if self.file_data is None:
            return

        if len(self.file_data) >= 4:
            if messagebox.askyesno("确认", "确定要删除最后4字节吗？"):
                self.file_data = self.file_data[:-4]
                messagebox.showinfo("成功", "已删除最后4字节")
                self.calculate_crc()

    def refresh_info(self):
        if self.file_data is None:
            return

        data = bytes(self.file_data)
        size = len(data)

        info = f"文件: {self.file_path}\n"
        info += f"大小: {size} 字节\n"
        info += f"MD5: {hashlib.md5(data).hexdigest()}\n"
        info += f"SHA256: {hashlib.sha256(data).hexdigest()}\n\n"

        info += "文件头(前64字节):\n"
        head = data[:min(64, size)]
        info += f"HEX: {bytes_to_hex(head)}\n"
        info += f"ASCII: {safe_ascii(head)}\n\n"

        info += "文件尾(后64字节):\n"
        tail = data[-min(64, size):] if size else b""
        info += f"HEX: {bytes_to_hex(tail)}\n"
        info += f"ASCII: {safe_ascii(tail)}\n"

        self.info_text.delete("1.0", tk.END)
        self.info_text.insert(tk.END, info)

    def refresh_display(self):
        if self.file_data is not None:
            self.read_serial()
            self.calculate_crc()
            self.refresh_info()

    def save_file(self):
        if self.file_data is None:
            messagebox.showwarning("提示", "没有要保存的数据")
            return

        if not self.file_path:
            self.save_as_file()
            return

        try:
            write_bin_file(self.file_path, bytes(self.file_data))
            self.original_data = self.file_data.copy()
            messagebox.showinfo("成功", f"文件已保存: {self.file_path}")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def save_as_file(self):
        if self.file_data is None:
            messagebox.showwarning("提示", "没有要保存的数据")
            return

        save_path = filedialog.asksaveasfilename(
            title="保存BIN文件",
            defaultextension=".bin",
            filetypes=[("BIN files", "*.bin"), ("All files", "*.*")]
        )

        if save_path:
            try:
                write_bin_file(save_path, bytes(self.file_data))
                self.file_path = save_path
                self.file_var.set(save_path)
                self.original_data = self.file_data.copy()
                messagebox.showinfo("成功", f"文件已保存: {save_path}")
            except Exception as e:
                messagebox.showerror("错误", str(e))

    def revert_changes(self):
        if self.original_data is None:
            return

        if messagebox.askyesno("确认", "确定要撤销所有修改吗？"):
            self.file_data = self.original_data.copy()
            self.refresh_display()
            messagebox.showinfo("成功", "已撤销所有修改")


if __name__ == "__main__":
    root = tk.Tk()
    app = BinEditor(root)
    root.mainloop()