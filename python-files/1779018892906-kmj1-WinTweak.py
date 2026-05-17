import os
import shutil

tempPath = rf"{os.getenv('TEMP')}"
winTempPath = r"C:\Windows\Temp"
prefetchPath = r"C:\Windows\Prefetch"

def cleanDir(folder):
    delFileCount = 0
    delFolderCount = 0

    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
                delFileCount = delFileCount + 1

            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
                delFolderCount = delFolderCount + 1

        except Exception as e:
            pass
    
    print(f"Successfully deleted {str(delFileCount + delFolderCount)} objects in \033[93m{folder}\033[0m")

print("\033[93mWinTweak v1.0a\033[0m")
print()
print("\033[36mPERFORMANCE --------\033[0m")
print(" [1] System Cleanup")
print("\033[36mOTHER --------------\033[0m")
print(" [2] Exit")
print("\033[36m--------------------\033[0m")
print()

while True:
    inp = input("Select: ")

    if inp == "1":
        cleanDir(tempPath)
        cleanDir(winTempPath)
        cleanDir(prefetchPath)
    elif inp == "2":
        exit()
    else:
        print("wrong choice")