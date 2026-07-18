import sys
import os
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sv_ttk
import darkdetect
from PIL import Image

try: # again, jic
    import pywinstyles
except ImportError:
    pywinstyles = None

FFMPEG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ffmpeg.exe") #absolute path jus to be safe

cat_exts = { #cats such a cute shortform for 'category' ^owo^
    'image': ['jpg', 'jpeg', 'png', 'webp', 'bmp', 'gif', 'ico', 'tiff'],
    'audio': ['mp3', 'wav', 'flac', 'ogg', 'aac', 'm4a', 'wma'], #some extensions
    'video': ['mp4', 'mkv', 'webm', 'avi', 'mov', 'flv', 'wmv'],
}


def detect_cat(path): 
    ext = path.split('.')[-1].lower()
    for cat, exts in cat_exts.items():
        if ext in exts:
            return cat
    return ''


def convert(input_path, output_path):
    cat = detect_cat(input_path)

    if cat == 'image':
        img = Image.open(input_path)
        target_ext = output_path.split('.')[-1].lower()
        if target_ext in ('jpg', 'jpeg') and img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        img.save(output_path)
        return None

    elif cat in ('audio', 'video'):
        return subprocess.run(
            [FFMPEG_PATH, '-i', input_path, '-y', output_path],
            capture_output=True, text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

    else:
        raise ValueError("unsupported file type")


#NOW WE BEGIN..... THE GUUIIIIIIIIIIIII

inputpath = ''
inputname = ''
inputcat = ''


def apply_theme_to_titlebar(root): # copied form sv_ttk readme
    version = sys.getwindowsversion()
    if version.major == 10 and version.build >= 22000:
        pywinstyles.change_header_color(root, "#1c1c1c" if sv_ttk.get_theme() == "dark" else "#fafafa")  # type: ignore
    elif version.major == 10:
        pywinstyles.apply_style(root, "dark" if sv_ttk.get_theme() == "dark" else "normal")  # type: ignore
        root.wm_attributes("-alpha", 0.99)
        root.wm_attributes("-alpha", 1)

win = tk.Tk()
win.title("File Converter - HyprTools")
win.geometry("360x120")

label_1 = ttk.Label(win, text="File Converter", font=('Courier', 28, 'bold'))
label_1.pack(pady=10)

btn_pick = ttk.Button(win, text="Choose file...")
btn_pick.pack(pady=5)

frame_mid = ttk.Frame(win, padding=(20, 15))
frame_mid.pack(fill='x')

frame_fileinfo = ttk.Frame(frame_mid)
frame_fileinfo.pack(side='left')

label_emoji = ttk.Label(frame_fileinfo, text='', font=('Segoe UI Emoji', 28))
label_emoji.pack(side='left', padx=(0, 10))

filevar = tk.StringVar()
filevar.set('')
label_file = ttk.Label(frame_fileinfo, textvariable=filevar, font=("Consolas", 11))
label_file.pack(side='left')

dd1 = ttk.Combobox(frame_mid, values=[], state='readonly', width=12, font=("Segoe UI Variable", 10))


def pick_file():
    global inputpath, inputname, inputcat
    p = filedialog.askopenfilename()
    if not p:
        return
    cat = detect_cat(p)
    if cat == '':
        messagebox.showwarning("Unsupported file", "That file type isn't image, audio, or video.")
        return

    inputpath = p
    fullname = p.split('/')[-1]
    inputname = os.path.splitext(fullname)[0]
    inputcat = cat

    if cat == 'image':
        label_emoji.config(text='🖼️')# GUYS IM NOT USING AI HERE, IM JUST TOO LAZY TO ACUALLY USE PROPER ICONS, also they look like normal icons with the segoe emoji font
    elif cat == 'audio':
        label_emoji.config(text='🎵')
    elif cat == 'video':
        label_emoji.config(text='🎬')
    else:
        label_emoji.config(text='❓')

    filevar.set(fullname)

    opts = list(cat_exts[cat])
    curr_ext = fullname.split('.')[-1].lower()
    if curr_ext in opts:
        opts.remove(curr_ext)
    dd1.config(values=opts)
    if len(opts) > 0:
        win.geometry("640x360")
        dd1.current(0)
        dd1.pack(side='right')
        
        btn_convert.pack(side='bottom')

btn_pick.config(command=pick_file)

frame_bot = ttk.Frame(win, padding=(20, 15))
frame_bot.pack(fill='x', side='bottom')

def show_loading():
    load_win = tk.Toplevel(win)
    load_win.title("Converting...")
    load_win.geometry("300x100")
    load_win.resizable(False, False)
    load_win.transient(win)
    load_win.grab_set()

    lbl = ttk.Label(load_win, text="Converting, please wait...", font=("Segoe UI Variable", 10))
    lbl.pack(pady=10)

    pb = ttk.Progressbar(load_win, mode='indeterminate', length=200)
    pb.pack(pady=5)
    pb.start(10)

    return load_win # lit js tkinter's progressbar

def do_convert(outputdir):
    outputext = dd1.get()
    outputpath = os.path.join(outputdir, inputname + '.' + outputext)

    load_win = show_loading()

    def worker():
        err = None
        try:
            result = convert(inputpath, outputpath)
            if result is not None and result.returncode != 0:
                err = result.stderr.strip()[-500:]
        except Exception as e:
            err = str(e)

        def finish():
            load_win.destroy()
            if err:
                messagebox.showerror("Conversion failed", err if err != '' else "Unknown error")
            else:
                messagebox.showinfo("Success!", "\nFile converted successfully!")

        win.after(0, finish)

    threading.Thread(target=worker, daemon=True).start() # i got to do this coz tkinter is A PIECE OF SHIT AND I DONT WANNA LEARN FLET


def convert_click():
    if inputpath == '':
        messagebox.showwarning("No file", "Choose a file first.")
        return
    if dd1.get() == '':
        messagebox.showwarning("No format", "Pick a target format first.")
        return

    outputdir = filedialog.askdirectory()
    if not outputdir:
        return

    do_convert(outputdir) #func for the convert button down... there v

btn_convert = ttk.Button(frame_bot, text="Convert!", style="Accent.TButton", command=convert_click)


system_theme = "dark" if darkdetect.isDark() else "light"
sv_ttk.set_theme(system_theme)
if pywinstyles:
    apply_theme_to_titlebar(win)

win.mainloop()
