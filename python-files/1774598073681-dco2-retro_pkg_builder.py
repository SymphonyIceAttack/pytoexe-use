import os, shutil, tkinter as tk
from tkinter import filedialog, messagebox

# Core mapping for auto-detect
CORES = {
    ".nes": "fceumm_libretro.self",
    ".sfc": "snes9x_libretro.self",
    ".smc": "snes9x_libretro.self",
    ".gb":  "gambatte_libretro.self",
    ".gbc": "gambatte_libretro.self",
    ".gba": "mgba_libretro.self",
    ".md":  "genesis_plus_gx_libretro.self",
    ".gen": "genesis_plus_gx_libretro.self",
    ".cue": "mednafen_psx_libretro.self",
    ".iso": "mednafen_psx_libretro.self",
}

def select_file():
    path = filedialog.askopenfilename()
    rom_path.set(path)
    ext = os.path.splitext(path)[1].lower()
    console.set("Unsupported" if ext not in CORES else ext[1:].upper())

def build_pkg():
    rom = rom_path.get()
    if not os.path.isfile(rom):
        messagebox.showerror("Error", "No ROM selected")
        return
    ext = os.path.splitext(rom)[1].lower()
    if ext not in CORES:
        messagebox.showerror("Error", "Unsupported ROM")
        return

    core = CORES[ext]
    title = title_entry.get() or os.path.splitext(os.path.basename(rom))[0]
    title_id = id_entry.get() or "RETRO" + title[:5].upper()

    build = "build"
    usrdir = os.path.join(build,"USRDIR")
    os.makedirs(usrdir, exist_ok=True)
    shutil.copy(rom, os.path.join(usrdir, os.path.basename(rom)))
    with open(os.path.join(usrdir,"launch.sh"),"w") as f:
        f.write(f"/retroarch/retroarch -L /cores/{core} /USRDIR/{os.path.basename(rom)}\n")

    messagebox.showinfo("Done", f"Build ready: {title_id}")

# GUI
root = tk.Tk()
root.title("Retro → PS3 PKG")
root.geometry("500x300")
root.configure(bg="#2c2c2c")  # dark grey

# Glass effect frame
frame = tk.Frame(root, bg="#3c3c3c", bd=1, relief="ridge")
frame.place(relx=0.05, rely=0.05, relwidth=0.9, relheight=0.9)

rom_path = tk.StringVar()
console = tk.StringVar()

tk.Label(frame, text="ROM:", bg="#3c3c3c", fg="white").pack(pady=5)
tk.Entry(frame, textvariable=rom_path, width=50, bg="#2c2c2c", fg="white").pack()
tk.Button(frame, text="Select ROM", command=select_file).pack(pady=5)

tk.Label(frame, text="Console:", bg="#3c3c3c", fg="white").pack()
tk.Label(frame, textvariable=console, bg="#3c3c3c", fg="white").pack(pady=5)

tk.Label(frame, text="Title:", bg="#3c3c3c", fg="white").pack()
title_entry = tk.Entry(frame, width=30, bg="#2c2c2c", fg="white")
title_entry.pack(pady=2)

tk.Label(frame, text="Title ID:", bg="#3c3c3c", fg="white").pack()
id_entry = tk.Entry(frame, width=30, bg="#2c2c2c", fg="white")
id_entry.pack(pady=2)

tk.Button(frame, text="Build PKG", command=build_pkg, bg="#5555ff", fg="white").pack(pady=10)

root.mainloop()

REM Create build directories
if not exist build mkdir build
if not exist build\USRDIR mkdir build\USRDIR

REM Copy icon
copy "%ICON%" build\ICON0.PNG /Y

REM Create launch.cfg
(
echo core=%CORE%
echo rom=%ROM%
echo aspect_ratio=16:9
) > build\USRDIR\launch.cfg

REM Create PARAM.SFO
(
echo TITLE=%TITLE%
echo TITLE_ID=%ID%
echo CATEGORY=HG
) > build\PARAM.SFO

REM Build PKG using pkg.py (requires pkg.py and scetool.exe in same folder)
pkg.py --contentid EP0000-%ID%_00-RETROFORWARDER0000 "build" "%TITLE%.pkg"

echo PKG build finished. Check the folder for %TITLE%.pkg
pause