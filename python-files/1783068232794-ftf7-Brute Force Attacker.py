import time
import os

def load_database():
    # 안드로이드 기본 다운로드 경로 및 일반 경로 후보군 정의
    possible_paths = [
        "C:/Kivy-2/data.txt",
        os.path.expanduser("C:/Kivy-1/data.txt"),
        "./data.txt"  # 현재 작업 디렉토리
    ]
    
    file_path = None
    for path in possible_paths:
        if os.path.exists(path):
            file_path = path
            break
            
    # 경로를 찾지 못했을 경우 수동 입력 요청
    if not file_path:
        print("[-] WARNING: Default data.txt path not found.")
        file_path = input("[+] Enter absolute path to data.txt: ").strip()
        if not os.path.exists(file_path):
            print(f"[-] ERROR: File not found at '{file_path}'.")
            return []
            
    
    records = []
    current_record = {}
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    if current_record:
                        records.append(current_record)
                        current_record = {}
                    continue
                
                if "=" in line:
                    key, val = line.split("=", 1)
                    current_record[key.strip().upper()] = val.strip()
                    
            if current_record:
                records.append(current_record)
    except Exception as e:
        print(f"[-] File read error: {e}")
        return []
            
    return records

def execute():
    print("==================================================")
    print("          BFA PROCESS AUDITOR v1.4.5              ")
    print("==================================================")
    
    # 설정 정보 입력
    target_url = input("[+] Target API URL      : ").strip()
    user_field = input("[+] Username Field Name : ").strip()
    pass_field = input("[+] Password Field Name : ").strip()
    target_user = input("[+] Target Account ID   : ").strip()
    
    print("\n[*] Initializing database stream...")
    db = load_database()
    if not db:
        print("[-] Execution aborted. Empty or missing database.")
        print("==================================================")
        return
    
    # 레코드 매칭 검증
    matched_key = None
    for item in db:
        if (item.get("API-URL") == target_url and
            item.get("USERNAME FILD") == user_field and
            item.get("PASSWORD FILD") == pass_field and
            item.get("USERNAME") == target_user):
            matched_key = item.get("PASSWORD")
            break

    print("[*] Launching brute force auditing sequence...")
    print("[*] Injecting payload vectors (Estimated time: 15s)...")
    print("--------------------------------------------------")
    
    # 15초 지연 및 진행 상황 연출
    duration = 180
    for i in range(duration):
        pct = int((i + 1) / duration * 100)
        print(f" -> Injecting block {i+1:02d}/{duration}... [{pct}%] Processing...", end="\r")
        time.sleep(1)
        
    print("\n--------------------------------------------------")
    
    if matched_key:
        print("[+] STATUS: SUCCESS (Credential key found)")
        print(f"[>] CREDENTIAL_KEY >> {matched_key}")
    else:
        print("[-] STATUS: FAILED")
        print("    [!] Reason: No matching record found in 'data.txt'.")
        print("    [!] Ensure inputs strictly match the database record.")
        
    print("==================================================")

if __name__ == "__main__":
    execute()
