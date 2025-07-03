import sys
import os
import io
import threading
import requests
import qrcode
from PIL import Image

try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
    PYQT_VERSION = 5
except ImportError:
    try:
        from PyQt6.QtWidgets import *
        from PyQt6.QtCore import *
        from PyQt6.QtGui import *
        PYQT_VERSION = 6
    except ImportError:
        print("Please install PyQt5 or PyQt6: pip install PyQt5 or pip install PyQt6")
        sys.exit(1)

# 🔐 Replace with your actual ImgBB API key
IMGBB_API_KEY = "6c21e17ed1e741b2e8f127731233fb73"

class ModernButton(QPushButton):
    def __init__(self, text, color_scheme="primary", parent=None):
        super().__init__(text, parent)
        self.color_scheme = color_scheme
        self.setStyleSheet(self.get_button_style())
        self.setCursor(Qt.PointingHandCursor if PYQT_VERSION == 5 else Qt.CursorShape.PointingHandCursor)
        
    def get_button_style(self):
        schemes = {
            "primary": {
                "bg": "#667eea",
                "hover": "#764ba2",
                "text": "#ffffff"
            },
            "success": {
                "bg": "#48bb78",
                "hover": "#38a169",
                "text": "#ffffff"
            },
            "secondary": {
                "bg": "#ed64a6",
                "hover": "#d53f8c",
                "text": "#ffffff"
            },
            "danger": {
                "bg": "#f56565",
                "hover": "#e53e3e",
                "text": "#ffffff"
            }
        }
        
        scheme = schemes.get(self.color_scheme, schemes["primary"])
        
        return f"""
            QPushButton {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 {scheme['bg']}, stop: 1 {scheme['hover']});
                color: {scheme['text']};
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 13px;
                min-height: 20px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 {scheme['hover']}, stop: 1 {scheme['bg']});
                transform: translateY(-2px);
            }}
            QPushButton:pressed {{
                background: {scheme['hover']};
                transform: translateY(1px);
            }}
            QPushButton:disabled {{
                background: #a0aec0;
                color: #718096;
            }}
        """

class GradientWidget(QWidget):
    def __init__(self, colors, parent=None):
        super().__init__(parent)
        self.colors = colors
        
    def paintEvent(self, event):
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, 0, self.height())
        
        for i, color in enumerate(self.colors):
            gradient.setColorAt(i / (len(self.colors) - 1), QColor(color))
        
        painter.fillRect(self.rect(), gradient)

class WorkerThread(QThread):
    success = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, image_path, api_key):
        super().__init__()
        self.image_path = image_path
        self.api_key = api_key
    
    def run(self):
        try:
            url = self.upload_image_to_imgbb(self.image_path, self.api_key)
            self.success.emit(url)
        except Exception as e:
            self.error.emit(str(e))
    
    def upload_image_to_imgbb(self, image_path, api_key):
        with open(image_path, "rb") as file:
            url = "https://api.imgbb.com/1/upload"
            payload = {"key": api_key}
            files = {"image": file}
            response = requests.post(url, data=payload, files=files)
            if response.status_code == 200:
                return response.json()['data']['url']
            else:
                raise Exception("Image upload failed:\n" + response.text)

class QRCodeGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_qr_image = None
        self.current_url = ""
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("🎨 QR Code Generator Pro")
        self.setGeometry(100, 100, 800, 900)
        self.setMinimumSize(600, 700)
        
        # Set window icon
        self.setWindowIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        
        # Create central widget with gradient background
        central_widget = GradientWidget(["#667eea", "#764ba2", "#f093fb", "#f5576c"])
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create main content area
        content_widget = QWidget()
        content_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.95);
                border-radius: 15px;
                margin: 20px;
            }
        """)
        main_layout.addWidget(content_widget)
        
        # Content layout
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(25)
        
        # Header section
        self.create_header(content_layout)
        
        # Upload section
        self.create_upload_section(content_layout)
        
        # URL section
        self.create_url_section(content_layout)
        
        # QR Code section
        self.create_qr_section(content_layout)
        
        # Action buttons
        self.create_action_buttons(content_layout)
        
        # Apply global styles
        self.apply_global_styles()
        
    def create_header(self, layout):
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setAlignment(Qt.AlignCenter)
        
        # Title
        title_label = QLabel("🎨 QR Code Generator Pro")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 32px;
                font-weight: bold;
                color: #2d3748;
                margin-bottom: 10px;
                background: transparent;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        
        # Subtitle
        subtitle_label = QLabel("Transform your images into beautiful QR codes")
        subtitle_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #718096;
                background: transparent;
            }
        """)
        subtitle_label.setAlignment(Qt.AlignCenter)
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        layout.addWidget(header_widget)
        
    def create_upload_section(self, layout):
        upload_group = QGroupBox("📤 Step 1: Upload Your Image")
        upload_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #2d3748;
                border: 2px solid #e2e8f0;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
                background: transparent;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
            }
        """)
        
        upload_layout = QVBoxLayout(upload_group)
        upload_layout.setSpacing(15)
        
        # Upload button
        self.upload_btn = ModernButton("🖼️ Browse & Upload Image", "primary")
        self.upload_btn.clicked.connect(self.handle_upload)
        upload_layout.addWidget(self.upload_btn)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                text-align: center;
                background-color: #f7fafc;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #667eea, stop: 1 #764ba2);
                border-radius: 6px;
            }
        """)
        self.progress_bar.setVisible(False)
        upload_layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready to upload your image")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #718096;
                font-size: 14px;
                background: transparent;
                padding: 5px;
            }
        """)
        self.status_label.setAlignment(Qt.AlignCenter)
        upload_layout.addWidget(self.status_label)
        
        layout.addWidget(upload_group)
        
    def create_url_section(self, layout):
        url_group = QGroupBox("🔗 Step 2: Generated URL")
        url_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #2d3748;
                border: 2px solid #e2e8f0;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
                background: transparent;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
            }
        """)
        
        url_layout = QVBoxLayout(url_group)
        url_layout.setSpacing(15)
        
        # URL text area
        self.url_text = QTextEdit()
        self.url_text.setMaximumHeight(80)
        self.url_text.setStyleSheet("""
            QTextEdit {
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                background-color: #f8f9fa;
                color: #2d3748;
            }
        """)
        self.url_text.setReadOnly(True)
        url_layout.addWidget(self.url_text)
        
        # Copy button
        self.copy_btn = ModernButton("📋 Copy URL", "secondary")
        self.copy_btn.clicked.connect(self.copy_url)
        self.copy_btn.setEnabled(False)
        url_layout.addWidget(self.copy_btn)
        
        layout.addWidget(url_group)
        
    def create_qr_section(self, layout):
        qr_group = QGroupBox("🎯 Step 3: QR Code Preview")
        qr_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #2d3748;
                border: 2px solid #e2e8f0;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
                background: transparent;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
            }
        """)
        
        qr_layout = QVBoxLayout(qr_group)
        qr_layout.setSpacing(15)
        
        # QR display area
        self.qr_label = QLabel("Your QR Code will appear here")
        self.qr_label.setStyleSheet("""
            QLabel {
                border: 3px dashed #cbd5e0;
                border-radius: 15px;
                padding: 40px;
                font-size: 18px;
                color: #a0aec0;
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #f7fafc, stop: 1 #edf2f7);
                min-height: 300px;
            }
        """)
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.qr_label.setScaledContents(True)
        qr_layout.addWidget(self.qr_label)
        
        # Size controls
        size_widget = QWidget()
        size_layout = QHBoxLayout(size_widget)
        size_layout.setContentsMargins(0, 0, 0, 0)
        
        size_label = QLabel("Size:")
        size_label.setStyleSheet("color: #4a5568; font-weight: bold; background: transparent;")
        
        self.size_combo = QComboBox()
        self.size_combo.addItems(["Small", "Medium", "Large"])
        self.size_combo.setCurrentText("Medium")
        self.size_combo.setStyleSheet("""
            QComboBox {
                border: 2px solid #e2e8f0;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
                background-color: white;
                color: #2d3748;
                min-width: 100px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border: 5px solid transparent;
                border-top: 5px solid #718096;
                margin-right: 5px;
            }
        """)
        self.size_combo.currentTextChanged.connect(self.update_qr_size)
        
        size_layout.addWidget(size_label)
        size_layout.addWidget(self.size_combo)
        size_layout.addStretch()
        
        qr_layout.addWidget(size_widget)
        layout.addWidget(qr_group)
        
    def create_action_buttons(self, layout):
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(15)
        
        # Save button
        self.save_btn = ModernButton("💾 Save QR Code", "success")
        self.save_btn.clicked.connect(self.save_qr_image)
        self.save_btn.setEnabled(False)
        
        # Clear button
        self.clear_btn = ModernButton("🗑️ Clear All", "danger")
        self.clear_btn.clicked.connect(self.clear_all)
        self.clear_btn.setEnabled(False)
        
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.clear_btn)
        button_layout.addStretch()
        
        layout.addWidget(button_widget)
        
    def apply_global_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f7fafc;
            }
            QWidget {
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        
    def handle_upload(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Image File", 
            "", 
            "Image Files (*.png *.jpg *.jpeg *.gif *.bmp);;All Files (*)"
        )
        
        if file_path:
            self.upload_btn.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate
            self.status_label.setText("Uploading image...")
            self.status_label.setStyleSheet("color: #3182ce; font-weight: bold; background: transparent;")
            
            # Start upload thread
            self.worker = WorkerThread(file_path, IMGBB_API_KEY)
            self.worker.success.connect(self.upload_success)
            self.worker.error.connect(self.upload_error)
            self.worker.start()
            
    def upload_success(self, url):
        self.progress_bar.setVisible(False)
        self.upload_btn.setEnabled(True)
        self.status_label.setText("✅ Upload successful!")
        self.status_label.setStyleSheet("color: #38a169; font-weight: bold; background: transparent;")
        
        # Store URL and generate QR
        self.current_url = url
        self.url_text.setPlainText(url)
        self.generate_and_display_qr(url)
        
        # Enable buttons
        self.copy_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)
        
        # Show success message
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Success")
        msg.setText("Image uploaded and QR code generated successfully!")
        msg.setStyleSheet("""
            QMessageBox {
                background-color: white;
                color: #2d3748;
            }
            QMessageBox QPushButton {
                background-color: #48bb78;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        msg.exec_()
        
    def upload_error(self, error):
        self.progress_bar.setVisible(False)
        self.upload_btn.setEnabled(True)
        self.status_label.setText("❌ Upload failed")
        self.status_label.setStyleSheet("color: #e53e3e; font-weight: bold; background: transparent;")
        
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Upload Error")
        msg.setText(f"Upload failed:\n{error}")
        msg.setStyleSheet("""
            QMessageBox {
                background-color: white;
                color: #2d3748;
            }
            QMessageBox QPushButton {
                background-color: #f56565;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        msg.exec_()
        
    def generate_and_display_qr(self, url):
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        self.current_qr_image = qr_img
        
        # Display QR code
        self.display_qr_image(qr_img)
        
    def display_qr_image(self, qr_img):
        # Convert PIL image to QPixmap
        bio = io.BytesIO()
        qr_img.save(bio, format="PNG")
        bio.seek(0)
        
        pixmap = QPixmap()
        pixmap.loadFromData(bio.getvalue())
        
        # Scale based on size selection
        size_map = {"Small": 200, "Medium": 300, "Large": 400}
        target_size = size_map.get(self.size_combo.currentText(), 300)
        
        scaled_pixmap = pixmap.scaled(target_size, target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        self.qr_label.setPixmap(scaled_pixmap)
        self.qr_label.setStyleSheet("""
            QLabel {
                border: 3px solid #48bb78;
                border-radius: 15px;
                padding: 20px;
                background: white;
                min-height: 300px;
            }
        """)
        
    def update_qr_size(self):
        if self.current_qr_image:
            self.display_qr_image(self.current_qr_image)
            
    def copy_url(self):
        if self.current_url:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.current_url)
            
            # Show temporary notification
            self.status_label.setText("📋 URL copied to clipboard!")
            self.status_label.setStyleSheet("color: #805ad5; font-weight: bold; background: transparent;")
            
            # Reset after 2 seconds
            QTimer.singleShot(2000, lambda: self.status_label.setText("✅ Upload successful!"))
            
    def save_qr_image(self):
        if not self.current_qr_image:
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save QR Code", 
            "qr_code.png", 
            "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)"
        )
        
        if file_path:
            try:
                self.current_qr_image.save(file_path)
                
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setWindowTitle("Saved")
                msg.setText(f"QR Code saved successfully to:\n{os.path.basename(file_path)}")
                msg.setStyleSheet("""
                    QMessageBox {
                        background-color: white;
                        color: #2d3748;
                    }
                    QMessageBox QPushButton {
                        background-color: #48bb78;
                        color: white;
                        border: none;
                        padding: 8px 16px;
                        border-radius: 4px;
                        font-weight: bold;
                    }
                """)
                msg.exec_()
                
            except Exception as e:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setWindowTitle("Save Error")
                msg.setText(f"Failed to save QR code:\n{str(e)}")
                msg.exec_()
                
    def clear_all(self):
        # Reset all fields
        self.url_text.clear()
        self.qr_label.setPixmap(QPixmap())
        self.qr_label.setText("Your QR Code will appear here")
        self.qr_label.setStyleSheet("""
            QLabel {
                border: 3px dashed #cbd5e0;
                border-radius: 15px;
                padding: 40px;
                font-size: 18px;
                color: #a0aec0;
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #f7fafc, stop: 1 #edf2f7);
                min-height: 300px;
            }
        """)
        
        # Reset variables
        self.current_qr_image = None
        self.current_url = ""
        
        # Disable buttons
        self.copy_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
        
        # Reset status
        self.status_label.setText("Ready to upload your image")
        self.status_label.setStyleSheet("color: #718096; font-size: 14px; background: transparent;")

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern style
    
    # Set application icon
    app.setWindowIcon(app.style().standardIcon(QStyle.SP_ComputerIcon))
    
    generator = QRCodeGenerator()
    generator.show()
    
    sys.exit(app.exec_() if PYQT_VERSION == 5 else app.exec())

if __name__ == "__main__":
    main()