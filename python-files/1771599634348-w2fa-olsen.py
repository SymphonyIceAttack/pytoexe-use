import os
import re
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import yt_dlp
import imageio_ffmpeg
from plyer import notification

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


# =========================
# VIDEO FUNKSJONER
# =========================

def download_video(url):
    ydl_opts = {
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "outtmpl": "video.mp4",
        "quiet": True,
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return "video.mp4"


def get_duration(video):
    """Returner videoens varighet i sekunder."""
    p = subprocess.run(
        [FFMPEG, "-i", video],
        stderr=subprocess.PIPE,
        text=True
    )
    m = re.search(r"Duration: (\d+):(\d+):(\d+)", p.stderr)
    if not m:
        return 0
    h, m_, s = map(int, m.groups())
    return h * 3600 + m_ * 60 + s


# =========================
# HØYDEPUNKT‑KLIPPING
# =========================

def clip_video(video):
    os.makedirs("clips", exist_ok=True)
    duration = get_duration(video)

    if duration < 30:
        raise Exception("Videoen er for kort for å lage highlights!")

    # --- PRØV OPUS‑STYLE SKILLE MELLOM STILLHET/FULL LYD ---
    analyze = subprocess.run(
        [
            FFMPEG,
            "-i", video,
            "-af", "silencedetect=noise=-35dB:d=0.3,astats=metadata=1:reset=1",
            "-f", "null", "-"
        ],
        stderr=subprocess.PIPE,
        text=True
    )

    silence_starts = [float(x) for x in re.findall(r"silence_start: (\d+\.?\d*)", analyze.stderr)]
    silence_ends = [float(x) for x in re.findall(r"silence_end: (\d+\.?\d*)", analyze.stderr)]
    rms_vals = [float(x) for x in re.findall(r"RMS level dB: (-?\d+\.?\d*)", analyze.stderr)]

    segments = []
    for i in range(min(len(silence_starts), len(silence_ends), len(rms_vals))):
        start = silence_ends[i]
        end = silence_starts[i]
        if end - start > 8:
            segments.append({"start": start, "energy": rms_vals[i]})

    # --- FALLBACK (ALLTID CLIPS) ---
    if not segments:
        CLIP_LEN = 28
        OVERLAP = 6
        MAX_CLIPS = 8

        segments = []
        current = int(duration * 0.15)

        for _ in range(MAX_CLIPS):
            if current + CLIP_LEN > duration:
                break
            segments.append({"start": current, "energy": 0})
            current += CLIP_LEN - OVERLAP

    # --- SORTER PÅ ENERGI (BEST FØRST) ---
    segments.sort(key=lambda x: x["energy"], reverse=True)

    # --- LAG CLIPS ---
    clips = []
    for i, seg in enumerate(segments[:8]):
        start = max(seg["start"] - 4, 0)
        out = f"clips/clip_{i+1}.mp4"

        subprocess.run([
            FFMPEG,
            "-y",
            "-ss", str(start),
            "-i", video,
            "-t", "28",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "17",
            "-pix_fmt", "yuv420p",
            "-profile:v", "high",
            "-c:a", "aac",
            "-b:a", "192k",
            out
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        clips.append(out)

    return clips


def make_thumb(video):
    thumb = video.replace(".mp4", ".png")
    subprocess.run([
        FFMPEG,
        "-y",
        "-ss", "1",
        "-i", video,
        "-vframes", "1",
        thumb
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return thumb


# =========================
# GUI
# =========================

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Opus‑Style Clipper (GRATIS)")
        self.geometry("900x650")
        self.configure(bg="#1e1e1e")

        self.url = tk.Entry(self, font=("Segoe UI", 14))
        self.url.pack(pady=20, padx=20, fill="x")

        tk.Button(
            self,
            text="FÅ HIGHLIGHTS",
            font=("Segoe UI", 16),
            bg="#22c55e",
            fg="white",
            command=self.start
        ).pack(pady=10)

        self.status = tk.Label(self, text="", fg="white", bg="#1e1e1e")
        self.status.pack(pady=5)

        self.container = tk.Frame(self, bg="#1e1e1e")
        self.container.pack(fill="both", expand=True)

    def start(self):
        url = self.url.get().strip()
        if not url:
            messagebox.showwarning("Feil", "Lim inn en YouTube‑link!")
            return

        self.status.config(text="⏳ Laster ned video …")
        threading.Thread(target=self.process, args=(url,), daemon=True).start()

    def process(self, url):
        try:
            video = download_video(url)

            self.status.config(text="🚀 Klipping starter nå …")
            notification.notify(
                title="Clipper",
                message="Highlight‑klipping starter ✂️",
                timeout=3
            )

            clips = clip_video(video)

            self.status.config(text="📸 Lager thumbnails …")
            for idx, c in enumerate(clips, start=1):
                thumb = make_thumb(c)
                self.after(0, self.show_clip, c, thumb)

            self.status.config(text="✅ Ferdig — Clips klare 🎉")

        except Exception as e:
            messagebox.showerror("Feil", str(e))

    def show_clip(self, video, thumb):
        frame = tk.Frame(self.container, bg="#2a2a2a")
        frame.pack(fill="x", padx=10, pady=5)

        img = ImageTk.PhotoImage(Image.open(thumb).resize((120, 70)))
        lbl = tk.Label(frame, image=img)
        lbl.image = img
        lbl.pack(side="left", padx=5)

        tk.Label(
            frame,
            text=os.path.basename(video),
            fg="white",
            bg="#2a2a2a"
        ).pack(side="left", padx=10)

        def save():
            path = filedialog.asksaveasfilename(
                defaultextension=".mp4",
                filetypes=[("MP4 video", "*.mp4")],
                initialfile=os.path.basename(video)
            )
            if path:
                shutil.copy(video, path)
                notification.notify(title="Clipper", message="Clip lagret 🎯")

        tk.Button(
            frame,
            text="Last ned",
            bg="#3b82f6",
            fg="white",
            command=save
        ).pack(side="right", padx=10)


# =========================
# START APP
# =========================

if __name__ == "__main__":
    App().mainloop()
