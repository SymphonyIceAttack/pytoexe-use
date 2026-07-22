"code-keyword">import sys
"code-keyword">import os
"code-keyword">import time
"code-keyword">import traceback
"code-keyword">from dataclasses "code-keyword">import dataclass

"code-keyword">import numpy "code-keyword">as np
"code-keyword">import onnxruntime "code-keyword">as ort

"code-keyword">from PySide6.QtCore "code-keyword">import Qt, QTimer, Signal, QObject
"code-keyword">from PySide6.QtGui "code-keyword">import QImage, QPixmap
"code-keyword">from PySide6.QtWidgets "code-keyword">import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QLineEdit, QComboBox, QSpinBox, QCheckBox, QTextEdit,
    QTabWidget, QGroupBox, QMessageBox, QListWidget, QListWidgetItem,
    QFormLayout, QDoubleSpinBox, QSlider, QSizePolicy
)

"code-keyword">import cv2
"code-keyword">from PIL "code-keyword">import Image


# -----------------------------
# Utilities
# -----------------------------
"code-keyword">class="code-keyword">def numpy_to_qimage(img: np.ndarray) -> QImage:
    """
    img: BGR uint8 ">or RGB uint8
    """
    "code-keyword">if img "code-keyword">is None:
        "code-keyword">return QImage()
    "code-keyword">if img.ndim == 2:
        # grayscale
        h, w = img.shape
        "code-keyword">return QImage(img.data, w, h, w, QImage.Format_Grayscale8).copy()
    "code-keyword">if img.shape[2] == 3:
        # assume BGR -> RGB
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, _ = rgb.shape
        "code-keyword">return QImage(rgb.data, w, h, 3 * w, QImage.Format_RGB888).copy()
    "code-keyword">return QImage()


"code-keyword">class="code-keyword">def safe_float(x, default=0.0):
    "code-keyword">try:
        "code-keyword">return float(x)
    "code-keyword">except Exception:
        "code-keyword">return default


@dataclass
"code-keyword">class ProviderConfig:
    provider_name: str
    threads: int
    fp16: bool
    batch_size: int


