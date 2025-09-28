import tkinter as tk
from tkinterdnd2 import DND_FILES, TkinterDnD
from tkinter import filedialog, messagebox
import shutil
import os

def process_pdf(file_path):
    # Example: just copy the PDF to a chosen location
    save_path = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF files", "*.pdf")],
        initialfile=os.path.basename(file_path).replace(".pdf", "_processed.pdf"),
        title="Save processed PDF as..."
    )

    if save_path:
        shutil.copy(file_path, save_path)
        messagebox.showinfo("Success", f"Processed PDF saved as:\n{save_path}")
    else:
        messagebox.showinfo("Cancelled", "Save operation cancelled.")

def drop(event):
    file_path = event.data.strip("{}")  # Handles spaces in filenames
    if file_path.lower().endswith(".pdf"):
        process_pdf(file_path)
    else:
        messagebox.showerror("Error", "Please drop a PDF file")

root = TkinterDnD.Tk()
root.title("PDF Tool")
root.geometry("400x200")

label = tk.Label(root, text="Drag and drop a PDF here", width=40, height=10, relief="ridge")
label.pack(pady=20)

label.drop_target_register(DND_FILES)
label.dnd_bind("<<Drop>>", drop)

root.mainloop()
