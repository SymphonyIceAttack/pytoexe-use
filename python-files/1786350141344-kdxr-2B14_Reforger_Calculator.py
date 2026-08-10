
import tkinter as tk
from tkinter import ttk, messagebox
from bisect import bisect_left
import math

APP_TITLE = "2Б14 Mortar Calculator — Arma Reforger"
DATA_NOTE = "Ballistic tables: Arma Reforger 1.7-era vanilla 2Б14 data"

# Vanilla 2Б14 HE table data visible in current public Reforger calculators.
# Each tuple: range_m, elevation_mils, tof_s, Hw, Zw, Xw
TABLES = {
    0: [
        (50,1456,15,44,169,9),(100,1411,15,46,82,9),(150,1365,14.9,47,55,9),
        (200,1319,14.8,50,42,10),(250,1269,14.6,51,33,11),(300,1218,14.4,58,28,11),
        (350,1160,14.1,64,24,12),(400,1097,13.7,72,21,13),(450,1025,13.2,101,18,13),
        (500,927,12.4,0,15,14)
    ],
    1: [
        (100,1446,19.5,27,215,18),(200,1392,19.4,28,99,19),(300,1336,19.2,29,64,20),
        (400,1276,18.9,31,44,22),(500,1213,18.6,35,35,24),(600,1142,18.1,40,28,26),
        (700,1060,17.4,48,25,27),(800,955,16.4,81,21,28)
    ],
    2: [
        (200,1432,24.8,17,169,37),(300,1397,24.7,18,129,37),(400,1362,24.6,18,86,39),
        (500,1326,24.4,18,69,41),(600,1288,24.2,20,62,42),(700,1249,24,20,52,44),
        (800,1208,23.7,22,44,47),(900,1163,23.3,23,39,49),(1000,1115,22.9,26,36,50),
        (1100,1062,22.3,29,32,52),(1200,999,21.5,37,28,53),(1300,917,20.4,55,24,53),
        (1400,765,17.8,0,19,49)
    ],
    3: [
        (300,1423,28.9,13,174,57),(400,1397,28.8,14,149,59),(500,1370,28.6,13,106,60),
        (600,1343,28.5,14,97,60),(700,1316,28.5,14,76,63),(800,1287,28.3,14,72,64),
        (900,1257,28.1,16,59,67),(1000,1227,27.9,16,54,69),(1100,1194,27.6,16,51,70),
        (1200,1160,27.2,18,44,73),(1300,1125,26.8,19,41,75),(1400,1085,26.4,22,37,77),
        (1500,1042,25.8,24,34,78),(1600,993,25.1,28,31,79),(1700,935,24.2,36,29,79),
        (1800,855,22.8,68,26,78)
    ],
    4: [
        (400,1419,32.9,10,186,81),(500,1398,32.9,11,170,81),(600,1377,32.8,10,126,84),
        (700,1355,32.7,11,108,86),(800,1333,32.6,11,94,88),(900,1311,32.4,12,84,90),
        (1000,1288,32.2,12,81,90),(1100,1265,32.1,12,69,94),(1200,1240,31.8,13,67,94),
        (1300,1216,31.6,13,59,98),(1400,1189,31.3,14,57,98),(1500,1162,31,14,50,102),
        (1600,1134,30.7,15,45,104),(1700,1103,30.3,16,45,104),(1800,1071,29.8,17,41,106),
        (1900,1036,29.3,19,38,107),(2000,996,28.7,22,36,108),(2100,952,27.9,26,34,108),
        (2200,899,26.9,34,30,108),(2300,825,25.3,65,27,105)
    ],
}

# Approximate max ranges used only for validation/selection.
RANGES = {k:(v[0][0],v[-1][0]) for k,v in TABLES.items()}

def interp(table, x):
    xs=[r[0] for r in table]
    if x < xs[0] or x > xs[-1]:
        raise ValueError("outside table")
    i=bisect_left(xs,x)
    if i==0: return table[0][1:]
    if i==len(xs): return table[-1][1:]
    a,b=table[i-1],table[i]
    t=(x-a[0])/(b[0]-a[0])
    return tuple(a[j]+t*(b[j]-a[j]) for j in range(1,6))

