from tkinter import *
from tkinter import ttk
from addictions import *
from tkinter.messagebox import showinfo

root=Tk()
root.title("Электрические цепи")
root.geometry("1200x700")

options=[2,3,4,5]
counter=0
first_point=60
basic_len=40
dr_lev=100
rezis=[]
entrys=[]
fin_rezs=[]
rez_names=[]
u=0

class Rezister:
    def __init__(self, canvas, rezistance, x0, y0, name, i):
        self.rezist=rezistance
        self.canvas=canvas
        self.x0=x0
        self.y0=y0
        self.name=name
        self.i=i
        name=canvas.create_rectangle(x0, y0, x0+80, y0-30, fill="#41454E", outline="#000000",
                                 activefill="#5661CA")
        canvas.create_text(x0+40, y0-15, text=str(self.rezist)+" Ом",
                            fill="#BDBDBD")

    def __str__(self):
        return f"Резистор с сопротивлением {self.rezist} Ом"

class Wire:
    def __init__(self, canvas, x0, y0, lenght):
         self.canvas=canvas
         self.x0=x0
         self.y0=y0
         self.len=lenght
         canvas.create_line(x0, y0, x0+self.len, y0, fill="#000000", width=3)

def count():
    final_rezistanse=0
    for rezs in fin_rezs:
        final_rezistanse+=rezs
    global u
    u=float(en2.get())
    i=round((u/final_rezistanse), 3)
    lab_fin.config(text=f"I={i}, U={u}, R={final_rezistanse}")

def count2(event):
    for rez in rez_names:
        if rez.x0<=event.x<=rez.x0+80 and rez.y0-30<=event.y<=rez.y0:
            ids=rez.name
            r=float(rez.rezist)
    if ids=="seq":
        final_rezistanse=0
        for rezs in fin_rezs:
            final_rezistanse+=rezs
        i=u/final_rezistanse
        ur=i*r
        showinfo(title="Информация", message=f"U={ur}, I={round(i, 2)}, R={r}")
    else:
        rp_rezs=[]
        if not dr_lev-15<=event.y<=dr_lev+15:
            for rez in rez_names:
                if rez.x0<=event.x<=rez.x0+80 and rez.y0-30<=dr_lev<=rez.y0:
                    rp=float(rez.rezist)
                    rp_rezs.append(rp)
                    y=dr_lev
                    while y < dr_lev+35*rez.i:
                        y+=35
                        for rez in rez_names:
                            if rez.x0<=event.x<=rez.x0+80 and rez.y0-30<=y<=rez.y0:
                                rp=float(rez.rezist)
                                rp_rezs.append(rp)
        else:
            for rez in rez_names:
                if rez.x0<=event.x<=rez.x0+80 and rez.y0-30<=event.y<=rez.y0:
                    rp=float(rez.rezist)
                    rp_rezs.append(rp)
            y=event.y
            while y<event.y+35*rez.i:
                y+=35
                for rez in rez_names:
                    if rez.x0<=event.x<=rez.x0+80 and rez.y0-30<=y<=rez.y0:
                        rp=float(rez.rezist)
                        rp_rezs.append(rp)                    
        x=0
        for rez in rp_rezs:
            x+=(1/float(rez))
        par_rezistance=round((1/x), 2)
        final_rezistanse=0
        for rezs in fin_rezs:
            final_rezistanse+=rezs
        i=u/final_rezistanse
        up=i*par_rezistance
        ip=up/r
        showinfo(title="Информация", message=f"U={up}, I={round(ip, 2)}, R={r}")

def creator():
    global counter
    rezi=int(en1.get())
    r1=Rezister(canvas=canvas, rezistance=rezi, x0=first_point+20+(80+basic_len)*counter, y0=dr_lev+15, name="seq", i=1)
    fin_rezs.append(rezi)
    rez_names.append(r1)
    counter+=1
    if counter==1:
        Wire(canvas=canvas, x0=first_point+20+80, y0=dr_lev, lenght=basic_len)
    else:
        Wire(canvas=canvas, x0=first_point+20+80+(basic_len+80)*(counter-1), y0=dr_lev, lenght=basic_len)

