# main.py
import sys
import os
import io
import requests
import qrcode
from PIL import Image
from dotenv import load_dotenv

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QFileDialog,
    QVBoxLayout, QHBoxLayout, QTextEdit, QComboBox, QTabWidget, QColorDialog,
    QMessageBox, QProgressBar, QCheckBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QMimeData
from PyQt5.QtGui import QPixmap, QDragEnterEvent, QDropEvent, QPalette, QColor

# Load .env file
load_dotenv()
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY")
if not IMGBB_API_KEY:
    print("❌ IMGBB_API_KEY not found in .env")
    sys.exit(1)

class UploadThread(QThread):
    success = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path

    def run(self):
        try:
            with open(self.image_path, "rb") as file:
                response = requests.post(
                    "https://api.imgbb.com/1/upload",
                    data={"key": IMGBB_API_KEY},
                    files={"image": file}
                )
            if response.status_code == 200:
                url = response.json()["data"]["url"]
                self.success.emit(url)
            else:
                self.error.emit("Upload failed: " + response.text)
        except Exception as e:
            self.error.emit(str(e))

class DropLabel(QLabel):
    fileDropped = pyqtSignal(str)

    def __init__(self):
        super().__init__("\n\nDrop Image Here\n", alignment=Qt.AlignCenter)
        self.setAcceptDrops(True)
        self.setStyleSheet("border: 2px dashed #aaa; font-size: 16px; padding: 40px;")

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.isfile(file_path):
                self.fileDropped.emit(file_path)
                break

class QRCodeApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎨 QR Code Generator Pro")
        self.setGeometry(100, 100, 800, 700)
        self.url = ""
        self.qr_image = None
        self.dark_mode = False
        self.init_ui()

    def init_ui(self):
        tabs = QTabWidget()
        tabs.addTab(self.create_generate_tab(), "Generate QR")
        tabs.addTab(self.create_settings_tab(), "Settings")
        self.setCentralWidget(tabs)

    def create_generate_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.drop_label = DropLabel()
        self.drop_label.fileDropped.connect(self.upload_image)
        layout.addWidget(self.drop_label)

        self.upload_btn = QPushButton("📤 Browse Image")
        self.upload_btn.clicked.connect(self.browse_image)
        layout.addWidget(self.upload_btn)

        self.image_preview = QLabel("Image Preview")
        self.image_preview.setFixedHeight(200)
        self.image_preview.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image_preview)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        self.url_display = QTextEdit()
        self.url_display.setReadOnly(True)
        layout.addWidget(self.url_display)

        self.copy_btn = QPushButton("📋 Copy URL")
        self.copy_btn.clicked.connect(self.copy_url)
        self.copy_btn.setEnabled(False)
        layout.addWidget(self.copy_btn)

        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Size:"))
        self.size_box = QComboBox()
        self.size_box.addItems(["Small", "Medium", "Large"])
        self.size_box.setCurrentText("Medium")
        size_layout.addWidget(self.size_box)

        self.color_btn = QPushButton("🎨 Pick Color")
        self.color_btn.clicked.connect(self.pick_color)
        self.qr_color = "black"
        size_layout.addWidget(self.color_btn)
        layout.addLayout(size_layout)

        self.qr_label = QLabel("QR Code Preview")
        self.qr_label.setFixedHeight(250)
        self.qr_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.qr_label)

        self.save_btn = QPushButton("💾 Save QR Code")
        self.save_btn.clicked.connect(self.save_qr)
        self.save_btn.setEnabled(False)
        layout.addWidget(self.save_btn)

        return widget

    def create_settings_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.dark_toggle = QCheckBox("🌙 Enable Dark Mode")
        self.dark_toggle.stateChanged.connect(self.toggle_dark_mode)
        layout.addWidget(self.dark_toggle)

        clear_btn = QPushButton("🧹 Clear All")
        clear_btn.clicked.connect(self.clear_all)
        layout.addWidget(clear_btn)

        return widget

    def browse_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Images (*.png *.jpg *.jpeg *.gif)")
        if path:
            self.upload_image(path)

    def upload_image(self, file_path):
        self.image_preview.setPixmap(QPixmap(file_path).scaled(200, 200, Qt.KeepAspectRatio))
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.thread = UploadThread(file_path)
        self.thread.success.connect(self.upload_success)
        self.thread.error.connect(self.upload_error)
        self.thread.start()

    def upload_success(self, url):
        self.progress.setVisible(False)
        self.url = url
        self.url_display.setText(url)
        self.copy_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        self.generate_qr(url)

    def upload_error(self, err):
        self.progress.setVisible(False)
        QMessageBox.critical(self, "Upload Failed", err)

    def copy_url(self):
        QApplication.clipboard().setText(self.url)

    def generate_qr(self, data):
        size_map = {"Small": 200, "Medium": 300, "Large": 400}
        size = size_map[self.size_box.currentText()]
        qr = qrcode.QRCode(box_size=10, border=4)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color=self.qr_color, back_color="white")
        self.qr_image = img

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        pixmap = QPixmap()
        pixmap.loadFromData(buffer.getvalue())
        self.qr_label.setPixmap(pixmap.scaled(size, size, Qt.KeepAspectRatio))

    def pick_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.qr_color = color.name()
            if self.url:
                self.generate_qr(self.url)

    def save_qr(self):
        if self.qr_image:
            path, _ = QFileDialog.getSaveFileName(self, "Save QR Code", "qr_code.png", "PNG Files (*.png)")
            if path:
                self.qr_image.save(path)

    def clear_all(self):
        self.url = ""
        self.qr_image = None
        self.qr_label.clear()
        self.url_display.clear()
        self.copy_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.image_preview.clear()
        self.drop_label.setText("\n\nDrop Image Here\n")

    def toggle_dark_mode(self, state):
        if state:
            palette = QPalette()
            palette.setColor(QPalette.Window, QColor(53, 53, 53))
            palette.setColor(QPalette.WindowText, Qt.white)
            palette.setColor(QPalette.Base, QColor(25, 25, 25))
            palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
            palette.setColor(QPalette.ToolTipBase, Qt.white)
            palette.setColor(QPalette.ToolTipText, Qt.white)
            palette.setColor(QPalette.Text, Qt.white)
            palette.setColor(QPalette.Button, QColor(53, 53, 53))
            palette.setColor(QPalette.ButtonText, Qt.white)
            palette.setColor(QPalette.BrightText, Qt.red)
            QApplication.setPalette(palette)
        else:
            QApplication.setPalette(QApplication.style().standardPalette())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    win = QRCodeApp()
    win.show()
    sys.exit(app.exec_())
