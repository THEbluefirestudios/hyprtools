import subprocess
import ctypes
import sys
import pyautogui as mouse
from time import sleep
import re
import os
import shutil
import winreg


if not ctypes.windll.shell32.IsUserAnAdmin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
    sys.exit()



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
        return "DISM error: ", dism_err
    sfc_out, sfc_err = run_cmd('sfc /scannow')
    if sfc_err:
        return "SFC error: ", sfc_err

    return "done"

def pc_stress_test():
    def remap_score(s):
        old_min, old_max = 6.0, 9.9
        score = (s - old_min) / (old_max - old_min) * 9.0 + 1.0
        return round(max(1.0, min(10.0, score)), 1)

    run_cmd('winsat dwm')
    out, err = run_cmd('powershell -Command "Get-CimInstance Win32_WinSAT | Select-Object CPUScore, DiskScore, GraphicsScore, MemoryScore, WinSPRLevel | Format-List"')

    if err:
        return "error: " + err.strip()
    
    scores = {}
    for line in out.splitlines():
        if ':' in line:
            key, val = line.split(':', 1)
            try:
                scores[key.strip()] = remap_score(float(val.strip()))
            except ValueError:
                pass
    
    return scores if scores else {"error: Failed to retrieve scores."}

def delete_temp():
    out, err= run_cmd('del /q /f /s %temp%\\*')
    return "error: " + err.strip() if err else "done"

def update_all():
    out, err= run_cmd('winget upgrade --all --include-unknown --accept-package-agreements --accept-source-agreements')
    return "error: " + err.strip() if err else "done"


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
    r"onedrive", # u def dont want these as startup apps
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
    """Returns 'definite', 'maybe', or 'unknown' for a startup item."""
    haystack = f"{item['name']} {item['command']}"
    if _definite_re.search(haystack):
        return "definite"
    if _maybe_re.search(haystack):
        return "maybe"
    return "unknown"


def classify_startup_items(items):
    """Splits a list of startup items into three buckets."""
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


'''
Downloaded Files Categoriser code by Aarsh Garg <== my friend, edited and enhanced by Aarav Raut (THEbluefirestudios)
Categorises files into 9 categories - images, videos, documents, archives, text, programming, executables and other.
Except for other extensions, this code has a diversity of 81 extensions in total.
'''

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE_PATH = os.path.join(SCRIPT_DIR, "move_log.txt")

DIRECTORIES = {
    "Images": [".jpeg", ".jpg", ".tiff", ".tif", ".gif", ".bmp", ".png", ".bpg", ".svg", ".heif", ".heic",".psd", ".ai", ".eps", ".raw", ".cr2", ".nef", ".orf", ".sr2", ".webp", ".jfif", ".ico", ".dds",".xcf", ".indd", ".jp2", ".avif"],
    "Fonts": [".fnt", ".fon", ".otf", ".ttf", ".woff", ".woff2", ".eot", ".pfb", ".pfm"],
    "Icons": [".ico", ".icns", ".cur"],
    "Videos": [".avi", ".flv", ".wmv", ".mov", ".mp4", ".webm", ".vob", ".mng", ".qt", ".mpg", ".mpeg", ".3gp", ".3g2", ".mkv", ".m4v", ".ogv", ".rm", ".rmvb", ".ts", ".mts", ".m2ts", ".divx", ".f4v"],
    "Documents": [".oxps", ".epub", ".pages", ".docx", ".doc", ".fdf", ".ods", ".odt", ".pwn", ".pdf",".xls", ".xlsx", ".ppt", ".pptx", ".rtf", ".tex", ".md", ".odp", ".csv", ".tsv",".numbers", ".key", ".mobi", ".azw", ".azw3", ".chm", ".wpd", ".wps", ".xps"],
    "Archives": [".a", ".ar", ".cpio", ".iso", ".tar", ".gz", ".tgz", ".rz", ".7z", ".dmg", ".rar",".xar", ".zip", ".bz2", ".xz", ".lz", ".lzma", ".z", ".cab", ".arj", ".img", ".pkg"],
    "Audio": [".aac", ".aa", ".dvf", ".m4a", ".m4b", ".m4p", ".mp3", ".msv", ".ogg", ".oga", ".opus",".raw", ".vox", ".wav", ".wma", ".flac", ".alac", ".aiff", ".aif", ".mid", ".midi",".amr", ".ac3", ".dts", ".ra"],
    "Text": [".txt", ".in", ".out", ".log", ".ini", ".cfg", ".conf", ".env", ".nfo", ".readme", ".diz"],
    "Code": [".py", ".cpp", ".c", ".h", ".hpp", ".java", ".js", ".jsx", ".tsx", ".html",
                           ".htm", ".css", ".scss", ".sass", ".less", ".sh", ".swift", ".pyw", ".ipynb",
                           ".r", ".pl", ".rb", ".go", ".rs", ".ts", ".php", ".yaml", ".yml", ".json",
                           ".xml", ".sql", ".bat", ".ps1", ".vbs", ".asm", ".s", ".d", ".erl", ".hs",
                           ".lisp", ".lua", ".ml", ".nim", ".pas", ".rkt", ".scm", ".kt", ".kts",
                           ".dart", ".scala", ".clj", ".ex", ".exs", ".m", ".mm", ".vue", ".svelte",
                           ".toml", ".gradle", ".makefile", ".cmake", ".dockerfile", ".proto", ".jl"],
    "Executables": [".exe", ".msi", ".bin", ".app", ".bat", ".command", ".run", ".apk", ".appimage", ".deb", ".rpm", ".jar", ".gadget", ".wsf", ".vb", ".cgi", ".out"],
    "Ebooks": [".epub", ".mobi", ".azw", ".azw3", ".fb2", ".lit", ".pdb", ".ibooks"],
    "Models": [".stl", ".obj", ".fbx", ".dae", ".3ds", ".blend", ".dwg", ".dxf", ".step", ".stp",".iges", ".igs", ".skp", ".ply", ".gltf", ".glb"],
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