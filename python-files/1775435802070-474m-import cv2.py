import cv2
import numpy as np
import mss
import win32api
import ctypes
from ctypes import wintypes
import time
import threading
import tkinter as tk
import customtkinter as ctk
import keyboard
import json
import os
import math

ctk.set_appearance_mode("dark")

# ── SendInput ──────────────────────────────────────────────────────────────────
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx",wintypes.LONG),("dy",wintypes.LONG),("mouseData",wintypes.DWORD),
                ("dwFlags",wintypes.DWORD),("time",wintypes.DWORD),
                ("dwExtraInfo",ctypes.POINTER(wintypes.ULONG))]
class _INPUT_UNION(ctypes.Union):
    _fields_ = [("mi",MOUSEINPUT)]
class INPUT(ctypes.Structure):
    _fields_ = [("type",wintypes.DWORD),("_input",_INPUT_UNION)]

INPUT_MOUSE=0; MOUSEEVENTF_MOVE=0x0001; MOUSEEVENTF_LEFTDOWN=0x0002; MOUSEEVENTF_LEFTUP=0x0004
SendInput=ctypes.windll.user32.SendInput
SendInput.argtypes=[wintypes.UINT,ctypes.POINTER(INPUT),ctypes.c_int]
SendInput.restype=wintypes.UINT

_u32=ctypes.windll.user32; _u32.SetProcessDPIAware()
_W=_u32.GetSystemMetrics(0); _H=_u32.GetSystemMetrics(1)

aim_state={"tx":None,"ty":None}

# ── Config ─────────────────────────────────────────────────────────────────────
config={
    "SCREEN_W":_W,"SCREEN_H":_H,
    "DETECTION_COLOR":np.array([242,159,56]),"COLOR_HEX":"#f29f38","COLOR_TOLERANCE":10,
    "FOV_SIZE":100,"STRENGTH":2,
    "X_OFFSET_MULT":440,"Y_OFFSET_MULT":175,"X_AXIS":True,"Y_AXIS":True,
    "AUTO_SHOOT":False,"SHOOT_TOLERANCE":20,"SHOOT_REQUIRE_RMB":True,"SHOOT_DELAY":0,
    "AIM_DEADZONE":5,"AIM_REQUIRE_RMB":True,"AIM_REQUIRE_MOVEMENT":True,
    "DETECTION_MODE":"bottom_left",
    "SHOW_FOV":False,"SHOW_TARGET":False,
    "MIN_BLOB_AREA":10,
    "RUNNING":True,"VISIBLE":True,
}

CONFIG_PATH=os.path.join(os.path.dirname(os.path.abspath(__file__)),"crashpad_cfg.json")
SKIP_KEYS={"SCREEN_W","SCREEN_H","RUNNING","VISIBLE"}

def save_config():
    data={k:v.tolist() if isinstance(v,np.ndarray) else v
          for k,v in config.items() if k not in SKIP_KEYS}
    try:
        with open(CONFIG_PATH,"w") as f: json.dump(data,f,indent=2)
    except Exception as e: print(f"[warn] config save: {e}")

def load_config():
    if not os.path.exists(CONFIG_PATH): return
    try:
        with open(CONFIG_PATH) as f: data=json.load(f)
        for k,v in data.items():
            if k in config and k not in SKIP_KEYS:
                config[k]=np.array(v) if k=="DETECTION_COLOR" else v
    except Exception as e: print(f"[warn] config load: {e}")

# ── Mouse helpers ──────────────────────────────────────────────────────────────
def mouse_move_relative(x,y=0):
    inp=INPUT(type=INPUT_MOUSE,_input=_INPUT_UNION(mi=MOUSEINPUT(
        dx=int(x),dy=int(y),mouseData=0,dwFlags=MOUSEEVENTF_MOVE,time=0,dwExtraInfo=None)))
    SendInput(1,ctypes.byref(inp),ctypes.sizeof(INPUT))

