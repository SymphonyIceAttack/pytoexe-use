import tkinter as tk
import asyncio
from tkinter import ttk, messagebox, Menu

pbl = [0, 0, 0]
pbl2 = []
lstp = [2, 7, 13, 16]
lstn = [-3, -6, -9, -15]
newlst = []

#########################################################################

def closest(lst, K):
    return lst[min(range(len(lst)), key = lambda i: abs(lst[i]-K))]

def lo():
    global pbl
    pbl[2] = pbl[1]
    pbl[1] = pbl[0]
    pbl[0] = -3
    update_label()

def lt():
    global pbl
    pbl[2] = pbl[1]
    pbl[1] = pbl[0]
    pbl[0] = -6
    update_label()

def lth():
    global pbl
    pbl[2] = pbl[1]
    pbl[1] = pbl[0]
    pbl[0] = -9
    update_label()

def lf():
    global pbl
    pbl[2] = pbl[1]
    pbl[1] = pbl[0]
    pbl[0] = -15
    update_label()

def ro():
    global pbl
    pbl[2] = pbl[1]
    pbl[1] = pbl[0]
    pbl[0] = 2
    update_label()

def rt():
    global pbl
    pbl[2] = pbl[1]
    pbl[1] = pbl[0]
    pbl[0] = 7
    update_label()

def rth():
    global pbl
    pbl[2] = pbl[1]
    pbl[1] = pbl[0]
    pbl[0] = 13
    update_label()

def rf():
    global pbl
    pbl[2] = pbl[1]
    pbl[1] = pbl[0]
    pbl[0] = 16
    update_label()

def lo2():
    global pbl2
    pbl2.append(-3)
    update_label()

def lt2():
    global pbl2
    pbl2.append(-6)
    update_label()

def lth2():
    global pbl2
    pbl2.append(-9)
    update_label()

def lf2():
    global pbl2
    pbl2.append(-15)
    update_label()

def ro2():
    global pbl2
    pbl2.append(2)
    update_label()

def rt2():
    global pbl2
    pbl2.append(7)
    update_label()

def rth2():
    global pbl2
    pbl2.append(13)
    update_label()

def rf2():
    global pbl2
    pbl2.append(16)
    update_label()

def reset():
    global pbl2
    pbl2 = []

def update_label():
   global pressedL
   pressedL.config(text = pbl)

def calce():
    global pbl2
    global pressedL2
    coord = sum(pbl2)
    pressedL2.config(text = f"The end coordinate is {coord}")
    

def calculatepath():
    global resultP
    global pbl
    global cente
    result = 0
    newlst = []
    a = pbl[2]
    b = pbl[1]
    c = pbl[0]
    cn = cente.get()
    try:
        cn = int(cn)
        bf = (((cn-a)-b)-c)
        fs = 0
    except:
        resultP.config(text = "Error! Put end coordinate in the entrybox!")
    
    while fs != bf:
        x = bf - fs
        if x > 0:
            dif = closest(lstp, x)
            fs += dif
            newlst.append(dif)
        if x < 0:
            dif = closest(lstn, x)
            fs += dif
            newlst.append(dif)

    newlst.append(c)
    newlst.append(b)
    newlst.append(a)

    
    for i in range(len(newlst)):
        result = result + newlst[i]
        if newlst[i] == 2:
            newlst[i] = 'Штамповать'
        if newlst[i] == 7:
            newlst[i] = 'Изогнуть'
        if newlst[i] == 13:
            newlst[i] = 'Обжать'
        if newlst[i] == 16:
            newlst[i] = 'Усадить'
        if newlst[i] == -3:
            newlst[i] = 'Слабо ударить'
        if newlst[i] == -6:
            newlst[i] = 'Ударить'
        if newlst[i] == -9:
            newlst[i] = 'Сильно ударить'
        if newlst[i] == -15:
            newlst[i] = 'Протянуть'
    resultP.config(text = newlst)

def about():
    tk.messagebox.showinfo(title='About', message='''This is a program to help with anvil minigame in TerraFirmaCraft, a Minecraft mod made by Robert "Bioxx" Anthony, Amanda "Kittychanley" Halek, and others.

Program author: dzhemvrot
Program version: 1.0
Program restributed using GPL-3.0 license''')

