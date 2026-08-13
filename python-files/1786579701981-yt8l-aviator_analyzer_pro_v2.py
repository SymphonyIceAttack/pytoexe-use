import tkinter as tk
from tkinter import messagebox
import json, os, math

DB="aviator_v2_data.json"

def side(x): return 1 if x>=2 else 0

def analyze(a):
    if len(a)<10:
        return ("NONE","تحتاج إلى 10 نتائج على الأقل.",[])
    s=[side(x) for x in a[-30:]]
    parts=[]
    # recency
    ws=[0.94**j for j in range(len(s))]
    p=sum(x*w for x,w in zip(s,ws))/sum(ws)
    parts.append(("الترجيح الزمني",p,1.0))
    # transitions
    c=[[1.,1.],[1.,1.]]
    for x,y in zip(s,s[1:]): c[x][y]+=1
    p=c[s[-1]][1]/sum(c[s[-1]])
    parts.append(("انتقال الحالة",p,1.0))
    # repeated patterns
    for k in (3,4,5):
        if len(s)<=k: continue
        pat=tuple(s[-k:]); vals=[]
        for i in range(k,len(s)):
            if tuple(s[i-k:i])==pat: vals.append(s[i])
        if vals:
            p=(sum(vals)+2)/(len(vals)+4)
            parts.append((f"النمط {k}",p,min(1.5,.5+.18*len(vals))))
    w=sum(x[2] for x in parts)
    score=.5+sum((p-.5)*wt for _,p,wt in parts)/w
    spread=max(x[1] for x in parts)-min(x[1] for x in parts)
    agreement=max(0,1-spread/.45)
    strength=abs(score-.5)*2*agreement
    if agreement<.68 or strength<.18:
        return ("NONE","لا توجد إشارة قوية بما يكفي.",parts)
    if score>=.615 and strength>=.25:
        return ("ABOVE","إشارة فوق 2×.",parts)
    if score<=.385 and strength>=.25:
        return ("BELOW","إشارة تحت 2×.",parts)
    return ("NONE","النماذج غير حاسمة.",parts)

class App:
    def __init__(self,r):
        self.r=r; self.a=[]
        if os.path.exists(DB):
            try:self.a=json.load(open(DB)).get("rounds",[])
            except:pass
        r.title("Aviator Analyzer PRO v2");r.geometry("900x700")
        tk.Label(r,text="Aviator Analyzer PRO v2",font=("Arial",24,"bold")).pack(pady=10)
        tk.Label(r,text="أدخل المضاعف الحقيقي؛ 2× يستخدم لتضييق المجال فقط.",font=("Arial",12)).pack()
        f=tk.Frame(r);f.pack(pady=12)
        self.e=tk.Entry(f,font=("Arial",16),width=15);self.e.pack(side="left",padx=5)
        tk.Button(f,text="إضافة",command=self.add,font=("Arial",13)).pack(side="left")
        tk.Button(f,text="تراجع",command=self.undo).pack(side="left",padx=4)
        tk.Button(f,text="مسح",command=self.clear).pack(side="left")
        self.seq=tk.Label(r,text="",wraplength=820,font=("Arial",11));self.seq.pack(pady=10)
        tk.Button(r,text="تحليل الجولة القادمة",command=self.go,font=("Arial",16)).pack(pady=12)
        self.out=tk.Label(r,text="لا توجد إشارة",font=("Arial",24,"bold"));self.out.pack(pady=8)
        self.info=tk.Label(r,text="",font=("Arial",11));self.info.pack()
        self.list=tk.Listbox(r,font=("Arial",11),height=8,width=85);self.list.pack(pady=15)
        self.refresh()
    def save(self):
        json.dump({"rounds":self.a},open(DB,"w"),ensure_ascii=False)
    def add(self):
        try:
            x=float(self.e.get().replace(",",".")); assert x>0
        except:
            messagebox.showerror("خطأ","أدخل مثل 1.42 أو 2.75");return
        self.a.append(x);self.save();self.e.delete(0,"end");self.refresh()
    def undo(self):
        if self.a:self.a.pop();self.save();self.refresh()
    def clear(self):
        if messagebox.askyesno("تأكيد","مسح كل النتائج؟"):
            self.a=[];self.save();self.refresh()
    def refresh(self):
        self.seq.config(text=" | ".join(f"{x:.2f}×" for x in self.a[-50:]) or "لم تدخل نتائج.")
    def go(self):
        sig,reason,parts=analyze(self.a)
        self.out.config(text={"ABOVE":"🟢 إشارة: فوق 2×","BELOW":"🔴 إشارة: تحت 2×","NONE":"⚪ لا توجد إشارة"}[sig])
        self.info.config(text=reason)
        self.list.delete(0,"end")
        for n,p,w in parts:self.list.insert("end",f"{n}: {p*100:.1f}%   وزن={w:.2f}")

root=tk.Tk();App(root);root.mainloop()
