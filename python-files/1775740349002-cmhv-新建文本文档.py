# -*- coding: utf-8 -*-
"""
批量图片水印工具 - 高级命名脚本版
"""

import os
import re
import threading
import tempfile
from datetime import datetime
from tkinter import *
from tkinter import ttk, filedialog, messagebox

try:
    from PIL import Image
    try:
        RESAMPLE_FILTER = Image.Resampling.LANCZOS
    except AttributeError:
        RESAMPLE_FILTER = Image.LANCZOS
except ImportError:
    messagebox.showerror("缺少依赖", "请先安装 Pillow 库：\npip install Pillow")
    raise

# ================== 核心处理函数 ==================
def get_image_files(folder):
    SUPPORTED_EXT = ('.jpg', '.jpeg', '.png', '.tif', '.tiff', '.bmp', '.psd', '.webp')
    files = []
    if not os.path.exists(folder):
        return files
    for item in os.listdir(folder):
        full_path = os.path.join(folder, item)
        if os.path.isfile(full_path):
            ext = os.path.splitext(item)[1].lower()
            if ext in SUPPORTED_EXT:
                files.append(full_path)
    return files

def get_sub_folders(parent_folder):
    if not os.path.exists(parent_folder):
        return []
    return [os.path.join(parent_folder, d) for d in os.listdir(parent_folder)
            if os.path.isdir(os.path.join(parent_folder, d))]

def generate_output_filename(original_path, naming_config, current_index, log_func=None):
    base_name = os.path.splitext(os.path.basename(original_path))[0]
    folder_path = os.path.dirname(original_path)
    folder_name = os.path.basename(folder_path)
    ext = os.path.splitext(original_path)[1].lower()
    
    # 简单模式
    if not naming_config.get('advanced_enabled', False):
        text = naming_config.get('text_content', '') if naming_config.get('text_enabled') else ''
        number = str(naming_config.get('start_number', 1) + current_index - 1) if naming_config.get('number_enabled') else ''
        
        if naming_config.get('script_enabled'):
            template = naming_config.get('script_template', '{basename}')
            result = template
            result = result.replace('{basename}', base_name)
            result = result.replace('{text}', text)
            result = result.replace('{number}', number)
            return result
        else:
            if naming_config.get('text_enabled'):
                pos = naming_config.get('text_position', 'start')
                if pos == 'start':
                    return text + number + base_name
                elif pos == 'after_basename':
                    return base_name + text + number
                else:
                    return base_name + number + text
            else:
                return base_name + number
    else:
        # 高级模式
        advanced_script = naming_config.get('advanced_script', 'result = basename')
        local_vars = {
            'basename': base_name,
            'folder': folder_path,
            'foldername': folder_name,
            'ext': ext,
            'idx': current_index,
            'datetime': datetime,
            're': re,
            'os': os,
        }
        try:
            exec(advanced_script, {}, local_vars)
            result = local_vars.get('result', base_name)
            return str(result)
        except Exception as e:
            error_msg = f"高级命名脚本错误: {e}"
            if log_func:
                log_func(error_msg)
            return base_name

def collect_all_image_tasks(src_root, dest_root, skip_existing, naming_config, output_format, log_func):
    tasks = []
    index_counter = 1
    
    def make_dst_path(src_path, idx):
        new_basename = generate_output_filename(src_path, naming_config, idx, log_func)
        src_ext = os.path.splitext(src_path)[1].lower()
        if output_format == 'keep':
            ext = src_ext
        elif output_format == 'jpg':
            ext = '.jpg'
        elif output_format == 'png':
            ext = '.png'
        elif output_format == 'webp':
            ext = '.webp'
        else:
            ext = '.jpg'
        if not ext.startswith('.'):
            ext = '.' + ext
        return new_basename + ext
    
    root_images = get_image_files(src_root)
    for img in root_images:
        dst = os.path.join(dest_root, make_dst_path(img, index_counter))
        tasks.append((img, dst))
        index_counter += 1
    
    sub_dirs = get_sub_folders(src_root)
    for sub in sub_dirs:
        folder_name = os.path.basename(sub)
        dst_folder = os.path.join(dest_root, folder_name)
        images = get_image_files(sub)
        for img in images:
            dst = os.path.join(dst_folder, make_dst_path(img, index_counter))
            tasks.append((img, dst))
            index_counter += 1
    
    return tasks

