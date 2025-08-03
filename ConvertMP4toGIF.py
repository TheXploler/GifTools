import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os
import tempfile


def browse_input():
    file_path = filedialog.askopenfilename(filetypes=[("MP4 files", "*.mp4")])
    if file_path:
        entry_input.delete(0, tk.END)
        entry_input.insert(0, file_path)


def browse_output():
    file_path = filedialog.asksaveasfilename(
        defaultextension=".gif", filetypes=[("GIF files", "*.gif")])
    if file_path:
        entry_output.delete(0, tk.END)
        entry_output.insert(0, file_path)


def convert_video():
    input_file = entry_input.get()
    output_file = entry_output.get()
    fps = entry_fps.get()
    width = entry_width.get()
    height = entry_height.get()

    if not os.path.exists(input_file):
        messagebox.showerror("Error", "Input file does not exist.")
        return
    if not output_file:
        messagebox.showerror("Error", "Please specify an output file.")
        return
    if not fps:
        messagebox.showerror("Error", "Please enter FPS value.")
        return
    if not width or not height:
        messagebox.showerror("Error", "Please enter both width and height.")
        return

    try:
        # Create a temporary file for the palette
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            palette_file = tmp.name

        # Step 1: Generate the palette
        palette_cmd = [
            "ffmpeg",
            "-y",
            "-i", input_file,
            "-vf", f"fps={fps},scale={width}:{height}:flags=lanczos,palettegen",
            palette_file
        ]
        subprocess.run(palette_cmd, check=True)

        # Step 2: Use the palette to create the GIF
        gif_cmd = [
            "ffmpeg",
            "-y",  # Force overwrite
            "-i", input_file,
            "-i", palette_file,
            "-filter_complex", f"fps={fps},scale={width}:{height}:flags=lanczos[x];[x][1:v]paletteuse",
            output_file
        ]
        subprocess.run(gif_cmd, check=True)

        # Remove the temporary palette file
        os.remove(palette_file)

        messagebox.showinfo("Success", "Conversion completed successfully!")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"Conversion failed:\n{e}")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred:\n{e}")


def start_convert_mp4_to_gif():
    global entry_input, entry_output, entry_fps, entry_width, entry_height
    # Set up the GUI
    root = tk.Tk()
    root.title("MP4 to GIF Converter")
    root.wm_attributes('-toolwindow', 'True')  # Set as a tool window

    # Input file selection
    tk.Label(root, text="Input MP4 File:").grid(
        row=0, column=0, padx=5, pady=5, sticky="e")
    entry_input = tk.Entry(root, width=50)
    entry_input.grid(row=0, column=1, padx=5, pady=5)
    tk.Button(root, text="Browse", command=browse_input).grid(
        row=0, column=2, padx=5, pady=5)

    # Output file selection
    tk.Label(root, text="Output GIF File:").grid(
        row=1, column=0, padx=5, pady=5, sticky="e")
    entry_output = tk.Entry(root, width=50)
    entry_output.grid(row=1, column=1, padx=5, pady=5)
    tk.Button(root, text="Browse", command=browse_output).grid(
        row=1, column=2, padx=5, pady=5)

    # FPS input with pre-filled value "30"
    tk.Label(root, text="FPS:").grid(
        row=2, column=0, padx=5, pady=5, sticky="e")
    entry_fps = tk.Entry(root)
    entry_fps.grid(row=2, column=1, padx=5, pady=5, sticky="w")
    entry_fps.insert(0, "30")

    # Output size input with pre-filled values 640x480
    tk.Label(root, text="Output Size (width x height):").grid(
        row=3, column=0, padx=5, pady=5, sticky="e")
    entry_width = tk.Entry(root, width=10)
    entry_width.grid(row=3, column=1, padx=(5, 0), pady=5, sticky="w")
    entry_width.insert(0, "640")
    tk.Label(root, text="x").grid(
        row=3, column=1, padx=(80, 0), pady=5, sticky="w")
    entry_height = tk.Entry(root, width=10)
    entry_height.grid(row=3, column=1, padx=(100, 0), pady=5, sticky="w")
    entry_height.insert(0, "480")

    # Convert button
    tk.Button(root, text="Convert", command=convert_video).grid(
        row=4, column=1, padx=5, pady=15)

    root.mainloop()

if __name__ == "__main__":
    start_convert_mp4_to_gif()
