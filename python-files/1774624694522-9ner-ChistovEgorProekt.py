import random
import tkinter
from tkinter import *
from tkinter import ttk

window = Tk()
window.resizable(width=False, height=False)

a=[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25]

canvas1 = Canvas(bg="white", width=420,height=420)

def button3():
    global buttonA
    global canvas1
    b=["го","ка","ло","ко","сто","мя","во","на","ру","ше","ре","ча","вк","ку","це","бо","ку","сле","дра","ме","на","ве","со","сме","сце","му","вы","ра","ры","от"]
    c=["сти", "ша", "жка","шка","лб","та","лк","бор","ка","лк","чь","шка","ус","ст","лое","кс","ча","за","ма","тро","лог","дро","сна","на","на","сор","зов","зум","ба","бор"]
    window.geometry("720x600")
    canvas1=Canvas(bg="white", width=720, height=720)
    canvas1.pack(expand=1)
    d=list(zip(b,c))
    random.shuffle(d)
    b,c=zip(*d)
    canvas1.create_line(300, 60, 420, 60)
    canvas1.create_line(270, 120, 450, 120)
    canvas1.create_line(240, 180, 480, 180)
    canvas1.create_line(210, 240, 510, 240)
    canvas1.create_line(180, 300, 540, 300)
    canvas1.create_line(150, 360, 570, 360)
    canvas1.create_line(120, 420, 600, 420)
    canvas1.create_line(90, 480, 630, 480)
    canvas1.create_line(60, 540, 660, 540)
    canvas1.create_text(360, 50, text="1",font=("Times New Roman", 20))
    canvas1.create_text(360, 110, text="2", font=("Times New Roman", 20))
    canvas1.create_text(360, 170, text="3", font=("Times New Roman", 20))
    canvas1.create_text(360, 230, text="4", font=("Times New Roman", 20))
    canvas1.create_text(360, 290, text="5", font=("Times New Roman", 20))
    canvas1.create_text(360, 350, text="6", font=("Times New Roman", 20))
    canvas1.create_text(360, 410, text="7", font=("Times New Roman", 20))
    canvas1.create_text(360, 470, text="8", font=("Times New Roman", 20))
    canvas1.create_text(360, 530, text="9", font=("Times New Roman", 20))
    canvas1.create_text(280, 50, text=str(''.join(map(str, b[:1]))), font=("Times New Roman", 20))
    canvas1.create_text(440, 50, text=str(''.join(map(str, c[:1]))), font=("Times New Roman", 20))
    canvas1.create_text(250, 110, text=str(''.join(map(str, b[1:2]))), font=("Times New Roman", 20))
    canvas1.create_text(470, 110, text=str(''.join(map(str, c[1:2]))), font=("Times New Roman", 20))
    canvas1.create_text(220, 170, text=str(''.join(map(str, b[2:3]))), font=("Times New Roman", 20))
    canvas1.create_text(500, 170, text=str(''.join(map(str, c[2:3]))), font=("Times New Roman", 20))
    canvas1.create_text(190, 230, text=str(''.join(map(str, b[3:4]))), font=("Times New Roman", 20))
    canvas1.create_text(530, 230, text=str(''.join(map(str, c[3:4]))), font=("Times New Roman", 20))
    canvas1.create_text(160, 290, text=str(''.join(map(str, b[4:5]))), font=("Times New Roman", 20))
    canvas1.create_text(560, 290, text=str(''.join(map(str, c[4:5]))), font=("Times New Roman", 20))
    canvas1.create_text(130, 350, text=str(''.join(map(str, b[5:6]))), font=("Times New Roman", 20))
    canvas1.create_text(590, 350, text=str(''.join(map(str, c[5:6]))), font=("Times New Roman", 20))
    canvas1.create_text(100, 410, text=str(''.join(map(str, b[6:7]))), font=("Times New Roman", 20))
    canvas1.create_text(620, 410, text=str(''.join(map(str, c[6:7]))), font=("Times New Roman", 20))
    canvas1.create_text(70, 470, text=str(''.join(map(str, b[7:8]))), font=("Times New Roman", 20))
    canvas1.create_text(650, 470, text=str(''.join(map(str, c[7:8]))), font=("Times New Roman", 20))
    canvas1.create_text(40, 530, text=str(''.join(map(str, b[8:9]))), font=("Times New Roman", 20,)) ##-20
    canvas1.create_text(680, 530, text=str(''.join(map(str, c[8:9]))), font=("Times New Roman", 20)) ##+20
    buttonA=ttk.Button(text="<-",command=button2)
    buttonA.place(x=320,y=575)

def button2():
    canvas1.destroy()
    buttonA.destroy()
    window.geometry("720x420")

