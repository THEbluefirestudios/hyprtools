import sys
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sv_ttk
import darkdetect
from PIL import Image, ImageTk, ImageFilter, ImageEnhance, ImageOps

try:
    import pywinstyles
except ImportError:
    pywinstyles = None

CANVW = 640
CANVH = 480

origimg = None      # untouched, loaded straight from disk, for reset
currentimg = None    # working image, every op applies here
history = []         # simple undo stack of PIL images

dispscale = 1.0
dispoffx = 0
dispoffy = 0

cropmode = False
cropclicks = []
cropmarkers = []


def apply_theme_to_titlebar(root):
    version = sys.getwindowsversion()
    if version.major == 10 and version.build >= 22000:
        pywinstyles.change_header_color(root, "#1c1c1c" if sv_ttk.get_theme() == "dark" else "#fafafa")  # type: ignore
    elif version.major == 10:
        pywinstyles.apply_style(root, "dark" if sv_ttk.get_theme() == "dark" else "normal")  # type: ignore
        root.wm_attributes("-alpha", 0.99)
        root.wm_attributes("-alpha", 1)

#setup main window
win = tk.Tk()
win.title("HyprPhotos - HyprTools")
win.geometry("980x710")
win.resizable(False, False)

label_1 = ttk.Label(win, text="HyprPhotos", font=('Courier', 22, 'bold'))
label_1.pack(pady=8)

frame_main = ttk.Frame(win)
frame_main.pack(fill='both', expand=True, padx=10)

frame_left = ttk.Frame(frame_main)
frame_left.pack(side='left', padx=10)

canvas_1 = tk.Canvas(frame_left, width=CANVW, height=CANVH, bg='#111111', highlightthickness=1, highlightbackground='#333333')
canvas_1.pack()

frame_openbar = ttk.Frame(frame_left)
frame_openbar.pack(fill='x', pady=8)

btn_open = ttk.Button(frame_openbar, text="Open image 📂")
btn_open.pack(side='left')

btn_save = ttk.Button(frame_openbar, text="Save as 💾")
btn_save.pack(side='left', padx=5)

btn_undo = ttk.Button(frame_openbar, text="Undo ↺")
btn_undo.pack(side='left', padx=5)

btn_reset = ttk.Button(frame_openbar, text="Reset to original ↩")
btn_reset.pack(side='left', padx=5)

statusvar = tk.StringVar()
statusvar.set(' ')
label_status = ttk.Label(frame_left, textvariable=statusvar, font=("Segoe UI Variable", 9))
label_status.pack(anchor='w')

frame_right = ttk.Frame(frame_main, padding=(10, 0))
frame_right.pack(side='left', fill='y')

#image preview

def push_history():
    global history
    if currentimg is not None:
        history.append(currentimg.copy())
        if len(history) > 15:
            history.pop(0)


def redraw_canvas():
    global dispscale, dispoffx, dispoffy
    canvas_1.delete('all')
    if currentimg is None:
        return

    iw, ih = currentimg.size
    scale = min(CANVW / iw, CANVH / ih)
    dispw = max(1, int(iw * scale))
    disph = max(1, int(ih * scale))
    dispscale = scale
    dispoffx = (CANVW - dispw) // 2
    dispoffy = (CANVH - disph) // 2

    dispimg_pil = currentimg.resize((dispw, disph), Image.LANCZOS) #type: ignore
    dispimg = ImageTk.PhotoImage(dispimg_pil)
    canvas_1.dispimgref = dispimg  #type: ignore

    canvas_1.create_image(dispoffx, dispoffy, image=dispimg, anchor='nw')

    for (mx, my) in cropmarkers:
        canvas_1.create_oval(mx - 4, my - 4, mx + 4, my + 4, outline="#0565f5", width=2)

    statusvar.set(f"{iw} x {ih} px")


def canvas_to_image_coords(cx, cy):
    ix = (cx - dispoffx) / dispscale
    iy = (cy - dispoffy) / dispscale
    ix = max(0, min(currentimg.size[0], ix))#type: ignore
    iy = max(0, min(currentimg.size[1], iy))#type: ignore
    return int(ix), int(iy)


