#hello sw/goi, u may have seen that i am using emojis in this and other files, rest assured it is not coz im using ai, 
#its coz i wanted monochrome icons, and emojis are monochrome in tkinter and no extra import/assets so i went with it
#dw ill stop using tkinter
import subprocess
import ctypes
import sys
import pyautogui as mouse
from time import sleep
import re
import os
import shutil
import winreg
import json
import threading
from random import choice

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk

try:
    import sv_ttk
except ImportError:
    sv_ttk = None

try:
    import darkdetect
except ImportError:
    darkdetect = None

try:
    import pywinstyles
except ImportError:
    pywinstyles = None

# actual backend and logic

if not ctypes.windll.shell32.IsUserAnAdmin():
    if getattr(sys, 'frozen', False):
        params = f'"{sys.executable}"'
    else:
        params = f'"{os.path.abspath(__file__)}"'
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
    sys.exit()

if getattr(sys, 'frozen', False):
    SCRIPT_DIR = os.path.dirname(sys.executable)
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.join(SCRIPT_DIR, "tools")
LOG_FILE_PATH = os.path.join(TOOLS_DIR, "move_log.txt")
JSONPATH = os.path.join(TOOLS_DIR, "hyprtools.json")

ICON_CACHE = {}


def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS#type: ignore
    except AttributeError:
        base_path = SCRIPT_DIR
    return os.path.join(base_path, relative_path)


def get_tool_icon(tool_name, size=(20, 20)):
    cache_key = (tool_name, size)
    if cache_key in ICON_CACHE:
        return ICON_CACHE[cache_key]

    filename_map = {
        'hyprclickr': 'hyprclicker.png',
        'fileconv': 'fileconvert.png',
        'fakeerr': 'bsod_blue.png',
        'fakeupd': 'hyprtools.png',
        'hyprtools': 'hyprtools.png',
    }
    fname = filename_map.get(tool_name, f"{tool_name}.png")

    paths_to_check = [
        get_resource_path(os.path.join("tools", fname)),
        get_resource_path(fname),
        get_resource_path(os.path.join("doneicons", fname)),
        get_resource_path(os.path.join("tools", "hyprtools.png")),
    ]

    for p in paths_to_check:
        if os.path.exists(p):
            try:
                pil_img = Image.open(p).resize(size, Image.LANCZOS)#type: ignore
                tk_img = ImageTk.PhotoImage(pil_img)
                ICON_CACHE[cache_key] = tk_img
                return tk_img
            except Exception:
                pass
    return None


def apply_theme_to_titlebar(root):
    try:
        if sv_ttk and pywinstyles:
            version = sys.getwindowsversion()
            theme = sv_ttk.get_theme()
            if version.major == 10 and version.build >= 22000:
                pywinstyles.change_header_color(root, "#1c1c1c" if theme == "dark" else "#fafafa")
            elif version.major == 10:
                pywinstyles.apply_style(root, "dark" if theme == "dark" else "normal")
                root.wm_attributes("-alpha", 0.99)
                root.wm_attributes("-alpha", 1)
    except Exception:
        pass


def set_app_icon(win):
    hypr_p = get_resource_path(os.path.join("tools", "hyprtools.png"))
    if not os.path.exists(hypr_p):
        hypr_p = get_resource_path("hyprtools.png")

    if os.path.exists(hypr_p):
        try:
            win.iconphoto(True, tk.PhotoImage(file=hypr_p))
            return
        except Exception:
            pass

    for icon_name in ['hyprpicker.png', 'hyprsearch.png', 'hyprvoice.png']:
        icon_p = get_resource_path(os.path.join("doneicons", icon_name))
        if not os.path.exists(icon_p):
            icon_p = get_resource_path(os.path.join("tools", icon_name))
        if os.path.exists(icon_p):
            try:
                win.iconphoto(True, tk.PhotoImage(file=icon_p))
                break
            except Exception:
                pass


