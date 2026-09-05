import os
import webbrowser as wb
import subprocess
import urllib.parse as urlparse
import wikipedia
import datetime

import warnings
from bs4 import GuessedAtParserWarning

import requests
import socket

from difflib import SequenceMatcher
from urllib.parse import urlparse

import win32com.client
import re

import json
import string
import sys #ooo giant import bloxk
import tempfile
import threading
import queue
import ctypes

import tkinter as tk
from tkinter import ttk, messagebox
import sv_ttk
import darkdetect
import pywinstyles
import pystray
from pynput import keyboard as pynput_keyboard
from PIL import Image, ImageDraw

warnings.filterwarnings("ignore", category=GuessedAtParserWarning)

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
user32.SetForegroundWindow.argtypes = [ctypes.c_void_p]
user32.BringWindowToTop.argtypes = [ctypes.c_void_p]
user32.GetForegroundWindow.restype = ctypes.c_void_p  #yea tys uses a lot of ctypes
user32.GetWindowThreadProcessId.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
user32.GetWindowThreadProcessId.restype = ctypes.c_uint32
user32.AttachThreadInput.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_int]
kernel32.GetCurrentThreadId.restype = ctypes.c_uint32


def load_start_apps(): # i was using appopener but it didnt support uwp apps and apps on other drives
    apps = {}
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", "Get-StartApps | ConvertTo-Json -Compress"],
            capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=20
        )
        data = json.loads(result.stdout)
        if isinstance(data, dict):
            data = [data]
        for entry in data:
            name = entry.get("Name")
            app_id = entry.get("AppID")
            if name and app_id and name not in apps:
                apps[name] = app_id
    except Exception:
        pass
    return apps


STARTAPPS = load_start_apps()
applist = list(STARTAPPS.keys())

BASEDIR = os.path.dirname(os.path.abspath(__file__))
HYPRTOOLS_JSON = os.path.join(BASEDIR, 'hyprtools.json')


def save_setting(key, value): #same save and load json funcs
    data = {}
    if os.path.exists(HYPRTOOLS_JSON):
        try:
            with open(HYPRTOOLS_JSON, "r") as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            data = {}

    if data.get(key) != value:
        data[key] = value
        with open(HYPRTOOLS_JSON, "w") as f:
            json.dump(data, f, indent=4)

def load_setting(key, default=None):
    if os.path.exists(HYPRTOOLS_JSON):
        try:
            with open(HYPRTOOLS_JSON, "r") as f:
                data = json.load(f)
            return data.get(key, default)
        except (json.JSONDecodeError, FileNotFoundError):
            return default
    return default

save_setting("do_engine_search", True)

#yea i use minimax m3 help here, ut only after i made the logic work

SEARCH_ENGINES = {
    
    "qwant": "https://www.qwant.com/?q=",
    "duckduckgo": "https://duckduckgo.com/?q=", # THE GOATED search engines
    "ecosia": "https://www.ecosia.org/search?q=",
    "kagi": "https://kagi.com/search?q=",

    "google": "https://www.google.com/search?q=",
    "bing": "https://www.bing.com/search?q=",
    "brave": "https://search.brave.com/search?q=",
    "startpage": "https://www.startpage.com/sp/search?query=",
    "yahoo": "https://search.yahoo.com/search?p=",  # ehh search engines
    "yandex": "https://yandex.com/search/?text=",
    "baidu": "https://www.baidu.com/s?wd=",
    "wolframalpha": "https://www.wolframalpha.com/input?i=",
}

DO_ENGINESEARCH = load_setting("do_engine_search", default=True)
bangs = [
    '!open',#opnes app or website
    '!app',#opnes app
    '!web',#opnes website
    '!searchweb',#web search by engine
    '!file',#searches for files on pc
    '!wiki',#fetches wikipedia summary
    '!time',#tells current time (USELESS)
    '!install',#winget install... u get it
    '!math',#uses eval for math, with a filter so that it only works for math expressions
    '!cmd',#run cmd command, i reccomend cmdgen for this tho
]

username = os.getenv("USERNAME") or os.getenv("USER")

TERMINAL_KEYWORDS = [ #bunch o keywords, i just brainstormed as many as i knew
    "cd", "dir", "ls", "cls", "clear", "echo", "type", "cat", "copy", "cp",
    "move", "mv", "del", "rm", "mkdir", "md", "rmdir", "rd", "ren", "rename",
    "attrib", "tree", "find", "findstr", "grep", "where", "which",
    "ping", "ipconfig", "ifconfig", "netstat", "tracert", "traceroute", "nslookup",
    "tasklist", "taskkill", "kill", "ps", "systeminfo", "whoami", "hostname",
    "python", "pip", "node", "npm", "npx", "git", "docker", "winget", "choco",
    "powershell", "cmd", "bash", "sh", "sudo", "chmod", "chown",
    "curl", "wget", "ssh", "scp", "ftp", "telnet", "winget", "choco", "apt", "yum", "dnf", "pacman", "brew",
    "set", "export", "env", "path", "exit", "start", "runas", "ffmpeg", "convert", "magick", "imagemagick", "ffprobe", "ffplay",
    "yt-dlp", "youtube-dl", "aria2c", "aria2", "rsync", "tar", "zip", "unzip", "7z", "7za", "7zr",
]

FILE_EXTENSIONS = {#ye same  here
    "txt", "doc", "docx", "pdf", "rtf", "odt", "md", "tex", "wpd", "log",
    "xlsx", "xls", "csv", "tsv", "ods", "json", "xml", "yaml", "yml", "toml",
    "pptx", "ppt", "odp", "key",
    "png", "jpg", "jpeg", "gif", "bmp", "svg", "webp", "ico", "tiff", "tif",
    "heic", "raw", "psd", "ai", "eps", "avif",
    "mp3", "wav", "flac", "aac", "ogg", "wma", "m4a", "opus", "aiff",
    "mp4", "mkv", "avi", "mov", "wmv", "flv", "webm", "m4v", "3gp", "ts",
    "zip", "rar", "7z", "tar", "gz", "bz2", "xz", "iso", "cab",
    "py", "js", "ts", "jsx", "tsx", "html", "htm", "css", "scss", "java",
    "c", "cpp", "h", "hpp", "cs", "go", "rs", "rb", "php", "swift", "kt",
    "sh", "bat", "ps1", "sql", "r", "lua", "pl", "dart", "vue", "svelte",
    "ini", "cfg", "conf", "env", "gitignore", "properties", "reg",
    "exe", "msi", "dll", "bat", "cmd", "app", "apk", "deb", "rpm", "dmg",
    "ttf", "otf", "woff", "woff2",
    "epub", "mobi", "azw3",
    "obj", "fbx", "blend", "stl", "gltf", "glb", "unity", "uasset",
    "jar", "mcpack", "mcworld", "litematic", "schematic", "nbt",
    "glsl", "vsh", "fsh", "csh", "properties",
    "torrent", "url", "lnk", "bak", "tmp",
}


