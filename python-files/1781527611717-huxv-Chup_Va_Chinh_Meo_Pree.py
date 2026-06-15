import ctypes
import ctypes.wintypes
import io
import time
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import subprocess
import platform
from PIL import Image, ImageTk, ImageGrab, ImageFilter
from pathlib import Path
import threading
import math
import numpy as np
import webbrowser

# ── Thay pyautogui bằng PIL.ImageGrab ──
# ── Thay keyboard bằng ctypes user32 ──
# ── Thay cv2 bằng PIL + numpy ──

try:
    import winsound
    WINSOUND_AVAILABLE = True
except ImportError:
    WINSOUND_AVAILABLE = False

try:
    import winreg
    REGISTRY_AVAILABLE = True
except ImportError:
    REGISTRY_AVAILABLE = False

# ─────────────────────────────────────────────────────────────
# Thay thế keyboard.is_pressed bằng ctypes
# ─────────────────────────────────────────────────────────────
VK_TAB    = 0x09
VK_ESCAPE = 0x1B
VK_LEFT   = 0x25
VK_RIGHT  = 0x27

user32 = ctypes.windll.user32

def is_key_pressed(vk_code):
    return bool(user32.GetAsyncKeyState(vk_code) & 0x8000)


# ─────────────────────────────────────────────────────────────
# Copy ảnh vào clipboard Windows (CF_DIB)
# ─────────────────────────────────────────────────────────────
CF_DIB = 8
GMEM_MOVEABLE = 0x0002

def copy_image_to_clipboard(arr):
    try:
        img = numpy_to_pil(arr).convert('RGB')
        output = io.BytesIO()
        img.save(output, 'BMP')
        bmp_data = output.getvalue()
        output.close()
        dib_data = bmp_data[14:]

        kernel32 = ctypes.windll.kernel32

        h_global = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(dib_data))
        if not h_global:
            return False
        ptr = kernel32.GlobalLock(h_global)
        if not ptr:
            kernel32.GlobalFree(h_global)
            return False
        ctypes.memmove(ptr, dib_data, len(dib_data))
        kernel32.GlobalUnlock(h_global)

        if not user32.OpenClipboard(0):
            kernel32.GlobalFree(h_global)
            return False
        try:
            user32.EmptyClipboard()
            if not user32.SetClipboardData(CF_DIB, h_global):
                kernel32.GlobalFree(h_global)
                return False
        finally:
            user32.CloseClipboard()
        return True
    except Exception as e:
        print("copy_image_to_clipboard error: {}".format(e))
        return False


# ─────────────────────────────────────────────────────────────
# Thay thế cv2 bằng PIL + numpy
# ─────────────────────────────────────────────────────────────

def pil_to_numpy(pil_img):
    arr = np.array(pil_img.convert('RGB'))
    return arr[:, :, ::-1].copy()

def numpy_to_pil(arr):
    rgb = arr[:, :, ::-1].copy()
    return Image.fromarray(rgb.astype(np.uint8))

def cv2_imread(filepath):
    try:
        img = Image.open(filepath).convert('RGB')
        return pil_to_numpy(img)
    except Exception as e:
        print("cv2_imread error: {}".format(e))
        return None

def cv2_imwrite(filepath, arr):
    try:
        img = numpy_to_pil(arr)
        ext = os.path.splitext(filepath)[1].lower()
        if ext in ('.jpg', '.jpeg'):
            img.save(filepath, 'JPEG', quality=100, subsampling=0)
        elif ext == '.webp':
            img.save(filepath, 'WEBP', lossless=True, quality=100)
        elif ext in ('.bmp',):
            img.save(filepath, 'BMP')
        elif ext in ('.tif', '.tiff'):
            img.save(filepath, 'TIFF')
        else:
            img.save(filepath, 'PNG')
        return True
    except Exception as e:
        print("cv2_imwrite error: {}".format(e))
        return False

def cv2_resize(arr, size, interpolation=None):
    img = numpy_to_pil(arr)
    resample = Image.BILINEAR
    img = img.resize(size, resample)
    return pil_to_numpy(img)

def cv2_rotate_90cw(arr):
    img = numpy_to_pil(arr)
    img = img.transpose(Image.ROTATE_270)
    return pil_to_numpy(img)

def cv2_rotate_90ccw(arr):
    img = numpy_to_pil(arr)
    img = img.transpose(Image.ROTATE_90)
    return pil_to_numpy(img)

def cv2_flip(arr, flip_code):
    img = numpy_to_pil(arr)
    if flip_code == 1:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    else:
        img = img.transpose(Image.FLIP_TOP_BOTTOM)
    return pil_to_numpy(img)

def cv2_warp_affine_rotation(arr, angle_deg):
    img = numpy_to_pil(arr)
    rotated = img.rotate(angle_deg, expand=True, resample=Image.BILINEAR)
    bg = Image.new('RGB', rotated.size, (255, 255, 255))
    bg.paste(rotated, (0, 0))
    return pil_to_numpy(bg)

def cv2_perspective_transform(arr, src_pts, dst_pts, out_w, out_h):
    try:
        coeffs = _compute_pil_perspective(dst_pts, src_pts)
        img = numpy_to_pil(arr)
        out = img.transform(
            (out_w, out_h),
            Image.PERSPECTIVE,
            coeffs,
            Image.BILINEAR
        )
        return pil_to_numpy(out)
    except Exception as e:
        print("perspective error: {}".format(e))
        return arr


def _compute_pil_perspective(src4, dst4):
    src = [(float(p[0]), float(p[1])) for p in src4]
    dst = [(float(p[0]), float(p[1])) for p in dst4]
    A = []
    b_vec = []
    for (x, y), (X, Y) in zip(src, dst):
        A.append([x, y, 1, 0, 0, 0, -x*X, -y*X])
        A.append([0, 0, 0, x, y, 1, -x*Y, -y*Y])
        b_vec.append(X)
        b_vec.append(Y)
    A = np.array(A, dtype=np.float64)
    b_vec = np.array(b_vec, dtype=np.float64)
    result, _, _, _ = np.linalg.lstsq(A, b_vec, rcond=None)
    return tuple(result)

