# signal_assistant_demo.py
import time, threading, json, random
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, scrolledtext

CANDLE_INTERVAL = 30
COOLDOWN_SECONDS = 120
MAX_CONCURRENT_SIGNALS = 2
SMA_PERIOD = 3
HISTORY_FILE = "signal_history.json"

def now_str(): return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class Candle:
    def __init__(self, open_p, high, low, close):
        self.open = open_p
        self.high = high
        self.low = low
        self.close = close
    def direction(self): return "bull" if self.close > self.open else ("bear" if self.close < self.open else "neutral")

class DemoBuilder:
    def __init__(self):
        self.pairs = ["EUR/USD OTC","GBP/USD OTC","USD/JPY OTC","AUD/USD OTC","GOLD OTC"]
        self.samples = {p:[1.0+random.random()*0.01] for p in self.pairs}
        self.candles = {p:[] for p in self.pairs}
        self.lock = threading.Lock()
    def start_sampling(self):
        threading.Thread(target=self._run_sampler, daemon=True).start()
    def _run_sampler(self):
        while True:
            with self.lock:
                for p in self.pairs:
                    last = self.samples[p][-1]
                    change = (random.random()-0.5)*0.001
                    new = round(last+change,5)
                    self.samples[p].append(new)
                    if len(self.samples[p])>CANDLE_INTERVAL: self.samples[p].pop(0)
            time.sleep(1)
    def build_candle(self,pair):
        with self.lock:
            lst = self.samples[pair]
            open_p = lst[0]; close = lst[-1]; high=max(lst); low=min(lst)
            c = Candle(open_p, high, low, close)
            arr = self.candles[pair]; arr.append(c)
            if len(arr)>50: arr.pop(0)
            return c
    def get_sma(self,pair,n=SMA_PERIOD):
        arr=self.candles[pair][-n:]
        if len(arr)<n: return None
        return sum(c.close for c in arr)/n

def analyze(c1,c2,cbuilder,pair):
    score=0; parts=[]
    dir1=c1.direction(); dir2=c2.direction()
    if dir1==dir2 and dir1 in ("bull","bear"): score+=30; parts.append("2cand same dir")
    b=abs(c1.close-c1.open)/((c1.high-c1.low) if c1.high!=c1.low else 1e-9)*100
    score+=25 if b>=60 else 0; parts.append(f"body{int(b)}%")
    rev=abs((c1.open-c1.low) if dir1=="bull" else (c1.high-c1.open))/((c1.high-c1.low) if c1.high!=c1.low else 1e-9)*100
    score+=15 if rev<=25 else 0; parts.append(f"revW{int(rev)}%")
    sma=cbuilder.get_sma(pair)
    if sma: score+=10 if (dir1=="bull" and c1.close>sma) or (dir1=="bear" and c1.close<sma) else 0
    decision="SKIP"
    if score>=45 and dir1=="bull": decision="CALL"
    elif score>=45 and dir1=="bear": decision="PUT"
    return decision,score,"; ".join(parts)

class Signal:
    def __init__(self,pair,entry_time,direction,confidence,reason):
        self.pair=pair; self.entry_time=entry_time; self.direction=direction
        self.confidence=confidence; self.reason=reason
        self.id=f"{pair}_{int(entry_time)}"; self.state="PENDING"; self.result=None
        self.widget=None; self.buttons=None

