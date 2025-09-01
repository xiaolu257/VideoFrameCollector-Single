import subprocess
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from core.util import get_duration


class FFmpegWorker(QThread):
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal()
    status_signal = pyqtSignal(str)

    def __init__(self, video_path, output_dir, start_sec, end_sec, mode, param, fmt, quality, video_info=None,
                 use_gpu=False):
        super().__init__()
        self.video_path = Path(video_path)
        self.output_dir = Path(output_dir)
        self.start_sec = start_sec
        self.end_sec = end_sec
        self.mode = mode
        self.param = param
        self.fmt = fmt.lower()
        self.quality = quality
        self.use_gpu = use_gpu
        self._stop = False
        self.proc = None

        # 帧数统计
        self.extracted_frames = 0

        # 🔹 使用传入的 video_info，只有在不合法时才获取
        if video_info is None or video_info.get("duration", 0) <= 0:
            full_duration = get_duration(self.video_path)
            video_info = {"duration": full_duration, "fps": 0, "total_frames": 0}
        self.video_info = video_info
        full_duration = self.video_info.get("duration", 0)
        self.duration = (min(full_duration,
                             self.end_sec) - self.start_sec) if self.end_sec > 0 else full_duration - self.start_sec
        if self.duration <= 0:
            self.duration = full_duration

    def run(self):
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)

            input_options = []
            if self.use_gpu:
                input_options += ["-hwaccel", "cuda"]

            output_pattern = str(self.output_dir / f"frame_%05d.{self.fmt}")

            # 计算 total_frames
            if self.mode == "每N秒取1帧":
                filter_option = f"fps=1/{self.param}"
                total_frames = max(1, int(self.duration / self.param))
            else:  # 每N帧取1帧
                filter_option = f"select='not(mod(n\\,{self.param}))',setpts=N/FRAME_RATE/TB"
                fps = self.video_info.get("fps", 0)
                if fps > 0:
                    total_frames_raw = int((self.end_sec - self.start_sec) * fps)
                    total_frames = max(1, total_frames_raw // self.param)
                else:
                    total_frames = 1

            cmd = [
                "ffmpeg",
                *input_options,
                "-ss", str(self.start_sec),
                "-to", str(self.end_sec),
                "-i", str(self.video_path),
                "-vf", filter_option
            ]

            if self.fmt == "jpg":
                q = max(1, min(31, int(31 * (100 - self.quality) / 100)))
                cmd += ["-q:v", str(q)]

            cmd += [output_pattern, "-progress", "pipe:1", "-nostats"]

            self.status_signal.emit("提取中...")

            self.proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="ignore",
                bufsize=1,
                universal_newlines=True
            )

            for line in iter(self.proc.stdout.readline, ''):
                if self._stop:
                    self.proc.terminate()
                    self.status_signal.emit("已终止处理")
                    break

                line = line.strip()

                # 每N秒模式：用 out_time_ms 更新进度，同时统计帧数
                if self.mode == "每N秒取1帧" and line.startswith("out_time_ms="):
                    try:
                        out_ms_str = line[len("out_time_ms="):]
                        out_ms = int(out_ms_str)
                        progress = min(int(out_ms / (self.duration * 1e6) * 100), 100)
                        self.progress_signal.emit(progress)

                        # 估算帧数（已处理时长 / param）
                        self.extracted_frames = min(total_frames, int((out_ms / 1e6) / self.param))
                    except Exception:
                        pass

                # 每N帧模式：用 frame= 更新进度，并记录帧数
                elif self.mode == "每N帧取1帧" and line.startswith("frame="):
                    try:
                        frame_str = line[len("frame="):]
                        self.extracted_frames = int(frame_str)
                        progress = min(int(self.extracted_frames / total_frames * 100), 100)
                        self.progress_signal.emit(progress)
                    except Exception:
                        pass

                elif line.startswith("progress=end"):
                    self.progress_signal.emit(100)

            self.proc.wait()
            if not self._stop:
                self.progress_signal.emit(100)
                self.status_signal.emit("提取完成")

                # 保底：没统计到就直接数文件数
                if self.extracted_frames <= 0:
                    try:
                        self.extracted_frames = len([
                            f for f in self.output_dir.iterdir()
                            if f.suffix.lower() == f".{self.fmt}"
                        ])
                    except Exception:
                        self.extracted_frames = 0

            self.finished_signal.emit()

        except Exception as e:
            self.status_signal.emit(f"提取错误: {e}")
            self.finished_signal.emit()

    def stop(self):
        if self.proc:
            self._stop = True
            self.proc.terminate()
            self.status_signal.emit("已终止处理")
