import tkinter as tk
from PIL import Image, ImageTk
import cv2
import pygame
import pyttsx3
import threading
import os
import numpy as np
import time

# ========== CONFIGURATION ==========
INTRO_VIDEO = "intro.mp4"
INTRO_AUDIO = "intro.mpeg"
ASSISTANT_VIDEO = "video.mp4"
TV_FRAME = "tv.jpeg"
VIDEO_SPEED = 1.75

# ========== INITIALIZE ==========
pygame.mixer.init(frequency=44100)


# ========== FEMALE VOICE FUNCTION ==========
def speak(text):
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')

        female_voice_found = False

        for voice in voices:
            if "zira" in voice.name.lower() or "female" in voice.name.lower():
                engine.setProperty('voice', voice.id)
                female_voice_found = True
                print(f"🎤 Female voice selected: {voice.name}")
                break

        if not female_voice_found and len(voices) > 1:
            engine.setProperty('voice', voices[1].id)
            print(f"🎤 Using voice index 1: {voices[1].name}")
        else:
            print(f"🎤 Using default voice: {voices[0].name}")

        engine.setProperty('rate', 155)
        engine.setProperty('volume', 1.0)

        print(f"🗣️ Saying: {text}")
        engine.say(text)
        engine.runAndWait()

    except Exception as e:
        print(f"❌ Speech error: {e}")
        print(f"🔊 {text}")


# ========== INTRO VIDEO PLAYER ==========
class IntroPlayer:
    def __init__(self, video_path, audio_path=None, on_complete=None, speed=1.0):
        self.video_path = video_path
        self.audio_path = audio_path
        self.on_complete = on_complete
        self.speed = speed
        self.cap = None
        self.root = None
        self.label = None
        self.running = True

    def play_audio(self):
        try:
            if self.audio_path and os.path.exists(self.audio_path):
                pygame.mixer.music.load(self.audio_path)
                pygame.mixer.music.play()
                print("🎵 Audio playing...")
        except Exception as e:
            print(f"Audio error: {e}")

    def play(self):
        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            print("❌ Intro video open failed")
            if self.on_complete:
                self.on_complete()
            return

        fps = self.cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 60

        play_fps = fps * self.speed
        self.delay = int(1000 / play_fps)

        print(f"🎬 Intro FPS: {fps}, Playing at: {play_fps:.1f}fps")

        ret, frame = self.cap.read()
        if not ret:
            if self.on_complete:
                self.on_complete()
            return

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg='black')

        self.label = tk.Label(self.root, bg='black')
        self.label.pack(expand=True)

        threading.Thread(target=self.play_audio, daemon=True).start()
        self.update_frame()
        self.root.mainloop()

    def update_frame(self):
        if not self.running:
            return

        ret, frame = self.cap.read()
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            screen_w = self.root.winfo_screenwidth()
            screen_h = self.root.winfo_screenheight()
            frame_h, frame_w = frame_rgb.shape[:2]
            scale = min(screen_w / frame_w, screen_h / frame_h)
            new_w = int(frame_w * scale)
            new_h = int(frame_h * scale)
            resized = cv2.resize(frame_rgb, (new_w, new_h))
            final = np.zeros((screen_h, screen_w, 3), dtype=np.uint8)
            x = (screen_w - new_w) // 2
            y = (screen_h - new_h) // 2
            final[y:y + new_h, x:x + new_w] = resized
            img = Image.fromarray(final)
            imgtk = ImageTk.PhotoImage(image=img)
            self.label.config(image=imgtk)
            self.label.image = imgtk
            self.root.after(self.delay, self.update_frame)
        else:
            self.cleanup()

    def cleanup(self):
        self.running = False
        if self.cap:
            self.cap.release()
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        if self.root:
            self.root.destroy()
        if self.on_complete:
            self.on_complete()


