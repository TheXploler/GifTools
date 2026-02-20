import sys
import os
import subprocess
import tempfile
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QMessageBox, QHBoxLayout, QFrame, QVBoxLayout,
    QSpinBox, QDoubleSpinBox, QSizePolicy, QStyle, QRadioButton
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QAction


class VideoToGifConverter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video ↔ GIF Converter")
        self.resize(650, 520)
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
            /* Cards */
            QFrame#Card {
                background-color: #313244;
                border-radius: 10px;
                border: 1px solid #45475a;
            }
            /* Inputs */
            QLineEdit, QSpinBox, QDoubleSpinBox {
                background-color: #181825;
                border: 1px solid #45475a;
                border-radius: 5px;
                padding: 8px;
                color: #cdd6f4;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border: 1px solid #a6e3a1; /* Green accent */
            }
            /* Buttons */
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
                background-color: #a6e3a1; /* Green */
                color: #1e1e2e;
                font-size: 16px;
                padding: 12px;
            }
            QPushButton#PrimaryBtn:hover {
                background-color: #94e2d5;
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
                color: #a6e3a1;
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
        self.title_lbl = QLabel("Video ↔ GIF Converter")
        self.title_lbl.setObjectName("Header")
        main_layout.addWidget(self.title_lbl)

        # Mode Selection
        mode_frame = QFrame()
        mode_frame.setObjectName("Card")
        mode_layout = QHBoxLayout(mode_frame)
        self.btn_mode_to_gif = QRadioButton("MP4 to GIF")
        self.btn_mode_to_mp4 = QRadioButton("GIF to MP4")
        self.btn_mode_to_gif.setChecked(True)
        self.btn_mode_to_gif.toggled.connect(self.on_mode_changed)
        mode_layout.addWidget(self.btn_mode_to_gif)
        mode_layout.addWidget(self.btn_mode_to_mp4)
        main_layout.addWidget(mode_frame)

        # Files
        file_frame = QFrame()
        file_frame.setObjectName("Card")
        file_layout = QGridLayout(file_frame)
        file_layout.setContentsMargins(20, 20, 20, 20)
        file_layout.setSpacing(15)

        # Input
        self.lbl_input = QLabel("Source Video:")
        file_layout.addWidget(self.lbl_input, 0, 0)
        self.entry_input = QLineEdit()
        self.entry_input.setPlaceholderText("Select .mp4 file...")
        file_layout.addWidget(self.entry_input, 0, 1)
        self.btn_browse_input = QPushButton("📂 Browse")
        self.btn_browse_input.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_browse_input.clicked.connect(self.browse_input)
        file_layout.addWidget(self.btn_browse_input, 0, 2)

        # Output
        self.lbl_output = QLabel("Output GIF:")
        file_layout.addWidget(self.lbl_output, 1, 0)
        self.entry_output = QLineEdit()
        self.entry_output.setPlaceholderText("Save destination...")
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

        settings_layout.addWidget(QLabel("Encoding Options"))

        # Grid for options
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
        self.btn_auto_fps.setObjectName("IconBtn")
        self.btn_auto_fps.setToolTip("Auto-detect FPS from source video")
        self.btn_auto_fps.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_auto_fps.clicked.connect(self.auto_detect_fps)
        fps_container.addWidget(self.btn_auto_fps)

        opt_grid.addLayout(fps_container, 0, 1)

        # Resolution
        opt_grid.addWidget(QLabel("Resolution:"), 1, 0)

        res_container = QHBoxLayout()
        self.spin_width = QSpinBox()
        self.spin_width.setRange(1, 7680)
        self.spin_width.setValue(640)
        self.spin_width.setPrefix("W: ")

        self.spin_height = QSpinBox()
        self.spin_height.setRange(1, 4320)
        self.spin_height.setValue(480)
        self.spin_height.setPrefix("H: ")

        res_container.addWidget(self.spin_width)
        res_container.addWidget(self.spin_height)

        self.btn_auto_res = QPushButton("🔍 Detect")
        self.btn_auto_res.setObjectName("IconBtn")
        self.btn_auto_res.setToolTip(
            "Auto-detect Resolution from source video")
        self.btn_auto_res.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_auto_res.clicked.connect(self.auto_detect_resolution)
        res_container.addWidget(self.btn_auto_res)

        opt_grid.addLayout(res_container, 1, 1)

        settings_layout.addLayout(opt_grid)
        main_layout.addWidget(settings_frame)

        # Action
        main_layout.addStretch()

        self.btn_convert = QPushButton("Start Conversion")
        self.btn_convert.setObjectName("PrimaryBtn")
        self.btn_convert.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_convert.clicked.connect(self.convert_video)
        main_layout.addWidget(self.btn_convert)

        # Status Bar
        self.lbl_status = QLabel("Ready")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet("color: #6c7086; font-size: 12px;")
        main_layout.addWidget(self.lbl_status)

    # Logic
    def on_mode_changed(self):
        self.entry_input.clear()
        self.entry_output.clear()
        if self.btn_mode_to_mp4.isChecked():
            self.title_lbl.setText("GIF to MP4 Converter")
            self.lbl_input.setText("Source GIF:")
            self.entry_input.setPlaceholderText("Select .gif file...")
            self.lbl_output.setText("Output Video:")
            self.entry_output.setPlaceholderText("Save destination...")
        else:
            self.title_lbl.setText("MP4 to GIF Converter")
            self.lbl_input.setText("Source Video:")
            self.entry_input.setPlaceholderText("Select .mp4 file...")
            self.lbl_output.setText("Output GIF:")
            self.entry_output.setPlaceholderText("Save destination...")

    def browse_input(self):
        if self.btn_mode_to_mp4.isChecked():
            filter_str = "GIF Files (*.gif)"
        else:
            filter_str = "Video Files (*.mp4 *.mov *.avi *.mkv)"
            
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Input File", "", filter_str)
        if file_path:
            self.entry_input.setText(file_path)
            # Autosuggest output
            if not self.entry_output.text():
                base, _ = os.path.splitext(file_path)
                ext = ".mp4" if self.btn_mode_to_mp4.isChecked() else ".gif"
                self.entry_output.setText(f"{base}{ext}")
            # Autorun detection
            self.auto_detect_fps()
            self.auto_detect_resolution()

    def browse_output(self):
        if self.btn_mode_to_mp4.isChecked():
            filter_str = "Video Files (*.mp4)"
            ext = ".mp4"
        else:
            filter_str = "GIF Files (*.gif)"
            ext = ".gif"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save As", "", filter_str)
        if file_path:
            if not file_path.lower().endswith(ext):
                file_path += ext
            self.entry_output.setText(file_path)

    def get_video_info(self):
        """Helper to get video metadata using ffprobe"""
        input_file = self.entry_input.text()
        if not input_file or not os.path.exists(input_file):
            return None

        try:
            cmd = [
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=width,height,r_frame_rate",
                "-of", "json", input_file
            ]
            # Hide console window on Windows
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True, startupinfo=startupinfo)
            data = json.loads(result.stdout)
            return data["streams"][0]
        except Exception as e:
            print(f"Probe Error: {e}")
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

    def auto_detect_resolution(self):
        self.lbl_status.setText("Analyzing video...")
        QApplication.processEvents()
        info = self.get_video_info()
        if info:
            w = info.get("width")
            h = info.get("height")
            if w and h:
                self.spin_width.setValue(int(w))
                self.spin_height.setValue(int(h))
                self.lbl_status.setText(f"Detected {w}x{h}")
        else:
            self.lbl_status.setText("Could not detect resolution")

    def convert_video(self):
        input_file = self.entry_input.text()
        output_file = self.entry_output.text()
        fps = self.spin_fps.value()
        width = self.spin_width.value()
        height = self.spin_height.value()

        if not os.path.exists(input_file):
            QMessageBox.critical(self, "Error", "Input file does not exist")
            return
        if not output_file:
            QMessageBox.critical(
                self, "Error", "Please specify an output file")
            return

        self.btn_convert.setEnabled(False)
        self.btn_convert.setText("Converting...")
        QApplication.processEvents()

        # Temp file for palette
        fd, palette_file = tempfile.mkstemp(suffix=".png")
        os.close(fd)  # Close handle so ffmpeg can use it

        try:
            # Startup info to hide console
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            # Generate GIF or MP4 depending on mode
            if self.btn_mode_to_mp4.isChecked():
                self.lbl_status.setText("Converting GIF to MP4...")
                QApplication.processEvents()
                # Need consistent even size for H.264
                mp4_cmd = [
                    "ffmpeg", "-y", "-i", input_file,
                    "-movflags", "faststart", "-pix_fmt", "yuv420p",
                    "-vf", f"fps={fps},scale={width}:{height}:flags=lanczos,scale=trunc(iw/2)*2:trunc(ih/2)*2",
                    output_file
                ]
                subprocess.run(mp4_cmd, check=True, startupinfo=startupinfo)
            else:
                self.lbl_status.setText("Phase 1/2: Generating Color Palette...")
                QApplication.processEvents()

                palette_cmd = [
                    "ffmpeg", "-y", "-i", input_file,
                    "-vf", f"fps={fps},scale={width}:{height}:flags=lanczos,palettegen",
                    palette_file
                ]
                subprocess.run(palette_cmd, check=True, startupinfo=startupinfo)

                self.lbl_status.setText("Phase 2/2: Encoding GIF...")
                QApplication.processEvents()

                gif_cmd = [
                    "ffmpeg", "-y", "-i", input_file, "-i", palette_file,
                    "-filter_complex", f"fps={fps},scale={width}:{height}:flags=lanczos[x];[x][1:v]paletteuse",
                    output_file
                ]
                subprocess.run(gif_cmd, check=True, startupinfo=startupinfo)

            self.lbl_status.setText("Done!")
            QMessageBox.information(
                self, "Success", f"File saved to:\n{output_file}")

        except subprocess.CalledProcessError:
            self.lbl_status.setText("Error during conversion")
            QMessageBox.critical(
                self, "Error", "FFmpeg failed. Check that ffmpeg is installed")
        except Exception as e:
            self.lbl_status.setText("Error")
            QMessageBox.critical(self, "Error", f"An error occurred:\n{e}")
        finally:
            if os.path.exists(palette_file):
                try:
                    os.remove(palette_file)
                except:
                    pass
            self.btn_convert.setEnabled(True)
            self.btn_convert.setText("Start Conversion")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoToGifConverter()
    window.show()
    sys.exit(app.exec())
