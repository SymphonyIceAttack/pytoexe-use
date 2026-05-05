import sys
import os
import ctypes
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import vlc
from PIL import Image, ImageTk

# Windows registry handling for file associations
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)

def register_file_associations():
    """Register this app as default player for video/audio/image extensions"""
    exe_path = sys.executable if getattr(sys, 'frozen', False) else __file__
    exe_path = os.path.abspath(exe_path)
    if getattr(sys, 'frozen', False):
        # Running as exe
        app_name = "MediaPlayerApp"
        extensions = ['.mp4', '.avi', '.mkv', '.mov', '.flv', '.mp3', '.wav', '.ogg', '.m4a', '.jpg', '.jpeg', '.png', '.gif', '.bmp']
    else:
        app_name = "MediaPlayerDev"
        extensions = ['.mp4', '.mp3', '.jpg']
    
    # Create ProgID
    prog_id = f"{app_name}.File"
    command = f'"{exe_path}" "%1"'
    
    # Set registry keys
    import winreg
    try:
        # ProgID
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{prog_id}") as key:
            winreg.SetValue(key, "", winreg.REG_SZ, app_name)
            with winreg.CreateKey(key, "DefaultIcon") as icon_key:
                winreg.SetValue(icon_key, "", winreg.REG_SZ, f'"{exe_path}",0')
            with winreg.CreateKey(key, "shell\\open\\command") as cmd_key:
                winreg.SetValue(cmd_key, "", winreg.REG_SZ, command)
        
        # Associate each extension
        for ext in extensions:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{ext}") as ext_key:
                winreg.SetValue(ext_key, "", winreg.REG_SZ, prog_id)
        
        # Set as default for these extensions (optional)
        # Notify shell
        ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x0000, None, None)
        return True
    except Exception as e:
        print(f"Register failed: {e}")
        return False

class MediaPlayerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Media Player")
        self.root.geometry("900x600")
        self.root.minsize(600, 400)
        
        self.current_path = None
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        self.is_playing = False
        self.is_video = False
        self.audio_duration = 0
        
        # GUI Layout
        self.create_widgets()
        
        # Check if file passed as argument
        if len(sys.argv) > 1:
            file_path = sys.argv[1]
            if os.path.exists(file_path):
                self.load_media(file_path)
    
    def create_widgets(self):
        # Top bar
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Button(top_frame, text="Open File", command=self.open_file).pack(side=tk.LEFT, padx=2)
        tk.Button(top_frame, text="Register as Default Player", command=self.do_register).pack(side=tk.LEFT, padx=2)
        self.status_label = tk.Label(top_frame, text="Ready", anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        
        # Video/Image frame
        self.media_frame = tk.Frame(self.root, bg='black')
        self.media_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # For video (will be embeded)
        self.video_frame = tk.Frame(self.media_frame, bg='black')
        self.video_frame.pack(fill=tk.BOTH, expand=True)
        
        # For image display
        self.image_label = tk.Label(self.media_frame, bg='black')
        
        # Control bar
        control_frame = tk.Frame(self.root)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.play_pause_btn = tk.Button(control_frame, text="Play", command=self.play_pause, state=tk.DISABLED)
        self.play_pause_btn.pack(side=tk.LEFT, padx=2)
        tk.Button(control_frame, text="Stop", command=self.stop, state=tk.DISABLED).pack(side=tk.LEFT, padx=2)
        
        self.time_slider = ttk.Scale(control_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=self.seek)
        self.time_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        
        self.time_label = tk.Label(control_frame, text="00:00 / 00:00")
        self.time_label.pack(side=tk.LEFT, padx=5)
        
        self.volume_btn = tk.Button(control_frame, text="🔊", command=self.toggle_mute)
        self.volume_btn.pack(side=tk.RIGHT, padx=2)
        self.volume_slider = ttk.Scale(control_frame, from_=0, to=100, orient=tk.HORIZONTAL, length=100, command=self.set_volume)
        self.volume_slider.set(80)
        self.volume_slider.pack(side=tk.RIGHT, padx=5)
        
        # Update timer
        self.update_timer()
        
        # Bind events
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def open_file(self):
        filetypes = [
            ("Media files", "*.mp4 *.avi *.mkv *.mov *.flv *.mp3 *.wav *.ogg *.m4a *.jpg *.jpeg *.png *.gif *.bmp"),
            ("Video", "*.mp4 *.avi *.mkv *.mov *.flv"),
            ("Audio", "*.mp3 *.wav *.ogg *.m4a"),
            ("Image", "*.jpg *.jpeg *.png *.gif *.bmp"),
            ("All files", "*.*")
        ]
        path = filedialog.askopenfilename(title="Open Media", filetypes=filetypes)
        if path:
            self.load_media(path)
    
    def load_media(self, path):
        self.current_path = path
        ext = os.path.splitext(path)[1].lower()
        
        # Stop current playback
        self.stop()
        
        # Hide both video and image containers
        self.video_frame.pack_forget()
        self.image_label.pack_forget()
        
        # Determine type
        image_exts = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
        video_exts = ['.mp4', '.avi', '.mkv', '.mov', '.flv']
        audio_exts = ['.mp3', '.wav', '.ogg', '.m4a']
        
        if ext in image_exts:
            self.is_video = False
            self.display_image(path)
        elif ext in video_exts:
            self.is_video = True
            self.play_video(path)
        elif ext in audio_exts:
            self.is_video = False
            self.play_audio(path)
        else:
            self.status_label.config(text=f"Unsupported file type: {ext}")
            return
        
        self.play_pause_btn.config(state=tk.NORMAL)
        self.status_label.config(text=f"Playing: {os.path.basename(path)}")
    
    def display_image(self, path):
        img = Image.open(path)
        # Resize to fit frame
        frame_w = self.media_frame.winfo_width()
        frame_h = self.media_frame.winfo_height()
        if frame_w > 10 and frame_h > 10:
            img.thumbnail((frame_w-20, frame_h-20), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        self.image_label.config(image=photo)
        self.image_label.image = photo
        self.image_label.pack(fill=tk.BOTH, expand=True)
        self.time_slider.config(state=tk.DISABLED)
        self.time_label.config(text="Image")
    
    def play_video(self, path):
        media = self.instance.media_new(path)
        self.player.set_media(media)
        self.player.set_hwnd(self.video_frame.winfo_id())
        self.player.play()
        self.is_playing = True
        self.play_pause_btn.config(text="Pause")
        self.video_frame.pack(fill=tk.BOTH, expand=True)
        self.time_slider.config(state=tk.NORMAL)
        # Get duration
        self.audio_duration = self.player.get_length() / 1000
        
    def play_audio(self, path):
        media = self.instance.media_new(path)
        self.player.set_media(media)
        self.player.play()
        self.is_playing = True
        self.play_pause_btn.config(text="Pause")
        # No video frame visible
        self.time_slider.config(state=tk.NORMAL)
        self.audio_duration = self.player.get_length() / 1000
        self.status_label.config(text=f"Playing audio: {os.path.basename(path)}")
    
    def play_pause(self):
        if self.player is None:
            return
        if self.is_playing:
            self.player.pause()
            self.is_playing = False
            self.play_pause_btn.config(text="Play")
        else:
            self.player.play()
            self.is_playing = True
            self.play_pause_btn.config(text="Pause")
    
    def stop(self):
        if self.player:
            self.player.stop()
        self.is_playing = False
        self.play_pause_btn.config(text="Play", state=tk.DISABLED)
        self.time_slider.set(0)
        self.time_label.config(text="00:00 / 00:00")
        self.video_frame.pack_forget()
        self.image_label.pack_forget()
        self.current_path = None
    
    def seek(self, value):
        if self.player and self.audio_duration > 0:
            pos = float(value) / 100
            self.player.set_position(pos)
    
    def set_volume(self, value):
        vol = int(float(value))
        self.player.audio_set_volume(vol)
    
    def toggle_mute(self):
        current = self.player.audio_get_volume()
        if current > 0:
            self._prev_vol = current
            self.player.audio_set_volume(0)
            self.volume_slider.set(0)
            self.volume_btn.config(text="🔇")
        else:
            vol = self._prev_vol if hasattr(self, '_prev_vol') else 80
            self.player.audio_set_volume(vol)
            self.volume_slider.set(vol)
            self.volume_btn.config(text="🔊")
    
    def update_timer(self):
        if self.player and self.current_path:
            if self.player.is_playing():
                # Update slider and time label
                if self.audio_duration > 0:
                    pos = self.player.get_position() * 100
                    self.time_slider.set(pos)
                    current_time = self.player.get_time() / 1000
                    current_str = f"{int(current_time//60):02d}:{int(current_time%60):02d}"
                    dur_str = f"{int(self.audio_duration//60):02d}:{int(self.audio_duration%60):02d}"
                    self.time_label.config(text=f"{current_str} / {dur_str}")
                else:
                    # try to get duration again
                    dur = self.player.get_length() / 1000
                    if dur > 0:
                        self.audio_duration = dur
        self.root.after(500, self.update_timer)
    
    def do_register(self):
        if not is_admin():
            if messagebox.askyesno("Admin Required", "Registering as default player requires administrator privileges. Run as admin?"):
                run_as_admin()
            return
        if register_file_associations():
            messagebox.showinfo("Success", "File associations registered. You can now set this app as default player for media files.")
        else:
            messagebox.showerror("Error", "Failed to register. Try running as administrator manually.")
    
    def on_close(self):
        self.stop()
        self.player.release()
        self.root.destroy()

def main():
    # Ensure VLC is available (provide hint if missing)
    try:
        import vlc
    except ImportError:
        tk.Tk().withdraw()
        messagebox.showerror("Missing Dependency", "python-vlc is not installed.\nPlease run: pip install python-vlc")
        sys.exit(1)
    
    root = tk.Tk()
    app = MediaPlayerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()