def load_hyprtools_settings():
    if os.path.exists(JSONPATH):
        try:
            with open(JSONPATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_hyprtools_setting(key, value):
    data = load_hyprtools_settings()
    data[key] = value
    try:
        with open(JSONPATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception:
        pass


def run_cmd(command):
    result = subprocess.run(command, capture_output=True, text=True, shell=True)
    return result.stdout, result.stderr


def fix_my_pc():
    process = subprocess.Popen(
        'DISM /Online /Cleanup-Image /RestoreHealth',
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        encoding='utf-8', shell=True
    )
    dism_out, dism_err = process.communicate()

    if dism_err:
        return "DISM error: " + str(dism_err)
    sfc_out, sfc_err = run_cmd('sfc /scannow')
    if sfc_err:
        return "SFC error: " + str(sfc_err)

    return "done"


def pc_stress_test():
    def remap_score(s):
        old_min, old_max = 6.0, 9.9
        score = (s - old_min) / (old_max - old_min) * 9.0 + 1.0
        return round(max(1.0, min(10.0, score)), 1)

    run_cmd('winsat dwm')
    out, err = run_cmd('powershell -Command "Get-CimInstance Win32_WinSAT | Select-Object CPUScore, DiskScore, GraphicsScore, MemoryScore, WinSPRLevel | Format-List"')

    if err and not out:
        return {"error": err.strip()}

    scores = {}
    for line in out.splitlines():
        if ':' in line:
            key, val = line.split(':', 1)
            try:
                scores[key.strip()] = remap_score(float(val.strip()))
            except ValueError:
                pass

    return scores if scores else {"error": "Failed to retrieve scores."}


def delete_temp():
    out, err = run_cmd('del /q /f /s %temp%\\*')
    return "error: " + err.strip() if err else "done"


def update_all():
    out, err = run_cmd('winget upgrade --all --include-unknown --accept-package-agreements --accept-source-agreements')
    return out, err


def refresh_display():
    mouse.hotkey('win', 'ctrl', 'shift', 'b')


def wifi_reset():
    out, err = run_cmd('ipconfig /flushdns')
    return "error: " + err.strip() if err else "done"


STARTUP_APPROVED_RUN = r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run"
RUN_KEYS = [
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
]

STARTUP_FOLDERS = [
    os.path.join(os.getenv("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Startup"),
    os.path.join(os.getenv("PROGRAMDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Startup"),
]
DISABLED_SUBDIR = "HyprTools_Disabled"


def _is_enabled_registry(name):
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_APPROVED_RUN) as key:
            data, _ = winreg.QueryValueEx(key, name)
            return data[0] == 0x02
    except FileNotFoundError:
        return True
    except OSError:
        return True


def _set_enabled_registry(name, enabled):
    try:
        key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, STARTUP_APPROVED_RUN, 0, winreg.KEY_ALL_ACCESS)
    except OSError:
        return False
    try:
        try:
            existing, _ = winreg.QueryValueEx(key, name)
            data = bytearray(existing)
        except FileNotFoundError:
            data = bytearray(12)
        data[0] = 0x02 if enabled else 0x03
        winreg.SetValueEx(key, name, 0, winreg.REG_BINARY, bytes(data))
        return True
    finally:
        winreg.CloseKey(key)


def get_registry_startup_items():
    items = []
    for hive, path in RUN_KEYS:
        try:
            with winreg.OpenKey(hive, path) as key:
                i = 0
                while True:
                    try:
                        name, command, _ = winreg.EnumValue(key, i)
                        items.append({
                            "name": name,
                            "command": command,
                            "source": "HKCU Run" if hive == winreg.HKEY_CURRENT_USER else "HKLM Run",
                            "type": "registry",
                            "enabled": _is_enabled_registry(name),
                        })
                        i += 1
                    except OSError:
                        break
        except FileNotFoundError:
            continue
    return items


def get_folder_startup_items():
    items = []
    for folder in STARTUP_FOLDERS:
        if not os.path.isdir(folder):
            continue
        for fname in os.listdir(folder):
            if fname == DISABLED_SUBDIR:
                continue
            full = os.path.join(folder, fname)
            if os.path.isfile(full):
                items.append({
                    "name": fname,
                    "command": full,
                    "source": folder,
                    "type": "folder",
                    "enabled": True,
                })
        disabled_dir = os.path.join(folder, DISABLED_SUBDIR)
        if os.path.isdir(disabled_dir):
            for fname in os.listdir(disabled_dir):
                items.append({
                    "name": fname,
                    "command": os.path.join(disabled_dir, fname),
                    "source": folder,
                    "type": "folder",
                    "enabled": False,
                })
    return items


def get_all_startup_items():
    return get_registry_startup_items() + get_folder_startup_items()


DEFINITE_PATTERNS = [
    r"onedrive",
    r"microsoft edge update",
    r"edgeupdate",
    r"adobe.*updater",
    r"acrord32|acrotray|reader_sl",
    r"quicktime",
    r"realplayer",
    r"itunes.*helper",
    r"apple.*(push|mobile).*service",
    r"java.*update.*scheduler|jusched",
    r"cc(x)?process|creative cloud",
    r"skype",
    r"spotify.*(helper|autostart)",
    r"dropbox.*update",
    r"bonjour",
    r"realtek hd audio manager",
    r"cortana",
    r"copilot",
    r"microsoft.*(office|onenote|outlook|word|excel|powerpoint)",
    r"mcafee",
    r"norton|nortonsecurity|nls",
    r"avg", # y r u lowk using these in 2026 vro
    r"avira",
]

MAYBE_PATTERNS = [
    r"steam",
    r"discord",
    r"whatsapp",
    r"telegram",
    r"icue|corsair",
    r"razer.*synapse",
    r"logitech.*(g ?hub|options)",
    r"msi.*(afterburner|center|dragon)",
    r"asus.*(armoury|aura)",
    r"lenovo.*(legion|thinkpad)",
    r"nvidia.*(geforce experience|share)",
    r"epic.*games.*launcher",
    r"battle\.net",
    r"origin",
    r"ea desktop",
    r"riot.*client",
    r"teams",
    r"zoom",
    r"slack",
    r"nahimic",
]

_definite_re = re.compile("|".join(DEFINITE_PATTERNS), re.IGNORECASE)
_maybe_re = re.compile("|".join(MAYBE_PATTERNS), re.IGNORECASE)


def classify_item(item):
    haystack = f"{item['name']} {item['command']}"
    if _definite_re.search(haystack):
        return "definite"
    if _maybe_re.search(haystack):
        return "maybe"
    return "unknown"


def classify_startup_items(items):
    definite, maybe, unknown = [], [], []
    for item in items:
        tier = classify_item(item)
        if tier == "definite":
            definite.append(item)
        elif tier == "maybe":
            maybe.append(item)
        else:
            unknown.append(item)
    return definite, maybe, unknown


DIRECTORIES = {
    "Images": [".jpeg", ".jpg", ".tiff", ".tif", ".gif", ".bmp", ".png", ".bpg", ".svg", ".heif", ".heic", ".psd", ".ai", ".eps", ".raw", ".cr2", ".nef", ".orf", ".sr2", ".webp", ".jfif", ".ico", ".dds", ".xcf", ".indd", ".jp2", ".avif"],
    "Fonts": [".fnt", ".fon", ".otf", ".ttf", ".woff", ".woff2", ".eot", ".pfb", ".pfm"],
    "Icons": [".ico", ".icns", ".cur"],
    "Videos": [".avi", ".flv", ".wmv", ".mov", ".mp4", ".webm", ".vob", ".mng", ".qt", ".mpg", ".mpeg", ".3gp", ".3g2", ".mkv", ".m4v", ".ogv", ".rm", ".rmvb", ".ts", ".mts", ".m2ts", ".divx", ".f4v"],
    "Documents": [".oxps", ".epub", ".pages", ".docx", ".doc", ".fdf", ".ods", ".odt", ".pwn", ".pdf", ".xls", ".xlsx", ".ppt", ".pptx", ".rtf", ".tex", ".md", ".odp", ".csv", ".tsv", ".numbers", ".key", ".mobi", ".azw", ".azw3", ".chm", ".wpd", ".wps", ".xps"],
    "Archives": [".a", ".ar", ".cpio", ".iso", ".tar", ".gz", ".tgz", ".rz", ".7z", ".dmg", ".rar", ".xar", ".zip", ".bz2", ".xz", ".lz", ".lzma", ".z", ".cab", ".arj", ".img", ".pkg"],
    "Audio": [".aac", ".aa", ".dvf", ".m4a", ".m4b", ".m4p", ".mp3", ".msv", ".ogg", ".oga", ".opus", ".raw", ".vox", ".wav", ".wma", ".flac", ".alac", ".aiff", ".aif", ".mid", ".midi", ".amr", ".ac3", ".dts", ".ra"],
    "Text": [".txt", ".in", ".out", ".log", ".ini", ".cfg", ".conf", ".env", ".nfo", ".readme", ".diz"],
    "Code": [".py", ".cpp", ".c", ".h", ".hpp", ".java", ".js", ".jsx", ".tsx", ".html", ".htm", ".css", ".scss", ".sass", ".less", ".sh", ".swift", ".pyw", ".ipynb", ".r", ".pl", ".rb", ".go", ".rs", ".ts", ".php", ".yaml", ".yml", ".json", ".xml", ".sql", ".bat", ".ps1", ".vbs", ".asm", ".s", ".d", ".erl", ".hs", ".lisp", ".lua", ".ml", ".nim", ".pas", ".rkt", ".scm", ".kt", ".kts", ".dart", ".scala", ".clj", ".ex", ".exs", ".m", ".mm", ".vue", ".svelte", ".toml", ".gradle", ".makefile", ".cmake", ".dockerfile", ".proto", ".jl"],
    "Executables": [".exe", ".msi", ".bin", ".app", ".bat", ".command", ".run", ".apk", ".appimage", ".deb", ".rpm", ".jar", ".gadget", ".wsf", ".vb", ".cgi", ".out"],
    "Ebooks": [".epub", ".mobi", ".azw", ".azw3", ".fb2", ".lit", ".pdb", ".ibooks"],
    "Models": [".stl", ".obj", ".fbx", ".dae", ".3ds", ".blend", ".dwg", ".dxf", ".step", ".stp", ".iges", ".igs", ".skp", ".ply", ".gltf", ".glb"],
    "Disc_images": [".iso", ".img", ".vhd", ".vhdx", ".vmdk", ".ova", ".ovf", ".qcow2"],
    "Databases": [".db", ".sqlite", ".sqlite3", ".mdb", ".accdb", ".dbf", ".sql", ".bak"],
    "Torrents": [".torrent"],
    "Subtitles": [".srt", ".sub", ".ass", ".ssa", ".vtt"],
    "Certificate_keys": [".pem", ".crt", ".cer", ".key", ".pfx", ".p12", ".csr", ".der"],
    "System": [".dll", ".sys", ".drv", ".ocx", ".reg", ".lnk", ".ini", ".manifest"],
}


def organize(target_path):
    extension_lookup = {ext: dest for dest, exts in DIRECTORIES.items() for ext in exts}
    this_script = os.path.basename(__file__)

    if not os.path.exists(target_path):
        return {"success": False, "error": f"Path {target_path} not found.", "count": 0}

    count = 0
    errors = []

    with open(LOG_FILE_PATH, "a", encoding="utf-8") as log:
        for filename in os.listdir(target_path):
            file_path = os.path.join(target_path, filename)
            if os.path.isdir(file_path) or filename == this_script or filename == "move_log.txt":
                continue

            ext = os.path.splitext(filename)[1].lower()
            category = extension_lookup.get(ext, "Other")
            target_folder = os.path.join(target_path, category)

            os.makedirs(target_folder, exist_ok=True)
            dest_path = os.path.join(target_folder, filename)

            try:
                shutil.move(file_path, dest_path)
                log.write(f"{dest_path}|{file_path}\n")
                count += 1
            except Exception as e:
                errors.append(f"Error moving {filename}: {e}")

    return {"success": True, "count": count, "errors": errors}


def undo():
    if not os.path.exists(LOG_FILE_PATH):
        return {"success": False, "error": "No log file found. Nothing to undo."}

    with open(LOG_FILE_PATH, "r", encoding="utf-8") as log:
        lines = log.readlines()

    if not lines:
        return {"success": False, "error": "Log is empty."}

    touched_folders = set()
    errors = []
    restored = 0

    for line in reversed(lines):
        line = line.strip()
        if "|" not in line: continue
        current_path, original_path = line.split("|")

        touched_folders.add(os.path.dirname(current_path))

        if os.path.exists(current_path):
            try:
                shutil.move(current_path, original_path)
                restored += 1
            except Exception as e:
                errors.append(f"Error restoring {current_path}: {e}")

    for folder in touched_folders:
        try:
            if os.path.isdir(folder) and not os.listdir(folder):
                os.rmdir(folder)
        except Exception as e:
            errors.append(f"Error removing folder {folder}: {e}")

    os.remove(LOG_FILE_PATH)
    return {"success": True, "restored": restored, "errors": errors}


def set_hyprtool_as_startup(name):
    tools = {
        'hyprsearch': "HyprSearch.exe",
        'hyprvoice': "HyprVoice.exe",
        'hyprpicker': "HyprPicker.exe",
    }
    if name not in tools:
        return ValueError("Invalid name. Must be 'hyprsearch', 'hyprvoice', or 'hyprpicker'.")

    exe_path = os.path.join(SCRIPT_DIR, "tools", tools[name])
    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0, winreg.KEY_SET_VALUE
    )
    winreg.SetValueEx(key, name, 0, winreg.REG_SZ, f'"{exe_path}"')
    winreg.CloseKey(key)
    _set_enabled_registry(name, True)


def remove_hyprtool_from_startup(name):
    if name not in ('hyprsearch', 'hyprvoice', 'hyprpicker'):
        return ValueError("Invalid name. Must be 'hyprsearch', 'hyprvoice', or 'hyprpicker'.")

    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0, winreg.KEY_SET_VALUE
    )
    try:
        winreg.DeleteValue(key, name)
    except FileNotFoundError:
        pass
    finally:
        winreg.CloseKey(key)


