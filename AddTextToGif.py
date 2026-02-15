import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QComboBox, QSpinBox, QCheckBox,
    QColorDialog, QFileDialog, QMessageBox, QFrame, QScrollArea, QSizePolicy,
    QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QPixmap, QImage, QCursor, QColor
from PIL import Image, ImageDraw, ImageFont, ImageSequence

# Custom Widget for Handling Mouse Events


class InteractiveLabel(QLabel):
    """Emits signals for mouse events to handle dragging"""
    mousePressed = pyqtSignal(QPoint)
    mouseMoved = pyqtSignal(QPoint)
    mouseReleased = pyqtSignal(QPoint)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(False)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.mousePressed.emit(event.pos())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.mouseMoved.emit(event.pos())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.mouseReleased.emit(event.pos())
        super().mouseReleaseEvent(event)


class GifTextEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GIF Text Adder")
        self.resize(1100, 700)

        # State Variables
        self.gif_image = None
        self.frames = []
        self.duration = 100

        self.text_x = 50
        self.text_y = 50

        self.font_color = "#FFFFFF"
        self.shadow_color = "#000000"
        self.stroke_color = "#000000"

        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.dragging = False
        self.current_text_bounds = (0, 0, 0, 0)

        self.init_ui()

    def init_ui(self):
        # Stylesheet
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e2e; }
            QWidget { color: #cdd6f4; font-family: 'Segoe UI', sans-serif; font-size: 14px; }
            
            /* Sidebar */
            QFrame#Sidebar { background-color: #313244; border-right: 1px solid #45475a; }
            
            /* GroupBox */
            QGroupBox { 
                border: 1px solid #45475a; border-radius: 6px; 
                margin-top: 20px; font-weight: bold; color: #89b4fa; 
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            QGroupBox::indicator { width: 14px; height: 14px; }
            
            /* Inputs */
            QLineEdit, QComboBox, QSpinBox {
                background-color: #181825; border: 1px solid #45475a;
                border-radius: 4px; padding: 5px; color: #cdd6f4;
            }
            
            /* Buttons */
            QPushButton {
                background-color: #45475a; border: none; border-radius: 4px;
                padding: 8px; color: white;
            }
            QPushButton:hover { background-color: #585b70; }
            
            QPushButton#PrimaryBtn {
                background-color: #cba6f7; color: #1e1e2e; font-weight: bold;
                font-size: 15px; padding: 12px;
            }
            QPushButton#PrimaryBtn:hover { background-color: #d6bdf9; }
            
            /* Color Swatch Button */
            QPushButton#ColorBtn {
                border: 1px solid #6c7086;
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(340)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 20, 20, 20)
        sidebar_layout.setSpacing(15)

        # File Section
        self.load_btn = QPushButton("📂 Open GIF")
        self.load_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.load_btn.clicked.connect(self.load_gif)
        sidebar_layout.addWidget(self.load_btn)

        # Text Content
        grp_text = QGroupBox("Tt Text Content")
        form_text = QFormLayout()

        self.text_entry = QLineEdit("Your Text Here")
        self.text_entry.textChanged.connect(self.update_preview)
        form_text.addRow("Caption:", self.text_entry)

        self.font_combo = QComboBox()
        self.font_combo.addItems(
            ["Arial", "Times New Roman", "Courier New", "Verdana", "Impact"])
        self.font_combo.currentTextChanged.connect(self.update_preview)
        form_text.addRow("Font:", self.font_combo)

        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(10, 300)
        self.font_size_spin.setValue(40)
        self.font_size_spin.valueChanged.connect(self.update_preview)
        form_text.addRow("Size:", self.font_size_spin)

        self.color_btn = QPushButton()
        self.color_btn.setObjectName("ColorBtn")
        self.update_color_button(self.color_btn, self.font_color)
        self.color_btn.clicked.connect(self.choose_font_color)
        form_text.addRow("Color:", self.color_btn)

        self.width_spin = QSpinBox()
        self.width_spin.setRange(50, 2000)
        self.width_spin.setValue(400)
        self.width_spin.setSuffix(" px")
        self.width_spin.valueChanged.connect(self.update_preview)
        form_text.addRow("Max Width:", self.width_spin)

        grp_text.setLayout(form_text)
        sidebar_layout.addWidget(grp_text)

        # Styling (Shadow)
        self.grp_shadow = QGroupBox("Drop Shadow")
        self.grp_shadow.setCheckable(True)
        self.grp_shadow.setChecked(False)
        self.grp_shadow.toggled.connect(self.update_preview)

        form_shadow = QFormLayout()
        self.shadow_size_spin = QSpinBox()
        self.shadow_size_spin.setRange(1, 50)
        self.shadow_size_spin.setValue(3)
        self.shadow_size_spin.valueChanged.connect(self.update_preview)
        form_shadow.addRow("Offset:", self.shadow_size_spin)

        self.shadow_color_btn = QPushButton()
        self.shadow_color_btn.setObjectName("ColorBtn")
        self.update_color_button(self.shadow_color_btn, self.shadow_color)
        self.shadow_color_btn.clicked.connect(self.choose_shadow_color)
        form_shadow.addRow("Color:", self.shadow_color_btn)

        self.grp_shadow.setLayout(form_shadow)
        sidebar_layout.addWidget(self.grp_shadow)

        # Styling (Stroke)
        self.grp_stroke = QGroupBox("Outline / Stroke")
        self.grp_stroke.setCheckable(True)
        self.grp_stroke.setChecked(False)
        self.grp_stroke.toggled.connect(self.update_preview)

        form_stroke = QFormLayout()
        self.stroke_size_spin = QSpinBox()
        self.stroke_size_spin.setRange(1, 20)
        self.stroke_size_spin.setValue(2)
        self.stroke_size_spin.valueChanged.connect(self.update_preview)
        form_stroke.addRow("Thickness:", self.stroke_size_spin)

        self.stroke_color_btn = QPushButton()
        self.stroke_color_btn.setObjectName("ColorBtn")
        self.update_color_button(self.stroke_color_btn, self.stroke_color)
        self.stroke_color_btn.clicked.connect(self.choose_stroke_color)
        form_stroke.addRow("Color:", self.stroke_color_btn)

        self.grp_stroke.setLayout(form_stroke)
        sidebar_layout.addWidget(self.grp_stroke)

        sidebar_layout.addStretch()

        # Export
        self.export_btn = QPushButton("Export GIF")
        self.export_btn.setObjectName("PrimaryBtn")
        self.export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_btn.clicked.connect(self.export_gif)
        sidebar_layout.addWidget(self.export_btn)

        main_layout.addWidget(sidebar)

        # Right Preview Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setStyleSheet(
            "background-color: #11111b; border: none;")

        self.image_label = InteractiveLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.image_label.setStyleSheet("border: 2px dashed #45475a;")

        self.image_label.mousePressed.connect(self.on_mouse_down)
        self.image_label.mouseMoved.connect(self.on_mouse_drag)
        self.image_label.mouseReleased.connect(self.on_mouse_up)

        self.scroll_area.setWidget(self.image_label)
        main_layout.addWidget(self.scroll_area)

    # Helpers

    def update_color_button(self, btn, hex_color):
        # Calculate contrasting text color (black or white) for readability if we were to add text
        btn.setStyleSheet(
            f"background-color: {hex_color}; border: 1px solid #6c7086; border-radius: 4px;")

    def pil2pixmap(self, im):
        if im is None:
            return QPixmap()
        im = im.convert("RGBA")
        data = im.tobytes("raw", "RGBA")
        qim = QImage(data, im.width, im.height, QImage.Format.Format_RGBA8888)
        return QPixmap.fromImage(qim)

    def get_font(self, size):
        font_name = self.font_combo.currentText()
        # Mapping common names to file names
        # TODO: Use QFontDatabase or smth
        font_map = {
            "Arial": "arial.ttf",
            "Times New Roman": "times.ttf",
            "Courier New": "cour.ttf",
            "Verdana": "verdana.ttf",
            "Impact": "impact.ttf"
        }

        filename = font_map.get(font_name, "arial.ttf")
        try:
            return ImageFont.truetype(filename, size)
        except OSError:
            # Fallback to default if TTF not found
            try:
                return ImageFont.load_default()
            except:
                return None

    def wrap_text(self, text, font, max_width):
        if not font:
            return text
        draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
        lines = []
        for paragraph in text.split('\n'):
            line = []
            for word in paragraph.split():
                # Check width of current line + word
                test_line = ' '.join(line + [word])
                bbox = draw.textbbox((0, 0), test_line, font=font)
                if (bbox[2] - bbox[0]) <= max_width:
                    line.append(word)
                else:
                    if line:
                        lines.append(' '.join(line))
                    line = [word]
            if line:
                lines.append(' '.join(line))
        return '\n'.join(lines)

    def get_multiline_text_size(self, text, font):
        draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
        try:
            bbox = draw.multiline_textbbox((0, 0), text, font=font)
            return (bbox[2] - bbox[0], bbox[3] - bbox[1])
        except AttributeError:
            return (0, 0)

    # Logic
    def load_gif(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open GIF", "", "GIF Files (*.gif)")
        if not file_name:
            return

        try:
            self.gif_image = Image.open(file_name)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Cannot open GIF: {e}")
            return

        self.frames = []
        try:
            for frame in ImageSequence.Iterator(self.gif_image):
                self.frames.append(frame.copy().convert("RGBA"))
            self.duration = self.gif_image.info.get("duration", 100)
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Error processing frames: {e}")
            return

        self.text_x, self.text_y = self.frames[0].width // 4, self.frames[0].height // 2
        self.update_preview()

    def update_preview(self):
        if not self.frames:
            return

        preview = self.frames[0].copy()
        draw = ImageDraw.Draw(preview)

        font_size = self.font_size_spin.value()
        font = self.get_font(font_size)
        textbox_width = self.width_spin.value()
        text = self.text_entry.text()

        wrapped_text = self.wrap_text(text, font, textbox_width)

        # Bounds for clicking
        text_w, text_h = self.get_multiline_text_size(wrapped_text, font)
        self.current_text_bounds = (
            self.text_x, self.text_y,
            self.text_x + text_w, self.text_y + text_h
        )

        # Draw Shadow
        if self.grp_shadow.isChecked():
            offset = self.shadow_size_spin.value()
            draw.multiline_text((self.text_x + offset, self.text_y + offset),
                                wrapped_text, font=font, fill=self.shadow_color)

        # Draw Text/Stroke
        if self.grp_stroke.isChecked():
            draw.multiline_text((self.text_x, self.text_y), wrapped_text, font=font,
                                fill=self.font_color, stroke_width=self.stroke_size_spin.value(), stroke_fill=self.stroke_color)
        else:
            draw.multiline_text((self.text_x, self.text_y),
                                wrapped_text, font=font, fill=self.font_color)

        pixmap = self.pil2pixmap(preview)
        self.image_label.setPixmap(pixmap)
        self.image_label.setFixedSize(pixmap.size())

    # Mouse Events
    def on_mouse_down(self, pos):
        x, y = pos.x(), pos.y()
        x0, y0, x1, y1 = self.current_text_bounds
        # Simple bounding box check
        if x0 <= x <= x1 and y0 <= y <= y1:
            self.dragging = True
            self.drag_offset_x = x - self.text_x
            self.drag_offset_y = y - self.text_y
            self.image_label.setCursor(
                QCursor(Qt.CursorShape.ClosedHandCursor))

    def on_mouse_drag(self, pos):
        if self.dragging:
            self.text_x = pos.x() - self.drag_offset_x
            self.text_y = pos.y() - self.drag_offset_y
            self.update_preview()

    def on_mouse_up(self, pos):
        self.dragging = False
        self.image_label.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    # Color Pickers
    def choose_font_color(self):
        c = QColorDialog.getColor(QColor(self.font_color))
        if c.isValid():
            self.font_color = c.name()
            self.update_color_button(self.color_btn, self.font_color)
            self.update_preview()

    def choose_shadow_color(self):
        c = QColorDialog.getColor(QColor(self.shadow_color))
        if c.isValid():
            self.shadow_color = c.name()
            self.update_color_button(self.shadow_color_btn, self.shadow_color)
            self.update_preview()

    def choose_stroke_color(self):
        c = QColorDialog.getColor(QColor(self.stroke_color))
        if c.isValid():
            self.stroke_color = c.name()
            self.update_color_button(self.stroke_color_btn, self.stroke_color)
            self.update_preview()

    def export_gif(self):
        if not self.frames:
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save GIF", "", "GIF Files (*.gif)")
        if not file_path:
            return
        if not file_path.lower().endswith(".gif"):
            file_path += ".gif"

        new_frames = []
        font = self.get_font(self.font_size_spin.value())
        text = self.wrap_text(self.text_entry.text(),
                              font, self.width_spin.value())

        self.export_btn.setText("Processing...")
        self.export_btn.setEnabled(False)
        QApplication.processEvents()

        try:
            for frame in self.frames:
                f = frame.copy().convert("RGBA")
                d = ImageDraw.Draw(f)

                # Shadow
                if self.grp_shadow.isChecked():
                    off = self.shadow_size_spin.value()
                    d.multiline_text(
                        (self.text_x + off, self.text_y + off), text, font=font, fill=self.shadow_color)

                # Main
                if self.grp_stroke.isChecked():
                    d.multiline_text((self.text_x, self.text_y), text, font=font, fill=self.font_color,
                                     stroke_width=self.stroke_size_spin.value(), stroke_fill=self.stroke_color)
                else:
                    d.multiline_text((self.text_x, self.text_y),
                                     text, font=font, fill=self.font_color)

                new_frames.append(f)

            new_frames[0].save(file_path, save_all=True, append_images=new_frames[1:],
                               duration=self.duration, loop=0, disposal=2)
            QMessageBox.information(self, "Success", f"Saved to {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        finally:
            self.export_btn.setText("Export GIF")
            self.export_btn.setEnabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GifTextEditor()
    window.show()
    sys.exit(app.exec())
