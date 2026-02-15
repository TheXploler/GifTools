import sys
import os
import tempfile
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QGridLayout, QFileDialog, QComboBox, QMessageBox,
    QSlider, QStackedWidget, QVBoxLayout, QHBoxLayout,
    QDoubleSpinBox, QFrame, QMainWindow
)
from PyQt6.QtCore import Qt


class GifConverterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GIF Resizer & Scaler")
        self.resize(600, 550)
        self.init_ui()

    def init_ui(self):
        # Theme & Stylesheet
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
                border-radius: 12px;
                border: 1px solid #45475a;
            }
            /* Inputs */
            QLineEdit, QComboBox, QDoubleSpinBox {
                background-color: #181825;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 8px;
                color: #cdd6f4;
            }
            QLineEdit:focus, QDoubleSpinBox:focus {
                border: 1px solid #89b4fa;
            }
            /* Buttons */
            QPushButton {
                background-color: #45475a;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #585b70;
            }
            QPushButton#PrimaryBtn {
                background-color: #89b4fa; /* Blue accent */
                color: #1e1e2e;
                font-size: 16px;
                padding: 12px;
            }
            QPushButton#PrimaryBtn:hover {
                background-color: #b4befe;
            }
            /* Sliders */
            QSlider::groove:horizontal {
                border: 1px solid #45475a;
                height: 8px;
                background: #181825;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #89b4fa;
                border: 1px solid #89b4fa;
                width: 18px;
                height: 18px;
                margin: -7px 0;
                border-radius: 9px;
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main Layout
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(30, 30, 30, 30)
        self.main_layout.setSpacing(20)

        # Header
        header = QLabel("Resize & Scale GIF")
        header.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #89b4fa;")
        self.main_layout.addWidget(header)

        # I/O Card
        io_frame = QFrame()
        io_frame.setObjectName("Card")
        io_layout = QGridLayout(io_frame)
        io_layout.setContentsMargins(20, 20, 20, 20)
        io_layout.setSpacing(15)

        # Input
        io_layout.addWidget(QLabel("Input File:"), 0, 0)
        self.entry_input = QLineEdit()
        self.entry_input.setPlaceholderText("Select source GIF...")
        io_layout.addWidget(self.entry_input, 0, 1)
        self.btn_browse_input = QPushButton("📂 Browse")
        self.btn_browse_input.setToolTip("Browse Input")
        self.btn_browse_input.clicked.connect(self.browse_input)
        io_layout.addWidget(self.btn_browse_input, 0, 2)

        # Output
        io_layout.addWidget(QLabel("Output File:"), 1, 0)
        self.entry_output = QLineEdit()
        self.entry_output.setPlaceholderText("Save destination...")
        io_layout.addWidget(self.entry_output, 1, 1)
        self.btn_browse_output = QPushButton("📂 Browse")
        self.btn_browse_output.setToolTip("Browse Output")
        self.btn_browse_output.clicked.connect(self.browse_output)
        io_layout.addWidget(self.btn_browse_output, 1, 2)

        # FPS Row
        io_layout.addWidget(QLabel("Frame Rate:"), 2, 0)
        self.entry_fps = QLineEdit()
        self.entry_fps.setPlaceholderText("Auto")
        io_layout.addWidget(self.entry_fps, 2, 1)
        self.btn_detect_fps = QPushButton("Detect FPS")
        self.btn_detect_fps.setStyleSheet("font-size: 11px; padding: 5px;")
        self.btn_detect_fps.clicked.connect(self.detect_fps_ui)
        io_layout.addWidget(self.btn_detect_fps, 2, 2)

        self.main_layout.addWidget(io_frame)

        # Settings Card
        settings_frame = QFrame()
        settings_frame.setObjectName("Card")
        settings_layout = QVBoxLayout(settings_frame)
        settings_layout.setContentsMargins(20, 20, 20, 20)
        settings_layout.setSpacing(15)

        # Mode Selection
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Resize Strategy:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(
            ["Fixed Resolution (Px)", "Scale Percentage (%)", "Target File Size (MB)"])
        self.mode_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mode_combo.currentIndexChanged.connect(self.update_mode)
        mode_layout.addWidget(self.mode_combo, 1)
        settings_layout.addLayout(mode_layout)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Plain)
        line.setStyleSheet("background-color: #45475a;")
        settings_layout.addWidget(line)

        # Stacked Widget for Options
        self.options_stack = QStackedWidget()

        # Resolution
        self.page_resolution = QWidget()
        res_layout = QHBoxLayout(self.page_resolution)
        res_layout.setContentsMargins(0, 10, 0, 10)
        res_layout.addWidget(QLabel("Width:"))
        self.entry_width = QLineEdit("640")
        res_layout.addWidget(self.entry_width)
        res_layout.addWidget(QLabel("Height:"))
        self.entry_height = QLineEdit("480")
        res_layout.addWidget(self.entry_height)
        self.options_stack.addWidget(self.page_resolution)

        # Scale
        self.page_scale = QWidget()
        scale_layout = QHBoxLayout(self.page_scale)
        scale_layout.setContentsMargins(0, 10, 0, 10)
        scale_layout.addWidget(QLabel("Scale:"))
        self.scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.scale_slider.setRange(1, 200)
        self.scale_slider.setValue(100)
        self.scale_spinbox = QDoubleSpinBox()
        self.scale_spinbox.setRange(1.0, 5000.0)
        self.scale_spinbox.setValue(100.0)
        self.scale_spinbox.setSuffix("%")

        self.scale_slider.valueChanged.connect(self.sync_scale_slider_to_box)
        self.scale_spinbox.valueChanged.connect(self.sync_scale_box_to_slider)

        scale_layout.addWidget(self.scale_slider)
        scale_layout.addWidget(self.scale_spinbox)
        self.options_stack.addWidget(self.page_scale)

        # Target Size
        self.page_target = QWidget()
        target_layout = QHBoxLayout(self.page_target)
        target_layout.setContentsMargins(0, 10, 0, 10)
        target_layout.addWidget(QLabel("Target:"))
        self.target_slider = QSlider(Qt.Orientation.Horizontal)
        self.target_slider.setRange(1, 200)  # 0.1MB to 20MB
        self.target_slider.setValue(100)
        self.target_spinbox = QDoubleSpinBox()
        self.target_spinbox.setRange(0.01, 1000.0)
        self.target_spinbox.setValue(10.0)
        self.target_spinbox.setSuffix(" MB")

        self.target_slider.valueChanged.connect(self.sync_target_slider_to_box)
        self.target_spinbox.valueChanged.connect(
            self.sync_target_box_to_slider)

        target_layout.addWidget(self.target_slider)
        target_layout.addWidget(self.target_spinbox)
        self.options_stack.addWidget(self.page_target)

        settings_layout.addWidget(self.options_stack)
        self.main_layout.addWidget(settings_frame)

        # Action
        self.main_layout.addStretch()

        self.btn_convert = QPushButton("Process GIF")
        self.btn_convert.setObjectName("PrimaryBtn")
        self.btn_convert.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_convert.clicked.connect(self.convert_gif)
        self.main_layout.addWidget(self.btn_convert)

        self.lbl_status = QLabel("Ready")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet(
            "color: #6c7086; font-size: 12px; margin-top: 5px;")
        self.main_layout.addWidget(self.lbl_status)

    # Probing FPS 🥵
    def get_fps_probe(self, file_path):
        if not os.path.exists(file_path):
            return None
        try:
            cmd = [
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=r_frame_rate",
                "-of", "default=noprint_wrappers=1:nokey=1", file_path
            ]
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            result = subprocess.check_output(
                cmd, startupinfo=startupinfo).decode().strip()

            if '/' in result:
                num, den = result.split('/')
                if int(den) > 0:
                    return str(int(round(int(num) / int(den))))
            return str(int(float(result)))
        except Exception as e:
            print(f"FPS Detection Error: {e}")
            return "30"

    def detect_fps_ui(self):
        path = self.entry_input.text()
        if path:
            fps = self.get_fps_probe(path)
            if fps:
                self.entry_fps.setText(fps)
                self.lbl_status.setText(f"Detected {fps} FPS")
            else:
                self.lbl_status.setText("Could not detect FPS")

    # Sync Logic
    def sync_scale_slider_to_box(self, value):
        self.scale_spinbox.blockSignals(True)
        self.scale_spinbox.setValue(float(value))
        self.scale_spinbox.blockSignals(False)

    def sync_scale_box_to_slider(self, value):
        self.scale_slider.blockSignals(True)
        self.scale_slider.setValue(int(value))
        self.scale_slider.blockSignals(False)

    def sync_target_slider_to_box(self, value):
        float_val = value / 10.0
        self.target_spinbox.blockSignals(True)
        self.target_spinbox.setValue(float_val)
        self.target_spinbox.blockSignals(False)

    def sync_target_box_to_slider(self, value):
        int_val = int(value * 10)
        self.target_slider.blockSignals(True)
        self.target_slider.setValue(int_val)
        self.target_slider.blockSignals(False)

    # File Browsing
    def browse_input(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select GIF", "", "GIF files (*.gif)")
        if file_path:
            self.entry_input.setText(file_path)
            self.detect_fps_ui()
            # Auto suggest output
            if not self.entry_output.text():
                base, ext = os.path.splitext(file_path)
                self.entry_output.setText(f"{base}_resized{ext}")

    def browse_output(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save GIF", "", "GIF files (*.gif)")
        if file_path:
            if not file_path.lower().endswith(".gif"):
                file_path += ".gif"
            self.entry_output.setText(file_path)

    def update_mode(self):
        self.options_stack.setCurrentIndex(self.mode_combo.currentIndex())

    # Conversion Logic
    def convert_gif(self):
        input_file = self.entry_input.text()
        output_file = self.entry_output.text()
        fps = self.entry_fps.text()

        if not os.path.exists(input_file):
            QMessageBox.critical(self, "Error", "Input file does not exist")
            return
        if not output_file:
            QMessageBox.critical(
                self, "Error", "Please specify an output file")
            return
        if not fps:
            QMessageBox.critical(
                self, "Error", "FPS missing, click 'Detect' or enter manually")
            return

        self.btn_convert.setEnabled(False)
        self.btn_convert.setText("Processing...")
        self.lbl_status.setText("Starting conversion...")
        QApplication.processEvents()

        try:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

            # Logic selection based on index
            mode_index = self.mode_combo.currentIndex()

            if mode_index == 0:  # Resolution
                width = self.entry_width.text()
                height = self.entry_height.text()
                if not width or not height:
                    raise ValueError("Please enter both width and height")
                filter_scale = f"scale={width}:{height}:flags=lanczos"
                self.run_ffmpeg_conversion(
                    input_file, output_file, fps, filter_scale)

            elif mode_index == 1:  # Percentage
                percentage = self.scale_spinbox.value()
                factor = percentage / 100.0
                filter_scale = f"scale=iw*{factor}:ih*{factor}:flags=lanczos"
                self.run_ffmpeg_conversion(
                    input_file, output_file, fps, filter_scale)

            elif mode_index == 2:  # Target Size
                self.lbl_status.setText(
                    "Calculating optimal size (this may take time)...")
                QApplication.processEvents()
                target_mb = self.target_spinbox.value()
                self.run_target_size_logic(
                    input_file, output_file, fps, target_mb)

            QMessageBox.information(
                self, "Success", "GIF processed successfully!")
            self.lbl_status.setText("Done")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred:\n{e}")
            self.lbl_status.setText("Error occurred")
        finally:
            QApplication.restoreOverrideCursor()
            self.btn_convert.setEnabled(True)
            self.btn_convert.setText("Process GIF")

    def run_ffmpeg_conversion(self, input_file, output_file, fps, scale_filter):
        palette_filter = f"fps={fps},{scale_filter},palettegen"
        filter_complex = f"fps={fps},{scale_filter}[x];[x][1:v]paletteuse"

        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            palette_file = tmp.name

        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        try:
            # Pass 1: Palette
            cmd_palette = ["ffmpeg", "-y", "-i", input_file,
                           "-vf", palette_filter, palette_file]
            subprocess.run(cmd_palette, check=True, startupinfo=startupinfo,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Pass 2: GIF
            cmd_gif = ["ffmpeg", "-y", "-i", input_file, "-i",
                       palette_file, "-filter_complex", filter_complex, output_file]
            subprocess.run(cmd_gif, check=True, startupinfo=startupinfo,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        finally:
            if os.path.exists(palette_file):
                os.remove(palette_file)

    def run_target_size_logic(self, input_file, output_file, fps, target_mb):
        low = 0.1
        high = 1.0
        best_scale = 0.1
        tolerance = max(0.05 * target_mb, 0.1)
        iterations = 6

        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        for i in range(iterations):
            mid = (low + high) / 2
            self.lbl_status.setText(f"Optimizing... Pass {i+1}/{iterations}")
            QApplication.processEvents()

            temp_gif = tempfile.NamedTemporaryFile(
                delete=False, suffix=".gif").name
            temp_palette = tempfile.NamedTemporaryFile(
                delete=False, suffix=".png").name

            try:
                scale_filter = f"scale=iw*{mid}:ih*{mid}:flags=lanczos"
                palette_filter_iter = f"fps={fps},{scale_filter},palettegen"
                filter_complex_iter = f"fps={fps},{scale_filter}[x];[x][1:v]paletteuse"

                subprocess.run(["ffmpeg", "-y", "-i", input_file, "-vf", palette_filter_iter, temp_palette],
                               check=True, startupinfo=startupinfo, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                subprocess.run(["ffmpeg", "-y", "-i", input_file, "-i", temp_palette, "-filter_complex", filter_complex_iter, temp_gif],
                               check=True, startupinfo=startupinfo, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                size_mb = os.path.getsize(temp_gif) / (1024 * 1024)

                if abs(size_mb - target_mb) <= tolerance:
                    best_scale = mid
                    break
                elif size_mb > target_mb:
                    high = mid
                else:
                    low = mid
                best_scale = mid
            finally:
                if os.path.exists(temp_palette):
                    os.remove(temp_palette)
                if os.path.exists(temp_gif):
                    os.remove(temp_gif)

        final_scale_filter = f"scale=iw*{best_scale}:ih*{best_scale}:flags=lanczos"
        self.run_ffmpeg_conversion(
            input_file, output_file, fps, final_scale_filter)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GifConverterApp()
    window.show()
    sys.exit(app.exec())
