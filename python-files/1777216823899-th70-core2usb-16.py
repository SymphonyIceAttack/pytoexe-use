#!/usr/bin/python
# -*- coding: utf-8 -*-

###########################################################
#                                                         #
#                                                         #
# 2012.09.05.                                             #
#                                                         #
# v1.6                                                    #
#                                                         #
# Márkus Béla / HA5DI                                     #
###########################################################

import sys
import time
import datetime
import getopt
import tempfile
import shutil
import ftplib
#import zipfile
import os
import hashlib
import subprocess
import win32com.client 
import win32file
import win32api
import tkMessageBox
import Tkconstants
import tkFileDialog

from Tkinter import *
import ttk

def ftpcallbackdir(s):
    w = s.split()

    if len(w) == 11:
        if w[9] == '->' and w[8].find('-current.iso') > 0:
            ftplst.append(s)
            
    return

def getlatestversionid():
    try:
        ftp = ftplib.FTP('distro.ibiblio.org')
        ftp.login()
        ftp.cwd('tinycorelinux/4.x/x86/release')
        ftp.retrlines('LIST', ftpcallbackdir)
        ftp.quit()
    except:
        pass

    id = ''

    w = []

    if len(ftplst) <> 0:
        w = ftplst[0].split()[10].split('-')[1].split('.')

    if len(w) >= 3:
        s = ''
        for i in range(0, len(w) - 1):
            s += w[i] + '.'

        id = s[:-1]
        
    return id


def GetListRemovableDrives():
    lst = []
                
    for d in win32api.GetLogicalDriveStrings().split(chr(0)):
        if win32file.GetDriveType(d) == 2:
            if d[0] == 'A' or d[0] == 'B':
                continue
            
            lst.append(d[:2])

    return lst

def menuexit():
    if tkMessageBox.askquestion("Exit", "Do you really want to exit?") == "yes":
        root.destroy()
    
    return
    
def menuabout():
    s = "Tiny Core Linux USB installer\n\nv1.6\n\n"
    s += "(c) B. Márkus - September 5, 2012\n\n"
    s += "https://sourceforge.net/projects/core2usb/"
    tkMessageBox.showinfo("", s)
    return

def menuchkmd5():
    global w5
    global fn

    fp = open(fn, 'rb')
    m = hashlib.md5()
    
    while True:
        bf = fp.read(1000000)

        if len(bf) == 0:
            break

        m.update(bf)
        
    fp.close()

    if w5[0] == m.hexdigest():
        tkMessageBox.showinfo("", "MD5 is OK")
    else:
        tkMessageBox.showerror("", "MD5 check failed, ISO file is corrupted")
        
    return


def menutcversion():
    global fn
    lst = []
    vers = getlatestversionid()

    if vers <> '':
        tkMessageBox.showinfo("", 'Current TC version is ' + vers)
    else:
        tkMessageBox.showerror("", 'Error checking current version')
        
    return
    
def callback1():
    global tmpdir
    global w5
    global fn
    
    if tmpdir <> '':
        shutil.rmtree(tmpdir)

    tmpdir = tempfile.mkdtemp(prefix='core2usb')
    fn = tkFileDialog.askopenfilename(parent=root, initialdir="\\", filetypes=[('Core image files', '.iso')])

    fn = fn.replace('/', '\\')
    if fn == '':
        tmpdir = ''
    else:
        variso.set(fn)
        UpdateStatus('Extracting ISO file', 'red')
        r =subprocess.call(['7zG.exe', 'x', fn, '-o' + tmpdir])
        UpdateStatus('', 'black')
        LbISOfile.config(fg='BLACK')
        
        if r <> 0:
            shutil.rmtree(tmpdir)
            tmpdir = ''

        try:
            fp5 = open(fn + '.md5.txt')
            ln5 = fp5.readline()
            fp5.close()
            w5 = ln5.split()
            if len(w5) == 2:
                if len(w5[0]) == 32:
                    filemenu.entryconfig(0, state=NORMAL)
            
        except IOError:
            filemenu.entryconfig(0, state=DISABLED)
        
    UpdateSetupStatus()
    return

