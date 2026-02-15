import sys
import os
import shutil
import subprocess
from enum import Enum
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QMessageBox, QScrollArea,
    QSpinBox, QGroupBox, QGridLayout, QSlider, QStyle, QFrame,
    QSizePolicy
)
from PyQt6.QtCore import Qt, QRect, QSize, QPoint, pyqtSignal, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QMovie, QIcon, QPalette

# Constants
ACCENT_COLOR = QColor("#cba6f7")  # Bootleg Catppuccin
HANDLE_COLOR = QColor("#ffffff")
OVERLAY_COLOR = QColor(0, 0, 0, 180)  # Darker dim for better focus
HANDLE_SIZE = 12


class EditMode(Enum):
    NONE = 0
    CREATE = 1
    MOVE = 2
    RESIZE = 3


class ResizeSide(Enum):
    NONE = 0
    LEFT = 1
    TOP_LEFT = 2
    TOP = 3
    TOP_RIGHT = 4
    RIGHT = 5
    BOTTOM_RIGHT = 6
    BOTTOM = 7
    BOTTOM_LEFT = 8

# Custom Scroll Area


class ZoomableScrollArea(QScrollArea):
    zoomRequest = pyqtSignal(int)

    def wheelEvent(self, event):
        modifiers = event.modifiers()
        if modifiers == Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta != 0:
                self.zoomRequest.emit(delta)
            event.accept()
        elif modifiers == Qt.KeyboardModifier.ShiftModifier:
            delta = event.angleDelta().y()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta)
            event.accept()
        else:
            super().wheelEvent(event)


