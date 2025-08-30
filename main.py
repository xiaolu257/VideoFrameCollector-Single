# Project Path: ui/single_video_window.py
import os
import sys
import subprocess
import json
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QProgressBar, QComboBox,
    QSpinBox, QApplication, QGroupBox, QFormLayout,
    QMessageBox
)


class SingleVideoApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("单视频帧提取器")
        self.setGeometry(400, 150, 600, 400)
        self.settings = QSettings("MyCompany", "SingleVideoExtractor")

        self.setup_ui()
        # === 启动时自动加载上次选择的视频信息 ===
        last_file = self.settings.value("last_file", "")
        if last_file and os.path.isfile(last_file):
            self.load_video_info(last_file)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # === 文件选择 ===
        path_layout = QHBoxLayout()
        path_label = QLabel("🎬 视频文件:")
        self.file_input = QLineEdit()
        self.file_input.setReadOnly(True)
        self.file_input.setFixedWidth(350)
        self.file_input.setText(self.settings.value("last_file", ""))

        self.browse_btn = QPushButton("浏览")
        self.browse_btn.setFixedWidth(60)
        self.browse_btn.clicked.connect(self.choose_file)

        path_layout.addStretch(1)
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.file_input)
        path_layout.addWidget(self.browse_btn)
        path_layout.addStretch(1)
        layout.addLayout(path_layout)

        # === 视频信息区 ===
        self.info_group = QGroupBox("📊 视频信息")
        info_layout = QFormLayout()

        self.info_name = QLabel("-")
        self.info_type = QLabel("-")
        self.info_duration = QLabel("-")
        self.info_resolution = QLabel("-")
        self.info_fps = QLabel("-")
        self.info_frames = QLabel("-")

        info_layout.addRow("文件名:", self.info_name)
        info_layout.addRow("类型:", self.info_type)
        info_layout.addRow("时长:", self.info_duration)
        info_layout.addRow("分辨率:", self.info_resolution)
        info_layout.addRow("帧率 (FPS):", self.info_fps)
        info_layout.addRow("总帧数:", self.info_frames)

        self.info_group.setLayout(info_layout)
        layout.addWidget(self.info_group)

        # === 提取模式 ===
        mode_layout = QHBoxLayout()
        mode_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        mode_label = QLabel("🎯 提取模式:")
        self.mode_box = QComboBox()
        self.mode_box.addItems(["每N秒取1帧", "每N帧取1帧"])
        self.mode_box.setFixedWidth(180)

        param_label = QLabel("参数N:")
        self.param_input = QSpinBox()
        self.param_input.setRange(1, 3600)
        self.param_input.setValue(1)

        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.mode_box)
        mode_layout.addWidget(param_label)
        mode_layout.addWidget(self.param_input)
        layout.addLayout(mode_layout)

        # === 线程数 ===
        thread_layout = QHBoxLayout()
        thread_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        thread_label = QLabel("⚙️ 最大线程数:")
        self.thread_input = QComboBox()
        cpu_threads = os.cpu_count() or 4
        for i in range(1, cpu_threads + 1):
            self.thread_input.addItem(str(i))
        self.thread_input.setCurrentIndex(min(3, cpu_threads - 1))
        thread_layout.addWidget(thread_label)
        thread_layout.addWidget(self.thread_input)
        layout.addLayout(thread_layout)

        # === 图片格式 ===
        format_layout = QHBoxLayout()
        format_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        format_label = QLabel("🖼️ 图片格式:")
        self.format_box = QComboBox()
        self.format_box.addItems(["PNG", "JPG"])
        self.format_box.setFixedWidth(100)
        self.format_box.currentIndexChanged.connect(self.toggle_quality_input)

        self.quality_label = QLabel("压缩质量:")
        self.quality_input = QSpinBox()
        self.quality_input.setRange(1, 100)
        self.quality_input.setValue(85)
        self.quality_input.setFixedWidth(100)
        self.quality_label.setVisible(False)
        self.quality_input.setVisible(False)

        format_layout.addWidget(format_label)
        format_layout.addWidget(self.format_box)
        format_layout.addWidget(self.quality_label)
        format_layout.addWidget(self.quality_input)
        layout.addLayout(format_layout)

        # === 控制按钮 ===
        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.start_btn = QPushButton("🚀 开始提取")
        self.start_btn.setFixedWidth(120)

        self.pause_resume_btn = QPushButton("⏸ 暂停")
        self.pause_resume_btn.setFixedWidth(120)
        self.pause_resume_btn.setEnabled(False)

        self.stop_btn = QPushButton("⏹ 停止")
        self.stop_btn.setFixedWidth(120)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("color: red;")

        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.pause_resume_btn)
        btn_layout.addWidget(self.stop_btn)
        layout.addLayout(btn_layout)

        # === 进度显示 ===
        progress_layout = QVBoxLayout()
        progress_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(350)
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("准备就绪")
        progress_layout.addWidget(self.progress_label)

        layout.addLayout(progress_layout)

        self.setLayout(layout)

    def toggle_quality_input(self, index):
        is_jpg = self.format_box.currentText().lower() == "jpg"
        self.quality_label.setVisible(is_jpg)
        self.quality_input.setVisible(is_jpg)
        if is_jpg:
            self.quality_input.setValue(85)

    def choose_file(self):
        start_dir = self.file_input.text() or os.path.expanduser("~")
        file, _ = QFileDialog.getOpenFileName(
            self, "选择视频文件", start_dir,
            "视频文件 (*.mp4 *.avi *.mov *.mkv)"
        )
        if file:
            self.file_input.setText(file)
            self.settings.setValue("last_file", file)
            self.load_video_info(file)

    def format_duration(self, seconds: float) -> str:
        """格式化秒数为 n小时n分n秒"""
        seconds = int(seconds)
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        parts = []
        if h > 0:
            parts.append(f"{h}小时")
        if m > 0:
            parts.append(f"{m}分")
        if s > 0 or not parts:
            parts.append(f"{s}秒")
        return "".join(parts)

    def load_video_info(self, path):
        """用 ffprobe 获取视频信息"""
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration:stream=width,height,avg_frame_rate,nb_frames",
                "-of", "json", path
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode != 0:
                raise RuntimeError(result.stderr)

            info = json.loads(result.stdout)
            duration = float(info["format"]["duration"])
            streams = [s for s in info["streams"] if "width" in s]
            if not streams:
                raise RuntimeError("未找到视频流")
            stream = streams[0]

            width, height = stream.get("width", 0), stream.get("height", 0)
            fps_str = stream.get("avg_frame_rate", "0/1")
            fps = eval(fps_str) if fps_str != "0/0" else 0
            total_frames = stream.get("nb_frames", "未知")

            # 文件名和类型
            name = os.path.basename(path)
            ext = os.path.splitext(path)[1].lower().replace(".", "").upper()

            # 更新UI
            self.info_name.setText(name)
            self.info_type.setText(ext)
            self.info_duration.setText(self.format_duration(duration))
            self.info_resolution.setText(f"{width} x {height}")
            self.info_fps.setText(f"{fps:.2f}" if fps else "未知")
            self.info_frames.setText(total_frames)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法读取视频信息：\n{str(e)}")
            # 重置为默认
            self.info_name.setText("-")
            self.info_type.setText("-")
            self.info_duration.setText("-")
            self.info_resolution.setText("-")
            self.info_fps.setText("-")
            self.info_frames.setText("-")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = SingleVideoApp()
    win.show()
    sys.exit(app.exec())
