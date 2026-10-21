"""Create a desktop shortcut for ffReal using the current project location."""

from pathlib import Path
import sys

import win32com.client


project_dir = Path(__file__).resolve().parent
desktop = Path.home() / "Desktop"
shortcut_path = desktop / "ffReal.lnk"
pythonw = Path(sys.executable).with_name("pythonw.exe")

shell = win32com.client.Dispatch("WScript.Shell")
shortcut = shell.CreateShortCut(str(shortcut_path))
shortcut.TargetPath = str(pythonw)
shortcut.Arguments = f'"{project_dir / "ffReal.pyw"}"'
shortcut.WorkingDirectory = str(project_dir)

icon = project_dir / "app_icon.ico"
if icon.exists():
    shortcut.IconLocation = f"{icon},0"

shortcut.Description = "ffReal — FocusForReal task timer"
shortcut.Save()
print(f"Created: {shortcut_path}")
