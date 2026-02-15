import sys
import os
import shutil
import math
import re
from enum import Enum
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QMessageBox, QScrollArea,
    QSpinBox, QGroupBox, QFormLayout, QSlider, QStyle, QComboBox,
    QFrame, QStyleOptionSlider, QGridLayout, QProgressDialog
)
from PyQt6.QtCore import Qt, QRect, QSize, QPoint, QPointF, pyqtSignal, QRectF, QProcess
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QMovie, QPolygon, 
    QFont, QPalette, QAction, QKeySequence, QShortcut
)

# Constants
HANDLE_SIZE = 12
BORDER_COLOR = QColor("#cba6f7")    # Bootleg Catpuccin
HANDLE_COLOR = QColor("#ffffff") 
OVERLAY_COLOR = QColor(0, 0, 0, 180)  
KEYFRAME_COLOR = QColor("#f38ba8")  # Astolfo for keyframes on timeline

# Stylesheet
DARK_STYLESHEET = """
    QMainWindow, QWidget {
        background-color: #1e1e2e;
        color: #cdd6f4;
        font-family: 'Segoe UI', sans-serif;
        font-size: 14px;
    }
    QGroupBox {
        border: 1px solid #45475a;
        border-radius: 6px;
        margin-top: 22px;
        font-weight: bold;
        color: #89b4fa;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 5px;
        left: 10px;
    }
    QPushButton {
        background-color: #313244;
        border: 1px solid #45475a;
        border-radius: 4px;
        padding: 6px 12px;
        color: #fff;
    }
    QPushButton:hover {
        background-color: #45475a;
        border-color: #585b70;
    }
    QPushButton:pressed {
        background-color: #cba6f7;
        color: #1e1e2e;
    }
    QPushButton:disabled {
        background-color: #2a2a2a;
        color: #555;
        border-color: #333;
    }
    QPushButton#PrimaryBtn {
        background-color: #cba6f7;
        color: #1e1e2e;
        font-weight: bold;
        font-size: 14px;
    }
    QPushButton#PrimaryBtn:hover {
        background-color: #d6bdf9;
    }
    QPushButton#LockBtn {
        font-weight: bold;
    }
    QPushButton#LockBtn:checked {
        background-color: #f38ba8; /* Astolfo when locked */
        color: #1e1e2e;
        border-color: #f38ba8;
    }
    QSpinBox, QComboBox {
        background-color: #181825;
        border: 1px solid #45475a;
        border-radius: 4px;
        padding: 5px;
        color: #cdd6f4;
    }
    QSpinBox::up-button, QSpinBox::down-button {
        background-color: #313244;
        border: none;
        width: 16px;
    }
    QLabel#InfoPanel {
        background-color: #181825;
        border: 1px solid #45475a;
        border-radius: 4px;
        padding: 10px;
        color: #a6adc8;
        font-family: Consolas, monospace;
        font-size: 12px;
    }
    QFrame#BottomBar {
        background-color: #11111b;
        border-top: 1px solid #45475a;
    }
    QScrollBar:horizontal, QScrollBar:vertical {
        background: #1e1e2e;
        border-radius: 4px;
    }
    QScrollBar::handle {
        background: #45475a;
        border-radius: 4px;
    }
"""

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

class InterpolationType(Enum):
    LINEAR = "Linear"
    EASE_IN = "Ease In (Quad)"
    EASE_OUT = "Ease Out (Quad)"
    BEZIER = "Smoothstep (Bezier)"

# Slider for Timeline
class KeyframeSlider(QSlider):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.keyframes = set()

    def set_keyframes(self, frames):
        self.keyframes = set(frames)
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.keyframes or self.maximum() <= 0: return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(KEYFRAME_COLOR))
        painter.setPen(Qt.PenStyle.NoPen)

        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        style = self.style()
        groove = style.subControlRect(QStyle.ComplexControl.CC_Slider, opt, QStyle.SubControl.SC_SliderGroove, self)
        handle = style.subControlRect(QStyle.ComplexControl.CC_Slider, opt, QStyle.SubControl.SC_SliderHandle, self)

        slider_len = groove.width() - handle.width()
        start_x = groove.x() + handle.width() / 2

        for frame in self.keyframes:
            ratio = frame / self.maximum()
            pos_x = start_x + (ratio * slider_len)
            center_y = groove.center().y()
            size = 5
            # Draw Diamond Marker
            painter.drawPolygon(QPolygon([
                QPoint(int(pos_x), int(center_y - size)),
                QPoint(int(pos_x + size), int(center_y)),
                QPoint(int(pos_x), int(center_y + size)),
                QPoint(int(pos_x - size), int(center_y))
            ]))

