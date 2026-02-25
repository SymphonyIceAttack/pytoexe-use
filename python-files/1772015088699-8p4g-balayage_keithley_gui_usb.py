import pyvisa
import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import threading

class KeithleyGUI:
    def __init__(self, master):
        self.master = master
        master.title("Balayage tension 4-wire Keithley USB")

        # 🔹 Vérification de NI-VISA
        try:
            rm = pyvisa.ResourceManager()
            resources = rm.list_resources()
            rm.close()
            if not resources:
                messagebox.showerror(
                    "Erreur",
                    "Aucun instrument USB détecté.\n"
                    "Assurez-vous que NI-VISA Runtime est installé."
                )
                master.destroy()
                return
        except Exception as e:
            messagebox.showerror(
                "Erreur",
                f"NI-VISA non trouvé ou inaccessible.\n"
                f"Veuillez installer NI-VISA Runtime.\n\nDétails : {e}"
            )
            master.destroy()
            return

        # 🔹 Sélection de l'adresse USB
        self.resource = simpledialog.askstring(
            "Sélection USB",
            "Ressources détectées :\n" + "\n".join(resources) +
            "\n\nEntrez l'adresse du Keithley à utiliser :"
        )
        if not self.resource or self.resource not in resources:
            messagebox.showerror("Erreur", "Adresse USB invalide ou non sélectionnée.")
            master.destroy()
            return

        # 🔹 Paramètres de balayage
        tk.Label(master, text="Tension min (V):").grid(row=0, column=0)
        self.v_min_entry = tk.Entry(master); self.v_min_entry.grid(row=0, column=1)
        tk.Label(master, text="Tension max (V):").grid(row=1, column=0)
        self.v_max_entry = tk.Entry(master); self.v_max_entry.grid(row=1, column=1)
        tk.Label(master, text="Pas (V):").grid(row=2, column=0)
        self.step_entry = tk.Entry(master); self.step_entry.grid(row=2, column=1)
        tk.Label(master, text="Pause (s):").grid(row=3, column=0)
        self.delay_entry = tk.Entry(master); self.delay_entry.grid(row=3, column=1)
        tk.Label(master, text="Répetitions:").grid(row=4, column=0)
        self.repeat_entry = tk.Entry(master); self.repeat_entry.grid(row=4, column=1)

        # 🔹 Boutons
        self.start_button = tk.Button(master, text="Lancer le balayage", command=self.start_scan_thread)
        self.start_button.grid(row=5, column=0, pady=10)
        self.stop_button = tk.Button(master, text="Stop", command=self.stop_scan, state=tk.DISABLED)
        self.stop_button.grid(row=5, column=1, pady=10)

        # 🔹 Graphique
        self.fig, self.ax = plt.subplots(figsize=(5,4))
        self.ax.set_title("Balayage tension")
        self.ax.set_xlabel("Tension appliquée (V)")
        self.ax.set_ylabel("Tension mesurée (V)")
        self.ax.grid(True)
        self.canvas = FigureCanvasTkAgg(self.fig, master)
        self.canvas.get_tk_widget().grid(row=6, column=0, columnspan=2)

        self.stop_flag = False

    # ----------------------
    # Threads
    # ----------------------
    def start_scan_thread(self):
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        threading.Thread(target=self.start_scan).start()

    def stop_scan(self):
        self.stop_flag = True

    # ----------------------
    # Balayage
    # ----------------------
    def start_scan(self):
        try:
            v_min = float(self.v_min_entry.get())
            v_max = float(self.v_max_entry.get())
            step = float(self.step_entry.get())
            delay = float(self.delay_entry.get())
            repeat = int(self.repeat_entry.get())
        except ValueError:
            messagebox.showerror("Erreur", "Veuillez entrer des valeurs numériques valides")
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            return

        voltages = np.linspace(v_min, v_max, int(abs(v_max-v_min)/step)+1)
        all_measured = []

        # 🔹 Connexion Keithley
        try:
            rm = pyvisa.ResourceManager()
            sm = rm.open_resource(self.resource)
            sm.write("*RST")
            sm.write(":SENS:FUNC 'VOLT'")
            sm.write(":SENS:VOLT:RSENSE ON")
        except Exception as e:
            messagebox.showerror(
                "Erreur",
                f"Impossible de connecter le Keithley.\n"
                f"Vérifiez NI-VISA et la connexion USB.\n\nDétails : {e}"
            )
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            return

        # 🔹 Balayage et graphique dynamique
        self.ax.clear()
        self.ax.set_title("Balayage tension")
        self.ax.set_xlabel("Tension appliquée (V)")
        self.ax.set_ylabel("Tension mesurée (V)")
        self.ax.grid(True)

        for r in range(repeat):
            if self.stop_flag:
                break
            measured = []
            for v in voltages:
                if self.stop_flag:
                    break
                sm.write(f":SOUR:VOLT {v}")
                time.sleep(delay)
                voltage_measured = float(sm.query(":MEAS:VOLT?"))
                measured.append(voltage_measured)
                self.ax.clear()
                for i, m in enumerate(all_measured + [measured]):
                    self.ax.plot(voltages[:len(m)], m, marker='o', label=f"Balayage {i+1}")
                self.ax.set_title("Balayage tension")
                self.ax.set_xlabel("Tension appliquée (V)")
                self.ax.set_ylabel("Tension mesurée (V)")
                self.ax.grid(True)
                self.ax.legend()
                self.canvas.draw()
            all_measured.append(measured)

        sm.close()
        rm.close()
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

        # 🔹 Boîte de dialogue sauvegarde
        save_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Fichiers texte","*.txt")],
            title="Enregistrer les mesures sous"
        )
        if save_path:
            with open(save_path, 'w') as f:
                header = "Tension_appliquee\t" + "\t".join([f"Mesure_{i+1}" for i in range(len(all_measured))]) + "\n"
                f.write(header)
                for i in range(len(voltages)):
                    row = f"{voltages[i]:.6f}\t" + "\t".join([f"{all_measured[r][i]:.6f}" for r in range(len(all_measured))]) + "\n"
                    f.write(row)
            messagebox.showinfo("Terminé", f"Données sauvegardées dans {save_path}")
        else:
            messagebox.showinfo("Annulé", "Sauvegarde annulée par l'utilisateur.")
        self.stop_flag = False

if __name__ == "__main__":
    root = tk.Tk()
    gui = KeithleyGUI(root)
    root.mainloop()