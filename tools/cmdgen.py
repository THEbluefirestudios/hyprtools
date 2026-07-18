import sys
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sv_ttk
import darkdetect

import ctypes
import sys

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

try:
    import pywinstyles
except ImportError:
    pywinstyles = None

cmds = [
    'shutdown', 'echo', 'cd', 'ping', 'mkdir', 'del', 'copy', 'ipconfig',
    'dir', 'cls', 'tasklist', 'taskkill', 'netstat', 'systeminfo',
    'whoami', 'tree', 'xcopy', 'timeout', 'start', 'attrib',
]

cmdlabels = [
    'Shut down or restart', 'Display a message', 'Change folder', 'Ping a host',
    'Make a new folder', 'Delete a file', 'Copy a file', 'Show network info',
    'List folder contents', 'Clear the screen', 'List running programs',
    'Close a program', 'Show network connections', 'Show system info',
    'Show current user', 'Show folder tree', 'Copy a folder', 'Wait a bit',
    'Open a program or file', 'Change file attributes',
]

cmdfmt = [
    'shutdown {0} /t {1}',
    'echo {0}',
    'cd {0}',
    'ping {0} {1}',
    'mkdir {0}',
    'del {0}',
    'copy {0} {1}',
    'ipconfig',
    'dir {0}',
    'cls',
    'tasklist',
    'taskkill /im {0} {1}',
    'netstat {0}',
    'systeminfo',
    'whoami',
    'tree {0}',
    'xcopy {0} {1} {2}',
    'timeout {0}',
    'start {0}',
    'attrib {0} {1}',
]

params = [
    ['what to do', 'delay in seconds'],
    ['message to display'],
    ['folder to open'],
    ['ping count', 'target host'],
    ['new folder name'],
    ['file to delete'],
    ['source file', 'destination'],
    [],
    ['folder to list'],
    [],
    [],
    ['process name', 'force close'],
    ['flags'],
    [],
    [],
    ['folder to show'],
    ['source folder', 'destination', 'include subfolders'],
    ['seconds to wait'],
    ['program or file to open'],
    ['file', 'attribute to set'],
]

paramvals = [
    [[('shut the pc down', '/s'), ('restart the pc', '/r'), ('log off', '/l'), ('hibernate', '/h')], 'numinput'],
    ['input'],
    ['folderpicker'],
    ['numinput', 'input'],
    ['input'],
    ['filepicker'],
    ['filepicker', 'filepicker'],
    [],
    ['folderpicker'],
    [],
    [],
    ['input', [('yes', '/f'), ('no', '')]],
    [[('all connections', '-a'), ('with process names', '-b'), ('routing table', '-r')]],
    [],
    [],
    ['folderpicker'],
    ['folderpicker', 'folderpicker', [('yes', '/e'), ('no', '')]],
    ['numinput'],
    ['filepicker'],
    ['filepicker', [('read-only', '+r'), ('hidden', '+h'), ('remove read-only', '-r'), ('remove hidden', '-h')]],
]

paramwidgets = []
paramkinds = []
paramoptmaps = []
curridx = -1


def apply_theme_to_titlebar(root):
    version = sys.getwindowsversion()
    if version.major == 10 and version.build >= 22000:
        pywinstyles.change_header_color(root, "#1c1c1c" if sv_ttk.get_theme() == "dark" else "#fafafa") #type: ignore
    elif version.major == 10:
        pywinstyles.apply_style(root, "dark" if sv_ttk.get_theme() == "dark" else "normal")#type: ignore
        root.wm_attributes("-alpha", 0.99)
        root.wm_attributes("-alpha", 1)


win = tk.Tk()
win.title("Terminal Command Generator - HyprTools")
win.geometry("880x460")

label_1 = tk.Label(win, text="Terminal Command Generator", font=('Courier', 28, 'bold'))
label_1.pack(pady=10)

frame_top = tk.Frame(win, padx=15, pady=15)
frame_top.pack(fill='x')

label_2 = tk.Label(frame_top, text="Preview:", font=("Courier", 12, "bold"))
label_2.pack(anchor='w')

frame_prevbox = ttk.Frame(frame_top, relief='solid', borderwidth=1, padding=10)
frame_prevbox.pack(fill='x', pady=5)

prevvar = tk.StringVar()
prevvar.set('')
label_prev = tk.Label(frame_prevbox, textvariable=prevvar, font=("Consolas", 13), wraplength=800, justify='left', anchor='w')
label_prev.pack(fill='x')

frame_mid = tk.Frame(win, padx=15, pady=15)
frame_mid.pack(fill='both', expand=True)

frame_row = tk.Frame(frame_mid)
frame_row.pack(anchor='w')


def refresh_preview():
    global curridx
    sel = dd1.get()
    if sel not in cmdlabels:
        prevvar.set('')
        return
    curridx = cmdlabels.index(sel)
    vals = []
    for i in range(len(paramwidgets)):
        w = paramwidgets[i]
        kind = paramkinds[i]
        if kind == 'dropdown':
            txt = w.get()
            m = paramoptmaps[i]
            vals.append(m[txt] if txt in m else '')
        elif kind == 'filepicker' or kind == 'folderpicker':
            p = w.pathval
            if p != '':
                vals.append('"' + p + '"')
            else:
                vals.append('')
        else:
            vals.append(w.get())
    try:
        out = cmdfmt[curridx].format(*vals)
    except:
        out = cmdfmt[curridx]
    while '  ' in out:
        out = out.replace('  ', ' ')
    prevvar.set(out.strip())