# -----------------------------
# Inference engine (ONNX Runtime)
# -----------------------------
"code-keyword">class InferenceEngine(QObject):
    log = Signal(str)
    model_changed = Signal()
    output_updated = Signal(object)  # outputs
    metrics_updated = Signal(float, float)  # inference_ms, fps

    "code-keyword">class="code-keyword">def __init__(self):
        super().__init__()
        self.session = None
        self.model_path = None
        self.input_meta = []
        self.output_meta = []
        self.providers_supported = self._detect_providers()

        self.execution_provider = None
        self.threads = 0
        self.use_fp16 = False
        self.batch_size = 1

        # runtime stats
        self._last_frame_time = None
        self._fps = 0.0
        self._fps_alpha = 0.15  # smoothing

    "code-keyword">class="code-keyword">def _detect_providers(self):
        # List what ONNX Runtime reports "code-keyword">as available on this system
        "code-keyword">return list(ort.get_available_providers())

    "code-keyword">class="code-keyword">def set_config(self, cfg: ProviderConfig):
        self.execution_provider = cfg.provider_name
        self.threads = cfg.threads
        self.use_fp16 = cfg.fp16
        self.batch_size = cfg.batch_size

    "code-keyword">class="code-keyword">def load_model(self, model_path: str):
        self.model_path = model_path
        self.log.emit(f"Loading model: {model_path}")
        "code-keyword">try:
            so = ort.SessionOptions()
            "code-keyword">if self.threads "code-keyword">and self.threads > 0:
                so.intra_op_num_threads = int(self.threads)

            # FP16 switch: note that ONNX Runtime generally uses model graph dtype.
            # We'll attempt FP16 via optimization if supported by provider.
            # For true FP16, the model itself must be FP16 (or graph transformed).
            so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

            # Providers selection
            providers = self._choose_providers(self.execution_provider)

            # Create session
            self.session = ort.InferenceSession(model_path, sess_options=so, providers=providers)

            # Gather model IO
            self.input_meta = []
            self.output_meta = []
            for inp in self.session.get_inputs():
                self.input_meta.append({
                    "name": inp.name,
                    "type": str(inp.type),
                    "shape": inp.shape
                })
            for out in self.session.get_outputs():
                self.output_meta.append({
                    "name": out.name,
                    "type": str(out.type),
                    "shape": out.shape
                })

            self.log.emit("Model loaded successfully.")
            self.model_changed.emit()
            return True
        except Exception as e:
            self.log.emit("Failed to load model.")
            self.log.emit(str(e))
            self.log.emit(traceback.format_exc())
            self.session = None
            return False

    class="code-keyword">def _choose_providers(self, provider_name: str):
        available = self._detect_providers()
        # provider_name might be "CPUExecutionProvider" etc.
        if provider_name in available:
            return [provider_name]
        # fallback: if user asked for something not available
        if "CPUExecutionProvider" in available:
            self.log.emit(f"Provider '{provider_name}' not available. Falling back to CPU.")
            return ["CPUExecutionProvider"]
        return available[:1] if available else ["CPUExecutionProvider"]

    class="code-keyword">def _prepare_input_tensor(self, frame: np.ndarray):
        """
        Generic preprocessing:
        - If model expects NCHW: convert BGR->RGB, resize to first 2 dims if known.
        - Otherwise feed as-is.
        - Batch size is applied if first dimension is dynamic or fixed to 1.
        """
        if not self.session:
            return None

        # If multiple inputs exist, we only fill the first input (configurable in future).
        inp = self.session.get_inputs()[0]
        inp_name = inp.name
        expected_shape = inp.shape  # may contain None or strings

        x = frame
        # Convert BGR->RGB for typical vision models
        if x.ndim == 3 and x.shape[2] == 3:
            x = cv2.cvtColor(x, cv2.COLOR_BGR2RGB)

        # Determine resize if H/W known and rank is 4
        rank = len(expected_shape) if isinstance(expected_shape, (list, tuple)) else None
        if rank == 4:
            # expected: [N, C, H, W] or [N, H, W, C]
            n0, c0, h0, w0 = expected_shape
            if h0 is not None and w0 is not None and isinstance(h0, int) and isinstance(w0, int):
                x = cv2.resize(x, (w0, h0), interpolation=cv2.INTER_LINEAR)

            # Decide channel order: if c0 is 1/3, assume NCHW
            if c0 in (1, 3) or (isinstance(c0, str) and c0.lower() in ("c",)):
                # NCHW
                x = x.astype(np.float32)
                x = x.transpose(2, 0, 1)  # HWC -> CHW
                # Apply batch
                batch = self.batch_size if self.batch_size > 0 else 1
                x = np.expand_dims(x, 0)
                if batch != 1:
                    x = np.repeat(x, batch, axis=0)
                return {inp_name: x}
            else:
                # NHWC
                x = x.astype(np.float32)
                batch = self.batch_size if self.batch_size > 0 else 1
                x = np.expand_dims(x, 0)
                if batch != 1:
                    x = np.repeat(x, batch, axis=0)
                return {inp_name: x}

        # Fallback: single input, attempt to batch
        x = x.astype(np.float32)
        batch = self.batch_size if self.batch_size > 0 else 1
        if x.ndim == 2:
            x = np.expand_dims(x, -1)
        x = np.expand_dims(x, 0)
        if batch != 1:
            x = np.repeat(x, batch, axis=0)
        return {inp_name: x}

    class="code-keyword">def infer(self, frame: np.ndarray):
        if not self.session:
            return None

        try:
            inputs = self._prepare_input_tensor(frame)
            if inputs is None:
                return None

            t0 = time.perf_counter()
            outputs = self.session.run(None, inputs)
            t1 = time.perf_counter()

            infer_ms = (t1 - t0) * 1000.0

            # FPS based on wall-clock between calls
            now = time.perf_counter()
            if self._last_frame_time is None:
                fps = 0.0
            else:
                dt = now - self._last_frame_time
                fps = 1.0 / dt if dt > 0 else 0.0
            self._last_frame_time = now
            # smooth
            self._fps = fps if self._fps == 0.0 else (1 - self._fps_alpha) * self._fps + self._fps_alpha * fps

            self.metrics_updated.emit(infer_ms, self._fps)
            self.output_updated.emit(outputs)
            return outputs
        except Exception as e:
            self.log.emit("Inference failed.")
            self.log.emit(str(e))
            self.log.emit(traceback.format_exc())
            return None

    class="code-keyword">def get_model_info_text(self):
        if not self.session:
            return "No model loaded."
        lines = []
        lines.append("=== Model Information ===")
        lines.append("Inputs:")
        for i in self.input_meta:
            lines.append(f"- {i['name']} | type={i['type']} | shape={i['shape']}")
        lines.append("Outputs:")
        for o in self.output_meta:
            lines.append(f"- {o['name']} | type={o['type']} | shape={o['shape']}")
        lines.append("Supported providers (available on this system):")
        ">for p ">in self.providers_supported:
            lines.append(f"- {p}")
        ">return "\n".join(lines)


