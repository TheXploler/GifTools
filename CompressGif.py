import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox, QSlider, QSpinBox,
    QFileDialog, QMessageBox, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QFont

# Try to import pygifsicle, handle error if missing
try:
    from pygifsicle import gifsicle
except ImportError:
    gifsicle = None


class GifCompressor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GIF Compressor")
        self.resize(600, 450)

        # Check for dependency
        if gifsicle is None:
            QMessageBox.critical(
                self, "Missing Dependency", "Please install 'pygifsicle' to use this tool.\npip install pygifsicle")

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
            /* Frames (Cards) */
            QFrame#Card {
                background-color: #313244;
                border-radius: 10px;
                border: 1px solid #45475a;
            }
            /* Inputs */
            QLineEdit {
                background-color: #181825;
                border: 1px solid #45475a;
                border-radius: 5px;
                padding: 8px;
                color: #cdd6f4;
            }
            QLineEdit:focus {
                border: 1px solid #89b4fa;
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
                background-color: #fab387; /* Peach/Orange accent */
                color: #1e1e2e;
                font-size: 15px;
                padding: 12px;
            }
            QPushButton#PrimaryBtn:hover {
                background-color: #f9c096;
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
                background: #fab387;
                border: 1px solid #fab387;
                width: 18px;
                height: 18px;
                margin: -7px 0;
                border-radius: 9px;
            }
            /* Checkbox */
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                background-color: #181825;
                border: 1px solid #45475a;
                border-radius: 4px;
            }
            QCheckBox::indicator:checked {
                background-color: #fab387;
                image: url(check.png); /* Optional: uses default tick if image missing */
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # Header
        header_lbl = QLabel("GIF Optimizer & Compressor")
        header_lbl.setStyleSheet(
            "font-size: 22px; font-weight: bold; color: #fab387;")
        main_layout.addWidget(header_lbl)

        # File Selection
        file_frame = QFrame()
        file_frame.setObjectName("Card")
        file_layout = QGridLayout(file_frame)
        file_layout.setContentsMargins(20, 20, 20, 20)
        file_layout.setSpacing(15)

        # Input
        file_layout.addWidget(QLabel("Input Source:"), 0, 0)
        self.entry_input = QLineEdit()
        self.entry_input.setPlaceholderText("Select a .gif file...")
        file_layout.addWidget(self.entry_input, 0, 1)

        self.btn_browse_input = QPushButton("📂 Browse")
        self.btn_browse_input.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_browse_input.clicked.connect(self.browse_input)
        file_layout.addWidget(self.btn_browse_input, 0, 2)

        # Output
        file_layout.addWidget(QLabel("Destination:"), 1, 0)
        self.entry_output = QLineEdit()
        self.entry_output.setPlaceholderText("Save as...")
        file_layout.addWidget(self.entry_output, 1, 1)

        self.btn_browse_output = QPushButton("📂 Browse")
        self.btn_browse_output.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_browse_output.clicked.connect(self.browse_output)
        file_layout.addWidget(self.btn_browse_output, 1, 2)

        main_layout.addWidget(file_frame)

        # Compression Options
        opt_frame = QFrame()
        opt_frame.setObjectName("Card")
        opt_layout = QVBoxLayout(opt_frame)
        opt_layout.setContentsMargins(20, 20, 20, 20)
        opt_layout.setSpacing(15)

        # Color Reduction
        self.chk_color = QCheckBox("Reduce Color Palette")
        self.chk_color.setToolTip(
            "Reduces the number of unique colors. Fewer colors = smaller file")
        self.chk_color.stateChanged.connect(self.toggle_color_options)
        opt_layout.addWidget(self.chk_color)

        self.container_color = QWidget()
        color_sub_layout = QHBoxLayout(self.container_color)
        color_sub_layout.setContentsMargins(25, 0, 0, 0)  # Indent

        lbl_colors = QLabel("Colors:")
        lbl_colors.setFixedWidth(60)
        self.slider_color = QSlider(Qt.Orientation.Horizontal)
        self.slider_color.setRange(2, 256)
        self.slider_color.setValue(256)

        self.spin_color = QSpinBox()
        self.spin_color.setRange(2, 256)
        self.spin_color.setValue(256)
        self.spin_color.setStyleSheet(
            "background-color: #181825; color: #fff; padding: 5px;")

        self.slider_color.valueChanged.connect(self.spin_color.setValue)
        self.spin_color.valueChanged.connect(self.slider_color.setValue)

        color_sub_layout.addWidget(lbl_colors)
        color_sub_layout.addWidget(self.slider_color)
        color_sub_layout.addWidget(self.spin_color)

        opt_layout.addWidget(self.container_color)
        self.container_color.setVisible(False)  # Hide initially

        # Separator line inside options
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Plain)
        line.setStyleSheet("background-color: #45475a;")
        opt_layout.addWidget(line)

        # Lossy Compression
        self.chk_lossy = QCheckBox("Apply Lossy Compression")
        self.chk_lossy.setToolTip(
            "Significantly reduces file size with minor visual artifacts")
        self.chk_lossy.stateChanged.connect(self.toggle_lossy_options)
        opt_layout.addWidget(self.chk_lossy)

        self.container_lossy = QWidget()
        lossy_sub_layout = QHBoxLayout(self.container_lossy)
        lossy_sub_layout.setContentsMargins(25, 0, 0, 0)  # Indent

        lbl_lossy = QLabel("Intensity:")
        lbl_lossy.setFixedWidth(60)
        self.slider_lossy = QSlider(Qt.Orientation.Horizontal)
        self.slider_lossy.setRange(10, 200)  # Extended range slightly
        self.slider_lossy.setValue(30)

        self.spin_lossy = QSpinBox()
        self.spin_lossy.setRange(10, 200)
        self.spin_lossy.setValue(30)
        self.spin_lossy.setStyleSheet(
            "background-color: #181825; color: #fff; padding: 5px;")

        self.slider_lossy.valueChanged.connect(self.spin_lossy.setValue)
        self.spin_lossy.valueChanged.connect(self.slider_lossy.setValue)

        lossy_sub_layout.addWidget(lbl_lossy)
        lossy_sub_layout.addWidget(self.slider_lossy)
        lossy_sub_layout.addWidget(self.spin_lossy)

        opt_layout.addWidget(self.container_lossy)
        self.container_lossy.setVisible(False)

        main_layout.addWidget(opt_frame)

        # Action
        main_layout.addStretch()

        self.btn_compress = QPushButton("Start Compression")
        self.btn_compress.setObjectName("PrimaryBtn")
        self.btn_compress.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_compress.clicked.connect(self.compress_gif)
        main_layout.addWidget(self.btn_compress)

        # Status Label
        self.lbl_status = QLabel("Ready")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet("color: #6c7086; font-size: 12px;")
        main_layout.addWidget(self.lbl_status)

    # Logic
    def browse_input(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Input GIF", "", "GIF Files (*.gif)")
        if file_path:
            self.entry_input.setText(file_path)
            # Auto-suggest output name
            if not self.entry_output.text():
                base, ext = os.path.splitext(file_path)
                self.entry_output.setText(f"{base}_compressed{ext}")

    def browse_output(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Select Output GIF", "", "GIF Files (*.gif)")
        if file_path:
            if not file_path.lower().endswith(".gif"):
                file_path += ".gif"
            self.entry_output.setText(file_path)

    def toggle_color_options(self):
        self.container_color.setVisible(self.chk_color.isChecked())

    def toggle_lossy_options(self):
        self.container_lossy.setVisible(self.chk_lossy.isChecked())

    def compress_gif(self):
        # Validation
        input_file = self.entry_input.text()
        output_file = self.entry_output.text()

        if not input_file or not os.path.exists(input_file):
            QMessageBox.critical(
                self, "File Error", "Input file not found.\nPlease select a valid GIF")
            return
        if not output_file:
            QMessageBox.critical(
                self, "File Error", "Please specify where to save the output file")
            return

        # Update UI
        self.lbl_status.setText("Compressing... Please wait")
        self.btn_compress.setEnabled(False)
        self.btn_compress.setText("Processing...")
        QApplication.processEvents()  # Force UI update

        # Prepare Options
        options = {
            'sources': [input_file],
            'destination': output_file,
            'optimize': True,  # Basic optimization always on
        }

        if self.chk_color.isChecked():
            options['colors'] = self.spin_color.value()

        if self.chk_lossy.isChecked():
            # Pass as list of strings for pygifsicle
            options['options'] = [f'--lossy={self.spin_lossy.value()}']

        # Execute
        try:
            if gifsicle:
                gifsicle(**options)

                # Check if file was actually created/modified
                if os.path.exists(output_file):
                    # Calculate savings
                    orig_size = os.path.getsize(input_file) / 1024
                    new_size = os.path.getsize(output_file) / 1024
                    saving = ((orig_size - new_size) / orig_size) * 100

                    msg = (f"Compression Successful!\n\n"
                           f"Original: {orig_size:.1f} KB\n"
                           f"New: {new_size:.1f} KB\n"
                           f"Saved: {saving:.1f}%")
                    QMessageBox.information(self, "Done", msg)
                    self.lbl_status.setText(f"Saved {saving:.1f}%")
                else:
                    raise Exception("Output file was not created")
            else:
                QMessageBox.critical(
                    self, "Error", "pygifsicle library is not loaded")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred:\n{e}")
            self.lbl_status.setText("Error occurred")

        finally:
            self.btn_compress.setEnabled(True)
            self.btn_compress.setText("Start Compression")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GifCompressor()
    window.show()
    sys.exit(app.exec())
