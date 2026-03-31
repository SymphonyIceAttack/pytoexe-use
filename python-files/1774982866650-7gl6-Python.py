from tkinter import *

root = Tk()
root.title('Antilock')
root.geometry("400x200+700+500")
root.resizable(width=False, height=False)

l = Label(text = 'Введите ID ключа, чтобы продолжить')
l2 = Label(text='Лучший обход всех блокировок РКН!')
e = Entry(textvariable='None')
b = Button(text="Activate")


l.pack(side=TOP)
l2.pack(side=BOTTOM, pady='20')
e.pack()
b.pack()

root.mainloop()