def selected(event):
    entrys.clear()
    window = Toplevel(root)
    window.title("Сопротивления")
    window.geometry("250x250")
    for i in range(int(com.get())):
        lab=ttk.Label(window, text=f"Сопротивление резистора {i+1}:")
        lab.pack()
        en=ttk.Entry(window)
        en.pack()
        entrys.append(en)
    coll=ttk.Button(window, text="Создать", command=creator2)
    coll.pack()

def creator2():
    selection=int(com.get())
    rezis.clear()
    parr_rezs=[]
    for i in range(selection):
        rezis.append(entrys[i].get())
    global counter
    if counter==0:
        canvas.create_line(first_point+20, dr_lev, first_point+20, dr_lev+35*(selection-1), fill="#000000", width=3)
        for i in range(selection):
            Wire(canvas=canvas, x0=first_point+20, y0=dr_lev+35*i, lenght=10)
            r2=Rezister(canvas=canvas, rezistance=rezis[i], x0=first_point+20+10, y0=dr_lev+35*i+15, name="parr", i=i+1)
            parr_rezs.append(rezis[i])
            rez_names.append(r2)
            Wire(canvas=canvas, x0=first_point+20+10+80, y0=dr_lev+35*i, lenght=10)
        canvas.create_line(first_point+20+100, dr_lev, first_point+20+100, dr_lev+35*(selection-1), fill="#000000", width=3)
        Wire(canvas=canvas, x0=first_point+20+10+80, y0=dr_lev, lenght=basic_len)
    else:
        canvas.create_line(first_point+20+120*counter, dr_lev, first_point+20+120*counter, dr_lev+35*(selection-1), fill="#000000", width=3)
        for i in range(selection):
            Wire(canvas=canvas, x0=first_point+20+120*counter, y0=dr_lev+35*i, lenght=10)
            r2=Rezister(canvas=canvas, rezistance=rezis[i], x0=first_point+20+10+120*counter, y0=dr_lev+35*i+15, name="parr", i=i+1)
            parr_rezs.append(rezis[i])
            rez_names.append(r2)
            Wire(canvas=canvas, x0=first_point+20+120*counter+10+80, y0=dr_lev+35*i, lenght=10)
        canvas.create_line(first_point+20+120*counter+100, dr_lev, first_point+20+120*counter+100, dr_lev+35*(selection-1), fill="#000000", width=3)
        Wire(canvas=canvas, x0=first_point+20+120*counter+10+80, y0=dr_lev, lenght=basic_len)
    counter+=1
    x=0
    for rez in parr_rezs:
        x+=(1/float(rez))
    par_rezistance=round((1/x), 2)
    fin_rezs.append(par_rezistance)

def clear():
    canvas.delete("all")
    lab_fin.config(text="")
    global counter
    counter=0
    fin_rezs.clear()
    Wire(canvas=canvas, x0=20, y0=dr_lev, lenght=first_point)


lab1=ttk.Label(text="Сопротивление резистора(если больше 1, то не писать):")
lab1.pack(anchor=NW)
en1=ttk.Entry()
en1.pack(anchor=NW)
lab2=ttk.Label(text="Кол-во:")
lab2.pack(anchor=NW)
com=ttk.Combobox(values=options)
com.pack(anchor=NW)
com.bind("<<ComboboxSelected>>", selected)
creat=ttk.Button(text="Создать", command=creator)
creat.pack(anchor=NW)
lab3=ttk.Label(text="Введите напряжение на клеммах источника")
lab3.pack(anchor=NW)
en2=ttk.Entry()
en2.pack(anchor=NW)
clearbtn=ttk.Button(text="Очистить", command=clear)
clearbtn.pack(anchor=NW)
voltagebtn=ttk.Button(text="Расчитать", command=count)
voltagebtn.pack()
lab_fin=ttk.Label(text="")
lab_fin.pack()

canvas=Canvas(bg="white", width=1200, height=500)
canvas.pack(anchor=S)

canvas.bind("<Button-1>", count2)

Wire(canvas=canvas, x0=20, y0=dr_lev, lenght=first_point)

root.mainloop()