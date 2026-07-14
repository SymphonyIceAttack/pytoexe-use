"""
PDF Size Compressor (GUI) - v2 (Faster, Multi-core, Splash Screen)
===================================================================

Developed By Imran Hossain

এই প্রোগ্রামটি একটি সোর্স ফোল্ডার থেকে সব PDF ফাইল স্ক্যান করে:
  - যেসব ফাইলের সাইজ নির্দিষ্ট লিমিটের (ডিফল্ট ২০০ KB) বেশি, সেগুলোকে
    কম্প্রেস করে লিমিটের নিচে আনার চেষ্টা করে এবং আউটপুট ফোল্ডারে সেভ করে।
  - যেসব ফাইলের সাইজ লিমিটের সমান বা কম, সেগুলোকে কম্প্রেস না করে
    সরাসরি (as-is) কপি করে আউটপুট ফোল্ডারে রাখে।
  - একাধিক CPU কোর ব্যবহার করে সমান্তরালভাবে (parallel) ফাইল প্রসেস করে বলে
    আগের ভার্সনের চেয়ে অনেক দ্রুত কাজ করে।
  - GUI তে দেখা যাবে মোট কতগুলো ফাইল লোড হয়েছে আর কতগুলো সম্পন্ন হয়েছে।

চালানোর আগে (একবারই, টার্মিনালে):
    pip install pymupdf

তারপর:
    python pdf_compressor_gui_v2.py
"""

import os
import shutil
import queue
import threading
import multiprocessing
import concurrent.futures
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

DEVELOPER_TEXT = "This Pdf File compressor is Developed By Imran Hossain"
DEVELOPER_ROLE = "Scanning & Equipment Maintenance Operator"
DEVELOPER_CONTACT = "WhatsApp: 01737045288"
SPLASH_SECONDS = 20


# ------------------------- কম্প্রেশন লজিক (worker process এ চলে) ------------------------- #

def compress_pdf(input_path: str, output_path: str, target_bytes: int) -> int:
    """
    input_path এর PDF কে বারবার (quality/scale কমিয়ে কমিয়ে) কম্প্রেস করে
    output_path এ সেভ করে, যতক্ষণ না সাইজ target_bytes এর নিচে আসে অথবা
    আর কমানোর সুযোগ না থাকে। ফাইনাল সাইজ (bytes) রিটার্ন করে।
    """
    quality = 80
    scale = 1.0
    min_quality = 15
    min_scale = 0.25
    best_size = None

    while True:
        doc = fitz.open(input_path)

        for page in doc:
            try:
                images = page.get_images(full=True)
            except Exception:
                images = []

            for img in images:
                xref = img[0]
                try:
                    pix = fitz.Pixmap(doc, xref)

                    if pix.n - pix.alpha >= 4:  # CMYK -> RGB
                        pix = fitz.Pixmap(fitz.csRGB, pix)

                    if scale < 0.999:
                        new_w = max(1, int(pix.width * scale))
                        new_h = max(1, int(pix.height * scale))
                        pix = fitz.Pixmap(pix, new_w, new_h, None)

                    jpg_bytes = pix.tobytes("jpeg", jpg_quality=quality)
                    page.replace_image(xref, stream=jpg_bytes)
                except Exception:
                    continue

        doc.save(output_path, deflate=True, garbage=4, clean=True)
        doc.close()

        size = os.path.getsize(output_path)
        best_size = size

        if size <= target_bytes:
            break
        if quality <= min_quality and scale <= min_scale:
            break

        if quality > min_quality:
            quality = max(min_quality, quality - 15)
        else:
            scale = max(min_scale, round(scale - 0.15, 2))

    return best_size