def callback2():
    global finished
    
    if tmpdir == '':
        tkMessageBox.showerror("Error", "No source ISO file selected")
        return

    if targetdrive == '':
        tkMessageBox.showerror("Error", "No target drive selected")
        return    

    for rt, dirs, files in os.walk(targetdrive):
        break

    if len(files) <> 0 or len(dirs) <> 0:
        UpdateStatus('Not empty', 'RED')
        r = tkMessageBox.showerror("Error", "Target drive is not empty")
        return
    
    Button1.config(state='disabled')
    Button2.config(state='disabled')
    
    try:
        os.mkdir(targetdrive + '\\boot')
    except WindowsError:
        os.remove(targetdrive + '\\boot\\syslinux\\ldlinux.sys')
        shutil.rmtree(targetdrive + '\\boot')

    for rt, dirs, files in os.walk(tmpdir + '\\boot'):
        break
                
    for p in files:       
        mycopy(tmpdir + '\\boot\\' + p, targetdrive + '\\boot\\' + p)

    for rt, dirs, files in os.walk(tmpdir + '\\boot\\isolinux'):
        break

    try:
        os.mkdir(targetdrive + '\\boot\\syslinux')
    except WindowsError:
        tkMessageBox.showerror("Error", "\\boot\\syslinux directory already exists")
        return

    for p in files:
        if p == 'isolinux.cfg':
            fp = open(tmpdir + '\\boot\\isolinux\\isolinux.cfg')
            ln = fp.read(10000)
            fp.close()

            fp = open(targetdrive + '\\boot\\syslinux\\syslinux.cfg', 'w')
            fp.write(ln.replace('quiet', 'quiet waitusb=5'))
            fp.close()
            
        elif p <> 'isolinux.bin':
            #print 'boot\\syslinux\\' + p
            mycopy(tmpdir + '\\boot\\isolinux\\' + p, targetdrive + '\\boot\\syslinux\\' + p)

    #os.rename(targetdrive + '\\boot\\syslinux\\isolinux.cfg', targetdrive + '\\boot\\syslinux\\syslinux.cfg')

    # Make it bootable
    UpdateStatus('Installing syslinux', 'red')
    r = subprocess.call(['syslinux.exe', '-maf', '-d', '\\boot\\syslinux', targetdrive])

    # Create TCE duirectory
    
    try:
        os.mkdir(targetdrive + '\\tce')
    except WindowsError:
        tkMessageBox.showerror("Error", "Error creating \\tce directory")
        return

    try:
        os.mkdir(targetdrive + '\\tce\\optional')
    except WindowsError:
        tkMessageBox.showerror("Error", "Error creating \\cde\\optional directory")
        return

    try:
        os.mkdir(targetdrive + '\\tce\\ondemand')
    except WindowsError:
        tkMessageBox.showerror("Error", "Error creating \\cde\\ondemand directory")
        return

    # Copy CDE

    for rt, dirs, files in os.walk(tmpdir):
        break

    flg = 0
    
    for p in dirs:
        if p == 'cde':
            flg = 1
            break
        
    if flg <> 0:

        # Copy cde 

        for rt, dirs, files in os.walk(tmpdir + '\\cde'):
            break

        for p in files:
            #print 'cde\\' + p
            mycopy(tmpdir + '\\cde\\' + p, targetdrive + '\\tce\\' + p)
       
        # Copy optional

        for rt, dirs, files in os.walk(tmpdir + '\\cde\\optional'):
            break

        for p in files:
            #print 'cde\\optional\\' + p
            mycopy(tmpdir + '\\cde\\optional\\' + p, targetdrive + '\\tce\\optional\\' + p)

    # Copy TCE

    for rt, dirs, files in os.walk(tmpdir):
        break

    flg = 0
    
    for p in dirs:
        if p == 'tce':
            flg = 1
            break
        
    if flg <> 0:

        # Copy cde 

        for rt, dirs, files in os.walk(tmpdir + '\\tce'):
            break

        for p in files:
            #print 'cde\\' + p
            mycopy(tmpdir + '\\tce\\' + p, targetdrive + '\\tce\\' + p)
       
        # Copy optional

        for rt, dirs, files in os.walk(tmpdir + '\\tce\\optional'):
            break

        for p in files:
            #print 'cde\\optional\\' + p
            mycopy(tmpdir + '\\tce\\optional\\' + p, targetdrive + '\\tce\\optional\\' + p)        

        # Copy ondemand

        for rt, dirs, files in os.walk(tmpdir + '\\tce\\ondemand'):
            break

        print "ONDEMAND:", files

        for p in files:
            #print 'cde\\ondemand\\' + p
            mycopy(tmpdir + '\\tce\\ondemand\\' + p, targetdrive + '\\tce\\ondemand\\' + p)
            print "---", p
               
    finished = True
    UpdateStatus("Installation succesful on drive %s" % (targetdrive), "black")
    UpdateTargets()
    return

