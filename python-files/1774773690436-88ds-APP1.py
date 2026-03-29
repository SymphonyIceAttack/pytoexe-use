import tkinter as tk
from tkinter import ttk

# ================= �������ֺ�����ģ������Ҳ������Դ����΢�� =================
TITLE_TEXT   = "Windows �汾"
VER_TEXT     = "Windows 7 �콢��"
SP_TEXT      = "Service Pack 1"
COPY_TEXT    = "��Ȩ���� ? 2009 Microsoft Corporation����������Ȩ����"

root = tk.Tk()
root.title("winver")
root.geometry("500x260")
root.resizable(False, False)

# �������š��̶�������ʽ
root.attributes("-toolwindow", 0)

# �Ű沼��
lb_title = ttk.Label(root, text=TITLE_TEXT, font=("΢���ź�", 12))
lb_title.place(x=120, y=40)

lb_ver = ttk.Label(root, text=VER_TEXT, font=("΢���ź�", 11, "bold"))
lb_ver.place(x=120, y=80)

lb_sp = ttk.Label(root, text=SP_TEXT, font=("΢���ź�", 10))
lb_sp.place(x=120, y=115)

lb_copy = ttk.Label(root, text=COPY_TEXT, font=("΢���ź�", 9))
lb_copy.place(x=120, y=160)

# ���ռλģ��ϵͳͼ�����򣨴����Ƕ����ʵico���ɣ�
root.mainloop()