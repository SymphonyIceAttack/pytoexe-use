"""
Radiation Protection Dose Optimisation Tool V3
===============================================
Enhanced clinical decision-support system with sound and visual alerts.

Features:
- Sound alerts for warnings (beeps)
- Visual alerts (flashing) for excessive doses
- Colour-coded DRL dashboard
- User-friendly interface
- ALARA compliance indicators

Based on: Deterministic Spectral Model for Predicting EI and ESAK
Author: [Your Name]
Date: 2025
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import numpy as np
from datetime import datetime
import winsound
import threading
import time

# ============================================================================
# MODEL CONSTANTS (Chapter 4, Table 4.5)
# ============================================================================

Y0 = 81.31
n = 1.668
c0 = 100
kVp0 = 80
d0 = 100
mu0_80 = 0.3317
mu1_80 = -0.0028
A_80 = 0.0313
B_SPR_80 = 0.0438
BSF_80 = 1.280

# ============================================================================
# MODEL FUNCTIONS
# ============================================================================

def predict(kVp, mAs, SID, t):
    """Predict EI and ESAK from exposure parameters."""
    if kVp < 40 or kVp > 150:
        raise ValueError(f"kVp {kVp} out of range (40-150)")
    if mAs <= 0:
        raise ValueError("mAs must be positive")
    if SID < 50 or SID > 300:
        raise ValueError(f"SID {SID} out of range (50-300)")
    if t < 1 or t > 50:
        raise ValueError(f"Thickness {t} out of range (1-50)")
    if SID - t <= 0:
        raise ValueError("SID must be greater than thickness")

    mu0 = mu0_80 + (kVp - 80) * 0.0005
    mu1 = mu1_80 + (kVp - 80) * 0.00002
    mu_eff = mu0 + mu1 * t
    T_primary = np.exp(-mu_eff * t)
    A = A_80 + (kVp - 80) * 0.00002
    B = B_SPR_80 + (kVp - 80) * 0.00001
    SPR = A * t * np.exp(B * t)
    BSF = BSF_80 + (kVp - 80) * 0.0015

    K_ref = Y0 * (kVp / kVp0) ** n * mAs
    K_incident = K_ref * (d0 / (SID - t)) ** 2
    K_det_primary = K_incident * T_primary
    K_det_total = K_det_primary * (1 + SPR)
    EI_phys = c0 * K_det_total
    ESAK = BSF * K_incident

    return EI_phys, ESAK, {
        'K_ref': K_ref, 'FSD': SID - t, 'K_incident': K_incident,
        'mu_eff': mu_eff, 'T_primary': T_primary, 'SPR': SPR, 'BSF': BSF,
        'K_det_primary': K_det_primary, 'K_det_total': K_det_total,
        'u_EI': 0.27 * EI_phys, 'u_ESAK': 0.12 * ESAK
    }

def calculate_DI(EI_measured, EI_predicted):
    if EI_predicted <= 0:
        return float('inf')
    return 10 * np.log10(EI_measured / EI_predicted)

# ============================================================================
# SOUND FUNCTIONS
# ============================================================================

def play_beep(frequency=1000, duration=200):
    """Play a beep sound."""
    try:
        winsound.Beep(frequency, duration)
    except:
        pass

def play_warning():
    """Play a warning sound (two beeps)."""
    try:
        winsound.Beep(800, 200)
        time.sleep(0.1)
        winsound.Beep(800, 200)
    except:
        pass

def play_alert():
    """Play an urgent alert sound (three beeps)."""
    try:
        for _ in range(3):
            winsound.Beep(600, 300)
            time.sleep(0.1)
    except:
        pass

# ============================================================================
# GUI APPLICATION
# ============================================================================

class RadiationProtectionToolV3:
    def __init__(self, root):
        self.root = root
        self.root.title("Radiation Protection Dose Optimisation Tool V3")
        self.root.geometry("1200x850")
        self.root.resizable(True, True)
        
        # Set colour scheme
        self.colors = {
            'bg': '#1a1a2e',
            'header': '#16213e',
            'panel': '#0f3460',
            'accent': '#e94560',
            'text': '#ffffff',
            'success': '#00b894',
            'warning': '#fdcb6e',
            'danger': '#e94560',
            'info': '#74b9ff',
            'flash': '#ff0000'
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # Flash control
        self.flash_active = False
        self.flash_id = None
        
        self.create_widgets()
        
        # Play startup sound
        play_beep(500, 100)
        
    def create_widgets(self):
        # ===== HEADER =====
        header = tk.Frame(self.root, bg=self.colors['header'], height=110)
        header.pack(fill='x', padx=0, pady=0)
        header.pack_propagate(False)
        
        # Radiation symbol
        symbol = tk.Label(header, text="☢", font=('Arial', 42), 
                          fg=self.colors['accent'], bg=self.colors['header'])
        symbol.pack(side='left', padx=20, pady=10)
        
        # Title
        title_frame = tk.Frame(header, bg=self.colors['header'])
        title_frame.pack(side='left', fill='both', expand=True, padx=10)
        
        title = tk.Label(title_frame, text="RADIATION PROTECTION", 
                         font=('Arial', 20, 'bold'), fg=self.colors['text'], 
                         bg=self.colors['header'])
        title.pack(anchor='w')
        
        subtitle = tk.Label(title_frame, text="Dose Optimisation Tool V3", 
                            font=('Arial', 14), fg=self.colors['info'], 
                            bg=self.colors['header'])
        subtitle.pack(anchor='w')
        
        tagline = tk.Label(title_frame, text="ALARA — As Low As Reasonably Achievable", 
                           font=('Arial', 11, 'bold'), fg=self.colors['warning'], 
                           bg=self.colors['header'])
        tagline.pack(anchor='w')
        
        # Version indicator
        version = tk.Label(header, text="v3.0", 
                           font=('Arial', 12, 'bold'), fg=self.colors['accent'], 
                           bg=self.colors['header'])
        version.pack(side='right', padx=20)
        
        # ===== MAIN CONTENT =====
        main_frame = tk.Frame(self.root, bg=self.colors['bg'])
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # ===== LEFT PANEL =====
        left = tk.Frame(main_frame, bg=self.colors['bg'])
        left.pack(side='left', fill='both', expand=True, padx=5)
        
        # Input panel
        input_frame = tk.LabelFrame(left, text="☢ Exposure Parameters", 
                                    fg=self.colors['accent'], bg=self.colors['panel'],
                                    font=('Arial', 13, 'bold'))
        input_frame.pack(fill='x', pady=5)
        input_frame.configure(bg=self.colors['panel'])
        
        self.create_input_row(input_frame, "kVp:", 0, "40-150 kV")
        self.create_input_row(input_frame, "mAs:", 1, "0.1-100 mAs")
        self.create_input_row(input_frame, "SID (cm):", 2, "50-300 cm")
        self.create_input_row(input_frame, "Patient Thickness (cm):", 3, "1-50 cm")
        
        # Measured EI
        ei_frame = tk.Frame(input_frame, bg=self.colors['panel'])
        ei_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(ei_frame, text="📊 Measured EI (optional):", 
                 fg=self.colors['text'], bg=self.colors['panel'],
                 font=('Arial', 10)).pack(side='left', padx=5)
        
        self.EI_meas_var = tk.DoubleVar(value=0)
        tk.Entry(ei_frame, textvariable=self.EI_meas_var, width=15,
                 font=('Arial', 10), bg='#0a0a1a', fg='white',
                 insertbackground='white').pack(side='left', padx=5)
        
        # Radiation protection message
        rp_frame = tk.LabelFrame(left, text="☢ Radiation Protection", 
                                 fg=self.colors['accent'], bg=self.colors['panel'],
                                 font=('Arial', 11, 'bold'))
        rp_frame.pack(fill='x', pady=5)
        rp_frame.configure(bg=self.colors['panel'])
        
        rp_msg = tk.Label(rp_frame, 
                          text="This tool supports optimisation of patient radiation exposure\n"
                               "in accordance with the ALARA principle.\n"
                               "⚠ Sound and visual alerts are enabled for dose warnings.",
                          fg=self.colors['info'], bg=self.colors['panel'],
                          font=('Arial', 10), justify='center')
        rp_msg.pack(pady=5)
        
        # Calculate button
        btn = tk.Button(left, text="CALCULATE ⚡", 
                        command=self.calculate,
                        bg=self.colors['accent'], fg='white',
                        font=('Arial', 16, 'bold'), height=2)
        btn.pack(fill='x', pady=10)
        
        # Export buttons
        btn_frame = tk.Frame(left, bg=self.colors['bg'])
        btn_frame.pack(fill='x', pady=5)
        
        tk.Button(btn_frame, text="📋 Copy Results", 
                  command=self.copy_results,
                  bg=self.colors['panel'], fg=self.colors['text'],
                  font=('Arial', 10)).pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="🗑 Clear",
                  command=self.clear_results,
                  bg=self.colors['panel'], fg=self.colors['text'],
                  font=('Arial', 10)).pack(side='left', padx=5)
        
        # ===== RIGHT PANEL =====
        right = tk.Frame(main_frame, bg=self.colors['bg'])
        right.pack(side='right', fill='both', expand=True, padx=5)
        
        # DRL Dashboard (NEW)
        dashboard_frame = tk.LabelFrame(right, text="📊 DRL Dashboard", 
                                        fg=self.colors['warning'], bg=self.colors['panel'],
                                        font=('Arial', 12, 'bold'))
        dashboard_frame.pack(fill='x', pady=5)
        dashboard_frame.configure(bg=self.colors['panel'])
        
        dashboard_inner = tk.Frame(dashboard_frame, bg=self.colors['panel'])
        dashboard_inner.pack(fill='x', padx=10, pady=10)
        
        # Status indicator (flashing)
        self.status_indicator = tk.Label(dashboard_inner, text="⚪ WAITING", 
                                         font=('Arial', 14, 'bold'),
                                         fg=self.colors['info'], bg=self.colors['panel'])
        self.status_indicator.pack(pady=5)
        
        # Metrics row
        metrics_frame = tk.Frame(dashboard_inner, bg=self.colors['panel'])
        metrics_frame.pack(fill='x', pady=5)
        
        self.drl_esak_label = tk.Label(metrics_frame, text="ESAK: —", 
                                        fg=self.colors['text'], bg=self.colors['panel'],
                                        font=('Arial', 12))
        self.drl_esak_label.pack(side='left', padx=10)
        
        self.drl_ratio_label = tk.Label(metrics_frame, text="Ratio: —", 
                                         fg=self.colors['text'], bg=self.colors['panel'],
                                         font=('Arial', 12))
        self.drl_ratio_label.pack(side='left', padx=10)
        
        self.drl_status_label = tk.Label(metrics_frame, text="Status: —", 
                                          fg=self.colors['text'], bg=self.colors['panel'],
                                          font=('Arial', 12))
        self.drl_status_label.pack(side='left', padx=10)
        
        # DRL quick reference
        drl_ref = tk.Label(dashboard_inner, 
                           text="DRL (Chest PA): 0.31 mGy  |  ALARA: Keep ratio < 1.0",
                           fg=self.colors['info'], bg=self.colors['panel'],
                           font=('Arial', 9))
        drl_ref.pack(pady=2)
        
        # Results
        results_frame = tk.LabelFrame(right, text="📄 Results", 
                                      fg=self.colors['text'], bg=self.colors['panel'],
                                      font=('Arial', 12, 'bold'))
        results_frame.pack(fill='both', expand=True, pady=5)
        results_frame.configure(bg=self.colors['panel'])
        
        self.results_text = scrolledtext.ScrolledText(results_frame, 
                                                       font=('Courier New', 9),
                                                       bg='#0a0a1a', fg='#00ff88',
                                                       height=12)
        self.results_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Sound status
        sound_frame = tk.Frame(right, bg=self.colors['bg'])
        sound_frame.pack(fill='x', pady=5)
        
        self.sound_status = tk.Label(sound_frame, text="🔊 Sound alerts enabled", 
                                      fg=self.colors['info'], bg=self.colors['bg'],
                                      font=('Arial', 9))
        self.sound_status.pack()
        
        # Status bar
        status = tk.Label(self.root, text="Ready | ☢ ALARA — Optimise patient dose | v3.0",
                          bg=self.colors['header'], fg=self.colors['info'],
                          font=('Arial', 9))
        status.pack(side='bottom', fill='x')
    
    def create_input_row(self, parent, label, row, tooltip):
        """Create a labelled input row with slider."""
        frame = tk.Frame(parent, bg=parent['bg'])
        frame.pack(fill='x', padx=10, pady=2)

        lbl = tk.Label(frame, text=label, fg=self.colors['text'],
                       bg=parent['bg'], font=('Arial', 10), width=18)
        lbl.pack(side='left', padx=5)
        
        # Tooltip
        tt = tk.Label(frame, text="?", fg=self.colors['info'], bg=parent['bg'],
                      font=('Arial', 8, 'bold'), cursor='question_arrow')
        tt.pack(side='left', padx=2)
        tt.bind('<Enter>', lambda e, msg=tooltip: self.show_tooltip(e, msg))
        tt.bind('<Leave>', self.hide_tooltip)

        var = tk.DoubleVar()

        if label == "kVp:":
            var = tk.DoubleVar(value=80)
            spin = tk.Spinbox(frame, from_=40, to=150, textvariable=var, width=8,
                              bg='#0a0a1a', fg='white', buttonbackground=self.colors['panel'])
            spin.pack(side='left', padx=5)
            scale = tk.Scale(frame, from_=40, to=150, variable=var,
                             orient='horizontal', length=150,
                             bg=parent['bg'], fg=self.colors['text'],
                             highlightthickness=0)
            scale.pack(side='left', padx=5)
            self.kVp_var = var

        elif label == "mAs:":
            var = tk.DoubleVar(value=10)
            spin = tk.Spinbox(frame, from_=0.1, to=100, increment=0.5, textvariable=var, width=8,
                              bg='#0a0a1a', fg='white', buttonbackground=self.colors['panel'])
            spin.pack(side='left', padx=5)
            scale = tk.Scale(frame, from_=0.1, to=50, variable=var,
                             orient='horizontal', length=150,
                             bg=parent['bg'], fg=self.colors['text'],
                             highlightthickness=0)
            scale.pack(side='left', padx=5)
            self.mAs_var = var

        elif label == "SID (cm):":
            var = tk.DoubleVar(value=100)
            spin = tk.Spinbox(frame, from_=50, to=300, textvariable=var, width=8,
                              bg='#0a0a1a', fg='white', buttonbackground=self.colors['panel'])
            spin.pack(side='left', padx=5)
            scale = tk.Scale(frame, from_=50, to=200, variable=var,
                             orient='horizontal', length=150,
                             bg=parent['bg'], fg=self.colors['text'],
                             highlightthickness=0)
            scale.pack(side='left', padx=5)
            self.SID_var = var

        elif label == "Patient Thickness (cm):":
            var = tk.DoubleVar(value=20)
            spin = tk.Spinbox(frame, from_=1, to=50, textvariable=var, width=8,
                              bg='#0a0a1a', fg='white', buttonbackground=self.colors['panel'])
            spin.pack(side='left', padx=5)
            scale = tk.Scale(frame, from_=1, to=40, variable=var,
                             orient='horizontal', length=150,
                             bg=parent['bg'], fg=self.colors['text'],
                             highlightthickness=0)
            scale.pack(side='left', padx=5)
            self.thick_var = var
    
    def show_tooltip(self, event, msg):
        """Show a tooltip."""
        self.tooltip = tk.Toplevel(self.root)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
        label = tk.Label(self.tooltip, text=msg, bg='#ffffaa', fg='black',
                         font=('Arial', 9), relief='solid', borderwidth=1)
        label.pack()
    
    def hide_tooltip(self, event):
        """Hide the tooltip."""
        if hasattr(self, 'tooltip') and self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
    
    def calculate(self):
        """Perform the prediction calculation."""
        try:
            kVp = self.kVp_var.get()
            mAs = self.mAs_var.get()
            SID = self.SID_var.get()
            t = self.thick_var.get()
            EI_m = self.EI_meas_var.get()
            
            if SID - t <= 0:
                messagebox.showerror("Error", "SID must be greater than thickness")
                return
            
            EI, ESAK, d = predict(kVp, mAs, SID, t)
            DI = calculate_DI(EI_m, EI) if EI_m > 0 else None
            
            # Calculate DRL ratio
            ESAK_mGy = ESAK / 1000
            drl = 0.31
            ratio = ESAK_mGy / drl
            
            # Determine status
            if ratio < 0.5:
                status = "✅ LOW — Consider optimisation"
                status_color = self.colors['success']
                sound_fn = None
                flash = False
            elif ratio < 1.0:
                status = "✅ WITHIN DRL — Acceptable"
                status_color = self.colors['info']
                sound_fn = play_beep
                flash = False
            elif ratio < 1.5:
                status = "⚠ ABOVE DRL — Review technique"
                status_color = self.colors['warning']
                sound_fn = play_warning
                flash = True
            else:
                status = "❌ EXCESSIVE — Investigate immediately"
                status_color = self.colors['danger']
                sound_fn = play_alert
                flash = True
            
            # Play sound if needed
            if sound_fn:
                threading.Thread(target=sound_fn, daemon=True).start()
            
            # Update dashboard
            self.update_dashboard(ESAK_mGy, ratio, status, status_color, flash)
            
            # Build results
            lines = [
                "="*60,
                "RADIATION PROTECTION DOSE OPTIMISATION TOOL V3",
                "="*60,
                f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
                "--- INPUT PARAMETERS ---",
                f"kVp: {kVp:.0f} kV",
                f"mAs: {mAs:.1f}",
                f"SID: {SID:.0f} cm",
                f"Patient Thickness: {t:.1f} cm",
                f"Measured EI: {EI_m:.1f}\n" if EI_m > 0 else "",
                "--- OUTPUT ---",
                f"EI_phys (Predicted): {EI:.1f}",
                f"ESAK: {ESAK:.2f} µGy ({ESAK_mGy:.3f} mGy)",
            ]
            
            if DI is not None:
                lines.append(f"DI_phys: {DI:.2f}")
                if DI < -1:
                    target = mAs * 10 ** (1/10)
                    lines.append("  ⚠ UNDER-EXPOSURE")
                    lines.append(f"  → Increase mAs to ~{target:.1f}")
                elif DI > 1:
                    target = mAs * 10 ** (-1/10)
                    lines.append("  ⚠ OVER-EXPOSURE")
                    lines.append(f"  → Decrease mAs to ~{target:.1f}")
                else:
                    lines.append("  ✅ OPTIMAL — Within acceptable range")
            
            lines.extend([
                "\n--- INTERMEDIATE VALUES ---",
                f"Tube Output: {d['K_ref']:.2f} µGy",
                f"FSD: {d['FSD']:.0f} cm",
                f"Incident Kerma: {d['K_incident']:.2f} µGy",
                f"Attenuation: {d['mu_eff']:.4f} cm⁻¹",
                f"Transmission: {d['T_primary']:.6f}",
                f"SPR: {d['SPR']:.3f}",
                f"BSF: {d['BSF']:.3f}",
                f"Detector Kerma: {d['K_det_total']:.2f} µGy",
                "\n--- UNCERTAINTY ---",
                f"u(EI): {d['u_EI']:.1f} ({d['u_EI']/EI*100:.0f}%)",
                f"u(ESAK): {d['u_ESAK']:.2f} µGy ({d['u_ESAK']/ESAK*100:.0f}%)",
                "\n--- DRL COMPLIANCE ---",
                f"DRL (Chest PA): {drl:.2f} mGy",
                f"Your ESAK: {ESAK_mGy:.3f} mGy",
                f"DRL Ratio: {ratio:.2f}",
                f"Status: {status}",
                "\n" + "="*60,
                "ALARA — As Low As Reasonably Achievable",
                "="*60
            ])
            
            self.results_text.delete('1.0', tk.END)
            self.results_text.insert('1.0', "\n".join(lines))
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def update_dashboard(self, esa_mGy, ratio, status, status_color, flash):
        """Update the DRL dashboard with alerts."""
        self.drl_esak_label.config(text=f"ESAK: {esa_mGy:.3f} mGy", fg=self.colors['text'])
        self.drl_ratio_label.config(text=f"Ratio: {ratio:.2f}", fg=status_color)
        self.drl_status_label.config(text=f"Status: {status}", fg=status_color)
        self.status_indicator.config(text=f"● {status}", fg=status_color)
        
        # Stop any existing flash
        if self.flash_active:
            self.flash_active = False
            if self.flash_id:
                self.root.after_cancel(self.flash_id)
                self.flash_id = None
            self.status_indicator.config(bg=self.colors['panel'])
        
        # Start flashing if needed
        if flash:
            self.flash_active = True
            self.flash_dashboard()
    
    def flash_dashboard(self):
        """Flash the dashboard for alerts."""
        if not self.flash_active:
            return
        
        # Toggle background color
        current_bg = self.status_indicator.cget('bg')
        if current_bg == self.colors['panel']:
            self.status_indicator.config(bg=self.colors['danger'])
            self.drl_esak_label.config(bg=self.colors['danger'])
            self.drl_ratio_label.config(bg=self.colors['danger'])
            self.drl_status_label.config(bg=self.colors['danger'])
        else:
            self.status_indicator.config(bg=self.colors['panel'])
            self.drl_esak_label.config(bg=self.colors['panel'])
            self.drl_ratio_label.config(bg=self.colors['panel'])
            self.drl_status_label.config(bg=self.colors['panel'])
        
        # Schedule next flash
        self.flash_id = self.root.after(500, self.flash_dashboard)
    
    def copy_results(self):
        """Copy results to clipboard."""
        self.root.clipboard_clear()
        self.root.clipboard_append(self.results_text.get('1.0', tk.END))
        messagebox.showinfo("Copied", "Results copied to clipboard")
        play_beep(800, 100)
    
    def clear_results(self):
        """Clear the results."""
        self.results_text.delete('1.0', tk.END)
        
        # Reset dashboard
        self.flash_active = False
        if self.flash_id:
            self.root.after_cancel(self.flash_id)
            self.flash_id = None
        
        self.drl_esak_label.config(text="ESAK: —", fg=self.colors['text'])
        self.drl_ratio_label.config(text="Ratio: —", fg=self.colors['text'])
        self.drl_status_label.config(text="Status: —", fg=self.colors['text'])
        self.status_indicator.config(text="⚪ WAITING", fg=self.colors['info'], bg=self.colors['panel'])
        
        play_beep(400, 100)

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    root = tk.Tk()
    app = RadiationProtectionToolV3(root)
    root.mainloop()