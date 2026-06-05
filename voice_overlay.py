# -*- coding: utf-8 -*-
"""
Voice Overlay v5 - tkinter Canvas + transparentcolor + PIL rendering
  - Proven approach: Canvas bg="black" + transparentcolor="black" = true transparency
  - WS_EX_TRANSPARENT for click-through
  - Second (right) monitor positioning
  - Single-instance PID lock
  - Always-on standby display
"""
import os, sys, time, threading, ctypes

APP_DIR = os.path.dirname(os.path.abspath(__file__))
TEXT_FILE = os.path.join(APP_DIR, "overlay_text.txt")
LOCK_FILE = os.path.join(APP_DIR, "overlay.lock")
LOG_FILE = os.path.join(APP_DIR, "overlay.log")

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

import tkinter as tk
from PIL import Image, ImageDraw, ImageFont, ImageTk


def log(msg):
    line = "[{}] {}".format(time.strftime("%H:%M:%S"), msg)
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def process_exists(pid):
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    STILL_ACTIVE = 259
    handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return False
    try:
        status = ctypes.c_ulong()
        ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(status))
        return status.value == STILL_ACTIVE
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


def acquire_lock():
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, "r") as f:
                old_pid = int(f.read().strip())
            if process_exists(old_pid):
                log("Another overlay running (PID {}), exiting.".format(old_pid))
                sys.exit(0)
            else:
                log("Stale lock (PID {} dead), taking over.".format(old_pid))
        except Exception:
            pass
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))
    log("Lock acquired (PID {})".format(os.getpid()))


def release_lock():
    try:
        if os.path.exists(LOCK_FILE):
            os.unlink(LOCK_FILE)
    except Exception:
        pass


def get_monitors():
    u32 = ctypes.windll.user32
    primary_w = u32.GetSystemMetrics(0)
    primary_h = u32.GetSystemMetrics(1)
    virtual_w = u32.GetSystemMetrics(78)
    virtual_h = u32.GetSystemMetrics(79)
    virtual_x = u32.GetSystemMetrics(76)
    virtual_y = u32.GetSystemMetrics(77)
    monitors = [{"x": virtual_x, "y": virtual_y, "w": primary_w, "h": primary_h, "primary": True}]
    if virtual_w > primary_w:
        monitors.append({"x": virtual_x + primary_w, "y": virtual_y, "w": virtual_w - primary_w, "h": virtual_h, "primary": False})
    elif virtual_x < 0:
        monitors.append({"x": 0, "y": virtual_y, "w": -virtual_x, "h": virtual_h, "primary": False})
    return monitors


