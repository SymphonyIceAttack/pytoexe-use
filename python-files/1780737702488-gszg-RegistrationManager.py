import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from PIL import Image, ImageTk, ImageDraw, ImageFont
import csv
import json
import os
from datetime import datetime

# --------------------------
# Configuration & Storage
# --------------------------
USER_DATA_FILE = "program_users.json"
POU_RECORDS_FILE = "pou_records.json"
MOREHU_RECORDS_FILE = "morehu_records.json"
UPLOADS_FOLDER = "uploads"
ID_CARDS_FOLDER = "id_cards"
EXPORTS_FOLDER = "exports"
ID_COUNTER_FILE = "id_counters.json"

os.makedirs(UPLOADS_FOLDER, exist_ok=True)
os.makedirs(ID_CARDS_FOLDER, exist_ok=True)
os.makedirs(EXPORTS_FOLDER, exist_ok=True)

DEFAULT_USERS = {
    "itadmin": {
        "password": "admin123",
        "role": "IT Administrator"
    }
}

# Turanga options list
TURANGA_OPTIONS = [
    "Apotoro Rehita",
    "Apotoro Wairua",
    "Akonga",
    "Apotoro Takiwa",
    "Runanga",
    "Awhina",
    "Roopu Raupo",
    "Kaitiaki Whakamoemiti",
    "Mema o Nga Koea",
    "Mema o Nga Reo"
]

def init_data_files():
    if not os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "w") as f:
            json.dump(DEFAULT_USERS, f, indent=4)
    if not os.path.exists(POU_RECORDS_FILE):
        with open(POU_RECORDS_FILE, "w") as f:
            json.dump([], f)
    if not os.path.exists(MOREHU_RECORDS_FILE):
        with open(MOREHU_RECORDS_FILE, "w") as f:
            json.dump([], f)
    if not os.path.exists(ID_COUNTER_FILE):
        with open(ID_COUNTER_FILE, "w") as f:
            json.dump({"next_pou_id": 1, "next_morehu_id": 1}, f, indent=4)

def load_id_counters():
    with open(ID_COUNTER_FILE, "r") as f:
        return json.load(f)

def save_id_counters(counters):
    with open(ID_COUNTER_FILE, "w") as f:
        json.dump(counters, f, indent=4)

def get_next_suggested_id(is_pou):
    counters = load_id_counters()
    num = counters["next_pou_id"] if is_pou else counters["next_morehu_id"]
    return f"P-{num:06d}" if is_pou else f"M-{num:06d}"

def increment_id_counter(is_pou):
    counters = load_id_counters()
    if is_pou:
        counters["next_pou_id"] += 1
    else:
        counters["next_morehu_id"] += 1
    save_id_counters(counters)

def is_id_unique(new_id, exclude_index=None):
    all_records = []
    if os.path.exists(POU_RECORDS_FILE):
        all_records.extend(json.load(open(POU_RECORDS_FILE)))
    if os.path.exists(MOREHU_RECORDS_FILE):
        all_records.extend(json.load(open(MOREHU_RECORDS_FILE)))
    
    for idx, rec in enumerate(all_records):
        if exclude_index is not None and idx == exclude_index:
            continue
        if rec.get("id") == new_id:
            return False
    return True

def get_record_by_id(target_id):
    if not target_id:
        return None
    file_path = POU_RECORDS_FILE if target_id.startswith("P-") else MOREHU_RECORDS_FILE
    if not os.path.exists(file_path):
        return None
    records = json.load(open(file_path))
    for idx, rec in enumerate(records):
        if rec.get("id") == target_id:
            return {"file": file_path, "index": idx, "data": rec}
    return None

def load_users():
    return json.load(open(USER_DATA_FILE))

def save_users(users):
    json.dump(users, open(USER_DATA_FILE, "w"), indent=4)

def save_record(file_path, record):
    records = json.load(open(file_path)) if os.path.exists(file_path) else []
    records.append(record)
    json.dump(records, open(file_path, "w"), indent=4)
    return len(records) - 1

def update_record(file_path, index, updated_record):
    records = json.load(open(file_path)) if os.path.exists(file_path) else []
    if 0 <= index < len(records):
        records[index] = updated_record
        json.dump(records, open(file_path, "w"), indent=4)
        return True
    return False

def load_records(file_path):
    return json.load(open(file_path)) if os.path.exists(file_path) else []

def search_records(search_term):
    results = []
    search_term = search_term.lower().strip()
    for file_path in [POU_RECORDS_FILE, MOREHU_RECORDS_FILE]:
        records = load_records(file_path)
        for idx, rec in enumerate(records):
            if (search_term in rec.get("id", "").lower() or
                search_term in rec.get("name", "").lower() or
                search_term in rec.get("last_name", "").lower() or
                search_term in rec.get("email", "").lower() or
                search_term in rec.get("phone", "").lower() or
                search_term in rec.get("turanga", "").lower()):
                results.append({
                    "file": file_path,
                    "index": idx,
                    "id": rec.get("id"),
                    "type": rec.get("type"),
                    "name": f"{rec.get('name', '')} {rec.get('last_name', '')}",
                    "email": rec.get("email", ""),
                    "turanga": rec.get("turanga", "")
                })
    return results

