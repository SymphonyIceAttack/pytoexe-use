import tkinter as tk
import random
import time
import platform
message=["义父，我很想你", "我什么都愿意为你做", "刀山火海我也能走下去", "唯有片甲相伴，聊作慰藉", 
         "子熹，你亲亲我", "伤口疼", "我还能等到你吗", "你扶着我就好", "你恨先帝吗", "你答应我的事呢", 
         "好将军，不是说要疼我吗", "...怕", "你说这话不是戳我的心吗", "大梁的气运站在我身后", "你亲我了",
         "我可以做到的", "你相信我", "经年痴心妄想", "你要死，我给你殉葬", "义父尊前...", "偌大京城，远近无亲", "我只有你了"]
morandi_colors=["#E8DCCA", "#D4C2B8", "#C0B09E", "#A99E8F", "#B8B9AB", "#9A9CAA", "#B0A0A8", 
                "#CFAF9B", "#D9C7B8", "#B5A4A7"]
def create_safe_windows():
    windows=[]
    window_count=99
    for i in range(window_count):
        try:
            win=tk.Toplevel()
            width=win.winfo_screenwidth()
            height=win.winfo_screenheight()
            win_width=random.randint(200,400)
            win_height=random.randint(80,150)
            x=random.randrange(0, width-win_width)
            y=random.randrange(0, height-win_height)
            win.title("你在哪？")
            win.geometry(f"{win_width}x{win_height}+{x}+{y}")
            bg_color=random.choice(morandi_colors)
            msg=random.choice(message)
            system=platform.system()
            if system=="Darwin":
                chinese_font="STXingkai"
            elif system=="Windows":
                chinese_font="行楷"
            else:
                chinese_font="WenQuanYi Zen Hei"
            base_size=min(win_width, win_height)
            font_size=max(20, min(30, base_size//20))
            label=tk.Label(win,
                           text=msg,
                           bg=bg_color,
                           fg="black",
                           font=(chinese_font, font_size),
                           wraplength=win_width-20,
                           justify="center")
            label.pack(fill="both", expand=True)
            win.after(random.randint(10000, 30000), win.destroy)
            windows.append(win)
            win.update()
            time.sleep(0.1)
        except Exception as e:
            print(f"创建窗口{i}失败{e}")
            continue
    return windows
root=tk.Tk()
root.withdraw()
windows=create_safe_windows()
try:
    root.mainloop()
except Exception as e:
    print(f"主循环错误：{e}")