import tkinter as tk
from tkinter import filedialog, colorchooser, ttk, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageSequence
import os


class GifTextEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("GIF Text Editor")

        self.gif_image = None
        self.frames = []
        self.duration = 100
        self.preview_image = None

        self.text_x = 50
        self.text_y = 50

        self.text_var = tk.StringVar(value="Enter your text here")
        self.font_var = tk.StringVar(value="Arial")
        self.font_size_var = tk.IntVar(value=40)
        self.font_color = "#FFFFFF"
        self.textbox_width_var = tk.IntVar(value=300)

        self.shadow_enabled = tk.BooleanVar(value=False)
        self.shadow_size_var = tk.IntVar(value=2)
        self.shadow_color = "#000000"

        self.stroke_enabled = tk.BooleanVar(value=False)
        self.stroke_size_var = tk.IntVar(value=2)
        self.stroke_color = "#000000"

        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.dragging = False

        control_frame = tk.Frame(root)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        preview_frame = tk.Frame(root, bd=2, relief=tk.SUNKEN)
        preview_frame.pack(side=tk.RIGHT, padx=5, pady=5)

        self.canvas = tk.Canvas(
            preview_frame, width=500, height=500, bg="grey")
        self.canvas.pack()
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)

        load_btn = tk.Button(
            control_frame, text="Load GIF", command=self.load_gif)
        load_btn.pack(pady=2, fill=tk.X)

        tk.Label(control_frame, text="Text:").pack(anchor="w")
        text_entry = tk.Entry(
            control_frame, textvariable=self.text_var, width=40)
        text_entry.pack(pady=2)
        self.text_var.trace_add("write", lambda *args: self.update_preview())

        tk.Label(control_frame, text="Font:").pack(anchor="w")
        font_choices = ["Arial", "Times New Roman", "Courier New"]
        font_menu = ttk.OptionMenu(control_frame, self.font_var, self.font_var.get(), *font_choices,
                                   command=lambda _: self.update_preview())
        font_menu.pack(pady=2, fill=tk.X)

        tk.Label(control_frame, text="Font Size:").pack(anchor="w")
        tk.Spinbox(control_frame, from_=10, to=200, textvariable=self.font_size_var,
                   command=self.update_preview).pack(pady=2, fill=tk.X)

        tk.Button(control_frame, text="Choose Font Color",
                  command=self.choose_font_color).pack(pady=2, fill=tk.X)

        tk.Label(control_frame, text="Textbox Width (px):").pack(anchor="w")
        tk.Spinbox(control_frame, from_=50, to=1000, textvariable=self.textbox_width_var,
                   command=self.update_preview).pack(pady=2, fill=tk.X)

        tk.Checkbutton(control_frame, text="Enable Shadow", variable=self.shadow_enabled,
                       command=self.update_preview).pack(anchor="w")
        tk.Label(control_frame, text="Shadow Size:").pack(anchor="w")
        tk.Spinbox(control_frame, from_=1, to=20, textvariable=self.shadow_size_var,
                   command=self.update_preview).pack(pady=2, fill=tk.X)
        tk.Button(control_frame, text="Choose Shadow Color",
                  command=self.choose_shadow_color).pack(pady=2, fill=tk.X)

        tk.Checkbutton(control_frame, text="Enable Stroke", variable=self.stroke_enabled,
                       command=self.update_preview).pack(anchor="w")
        tk.Label(control_frame, text="Stroke Size:").pack(anchor="w")
        tk.Spinbox(control_frame, from_=1, to=20, textvariable=self.stroke_size_var,
                   command=self.update_preview).pack(pady=2, fill=tk.X)
        tk.Button(control_frame, text="Choose Stroke Color",
                  command=self.choose_stroke_color).pack(pady=2, fill=tk.X)

        export_btn = tk.Button(
            control_frame, text="Export GIF", command=self.export_gif)
        export_btn.pack(pady=10, fill=tk.X)

    def load_gif(self):
        path = filedialog.askopenfilename(filetypes=[("GIF files", "*.gif")])
        if not path:
            return
        try:
            self.gif_image = Image.open(path)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open GIF: {e}")
            return

        self.frames = []
        try:
            for frame in ImageSequence.Iterator(self.gif_image):
                self.frames.append(frame.copy().convert("RGBA"))
            self.duration = self.gif_image.info.get("duration", 100)
        except Exception as e:
            messagebox.showerror("Error", f"Error processing GIF frames: {e}")
            return

        w, h = self.frames[0].size
        self.canvas.config(width=w, height=h)
        self.text_x, self.text_y = 50, 50
        self.update_preview()

    def choose_font_color(self):
        color = colorchooser.askcolor()[1]
        if color:
            self.font_color = color
            self.update_preview()

    def choose_shadow_color(self):
        color = colorchooser.askcolor()[1]
        if color:
            self.shadow_color = color
            self.update_preview()

    def choose_stroke_color(self):
        color = colorchooser.askcolor()[1]
        if color:
            self.stroke_color = color
            self.update_preview()

    def get_font(self, size):
        font_name = self.font_var.get()
        font_file = None
        if font_name.lower() == "arial":
            font_file = "arial.ttf"
        elif font_name.lower() == "times new roman":
            font_file = "times.ttf"
        elif font_name.lower() == "courier new":
            font_file = "cour.ttf"
        try:
            return ImageFont.truetype(font_file, size)
        except Exception as e:
            print(f"Warning: {e}. Falling back to default font.")
            return ImageFont.load_default()

    def wrap_text(self, text, font, max_width):
        words = text.split()
        lines = []
        line = ""
        # Create a temporary image for text measurement
        temp_img = Image.new("RGB", (1, 1))
        draw = ImageDraw.Draw(temp_img)
        for word in words:
            test_line = line + " " + word if line else word
            bbox = draw.textbbox((0, 0), test_line, font=font)
            w = bbox[2] - bbox[0]
            if w <= max_width:
                line = test_line
            else:
                if line:
                    lines.append(line)
                line = word
        if line:
            lines.append(line)
        return "\n".join(lines)

    def get_multiline_text_size(self, text, font):
        temp_img = Image.new("RGB", (1, 1))
        draw = ImageDraw.Draw(temp_img)
        try:
            bbox = draw.multiline_textbbox((0, 0), text, font=font)
            return (bbox[2] - bbox[0], bbox[3] - bbox[1])
        except AttributeError:
            # Fallback: calculate size line-by-line
            lines = text.split('\n')
            max_width = 0
            total_height = 0
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                line_width = bbox[2] - bbox[0]
                line_height = bbox[3] - bbox[1]
                max_width = max(max_width, line_width)
                total_height += line_height
            return (max_width, total_height)

    def update_preview(self):
        if not self.frames:
            return
        preview = self.frames[0].copy()
        draw = ImageDraw.Draw(preview)
        font_size = self.font_size_var.get()
        font = self.get_font(font_size)
        textbox_width = self.textbox_width_var.get()
        text = self.text_var.get()
        wrapped_text = self.wrap_text(text, font, textbox_width)

        # Calculate text size (for dragging bounds)
        text_size = self.get_multiline_text_size(wrapped_text, font)

        if self.shadow_enabled.get():
            shadow_offset = self.shadow_size_var.get()
            shadow_pos = (self.text_x + shadow_offset,
                          self.text_y + shadow_offset)
            draw.multiline_text(shadow_pos, wrapped_text,
                                font=font, fill=self.shadow_color)
        if self.stroke_enabled.get():
            draw.multiline_text((self.text_x, self.text_y), wrapped_text, font=font,
                                fill=self.font_color, stroke_width=self.stroke_size_var.get(),
                                stroke_fill=self.stroke_color)
        else:
            draw.multiline_text((self.text_x, self.text_y),
                                wrapped_text, font=font, fill=self.font_color)

        self.preview_image = ImageTk.PhotoImage(preview)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.preview_image)

    def on_mouse_down(self, event):
        font = self.get_font(self.font_size_var.get())
        wrapped_text = self.wrap_text(
            self.text_var.get(), font, self.textbox_width_var.get())
        text_size = self.get_multiline_text_size(wrapped_text, font)
        x0, y0 = self.text_x, self.text_y
        x1, y1 = x0 + text_size[0], y0 + text_size[1]
        if x0 <= event.x <= x1 and y0 <= event.y <= y1:
            self.dragging = True
            self.drag_offset_x = event.x - self.text_x
            self.drag_offset_y = event.y - self.text_y

    def on_mouse_drag(self, event):
        if self.dragging:
            self.text_x = event.x - self.drag_offset_x
            self.text_y = event.y - self.drag_offset_y
            self.update_preview()

    def export_gif(self):
        if not self.frames:
            messagebox.showwarning("Warning", "No GIF loaded.")
            return

        out_path = filedialog.asksaveasfilename(defaultextension=".gif",
                                                filetypes=[("GIF files", "*.gif")])
        if not out_path:
            return

        new_frames = []
        font_size = self.font_size_var.get()
        font = self.get_font(font_size)
        textbox_width = self.textbox_width_var.get()
        text = self.text_var.get()
        wrapped_text = self.wrap_text(text, font, textbox_width)

        for frame in self.frames:
            frame = frame.copy().convert("RGBA")
            draw = ImageDraw.Draw(frame)
            if self.shadow_enabled.get():
                shadow_offset = self.shadow_size_var.get()
                shadow_pos = (self.text_x + shadow_offset,
                              self.text_y + shadow_offset)
                draw.multiline_text(shadow_pos, wrapped_text,
                                    font=font, fill=self.shadow_color)
            if self.stroke_enabled.get():
                draw.multiline_text((self.text_x, self.text_y), wrapped_text, font=font,
                                    fill=self.font_color, stroke_width=self.stroke_size_var.get(),
                                    stroke_fill=self.stroke_color)
            else:
                draw.multiline_text((self.text_x, self.text_y),
                                    wrapped_text, font=font, fill=self.font_color)
            new_frames.append(frame)

        try:
            new_frames[0].save(out_path, save_all=True, append_images=new_frames[1:],
                               duration=self.duration, loop=0, disposal=2)
            messagebox.showinfo(
                "Success", f"Exported GIF saved to:\n{out_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export GIF:\n{e}")


def start_add_text_to_gif():
    root = tk.Toplevel()
    app = GifTextEditor(root)
    root.mainloop()


if __name__ == "__main__":
    start_add_text_to_gif()
