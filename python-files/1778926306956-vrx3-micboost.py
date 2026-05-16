import tkinter as tk
import subprocess
import threading

__author__ = "forgot1en"

# ── Apply mic volume via PowerShell (no external libs needed) ──
def apply_mic_volume(pct):
    val = round(pct / 100, 2)
    script = f"""
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
[Guid("5CDF2C82-841E-4546-9722-0CF74078229A"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioEndpointVolume {{
    int _VtblGap1_6();
    int SetMasterVolumeLevelScalar(float fLevel, ref Guid pguidEventContext);
    int _VtblGap2_1();
    int GetMasterVolumeLevelScalar(out float pfLevel);
    int SetMute([MarshalAs(UnmanagedType.Bool)] bool bMute, ref Guid pguidEventContext);
    int GetMute([MarshalAs(UnmanagedType.Bool)] out bool pbMute);
}}
[Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDevice {{
    int Activate(ref Guid iid, int dwClsCtx, IntPtr pActivationParams, [MarshalAs(UnmanagedType.IUnknown)] out object ppInterface);
}}
[Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDeviceEnumerator {{
    int _VtblGap1_1();
    int GetDefaultAudioEndpoint(int dataFlow, int role, out IMMDevice ppDevice);
}}
[ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")]
class MMDeviceEnumeratorComClass {{ }}
public class MicVol {{
    public static void Set(float level) {{
        var t = Type.GetTypeFromCLSID(new Guid("BCDE0395-E52F-467C-8E3D-C4579291692E"));
        var e = (IMMDeviceEnumerator)Activator.CreateInstance(t);
        IMMDevice dev;
        e.GetDefaultAudioEndpoint(1, 1, out dev);
        var iid = new Guid("5CDF2C82-841E-4546-9722-0CF74078229A");
        object obj;
        dev.Activate(ref iid, 23, IntPtr.Zero, out obj);
        var ep = (IAudioEndpointVolume)obj;
        var g = Guid.Empty;
        ep.SetMasterVolumeLevelScalar(level, ref g);
    }}
}}
'@
[MicVol]::Set({val}f)
"""
    try:
        subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-Command", script],
                       capture_output=True, timeout=15)
        return True
    except:
        return False

def apply_mic_boost_reg(boost_db):
    # Set mic boost via Windows mixer registry
    script = f"""
$path = 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\MMDevices\\Audio\\Capture'
if (Test-Path $path) {{
    Get-ChildItem $path | ForEach-Object {{
        $p = "$($_.PSPath)\\Properties"
        if (Test-Path $p) {{
            New-ItemProperty -Path $p -Name '{{BF463910-BE6B-11D0-8E97-00A0C90F26F8}},0' -Value {boost_db} -PropertyType DWord -Force -ErrorAction SilentlyContinue | Out-Null
        }}
    }}
}}
"""
    try:
        subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-Command", script],
                       capture_output=True, timeout=15)
        return True
    except:
        return False

# ── GUI ───────────────────────────────────────────────────────
root = tk.Tk()
root.title("MicBoost — by forgot1en")
root.geometry("420x500")
root.resizable(False, False)

DARK  = "#1e1f22"
CARD  = "#2b2d31"
BORD  = "#3a3b3e"
TEXT  = "#dbdee1"
MUTED = "#949ba4"
BLUE  = "#5865f2"
GREEN = "#23a55a"
RED   = "#ed4245"

root.configure(bg=DARK)

def lbl(parent, text, size=13, color=TEXT, bold=False, anchor="w", **kw):
    return tk.Label(parent, text=text, bg=parent["bg"], fg=color,
                    font=("Segoe UI", size, "bold" if bold else "normal"),
                    anchor=anchor, **kw)

def hframe(parent, bg=DARK, **kw):
    return tk.Frame(parent, bg=bg, **kw)

def cframe(parent):
    return tk.Frame(parent, bg=CARD, highlightbackground=BORD, highlightthickness=1)

# Header
hdr = hframe(root, pady=10, padx=16)
hdr.pack(fill="x")
lbl(hdr, "🔊  MicBoost", 16, TEXT, bold=True).pack(side="left")
status_lbl = lbl(hdr, "● Idle", 12, MUTED)
status_lbl.pack(side="right")

# Stats
stats_row = hframe(root, padx=16)
stats_row.pack(fill="x", pady=(0, 8))
for c in range(2): stats_row.columnconfigure(c, weight=1)

