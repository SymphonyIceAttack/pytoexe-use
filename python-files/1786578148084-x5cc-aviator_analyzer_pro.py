import tkinter as tk
from tkinter import ttk,messagebox
import json,os

DB="aviator_pro_data.json"

def runs(s):
    out=[]; cur=s[0]; n=1
    for x in s[1:]:
        if x==cur:n+=1
        else:out.append((cur,n));cur=x;n=1
    out.append((cur,n));return out

def pattern(s,k):
    if len(s)<=k:return None
    t=tuple(s[-k:]); a=[]
    for i in range(k,len(s)):
        if tuple(s[i-k:i])==t:a.append(s[i])
    return ((sum(a)+1)/(len(a)+2),len(a)) if a else None

def similarity(s,k=8):
    if len(s)<k+1:return None
    t=s[-k:]; a=[]
    for i in range(k,len(s)-1):
        q=s[i-k:i]; sim=sum(x==y for x,y in zip(q,t))/k
        if sim>=.75:a.append((sim,s[i]))
    if not a:return None
    w=sum(x for x,y in a)
    return ((sum(x*y for x,y in a)+.5)/(w+1),len(a))

def analyze(s):
    if len(s)<10:return None
    parts=[]
    # Transition model
    c=[[1.,1.],[1.,1.]]
    for a,b in zip(s[-30:],s[-30:][1:]):c[a][b]+=1
    last=s[-1]; p=c[last][1]/sum(c[last]);parts.append(("انتقال الحالة",p,1.0))
    for k in (3,4,5):
        x=pattern(s,k)
        if x:parts.append((f"نمط {k}",x[0],min(2.,.7+.25*x[1])))
    x=similarity(s)
    if x:parts.append(("تشابه تسلسلي",x[0],min(2.,.8+.15*x[1])))
    rr=runs(s[-20:]); lv,ln=rr[-1]
    if ln>=3:parts.append(("سلوك السلسلة",.42 if lv else .58,.6))
    if not parts:return None
    w=sum(x[2] for x in parts)
    score=.5+sum((x[1]-.5)*x[2] for x in parts)/w
    return score,parts

class App:
    def __init__(self,r):
        self.r=r;self.s=[];self.pred=None
        if os.path.exists(DB):
            try:self.s=json.load(open(DB,encoding="utf8")).get("rounds",[])
            except:pass
        r.title("Aviator Analyzer PRO");r.geometry("900x650")
        tk.Label(r,text="Aviator Analyzer PRO",font=("Arial",24,"bold")).pack(pady=10)
        tk.Label(r,text="فوق/تحت 2× = تضييق للمجال، وليس الخوارزمية نفسها.",font=("Arial",12)).pack()
        self.seq=tk.Label(r,text="",font=("Arial",14),wraplength=850);self.seq.pack(pady=15)
        f=tk.Frame(r);f.pack()
        for text,v in [("تحت 2×",0),("فوق 2×",1)]:
            tk.Button(f,text=text,font=("Arial",14),width=14,command=lambda v=v:self.add(v)).pack(side="left",padx=5)
        tk.Button(f,text="تراجع",command=self.undo).pack(side="left",padx=5)
        tk.Button(f,text="مسح",command=self.clear).pack(side="left",padx=5)
        tk.Button(r,text="تحليل",font=("Arial",16),command=self.go).pack(pady=15)
        self.out=tk.Label(r,text="لا توجد إشارة",font=("Arial",22,"bold"));self.out.pack()
        self.detail=tk.Label(r,text="",justify="left",font=("Arial",11));self.detail.pack(pady=8)
        self.tree=ttk.Treeview(r,columns=("a","b","c"),show="headings",height=8)
        for c,t in zip(("a","b","c"),("مكوّن التحليل","الميل","الوزن")):self.tree.heading(c,text=t)
        self.tree.pack(fill="x",padx=30,pady=10)
        self.status=tk.Label(r,text="");self.status.pack()
        self.refresh()
    def save(self):json.dump({"rounds":self.s},open(DB,"w",encoding="utf8"),ensure_ascii=False)
    def add(self,v):self.s.append(v);self.save();self.refresh()
    def undo(self):
        if self.s:self.s.pop();self.save();self.refresh()
    def clear(self):
        if messagebox.askyesno("تأكيد","مسح الجولات؟"):self.s=[];self.save();self.refresh()
    def refresh(self):
        self.seq.config(text="  ".join("فوق 2×" if x else "تحت 2×" for x in self.s[-60:]) or "أدخل النتائج")
        self.status.config(text=f"الجولات المحفوظة: {len(self.s)} | كل جولة جديدة تدخل في التحليل التالي.")
    def go(self):
        z=analyze(self.s)
        if not z:messagebox.showinfo("التحليل","تحتاج إلى 10 جولات على الأقل.");return
        score,parts=z;side="فوق 2×" if score>=.5 else "تحت 2×"
        self.out.config(text=f"الإشارة: {side}")
        self.detail.config(text=f"ميل المحرك: {score*100:.1f}%\nهذا ليس احتمال نجاح ولا نسبة دقة؛ هو ناتج تجميع مؤشرات التحليل.")
        for x in self.tree.get_children():self.tree.delete(x)
        for n,p,w in parts:self.tree.insert("", "end",values=(n,f"{p*100:.1f}%",f"{w:.2f}"))

root=tk.Tk();App(root);root.mainloop()
