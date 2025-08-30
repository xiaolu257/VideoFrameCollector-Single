# Project Path: ui/single_video_window.py
import os
import sys
import subprocess
import json
from PyQt6.QtCore import Qt, QSettings, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog,
    QProgressBar, QComboBox, QSpinBox, QApplication, QGroupBox, QFormLayout, QMessageBox
)


def detect_gpu():
    """检测系统是否有可用 CUDA GPU"""
    try:
        result = subprocess.run(["ffmpeg", "-hwaccels"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return "cuda" in result.stdout.lower()
    except:
        return False


GPU_AVAILABLE = detect_gpu()  # 程序启动时检测一次


class FFmpegWorker(QThread):
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal()
    status_signal = pyqtSignal(str)

    def __init__(self, video_path, output_dir, start_sec, end_sec, mode, param, fmt, quality, total_frames):
        super().__init__()
        self.video_path = video_path
        self.output_dir = output_dir
        self.start_sec = start_sec
        self.end_sec = end_sec
        self.mode = mode
        self.param = param
        self.fmt = fmt
        self.quality = quality
        self.total_frames = total_frames
        self._stop = False
        self.proc = None

    def run(self):
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            input_options = []
            if GPU_AVAILABLE:
                input_options += ["-hwaccel", "cuda"]

            if self.mode == "每N秒取1帧":
                fps_option = f"1/{self.param}"
                cmd = [
                    "ffmpeg",
                    *input_options,
                    "-ss", str(self.start_sec),
                    "-to", str(self.end_sec),
                    "-i", self.video_path,
                    "-vf", f"fps={fps_option}",
                    os.path.join(self.output_dir, f"frame_%05d.{self.fmt.lower()}")
                ]
            else:
                select_filter = f"not(mod(n\\,{self.param}))"
                cmd = [
                    "ffmpeg",
                    *input_options,
                    "-ss", str(self.start_sec),
                    "-to", str(self.end_sec),
                    "-i", self.video_path,
                    "-vf", f"select='{select_filter}',setpts=N/FRAME_RATE/TB",
                    os.path.join(self.output_dir, f"frame_%05d.{self.fmt.lower()}")
                ]
            if self.fmt.lower() == "jpg":
                cmd.insert(-1, "-q:v")
                cmd.insert(-1, str(100 - self.quality))

            self.status_signal.emit("提取中...")
            self.proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="ignore"
            )

            # 使用迭代方式读取 stderr，避免 readline 阻塞
            for line in self.proc.stderr:
                if self._stop:
                    self.proc.terminate()
                    self.status_signal.emit("已终止处理")
                    break
                if "frame=" in line:
                    try:
                        for part in line.strip().split():
                            if part.startswith("frame="):
                                frame_num = int(part.split("=")[1])
                                if self.total_frames and self.total_frames != "未知":
                                    progress = min(int(frame_num / int(self.total_frames) * 100), 100)
                                else:
                                    total_sec = self.end_sec - self.start_sec
                                    progress = min(int(frame_num / (total_sec * 30) * 100), 100)
                                self.progress_signal.emit(progress)
                    except:
                        pass

            self.proc.wait()
            if not self._stop:
                self.progress_signal.emit(100)
                self.status_signal.emit("提取完成")
            self.finished_signal.emit()
        except Exception as e:
            self.status_signal.emit(f"提取错误: {str(e)}")
            self.finished_signal.emit()

    def stop(self):
        if self.proc:
            self._stop = True
            self.proc.terminate()
            self.status_signal.emit("已终止处理")


class SingleVideoApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("单视频帧提取器")
        self.setGeometry(400, 150, 700, 500)
        self.settings = QSettings("MyCompany", "SingleVideoExtractor")
        self.worker = None
        self.setup_ui()
        last_file = self.settings.value("last_file", "")
        if last_file and os.path.isfile(last_file):
            self.load_video_info(last_file)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 文件选择
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

        # 输出路径
        output_layout = QHBoxLayout()
        output_label = QLabel("📂 输出路径:")
        self.output_input = QLineEdit()
        self.output_input.setReadOnly(True)
        self.output_input.setFixedWidth(350)
        self.output_input.setText(self.settings.value("last_output_dir", os.path.expanduser("~")))
        self.output_btn = QPushButton("选择")
        self.output_btn.setFixedWidth(60)
        self.output_btn.clicked.connect(self.choose_output_dir)
        output_layout.addStretch(1)
        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_input)
        output_layout.addWidget(self.output_btn)
        output_layout.addStretch(1)
        layout.addLayout(output_layout)

        # 视频信息
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

        # 提取范围
        self.range_group = QGroupBox("⏱️ 提取范围")
        range_layout = QHBoxLayout()
        self.start_hour = QSpinBox()
        self.start_hour.setRange(0, 999)
        self.start_hour.setFixedWidth(60)
        self.start_min = QSpinBox()
        self.start_min.setRange(0, 59)
        self.start_min.setFixedWidth(60)
        self.start_sec = QSpinBox()
        self.start_sec.setRange(0, 59)
        self.start_sec.setFixedWidth(60)
        self.end_hour = QSpinBox()
        self.end_hour.setRange(0, 999)
        self.end_hour.setFixedWidth(60)
        self.end_min = QSpinBox()
        self.end_min.setRange(0, 59)
        self.end_min.setFixedWidth(60)
        self.end_sec = QSpinBox()
        self.end_sec.setRange(0, 59)
        self.end_sec.setFixedWidth(60)
        range_layout.addWidget(QLabel("起始时间:"))
        range_layout.addWidget(self.start_hour)
        range_layout.addWidget(QLabel("时"))
        range_layout.addWidget(self.start_min)
        range_layout.addWidget(QLabel("分"))
        range_layout.addWidget(self.start_sec)
        range_layout.addWidget(QLabel("秒"))
        range_layout.addWidget(QLabel("结束时间:"))
        range_layout.addWidget(self.end_hour)
        range_layout.addWidget(QLabel("时"))
        range_layout.addWidget(self.end_min)
        range_layout.addWidget(QLabel("分"))
        range_layout.addWidget(self.end_sec)
        range_layout.addWidget(QLabel("秒"))
        self.reset_range_btn = QPushButton("重置")
        self.reset_range_btn.clicked.connect(self.reset_time_range)
        range_layout.addWidget(self.reset_range_btn)
        self.range_group.setLayout(range_layout)
        layout.addWidget(self.range_group)

        # 提取模式
        mode_layout = QHBoxLayout()
        mode_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.mode_box = QComboBox()
        self.mode_box.addItems(["每N秒取1帧", "每N帧取1帧"])
        self.mode_box.setFixedWidth(180)
        param_label = QLabel("参数N:")
        self.param_input = QSpinBox()
        self.param_input.setRange(1, 3600)
        self.param_input.setValue(1)
        mode_layout.addWidget(QLabel("🎯 提取模式:"))
        mode_layout.addWidget(self.mode_box)
        mode_layout.addWidget(param_label)
        mode_layout.addWidget(self.param_input)
        layout.addLayout(mode_layout)

        # 图片格式
        format_layout = QHBoxLayout()
        format_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
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
        format_layout.addWidget(QLabel("🖼️ 图片格式:"))
        format_layout.addWidget(self.format_box)
        format_layout.addWidget(self.quality_label)
        format_layout.addWidget(self.quality_input)
        layout.addLayout(format_layout)

        # 控制按钮
        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.start_btn = QPushButton("🚀 开始提取")
        self.start_btn.setFixedWidth(120)
        self.start_btn.clicked.connect(self.start_extraction)
        self.stop_btn = QPushButton("⏹ 终止处理")
        self.stop_btn.setFixedWidth(120)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("color:red")
        self.stop_btn.clicked.connect(self.stop_extraction)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        layout.addLayout(btn_layout)

        # 进度显示
        progress_layout = QVBoxLayout()
        progress_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(350)
        self.progress_bar.setVisible(False)
        self.progress_label = QLabel("准备就绪")
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_label)
        layout.addLayout(progress_layout)

        self.setLayout(layout)

    def choose_output_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出文件夹",
                                                    self.output_input.text() or os.path.expanduser("~"))
        if dir_path:
            self.output_input.setText(dir_path)
            self.settings.setValue("last_output_dir", dir_path)

    def reset_time_range(self):
        self.start_hour.setValue(0)
        self.start_min.setValue(0)
        self.start_sec.setValue(0)
        total_sec = int(getattr(self, "video_duration_seconds", 0))
        h, m = divmod(total_sec, 3600)
        m, s = divmod(m, 60)
        self.end_hour.setValue(h)
        self.end_min.setValue(m)
        self.end_sec.setValue(s)

    def toggle_quality_input(self, index):
        is_jpg = self.format_box.currentText().lower() == "jpg"
        self.quality_label.setVisible(is_jpg)
        self.quality_input.setVisible(is_jpg)
        if is_jpg: self.quality_input.setValue(85)

    def choose_file(self):
        start_dir = self.file_input.text() or os.path.expanduser("~")
        file, _ = QFileDialog.getOpenFileName(self, "选择视频文件", start_dir, "视频文件 (*.mp4 *.avi *.mov *.mkv)")
        if file:
            self.file_input.setText(file)
            self.settings.setValue("last_file", file)
            self.load_video_info(file)

    def format_duration(self, seconds: float) -> str:
        seconds = int(seconds)
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        parts = []
        if h > 0: parts.append(f"{h}小时")
        if m > 0: parts.append(f"{m}分")
        if s > 0 or not parts: parts.append(f"{s}秒")
        return "".join(parts)

    def load_video_info(self, path):
        try:
            cmd = ["ffprobe", "-v", "error", "-show_entries",
                   "format=duration:stream=width,height,avg_frame_rate,nb_frames", "-of", "json", path]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode != 0: raise RuntimeError(result.stderr)
            info = json.loads(result.stdout)
            duration = float(info["format"]["duration"])
            streams = [s for s in info["streams"] if "width" in s]
            if not streams: raise RuntimeError("未找到视频流")
            stream = streams[0]
            width, height = stream.get("width", 0), stream.get("height", 0)
            fps_str = stream.get("avg_frame_rate", "0/1")
            fps = eval(fps_str) if fps_str != "0/0" else 0
            total_frames = stream.get("nb_frames", "未知")
            name = os.path.basename(path)
            ext = os.path.splitext(path)[1].lower().replace(".", "").upper()
            self.info_name.setText(name)
            self.info_type.setText(ext)
            self.info_duration.setText(self.format_duration(duration))
            self.info_resolution.setText(f"{width} x {height}")
            self.info_fps.setText(f"{fps:.2f}" if fps else "未知")
            self.info_frames.setText(total_frames)
            self.video_duration_seconds = int(duration)
            h, rem = divmod(self.video_duration_seconds, 3600)
            m, s = divmod(rem, 60)
            self.start_hour.setValue(0)
            self.start_min.setValue(0)
            self.start_sec.setValue(0)
            self.end_hour.setValue(h)
            self.end_min.setValue(m)
            self.end_sec.setValue(s)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法读取视频信息：\n{str(e)}")
            self.info_name.setText("-")
            self.info_type.setText("-")
            self.info_duration.setText("-")
            self.info_resolution.setText("-")
            self.info_fps.setText("-")
            self.info_frames.setText("-")
            self.start_hour.setValue(0)
            self.start_min.setValue(0)
            self.start_sec.setValue(0)
            self.end_hour.setValue(0)
            self.end_min.setValue(0)
            self.end_sec.setValue(0)
            self.video_duration_seconds = 0

    def get_selected_range_seconds(self):
        start_seconds = self.start_hour.value() * 3600 + self.start_min.value() * 60 + self.start_sec.value()
        end_seconds = self.end_hour.value() * 3600 + self.end_min.value() * 60 + self.end_sec.value()
        if start_seconds >= end_seconds:
            QMessageBox.warning(self, "错误", "起始时间必须小于结束时间")
            return None, None
        return start_seconds, end_seconds

    def start_extraction(self):
        if not self.file_input.text():
            QMessageBox.warning(self, "提示", "请先选择视频文件")
            return
        if not self.output_input.text():
            QMessageBox.warning(self, "提示", "请先选择输出路径")
            return
        start_sec, end_sec = self.get_selected_range_seconds()
        if start_sec is None: return

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        mode = self.mode_box.currentText()
        param = self.param_input.value()
        fmt = self.format_box.currentText()
        quality = self.quality_input.value() if fmt.lower() == "jpg" else 0
        total_frames = self.info_frames.text()
        self.worker = FFmpegWorker(
            self.file_input.text(),
            self.output_input.text(),
            start_sec,
            end_sec,
            mode,
            param,
            fmt,
            quality,
            total_frames
        )
        self.worker.progress_signal.connect(self.progress_bar.setValue)
        self.worker.status_signal.connect(self.progress_label.setText)
        self.worker.finished_signal.connect(self.extraction_finished)
        self.worker.start()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.progress_label.setText("正在提取...")

    def stop_extraction(self):
        if self.worker: self.worker.stop()

    def extraction_finished(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.worker = None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = SingleVideoApp()
    win.show()
    sys.exit(app.exec())