class VoiceOverlay:
    WIDTH = 1020
    HEIGHT = 100
    FG_MAIN = (255, 255, 255, 255)
    FG_WAKE = (0, 255, 136, 255)      # Bright green for wake
    FG_DIM = (255, 255, 255, 200)      # White dim
    FG_STANDBY = (255, 255, 255, 180)  # White muted for idle
    FONT_SIZE = 22
    FONT_SIZE2 = 18
    FADE_AFTER = 10

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.resizable(False, False)

        # Position on second monitor
        monitors = get_monitors()
        log("Monitors: {}".format(monitors))
        mon = monitors[1] if len(monitors) >= 2 else monitors[0]
        self.x_pos = mon["x"] + 20
        self.y_pos = mon["y"] + 20
        self.root.geometry("{}x{}+{}+{}".format(self.WIDTH, self.HEIGHT, self.x_pos, self.y_pos))

        # Canvas with black bg (will be made transparent)
        self.canvas = tk.Canvas(self.root, width=self.WIDTH, height=self.HEIGHT,
                                bg="black", highlightthickness=0, bd=0)
        self.canvas.pack()

        # Make black pixels transparent
        self.root.attributes("-transparentcolor", "black")

        # Click-through
        self.root.after(500, self._click_through)

        # Fonts
        self.font = self._load_font("msyhbd.ttc", self.FONT_SIZE)
        self.font2 = self._load_font("msyh.ttc", self.FONT_SIZE2)

        # Initial render
        self.last_update = time.time()
        self.running = True
        self._show_standby()

        # File watcher + standby loop
        threading.Thread(target=self._watch, daemon=True).start()
        self._standby_loop()

        log("Position: x={}, y={} on {}".format(self.x_pos, self.y_pos,
             "2nd monitor" if len(monitors) >= 2 else "primary"))

    def _load_font(self, name, size):
        for d in [os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts"), r"C:\Windows\Fonts"]:
            path = os.path.join(d, name)
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, size)
                except Exception:
                    pass
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            log("Font '{}' not found, using default.".format(name))
            return ImageFont.load_default()

    def _render_text(self, line1, line2, color1=None, color2=None):
        if color1 is None:
            color1 = self.FG_MAIN
        if color2 is None:
            color2 = self.FG_DIM
        img = Image.new("RGBA", (self.WIDTH, self.HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        if line1:
            draw.text((20, 15), line1, fill=color1, font=self.font)
        if line2:
            draw.text((20, 55), line2, fill=color2, font=self.font2)
        self._photo = ImageTk.PhotoImage(img)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self._photo)

    def _show_standby(self):
        self._render_text("语音待机中...", '说 "狗蛋" 唤醒', self.FG_STANDBY)

    def _click_through(self):
        try:
            hwnd = self.root.winfo_id()
            u32 = ctypes.windll.user32
            parent = u32.GetParent(hwnd)
            if parent:
                buf = ctypes.create_unicode_buffer(256)
                u32.GetClassNameW(parent, buf, 256)
                if buf.value.startswith("TkTop"):
                    hwnd = parent
            ex = u32.GetWindowLongW(hwnd, -20)
            u32.SetWindowLongW(hwnd, -20, ex | 0x20 | 0x80000 | 0x80)
            u32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0020 | 0x0001 | 0x0002 | 0x0040)
            log("Click-through OK (hwnd={})".format(hwnd))
        except Exception as e:
            log("Click-through error: {}".format(e))

    def _watch(self):
        last_mtime = 0
        while self.running:
            try:
                if os.path.exists(TEXT_FILE):
                    mt = os.path.getmtime(TEXT_FILE)
                    if mt > last_mtime:
                        last_mtime = mt
                        with open(TEXT_FILE, "r", encoding="utf-8") as f:
                            content = f.read().strip()
                        if content:
                            self.root.after(0, self._update, content)
            except Exception:
                pass
            time.sleep(0.15)

    def _update(self, content):
        self.last_update = time.time()
        line = content.strip()
        if line.startswith("[Listening]"):
            self._render_text("正在收听...", "", self.FG_DIM)
        elif line.startswith("[Heard]"):
            self._render_text(line[7:].strip(), "", self.FG_MAIN)
        elif line.startswith("[Wake]"):
            self._render_text("狗蛋 > " + (line[6:].strip() or "请说话..."), "", self.FG_WAKE)
        elif line.startswith("[Sending]"):
            t = line[9:].strip()
            if len(t) > 80:
                t = t[:77] + "..."
            self._render_text("发送: " + t, "", self.FG_WAKE)
        elif line.startswith("[CMD]"):
            self._render_text(line[5:].strip(), "", self.FG_MAIN)
        elif line.startswith("[TTS]"):
            self._render_text("", line[5:].strip(), self.FG_MAIN, self.FG_DIM)
        else:
            self._render_text(line, "", self.FG_MAIN)

    def _standby_loop(self):
        if not self.running:
            return
        if time.time() - self.last_update >= self.FADE_AFTER:
            self._show_standby()
        self.root.after(1000, self._standby_loop)

    def run(self):
        self.root.mainloop()

    def stop(self):
        self.running = False
        try:
            self.root.destroy()
        except Exception:
            pass


def main():
    log("=" * 50)
    log("  Voice Overlay v5")
    log("  PID: {}".format(os.getpid()))
    log("=" * 50)
    acquire_lock()
    overlay = VoiceOverlay()
    try:
        overlay.run()
    except KeyboardInterrupt:
        overlay.stop()
    finally:
        release_lock()
        log("Overlay shutdown.")


if __name__ == "__main__":
    main()
