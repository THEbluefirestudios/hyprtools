import pyautogui as m
import tkinter as tk
from tkinter import ttk
import sv_ttk as sv
import pywinstyles, sys
import darkdetect
system_theme = "dark" if darkdetect.isDark() else "light"
