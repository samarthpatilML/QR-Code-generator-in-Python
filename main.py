import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import qrcode
import requests
import io

# 🔐 Replace with your actual ImgBB API key
IMGBB_API_KEY = "6c21e17ed1e741b2e8f127731233fb73"

# 📤 Function to upload image
def upload_image_to_imgbb(image_path, api_key):
    with open(image_path, "rb") as file:
        url = "https://api.imgbb.com/1/upload"
        payload = {"key": api_key}
        files = {"image": file}
        response = requests.post(url, data=payload, files=files)
        if response.status_code == 200:
            return response.json()['data']['url']
        else:
            raise Exception("Image upload failed:\n" + response.text)

# 🔲 Function to generate QR Code
def generate_qr_code(data):
    qr = qrcode.make(data)
    return qr

# 🖼️ Load QR Image to preview in GUI
def show_qr_on_label(qr_img):
    bio = io.BytesIO()
    qr_img.save(bio, format="PNG")
    bio.seek(0)
    qr_img_tk = Image.open(bio)
    qr_img_tk = qr_img_tk.resize((200, 200))
    qr_photo = ImageTk.PhotoImage(qr_img_tk)
    qr_label.config(image=qr_photo)
    qr_label.image = qr_photo

# 🎯 Action when "Upload & Generate" is clicked
def handle_upload_and_generate():
    image_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.png *.jpeg *.gif")])
    if not image_path:
        return

    try:
        url = upload_image_to_imgbb(image_path, IMGBB_API_KEY)
        url_var.set(url)
        qr = generate_qr_code(url)
        show_qr_on_label(qr)
        save_button.config(state=tk.NORMAL)
        messagebox.showinfo("Success", "Image uploaded and QR code generated.")
    except Exception as e:
        messagebox.showerror("Error", str(e))

# 💾 Save QR Image
def save_qr_image():
    path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Files", "*.png")])
    if path:
        qr_img = generate_qr_code(url_var.get())
        qr_img.save(path)
        messagebox.showinfo("Saved", f"QR Code saved to {path}")

# 🖼️ GUI Setup
root = tk.Tk()
root.title("Image to QR Code Generator")
root.geometry("500x450")
root.resizable(False, False)

frame = tk.Frame(root, padx=20, pady=20)
frame.pack(expand=True)

title = tk.Label(frame, text="🖼️ Image to QR Code Generator", font=("Helvetica", 16, "bold"))
title.pack(pady=10)

upload_button = tk.Button(frame, text="📤 Select Image & Generate QR", command=handle_upload_and_generate)
upload_button.pack(pady=10)

url_var = tk.StringVar()
url_label = tk.Label(frame, textvariable=url_var, wraplength=400, fg="blue")
url_label.pack(pady=5)

qr_label = tk.Label(frame)
qr_label.pack(pady=10)

save_button = tk.Button(frame, text="💾 Save QR Code", command=save_qr_image, state=tk.DISABLED)
save_button.pack(pady=5)

root.mainloop()
