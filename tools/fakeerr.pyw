import tkinter as tk
from PIL import Image, ImageTk
import sys
import os
from random import randint

is_win11 = sys.getwindowsversion().build >= 22000
import ctypes

def show_bsod(image_path):
    bsod = tk.Tk()
    bsod.attributes('-fullscreen', True)
    bsod.attributes('-topmost', True)
    bsod.config(cursor="none")

    img = Image.open(image_path)
    screen_width = bsod.winfo_screenwidth()
    screen_height = bsod.winfo_screenheight()
    img = img.resize((screen_width, screen_height))
    photo = ImageTk.PhotoImage(img)

    bg_label = tk.Label(bsod, image=photo)
    bg_label.image = photo#type: ignore
    bg_label.place(x=0, y=0, relwidth=1, relheight=1)
    if is_win11:
        progress_label = tk.Label(bsod, text="0% complete", font=("Segoe UI", 22),fg="white", bg="black", anchor = 'center', justify = 'center')
        progress_label.place(relx=0.50, rely=0.54, anchor = 'center')
    else:
        progress_label = tk.Label(bsod, text="0% complete", font=("Segoe UI", 30),fg="white", bg="#0078D7")
        progress_label.place(relx=0.105, rely=0.555)
    def update_progress(percent=0):
        if percent <= 100:
            progress_label.config(text=f"{percent}% complete")
            bsod.after(randint(15000, 60000), update_progress, percent + 1)
        else:
            bsod.destroy()

            ctypes.windll.user32.LockWorkStation()
    update_progress()

    bsod.bind('<Escape>', lambda e: bsod.destroy())
    bsod.mainloop()

script_dir = os.path.dirname(os.path.abspath(__file__))

try:
    base = sys._MEIPASS
except AttributeError:
    base = script_dir

image_path = os.path.join(base, "bsod_black.png" if is_win11 else "bsod_blue.png")

show_bsod(image_path)