def open_image():
    global origimg, currentimg, history
    p = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.webp *.gif")])
    if not p:
        return
    img = Image.open(p)
    if img.mode not in ('RGB', 'RGBA', 'L'):
        img = img.convert('RGBA')
    origimg = img.copy()
    currentimg = img.copy()
    history = []
    redraw_canvas()


def save_image():
    if currentimg is None:
        messagebox.showwarning("No image", "Open an image first.")
        return
    p = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("BMP", "*.bmp"), ("WEBP", "*.webp")])
    if not p:
        return
    outimg = currentimg
    if p.lower().endswith(('.jpg', '.jpeg')) and outimg.mode == 'RGBA':
        outimg = outimg.convert('RGB')
    outimg.save(p)
    messagebox.showinfo("Saved", "Image saved successfully!")


def undo():
    global currentimg
    if history:
        currentimg = history.pop()
        redraw_canvas()


def reset_to_original():
    global currentimg, history
    if origimg is not None:
        push_history()
        currentimg = origimg.copy()
        history = []
        redraw_canvas()


btn_open.config(command=open_image)
btn_save.config(command=save_image)
btn_undo.config(command=undo)
btn_reset.config(command=reset_to_original)


def on_canvas_click(event):
    global cropclicks, cropmode, cropmarkers, currentimg
    if not cropmode or currentimg is None:
        return

    ix, iy = canvas_to_image_coords(event.x, event.y)
    cropclicks.append((ix, iy))
    cropmarkers.append((event.x, event.y))
    redraw_canvas()

    if len(cropclicks) == 2:
        (x1, y1), (x2, y2) = cropclicks
        left = min(x1, x2)
        right = max(x1, x2)
        top = min(y1, y2)
        bottom = max(y1, y2)
        if right - left >= 2 and bottom - top >= 2:
            push_history()
            currentimg = currentimg.crop((left, top, right, bottom))
        cropclicks = []
        cropmarkers = []
        cropmode = False
        btn_crop_arm.config(text="Start crop ⏹️")# using emojis as icons, coz tkinter fonts are ancient and have the old win7 black and white emojis, and they look like vector icons so i use dem everywhere
        redraw_canvas()

# up/down scale + resize

canvas_1.bind('<Button-1>', on_canvas_click)

label_r1 = ttk.Label(frame_right, text="Resize", font=("Courier", 12, "bold"))
label_r1.pack(anchor='w', pady=(0, 4))

frame_r1 = ttk.Frame(frame_right)
frame_r1.pack(anchor='w', pady=2)
label_r2 = ttk.Label(frame_r1, text="Scale %:")
label_r2.pack(side='left')
entry_scalepct = ttk.Entry(frame_r1, width=8)
entry_scalepct.insert(0, "100")
entry_scalepct.pack(side='left', padx=5)

frame_r2 = ttk.Frame(frame_right)
frame_r2.pack(anchor='w', pady=2)
label_r3 = ttk.Label(frame_r2, text="Method:")
label_r3.pack(side='left')
dd_resample = ttk.Combobox(frame_r2, values=['Nearest Neighbor', 'Bilinear', 'Bicubic', 'Lanczos', 'Box', 'Hamming'], state='readonly', width=10)
dd_resample.current(3)
dd_resample.pack(side='left', padx=5)

resamplemap = {
    'Nearest Neighbor': Image.NEAREST, #type: ignore
    'Bilinear': Image.BILINEAR,#type: ignore
    'Bicubic': Image.BICUBIC,#type: ignore
    'Lanczos': Image.LANCZOS,#type: ignore
    'Box': Image.BOX,#type: ignore
    'Hamming': Image.HAMMING,#type: ignore
}