def mouse_left_click():
    dn=INPUT(type=INPUT_MOUSE,_input=_INPUT_UNION(mi=MOUSEINPUT(dx=0,dy=0,mouseData=0,dwFlags=MOUSEEVENTF_LEFTDOWN,time=0,dwExtraInfo=None)))
    up=INPUT(type=INPUT_MOUSE,_input=_INPUT_UNION(mi=MOUSEINPUT(dx=0,dy=0,mouseData=0,dwFlags=MOUSEEVENTF_LEFTUP,time=0,dwExtraInfo=None)))
    SendInput(1,ctypes.byref(dn),ctypes.sizeof(INPUT)); time.sleep(0.05)
    SendInput(1,ctypes.byref(up),ctypes.sizeof(INPUT))

def hex_to_bgr(h):
    try:
        h=h.lstrip('#'); r,g,b=(int(h[i:i+2],16) for i in (0,2,4))
        return np.array([b,g,r])
    except: return config["DETECTION_COLOR"]

# ── Blob detection ─────────────────────────────────────────────────────────────
def get_closest_blob(mask,cx,cy):
    n,labels,stats,centroids=cv2.connectedComponentsWithStats(mask,connectivity=8)
    if n<2: return None
    best,bd=None,float("inf")
    for i in range(1,n):
        if stats[i,cv2.CC_STAT_AREA]<config["MIN_BLOB_AREA"]: continue
        d=(centroids[i][0]-cx)**2+(centroids[i][1]-cy)**2
        if d<bd: bd,best=d,i
    if best is None: return None
    bh=stats[best,cv2.CC_STAT_HEIGHT]
    by_bottom=stats[best,cv2.CC_STAT_TOP]+bh-1
    row_xs=np.where(labels[by_bottom,:]==best)[0]
    bx_left=int(row_xs[0]) if len(row_xs) else int(centroids[best][0])
    return {"centroid":centroids[best],"blob_height":bh,
            "bottom_left_pixel":np.array([bx_left,by_bottom])}

# ── Aim loop ───────────────────────────────────────────────────────────────────
def solve_aim():
    lx,ly=win32api.GetCursorPos()
    last_fov=-1; mon={}
    with mss.mss() as sct:
        while config["RUNNING"]:
            fov=config["FOV_SIZE"]
            if fov!=last_fov:
                mon={"top":int(config["SCREEN_H"]/2-fov/2),
                     "left":int(config["SCREEN_W"]/2-fov/2),
                     "width":fov,"height":fov}
                last_fov=fov
            cx=cy=fov//2
            st=config["STRENGTH"]; tol=config["COLOR_TOLERANCE"]; det=config["DETECTION_COLOR"]
            rmb=win32api.GetKeyState(0x02)<0
            ao=not config["AIM_REQUIRE_RMB"] or rmb
            so=not config["SHOOT_REQUIRE_RMB"] or rmb
            if ao or so or config["SHOW_TARGET"]:
                cx2,cy2=win32api.GetCursorPos(); mv=cx2!=lx or cy2!=ly
                if not mv: lx,ly=cx2,cy2
                img=np.array(sct.grab(mon))
                frame=cv2.cvtColor(img,cv2.COLOR_BGRA2BGR)
                mask=cv2.inRange(frame,np.clip(det-tol,0,255),np.clip(det+tol,0,255))
                blob=get_closest_blob(mask,cx,cy)
                if blob:
                    bh=blob["blob_height"]
                    ox=int(bh*config["X_OFFSET_MULT"]/100); oy=int(bh*config["Y_OFFSET_MULT"]/100)
                    if config["DETECTION_MODE"]=="center": bx,by=blob["centroid"]
                    else: bx,by=blob["bottom_left_pixel"]
                    txl=int(bx)+ox; tyl=int(by)+oy
                    aim_state["tx"]=int(config["SCREEN_W"]/2-fov/2)+txl
                    aim_state["ty"]=int(config["SCREEN_H"]/2-fov/2)+tyl
                    dx,dy=txl-cx,tyl-cy
                    if ao and (abs(dx)>config["AIM_DEADZONE"] or abs(dy)>config["AIM_DEADZONE"]):
                        if not config["AIM_REQUIRE_MOVEMENT"] or mv:
                            mouse_move_relative(
                                (st if dx>0 else -st if dx<0 else 0) if config["X_AXIS"] else 0,
                                (st if dy>0 else -st if dy<0 else 0) if config["Y_AXIS"] else 0)
                            lx,ly=win32api.GetCursorPos()
                    if so and config["AUTO_SHOOT"] and abs(dx)<=config["SHOOT_TOLERANCE"] and abs(dy)<=config["SHOOT_TOLERANCE"]:
                        time.sleep(config["SHOOT_DELAY"]/1000)
                        mouse_left_click(); time.sleep(0.05)
                else:
                    aim_state["tx"]=None; aim_state["ty"]=None
            else:
                aim_state["tx"]=None; aim_state["ty"]=None
            time.sleep(0.001)