def normalize_deg(x): return x % 360.0

def solve(range_m, bearing_deg, mortar_h, target_h, wind_speed, wind_from):
    # Height difference is handled as a first-order trajectory correction.
    # Wind coefficients are taken from the in-game table convention:
    # Hw -> elevation effect, Zw -> azimuth effect, Xw -> longitudinal range effect.
    candidates=[]
    for rings, table in TABLES.items():
        lo,hi=RANGES[rings]
        if lo <= range_m <= hi:
            p,tof,hw,zw,xw = interp(table, range_m)
            # Wind vector: direction FROM. Resolve along target bearing.
            rel=math.radians(normalize_deg(wind_from-bearing_deg))
            head = wind_speed*math.cos(rel)      # + = wind coming from target direction
            cross = wind_speed*math.sin(rel)     # + = from right of target axis
            # Longitudinal wind changes effective range; crosswind changes azimuth.
            # Sign convention is chosen to match the meteorological FROM convention.
            effective_range = range_m + xw*head
            try:
                p_w,tof_w,hw_w,zw_w,xw_w = interp(table, max(lo,min(hi,effective_range)))
            except Exception:
                p_w,tof_w,hw_w,zw_w,xw_w = p,tof,hw,zw,xw
            elevation = p_w + hw_w*head/100.0
            az_corr = zw_w*cross/10.0
            # Height: positive target elevation requires a slightly higher trajectory.
            # This is a gameplay approximation and is intentionally exposed as such.
            dh = target_h - mortar_h
            elevation += (dh/max(range_m,1.0))*1000.0*0.35
            azimuth = normalize_deg(bearing_deg + az_corr/10.0)
            candidates.append((rings,elevation,azimuth,tof_w,head,cross,dh,p_w,az_corr))
    if not candidates:
        return None
    # Prefer the lowest charge that can reach the target.
    return min(candidates, key=lambda x:x[0])

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("760x650")
        self.minsize(700,600)
        self.configure(padx=16,pady=16)
        self._build()

    def _entry(self, parent, label, default, row, unit=""):
        ttk.Label(parent,text=label).grid(row=row,column=0,sticky="w",padx=5,pady=5)
        e=ttk.Entry(parent,width=18)
        e.insert(0,str(default))
        e.grid(row=row,column=1,sticky="w",padx=5,pady=5)
        if unit: ttk.Label(parent,text=unit).grid(row=row,column=2,sticky="w",padx=5)
        return e

    def _build(self):
        ttk.Label(self,text="2Б14 — MORTAR CALCULATOR",font=("Segoe UI",18,"bold")).pack(anchor="w")
        ttk.Label(self,text="Arma Reforger • vanilla 2Б14 • automatic ring selection",
                  font=("Segoe UI",10)).pack(anchor="w",pady=(0,12))

        f=ttk.LabelFrame(self,text="Ввод данных",padding=12); f.pack(fill="x")
        self.e_range=self._entry(f,"Дальность до цели",1500,0,"м")
        self.e_bearing=self._entry(f,"Азимут на цель",90,1,"°")
        self.e_mh=self._entry(f,"Высота миномёта",100,2,"м MSL")
        self.e_th=self._entry(f,"Высота цели",100,3,"м MSL")
        self.e_ws=self._entry(f,"Скорость ветра",0,4,"м/с")
        self.e_wd=self._entry(f,"Направление ветра FROM",0,5,"°")

        bf=ttk.Frame(f); bf.grid(row=6,column=0,columnspan=3,sticky="w",pady=(10,0))
        ttk.Label(bf,text="Режим колец:").pack(side="left",padx=(0,6))
        self.ring=ttk.Combobox(bf,state="readonly",width=12,
                               values=["Авто","0","1","2","3","4"])
        self.ring.set("Авто"); self.ring.pack(side="left")

        ttk.Button(bf,text="РАССЧИТАТЬ",command=self.calculate).pack(side="left",padx=12)
        ttk.Button(bf,text="Очистить",command=self.clear).pack(side="left")

        out=ttk.LabelFrame(self,text="Результат",padding=12); out.pack(fill="both",expand=True,pady=12)
        self.vars={k:tk.StringVar(value="—") for k in
                   ["rings","elev","az","tof","wind","height","range"]}
        labels=[
            ("КОЛЕЦ","rings"),("ПРИЦЕЛ / ELEVATION","elev"),("АЗИМУТ","az"),
            ("ВРЕМЯ ПОЛЁТА","tof"),("ВЕТРОВАЯ ПОПРАВКА","wind"),
            ("ПРЕВЫШЕНИЕ ЦЕЛИ","height"),("РАСЧЁТНАЯ ДАЛЬНОСТЬ","range")]
        for i,(lab,key) in enumerate(labels):
            ttk.Label(out,text=lab,font=("Segoe UI",10,"bold")).grid(row=i,column=0,sticky="w",pady=6)
            ttk.Label(out,textvariable=self.vars[key],font=("Consolas",12)).grid(row=i,column=1,sticky="w",padx=18)

        note=ttk.LabelFrame(self,text="Важно",padding=10); note.pack(fill="x")
        ttk.Label(note,text=
            "Это игровой калькулятор. Табличные данные взяты из опубликованных таблиц 2Б14 "
            "для Reforger. Ветровая/высотная коррекция в этой версии — приближённая; "
            "перед использованием в игре обязательно проверь результат несколькими выстрелами.",
            wraplength=690,justify="left").pack(anchor="w")
        ttk.Label(self,text=DATA_NOTE,foreground="#666").pack(anchor="w",pady=(6,0))

    def clear(self):
        for v in self.vars.values(): v.set("—")

    def calculate(self):
        try:
            R=float(self.e_range.get().replace(",","."))
            B=float(self.e_bearing.get().replace(",","."))
            MH=float(self.e_mh.get().replace(",","."))
            TH=float(self.e_th.get().replace(",","."))
            WS=float(self.e_ws.get().replace(",","."))
            WD=float(self.e_wd.get().replace(",","."))
            if R<=0 or WS<0: raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка","Проверь числовые поля.")
            return

        manual=self.ring.get()
        if manual=="Авто":
            sol=solve(R,B,MH,TH,WS,WD)
        else:
            ring=int(manual)
            lo,hi=RANGES[ring]
            if not(lo<=R<=hi):
                messagebox.showwarning("Дальность вне таблицы",
                    f"Для {ring} колец таблица покрывает {lo}–{hi} м.")
                return
            # temporarily solve with a fixed ring
            p,tof,hw,zw,xw=interp(TABLES[ring],R)
            rel=math.radians(normalize_deg(WD-B))
            head=WS*math.cos(rel); cross=WS*math.sin(rel)
            eff=R+xw*head
            eff=max(lo,min(hi,eff))
            p2,tof2,hw2,zw2,xw2=interp(TABLES[ring],eff)
            elev=p2+hw2*head/100.0+(TH-MH)/max(R,1)*350
            az=normalize_deg(B+(zw2*cross/10)/10)
            sol=(ring,elev,az,tof2,head,cross,TH-MH,p2,(zw2*cross/10))
        if sol is None:
            messagebox.showerror("Нет решения","Цель находится вне диапазона 2Б14 для всех колец.")
            return
        rings,elev,az,tof,head,cross,dh,p0,azcorr=sol
        self.vars["rings"].set(str(rings))
        self.vars["elev"].set(f"{elev:.1f} тыс.")
        self.vars["az"].set(f"{az:.1f}°  ({az*10:.0f} тыс.)")
        self.vars["tof"].set(f"{tof:.1f} с")
        self.vars["wind"].set(f"прод. {head:+.2f} м/с; бок. {cross:+.2f} м/с")
        self.vars["height"].set(f"{dh:+.1f} м")
        self.vars["range"].set(f"{R:.0f} м")

if __name__=="__main__":
    App().mainloop()