# Custom Scroll Area
class ZoomableScrollArea(QScrollArea):
    zoomRequest = pyqtSignal(int)

    def wheelEvent(self, event):
        modifiers = event.modifiers()
        if modifiers == Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta != 0: self.zoomRequest.emit(delta)
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
        self.selection_rect = QRectF() 
        self.pixmap_ref = None          
        self.scale_factor = 1.0
        self.mode = EditMode.NONE
        self.active_handle = ResizeSide.NONE
        self.drag_start_pos = QPoint()      
        self.rect_start_geo = QRectF() 
        
        # Locking Constraints
        self.aspect_locked = False
        self.target_aspect_ratio = 1.0 # Width / Height

    def set_pixmap_ref(self, pixmap):
        self.pixmap_ref = pixmap
        self.refresh_display()

    def set_zoom(self, scale_value):
        self.scale_factor = scale_value
        self.refresh_display()
        
    def set_lock_aspect(self, locked, ratio=1.0):
        self.aspect_locked = locked
        self.target_aspect_ratio = ratio
        if locked and not self.selection_rect.isEmpty():
            # Snap current rect to aspect ratio immediately
            current_w = self.selection_rect.width()
            new_h = current_w / ratio
            if self.selection_rect.top() + new_h > self.pixmap_ref.height():
                new_h = self.pixmap_ref.height() - self.selection_rect.top()
                current_w = new_h * ratio
                
            self.selection_rect.setWidth(current_w)
            self.selection_rect.setHeight(new_h)
            self.update()
            self.selectionChanged.emit(self.selection_rect.toRect())

    def refresh_display(self):
        if self.pixmap_ref:
            scaled_w = int(self.pixmap_ref.width() * self.scale_factor)
            scaled_h = int(self.pixmap_ref.height() * self.scale_factor)
            mode = Qt.TransformationMode.FastTransformation if self.scale_factor < 1.0 else Qt.TransformationMode.SmoothTransformation
            scaled_pix = self.pixmap_ref.scaled(scaled_w, scaled_h, Qt.AspectRatioMode.KeepAspectRatio, mode)
            self.setPixmap(scaled_pix)
            self.setFixedSize(scaled_pix.size())
            self.update()

    def set_selection(self, x, y, w, h):
        if self.pixmap_ref:
            img_rect = self.pixmap_ref.rect()
            safe_w = max(1.0, min(float(w), float(img_rect.width())))
            safe_h = max(1.0, min(float(h), float(img_rect.height())))
            
            if self.aspect_locked:
                safe_h = safe_w / self.target_aspect_ratio
                
            safe_x = max(0.0, min(float(x), float(img_rect.width()) - safe_w))
            safe_y = max(0.0, min(float(y), float(img_rect.height()) - safe_h))

            self.selection_rect = QRectF(safe_x, safe_y, safe_w, safe_h)
            self.update()
            self.selectionChanged.emit(self.selection_rect.toRect())

    def _to_screen(self, rect_f):
        return QRect(
            int(rect_f.x() * self.scale_factor),
            int(rect_f.y() * self.scale_factor),
            int(rect_f.width() * self.scale_factor),
            int(rect_f.height() * self.scale_factor)
        )

    def _to_original(self, point):
        return QPoint(int(point.x() / self.scale_factor), int(point.y() / self.scale_factor))

    def paintEvent(self, event):
        super().paintEvent(event) 
        if not self.pixmap_ref: return
        painter = QPainter(self)
        if not self.selection_rect.isNull():
            full_rect = self.rect()
            r_vis = self._to_screen(self.selection_rect)
            
            # Draw Overlay
            painter.fillRect(0, 0, full_rect.width(), r_vis.top(), OVERLAY_COLOR)
            painter.fillRect(0, r_vis.bottom() + 1, full_rect.width(), full_rect.height() - r_vis.bottom(), OVERLAY_COLOR)
            painter.fillRect(0, r_vis.top(), r_vis.left(), r_vis.height(), OVERLAY_COLOR)
            painter.fillRect(r_vis.right() + 1, r_vis.top(), full_rect.width() - r_vis.right(), r_vis.height(), OVERLAY_COLOR)
            
            # Draw Border
            pen = QPen(BORDER_COLOR); pen.setWidth(2)
            painter.setPen(pen); painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(r_vis)
            
            # Draw Handles
            painter.setBrush(QBrush(HANDLE_COLOR)); painter.setPen(QPen(BORDER_COLOR))
            handles = self._get_handle_rects(r_vis)
            for handle_rect in handles.values(): painter.drawRect(handle_rect)

    def mousePressEvent(self, event):
        if not self.pixmap_ref or event.button() != Qt.MouseButton.LeftButton: return
        screen_pos = event.pos()
        self.drag_start_pos = screen_pos
        self.rect_start_geo = self.selection_rect 
        handle_type = self._hit_test_handles(screen_pos)
        
        if handle_type != ResizeSide.NONE:
            self.mode = EditMode.RESIZE; self.active_handle = handle_type
        elif self._to_screen(self.selection_rect).contains(screen_pos):
            self.mode = EditMode.MOVE; self.setCursor(Qt.CursorShape.SizeAllCursor)
        else:
            self.mode = EditMode.CREATE
            orig_pos = self._to_original(screen_pos)
            self.selection_rect = QRectF(float(orig_pos.x()), float(orig_pos.y()), 0.0, 0.0)
            self.update()

    def mouseMoveEvent(self, event):
        screen_pos = event.pos()
        orig_pos = self._to_original(screen_pos) 
        img_rect = self.pixmap_ref.rect()
        
        if self.mode == EditMode.NONE:
            self._update_cursor(screen_pos); return

        if self.mode == EditMode.CREATE:
            start_orig = self._to_original(self.drag_start_pos)
            w = orig_pos.x() - start_orig.x()
            h = orig_pos.y() - start_orig.y()
            
            if self.aspect_locked:
                if abs(w) > 1: h = w / self.target_aspect_ratio
            
            rect = QRectF(float(start_orig.x()), float(start_orig.y()), float(w), float(h)).normalized()
            self.selection_rect = rect.intersected(QRectF(img_rect))
        
        elif self.mode == EditMode.MOVE:
            delta_screen = screen_pos - self.drag_start_pos
            delta_x = delta_screen.x() / self.scale_factor
            delta_y = delta_screen.y() / self.scale_factor
            
            new_top_left = self.rect_start_geo.topLeft() + QPointF(delta_x, delta_y)
            new_rect = QRectF(new_top_left, self.rect_start_geo.size())
            
            if new_rect.left() < 0: new_rect.moveLeft(0)
            if new_rect.top() < 0: new_rect.moveTop(0)
            if new_rect.right() > img_rect.right(): new_rect.moveRight(img_rect.right())
            if new_rect.bottom() > img_rect.bottom(): new_rect.moveBottom(img_rect.bottom())
            
            self.selection_rect = new_rect

        elif self.mode == EditMode.RESIZE:
            self._handle_resize(orig_pos)

        self.update()
        self.selectionChanged.emit(self.selection_rect.toRect())

    def mouseReleaseEvent(self, event):
        self.mode = EditMode.NONE; self.active_handle = ResizeSide.NONE
        self._update_cursor(event.pos())
        self.selectionChanged.emit(self.selection_rect.toRect())

    def _get_handle_rects(self, r_vis):
        hw = HANDLE_SIZE // 2
        rects = {
            ResizeSide.TOP_LEFT: QRect(r_vis.left()-hw, r_vis.top()-hw, HANDLE_SIZE, HANDLE_SIZE),
            ResizeSide.TOP_RIGHT: QRect(r_vis.right()-hw, r_vis.top()-hw, HANDLE_SIZE, HANDLE_SIZE),
            ResizeSide.BOTTOM_RIGHT: QRect(r_vis.right()-hw, r_vis.bottom()-hw, HANDLE_SIZE, HANDLE_SIZE),
            ResizeSide.BOTTOM_LEFT: QRect(r_vis.left()-hw, r_vis.bottom()-hw, HANDLE_SIZE, HANDLE_SIZE),
        }
        if not self.aspect_locked:
            rects.update({
                ResizeSide.TOP: QRect(r_vis.center().x()-hw, r_vis.top()-hw, HANDLE_SIZE, HANDLE_SIZE),
                ResizeSide.RIGHT: QRect(r_vis.right()-hw, r_vis.center().y()-hw, HANDLE_SIZE, HANDLE_SIZE),
                ResizeSide.BOTTOM: QRect(r_vis.center().x()-hw, r_vis.bottom()-hw, HANDLE_SIZE, HANDLE_SIZE),
                ResizeSide.LEFT: QRect(r_vis.left()-hw, r_vis.center().y()-hw, HANDLE_SIZE, HANDLE_SIZE),
            })
        return rects

    def _hit_test_handles(self, screen_pos):
        if self.selection_rect.isNull(): return ResizeSide.NONE
        r_vis = self._to_screen(self.selection_rect)
        handles = self._get_handle_rects(r_vis)
        for side, rect in handles.items():
            if rect.adjusted(-5,-5,5,5).contains(screen_pos): return side
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
        r = self.rect_start_geo
        left, top, right, bottom = r.left(), r.top(), r.right(), r.bottom()
        img_rect = self.pixmap_ref.rect()
        
        x = max(0, min(orig_pos.x(), img_rect.right()))
        y = max(0, min(orig_pos.y(), img_rect.bottom()))

        if not self.aspect_locked:
            if self.active_handle in (ResizeSide.LEFT, ResizeSide.TOP_LEFT, ResizeSide.BOTTOM_LEFT): left = x
            if self.active_handle in (ResizeSide.RIGHT, ResizeSide.TOP_RIGHT, ResizeSide.BOTTOM_RIGHT): right = x
            if self.active_handle in (ResizeSide.TOP, ResizeSide.TOP_LEFT, ResizeSide.TOP_RIGHT): top = y
            if self.active_handle in (ResizeSide.BOTTOM, ResizeSide.BOTTOM_LEFT, ResizeSide.BOTTOM_RIGHT): bottom = y
        else:
            if self.active_handle == ResizeSide.BOTTOM_RIGHT:
                w_new = x - left
                h_new = w_new / self.target_aspect_ratio
                right = x; bottom = top + h_new
            elif self.active_handle == ResizeSide.BOTTOM_LEFT:
                w_new = right - x
                h_new = w_new / self.target_aspect_ratio
                left = x; bottom = top + h_new
            elif self.active_handle == ResizeSide.TOP_LEFT:
                w_new = right - x
                h_new = w_new / self.target_aspect_ratio
                left = x; top = bottom - h_new
            elif self.active_handle == ResizeSide.TOP_RIGHT:
                w_new = x - left
                h_new = w_new / self.target_aspect_ratio
                right = x; top = bottom - h_new

        self.selection_rect = QRectF(QPointF(left, top), QPointF(right, bottom)).normalized()

