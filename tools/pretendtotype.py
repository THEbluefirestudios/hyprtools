import pyautogui as auto
from time import sleep
from random import randint


def dist_on_kb(char_a, char_b):
    kbrow_0 = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '-', '_', '=', '+']
    kbrow_1 = ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']', '{', '}']
    kbrow_2 = ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', ':', "'", '"']
    kbrow_3 = ['z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '/', '<', '>', '?', '\\', '|']

    #this function calculates distance between 2 chars on a keyboard, to get more realistic typing speeds
    try:
        index_1 = kbrow_0.index(char_a)
        y_1 = 0
    except ValueError:
        try:
            index_1 = kbrow_1.index(char_a)
            y_1 = 1
        except ValueError:
            try:
                index_1 = kbrow_2.index(char_a)
                y_1 = 2
            except ValueError:
                try:
                    index_1 = kbrow_3.index(char_a)
                    y_1 = 3
                except ValueError:
                    index_1 = 2  
                    y_1 = 2      
    
    try:
        index_2 = kbrow_0.index(char_b)
        y_2 = 0
    except ValueError:
        try:
            index_2 = kbrow_1.index(char_b)
            y_2 = 1
        except ValueError:
            try:
                index_2 = kbrow_2.index(char_b)
                y_2 = 2
            except ValueError:
                try:
                    index_2 = kbrow_3.index(char_b)
                    y_2 = 3
                except ValueError:
                    index_2 = 2  
                    y_2 = 2    

    dist_x = abs(index_2 - index_1)
    dist_y = abs(y_2 - y_1)

    total_multiplier = dist_x + dist_y + 1

    return total_multiplier

def boilerplate_pretend_type(textstr):
    for index, char in enumerate(textstr):
        if char > 0:
            prev_char = textstr[index - 1]
        else:
            prev_char = 'f'
        auto.write(char, _pause = False)
        sleep(((randint(10, 15)+(dist_on_kb(char,prev_char))/150)))

def code_pretend_type(textstr):
    for index, char in enumerate(textstr):
        if char > 0:
            prev_char = textstr[index - 1]
        else:
            prev_char = 'f'
        auto.write(char, _pause = False)
        sleep(((randint(10, 15)+(dist_on_kb(char,prev_char))/150)))


print('starting....')
sleep(10)

boilerplate_pretend_type("""import pyautogui as m
import tkinter as tk
from tkinter import ttk
import sv_ttk as sv
import pywinstyles, sys

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
win.geometry('380x220')
win.title('HyprTools - HyprClickr')


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
""")