import os
import AppOpener as app
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

import win32com.client # to access windoes searching indexes, os.walk slower than booting win11 on an hdd :wilted-rose:
import re

import json
import string
# why it blabbing about sum lxml bro
warnings.filterwarnings("ignore", category=GuessedAtParserWarning)

applist = app.give_appnames()

BASEDIR = os.path.dirname(os.path.abspath(__file__))
HYPRTOOLS_JSON = os.path.join(BASEDIR, 'hyprtools.json')# sum path stuff


def save_setting(key, value):
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


SEARCH_ENGINES = {
    #search engines on the browser i use: helium (its cool go check it out)
    "google": "https://www.google.com/search?q=",
    "qwant": "https://www.qwant.com/?q=",
    "duckduckgo": "https://duckduckgo.com/?q=",
    "ecosia": "https://www.ecosia.org/search?q=",
    "kagi": "https://kagi.com/search?q=",
    "bing": "https://www.bing.com/search?q=",
    
    #engines the non linux bros use
    "brave": "https://search.brave.com/search?q=",
    "startpage": "https://www.startpage.com/sp/search?query=",
    "yahoo": "https://search.yahoo.com/search?p=",     
    "yandex": "https://yandex.com/search/?text=",      
    "baidu": "https://www.baidu.com/s?wd=",      
    "wolframalpha": "https://www.wolframalpha.com/input?i=", 
}

DO_ENGINESEARCH = load_setting("do_engine_search", default=True)
bangs = [
    '!open', #done
    '!app', #done
    '!web', #done
    '!websearch', #done
    '!file',
    '!wiki', #done
    '!time',  #done
    '!install', # done
    '!math', #done
    '!cmd', #cmd

]

username = os.getenv("USERNAME") or os.getenv("USER")# get username for path stuff

