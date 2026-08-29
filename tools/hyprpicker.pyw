import sys
import threading
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageGrab, ImageTk, ImageDraw
from pynput import keyboard
import pystray
import os
BASEDIR = os.path.dirname(os.path.abspath(__file__))

try:
    import win32clipboard
except ImportError:
    win32clipboard = None

import ctypes

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # making sure the screen grab is not ofsetted :(
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def get_virtual_screen_bounds():
    user32 = ctypes.windll.user32
    x = user32.GetSystemMetrics(76)   # SM_XVIRTUALSCREEN
    y = user32.GetSystemMetrics(77)   # SM_YVIRTUALSCREEN
    w = user32.GetSystemMetrics(78)   # SM_CXVIRTUALSCREEN
    h = user32.GetSystemMetrics(79)   # SM_CYVIRTUALSCREEN
    return x, y, w, h


pressed = set()
overlaywin = None
tray_icon = None


def copy_to_clipboard(text):
    if win32clipboard:
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(text) #type: ignore
        win32clipboard.CloseClipboard()
    else:
        # fallback, needs a live tk root, less reliable once window closes
        r = tk.Tk()
        r.withdraw()
        r.clipboard_clear()
        r.clipboard_append(text)
        r.update()
        r.after(200, r.destroy)


def show_toast(hexcode, rgbtuple):
    toast = tk.Toplevel()
    toast.overrideredirect(True)
    toast.attributes('-topmost', True)

    frame_t = tk.Frame(toast, bg='#1c1c1c', highlightbackground='#333333', highlightthickness=1)
    frame_t.pack()

    swatch = tk.Label(frame_t, bg=hexcode, width=2, height=1)
    swatch.pack(side='left', padx=8, pady=8)

    label_t = tk.Label(frame_t, text=f"Copied {hexcode} to clipboard", bg='#1c1c1c', fg='#ffffff', font=("Segoe UI Variable", 10), padx=5)
    label_t.pack(side='left', padx=(0, 10), pady=8)

    toast.update_idletasks()
    sw = toast.winfo_screenwidth()
    sh = toast.winfo_screenheight()
    tw = toast.winfo_width()
    th = toast.winfo_height()
    toast.geometry(f"+{sw - tw - 30}+{sh - th - 60}")

    toast.after(2200, toast.destroy)


def spawn_picker():
    global overlaywin
    if overlaywin is not None and overlaywin.winfo_exists():
        return

    vx, vy, vw, vh = get_virtual_screen_bounds()
    shot_full = ImageGrab.grab(bbox=(vx, vy, vx + vw, vy + vh), all_screens=True)

    overlaywin = tk.Toplevel()
    overlaywin.overrideredirect(True)
    overlaywin.attributes('-topmost', True)

    tkw = root.winfo_screenwidth()
    tkh = root.winfo_screenheight()
    overlaywin.geometry(f"{tkw}x{tkh}+0+0")

    shot = shot_full.resize((tkw, tkh), Image.LANCZOS)#type: ignore
    #lanczos is a fucking part of PIL.Image, stop giving false alarms, Pylance

    bgimg = ImageTk.PhotoImage(shot)
    canvas_1 = tk.Canvas(overlaywin, width=tkw, height=tkh, highlightthickness=0, cursor='crosshair')
    canvas_1.pack()
    canvas_1.create_image(0, 0, image=bgimg, anchor='nw')
    canvas_1.bgimgref = bgimg  # type: ignore

    tip = tk.Toplevel(overlaywin)
    tip.overrideredirect(True)
    tip.attributes('-topmost', True)

    tipframe = tk.Frame(tip, bg='#1c1c1c', highlightbackground='#333333', highlightthickness=1)
    tipframe.pack()
    tipswatch = tk.Label(tipframe, bg='#000000', width=2, height=1)
    tipswatch.pack(side='left', padx=6, pady=6)
    tiplabel = tk.Label(tipframe, text='#000000', bg='#1c1c1c', fg='#ffffff', font=("Consolas", 10), padx=5)
    tiplabel.pack(side='left', padx=(0, 8), pady=6)

    def on_motion(event):
        x, y = event.x, event.y
        if 0 <= x < tkw and 0 <= y < tkh:
            px = shot.getpixel((x, y))
            if isinstance(px, int):
                px = (px, px, px)
            hexcode = '#%02x%02x%02x' % px[:3]  # that looks like  :3 emoji :)))))) #type: ignore
            tipswatch.config(bg=hexcode)
            tiplabel.config(text=hexcode)

            tip.update_idletasks()
            tipw = tip.winfo_width()
            tiph = tip.winfo_height()
            screenw = tip.winfo_screenwidth()
            screenh = tip.winfo_screenheight()

            tipx = event.x_root + 18
            tipy = event.y_root + 18

            if tipx + tipw > screenw:
                tipx = event.x_root - tipw - 18  # flip to left of cursor, to avoid the tip from being blocked

            if tipy + tiph > screenh:
                tipy = event.y_root - tiph - 18  # snap above cursor instead of below, for same reson

            tip.geometry(f"+{tipx}+{tipy}")
    def on_click(event):
        try:
            x, y = event.x, event.y
            if 0 <= x < tkw and 0 <= y < tkh:
                px = shot.getpixel((x, y))
                if isinstance(px, int):
                    px = (px, px, px)
                hexcode = '#%02x%02x%02x' % px[:3]#type: ignore
                copy_to_clipboard(hexcode)
                close_picker()
                show_toast(hexcode, px)
        except Exception:
            close_picker()  # always clean up, even if something above breaks

    def on_escape(event=None):
        close_picker()

    def close_picker():
        global overlaywin
        if tip.winfo_exists():
            tip.destroy()
        if overlaywin is not None and overlaywin.winfo_exists():
            overlaywin.destroy()
        overlaywin = None

    canvas_1.bind('<Motion>', on_motion)
    overlaywin.bind('<Escape>', on_escape)

    overlaywin.update_idletasks()
    overlaywin.lift()
    overlaywin.focus_force()
    tip.lift()  # make sure tooltip stays above the fullscreen overlay

    # eat the activation click, only enable real clicking after a short delay
    overlaywin.after(200, lambda: canvas_1.bind('<Button-1>', on_click))


def make_tray_icon_image():
    try:
        base = sys._MEIPASS
    except AttributeError:
        base = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base, 'hyprpicker.png')
    return Image.open(icon_path).convert('RGBA')


def quit_app(icon_ref=None, item=None):
    tray_icon.stop()#type: ignore
    sys.exit(0)


def run_tray():
    global tray_icon
    menu = pystray.Menu(
        pystray.MenuItem('Pick a color (Alt + K)', lambda i, it: spawn_picker()),
        pystray.MenuItem('Quit', quit_app),
    )
    tray_icon = pystray.Icon('HyprPicker', make_tray_icon_image(), 'HyprPicker', menu)
    tray_icon.run()


def on_press(key):
    pressed.add(key)
    if (keyboard.Key.alt_l in pressed or keyboard.Key.alt_r in pressed):
        try:
            if key.char is not None and key.char.lower() == 'k':
                root.after(0, spawn_picker)
        except AttributeError:
            pass


def on_release(key):
    pressed.discard(key)


def run_hotkey_listener():
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()


root = tk.Tk()
try:
    base = sys._MEIPASS
except AttributeError:
    base = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(base, "hyprpicker.png")
root.iconphoto(True, tk.PhotoImage(file=icon_path))
root.withdraw() 

threading.Thread(target=run_hotkey_listener, daemon=True).start()
threading.Thread(target=run_tray, daemon=True).start()

root.mainloop()