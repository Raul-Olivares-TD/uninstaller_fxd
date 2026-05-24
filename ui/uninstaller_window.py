import sys
import os
import configparser
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                                QLabel, QPushButton, QScrollArea, QFrame,
                                QMessageBox, QSizePolicy)
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QLinearGradient, QRegion, QPainterPath


# ── path helpers (identical to main_window.py) ────────────────────────────────

def _get_base_path():
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent

def _get_icon_path():
    return _get_base_path() / "assets" / "logoApp03.ico"

def _get_pipeline_folder():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


# ── stylesheet ─────────────────────────────────────────────────────────────────

_STYLESHEET = """
QWidget {
    color: #F8FAFC;
    font-family: 'Segoe UI', Arial, sans-serif;
}

QLabel {
    background-color: transparent;
}

QLabel#brand_label {
    color: #FF6E00;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 4px;
    background: transparent;
}

QLabel#headline {
    color: #F8FAFC;
    font-size: 26px;
    font-weight: 700;
    background: transparent;
}

QLabel#card_name {
    color: #F8FAFC;
    font-size: 14px;
    font-weight: 600;
    background: transparent;
}

QLabel#card_path {
    color: #94A3B8;
    font-size: 11px;
    font-family: 'Courier New', monospace;
    background: transparent;
}

QPushButton#cancel_btn {
    background-color: #2A3744;
    color: #94A3B8;
    border: 1px solid #334155;
    border-radius: 4px;
    font-size: 14px;
    font-weight: 600;
    min-height: 44px;
}
QPushButton#cancel_btn:hover {
    background-color: #37475A;
    color: #F8FAFC;
    border-color: #94A3B8;
}
QPushButton#cancel_btn:pressed {
    background-color: #051424;
}

QPushButton#uninstall_btn {
    background-color: #FF6E00;
    color: #FFFFFF;
    border: none;
    border-radius: 4px;
    font-size: 14px;
    font-weight: 600;
    min-height: 44px;
}
QPushButton#uninstall_btn:hover {
    background-color: #FF8C33;
}
QPushButton#uninstall_btn:pressed {
    background-color: #E65C00;
}
QPushButton#uninstall_btn:disabled {
    background-color: #594136;
    color: #A98A7C;
}

QScrollArea { border: none; }

QScrollBar:vertical {
    background: transparent;
    width: 6px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #334155;
    border-radius: 3px;
    min-height: 24px;
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical { height: 0; }
"""

_BG_IMAGE_HEIGHT = 180  # px reserved at the top for the header image


# ── components ─────────────────────────────────────────────────────────────────

