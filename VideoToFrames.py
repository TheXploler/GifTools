import sys
import os
import subprocess
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QMessageBox, QHBoxLayout, QFrame, QVBoxLayout,
    QDoubleSpinBox
)
from PyQt6.QtCore import Qt

class VideoToFramesConverter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video to Frames Extractor")
        self.resize(650, 450)
        self.init_ui()

    def init_ui(self):
        # Stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e2e;
            }
            QWidget {
                color: #cdd6f4;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
            }
            QFrame#Card {
                background-color: #313244;
                border-radius: 10px;
                border: 1px solid #45475a;
            }
            QLineEdit, QDoubleSpinBox {
                background-color: #181825;
                border: 1px solid #45475a;
                border-radius: 5px;
                padding: 8px;
                color: #cdd6f4;
            }
            QLineEdit:focus, QDoubleSpinBox:focus {
                border: 1px solid #89b4fa;
            }
            QPushButton {
                background-color: #45475a;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #585b70;
            }
            QPushButton#PrimaryBtn {
                background-color: #89b4fa;
                color: #1e1e2e;
                font-size: 16px;
                padding: 12px;
            }
            QPushButton#PrimaryBtn:hover {
                background-color: #b4befe;
            }
            QPushButton#IconBtn {
                padding: 5px;
                background-color: transparent;
                border: 1px solid #45475a;
            }
            QPushButton#IconBtn:hover {
                background-color: #45475a;
            }
            QLabel#Header {
                color: #89b4fa;
                font-size: 18px;
                font-weight: bold;
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        # Title
        title_lbl = QLabel("Video to Image Sequence")
        title_lbl.setObjectName("Header")
        main_layout.addWidget(title_lbl)

        # Files
        file_frame = QFrame()
        file_frame.setObjectName("Card")
        file_layout = QGridLayout(file_frame)
        file_layout.setContentsMargins(20, 20, 20, 20)
        file_layout.setSpacing(15)

        # Input Video
        file_layout.addWidget(QLabel("Source Video:"), 0, 0)
        self.entry_input = QLineEdit()
        self.entry_input.setPlaceholderText("Select video file...")
        file_layout.addWidget(self.entry_input, 0, 1)
        self.btn_browse_input = QPushButton("📂 Browse")
        self.btn_browse_input.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_browse_input.clicked.connect(self.browse_input)
        file_layout.addWidget(self.btn_browse_input, 0, 2)

        # Output Folder
        file_layout.addWidget(QLabel("Output Folder:"), 1, 0)
        self.entry_output = QLineEdit()
        self.entry_output.setPlaceholderText("Select folder to save frames...")
        file_layout.addWidget(self.entry_output, 1, 1)
        self.btn_browse_output = QPushButton("📂 Browse")
        self.btn_browse_output.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_browse_output.clicked.connect(self.browse_output)
        file_layout.addWidget(self.btn_browse_output, 1, 2)

        main_layout.addWidget(file_frame)

        # Settings
        settings_frame = QFrame()
        settings_frame.setObjectName("Card")
        settings_layout = QVBoxLayout(settings_frame)
        settings_layout.setContentsMargins(20, 20, 20, 20)
        settings_layout.setSpacing(15)

        settings_layout.addWidget(QLabel("Extraction Options"))

        opt_grid = QGridLayout()
        opt_grid.setSpacing(15)

        # FPS
        opt_grid.addWidget(QLabel("Frame Rate (FPS):"), 0, 0)

        fps_container = QHBoxLayout()
        self.spin_fps = QDoubleSpinBox()
        self.spin_fps.setRange(1.0, 144.0)
        self.spin_fps.setValue(30.0)
        self.spin_fps.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        self.spin_fps.setSuffix(" fps")
        fps_container.addWidget(self.spin_fps)

        self.btn_auto_fps = QPushButton("🔍 Detect")
        self.btn_auto_fps.setToolTip("Auto-detect FPS from source video")
        self.btn_auto_fps.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_auto_fps.clicked.connect(self.auto_detect_fps)
        fps_container.addWidget(self.btn_auto_fps)

        opt_grid.addLayout(fps_container, 0, 1)
        settings_layout.addLayout(opt_grid)
        main_layout.addWidget(settings_frame)

        main_layout.addStretch()

        self.btn_convert = QPushButton("Extract Frames")
        self.btn_convert.setObjectName("PrimaryBtn")
        self.btn_convert.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_convert.clicked.connect(self.extract_frames)
        main_layout.addWidget(self.btn_convert)

        self.lbl_status = QLabel("Ready")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet("color: #6c7086; font-size: 12px;")
        main_layout.addWidget(self.lbl_status)

    def browse_input(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Input Video", "", "Video Files (*.mp4 *.mov *.avi *.mkv)")
        if file_path:
            self.entry_input.setText(file_path)
            # Autosuggest output directory
            if not self.entry_output.text():
                base, _ = os.path.splitext(file_path)
                out_dir = base + "_frames"
                self.entry_output.setText(out_dir)
            self.auto_detect_fps()

    def browse_output(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if dir_path:
            self.entry_output.setText(dir_path)

    def get_video_info(self):
        input_file = self.entry_input.text()
        if not input_file or not os.path.exists(input_file):
            return None
        try:
            cmd = [
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=r_frame_rate",
                "-of", "json", input_file
            ]
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, startupinfo=startupinfo)
            data = json.loads(result.stdout)
            return data["streams"][0]
        except Exception:
            return None

    def auto_detect_fps(self):
        self.lbl_status.setText("Analyzing video...")
        QApplication.processEvents()
        info = self.get_video_info()
        if info:
            fps_str = info.get("r_frame_rate", "30/1")
            try:
                num, den = map(int, fps_str.split('/'))
                if den != 0:
                    fps = num / den
                    self.spin_fps.setValue(fps)
                    self.lbl_status.setText(f"Detected {fps:.2f} FPS")
            except ValueError:
                pass
        else:
            self.lbl_status.setText("Could not detect FPS")

    def extract_frames(self):
        input_file = self.entry_input.text()
        output_dir = self.entry_output.text()
        fps = self.spin_fps.value()

        if not os.path.exists(input_file):
            QMessageBox.critical(self, "Error", "Input file does not exist")
            return
        if not output_dir:
            QMessageBox.critical(self, "Error", "Please specify an output folder")
            return

        os.makedirs(output_dir, exist_ok=True)

        self.btn_convert.setEnabled(False)
        self.btn_convert.setText("Extracting...")
        QApplication.processEvents()

        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            self.lbl_status.setText("Extracting frames...")
            QApplication.processEvents()

            cmd = [
                "ffmpeg", "-y", "-i", input_file,
                "-vf", f"fps={fps}",
                os.path.join(output_dir, "frame_%04d.png")
            ]
            subprocess.run(cmd, check=True, startupinfo=startupinfo)

            self.lbl_status.setText("Done!")
            QMessageBox.information(self, "Success", f"Sequence extracted to:\n{output_dir}")

        except subprocess.CalledProcessError:
            self.lbl_status.setText("Error during extraction")
            QMessageBox.critical(self, "Error", "FFmpeg failed.")
        except Exception as e:
            self.lbl_status.setText("Error")
            QMessageBox.critical(self, "Error", f"An error occurred:\n{e}")
        finally:
            self.btn_convert.setEnabled(True)
            self.btn_convert.setText("Extract Frames")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoToFramesConverter()
    window.show()
    sys.exit(app.exec())
