import tkinter as tk
from tkinter import messagebox
import random

# ===== 150개 문장 =====
messages = [
    "힘내세요.", "좋은 하루 보내세요.", "오늘도 잘 해내고 있어요.", "당신은 충분히 잘하고 있습니다.",
    "지금 이대로도 괜찮아요.", "오늘은 분명 의미 있는 하루입니다.", "조금 느려도 괜찮습니다.",
    "당신의 노력은 헛되지 않습니다.", "스스로를 믿어도 됩니다.", "오늘도 한 걸음 나아갔습니다.",
    "잘 버텨주셔서 감사합니다.", "내일은 더 나아질 거예요.", "당신은 소중한 존재입니다.",
    "지금도 충분히 가치 있습니다.", "오늘 하루도 수고 많으셨어요.", "작은 성취도 충분히 대단합니다.",
    "당신은 생각보다 강합니다.", "지금의 선택은 의미가 있습니다.", "쉬어가도 괜찮습니다.",
    "오늘을 살아낸 것만으로도 잘했습니다.", "당신의 마음도 존중받아야 합니다.",
    "잘하고 있다는 사실을 잊지 마세요.", "오늘의 당신을 응원합니다.",
    "충분히 노력하고 있습니다.", "지금 이 순간도 소중합니다.",
    "당신의 속도는 올바릅니다.", "오늘도 최선을 다했습니다.",
    "괜찮아질 시간은 분명 옵니다.", "당신은 혼자가 아닙니다.",
    "오늘의 선택은 틀리지 않았습니다.", "지금도 성장하고 있습니다.",
    "스스로에게 조금 더 관대해지세요.", "오늘도 의미 없는 하루는 아닙니다.",
    "당신의 진심은 전해질 것입니다.", "잘 견뎌내고 있습니다.",
    "오늘의 당신은 충분합니다.", "지금도 잘 해내고 있어요.",
    "오늘 하루를 자랑스러워해도 됩니다.", "당신은 계속 나아가고 있습니다.",
    "괜찮다고 말해줘도 됩니다.", "오늘의 노력은 내일로 이어집니다.",
    "당신의 선택을 믿어보세요.", "지금의 고민도 언젠가는 지나갑니다.",
    "마음이 지쳐도 괜찮습니다.", "충분히 잘해왔습니다.",
    "당신의 존재는 의미가 있습니다.", "오늘을 버텨낸 것만으로도 훌륭합니다.",
    "당신은 포기하지 않았습니다.", "오늘도 스스로를 지켜냈습니다.",
    "잘하고 있으니 걱정하지 마세요.", "당신의 속도대로 가면 됩니다.",
    "당신은 계속 앞으로 가고 있습니다.", "지금의 모습도 충분히 좋습니다.",
    "오늘도 의미 있는 하루였습니다.", "당신은 이미 많은 걸 해냈습니다.",
    "오늘도 자신에게 박수를 보내세요.",
    "당신의 노력은 반드시 남습니다.",
    "오늘 하루도 정말 수고 많으셨습니다."
]

# ===== 상태 =====
remaining = 0
timer_id = None

def countdown():
    global remaining
    if remaining > 0:
        remaining -= 1
        timer_label.config(text=f"다음 메시지까지: {remaining}초")
        root.after(1000, countdown)
    else:
        timer_label.config(text="메시지 열기 가능")

def open_message():
    global remaining
    if remaining > 0:
        messagebox.showinfo("알림", f"아직 {remaining}초 남았습니다.")
        return

    messagebox.showinfo("메시지", random.choice(messages))
    remaining = 60
    timer_label.config(text=f"Until the next message: {remaining}second")
    countdown()

# ===== GUI =====
root = tk.Tk()
root.title("Random Message Box")
root.geometry("320x180")

open_btn = tk.Button(root, text="Open Message", command=open_message, width=20, height=2)
open_btn.pack(pady=20)

timer_label = tk.Label(root, text="Message can be opened", font=("Arial", 12))
timer_label.pack(pady=10)

root.mainloop()
