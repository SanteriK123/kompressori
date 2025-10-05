#!/usr/bin/env python3

import sys
import subprocess
import os
import glob

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit,
    QFileDialog, QMessageBox, QProgressBar, QSlider, QComboBox
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QPalette, QColor, QIcon
from pathlib import Path

def get_duration(filename):
    """Return duration in seconds using ffprobe."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", filename],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    return float(result.stdout)

def get_video_dimensions(filename):
    """Return width, height, fps."""
    result = subprocess.run(
        ["ffprobe", "-v", "error",
         "-select_streams", "v:0",
         "-show_entries", "stream=width,height,r_frame_rate",
         "-of", "default=noprint_wrappers=1:nokey=1",
         filename],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    ).stdout.decode().splitlines()
    width = int(result[0])
    height = int(result[1])
    num, den = map(int, result[2].split('/'))
    fps = num / den
    return width, height, fps

def get_unique_output(file):
    base, ext = os.path.splitext(file)
    output = f"{base}_compressed.mp4"
    counter = 1
    while os.path.exists(output):
        output = f"{base}_compressed_{counter}.mp4"
        counter += 1
    return output

def get_app_icon():
    # Detect platform
    if getattr(sys, 'frozen', False):
        # Running from PyInstaller bundle
        base_path = Path(sys._MEIPASS)
    else:
        # Running from source
        base_path = Path(__file__).resolve().parent

    # Icon filenames we expect
    possible_icons = [
        base_path / "kompressori.png",         # local dev
        base_path / "icon.png",                # alternative
        Path("/usr/share/icons/hicolor/128x128/apps/kompressori.png"),  # Linux install path
    ]

    for icon_path in possible_icons:
        if icon_path.exists():
            return QIcon(str(icon_path))
    return QIcon()  # fallback empty icon

class CompressorThread(QThread):
    progress = Signal(str)
    finished = Signal(bool, str)

    def __init__(self, input_file, target_size_mb, output_file, scale_pct, fps_target):
        super().__init__()
        self.input_file = input_file
        self.target_size_mb = target_size_mb
        self.output_file = output_file
        self.scale_pct = scale_pct / 100
        self.fps_target = fps_target

    def run(self):
        try:
            # Detect OS-specific null device
            null_device = "NUL" if os.name == "nt" else "/dev/null"

            duration = get_duration(self.input_file)
            width, height, original_fps = get_video_dimensions(self.input_file)

            new_width = int(width * self.scale_pct)
            new_height = int(height * self.scale_pct)
            fps = min(self.fps_target, original_fps)

            target_bitrate = (self.target_size_mb * 1024 * 1024 * 8) / duration
            audio_bitrate = 128 * 1024
            video_bitrate = target_bitrate - audio_bitrate
            v_bitrate_k = int(video_bitrate / 1000)
            a_bitrate_k = 128

            scale_filter = f"scale={new_width}:{new_height}"

            # Use a log file beside the output (so we always have write access)
            base_name, _ = os.path.splitext(self.output_file)
            log_file = f"{base_name}_2pass.log"

            # First pass
            self.progress.emit("Pass 1: Analyzing...")
            subprocess.run([
                "ffmpeg", "-y", "-i", self.input_file,
                "-vf", scale_filter, "-r", str(fps),
                "-b:v", f"{v_bitrate_k}k",
                "-pass", "1", "-an",
                "-passlogfile", log_file,
                "-f", "mp4", null_device
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Second pass
            self.progress.emit("Pass 2: Compressing...")
            subprocess.run([
                "ffmpeg", "-y", "-i", self.input_file,
                "-vf", scale_filter, "-r", str(fps),
                "-b:v", f"{v_bitrate_k}k",
                "-b:a", f"{a_bitrate_k}k",
                "-pass", "2",
                "-passlogfile", log_file,
                "-c:v", "libx264", "-c:a", "aac",
                self.output_file
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Cleanup two-pass log files
            for f in glob.glob(f"{base_name}_2pass.log*"):
                try:
                    os.remove(f)
                except Exception:
                    pass

            self.progress.emit("✅ Compression complete!")
            self.finished.emit(True, self.output_file)
        except Exception as e:
            self.finished.emit(False, str(e))

class CompressorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kompressori")
        self.setMinimumWidth(450)

        # ----------------- Color setup -----------------
        primary_color = self.palette().color(QPalette.Highlight)
        h, s, v, a = primary_color.getHsvF()
        comp_hue = (h + 0.5) % 1.0
        secondary_color = QColor.fromHsvF(comp_hue, s, v, a)

        self.primary_hex = primary_color.name()
        self.secondary_hex = secondary_color.name()
        self.accent_hex = primary_color.name()
        self.bg_hex = "#fff0db"

        # ----------------- Global stylesheet -----------------
        self.setStyleSheet(f"""
        QWidget {{
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 14px;
            color: {self.secondary_hex};
            background-color: {self.bg_hex};
        }}
        QLineEdit {{
            border: 2px solid {self.secondary_hex};
            border-radius: 6px;
            padding: 4px;
            background-color: #1a1a1a;
            color: white;
        }}
        QLabel {{
            font-weight: bold;
            color: {self.accent_hex};
        }}
        QPushButton {{
            background-color: {self.primary_hex};
            border: 2px solid {self.accent_hex};
            border-radius: 10px;
            color: white;
            font-weight: bold;
            padding: 6px 12px;
        }}
        QPushButton:hover {{
            background-color: {self.accent_hex};
            color: {self.bg_hex};
        }}
        QProgressBar {{
            border: 2px solid {self.accent_hex};
            border-radius: 8px;
            text-align: center;
            background-color: #1a1a1a;
            color: white;
        }}
        QProgressBar::chunk {{
            background-color: {self.primary_hex};
            width: 20px;
            margin: 0.5px;
        }}
        QComboBox {{
            border: 2px solid {self.secondary_hex};
            border-radius: 6px;
            padding: 4px;
            background-color: #1a1a1a;
            color: white;
        }}
        QComboBox QAbstractItemView {{
            background-color: #1a1a1a;
            selection-background-color: {self.primary_hex};
            color: white;
        }}
        """)

        layout = QVBoxLayout()

        # ----------------- File selection -----------------
        self.label_file = QLabel("Select video file:")
        self.input_file = QLineEdit()
        self.btn_browse = QPushButton("Browse")
        self.btn_browse.clicked.connect(self.browse_file)

        # ----------------- Target size -----------------
        self.label_size = QLabel("Target size (MB):")
        self.input_size = QLineEdit()

        # ----------------- Frame rate dropdown -----------------
        self.label_fps = QLabel("Frame rate (fps):")
        self.fps_combo = QComboBox()
        self.fps_combo.addItems(["10", "15", "24", "30", "45", "60"])
        self.fps_combo.setCurrentText("24")

        # ----------------- Resolution slider -----------------
        self.label_res = QLabel("Resolution scale: 100%")
        self.res_slider = QSlider(Qt.Horizontal)
        self.res_slider.setRange(0, 100)
        self.res_slider.setValue(100)
        self.res_slider.setTickInterval(25)
        self.res_slider.setTickPosition(QSlider.TicksBelow)
        self.res_slider.valueChanged.connect(self.update_res_label)
        self.res_slider.setStyleSheet(f"""
        QSlider::groove:horizontal {{
            height: 12px;
            border-radius: 6px;
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 {self.secondary_hex},
                stop:0.25 {self.secondary_hex},
                stop:0.25 {self.primary_hex},
                stop:1 {self.primary_hex}
            );
        }}
        QSlider::handle:horizontal {{
            background: #1f2041;
            border: 2px solid {self.accent_hex};
            width: 20px;
            height: 20px;
            margin: -4px 0;
            border-radius: 10px;
        }}
        """)

        # ----------------- Compress button -----------------
        self.btn_compress = QPushButton("Compress")
        self.btn_compress.clicked.connect(self.start_compression)

        # ----------------- Progress bar & label -----------------
        self.progress = QLabel("")
        self.bar = QProgressBar()
        self.bar.setRange(0, 0)
        self.bar.hide()

        # ----------------- Layout setup -----------------
        layout.addWidget(self.label_file)
        layout.addWidget(self.input_file)
        layout.addWidget(self.btn_browse)
        layout.addWidget(self.label_size)
        layout.addWidget(self.input_size)
        layout.addWidget(self.label_fps)
        layout.addWidget(self.fps_combo)
        layout.addWidget(self.label_res)
        layout.addWidget(self.res_slider)
        layout.addWidget(self.btn_compress)
        layout.addWidget(self.bar)
        layout.addWidget(self.progress)

        self.setLayout(layout)

    def update_res_label(self, value):
        if value < 25:
            self.res_slider.setValue(25)
            value = 25
        self.label_res.setText(f"Resolution scale: {value}%")

    def browse_file(self):
        file, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video",
            "",
            "Video Files (*.mp4 *.mkv *.mov *.avi *.webm *.flv *.ts *.m4v)"
        )
        if file:
            self.input_file.setText(file)

    def start_compression(self):
        file = self.input_file.text().strip()
        size = self.input_size.text().strip()
        fps = int(self.fps_combo.currentText())
        scale = self.res_slider.value()

        if not os.path.exists(file) or not size.isdigit():
            QMessageBox.warning(self, "Error", "Please choose a valid file and target size.")
            return

        output = get_unique_output(file)

        self.thread = CompressorThread(file, float(size), output, scale, fps)
        self.thread.progress.connect(self.update_progress)
        self.thread.finished.connect(self.compression_done)

        self.bar.show()
        self.progress.setText("Starting...")
        self.btn_compress.setEnabled(False)
        self.thread.start()

    def update_progress(self, text):
        self.progress.setText(text)

    def compression_done(self, success, msg):
        self.bar.hide()
        self.btn_compress.setEnabled(True)
        if success:
            self.progress.setText("✅ Done!")
            QTimer.singleShot(3000, lambda: self.progress.setText(""))
            QMessageBox.information(self, "Done", f"Compression complete!\nSaved to:\n{msg}")
        else:
            self.progress.setText("❌ Failed.")
            QMessageBox.critical(self, "Error", msg)
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(get_app_icon())
    window = CompressorApp()
    window.show()
    sys.exit(app.exec())