def open_hyprtool(name):
    if name == 'hyprsearch':
        subprocess.Popen([os.path.join(SCRIPT_DIR, "tools", "HyprSearch.exe")])
    elif name == 'hyprvoice':
        subprocess.Popen([os.path.join(SCRIPT_DIR, "tools", "HyprVoice.exe")])
    elif name == 'hyprpicker':
        subprocess.Popen([os.path.join(SCRIPT_DIR, "tools", "HyprPicker.exe")])
    if name == 'asciicam':
        subprocess.Popen([os.path.join(SCRIPT_DIR, "tools", "AsciiCam.exe")])
    elif name == 'cmdgen':
        subprocess.Popen([os.path.join(SCRIPT_DIR, "tools", "CmdGen.exe")])
    elif name == 'fakeerr':
        subprocess.Popen([os.path.join(SCRIPT_DIR, "tools", "FakeError.exe")])
    elif name == 'fakeupd':
        subprocess.Popen([os.path.join(SCRIPT_DIR, "tools", "FakeUpdate.exe")])
    elif name == 'fileconv':
        subprocess.Popen([os.path.join(SCRIPT_DIR, "tools", "FileConverter.exe")])
    elif name == 'hyprclickr':
        subprocess.Popen([os.path.join(SCRIPT_DIR, "tools", "HyprClickr.exe")])
    elif name == 'hyprocr':
        subprocess.Popen([os.path.join(SCRIPT_DIR, "tools", "HyprOCR.exe")])
    elif name == 'hyprphotos':
        subprocess.Popen([os.path.join(SCRIPT_DIR, "tools", "HyprPhotos.exe")])
    elif name == 'imgtoascii':
        subprocess.Popen([os.path.join(SCRIPT_DIR, "tools", "ImageToAscii.exe")])
    elif name == 'typeghost':
        subprocess.Popen([os.path.join(SCRIPT_DIR, "tools", "TypeGhost.exe")])
    elif name == 'webapps':
        subprocess.Popen([os.path.join(SCRIPT_DIR, "tools", "WebApps.exe")])


#setup stuff for ui like consts and funcs

