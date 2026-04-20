import os
import psutil
import GPUtil
import shutil
from datetime import datetime

# --- CONFIGURATION ---
CLEANUP_TARGET = os.path.join(os.environ['USERPROFILE'], 'Downloads') # Example: Downloads folder
MAX_SIZE_GB = 10  # Delete files if folder is bigger than this
# ---------------------

def get_size(start_path='.'):
    """Calculates total size of a directory in bytes."""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    return total_size

def run_system_report():
    print(f"--- System Report ({datetime.now().strftime('%H:%M:%S')}) ---")
    
    # CPU Usage
    print(f"CPU Usage: {psutil.cpu_percent()}%")
    
    # RAM Usage
    ram = psutil.virtual_memory()
    print(f"RAM: {ram.percent}% used ({ram.available // (1024**2)}MB free)")
    
    # GPU Usage
    gpus = GPUtil.getGPUs()
    for gpu in gpus:
        print(f"GPU: {gpu.name} | Temp: {gpu.temperature}°C | Load: {gpu.load*100}%")
    
    # Storage Check & Cleanup
    folder_size_bytes = get_size(CLEANUP_TARGET)
    folder_size_gb = folder_size_bytes / (1024**3)
    
    print(f"Target Folder ({CLEANUP_TARGET}): {folder_size_gb:.2f} GB")
    
    if folder_size_gb > MAX_SIZE_GB:
        print(f"!!! Folder exceeds {MAX_SIZE_GB}GB. Starting cleanup...")
        for filename in os.listdir(CLEANUP_TARGET):
            file_path = os.path.join(CLEANUP_TARGET, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")
        print("Cleanup complete.")
    else:
        print("Storage is within safe limits.")

if __name__ == "__main__":
    run_system_report()