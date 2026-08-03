#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量重命名工具 - RenameTool v1.0
基于 Python + Tkinter，支持拖拽文件、模板管理、注册表持久化
打包：pyinstaller --onefile --windowed --collect-all tkinterdnd2 RenameTool.py
"""

import os
import sys
import json
import winreg
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# ── 尝试导入拖拽支持 ──
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False

# ============================================================
# 常量
# ============================================================
APP_NAME = "批量重命名工具 v1.0"
REG_PATH = r"Software\RenameTool"
WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 620

# 内置默认模板（硬编码）
DEFAULT_TEMPLATES = {
    "中文数字": [
        "一", "二", "三", "四", "五", "六", "七", "八", "九", "十",
        "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十"
    ],
    "罗马数字": ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"],
    "英文数字": ["One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten"],
}

BUILTIN_NAMES = set(DEFAULT_TEMPLATES.keys())

# ============================================================
# 注册表操作
# ============================================================
def reg_get_templates():
    """从注册表读取所有模板，返回 {name: [items], ...}"""
    templates = {}
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_READ)
        i = 0
        while True:
            try:
                name, value, _ = winreg.EnumValue(key, i)
                templates[name] = json.loads(value)
                i += 1
            except OSError:
                break
        winreg.CloseKey(key)
    except FileNotFoundError:
        pass
    return templates


def reg_save_template(name, items):
    """保存单个模板到注册表"""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_SET_VALUE)
    except FileNotFoundError:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_PATH)
    winreg.SetValueEx(key, name, 0, winreg.REG_SZ, json.dumps(items, ensure_ascii=False))
    winreg.CloseKey(key)


def reg_delete_template(name):
    """从注册表删除指定模板"""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, name)
        winreg.CloseKey(key)
    except (FileNotFoundError, OSError):
        pass


def reg_initialize():
    """初始化注册表：为空则写入默认模板"""
    templates = reg_get_templates()
    if not templates:
        for name, items in DEFAULT_TEMPLATES.items():
            reg_save_template(name, items)
    return reg_get_templates()


def reg_reset_all():
    """删除所有模板值，重写默认模板"""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_SET_VALUE)
        names = []
        i = 0
        while True:
            try:
                name, _, _ = winreg.EnumValue(key, i)
                names.append(name)
                i += 1
            except OSError:
                break
        for name in names:
            winreg.DeleteValue(key, name)
        winreg.CloseKey(key)
    except FileNotFoundError:
        pass
    for name, items in DEFAULT_TEMPLATES.items():
        reg_save_template(name, items)


def reg_merge_builtins():
    """确保内置模板始终存在（补全可能被删的内置模板）"""
    templates = reg_get_templates()
    for name in BUILTIN_NAMES:
        if name not in templates:
            reg_save_template(name, DEFAULT_TEMPLATES[name])


# ============================================================
# 模板管理窗口
# ============================================================
class TemplateManager(tk.Toplevel):
    """模板管理对话框"""

    def __init__(self, parent, on_close=None):
        super().__init__(parent)
        self.title("管理模板")
        self.geometry("620x500")
        self.minsize(500, 380)
        self.on_close_callback = on_close
        self.current_edit_name = None  # 当前正在编辑的模板名

        self._build_ui()
        self._refresh_list()

        self.protocol("WM_DELETE_WINDOW", self._close)
        self.transient(parent)
        self.grab_set()

    def _build_ui(self):
        # ── 主容器：左右分栏 ──
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # ── 左栏：模板列表 ──
        left = ttk.Frame(paned)
        paned.add(left, weight=2)

        ttk.Label(left, text="模板列表", font=("", 10, "bold")).pack(anchor=tk.W)

        list_container = ttk.Frame(left)
        list_container.pack(fill=tk.BOTH, expand=True, pady=4)

        self.listbox = tk.Listbox(list_container, exportselection=False,
                                   activestyle="dotbox", font=("", 10))
        scroll = ttk.Scrollbar(list_container, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.config(yscrollcommand=scroll.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.bind("<<ListboxSelect>>", self._on_list_select)

        # 按钮组
        btn_frame = ttk.Frame(left)
        btn_frame.pack(fill=tk.X, pady=6)
        ttk.Button(btn_frame, text="新建", command=self._on_new).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="删除", command=self._on_delete).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="恢复默认", command=self._on_reset).pack(side=tk.LEFT, padx=2)

        # ── 右栏：编辑区 ──
        right = ttk.Frame(paned)
        paned.add(right, weight=3)

        ttk.Label(right, text="模板名称").pack(anchor=tk.W)
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(right, textvariable=self.name_var, font=("", 10))
        self.name_entry.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(right, text="词条内容（一行一个词条）").pack(anchor=tk.W)
        content_frame = ttk.Frame(right)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        self.content_text = tk.Text(content_frame, wrap=tk.WORD, font=("", 10),
                                     undo=True, maxundo=50)
        content_scroll = ttk.Scrollbar(content_frame, orient=tk.VERTICAL,
                                        command=self.content_text.yview)
        self.content_text.config(yscrollcommand=content_scroll.set)
        self.content_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        content_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Button(right, text="保存", command=self._on_save).pack(pady=4)

    def _refresh_list(self):
        self.listbox.delete(0, tk.END)
        templates = reg_get_templates()
        for name in sorted(templates.keys()):
            self.listbox.insert(tk.END, name)

    def _on_list_select(self, event):
        sel = self.listbox.curselection()
        if not sel:
            return
        name = self.listbox.get(sel[0])
        self.current_edit_name = name
        templates = reg_get_templates()
        items = templates.get(name, [])

        self.name_var.set(name)
        self.content_text.delete("1.0", tk.END)
        self.content_text.insert("1.0", "\n".join(items))

        # 内置模板不允许修改名称
        if name in BUILTIN_NAMES:
            self.name_entry.config(state="disabled")
        else:
            self.name_entry.config(state="normal")

    def _on_new(self):
        self.current_edit_name = None
        self.name_var.set("")
        self.name_entry.config(state="normal")
        self.content_text.delete("1.0", tk.END)
        self.listbox.selection_clear(0, tk.END)

    def _on_save(self):
        name = self.name_var.get().strip()
        content = self.content_text.get("1.0", tk.END).strip()

        if not name:
            messagebox.showwarning("提示", "请输入模板名称", parent=self)
            return

        items = [line.strip() for line in content.split("\n") if line.strip()]
        if not items:
            messagebox.showwarning("提示", "至少需要一个词条", parent=self)
            return

        # 内置模板不允许改名
        if self.current_edit_name and self.current_edit_name in BUILTIN_NAMES:
            if name != self.current_edit_name:
                messagebox.showwarning("提示", "内置模板不允许修改名称", parent=self)
                return

        # 如果改名了，删除旧键
        if self.current_edit_name and self.current_edit_name != name:
            reg_delete_template(self.current_edit_name)

        reg_save_template(name, items)
        self._refresh_list()

        # 选中刚保存的模板
        templates = reg_get_templates()
        sorted_names = sorted(templates.keys())
        if name in sorted_names:
            idx = sorted_names.index(name)
            self.listbox.selection_set(idx)
            self.listbox.see(idx)
            self.current_edit_name = name

        messagebox.showinfo("提示", "模板已保存", parent=self)

    def _on_delete(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("提示", "请先选择一个模板", parent=self)
            return
        name = self.listbox.get(sel[0])
        if name in BUILTIN_NAMES:
            messagebox.showwarning("提示", "内置默认模板不允许删除", parent=self)
            return

        if messagebox.askyesno("确认删除", f"确定要删除模板「{name}」吗？", parent=self):
            reg_delete_template(name)
            self._refresh_list()
            self.current_edit_name = None
            self.name_var.set("")
            self.content_text.delete("1.0", tk.END)

    def _on_reset(self):
        if messagebox.askyesno("确认恢复",
                                "将删除所有自定义模板，恢复为内置默认模板。\n确定继续吗？",
                                parent=self):
            reg_reset_all()
            self._refresh_list()
            self.current_edit_name = None
            self.name_var.set("")
            self.content_text.delete("1.0", tk.END)
            messagebox.showinfo("提示", "已恢复默认模板", parent=self)

    def _close(self):
        if self.on_close_callback:
            self.on_close_callback()
        self.destroy()


# ============================================================
# 主窗口
# ============================================================
class RenameTool:
    """批量重命名工具主窗口"""

    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.minsize(800, 450)

        # ── 数据模型 ──
        # self.file_data: [{path, orig_name, ext, new_base, is_manual}]
        self.file_data = []
        # 手动编辑标记：{item_id: bool}
        self.manual_flags = {}
        # 模板词条不足的行 item_id set
        self.overflow_items = set()

        # ── 模板数据 ──
        reg_merge_builtins()
        self.templates = reg_get_templates()
        self.template_var = tk.StringVar()

        # ── 构建界面 ──
        self._build_menu()
        self._build_ui()

        # ── 绑定事件 ──
        self.root.bind("<Delete>", self._on_delete_key)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # ── 居中窗口 ──
        self.root.update_idletasks()
        self._center_window()

    # ─── 菜单栏 ─────────────────────────────────────
    def _build_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # 模板菜单
        template_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="模板", menu=template_menu)
        template_menu.add_command(label="管理模板...", command=self._open_template_manager)
        template_menu.add_separator()
        template_menu.add_command(label="恢复默认模板", command=self._reset_templates)

        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self._show_about)

    # ─── 三栏主界面 ────────────────────────────────
    def _build_ui(self):
        # ── 主 PanedWindow（三栏可拖拽调整宽度） ──
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # ── 左栏：文件列表 ──
        self._build_left_panel(main_paned)

        # ── 中栏：模板选择 ──
        self._build_middle_panel(main_paned)

        # ── 右栏：目标名称 ──
        self._build_right_panel(main_paned)

        # ── 底部：执行按钮 ──
        bottom_frame = ttk.Frame(self.root)
        bottom_frame.pack(fill=tk.X, padx=5, pady=(0, 8))

        ttk.Button(bottom_frame, text="执行重命名", command=self._execute_rename,
                   style="Action.TButton").pack(side=tk.RIGHT, padx=5)

        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(bottom_frame, textvariable=self.status_var, foreground="gray")
        status_label.pack(side=tk.LEFT, padx=5)

        # 自定义样式
        style = ttk.Style()
        style.configure("Action.TButton", font=("", 10, "bold"))

    def _build_left_panel(self, parent):
        """左栏：文件列表"""
        frame = ttk.LabelFrame(parent, text="文件列表", padding=3)
        parent.add(frame, weight=3)

        # 文件计数
        self.file_count_var = tk.StringVar(value="共 0 个文件")
        ttk.Label(frame, textvariable=self.file_count_var).pack(anchor=tk.W, padx=3)

        # 文件列表（Listbox + 滚动条）
        list_container = ttk.Frame(frame)
        list_container.pack(fill=tk.BOTH, expand=True, pady=3)

        self.file_listbox = tk.Listbox(list_container, exportselection=False,
                                        selectmode=tk.EXTENDED, font=("", 10))
        file_scroll = ttk.Scrollbar(list_container, orient=tk.VERTICAL,
                                     command=self.file_listbox.yview)
        self.file_listbox.config(yscrollcommand=file_scroll.set)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        file_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # 右键菜单
        self.file_context_menu = tk.Menu(self.root, tearoff=0)
        self.file_context_menu.add_command(label="移除选中文件", command=self._remove_selected_files)
        self.file_context_menu.add_command(label="清空全部文件", command=self._clear_all_files)

        self.file_listbox.bind("<Button-3>", self._on_file_right_click)
        self.file_listbox.bind("<Motion>", self._on_file_hover)

        # ── 拖拽支持 ──
        if HAS_DND:
            self.file_listbox.drop_target_register(DND_FILES)
            self.file_listbox.dnd_bind("<<Drop>>", self._on_drop)
            # 也支持拖拽到整个左栏
            frame.drop_target_register(DND_FILES)
            frame.dnd_bind("<<Drop>>", self._on_drop)

        # ── 按钮 ──
        btn_row = ttk.Frame(frame)
        btn_row.pack(fill=tk.X, pady=3)
        ttk.Button(btn_row, text="添加文件...", command=self._add_files).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_row, text="移除选中", command=self._remove_selected_files).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_row, text="清空", command=self._clear_all_files).pack(side=tk.LEFT, padx=2)

        # ── 提示文本（无拖拽支持时） ──
        if not HAS_DND:
            ttk.Label(frame, text="⚠ 未安装拖拽支持（tkinterdnd2），请使用「添加文件」按钮",
                      foreground="gray").pack(anchor=tk.W, padx=3)

    def _build_middle_panel(self, parent):
        """中栏：模板选择"""
        frame = ttk.LabelFrame(parent, text="模板选择", padding=3)
        parent.add(frame, weight=2)

        self.template_radio_frame = ttk.Frame(frame)
        self.template_radio_frame.pack(fill=tk.BOTH, expand=True, pady=3)

        # 底部按钮
        btn_row = ttk.Frame(frame)
        btn_row.pack(fill=tk.X, pady=3)
        ttk.Button(btn_row, text="清空右侧", command=self._clear_right_column).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_row, text="管理模板...", command=self._open_template_manager).pack(side=tk.LEFT, padx=2)

        self._refresh_template_radios()

    def _build_right_panel(self, parent):
        """右栏：目标名称 Treeview"""
        frame = ttk.LabelFrame(parent, text="目标名称（双击编辑）", padding=3)
        parent.add(frame, weight=5)

        # Treeview
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=3)

        columns = ("orig", "new")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings",
                                  selectmode="extended")
        self.tree.heading("orig", text="原文件名")
        self.tree.heading("new", text="新文件名")
        self.tree.column("orig", width=180, minwidth=100)
        self.tree.column("new", width=200, minwidth=120)

        tree_scroll_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.config(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        tree_scroll_y.grid(row=0, column=1, sticky="ns")
        tree_scroll_x.grid(row=1, column=0, sticky="ew")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        # 标签样式
        self.tree.tag_configure("manual", foreground="blue", font=("", 10, "bold"))
        self.tree.tag_configure("overflow", foreground="red")

        # 双击编辑
        self.tree.bind("<Double-1>", self._on_cell_double_click)

        # ── 编辑控件（浮动 Entry） ──
        self.edit_entry = None  # 当前编辑 Entry

    # ─── 模板 RadioButton 刷新 ─────────────────────
    def _refresh_template_radios(self):
        """重建模板单选按钮组"""
        for widget in self.template_radio_frame.winfo_children():
            widget.destroy()

        self.templates = reg_get_templates()
        self.template_var.set("")

        if not self.templates:
            ttk.Label(self.template_radio_frame, text="暂无模板",
                      foreground="gray").pack(pady=10)
            return

        container = ttk.Frame(self.template_radio_frame)
        container.pack(fill=tk.BOTH, expand=True)

        for name in sorted(self.templates.keys()):
            rb = ttk.Radiobutton(container, text=name, variable=self.template_var,
                                  value=name, command=self._on_template_selected)
            rb.pack(anchor=tk.W, pady=1)

    def _on_template_selected(self):
        """选中模板 → 自动填入右栏"""
        template_name = self.template_var.get()
        if not template_name or not self.file_data:
            return

        items = self.templates.get(template_name, [])
        if not items:
            return

        self._apply_template_to_tree(items)

    def _apply_template_to_tree(self, items):
        """将模板词条按顺序填入新文件名列（不覆盖手动编辑的行）"""
        for i, fd in enumerate(self.file_data):
            item_id = self.tree.get_children()[i]

            # 跳过手动编辑的行
            if self.manual_flags.get(item_id, False):
                continue

            if i < len(items):
                new_name = items[i] + fd["ext"]
                self.tree.set(item_id, "new", new_name)
                fd["new_base"] = items[i]
                fd["is_manual"] = False
                self.overflow_items.discard(item_id)

                # 清除手动标签
                current_tags = self.tree.item(item_id, "tags")
                if "manual" in current_tags:
                    new_tags = tuple(t for t in current_tags if t != "manual")
                    self.tree.item(item_id, tags=new_tags)
            else:
                # 模板词条不足
                self.tree.set(item_id, "new", "模板不足")
                fd["new_base"] = ""
                fd["is_manual"] = False
                self.overflow_items.add(item_id)

                current_tags = self.tree.item(item_id, "tags")
                if "overflow" not in current_tags:
                    new_tags = current_tags + ("overflow",)
                    self.tree.item(item_id, tags=new_tags)

    # ─── 文件操作 ──────────────────────────────────
    def _add_files_to_list(self, file_paths):
        """添加文件到列表（内部方法）"""
        added = 0
        for path in file_paths:
            if not os.path.isfile(path):
                continue
            # 避免重复
            existing = {fd["path"] for fd in self.file_data}
            if path in existing:
                continue

            orig_name = os.path.basename(path)
            root_part, ext = os.path.splitext(orig_name)

            fd = {
                "path": path,
                "orig_name": orig_name,
                "ext": ext,
                "new_base": "",
                "is_manual": False,
            }
            self.file_data.append(fd)

            # Treeview
            values = (orig_name, "")
            item_id = self.tree.insert("", tk.END, values=values)
            self.manual_flags[item_id] = False

            # Listbox（只显示文件名）
            self.file_listbox.insert(tk.END, orig_name)
            added += 1

        if added > 0:
            self._update_file_count()
            self.status_var.set(f"已添加 {added} 个文件")

            # 如果已有模板选中，自动填入
            template_name = self.template_var.get()
            if template_name:
                items = self.templates.get(template_name, [])
                if items:
                    self._apply_template_to_tree(items)

    def _add_files(self):
        """按钮：添加文件"""
        paths = filedialog.askopenfilenames(
            title="选择要重命名的文件",
            filetypes=[("所有文件", "*.*")]
        )
        if paths:
            self._add_files_to_list(paths)

    def _on_drop(self, event):
        """拖拽文件进入"""
        files = self._parse_drop_data(event.data)
        self._add_files_to_list(files)

    def _parse_drop_data(self, data):
        """解析拖拽数据，提取文件路径"""
        files = []
        # tkinterdnd2 返回的格式: {path1} {path2} ...
        # Windows 下可能是用花括号包裹带空格的路径
        if data.startswith("{"):
            # 花括号包裹格式
            parts = []
            current = ""
            in_brace = False
            for ch in data:
                if ch == "{":
                    in_brace = True
                    current = ""
                elif ch == "}":
                    in_brace = False
                    if current:
                        parts.append(current)
                elif in_brace:
                    current += ch
                elif ch == " " and not in_brace:
                    if current:
                        parts.append(current)
                        current = ""
                else:
                    current += ch
            if current:
                parts.append(current)
            files = [p for p in parts if os.path.isfile(p)]
        else:
            # 空格分割
            for p in data.split():
                p = p.strip()
                if os.path.isfile(p):
                    files.append(p)
        return files

    def _remove_selected_files(self):
        """移除选中的文件"""
        selected = self.file_listbox.curselection()
        if not selected:
            return

        # 从后往前删（避免索引错位）
        for idx in reversed(selected):
            # 删除 Treeview 对应行
            tree_children = self.tree.get_children()
            if idx < len(tree_children):
                item_id = tree_children[idx]
                self.tree.delete(item_id)
                self.manual_flags.pop(item_id, None)
                self.overflow_items.discard(item_id)

            self.file_listbox.delete(idx)
            del self.file_data[idx]

        self._update_file_count()
        self.status_var.set(f"已移除 {len(selected)} 个文件")

    def _clear_all_files(self):
        """清空所有文件"""
        if not self.file_data:
            return
        self.file_data.clear()
        self.file_listbox.delete(0, tk.END)
        for item_id in self.tree.get_children():
            self.tree.delete(item_id)
        self.manual_flags.clear()
        self.overflow_items.clear()
        self._update_file_count()
        self.status_var.set("已清空所有文件")

    def _clear_right_column(self):
        """清空右侧新文件名列，重置手动标记"""
        for i, fd in enumerate(self.file_data):
            tree_children = self.tree.get_children()
            item_id = tree_children[i]
            self.tree.set(item_id, "new", "")
            fd["new_base"] = ""
            fd["is_manual"] = False
            self.manual_flags[item_id] = False
            self.overflow_items.discard(item_id)
            # 清除所有标签
            self.tree.item(item_id, tags=())
        self.status_var.set("已清空目标名称")

    def _update_file_count(self):
        self.file_count_var.set(f"共 {len(self.file_data)} 个文件")

    # ─── 悬停提示 ──────────────────────────────────
    def _on_file_hover(self, event):
        """鼠标悬停显示完整路径"""
        idx = self.file_listbox.nearest(event.y)
        if 0 <= idx < len(self.file_data):
            tooltip = self.file_data[idx]["path"]
            self._show_tooltip(event, tooltip)
        else:
            self._hide_tooltip()

    def _show_tooltip(self, event, text):
        if hasattr(self, "_tooltip") and self._tooltip:
            self._tooltip.destroy()

        self._tooltip = tk.Toplevel(self.root)
        self._tooltip.wm_overrideredirect(True)
        self._tooltip.wm_geometry(f"+{event.x_root + 15}+{event.y_root + 10}")

        label = tk.Label(self._tooltip, text=text, background="#ffffcc",
                          relief=tk.SOLID, borderwidth=1, font=("", 9),
                          wraplength=500, justify=tk.LEFT)
        label.pack()

        # 自动消失
        self._tooltip.after(3000, self._hide_tooltip)

    def _hide_tooltip(self):
        if hasattr(self, "_tooltip") and self._tooltip:
            self._tooltip.destroy()
            self._tooltip = None

    # ─── 右键菜单 ──────────────────────────────────
    def _on_file_right_click(self, event):
        try:
            idx = self.file_listbox.nearest(event.y)
            if idx >= 0:
                self.file_listbox.selection_clear(0, tk.END)
                self.file_listbox.selection_set(idx)
        except Exception:
            pass
        self.file_context_menu.post(event.x_root, event.y_root)

    def _on_delete_key(self, event):
        """Delete 键移除选中"""
        # 只在文件列表有焦点时响应
        if self.root.focus_get() == self.file_listbox:
            self._remove_selected_files()

    # ─── Treeview 单元格编辑 ──────────────────────
    def _on_cell_double_click(self, event):
        """双击 Treeview 单元格进入编辑"""
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            return

        column = self.tree.identify_column(event.x)
        if column != "#2":  # 只允许编辑「新文件名」列
            return

        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return

        # 获取单元格坐标
        bbox = self.tree.bbox(item_id, column)
        if not bbox:
            return

        x, y, width, height = bbox

        # 当前值
        current_value = self.tree.set(item_id, "new")

        # 获取该文件在 file_data 中的索引
        tree_children = self.tree.get_children()
        idx = list(tree_children).index(item_id)
        fd = self.file_data[idx]

        # 编辑时只显示基础名（不含扩展名）
        edit_value = current_value
        if current_value == "模板不足":
            edit_value = ""

        # 在单元格上放置 Entry
        self.edit_entry = ttk.Entry(self.tree, font=("", 10))
        self.edit_entry.place(x=x, y=y, width=width, height=height)

        self.edit_entry.insert(0, edit_value)
        self.edit_entry.select_range(0, tk.END)
        self.edit_entry.focus_set()

        # 绑定保存事件
        self.edit_entry.bind("<Return>", lambda e: self._save_cell_edit(item_id, idx, fd))
        self.edit_entry.bind("<FocusOut>", lambda e: self._save_cell_edit(item_id, idx, fd))
        self.edit_entry.bind("<Escape>", lambda e: self._cancel_cell_edit())

    def _save_cell_edit(self, item_id, idx, fd, event=None):
        """保存单元格编辑"""
        if not self.edit_entry:
            return

        new_base = self.edit_entry.get().strip()
        self.edit_entry.destroy()
        self.edit_entry = None

        if new_base:
            new_full = new_base + fd["ext"]
            self.tree.set(item_id, "new", new_full)
            fd["new_base"] = new_base
            fd["is_manual"] = True
            self.manual_flags[item_id] = True
            self.overflow_items.discard(item_id)

            # 添加手动标签
            current_tags = self.tree.item(item_id, "tags")
            if "manual" not in current_tags:
                new_tags = tuple(t for t in current_tags if t != "overflow") + ("manual",)
                self.tree.item(item_id, tags=new_tags)
        else:
            # 清空
            self.tree.set(item_id, "new", "")
            fd["new_base"] = ""
            fd["is_manual"] = False
            self.manual_flags[item_id] = False
            self.overflow_items.discard(item_id)
            self.tree.item(item_id, tags=())

    def _cancel_cell_edit(self, event=None):
        """取消单元格编辑"""
        if self.edit_entry:
            self.edit_entry.destroy()
            self.edit_entry = None

    # ─── 执行重命名 ────────────────────────────────
    def _execute_rename(self):
        """执行批量重命名"""
        if not self.file_data:
            messagebox.showwarning("提示", "请先添加文件")
            return

        # ── 收集并校验 ──
        rename_list = []  # [(old_path, new_path, tree_item_id)]
        new_names_set = set()
        errors = []

        tree_children = self.tree.get_children()
        for i, fd in enumerate(self.file_data):
            item_id = tree_children[i]
            new_base = fd.get("new_base", "")

            if not new_base:
                errors.append(f"  {fd['orig_name']} → 新文件名为空")
                continue

            new_name = new_base + fd["ext"]
            new_path = os.path.join(os.path.dirname(fd["path"]), new_name)

            # 检查同批重名
            if new_name in new_names_set:
                errors.append(f"  {fd['orig_name']} → {new_name}（与同批其他文件重名）")
                continue

            # 检查与目标文件夹中已有文件冲突（排除自身）
            if os.path.exists(new_path) and os.path.normpath(new_path) != os.path.normpath(fd["path"]):
                errors.append(f"  {fd['orig_name']} → {new_name}（目标文件夹中已存在同名文件）")
                continue

            new_names_set.add(new_name)
            rename_list.append((fd["path"], new_path, item_id))

        # ── 错误处理 ──
        if errors:
            error_msg = "以下文件校验未通过：\n" + "\n".join(errors)
            messagebox.showerror("校验失败", error_msg)
            return

        if not rename_list:
            messagebox.showwarning("提示", "没有可执行的重命名操作")
            return

        # ── 确认预览 ──
        preview_lines = []
        for old_path, new_path, _ in rename_list:
            old_name = os.path.basename(old_path)
            new_name = os.path.basename(new_path)
            preview_lines.append(f"  {old_name}  →  {new_name}")

        preview_msg = f"即将重命名 {len(rename_list)} 个文件：\n\n" + "\n".join(preview_lines)
        preview_msg += "\n\n确定执行？"

        if not messagebox.askyesno("确认重命名", preview_msg):
            return

        # ── 执行 ──
        success = 0
        failed = 0

        for old_path, new_path, _ in rename_list:
            try:
                os.rename(old_path, new_path)
                success += 1
            except OSError as e:
                failed += 1
                messagebox.showerror("重命名失败", f"无法重命名文件：\n{old_path}\n\n错误：{e}")

        # ── 结果 ──
        result_msg = f"重命名完成！\n\n成功：{success} 个\n失败：{failed} 个"
        messagebox.showinfo("执行结果", result_msg)

        # ── 清空状态 ──
        self._clear_all_files()
        self.template_var.set("")

    # ─── 模板管理 ──────────────────────────────────
    def _open_template_manager(self):
        """打开模板管理窗口"""
        TemplateManager(self.root, on_close=self._on_template_manager_close)

    def _on_template_manager_close(self):
        """模板管理窗口关闭后刷新"""
        self._refresh_template_radios()

    def _reset_templates(self):
        """菜单：恢复默认模板"""
        if messagebox.askyesno("确认恢复",
                                "将删除所有自定义模板，恢复为内置默认模板。\n确定继续吗？"):
            reg_reset_all()
            self._refresh_template_radios()
            messagebox.showinfo("提示", "已恢复默认模板")

    # ─── 帮助 ──────────────────────────────────────
    def _show_about(self):
        messagebox.showinfo("关于",
                             f"{APP_NAME}\n\n"
                             "基于 Python + Tkinter 构建\n"
                             "模板数据存储于 Windows 注册表\n"
                             "HKEY_CURRENT_USER\\Software\\RenameTool")

    # ─── 窗口 ──────────────────────────────────────
    def _center_window(self):
        """窗口居中"""
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"+{x}+{y}")

    def _on_close(self):
        """关闭窗口"""
        self._hide_tooltip()
        self.root.destroy()


# ============================================================
# 入口
# ============================================================
def main():
    # 初始化注册表
    reg_initialize()

    # 创建主窗口（优先使用拖拽支持）
    if HAS_DND:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()

    app = RenameTool(root)
    root.mainloop()


if __name__ == "__main__":
    main()