# ========== RIIKO ASSISTANT (FIXED) ==========
class RiikoAssistant:
    def __init__(self):
        self.root = None
        self.cap = None
        self.fullscreen_mode = False
        self.shrink_timer = None
        self.drag_x = 0
        self.drag_y = 0

        # Load video
        self.cap = cv2.VideoCapture(ASSISTANT_VIDEO)
        if not self.cap.isOpened():
            print("❌ Assistant video open failed")
            return

        # Load TV frame
        self.frame_img = Image.open(TV_FRAME).convert("RGBA")
        self.frame_img = self.frame_img.resize((260, 170))
        self.FRAME_W = 260
        self.FRAME_H = 170

        # TV screen margins
        self.LEFT = 5
        self.TOP = 5
        self.RIGHT = 5
        self.BOTTOM = 5

        self.VIDEO_W = self.FRAME_W - self.LEFT - self.RIGHT
        self.VIDEO_H = self.FRAME_H - self.TOP - self.BOTTOM

        # Initialize resize variables
        self.frame_img_resized = self.frame_img
        self.FRAME_W_NEW = self.FRAME_W
        self.FRAME_H_NEW = self.FRAME_H
        self.LEFT_NEW = self.LEFT
        self.TOP_NEW = self.TOP
        self.RIGHT_NEW = self.RIGHT
        self.BOTTOM_NEW = self.BOTTOM
        self.VIDEO_W_NEW = self.VIDEO_W
        self.VIDEO_H_NEW = self.VIDEO_H

        print(f"📺 Assistant started - TV Frame: {self.FRAME_W}x{self.FRAME_H}")

    def cover_fill(self, frame, w, h):
        fh, fw = frame.shape[:2]
        scale = max(w / fw, h / fh) * 1.03
        nw, nh = int(fw * scale), int(fh * scale)
        resized = cv2.resize(frame, (nw, nh))
        x = (nw - w) // 2
        y = (nh - h) // 2
        return resized[y:y + h, x:x + w]

    def auto_shrink(self):
        if self.fullscreen_mode:
            print("🔽 Auto-shrink ho raha hai...")
            self.root.attributes("-fullscreen", False)
            self.fullscreen_mode = False
            screen_w = self.root.winfo_screenwidth()
            screen_h = self.root.winfo_screenheight()
            self.root.geometry(
                f"{self.FRAME_W}x{self.FRAME_H}+{screen_w - self.FRAME_W - 20}+{screen_h - self.FRAME_H - 40}")
            self.shrink_timer = None

    def toggle_fullscreen(self, event=None):
        if self.shrink_timer:
            self.root.after_cancel(self.shrink_timer)
            self.shrink_timer = None

        self.fullscreen_mode = not self.fullscreen_mode

        if self.fullscreen_mode:
            self.root.attributes("-fullscreen", True)
            screen_w = self.root.winfo_screenwidth()
            screen_h = self.root.winfo_screenheight()
            new_w = screen_w
            new_h = screen_h

            self.frame_img_resized = self.frame_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            self.FRAME_W_NEW = new_w
            self.FRAME_H_NEW = new_h
            self.LEFT_NEW = int(self.LEFT * (new_w / self.FRAME_W))
            self.TOP_NEW = int(self.TOP * (new_h / self.FRAME_H))
            self.RIGHT_NEW = int(self.RIGHT * (new_w / self.FRAME_W))
            self.BOTTOM_NEW = int(self.BOTTOM * (new_h / self.FRAME_H))
            self.VIDEO_W_NEW = self.FRAME_W_NEW - self.LEFT_NEW - self.RIGHT_NEW
            self.VIDEO_H_NEW = self.FRAME_H_NEW - self.TOP_NEW - self.BOTTOM_NEW

            self.root.geometry(f"{self.FRAME_W_NEW}x{self.FRAME_H_NEW}")
            self.shrink_timer = self.root.after(10000, self.auto_shrink)
        else:
            self.root.attributes("-fullscreen", False)
            self.frame_img_resized = self.frame_img
            self.FRAME_W_NEW = self.FRAME_W
            self.FRAME_H_NEW = self.FRAME_H
            self.LEFT_NEW = self.LEFT
            self.TOP_NEW = self.TOP
            self.RIGHT_NEW = self.RIGHT
            self.BOTTOM_NEW = self.BOTTOM
            self.VIDEO_W_NEW = self.VIDEO_W
            self.VIDEO_H_NEW = self.VIDEO_H
            screen_w = self.root.winfo_screenwidth()
            screen_h = self.root.winfo_screenheight()
            self.root.geometry(
                f"{self.FRAME_W}x{self.FRAME_H}+{screen_w - self.FRAME_W - 20}+{screen_h - self.FRAME_H - 40}")

    def start_move(self, event):
        if not self.fullscreen_mode:
            self.drag_x = event.x
            self.drag_y = event.y

    def do_move(self, event):
        if not self.fullscreen_mode:
            x = self.root.winfo_x() + event.x - self.drag_x
            y = self.root.winfo_y() + event.y - self.drag_y
            self.root.geometry(f"+{x}+{y}")

    def start(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)

        # Canvas for video display
        self.canvas = tk.Canvas(self.root, bd=0, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Bind events
        self.canvas.bind("<Button-1>", self.start_move)
        self.canvas.bind("<B1-Motion>", self.do_move)
        self.canvas.bind("<Double-Button-1>", self.toggle_fullscreen)
        self.root.bind("<Escape>", self.toggle_fullscreen)

        # Start in window mode at bottom-right
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = screen_w - self.FRAME_W - 20
        y = screen_h - self.FRAME_H - 40
        self.root.geometry(f"{self.FRAME_W}x{self.FRAME_H}+{x}+{y}")
        print(f"📍 Assistant at bottom-right: {x}, {y}")

        # Start video update
        self.update_video()

        self.root.mainloop()

    def update_video(self):
        if self.cap is None:
            self.root.after(30, self.update_video)
            return

        ret, frame = self.cap.read()
        if not ret:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.root.after(30, self.update_video)
            return

        frame = self.cover_fill(frame, self.VIDEO_W_NEW, self.VIDEO_H_NEW)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        video_img = Image.fromarray(frame).convert("RGBA")

        final = self.frame_img_resized.copy()
        final.paste(video_img, (self.LEFT_NEW, self.TOP_NEW))

        img = ImageTk.PhotoImage(final)

        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=img)
        self.canvas.image = img
        self.canvas.config(width=self.FRAME_W_NEW, height=self.FRAME_H_NEW)

        self.root.after(30, self.update_video)