def pick_file(btn):
    p = filedialog.askopenfilename()
    if p:
        btn.pathval = p
        fname = p.split('/')[-1]
        btn.config(text=fname)
    refresh_preview()


def pick_folder(btn):
    p = filedialog.askdirectory()
    if p:
        btn.pathval = p
        fname = p.split('/')[-1]
        btn.config(text=fname)
    refresh_preview()


def build_params(event=None):
    global paramwidgets, paramkinds, paramoptmaps

    for w in frame_row.winfo_children():
        if w != dd1:
            w.destroy()
    paramwidgets = []
    paramkinds = []
    paramoptmaps = []

    sel = dd1.get()
    if sel not in cmdlabels:
        refresh_preview()
        return
    idx = cmdlabels.index(sel)

    plist = params[idx]
    vlist = paramvals[idx]

    for j in range(len(plist)):
        lbl = plist[j]
        val = vlist[j]

        pfr = tk.Frame(frame_row)
        pfr.pack(side='left', padx=8)
        lb = tk.Label(pfr, text=lbl, font=("Segoe UI Variable", 8))
        lb.pack(anchor='w')

        if type(val) == list:
            optmap = {}
            for pair in val:
                optmap[pair[0]] = pair[1]
            cb = ttk.Combobox(pfr, values=list(optmap.keys()), state='readonly', width=18)
            cb.current(0)
            cb.bind('<<ComboboxSelected>>', lambda e: refresh_preview())
            cb.pack()
            paramwidgets.append(cb)
            paramkinds.append('dropdown')
            paramoptmaps.append(optmap)

        elif val == 'numinput':
            sb = ttk.Spinbox(pfr, from_=0, to=9999, width=8, command=refresh_preview)
            sb.set(0)
            sb.bind('<KeyRelease>', lambda e: refresh_preview())
            sb.pack()
            paramwidgets.append(sb)
            paramkinds.append('num')
            paramoptmaps.append(None)

        elif val == 'filepicker':
            fbtn = ttk.Button(pfr, text="choose file")
            fbtn.pathval = ''#type: ignore
            fbtn.config(command=lambda b=fbtn: pick_file(b))
            fbtn.pack()
            paramwidgets.append(fbtn)
            paramkinds.append('filepicker')
            paramoptmaps.append(None)

        elif val == 'folderpicker':
            dbtn = ttk.Button(pfr, text="choose folder")
            dbtn.pathval = ''#type: ignore
            dbtn.config(command=lambda b=dbtn: pick_folder(b))
            dbtn.pack()
            paramwidgets.append(dbtn)
            paramkinds.append('folderpicker')
            paramoptmaps.append(None)

        else:
            ent = ttk.Entry(pfr, width=20)
            ent.bind('<KeyRelease>', lambda e: refresh_preview())
            ent.pack()
            paramwidgets.append(ent)
            paramkinds.append('text')
            paramoptmaps.append(None)

    refresh_preview()


dd1 = ttk.Combobox(frame_row, values=cmdlabels, state='readonly', width=22, font=("Segoe UI Variable", 10))
dd1.set('Select an action!')
dd1.pack(side='left')
dd1.bind('<<ComboboxSelected>>', build_params)

frame_bot = tk.Frame(win, padx=15, pady=15)
frame_bot.pack(fill='x', side='bottom')


def copy_cmd():
    win.clipboard_clear()
    win.clipboard_append(prevvar.get())
import os


def validate_params():
    for i in range(len(paramwidgets)):
        w = paramwidgets[i]
        kind = paramkinds[i]
        if kind == 'text' and w.get().strip() == '':
            messagebox.showwarning("Missing info", "Please fill in all fields before running.")
            return False
        if (kind == 'filepicker' or kind == 'folderpicker') and w.pathval == '':
            messagebox.showwarning("Missing info", "Please fill in all fields before running.")
            return False
    return True

def run_cmd():
    text = prevvar.get()
    if text == '':
        return
    if not validate_params():
        return
    yn = messagebox.askyesno("Run this?", "\n" + text)
    if yn == True:
        try:
            result = subprocess.run(text, shell=True, cwd=os.path.expanduser('~'), capture_output=True, text=True)
            if result.returncode != 0 or result.stderr.strip() != '':
                messagebox.showerror("Command failed to run", result.stderr.strip() if result.stderr.strip() != '' else "Unknown error")
            else:
                messagebox.showinfo("Command Run Sucesssful!", "\n Command run successfully!")
        except Exception as e:
            messagebox.showerror("Command failed to run", str(e))

btn_run = ttk.Button(frame_bot, text="Run", style="Accent.TButton", command=run_cmd)
btn_run.pack(side='right', padx=5)

btn_copy = ttk.Button(frame_bot, text="Copy", command=copy_cmd)
btn_copy.pack(side='right', padx=5)

system_theme = "dark" if darkdetect.isDark() else "light"
sv_ttk.set_theme(system_theme)
if pywinstyles:
    apply_theme_to_titlebar(win)

win.mainloop()