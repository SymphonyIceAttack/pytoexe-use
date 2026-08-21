# -*- coding: utf-8 -*-
"""
视频去重工具（GUI）
- 选择文件夹，递归扫描所有视频
- 按文件大小(字节)分组，大小相同的只保留一个，其余删除
- 保留文件位置不变，仅删除重复项
"""
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

VIDEO_EXTS = {
    ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv",
    ".webm", ".ts", ".m4v", ".mpg", ".mpeg", ".3gp", ".rmvb"
}


def scan_duplicates(root):
    """扫描 root 下所有视频，按大小分组，返回 (size_groups, file_list)"""
    size_map = {}
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            ext = os.path.splitext(name)[1].lower()
            if ext not in VIDEO_EXTS:
                continue
            full = os.path.join(dirpath, name)
            try:
                sz = os.path.getsize(full)
            except OSError:
                continue
            size_map.setdefault(sz, []).append(full)
    # 仅保留有重复的组
    dups = {sz: files for sz, files in size_map.items() if len(files) > 1}
    return dups, size_map


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("视频去重工具")
        self.geometry("760x560")
        self.minsize(700, 480)

        self.root_dir = tk.StringVar(value="")

        frm = ttk.Frame(self, padding=10)
        frm.pack(fill="x")

        ttk.Label(frm, text="文件夹：").pack(side="left")
        self.entry = ttk.Entry(frm, textvariable=self.root_dir, width=55)
        self.entry.pack(side="left", padx=(0, 8), fill="x", expand=True)
        ttk.Button(frm, text="选择文件夹", command=self.on_choose).pack(side="left")

        btns = ttk.Frame(self, padding=(10, 0))
        btns.pack(fill="x")
        self.btn_scan = ttk.Button(btns, text="扫描重复", command=self.on_scan)
        self.btn_scan.pack(side="left", padx=(0, 8))
        self.btn_dedup = ttk.Button(btns, text="开始去重", command=self.on_dedup)
        self.btn_dedup.pack(side="left")
        self.btn_dedup["state"] = "disabled"

        self.log = scrolledtext.ScrolledText(self, wrap="none", height=30)
        self.log.pack(fill="both", expand=True, padx=10, pady=10)

        self.dup_groups = None

    def logln(self, text):
        self.log.insert("end", text + "\n")
        self.log.see("end")

    def on_choose(self):
        d = filedialog.askdirectory(title="选择要去重的视频文件夹")
        if d:
            self.root_dir.set(d)
            self.log.delete("1.0", "end")
            self.dup_groups = None
            self.btn_dedup["state"] = "disabled"

    def on_scan(self):
        root = self.root_dir.get().strip()
        if not root or not os.path.isdir(root):
            messagebox.showwarning("提示", "请先选择有效的文件夹")
            return
        self.log.delete("1.0", "end")
        self.logln("正在扫描：" + root)
        self.update()
        dups, _ = scan_duplicates(root)
        self.dup_groups = dups
        if not dups:
            self.logln("未发现大小重复的视频文件。")
            self.btn_dedup["state"] = "disabled"
            return
        total_del = 0
        for sz, files in sorted(dups.items(), key=lambda x: -x[0]):
            self.logln("--- 大小 %d 字节，共 %d 个重复 ---" % (sz, len(files)))
            self.logln("  [保留] " + files[0])
            for f in files[1:]:
                self.logln("  [删除] " + f)
                total_del += 1
        self.logln("")
        self.logln("扫描完成：%d 组重复，拟删除 %d 个文件。" % (len(dups), total_del))
        self.btn_dedup["state"] = "normal"

    def on_dedup(self):
        if not self.dup_groups:
            return
        if not messagebox.askyesno("确认", "即将删除上述重复视频，此操作不可恢复！\n确定继续吗？"):
            return
        deleted = 0
        failed = 0
        for files in self.dup_groups.values():
            for f in files[1:]:
                try:
                    os.remove(f)
                    self.logln("[已删除] " + f)
                    deleted += 1
                except OSError as e:
                    self.logln("[删除失败] %s  (%s)" % (f, e))
                    failed += 1
        self.logln("")
        self.logln("去重完成：成功删除 %d 个，失败 %d 个。" % (deleted, failed))
        self.btn_dedup["state"] = "disabled"
        self.dup_groups = None


if __name__ == "__main__":
    App().mainloop()
