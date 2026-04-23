import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import qrcode
from PIL import Image, ImageTk, ImageDraw, ImageFont
import datetime
import random

class LazyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Lazy")
        self.root.geometry("920x700")

        self.today = datetime.datetime.now().strftime("%Y%m%d")
        self.sheets = []
        self.current_page = 0
        self.tk_img = None

        ttk.Label(root, text="格式：物料编码 数量，最后一行=工厂代码", font=("微软雅黑", 12)).pack(pady=8)

        self.text_input = tk.Text(root, width=100, height=10, font=("Consolas", 10))
        self.text_input.pack(pady=5, padx=10)

        f_btn = ttk.Frame(root)
        f_btn.pack(pady=8)
        ttk.Button(f_btn, text="生成二维码", width=14, command=self.generate).grid(row=0, column=0, padx=4)
        ttk.Button(f_btn, text="清空内容", width=14, command=self.clear_all).grid(row=0, column=1, padx=4)
        ttk.Button(f_btn, text="仅本次保存", width=14, command=self.manual_save).grid(row=0, column=2, padx=4)

        self.f_page = ttk.Frame(root)
        self.btn_prev = ttk.Button(self.f_page, text="← 上一页", width=10, command=self.prev_page)
        self.lbl_page = ttk.Label(self.f_page, text="第 0/0 页", font=("微软雅黑", 10))
        self.btn_next = ttk.Button(self.f_page, text="下一页 →", width=10, command=self.next_page)
        self.btn_prev.grid(row=0, column=0, padx=5)
        self.lbl_page.grid(row=0, column=1, padx=5)
        self.btn_next.grid(row=0, column=2, padx=5)
        self.f_page.pack(pady=5)
        self.set_page_buttons(False)

        self.preview = ttk.Label(root)
        self.preview.pack(pady=15, padx=15)

    def make_qr(self, code, qty, fac):
        serial = str(random.randint(100000, 999999))
        content = f"{code}/{qty}/{self.today}/{fac}/{serial}"
        qr = qrcode.QRCode(box_size=7, border=3)
        qr.add_data(content)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").resize((160, 160))

        out = Image.new("RGB", (160, 200), "white")
        out.paste(img, (0, 0))
        d = ImageDraw.Draw(out)
        try:
            font = ImageFont.truetype("simhei.ttf", 14)
        except:
            font = ImageFont.load_default()
        d.text((80, 185), code, font=font, fill="black", anchor="mm")
        return out

    def make_sheet(self, qr_list):
        pad = 25
        w = 160 * 4 + pad * 5
        h = 240
        sheet = Image.new("RGB", (w, h), "white")
        for i, im in enumerate(qr_list):
            x = pad + i * (160 + pad)
            sheet.paste(im, (x, 20))
        return sheet

    def generate(self):
        lines = [l.strip() for l in self.text_input.get("1.0", tk.END).splitlines() if l.strip()]
        if len(lines) < 2:
            messagebox.showwarning("提示", "至少1行物料+工厂代码")
            return

        fac = lines[-1]
        mats = lines[:-1]
        qr_images = []

        for line in mats:
            parts = line.split()
            if len(parts) >= 2:
                code, qty = parts[0], parts[1]
                qr_images.append(self.make_qr(code, qty, fac))

        self.sheets = [self.make_sheet(qr_images[i:i+4]) for i in range(0, len(qr_images), 4)]
        self.current_page = 0
        self.show_page()
        self.set_page_buttons(len(self.sheets) > 1)
        messagebox.showinfo("完成", f"共{len(qr_images)}个，{len(self.sheets)}页\n仅显示，不自动保存")

    def show_page(self):
        if not self.sheets:
            self.preview.config(image="")
            self.lbl_page.config(text="第 0/0 页")
            return
        img = self.sheets[self.current_page]
        self.tk_img = ImageTk.PhotoImage(img)
        self.preview.config(image=self.tk_img)
        self.lbl_page.config(text=f"第 {self.current_page+1}/{len(self.sheets)} 页")

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.show_page()

    def next_page(self):
        if self.current_page < len(self.sheets)-1:
            self.current_page += 1
            self.show_page()

    def set_page_buttons(self, enable):
        s = "normal" if enable else "disabled"
        self.btn_prev.config(state=s)
        self.btn_next.config(state=s)

    def manual_save(self):
        if not self.sheets:
            messagebox.showwarning("提示", "先生成二维码")
            return
        folder = filedialog.askdirectory(title="选择保存位置")
        if folder:
            for i, img in enumerate(self.sheets):
                img.save(f"{folder}/Lazy_page{i+1}.png")
            messagebox.showinfo("已保存", f"已保存{len(self.sheets)}页")

    def clear_all(self):
        self.text_input.delete("1.0", tk.END)
        self.sheets = []
        self.tk_img = None
        self.preview.config(image="")
        self.set_page_buttons(False)
        self.lbl_page.config(text="第 0/0 页")
        messagebox.showinfo("已清空", "所有内容已清除")

if __name__ == "__main__":
    root = tk.Tk()
    LazyApp(root)
    root.mainloop()