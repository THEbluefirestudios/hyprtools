import cv2
from ascii_magic import AsciiArt
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk
import sv_ttk
import darkdetect
import pywinstyles
import sys
import time
import os
from io import BytesIO
# --- DEFAULTS ---
CAMERA_INDEX = 0
COLUMNS = 80
FPS = 15
# ----------------

system_theme = "dark" if darkdetect.isDark() else "light"
cap = None


def apply_theme_to_titlebar(root):
    version = sys.getwindowsversion()
    if version.major == 10 and version.build >= 22000:
        pywinstyles.change_header_color(root, "#1c1c1c" if sv_ttk.get_theme() == "dark" else "#fafafa")
    elif version.major == 10:
        pywinstyles.apply_style(root, "dark" if sv_ttk.get_theme() == "dark" else "normal")
        root.wm_attributes("-alpha", 0.99)
        root.wm_attributes("-alpha", 1)


def start_camera():
    global cap, COLUMNS, FPS, CAMERA_INDEX
    try:
        COLUMNS = int(entry_1.get())
    except ValueError:
        COLUMNS = 80
    try:
        FPS = int(entry_2.get())
    except ValueError:
        FPS = 15
    try:
        CAMERA_INDEX = int(entry_3.get())
    except ValueError:
        CAMERA_INDEX = 0

    cap = cv2.VideoCapture(CAMERA_INDEX)

    frame_settings.pack_forget()
    label_1.pack_forget()
    win.geometry("640x360")  #turbowarp ahh window size
    frame_cam.pack(expand=True, fill='both')
    win.bind('<Escape>', stop_camera)

    update()

def stop_camera(event=None):
    global cap
    win.attributes('-fullscreen', False)
    if cap:
        cap.release()
        cap = None
    frame_cam.pack_forget()
    label_1.pack(pady=10)
    frame_settings.pack(expand=True, fill='both', padx=20, pady=10)



def update():
    global cap
    if cap is None:
        return

    ret, frame = cap.read()
    if not ret:
        cap.release()
        time.sleep(1)
        cap = cv2.VideoCapture(CAMERA_INDEX)
        win.after(100, update)
        return

    h, w = frame.shape[:2]
    frame = cv2.resize(frame, (w, int(w * 9 / 16)))
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(frame_rgb)

    ascii_art = AsciiArt.from_pillow_image(pil_img)
    
    buf = BytesIO()
    ascii_art.to_image_file(buf, columns=COLUMNS, full_color=True)
    buf.seek(0)
    ascii_pil = Image.open(buf)

    win_w = frame_cam.winfo_width()
    win_h = frame_cam.winfo_height()

    if win_w > 1 and win_h > 1:
        ascii_pil = ascii_pil.resize((win_w, win_h), Image.LANCZOS)

    img = ImageTk.PhotoImage(ascii_pil)
    label_4.config(image=img)
    label_4.image = img  # type: ignore

    win.after(1000 // FPS, update)

def on_close():
    global cap
    if cap:
        cap.release()
    win.destroy()


win = tk.Tk()
win.title("ASCII Camera - HyprTools")
win.geometry("440x350")
win.protocol("WM_DELETE_WINDOW", on_close)

# js the start menu page
label_1 = ttk.Label(win, text="ASCII Camera", font=('Courier', 28, 'bold'))
label_1.pack(pady=10)

frame_settings = ttk.Frame(win)
frame_settings.pack(expand=True, fill='both', padx=20, pady=10)

frame_1 = ttk.Frame(frame_settings)
frame_1.pack(pady=5)
label_2 = ttk.Label(frame_1, text="Columns:", font=('Segoe UI Variable', 11))
label_2.pack(side='left', padx=5)
entry_1 = ttk.Entry(frame_1, width=8)
entry_1.insert(0, str(COLUMNS))
entry_1.pack(side='left')

frame_2 = ttk.Frame(frame_settings)
frame_2.pack(pady=5)
label_3 = ttk.Label(frame_2, text="FPS:", font=('Segoe UI Variable', 11))
label_3.pack(side='left', padx=5)
entry_2 = ttk.Entry(frame_2, width=8)
entry_2.insert(0, str(FPS))
entry_2.pack(side='left')

frame_3 = ttk.Frame(frame_settings)
frame_3.pack(pady=5)
label_5 = ttk.Label(frame_3, text="Camera index:", font=('Segoe UI Variable', 11))
label_5.pack(side='left', padx=5)
entry_3 = ttk.Entry(frame_3, width=8)
entry_3.insert(0, str(CAMERA_INDEX))
entry_3.pack(side='left')

btn_1 = ttk.Button(frame_settings, text="Start", style='Accent.TButton', command=start_camera)
btn_1.pack(pady=15)

label_6 = ttk.Label(frame_settings, text="On clicking 'start', open OBS Studio, set this window as a window capture source and click 'Start Virtual Camera', now enjoy your ASCII Camera anywhere by setting camera to 'OBS virtual camera' :3", font=('Segoe UI Variable', 8), wraplength=400, foreground="#535353", justify = 'center')
label_6.pack(pady=10)
# very jank way to get a virtual camera, user has to manually set this win as capture source and use it that way
frame_cam = ttk.Frame(win)
label_4 = ttk.Label(frame_cam)
label_4.pack(expand=True, fill='both')

sv_ttk.set_theme(system_theme)
apply_theme_to_titlebar(win)

win.mainloop()