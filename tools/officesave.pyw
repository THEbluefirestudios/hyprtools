import pyautogui
import pygetwindow as gw
from time import sleep

office_apps = ["Word", "Excel", "PowerPoint"]

delay = 10

import os

script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, "savedelay.txt")

with open(file_path, 'r') as f:
    delay = f.readline().strip()

while True:
    active = gw.getActiveWindow()
    if active and any(app in active.title for app in office_apps):
        pyautogui.hotkey("ctrl", "s")
    sleep(int(delay))