import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import re


# ============================================================
# EasyWorship 2009 Lyrics Formatter
# ============================================================

SECTION_PATTERNS = [
    (r"^(verse|verses)\s*(\d*)$", "Verse"),
    (r"^(chorus|choruses)\s*(\d*)$", "Chorus"),
    (r"^(bridge|bridges)\s*(\d*)$", "Bridge"),
    (r"^(intro|intros)\s*(\d*)$", "Intro"),
    (r"^(tag|tags)\s*(\d*)$", "Tag"),
    (r"^(pre[- ]?chorus|prechorus)\s*(\d*)$", "Pre-Chorus"),
    (r"^(ending|end)\s*(\d*)$", "End"),
    (r"^(refrain)\s*(\d*)$", "Refrain"),
]


def detect_section(line):
    """
    Detect common worship-song section headings.

    Examples:
        Verse
        Verse 1
        Chorus
        Chorus 2
        Bridge
        Pre-Chorus
    """
    cleaned = line.strip().lower()

    for pattern, section_name in SECTION_PATTERNS:
        match = re.match(pattern, cleaned, re.IGNORECASE)

        if match:
            number = match.group(2).strip()

            if number:
                return f"{section_name} {number}"
            return section_name

    return None


def split_into_slides(lines, lines_per_slide):
    """
    Split lyric lines into slides.

    Blank lines cause a slide break.
    """
    slides = []
    current = []

    for line in lines:
        line = line.rstrip()

        # Blank line = intentional slide break
        if not line.strip():
            if current:
                slides.append(current)
                current = []
            continue

        current.append(line)

        if len(current) >= lines_per_slide:
            slides.append(current)
            current = []

    if current:
        slides.append(current)

    return slides


def format_lyrics(text, lines_per_slide=4, include_labels=True):
    """
    Main formatter.
    """
    raw_lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")

    slides = []
    current_section = None
    current_lines = []

    def flush():
        nonlocal current_lines

        if not current_lines:
            return

        pieces = split_into_slides(
            current_lines,
            lines_per_slide
        )

        for index, piece in enumerate(pieces):
            slides.append({
                "section": current_section,
                "lines": piece
            })

        current_lines = []

    for raw_line in raw_lines:
        line = raw_line.strip()

        if not line:
            # Blank line ends current slide group
            if current_lines:
                flush()
            continue

        section = detect_section(line)

        if section:
            flush()
            current_section = section
            continue

        current_lines.append(line)

    flush()

    # --------------------------------------------------------
    # Create EasyWorship-friendly text
    #
    # Each blank line represents a new slide when imported.
    # --------------------------------------------------------

    output = []

    for slide in slides:
        block = []

        if include_labels and slide["section"]:
            block.append(slide["section"])

        block.extend(slide["lines"])

        output.append("\n".join(block))

    return "\n\n".join(output), slides


