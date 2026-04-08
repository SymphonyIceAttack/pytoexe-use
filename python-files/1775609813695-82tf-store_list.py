import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog, filedialog
import json
import os
import pandas as pd
from datetime import datetime

DATA_FILE = "store_data.json"
TEMPLATE_FILE = "goods_templates.json"

class StoreApp:
    def __init__(self, root):
        self.root = root
        self.root.title("门店备货清单管理系统")
        self.root.geometry("1250x880")

        self.data_list = self.load_data()
        self.templates = self.load_templates()

        # 标题
        tk.Label(root, text="🏪 门店备货清单管理系统", font=("微软雅黑", 22, "bold")).pack(pady=10)

        # ========== 录入区域 ==========
        input_frame = ttk.LabelFrame(root, text="信息录入")
        input_frame.pack(fill="x", padx=20, pady=5)

        # 第0行：模板
        ttk.Label(input_frame, text="货物模板：").grid(row=0, column=0, padx=4, pady=6)
        self.template_var = tk.StringVar()
        self.template_combo = ttk.Combobox(
            input_frame, textvariable=self.template_var,
            values=[t["名称"] for t in self.templates], width=16
        )
        self.template_combo.grid(row=0, column=1)
        ttk.Button(input_frame, text="✅ 一键导入", command=self.load_template).grid(row=0, column=2, padx=4)
        ttk.Button(input_frame, text="💾 保存为模板", command=self.save_as_template).grid(row=0, column=3, padx=4)

        # 第1行
        ttk.Label(input_frame, text="日期：").grid(row=1, column=0, padx=4)
        self.date = ttk.Entry(input_frame, width=12)
        self.date.grid(row=1, column=1)
        self.date.insert(0, datetime.now().strftime("%Y-%m-%d"))

        ttk.Label(input_frame, text="门店号：").grid(row=1, column=2, padx=4)
        self.store_id = ttk.Entry(input_frame, width=8)
        self.store_id.grid(row=1, column=3)

        ttk.Label(input_frame, text="手机号：").grid(row=1, column=4, padx=4)
        self.phone = ttk.Entry(input_frame, width=15)
        self.phone.grid(row=1, column=5)

        ttk.Label(input_frame, text="项目名称：").grid(row=1, column=6, padx=4)
        self.item = ttk.Entry(input_frame, width=20)
        self.item.grid(row=1, column=7)

        # 第2行
        ttk.Label(input_frame, text="数量：").grid(row=2, column=0, padx=4, pady=6)
        self.num = ttk.Entry(input_frame, width=8)
        self.num.grid(row=2, column=1)

        ttk.Label(input_frame, text="单位：").grid(row=2, column=2, padx=4)
        self.unit = ttk.Entry(input_frame, width=8)
        self.unit.grid(row=2, column=3)

        ttk.Label(input_frame, text="来源：").grid(row=2, column=4, padx=4)
        self.source = ttk.Entry(input_frame, width=12)
        self.source.grid(row=2, column=5)

        ttk.Label(input_frame, text="物流单号：").grid(row=2, column=6, padx=4)
        self.logi = ttk.Entry(input_frame, width=20)
        self.logi.grid(row=2, column=7)

        # 第3行
        ttk.Label(input_frame, text="备货：").grid(row=3, column=0, padx=4, pady=6)
        self.prepare = tk.StringVar(value="否")
        ttk.Combobox(input_frame, textvariable=self.prepare, values=["是", "否"], width=6).grid(row=3, column=1)

        ttk.Label(input_frame, text="发货：").grid(row=3, column=2, padx=4)
        self.send = tk.StringVar(value="否")
        ttk.Combobox(input_frame, textvariable=self.send, values=["是", "否"], width=6).grid(row=3, column=3)

        ttk.Label(input_frame, text="收货：").grid(row=3, column=4, padx=4)
        self.receive = tk.StringVar(value="否")
        ttk.Combobox(input_frame, textvariable=self.receive, values=["是", "否"], width=6).grid(row=3, column=5)

        ttk.Label(input_frame, text="备注：").grid(row=3, column=6, padx=4)
        self.note = ttk.Entry(input_frame, width=24)
        self.note.grid(row=3, column=7)

        # ========== 按钮区 ==========
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=6)
        ttk.Button(btn_frame, text="✅ 提交", command=self.submit, width=10).pack(side="left", pad=4)
        ttk.Button(btn_frame, text="🧹 清空", command=self.clear, width=10).pack(side="left", pad=4)
        ttk.Button(btn_frame, text="📋 剪贴板识别", command=self.paste_clip, width=12).pack(side="left", pad=4)
        ttk.Button(btn_frame, text="🧾 打印小票", command=self.print_ticket, width=12).pack(side="left", pad=4)
        ttk.Button(btn_frame, text="📤 导出Excel", command=self.export_excel, width=12).pack(side="left", pad=4)
        ttk.Button(btn_frame, text="📂 Excel批量导入", command=self.import_from_excel, width=16).pack(side="left", pad=4)

        # ========== 搜索 ==========
        search_frame = ttk.LabelFrame(root, text="查询操作")
        search_frame.pack(fill="x", padx=20, pady=3)
        ttk.Label(search_frame, text="搜索关键词：").pack(side="left", pad=5)
        self.search_key = ttk.Entry(search_frame, width=35)
        self.search_key.pack(side="left", pad=5)
        ttk.Button(search_frame, text="搜索", command=self.do_search).pack(side="left", pad=4)
        ttk.Button(search_frame, text="显示全部", command=self.show_all).pack(side="left", pad=4)
        ttk.Button(search_frame, text="修改", command=self.edit_item).pack(side="left", pad=4)
        ttk.Button(search_frame, text="删除", command=self.del_item).pack(side="left", pad=4)

        # ========== 列表 ==========
        tk.Label(root, text="备货清单列表", font=("微软雅黑", 12)).pack()
        self.text_area = scrolledtext.ScrolledText(root, width=150, height=36)
        self.text_area.pack(padx=20, pady=5, fill="both", expand=True)

        self.show_all()

    # ================== 数据 ==================
    def load_data(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def save_data(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data_list, f, ensure_ascii=False, indent=2)

    def load_templates(self):
        if os.path.exists(TEMPLATE_FILE):
            with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return [
            {"名称": "矿泉水大桶", "单位": "桶", "备注": "常规备货", "来源": "总部"},
            {"名称": "矿泉水小瓶", "单位": "箱", "备注": "常规备货", "来源": "总部"},
            {"名称": "纸巾", "单位": "包", "备注": "门店用品", "来源": "采购"},
            {"名称": "纸杯", "单位": "袋", "备注": "门店用品", "来源": "采购"},
            {"名称": "清洁液", "单位": "瓶", "备注": "清洁用品", "来源": "采购"}
        ]

    def save_templates(self):
        with open(TEMPLATE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.templates, f, ensure_ascii=False, indent=2)

    # ================== 模板功能 ==================
    def load_template(self):
        t_name = self.template_var.get()
        if not t_name:
            messagebox.showwarning("提示", "请选择模板")
            return
        for t in self.templates:
            if t["名称"] == t_name:
                self.item.delete(0, tk.END)
                self.item.insert(0, t["名称"])
                self.unit.delete(0, tk.END)
                self.unit.insert(0, t["单位"])
                self.note.delete(0, tk.END)
                self.note.insert(0, t["备注"])
                self.source.delete(0, tk.END)
                self.source.insert(0, t["来源"])
                messagebox.showinfo("成功", f"已导入：{t_name}")
                return
        messagebox.showerror("错误", "模板不存在")

    def save_as_template(self):
        item_name = self.item.get().strip()
        unit = self.unit.get().strip()
        note = self.note.get().strip()
        source = self.source.get().strip()
        if not item_name:
            messagebox.showwarning("提示", "项目名称不能为空")
            return
        for t in self.templates:
            if t["名称"] == item_name:
                if not messagebox.askyesno("提示", "模板已存在，是否覆盖？"):
                    return
                self.templates.remove(t)
                break
        self.templates.append({
            "名称": item_name,
            "单位": unit,
            "备注": note,
            "来源": source
        })
        self.save_templates()
        self.template_combo["values"] = [t["名称"] for t in self.templates]
        messagebox.showinfo("成功", "模板已保存")

    # ================== 【核心】Excel批量导入 ==================
    def import_from_excel(self):
        path = filedialog.askopenfilename(
            title="选择Excel文件",
            filetypes=[("Excel文件", "*.xlsx;*.xls")]
        )
        if not path:
            return

        try:
            df = pd.read_excel(path)
            required = ["日期", "项目名称", "数量"]
            for col in required:
                if col not in df.columns:
                    messagebox.showerror("错误", f"Excel必须包含列：{required}")
                    return

            count = 0
            for _, row in df.iterrows():
                item = str(row["项目名称"]).strip()
                num = str(row["数量"]).strip()
                if not item or not num:
                    continue
                try:
                    num = str(int(float(num)))
                except:
                    continue

                data = {
                    "序号": len(self.data_list)+1,
                    "日期": str(row.get("日期", datetime.now().strftime("%Y-%m-%d"))).strip(),
                    "门店号": str(row.get("门店号", "")).strip(),
                    "手机号": str(row.get("手机号", "")).strip(),
                    "项目名称": item,
                    "数量": num,
                    "单位": str(row.get("单位", "")).strip(),
                    "来源": str(row.get("来源", "")).strip(),
                    "物流单号": str(row.get("物流单号", "")).strip(),
                    "备货": str(row.get("备货", "否")).strip(),
                    "发货": str(row.get("发货", "否")).strip(),
                    "收货": str(row.get("收货", "否")).strip(),
                    "备注": str(row.get("备注", "")).strip()
                }
                self.data_list.append(data)
                count +=1

            self.save_data()
            self.show_all()
            messagebox.showinfo("成功", f"批量导入完成！共导入 {count} 条数据")
        except Exception as e:
            messagebox.showerror("导入失败", str(e))

    # ================== 提交 ==================
    def submit(self):
        date = self.date.get().strip()
        store_id = self.store_id.get().strip()
        phone = self.phone.get().strip()
        item = self.item.get().strip()
        num = self.num.get().strip()
        unit = self.unit.get().strip()
        source = self.source.get().strip()
        logi = self.logi.get().strip()
        prepare = self.prepare.get()
        send = self.send.get()
        receive = self.receive.get()
        note = self.note.get().strip()

        if not item or not num:
            messagebox.showwarning("提示", "项目名称和数量不能为空")
            return

        item_data = {
            "序号": len(self.data_list)+1,
            "日期": date,
            "门店号": store_id,
            "手机号": phone,
            "项目名称": item,
            "数量": num,
            "单位": unit,
            "来源": source,
            "物流单号": logi,
            "备货": prepare,
            "发货": send,
            "收货": receive,
            "备注": note
        }
        self.data_list.append(item_data)
        self.save_data()
        messagebox.showinfo("成功", "已保存")
        self.clear()
        self.show_all()

    def clear(self):
        for w in [self.store_id,self.phone,self.item,self.num,self.unit,self.source,self.logi,self.note]:
            w.delete(0,tk.END)
        self.date.delete(0,tk.END)
        self.date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.prepare.set("否")
        self.send.set("否")
        self.receive.set("否")
        self.template_var.set("")

    def paste_clip(self):
        try:
            txt = self.root.clipboard_get().strip()
            self.item.delete(0,tk.END)
            self.item.insert(0,txt)
            messagebox.showinfo("成功","已粘贴到项目名称")
        except:
            messagebox.showerror("错误","剪贴板读取失败")

    def print_ticket(self):
        info = f"""
====== 门店备货单 ======
日期：{self.date.get()}
门店号：{self.store_id.get() or '无'}
手机号：{self.phone.get() or '无'}
项目：{self.item.get()}
数量：{self.num.get()} {self.unit.get()}
来源：{self.source.get() or '无'}
物流单号：{self.logi.get() or '无'}
备货：{self.prepare.get()} 发货：{self.send.get()} 收货：{self.receive.get()}
备注：{self.note.get() or '无'}
========================
        """
        messagebox.showinfo("小票预览", info.strip())

    def show_all(self):
        self.text_area.delete(1.0,tk.END)
        for i,it in enumerate(self.data_list,1):
            line = (f"[{i}] {it['日期']} | 门店:{it['门店号']} | 电话:{it['手机号']} | "
                    f"项目:{it['项目名称']} | 数量:{it['数量']}{it['单位']} | 来源:{it['来源']} | "
                    f"物流:{it['物流单号']} | 备货:{it['备货']} 发货:{it['发货']} 收货:{it['收货']} | "
                    f"备注:{it['备注']}\n{'-'*230}\n")
            self.text_area.insert(tk.END, line)

    def do_search(self):
        key = self.search_key.get().strip()
        if not key:
            return
        res = [r for r in self.data_list if key in str(r.values())]
        self.text_area.delete(1.0,tk.END)
        for r in res:
            self.text_area.insert(tk.END, f"{r}\n------------------------------------\n")

    def edit_item(self):
        idx = simpledialog.askinteger("修改", "输入序号：")
        if not idx or idx<1 or idx>len(self.data_list):
            return
        it = self.data_list[idx-1]
        date = simpledialog.askstring("修改","日期：",initialvalue=it["日期"])
        store = simpledialog.askstring("修改","门店号：",initialvalue=it["门店号"])
        phone = simpledialog.askstring("修改","手机号：",initialvalue=it["手机号"])
        item = simpledialog.askstring("修改","项目名称：",initialvalue=it["项目名称"])
        num = simpledialog.askstring("修改","数量：",initialvalue=it["数量"])
        unit = simpledialog.askstring("修改","单位：",initialvalue=it["单位"])
        source = simpledialog.askstring("修改","来源：",initialvalue=it["来源"])
        logi = simpledialog.askstring("修改","物流单号：",initialvalue=it["物流单号"])
        prep = simpledialog.askstring("修改","备货(是/否)：",initialvalue=it["备货"])
        send = simpledialog.askstring("修改","发货(是/否)：",initialvalue=it["发货"])
        recv = simpledialog.askstring("修改","收货(是/否)：",initialvalue=it["收货"])
        note = simpledialog.askstring("修改","备注：",initialvalue=it["备注"])
        if item and num:
            it.update({
                "日期":date,"门店号":store,"手机号":phone,"项目名称":item,"数量":num,
                "单位":unit,"来源":source,"物流单号":logi,"备货":prep,"发货":send,
                "收货":recv,"备注":note
            })
            self.save_data()
            self.show_all()
            messagebox.showinfo("成功","修改完成")

    def del_item(self):
        idx = simpledialog.askinteger("删除","输入序号：")
        if idx and 1<=idx<=len(self.data_list):
            del self.data_list[idx-1]
            self.save_data()
            self.show_all()
            messagebox.showinfo("成功","已删除")

    def export_excel(self):
        if not self.data_list:
            messagebox.showwarning("提示","无数据")
            return
        pd.DataFrame(self.data_list).to_excel("门店备货清单.xlsx", index=False)
        messagebox.showinfo("成功","已导出：门店备货清单.xlsx")

if __name__ == "__main__":
    root = tk.Tk()
    StoreApp(root)
    root.mainloop()