def button1():
    global buttonA
    global canvas1
    random.shuffle(a)
    window.geometry("420x420")
    canvas1 = Canvas(bg="white", width=420, height=420)
    canvas1.pack(expand=1)
    canvas1.create_line(84,0,84,420)
    canvas1.create_line(168, 0, 168, 420)
    canvas1.create_line(252, 0, 252, 420)
    canvas1.create_line(336, 0, 336, 420)
    canvas1.create_line(0, 84, 420, 84)
    canvas1.create_line(0, 168, 420, 168)
    canvas1.create_line(0, 252, 420, 252)
    canvas1.create_line(0, 336, 420, 336)
    canvas1.create_text(42,42,text=str(''.join(map(str, a[:1]))),font=("Times New Roman", 20))
    canvas1.create_text(126, 42, text=str(''.join(map(str, a[1:2]))), font=("Times New Roman", 20))
    canvas1.create_text(210, 42, text=str(''.join(map(str, a[2:3]))), font=("Times New Roman", 20))
    canvas1.create_text(294, 42, text=str(''.join(map(str, a[3:4]))), font=("Times New Roman", 20))
    canvas1.create_text(378, 42, text=str(''.join(map(str, a[4:5]))), font=("Times New Roman", 20))
    canvas1.create_text(42, 126, text=str(''.join(map(str, a[5:6]))), font=("Times New Roman", 20))
    canvas1.create_text(126, 126, text=str(''.join(map(str, a[6:7]))), font=("Times New Roman", 20))
    canvas1.create_text(210, 126, text=str(''.join(map(str, a[7:8]))), font=("Times New Roman", 20))
    canvas1.create_text(294, 126, text=str(''.join(map(str, a[8:9]))), font=("Times New Roman", 20))
    canvas1.create_text(378, 126, text=str(''.join(map(str, a[9:10]))), font=("Times New Roman", 20))
    canvas1.create_text(42, 210, text=str(''.join(map(str, a[10:11]))), font=("Times New Roman", 20))
    canvas1.create_text(126, 210, text=str(''.join(map(str, a[11:12]))), font=("Times New Roman", 20))
    canvas1.create_text(210, 210, text=str(''.join(map(str, a[12:13]))), font=("Times New Roman", 20))
    canvas1.create_text(294, 210, text=str(''.join(map(str, a[13:14]))), font=("Times New Roman", 20))
    canvas1.create_text(378, 210, text=str(''.join(map(str, a[14:15]))), font=("Times New Roman", 20))
    canvas1.create_text(42, 294, text=str(''.join(map(str, a[15:16]))), font=("Times New Roman", 20))
    canvas1.create_text(126, 294, text=str(''.join(map(str, a[16:17]))), font=("Times New Roman", 20))
    canvas1.create_text(210, 294, text=str(''.join(map(str, a[17:18]))), font=("Times New Roman", 20))
    canvas1.create_text(294, 294, text=str(''.join(map(str, a[18:19]))), font=("Times New Roman", 20))
    canvas1.create_text(378, 294, text=str(''.join(map(str, a[19:20]))), font=("Times New Roman", 20))
    canvas1.create_text(42, 378, text=str(''.join(map(str, a[20:21]))), font=("Times New Roman", 20))
    canvas1.create_text(126, 378, text=str(''.join(map(str, a[21:22]))), font=("Times New Roman", 20))
    canvas1.create_text(210, 378, text=str(''.join(map(str, a[22:23]))), font=("Times New Roman", 20))
    canvas1.create_text(294, 378, text=str(''.join(map(str, a[23:24]))), font=("Times New Roman", 20))
    canvas1.create_text(378, 378, text=str(''.join(map(str, a[24:25]))), font=("Times New Roman", 20))
    buttonA=ttk.Button(text="<-",command=button2)
    buttonA.place(x=172,y=395)


window.title("Программа для скорочтния")
window.geometry("720x420")
window["bg"] = "white"

titler=tkinter.Label(window, text="Программа для скорочтения",font=("Times New Roman", 20), fg="black", bg="white")
titler.pack()
titler.place(x=200, y=50)

buttonAA=tkinter.Button(window, text="Таблица Шульте", command=button1,width="35",height="3",fg="black",bg="white")
buttonAA.place(x=250, y=100)

buttonBB=tkinter.Button(window, text="Клиновидная таблица", command=button3,width="35",height="3",fg="black",bg="white")
buttonBB.place(x=250, y=200)

titlerer=tkinter.Label(window, text="Постарайся делать упражнения смотря на середину!",font=("Times New Roman", 14), fg="black", bg="white")
titlerer.place(x=160, y=350)

window.mainloop()