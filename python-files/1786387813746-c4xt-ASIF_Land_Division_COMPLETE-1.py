# -*- coding: utf-8 -*-
"""
ASIF LAND DIVISION SYSTEM - SINGLE FILE OFFLINE EDITION
Rana Rashid Ali Zaheer Enterprises
Proprietor: Mohammad Asif Iqbal
Mobile: 0325 6050004 | WhatsApp: 0340 6050004

Single-file desktop application.
Default login: admin / 1234
All operational data is stored locally in SQLite beside this program.
"""

import sqlite3, tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from datetime import datetime
from pathlib import Path
import html, webbrowser, shutil, json

APP = "ASIF LAND DIVISION SYSTEM"
BASE = Path(__file__).resolve().parent
DB = BASE / "ASIF_Land_Database.db"
MARLA_SQFT = 272.25

def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    c = conn()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(
      id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE,
      password TEXT, active INTEGER DEFAULT 1);
    CREATE TABLE IF NOT EXISTS owners(
      id INTEGER PRIMARY KEY AUTOINCREMENT, serial INTEGER UNIQUE,
      entry_date TEXT, entry_time TEXT, name TEXT, cnic TEXT, mobile TEXT,
      district TEXT, tehsil TEXT, village TEXT, khewat TEXT, notes TEXT);
    CREATE TABLE IF NOT EXISTS khasra(
      id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER,
      khasra_no TEXT, north REAL DEFAULT 0, south REAL DEFAULT 0,
      east REAL DEFAULT 0, west REAL DEFAULT 0, length REAL DEFAULT 0,
      width REAL DEFAULT 0, area_sqft REAL DEFAULT 0, sort_order INTEGER);
    CREATE TABLE IF NOT EXISTS boundary(
      id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER,
      direction TEXT, kind TEXT, length REAL DEFAULT 0,
      width REAL DEFAULT 0, area_sqft REAL DEFAULT 0);
    CREATE TABLE IF NOT EXISTS gps(
      id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER,
      point_no INTEGER, latitude REAL, longitude REAL);
    CREATE TABLE IF NOT EXISTS heirs(
      id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER,
      name TEXT, relation TEXT, share REAL DEFAULT 0, share_sqft REAL DEFAULT 0);
    CREATE TABLE IF NOT EXISTS documents(
      id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER,
      file_path TEXT, file_type TEXT, description TEXT);
    CREATE TABLE IF NOT EXISTS settings(
      name TEXT PRIMARY KEY, value TEXT);
    """)
    if not c.execute("SELECT 1 FROM users LIMIT 1").fetchone():
        c.execute("INSERT INTO users(username,password) VALUES('admin','1234')")
    c.execute("INSERT OR IGNORE INTO settings(name,value) VALUES('MarlaSqFt','272.25')")
    c.commit(); c.close()

def n(v):
    try: return float(v or 0)
    except: return 0.0

def next_serial():
    c=conn(); x=c.execute("SELECT COALESCE(MAX(serial),0)+1 n FROM owners").fetchone()["n"]; c.close(); return x

def area_units(sqft):
    marla_sqft=n(conn().execute("SELECT value FROM settings WHERE name='MarlaSqFt'").fetchone()["value"] or MARLA_SQFT)
    if marla_sqft<=0: marla_sqft=MARLA_SQFT
    marla=sqft/marla_sqft
    return sqft, marla, marla/20

class Login(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP); self.geometry("620x460"); self.resizable(False,False)
        tk.Label(self,text="RANA RASHID ALI ZAHEER ENTERPRISES",
                 font=("Arial",19,"bold")).pack(pady=(55,6))
        tk.Label(self,text="Proprietor: Mohammad Asif Iqbal",
                 font=("Arial",12)).pack()
        tk.Label(self,text="Mobile: 0325 6050004   |   WhatsApp: 0340 6050004").pack(pady=4)
        f=tk.Frame(self); f.pack(pady=35)
        tk.Label(f,text="User Name").grid(row=0,column=0,padx=8,pady=8)
        self.u=tk.Entry(f,width=30); self.u.grid(row=0,column=1)
        tk.Label(f,text="Password").grid(row=1,column=0,padx=8,pady=8)
        self.p=tk.Entry(f,width=30,show="*"); self.p.grid(row=1,column=1)
        tk.Button(self,text="LOGIN",width=20,height=2,command=self.login).pack()
        tk.Label(self,text="Offline • Local Database",fg="gray").pack(side="bottom",pady=20)
        self.bind("<Return>",lambda e:self.login())
    def login(self):
        c=conn(); ok=c.execute(
            "SELECT 1 FROM users WHERE username=? AND password=? AND active=1",
            (self.u.get(),self.p.get())).fetchone(); c.close()
        if ok:
            self.destroy(); Main().mainloop()
        else: messagebox.showerror("Login","Invalid username or password.")

class Main(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP); self.geometry("1280x800")
        self.owner_id=None; self.krows=[]
        self.make_ui(); self.new_record()

    def make_ui(self):
        tk.Label(self,text=APP,font=("Arial",20,"bold")).pack(pady=6)
        bar=tk.Frame(self); bar.pack(fill="x",padx=8,pady=6)
        buttons=[
            ("New",self.new_record),("Save",self.save),("Search",self.search),
            ("Database",self.database),("Print A4",self.print_a4),
            ("Save PDF/HTML",self.save_report),("Virasat",self.virasat),
            ("Backup",self.backup),("Settings",self.settings),("Exit",self.destroy)]
        for text,cmd in buttons:
            tk.Button(bar,text=text,width=12,command=cmd).pack(side="left",padx=2)
        nb=ttk.Notebook(self); nb.pack(fill="both",expand=True,padx=8)
        self.owner_tab=tk.Frame(nb); self.kh_tab=tk.Frame(nb)
        self.gps_tab=tk.Frame(nb); self.bound_tab=tk.Frame(nb); self.docs_tab=tk.Frame(nb)
        nb.add(self.owner_tab,text="مالک کی تفصیل"); nb.add(self.kh_tab,text="خسرہ")
        nb.add(self.gps_tab,text="GPS"); nb.add(self.bound_tab,text="حدود / گلی")
        nb.add(self.docs_tab,text="Documents")
        self.fields={}
        labels=[("Serial","serial"),("Date","date"),("Time","time"),
                ("Name","name"),("CNIC","cnic"),("Mobile","mobile"),
                ("District","district"),("Tehsil","tehsil"),
                ("Village","village"),("Khewat","khewat")]
        for i,(lab,key) in enumerate(labels):
            r=(i//2)*2; col=(i%2)*2
            tk.Label(self.owner_tab,text=lab).grid(row=r,column=col,padx=8,pady=4,sticky="e")
            e=tk.Entry(self.owner_tab,width=36); e.grid(row=r,column=col+1,padx=8,pady=4)
            self.fields[key]=e
        tk.Label(self.owner_tab,text="Notes").grid(row=10,column=0,padx=8,sticky="ne")
        self.notes=tk.Text(self.owner_tab,width=82,height=7); self.notes.grid(row=10,column=1,columnspan=3,pady=8)
        tk.Button(self.owner_tab,text="Calculate Total",command=self.update_total).grid(row=11,column=1,pady=5)

        top=tk.Frame(self.kh_tab); top.pack(fill="x")
        tk.Button(top,text="+ Add Khasra",command=self.add_khasra).pack(side="left",padx=5,pady=5)
        tk.Label(top,text="Length × Width = Area (sq.ft)").pack(side="left")
        self.kh_canvas=tk.Canvas(self.kh_tab)
        sb=ttk.Scrollbar(self.kh_tab,orient="vertical",command=self.kh_canvas.yview)
        self.kh_frame=tk.Frame(self.kh_canvas)
        self.kh_canvas.create_window((0,0),window=self.kh_frame,anchor="nw")
        self.kh_canvas.configure(yscrollcommand=sb.set)
        self.kh_canvas.pack(side="left",fill="both",expand=True); sb.pack(side="right",fill="y")

        self.gps_tree=ttk.Treeview(self.gps_tab,columns=("p","lat","lon"),show="headings")
        for c,h in zip(("p","lat","lon"),("Point","Latitude","Longitude")):
            self.gps_tree.heading(c,text=h); self.gps_tree.column(c,width=220)
        self.gps_tree.pack(fill="both",expand=True,padx=10,pady=10)
        tk.Button(self.gps_tab,text="Enter 4 Corner Points",command=self.gps_edit).pack(pady=5)
        tk.Button(self.gps_tab,text="Open Polygon in Google Maps",command=self.open_map).pack(pady=5)

        self.btree=ttk.Treeview(self.bound_tab,columns=("dir","kind","len","width","area"),show="headings")
        for c,h in zip(("dir","kind","len","width","area"),("Direction","Type","Length ft","Width ft","Half Area sq.ft")):
            self.btree.heading(c,text=h); self.btree.column(c,width=170)
        self.btree.pack(fill="both",expand=True,padx=10,pady=10)
        tk.Button(self.bound_tab,text="+ Add Boundary / Road",command=self.bound_add).pack(pady=5)

        self.doclist=tk.Listbox(self.docs_tab); self.doclist.pack(fill="both",expand=True,padx=10,pady=10)
        tk.Button(self.docs_tab,text="Add JPG / DWG / PDF",command=self.add_document).pack(pady=5)

        self.total=tk.Label(self,text="Total: 0.00 sq.ft | 0.00 Marla | 0.00 Kanal",
                            font=("Arial",12,"bold")); self.total.pack(pady=5)

    def new_record(self):
        self.owner_id=None
        for e in self.fields.values(): e.delete(0,"end")
        self.fields["serial"].insert(0,str(next_serial()))
        now=datetime.now()
        self.fields["date"].insert(0,now.strftime("%Y-%m-%d"))
        self.fields["time"].insert(0,now.strftime("%H:%M:%S"))
        self.notes.delete("1.0","end")
        for row,*_ in self.krows: row.destroy()
        self.krows=[]; self.add_khasra(); self.add_khasra()
        for t in (self.gps_tree,self.btree):
            for x in t.get_children(): t.delete(x)
        self.doclist.delete(0,"end"); self.update_total()

    def add_khasra(self, vals=None):
        row=tk.Frame(self.kh_frame,bd=1,relief="groove"); row.pack(fill="x",pady=2)
        es=[]
        for lab,w in [("Khasra",14),("Length",10),("Width",10)]:
            tk.Label(row,text=lab).pack(side="left",padx=2)
            e=tk.Entry(row,width=w); e.pack(side="left",padx=2); es.append(e)
        area=tk.Label(row,text="Area 0.00"); area.pack(side="left",padx=8)
        units=tk.Label(row,text="0.00 M / 0.00 K"); units.pack(side="left",padx=8)
        tk.Button(row,text="Remove",command=lambda:self.remove_khasra(row)).pack(side="right",padx=5)
        for e in es[1:]: e.bind("<KeyRelease>",lambda ev:self.update_total())
        if vals:
            for e,v in zip(es,vals): e.insert(0,str(v))
        self.krows.append((row,es,area,units)); self.update_total()

    def remove_khasra(self,row):
        self.krows=[x for x in self.krows if x[0] is not row]
        row.destroy(); self.update_total()

    def update_total(self):
        total=0
        for _,es,lab,units in self.krows:
            a=n(es[1].get())*n(es[2].get()); total+=a
            _,m,k=area_units(a)
            lab.config(text=f"Area {a:,.2f}")
            units.config(text=f"{m:,.2f} M / {k:,.2f} K")
        _,m,k=area_units(total)
        self.total.config(text=f"Total: {total:,.2f} sq.ft | {m:,.2f} Marla | {k:,.2f} Kanal")

    def save(self):
        c=conn(); v={k:e.get() for k,e in self.fields.items()}
        if not v["name"].strip():
            c.close(); messagebox.showwarning("Save","مالک کا نام درج کریں."); return
        if self.owner_id:
            c.execute("""UPDATE owners SET serial=?,entry_date=?,entry_time=?,name=?,cnic=?,mobile=?,
                district=?,tehsil=?,village=?,khewat=?,notes=? WHERE id=?""",
                (v["serial"],v["date"],v["time"],v["name"],v["cnic"],v["mobile"],v["district"],
                 v["tehsil"],v["village"],v["khewat"],self.notes.get("1.0","end").strip(),self.owner_id))
            c.execute("DELETE FROM khasra WHERE owner_id=?",(self.owner_id,))
        else:
            cur=c.execute("""INSERT INTO owners(serial,entry_date,entry_time,name,cnic,mobile,district,tehsil,village,khewat,notes)
                VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (v["serial"],v["date"],v["time"],v["name"],v["cnic"],v["mobile"],v["district"],
                 v["tehsil"],v["village"],v["khewat"],self.notes.get("1.0","end").strip()))
            self.owner_id=cur.lastrowid
        for i,(_,es,*_) in enumerate(self.krows,1):
            c.execute("""INSERT INTO khasra(owner_id,khasra_no,length,width,area_sqft,sort_order)
                VALUES(?,?,?,?,?,?)""",
                (self.owner_id,es[0].get(),n(es[1].get()),n(es[2].get()),
                 n(es[1].get())*n(es[2].get()),i))
        c.commit(); c.close()
        messagebox.showinfo("Save","Record saved in the local offline database.")

    def search(self):
        q=simpledialog.askstring("Search","Name or Serial:",parent=self)
        if not q:return
        c=conn(); r=c.execute("""SELECT * FROM owners
            WHERE name LIKE ? OR CAST(serial AS TEXT)=? ORDER BY id DESC LIMIT 1""",(f"%{q}%",q)).fetchone()
        if not r: c.close(); messagebox.showinfo("Search","Record not found."); return
        self.owner_id=r["id"]
        for k,e in self.fields.items():
            e.delete(0,"end"); e.insert(0,str(r[k] or ""))
        self.notes.delete("1.0","end"); self.notes.insert("1.0",r["notes"] or "")
        for row,*_ in self.krows: row.destroy()
        self.krows=[]
        for x in c.execute("SELECT khasra_no,length,width FROM khasra WHERE owner_id=? ORDER BY sort_order",(self.owner_id,)):
            self.add_khasra((x["khasra_no"],x["length"],x["width"]))
        c.close(); self.update_total()

    def database(self):
        w=tk.Toplevel(self); w.title("Local Database"); w.geometry("950x520")
        tr=ttk.Treeview(w,columns=("id","serial","name","cnic","district","tehsil","village"),show="headings")
        for c,h in zip(("id","serial","name","cnic","district","tehsil","village"),
                       ("ID","Serial","Name","CNIC","District","Tehsil","Village")):
            tr.heading(c,text=h); tr.column(c,width=120)
        tr.pack(fill="both",expand=True)
        c=conn()
        for r in c.execute("SELECT id,serial,name,cnic,district,tehsil,village FROM owners ORDER BY id DESC"):
            tr.insert("", "end",values=tuple(r))
        c.close()

    def gps_edit(self):
        w=tk.Toplevel(self); w.title("GPS Corner Points"); w.geometry("600x350")
        es=[]
        for i in range(4):
            tk.Label(w,text=f"Point {i+1} Latitude").grid(row=i,column=0,padx=6,pady=6)
            a=tk.Entry(w,width=22); a.grid(row=i,column=1)
            tk.Label(w,text="Longitude").grid(row=i,column=2,padx=6)
            b=tk.Entry(w,width=22); b.grid(row=i,column=3); es.append((a,b))
        def ok():
            for x in self.gps_tree.get_children(): self.gps_tree.delete(x)
            for i,(a,b) in enumerate(es,1):
                self.gps_tree.insert("", "end",values=(i,a.get(),b.get()))
            w.destroy()
        tk.Button(w,text="Save Points",command=ok).grid(row=5,column=0,columnspan=4,pady=12)

    def open_map(self):
        pts=[]
        for x in self.gps_tree.get_children():
            v=self.gps_tree.item(x)["values"]
            try: pts.append((float(v[1]),float(v[2])))
            except: pass
        if not pts:
            messagebox.showwarning("Map","Enter GPS points first."); return
        # Google Maps directions-style path
        path="/".join(f"{a},{b}" for a,b in pts+[pts[0]])
        webbrowser.open("https://www.google.com/maps/dir/"+path)

    def bound_add(self):
        w=tk.Toplevel(self); w.title("Boundary / Road"); w.geometry("450x300")
        es=[]
        for i,l in enumerate(["Direction","Type","Length ft","Width ft"]):
            tk.Label(w,text=l).grid(row=i,column=0,padx=8,pady=7)
            e=tk.Entry(w,width=30); e.grid(row=i,column=1); es.append(e)
        def add():
            d,k,L,W=es[0].get(),es[1].get(),n(es[2].get()),n(es[3].get())
            a=L*W/2
            self.btree.insert("", "end",values=(d,k,f"{L:.2f}",f"{W:.2f}",f"{a:.2f}"))
            w.destroy()
        tk.Button(w,text="Add",command=add).grid(row=5,column=0,columnspan=2,pady=10)

    def add_document(self):
        files=filedialog.askopenfilenames(filetypes=[("Documents","*.jpg *.jpeg *.png *.pdf *.dwg"),("All files","*.*")])
        for f in files: self.doclist.insert("end",f)

    def report_html(self):
        v={k:e.get() for k,e in self.fields.items()}
        rows=""; total=0
        for i,(_,es,*_) in enumerate(self.krows,1):
            a=n(es[1].get())*n(es[2].get()); total+=a
            rows+=f"<tr><td>{i}</td><td>{html.escape(es[0].get())}</td><td>{n(es[1].get()):,.2f}</td><td>{n(es[2].get()):,.2f}</td><td>{a:,.2f}</td></tr>"
        _,m,k=area_units(total)
        gps=""
        for x in self.gps_tree.get_children():
            vv=self.gps_tree.item(x)["values"]; gps+=f"<tr><td>{vv[0]}</td><td>{html.escape(str(vv[1]))}</td><td>{html.escape(str(vv[2]))}</td></tr>"
        return f"""<!doctype html><html><head><meta charset="utf-8">
        <style>@page{{size:A4;margin:15mm}}body{{font-family:Arial,sans-serif;font-size:12pt}}
        table{{width:100%;border-collapse:collapse;margin:10px 0}}th,td{{border:1px solid #555;padding:6px}}
        h2{{text-align:center}}</style></head><body>
        <h2>Land Division Record</h2>
        <p>Serial: {html.escape(v['serial'])} &nbsp; Date: {html.escape(v['date'])} &nbsp; Time: {html.escape(v['time'])}</p>
        <p>Name: {html.escape(v['name'])}<br>CNIC: {html.escape(v['cnic'])}<br>Mobile: {html.escape(v['mobile'])}<br>
        District: {html.escape(v['district'])} &nbsp; Tehsil: {html.escape(v['tehsil'])}<br>
        Village: {html.escape(v['village'])} &nbsp; Khewat: {html.escape(v['khewat'])}</p>
        <table><tr><th>No.</th><th>Khasra</th><th>Length ft</th><th>Width ft</th><th>Area sq.ft</th></tr>{rows}</table>
        <p><b>Total:</b> {total:,.2f} sq.ft &nbsp; {m:,.2f} Marla &nbsp; {k:,.2f} Kanal</p>
        <h3>GPS Points</h3><table><tr><th>Point</th><th>Latitude</th><th>Longitude</th></tr>{gps}</table>
        <br><br><table><tr><td>Patwari Name / Signature</td><td>Qanungo Name / Signature</td><td>Tehsildar Name / Signature</td></tr>
        <tr><td><br><br><br></td><td></td><td></td></tr></table>
        </body></html>"""

    def save_report(self):
        p=filedialog.asksaveasfilename(defaultextension=".html",filetypes=[("A4 Report","*.html")])
        if p:
            Path(p).write_text(self.report_html(),encoding="utf-8")
            webbrowser.open(Path(p).as_uri())

    def print_a4(self):
        self.save_report()

    def backup(self):
        p=filedialog.asksaveasfilename(defaultextension=".db",filetypes=[("Database","*.db")])
        if p: shutil.copy2(DB,p); messagebox.showinfo("Backup","Local database backup saved.")

    def settings(self):
        c=conn(); current=c.execute("SELECT value FROM settings WHERE name='MarlaSqFt'").fetchone()["value"]; c.close()
        v=simpledialog.askfloat("Settings","Square feet per Marla:",initialvalue=float(current),parent=self)
        if v and v>0:
            c=conn(); c.execute("UPDATE settings SET value=? WHERE name='MarlaSqFt'",(str(v),)); c.commit(); c.close()
            messagebox.showinfo("Settings","Setting saved.")

    def virasat(self):
        w=tk.Toplevel(self); w.title("Virasat Taqseem Calculator"); w.geometry("800x520")
        tk.Label(w,text="Total Land (sq.ft)").pack(pady=5)
        total=tk.Entry(w,width=25); total.pack()
        tr=ttk.Treeview(w,columns=("name","relation","share","area"),show="headings")
        for c,h in zip(("name","relation","share","area"),("Name","Relation","Share %","Share sq.ft")):
            tr.heading(c,text=h); tr.column(c,width=180)
        tr.pack(fill="both",expand=True,pady=10)
        def add():
            name=simpledialog.askstring("Heir","Name",parent=w)
            rel=simpledialog.askstring("Heir","Relation",parent=w)
            share=simpledialog.askfloat("Heir","Share %",parent=w)
            if name and share is not None:
                tr.insert("", "end",values=(name,rel or "",f"{share:.2f}",f"{n(total.get())*share/100:.2f}"))
        tk.Button(w,text="+ Add Heir",command=add).pack(pady=5)

init_db()
if __name__=="__main__":
    Login().mainloop()
