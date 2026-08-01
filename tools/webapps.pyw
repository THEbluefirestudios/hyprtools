import webview as wb
import tkinter as tk
from tkinter import ttk, messagebox
import sv_ttk as sv
import pywinstyles, sys
import os
import json
import subprocess
import requests
from PIL import Image, ImageTk

BASEDIR = os.path.dirname(os.path.abspath(__file__))
JSONPATH = os.path.join(BASEDIR, 'hyprtools.json')# sum path stuff
ICONDIR = os.path.join(BASEDIR, 'icons')

if not os.path.exists(ICONDIR):
    os.makedirs(ICONDIR)


def apply_theme_to_titlebar(root):# copy-pasted from sv_ttk doco
    version = sys.getwindowsversion()
    if version.major == 10 and version.build >= 22000:
        pywinstyles.change_header_color(root, "#1c1c1c")
    elif version.major == 10:
        pywinstyles.apply_style(root, "dark")
        root.wm_attributes("-alpha", 0.99)
        root.wm_attributes("-alpha", 1)


def load_data(): # data is in the hyprtools.json, which will (as of wititng this) contain every  dta hyprtools needs so that its a portable and not an installer. if the file doesnt exist, create it with default values.
    if not os.path.exists(JSONPATH):
        data = {'webapps': [], 'settings': {'launch_width': 1100, 'launch_height': 700, 'dark_mode': True}}
        save_data(data)
        return data

    with open(JSONPATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    changed = False
    if 'webapps' not in data:
        data['webapps'] = []
        changed = True
    if 'settings' not in data:
        data['settings'] = {'launch_width': 1100, 'launch_height': 700, 'dark_mode': True}
        changed = True

    if changed:
        save_data(data)

    return data

def save_data(data):
    with open(JSONPATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def fetch_favicon(url, savepath): # get that icon u see in really small in the tab, and save it to the icons folder. if it fails, return false.
    try:
        favurl = "https://www.google.com/s2/favicons?domain=" + url + "&sz=64"
        r = requests.get(favurl, timeout=5)
        with open(savepath, 'wb') as f:
            f.write(r.content)
        return True
    except Exception:
        return False




if len(sys.argv) >= 4 and sys.argv[1] == '--launch': 
    launch_title = sys.argv[2]
    launch_url = sys.argv[3]
    d = load_data()
    w = d.get('settings', {}).get('launch_width', 1100)
    h = d.get('settings', {}).get('launch_height', 700)
    wb.create_window(launch_title, launch_url, width=w, height=h)
    wb.start()
    sys.exit(0)

data = load_data()
# the guiiiiiiii
root = tk.Tk()
root.geometry('460x420') 
root.title('Web Apps - Hyprtools')

label_1 = ttk.Label(root, text='Web Apps', font=('courier', 28, 'bold'))
label_1.pack(pady=10)

frame_grid = ttk.Frame(root, padding=10)
frame_grid.pack(fill='both', expand=True)

iconcache = []


def launch_webapp(name, url): # just pywebview
    subprocess.Popen([sys.executable, os.path.abspath(__file__), '--launch', name, 'https://' + url])


def delete_webapp(entry): #tk dialogbox + remove from json + rebuild grid
    yn = messagebox.askyesno('Delete', 'Remove "' + entry['name'] + '" from Web Apps?')
    if yn:
        data['webapps'].remove(entry)
        save_data(data)
        os.remove(entry['icon'].split('/')[-1]) # remove the icon
        rebuild_grid()


def open_create_dialog():
    win_new = tk.Toplevel(root) # another tk guiiiiiiiiii for making  'new app'
    win_new.title('New Web App')
    win_new.geometry('320x220')
    apply_theme_to_titlebar(win_new)

    label_n1 = ttk.Label(win_new, text='New Web App', font=('courier', 16, 'bold'))
    label_n1.pack(pady=10)

    frame_n1 = ttk.Frame(win_new)
    frame_n1.pack(pady=5, fill='x', padx=15)
    label_n2 = ttk.Label(frame_n1, text='App name:')
    label_n2.pack(side='left', padx=5)
    entry_n1 = ttk.Entry(frame_n1)
    entry_n1.pack(side='left', fill='x', expand=True)

    frame_n2 = ttk.Frame(win_new)
    frame_n2.pack(pady=5, fill='x', padx=15)
    label_n3 = ttk.Label(frame_n2, text='URL:\t')
    label_n3.pack(side='left', padx=5)
    entry_n2 = ttk.Entry(frame_n2)
    entry_n2.pack(side='left', fill='x', expand=True)

    statusvar_n = tk.StringVar()
    statusvar_n.set('')
    label_status_n = ttk.Label(win_new, textvariable=statusvar_n, font=('Segoe UI Variable', 8), foreground='#535353')
    label_status_n.pack(pady=5)

    def do_create():
        name = entry_n1.get().strip()
        url = entry_n2.get().strip()
        if name == '' or url == '':
            statusvar_n.set('Fill in both fields.')
            return
        url = url.replace('https://', '').replace('http://', '')

        statusvar_n.set('Fetching favicon...')
        win_new.update()

        iconpath = os.path.join(ICONDIR, name.replace(' ', '_') + '.png')
        fetch_favicon(url, iconpath)

        entry = {'name': name, 'url': url, 'icon': iconpath}
        data['webapps'].append(entry)
        save_data(data)
        rebuild_grid()
        win_new.destroy()

    btn_create = ttk.Button(win_new, text='Create +', style='Accent.TButton', command=do_create)
    btn_create.pack(pady=10)


def open_settings_dialog(): # yet another guiiiiiiiiiii for settings. this one is a bit more complex, but not too bad.
    win_set = tk.Toplevel(root)
    win_set.title('Settings')
    win_set.geometry('300x220')
    apply_theme_to_titlebar(win_set)

    label_s1 = ttk.Label(win_set, text='Settings', font=('courier', 16, 'bold'))
    label_s1.pack(pady=10)

    frame_s1 = ttk.Frame(win_set, padding=(15, 5))
    frame_s1.pack(fill='x')

    label_w = ttk.Label(frame_s1, text='Launch width:')
    label_w.pack(anchor='w')
    spin_w = ttk.Spinbox(frame_s1, from_=400, to=3000, width=10)
    spin_w.set(data['settings'].get('launch_width', 1100))
    spin_w.pack(anchor='w', pady=(0, 8))

    label_h = ttk.Label(frame_s1, text='Launch height:')
    label_h.pack(anchor='w')
    spin_h = ttk.Spinbox(frame_s1, from_=300, to=2000, width=10)
    spin_h.set(data['settings'].get('launch_height', 700))
    spin_h.pack(anchor='w', pady=(0, 8))

    darkvar = tk.BooleanVar(value=data['settings'].get('dark_mode', True))
    chk_dark = ttk.Checkbutton(frame_s1, text='Dark mode', variable=darkvar)
    chk_dark.pack(anchor='w', pady=5)

    def do_save():
        data['settings']['launch_width'] = int(spin_w.get()) # type: ignore
        data['settings']['launch_height'] = int(spin_h.get())
        data['settings']['dark_mode'] = darkvar.get()
        save_data(data)
        sv.set_theme('dark' if darkvar.get() else 'light')
        win_set.destroy()

    btn_save = ttk.Button(win_set, text='Save 💾', style='Accent.TButton', command=do_save)
    btn_save.pack(pady=10)


def rebuild_grid(): # makes dat grid u see of apps in thwe homescreen
    for w in frame_grid.winfo_children():
        w.destroy()
    iconcache.clear()

    col = 0
    row = 0
    maxcols = 4

    for entry in data['webapps']:
        cell = ttk.Frame(frame_grid, padding=8)
        cell.grid(row=row, column=col, padx=5, pady=5)

        img = None
        if os.path.exists(entry['icon']):
            try:
                pilimg = Image.open(entry['icon']).resize((40, 40))
                img = ImageTk.PhotoImage(pilimg)
                iconcache.append(img)
            except Exception:
                img = None

        if img is not None:
            btn_app = ttk.Button(cell, image=img, command=lambda e=entry: launch_webapp(e['name'], e['url']))
        else:
            btn_app = ttk.Button(cell, text='🌐', command=lambda e=entry: launch_webapp(e['name'], e['url'])) # i use emojis as arial dosent have colored emojis, so its black n white and looks like icon
        btn_app.pack()# also the emoji is kinda useless, i just realised that, there is a similar fallback already built...

        label_name = ttk.Label(cell, text=entry['name'], font=('Segoe UI Variable', 8))
        label_name.pack()

        def make_delete_handler(e):
            def handler(event):
                delete_webapp(e)
            return handler

        btn_app.bind('<Button-3>', make_delete_handler(entry))  # right click to delete, i think i am smrt

        col += 1
        if col >= maxcols:
            col = 0
            row += 1

    cell_add = ttk.Frame(frame_grid, padding=8)
    cell_add.grid(row=row, column=col, padx=5, pady=5)
    btn_add = ttk.Button(cell_add, text='➕', command=open_create_dialog) # same thing with da mojis here
    btn_add.pack()
    label_add = ttk.Label(cell_add, text='New app', font=('Segoe UI Variable', 8))
    label_add.pack()

# just init everything u saw above ts
frame_bot = ttk.Frame(root, padding=(15, 10))
frame_bot.pack(fill='x', side='bottom')

btn_settings = ttk.Button(frame_bot, text='⚙️ Settings', command=open_settings_dialog)
btn_settings.pack(side='right')

rebuild_grid()

apply_theme_to_titlebar(root)
sv.set_theme('dark' if data['settings'].get('dark_mode', True) else 'light')

root.mainloop()