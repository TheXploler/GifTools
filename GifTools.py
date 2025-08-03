import tkinter as tk  
from tkinter import messagebox  
from ResizeGif import start_resize_gif  
from EditGifFrames import start_edit_gif_frames  
from ConvertMP4toGIF import start_convert_mp4_to_gif  
from CompressGif import start_compress_gif  
from AddTextToGif import start_add_text_to_gif  
import ttkbootstrap as ttk  

class GifToolsApp:  
    def __init__(self, master):  
        self.master = master  
        master.title("GifTools")  
        master.geometry("400x400")  

        # Frame for the main content  
        frame = ttk.Frame(master, padding=10)  
        frame.pack(padx=10, pady=10, fill=tk.X)  

        # Title  
        self.title_label = ttk.Label(frame, text="GifTools", font=("Helvetica", 16), bootstyle="light")  
        self.title_label.pack(pady=(0, 10))  

        # Buttons for each GIF tool  
        self.add_text_button = ttk.Button(frame, text="Add Text to GIF", command=start_add_text_to_gif, bootstyle="success")  
        self.add_text_button.pack(pady=5, fill=tk.X)  

        self.compress_button = ttk.Button(frame, text="Compress GIF", command=start_compress_gif, bootstyle="info")  
        self.compress_button.pack(pady=5, fill=tk.X)  

        self.convert_button = ttk.Button(frame, text="Convert MP4 to GIF", command=start_convert_mp4_to_gif, bootstyle="warning")  
        self.convert_button.pack(pady=5, fill=tk.X)  

        self.edit_frames_button = ttk.Button(frame, text="Edit GIF Frames", command=start_edit_gif_frames, bootstyle="primary")  
        self.edit_frames_button.pack(pady=5, fill=tk.X)  

        self.resize_button = ttk.Button(frame, text="Resize GIF", command=start_resize_gif, bootstyle="light")  
        self.resize_button.pack(pady=5, fill=tk.X)  

        # Exit button  
        self.exit_button = ttk.Button(frame, text="Exit", command=master.quit, bootstyle="danger")  
        self.exit_button.pack(pady=20, fill=tk.X)  

if __name__ == "__main__":  
    root = ttk.Window(themename="superhero")  
    app = GifToolsApp(root)  
    root.mainloop()  