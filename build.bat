@echo off
REM Rebuild the standalone double-clickable exe into dist\  (PySide6 / Qt build)
pyinstaller --noconfirm --onefile --windowed ^
  --name "PDF and Tools" ^
  --icon "pdf-and-tools.ico" ^
  --add-data "pdf-and-tools.ico;." ^
  --collect-all sklearn ^
  --exclude-module tkinter ^
  --exclude-module customtkinter ^
  --exclude-module PyQt5 ^
  --exclude-module PyQt6 ^
  app.py
echo.
echo Done. Exe is in dist\PDF and Tools.exe
pause