class CropLabel(QLabel):
    selectionChanged = pyqtSignal(QRect)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.selection_rect = QRect()
        self.pixmap_ref = None
        self.scale_factor = 1.0

        self.mode = EditMode.NONE
        self.active_handle = ResizeSide.NONE
        self.drag_start_pos = QPoint()
        self.rect_start_geo = QRect()

    def set_pixmap_ref(self, pixmap):
        self.pixmap_ref = pixmap
        self.refresh_display()

    def set_zoom(self, scale_value):
        self.scale_factor = scale_value
        self.refresh_display()

    def refresh_display(self):
        if self.pixmap_ref:
            scaled_w = int(self.pixmap_ref.width() * self.scale_factor)
            scaled_h = int(self.pixmap_ref.height() * self.scale_factor)
            mode = Qt.TransformationMode.FastTransformation if self.scale_factor < 1.0 else Qt.TransformationMode.SmoothTransformation
            scaled_pix = self.pixmap_ref.scaled(
                scaled_w, scaled_h, Qt.AspectRatioMode.KeepAspectRatio, mode)
            self.setPixmap(scaled_pix)
            self.setFixedSize(scaled_pix.size())
            self.update()

    def set_selection(self, x, y, w, h):
        if self.pixmap_ref:
            img_rect = self.pixmap_ref.rect()
            safe_w = max(1, min(w, img_rect.width()))
            safe_h = max(1, min(h, img_rect.height()))
            max_x = img_rect.width() - safe_w
            max_y = img_rect.height() - safe_h
            safe_x = max(0, min(x, max_x))
            safe_y = max(0, min(y, max_y))
            self.selection_rect = QRect(safe_x, safe_y, safe_w, safe_h)
            self.update()
            self.selectionChanged.emit(self.selection_rect)

    def _to_screen(self, rect):
        return QRect(
            int(rect.x() * self.scale_factor),
            int(rect.y() * self.scale_factor),
            int(rect.width() * self.scale_factor),
            int(rect.height() * self.scale_factor)
        )

    def _to_original(self, point):
        return QPoint(
            int(point.x() / self.scale_factor),
            int(point.y() / self.scale_factor)
        )

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.pixmap_ref or self.selection_rect.isNull():
            return

        painter = QPainter(self)
        full_rect = self.rect()
        r_vis = self._to_screen(self.selection_rect)

        # Draw Dimmed Overlay (Crop Mask)
        painter.fillRect(0, 0, full_rect.width(),
                         r_vis.top(), OVERLAY_COLOR)  # Top
        painter.fillRect(0, r_vis.bottom() + 1, full_rect.width(),
                         full_rect.height() - r_vis.bottom(), OVERLAY_COLOR)  # Bottom
        painter.fillRect(0, r_vis.top(), r_vis.left(),
                         r_vis.height(), OVERLAY_COLOR)  # Left
        painter.fillRect(r_vis.right() + 1, r_vis.top(), full_rect.width() -
                         r_vis.right(), r_vis.height(), OVERLAY_COLOR)  # Right

        # Draw Selection Border
        pen = QPen(ACCENT_COLOR)
        pen.setWidth(2)
        pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(r_vis)

        # Draw Handles
        painter.setBrush(QBrush(HANDLE_COLOR))
        painter.setPen(QPen(ACCENT_COLOR, 1))
        handles = self._get_handle_rects(r_vis)
        for handle_rect in handles.values():
            painter.drawRect(handle_rect)

    def mousePressEvent(self, event):
        if not self.pixmap_ref or event.button() != Qt.MouseButton.LeftButton:
            return
        screen_pos = event.pos()
        self.drag_start_pos = screen_pos
        self.rect_start_geo = self.selection_rect
        handle_type = self._hit_test_handles(screen_pos)

        if handle_type != ResizeSide.NONE:
            self.mode = EditMode.RESIZE
            self.active_handle = handle_type
        elif self._to_screen(self.selection_rect).contains(screen_pos):
            self.mode = EditMode.MOVE
            self.setCursor(Qt.CursorShape.SizeAllCursor)
        else:
            self.mode = EditMode.CREATE
            orig_pos = self._to_original(screen_pos)
            self.selection_rect = QRect(orig_pos, QSize())
            self.update()

    def mouseMoveEvent(self, event):
        screen_pos = event.pos()
        orig_pos = self._to_original(screen_pos)
        img_rect = self.pixmap_ref.rect()

        if self.mode == EditMode.NONE:
            self._update_cursor(screen_pos)
            return

        if self.mode == EditMode.CREATE:
            start_orig = self._to_original(self.drag_start_pos)
            rect = QRect(start_orig, orig_pos).normalized()
            self.selection_rect = rect.intersected(img_rect)
        elif self.mode == EditMode.MOVE:
            delta_screen = screen_pos - self.drag_start_pos
            delta_x = int(delta_screen.x() / self.scale_factor)
            delta_y = int(delta_screen.y() / self.scale_factor)
            new_top_left = self.rect_start_geo.topLeft() + QPoint(delta_x, delta_y)
            new_rect = QRect(new_top_left, self.rect_start_geo.size())

            # Boundary checks
            if new_rect.left() < 0:
                new_rect.moveLeft(0)
            if new_rect.top() < 0:
                new_rect.moveTop(0)
            if new_rect.right() > img_rect.right():
                new_rect.moveRight(img_rect.right())
            if new_rect.bottom() > img_rect.bottom():
                new_rect.moveBottom(img_rect.bottom())
            self.selection_rect = new_rect
        elif self.mode == EditMode.RESIZE:
            self._handle_resize(orig_pos)

        self.update()
        self.selectionChanged.emit(self.selection_rect)

    def mouseReleaseEvent(self, event):
        self.mode = EditMode.NONE
        self.active_handle = ResizeSide.NONE
        self._update_cursor(event.pos())
        self.selectionChanged.emit(self.selection_rect)

    def _get_handle_rects(self, r_vis):
        hw = HANDLE_SIZE // 2
        return {
            ResizeSide.TOP_LEFT: QRect(r_vis.left()-hw, r_vis.top()-hw, HANDLE_SIZE, HANDLE_SIZE),
            ResizeSide.TOP: QRect(r_vis.center().x()-hw, r_vis.top()-hw, HANDLE_SIZE, HANDLE_SIZE),
            ResizeSide.TOP_RIGHT: QRect(r_vis.right()-hw, r_vis.top()-hw, HANDLE_SIZE, HANDLE_SIZE),
            ResizeSide.RIGHT: QRect(r_vis.right()-hw, r_vis.center().y()-hw, HANDLE_SIZE, HANDLE_SIZE),
            ResizeSide.BOTTOM_RIGHT: QRect(r_vis.right()-hw, r_vis.bottom()-hw, HANDLE_SIZE, HANDLE_SIZE),
            ResizeSide.BOTTOM: QRect(r_vis.center().x()-hw, r_vis.bottom()-hw, HANDLE_SIZE, HANDLE_SIZE),
            ResizeSide.BOTTOM_LEFT: QRect(r_vis.left()-hw, r_vis.bottom()-hw, HANDLE_SIZE, HANDLE_SIZE),
            ResizeSide.LEFT: QRect(r_vis.left()-hw, r_vis.center().y()-hw, HANDLE_SIZE, HANDLE_SIZE),
        }

    def _hit_test_handles(self, screen_pos):
        if self.selection_rect.isNull():
            return ResizeSide.NONE
        r_vis = self._to_screen(self.selection_rect)
        handles = self._get_handle_rects(r_vis)
        for side, rect in handles.items():
            if rect.adjusted(-5, -5, 5, 5).contains(screen_pos):
                return side
        return ResizeSide.NONE

    def _update_cursor(self, screen_pos):
        handle = self._hit_test_handles(screen_pos)
        cursors = {
            ResizeSide.TOP_LEFT: Qt.CursorShape.SizeFDiagCursor,
            ResizeSide.BOTTOM_RIGHT: Qt.CursorShape.SizeFDiagCursor,
            ResizeSide.TOP_RIGHT: Qt.CursorShape.SizeBDiagCursor,
            ResizeSide.BOTTOM_LEFT: Qt.CursorShape.SizeBDiagCursor,
            ResizeSide.TOP: Qt.CursorShape.SizeVerCursor,
            ResizeSide.BOTTOM: Qt.CursorShape.SizeVerCursor,
            ResizeSide.LEFT: Qt.CursorShape.SizeHorCursor,
            ResizeSide.RIGHT: Qt.CursorShape.SizeHorCursor
        }
        if handle in cursors:
            self.setCursor(cursors[handle])
        elif self._to_screen(self.selection_rect).contains(screen_pos):
            self.setCursor(Qt.CursorShape.SizeAllCursor)
        else:
            self.setCursor(Qt.CursorShape.CrossCursor)

    def _handle_resize(self, orig_pos):
        r = QRect(self.rect_start_geo)
        l, t, r_edge, b = r.left(), r.top(), r.right(), r.bottom()
        img_rect = self.pixmap_ref.rect()
        x = max(0, min(orig_pos.x(), img_rect.right()))
        y = max(0, min(orig_pos.y(), img_rect.bottom()))

        if self.active_handle in (ResizeSide.LEFT, ResizeSide.TOP_LEFT, ResizeSide.BOTTOM_LEFT):
            l = x
        if self.active_handle in (ResizeSide.RIGHT, ResizeSide.TOP_RIGHT, ResizeSide.BOTTOM_RIGHT):
            r_edge = x
        if self.active_handle in (ResizeSide.TOP, ResizeSide.TOP_LEFT, ResizeSide.TOP_RIGHT):
            t = y
        if self.active_handle in (ResizeSide.BOTTOM, ResizeSide.BOTTOM_LEFT, ResizeSide.BOTTOM_RIGHT):
            b = y
        self.selection_rect = QRect(
            QPoint(l, t), QPoint(r_edge, b)).normalized()


