# MIT License (c) 2024, 2025 Masakazu Suzuoki, AxTecChare
# See LICENSE.txt for details.

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from blindx.romhira import Romhira
from blindx.frontend import Backend
from blindx.frontend import Frontend
from blindx.edit_line import EditLine
from ft_viewer import FtViewer
import blindx.misc as misc

import flet as ft
import logging

misc.set_logger('app0')
backend = Backend()

special_keys = {
    'Page UP':'P', 
    'Page Down':'N', 
    'Home':'A', 
    'End':'E', 
    'Arrow Right':'F', 
    'Arrow Left':'B', 
    'Arrow Up':'P', 
    'Arrow Down':'N', 
    'Delete':'D', 
    'Backspace':'H', 
    'Enter':'M', 
    'Zenkaku Hankaku':'`', 
} 

def main(page: ft.Page):
    
    viewer = FtViewer()

    def output_callback(lines):
        viewer.set_output(lines, frontend.lineno)

    def on_change_callback(edit_line):
        viewer.set_input(edit_line.before.hiragana_and_preface(), edit_line.after)
        viewer.set_output(backend.lines, frontend.lineno)

    def on_connect(e):
        frontend.set_output_callback(output_callback)

    def on_disconnect(e):
        frontend.discard_callback()

    frontend = Frontend(backend)
    frontend.lineno = len(backend.lines) - 1

    edit_line = EditLine(frontend, on_change_callback)

    def on_keyboard_event(e):
        special_key = special_keys.get(e.key, None)
        if special_key:
            keycode, ctrl, shift = special_key, True, e.shift
        else:    
            keycode, ctrl, shift = e.key, e.ctrl or e.alt, e.shift

        edit_line.on_keyboard_input(keycode, ctrl, shift)

    viewer.start(page, on_keyboard_event)
    on_connect(None)
    viewer.set_input('', '')
    viewer.set_output(backend.lines, frontend.lineno)


backend.start()
ft.app(target=main)
backend.shutdown()
