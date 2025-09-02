import json
import subprocess
import sys
from pathlib import Path

from PyQt6.QtWidgets import QMessageBox

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent  # 假设文件在 core/ 下
FFMPEG_BIN = PROJECT_ROOT / "ffmpeg" / ("ffmpeg.exe" if sys.platform == "win32" else "ffmpeg")
FFPROBE_BIN = PROJECT_ROOT / "ffmpeg" / ("ffprobe.exe" if sys.platform == "win32" else "ffprobe")


def check_ffmpeg_exists(gui_mode=True):
    missing = []
    if not FFMPEG_BIN.is_file():
        missing.append(FFMPEG_BIN)
    if not FFPROBE_BIN.is_file():
        missing.append(FFPROBE_BIN)
    if missing:
        msg = "缺少必要的组件：\n" + "\n".join(map(str, missing)) + \
              "\n\n请将 ffmpeg 和 ffprobe 放入项目的 ffmpeg/ 文件夹。"
        if gui_mode:
            QMessageBox.critical(None, "缺少 ffmpeg", msg)
        else:
            print(msg)
        sys.exit(1)


def get_duration(video_path: Path):
    """用内置 ffprobe 获取视频时长（秒），不显示 cmd 窗口"""
    cmd = [
        str(FFPROBE_BIN), "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        str(video_path)
    ]
    try:
        # Windows 下禁止弹出黑框
        creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="ignore",
            creationflags=creation_flags,
            shell=False
        )
        stdout, _ = proc.communicate()
        info = json.loads(stdout)
        return float(info["format"]["duration"])
    except Exception:
        return 0


def format_duration(seconds: float) -> str:
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    parts = []
    if h > 0:
        parts.append(f"{h}小时")
    if m > 0:
        parts.append(f"{m}分")
    if s > 0 or not parts: parts.append(f"{s}秒")
    return "".join(parts)
