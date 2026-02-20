import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QGridLayout,
    QPushButton, QLabel, QFrame
)
from PyQt6.QtCore import Qt

try:
    # Tool Imports
    from AddTextToGif import GifTextEditor
    from CompressGif import GifCompressor
    from ConvertMP4toGIF import VideoToGifConverter
    from EditGifFrames import GifEditor
    from ResizeGif import GifConverterApp
    from CropGif import GifCropper
    from CropGifWithKeyframes import GifCropper as KeyframeCropper
    from VideoToFrames import VideoToFramesConverter
    from About import About 
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Ensure all python tool files are in the same folder")


class GifToolsLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gif Tools")
        self.resize(500, 600)

        self.windows = {}
        self.init_ui()

    def init_ui(self):
        # Stylesheet 
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e2e;
            }
            QWidget {
                color: #cdd6f4;
                font-family: 'Segoe UI', 'Helvetica', sans-serif;
                font-size: 14px;
            }
            QLabel#TitleLabel {
                color: #f5c2e7;
                font-size: 26px;
                font-weight: bold;
                margin-bottom: 10px;
            }
            QLabel#SubtitleLabel {
                color: #bac2de;
                font-size: 14px;
                font-style: italic;
                margin-bottom: 20px;
            }
            QPushButton {
                background-color: #313244;
                color: #ffffff;
                border: 1px solid #45475a;
                border-radius: 8px;
                padding: 15px;
                text-align: left;
                font-weight: bold;
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: #45475a;
                border: 1px solid #cba6f7;
            }
            QPushButton:pressed {
                background-color: #585b70;
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main Layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(30, 40, 30, 40)
        main_layout.setSpacing(10)

        # Header Section
        title = QLabel("GIF Tools")
        title.setObjectName("TitleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        subtitle = QLabel("Select a tool to begin")
        subtitle.setObjectName("SubtitleLabel")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(subtitle)

        # Grid Section for Tools
        grid_layout = QGridLayout()
        grid_layout.setSpacing(15)

        # ROW 0
        # Video Converter
        self.btn_convert = self.create_button(
            "🎬  Video ↔ GIF", "Convert between MP4 and GIF", "#f9e2af")
        self.btn_convert.clicked.connect(self.launch_convert)
        grid_layout.addWidget(self.btn_convert, 0, 0)
        
        # Video to Frames
        self.btn_extract = self.create_button(
            "🖼️  MP4 to Frames", "Extract an image sequence", "#fab387")
        self.btn_extract.clicked.connect(self.launch_extract)
        grid_layout.addWidget(self.btn_extract, 0, 1)
        
        # ROW 1
        # Text Editor
        self.btn_text = self.create_button(
            "Tt  Add Text", "Overlay your GIF with text", "#a6e3a1")
        self.btn_text.clicked.connect(self.launch_add_text)
        grid_layout.addWidget(self.btn_text, 1, 0)

        # Frame Editor
        self.btn_edit = self.create_button(
            "🎞️  Edit Frames", "Reorder/Delete Frames", "#89b4fa")
        self.btn_edit.clicked.connect(self.launch_edit_frames)
        grid_layout.addWidget(self.btn_edit, 1, 1)

        # ROW 2
        # Standard Crop
        self.btn_crop = self.create_button(
            "✂️  Crop & Rotate", "Crop & Rotate your GIF", "#cba6f7")
        self.btn_crop.clicked.connect(self.launch_crop)
        grid_layout.addWidget(self.btn_crop, 2, 0)

        # Keyframe Crop
        self.btn_crop_keys = self.create_button(
            "🏃‍♂️  Advanced Crop", "Crop with keyframe motion", "#f5c2e7")
        self.btn_crop_keys.clicked.connect(self.launch_crop_keys)
        grid_layout.addWidget(self.btn_crop_keys, 2, 1)

        # ROW 3
        # Resize
        self.btn_resize = self.create_button(
            "xy  Resize", "Resize your GIF", "#94e2d5")
        self.btn_resize.clicked.connect(self.launch_resize)
        grid_layout.addWidget(self.btn_resize, 3, 0)

        # Compress
        self.btn_compress = self.create_button(
            "📉  Compress", "Reduce file size", "#fab387")
        self.btn_compress.clicked.connect(self.launch_compress)
        grid_layout.addWidget(self.btn_compress, 3, 1)

        # ROW 4
        # About Button
        self.btn_about = self.create_button(
            "ℹ️ About", "App info & version", "#bac2de")
        self.btn_about.clicked.connect(self.launch_about)
        grid_layout.addWidget(self.btn_about, 4, 0)

        # Exit Button (Styled as a card now)
        self.btn_exit = self.create_button(
            "🚪 Exit", "Close Application", "#f38ba8")
        self.btn_exit.clicked.connect(self.close)
        grid_layout.addWidget(self.btn_exit, 4, 1)

        main_layout.addLayout(grid_layout)
        main_layout.addStretch()

    def create_button(self, title, subtext, accent_color):
        btn = QPushButton()
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumHeight(70)

        # Create a layout inside the button for Title Subtitle
        layout = QVBoxLayout(btn)
        layout.setSpacing(2)
        layout.setContentsMargins(10, 5, 10, 5)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(
            f"font-size: 16px; font-weight: bold; color: {accent_color}; background: transparent; border: none;")

        lbl_sub = QLabel(subtext)
        lbl_sub.setStyleSheet(
            "font-size: 11px; color: #a6adc8; background: transparent; border: none;")

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_sub)

        return btn

    # Launchers
    def launch_add_text(self):
        self.windows['text'] = GifTextEditor()
        self.windows['text'].show()

    def launch_compress(self):
        self.windows['compress'] = GifCompressor()
        self.windows['compress'].show()

    def launch_convert(self):
        self.windows['convert'] = VideoToGifConverter()
        self.windows['convert'].show()

    def launch_extract(self):
        self.windows['extract'] = VideoToFramesConverter()
        self.windows['extract'].show()

    def launch_edit_frames(self):
        self.windows['edit'] = GifEditor()
        self.windows['edit'].show()

    def launch_resize(self):
        self.windows['resize'] = GifConverterApp()
        self.windows['resize'].show()

    def launch_crop(self):
        self.windows['crop'] = GifCropper()
        self.windows['crop'].show()

    def launch_crop_keys(self):
        self.windows['crop_keys'] = KeyframeCropper()
        self.windows['crop_keys'].show()

    def launch_about(self):
        self.windows['about'] = About()
        self.windows['about'].show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GifToolsLauncher()
    window.show()
    sys.exit(app.exec())