def cv2_gaussian_blur(arr, ksize=5):
    img = numpy_to_pil(arr)
    img = img.filter(ImageFilter.GaussianBlur(radius=ksize//2))
    return pil_to_numpy(img)

def cv2_add_weighted(arr1, a1, arr2, a2, gamma):
    res = np.clip(arr1.astype(np.float32)*a1 + arr2.astype(np.float32)*a2 + gamma, 0, 255)
    return res.astype(np.uint8)

def arr_to_imagetk(arr, zoom=1.0):
    img = numpy_to_pil(arr)
    if zoom != 1.0:
        w = max(1, int(img.width * zoom))
        h = max(1, int(img.height * zoom))
        img = img.resize((w, h), Image.BILINEAR)
    return ImageTk.PhotoImage(img)

def perspective_inverse_transform(coeffs_fwd, pts):
    pass


def compute_perspective_matrix(src4, dst4):
    return _compute_pil_perspective(src4, dst4)


def apply_perspective_to_points(coeffs, points):
    a, b, c, d, e, f, g, h = coeffs
    result = []
    for pt in points:
        x, y = float(pt[0]), float(pt[1])
        denom = g*x + h*y + 1.0
        if abs(denom) < 1e-10:
            result.append([x, y])
        else:
            X = (a*x + b*y + c) / denom
            Y = (d*x + e*y + f) / denom
            result.append([X, Y])
    return result


# ─────────────────────────────────────────────────────────────
# Chụp màn hình thay pyautogui
# ─────────────────────────────────────────────────────────────
def take_screenshot(region=None):
    if region:
        x1, y1, x2, y2 = region
        return ImageGrab.grab(bbox=(x1, y1, x2, y2))
    else:
        return ImageGrab.grab()


# ─────────────────────────────────────────────────────────────
# Sắp xếp 4 điểm: TL, TR, BR, BL
# ─────────────────────────────────────────────────────────────
def order_points(pts):
    pts = np.array(pts, dtype=np.float32)
    sc = pts.sum(axis=1)
    dc = np.diff(pts, axis=1).flatten()
    tl = pts[np.argmin(sc)]
    br = pts[np.argmax(sc)]
    tr = pts[np.argmin(dc)]
    bl = pts[np.argmax(dc)]
    return [tl.tolist(), tr.tolist(), br.tolist(), bl.tolist()]


# ─────────────────────────────────────────────────────────────
# Hàm tiện ích: căn giữa popup/dialog theo cửa sổ root
# ─────────────────────────────────────────────────────────────
def center_on_root(popup, root, pw, ph):
    """
    Đặt popup (kích thước pw x ph) vào giữa cửa sổ root hiện tại,
    dù root đang ở đâu trên màn hình hay ở monitor nào.
    Gọi SAU khi đã set geometry kích thước, TRƯỚC khi deiconify/grab.
    """
    root.update_idletasks()
    popup.update_idletasks()
    rx = root.winfo_rootx()
    ry = root.winfo_rooty()
    rw = root.winfo_width()
    rh = root.winfo_height()
    x = rx + (rw - pw) // 2
    y = ry + (rh - ph) // 2
    # Đảm bảo không bị ra ngoài màn hình (phòng trường hợp màn hình nhỏ)
    x = max(0, x)
    y = max(0, y)
    popup.geometry("{}x{}+{}+{}".format(pw, ph, x, y))


# ─────────────────────────────────────────────────────────────
# Popup thông báo tính năng cao cấp (dùng chung)
# ─────────────────────────────────────────────────────────────
def show_premium_popup(root, app=None, feature_name="Tính năng này"):
    """Hiển thị popup thông báo tính năng chỉ có trong bản cao cấp."""
    popup = tk.Toplevel(root)
    popup.title("Tính năng cao cấp")
    try:
        if app and getattr(app, '_icon_ico_path', None):
            popup.iconbitmap(app._icon_ico_path)
        elif app and getattr(app, '_icon_png_img', None):
            popup.iconphoto(False, app._icon_png_img)
    except Exception:
        pass
    popup.resizable(False, False)
    popup.configure(bg='white')
    popup.attributes('-topmost', True)

    pw, ph = 420, 360
    center_on_root(popup, root, pw, ph)

    popup.grab_set()

    # Header vàng nổi bật
    header = tk.Frame(popup, bg='#f39c12', height=56)
    header.pack(fill='x')
    header.pack_propagate(False)
    tk.Label(header,
             text="  Tính năng Cao cấp  ",
             font=('Arial', 13, 'bold'), bg='#f39c12', fg='white').pack(expand=True)

    # Tên tính năng
    tk.Label(popup,
             text="「 {} 」".format(feature_name),
             font=('Arial', 11, 'bold'), bg='white', fg='#c0392b').pack(pady=(14, 2))

    tk.Label(popup,
             text="chỉ có trong  Bản Cao Cấp",
             font=('Arial', 10), bg='white', fg='#7f8c8d').pack(pady=(0, 10))

    # Card giá
    price_card = tk.Frame(popup, bg='#eafaf1', relief='solid', bd=1)
    price_card.pack(fill='x', padx=30, pady=(0, 10))
    tk.Label(price_card,
             text="Chỉ  79.000 VNĐ",
             font=('Arial', 16, 'bold'), bg='#eafaf1', fg='#27ae60').pack(pady=(10, 2))
    tk.Label(price_card,
             text="Mua một lần – Dùng vĩnh viễn",
             font=('Arial', 9), bg='#eafaf1', fg='#7f8c8d').pack(pady=(0, 10))

    # Thông tin liên hệ
    contact_card = tk.Frame(popup, bg='#eaf4fb', relief='solid', bd=1)
    contact_card.pack(fill='x', padx=30, pady=(0, 14))

    tk.Label(contact_card,
             text="Liên hệ để mua bản cao cấp:",
             font=('Arial', 9, 'bold'), bg='#eaf4fb', fg='#2c3e50').pack(pady=(8, 2))

    tk.Label(contact_card,
             text="Lập Phạm  –  ĐT / Zalo: 0357 519 915",
             font=('Arial', 10, 'bold'), bg='#eaf4fb', fg='#2c3e50').pack(pady=(0, 2))

    fb_lbl = tk.Label(contact_card,
                      text="Facebook: fb.com/daiklap",
                      font=('Arial', 10, 'bold'), bg='#eaf4fb', fg='#2980b9',
                      cursor='hand2')
    fb_lbl.pack(pady=(0, 8))
    fb_lbl.bind('<Button-1>', lambda e: webbrowser.open('https://fb.com/daiklap'))

    # Nút đóng
    tk.Button(popup, text="Đã hiểu, đóng lại", command=popup.destroy,
              font=('Arial', 10, 'bold'), bg='#2980b9', fg='white',
              relief='raised', bd=2, padx=20, pady=6,
              cursor='hand2').pack(pady=(0, 16))


# ─────────────────────────────────────────────────────────────
# Wrapper filedialog luôn hiện giữa root
# ─────────────────────────────────────────────────────────────
def ask_open_filename(root, **kwargs):
    """filedialog.askopenfilename với parent=root để dialog hiện gần cửa sổ chính."""
    kwargs.setdefault('parent', root)
    return filedialog.askopenfilename(**kwargs)

def ask_save_filename(root, **kwargs):
    """filedialog.asksaveasfilename với parent=root để dialog hiện gần cửa sổ chính."""
    kwargs.setdefault('parent', root)
    return filedialog.asksaveasfilename(**kwargs)

def ask_directory(root, **kwargs):
    """filedialog.askdirectory với parent=root để dialog hiện gần cửa sổ chính."""
    kwargs.setdefault('parent', root)
    return filedialog.askdirectory(**kwargs)


# ─────────────────────────────────────────────────────────────
class RegistryManager:
    def __init__(self):
        self.key_path = r"SOFTWARE\FileManager"
        self.region_value_name = "CaptureRegion"
        self.last_image_dir_value_name = "LastImageDir"

    def save_last_image_dir(self, folder):
        if not REGISTRY_AVAILABLE or not folder:
            return False
        try:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, self.key_path) as key:
                winreg.SetValueEx(key, self.last_image_dir_value_name, 0, winreg.REG_SZ, folder)
            return True
        except Exception as e:
            print("Lỗi lưu đường dẫn ảnh vào registry: {}".format(e))
            return False

    def load_last_image_dir(self):
        if not REGISTRY_AVAILABLE:
            return None
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.key_path) as key:
                folder, _ = winreg.QueryValueEx(key, self.last_image_dir_value_name)
                if folder and os.path.isdir(folder):
                    return folder
        except Exception:
            pass
        return None

    def save_capture_region(self, region):
        if not REGISTRY_AVAILABLE or not region:
            return False
        try:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, self.key_path) as key:
                winreg.SetValueEx(key, self.region_value_name, 0, winreg.REG_SZ,
                                  "{},{},{},{}".format(*region))
            return True
        except Exception as e:
            print("Lỗi lưu registry: {}".format(e))
            return False

    def load_capture_region(self):
        if not REGISTRY_AVAILABLE:
            return None
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.key_path) as key:
                region_str, _ = winreg.QueryValueEx(key, self.region_value_name)
                coords = region_str.split(",")
                if len(coords) == 4:
                    return tuple(int(x) for x in coords)
        except Exception:
            pass
        return None

    def delete_capture_region(self):
        if not REGISTRY_AVAILABLE:
            return False
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.key_path, 0, winreg.KEY_WRITE) as key:
                winreg.DeleteValue(key, self.region_value_name)
        except Exception:
            pass
        return True


