import cv2
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import subprocess
import tempfile

class VideoPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Player 4.0.2. L.A.")          # ✨ Nuovo nome
        self.root.geometry("800x600")
        self.root.minsize(700, 500)
        self.root.configure(bg="#1e1e1e")

        self.cap = None
        self.playing = False
        self.pausa = False
        self.frame = None
        self.total_frames = 0
        self.fps = 0
        self.foto_counter = 0
        self.tmp_file = None
        self.current_file = ""                         # per i messaggi di stato
        self.cartella_foto = None                      # cartella scelta per Scatta

        # Stile moderno
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#1e1e1e")
        style.configure("TLabel", background="#1e1e1e", foreground="white", font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 12, "bold"), foreground="#00d4aa")
        style.configure("TButton", font=("Segoe UI", 10, "bold"))
        style.configure("TProgressbar", thickness=6, troughcolor="#2d2d2d", background="#00d4aa")

        # ---- Barra superiore ----
        top = ttk.Frame(root)
        top.pack(fill=tk.X, padx=10, pady=(10, 5))
        ttk.Label(top, text="🎞️  Player 4.0.2", style="Title.TLabel").pack(side=tk.LEFT)
        self.status_label = ttk.Label(top, text="Nessun video", style="TLabel")
        self.status_label.pack(side=tk.RIGHT)

        # ---- Area video ----
        self.canvas = tk.Canvas(root, bg="black", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # ---- Controlli in basso ----
        bottom = ttk.Frame(root)
        bottom.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(5, 10))

        # Timeline
        time_frame = ttk.Frame(bottom)
        time_frame.pack(fill=tk.X, pady=(0, 5))
        self.time_current = ttk.Label(time_frame, text="00:00", style="TLabel")
        self.time_current.pack(side=tk.LEFT)
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(time_frame, variable=self.progress_var, maximum=100, style="TProgressbar")
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        self.time_total = ttk.Label(time_frame, text="00:00", style="TLabel")
        self.time_total.pack(side=tk.RIGHT)

        # Pulsanti
        btn_frame = ttk.Frame(bottom)
        btn_frame.pack(fill=tk.X)
        self.btn_open = ttk.Button(btn_frame, text="📂 Apri", command=self.apri)
        self.btn_open.pack(side=tk.LEFT, padx=5)
        self.btn_play = ttk.Button(btn_frame, text="▶ Play", command=self.play, state=tk.DISABLED)
        self.btn_play.pack(side=tk.LEFT, padx=5)
        self.btn_pause = ttk.Button(btn_frame, text="⏸ Pausa", command=self.pausa_video, state=tk.DISABLED)
        self.btn_pause.pack(side=tk.LEFT, padx=5)
        self.btn_foto = ttk.Button(btn_frame, text="📷 Scatta", command=self.scatta_foto, state=tk.DISABLED)
        self.btn_foto.pack(side=tk.LEFT, padx=5)
        self.btn_salva = ttk.Button(btn_frame, text="💾 Salva con nome", command=self.salva_foto, state=tk.DISABLED)
        self.btn_salva.pack(side=tk.LEFT, padx=5)

        self.root.protocol("WM_DELETE_WINDOW", self.chiudi)

        self.aggiorna_ui()

    # ---------- Gestione video ----------
    def apri(self):
        percorso = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.dav *.avi *.mkv *.mov"), ("Tutti", "*.*")])
        if not percorso:
            return

        self.ferma()

        cap = cv2.VideoCapture(percorso)
        if not cap.isOpened():
            if percorso.lower().endswith('.dav'):
                try:
                    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
                        tmp_mp4 = tmp.name
                    subprocess.run(['ffmpeg', '-y', '-i', percorso, '-c:v', 'copy', '-c:a', 'copy', tmp_mp4],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                    cap = cv2.VideoCapture(tmp_mp4)
                    if not cap.isOpened():
                        os.unlink(tmp_mp4)
                        raise Exception()
                    self.tmp_file = tmp_mp4
                except Exception:
                    messagebox.showerror("Errore", "Impossibile aprire il video. Convertilo manualmente.")
                    return
            else:
                messagebox.showerror("Errore", "Formato video non supportato.")
                return
        else:
            self.tmp_file = None

        self.cap = cap
        self.current_file = percorso                           # memorizza il percorso
        self.fps = cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        durata = self.total_frames / self.fps if self.fps > 0 else 0
        self.time_total.config(text=self.sec_to_time(durata))
        self.time_current.config(text="00:00")
        self.progress_var.set(0)

        self.btn_play.config(state=tk.DISABLED)
        self.btn_pause.config(state=tk.NORMAL)
        self.btn_foto.config(state=tk.NORMAL)
        self.btn_salva.config(state=tk.NORMAL)
        self.status_label.config(text=f"▶ {os.path.basename(self.current_file)}")

        self.playing = True
        self.pausa = False
        # Mostra il primo frame
        ret, frame = cap.read()
        if ret:
            self.frame = frame
            self.mostra_frame(frame)
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    def play(self):
        """Riprende la riproduzione (annulla la pausa)."""
        if self.cap:
            self.pausa = False
            self.btn_play.config(state=tk.DISABLED)
            self.btn_pause.config(state=tk.NORMAL)
            self.status_label.config(text=f"▶ {os.path.basename(self.current_file)}")

    def pausa_video(self):
        """Mette in pausa."""
        if self.cap:
            self.pausa = True
            self.btn_play.config(state=tk.NORMAL)
            self.btn_pause.config(state=tk.DISABLED)
            self.status_label.config(text="⏸ Pausa")

    def mostra_frame(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb)
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w > 10 and h > 10:
            img.thumbnail((w, h), Image.Resampling.LANCZOS)
        else:
            img.thumbnail((640, 360), Image.Resampling.LANCZOS)
        self.tk_img = ImageTk.PhotoImage(img)
        self.canvas.delete("all")
        self.canvas.create_image(w//2, h//2, image=self.tk_img, anchor=tk.CENTER)

    def aggiorna_ui(self):
        if self.playing and self.cap and not self.pausa:
            ret, frame = self.cap.read()
            if not ret:
                self.playing = False
                self.status_label.config(text="⏹ Fine video")
                self.btn_play.config(state=tk.DISABLED)
                self.btn_pause.config(state=tk.DISABLED)
                self.btn_foto.config(state=tk.DISABLED)
                self.btn_salva.config(state=tk.DISABLED)
            else:
                self.frame = frame
                self.mostra_frame(frame)
                try:
                    pos = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
                    if self.total_frames > 0:
                        self.progress_var.set((pos / self.total_frames) * 100)
                        curr_sec = pos / self.fps if self.fps > 0 else 0
                        self.time_current.config(text=self.sec_to_time(curr_sec))
                except:
                    pass

        self.root.after(20, self.aggiorna_ui)

    # ---------- Funzioni foto ----------
    def scatta_foto(self):
        """
        Salva il fotogramma corrente in una cartella scelta dall'utente.
        La prima volta chiede la cartella, poi la riutilizza per tutte le foto successive.
        """
        # Se non c'è ancora un frame, prova a catturarlo
        if self.frame is None and self.cap is not None:
            ret, frame = self.cap.read()
            if ret:
                self.frame = frame
                self.mostra_frame(frame)

        if self.frame is None:
            messagebox.showwarning("Attenzione", "Nessun fotogramma disponibile.")
            return

        # Chiede la cartella solo la prima volta (o se è stata resettata)
        if self.cartella_foto is None:
            cartella = filedialog.askdirectory(title="Seleziona la cartella dove salvare le foto")
            if not cartella:          # utente ha annullato
                return
            self.cartella_foto = cartella

        # Salva con nome progressivo
        self.foto_counter += 1
        nome_file = f"foto_{self.foto_counter:04d}.png"
        percorso_completo = os.path.join(self.cartella_foto, nome_file)
        cv2.imwrite(percorso_completo, self.frame)
        self.status_label.config(text=f"📸 Salvata in: {os.path.basename(self.cartella_foto)}/{nome_file}")

    def salva_foto(self):
        """Salva con nome e percorso scelti ogni volta dall'utente."""
        if self.frame is None and self.cap is not None:
            ret, frame = self.cap.read()
            if ret:
                self.frame = frame
                self.mostra_frame(frame)

        if self.frame is None:
            messagebox.showwarning("Attenzione", "Nessun fotogramma disponibile.")
            return

        path = filedialog.asksaveasfilename(defaultextension=".png",
                                           filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg")])
        if path:
            cv2.imwrite(path, self.frame)
            self.status_label.config(text=f"💾 Salvato: {os.path.basename(path)}")

    def sec_to_time(self, sec):
        m, s = divmod(int(sec), 60)
        return f"{m:02d}:{s:02d}"

    def ferma(self):
        if self.cap:
            self.cap.release()
        if self.tmp_file and os.path.exists(self.tmp_file):
            os.unlink(self.tmp_file)
        self.playing = False
        self.cap = None
        self.frame = None

    def chiudi(self):
        self.ferma()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoPlayer(root)
    root.mainloop()