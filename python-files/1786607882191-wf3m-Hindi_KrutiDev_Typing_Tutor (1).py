import tkinter as tk
from tkinter import ttk, messagebox
import time

# ============================================================
# Hindi Kruti Dev / Remington typing tutor
# Physical key -> Hindi Unicode mapping
# The mapping is designed for the common Kruti Dev 010 layout.
# ============================================================

KRUTI = {
    # top number row
    "`":"़", "1":"१", "2":"२", "3":"३", "4":"४", "5":"५", "6":"६",
    "7":"७", "8":"८", "9":"९", "0":"०", "-":"ृ", "=":"्र",

    # q row
    "q":"फ", "w":"ू", "e":"म", "r":"त", "t":"ज", "y":"ल", "u":"न",
    "i":"प", "o":"व", "p":"च", "[":"ख", "]":"द", "\\":"़",

    # home row
    "a":"ं", "s":"े", "d":"क", "f":"ि", "g":"ह", "h":"ी", "j":"र",
    "k":"ा", "l":"स", ";":"य", "'":"श",

    # bottom row
    "z":"र्", "x":"ग", "c":"ब", "v":"अ", "b":"इ", "n":"द", "m":"उ",
    ",":"ए", ".":"ण", "/":"ध",
}

KRUTI_SHIFT = {
    "`":"्", "1":"!", "2":"@", "3":"#", "4":"$", "5":"%", "6":"^",
    "7":"&", "8":"*", "9":"(", "0":")", "-":"ऋ", "=":"त्र",

    "q":"फ", "w":"ऊ", "e":"म्", "r":"त्", "t":"ज्", "y":"ल्",
    "u":"न्", "i":"प्", "o":"व्", "p":"च्", "[":"क्ष", "]":"द्व",
    "\\":"द्य",

    "a":"।", "s":"ै", "d":"क्", "f":"थ्", "g":"ळ", "h":"भ्",
    "j":"श्र", "k":"ज्ञ", "l":"स्", ";":"रू", "'":"ष",

    "z":"र्", "x":"ग्", "c":"ब्", "v":"ट", "b":"ठ", "n":"छ",
    "m":"ड", ",":"ढ", ".":"झ", "/":"घ",
}

PASSAGES = [
    "भारत एक महान देश है। यहाँ अनेक भाषाएँ और संस्कृतियाँ मिलकर हमारी पहचान बनाती हैं।",
    "नियमित अभ्यास से हिंदी टाइपिंग की गति और शुद्धता दोनों बेहतर होती हैं।",
    "समय का सही उपयोग सफलता की पहली सीढ़ी है। हमें प्रतिदिन मेहनत और अनुशासन के साथ अभ्यास करना चाहिए।",
    "हिंदी भाषा हमारी संस्कृति और विचारों को व्यक्त करने का सुंदर माध्यम है। लगातार अभ्यास करने से टाइपिंग में गति और सटीकता आती है।",
]

KEY_ROWS = [
    "`1234567890-=",
    "qwertyuiop[]\\",
    "asdfghjkl;'",
    "zxcvbnm,./",
]

