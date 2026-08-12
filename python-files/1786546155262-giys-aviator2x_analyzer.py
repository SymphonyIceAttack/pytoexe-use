import tkinter as tk
from tkinter import messagebox, filedialog
import json, os, csv
from collections import Counter, defaultdict

DATA_FILE = "aviator2x_data.json"

class App:
    def __init__(self, root):
        self.root=root
        self.root.title("Aviator 2X Analyzer - Test")
        self.root.geometry("760x700")
        self.data=self.load()
        self.current=[]
        self.pred=None
        self.pattern_used=None
        self.build()

    def load(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE,"r",encoding="utf-8") as f: return json.load(f)
            except: pass
        return {"rounds":[],"predictions":[]}

    def save(self):
        with open(DATA_FILE,"w",encoding="utf-8") as f: json.dump(self.data,f,ensure_ascii=False,indent=2)

    def build(self):
        tk.Label(self.root,text="Aviator 2X Analyzer",font=("Arial",24,"bold")).pack(pady=10)
        tk.Label(self.root,text="أدخل نتائج الجولات: فوق 2× أو تحت 2×",font=("Arial",14)).pack()

        self.seq=tk.Label(self.root,text="—",font=("Arial",18))
        self.seq.pack(pady=12)

        f=tk.Frame(self.root); f.pack()
        tk.Button(f,text="فوق 2×",font=("Arial",15),width=12,command=lambda:self.add(1)).grid(row=0,column=0,padx=5)
        tk.Button(f,text="تحت 2×",font=("Arial",15),width=12,command=lambda:self.add(0)).grid(row=0,column=1,padx=5)
        tk.Button(f,text="حذف آخر",font=("Arial",12),command=self.undo).grid(row=0,column=2,padx=5)
        tk.Button(f,text="مسح العشر",font=("Arial",12),command=self.clear).grid(row=0,column=3,padx=5)

        self.pred_label=tk.Label(self.root,text="التوقع: —",font=("Arial",22,"bold"))
        self.pred_label.pack(pady=16)
        self.info=tk.Label(self.root,text="أدخل 10 نتائج ثم اضغط تحليل",font=("Arial",12),justify="center")
        self.info.pack()

        tk.Button(self.root,text="تحليل الجولة القادمة",font=("Arial",15),command=self.analyze).pack(pady=10)

        fb=tk.Frame(self.root); fb.pack()
        tk.Button(fb,text="✓ صحيح",font=("Arial",14),width=12,command=lambda:self.feedback(True)).grid(row=0,column=0,padx=10)
        tk.Button(fb,text="✗ خطأ",font=("Arial",14),width=12,command=lambda:self.feedback(False)).grid(row=0,column=1,padx=10)

        self.stats=tk.Label(self.root,text="",font=("Arial",12),justify="left")
        self.stats.pack(pady=14)

        bt=tk.Frame(self.root); bt.pack()
        tk.Button(bt,text="تصدير CSV",command=self.export).grid(row=0,column=0,padx=5)
        tk.Button(bt,text="عرض السجل",command=self.history).grid(row=0,column=1,padx=5)
        tk.Button(bt,text="مسح كل البيانات",command=self.reset_all).grid(row=0,column=2,padx=5)

        tk.Label(self.root,text="ملاحظة: هذا محلل إحصائي تجريبي، ولا يضمن نتيجة الجولة القادمة.",font=("Arial",10)).pack(pady=10)
        self.refresh()

    def add(self,x):
        if len(self.current)>=10:
            messagebox.showinfo("تنبيه","أكملت 10 نتائج. حلل أولًا.")
            return
        self.current.append(x); self.refresh()

    def undo(self):
        if self.current: self.current.pop(); self.refresh()

    def clear(self):
        self.current=[]; self.pred=None; self.refresh()

    def refresh(self):
        self.seq.config(text="  ".join("فوق 2×" if x else "تحت 2×" for x in self.current) or "—")
        self.stats.config(text=self.stats_text())

    def stats_text(self):
        ps=self.data["predictions"]
        n=len(ps); c=sum(p["correct"] for p in ps)
        acc=(100*c/n) if n else 0
        return f"التوقعات المسجلة: {n}    صحيح: {c}    خطأ: {n-c}    الدقة: {acc:.1f}%"

    def pattern_outcomes(self, pattern):
        # Exact pattern history, with Laplace smoothing.
        hits=[]
        for p in self.data["predictions"]:
            if p.get("pattern")==pattern and "actual" in p:
                hits.append(p["actual"])
        return hits

    def similarity_score(self, pattern):
        # Compare current pattern to historical patterns of equal length.
        # Similarity = matching positions; only past, resolved predictions are used.
        records=[]
        for p in self.data["predictions"]:
            old=p.get("pattern")
            if old and "actual" in p and len(old)==len(pattern):
                matches=sum(a==b for a,b in zip(old,pattern))
                sim=matches/len(pattern)
                if sim>=0.6: records.append((sim,p["actual"]))
        return records

    def analyze(self):
        if len(self.current)!=10:
            messagebox.showinfo("تنبيه","يجب إدخال 10 نتائج بالضبط.")
            return
        pat="".join(map(str,self.current))
        exact=self.pattern_outcomes(pat)
        sim=self.similarity_score(self.current)

        # Base rate from all resolved rounds
        all_actual=[p["actual"] for p in self.data["predictions"] if "actual" in p]
        # Use outcomes following recorded patterns, plus base rate when data is sparse.
        if exact:
            above=(sum(exact)+1)/(len(exact)+2)
            source=f"مطابقة تامة: {len(exact)}"
        elif sim:
            w=sum(s for s,_ in sim)
            above=(sum(s*a for s,a in sim)+0.5*w)/(w*1.0+1.0)
            source=f"أنماط مشابهة: {len(sim)}"
        elif all_actual:
            above=(sum(all_actual)+1)/(len(all_actual)+2)
            source=f"خط أساس: {len(all_actual)} نتيجة"
        else:
            above=0.5
            source="لا توجد بيانات تاريخية"

        self.pred=1 if above>=0.5 else 0
        self.pattern_used=pat
        pct=above*100
        self.pred_label.config(text="التوقع التجريبي: "+("فوق 2×" if self.pred else "تحت 2×"))
        self.info.config(text=f"مؤشر الاحتمال التاريخي: {pct:.1f}%\n{source}\nلا توجد ضمانات للنتيجة القادمة.")

    def feedback(self, correct_button):
        if self.pred is None:
            messagebox.showinfo("تنبيه","حلل الجولة أولًا.")
            return
        # Ask actual result; the Correct/Wrong buttons are feedback, as requested.
        actual = self.pred if correct_button else 1-self.pred
        self.data["predictions"].append({
            "pattern":self.pattern_used,
            "prediction":self.pred,
            "actual":actual,
            "correct":bool(correct_button)
        })
        self.data["rounds"].append(actual)
        self.save()
        self.current=(self.current+[actual])[-10:]
        self.pred=None; self.pattern_used=None
        self.pred_label.config(text="التوقع: —")
        self.info.config(text="تم تسجيل النتيجة. أضف/عدّل آخر 10 ثم حلل من جديد.")
        self.refresh()

    def export(self):
        path=filedialog.asksaveasfilename(defaultextension=".csv",filetypes=[("CSV","*.csv")])
        if not path:return
        with open(path,"w",newline="",encoding="utf-8-sig") as f:
            w=csv.writer(f); w.writerow(["pattern","prediction","actual","correct"])
            for p in self.data["predictions"]:
                w.writerow([p.get("pattern"),p.get("prediction"),p.get("actual"),p.get("correct")])
        messagebox.showinfo("تم","تم تصدير السجل.")

    def history(self):
        win=tk.Toplevel(self.root); win.title("السجل"); win.geometry("700x500")
        t=tk.Text(win); t.pack(fill="both",expand=True)
        for i,p in enumerate(self.data["predictions"],1):
            t.insert("end",f"{i}. النمط={p.get('pattern')} | توقع={'فوق' if p.get('prediction') else 'تحت'} | النتيجة={'فوق' if p.get('actual') else 'تحت'} | {'صحيح' if p.get('correct') else 'خطأ'}\n")

    def reset_all(self):
        if messagebox.askyesno("تأكيد","مسح جميع البيانات؟"):
            self.data={"rounds":[],"predictions":[]}; self.current=[]; self.pred=None; self.save(); self.refresh()

root=tk.Tk()
App(root)
root.mainloop()
