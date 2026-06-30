"""PDF & Tools — desktop toolbox (PySide6 / Qt front end).

Native Qt UI over the pure-logic backend in pdf_tools.py. Qt is GPU-composited,
so window resizing is smooth (unlike the old tkinter/CustomTkinter version).
Run: `python app.py`  (or the bundled .exe).
"""
import os
import sys
import io
import json

from PySide6.QtCore import Qt, QObject, QRunnable, QThreadPool, Signal, QRect, QPoint, QSize
from PySide6.QtGui import QPixmap, QImage, QIcon, QPainter, QColor, QPen
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QComboBox, QSlider,
    QFrame, QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea, QStackedWidget,
    QFileDialog, QSizePolicy, QLayout, QListWidget, QListWidgetItem,
    QAbstractItemView,
)

import pdf_tools


def resource_path(rel):
    """Path that works both in dev and inside a PyInstaller bundle."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)


# ----------------------------- settings store ----------------------------
class Settings:
    """User preferences persisted to a JSON file in the home directory."""
    PATH = os.path.join(os.path.expanduser("~"), ".pdf_and_tools.json")
    DEFAULTS = {"theme": "dark", "folder": "", "lang": "en"}

    def __init__(self):
        self.data = dict(self.DEFAULTS)
        try:
            with open(self.PATH, "r", encoding="utf-8") as fp:
                self.data.update(json.load(fp))
        except Exception:
            pass

    def get(self, key):
        return self.data.get(key, self.DEFAULTS.get(key))

    def set(self, key, value):
        self.data[key] = value
        try:
            with open(self.PATH, "w", encoding="utf-8") as fp:
                json.dump(self.data, fp, indent=2)
        except Exception:
            pass

    def initdir(self):
        f = self.get("folder")
        return f if f and os.path.isdir(f) else ""


SETTINGS = Settings()


# ------------------------------ translations -----------------------------
IT = {
    "{n} tools, one tidy toolbox": "{n} strumenti in una cassetta ordinata",
    "Search tools…": "Cerca strumenti…",
    "No tools match your search.": "Nessuno strumento corrisponde.",
    "←  Back": "←  Indietro", "Browse": "Sfoglia", "Clear": "Cancella",
    "Organize": "Organizza", "Optimize & Secure": "Ottimizza e proteggi",
    "Convert": "Converti", "Create": "Crea",
    "Settings": "Impostazioni",
    "Preferences are saved and remembered next time.":
        "Le preferenze vengono salvate e ricordate la prossima volta.",
    "Appearance": "Aspetto", "Light": "Chiaro", "Dark": "Scuro",
    "Language": "Lingua", "Default folder": "Cartella predefinita",
    "Where Browse dialogs start when picking files.":
        "Da dove partono le finestre Sfoglia quando scegli i file.",
    "Merge PDFs": "Unisci PDF", "Split PDF": "Dividi PDF",
    "Remove Duplicates": "Rimuovi duplicati", "Reorder Pages": "Riordina pagine",
    "Delete Pages": "Elimina pagine", "Rotate Pages": "Ruota pagine",
    "Compress PDF": "Comprimi PDF", "Password Protect": "Proteggi con password",
    "Watermark": "Filigrana", "Page Numbers": "Numeri di pagina",
    "Extract Images": "Estrai immagini", "PDF → Images": "PDF → Immagini",
    "Images → PDF": "Immagini → PDF", "Extract Text": "Estrai testo",
    "HTML → PDF": "HTML → PDF", "Resize Image": "Ridimensiona immagine",
    "Convert Image": "Converti immagine", "Watermark Image": "Filigrana immagine",
    "Compress Image": "Comprimi immagine", "Crop Image": "Ritaglia immagine",
    "QR Generator": "Generatore QR", "Color Palette": "Tavolozza colori",
    "Combine PDFs into one": "Unisci più PDF in uno",
    "Break a PDF into parts": "Spezza un PDF in parti",
    "Drop repeated slides": "Elimina diapositive ripetute",
    "Change page order": "Cambia l'ordine delle pagine",
    "Remove chosen pages": "Rimuovi le pagine scelte",
    "Turn pages 90/180/270": "Ruota le pagine 90/180/270",
    "Shrink file size": "Riduci la dimensione del file",
    "Encrypt with AES-256": "Cifra con AES-256",
    "Stamp text on pages": "Timbra testo sulle pagine",
    "Number every page": "Numera ogni pagina",
    "Save images from a PDF": "Salva le immagini da un PDF",
    "Each page to PNG": "Ogni pagina in PNG",
    "Combine images to PDF": "Unisci immagini in PDF",
    "PDF text to .txt": "Testo PDF in .txt",
    "Web page / file to PDF": "Pagina web / file in PDF",
    "Scale image up or down": "Ingrandisci o riduci l'immagine",
    "JPG ↔ PNG ↔ WebP": "JPG ↔ PNG ↔ WebP",
    "Stamp text on an image": "Timbra testo su un'immagine",
    "Shrink image file size": "Riduci la dimensione dell'immagine",
    "Drag-select to crop": "Trascina per ritagliare",
    "Text / URL → QR code": "Testo / URL → codice QR",
    "Dominant colors of image": "Colori dominanti dell'immagine",
    "Remove Duplicate Pages": "Rimuovi pagine duplicate",
    "QR Code Generator": "Generatore di codici QR",
    "Color Palette Extractor": "Estrattore tavolozza colori",
    "Add Page Numbers": "Aggiungi numeri di pagina",
    "Combine several PDFs into one, in the order chosen.":
        "Unisci più PDF in uno, nell'ordine scelto.",
    "Ranges like 1-3,5,8-10 — each group becomes a file.":
        "Intervalli come 1-3,5,8-10 — ogni gruppo diventa un file.",
    "Pull every embedded image out of a PDF as PNG.":
        "Estrai ogni immagine incorporata da un PDF come PNG.",
    "Strips repeated/animation-build slides, keeping the most complete one of each run.":
        "Rimuove le diapositive ripetute/animate, tenendo la più completa di ogni gruppo.",
    "Encode a link or any text into a QR PNG.":
        "Codifica un link o testo in un QR PNG.",
    "Pull the dominant colors out of an image.":
        "Estrai i colori dominanti da un'immagine.",
    "Rotate all pages, or only the ones you list.":
        "Ruota tutte le pagine, o solo quelle indicate.",
    "Re-save with cleanup + deflate to shrink file size.":
        "Risalva con pulizia + deflate per ridurre la dimensione.",
    "Render each page to a PNG.": "Converte ogni pagina in PNG.",
    "Stamp diagonal text across every page.":
        "Timbra testo in diagonale su ogni pagina.",
    "Give the new page order — drop or repeat pages too.":
        "Indica il nuovo ordine — puoi togliere o ripetere pagine.",
    "Remove the pages you list, keep the rest.":
        "Rimuove le pagine indicate, tiene le altre.",
    "Combine images into one PDF, one per page.":
        "Unisci immagini in un PDF, una per pagina.",
    "Lock a PDF with AES-256 encryption.":
        "Blocca un PDF con cifratura AES-256.",
    "Stamp page numbers at the bottom of each page.":
        "Timbra i numeri in fondo a ogni pagina.",
    "Pull all text out of a PDF into a .txt file.":
        "Estrai tutto il testo di un PDF in un file .txt.",
    "Convert an HTML file or a web page (URL) to a PDF.":
        "Converti un file HTML o una pagina web (URL) in PDF.",
    "Scale an image up or down — aspect ratio kept.":
        "Ingrandisci o riduci un'immagine — proporzioni mantenute.",
    "Change an image's format — JPG ↔ PNG ↔ WebP ↔ BMP.":
        "Cambia il formato di un'immagine — JPG ↔ PNG ↔ WebP ↔ BMP.",
    "Stamp diagonal text across an image.":
        "Timbra testo in diagonale su un'immagine.",
    "Shrink an image's file size.": "Riduci la dimensione di un'immagine.",
    "Drag a box over the image to crop it.":
        "Trascina un riquadro sull'immagine per ritagliarla.",
    "PDF file": "File PDF", "PDF files": "File PDF", "Save as": "Salva come",
    "Image": "Immagine", "Images": "Immagini", "Ranges": "Intervalli",
    "Sensitivity": "Sensibilità", "Text / URL": "Testo / URL",
    "Colors": "Colori", "Angle": "Angolo", "Pages": "Pagine",
    "Quality (DPI)": "Qualità (DPI)", "Text": "Testo", "New order": "Nuovo ordine",
    "Password": "Password", "HTML / URL": "HTML / URL", "Resize by": "Ridimensiona per",
    "Amount": "Quantità", "Convert to": "Converti in", "Opacity": "Opacità",
    "Quality": "Qualità",
    "Merge": "Unisci", "Split": "Dividi", "Extract": "Estrai",
    "Clean up": "Pulisci", "Generate": "Genera", "Rotate": "Ruota",
    "Compress": "Comprimi", "Render": "Converti", "Apply": "Applica",
    "Reorder": "Riordina", "Delete": "Elimina", "Build PDF": "Crea PDF",
    "Encrypt": "Cifra", "Number": "Numera", "Resize": "Ridimensiona",
    "Crop & Save": "Ritaglia e salva",
    "Save as image": "Salva come immagine",
    "Save codes (.txt)": "Salva codici (.txt)",
    "Preview (merge order →)": "Anteprima (ordine di unione →)",
    "Working…": "Lavoro in corso…",
    "Add files": "Aggiungi file", "Remove": "Rimuovi",
    "+ Add interval": "+ Aggiungi intervallo",
    "Drag to reorder · drop files here, or use the buttons":
        "Trascina per riordinare · rilascia i file qui, o usa i pulsanti",
    "One interval per box — add as many as you need.":
        "Un intervallo per casella — aggiungine quante ne servono.",
}


def tr(s):
    """Translate a UI string to the current language (no-op for English)."""
    if SETTINGS.get("lang") == "it":
        return IT.get(s, s)
    return s


# --------------------------- theme (QSS) ---------------------------------
PALETTES = {
    "dark": dict(BG="#0d0e12", SURFACE="#171922", SURFACE2="#20232e",
                 BORDER="#262a36", TEXT="#eceef5", MUTED="#888ea0"),
    "light": dict(BG="#eef0f6", SURFACE="#ffffff", SURFACE2="#f1f2f8",
                  BORDER="#e2e4ee", TEXT="#16181f", MUTED="#737888"),
}
ACCENT = "#7c5cff"
ACCENT_H = "#6a48ec"
OK_C = "#3fb950"
ERR_C = "#f85149"


def build_qss(mode):
    p = PALETTES["light" if mode == "light" else "dark"]
    return f"""
    QWidget {{ background: {p['BG']}; color: {p['TEXT']};
        font-family: 'Segoe UI'; font-size: 13px; }}
    QLabel {{ background: transparent; }}
    QLabel#h1 {{ font-size: 26px; font-weight: 700; }}
    QLabel#brand {{ font-size: 28px; font-weight: 700; }}
    QLabel#muted {{ color: {p['MUTED']}; }}
    QLabel#cardname {{ font-size: 14px; font-weight: 600; }}
    QLabel#carddesc {{ color: {p['MUTED']}; font-size: 11px; }}
    QLabel#cardicon {{ font-size: 26px; }}
    QLineEdit, QComboBox {{ background: {p['SURFACE2']}; border: 1px solid {p['BORDER']};
        border-radius: 8px; padding: 8px 10px; color: {p['TEXT']}; selection-background-color: {ACCENT}; }}
    QLineEdit:focus, QComboBox:focus {{ border: 1px solid {ACCENT}; }}
    QComboBox::drop-down {{ border: none; width: 22px; }}
    QComboBox QAbstractItemView {{ background: {p['SURFACE']}; border: 1px solid {p['BORDER']};
        selection-background-color: {ACCENT}; outline: none; }}
    QPushButton#primary {{ background: {ACCENT}; color: white; border: none;
        border-radius: 9px; padding: 11px 24px; font-weight: 600; font-size: 14px; }}
    QPushButton#primary:hover {{ background: {ACCENT_H}; }}
    QPushButton#primary:disabled {{ background: {p['BORDER']}; color: {p['MUTED']}; }}
    QPushButton#ghost {{ background: transparent; border: 1px solid {p['BORDER']};
        border-radius: 8px; padding: 7px 14px; color: {p['TEXT']}; }}
    QPushButton#ghost:hover {{ border: 1px solid {ACCENT}; color: {ACCENT}; }}
    QPushButton#gear {{ background: {p['SURFACE2']}; border: 1px solid {p['BORDER']};
        border-radius: 21px; font-size: 19px; }}
    QPushButton#gear:hover {{ background: {ACCENT}; }}
    QFrame#card {{ background: {p['SURFACE']}; border: 1px solid {p['BORDER']};
        border-radius: 14px; }}
    QFrame#card:hover {{ border: 1px solid {ACCENT}; background: {p['SURFACE2']}; }}
    QFrame#panel {{ background: {p['SURFACE']}; border: 1px solid {p['BORDER']};
        border-radius: 16px; }}
    QFrame#chip {{ background: {p['SURFACE2']}; border: 1px solid {p['BORDER']};
        border-radius: 10px; }}
    QScrollArea {{ border: none; background: transparent; }}
    QScrollBar:vertical {{ background: transparent; width: 12px; margin: 2px; }}
    QScrollBar::handle:vertical {{ background: {p['BORDER']}; border-radius: 5px; min-height: 36px; }}
    QScrollBar::handle:vertical:hover {{ background: {ACCENT}; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
    QScrollBar:horizontal {{ background: transparent; height: 12px; margin: 2px; }}
    QScrollBar::handle:horizontal {{ background: {p['BORDER']}; border-radius: 5px; min-width: 36px; }}
    QSlider::groove:horizontal {{ height: 5px; background: {p['BORDER']}; border-radius: 2px; }}
    QSlider::sub-page:horizontal {{ background: {ACCENT}; border-radius: 2px; }}
    QSlider::handle:horizontal {{ background: {ACCENT}; width: 16px; height: 16px;
        margin: -6px 0; border-radius: 8px; }}
    """


def pil_to_pixmap(img):
    """PIL.Image -> QPixmap via PNG bytes (avoids ImageQt binding issues)."""
    buf = io.BytesIO()
    img.save(buf, "PNG")
    pm = QPixmap()
    pm.loadFromData(buf.getvalue())
    return pm


# ---------------------- drag-and-drop input widgets ----------------------
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tif", ".tiff", ".webp")
DROP_EXTS = {"pdf": (".pdf",), "image": IMAGE_EXTS, "html": (".html", ".htm")}


def _urls_to_paths(mime, exts):
    out = []
    for url in mime.urls():
        p = url.toLocalFile()
        if p and (not exts or p.lower().endswith(exts)):
            out.append(p)
    return out


class DropLineEdit(QLineEdit):
    """Single-file line edit that also accepts an OS file drop."""

    def __init__(self, exts=None):
        super().__init__()
        self._exts = exts
        self.setAcceptDrops(True)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
        else:
            super().dragEnterEvent(e)

    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
        else:
            super().dragMoveEvent(e)

    def dropEvent(self, e):
        paths = _urls_to_paths(e.mimeData(), self._exts)
        if paths:
            self.setText(paths[0])
            e.acceptProposedAction()
        else:
            super().dropEvent(e)


class FileListWidget(QListWidget):
    """Reorderable file list: OS file drop + internal drag-to-reorder."""

    def __init__(self, exts=None):
        super().__init__()
        self._exts = exts
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setMinimumHeight(132)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
        else:
            super().dragEnterEvent(e)

    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
        else:
            super().dragMoveEvent(e)

    def dropEvent(self, e):
        if e.mimeData().hasUrls():
            for p in _urls_to_paths(e.mimeData(), self._exts):
                self.add_path(p)
            e.acceptProposedAction()
        else:
            super().dropEvent(e)   # internal reorder

    def add_path(self, p):
        it = QListWidgetItem(os.path.basename(p))
        it.setData(Qt.UserRole, p)
        it.setToolTip(p)
        self.addItem(it)

    def paths(self):
        return [self.item(i).data(Qt.UserRole) for i in range(self.count())]


class RangesField(QWidget):
    """Stack of interval boxes — one box plus an 'add interval' button.

    spec() joins the non-empty boxes with commas, so the result feeds the
    same backend parsers (parse_ranges / parse_page_list) as a single box.
    """

    def __init__(self, placeholder="", on_change=None):
        super().__init__()
        self._placeholder = placeholder
        self._on_change = on_change
        self._rows = []                      # (holder_widget, line_edit)

        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(6)
        self._rows_box = QVBoxLayout()
        self._rows_box.setSpacing(6)
        v.addLayout(self._rows_box)

        add = QPushButton(tr("+ Add interval"))
        add.setObjectName("ghost")
        add.setCursor(Qt.PointingHandCursor)
        add.clicked.connect(lambda: self.add_row())
        bar = QHBoxLayout()
        bar.addWidget(add)
        bar.addStretch(1)
        v.addLayout(bar)

        self.add_row()

    def add_row(self, text=""):
        edit = QLineEdit()
        edit.setPlaceholderText(self._placeholder)
        edit.setText(text)
        rm = QPushButton("✕")
        rm.setObjectName("ghost")
        rm.setFixedWidth(38)
        rm.setCursor(Qt.PointingHandCursor)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(edit, 1)
        row.addWidget(rm)
        holder = QWidget()
        holder.setLayout(row)
        self._rows_box.addWidget(holder)

        entry = (holder, edit)
        self._rows.append(entry)
        rm.clicked.connect(lambda: self._remove(entry))
        if self._on_change:
            edit.textChanged.connect(lambda *_: self._on_change())

    def _remove(self, entry):
        if len(self._rows) == 1:             # always keep one box
            entry[1].clear()
            return
        holder, _ = entry
        self._rows.remove(entry)
        holder.setParent(None)
        holder.deleteLater()
        if self._on_change:
            self._on_change()

    def spec(self):
        parts = [e.text().strip() for _, e in self._rows]
        return ",".join(p for p in parts if p)


# ----------------------------- async worker ------------------------------
class WorkerSignals(QObject):
    done = Signal(object, object)   # (result, error)


class Worker(QRunnable):
    def __init__(self, fn):
        super().__init__()
        self.fn = fn
        self.signals = WorkerSignals()

    def run(self):
        try:
            res, err = self.fn(), None
        except Exception as e:           # surface backend errors to the UI
            res, err = None, e
        self.signals.done.emit(res, err)


# ------------------------------ flow layout ------------------------------
class FlowLayout(QLayout):
    """Left-to-right wrapping layout (Qt example). Cards reflow to fit width."""

    def __init__(self, margin=0, spacing=12):
        super().__init__()
        self._items = []
        self.setContentsMargins(margin, margin, margin, margin)
        self._spacing = spacing

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, i):
        return self._items[i] if 0 <= i < len(self._items) else None

    def takeAt(self, i):
        return self._items.pop(i) if 0 <= i < len(self._items) else None

    def expandingDirections(self):
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), test=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, test=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for it in self._items:
            size = size.expandedTo(it.minimumSize())
        m = self.contentsMargins()
        size += QSize(m.left() + m.right(), m.top() + m.bottom())
        return size

    def _do_layout(self, rect, test):
        x, y = rect.x(), rect.y()
        line_h = 0
        for it in self._items:
            w = it.sizeHint().width()
            h = it.sizeHint().height()
            nx = x + w + self._spacing
            if nx - self._spacing > rect.right() and line_h > 0:
                x = rect.x()
                y = y + line_h + self._spacing
                nx = x + w + self._spacing
                line_h = 0
            if not test:
                it.setGeometry(QRect(QPoint(x, y), it.sizeHint()))
            x = nx
            line_h = max(line_h, h)
        return y + line_h - rect.y()


# -------------------------------- tool list ------------------------------
def _tools():
    return [
        ("⊞", "Merge PDFs", "Combine PDFs into one", MergeTool, "Organize"),
        ("◫", "Split PDF", "Break a PDF into parts", SplitTool, "Organize"),
        ("⊠", "Remove Duplicates", "Drop repeated slides", DedupeTool, "Organize"),
        ("⇅", "Reorder Pages", "Change page order", ReorderTool, "Organize"),
        ("⊘", "Delete Pages", "Remove chosen pages", DeletePagesTool, "Organize"),
        ("↻", "Rotate Pages", "Turn pages 90/180/270", RotateTool, "Organize"),
        ("⇲", "Compress PDF", "Shrink file size", CompressTool, "Optimize & Secure"),
        ("⚿", "Password Protect", "Encrypt with AES-256", EncryptTool, "Optimize & Secure"),
        ("❖", "Watermark", "Stamp text on pages", WatermarkTool, "Optimize & Secure"),
        ("#", "Page Numbers", "Number every page", PageNumbersTool, "Optimize & Secure"),
        ("▣", "Watermark Image", "Stamp text on an image", ImageWatermarkTool, "Optimize & Secure"),
        ("⤓", "Compress Image", "Shrink image file size", CompressImageTool, "Optimize & Secure"),
        ("❏", "Extract Images", "Save images from a PDF", ExtractImagesTool, "Convert"),
        ("▦", "PDF → Images", "Each page to PNG", PdfToImagesTool, "Convert"),
        ("▤", "Images → PDF", "Combine images to PDF", ImagesToPdfTool, "Convert"),
        ("≣", "Extract Text", "PDF text to .txt", ExtractTextTool, "Convert"),
        ("⌗", "HTML → PDF", "Web page / file to PDF", HtmlToPdfTool, "Convert"),
        ("⤡", "Resize Image", "Scale image up or down", ResizeImageTool, "Convert"),
        ("⇄", "Convert Image", "JPG ↔ PNG ↔ WebP", ConvertImageTool, "Convert"),
        ("✁", "Crop Image", "Drag-select to crop", CropImageTool, "Convert"),
        ("▩", "QR Generator", "Text / URL → QR code", QRTool, "Create"),
        ("◐", "Color Palette", "Dominant colors of image", PaletteTool, "Create"),
    ]


CATEGORIES = ["Organize", "Optimize & Secure", "Convert", "Create"]
IMG_FILTER = "Images (*.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff *.webp)"


# =============================== base panel ==============================
class ToolPanel(QWidget):
    """Base tool screen: back, title, subtitle, form body, status line."""

    def __init__(self, window, title, subtitle=""):
        super().__init__()
        self.window = window
        self._pool = QThreadPool.globalInstance()

        root = QVBoxLayout(self)
        root.setContentsMargins(34, 22, 34, 22)
        root.setSpacing(4)

        back = QPushButton(tr("←  Back"))
        back.setObjectName("ghost")
        back.setCursor(Qt.PointingHandCursor)
        back.setFixedWidth(110)
        back.clicked.connect(self.window.show_home)
        root.addWidget(back, 0, Qt.AlignLeft)

        h1 = QLabel(tr(title))
        h1.setObjectName("h1")
        root.addSpacing(8)
        root.addWidget(h1)
        if subtitle:
            sub = QLabel(tr(subtitle))
            sub.setObjectName("muted")
            root.addWidget(sub)

        panel = QFrame()
        panel.setObjectName("panel")
        self.body = QVBoxLayout(panel)
        self.body.setContentsMargins(24, 22, 24, 22)
        self.body.setSpacing(10)
        root.addSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(panel)
        root.addWidget(scroll, 1)

        self.status = QLabel("")
        self.status.setStyleSheet("font-weight: 600;")
        root.addWidget(self.status)

        self.build()
        self.body.addStretch(1)

    # ---- form-field helpers -------------------------------------------
    def _label(self, text):
        lab = QLabel(tr(text))
        lab.setObjectName("muted")
        lab.setFixedWidth(120)
        return lab

    def _row(self, text, *widgets):
        row = QHBoxLayout()
        row.addWidget(self._label(text))
        for w in widgets:
            row.addWidget(w)
        self.body.addLayout(row)
        return row

    def file_field(self, label, kind):
        exts = DROP_EXTS.get(kind)
        edit = DropLineEdit(exts) if exts else QLineEdit()
        btn = QPushButton(tr("Browse"))
        btn.setObjectName("ghost")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda: self._browse(edit, kind))
        row = QHBoxLayout()
        row.addWidget(self._label(label))
        row.addWidget(edit, 1)
        row.addWidget(btn)
        self.body.addLayout(row)
        return edit

    def file_list_field(self, label, kind):
        """Reorderable multi-file picker: drop files, drag to reorder, buttons."""
        exts = IMAGE_EXTS if kind == "images" else (".pdf",)
        lst = FileListWidget(exts)

        browse = QPushButton(tr("Add files"))
        remove = QPushButton(tr("Remove"))
        clear = QPushButton(tr("Clear"))
        for b in (browse, remove, clear):
            b.setObjectName("ghost")
            b.setCursor(Qt.PointingHandCursor)
        browse.clicked.connect(lambda: self._browse_into(lst, kind))
        remove.clicked.connect(
            lambda: [lst.takeItem(lst.row(it)) for it in lst.selectedItems()])
        clear.clicked.connect(lst.clear)

        head = QHBoxLayout()
        head.addWidget(self._label(label))
        head.addStretch(1)
        head.addWidget(browse)
        head.addWidget(remove)
        head.addWidget(clear)
        self.body.addLayout(head)
        self.body.addWidget(lst)
        self.hint("Drag to reorder · drop files here, or use the buttons")
        return lst

    def _browse_into(self, lst, kind):
        d = SETTINGS.initdir()
        flt = IMG_FILTER if kind == "images" else "PDF (*.pdf)"
        ps, _ = QFileDialog.getOpenFileNames(self, "", d, flt)
        for p in ps:
            lst.add_path(p)

    def ranges_field(self, label, placeholder="", on_change=None):
        f = RangesField(placeholder, on_change)
        lab = self._label(label)
        lab.setAlignment(Qt.AlignTop)
        row = QHBoxLayout()
        row.addWidget(lab)
        row.addWidget(f, 1)
        self.body.addLayout(row)
        self.hint("One interval per box — add as many as you need.")
        return f

    def _browse(self, edit, kind):
        d = SETTINGS.initdir()
        if kind == "pdf":
            p, _ = QFileDialog.getOpenFileName(self, "", d, "PDF (*.pdf)")
        elif kind == "pdfs":
            ps, _ = QFileDialog.getOpenFileNames(self, "", d, "PDF (*.pdf)")
            p = "  |  ".join(ps)
        elif kind == "image":
            p, _ = QFileDialog.getOpenFileName(self, "", d, IMG_FILTER)
        elif kind == "images":
            ps, _ = QFileDialog.getOpenFileNames(self, "", d, IMG_FILTER)
            p = "  |  ".join(ps)
        elif kind == "html":
            p, _ = QFileDialog.getOpenFileName(self, "", d, "HTML (*.html *.htm)")
        elif kind == "save_pdf":
            p, _ = QFileDialog.getSaveFileName(self, "", d, "PDF (*.pdf)")
        elif kind == "save_txt":
            p, _ = QFileDialog.getSaveFileName(self, "", d, "Text (*.txt)")
        elif kind == "save_img":
            p, _ = QFileDialog.getSaveFileName(
                self, "", d, "PNG (*.png);;JPEG (*.jpg);;WebP (*.webp);;BMP (*.bmp)")
        else:
            p = ""
        if p:
            edit.setText(p)

    def text_field(self, label, placeholder=""):
        edit = QLineEdit()
        if placeholder:
            edit.setPlaceholderText(placeholder)
        self._row(label, edit)
        return edit

    def password_field(self, label):
        edit = QLineEdit()
        edit.setEchoMode(QLineEdit.Password)
        self._row(label, edit)
        return edit

    def slider_field(self, label, lo, hi, default):
        s = QSlider(Qt.Horizontal)
        s.setRange(lo, hi)
        s.setValue(default)
        val = QLabel(str(default))
        val.setObjectName("muted")
        val.setFixedWidth(40)
        s.valueChanged.connect(lambda v: val.setText(str(v)))
        self._row(label, s, val)
        return s

    def combo_field(self, label, options):
        c = QComboBox()
        c.addItems(options)
        c.setCursor(Qt.PointingHandCursor)
        self._row(label, c)
        return c

    def hint(self, text):
        lab = QLabel(text)
        lab.setStyleSheet("color: gray; font-size: 11px;")
        lab.setContentsMargins(120, 0, 0, 0)
        self.body.addWidget(lab)

    def primary_button(self, text):
        btn = QPushButton(tr(text))
        btn.setObjectName("primary")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(self.go)
        wrap = QHBoxLayout()
        wrap.addStretch(1)
        wrap.addWidget(btn)
        wrap.addStretch(1)
        self.body.addSpacing(6)
        self.body.addLayout(wrap)
        return btn

    # ---- status + async ------------------------------------------------
    def set_status(self, text, ok=True):
        self.status.setText(text)
        self.status.setStyleSheet(f"font-weight: 600; color: {OK_C if ok else ERR_C};")

    def run_async(self, fn, ok_msg):
        self.set_status(tr("Working…"), ok=True)
        self._submit(fn, lambda res, err: self._handle(res, err, ok_msg))

    def _handle(self, res, err, ok_msg):
        if err:
            self.set_status(str(err), ok=False)
        else:
            self.set_status(ok_msg(res) if callable(ok_msg) else ok_msg, ok=True)

    def _submit(self, fn, on_done):
        """Run fn off-thread; deliver (result, error) to on_done on the UI thread.

        Keeps the worker referenced and disables auto-delete so the queued
        signal isn't lost when the QRunnable finishes.
        """
        if not hasattr(self, "_jobs"):
            self._jobs = []
        w = Worker(fn)
        w.setAutoDelete(False)
        self._jobs.append(w)

        def wrapped(res, err):
            on_done(res, err)
            try:
                self._jobs.remove(w)
            except ValueError:
                pass
        w.signals.done.connect(wrapped)
        self._pool.start(w)

    # subclasses override
    def build(self):
        pass

    def go(self):
        pass


# =============================== PDF tools ================================
class MergeTool(ToolPanel):
    def __init__(self, window):
        super().__init__(window, "Merge PDFs",
                         "Combine several PDFs into one, in the order chosen.")

    def build(self):
        self.files = self.file_list_field("PDF files", "pdfs")
        self.out = self.file_field("Save as", "save_pdf")
        self.primary_button("Merge")

    def go(self):
        files, out = self.files.paths(), self.out.text()
        if not files or not out:
            return self.set_status("Pick files and an output path.", ok=False)
        self.run_async(lambda: pdf_tools.merge_pdfs(files, out),
                       lambda r: f"Saved {os.path.basename(r)}")


class SplitTool(ToolPanel):
    def __init__(self, window):
        super().__init__(window, "Split PDF",
                         "Ranges like 1-3,5,8-10 — each group becomes a file.")

    def build(self):
        self.file = self.file_field("PDF file", "pdf")
        self.file.textChanged.connect(self._preview)
        self.info = QLabel("")
        self.info.setObjectName("muted")
        self.body.addWidget(self.info)
        self.ranges = self.ranges_field("Ranges", "1-3", self._summary)
        self.sumlab = QLabel("")
        self.sumlab.setContentsMargins(120, 0, 0, 0)
        self.body.addWidget(self.sumlab)
        self._count = 0
        self.primary_button("Split")

    def _preview(self):
        f = self.file.text()
        self._count = 0
        self.info.setText("")
        if not f:
            return

        def done(r, e):
            if not e:
                self._count = r
                self.info.setText(f"{r} pages")
                self._summary()
        self._submit(lambda: pdf_tools.pdf_page_count(f), done)

    def _summary(self):
        spec = self.ranges.spec().strip()
        if not spec or not self._count:
            self.sumlab.setText("")
            return
        try:
            groups = pdf_tools.parse_ranges(spec, self._count)
            total = sum(len(g) for g in groups)
            self.sumlab.setText(f"→ {len(groups)} file(s), {total} page(s)")
            self.sumlab.setStyleSheet(f"color: {OK_C};")
        except Exception as e:
            self.sumlab.setText(f"✗ {e}")
            self.sumlab.setStyleSheet(f"color: {ERR_C};")

    def go(self):
        f, spec = self.file.text(), self.ranges.spec()
        if not f or not spec:
            return self.set_status("Pick a file and enter ranges.", ok=False)
        out_dir = QFileDialog.getExistingDirectory(self, "Save parts to…",
                                                   SETTINGS.initdir())
        if not out_dir:
            return
        self.run_async(lambda: pdf_tools.split_pdf(f, spec, out_dir),
                       lambda r: f"Wrote {len(r)} file(s).")


class ExtractImagesTool(ToolPanel):
    def __init__(self, window):
        super().__init__(window, "Extract Images",
                         "Pull every embedded image out of a PDF as PNG.")

    def build(self):
        self.file = self.file_field("PDF file", "pdf")
        self.primary_button("Extract")

    def go(self):
        f = self.file.text()
        if not f:
            return self.set_status("Pick a PDF.", ok=False)
        out_dir = QFileDialog.getExistingDirectory(self, "Save images to…",
                                                   SETTINGS.initdir())
        if not out_dir:
            return
        self.run_async(lambda: pdf_tools.extract_images(f, out_dir),
                       lambda r: f"Saved {r} image(s).")


class DedupeTool(ToolPanel):
    def __init__(self, window):
        super().__init__(window, "Remove Duplicate Pages",
                         "Strips repeated/animation-build slides, keeping the "
                         "most complete one of each run.")

    def build(self):
        self.file = self.file_field("PDF file", "pdf")
        self.out = self.file_field("Save as", "save_pdf")
        self.sens = self.slider_field("Sensitivity", 0, 12, 4)
        self.hint("Low = only exact dupes · High = more aggressive")
        self.primary_button("Clean up")

    def go(self):
        f, out = self.file.text(), self.out.text()
        if not f or not out:
            return self.set_status("Pick a file and an output path.", ok=False)
        thr = self.sens.value()
        self.run_async(lambda: pdf_tools.remove_duplicate_pages(f, out, thr),
                       lambda r: f"Kept {r[0]} pages, removed {r[1]}.")


class RotateTool(ToolPanel):
    def __init__(self, window):
        super().__init__(window, "Rotate Pages",
                         "Rotate all pages, or only the ones you list.")

    def build(self):
        self.file = self.file_field("PDF file", "pdf")
        self.out = self.file_field("Save as", "save_pdf")
        self.angle = self.combo_field("Angle", ["90", "180", "270"])
        self.pages = self.ranges_field("Pages", "blank = all, or 1,3,5-8")
        self.primary_button("Rotate")

    def go(self):
        f, out = self.file.text(), self.out.text()
        if not f or not out:
            return self.set_status("Pick a file and an output path.", ok=False)
        ang = int(self.angle.currentText())
        self.run_async(lambda: pdf_tools.rotate_pdf(f, out, ang, self.pages.spec()),
                       lambda r: f"Rotated → {os.path.basename(r)}")


class CompressTool(ToolPanel):
    def __init__(self, window):
        super().__init__(window, "Compress PDF",
                         "Re-save with cleanup + deflate to shrink file size.")

    def build(self):
        self.file = self.file_field("PDF file", "pdf")
        self.out = self.file_field("Save as", "save_pdf")
        self.primary_button("Compress")

    def go(self):
        f, out = self.file.text(), self.out.text()
        if not f or not out:
            return self.set_status("Pick a file and an output path.", ok=False)

        def msg(r):
            b, a = r
            pct = (1 - a / b) * 100 if b else 0
            return f"{b/1e6:.1f} MB → {a/1e6:.1f} MB ({pct:.0f}% smaller)"
        self.run_async(lambda: pdf_tools.compress_pdf(f, out), msg)


class PdfToImagesTool(ToolPanel):
    def __init__(self, window):
        super().__init__(window, "PDF → Images", "Render each page to a PNG.")

    def build(self):
        self.file = self.file_field("PDF file", "pdf")
        self.dpi = self.slider_field("Quality (DPI)", 72, 300, 150)
        self.primary_button("Render")

    def go(self):
        f = self.file.text()
        if not f:
            return self.set_status("Pick a PDF.", ok=False)
        out_dir = QFileDialog.getExistingDirectory(self, "Save images to…",
                                                   SETTINGS.initdir())
        if not out_dir:
            return
        dpi = self.dpi.value()
        self.run_async(lambda: pdf_tools.pdf_to_images(f, out_dir, dpi),
                       lambda r: f"Rendered {r} page(s).")


class WatermarkTool(ToolPanel):
    def __init__(self, window):
        super().__init__(window, "Watermark",
                         "Stamp diagonal text across every page.")

    def build(self):
        self.file = self.file_field("PDF file", "pdf")
        self.text = self.text_field("Text", "CONFIDENTIAL")
        self.out = self.file_field("Save as", "save_pdf")
        self.primary_button("Apply")

    def go(self):
        f, out, txt = self.file.text(), self.out.text(), self.text.text()
        if not f or not out or not txt:
            return self.set_status("Pick file, text, and output.", ok=False)
        self.run_async(lambda: pdf_tools.watermark_pdf(f, out, txt),
                       lambda r: f"Stamped → {os.path.basename(r)}")


class ReorderTool(ToolPanel):
    def __init__(self, window):
        super().__init__(window, "Reorder Pages",
                         "Give the new page order — drop or repeat pages too.")

    def build(self):
        self.file = self.file_field("PDF file", "pdf")
        self.spec = self.ranges_field("New order", "3 or 1-4")
        self.out = self.file_field("Save as", "save_pdf")
        self.primary_button("Reorder")

    def go(self):
        f, out, spec = self.file.text(), self.out.text(), self.spec.spec()
        if not f or not out or not spec:
            return self.set_status("Pick file, order, and output.", ok=False)
        self.run_async(lambda: pdf_tools.reorder_pdf(f, out, spec),
                       lambda r: f"Reordered → {os.path.basename(r)}")


class DeletePagesTool(ToolPanel):
    def __init__(self, window):
        super().__init__(window, "Delete Pages",
                         "Remove the pages you list, keep the rest.")

    def build(self):
        self.file = self.file_field("PDF file", "pdf")
        self.spec = self.ranges_field("Pages", "2 or 9-11")
        self.out = self.file_field("Save as", "save_pdf")
        self.primary_button("Delete")

    def go(self):
        f, out, spec = self.file.text(), self.out.text(), self.spec.spec()
        if not f or not out or not spec:
            return self.set_status("Pick file, pages, and output.", ok=False)
        self.run_async(lambda: pdf_tools.delete_pages(f, out, spec),
                       lambda r: f"Kept {r[0]}, removed {r[1]} page(s).")


class ImagesToPdfTool(ToolPanel):
    def __init__(self, window):
        super().__init__(window, "Images → PDF",
                         "Combine images into one PDF, one per page.")

    def build(self):
        self.imgs = self.file_list_field("Images", "images")
        self.out = self.file_field("Save as", "save_pdf")
        self.primary_button("Build PDF")

    def go(self):
        files, out = self.imgs.paths(), self.out.text()
        if not files or not out:
            return self.set_status("Pick images and an output path.", ok=False)
        self.run_async(lambda: pdf_tools.images_to_pdf(files, out),
                       lambda r: f"Built {os.path.basename(r)}")


class EncryptTool(ToolPanel):
    def __init__(self, window):
        super().__init__(window, "Password Protect",
                         "Lock a PDF with AES-256 encryption.")

    def build(self):
        self.file = self.file_field("PDF file", "pdf")
        self.pw = self.password_field("Password")
        self.out = self.file_field("Save as", "save_pdf")
        self.primary_button("Encrypt")

    def go(self):
        f, out, pw = self.file.text(), self.out.text(), self.pw.text()
        if not f or not out or not pw:
            return self.set_status("Pick file, password, and output.", ok=False)
        self.run_async(lambda: pdf_tools.encrypt_pdf(f, out, pw),
                       lambda r: f"Locked → {os.path.basename(r)}")


class PageNumbersTool(ToolPanel):
    def __init__(self, window):
        super().__init__(window, "Add Page Numbers",
                         "Stamp page numbers at the bottom of each page.")

    def build(self):
        self.file = self.file_field("PDF file", "pdf")
        self.out = self.file_field("Save as", "save_pdf")
        self.primary_button("Number")

    def go(self):
        f, out = self.file.text(), self.out.text()
        if not f or not out:
            return self.set_status("Pick a file and an output path.", ok=False)
        self.run_async(lambda: pdf_tools.add_page_numbers(f, out),
                       lambda r: f"Numbered → {os.path.basename(r)}")


class ExtractTextTool(ToolPanel):
    def __init__(self, window):
        super().__init__(window, "Extract Text",
                         "Pull all text out of a PDF into a .txt file.")

    def build(self):
        self.file = self.file_field("PDF file", "pdf")
        self.out = self.file_field("Save as", "save_txt")
        self.primary_button("Extract")

    def go(self):
        f, out = self.file.text(), self.out.text()
        if not f or not out:
            return self.set_status("Pick a file and an output path.", ok=False)
        self.run_async(lambda: pdf_tools.extract_text(f, out),
                       lambda r: f"Wrote {r} characters.")


class HtmlToPdfTool(ToolPanel):
    def __init__(self, window):
        super().__init__(window, "HTML → PDF",
                         "Convert an HTML file or a web page (URL) to a PDF.")

    def build(self):
        self.src = self.file_field("HTML / URL", "html")
        self.hint("Pick an .html file, or paste a http(s):// link.")
        self.out = self.file_field("Save as", "save_pdf")
        self.primary_button("Convert")

    def go(self):
        src, out = self.src.text().strip(), self.out.text()
        if not src or not out:
            return self.set_status("Pick an HTML file / URL and an output path.", ok=False)
        self.run_async(lambda: pdf_tools.html_to_pdf(src, out),
                       lambda r: f"Wrote {r} page(s).")


# ============================== image tools ==============================
class ResizeImageTool(ToolPanel):
    MODES = {"Percent %": "percent", "Width px": "width",
             "Height px": "height", "Longest side px": "longest"}

    def __init__(self, window):
        super().__init__(window, "Resize Image",
                         "Scale an image up or down — aspect ratio kept.")

    def build(self):
        self.img = self.file_field("Image", "image")
        self.mode = self.combo_field("Resize by", list(self.MODES.keys()))
        self.amount = self.text_field("Amount", "e.g. 50")
        self.amount.setText("50")
        self.out = self.file_field("Save as", "save_img")
        self.primary_button("Resize")

    def go(self):
        img, out = self.img.text(), self.out.text()
        if not img or not out:
            return self.set_status("Pick an image and an output path.", ok=False)
        try:
            value = float(self.amount.text())
        except ValueError:
            return self.set_status("Amount must be a number.", ok=False)
        mode = self.MODES[self.mode.currentText()]
        self.run_async(lambda: pdf_tools.resize_image(img, out, mode, value),
                       lambda r: f"{r[0][0]}×{r[0][1]} → {r[1][0]}×{r[1][1]}")


class ConvertImageTool(ToolPanel):
    EXT = {"PNG": ".png", "JPEG": ".jpg", "WebP": ".webp", "BMP": ".bmp"}

    def __init__(self, window):
        super().__init__(window, "Convert Image",
                         "Change an image's format — JPG ↔ PNG ↔ WebP ↔ BMP.")

    def build(self):
        self.img = self.file_field("Image", "image")
        self.fmt = self.combo_field("Convert to", list(self.EXT.keys()))
        self.out = self.file_field("Save as", "save_img")
        self.hint("Leave 'Save as' blank to write next to the source.")
        self.primary_button("Convert")

    def go(self):
        img = self.img.text()
        if not img:
            return self.set_status("Pick an image.", ok=False)
        out = self.out.text().strip()
        if not out:
            out = os.path.splitext(img)[0] + self.EXT[self.fmt.currentText()]
        self.run_async(lambda: pdf_tools.convert_image(img, out),
                       lambda r: f"Saved {os.path.basename(r)}")


class ImageWatermarkTool(ToolPanel):
    def __init__(self, window):
        super().__init__(window, "Watermark Image",
                         "Stamp diagonal text across an image.")

    def build(self):
        self.img = self.file_field("Image", "image")
        self.text = self.text_field("Text", "CONFIDENTIAL")
        self.opacity = self.slider_field("Opacity", 10, 90, 30)
        self.out = self.file_field("Save as", "save_img")
        self.primary_button("Apply")

    def go(self):
        img, out, txt = self.img.text(), self.out.text(), self.text.text()
        if not img or not out or not txt:
            return self.set_status("Pick image, text, and output.", ok=False)
        op = self.opacity.value() / 100.0
        self.run_async(lambda: pdf_tools.watermark_image(img, out, txt, op),
                       lambda r: f"Saved {os.path.basename(r)}")


class CompressImageTool(ToolPanel):
    def __init__(self, window):
        super().__init__(window, "Compress Image", "Shrink an image's file size.")

    def build(self):
        self.img = self.file_field("Image", "image")
        self.quality = self.slider_field("Quality", 10, 95, 70)
        self.out = self.file_field("Save as", "save_img")
        self.hint("JPEG / WebP use Quality (lossy). PNG is lossless.")
        self.primary_button("Compress")

    def go(self):
        img, out = self.img.text(), self.out.text()
        if not img or not out:
            return self.set_status("Pick an image and an output path.", ok=False)
        q = self.quality.value()

        def msg(r):
            b, a = r
            pct = (1 - a / b) * 100 if b else 0
            return f"{b/1024:.0f} KB → {a/1024:.0f} KB ({pct:.0f}% smaller)"
        self.run_async(lambda: pdf_tools.compress_image(img, out, q), msg)


# ------------------------------ QR + palette -----------------------------
class QRTool(ToolPanel):
    def __init__(self, window):
        super().__init__(window, "QR Code Generator",
                         "Encode a link or any text into a QR PNG.")

    def build(self):
        self.data = self.text_field("Text / URL")
        self.out = self.file_field("Save as", "save_img")
        self.primary_button("Generate")
        self.preview = QLabel("")
        self.preview.setAlignment(Qt.AlignCenter)
        self.body.addWidget(self.preview)

    def go(self):
        data, out = self.data.text(), self.out.text()
        if not data or not out:
            return self.set_status("Enter text and an output path.", ok=False)

        def msg(r):
            pm = QPixmap(r).scaled(180, 180, Qt.KeepAspectRatio,
                                   Qt.SmoothTransformation)
            self.preview.setPixmap(pm)
            return f"Saved {os.path.basename(r)}"
        self.run_async(lambda: pdf_tools.generate_qr(data, out), msg)


class PaletteTool(ToolPanel):
    def __init__(self, window):
        super().__init__(window, "Color Palette Extractor",
                         "Pull the dominant colors out of an image.")

    def build(self):
        self.img = self.file_field("Image", "image")
        self.n = self.slider_field("Colors", 2, 12, 6)
        self.primary_button("Extract")
        srow = QHBoxLayout()
        self.save_img = QPushButton(tr("Save as image"))
        self.save_txt = QPushButton(tr("Save codes (.txt)"))
        for b in (self.save_img, self.save_txt):
            b.setObjectName("ghost")
            b.setCursor(Qt.PointingHandCursor)
            b.setEnabled(False)
        self.save_img.clicked.connect(self._save_image)
        self.save_txt.clicked.connect(self._save_text)
        srow.addStretch(1)
        srow.addWidget(self.save_img)
        srow.addWidget(self.save_txt)
        srow.addStretch(1)
        self.body.addLayout(srow)
        self.swatches = QHBoxLayout()
        self.swatches.setSpacing(6)
        self.body.addLayout(self.swatches)
        self.colors = []

    def go(self):
        img = self.img.text()
        if not img:
            return self.set_status("Pick an image.", ok=False)
        n = self.n.value()

        def msg(r):
            self.colors = r
            self._render(r)
            self.save_img.setEnabled(True)
            self.save_txt.setEnabled(True)
            return f"Found {len(r)} colors."
        self.run_async(lambda: pdf_tools.extract_palette(img, n), msg)

    def _render(self, colors):
        while self.swatches.count():
            item = self.swatches.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for hex_code, _ in colors:
            cell = QVBoxLayout()
            box = QFrame()
            box.setFixedHeight(56)
            box.setStyleSheet(f"background: {hex_code}; border-radius: 8px;")
            lab = QLabel(hex_code)
            lab.setAlignment(Qt.AlignCenter)
            lab.setStyleSheet("font-family: Consolas; font-size: 11px;")
            holder = QWidget()
            hb = QVBoxLayout(holder)
            hb.setContentsMargins(0, 0, 0, 0)
            hb.addWidget(box)
            hb.addWidget(lab)
            self.swatches.addWidget(holder)

    def _save_image(self):
        if not self.colors:
            return
        p, _ = QFileDialog.getSaveFileName(self, "", SETTINGS.initdir(), "PNG (*.png)")
        if p:
            self.run_async(lambda: pdf_tools.save_palette_image(self.colors, p),
                           lambda r: f"Saved {os.path.basename(r)}")

    def _save_text(self):
        if not self.colors:
            return
        p, _ = QFileDialog.getSaveFileName(self, "", SETTINGS.initdir(), "Text (*.txt)")
        if p:
            self.run_async(lambda: pdf_tools.save_palette_text(self.colors, p),
                           lambda r: f"Saved {os.path.basename(r)}")


# ------------------------------- crop tool -------------------------------
class CropArea(QLabel):
    """Shows an image and lets the user drag a crop rectangle over it."""
    MAXW, MAXH = 620, 360

    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignCenter)
        self.setText("Pick an image to start")
        self.setStyleSheet("color: #888ea0; background: #20232e; border-radius: 10px;")
        self.setMinimumSize(self.MAXW, self.MAXH)
        self._pix = None
        self._scale = 1.0
        self._start = None
        self._rect = None        # selection in label coords
        self.orig_size = (0, 0)

    def load(self, path):
        pm = QPixmap(path)
        if pm.isNull():
            self.setText("Can't open image")
            self._pix = None
            return False
        self.orig_size = (pm.width(), pm.height())
        self._scale = min(self.MAXW / pm.width(), self.MAXH / pm.height(), 1.0)
        dw, dh = int(pm.width() * self._scale), int(pm.height() * self._scale)
        self._pix = pm.scaled(dw, dh, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self._rect = None
        self.setText("")
        self.update()
        return True

    def _img_rect(self):
        if not self._pix:
            return QRect()
        x = (self.width() - self._pix.width()) // 2
        y = (self.height() - self._pix.height()) // 2
        return QRect(x, y, self._pix.width(), self._pix.height())

    def mousePressEvent(self, e):
        if self._pix and self._img_rect().contains(e.position().toPoint()):
            self._start = e.position().toPoint()
            self._rect = QRect(self._start, self._start)
            self.update()

    def mouseMoveEvent(self, e):
        if self._start:
            ir = self._img_rect()
            p = e.position().toPoint()
            p.setX(max(ir.left(), min(p.x(), ir.right())))
            p.setY(max(ir.top(), min(p.y(), ir.bottom())))
            self._rect = QRect(self._start, p).normalized()
            self.update()

    def selection(self):
        """Return crop box in original pixels, or None."""
        if not self._rect or not self._pix or self._rect.width() < 3:
            return None
        ir = self._img_rect()
        lx = (self._rect.left() - ir.left()) / self._scale
        ty = (self._rect.top() - ir.top()) / self._scale
        rx = (self._rect.right() - ir.left()) / self._scale
        by = (self._rect.bottom() - ir.top()) / self._scale
        return (lx, ty, rx, by)

    def paintEvent(self, e):
        super().paintEvent(e)
        if not self._pix:
            return
        qp = QPainter(self)
        qp.drawPixmap(self._img_rect().topLeft(), self._pix)
        if self._rect:
            qp.setPen(QPen(QColor(ACCENT), 2))
            qp.drawRect(self._rect)


class CropImageTool(ToolPanel):
    def __init__(self, window):
        super().__init__(window, "Crop Image",
                         "Drag a box over the image to crop it.")

    def build(self):
        self.img = self.file_field("Image", "image")
        self.img.textChanged.connect(self._load)
        self.canvas = CropArea()
        self.body.addWidget(self.canvas, 0, Qt.AlignCenter)
        self.dims = QLabel("")
        self.dims.setObjectName("muted")
        self.body.addWidget(self.dims)
        self.out = self.file_field("Save as", "save_img")
        self.primary_button("Crop & Save")

    def _load(self):
        if self.canvas.load(self.img.text()):
            w, h = self.canvas.orig_size
            self.dims.setText(f"Original: {w} × {h}px  ·  drag to select")

    def go(self):
        out = self.out.text()
        box = self.canvas.selection()
        if not self.img.text():
            return self.set_status("Pick an image first.", ok=False)
        if not box:
            return self.set_status("Drag a box over the image.", ok=False)
        if not out:
            return self.set_status("Choose an output path.", ok=False)
        self.run_async(lambda: pdf_tools.crop_image(self.img.text(), out, box),
                       lambda r: f"Cropped to {r[0]} × {r[1]}px")


# =============================== settings ================================
class SettingsPanel(ToolPanel):
    def __init__(self, window):
        super().__init__(window, "Settings",
                         "Preferences are saved and remembered next time.")

    def build(self):
        self.theme = self.combo_field("Appearance", [tr("Light"), tr("Dark")])
        self.theme.setCurrentText(tr("Dark") if SETTINGS.get("theme") == "dark"
                                  else tr("Light"))
        self._theme_map = {tr("Light"): "light", tr("Dark"): "dark"}
        self.theme.currentTextChanged.connect(self._set_theme)

        self.lang = self.combo_field("Language", ["English", "Italiano"])
        self.lang.setCurrentText("Italiano" if SETTINGS.get("lang") == "it"
                                 else "English")
        self.lang.currentTextChanged.connect(self._set_lang)

        self.folder = QLineEdit(SETTINGS.get("folder"))
        browse = QPushButton(tr("Browse"))
        clear = QPushButton(tr("Clear"))
        for b in (browse, clear):
            b.setObjectName("ghost")
            b.setCursor(Qt.PointingHandCursor)
        browse.clicked.connect(self._pick_folder)
        clear.clicked.connect(self._clear_folder)
        row = QHBoxLayout()
        row.addWidget(self._label("Default folder"))
        row.addWidget(self.folder, 1)
        row.addWidget(browse)
        row.addWidget(clear)
        self.body.addLayout(row)
        self.hint("Where Browse dialogs start when picking files.")

    def _set_theme(self, choice):
        mode = self._theme_map.get(choice, "dark")
        SETTINGS.set("theme", mode)
        self.window.apply_theme(mode)

    def _set_lang(self, choice):
        lang = "it" if choice == "Italiano" else "en"
        if lang != SETTINGS.get("lang"):
            self.window.set_language(lang)

    def _pick_folder(self):
        d = QFileDialog.getExistingDirectory(self, "Choose a default folder…",
                                             SETTINGS.initdir())
        if d:
            self.folder.setText(d)
            SETTINGS.set("folder", d)
            self.set_status(f"Default folder set to {d}", ok=True)

    def _clear_folder(self):
        self.folder.setText("")
        SETTINGS.set("folder", "")
        self.set_status("Default folder cleared.", ok=True)


# ================================ home ===================================
class Card(QFrame):
    """Clickable tool tile."""
    def __init__(self, tool, on_click):
        super().__init__()
        self.setObjectName("card")
        self.setFixedSize(190, 122)
        self.setCursor(Qt.PointingHandCursor)
        icon, name, desc, cls, _ = tool
        self._cls = cls
        self._on_click = on_click

        v = QVBoxLayout(self)
        v.setContentsMargins(16, 14, 16, 14)
        v.setSpacing(4)
        ic = QLabel(icon)
        ic.setObjectName("cardicon")
        nm = QLabel(tr(name))
        nm.setObjectName("cardname")
        ds = QLabel(tr(desc))
        ds.setObjectName("carddesc")
        ds.setWordWrap(True)
        for w in (ic, nm, ds):
            w.setAttribute(Qt.WA_TransparentForMouseEvents)  # let card get hover/click
        v.addWidget(ic)
        v.addWidget(nm)
        v.addWidget(ds)
        v.addStretch(1)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._on_click(self._cls)


class HomePage(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        root = QVBoxLayout(self)
        root.setContentsMargins(34, 26, 34, 18)
        root.setSpacing(6)

        head = QHBoxLayout()
        left = QVBoxLayout()
        left.setSpacing(0)
        brand = QLabel("PDF & Tools")
        brand.setObjectName("brand")
        subtitle = QLabel(tr("{n} tools, one tidy toolbox").format(n=len(_tools())))
        subtitle.setObjectName("muted")
        left.addWidget(brand)
        left.addWidget(subtitle)
        head.addLayout(left)
        head.addStretch(1)
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍  " + tr("Search tools…"))
        self.search.setFixedWidth(250)
        self.search.textChanged.connect(self._filter)
        head.addWidget(self.search, 0, Qt.AlignTop)
        head.addSpacing(48)            # clear the floating gear
        root.addLayout(head)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        self.vbox = QVBoxLayout(container)
        self.vbox.setContentsMargins(0, 8, 0, 8)
        self.vbox.setSpacing(6)
        scroll.setWidget(container)
        root.addWidget(scroll, 1)

        self._sections = []   # (header_label, [cards], flow_container)
        self._cards = []      # (tool, Card)
        for cat in CATEGORIES:
            tools = [t for t in _tools() if t[4] == cat]
            if not tools:
                continue
            hdr = QLabel(tr(cat).upper())
            hdr.setObjectName("muted")
            hdr.setStyleSheet("font-weight: 700; font-size: 12px; padding-top: 10px;")
            self.vbox.addWidget(hdr)
            holder = QWidget()
            flow = FlowLayout(spacing=12)
            holder.setLayout(flow)
            cat_cards = []
            for t in tools:
                c = Card(t, self.window.open_tool)
                flow.addWidget(c)
                cat_cards.append(c)
                self._cards.append((t, c))
            self.vbox.addWidget(holder)
            self._sections.append((hdr, cat_cards, holder))
        self.vbox.addStretch(1)

        self.nomatch = QLabel(tr("No tools match your search."))
        self.nomatch.setObjectName("muted")
        self.nomatch.setAlignment(Qt.AlignCenter)
        self.nomatch.hide()
        self.vbox.addWidget(self.nomatch)

    def _filter(self, text):
        q = text.strip().lower()
        any_shown = False
        for hdr, cards, holder in self._sections:
            shown = 0
            for card in cards:
                t = next(tt for tt, cc in self._cards if cc is card)
                hay = f"{t[1]} {t[2]} {tr(t[1])} {tr(t[2])}".lower()
                vis = (not q) or (q in hay)
                card.setVisible(vis)
                shown += int(vis)
            hdr.setVisible(shown > 0)
            holder.setVisible(shown > 0)
            any_shown = any_shown or shown > 0
        self.nomatch.setVisible(bool(q) and not any_shown)


# ============================== main window ==============================
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF & Tools")
        self.resize(880, 640)
        self.setMinimumSize(720, 540)

        self.stack = QStackedWidget(self)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self.stack)

        self.gear = QPushButton("⚙", self)
        self.gear.setObjectName("gear")
        self.gear.setFixedSize(42, 42)
        self.gear.setCursor(Qt.PointingHandCursor)
        self.gear.clicked.connect(self.show_settings)

        self._cache = {}
        self.show_home()
        self.apply_theme(SETTINGS.get("theme"))

    # ---- navigation ----------------------------------------------------
    def _show(self, key, factory):
        page = self._cache.get(key)
        if page is None:
            page = factory()
            self._cache[key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(page)
        self.gear.raise_()

    def show_home(self):
        self._show("home", lambda: HomePage(self))

    def open_tool(self, cls):
        self._show(cls, lambda: cls(self))

    def show_settings(self):
        self._show("settings", lambda: SettingsPanel(self))

    # ---- theme + language ---------------------------------------------
    def apply_theme(self, mode):
        QApplication.instance().setStyleSheet(build_qss(mode))

    def set_language(self, lang):
        SETTINGS.set("lang", lang)
        # rebuild every page so strings re-translate
        for key, page in list(self._cache.items()):
            self.stack.removeWidget(page)
            page.deleteLater()
        self._cache.clear()
        self.show_settings()

    # ---- keep the gear pinned top-right -------------------------------
    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.gear.move(self.width() - self.gear.width() - 16, 14)
        self.gear.raise_()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PDF & Tools")
    try:
        app.setWindowIcon(QIcon(resource_path("pdf-and-tools.ico")))
    except Exception:
        pass
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
