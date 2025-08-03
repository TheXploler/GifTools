import tkinter as tk
from tkinter import filedialog, messagebox
import os
from pygifsicle import gifsicle
import ttkbootstrap as ttk


def browse_input():
    file_path = filedialog.askopenfilename(filetypes=[("GIF files", "*.gif")])
    if file_path:
        entry_input.delete(0, ttk.END)
        entry_input.insert(0, file_path)


def browse_output():
    file_path = filedialog.asksaveasfilename(
        defaultextension=".gif", filetypes=[("GIF files", "*.gif")])
    if file_path:
        entry_output.delete(0, ttk.END)
        entry_output.insert(0, file_path)


def compress_gif():
    input_file = entry_input.get()
    output_file = entry_output.get()

    if not os.path.exists(input_file):
        messagebox.showerror("Error", "Input file does not exist.")
        return
    if not output_file:
        messagebox.showerror("Error", "Please specify an output file.")
        return

    color_count = entry_color_count.get() if var_color.get() else None
    quality = entry_quality.get() if var_lossy.get() else None

    try:
        # Set up options for gifsicle
        options = {
            'sources': [input_file],
            'destination': output_file,
            'optimize': True,
        }

        if color_count is not None:
            options['colors'] = int(color_count)
        if quality is not None:
            options['options'] = [f'--lossy={int(quality)}']

        gifsicle(**options)  # Use the gifsicle function with options as kwargs

        messagebox.showinfo("Success", "Compression completed successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred:\n{e}")
        print(f"Error: {e}")


def toggle_options():
    if var_color.get():
        label_color_count.grid(row=7, column=0, padx=5, pady=5, sticky="e")
        slider_color_count.grid(row=7, column=1, padx=5, pady=5, sticky="w")
        entry_color_count.grid(row=7, column=2, padx=5, pady=5, sticky="w")
    else:
        label_color_count.grid_forget()
        slider_color_count.grid_forget()
        entry_color_count.grid_forget()

    if var_lossy.get():
        label_quality.grid(row=8, column=0, padx=5, pady=5, sticky="e")
        slider_quality.grid(row=8, column=1, padx=5, pady=5, sticky="w")
        entry_quality.grid(row=8, column=2, padx=5, pady=5, sticky="w")
    else:
        label_quality.grid_forget()
        slider_quality.grid_forget()
        entry_quality.grid_forget()


def update_color_count(value):
    entry_color_count.delete(0, ttk.END)
    entry_color_count.insert(0, value)


def update_quality(value):
    entry_quality.delete(0, ttk.END)
    entry_quality.insert(0, value)


# Set up the GUI
root = ttk.Window(themename="superhero")
root.title("GIF Compressor")
root.wm_attributes('-toolwindow', 'True')  # Set as a tool window

# Input file selection
ttk.Label(root, text="Input GIF File:").grid(
    row=0, column=0, padx=5, pady=5, sticky="e")
entry_input = ttk.Entry(root, width=50)
entry_input.grid(row=0, column=1, padx=5, pady=5)
ttk.Button(root, text="Browse", command=browse_input).grid(
    row=0, column=2, padx=5, pady=5)

# Output file selection
ttk.Label(root, text="Output GIF File:").grid(
    row=1, column=0, padx=5, pady=5, sticky="e")
entry_output = ttk.Entry(root, width=50)
entry_output.grid(row=1, column=1, padx=5, pady=5)
ttk.Button(root, text="Browse", command=browse_output).grid(
    row=1, column=2, padx=5, pady=5)

# Color reduction option
var_color = ttk.BooleanVar()
ttk.Checkbutton(root, text="Enable Color Reduction", variable=var_color,
               command=toggle_options).grid(row=6, column=1, padx=5, pady=5, sticky="w")
label_color_count = ttk.Label(root, text="Color Count (2-256):")
slider_color_count = tk.Scale(
    root, from_=2, to=256, orient=ttk.HORIZONTAL, command=update_color_count)
entry_color_count = ttk.Entry(root)
entry_color_count.insert(0, "2")  # default value

# Lossy GIF option
var_lossy = ttk.BooleanVar()
ttk.Checkbutton(root, text="Enable Lossy GIF", variable=var_lossy,
               command=toggle_options).grid(row=6, column=2, padx=5, pady=5, sticky="w")
label_quality = ttk.Label(root, text="Quality (30-200):")
slider_quality = tk.Scale(root, from_=30, to=200,
                          orient=ttk.HORIZONTAL, command=update_quality)
entry_quality = ttk.Entry(root)
entry_quality.insert(0, "30")  # default value

# Compress button
ttk.Button(root, text="Compress", command=compress_gif).grid(
    row=9, column=1, padx=5, pady=15)

root.mainloop()