WELCOME_MSGS=["Utility Suite for Windows", 
             "Welcome to HyprTools!", 
             "Select a tool from the left panel to get started.", 
             "All tools are free and open-source.", 
             "ooo u reached the dark side of this lil label", 
             ":3 hi there!", 
             "the longer u dont pee the longer u pee", 
             "One stop utilities for Windows", 
             "Everything You Need!", 
             "Made for Stardance!", 
             "Python Tkinter btw :hs:", 
             "Sourcecode on Github!", 
             "Check out the tools in the left panel!", 
             "Open-source utility suite for Windows.", 
             "Small utilities for Windows.", 
             "HTML is a programming lang", 
             "Javascript best", 
             "You do NOT use Arch btw",
             "Think of this as Minecraft splashtext",
             "This is my conscience speaking",
             "I am a label, I have no feelings",
             "#FREETTKLABELS",
             "You are hypnotized, now use my software",
             "YOU SHALL PASS!",
             "You are only a mere mortal against this godly label",
             "Am i conscious??"
             "Welcome to HyprTools!", 
             "Select a tool from the left panel to get started.", 
             "All tools are free and open-source.", 
             "Welcome to HyprTools!", 
             "Select a tool from the left panel to get started.", 
             "All tools are free and open-source.", # i copied deez to make the.. uhh. unconventional messages actually rare, and like collectible like minecraft splash texts
             "Welcome to HyprTools!", 
             "Select a tool from the left panel to get started.", 
             "All tools are free and open-source.", 
             "Welcome to HyprTools!", 
             "Select a tool from the left panel to get started.", 
             "All tools are free and open-source.", 
             "Welcome to HyprTools!", 
             "Select a tool from the left panel to get started.", 
             "All tools are free and open-source.", 
             "Welcome to HyprTools!", 
             "Select a tool from the left panel to get started.", 
             "All tools are free and open-source.", ]

WELCOME_MSG = choice(WELCOME_MSGS)


# the built in tools (the ones not in a seperate exe)
def open_fix_pc_window(parent_root):
    win = tk.Toplevel(parent_root)
    win.title("Fix My PC - System Repair")
    win.geometry("560x340")
    set_app_icon(win)
    apply_theme_to_titlebar(win)

    ttk.Label(win, text="🛠️ System Repair", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=20, pady=(15, 5))
    status_lbl = ttk.Label(win, text="Doing cleanup...", font=("Segoe UI", 10))
    status_lbl.pack(anchor="w", padx=20, pady=(0, 10))

    pbar = ttk.Progressbar(win, mode="indeterminate")
    pbar.pack(fill="x", padx=20, pady=5)
    pbar.start(10)

    log_frame = ttk.LabelFrame(win, text="Output Log", padding=10)
    log_frame.pack(fill="both", expand=True, padx=20, pady=10)

    log_txt = tk.Text(log_frame, wrap="word", font=("Consolas", 9), relief="flat", highlightthickness=0)
    scroll = ttk.Scrollbar(log_frame, orient="vertical", command=log_txt.yview)
    log_txt.configure(yscrollcommand=scroll.set)
    log_txt.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")

    bg_color = "#1c1c1c" if (sv_ttk and sv_ttk.get_theme() == "dark") else "#ffffff"
    fg_color = "#ffffff" if (sv_ttk and sv_ttk.get_theme() == "dark") else "#000000"
    log_txt.configure(bg=bg_color, fg=fg_color)

    def worker():
        log_txt.insert("end", "[1/2] Running DISM /Online /Cleanup-Image /RestoreHealth...\n")
        res = fix_my_pc()
        pbar.stop()
        pbar.pack_forget()
        if res == "done":
            status_lbl.configure(text="System repair completed successfully!")
            log_txt.insert("end", "[2/2] SFC /scannow completed with no errors.\nDone!")
        else:
            status_lbl.configure(text="System repair encountered an error.")
            log_txt.insert("end", f"Result: {res}\n")
        log_txt.configure(state="disabled")

    threading.Thread(target=worker, daemon=True).start()


def open_stress_test_window(parent_root):
    win = tk.Toplevel(parent_root)
    win.title("PC Stress Test & Benchmark")
    win.geometry("580x120")
    set_app_icon(win)
    apply_theme_to_titlebar(win)

    ttk.Label(win, text="🖥️ Hardware Benchmark", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=20, pady=(15, 5))
    status_lbl = ttk.Label(win, text="Testing... Please wait.", font=("Segoe UI", 10))
    status_lbl.pack(anchor="w", padx=20, pady=(0, 0))

    pbar = ttk.Progressbar(win, mode="indeterminate")
    pbar.pack(fill="x", padx=20, pady=(15, 5))
    pbar.start(10)

    scores_frame = ttk.Frame(win, padding=15)
    scores_frame.pack(fill="both", expand=True)

    def worker():
        scores = pc_stress_test()
        pbar.stop()
        pbar.pack_forget()
        def get_avg(scores_dict):
            total = sum(float(v) for v in scores_dict.values() if isinstance(v, (int, float)))
            count = sum(1 for v in scores_dict.values() if isinstance(v, (int, float)))
            return round(total / count, 2) if count > 0 else 0.0

        
        if isinstance(scores, dict) and "error" not in scores:
            win.geometry("580x440")
            status_lbl.configure(text="Benchmark complete!")
            avg_score = get_avg(scores)
            if round(avg_score) == 10:
                OPINION = choice(["HOWWWW", "HOW MUCH MONEYY DID U SPEND", "WHAT, A PERFECT 10??", "ok, you,, are rich", "Can i have that PC", "What do u even do on this BEAST"])
            elif round(avg_score) >= 8:
                OPINION = choice(["Quite good!", "Nice PC u got there!", "The perfect middle ground", "Not bad!", "You do not need to upgrade"])
            elif round(avg_score) >= 6:
                OPINION = choice(["Bro u might need an upgrade", "You might wanna upgrade soon", "Not bad, not good", "Simple office PC?", "You can do better, just spend more"])
            elif round(avg_score) >= 4:
                OPINION = choice(["Yo I think u need an upgrade", "Only OK for MS word", "Get a new PC", "This literally 'just works'", "Graphics: Low settings only", "You need smth better"])
            elif round(avg_score) >= 2:
                OPINION = choice(["GENUINELY BAD", "What is this vro :hs:", "GET A NEW PCCC", "🥔🥔🥔 potato", "PLZ UPGRADE!", "get better pc, NOW"])
            elif round(avg_score) >= 1:
                OPINION = choice(["BRO WHAT IS THIS", "HOW OLD IS THISS", "u need linux, or a better pc", "vro, HOW DO U SURVIVE", "this is just the worst it can possibly get"])
            elif round(avg_score) == 0:
                OPINION = choice(["YOU NEEEEED SMTH BETTER", "THIS CANT RUN NOTEPAD", "HOW AM I EVEN RUNNING ON THIS", "hyprtools was NOT built for this pc", "last hope: get a new pc", "even linux cant save u"])
            else:
                OPINION = "something went wrong, try again"
            opinion_lbl = ttk.Label(scores_frame, text=OPINION, font=("Segoe UI", 16, "bold"), anchor="center")
            opinion_lbl.pack(pady=1)
            for key, val in scores.items():
                card = ttk.LabelFrame(scores_frame, text=key, padding=(15, 8))
                card.pack(fill="x", pady=4)

                score_val = float(val) if isinstance(val, (int, float)) else 0.0
                score_lbl = ttk.Label(card, text=f"{val} / 10.0", font=("Segoe UI", 12, "bold"))
                score_lbl.pack(side="left")

                prog = ttk.Progressbar(card, value=score_val * 10, maximum=100)
                prog.pack(side="right", fill="x", expand=True, padx=(15, 0))
        else:
            status_lbl.configure(text="Stress test failed or score unavailable.")
            ttk.Label(scores_frame, text=str(scores), font=("Segoe UI", 10)).pack(pady=20)

    threading.Thread(target=worker, daemon=True).start()