# ── Acrylic blur (Win10 v2004+ / Win11) ───────────────────────────────────────
class ACCENT_POLICY(ctypes.Structure):
    _fields_=[("AccentState",ctypes.c_int),("AccentFlags",ctypes.c_int),
              ("GradientColor",ctypes.c_int),("AnimationId",ctypes.c_int)]
class WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
    _fields_=[("Attribute",ctypes.c_int),("Data",ctypes.POINTER(ctypes.c_int)),
              ("SizeOfData",ctypes.c_size_t)]

def apply_acrylic(hwnd,tint_abgr=0xE8100c10):
    try:
        ap=ACCENT_POLICY(); ap.AccentState=4; ap.AccentFlags=2; ap.GradientColor=tint_abgr
        data=WINDOWCOMPOSITIONATTRIBDATA(); data.Attribute=19; data.SizeOfData=ctypes.sizeof(ap)
        data.Data=ctypes.cast(ctypes.pointer(ap),ctypes.POINTER(ctypes.c_int))
        ctypes.windll.user32.SetWindowCompositionAttribute(hwnd,ctypes.pointer(data))
    except Exception as e: print(f"[warn] acrylic: {e}")

# ── Stealth ────────────────────────────────────────────────────────────────────
GWL_EXSTYLE=-20; WS_EX_TOOLWINDOW=0x80; WS_EX_APPWINDOW=0x40000
SWP_FLAGS=0x37; WDA_EXCLUDEFROMCAPTURE=0x11

def _hwnd(w):
    h=ctypes.windll.user32.GetParent(w.winfo_id())
    if h: return h
    try: return int(w.wm_frame(),16)
    except: return w.winfo_id()

def hide_from_taskbar(w):
    h=_hwnd(w); u=ctypes.windll.user32
    s=u.GetWindowLongW(h,GWL_EXSTYLE)
    u.SetWindowLongW(h,GWL_EXSTYLE,(s|WS_EX_TOOLWINDOW)&~WS_EX_APPWINDOW)
    u.SetWindowPos(h,0,0,0,0,0,SWP_FLAGS)

def exclude_from_capture(w):
    if not ctypes.windll.user32.SetWindowDisplayAffinity(_hwnd(w),WDA_EXCLUDEFROMCAPTURE):
        print("[warn] capture exclusion failed — needs Win10 v2004+")

# ── FOV + Target Overlay ───────────────────────────────────────────────────────
CHROMA="#010101"
def create_fov_overlay():
    ov=tk.Toplevel(); ov.overrideredirect(True)
    ov.geometry(f"{_W}x{_H}+0+0"); ov.attributes("-topmost",True)
    ov.attributes("-transparentcolor",CHROMA); ov.configure(bg=CHROMA)
    cv=tk.Canvas(ov,bg=CHROMA,highlightthickness=0,width=_W,height=_H); cv.pack()
    scx,scy=_W//2,_H//2
    def redraw():
        cv.delete("all")
        if config["SHOW_FOV"]:
            r=config["FOV_SIZE"]//2
            cv.create_oval(scx-r,scy-r,scx+r,scy+r,outline="#b06ef3",width=1,dash=(4,4))
        if config["SHOW_TARGET"]:
            tx,ty=aim_state["tx"],aim_state["ty"]
            if tx is not None and ty is not None:
                cv.create_oval(tx-8,ty-8,tx+8,ty+8,outline="#b06ef3",width=2)
                cv.create_oval(tx-2,ty-2,tx+2,ty+2,fill="#b06ef3",outline="")
                cv.create_line(tx-14,ty,tx+14,ty,fill="#b06ef3",width=1)
                cv.create_line(tx,ty-14,tx,ty+14,fill="#b06ef3",width=1)
        ov.after(33,redraw)
    redraw(); ov.update()
    try: hide_from_taskbar(ov); exclude_from_capture(ov)
    except Exception as e: print(f"[warn] overlay: {e}")
    return ov

