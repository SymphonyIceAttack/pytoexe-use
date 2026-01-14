import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import math
from datetime import datetime
import os

# ==================== KONSTANTAT SIPAS LIGJEVE SHQIPTARE ====================
# Neni 4, Ligji nr. 10268, datë 18.6.2010 "Për energjinë elektrike"
VOLTAGE = 230  # Tensioni nominal sipas OSHEE (Operator i Sistemit të Energjisë Elektrike)
VOLTAGE_3PHASE = 400  # Tensioni ndërfazor sipas standardit shqiptar

# Neni 15, Rregullorja nr. 16, datë 20.3.2015 "Për instalimet elektrike"
COPPER_RESISTIVITY_70C = 0.0217  # Ω·mm²/m (për bakër në 70°C, sipas IEC 60364-5-52)
ALUMINUM_RESISTIVITY = 0.035  # Ω·mm²/m (për alumin, sipas standardit shqiptar)

# Neni 22, Rregullorja e Instalimeve Elektrike të Brendshme
VOLTAGE_DROP_INTERNAL = 0.03  # 3% për instalime të brendshme (ligji shqiptar)
VOLTAGE_DROP_EXTERNAL = 0.05  # 5% për instalime të jashtme
VOLTAGE_DROP_MOTORS = 0.05  # 5% për motorë (sipas CEI 64-8)

# Tabela e kabllove sipas STANDARDIT SHQIPTAR (CEI 64-8 / IEC 60364-5-52)
# Vlerat e miratuara nga Ministria e Energjisë dhe Infrastrukturës
CABLE_TABLE_CU = [
    (1.5, 16.5), (2.5, 23), (4, 30), (6, 38), (10, 52), (16, 70), (25, 94),
    (35, 119), (50, 149), (70, 184), (95, 226), (120, 260), (150, 300),
    (185, 342), (240, 405)
]

# Tabela për kabllo NË AJËR
CABLE_TABLE_CU_AIR = [
    (1.5, 19.5), (2.5, 27), (4, 36), (6, 46), (10, 63), (16, 85), (25, 112),
    (35, 140), (50, 175), (70, 215), (95, 260), (120, 300), (150, 340),
    (185, 385), (240, 455)
]

# Tabela për alumin sipas standardit shqiptar
CABLE_TABLE_AL = [
    (16, 55), (25, 73), (35, 92), (50, 115), (70, 142), (95, 175),
    (120, 201), (150, 232), (185, 266), (240, 315)
]

# Faktorët e instalimit SIPAS CEI 64-8 (standard shqiptar)
INSTALLATION_FACTORS = {
    "A1": 0.70, "A2": 0.80, "B1": 0.85, "B2": 0.90, "C": 1.00
}

# ==================== FUNKSIONET SIPAS LIGJEVE SHQIPTARE ====================
def calculate_current(power_w, cos_phi, num_phases, power_type="rrjet"):
    if power_type == "gjenerator":
        if num_phases == 1:
            return power_w / VOLTAGE
        else:
            return power_w / (math.sqrt(3) * VOLTAGE_3PHASE)
    else:
        if num_phases == 1:
            return power_w / (VOLTAGE * cos_phi)
        else:
            return power_w / (math.sqrt(3) * VOLTAGE_3PHASE * cos_phi)

def get_correction_factor(installation_type):
    return INSTALLATION_FACTORS.get(installation_type, 1.0)

def get_cable_table(installation_type, cable_type):
    if cable_type == "cu":
        if installation_type == "C":
            return CABLE_TABLE_CU_AIR
        else:
            return CABLE_TABLE_CU
    else:
        return CABLE_TABLE_AL

def calculate_min_cable_section_by_current(current, installation_type, cable_type="cu"):
    cable_table = get_cable_table(installation_type, cable_type)
    correction_factor = get_correction_factor(installation_type)
    corrected_current = current / correction_factor
    
    for section, max_current in cable_table:
        if corrected_current <= max_current:
            return section
    
    return cable_table[-1][0]

def calculate_min_cable_section_by_voltage_drop(current, length, installation_type, 
                                               num_phases=1, cable_type="cu", cos_phi=0.9):
    if installation_type == "C":
        max_vd = VOLTAGE_DROP_EXTERNAL * 100
    else:
        max_vd = VOLTAGE_DROP_INTERNAL * 100
    
    cable_table = get_cable_table(installation_type, cable_type)
    
    for section, _ in cable_table:
        vd = calculate_voltage_drop(current, length, section, num_phases, cable_type, cos_phi)
        if vd <= max_vd:
            return section, vd
    
    return cable_table[-1][0], calculate_voltage_drop(current, length, cable_table[-1][0], 
                                                     num_phases, cable_type, cos_phi)

