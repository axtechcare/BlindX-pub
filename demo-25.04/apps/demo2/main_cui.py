#@title かな漢字変換テスト
# MIT License (c) 2024, 2025 Masakazu Suzuoki, AxTecChare
# See LICENSE.txt for details.

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import asyncio
import blindx.misc as misc
from proofreader import Proofreader
import argparse
from tqdm import tqdm
import logging

if __name__ == "__main__":

    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', help='source filename', default='input.txt')
    parser.add_argument('-o', '--output', help='result filename', default='-')
    parser.add_argument('-e', '--echo', help='phrase') 
    parser.add_argument('--encoding', choices=['utf-8', 'utf-16-le'], default='utf-8', help='text encoding') 
    parser.add_argument('--hotwords', nargs='+', help='hot words')
    args = parser.parse_args()

    def read_lines(name):
        with open(name, 'r', encoding=args.encoding) as f:
            lines = []
            for input_text in f:
                line = ''
                for char in input_text.rstrip('\n'):
                    if ord(char) != 65279:
                        line += char
                lines.append(line)
            return lines    

    async def main():
        misc.set_logger('kousei', logging.WARN)

        hotwords = [
            ' ', '　', '、', ',', '…', '^◆.*$',
            '【.*?】', '［.*?］', '^◆.*$', '//.*$', '^;.*$',
        ]
        if args.hotwords:
            hotwords += args.hotwords

        if args.echo:
            lines = [args.echo]
        else:    
            lines = read_lines(args.input)

        proofreader = Proofreader()
        await proofreader.start_async()

        await proofreader.set_pattern_async('|'.join(hotwords))
        await proofreader.set_replacement_async('$')

        if args.output == '-':
            file = sys.stdout
            progress_bar = None
        else:    
            file = open(args.output, 'w')
            progress_bar = tqdm(lines, total=len(lines), desc="校正中")

        fail_count = 0
        for lineno, line in enumerate(progress_bar if progress_bar else lines):
            if not line: continue

            if await proofreader.test_async(line):
                print(f'{lineno:4d}:PASS: {proofreader.input_text}', file=file)
                print(f'        {proofreader.passed_index}; {proofreader.output_texts[proofreader.passed_index]}', file=file)
            else:    
                fail_count += 1
                print(f'{lineno:4d}:FAIL: {proofreader.zenkaku_input_text}', file=file)
                output_scores = {}
                for output_text in proofreader.output_texts:
                    zenkaku_output_text = proofreader.concat_output_text(output_text)
                    score = proofreader.get_score(zenkaku_output_text)
                    output_scores[zenkaku_output_text] = score

                sorted_scores = sorted(output_scores.items(), key=lambda x: x[1], reverse=True)
                for item in sorted_scores:
                    print(f'      {item[1]:3.0f}: {item[0]}', file=file)

            if progress_bar:       
                progress_bar.set_postfix({'怪しい行': fail_count})

        file.close()            
        await proofreader.shutdown_async()

    asyncio.run(main())
