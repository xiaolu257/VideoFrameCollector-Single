# Project Path: ui/single_video_window.py
import sys

from PyQt6.QtWidgets import (
    QApplication
)

from core.SingleVideoApp import SingleVideoApp
from core.util import check_ffmpeg_exists

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # ---------- 调用检测函数 ---------- #
    check_ffmpeg_exists()

    # ---------- 正常启动 ---------- #
    win = SingleVideoApp()
    win.show()
    sys.exit(app.exec())