def myscrset(*scr):
    Listbox1.yview(*scr)

def cbk1(event):
    global targetdrive
    global finished

    if not finished:
        r = Listbox1.curselection()
        targetdrive = lstdrv[int(r[0])]

        for rt, dirs, files in os.walk(targetdrive):
            break

        # Is it empty?
        if len(files) <> 0 or len(dirs) <> 0:
            vardrive.set('Selected drive is not empty')
            LbDrive.config(fg='RED')
            targetdrive = ''
        else:
            vardrive.set('Selected drive:')
            LbDrive.config(fg='BLACK')
            
        UpdateSetupStatus()
    return

def mycopy(src, dst):
    try:
        fpin = open(src, 'rb')
    except:
        tkMessageBox.showerror("Error", "Error opening file")
        sys.exit(1)
        
    try:
        fpou = open(dst, 'wb')
    except:
        tkMessageBox.showerror("Error", "Error creating file")
        sys.exit(1)
        
    tm = os.stat(src).st_mtime

    s = dst[:45]

    if s <> dst:
        s += '...'
        
    UpdateStatus('Copying ' + s, 'red')
    
    while True:
        try:
            w = fpin.read()
        except:
            tkMessageBox.showerror("Error", "Error reading file")
            sys.exit(1)

        if w == '':
            break

        try:
            fpou.write(w)
        except:
            tkMessageBox.showerror("Error", "Error writing file")
            sys.exit(1)
            
    try:
        fpin.close()
    except:
        tkMessageBox.showerror("Error", "Error closing input file")
        sys.exit(1)
        
    try:
        fpou.close()
    except:
        tkMessageBox.showerror("Error", "Error closing output file file")
        sys.exit(1)


    os.utime(dst, (tm, tm))
    return

def UpdateStatus(msg, color):
    varstatus.set('Status: ' + msg)
    LbStatus.config(fg=color)
    LbStatus.update()
    return

def UpdateSetupStatus():
    Button2.config(state='disabled')
    
    if targetdrive <> '' and tmpdir <> '':
        s = ('Ready to install', 'black')
        Button2.config(state='active')

    elif targetdrive == '' and tmpdir == '':
        s = ('Select ISO file and targer drive', 'red')

    elif targetdrive == '':
        s = ('Select target drive', 'red')
    else:
        s = ('Select ISO file', 'red')

    UpdateStatus(s[0], s[1])
    return

def change(a=0):
    #print a, ## debug
    lbl.config(fg = "black" if a & 1 else "red")
    
    if a < 10:
        lbl.after(400,change, a + 1)
    
def UpdateTargets():
    global lstdrv
    
    lstdrv = GetListRemovableDrives()

    n = Listbox1.size()

    if n > 0:
        Listbox1.delete(0, n - 1)

    for p in lstdrv:
        try:
            f = win32api.GetDiskFreeSpaceEx(p)
            s = "%s       (%0.1f/%0.1fMB)" % (p, f[2]/1024.0/1024.0, f[1]/1024.0/1024.0)
        except:
            s = "%s        ***ERROR***" % (p) 
            
        Listbox1.insert(END, s)

    return

##########################################################
# Initializevariables
##########################################################

lstdrv = GetListRemovableDrives()

targetdrive = ''
tmpdir = ''
finished = False
ftplst = []

