"""
MagicMastering - Professional Audio Mastering Tool
Requiere: pip install numpy scipy soundfile pyloudnorm
Para compilar a .exe: pyinstaller --onefile --windowed magicmastering.py
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
import threading
import os
import wave
import struct

try:
    import soundfile as sf
    HAS_SOUNDFILE = True
except ImportError:
    HAS_SOUNDFILE = False

try:
    import pyloudnorm as pyln
    HAS_PYLOUDNORM = True
except ImportError:
    HAS_PYLOUDNORM = False

from scipy import signal as scipy_signal

# ─────────────────────────────────────────────
#  AUDIO PROCESSING ENGINE
# ─────────────────────────────────────────────

def read_audio(path):
    """Lee archivo WAV y retorna (samples float32, samplerate, channels)"""
    with wave.open(path, 'rb') as wf:
        sr = wf.getframerate()
        n_ch = wf.getnchannels()
        n_frames = wf.getnframes()
        sampwidth = wf.getsampwidth()
        raw = wf.readframes(n_frames)

    if sampwidth == 2:
        dtype = np.int16
        max_val = 32768.0
    elif sampwidth == 3:
        # 24-bit
        raw_arr = np.frombuffer(raw, dtype=np.uint8)
        samples_int = np.zeros(n_frames * n_ch, dtype=np.int32)
        for i in range(n_frames * n_ch):
            b = raw_arr[i*3:(i+1)*3]
            val = int(b[0]) | (int(b[1]) << 8) | (int(b[2]) << 16)
            if val & 0x800000:
                val -= 0x1000000
            samples_int[i] = val
        samples = samples_int.astype(np.float32) / 8388608.0
        if n_ch > 1:
            samples = samples.reshape(-1, n_ch)
        return samples, sr, n_ch
    elif sampwidth == 4:
        dtype = np.int32
        max_val = 2147483648.0
    else:
        raise ValueError(f"Bit depth no soportado: {sampwidth*8}-bit")

    samples = np.frombuffer(raw, dtype=dtype).astype(np.float32) / max_val
    if n_ch > 1:
        samples = samples.reshape(-1, n_ch)
    return samples, sr, n_ch


def write_audio(path, samples, sr):
    """Escribe WAV 24-bit"""
    if samples.ndim == 1:
        samples = samples.reshape(-1, 1)
    n_ch = samples.shape[1]
    # Clamp
    samples = np.clip(samples, -1.0, 1.0)
    int_samples = (samples * 8388607.0).astype(np.int32)

    with wave.open(path, 'wb') as wf:
        wf.setnchannels(n_ch)
        wf.setsampwidth(3)
        wf.setframerate(sr)
        flat = int_samples.flatten()
        raw = bytearray()
        for v in flat:
            if v < 0:
                v += 0x1000000
            raw += bytes([v & 0xFF, (v >> 8) & 0xFF, (v >> 16) & 0xFF])
        wf.writeframes(bytes(raw))


def measure_lufs_simple(samples, sr):
    """Medición LUFS simplificada (K-weighting aproximado)"""
    if samples.ndim > 1:
        mono = np.mean(samples, axis=1)
    else:
        mono = samples

    # K-weighting stage 1: high-shelf
    b1 = np.array([1.53512485958697, -2.69169618940638, 1.19839281085285])
    a1 = np.array([1.0, -1.69065929318241, 0.73248077421585])
    mono = scipy_signal.lfilter(b1, a1, mono)

    # K-weighting stage 2: high-pass
    b2 = np.array([1.0, -2.0, 1.0])
    a2 = np.array([1.0, -1.99004745483398, 0.99007225036621])
    mono = scipy_signal.lfilter(b2, a2, mono)

    mean_sq = np.mean(mono ** 2)
    if mean_sq < 1e-10:
        return -70.0
    lufs = -0.691 + 10 * np.log10(mean_sq)
    return lufs


def apply_eq(samples, sr, bands):
    """
    Aplica EQ paramétrica de 5 bandas.
    bands: lista de dicts {freq, gain_db, q, type}
    """
    result = samples.copy()
    for band in bands:
        freq = band['freq']
        gain_db = band['gain']
        q = band['q']
        btype = band['type']

        if abs(gain_db) < 0.01:
            continue

        if btype == 'lowshelf':
            b, a = scipy_signal.iirfilter(2, freq / (sr / 2), btype='lowpass',
                                           ftype='butter')
            # Simplified shelf
            A = 10 ** (gain_db / 40.0)
            b, a = _peaking_eq(freq, gain_db, q, sr)
        elif btype == 'highshelf':
            b, a = _peaking_eq(freq, gain_db, q, sr)
        else:
            b, a = _peaking_eq(freq, gain_db, q, sr)

        if result.ndim == 1:
            result = scipy_signal.lfilter(b, a, result)
        else:
            for ch in range(result.shape[1]):
                result[:, ch] = scipy_signal.lfilter(b, a, result[:, ch])
    return result


def _peaking_eq(freq, gain_db, q, sr):
    """Filtro peaking EQ (biquad)"""
    A = 10 ** (gain_db / 40.0)
    w0 = 2 * np.pi * freq / sr
    alpha = np.sin(w0) / (2 * q)
    b0 = 1 + alpha * A
    b1 = -2 * np.cos(w0)
    b2 = 1 - alpha * A
    a0 = 1 + alpha / A
    a1 = -2 * np.cos(w0)
    a2 = 1 - alpha / A
    return np.array([b0/a0, b1/a0, b2/a0]), np.array([1.0, a1/a0, a2/a0])


def apply_compressor(samples, sr, threshold_db, ratio, attack_ms=10, release_ms=100):
    """Compresor estéreo"""
    threshold = 10 ** (threshold_db / 20.0)
    attack = 1 - np.exp(-1 / (sr * attack_ms / 1000.0))
    release = 1 - np.exp(-1 / (sr * release_ms / 1000.0))

    if samples.ndim == 1:
        mono = samples
    else:
        mono = np.mean(np.abs(samples), axis=1)

    n = len(mono)
    gain = np.ones(n)
    env = 0.0
    for i in range(n):
        level = abs(mono[i])
        if level > env:
            env = attack * level + (1 - attack) * env
        else:
            env = release * level + (1 - release) * env

        if env > threshold:
            desired = threshold * (env / threshold) ** (1.0 / ratio)
            gain[i] = desired / (env + 1e-10)
        else:
            gain[i] = 1.0

    if samples.ndim == 1:
        return samples * gain
    else:
        return samples * gain[:, np.newaxis]


def apply_maximizer(samples, ceiling_db):
    """Limiter/Maximizer brick wall"""
    ceiling = 10 ** (ceiling_db / 20.0)
    # Soft clip suave + hard limit
    result = np.tanh(samples * 1.5) / 1.5
    result = np.clip(result, -ceiling, ceiling)
    return result


def normalize_to_lufs(samples, sr, target_lufs):
    """Normaliza a LUFS objetivo"""
    measured = measure_lufs_simple(samples, sr)
    if measured < -69:
        return samples
    gain_db = target_lufs - measured
    gain_linear = 10 ** (gain_db / 20.0)
    return samples * gain_linear


# ─────────────────────────────────────────────
#  GUI
# ─────────────────────────────────────────────

BG = "#0a0a0f"
BG2 = "#111118"
BG3 = "#1a1a24"
ACCENT = "#00d4ff"
ACCENT2 = "#ff6b35"
TEXT = "#e8e8f0"
TEXT_DIM = "#7070a0"
KNOB_COLOR = "#252535"
BORDER = "#2a2a3a"

FONT_TITLE = ("Courier New", 22, "bold")
FONT_LABEL = ("Courier New", 9, "bold")
FONT_VALUE = ("Courier New", 11, "bold")
FONT_SMALL = ("Courier New", 8)


class Knob(tk.Canvas):
    """Knob giratorio personalizado"""
    def __init__(self, parent, label, min_val, max_val, default, unit="",
                 color=ACCENT, command=None, **kwargs):
        size = kwargs.pop('size', 70)
        super().__init__(parent, width=size, height=size+24,
                         bg=BG2, highlightthickness=0, **kwargs)
        self.min_val = min_val
        self.max_val = max_val
        self.value = default
        self.unit = unit
        self.color = color
        self.command = command
        self.label = label
        self.size = size
        self._drag_y = None

        self._draw()
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<MouseWheel>", self._on_scroll)

    def _angle(self):
        norm = (self.value - self.min_val) / (self.max_val - self.min_val)
        return -225 + norm * 270

    def _draw(self):
        self.delete("all")
        cx = self.size // 2
        cy = self.size // 2
        r = self.size // 2 - 6

        # Outer ring background
        self.create_oval(cx-r-3, cy-r-3, cx+r+3, cy+r+3,
                         fill="#0d0d18", outline=BORDER, width=1)
        # Track arc (background)
        self.create_arc(cx-r, cy-r, cx+r, cy+r,
                        start=-225+270, extent=-270,
                        style=tk.ARC, outline="#222235", width=3)
        # Value arc
        norm = (self.value - self.min_val) / (self.max_val - self.min_val)
        extent = norm * -270
        if abs(extent) > 0.5:
            self.create_arc(cx-r, cy-r, cx+r, cy+r,
                            start=-225+270, extent=extent,
                            style=tk.ARC, outline=self.color, width=3)
        # Knob body
        kr = r - 8
        self.create_oval(cx-kr, cy-kr, cx+kr, cy+kr,
                         fill=KNOB_COLOR, outline="#333348", width=1)
        # Pointer
        angle_rad = np.deg2rad(self._angle())
        px = cx + (kr - 4) * np.cos(angle_rad)
        py = cy - (kr - 4) * np.sin(angle_rad)
        self.create_line(cx, cy, px, py, fill=self.color, width=2, capstyle=tk.ROUND)
        self.create_oval(cx-2, cy-2, cx+2, cy+2, fill=self.color, outline="")

        # Value text
        val_str = f"{self.value:.1f}{self.unit}"
        self.create_text(cx, self.size + 8, text=val_str,
                         fill=TEXT, font=FONT_VALUE, anchor="center")
        self.create_text(cx, self.size + 20, text=self.label,
                         fill=TEXT_DIM, font=FONT_SMALL, anchor="center")

    def _on_press(self, e):
        self._drag_y = e.y

    def _on_drag(self, e):
        if self._drag_y is None:
            return
        delta = (self._drag_y - e.y) * (self.max_val - self.min_val) / 150.0
        self._drag_y = e.y
        self.set_value(self.value + delta)

    def _on_release(self, e):
        self._drag_y = None

    def _on_scroll(self, e):
        step = (self.max_val - self.min_val) / 100.0
        self.set_value(self.value + (step if e.delta > 0 else -step))

    def set_value(self, v):
        self.value = max(self.min_val, min(self.max_val, v))
        self._draw()
        if self.command:
            self.command(self.value)

    def get(self):
        return self.value


class EQBand(tk.Frame):
    """Una banda de EQ con freq, gain y Q"""
    def __init__(self, parent, label, freq, band_type="peak", **kwargs):
        super().__init__(parent, bg=BG2, **kwargs)
        self.band_type = band_type

        tk.Label(self, text=label, bg=BG2, fg=ACCENT2,
                 font=("Courier New", 8, "bold")).pack(pady=(6, 0))

        self.gain_knob = Knob(self, "GAIN", -12, 12, 0, "dB",
                              color=ACCENT, size=60)
        self.gain_knob.pack()

        self.freq_knob = Knob(self, "FREQ", 20, 20000, freq, "Hz",
                              color=ACCENT2, size=60)
        self.freq_knob.pack()

        self.q_knob = Knob(self, "Q", 0.1, 10, 1.0, "",
                           color="#aa44ff", size=60)
        self.q_knob.pack(pady=(0, 4))

    def get_band(self):
        return {
            'freq': self.freq_knob.get(),
            'gain': self.gain_knob.get(),
            'q': self.q_knob.get(),
            'type': self.band_type
        }


class MagicMastering(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("✦ MAGICMASTERING ✦")
        self.configure(bg=BG)
        self.resizable(False, False)

        self.input_path = tk.StringVar(value="")
        self.output_path = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="Listo para masterizar")
        self.lufs_var = tk.StringVar(value="LUFS: ---")
        self.processing = False

        self._build_ui()
        self._center_window()

    def _center_window(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")

    def _build_ui(self):
        # ── HEADER ──
        header = tk.Frame(self, bg=BG, pady=0)
        header.pack(fill="x")

        tk.Canvas(self, height=1, bg=BORDER, highlightthickness=0).pack(fill="x")

        title_frame = tk.Frame(header, bg=BG)
        title_frame.pack()
        tk.Label(title_frame, text="✦ MAGIC", bg=BG, fg=ACCENT,
                 font=("Courier New", 26, "bold")).pack(side="left")
        tk.Label(title_frame, text="MASTERING", bg=BG, fg=ACCENT2,
                 font=("Courier New", 26, "bold")).pack(side="left")
        tk.Label(title_frame, text=" ✦", bg=BG, fg=ACCENT,
                 font=("Courier New", 26, "bold")).pack(side="left")
        tk.Label(self, text="PROFESSIONAL AUDIO MASTERING SUITE",
                 bg=BG, fg=TEXT_DIM, font=("Courier New", 8)).pack()

        tk.Canvas(self, height=1, bg=BORDER, highlightthickness=0).pack(fill="x", pady=(6, 0))

        # ── FILE I/O ──
        io_frame = tk.Frame(self, bg=BG3, padx=12, pady=10)
        io_frame.pack(fill="x", padx=14, pady=8)

        def file_row(parent, label, var, cmd):
            row = tk.Frame(parent, bg=BG3)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=label, bg=BG3, fg=TEXT_DIM,
                     font=FONT_LABEL, width=9, anchor="w").pack(side="left")
            tk.Entry(row, textvariable=var, bg="#0d0d1a", fg=TEXT,
                     insertbackground=ACCENT, relief="flat",
                     font=("Courier New", 9), width=42).pack(side="left", padx=4)
            tk.Button(row, text="BROWSE", command=cmd,
                      bg=BG, fg=ACCENT, font=FONT_LABEL,
                      relief="flat", padx=8, cursor="hand2",
                      activebackground=ACCENT, activeforeground=BG).pack(side="left")

        file_row(io_frame, "INPUT ›", self.input_path, self._browse_input)
        file_row(io_frame, "OUTPUT ›", self.output_path, self._browse_output)

        # ── LOUDNESS TARGET ──
        loud_frame = tk.Frame(self, bg=BG2, padx=14, pady=10)
        loud_frame.pack(fill="x", padx=14, pady=4)

        tk.Label(loud_frame, text="◈  LOUDNESS TARGET",
                 bg=BG2, fg=ACCENT, font=("Courier New", 10, "bold")).pack(anchor="w")

        knobs_row = tk.Frame(loud_frame, bg=BG2)
        knobs_row.pack(anchor="w", pady=6)

        self.lufs_knob = Knob(knobs_row, "TARGET LUFS", -14, -6, -9, "LUFS",
                              color=ACCENT, size=80)
        self.lufs_knob.pack(side="left", padx=10)

        self.thresh_knob = Knob(knobs_row, "THRESHOLD", -30, -3, -12, "dB",
                                color="#ff4466", size=80)
        self.thresh_knob.pack(side="left", padx=10)

        self.ratio_knob = Knob(knobs_row, "RATIO", 1, 10, 3, ":1",
                               color=ACCENT2, size=80)
        self.ratio_knob.pack(side="left", padx=10)

        self.ceiling_knob = Knob(knobs_row, "MAXIMIZER", -3, 0, -0.5, "dB",
                                 color="#44ffaa", size=80)
        self.ceiling_knob.pack(side="left", padx=10)

        self.makeup_knob = Knob(knobs_row, "MAKEUP GAIN", -6, 12, 0, "dB",
                                color="#ffcc00", size=80)
        self.makeup_knob.pack(side="left", padx=10)

        # ── EQ ──
        eq_outer = tk.Frame(self, bg=BG, padx=14)
        eq_outer.pack(fill="x", pady=4)

        tk.Label(eq_outer, text="◈  5-BAND PARAMETRIC EQ",
                 bg=BG, fg=ACCENT, font=("Courier New", 10, "bold")).pack(anchor="w", pady=(0, 4))

        eq_frame = tk.Frame(eq_outer, bg=BG2, padx=8, pady=4)
        eq_frame.pack(fill="x")

        self.eq_bands = []
        band_configs = [
            ("LOW\nSHELF", 80, "lowshelf"),
            ("LOW\nMID", 250, "peak"),
            ("MID", 1000, "peak"),
            ("HIGH\nMID", 4000, "peak"),
            ("HIGH\nSHELF", 12000, "highshelf"),
        ]

        for label, freq, btype in band_configs:
            sep = tk.Frame(eq_frame, bg=BORDER, width=1)
            sep.pack(side="left", fill="y", padx=2)
            band = EQBand(eq_frame, label, freq, band_type=btype)
            band.pack(side="left", padx=4)
            self.eq_bands.append(band)

        # ── STATUS + PROCESS ──
        bottom = tk.Frame(self, bg=BG, padx=14, pady=10)
        bottom.pack(fill="x")

        self.meter_canvas = tk.Canvas(bottom, width=300, height=18,
                                      bg="#0a0a12", highlightthickness=1,
                                      highlightbackground=BORDER)
        self.meter_canvas.pack(side="left", padx=(0, 10))
        self._draw_meter(0)

        tk.Label(bottom, textvariable=self.lufs_var,
                 bg=BG, fg=ACCENT, font=("Courier New", 10, "bold")).pack(side="left", padx=6)

        self.process_btn = tk.Button(
            bottom, text="▶  PROCESS & MASTER",
            command=self._start_processing,
            bg=ACCENT, fg=BG, font=("Courier New", 11, "bold"),
            relief="flat", padx=20, pady=6, cursor="hand2",
            activebackground=ACCENT2, activeforeground=BG
        )
        self.process_btn.pack(side="right")

        # Analyze button
        tk.Button(
            bottom, text="ANALYZE LUFS",
            command=self._analyze_lufs,
            bg=BG3, fg=TEXT, font=FONT_LABEL,
            relief="flat", padx=10, pady=6, cursor="hand2"
        ).pack(side="right", padx=6)

        tk.Canvas(self, height=1, bg=BORDER, highlightthickness=0).pack(fill="x")

        status_bar = tk.Frame(self, bg="#07070e", pady=4)
        status_bar.pack(fill="x")
        tk.Label(status_bar, textvariable=self.status_var,
                 bg="#07070e", fg=TEXT_DIM, font=FONT_SMALL).pack(side="left", padx=10)

    def _draw_meter(self, level_0_to_1, color=ACCENT):
        self.meter_canvas.delete("all")
        w = 300
        h = 18
        # Background segments
        for i in range(30):
            x = i * 10 + 1
            c = "#1a1a2a"
            self.meter_canvas.create_rectangle(x, 2, x+8, h-2, fill=c, outline="")
        # Active segments
        active = int(level_0_to_1 * 30)
        for i in range(active):
            x = i * 10 + 1
            frac = i / 30.0
            if frac < 0.6:
                c = ACCENT
            elif frac < 0.85:
                c = ACCENT2
            else:
                c = "#ff2244"
            self.meter_canvas.create_rectangle(x, 2, x+8, h-2, fill=c, outline="")

    def _browse_input(self):
        path = filedialog.askopenfilename(
            title="Seleccionar archivo de audio",
            filetypes=[("WAV files", "*.wav"), ("All files", "*.*")]
        )
        if path:
            self.input_path.set(path)
            base, _ = os.path.splitext(path)
            self.output_path.set(base + "_mastered.wav")

    def _browse_output(self):
        path = filedialog.asksaveasfilename(
            title="Guardar como",
            defaultextension=".wav",
            filetypes=[("WAV files", "*.wav")]
        )
        if path:
            self.output_path.set(path)

    def _analyze_lufs(self):
        path = self.input_path.get()
        if not path or not os.path.exists(path):
            messagebox.showerror("Error", "Selecciona un archivo de entrada válido.")
            return
        self.status_var.set("Analizando LUFS...")
        self.update()

        def do_analyze():
            try:
                samples, sr, _ = read_audio(path)
                lufs = measure_lufs_simple(samples, sr)
                self.after(0, lambda: self.lufs_var.set(f"LUFS: {lufs:.1f}"))
                self.after(0, lambda: self.status_var.set(f"Análisis completo — {lufs:.1f} LUFS"))
                level = max(0, min(1, (lufs + 30) / 30))
                self.after(0, lambda: self._draw_meter(level))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", str(e)))
                self.after(0, lambda: self.status_var.set("Error en análisis"))

        threading.Thread(target=do_analyze, daemon=True).start()

    def _start_processing(self):
        if self.processing:
            return
        inp = self.input_path.get()
        out = self.output_path.get()
        if not inp or not os.path.exists(inp):
            messagebox.showerror("Error", "Selecciona un archivo de entrada válido.")
            return
        if not out:
            messagebox.showerror("Error", "Selecciona un archivo de salida.")
            return

        self.processing = True
        self.process_btn.config(state="disabled", text="PROCESANDO...")
        self.status_var.set("Procesando audio...")
        threading.Thread(target=self._process_audio, args=(inp, out), daemon=True).start()

    def _process_audio(self, inp, out):
        try:
            self.after(0, lambda: self.status_var.set("Leyendo archivo..."))
            samples, sr, n_ch = read_audio(inp)

            self.after(0, lambda: self.status_var.set("Aplicando EQ..."))
            eq_bands = [b.get_band() for b in self.eq_bands]
            samples = apply_eq(samples, sr, eq_bands)

            self.after(0, lambda: self.status_var.set("Aplicando compresor..."))
            thresh = self.thresh_knob.get()
            ratio = self.ratio_knob.get()
            samples = apply_compressor(samples, sr, thresh, ratio)

            # Makeup gain
            makeup = self.makeup_knob.get()
            if abs(makeup) > 0.01:
                samples = samples * (10 ** (makeup / 20.0))

            self.after(0, lambda: self.status_var.set("Normalizando a LUFS..."))
            target_lufs = self.lufs_knob.get()
            samples = normalize_to_lufs(samples, sr, target_lufs)

            self.after(0, lambda: self.status_var.set("Aplicando maximizer..."))
            ceiling = self.ceiling_knob.get()
            samples = apply_maximizer(samples, ceiling)

            self.after(0, lambda: self.status_var.set("Escribiendo archivo..."))
            write_audio(out, samples, sr)

            final_lufs = measure_lufs_simple(samples, sr)
            self.after(0, lambda: self.lufs_var.set(f"LUFS: {final_lufs:.1f}"))
            level = max(0, min(1, (final_lufs + 30) / 30))
            self.after(0, lambda: self._draw_meter(level, "#44ffaa"))
            self.after(0, lambda: self.status_var.set(
                f"✦ Masterización completa — {final_lufs:.1f} LUFS → {os.path.basename(out)}"))
            self.after(0, lambda: messagebox.showinfo(
                "¡Completado!", f"Masterización exitosa!\n\nLUFS final: {final_lufs:.1f}\nArchivo: {out}"))

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", f"Error en procesamiento:\n{e}"))
            self.after(0, lambda: self.status_var.set("Error en procesamiento"))
        finally:
            self.processing = False
            self.after(0, lambda: self.process_btn.config(state="normal", text="▶  PROCESS & MASTER"))


if __name__ == "__main__":
    app = MagicMastering()
    app.mainloop()
