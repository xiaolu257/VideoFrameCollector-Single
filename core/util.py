import json
import subprocess
from pathlib import Path


def get_duration(video_path: Path):
    """用 ffprobe 获取视频时长（秒）"""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json", video_path
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
        info = json.loads(res.stdout)
        return float(info["format"]["duration"])
    except Exception:
        return 0


def format_duration(seconds: float) -> str:
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    parts = []
    if h > 0: parts.append(f"{h}小时")
    if m > 0: parts.append(f"{m}分")
    if s > 0 or not parts: parts.append(f"{s}秒")
    return "".join(parts)
