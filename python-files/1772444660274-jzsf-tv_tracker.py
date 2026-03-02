import os
import json
import webbrowser
from datetime import datetime, timedelta
from tkinter import *
from tkinter import ttk, messagefont, simpledialog, messagebox
from functools import partial

# 数据文件存储路径
DATA_FILE = "shows.json"
WEEKDAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
# 星期映射: 0=周一 ... 6=周日 (与datetime.weekday()一致)

class ScrollableFrame(ttk.Frame):
    """一个可滚动的框架，用于放置七天的列"""
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.canvas = Canvas(self, borderwidth=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.inner_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.inner_frame.bind("<Configure>", self._on_frame_configure)

    def _on_frame_configure(self, event):
        """更新canvas的滚动区域"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))


class TvTrackerApp(Tk):
    def __init__(self):
        super().__init__()
        self.title("追剧助手 · 自动更新集数")
        self.geometry("1300x700")
        self.resizable(True, True)

        # 数据
        self.shows = []          # 剧集列表
        self.last_update = None   # 上次自动更新的日期 (datetime.date对象)

        # 加载数据 (如果文件存在)
        self.load_data()

        # 创建界面
        self.create_widgets()

        # 自动更新 (基于日期变化)
        self.apply_auto_update()

        # 启动定时检查 (每小时检查一次日期变化)
        self.schedule_check()

        # 绑定关闭事件，确保退出前保存
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    # ---------- 数据持久化 ----------
    def load_data(self):
        """从JSON文件加载数据，若文件不存在则初始化"""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.shows = data.get("shows", [])
                last_str = data.get("last_update")
                if last_str:
                    self.last_update = datetime.strptime(last_str, "%Y-%m-%d").date()
                else:
                    self.last_update = datetime.now().date()
            except Exception as e:
                messagebox.showerror("错误", f"读取数据文件失败: {e}\n将使用默认数据。")
                self.shows = []
                self.last_update = datetime.now().date()
        else:
            self.shows = []
            self.last_update = datetime.now().date()
            self.save_data()   # 创建默认文件

    def save_data(self):
        """保存剧集数据和最后更新日期到JSON"""
        data = {
            "shows": self.shows,
            "last_update": self.last_update.strftime("%Y-%m-%d") if self.last_update else None
        }
        try:
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("错误", f"保存数据失败: {e}")

    # ---------- 核心逻辑: 自动更新集数 ----------
    def apply_auto_update(self):
        """根据上次更新日期与今天的差距，对相应更新日的剧集增加集数"""
        today = datetime.now().date()
        if self.last_update is None:
            self.last_update = today
            self.save_data()
            return

        # 如果上次更新日期 >= 今天，不需要更新
        if self.last_update >= today:
            return

        # 需要更新的日期范围: 从 last_update+1 到 today (包含今天)
        delta_days = (today - self.last_update).days
        updated = False
        for i in range(1, delta_days + 1):
            current_date = self.last_update + timedelta(days=i)
            weekday = current_date.weekday()  # 0=周一
            # 遍历所有剧集，如果剧集的更新日等于该日星期，集数+1
            for show in self.shows:
                if show.get("day") == weekday:
                    show["episode"] = show.get("episode", 0) + 1
                    updated = True

        if updated:
            self.last_update = today
            self.save_data()
            self.refresh_display()
        else:
            # 即使没有剧集更新，也要更新最后日期，避免重复扫描
            self.last_update = today
            self.save_data()

    def schedule_check(self):
        """每小时检查一次日期变化 (3600000毫秒)"""
        self.check_update_periodic()
        self.after(3600000, self.schedule_check)  # 1小时

    def check_update_periodic(self):
        """定时检查: 如果日期变了，执行自动更新"""
        today = datetime.now().date()
        if self.last_update < today:
            self.apply_auto_update()   # 内部会刷新

    # ---------- 界面构建 ----------
    def create_widgets(self):
        # 顶部：添加剧集区域
        top_frame = ttk.Frame(self, padding="5")
        top_frame.pack(fill=X)

        ttk.Label(top_frame, text="剧名:").grid(row=0, column=0, padx=2, pady=2)
        self.entry_name = ttk.Entry(top_frame, width=15)
        self.entry_name.grid(row=0, column=1, padx=2, pady=2)

        ttk.Label(top_frame, text="链接:").grid(row=0, column=2, padx=2, pady=2)
        self.entry_link = ttk.Entry(top_frame, width=30)
        self.entry_link.grid(row=0, column=3, padx=2, pady=2)

        ttk.Label(top_frame, text="更新日:").grid(row=0, column=4, padx=2, pady=2)
        self.day_combo = ttk.Combobox(top_frame, values=WEEKDAYS, state="readonly", width=6)
        self.day_combo.grid(row=0, column=5, padx=2, pady=2)
        self.day_combo.current(0)

        ttk.Label(top_frame, text="当前集数:").grid(row=0, column=6, padx=2, pady=2)
        self.ep_spin = ttk.Spinbox(top_frame, from_=0, to=9999, width=6)
        self.ep_spin.grid(row=0, column=7, padx=2, pady=2)
        self.ep_spin.delete(0, END)
        self.ep_spin.insert(0, "1")

        btn_add = ttk.Button(top_frame, text="添加剧集", command=self.add_show)
        btn_add.grid(row=0, column=8, padx=10, pady=2)

        # 提示标签
        ttk.Label(top_frame, text="(点击剧名可打开链接)", foreground="gray").grid(row=1, column=0, columnspan=9, sticky=W, pady=2)

        # 中间：可滚动的七天视图
        self.scrollable = ScrollableFrame(self)
        self.scrollable.pack(fill=BOTH, expand=True, padx=5, pady=5)

        # 创建七个列的框架，存放在字典中
        self.day_frames = {}
        header_frame = ttk.Frame(self.scrollable.inner_frame)
        header_frame.pack(fill=X, pady=2)
        for i, day in enumerate(WEEKDAYS):
            lbl = ttk.Label(header_frame, text=day, font=('Arial', 10, 'bold'), borderwidth=1, relief="solid", width=16)
            lbl.grid(row=0, column=i, padx=1, pady=1, sticky="ew")
            header_frame.columnconfigure(i, weight=1)

        # 内容框架 (每列放置剧集卡片)
        self.content_frame = ttk.Frame(self.scrollable.inner_frame)
        self.content_frame.pack(fill=BOTH, expand=True)
        for i in range(7):
            frame = ttk.Frame(self.content_frame, borderwidth=1, relief="groove", width=180)
            frame.grid(row=0, column=i, padx=2, pady=2, sticky="nsew")
            frame.columnconfigure(0, weight=1)
            # 阻止frame随内部内容收缩
            frame.grid_propagate(False)
            frame.update_idletasks()
            self.day_frames[i] = frame
            # 让每一列在网格中均匀扩展
            self.content_frame.columnconfigure(i, weight=1)

        # 填充初始数据
        self.refresh_display()

    # ---------- 剧集卡片管理 ----------
    def refresh_display(self):
        """根据self.shows重新绘制所有卡片"""
        # 清除所有day_frame中的子控件
        for frame in self.day_frames.values():
            for widget in frame.winfo_children():
                widget.destroy()

        # 重新绘制
        for idx, show in enumerate(self.shows):
            day = show.get("day", 0)
            if day not in self.day_frames:
                continue   # 防御
            parent = self.day_frames[day]

            # 卡片框架
            card = ttk.Frame(parent, relief="raised", borderwidth=1, padding=3)
            card.pack(fill=X, pady=2, padx=2)

            # 第一行：剧名和集数
            top_row = ttk.Frame(card)
            top_row.pack(fill=X)
            # 剧名（可点击打开链接）
            name_lbl = ttk.Label(top_row, text=show.get("name", "未知"), foreground="blue", cursor="hand2")
            name_lbl.pack(side=LEFT, padx=2)
            name_lbl.bind("<Button-1>", lambda e, idx=idx: self.open_link(idx))

            ep_label = ttk.Label(top_row, text=f"第{show.get('episode',0)}集")
            ep_label.pack(side=RIGHT, padx=2)

            # 第二行：按钮组
            btn_row = ttk.Frame(card)
            btn_row.pack(fill=X, pady=2)

            # +1
            btn_plus = ttk.Button(btn_row, text="+1", width=3, command=partial(self.increment_ep, idx))
            btn_plus.pack(side=LEFT, padx=1)

            # -1
            btn_minus = ttk.Button(btn_row, text="-1", width=3, command=partial(self.decrement_ep, idx))
            btn_minus.pack(side=LEFT, padx=1)

            # 链接
            btn_link = ttk.Button(btn_row, text="🔗", width=3, command=partial(self.open_link, idx))
            btn_link.pack(side=LEFT, padx=1)

            # 同步 (网盘)
            btn_sync = ttk.Button(btn_row, text="同步", width=4, command=partial(self.sync_show, idx))
            btn_sync.pack(side=LEFT, padx=1)

            # 删除
            btn_del = ttk.Button(btn_row, text="✕", width=3, command=partial(self.delete_show, idx))
            btn_del.pack(side=LEFT, padx=1)

        # 更新滚动区域
        self.scrollable._on_frame_configure(None)

    # ---------- 按钮回调函数 ----------
    def increment_ep(self, idx):
        """增加一集"""
        if 0 <= idx < len(self.shows):
            self.shows[idx]["episode"] = self.shows[idx].get("episode", 0) + 1
            self.save_data()
            self.refresh_display()

    def decrement_ep(self, idx):
        """减少一集 (不低于0)"""
        if 0 <= idx < len(self.shows):
            current = self.shows[idx].get("episode", 0)
            if current > 0:
                self.shows[idx]["episode"] = current - 1
                self.save_data()
                self.refresh_display()

    def open_link(self, idx):
        """打开剧集链接"""
        if 0 <= idx < len(self.shows):
            link = self.shows[idx].get("link", "")
            if link and link.startswith(("http://", "https://")):
                webbrowser.open(link)
            else:
                messagebox.showinfo("提示", "该剧没有有效的链接")

    def sync_show(self, idx):
        """同步网盘集数：弹窗让用户输入网盘实际集数，将记录更新为该数值"""
        if idx >= len(self.shows):
            return
        show = self.shows[idx]
        current_ep = show.get("episode", 0)

        # 自定义对话框
        dialog = Toplevel(self)
        dialog.title("同步网盘集数")
        dialog.geometry("300x150")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        ttk.Label(dialog, text=f"剧名: {show.get('name')}").pack(pady=5)
        ttk.Label(dialog, text=f"当前记录集数: {current_ep}").pack(pady=2)
        ttk.Label(dialog, text="输入网盘实际集数:").pack(pady=2)

        var = IntVar(value=current_ep)
        spin = ttk.Spinbox(dialog, from_=0, to=9999, textvariable=var, width=10)
        spin.pack(pady=5)

        def do_sync():
            try:
                new_ep = var.get()
                if new_ep < 0:
                    messagebox.showerror("错误", "集数不能为负数")
                    return
                self.shows[idx]["episode"] = new_ep
                self.save_data()
                self.refresh_display()
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("错误", f"输入无效: {e}")

        btn_ok = ttk.Button(dialog, text="同步", command=do_sync)
        btn_ok.pack(pady=10)

    def delete_show(self, idx):
        """删除剧集（带确认）"""
        if idx < 0 or idx >= len(self.shows):
            return
        name = self.shows[idx].get("name", "未知")
        if messagebox.askyesno("确认删除", f"确定要删除《{name}》吗？"):
            del self.shows[idx]
            self.save_data()
            self.refresh_display()

    def add_show(self):
        """从输入框添加新剧集"""
        name = self.entry_name.get().strip()
        link = self.entry_link.get().strip()
        day_str = self.day_combo.get()
        ep_str = self.ep_spin.get().strip()

        if not name:
            messagebox.showwarning("警告", "请输入剧名")
            return
        if not link:
            # 链接可以为空，但建议输入
            if not messagebox.askyesno("链接为空", "播放链接为空，确定继续添加吗？"):
                return
        try:
            episode = int(ep_str) if ep_str else 1
        except ValueError:
            episode = 1

        # 获取星期索引
        try:
            day_index = WEEKDAYS.index(day_str)
        except ValueError:
            day_index = 0

        new_show = {
            "name": name,
            "link": link,
            "day": day_index,
            "episode": episode
        }
        self.shows.append(new_show)
        self.save_data()
        self.refresh_display()

        # 清空输入框 (保留星期和默认集数)
        self.entry_name.delete(0, END)
        self.entry_link.delete(0, END)
        self.ep_spin.delete(0, END)
        self.ep_spin.insert(0, "1")
        self.day_combo.current(0)

    def on_closing(self):
        """关闭窗口前保存数据"""
        self.save_data()
        self.destroy()


if __name__ == "__main__":
    app = TvTrackerApp()
    app.mainloop()