save_setting("search_engine", "duckduckgo") #cmon duckduckgo GOATED

SEARCHENGINE = load_setting("search_engine", default="duckduckgo")

SEARCHDIRS = [
    f"C:\\Users\\{username}",
    f"C:\\Users\\Public\\Public Documents",
    f"C:\\Users\\Public\\Public Downloads", #IF U KEEP UR SHI IN... SYSTEM32 FOLER I WILL FIND U
    f"C:\\Users\\Public\\Public Music",
    f"C:\\Users\\Public\\Public Videos",
    f"C:\\Users\\Public\\Public Pictures",
]


for letter in string.ascii_uppercase:
    if letter == "C":
        continue
    drive = f"{letter}:\\" #extra driveletters in case if any
    if os.path.exists(drive):
        SEARCHDIRS.append(drive)


def save_search_dirs(search_dirs): 
    data = {}
    if os.path.exists(HYPRTOOLS_JSON):
        try:
            with open(HYPRTOOLS_JSON, "r") as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            data = {}

    existing = data.get("search_dirs")
    if existing != search_dirs:
        data["search_dirs"] = search_dirs
        with open(HYPRTOOLS_JSON, "w") as f:
            json.dump(data, f, indent=4)

save_search_dirs(SEARCHDIRS)

def is_terminal_command(text):
    if not text or not text.strip():
        return False
    first_word = text.strip().split()[0].lower()
    return first_word in TERMINAL_KEYWORDS

MATH_CHARS = set("0123456789+-*/^%().")# see i told u i did some filtering for the math expression

def is_math_expression(text):
    if not text or not text.strip():
        return False
    text = text.strip()
    if re.search(r"[a-zA-Z]", text):
        return False
    if not re.search(r"\d", text):
        return False
    return all(c in MATH_CHARS or c.isspace() for c in text)

def looks_like_filename(text):
    text = text.strip()
    match = re.search(r"\.(\w+)$", text)
    return match is not None and match.group(1).lower() in FILE_EXTENSIONS

wikipedia.set_user_agent("hyprsearch/1.0 (https://github.com/THEbluefirestudios/hyprtools/issues)")#real header

def starts_with(string1, string2):
    return string2.lower().startswith(string1.lower())

def find_best_app_match(query, threshold=0.72): #fuzzymatching app anmes, so like whutsipp will return whatsapp
    if not STARTAPPS or not query:
        return None
    query_l = query.lower().strip()
    if not query_l:
        return None
    best_name = None
    best_ratio = 0.0
    for name in STARTAPPS:
        name_l = name.lower()
        if query_l == name_l:
            return name
        ratio = SequenceMatcher(None, query_l, name_l).ratio()
        if name_l.startswith(query_l):
            ratio = max(ratio, 0.9)
        if ratio > best_ratio:
            best_ratio = ratio
            best_name = name
    if best_ratio >= threshold:
        return best_name
    return None

def math_solve(expression):
    try:
        result = eval(expression)
        return result
    except Exception as e:
        return f"{str(e)}"

def resolve_website(user_input, timeout=3): #my magnum opus, uses im feeling lucky to get website
    query = user_input.strip()
    try:
        r = requests.get(
            "https://www.google.com/search",
            params={"q": f"{query} website", "btnI": "1"},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=timeout,
            allow_redirects=True,
        )
        if r.url and "google.com/search" not in r.url:
            return r.url
    except requests.RequestException:
        pass
    candidate = query if "." in query else f"{query.lower().replace(' ', '')}.com"
    try:
        socket.setdefaulttimeout(1.5)
        socket.gethostbyname(candidate)
        return f"https://{candidate}"
    except socket.error:
        return None


def resolve_website_confident(user_input, timeout=3):
    query = user_input.strip()
    try:
        r = requests.get(
            "https://www.google.com/search",
            params={"q": f"{query} website", "btnI": "1"},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=timeout,
            allow_redirects=True,
        )
        if r.url and "google.com/search" not in r.url:
            return r.url
    except requests.RequestException:
        pass
    return None