class GifCropper(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GIF Cropper With Keyframes")
        self.resize(1280, 950)
        self.input_path = None
        self.setStyleSheet(DARK_STYLESHEET)
        
        self.movie = None
        self.is_playing = False
        self.updating_spinboxes = False
        self.block_seek_update = False 
        self.project_locked = False
        self.target_w = 0
        self.target_h = 0
        
        self.keyframes = {} # { frame_index: QRectF }
        self.current_frame = 0

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top Area 
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(10, 10, 10, 0)

        # Viewer
        self.scroll_area = ZoomableScrollArea()
        self.scroll_area.setWidgetResizable(False) 
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setStyleSheet("background-color: #11111b; border: none;")
        self.scroll_area.zoomRequest.connect(self.on_scroll_zoom)

        self.image_label = CropLabel()
        self.image_label.selectionChanged.connect(self.on_visual_selection_changed)
        self.scroll_area.setWidget(self.image_label)
        top_layout.addWidget(self.scroll_area, stretch=1)

        # Sidebar
        sidebar = QWidget()
        sidebar.setFixedWidth(340)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setSpacing(12)

        # Top Buttons
        top_btns_layout = QHBoxLayout()
        self.btn_open = QPushButton("📂 Open GIF")
        self.btn_open.clicked.connect(self.open_gif)
        self.btn_open.setMinimumHeight(40)
        self.btn_help = QPushButton("?")
        self.btn_help.setFixedSize(40, 40)
        self.btn_help.clicked.connect(self.show_hotkeys)
        top_btns_layout.addWidget(self.btn_open)
        top_btns_layout.addWidget(self.btn_help)
        sidebar_layout.addLayout(top_btns_layout)
        
        # Project Settings (Resolution Lock)
        proj_group = QGroupBox("Output Resolution (Lock First)")
        proj_layout = QGridLayout()
        
        self.spin_out_w = QSpinBox()
        self.spin_out_w.setRange(1, 9999); self.spin_out_w.setValue(400); self.spin_out_w.setSuffix(" px")
        self.spin_out_h = QSpinBox()
        self.spin_out_h.setRange(1, 9999); self.spin_out_h.setValue(400); self.spin_out_h.setSuffix(" px")
        
        self.btn_lock = QPushButton("🔒 Lock Output Size")
        self.btn_lock.setCheckable(True)
        self.btn_lock.setObjectName("LockBtn")
        self.btn_lock.clicked.connect(self.toggle_project_lock)
        
        proj_layout.addWidget(QLabel("Width:"), 0, 0)
        proj_layout.addWidget(self.spin_out_w, 0, 1)
        proj_layout.addWidget(QLabel("Height:"), 0, 2)
        proj_layout.addWidget(self.spin_out_h, 0, 3)
        proj_layout.addWidget(self.btn_lock, 1, 0, 1, 4)
        proj_group.setLayout(proj_layout)
        sidebar_layout.addWidget(proj_group)

        # Keyframes
        kf_group = QGroupBox("Keyframe Manager")
        kf_layout = QVBoxLayout()
        kf_layout.setSpacing(10)
        
        kf_btn_grid = QGridLayout()
        self.btn_prev_kf = QPushButton("◀"); self.btn_prev_kf.clicked.connect(self.jump_prev_kf)
        self.btn_next_kf = QPushButton("▶"); self.btn_next_kf.clicked.connect(self.jump_next_kf)
        self.btn_add_kf = QPushButton("➕ Add Keyframe"); self.btn_add_kf.clicked.connect(self.add_keyframe)
        self.btn_rem_kf = QPushButton("🗑️ Del Keyframe"); self.btn_rem_kf.clicked.connect(self.remove_keyframe)
        kf_btn_grid.addWidget(self.btn_prev_kf, 0, 0)
        kf_btn_grid.addWidget(self.btn_add_kf, 0, 1)
        kf_btn_grid.addWidget(self.btn_rem_kf, 0, 2)
        kf_btn_grid.addWidget(self.btn_next_kf, 0, 3)
        kf_layout.addLayout(kf_btn_grid)

        self.lbl_kf_status = QLabel("No keyframes")
        self.lbl_kf_status.setObjectName("InfoPanel")
        self.lbl_kf_status.setWordWrap(True)
        kf_layout.addWidget(self.lbl_kf_status)

        kf_layout.addWidget(QLabel("Interpolation Shape:"))
        self.combo_interp = QComboBox()
        for t in InterpolationType: self.combo_interp.addItem(t.value, t)
        self.combo_interp.currentIndexChanged.connect(self.on_interp_changed)
        kf_layout.addWidget(self.combo_interp)
        kf_group.setLayout(kf_layout)
        sidebar_layout.addWidget(kf_group)

        # Coordinates
        coord_group = QGroupBox("Current Crop Data")
        form_layout = QFormLayout()
        self.spin_x = self.create_spinbox(); self.spin_x.valueChanged.connect(self.on_spinbox_changed)
        self.spin_y = self.create_spinbox(); self.spin_y.valueChanged.connect(self.on_spinbox_changed)
        self.spin_w = self.create_spinbox(); self.spin_w.valueChanged.connect(self.on_spinbox_changed)
        self.spin_h = self.create_spinbox(); self.spin_h.valueChanged.connect(self.on_spinbox_changed)
        form_layout.addRow("X:", self.spin_x); form_layout.addRow("Y:", self.spin_y)
        form_layout.addRow("W:", self.spin_w); form_layout.addRow("H:", self.spin_h)
        coord_group.setLayout(form_layout)
        sidebar_layout.addWidget(coord_group)

        # Save
        self.btn_crop_save = QPushButton("Export Animated GIF")
        self.btn_crop_save.setObjectName("PrimaryBtn")
        self.btn_crop_save.clicked.connect(self.crop_and_save)
        self.btn_crop_save.setMinimumHeight(45)
        sidebar_layout.addWidget(self.btn_crop_save)
        
        # Zoom Controls
        zoom_layout = QHBoxLayout()
        self.lbl_zoom = QLabel("100%")
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(10, 400); self.zoom_slider.setValue(100)
        self.zoom_slider.valueChanged.connect(self.on_zoom_changed)
        self.btn_reset_zoom = QPushButton("R"); self.btn_reset_zoom.setFixedWidth(30)
        self.btn_reset_zoom.clicked.connect(lambda: self.zoom_slider.setValue(100))
        zoom_layout.addWidget(QLabel("Zoom:"))
        zoom_layout.addWidget(self.zoom_slider)
        zoom_layout.addWidget(self.lbl_zoom)
        zoom_layout.addWidget(self.btn_reset_zoom)
        sidebar_layout.addLayout(zoom_layout)

        sidebar_layout.addStretch()
        top_layout.addWidget(sidebar)
        main_layout.addWidget(top_widget)

        # Bottom Player
        bottom_frame = QFrame()
        bottom_frame.setObjectName("BottomBar")
        bottom_layout = QVBoxLayout(bottom_frame)
        self.seek_slider = KeyframeSlider(Qt.Orientation.Horizontal)
        self.seek_slider.setEnabled(False)
        self.seek_slider.sliderPressed.connect(self.on_seek_pressed)
        self.seek_slider.sliderReleased.connect(self.on_seek_released)
        self.seek_slider.valueChanged.connect(self.on_seek_moved)
        bottom_layout.addWidget(self.seek_slider)

        ctrl_layout = QHBoxLayout()
        ctrl_layout.addStretch()
        self.btn_stop = QPushButton(); self.btn_stop.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop)); self.btn_stop.clicked.connect(self.stop_movie)
        self.btn_play = QPushButton(); self.btn_play.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)); self.btn_play.clicked.connect(self.play_movie)
        self.btn_pause = QPushButton(); self.btn_pause.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause)); self.btn_pause.clicked.connect(self.pause_movie)
        for btn in [self.btn_stop, self.btn_play, self.btn_pause]:
            btn.setFixedSize(40, 40); btn.setEnabled(False); ctrl_layout.addWidget(btn)
        ctrl_layout.addStretch()
        bottom_layout.addLayout(ctrl_layout)
        main_layout.addWidget(bottom_frame)
        
        self.setup_shortcuts()

    def setup_shortcuts(self):
            QShortcut(QKeySequence(Qt.Key.Key_Space), self, self.toggle_playback)
            QShortcut(QKeySequence(Qt.Key.Key_Left), self, self.step_prev_frame)
            QShortcut(QKeySequence(Qt.Key.Key_Right), self, self.step_next_frame)
            QShortcut(QKeySequence("Shift+Left"), self, self.jump_prev_kf)
            QShortcut(QKeySequence("Shift+Right"), self, self.jump_next_kf)
            QShortcut(QKeySequence("Ctrl+Left"), self, self.go_to_start)
            QShortcut(QKeySequence("Ctrl+Right"), self, self.go_to_end)

    # Logic Handler Methods
    def toggle_playback(self):
        if not self.movie or not self.input_path: return
        if self.movie.state() == QMovie.MovieState.Running: self.pause_movie()
        else: self.play_movie()

    def step_prev_frame(self):
        if not self.movie or not self.input_path: return
        new_frame = max(0, self.current_frame - 1)
        self.movie.jumpToFrame(new_frame)
        self.pause_movie()

    def step_next_frame(self):
        if not self.movie or not self.input_path: return
        new_frame = min(self.movie.frameCount() - 1, self.current_frame + 1)
        self.movie.jumpToFrame(new_frame)
        self.pause_movie()

    def go_to_start(self):
        if not self.movie: return
        self.movie.jumpToFrame(0); self.pause_movie()

    def go_to_end(self):
        if not self.movie: return
        self.movie.jumpToFrame(self.movie.frameCount() - 1); self.pause_movie()

    def show_hotkeys(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Keyboard Shortcuts")
        msg.setText(
            "<b>Controls:</b><br>Space: Play / Pause<br>Left / Right: Prev / Next Frame<br><br>"
            "<b>Navigation:</b><br>Shift + Left / Right: Jump to Prev / Next Keyframe<br>Ctrl + Left / Right: Jump to Start / End"
        )
        msg.exec()

    def create_spinbox(self):
        sb = QSpinBox()
        sb.setRange(0, 99999); sb.setEnabled(False)
        return sb

    def open_gif(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select GIF", "", "GIF Files (*.gif)")
        if not file_path: return
        self.input_path = file_path
        if self.movie: self.movie.stop(); self.movie.deleteLater()
        
        self.movie = QMovie(file_path)
        self.movie.setCacheMode(QMovie.CacheMode.CacheAll)
        self.movie.isValid()
        self.movie.frameChanged.connect(self.on_frame_changed)
        self.movie.start(); self.movie.setPaused(True); self.movie.jumpToFrame(0)
        
        current_pix = self.movie.currentPixmap()
        if current_pix.isNull(): return
        self.image_label.set_pixmap_ref(current_pix)
        
        for btn in [self.btn_play, self.btn_pause, self.btn_stop, self.seek_slider]: btn.setEnabled(True)
        self.seek_slider.setRange(0, self.movie.frameCount() - 1); self.seek_slider.setValue(0)
        self.keyframes = {}; self.seek_slider.set_keyframes([]); self.update_kf_status()
        
        # Auto set resolution to current image size
        self.spin_out_w.setValue(current_pix.width())
        self.spin_out_h.setValue(current_pix.height())
        self.unlock_project()

    def toggle_project_lock(self, checked):
        if checked:
            self.lock_project()
        else:
            if self.keyframes:
                reply = QMessageBox.warning(
                    self, "Unlock Project?",
                    "Unlocking the resolution will DELETE all existing keyframes\n\nDo you want to continue?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    self.btn_lock.blockSignals(True)
                    self.btn_lock.setChecked(True)
                    self.btn_lock.blockSignals(False)
                    return
                self.keyframes.clear()
                self.seek_slider.set_keyframes([])
                self.update_kf_status()
            self.unlock_project()

    def lock_project(self):
        self.project_locked = True
        self.target_w = self.spin_out_w.value()
        self.target_h = self.spin_out_h.value()
        ratio = self.target_w / self.target_h
        self.image_label.set_lock_aspect(True, ratio)
        self.btn_lock.setText("🔓 Unlock Output Size")
        self.spin_out_w.setEnabled(False)
        self.spin_out_h.setEnabled(False)
        if self.image_label.selection_rect.isEmpty():
            self.image_label.set_selection(0, 0, self.target_w, self.target_h)

    def unlock_project(self):
        self.project_locked = False
        self.image_label.set_lock_aspect(False)
        self.btn_lock.setChecked(False)
        self.btn_lock.setText("🔒 Lock Output Size")
        self.spin_out_w.setEnabled(True)
        self.spin_out_h.setEnabled(True)

    def add_keyframe(self):
        if not self.input_path: return
        if not self.project_locked:
            QMessageBox.warning(self, "Info", "Please set Output Resolution and LOCK the project first")
            return

        rect = self.image_label.selection_rect
        if rect.isEmpty():
            QMessageBox.warning(self, "Error", "Select a crop area first")
            return
        
        self.keyframes[self.current_frame] = rect
        self.seek_slider.set_keyframes(self.keyframes.keys())
        self.update_kf_status()
        self.refresh_current_frame()

    def remove_keyframe(self):
        if self.current_frame in self.keyframes:
            del self.keyframes[self.current_frame]
            self.seek_slider.set_keyframes(self.keyframes.keys())
            self.update_kf_status()
            self.refresh_current_frame()

    def jump_prev_kf(self):
        if not self.keyframes: return
        sorted_frames = sorted(self.keyframes.keys())
        prev_f = next((f for f in reversed(sorted_frames) if f < self.current_frame), None)
        if prev_f is not None:
             self.movie.jumpToFrame(prev_f)
             self.pause_movie()
        elif sorted_frames:
             self.movie.jumpToFrame(sorted_frames[-1])
             self.pause_movie()

    def jump_next_kf(self):
        if not self.keyframes: return
        sorted_frames = sorted(self.keyframes.keys())
        next_f = next((f for f in sorted_frames if f > self.current_frame), None)
        if next_f is not None:
             self.movie.jumpToFrame(next_f)
             self.pause_movie()
        elif sorted_frames:
             self.movie.jumpToFrame(sorted_frames[0])
             self.pause_movie()

    def update_kf_status(self):
        total = len(self.keyframes)
        interp_name = self.combo_interp.currentText()
        
        if total == 0:
            self.lbl_kf_status.setText(f"No keyframes added.\nMode: {interp_name}")
            self.lbl_kf_status.setStyleSheet("QLabel#InfoPanel { border-left: 3px solid #888; }")
            return

        sorted_frames = sorted(self.keyframes.keys())
        
        if self.current_frame in self.keyframes:
            idx = sorted_frames.index(self.current_frame) + 1
            rect = self.keyframes[self.current_frame]
            info = (f"KEYFRAME {idx} / {total}\nFrame: {self.current_frame}\n"
                    f"Crop: {int(rect.width())}x{int(rect.height())} @ ({int(rect.x())}, {int(rect.y())})\n"
                    f"Output: {self.target_w}x{self.target_h}")
            self.lbl_kf_status.setText(info)
            self.lbl_kf_status.setStyleSheet("QLabel#InfoPanel { border-left: 3px solid #a6e3a1; }") 
        else:
            prev_f = next((f for f in reversed(sorted_frames) if f < self.current_frame), None)
            next_f = next((f for f in sorted_frames if f > self.current_frame), None)
            
            status = "Interpolating..."
            color = "#fab387" 
            if prev_f is None: status = "Holding (Start)"; color="#888"
            elif next_f is None: status = "Holding (End)"; color="#888"
                
            self.lbl_kf_status.setText(f"{status}\nFrame: {self.current_frame}\nMode: {interp_name}")
            self.lbl_kf_status.setStyleSheet(f"QLabel#InfoPanel {{ border-left: 3px solid {color}; }}")

    def on_interp_changed(self):
        self.refresh_current_frame()
        self.update_kf_status()

    def get_interpolated_rect(self, frame):
        if not self.keyframes: return self.image_label.selection_rect
        if frame in self.keyframes: return self.keyframes[frame]

        sorted_frames = sorted(self.keyframes.keys())
        if frame < sorted_frames[0]: return self.keyframes[sorted_frames[0]]
        if frame > sorted_frames[-1]: return self.keyframes[sorted_frames[-1]]

        prev_f = next(f for f in reversed(sorted_frames) if f < frame)
        next_f = next(f for f in sorted_frames if f > frame)
        
        rect_start = self.keyframes[prev_f]
        rect_end = self.keyframes[next_f]

        t = (frame - prev_f) / (next_f - prev_f)
        
        interp = self.combo_interp.currentData()
        if interp == InterpolationType.EASE_IN: t = t * t
        elif interp == InterpolationType.EASE_OUT: t = t * (2 - t)
        elif interp == InterpolationType.BEZIER: t = t * t * (3 - 2 * t)

        x = rect_start.x() + (rect_end.x() - rect_start.x()) * t
        y = rect_start.y() + (rect_end.y() - rect_start.y()) * t
        w = rect_start.width() + (rect_end.width() - rect_start.width()) * t
        h = rect_start.height() + (rect_end.height() - rect_start.height()) * t
        return QRectF(x, y, w, h)

    def refresh_current_frame(self):
        rect = self.get_interpolated_rect(self.current_frame)
        self.updating_spinboxes = True
        self.image_label.set_selection(rect.x(), rect.y(), rect.width(), rect.height())
        self.spin_x.setValue(int(rect.x())); self.spin_y.setValue(int(rect.y()))
        self.spin_w.setValue(int(rect.width())); self.spin_h.setValue(int(rect.height()))
        self.updating_spinboxes = False

    def play_movie(self):
        if self.movie: self.movie.setPaused(False)
    def pause_movie(self):
        if self.movie: self.movie.setPaused(True)
    def stop_movie(self):
        if self.movie: self.movie.jumpToFrame(0); self.movie.setPaused(True)

    def on_frame_changed(self, frame_number):
        self.current_frame = frame_number
        if self.movie: self.image_label.set_pixmap_ref(self.movie.currentPixmap())
        if not self.block_seek_update: self.seek_slider.setValue(frame_number)
        if self.image_label.mode == EditMode.NONE: self.refresh_current_frame()
        self.update_kf_status()

    def on_seek_pressed(self): self.block_seek_update = True; self.pause_movie()
    def on_seek_released(self): self.block_seek_update = False
    def on_seek_moved(self, value):
        if self.movie and self.block_seek_update:
            self.movie.jumpToFrame(value); self.current_frame = value; self.update_kf_status()

    def on_zoom_changed(self, value):
        self.lbl_zoom.setText(f"{value}%"); self.image_label.set_zoom(value / 100.0)
    def on_scroll_zoom(self, delta):
        self.zoom_slider.setValue(max(10, min(400, self.zoom_slider.value() + (10 if delta > 0 else -10))))

    def on_spinbox_changed(self):
        if self.updating_spinboxes: return
        self.image_label.set_selection(self.spin_x.value(), self.spin_y.value(), self.spin_w.value(), self.spin_h.value())

    def on_visual_selection_changed(self, rect):
        if self.updating_spinboxes: return
        self.updating_spinboxes = True
        self.spin_x.setValue(rect.x()); self.spin_y.setValue(rect.y())
        self.spin_w.setValue(rect.width()); self.spin_h.setValue(rect.height())
        self.updating_spinboxes = False

    def crop_and_save(self):
        if not self.input_path: return
        if not self.project_locked:
            QMessageBox.warning(self, "Locked State Required", "Please LOCK the output resolution first")
            return
        if not self.keyframes:
            QMessageBox.warning(self, "Keyframes Required", "Add at least one keyframe")
            return
        if not shutil.which("ffmpeg"):
            QMessageBox.critical(self, "Error", "FFmpeg not found")
            return

        save_path, _ = QFileDialog.getSaveFileName(self, "Save GIF", "", "GIF Files (*.gif)")
        if not save_path: return
        if not save_path.lower().endswith(".gif"): save_path += ".gif"

        # Prepare Filter Strings
        sorted_keys = sorted(self.keyframes.keys())
        total_frames = self.movie.frameCount()
        
        def f(val): return f"{val:.2f}"
        interp = self.combo_interp.currentData()
        t_expr = "((n-START_F)/((END_F-START_F)*1.0))"
        
        if interp == InterpolationType.LINEAR: anim_t = t_expr
        elif interp == InterpolationType.EASE_IN: anim_t = f"pow({t_expr},2)"
        elif interp == InterpolationType.EASE_OUT: anim_t = f"({t_expr} * (2 - {t_expr}))"
        elif interp == InterpolationType.BEZIER: anim_t = f"({t_expr}*{t_expr}*(3-2*{t_expr}))"

        final_x, final_y, final_w, final_h = [], [], [], []
        
        k0 = sorted_keys[0]
        r0 = self.keyframes[k0]
        final_x.append(f"if(lt(n,{k0}),{f(r0.x())},")
        final_y.append(f"if(lt(n,{k0}),{f(r0.y())},")
        final_w.append(f"if(lt(n,{k0}),{f(r0.width())},")
        final_h.append(f"if(lt(n,{k0}),{f(r0.height())},")

        for i in range(len(sorted_keys) - 1):
            start_f = sorted_keys[i]
            end_f = sorted_keys[i+1]
            r_start = self.keyframes[start_f]
            r_end = self.keyframes[end_f]
            seg_t = anim_t.replace("START_F", str(start_f)).replace("END_F", str(end_f))
            
            lx = f"({f(r_start.x())}+({f(r_end.x()-r_start.x())})*{seg_t})"
            ly = f"({f(r_start.y())}+({f(r_end.y()-r_start.y())})*{seg_t})"
            lw = f"({f(r_start.width())}+({f(r_end.width()-r_start.width())})*{seg_t})"
            lh = f"({f(r_start.height())}+({f(r_end.height()-r_start.height())})*{seg_t})"

            final_x.append(f"if(lt(n,{end_f}),{lx},")
            final_y.append(f"if(lt(n,{end_f}),{ly},")
            final_w.append(f"if(lt(n,{end_f}),{lw},")
            final_h.append(f"if(lt(n,{end_f}),{lh},")

        r_last = self.keyframes[sorted_keys[-1]]
        final_x.append(f"{f(r_last.x())}")
        final_y.append(f"{f(r_last.y())}")
        final_w.append(f"{f(r_last.width())}")
        final_h.append(f"{f(r_last.height())}")
        
        parens = ")" * (len(sorted_keys))
        str_x = "".join(final_x) + parens
        str_y = "".join(final_y) + parens
        str_w = "".join(final_w) + parens
        str_h = "".join(final_h) + parens

        tgt_w = self.target_w
        tgt_h = self.target_h
        scale_x_expr = f"({tgt_w}*1.0/({str_w}))"
        scale_y_expr = f"({tgt_h}*1.0/({str_h}))"
        new_w_expr = f"iw*{scale_x_expr}"
        new_h_expr = f"ih*{scale_y_expr}"
        new_crop_x = f"({str_x})*{scale_x_expr}"
        new_crop_y = f"({str_y})*{scale_y_expr}"

        filter_str = (
            f"scale=w='{new_w_expr}':h='{new_h_expr}':eval=frame:flags=lanczos,"
            f"crop=w={tgt_w}:h={tgt_h}:x='{new_crop_x}':y='{new_crop_y}':exact=1,"
            f"split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse"
        )

        self.process = QProcess()
        self.progress_dlg = QProgressDialog("Rendering...", "Cancel", 0, total_frames, self)
        self.progress_dlg.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dlg.setMinimumDuration(0)
        
        self.process.readyReadStandardError.connect(self.handle_render_progress)
        self.process.finished.connect(lambda: self.handle_render_finished(save_path))
        self.progress_dlg.canceled.connect(self.process.kill)

        cmd = ["ffmpeg", "-y", "-i", self.input_path, "-filter_complex", filter_str, save_path]
        
        self.process.start(cmd[0], cmd[1:])

    def handle_render_progress(self):
        stderr = self.process.readAllStandardError().data().decode()
        match = re.search(r"frame=\s*(\d+)", stderr)
        if match:
            frame = int(match.group(1))
            self.progress_dlg.setValue(frame)

    def handle_render_finished(self, save_path):
        self.progress_dlg.close()
        if self.process.exitStatus() == QProcess.ExitStatus.NormalExit and self.process.exitCode() == 0:
             QMessageBox.information(self, "Success", f"Export Complete!\nSaved to: {save_path}")
        else:
             if self.progress_dlg.wasCanceled():
                 QMessageBox.information(self, "Cancelled", "Export cancelled by user")
             else:
                 QMessageBox.critical(self, "FFmpeg Error", "Failed to export, check console or log")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GifCropper()
    window.show()
    sys.exit(app.exec())