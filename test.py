import sys
import subprocess
import json
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QFileDialog, QLabel, QHBoxLayout
)


def get_video_info(path: str):
    """调用 ffprobe 获取视频信息"""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,duration",
        "-of", "json",
        path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    info = json.loads(result.stdout)

    if not info.get("streams"):
        return None

    stream = info["streams"][0]
    width = stream["width"]
    height = stream["height"]
    duration = float(stream["duration"])
    fps_str = stream["r_frame_rate"]

    # 转换 r_frame_rate，例如 "30000/1001"
    try:
        num, den = map(int, fps_str.split("/"))
        fps = round(num / den, 2)
    except Exception:
        fps = None

    return {
        "width": width,
        "height": height,
        "duration": round(duration, 2),
        "fps": fps,
    }


class VideoInfoUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("视频信息查看器")
        self.resize(400, 200)

        layout = QVBoxLayout()

        # 选择按钮
        self.btn_select = QPushButton("选择视频")
        self.btn_select.clicked.connect(self.select_video)
        layout.addWidget(self.btn_select)

        # 信息区域
        info_layout = QVBoxLayout()
        self.label_path = QLabel("文件: 未选择")
        self.label_duration = QLabel("时长: -")
        self.label_fps = QLabel("帧率: -")
        self.label_resolution = QLabel("分辨率: -")

        info_layout.addWidget(self.label_path)
        info_layout.addWidget(self.label_duration)
        info_layout.addWidget(self.label_fps)
        info_layout.addWidget(self.label_resolution)

        layout.addLayout(info_layout)
        self.setLayout(layout)

    def select_video(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "选择视频", "", "Video Files (*.mp4 *.avi *.mkv *.mov)"
        )
        if file:
            self.label_path.setText(f"文件: {file}")
            info = get_video_info(file)
            if info:
                self.label_duration.setText(f"时长: {info['duration']} 秒")
                self.label_fps.setText(f"帧率: {info['fps']} fps")
                self.label_resolution.setText(f"分辨率: {info['width']}x{info['height']}")
            else:
                self.label_duration.setText("时长: 读取失败")
                self.label_fps.setText("帧率: 读取失败")
                self.label_resolution.setText("分辨率: 读取失败")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoInfoUI()
    window.show()
    sys.exit(app.exec())
