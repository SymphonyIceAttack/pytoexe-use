import json
import os
import datetime
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

# ===================== 全局配置 =====================
DATA_FILE = "high_school_errors.json"
IMAGE_DIR = "error_images"
os.makedirs(IMAGE_DIR, exist_ok=True)

COLOR_PRIMARY = "#547bc2"
COLOR_SECONDARY = "#A23B72"
COLOR_LIGHT = "#f5f7fa"
COLOR_DARK = "#333333"
COLOR_DANGER = "#e65252"

if os.name == "nt":
    FONT_MAIN = ("Microsoft YaHei", 10)
    FONT_TITLE = ("Microsoft YaHei", 12, "bold")
else:
    FONT_MAIN = ("SimHei", 10)
    FONT_TITLE = ("SimHei", 12, "bold")

# ===================== 数据操作 =====================
def load_errors():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

# 修复：把indent参数移到json.dump里，open函数只保留必要参数
def save_errors(errors):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(errors, f, ensure_ascii=False, indent=4)

def get_error_by_id(error_id):
    for e in load_errors():
        if e.get("id") == error_id:
            return e
    return None

def update_error(error_id, data):
    lst = load_errors()
    for i, e in enumerate(lst):
        if e.get("id") == error_id:
            lst[i] = data
            save_errors(lst)
            return True
    return False

def analyze_knowledge_errors():
    errors = load_errors()
    d = {}
    for e in errors:
        ks = e.get("知识点", "").strip()
        if not ks:
            continue
        for k in [x.strip() for x in ks.split(",") if x.strip()]:
            d[k] = d.get(k, 0) + 1
    return d

# ===================== 批量导入JSON =====================
def batch_import_from_json():
    path = filedialog.askopenfilename(
        title="选择JSON文件",
        filetypes=[("JSON文件", "*.json")],
    )
    if not path:
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            import_list = json.load(f)
        if not isinstance(import_list, list):
            messagebox.showerror("错误", "仅支持导入数组格式的JSON")
            return
        current = load_errors()
        max_id = max([e.get("id", 0) for e in current], default=0)
        for item in import_list:
            max_id += 1
            new_item = {
                "id": max_id,
                "题型": item.get("题型", ""),
                "知识点": item.get("知识点", ""),
                "题目": item.get("题目", ""),
                "题目图片": item.get("题目图片", ""),
                "答案": item.get("答案", ""),
                "解析": item.get("解析", ""),
                "错因分析": item.get("错因分析", ""),
                "举一反三": item.get("举一反三", ""),
            }
            current.append(new_item)
        save_errors(current)
        messagebox.showinfo("成功", f"导入完成，共 {len(import_list)} 题")
    except Exception as ex:
        messagebox.showerror("导入失败", str(ex))

# ===================== PDF导出（不超边距） =====================
def export_selected_to_pdf(selected_errors):
    pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
    fontname = 'STSong-Light'
    if not selected_errors:
        messagebox.showwarning("提示", "请选择题目")
        return
    path = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF文件", "*.pdf")],
        initialfile="错题本.pdf"
    )
    if not path:
        return
    try:
        c = canvas.Canvas(path, pagesize=A4)
        w, h = A4
        left_margin = 2 * cm
        max_img_w = w - 4 * cm

        for err in selected_errors:
            y = h - 2 * cm
            c.setFont(fontname, 12)

            c.drawString(left_margin, y, f"题型：{err.get('题型','')}")
            y -= 16
            c.drawString(left_margin, y, f"知识点：{err.get('知识点','无')}")
            y -= 20

            q_text = err.get("题目", "").strip()
            if q_text:
                for line in q_text.split("\n"):
                    if y < 3 * cm:
                        c.showPage()
                        y = h - 2 * cm
                    c.drawString(left_margin, y, line.strip())
                    y -= 16
                y -= 10

            img_path = err.get("题目图片")
            if img_path and os.path.exists(img_path):
                try:
                    im = Image.open(img_path)
                    iw, ih = im.size
                    scale = max_img_w / iw if iw > max_img_w else 0.9
                    dh = ih * scale
                    if y - dh < 2 * cm:
                        c.showPage()
                        y = h - 2 * cm
                    c.drawImage(img_path, left_margin, y - dh, width=iw*scale, height=dh)
                    y -= dh + 20
                except:
                    c.drawString(left_margin, y, "图片无法显示")
                    y -= 20

            if y < 3 * cm:
                c.showPage()
                y = h - 2 * cm
            c.drawString(left_margin, y, f"答案：{err.get('答案','无')}")
            y -= 16
            c.drawString(left_margin, y, f"解析：{err.get('解析','无')}")
            y -= 16
            c.drawString(left_margin, y, f"错因：{err.get('错因分析','无')}")
            c.showPage()

        c.save()
        messagebox.showinfo("成功", "PDF导出完成！")
    except Exception as ex:
        messagebox.showerror("错误", str(ex))

