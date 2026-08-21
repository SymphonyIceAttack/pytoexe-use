import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import re
import json
import os

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.douyin.com/"
}

def extract_douyin_video_id(url: str):
    pat = re.compile(r'video/(\d+)')
    match = pat.search(url)
    if match:
        return match.group(1)
    return None

def get_douyin_subtitle(video_id: str):
    api_url = f"https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id={video_id}"
    resp = requests.get(api_url, headers=HEADERS, timeout=15)
    data = resp.json()
    aweme = data.get("aweme_detail", {})
    text_raw = aweme.get("desc", "")

    subtitle_infos = aweme.get("subtitle_infos", [])
    if not subtitle_infos:
        return False, text_raw, None, "该视频没有内置字幕，仅拿到简介"

    sub_info = subtitle_infos[0]
    subtitle_url = sub_info.get("subtitle_url")
    if not subtitle_url:
        return False, text_raw, None, "字幕地址为空"

    sub_resp = requests.get(subtitle_url, headers=HEADERS, timeout=15)
    sub_json = sub_resp.json()
    blocks = sub_json.get("blocks", [])

    full_text = []
    srt_lines = []
    idx = 1
    for blk in blocks:
        start = blk["start"] / 1000.0
        end = blk["end"] / 1000.0
        txt = blk["text"]
        full_text.append(txt)

        def format_sec(s):
            h = int(s // 3600)
            m = int((s % 3600) // 60)
            sec = s % 60
            return f"{h:02d}:{m:02d}:{sec:06.3f}".replace(".",",")
        srt_lines.append(f"{idx}")
        srt_lines.append(f"{format_sec(start)} --> {format_sec(end)}")
        srt_lines.append(txt)
        srt_lines.append("")
        idx +=1

    all_txt = "\n".join(full_text)
    srt_content = "\n".join(srt_lines)
    return True, all_txt, srt_content, "成功抓取字幕"


class SubtitleGrabApp:
    def __init__(self, root):
        self.root = root
        self.root.title("视频字幕提取工具【抓内置字幕版】")
        self.root.geometry("620x380")

        ttk.Label(root, text="输入视频链接：").pack(pady=5)
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(root, textvariable=self.url_var, width=85)
        self.url_entry.pack(pady=2)

        self.btn_frame = ttk.Frame(root)
        self.btn_frame.pack(pady=8)
        self.run_btn = ttk.Button(self.btn_frame, text="抓取字幕", command=self.do_grab)
        self.run_btn.grid(row=0, column=0, padx=8)

        self.result_text = tk.Text(root, wrap=tk.WORD)
        self.result_text.pack(padx=10,pady=5,fill=tk.BOTH,expand=True)

        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(root, textvariable=self.status_var).pack()

    def do_grab(self):
        url = self.url_var.get().strip()
        self.result_text.delete(1.0, tk.END)
        if not url:
            messagebox.showwarning("提示","请输入视频链接")
            return
        self.status_var.set("正在解析...")
        try:
            vid = extract_douyin_video_id(url)
            if not vid:
                self.status_var.set("❌识别不到视频ID，请确认是抖音链接")
                return
            ok, txt, srt_str, msg = get_douyin_subtitle(vid)
            self.status_var.set(msg)
            self.result_text.insert(tk.END, txt)

            if ok and srt_str:
                save_path = filedialog.asksaveasfilename(
                    defaultextension=".srt",
                    filetypes=[("字幕srt","*.srt"),("文本txt","*.txt")]
                )
                if save_path:
                    with open(save_path,"w",encoding="utf-8") as f:
                        if save_path.endswith(".srt"):
                            f.write(srt_str)
                        else:
                            f.write(txt)
                    messagebox.showinfo("完成",f"文件已保存：{save_path}")
        except Exception as e:
            self.status_var.set(f"异常：{str(e)}")
            messagebox.showerror("错误", str(e))


if __name__ == "__main__":
    win = tk.Tk()
    app = SubtitleGrabApp(win)
    win.mainloop()
