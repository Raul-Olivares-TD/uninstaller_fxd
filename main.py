"""
Uninstaller script for uninstall the fxdpipeline.
"""
import sys
from PySide6.QtWidgets import QApplication
from uninstaller_fxd.ui.uninstaller_window import UninstallWindow


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = UninstallWindow()
    window.show()
    sys.exit(app.exec())