import re
import requests
import tkinter as tk
from tkinter import scrolledtext, messagebox

# -------------------------
# Parser fleksibel
# -------------------------
def ambil_angka(teks):
    teks = re.sub(r'[,|;]', ' ', teks)
    teks = re.sub(r'\.{2,}', ' ', teks)
    parts = teks.split()
    angka=[]
    for p in parts:
        try: angka.append(int(p))
        except: pass
    return angka

def ambil_angka_opsi(teks):
    teks = re.sub(r'[,|;]', ' ', teks)
    teks = re.sub(r'\.{2,}', ' ', teks)
    parts = teks.split()
    angka=[]
    for p in parts:
        try: angka.append(int(p))
        except: pass
    return angka

# -------------------------
# Internal pattern detection
# -------------------------
def beda(arr): return [arr[i+1]-arr[i] for i in range(len(arr)-1)]
def rasio(arr):
    r=[]
    for i in range(len(arr)-1):
        if arr[i]!=0: r.append(arr[i+1]/arr[i])
    return r
def konsisten(lst): return len(lst)>=2 and len(set(round(x,5) for x in lst))==1

def deteksi_pola(arr):
    pola=[]
    d = beda(arr)
    r = rasio(arr)
    if konsisten(d): pola.append(("Aritmatika", d[0]))
    if konsisten(r): pola.append(("Geometri", r[0]))
    if len(d)>=2:
        d2 = beda(d)
        if konsisten(d2): pola.append(("Bertingkat", d2[-1]))
    if all(int(x**0.5)**2 == x for x in arr if x>=0) and len(arr)>=2:
        pola.append(("Kuadrat", None))
    if all(int(round(x**(1/3)))**3 == x for x in arr) and len(arr)>=2:
        pola.append(("Kubik", None))
    return pola

def prediksi_internal(arr, pola):
    hasil=[]
    penjelasan=[]
    for p in pola:
        nama,nilai=p
        if nama=="Aritmatika":
            hasil.append(arr[-1]+nilai)
            penjelasan.append(f"Aritmatika (beda {nilai})")
        elif nama=="Geometri":
            hasil.append(round(arr[-1]*nilai))
            penjelasan.append(f"Geometri (rasio {round(nilai,3)})")
        elif nama=="Bertingkat":
            d = beda(arr)
            hasil.append(arr[-1]+d[-1]+nilai)
            penjelasan.append(f"Bertingkat (selisih berubah {nilai})")
        elif nama=="Kuadrat":
            n=int(arr[-1]**0.5)+1
            hasil.append(n*n)
            penjelasan.append("Kuadrat")
        elif nama=="Kubik":
            n=round(arr[-1]**(1/3))+1
            hasil.append(n**3)
            penjelasan.append("Kubik")
    return hasil,penjelasan

# -------------------------
# OEIS query
# -------------------------
def query_oeis(sequence):
    q = ",".join(str(x) for x in sequence)
    url = f"https://oeis.org/search?q={q}&fmt=json"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        results = data.get("results", [])
        if not results: return None
        best = results[0]
        seqname = best.get("name","")
        seqdata = best.get("data","")
        oeis_list = [int(x) for x in seqdata.split(",") if x.strip().isdigit()]
        return {"name": seqname, "sequence": oeis_list}
    except:
        return None

def prediksi_oeis(arr):
    oeis = query_oeis(arr)
    if not oeis: return None, []
    seq = oeis["sequence"]
    name = oeis["name"]
    try:
        idx = seq.index(arr[-1])
        next_val = seq[idx+1]
        return next_val, [f"OEIS: {name} → next = {next_val}"]
    except:
        return None, [f"OEIS match found: {name}, tetapi tidak bisa prediksi langsung"]

# -------------------------
# Engine utama
# -------------------------
def engine_cpns_smart(arr, opsi_angka_list=None):
    pembahasan=[]
    pola = deteksi_pola(arr)
    hasil_int, pen_int = prediksi_internal(arr, pola)
    if pen_int: pembahasan += ["Internal: "+x for x in pen_int]
    if hasil_int: hasil = hasil_int
    else:
        nxt_oeis, pen_oeis = prediksi_oeis(arr)
        if nxt_oeis is not None:
            hasil = [nxt_oeis]
            pembahasan += pen_oeis
        else:
            if len(arr)>=2:
                diff = arr[-1]-arr[-2]
                hasil = [arr[-1]+diff]
                pembahasan.append(f"Fallback: selisih terakhir {diff}")
            else:
                hasil=[]
    # Cocokkan opsi ganda jika ada
    final = hasil[0] if hasil else None
    if opsi_angka_list:
        scores = {}
        for k, ops in opsi_angka_list.items():
            score = sum(1 for x in hasil if x in ops)
            scores[k]=score
        best = max(scores, key=lambda m: (scores[m], -min((abs(x-ops[0]) for x in hasil for ops in [opsi_angka_list[m]]))))
        final = best
    return final, pembahasan

# =========================
# GUI
# =========================
root = tk.Tk()
root.title("Smart CPNS Deret Angka (OEIS + Internal)")

tk.Label(root, text="Masukkan soal deret:", font=("Arial",11,"bold")).pack()
entry_soal = tk.Entry(root, width=60)
entry_soal.pack(pady=5)

tk.Label(root, text="Pilihan ganda opsional (A–E):", font=("Arial",11,"bold")).pack()
opsi={}
for h in ["A","B","C","D","E"]:
    frame=tk.Frame(root); frame.pack()
    tk.Label(frame, text=h, width=2).pack(side=tk.LEFT)
    opsi[h]=tk.Entry(frame, width=15); opsi[h].pack(side=tk.LEFT)

btn=tk.Button(root, text="ANALISIS", command=lambda: run_analyze())
btn.pack(pady=8)

text_hasil = scrolledtext.ScrolledText(root, height=20)
text_hasil.pack()

def run_analyze():
    arr = ambil_angka(entry_soal.get())
    if not arr:
        messagebox.showwarning("Error","Tidak terdeteksi angka")
        return
    ops = {k:v.get() for k,v in opsi.items() if v.get().strip()}
    opsi_list = {k: ambil_angka_opsi(v) for k,v in ops.items()}
    jawaban, pemb = engine_cpns_smart(arr, opsi_list if opsi_list else None)
    text_hasil.delete("1.0", tk.END)
    text_hasil.insert(tk.END, "📘 PEMBAHASAN POLA:\n")
    for p in pemb:
        text_hasil.insert(tk.END, "- "+p+"\n")
    text_hasil.insert(tk.END, f"\n🔮 JAWABAN FINAL: {jawaban}\n")
    if opsi_list:
        text_hasil.insert(tk.END, "\nPilihan:\n")
        for k,v in opsi_list.items():
            tag = "✅" if jawaban in v else "❌"
            text_hasil.insert(tk.END, f"{k}. {ops[k]} {tag}\n")

root.mainloop()