def find_optimal_quality(image, target_bytes, min_q, max_q, step):
    low, high = min_q, max_q
    best_q = min_q
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
        tmp_path = tmp.name
    try:
        while low <= high:
            mid = (low + high) // 2
            image.save(tmp_path, "JPEG", quality=mid, optimize=True)
            size = os.path.getsize(tmp_path)
            if size <= target_bytes:
                best_q = mid
                low = mid + 1
            else:
                high = mid - 1
            if high - low < step:
                break
        for q in [best_q, best_q + step, best_q - step]:
            if q < min_q or q > max_q:
                continue
            image.save(tmp_path, "JPEG", quality=q, optimize=True)
            if os.path.getsize(tmp_path) <= target_bytes and q > best_q:
                best_q = q
        return best_q
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def save_image_with_format(image, dst_path, output_format, config, log_callback):
    ext = os.path.splitext(dst_path)[1].lower()
    if output_format == 'jpg' or ext == '.jpg':
        out_rgb = image.convert("RGB")
        quality = config.get('jpeg_quality', 85)
        if config.get('auto_quality', False):
            target_bytes = config.get('target_size_kb', 1500) * 1024
            min_q = config.get('min_quality', 30)
            max_q = config.get('max_quality', 95)
            step = config.get('quality_step', 5)
            quality = find_optimal_quality(out_rgb, target_bytes, min_q, max_q, step)
        out_rgb.save(dst_path, "JPEG", quality=quality, optimize=True)
    elif output_format == 'png' or ext == '.png':
        image.save(dst_path, "PNG", compress_level=9)
    elif output_format == 'webp' or ext == '.webp':
        quality = config.get('jpeg_quality', 85)
        image.save(dst_path, "WEBP", quality=quality)
    elif output_format == 'keep':
        original_ext = ext
        if original_ext in ('.jpg', '.jpeg'):
            out_rgb = image.convert("RGB")
            quality = config.get('jpeg_quality', 85)
            if config.get('auto_quality', False):
                target_bytes = config.get('target_size_kb', 1500) * 1024
                min_q = config.get('min_quality', 30)
                max_q = config.get('max_quality', 95)
                step = config.get('quality_step', 5)
                quality = find_optimal_quality(out_rgb, target_bytes, min_q, max_q, step)
            out_rgb.save(dst_path, "JPEG", quality=quality, optimize=True)
        elif original_ext == '.png':
            image.save(dst_path, "PNG", compress_level=9)
        elif original_ext == '.webp':
            quality = config.get('jpeg_quality', 85)
            image.save(dst_path, "WEBP", quality=quality)
        else:
            out_rgb = image.convert("RGB")
            out_rgb.save(dst_path, "JPEG", quality=85)
    else:
        out_rgb = image.convert("RGB")
        out_rgb.save(dst_path, "JPEG", quality=85)

