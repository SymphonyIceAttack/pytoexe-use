import os
import subprocess
import sys

def build():
    print("بدء عملية تحويل البرنامج إلى ملف تنفيذي (EXE)...")
    
    # تحديد الملف الرئيسي
    main_file = "main.py"
    
    # أوامر PyInstaller
    # --onefile: لدمج كل شيء في ملف واحد
    # --windowed: لمنع ظهور نافذة الكونسول السوداء عند التشغيل
    # --name: اسم البرنامج النهائي
    # --hidden-import: للتأكد من تضمين المكتبات التي قد لا يكتشفها تلقائياً
    
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name=EGX_Pro_Monitor",
        "--hidden-import=PyQt6",
        "--hidden-import=pandas",
        "--hidden-import=numpy",
        "--hidden-import=matplotlib",
        "--hidden-import=egxpy",
        "--hidden-import=tvdatafeed",
        "--hidden-import=plyer",
        main_file
    ]
    
    try:
        subprocess.check_call(cmd)
        print("\nتمت العملية بنجاح!")
        print("ستجد الملف التنفيذي في مجلد 'dist' باسم 'EGX_Pro_Monitor.exe'")
    except Exception as e:
        print(f"\nحدث خطأ أثناء العملية: {e}")

if __name__ == "__main__":
    os.chdir("/home/ubuntu/stock_monitor")
    build()
