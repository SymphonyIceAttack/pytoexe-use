import sys, json
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
        self.smooth_input.setPlaceholderText("Window smoothing (misal: 3, 5, 7)")
        layout.addWidget(self.smooth_input)

        # Input cutoff net pay
        self.phi_cutoff_input = QLineEdit()
        self.phi_cutoff_input.setPlaceholderText("Cutoff Porositas Efektif (misal: 0.15)")
        layout.addWidget(self.phi_cutoff_input)

        self.sw_cutoff_input = QLineEdit()
        self.sw_cutoff_input.setPlaceholderText("Cutoff Water Saturation (misal: 0.5)")
        layout.addWidget(self.sw_cutoff_input)

        # Input formasi & reservoir
        self.formasi_input = QLineEdit(); self.formasi_input.setPlaceholderText("Nama Formasi")
        layout.addWidget(self.formasi_input)
        self.top_res_input = QLineEdit(); self.top_res_input.setPlaceholderText("Top Reservoir (MD/TVD/TVDSS)")
        layout.addWidget(self.top_res_input)
        self.bottom_res_input = QLineEdit(); self.bottom_res_input.setPlaceholderText("Bottom Reservoir (MD/TVD/TVDSS)")
        layout.addWidget(self.bottom_res_input)
        self.window_res_input = QLineEdit(); self.window_res_input.setPlaceholderText("Window Geosteering (MD/TVD/TVDSS)")
        layout.addWidget(self.window_res_input)

        # Input koordinat sumur
        self.xy_kb_input = QLineEdit(); self.xy_kb_input.setPlaceholderText("Koordinat Sumur (X,Y,KB)")
        layout.addWidget(self.xy_kb_input)

        # Tombol aksi
        btn_plot = QPushButton("Plot Logs"); btn_plot.clicked.connect(self.plot_logs); layout.addWidget(btn_plot)
        btn_ai = QPushButton("AI Steering Suggestion"); btn_ai.clicked.connect(self.ai_suggestion); layout.addWidget(btn_ai)
        btn_netpay = QPushButton("Calculate Net Pay"); btn_netpay.clicked.connect(self.calculate_netpay); layout.addWidget(btn_netpay)
        btn_surface = QPushButton("Load Surface (ASCII X-Y-Z)"); btn_surface.clicked.connect(self.load_surface); layout.addWidget(btn_surface)
        btn_export = QPushButton("Export Report (Excel + PDF)"); btn_export.clicked.connect(self.export_report); layout.addWidget(btn_export)

        # Tombol Save/Load Project
        btn_save = QPushButton("Save Project"); btn_save.clicked.connect(self.save_project); layout.addWidget(btn_save)
        btn_load = QPushButton("Load Project"); btn_load.clicked.connect(self.load_project); layout.addWidget(btn_load)

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
        gamma_ref = [40, 55, 