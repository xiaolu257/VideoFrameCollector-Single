# Project Path: ui/single_video_window.py
import sys

from PyQt6.QtWidgets import (
    QApplication
)

from core.SingleVideoApp import SingleVideoApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = SingleVideoApp()
    win.show()
    sys.exit(app.exec())
