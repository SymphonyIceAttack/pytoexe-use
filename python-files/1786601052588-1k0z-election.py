import tkinter as tk
from tkinter import messagebox
import json
import os


# ============================================================
# SCHOOL ELECTION 2026
# 100% PYTHON / TKINTER
# ============================================================

VOTES_FILE = "votes.json"
CANDIDATES_FILE = "candidates.json"

ADMIN_PASSWORD = "school123"


# ============================================================
# HOUSES
# ============================================================

HOUSES = [
    "Yaqeen",
    "Adal",
    "Ehsaan",
    "Sabar"
]


# ============================================================
# HOUSE COLORS
# ============================================================

HOUSE_COLORS = {
    "Yaqeen": "#2e7d32",   # GREEN
    "Adal": "#1565c0",     # BLUE
    "Ehsaan": "#d32f2f",   # RED
    "Sabar": "#f9a825"     # YELLOW
}


# ============================================================
# POSITIONS
# ============================================================

POSITIONS = [
    ("head_boy", "HEAD BOY"),
    ("captain", "CAPTAIN"),
    ("vice_captain", "VICE CAPTAIN")
]


# ============================================================
# DEFAULT CANDIDATES
#
# IMPORTANT:
#
# HEAD BOY:
# Same candidates for EVERY house.
#
# CAPTAIN:
# Different candidates according to house.
#
# VICE CAPTAIN:
# Different candidates according to house.
# ============================================================

DEFAULT_CANDIDATES = {

    # ========================================================
    # HEAD BOY
    # SAME FOR EVERY HOUSE
    # ========================================================

    "head_boy": [

        {"id": "HB01", "name": "Aarav Sharma"},
        {"id": "HB02", "name": "Rohan Verma"},
        {"id": "HB03", "name": "Aditya Singh"},
        {"id": "HB04", "name": "Rahul Patel"},
        {"id": "HB05", "name": "Arjun Kumar"},
        {"id": "HB06", "name": "Vivek Yadav"},
        {"id": "HB07", "name": "Karan Mehta"},
        {"id": "HB08", "name": "Manish Gupta"},
        {"id": "HB09", "name": "Dev Sharma"},
        {"id": "HB10", "name": "Mohit Jain"},
        {"id": "HB11", "name": "Sahil Khan"},
        {"id": "HB12", "name": "Ankit Das"}
    ],


    # ========================================================
    # CAPTAIN
    # DIFFERENT FOR EACH HOUSE
    # ========================================================

    "captain": [

        # Yaqeen
        {"id": "C01", "name": "Vivek Kumar", "house": "Yaqeen"},
        {"id": "C02", "name": "Karan Mehta", "house": "Yaqeen"},
        {"id": "C03", "name": "Manish Yadav", "house": "Yaqeen"},

        # Adal
        {"id": "C04", "name": "Arjun Das", "house": "Adal"},
        {"id": "C05", "name": "Ritesh Patel", "house": "Adal"},
        {"id": "C06", "name": "Nikhil Sharma", "house": "Adal"},

        # Ehsaan
        {"id": "C07", "name": "Yash Verma", "house": "Ehsaan"},
        {"id": "C08", "name": "Ravi Singh", "house": "Ehsaan"},
        {"id": "C09", "name": "Aman Gupta", "house": "Ehsaan"},

        # Sabar
        {"id": "C10", "name": "Harsh Jain", "house": "Sabar"},
        {"id": "C11", "name": "Varun Khan", "house": "Sabar"},
        {"id": "C12", "name": "Krishna Das", "house": "Sabar"}
    ],


    # ========================================================
    # VICE CAPTAIN
    # DIFFERENT FOR EACH HOUSE
    # ========================================================

    "vice_captain": [

        # Yaqeen
        {"id": "VC01", "name": "Ankit Gupta", "house": "Yaqeen"},
        {"id": "VC02", "name": "Dev Sharma", "house": "Yaqeen"},
        {"id": "VC03", "name": "Mohit Jain", "house": "Yaqeen"},

        # Adal
        {"id": "VC04", "name": "Sahil Khan", "house": "Adal"},
        {"id": "VC05", "name": "Rohit Patel", "house": "Adal"},
        {"id": "VC06", "name": "Aman Yadav", "house": "Adal"},

        # Ehsaan
        {"id": "VC07", "name": "Deepak Singh", "house": "Ehsaan"},
        {"id": "VC08", "name": "Sumit Verma", "house": "Ehsaan"},
        {"id": "VC09", "name": "Raj Mehta", "house": "Ehsaan"},

        # Sabar
        {"id": "VC10", "name": "Abhishek Das", "house": "Sabar"},
        {"id": "VC11", "name": "Vishal Kumar", "house": "Sabar"},
        {"id": "VC12", "name": "Tarun Sharma", "house": "Sabar"}
    ]
}


