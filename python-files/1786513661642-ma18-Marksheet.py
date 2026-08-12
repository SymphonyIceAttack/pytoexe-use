import tkinter as tk
from tkinter import ttk, messagebox
from decimal import Decimal, InvalidOperation


# ============================================================
# CA FOUNDATION MARKSHEET
# Based on ICAI Foundation examination structure
# ============================================================

PAPER_NAMES = [
    "Paper 1 - Accounting",
    "Paper 2 - Business Laws",
    "Paper 3 - Quantitative Aptitude",
    "Paper 4 - Business Economics"
]

MAX_MARKS = 100
NEGATIVE_MARKING = Decimal("0.25")


class CAMarksheet:
    def __init__(self, root):
        self.root = root
        self.root.title("CA Foundation Examination Marksheet")
        self.root.geometry("900x700")
        self.root.resizable(False, False)

        self.create_variables()
        self.create_interface()

    # --------------------------------------------------------
    # Variables
    # --------------------------------------------------------
    def create_variables(self):

        self.name_var = tk.StringVar()
        self.roll_var = tk.StringVar()
        self.reg_var = tk.StringVar()
        self.attempt_var = tk.StringVar(value="May 2026")

        # Subjective papers
        self.p1_var = tk.StringVar()
        self.p2_var = tk.StringVar()

        # Objective papers
        self.p3_correct = tk.StringVar()
        self.p3_wrong = tk.StringVar()
        self.p3_unattempted = tk.StringVar()

        self.p4_correct = tk.StringVar()
        self.p4_wrong = tk.StringVar()
        self.p4_unattempted = tk.StringVar()

    # --------------------------------------------------------
    # Interface
    # --------------------------------------------------------
    def create_interface(self):

        title = tk.Label(
            self.root,
            text="CA FOUNDATION EXAMINATION MARKSHEET",
            font=("Arial", 20, "bold"),
            fg="#17365D"
        )
        title.pack(pady=15)

        subtitle = tk.Label(
            self.root,
            text="Student Marks Entry & Result Calculator",
            font=("Arial", 11)
        )
        subtitle.pack()

        # ----------------------------------------------------
        # Student Details
        # ----------------------------------------------------
        details = ttk.LabelFrame(
            self.root,
            text="Student Details",
            padding=15
        )
        details.pack(fill="x", padx=25, pady=15)

        ttk.Label(details, text="Student Name:").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        ttk.Entry(
            details,
            textvariable=self.name_var,
            width=35
        ).grid(row=0, column=1, padx=5)

        ttk.Label(details, text="Roll Number:").grid(
            row=0, column=2, sticky="w", padx=5
        )
        ttk.Entry(
            details,
            textvariable=self.roll_var,
            width=20
        ).grid(row=0, column=3, padx=5)

        ttk.Label(details, text="Registration Number:").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        ttk.Entry(
            details,
            textvariable=self.reg_var,
            width=35
        ).grid(row=1, column=1, padx=5)

        ttk.Label(details, text="Examination:").grid(
            row=1, column=2, sticky="w", padx=5
        )

        exam_box = ttk.Combobox(
            details,
            textvariable=self.attempt_var,
            values=[
                "January 2026",
                "May 2026",
                "September 2026"
            ],
            state="readonly",
            width=17
        )
        exam_box.grid(row=1, column=3, padx=5)

        # ----------------------------------------------------
        # Marks Entry
        # ----------------------------------------------------
        marks_frame = ttk.LabelFrame(
            self.root,
            text="Marks / Question-wise Data Entry",
            padding=15
        )
        marks_frame.pack(fill="x", padx=25, pady=5)

        headers = [
            "Paper",
            "Type",
            "Data Entry",
            "Calculated Marks"
        ]

        for col, header in enumerate(headers):
            ttk.Label(
                marks_frame,
                text=header,
                font=("Arial", 10, "bold")
            ).grid(
                row=0,
                column=col,
                padx=10,
                pady=5
            )

        # Paper 1
        ttk.Label(
            marks_frame,
            text=PAPER_NAMES[0]
        ).grid(row=1, column=0, sticky="w", padx=10, pady=8)

        ttk.Label(
            marks_frame,
            text="Subjective"
        ).grid(row=1, column=1)

        ttk.Entry(
            marks_frame,
            textvariable=self.p1_var,
            width=15
        ).grid(row=1, column=2)

        ttk.Label(
            marks_frame,
            text="Enter marks / 100"
        ).grid(row=1, column=3)

        # Paper 2
        ttk.Label(
            marks_frame,
            text=PAPER_NAMES[1]
        ).grid(row=2, column=0, sticky="w", padx=10, pady=8)

        ttk.Label(
            marks_frame,
            text="Subjective"
        ).grid(row=2, column=1)

        ttk.Entry(
            marks_frame,
            textvariable=self.p2_var,
            width=15
        ).grid(row=2, column=2)

        ttk.Label(
            marks_frame,
            text="Enter marks / 100"
        ).grid(row=2, column=3)

        # Paper 3
        self.create_objective_row(
            marks_frame,
            row=3,
            paper=PAPER_NAMES[2],
            correct=self.p3_correct,
            wrong=self.p3_wrong,
            unattempted=self.p3_unattempted
        )

        # Paper 4
        self.create_objective_row(
            marks_frame,
            row=4,
            paper=PAPER_NAMES[3],
            correct=self.p4_correct,
            wrong=self.p4_wrong,
            unattempted=self.p4_unattempted
        )

        # ----------------------------------------------------
        # Rules
        # ----------------------------------------------------
        rules = ttk.LabelFrame(
            self.root,
            text="Validation Rules",
            padding=10
        )
        rules.pack(fill="x", padx=25, pady=10)

        rule_text = (
            "• Each paper: 100 marks\n"
            "• Papers 1 & 2: Subjective marks entered directly\n"
            "• Papers 3 & 4: Correct = +1, Wrong = −0.25, Unattempted = 0\n"
            "• Minimum 40 marks in EACH paper\n"
            "• Minimum 200 marks out of 400 overall"
        )

        ttk.Label(
            rules,
            text=rule_text,
            justify="left"
        ).pack(anchor="w")

        # ----------------------------------------------------
        # Buttons
        # ----------------------------------------------------
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)

        ttk.Button(
            button_frame,
            text="Calculate Result",
            command=self.calculate_result
        ).grid(row=0, column=0, padx=10)

        ttk.Button(
            button_frame,
            text="Clear",
            command=self.clear_form
        ).grid(row=0, column=1, padx=10)

        # ----------------------------------------------------
        # Result
        # ----------------------------------------------------
        self.result_label = tk.Label(
            self.root,
            text="",
            font=("Arial", 16, "bold")
        )
        self.result_label.pack(pady=10)

    # --------------------------------------------------------
    # Objective paper row
    # --------------------------------------------------------
    def create_objective_row(
        self,
        parent,
        row,
        paper,
        correct,
        wrong,
        unattempted
    ):

        ttk.Label(
            parent,
            text=paper
        ).grid(
            row=row,
            column=0,
            sticky="w",
            padx=10,
            pady=8
        )

        ttk.Label(
            parent,
            text="Objective"
        ).grid(row=row, column=1)

        frame = tk.Frame(parent)
        frame.grid(row=row, column=2, columnspan=2)

        ttk.Label(frame, text="Correct").grid(row=0, column=0)
        ttk.Entry(
            frame,
            textvariable=correct,
            width=8
        ).grid(row=1, column=0, padx=4)

        ttk.Label(frame, text="Wrong").grid(row=0, column=1)
        ttk.Entry(
            frame,
            textvariable=wrong,
            width=8
        ).grid(row=1, column=1, padx=4)

        ttk.Label(frame, text="Unattempted").grid(row=0, column=2)
        ttk.Entry(
            frame,
            textvariable=unattempted,
            width=8
        ).grid(row=1, column=2, padx=4)

    # --------------------------------------------------------
    # Validation: integer
    # --------------------------------------------------------
    def get_non_negative_int(self, value, field_name):

        if value.strip() == "":
            raise ValueError(f"{field_name} cannot be blank.")

        try:
            number = int(value)
        except ValueError:
            raise ValueError(
                f"{field_name} must be a whole number."
            )

        if number < 0:
            raise ValueError(
                f"{field_name} cannot be negative."
            )

        return number

    # --------------------------------------------------------
    # Validation: subjective marks
    # --------------------------------------------------------
    def get_subjective_marks(self, value, paper_name):

        if value.strip() == "":
            raise ValueError(
                f"{paper_name} marks cannot be blank."
            )

        try:
            marks = Decimal(value)
        except InvalidOperation:
            raise ValueError(
                f"{paper_name} marks must be numeric."
            )

        if marks < 0 or marks > 100:
            raise ValueError(
                f"{paper_name} marks must be between 0 and 100."
            )

        return marks

    # --------------------------------------------------------
    # Calculate objective paper
    # --------------------------------------------------------
    def calculate_objective(
        self,
        correct,
        wrong,
        unattempted,
        paper_name
    ):

        correct = self.get_non_negative_int(
            correct,
            f"{paper_name} Correct Answers"
        )

        wrong = self.get_non_negative_int(
            wrong,
            f"{paper_name} Wrong Answers"
        )

        unattempted = self.get_non_negative_int(
            unattempted,
            f"{paper_name} Unattempted Questions"
        )

        total_questions = correct + wrong + unattempted

        # Foundation objective paper assumed as
        # 100 questions / 100 marks.
        if total_questions != 100:
            raise ValueError(
                f"{paper_name}: Correct + Wrong + "
                f"Unattempted must equal 100."
            )

        marks = (
            Decimal(correct)
            - Decimal(wrong) * NEGATIVE_MARKING
        )

        # Prevent a negative final paper score.
        marks = max(Decimal("0"), marks)

        # Marks cannot exceed 100.
        marks = min(Decimal("100"), marks)

        return marks

    # --------------------------------------------------------
    # Calculate result
    # --------------------------------------------------------
    def calculate_result(self):

        try:
            # Student details
            name = self.name_var.get().strip()
            roll = self.roll_var.get().strip()
            registration = self.reg_var.get().strip()

            if not name:
                raise ValueError("Student Name is required.")

            if not roll:
                raise ValueError("Roll Number is required.")

            if not registration:
                raise ValueError(
                    "Registration Number is required."
                )

            # Subjective
            p1 = self.get_subjective_marks(
                self.p1_var.get(),
                "Paper 1"
            )

            p2 = self.get_subjective_marks(
                self.p2_var.get(),
                "Paper 2"
            )

            # Objective
            p3 = self.calculate_objective(
                self.p3_correct.get(),
                self.p3_wrong.get(),
                self.p3_unattempted.get(),
                "Paper 3"
            )

            p4 = self.calculate_objective(
                self.p4_correct.get(),
                self.p4_wrong.get(),
                self.p4_unattempted.get(),
                "Paper 4"
            )

            # Total
            total = p1 + p2 + p3 + p4
            percentage = (total / Decimal("400")) * 100

            # ICAI passing criteria
            paper_pass = all(
                marks >= Decimal("40")
                for marks in [p1, p2, p3, p4]
            )

            aggregate_pass = total >= Decimal("200")

            passed = paper_pass and aggregate_pass

            result = "PASS" if passed else "FAIL"

            # ------------------------------------------------
            # Result window
            # ------------------------------------------------
            self.show_result(
                name,
                roll,
                registration,
                p1,
                p2,
                p3,
                p4,
                total,
                percentage,
                result
            )

        except ValueError as error:
            messagebox.showerror(
                "Validation Error",
                str(error)
            )

    # --------------------------------------------------------
    # Result / Marksheet
    # --------------------------------------------------------
    def show_result(
        self,
        name,
        roll,
        registration,
        p1,
        p2,
        p3,
        p4,
        total,
        percentage,
        result
    ):

        result_window = tk.Toplevel(self.root)
        result_window.title("CA Foundation Marksheet")
        result_window.geometry("750x650")

        tk.Label(
            result_window,
            text="INSTITUTE OF CHARTERED ACCOUNTANTS OF INDIA",
            font=("Arial", 16, "bold"),
            fg="#17365D"
        ).pack(pady=(20, 5))

        tk.Label(
            result_window,
            text="CA FOUNDATION EXAMINATION",
            font=("Arial", 14, "bold")
        ).pack()

        ttk.Separator(
            result_window,
            orient="horizontal"
        ).pack(fill="x", padx=30, pady=15)

        # Student details
        details = tk.Frame(result_window)
        details.pack(fill="x", padx=50)

        details_text = (
            f"Student Name       : {name}\n"
            f"Roll Number        : {roll}\n"
            f"Registration No.   : {registration}\n"
            f"Examination        : {self.attempt_var.get()}"
        )

        tk.Label(
            details,
            text=details_text,
            justify="left",
            font=("Arial", 11)
        ).pack(anchor="w")

        # Marks table
        table = ttk.Treeview(
            result_window,
            columns=(
                "paper",
                "max",
                "marks",
                "status"
            ),
            show="headings",
            height=6
        )

        table.heading("paper", text="Paper")
        table.heading("max", text="Maximum")
        table.heading("marks", text="Marks")
        table.heading("status", text="Status")

        table.column("paper", width=300)
        table.column("max", width=100, anchor="center")
        table.column("marks", width=100, anchor="center")
        table.column("status", width=100, anchor="center")

        table.pack(pady=20)

        paper_marks = [
            ("Paper 1 - Accounting", p1),
            ("Paper 2 - Business Laws", p2),
            ("Paper 3 - Quantitative Aptitude", p3),
            ("Paper 4 - Business Economics", p4)
        ]

        for paper, marks in paper_marks:

            status = "PASS" if marks >= 40 else "FAIL"

            table.insert(
                "",
                "end",
                values=(
                    paper,
                    "100",
                    f"{marks:.2f}",
                    status
                )
            )

        # Summary
        summary = tk.Frame(result_window)
        summary.pack(pady=10)

        tk.Label(
            summary,
            text=f"TOTAL: {total:.2f} / 400",
            font=("Arial", 13, "bold")
        ).pack()

        tk.Label(
            summary,
            text=f"PERCENTAGE: {percentage:.2f}%",
            font=("Arial", 13, "bold")
        ).pack(pady=5)

        result_color = "green" if result == "PASS" else "red"

        tk.Label(
            result_window,
            text=result,
            font=("Arial", 24, "bold"),
            fg=result_color
        ).pack(pady=15)

        if result == "PASS":
            note = (
                "Candidate satisfies the 40% minimum in each paper "
                "and 50% aggregate requirement."
            )
        else:
            note = (
                "Candidate does not satisfy the ICAI minimum "
                "paper-wise and/or aggregate passing requirement."
            )

        tk.Label(
            result_window,
            text=note,
            wraplength=650,
            justify="center"
        ).pack(pady=5)

        ttk.Button(
            result_window,
            text="Close",
            command=result_window.destroy
        ).pack(pady=15)

    # --------------------------------------------------------
    # Clear form
    # --------------------------------------------------------
    def clear_form(self):

        variables = [
            self.name_var,
            self.roll_var,
            self.reg_var,
            self.p1_var,
            self.p2_var,
            self.p3_correct,
            self.p3_wrong,
            self.p3_unattempted,
            self.p4_correct,
            self.p4_wrong,
            self.p4_unattempted
        ]

        for variable in variables:
            variable.set("")

        self.attempt_var.set("May 2026")
        self.result_label.config(text="")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    root = tk.Tk()
    app = CAMarksheet(root)
    root.mainloop()