def run_cmd(command):
    try:
        subprocess.run(command, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
    except Exception as e:
        return f"{str(e)}"

def current_time():
    now = datetime.datetime.now()
    return now.strftime("%H:%M:%S")

def open_app(app_name):
    app_id = STARTAPPS.get(app_name)
    if not app_id:
        match = find_best_app_match(app_name)
        if match:
            app_id = STARTAPPS.get(match)
    if not app_id:
        return f"Could not find app '{app_name}'"
    try:
        subprocess.run(["explorer.exe", f"shell:appsFolder\\{app_id}"], creationflags=subprocess.CREATE_NO_WINDOW)
    except Exception as e:
        return f"{str(e)}"

def open_website(user_input):
    url = resolve_website(user_input)
    if url is None:
        return f"Could not resolve '{user_input}' to a website"
    try:
        wb.open(url)
    except Exception as e:
        return f"{str(e)}"


def search_wikipedia(query):
    try:
        summary = wikipedia.summary(query, sentences=2)
        return summary
    except wikipedia.exceptions.DisambiguationError as e:
        top_5 = e.options[:5]
        summary = "Ambigious topic, do you mean?: \n"
        for option in top_5:
            try:
                summary += '\n\n' + wikipedia.summary(option, sentences=2)
            except (wikipedia.exceptions.PageError, wikipedia.exceptions.DisambiguationError):
                pass
        return summary
    except wikipedia.exceptions.PageError:
        return "No Wikipedia page found for that query."
    except Exception as e:
        return f"Error: {str(e)}"


def search_on_engine(query, engine="duckduckgo"):
    if engine not in SEARCH_ENGINES:
        searchengine = "duckduckgo"
    else:
        searchengine = engine
    search_url = SEARCH_ENGINES[searchengine] + urlparse.quote_plus(query)
    try:
        wb.open(search_url)
    except Exception as e:
        pass

def winget_install(package_name):
    try:
        subprocess.run(
            ["winget", "install", package_name, "--accept-package-agreements", "--accept-source-agreements", "--silent", "--disable-interactivity"],
            capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
        )
    except Exception as e:
        return f"{str(e)}"


def file_search(file_name, search_path=None):
    matches = []
    try:
        conn = win32com.client.Dispatch("ADODB.Connection")
        conn.Open("Provider=Search.CollatorDSO;Extended Properties='Application=Windows'")
        rs = win32com.client.Dispatch("ADODB.Recordset")

        safe_name = file_name.replace("'", "''")
        query = f"""
            SELECT System.ItemPathDisplay
            FROM SYSTEMINDEX
            WHERE System.FileName LIKE '%{safe_name}%'
        """
        if search_path:
            safe_path = search_path.replace("'", "''").rstrip("\\")
            query += f" AND SCOPE='file:{safe_path}'"

        rs.Open(query, conn)
        while not rs.EOF:
            matches.append(rs.Fields.Item("System.ItemPathDisplay").Value)
            rs.MoveNext()
        rs.Close()
        conn.Close()
    except Exception:
        pass

    if not matches and search_path:
        name_lower = file_name.lower()
        for root, _, files in os.walk(search_path):
            for f in files:
                if name_lower in f.lower():
                    matches.append(os.path.join(root, f))

    return matches


def file_search_diverse(file_name, max_results=5):
    seen_dirs = set()
    results = []
    for search_dir in SEARCHDIRS:
        matches = file_search(file_name, search_path=search_dir)
        for m in matches:
            parent = os.path.dirname(m)
            if parent in seen_dirs:
                continue
            seen_dirs.add(parent)
            results.append(m)
            if len(results) >= max_results:
                return results
    return results


FILE_ICON_MAP = {
    "txt": "\U0001F4C4", "doc": "\U0001F4C4", "docx": "\U0001F4C4", "rtf": "\U0001F4C4",
    "odt": "\U0001F4C4", "md": "\U0001F4C4", "tex": "\U0001F4C4", "wpd": "\U0001F4C4",
    "log": "\U0001F4C4", "pdf": "\U0001F4D5",
    "json": "\U0001F4C4", "xml": "\U0001F4C4", "yaml": "\U0001F4C4", "yml": "\U0001F4C4",
    "toml": "\U0001F4C4", "ini": "\U0001F4C4", "cfg": "\U0001F4C4", "conf": "\U0001F4C4",
    "env": "\U0001F4C4", "gitignore": "\U0001F4C4", "properties": "\U0001F4C4", "reg": "\U0001F4C4",
    "xlsx": "\U0001F4CA", "xls": "\U0001F4CA", "csv": "\U0001F4CA", "tsv": "\U0001F4CA", "ods": "\U0001F4CA",
    "pptx": "\U0001F4FD\uFE0F", "ppt": "\U0001F4FD\uFE0F", "odp": "\U0001F4FD\uFE0F", "key": "\U0001F4FD\uFE0F",
    "png": "\U0001F5BC\uFE0F", "jpg": "\U0001F5BC\uFE0F", "jpeg": "\U0001F5BC\uFE0F", "gif": "\U0001F5BC\uFE0F",
    "bmp": "\U0001F5BC\uFE0F", "svg": "\U0001F5BC\uFE0F", "webp": "\U0001F5BC\uFE0F", "ico": "\U0001F5BC\uFE0F",
    "tiff": "\U0001F5BC\uFE0F", "tif": "\U0001F5BC\uFE0F", "heic": "\U0001F5BC\uFE0F", "raw": "\U0001F5BC\uFE0F",
    "psd": "\U0001F5BC\uFE0F", "ai": "\U0001F5BC\uFE0F", "eps": "\U0001F5BC\uFE0F", "avif": "\U0001F5BC\uFE0F",
    "mp3": "\U0001F3B5", "wav": "\U0001F3B5", "flac": "\U0001F3B5", "aac": "\U0001F3B5",
    "ogg": "\U0001F3B5", "wma": "\U0001F3B5", "m4a": "\U0001F3B5", "opus": "\U0001F3B5", "aiff": "\U0001F3B5",
    "mp4": "\U0001F3AC", "mkv": "\U0001F3AC", "avi": "\U0001F3AC", "mov": "\U0001F3AC",
    "wmv": "\U0001F3AC", "flv": "\U0001F3AC", "webm": "\U0001F3AC", "m4v": "\U0001F3AC",
    "3gp": "\U0001F3AC", "ts": "\U0001F3AC",
    "zip": "\U0001F5DC\uFE0F", "rar": "\U0001F5DC\uFE0F", "7z": "\U0001F5DC\uFE0F", "tar": "\U0001F5DC\uFE0F",
    "gz": "\U0001F5DC\uFE0F", "bz2": "\U0001F5DC\uFE0F", "xz": "\U0001F5DC\uFE0F", "iso": "\U0001F5DC\uFE0F", "cab": "\U0001F5DC\uFE0F",
    "py": "\U0001F4BB", "js": "\U0001F4BB", "jsx": "\U0001F4BB", "tsx": "\U0001F4BB",
    "html": "\U0001F4BB", "htm": "\U0001F4BB", "css": "\U0001F4BB", "scss": "\U0001F4BB", "java": "\U0001F4BB",
    "c": "\U0001F4BB", "cpp": "\U0001F4BB", "h": "\U0001F4BB", "hpp": "\U0001F4BB", "cs": "\U0001F4BB",
    "go": "\U0001F4BB", "rs": "\U0001F4BB", "rb": "\U0001F4BB", "php": "\U0001F4BB", "swift": "\U0001F4BB",
    "kt": "\U0001F4BB", "sh": "\U0001F4BB", "ps1": "\U0001F4BB", "sql": "\U0001F4BB", "r": "\U0001F4BB",
    "lua": "\U0001F4BB", "pl": "\U0001F4BB", "dart": "\U0001F4BB", "vue": "\U0001F4BB", "svelte": "\U0001F4BB",
    "glsl": "\U0001F4BB", "vsh": "\U0001F4BB", "fsh": "\U0001F4BB", "csh": "\U0001F4BB",
    "exe": "\U0001F4E6", "msi": "\U0001F4E6", "dll": "\U0001F4E6", "app": "\U0001F4E6",
    "apk": "\U0001F4E6", "deb": "\U0001F4E6", "rpm": "\U0001F4E6", "dmg": "\U0001F4E6",
    "bat": "\U0001F4E6", "cmd": "\U0001F4E6",
    "ttf": "\U0001F520", "otf": "\U0001F520", "woff": "\U0001F520", "woff2": "\U0001F520",
    "epub": "\U0001F4DA", "mobi": "\U0001F4DA", "azw3": "\U0001F4DA",
    "obj": "\U0001F9CA", "fbx": "\U0001F9CA", "blend": "\U0001F9CA", "stl": "\U0001F9CA",
    "gltf": "\U0001F9CA", "glb": "\U0001F9CA", "unity": "\U0001F9CA", "uasset": "\U0001F9CA",
    "jar": "\u26CF\uFE0F", "mcpack": "\u26CF\uFE0F", "mcworld": "\u26CF\uFE0F",
    "litematic": "\u26CF\uFE0F", "schematic": "\u26CF\uFE0F", "nbt": "\u26CF\uFE0F",
    "torrent": "\U0001F4CE", "url": "\U0001F4CE", "lnk": "\U0001F4CE", "bak": "\U0001F4CE", "tmp": "\U0001F4CE",
}

DEFAULT_FILE_ICON = "\U0001F4C4"

def get_file_icon(path):
    ext = os.path.splitext(path)[1].lstrip(".").lower()
    return FILE_ICON_MAP.get(ext, DEFAULT_FILE_ICON)


def reveal_in_explorer(file_path):
    subprocess.run(f'explorer /select,"{file_path}"')


def search(query):
    matched_bang = None
    for bang in bangs:
        if starts_with(bang, query):
            matched_bang = bang
            break

    if matched_bang:
        query = query.removeprefix(matched_bang).strip()
        if not query:
            return f"Please provide a query after the bang '{matched_bang}'"

        while query.startswith(" "):
            query = query[1:]
        if matched_bang == '!open':
            app_match = find_best_app_match(query)
            if app_match:
                return open_app(app_match)
            else:
                if resolve_website(query):
                    return open_website(query)
                else:
                    return f"Could not find an app or website for '{query}'"
        elif matched_bang == '!app':
            app_match = find_best_app_match(query)
            if app_match:
                return open_app(app_match)
            else:
                return f"Could not find an app for '{query}'"
        elif matched_bang == '!web':
            if resolve_website(query):
                return open_website(query)
            else:
                return f"Could not find a website for '{query}'"
        elif matched_bang == '!searchweb':
            search_on_engine(query, engine=SEARCHENGINE)
        elif matched_bang == '!install':
            return winget_install(query)
        elif matched_bang == '!math':
            if is_math_expression(query):
                return math_solve(query)
            else:
                return f"'{query}' is not a valid math expression."
        elif matched_bang == '!cmd':
            if is_terminal_command(query):
                return run_cmd(query)
            else:
                return f"'{query}' is not a recognized terminal command."
        elif matched_bang == '!time':
            return current_time()
        elif matched_bang == '!wiki':
            return search_wikipedia(query)
        elif matched_bang == '!file':
            matches = file_search_diverse(query)
            if matches:
                return matches
            else:
                return f"No files found for '{query}' in the specified directories."
        else:
            pass

    if is_math_expression(query):
        return math_solve(query)
    elif is_terminal_command(query):
        return run_cmd(query)
    elif find_best_app_match(query):
        return open_app(find_best_app_match(query))
    elif " " not in query.strip() and resolve_website(query):
        return open_website(query)
    elif looks_like_filename(query):
        matches = file_search_diverse(query)
        if matches:
            return matches
        else:
            if DO_ENGINESEARCH:
                search_on_engine(query, engine=SEARCHENGINE)
            else:
                wiki_result = search_wikipedia(query)
                if "No Wikipedia page found" not in wiki_result:
                    return wiki_result
    else:
        if DO_ENGINESEARCH:
            search_on_engine(query, engine=SEARCHENGINE)
        else:
            wiki_result = search_wikipedia(query)
            if "No Wikipedia page found" not in wiki_result:
                return wiki_result


def gather_bang_candidate(matched_bang, query):
    q = query.removeprefix(matched_bang).strip()
    while q.startswith(" "):
        q = q[1:]
    if not q:
        return [{"title": f"Provide a query after '{matched_bang}'", "subtitle": "", "kind": "error", "payload": None}]
    if matched_bang == '!open':
        app_match = find_best_app_match(q)
        if app_match:
            return [{"title": f"Open {app_match}", "subtitle": "Application", "kind": "app", "payload": app_match}]
        url = resolve_website(q)
        if url:
            return [{"title": "Open website", "subtitle": url, "kind": "website", "payload": url}]
        return [{"title": "Could not find an app or website", "subtitle": q, "kind": "error", "payload": None}]
    elif matched_bang == '!app':
        app_match = find_best_app_match(q)
        if app_match:
            return [{"title": f"Open {app_match}", "subtitle": "Application", "kind": "app", "payload": app_match}]
        return [{"title": "Could not find an app", "subtitle": q, "kind": "error", "payload": None}]
    elif matched_bang == '!web':
        url = resolve_website(q)
        if url:
            return [{"title": "Open website", "subtitle": url, "kind": "website", "payload": url}]
        return [{"title": "Could not find a website", "subtitle": q, "kind": "error", "payload": None}]
    elif matched_bang == '!searchweb':
        return [{"title": f"Search the web in {SEARCHENGINE.title()}", "subtitle": f'Search for "{q}"', "kind": "searchweb", "payload": q}]
    elif matched_bang == '!install':
        return [{"title": "Install via winget", "subtitle": q, "kind": "install", "payload": q}]
    elif matched_bang == '!math':
        if is_math_expression(q):
            return [{"title": str(math_solve(q)), "subtitle": q, "kind": "math", "payload": q}]
        return [{"title": f"'{q}' is not a valid math expression", "subtitle": "", "kind": "error", "payload": None}]
    elif matched_bang == '!cmd':
        if is_terminal_command(q):
            return [{"title": "Run command", "subtitle": q, "kind": "cmd", "payload": q}]
        return [{"title": f"'{q}' is not a recognized terminal command", "subtitle": "", "kind": "error", "payload": None}]
    elif matched_bang == '!time':
        return [{"title": current_time(), "subtitle": "Current time", "kind": "time", "payload": None}]
    elif matched_bang == '!wiki':
        return [{"title": "Wikipedia summary", "subtitle": q, "kind": "wiki", "payload": q}]
    elif matched_bang == '!file':
        return [{"title": f'Search for "{q}" in files', "subtitle": "Files on this PC", "kind": "file", "payload": q}]
    return []


def gather_candidates(query):
    query = query.strip()
    if not query:
        return []

    matched_bang = None
    for bang in bangs:
        if starts_with(bang, query):
            matched_bang = bang
            break
    if matched_bang:
        return gather_bang_candidate(matched_bang, query)

    candidates = []
    if is_math_expression(query):
        candidates.append({"title": str(math_solve(query)), "subtitle": query, "kind": "math", "payload": query})
    if is_terminal_command(query):
        candidates.append({"title": "Run command", "subtitle": query, "kind": "cmd", "payload": query})
    app_match = find_best_app_match(query)
    if app_match:
        candidates.append({"title": f"Open {app_match}", "subtitle": "Application", "kind": "app", "payload": app_match})

    candidates.append({"title": f'Search for "{query}" in files', "subtitle": "Files on this PC", "kind": "file", "payload": query})

    site_url = None
    if " " not in query.strip():
        site_url = resolve_website_confident(query)
    if site_url:
        candidates.append({"title": "Open website", "subtitle": site_url, "kind": "website", "payload": site_url})

    if DO_ENGINESEARCH:
        candidates.append({"title": f"Search the web in {SEARCHENGINE.title()}", "subtitle": f'Search for "{query}"', "kind": "searchweb", "payload": query})
    else:
        candidates.append({"title": "Wikipedia summary", "subtitle": query, "kind": "wiki", "payload": query})
    return candidates


def stream_process(command_args, shell, output_queue):
    try:
        proc = subprocess.Popen(
            command_args,
            shell=shell,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        for line in proc.stdout: #type: ignore
            output_queue.put(line.rstrip("\n"))
        proc.wait()
        output_queue.put(None)
    except Exception as e:
        output_queue.put(f"{str(e)}")
        output_queue.put(None)


def apply_theme_to_titlebar(root):
    try:
        version = sys.getwindowsversion()
        if version.major == 10 and version.build >= 22000:
            pywinstyles.change_header_color(root, "#1c1c1c" if sv_ttk.get_theme() == "dark" else "#fafafa")
        elif version.major == 10:
            pywinstyles.apply_style(root, "dark" if sv_ttk.get_theme() == "dark" else "normal")
            root.wm_attributes("-alpha", 0.99)
            root.wm_attributes("-alpha", 1)
    except Exception:
        pass

#gui consts
RESULT_WIDTH = 760
CORNER_RADIUS = 18
TRANSPARENT_KEY = "#ff00fe"
HOTKEY = "<alt>+q"

ICON_MAP = {
    "app": "\U0001F4E6",
    "website": "\U0001F310",
    "searchweb": "\U0001F310",
    "wiki": "\U0001F4D6",
    "file": "\U0001F4C2",
    "file_open": "\U0001F4C4",
    "install": "\u2B07\uFE0F",
    "math": "\U0001F522",
    "cmd": "\U0001F5A5\uFE0F",
    "time": "\U0001F550",
    "error": "\u26A0\uFE0F",
    "info": "\U0001F4C2",
}

#oohh java class reference
class HyprSearchApp:
    def __init__(self):
        self.root = tk.Tk()
        try:
            base = sys._MEIPASS#type: ignore
        except AttributeError:
            base = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base, "hyprsearch.png")
        self.root.iconphoto(True, tk.PhotoImage(file=icon_path))
        self.root.withdraw()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        sv_ttk.set_theme("dark" if darkdetect.isDark() else "light")

        self.suggestion_job = None
        self.icon = None
        self.hotkey_listener = None
        self.visible = False
        self.current_candidates = []
        self.panel_color = "#1c1c1c" if sv_ttk.get_theme() == "dark" else "#fafafa"

        self.build_ui()
        apply_theme_to_titlebar(self.root)

        self.root.bind("<Escape>", lambda e: self.hide_window())
        self.root.bind("<FocusOut>", self._on_focus_out)
        self.entry.bind("<KeyRelease>", self.on_key_release)
        self.entry.bind("<Return>", self.on_search)
        for i in range(1, 10):
            self.root.bind_all(f"<Control-Key-{i}>", lambda e, idx=i - 1: self._select_index(idx))

        self.setup_tray()
        self.setup_hotkey()
        self.root.mainloop()

    def build_ui(self):
        self.root.configure(bg=TRANSPARENT_KEY)
        self.rounded = sys.platform == "win32"
        if self.rounded:
            try:
                self.root.wm_attributes("-transparentcolor", TRANSPARENT_KEY)
            except tk.TclError:
                self.rounded = False

        self.bg_canvas = tk.Canvas(self.root, bg=TRANSPARENT_KEY, highlightthickness=0, bd=0)
        self.bg_canvas.pack(fill="both", expand=True)

        container = ttk.Frame(self.bg_canvas, padding=0)
        self.content_window = self.bg_canvas.create_window(0, 0, anchor="nw", window=container)

        search_row = ttk.Frame(container)
        search_row.pack(fill="x")

        self.query_var = tk.StringVar()
        self.entry = ttk.Entry(search_row, textvariable=self.query_var, font=("Segoe UI", 14))
        self.entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 8))

        search_btn_frame = ttk.Frame(search_row, width=44, height=44)
        search_btn_frame.pack(side="left", padx=(0, 6))
        search_btn_frame.pack_propagate(False)
        self.search_btn = ttk.Button(search_btn_frame, text="\U0001F50D", style="Accent.TButton", command=self.on_search)
        self.search_btn.pack(fill="both", expand=True)

        settings_btn_frame = ttk.Frame(search_row, width=44, height=44)
        settings_btn_frame.pack(side="left")
        settings_btn_frame.pack_propagate(False)
        self.settings_btn = ttk.Button(settings_btn_frame, text="\u2699", command=self.open_settings)
        self.settings_btn.pack(fill="both", expand=True)

        self._style_result_row()

        self.results_container = ttk.Frame(container)

        self.output_frame = ttk.Frame(container)
        self.output_text = tk.Text(self.output_frame, height=3, wrap="word", relief="flat", bd=0)
        output_scroll = ttk.Scrollbar(self.output_frame, orient="vertical", command=self.output_text.yview)
        self.output_text.configure(yscrollcommand=output_scroll.set, state="disabled")
        self.output_text.pack(side="left", fill="both", expand=True)
        output_scroll.pack(side="right", fill="y")
        self._style_output()

        self.container = container

    def _style_result_row(self):
        style = ttk.Style()
        is_dark = sv_ttk.get_theme() == "dark"
        bg = self.panel_color
        fg = "#ffffff" if is_dark else "#1a1a1a"
        sub_fg = "#a0a0a0" if is_dark else "#5a5a5a"
        style.configure("Result.TFrame", background=bg)
        style.configure("ResultTitle.TLabel", background=bg, foreground=fg, font=("Segoe UI", 15, "bold"))
        style.configure("ResultTitleAlt.TLabel", background=bg, foreground=fg, font=("Segoe UI", 12))
        style.configure("ResultSub.TLabel", background=bg, foreground=sub_fg, font=("Segoe UI", 10))
        style.configure("ResultNum.TLabel", background=bg, foreground=sub_fg, font=("Segoe UI", 9))
        style.configure("ResultIcon.TLabel", background=bg, font=("Segoe UI Emoji", 20))
        style.configure("ResultIconAlt.TLabel", background=bg, font=("Segoe UI Emoji", 15))

    def _style_output(self):
        is_dark = sv_ttk.get_theme() == "dark"
        bg = self.panel_color
        fg = "#e6e6e6" if is_dark else "#1a1a1a"
        self.output_text.configure(bg=bg, fg=fg, insertbackground=fg, font=("Consolas", 10))

    def _round_rect_points(self, x1, y1, x2, y2, r):
        return [
            x1 + r, y1,
            x2 - r, y1,
            x2, y1,
            x2, y1 + r,
            x2, y2 - r,
            x2, y2,
            x2 - r, y2,
            x1 + r, y2,
            x1, y2,
            x1, y2 - r,
            x1, y1 + r,
            x1, y1,
        ]

    def _draw_panel(self, w, h):
        self.bg_canvas.config(width=w, height=h)
        self.bg_canvas.delete("panel")
        if self.rounded:
            points = self._round_rect_points(1, 1, w - 1, h - 1, CORNER_RADIUS)
            self.bg_canvas.create_polygon(points, smooth=True, fill=self.panel_color, outline=self.panel_color, tags="panel")
            self.bg_canvas.tag_lower("panel")
            inset = CORNER_RADIUS
        else:
            self.bg_canvas.create_rectangle(0, 0, w, h, fill=self.panel_color, outline=self.panel_color, tags="panel")
            self.bg_canvas.tag_lower("panel")
            inset = 1
        self.bg_canvas.coords(self.content_window, inset, inset)
        self.bg_canvas.itemconfig(self.content_window, width=w - 2 * inset, height=h - 2 * inset)

    def resize_to(self, height):
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - RESULT_WIDTH) // 2
        y = sh // 6
        self.root.geometry(f"{RESULT_WIDTH}x{height}+{x}+{y}")
        self._draw_panel(RESULT_WIDTH, height)

    def _sync_size(self):
        self.root.update_idletasks()
        self.container.update_idletasks()
        has_results = self.results_container.winfo_ismapped() or self.output_frame.winfo_ismapped()
        padding = 50 if has_results else 30
        h = self.container.winfo_reqheight() + padding
        self.resize_to(h)

        self.root.update_idletasks()
        has_results2 = self.results_container.winfo_ismapped() or self.output_frame.winfo_ismapped()
        padding2 = 50 if has_results2 else 30
        h2 = self.container.winfo_reqheight() + padding2
        if abs(h2 - h) > 1:
            self.resize_to(h2)

    def _cancel_suggestion_job(self):
        if self.suggestion_job:
            try:
                self.root.after_cancel(self.suggestion_job)
            except Exception:
                pass
            self.suggestion_job = None

    def show_window(self):
        self._cancel_suggestion_job()
        self.query_var.set("")
        self.current_candidates = []
        self.results_container.pack_forget()
        self.output_frame.pack_forget()
        for child in self.results_container.winfo_children():
            child.destroy()
        self._sync_size()
        self.root.deiconify()
        self.root.attributes("-topmost", True)
        self._force_entry_focus()
        self.visible = True

    def _force_entry_focus(self):
        self.root.lift()
        hwnd = self.root.winfo_id()
        try:
            fg_hwnd = user32.GetForegroundWindow()
            fg_thread = user32.GetWindowThreadProcessId(fg_hwnd, None)
            cur_thread = kernel32.GetCurrentThreadId()
            if fg_thread and fg_thread != cur_thread:
                user32.AttachThreadInput(fg_thread, cur_thread, True)
                user32.BringWindowToTop(hwnd)
                user32.SetForegroundWindow(hwnd)
                user32.AttachThreadInput(fg_thread, cur_thread, False)
            else:
                user32.BringWindowToTop(hwnd)
                user32.SetForegroundWindow(hwnd)
        except Exception:
            pass
        self.root.focus_force()
        self.entry.focus_set()
        self.root.after(50, self._reassert_entry_focus)
        self.root.after(150, self._reassert_entry_focus)
        self.root.after(300, self._reassert_entry_focus)

    def _reassert_entry_focus(self):
        if self.visible:
            self.entry.focus_force()

    def hide_window(self):
        self._cancel_suggestion_job()
        self.root.withdraw()
        self.visible = False

    def toggle_window(self):
        if self.visible:
            self.hide_window()
        else:
            self.show_window()

    def _on_focus_out(self, event):
        if event.widget != self.root:
            return
        self.root.after(1, self._check_focus_lost)

    def _check_focus_lost(self):
        if self.visible and self.root.focus_get() is None:
            self.hide_window()

    def on_key_release(self, event):
        if event.keysym in ("Return", "Escape"):
            return
        if event.state & 0x0004:
            return
        self._cancel_suggestion_job()
        self.suggestion_job = self.root.after(350, self.update_suggestion)

    def update_suggestion(self):
        self.suggestion_job = None
        query = self.query_var.get()
        if not query.strip():
            self.current_candidates = []
            self.results_container.pack_forget()
            self.output_frame.pack_forget()
            for child in self.results_container.winfo_children():
                child.destroy()
            self._sync_size()
            return
        threading.Thread(target=self._compute_candidates, args=(query,), daemon=True).start()

    def _compute_candidates(self, query):
        try:
            candidates = gather_candidates(query)
        except Exception as e:
            candidates = [{"title": str(e), "subtitle": "", "kind": "error", "payload": None}]
        self.root.after(0, lambda: self._show_candidates(query, candidates))

    def _show_candidates(self, query, candidates):
        if self.query_var.get() != query:
            return
        self.output_frame.pack_forget()
        for child in self.results_container.winfo_children():
            child.destroy()
        self.current_candidates = candidates
        if not candidates:
            self.results_container.pack_forget()
            self._sync_size()
            return
        for i, c in enumerate(candidates[:6]):
            row = self._build_result_row(i, c)
            row.pack(fill="x", pady=(0 if i == 0 else 3, 0))
        if not self.results_container.winfo_ismapped():
            self.results_container.pack(fill="x", pady=(10, 0))
        self._sync_size()

    def _build_result_row(self, index, candidate):
        row = ttk.Frame(self.results_container, style="Result.TFrame")
        accent_color = "#3d8bfd" if index == 0 else self.panel_color
        accent = tk.Frame(row, width=4, bg=accent_color)
        accent.pack(side="left", fill="y")

        icon_style = "ResultIcon.TLabel" if index == 0 else "ResultIconAlt.TLabel"
        icon_text = candidate.get("icon") or ICON_MAP.get(candidate.get("kind"), "\U0001F50D")
        icon_frame = ttk.Frame(row, style="Result.TFrame", width=48 if index == 0 else 40)
        icon_frame.pack(side="left", fill="y")
        icon_frame.pack_propagate(False)
        icon_lbl = ttk.Label(icon_frame, text=icon_text, style=icon_style, anchor="center")
        icon_lbl.pack(fill="both", expand=True)

        text_frame = ttk.Frame(row, style="Result.TFrame")
        text_frame.pack(side="left", fill="both", expand=True, padx=(4, 8), pady=(12 if index == 0 else 8))
        title_style = "ResultTitle.TLabel" if index == 0 else "ResultTitleAlt.TLabel"
        ttk.Label(text_frame, text=candidate["title"], style=title_style, wraplength=RESULT_WIDTH - 220).pack(anchor="w")
        if candidate["subtitle"]:
            ttk.Label(text_frame, text=candidate["subtitle"], style="ResultSub.TLabel", wraplength=RESULT_WIDTH - 220).pack(anchor="w", pady=(2, 0))
        num = ttk.Label(row, text=f"Ctrl + {str(index + 1)}", style="ResultNum.TLabel")
        num.pack(side="right", padx=(0, 14))
        clickables = [row, accent, icon_frame, icon_lbl, text_frame, num] + list(text_frame.winfo_children())
        for widget in clickables:
            widget.bind("<Button-1>", lambda e, c=candidate: self.select_candidate(c))
        return row

    def _select_index(self, idx):
        if not self.visible:
            return
        if 0 <= idx < len(self.current_candidates):
            self.select_candidate(self.current_candidates[idx])

    def on_search(self, event=None):
        self._cancel_suggestion_job()
        if self.current_candidates:
            self.select_candidate(self.current_candidates[0])

    def select_candidate(self, candidate):
        self._cancel_suggestion_job()
        kind = candidate.get("kind")
        payload = candidate.get("payload")
        try:
            if kind == "app":
                err = open_app(payload)
                if err:
                    messagebox.showerror("HyprSearch", err)
                    return
                self.hide_window()
            elif kind == "website":
                wb.open(payload)
                self.hide_window()
            elif kind == "searchweb":
                search_on_engine(payload, engine=SEARCHENGINE)
                self.hide_window()
            elif kind in ("math", "time"):
                self.root.clipboard_clear()
                self.root.clipboard_append(candidate.get("title", ""))
                self.hide_window()
            elif kind == "cmd":
                self.run_command_live(payload)
            elif kind == "install":
                self.run_install(payload)
            elif kind == "wiki":
                self.run_wiki(payload)
            elif kind == "file":
                self.run_file_search(payload)
            elif kind == "file_open":
                try:
                    os.startfile(payload)
                except Exception as e:
                    messagebox.showerror("HyprSearch", str(e))
                    return
                self.hide_window()
            elif kind in ("error", "info"):
                pass
        except Exception as e:
            messagebox.showerror("HyprSearch Error", str(e))

    def show_output_view(self, header):
        self._cancel_suggestion_job()
        self.results_container.pack_forget()
        for child in self.results_container.winfo_children():
            child.destroy()
        self.output_text.configure(state="normal", height=3)
        self.output_text.delete("1.0", "end")
        self.output_text.insert("end", header + "\n\n")
        self.output_text.configure(state="disabled")
        if not self.output_frame.winfo_ismapped():
            self.output_frame.pack(fill="both", expand=True, pady=(10, 0))
        self._fit_output_height()
        self._sync_size()

    def _fit_output_height(self):
        self.output_text.configure(state="normal")
        line_count = int(self.output_text.index("end-1c").split(".")[0])
        self.output_text.configure(state="disabled")
        height = max(3, min(line_count, 14))
        self.output_text.configure(height=height)

    def _append_output(self, text, newline=True):
        self.output_text.configure(state="normal")
        self.output_text.insert("end", text + ("\n" if newline else ""))
        self.output_text.see("end")
        self.output_text.configure(state="disabled")
        self._fit_output_height()
        self._sync_size()

    def run_command_live(self, command_text):
        self.show_output_view(f"$ {command_text}")
        q = queue.Queue()
        threading.Thread(target=stream_process, args=(command_text, True, q), daemon=True).start()
        self._poll_output_queue(q)

    def run_install(self, package_name):
        args = ["winget", "install", package_name, "--accept-package-agreements", "--accept-source-agreements", "--silent", "--disable-interactivity"]
        self.show_output_view(f"Installing {package_name}...")
        q = queue.Queue()
        threading.Thread(target=stream_process, args=(args, False, q), daemon=True).start()
        self._poll_output_queue(q)

    def _poll_output_queue(self, q):
        try:
            while True:
                line = q.get_nowait()
                if line is None:
                    self._append_output("\nDone.")
                    return
                self._append_output(line)
        except queue.Empty:
            pass
        self.root.after(60, lambda: self._poll_output_queue(q))

    def run_wiki(self, query):
        self.show_output_view(f"Wikipedia: {query}")
        threading.Thread(target=self._wiki_worker, args=(query,), daemon=True).start()

    def _wiki_worker(self, query):
        try:
            summary = search_wikipedia(query)
        except Exception as e:
            summary = str(e)
        self.root.after(0, lambda: self._append_output(summary, newline=False))

    def run_file_search(self, query):
        self._cancel_suggestion_job()
        self.output_frame.pack_forget()
        for child in self.results_container.winfo_children():
            child.destroy()
        self.current_candidates = [{"title": "Searching files...", "subtitle": query, "kind": "info", "payload": None}]
        row = self._build_result_row(0, self.current_candidates[0])
        row.pack(fill="x")
        if not self.results_container.winfo_ismapped():
            self.results_container.pack(fill="x", pady=(10, 0))
        self._sync_size()
        threading.Thread(target=self._file_worker, args=(query,), daemon=True).start()

    def _file_worker(self, query):
        try:
            results = file_search_diverse(query, max_results=5)
        except Exception:
            results = []

        candidates = []
        if results:
            for path in results:
                candidates.append({
                    "title": os.path.basename(path),
                    "subtitle": path,
                    "kind": "file_open",
                    "payload": path,
                    "icon": get_file_icon(path),
                })
        else:
            candidates.append({"title": "No files found", "subtitle": query, "kind": "error", "payload": None})

        self.root.after(0, lambda: self._render_file_results(query, candidates))

    def _render_file_results(self, query, candidates):
        if self.query_var.get() != query:
            return
        self.output_frame.pack_forget()
        for child in self.results_container.winfo_children():
            child.destroy()
        self.current_candidates = candidates
        for i, c in enumerate(candidates[:5]):
            row = self._build_result_row(i, c)
            row.pack(fill="x", pady=(0 if i == 0 else 3, 0))
        if not self.results_container.winfo_ismapped():
            self.results_container.pack(fill="x", pady=(10, 0))
        self._sync_size()

    def open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("HyprSearch Settings")
        win.geometry("380x220")
        win.resizable(False, False)
        win.attributes("-topmost", True)
        apply_theme_to_titlebar(win)

        frame = ttk.Frame(win, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Default search engine").pack(anchor="w")
        engine_var = tk.StringVar(value=SEARCHENGINE)
        engine_combo = ttk.Combobox(frame, textvariable=engine_var, values=sorted(SEARCH_ENGINES.keys()), state="readonly")
        engine_combo.pack(fill="x", pady=(4, 18))

        engine_pref_var = tk.BooleanVar(value=DO_ENGINESEARCH)
        ttk.Checkbutton(frame, text="Prefer engine search over Wikipedia summaries", variable=engine_pref_var).pack(anchor="w", pady=(0, 20))

        def save_and_close():
            global SEARCHENGINE, DO_ENGINESEARCH
            SEARCHENGINE = engine_var.get()
            DO_ENGINESEARCH = engine_pref_var.get()
            save_setting("search_engine", SEARCHENGINE)
            save_setting("do_engine_search", DO_ENGINESEARCH)
            win.destroy()

        ttk.Button(frame, text="Save", style="Accent.TButton", command=save_and_close).pack(fill="x")

    def create_icon_image(self):
        try:
            base = sys._MEIPASS #type: ignore
        except AttributeError:
            base = os.path.dirname(os.path.abspath(__file__))
        img = Image.open(os.path.join(base, "hyprsearch.png"), mode="r").convert("RGBA")
        
        icon_path = os.path.join(tempfile.gettempdir(), "hyprsearch.ico")
        img.save(icon_path, format="ICO")
        return icon_path

    def setup_tray(self):
        icon_path = self.create_icon_image()
        image = Image.open(icon_path)
        menu = pystray.Menu(
            pystray.MenuItem("Show", lambda: self.root.after(0, self.show_window), default=True),
            pystray.MenuItem("Exit", lambda: self.root.after(0, self.quit_app)),
        )
        self.icon = pystray.Icon("HyprSearch", image, "HyprSearch", menu)
        threading.Thread(target=self.icon.run, daemon=True).start()

    def setup_hotkey(self):
        try:
            self.hotkey_listener = pynput_keyboard.GlobalHotKeys({
                HOTKEY: lambda: self.root.after(0, self.toggle_window) #type: ignore
            })
            self.hotkey_listener.start()
        except Exception:
            self.hotkey_listener = None

    def quit_app(self):
        if self.hotkey_listener:
            try:
                self.hotkey_listener.stop()
            except Exception:
                pass
        if self.icon:
            self.icon.stop()
        self.root.destroy()


if __name__ == "__main__":
    HyprSearchApp()