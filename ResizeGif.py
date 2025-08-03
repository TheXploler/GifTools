import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os
import tempfile


def browse_input():
    file_path = filedialog.askopenfilename(filetypes=[("GIF files", "*.gif")])
    if file_path:
        entry_input.delete(0, tk.END)
        entry_input.insert(0, file_path)


def browse_output():
    file_path = filedialog.asksaveasfilename(
        defaultextension=".gif", filetypes=[("GIF files", "*.gif")])
    if file_path:
        entry_output.delete(0, tk.END)
        entry_output.insert(0, file_path)


def update_mode(*args):
    mode = mode_var.get()
    # Hide all option frames
    frame_resolution.grid_remove()
    frame_scale.grid_remove()
    frame_target.grid_remove()

    if mode == "Enter Resolution":
        frame_resolution.grid(row=4, column=0, columnspan=3,
                              padx=5, pady=5, sticky="w")
    elif mode == "Scale Percentage":
        frame_scale.grid(row=4, column=0, columnspan=3,
                         padx=5, pady=5, sticky="w")
    elif mode == "Target File Size":
        frame_target.grid(row=4, column=0, columnspan=3,
                          padx=5, pady=5, sticky="w")


def convert_gif():
    input_file = entry_input.get()
    output_file = entry_output.get()
    fps = entry_fps.get()

    if not os.path.exists(input_file):
        messagebox.showerror("Error", "Input file does not exist.")
        return
    if not output_file:
        messagebox.showerror("Error", "Please specify an output file.")
        return
    if not fps:
        messagebox.showerror("Error", "Please enter an FPS value.")
        return

    # Always overwrite output file if it exists.
    if os.path.exists(output_file):
        try:
            os.remove(output_file)
        except Exception as e:
            messagebox.showerror(
                "Error", f"Failed to remove existing output file:\n{e}")
            return

    mode = mode_var.get()

    try:
        if mode == "Enter Resolution":
            width = entry_width.get()
            height = entry_height.get()
            if not width or not height:
                messagebox.showerror(
                    "Error", "Please enter both width and height.")
                return
            filter_scale = f"scale={width}:{height}:flags=lanczos"
            palette_filter = f"fps={fps},{filter_scale},palettegen"
            filter_complex = f"fps={fps},{filter_scale}[x];[x][1:v]paletteuse"

            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                palette_file = tmp.name

            cmd_palette = [
                "ffmpeg", "-y", "-i", input_file,
                "-vf", palette_filter, palette_file
            ]
            subprocess.run(cmd_palette, check=True)

            cmd_gif = [
                "ffmpeg", "-y", "-i", input_file, "-i", palette_file,
                "-filter_complex", filter_complex, output_file
            ]
            subprocess.run(cmd_gif, check=True)
            os.remove(palette_file)

        elif mode == "Scale Percentage":
            percentage = scale_slider.get()
            factor = percentage / 100.0
            filter_scale = f"scale=iw*{factor}:ih*{factor}:flags=lanczos"
            palette_filter = f"fps={fps},{filter_scale},palettegen"
            filter_complex = f"fps={fps},{filter_scale}[x];[x][1:v]paletteuse"

            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                palette_file = tmp.name

            cmd_palette = [
                "ffmpeg", "-y", "-i", input_file,
                "-vf", palette_filter, palette_file
            ]
            subprocess.run(cmd_palette, check=True)

            cmd_gif = [
                "ffmpeg", "-y", "-i", input_file, "-i", palette_file,
                "-filter_complex", filter_complex, output_file
            ]
            subprocess.run(cmd_gif, check=True)
            os.remove(palette_file)

        elif mode == "Target File Size":
            # In this mode, we iteratively adjust the scale factor using a binary search
            # until the output file's size is close to the target (in MB).
            target_mb = target_slider.get()
            low = 0.1
            high = 1.0
            best_scale = None
            tolerance = max(0.05 * target_mb, 0.1)  # tolerance in MB
            iterations = 8

            for i in range(iterations):
                mid = (low + high) / 2
                temp_gif = tempfile.NamedTemporaryFile(
                    delete=False, suffix=".gif").name
                temp_palette = tempfile.NamedTemporaryFile(
                    delete=False, suffix=".png").name

                scale_filter = f"scale=iw*{mid}:ih*{mid}:flags=lanczos"
                palette_filter_iter = f"fps={fps},{scale_filter},palettegen"
                filter_complex_iter = f"fps={fps},{scale_filter}[x];[x][1:v]paletteuse"

                cmd_palette_iter = [
                    "ffmpeg", "-y", "-i", input_file,
                    "-vf", palette_filter_iter, temp_palette
                ]
                subprocess.run(cmd_palette_iter, check=True,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                cmd_gif_iter = [
                    "ffmpeg", "-y", "-i", input_file, "-i", temp_palette,
                    "-filter_complex", filter_complex_iter, temp_gif
                ]
                subprocess.run(
                    cmd_gif_iter, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                size_mb = os.path.getsize(temp_gif) / (1024 * 1024)

                os.remove(temp_palette)
                os.remove(temp_gif)

                if abs(size_mb - target_mb) <= tolerance:
                    best_scale = mid
                    break
                elif size_mb > target_mb:
                    high = mid
                else:
                    low = mid
                best_scale = mid  # Keep the last mid value

            scale_filter_final = f"scale=iw*{best_scale}:ih*{best_scale}:flags=lanczos"
            palette_filter_final = f"fps={fps},{scale_filter_final},palettegen"
            filter_complex_final = f"fps={fps},{scale_filter_final}[x];[x][1:v]paletteuse"

            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                final_palette = tmp.name

            cmd_palette_final = [
                "ffmpeg", "-y", "-i", input_file,
                "-vf", palette_filter_final, final_palette
            ]
            subprocess.run(cmd_palette_final, check=True)

            cmd_final = [
                "ffmpeg", "-y", "-i", input_file, "-i", final_palette,
                "-filter_complex", filter_complex_final, output_file
            ]
            subprocess.run(cmd_final, check=True)
            os.remove(final_palette)

        else:
            messagebox.showerror("Error", "Unknown resize mode selected.")
            return

        messagebox.showinfo("Success", "Conversion completed successfully!")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"Conversion failed:\n{e}")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred:\n{e}")

def start_resize_gif():
    global entry_input, entry_output, entry_fps, mode_var, entry_width, entry_height, scale_slider, target_slider, frame_resolution, frame_scale, frame_target
    # Set up the GUI.
    root = tk.Tk()
    root.title("GIF to GIF Converter with Resize Modes")
    root.wm_attributes('-toolwindow', 'True')  # Set as a tool window

    # Input file selection.
    tk.Label(root, text="Input GIF File:").grid(
        row=0, column=0, padx=5, pady=5, sticky="e")
    entry_input = tk.Entry(root, width=50)
    entry_input.grid(row=0, column=1, padx=5, pady=5)
    tk.Button(root, text="Browse", command=browse_input).grid(
        row=0, column=2, padx=5, pady=5)

    # Output file selection.
    tk.Label(root, text="Output GIF File:").grid(
        row=1, column=0, padx=5, pady=5, sticky="e")
    entry_output = tk.Entry(root, width=50)
    entry_output.grid(row=1, column=1, padx=5, pady=5)
    tk.Button(root, text="Browse", command=browse_output).grid(
        row=1, column=2, padx=5, pady=5)

    # FPS input.
    tk.Label(root, text="FPS:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
    entry_fps = tk.Entry(root)
    entry_fps.grid(row=2, column=1, padx=5, pady=5, sticky="w")
    entry_fps.insert(0, "30")  # default to 30 FPS

    # Dropdown for selecting resize mode.
    tk.Label(root, text="Resize Mode:").grid(
        row=3, column=0, padx=5, pady=5, sticky="e")
    mode_var = tk.StringVar(root)
    mode_options = ["Enter Resolution", "Scale Percentage", "Target File Size"]
    mode_var.set(mode_options[0])
    mode_menu = tk.OptionMenu(root, mode_var, *mode_options, command=update_mode)
    mode_menu.grid(row=3, column=1, padx=5, pady=5, sticky="w")

    # --- Frame for "Enter Resolution" mode ---
    frame_resolution = tk.Frame(root)
    tk.Label(frame_resolution, text="Width:").grid(row=0, column=0, padx=5, pady=5)
    entry_width = tk.Entry(frame_resolution, width=10)
    entry_width.grid(row=0, column=1, padx=5, pady=5)
    tk.Label(frame_resolution, text="Height:").grid(
        row=0, column=2, padx=5, pady=5)
    entry_height = tk.Entry(frame_resolution, width=10)
    entry_height.grid(row=0, column=3, padx=5, pady=5)
    entry_width.insert(0, "640")
    entry_height.insert(0, "480")

    # --- Frame for "Scale Percentage" mode ---
    frame_scale = tk.Frame(root)
    tk.Label(frame_scale, text="Scale Percentage:").grid(
        row=0, column=0, padx=5, pady=5)
    scale_slider = tk.Scale(frame_scale, from_=10, to=200, orient=tk.HORIZONTAL)
    scale_slider.set(100)  # 100% means no scaling.
    scale_slider.grid(row=0, column=1, padx=5, pady=5)

    # --- Frame for "Target File Size" mode ---
    frame_target = tk.Frame(root)
    tk.Label(frame_target, text="Target File Size (MB):").grid(
        row=0, column=0, padx=5, pady=5)
    target_slider = tk.Scale(frame_target, from_=0.1, to=20,
                            resolution=0.1, orient=tk.HORIZONTAL)
    target_slider.set(10)  # Default target of 10 MB.
    target_slider.grid(row=0, column=1, padx=5, pady=5)

    # Initially show the "Enter Resolution" frame.
    frame_resolution.grid(row=4, column=0, columnspan=3,
                        padx=5, pady=5, sticky="w")

    # Convert button.
    tk.Button(root, text="Convert", command=convert_gif).grid(
        row=5, column=1, padx=5, pady=15)

    root.mainloop()

if __name__ == "__main__":
    start_resize_gif()