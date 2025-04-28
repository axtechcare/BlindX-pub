# MIT License (c) 2024, 2025 Masakazu Suzuoki, AxTecChare
# See LICENSE.txt for details.

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import asyncio
from blindx.kanhira import Kanhira
from blindx.remote_inference import RemoteInference
from rapidfuzz import fuzz
import jaconv

class Proofreader():

    def __init__(self):
        self.kanhira = Kanhira()
        self.inference = RemoteInference()

    async def start_async(self):
        await self.inference.start_async()
        self.dict_names = await self.inference.send_recv_async('query:', 'dict_names')
        self.dict_count = len(self.dict_names.split(':'))

    async def shutdown_async(self):
        await self.inference.shutdown_async()
        
    def concat_output_text(self, output_text):
        items = output_text.split(',')
        tokens = items[::2]
        probs = items[1::2]
        result_text = ''.join(tokens)
        return jaconv.h2z(result_text, ascii=True, digit=True)

    def get_score(self, zenkaku_output_text):
        return fuzz.ratio(self.zenkaku_input_text, zenkaku_output_text)

    async def test_async(self, input_text, num_beams = 2):

        self.input_text = input_text
        self.hiragana_text = self.kanhira.convert(self.input_text)
        self.zenkaku_input_text = jaconv.h2z(self.input_text, ascii=True, digit=True)

        self.output_texts = []
        self.passed_index = 0

        for dict_index in range(0, self.dict_count):
            dict = f'T{dict_index}:{num_beams}+:'
            # t5_args = 'do_sample=True,top_k=100'
            t5_args = ''

            blindx_texts =  await self.inference.send_recv_async(dict, self.hiragana_text, '', t5_args)
            output_texts = blindx_texts.split(':')
            self.output_texts += output_texts
            for output_text in output_texts:
                zenkaku_output_text = self.concat_output_text(output_text)
                if self.get_score(zenkaku_output_text) == 100:
                    return True
                self.passed_index += 1

        return False    

    async def set_pattern_async(self, pattern):
        self.kanhira.set_pattern(pattern)
        await self.inference.send_recv_async('set:wrapper_pattern:', pattern)

    async def set_replacement_async(self, replacement):
        self.kanhira.set_replacement(replacement)
        await self.inference.send_recv_async('set:wrapper_replacement:', replacement)