class LyricsFormatterApp:

    def __init__(self, root):
        self.root = root

        self.root.title("EasyWorship 2009 Lyrics Formatter")
        self.root.geometry("1200x750")
        self.root.minsize(900, 600)

        self.slides = []
        self.current_slide = 0

        self.create_variables()
        self.create_interface()

    # ========================================================
    # Variables
    # ========================================================

    def create_variables(self):
        self.lines_per_slide = tk.IntVar(value=4)
        self.include_labels = tk.BooleanVar(value=True)
        self.status_text = tk.StringVar(
            value="Paste lyrics on the left, then click Format Lyrics."
        )

    # ========================================================
    # Interface
    # ========================================================

    def create_interface(self):

        # ----------------------------
        # Top toolbar
        # ----------------------------

        toolbar = ttk.Frame(self.root, padding=8)
        toolbar.pack(fill=tk.X)

        ttk.Button(
            toolbar,
            text="Format Lyrics",
            command=self.format
        ).pack(side=tk.LEFT, padx=4)

        ttk.Button(
            toolbar,
            text="Clear",
            command=self.clear
        ).pack(side=tk.LEFT, padx=4)

        ttk.Button(
            toolbar,
            text="Copy Output",
            command=self.copy_output
        ).pack(side=tk.LEFT, padx=4)

        ttk.Button(
            toolbar,
            text="Export TXT",
            command=self.export_txt
        ).pack(side=tk.LEFT, padx=4)

        ttk.Button(
            toolbar,
            text="Open TXT",
            command=self.open_txt
        ).pack(side=tk.LEFT, padx=4)

        ttk.Separator(
            toolbar,
            orient=tk.VERTICAL
        ).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        ttk.Label(
            toolbar,
            text="Lines per slide:"
        ).pack(side=tk.LEFT)

        lines_box = ttk.Combobox(
            toolbar,
            textvariable=self.lines_per_slide,
            values=[2, 3, 4, 5, 6],
            width=5,
            state="readonly"
        )
        lines_box.pack(side=tk.LEFT, padx=5)

        ttk.Checkbutton(
            toolbar,
            text="Include section labels",
            variable=self.include_labels
        ).pack(side=tk.LEFT, padx=15)

        # ----------------------------
        # Main area
        # ----------------------------

        main = ttk.PanedWindow(
            self.root,
            orient=tk.HORIZONTAL
        )

        main.pack(
            fill=tk.BOTH,
            expand=True,
            padx=8,
            pady=5
        )

        # ====================================================
        # LEFT: Input
        # ====================================================

        input_frame = ttk.Frame(main)

        ttk.Label(
            input_frame,
            text="Original Lyrics",
            font=("Segoe UI", 12, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))

        self.input_text = tk.Text(
            input_frame,
            wrap=tk.WORD,
            font=("Consolas", 11),
            undo=True
        )

        input_scroll = ttk.Scrollbar(
            input_frame,
            orient=tk.VERTICAL,
            command=self.input_text.yview
        )

        self.input_text.configure(
            yscrollcommand=input_scroll.set
        )

        input_scroll.pack(
            side=tk.RIGHT,
            fill=tk.Y
        )

        self.input_text.pack(
            fill=tk.BOTH,
            expand=True
        )

        main.add(input_frame, weight=1)

        # ====================================================
        # MIDDLE: Output
        # ====================================================

        output_frame = ttk.Frame(main)

        ttk.Label(
            output_frame,
            text="EasyWorship Output",
            font=("Segoe UI", 12, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))

        self.output_text = tk.Text(
            output_frame,
            wrap=tk.WORD,
            font=("Consolas", 11),
            undo=True
        )

        output_scroll = ttk.Scrollbar(
            output_frame,
            orient=tk.VERTICAL,
            command=self.output_text.yview
        )

        self.output_text.configure(
            yscrollcommand=output_scroll.set
        )

        output_scroll.pack(
            side=tk.RIGHT,
            fill=tk.Y
        )

        self.output_text.pack(
            fill=tk.BOTH,
            expand=True
        )

        main.add(output_frame, weight=1)

        # ====================================================
        # RIGHT: Slide Preview
        # ====================================================

        preview_frame = ttk.Frame(main)

        ttk.Label(
            preview_frame,
            text="Slide Preview",
            font=("Segoe UI", 12, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))

        self.slide_number_label = ttk.Label(
            preview_frame,
            text="No slides yet",
            font=("Segoe UI", 10)
        )

        self.slide_number_label.pack(pady=5)

        self.preview = tk.Text(
            preview_frame,
            wrap=tk.WORD,
            font=("Arial", 20),
            bg="#111111",
            fg="white",
            insertbackground="white",
            justify=tk.CENTER
        )

        preview_scroll = ttk.Scrollbar(
            preview_frame,
            orient=tk.VERTICAL,
            command=self.preview.yview
        )

        self.preview.configure(
            yscrollcommand=preview_scroll.set
        )

        preview_scroll.pack(
            side=tk.RIGHT,
            fill=tk.Y
        )

        self.preview.pack(
            fill=tk.BOTH,
            expand=True,
            padx=5
        )

        # Navigation

        navigation = ttk.Frame(preview_frame)
        navigation.pack(fill=tk.X, pady=8)

        ttk.Button(
            navigation,
            text="◀ Previous",
            command=self.previous_slide
        ).pack(side=tk.LEFT, expand=True, padx=3)

        ttk.Button(
            navigation,
            text="Next ▶",
            command=self.next_slide
        ).pack(side=tk.LEFT, expand=True, padx=3)

        main.add(preview_frame, weight=1)

        # ----------------------------
        # Status bar
        # ----------------------------

        status = ttk.Label(
            self.root,
            textvariable=self.status_text,
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=5
        )

        status.pack(
            fill=tk.X,
            side=tk.BOTTOM
        )

    # ========================================================
    # Formatting
    # ========================================================

    def format(self):

        text = self.input_text.get(
            "1.0",
            tk.END
        ).strip()

        if not text:
            messagebox.showwarning(
                "No lyrics",
                "Please paste some lyrics first."
            )
            return

        output, slides = format_lyrics(
            text,
            self.lines_per_slide.get(),
            self.include_labels.get()
        )

        self.slides = slides
        self.current_slide = 0

        self.output_text.delete(
            "1.0",
            tk.END
        )

        self.output_text.insert(
            "1.0",
            output
        )

        self.show_slide()

        self.status_text.set(
            f"Formatted {len(slides)} slides."
        )

    # ========================================================
    # Preview
    # ========================================================

    def show_slide(self):

        self.preview.delete(
            "1.0",
            tk.END
        )

        if not self.slides:
            self.slide_number_label.config(
                text="No slides yet"
            )
            return

        slide = self.slides[
            self.current_slide
        ]

        text = "\n".join(slide["lines"])

        if slide["section"]:
            text = (
                slide["section"]
                + "\n\n"
                + text
            )

        self.preview.insert(
            "1.0",
            text
        )

        self.slide_number_label.config(
            text=(
                f"Slide {self.current_slide + 1}"
                f" of {len(self.slides)}"
            )
        )

    def next_slide(self):

        if not self.slides:
            return

        if self.current_slide < len(self.slides) - 1:
            self.current_slide += 1
            self.show_slide()

    def previous_slide(self):

        if not self.slides:
            return

        if self.current_slide > 0:
            self.current_slide -= 1
            self.show_slide()

    # ========================================================
    # File operations
    # ========================================================

    def export_txt(self):

        text = self.output_text.get(
            "1.0",
            tk.END
        ).strip()

        if not text:
            messagebox.showwarning(
                "Nothing to export",
                "Format the lyrics first."
            )
            return

        filename = filedialog.asksaveasfilename(
            title="Export for EasyWorship 2009",
            defaultextension=".txt",
            filetypes=[
                (
                    "Text Files",
                    "*.txt"
                ),
                (
                    "All Files",
                    "*.*"
                )
            ]
        )

        if not filename:
            return

        try:
            with open(
                filename,
                "w",
                encoding="utf-8-sig"
            ) as file:

                file.write(text)

            messagebox.showinfo(
                "Export complete",
                "The lyrics were exported successfully."
            )

        except Exception as error:

            messagebox.showerror(
                "Export error",
                str(error)
            )

    def open_txt(self):

        filename = filedialog.askopenfilename(
            title="Open Lyrics",
            filetypes=[
                (
                    "Text Files",
                    "*.txt"
                ),
                (
                    "All Files",
                    "*.*"
                )
            ]
        )

        if not filename:
            return

        try:

            with open(
                filename,
                "r",
                encoding="utf-8-sig"
            ) as file:

                text = file.read()

            self.input_text.delete(
                "1.0",
                tk.END
            )

            self.input_text.insert(
                "1.0",
                text
            )

            self.status_text.set(
                f"Loaded: {filename}"
            )

        except Exception as error:

            messagebox.showerror(
                "Open error",
                str(error)
            )

    def copy_output(self):

        text = self.output_text.get(
            "1.0",
            tk.END
        ).strip()

        if not text:
            messagebox.showwarning(
                "Nothing to copy",
                "Format the lyrics first."
            )
            return

        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()

        self.status_text.set(
            "Formatted lyrics copied to clipboard."
        )

    def clear(self):

        self.input_text.delete(
            "1.0",
            tk.END
        )

        self.output_text.delete(
            "1.0",
            tk.END
        )

        self.preview.delete(
            "1.0",
            tk.END
        )

        self.slides = []
        self.current_slide = 0

        self.slide_number_label.config(
            text="No slides yet"
        )

        self.status_text.set(
            "Ready."
        )


# ============================================================
# Run application
# ============================================================

if __name__ == "__main__":

    root = tk.Tk()

    # Windows-friendly default font
    try:
        root.option_add(
            "*Font",
            "Segoe UI 10"
        )
    except Exception:
        pass

    app = LyricsFormatterApp(root)

    root.mainloop()