class App:
    def __init__(self,root):
        self.root=root; self.root.title("Demo Signal OTC 30s")
        self.cbuilder=DemoBuilder(); self.cbuilder.start_sampling()
        self.history=self._load_history()
        self.signals={}; self.signals_lock=threading.Lock(); self.cooldown_until=0; self.running=False
        topf=tk.Frame(root); topf.pack(fill="x",padx=6,pady=4)
        tk.Button(topf,text="Start",command=self.start).pack(side="left",padx=4)
        tk.Button(topf,text="Stop",command=self.stop).pack(side="left")
        tk.Button(topf,text="Show History",command=self.show_history).pack(side="right")
        self.log=scrolledtext.ScrolledText(root,height=12); self.log.pack(fill="both",padx=6,pady=4)
        self.sig_frame=tk.Frame(root); self.sig_frame.pack(fill="both",expand=True,padx=6,pady=4)
        tk.Label(self.sig_frame,text="Active Signals:").pack(anchor="w")
        self.sig_list=tk.Frame(self.sig_frame); self.sig_list.pack(fill="both",expand=True)
        self.ui_updater()

    def log_msg(self,s): self.log.insert("end",f"[{now_str()}] {s}\n"); self.log.see("end")
    def start(self):
        if self.running: return
        self.running=True; threading.Thread(target=self._loop,daemon=True).start(); self.log_msg("Started demo scanner.")
    def stop(self): self.running=False; self.log_msg("Stopped demo scanner.")
    def _loop(self):
        while self.running:
            if time.time()<self.cooldown_until: time.sleep(1); continue
            pairs=self.cbuilder.pairs; candidates=[]
            for p in pairs:
                c1=self.cbuilder.build_candle(p); c2=self.cbuilder.build_candle(p)
                decision,score,reason=analyze(c1,c2,self.cbuilder,p)
                if decision!="SKIP":
                    entry_time=time.time()+CANDLE_INTERVAL
                    candidates.append((score,p,entry_time,decision,reason))
            if candidates:
                candidates.sort(reverse=True,key=lambda x:x[0])
                chosen=candidates[:MAX_CONCURRENT_SIGNALS]
                for score,p,entry_time,decision,reason in chosen:
                    with self.signals_lock:
                        exists=[s for s in self.signals.values() if s.pair==p and abs(s.entry_time-entry_time)<2]
                        if exists: continue
                        sig=Signal(p,entry_time,decision,int(score),reason)
                        self.signals[sig.id]=sig; self._add_signal_widget(sig)
                        self._alert_prepare(sig)
                        threading.Thread(target=self._schedule_entry,args=(sig,),daemon=True).start()
                        self.cooldown_until=time.time()+COOLDOWN_SECONDS
            time.sleep(1)

    def _add_signal_widget(self,sig):
        f=tk.Frame(self.sig_list,bd=1,relief="solid",padx=4,pady=4); f.pack(fill="x",pady=3)
        lbl=tk.Label(f,text=f"{sig.pair} | {sig.direction} | Conf {sig.confidence}",font=("Segoe UI",10,"bold")); lbl.pack(side="left")
        info=tk.Label(f,text=f"Entry: {datetime.fromtimestamp(sig.entry_time).strftime('%H:%M:%S')}  Reason: {sig.reason}"); info.pack(side="left",padx=8)
        btn_win=tk.Button(f,text="Win",command=lambda s=sig:self.resolve(s,"WIN"))
        btn_loss=tk.Button(f,text="Loss",command=lambda s=sig:self.resolve(s,"LOSS"))
        btn_win2=tk.Button(f,text="Win2",command=lambda s=sig:self.resolve(s,"WIN2"))
        btn_win.pack(side="right",padx=3); btn_loss.pack(side="right",padx=3); btn_win2.pack(side="right",padx=3)
        sig.widget=f; sig.buttons=(btn_win,btn_loss,btn_win2)

    def _alert_prepare(self,sig): self.log_msg(f"Prepare: {sig.pair} -> {sig.direction} at {datetime.fromtimestamp(sig.entry_time).strftime('%H:%M:%S')}")

    def _schedule_entry(self,sig):
        wait=sig.entry_time-time.time(); time.sleep(max(0,wait))
        self.log_msg(f"ENTER NOW: {sig.pair} -> {sig.direction}"); time.sleep(CANDLE_INTERVAL+1)
        self.log_msg(f"Trade expired for {sig.pair}. Please mark Win / Loss / Win2.")

    def resolve(self,sig,result):
        with self.signals_lock:
            if sig.state=="RESOLVED": return
            sig.state="RESOLVED"; sig.result=result
            rec={"timestamp":now_str(),"pair":sig.pair,"direction":sig.direction,"entry":datetime.fromtimestamp(sig.entry_time).strftime("%Y-%m-%d %H:%M:%S"),"confidence":sig.confidence,"reason":sig.reason,"result":result}
            self.history.append(rec); self._save_history(); self.log_msg(f"Resolved {sig.pair} as {result}")
            try:
                for b in sig.buttons: b.config(state="disabled")
                lbl=tk.Label(sig.widget,text=f" -> {result}",fg="green" if result.startswith("WIN") else "red",font=("Segoe UI",10,"bold")); lbl.pack(side="right")
            except: pass
            self.cooldown_until=time.time()+COOLDOWN_SECONDS

    def _load_history(self):
        try: return json.load(open(HISTORY_FILE,"r"))
        except: return []

    def _save_history(self):
        try: json.dump(self.history,open(HISTORY_FILE,"w"),indent=2)
        except: self.log_msg("Save history error")

    def show_history(self):
        w=tk.Toplevel(self.root); w.title("History")
        txt=scrolledtext.ScrolledText(w,width=100,height=30); txt.pack(fill="both",expand=True)
        txt.insert("end",json.dumps(self.history,indent=2)); txt.config(state="disabled")

    def ui_updater(self):
        with self.signals_lock:
            to_delete=[]
            for sid,s in list(self.signals.items()):
                if s.state=="RESOLVED":
                    try:
                        created=datetime.strptime(s.created_at,"%Y-%m-%d %H:%M:%S")
                        if (datetime.now()-created).total_seconds()>600: s.widget.destroy(); to_delete.append(sid)
                    except: pass
            for d in to_delete: del self.signals[d]
        self.root.after(2000,self.ui_updater)

if __name__=="__main__":
    root=tk.Tk(); app=App(root); root.mainloop()