# ========== MAIN ==========
def intro_complete():
    print("🎬 Intro complete!")

    def say_greeting():
        speak("Welcome Master. Riiko is now online. I am ready to assist you.")

    greeting_thread = threading.Thread(target=say_greeting, daemon=True)
    greeting_thread.start()
    greeting_thread.join(timeout=3)

    print("🤖 Starting Riiko Assistant...")
    assistant = RiikoAssistant()
    assistant.start()


def main():
    print("=" * 50)
    print("🎀 RIIKO ASSISTANT - FEMALE VOICE EDITION 🎀")
    print("=" * 50)

    if not os.path.exists(INTRO_VIDEO):
        print(f"❌ Intro video not found: {INTRO_VIDEO}")
        intro_complete()
        return

    if os.path.exists(INTRO_AUDIO):
        print(f"✅ Audio file found: {INTRO_AUDIO}")
    else:
        print(f"⚠️ Audio file not found: {INTRO_AUDIO}")

    if os.path.exists(ASSISTANT_VIDEO):
        print(f"✅ Assistant video found: {ASSISTANT_VIDEO}")
    else:
        print(f"❌ Assistant video not found: {ASSISTANT_VIDEO}")

    if os.path.exists(TV_FRAME):
        print(f"✅ TV frame found: {TV_FRAME}")
    else:
        print(f"❌ TV frame not found: {TV_FRAME}")

    print("=" * 50)
    print("🎬 Playing intro video...")
    print("=" * 50)

    player = IntroPlayer(INTRO_VIDEO, INTRO_AUDIO, on_complete=intro_complete, speed=VIDEO_SPEED)
    player.play()


if __name__ == "__main__":
    main()