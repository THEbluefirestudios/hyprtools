import sys
import os
import io
import asyncio
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sv_ttk
import darkdetect
from PIL import Image, ImageGrab, ImageTk
from winsdk.windows.media.ocr import OcrEngine
from winsdk.windows.graphics.imaging import BitmapDecoder
from winsdk.windows.storage.streams import InMemoryRandomAccessStream, DataWriter

try:
    import pywinstyles
except ImportError:
    pywinstyles = None

#

loadedimg = None

PREVW = 300
PREVH = 220


def apply_theme_to_titlebar(root):
    version = sys.getwindowsversion()
    if version.major == 10 and version.build >= 22000:
        pywinstyles.change_header_color(root, "#1c1c1c" if sv_ttk.get_theme() == "dark" else "#fafafa")  # type: ignore
    elif version.major == 10:
        pywinstyles.apply_style(root, "dark" if sv_ttk.get_theme() == "dark" else "normal")  # type: ignore
        root.wm_attributes("-alpha", 0.99)
        root.wm_attributes("-alpha", 1)


async def ocr_image_async(pil_img):
    buf = io.BytesIO()
    pil_img.save(buf, format='PNG')
    data = buf.getvalue()

    stream = InMemoryRandomAccessStream()
    writer = DataWriter(stream.get_output_stream_at(0))
    writer.write_bytes(bytearray(data))#type: ignore
    await writer.store_async()
    await writer.flush_async()
    stream.seek(0)

    decoder = await BitmapDecoder.create_async(stream)#type: ignore
    bitmap = await decoder.get_software_bitmap_async()

    engine = OcrEngine.try_create_from_user_profile_languages()
    if engine is None:
        raise RuntimeError("No OCR engine available")

    result = await engine.recognize_async(bitmap)
    return result.text


win = tk.Tk()
try:
    base = sys._MEIPASS
except AttributeError:
    base = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(base, "hyprocr.png")
win.iconphoto(True, tk.PhotoImage(file=icon_path))
win.title("HyprOCR - HyprTools")
win.geometry("620x560")

label_1 = ttk.Label(win, text="HyprOCR", font=('Courier', 26, 'bold'))
label_1.pack(pady=10)

frame_top = ttk.Frame(win, padding=(20, 5))
frame_top.pack(fill='x')

btn_open = ttk.Button(frame_top, text="Open image...")
btn_open.pack(side='left')

btn_paste = ttk.Button(frame_top, text="Paste from clipboard (Ctrl+V)")
btn_paste.pack(side='left', padx=8)

frame_prev = ttk.Frame(win, padding=(20, 5))
frame_prev.pack()

canvas_1 = tk.Canvas(frame_prev, width=PREVW, height=PREVH, bg='#111111', highlightthickness=1, highlightbackground='#333333')
canvas_1.pack()

label_placeholder = ttk.Label(canvas_1, text="Open or paste an image to begin", font=("Segoe UI Variable", 10), foreground="#535353")
canvas_1.create_window(PREVW // 2, PREVH // 2, window=label_placeholder)

frame_mid = ttk.Frame(win, padding=(20, 10))
frame_mid.pack(fill='both', expand=True)

label_2 = ttk.Label(frame_mid, text="Extracted text:", font=("Courier", 11, "bold"))
label_2.pack(anchor='w')

txt_out = tk.Text(
    frame_mid, height=10, font=("Consolas", 10), wrap='word',
    bg='#1c1c1c', fg='#ffffff', insertbackground='#ffffff',
    relief='flat', highlightthickness=1, highlightbackground='#333333',
    highlightcolor='#0078d4', padx=8, pady=8,
)
txt_out.pack(fill='both', expand=True, pady=5)

frame_bot = ttk.Frame(win, padding=(20, 10))
frame_bot.pack(fill='x', side='bottom')

statusvar = tk.StringVar()
statusvar.set('Ready')
label_status = ttk.Label(frame_bot, textvariable=statusvar, font=("Segoe UI Variable", 9))
label_status.pack(side='left')


def show_preview(img):
    canvas_1.delete('all')
    iw, ih = img.size
    scale = min(PREVW / iw, PREVH / ih)
    dispw = max(1, int(iw * scale))
    disph = max(1, int(ih * scale))
    dispimg = ImageTk.PhotoImage(img.resize((dispw, disph), Image.LANCZOS)) #type: ignore
    canvas_1.dispimgref = dispimg  #type: ignore
    offx = (PREVW - dispw) // 2
    offy = (PREVH - disph) // 2
    canvas_1.create_image(offx, offy, image=dispimg, anchor='nw')


def run_ocr():
    global loadedimg
    if loadedimg is None:
        return
    statusvar.set('Reading text...')
    win.update()
    try:
        text = asyncio.run(ocr_image_async(loadedimg))
        txt_out.delete('1.0', 'end')
        txt_out.insert('1.0', text.strip())
        statusvar.set('Done')
    except Exception as e:
        messagebox.showerror("OCR failed", str(e))
        statusvar.set('Ready')


def open_image():
    global loadedimg
    p = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.webp *.tiff *.tif")])
    if not p:
        return
    loadedimg = Image.open(p)
    show_preview(loadedimg)
    run_ocr()


def paste_image(event=None):
    global loadedimg
    clip = ImageGrab.grabclipboard()

    if clip is None:
        statusvar.set('Nothing usable on clipboard')
        return

    if isinstance(clip, list):
        # clipboard had file path(s), not raw image data
        if len(clip) == 0:
            statusvar.set('Nothing usable on clipboard')
            return
        try:
            loadedimg = Image.open(clip[0])
        except Exception:
            statusvar.set('Clipboard file is not an image')
            return
    else:
        loadedimg = clip

    show_preview(loadedimg)
    run_ocr()


btn_open.config(command=open_image)
btn_paste.config(command=paste_image)
win.bind('<Control-v>', paste_image)


def copy_text():
    win.clipboard_clear()
    win.clipboard_append(txt_out.get('1.0', 'end-1c'))
    statusvar.set('Copied to clipboard')


btn_copy = ttk.Button(frame_bot, text="Copy text", style="Accent.TButton", command=copy_text)
btn_copy.pack(side='right')

system_theme = "dark" if darkdetect.isDark() else "light"
sv_ttk.set_theme(system_theme)
if pywinstyles:
    apply_theme_to_titlebar(win)

win.mainloop()