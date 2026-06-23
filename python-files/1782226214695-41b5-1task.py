import subprocess
import os
import tkinter
def roblox():
    home = os.path.expanduser('~')
    desktop = os.path.join(home, 'Desktop')
    robloxstart = subprocess.Popen(['start', 'Bloxstrap.lnk'], shell=True, cwd=desktop)
def operagx():
    operagxstart = subprocess.Popen(['start', 'operagx.lnk'], shell=True, cwd='C:\\Users\\IXSAZ\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs')
def discord():
    discordstart = subprocess.Popen(['start', 'Discord.lnk'], shell=True, cwd='C:\\Users\\IXSAZ\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Discord Inc')
def kill():
    os.system('taskkill /f /im python.exe')
window = tkinter.Tk()
window.title('Gm')
window.geometry('500x500')
window.configure(background='black')
button1 = tkinter.Button(window, text='Roblox',command=roblox)
button2 = tkinter.Button(window, text='Operagx',command=operagx)
button3 = tkinter.Button(window, text='Discord',command=discord)
button1.configure(bg='black', fg='white', font=('Consolas', 12))
button2.configure(bg='black', fg='white', font=('Consolas', 12))
button3.configure(bg='black', fg='white', font=('Consolas', 12))
button1.place(relx=0.5, rely=0.5, anchor='center')
button2.place(relx=0.3, rely=0.5, anchor='center')
button3.place(relx=0.7, rely=0.5, anchor='center')
button4 = tkinter.Button(window, text='Exit', command=kill)
button4.configure(bg='black', fg='white', font=('Consolas', 12))
button4.place(relx=0.5, rely=0.7, anchor='center')
window.attributes('-topmost', True)
window.focus_set()
window.mainloop()



