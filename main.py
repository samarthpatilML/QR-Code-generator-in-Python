import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import qrcode
import requests
import io
import threading
import os
from dotenv import load_dotenv

load_dotenv()
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY")
if not IMGBB_API_KEY:
    print("❌ IMGBB_API_KEY not found in .env")
    sys.exit(1)

class QRCodeGenerator:
    def __init__(self, root):
        self.root = root
        self.setup_window()
        self.create_widgets()
        self.current_qr_image = None
        self.current_url = ""
        
    def setup_window(self):
        self.root.title("QR Code Generator Pro")
        self.root.geometry("600x700")
        self.root.resizable(True, True)
        self.root.configure(bg='#f0f0f0')
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Title.TLabel', font=('Helvetica', 20, 'bold'), background='#f0f0f0')
        style.configure('Subtitle.TLabel', font=('Helvetica', 10), background='#f0f0f0', foreground='#666')
        style.configure('Modern.TButton', font=('Helvetica', 10, 'bold'), padding=10)
        style.configure('Save.TButton', font=('Helvetica', 10, 'bold'), padding=8)
        
    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header section
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = ttk.Label(header_frame, text="🖼️ QR Code Generator Pro", style='Title.TLabel')
        title_label.pack(anchor='center')
        
        subtitle_label = ttk.Label(header_frame, 
                                 text="Upload an image to generate a QR code that links to it", 
                                 style='Subtitle.TLabel')
        subtitle_label.pack(anchor='center', pady=(5, 0))
        
        # Upload section
        upload_frame = ttk.LabelFrame(main_frame, text="Step 1: Select Image", padding="15")
        upload_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.upload_button = ttk.Button(upload_frame, 
                                      text="📤 Browse & Upload Image", 
                                      command=self.handle_upload_and_generate,
                                      style='Modern.TButton')
        self.upload_button.pack(pady=5)
        
        # Progress bar
        self.progress = ttk.Progressbar(upload_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=(10, 0))
        self.progress.pack_forget()  # Initially hidden
        
        # Status label
        self.status_label = ttk.Label(upload_frame, text="Ready to upload", foreground='#666')
        self.status_label.pack(pady=(5, 0))
        
        # URL display section
        url_frame = ttk.LabelFrame(main_frame, text="Step 2: Generated URL", padding="15")
        url_frame.pack(fill=tk.X, pady=(0, 15))
        
        # URL text widget with scrollbar
        url_text_frame = ttk.Frame(url_frame)
        url_text_frame.pack(fill=tk.X)
        
        self.url_text = tk.Text(url_text_frame, height=3, wrap=tk.WORD, 
                               state=tk.DISABLED, font=('Courier', 9))
        url_scrollbar = ttk.Scrollbar(url_text_frame, orient=tk.VERTICAL, command=self.url_text.yview)
        self.url_text.configure(yscrollcommand=url_scrollbar.set)
        
        self.url_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        url_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Copy URL button
        self.copy_button = ttk.Button(url_frame, text="📋 Copy URL", 
                                    command=self.copy_url, state=tk.DISABLED)
        self.copy_button.pack(pady=(10, 0))
        
        # QR Code display section
        qr_frame = ttk.LabelFrame(main_frame, text="Step 3: QR Code Preview", padding="15")
        qr_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # QR Code display with border
        qr_display_frame = ttk.Frame(qr_frame)
        qr_display_frame.pack(expand=True, fill=tk.BOTH)
        
        self.qr_label = ttk.Label(qr_display_frame, text="QR Code will appear here", 
                                anchor='center', background='white', relief='sunken')
        self.qr_label.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        # QR Code options
        options_frame = ttk.Frame(qr_frame)
        options_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Size selection
        size_frame = ttk.Frame(options_frame)
        size_frame.pack(side=tk.LEFT)
        
        ttk.Label(size_frame, text="Size:").pack(side=tk.LEFT)
        self.size_var = tk.StringVar(value="Medium")
        size_combo = ttk.Combobox(size_frame, textvariable=self.size_var, 
                                values=["Small", "Medium", "Large"], 
                                state="readonly", width=10)
        size_combo.pack(side=tk.LEFT, padx=(5, 0))
        size_combo.bind('<<ComboboxSelected>>', self.update_qr_size)
        
        # Save section
        save_frame = ttk.Frame(main_frame)
        save_frame.pack(fill=tk.X)
        
        self.save_button = ttk.Button(save_frame, text="💾 Save QR Code", 
                                    command=self.save_qr_image, 
                                    state=tk.DISABLED,
                                    style='Save.TButton')
        self.save_button.pack(side=tk.LEFT)
        
        # Clear button
        self.clear_button = ttk.Button(save_frame, text="🗑️ Clear", 
                                     command=self.clear_all, 
                                     state=tk.DISABLED)
        self.clear_button.pack(side=tk.LEFT, padx=(10, 0))
        
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
    
    def generate_qr_code(self, data, size='Medium'):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        # Create QR code image
        qr_img = qr.make_image(fill_color="black", back_color="white")
        return qr_img
    
    def get_display_size(self):
        size_map = {"Small": 150, "Medium": 200, "Large": 250}
        return size_map.get(self.size_var.get(), 200)
    
    def show_qr_on_label(self, qr_img):
        bio = io.BytesIO()
        qr_img.save(bio, format="PNG")
        bio.seek(0)
        qr_img_tk = Image.open(bio)
        
        # Resize based on selected size
        display_size = self.get_display_size()
        qr_img_tk = qr_img_tk.resize((display_size, display_size), Image.Resampling.LANCZOS)
        
        qr_photo = ImageTk.PhotoImage(qr_img_tk)
        self.qr_label.config(image=qr_photo, text="")
        self.qr_label.image = qr_photo
    
    def update_qr_size(self, event=None):
        if self.current_qr_image:
            self.show_qr_on_label(self.current_qr_image)
    
    def handle_upload_and_generate(self):
        image_path = filedialog.askopenfilename(
            title="Select Image File",
            filetypes=[
                ("Image Files", "*.jpg *.jpeg *.png *.gif *.bmp"),
                ("JPEG Files", "*.jpg *.jpeg"),
                ("PNG Files", "*.png"),
                ("All Files", "*.*")
            ]
        )
        
        if not image_path:
            return
        
        # Start upload in separate thread
        def upload_thread():
            try:
                self.root.after(0, self.start_upload_ui)
                url = self.upload_image_to_imgbb(image_path, IMGBB_API_KEY)
                qr = self.generate_qr_code(url)
                
                # Update UI in main thread
                self.root.after(0, lambda: self.upload_success(url, qr))
                
            except Exception as e:
                self.root.after(0, lambda: self.upload_error(str(e)))
        
        threading.Thread(target=upload_thread, daemon=True).start()
    
    def start_upload_ui(self):
        self.upload_button.config(state=tk.DISABLED)
        self.progress.pack(fill=tk.X, pady=(10, 0))
        self.progress.start()
        self.status_label.config(text="Uploading image...", foreground='#0066cc')
    
    def upload_success(self, url, qr):
        self.progress.stop()
        self.progress.pack_forget()
        self.upload_button.config(state=tk.NORMAL)
        self.status_label.config(text="Upload successful!", foreground='#006600')
        
        # Update URL display
        self.url_text.config(state=tk.NORMAL)
        self.url_text.delete(1.0, tk.END)
        self.url_text.insert(1.0, url)
        self.url_text.config(state=tk.DISABLED)
        
        # Store current data
        self.current_url = url
        self.current_qr_image = qr
        
        # Show QR code
        self.show_qr_on_label(qr)
        
        # Enable buttons
        self.save_button.config(state=tk.NORMAL)
        self.clear_button.config(state=tk.NORMAL)
        self.copy_button.config(state=tk.NORMAL)
        
        messagebox.showinfo("Success", "Image uploaded and QR code generated successfully!")
    
    def upload_error(self, error_msg):
        self.progress.stop()
        self.progress.pack_forget()
        self.upload_button.config(state=tk.NORMAL)
        self.status_label.config(text="Upload failed", foreground='#cc0000')
        messagebox.showerror("Error", f"Upload failed:\n{error_msg}")
    
    def copy_url(self):
        if self.current_url:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.current_url)
            messagebox.showinfo("Copied", "URL copied to clipboard!")
    
    def save_qr_image(self):
        if not self.current_qr_image:
            return
            
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[
                ("PNG Files", "*.png"),
                ("JPEG Files", "*.jpg"),
                ("All Files", "*.*")
            ],
            title="Save QR Code"
        )
        
        if path:
            try:
                self.current_qr_image.save(path)
                messagebox.showinfo("Saved", f"QR Code saved successfully to:\n{os.path.basename(path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save QR code:\n{str(e)}")
    
    def clear_all(self):
        # Clear URL
        self.url_text.config(state=tk.NORMAL)
        self.url_text.delete(1.0, tk.END)
        self.url_text.config(state=tk.DISABLED)
        
        # Clear QR code
        self.qr_label.config(image='', text="QR Code will appear here")
        self.qr_label.image = None
        
        # Reset variables
        self.current_qr_image = None
        self.current_url = ""
        
        # Disable buttons
        self.save_button.config(state=tk.DISABLED)
        self.clear_button.config(state=tk.DISABLED)
        self.copy_button.config(state=tk.DISABLED)
        
        # Reset status
        self.status_label.config(text="Ready to upload", foreground='#666')

# 🖼️ Main application
def main():
    root = tk.Tk()
    app = QRCodeGenerator(root)
    root.mainloop()

if __name__ == "__main__":
    main()