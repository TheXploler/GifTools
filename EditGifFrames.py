import sys
import os
import shutil
import subprocess
import tempfile
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QListWidget, QListWidgetItem,
    QFileDialog, QMessageBox, QLabel, QFrame, QAbstractItemView,
    QStyle, QDoubleSpinBox, QGroupBox, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap, QColor, QAction

class GifEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GIF Frame Sequencer")
        self.resize(1000, 750)

        # State
        self.temp_dir = None
        
        self.init_ui()

    def init_ui(self):
        # --- Stylesheet ---
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e2e;
            }
            QWidget {
                color: #cdd6f4;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
            }
            /* Sidebar */
            QFrame#Sidebar {
                background-color: #313244;
                border-left: 1px solid #45475a;
            }
            /* Groups */
            QGroupBox {
                border: 1px solid #45475a;
                border-radius: 6px;
                margin-top: 22px;
                font-weight: bold;
                color: #89b4fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            /* List Widget (The Filmstrip) */
            QListWidget {
                background-color: #181825;
                border: none;
                outline: none;
            }
            QListWidget::item {
                background-color: #313244;
                color: #cdd6f4;
                border-radius: 8px;
                margin: 4px 10px; /* Spacing between rows */
                padding: 10px;
                border: 1px solid #45475a;
            }
            QListWidget::item:selected {
                background-color: #45475a;
                border: 1px solid #cba6f7; /* Accent border */
            }
            QListWidget::item:hover {
                background-color: #3b3e4f;
            }
            /* Buttons */
            QPushButton {
                background-color: #45475a;
                border: none;
                border-radius: 6px;
                padding: 8px;
                color: #ffffff;
                text-align: left;
                padding-left: 15px;
            }
            QPushButton:hover {
                background-color: #585b70;
            }
            QPushButton#PrimaryBtn {
                background-color: #cba6f7;
                color: #1e1e2e;
                font-weight: bold;
                text-align: center;
                font-size: 15px;
                padding: 12px;
            }
            QPushButton#PrimaryBtn:hover {
                background-color: #d6bdf9;
            }
            QPushButton#DestructiveBtn {
                background-color: #313244;
                border: 1px solid #f38ba8;
                color: #f38ba8;
            }
            QPushButton#DestructiveBtn:hover {
                background-color: #f38ba8;
                color: #1e1e2e;
            }
            /* SpinBox */
            QDoubleSpinBox {
                background-color: #181825;
                border: 1px solid #45475a;
                border-radius: 4px;
                padding: 5px;
                color: #cdd6f4;
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # LEFT: The List (Filmstrip)
        self.list_widget = QListWidget()
        self.list_widget.setViewMode(QListWidget.ViewMode.ListMode)
        self.list_widget.setIconSize(QSize(120, 80)) # Rectangular thumbnails
        self.list_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.list_widget.setSpacing(2)
        
        # Drag & Drop
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.list_widget.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.list_widget.setSortingEnabled(False)

        main_layout.addWidget(self.list_widget, stretch=1)

        # RIGHT: Sidebar Controls
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(300)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 20, 20, 20)
        sidebar_layout.setSpacing(15)

        # Info Dashboard
        dash_layout = QHBoxLayout()
        self.lbl_count = QLabel("0 Frames")
        self.lbl_count.setStyleSheet("font-size: 16px; font-weight: bold; color: #89b4fa;")
        dash_layout.addWidget(self.lbl_count)
        dash_layout.addStretch()
        sidebar_layout.addLayout(dash_layout)

        # File Operations
        grp_file = QGroupBox("Import")
        layout_file = QVBoxLayout()
        
        self.btn_open = QPushButton("📂 Open GIF")
        self.btn_open.clicked.connect(self.open_gif)
        layout_file.addWidget(self.btn_open)

        self.btn_add_frame = QPushButton("➕ Add Image Frame")
        self.btn_add_frame.clicked.connect(self.add_frame)
        layout_file.addWidget(self.btn_add_frame)
        
        grp_file.setLayout(layout_file)
        sidebar_layout.addWidget(grp_file)

        # Edit Operations
        grp_edit = QGroupBox("Edit Sequence")
        layout_edit = QVBoxLayout()
        
        self.btn_remove = QPushButton("🗑️ Remove Selected")
        self.btn_remove.setObjectName("DestructiveBtn")
        self.btn_remove.clicked.connect(self.remove_selected)
        layout_edit.addWidget(self.btn_remove)
        
        self.btn_reverse = QPushButton("🔄 Reverse Order")
        self.btn_reverse.clicked.connect(self.reverse_order)
        layout_edit.addWidget(self.btn_reverse)

        grp_edit.setLayout(layout_edit)
        sidebar_layout.addWidget(grp_edit)

        # Export Settings
        grp_export = QGroupBox("Export")
        layout_export = QVBoxLayout()
        layout_export.setSpacing(10)

        # FPS Row
        fps_layout = QHBoxLayout()
        fps_layout.addWidget(QLabel("Frame Rate:"))
        self.fps_spin = QDoubleSpinBox()
        self.fps_spin.setRange(0.1, 120.0)
        self.fps_spin.setValue(10.0)
        self.fps_spin.setSuffix(" fps")
        fps_layout.addWidget(self.fps_spin)
        layout_export.addLayout(fps_layout)

        self.btn_export_frames = QPushButton("💾 Export All Frames")
        self.btn_export_frames.clicked.connect(self.export_all_frames)
        layout_export.addWidget(self.btn_export_frames)

        self.btn_export_selected = QPushButton("💾 Export Selected Only")
        self.btn_export_selected.clicked.connect(self.export_selected_frames)
        layout_export.addWidget(self.btn_export_selected)

        grp_export.setLayout(layout_export)
        sidebar_layout.addWidget(grp_export)

        sidebar_layout.addStretch()

        # Primary Action (Bottom)
        self.btn_reassemble = QPushButton("Reassemble to GIF")
        self.btn_reassemble.setObjectName("PrimaryBtn")
        self.btn_reassemble.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reassemble.clicked.connect(self.reassemble_gif)
        sidebar_layout.addWidget(self.btn_reassemble)

        main_layout.addWidget(sidebar)

    # Logic

    def update_frame_count(self):
        count = self.list_widget.count()
        self.lbl_count.setText(f"{count} Frames")

    def detect_fps(self, gif_path):
        try:
            cmd = [
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=r_frame_rate",
                "-of", "default=noprint_wrappers=1:nokey=1",
                gif_path
            ]
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            result = subprocess.run(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, check=True, startupinfo=startupinfo
            )

            fps_str = result.stdout.strip()
            if '/' in fps_str:
                num, den = map(float, fps_str.split('/'))
                if den != 0: return num / den
            return float(fps_str)
        except:
            return None

    def open_gif(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select GIF", "", "GIF Files (*.gif)")
        if not file_path: return

        if self.temp_dir: shutil.rmtree(self.temp_dir, ignore_errors=True)
        self.temp_dir = tempfile.mkdtemp(prefix="qt_gif_editor_")

        # Detect FPS
        detected_fps = self.detect_fps(file_path)
        if detected_fps: self.fps_spin.setValue(detected_fps)

        # Extract
        extract_pattern = os.path.join(self.temp_dir, "frame_%04d.png")
        cmd = ["ffmpeg", "-i", file_path, extract_pattern]

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
        except subprocess.CalledProcessError as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, "Error", f"FFmpeg failed to extract frames.\n{e}")
            return

        # Populate List
        self.list_widget.clear()
        files = sorted([f for f in os.listdir(self.temp_dir) if f.startswith("frame_") and f.endswith(".png")])

        for f in files:
            full_path = os.path.join(self.temp_dir, f)
            self.add_frame_item(full_path)
        
        QApplication.restoreOverrideCursor()
        self.update_frame_count()

    def add_frame_item(self, path):
        item = QListWidgetItem()
        pixmap = QPixmap(path)
        
        # Scale pixmap for the icon to save memory on large lists
        icon_pix = pixmap.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        item.setIcon(QIcon(icon_pix))
        
        # Text details
        filename = os.path.basename(path)
        dims = f"{pixmap.width()}x{pixmap.height()}"
        item.setText(f"{filename}\nDimensions: {dims}")
        
        item.setData(Qt.ItemDataRole.UserRole, path)
        self.list_widget.addItem(item)

    def add_frame(self):
        if not self.temp_dir: self.temp_dir = tempfile.mkdtemp(prefix="qt_gif_editor_")

        file_path, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
        if not file_path: return

        new_index = self.list_widget.count() + 1
        new_filename = f"frame_added_{new_index:04d}.png"
        dest_path = os.path.join(self.temp_dir, new_filename)

        # Normalize to PNG
        cmd = ["ffmpeg", "-y", "-i", file_path, dest_path]
        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
            self.add_frame_item(dest_path)
            self.update_frame_count()
        except subprocess.CalledProcessError:
            QMessageBox.critical(self, "Error", "Failed to process image.")

    def remove_selected(self):
        selected_items = self.list_widget.selectedItems()
        if not selected_items: return
        
        # Loop backwards to avoid index shifting issues
        for item in selected_items:
            row = self.list_widget.row(item)
            self.list_widget.takeItem(row)
        self.update_frame_count()

    def reverse_order(self):
        count = self.list_widget.count()
        if count < 2: return
        
        items = []
        for i in range(count):
            items.append(self.list_widget.takeItem(0))
            
        for item in reversed(items):
            self.list_widget.addItem(item)

    def reassemble_gif(self):
        if self.list_widget.count() == 0:
            QMessageBox.warning(self, "Warning", "No frames to assemble.")
            return

        save_path, _ = QFileDialog.getSaveFileName(self, "Save GIF", "", "GIF Files (*.gif)")
        if not save_path: return
        if not save_path.lower().endswith(".gif"): save_path += ".gif"

        fps = self.fps_spin.value()
        assemble_dir = tempfile.mkdtemp(prefix="gif_assemble_")

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            # Copy frames in visual order to new temp dir
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                original_path = item.data(Qt.ItemDataRole.UserRole)
                if not os.path.exists(original_path): continue
                
                # Naming must be sequential for ffmpeg glob/sequence
                new_name = f"frame_{i:04d}.png"
                shutil.copy(original_path, os.path.join(assemble_dir, new_name))

            # Generate Palette first for better quality
            palette_path = os.path.join(assemble_dir, "palette.png")
            
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            # Palette Gen
            cmd_pal = [
                "ffmpeg", "-y", "-framerate", str(fps),
                "-i", os.path.join(assemble_dir, "frame_%04d.png"),
                "-vf", "palettegen", palette_path
            ]
            subprocess.run(cmd_pal, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)

            # Gif Gen
            cmd_gif = [
                "ffmpeg", "-y", "-framerate", str(fps),
                "-i", os.path.join(assemble_dir, "frame_%04d.png"),
                "-i", palette_path,
                "-lavfi", "paletteuse", "-loop", "0",
                save_path
            ]
            subprocess.run(cmd_gif, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
            
            QApplication.restoreOverrideCursor()
            QMessageBox.information(self, "Success", f"GIF Assembled Successfully!\nSaved to: {save_path}")

        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, "Error", f"Failed to reassemble GIF.\n{e}")
        finally:
            shutil.rmtree(assemble_dir, ignore_errors=True)

    def export_all_frames(self):
        if self.list_widget.count() == 0: return
        dest_dir = QFileDialog.getExistingDirectory(self, "Select Export Directory")
        if not dest_dir: return

        count = 0
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            original_path = item.data(Qt.ItemDataRole.UserRole)
            filename = f"export_frame_{i:04d}.png"
            shutil.copy(original_path, os.path.join(dest_dir, filename))
            count += 1
        
        QMessageBox.information(self, "Success", f"Exported {count} frames.")

    def export_selected_frames(self):
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Required", "Please select at least one frame to export.")
            return

        dest_dir = QFileDialog.getExistingDirectory(self, "Select Export Directory")
        if not dest_dir: return

        # Sort selected items by their visual index in the list
        selected_items.sort(key=lambda x: self.list_widget.row(x))

        count = 0
        for i, item in enumerate(selected_items):
            original_path = item.data(Qt.ItemDataRole.UserRole)
            if original_path and os.path.exists(original_path):
                # Naming them sequentially based on selection order
                filename = f"selected_frame_{i:04d}.png"
                shutil.copy(original_path, os.path.join(dest_dir, filename))
                count += 1
        
        QMessageBox.information(self, "Success", f"Exported {count} selected frames.")

    def closeEvent(self, event):
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = GifEditor()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()