def open_startup_analyzer_window(parent_root):
    win = tk.Toplevel(parent_root)
    win.title("Startup App Analyzer & Recommendations")
    win.geometry("720x540")
    set_app_icon(win)
    apply_theme_to_titlebar(win)

    ttk.Label(win, text="📊 Startup App Recommendations", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=20, pady=(15, 5))
    ttk.Label(win, text="Review apps configured to run at Windows boot and disable unneeded bloatware.", font=("Segoe UI", 9)).pack(anchor="w", padx=20, pady=(0, 10))

    notebook = ttk.Notebook(win, padding=10)
    notebook.pack(fill="both", expand=True, padx=10, pady=5)

    all_items = get_all_startup_items()
    all_items = [item for item in all_items if item.get("enabled", True)]
    definite, maybe, unknown = classify_startup_items(all_items)

    def populate_tab(tab, items, category_desc):
        ttk.Label(tab, text=category_desc, font=("Segoe UI", 9, "italic")).pack(anchor="w", pady=(5, 10))

        canvas = tk.Canvas(tab, highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas, padding=5)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        cw = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(cw, width=e.width))
        canvas.configure(yscrollcommand=scrollbar.set)

        bg_color = "#1c1c1c" if (sv_ttk and sv_ttk.get_theme() == "dark") else "#fafafa"
        canvas.configure(bg=bg_color)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        if not items:
            ttk.Label(scroll_frame, text="Be happy, there is nothing here", font=("Segoe UI", 10)).pack(pady=20)
            return

        for item in items:
            card = ttk.LabelFrame(scroll_frame, padding=(12, 8))
            card.pack(fill="x", pady=4)

            left = ttk.Frame(card)
            left.pack(side="left", fill="both", expand=True)

            name_lbl = ttk.Label(left, text=item['name'], font=("Segoe UI", 10, "bold"))
            name_lbl.pack(anchor="w")
            cmd_lbl = ttk.Label(left, text=f"{item['source']} • {item['command']}", font=("Segoe UI", 8), wraplength=450)
            cmd_lbl.pack(anchor="w")

            right = ttk.Frame(card)
            right.pack(side="right", padx=(10, 0))

            state_var = tk.BooleanVar(value=item.get('enabled', True))

            def make_toggle_handler(itm, svar, btn_ref):
                def handler():
                    new_state = not svar.get()
                    svar.set(new_state)
                    if itm['type'] == 'registry':
                        _set_enabled_registry(itm['name'], new_state)
                    elif itm['type'] == 'folder':
                        src_path = itm['command']
                        if not new_state and os.path.exists(src_path):
                            dis_dir = os.path.join(os.path.dirname(src_path), DISABLED_SUBDIR)
                            os.makedirs(dis_dir, exist_ok=True)
                            try:
                                shutil.move(src_path, os.path.join(dis_dir, os.path.basename(src_path)))
                            except Exception:
                                pass
                        elif new_state and os.path.exists(src_path):
                            parent_dir = os.path.dirname(os.path.dirname(src_path))
                            try:
                                shutil.move(src_path, os.path.join(parent_dir, os.path.basename(src_path)))
                            except Exception:
                                pass
                    btn_ref.configure(text="Enable" if not new_state else "Disable")
                return handler

            tbtn = ttk.Button(right, text="Disable" if state_var.get() else "Enable")
            tbtn.configure(command=make_toggle_handler(item, state_var, tbtn))
            tbtn.pack()

    tab1 = ttk.Frame(notebook, padding=10)
    tab2 = ttk.Frame(notebook, padding=10)
    tab3 = ttk.Frame(notebook, padding=10)

    notebook.add(tab1, text=f"🚨 Not Recommended ({len(definite)})")
    notebook.add(tab2, text=f"⚠️ Optional ({len(maybe)})")
    notebook.add(tab3, text=f"❓ Other ({len(unknown)})")

    populate_tab(tab1, definite, "PLZ TURN THESE OFF:")
    populate_tab(tab2, maybe, "Optional apps you might want to turn off:")
    populate_tab(tab3, unknown, "idk about these:")


def open_update_window(parent_root):
    win = tk.Toplevel(parent_root)
    win.title("Package & Driver Updater")
    win.geometry("580x380")
    set_app_icon(win)
    apply_theme_to_titlebar(win)

    ttk.Label(win, text="📦App & Driver Update", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=20, pady=(15, 5))
    status_lbl = ttk.Label(win, text="Updating all apps... Please wait.", font=("Segoe UI", 10))
    status_lbl.pack(anchor="w", padx=20, pady=(0, 10))

    pbar = ttk.Progressbar(win, mode="indeterminate")
    pbar.pack(fill="x", padx=20, pady=5)
    pbar.start(10)

    log_frame = ttk.LabelFrame(win, text="Console Output", padding=10)
    log_frame.pack(fill="both", expand=True, padx=20, pady=10)

    log_txt = tk.Text(log_frame, wrap="word", font=("Consolas", 9), relief="flat", highlightthickness=0)
    scroll = ttk.Scrollbar(log_frame, orient="vertical", command=log_txt.yview)
    log_txt.configure(yscrollcommand=scroll.set)
    log_txt.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")

    bg_color = "#1c1c1c" if (sv_ttk and sv_ttk.get_theme() == "dark") else "#ffffff"
    fg_color = "#ffffff" if (sv_ttk and sv_ttk.get_theme() == "dark") else "#000000"
    log_txt.configure(bg=bg_color, fg=fg_color)

    def worker():
        out, err = update_all()
        pbar.stop()
        pbar.pack_forget()
        if out:
            log_txt.insert("end", out)
        if err:
            log_txt.insert("end", "\nErrors:\n" + str(err))
        status_lbl.configure(text="Upgrade process completed!")
        log_txt.configure(state="disabled")

    threading.Thread(target=worker, daemon=True).start()


