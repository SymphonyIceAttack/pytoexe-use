import platform
import subprocess
import sys


#!/usr/bin/env python3
"""
Shutdown script: prompts for confirmation then issues an OS shutdown command.
Use responsibly. May require administrative privileges.
"""

def confirm():
    return input("This will shut down the computer. Type YES to proceed: ").strip().upper() == "YES"

def shutdown():
    osname = platform.system()
    if osname == "Windows":
        cmd = "shutdown /s /t 0"
    elif osname in ("Linux", "Darwin"):
        cmd = "shutdown -h now"
    else:
        print("Unsupported OS:", osname)
        sys.exit(1)

    print("Running:", cmd)
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError:
        print("Failed to run shutdown command. You may need administrative privileges.")
        sys.exit(1)

if __name__ == "__main__":
    if confirm():
        shutdown()
    else:
        print("Aborted.")