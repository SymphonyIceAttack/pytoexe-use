import sys
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from fpdf import FPDF
from sklearn.preprocessing import QuantileTransformer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QCheckBox, QFileDialog

class GeoSteeringApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GeoSteering Final Prototype")
        self.setGeometry(100, 100, 1600, 950)

        central_widget = QWidget()
        layout = QVBoxLayout()

        label = QLabel("GeoSteering Software Prototype - Final Version")
        label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(label)

        # Checkbox normalisasi
        self.normalize_checkbox = QCheckBox("Normalisasi Gamma Ray dengan AI/ML berdasarkan type log")
        layout.addWidget(self.normalize_checkbox)

        # Input smoothing
        self.smooth_input = QLineEdit()
        self.smooth_input.setPlaceholderText("Masukkan window smoothing (misal: 3, 5, 7)")
        layout.addWidget(self.smooth_input)

        # Input cutoff net pay
        self.phi_cutoff_input = QLineEdit()
        self.phi_cutoff_input.setPlaceholderText("Cutoff Porositas Efektif (misal: 0.15)")
        layout.addWidget(self.phi_cutoff_input)

        self.sw_cutoff_input = QLineEdit()
        self.sw_cutoff_input.setPlaceholderText("Cutoff Water Saturation (misal: 0.5)")
        layout.addWidget(self.sw_cutoff_input)

        # Input formasi & reservoir
        self.formasi_input = QLineEdit()
        self.formasi_input.setPlaceholderText("Nama Formasi (misal: Sandstone A)")
        layout.addWidget(self.formasi_input)

        self.top_res_input = QLineEdit()
        self.top_res_input.setPlaceholderText("Top Reservoir (MD/TVD/TVDSS)")
        layout.addWidget(self.top_res_input)

        self.bottom_res_input = QLineEdit()
        self.bottom_res_input.setPlaceholderText("Bottom Reservoir (MD/TVD/TVDSS)")
        layout.addWidget(self.bottom_res_input)

        self.window_res_input = QLineEdit()
        self.window_res_input.setPlaceholderText("Window Geosteering (MD/TVD/TVDSS)")
        layout.addWidget(self.window_res_input)

        # Input koordinat sumur
        self.xy_kb_input = QLineEdit()
        self.xy_kb_input.setPlaceholderText("Koordinat Sumur (X,Y,KB)")
        layout.addWidget(self.xy_kb_input)

        # Tombol aksi
        btn_plot = QPushButton("Plot Logs")
        btn_plot.clicked.connect(self.plot_logs)
        layout.addWidget(btn_plot)

        btn_ai = QPushButton("AI Steering Suggestion")
        btn_ai.clicked.connect(self.ai_suggestion)
        layout.addWidget(btn_ai)

        btn_netpay = QPushButton("Calculate Net Pay")
        btn_netpay.clicked.connect(self.calculate_netpay)
        layout.addWidget(btn_netpay)

        btn_surface = QPushButton("Load Surface (ASCII X-Y-Z)")
        btn_surface.clicked.connect(self.load_surface)
        layout.addWidget(btn_surface)

        btn_export = QPushButton("Export Report (Excel + PDF)")
        btn_export.clicked.connect(self.export_report)
        layout.addWidget(btn_export)

        # Canvas plot
        self.fig, self.axs = plt.subplots(2, 2, figsize=(12, 8))
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def normalize_gamma_ray(self, ref_log, drill_log):
        ref_log = np.array(ref_log).reshape(-1,1)
        drill_log = np.array(drill_log).reshape(-1,1)
        qt = QuantileTransformer(n_quantiles=100, output_distribution='uniform')
        qt.fit(ref_log)
        drill_norm = qt.transform(drill_log)
        return drill_norm.flatten()

    def plot_logs(self):
        depth = [1500, 1520, 1540, 1560, 1580, 1600]
        gamma_ref = [40, 55, 75, 95, 85, 65]
        gamma_drill = [42, 58, 78, 98, 88, 68]

        try:
            window = int(self.smooth_input.text())
        except:
            window = 3

        gamma_ref_smooth = np.convolve(gamma_ref, np.ones(window)/window, mode='valid')
        gamma_drill_smooth = np.convolve(gamma_drill, np.ones(window)/window, mode='valid')

        if self.normalize_checkbox.isChecked():
            gamma_drill_smooth = self.normalize_gamma_ray(gamma_ref_smooth, gamma_drill_smooth)

        self.axs[0,0].clear()
        self.axs[0,0].plot(gamma_ref_smooth, depth[:len(gamma_ref_smooth)], label="Type Log (Smoothed)")
        self.axs[0,0].plot(gamma_drill_smooth, depth[:len(gamma_drill_smooth)], label="Drilling (Normalized)", linestyle="--")
        self.axs[0,0].invert_yaxis()
        self.axs[0,0].set_title("Gamma Ray (Smoothed/Normalized)")
        self.axs[0,0].legend()
        self.canvas.draw()

    def ai_suggestion(self):
        slope = 1.2
        rec = "Gamma Ray naik → rekomendasi TURUN"
        self.axs[0,1].clear()
        self.axs[0,1].text(0.1, 0.5, f"Slope: {slope}\nRekomendasi: {rec}", fontsize=12)
        self.axs[0,1].set_axis_off()
        self.canvas.draw()

    def calculate_netpay(self):
        depth = [1500, 1510, 1520, 1530, 1540]
        phiE = [0.12, 0.18, 0.20, 0.10, 0.22]
        Sw = [0.45, 0.40, 0.35, 0.60, 0.30]

        try:
            phi_cutoff = float(self.phi_cutoff_input.text())
        except:
            phi_cutoff = 0.15
        try:
            sw_cutoff = float(self.sw_cutoff_input.text())
        except:
            sw_cutoff = 0.5

        netpay = sum([depth[i+1]-depth[i] for i in range(len(depth)-1) if phiE[i]>=phi_cutoff and Sw[i]<=sw_cutoff])
        self.axs[1,0].clear()
        self.axs[1,0].text(0.1, 0.5, f"Net Pay: {netpay} m", fontsize=12)
        self.axs[1,0].set_axis_off()
        self.canvas.draw()

    def load_surface(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Open Surface File", "", "Text Files (*.txt *.asc)")
        if fname:
            surface = np.loadtxt(fname)
            self.axs[1,1].clear()
            self.axs[1,1].scatter(surface[:,0], surface[:,1], c=surface[:,2], cmap="viridis")
            self.axs[1,1].set_title("Surface Interpretation")
            self.canvas.draw()

    def export_report(self):
        df = pd.DataFrame({"Depth":[1500,1520,1540],"GammaRay":[40,55,75]})
        df.to_excel("geosteering_report.xlsx", index=False)

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, "Geosteering Report", ln=True, align="C")
        pdf.cell(200, 10, f"Formasi: {self.formasi_input.text()}", ln=True)
        pdf.cell(200, 10, f"Top Reservoir: {self.top_res_input.text()}", ln=True)
        pdf.cell(200, 10, f"Bottom Reservoir: {self.bottom_res_input.text()}", ln=True)
        pdf.cell(200, 10, f"Window: {self.window_res_input.text()}", ln=True)
        pdf.cell(200, 10, f"Koordinat Sumur: {self.xy_kb_input.text()}", ln=True)
        pdf.cell(200, 10, "Net Pay: 40 m", ln=True)
        pdf.output("geosteering_report.pdf")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GeoSteeringApp()
    window.show()
    sys.exit(app.exec_())
