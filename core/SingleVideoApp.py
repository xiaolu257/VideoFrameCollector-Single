import datetime
import json
import os
import subprocess
import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog,
    QProgressBar, QComboBox, QSpinBox, QGroupBox, QFormLayout, QMessageBox
)

from core.FFmpegWorker import FFmpegWorker
from core.util import format_duration


def detect_gpu():
    """检测系统是否有可用 CUDA GPU"""
    try:
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        result = subprocess.run(
            ["ffmpeg", "-hwaccels"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=flags
        )
        return "cuda" in result.stdout.lower()
    except:
        return False


class SingleVideoApp(QWidget):
    def __init__(self):
        super().__init__()
        self.video_duration_seconds = None
        self.progress_label = None
        self.progress_bar = None
        self.stop_btn = None
        self.start_btn = None
        self.quality_input = None
        self.quality_label = None
        self.format_box = None
        self.param_input = None
        self.mode_box = None
        self.reset_range_btn = None
        self.end_sec = None
        self.end_min = None
        self.end_hour = None
        self.start_sec = None
        self.start_min = None
        self.start_hour = None
        self.range_group = None
        self.info_frames = None
        self.info_fps = None
        self.info_resolution = None
        self.info_duration = None
        self.info_type = None
        self.info_name = None
        self.info_group = None
        self.output_btn = None
        self.output_input = None
        self.browse_btn = None
        self.file_input = None
        self.setWindowTitle("单视频帧提取器")
        self.setGeometry(400, 150, 700, 500)
        self.settings = QSettings("MyCompany", "SingleVideoExtractor")
        self.worker = None
        self.current_video_info = None  # 🔹 缓存当前视频信息
        self.setup_ui()

        last_file = self.settings.value("last_file", "")
        last_file_path = Path(last_file)
        if last_file_path.is_file():
            self.load_video_info(last_file_path)

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
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 8px;
                background-color: #e6e6e6;     /* 背景浅灰 */
                text-align: center;
                padding-right: 6px;
                color: #333333;
                font-weight: bold;
            }
            QProgressBar::chunk {
                border-radius: 8px;            /* 整体圆角 */
                background: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4caf50, stop:1 #81c784
                );
                margin: 0px;                   /* 避免出现断层 */
            }
        """)

        self.progress_label = QLabel("准备就绪")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)  # 🔹保证始终居中
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_label)
        layout.addLayout(progress_layout)

        self.setLayout(layout)

    def choose_output_dir(self):
        start_dir = Path(self.output_input.text() or Path.home())
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出文件夹", str(start_dir))
        if dir_path:
            dir_path = Path(dir_path)
            self.output_input.setText(str(dir_path))
            self.settings.setValue("last_output_dir", str(dir_path))

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
        start_dir = Path(self.file_input.text() or Path.home())
        file, _ = QFileDialog.getOpenFileName(
            self,
            "选择视频文件",
            str(start_dir),
            "视频文件 (*.mp4 *.avi *.mov *.mkv)"
        )
        if file:
            file_path = Path(file)
            self.file_input.setText(str(file_path))
            self.settings.setValue("last_file", str(file_path))
            self.load_video_info(file_path)

    def load_video_info(self, path: Path):
        """
        读取视频信息并缓存，保证 total_frames 为 int
        """
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration:stream=width,height,avg_frame_rate,nb_frames",
                "-of", "json",
                str(path)
            ]

            # ✅ Windows 下禁止弹出黑框
            create_no_window = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=create_no_window
            )
            stdout, stderr = proc.communicate()

            if proc.returncode != 0:
                raise RuntimeError(stderr)

            info = json.loads(stdout)
            duration = float(info["format"]["duration"])

            streams = [s for s in info["streams"] if "width" in s]
            if not streams:
                raise RuntimeError("未找到视频流")
            stream = streams[0]

            width, height = stream.get("width", 0), stream.get("height", 0)
            fps_str = stream.get("avg_frame_rate", "0/1")
            fps = eval(fps_str) if fps_str != "0/0" else 0
            nb_frames_raw = stream.get("nb_frames", "0")
            try:
                total_frames = int(nb_frames_raw)
            except Exception:
                total_frames = 0

            self.info_name.setText(path.name)
            self.info_type.setText(path.suffix.lower().replace(".", "").upper())
            self.info_duration.setText(format_duration(duration))
            self.info_resolution.setText(f"{width} x {height}")
            self.info_fps.setText(f"{fps:.2f}" if fps else "未知")
            self.info_frames.setText(str(total_frames))

            # 缓存数据
            self.video_duration_seconds = int(duration)
            self.current_video_info = {
                "duration": duration,
                "fps": fps,
                "total_frames": total_frames
            }

            # 设置默认提取范围
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
            self.current_video_info = None

    def get_selected_range_seconds(self):
        """返回用户选择的起始和结束秒数，并进行合法性校验"""
        start_seconds = self.start_hour.value() * 3600 + self.start_min.value() * 60 + self.start_sec.value()
        end_seconds = self.end_hour.value() * 3600 + self.end_min.value() * 60 + self.end_sec.value()

        if start_seconds >= end_seconds:
            QMessageBox.warning(self, "错误", "起始时间必须小于结束时间")
            return None, None

        total_duration = getattr(self, "video_duration_seconds", 0)
        if total_duration <= 0:
            QMessageBox.warning(self, "错误", "视频时长信息无效，请重新选择视频文件")
            return None, None

        if end_seconds > total_duration:
            QMessageBox.warning(self, "错误", "结束时间不能超过视频总时长")
            return None, None

        if start_seconds < 0 or end_seconds < 0:
            QMessageBox.warning(self, "错误", "时间范围不能为负数")
            return None, None

        return start_seconds, end_seconds

    def start_extraction(self):
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, "提示", "正在提取，请等待完成或先终止处理")
            return

        if not self.file_input.text() or not self.output_input.text():
            QMessageBox.warning(self, "提示", "请先选择视频文件和输出路径")
            return

        start_sec, end_sec = self.get_selected_range_seconds()
        if start_sec is None:
            return

        self.toggle_ui_enabled(False)
        self.stop_btn.setEnabled(True)

        mode = self.mode_box.currentText()
        param = self.param_input.value()
        fmt = self.format_box.currentText()
        quality = self.quality_input.value() if fmt.lower() == "jpg" else 0
        use_gpu = detect_gpu()

        base_output = Path(self.output_input.text())
        video_name = Path(self.file_input.text()).stem
        timestamp = datetime.datetime.now().strftime("%Y年%m月%d日%H时%M分%S秒")
        output_dir = base_output / f"{video_name}_帧提取_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)

        video_info = getattr(self, "current_video_info", None)
        if video_info is None or video_info.get("duration", 0) <= 0:
            video_info = {
                "duration": getattr(self, "video_duration_seconds", 0),
                "fps": float(self.info_fps.text()) if self.info_fps.text() != "未知" else 0,
                "total_frames": int(self.info_frames.text()) if str(self.info_frames.text()).isdigit() else 0
            }

        self.worker = FFmpegWorker(
            video_path=str(self.file_input.text()),
            output_dir=output_dir,
            start_sec=start_sec,
            end_sec=end_sec,
            mode=mode,
            param=param,
            fmt=fmt,
            quality=quality,
            video_info=video_info,
            use_gpu=use_gpu
        )

        self.worker.progress_signal.connect(self.progress_bar.setValue)
        self.worker.status_signal.connect(self.progress_label.setText)
        self.worker.finished_signal.connect(self.extraction_finished)

        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.progress_label.setText("正在提取...")
        self.worker.start()

    def stop_extraction(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.progress_label.setText("终止中...")
            self.progress_bar.setValue(0)
            # 提取完成后 extraction_finished 会恢复 UI

    def extraction_finished(self):
        self.toggle_ui_enabled(True)
        self.stop_btn.setEnabled(False)

        if self.worker and self.worker._stop:
            self.progress_label.setText("已终止处理")
        else:
            self.progress_label.setText("提取完成")
            self.progress_bar.setValue(100)

            video_name = Path(self.worker.video_path).name
            output_dir = self.worker.output_dir
            frame_count = getattr(self.worker, "extracted_frames", None)

            details = f"视频文件：{video_name}\n输出目录：{output_dir}"
            if frame_count is not None:
                details += f"\n提取帧数：{frame_count}"

            reply = QMessageBox.question(
                self,
                "提取完成",
                f"帧提取已完成！\n\n{details}\n\n是否要打开输出文件夹？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )

            if reply == QMessageBox.StandardButton.Yes:
                if sys.platform == "win32":
                    os.startfile(output_dir)
                elif sys.platform == "darwin":
                    subprocess.run(["open", str(output_dir)])
                else:
                    subprocess.run(["xdg-open", str(output_dir)])

        self.worker = None

    def toggle_ui_enabled(self, enabled: bool):
        """
        控制提取期间可编辑的 UI 控件
        enabled: True => 恢复可编辑
                 False => 禁止编辑参数（但终止按钮除外）
        """
        # 影响提取参数的控件
        self.file_input.setEnabled(enabled)
        self.browse_btn.setEnabled(enabled)
        self.output_input.setEnabled(enabled)
        self.output_btn.setEnabled(enabled)
        self.start_hour.setEnabled(enabled)
        self.start_min.setEnabled(enabled)
        self.start_sec.setEnabled(enabled)
        self.end_hour.setEnabled(enabled)
        self.end_min.setEnabled(enabled)
        self.end_sec.setEnabled(enabled)
        self.reset_range_btn.setEnabled(enabled)  # 重置按钮也禁用
        self.mode_box.setEnabled(enabled)
        self.param_input.setEnabled(enabled)
        self.format_box.setEnabled(enabled)
        self.quality_input.setEnabled(enabled)

        # 开始按钮仅在 enabled=True 时可用
        self.start_btn.setEnabled(enabled)

        # stop_btn 不受此影响，保持单独控制
