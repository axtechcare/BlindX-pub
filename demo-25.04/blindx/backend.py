# MIT License (c) 2024, 2025 Masakazu Suzuoki, AxTecChare
# See LICENSE.txt for details.

from .remote_inference import RemoteInference
from .backend_line import BackendLine

import asyncio
import time
import threading
import logging

class ConditionVariable:
    def __init__(self):
        self.condition = threading.Condition()
        self.is_ready = False

    def notify_all(self):    
        with self.condition:
            self.is_ready = True
            self.condition.notify_all()

    def wait(self, timeout=None):    
        with self.condition:
            while not self.is_ready:
                if not self.condition.wait(timeout):
                    return False
            self.is_ready = False
        return True    

class Backend():

    def __init__(self):
        self.lines = []
        self.logger = logging.getLogger(__name__)
        self.exec_condition = ConditionVariable()
        self.output_callbacks = set()
        self.key = None
        self.dict_names = None
        self.wait_level = 0
        self.wait_times = [
            None, 1.0, 2.0, 4.0
        ]
        self.attrs = {}

    def default_attr(self):    
        return {
            'max_concat_size':64,
            'truncate_step':12,
            'dict_type':'T0:1:',
        }

    def set_attr(self, key, attr):
        self.logger.info(f'set_attr key={key}, attr={attr}')
        self.attrs[key] = attr

    def get_attr(self, key):
        return self.attrs.get(key, self.default_attr())

    def remove_attr(self, key):
        del self.attrs[key]

    def add_output_callback(self, output_callback):
        self.logger.info('add_output_callback')
        self.output_callbacks.add(output_callback)

    def discard_output_callback(self, output_callback):
        self.logger.info('discard_output_callback')
        self.output_callbacks.discard(output_callback)

    def discard_output_callbacks(self):    
        self.logger.info('discard_output_callbacks')
        self.output_callbacks.clear()

    def clear_all_lines(self, key = None):         
        self.logger.info(f'clear_all_lines {key}')
        self.lines = [] if key == None else [line for line in self.lines if line.key != key]
        self.invoke_output_callbacks()

    def append_line(self, key):
        while self.lines and self.lines[-1].key == None:
            self.lines = self.lines[:-1]

        self.lines.append(BackendLine())
        self.lines[-1].key = key
        return len(self.lines) - 1

    def clear_lines(self, key, lineno, is_input_text_only=False):
        while lineno < len(self.lines):
            if self.lines[lineno].key == key:
                if is_input_text_only:
                    self.lines[lineno].input_text = ''
                else:    
                    self.lines[lineno] = BackendLine()
            lineno += 1

    def insert_line(self, key, lineno):
        for replace_lineno in range(lineno - 1, -1, -1):
            if self.lines[replace_lineno].key == key:
                break
            elif self.lines[replace_lineno].key == None:
                self_lines[replace_lineno].key = key
                return replace_lineno

        self.lines.insert(lineno, BackendLine())
        self.lines[lineno].key = key
        return lineno

    def delete_line(self, key, lineno):

        if 0 <= lineno < len(self.lines):
            self.lines[lineno] = BackendLine()
            while len(self.lines) > lineno and not self.lines[-1].input_text:
                self.lines = self.lines[:-1]

        return self.prev_line(key, lineno)
        
    def next_line(self, key, lineno):
        while lineno < len(self.lines) - 1:
            lineno += 1
            if self.lines[lineno].key == key:
                return lineno
        return self.append_line(key)    

    def prev_line(self, key, lineno):
        while lineno > 0:
            lineno -= 1
            if self.lines[lineno].key == key:
                return lineno
        return -1

    def invoke_output_callbacks(self):
        for output_callback in self.output_callbacks:
            output_callback(self.lines)

    def start(self):
        self.logger.info('start')
        self.is_cancel = False
        self.thread = threading.Thread(target=self.thread_func)
        self.thread.start()
        while not self.dict_names:
            time.sleep(0.1)

    def shutdown(self):    
        self.logger.info('shutdown')
        self.discard_output_callbacks()
        self.is_cancel = True
        self.exec_condition.notify_all()
        self.thread.join()

    def report(self, key, str = 'list'): 
        print(f'{str} : key={key}')
        for lineno, line in enumerate(self.lines):
            if line.key == None or line.key != None:
                line.report(lineno)

    def request(self, key):
        self.key = key
        self.exec_condition.notify_all()

    def thread_func(self):
        asyncio.run(self.event_loop())

    async def event_loop(self):
        async with RemoteInference() as inference:
            await self.query_list_async(inference)
            is_in_time = False
            while not self.is_cancel:
                is_in_time = self.exec_condition.wait(self.wait_times[self.wait_level])
                if not self.is_cancel:
                    await self.on_request_async(inference, is_in_time)

    async def query_list_async(self, inference):
        recv_message = await inference.send_recv_async('query:', 'dict_names')
        self.dict_names = recv_message.split(':')

    async def on_request_async(self, inference, is_in_time):

        if is_in_time:
            self.wait_level = 1
        else:    
            self.wait_level = (self.wait_level + 1) % len(self.wait_times)

        for lineno, line in enumerate(self.lines):
            attr = self.get_attr(line.key)
            if line.key == self.key:
                if line.input_text != line.stage_input_text:
                    if self.fix_trivial_difference(line):
                        pass
                    elif line.input_text.endswith(('\n', '。')):
                        await self.predict_async_long(inference, attr, line, lineno)
                        self.invoke_output_callbacks()
                    else:
                        truncated_stage_input_text = self.truncate_input_text(
                            line.input_text, attr['truncate_step'])
                        if truncated_stage_input_text != line.stage_input_text:
                            await self.predict_async_short(inference, attr, line, truncated_stage_input_text)
                            self.invoke_output_callbacks()

                if self.wait_level >= 2 and line.long_output_text != line.output_text:
                    await self.predict_async_long(inference, attr, line, lineno)
                    self.invoke_output_callbacks()

    async def predict_async_short(self, inference, attr, line, stage_input_text):

        if line.do_short:
            output = await inference.send_recv_async(attr['dict_type'], stage_input_text)
            # output = await inference.send_recv_async(attr['dict_type'], stage_input_text, '', 'num_beams=1')
        else:    
            output = stage_input_text

        line.stage_input_text = stage_input_text
        line.prev_output_text = line.output_text
        line.output_text = output

    async def predict_async_long(self, inference, attr, line, lineno):
        stage_input_text = line.input_text
        if line.do_long:
            all_stage_input_text = self.concat_prev_inputs(line.key, lineno, attr['max_concat_size'])
            recv_message = await inference.send_recv_async(attr['dict_type'] , all_stage_input_text)
            output = recv_message.split('\\&')[-1]
            line.do_short = True # don't forget
        else:    
            output = line.input_text

        line.stage_input_text = stage_input_text
        line.prev_output_text = line.output_text
        line.long_output_text = line.output_text = output

    def fix_trivial_difference(self, line):
        if line.output_text == line.long_output_text:
            if line.input_text + '\n' == line.stage_input_text:
                line.output_text = line.output_text.strip()
            elif line.input_text == line.stage_input_text + '\n':
                line.output_text += '\n'
            else:
                return False
            line.stage_input_text = line.input_text
            line.long_output_text = line.prev_output_text = line.output_text
            return True
        else:
            return False


    def truncate_input_text(self, input_text, truncate_step):
        if input_text.endswith(('\n', '。', '　', '、')):
            return input_text

        input_len = len(input_text)
        truncated_len = input_len - input_len % truncate_step
        return input_text[:truncated_len]

    def concat_prev_inputs(self, key, lineno, max_concat_size):    
        all_stage_input_text = ''
        while lineno >= 0 and len(all_stage_input_text) < max_concat_size:
            if self.lines[lineno].key == key:
                all_stage_input_text = self.lines[lineno].input_text + '\\&' + all_stage_input_text 
            lineno -= 1
        return all_stage_input_text[:-2]




        


