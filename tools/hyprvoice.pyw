import sys
import threading
import time
import re
import tkinter as tk
from tkinter import ttk
import sv_ttk
import darkdetect
import pyautogui as auto
import speech_recognition as sr
from pynput import keyboard
from time import sleep
import pystray
from PIL import Image, ImageDraw

try:
    import pywinstyles
except ImportError:
    pywinstyles = None


recog = sr.Recognizer()
recog.pause_threshold = 2.0
recog.non_speaking_duration = 0.3
recog.energy_threshold = 300
pressed = set()
stop_listening_fn = None
manuallyon = False
tray_icon = None

alwaysontop = True
sr_provider = 'google'
profanityfilter = True
autopunctuate = False
last_utterance_time = None

swearlist = ['fuck', 'ass', 'bitch', 'nigger', 'nigga', 'motherfucker', ] #dont judge me on saying the n word


def apply_profanity_filter(text):
    words = text.split(' ')
    out = []
    for w in words:
        stripped = re.sub(r'^\W+|\W+$', '', w)  #no clbuttic, sorry
        if stripped.lower() in swearlist:
            out.append(w.replace(stripped, '_' * len(stripped)))
        else:
            out.append(w)
    return ' '.join(out)


def apply_autopunctuate(text):
    global last_utterance_time
    now = time.time()
    prefix = ''
    if last_utterance_time is not None:
        gap = now - last_utterance_time
        if gap >= 2.0:
            prefix = '. '
        elif gap >= 0.6:
            prefix = ', '
    last_utterance_time = now
    return prefix + text


def callback(recognizer, audio):
    try:
        if sr_provider == 'google':
            text = recognizer.recognize_google(audio).lower()
        elif sr_provider == 'sphinx':
            text = recognizer.recognize_sphinx(audio).lower()
        elif sr_provider == 'wit':
            text = recognizer.recognize_wit(audio).lower()
        elif sr_provider == 'azure':
            text = recognizer.recognize_azure(audio).lower()
        elif sr_provider == 'houndify':
            text = recognizer.recognize_houndify(audio).lower()
        elif sr_provider == 'ibm':
            text = recognizer.recognize_ibm(audio).lower()
        elif sr_provider == 'whisper':
            text = recognizer.recognize_whisper(audio).lower()
        else:
            text = recognizer.recognize_google(audio).lower()

        if profanityfilter:
            text = apply_profanity_filter(text)
        if autopunctuate:
            text = apply_autopunctuate(text)

        sleep(0.1)
        auto.write(text + ' ', _pause=False)
        win.after(0, lambda: statusvar.set("Recognised: " + text))
    except sr.UnknownValueError:
        win.after(0, lambda: statusvar.set('Heard something, could not understand'))
    except sr.RequestError as e:
        win.after(0, lambda: statusvar.set(f"Provider error: {e}"))
    except Exception as e:
        win.after(0, lambda: statusvar.set(f"Error: {e}"))

def start_listening():
    global stop_listening_fn
    if stop_listening_fn is None:
        mic = sr.Microphone()
        with mic as source:
            recog.adjust_for_ambient_noise(source, duration=1)
        recog.dynamic_energy_threshold = False  
        stop_listening_fn = recog.listen_in_background(mic, callback)
        win.after(0, lambda: statusvar.set('Listening...'))
        win.after(0, lambda: btn_mic.config(text='⬛'))

def stop_listening():
    global stop_listening_fn
    if stop_listening_fn:
        stop_listening_fn(wait_for_stop=False)
        stop_listening_fn = None
        win.after(0, lambda: statusvar.set('Ready'))
        win.after(0, lambda: btn_mic.config(text='🎙️'))


def toggle_mic():
    global manuallyon
    if stop_listening_fn is None:
        manuallyon = True
        start_listening()
    else:
        manuallyon = False
        stop_listening()


def show_window():
    win.deiconify()
    win.lift()


def on_press(key):
    pressed.add(key)
    if (keyboard.Key.ctrl_l in pressed or keyboard.Key.ctrl_r in pressed) and \
       (keyboard.Key.alt_l in pressed or keyboard.Key.alt_r in pressed):
        win.after(0, show_window)


def on_release(key):
    pressed.discard(key)


def run_hotkey_listener():
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()


def apply_theme_to_titlebar(root):
    version = sys.getwindowsversion()
    if version.major == 10 and version.build >= 22000:
        pywinstyles.change_header_color(root, "#1c1c1c" if sv_ttk.get_theme() == "dark" else "#fafafa")  # type: ignore
    elif version.major == 10:
        pywinstyles.apply_style(root, "dark" if sv_ttk.get_theme() == "dark" else "normal")  # type: ignore
        root.wm_attributes("-alpha", 0.99)
        root.wm_attributes("-alpha", 1)


# tiny tooltip helper, tk only coz ttk has nothing like this
class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind('<Enter>', self.show)
        widget.bind('<Leave>', self.hide)

    def show(self, event=None):
        if self.tip is not None:
            return
        x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tip = tk.Toplevel(self.widget)
        self.tip.overrideredirect(True)
        self.tip.attributes('-topmost', True)
        lbl = tk.Label(
            self.tip, text=self.text, justify='left', wraplength=220,
            bg='#2b2b2b', fg='#ffffff', font=("Segoe UI Variable", 8),
            relief='solid', borderwidth=1, padx=6, pady=4,
        )
        lbl.pack()
        self.tip.update_idletasks()
        tipw = self.tip.winfo_width()
        self.tip.geometry(f"+{x - tipw // 2}+{y}")

    def hide(self, event=None):
        if self.tip is not None:
            self.tip.destroy()
            self.tip = None


