import sys, os, tempfile, subprocess
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import cv2

APP_TITLE = "PS3 Coldboot RAF Maker"

def get_ffmpeg():
    base = getattr(sys, '_MEIPASS', os.path.dirname(__file__))
    return os.path.join(base, "ffmpeg.exe")

class DropList(QListWidget):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        event.accept()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            self.addItem(path)

class ColdbootMaker(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(600, 520)

        layout = QVBoxLayout()

        title = QLabel("PS3 Coldboot RAF Creator")
        title.setStyleSheet("font-size:18px;font-weight:bold")
        layout.addWidget(title)

        layout.addWidget(QLabel("Drag files below (png/jpg/mp4)"))

        self.list = DropList()
        layout.addWidget(self.list)

        btns = QHBoxLayout()

        add = QPushButton("Add")
        add.clicked.connect(self.add_files)
        btns.addWidget(add)

        remove = QPushButton("Remove")
        remove.clicked.connect(self.remove)
        btns.addWidget(remove)

        preview = QPushButton("Preview")
        preview.clicked.connect(self.preview)
        btns.addWidget(preview)

        layout.addLayout(btns)

        self.preview_label = QLabel()
        self.preview_label.setFixedHeight(200)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("background:#111;border:1px solid #333")
        layout.addWidget(self.preview_label)

        self.name = QLineEdit()
        self.name.setPlaceholderText("output name")
        layout.addWidget(self.name)

        export = QPushButton("EXPORT RAF")
        export.clicked.connect(self.export)
        export.setStyleSheet("height:40px;font-weight:bold")
        layout.addWidget(export)

        self.status = QLabel("")
        layout.addWidget(self.status)

        self.setLayout(layout)

    def add_files(self):
        files,_ = QFileDialog.getOpenFileNames(
            self,"media","","Media (*.png *.jpg *.mp4 *.avi)"
        )
        for f in files:
            self.list.addItem(f)

    def remove(self):
        for i in self.list.selectedItems():
            self.list.takeItem(self.list.row(i))

    def preview(self):
        item = self.list.currentItem()
        if not item:
            return

        path = item.text()

        if path.lower().endswith((".png",".jpg",".jpeg")):
            pix = QPixmap(path).scaled(
                500,200,
                Qt.AspectRatioMode.KeepAspectRatio
            )
            self.preview_label.setPixmap(pix)
            return

        cap = cv2.VideoCapture(path)
        ret, frame = cap.read()
        cap.release()

        if ret:
            temp = os.path.join(tempfile.gettempdir(),"preview.jpg")
            cv2.imwrite(temp, frame)
            pix = QPixmap(temp).scaled(
                500,200,
                Qt.AspectRatioMode.KeepAspectRatio
            )
            self.preview_label.setPixmap(pix)

    def export(self):
        if self.list.count() == 0:
            self.status.setText("add media first")
            return

        if not self.name.text():
            self.status.setText("enter name")
            return

        ffmpeg = get_ffmpeg()

        txt = os.path.join(tempfile.gettempdir(),"raf.txt")

        with open(txt,"w") as f:
            for i in range(self.list.count()):
                p = self.list.item(i).text()
                f.write(f"file '{os.path.abspath(p)}'\n")

        out = self.name.text() + ".raf"

        subprocess.run([
            ffmpeg,
            "-y",
            "-f","concat",
            "-safe","0",
            "-i",txt,
            "-vf","scale=1920:1080",
            "-c:v","mpeg2video",
            "-pix_fmt","yuv420p",
            "-r","60",
            out
        ])

        self.status.setText("done: " + out)

app = QApplication(sys.argv)
w = ColdbootMaker()
w.show()
sys.exit(app.exec())