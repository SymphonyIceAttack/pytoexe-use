import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import ctypes
import os

# ��ȡWindowsϵͳ�Ѱ�װ����
def get_system_fonts():
    gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
    fonts = []
    def enum_font(lpelf, lpnt, nFontType, lParam):
        name = lpelf.contents.lfFaceName.decode("utf-8", errors="ignore").strip("\x00")
        if name and name not in fonts:
            fonts.append(name)
        return 1
    proc = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_void_p), ctypes.c_uint, ctypes.c_void_p)(enum_font)
    gdi32.EnumFontFamiliesExW(gdi32.GetDC(0), None, proc, 0, 0)
    return sorted(fonts)

system_fonts = get_system_fonts()

class TextToKaraokeTool:
    def __init__(self, root):
        self.root = root
        self.root.title("��Ϸ����硤��Ļ��������ϵͳ����ֱ��ѡ���뼶����")
        self.root.geometry("740x640")

        # 1. ��������
        self.text_input = scrolledtext.ScrolledText(root, width=82, height=6)
        self.text_input.place(x=20, y=15)
        self.text_input.insert(tk.END, "�[��Ҏ�t\nŶ �[��Ҏ�t")
        tk.Label(root, text="?? ֱ��������Ļ��һ��һ����", font=("΢���ź�", 10, "bold")).place(x=20, y=0)

        # 2. ϵͳ����ѡ�񣨺���������
        tk.Label(root, text="?? ѡ��ϵͳ����", font=("΢���ź�",10,"bold")).place(x=20, y=120)
        self.font_name = tk.StringVar(value="Microsoft YaHei")
        self.font_menu = tk.OptionMenu(root, self.font_name, *system_fonts)
        self.font_menu.config(width=22)
        self.font_menu.place(x=20, y=145)

        # 3. ��ʽ����
        self.stroke_w = tk.StringVar(value="8")
        self.stroke_color = tk.StringVar(value="��ɫ #FF0000")
        self.text_color = tk.StringVar(value="��ɫ #FFFFFF")
        self.shadow_offset = tk.StringVar(value="3")
        self.bold_enable = tk.BooleanVar(value=True)
        self.title_stroke_w = tk.StringVar(value="10")
        self.pos_x = tk.StringVar(value="640")
        self.pos_y = tk.StringVar(value="540")

        # 4. �뼶��������
        self.anim_in_sec = tk.StringVar(value="0.4")
        self.anim_run_sec = tk.StringVar(value="0.5")
        self.anim_out_sec = tk.StringVar(value="0.3")
        self.anim_type = tk.StringVar(value="����")

        # ���/��ɫ/��Ӱ
        tk.Label(root, text="?? ��ʽ����", font=("΢���ź�",10,"bold")).place(x=20, y=180)
        tk.Label(root, text="��Ļ��ߣ�").place(x=20, y=210)
        tk.Entry(root, textvariable=self.stroke_w, width=6).place(x=78, y=210)
        tk.Label(root, text="������ߣ�").place(x=135, y=210)
        tk.Entry(root, textvariable=self.title_stroke_w, width=6).place(x=193, y=210)

        tk.Label(root, text="���ɫ��").place(x=250, y=210)
        stroke_menu = tk.OptionMenu(root, self.stroke_color, "��ɫ #FF0000", "��ɫ #000000", "��ɫ #FFFFFF")
        stroke_menu.config(width=10)
        stroke_menu.place(x=300, y=207)

        tk.Label(root, text="����ɫ��").place(x=410, y=210)
        text_menu = tk.OptionMenu(root, self.text_color, "��ɫ #FFFFFF", "��ɫ #FFFF00")
        text_menu.config(width=10)
        text_menu.place(x=460, y=207)

        tk.Label(root, text="��Ӱƫ�ƣ�").place(x=20, y=245)
        tk.Entry(root, textvariable=self.shadow_offset, width=6).place(x=78, y=245)
        tk.Checkbutton(root, text="���ּӴ�", variable=self.bold_enable, font=("΢���ź�",9)).place(x=135, y=245)
        tk.Label(root, text="X(����)��").place(x=240, y=245)
        tk.Entry(root, textvariable=self.pos_x, width=6).place(x=285, y=245)
        tk.Label(root, text="Y(����)��").place(x=340, y=245)
        tk.Entry(root, textvariable=self.pos_y, width=6).place(x=385, y=245)

        # ����
        tk.Label(root, text="? �������볡/����/�������룬С�����ã�", font=("΢���ź�",10,"bold")).place(x=20, y=280)
        tk.Label(root, text="�볡��").place(x=20, y=315)
        tk.Entry(root, textvariable=self.anim_in_sec, width=7).place(x=60, y=315)
        tk.Label(root, text="���У�").place(x=120, y=315)
        tk.Entry(root, textvariable=self.anim_run_sec, width=7).place(x=160, y=315)
        tk.Label(root, text="������").place(x=220, y=315)
        tk.Entry(root, textvariable=self.anim_out_sec, width=7).place(x=260, y=315)
        tk.Label(root, text="���ͣ�").place(x=320, y=315)
        anim_menu = tk.OptionMenu(root, self.anim_type, "����", "�Ŵ�", "�Ҳ໬��", "���һζ�", "�޶���")
        anim_menu.config(width=12)
        anim_menu.place(x=360, y=312)

        # ��ť
        tk.Button(root, text="?? һ������ASS��Ļ", width=48, height=2, command=self.generate_ass).place(x=110, y=355)
        tk.Button(root, text="?? ��������", width=48, height=2, command=self.save_ass).place(x=110, y=420)

        # ��ʾ
        tk.Label(root, text="?? �Ƽ����ֺ���+��Ļ���8���������10����Ӱ3������0.4/0.5/0.3��", font=("΢���ź�",9), fg="#555").place(x=25, y=480)
        self.ass_content = ""

    def generate_ass(self):
        try:
            stroke_w = int(self.stroke_w.get())
            title_w = int(self.title_stroke_w.get())
            shadow = int(self.shadow_offset.get())
            pos_x = int(self.pos_x.get())
            pos_y = int(self.pos_y.get())
            t_in = int(float(self.anim_in_sec.get())