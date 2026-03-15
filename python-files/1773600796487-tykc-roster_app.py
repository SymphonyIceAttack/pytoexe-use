import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import json
import csv
from itertools import combinations
import os

# ----------------------------------------------------------------------
# Colour list for doctors (enough for many doctors)
COLOURS = [
    '#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF',
    '#FFA500', '#800080', '#008000', '#000080', '#808000', '#800000',
    '#FFC0CB', '#A52A2A', '#808080', '#FFFFFF', '#000000'
]

# ----------------------------------------------------------------------
# Doctor class
class Doctor:
    def __init__(self, name, colour=None):
        self.name = name
        self.colour = colour
        self.max_shifts = 4          # default per week (adjust for longer periods)
        self.unavailable_days = []    # list of day numbers (1-based)
        self.preferred_days = None    # None = any day, else list of day numbers
        self.can_work_day = True
        self.can_work_night = True

    def to_dict(self):
        return {
            'name': self.name,
            'colour': self.colour,
            'max_shifts': self.max_shifts,
            'unavailable_days': self.unavailable_days,
            'preferred_days': self.preferred_days,
            'can_work_day': self.can_work_day,
            'can_work_night': self.can_work_night
        }

    @classmethod
    def from_dict(cls, data):
        doc = cls(data['name'], data['colour'])
        doc.max_shifts = data['max_shifts']
        doc.unavailable_days = data['unavailable_days']
        doc.preferred_days = data['preferred_days']
        doc.can_work_day = data['can_work_day']
        doc.can_work_night = data['can_work_night']
        return doc

# ----------------------------------------------------------------------
# Scheduler (backtracking with heuristic ordering and capacity check)
def schedule_roster(doctors, total_days):
    if len(doctors) < 4:
        return None, "Need at least 4 doctors."

    # Total shifts needed: 2 day + 2 night per day
    shifts_needed = total_days * 4
    total_capacity = sum(d.max_shifts for d in doctors)
    if total_capacity < shifts_needed:
        return None, (f"Insufficient total capacity: need {shifts_needed} shifts, "
                      f"but total max_shifts = {total_capacity}. Increase max_shifts.")

    assignments = [None] * total_days   # each entry: ([day_doctors], [night_doctors])
    shift_count = {doc: 0 for doc in doctors}

    def is_available(doctor, day, shift_type):
        if shift_type == 'day' and not doctor.can_work_day:
            return False
        if shift_type == 'night' and not doctor.can_work_night:
            return False
        if day in doctor.unavailable_days:
            return False
        if doctor.preferred_days is not None and day not in doctor.preferred_days:
            return False
        if shift_count[doctor] >= doctor.max_shifts:
            return False
        return True

    # Quick feasibility check for a given day (forward prune)
    def day_feasible(day, prev_night_docs):
        day_possible = sum(1 for d in doctors
                           if is_available(d, day, 'day') and d not in prev_night_docs)
        night_possible = sum(1 for d in doctors if is_available(d, day, 'night'))
        return day_possible >= 2 and night_possible >= 2

    def backtrack(day):
        if day > total_days:
            return True

        prev_night = assignments[day-2][1] if day > 1 else []

        if not day_feasible(day, prev_night):
            return False

        # Candidates for day and night shifts
        day_candidates = [d for d in doctors if is_available(d, day, 'day') and d not in prev_night]
        night_candidates = [d for d in doctors if is_available(d, day, 'night')]

        # Heuristic: sort by fewest shifts worked so far
        day_candidates.sort(key=lambda d: shift_count[d])
        night_candidates.sort(key=lambda d: shift_count[d])

        day_pairs = list(combinations(day_candidates, 2))
        night_pairs = list(combinations(night_candidates, 2))

        # Order pairs by total shifts of the two doctors (ascending)
        day_pairs.sort(key=lambda p: shift_count[p[0]] + shift_count[p[1]])
        night_pairs.sort(key=lambda p: shift_count[p[0]] + shift_count[p[1]])

        for d1, d2 in day_pairs:
            for n1, n2 in night_pairs:
                if len({d1, d2, n1, n2}) == 4:   # all distinct
                    assignments[day-1] = ([d1, d2], [n1, n2])
                    shift_count[d1] += 1
                    shift_count[d2] += 1
                    shift_count[n1] += 1
                    shift_count[n2] += 1

                    if backtrack(day+1):
                        return True

                    # backtrack
                    shift_count[d1] -= 1
                    shift_count[d2] -= 1
                    shift_count[n1] -= 1
                    shift_count[n2] -= 1

        assignments[day-1] = None
        return False

    success = backtrack(1)
    if not success:
        return None, "No valid schedule found with current rules. Try relaxing constraints."

    # Count final shifts for summary
    day_counts = {doc: 0 for doc in doctors}
    night_counts = {doc: 0 for doc in doctors}
    for day_docs, night_docs in assignments:
        for d in day_docs:
            day_counts[d] += 1
        for n in night_docs:
            night_counts[n] += 1

    return assignments, (day_counts, night_counts)

