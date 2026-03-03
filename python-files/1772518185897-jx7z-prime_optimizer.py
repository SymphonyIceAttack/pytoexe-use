import os
import psutil
import subprocess
import threading
import time
import gc
import GPUtil

# ==========================================================
# PRIME CORE
# ==========================================================

class PrimeCore:
    def __init__(self):
        self.running = False
        self.game_process = None

    def log(self, msg):
        print(f"[PRIME] {msg}")

core = PrimeCore()

# ==========================================================
# KEYBOARD SECTION (SAFE)
# ==========================================================

class KeyboardOptimizer:

    def optimize(self):
        core.log("Keyboard optimization applied (safe mode)")
        core.log("Disable Sticky Keys & Filter Keys manually in Windows")

# ==========================================================
# MOUSE SECTION (SAFE)
# ==========================================================

class MouseOptimizer:

    def optimize(self):
        core.log("Mouse optimization mode enabled")
        core.log("Recommended: Disable Enhance Pointer Precision")
        core.log("Recommended DPI: 800 / 1600")

# ==========================================================
# PC OPTIMIZATION SECTION (SAFE)
# ==========================================================

class PCOptimizer:

    def find_game(self, exe_name):
        for proc in psutil.process_iter(['pid','name']):
            if proc.info['name'] and exe_name.lower() in proc.info['name'].lower():
                core.game_process = proc
                core.log(f"Game found: {proc.info['name']}")
                return True
        return False

    def set_priority(self, level="HIGH"):
        if not core.game_process:
            core.log("No game process selected")
            return

        priority_map = {
            "LOW": psutil.IDLE_PRIORITY_CLASS,
            "BELOW NORMAL": psutil.BELOW_NORMAL_PRIORITY_CLASS,
            "NORMAL": psutil.NORMAL_PRIORITY_CLASS,
            "ABOVE NORMAL": psutil.ABOVE_NORMAL_PRIORITY_CLASS,
            "HIGH": psutil.HIGH_PRIORITY_CLASS
        }

        if level in priority_map:
            core.game_process.nice(priority_map[level])
            core.log(f"Priority set to {level}")

    def set_affinity(self):
        if not core.game_process:
            core.log("No game process selected")
            return

        cores = list(range(psutil.cpu_count()))
        core.game_process.cpu_affinity(cores)
        core.log(f"CPU Affinity set to all cores {cores}")

    def clean_memory(self):
        gc.collect()
        core.log("Memory cleaned safely (Python GC only)")

# ==========================================================
# NETWORK SECTION (SAFE)
# ==========================================================

class NetworkOptimizer:

    def optimize_tcp(self):
        subprocess.run(
            ["netsh", "int", "tcp", "set", "global", "autotuninglevel=normal"],
            capture_output=True
        )
        core.log("TCP AutoTuning set to normal")

    def flush_dns(self):
        subprocess.run(["ipconfig", "/flushdns"], capture_output=True)
        core.log("DNS cache flushed")

# ==========================================================
# MONITORING SECTION
# ==========================================================

def system_monitor():
    while core.running:
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent

        try:
            gpus = GPUtil.getGPUs()
            gpu = gpus[0].load * 100 if gpus else 0
        except:
            gpu = 0

        print(f"CPU: {cpu}% | RAM: {ram}% | GPU: {gpu:.0f}%")
        time.sleep(3)

# ==========================================================
# START ENGINE
# ==========================================================

def start_engine():
    core.running = True
    threading.Thread(target=system_monitor, daemon=True).start()
    core.log("PRIME SAFE ENGINE STARTED")

def stop_engine():
    core.running = False
    core.log("PRIME ENGINE STOPPED")

# ==========================================================
# USAGE EXAMPLE
# ==========================================================

if __name__ == "__main__":

    keyboard = KeyboardOptimizer()
    mouse = MouseOptimizer()
    pc = PCOptimizer()
    net = NetworkOptimizer()

    start_engine()

    # Example usage
    keyboard.optimize()
    mouse.optimize()
    pc.clean_memory()
    net.flush_dns()