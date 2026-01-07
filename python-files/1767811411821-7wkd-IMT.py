from io import text_encoding
from tkinter import *

root = Tk()
root.geometry('500x500')
root.maxsize(500,500)
root.minsize(500, 500)
root.title('Калькулятор ИМТ')

lbl = Label(root, text='Калькулятор ИМТ', font=('Arial',16, 'bold'))
lbl.pack()

lbl1 = Label(root, text='Рост в см', font=('Arial', 12, 'bold'))
lbl1.place(x=30, y = 35)

lbl2 = Label(root, text='Вес в кг', font=('Arial', 12, 'bold'))
lbl2.place(x=30, y=55)

lbl3 = Label(root, text='Ваш пол',  font=('Arial', 12, 'bold'))
lbl3.place(x=30, y=75)

lbl4 = Label(root, text='Ваше имя', font=('Arial', 12, 'bold'))
lbl4.place(x=30, y=95)

lbl5 = Label(root, text='Ваш ИМТ:', font=('Arial', 14, 'bold'))
lbl5.place(x=30, y = 140)

lbl6 = Label(root, font=('Arial', 14, 'bold'))
lbl6.place(x=135, y=140)

ent1 = Entry(root)
ent1.place(x=120, y=38)

ent2 = Entry(root)
ent2.place(x=120, y=58)

ent3 = Entry(root)
ent3.place(x=120, y=78)

ent4 = Entry(root)
ent4.place(x=120, y=98)

def hght(element):
    height = float(ent1.get())

def wght(element):
    weight = float(ent2.get())

def sx(element):
    sex = ent3.get()

def nm(element):
    name = str(ent4.get())
ent1.bind('<Return>', lambda e: ent2.focus(), hght)
ent2.bind('<Return>', lambda e: ent3.focus(), wght)
ent3.bind('<Return>', lambda e: ent4.focus(), sx)
ent4.bind("<Return>", nm)

def i():
    imt = round(float(ent2.get() )/(float((ent1.get()))/100) ** 2, ndigits=1)
    lbl6.configure(text=imt)
    if imt < 18.5:
        lbl7 = Label(root,text='Дефецит массы тела', font=('Arial', 12, 'bold'), fg='blue')
        lbl7.place(x=35, y=165)
    if imt >= 18.5 and imt <= 24.9:
        lbl7 = Label(root, text='Нормальная масса тела', font=('Arial', 12, 'bold'), fg='green')
        lbl7.place(x=35, y=165)
    if imt >= 25.0 and imt <= 29.9:
        lbl7 = Label(root, text='Избыточная масса тела', font=('Arial', 12, 'bold'), fg='yellow')
        lbl7.place(x=35, y=165)
    if imt >= 30.0 and imt <= 34.9:
        lbl7 = Label(root, text='Ожирение первой степени',  font=('Arial', 12, 'bold'), fg='orange')
        lbl7.place(x=35, y=165)
    if imt >= 35.0 and imt <= 39.9:
        lbl7 = Label(root, text='Ожирение второй степени', font=('Arial', 12, 'bold'), fg='red')
        lbl7.place(x=35, y=165)
    if imt >= 40.0:
        lbl7 = Label(root, text='Ожирение третьей степени', font=('Arial', 12, 'bold'), fg='black')
        lbl7.place(x=35, y=165)

bt = Button(root, text='Рассчитать', fg= 'green', command=i)
bt.place(x=235, y=140)

root.mainloop()


