# ============================================================
# MAIN APPLICATION
# ============================================================

class SchoolElection:

    def __init__(self, root):

        self.root = root

        self.root.title("School Election 2026")

        self.root.geometry("1000x720")

        self.root.minsize(700, 500)

        self.root.configure(bg="#eaf4ff")

        self.roll_number = ""
        self.house = ""

        self.head_boy_vote = ""
        self.captain_vote = ""
        self.vice_captain_vote = ""

        self.current_selection = tk.StringVar()

        self.candidates = self.load_candidates()

        self.show_home()


    # ========================================================
    # CLEAR WINDOW
    # ========================================================

    def clear_window(self):

        for widget in self.root.winfo_children():
            widget.destroy()


    # ========================================================
    # TITLE BAR
    # ========================================================

    def title_bar(self, title, subtitle=""):

        frame = tk.Frame(
            self.root,
            bg="#1565c0"
        )

        frame.pack(
            fill="x"
        )

        tk.Label(
            frame,
            text=title,
            font=("Arial", 26, "bold"),
            fg="white",
            bg="#1565c0"
        ).pack(
            pady=(15, 3)
        )

        if subtitle:

            tk.Label(
                frame,
                text=subtitle,
                font=("Arial", 12),
                fg="white",
                bg="#1565c0"
            ).pack(
                pady=(0, 12)
            )


    # ========================================================
    # BUTTON
    # ========================================================

    def create_button(
        self,
        parent,
        text,
        command,
        color="#1565c0"
    ):

        return tk.Button(
            parent,
            text=text,
            command=command,
            font=("Arial", 13, "bold"),
            bg=color,
            fg="white",
            activebackground=color,
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=10
        )


    # ========================================================
    # SCROLLABLE FRAME
    #
    # This is used throughout the application.
    # Mouse wheel + scrollbar both work.
    # ========================================================

    def create_scrollable_frame(self, parent):

        outer = tk.Frame(
            parent,
            bg="#eaf4ff"
        )

        outer.pack(
            fill="both",
            expand=True
        )

        canvas = tk.Canvas(
            outer,
            bg="#eaf4ff",
            highlightthickness=0
        )

        scrollbar = tk.Scrollbar(
            outer,
            orient="vertical",
            command=canvas.yview
        )

        scroll_frame = tk.Frame(
            canvas,
            bg="#eaf4ff"
        )

        scroll_window = canvas.create_window(
            (0, 0),
            window=scroll_frame,
            anchor="nw"
        )


        def update_scroll_region(event=None):

            canvas.configure(
                scrollregion=canvas.bbox("all")
            )


        def resize_inner_frame(event):

            canvas.itemconfig(
                scroll_window,
                width=event.width
            )


        scroll_frame.bind(
            "<Configure>",
            update_scroll_region
        )

        canvas.bind(
            "<Configure>",
            resize_inner_frame
        )


        canvas.configure(
            yscrollcommand=scrollbar.set
        )


        canvas.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )


        # ----------------------------------------------------
        # MOUSE WHEEL
        # ----------------------------------------------------

        def mousewheel(event):

            canvas.yview_scroll(
                int(-1 * (event.delta / 120)),
                "units"
            )


        canvas.bind_all(
            "<MouseWheel>",
            mousewheel
        )

        # Linux mouse wheel
        canvas.bind_all(
            "<Button-4>",
            lambda event: canvas.yview_scroll(-1, "units")
        )

        canvas.bind_all(
            "<Button-5>",
            lambda event: canvas.yview_scroll(1, "units")
        )


        return outer, canvas, scroll_frame


    # ========================================================
    # HOME PAGE
    # ========================================================

    def show_home(self):

        self.clear_window()

        self.roll_number = ""
        self.house = ""

        self.head_boy_vote = ""
        self.captain_vote = ""
        self.vice_captain_vote = ""

        self.title_bar(
            "🏫 SCHOOL ELECTION 2026",
            "Student Council Voting System"
        )


        outer, canvas, frame = self.create_scrollable_frame(
            self.root
        )


        card = tk.Frame(
            frame,
            bg="white",
            bd=1,
            relief="solid"
        )

        card.pack(
            padx=40,
            pady=30,
            ipadx=40,
            ipady=25
        )


        tk.Label(
            card,
            text="🗳️ CAST YOUR VOTE",
            font=("Arial", 23, "bold"),
            fg="#1565c0",
            bg="white"
        ).pack(
            pady=(10, 20)
        )


        # ----------------------------------------------------
        # ROLL NUMBER
        # ----------------------------------------------------

        tk.Label(
            card,
            text="Roll Number",
            font=("Arial", 13, "bold"),
            bg="white"
        ).pack(
            anchor="w",
            padx=30
        )


        self.roll_entry = tk.Entry(
            card,
            font=("Arial", 14),
            width=35
        )

        self.roll_entry.pack(
            padx=30,
            pady=(5, 20),
            ipady=7
        )


        # ----------------------------------------------------
        # HOUSE
        # ----------------------------------------------------

        tk.Label(
            card,
            text="Select Your House",
            font=("Arial", 15, "bold"),
            fg="#1565c0",
            bg="white"
        ).pack(
            pady=(5, 10)
        )


        self.house_var = tk.StringVar()


        house_frame = tk.Frame(
            card,
            bg="white"
        )

        house_frame.pack(
            padx=20,
            pady=5
        )


        for house in HOUSES:

            tk.Radiobutton(
                house_frame,
                text=house,
                variable=self.house_var,
                value=house,
                font=("Arial", 13, "bold"),
                fg=HOUSE_COLORS[house],
                bg="white",
                activebackground="white",
                padx=10,
                pady=8
            ).pack(
                side="left"
            )


        # ----------------------------------------------------
        # START
        # ----------------------------------------------------

        self.create_button(
            card,
            "START VOTING →",
            self.start_voting,
            "#1565c0"
        ).pack(
            fill="x",
            padx=30,
            pady=(25, 10)
        )


        # ----------------------------------------------------
        # ADMIN
        # ----------------------------------------------------

        self.create_button(
            card,
            "🔐 ADMIN / RESULTS",
            self.admin_login,
            "#616161"
        ).pack(
            fill="x",
            padx=30,
            pady=5
        )


        tk.Label(
            frame,
            text="Each roll number can vote only once.",
            font=("Arial", 11),
            fg="#555555",
            bg="#eaf4ff"
        ).pack(
            pady=15
        )


    # ========================================================
    # START VOTING
    # ========================================================

    def start_voting(self):

        roll = self.roll_entry.get().strip()

        house = self.house_var.get().strip()


        if roll == "":

            messagebox.showerror(
                "Missing Information",
                "Please enter the roll number."
            )

            return


        if house == "":

            messagebox.showerror(
                "Select House",
                "Please select your house."
            )

            return


        if self.already_voted(roll):

            messagebox.showerror(
                "Already Voted",
                "This roll number has already submitted a vote."
            )

            return


        self.roll_number = roll
        self.house = house

        self.head_boy_vote = ""
        self.captain_vote = ""
        self.vice_captain_vote = ""


        self.show_head_boy()


    # ========================================================
    # GET CANDIDATES
    # ========================================================

    def get_candidates(self, position):

        # HEAD BOY:
        # SAME CANDIDATES FOR EVERY HOUSE

        if position == "head_boy":

            return self.candidates[position]


        # CAPTAIN / VICE CAPTAIN:
        # ONLY SELECTED HOUSE

        result = []

        for candidate in self.candidates[position]:

            if candidate.get("house") == self.house:

                result.append(candidate)


        return result


    # ========================================================
    # CANDIDATE PAGE
    # ========================================================

    def show_candidates(
        self,
        position,
        title,
        step
    ):

        self.clear_window()


        self.title_bar(
            "🏫 SCHOOL ELECTION 2026",
            "House: " + self.house
        )


        # ----------------------------------------------------
        # SCROLLABLE ELECTION AREA
        # ----------------------------------------------------

        outer, canvas, frame = self.create_scrollable_frame(
            self.root
        )


        tk.Label(
            frame,
            text="STEP " + str(step) + " OF 3",
            font=("Arial", 12, "bold"),
            fg="#555555",
            bg="#eaf4ff"
        ).pack(
            pady=10
        )


        card = tk.Frame(
            frame,
            bg="white",
            bd=1,
            relief="solid"
        )

        card.pack(
            fill="x",
            padx=40,
            pady=5
        )


        tk.Label(
            card,
            text=title,
            font=("Arial", 24, "bold"),
            fg="#1565c0",
            bg="white"
        ).pack(
            pady=(20, 5)
        )


        # ----------------------------------------------------
        # HOUSE DISPLAY
        # ----------------------------------------------------

        if position == "head_boy":

            house_text = "HEAD BOY IS OPEN TO ALL HOUSES"

            house_color = "#1565c0"

        else:

            house_text = "House: " + self.house

            house_color = HOUSE_COLORS.get(
                self.house,
                "#1565c0"
            )


        tk.Label(
            card,
            text=house_text,
            font=("Arial", 14, "bold"),
            fg=house_color,
            bg="white"
        ).pack(
            pady=5
        )


        tk.Label(
            card,
            text="Select ONE candidate",
            font=("Arial", 13),
            fg="#555555",
            bg="white"
        ).pack(
            pady=(0, 15)
        )


        self.current_selection = tk.StringVar()


        candidates = self.get_candidates(position)


        candidates_frame = tk.Frame(
            card,
            bg="white"
        )

        candidates_frame.pack(
            fill="x",
            padx=30,
            pady=10
        )


        # ----------------------------------------------------
        # CANDIDATES
        # ----------------------------------------------------

        for index, candidate in enumerate(candidates):

            candidate_id = candidate["id"]

            candidate_name = candidate["name"]


            candidate_frame = tk.Frame(
                candidates_frame,
                bg="#f8fbff",
                bd=2,
                relief="groove"
            )

            candidate_frame.pack(
                fill="x",
                padx=20,
                pady=8,
                ipady=8
            )


            radio = tk.Radiobutton(
                candidate_frame,
                text=candidate_name,
                variable=self.current_selection,
                value=candidate_id,
                font=("Arial", 16, "bold"),
                bg="#f8fbff",
                activebackground="#f8fbff",
                anchor="w"
            )

            radio.pack(
                side="left",
                padx=20
            )


            tk.Label(
                candidate_frame,
                text="Candidate " + str(index + 1),
                font=("Arial", 11),
                fg="#666666",
                bg="#f8fbff"
            ).pack(
                side="right",
                padx=20
            )


        # ----------------------------------------------------
        # BUTTON
        # ----------------------------------------------------

        if position == "head_boy":

            button_text = "NEXT →"

            command = self.head_boy_next

        elif position == "captain":

            button_text = "NEXT →"

            command = self.captain_next

        else:

            button_text = "🗳️ SUBMIT FINAL VOTE"

            command = self.submit_vote


        self.create_button(
            card,
            button_text,
            command,
            "#2e7d32"
        ).pack(
            fill="x",
            padx=50,
            pady=25
        )


        # ----------------------------------------------------
        # IMPORTANT:
        # Scroll automatically to TOP
        # ----------------------------------------------------

        canvas.yview_moveto(0)


    # ========================================================
    # HEAD BOY
    # ========================================================

    def show_head_boy(self):

        self.show_candidates(
            "head_boy",
            "🧑‍🎓 VOTE FOR HEAD BOY",
            1
        )


    def head_boy_next(self):

        selected = self.current_selection.get()


        if selected == "":

            messagebox.showwarning(
                "Select Candidate",
                "Please select a Head Boy candidate."
            )

            return


        self.head_boy_vote = selected


        # IMPORTANT:
        # Go directly to Captain page.

        self.show_captain()


    # ========================================================
    # CAPTAIN
    # ========================================================

    def show_captain(self):

        self.show_candidates(
            "captain",
            "🏆 VOTE FOR CAPTAIN",
            2
        )


    def captain_next(self):

        selected = self.current_selection.get()


        if selected == "":

            messagebox.showwarning(
                "Select Candidate",
                "Please select a Captain candidate."
            )

            return


        self.captain_vote = selected


        self.show_vice_captain()


    # ========================================================
    # VICE CAPTAIN
    # ========================================================

    def show_vice_captain(self):

        self.show_candidates(
            "vice_captain",
            "⭐ VOTE FOR VICE CAPTAIN",
            3
        )


    # ========================================================
    # SUBMIT
    # ========================================================

    def submit_vote(self):

        selected = self.current_selection.get()


        if selected == "":

            messagebox.showwarning(
                "Select Candidate",
                "Please select a Vice Captain candidate."
            )

            return


        self.vice_captain_vote = selected


        # Final duplicate check

        if self.already_voted(self.roll_number):

            messagebox.showerror(
                "Already Voted",
                "This roll number has already voted."
            )

            self.show_home()

            return


        vote = {

            "roll_number": self.roll_number,

            "house": self.house,

            "head_boy": self.head_boy_vote,

            "captain": self.captain_vote,

            "vice_captain": self.vice_captain_vote

        }


        votes = self.load_votes()

        votes.append(vote)

        self.save_votes(votes)


        self.show_countdown(5)


    # ========================================================
    # COUNTDOWN
    # ========================================================

    def show_countdown(self, seconds):

        self.clear_window()


        self.title_bar(
            "🏫 SCHOOL ELECTION 2026",
            "Vote Submitted"
        )


        outer, canvas, frame = self.create_scrollable_frame(
            self.root
        )


        card = tk.Frame(
            frame,
            bg="white",
            bd=1,
            relief="solid"
        )

        card.pack(
            padx=80,
            pady=50,
            ipadx=50,
            ipady=30
        )


        tk.Label(
            card,
            text="✓",
            font=("Arial", 70, "bold"),
            fg="#2e7d32",
            bg="white"
        ).pack(
            pady=(30, 10)
        )


        tk.Label(
            card,
            text="VOTE SUBMITTED SUCCESSFULLY!",
            font=("Arial", 22, "bold"),
            fg="#2e7d32",
            bg="white"
        ).pack()


        tk.Label(
            card,
            text="Your vote has been recorded.",
            font=("Arial", 14),
            bg="white"
        ).pack(
            pady=10
        )


        self.countdown_label = tk.Label(
            card,
            text=str(seconds),
            font=("Arial", 70, "bold"),
            fg="#1565c0",
            bg="white"
        )

        self.countdown_label.pack(
            pady=20
        )


        tk.Label(
            card,
            text="Next voter page will open automatically...",
            font=("Arial", 12),
            fg="#555555",
            bg="white"
        ).pack()


        self.countdown(seconds)


    def countdown(self, seconds):

        self.countdown_label.config(
            text=str(seconds)
        )


        if seconds <= 0:

            self.show_home()

            return


        self.root.after(
            1000,
            lambda: self.countdown(seconds - 1)
        )


    # ========================================================
    # LOAD VOTES
    # ========================================================

    def load_votes(self):

        if not os.path.exists(VOTES_FILE):

            return []


        try:

            with open(
                VOTES_FILE,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)


                if isinstance(data, list):

                    return data


        except Exception:

            pass


        return []


    # ========================================================
    # SAVE VOTES
    # ========================================================

    def save_votes(self, votes):

        with open(
            VOTES_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                votes,
                file,
                indent=4
            )


    # ========================================================
    # LOAD CANDIDATES
    # ========================================================

    def load_candidates(self):

        if not os.path.exists(CANDIDATES_FILE):

            self.save_candidates(
                DEFAULT_CANDIDATES
            )

            return DEFAULT_CANDIDATES


        try:

            with open(
                CANDIDATES_FILE,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)


                if isinstance(data, dict):

                    return data


        except Exception:

            pass


        self.save_candidates(
            DEFAULT_CANDIDATES
        )

        return DEFAULT_CANDIDATES


    # ========================================================
    # SAVE CANDIDATES
    # ========================================================

    def save_candidates(self, candidates):

        with open(
            CANDIDATES_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                candidates,
                file,
                indent=4
            )


    # ========================================================
    # DUPLICATE CHECK
    # ========================================================

    def already_voted(self, roll):

        roll = str(
            roll
        ).strip().lower()


        votes = self.load_votes()


        for vote in votes:

            saved_roll = str(
                vote.get(
                    "roll_number",
                    ""
                )
            ).strip().lower()


            if saved_roll == roll:

                return True


        return False


    # ========================================================
    # ADMIN LOGIN
    # ========================================================

    def admin_login(self):

        window = tk.Toplevel(
            self.root
        )

        window.title(
            "Admin Login"
        )

        window.geometry(
            "420x280"
        )

        window.configure(
            bg="white"
        )

        window.resizable(
            False,
            False
        )


        tk.Label(
            window,
            text="🔐 ADMIN LOGIN",
            font=("Arial", 21, "bold"),
            fg="#1565c0",
            bg="white"
        ).pack(
            pady=25
        )


        tk.Label(
            window,
            text="Admin Password",
            font=("Arial", 12, "bold"),
            bg="white"
        ).pack()


        password_entry = tk.Entry(
            window,
            show="*",
            font=("Arial", 14),
            width=25
        )

        password_entry.pack(
            pady=12,
            ipady=5
        )


        def check_password():

            password = password_entry.get()


            if password == ADMIN_PASSWORD:

                window.destroy()

                self.show_admin_panel()

            else:

                messagebox.showerror(
                    "Incorrect Password",
                    "The admin password is incorrect.",
                    parent=window
                )


        self.create_button(
            window,
            "LOGIN",
            check_password,
            "#1565c0"
        ).pack(
            fill="x",
            padx=80,
            pady=10
        )


        password_entry.focus()


    # ========================================================
    # ADMIN PANEL
    # ========================================================

    def show_admin_panel(self):

        self.clear_window()


        self.title_bar(
            "🔐 ADMIN PANEL",
            "School Election 2026"
        )


        outer, canvas, frame = self.create_scrollable_frame(
            self.root
        )


        tk.Label(
            frame,
            text="Administrator Controls",
            font=("Arial", 22, "bold"),
            fg="#1565c0",
            bg="#eaf4ff"
        ).pack(
            pady=25
        )


        self.create_button(
            frame,
            "📊 VIEW ELECTION RESULTS",
            self.show_results,
            "#1565c0"
        ).pack(
            fill="x",
            padx=180,
            pady=8
        )


        self.create_button(
            frame,
            "✏️ CHANGE CANDIDATE NAMES",
            self.edit_candidates,
            "#ef6c00"
        ).pack(
            fill="x",
            padx=180,
            pady=8
        )


        self.create_button(
            frame,
            "🗑️ DELETE ALL VOTES",
            self.delete_votes,
            "#c62828"
        ).pack(
            fill="x",
            padx=180,
            pady=8
        )


        self.create_button(
            frame,
            "🏠 BACK TO VOTING PAGE",
            self.show_home,
            "#616161"
        ).pack(
            fill="x",
            padx=180,
            pady=8
        )


    # ========================================================
    # EDIT CANDIDATES
    # ========================================================

    def edit_candidates(self):

        self.clear_window()


        self.title_bar(
            "✏️ EDIT CANDIDATES",
            "Admin can change candidate names"
        )


        # ----------------------------------------------------
        # SCROLLABLE ADMIN AREA
        # ----------------------------------------------------

        outer, canvas, frame = self.create_scrollable_frame(
            self.root
        )


        self.candidate_entries = []


        # ----------------------------------------------------
        # POSITIONS
        # ----------------------------------------------------

        for position, position_name in POSITIONS:

            section = tk.Frame(
                frame,
                bg="white",
                bd=1,
                relief="solid"
            )

            section.pack(
                fill="x",
                padx=30,
                pady=12
            )


            tk.Label(
                section,
                text=position_name,
                font=("Arial", 19, "bold"),
                fg="#1565c0",
                bg="white"
            ).pack(
                pady=10
            )


            # Information for Head Boy

            if position == "head_boy":

                tk.Label(
                    section,
                    text="Same Head Boy candidates for all houses",
                    font=("Arial", 11, "italic"),
                    fg="#777777",
                    bg="white"
                ).pack(
                    pady=(0, 8)
                )


            for candidate in self.candidates[position]:

                row = tk.Frame(
                    section,
                    bg="white"
                )

                row.pack(
                    fill="x",
                    padx=20,
                    pady=5
                )


                tk.Label(
                    row,
                    text=candidate["id"],
                    font=("Arial", 10, "bold"),
                    width=7,
                    bg="white",
                    fg="#555555"
                ).pack(
                    side="left"
                )


                if position == "head_boy":

                    house_text = "ALL"

                    house_color = "#1565c0"

                else:

                    house_text = candidate["house"]

                    house_color = HOUSE_COLORS.get(
                        house_text,
                        "#333333"
                    )


                tk.Label(
                    row,
                    text=house_text,
                    font=("Arial", 11, "bold"),
                    width=10,
                    bg="white",
                    fg=house_color
                ).pack(
                    side="left"
                )


                entry = tk.Entry(
                    row,
                    font=("Arial", 12),
                    width=35
                )


                entry.insert(
                    0,
                    candidate["name"]
                )


                entry.pack(
                    side="left",
                    padx=10,
                    ipady=5
                )


                self.candidate_entries.append(
                    (
                        position,
                        candidate["id"],
                        entry
                    )
                )


        # ----------------------------------------------------
        # SAVE
        # ----------------------------------------------------

        self.create_button(
            frame,
            "💾 SAVE ALL CANDIDATE NAMES",
            self.save_candidate_names,
            "#2e7d32"
        ).pack(
            fill="x",
            padx=150,
            pady=20
        )


        self.create_button(
            frame,
            "← BACK TO ADMIN",
            self.show_admin_panel,
            "#616161"
        ).pack(
            fill="x",
            padx=150,
            pady=(0, 30)
        )


        # Start at top

        canvas.yview_moveto(0)


    # ========================================================
    # SAVE CANDIDATE NAMES
    # ========================================================

    def save_candidate_names(self):

        for position, candidate_id, entry in self.candidate_entries:

            new_name = entry.get().strip()


            if new_name == "":

                messagebox.showerror(
                    "Invalid Name",
                    "Candidate names cannot be empty."
                )

                return


            for candidate in self.candidates[position]:

                if candidate["id"] == candidate_id:

                    candidate["name"] = new_name


        self.save_candidates(
            self.candidates
        )


        messagebox.showinfo(
            "Saved",
            "Candidate names have been updated successfully."
        )


        self.show_admin_panel()


    # ========================================================
    # RESULTS
    # ========================================================

    def show_results(self):

        self.clear_window()


        self.title_bar(
            "📊 ELECTION RESULTS",
            "Administrator Results"
        )


        votes = self.load_votes()


        outer, canvas, frame = self.create_scrollable_frame(
            self.root
        )


        tk.Label(
            frame,
            text="TOTAL VOTES: " + str(len(votes)),
            font=("Arial", 20, "bold"),
            fg="#1565c0",
            bg="#eaf4ff"
        ).pack(
            pady=10
        )


        # ----------------------------------------------------
        # HOUSE SUMMARY
        # ----------------------------------------------------

        house_frame = tk.Frame(
            frame,
            bg="white",
            bd=1,
            relief="solid"
        )

        house_frame.pack(
            fill="x",
            padx=30,
            pady=10
        )


        tk.Label(
            house_frame,
            text="HOUSE-WISE VOTES",
            font=("Arial", 18, "bold"),
            fg="#1565c0",
            bg="white"
        ).pack(
            pady=8
        )


        for house in HOUSES:

            count = 0


            for vote in votes:

                if vote.get("house") == house:

                    count += 1


            tk.Label(
                house_frame,
                text=house + " House : " + str(count) + " vote(s)",
                font=("Arial", 12, "bold"),
                fg=HOUSE_COLORS[house],
                bg="white"
            ).pack(
                pady=2
            )


        # ----------------------------------------------------
        # RESULTS
        # ----------------------------------------------------

        for house in HOUSES:

            self.show_house_results(
                frame,
                house,
                votes
            )


        # ----------------------------------------------------
        # BUTTONS
        # ----------------------------------------------------

        self.create_button(
            frame,
            "← ADMIN PANEL",
            self.show_admin_panel,
            "#616161"
        ).pack(
            fill="x",
            padx=150,
            pady=10
        )


        self.create_button(
            frame,
            "🗑️ DELETE ALL VOTES",
            self.delete_votes,
            "#c62828"
        ).pack(
            fill="x",
            padx=150,
            pady=(0, 30)
        )


    # ========================================================
    # HOUSE RESULTS
    # ========================================================

    def show_house_results(
        self,
        parent,
        house,
        votes
    ):

        section = tk.Frame(
            parent,
            bg="white",
            bd=1,
            relief="solid"
        )


        section.pack(
            fill="x",
            padx=30,
            pady=10
        )


        tk.Label(
            section,
            text="🏠 " + house.upper() + " HOUSE",
            font=("Arial", 19, "bold"),
            fg=HOUSE_COLORS[house],
            bg="white"
        ).pack(
            pady=10
        )


        house_votes = []


        for vote in votes:

            if vote.get("house") == house:

                house_votes.append(vote)


        tk.Label(
            section,
            text="Votes: " + str(len(house_votes)),
            font=("Arial", 12, "bold"),
            fg="#555555",
            bg="white"
        ).pack(
            pady=(0, 8)
        )


        for position, position_name in POSITIONS:

            counts = {}


            # ------------------------------------------------
            # HEAD BOY = ALL CANDIDATES
            # CAPTAIN/VICE = HOUSE CANDIDATES
            # ------------------------------------------------

            if position == "head_boy":

                candidates = self.candidates[position]

            else:

                candidates = [

                    candidate

                    for candidate in self.candidates[position]

                    if candidate.get("house") == house

                ]


            for candidate in candidates:

                counts[candidate["id"]] = 0


            for vote in house_votes:

                candidate_id = vote.get(
                    position,
                    ""
                )


                if candidate_id in counts:

                    counts[candidate_id] += 1


            highest = 0


            if counts:

                highest = max(
                    counts.values()
                )


            tk.Label(
                section,
                text=position_name,
                font=("Arial", 14, "bold"),
                fg="#1565c0",
                bg="white"
            ).pack(
                anchor="w",
                padx=25,
                pady=(8, 3)
            )


            for candidate in candidates:

                candidate_id = candidate["id"]

                count = counts.get(
                    candidate_id,
                    0
                )


                if count == highest and highest > 0:

                    text = (
                        "🏆 " +
                        candidate["name"] +
                        " — " +
                        str(count) +
                        " vote(s)  WINNER"
                    )

                    color = "#2e7d32"

                else:

                    text = (
                        candidate["name"] +
                        " — " +
                        str(count) +
                        " vote(s)"
                    )

                    color = "#333333"


                tk.Label(
                    section,
                    text=text,
                    font=("Arial", 11, "bold"),
                    fg=color,
                    bg="white"
                ).pack(
                    anchor="w",
                    padx=45,
                    pady=2
                )


    # ========================================================
    # DELETE VOTES
    # ========================================================

    def delete_votes(self):

        answer = messagebox.askyesno(
            "Delete All Votes",
            "WARNING!\n\n"
            "This will permanently delete ALL election votes.\n\n"
            "Are you sure?"
        )


        if not answer:

            return


        window = tk.Toplevel(
            self.root
        )


        window.title(
            "Confirm Admin Password"
        )


        window.geometry(
            "420x250"
        )


        window.configure(
            bg="white"
        )


        window.resizable(
            False,
            False
        )


        tk.Label(
            window,
            text="🔐 ENTER ADMIN PASSWORD",
            font=("Arial", 17, "bold"),
            fg="#c62828",
            bg="white"
        ).pack(
            pady=25
        )


        entry = tk.Entry(
            window,
            show="*",
            font=("Arial", 14),
            width=25
        )


        entry.pack(
            pady=10,
            ipady=5
        )


        def confirm_delete():

            password = entry.get()


            if password != ADMIN_PASSWORD:

                messagebox.showerror(
                    "Error",
                    "Incorrect admin password.",
                    parent=window
                )

                return


            self.save_votes([])

            window.destroy()


            messagebox.showinfo(
                "Deleted",
                "All votes have been deleted."
            )


            self.show_results()


        self.create_button(
            window,
            "DELETE ALL VOTES",
            confirm_delete,
            "#c62828"
        ).pack(
            fill="x",
            padx=70,
            pady=10
        )


        entry.focus()


# ============================================================
# START PROGRAM
# ============================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = SchoolElection(root)

    root.mainloop()
