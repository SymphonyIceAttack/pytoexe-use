import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
import easyocr
from translatepy import Translator

# 语言列表
LANG_LIST = {
    "中文": "zh",
    "英文": "en",
    "日语": "ja",
    "韩语": "ko",
    "法语": "fr",
    "德语": "de",
    "俄语": "ru",
    "西班牙语": "es"
}

class TransApp:
    def __init__(self, win):
        self.win = win
        self.win.title("本地图片翻译工具")
        self.win.geometry("950x720")
        self.img_path = ""
        self.reader = None
        self.trans = Translator()
        self.ui()

    def ui(self):
        top = ttk.Frame(self.win, padding=8)
        top.pack(fill=tk.X)

        ttk.Button(top, text="选择图片", command=self.load_img).grid(row=0,column=0,padx=4)
        ttk.Label(top,text="识别语言:").grid(row=0,column=1,padx=4)
        self.cb1 = ttk.Combobox(top,values=list(LANG_LIST.keys()),width=10)
        self.cb1.current(1)
        self.cb1.grid(row=0,column=2)

        ttk.Label(top,text="翻译为:").grid(row=0,column=3,padx=4)
        self.cb2 = ttk.Combobox(top,values=list(LANG_LIST.keys()),width=10)
        self.cb2.current(0)
        self.cb2.grid(row=0,column=4)

        ttk.Button(top,text="开始识别翻译",command=self.run_task).grid(row=0,column=5,padx=10)
        ttk.Button(top,text="清空",command=self.clear_all).grid(row=0,column=6)

        # 图片预览
        img_frame = ttk.LabelFrame(self.win,text="图片预览",padding=10)
        img_frame.pack(fill=tk.BOTH,expand=True,padx=10,pady=5)
        self.img_show = ttk.Label(img_frame,text="请选择图片")
        self.img_show.pack()

        # 结果框
        res_frame = ttk.LabelFrame(self.win,text="识别+翻译结果",padding=10)
        res_frame.pack(fill=tk.BOTH,expand=True,padx=10,pady=5)
        self.text_out = scrolledtext.ScrolledText(res_frame,font=("微软雅黑",10))
        self.text_out.pack(fill=tk.BOTH,expand=True)

    def load_img(self):
        path = filedialog.askopenfilename(filetypes=[("图片","*.jpg;*.png;*.jpeg;*.bmp")])
        if not path:return
        self.img_path = path
        img = Image.open(path)
        img.thumbnail((450,350))
        self.tk_img = ImageTk.PhotoImage(img)
        self.img_show.config(image=self.tk_img,text="")

    def run_task(self):
        if not self.img_path:
            messagebox.showwarning("提示","请先选择图片")
            return
        self.text_out.delete(1.0,tk.END)
        self.text_out.insert(tk.END,"正在加载模型+识别文字...\n")
        self.win.update()

        s_lang = LANG_LIST[self.cb1.get()]
        t_lang = LANG_LIST[self.cb2.get()]

        if not self.reader:
            self.reader = easyocr.Reader([s_lang],gpu=False)

        ocr_res = self.reader.readtext(self.img_path,detail=0)
        raw_text = "\n".join(ocr_res)

        try:
            trans_res = self.trans.translate(raw_text,destination=t_lang).result
        except:
            trans_res = "翻译失败，请检查网络"

        self.text_out.delete(1.0,tk.END)
        self.text_out.insert(tk.END,f"【原图文字】\n{raw_text}\n\n【翻译结果】\n{trans_res}")

    def clear_all(self):
        self.img_path = ""
        self.img_show.config(image="",text="请选择图片")
        self.text_out.delete(1.0,tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = TransApp(root)
    root.mainloop()