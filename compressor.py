import sys
import subprocess
import os
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QFileDialog, QMessageBox, QProgressBar
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QCoreApplication

def get_duration(filename):
    """Return duration in seconds using ffprobe."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", filename],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    return float(result.stdout)


class CompressorThread(QThread):
    progress = Signal(str)
    finished = Signal(bool, str)

    def __init__(self, input_file, target_size_mb, output_file):
        super().__init__()
        self.input_file = input_file
        self.target_size_mb = target_size_mb
        self.output_file = output_file

    def run(self):
        try:
            duration = get_duration(self.input_file)
            target_bitrate = (self.target_size_mb * 1024 * 1024 * 8) / duration
            audio_bitrate = 128 * 1024
            video_bitrate = target_bitrate - audio_bitrate
            v_bitrate_k = int(video_bitrate / 1000)
            a_bitrate_k = 128

            # First pass
            self.progress.emit("Pass 1: Analyzing...")
            subprocess.run([
                "ffmpeg", "-y", "-i", self.input_file, "-b:v", f"{v_bitrate_k}k",
                "-pass", "1", "-an", "-f", "mp4", "/dev/null"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Second pass
            self.progress.emit("Pass 2: Compressing...")
            subprocess.run([
                "ffmpeg", "-i", self.input_file, "-b:v", f"{v_bitrate_k}k",
                "-b:a", f"{a_bitrate_k}k", "-pass", "2", self.output_file
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # ✅ Add this line
            self.progress.emit("✅ Compression complete!")
            self.finished.emit(True, self.output_file)
        except Exception as e:
            self.finished.emit(False, str(e))


class CompressorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FFmpeg Video Compressor")
        self.setMinimumWidth(400)

        layout = QVBoxLayout()

        self.label_file = QLabel("Select video file:")
        self.input_file = QLineEdit()
        self.btn_browse = QPushButton("Browse")
        self.btn_browse.clicked.connect(self.browse_file)

        self.label_size = QLabel("Target size (MB):")
        self.input_size = QLineEdit()

        self.btn_compress = QPushButton("Compress")
        self.btn_compress.clicked.connect(self.start_compression)

        self.progress = QLabel("")
        self.bar = QProgressBar()
        self.bar.setRange(0, 0)
        self.bar.hide()

        layout.addWidget(self.label_file)
        layout.addWidget(self.input_file)
        layout.addWidget(self.btn_browse)
        layout.addWidget(self.label_size)
        layout.addWidget(self.input_size)
        layout.addWidget(self.btn_compress)
        layout.addWidget(self.bar)
        layout.addWidget(self.progress)

        self.setLayout(layout)

    def browse_file(self):
        QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
        file, _ = QFileDialog.getOpenFileName(
            None,
            "Select Video",
            "",
            "Video Files (*.mp4 *.mkv *.mov *.avi *.webm *.flv *.ts *.m4v)"
        )
        if file:
            self.input_file.setText(file)

    def start_compression(self):
        file = self.input_file.text().strip()
        size = self.input_size.text().strip()

        if not os.path.exists(file) or not size.isdigit():
            QMessageBox.warning(self, "Error", "Please choose a valid file and target size.")
            return

        output = os.path.splitext(file)[0] + "_compressed.mp4"
        self.thread = CompressorThread(file, float(size), output)
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
    window = CompressorApp()
    window.show()
    sys.exit(app.exec())

