import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import json, os

DATA='calendar_events.json'

def load():
    if os.path.exists(DATA):
        try:
            return json.load(open(DATA,'r',encoding='utf-8'))
        except: return []
    return []

def save(events):
    json.dump(events, open(DATA,'w',encoding='utf-8'), ensure_ascii=False, indent=2)

class App:
    def __init__(self,r):
        self.r=r; r.title('Desktop Calendar Reminder'); r.geometry('420x500')
        r.attributes('-topmost',True)
        self.events=load()
        ttk.Label(r,text='日付(YYYY-MM-DD)').pack()
        self.date=ttk.Entry(r); self.date.pack(fill='x',padx=5)
        ttk.Label(r,text='予定').pack()
        self.text=ttk.Entry(r); self.text.pack(fill='x',padx=5)
        ttk.Button(r,text='追加',command=self.add).pack(pady=4)
        self.lb=tk.Listbox(r); self.lb.pack(fill='both',expand=True,padx=5,pady=5)
        self.refresh(); self.check()
    def add(self):
        d=self.date.get().strip(); t=self.text.get().strip()
        if not d or not t: return
        self.events.append({'date':d,'text':t,'reminded':False})
        save(self.events); self.refresh()
    def refresh(self):
        self.lb.delete(0,'end')
        for e in self.events: self.lb.insert('end', f"{e['date']} : {e['text']}")
    def check(self):
        today=datetime.now().strftime('%Y-%m-%d')
        changed=False
        for e in self.events:
            if e['date']<=today and not e.get('reminded'):
                e['reminded']=True; changed=True
                messagebox.showinfo('リマインダー', e['text'])
        if changed: save(self.events)
        self.r.after(60000,self.check)
root=tk.Tk(); App(root); root.mainloop()
