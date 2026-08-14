import tkinter as tk
from tkinter import ttk
import threading, time, json, os, re, webbrowser
from urllib.request import Request, urlopen
import winsound
from html.parser import HTMLParser

URL='https://kp04.skladchik.org/groupbuys/new/?prefix_id=1'
DATA=os.path.join(os.path.dirname(os.path.abspath(__file__)),'seen_topics.json')

class P(HTMLParser):
    def __init__(self): super().__init__(); self.a=False; self.buf=[]; self.items=[]
    def handle_starttag(self,t,a):
        if t=='a': self.a=True; self.buf=[]
    def handle_endtag(self,t):
        if t=='a' and self.a:
            s=re.sub(r'\s+',' ',''.join(self.buf)).strip()
            if len(s)>20: self.items.append(s)
            self.a=False
    def handle_data(self,d):
        if self.a: self.buf.append(d)

def get_topics(url):
    req=Request(url,headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151 Safari/537.36'})
    with urlopen(req,timeout=15) as r: html=r.read().decode('utf-8','ignore')
    p=P(); p.feed(html)
    bad=('Скрыть объявление','Новые складчины','Все складчины','Сбор взносов')
    return list(dict.fromkeys(x for x in p.items if not any(b in x for b in bad)))

class App:
    def __init__(self,root):
        self.root=root; self.root.title('Монитор новых складчин'); self.root.geometry('720x470'); self.running=False
        try: self.seen=set(json.load(open(DATA,encoding='utf-8')))
        except: self.seen=set()
        f=ttk.Frame(root,padding=12); f.pack(fill='both',expand=True)
        ttk.Label(f,text='Страница:').pack(anchor='w')
        self.url=ttk.Entry(f); self.url.insert(0,URL); self.url.pack(fill='x',pady=(0,10))
        row=ttk.Frame(f); row.pack(anchor='w')
        ttk.Label(row,text='Проверять каждые:').pack(side='left')
        self.sec=ttk.Spinbox(row,from_=2,to=3600,width=8); self.sec.set('2'); self.sec.pack(side='left',padx=6)
        ttk.Label(row,text='сек.').pack(side='left')
        buttons=ttk.Frame(f); buttons.pack(fill='x',pady=10)
        self.start=ttk.Button(buttons,text='▶ Запустить',command=self.start_monitor); self.start.pack(side='left')
        self.stopb=ttk.Button(buttons,text='■ Остановить',command=self.stop,state='disabled'); self.stopb.pack(side='left',padx=6)
        ttk.Button(buttons,text='Открыть страницу',command=lambda:webbrowser.open(self.url.get())).pack(side='right')
        self.status=ttk.Label(f,text='Готово. Первый запуск запоминает текущие складчины без звука.'); self.status.pack(anchor='w')
        ttk.Label(f,text='События:').pack(anchor='w',pady=(10,0))
        self.log=tk.Listbox(f); self.log.pack(fill='both',expand=True)
    def save(self):
        with open(DATA,'w',encoding='utf-8') as x: json.dump(sorted(self.seen),x,ensure_ascii=False,indent=2)
    def msg(self,s): self.root.after(0,lambda:(self.log.insert(0,s),self.status.config(text=s)))
    def start_monitor(self):
        if self.running:return
        self.running=True; self.start.config(state='disabled'); self.stopb.config(state='normal'); threading.Thread(target=self.loop,daemon=True).start()
    def stop(self): self.running=False; self.start.config(state='normal'); self.stopb.config(state='disabled'); self.status.config(text='Остановлено.')
    def loop(self):
        first=True
        while self.running:
            try:
                topics=get_topics(self.url.get().strip())
                if first and not self.seen:
                    self.seen.update(topics); self.save(); self.msg(f'Запомнено: {len(topics)} складчин')
                else:
                    new=[x for x in topics if x not in self.seen]
                    if new:
                        self.seen.update(new); self.save(); winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                        for x in new:self.msg('🔔 НОВАЯ СКЛАДЧИНА: '+x)
                    else:self.msg(f'Проверено: новых нет ({len(topics)} найдено)')
                first=False
            except Exception as e:self.msg('Ошибка: '+str(e))
            try: delay=max(2,int(self.sec.get()))
            except: delay=2
            for _ in range(delay):
                if not self.running:break
                time.sleep(1)

root=tk.Tk(); App(root); root.mainloop()
