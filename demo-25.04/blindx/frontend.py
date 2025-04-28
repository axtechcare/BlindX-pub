# MIT License (c) 2024, 2025 Masakazu Suzuoki, AxTecChare
# See LICENSE.txt for details.

from .romhira import Romhira
from .backend import Backend
from .backend import BackendLine
from enum import Enum
import logging

class Frontend():
    def __init__(self, backend):
        self.logger = logging.getLogger(__name__)
        self.backend = backend
        self.romhira = Romhira()
        self.lineno = -1
        self.is_new_line = True
        self.input_text = ''

    def set_output_callback(self, output_callback):
        self.output_callback = output_callback
        self.backend.add_output_callback(self.output_callback)

    def discard_output_callback(self):
        self.backend.discard_output_callback(self.output_callback)
        self.output_callback = None

    def invoke_output_callbacks(self):
        self.backend.invoke_output_callbacks()

    def invoke_frontend_output_callback(self):
        self.output_callback()

    def current_input_text(self):
        return self.backend.lines[self.lineno].input_text.rstrip() if self.lineno >= 0 else ''

    def terminate_line(self, end = '\n'):
        if 0 <= self.lineno < len(self.backend.lines):
            if not self.backend.lines[self.lineno].input_text.endswith(end):
                self.backend.lines[self.lineno].input_text += end

    def clear_all_lines(self, key = None):
        self.backend.clear_all_lines(key)
        self.lineno = -1
        self.is_new_line = True
        return ''

    def clear_line(self, key):
        if self.is_new_line:
            self.is_new_line = False
            return self.current_input_text()

        else:
            self.backend.clear_lines(key, self.lineno)
            self.lineno = self.backend.prev_line(key, self.lineno + 1)
            return self.current_input_text()

    def prev_line(self, key):
        self.lineno = self.backend.prev_line(key, self.lineno)
        if self.lineno < 0:
            self.is_new_line = True
            return ''
        else:
            self.is_new_line = False
            return self.current_input_text()

    def next_line(self, key):
        self.is_new_line = False
        self.lineno = self.backend.next_line(key, self.lineno)
        return self.current_input_text()

    def join_line(self, key):
        if 0 <= self.lineno < len(self.backend.lines):
            next_lineno = self.backend.next_line(key, self.lineno)
            input_text = self.backend.lines[self.lineno].input_text.rstrip()
            next_input_text = self.backend.lines[next_lineno].input_text.rstrip()
            self.backend.lines[self.lineno].input_text = input_text + next_input_text
            self.backend.delete_line(key, next_lineno)

        return self.current_input_text()

    def delete_line(self, key):
        if self.is_new_line:
            self.is_new_line = False
            return self.current_input_text()
        else:
            self.lineno = self.backend.delete_line(key, self.lineno)
            return self.current_input_text()

    def insert_next_line(self, key, is_insert=False):
        if is_insert:
            self.lineno = self.backend.insert_line(key, self.lineno + 1)
        else:
            self.lineno = self.backend.next_line(key, self.lineno)

    def insert_and_move_to_next_line(self, key, is_insert=False):
        prev_lineno = self.lineno
        self.insert_next_line(key, is_insert)
        self.backend.lines[self.lineno] = self.backend.lines[prev_lineno]
        self.backend.lines[prev_lineno] = BackendLine()
        self.backend.lines[prev_lineno].key = key

    def move_from_romhira(self, key):
        self.lineno = self.backend.prev_line(key, self.lineno + 1)
        try:
            line = self.backend.lines[self.lineno]
            line.do_short = line.do_long = not self.romhira.is_kanji
            line.input_text = self.romhira.hiragana_and_preface()
            self.romhira.clear()
        except IndexError:
            return ''
        return line.input_text

    def append(self, key, input_text, output_text):
        self.insert_next_line(key)
        self.lineno = self.backend.prev_line(key, self.lineno + 1)

        line = self.backend.lines[self.lineno]
        line.do_short = line.do_long = True
        line.input_text = input_text
        if output_text:
            line.stage_input_text = input_text
            line.prev_output_text = output_text
            line.output_text = output_text
            line.long_output_text = output_text
            self.backend.invoke_output_callbacks()

        self.backend.request(key)    

    def update(self, key, romaji_text, is_insert = False):

        input_text = ''
        self.romhira.clear()

        for char in romaji_text:
            if self.is_new_line:
                self.insert_next_line(key, is_insert)
                self.is_new_line = False

            self.romhira.add(char)
            if char == '\n':
                self.is_new_line = True
                input_text = self.move_from_romhira(key)

        if not self.is_new_line:
            input_text = self.move_from_romhira(key)

        else: 
            input_text = ''
            if is_insert:    
                self.is_new_line = False
                self.insert_next_line(key, is_insert)

        self.backend.request(key)    
        return input_text, self.backend.lines



