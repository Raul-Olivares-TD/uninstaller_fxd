import sys
import os
import configparser
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                                QLabel, QPushButton, QListWidget,
                                QListWidgetItem, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon




def obtener_ruta_recurso(ruta_relativa):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, ruta_relativa)
    return os.path.join(os.path.abspath("."), ruta_relativa)

def _get_base_path():
    """Get base path depending on whether running as frozen exe or script."""
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent

def _get_icon_path():
    """Get icon path depending on whether running as frozen exe or script."""
    return _get_base_path() / "assets" / "logoApp03.ico"

def _get_pipeline_folder():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


class UninstallWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FXD Pipeline Uninstaller")
        self.setWindowIcon(QIcon(str(_get_icon_path())))
        self.setFixedSize(500, 400)
        self._setup_ui()
        self._load_versions()

        icon_path = _get_icon_path()
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Uninstall FXD Pipeline")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)

        lbl = QLabel("The following will be removed:")
        layout.addWidget(lbl)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()

        self.uninstall_btn = QPushButton("Uninstall")
        self.uninstall_btn.setStyleSheet("background: #e74c3c; color: white;")
        self.uninstall_btn.clicked.connect(self._uninstall)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.close)

        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.uninstall_btn)

        layout.addLayout(btn_layout)

    def _load_versions(self):
        pipeline_folder = _get_pipeline_folder()
        credentials_ini = pipeline_folder / "config" / "credentials.ini"

        if not credentials_ini.exists():
            item = QListWidgetItem(f"credentials.ini not found at {credentials_ini}")
            item.setFlags(Qt.NoItemFlags)
            self.list_widget.addItem(item)
            self.uninstall_btn.setEnabled(False)
            return

        config = configparser.ConfigParser()
        config.read(str(credentials_ini))
        fxdpipe_json = config.get("HOUDINI_USER_PREF_DIR", "json_file")

        self.pipeline_folder = pipeline_folder
        self.fxdpipe_json = Path(fxdpipe_json)

        item1 = QListWidgetItem(f"Pipeline folder: {pipeline_folder}")
        item1.setFlags(Qt.NoItemFlags)
        self.list_widget.addItem(item1)

        item2 = QListWidgetItem(f"fxdpipe.json: {fxdpipe_json}")
        item2.setFlags(Qt.NoItemFlags)
        self.list_widget.addItem(item2)


    def _uninstall(self):
        reply = QMessageBox.question(
            self, "Confirm",
            f"Remove fxdpipe.json and delete the Pipeline folder?\n\n"
            f"Pipeline folder: {self.pipeline_folder}\n"
            f"fxdpipe.json: {self.fxdpipe_json}",
            QMessageBox.Yes | QMessageBox.No
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

            # Copy to %TEMP% so PyInstaller cleanup of _MEIPASS doesn't kill it mid-execution
            bat_path = Path(tempfile.gettempdir()) / "fxd_uninstall.bat"
            shutil.copy2(src_bat, bat_path)

            try:
                cmd = ['cmd', '/c', str(bat_path)]
                if pipeline_path:
                    cmd.append(pipeline_path)
                subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
            except Exception as e:
                print(f"Error launching cleanup script: {e}")