def add_single_watermark(src_path, dst_path, watermark_img, config, log_callback=None):
    if log_callback is None:
        log_callback = print
    if config.get('skip_existing', True) and os.path.exists(dst_path):
        log_callback(f"跳过已存在: {os.path.basename(src_path)} -> {os.path.basename(dst_path)}")
        return True, True, 0, None
    try:
        base = Image.open(src_path).convert("RGBA")
        base_width, base_height = base.size
        h_align = config.get('h_align', 'right')
        v_align = config.get('v_align', 'bottom')
        h_offset = config.get('h_offset', 5)
        v_offset = config.get('v_offset', 5)
        width_ratio = config.get('watermark_width_ratio', 0.6)
        opacity = config.get('watermark_opacity', 0.7)

        target_w = int(base_width * width_ratio)
        target_h = int(watermark_img.height * (target_w / watermark_img.width))
        if target_h > base_height:
            target_h = base_height - 2
            target_w = int(watermark_img.width * (target_h / watermark_img.height))
            if target_w > base_width:
                target_w = base_width - 2
                target_h = int(watermark_img.height * (target_w / watermark_img.width))

        watermark_resized = watermark_img.resize((target_w, target_h), RESAMPLE_FILTER)
        if opacity < 1.0:
            r, g, b, a = watermark_resized.split()
            a = a.point(lambda p: int(p * opacity))
            watermark_resized = Image.merge("RGBA", (r, g, b, a))

        if h_align == 'left':
            pos_x = h_offset
        elif h_align == 'center':
            pos_x = (base_width - target_w) // 2 + h_offset
        else:
            pos_x = base_width - target_w - h_offset

        if v_align == 'top':
            pos_y = v_offset
        elif v_align == 'center':
            pos_y = (base_height - target_h) // 2 + v_offset
        else:
            pos_y = base_height - target_h - v_offset

        pos_x = max(0, min(pos_x, base_width - target_w))
        pos_y = max(0, min(pos_y, base_height - target_h))

        watermarked = Image.new("RGBA", base.size, (0, 0, 0, 0))
        watermarked.paste(watermark_resized, (pos_x, pos_y), watermark_resized)
        out = Image.alpha_composite(base, watermarked)

        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
        output_format = config.get('output_format', 'keep')
        save_image_with_format(out, dst_path, output_format, config, log_callback)

        size_kb = os.path.getsize(dst_path) / 1024
        log_callback(f"已处理: {os.path.basename(src_path)} -> {os.path.basename(dst_path)} ({size_kb:.1f}KB)")
        return True, False, size_kb, None
    except Exception as e:
        error_msg = f"处理失败 {os.path.basename(src_path)}: {e}"
        log_callback(error_msg)
        return False, False, 0, error_msg

