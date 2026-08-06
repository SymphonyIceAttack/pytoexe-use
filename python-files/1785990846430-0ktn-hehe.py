import tkinter as tk
import webbrowser

newwindow = tk.Tk()
newwindow.geometry('400x400')

def opendildo():
	webbrowser.open_new_tab('https://www.pinkcherry.ca/collections/dildo-sex-toys')
	newwindow.after(500, opendildo)

button = tk.Button(font=('Arial', 20), text='Press for free futa porn', command=opendildo)
button.pack()

newwindow.mainloop()