def open_clear_temp_window(parent_root):
    win = tk.Toplevel(parent_root)
    win.title("Clear Temporary Files")
    win.geometry("480x240")
    set_app_icon(win)
    apply_theme_to_titlebar(win)

    ttk.Label(win, text="🧹 Clear Temp Files & Cache", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=20, pady=(15, 5))
    status_lbl = ttk.Label(win, text="Cleaning %temp% folder...", font=("Segoe UI", 10))
    status_lbl.pack(anchor="w", padx=20, pady=(0, 10))

    pbar = ttk.Progressbar(win, mode="indeterminate")
    pbar.pack(fill="x", padx=20, pady=5)
    pbar.start(10)

    res_lbl = ttk.Label(win, text="", font=("Segoe UI", 10))
    res_lbl.pack(pady=20)

    def worker():
        res = delete_temp()
        pbar.stop()
        pbar.pack_forget()
        if res == "done":
            status_lbl.configure(text="Temp files cleared successfully!")
            res_lbl.configure(text="✅ All temporary files removed from %temp%.")
        else:
            status_lbl.configure(text="Cleared temp files with locked files skipped.")
            res_lbl.configure(text=f"Note: {res}")

    threading.Thread(target=worker, daemon=True).start()


def open_organize_window(parent_root):
    win = tk.Toplevel(parent_root)
    win.title("Downloads & Folder Organizer")
    win.geometry("520x300")
    set_app_icon(win)
    apply_theme_to_titlebar(win)

    ttk.Label(win, text="📁 Downloads & Folder Organizer", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=20, pady=(15, 5))
    ttk.Label(win, text="Categorize files by filetype", font=("Segoe UI", 9), wraplength=480).pack(anchor="w", padx=20, pady=(0, 15))

    folder_frame = ttk.LabelFrame(win, text="Select Target Folder", padding=10)
    folder_frame.pack(fill="x", padx=20, pady=5)

    folder_var = tk.StringVar(value=os.path.expanduser("~/Downloads"))
    folder_ent = ttk.Entry(folder_frame, textvariable=folder_var)
    folder_ent.pack(side="left", fill="x", expand=True, padx=(0, 10))

    def browse_folder():
        p = filedialog.askdirectory()
        if p:
            folder_var.set(p)

    ttk.Button(folder_frame, text="Browse...", command=browse_folder).pack(side="right")

    status_lbl = ttk.Label(win, text="", font=("Segoe UI", 9))
    status_lbl.pack(pady=10)

    btn_frame = ttk.Frame(win)
    btn_frame.pack(pady=10)

    def do_organize():
        res = organize(folder_var.get())
        if res["success"]:
            status_lbl.configure(text=f"✅ Organized {res['count']} files into category folders.")
        else:
            status_lbl.configure(text=f"❌ Error: {res.get('error', 'Unknown error')}")

    def do_undo():
        res = undo()
        if res["success"]:
            status_lbl.configure(text=f"↩️ Restored {res['restored']} files to how they were before.")
        else:
            status_lbl.configure(text=f"❌ Error: {res.get('error', 'Unknown error')}")

    ttk.Button(btn_frame, text="Organize Folder 📁", style="Accent.TButton", command=do_organize).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="Undo Last Move ↩️", command=do_undo).pack(side="left", padx=5)

#obv splash screen

def show_splash_screen(win):
    win.withdraw()
    splash = tk.Toplevel(win)
    splash.overrideredirect(True)
    splash.attributes("-topmost", True)

    sw = splash.winfo_screenwidth()
    sh = splash.winfo_screenheight()
    w, h = 420, 240
    x = (sw - w) // 2
    y = (sh - h) // 2
    splash.geometry(f"{w}x{h}+{x}+{y}")

    container = ttk.Frame(splash, padding=25)
    container.pack(fill="both", expand=True)

    logo_frame = ttk.Frame(container)
    logo_frame.pack(pady=(10, 15))

    logo_img = get_tool_icon("hyprtools", size=(56, 56))
    if logo_img:
        lbl_img = ttk.Label(logo_frame, image=logo_img)
        lbl_img.image = logo_img#type: ignore
        lbl_img.pack(side="left", padx=(0, 15))

    title_frame = ttk.Frame(logo_frame)
    title_frame.pack(side="left")

    ttk.Label(title_frame, text="HyprTools", font=("Courier", 22, "bold")).pack(anchor="w")
    ttk.Label(title_frame, text=WELCOME_MSG, font=("Segoe UI", 9)).pack(anchor="w")

    ttk.Label(container, text="Loading...", font=("Segoe UI", 9)).pack(anchor="w", pady=(5, 8))

    pbar = ttk.Progressbar(container, mode="indeterminate", length=360)
    pbar.pack(fill="x", pady=(0, 10))
    pbar.start(12)

    set_app_icon(splash)
    apply_theme_to_titlebar(splash)
    splash.update()

    def finish_splash():
        pbar.stop()
        splash.destroy()
        win.deiconify()
        win.lift()
        win.focus_force()

    win.after(1600, finish_splash)

# the func that creates the button with toolname AND ICON YESSSSS

def create_tool_button(parent, tool_name, btn_text, style="TButton", command=None):
    try:
        icon_img = get_tool_icon(tool_name, size=(18, 18))
    except Exception:
        icon_img = None

    if command is None:
        command = lambda: open_hyprtool(tool_name)

    try:
        if icon_img:
            btn = ttk.Button(parent, text=f" {btn_text}", image=icon_img, compound="left", style=style, command=command)
            btn.image = icon_img#type: ignore
        else:
            btn = ttk.Button(parent, text=btn_text, style=style, command=command)
        return btn
    except Exception:
        try:
            return ttk.Button(parent, text=btn_text, style=style, command=command)
        except Exception:
            return None

