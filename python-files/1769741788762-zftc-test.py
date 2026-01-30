from ftplib import FTP
import os

# FTP 서버 정보
FTP_HOST = "192.168.0.29"
FTP_USER = "admin"
FTP_PASS = "admin"

# 전송할 파일 경로
LOCAL_FILE_PATH = r"Z:\test.txt"

# FTP 서버에 저장될 파일 이름
REMOTE_FILE_NAME = os.path.basename(LOCAL_FILE_PATH)

def upload_file():
    ftp = FTP()
    ftp.connect(FTP_HOST, 21)
    ftp.login(FTP_USER, FTP_PASS)
    ftp.set_pasv(True)  # 패시브 모드 (보통 필요)

    with open(LOCAL_FILE_PATH, "rb") as file:
        ftp.storbinary(f"STOR {REMOTE_FILE_NAME}", file)

    ftp.quit()
    print("파일 전송 완료!")

if __name__ == "__main__":
    upload_file()
