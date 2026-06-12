
#!/usr/bin/env python3
# GUI-only launcher for video_slow_reverse with full error dialogs
import subprocess, sys, shutil, traceback
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

def show_log_window(title, text):
    win = tk.Toplevel()
    win.title(title)
    win.geometry("900x500")
    txt = scrolledtext.ScrolledText(win, wrap="word")
    txt.insert("1.0", text)
    txt.config(state="disabled")
    txt.pack(fill="both", expand=True)
    def copy_all():
        win.clipboard_clear()
        win.clipboard_append(text)
        messagebox.showinfo("Готово", "Скопировано")
    btn = tk.Button(win, text="Копировать", command=copy_all)
    btn.pack()
    win.attributes("-topmost", True)
    win.focus_force()

def run_ffmpeg(input_file, output_file, speed):
    def detect_audio(p):
        try:
            pr = subprocess.run(
                ["ffprobe","-v","error","-select_streams","a","-show_entries","stream=index","-of","csv=p=0",p],
                stdout=subprocess.PIPE, text=True
            )
            return bool(pr.stdout.strip())
        except:
            return True

    if shutil.which("ffmpeg") is None:
        raise EnvironmentError("FFmpeg не найден")

    has_audio = detect_audio(input_file)
    if has_audio:
        filter_str = (
            f"[0:v]split=2[vA][vB];"
            f"[vA]setpts=PTS/{speed}[v1];"
            f"[vB]setpts=PTS/{speed},reverse[v2];"
            f"[0:a]asplit=2[aA][aB];"
            f"[aA]atempo={speed}[a1];"
            f"[aB]atempo={speed},areverse[a2];"
            f"[v1][a1][v2][a2]concat=n=2:v=1:a=1[outv][outa]"
        )
    else:
        filter_str = (
            f"[0:v]split=2[vA][vB];"
            f"[vA]setpts=PTS/{speed}[v1];"
            f"[vB]setpts=PTS/{speed},reverse[v2];"
            f"[v1][v2]concat=n=2:v=1:a=0[outv]"
        )

    cmd = ["ffmpeg","-y","-i",input_file,"-filter_complex",filter_str,"-map","[outv]"]
    if has_audio: cmd+=["-map","[outa]"]
    cmd+=["-c:v","libx264","-crf","18","-preset","medium"]
    if has_audio: cmd+=["-c:a","aac","-b:a","192k"]
    cmd.append(output_file)

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    log=[]
    for line in proc.stdout:
        log.append(line)
    rc=proc.wait()
    log_text="".join(log)
    if rc!=0:
        raise RuntimeError("FFmpeg завершился с ошибкой:\n\n"+log_text)
    return log_text

def start_process():
    try:
        inp = input_path.get()
        outp = output_path.get()
        sp = float(speed_entry.get())

        if not Path(inp).exists():
            messagebox.showerror("Ошибка","Входной файл не найден")
            return

        log = run_ffmpeg(inp, outp, sp)
        show_log_window("Готово", "Видео успешно обработано!\n\n"+log)

    except Exception as e:
        tb = traceback.format_exc()
        show_log_window("Ошибка", f"{e}\n\n{tb}")

root = tk.Tk()
root.title("Видео — замедление + реверс")
root.geometry("600x250")

tk.Label(root, text="Выберите входное видео:").pack()
input_path = tk.Entry(root, width=80)
input_path.pack()
tk.Button(root, text="Обзор", command=lambda: input_path.insert(0, filedialog.askopenfilename())).pack()

tk.Label(root, text="Выберите выходной файл:").pack()
output_path = tk.Entry(root, width=80)
output_path.pack()
tk.Button(root, text="Сохранить как", command=lambda: output_path.insert(0, filedialog.asksaveasfilename(defaultextension=".mp4"))).pack()

tk.Label(root, text="Скорость (например 0.7):").pack()
speed_entry = tk.Entry(root)
speed_entry.insert(0,"0.7")
speed_entry.pack()

tk.Button(root, text="Запустить", command=start_process).pack(pady=10)

root.mainloop()