# asked claude to do the entire system try thingy.


def make_tray_icon_image():
    img = Image.new('RGB', (64, 64), '#1c1c1c')
    draw = ImageDraw.Draw(img)
    draw.ellipse((16, 8, 48, 40), fill='#0078d4')  
    draw.rectangle((28, 40, 36, 52), fill='#0078d4') 
    return img


def quit_app(icon_ref=None, item=None):
    tray_icon.stop() # type:ignore
    win.after(0, win.destroy)
    sys.exit(0)


def tray_show(icon_ref=None, item=None):
    win.after(0, show_window)

def run_tray():
    global tray_icon
    menu = pystray.Menu(
        pystray.MenuItem('Show HyprVoice', tray_show, default=True),
        pystray.MenuItem('Quit', quit_app),
    )
    tray_icon = pystray.Icon('HyprVoice', make_tray_icon_image(), 'HyprVoice', menu)
    tray_icon.run()


win = tk.Tk()
win.title("")
win.geometry("220x100")
win.resizable(False, False)
win.attributes('-topmost', alwaysontop)

def hide_instead_of_close():
    win.withdraw()
    stop_listening()# make sure it dosent listen in the bg, i think we can all agree if u see the mic icon on your system tray........ listening


win.protocol("WM_DELETE_WINDOW", hide_instead_of_close)

label_1 = ttk.Label(win, text="HyprVoice", font=('Courier', 10, 'bold'))
label_1.pack(pady=1)

frame_row = ttk.Frame(win, padding=(15, 5))
frame_row.pack(fill='both', expand=True)

btn_gear = ttk.Button(frame_row, text="⚙️", width=3)
btn_gear.pack(side='left', padx=5)

frame_sq = ttk.Frame(frame_row, width=44, height=44)
frame_sq.pack_propagate(False)
frame_sq.pack(side='left', expand=True)

btn_mic = ttk.Button(frame_sq, text="🎙️", style="Accent.TButton", command=toggle_mic)
btn_mic.pack(fill='both', expand=True)

btn_help = ttk.Button(frame_row, text="❓", width=3)
btn_help.pack(side='right', padx=5)

Tooltip(btn_help, "Hold Ctrl+Alt anywhere to bring up this window. Click the mic to start/stop listening. Gear icon opens settings.")

statusvar = tk.StringVar()
statusvar.set('Ready')
label_status = ttk.Label(win, textvariable=statusvar, font=("Segoe UI Variable", 7), wraplength=200, justify='center')
label_status.pack(pady=(0, 8))

win_set = None


def open_settings():
    global win_set
    if win_set is not None and win_set.winfo_exists():
        win_set.lift()
        return

    win_set = tk.Toplevel(win)
    win_set.title("HyprVoice Settings")
    win_set.geometry("300x260")
    win_set.resizable(False, False)

    if pywinstyles:
        apply_theme_to_titlebar(win_set)

    label_s1 = ttk.Label(win_set, text="Settings", font=('Courier', 16, 'bold'))
    label_s1.pack(pady=10)

    frame_s1 = ttk.Frame(win_set, padding=(15, 5))
    frame_s1.pack(fill='x')

    aotvar = tk.BooleanVar(value=alwaysontop)

    def on_aot_toggle():
        global alwaysontop
        alwaysontop = aotvar.get()
        win.attributes('-topmost', alwaysontop)

    chk_aot = ttk.Checkbutton(frame_s1, text="Always on top", variable=aotvar, command=on_aot_toggle)
    chk_aot.pack(anchor='w')

    profvar = tk.BooleanVar(value=profanityfilter)

    def on_prof_toggle():
        global profanityfilter
        profanityfilter = profvar.get()

    chk_prof = ttk.Checkbutton(frame_s1, text="Filter profanity", variable=profvar, command=on_prof_toggle)
    chk_prof.pack(anchor='w', pady=5)

    punctvar = tk.BooleanVar(value=autopunctuate)

    def on_punct_toggle():
        global autopunctuate
        autopunctuate = punctvar.get()

    chk_punct = ttk.Checkbutton(frame_s1, text="Auto-punctuate", variable=punctvar, command=on_punct_toggle)
    chk_punct.pack(anchor='w')

    frame_s2 = ttk.Frame(win_set, padding=(15, 10))
    frame_s2.pack(fill='x')

    label_s2 = ttk.Label(frame_s2, text="Recognition provider:", font=("Segoe UI Variable", 9))
    label_s2.pack(anchor='w')

    dd_provider = ttk.Combobox(frame_s2, values=['google', 'sphinx', 'wit', 'azure', 'houndify', 'ibm', 'whisper'], state='readonly', width=18)
    dd_provider.set(sr_provider)
    dd_provider.pack(anchor='w', pady=5)

    def on_provider_change(event=None):
        global sr_provider
        sr_provider = dd_provider.get()

    dd_provider.bind('<<ComboboxSelected>>', on_provider_change)

    label_s3 = ttk.Label(win_set, text="Some providers need their own API keys, see speech_recognition docs", font=("Segoe UI Variable", 7), foreground="#535353", wraplength=260, justify='center')
    label_s3.pack(side='bottom', pady=10)


btn_gear.config(command=open_settings)

threading.Thread(target=run_hotkey_listener, daemon=True).start()
threading.Thread(target=run_tray, daemon=True).start()

system_theme = "dark" if darkdetect.isDark() else "light"
sv_ttk.set_theme(system_theme)
if pywinstyles:
    apply_theme_to_titlebar(win)#fallback for titlebar color on win10, pywinstyles is optional but recommended

win.mainloop()