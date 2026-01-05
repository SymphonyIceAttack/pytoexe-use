import psutil
import tkinter as tk
from tkinter import messagebox

exe_name = "ROM.exe"  # 종료할 클라이언트 exe 이름으로 바꿔주세요

def kill_instance(instance_number):
    # 실행 중인 exe_name 프로세스 리스트 가져오기
    procs = [p for p in psutil.process_iter(['pid', 'name']) if p.info['name'] == exe_name]
    
    if len(procs) < instance_number:
        messagebox.showinfo("알림", f"{instance_number}번 클라이언트는 실행 중이 아닙니다.")
        return
    
    try:
        procs[instance_number - 1].kill()
        messagebox.showinfo("알림", f"{exe_name} {instance_number}번 클라이언트를 종료했습니다.")
    except Exception as e:
        messagebox.showerror("오류", f"종료 실패: {e}")

# GUI 생성
root = tk.Tk()
root.title("클라이언트 종료 도구")
root.geometry("300x250")

for i in range(1, 6):  # 1~5번 버튼 생성
    tk.Button(root, text=f"{i}번 클라이언트 종료", command=lambda x=i: kill_instance(x)).pack(pady=10, fill='x')

root.mainloop()