# ===================== GUI =====================
class ErrorBookGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("错题本系统 · 完整版")
        self.root.geometry("1000x700")
        self.root.minsize(850, 600)
        self.root.configure(bg=COLOR_LIGHT)
        self.current_edit_id = None
        self.img_preview = {}
        self.build_ui()

    def build_ui(self):
        top = tk.Frame(self.root, bg=COLOR_PRIMARY, height=50)
        top.pack(fill=tk.X)
        tk.Label(top, text="📚 错题本管理系统", font=("Microsoft YaHei", 16, "bold"),
                 bg=COLOR_PRIMARY, fg="white").pack(expand=True, pady=8)

        main = tk.Frame(self.root, bg=COLOR_LIGHT)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left = tk.Frame(main, width=180, bg=COLOR_LIGHT)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left.pack_propagate(False)

        btn_common = {
            "font": FONT_TITLE,
            "bg": COLOR_PRIMARY,
            "fg": "white",
            "relief": tk.FLAT,
            "height": 2,
            "activebackground": COLOR_SECONDARY
        }

        tk.Button(left, text="录入错题", **btn_common, command=self.show_add).pack(fill=tk.X, pady=4)
        tk.Button(left, text="批量导入", **btn_common, command=batch_import_from_json).pack(fill=tk.X, pady=4)
        tk.Button(left, text="查询/修改", **btn_common, command=self.show_list).pack(fill=tk.X, pady=4)
        tk.Button(left, text="知识点分析", **btn_common, command=self.show_analysis).pack(fill=tk.X, pady=4)
        tk.Button(left, text="导出PDF", **btn_common, command=self.export_pdf).pack(fill=tk.X, pady=4)

        self.panel = tk.Frame(main, bg="white", bd=1, relief=tk.RIDGE)
        self.panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.show_list()

    def clear(self):
        for w in self.panel.winfo_children():
            w.destroy()

    # ===================== 查看详情 + 打印 =====================
    def show_detail(self, error_id):
        err = get_error_by_id(error_id)
        if not err:
            messagebox.showwarning("提示", "未找到该题目")
            return

        top = tk.Toplevel(self.root)
        top.title("题目详情")
        top.geometry("700x550")
        frame = tk.Frame(top, padx=20, pady=15)
        frame.pack(fill=tk.BOTH, expand=True)

        fields = [
            ("ID", err.get("id")),
            ("题型", err.get("题型")),
            ("知识点", err.get("知识点")),
            ("", ""),
            ("题目", err.get("题目", "无")),
            ("答案", err.get("答案", "无")),
            ("解析", err.get("解析", "无")),
            ("错因分析", err.get("错因分析", "无")),
            ("举一反三", err.get("举一反三", "无")),
        ]

        for label, value in fields:
            if not label:
                tk.Label(frame, text="", bg="white").pack(anchor="w")
                continue
            lb = tk.Label(
                frame, text=f"{label}：{value}",
                anchor="w", justify=tk.LEFT, font=FONT_MAIN, bg="white"
            )
            lb.pack(anchor="w", pady=2)

        # 打印按钮
        def print_detail():
            try:
                import tempfile
                with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt", encoding="utf-8") as f:
                    f.write(f"【ID】{err.get('id')}\n")
                    f.write(f"【题型】{err.get('题型')}\n")
                    f.write(f"【知识点】{err.get('知识点')}\n\n")
                    f.write(f"【题目】\n{err.get('题目','无')}\n\n")
                    f.write(f"【答案】\n{err.get('答案','无')}\n\n")
                    f.write(f"【解析】\n{err.get('解析','无')}\n\n")
                    f.write(f"【错因分析】\n{err.get('错因分析','无')}\n\n")
                    f.write(f"【举一反三】\n{err.get('举一反三','无')}\n")
                os.startfile(f.name, "print")
            except:
                messagebox.showwarning("打印", "当前系统不支持直接打印，可复制内容手动打印")

        tk.Button(frame, text="打印本题", command=print_detail, bg=COLOR_PRIMARY, fg="white").pack(pady=10)

    # ===================== 错题列表（双击查看详情） =====================
    def show_list(self):
        self.clear()
        tk.Label(self.panel, text="错题列表", font=FONT_TITLE, bg="white").pack(anchor="w", padx=20, pady=10)
        f = tk.Frame(self.panel, bg="white")
        f.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        sb = ttk.Scrollbar(f)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree = ttk.Treeview(f, columns=("id", "type", "know"), show="headings", yscrollcommand=sb.set)
        sb.config(command=self.tree.yview)
        self.tree.heading("id", text="ID")
        self.tree.heading("type", text="题型")
        self.tree.heading("know", text="知识点")
        self.tree.column("id", width=60)
        self.tree.column("type", width=180)
        self.tree.column("know", width=500)
        self.tree.pack(fill=tk.BOTH, expand=True)

        for e in load_errors():
            self.tree.insert("", "end", values=(e.get("id", ""), e.get("题型", ""), e.get("知识点", "")))

        def on_double_click(event):
            item = self.tree.selection()
            if not item:
                return
            # 只取第一个选中的条目查看详情
            vid = self.tree.item(item[0])["values"][0]
            self.show_detail(int(vid))

        self.tree.bind("<Double-1>", on_double_click)

        btn_f = tk.Frame(self.panel, bg="white")
        btn_f.pack(pady=5)
        ttk.Button(btn_f, text="添加", command=self.show_add).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_f, text="修改", command=self.edit_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_f, text="删除", command=self.delete_selected).pack(side=tk.LEFT, padx=5)

    # ===================== 修改功能（仅支持单行修改） =====================
    def edit_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请选择一项进行修改")
            return
        if len(sel) > 1:
            messagebox.showwarning("提示", "一次只能修改一道题目，请只选择一行")
            return
        # 取第一个选中的条目ID
        self.current_edit_id = int(self.tree.item(sel[0])["values"][0])
        self.show_add()

    # ===================== 删除功能（支持单行/多行删除） =====================
    def delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请先选择要删除的题目")
            return
        
        # 获取所有选中条目的ID
        delete_ids = []
        for item in sel:
            try:
                item_id = int(self.tree.item(item)["values"][0])
                delete_ids.append(item_id)
            except:
                continue
        
        if not delete_ids:
            messagebox.showwarning("提示", "未识别到可删除的题目ID")
            return
        
        # 确认删除
        confirm = messagebox.askyesno("确认删除", f"确定要删除选中的 {len(delete_ids)} 道题目吗？删除后无法恢复！")
        if not confirm:
            return
        
        # 过滤掉要删除的题目
        current_errors = load_errors()
        new_errors = [e for e in current_errors if e.get("id") not in delete_ids]
        save_errors(new_errors)
        
        # 刷新列表
        messagebox.showinfo("成功", f"已删除 {len(delete_ids)} 道题目")
        self.show_list()

    # ===================== 录入/修改 =====================
    def show_add(self):
        self.clear()
        err = get_error_by_id(self.current_edit_id) if self.current_edit_id else None
        tk.Label(self.panel, text="修改错题" if err else "录入错题", font=FONT_TITLE, bg="white").pack(anchor="w", padx=20, pady=10)
        f = tk.Frame(self.panel, bg="white")
        f.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        f.grid_columnconfigure(1, weight=1)

        row = 0
        tk.Label(f, text="题型：", bg="white").grid(row=row, column=0, sticky="w", padx=5, pady=4)
        self.t_var = tk.StringVar(value=err.get("题型", "") if err else "")
        ttk.Entry(f, textvariable=self.t_var).grid(row=row, column=1, sticky="ew", padx=5, pady=4)

        row += 1
        tk.Label(f, text="知识点：", bg="white").grid(row=row, column=0, sticky="w", padx=5, pady=4)
        self.k_var = tk.StringVar(value=err.get("知识点", "") if err else "")
        ttk.Entry(f, textvariable=self.k_var).grid(row=row, column=1, sticky="ew", padx=5, pady=4)

        row += 1
        tk.Label(f, text="题目文字：", bg="white").grid(row=row, column=0, sticky="nw", padx=5, pady=4)
        self.q_text = tk.Text(f, height=4)
        self.q_text.grid(row=row, column=1, sticky="ew", padx=5, pady=4)
        if err and err.get("题目"):
            self.q_text.insert("1.0", err.get("题目"))

        row += 1
        tk.Label(f, text="题目图片：", bg="white").grid(row=row, column=0, sticky="w", padx=5, pady=4)
        self.img_var = tk.StringVar(value=err.get("题目图片", "") if err else "")
        ttk.Entry(f, textvariable=self.img_var).grid(row=row, column=1, sticky="ew", padx=5, pady=4)
        def pick_img():
            p = filedialog.askopenfilename(filetypes=[("图片", "*.png;*.jpg;*.jpeg")])
            if p:
                self.img_var.set(p)
        ttk.Button(f, text="选择", command=pick_img).grid(row=row, column=2, padx=5, pady=4)

        row += 1
        tk.Label(f, text="答案：", bg="white").grid(row=row, column=0, sticky="w", padx=5, pady=4)
        self.ans_var = tk.StringVar(value=err.get("答案", "") if err else "")
        ttk.Entry(f, textvariable=self.ans_var).grid(row=row, column=1, sticky="ew", padx=5, pady=4)

        row += 1
        tk.Label(f, text="解析：", bg="white").grid(row=row, column=0, sticky="nw", padx=5, pady=4)
        self.ana_text = tk.Text(f, height=3)
        self.ana_text.grid(row=row, column=1, sticky="ew", padx=5, pady=4)
        if err and err.get("解析"):
            self.ana_text.insert("1.0", err.get("解析"))

        row += 1
        tk.Label(f, text="错因分析：", bg="white").grid(row=row, column=0, sticky="nw", padx=5, pady=4)
        self.reason_text = tk.Text(f, height=3)
        self.reason_text.grid(row=row, column=1, sticky="ew", padx=5, pady=4)
        if err and err.get("错因分析"):
            self.reason_text.insert("1.0", err.get("错因分析"))

        row += 1
        tk.Label(f, text="举一反三：", bg="white").grid(row=row, column=0, sticky="nw", padx=5, pady=4)
        self.ext_text = tk.Text(f, height=2)
        self.ext_text.grid(row=row, column=1, sticky="ew", padx=5, pady=4)
        if err and err.get("举一反三"):
            self.ext_text.insert("1.0", err.get("举一反三"))

        def save():
            data = {
                "id": self.current_edit_id or max([e.get("id", 0) for e in load_errors()], default=0) + 1,
                "题型": self.t_var.get().strip(),
                "知识点": self.k_var.get().strip(),
                "题目": self.q_text.get("1.0", tk.END).strip(),
                "题目图片": self.img_var.get().strip(),
                "答案": self.ans_var.get().strip(),
                "解析": self.ana_text.get("1.0", tk.END).strip(),
                "错因分析": self.reason_text.get("1.0", tk.END).strip(),
                "举一反三": self.ext_text.get("1.0", tk.END).strip()
            }
            if self.current_edit_id:
                update_error(self.current_edit_id, data)
            else:
                lst = load_errors()
                lst.append(data)
                save_errors(lst)
            messagebox.showinfo("成功", "已保存")
            self.current_edit_id = None
            self.show_list()

        row += 1
        ttk.Button(f, text="保存", command=save).grid(row=row, column=1, pady=10)

    # ===================== 知识点分析 =====================
    def show_analysis(self):
        self.clear()
        tk.Label(self.panel, text="知识点统计", font=FONT_TITLE, bg="white").pack(anchor="w", padx=20, pady=10)
        data = analyze_knowledge_errors()
        if not data:
            tk.Label(self.panel, text="暂无知识点数据", bg="white").pack(pady=20)
            return
        try:
            plt.switch_backend('Agg')
            plt.rcParams["font.family"] = ["SimHei", "Microsoft YaHei"]
            plt.rcParams['axes.unicode_minus'] = False
            plt.figure(figsize=(8, 5))
            keys = list(data.keys())
            vals = list(data.values())
            plt.bar(keys, vals, color=COLOR_PRIMARY)
            plt.title("知识点错题数量统计")
            plt.xticks(rotation=30, ha='right')
            plt.tight_layout()
            img_path = os.path.join(IMAGE_DIR, "analysis.png")
            plt.savefig(img_path, dpi=120)
            plt.close()
            img = Image.open(img_path)
            img.thumbnail((750, 450))
            photo = ImageTk.PhotoImage(img)
            lbl = tk.Label(self.panel, image=photo, bg="white")
            lbl.image = photo
            lbl.pack(pady=10)
        except Exception as e:
            tk.Label(self.panel, text=f"图表加载异常：{e}", fg="red", bg="white").pack(pady=20)

    # ===================== 导出PDF =====================
    def export_pdf(self):
        errors = load_errors()
        if not errors:
            messagebox.showwarning("提示", "暂无错题")
            return
        top = tk.Toplevel(self.root)
        top.title("选择导出")
        top.geometry("700x450")
        tk.Label(top, text="Ctrl 多选，然后导出选中").pack(pady=5)
        tree = ttk.Treeview(top, columns=("id", "t", "k"), show="headings", selectmode="extended")
        tree.heading("id", text="ID")
        tree.heading("t", text="题型")
        tree.heading("k", text="知识点")
        tree.column("id", width=60)
        tree.column("t", width=180)
        tree.column("k", width=450)
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        for e in errors:
            tree.insert("", "end", values=(e.get("id", ""), e.get("题型", ""), e.get("知识点", "")))

        def go_export():
            sels = tree.selection()
            if not sels:
                messagebox.showwarning("提示", "请先选择题目标题")
                return
            ids = [int(tree.item(i)["values"][0]) for i in sels]
            export_selected_to_pdf([e for e in errors if e.get("id") in ids])
            top.destroy()

        ttk.Button(top, text="导出选中", command=go_export).pack(pady=8)

if __name__ == "__main__":
    root = tk.Tk()
    ErrorBookGUI(root)
    root.mainloop()