# -----------------------------
# Webcam / input manager
# -----------------------------
">class InputSource(QObject):
    frame_ready = Signal(np.ndarray)
    status = Signal(str)

    ">class="code-keyword">def __init__(self):
        super().__init__()
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        self.running = False
        self.device_index = 0
        self.target_fps = 30

    ">class="code-keyword">def start_webcam(self, device_index=0, target_fps=30):
        self.stop()
        self.device_index = device_index
        self.target_fps = target_fps

        self.cap = cv2.VideoCapture(self.device_index)
        ">if ">not self.cap.isOpened():
            self.status.emit("Failed to open webcam.")
            self.stop()
            ">return False

        self.running = True
        self.status.emit("Webcam started.")
        interval_ms = max(1, int(1000 / self.target_fps))
        self.timer.start(interval_ms)
        ">return True

    ">class="code-keyword">def _tick(self):
        ">if ">not self.running ">or ">not self.cap:
            ">return
        ok, frame = self.cap.read()
        ">if ">not ok ">or frame ">is None:
            self.status.emit("Failed to read webcam frame.")
            ">return
        self.frame_ready.emit(frame)

    ">class="code-keyword">def stop(self):
        self.running = False
        self.timer.stop()
        ">if self.cap ">is ">not None:
            ">try:
                self.cap.release()
            ">except Exception:
                pass
        self.cap = None
        self.status.emit("Webcam stopped.")

    ">class="code-keyword">def running_source(self):
        ">return self.running


