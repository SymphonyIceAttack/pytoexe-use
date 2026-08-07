import math
import random
import tkinter as tk
from tkinter import messagebox
print('if you forgat your pas type your yoser name')
print('verion: 1.0')
pas=input('enter pasword: ')
if pas=='@hasanam':
    messagebox.showinfo('72947397437')
    print('72947397437')
if pas=='hasan770'or'72947397437':
    print('1_projects')
    has=int(input('select: '))
    if has==1:
        print('1_quiz')
        print('2_list')
        quiz=input('select: ')
        if quiz=='1':
            print('1_get question')
            print('2_add question')
            qus=(random.randint(1,21))
            qu=input('select: ')
            if qu=='1':
                print(qus)
            if qu=='2':
                que=[input('enter question:')]
                qus.append(que)
        elif quiz=='2':
            namelist=[' ',' ']
            d=[' ',' ']
            numoffst=int(input('enter st number: '))
            for i in range(numoffst):
                a=input('enter name :')
                b=int(input('enter scoar: '))
                d.append(b)
                namelist.append(a)
                print(namelist)
                print(d)
elif pas=='/admin | coder':
    print('hasan pas:hasan770')
    print('hasan pas2:72947397437')
else:
    messagebox.sowerror('in ramz vojood nadureh')
if pas=='hasanarabbastanshenas':
    for ii in range(1):
         messagebox.showwarning('fozoly mamno')
    messagebox.showinfo('fozol')