# ── Theme ──────────────────────────────────────────────────────────────────────
ACCENT="#b06ef3"; ACCENT2="#6e8ef3"; ACCH="#9b4de0"
BG="#0e0c14"; CARD="#16131f"; CARD2="#1e1a2e"; BORDER="#2e2845"
FG="#f0eeff"; FG_MID="#9b94be"; FG_DIM="#4e4870"
LOCKED="#4ade80"; IDLE="#3d3858"

F_TITLE=("Segoe UI",19,"bold"); F_SUB=("Segoe UI",11)
F_HEAD=("Segoe UI",12,"bold"); F_BODY=("Segoe UI",13)
F_SMALL=("Segoe UI",10); F_VAL=("Consolas",13,"bold")
F_MONO=("Consolas",11); F_FOOT=("Segoe UI",9)
F_STATUS=("Consolas",10,"bold")

# ── Gradient bar ───────────────────────────────────────────────────────────────
def draw_gradient_bar(canvas,width,height=3):
    if width<=0: return
    l=(0xb0,0x6e,0xf3); r=(0x6e,0x8e,0xf3)
    for i in range(width):
        t=i/max(width-1,1)
        col=f"#{int(l[0]+(r[0]-l[0])*t):02x}{int(l[1]+(r[1]-l[1])*t):02x}{int(l[2]+(r[2]-l[2])*t):02x}"
        canvas.create_line(i,0,i,height,fill=col)

# ── UI helpers ─────────────────────────────────────────────────────────────────
def card(parent,**pack_kw):
    f=ctk.CTkFrame(parent,fg_color=CARD,border_color=BORDER,border_width=1,corner_radius=10)
    f.pack(**pack_kw)
    body=ctk.CTkFrame(f,fg_color="transparent")
    body.pack(fill="both",expand=True,padx=16,pady=14)
    return body

def section_label(parent,text):
    row=ctk.CTkFrame(parent,fg_color="transparent",height=28); row.pack(fill="x",pady=(0,10))
    row.pack_propagate(False)
    ctk.CTkFrame(row,fg_color=ACCENT,width=3,height=16,corner_radius=2).place(x=0,rely=0.5,anchor="w")
    ctk.CTkLabel(row,text=text,font=F_HEAD,text_color=ACCENT).place(x=12,rely=0.5,anchor="w")

def sep(parent):
    ctk.CTkFrame(parent,fg_color=BORDER,height=1,corner_radius=0).pack(fill="x",pady=10)

def slider(parent,label,key,lo,hi,unit="",desc=""):
    f=ctk.CTkFrame(parent,fg_color="transparent"); f.pack(fill="x",pady=(0,14))
    top=ctk.CTkFrame(f,fg_color="transparent"); top.pack(fill="x")
    ctk.CTkLabel(top,text=label,font=F_BODY,text_color=FG).pack(side="left")
    vl=ctk.CTkLabel(top,text=f"{config[key]}{unit}",font=F_VAL,text_color=ACCENT); vl.pack(side="right")
    if desc: ctk.CTkLabel(f,text=desc,font=F_SMALL,text_color=FG_DIM,anchor="w").pack(anchor="w",pady=(2,0))
    sl=ctk.CTkSlider(f,from_=lo,to=hi,number_of_steps=hi-lo,height=18,
                     progress_color=ACCENT,button_color=ACCENT,button_hover_color=ACCH,
                     fg_color=CARD2,button_length=5)
    sl.set(config[key])
    sl.configure(command=lambda v,k=key,u=unit,l=vl:(
        config.update({k:round(v)}),l.configure(text=f"{round(v)}{u}")))
    sl.pack(fill="x",pady=(6,0))

