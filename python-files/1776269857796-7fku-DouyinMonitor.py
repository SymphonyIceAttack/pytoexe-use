import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import time
import datetime
import os
import hashlib
import json
import qrcode
import webbrowser

VERSION = "�������������� ? ����� 99Ԫ/��"
SECRET = "Ultimate_2026_99_MONTHLY"

def get_machine_id():
    info = os.environ.get("COMPUTERNAME","") + os.environ.get("USERNAME","")
    return hashlib.md5((info + SECRET).encode()).hexdigest()[:16].upper()

def check_license():
    if not os.path.exists("license.json"):
        return False, "δ��Ȩ"
    try:
        with open("license.json","r",encoding="utf-8") as f:
            data=json.load(f)
        mid,code,expire=data.get("mid",""),data.get("code",""),data.get("expire","")
        if mid!=get_machine_id():return False,"�����벻ƥ��"
        s=f"{mid}|{expire}|{SECRET}"
        if hashlib.md5(s.encode()).hexdigest()[:16].upper()!=code:
            return False,"��Ȩ����Ч"
        now=datetime.datetime.now().strftime("%Y-%m-%d")
        if now>expire:return False,"��Ȩ�ѵ��ڣ�������99Ԫ/��"
        return True,f"��Ȩ��Ч ? ���ڣ�{expire}"
    except:
        return False,"��Ȩ�ļ��쳣"

class UltimateApp:
    def __init__(self,root):
        self.root=root
        self.root.title(VERSION)
        self.root.geometry("1200x800")
        self.root.configure(bg="#121212")
        ok,msg=check_license()
        if not ok:
            messagebox.showerror("δ��Ȩ",msg)
            root.destroy()
            return
        self.running=False
        self.setup_ui()

    def setup_ui(self):
        left=tk.Frame(self.root,bg="#1e1e1e")
        left.place(x=10,y=10,width=330,height=780)
        tk.Label(left,text="ֱ����ID",bg="#1e1e1e",fg="white").pack()
        self.room=scrolledtext.ScrolledText(left,height=6,bg="#222",fg="white")
        self.room.pack(fill="x",pady=5)

        tk.Button(left,text="��ʼ���",bg="#333",fg="white",width=25,height=2,command=self.start).pack(pady=2)
        tk.Button(left,text="ֹͣ���",bg="#333",fg="white",width=25,height=2,command=self.stop).pack(pady=2)
        tk.Button(left,text="�����ö�",bg="#333",fg="white",width=25,height=2,command=lambda:self.root.attributes("-topmost",1)).pack(pady=2)

        tk.Label(left,text="���װ� TOP30",bg="#1e1e1e",fg="cyan").pack(pady=(5,0))
        self.rank=scrolledtext.ScrolledText(left,height=20,bg="#222",fg="white")
        self.rank.pack(fill="both",expand=True,pady=5)

        tk.Label(self.root,text="ʵʱ����",bg="#121212",fg="white").place(x=350,y=10)
        self.log=scrolledtext.ScrolledText(self.root,bg="#1a1a1a",fg="white",font=("΢���ź�",10))
        self.log.place(x=350,y=35,width=500,height=750)

        uif=tk.Frame(self.root,bg="#1e1e1e")
        uif.place(x=860,y=10,width=320,height=780)
        tk.Label(uif,text="�û���Ϣ",bg="#1e1e1e",fg="cyan").pack(pady=5)
        tk.Label(uif,text="�ǳ�",bg="#1e1e1e",fg="white").pack()
        self.name=tk.Entry(uif,bg="#222",fg="white")
        self.name.pack(fill="x",pady=2)
        tk.Label(uif,text="����UID",bg="#1e1e1e",fg="white").pack()
        self.uid=tk.Entry(uif,bg="#222",fg="white")
        self.uid.pack(fill="x",pady=2)

        tk.Button(uif,text="���ɶ�ά��",bg="#444",fg="white",width=28,height=2,command=self.make_qr).pack(pady=3)
        tk.Button(uif,text="����ҳ",bg="#444",fg="white",width=28,height=2,command=self.open_home).pack(pady=3)
        self.qrl=tk.Label(uif,bg="#1e1e1e")
        self.qrl.pack(pady=10)

    def start(self):
        self.running=True
        threading.Thread(target=self.loop,daemon=True).start()
        self.log.insert("end","[ϵͳ] �����������\n")

    def stop(self):
        self.running=False
        self.log.insert("end","[ϵͳ] ��ֹͣ\n")

    def loop(self):
        while self.running:time.sleep(1)

    def make_qr(self):
        uid=self.uid.get().strip()
        if not uid:return
        qr=qrcode.make(f"https://www.douyin.com/user/{uid}")
        qr.save("tmp.png")
        img=tk.PhotoImage(file="tmp.png").subsample(3,3)
        self.qrl.config(image=img)
        self.qrl.image=img

    def open_home(self):
        uid=self.uid.get().strip()
        if uid:webbrowser.open(f"https://www.douyin.com/user/{uid}")

def auth_win():
    w=tk.Tk()
    w.title("���� ? 99Ԫ/��")
    w.geometry("460x280")
    mid=get_machine_id()
    tk.Label(w,text="������").pack()
    e1=tk.Entry(w,font=("",12))
    e1.insert(0,mid)
    e1.config(state="readonly")
    e1.pack(pady=5)
    tk.Label(w,text="��Ȩ��").pack()
    e2=tk.Entry(w,font=("",12))
    e2.pack(pady=5)
    def save():
        with open("license.json","w",encoding="utf-8") as f:
            json.dump({"mid":mid,"code":e2.get().strip().upper(),"expire":"2026-05-15"},f)
        messagebox.showinfo("�ɹ�","����ɹ�������������")
        w.destroy()
    tk.Button(w,text="����",width=15,height=2,command=save).pack(pady=10)
    w.mainloop()

if __name__=="__main__":
    if not os.path.exists("license.json"):
        auth_win()
    else:
        root=tk.Tk()
        UltimateApp(root)
        root.mainloop()