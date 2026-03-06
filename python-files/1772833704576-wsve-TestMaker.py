#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TestMaker v2 — Soru Fotoğraflarından PDF Oluşturucu
Her PNG bir sorudur. İki sütunlu A4: Sol 1,3,5… | Sağ 2,4,6…
"""

import sys, os, platform
from pathlib import Path
from io import BytesIO
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QScrollArea, QFrame, QFileDialog, QMessageBox,
    QGroupBox, QComboBox, QCheckBox, QSplitter, QLineEdit, QProgressBar,
    QToolButton, QGridLayout, QDoubleSpinBox, QSpinBox, QColorDialog, QShortcut,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap, QImage, QColor, QKeySequence

from PIL import Image
from reportlab.lib.pagesizes import A4, A3, letter
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader

# ─── Sabitler ─────────────────────────────────────────────────────────────────
THUMB_SIZE = 170
VERSION    = "2.1"

PAGE_SIZES = {
    "A4  (210×297 mm)":    A4,
    "A3  (297×420 mm)":    A3,
    "Letter (216×279 mm)": letter,
}
LAYOUT_MODES = {
    "İki Sütun  |  Sol 1,3,5…  |  Sağ 2,4,6…": "two_col",
    "Tek Sütun  |  Tüm sorular arka arkaya":     "one_col",
    "Her Soru Ayrı Sayfada":                     "one_per_page",
}

# ─── Buton stilleri (tema override sorununu önlemek için inline) ──────────────
S_BTN = (
    "QPushButton{background:#313244;color:#cdd6f4;border:1px solid #45475a;"
    "border-radius:6px;padding:5px 12px;}"
    "QPushButton:hover{background:#45475a;border-color:#cba6f7;color:#cdd6f4;}"
    "QPushButton:pressed{background:#585b70;color:#cdd6f4;}"
)
S_BTN_GREEN = (
    "QPushButton{background:#a6e3a1;color:#1e1e2e;font-weight:bold;"
    "font-size:14px;padding:8px 24px;border:none;border-radius:8px;}"
    "QPushButton:hover{background:#94e2d5;color:#1e1e2e;}"
    "QPushButton:disabled{background:#45475a;color:#6c7086;border:none;}"
)
S_BTN_RED = (
    "QPushButton{background:#f38ba8;color:#1e1e2e;font-weight:bold;"
    "border:none;border-radius:6px;padding:5px 14px;}"
    "QPushButton:hover{background:#eba0ac;color:#1e1e2e;}"
)
S_BTN_BLUE = (
    "QPushButton{background:#89b4fa;color:#1e1e2e;font-weight:bold;"
    "border:none;border-radius:5px;padding:3px 8px;}"
    "QPushButton:hover{background:#74c7ec;color:#1e1e2e;}"
)

# ─── Genel koyu tema (buton stilleri hariç) ───────────────────────────────────
DARK_STYLE = """
QMainWindow, QDialog, QWidget {
    background: #1e1e2e;
    color: #cdd6f4;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}
QGroupBox {
    border: 1px solid #45475a;
    border-radius: 7px;
    margin-top: 10px;
    padding-top: 6px;
    font-weight: bold;
    color: #cba6f7;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
}
QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit {
    background: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 5px;
    padding: 4px 8px;
    min-height: 22px;
}
QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover, QLineEdit:hover {
    border-color: #cba6f7;
}
QComboBox QAbstractItemView {
    background: #313244;
    color: #cdd6f4;
    selection-background-color: #585b70;
}
QComboBox::drop-down { border: none; width: 20px; }
QScrollArea { border: none; }
QScrollBar:vertical {
    background: #313244; width: 7px; border-radius: 3px;
}
QScrollBar::handle:vertical {
    background: #585b70; border-radius: 3px; min-height: 20px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: #313244; height: 7px; border-radius: 3px;
}
QScrollBar::handle:horizontal {
    background: #585b70; border-radius: 3px;
}
QCheckBox { color: #cdd6f4; spacing: 6px; }
QCheckBox::indicator {
    width: 14px; height: 14px; border-radius: 3px;
    border: 2px solid #585b70; background: #313244;
}
QCheckBox::indicator:checked { background: #a6e3a1; border-color: #a6e3a1; }
QCheckBox:disabled { color: #585b70; }
QLabel { color: #cdd6f4; }
QProgressBar { background: #313244; border: none; border-radius: 3px; }
QProgressBar::chunk { background: #a6e3a1; border-radius: 3px; }
"""

# ─── Thumbnail Kart ───────────────────────────────────────────────────────────
class ThumbCard(QFrame):
    remove_me = pyqtSignal(object)
    clicked   = pyqtSignal(object)

    def __init__(self, path, index, parent=None):
        super().__init__(parent)
        self.path  = path
        self.index = index
        self._sel  = False
        self.setFixedSize(THUMB_SIZE + 22, THUMB_SIZE + 52)
        self.setFrameShape(QFrame.StyledPanel)
        self.setCursor(Qt.PointingHandCursor)
        self._build()
        self._load()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(3)

        top = QHBoxLayout()
        top.addStretch()
        bx = QToolButton()
        bx.setText("✕")
        bx.setFixedSize(20, 20)
        bx.setStyleSheet(
            "QToolButton{background:#f38ba8;color:#1e1e2e;border-radius:10px;"
            "font-size:11px;font-weight:bold;border:none;}"
            "QToolButton:hover{background:#eba0ac;color:#1e1e2e;}"
        )
        bx.clicked.connect(lambda: self.remove_me.emit(self))
        top.addWidget(bx)
        lay.addLayout(top)

        self.img_lbl = QLabel()
        self.img_lbl.setFixedSize(THUMB_SIZE, THUMB_SIZE)
        self.img_lbl.setAlignment(Qt.AlignCenter)
        self.img_lbl.setStyleSheet(
            "border:1px solid #45475a;border-radius:4px;background:#181825;color:#cdd6f4;")
        lay.addWidget(self.img_lbl, alignment=Qt.AlignCenter)

        name = Path(self.path).name
        if len(name) > 22:
            name = name[:10] + "…" + name[-9:]
        nl = QLabel(name)
        nl.setAlignment(Qt.AlignCenter)
        nl.setStyleSheet("color:#9399b2;font-size:11px;")
        lay.addWidget(nl)

        self.idx_lbl = QLabel()
        self.idx_lbl.setAlignment(Qt.AlignCenter)
        self.idx_lbl.setStyleSheet("color:#cba6f7;font-size:12px;font-weight:bold;")
        lay.addWidget(self.idx_lbl)
        self._refresh_badge()

    def _load(self):
        try:
            pil = Image.open(self.path)
            pil.thumbnail((THUMB_SIZE, THUMB_SIZE), Image.LANCZOS)
            buf = BytesIO()
            pil.save(buf, format="PNG")
            qi = QImage.fromData(buf.getvalue())
            self.img_lbl.setPixmap(QPixmap.fromImage(qi))
        except Exception as e:
            self.img_lbl.setText(f"Hata\n{e}")

    def _refresh_badge(self):
        col = "Sol" if self.index % 2 == 0 else "Sağ"
        self.idx_lbl.setText(f"#{self.index + 1}  ·  {col}")

    def set_index(self, idx):
        self.index = idx
        self._refresh_badge()

    def set_selected(self, val):
        self._sel = val
        if val:
            self.setStyleSheet(
                "QFrame{border:2px solid #cba6f7;border-radius:6px;background:#2a2a3e;}")
        else:
            self.setStyleSheet("")

    def mousePressEvent(self, e):
        self.clicked.emit(self)
        super().mousePressEvent(e)


# ─── Drop Zone ────────────────────────────────────────────────────────────────
class DropZone(QScrollArea):
    images_changed = pyqtSignal()

    EXTS = {'.png', '.jpg', '.jpeg', '.bmp', '.webp', '.tiff', '.tif'}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setWidgetResizable(True)
        self.image_paths = []
        self.cards = []
        self._sel  = None

        self.container = QWidget()
        self.container.setStyleSheet("background:#181825;border-radius:8px;")
        self.grid = QGridLayout(self.container)
        self.grid.setSpacing(10)
        self.grid.setContentsMargins(15, 15, 15, 15)
        self.setWidget(self.container)

        self.hint = QLabel(
            "Resimleri buraya sürükleyin\n"
            "veya  Ctrl+V  ile yapıştırın\n\n"
            "PNG  ·  JPG  ·  BMP  ·  WEBP  ·  TIFF"
        )
        self.hint.setAlignment(Qt.AlignCenter)
        self.hint.setStyleSheet("font-size:15px;color:#6c7086;padding:40px;")
        self.grid.addWidget(self.hint, 0, 0, 1, 4)

    # ── Drag & Drop ──────────────────────────────────────────────────────────
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
            self.container.setStyleSheet(
                "background:#2a2a3e;border:2px dashed #cba6f7;border-radius:8px;")

    def dragLeaveEvent(self, e):
        self.container.setStyleSheet("background:#181825;border-radius:8px;")

    def dropEvent(self, e):
        self.container.setStyleSheet("background:#181825;border-radius:8px;")
        paths = [u.toLocalFile() for u in e.mimeData().urls()
                 if Path(u.toLocalFile()).suffix.lower() in self.EXTS]
        self.add_images(paths)

    # ── Clipboard ────────────────────────────────────────────────────────────
    def paste_from_clipboard(self):
        cb = QApplication.clipboard()
        md = cb.mimeData()
        if md.hasUrls():
            paths = [u.toLocalFile() for u in md.urls()
                     if Path(u.toLocalFile()).suffix.lower() in self.EXTS]
            if paths:
                self.add_images(paths)
                return
        if md.hasImage():
            img = cb.image()
            if not img.isNull():
                import tempfile
                fd, p = tempfile.mkstemp(suffix=".png", prefix="paste_")
                os.close(fd)
                img.save(p)
                self.add_images([p])

    # ── Yönetim ──────────────────────────────────────────────────────────────
    def add_images(self, paths):
        added = False
        for p in paths:
            if p not in self.image_paths:
                self.image_paths.append(p)
                card = ThumbCard(p, len(self.cards))
                card.remove_me.connect(self.remove_card)
                card.clicked.connect(self._select)
                self.cards.append(card)
                added = True
        if added:
            self._refresh()
            self.images_changed.emit()

    def remove_card(self, card):
        if card in self.cards:
            self.image_paths.remove(card.path)
            self.cards.remove(card)
            card.deleteLater()
        self._refresh()
        self.images_changed.emit()

    def _select(self, card):
        if self._sel:
            self._sel.set_selected(False)
        self._sel = card
        card.set_selected(True)

    def _refresh(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        if not self.cards:
            self.grid.addWidget(self.hint, 0, 0, 1, 4)
            self.hint.show()
            return
        self.hint.hide()
        cols = max(1, min(5, self.width() // (THUMB_SIZE + 32)))
        for i, card in enumerate(self.cards):
            card.set_index(i)
            self.grid.addWidget(card, i // cols, i % cols)

    def clear_all(self):
        for c in self.cards:
            c.deleteLater()
        self.cards.clear()
        self.image_paths.clear()
        self._sel = None
        self._refresh()
        self.images_changed.emit()

    def move_sel(self, direction):
        if not self._sel:
            return
        idx  = self.cards.index(self._sel)
        nidx = idx + direction
        if 0 <= nidx < len(self.cards):
            self.cards[idx], self.cards[nidx]             = self.cards[nidx], self.cards[idx]
            self.image_paths[idx], self.image_paths[nidx] = self.image_paths[nidx], self.image_paths[idx]
            self._refresh()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._refresh()


# ─── PDF Worker ───────────────────────────────────────────────────────────────
class PdfWorker(QThread):
    progress = pyqtSignal(int)
    done     = pyqtSignal(str)
    error    = pyqtSignal(str)

    def __init__(self, paths, out_path, settings):
        super().__init__()
        self.paths    = paths
        self.out_path = out_path
        self.s        = settings

    def _rl(self, pil_img):
        buf = BytesIO()
        pil_img.save(buf, format="PNG")
        buf.seek(0)
        return ImageReader(buf)

    def _load(self, path):
        img = Image.open(path)
        if img.mode == 'RGBA':
            bg = Image.new('RGB', img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3])
            return bg
        return img.convert('RGB') if img.mode != 'RGB' else img

    def _hex_rgb(self, hex_color):
        h = hex_color.lstrip('#')
        return int(h[0:2], 16)/255, int(h[2:4], 16)/255, int(h[4:6], 16)/255

    def _draw_badge(self, c, number, img_x, img_top, size, color_hex):
        """saveState/restoreState ile alfa sızmasını önler."""
        c.saveState()
        r  = size / 2
        cx = img_x + r + 2*mm
        cy = img_top - r - 2*mm
        c.setFillColorRGB(0, 0, 0, 0.25)
        c.circle(cx + 0.7, cy - 0.7, r, fill=1, stroke=0)
        rc, gc, bc = self._hex_rgb(color_hex)
        c.setFillColorRGB(rc, gc, bc)
        c.circle(cx, cy, r, fill=1, stroke=0)
        c.setStrokeColorRGB(1, 1, 1)
        c.setLineWidth(0.7)
        c.circle(cx, cy, r, fill=0, stroke=1)
        c.setFillColorRGB(1, 1, 1)
        fsz = size * 0.46
        c.setFont("Helvetica-Bold", fsz)
        txt = str(number)
        tw  = c.stringWidth(txt, "Helvetica-Bold", fsz)
        c.drawString(cx - tw/2, cy - fsz*0.36, txt)
        c.restoreState()

    def _draw_sep(self, c, x, y, w, color_hex):
        c.saveState()
        rc, gc, bc = self._hex_rgb(color_hex)
        c.setStrokeColorRGB(rc, gc, bc)
        c.setLineWidth(0.35)
        c.setDash(3, 3)
        c.line(x, y, x + w, y)
        c.restoreState()

    def _draw_header(self, c, text, pw, ph, margin):
        c.saveState()
        c.setFillColorRGB(0.38, 0.35, 0.58)
        c.setFont("Helvetica-Bold", 9)
        tw = c.stringWidth(text, "Helvetica-Bold", 9)
        c.drawString((pw - tw) / 2, ph - margin + 3*mm, text)
        c.setStrokeColorRGB(0.65, 0.62, 0.80)
        c.setLineWidth(0.4)
        c.line(margin, ph - margin + 1.5*mm, pw - margin, ph - margin + 1.5*mm)
        c.restoreState()

    def _draw_footer(self, c, page_num, total_pages, pw, margin):
        c.saveState()
        c.setFillColorRGB(0.52, 0.52, 0.62)
        c.setFont("Helvetica", 8)
        txt = f"{page_num}  /  {total_pages}"
        tw  = c.stringWidth(txt, "Helvetica", 8)
        c.drawString((pw - tw) / 2, margin * 0.4, txt)
        c.restoreState()

    def run(self):
        try:
            s = self.s
            page_size   = PAGE_SIZES[s["page_size"]]
            layout_mode = LAYOUT_MODES[s["layout_mode"]]
            margin      = s["margin_mm"] * mm
            img_gap     = s["img_gap_mm"] * mm
            col_gap     = 6 * mm
            pw, ph      = page_size

            show_header = s["show_header"] and s["header_text"].strip()
            header_text = s["header_text"].strip()
            show_footer = s["show_footer"]
            show_badge  = s["show_badge"]
            badge_color = s["badge_color"]
            badge_size  = s["badge_size"] * mm
            start_num   = s["start_num"]
            show_sep    = s["show_sep"]
            sep_color   = s["sep_color"]

            header_h      = 7*mm if show_header else 0
            footer_h      = 7*mm if show_footer else 0
            top_margin    = margin + header_h
            bottom_margin = margin + footer_h
            avail_h       = ph - top_margin - bottom_margin

            total = len(self.paths)
            imgs  = []
            for i, path in enumerate(self.paths):
                self.progress.emit(int(i / total * 35))
                imgs.append(self._load(path))

            def sh(pil, w):
                iw, ih = pil.size
                return ih * (w / iw)

            # Toplam sayfa sayısını önceden hesapla (alt bilgi için)
            if layout_mode == "two_col":
                cw_ = (pw - 2*margin - col_gap) / 2
                lh  = [sh(imgs[i], cw_) for i in range(0, total, 2)]
                rh  = [sh(imgs[i], cw_) for i in range(1, total, 2)]
                def cnt(heights):
                    p, idx = 0, 0
                    while idx < len(heights):
                        used, first = 0.0, True
                        while idx < len(heights):
                            h = heights[idx]
                            n = h if first else h + img_gap
                            if used + n <= avail_h + 0.5:
                                used += n; idx += 1; first = False
                            else:
                                break
                        p += 1
                        if first: idx += 1
                    return p
                total_pages = max(cnt(lh), cnt(rh)) if (lh or rh) else 1
            elif layout_mode == "one_per_page":
                total_pages = total
            else:
                cw_   = pw - 2*margin
                all_h = [sh(im, cw_) for im in imgs]
                total_pages, idx = 0, 0
                while idx < total:
                    used, first = 0.0, True
                    while idx < total:
                        h = all_h[idx]
                        n = h if first else h + img_gap
                        if used + n <= avail_h + 0.5:
                            used += n; idx += 1; first = False
                        else:
                            break
                    total_pages += 1
                    if first: idx += 1

            c = rl_canvas.Canvas(self.out_path, pagesize=page_size)

            def begin_page(pn):
                if show_header:
                    self._draw_header(c, header_text, pw, ph, margin)
                if layout_mode == "two_col":
                    cw2 = (pw - 2*margin - col_gap) / 2
                    div = margin + cw2 + col_gap/2
                    c.saveState()
                    c.setStrokeColorRGB(0.73, 0.73, 0.82)
                    c.setLineWidth(0.5)
                    c.line(div, bottom_margin, div, ph - top_margin)
                    c.restoreState()

            def end_page(pn):
                if show_footer:
                    self._draw_footer(c, pn, total_pages, pw, margin)
                c.showPage()

            def draw_img(pil_img, x, y_bottom, cw, h, q_num, is_first):
                if show_sep and not is_first:
                    self._draw_sep(c, x, y_bottom + h + img_gap/2, cw, sep_color)
                c.drawImage(self._rl(pil_img), x, y_bottom, cw, h, mask='auto')
                if show_badge:
                    self._draw_badge(c, q_num, x, y_bottom + h, badge_size, badge_color)

            # ── İki Sütun ────────────────────────────────────────────────────
            if layout_mode == "two_col":
                cw    = (pw - 2*margin - col_gap) / 2
                lx    = margin
                rx    = margin + cw + col_gap
                limgs = [(imgs[i], i) for i in range(0, total, 2)]
                rimgs = [(imgs[i], i) for i in range(1, total, 2)]
                lhs   = [sh(im, cw) for im, _ in limgs]
                rhs   = [sh(im, cw) for im, _ in rimgs]
                li = ri = pn = 0

                while li < len(limgs) or ri < len(rimgs):
                    pn += 1
                    begin_page(pn)

                    lp, used = [], 0.0
                    while li < len(limgs):
                        h = lhs[li]; need = h if not lp else h + img_gap
                        if used + need <= avail_h + 0.5:
                            lp.append((limgs[li], h)); used += need; li += 1
                        else: break

                    rp, used = [], 0.0
                    while ri < len(rimgs):
                        h = rhs[ri]; need = h if not rp else h + img_gap
                        if used + need <= avail_h + 0.5:
                            rp.append((rimgs[ri], h)); used += need; ri += 1
                        else: break

                    y = ph - top_margin
                    for k, ((pil, oi), h) in enumerate(lp):
                        y -= h
                        draw_img(pil, lx, y, cw, h, oi + start_num, k == 0)
                        y -= img_gap

                    y = ph - top_margin
                    for k, ((pil, oi), h) in enumerate(rp):
                        y -= h
                        draw_img(pil, rx, y, cw, h, oi + start_num, k == 0)
                        y -= img_gap

                    end_page(pn)
                    self.progress.emit(35 + int(pn / total_pages * 60))
                    if not lp and not rp:
                        break

            # ── Tek Sütun ────────────────────────────────────────────────────
            elif layout_mode == "one_col":
                cw    = pw - 2*margin
                all_h = [sh(im, cw) for im in imgs]
                idx = pn = 0
                while idx < total:
                    pn += 1
                    begin_page(pn)
                    y = ph - top_margin
                    first = True
                    while idx < total:
                        h = all_h[idx]
                        need = h if first else h + img_gap
                        if y - need >= bottom_margin - 0.5:
                            y -= h
                            draw_img(imgs[idx], margin, y, cw, h, idx + start_num, first)
                            y -= img_gap; idx += 1; first = False
                        else:
                            break
                    end_page(pn)
                    self.progress.emit(35 + int(idx / total * 60))
                    if first:
                        pn += 1; begin_page(pn)
                        iw, ih = imgs[idx].size
                        sc = min(cw / iw, avail_h / ih)
                        nw, nh = iw*sc, ih*sc
                        ox = margin + (cw-nw)/2; oy = bottom_margin + (avail_h-nh)/2
                        c.drawImage(self._rl(imgs[idx]), ox, oy, nw, nh, mask='auto')
                        if show_badge:
                            self._draw_badge(c, idx + start_num, ox, oy + nh,
                                             badge_size, badge_color)
                        end_page(pn); idx += 1

            # ── Her Soru Ayrı Sayfa ───────────────────────────────────────────
            elif layout_mode == "one_per_page":
                cw = pw - 2*margin
                for idx, pil in enumerate(imgs):
                    pn = idx + 1; begin_page(pn)
                    iw, ih = pil.size
                    sc = min(cw / iw, avail_h / ih)
                    nw, nh = iw*sc, ih*sc
                    ox = margin + (cw-nw)/2; oy = bottom_margin + (avail_h-nh)/2
                    c.drawImage(self._rl(pil), ox, oy, nw, nh, mask='auto')
                    if show_badge:
                        self._draw_badge(c, idx + start_num, ox, oy + nh,
                                         badge_size, badge_color)
                    end_page(pn)
                    self.progress.emit(35 + int(idx / total * 60))

            self.progress.emit(97)
            c.save()
            self.progress.emit(100)
            self.done.emit(self.out_path)

        except Exception as e:
            import traceback
            self.error.emit(str(e) + "\n" + traceback.format_exc())


# ─── Renk Butonu ─────────────────────────────────────────────────────────────
class ColorBtn(QPushButton):
    color_changed = pyqtSignal(str)

    def __init__(self, hex_color="#a6e3a1", parent=None):
        super().__init__(parent)
        self.hex_color = hex_color
        self.setFixedSize(36, 26)
        self._apply()
        self.clicked.connect(self._pick)

    def _apply(self):
        self.setStyleSheet(
            f"QPushButton{{background:{self.hex_color};border:1px solid #585b70;"
            f"border-radius:5px;}}"
            f"QPushButton:hover{{border:2px solid #cdd6f4;}}"
        )

    def _pick(self):
        col = QColorDialog.getColor(QColor(self.hex_color), self)
        if col.isValid():
            self.hex_color = col.name()
            self._apply()
            self.color_changed.emit(self.hex_color)

    def get_color(self):
        return self.hex_color


# ─── Ayarlar Paneli ───────────────────────────────────────────────────────────
class SettingsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setSpacing(10)
        lay.setContentsMargins(6, 6, 6, 6)

        def sublbl(text):
            l = QLabel(text)
            l.setStyleSheet("color:#9399b2;font-size:11px;margin-bottom:1px;")
            return l

        def grp(title):
            g = QGroupBox(title)
            v = QVBoxLayout(g)
            v.setSpacing(6)
            return g, v

        # ── 1. Sayfa & Düzen ─────────────────────────────────────────────────
        g1, v1 = grp("Sayfa & Düzen")
        v1.addWidget(sublbl("Sayfa boyutu"))
        self.combo_page = QComboBox()
        self.combo_page.addItems(list(PAGE_SIZES.keys()))
        v1.addWidget(self.combo_page)

        v1.addWidget(sublbl("Yerleşim"))
        self.combo_layout = QComboBox()
        self.combo_layout.addItems(list(LAYOUT_MODES.keys()))
        v1.addWidget(self.combo_layout)

        r = QHBoxLayout(); r.setSpacing(8)
        lv = QVBoxLayout(); lv.setSpacing(2)
        lv.addWidget(sublbl("Kenar (mm)"))
        self.spin_margin = QDoubleSpinBox()
        self.spin_margin.setRange(0, 30); self.spin_margin.setValue(8); self.spin_margin.setDecimals(1)
        lv.addWidget(self.spin_margin)
        rv = QVBoxLayout(); rv.setSpacing(2)
        rv.addWidget(sublbl("Boşluk (mm)"))
        self.spin_gap = QDoubleSpinBox()
        self.spin_gap.setRange(0, 20); self.spin_gap.setValue(4); self.spin_gap.setDecimals(1)
        rv.addWidget(self.spin_gap)
        r.addLayout(lv); r.addLayout(rv); v1.addLayout(r)
        lay.addWidget(g1)

        # ── 2. Soru Numaralandırma ────────────────────────────────────────────
        g2, v2 = grp("Soru Numaralandırma")
        self.chk_badge = QCheckBox("Köşe rozeti göster (soru no)")
        self.chk_badge.setChecked(False)
        v2.addWidget(self.chk_badge)

        self.badge_opts = QWidget()
        bv = QVBoxLayout(self.badge_opts)
        bv.setContentsMargins(0, 0, 0, 0); bv.setSpacing(4)

        r2 = QHBoxLayout(); r2.setSpacing(8)
        lv2 = QVBoxLayout(); lv2.setSpacing(2)
        lv2.addWidget(sublbl("Başlangıç no"))
        self.spin_start = QSpinBox()
        self.spin_start.setRange(1, 999); self.spin_start.setValue(1)
        lv2.addWidget(self.spin_start)
        rv2 = QVBoxLayout(); rv2.setSpacing(2)
        rv2.addWidget(sublbl("Boyut (mm)"))
        self.spin_bsz = QDoubleSpinBox()
        self.spin_bsz.setRange(3, 15); self.spin_bsz.setValue(6)
        rv2.addWidget(self.spin_bsz)
        r2.addLayout(lv2); r2.addLayout(rv2); bv.addLayout(r2)

        cr = QHBoxLayout(); cr.setSpacing(6)
        cr.addWidget(sublbl("Renk:"))
        self.badge_col = ColorBtn("#cba6f7")
        cr.addWidget(self.badge_col); cr.addStretch()
        bv.addLayout(cr)

        self.badge_opts.setVisible(False)
        v2.addWidget(self.badge_opts)
        self.chk_badge.toggled.connect(self.badge_opts.setVisible)
        lay.addWidget(g2)

        # ── 3. Başlık & Sayfa No ─────────────────────────────────────────────
        g3, v3 = grp("Başlık & Sayfa No")
        self.chk_header = QCheckBox("Sayfa başlığı göster")
        v3.addWidget(self.chk_header)
        self.edit_header = QLineEdit()
        self.edit_header.setPlaceholderText("Örn: Türev — 1. Test")
        self.edit_header.setEnabled(False)
        v3.addWidget(self.edit_header)
        self.chk_header.toggled.connect(self.edit_header.setEnabled)
        self.chk_footer = QCheckBox("Sayfa numarası göster  (1 / 3)")
        self.chk_footer.setChecked(True)
        v3.addWidget(self.chk_footer)
        lay.addWidget(g3)

        # ── 4. Soru Arası Ayraç ───────────────────────────────────────────────
        g4, v4 = grp("Soru Arası Ayraç")
        self.chk_sep = QCheckBox("Sorular arası kesik çizgi")
        v4.addWidget(self.chk_sep)
        sr = QHBoxLayout(); sr.setSpacing(6)
        sr.addWidget(sublbl("Renk:"))
        self.sep_col = ColorBtn("#45475a")
        sr.addWidget(self.sep_col); sr.addStretch()
        v4.addLayout(sr)
        lay.addWidget(g4)

        # ── 5. Çıktı Dosyası ─────────────────────────────────────────────────
        g5, v5 = grp("Çıktı Dosyası")
        v5.addWidget(sublbl("Dosya adı"))
        fr = QHBoxLayout(); fr.setSpacing(4)
        self.edit_out = QLineEdit("test_sorulari.pdf")
        fr.addWidget(self.edit_out)

        btn_ts = QPushButton("Tarih")
        btn_ts.setFixedWidth(46)
        btn_ts.setStyleSheet(S_BTN_BLUE)
        btn_ts.setToolTip("Otomatik zaman damgalı dosya adı")
        btn_ts.clicked.connect(self._auto_name)
        fr.addWidget(btn_ts)

        btn_br = QPushButton("…")
        btn_br.setFixedWidth(30)
        btn_br.setStyleSheet(S_BTN)
        btn_br.clicked.connect(self._browse)
        fr.addWidget(btn_br)
        v5.addLayout(fr)

        self.chk_open = QCheckBox("Oluşturulunca otomatik aç")
        self.chk_open.setChecked(True)
        v5.addWidget(self.chk_open)
        lay.addWidget(g5)

        lay.addStretch()

    def _auto_name(self):
        self.edit_out.setText(datetime.now().strftime("sorular_%Y%m%d_%H%M.pdf"))

    def _browse(self):
        p, _ = QFileDialog.getSaveFileName(self, "PDF Kaydet",
                                           self.edit_out.text(), "PDF (*.pdf)")
        if p:
            self.edit_out.setText(p if p.endswith(".pdf") else p + ".pdf")

    def get_settings(self):
        return {
            "page_size":   self.combo_page.currentText(),
            "layout_mode": self.combo_layout.currentText(),
            "margin_mm":   self.spin_margin.value(),
            "img_gap_mm":  self.spin_gap.value(),
            "show_badge":  self.chk_badge.isChecked(),
            "start_num":   self.spin_start.value(),
            "badge_color": self.badge_col.get_color(),
            "badge_size":  self.spin_bsz.value(),
            "show_header": self.chk_header.isChecked(),
            "header_text": self.edit_header.text(),
            "show_footer": self.chk_footer.isChecked(),
            "show_sep":    self.chk_sep.isChecked(),
            "sep_color":   self.sep_col.get_color(),
            "out_path":    self.edit_out.text(),
            "open_after":  self.chk_open.isChecked(),
        }


# ─── Ana Pencere ──────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"TestMaker v{VERSION}")
        self.resize(1180, 760)
        self.setMinimumSize(900, 560)
        self._worker = None
        self._build_ui()
        self._setup_shortcuts()

    def _build_ui(self):
        root_w = QWidget()
        self.setCentralWidget(root_w)
        root = QVBoxLayout(root_w)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Başlık Çubuğu ────────────────────────────────────────────────────
        hbar = QWidget()
        hbar.setFixedHeight(52)
        hbar.setStyleSheet("background:#181825;border-bottom:1px solid #313244;")
        hl = QHBoxLayout(hbar)
        hl.setContentsMargins(16, 0, 16, 0)
        hl.setSpacing(10)

        lbl_title = QLabel("TestMaker")
        lbl_title.setStyleSheet(
            "font-size:20px;font-weight:bold;color:#cba6f7;letter-spacing:1px;")
        hl.addWidget(lbl_title)

        vsep = QFrame(); vsep.setFrameShape(QFrame.VLine)
        vsep.setStyleSheet("background:#313244;margin:12px 4px;")
        vsep.setFixedWidth(1)
        hl.addWidget(vsep)

        lbl_sub = QLabel("Her PNG = 1 soru  ·  Sol: 1,3,5…  |  Sağ: 2,4,6…")
        lbl_sub.setStyleSheet("font-size:12px;color:#585b70;")
        hl.addWidget(lbl_sub)
        hl.addStretch()

        self.lbl_count = QLabel("  0 görüntü  ")
        self.lbl_count.setStyleSheet(
            "color:#cba6f7;font-weight:bold;font-size:13px;"
            "background:#313244;border-radius:10px;padding:2px 10px;")
        hl.addWidget(self.lbl_count)
        root.addWidget(hbar)

        # ── Araç Çubuğu ──────────────────────────────────────────────────────
        tbar = QWidget()
        tbar.setFixedHeight(46)
        tbar.setStyleSheet("background:#1e1e2e;border-bottom:1px solid #313244;")
        tl = QHBoxLayout(tbar)
        tl.setContentsMargins(12, 0, 12, 0)
        tl.setSpacing(6)

        def mkbtn(text, slot, style=S_BTN):
            b = QPushButton(text)
            b.setFixedHeight(30)
            b.setStyleSheet(style)
            b.clicked.connect(slot)
            return b

        tl.addWidget(mkbtn("➕  Resim Ekle",    self._open_files))
        tl.addWidget(mkbtn("📋  Yapıştır",       self._paste))

        vsep2 = QFrame(); vsep2.setFrameShape(QFrame.VLine)
        vsep2.setStyleSheet("background:#313244;margin:10px 2px;")
        vsep2.setFixedWidth(1)
        tl.addWidget(vsep2)

        tl.addWidget(mkbtn("▲  Yukarı",   lambda: self.dz.move_sel(-1)))
        tl.addWidget(mkbtn("▼  Aşağı",    lambda: self.dz.move_sel(+1)))

        self.btn_clear = mkbtn("🗑  Hepsini Sil", self._clear_all, S_BTN_RED)
        tl.addWidget(self.btn_clear)
        tl.addStretch()
        root.addWidget(tbar)

        # ── Gövde ─────────────────────────────────────────────────────────────
        body = QSplitter(Qt.Horizontal)
        body.setHandleWidth(1)
        body.setStyleSheet("QSplitter::handle{background:#313244;}")

        self.dz = DropZone()
        self.dz.images_changed.connect(self._update_count)
        body.addWidget(self.dz)

        # Sağ panel
        rw = QWidget()
        rw.setMinimumWidth(265); rw.setMaximumWidth(310)
        rw.setStyleSheet("background:#181825;")
        rl = QVBoxLayout(rw)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)

        lbl_panel = QLabel("   ⚙  AYARLAR")
        lbl_panel.setFixedHeight(30)
        lbl_panel.setStyleSheet(
            "background:#181825;color:#585b70;font-size:10px;"
            "font-weight:bold;letter-spacing:2px;border-bottom:1px solid #313244;")
        rl.addWidget(lbl_panel)

        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setStyleSheet("border:none;background:#181825;")
        sc.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.settings = SettingsPanel()
        sc.setWidget(self.settings)
        rl.addWidget(sc)

        body.addWidget(rw)
        body.setStretchFactor(0, 1)
        body.setStretchFactor(1, 0)
        root.addWidget(body)

        # ── Durum Çubuğu ─────────────────────────────────────────────────────
        sbar = QWidget()
        sbar.setFixedHeight(50)
        sbar.setStyleSheet("background:#181825;border-top:1px solid #313244;")
        sl = QHBoxLayout(sbar)
        sl.setContentsMargins(14, 0, 14, 0)
        sl.setSpacing(10)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setFixedHeight(6)
        self.progress.setFixedWidth(200)
        self.progress.setStyleSheet(
            "QProgressBar{background:#313244;border:none;border-radius:3px;}"
            "QProgressBar::chunk{background:#a6e3a1;border-radius:3px;}")
        sl.addWidget(self.progress)

        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("color:#585b70;font-size:12px;")
        sl.addWidget(self.lbl_status)
        sl.addStretch()

        self.btn_export = QPushButton("  ⚡  PDF Oluştur  ")
        self.btn_export.setFixedHeight(36)
        self.btn_export.setStyleSheet(S_BTN_GREEN)
        self.btn_export.setEnabled(False)
        self.btn_export.clicked.connect(self._export)
        sl.addWidget(self.btn_export)
        root.addWidget(sbar)

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+O"),      self, self._open_files)
        QShortcut(QKeySequence("Ctrl+V"),      self, self._paste)
        QShortcut(QKeySequence("Ctrl+Return"), self, self._export)

    def _open_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Resim Seç", "",
            "Resimler (*.png *.jpg *.jpeg *.bmp *.webp *.tiff *.tif)")
        if paths:
            self.dz.add_images(sorted(paths))

    def _paste(self):
        self.dz.paste_from_clipboard()

    def _clear_all(self):
        if not self.dz.image_paths:
            return
        if QMessageBox.question(
                self, "Hepsini Sil",
                "Tüm resimler silinsin mi?",
                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.dz.clear_all()

    def _update_count(self):
        n = len(self.dz.image_paths)
        self.lbl_count.setText(f"  {n} görüntü  ")
        self.btn_export.setEnabled(n > 0)
        # Stil sıfırlama (disabled → enabled geçişinde renk kaybolmasın)
        self.btn_export.setStyleSheet(S_BTN_GREEN)

    def _export(self):
        if not self.dz.image_paths:
            return
        if self._worker and self._worker.isRunning():
            return

        s   = self.settings.get_settings()
        out = s["out_path"]
        if not os.path.isabs(out):
            out = str(Path.home() / "Desktop" / out)
        if not out.endswith(".pdf"):
            out += ".pdf"

        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.btn_export.setEnabled(False)
        self.btn_export.setStyleSheet(S_BTN_GREEN)
        self.lbl_status.setText("PDF oluşturuluyor…")

        self._worker = PdfWorker(self.dz.image_paths[:], out, s)
        self._worker.progress.connect(self.progress.setValue)
        self._worker.done.connect(self._on_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_done(self, path):
        self.progress.setValue(100)
        self.lbl_status.setText(f"✅  Kaydedildi: {Path(path).name}")
        self.btn_export.setEnabled(True)
        self.btn_export.setStyleSheet(S_BTN_GREEN)
        QTimer.singleShot(3000, lambda: (
            self.progress.setVisible(False),
            self.lbl_status.setText("")
        ))
        s = self.settings.get_settings()
        if s["open_after"]:
            try:
                if platform.system() == "Windows":
                    os.startfile(path)
                elif platform.system() == "Darwin":
                    import subprocess; subprocess.run(["open", path])
                else:
                    import subprocess; subprocess.run(["xdg-open", path])
            except Exception:
                pass
        QMessageBox.information(self, "Başarılı ✅", f"PDF oluşturuldu!\n\n{path}")

    def _on_error(self, msg):
        self.progress.setVisible(False)
        self.btn_export.setEnabled(True)
        self.btn_export.setStyleSheet(S_BTN_GREEN)
        self.lbl_status.setText("❌  Hata!")
        QMessageBox.critical(self, "Hata", f"PDF oluşturulurken hata:\n{msg}")

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_V and e.modifiers() == Qt.ControlModifier:
            self._paste()
        else:
            super().keyPressEvent(e)


# ─── Giriş Noktası ────────────────────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("TestMaker")
    app.setStyle("Fusion")
    app.setStyleSheet(DARK_STYLE)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
