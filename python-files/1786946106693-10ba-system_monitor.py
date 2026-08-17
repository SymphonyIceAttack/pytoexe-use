# -*- coding: utf-8 -*-
"""
مانیتور سیستم — Simlang Studio
نمایش لحظه‌ای اطلاعات کامل سخت‌افزاری با رابط کاربری نارنجی
ساخته شده توسط سیملانگ استودیو
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
import platform
import math
import socket

import psutil

# ---------- کتابخانه‌های اختیاری (در صورت نبود، بی‌صدا رد می‌شود) ----------
try:
    import cpuinfo
    HAS_CPUINFO = True
except ImportError:
    HAS_CPUINFO = False

try:
    import GPUtil
    HAS_GPUTIL = True
except ImportError:
    HAS_GPUTIL = False

try:
    import wmi
    HAS_WMI = True
except ImportError:
    HAS_WMI = False


# ============================= رنگ‌بندی نارنجی =============================
COLOR_BG          = "#1c1712"
COLOR_PANEL       = "#2a2119"
COLOR_PANEL_2     = "#332818"
COLOR_ORANGE      = "#ff8c1a"
COLOR_ORANGE_DIM  = "#c96f14"
COLOR_ORANGE_LIGHT= "#ffb066"
COLOR_TEXT        = "#f5e8d8"
COLOR_TEXT_DIM    = "#b8a48c"
COLOR_GREEN       = "#7fd858"
COLOR_RED         = "#ff5c4d"
COLOR_YELLOW      = "#ffd166"

FONT_TITLE  = ("Segoe UI", 20, "bold")
FONT_HEAD   = ("Segoe UI", 12, "bold")
FONT_LABEL  = ("Segoe UI", 10)
FONT_VALUE  = ("Segoe UI", 10, "bold")
FONT_BIG    = ("Segoe UI", 26, "bold")
FONT_SMALL  = ("Segoe UI", 8)


def bytes_to_human(n):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(n) < 1024.0:
            return f"{n:3.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} PB"


def status_color(percent):
    if percent < 50:
        return COLOR_GREEN
    if percent < 80:
        return COLOR_YELLOW
    return COLOR_RED


# ============================= ویجت نوار پیشرفت سفارشی =============================
class OrangeBar(tk.Canvas):
    def __init__(self, master, width=220, height=14, **kwargs):
        super().__init__(master, width=width, height=height,
                          bg=COLOR_PANEL_2, highlightthickness=0, **kwargs)
        self.width = width
        self.height = height
        self.set_value(0)

    def set_value(self, percent):
        percent = max(0, min(100, percent))
        self.delete("all")
        self.create_rectangle(0, 0, self.width, self.height,
                               fill=COLOR_PANEL_2, outline="")
        fill_w = int(self.width * percent / 100)
        color = status_color(percent)
        if fill_w > 0:
            self.create_rectangle(0, 0, fill_w, self.height,
                                   fill=color, outline="")
        self.create_rectangle(0, 0, self.width, self.height,
                               outline=COLOR_ORANGE_DIM)


# ============================= پره‌ی متحرک (Propeller) =============================
class Propeller(tk.Canvas):
    """پره‌ای که سرعت چرخشش با میزان بار سیستم متناسب است"""

    def __init__(self, master, size=140, **kwargs):
        super().__init__(master, width=size, height=size,
                          bg=COLOR_BG, highlightthickness=0, **kwargs)
        self.size = size
        self.angle = 0.0
        self.speed = 2.0  # درجه بر فریم، بر اساس بار سیستم آپدیت می‌شود
        self._running = True
        self._tick()

    def set_load(self, percent):
        # سرعت چرخش بین 1 تا 28 درجه بر فریم
        self.speed = 1 + (percent / 100.0) * 27

    def _tick(self):
        if not self._running:
            return
        self.angle = (self.angle + self.speed) % 360
        self._draw()
        self.after(30, self._tick)

    def _draw(self):
        self.delete("all")
        cx = cy = self.size / 2
        r_hub = self.size * 0.10
        blade_len = self.size * 0.42
        blade_w = self.size * 0.16

        # پرتوهای نارنجی پشت پره برای حس انرژی
        self.create_oval(cx - self.size*0.48, cy - self.size*0.48,
                          cx + self.size*0.48, cy + self.size*0.48,
                          outline=COLOR_ORANGE_DIM, width=1)

        for i in range(3):
            a = math.radians(self.angle + i * 120)
            tip_x = cx + blade_len * math.cos(a)
            tip_y = cy + blade_len * math.sin(a)
            perp = a + math.pi / 2
            w = blade_w / 2
            p1 = (cx + w * math.cos(perp), cy + w * math.sin(perp))
            p2 = (cx - w * math.cos(perp), cy - w * math.sin(perp))
            self.create_polygon(
                p1[0], p1[1], tip_x, tip_y, p2[0], p2[1],
                fill=COLOR_ORANGE, outline=COLOR_ORANGE_LIGHT, smooth=True
            )

        self.create_oval(cx - r_hub, cy - r_hub, cx + r_hub, cy + r_hub,
                          fill=COLOR_ORANGE_LIGHT, outline=COLOR_TEXT)

    def stop(self):
        self._running = False


# ============================= پنل بخش =============================
class Section(tk.Frame):
    def __init__(self, master, title, **kwargs):
        super().__init__(master, bg=COLOR_PANEL, bd=0,
                          highlightbackground=COLOR_ORANGE_DIM,
                          highlightthickness=1, **kwargs)
        head = tk.Label(self, text=title, font=FONT_HEAD,
                         bg=COLOR_PANEL, fg=COLOR_ORANGE, anchor="w")
        head.pack(fill="x", padx=12, pady=(10, 4))
        self.body = tk.Frame(self, bg=COLOR_PANEL)
        self.body.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    def add_row(self, label_text):
        row = tk.Frame(self.body, bg=COLOR_PANEL)
        row.pack(fill="x", pady=3)
        lbl = tk.Label(row, text=label_text, font=FONT_LABEL,
                        bg=COLOR_PANEL, fg=COLOR_TEXT_DIM, anchor="w", width=16)
        lbl.pack(side="left")
        val = tk.Label(row, text="—", font=FONT_VALUE,
                        bg=COLOR_PANEL, fg=COLOR_TEXT, anchor="w")
        val.pack(side="left", fill="x", expand=True)
        return val


# ============================= برنامه اصلی =============================
class SystemMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("مانیتور سیستم — Simlang Studio")
        self.root.geometry("1150x760")
        self.root.configure(bg=COLOR_BG)
        self.root.minsize(1000, 680)

        self._build_ui()
        self._net_last = psutil.net_io_counters()
        self._disk_last = psutil.disk_io_counters()
        self._last_time = time.time()

        self._running = True
        self._start_worker()

    # ---------------------- ساخت رابط کاربری ----------------------
    def _build_ui(self):
        header = tk.Frame(self.root, bg=COLOR_BG)
        header.pack(fill="x", padx=20, pady=(16, 6))

        title = tk.Label(header, text="مانیتور سیستم", font=FONT_TITLE,
                          bg=COLOR_BG, fg=COLOR_ORANGE)
        title.pack(side="right")

        subtitle = tk.Label(header, text="ساخته شده توسط سیملانگ استودیو",
                             font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_TEXT_DIM)
        subtitle.pack(side="right", padx=(0, 14), pady=(8, 0))

        # ناحیه بالا: پره + خلاصه سریع
        top = tk.Frame(self.root, bg=COLOR_BG)
        top.pack(fill="x", padx=20, pady=6)

        prop_frame = tk.Frame(top, bg=COLOR_BG)
        prop_frame.pack(side="right", padx=10)
        self.propeller = Propeller(prop_frame, size=140)
        self.propeller.pack()
        self.load_label = tk.Label(prop_frame, text="بار سیستم: 0%",
                                    font=FONT_LABEL, bg=COLOR_BG, fg=COLOR_TEXT_DIM)
        self.load_label.pack(pady=(4, 0))

        quick = tk.Frame(top, bg=COLOR_BG)
        quick.pack(side="right", fill="x", expand=True, padx=10)

        self.quick_cpu = self._quick_stat(quick, "CPU")
        self.quick_ram = self._quick_stat(quick, "RAM")
        self.quick_disk = self._quick_stat(quick, "دیسک")
        self.quick_gpu = self._quick_stat(quick, "GPU")

        # ناحیه اصلی: گرید پنل‌ها
        main = tk.Frame(self.root, bg=COLOR_BG)
        main.pack(fill="both", expand=True, padx=20, pady=10)
        main.columnconfigure((0, 1, 2), weight=1, uniform="col")
        main.rowconfigure((0, 1), weight=1)

        # --- پنل CPU ---
        self.sec_cpu = Section(main, "پردازنده (CPU)")
        self.sec_cpu.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        self.val_cpu_model = self.sec_cpu.add_row("مدل")
        self.val_cpu_cores = self.sec_cpu.add_row("هسته/ترد")
        self.val_cpu_freq = self.sec_cpu.add_row("فرکانس")
        self.val_cpu_temp = self.sec_cpu.add_row("دما")
        self.bar_cpu = OrangeBar(self.sec_cpu.body, width=230)
        self.bar_cpu.pack(anchor="w", pady=(6, 2))
        self.cores_frame = tk.Frame(self.sec_cpu.body, bg=COLOR_PANEL)
        self.cores_frame.pack(fill="x", pady=(6, 0))
        self.core_bars = []

        # --- پنل RAM ---
        self.sec_ram = Section(main, "حافظه (RAM)")
        self.sec_ram.grid(row=0, column=1, sticky="nsew", padx=6, pady=6)
        self.val_ram_total = self.sec_ram.add_row("کل حافظه")
        self.val_ram_used = self.sec_ram.add_row("استفاده‌شده")
        self.val_ram_free = self.sec_ram.add_row("آزاد")
        self.val_swap = self.sec_ram.add_row("Swap")
        self.bar_ram = OrangeBar(self.sec_ram.body, width=230)
        self.bar_ram.pack(anchor="w", pady=(6, 2))

        # --- پنل GPU ---
        self.sec_gpu = Section(main, "کارت گرافیک (GPU)")
        self.sec_gpu.grid(row=0, column=2, sticky="nsew", padx=6, pady=6)
        self.val_gpu_model = self.sec_gpu.add_row("مدل")
        self.val_gpu_temp = self.sec_gpu.add_row("دما")
        self.val_gpu_vram = self.sec_gpu.add_row("VRAM")
        self.bar_gpu = OrangeBar(self.sec_gpu.body, width=230)
        self.bar_gpu.pack(anchor="w", pady=(6, 2))

        # --- پنل دیسک ---
        self.sec_disk = Section(main, "دیسک")
        self.sec_disk.grid(row=1, column=0, sticky="nsew", padx=6, pady=6)
        self.disk_partition_labels = []
        self.val_disk_read = self.sec_disk.add_row("خواندن")
        self.val_disk_write = self.sec_disk.add_row("نوشتن")

        # --- پنل شبکه ---
        self.sec_net = Section(main, "شبکه")
        self.sec_net.grid(row=1, column=1, sticky="nsew", padx=6, pady=6)
        self.val_net_name = self.sec_net.add_row("نام دستگاه")
        self.val_net_up = self.sec_net.add_row("آپلود")
        self.val_net_down = self.sec_net.add_row("دانلود")
        self.val_net_sent = self.sec_net.add_row("کل ارسالی")
        self.val_net_recv = self.sec_net.add_row("کل دریافتی")

        # --- پنل سیستم/باتری ---
        self.sec_sys = Section(main, "سیستم و باتری")
        self.sec_sys.grid(row=1, column=2, sticky="nsew", padx=6, pady=6)
        self.val_os = self.sec_sys.add_row("سیستم‌عامل")
        self.val_uptime = self.sec_sys.add_row("زمان روشن بودن")
        self.val_battery = self.sec_sys.add_row("باتری")
        self.val_procs = self.sec_sys.add_row("تعداد پردازش‌ها")

        # نوار پایین
        footer = tk.Frame(self.root, bg=COLOR_PANEL, height=26)
        footer.pack(fill="x", side="bottom")
        self.status_label = tk.Label(footer, text="آماده", font=FONT_SMALL,
                                      bg=COLOR_PANEL, fg=COLOR_TEXT_DIM)
        self.status_label.pack(side="right", padx=10, pady=4)

    def _quick_stat(self, parent, name):
        box = tk.Frame(parent, bg=COLOR_PANEL, highlightbackground=COLOR_ORANGE_DIM,
                        highlightthickness=1)
        box.pack(side="right", padx=6, fill="both", expand=True, ipady=6)
        tk.Label(box, text=name, font=FONT_LABEL, bg=COLOR_PANEL,
                 fg=COLOR_TEXT_DIM).pack(pady=(6, 0))
        val = tk.Label(box, text="0%", font=FONT_BIG, bg=COLOR_PANEL, fg=COLOR_ORANGE)
        val.pack(pady=(0, 6))
        return val

    # ---------------------- به‌روزرسانی داده‌ها (ترد جدا) ----------------------
    def _start_worker(self):
        self.root.after(200, self._update_static_info)
        t = threading.Thread(target=self._worker_loop, daemon=True)
        t.start()

    def _update_static_info(self):
        """اطلاعات ثابت که فقط یک بار خوانده می‌شود"""
        try:
            if HAS_CPUINFO:
                info = cpuinfo.get_cpu_info()
                cpu_name = info.get("brand_raw", platform.processor())
            else:
                cpu_name = platform.processor() or "نامشخص"
        except Exception:
            cpu_name = "نامشخص"

        self.val_cpu_model.config(text=cpu_name)
        self.val_cpu_cores.config(
            text=f"{psutil.cpu_count(logical=False)} هسته / {psutil.cpu_count(logical=True)} ترد"
        )

        # ساخت نوارهای هسته‌به‌هسته
        n = psutil.cpu_count(logical=True)
        for i in range(n):
            row = tk.Frame(self.cores_frame, bg=COLOR_PANEL)
            row.pack(fill="x", pady=1)
            tk.Label(row, text=f"هسته {i+1}", font=FONT_SMALL,
                     bg=COLOR_PANEL, fg=COLOR_TEXT_DIM, width=8, anchor="w").pack(side="left")
            bar = OrangeBar(row, width=170, height=8)
            bar.pack(side="left")
            self.core_bars.append(bar)

        self.val_net_name.config(text=socket.gethostname())
        self.val_os.config(
            text=f"{platform.system()} {platform.release()} ({platform.machine()})"
        )

        # اسکن پارتیشن‌های دیسک
        for part in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(part.mountpoint)
            except (PermissionError, OSError):
                continue
            row = tk.Frame(self.sec_disk.body, bg=COLOR_PANEL)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=part.device, font=FONT_LABEL,
                     bg=COLOR_PANEL, fg=COLOR_TEXT_DIM, width=10, anchor="w").pack(side="left")
            bar = OrangeBar(row, width=110, height=10)
            bar.pack(side="left", padx=4)
            lbl = tk.Label(row, text="", font=FONT_SMALL,
                            bg=COLOR_PANEL, fg=COLOR_TEXT)
            lbl.pack(side="left", padx=4)
            self.disk_partition_labels.append((part.mountpoint, bar, lbl, usage))
        # جابجایی ردیف‌های خواندن/نوشتن به پایین
        self.val_disk_read.master.pack(fill="x", pady=3)
        self.val_disk_write.master.pack(fill="x", pady=3)

    def _worker_loop(self):
        psutil.cpu_percent(percpu=True)  # فراخوانی اول برای کالیبراسیون
        while self._running:
            try:
                data = self._collect()
                self.root.after(0, self._apply, data)
            except Exception as e:
                self.root.after(0, lambda: self.status_label.config(
                    text=f"خطا: {e}", fg=COLOR_RED))
            time.sleep(1)

    def _collect(self):
        d = {}
        # CPU
        d["cpu_percpu"] = psutil.cpu_percent(percpu=True)
        d["cpu_total"] = sum(d["cpu_percpu"]) / len(d["cpu_percpu"])
        freq = psutil.cpu_freq()
        d["cpu_freq"] = freq.current if freq else None
        try:
            temps = psutil.sensors_temperatures()
            cpu_temp = None
            for name, entries in temps.items():
                if entries:
                    cpu_temp = entries[0].current
                    break
            d["cpu_temp"] = cpu_temp
        except (AttributeError, Exception):
            d["cpu_temp"] = None

        # RAM
        vm = psutil.virtual_memory()
        d["ram"] = vm
        d["swap"] = psutil.swap_memory()

        # GPU
        d["gpu"] = None
        if HAS_GPUTIL:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    g = gpus[0]
                    d["gpu"] = {
                        "name": g.name, "temp": g.temperature,
                        "load": g.load * 100,
                        "mem_used": g.memoryUsed, "mem_total": g.memoryTotal,
                    }
            except Exception:
                pass

        # دیسک I/O
        disk_io = psutil.disk_io_counters()
        d["disk_io"] = disk_io

        # شبکه
        d["net_io"] = psutil.net_io_counters()

        # سیستم
        d["boot_time"] = psutil.boot_time()
        d["proc_count"] = len(psutil.pids())
        try:
            batt = psutil.sensors_battery()
            d["battery"] = batt
        except Exception:
            d["battery"] = None

        return d

    # ---------------------- اعمال داده روی UI (در ترد اصلی) ----------------------
    def _apply(self, d):
        now = time.time()
        dt = max(now - self._last_time, 0.001)

        # CPU
        cpu_total = d["cpu_total"]
        self.bar_cpu.set_value(cpu_total)
        self.quick_cpu.config(text=f"{cpu_total:.0f}%", fg=status_color(cpu_total))
        for i, val in enumerate(d["cpu_percpu"]):
            if i < len(self.core_bars):
                self.core_bars[i].set_value(val)
        if d["cpu_freq"]:
            self.val_cpu_freq.config(text=f"{d['cpu_freq']:.0f} MHz")
        if d["cpu_temp"] is not None:
            self.val_cpu_temp.config(text=f"{d['cpu_temp']:.0f}°C",
                                      fg=status_color(d["cpu_temp"]))
        else:
            self.val_cpu_temp.config(text="در دسترس نیست")

        # RAM
        vm = d["ram"]
        self.bar_ram.set_value(vm.percent)
        self.quick_ram.config(text=f"{vm.percent:.0f}%", fg=status_color(vm.percent))
        self.val_ram_total.config(text=bytes_to_human(vm.total))
        self.val_ram_used.config(text=bytes_to_human(vm.used))
        self.val_ram_free.config(text=bytes_to_human(vm.available))
        sw = d["swap"]
        self.val_swap.config(text=f"{bytes_to_human(sw.used)} / {bytes_to_human(sw.total)}")

        # GPU
        if d["gpu"]:
            g = d["gpu"]
            self.val_gpu_model.config(text=g["name"])
            self.val_gpu_temp.config(text=f"{g['temp']:.0f}°C", fg=status_color(g["temp"]))
            self.val_gpu_vram.config(text=f"{g['mem_used']:.0f} / {g['mem_total']:.0f} MB")
            self.bar_gpu.set_value(g["load"])
            self.quick_gpu.config(text=f"{g['load']:.0f}%", fg=status_color(g["load"]))
        else:
            self.val_gpu_model.config(text="یافت نشد / پشتیبانی نمی‌شود")
            self.quick_gpu.config(text="—", fg=COLOR_TEXT_DIM)

        # دیسک I/O
        disk_io = d["disk_io"]
        if disk_io and self._disk_last:
            read_speed = (disk_io.read_bytes - self._disk_last.read_bytes) / dt
            write_speed = (disk_io.write_bytes - self._disk_last.write_bytes) / dt
            self.val_disk_read.config(text=f"{bytes_to_human(read_speed)}/s")
            self.val_disk_write.config(text=f"{bytes_to_human(write_speed)}/s")
        self._disk_last = disk_io

        max_disk_pct = 0
        for mountpoint, bar, lbl, _old_usage in self.disk_partition_labels:
            try:
                usage = psutil.disk_usage(mountpoint)
                bar.set_value(usage.percent)
                lbl.config(text=f"{usage.percent:.0f}% از {bytes_to_human(usage.total)}")
                max_disk_pct = max(max_disk_pct, usage.percent)
            except OSError:
                continue
        self.quick_disk.config(text=f"{max_disk_pct:.0f}%", fg=status_color(max_disk_pct))

        # شبکه
        net_io = d["net_io"]
        if net_io and self._net_last:
            up_speed = (net_io.bytes_sent - self._net_last.bytes_sent) / dt
            down_speed = (net_io.bytes_recv - self._net_last.bytes_recv) / dt
            self.val_net_up.config(text=f"{bytes_to_human(up_speed)}/s")
            self.val_net_down.config(text=f"{bytes_to_human(down_speed)}/s")
            self.val_net_sent.config(text=bytes_to_human(net_io.bytes_sent))
            self.val_net_recv.config(text=bytes_to_human(net_io.bytes_recv))
        self._net_last = net_io

        # سیستم
        uptime_sec = now - d["boot_time"]
        hrs = int(uptime_sec // 3600)
        mins = int((uptime_sec % 3600) // 60)
        self.val_uptime.config(text=f"{hrs} ساعت و {mins} دقیقه")
        self.val_procs.config(text=str(d["proc_count"]))

        batt = d["battery"]
        if batt:
            state = "در حال شارژ" if batt.power_plugged else "تخلیه باتری"
            self.val_battery.config(text=f"{batt.percent:.0f}% ({state})",
                                     fg=status_color(100 - batt.percent))
        else:
            self.val_battery.config(text="یافت نشد (دسکتاپ)")

        # پره و بار کلی سیستم
        overall_load = (cpu_total + vm.percent) / 2
        self.propeller.set_load(overall_load)
        self.load_label.config(text=f"بار سیستم: {overall_load:.0f}%")

        self.status_label.config(
            text=f"آخرین به‌روزرسانی: {time.strftime('%H:%M:%S')}", fg=COLOR_TEXT_DIM)

        self._last_time = now

    def stop(self):
        self._running = False
        self.propeller.stop()


def main():
    root = tk.Tk()
    app = SystemMonitorApp(root)

    def on_close():
        app.stop()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