def apply_resize():
    global currentimg
    if currentimg is None:
        return

    try:
        pct = float(entry_scalepct.get())
    except ValueError:
        messagebox.showwarning("Invalid Value", "Scale % must be a number, u idiot.")
        return
    method = resamplemap[dd_resample.get()]
    iw, ih = currentimg.size
    neww = max(1, round(iw * pct / 100))
    newh = max(1, round(ih * pct / 100))
    if neww > 8000 or newh > 8000:
        messagebox.showwarning("Too large !", f"Resulting image would be {neww}x{newh}, which is too large for me to process :(. Try a smaller scale % plz.")
        return
    push_history()
    currentimg = currentimg.resize((neww, newh), method)
    redraw_canvas()



btn_resize = ttk.Button(frame_right, text="Apply resize", style="Accent.TButton", command=apply_resize)
btn_resize.pack(anchor='w', pady=(2, 12))

#rotate

label_ro1 = ttk.Label(frame_right, text="Rotate ", font=("Courier", 12, "bold"))
label_ro1.pack(anchor='w', pady=(0, 4))

frame_ro1 = ttk.Frame(frame_right)
frame_ro1.pack(anchor='w', pady=2)
label_ro2 = ttk.Label(frame_ro1, text="Angle:")
label_ro2.pack(side='left')
entry_angle = ttk.Entry(frame_ro1, width=8)
entry_angle.insert(0, "0")
entry_angle.pack(side='left', padx=5)


def apply_rotate_custom():
    global currentimg
    if currentimg is None:
        return
    try:
        angle = float(entry_angle.get())
    except ValueError:
        messagebox.showwarning("Invalid Value", "Angle must be a number, u idiot.")
        return
    push_history()
    currentimg = currentimg.rotate(-angle, expand=True)
    redraw_canvas()


def apply_rotate_quick(deg):
    global currentimg
    if currentimg is None:
        return
    push_history()
    currentimg = currentimg.rotate(-deg, expand=True)
    redraw_canvas()


btn_rotatego = ttk.Button(frame_ro1, text="Go", command=apply_rotate_custom)
btn_rotatego.pack(side='left')

frame_ro2 = ttk.Frame(frame_right)
frame_ro2.pack(anchor='w', pady=(2, 12))
btn_rot90 = ttk.Button(frame_ro2, text="90°", width=5, command=lambda: apply_rotate_quick(90))
btn_rot90.pack(side='left', padx=2)
btn_rot180 = ttk.Button(frame_ro2, text="180°", width=5, command=lambda: apply_rotate_quick(180))
btn_rot180.pack(side='left', padx=2)
btn_rot270 = ttk.Button(frame_ro2, text="270°", width=5, command=lambda: apply_rotate_quick(270))
btn_rot270.pack(side='left', padx=2)


#quick crop, i really like how this feature came out :)

label_c1 = ttk.Label(frame_right, text="Crop", font=("Courier", 12, "bold"))
label_c1.pack(anchor='w', pady=(0, 4))

label_c2 = ttk.Label(frame_right, text="Click on 2 points on the image", font=("Segoe UI Variable", 8), foreground="#535353")
label_c2.pack(anchor='w')


def toggle_crop_mode():
    global cropmode, cropclicks, cropmarkers
    cropmode = not cropmode
    cropclicks = []
    cropmarkers = []
    if cropmode:
        btn_crop_arm.config(text="Cancel crop")
    else:
        btn_crop_arm.config(text="Quick crop ⏹️")
    redraw_canvas()


btn_crop_arm = ttk.Button(frame_right, text="Quick crop ⏹️", command=toggle_crop_mode, style="Accent.TButton")
btn_crop_arm.pack(anchor='w', pady=(4, 12))

#flip

label_f1 = ttk.Label(frame_right, text="Flip", font=("Courier", 12, "bold"))
label_f1.pack(anchor='w', pady=(0, 4))

frame_f1 = ttk.Frame(frame_right)
frame_f1.pack(anchor='w', pady=2)


def apply_flip_h():
    global currentimg
    if currentimg is None:
        return
    push_history()
    currentimg = ImageOps.mirror(currentimg)
    redraw_canvas()


def apply_flip_v():
    global currentimg
    if currentimg is None:
        return
    push_history()
    currentimg = ImageOps.flip(currentimg)
    redraw_canvas()


