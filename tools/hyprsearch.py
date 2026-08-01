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

# why it blabbing about sum lxml bro
warnings.filterwarnings("ignore", category=GuessedAtParserWarning)

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

wikipedia.set_user_agent("hyprsearch/1.0 (https://github.com/THEbluefirestudios/hyprtools/issues)")
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
            params={"q": query, "btnI": "1"},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=timeout,
            allow_redirects=True,
        )
        if r.url and "google.com/search" not in r.url:
            if query.lower() in r.url.lower():
                return r.url
            else:
                if query.lower().replace(" ", "") in r.url.lower().replace(" ", ""):
                    return r.url
                else:
                    pass
    except requests.RequestException:
        pass
    #IF NO IM FEELING LUCKY, JUST ADD .COM AT THE END
    candidate = query if "." in query else f"{query.lower().replace(' ', '')}.com"
    try:
        socket.setdefaulttimeout(1.5)
        socket.gethostbyname(candidate)
        return f"https://{candidate}"
    except socket.error:
        return None
    
def run_cmd(command):
    try:
        subprocess.run(command, shell=True)
    except Exception as e:
        return f"{str(e)}"

def current_time():
    now = datetime.datetime.now()
    return now.strftime("%H:%M:%S")

def open_app(app_name):
    try:
        app.open(app_name, match_closest=True, throw_error=True)
    except Exception as e:
        return f"{str(e)}"

def open_website(user_input): # i use some... well... not so elegant logic to resolce string to website, see the resolve_website function for more info (hint: it uses 'im feeling lucky')
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
            try:
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
            capture_output=True, text=True
        )

    except Exception as e:
        return f"{str(e)}"
'''
def file_search(file_name, search_path):
    matches = []
    for root, dirs, files in os.walk(search_path):
        for file in files:
            if file_name.lower() in file.lower():
                matches.append(os.path.join(root, file))
    return matches'''

open_website("fmovies")