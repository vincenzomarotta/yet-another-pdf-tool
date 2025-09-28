import customtkinter as ctk
from tkinter import filedialog, messagebox
import winreg

def open_pdf():
    file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
    if file_path:
        messagebox.showinfo("File Selected", f"You chose:\n{file_path}")

def save_pdf():
    save_path = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF files", "*.pdf")],
        title="Save PDF as..."
    )
    if save_path:
        messagebox.showinfo("Saved", f"File will be saved to:\n{save_path}")

def process_pdf():
    pass

def is_dark_mode():
    try:
        registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
        key = winreg.OpenKey(registry, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return value == 0  # 0 = Dark Mode, 1 = Light Mode
    except Exception:
        return False  # default to light


# --- Setup CustomTkinter ---
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

root = ctk.CTk()
root.title("Tool & Utilities")
root.geometry("500x300")

frame = ctk.CTkFrame(root)
frame.place(relx=0.5, rely=0.5, anchor="center")

frame.grid_rowconfigure((0,1,2), weight=1)
frame.grid_columnconfigure((0,1), weight=1)

# Configure grid so buttons expand equally
frame.grid_rowconfigure((0, 1), weight=1)
frame.grid_columnconfigure((0, 1), weight=1)

# --- Buttons ---
btn1 = ctk.CTkButton(frame, text="Open PDF", command=open_pdf)
btn1.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

btn2 = ctk.CTkButton(frame, text="Save PDF", command=save_pdf)
btn2.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

btn3 = ctk.CTkButton(frame, text="Process PDF")
btn3.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

btn4 = ctk.CTkButton(frame, text="Exit", command=root.quit)
btn4.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")


root.mainloop()
