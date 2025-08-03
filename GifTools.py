import tkinter as tk
from tkinter import messagebox
import subprocess
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

# Run other python scripts


def run_script(script_name):
    try:
        subprocess.run(['python', script_name], check=True)
    except subprocess.CalledProcessError as e:
        messagebox.showerror(
            "Error", f"An error occurred while running {script_name}: {e}")


class GifToolsApp:
    def __init__(self, master):
        self.master = master
        master.title("GifTools")
        master.geometry("400x400")

        # Frame for the main content
        frame = ttk.Frame(master, padding=10)
        frame.pack(padx=10, pady=10, fill=X)

        # Title
        self.title_label = ttk.Label(frame, text="GifTools", font=(
            "Helvetica", 16), bootstyle="light")
        self.title_label.pack(pady=(0, 10))  # Spacing

        # Buttons for each GIF tools
        self.add_text_button = ttk.Button(frame, text="Add Text to GIF", command=lambda: run_script(
            "AddTextToGif.py"), bootstyle="success")
        self.add_text_button.pack(pady=5, fill=X)

        self.compress_button = ttk.Button(
            frame, text="Compress GIF", command=lambda: run_script("CompressGif.py"), bootstyle="info")
        self.compress_button.pack(pady=5, fill=X)

        self.convert_button = ttk.Button(frame, text="Convert MP4 to GIF", command=lambda: run_script(
            "ConvertMP4toGIF.py"), bootstyle="warning")
        self.convert_button.pack(pady=5, fill=X)

        self.edit_frames_button = ttk.Button(frame, text="Edit GIF Frames", command=lambda: run_script(
            "EditGifFrames.py"), bootstyle="primary")
        self.edit_frames_button.pack(pady=5, fill=X)

        self.resize_button = ttk.Button(frame, text="Resize GIF", command=lambda: run_script(
            "ResizeGif.py"), bootstyle="light")
        self.resize_button.pack(pady=5, fill=X)

        # Exit button
        self.exit_button = ttk.Button(
            frame, text="Exit", command=master.quit, bootstyle="danger")
        self.exit_button.pack(pady=20, fill=X)


if __name__ == "__main__":
    root = ttk.Window(themename="superhero")
    app = GifToolsApp(root)
    root.mainloop()