class GifCropper(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GIF Cropper")
        self.resize(1280, 850)
        self.input_path = None

        self.movie = None
        self.is_playing = False
        self.updating_spinboxes = False
        self.block_seek_update = False

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
            /* Sidebar Container */
            QFrame#Sidebar {
                background-color: #313244;
                border-left: 1px solid #45475a;
            }
            /* Cards/Groups */
            QGroupBox {
                border: 1px solid #45475a;
                border-radius: 8px;
                margin-top: 20px;
                background-color: #313244;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #cba6f7;
                font-weight: bold;
            }
            /* Buttons */
            QPushButton {
                background-color: #45475a;
                border: none;
                border-radius: 6px;
                padding: 8px;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: #585b70;
            }
            QPushButton:disabled {
                background-color: #313244;
                color: #585b70;
            }
            /* Primary Action Button */
            QPushButton#Primary {
                background-color: #cba6f7;
                color: #1e1e2e;
                font-weight: bold;
                font-size: 16px;
                padding: 12px;
            }
            QPushButton#Primary:hover {
                background-color: #d6bdf9;
            }
            /* Inputs */
            QSpinBox {
                background-color: #181825;
                border: 1px solid #45475a;
                border-radius: 4px;
                padding: 5px;
                color: #cdd6f4;
            }
            QSpinBox:focus {
                border: 1px solid #cba6f7;
            }
            /* Sliders */
            QSlider::groove:horizontal {
                border: 1px solid #45475a;
                height: 6px;
                background: #181825;
                margin: 2px 0;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #89b4fa;
                border: 1px solid #89b4fa;
                width: 14px;
                height: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            /* Scroll Area */
            QScrollArea {
                background-color: #11111b;
                border: none;
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Zoomable Scroll Area
        self.scroll_area = ZoomableScrollArea()
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.zoomRequest.connect(self.on_scroll_zoom)

        self.image_label = CropLabel()
        self.image_label.selectionChanged.connect(
            self.on_visual_selection_changed)

        self.scroll_area.setWidget(self.image_label)
        main_layout.addWidget(self.scroll_area, stretch=1)

        # Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(320)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setSpacing(20)
        sidebar_layout.setContentsMargins(20, 20, 20, 20)

        # Title
        lbl_title = QLabel("GIF Cropper")
        lbl_title.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: #89b4fa; letter-spacing: 2px;")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(lbl_title)

        # File Group
        file_group = QGroupBox("Source")
        file_layout = QVBoxLayout()
        self.btn_open = QPushButton("📂 Open GIF File")
        self.btn_open.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open.clicked.connect(self.open_gif)
        file_layout.addWidget(self.btn_open)

        self.lbl_info = QLabel("No file loaded")
        self.lbl_info.setStyleSheet("color: #a6adc8; font-size: 12px;")
        self.lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        file_layout.addWidget(self.lbl_info)

        file_group.setLayout(file_layout)
        sidebar_layout.addWidget(file_group)

        # Playback Group
        play_group = QGroupBox("Timeline")
        play_layout = QVBoxLayout()

        # Seekbar
        self.seek_slider = QSlider(Qt.Orientation.Horizontal)
        self.seek_slider.setEnabled(False)
        self.seek_slider.sliderPressed.connect(self.on_seek_pressed)
        self.seek_slider.sliderReleased.connect(self.on_seek_released)
        self.seek_slider.valueChanged.connect(self.on_seek_moved)
        play_layout.addWidget(self.seek_slider)

        # Controls Row
        ctrl_layout = QHBoxLayout()
        ctrl_layout.setSpacing(10)

        self.btn_stop = self.create_media_btn(
            QStyle.StandardPixmap.SP_MediaStop)
        self.btn_stop.clicked.connect(self.stop_movie)

        self.btn_play = self.create_media_btn(
            QStyle.StandardPixmap.SP_MediaPlay)
        self.btn_play.clicked.connect(self.play_movie)

        self.btn_pause = self.create_media_btn(
            QStyle.StandardPixmap.SP_MediaPause)
        self.btn_pause.clicked.connect(self.pause_movie)

        ctrl_layout.addStretch()
        ctrl_layout.addWidget(self.btn_stop)
        ctrl_layout.addWidget(self.btn_play)
        ctrl_layout.addWidget(self.btn_pause)
        ctrl_layout.addStretch()

        play_layout.addLayout(ctrl_layout)
        play_group.setLayout(play_layout)
        sidebar_layout.addWidget(play_group)

        # Zoom Group
        zoom_group = QGroupBox("Canvas View")
        zoom_layout = QHBoxLayout()
        zoom_layout.addWidget(QLabel("Zoom:"))
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(10, 400)
        self.zoom_slider.setValue(100)
        self.zoom_slider.valueChanged.connect(self.on_zoom_changed)
        zoom_layout.addWidget(self.zoom_slider)

        self.lbl_zoom = QLabel("100%")
        self.lbl_zoom.setFixedWidth(40)
        self.lbl_zoom.setAlignment(Qt.AlignmentFlag.AlignRight)
        zoom_layout.addWidget(self.lbl_zoom)
        zoom_group.setLayout(zoom_layout)
        sidebar_layout.addWidget(zoom_group)

        # Geometry Group
        geo_group = QGroupBox("Crop Dimensions")
        geo_layout = QGridLayout()
        geo_layout.setVerticalSpacing(10)

        geo_layout.addWidget(QLabel("X:"), 0, 0)
        self.spin_x = self.create_spinbox()
        geo_layout.addWidget(self.spin_x, 0, 1)

        geo_layout.addWidget(QLabel("Y:"), 0, 2)
        self.spin_y = self.create_spinbox()
        geo_layout.addWidget(self.spin_y, 0, 3)

        geo_layout.addWidget(QLabel("W:"), 1, 0)
        self.spin_w = self.create_spinbox()
        geo_layout.addWidget(self.spin_w, 1, 1)

        geo_layout.addWidget(QLabel("H:"), 1, 2)
        self.spin_h = self.create_spinbox()
        geo_layout.addWidget(self.spin_h, 1, 3)

        # Connect signals
        for sb in [self.spin_x, self.spin_y, self.spin_w, self.spin_h]:
            sb.valueChanged.connect(self.on_spinbox_changed)

        geo_group.setLayout(geo_layout)
        sidebar_layout.addWidget(geo_group)

        sidebar_layout.addStretch()

        # Action Button
        self.btn_crop_save = QPushButton("Apply Crop && Save")
        self.btn_crop_save.setObjectName("Primary")
        self.btn_crop_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_crop_save.clicked.connect(self.crop_and_save)
        sidebar_layout.addWidget(self.btn_crop_save)

        main_layout.addWidget(sidebar)

    def create_media_btn(self, icon_standard):
        btn = QPushButton()
        btn.setIcon(self.style().standardIcon(icon_standard))
        btn.setFixedSize(40, 40)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setEnabled(False)
        return btn

    def create_spinbox(self):
        sb = QSpinBox()
        sb.setRange(0, 99999)
        sb.setEnabled(False)
        return sb

    # Logic
    def open_gif(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select GIF", "", "GIF Files (*.gif)")
        if not file_path:
            return

        self.input_path = file_path

        if self.movie:
            self.movie.stop()
            self.movie.deleteLater()

        self.movie = QMovie(file_path)
        self.movie.setCacheMode(QMovie.CacheMode.CacheAll)
        self.movie.isValid()
        self.movie.frameChanged.connect(self.on_frame_changed)

        # Initialize
        self.movie.start()
        self.movie.setPaused(True)
        self.movie.jumpToFrame(0)

        current_pix = self.movie.currentPixmap()
        if current_pix.isNull():
            QMessageBox.critical(self, "Error", "Failed to load image data.")
            return

        self.image_label.set_pixmap_ref(current_pix)

        w, h = current_pix.width(), current_pix.height()
        self.lbl_info.setText(f"{os.path.basename(file_path)}\n{w} x {h} px")

        # Reset UI
        self.zoom_slider.setValue(100)
        for sb in [self.spin_x, self.spin_y, self.spin_w, self.spin_h]:
            sb.setEnabled(True)

        for btn in [self.btn_play, self.btn_pause, self.btn_stop, self.seek_slider, self.btn_crop_save]:
            btn.setEnabled(True)

        self.seek_slider.setRange(0, self.movie.frameCount() - 1)
        self.seek_slider.setValue(0)

        # Reset selection
        self.updating_spinboxes = True
        self.spin_x.setValue(0)
        self.spin_y.setValue(0)
        self.spin_w.setValue(0)
        self.spin_h.setValue(0)
        self.image_label.selection_rect = QRect()
        self.image_label.update()
        self.updating_spinboxes = False

    def play_movie(self):
        if self.movie:
            self.movie.setPaused(False)

    def pause_movie(self):
        if self.movie:
            self.movie.setPaused(True)

    def stop_movie(self):
        if self.movie:
            self.movie.jumpToFrame(0)
            self.movie.setPaused(True)

    def on_frame_changed(self, frame_number):
        pix = self.movie.currentPixmap()
        self.image_label.set_pixmap_ref(pix)
        if not self.block_seek_update:
            self.seek_slider.setValue(frame_number)

    def on_seek_pressed(self):
        self.block_seek_update = True
        self.pause_movie()

    def on_seek_released(self):
        self.block_seek_update = False

    def on_seek_moved(self, value):
        if self.movie and self.block_seek_update:
            self.movie.jumpToFrame(value)

    def on_zoom_changed(self, value):
        scale = value / 100.0
        self.lbl_zoom.setText(f"{value}%")
        self.image_label.set_zoom(scale)

    def on_scroll_zoom(self, delta):
        val = self.zoom_slider.value()
        step = 10 if delta > 0 else -10
        self.zoom_slider.setValue(max(10, min(400, val + step)))

    def on_visual_selection_changed(self, rect):
        if self.updating_spinboxes:
            return
        self.updating_spinboxes = True
        self.spin_x.setValue(rect.x())
        self.spin_y.setValue(rect.y())
        self.spin_w.setValue(rect.width())
        self.spin_h.setValue(rect.height())
        self.updating_spinboxes = False

    def on_spinbox_changed(self):
        if self.updating_spinboxes:
            return
        self.image_label.set_selection(
            self.spin_x.value(), self.spin_y.value(),
            self.spin_w.value(), self.spin_h.value()
        )
        # Re-sync to handle boundary clamping in label
        final = self.image_label.selection_rect
        self.updating_spinboxes = True
        self.spin_x.setValue(final.x())
        self.spin_y.setValue(final.y())
        self.spin_w.setValue(final.width())
        self.spin_h.setValue(final.height())
        self.updating_spinboxes = False

    def crop_and_save(self):
        if not self.input_path:
            return
        rect = self.image_label.selection_rect
        if rect.isEmpty():
            QMessageBox.warning(self, "Action Required",
                                "Please draw a crop box on the image first")
            return

        # Check ffmpeg
        if not shutil.which("ffmpeg"):
            QMessageBox.critical(
                self, "System Error", "FFmpeg was not found in your system PATH, \nplease install FFmpeg to use this feature")
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save Cropped GIF", "", "GIF Files (*.gif)")
        if not save_path:
            return
        if not save_path.lower().endswith(".gif"):
            save_path += ".gif"

        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()

        # Palette generation filter
        filter_complex = f"crop={w}:{h}:{x}:{y},split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse"

        cmd = [
            "ffmpeg", "-y",
            "-i", self.input_path,
            "-filter_complex", filter_complex,
            save_path
        ]

        self.btn_crop_save.setText("Processing...")
        self.btn_crop_save.setEnabled(False)
        QApplication.processEvents()

        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL,
                           stderr=subprocess.PIPE, startupinfo=startupinfo)
            QMessageBox.information(
                self, "Success", f"GIF Cropped successfully!\nSaved to: {save_path}")
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(
                self, "FFmpeg Error", f"Conversion failed:\n{e.stderr.decode() if e.stderr else 'Unknown error'}")
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"An unexpected error occurred:\n{e}")
        finally:
            self.btn_crop_save.setText("Apply Crop && Save")
            self.btn_crop_save.setEnabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GifCropper()
    window.show()
    sys.exit(app.exec())
