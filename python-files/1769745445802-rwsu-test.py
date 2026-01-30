import shutil
import os

# 원본 파일 경로
source_file = r"Z:\test.txt"

# 대상 폴더 경로
destination_dir = r"D:\"

# 대상 파일 전체 경로
destination_file = os.path.join(destination_dir, os.path.basename(source_file))

def copy_file():
    shutil.copy2(source_file, destination_file)
    print("파일 복사 완료!")

if __name__ == "__main__":
    copy_file()