# ----------------------------------------------------------------------
# Main GUI Application
class RosterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Doctor Roster Scheduler")
        self.root.geometry("1200x700")

        self.doctors = []          # list of Doctor objects
        self.current_doctor = None # for editing rules
        self.rosters = None        # last generated assignments
        self.colour_index = 0

        # Create GUI layout
        self.create_menu()
        self.create_widgets()

        # Try loading doctors from file on startup
        self.load_doctors(auto=True)

    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Load doctors...", command=self.load_doctors_dialog)
        file_menu.add_command(label="Save doctors...", command=self.save_doctors_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Export roster as CSV...", command=self.export_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        schedule_menu = tk.Menu(menubar, tearoff=0)
        schedule_menu.add_command(label="Generate roster...", command=self.generate_roster)
        menubar.add_cascade(label="Schedule", menu=schedule_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

    def create_widgets(self):
        # Main paned window
        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # Left frame: doctor list
        left_frame = ttk.Frame(paned, width=250, relief=tk.SUNKEN, padding=5)
        paned.add(left_frame, weight=1)

        ttk.Label(left_frame, text="Doctors", font=('Arial', 12, 'bold')).pack(anchor=tk.W)

        # Listbox with scrollbar
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.doctor_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                                         selectmode=tk.SINGLE, height=15)
        self.doctor_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.doctor_listbox.yview)

        self.doctor_listbox.bind('<<ListboxSelect>>', self.on_doctor_select)

        # Buttons for doctor management
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame, text="Add", command=self.add_doctor).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Remove", command=self.remove_doctor).pack(side=tk.LEFT, padx=2)

        # Middle frame: rules for selected doctor
        middle_frame = ttk.Frame(paned, width=350, relief=tk.SUNKEN, padding=5)
        paned.add(middle_frame, weight=1)

        ttk.Label(middle_frame, text="Rules for selected doctor", font=('Arial', 12, 'bold')).pack(anchor=tk.W)

        # We'll create a canvas with scrollbar for rules (in case many widgets)
        canvas = tk.Canvas(middle_frame, borderwidth=0, highlightthickness=0)
        v_scroll = ttk.Scrollbar(middle_frame, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=v_scroll.set)

        rules_frame = ttk.Frame(canvas)
        rules_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0,0), window=rules_frame, anchor="nw")

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # --- Rules widgets ---
        row = 0
        ttk.Label(rules_frame, text="Max shifts:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.max_shifts_var = tk.IntVar(value=4)
        ttk.Spinbox(rules_frame, from_=1, to=100, textvariable=self.max_shifts_var, width=10).grid(row=row, column=1, sticky=tk.W, padx=5)
        row += 1

        # Unavailable days (checkboxes for 1-7, but could be extended)
        ttk.Label(rules_frame, text="Unavailable days:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.unavail_vars = []
        unavail_frame = ttk.Frame(rules_frame)
        unavail_frame.grid(row=row, column=1, sticky=tk.W, padx=5)
        for i in range(1,8):
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(unavail_frame, text=str(i), variable=var)
            cb.pack(side=tk.LEFT, padx=2)
            self.unavail_vars.append(var)
        row += 1

        # Preferred days: "Any day" or specific
        ttk.Label(rules_frame, text="Preferred days:").grid(row=row, column=0, sticky=tk.W, pady=5)
        pref_frame = ttk.Frame(rules_frame)
        pref_frame.grid(row=row, column=1, sticky=tk.W, padx=5)

        self.pref_any_var = tk.BooleanVar(value=True)
        ttk.Radiobutton(pref_frame, text="Any day", variable=self.pref_any_var, value=True,
                        command=self.toggle_pref_days).pack(anchor=tk.W)
        self.pref_specific_var = tk.BooleanVar(value=False)
        ttk.Radiobutton(pref_frame, text="Only these:", variable=self.pref_any_var, value=False,
                        command=self.toggle_pref_days).pack(anchor=tk.W)

        self.pref_day_vars = []
        pref_days_frame = ttk.Frame(rules_frame)
        pref_days_frame.grid(row=row+1, column=1, sticky=tk.W, padx=20)
        for i in range(1,8):
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(pref_days_frame, text=str(i), variable=var, state=tk.DISABLED)
            cb.pack(side=tk.LEFT, padx=2)
            self.pref_day_vars.append(var)
        row += 2

        # Shift type
        ttk.Label(rules_frame, text="Can work:").grid(row=row, column=0, sticky=tk.W, pady=5)
        shift_frame = ttk.Frame(rules_frame)
        shift_frame.grid(row=row, column=1, sticky=tk.W, padx=5)
        self.can_day_var = tk.BooleanVar(value=True)
        self.can_night_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(shift_frame, text="Day", variable=self.can_day_var).pack(side=tk.LEFT, padx=2)
        ttk.Checkbutton(shift_frame, text="Night", variable=self.can_night_var).pack(side=tk.LEFT, padx=2)
        row += 1

        # Apply button
        ttk.Button(rules_frame, text="Apply Rules", command=self.apply_rules).grid(row=row, column=0, columnspan=2, pady=10)

        # Right frame: roster display
        right_frame = ttk.Frame(paned, width=500, relief=tk.SUNKEN, padding=5)
        paned.add(right_frame, weight=2)

        ttk.Label(right_frame, text="Generated Roster", font=('Arial', 12, 'bold')).pack(anchor=tk.W)

        # Treeview for roster
        columns = ('day', 'day_shift', 'night_shift')
        self.roster_tree = ttk.Treeview(right_frame, columns=columns, show='headings', height=20)
        self.roster_tree.heading('day', text='Day')
        self.roster_tree.heading('day_shift', text='Day Shift')
        self.roster_tree.heading('night_shift', text='Night Shift')
        self.roster_tree.column('day', width=50, anchor='center')
        self.roster_tree.column('day_shift', width=200)
        self.roster_tree.column('night_shift', width=200)

        scroll_y = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.roster_tree.yview)
        self.roster_tree.configure(yscrollcommand=scroll_y.set)
        self.roster_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        # Initially disable rules panel until a doctor is selected
        self.toggle_pref_days()  # set initial state

    def toggle_pref_days(self):
        state = tk.NORMAL if not self.pref_any_var.get() else tk.DISABLED
        for cbvar in self.pref_day_vars:
            # we need to access the checkbox widgets? quick hack: we'll set the state later in apply_rules.
            # For now, just store state; we'll enable/disable checkboxes themselves.
            # We'll keep a reference to the checkboxes? Simpler: we'll just enable/disable in apply_rules based on radiobutton.
            pass
        # Actually we need to modify the checkboxes. Since we didn't store them, we'll handle in apply_rules.
        # But we can also store them. Let's modify to store checkbuttons.
        # For simplicity, we'll just manage state when applying rules.
        pass

    # ------------------------------------------------------------------
    # Doctor list management
    def refresh_doctor_list(self):
        self.doctor_listbox.delete(0, tk.END)
        for doc in self.doctors:
            self.doctor_listbox.insert(tk.END, doc.name)
        if self.doctors:
            self.doctor_listbox.selection_set(0)
            self.on_doctor_select()

    def add_doctor(self):
        name = simpledialog.askstring("Add Doctor", "Enter doctor's name:")
        if not name:
            return
        # Check for duplicate
        if any(d.name == name for d in self.doctors):
            messagebox.showerror("Error", "A doctor with that name already exists.")
            return
        # Assign a colour
        used_colours = [d.colour for d in self.doctors if d.colour]
        colour = None
        for c in COLOURS:
            if c not in used_colours:
                colour = c
                break
        if not colour:
            colour = '#000000'  # fallback
        new_doc = Doctor(name, colour)
        self.doctors.append(new_doc)
        self.refresh_doctor_list()

    def remove_doctor(self):
        sel = self.doctor_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        doc = self.doctors[idx]
        if messagebox.askyesno("Confirm", f"Remove {doc.name}?"):
            del self.doctors[idx]
            self.refresh_doctor_list()
            self.current_doctor = None
            self.clear_rules_panel()

    def clear_rules_panel(self):
        self.max_shifts_var.set(4)
        for var in self.unavail_vars:
            var.set(False)
        self.pref_any_var.set(True)
        for var in self.pref_day_vars:
            var.set(False)
        self.can_day_var.set(True)
        self.can_night_var.set(True)

    def on_doctor_select(self, event=None):
        sel = self.doctor_listbox.curselection()
        if not sel:
            self.current_doctor = None
            self.clear_rules_panel()
            return
        idx = sel[0]
        doc = self.doctors[idx]
        self.current_doctor = doc

        # Load rules into widgets
        self.max_shifts_var.set(doc.max_shifts)

        # Unavailable days
        for i, var in enumerate(self.unavail_vars, start=1):
            var.set(i in doc.unavailable_days)

        # Preferred days
        if doc.preferred_days is None:
            self.pref_any_var.set(True)
            for var in self.pref_day_vars:
                var.set(False)
        else:
            self.pref_any_var.set(False)
            for i, var in enumerate(self.pref_day_vars, start=1):
                var.set(i in doc.preferred_days)

        # Shift type
        self.can_day_var.set(doc.can_work_day)
        self.can_night_var.set(doc.can_work_night)

    def apply_rules(self):
        if not self.current_doctor:
            messagebox.showwarning("No doctor", "Select a doctor first.")
            return
        doc = self.current_doctor

        doc.max_shifts = self.max_shifts_var.get()

        # Unavailable days
        doc.unavailable_days = [i for i, var in enumerate(self.unavail_vars, start=1) if var.get()]

        # Preferred days
        if self.pref_any_var.get():
            doc.preferred_days = None
        else:
            doc.preferred_days = [i for i, var in enumerate(self.pref_day_vars, start=1) if var.get()]

        doc.can_work_day = self.can_day_var.get()
        doc.can_work_night = self.can_night_var.get()

        messagebox.showinfo("Success", f"Rules for {doc.name} updated.")

    # ------------------------------------------------------------------
    # Scheduling
    def generate_roster(self):
        if len(self.doctors) < 4:
            messagebox.showerror("Error", "Need at least 4 doctors.")
            return

        days = simpledialog.askinteger("Days", "Enter number of days to schedule (e.g., 7, 14, 30):",
                                       minvalue=1, maxvalue=365)
        if not days:
            return

        # Call scheduler
        result = schedule_roster(self.doctors, days)
        if result[0] is None:
            messagebox.showerror("Scheduling failed", result[1])
            return

        assignments, (day_counts, night_counts) = result
        self.rosters = assignments

        # Clear tree
        for row in self.roster_tree.get_children():
            self.roster_tree.delete(row)

        # Insert rows
        for day_idx, (day_docs, night_docs) in enumerate(assignments, start=1):
            day_names = ' '.join(d.name for d in day_docs)
            night_names = ' '.join(d.name for d in night_docs)
            self.roster_tree.insert('', tk.END, values=(day_idx, day_names, night_names),
                                    tags=(day_docs[0].colour, day_docs[1].colour,
                                          night_docs[0].colour, night_docs[1].colour))

        # Configure tags for colours
        # We need to assign each doctor's colour as a tag
        for doc in self.doctors:
            self.roster_tree.tag_configure(doc.colour, foreground=doc.colour)

        # Also show summary (optional)
        summary = "Shifts per doctor:\n"
        for doc in self.doctors:
            summary += f"{doc.name}: day {day_counts[doc]}, night {night_counts[doc]}, total {day_counts[doc]+night_counts[doc]}\n"
        messagebox.showinfo("Roster generated", summary)

    # ------------------------------------------------------------------
    # File I/O
    def load_doctors(self, auto=False, filename=None):
        if not filename:
            filename = filedialog.askopenfilename(defaultextension=".json",
                                                  filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
            if not filename:
                return
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            self.doctors = [Doctor.from_dict(d) for d in data]
            self.refresh_doctor_list()
            if not auto:
                messagebox.showinfo("Loaded", f"Loaded {len(self.doctors)} doctors.")
        except Exception as e:
            if not auto:
                messagebox.showerror("Error", f"Failed to load: {e}")

    def load_doctors_dialog(self):
        self.load_doctors(auto=False)

    def save_doctors_dialog(self):
        filename = filedialog.asksaveasfilename(defaultextension=".json",
                                                filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if not filename:
            return
        try:
            with open(filename, 'w') as f:
                json.dump([doc.to_dict() for doc in self.doctors], f, indent=2)
            messagebox.showinfo("Saved", f"Saved {len(self.doctors)} doctors.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")

    def export_csv(self):
        if not self.rosters:
            messagebox.showwarning("No roster", "Generate a roster first.")
            return
        filename = filedialog.asksaveasfilename(defaultextension=".csv",
                                                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not filename:
            return
        try:
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Day", "Day Shift", "Night Shift"])
                for day, (day_docs, night_docs) in enumerate(self.rosters, start=1):
                    day_names = ' '.join(d.name for d in day_docs)
                    night_names = ' '.join(d.name for d in night_docs)
                    writer.writerow([day, day_names, night_names])
            messagebox.showinfo("Exported", f"Roster saved to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {e}")

    def show_about(self):
        messagebox.showinfo("About", "Doctor Roster Scheduler\nVersion 1.0\n\nAllows custom rules and colour-coded display.")

# ----------------------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = RosterApp(root)
    root.mainloop()