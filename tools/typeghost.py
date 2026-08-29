import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sv_ttk
import darkdetect
import pyautogui as auto
from time import sleep
from random import randint
import os

try:
    import pywinstyles
except ImportError:
    pywinstyles = None


TYPE_SPEED = 150 
SPELLERROR_RATE = 50  # percentage of characters that will have spelling errors
# FUNCS FOR THE ACTIAL TYPING
def find_closest_char_on_kb(char):
    kbrow_0 = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '-', '_', '=', '+']
    kbrow_1 = ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']', '{', '}']
    kbrow_2 = ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', ':', "'", '"']
    kbrow_3 = ['z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '/', '<', '>', '?', '\\', '|']

    dir = randint(1, 4)
    if dir == 1:  # gets key to right of char
        if char in kbrow_0:
            index = kbrow_0.index(char)
            if index < len(kbrow_0) - 1:
                return kbrow_0[index + 1]
            elif index > 0:
                return kbrow_0[index - 1]
        elif char in kbrow_1:
            index = kbrow_1.index(char)
            if index < len(kbrow_1) - 1:
                return kbrow_1[index + 1]
            elif index > 0:
                return kbrow_1[index - 1]
        elif char in kbrow_2:
            index = kbrow_2.index(char)
            if index < len(kbrow_2) - 1:
                return kbrow_2[index + 1]
            elif index > 0:
                return kbrow_2[index - 1]
        elif char in kbrow_3:
            index = kbrow_3.index(char)
            if index < len(kbrow_3) - 1:
                return kbrow_3[index + 1]
            elif index > 0:
                return kbrow_3[index - 1]
    elif dir == 2:  # gets key to left of char
        if char in kbrow_0:
            index = kbrow_0.index(char)
            if index > 0:
                return kbrow_0[index - 1]
            elif index < len(kbrow_0) - 1:
                return kbrow_0[index + 1]
        elif char in kbrow_1:
            index = kbrow_1.index(char)
            if index > 0:
                return kbrow_1[index - 1]
            elif index < len(kbrow_1) - 1:
                return kbrow_1[index + 1]
        elif char in kbrow_2:
            index = kbrow_2.index(char)
            if index > 0:
                return kbrow_2[index - 1]
            elif index < len(kbrow_2) - 1:
                return kbrow_2[index + 1]
        elif char in kbrow_3:
            index = kbrow_3.index(char)
            if index > 0:
                return kbrow_3[index - 1]
            elif index < len(kbrow_3) - 1:
                return kbrow_3[index + 1]
    elif dir == 3:  # gets key above char
        if char in kbrow_0:
            index = kbrow_0.index(char)
            if index < len(kbrow_1):
                return kbrow_1[index]
        elif char in kbrow_1:
            index = kbrow_1.index(char)
            if index < len(kbrow_0):
                return kbrow_0[index]
        elif char in kbrow_2:
            index = kbrow_2.index(char)
            if index < len(kbrow_1):
                return kbrow_1[index]
        elif char in kbrow_3:
            index = kbrow_3.index(char)
            if index < len(kbrow_2):
                return kbrow_2[index]
    elif dir == 4:  # gets key below char
        if char in kbrow_0:
            index = kbrow_0.index(char)
            if index < len(kbrow_1):
                return kbrow_1[index]
        elif char in kbrow_1:
            index = kbrow_1.index(char)
            if index < len(kbrow_2):
                return kbrow_2[index]
        elif char in kbrow_2:
            index = kbrow_2.index(char)
            if index < len(kbrow_3):
                return kbrow_3[index]
        elif char in kbrow_3:
            index = kbrow_3.index(char)
            if index < len(kbrow_2):
                return kbrow_2[index]

def type_char(char, spellerror_rate, prevs_char):#how human-like do you want the autotyper to feel. me: YES
    if randint(0, 100) < spellerror_rate:
        wrong_char = find_closest_char_on_kb(char)
        if wrong_char is None:
            wrong_char = char 

         # spell eroor, it will always be cororected
        auto.write(wrong_char, _pause=False)
        sleep((randint(10, 15) + dist_on_kb(wrong_char, prevs_char)) / TYPE_SPEED)
        sleep(randint(20, 50) / TYPE_SPEED) 
        auto.press('backspace')
        sleep(randint(5, 15) / TYPE_SPEED)
        auto.write(char, _pause=False)
        sleep((randint(10, 15) + dist_on_kb(char, wrong_char)) / TYPE_SPEED)

    else:
        auto.write(char, _pause=False)
        sleep((randint(10, 15) + dist_on_kb(char, prevs_char)) / TYPE_SPEED)

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
        if index > 0:
            prev_char = textstr[index - 1]
        else:
            prev_char = 'f'
        type_char(char, SPELLERROR_RATE, prev_char)


def code_pretend_type(textstr):
    formatted_text = textstr.replace('    ', "").replace('\t', '')
    closers = {'{': '}', '(': ')', '[': ']'}

    for index, char in enumerate(formatted_text):
        if index > 0:
            prev_char = formatted_text[index - 1]
        else:
            prev_char = 'f'
        type_char(char, SPELLERROR_RATE, prev_char)

        if char in closers:
            next_char = formatted_text[index + 1] if index + 1 < len(formatted_text) else ''
            immediately_closes = next_char == closers[char]
            if not immediately_closes and randint(0, 100) < 50:
                sleep(randint(1, 3))

        if char == '\n' and randint(0, 100) < 30:
            sleep(randint(1, 3))


def essay_pretend_type(textstr):
    sentence_enders = ('.', '!', '?')
    for index, char in enumerate(textstr):
        if index > 0:
            prev_char = textstr[index - 1]
        else:
            prev_char = 'f'
        type_char(char, SPELLERROR_RATE, prev_char)

        if char in sentence_enders:
            next_char = textstr[index + 1] if index + 1 < len(textstr) else ''
            if next_char == ' ' or next_char == '\n' or next_char == '':
                sleep(randint(3, 7) / TYPE_SPEED * 100)  # thinking pause before next sentence

        if char == '\n':
            next_char = textstr[index + 1] if index + 1 < len(textstr) else ''
            if next_char == '\n':
                sleep(randint(8, 15) / TYPE_SPEED * 100)  # longer pause, new paragraph

# parsation of files
def parse_text_file(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


#GUIIII > .<

def apply_theme_to_titlebar(root):
    version = sys.getwindowsversion()
    if version.major == 10 and version.build >= 22000:
        pywinstyles.change_header_color(root, "#1c1c1c" if sv_ttk.get_theme() == "dark" else "#fafafa")  # type: ignore
    elif version.major == 10:
        pywinstyles.apply_style(root, "dark" if sv_ttk.get_theme() == "dark" else "normal")  # type: ignore
        root.wm_attributes("-alpha", 0.99)
        root.wm_attributes("-alpha", 1)


loadedtext = ''

win = tk.Tk()
try:
    base = sys._MEIPASS
except AttributeError:
    base = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(base, "typeghost.png")
win.iconphoto(True, tk.PhotoImage(file=icon_path))
win.title("TypeGhost - HyprTools")
win.geometry("560x340")

label_1 = ttk.Label(win, text="TypeGhost", font=('Courier', 28, 'bold'))
label_1.pack(pady=10)

frame_top = ttk.Frame(win, padding=(20, 5))
frame_top.pack(fill='x')

btn_pick = ttk.Button(frame_top, text="Choose a .txt file")
btn_pick.pack(anchor='w')

filevar = tk.StringVar()
filevar.set('No file chosen')
label_file = ttk.Label(frame_top, textvariable=filevar, font=("Consolas", 11))
label_file.pack(anchor='w', pady=8)


def pick_file():
    global loadedtext
    p = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if not p:
        return
    loadedtext = parse_text_file(p)
    filevar.set(p.split('/')[-1])


btn_pick.config(command=pick_file)

frame_mid = ttk.Frame(win, padding=(20, 10))
frame_mid.pack(fill='x')

label_3 = ttk.Label(frame_mid, text="Mode:", font=("Segoe UI Variable", 10))
label_3.pack(side='left')

dd1 = ttk.Combobox(frame_mid, values=['Boilerplate', 'Code', 'Essay'], state='readonly', width=14)
dd1.current(0)
dd1.pack(side='left', padx=10)

frame_speed = ttk.Frame(win, padding=(20, 5))
frame_speed.pack(fill='x')

label_4 = ttk.Label(frame_speed, text="Type speed (1-7):", font=("Segoe UI Variable", 10))
label_4.pack(side='left')

spin_1 = ttk.Spinbox(frame_speed, from_=1, to=7, width=8)
spin_1.set(3)
spin_1.pack(side='left', padx=10)

label_5 = ttk.Label(frame_speed, text="Typo chance (%):", font=("Segoe UI Variable", 10))
label_5.pack(side='left', padx=(20, 0))

spin_2 = ttk.Spinbox(frame_speed, from_=0, to=100, width=8)
spin_2.set(5)
spin_2.pack(side='left', padx=10)

frame_bot = ttk.Frame(win, padding=(20, 15))
frame_bot.pack(fill='x', side='bottom')

statusvar = tk.StringVar()
statusvar.set('Status: Ready')
label_status = ttk.Label(frame_bot, textvariable=statusvar, font=("Segoe UI Variable", 10))
label_status.pack(side='left')


def do_countdown(n):
    if n > 0:
        statusvar.set(f'Starting in: {n}')
        win.after(1000, do_countdown, n - 1)
    else:
        statusvar.set('Typing...')
        threading.Thread(target=run_typer, daemon=True).start()


def run_typer():
    global TYPE_SPEED, SPELLERROR_RATE
    mode = dd1.get()

    TYPE_SPEED = int(spin_1.get()) * 50
    SPELLERROR_RATE = int(spin_2.get())

    if mode == 'Boilerplate':
        boilerplate_pretend_type(loadedtext)
    elif mode == 'Code':
        code_pretend_type(loadedtext)
    elif mode == 'Essay':
        essay_pretend_type(loadedtext)

    win.after(0, lambda: statusvar.set('Status: Ready'))


def start_click():
    if loadedtext.strip() == '':
        messagebox.showwarning("No file", "Choose a .txt file first.")
        return
    do_countdown(5)


btn_start = ttk.Button(frame_bot, text="Start", style="Accent.TButton", command=start_click)
btn_start.pack(side='right')

system_theme = "dark" if darkdetect.isDark() else "light"
sv_ttk.set_theme(system_theme)
if pywinstyles:
    apply_theme_to_titlebar(win)

win.mainloop()