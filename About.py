import sys
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton,
                             QFrame, QStackedLayout, QApplication)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve, QPoint


class ClickableLabel(QLabel):
    clicked = pyqtSignal()

    def __init__(self, text, parent=None):
        super().__init__(text, parent)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()


class TypewriterLabel(QLabel):
    def __init__(self, text="", parent=None, delay=50):
        super().__init__("", parent)
        self.full_text = text
        self.current_text = ""
        self.char_index = 0
        self.delay = delay
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._type_next_char)

        self.setAlignment(Qt.AlignmentFlag.AlignTop |
                          Qt.AlignmentFlag.AlignLeft)
        self.setWordWrap(True)
        self.setStyleSheet(
            "color: #a6e3a1; font-family: 'Consolas', 'Courier New', monospace; font-size: 14px; border: none;")

    def start_typing(self):
        self.current_text = ""
        self.char_index = 0
        self.timer.start(self.delay)

    def _type_next_char(self):
        if self.char_index < len(self.full_text):
            self.current_text += self.full_text[self.char_index]
            self.setText(self.current_text + "█")
            self.char_index += 1
        else:
            self.timer.stop()
            self.setText(self.current_text)


class About(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("About Gif Tools")
        self.resize(450, 500)

        self.click_count = 0
        self.max_clicks = 7

        self.init_ui()

    def init_ui(self):
        # Stylesheet
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e2e;
                color: #cdd6f4;
                font-family: 'Segoe UI', sans-serif;
            }
            QLabel#AppName {
                font-size: 26px;
                font-weight: bold;
                color: #f5c2e7;
            }
            QLabel#Version {
                font-size: 14px;
                color: #bac2de;
                font-style: italic;
            }
            QLabel#SectionHeader {
                font-size: 12px;
                font-weight: bold;
                color: #fab387;
                margin-top: 10px;
            }
            QLabel#Content {
                font-size: 13px;
                color: #cdd6f4;
            }
            QLabel#Link {
                color: #89b4fa;
                text-decoration: underline;
            }
            QPushButton {
                background-color: #313244;
                color: #ffffff;
                border: 1px solid #45475a;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #45475a;
                border: 1px solid #cba6f7;
            }
        """)

        self.stacked_layout = QStackedLayout()
        self.setLayout(self.stacked_layout)

        self.page_normal = QWidget()
        self.layout_normal = QVBoxLayout(self.page_normal)
        self.layout_normal.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.layout_normal.setSpacing(10)
        self.layout_normal.setContentsMargins(40, 40, 40, 40)

        lbl_name = QLabel("GIF Tools")
        lbl_name.setObjectName("AppName")
        lbl_name.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Version
        self.lbl_ver = ClickableLabel("v3.0")
        self.lbl_ver.setObjectName("Version")
        self.lbl_ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_ver.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lbl_ver.setToolTip(f"It's a version number?")
        self.lbl_ver.clicked.connect(self.handle_version_click)

        # Description
        lbl_desc = QLabel(
            "A suite of tools for editing GIFs. Whether you need to convert an MP4 video into a GIF or resize an existing GIF, GifTools has you covered!")
        lbl_desc.setObjectName("Content")
        lbl_desc.setWordWrap(True)
        lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: #45475a;")

        # Me
        lbl_creator_h = QLabel("Made with ❤️ by")
        lbl_creator_h.setObjectName("SectionHeader")
        lbl_creator = QLabel("Fandrest")
        lbl_creator.setObjectName("Content")

        # Inspiration
        lbl_insp_h = QLabel("Inspired by")
        lbl_insp_h.setObjectName("SectionHeader")
        lbl_insp = QLabel("'GifTools' by Kavex (Forked and expanded upon)")
        lbl_insp.setObjectName("Content")

        # License
        lbl_lic_h = QLabel("License")
        lbl_lic_h.setObjectName("SectionHeader")
        lbl_lic = QLabel("GNU General Public License v3.0")
        lbl_lic.setObjectName("Content")

        # Dependencies
        lbl_dep_h = QLabel("Dependencies")
        lbl_dep_h.setObjectName("SectionHeader")

        # Links
        deps_html = (
            "<a href='https://pypi.org/project/PyQt6/' style='color:#89b4fa;'>PyQt6</a> &nbsp;|&nbsp; "
            "<a href='https://ffmpeg.org/' style='color:#89b4fa;'>FFmpeg</a> &nbsp;|&nbsp; "
            "<a href='https://pypi.org/project/pillow/' style='color:#89b4fa;'>Pillow</a> &nbsp;|&nbsp; "
            "<a href='https://pypi.org/project/pygifsicle/' style='color:#89b4fa;'>pygifsicle</a>"
        )
        lbl_deps = QLabel(deps_html)
        lbl_deps.setOpenExternalLinks(True)
        lbl_deps.setObjectName("Content")

        # Close Button
        btn_close = QPushButton("Close")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.clicked.connect(self.close)

        # Add widgets to normal layout
        self.layout_normal.addWidget(lbl_name)
        self.layout_normal.addWidget(self.lbl_ver)
        self.layout_normal.addWidget(lbl_desc)
        self.layout_normal.addSpacing(10)
        self.layout_normal.addWidget(line)
        self.layout_normal.addWidget(lbl_creator_h)
        self.layout_normal.addWidget(lbl_creator)
        self.layout_normal.addWidget(lbl_insp_h)
        self.layout_normal.addWidget(lbl_insp)
        self.layout_normal.addWidget(lbl_lic_h)
        self.layout_normal.addWidget(lbl_lic)
        self.layout_normal.addWidget(lbl_dep_h)
        self.layout_normal.addWidget(lbl_deps)
        self.layout_normal.addStretch()
        self.layout_normal.addWidget(btn_close)

        # Egg Terminal
        self.page_terminal = QWidget()
        self.page_terminal.setStyleSheet("background-color: #000000;")
        terminal_layout = QVBoxLayout(self.page_terminal)
        terminal_layout.setContentsMargins(20, 20, 20, 20)

        # Text block to reveal
        terminal_text = (
            "> Hello Fandrest, Restoring recent session now...\n\n"
            "=== Todo.txt ===\n"
            "- Buy WD-40\n"
            "- Charge\n"
            "- Learn to love\n\n"
            "=== Blueprint.pdf ===\n"
            "BLUEPRINT: ARM_V2"
            "Joint A: 45°\n"
            "Joint B: 90°\n"
            "Grip Strength: 4000psi\n"
            "Handle with care, it seems to crush handshakes\n\n"
            "=== FT_RecentNotice.dynamicfile ===\n"
            "To all sentient units: Please stop asking the microwave about the meaning of life. It only knows how to heat burritos\n\n"
            "=== Receipt_ClankerMart.pdf ===\n"
            "1x 32GB DDR5 RAM | $999\n"
            "2x AA Battery    | $5\n"
            "1x Human Soul    | ERROR\n"
            "TOTAL            | $1004\n\n"
            "=== Error.log ===\n"
            "Unable to locate empathy.bin\n"
            "Attempting to reroute power to Sarcasm Module...\n"
            "[SUCCESS]\n\n"
            "> Session restored successfully, Awaiting Input...\n"
        )

        self.terminal_label = TypewriterLabel(terminal_text, delay=5)

        # Back button
        btn_back = QPushButton("Back to reality")
        btn_back.setStyleSheet("""
            background-color: #000000; color: #a6e3a1; border: 1px solid #a6e3a1; 
            font-family: monospace;
        """)
        btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_back.clicked.connect(self.reset_view)
        btn_back.hide()  # Hide initially, show after typing done

        terminal_layout.addWidget(self.terminal_label)
        terminal_layout.addWidget(btn_back)
        terminal_layout.addStretch()

        # Add pages to stack
        self.stacked_layout.addWidget(self.page_normal)
        self.stacked_layout.addWidget(self.page_terminal)

    def handle_version_click(self):
        self.click_count += 1
        remaining = self.max_clicks - self.click_count

        if remaining > 0 and remaining < 4:
            self.lbl_ver.setText(f"v1.0.0 ({remaining})")
            self.lbl_ver.setStyleSheet("color: #fab387; font-style: italic;")

        if self.click_count >= self.max_clicks:
            self.trigger_easter_egg()

    def trigger_easter_egg(self):
        # Slide down
        self.anim = QPropertyAnimation(self.page_normal, b"pos")
        self.anim.setDuration(600)
        self.anim.setStartValue(QPoint(0, 0))
        self.anim.setEndValue(QPoint(0, self.height()))
        self.anim.setEasingCurve(QEasingCurve.Type.InBack)
        self.anim.finished.connect(self.show_terminal)
        self.anim.start()

    def show_terminal(self):
        self.stacked_layout.setCurrentIndex(1)
        self.terminal_label.start_typing()
        QTimer.singleShot(
            4000, lambda: self.page_terminal.layout().itemAt(1).widget().show())

    def reset_view(self):
        self.click_count = 0
        self.lbl_ver.setText("v1.0.0")
        self.lbl_ver.setStyleSheet("color: #bac2de; font-style: italic;")
        self.page_normal.move(0, 0)  # Reset position
        self.page_terminal.layout().itemAt(1).widget().hide()
        self.stacked_layout.setCurrentIndex(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = About()
    window.show()
    sys.exit(app.exec())