def stat_card(parent, val, label_text, col):
    f = tk.Frame(parent, bg=CARD, highlightbackground=BORD, highlightthickness=1)
    f.grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else 6, 0))
    vl = tk.Label(f, text=val, bg=CARD, fg="#fff", font=("Segoe UI", 20, "bold"), anchor="center")
    vl.pack(pady=(12, 0))
    tk.Label(f, text=label_text, bg=CARD, fg=MUTED, font=("Segoe UI", 10), anchor="center").pack(pady=(0, 12))
    return vl

stat_vol   = stat_card(stats_row, "100%",  "Mic Volume",  0)
stat_boost = stat_card(stats_row, "30 dB", "Boost Level", 1)

# Sliders
sl_card = cframe(root)
sl_card.pack(fill="x", padx=16, pady=(0, 8))
sp = hframe(sl_card, CARD, padx=12, pady=12)
sp.pack(fill="x")

vol_var   = tk.IntVar(value=100)
boost_var = tk.IntVar(value=30)

def make_slider_row(parent, label_text, var, from_, to, fmt, on_change):
    row = hframe(parent, CARD)
    row.pack(fill="x", pady=(0, 10))
    top = hframe(row, CARD)
    top.pack(fill="x")
    lbl(top, label_text, 13, TEXT).pack(side="left")
    val_lbl = lbl(top, fmt(var.get()), 13, "#fff", bold=True, anchor="e")
    val_lbl.pack(side="right")
    def _cmd(v):
        val_lbl.config(text=fmt(int(float(v))))
        on_change(int(float(v)))
    tk.Scale(row, variable=var, from_=from_, to=to, orient="horizontal",
             bg=CARD, fg=TEXT, troughcolor=DARK, activebackground=BLUE,
             highlightthickness=0, bd=0, showvalue=False, sliderlength=18,
             command=_cmd).pack(fill="x")

make_slider_row(sp, "Mic Volume", vol_var, 0, 100,
                lambda v: f"{v}%",
                lambda v: stat_vol.config(text=f"{v}%"))

make_slider_row(sp, "Boost (dB)", boost_var, 0, 60,
                lambda v: f"{v} dB",
                lambda v: stat_boost.config(text=f"{v} dB"))

# Info
info = cframe(root)
info.pack(fill="x", padx=16, pady=(0, 8))
inf = hframe(info, CARD, padx=12, pady=10)
inf.pack(fill="x")
lbl(inf, "ℹ  How it works", 11, MUTED, bold=True).pack(anchor="w", pady=(0, 4))
lbl(inf, "Sets your Windows mic volume and boost directly via system API.", 11, MUTED).pack(anchor="w")
lbl(inf, "Works in Discord, games, and every app — system wide.", 11, MUTED).pack(anchor="w")

# Buttons
def apply_settings():
    status_lbl.config(text="● Applying...", fg=MUTED)
    root.update()
    def do():
        v = apply_mic_volume(vol_var.get())
        b = apply_mic_boost_reg(boost_var.get())
        if v or b:
            status_lbl.config(text="● Applied!", fg=GREEN)
        else:
            status_lbl.config(text="● Run as Admin!", fg=RED)
    threading.Thread(target=do, daemon=True).start()

def reset_settings():
    vol_var.set(100)
    boost_var.set(30)
    stat_vol.config(text="100%")
    stat_boost.config(text="30 dB")
    status_lbl.config(text="● Reset", fg=MUTED)

btn_frame = hframe(root, padx=16, pady=4)
btn_frame.pack(fill="x")

tk.Button(btn_frame, text="▶  Apply Boost", bg=BLUE, fg="#fff",
          font=("Segoe UI", 13, "bold"), relief="flat", cursor="hand2",
          activebackground="#4752c4", activeforeground="#fff",
          command=apply_settings, pady=10).pack(fill="x", pady=(0, 6))

tk.Button(btn_frame, text="↺  Reset", bg=CARD, fg=TEXT,
          font=("Segoe UI", 11), relief="flat", cursor="hand2",
          activebackground=BORD, highlightbackground=BORD, highlightthickness=1,
          command=reset_settings, pady=7).pack(fill="x")

tk.Label(root, text="Right click → Run as Administrator for best results",
         bg=DARK, fg=MUTED, font=("Segoe UI", 10)).pack(pady=(8, 2))
tk.Label(root, text="by forgot1en", bg=DARK, fg=BORD, font=("Segoe UI", 9)).pack()

root.mainloop()