def process_single_pdf(path: str, dest: str, target_bytes: int) -> dict:
    """
    একটা মাত্র PDF প্রসেস করে (কপি অথবা কম্প্রেস)। এই ফাংশনটা আলাদা প্রসেসে
    চলে (ProcessPoolExecutor), তাই এখান থেকে সরাসরি Tkinter আপডেট করা যাবে না —
    শুধু একটা dict রেজাল্ট রিটার্ন করবে।
    """
    name = os.path.basename(path)
    try:
        orig_size = os.path.getsize(path)

        if orig_size <= target_bytes:
            shutil.copy2(path, dest)
            return {
                "name": name, "status": "copied",
                "orig_size": orig_size, "final_size": orig_size, "error": None,
            }
        else:
            final_size = compress_pdf(path, dest, target_bytes)
            status = "compressed" if final_size <= target_bytes else "partial"
            return {
                "name": name, "status": status,
                "orig_size": orig_size, "final_size": final_size, "error": None,
            }
    except Exception as e:
        return {
            "name": name, "status": "failed",
            "orig_size": 0, "final_size": 0, "error": str(e),
        }


# --------------------------------- স্প্ল্যাশ স্ক্রিন --------------------------------- #

class SplashScreen(tk.Toplevel):
    def __init__(self, master, on_done, seconds=SPLASH_SECONDS):
        super().__init__(master)
        self.on_done = on_done
        self.seconds = seconds

        self.overrideredirect(True)
        w, h = 520, 260
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.configure(bg="#1b1f27")

        tk.Label(self, text="PDF Size Compressor", font=("Segoe UI", 20, "bold"),
                 bg="#1b1f27", fg="#ffffff").pack(pady=(45, 10))

        tk.Label(self, text=DEVELOPER_TEXT, font=("Segoe UI", 11),
                 bg="#1b1f27", fg="#9ad1ff", wraplength=460, justify="center").pack(pady=(0, 4))

        tk.Label(self, text=DEVELOPER_ROLE, font=("Segoe UI", 9, "italic"),
                 bg="#1b1f27", fg="#bbbbbb", wraplength=460, justify="center").pack(pady=(0, 2))

        tk.Label(self, text=DEVELOPER_CONTACT, font=("Segoe UI", 9),
                 bg="#1b1f27", fg="#25d366", wraplength=460, justify="center").pack(pady=(0, 16))

        self.progress = ttk.Progressbar(self, orient="horizontal", mode="determinate",
                                         length=420, maximum=self.seconds)
        self.progress.pack(pady=10)

        self.count_label = tk.Label(self, text="", font=("Segoe UI", 9),
                                     bg="#1b1f27", fg="#cccccc")
        self.count_label.pack()

        self.remaining = self.seconds
        self.tick()

    def tick(self):
        self.progress.configure(value=self.seconds - self.remaining)
        self.count_label.configure(text=f"লোড হচ্ছে... {self.remaining} সেকেন্ড")
        if self.remaining <= 0:
            self.destroy()
            self.on_done()
            return
        self.remaining -= 1
        self.after(1000, self.tick)


# --------------------------------- মূল GUI --------------------------------- #

