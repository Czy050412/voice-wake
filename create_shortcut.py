# -*- coding: utf-8 -*-
"""Create desktop shortcut for Voice Wake start.bat"""
import os, sys
import pythoncom
from win32com.shell import shell, shellcon

desktop = shell.SHGetFolderPath(0, shellcon.CSIDL_DESKTOP, None, 0)
link_path = os.path.join(desktop, "Voice Wake.lnk")
script_dir = r"F:\Agent\Claw\voice_wake"
bat_path = os.path.join(script_dir, "start.bat")
icon_path = os.path.join(script_dir, "voice_overlay.py")  # fallback

shortcut = pythoncom.CoCreateInstance(
    shell.CLSID_ShellLink,
    None,
    pythoncom.CLSCTX_INPROC_SERVER,
    shell.IID_IShellLink,
)
shortcut.SetPath(bat_path)
shortcut.SetWorkingDirectory(script_dir)
shortcut.SetDescription("Voice Wake - 语音助手启动")
shortcut.SetIconLocation(os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "System32", "SHELL32.dll"), 132)
shortcut.QueryInterface(pythoncom.IID_IPersistFile).Save(link_path, 0)
print("Shortcut created: {}".format(link_path))
