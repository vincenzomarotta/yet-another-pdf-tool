# Yet another Pdf Tool

The internet has roughly nine hundred billion PDF tools. Here's nine hundred billion and one.

In my defense, this one runs offline, costs nothing, has no ads, no "upload your file to our servers," no watermark on the free tier (because there is no tier), and no popup begging you to go Premium. It's just a window with buttons. You click a button, a thing happens to your PDF. Revolutionary.

A small desktop toolbox (PySide6 / Qt) wrapping 22 PDF and image tools.

## What's in the box

- **Organize** — Merge, Split, Remove duplicate pages, Reorder, Delete pages, Rotate
- **Optimize & Secure** — Compress PDF, Password protect (AES-256), Watermark, Page numbers, Watermark image, Compress image
- **Convert** — Extract images, PDF to images, Images to PDF, Extract text, HTML to PDF, Resize image, Convert image (JPG - PNG - WebP - BMP), Crop image
- **Create** — QR code generator, Color palette extractor

Drag-and-drop files onto any tool, drag to reorder lists (Merge, Images to PDF), and add as many page-range boxes as you need (Split, Delete, Rotate, Reorder). 

Dark/light theme and English/Italian, both in Settings.

## Just run it

Grab `dist/PDF and Tools.exe` and double-click. Standalone — nothing to install. Hand that single file to anyone on Windows and it works.

## Run from source

Needs Python 3.10+.

```powershell
pip install pyside6 pymupdf pillow qrcode scikit-learn imagehash
python app.py
```

## Build the .exe yourself

Install the deps above plus PyInstaller:

```powershell
pip install pyinstaller
```

Then double-click `build.bat`, or run it:

```powershell
.\build.bat
```

Output lands at `dist\PDF and Tools.exe` (~130 MB, one file). Takes a couple of minutes.

Under the hood `build.bat` is one PyInstaller call:

```
pyinstaller --noconfirm --onefile --windowed --name "PDF and Tools" ^
  --icon "pdf-and-tools.ico" --add-data "pdf-and-tools.ico;." ^
  --collect-all sklearn ^
  --exclude-module tkinter --exclude-module customtkinter ^
  --exclude-module PyQt5 --exclude-module PyQt6 app.py
```

- `--onefile --windowed` — single .exe, no console window
- `--collect-all sklearn` — scikit-learn (color palette) isn't auto-detected, so force it in
- `--exclude-module …` — drop unused toolkits to keep the size down

## Layout

- `app.py` — the whole UI
- `pdf_tools.py` — the actual PDF/image logic (no UI), import and reuse it however you like
- `build.bat` — the build command

Want to change a tool's icon? Edit the glyph in `_tools()` near the top of `app.py`, then rebuild.
