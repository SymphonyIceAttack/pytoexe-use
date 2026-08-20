import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import json, os, sys, time, winsound

APP = "Focus App"
MAX_BREAK = 20
INTERVAL = 10 * 60
ROOT = Path(os.getenv("APPDATA", Path.home())) / "FocusApp"
ROOT.mkdir(parents=True, exist_ok=True)
SETTINGS = ROOT / "settings.json"
HISTORY = ROOT / "history.json"

DARK = {"bg":"#0B2238","panel":"#102D47","card":"#173F60","text":"#F7F3ED",
        "muted":"#A9BAC8","accent":"#9B86D0","gold":"#F4C96A","line":"#31516B",
        "input":"#0E2A43","danger":"#E98C8C"}
LIGHT = {"bg":"#F4F1EB","panel":"#FFFFFF","card":"#EEE9E0","text":"#172536",
         "muted":"#647486","accent":"#8068BA","gold":"#D39D20","line":"#D7D0C6",
         "input":"#F8F6F2","danger":"#C75B5B"}

def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default
    except Exception:
        return default

def save(path, data):
    try: path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception: pass

def resource(name):
    return Path(getattr(sys, "_MEIPASS", Path(__file__).parent)) / name

cfg = load(SETTINGS, {"dark":True,"work":50,"break":10,"breaks":3,"sound":"","notify":True})
history = load(HISTORY, [])

class FocusApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP); self.geometry("1040x700"); self.minsize(900,620)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.running=False; self.paused=False; self.mode="work"
        self.remaining=0; self.phase_total=0; self.block=0
        self.worked=0; self.broken=0; self.blocks=[]; self.started=None
        self.job=None; self.next_notice=INTERVAL
        self.work=tk.IntVar(value=int(cfg.get("work",50)))
        self.brk=tk.IntVar(value=min(MAX_BREAK,int(cfg.get("break",10))))
        self.breaks=tk.IntVar(value=max(0,int(cfg.get("breaks",3))))
        self.dark=tk.BooleanVar(value=bool(cfg.get("dark",True)))
        self.notify=tk.BooleanVar(value=bool(cfg.get("notify",True)))
        self.sound=tk.StringVar(value=cfg.get("sound",""))
        self.set_theme()
        self.build()
        self.recommend()
    def set_theme(self):
        global T
        T=DARK if self.dark.get() else LIGHT
        self.configure(bg=T["bg"])
        s=ttk.Style(self)
        try:s.theme_use("clam")
        except:pass
        s.configure("P.Horizontal.TProgressbar",troughcolor=T["line"],background=T["accent"],
                    lightcolor=T["accent"],darkcolor=T["accent"],bordercolor=T["line"],thickness=12)
    def L(self,p,text="",size=10,bold=False,color=None,bg=None,**kw):
        return tk.Label(p,text=text,bg=bg or T["panel"],fg=color or T["text"],
                        font=("Segoe UI",size,"bold" if bold else "normal"),**kw)
    def B(self,p,text,cmd,kind="normal"):
        bg,fg={"normal":(T["card"],T["text"]),"accent":(T["accent"],"white"),
               "gold":(T["gold"],"#172536"),"ghost":(T["bg"],T["text"])}.get(kind,(T["card"],T["text"]))
        return tk.Button(p,text=text,command=cmd,bg=bg,fg=fg,activebackground=bg,
                         activeforeground=fg,relief="flat",bd=0,padx=14,pady=9,
                         font=("Segoe UI",10,"bold"),cursor="hand2")
    def card(self,p):
        f=tk.Frame(p,bg=T["panel"],highlightbackground=T["line"],highlightthickness=1)
        f.pack(fill="x",pady=(0,15))
        i=tk.Frame(f,bg=T["panel"]); i.pack(fill="both",expand=True,padx=22,pady=18)
        return i
    def build(self):
        for w in self.winfo_children(): w.destroy()
        top=tk.Frame(self,bg=T["bg"]); top.pack(fill="x",padx=28,pady=20)
        lf=tk.Frame(top,bg=T["bg"]); lf.pack(side="left")
        img=resource("Focus.png")
        self.logo=None
        if img.exists():
            try:
                self.logo=tk.PhotoImage(file=str(img))
                if self.logo.width()>100 or self.logo.height()>100:
                    import math
                    self.logo=self.logo.subsample(max(1,math.ceil(max(self.logo.width(),self.logo.height())/90)))
                tk.Label(lf,image=self.logo,bg=T["bg"],bd=0).pack(side="left",padx=(0,12))
            except: pass
        tk.Label(lf,text="FOCUS",bg=T["bg"],fg=T["text"],font=("Georgia",28,"bold")).pack(side="left")
        tk.Label(lf,text=" APP",bg=T["bg"],fg=T["accent"],font=("Georgia",20,"bold")).pack(side="left",pady=(7,0))
        nav=tk.Frame(top,bg=T["bg"]); nav.pack(side="right")
        self.B(nav,"⚙ Paramètres",self.settings).pack(side="left",padx=4)
        self.B(nav,"▣ Historique",self.history_window).pack(side="left",padx=4)

        main=tk.Frame(self,bg=T["bg"]); main.pack(fill="both",expand=True,padx=28)
        left=tk.Frame(main,bg=T["bg"]); left.pack(side="left",fill="both",expand=True,padx=(0,10))
        right=tk.Frame(main,bg=T["bg"],width=315); right.pack(side="right",fill="y",padx=(10,0)); right.pack_propagate(False)

        c=self.card(left)
        self.phase=self.L(c,"PRÊT",11,True,T["accent"]); self.phase.pack(anchor="w")
        self.clock=self.L(c,"00:00",68,True,bg=T["panel"]); self.clock.pack(pady=(2,8))
        self.bar=ttk.Progressbar(c,style="P.Horizontal.TProgressbar",maximum=100); self.bar.pack(fill="x",pady=(0,16))
        self.status=self.L(c,"Configure ta séance puis lance le chronomètre.",10,False,T["muted"]); self.status.pack()
        q=tk.Frame(c,bg=T["panel"]); q.pack(pady=(17,0))
        self.start=self.B(q,"▶  Démarrer",self.start_session,"accent"); self.start.pack(side="left",padx=4)
        self.pause=self.B(q,"Ⅱ  Pause",self.toggle_pause); self.pause.pack(side="left",padx=4)
        self.B(q,"↻  Réinitialiser",self.reset).pack(side="left",padx=4)

        c=self.card(left)
        self.L(c,"RECOMMANDATION",10,True,T["gold"]).pack(anchor="w")
        self.rec=self.L(c,"",11,False,bg=T["panel"],wraplength=650,justify="left"); self.rec.pack(anchor="w",pady=(7,0))

        c=self.card(right)
        self.L(c,"TA SÉANCE",10,True,T["gold"]).pack(anchor="w")
        self.info=self.L(c,"",11,False,bg=T["panel"],justify="left"); self.info.pack(anchor="w",pady=(10,18))
        self.update_info()
    def update_info(self):
        total=self.work.get()+self.brk.get()*self.breaks.get()
        if hasattr(self,"info"):
            self.info.config(text=f"Travail :  {self.work.get()} min\nPauses :   {self.brk.get()} min × {self.breaks.get()}\n"
                                  f"Temps programmé :  {total} min\n\nUn objectif unique par bloc.")
    def recommend(self):
        w=self.work.get(); b=min(MAX_BREAK,self.brk.get()); n=self.breaks.get()
        if w<=25: x="Session courte : choisis un objectif très précis et une pause courte."
        elif w<=50: x="Format équilibré : travaille en profondeur puis éloigne-toi de l'écran pendant la pause."
        elif w<=90: x="Session longue : une pause de 10–15 min aide à préserver l'attention."
        else: x="Très longue session : fractionne le travail en blocs pour éviter la fatigue."
        if n>=4:x+=" Beaucoup de pauses : évite les changements de tâche inutiles."
        if b>=15:x+=" Profite de la pause pour bouger et décrocher de l'écran."
        self.rec.config(text=x)
    def settings(self):
        w=tk.Toplevel(self); w.title("Paramètres — Focus App"); w.geometry("560x600"); w.configure(bg=T["bg"]); w.transient(self); w.grab_set()
        o=tk.Frame(w,bg=T["bg"]); o.pack(fill="both",expand=True,padx=28,pady=24)
        self.L(o,"PARAMÈTRES",22,True,bg=T["bg"]).pack(anchor="w")
        self.L(o,"Personnalise ton expérience Focus.",10,False,T["muted"],bg=T["bg"]).pack(anchor="w",pady=(2,18))
        f=tk.Frame(o,bg=T["panel"],highlightbackground=T["line"],highlightthickness=1); f.pack(fill="x")
        def row(name,var,a,z):
            r=tk.Frame(f,bg=T["panel"]); r.pack(fill="x",padx=18,pady=10)
            self.L(r,name,10,True,bg=T["panel"]).pack(side="left")
            tk.Spinbox(r,from_=a,to=z,textvariable=var,width=6,bg=T["input"],fg=T["text"],
                       insertbackground=T["text"],relief="flat").pack(side="right")
        row("Travail (minutes)",self.work,5,240); row("Pause (minutes)",self.brk,1,MAX_BREAK); row("Nombre de pauses",self.breaks,0,20)
        r=tk.Frame(f,bg=T["panel"]); r.pack(fill="x",padx=18,pady=10)
        self.L(r,"Notifications toutes les 10 min",10,True,bg=T["panel"]).pack(side="left")
        tk.Checkbutton(r,variable=self.notify,bg=T["panel"],activebackground=T["panel"],selectcolor=T["input"]).pack(side="right")
        r=tk.Frame(f,bg=T["panel"]); r.pack(fill="x",padx=18,pady=10)
        self.L(r,"Mode sombre",10,True,bg=T["panel"]).pack(side="left")
        tk.Checkbutton(r,variable=self.dark,command=lambda:self.toggle_theme(w),bg=T["panel"],
                       activebackground=T["panel"],selectcolor=T["input"]).pack(side="right")
        r=tk.Frame(f,bg=T["panel"]); r.pack(fill="x",padx=18,pady=(10,18))
        self.L(r,"Son d'alarme (.wav)",10,True,bg=T["panel"]).pack(anchor="w")
        rr=tk.Frame(r,bg=T["panel"]); rr.pack(fill="x",pady=(6,0))
        tk.Entry(rr,textvariable=self.sound,bg=T["input"],fg=T["text"],insertbackground=T["text"],relief="flat").pack(side="left",fill="x",expand=True,ipady=8)
        self.B(rr,"Choisir",self.choose_sound).pack(side="left",padx=(7,0))
        bb=tk.Frame(o,bg=T["bg"]); bb.pack(fill="x",pady=18)
        self.B(bb,"Enregistrer",lambda:self.save_settings(w),"accent").pack(side="right")
        self.B(bb,"Annuler",w.destroy,"ghost").pack(side="right",padx=7)
    def toggle_theme(self,w):
        cfg["dark"]=bool(self.dark.get()); save(SETTINGS,cfg); self.set_theme(); w.destroy(); self.build(); self.recommend()
        self.settings()
    def choose_sound(self):
        p=filedialog.askopenfilename(title="Choisir un son WAV",filetypes=[("Fichiers WAV","*.wav")])
        if p:self.sound.set(p)
    def save_settings(self,w=None):
        self.brk.set(max(1,min(MAX_BREAK,self.brk.get()))); self.work.set(max(5,min(240,self.work.get()))); self.breaks.set(max(0,self.breaks.get()))
        cfg.update({"dark":bool(self.dark.get()),"work":self.work.get(),"break":self.brk.get(),"breaks":self.breaks.get(),
                    "sound":self.sound.get(),"notify":bool(self.notify.get())}); save(SETTINGS,cfg)
        if w:w.destroy()
        self.set_theme(); self.build(); self.recommend()
    def start_session(self):
        if self.running:return
        self.running=True; self.paused=False; self.mode="work"; self.block=0
        self.worked=self.broken=0; self.blocks=[]; self.started=time.time(); self.next_notice=INTERVAL
        self.remaining=self.work.get()*60; self.phase_total=self.remaining
        self.start.config(state="disabled"); self.status.config(text="Concentre-toi sur une seule tâche.")
        self.last=time.time(); self.tick()
    def toggle_pause(self):
        if not self.running:return
        self.paused=not self.paused
        if self.paused:self.pause.config(text="▶  Reprendre"); self.status.config(text="Chronomètre en pause.")
        else:self.pause.config(text="Ⅱ  Pause"); self.status.config(text="C'est reparti. Ne te déconcentre pas !"); self.last=time.time(); self.tick()
    def reset(self):
        if self.job:
            try:self.after_cancel(self.job)
            except:pass
        self.running=False; self.paused=False; self.remaining=0; self.phase_total=0; self.block=0; self.blocks=[]
        self.start.config(state="normal"); self.pause.config(text="Ⅱ  Pause"); self.phase.config(text="PRÊT")
        self.clock.config(text="00:00"); self.bar["value"]=0; self.status.config(text="Configure ta séance puis lance le chronomètre.")
    def tick(self):
        if not self.running or self.paused:return
        now=time.time(); delta=max(0,int(now-self.last)); self.last=now
        if delta:
            self.remaining-=delta
            if self.mode=="work":self.worked+=delta
            else:self.broken+=delta
        self.clock.config(text=f"{max(0,self.remaining)//60:02d}:{max(0,self.remaining)%60:02d}")
        self.bar["value"]=max(0,min(100,(1-self.remaining/max(1,self.phase_total))*100))
        self.phase.config(text=("TRAVAIL" if self.mode=="work" else "PAUSE")+f"  •  BLOC {self.block+1}")
        elapsed=int(time.time()-self.started)
        if self.notify.get() and elapsed>=self.next_notice:
            self.notice(); self.next_notice=((elapsed//INTERVAL)+1)*INTERVAL
        if self.remaining<=0:self.finish_phase()
        else:self.job=self.after(250,self.tick)
    def alarm(self):
        try:
            p=self.sound.get()
            if p and Path(p).exists():winsound.PlaySound(p,winsound.SND_FILENAME|winsound.SND_ASYNC)
            else:winsound.MessageBeep()
        except:pass
    def notice(self):
        mins=max(0,self.remaining)//60
        self.popup("Petit rappel Focus",f"Il reste environ {mins} min.\n\nRespire, garde une seule tâche en tête et ne te déconcentre pas.")
    def popup(self,title,msg):
        w=tk.Toplevel(self); w.title(title); w.geometry("370x190"); w.configure(bg=T["panel"]); w.transient(self)
        f=tk.Frame(w,bg=T["panel"],highlightbackground=T["line"],highlightthickness=1); f.pack(fill="both",expand=True,padx=10,pady=10)
        self.L(f,title,15,True,T["accent"],bg=T["panel"]).pack(pady=(18,8))
        self.L(f,msg,10,False,bg=T["panel"],justify="center",wraplength=310).pack(padx=15)
        self.B(f,"OK",w.destroy,"accent").pack(pady=13)
        w.after(8000,lambda:w.destroy() if w.winfo_exists() else None)
    def finish_phase(self):
        self.alarm()
        self.blocks.append((self.mode,self.phase_total/60))
        if self.mode=="work" and self.block<self.breaks.get():
            self.mode="break"; self.remaining=self.brk.get()*60; self.phase_total=self.remaining; self.block+=1
            self.status.config(text="Bloc terminé. Respire et éloigne-toi de l'écran."); self.popup("Pause","Ton bloc est terminé. Prends une vraie pause.")
        elif self.mode=="break":
            self.mode="work"; self.remaining=self.work.get()*60; self.phase_total=self.remaining
            self.status.config(text="Pause terminée. Retour au focus !"); self.popup("Retour au focus","La pause est terminée. On repart !")
        else:self.finish_session(); return
        self.last=time.time(); self.tick()
    def finish_session(self):
        self.running=False; self.paused=False; self.bar["value"]=100; self.start.config(state="normal"); self.phase.config(text="SESSION TERMINÉE")
        self.status.config(text="Bravo. Prends quelques minutes pour décrocher.")
        item={"date":time.strftime("%Y-%m-%d %H:%M"),"work":round(self.worked/60,1),"break":round(self.broken/60,1),
              "total":round((self.worked+self.broken)/60,1),"blocks":len([x for x in self.blocks if x[0]=="work"])}
        history.append(item); del history[:-50]; save(HISTORY,history); self.summary()
    def summary(self):
        w=tk.Toplevel(self); w.title("Récapitulatif — Focus App"); w.geometry("760x630"); w.configure(bg=T["bg"])
        o=tk.Frame(w,bg=T["bg"]); o.pack(fill="both",expand=True,padx=24,pady=20)
        self.L(o,"SESSION TERMINÉE",22,True,bg=T["bg"]).pack(anchor="w")
        self.L(o,"Résumé de ton temps de concentration.",10,False,T["muted"],bg=T["bg"]).pack(anchor="w",pady=(2,16))
        stats=tk.Frame(o,bg=T["bg"]); stats.pack(fill="x")
        vals=[("Travail",f"{self.worked/60:.0f} min"),("Pauses",f"{self.broken/60:.0f} min"),
              ("Blocs",str(len([x for x in self.blocks if x[0]=="work"]))),("Total",f"{(self.worked+self.broken)/60:.0f} min")]
        for a,b in vals:
            c=tk.Frame(stats,bg=T["panel"],highlightbackground=T["line"],highlightthickness=1); c.pack(side="left",fill="x",expand=True,padx=3)
            self.L(c,a,9,True,T["muted"],bg=T["panel"]).pack(pady=(10,2)); self.L(c,b,17,True,bg=T["panel"]).pack(pady=(0,10))
        self.L(o,"CHRONOLOGIE DE LA SÉANCE",11,True,T["gold"],bg=T["bg"]).pack(anchor="w",pady=(20,7))
        cv=tk.Canvas(o,height=230,bg=T["panel"],highlightbackground=T["line"],highlightthickness=1); cv.pack(fill="x")
        self.draw_chart(cv)
        self.B(o,"Fermer",w.destroy,"accent").pack(pady=15)
    def draw_chart(self,cv):
        cv.delete("all"); cv.update_idletasks(); width=max(650,cv.winfo_width()); data=self.blocks
        if not data:
            cv.create_text(width//2,110,text="Aucune donnée.",fill=T["muted"]); return
        mx=max(1,max(v for _,v in data)); gap=width/(len(data)+1)
        for i,(kind,v) in enumerate(data):
            x=gap*(i+1); h=v/mx*155; top=185-h; col=T["accent"] if kind=="work" else T["gold"]
            cv.create_line(x,top-8,x,193,fill=col,width=2)
            cv.create_rectangle(x-11,top,x+11,193,fill=col,outline=col)
            cv.create_text(x,208,text=str(i+1),fill=T["muted"],font=("Segoe UI",8))
        cv.create_text(12,15,anchor="nw",text="Violet = travail   •   Doré = pause",fill=T["muted"],font=("Segoe UI",8))
    def history_window(self):
        w=tk.Toplevel(self); w.title("Historique — Focus App"); w.geometry("700x500"); w.configure(bg=T["bg"])
        o=tk.Frame(w,bg=T["bg"]); o.pack(fill="both",expand=True,padx=24,pady=20)
        self.L(o,"HISTORIQUE",22,True,bg=T["bg"]).pack(anchor="w")
        self.L(o,"Les 50 dernières séances sont conservées localement.",10,False,T["muted"],bg=T["bg"]).pack(anchor="w",pady=(2,15))
        cols=("date","work","break","blocks","total"); tr=ttk.Treeview(o,columns=cols,show="headings")
        for c,h in zip(cols,["Date","Travail","Pauses","Blocs","Total"]):tr.heading(c,text=h);tr.column(c,width=125,anchor="center")
        tr.pack(fill="both",expand=True)
        for x in reversed(history):tr.insert("", "end", values=(x.get("date",""),f'{x.get("work",0):.0f} min',f'{x.get("break",0):.0f} min',x.get("blocks",0),f'{x.get("total",0):.0f} min'))
        self.B(o,"Fermer",w.destroy,"accent").pack(pady=14)
    def close(self):
        if self.running and not messagebox.askyesno("Quitter Focus App","Une séance est en cours. Quitter ?"):return
        cfg.update({"dark":bool(self.dark.get()),"work":self.work.get(),"break":self.brk.get(),"breaks":self.breaks.get(),"sound":self.sound.get(),"notify":bool(self.notify.get())})
        save(SETTINGS,cfg); self.destroy()

if __name__=="__main__":
    FocusApp().mainloop()
