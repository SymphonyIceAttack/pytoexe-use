import time;
import urllib.request;
import filecmp;
from pathlib import Path;
import os;
import shutil;
import subprocess
from datetime import datetime


Running = True
Root = Path(Path(__file__).resolve().parent,"Views")
print("\033[?25l", end="")

def Format(string:str = "",before = "",end = ""):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return before +"["+timestamp+"]\t" + string + end

BaseLink = "https://wavespray.dathost.net/fastdl/teamfortress2/679d9656b8573d37aa848d60/"

materialslink = BaseLink+"materials/"
soundlink = BaseLink+"sound/"

ViewLink = materialslink + "view.vtf"
ViewSoundLink = soundlink + "view.wav"

for t in range(30):
    print()

def DownloadView():
        Root.mkdir(parents=True,exist_ok=True);
        print(Format("Trying...","\033[1A\033[2K"))
        Folders = []
        for name in os.listdir(Root):
            if os.path.isdir(Path(Root,name)) and name.isdigit():
                Folders.insert(int(name),name)       
        if Folders == []:
            Folders = ["0"]
        LatestFolder = Path(Root,Folders[len(Folders) - 1])
        LastestView = Path(LatestFolder,"view.vtf")

        NextFolder = Path(Root,str(int(Folders[len(Folders) - 1]) + 1))

        Temp = Path(Root,"temp")
        Temp.mkdir(parents=True, exist_ok=True)
        shouldremove = True;
        ViewVtf = Path(Root,urllib.request.urlretrieve(ViewLink,Path(Temp,"view.vtf"))[0])
        ViewSound = Path(Root,urllib.request.urlretrieve(ViewSoundLink,Path(Temp,"view.wav"))[0])


        if (not LastestView.is_file() or not filecmp.cmp(LastestView,ViewVtf,shallow=False)):
            print(Format("Change Found!\a\a\a\n","\033[1A\033[2K"))

            shouldremove = False
            NextFolder.mkdir(parents=True, exist_ok=True)

            with open(Path(NextFolder,datetime.now().strftime("%Y-%m-%d %H-%M-%S")),"x"):
                pass

            shutil.move(ViewVtf,NextFolder)
            shutil.move(ViewSound,NextFolder)
            
            subprocess.run([
                "no_vtf",
                "--animate",
                "--fps", "10",
                Path(NextFolder,"view.vtf"),
                "--always-write",
                "-f", "gif"
            ])

            

        if (shouldremove):
            print(Format("No Change Found.","\033[1A\033[2K"))
            ViewVtf.unlink()
            ViewSound.unlink()

        Temp.rmdir()
    

try:
    while Running:
        DownloadView();
        time.sleep(1)

except KeyboardInterrupt:
   print("\x1b[?25h",end="")
   Running = False