class RegionSelector:
    def __init__(self):
        self.selecting = False
        self.start_x = self.start_y = None
        self.selection_window = None

    def start_selection(self):
        self.selecting = True
        self.region = None
        self.create_overlay()

    def create_overlay(self):
        self.selection_window = tk.Toplevel()
        self.selection_window.attributes('-fullscreen', True)
        self.selection_window.attributes('-alpha', 0.3)
        self.selection_window.attributes('-topmost', True)
        self.selection_window.configure(bg='black')
        self.selection_window.overrideredirect(True)
        self.canvas = tk.Canvas(self.selection_window, highlightthickness=0, bg='black', bd=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind('<Button-1>', self.on_click)
        self.canvas.bind('<B1-Motion>', self.on_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_release)
        self.canvas.bind('<Button-3>', self.cancel_selection)
        self.selection_window.bind('<Escape>', self.cancel_selection)
        self.selection_window.focus_set()
        self.canvas.focus_set()
        sw = self.selection_window.winfo_screenwidth()
        self.canvas.create_text(sw // 2, 50,
            text="Kéo chuột để chọn vùng chụp màn hình\nNhấn ESC để hủy",
            fill='white', font=('Arial', 16, 'bold'), justify=tk.CENTER)
        threading.Thread(target=self._esc_watcher, daemon=True).start()

    def _esc_watcher(self):
        while self.selecting and self.selection_window:
            try:
                if is_key_pressed(VK_ESCAPE):
                    self.selection_window.after(0, self.cancel_selection)
                    break
                time.sleep(0.05)
            except Exception:
                break

    def on_click(self, event):
        self.start_x, self.start_y = event.x, event.y

    def on_drag(self, event):
        if self.start_x is None:
            return
        self.canvas.delete('sel')
        self.canvas.create_rectangle(self.start_x, self.start_y, event.x, event.y,
                                     outline='red', width=2, tags='sel')
        self.canvas.delete('sz')
        self.canvas.create_text((self.start_x + event.x) // 2, (self.start_y + event.y) // 2,
                                text="{} x {}".format(abs(event.x-self.start_x), abs(event.y-self.start_y)),
                                fill='white', font=('Arial', 12, 'bold'), tags='sz')

    def on_release(self, event):
        if self.start_x is None:
            return
        x1 = min(self.start_x, event.x); y1 = min(self.start_y, event.y)
        x2 = max(self.start_x, event.x); y2 = max(self.start_y, event.y)
        self.region = (x1, y1, x2, y2)
        self.close_overlay()

    def cancel_selection(self, event=None):
        self.region = None
        self.close_overlay()

    def close_overlay(self):
        if self.selection_window:
            self.selection_window.destroy()
            self.selection_window = None
        self.selecting = False

    def get_region(self):
        return getattr(self, 'region', None)


# ─────────────────────────────────────────────────────────────
# TAB 1  –  Chụp ảnh
# ─────────────────────────────────────────────────────────────
class ScreenshotTab:
    def __init__(self, parent_frame, root, app=None):
        self.root = root
        self.app = app
        self.frame = parent_frame
        self.current_folder = ""
        self.opened_files = set()
        self.file_processes = {}
        self.files = []
        self.current_page = 0
        self.selected_file = None
        self.file_labels = {}
        self.hide_files_with_images = False
        sh = root.winfo_screenheight()
        sw = root.winfo_screenwidth()
        self.items_per_column = max(3, (sh - 150) // 30)
        self.num_columns = max(3, (sw - 50) // 200)
        self.items_per_page = self.items_per_column * self.num_columns
        self.region_selector = RegionSelector()
        self.registry_manager = RegistryManager()
        self.capture_region = None
        self._setup_ui()
        self._load_settings()
        self._start_key_listener()

    def _setup_ui(self):
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=1)

        toolbar = ttk.LabelFrame(self.frame, text="Chọn thư mục", padding="5")
        toolbar.grid(row=0, column=0, sticky='we', pady=(0, 5))
        toolbar.columnconfigure(1, weight=1)
        self.folder_frame = toolbar

        ttk.Button(toolbar, text="Chọn thư mục", command=self.select_folder).grid(row=0, column=0, padx=(0,8))
        self.folder_label = ttk.Label(toolbar, text="Chưa chọn thư mục", background="white", relief="sunken")
        self.folder_label.grid(row=0, column=1, sticky='we', padx=(0,8))
        ttk.Button(toolbar, text="Ẩn mẫu có ảnh", command=self.toggle_hide).grid(row=0, column=2, padx=4)
        ttk.Button(toolbar, text="Làm mới", command=self.refresh_files).grid(row=0, column=3, padx=4)
        ttk.Button(toolbar, text="Xóa vết mở", command=self.clear_opened).grid(row=0, column=4, padx=4)
        ttk.Button(toolbar, text="Chọn vùng chụp", command=self.select_region).grid(row=0, column=5, padx=4)
        ttk.Button(toolbar, text="Reset vùng chụp", command=self.reset_region).grid(row=0, column=6, padx=4)
        ttk.Button(toolbar, text="Hướng dẫn", command=self._show_help_popup).grid(row=0, column=7, padx=(12,0))

        self.region_label = ttk.Label(toolbar, text="Chụp toàn màn hình", background="lightgray", relief="sunken")
        self.region_label.grid(row=1, column=0, columnspan=7, sticky='we', pady=(5,0))

        flist = ttk.LabelFrame(self.frame, text="Danh sách file", padding="5")
        flist.grid(row=1, column=0, sticky='nswe')
        flist.columnconfigure(0, weight=1)
        flist.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(flist, bg='white')
        sb = ttk.Scrollbar(flist, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=sb.set)
        self.canvas.grid(row=0, column=0, sticky='nswe')
        sb.grid(row=0, column=1, sticky='ns')

        self.file_frame = ttk.Frame(self.canvas)
        self._cw = self.canvas.create_window((0, 0), window=self.file_frame, anchor='nw')
        self.canvas.bind('<MouseWheel>', self._wheel)
        self.file_frame.bind('<MouseWheel>', self._wheel)
        self.file_frame.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<Configure>', lambda e: self.canvas.itemconfig(self._cw, width=e.width))

    def _load_settings(self):
        r = self.registry_manager.load_capture_region()
        if r:
            self.capture_region = r
            x1, y1, x2, y2 = r
            self.region_label.config(
                text="Vùng chụp (đã lưu): {}x{} tại ({},{})".format(x2-x1, y2-y1, x1, y1),
                background="lightgreen")

    def save_settings(self):
        if self.capture_region:
            self.registry_manager.save_capture_region(self.capture_region)

    def reset_region(self):
        if messagebox.askyesno("Xác nhận", "Reset về chụp toàn màn hình?\nThông số đã lưu sẽ bị xóa.",
                               parent=self.root):
            self.capture_region = None
            self.registry_manager.delete_capture_region()
            self.region_label.config(text="Chụp toàn màn hình", background="lightgray")

    def select_region(self):
        self.root.withdraw()
        time.sleep(0.2)
        self.region_selector.start_selection()
        self.root.after(100, self._check_region)

    def _check_region(self):
        if self.region_selector.selecting:
            self.root.after(100, self._check_region)
            return
        r = self.region_selector.get_region()
        if r:
            self.capture_region = r
            x1, y1, x2, y2 = r
            self.region_label.config(
                text="Vùng chụp: {}x{} tại ({},{})".format(x2-x1, y2-y1, x1, y1),
                background="lightblue")
            self.save_settings()
        else:
            self.region_label.config(text="Chụp toàn màn hình")
        self.root.deiconify()
        self.root.state('zoomed')
        self.root.focus_force()

    def clear_opened(self):
        if not self.opened_files:
            messagebox.showinfo("Thông báo", "Không có file nào đã được mở!", parent=self.root)
            return
        if messagebox.askyesno("Xác nhận", "Xóa vết mở của {} file?".format(len(self.opened_files)),
                               parent=self.root):
            for proc in self.file_processes.values():
                try:
                    if proc and proc.poll() is None:
                        proc.terminate()
                except Exception:
                    pass
            self.opened_files.clear()
            self.file_processes.clear()
            self.selected_file = None
            self.display_page()

    def toggle_hide(self):
        self.hide_files_with_images = not self.hide_files_with_images
        txt = "Hiện tất cả file" if self.hide_files_with_images else "Ẩn mẫu có ảnh"
        for w in self.folder_frame.winfo_children():
            if isinstance(w, ttk.Button) and w.cget("text") in ["Ẩn mẫu có ảnh", "Hiện tất cả file"]:
                w.configure(text=txt)
                break
        self.current_page = 0
        self.refresh_files()

    def _show_help_popup(self):
        popup = tk.Toplevel(self.root)
        popup.title("Hướng dẫn sử dụng")
        try:
            if self.app and getattr(self.app, '_icon_ico_path', None):
                popup.iconbitmap(self.app._icon_ico_path)
            elif self.app and getattr(self.app, '_icon_png_img', None):
                popup.iconphoto(False, self.app._icon_png_img)
        except Exception:
            pass
        popup.resizable(False, False)
        popup.configure(bg='white')

        pw, ph = 480, 420
        center_on_root(popup, self.root, pw, ph)
        popup.grab_set()

        tk.Label(popup, text="Hướng dẫn sử dụng - Tab Chụp ảnh",
                 font=('Arial', 13, 'bold'), bg='white', fg='#2c3e50').pack(pady=(16, 6))

        frame = tk.Frame(popup, bg='#f4f6f8', relief='solid', bd=1)
        frame.pack(fill='both', expand=True, padx=20, pady=(0, 10))

        lines = [
            ("Chọn thư mục",    "Chọn thư mục chứa các file mẫu cần chụp ảnh."),
            ("Ẩn mẫu có ảnh",   "Ẩn các file đã có ảnh chụp, chỉ hiện file chưa chụp."),
            ("Làm mới",         "Tải lại danh sách file trong thư mục đang chọn."),
            ("Xóa vết mở",      "Xóa trạng thái đã mở của tất cả file (màu xanh)."),
            ("Chọn vùng chụp",  "Kéo chuột để chọn vùng màn hình sẽ được chụp."),
            ("Reset vùng chụp", "Quay về chụp toàn màn hình, xóa vùng đã lưu."),
            ("Mở file",         "Click 1 lần vào tên file để mở. File đã mở hiện màu xanh."),
            ("Chụp ảnh (TAB)",  "Nhấn phím TAB (giữ < 2 giây rồi nhả) để chụp màn hình."),
        ]

        for i, (title, desc) in enumerate(lines):
            row_bg = 'white' if i % 2 == 0 else '#f4f6f8'
            row = tk.Frame(frame, bg=row_bg)
            row.pack(fill='x')
            tk.Label(row, text="  {}".format(title), font=('Arial', 9, 'bold'), bg=row_bg,
                     fg='#2980b9', width=16, anchor='w').pack(side='left', padx=(4,0), pady=5)
            tk.Label(row, text=desc, font=('Arial', 9), bg=row_bg,
                     fg='#2c3e50', anchor='w', justify='left', wraplength=310).pack(
                     side='left', padx=8, pady=5, fill='x')

        tk.Button(popup, text="Đã hiểu, đóng lại", command=popup.destroy,
                  font=('Arial', 10), bg='#2980b9', fg='white',
                  relief='raised', bd=2, padx=20, pady=6, cursor='hand2').pack(pady=(0, 16))

    def select_folder(self):
        folder = ask_directory(self.root, title="Chọn thư mục chứa file")
        if folder:
            self.current_folder = folder
            self.folder_label.config(text=folder)
            self.current_page = 0
            self.refresh_files()

    def refresh_files(self):
        if not self.current_folder:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn thư mục trước!", parent=self.root)
            return
        for w in self.file_frame.winfo_children():
            w.destroy()
        self.file_labels.clear()
        try:
            all_files = [f for f in os.listdir(self.current_folder)
                         if os.path.isfile(os.path.join(self.current_folder, f))]
            if self.hide_files_with_images:
                img_ext = {'.png', '.jpg', '.bmp'}
                bases = {os.path.splitext(f)[0] for f in all_files
                         if os.path.splitext(f)[1].lower() in img_ext}
                self.files = [f for f in all_files if os.path.splitext(f)[0] not in bases]
            else:
                self.files = all_files
            self.display_page()
        except Exception as e:
            messagebox.showerror("Lỗi", "Không thể đọc thư mục: {}".format(e), parent=self.root)

    def display_page(self):
        for w in self.file_frame.winfo_children():
            w.destroy()
        self.file_labels.clear()
        start = self.current_page * self.items_per_page
        for col in range(self.num_columns):
            cf = ttk.Frame(self.file_frame)
            cf.grid(row=0, column=col, padx=10, sticky='n')
            for row in range(self.items_per_column):
                idx = start + col * self.items_per_column + row
                if idx >= len(self.files):
                    break
                fn = self.files[idx]
                fp = os.path.join(self.current_folder, fn)
                opened = fp in self.opened_files
                lbl = ttk.Label(cf, text=fn, width=30, anchor='w',
                                background='blue' if opened else 'white',
                                foreground='white' if opened else 'black',
                                font=('', 10, 'bold' if opened else 'normal'))
                lbl.grid(row=row, column=0, pady=5, sticky='w')
                self.file_labels[fp] = lbl
                lbl.bind('<Button-1>', lambda e, f=fn, p=fp: self._click(f, p))
                lbl.bind('<Double-Button-1>', lambda e, f=fn, p=fp: self._dbl(f, p))
                lbl.bind('<MouseWheel>', self._wheel)
                cf.bind('<MouseWheel>', self._wheel)
                if fn == self.selected_file:
                    lbl.configure(relief='sunken', borderwidth=2)
        for i in range(self.num_columns):
            self.file_frame.columnconfigure(i, weight=1)
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def _update_lbl(self, fp):
        if fp in self.file_labels:
            opened = fp in self.opened_files
            self.file_labels[fp].configure(
                background='blue' if opened else 'white',
                foreground='white' if opened else 'black',
                font=('', 10, 'bold' if opened else 'normal'))

    def _update_sel(self):
        for fp, lbl in self.file_labels.items():
            lbl.configure(
                relief='sunken' if os.path.basename(fp) == self.selected_file else 'flat',
                borderwidth=2 if os.path.basename(fp) == self.selected_file else 0)

    def _wheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _click(self, fn, fp):
        self.selected_file = fn
        self._update_sel()
        if fp not in self.opened_files:
            self._open(fp)

    def _dbl(self, fn, fp):
        self.selected_file = fn
        self._update_sel()
        if fp in self.opened_files:
            self._open(fp)

    def _open(self, fp):
        try:
            if platform.system() == 'Windows':
                proc = subprocess.Popen(['start', '', fp], shell=True)
            elif platform.system() == 'Darwin':
                proc = subprocess.Popen(['open', fp])
            else:
                proc = subprocess.Popen(['xdg-open', fp])
            self.opened_files.add(fp)
            self.file_processes[fp] = proc
            self._update_lbl(fp)
        except Exception as e:
            messagebox.showerror("Lỗi", "Không thể mở file: {}".format(e), parent=self.root)

    def take_screenshot(self):
        if not self.current_folder:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn thư mục trước!", parent=self.root)
            return
        if not self.selected_file:
            for fn in self.files:
                fp = os.path.join(self.current_folder, fn)
                if fp in self.opened_files:
                    self.selected_file = fn
                    break
        if not self.selected_file:
            messagebox.showwarning("Cảnh báo", "Không có file nào đang mở!", parent=self.root)
            return
        fp = os.path.join(self.current_folder, self.selected_file)
        if fp not in self.opened_files:
            messagebox.showwarning("Cảnh báo", "File chưa được mở!", parent=self.root)
            return
        try:
            self.root.withdraw()
            time.sleep(0.3)
            shot = take_screenshot(self.capture_region)
            base = os.path.splitext(self.selected_file)[0]
            shot.save(os.path.join(self.current_folder, "{}.png".format(base)))
            self.root.state('zoomed')
            self.root.deiconify()
            self.root.attributes('-topmost', True)
            self.root.focus_force()
            self.root.attributes('-topmost', False)
            if WINSOUND_AVAILABLE:
                winsound.Beep(1000, 200)
            if self.hide_files_with_images:
                self.refresh_files()
        except Exception as e:
            self.root.deiconify()
            messagebox.showerror("Lỗi", "Không thể chụp màn hình: {}".format(e), parent=self.root)

    def _start_key_listener(self):
        def _loop():
            pressed = False
            t0 = 0
            while True:
                try:
                    now = time.time()
                    if is_key_pressed(VK_TAB):
                        if not pressed:
                            pressed = True
                            t0 = now
                    else:
                        if pressed:
                            pressed = False
                            if now - t0 < 2.0:
                                self.take_screenshot()
                                time.sleep(0.3)
                    time.sleep(0.05)
                except Exception as e:
                    print("Key listener error: {}".format(e))
                    time.sleep(0.1)
        threading.Thread(target=_loop, daemon=True).start()


# ─────────────────────────────────────────────────────────────
# TAB 2  –  Chỉnh méo ảnh
# ─────────────────────────────────────────────────────────────
class DistortionTab:
    def __init__(self, parent_frame, root, app=None):
        self.root = root
        self.app = app
        self.frame = parent_frame
        self.source_image = None
        self.original_image = None
        self.current_image = None
        self.display_image = None
        self.base_image = None
        self.points = []
        self.offset_points = []
        self.rotated_cache = {}
        self.rotation_angle = 0.0
        self.zoom_level = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        self.is_panning = False
        self.is_stretching = False
        self.dragging_point_index = None
        self.point_hit_radius = 14
        self._rotation_pending = False
        self.stretch_x_factor = 1.0
        self.stretch_y_factor = 1.0
        self.stretch_handle = None
        self._stretch_pending = False
        self._stretch_base_iw = 0
        self._stretch_base_ih = 0
        self._stretch_origin_x = 0
        self._stretch_origin_y = 0
        self._scroll_bounds = (0.0, 0.0, 0.0, 0.0)
        self.show_grid = tk.BooleanVar()
        self.offset_count = 0
        self.max_offset = 10
        self.file_path = None
        self.undo_stack = []
        self.registry_manager = RegistryManager()
        self.last_image_dir = self.registry_manager.load_last_image_dir()
        self._setup_ui()
        self._bind()

    def _setup_ui(self):
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)

        main = tk.Frame(self.frame, bg='white')
        main.pack(fill='both', expand=True, padx=5, pady=5)

        left = tk.Frame(main, bg='white', relief='solid', bd=1)
        left.pack(side='left', fill='both', expand=True, padx=(0, 5))

        cf = tk.Frame(left)
        cf.pack(fill='both', expand=True, padx=5, pady=5)
        self.canvas = tk.Canvas(cf, bg='white', cursor='crosshair')
        vsb = ttk.Scrollbar(cf, orient='vertical', command=self.canvas.yview)
        hsb = ttk.Scrollbar(cf, orient='horizontal', command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')
        self.canvas.pack(side='left', fill='both', expand=True)

        right = tk.Frame(main, bg='white', width=240, relief='solid', bd=1)
        right.pack(side='right', fill='y', padx=(5, 0))
        right.pack_propagate(False)

        tk.Button(right, text="Chọn ảnh", command=self.load_image,
                  font=('Arial', 11), bg='white', fg='black', relief='raised', bd=2,
                  padx=15, pady=4).pack(pady=(8, 4), fill='x', padx=15)

        zf = tk.LabelFrame(right, text="Điều khiển xem", font=('Arial', 9), bg='white', fg='black')
        zf.pack(fill='x', padx=15, pady=5)
        tk.Button(zf, text="Ảnh toàn màn Full", command=self.fit_to_canvas,
                  font=('Arial', 8), bg='white', relief='raised', bd=2).pack(fill='x', padx=5, pady=2)

        self._rotate_job = None
        self._rotate_hold_job = None

        slf = tk.Frame(zf, bg='white')
        slf.pack(fill='x', padx=5, pady=(2, 0))

        def _start_rotate(delta):
            self._push_undo("Xoay {:.1f}".format(self.rotation_angle))
            if self.current_image is not None:
                self.rotation_angle = round(self.rotation_angle + delta, 1)
                self.rotation_var.set(self.rotation_angle)
                self._apply_rotation()
            def _begin_spin():
                def _spin():
                    if self.current_image is None:
                        return
                    self.rotation_angle = round(self.rotation_angle + delta, 1)
                    self.rotation_var.set(self.rotation_angle)
                    self._apply_rotation()
                    self._rotate_job = slf.after(80, _spin)
                _spin()
            self._rotate_hold_job = slf.after(600, _begin_spin)

        def _stop_rotate():
            if self._rotate_hold_job is not None:
                slf.after_cancel(self._rotate_hold_job)
                self._rotate_hold_job = None
            if self._rotate_job is not None:
                slf.after_cancel(self._rotate_job)
                self._rotate_job = None

        btn_ccw = tk.Button(slf, text="<", font=('Arial', 9), bg='white', relief='raised', bd=2)
        btn_ccw.pack(side='left', padx=(0, 2))
        btn_ccw.bind('<ButtonPress-1>',   lambda e: _start_rotate(-0.1))
        btn_ccw.bind('<ButtonRelease-1>', lambda e: _stop_rotate())

        self.rotation_var = tk.DoubleVar(value=0.0)
        self.rotation_slider = tk.Scale(
            slf, from_=-180, to=180, resolution=0.1,
            orient=tk.HORIZONTAL, variable=self.rotation_var,
            bg='white', fg='black', highlightthickness=0,
            troughcolor='#ddd', showvalue=False,
            command=lambda v: self._on_slider_rotate(v))
        self.rotation_slider.pack(side='left', fill='x', expand=True, padx=2)

        btn_cw = tk.Button(slf, text=">", font=('Arial', 9), bg='white', relief='raised', bd=2)
        btn_cw.pack(side='left', padx=(2, 0))
        btn_cw.bind('<ButtonPress-1>',   lambda e: _start_rotate(0.1))
        btn_cw.bind('<ButtonRelease-1>', lambda e: _stop_rotate())

        # ── Nhãn hiển thị góc – click mở popup nhập góc (CAO CẤP) ──
        self.rotation_angle_label = tk.Label(zf, text="0.0", font=('Arial', 8), bg='white',
                                              cursor='hand2', relief='groove', bd=1, padx=4)
        self.rotation_angle_label.pack(pady=(0, 2))
        self.rotation_angle_label.bind('<Button-1>', lambda e: self._show_angle_popup())

        gf = tk.Frame(zf, bg='white')
        gf.pack(fill='x', padx=5, pady=(0, 2))
        tk.Checkbutton(gf, text="Hiển thị lưới", variable=self.show_grid,
                       command=self._toggle_grid, font=('Arial', 9), bg='white').pack(side='left', anchor='w')
        self.zoom_label = tk.Label(gf, text="Zoom: 100%", font=('Arial', 9), bg='white')
        self.zoom_label.pack(side='right')

        ctrl = tk.LabelFrame(right, text="Điều khiển", font=('Arial', 9), bg='white', fg='black')
        ctrl.pack(fill='x', padx=15, pady=(2, 3))

        # ── Nút Tạo viền offset (CAO CẤP) ──
        self.offset_btn = tk.Button(ctrl, text="Tạo viền offset ",
                                    command=self.create_offset_border,
                                    font=('Arial', 10), bg='white', relief='raised', bd=2, state='disabled')
        self.offset_btn.pack(fill='x', padx=8, pady=3)

        self.correct_btn = tk.Button(ctrl, text="Chỉnh sửa méo", command=self.correct_distortion,
                                     font=('Arial', 10), bg='white', relief='raised', bd=2, state='disabled')
        self.correct_btn.pack(fill='x', padx=8, pady=3)

        sharpen_row = tk.Frame(ctrl, bg='white')
        sharpen_row.pack(fill='x', padx=8, pady=3)
        self.sharpen_btn = tk.Button(sharpen_row, text="Làm nét ảnh", command=self.sharpen_image,
                                     font=('Arial', 10), bg='white', relief='raised', bd=2)
        self.sharpen_btn.pack(side='left', fill='x', expand=True, padx=(0, 2))

        # ── Nút Copy ảnh (CAO CẤP) ──
        self.copy_btn = tk.Button(sharpen_row, text="Copy ảnh ", command=self.copy_image,
                                  font=('Arial', 10), bg='white', relief='raised', bd=2)
        self.copy_btn.pack(side='left', fill='x', expand=True, padx=(2, 0))

        flipf = tk.Frame(ctrl, bg='white')
        flipf.pack(fill='x', padx=8, pady=3)
        tk.Button(flipf, text="Lật 90 CW", command=lambda: self.rotate_flip(90),
                  font=('Arial', 9), bg='white', relief='raised', bd=2).pack(side='left', fill='x', expand=True, padx=(0, 2))
        tk.Button(flipf, text="Lật 90 CCW", command=lambda: self.rotate_flip(-90),
                  font=('Arial', 9), bg='white', relief='raised', bd=2).pack(side='left', fill='x', expand=True, padx=2)

        flipf2 = tk.Frame(ctrl, bg='white')
        flipf2.pack(fill='x', padx=8, pady=(0, 3))
        tk.Button(flipf2, text="Lật Ngang", command=lambda: self.flip_image(1),
                  font=('Arial', 9), bg='white', relief='raised', bd=2).pack(side='left', fill='x', expand=True, padx=(0, 2))
        tk.Button(flipf2, text="Lật Dọc", command=lambda: self.flip_image(0),
                  font=('Arial', 9), bg='white', relief='raised', bd=2).pack(side='left', fill='x', expand=True, padx=2)

        bf = tk.Frame(ctrl, bg='white')
        bf.pack(fill='x', padx=8, pady=(3, 6))
        tk.Button(bf, text="Reset", command=self.reset_image, font=('Arial', 9),
                  bg='white', relief='raised', bd=2).pack(side='left', fill='x', expand=True, padx=(0, 3))
        self.restore_btn = tk.Button(bf, text="Ảnh gốc", command=self.reload_original,
                                     font=('Arial', 9), bg='white', relief='raised', bd=2, state='disabled')
        self.restore_btn.pack(side='left', fill='x', expand=True, padx=3)
        self.save_btn = tk.Button(bf, text="Lưu ảnh", command=self.save_image,
                                  font=('Arial', 9), bg='white', relief='raised', bd=2, state='disabled')
        self.save_btn.pack(side='right', fill='x', expand=True, padx=(3, 0))

        self.status_label = tk.Label(right, text="Chưa tải ảnh", font=('Arial', 9),
                                     bg='lightgray', relief='solid', bd=1, pady=4)
        self.status_label.pack(fill='x', padx=15, pady=(0, 5))

        inf = tk.LabelFrame(right, text="Hướng dẫn", font=('Arial', 9), bg='white', fg='black')
        inf.pack(fill='x', padx=15, pady=(1, 3))
        for t in [
            "1. Tải ảnh cần chỉnh sửa",
            "2. Click 4 điểm góc hình bình hành",
            "3. Bấm 'Chỉnh sửa méo' hoặc 'Tạo viền offset'",
            "4. Lưu ảnh / Copy ảnh để dán sang nơi khác",
            "─────────────────────────",
            "Cuộn lăn chuột: Zoom in/out (tại vị trí con trỏ)",
            "Chuột phải + kéo: Di chuyển ảnh",
            "Kéo ô vàng cạnh phải: Dãn ngang",
            "Kéo ô vàng cạnh dưới: Dãn dọc",
            "Kéo điểm đỏ: Di chuyển điểm đã chọn",
            "Nút < >: Click=+-0.1, Giữ=liên tục",
            "Thanh trượt: Xoay tự do +-180",
            "Ctrl+Z: Hoàn tác",
            "─────────────────────────",
            " = Tính năng Bản Cao Cấp",
            "    LH: Lập Phạm 0357 519 915",
        ]:
            lbl_color = '#c0392b' if t.startswith("") or t.startswith("    LH") else '#2c3e50'
            tk.Label(inf, text=t, font=('Arial', 8), bg='white', anchor='w',
                     pady=0, bd=0, highlightthickness=0, fg=lbl_color).pack(anchor='w', fill='x', padx=6, pady=0)

    def _bind(self):
        self.canvas.bind("<Button-1>", self._click)
        self.canvas.bind("<B1-Motion>", self._drag)
        self.canvas.bind("<ButtonRelease-1>", self._release)
        self.canvas.bind("<MouseWheel>", self._wheel)
        self.canvas.bind("<Button-4>", self._wheel)
        self.canvas.bind("<Button-5>", self._wheel)
        self.canvas.bind("<Button-3>", self._pan_start)
        self.canvas.bind("<B3-Motion>", self._pan_do)
        self.canvas.bind("<ButtonRelease-3>", self._pan_end)
        self.canvas.bind("<Motion>", self._update_handles)
        self.canvas.bind("<Control-z>", lambda e: self.undo())
        self.canvas.bind("<Control-Z>", lambda e: self.undo())
        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Control-Z>", lambda e: self.undo())

    def activate(self):
        self.canvas.focus_set()

    def _push_undo(self, label=""):
        if self.current_image is None:
            return
        state = {
            'current_image':  self.current_image.copy(),
            'original_image': self.original_image.copy() if self.original_image is not None else None,
            'base_image':     self.base_image.copy()     if self.base_image is not None else None,
            'source_image':   self.source_image.copy()   if self.source_image is not None else None,
            'points':         [p[:] for p in self.points],
            'offset_points':  [p[:] for p in self.offset_points],
            'offset_count':   self.offset_count,
            'rotation_angle': self.rotation_angle,
            'sharpen_used':   self.sharpen_btn['state'] == 'disabled',
            'label':          label,
        }
        self.undo_stack.append(state)
        if len(self.undo_stack) > 20:
            self.undo_stack.pop(0)

    def undo(self):
        if not self.undo_stack:
            self.status_label.config(text="Không có thao tác nào để hoàn tác!", bg='#ffe0e0')
            return
        state = self.undo_stack.pop()
        self.current_image  = state['current_image']
        self.original_image = state['original_image']
        self.base_image     = state['base_image']
        self.source_image   = state['source_image']
        self.points         = state['points']
        self.offset_points  = state['offset_points']
        self.offset_count   = state['offset_count']
        self.rotation_angle = state['rotation_angle']
        self.rotation_var.set(self.rotation_angle)
        self.rotation_angle_label.config(text="{:.1f}".format(self.rotation_angle))
        self.rotated_cache  = {}
        if state['sharpen_used']:
            self.sharpen_btn.config(state='disabled', bg='#f0f0f0', fg='#aaaaaa')
        else:
            self.sharpen_btn.config(state='normal', bg='white', fg='black')
        if len(self.points) == 4:
            self.correct_btn.config(state='normal')
            self.offset_btn.config(state='normal')
        else:
            self.correct_btn.config(state='disabled')
            self.offset_btn.config(state='disabled')
        lbl = state['label']
        self.root.after(30, self.fit_to_canvas)
        self.status_label.config(
            text="Đã hoàn tác: {}  (còn {} bước)".format(lbl, len(self.undo_stack)) if lbl
                 else "Đã hoàn tác  (còn {} bước)".format(len(self.undo_stack)),
            bg='lightyellow')

    def load_image(self):
        fp = ask_open_filename(
            self.root,
            title="Chọn ảnh",
            initialdir=self.last_image_dir if self.last_image_dir else None,
            filetypes=[
                ("Tất cả ảnh hỗ trợ", "*.jpg *.jpeg *.png *.bmp *.tiff *.tif *.webp"),
                ("JPEG", "*.jpg *.jpeg"),
                ("PNG", "*.png"),
                ("WebP", "*.webp"),
                ("Bitmap", "*.bmp"),
                ("TIFF", "*.tiff *.tif"),
                ("Tất cả file", "*.*"),
            ])
        if not fp:
            return
        try:
            self.file_path = fp
            folder = os.path.dirname(fp)
            if folder and folder != self.last_image_dir:
                self.last_image_dir = folder
                self.registry_manager.save_last_image_dir(folder)
            self.source_image = cv2_imread(fp)
            self.original_image = self.source_image.copy()
            self.current_image = self.source_image.copy()
            self.base_image = self.source_image.copy()
            self._reset_state()
            self.rotation_var.set(0.0)
            self.rotation_angle_label.config(text="0.0")
            self.root.after(100, self.fit_to_canvas)
            self.status_label.config(text="Đã tải ảnh. Vẽ 4 điểm góc hình bình hành", bg='lightgreen')
            self.save_btn.config(state='normal')
            self.restore_btn.config(state='normal')
            self.sharpen_btn.config(state='normal', bg='white', fg='black')
        except Exception as e:
            messagebox.showerror("Lỗi", "Không thể tải ảnh: {}".format(e), parent=self.root)

    def reload_original(self):
        if not self.file_path:
            return
        try:
            self.source_image = cv2_imread(self.file_path)
            self.original_image = self.source_image.copy()
            self.current_image = self.source_image.copy()
            self.base_image = self.source_image.copy()
            self._reset_state()
            self.rotation_var.set(0.0)
            self.rotation_angle_label.config(text="0.0")
            self.root.after(100, self.fit_to_canvas)
            self.status_label.config(text="Đã khôi phục ảnh gốc.", bg='lightgreen')
            self.sharpen_btn.config(state='normal', bg='white', fg='black')
        except Exception as e:
            messagebox.showerror("Lỗi", "Không thể khôi phục: {}".format(e), parent=self.root)

    def _reset_state(self):
        self.points = []
        self.offset_points = []
        self.rotated_cache = {}
        self.rotation_angle = 0.0
        self.stretch_x_factor = 1.0
        self.stretch_y_factor = 1.0
        self.offset_count = 0
        self.correct_btn.config(state='disabled')
        self.offset_btn.config(state='disabled')

    # ── Copy ảnh → PREMIUM ──────────────────────────────────
    def copy_image(self):
        show_premium_popup(self.root, self.app, "Copy ảnh vào Clipboard")

    # ── Làm nét ảnh (giữ nguyên free) ───────────────────────
    def sharpen_image(self):
        if self.current_image is None:
            return
        self._push_undo("Làm nét ảnh")
        blurred = cv2_gaussian_blur(self.current_image, 5)
        self.current_image = cv2_add_weighted(self.current_image, 1.5, blurred, -0.5, 0)
        self.original_image = self.current_image.copy()
        self.base_image = self.current_image.copy()
        self.rotated_cache = {}
        self.rotation_angle = 0.0
        self.rotation_var.set(0.0)
        self.rotation_angle_label.config(text="0.0")
        self._draw()
        self.source_image = self.current_image.copy()
        self.sharpen_btn.config(state='disabled', bg='#f0f0f0', fg='#aaaaaa')
        self.status_label.config(text="Đã làm nét ảnh! (chỉ dùng 1 lần)", bg='lightgreen')

    def rotate_flip(self, degrees):
        if self.current_image is None:
            return
        lbl = "Lật CW +90" if degrees == 90 else "Lật CCW -90"
        self._push_undo(lbl)
        if degrees == 90:
            self.current_image = cv2_rotate_90cw(self.current_image)
        else:
            self.current_image = cv2_rotate_90ccw(self.current_image)
        self.original_image = self.current_image.copy()
        self.base_image = self.current_image.copy()
        self.source_image = self.current_image.copy()
        self.points = []
        self.offset_points = []
        self.offset_count = 0
        self.rotated_cache = {}
        self.rotation_angle = 0.0
        self.rotation_var.set(0.0)
        self.rotation_angle_label.config(text="0.0")
        self.root.after(50, self.fit_to_canvas)
        self.status_label.config(text="Đã {}. Vẽ 4 điểm để chỉnh méo.".format(lbl), bg='lightyellow')

    def flip_image(self, flip_code):
        if self.current_image is None:
            return
        lbl = "Lật phản chiếu ngang" if flip_code == 1 else "Lật phản chiếu dọc"
        self._push_undo(lbl)
        self.current_image = cv2_flip(self.current_image, flip_code)
        self.original_image = self.current_image.copy()
        self.base_image = self.current_image.copy()
        self.source_image = self.current_image.copy()
        self.points = []
        self.offset_points = []
        self.offset_count = 0
        self.rotated_cache = {}
        self.rotation_angle = 0.0
        self.rotation_var.set(0.0)
        self.rotation_angle_label.config(text="0.0")
        self._draw()
        self.status_label.config(text="Đã {}.".format(lbl), bg='lightyellow')

    def _on_slider_rotate(self, val):
        if self.current_image is None:
            return
        self.rotation_angle = round(float(val), 1)
        if getattr(self, '_rotation_pending', False):
            return
        self._rotation_pending = True
        self.root.after(15, self._apply_rotation_debounced)

    def _apply_rotation_debounced(self):
        self._rotation_pending = False
        self._apply_rotation()

    # ── Nhập góc xoay → PREMIUM ─────────────────────────────
    def _show_angle_popup(self):
        """Click vào nhãn góc: hiển thị popup bản cao cấp thay vì cho nhập."""
        show_premium_popup(self.root, self.app, "Nhập góc xoay tùy ý")

    def rotate_by_key(self, delta):
        if self.current_image is None:
            return
        self._push_undo("Xoay {:.1f}".format(self.rotation_angle))
        self.rotation_angle = round(self.rotation_angle + delta, 1)
        self.rotation_var.set(self.rotation_angle)
        self._apply_rotation()

    def _apply_rotation(self):
        if self.base_image is None:
            return
        a = self.rotation_angle
        if a in self.rotated_cache:
            rotated = self.rotated_cache[a]
        else:
            rotated = cv2_warp_affine_rotation(self.base_image, a)
            if len(self.rotated_cache) > 60:
                del self.rotated_cache[next(iter(self.rotated_cache))]
            self.rotated_cache[a] = rotated

        self.current_image = rotated
        self.points = []
        self.offset_points = []
        self.offset_count = 0
        self.rotation_angle_label.config(text="{:.1f}".format(a))
        self._draw()
        self.status_label.config(text="Xoay {:.1f}. Vẽ 4 điểm để chỉnh méo.".format(a), bg='lightyellow')

    def _get_image_offset(self):
        if self.current_image is None:
            return 0, 0
        ih, iw = self.current_image.shape[:2]
        dw = int(iw * self.zoom_level)
        dh = int(ih * self.zoom_level)
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        ox = max(0, (cw - dw) // 2)
        oy = max(0, (ch - dh) // 2)
        return ox, oy

    def _draw(self):
        if self.current_image is None:
            return
        self.canvas.update_idletasks()
        ih, iw = self.current_image.shape[:2]
        dw, dh = max(1, int(iw * self.zoom_level)), max(1, int(ih * self.zoom_level))
        img_pil = numpy_to_pil(self.current_image)
        resample = Image.NEAREST if abs(self.zoom_level - 1.0) > 1e-6 else Image.BILINEAR
        img_pil = img_pil.resize((dw, dh), resample)
        self.display_image = ImageTk.PhotoImage(img_pil)
        ox, oy = self._get_image_offset()
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()

        margin = 30
        min_x, min_y = 0.0, 0.0
        max_x, max_y = float(dw), float(dh)
        for pt in self.points + self.offset_points:
            px = pt[0] * self.zoom_level
            py = pt[1] * self.zoom_level
            min_x = min(min_x, px)
            min_y = min(min_y, py)
            max_x = max(max_x, px)
            max_y = max(max_y, py)
        min_x -= margin
        min_y -= margin
        max_x += margin
        max_y += margin

        sr_x1 = min(0, ox + min_x)
        sr_y1 = min(0, oy + min_y)
        sr_x2 = max(cw, ox + max_x)
        sr_y2 = max(ch, oy + max_y)

        self.canvas.delete("all")
        self.canvas.configure(scrollregion=(sr_x1, sr_y1, sr_x2, sr_y2))
        self._scroll_bounds = (sr_x1, sr_y1, sr_x2, sr_y2)
        self.canvas.create_image(ox, oy, anchor='nw', image=self.display_image)
        self._draw_grid(ox, oy)
        self._draw_points(ox, oy)
        self._draw_handles(ox, oy)

    def fit_to_canvas(self):
        if self.current_image is None:
            return
        self.canvas.update_idletasks()
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        if cw <= 1 or ch <= 1:
            self.root.after(50, self.fit_to_canvas)
            return
        ih, iw = self.current_image.shape[:2]
        self.zoom_level = max(self.min_zoom, min(self.max_zoom, min(cw / iw, ch / ih) * 0.95))
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)
        self._draw()
        self._upd_zoom()

    def _upd_zoom(self):
        self.zoom_label.config(text="Zoom: {}%".format(int(self.zoom_level * 100)))

    def _wheel(self, event):
        if self.current_image is None:
            return
        if getattr(event, 'num', None) == 4:
            steps = 1.0
        elif getattr(event, 'num', None) == 5:
            steps = -1.0
        else:
            d = event.delta
            steps = d / 120.0 if d != 0 else 0.0
            if steps == 0:
                return
        f = 1.15 ** steps
        old_zoom = self.zoom_level
        nz = max(self.min_zoom, min(self.max_zoom, old_zoom * f))
        if nz == old_zoom:
            return

        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)

        ox, oy = self._get_image_offset()
        img_x = (cx - ox) / old_zoom
        img_y = (cy - oy) / old_zoom

        self.zoom_level = nz
        self._draw()
        self._upd_zoom()

        ox2, oy2 = self._get_image_offset()
        new_cx = ox2 + img_x * nz
        new_cy = oy2 + img_y * nz

        target_left = new_cx - event.x
        target_top  = new_cy - event.y

        sr_x1, sr_y1, sr_x2, sr_y2 = self._scroll_bounds
        w = sr_x2 - sr_x1
        h = sr_y2 - sr_y1
        if w > 0:
            frac_x = (target_left - sr_x1) / w
            self.canvas.xview_moveto(max(0.0, min(1.0, frac_x)))
        if h > 0:
            frac_y = (target_top - sr_y1) / h
            self.canvas.yview_moveto(max(0.0, min(1.0, frac_y)))

    def _toggle_grid(self):
        if self.current_image is not None:
            self._draw()

    def _draw_grid(self, ox=0, oy=0):
        if not self.show_grid.get() or self.current_image is None:
            return
        ih, iw = self.current_image.shape[:2]
        dw, dh = int(iw * self.zoom_level), int(ih * self.zoom_level)
        sp = max(20, int(50 * self.zoom_level))
        for x in range(0, dw, sp):
            self.canvas.create_line(ox + x, oy, ox + x, oy + dh, fill='#9ACD32', width=1)
        for y in range(0, dh, sp):
            self.canvas.create_line(ox, oy + y, ox + dw, oy + y, fill='#9ACD32', width=1)

    def _pan_start(self, event):
        self.is_panning = True
        self.canvas.scan_mark(event.x, event.y)
        self.canvas.config(cursor="fleur")

    def _pan_do(self, event):
        if self.is_panning:
            self.canvas.scan_dragto(event.x, event.y, gain=1)

    def _pan_end(self, event):
        self.is_panning = False
        self.canvas.config(cursor="crosshair")

    def _draw_handles(self, ox, oy):
        if self.current_image is None:
            return
        ih, iw = self.current_image.shape[:2]
        dw, dh = iw * self.zoom_level, ih * self.zoom_level
        hs = 8
        right_x = ox + dw
        mid_y   = oy + dh / 2
        mid_x   = ox + dw / 2
        bot_y   = oy + dh
        self.canvas.create_rectangle(
            right_x - hs, mid_y - hs, right_x + hs, mid_y + hs,
            fill='yellow', outline='#333', width=1, tags='h_handle')
        self.canvas.create_rectangle(
            mid_x - hs, bot_y - hs, mid_x + hs, bot_y + hs,
            fill='yellow', outline='#333', width=1, tags='v_handle')

    def _hit_test_point(self, cx, cy, ox, oy):
        thr = self.point_hit_radius
        for i, pt in enumerate(self.points):
            px = ox + pt[0] * self.zoom_level
            py = oy + pt[1] * self.zoom_level
            if abs(cx - px) < thr and abs(cy - py) < thr:
                return i
        return None

    def _update_handles(self, event):
        if self.current_image is None or self.is_stretching:
            return
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        ih, iw = self.current_image.shape[:2]
        ox, oy = self._get_image_offset()
        dw, dh = iw * self.zoom_level, ih * self.zoom_level
        right_x = ox + dw
        mid_y   = oy + dh / 2
        mid_x   = ox + dw / 2
        bot_y   = oy + dh
        thr = 14
        if self.dragging_point_index is not None:
            return
        on_h = abs(cx - right_x) < thr and abs(cy - mid_y) < thr
        on_v = abs(cx - mid_x)   < thr and abs(cy - bot_y) < thr
        if on_h:
            self.canvas.config(cursor="size_we")
        elif on_v:
            self.canvas.config(cursor="size_ns")
        else:
            self.canvas.config(cursor="crosshair")

    def _click(self, event):
        if self.current_image is None or self.is_panning:
            return
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        ih, iw = self.current_image.shape[:2]
        ox, oy = self._get_image_offset()
        dw, dh = iw * self.zoom_level, ih * self.zoom_level
        right_x = ox + dw
        mid_y   = oy + dh / 2
        mid_x   = ox + dw / 2
        bot_y   = oy + dh
        thr = 14
        if abs(cx - right_x) < thr and abs(cy - mid_y) < thr:
            self._stretch_start(event, 'h_handle')
            return
        if abs(cx - mid_x) < thr and abs(cy - bot_y) < thr:
            self._stretch_start(event, 'v_handle')
            return
        if len(self.points) == 4:
            hit = self._hit_test_point(cx, cy, ox, oy)
            if hit is not None:
                self._push_undo("Di chuyển điểm")
                self.dragging_point_index = hit
                if self.offset_points:
                    self.offset_points = []
                    self.offset_count = 0
                    self.offset_btn.config(state='normal')
                return
        if len(self.points) < 4:
            ix = (cx - ox) / self.zoom_level
            iy = (cy - oy) / self.zoom_level
            if 0 <= ix < self.current_image.shape[1] and 0 <= iy < self.current_image.shape[0]:
                self.points.append([ix, iy])
                self._draw()
                if len(self.points) == 4:
                    self.offset_btn.config(state='normal')
                    self.correct_btn.config(state='normal')
                    self.status_label.config(text="Đủ 4 điểm. Bấm Chỉnh sửa méo hoặc Tạo viền offset", bg='lightblue')
                else:
                    self.status_label.config(text="Đã chọn {}/4 điểm".format(len(self.points)), bg='lightyellow')

    def _drag_point(self, event):
        if self.current_image is None or self.dragging_point_index is None:
            return
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        ox, oy = self._get_image_offset()
        ih, iw = self.current_image.shape[:2]
        ix = (cx - ox) / self.zoom_level
        iy = (cy - oy) / self.zoom_level
        margin_x = iw * 0.5
        margin_y = ih * 0.5
        ix = max(-margin_x, min(iw + margin_x, ix))
        iy = max(-margin_y, min(ih + margin_y, iy))
        self.points[self.dragging_point_index] = [ix, iy]
        self._draw()
        self.status_label.config(
            text="Đang di chuyển điểm {}/4".format(self.dragging_point_index + 1),
            bg='lightyellow')

    def _drag(self, event):
        if self.dragging_point_index is not None:
            self._drag_point(event)
        elif self.is_stretching:
            self._stretch_do(event)

    def _release(self, event):
        if self.dragging_point_index is not None:
            self.dragging_point_index = None
            if len(self.points) == 4:
                self.status_label.config(text="Đủ 4 điểm. Bấm Chỉnh sửa méo hoặc Tạo viền offset", bg='lightblue')
        elif self.is_stretching:
            self._stretch_end(event)

    def _stretch_start(self, event, handle):
        self.is_stretching = True
        self.stretch_handle = handle
        self._stretch_pending = False
        src = self.source_image if self.source_image is not None else self.original_image
        self._stretch_base_iw = src.shape[1]
        self._stretch_base_ih = src.shape[0]
        cur_h, cur_w = self.current_image.shape[:2]
        self.stretch_x_factor = cur_w / self._stretch_base_iw
        self.stretch_y_factor = cur_h / self._stretch_base_ih
        ox, oy = self._get_image_offset()
        self._stretch_origin_x = ox
        self._stretch_origin_y = oy
        self.canvas.config(cursor="size_we" if handle == 'h_handle' else "size_ns")

    def _stretch_do(self, event):
        if not self.is_stretching or self.current_image is None:
            return
        if self._stretch_pending:
            return
        self._stretch_pending = True
        ex, ey = event.x, event.y
        self.root.after(16, lambda: self._stretch_render(ex, ey))

    def _stretch_render(self, ex, ey):
        self._stretch_pending = False
        if not self.is_stretching or self.original_image is None:
            return
        cx = self.canvas.canvasx(ex)
        cy = self.canvas.canvasy(ey)
        ox = self._stretch_origin_x
        oy = self._stretch_origin_y
        if self.stretch_handle == 'h_handle':
            new_w_px = cx - ox
            new_w_img = new_w_px / self.zoom_level
            self.stretch_x_factor = max(0.15, min(5.0, new_w_img / self._stretch_base_iw))
        else:
            new_h_px = cy - oy
            new_h_img = new_h_px / self.zoom_level
            self.stretch_y_factor = max(0.15, min(5.0, new_h_img / self._stretch_base_ih))
        self._apply_stretch_preview()

    def _stretch_end(self, event):
        if not self.is_stretching:
            return
        self._apply_stretch_final()
        self.is_stretching = False
        self.stretch_handle = None
        self.canvas.config(cursor="crosshair")

    def _apply_stretch_preview(self):
        if self.source_image is None and self.original_image is None:
            return
        src = self.source_image if self.source_image is not None else self.original_image
        nw = max(1, int(self._stretch_base_iw * self.stretch_x_factor))
        nh = max(1, int(self._stretch_base_ih * self.stretch_y_factor))
        disp_w = max(1, int(nw * self.zoom_level))
        disp_h = max(1, int(nh * self.zoom_level))
        MAX_DISP = 2400
        if disp_w > MAX_DISP or disp_h > MAX_DISP:
            s = MAX_DISP / max(disp_w, disp_h)
            disp_w = max(1, int(disp_w * s))
            disp_h = max(1, int(disp_h * s))
        img_pil = numpy_to_pil(src)
        img_pil = img_pil.resize((disp_w, disp_h), Image.NEAREST)
        self.display_image = ImageTk.PhotoImage(img_pil)
        ox = self._stretch_origin_x
        oy = self._stretch_origin_y
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        sr_w = max(disp_w + 2 * ox, cw)
        sr_h = max(disp_h + 2 * oy, ch)
        self.canvas.delete("all")
        self.canvas.configure(scrollregion=(0, 0, sr_w, sr_h))
        self._scroll_bounds = (0, 0, sr_w, sr_h)
        self.canvas.create_image(ox, oy, anchor='nw', image=self.display_image)
        hs = 8
        right_x = ox + disp_w
        mid_y   = oy + disp_h / 2
        mid_x   = ox + disp_w / 2
        bot_y   = oy + disp_h
        self.canvas.create_rectangle(right_x - hs, mid_y - hs, right_x + hs, mid_y + hs,
                                     fill='yellow', outline='#333', width=1, tags='h_handle')
        self.canvas.create_rectangle(mid_x - hs, bot_y - hs, mid_x + hs, bot_y + hs,
                                     fill='yellow', outline='#333', width=1, tags='v_handle')
        self.status_label.config(
            text="Kích thước: {} x {} px  (ngang {:.1f}%  dọc {:.1f}%)".format(
                nw, nh, self.stretch_x_factor * 100, self.stretch_y_factor * 100),
            bg='lightyellow')

    def _apply_stretch_final(self):
        src = self.source_image if self.source_image is not None else self.original_image
        if src is None:
            return
        self._push_undo("Dãn ảnh")
        nw = max(1, int(self._stretch_base_iw * self.stretch_x_factor))
        nh = max(1, int(self._stretch_base_ih * self.stretch_y_factor))
        stretched = cv2_resize(src, (nw, nh))
        for pt in self.points + self.offset_points:
            pt[0] = pt[0] / (self.current_image.shape[1] / nw) if self.current_image is not None else pt[0]
            pt[1] = pt[1] / (self.current_image.shape[0] / nh) if self.current_image is not None else pt[1]
        self.current_image  = stretched
        self.original_image = stretched.copy()
        self.base_image     = stretched.copy()
        self.rotated_cache  = {}
        self.rotation_angle = 0.0
        self.rotation_var.set(0.0)
        self.rotation_angle_label.config(text="0.0")
        self.stretch_x_factor = 1.0
        self.stretch_y_factor = 1.0
        self.root.after(30, self.fit_to_canvas)

    def _draw_points(self, ox=0, oy=0):
        if self.current_image is None:
            return
        r = max(3, int(5 * self.zoom_level))
        fs = max(8, int(12 * self.zoom_level))
        lw = max(1, int(2 * self.zoom_level))
        for i, pt in enumerate(self.points):
            cx, cy = ox + pt[0] * self.zoom_level, oy + pt[1] * self.zoom_level
            self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill='red', outline='black', width=2)
            self.canvas.create_text(cx + r + 5, cy - r - 5, text=str(i + 1), fill='red', font=('Arial', fs, 'bold'))
        for i, pt in enumerate(self.offset_points):
            cx, cy = ox + pt[0] * self.zoom_level, oy + pt[1] * self.zoom_level
            self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill='green', outline='black', width=2)
            self.canvas.create_text(cx + r + 5, cy - r - 5, text="O{}".format(i + 1), fill='green', font=('Arial', fs, 'bold'))
        for pts, color in [(self.points, 'blue'), (self.offset_points, 'green')]:
            n = len(pts)
            if n >= 2:
                for i in range(n):
                    if n == 4 or i < n - 1:
                        p1, p2 = pts[i], pts[(i + 1) % n]
                        self.canvas.create_line(
                            ox + p1[0] * self.zoom_level, oy + p1[1] * self.zoom_level,
                            ox + p2[0] * self.zoom_level, oy + p2[1] * self.zoom_level,
                            fill=color, width=lw)

    # ── Tạo viền offset → PREMIUM ───────────────────────────
    def create_offset_border(self):
        show_premium_popup(self.root, self.app, "Tạo viền Offset")

    def correct_distortion(self):
        if len(self.points) != 4:
            messagebox.showwarning("Cảnh báo", "Cần chọn đủ 4 điểm!", parent=self.root)
            return
        self._push_undo("Chỉnh méo")
        try:
            use_pts = self.offset_points if self.offset_points else self.points
            ordered = order_points(use_pts)
            tl, tr, br, bl = ordered

            w = int(max(
                math.sqrt((tr[0]-tl[0])**2 + (tr[1]-tl[1])**2),
                math.sqrt((br[0]-bl[0])**2 + (br[1]-bl[1])**2)
            ))
            h = int(max(
                math.sqrt((bl[0]-tl[0])**2 + (bl[1]-tl[1])**2),
                math.sqrt((br[0]-tr[0])**2 + (br[1]-tr[1])**2)
            ))

            src4 = [tl, tr, br, bl]
            dst4 = [[0, 0], [w, 0], [w, h], [0, h]]

            self.current_image = cv2_perspective_transform(
                self.current_image, src4, dst4, w, h)
            self.original_image = self.current_image.copy()
            self.source_image   = self.current_image.copy()
            self.base_image     = self.current_image.copy()
            self.points = []
            self.offset_points = []
            self.offset_count = 0
            self.rotated_cache = {}
            self.rotation_angle = 0.0
            self.rotation_var.set(0.0)
            self.rotation_angle_label.config(text="0.0")
            self.root.after(100, self.fit_to_canvas)
            self.correct_btn.config(state='normal')
            self.offset_btn.config(state='normal')
            self.save_btn.config(state='normal')
            self.status_label.config(text="Chỉnh méo thành công! Vẽ 4 điểm mới để chỉnh tiếp.", bg='lightgreen')
        except Exception as e:
            messagebox.showerror("Lỗi", "Không thể chỉnh sửa méo: {}".format(e), parent=self.root)

    def reset_image(self):
        if self.original_image is not None:
            self.current_image = self.original_image.copy()
            self._reset_state()
            self.rotation_var.set(0.0)
            self.rotation_angle_label.config(text="0.0")
            self.root.after(100, self.fit_to_canvas)
            self.save_btn.config(state='normal')
            self.restore_btn.config(state='normal')
            self.sharpen_btn.config(state='normal', bg='white', fg='black')
            self.status_label.config(text="Đã reset. Vẽ 4 điểm góc hình bình hành", bg='lightgreen')

    def save_image(self):
        if self.current_image is None:
            return
        fp = ask_save_filename(
            self.root,
            title="Lưu ảnh", defaultextension=".png",
            filetypes=[
                ("PNG - chất lượng cao", "*.png"),
                ("JPEG", "*.jpg *.jpeg"),
                ("WebP", "*.webp"),
                ("Bitmap", "*.bmp"),
                ("TIFF", "*.tiff *.tif"),
                ("Tất cả file", "*.*"),
            ])
        if fp:
            try:
                if not os.path.splitext(fp)[1]:
                    fp += ".png"
                ok = cv2_imwrite(fp, self.current_image)
                if ok:
                    messagebox.showinfo("Thành công", "Đã lưu ảnh thành công!", parent=self.root)
                else:
                    messagebox.showerror("Lỗi", "Không thể lưu ảnh!", parent=self.root)
            except Exception as e:
                messagebox.showerror("Lỗi", "Không thể lưu ảnh: {}".format(e), parent=self.root)