# run above funcs one aftr another in nice style
def run_main_gui():
    win = tk.Tk()
    win.title("HyprTools Suite")
    win.geometry("1040x700")
    win.minsize(880, 580)
    try:
        set_app_icon(win)
    except Exception:
        pass

    try:
        if sv_ttk and darkdetect:
            sv_ttk.set_theme("dark" if darkdetect.isDark() else "light")
        elif sv_ttk:
            sv_ttk.set_theme("dark")
    except Exception:
        pass

    try:
        _style = ttk.Style()
        _style.configure("Sidebar.TButton", anchor="w")
        _style.configure("SidebarActive.TButton", anchor="w")
        _style.map("SidebarActive.TButton",
                   background=[("active", "#3d8bfd"), ("!disabled", "#0078d4")],
                   foreground=[("!disabled", "#ffffff")])
    except Exception:
        pass

    try:
        apply_theme_to_titlebar(win)
    except Exception:
        pass

    try:
        show_splash_screen(win)
    except Exception:
        pass
    main_container = ttk.Frame(win)
    main_container.pack(fill="both", expand=True)

    sidebar = ttk.Frame(main_container, padding=(15, 20), width=240)
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False)

    content_area = ttk.Frame(main_container, padding=(25, 20))
    content_area.pack(side="right", fill="both", expand=True)

    header_frame = ttk.Frame(sidebar)
    header_frame.pack(anchor="w", fill="x", pady=(0, 15))

    hypr_icon = get_tool_icon("hyprtools", size=(36, 36))
    if hypr_icon:
        icon_lbl = ttk.Label(header_frame, image=hypr_icon)
        icon_lbl.image = hypr_icon#type: ignore
        icon_lbl.pack(side="left", padx=(0, 10))

    title_box = ttk.Frame(header_frame)
    title_box.pack(side="left", fill="x", expand=True)
    WELCOME_MSG = choice(WELCOME_MSGS)
    ttk.Label(title_box, text="HyprTools", font=("Courier", 18, "bold")).pack(anchor="w")
    ttk.Label(title_box, text=WELCOME_MSG, font=("Segoe UI", 9 if len(WELCOME_MSG) < 50 else 6), wraplength=170).pack(anchor="w")

    ttk.Separator(sidebar, orient="horizontal").pack(fill="x", pady=(0, 15))

    sidebar_buttons = {}

    SECTIONS = [
        ("repair", "🛠️Repair & Cleanup", "Fix and clean up you PC (not physically)"),
        ("performance", "🚀   Performance", "Make ur PC go like flashhh"),
        ("tweaks", "🎨   Windows Tweaks", "Bunch of good stuff fot tweaking"),
        ("files", "📁   File Tools", "All about files, organise, convert and manage them."),
        ("productivity", "🧠   Productivity", "Make YOU go like flashhh"),
        ("extras", "🎮   Extras & Fun", "Fun stuff, Cool stuff, kinda useless stuff"),
        ("startup", "⚙️   Startup & Settings", "See which hyprtools u want as startup"),
    ]

    header_title_var = tk.StringVar(value="")
    header_desc_var = tk.StringVar(value="")

    header_title_lbl = ttk.Label(content_area, textvariable=header_title_var, font=("Segoe UI", 16, "bold"))
    header_title_lbl.pack(anchor="w")

    header_desc_lbl = ttk.Label(content_area, textvariable=header_desc_var, font=("Segoe UI", 10))
    header_desc_lbl.pack(anchor="w", pady=(2, 0))

    ttk.Separator(content_area, orient="horizontal").pack(fill="x", pady=(12, 18))

    content_body = ttk.Frame(content_area)
    content_body.pack(fill="both", expand=True)

    def create_card_row(parent, emoji, title, description, widget_builder): #make that right side specific card
        card = ttk.LabelFrame(parent, padding=(18, 14))
        card.pack(fill="x", pady=7, padx=5)

        left_frame = ttk.Frame(card)
        left_frame.pack(side="left", fill="both", expand=True)

        emoji_label = ttk.Label(left_frame, text=emoji, font=("Segoe UI Emoji", 20), width=3)
        emoji_label.pack(side="left", padx=(0, 14))

        text_frame = ttk.Frame(left_frame)
        text_frame.pack(side="left", fill="both", expand=True)

        title_label = ttk.Label(text_frame, text=title, font=("Segoe UI", 11, "bold"))
        title_label.pack(anchor="w")

        desc_label = ttk.Label(text_frame, text=description, font=("Segoe UI", 9), wraplength=450, justify="left")
        desc_label.pack(anchor="w", pady=(2, 0))

        right_frame = ttk.Frame(card)
        right_frame.pack(side="right", padx=(10, 0))

        if widget_builder:
            widget_builder(right_frame)

        return card

    def create_startup_slider(parent, tool_name, display_title): #that on off slider from scratch with scales, coz tk is dumb and idk why im still using it
        settings = load_hyprtools_settings()
        is_active = settings.get(f"startup_{tool_name}", _is_enabled_registry(tool_name))

        status_var = tk.StringVar(value="On" if is_active else "Off")

        status_lbl = ttk.Label(parent, textvariable=status_var, font=("Segoe UI", 9, "bold"), width=6, anchor="center")
        status_lbl.pack(side="left", padx=(0, 8))

        scale = ttk.Scale(parent, from_=0, to=1, value=1 if is_active else 0, length=90)
        scale.pack(side="left")

        last_val = [1 if is_active else 0]

        def on_slider_release(event):
            v = scale.get()
            active = v >= 0.5
            target = 1 if active else 0
            scale.set(target)
            status_var.set("ON" if active else "OFF")
            if last_val[0] != target:
                last_val[0] = target
                save_hyprtools_setting(f"startup_{tool_name}", active)
                if active:
                    set_hyprtool_as_startup(tool_name)
                else:
                    remove_hyprtool_from_startup(tool_name)

        scale.bind("<ButtonRelease-1>", on_slider_release)

    def load_section_view(sec_id): #this makes both left side and right side sections
        for b_id, btn in sidebar_buttons.items():
            if b_id == sec_id:
                btn.configure(style="SidebarActive.TButton")
            else:
                btn.configure(style="Sidebar.TButton")

        for child in content_body.winfo_children():
            child.destroy()

        sec_tuple = next((s for s in SECTIONS if s[0] == sec_id), None)
        if not sec_tuple:
            return

        header_title_var.set(sec_tuple[1])
        header_desc_var.set(sec_tuple[2])

        canvas = tk.Canvas(content_body, highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(content_body, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        cw = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(cw, width=e.width))
        canvas.configure(yscrollcommand=scrollbar.set)

        bg_color = "#1c1c1c" if (sv_ttk and sv_ttk.get_theme() == "dark") else "#fafafa"
        canvas.configure(bg=bg_color)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        if sec_id == "repair":
            create_card_row(
                scroll_frame, "🛠️ ", "Fix My PC",
                "Magic repair your PC, takes upto 3 hours.",
                lambda f: ttk.Button(f, text="Run Repair", command=lambda: open_fix_pc_window(win)).pack()
            )
            create_card_row(
                scroll_frame, "🧹", "Clear Temp Files & Cache",
                "Delete temp and cache files to free up disk space!",
                lambda f: ttk.Button(f, text="Clean Temp", command=lambda: open_clear_temp_window(win)).pack()
            )
            create_card_row(
                scroll_frame, "🌐", "Reset Wi-Fi & Network",
                "Just kinda refresh your Wi-Fi, in simple terms",
                lambda f: ttk.Button(f, text="Reset Wi-Fi", command=lambda: (wifi_reset(), messagebox.showinfo("Wi-Fi Reset", "Wi-Fi resetted successfully!"))).pack()
            )

        elif sec_id == "performance":
            create_card_row(
                scroll_frame, "🚀", "Update Apps & Drivers",
                "Check and update EVERYTHING via Winget.",
                lambda f: ttk.Button(f, text="Update All", command=lambda: open_update_window(win)).pack()
            )
            create_card_row(
                scroll_frame, "🖥️", "Refresh Display Drivers",
                "Restart graphics drivers, if they are not doing graphics properly.",
                lambda f: ttk.Button(f, text="Refresh Display", command=lambda: (refresh_display(), messagebox.showinfo("Display Refresh", "Graphics driver refreshed!"))).pack()
            )
            create_card_row(
                scroll_frame, "⚡", "PC Hardware Stress Test",
                "Run benchmarks to score CPU, RAM, Disk, and Graphics performance, then give my honest opinion",
                lambda f: ttk.Button(f, text="Start Test", command=lambda: open_stress_test_window(win)).pack()
            )
            create_card_row(
                scroll_frame, "📊", "Startup App Recommendations",
                "See your boot items and tell you what you need and don\'t need to run upon turning on your PC",
                lambda f: ttk.Button(f, text="Analyze Startup", command=lambda: open_startup_analyzer_window(win)).pack()
            )

        elif sec_id == "tweaks":
            create_card_row(
                scroll_frame, "⚙️", "Terminal Command Builder",
                "Use the terminal with ease, just press some buttons!",
                lambda f: create_tool_button(f, "cmdgen", "Open CmdGen").pack()#type: ignore
            )

        elif sec_id == "files":
            create_card_row(
                scroll_frame, "📁", "Downloads & Folder Organizer",
                "Fix your godforbidden mess by categorising by filetype and... yk.. organising",
                lambda f: ttk.Button(f, text="Organize Folder", command=lambda: open_organize_window(win)).pack()
            )
            create_card_row(
                scroll_frame, "🔄", "Local File Converter",
                "Convert images, audio and video files without Wi-Fi!",
                lambda f: create_tool_button(f, "fileconv", "Open FileConverter").pack()#type: ignore
            )
            create_card_row(
                scroll_frame, "🖼️", "HyprPhotos Image Editor",
                "Very very fast basic image editor!.",
                lambda f: create_tool_button(f, "hyprphotos", "Open HyprPhotos").pack()#type: ignore
            )

        elif sec_id == "productivity":
            create_card_row(
                scroll_frame, "🔍", "HyprSearch Global Search",
                "Spotlight-style search bar for basically everything! Press Alt + Q to open. [Startup app]",
                lambda f: create_startup_slider(f, "hyprsearch", "HyprSearch")
            )
            create_card_row(
                scroll_frame, "🎙️", "Voice Typing (HyprVoice)",
                "Speech-to-text, press Ctrl + Alt to use. [Startup app]",
                lambda f: create_startup_slider(f, "hyprvoice", "HyprVoice")
            )
            create_card_row(
                scroll_frame, "📄", "OCR: Image to Text (HyprOCR)",
                "\'Read\' text from images so that you can copy-paste it easily !",
                lambda f: create_tool_button(f, "hyprocr", "Launch HyprOCR").pack()#type: ignore
            )
            create_card_row(
                scroll_frame, "⌨️", "TypeGhost Auto-Typer",
                "The only auto-typer that can fool Hackatime",
                lambda f: create_tool_button(f, "typeghost", "Launch TypeGhost").pack()#type: ignore
            )
            create_card_row(
                scroll_frame, "🎨", "Colorpicker (HyprPicker)",
                "Screen color picker, activate with Alt + K [Startup app]",
                lambda f: create_startup_slider(f, "hyprpicker", "HyprPicker")
            )
            create_card_row(
                scroll_frame, "🌐", "Web Apps Manager",
                "Turn websites into desktop apps!",
                lambda f: create_tool_button(f, "webapps", "Launch WebApps").pack()#type: ignore
            )

        elif sec_id == "extras":
            create_card_row(
                scroll_frame, "🖱️", "HyprClickr Autoclicker",
                "Its an Autoclcker! Move mouse to stop.",
                lambda f: create_tool_button(f, "hyprclickr", "Launch HyprClickr").pack()#type: ignore
            )
            create_card_row(
                scroll_frame, "🔤", "Image to ASCII Art",
                "Convert images to ASCII art in PNG, HTML, or TXT format",
                lambda f: create_tool_button(f, "imgtoascii", "Launch ImageToAscii").pack()#type: ignore
            )
            create_card_row(
                scroll_frame, "📹", "Camera to ASCII (AsciiCam)",
                "Real-time webcam ASCII filter stream for OBS virtual camera (Instructions in app)",
                lambda f: create_tool_button(f, "asciicam", "Launch AsciiCam").pack()#type: ignore
            )
            create_card_row(
                scroll_frame, "🔄", "Fake Update Screen",
                "Fake Windows update screen",
                lambda f: create_tool_button(f, "fakeupd", "Launch FakeUpdate").pack()#type: ignore
            )
            create_card_row(
                scroll_frame, ":( ", "Fake Error Screen",
                "Fake Windows BSOD crash screen",
                lambda f: create_tool_button(f, "fakeerr", "Launch FakeError").pack() #type: ignore
            )

        elif sec_id == "startup":
            create_card_row(
                scroll_frame, "🔍", "HyprSearch Startup",
                "Automatically launch global HyprSearch search bar on Windows boot",
                lambda f: create_startup_slider(f, "hyprsearch", "HyprSearch")
            )
            create_card_row(
                scroll_frame, "🎨", "HyprPicker Startup",
                "Automatically launch HyprPicker color picker on Windows boot",
                lambda f: create_startup_slider(f, "hyprpicker", "HyprPicker")
            )
            create_card_row(
                scroll_frame, "🎙️", "HyprVoice Startup",
                "Automatically launch HyprVoice speech dictation on Windows boot",
                lambda f: create_startup_slider(f, "hyprvoice", "HyprVoice")
            )

    for sec_id, sec_title, _ in SECTIONS:
        btn = ttk.Button(
            sidebar, text=sec_title,
            style="Sidebar.TButton" if sec_id != "repair" else "SidebarActive.TButton",
            command=lambda s=sec_id: load_section_view(s)
        )
        btn.pack(fill="x", pady=4, ipady=3)
        sidebar_buttons[sec_id] = btn

    try:
        load_section_view("repair")
    except Exception:
        pass

    try:
        win.mainloop()
    except Exception:
        try:
            import traceback
            error_msg = traceback.format_exc()
            try:
                err_win = tk.Tk()
                err_win.withdraw()
                messagebox.showerror("HyprTools Error", error_msg)
            except Exception:
                print("HyprTools got smth wrong. error:")
                print(error_msg)
        except Exception:
            import traceback
            traceback.print_exc()

#main
if __name__ == "__main__":
    try:
        run_main_gui()
    except Exception:
        try:
            import traceback
            error_msg = traceback.format_exc()
            try:
                err_win = tk.Tk()
                err_win.withdraw()
                messagebox.showerror("HyprTools Error", error_msg)
            except Exception:
                print("HyprTools got smth wrong. error:")
                print(error_msg)
        except Exception:
            import traceback
            traceback.print_exc()