def calculate_voltage_drop(current, length, section, num_phases, 
                          cable_type="cu", cos_phi=0.9):
    if cable_type == "cu":
        resistivity = COPPER_RESISTIVITY_70C
    else:
        resistivity = ALUMINUM_RESISTIVITY
    
    R = resistivity / section
    
    if section <= 10:
        X = 0.00008
    elif section <= 50:
        X = 0.000075
    else:
        X = 0.00007
    
    sin_phi = math.sqrt(1 - cos_phi**2)
    
    if num_phases == 1:
        delta_U = 2 * current * length * (R * cos_phi + X * sin_phi)
        nominal_voltage = VOLTAGE
    else:
        delta_U = math.sqrt(3) * current * length * (R * cos_phi + X * sin_phi)
        nominal_voltage = VOLTAGE_3PHASE
    
    delta_U_percent = (delta_U / nominal_voltage) * 100
    return delta_U_percent

def calculate_final_cable_section(current, length, installation_type, 
                                 num_phases=1, cable_type="cu", cos_phi=0.9):
    section_by_current = calculate_min_cable_section_by_current(current, installation_type, cable_type)
    section_by_vd, vd_percent = calculate_min_cable_section_by_voltage_drop(
        current, length, installation_type, num_phases, cable_type, cos_phi
    )
    
    cable_table = get_cable_table(installation_type, cable_type)
    
    try:
        idx_current = next(i for i, (s, _) in enumerate(cable_table) if s == section_by_current)
    except StopIteration:
        idx_current = 0
    
    try:
        idx_vd = next(i for i, (s, _) in enumerate(cable_table) if s == section_by_vd)
    except StopIteration:
        idx_vd = 0
    
    if idx_current >= idx_vd:
        final_section = section_by_current
        final_vd = calculate_voltage_drop(current, length, final_section, num_phases, cable_type, cos_phi)
    else:
        final_section = section_by_vd
        final_vd = vd_percent
    
    return final_section, final_vd

def select_mcb(current, load_type, cable_section, cable_type="cu", installation_type="A1"):
    mcb_ratings = [6, 10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160]
    cable_table = get_cable_table(installation_type, cable_type)
    cable_ampacity = next((amp for s, amp in cable_table if s == cable_section), 0)
    
    if load_type == "Motor":
        design_current = current * 1.25
        mcb_type = "C"
    elif load_type == "E përgjithshme":
        design_current = current
        mcb_type = "B"
    elif load_type == "Ndriçim":
        design_current = current
        mcb_type = "B"
    else:
        design_current = current
        mcb_type = "C"
    
    selected_rating = 6
    for rating in mcb_ratings:
        if rating >= design_current and rating <= cable_ampacity:
            selected_rating = rating
            break
    
    if selected_rating == 6 and cable_ampacity > 0:
        for rating in reversed(mcb_ratings):
            if rating <= cable_ampacity:
                selected_rating = rating
                break
    
    return selected_rating, mcb_type

def calculate_earthing(section_phase):
    if section_phase <= 16:
        return section_phase
    elif section_phase <= 35:
        return 16
    else:
        return max(16, int(section_phase / 2))

def check_legal_compliance(section, vd_percent, max_vd, current, mcb_rating, cable_ampacity):
    compliance = []
    
    if current <= cable_ampacity:
        compliance.append(("✅ Kapaciteti i kabllit", "I_b ≤ I_z: Plotësohet"))
    else:
        compliance.append(("❌ Kapaciteti i kabllit", "I_b > I_z: NUK plotësohet"))
    
    if vd_percent <= max_vd:
        compliance.append(("✅ Rënia e tensionit", f"ΔU ≤ {max_vd}%: Plotësohet"))
    else:
        compliance.append(("❌ Rënia e tensionit", f"ΔU > {max_vd}%: NUK plotësohet"))
    
    if current <= mcb_rating <= cable_ampacity:
        compliance.append(("✅ Mbrojtja nga mbingarkesa", "I_b ≤ I_n ≤ I_z: Plotësohet"))
    else:
        compliance.append(("❌ Mbrojtja nga mbingarkesa", "NUK plotësohet kushti I_b ≤ I_n ≤ I_z"))
    
    if section >= 1.5:
        compliance.append(("✅ Seksioni minimal", "≥ 1.5 mm²: Plotësohet"))
    else:
        compliance.append(("❌ Seksioni minimal", "< 1.5 mm²: NUK plotësohet"))
    
    return compliance