fw = None
fn = None

##########################################################
# Build GUI items
##########################################################

root = Tk()

root.title("Tiny Core Linux USB installer")

# Build menu

menubar = Menu(root)

style = ttk.Style()
style.configure("S1", background="white")

filemenu = Menu(menubar, tearoff = 0)
#filemenu.add_command(label = "Open", command = menuopen)
#filemenu.add_command(label = "Save", command = menusave)
filemenu.add_command(label = "Check MD5", command = menuchkmd5)

filemenu.entryconfig(0, state=DISABLED)
                     
filemenu.add_command(label = "Exit", command = menuexit)
menubar.add_cascade(label = "File", menu = filemenu)

helpmenu = Menu(menubar, tearoff = 0)
helpmenu.add_command(label = "Current TC version", command = menutcversion)
helpmenu.add_command(label = "About", command = menuabout)
menubar.add_cascade(label = "Help", menu = helpmenu)

root.config(menu = menubar)

# Build frames

#Frame1 = LabelFrame(root, text=' Source ')
#Frame1.grid(row = 0, column = 0)

#Frame2 = LabelFrame(root, text=' Target ', width=020)
#Frame2.grid(row = 1, column = 0, sticky=W)

#Frame3 = LabelFrame(root, text=' Options ')
#Frame3.grid(row = 2, column = 0)

#Frame4 = LabelFrame(root, text=' Status ')
#Frame4.grid(row = 3, column = 0, sticky=W, columnspan=2)

LbHead1 = Label(root, text="Select Tiny Core ISO image file to install")
#LbHead1.grid(row = 0, column = 0, sticky = W, columnspan = 3)
LbHead1.config(fg='RED')

Button1 = Button(root, text="BROWSE", command=callback1)
Button1.grid(row = 1, column = 2, sticky = E, padx=4, pady=4, columnspan=2)

Button2 = Button(root, text="INSTALL", command=callback2)
Button2.grid(row = 6, column = 2, sticky = W, padx=4, pady=4)

variso = StringVar()
variso.set('Select Tiny Core ISO image file to install')
LbISOfile = Label(root, textvariable=variso,  width=50, anchor=W, bg='WHITE')
LbISOfile.grid(row = 1, column = 0, sticky = W, columnspan = 2)
LbISOfile.config(fg='RED')

# Bottom status line

lst = []

# Removable media selector list box

vardrive = StringVar()
vardrive.set('Select target removable drive')
LbDrive = Label(root, textvariable=vardrive)
LbDrive.grid(row = 2, column = 0, sticky = W)
LbDrive.config(fg='RED')

varstatus = StringVar()
varstatus.set('')
LbStatus = Label(root, textvariable=varstatus)
LbStatus.grid(row = 6, column = 0, sticky = W, columnspan = 2)

###################
varlbl = StringVar()
varlbl.set('Hi there')
lbl = Label(root, textvariable=varlbl)
#lbl.grid(row = 7, column = 0, sticky = W, columnspan = 2)

#Listbox1 = Listbox(root, height=min(len(lstdrv), 3))
Listbox1 = Listbox(root, height=5, )
Listbox1.grid(row = 3, column = 0, sticky = EW, columnspan=2)

UpdateTargets()
    
#Listbox1.bind('<Button-1>', cbk1)
Listbox1.bind('<Double-Button-1>', cbk1)
Listbox1.bind('<Return>', cbk1)

# Define scrollbar

if len(lstdrv) > 0:
    scrollbar = Scrollbar(root)
    scrollbar.grid(row =3, column = 2, sticky = N+S+W)
    scrollbar.config( command = myscrset )

# Check button

ModeVar1 = IntVar()
ModeVar1.set(1)
#ChkBtn1 = Checkbutton(root, text = "Create TCE directory ", variable = ModeVar1)
#ChkBtn1.grid(row = 5, column = 0, sticky = W, padx = 2, pady = 2, columnspan=3)

change()

UpdateSetupStatus()

root.resizable(False, False)
root.mainloop()

# Cleanup

if tmpdir <> '':
    shutil.rmtree(tmpdir)