# ================== 图形界面 ==================
class WatermarkApp:
    def __init__(self, root):
        self.root = root
        self.root.title("批量图片水印工具")
        self.root.geometry("900x700")
        self.stop_flag = False
        self.processing_thread = None
        self.create_widgets()

    def create_widgets(self):
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=0)
        self.root.grid_columnconfigure(0, weight=1)

        top_frame = ttk.Frame(self.root)
        top_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10,0))
        top_frame.grid_rowconfigure(0, weight=3)
        top_frame.grid_rowconfigure(1, weight=2)
        top_frame.grid_columnconfigure(0, weight=1)

        notebook = ttk.Notebook(top_frame)
        notebook.grid(row=0, column=0, sticky="nsew", pady=(0,5))
        basic_tab = ttk.Frame(notebook)
        notebook.add(basic_tab, text="基本设置")
        self.create_basic_tab(basic_tab)
        image_tab = ttk.Frame(notebook)
        notebook.add(image_tab, text="图片设置")
        self.create_image_settings_tab(image_tab)

        log_frame = ttk.LabelFrame(top_frame, text="处理日志")
        log_frame.grid(row=1, column=0, sticky="nsew")
        self.log_text = Text(log_frame, wrap=WORD, height=6)
        scrollbar = ttk.Scrollbar(log_frame, orient=VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        btn_frame = ttk.Frame(self.root)
        btn_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        btn_frame.grid_columnconfigure(2, weight=1)

        big_btn_font = ('微软雅黑', 11, 'normal')
        self.start_btn = Button(btn_frame, text="开始处理", command=self.start_processing,
                                font=big_btn_font, padx=20, pady=8, relief=RAISED, bd=2)
        self.start_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.stop_btn = Button(btn_frame, text="停止", command=self.stop_processing,
                               font=big_btn_font, padx=20, pady=8, relief=RAISED, bd=2, state=DISABLED)
        self.stop_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        clear_btn = Button(btn_frame, text="清空日志", command=self.clear_log,
                           font=big_btn_font, padx=20, pady=8, relief=RAISED, bd=2)
        clear_btn.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

    def create_basic_tab(self, parent):
        container = ttk.Frame(parent)
        container.pack(fill=BOTH, expand=True, padx=5, pady=5)
        container.columnconfigure(0, weight=0)
        container.columnconfigure(1, weight=1)
        container.columnconfigure(2, weight=0)
        container.columnconfigure(3, weight=0)
        
        row = 0
        Label(container, text="源根目录:").grid(row=row, column=0, sticky=W, padx=5, pady=5)
        self.src_path = StringVar()
        Entry(container, textvariable=self.src_path).grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        Button(container, text="浏览...", command=self.browse_src).grid(row=row, column=2, padx=5, pady=5)
        row += 1
        
        Label(container, text="输出根目录:").grid(row=row, column=0, sticky=W, padx=5, pady=5)
        self.dst_path = StringVar()
        Entry(container, textvariable=self.dst_path).grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        Button(container, text="浏览...", command=self.browse_dst).grid(row=row, column=2, padx=5, pady=5)
        row += 1
        
        Label(container, text="水印图片:").grid(row=row, column=0, sticky=W, padx=5, pady=5)
        self.watermark_path = StringVar()
        Entry(container, textvariable=self.watermark_path).grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        Button(container, text="浏览...", command=self.browse_watermark).grid(row=row, column=2, padx=5, pady=5)
        row += 1
        
        ttk.Separator(container, orient=HORIZONTAL).grid(row=row, column=0, columnspan=4, sticky=EW, pady=10)
        row += 1
        
        Label(container, text="水印位置:", font=('微软雅黑', 9, 'bold')).grid(row=row, column=0, sticky=W, padx=5, pady=5)
        row += 1
        
        Label(container, text="水平对齐:").grid(row=row, column=0, sticky=W, padx=5, pady=5)
        self.h_align = StringVar(value="right")
        h_frame = ttk.Frame(container)
        h_frame.grid(row=row, column=1, sticky=W, padx=5, pady=5)
        Radiobutton(h_frame, text="左", variable=self.h_align, value="left").pack(side=LEFT)
        Radiobutton(h_frame, text="中", variable=self.h_align, value="center").pack(side=LEFT)
        Radiobutton(h_frame, text="右", variable=self.h_align, value="right").pack(side=LEFT)
        Label(container, text="水平偏移:").grid(row=row, column=2, sticky=E, padx=5, pady=5)
        self.h_offset = IntVar(value=5)
        Spinbox(container, from_=-500, to=500, textvariable=self.h_offset).grid(row=row, column=3, sticky=W, padx=5, pady=5)
        row += 1
        
        Label(container, text="垂直对齐:").grid(row=row, column=0, sticky=W, padx=5, pady=5)
        self.v_align = StringVar(value="bottom")
        v_frame = ttk.Frame(container)
        v_frame.grid(row=row, column=1, sticky=W, padx=5, pady=5)
        Radiobutton(v_frame, text="上", variable=self.v_align, value="top").pack(side=LEFT)
        Radiobutton(v_frame, text="中", variable=self.v_align, value="center").pack(side=LEFT)
        Radiobutton(v_frame, text="下", variable=self.v_align, value="bottom").pack(side=LEFT)
        Label(container, text="垂直偏移:").grid(row=row, column=2, sticky=E, padx=5, pady=5)
        self.v_offset = IntVar(value=5)
        Spinbox(container, from_=-500, to=500, textvariable=self.v_offset).grid(row=row, column=3, sticky=W, padx=5, pady=5)
        row += 1
        
        ttk.Separator(container, orient=HORIZONTAL).grid(row=row, column=0, columnspan=4, sticky=EW, pady=10)
        row += 1
        
        Label(container, text="水印宽度比例(0~1):").grid(row=row, column=0, sticky=W, padx=5, pady=5)
        self.width_ratio = DoubleVar(value=0.6)
        Spinbox(container, from_=0.1, to=1.0, increment=0.05, textvariable=self.width_ratio).grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        
        Label(container, text="不透明度(0~1):").grid(row=row, column=0, sticky=W, padx=5, pady=5)
        self.opacity = DoubleVar(value=0.7)
        Spinbox(container, from_=0.1, to=1.0, increment=0.05, textvariable=self.opacity).grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        
        self.skip_existing = BooleanVar(value=True)
        Checkbutton(container, text="开启断点续传（跳过已存在文件）", variable=self.skip_existing).grid(row=row, column=0, columnspan=2, sticky=W, padx=5, pady=5)

    def create_image_settings_tab(self, parent):
        canvas = Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient=VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        def _configure_interior(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        def _configure_canvas(event):
            canvas.itemconfig(window_id, width=event.width)
        
        scrollable_frame.bind("<Configure>", _configure_interior)
        canvas.bind("<Configure>", _configure_canvas)
        window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        scrollable_frame.columnconfigure(0, weight=0)
        scrollable_frame.columnconfigure(1, weight=1)
        scrollable_frame.columnconfigure(2, weight=0)
        
        row = 0
        Label(scrollable_frame, text="输出格式:").grid(row=row, column=0, sticky=W, padx=5, pady=5)
        self.output_format = StringVar(value="keep")
        format_combo = ttk.Combobox(scrollable_frame, textvariable=self.output_format, values=["keep", "jpg", "png", "webp"])
        format_combo.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        Label(scrollable_frame, text="(keep=保持原格式)").grid(row=row, column=2, sticky=W, padx=5, pady=5)
        row += 1
        
        ttk.Separator(scrollable_frame, orient=HORIZONTAL).grid(row=row, column=0, columnspan=3, sticky=EW, pady=10)
        row += 1
        
        self.auto_quality = BooleanVar(value=False)
        cb = Checkbutton(scrollable_frame, text="启用自动JPEG/WebP质量调整（根据目标文件大小）", variable=self.auto_quality, command=self.toggle_auto_quality)
        cb.grid(row=row, column=0, columnspan=3, sticky=W, padx=5, pady=5)
        row += 1
        
        Label(scrollable_frame, text="固定质量(1-100):").grid(row=row, column=0, sticky=W, padx=5, pady=5)
        self.jpeg_quality = IntVar(value=85)
        self.quality_spin = Spinbox(scrollable_frame, from_=1, to=100, textvariable=self.jpeg_quality)
        self.quality_spin.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        
        Label(scrollable_frame, text="目标文件大小(KB):").grid(row=row, column=0, sticky=W, padx=5, pady=5)
        self.target_size = IntVar(value=1500)
        Entry(scrollable_frame, textvariable=self.target_size).grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        
        Label(scrollable_frame, text="自动调整步长:").grid(row=row, column=0, sticky=W, padx=5, pady=5)
        self.quality_step = IntVar(value=5)
        Spinbox(scrollable_frame, from_=1, to=20, textvariable=self.quality_step).grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        
        Label(scrollable_frame, text="最低允许质量:").grid(row=row, column=0, sticky=W, padx=5, pady=5)
        self.min_quality = IntVar(value=30)
        Spinbox(scrollable_frame, from_=1, to=100, textvariable=self.min_quality).grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        
        Label(scrollable_frame, text="最高允许质量:").grid(row=row, column=0, sticky=W, padx=5, pady=5)
        self.max_quality = IntVar(value=95)
        Spinbox(scrollable_frame, from_=1, to=100, textvariable=self.max_quality).grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        
        ttk.Separator(scrollable_frame, orient=HORIZONTAL).grid(row=row, column=0, columnspan=3, sticky=EW, pady=10)
        row += 1
        
        naming_frame = ttk.LabelFrame(scrollable_frame, text="输出文件名自定义")
        naming_frame.grid(row=row, column=0, columnspan=3, sticky=EW, padx=5, pady=5)
        naming_frame.columnconfigure(0, weight=0)
        naming_frame.columnconfigure(1, weight=1)
        row2 = 0
        
        # 简单模式控件
        self.use_text = BooleanVar(value=False)
        text_cb = Checkbutton(naming_frame, text="添加文字", variable=self.use_text, command=self.toggle_text_frame)
        text_cb.grid(row=row2, column=0, sticky=W, padx=5, pady=5)
        self.use_number = BooleanVar(value=False)
        number_cb = Checkbutton(naming_frame, text="添加编号", variable=self.use_number, command=self.toggle_number_frame)
        number_cb.grid(row=row2, column=1, sticky=W, padx=5, pady=5)
        row2 += 1
        
        self.text_detail_frame = ttk.Frame(naming_frame)
        self.text_detail_frame.grid(row=row2, column=0, columnspan=2, sticky=EW, padx=20, pady=2)
        self.text_detail_frame.grid_remove()
        Label(self.text_detail_frame, text="位置:").pack(side=LEFT, padx=5)
        self.text_pos = StringVar(value="start")
        Radiobutton(self.text_detail_frame, text="开头", variable=self.text_pos, value="start").pack(side=LEFT)
        Radiobutton(self.text_detail_frame, text="原文件名结尾", variable=self.text_pos, value="after_basename").pack(side=LEFT)
        Radiobutton(self.text_detail_frame, text="新名字结尾", variable=self.text_pos, value="end").pack(side=LEFT)
        Label(self.text_detail_frame, text="文字内容:").pack(side=LEFT, padx=5)
        self.custom_text = StringVar(value="watermark")
        Entry(self.text_detail_frame, textvariable=self.custom_text, width=15).pack(side=LEFT, padx=5)
        row2 += 1
        
        self.number_detail_frame = ttk.Frame(naming_frame)
        self.number_detail_frame.grid(row=row2, column=0, columnspan=2, sticky=EW, padx=20, pady=2)
        self.number_detail_frame.grid_remove()
        Label(self.number_detail_frame, text="起始编号:").pack(side=LEFT, padx=5)
        self.start_number = IntVar(value=1)
        Spinbox(self.number_detail_frame, from_=1, to=9999, textvariable=self.start_number, width=8).pack(side=LEFT, padx=5)
        row2 += 1
        
        self.use_script = BooleanVar(value=False)
        script_cb = Checkbutton(naming_frame, text="使用模板", variable=self.use_script, command=self.toggle_script_frame)
        script_cb.grid(row=row2, column=0, sticky=W, padx=5, pady=5)
        row2 += 1
        
        self.script_detail_frame = ttk.Frame(naming_frame)
        self.script_detail_frame.grid(row=row2, column=0, columnspan=2, sticky=EW, padx=20, pady=5)
        self.script_detail_frame.grid_remove()
        self.script_detail_frame.columnconfigure(0, weight=1)
        self.script_template_text = Text(self.script_detail_frame, height=5, wrap=WORD)
        self.script_template_text.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.script_template_text.insert(END, "{basename}_{text}_{number}")
        row2 += 1
        
        # 高级模式控件
        self.use_advanced = BooleanVar(value=False)
        adv_cb = Checkbutton(naming_frame, text="使用高级脚本", variable=self.use_advanced, command=self.toggle_advanced_frame)
        adv_cb.grid(row=row2, column=0, sticky=W, padx=5, pady=5)
        row2 += 1
        
        self.advanced_detail_frame = ttk.Frame(naming_frame)
        self.advanced_detail_frame.grid(row=row2, column=0, columnspan=2, sticky=EW, padx=20, pady=5)
        self.advanced_detail_frame.grid_remove()
        self.advanced_detail_frame.columnconfigure(0, weight=1)
        Label(self.advanced_detail_frame, text="高级脚本（可用变量: basename, foldername, folder, idx, datetime, re, os）\n示例: result = f\"OP{re.findall(r'\\d+', foldername)[0]}{idx:03d}\"").grid(row=0, column=0, sticky=W, padx=5, pady=2)
        self.advanced_script_text = Text(self.advanced_detail_frame, height=6, wrap=WORD)
        self.advanced_script_text.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        self.advanced_script_text.insert(END, "import re\nresult = basename")
        row2 += 1
        
        tip_label = Label(naming_frame, text="提示：简单模式与高级模式互斥，高级模式优先级更高", fg="gray")
        tip_label.grid(row=row2, column=0, columnspan=2, sticky=W, padx=5, pady=5)

    def toggle_text_frame(self):
        if self.use_text.get():
            self.text_detail_frame.grid()
        else:
            self.text_detail_frame.grid_remove()

    def toggle_number_frame(self):
        if self.use_number.get():
            self.number_detail_frame.grid()
        else:
            self.number_detail_frame.grid_remove()

    def toggle_script_frame(self):
        if self.use_script.get():
            self.script_detail_frame.grid()
        else:
            self.script_detail_frame.grid_remove()

    def toggle_advanced_frame(self):
        if self.use_advanced.get():
            self.advanced_detail_frame.grid()
            # 如果高级模式启用，自动禁用简单模式的相关选项
            self.use_script.set(False)
            self.toggle_script_frame()
            self.use_text.set(False)
            self.toggle_text_frame()
            self.use_number.set(False)
            self.toggle_number_frame()
        else:
            self.advanced_detail_frame.grid_remove()

    def toggle_auto_quality(self):
        if self.auto_quality.get():
            self.quality_spin.config(state=DISABLED)
        else:
            self.quality_spin.config(state=NORMAL)

    def import_script_from_file(self):
        file_path = filedialog.askopenfilename(
            title="选择脚本模板文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                if content:
                    self.script_template_text.delete(1.0, END)
                    self.script_template_text.insert(END, content)
                    self.log(f"已从文件导入脚本模板：{os.path.basename(file_path)}")
                else:
                    messagebox.showwarning("警告", "文件内容为空")
            except Exception as e:
                messagebox.showerror("错误", f"读取文件失败：{e}")

    def browse_src(self):
        path = filedialog.askdirectory(title="选择源根目录")
        if path:
            self.src_path.set(path)

    def browse_dst(self):
        path = filedialog.askdirectory(title="选择输出根目录")
        if path:
            self.dst_path.set(path)

    def browse_watermark(self):
        path = filedialog.askopenfilename(title="选择水印图片", filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.tif *.webp")])
        if path:
            self.watermark_path.set(path)

    def clear_log(self):
        self.log_text.delete(1.0, END)

    def log(self, message):
        def _append():
            self.log_text.insert(END, message + "\n")
            self.log_text.see(END)
        self.root.after(0, _append)

    def stop_processing(self):
        self.stop_flag = True
        self.log("用户请求停止，将在当前图片处理完成后终止...")

    def start_processing(self):
        src = self.src_path.get().strip()
        dst = self.dst_path.get().strip()
        watermark_file = self.watermark_path.get().strip()
        if not src or not os.path.exists(src):
            messagebox.showerror("错误", "请选择有效的源根目录")
            return
        if not dst:
            messagebox.showerror("错误", "请选择输出根目录")
            return
        if not watermark_file or not os.path.exists(watermark_file):
            messagebox.showerror("错误", "请选择有效的水印图片文件")
            return
        try:
            watermark_img = Image.open(watermark_file).convert("RGBA")
        except Exception as e:
            messagebox.showerror("错误", f"无法打开水印文件：{e}")
            return

        # 构建命名配置
        advanced_enabled = self.use_advanced.get()
        if advanced_enabled:
            advanced_script = self.advanced_script_text.get(1.0, END).strip()
            if not advanced_script:
                messagebox.showerror("错误", "高级脚本不能为空")
                return
            naming_config = {
                'advanced_enabled': True,
                'advanced_script': advanced_script
            }
        else:
            script_template = self.script_template_text.get(1.0, END).strip()
            naming_config = {
                'advanced_enabled': False,
                'text_enabled': self.use_text.get(),
                'text_content': self.custom_text.get().strip(),
                'text_position': self.text_pos.get(),
                'number_enabled': self.use_number.get(),
                'start_number': self.start_number.get(),
                'script_enabled': self.use_script.get(),
                'script_template': script_template
            }
            if naming_config['script_enabled'] and not naming_config['script_template']:
                messagebox.showerror("错误", "脚本模板不能为空")
                return
            if naming_config['text_enabled'] and not naming_config['text_content']:
                messagebox.showerror("错误", "文字内容不能为空")
                return

        output_format = self.output_format.get()
        skip_existing = self.skip_existing.get()

        tasks = collect_all_image_tasks(src, dst, skip_existing, naming_config, output_format, self.log)
        if not tasks:
            messagebox.showinfo("提示", "未找到任何支持的图片文件")
            return

        total = len(tasks)
        self.log(f"共发现 {total} 个图片文件需要处理")
        self.log(f"断点续传: {'开启' if skip_existing else '关闭'}")
        self.log(f"输出格式: {output_format}")
        if advanced_enabled:
            self.log("命名规则: 高级脚本模式")
        else:
            if naming_config['script_enabled']:
                self.log(f"命名规则: 脚本模板 '{naming_config['script_template']}'")
            else:
                parts = []
                if naming_config['text_enabled']:
                    pos = naming_config['text_position']
                    pos_name = {'start':'开头', 'after_basename':'原文件名结尾', 'end':'新名字结尾'}[pos]
                    parts.append(f"文字'{naming_config['text_content']}'({pos_name})")
                if naming_config['number_enabled']:
                    parts.append(f"编号(起始{naming_config['start_number']})")
                if parts:
                    self.log(f"命名规则: {' + '.join(parts)}")
                else:
                    self.log("命名规则: 保持原文件名")

        config = {
            'h_align': self.h_align.get(),
            'v_align': self.v_align.get(),
            'h_offset': self.h_offset.get(),
            'v_offset': self.v_offset.get(),
            'watermark_width_ratio': self.width_ratio.get(),
            'watermark_opacity': self.opacity.get(),
            'jpeg_quality': self.jpeg_quality.get(),
            'auto_quality': self.auto_quality.get(),
            'target_size_kb': self.target_size.get(),
            'quality_step': self.quality_step.get(),
            'min_quality': self.min_quality.get(),
            'max_quality': self.max_quality.get(),
            'skip_existing': skip_existing,
            'output_format': output_format,
        }
        self.start_btn.config(state=DISABLED)
        self.stop_btn.config(state=NORMAL)
        self.stop_flag = False
        self.processing_thread = threading.Thread(target=self.process_all, args=(tasks, watermark_img, config), daemon=True)
        self.processing_thread.start()

    def process_all(self, tasks, watermark_img, config):
        success_count = 0
        fail_count = 0
        skip_count = 0
        for idx, (src_path, dst_path) in enumerate(tasks, 1):
            if self.stop_flag:
                self.log("用户已停止处理。")
                break
            def log_cb(msg):
                self.log(msg)
            ok, skipped, size_kb, error = add_single_watermark(src_path, dst_path, watermark_img, config, log_cb)
            if ok:
                if skipped:
                    skip_count += 1
                else:
                    success_count += 1
            else:
                fail_count += 1
        self.root.after(0, lambda: self.on_finished(success_count, fail_count, skip_count))

    def on_finished(self, success, fail, skip):
        self.start_btn.config(state=NORMAL)
        self.stop_btn.config(state=DISABLED)
        self.log(f"\n处理完成！成功: {success}, 失败: {fail}, 跳过: {skip}")
        messagebox.showinfo("完成", f"批量处理结束\n成功: {success}\n失败: {fail}\n跳过: {skip}")

if __name__ == "__main__":
    root = Tk()
    app = WatermarkApp(root)
    root.mainloop()