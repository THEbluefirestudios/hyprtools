import subprocess
import ctypes
import sys
import pyautogui as mouse
mouse.FAILSAFE = False
from time import sleep

if not ctypes.windll.shell32.IsUserAnAdmin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
    sys.exit()



def run_cmd(command):
    result = subprocess.run(command, capture_output=True, text=True, shell=True)
    return result.stdout, result.stderr

def fix_my_pc():
    print("Fixing PC")
    process = subprocess.Popen(
        'DISM /Online /Cleanup-Image /RestoreHealth',
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        encoding='utf-8', shell=True
    )
    for line in process.stdout: #type: ignore
        print(line, end='')

    print(" ")
    run_cmd('sfc /scannow')
    print("SFC done!")
    
    print("Done!")



def pc_stress_test():
    def remap_score(s):
        old_min, old_max = 6.0, 9.9
        score = (s - old_min) / (old_max - old_min) * 9.0 + 1.0
        return round(max(1.0, min(10.0, score)), 1)

    run_cmd('winsat dwm')
    out, err = run_cmd('powershell -Command "Get-CimInstance Win32_WinSAT | Select-Object CPUScore, DiskScore, GraphicsScore, MemoryScore, WinSPRLevel | Format-List"')
    
    scores = {}
    for line in out.splitlines():
        if ':' in line:
            key, val = line.split(':', 1)
            try:
                scores[key.strip()] = remap_score(float(val.strip()))
            except ValueError:
                pass
    
    print(scores)

def delete_temp():
    out, err= run_cmd('del /q /f /s %temp%\\*')
    print(out or err)


def update_all():
    out, err= run_cmd('winget upgrade --all')
    print(out or err)


def refresh_display():
    mouse.hotkey('win', 'ctrl', 'shift', 'b')

def wifi_reset():
    out, err = run_cmd('ipconfig /flushdns')
    print(out or err)


update_all()