# -----------------------------
# UI
# -----------------------------
">class DropArea(QWidget):
    files_dropped = Signal(list)

    ">class="code-keyword">def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setLayout(QVBoxLayout())
        self.label = QLabel("Drag & drop .onnx model files here")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("color: rgba(220,220,220,0.9); font-size: 14px;")
        self.layout().addWidget(self.label)

        self.setStyleSheet("""
            QWidget{
                border: 1px dashed rgba(160,160,160,0.55);
                border-radius: 10px;
                background-color: rgba(30,30,35,0.35);
            }
        """)

    ">class="code-keyword">def dragEnterEvent(self, event):
        ">if event.mimeData().hasUrls():
            event.acceptProposedAction()
        ">else:
            event.ignore()

    ">class="code-keyword">def dropEvent(self, event):
        urls = event.mimeData().urls()
        paths = [u.toLocalFile() ">for u ">in urls ">if u.isLocalFile()]
        onnx = [p ">for p ">in paths ">if p.lower().endswith(".onnx")]
        ">if onnx:
            self.files_dropped.emit(onnx)
        event.acceptProposedAction()


">class MainWindow(QMainWindow):
    ">class="code-keyword">def __init__(self):
        super().__init__()
        self.setWindowTitle("Cyrex AI Runtime - ONNX Runner (fortnitepeelypro)")
        self.resize(1200, 720)

        self.engine = InferenceEngine()
        self.input_source = InputSource()

        self._build_ui()
        self._connect_signals()
        self._apply_dark_theme()

        self.current_image = None
        self.last_outputs = None

        self.engine.set_config(self._read_config_from_ui())

    ">class="code-keyword">def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root = QHBoxLayout(central)

        # Left: Controls + model loader
        left = QVBoxLayout()
        root.addLayout(left, 2)

        self.drop_area = DropArea()
        left.addWidget(self.drop_area)

        btn_row = QHBoxLayout()
        self.btn_browse_model = QPushButton("Browse Model (.onnx)")
        self.btn_clear = QPushButton("Clear")
        btn_row.addWidget(self.btn_browse_model)
        btn_row.addWidget(self.btn_clear)
        left.addLayout(btn_row)

        # Execution / Input controls
        group = QGroupBox("Inference")
        group_layout = QVBoxLayout(group)

        input_row = QHBoxLayout()
        self.btn_load_image = QPushButton("Load Image")
        self.btn_run_image = QPushButton("Run on Image")
        input_row.addWidget(self.btn_load_image)
        input_row.addWidget(self.btn_run_image)
        group_layout.addLayout(input_row)

        cam_row = QHBoxLayout()
        self.btn_start_cam = QPushButton("Start Webcam")
        self.btn_stop_cam = QPushButton("Stop")
        self.cam_device = QSpinBox()
        self.cam_device.setRange(0, 10)
        self.cam_device.setValue(0)
        cam_row.addWidget(self.btn_start_cam)
        cam_row.addWidget(self.btn_stop_cam)
        cam_row.addWidget(QLabel("Device:"))
        cam_row.addWidget(self.cam_device)
        group_layout.addLayout(cam_row)

        # Metrics
        metrics_row = QHBoxLayout()
        self.lbl_infer = QLabel("Inference: - ms")
        self.lbl_fps = QLabel("FPS: -")
        metrics_row.addWidget(self.lbl_infer)
        metrics_row.addWidget(self.lbl_fps)
        group_layout.addLayout(metrics_row)

        # Preview
        self.preview = QLabel("Preview will appear here")
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumHeight(260)
        self.preview.setStyleSheet("""
            QLabel{
                border: 1px solid rgba(160,160,160,0.25);
                border-radius: 10px;
                background-color: rgba(20,20,25,0.35);
                color: rgba(220,220,220,0.75);
            }
        """)
        self.preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        group_layout.addWidget(self.preview)

        left.addWidget(group, 1)

        # Right: Tabs
        right_tabs = QTabWidget()
        root.addWidget(right_tabs, 4)

        # Settings tab
        settings_tab = QWidget()
        s_layout = QVBoxLayout(settings_tab)

        s_form = QFormLayout()
        self.cmb_provider = QComboBox()
        self.cmb_provider.addItems(self.engine.providers_supported ">if self.engine.providers_supported ">else ["CPUExecutionProvider"])

        self.sp_threads = QSpinBox()
        self.sp_threads.setRange(0, 256)
        self.sp_threads.setValue(0)

        self.chk_fp16 = QCheckBox("Use FP16 ("code-keyword">if supported)")
        self.sp_batch = QSpinBox()
        self.sp_batch.setRange(1, 64)
        self.sp_batch.setValue(1)

        self.sp_batch.setToolTip("Batch size to repeat inputs "code-keyword">if model input accepts batching.")

        s_form.addRow("Execution Provider:", self.cmb_provider)
        s_form.addRow("Threads:", self.sp_threads)
        s_form.addRow("", self.chk_fp16)
        s_form.addRow("Batch size:", self.sp_batch)

        s_layout.addLayout(s_form)

        s_btn_row = QHBoxLayout()
        self.btn_apply_settings = QPushButton("Apply Settings (Recreate Session)")
        self.btn_refresh_providers = QPushButton("Refresh Providers")
        s_btn_row.addWidget(self.btn_apply_settings)
        s_btn_row.addWidget(self.btn_refresh_providers)
        s_layout.addLayout(s_btn_row)

        s_help = QLabel("If you change execution provider / threads, the app recreates the ONNX Runtime session.")
        s_help.setWordWrap(True)
        s_help.setStyleSheet("color: rgba(210,210,210,0.7); font-size: 12px;")
        s_layout.addWidget(s_help)

        right_tabs.addTab(settings_tab, "Settings")

        # Output tab
        output_tab = QWidget()
        o_layout = QVBoxLayout(output_tab)

        self.output_view = QTextEdit()
        self.output_view.setReadOnly(True)
        self.output_view.setStyleSheet("font-family: Consolas, monospace; font-size: 12px;")
        o_layout.addWidget(self.output_view)

        self.output_list = QListWidget()
        self.output_list.setFixedHeight(220)
        o_layout.addWidget(QLabel("Top outputs (quick view):"))
        o_layout.addWidget(self.output_list)

        right_tabs.addTab(output_tab, "Live Output")

        # Model Info tab
        info_tab = QWidget()
        i_layout = QVBoxLayout(info_tab)
        self.model_info_text = QTextEdit()
        self.model_info_text.setReadOnly(True)
        self.model_info_text.setStyleSheet("font-family: Consolas, monospace; font-size: 12px;")
        i_layout.addWidget(self.model_info_text)
        right_tabs.addTab(info_tab, "Model Info")

        # Console / Log tab
        log_tab = QWidget()
        l_layout = QVBoxLayout(log_tab)
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setStyleSheet("font-family: Consolas, monospace; font-size: 12px;")
        l_layout.addWidget(self.log_view)
        right_tabs.addTab(log_tab, "Console / Log")

        # About tab
        about_tab = QWidget()
        a_layout = QVBoxLayout(about_tab)
        about_text = QLabel(
            "<b>Cyrex AI Runtime</b><br>"
            "Maker: <b>fortnitepeelypro</b><br><br>"
            "Features:<br>"
            "• Dark theme UI<br>"
            "• Load any .onnx model<br>"
            "• Drag & drop<br>"
            "• Image "code-keyword">or webcam input<br>"
            "• Inference time + FPS<br>"
            "• Provider/threads/batch settings<br>"
        )
        about_text.setWordWrap(True)
        a_layout.addWidget(about_text)
        a_layout.addStretch(1)
        right_tabs.addTab(about_tab, "About")

        # Bottom row buttons
        left.addStretch(1)

        # Connections that depend on UI build
        self.btn_apply_settings.clicked.connect(self.on_apply_settings)
        self.btn_refresh_providers.clicked.connect(self.on_refresh_providers)
        self.drop_area.files_dropped.connect(self.on_models_dropped)
        self.btn_browse_model.clicked.connect(self.on_browse_model)
        self.btn_clear.clicked.connect(self.on_clear)

        self.btn_load_image.clicked.connect(self.on_load_image)
        self.btn_run_image.clicked.connect(self.on_run_image)

        self.btn_start_cam.clicked.connect(self.on_start_cam)
        self.btn_stop_cam.clicked.connect(self.on_stop_cam)

        self.btn_run_image.setEnabled(False)

    ">class="code-keyword">def _connect_signals(self):
        self.engine.log.connect(self.append_log)
        self.engine.model_changed.connect(self.on_model_loaded)
        self.engine.output_updated.connect(self.on_outputs)
        self.engine.metrics_updated.connect(self.on_metrics)

        self.input_source.frame_ready.connect(self.on_webcam_frame)
        self.input_source.status.connect(self.append_log)

    ">class="code-keyword">def _apply_dark_theme(self):
        app = QApplication.instance()
        ">if app:
            app.setStyleSheet("""
                QWidget { color: rgba(230,230,230,0.92); }
                QMainWindow { background-color: #0f1117; }
                QLabel { color: rgba(230,230,230,0.92); }
                QTabWidget::pane { border: 1px solid rgba(160,160,160,0.15); }
                QTabBar::tab {
                    background: rgba(20,20,30,0.75);
                    border: 1px solid rgba(160,160,160,0.15);
                    padding: 8px 14px;
                    margin-right: 4px;
                    border-top-left-radius: 8px;
                    border-top-right-radius: 8px;
                }
                QTabBar::tab:selected {
                    background: rgba(35,35,50,0.95);
                    border-bottom-color: rgba(35,35,50,0.95);
                }
                QPushButton {
                    background-color: rgba(30,30,45,0.95);
                    border: 1px solid rgba(160,160,160,0.2);
                    border-radius: 10px;
                    padding: 10px;
                }
                QPushButton:hover {
                    background-color: rgba(45,45,70,0.95);
                }
                QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit {
                    background-color: rgba(18,18,26,0.9);
                    border: 1px solid rgba(160,160,160,0.18);
                    border-radius: 10px;
                    padding: 6px;
                }
                QCheckBox::indicator { width: 16px; height: 16px; }
                QCheckBox { padding-left: 6px; }
                QListWidget {
                    background-color: rgba(18,18,26,0.9);
                    border: 1px solid rgba(160,160,160,0.18);
                    border-radius: 10px;
                }
            """)

    ">class="code-keyword">def _read_config_from_ui(self) -> ProviderConfig:
        provider = self.cmb_provider.currentText()
        threads = int(self.sp_threads.value())
        fp16 = bool(self.chk_fp16.isChecked())
        batch = int(self.sp_batch.value())
        ">return ProviderConfig(provider_name=provider, threads=threads, fp16=fp16, batch_size=batch)

    ">class="code-keyword">def on_refresh_providers(self):
        self.engine.providers_supported = list(ort.get_available_providers())
        self.cmb_provider.clear()
        self.cmb_provider.addItems(self.engine.providers_supported ">if self.engine.providers_supported ">else ["CPUExecutionProvider"])
        self.append_log(f"Available providers: {self.engine.providers_supported}")

    ">class="code-keyword">def on_apply_settings(self):
        ">if ">not self.engine.model_path:
            QMessageBox.information(self, "No model", "Load a model first.")
            ">return
        cfg = self._read_config_from_ui()
        self.engine.set_config(cfg)
        self.append_log(f"Applying settings: {cfg}")
        ok = self.engine.load_model(self.engine.model_path)
        ">if ">not ok:
            QMessageBox.warning(self, "Error", "Failed to apply settings.")
        # update UI
        self.model_info_text.setPlainText(self.engine.get_model_info_text())

    ">class="code-keyword">def on_models_dropped(self, paths):
        ">if ">not paths:
            ">return
        # pick first
        self.load_model_file(paths[0])

    ">class="code-keyword">def on_browse_model(self):
        p, _ = QFileDialog.getOpenFileName(self, "Select ONNX Model", "", "ONNX Files (*.onnx)")
        ">if p:
            self.load_model_file(p)

    ">class="code-keyword">def on_clear(self):
        self.engine.session = None
        self.engine.model_path = None
        self.current_image = None
        self.preview.setText("Preview will appear here")
        self.output_view.clear()
        self.output_list.clear()
        self.model_info_text.setPlainText("No model loaded.")
        self.log_view.clear()
        self.lbl_infer.setText("Inference: - ms")
        self.lbl_fps.setText("FPS: -")
        self.btn_run_image.setEnabled(False)
        self.input_source.stop()

    ">class="code-keyword">def load_model_file(self, model_path):
        cfg = self._read_config_from_ui()
        self.engine.set_config(cfg)
        ok = self.engine.load_model(model_path)
        ">if ">not ok:
            QMessageBox.warning(self, "Load failed", "Could "code-keyword">not load model. Check console/log.")
            ">return
        self.model_info_text.setPlainText(self.engine.get_model_info_text())
        self.btn_run_image.setEnabled(True)

    ">class="code-keyword">def on_model_loaded(self):
        self.model_info_text.setPlainText(self.engine.get_model_info_text())
        self.append_log("UI updated "code-keyword">with model info.")

    ">class="code-keyword">def on_load_image(self):
        p, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Images (*.png *.jpg *.jpeg *.bmp *.webp)")
        ">if ">not p:
            ">return
        img = cv2.imread(p, cv2.IMREAD_COLOR)
        ">if img ">is None:
            QMessageBox.warning(self, "Error", "Failed to load image.")
            ">return
        self.current_image = img
        self.preview.setPixmap(QPixmap.fromImage(numpy_to_qimage(img)).scaled(
            self.preview.width(), self.preview.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))

    ">class="code-keyword">def on_run_image(self):
        ">if self.current_image ">is None:
            QMessageBox.information(self, "No image", "Load an image first.")
            ">return
        ">if ">not self.engine.session:
            QMessageBox.information(self, "No model", "Load an ONNX model first.")
            ">return
        self.engine.infer(self.current_image)

    ">class="code-keyword">def on_start_cam(self):
        ">if ">not self.engine.session:
            QMessageBox.information(self, "No model", "Load an ONNX model first.")
            ">return
        ok = self.input_source.start_webcam(self.cam_device.value(), target_fps=30)
        ">if ">not ok:
            ">return
        self.btn_start_cam.setEnabled(False)

    ">class="code-keyword">def on_stop_cam(self):
        self.input_source.stop()
        self.btn_start_cam.setEnabled(True)

    ">class="code-keyword">def on_webcam_frame(self, frame: np.ndarray):
        # preview
        self.preview.setPixmap(QPixmap.fromImage(numpy_to_qimage(frame)).scaled(
            self.preview.width(), self.preview.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))
        # inference (can be throttled; currently runs each frame)
        self.engine.infer(frame)

    ">class="code-keyword">def on_outputs(self, outputs):
        self.last_outputs = outputs
        # Format outputs ">for the viewer
        lines = []
        self.output_list.clear()

        ">if ">not outputs:
            self.output_view.setPlainText("No outputs.")
            ">return

        ">for idx, out ">in enumerate(outputs):
            arr = np.array(out)
            shape = list(arr.shape)
            dtype = str(arr.dtype)

            # show small preview
            flat = arr.reshape(-1)
            preview_vals = flat[: min(10, flat.size)]
            preview_str = np.array2string(preview_vals, precision=4, separator=", ")

            lines.append(f"[Output {idx}] shape={shape}, dtype={dtype}")
            lines.append(f"  first values: {preview_str}")

            item = QListWidgetItem(f"Output {idx}: shape={shape}, dtype={dtype}")
            self.output_list.addItem(item)

        self.output_view.setPlainText("\n".join(lines))

    ">class="code-keyword">def on_metrics(self, infer_ms: float, fps: float):
        self.lbl_infer.setText(f"Inference: {infer_ms:.2f} ms")
        self.lbl_fps.setText(f"FPS: {fps:.2f}")

    ">class="code-keyword">def append_log(self, msg: str):
        ">if msg ">is None:
            ">return
        ts = time.strftime("%H:%M:%S")
        self.log_view.append(f"[{ts}] {msg}")
        self.log_view.verticalScrollBar().setValue(self.log_view.verticalScrollBar().maximum())


">class="code-keyword">def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


">if __name__ == "__main__":
    main()