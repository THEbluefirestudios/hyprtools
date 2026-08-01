import tkinter as tk
from tkinter import ttk
import pywinstyles
import darkdetect
import sys
import sv_ttk
import os
import json

system_theme = "dark" if darkdetect.isDark() else "light"
script_dir = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(script_dir, "hyprtools.json")

delay = 120


def load_json():
    if not os.path.exists(json_path):
        return {}
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data):
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def load_delay():
    global delay
    data = load_json()
    delay = data.get('actuallyautosave', {}).get('delay', 120)


def pretty_time_formatting(rawseconds):
    step = 10
    seconds = round(rawseconds / step) * step

    if seconds > 60:
        minutes = seconds // 60
        finalseconds = seconds % 60
        if finalseconds == 0:
            return f"{minutes} minutes"
        else:
            return f"{minutes} minutes, {finalseconds} seconds"
    else:
        return f"{seconds} seconds"


def apply_theme_to_titlebar(root):
    global theme
    version = sys.getwindowsversion()
    theme = sv_ttk.get_theme()
    if version.major == 10 and version.build >= 22000:
        pywinstyles.change_header_color(root, "#1c1c1c" if sv_ttk.get_theme() == "dark" else "#fafafa")
    elif version.major == 10:
        pywinstyles.apply_style(root, "dark" if sv_ttk.get_theme() == "dark" else "normal")
        root.wm_attributes("-alpha", 0.99)
        root.wm_attributes("-alpha", 1)


def on_slider_change(value):
    global delay
    delay = round(float(value) / 10) * 10
    status_label.config(text=pretty_time_formatting(delay))


def save_delay():
    global delay
    data = load_json()
    if 'actuallyautosave' not in data:
        data['actuallyautosave'] = {}
    data['actuallyautosave']['delay'] = delay
    save_json(data)
    status_label.config(text=f"Saved: {pretty_time_formatting(delay)}")


load_delay()

win = tk.Tk()
win.geometry('440x220')
win.title('ActuallyAutosave - HyprTools')
ttk.Label(win, text="ActuallyAutosave", font=('courier', 32, "bold")).pack(pady=10)
ttk.Label(win, text="Change saving delay:", font=('Segoe UI', 12)).pack()
status_label = ttk.Label(win, text=pretty_time_formatting(delay), font=('Segoe UI Variable', 10))
scale = ttk.Scale(win, from_=30, to=600, orient='horizontal', command=on_slider_change)
scale.set(delay)
scale.pack(pady=10)


status_label.pack()

start_btn = ttk.Button(win, text="Save", style='Accent.TButton', command=save_delay)
start_btn.pack(pady=10)

sv_ttk.set_theme(system_theme)
apply_theme_to_titlebar(win)

win.mainloop()