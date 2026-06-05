# -*- coding: utf-8 -*-
"""
Calibrate WorkBuddy input box position.
Run this script, move mouse onto WorkBuddy's input text box, press F12.
Coordinates will be saved to input_pos.cfg.
"""
import os
import sys
import time
import ctypes

APP_DIR = os.path.dirname(os.path.abspath(__file__))
CFG_FILE = os.path.join(APP_DIR, "input_pos.cfg")

u32 = ctypes.windll.user32
k32 = ctypes.windll.kernel32
VK_F12 = 0x7B

def get_cursor_pos():
    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
    pt = POINT()
    u32.GetCursorPos(ctypes.byref(pt))
    return (pt.x, pt.y)

def main():
    console = k32.GetConsoleWindow()

    print("=" * 50)
    print("  INPUT BOX CALIBRATION")
    print("  ----------------------")
    print("  1. Make sure WorkBuddy is open and visible")
    print("  2. Move your mouse ONTO the input text box")
    print("  3. Press F12 to save the position")
    print("  4. Press ESC to cancel")
    print("=" * 50)
    print("")

    # Minimize console so user can see WorkBuddy
    if console:
        u32.ShowWindow(console, 6)
        time.sleep(0.5)

    print("Waiting for F12... (mouse position will be recorded)")

    try:
        while True:
            time.sleep(0.05)

            # Check ESC
            if u32.GetAsyncKeyState(0x1B) & 0x8000:
                if console:
                    u32.ShowWindow(console, 9)
                print("Cancelled.")
                return

            # Check F12
            if u32.GetAsyncKeyState(VK_F12) & 0x8000:
                x, y = get_cursor_pos()
                print("")
                print("  F12 pressed!")
                print("  Mouse position: ({}, {})".format(x, y))
                print("  Saving to: {}".format(CFG_FILE))

                with open(CFG_FILE, "w", encoding="utf-8") as f:
                    f.write("{} {}\n".format(x, y))

                print("  Done! You can now run voice_wake.py")
                time.sleep(2)
                if console:
                    u32.ShowWindow(console, 9)
                return

    except KeyboardInterrupt:
        if console:
            u32.ShowWindow(console, 9)
        print("Cancelled.")

if __name__ == "__main__":
    main()
