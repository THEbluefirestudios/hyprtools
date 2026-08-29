import tkinter as tk
from tkinter import ttk, filedialog
import sv_ttk
import darkdetect #detecting the dark B)
import pywinstyles
import sys
import os
from PIL import Image, ImageDraw
from ascii_magic import AsciiArt as art

system_theme = "dark" if darkdetect.isDark() else "light"
selected_file = None


def apply_theme_to_titlebar(root):
    version = sys.getwindowsversion()
    if version.major == 10 and version.build >= 22000:
        pywinstyles.change_header_color(root, "#1c1c1c" if sv_ttk.get_theme() == "dark" else "#fafafa")
    elif version.major == 10:
        pywinstyles.apply_style(root, "dark" if sv_ttk.get_theme() == "dark" else "normal")
        root.wm_attributes("-alpha", 0.99)
        root.wm_attributes("-alpha", 1)


def pick_file():
    global selected_file
    path = filedialog.askopenfilename(
        title="Select an Image",
        filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.webp"), ("All files", "*.*")]
    )
    if path:
        selected_file = path
        label_2.config(text=os.path.basename(path))
    else:
        label_2.config(text="No file selected")


def get_bg_color():
    val = scale_1.get()
    hex_val = format(int(val), '02x')
    return f"#{hex_val}{hex_val}{hex_val}"


def build_ascii_image(char_data, bg_color, char_w=8, char_h=12):
    rows = len(char_data)
    cols = max(len(line) for line in char_data) if char_data else 0
    img_w = cols * char_w + 4
    img_h = rows * char_h + 4
    pil_img = Image.new('RGB', (img_w, img_h), bg_color)
    draw = ImageDraw.Draw(pil_img)
    for y, line in enumerate(char_data):
        for x, cell in enumerate(line):
            ch = cell.get('character', ' ')
            color_hex = cell.get('full-hex-color', '#ffffff')
            try:
                r = int(color_hex[1:3], 16)
                g = int(color_hex[3:5], 16)
                b = int(color_hex[5:7], 16)
                color = (r, g, b)
            except Exception:
                color = (255, 255, 255)
            draw.text((x * char_w + 2, y * char_h + 2), ch, fill=color)
    return pil_img


def char_data_to_html(char_data, bg_color):
    lines = []
    for line in char_data:
        row_html = []
        for cell in line:
            ch = cell.get('character', ' ')
            color_hex = cell.get('full-hex-color', '#ffffff')
            if ch == ' ':
                row_html.append('&nbsp;')
            else:
                ch_escaped = ch.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                row_html.append(f'<span style="color:{color_hex}">{ch_escaped}</span>')
        lines.append(''.join(row_html))
    body = '<br>'.join(lines)
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>ASCII Art</title>
<style>body{{background:{bg_color};font-family:monospace;white-space:nowrap;line-height:1;}}</style>
</head><body>{body}</body></html>"""

# so like it just wraps ascii magic
def convert():
    if not selected_file:
        label_5.config(text="Please select a file first.")
        return

    try:
        columns = int(entry_1.get())
    except ValueError:
        label_5.config(text="Invalid columns value.")
        return

    full_color = var_1.get()
    bg = get_bg_color()
    fmt = var_2.get()

    label_5.config(text="Converting...")
    win.update()

    try:
        image = art.from_image(selected_file)
        char_data = image.to_character_list(columns=columns, full_color=full_color, monochrome=not full_color, back=bg)#type: ignore

        if fmt == "png":
            save_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
            if save_path:
                pil_img = build_ascii_image(char_data, bg, char_w=8, char_h=12)
                pil_img.save(save_path)
                label_5.config(text=f"Saved to {os.path.basename(save_path)}")

        elif fmt == "html":
            save_path = filedialog.asksaveasfilename(defaultextension=".html", filetypes=[("HTML", "*.html")])
            if save_path:
                html_content = char_data_to_html(char_data, bg)
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                label_5.config(text=f"Saved to {os.path.basename(save_path)}")

        elif fmt == "txt":
            save_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text", "*.txt")])
            if save_path:
                with open(save_path, 'w', encoding='utf-8') as f:
                    for line in char_data:
                        f.write(''.join(cell.get('character', ' ') for cell in line) + '\n')
                label_5.config(text=f"Saved to {os.path.basename(save_path)}")

    except Exception as e:
        label_5.config(text=f"Error: {e}")


win = tk.Tk()
try:
    base = sys._MEIPASS#type: ignore
except AttributeError:
    base = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(base, "imgtoascii.png")
win.iconphoto(True, tk.PhotoImage(file=icon_path))
win.geometry('440x380')
win.title('Image to ASCII - HyprTools')

label_1 = ttk.Label(win, text="Image to ASCII", font=('Courier', 28, "bold"))
label_1.pack(pady=10)

frame_1 = ttk.Frame(win)
frame_1.pack(pady=5)
btn_1 = ttk.Button(frame_1, text="Pick Image", command=pick_file)
btn_1.pack(side='left', padx=5)
label_2 = ttk.Label(frame_1, text="No file selected", font=('Segoe UI Variable', 10))
label_2.pack(side='left')

var_1 = tk.BooleanVar(value=True)
check_1 = ttk.Checkbutton(win, text="Full Color", variable=var_1)
check_1.pack(pady=5)

label_3 = ttk.Label(win, text="Background color (Black → White)", font=('Segoe UI Variable', 10)) #dont question the variable names ok?
label_3.pack()
scale_1 = ttk.Scale(win, from_=0, to=255, orient='horizontal')
scale_1.set(0)
scale_1.pack(pady=2)

frame_2 = ttk.Frame(win)
frame_2.pack(pady=5)
label_4 = ttk.Label(frame_2, text="Columns:", font=('Segoe UI Variable', 10))
label_4.pack(side='left', padx=5)
entry_1 = ttk.Entry(frame_2, width=8)
entry_1.insert(0, "200")
entry_1.pack(side='left')

label_5 = ttk.Label(win, text="Output format:", font=('Segoe UI Variable', 10))
label_5.pack(pady=(10, 2))
var_2 = tk.StringVar(value="png")
frame_3 = ttk.Frame(win)
frame_3.pack()
for fmt in ["png", "html", "txt"]:
    ttk.Radiobutton(frame_3, text=fmt.upper(), variable=var_2, value=fmt).pack(side='left', padx=10)

btn_2 = ttk.Button(win, text="Convert & Save", style='Accent.TButton', command=convert)
btn_2.pack(pady=10)

label_5 = ttk.Label(win, text="", font=('Segoe UI Variable', 10))
label_5.pack()

sv_ttk.set_theme(system_theme)
apply_theme_to_titlebar(win)

win.mainloop()