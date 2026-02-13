import tkinter as tk
import random
import time


def create_tip_window(main_window, tips, bg_colors):
    window_width = 380
    window_height = 90
    x = random.randint(-30, 1500)
    y = random.randint(-20, 900)

    window = tk.Toplevel(main_window)
    window.title("温馨提示")
    window.geometry(f"{window_width}x{window_height}+{x}+{y}")
    window.attributes('-topmost', True)

    tip = random.choice(tips)
    bg = random.choice(bg_colors)

    tk.Label(
        window,
        text=tip,
        bg=bg,
        font=('微软雅黑', 16),
        width=38,
        height=3
    ).pack()

    return window


def close_windows_one_by_one(all_windows, index=0, delay=10):
    if index < len(all_windows):
        window = all_windows[index]
        if window.winfo_exists():
            window.destroy()
        all_windows[0].master.after(delay, close_windows_one_by_one, all_windows, index + 1, delay)
    else:
        create_final_window(all_windows[0].master)


def create_final_window(main_window):
    final_width = 380
    final_height = 90
    screen_width = main_window.winfo_screenwidth()
    screen_height = main_window.winfo_screenheight()

    x = (screen_width - final_width) // 2
    y = (screen_height - final_height) // 2

    final_window = tk.Toplevel(main_window)
    final_window.geometry(f"{final_width}x{final_height}+{x}+{y}")
    final_window.attributes('-topmost', True)

    tk.Label(
        final_window,
        text='高考加油',
        bg='lightpink',
        font=('微软雅黑', 18, 'bold'),
        width=38,
        height=3
    ).pack()


def main():
    main_window = tk.Tk()
    main_window.withdraw()  # 隐藏主窗口

    tips = ['多喝水','保持好心情','梦想成真', '万事顺遂', '别熬夜','好好学习','注意保暖']

    bg_colors = ["#C3C7CE","#E2D8DB","#E5DCD2","#C2C9C0","#F0EEE9","#D6B9B3"]

    all_windows = []

    # 创建100个提示窗口
    for _ in range(70):
        window = create_tip_window(main_window, tips, bg_colors)
        all_windows.append(window)
        main_window.update()
        time.sleep(0.1)

    # 2秒后开始逐个关闭窗口
    main_window.after(1000, close_windows_one_by_one, all_windows)

    main_window.mainloop()
if __name__ == "__main__":
    main()
