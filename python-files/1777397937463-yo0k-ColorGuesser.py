from tkinter import *
from random import *
from math import *
from time import *
from tkinter import ttk
####################################################################
def display():
    global count
    global colr
    global colg
    global colb
    global display_button
    global points
    global mod
    global r
    global t
    global q

    if mod == 0:
        pl_colr=int('0'+pl_colwr.get())
        pl_colg=int('0'+pl_colwg.get())
        pl_colb=int('0'+pl_colwb.get())
    if mod == 1:
        if r == 1:
            pl_colr=colr
            pl_colg=int('0'+pl_colwg.get())
            pl_colb=int('0'+pl_colwb.get())
        if r==2:
            pl_colr=int('0'+pl_colwr.get())
            pl_colg=colg
            pl_colb=int('0'+pl_colwb.get())
        if r==3:
            pl_colr=int('0'+pl_colwr.get())
            pl_colg=int('0'+pl_colwg.get())
            pl_colb=colb         
    if mod == 2:
        if r == 1:
            pl_colr=int(str(colr//10)+pl_colwr.get())
            pl_colg=int('0'+pl_colwg.get())
            pl_colb=int('0'+pl_colwb.get())
        if r==2:
            pl_colr=int('0'+pl_colwr.get())
            pl_colg=int(str(colg//10)+pl_colwg.get())
            pl_colb=int('0'+pl_colwb.get())
        if r==3:
            pl_colr=int('0'+pl_colwr.get())
            pl_colg=int('0'+pl_colwg.get())
            pl_colb=int(str(colb//10)+pl_colwb.get())
    if mod == 3:
        if r == 1:
            pl_colr=int(str(colr//100)+pl_colwr.get())
            pl_colg=int('0'+pl_colwg.get())
            pl_colb=int('0'+pl_colwb.get())
        if r==2:
            pl_colr=int('0'+pl_colwr.get())
            pl_colg=int(str(colg//100)+pl_colwg.get())
            pl_colb=int('0'+pl_colwb.get())
        if r==3:
            pl_colr=int('0'+pl_colwr.get())
            pl_colg=int('0'+pl_colwg.get())
            pl_colb=int(str(colb//100)+pl_colwb.get())

    cr=abs(pl_colr-colr)
    cg=abs(pl_colg-colg)
    cb=abs(pl_colb-colb)

    points=500-2*(cr+cg+cb)
    count+=points

    pl_colwr.delete(0, END)
    pl_colwg.delete(0, END)
    pl_colwb.delete(0, END)
    q=1
    playc()

def timer():
    global t
    global q
    if q == 1:
        q=0
        t=20
        return
    if t > 0:
        t-=0.5
        root.after(500, timer)
        canvas.itemconfigure('time', text='Время: '+str(ceil(t)))
    else:
        timer_display()

def timer_display():
    global points
    global count
    global pl_colwr
    global pl_colwg
    global pl_colwb
    global t

    points=-500
    count+=points

    pl_colwr.delete(0, END)
    pl_colwg.delete(0, END)
    pl_colwb.delete(0, END)
    t=20
    playc()

def play():
    play_but.destroy()
    set_but.destroy()
    canvas.delete(lbl)
    canvas.delete('menu')
    canvas.create_rectangle(95, 95, 505, 505, fill='white', tags=['play'])
    global count
    global colr
    global colg
    global colb
    global points
    global pl_colr
    global pl_colg
    global pl_colb
    global pl_colwr
    global pl_colwg
    global pl_colwb
    global display_button
    global mod
    global cnt

    canvas.create_text(512, 25, anchor=CENTER, text='Счёт: 0', font='Times 13', tags=['scores', 'play'])
    canvas.create_text(512, 55, anchor=CENTER, text='Время: ', font='Times 13', tags=['time', 'play'])
    colr=randint(0, 255)
    colg=randint(0, 255)
    colb=randint(0, 255)
    count=0
    
    pl_colwr=ttk.Entry(width=3)
    pl_colwg=ttk.Entry(width=3)
    pl_colwb=ttk.Entry(width=3)
    pl_colwr.place(x=150, y=550, anchor=NW)
    pl_colwg.place(x=250, y=550, anchor=NW)
    pl_colwb.place(x=350, y=550, anchor=NW)
    canvas.create_text(120, 548, text='R:', fill="#000000", font='Times 17', anchor=NW, tags=['play'])
    canvas.create_text(220, 548, text='G:', fill="#000000", font='Times 17', anchor=NW, tags=['play'])
    canvas.create_text(320, 548, text='B:', fill="#000000", font='Times 17', anchor=NW, tags=['play'])
    display_button = ttk.Button(text="ГОТОВО", command=display)
    display_button.place(anchor=NW, x=400, y=548)

    colrh=hex(colr)[2:]
    if len(colrh)==1:
        colrh='0'+colrh
    
    colgh=hex(colg)[2:]
    if len(colgh)==1:
        colgh='0'+colgh
    
    colbh=hex(colb)[2:]
    if len(colbh)==1:
        colbh='0'+colbh
    
    canvas.create_rectangle(100, 100, 500, 500, fill=f'#{colrh+colgh+colbh}', tags=['play'])
    points=0
    canvas.create_text(600, 120, fill="#0B3813", anchor=NW, text='Текущий модификатор:', font='Times 25', tags=['play'])
    canvas.create_text(610, 180, fill="#0B3813", anchor=NW, text='-', font='Times 25', tags=['mods', 'play'])
    
    if mode==1:
        timer()
    else:
        canvas.delete('time')

def playc():
    global count
    global colr
    global colg
    global colb
    global points
    global pl_colr
    global pl_colg
    global pl_colb
    global mod
    global r
    
    if count <= -1000:
        canvas.create_text(512, 200, text='ВЫ ПРОИГРАЛИ!', font='TImes 35', fill="#444444", tags=['menu'])
        menu()
        return
    if count >= 5000:
        canvas.create_text(512, 200, text='ВЫ ВЫИГРАЛИ!', font='Times 35', fill="#444444", tags=['menu'])
        menu()
        return

    canvas.itemconfigure('scores', text=f'Счёт: {count}')
    colr=randint(0, 255)
    colg=randint(0, 255)
    colb=randint(0, 255)

    if points >= -500 and points < -400:
        canvas.itemconfigure('mods', text='Раскрытие спектра')
        r=randint(1, 3)
        mod = 1
        if r==1:
            pl_colwr.insert(0, f'{colr}')
        if r==2:
            pl_colwg.insert(0, f'{colg}')
        if r==3:
            pl_colwb.insert(0, f'{colb}')
    if points >= -400 and points < -300:
        canvas.itemconfigure('mods', text='Раскрытие спектра')
        r=randint(1, 3)
        mod = 2
        if r==1:
            pl_colwr.insert(0, f'{colr//10}')
        if r==2:
            pl_colwg.insert(0, f'{colg//10}')
        if r==3:
            pl_colwb.insert(0, f'{colb//10}')
    if points >= -300 and points < -200:
        canvas.itemconfigure('mods', text='Раскрытие спектра')
        r=randint(1, 3)
        mod = 3
        if r==1:
            pl_colwr.insert(0, f'{colr//100}')
        if r==2:
            pl_colwg.insert(0, f'{colg//100}')
        if r==3:
            pl_colwb.insert(0, f'{colb//100}')
    if points >= -200 and points <= 200:
        canvas.itemconfigure('mods', text='-')
    if points > 200 and points <= 300:
        canvas.itemconfigure('mods', text='Прозрачность 75%')
        colr=(colr+(colr+255)//2)//2
        colg=(colg+(colg+255)//2)//2
        colb=(colb+(colb+255)//2)//2
    if points > 300 and points <= 400:
        canvas.itemconfigure('mods', text='Прозрачность 50%')
        colr=(colr+255)//2
        colg=(colg+255)//2
        colb=(colb+255)//2
    if points > 400:
        canvas.itemconfigure('mods', text='Прозрачность 25%')
        colr=(255+(colr+255)//2)//2
        colg=(255+(colg+255)//2)//2
        colb=(255+(colb+255)//2)//2

    colrh=hex(colr)[2:]
    if len(colrh)==1:
        colrh='0'+colrh
    
    colgh=hex(colg)[2:]
    if len(colgh)==1:
        colgh='0'+colgh
    
    colbh=hex(colb)[2:]
    if len(colbh)==1:
        colbh='0'+colbh
    
    canvas.create_rectangle(100, 100, 500, 500, fill=f'#{colrh+colgh+colbh}', tags=['play'])
    points=0
    
    if mode==1:
        timer()
    else:
        canvas.delete('time')

def menu():
    global play_but
    global set_but
    global display_button
    canvas.delete('play')
    display_button.destroy()
    pl_colwr.destroy()
    pl_colwg.destroy()
    pl_colwb.destroy()
    play_but=Button(text='Играть', command=play)
    set_but=Button(text='Настройки', command=settings)
    play_but.place(height=50, width=350, relx=0.5, rely=0.5, anchor='c')
    set_but.place(height=50, width=350, relx=0.5, rely=0.6, anchor='c')

def settings():
    global play_but
    global set_but
    global classic
    global notime
    global exit
    play_but.destroy()
    set_but.destroy()
    canvas.delete('menu')
    canvas.delete(lbl)
    canvas.create_text(512, 200, text='Выберите режим', font='Times 35', fill='#000000', tags=['settings'])
    classic=Button(text='Классический', command=clas)
    notime=Button(text='Без времени',  command=noti)
    exit=Button(text='Выход', command=set_menu)
    classic.place(height=50, width=350, relx=0.5, rely=0.5, anchor=CENTER)
    notime.place(height=50, width=350, relx=0.5, rely=0.6, anchor=CENTER)
    exit.place(height=50, width=350, relx=0.5, rely=0.7, anchor=CENTER)
def clas():
    global mode
    mode=1
    set_menu()
def noti():
    global mode
    mode=2
    set_menu()
def set_menu():
    global play_but
    global set_but
    global classic
    global notime
    global exit
    global lbl
    canvas.delete('settings')
    classic.destroy()
    notime.destroy()
    exit.destroy()
    lbl=canvas.create_image(0, 0, anchor='nw', image=label)
    play_but=Button(text='Играть', command=play)
    set_but=Button(text='Настройки', command=settings)
    play_but.place(height=50, width=350, relx=0.5, rely=0.5, anchor='c')
    set_but.place(height=50, width=350, relx=0.5, rely=0.6, anchor='c')
############################################################################
root = Tk()
root.title("ColorGuesser")
root.geometry("1024x720+240-75")
root.resizable(False, False)
icon = PhotoImage(file='icon.png')
root.iconphoto(True, icon)
canvas=Canvas(background='white', height=720, width=1024)
canvas.pack()
backg=PhotoImage(file='bg.png')
label=PhotoImage(file='lbl.png')
canvas.create_image(0, 0, anchor='nw', image=backg)
lbl=canvas.create_image(0, 0, anchor='nw', image=label)  
t=20
q=0
pl_colr=0
pl_colg=0
pl_colb=0
count=0
points=0
mod=0
mode=1

play_but=Button(text='Играть', command=play)
set_but=Button(text='Настройки', command=settings)
play_but.place(height=50, width=350, relx=0.5, rely=0.5, anchor='c')
set_but.place(height=50, width=350, relx=0.5, rely=0.6, anchor='c')


root.mainloop()