class TypingTutor:
    def __init__(self, root):
        self.root = root
        self.root.title("Hindi Kruti Dev 010 Typing Tutor")
        self.root.geometry("1150x800")
        self.root.minsize(950, 680)

        self.duration = 300
        self.target = ""
        self.raw_keys = []
        self.output = ""
        self.running = False
        self.started_at = 0.0
        self.finished = False

        self.correct = 0
        self.wrong = 0

        self.build_ui()
        self.load_passage(0)
        self.reset()

        root.bind("<KeyPress>", self.on_key)

    def font(self, size, bold=False):
        # DejaVu Sans has broad Unicode support; Windows usually has Noto Sans Devanagari too.
        return ("Noto Sans Devanagari", size, "bold" if bold else "normal")

    def build_ui(self):
        header = ttk.Frame(self.root, padding=12)
        header.pack(fill="x")

        ttk.Label(header, text="हिंदी टाइपिंग ट्यूटर",
                  font=self.font(24, True)).pack(side="left")

        self.time_label = ttk.Label(header, text="समय: 05:00",
                                    font=("Segoe UI", 16, "bold"))
        self.time_label.pack(side="right", padx=12)

        self.acc_label = ttk.Label(header, text="Accuracy: 100%",
                                   font=("Segoe UI", 14))
        self.acc_label.pack(side="right", padx=12)

        self.wpm_label = ttk.Label(header, text="WPM: 0.0",
                                   font=("Segoe UI", 14))
        self.wpm_label.pack(side="right", padx=12)

        controls = ttk.Frame(self.root, padding=(12, 0, 12, 8))
        controls.pack(fill="x")

        ttk.Label(controls, text="पैसेज:", font=self.font(12)).pack(side="left")

        self.passage_var = tk.StringVar(value="पैसेज 1")
        combo = ttk.Combobox(
            controls, textvariable=self.passage_var,
            values=[f"पैसेज {i+1}" for i in range(len(PASSAGES))],
            state="readonly", width=12
        )
        combo.pack(side="left", padx=8)
        combo.bind("<<ComboboxSelected>>", self.change_passage)

        ttk.Button(controls, text="1 मिनट",
                   command=lambda: self.change_duration(60)).pack(side="left", padx=3)
        ttk.Button(controls, text="5 मिनट",
                   command=lambda: self.change_duration(300)).pack(side="left", padx=3)
        ttk.Button(controls, text="10 मिनट",
                   command=lambda: self.change_duration(600)).pack(side="left", padx=3)
        ttk.Button(controls, text="नया टेस्ट",
                   command=self.reset).pack(side="left", padx=10)

        main = ttk.Frame(self.root, padding=12)
        main.pack(fill="both", expand=True)

        ttk.Label(main, text="टाइप करने के लिए:",
                  font=self.font(14, True)).pack(anchor="w")

        self.target_box = tk.Text(
            main, height=5, wrap="word",
            font=self.font(20), padx=12, pady=10
        )
        self.target_box.pack(fill="x", pady=(5, 12))
        self.target_box.configure(state="disabled")

        ttk.Label(main, text="आपका टाइप किया हुआ:",
                  font=self.font(14, True)).pack(anchor="w")

        self.output_box = tk.Text(
            main, height=5, wrap="word",
            font=self.font(20), padx=12, pady=10
        )
        self.output_box.pack(fill="x", pady=(5, 5))
        self.output_box.configure(state="disabled")

        self.status = ttk.Label(
            main,
            text="कीबोर्ड से टाइप करना शुरू करें। नीचे Kruti Dev key mapping देखें।",
            font=self.font(12)
        )
        self.status.pack(anchor="w", pady=5)

        keyboard = ttk.LabelFrame(
            main, text="Kruti Dev 010 / Remington Key Mapping", padding=8
        )
        keyboard.pack(fill="x", pady=(8, 0))

        self.key_widgets = {}
        for row in KEY_ROWS:
            row_frame = ttk.Frame(keyboard)
            row_frame.pack(pady=2)
            for key in row:
                hindi = KRUTI_SHIFT.get(key, "") + "\n" + KRUTI.get(key, key)
                label = tk.Label(
                    row_frame, text=hindi, width=5, height=2,
                    font=self.font(10), relief="raised", bd=1,
                    bg="white"
                )
                label.pack(side="left", padx=2)
                self.key_widgets[key] = label

        space = tk.Label(
            keyboard,
            text="SPACE  =  खाली स्थान",
            font=self.font(11), relief="groove", bd=1, pady=5
        )
        space.pack(fill="x", pady=(5, 0))

    def load_passage(self, index):
        self.target = PASSAGES[index]
        self.target_box.configure(state="normal")
        self.target_box.delete("1.0", "end")
        self.target_box.insert("1.0", self.target)
        self.target_box.configure(state="disabled")

    def change_passage(self, event=None):
        index = self.passage_var.get().split()[-1]
        self.load_passage(int(index) - 1)
        self.reset()

    def change_duration(self, seconds):
        self.duration = seconds
        self.reset()

    def reset(self):
        self.running = False
        self.finished = False
        self.started_at = 0.0
        self.raw_keys = []
        self.output = ""
        self.correct = 0
        self.wrong = 0

        self.output_box.configure(state="normal")
        self.output_box.delete("1.0", "end")
        self.output_box.configure(state="disabled")

        self.update_stats()
        self.time_label.configure(
            text=f"समय: {self.duration // 60:02d}:{self.duration % 60:02d}"
        )
        self.status.configure(
            text="टाइप करना शुरू करें — QWERTY keys Kruti Dev mapping के अनुसार हिंदी में बदलेंगी।"
        )

    def on_key(self, event):
        # Do not process function/system keys.
        if event.keysym in {
            "Shift_L", "Shift_R", "Control_L", "Control_R",
            "Alt_L", "Alt_R", "Caps_Lock", "Tab", "Escape",
            "Left", "Right", "Up", "Down", "Home", "End",
            "Prior", "Next", "Insert", "Delete"
        }:
            if event.keysym == "Escape":
                self.reset()
            return

        if self.finished:
            return "break"

        if not self.running:
            self.running = True
            self.started_at = time.time()
            self.status.configure(text="टेस्ट चल रहा है...")
            self.tick()

        if event.keysym == "BackSpace":
            if self.raw_keys:
                self.raw_keys.pop()
                self.output = self.rebuild_output()
                self.refresh_output()
            return "break"

        if event.keysym == "space":
            self.raw_keys.append(("space", False))
        elif event.keysym == "Return":
            self.raw_keys.append(("return", False))
        elif len(event.char) == 1:
            key = event.char.lower()
            shifted = bool(event.state & 0x0001)
            self.raw_keys.append((key, shifted))
            self.highlight_key(key)

        self.output = self.rebuild_output()
        self.refresh_output()
        self.update_stats()

        if self.output == self.target:
            self.finish("पैसेज पूरा हो गया। बहुत बढ़िया!")
        elif len(self.output) >= len(self.target):
            self.finish("पैसेज पूरा हुआ। परिणाम नीचे दिया गया है।")

        return "break"

    def rebuild_output(self):
        result = ""
        for key, shifted in self.raw_keys:
            if key == "space":
                result += " "
            elif key == "return":
                result += "\n"
            elif shifted:
                result += KRUTI_SHIFT.get(key, key)
            else:
                result += KRUTI.get(key, key)
        return result

    def refresh_output(self):
        self.output_box.configure(state="normal")
        self.output_box.delete("1.0", "end")

        for i, char in enumerate(self.output):
            tag = "correct" if i < len(self.target) and char == self.target[i] else "wrong"
            self.output_box.insert("end", char, tag)

        self.output_box.tag_configure("correct")
        self.output_box.tag_configure("wrong")
        self.output_box.configure(state="disabled")

    def update_stats(self):
        typed = self.output
        if typed:
            n = min(len(typed), len(self.target))
            self.correct = sum(
                1 for i in range(n) if typed[i] == self.target[i]
            )
            self.wrong = len(typed) - self.correct
        else:
            self.correct = 0
            self.wrong = 0

        if self.running:
            elapsed = max(time.time() - self.started_at, 0.1)
        else:
            elapsed = max(time.time() - self.started_at, 0.1) if self.started_at else 0

        minutes = elapsed / 60 if elapsed else 0
        wpm = (len(typed) / 5) / minutes if minutes else 0
        accuracy = (self.correct / len(typed) * 100) if typed else 100

        self.wpm_label.configure(text=f"WPM: {wpm:.1f}")
        self.acc_label.configure(text=f"Accuracy: {accuracy:.1f}%")

    def highlight_key(self, key):
        widget = self.key_widgets.get(key)
        if not widget:
            return
        original = widget.cget("background")
        widget.configure(background="#d9edf7")
        self.root.after(100, lambda: widget.configure(background=original))

    def tick(self):
        if not self.running:
            return

        elapsed = int(time.time() - self.started_at)
        remaining = max(self.duration - elapsed, 0)

        self.time_label.configure(
            text=f"समय: {remaining // 60:02d}:{remaining % 60:02d}"
        )
        self.update_stats()

        if remaining <= 0:
            self.finish("समय समाप्त! आपका typing result तैयार है।")
            return

        self.root.after(250, self.tick)

    def finish(self, message):
        self.running = False
        self.finished = True
        self.update_stats()
        self.status.configure(text=message)

        elapsed = max(time.time() - self.started_at, 0.1)
        minutes = elapsed / 60
        wpm = (len(self.output) / 5) / minutes if minutes else 0
        accuracy = self.correct / len(self.output) * 100 if self.output else 100

        messagebox.showinfo(
            "टेस्ट परिणाम",
            f"टेस्ट समाप्त\n\n"
            f"WPM: {wpm:.1f}\n"
            f"Accuracy: {accuracy:.1f}%\n"
            f"सही: {self.correct}\n"
            f"गलत: {self.wrong}\n"
            f"कुल टाइप: {len(self.output)}"
        )

if __name__ == "__main__":
    root = tk.Tk()
    TypingTutor(root)
    root.mainloop()