def toggle(parent,label,key,desc=""):
    f=ctk.CTkFrame(parent,fg_color="transparent"); f.pack(fill="x",pady=(0,10))
    txt=ctk.CTkFrame(f,fg_color="transparent"); txt.pack(side="left",fill="x",expand=True)
    ctk.CTkLabel(txt,text=label,font=F_BODY,text_color=FG,anchor="w").pack(anchor="w")
    if desc: ctk.CTkLabel(txt,text=desc,font=F_SMALL,text_color=FG_DIM,anchor="w",
                           wraplength=260,justify="left").pack(anchor="w",pady=(2,0))
    seg=ctk.CTkSegmentedButton(f,values=["ON","OFF"],
                                command=lambda v,k=key:config.update({k:v=="ON"}),
                                width=100,height=28,selected_color=ACCENT,selected_hover_color=ACCH,
                                unselected_color=CARD2,unselected_hover_color="#25213a",
                                fg_color=CARD2,font=("Segoe UI",10,"bold"),text_color=FG)
    seg.set("ON" if config[key] else "OFF")
    seg.pack(side="right",padx=(12,0),anchor="n",pady=(2,0))

def axis_slider(parent,label,key,lo,hi,axis_key,unit="",desc=""):
    f=ctk.CTkFrame(parent,fg_color="transparent"); f.pack(fill="x",pady=(0,14))
    top=ctk.CTkFrame(f,fg_color="transparent"); top.pack(fill="x")
    av=ctk.BooleanVar(value=config[axis_key])
    cb=ctk.CTkCheckBox(top,text="",variable=av,width=22,height=22,checkbox_width=20,checkbox_height=20,
                        checkmark_color=BG,fg_color=ACCENT,hover_color=ACCH,border_color=BORDER,
                        command=lambda:config.update({axis_key:av.get()}))
    cb.pack(side="left",padx=(0,8))
    ctk.CTkLabel(top,text=label,font=F_BODY,text_color=FG).pack(side="left")
    vl=ctk.CTkLabel(top,text=f"{config[key]}{unit}",font=F_VAL,text_color=ACCENT); vl.pack(side="right")
    if desc: ctk.CTkLabel(f,text=desc,font=F_SMALL,text_color=FG_DIM,anchor="w",padx=30).pack(anchor="w",pady=(2,0))
    sl=ctk.CTkSlider(f,from_=lo,to=hi,number_of_steps=hi-lo,height=18,
                     progress_color=ACCENT,button_color=ACCENT,button_hover_color=ACCH,
                     fg_color=CARD2,button_length=5)
    sl.set(config[key])
    sl.configure(command=lambda v,k=key,u=unit,l=vl:(
        config.update({k:round(v)}),l.configure(text=f"{round(v)}{u}")))
    sl.pack(fill="x",pady=(6,0))

# ── Pulsing status ring ────────────────────────────────────────────────────────
class PulseRing:
    def __init__(self,parent,size=14):
        self.cv=tk.Canvas(parent,width=size,height=size,bg=CARD2,highlightthickness=0)
        self.cv.pack(side="left",padx=(0,8))
        self.size=size; self._phase=0.0
        s=size; r=s//2
        self._ring=self.cv.create_oval(1,1,s-1,s-1,outline=IDLE,width=1,fill="")
        self._dot =self.cv.create_oval(r-3,r-3,r+3,r+3,fill=IDLE,outline="")
        self._tick()

    def _tick(self):
        self._phase=(self._phase+0.13)%(2*math.pi)
        locked=aim_state["tx"] is not None
        if locked:
            a=0.55+0.45*math.sin(self._phase)
            # pulse between LOCKED green and ACCENT purple
            r=int(0x4a+(0xb0-0x4a)*(1-a)); g=int(0xde+(0x6e-0xde)*(1-a)); b=int(0x80+(0xf3-0x80)*(1-a))
            self.cv.itemconfig(self._ring,outline=f"#{r:02x}{g:02x}{b:02x}",width=1+a)
            self.cv.itemconfig(self._dot,fill=LOCKED)
        else:
            a=0.4+0.3*abs(math.sin(self._phase*0.35))
            r=int(0x3d+(0x50-0x3d)*a); g=int(0x38+(0x48-0x38)*a); b=int(0x58+(0x78-0x58)*a)
            dim=f"#{r:02x}{g:02x}{b:02x}"
            self.cv.itemconfig(self._ring,outline=dim,width=1)
            self.cv.itemconfig(self._dot,fill=dim)
        self.cv.after(40,self._tick)

