import os
import sys
import numpy as np
import pandas as pd

from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout,
    QLabel, QFileDialog, QProgressBar, QMessageBox
)
from PySide6.QtCore import QThread, Signal

# ==========================
# НАЙТИ И НАСТРОИТЬ ANSYS DPF
# ==========================
def setup_ansys_dpf():
    import sys

    # === ПОДДЕРЖКА PyInstaller onefile ===
    if getattr(sys, 'frozen', False):
        bundle_dir = sys._MEIPASS
        bundled_dpf = os.path.join(bundle_dir, 'ansys', 'dpf_gatebin')
        if os.path.exists(bundled_dpf):
            os.environ["ANSYS_DPF_PATH"] = bundled_dpf
            print("✅ DPF используется из bundled exe")
            return bundled_dpf
    # ======================================
    # Попытка взять путь из переменных окружения
    if "ANSYS_DPF_PATH" in os.environ and os.path.exists(os.environ["ANSYS_DPF_PATH"]):
        return os.environ["ANSYS_DPF_PATH"]

    # Попытка найти ANSYS в стандартной папке Program Files
    base_dirs = [
        r"C:\Program Files\ANSYS Inc",
        r"C:\Program Files (x86)\ANSYS Inc"
    ]

    for base in base_dirs:
        if not os.path.exists(base):
            continue
        versions = sorted(os.listdir(base), reverse=True)
        for v in versions:
            candidate = os.path.join(base, v, "aisol", "bin", "winx64")
            if os.path.exists(candidate):
                os.environ["ANSYS_DPF_PATH"] = candidate
                os.environ["AWP_ROOT"] = os.path.join(base, v)
                return candidate

    # Если не найдено
    raise Exception("DPF не найден. Убедитесь, что ANSYS установлен.")

# ВАЖНО: вызываем ДО импорта dpf
setup_ansys_dpf()

from ansys.dpf import core as dpf

# ==========================
# WORKER (в отдельном потоке)
# ==========================
class Worker(QThread):
    progress = Signal(int)
    status = Signal(str)
    finished = Signal()
    error = Signal(str)

    def __init__(self, folder):
        super().__init__()
        self.folder = folder

    def run(self):
        try:
            self.status.emit("Поиск rst...")
            self.progress.emit(10)

            rst = None
            for f in os.listdir(self.folder):
                if f.endswith(".rst"):
                    rst = os.path.join(self.folder, f)
                    break

            if rst is None:
                raise Exception("RST не найден")

            self.status.emit("Загрузка модели...")
            self.progress.emit(20)

            model = dpf.Model(rst)
            mesh = model.metadata.meshed_region

            analysis = str(model.metadata.result_info.analysis_type).lower()

            op = dpf.operators.result.element_nodal_forces()
            op.inputs.data_sources.connect(model)

            # бимы
            beam_ids = []
            axes = {}

            for i in range(mesh.elements.n_elements):
                elem = mesh.elements.element_by_index(i)
                if len(elem.node_ids) == 2:
                    bid = elem.id
                    beam_ids.append(bid)

                    ni, nj = elem.node_ids
                    ci = np.array(mesh.nodes.node_by_id(ni).coordinates)
                    cj = np.array(mesh.nodes.node_by_id(nj).coordinates)

                    axis = cj - ci
                    axis = axis / np.linalg.norm(axis)
                    axes[bid] = axis

            beam_scope = dpf.Scoping()
            beam_scope.ids = beam_ids
            op.inputs.mesh_scoping.connect(beam_scope)

            time_freq = model.metadata.time_freq_support
            frequencies = time_freq.time_frequencies.data

            self.progress.emit(40)

            # ==========================
            # СТАТИКА
            # ==========================
            if "static" in analysis or len(frequencies) == 1:

                self.status.emit("Статика...")

                fc = op.outputs.fields_container()
                field = fc[0]

                results = []

                for bid in beam_ids:
                    data = field.get_entity_data_by_id(bid)
                    if len(data) < 2:
                        continue

                    Fj = data[1][:3]
                    axial = np.dot(Fj, axes[bid])

                    results.append({"BeamID": bid, "Axial": axial})

                df = pd.DataFrame(results)
                df.to_excel(os.path.join(self.folder, "static.xlsx"), index=False)

            # ==========================
            # ГАРМОНИКА
            # ==========================
            else:

                self.status.emit("Гармоника...")

                phases = np.radians([0,30,60,90,120,150,180])
                results = []

                for t, freq in enumerate(frequencies):

                    self.progress.emit(40 + int(50 * t / len(frequencies)))

                    ts = dpf.Scoping()
                    ts.ids = [t + 1]
                    op.inputs.time_scoping.connect(ts)

                    fc = op.outputs.fields_container()
                    if len(fc) < 2:
                        continue

                    field_re = fc[0]
                    field_im = fc[1]

                    for bid in beam_ids:

                        data_re = field_re.get_entity_data_by_id(bid)
                        data_im = field_im.get_entity_data_by_id(bid)

                        if len(data_re) < 2:
                            continue

                        Fj_re = data_re[1][:3]
                        Fj_im = data_im[1][:3]

                        vals = []

                        for phi in phases:
                            force = Fj_re*np.cos(phi)+Fj_im*np.sin(phi)
                            axial = np.dot(force, axes[bid])
                            shear = np.sqrt(np.linalg.norm(force)**2 - axial**2)
                            vals.append((axial, shear))

                        vals = np.array(vals)
                        idx = np.argmax(np.abs(vals[:,0]))

                        results.append({
                            "BeamID": bid,
                            "Freq": freq,
                            "Axial": vals[idx,0],
                            "Shear": vals[idx,1]
                        })

                df = pd.DataFrame(results)
                df.to_excel(os.path.join(self.folder, "harmonic.xlsx"), index=False)

            self.progress.emit(100)
            self.status.emit("Готово")
            self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))

# ==========================
# GUI
# ==========================
class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Beam Analyzer")
        self.resize(400, 200)

        self.layout = QVBoxLayout()

        self.label = QLabel("Папка не выбрана")
        self.layout.addWidget(self.label)

        self.btn_select = QPushButton("Выбрать папку")
        self.btn_select.clicked.connect(self.select_folder)
        self.layout.addWidget(self.btn_select)

        self.btn_run = QPushButton("Запустить")
        self.btn_run.clicked.connect(self.run)
        self.layout.addWidget(self.btn_run)

        self.progress = QProgressBar()
        self.layout.addWidget(self.progress)

        self.status = QLabel("Ожидание...")
        self.layout.addWidget(self.status)

        self.setLayout(self.layout)

        self.folder = None

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Выбери папку")
        if folder:
            self.folder = folder
            self.label.setText(folder)

    def run(self):
        if not self.folder:
            QMessageBox.warning(self, "Ошибка", "Выбери папку")
            return

        self.worker = Worker(self.folder)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.status.connect(self.status.setText)
        self.worker.finished.connect(lambda: QMessageBox.information(self, "OK", "Готово"))
        self.worker.error.connect(lambda e: QMessageBox.critical(self, "Ошибка", e))

        self.worker.start()

# ==========================
# ЗАПУСК
# ==========================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())