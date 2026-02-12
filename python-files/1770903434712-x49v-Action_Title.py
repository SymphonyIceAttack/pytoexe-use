from tkinter import * 
from tkinter import PhotoImage  #???

root = Tk()  
root.geometry("200x200")  
image = PhotoImage(file="Aloha_1.gif") #???
label = Label(root, text = "Экран-заставка", font = 18) #  image=image    ??? 
label.pack()

def main():  
    # уничтожить заставку  
    root.destroy()
    
    # запустить tkinter  
    root = Tk()  
    root.geometry("400x400")
    
    # установить интервал  
    root.after(3000, main)
    
    # запустить tkinter  
    root.mainloop()  