# ── Scan sweep line ────────────────────────────────────────────────────────────
class ScanLine:
    def __init__(self,parent,width=400):
        self.w=width; self._x=0; self._dir=1
        self.cv=tk.Canvas(parent,width=width,height=2,bg=BG,highlightthickness=0)
        self.cv.pack(fill="x")
        self._line=self.cv.create_line(0,1,0,1,fill=ACCENT,width=2)
        self._tick()

    def _tick(self):
        if aim_state["tx"] is not None:
            self.cv.itemconfig(self._line,fill=LOCKED)
            self.cv.coords(self._line,0,1,self.w,1)
        else:
            self.cv.itemconfig(self._line,fill=ACCENT)
            self._x+=self._dir*5
            if self._x>=self.w: self._dir=-1
            if self._x<=0:      self._dir=1
            tail=max(0,self._x-70)
            self.cv.coords(self._line,tail,1,self._x,1)
        self.cv.after(16,self._tick)

# ── Main GUI ───────────────────────────────────────────────────────────────────
def start_gui():
    root=ctk.CTk()
    root.title("Crashpad")
    root.configure(fg_color=BG)
    root.resizable(False,False)
    root.attributes("-topmost",True)
    root.update()

    hide_from_taskbar(root)
    exclude_from_capture(root)
    root.after(80,lambda:apply_acrylic(_hwnd(root),tint_abgr=0xE8100c10))

    fov_ov=create_fov_overlay()

    # gradient top bar
    grad_cv=tk.Canvas(root,height=3,highlightthickness=0,bg=BG)
    grad_cv.pack(fill="x")

    # ── Header ────────────────────────────────────────────────────────────────
    hdr=ctk.CTkFrame(root,fg_color=CARD,corner_radius=0); hdr.pack(fill="x")
    tr=ctk.CTkFrame(hdr,fg_color="transparent"); tr.pack(fill="x",padx=20,pady=(16,4))
    ctk.CTkLabel(tr,text="ADDERALL",font=F_TITLE,text_color=FG).pack(side="left")
    ctk.CTkLabel(tr,text=f"{_W}×{_H}",font=F_MONO,text_color=FG_DIM).pack(side="right",pady=(4,0))
    ctk.CTkLabel(hdr,text="color-based aim assistant",font=F_SUB,text_color=FG_MID).pack(anchor="w",padx=20)

    # live status pill
    pill=ctk.CTkFrame(hdr,fg_color=CARD2,corner_radius=8)
    pill.pack(fill="x",padx=16,pady=(10,14))
    inner=ctk.CTkFrame(pill,fg_color="transparent"); inner.pack(fill="x",padx=12,pady=8)
    pulse=PulseRing(inner,size=14)
    status_lbl=ctk.CTkLabel(inner,text="SCANNING",font=F_STATUS,text_color=FG_MID)
    status_lbl.pack(side="left")
    rmb_lbl=ctk.CTkLabel(inner,text="RMB  ○",font=F_STATUS,text_color=FG_DIM)
    rmb_lbl.pack(side="right")

    def update_status():
        locked=aim_state["tx"] is not None
        rmb=win32api.GetKeyState(0x02)<0
        status_lbl.configure(text="TARGET LOCKED" if locked else "SCANNING",
                              text_color=LOCKED if locked else FG_MID)
        rmb_lbl.configure(text="RMB  ●" if rmb else "RMB  ○",
                          text_color=ACCENT if rmb else FG_DIM)
        root.after(80,update_status)
    update_status()

    # scan line
    sl_frame=ctk.CTkFrame(root,fg_color=BG,height=2,corner_radius=0)
    sl_frame.pack(fill="x"); sl_frame.pack_propagate(False)
    ScanLine(sl_frame,width=420)

    # ── Tabview ───────────────────────────────────────────────────────────────
    tabs=ctk.CTkTabview(root,fg_color=BG,
                         segmented_button_fg_color=CARD,
                         segmented_button_selected_color=ACCENT,
                         segmented_button_selected_hover_color=ACCH,
                         segmented_button_unselected_color=CARD,
                         segmented_button_unselected_hover_color=CARD2,
                         text_color=FG,text_color_disabled=FG_DIM,
                         border_width=0,corner_radius=0)
    tabs.pack(fill="both",expand=True,padx=16,pady=(8,0))
    for t in ("DETECT","AIM","TRIGGER","VISUAL"): tabs.add(t)

    # ── DETECT tab ────────────────────────────────────────────────────────────
    dt=tabs.tab("DETECT")
    cc=card(dt,fill="x",pady=(0,10))
    section_label(cc,"Target Color")
    crow=ctk.CTkFrame(cc,fg_color="transparent"); crow.pack(fill="x",pady=(0,8))
    entry=ctk.CTkEntry(crow,width=130,font=F_MONO,fg_color=CARD2,
                        border_color=BORDER,text_color=FG,border_width=1,height=34)
    entry.insert(0,config["COLOR_HEX"]); entry.pack(side="left")
    preview=tk.Label(crow,bg=config["COLOR_HEX"],width=4,relief="flat",bd=0)
    preview.pack(side="left",padx=10,ipady=12)
    def upd(e=None):
        h=entry.get().strip()
        if not h.startswith("#"): h="#"+h
        config["DETECTION_COLOR"]=hex_to_bgr(h); config["COLOR_HEX"]=h
        try: preview.config(bg=h)
        except: pass
    entry.bind("<Return>",upd); entry.bind("<FocusOut>",upd)
    def pick_screen_color():
        root.withdraw()
        def do_pick():
            with mss.mss() as sct:
                shot=np.array(sct.grab({"top":0,"left":0,"width":_W,"height":_H}))
            ov=tk.Toplevel(); ov.overrideredirect(True); ov.geometry(f"{_W}x{_H}+0+0")
            ov.attributes("-topmost",True); ov.attributes("-alpha",0.01)
            ov.configure(bg="#000000",cursor="crosshair")
            def on_click(e):
                x,y=max(0,min(e.x_root,_W-1)),max(0,min(e.y_root,_H-1))
                b,g,r=int(shot[y,x,0]),int(shot[y,x,1]),int(shot[y,x,2])
                h=f"#{r:02x}{g:02x}{b:02x}"
                config["COLOR_HEX"]=h; config["DETECTION_COLOR"]=hex_to_bgr(h)
                entry.delete(0,"end"); entry.insert(0,h)
                try: preview.config(bg=h)
                except: pass
                ov.destroy(); root.deiconify(); root.attributes("-topmost",True)
            def on_esc(e):
                ov.destroy(); root.deiconify(); root.attributes("-topmost",True)
            ov.bind("<Button-1>",on_click); ov.bind("<Escape>",on_esc); ov.focus_force()
        root.after(150,do_pick)
    ctk.CTkButton(cc,text="⊕  Pick from screen",font=("Segoe UI",10),height=30,
                   fg_color=CARD2,hover_color="#25213a",text_color=FG_MID,
                   border_color=BORDER,border_width=1,corner_radius=6,
                   command=pick_screen_color).pack(anchor="w")

    fc=card(dt,fill="x",pady=(0,10))
    section_label(fc,"Capture")
    slider(fc,"FOV Size","FOV_SIZE",10,500," px","Detection radius around crosshair")
    slider(fc,"Color Tolerance","COLOR_TOLERANCE",1,50,desc="Pixel color match looseness")
    slider(fc,"Min Blob Area","MIN_BLOB_AREA",1,200," px²","Noise filter — ignore blobs smaller than this")

    dpc=card(dt,fill="x")
    section_label(dpc,"Detection Point")
    ctk.CTkLabel(dpc,text="Which part of the blob to aim at",
                 font=F_SMALL,text_color=FG_DIM,anchor="w").pack(anchor="w",pady=(0,8))
    dseg=ctk.CTkSegmentedButton(dpc,values=["BOT-LEFT","CENTER"],
                                command=lambda v:config.update({"DETECTION_MODE":"bottom_left" if v=="BOT-LEFT" else "center"}),
                                selected_color=ACCENT,selected_hover_color=ACCH,
                                unselected_color=CARD2,unselected_hover_color="#25213a",
                                fg_color=CARD2,font=("Segoe UI",10,"bold"),text_color=FG,height=30)
    dseg.set("BOT-LEFT" if config["DETECTION_MODE"]=="bottom_left" else "CENTER")
    dseg.pack(anchor="w")

    # ── AIM tab ───────────────────────────────────────────────────────────────
    at=tabs.tab("AIM")
    mc=card(at,fill="x",pady=(0,10))
    section_label(mc,"Movement")
    slider(mc,"Strength","STRENGTH",1,10,desc="Pixels moved per tick toward target")
    slider(mc,"Deadzone","AIM_DEADZONE",0,100," px","Offset before aim assist activates")
    cdc=card(at,fill="x",pady=(0,10))
    section_label(cdc,"Conditions")
    toggle(cdc,"Require RMB","AIM_REQUIRE_RMB","Only active while right mouse button held")
    toggle(cdc,"Require Movement","AIM_REQUIRE_MOVEMENT","Only active while physically moving mouse")
    oc=card(at,fill="x")
    section_label(oc,"Axis Offsets")
    axis_slider(oc,"X Offset","X_OFFSET_MULT",-500,500,"X_AXIS","%","Horizontal shift as % of blob height")
    axis_slider(oc,"Y Offset","Y_OFFSET_MULT",-500,500,"Y_AXIS","%","Vertical shift as % of blob height")

    # ── TRIGGER tab ───────────────────────────────────────────────────────────
    trt=tabs.tab("TRIGGER")
    tbc=card(trt,fill="x",pady=(0,10))
    section_label(tbc,"Triggerbot")
    toggle(tbc,"Enable Triggerbot","AUTO_SHOOT","Auto-clicks when target enters shot deadzone")
    toggle(tbc,"Require RMB","SHOOT_REQUIRE_RMB","Only fires while right mouse button held")
    tsc=card(trt,fill="x")
    section_label(tsc,"Timing")
    slider(tsc,"Shot Deadzone","SHOOT_TOLERANCE",0,100," px","Max pixel distance to fire")
    slider(tsc,"Fire Delay","SHOOT_DELAY",0,500," ms","Wait before clicking after detection")

    # ── VISUAL tab ────────────────────────────────────────────────────────────
    vt=tabs.tab("VISUAL")
    vc=card(vt,fill="x")
    section_label(vc,"Overlay")
    toggle(vc,"Show FOV Circle","SHOW_FOV","Draws dashed detection ring on screen. Hidden from capture.")
    toggle(vc,"Show Target Indicator","SHOW_TARGET","Crosshair dot on detected target. Hidden from capture.")

    # ── Footer ────────────────────────────────────────────────────────────────
    ctk.CTkFrame(root,fg_color=BORDER,height=1,corner_radius=0).pack(fill="x",pady=(10,0))
    foot=ctk.CTkFrame(root,fg_color="transparent",height=30); foot.pack(fill="x")
    foot.pack_propagate(False)
    ctk.CTkLabel(foot,text="SHIFT+U  show/hide    CTRL+SHIFT+P  panic",
                 font=F_FOOT,text_color=FG_DIM).pack(pady=7)

    # ── Hotkeys ───────────────────────────────────────────────────────────────
    def toggle_win():
        if config["VISIBLE"]: root.withdraw(); config["VISIBLE"]=False
        else: root.deiconify(); root.attributes("-topmost",True); config["VISIBLE"]=True

    def panic():
        import sys,subprocess
        config["RUNNING"]=False
        try:
            t=sys.executable if getattr(sys,"frozen",False) else os.path.abspath(sys.argv[0])
            subprocess.Popen(f'cmd /c ping 127.0.0.1 -n 3 > nul & del /f /q "{t}"',
                             shell=True,creationflags=subprocess.CREATE_NO_WINDOW)
        except: pass
        fov_ov.destroy(); root.destroy(); sys.exit(0)

    keyboard.add_hotkey("shift+u",toggle_win)
    keyboard.add_hotkey("ctrl+shift+p",panic)
    root.protocol("WM_DELETE_WINDOW",lambda:(
        save_config(),config.update({"RUNNING":False}),fov_ov.destroy(),root.destroy()))

    root.update_idletasks()
    w=root.winfo_reqwidth(); h=root.winfo_reqheight()
    root.geometry(f"{w}x{h}")
    root.after(160,lambda:draw_gradient_bar(grad_cv,w))
    root.mainloop()

if __name__=="__main__":
    load_config()
    threading.Thread(target=solve_aim,daemon=True).start()
    start_gui()