class _FileCard(QFrame):
    _H_PADDING = 32  # 16px left + 16px right inside the card

    def __init__(self, name: str, path: str, parent=None):
        super().__init__(parent)
        self.setObjectName("file_card")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setStyleSheet("""
        QFrame#file_card {
            background-color: #1D2D40;
            border: 1px solid #FF6600;
            border-radius: 8px;
        }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        name_lbl = QLabel(name)
        name_lbl.setObjectName("card_name")

        # Insert zero-width spaces after separators so Qt's word-wrap engine
        # can break the path at backslashes/slashes without visible change.
        breakable = path.replace('\\', '\\​').replace('/', '/​')
        self._path_lbl = QLabel(breakable)
        self._path_lbl.setObjectName("card_path")
        self._path_lbl.setWordWrap(True)
        self._path_lbl.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)

        layout.addWidget(name_lbl)
        layout.addWidget(self._path_lbl)

    def resizeEvent(self, event):
        # Explicitly cap the label width so wrap is always triggered correctly.
        self._path_lbl.setMaximumWidth(self.width() - self._H_PADDING)
        super().resizeEvent(event)


# ── main window ────────────────────────────────────────────────────────────────

class UninstallWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FXD Pipeline Uninstaller")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedSize(420, 540)
        self.setStyleSheet(_STYLESHEET)

        # Load the header image.
        self._bg_pixmap = None
        candidate = _get_base_path() / "assets" / "uninstall.png"
        if candidate.exists():
            px = QPixmap(str(candidate))
            if not px.isNull():
                self._bg_pixmap = px

        self._setup_ui()
        self._load_versions()

        icon_path = _get_icon_path()
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # For dragging the window
        self.offset = None

    def mousePressEvent(self, event):
        """
        Called when the mouse is pressed.
        Saves the position to calculate offset for dragging.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.offset = (event.pos())

    # ── Move window ──────────────────────────────────────────────────────────────

    def mouseMoveEvent(self, event):
        """
        Called when the mouse is moved while clicking.
        Moves the window accordingly.
        """
        if self.offset is not None and event.buttons() == Qt.MouseButton.LeftButton:
            current_pos = (event.pos())
            self.move(self.pos() + current_pos - self.offset)

    def mouseReleaseEvent(self, event):
        """
        Reset the offset when the mouse is released.
        """
        self.offset = None

    # ── painting ──────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        # Base window background
        painter.fillRect(self.rect(), QColor("#051424"))

        # Header image strip (top _BG_IMAGE_HEIGHT px)
        header_rect = QRect(0, 0, self.width(), _BG_IMAGE_HEIGHT)
        if self._bg_pixmap:
            scaled = self._bg_pixmap.scaled(
                header_rect.width(), header_rect.height(),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation,
            )
            # Center-crop if wider than window after scaling
            src_x = max(0, (scaled.width() - header_rect.width()) // 2)
            painter.drawPixmap(header_rect, scaled, QRect(src_x, 0, header_rect.width(), header_rect.height()))
            # Overlay so text stays legible over any image
            painter.fillRect(header_rect, QColor(5, 20, 36, 170))

            # Gradient fade at the bottom of header so there is no hard cut
            fade_h = 48
            fade_rect = QRect(0, header_rect.bottom() - fade_h + 1, self.width(), fade_h)
            grad = QLinearGradient(0, fade_rect.top(), 0, fade_rect.bottom())
            grad.setColorAt(0.0, QColor(5, 20, 36, 0))
            grad.setColorAt(1.0, QColor(5, 20, 36, 255))
            painter.fillRect(fade_rect, grad)

        painter.end()

        # CREATE ROUND BORDERS BY MASK
        mask = QPainterPath()
        # Adjust the radius as needed
        mask.addRoundedRect(self.rect(), 10, 10)
        # Set mask for the window
        self.setMask(QRegion(mask.toFillPolygon().toPolygon()))

    # ── layout ────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, _BG_IMAGE_HEIGHT + 16, 24, 24)
        outer.setSpacing(0)

        brand = QLabel("FXD  UNINSTALLER")
        brand.setObjectName("brand_label")
        outer.addWidget(brand)
        outer.addSpacing(10)

        headline = QLabel("Files gonna be deleted:")
        headline.setObjectName("headline")
        headline.setWordWrap(True)
        outer.addWidget(headline)
        outer.addSpacing(20)

        # Scrollable card list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        cards_widget = QWidget()
        cards_widget.setStyleSheet("background: transparent;")
        self._cards_layout = QVBoxLayout(cards_widget)
        self._cards_layout.setContentsMargins(0, 0, 4, 0)
        self._cards_layout.setSpacing(8)

        scroll.setWidget(cards_widget)
        outer.addWidget(scroll, 1)
        outer.addSpacing(20)

        # Action buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("cancel_btn")
        self.cancel_btn.clicked.connect(self.close)

        self.uninstall_btn = QPushButton("Uninstall")
        self.uninstall_btn.setObjectName("uninstall_btn")
        self.uninstall_btn.clicked.connect(self._uninstall)

        btn_row.addWidget(self.cancel_btn)
        btn_row.addWidget(self.uninstall_btn)
        outer.addLayout(btn_row)

    # ── data loading ──────────────────────────────────────────────────────────

    def _add_card(self, name: str, path: str):
        self._cards_layout.addWidget(_FileCard(name, path))

    def _load_versions(self):
        pipeline_folder = _get_pipeline_folder()
        credentials_ini = pipeline_folder / "config" / "credentials.ini"

        if not credentials_ini.exists():
            self._add_card("credentials.ini not found", str(credentials_ini))
            self.uninstall_btn.setEnabled(False)
            self._cards_layout.addStretch()
            return

        config = configparser.ConfigParser()
        config.read(str(credentials_ini))
        fxdpipe_json = config.get("HOUDINI_USER_PREF_DIR", "json_file")

        self.pipeline_folder = pipeline_folder
        self.fxdpipe_json = Path(fxdpipe_json)

        self._add_card("Pipeline", str(pipeline_folder))
        self._add_card("fxdpipe.json", fxdpipe_json)
        self._cards_layout.addStretch()

    # ── actions ───────────────────────────────────────────────────────────────

    def _uninstall(self):
        reply = QMessageBox.question(
            self, "Confirm",
            f"Remove fxdpipe.json and delete the Pipeline folder?\n\n"
            f"Pipeline folder: {self.pipeline_folder}\n"
            f"fxdpipe.json: {self.fxdpipe_json}",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            try:
                os.remove(str(self.fxdpipe_json))
            except Exception as e:
                print(f"Error removing {self.fxdpipe_json}: {e}")
            self._launch_cleanup_script(str(self.pipeline_folder))
            QApplication.quit()

    def _launch_cleanup_script(self, pipeline_path=None):
        import subprocess
        import shutil
        import tempfile

        src_bat = _get_base_path() / "assets" / "uninstall.bat"
        if not src_bat.exists():
            return

        bat_path = Path(tempfile.gettempdir()) / "fxd_uninstall.bat"
        shutil.copy2(src_bat, bat_path)

        try:
            cmd = ["cmd", "/c", str(bat_path)]
            if pipeline_path:
                cmd.append(pipeline_path)
            subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
        except Exception as e:
            print(f"Error launching cleanup script: {e}")