import json
import os
import re
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog


DATA_FILE = "video_lists.json"


def parse_duration(text):
    """
    Accepts:
    - HH:MM:SS
    - MM:SS
    - 1h 20m 30s
    - 10m
    - 90s
    - Plain number, treated as minutes
    """
    text = text.strip().lower()

    if not text:
        raise ValueError("Duration cannot be empty.")

    # Colon formats: HH:MM:SS or MM:SS
    if ":" in text:
        parts = text.split(":")

        if not all(part.strip().isdigit() for part in parts):
            raise ValueError("Invalid colon duration format.")

        parts = [int(part) for part in parts]

        if len(parts) == 2:
            minutes, seconds = parts
            return minutes * 60 + seconds

        if len(parts) == 3:
            hours, minutes, seconds = parts
            return hours * 3600 + minutes * 60 + seconds

        raise ValueError("Use MM:SS or HH:MM:SS format.")

    # Formats like 1h 20m 30s
    pattern = r"(\d+(?:\.\d+)?)\s*(h|hr|hrs|hour|hours|m|min|mins|minute|minutes|s|sec|secs|second|seconds)"
    matches = re.findall(pattern, text)

    if matches:
        total_seconds = 0

        for value, unit in matches:
            value = float(value)

            if unit.startswith("h"):
                total_seconds += value * 3600
            elif unit.startswith("m"):
                total_seconds += value * 60
            elif unit.startswith("s"):
                total_seconds += value

        return int(round(total_seconds))

    # Plain number = minutes
    try:
        return int(round(float(text) * 60))
    except ValueError:
        raise ValueError("Invalid duration format.")


def format_duration(seconds):
    seconds = int(round(seconds))

    hours = seconds // 3600
    minutes = seconds % 3600 // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"

    return f"{minutes}:{secs:02d}"


class VideoTimeTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Time Tracker")
        self.root.geometry("850x600")
        self.root.minsize(760, 520)

        self.data = {"lists": {"Default": []}}
        self.current_list_name = "Default"

        self.duration_var = tk.StringVar()
        self.note_var = tk.StringVar()
        self.speed_var = tk.StringVar(value="1.0")
        self.list_name_var = tk.StringVar(value=self.current_list_name)

        self.load_data()
        self.build_ui()
        self.refresh_list_selector()
        self.refresh_table()
        self.update_totals()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def build_ui(self):
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill="both", expand=True)

        # List controls
        list_frame = ttk.LabelFrame(main, text="Video Lists", padding=10)
        list_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(list_frame, text="Current list:").pack(side="left")

        self.list_selector = ttk.Combobox(
            list_frame,
            textvariable=self.list_name_var,
            state="readonly",
            width=30
        )
        self.list_selector.pack(side="left", padx=8)
        self.list_selector.bind("<<ComboboxSelected>>", self.change_list)

        ttk.Button(list_frame, text="New List", command=self.new_list).pack(side="left", padx=4)
        ttk.Button(list_frame, text="Delete List", command=self.delete_list).pack(side="left", padx=4)
        ttk.Button(list_frame, text="Save", command=self.save_data).pack(side="left", padx=4)

        # Input controls
        input_frame = ttk.LabelFrame(main, text="Add or Edit Video", padding=10)
        input_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(input_frame, text="Duration:").grid(row=0, column=0, sticky="w")
        duration_entry = ttk.Entry(input_frame, textvariable=self.duration_var, width=22)
        duration_entry.grid(row=0, column=1, sticky="w", padx=(8, 16))

        ttk.Label(input_frame, text="Note:").grid(row=0, column=2, sticky="w")
        note_entry = ttk.Entry(input_frame, textvariable=self.note_var, width=45)
        note_entry.grid(row=0, column=3, sticky="ew", padx=(8, 16))

        input_frame.columnconfigure(3, weight=1)

        ttk.Button(input_frame, text="Add Video", command=self.add_video).grid(row=0, column=4, padx=4)
        ttk.Button(input_frame, text="Update Selected", command=self.update_selected).grid(row=0, column=5, padx=4)
        ttk.Button(input_frame, text="Clear", command=self.clear_inputs).grid(row=0, column=6, padx=4)

        help_text = (
            "Examples: 12:30, 1:05:20, 10m, 90s, 1h 20m, or plain number like 15 for 15 minutes"
        )
        ttk.Label(input_frame, text=help_text).grid(
            row=1,
            column=0,
            columnspan=7,
            sticky="w",
            pady=(8, 0)
        )

        # Table
        table_frame = ttk.LabelFrame(main, text="Videos", padding=10)
        table_frame.pack(fill="both", expand=True, pady=(0, 10))

        columns = ("duration", "note")
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        self.tree.heading("duration", text="Duration")
        self.tree.heading("note", text="Note")

        self.tree.column("duration", width=140, anchor="center")
        self.tree.column("note", width=560, anchor="w")

        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.bind("<<TreeviewSelect>>", self.on_select_video)

        # Buttons below table
        button_frame = ttk.Frame(main)
        button_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(button_frame, text="Remove Selected", command=self.remove_selected).pack(side="left")
        ttk.Button(button_frame, text="Move Up", command=lambda: self.move_selected(-1)).pack(side="left", padx=6)
        ttk.Button(button_frame, text="Move Down", command=lambda: self.move_selected(1)).pack(side="left")

        # Totals
        totals_frame = ttk.LabelFrame(main, text="Totals", padding=10)
        totals_frame.pack(fill="x")

        ttk.Label(totals_frame, text="Playback speed:").grid(row=0, column=0, sticky="w")

        speed_entry = ttk.Entry(totals_frame, textvariable=self.speed_var, width=10)
        speed_entry.grid(row=0, column=1, sticky="w", padx=(8, 16))
        speed_entry.bind("<KeyRelease>", lambda event: self.update_totals())

        ttk.Label(totals_frame, text="x").grid(row=0, column=2, sticky="w")

        self.total_label = ttk.Label(totals_frame, text="Total video time: 0:00")
        self.total_label.grid(row=1, column=0, columnspan=3, sticky="w", pady=(8, 0))

        self.adjusted_label = ttk.Label(totals_frame, text="Time at selected speed: 0:00")
        self.adjusted_label.grid(row=2, column=0, columnspan=3, sticky="w", pady=(4, 0))

    def get_current_videos(self):
        return self.data["lists"].setdefault(self.current_list_name, [])

    def add_video(self):
        try:
            seconds = parse_duration(self.duration_var.get())
        except ValueError as error:
            messagebox.showerror("Invalid Duration", str(error))
            return

        note = self.note_var.get().strip()

        self.get_current_videos().append({
            "seconds": seconds,
            "note": note
        })

        self.clear_inputs()
        self.refresh_table()
        self.update_totals()

    def update_selected(self):
        selected = self.tree.selection()

        if not selected:
            messagebox.showinfo("No Selection", "Select a video to update.")
            return

        try:
            seconds = parse_duration(self.duration_var.get())
        except ValueError as error:
            messagebox.showerror("Invalid Duration", str(error))
            return

        index = int(selected[0])
        videos = self.get_current_videos()

        videos[index] = {
            "seconds": seconds,
            "note": self.note_var.get().strip()
        }

        self.refresh_table()
        self.tree.selection_set(str(index))
        self.update_totals()

    def remove_selected(self):
        selected = self.tree.selection()

        if not selected:
            messagebox.showinfo("No Selection", "Select a video to remove.")
            return

        index = int(selected[0])
        videos = self.get_current_videos()

        del videos[index]

        self.clear_inputs()
        self.refresh_table()
        self.update_totals()

    def move_selected(self, direction):
        selected = self.tree.selection()

        if not selected:
            messagebox.showinfo("No Selection", "Select a video to move.")
            return

        index = int(selected[0])
        videos = self.get_current_videos()

        new_index = index + direction

        if new_index < 0 or new_index >= len(videos):
            return

        videos[index], videos[new_index] = videos[new_index], videos[index]

        self.refresh_table()
        self.tree.selection_set(str(new_index))
        self.update_totals()

    def on_select_video(self, event=None):
        selected = self.tree.selection()

        if not selected:
            return

        index = int(selected[0])
        video = self.get_current_videos()[index]

        self.duration_var.set(format_duration(video["seconds"]))
        self.note_var.set(video.get("note", ""))

    def clear_inputs(self):
        self.duration_var.set("")
        self.note_var.set("")
        self.tree.selection_remove(self.tree.selection())

    def refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        for index, video in enumerate(self.get_current_videos()):
            self.tree.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    format_duration(video["seconds"]),
                    video.get("note", "")
                )
            )

    def update_totals(self):
        total_seconds = sum(video["seconds"] for video in self.get_current_videos())

        try:
            speed = float(self.speed_var.get())
            if speed <= 0:
                raise ValueError
        except ValueError:
            self.total_label.config(
                text=f"Total video time: {format_duration(total_seconds)}"
            )
            self.adjusted_label.config(
                text="Time at selected speed: enter a valid speed above 0"
            )
            return

        adjusted_seconds = total_seconds / speed

        self.total_label.config(
            text=f"Total video time: {format_duration(total_seconds)}"
        )
        self.adjusted_label.config(
            text=f"Time at {speed:g}x speed: {format_duration(adjusted_seconds)}"
        )

    def new_list(self):
        name = simpledialog.askstring("New List", "Enter a name for the new list:")

        if not name:
            return

        name = name.strip()

        if not name:
            return

        if name in self.data["lists"]:
            messagebox.showerror("List Exists", "A list with that name already exists.")
            return

        self.data["lists"][name] = []
        self.current_list_name = name
        self.list_name_var.set(name)

        self.refresh_list_selector()
        self.refresh_table()
        self.update_totals()

    def delete_list(self):
        if len(self.data["lists"]) <= 1:
            messagebox.showinfo("Cannot Delete", "You must keep at least one list.")
            return

        confirm = messagebox.askyesno(
            "Delete List",
            f"Delete the list '{self.current_list_name}'?"
        )

        if not confirm:
            return

        del self.data["lists"][self.current_list_name]

        self.current_list_name = next(iter(self.data["lists"]))
        self.list_name_var.set(self.current_list_name)

        self.refresh_list_selector()
        self.refresh_table()
        self.update_totals()

    def change_list(self, event=None):
        selected_name = self.list_name_var.get()

        if selected_name not in self.data["lists"]:
            return

        self.current_list_name = selected_name
        self.clear_inputs()
        self.refresh_table()
        self.update_totals()

    def refresh_list_selector(self):
        names = list(self.data["lists"].keys())
        self.list_selector["values"] = names

        if self.current_list_name not in names:
            self.current_list_name = names[0]

        self.list_name_var.set(self.current_list_name)

    def load_data(self):
        if not os.path.exists(DATA_FILE):
            return

        try:
            with open(DATA_FILE, "r", encoding="utf-8") as file:
                loaded = json.load(file)

            if "lists" in loaded and isinstance(loaded["lists"], dict):
                self.data = loaded

                if self.data["lists"]:
                    self.current_list_name = next(iter(self.data["lists"]))
                else:
                    self.data = {"lists": {"Default": []}}
                    self.current_list_name = "Default"

        except Exception:
            messagebox.showwarning(
                "Load Error",
                "Could not load saved video lists. Starting with a blank list."
            )
            self.data = {"lists": {"Default": []}}
            self.current_list_name = "Default"

    def save_data(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as file:
                json.dump(self.data, file, indent=4)

            messagebox.showinfo("Saved", "Your video lists have been saved.")
        except Exception as error:
            messagebox.showerror("Save Error", f"Could not save data:\n{error}")

    def on_close(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as file:
                json.dump(self.data, file, indent=4)
        except Exception:
            pass

        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = VideoTimeTrackerApp(root)
    root.mainloop()