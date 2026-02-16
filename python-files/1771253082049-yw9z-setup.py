import sys
from cx_Freeze import setup, Executable

# Dependencies
build_exe_options = {
    "packages": ["os", "sys", "json", "threading", "time", 
                 "PyQt5", "vk_api", "keyboard", "requests"],
    "excludes": [],
    "include_files": []
}

# Base for Windows
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="VK Music Player",
    version="1.0",
    description="VK Music Player with Hotkeys",
    options={"build_exe": build_exe_options},
    executables=[Executable("vk_music_player.py", base=base, icon="icon.ico")]
)