# ─────────────────────────────────────────────────────────────
# TAB 3  –  Thông tin
# ─────────────────────────────────────────────────────────────
class InfoTab:
    def __init__(self, parent_frame, root):
        self.root = root
        self.frame = parent_frame
        self._setup_ui()

    def _setup_ui(self):
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)

        wrapper = tk.Frame(self.frame, bg='white')
        wrapper.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(wrapper,
                 text="Chụp ảnh mẫu & Chỉnh méo ảnh",
                 font=('Arial', 18, 'bold'), bg='white', fg='#2c3e50').pack(pady=(0, 4))

        tk.Label(wrapper,
                 text="Phát triển bởi  Lập Phạm  -  0357 519 915",
                 font=('Arial', 10), bg='white', fg='#7f8c8d').pack(pady=(0, 20))

        # Card bản miễn phí
        card = tk.Frame(wrapper, bg='#eafaf1', relief='solid', bd=1)
        card.pack(fill='x', ipadx=20, ipady=15, pady=(0, 10))

        tk.Label(card, text="Bản Miễn Phí",
                 font=('Arial', 14, 'bold'), bg='#eafaf1', fg='#27ae60').pack(pady=(12, 4))

        msg = (
            "Phần mềm này được phép sử dụng MIỄN PHÍ\n"
            "cho cả Cá nhân lẫn Tổ chức / Doanh nghiệp.\n\n"
            "Một số tính năng nâng cao được giới hạn\n"
            "trong Bản Cao Cấp (xem bên dưới)."
        )
        tk.Label(card, text=msg, font=('Arial', 11), bg='#eafaf1',
                 fg='#2c3e50', justify='center').pack(padx=20, pady=(0, 12))

        # Card bản cao cấp
        card_premium = tk.Frame(wrapper, bg='#fff8e1', relief='solid', bd=1)
        card_premium.pack(fill='x', ipadx=20, ipady=15, pady=(0, 10))

        tk.Label(card_premium, text="  Bản Cao Cấp  –  79.000 VNĐ  ",
                 font=('Arial', 13, 'bold'), bg='#fff8e1', fg='#e67e22').pack(pady=(12, 4))

        msg_premium = (
            "Mua một lần – Dùng vĩnh viễn\n\n"
            "✔  Nhập góc xoay tùy ý (click vào ô số góc)\n"
            "✔  Copy ảnh vào Clipboard chất lượng cao\n"
            "✔  Tạo viền Offset tự động"
        )
        tk.Label(card_premium, text=msg_premium, font=('Arial', 10), bg='#fff8e1',
                 fg='#2c3e50', justify='left').pack(padx=30, pady=(0, 12))

        # Card liên hệ
        card2 = tk.Frame(wrapper, bg='#eaf4fb', relief='solid', bd=1)
        card2.pack(fill='x', ipadx=20, ipady=15, pady=(0, 16))

        tk.Label(card2, text="Liên hệ mua Bản Cao Cấp / Hỗ trợ",
                 font=('Arial', 13, 'bold'), bg='#eaf4fb', fg='#2980b9').pack(pady=(12, 4))

        cf = tk.Frame(card2, bg='#eaf4fb')
        cf.pack(pady=(4, 12))

        tk.Label(cf, text="Lập Phạm  –  ĐT / Zalo: 0357 519 915",
                 font=('Arial', 11, 'bold'), bg='#eaf4fb', fg='#2c3e50').pack()

        fb_label = tk.Label(cf, text="Facebook: fb.com/daiklap",
                            font=('Arial', 11, 'bold'), bg='#eaf4fb', fg='#2980b9',
                            cursor='hand2')
        fb_label.pack(pady=2)
        fb_label.bind('<Button-1>', lambda e: webbrowser.open('https://fb.com/daiklap'))

        tk.Label(wrapper,
                 text="(c) 2025 Lập Phạm. Phần mềm được phân phối tự do cho mục đích phi thương mại.",
                 font=('Arial', 8), bg='white', fg='#95a5a6').pack(pady=(4, 0))


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Chụp ảnh mẫu & Chỉnh méo ảnh - Lập Phạm 0357519915")
        self.root.state('zoomed')
        try:
            self.root.attributes('-zoomed', True)
        except Exception:
            pass

        self._icon_ico_path = None
        self._icon_png_img = None
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            ico_path = os.path.join(base_dir, "icon.ico")
            png_path = os.path.join(base_dir, "icon.png")
            if os.path.exists(ico_path):
                self.root.iconbitmap(ico_path)
                self._icon_ico_path = ico_path
            elif os.path.exists(png_path):
                img = tk.PhotoImage(file=png_path)
                self.root.iconphoto(True, img)
                self._icon_png_img = img
        except Exception:
            pass

        nb = ttk.Notebook(root)
        nb.pack(fill='both', expand=True, padx=5, pady=5)

        tab1 = ttk.Frame(nb, padding=5)
        tab2 = ttk.Frame(nb, padding=5)
        tab3 = ttk.Frame(nb, padding=5)
        nb.add(tab1, text="  Chụp ảnh  ")
        nb.add(tab2, text="  Chỉnh méo ảnh  ")
        nb.add(tab3, text="  Thông tin  ")

        self.ss_tab   = ScreenshotTab(tab1, root, self)
        self.dt_tab   = DistortionTab(tab2, root, self)
        self.info_tab = InfoTab(tab3, root)

        nb.select(1)

        def _key(event):
            if nb.index(nb.select()) == 1:
                if event.keysym == 'Left':
                    self.dt_tab.rotate_by_key(-0.1)
                elif event.keysym == 'Right':
                    self.dt_tab.rotate_by_key(0.1)
        root.bind('<Left>', _key)
        root.bind('<Right>', _key)

        nb.bind("<<NotebookTabChanged>>",
                lambda e: self.dt_tab.activate() if nb.index(nb.select()) == 1 else None)

    def on_closing(self):
        self.ss_tab.save_settings()
        for proc in self.ss_tab.file_processes.values():
            try:
                proc.terminate()
            except Exception:
                pass
        self.root.destroy()


def main():
    root = tk.Tk()
    app = App(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
