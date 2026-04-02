import subprocess
import time
import random

# List of commands that look "techy" or busy
commands = [
    "dir /s",          # Lists every file on the drive
    "tree",            # Shows folder structure visually
    "netstat -an",     # Shows active network connections
    "systeminfo",      # Displays system specifications
    "ipconfig /all"    # Displays network adapter info
]

def launch_prank(instances=10):
    print("Initializing system bypass...")
    time.sleep(2)
    
    for i in range(instances):
        # Pick a random command from the list
        cmd = random.choice(commands)
        
        # 'start' opens a new window, /k keeps it open after execution
        subprocess.Popen(f"start cmd /k {cmd}", shell=True)
        
        # Small delay so they don't all pop at once
        time.sleep(0.3)

if __name__ == "__main__":
    launch_prank(15)