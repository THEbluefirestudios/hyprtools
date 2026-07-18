# pip install sv-ttk pywinstyles darkdetect
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sv_ttk
import darkdetect
import pywinstyles

#so the idea here is to just spam lists 

cmds = [
    'shutdown', 'echo', 'cd', 'ping', 'mkdir', 'del', 'copy', 'ipconfig',
    'dir', 'cls', 'tasklist', 'taskkill', 'netstat', 'systeminfo',
    'whoami', 'tree', 'xcopy', 'timeout', 'start', 'attrib',
]

cmdlabels = [ #for the boomers out there
    'Shut down or restart', 'Display a message', 'Change folder', 'Ping a host',
    'Make a new folder', 'Delete a file', 'Copy a file', 'Show network info',
    'List folder contents', 'Clear the screen', 'List running programs',
    'Close a program', 'Show network connections', 'Show system info',
    'Show current user', 'Show folder tree', 'Copy a folder', 'Wait a bit',
    'Open a program or file', 'Change file attributes',
]

cmdfmt = [#here i define num of params:)
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

params = [ #again, for the bommers out there
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
    ['filepicker'],
    ['numinput', 'input'],
    ['input'],
    ['filepicker'],
    ['filepicker', 'filepicker'],
    [],
    ['filepicker'],
    [],
    [],
    ['input', [('yes', '/f'), ('no', '')]],
    [[('all connections', '-a'), ('with process names', '-b'), ('routing table', '-r')]],
    [],
    [],
    ['filepicker'],
    ['filepicker', 'filepicker', [('yes', '/e'), ('no', '')]],
    ['numinput'],
    ['filepicker'],
    ['filepicker', [('read-only', '+r'), ('hidden', '+h'), ('remove read-only', '-r'), ('remove hidden', '-h')]],
]


def apply_theme_to_titlebar(root):#js copied from sv_ttk documentation
    version = sys.getwindowsversion()
    if version.major == 10 and version.build >= 22000:
        pywinstyles.change_header_color(root, "#1c1c1c" if sv_ttk.get_theme() == "dark" else "#fafafa")
    elif version.major == 10:
        pywinstyles.apply_style(root, "dark" if sv_ttk.get_theme() == "dark" else "normal")
        root.wm_attributes("-alpha", 0.99)
        root.wm_attributes("-alpha", 1)


root = tk.Tk()
root.title("Terminal command generator - Hyprtools")
root.geometry("850x460")

label_1 = ttk.Label(root, text="Terminal command generator", font=('Courier', 28, 'bold'))
label_1.pack(pady=10)

fr_top = ttk.Frame(root, padding=15)
fr_top.pack(fill='x')

lbl_prevtitle = ttk.Label(fr_top, text="preview", font=("Courier", 12, "bold"))
lbl_prevtitle.pack(anchor='w')

fr_previewbox = ttk.Frame(fr_top, relief='solid', borderwidth=1, padding=10)
fr_previewbox.pack(fill='x', pady=5)

var_preview = tk.StringVar(value='')
lbl_preview = ttk.Label(fr_previewbox, textvariable=var_preview, font=("Consolas", 13), wraplength=780, justify='left', anchor='w')
lbl_preview.pack(fill='x')

fr_mid = ttk.Frame(root, padding=15)
fr_mid.pack(fill='both', expand=True)

fr_row = ttk.Frame(fr_mid)
fr_row.pack(anchor='w')

paramgetters = []


def update_preview(*_):
    sel = dd1.get()
    if sel not in cmdlabels:
        var_preview.set('')
        return
    idx = cmdlabels.index(sel)
    vals = [g() for g in paramgetters]
    try:
        text = cmdfmt[idx].format(*vals)
    except IndexError:
        text = cmdfmt[idx]
    var_preview.set(' '.join(text.split()))


def clear_params():
    for w in fr_row.winfo_children()[1:]:
        w.destroy()
    paramgetters.clear()


def make_dropdown_param(parent, options): #saves a lot of code!, just make dropdown from the list of params!
    mapping = {d: v for d, v in options}
    cb = ttk.Combobox(parent, values=list(mapping.keys()), state='readonly', width=18)
    cb.current(0)
    cb.bind('<<ComboboxSelected>>', update_preview)

    def getter():
        return mapping.get(cb.get(), '')
    return cb, getter


def make_input_param(parent):
    ent = ttk.Entry(parent, width=20)
    ent.bind('<KeyRelease>', update_preview)

    def getter():
        return ent.get()
    return ent, getter


def make_numinput_param(parent):
    sb = ttk.Spinbox(parent, from_=0, to=9999, width=8, command=update_preview)
    sb.set(0)
    sb.bind('<KeyRelease>', update_preview)

    def getter():
        return sb.get()
    return sb, getter


def make_filepicker_param(parent):
    pathvar = tk.StringVar(value='')

    def pick():
        p = filedialog.askopenfilename()
        if p:
            pathvar.set(p)
            btn.configure(text=p.split('/')[-1])
            update_preview()

    btn = ttk.Button(parent, text="choose file", command=pick)

    def getter():
        return f'"{pathvar.get()}"' if pathvar.get() else ''
    return btn, getter


def on_cmd_select(event=None):
    clear_params()
    sel = dd1.get()
    if sel not in cmdlabels:
        update_preview()
        return
    idx = cmdlabels.index(sel)
    for label, valtype in zip(params[idx], paramvals[idx]):
        pfr = ttk.Frame(fr_row)
        pfr.pack(side='left', padx=8)
        ttk.Label(pfr, text=label, font=("Segoe UI Variable", 8)).pack(anchor='w')
        if isinstance(valtype, list):
            widget, getter = make_dropdown_param(pfr, valtype)
        elif valtype == 'numinput':
            widget, getter = make_numinput_param(pfr)
        elif valtype == 'filepicker':
            widget, getter = make_filepicker_param(pfr)
        else:
            widget, getter = make_input_param(pfr)
        widget.pack()
        paramgetters.append(getter)
    update_preview()


dd1 = ttk.Combobox(fr_row, values=cmdlabels, state='readonly', width=22, font=("Segoe UI Variable", 10))
dd1.pack(side='left')
dd1.bind('<<ComboboxSelected>>', on_cmd_select)

fr_bot = ttk.Frame(root, padding=15)
fr_bot.pack(fill='x', side='bottom')


def copy_cmd():
    root.clipboard_clear()
    root.clipboard_append(var_preview.get())


def run_cmd():
    text = var_preview.get()
    if not text:
        return
    if not messagebox.askyesno("run this?", f"run:\n{text}"):
        return
    subprocess.Popen(text, shell=True)


btn_run = ttk.Button(fr_bot, text="run", style="Accent.TButton", command=run_cmd)
btn_run.pack(side='right', padx=5)

btn_copy = ttk.Button(fr_bot, text="copy", command=copy_cmd)
btn_copy.pack(side='right', padx=5)

system_theme = "dark" if darkdetect.isDark() else "light"
sv_ttk.set_theme(system_theme)
apply_theme_to_titlebar(root)

root.mainloop()