def quitting():
    root.destroy()
   
#########################################################################
  
root = tk.Tk() 
root.title("Tab Widget") 
tabControl = ttk.Notebook(root) 
  
tab1 = ttk.Frame(tabControl) 
tab2 = ttk.Frame(tabControl)
tab3 = ttk.Frame(tabControl)
  
tabControl.add(tab1, text ='Путь') 
tabControl.add(tab2, text ='Конец')
#tabControl.add(tab3, text ='Templates') 
tabControl.pack(expand = 1, fill ="both")

menubar = Menu(root)
root.config(menu=menubar)

file_menu = Menu(menubar,tearoff=0)

file_menu.add_command(
    label='Exit',
    command=quitting
)

menubar.add_cascade(
    label="File",
    menu=file_menu
)

menubar.add_command(label='About', command=about)

################################################################################

ttk.Label(tab1, text ="Просчитать путь").grid(column = 2, row = 0, padx = 30, pady = 0)
pressedL = ttk.Label(tab1, text = pbl)
pressedL.grid(column = 2, row = 1, padx = 0, pady = 0)

l1 = ttk.Button(tab1, text="Слабо ударить", command = lo).grid(column = 0, row = 2, padx = 10, pady = 10)
l2 = ttk.Button(tab1, text="Ударить", command = lt).grid(column = 1, row = 2, padx = 10, pady = 10)
l3 = ttk.Button(tab1, text="Сильно ударить", command = lth).grid(column = 0, row = 3, padx = 10, pady = 10)
l4 = ttk.Button(tab1, text="Протянуть", command = lf).grid(column = 1, row = 3, padx = 10, pady = 10)


r1 = ttk.Button(tab1, text="Штамповать", command = ro).grid(column = 3, row = 2, padx = 10, pady = 10)
r2 = ttk.Button(tab1, text="Изогнуть", command = rt).grid(column = 4, row = 2, padx = 10, pady = 10)
r3 = ttk.Button(tab1, text="Обжать", command = rth).grid(column = 3, row = 3, padx = 10, pady = 10)
r4 = ttk.Button(tab1, text="Усадить", command = rf).grid(column = 4, row = 3, padx = 10, pady = 10)

cente = ttk.Entry(tab1)
cente.grid(column = 2, row = 3)
calcp = ttk.Button(tab1, text="Просчитать", command = calculatepath).grid(column = 2, row = 4, padx = 10, pady = 10)

resultP = ttk.Label(tab1, text = "")
resultP.grid(column = 2, row = 5, padx = 0, pady = 0)


################################################################################

ttk.Label(tab2, text ="Calculate the end coordinate").grid(column = 2, row = 0, padx = 30, pady = 0)
pressedL2 = ttk.Label(tab2, text = "")
pressedL2.grid(column = 2, row = 1, padx = 0, pady = 0)

l12 = ttk.Button(tab2, text="Слабо ударить", command = lo2).grid(column = 0, row = 2, padx = 10, pady = 10)
l22 = ttk.Button(tab2, text="Ударить", command = lt2).grid(column = 1, row = 2, padx = 10, pady = 10)
l32 = ttk.Button(tab2, text="Сильно ударить", command = lth2).grid(column = 0, row = 3, padx = 10, pady = 10)
l42 = ttk.Button(tab2, text="Протянуть", command = lf2).grid(column = 1, row = 3, padx = 10, pady = 10)


r12 = ttk.Button(tab2, text="Штамповать", command = ro2).grid(column = 3, row = 2, padx = 10, pady = 10)
r22 = ttk.Button(tab2, text="Bend", command = rt2).grid(column = 4, row = 2, padx = 10, pady = 10)
r32 = ttk.Button(tab2, text="Обжать", command = rth2).grid(column = 3, row = 3, padx = 10, pady = 10)
r42 = ttk.Button(tab2, text="Усадить", command = rf2).grid(column = 4, row = 3, padx = 10, pady = 10)

resetB = ttk.Button(tab2, text="Reset", command = reset).grid(column = 2, row = 5, padx = 10, pady = 10)
calceB = ttk.Button(tab2, text="Calculate", command = calce).grid(column = 2, row = 4, padx = 10, pady = 10)

root.mainloop()
