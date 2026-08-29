import vlc
import tkinter as tk
import os
import sys
import ctypes

script_dir = os.path.dirname(os.path.abspath(__file__))
is_win11 = sys.getwindowsversion().build >= 22000

try:
    base = sys._MEIPASS
except AttributeError:
    base = script_dir

if is_win11:
    vido_path = os.path.join(base, "win11_upd.mp4") #misspelling on urpose coz there is a different video_path= param in my func
else:
    vido_path = os.path.join(base, "win10_upd.mp4")

def play_fake_update(video_path):
    root = tk.Tk()
    root.attributes('-fullscreen', True)
    root.attributes('-topmost', True)
    root.config(cursor="none", bg="black")

    instance = vlc.Instance()
    player = instance.media_player_new()#type: ignore
    media = instance.media_new(video_path)#type: ignore
    player.set_media(media)

    player.set_hwnd(root.winfo_id())
    player.play()

    root.bind('<Escape>', lambda e: (player.stop(), root.destroy()))
    root.mainloop()

play_fake_update(vido_path)
#ctypes.windll.user32.LockWorkStation()
