from tkinter import *
import customtkinter as ctk
import re

root = Tk()
root.geometry('280x500')
root.title("calculator")
root.resizable(False, False)
root.iconbitmap('icon.ico')
#functions

def display_input(_input):

    input_box.insert(END,  string=_input)
    display_result()



def display_result():

    try:

        calculation = input_box.get()
        
        if re.search(pattern=r'[\+\-\*\%/]', string=calculation):

        
        
            result = eval(calculation)
            result_lb.config(text=f' = {result}')
    
        else:
            result_lb.config(text='')
    except Exception as error:
        print(error)


def delete_input():
    index = input_box.index(END) - 1
    input_box.delete(index)
    display_result()

def clear_input():
    clear = input_box.get()
    input_box.delete(0, END)

    input_box.config(font=("bold", 20))
    result_lb.config(font=("bold", 15))
    display_result()

def highlight_result():
     input_box.config(font=('bold', 15)) 
     result_lb.config(font=("bold", 25))
     
     
def theme_change():
     if root.cget('bg') == 'SystemButtonFace':
        
        
        root.tk_setPalette('black')
        input_box.config(bg='black')
         
        theme_btn.config(text='☀')
        result_lb.config(fg=white) 
        input_box.config(fg=gray)
     else:

        root.tk_setPalette('SystemButtonFace') 
        theme_btn.config(text="🌙")
       





#input box

input_box = Entry(root, font=('bold', 20), justify=RIGHT,bd=0, bg='SystemBUttonFace')
input_box.place(x=15, y=10, width=250, height=50)

result_lb = Label(root, font=('bold', 15), fg="gray", anchor=E)
result_lb.place(x=15, y=75, width=250, height=40)

#button

clear_btn = ctk.CTkButton(master=root, text='C', width=40, height=45, font=('bold', 30), fg_color='#FF7433', 
corner_radius=8, command=clear_input)
clear_btn.place(x=15, y=135)

delete_btn = ctk.CTkButton(master=root, text='D', width=40, height=45, font=('bold', 30), fg_color='#FF7433', 
corner_radius=8, command=delete_input)
delete_btn.place(x=80, y=135)

percentage_btn = ctk.CTkButton(master=root, text='%', width=40, height=45, font=('bold', 20), fg_color='#FF7433', 
corner_radius=8, command=lambda:display_input('%'))
percentage_btn.place(x=145, y=135)

divide_btn = ctk.CTkButton(master=root, text='÷', width=40, height=45, font=('bold', 30), fg_color='#FF7433', 
corner_radius=8, command=lambda:display_input("/"))
divide_btn.place(x=215, y=135)


btn_7 = ctk.CTkButton(master=root, text='7', width=40, height=45, font=('bold', 25),
corner_radius=8, command=lambda:display_input('7'))
btn_7.place(x=15, y=210)

btn_8 = ctk.CTkButton(master=root, text='8', width=40, height=45, font=('bold', 25),
corner_radius=8, command=lambda:display_input('8'))
btn_8.place(x=80, y=210)

btn_9 = ctk.CTkButton(master=root, text='9', width=40, height=45, font=('bold', 25),
corner_radius=8, command=lambda:display_input('9'))
btn_9.place(x=145, y=210)

multiply_btn = ctk.CTkButton(master=root, text='×', width=40, height=45, font=('bold', 33), fg_color='#FF7433', 
corner_radius=8, command=lambda:display_input('*'))
multiply_btn.place(x=215, y=210)

btn_4 = ctk.CTkButton(master=root, text='4', width=40, height=45, font=('bold', 25),
corner_radius=8, command=lambda:display_input('4'))
btn_4.place(x=15, y=285)

btn_5 = ctk.CTkButton(master=root, text='5', width=40, height=45, font=('bold', 25),
corner_radius=8, command=lambda:display_input('5'))
btn_5.place(x=80, y=285)

btn_6 = ctk.CTkButton(master=root, text='6', width=40, height=45, font=('bold', 25),
corner_radius=8, command=lambda:display_input('6'))
btn_6.place(x=145, y=285)

minus_btn = ctk.CTkButton(master=root, text='-', width=40, height=45, font=('bold', 30),
fg_color='#FF7433' ,corner_radius=8, command=lambda:display_input('-'))
minus_btn.place(x=215, y=285)

btn_1 = ctk.CTkButton(master=root, text='1', width=40, height=45, font=('bold', 25),
corner_radius=8, command=lambda:display_input('1'))
btn_1.place(x=15, y=360)

btn_2 = ctk.CTkButton(master=root, text='2', width=40, height=45, font=('bold', 25),
corner_radius=8, command=lambda:display_input('2'))
btn_2.place(x=80, y=360)

btn_3 = ctk.CTkButton(master=root, text='3', width=40, height=45, font=('bold', 25),
corner_radius=8, command=lambda:display_input('3'))
btn_3.place(x=145, y=360)

plus_btn = ctk.CTkButton(master=root, text='+', width=40, height=45, font=('bold', 30),
fg_color='#FF7433' ,corner_radius=8, command=lambda:display_input('+'))
plus_btn.place(x=215, y=360)

theme_btn = Button(root, text='🌙', font=("bold", 20), bd=0, command=theme_change)
theme_btn.place(x=15,y=435, width=40, height=45)


btn_0 = ctk.CTkButton(master=root, text='0', width=40, height=45, font=('bold', 25),
corner_radius=8,command=lambda:display_input('0'))
btn_0.place(x=80, y=435)

decimal_btn = ctk.CTkButton(master=root, text='.', width=40, height=45, font=('bold', 30),
corner_radius=8, command=lambda:display_input('.'))
decimal_btn.place(x=145, y=435)

equal_btn = ctk.CTkButton(master=root, text='=', width=40, height=45, font=('bold', 30),
fg_color='#FF7433' ,corner_radius=8, command=highlight_result)
equal_btn.place(x=215, y=435)

def keyboard_input(event):

    key = event.keysym
    char = event.char

    # Numbers
    if char.isdigit():
        display_input(char)

    # Operators
    elif char in "+-*/%.":
        display_input(char)

    # Brackets
    elif char in "()":
        display_input(char)

    # Enter
    elif key == "Return":
        highlight_result()

    # Backspace
    elif key == "BackSpace":
        delete_input()

    # Delete (Clear All)
    elif key == "Delete":
        clear_input()

    # Escape (Clear All)
    elif key == "Escape":
        clear_input()







root.bind("<Key>", keyboard_input)





root.mainloop()