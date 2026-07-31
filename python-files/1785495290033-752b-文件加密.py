# -*- coding: utf-8 -*-
import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import hashlib
import hmac
import struct
import tempfile

# ==================== 加密核心 ====================
class CryptoStream:
    CHUNK_SIZE = 1024 * 1024          # 1MB
    MAGIC = b'ENC\x01'
    HEADER_FMT = '!4s16sQQ'           # 魔数(4)+盐(16)+计数器(8)+原始大小(8) = 36字节
    HMAC_SIZE = 32

    @staticmethod
    def _derive_key(password, salt, dklen=32, iterations=100000):
        return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations, dklen)

    @staticmethod
    def _xor_bytes(a, b):
        # 使用 bytearray 加速
        ba = bytearray(a)
        for i in range(len(ba)):
            ba[i] ^= b[i]
        return bytes(ba)

    @classmethod
    def encrypt_file(cls, filepath, password):
        with open(filepath, 'rb') as f:
            if f.read(4) == cls.MAGIC:
                raise RuntimeError("文件已是加密状态，跳过重复加密")

        salt = os.urandom(16)
        key = cls._derive_key(password, salt)
        counter = struct.unpack('>Q', os.urandom(8))[0]
        original_size = os.path.getsize(filepath)
        dirname = os.path.dirname(filepath)

        # 创建临时文件（重试3次）
        tmp_path = None
        for _ in range(3):
            try:
                fd, tmp_path = tempfile.mkstemp(dir=dirname, prefix='.enc_tmp_')
                os.close(fd)
                break
            except Exception:
                continue
        if tmp_path is None:
            raise IOError("无法创建临时文件，磁盘可能已满")

        try:
            hmac_ctx = hmac.new(key, digestmod=hashlib.sha256)
            ks = cls._Keystream(key, counter)

            with open(filepath, 'rb') as fin, open(tmp_path, 'wb') as fout:
                header = struct.pack(cls.HEADER_FMT, cls.MAGIC, salt, counter, original_size)
                fout.write(header)
                hmac_ctx.update(header)

                while True:
                    chunk = fin.read(cls.CHUNK_SIZE)
                    if not chunk:
                        break
                    pad = ks.read(len(chunk))
                    encrypted = cls._xor_bytes(chunk, pad)
                    fout.write(encrypted)
                    hmac_ctx.update(encrypted)

                fout.write(hmac_ctx.digest())

            os.replace(tmp_path, filepath)
        except Exception:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

        return salt.hex(), struct.pack('>Q', counter).hex(), original_size

    @classmethod
    def decrypt_file(cls, filepath, password):
        with open(filepath, 'rb') as f:
            header = f.read(struct.calcsize(cls.HEADER_FMT))
            if len(header) < struct.calcsize(cls.HEADER_FMT):
                raise ValueError("文件头不完整，无法解密")
            magic, salt, counter, original_size = struct.unpack(cls.HEADER_FMT, header)
            if magic != cls.MAGIC:
                raise RuntimeError("文件不是加密文件，无法解密")

            f.seek(0, os.SEEK_END)
            file_size = f.tell()
            ciphertext_len = file_size - struct.calcsize(cls.HEADER_FMT) - cls.HMAC_SIZE
            if ciphertext_len < 0:
                raise ValueError("文件长度不足，可能已损坏")
            f.seek(-cls.HMAC_SIZE, os.SEEK_END)
            stored_hmac = f.read(cls.HMAC_SIZE)

        key = cls._derive_key(password, salt)
        ks = cls._Keystream(key, counter)
        dirname = os.path.dirname(filepath)

        tmp_path = None
        for _ in range(3):
            try:
                fd, tmp_path = tempfile.mkstemp(dir=dirname, prefix='.dec_tmp_')
                os.close(fd)
                break
            except Exception:
                continue
        if tmp_path is None:
            raise IOError("无法创建临时文件，磁盘可能已满")

        try:
            hmac_ctx = hmac.new(key, digestmod=hashlib.sha256)

            with open(filepath, 'rb') as fin, open(tmp_path, 'wb') as fout:
                header = fin.read(struct.calcsize(cls.HEADER_FMT))
                hmac_ctx.update(header)

                total_written = 0
                while total_written < ciphertext_len:
                    read_size = min(cls.CHUNK_SIZE, ciphertext_len - total_written)
                    cipher_chunk = fin.read(read_size)
                    if not cipher_chunk:
                        raise RuntimeError("文件意外结束")
                    hmac_ctx.update(cipher_chunk)
                    pad = ks.read(len(cipher_chunk))
                    plain = cls._xor_bytes(cipher_chunk, pad)
                    fout.write(plain)
                    total_written += len(cipher_chunk)

            if not hmac.compare_digest(hmac_ctx.digest(), stored_hmac):
                raise ValueError("HMAC校验失败，密码错误或文件被篡改")
            if total_written != original_size:
                raise ValueError("解密后大小({})与原始大小({})不匹配".format(total_written, original_size))

            os.replace(tmp_path, filepath)
        except Exception:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    class _Keystream:
        def __init__(self, key, counter):
            self._key = key
            self._counter = counter
            self._block_idx = 0
            self._buffer = b''

        def read(self, n):
            result = bytearray()
            while len(result) < n:
                if not self._buffer:
                    data = struct.pack('>QQ', self._counter, self._block_idx)
                    self._buffer = hmac.new(self._key, data, hashlib.sha256).digest()
                    self._block_idx += 1
                needed = n - len(result)
                take = min(needed, len(self._buffer))
                result.extend(self._buffer[:take])
                self._buffer = self._buffer[take:]
            return bytes(result)