def generate_id_card(record):
    """Generate an image ID card from record details"""
    card_width, card_height = 856, 540
    background_color = (240, 245, 255) if record["type"] == "POU" else (255, 245, 240)
    header_color = (30, 80, 160) if record["type"] == "POU" else (160, 60, 30)
    text_color = (20, 20, 20)

    img = Image.new("RGB", (card_width, card_height), background_color)
    draw = ImageDraw.Draw(img)

    try:
        font_large = ImageFont.truetype("arial.ttf", 32)
        font_medium = ImageFont.truetype("arial.ttf", 24)
        font_small = ImageFont.truetype("arial.ttf", 18)
    except:
        font_large = ImageFont.load_default(size=32)
        font_medium = ImageFont.load_default(size=24)
        font_small = ImageFont.load_default(size=18)

    draw.rectangle([0, 0, card_width, 80], fill=header_color)
    draw.text((card_width//2, 40), f"{record['type']} REGISTRATION CARD", fill="white", font=font_large, anchor="mm")

    draw.text((30, 100), f"ID: {record['id']}", fill=text_color, font=font_medium)

    photo = None
    photo_path = None
    for file in record.get("uploaded_files", []):
        if file["name"].lower().endswith((".jpg", ".jpeg", ".png")):
            photo_path = file["path"]
            break

    if photo_path and os.path.exists(photo_path):
        try:
            photo = Image.open(photo_path).convert("RGB")
            photo = photo.resize((180, 220), Image.Resampling.LANCZOS)
            img.paste(photo, (30, 150))
        except:
            pass

    if not photo:
        draw.rectangle([30, 150, 210, 370], outline=text_color, width=2)
        draw.text((120, 260), "No Photo", fill=text_color, font=font_medium, anchor="mm")

    details_x = 260
    details_y = 150
    line_height = 35

    draw.text((details_x, details_y), f"Name: {record.get('name', '')} {record.get('last_name', '')}", fill=text_color, font=font_medium)
    details_y += line_height
    draw.text((details_x, details_y), f"Turanga: {record.get('turanga', 'N/A')}", fill=text_color, font=font_medium)
    details_y += line_height

    if record.get("group_name"):
        draw.text((details_x, details_y), f"Group: {record['group_name']}", fill=text_color, font=font_medium)
        details_y += line_height

    draw.text((details_x, details_y), f"Phone: {record.get('phone', 'N/A')}", fill=text_color, font=font_medium)
    details_y += line_height
    draw.text((details_x, details_y), f"Email: {record.get('email', 'N/A')}", fill=text_color, font=font_small)
    details_y += line_height
    draw.text((details_x, details_y), f"Pariha: {record.get('pariha', 'N/A')}", fill=text_color, font=font_small)
    details_y += line_height
    draw.text((details_x, details_y), f"Takiwa: {record.get('takiwa', 'N/A')}", fill=text_color, font=font_small)
    details_y += line_height
    draw.text((details_x, details_y), f"Baptised: {record.get('baptised', 'No')}", fill=text_color, font=font_small)

    draw.rectangle([0, card_height-60, card_width, card_height], fill=header_color)
    draw.text((card_width//2, card_height-30), f"Issued: {datetime.now().strftime('%d/%m/%Y')}", fill="white", font=font_small, anchor="mm")

    card_path = os.path.join(ID_CARDS_FOLDER, f"ID_Card_{record['id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png")
    img.save(card_path)
    return card_path

# --------------------------
# Main Application Class
# --------------------------
class RegistrationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Community Registration Manager")
        self.root.geometry("850x820")
        self.current_user_role = None
        self.current_username = None
        
        init_data_files()
        self.show_login_page()

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    # --------------------------
    # Login System
    # --------------------------
    def show_login_page(self):
        self.clear_window()
        frame = ttk.Frame(self.root, padding=30)
        frame.pack(expand=True)

        ttk.Label(frame, text="Login", font=("Arial", 18, "bold")).grid(row=0, column=0, columnspan=2, pady=15)

        ttk.Label(frame, text="Username:").grid(row=1, column=0, sticky="w", pady=5)
        self.username_entry = ttk.Entry(frame, width=35)
        self.username_entry.grid(row=1, column=1, pady=5)

        ttk.Label(frame, text="Password:").grid(row=2, column=0, sticky="w", pady=5)
        self.password_entry = ttk.Entry(frame, width=35, show="*")
        self.password_entry.grid(row=2, column=1, pady=5)

        ttk.Button(frame, text="Login", command=self.login).grid(row=3, column=0, columnspan=2, pady=15)
        ttk.Button(frame, text="Request Access", command=lambda: messagebox.showinfo("Info", "Contact IT Admin for access")).grid(row=4, column=0, columnspan=2)

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        users = load_users()
        if username in users and users[username]["password"] == password:
            self.current_user_role = users[username]["role"]
            self.current_username = username
            messagebox.showinfo("Success", f"Logged in as: {self.current_user_role}")
            self.show_main_menu()
        else:
            messagebox.showerror("Error", "Invalid username or password")

    # --------------------------
    # Main Menu
    # --------------------------
    def show_main_menu(self):
        self.clear_window()
        frame = ttk.Frame(self.root, padding=30)
        frame.pack(expand=True)

        ttk.Label(frame, text="Main Menu", font=("Arial", 18, "bold")).grid(row=0, column=0, columnspan=2, pady=20)

        ttk.Button(frame, text="📝 New POU Registration", width=44, command=self.show_pou_form).grid(row=1, column=0, pady=8)
        ttk.Button(frame, text="📝 New Morehu Registration", width=44, command=self.show_morehu_form).grid(row=2, column=0, pady=8)
        ttk.Button(frame, text="🔍 Search All Records", width=44, command=self.show_search_function).grid(row=3, column=0, pady=8)
        ttk.Button(frame, text="👥 View All Records", width=44, command=self.show_record_selection).grid(row=4, column=0, pady=8)

        # --- NEW EXPORT OPTIONS ---
        ttk.Separator(frame, orient='horizontal').grid(row=5, column=0, sticky="ew", pady=10)
        ttk.Label(frame, text="Export & Reports", font=("Arial", 12, "bold")).grid(row=6, column=0, pady=5)
        ttk.Button(frame, text="📤 Export Turanga Summary", width=44, command=self.export_turanga_summary).grid(row=7, column=0, pady=5)
        ttk.Button(frame, text="📄 Export All Full Profiles", width=44, command=self.export_all_profiles).grid(row=8, column=0, pady=5)

        if self.current_user_role == "IT Administrator":
            ttk.Button(frame, text="👤 Add New User", width=44, command=self.show_add_user).grid(row=9, column=0, pady=8)

        ttk.Button(frame, text="🚪 Logout", width=44, command=self.show_login_page).grid(row=10, column=0, pady=20)

    # --------------------------
    # Export Functions
    # --------------------------
    def export_turanga_summary(self):
        """Export all POU records grouped by Turanga"""
        pou_records = load_records(POU_RECORDS_FILE)
        if not pou_records:
            messagebox.showinfo("Info", "No POU records found to export.")
            return

        filename = f"Turanga_Summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        file_path = os.path.join(EXPORTS_FOLDER, filename)

        headers = ["Turanga", "Group Name", "ID", "First Name", "Last Name", "Phone", "Email"]

        try:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                for rec in pou_records:
                    writer.writerow({
                        "Turanga": rec.get("turanga", ""),
                        "Group Name": rec.get("group_name", ""),
                        "ID": rec.get("id", ""),
                        "First Name": rec.get("name", ""),
                        "Last Name": rec.get("last_name", ""),
                        "Phone": rec.get("phone", ""),
                        "Email": rec.get("email", "")
                    })
            messagebox.showinfo("Export Complete", 
                f"Turanga summary exported successfully!\n\nSaved to:\n{file_path}\n\nYou can open and print this file.")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {str(e)}")

    def export_all_profiles(self):
        """Export all POU and Morehu records with full details"""
        pou_records = load_records(POU_RECORDS_FILE)
        morehu_records = load_records(MOREHU_RECORDS_FILE)
        all_records = pou_records + morehu_records

        if not all_records:
            messagebox.showinfo("Info", "No records found to export.")
            return

        filename = f"All_Profiles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        file_path = os.path.join(EXPORTS_FOLDER, filename)

        headers = [
            "Record Type", "ID", "First Name", "Last Name", "Email", "Phone",
            "Address", "Pariha", "Takiwa", "Turanga", "Group Name", "Baptised"
        ]

        try:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                for rec in all_records:
                    writer.writerow({
                        "Record Type": rec.get("type", ""),
                        "ID": rec.get("id", ""),
                        "First Name": rec.get("name", ""),
                        "Last Name": rec.get("last_name", ""),
                        "Email": rec.get("email", ""),
                        "Phone": rec.get("phone", ""),
                        "Address": rec.get("address", ""),
                        "Pariha": rec.get("pariha", ""),
                        "Takiwa": rec.get("takiwa", ""),
                        "Turanga": rec.get("turanga", ""),
                        "Group Name": rec.get("group_name", ""),
                        "Baptised": rec.get("baptised", "")
                    })
            messagebox.showinfo("Export Complete", 
                f"All profiles exported successfully!\n\nSaved to:\n{file_path}\n\nYou can open and print this file.")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {str(e)}")

    # --------------------------
    # Search Function
    # --------------------------
    def show_search_function(self):
        self.clear_window()
        frame = ttk.Frame(self.root, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="🔍 Search Records", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=10)
        ttk.Label(frame, text="Search by ID, Name, Email, Phone, or Turanga").grid(row=1, column=0, columnspan=2, pady=5)

        search_entry = ttk.Entry(frame, width=55, font=("Arial", 11))
        search_entry.grid(row=2, column=0, padx=5, pady=10)
        search_entry.focus()

        results_listbox = tk.Listbox(frame, width=95, height=16, font=("Arial", 10))
        results_listbox.grid(row=3, column=0, columnspan=2, padx=5, pady=10)

        def perform_search():
            results_listbox.delete(0, tk.END)
            term = search_entry.get()
            results = search_records(term)
            if not results:
                results_listbox.insert(tk.END, "No matching records found.")
                return
            for res in results:
                results_listbox.insert(tk.END, f"{res['id']} | {res['type']} | {res['name']} | {res['turanga']}")

        def open_selected():
            selected = results_listbox.curselection()
            if not selected:
                messagebox.showwarning("Warning", "Select a record first")
                return
            term = search_entry.get()
            results = search_records(term)
            if 0 <= selected[0] < len(results):
                rec_info = results[selected[0]]
                self.edit_existing_record(rec_info["file"], rec_info["index"])

        ttk.Button(frame, text="Search", command=perform_search).grid(row=2, column=1, padx=5)
        ttk.Button(frame, text="Open Selected Record", command=open_selected).grid(row=4, column=0, pady=5)
        ttk.Button(frame, text="Back", command=self.show_main_menu).grid(row=4, column=1, pady=5)

    # --------------------------
    # New POU Form
    # --------------------------
    def show_pou_form(self):
        self.clear_window()
        frame = ttk.Frame(self.root, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="POU Registration Form", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=10)

        suggested_id = get_next_suggested_id(is_pou=True)
        ttk.Label(frame, text="Registration ID:", font=("Arial", 11, "bold")).grid(row=1, column=0, sticky="w", pady=8)
        id_entry = ttk.Entry(frame, width=48, font=("Arial", 11))
        id_entry.insert(0, suggested_id)
        id_entry.grid(row=1, column=1, pady=8)
        ttk.Label(frame, text="Format: P-000001", foreground="gray").grid(row=2, column=1, sticky="w")

        ttk.Label(frame, text="First Name:").grid(row=3, column=0, sticky="w", pady=5)
        name_entry = ttk.Entry(frame, width=48)
        name_entry.grid(row=3, column=1, pady=5)

        ttk.Label(frame, text="Last Name:").grid(row=4, column=0, sticky="w", pady=5)
        last_name_entry = ttk.Entry(frame, width=48)
        last_name_entry.grid(row=4, column=1, pady=5)

        ttk.Label(frame, text="Email:").grid(row=5, column=0, sticky="w", pady=5)
        email_entry = ttk.Entry(frame, width=48)
        email_entry.grid(row=5, column=1, pady=5)

        ttk.Label(frame, text="Phone:").grid(row=6, column=0, sticky="w", pady=5)
        phone_entry = ttk.Entry(frame, width=48)
        phone_entry.grid(row=6, column=1, pady=5)

        ttk.Label(frame, text="Address:").grid(row=7, column=0, sticky="w", pady=5)
        address_entry = ttk.Entry(frame, width=48)
        address_entry.grid(row=7, column=1, pady=5)

        ttk.Label(frame, text="Current Pariha:").grid(row=8, column=0, sticky="w", pady=5)
        pariha_entry = ttk.Entry(frame, width=48)
        pariha_entry.grid(row=8, column=1, pady=5)

        ttk.Label(frame, text="Current Takiwa:").grid(row=9, column=0, sticky="w", pady=5)
        takiwa_entry = ttk.Entry(frame, width=48)
        takiwa_entry.grid(row=9, column=1, pady=5)

        ttk.Label(frame, text="Turanga:").grid(row=10, column=0, sticky="w", pady=5)
        turanga_var = tk.StringVar()
        turanga_dropdown = ttk.Combobox(frame, textvariable=turanga_var, values=TURANGA_OPTIONS, state="readonly", width=45)
        turanga_dropdown.grid(row=10, column=1, pady=5)

        group_label = ttk.Label(frame, text="Group Name:")
        group_entry = ttk.Entry(frame, width=48)

        def toggle_group_field(*args):
            selected = turanga_var.get()
            if selected in ["Mema o Nga Koea", "Mema o Nga Reo"]:
                group_label.grid(row=11, column=0, sticky="w", pady=5)
                group_entry.grid(row=11, column=1, pady=5)
            else:
                group_label.grid_remove()
                group_entry.grid_remove()

        turanga_var.trace("w", toggle_group_field)

        baptised_var = tk.StringVar(value="No")
        ttk.Label(frame, text="Baptised under the church?").grid(row=12, column=0, sticky="w", pady=5)
        ttk.Radiobutton(frame, text="Yes", variable=baptised_var, value="Yes").grid(row=12, column=1, sticky="w", padx=60)
        ttk.Radiobutton(frame, text="No", variable=baptised_var, value="No").grid(row=12, column=1, sticky="e", padx=60)

        upload_frame = ttk.LabelFrame(frame, text="Upload Photo / Documents")
        upload_frame.grid(row=13, column=0, columnspan=2, pady=10, sticky="ew")
        uploaded_files = []
        file_label = ttk.Label(upload_frame, text="No files selected")
        file_label.grid(row=0, column=0, padx=10, pady=5)

        def upload_file():
            path = filedialog.askopenfilename(title="Select Photo or Document")
            if path:
                fname = os.path.basename(path)
                dest = os.path.join(UPLOADS_FOLDER, f"pou_{datetime.now():%Y%m%d%H%M%S}_{fname}")
                with open(path, "rb") as s, open(dest, "wb") as d:
                    d.write(s.read())
                uploaded_files.append({"name": fname, "path": dest})
                file_label.config(text=f"{len(uploaded_files)} file(s) uploaded")

        ttk.Button(upload_frame, text="Upload File", command=upload_file).grid(row=0, column=1, padx=10)

        link_frame = ttk.LabelFrame(frame, text="Link Related Records")
        link_frame.grid(row=14, column=0, columnspan=2, pady=10, sticky="ew")
        linked_ids = []
        link_entry = ttk.Entry(link_frame, width=25)
        link_entry.grid(row=0, column=0, padx=5, pady=5)

        def add_link():
            link_id = link_entry.get().strip().upper()
            if not link_id: return
            if not get_record_by_id(link_id):
                messagebox.showerror("Error", "This ID does not exist")
                return
            if link_id in linked_ids:
                messagebox.showinfo("Info", "Already linked")
                return
            linked_ids.append(link_id)
            link_entry.delete(0, tk.END)
            messagebox.showinfo("Success", f"Linked to {link_id}")

        ttk.Button(link_frame, text="Add Link", command=add_link).grid(row=0, column=1, padx=5)
        ttk.Label(link_frame, text="Format: P-000001 / M-000001", foreground="gray").grid(row=0, column=2, padx=10)

        notes_frame = ttk.LabelFrame(frame, text="Initial Notes")
        notes_frame.grid(row=15, column=0, columnspan=2, pady=10, sticky="nsew")
        note_text = tk.Text(notes_frame, width=90, height=3)
        note_text.grid(row=0, column=0, padx=10, pady=5)

        def submit_pou():
            entered_id = id_entry.get().strip().upper()
            turanga_selected = turanga_var.get().strip()
            group_name = group_entry.get().strip() if group_entry else ""

            if not entered_id.startswith("P-") or len(entered_id) != 8 or not entered_id[2:].isdigit():
                messagebox.showerror("Invalid ID", "Format must be: P-000001")
                return
            if not is_id_unique(entered_id):
                messagebox.showerror("Duplicate ID", "ID already in use")
                return
            if not turanga_selected:
                messagebox.showerror("Missing Field", "Select a Turanga")
                return
            if turanga_selected in ["Mema o Nga Koea", "Mema o Nga Reo"] and not group_name:
                messagebox.showerror("Missing Field", "Enter Group Name")
                return

            notes_list = []
            note_content = note_text.get("1.0", tk.END).strip()
            if note_content:
                notes_list.append({
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "user": self.current_username,
                    "text": note_content
                })

            record = {
                "id": entered_id,
                "type": "POU",
                "name": name_entry.get().strip(),
                "last_name": last_name_entry.get().strip(),
                "email": email_entry.get().strip(),
                "phone": phone_entry.get().strip(),
                "address": address_entry.get().strip(),
                "pariha": pariha_entry.get().strip(),
                "takiwa": takiwa_entry.get().strip(),
                "turanga": turanga_selected,
                "group_name": group_name,
                "baptised": baptised_var.get(),
                "uploaded_files": uploaded_files,
                "notes": notes_list,
                "linked_ids": linked_ids
            }

            if not record["name"] or not record["last_name"]:
                messagebox.showerror("Error", "First and Last Name required")
                return

            save_record(POU_RECORDS_FILE, record)
            increment_id_counter(is_pou=True)
            messagebox.showinfo("Success", f"Registration saved!\nID: {entered_id}")
            self.show_main_menu()

        ttk.Button(frame, text="Submit Registration", command=submit_pou).grid(row=16, column=0, columnspan=2, pady=15)
        ttk.Button(frame, text="Back", command=self.show_main_menu).grid(row=17, column=0, columnspan=2)

    # --------------------------
    # New Morehu Form
    # --------------------------
    def show_morehu_form(self):
        self.clear_window()
        frame = ttk.Frame(self.root, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Morehu Registration Form", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=10)

        suggested_id = get_next_suggested_id(is_pou=False)
        ttk.Label(frame, text="Registration ID:", font=("Arial", 11, "bold")).grid(row=1, column=0, sticky="w", pady=8)
        id_entry = ttk.Entry(frame, width=48, font=("Arial", 11))
        id_entry.insert(0, suggested_id)
        id_entry.grid(row=1, column=1, pady=8)
        ttk.Label(frame, text="Format: M-000001", foreground="gray").grid(row=2, column=1, sticky="w")

        ttk.Label(frame, text="First Name:").grid(row=3, column=0, sticky="w", pady=5)
        name_entry = ttk.Entry(frame, width=48)
        name_entry.grid(row=3, column=1, pady=5)

        ttk.Label(frame, text="Last Name:").grid(row=4, column=0, sticky="w", pady=5)
        last_name_entry = ttk.Entry(frame, width=48)
        last_name_entry.grid(row=4, column=1, pady=5)

        ttk.Label(frame, text="Email:").grid(row=5, column=0, sticky="w", pady=5)
        email_entry = ttk.Entry(frame, width=48)
        email_entry.grid(row=5, column=1, pady=5)

        ttk.Label(frame, text="Phone:").grid(row=6, column=0, sticky="w", pady=5)
        phone_entry = ttk.Entry(frame, width=48)
        phone_entry.grid(row=6, column=1, pady=5)

        ttk.Label(frame, text="Address:").grid(row=7, column=0, sticky="w", pady=5)
        address_entry = ttk.Entry(frame, width=48)
        address_entry.grid(row=7, column=1, pady=5)

        ttk.Label(frame, text="Current Pariha:").grid(row=8, column=0, sticky="w", pady=5)
        pariha_entry = ttk.Entry(frame, width=48)
        pariha_entry.grid(row=8, column=1, pady=5)

        ttk.Label(frame, text="Current Takiwa:").grid(row=9, column=0, sticky="w", pady=5)
        takiwa_entry = ttk.Entry(frame, width=48)
        takiwa_entry.grid(row=9, column=1, pady=5)

        baptised_var = tk.StringVar(value="No")
        ttk.Label(frame, text="Baptised under the church?").grid(row=10, column=0, sticky="w", pady=5)
        ttk.Radiobutton(frame, text="Yes", variable=baptised_var, value="Yes").grid(row=10, column=1, sticky="w", padx=60)
        ttk.Radiobutton(frame, text="No", variable=baptised_var, value="No").grid(row=10, column=1, sticky="e", padx=60)

        upload_frame = ttk.LabelFrame(frame, text="Upload Photo / Documents")
        upload_frame.grid(row=11, column=0, columnspan=2, pady=10, sticky="ew")
        uploaded_files = []
        file_label = ttk.Label(upload_frame, text="No files selected")
        file_label.grid(row=0, column=0, padx=10, pady=5)

        def upload_file():
            path = filedialog.askopenfilename(title="Select Photo or Document")
            if path:
                fname = os.path.basename(path)
                dest = os.path.join(UPLOADS_FOLDER, f"morehu_{datetime.now():%Y%m%d%H%M%S}_{fname}")
                with open(path, "rb") as s, open(dest, "wb") as d:
                    d.write(s.read())
                uploaded_files.append({"name": fname, "path": dest})
                file_label.config(text=f"{len(uploaded_files)} file(s) uploaded")

        ttk.Button(upload_frame, text="Upload File", command=upload_file).grid(row=0, column=1, padx=10)

        link_frame = ttk.LabelFrame(frame, text="Link Related Records")
        link_frame.grid(row=12, column=0, columnspan=2, pady=10, sticky="ew")
        linked_ids = []
        link_entry = ttk.Entry(link_frame, width=25)
        link_entry.grid(row=0, column=0, padx=5, pady=5)

        def add_link():
            link_id = link_entry.get().strip().upper()
            if not link_id: return
            if not get_record_by_id(link_id):
                messagebox.showerror("Error", "This ID does not exist")
                return
            if link_id in linked_ids:
                messagebox.showinfo("Info", "Already linked")
                return
            linked_ids.append(link_id)
            link_entry.delete(0, tk.END)
            messagebox.showinfo("Success", f"Linked to {link_id}")

        ttk.Button(link_frame, text="Add Link", command=add_link).grid(row=0, column=1, padx=5)
        ttk.Label(link_frame, text="Format: P-000001 / M-000001", foreground="gray").grid(row=0, column=2, padx=10)

        notes_frame = ttk.LabelFrame(frame, text="Initial Notes")
        notes_frame.grid(row=13, column=0, columnspan=2, pady=10, sticky="nsew")
        note_text = tk.Text(notes_frame, width=90, height=3)
        note_text.grid(row=0, column=0, padx=10, pady=5)

        def submit_morehu():
            entered_id = id_entry.get().strip().upper()

            if not entered_id.startswith("M-") or len(entered_id) != 8 or not entered_id[2:].isdigit():
                messagebox.showerror("Invalid ID", "Format must be: M-000001")
                return
            if not is_id_unique(entered_id):
                messagebox.showerror("Duplicate ID", "ID already in use")
                return

            notes_list = []
            note_content = note_text.get("1.0", tk.END).strip()
            if note_content:
                notes_list.append({
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "user": self.current_username,
                    "text": note_content
                })

            record = {
                "id": entered_id,
                "type": "Morehu",
                "name": name_entry.get().strip(),
                "last_name": last_name_entry.get().strip(),
                "email": email_entry.get().strip(),
                "phone": phone_entry.get().strip(),
                "address": address_entry.get().strip(),
                "pariha": pariha_entry.get().strip(),
                "takiwa": takiwa_entry.get().strip(),
                "baptised": baptised_var.get(),
                "uploaded_files": uploaded_files,
                "notes": notes_list,
                "linked_ids": linked_ids
            }

            if not record["name"] or not record["last_name"]:
                messagebox.showerror("Error", "First and Last Name required")
                return

            save_record(MOREHU_RECORDS_FILE, record)
            increment_id_counter(is_pou=False)
            messagebox.showinfo("Success", f"Registration saved!\nID: {entered_id}")
            self.show_main_menu()

        ttk.Button(frame, text="Submit Registration", command=submit_morehu).grid(row=14, column=0, columnspan=2, pady=15)
        ttk.Button(frame, text="Back", command=self.show_main_menu).grid(row=15, column=0, columnspan=2)

    # --------------------------
    # View / Edit Records with ID Card Generator
    # --------------------------
    def show_record_selection(self):
        self.clear_window()
        frame = ttk.Frame(self.root, padding=30)
        frame.pack(expand=True)
        ttk.Label(frame, text="Select Record Type", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=20)
        ttk.Button(frame, text="POU Records", width=28, command=lambda: self.show_record_list(POU_RECORDS_FILE)).grid(row=1, column=0, padx=20, pady=10)
        ttk.Button(frame, text="Morehu Records", width=28, command=lambda: self.show_record_list(MOREHU_RECORDS_FILE)).grid(row=1, column=1, padx=20, pady=10)
        ttk.Button(frame, text="Back", width=28, command=self.show_main_menu).grid(row=2, column=0, columnspan=2, pady=20)

    def show_record_list(self, file_path):
        self.clear_window()
        frame = ttk.Frame(self.root, padding=20)
        frame.pack(fill="both", expand=True)
        records = load_records(file_path)
        record_type = "POU" if file_path == POU_RECORDS_FILE else "Morehu"
        ttk.Label(frame, text=f"{record_type} Records", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=10)

        listbox = tk.Listbox(frame, width=95, height=18, font=("Arial", 10))
        listbox.grid(row=1, column=0, columnspan=2, padx=10, pady=10)
        for idx, rec in enumerate(records):
            listbox.insert(tk.END, f"{rec.get('id')} | {rec.get('name','')} {rec.get('last_name','')} | {rec.get('turanga', '')}")

        def open():
            sel = listbox.curselection()
            if sel:
                self.edit_existing_record(file_path, sel[0])
            else:
                messagebox.showwarning("Warning", "Select a record")

        ttk.Button(frame, text="Open Record", command=open).grid(row=2, column=0, padx=10, pady=10)
        ttk.Button(frame, text="Back", command=self.show_record_selection).grid(row=2, column=1, padx=10, pady=10)

    def edit_existing_record(self, file_path, index):
        self.clear_window()
        frame = ttk.Frame(self.root, padding=20)
        frame.pack(fill="both", expand=True)
        records = load_records(file_path)
        record = records[index]
        is_pou = record.get("type") == "POU"

        ttk.Label(frame, text=f"Edit Record: {record.get('id')}", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=10)

        ttk.Label(frame, text="Registration ID:").grid(row=1, column=0, sticky="w", pady=5)
        id_entry = ttk.Entry(frame, width=48)
        id_entry.insert(0, record.get("id", ""))
        id_entry.grid(row=1, column=1, pady=5)

        ttk.Label(frame, text="First Name:").grid(row=2, column=0, sticky="w", pady=5)
        name_entry = ttk.Entry(frame, width=48)
        name_entry.insert(0, record.get("name", ""))
        name_entry.grid(row=2, column=1, pady=5)

        ttk.Label(frame, text="Last Name:").grid(row=3, column=0, sticky="w", pady=5)
        last_name_entry = ttk.Entry(frame, width=48)
        last_name_entry.insert(0, record.get("last_name", ""))
        last_name_entry.grid(row=3, column=1, pady=5)

        ttk.Label(frame, text="Email:").grid(row=4, column=0, sticky="w", pady=5)
        email_entry = ttk.Entry(frame, width=48)
        email_entry.insert(0, record.get("email", ""))
        email_entry.grid(row=4, column=1, pady=5)

        ttk.Label(frame, text="Phone:").grid(row=5, column=0, sticky="w", pady=5)
        phone_entry = ttk.Entry(frame, width=48)
        phone_entry.insert(0, record.get("phone", ""))
        phone_entry.grid(row=5, column=1, pady=5)

        ttk.Label(frame, text="Address:").grid(row=6, column=0, sticky="w", pady=5)
        address_entry = ttk.Entry(frame, width=48)
        address_entry.insert(0, record.get("address", ""))
        address_entry.grid(row=6, column=1, pady=5)

        ttk.Label(frame, text="Current Pariha:").grid(row=7, column=0, sticky="w", pady=5)
        pariha_entry = ttk.Entry(frame, width=48)
        pariha_entry.insert(0, record.get("pariha", ""))
        pariha_entry.grid(row=7, column=1, pady=5)

        ttk.Label(frame, text="Current Takiwa:").grid(row=8, column=0, sticky="w", pady=5)
        takiwa_entry = ttk.Entry(frame, width=48)
        takiwa_entry.insert(0, record.get("takiwa", ""))
        takiwa_entry.grid(row=8, column=1, pady=5)

        turanga_var = None
        group_entry = None
        group_label = None
        if is_pou:
            ttk.Label(frame, text="Turanga:").grid(row=9, column=0, sticky="w", pady=5)
            turanga_var = tk.StringVar(value=record.get("turanga", ""))
            turanga_dropdown = ttk.Combobox(frame, textvariable=turanga_var, values=TURANGA_OPTIONS, state="readonly", width=45)
            turanga_dropdown.grid(row=9, column=1, pady=5)

            group_label = ttk.Label(frame, text="Group Name:")
            group_entry = ttk.Entry(frame, width=48)
            saved_group = record.get("group_name", "")

            def toggle_group_edit(*args):
                selected = turanga_var.get()
                if selected in ["Mema o Nga Koea", "Mema o Nga Reo"]:
                    group_label.grid(row=10, column=0, sticky="w", pady=5)
                    group_entry.grid(row=10, column=1, pady=5)
                    if saved_group:
                        group_entry.delete(0, tk.END)
                        group_entry.insert(0, saved_group)
                else:
                    group_label.grid_remove()
                    group_entry.grid_remove()

            toggle_group_edit()
            turanga_var.trace("w", toggle_group_edit)
            baptised_row = 11
        else:
            baptised_row = 9

        baptised_var = tk.StringVar(value=record.get("baptised", "No"))
        ttk.Label(frame, text="Baptised under the church?").grid(row=baptised_row, column=0, sticky="w", pady=5)
        ttk.Radiobutton(frame, text="Yes", variable=baptised_var, value="Yes").grid(row=baptised_row, column=1, sticky="w", padx=60)
        ttk.Radiobutton(frame, text="No", variable=baptised_var, value="No").grid(row=baptised_row, column=1, sticky="e", padx=60)

        linked_ids = record.get("linked_ids", [])
        link_frame = ttk.LabelFrame(frame, text="Linked Records")
        link_frame.grid(row=baptised_row+1, column=0, columnspan=2, pady=10, sticky="ew")
        linked_list = tk.Listbox(link_frame, width=35, height=3)
        linked_list.grid(row=0, column=0, padx=10, pady=5)
        for lid in linked_ids:
            linked_list.insert(tk.END, lid)

        def open_linked():
            sel = linked_list.curselection()
            if not sel: return
            link_id = linked_list.get(sel[0])
            rec_info = get_record_by_id(link_id)
            if rec_info:
                if messagebox.askyesno("Open Linked Record", "Unsaved changes will be lost. Continue?"):
                    self.edit_existing_record(rec_info["file"], rec_info["index"])

        def add_new_link():
            link_id = simpledialog.askstring("Add Link", "Enter record ID:")
            if not link_id: return
            link_id = link_id.strip().upper()
            if not get_record_by_id(link_id):
                messagebox.showerror("Error", "ID not found")
                return
            if link_id in linked_ids:
                messagebox.showinfo("Info", "Already linked")
                return
            linked_ids.append(link_id)
            linked_list.insert(tk.END, link_id)

        ttk.Button(link_frame, text="Open Selected", command=open_linked).grid(row=0, column=1, padx=5)
        ttk.Button(link_frame, text="Add New Link", command=add_new_link).grid(row=0, column=2, padx=5)

        uploaded_files = record.get("uploaded_files", [])
        file_frame = ttk.LabelFrame(frame, text="Upload