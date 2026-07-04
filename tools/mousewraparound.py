import pyautogui as mouse
from pynput import keyboard
from time import sleep
import threading

mouse.FAILSAFE = False

wrap_toggle = False

def toggle_wrap():
    global wrap_toggle
    wrap_toggle = not wrap_toggle

def mouse_wraparound():
    screen_size = mouse.size()
    screen_width, screen_height = screen_size
    mousex, mousey = mouse.position()
    if mousex == screen_width - 1:
        mouse.moveTo(1, mousey)
    elif mousex == 0:
        mouse.moveTo((screen_width - 2), mousey)
    elif mousey == screen_height - 1:
        mouse.moveTo(mousex, 1)
    elif mousey == 0:
        mouse.moveTo(mousex, (screen_height - 2))
    else:
        pass

# Track currently pressed keys
pressed_keys = set()

def on_press(key):
    pressed_keys.add(key)
    if keyboard.Key.ctrl_r in pressed_keys and keyboard.Key.insert in pressed_keys:
        toggle_wrap()

def on_release(key):
    pressed_keys.discard(key)

listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()

while True:
    if wrap_toggle:
        mouse_wraparound()
    sleep(0.01)