import os
import shutil
import tempfile
import ctypes

def delete_temp_files():
    temp_dirs = [
        tempfile.gettempdir(),
        os.environ.get('TEMP'),
        os.environ.get('TMP'),
        r"C:\Windows\Temp"
    ]

    print("\n🧹 Cleaning Temp Files...")
    for temp_dir in temp_dirs:
        if temp_dir and os.path.exists(temp_dir):
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    try:
                        os.remove(os.path.join(root, file))
                    except:
                        pass
                for dir in dirs:
                    shutil.rmtree(os.path.join(root, dir), ignore_errors=True)

    print("✅ Temp files cleaned!")

def clear_prefetch():
    prefetch_path = r"C:\Windows\Prefetch"
    print("\n⚡ Cleaning Prefetch...")
    
    if os.path.exists(prefetch_path):
        for file in os.listdir(prefetch_path):
            try:
                os.remove(os.path.join(prefetch_path, file))
            except:
                pass

    print("✅ Prefetch cleaned!")

def clear_dns_cache():
    print("\n🌐 Flushing DNS Cache...")
    os.system("ipconfig /flushdns")
    print("✅ DNS cache cleared!")

def clear_windows_cache():
    print("\n🗂️ Clearing Windows Cache...")
    
    cache_paths = [
        r"C:\Windows\SoftwareDistribution\Download"
    ]

    for path in cache_paths:
        if os.path.exists(path):
            for file in os.listdir(path):
                try:
                    file_path = os.path.join(path, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    else:
                        shutil.rmtree(file_path)
                except:
                    pass

    print("✅ Windows cache cleared!")

def empty_recycle_bin():
    choice = input("\n🗑️ Empty Recycle Bin? (yes/no): ").lower()
    
    if choice == "yes":
        ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 0x00000007)
        print("✅ Recycle Bin emptied!")
    else:
        print("❌ Skipped Recycle Bin.")

def main():
    print("=== Windows Optimizer Tool ===")

    delete_temp_files()
    clear_prefetch()
    clear_windows_cache()
    clear_dns_cache()
    empty_recycle_bin()

    print("\n🚀 System optimization complete!")

if __name__ == "__main__":
    main()