import pyautogui as m
import tkinter as tk
from tkinter import ttk
import sv_ttk as sv
import pywinstyles, sys
import os

import darkdetect

system_theme = "dark" if darkdetect.isDark() else "light"


def apply_theme_to_titlebar(root):
    global theme
    version = sys.getwindowsversion()
    theme = sv.get_theme()
    if version.major == 10 and version.build >= 22000:
     
        pywinstyles.change_header_color(root, "#1c1c1c" if sv.get_theme() == "dark" else "#fafafa")
        
    elif version.major == 10:
        pywinstyles.apply_style(root, "dark" if sv.get_theme() == "dark" else "normal")

     
        root.wm_attributes("-alpha", 0.99)
        root.wm_attributes("-alpha", 1)



def start_process():
 
    try:
        global cps
        cps = int(entry.get())
     
        countdown(5)
    except ValueError:
        status_label.config(text="Please enter a valid number")

def countdown(count):
    if count > 0:
        status_label.config(text=f"Starting in: {count}")
   
        win.after(1000, countdown, count - 1)
    else:
        status_label.config(text="Clicking... (Move mouse to stop)")
        auto_click()

def auto_click():

    global last_pos
    current_pos = m.position()
    
 
    if 'last_pos' not in globals():
        last_pos = current_pos


    m.click()
    

    if m.position() != current_pos:
        status_label.config(text="Stopped: Movement Detected")
        del globals()['last_pos'] 
        return


    interval = int(1000 / cps)
    win.after(interval, auto_click)

win = tk.Tk() 
try:
    base = sys._MEIPASS#type: ignore
except AttributeError:
    base = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(base, "hyprclicker.png")
win.iconphoto(True, tk.PhotoImage(file=icon_path))
win.geometry('380x220')
win.title('HyprClickr - HyprTools')


ttk.Label(win, text="HyprClickr", font=('courier', 32, "bold")).pack(pady = 10)
ttk.Label(win, text="Enter Clicks Per Second", font=('Segoe UI Variable', 12)).pack()

entry = ttk.Entry(win)
entry.insert(0, "10")
entry.pack(pady=5)

start_btn = ttk.Button(win, text="Start", command=start_process, style='Accent.TButton')
start_btn.pack(pady=10)

status_label = ttk.Label(win, text="Status: Ready", font=('Segoe UI Variable', 10))
status_label.pack()

sv.set_theme(system_theme)
apply_theme_to_titlebar(win)


win.mainloop()