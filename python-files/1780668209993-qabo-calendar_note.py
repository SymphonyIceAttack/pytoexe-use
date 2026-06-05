import tkinter as tk
from tkinter import simpledialog, messagebox
import calendar
import json
import os
from datetime import datetime

from lunar_python import Solar

DATA_FILE = "memo_data.json"


class CalendarNoteApp:

    def __init__(self, root):
        self.root = root
        self.root.title("桌面日历便签")
        self.root.geometry("980x700")

        # 默认置顶
        self.root.attributes("-topmost", True)

        now = datetime.now()
        self.year = now.year
        self.month = now.month

        self.data = self.load_data()

        self.create_header()
        self.create_calendar()

    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_data(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(
                self.data,
                f,
                ensure_ascii=False,
                indent=4
            )

    def create_header(self):
        frame = tk.Frame(self.root)
        frame.pack(fill="x", pady=10)

        tk.Button(
            frame,
            text="<< 上月",
            command=self.prev_month
        ).pack(side="left", padx=10)

        self.title_label = tk.Label(
            frame,
            text="",
            font=("微软雅黑", 16, "bold")
        )
        self.title_label.pack(side="left", expand=True)

        tk.Button(
            frame,
            text="下月 >>",
            command=self.next_month
        ).pack(side="right", padx=10)

    def create_calendar(self):
        if hasattr(self, "calendar_frame"):
            self.calendar_frame.destroy()

        self.calendar_frame = tk.Frame(self.root)
        self.calendar_frame.pack(
            fill="both",
            expand=True,
            padx=5,
            pady=5
        )

        self.title_label.config(
            text=f"{self.year}年 {self.month}月"
        )

        week_names = [
            "周一", "周二", "周三",
            "周四", "周五", "周六", "周日"
        ]

        for col, name in enumerate(week_names):
            lbl = tk.Label(
                self.calendar_frame,
                text=name,
                bg="#EAEAEA",
                font=("微软雅黑", 10, "bold"),
                relief="solid"
            )
            lbl.grid(
                row=0,
                column=col,
                sticky="nsew"
            )

        cal = calendar.Calendar(firstweekday=0)
        month_days = cal.monthdayscalendar(
            self.year,
            self.month
        )

        for row in range(6):
            self.calendar_frame.grid_rowconfigure(
                row + 1,
                weight=1
            )

        for col in range(7):
            self.calendar_frame.grid_columnconfigure(
                col,
                weight=1
            )

        for row_idx, week in enumerate(month_days):

            for col_idx, day in enumerate(week):

                frame = tk.Frame(
                    self.calendar_frame,
                    relief="solid",
                    bd=1
                )

                frame.grid(
                    row=row_idx + 1,
                    column=col_idx,
                    sticky="nsew"
                )

                if day == 0:
                    continue

                date_str = (
                    f"{self.year:04d}-"
                    f"{self.month:02d}-"
                    f"{day:02d}"
                )

                lunar_text = ""
                festival = ""

                try:
                    solar = Solar.fromYmd(
                        self.year,
                        self.month,
                        day
                    )
                    lunar = solar.getLunar()

                    if lunar.getFestivals():
                        festival = lunar.getFestivals()[0]

                    elif lunar.getOtherFestivals():
                        festival = lunar.getOtherFestivals()[0]

                    elif solar.getFestivals():
                        festival = solar.getFestivals()[0]

                    elif solar.getOtherFestivals():
                        festival = solar.getOtherFestivals()[0]

                    elif lunar.getJieQi():
                        festival = lunar.getJieQi()

                    lunar_text = lunar.getDayInChinese()

                except:
                    lunar_text = ""

                color = "black"
                if festival:
                    color = "red"

                top_text = str(day)

                lbl_day = tk.Label(
                    frame,
                    text=top_text,
                    anchor="nw",
                    font=("微软雅黑", 11, "bold")
                )
                lbl_day.pack(
                    anchor="nw",
                    padx=3,
                    pady=2
                )

                lbl_lunar = tk.Label(
                    frame,
                    text=lunar_text,
                    fg=color,
                    font=("微软雅黑", 9)
                )
                lbl_lunar.pack(anchor="nw")

                if festival:
                    lbl_festival = tk.Label(
                        frame,
                        text=festival,
                        fg="red",
                        font=("微软雅黑", 9, "bold")
                    )
                    lbl_festival.pack(anchor="nw")

                memo = self.data.get(date_str, "")

                if memo:
                    memo_show = memo[:15]
                    if len(memo) > 15:
                        memo_show += "..."

                    memo_lbl = tk.Label(
                        frame,
                        text="📝" + memo_show,
                        fg="blue",
                        justify="left",
                        wraplength=120
                    )
                    memo_lbl.pack(anchor="nw")

                frame.bind(
                    "<Button-1>",
                    lambda e,
                    d=date_str: self.edit_memo(d)
                )

                for widget in frame.winfo_children():
                    widget.bind(
                        "<Button-1>",
                        lambda e,
                        d=date_str: self.edit_memo(d)
                    )

    def edit_memo(self, date_str):

        old_text = self.data.get(date_str, "")

        text = simpledialog.askstring(
            "待办事项",
            f"{date_str}\n请输入备忘内容：",
            initialvalue=old_text
        )

        if text is None:
            return

        text = text.strip()

        if text:
            self.data[date_str] = text
        else:
            if date_str in self.data:
                del self.data[date_str]

        self.save_data()
        self.create_calendar()

    def prev_month(self):
        self.month -= 1

        if self.month < 1:
            self.month = 12
            self.year -= 1

        self.create_calendar()

    def next_month(self):
        self.month += 1

        if self.month > 12:
            self.month = 1
            self.year += 1

        self.create_calendar()


if __name__ == "__main__":
    root = tk.Tk()
    app = CalendarNoteApp(root)
    root.mainloop()