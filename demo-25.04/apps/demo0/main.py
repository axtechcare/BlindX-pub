
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from blindx.romhira import Romhira
from blindx.frontend import Backend
from blindx.frontend import Frontend
from blindx.edit_line import EditLine
from ft_viewer import FtViewer
from blindx.kanhira import Kanhira

import flet as ft
import asyncio
import threading
import time
import asyncio
import websockets

backend = Backend()

auto_text_running = False
video_path = "faster-whisper/audios/sunset-sunrise-short2.mp4"

async def speech_to_text(path):
    chunk_size = 64 * 1024  # 64KB ずつ送信
    uri = "ws://localhost:8765"
    async with websockets.connect(uri, max_size=None) as websocket:  # max_size=None で無制限受信可

        with open(path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                await websocket.send(chunk)

        await websocket.send("[EOF]")
        results = await websocket.recv()

        segments = []
        for result in results.splitlines():
            items = result.split(',')
            segments.append([float(items[0]), float(items[1]), items[2]])
        return segments

def auto_play(start_time, segments, callback):
    called = set()
    while True:
        elapsed = time.time() - start_time
        for segment in segments:
            if segment[1] <= elapsed and segment[1] not in called:
                callback(segment)
                called.add(segment[1])

        if elapsed > 180:
            break
        time.sleep(0.1)  # 応答性向上のため短めに


async def main_async(page: ft.Page):

    segments = await speech_to_text(video_path);
    viewer = FtViewer()
    kanhira = Kanhira()

    def callback(segment):   
        kanji = segment[2]
        hiragana = kanhira.convert(kanji)
        frontend.append(key, hiragana + '\n', kanji + '\n')

    def output_callback(lines):
        viewer.set_input(lines, frontend.lineno)
        viewer.set_output(lines, frontend.lineno)

    def on_change_callback(edit_line):
        viewer.set_edit_input(edit_line.before.hiragana_and_preface(), edit_line.after)
        viewer.set_input(backend.lines, frontend.lineno)
        viewer.set_output(backend.lines, frontend.lineno)

    def on_connect(e):
        frontend.set_output_callback(output_callback)

    def on_disconnect(e):
        frontend.discard_callback()

    frontend = Frontend(backend)
    frontend.lineno = len(backend.lines) - 1

    key = 'Alice' # temporary
    edit_line = EditLine(frontend, on_change_callback)

    def on_keyboard_event(e):
        keycode, ctrl, shift = e.key, e.ctrl or e.alt, e.shift
        if keycode == 'F1':
            viewer.video.play()
            auto_play(time.time(), segments, callback)

        else:    
            edit_line.on_keyboard_input(keycode, ctrl, shift)

    viewer.start(page, on_keyboard_event, video_path)
    on_connect(None)
    viewer.set_input(backend.lines, 0)

backend.start()
ft.app(target=main_async)
backend.shutdown()