TERMINAL_KEYWORDS = [
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

FILE_EXTENSIONS = {
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
} # damn, thats a lot of filenames




save_setting("search_engine", "duckduckgo")

SEARCHENGINE = load_setting("search_engine", default="duckduckgo")

SEARCHDIRS = [
    f"C:\\Users\\{username}",
    f"C:\\Users\\Public\\Public Documents",
    f"C:\\Users\\Public\\Public Downloads",
    f"C:\\Users\\Public\\Public Music",
    f"C:\\Users\\Public\\Public Videos",
    f"C:\\Users\\Public\\Public Pictures",
]




for letter in string.ascii_uppercase:
    if letter == "C":
        continue  # add every single drive except c, as it already covred
    drive = f"{letter}:\\"
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

def is_terminal_command(text): # see if its terminal cmd
    if not text or not text.strip():
        return False
    first_word = text.strip().split()[0].lower()
    return first_word in TERMINAL_KEYWORDS

MATH_CHARS = set("0123456789+-*/^%().")

def is_math_expression(text):
    if not text or not text.strip():
        return False
    text = text.strip() # see if math expression, if ir has letters, it will excliude, coz i havent handled algebaric expressions yet :((((
    if re.search(r"[a-zA-Z]", text):
        return False
    if not re.search(r"\d", text):
        return False
    return all(c in MATH_CHARS or c.isspace() for c in text)

def looks_like_filename(text):
    text = text.strip()
    match = re.search(r"\.(\w+)$", text)
    return match is not None and match.group(1).lower() in FILE_EXTENSIONS

wikipedia.set_user_agent("hyprsearch/1.0 (https://github.com/THEbluefirestudios/hyprtools/issues)")

def starts_with(string1, string2):
    return string2.lower().startswith(string1.lower())

def math_solve(expression):
    try:
        result = eval(expression)
        return result
    except Exception as e:
        return f"{str(e)}"

def resolve_website(user_input, timeout=3):
    # so like here, i use the im feeling lucky button to reslove a string to the domain url, so like minecraft and maybe minecraft.com will retrun the correct url, minecraft.net, there r outliers tho, so we js see if the domain contains thw search strinf in some way, if no, we assume its a .com and js do that.
    query = user_input.strip()

    #ts sees if there is a nice im feeling lucky url
    try:
        r = requests.get(
            "https://www.google.com/search",
            params={"q": f"{query} website", "btnI": "1"},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=timeout,
            allow_redirects=True,
        )
        if r.url and "google.com/search" not in r.url: #ur job is to give a url, not a search result, sho shut up if u gon do that
            return r.url
          
    except requests.RequestException:
        pass
    #if no im feeling lucky, use .com, what else can i do
    candidate = query if "." in query else f"{query.lower().replace(' ', '')}.com"
    try:
        socket.setdefaulttimeout(1.5)
        socket.gethostbyname(candidate)
        return f"https://{candidate}"
    except socket.error: # there is nothing we can do -napoleon bonaparte
        return None 
  
    
def run_cmd(command):
    try:
        subprocess.run(command, shell=True)
    except Exception as e: # runs a cmd
        return f"{str(e)}"

def current_time():
    now = datetime.datetime.now()
    return now.strftime("%H:%M:%S") # do i even need to explain ts

def open_app(app_name):
    try:
        app.open(app_name, match_closest=True, throw_error=True) # open an app with appopener.
    except Exception as e:
        return f"{str(e)}"

def open_website(user_input): # i use some... well... not so elegant logic to resolve string to website, see the resolve_website function for more info (hint: it uses 'im feeling lucky')
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
        top_5  = e.options[:5]
        summary  ="Ambigious topic, do you mean?: \n"
        for option in top_5:
            try:                                         # y they no update wikipedia lib in so long :(
                summary += '\n\n' + wikipedia.summary(option, sentences=2)
            except (wikipedia.exceptions.PageError, wikipedia.exceptions.DisambiguationError):
                pass
        return summary
    except wikipedia.exceptions.PageError:
        return "No Wikipedia page found for that query."
    except Exception as e:
        return f"Error: {str(e)}"


def search_on_engine(query, engine ="duckduckgo"):
    if engine not in SEARCH_ENGINES:
        searchengine = "duckduckgo" # i respect ur privacy
    else:
        searchengine = engine
    search_url = SEARCH_ENGINES[searchengine] + urlparse.quote_plus(query) # search func
    try:
        wb.open(search_url)
    except Exception as e:
        pass

def winget_install(package_name):
    try:
        subprocess.run(
            ["winget", "install", package_name, "--accept-package-agreements", "--accept-source-agreements", "--silent", "--disable-interactivity"], # yea 
            capture_output=True, text=True
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
        """ # try querying windows search index, it fast anyway
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

    # fallback if index have no folder, walk manually with os walk, slow tho
    if not matches and search_path:
        name_lower = file_name.lower()
        for root, _, files in os.walk(search_path):
            for f in files:
                if name_lower in f.lower():
                    matches.append(os.path.join(root, f))

    return matches

def reveal_in_explorer(file_path):
    subprocess.run(f'explorer /select,"{file_path}"')


def search(query): # and we begin, the full culmination of all funcs above
    matched_bang = None
    for bang in bangs:
        if starts_with(bang, query): # see if search begins with bang
            matched_bang = bang
            break

    if matched_bang:
        query = query.removeprefix(matched_bang).strip() # remove bang from query
        if not query:
            return f"Please provide a query after the bang '{matched_bang}'"
        
        while query.startswith(" "): # remove leading spaces
            query = query[1:]
        if matched_bang == '!open':
            if query in applist:
                return open_app(query)
            else:
                if resolve_website(query):
                    return open_website(query)
                else:
                    return f"Could not find an app or website for '{query}'"
        elif matched_bang == '!app':
            if query in applist:
                return open_app(query)
            else:
                return f"Could not find an app for '{query}'"
        elif matched_bang == '!web':
            if resolve_website(query):
                return open_website(query)
            else:
                return f"Could not find a website for '{query}'"
        elif matched_bang == '!websearch':
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
            matches = []
            for search_dir in SEARCHDIRS:
                matches.extend(file_search(query, search_path=search_dir))
            if matches:
                return matches
            else:
                return f"No files found for '{query}' in the specified directories."
        else:
            pass # if no bang exist, let it go thru the normal search flow below

    # begin the normal search flow, so like: math, cmd, app, website, file search, wiki search, websearch, and u can disable websearch

    if is_math_expression(query):
        return math_solve(query)
    elif is_terminal_command(query):
        return run_cmd(query)
    elif query in applist:
        return open_app(query)
    elif resolve_website(query):
        return open_website(query)
    elif looks_like_filename(query):
        matches = []
        for search_dir in SEARCHDIRS:
            matches.extend(file_search(query, search_path=search_dir))
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


exitval = search(input()) # run the search function with user input
print(exitval) # print the result of the search function