# ==================== 主程序 ====================
class FileEncryptorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("文件加密工具")
        self.root.geometry("840x680")
        self.root.minsize(720, 500)
        self.root.configure(bg="#f0f4f8")

        self.password = "INTERNAL_FIXED_PASSWORD_2024"
        self.file_list = []
        self.encrypted_records = []

        self._lock = threading.Lock()
        self._busy = False

        self._load_records()
        self._build_ui()

    # ---------- 按钮状态 ----------
    def _set_buttons_state(self, state):
        self.scan_btn.config(state=state)
        self.encrypt_btn.config(state=state)
        self.decrypt_btn.config(state=state)
        self.clear_btn.config(state=state)

    def _enter_busy(self):
        with self._lock:
            if self._busy:
                return False
            self._busy = True
        self.root.after(0, lambda: self._set_buttons_state(tk.DISABLED))
        return True

    def _leave_busy(self):
        with self._lock:
            self._busy = False
        self.root.after(0, lambda: self._set_buttons_state(tk.NORMAL))

    # ---------- 记录持久化 ----------
    def _records_path(self):
        return os.path.expanduser("~/.encrypt_tool_records.dat")

    def _load_records(self):
        path = self._records_path()
        self.encrypted_records = []
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        parts = line.split('|')
                        if len(parts) == 4:
                            fp, salt, counter, size = parts
                            self.encrypted_records.append((fp, salt, counter, int(size)))
            except Exception:
                self.encrypted_records = []

    def _save_records(self):
        """调用前必须持有 self._lock"""
        path = self._records_path()
        try:
            with open(path, 'w') as f:
                for fp, salt, counter, size in self.encrypted_records:
                    f.write("{}|{}|{}|{}\n".format(fp, salt, counter, size))
        except Exception as e:
            self._log("⚠️ 保存记录失败: {}".format(e))

    # ---------- 界面构建 ----------
    def _build_ui(self):
        # 顶部
        top_frame = tk.Frame(self.root, bg="#f0f4f8")
        top_frame.pack(fill=tk.X, padx=25, pady=(18, 6))
        tk.Label(top_frame, text="🔐 文件加密工具", font=("微软雅黑", 22, "bold"),
                 bg="#f0f4f8", fg="#2c3e50").pack(side=tk.LEFT)

        self.clear_btn = tk.Button(top_frame, text="🗑️ 清除记录", command=self._confirm_clear_records,
                                   font=("微软雅黑", 9), bg="#e74c3c", fg="white",
                                   relief="raised", bd=1, cursor="hand2")
        self.clear_btn.pack(side=tk.RIGHT, padx=(0, 5))

        # 功能按钮
        btn_frame = tk.Frame(self.root, bg="#f0f4f8")
        btn_frame.pack(pady=10)
        btn_style = {"width": 14, "height": 2, "font": ("微软雅黑", 11, "bold"),
                     "relief": "raised", "bd": 2, "cursor": "hand2"}

        self.scan_btn = tk.Button(btn_frame, text="📂 扫描文件", command=self._start_scan,
                                  bg="#3498db", fg="white", **btn_style)
        self.scan_btn.grid(row=0, column=0, padx=6)

        self.encrypt_btn = tk.Button(btn_frame, text="🔒 全部加密", command=self._start_encrypt,
                                     bg="#e67e22", fg="white", **btn_style)
        self.encrypt_btn.grid(row=0, column=1, padx=6)

        self.decrypt_btn = tk.Button(btn_frame, text="🔓 全部解密", command=self._start_decrypt,
                                     bg="#27ae60", fg="white", **btn_style)
        self.decrypt_btn.grid(row=0, column=2, padx=6)

        # 文件列表
        list_frame = tk.Frame(self.root, bg="#f0f4f8")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=4)
        self.listbox = tk.Listbox(list_frame, font=("Consolas", 10), bg="white",
                                  fg="#2d3436", relief="sunken", bd=2, selectmode=tk.SINGLE)
        scroll = tk.Scrollbar(list_frame, command=self.listbox.yview)
        self.listbox.config(yscrollcommand=scroll.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # 状态栏
        status_frame = tk.Frame(self.root, bg="#f0f4f8")
        status_frame.pack(fill=tk.X, padx=25, pady=5)
        self.status_label = tk.Label(status_frame, text="就绪", font=("微软雅黑", 10),
                                     bg="#f0f4f8", fg="#2d3436", anchor="w")
        self.status_label.pack(side=tk.LEFT)
        self.progress = ttk.Progressbar(status_frame, orient=tk.HORIZONTAL, length=280, mode='determinate')
        self.progress.pack(side=tk.RIGHT, padx=5)

        # 日志区
        log_frame = tk.Frame(self.root, bg="#f0f4f8")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=(0, 18))
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, font=("Consolas", 9),
                                                  state='disabled', wrap=tk.WORD,
                                                  bg="#fefefe", fg="#2d3436", relief="sunken", bd=2)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    # ---------- 线程安全日志/状态 ----------
    def _log(self, msg):
        self.root.after(0, lambda m=msg: self._update_log(m))

    def _update_log(self, msg):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def _update_status(self, text, progress=None):
        def _do():
            self.status_label.config(text=text)
            if progress is not None:
                self.progress['value'] = progress
        self.root.after(0, _do)

    # ---------- 清除记录（后台线程，不会卡UI） ----------
    def _confirm_clear_records(self):
        if not self.encrypted_records:
            messagebox.showinfo("提示", "当前没有加密记录。")
            return
        if messagebox.askyesno("确认清除", "确定要清除所有 {} 条加密记录吗？\n此操作不可撤销。".format(len(self.encrypted_records))):
            threading.Thread(target=self._do_clear_records, daemon=True).start()

    def _do_clear_records(self):
        if not self._enter_busy():
            return
        try:
            with self._lock:
                self.encrypted_records.clear()
                self._save_records()
            self._log("🗑️ 所有加密记录已清除。")
            self._update_status("加密记录已清除", 0)
        except Exception as e:
            self._log("❌ 清除记录失败: {}".format(e))
        finally:
            self._leave_busy()

    # ---------- 扫描 ----------
    def _start_scan(self):
        path = filedialog.askdirectory(title="选择要扫描的目录")
        if path:
            threading.Thread(target=self._do_scan, args=(path,), daemon=True).start()

    def _do_scan(self, path):
        if not self._enter_busy():
            return
        try:
            self._update_status("扫描中...", 0)
            exts = {
                '.jpg','.jpeg','.png','.gif','.bmp','.tiff','.webp','.ico','.svg',
                '.pdf','.doc','.docx','.xls','.xlsx','.ppt','.pptx','.txt','.rtf','.md',
                '.zip','.rar','.7z','.tar','.gz','.bz2','.xz',
                '.mp3','.wav','.flac','.aac','.ogg','.mp4','.avi','.mkv','.mov','.wmv','.flv','.webm',
                '.py','.js','.html','.css','.cpp','.c','.java','.go','.rs','.php','.rb','.sh','.bat',
                '.json','.xml','.yaml','.toml','.exe','.dll','.iso','.img'
            }
            files = []
            for root, _, filenames in os.walk(path):
                for f in filenames:
                    if os.path.splitext(f)[1].lower() in exts:
                        files.append(os.path.join(root, f))
            with self._lock:
                self.file_list = files
            self.root.after(0, lambda f=files: self._update_file_list(f))
            self._log("✅ 扫描完成，共 {} 个文件".format(len(files)))
            self._update_status("扫描完成，共 {} 个文件".format(len(files)), 100)
        except Exception as e:
            self._log("❌ 扫描异常: {}".format(e))
        finally:
            self._leave_busy()

    def _update_file_list(self, files):
        self.listbox.delete(0, tk.END)
        for f in files:
            self.listbox.insert(tk.END, f)

    # ---------- 加密 ----------
    def _start_encrypt(self):
        threading.Thread(target=self._do_encrypt, daemon=True).start()

    def _do_encrypt(self):
        if not self._enter_busy():
            return
        try:
            with self._lock:
                files = list(self.file_list)
            if not files:
                self._log("⚠️ 没有文件，请先扫描")
                self._update_status("无文件", 0)
                return

            total = len(files)
            self._log("🔒 开始加密 {} 个文件...".format(total))
            success = 0
            new_records = []
            for idx, fp in enumerate(files):
                try:
                    salt_hex, counter_hex, orig_size = CryptoStream.encrypt_file(fp, self.password)
                    new_records.append((fp, salt_hex, counter_hex, orig_size))
                    success += 1
                    progress = (idx + 1) / total * 100
                    self._update_status("加密: {}".format(os.path.basename(fp)), progress)
                    self._log("  ✅ {} (原大小 {} 字节)".format(os.path.basename(fp), orig_size))
                except RuntimeError as e:
                    self._log("  ⚠️ {} 跳过: {}".format(os.path.basename(fp), e))
                except Exception as e:
                    self._log("  ❌ {} 失败: {}".format(os.path.basename(fp), e))

            with self._lock:
                self.encrypted_records.extend(new_records)
                self._save_records()
            self._log("✅ 加密完成，成功 {}/{}".format(success, total))
            self._update_status("加密完成，成功 {}/{}".format(success, total), 100)
        except Exception as e:
            self._log("❌ 加密过程异常: {}".format(e))
        finally:
            self._leave_busy()

    # ---------- 解密 ----------
    def _start_decrypt(self):
        threading.Thread(target=self._do_decrypt, daemon=True).start()

    def _do_decrypt(self):
        if not self._enter_busy():
            return
        try:
            with self._lock:
                records = list(self.encrypted_records)
            if not records:
                self._log("ℹ️ 无加密记录，无需解密")
                self._update_status("无记录", 0)
                return

            total = len(records)
            self._log("🔓 开始解密 {} 个文件...".format(total))
            success = 0
            failed_records = []
            for idx, (fp, salt, counter, size) in enumerate(records):
                try:
                    if not os.path.exists(fp):
                        self._log("  ⚠️ 文件不存在: {}".format(fp))
                        failed_records.append((fp, salt, counter, size))
                        continue
                    CryptoStream.decrypt_file(fp, self.password)
                    success += 1
                    progress = (idx + 1) / total * 100
                    self._update_status("解密: {}".format(os.path.basename(fp)), progress)
                    self._log("  ✅ {}".format(os.path.basename(fp)))
                except RuntimeError as e:
                    self._log("  ⚠️ {} 跳过: {}".format(os.path.basename(fp), e))
                    failed_records.append((fp, salt, counter, size))
                except Exception as e:
                    self._log("  ❌ {} 失败: {}".format(os.path.basename(fp), e))
                    failed_records.append((fp, salt, counter, size))

            with self._lock:
                self.encrypted_records = failed_records
                self._save_records()
            self._log("✅ 解密完成，成功 {}/{}".format(success, total))
            self._update_status("解密完成，成功 {}/{}".format(success, total), 100)
        except Exception as e:
            self._log("❌ 解密过程异常: {}".format(e))
        finally:
            self._leave_busy()


if __name__ == "__main__":
    root = tk.Tk()
    app = FileEncryptorApp(root)
    root.mainloop()