class PDFCompressorApp:
    def __init__(self, root):
        self.root = root
        root.title("PDF Size Compressor - by Imran Hossain")
        root.geometry("700x580")
        root.resizable(True, True)

        self.result_queue = queue.Queue()
        self.worker_thread = None
        self.is_running = False

        pad = {"padx": 10, "pady": 6}

        # সোর্স ফোল্ডার
        frame1 = tk.Frame(root)
        frame1.pack(fill="x", **pad)
        tk.Label(frame1, text="সোর্স ফোল্ডার:", width=16, anchor="w").pack(side="left")
        self.source_var = tk.StringVar()
        tk.Entry(frame1, textvariable=self.source_var).pack(side="left", fill="x", expand=True, padx=5)
        tk.Button(frame1, text="ব্রাউজ", command=self.browse_source).pack(side="left")

        # আউটপুট ফোল্ডার
        frame2 = tk.Frame(root)
        frame2.pack(fill="x", **pad)
        tk.Label(frame2, text="আউটপুট ফোল্ডার:", width=16, anchor="w").pack(side="left")
        self.output_var = tk.StringVar()
        tk.Entry(frame2, textvariable=self.output_var).pack(side="left", fill="x", expand=True, padx=5)
        tk.Button(frame2, text="ব্রাউজ", command=self.browse_output).pack(side="left")

        # টার্গেট সাইজ + ওয়ার্কার সংখ্যা + সাবফোল্ডার
        frame3 = tk.Frame(root)
        frame3.pack(fill="x", **pad)
        tk.Label(frame3, text="টার্গেট সাইজ (KB):", width=16, anchor="w").pack(side="left")
        self.target_var = tk.StringVar(value="200")
        tk.Entry(frame3, textvariable=self.target_var, width=8).pack(side="left", padx=5)

        tk.Label(frame3, text="সমান্তরাল ওয়ার্কার:").pack(side="left", padx=(15, 0))
        self.workers_var = tk.StringVar(value=str(max(1, os.cpu_count() or 1)))
        tk.Entry(frame3, textvariable=self.workers_var, width=5).pack(side="left", padx=5)

        self.recursive_var = tk.BooleanVar(value=False)
        tk.Checkbutton(frame3, text="সাবফোল্ডারসহ স্ক্যান করো", variable=self.recursive_var).pack(side="left", padx=15)

        # স্ট্যাটাস কাউন্টার (লোড হয়েছে / সম্পন্ন হয়েছে)
        frame_status = tk.Frame(root)
        frame_status.pack(fill="x", **pad)

        self.loaded_var = tk.StringVar(value="মোট ফাইল লোড হয়েছে: 0")
        tk.Label(frame_status, textvariable=self.loaded_var, font=("Segoe UI", 10, "bold"),
                 fg="#1565c0").pack(side="left", padx=(0, 25))

        self.done_var = tk.StringVar(value="সম্পন্ন হয়েছে: 0 / 0")
        tk.Label(frame_status, textvariable=self.done_var, font=("Segoe UI", 10, "bold"),
                 fg="#2e7d32").pack(side="left", padx=(0, 25))

        self.copied_var = tk.StringVar(value="কপি: 0")
        tk.Label(frame_status, textvariable=self.copied_var).pack(side="left", padx=(0, 15))
        self.compressed_var = tk.StringVar(value="কম্প্রেস: 0")
        tk.Label(frame_status, textvariable=self.compressed_var).pack(side="left", padx=(0, 15))
        self.failed_var = tk.StringVar(value="ব্যর্থ: 0")
        tk.Label(frame_status, textvariable=self.failed_var, fg="#c62828").pack(side="left")

        # স্টার্ট বাটন + প্রোগ্রেস বার
        frame4 = tk.Frame(root)
        frame4.pack(fill="x", **pad)
        self.start_btn = tk.Button(frame4, text="শুরু করুন", command=self.start_clicked,
                                    bg="#2e7d32", fg="white", width=14)
        self.start_btn.pack(side="left")
        self.progress = ttk.Progressbar(frame4, orient="horizontal", mode="determinate")
        self.progress.pack(side="left", fill="x", expand=True, padx=10)

        # লগ উইন্ডো
        frame5 = tk.Frame(root)
        frame5.pack(fill="both", expand=True, **pad)
        self.log_text = tk.Text(frame5, wrap="word", state="disabled")
        scroll = tk.Scrollbar(frame5, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scroll.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # ফুটার
        footer_text = f"{DEVELOPER_TEXT}  |  {DEVELOPER_ROLE}  |  {DEVELOPER_CONTACT}"
        tk.Label(root, text=footer_text, font=("Segoe UI", 8), fg="#777777").pack(pady=(0, 6))

        if fitz is None:
            self.log("সতর্কতা: PyMuPDF (fitz) ইনস্টল করা নেই। টার্মিনালে চালান: pip install pymupdf")

    # ---------------------- UI হেল্পার ---------------------- #

    def browse_source(self):
        path = filedialog.askdirectory(title="সোর্স ফোল্ডার সিলেক্ট করুন")
        if path:
            self.source_var.set(path)

    def browse_output(self):
        path = filedialog.askdirectory(title="আউটপুট ফোল্ডার সিলেক্ট করুন")
        if path:
            self.output_var.set(path)

    def log(self, msg: str):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def find_pdfs(self, source):
        recursive = self.recursive_var.get()
        pdfs = []
        if recursive:
            for root_dir, _, files in os.walk(source):
                for f in files:
                    if f.lower().endswith(".pdf"):
                        pdfs.append(os.path.join(root_dir, f))
        else:
            for f in os.listdir(source):
                full = os.path.join(source, f)
                if os.path.isfile(full) and f.lower().endswith(".pdf"):
                    pdfs.append(full)
        return pdfs

    # ---------------------- প্রসেস শুরু/পরিচালনা ---------------------- #

    def start_clicked(self):
        if self.is_running:
            return

        source = self.source_var.get().strip()
        output = self.output_var.get().strip()

        if not source or not os.path.isdir(source):
            messagebox.showerror("ত্রুটি", "সঠিক সোর্স ফোল্ডার সিলেক্ট করুন।")
            return
        if not output:
            messagebox.showerror("ত্রুটি", "আউটপুট ফোল্ডার সিলেক্ট করুন।")
            return
        if fitz is None:
            messagebox.showerror("ত্রুটি", "PyMuPDF ইনস্টল করা নেই। টার্মিনালে চালান:\npip install pymupdf")
            return

        try:
            target_kb = float(self.target_var.get())
            target_bytes = int(target_kb * 1024)
        except ValueError:
            messagebox.showerror("ত্রুটি", "টার্গেট সাইজ একটি সংখ্যা হতে হবে।")
            return

        try:
            workers = max(1, int(self.workers_var.get()))
        except ValueError:
            workers = max(1, os.cpu_count() or 1)

        os.makedirs(output, exist_ok=True)

        pdfs = self.find_pdfs(source)
        total = len(pdfs)
        self.loaded_var.set(f"মোট ফাইল লোড হয়েছে: {total}")
        self.done_var.set(f"সম্পন্ন হয়েছে: 0 / {total}")
        self.copied_var.set("কপি: 0")
        self.compressed_var.set("কম্প্রেস: 0")
        self.failed_var.set("ব্যর্থ: 0")

        if total == 0:
            self.log("সোর্স ফোল্ডারে কোনো PDF ফাইল পাওয়া যায়নি।")
            return

        self.log(f"মোট {total} টি PDF ফাইল পাওয়া গেছে। {workers} টি ওয়ার্কার দিয়ে প্রসেসিং শুরু হচ্ছে...")

        # dest পাথ আগে থেকেই ঠিক করে নেওয়া (কনফ্লিক্ট এড়াতে) — মূল থ্রেডে করাই নিরাপদ
        tasks = []
        used_names = set()
        for path in pdfs:
            name = os.path.basename(path)
            dest = os.path.join(output, name)
            if dest in used_names or os.path.exists(dest):
                base, ext = os.path.splitext(name)
                counter = 1
                new_dest = dest
                while new_dest in used_names or os.path.exists(new_dest):
                    new_dest = os.path.join(output, f"{base}_{counter}{ext}")
                    counter += 1
                dest = new_dest
            used_names.add(dest)
            tasks.append((path, dest))

        self.progress.configure(maximum=total, value=0)
        self.is_running = True
        self.start_btn.configure(state="disabled")

        self.worker_thread = threading.Thread(
            target=self.run_process, args=(tasks, target_bytes, workers), daemon=True
        )
        self.worker_thread.start()

        self.root.after(150, self.poll_queue, total)

    def run_process(self, tasks, target_bytes, workers):
        """এই ফাংশনটা একটা background thread এ চলে, ProcessPoolExecutor ব্যবহার করে
        একাধিক PDF সমান্তরালভাবে (parallel) প্রসেস করে। প্রতিটা ফলাফল queue তে পাঠানো হয়,
        যা মূল (GUI) থ্রেড পোল করে নিরাপদে UI আপডেট করে।"""
        try:
            with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
                futures = {
                    executor.submit(process_single_pdf, path, dest, target_bytes): path
                    for path, dest in tasks
                }
                for future in concurrent.futures.as_completed(futures):
                    try:
                        result = future.result()
                    except Exception as e:
                        result = {"name": os.path.basename(futures[future]), "status": "failed",
                                  "orig_size": 0, "final_size": 0, "error": str(e)}
                    self.result_queue.put(result)
        except Exception as e:
            self.result_queue.put({"name": "-", "status": "fatal", "orig_size": 0,
                                    "final_size": 0, "error": str(e)})
        finally:
            self.result_queue.put({"status": "__DONE__"})

    def poll_queue(self, total):
        completed = getattr(self, "_completed_count", 0)
        copied = getattr(self, "_copied_count", 0)
        compressed = getattr(self, "_compressed_count", 0)
        failed = getattr(self, "_failed_count", 0)

        try:
            while True:
                result = self.result_queue.get_nowait()

                if result.get("status") == "__DONE__":
                    self.finish_process(total, completed, copied, compressed, failed)
                    return

                status = result["status"]
                name = result["name"]

                if status == "copied":
                    copied += 1
                    self.log(f"✔ {name} — ইতিমধ্যে লিমিটের মধ্যে, কপি করা হয়েছে "
                              f"({result['orig_size']/1024:.1f} KB)")
                elif status == "compressed":
                    compressed += 1
                    self.log(f"✔ {name} — কম্প্রেস সফল: {result['orig_size']/1024:.1f} KB → "
                              f"{result['final_size']/1024:.1f} KB")
                elif status == "partial":
                    compressed += 1
                    self.log(f"⚠ {name} — টার্গেটে আনা যায়নি, সর্বনিম্ন পাওয়া গেছে: "
                              f"{result['final_size']/1024:.1f} KB")
                else:  # failed / fatal
                    failed += 1
                    self.log(f"✘ {name} — ব্যর্থ: {result.get('error')}")

                completed += 1
                self.done_var.set(f"সম্পন্ন হয়েছে: {completed} / {total}")
                self.copied_var.set(f"কপি: {copied}")
                self.compressed_var.set(f"কম্প্রেস: {compressed}")
                self.failed_var.set(f"ব্যর্থ: {failed}")
                self.progress.configure(value=completed)

        except queue.Empty:
            pass

        self._completed_count = completed
        self._copied_count = copied
        self._compressed_count = compressed
        self._failed_count = failed

        if self.is_running:
            self.root.after(150, self.poll_queue, total)

    def finish_process(self, total, completed, copied, compressed, failed):
        self.is_running = False
        self.start_btn.configure(state="normal")
        self._completed_count = 0
        self._copied_count = 0
        self._compressed_count = 0
        self._failed_count = 0
        self.log("\n--- সম্পন্ন ---")
        self.log(f"মোট: {total}, কপি: {copied}, কম্প্রেস: {compressed}, ব্যর্থ: {failed}")
        messagebox.showinfo("সম্পন্ন", "সব ফাইল প্রসেস করা শেষ হয়েছে!")


# --------------------------------- এন্ট্রি পয়েন্ট --------------------------------- #

def main():
    root = tk.Tk()
    root.withdraw()  # স্প্ল্যাশ স্ক্রিন দেখানোর আগ পর্যন্ত মূল উইন্ডো লুকানো থাকবে

    app = PDFCompressorApp(root)

    def show_main():
        root.deiconify()

    SplashScreen(root, on_done=show_main, seconds=SPLASH_SECONDS)

    root.mainloop()


if __name__ == "__main__":
    multiprocessing.freeze_support()  # Windows এ .exe বানালে দরকার হয়
    main()