def apply_grayscale():
    global currentimg
    if currentimg is None:
        return
    push_history()
    currentimg = ImageOps.grayscale(currentimg).convert('RGB')
    redraw_canvas()


btn_fliph = ttk.Button(frame_f1, text="Flip ↔", command=apply_flip_h, style = "Accent.TButton")
btn_fliph.pack(side='left', padx=2)
btn_flipv = ttk.Button(frame_f1, text="Flip ↕", command=apply_flip_v, style = "Accent.TButton")
btn_flipv.pack(side='left', padx=2)




frame_f2 = ttk.Frame(frame_right)
frame_f2.pack(anchor='w', pady=(8, 2))
label_f2 = ttk.Label(frame_f2, text="Blur radius:")
label_f2.pack(side='left')
entry_blur = ttk.Entry(frame_f2, width=6)
entry_blur.insert(0, "2")
entry_blur.pack(side='left', padx=5)


def apply_blur():
    global currentimg
    if currentimg is None:
        return
    try:
        radius = float(entry_blur.get())
    except ValueError:
        messagebox.showwarning("Invalid Value", "Blur radius must be a number, u idiot.")
        return
    push_history()
    currentimg = currentimg.filter(ImageFilter.GaussianBlur(radius))
    redraw_canvas()


btn_blur = ttk.Button(frame_f2, text="Blur", command=apply_blur)
btn_blur.pack(side='left')


def apply_sharpen():
    global currentimg
    if currentimg is None:
        return
    push_history()
    currentimg = currentimg.filter(ImageFilter.SHARPEN)
    redraw_canvas()


btn_sharpen = ttk.Button(frame_right, text="Sharpen", command=apply_sharpen)
btn_sharpen.pack(anchor='w', pady=(4, 12))



label_b1 = ttk.Label(frame_right, text="Tone and Color", font=("Courier", 12, "bold"))
label_b1.pack(anchor='w', pady=(0, 4))

frame_b1 = ttk.Frame(frame_right)
frame_b1.pack(anchor='w', pady=2)
label_b2 = ttk.Label(frame_b1, text="Brightness:")
label_b2.pack(side='left')
entry_bright = ttk.Entry(frame_b1, width=6)
entry_bright.insert(0, "1.0")
entry_bright.pack(side='left', padx=5)


def apply_brightness():
    global currentimg
    if currentimg is None:
        return
    try:
        factor = float(entry_bright.get())
    except ValueError:
        messagebox.showwarning("Invalid Value", "Brightness must be a number, u idiot.")
        return
    push_history()
    currentimg = ImageEnhance.Brightness(currentimg).enhance(factor)
    redraw_canvas()


btn_bright = ttk.Button(frame_b1, text="Go", command=apply_brightness)
btn_bright.pack(side='left')

frame_b2 = ttk.Frame(frame_right)
frame_b2.pack(anchor='w', pady=2)
label_b3 = ttk.Label(frame_b2, text="Contrast:\t")
label_b3.pack(side='left')
entry_contrast = ttk.Entry(frame_b2, width=6)
entry_contrast.insert(0, "1.0")
entry_contrast.pack(side='left', padx=5)


def apply_contrast():
    global currentimg
    if currentimg is None:
        return
    try:
        factor = float(entry_contrast.get())
    except ValueError:
        messagebox.showwarning("Invalid Value", "Contrast must be a number.")
        return
    push_history()
    currentimg = ImageEnhance.Contrast(currentimg).enhance(factor)
    redraw_canvas()


btn_contrast = ttk.Button(frame_b2, text="Go", command=apply_contrast)
btn_contrast.pack(side='left')
frame_b3 = ttk.Frame(frame_right)
frame_b3.pack(anchor='w', pady=2)
label_b4 = ttk.Label(frame_b3, text="Grayscale:\t")
label_b4.pack(side='left')
btn_gray = ttk.Button(frame_b3, text="Grayscale", command=apply_grayscale)
btn_gray.pack(side='left', padx=2)

system_theme = "dark" if darkdetect.isDark() else "light"
sv_ttk.set_theme(system_theme)
if pywinstyles:
    apply_theme_to_titlebar(win)

win.mainloop()