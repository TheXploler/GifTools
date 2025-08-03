import os
import shutil
import subprocess
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox


class GifEditor(tk.Toplevel):
    def __init__(self):
        super().__init__()
        self.title("GIF Frame Editor")
        self.geometry("800x600")
        self.wm_attributes('-toolwindow', 'True')  # Set as a tool window
        # Each item: { "path": <file path>, "var": BooleanVar, "widget": <Frame> }
        self.frames_info = []
        self.temp_dir = None
        self.create_menu()
        self.create_widgets()

    def create_menu(self):
        menubar = tk.Menu(self)
        # File Menu: open/reassemble/export/exit
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open GIF", command=self.open_gif)
        file_menu.add_command(label="Reassemble GIF",
                              command=self.reassemble_gif)
        file_menu.add_command(label="Export Frames",
                              command=self.export_frames)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # Actions Menu: add, remove, select all
        actions_menu = tk.Menu(menubar, tearoff=0)
        actions_menu.add_command(label="Add Frame", command=self.add_frame)
        actions_menu.add_command(
            label="Remove Selected Frames", command=self.remove_selected)
        actions_menu.add_command(label="Select All", command=self.select_all)
        menubar.add_cascade(label="Actions", menu=actions_menu)

        self.config(menu=menubar)

    def create_widgets(self):
        # Control frame for FPS entry and Reassemble button (duplicate of the menu option)
        control_frame = tk.Frame(self)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        tk.Label(control_frame, text="FPS:").pack(side=tk.LEFT, padx=5)
        self.fps_entry = tk.Entry(control_frame, width=5)
        self.fps_entry.pack(side=tk.LEFT, padx=5)
        self.fps_entry.insert(0, "10")
        tk.Button(control_frame, text="Reassemble GIF",
                  command=self.reassemble_gif).pack(side=tk.LEFT, padx=5)

        # Canvas with scrollbar for displaying frame thumbnails
        self.canvas = tk.Canvas(self, borderwidth=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar = tk.Scrollbar(
            self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.thumb_container = tk.Frame(self.canvas)
        self.canvas.create_window(
            (0, 0), window=self.thumb_container, anchor="nw")
        self.thumb_container.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))

    def open_gif(self):
        gif_path = filedialog.askopenfilename(
            title="Select GIF file", filetypes=[("GIF files", "*.gif")])
        if not gif_path:
            return

        # Create or recreate the temporary directory for frames
        if self.temp_dir:
            shutil.rmtree(self.temp_dir)
        self.temp_dir = tempfile.mkdtemp(prefix="gif_editor_")

        # Extract frames as PPM images (tkinter natively supports PPM)
        extract_pattern = os.path.join(self.temp_dir, "frame_%03d.ppm")
        cmd = ["ffmpeg", "-i", gif_path, extract_pattern]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Error extracting frames:\n{e}")
            return

        # Clear previous frames from UI and internal list
        for widget in self.thumb_container.winfo_children():
            widget.destroy()
        self.frames_info.clear()

        # Load extracted frames (sorted by filename) into the UI
        files = sorted([f for f in os.listdir(self.temp_dir)
                       if f.startswith("frame_") and f.endswith(".ppm")])
        for file in files:
            path = os.path.join(self.temp_dir, file)
            self.add_frame_to_list(path)
        messagebox.showinfo(
            "Frames Loaded", f"Loaded {len(self.frames_info)} frames from the GIF.")

    def add_frame_to_list(self, path):
        # Create a UI container for the frame thumbnail and a deletion checkbox
        frame_ui = tk.Frame(self.thumb_container, bd=2, relief=tk.RIDGE)
        frame_ui.pack(padx=5, pady=5, side=tk.TOP, anchor="w")
        try:
            # Load the image; tkinter's PhotoImage supports PPM files
            img = tk.PhotoImage(file=path)
            # Use subsample to create a thumbnail if the image is large
            factor = max(img.width() // 100, img.height() // 100)
            thumb = img.subsample(factor, factor) if factor > 1 else img
        except Exception as e:
            messagebox.showerror(
                "Error", f"Error loading image:\n{e}\nFile: {path}")
            return
        label = tk.Label(frame_ui, image=thumb)
        label.image = thumb  # Keep a reference so it doesn't get garbage-collected
        label.pack(side=tk.LEFT)
        var = tk.BooleanVar(value=False)
        chk = tk.Checkbutton(frame_ui, text="Delete", variable=var)
        chk.pack(side=tk.LEFT, padx=5)
        self.frames_info.append({"path": path, "var": var, "widget": frame_ui})

    def remove_selected(self):
        # Remove from UI and internal list all frames marked for deletion
        to_remove = [fi for fi in self.frames_info if fi["var"].get()]
        for fi in to_remove:
            fi["widget"].destroy()
            self.frames_info.remove(fi)
        messagebox.showinfo("Removed", f"Removed {len(to_remove)} frame(s).")

    def select_all(self):
        # Mark all frames' checkboxes as selected
        for fi in self.frames_info:
            fi["var"].set(True)
        messagebox.showinfo("Select All", "All frames have been selected.")

    def add_frame(self):
        # Allow the user to add a frame from an image file
        img_path = filedialog.askopenfilename(
            title="Select image file",
            filetypes=[("Image files", "*.ppm;*.gif;*.png;*.jpg;*.jpeg")]
        )
        if not img_path:
            return
        if not self.temp_dir:
            self.temp_dir = tempfile.mkdtemp(prefix="gif_editor_")
        new_index = len(self.frames_info) + 1
        new_filename = f"frame_added_{new_index:03d}.ppm"
        dest = os.path.join(self.temp_dir, new_filename)
        # Convert the selected image to PPM using ffmpeg so that tkinter can load it
        cmd = ["ffmpeg", "-y", "-i", img_path, dest]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            messagebox.showerror(
                "Error", f"Error converting image to PPM:\n{e}")
            return
        self.add_frame_to_list(dest)
        messagebox.showinfo("Frame Added", "New frame added successfully.")

    def reassemble_gif(self):
        if not self.frames_info:
            messagebox.showerror("Error", "No frames available to assemble!")
            return
        fps = self.fps_entry.get()
        try:
            fps_val = float(fps)
        except ValueError:
            messagebox.showerror("Error", "Invalid FPS value!")
            return

        output_file = filedialog.asksaveasfilename(
            title="Save output GIF", defaultextension=".gif",
            filetypes=[("GIF files", "*.gif")]
        )
        if not output_file:
            return

        # Create a temporary folder to hold sequentially renamed frames
        assemble_dir = tempfile.mkdtemp(prefix="gif_assemble_")
        for idx, fi in enumerate(self.frames_info):
            new_name = os.path.join(assemble_dir, f"frame_{idx:03d}.ppm")
            shutil.copy(fi["path"], new_name)

        # Use ffmpeg to combine the frames into a GIF
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(fps_val),
            "-i", os.path.join(assemble_dir, "frame_%03d.ppm"),
            "-loop", "0",
            output_file
        ]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
            messagebox.showinfo("Success", f"New GIF saved as:\n{output_file}")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Error reassembling GIF:\n{e}")
        shutil.rmtree(assemble_dir)

    def export_frames(self):
        # Allow the user to export (extract) the current frames to a chosen folder
        if not self.frames_info:
            messagebox.showerror("Error", "No frames available to export!")
            return
        dest_dir = filedialog.askdirectory(
            title="Select folder to export frames")
        if not dest_dir:
            return
        for idx, fi in enumerate(self.frames_info):
            filename = f"frame_{idx:03d}.ppm"
            shutil.copy(fi["path"], os.path.join(dest_dir, filename))
        messagebox.showinfo(
            "Exported", f"Exported {len(self.frames_info)} frames to {dest_dir}.")


def start_edit_gif_frames():
    app = GifEditor()
    app.mainloop()


if __name__ == "__main__":
    start_edit_gif_frames()