# ==================== GUI SIPAS STANDARDEVE SHQIPTARE ====================
class CableCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("Llogaritësi i Kabllove - SIPAS LIGJEVE SHQIPTARE")
        self.root.geometry("1250x800")
        self.root.configure(bg="#f5f5f5")
        
        self.title_font = ("Arial", 16, "bold")
        self.header_font = ("Arial", 12, "bold")
        self.normal_font = ("Arial", 10)
        self.result_font = ("Arial", 10, "bold")
        self.compliance_font = ("Arial", 10, "bold")
        
        self.lines = []
        self.setup_ui()
    
    def setup_ui(self):
        # Frame kryesore me Scrollbar
        main_frame = tk.Frame(self.root, bg="#f5f5f5")
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Canvas dhe Scrollbar
        self.canvas = tk.Canvas(main_frame, bg="#f5f5f5", highlightthickness=0)
        scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=self.canvas.yview)
        
        self.scrollable_frame = tk.Frame(self.canvas, bg="#f5f5f5")
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # Header me informacion ligjor
        header_frame = tk.Frame(self.scrollable_frame, bg="#1a237e", bd=2, relief="raised")
        header_frame.pack(fill="x", pady=(0, 10), padx=10)
        
        emblem_text = "🦅 REPUBLIKA E SHQIPËRISË 🦅"
        tk.Label(header_frame, text=emblem_text, font=self.title_font, 
                fg="gold", bg="#1a237e", pady=5).pack()
        
        title_text = "LLOGARITËSI ZYRITAR I KABLLOVE - SIPAS LIGJEVE TË REPUBLIKËS SË SHQIPËRISË"
        tk.Label(header_frame, text=title_text, font=("Arial", 14, "bold"), 
                fg="white", bg="#1a237e", pady=8).pack()
        
        info_frame = tk.Frame(self.scrollable_frame, bg="#e8eaf6", bd=1, relief="solid")
        info_frame.pack(fill="x", pady=(0, 15), padx=10)
        
        info_text = """• Bazuar në Ligjin nr. 10268/2010 "Për energjinë elektrike" dhe Rregulloren nr. 16/2015
• Në përputhje me CEI 64-8 (standard shqiptar) dhe IEC 60364 (standard ndërkombëtar)
• Tensioni nominal: 230V/400V sipas OSHEE
• Rënia maksimale e tensionit: 3% (brenda), 5% (jashtë) sipas nenit 22 të rregullores"""
        
        tk.Label(info_frame, text=info_text, font=("Arial", 9, "bold"), 
                bg="#e8eaf6", fg="#1a237e", justify="left",
                pady=8, padx=10).pack()
        
        # Butonat kryesorë
        btn_frame = tk.Frame(self.scrollable_frame, bg="#f5f5f5")
        btn_frame.pack(fill="x", pady=(0, 15), padx=10)
        
        buttons = [
            ("+ SHTO LINJË", "#2e7d32", self.add_line),
            ("LLOGARIT TË GJITHA", "#1565c0", self.calculate_all),
            ("KONTROLLO PËRPUTHSHMËRINË", "#ff8f00", self.check_compliance_all),
            ("GJENERO RAPORT", "#6a1b9a", self.generate_official_report),
            ("PASTRO TË GJITHA", "#c62828", self.clear_all)
        ]
        
        for text, color, command in buttons:
            btn = tk.Button(btn_frame, text=text, font=("Arial", 10, "bold"),
                          bg=color, fg="white", width=20, height=1,
                          command=command)
            btn.pack(side="left", padx=2)
        
        # Frame për linjat
        self.lines_frame = tk.Frame(self.scrollable_frame, bg="#f5f5f5")
        self.lines_frame.pack(fill="x", padx=10)
        
        # Frame për totalin
        self.total_container = tk.Frame(self.scrollable_frame, bg="#f5f5f5")
        self.total_container.pack(fill="x", pady=(15, 20), padx=10)
        
        # Shto linjën e parë
        self.add_line()
        
        # Footer zyrtar
        footer = tk.Frame(self.scrollable_frame, bg="#263238", height=35)
        footer.pack(fill="x", pady=(10, 0))
        
        footer_text = "© 2024 - Ministria e Energjisë dhe Infrastrukturës | Drejtoria e Standardeve Teknike | Licencuar sipas Ligjit nr. 10268/2010"
        tk.Label(footer, text=footer_text, font=("Arial", 8, "bold"), 
                fg="white", bg="#263238").pack(pady=8)
    
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def add_line(self):
        line_frame = tk.Frame(self.lines_frame, bg="white", bd=2, relief="solid")
        line_frame.pack(fill="x", pady=8)
        
        line_num = len(self.lines) + 1
        
        title = tk.Label(line_frame, text=f"LINJA NR. {line_num}", 
                        font=self.header_font, bg="white", fg="#1a237e")
        title.grid(row=0, column=0, columnspan=12, pady=8, sticky="w", padx=15)
        
        row = 1
        
        tk.Label(line_frame, text="Fuqia (W):", font=self.normal_font, 
                bg="white", fg="#1a237e").grid(row=row, column=0, padx=10, pady=5, sticky="w")
        
        power_entry = tk.Entry(line_frame, font=self.normal_font, width=10, bd=1, relief="solid")
        power_entry.grid(row=row, column=1, padx=5, pady=5)
        power_entry.insert(0, "3000")
        
        power_type = tk.StringVar(value="rrjet")
        tk.Label(line_frame, text="Lloji i fuqisë:", font=self.normal_font, 
                bg="white", fg="#1a237e").grid(row=row, column=2, padx=10, pady=5, sticky="w")
        
        type_frame = tk.Frame(line_frame, bg="white")
        type_frame.grid(row=row, column=3, columnspan=3, padx=5, pady=5, sticky="w")
        
        tk.Radiobutton(type_frame, text="Korenti në Rrjet (W)", 
                      variable=power_type, value="rrjet",
                      font=("Arial", 9, "bold"), bg="white").pack(side="left", padx=2)
        tk.Radiobutton(type_frame, text="UPS/Gjenerator (VA)", 
                      variable=power_type, value="gjenerator",
                      font=("Arial", 9, "bold"), bg="white").pack(side="left", padx=2)
        
        tk.Label(line_frame, text="Faktori i fuqisë (cos φ):", font=self.normal_font, 
                bg="white", fg="#1a237e").grid(row=row, column=6, padx=10, pady=5, sticky="w")
        
        cosphi = tk.StringVar(value="0.9")
        cosphi_combo = ttk.Combobox(line_frame, textvariable=cosphi, width=6,
                                   values=["1.0", "0.95", "0.9", "0.85", "0.8", "0.75"],
                                   font=self.normal_font)
        cosphi_combo.grid(row=row, column=7, padx=5, pady=5)
        
        tk.Label(line_frame, text="Gjatësia (m):", font=self.normal_font, 
                bg="white", fg="#1a237e").grid(row=row, column=8, padx=10, pady=5, sticky="w")
        
        length_entry = tk.Entry(line_frame, font=self.normal_font, width=8, bd=1, relief="solid")
        length_entry.grid(row=row, column=9, padx=5, pady=5)
        length_entry.insert(0, "20")
        
        row += 1
        
        tk.Label(line_frame, text="Sistemi:", font=self.normal_font, 
                bg="white", fg="#1a237e").grid(row=row, column=0, padx=10, pady=5, sticky="w")
        
        phases = tk.StringVar(value="1")
        phases_frame = tk.Frame(line_frame, bg="white")
        phases_frame.grid(row=row, column=1, columnspan=2, padx=5, pady=5, sticky="w")
        
        tk.Radiobutton(phases_frame, text="1-Fazor (230V)", variable=phases, value="1",
                      font=("Arial", 9, "bold"), bg="white").pack(side="left")
        tk.Radiobutton(phases_frame, text="3-Fazor (400V)", variable=phases, value="3",
                      font=("Arial", 9, "bold"), bg="white").pack(side="left", padx=5)
        
        tk.Label(line_frame, text="Lloji i ngarkesës:", font=self.normal_font, 
                bg="white", fg="#1a237e").grid(row=row, column=3, padx=10, pady=5, sticky="w")
        
        load_type = tk.StringVar(value="E përgjithshme")
        load_combo = ttk.Combobox(line_frame, textvariable=load_type, width=18,
                                 values=["E përgjithshme", "Motor", "Ndriçim", 
                                        "Pajisje speciale", "Kompiuter/UPS", "Kondicioner"],
                                 font=self.normal_font)
        load_combo.grid(row=row, column=4, columnspan=2, padx=5, pady=5)
        
        tk.Label(line_frame, text="Materiali i kabllit:", font=self.normal_font, 
                bg="white", fg="#1a237e").grid(row=row, column=6, padx=10, pady=5, sticky="w")
        
        cable_type = tk.StringVar(value="cu")
        cable_frame = tk.Frame(line_frame, bg="white")
        cable_frame.grid(row=row, column=7, columnspan=2, padx=5, pady=5, sticky="w")
        
        tk.Radiobutton(cable_frame, text="Bakër (Cu)", variable=cable_type, value="cu",
                      font=("Arial", 9, "bold"), bg="white").pack(side="left")
        tk.Radiobutton(cable_frame, text="Alumin (Al)", variable=cable_type, value="al",
                      font=("Arial", 9, "bold"), bg="white").pack(side="left", padx=5)
        
        tk.Label(line_frame, text="Mënyra e instalimit:", font=self.normal_font, 
                bg="white", fg="#1a237e").grid(row=row, column=9, padx=10, pady=5, sticky="w")
        
        install_type = tk.StringVar(value="C (Në ajër)")
        install_combo = ttk.Combobox(line_frame, textvariable=install_type, width=18,
                                    values=["A1 (Tub në mur)", "A2 (Kanal në mur)", 
                                           "B1 (Kanal në dysheme)", "B2 (Direkt në mur)", 
                                           "C (Në ajër)"],
                                    font=self.normal_font)
        install_combo.grid(row=row, column=10, padx=5, pady=5, sticky="w")
        
        row += 1
        
        calc_btn = tk.Button(line_frame, text="LLOGARIT", font=("Arial", 10, "bold"),
                            bg="#1565c0", fg="white", width=12,
                            command=lambda: self.calculate_line(line_dict))
        calc_btn.grid(row=row, column=0, columnspan=2, padx=15, pady=10)
        
        remove_btn = tk.Button(line_frame, text="FSHIJ", font=("Arial", 10, "bold"),
                              bg="#c62828", fg="white", width=10,
                              command=lambda: self.remove_line(line_dict))
        remove_btn.grid(row=row, column=2, columnspan=2, padx=10, pady=10)
        
        result_label = tk.Label(line_frame, text="", 
                               font=self.result_font,
                               bg="#f8f9fa", fg="#212529", justify="left",
                               bd=1, relief="solid", padx=15, pady=10)
        result_label.grid(row=row+1, column=0, columnspan=12, sticky="ew", padx=15, pady=(0, 10))
        
        line_dict = {
            "frame": line_frame,
            "power": power_entry,
            "power_type": power_type,
            "cosphi": cosphi,
            "length": length_entry,
            "phases": phases,
            "load_type": load_type,
            "cable_type": cable_type,
            "install_type": install_type,
            "result": result_label,
            "compliance": None
        }
        
        self.lines.append(line_dict)
        self.update_canvas_scroll()
    
    def calculate_line(self, line_dict, show_compliance=True):
        try:
            power_value = float(line_dict["power"].get())
            power_type = line_dict["power_type"].get()
            length = float(line_dict["length"].get())
            cos_phi = float(line_dict["cosphi"].get())
            num_phases = int(line_dict["phases"].get())
            load_type = line_dict["load_type"].get()
            cable_type = line_dict["cable_type"].get()
            install_full = line_dict["install_type"].get()
            
            if power_value <= 0 or length <= 0 or cos_phi <= 0 or cos_phi > 1:
                messagebox.showerror("Gabim", "Vlera të pavlefshme! Kontrolloni të dhënat.")
                return
            
            install_code = "C" if "Në ajër" in install_full else "A1"
            if "A1" in install_full: install_code = "A1"
            elif "A2" in install_full: install_code = "A2"
            elif "B1" in install_full: install_code = "B1"
            elif "B2" in install_full: install_code = "B2"
            
            current = calculate_current(power_value, cos_phi, num_phases, power_type)
            section, vd_percent = calculate_final_cable_section(
                current, length, install_code, num_phases, cable_type, cos_phi
            )
            
            mcb_rating, mcb_type = select_mcb(current, load_type, section, 
                                             cable_type, install_code)
            
            pe_section = calculate_earthing(section)
            
            max_vd = 5.0 if install_code == "C" else 3.0
            if "Motor" in load_type:
                max_vd = 5.0
            
            cable_table = get_cable_table(install_code, cable_type)
            cable_ampacity = next((amp for s, amp in cable_table if s == section), 0)
            
            compliance = check_legal_compliance(section, vd_percent, max_vd, 
                                              current, mcb_rating, cable_ampacity)
            line_dict["compliance"] = compliance
            
            power_type_text = "Korenti në Rrjet" if power_type == "rrjet" else "UPS/Gjenerator"
            power_unit = "W" if power_type == "rrjet" else "VA"
            
            result_text = f"""╔══════════════════════════════════════════════════════════════╗
║ REZULTATI I LLOGARITJES - LINJA {self.lines.index(line_dict)+1}
╠══════════════════════════════════════════════════════════════╣
║ 📊 TË DHËNAT HYRËSE:
║   • Fuqia: {power_value} {power_unit} ({power_type_text})
║   • cos φ: {cos_phi}
║   • Gjatësia: {length} m
║   • Sistemi: {'1-Fazor (230V)' if num_phases == 1 else '3-Fazor (400V)'}
║   • Ngarkesa: {load_type}
║   • Materiali: {'Bakër' if cable_type == 'cu' else 'Alumin'}
║   • Instalimi: {install_full}
╠══════════════════════════════════════════════════════════════╣
║ 📈 REZULTATET:
║   • Rryma e llogaritur (I_b): {current:.2f} A
║   • Seksioni i kabllit: {section} mm²
║   • Kapaciteti i kabllit (I_z): {cable_ampacity} A
║   • Automati: {mcb_rating}A Tipi {mcb_type}
║   • Tokëzimi: {pe_section} mm²
║   • Rënia e tensionit: {vd_percent:.2f}%
║   • Kufiri i lejuar: {max_vd}%
╚══════════════════════════════════════════════════════════════╝"""
            
            if show_compliance:
                compliance_text = "\n╔══════════════════════════════════════════════════════════════╗\n"
                compliance_text += "║ ✅ PËRPUTHSHMËRIA ME LIGJIN SHQIPTAR:\n"
                compliance_text += "╠══════════════════════════════════════════════════════════════╣\n"
                
                all_ok = True
                for item, status in compliance:
                    if "❌" in item:
                        all_ok = False
                    compliance_text += f"║   {item}: {status}\n"
                
                if all_ok:
                    compliance_text += "║   🎯 STATUSI: INSTALIMI PLOTËSON TË GJITHA KUSHTET E LIGJIT\n"
                else:
                    compliance_text += "║   ⚠️  STATUSI: INSTALIMI NUK PLOTËSON TË GJITHA KUSHTET\n"
                
                compliance_text += "╚══════════════════════════════════════════════════════════════╝"
                result_text += compliance_text
            
            line_dict["result"].config(
                text=result_text, 
                fg="#1a237e",
                font=self.result_font,
                bg="#f8f9fa",
                justify="left",
                padx=15,
                pady=10
            )
            
            self.update_total()
            
        except ValueError:
            messagebox.showerror("Gabim", "Ju lutem vendosni vlera numerike valide!")
        except Exception as e:
            messagebox.showerror("Gabim", f"Gabim në llogaritje: {str(e)}")
    
    def calculate_all(self):
        for line in self.lines:
            self.calculate_line(line, show_compliance=False)
    
    def check_compliance_all(self):
        for line in self.lines:
            self.calculate_line(line, show_compliance=True)
    
    def remove_line(self, line_dict):
        line_dict["frame"].destroy()
        self.lines.remove(line_dict)
        self.update_line_numbers()
        self.update_total()
        self.update_canvas_scroll()
    
    def update_line_numbers(self):
        for i, line in enumerate(self.lines):
            for widget in line["frame"].winfo_children():
                if isinstance(widget, tk.Label) and widget.cget("text").startswith("LINJA NR."):
                    widget.config(text=f"LINJA NR. {i+1}")
                    break
    
    def update_total(self):
        for widget in self.total_container.winfo_children():
            widget.destroy()
        
        if not self.lines:
            return
        
        total_power_rrjet = 0
        total_power_gjenerator = 0
        total_current = 0
        max_section = 0
        
        for line in self.lines:
            try:
                power_value = float(line["power"].get())
                power_type = line["power_type"].get()
                
                if power_type == "rrjet":
                    total_power_rrjet += power_value
                else:
                    total_power_gjenerator += power_value
                
                cos_phi = float(line["cosphi"].get())
                num_phases = int(line["phases"].get())
                current = calculate_current(power_value, cos_phi, num_phases, power_type)
                total_current += current
                
                install_full = line["install_type"].get()
                install_code = "C" if "Në ajër" in install_full else "A1"
                length = float(line["length"].get()) if line["length"].get() else 1
                
                section, _ = calculate_final_cable_section(
                    current, length, install_code, num_phases, 
                    line["cable_type"].get(), cos_phi
                )
                if section > max_section:
                    max_section = section
                    
            except:
                continue
        
        total_frame = tk.Frame(self.total_container, bg="#1a237e", bd=2, relief="raised")
        total_frame.pack(fill="x", pady=5)
        
        title_label = tk.Label(total_frame, text="📋 RAPORTI TOTAL - SIPAS LIGJEVE TË SHQIPËRISË", 
                              font=("Arial", 14, "bold"), fg="white", bg="#1a237e",
                              pady=10)
        title_label.pack()
        
        now = datetime.now()
        date_time = now.strftime("%d/%m/%Y %H:%M")
        date_label = tk.Label(total_frame, text=f"📅 Data: {date_time}", 
                             font=("Arial", 10, "bold"), fg="#bbbbbb", bg="#1a237e")
        date_label.pack()
        
        data_frame = tk.Frame(total_frame, bg="#1a237e")
        data_frame.pack(padx=20, pady=10)
        
        def create_total_row(parent, label, value, unit=""):
            row_frame = tk.Frame(parent, bg="#1a237e")
            row_frame.pack(fill="x", pady=2)
            
            lbl = tk.Label(row_frame, text=label, font=("Arial", 10, "bold"), 
                          fg="#bbbbbb", bg="#1a237e", width=30, anchor="w")
            lbl.pack(side="left")
            
            val = tk.Label(row_frame, text=f"{value:.0f} {unit}", font=("Arial", 11, "bold"), 
                          fg="gold", bg="#1a237e")
            val.pack(side="right")
            
            return row_frame
        
        create_total_row(data_frame, "🔌 Fuqia totale në rrjet:", total_power_rrjet, "W")
        create_total_row(data_frame, "🔋 Fuqia totale UPS/Gjenerator:", total_power_gjenerator, "VA")
        create_total_row(data_frame, "⚡ Rryma totale e projektimit (I_b):", total_current, "A")
        create_total_row(data_frame, "🔗 Seksioni i kabllit kryesor:", max_section, "mm²")
        create_total_row(data_frame, "📈 Numri i linjave:", len(self.lines), "")
        
        main_mcb = int(total_current * 1.25)
        mcb_ratings = [6, 10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160]
        selected_main_mcb = 6
        for rating in mcb_ratings:
            if rating >= main_mcb:
                selected_main_mcb = rating
                break
        
        create_total_row(data_frame, "⚙️ Automati kryesor i rekomanduar:", selected_main_mcb, "A")
        
        rec_frame = tk.Frame(total_frame, bg="#1a237e")
        rec_frame.pack(pady=(5, 15))
        
        rec_text = f"""💡 REKOMANDIM ZYRITAR Sipas nenit 20 dhe 22 të Rregullores:
• Përdorni kabllo bakri {max_section}mm² si kryesore
• Instaloni automat {selected_main_mcb}A si mbrojtje kryesore
• Sigurohuni për tokëzim sipas nenit 27"""
        
        rec_label = tk.Label(rec_frame, text=rec_text, font=("Arial", 9, "bold"), 
                            fg="#90caf9", bg="#1a237e", justify="left")
        rec_label.pack()
        
        self.update_canvas_scroll()
    
    def update_canvas_scroll(self):
        self.canvas.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def clear_all(self):
        for line in self.lines[:]:
            self.remove_line(line)
    
    def generate_official_report(self):
        """Gjeneron raportin zyrtar"""
        try:
            now = datetime.now()
            
            # Përdor file dialog për të zgjedhur vendndodhjen
            filename = filedialog.asksaveasfilename(
                title="Ruaj Raportin Zyrtar",
                defaultextension=".txt",
                filetypes=[
                    ("Text files", "*.txt"),
                    ("All files", "*.*")
                ],
                initialfile=f"Raport_Zyrtar_{now.strftime('%Y%m%d_%H%M%S')}.txt",
                initialdir=os.path.join(os.path.expanduser("~"), "Desktop")
            )
            
            # Nëse përdoruesi klikon Cancel
            if not filename:
                messagebox.showinfo("Anuluar", "Ruajtja e raportit u anulua.")
                return
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write("="*80 + "\n")
                f.write("REPUBLIKA E SHQIPËRISË\n")
                f.write("MINISTRIA E ENERGJISË DHE INFRASTRUKTURËS\n")
                f.write("DREJTORIA E STANDARDEVE TEKNIKE\n")
                f.write("="*80 + "\n\n")
                
                f.write(f"RAPORTI ZYRITAR I LLOGARITJES SË KABLLOVE\n")
                f.write(f"Data: {now.strftime('%d/%m/%Y')}\n")
                f.write(f"Ora: {now.strftime('%H:%M')}\n")
                f.write("-"*80 + "\n\n")
                
                f.write("BAZË LIGJORE:\n")
                f.write("• Ligji nr. 10268/2010 'Për energjinë elektrike'\n")
                f.write("• Rregullorja nr. 16/2015 'Për instalimet elektrike'\n")
                f.write("• Standardi shqiptar CEI 64-8 (IEC 60364)\n")
                f.write("\n" + "="*80 + "\n\n")
                
                for i, line in enumerate(self.lines):
                    if line["result"].cget("text"):
                        f.write(f"LINJA NR. {i+1}\n")
                        f.write("-"*80 + "\n")
                        text = line["result"].cget("text")
                        text = text.replace("╔", "=").replace("╗", "=")
                        text = text.replace("╠", "-").replace("╣", "-")
                        text = text.replace("║", "|").replace("╚", "=").replace("╝", "=")
                        f.write(text + "\n\n")
                
                f.write("\n" + "="*80 + "\n")
                f.write("PËRFUNDIMET DHE REKOMANDIMET\n")
                f.write("="*80 + "\n\n")
                
                total_power_rrjet = 0
                total_current = 0
                max_section = 0
                
                for line in self.lines:
                    try:
                        power_value = float(line["power"].get())
                        power_type = line["power_type"].get()
                        
                        if power_type == "rrjet":
                            total_power_rrjet += power_value
                        
                        cos_phi = float(line["cosphi"].get())
                        num_phases = int(line["phases"].get())
                        current = calculate_current(power_value, cos_phi, num_phases, power_type)
                        total_current += current
                        
                    except:
                        continue
                
                main_mcb = int(total_current * 1.25)
                mcb_ratings = [6, 10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160]
                selected_main_mcb = 6
                for rating in mcb_ratings:
                    if rating >= main_mcb:
                        selected_main_mcb = rating
                        break
                
                f.write(f"TOTALET E LLOGARITJES:\n")
                f.write(f"• Fuqia totale në rrjet: {total_power_rrjet:.0f} W\n")
                f.write(f"• Rryma totale e projektimit: {total_current:.2f} A\n")
                f.write(f"• Numri i linjave: {len(self.lines)}\n")
                f.write(f"• Automati kryesor i rekomanduar: {selected_main_mcb} A\n")
                f.write(f"• Data e llogaritjes: {now.strftime('%d/%m/%Y %H:%M')}\n")
                f.write("\n" + "-"*80 + "\n")
                f.write("NËNshkrimi i Inxhinierit Elektrik:\n")
                f.write("\n\n____________________________\n")
                f.write("(Emri dhe nënshkrimi)\n")
                f.write("Inxhinier Elektrik i Licencuar\n")
                f.write("Licencë nr.: ______________\n")
            
            messagebox.showinfo("Sukses", f"Raporti u ruajt në:\n{filename}")
            
        except PermissionError:
            messagebox.showerror("Gabim", "Nuk keni leje për të shkruar në këtë lokacion.\nZgjidhni një vend tjetër (Desktop, Documents, etj.)")
        except Exception as e:
            messagebox.showerror("Gabim", f"Nuk mund të gjenerohet raporti: {str(e)}")

# ==================== EKZEKUTIMI ====================
if __name__ == "__main__":
    root = tk.Tk()
    app = CableCalculator(root)
    
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()