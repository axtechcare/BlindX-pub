# MIT License (c) 2024, 2025 Masakazu Suzuoki, AxTecChare
# See LICENSE.txt for details.


from .text_wrapper import TextWrapper
from . import misc
from transformers import T5ForConditionalGeneration, T5Tokenizer
import os
import asyncio
import torch
import logging
import re
import torch.nn.functional as F

class LocalInference():
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        os.environ['CUDA_VISIBLE_DEVICES'] = '0'

        args = misc.load_args_from_file('config.txt')
        model_filter = args.get('model_filter', 'all')

        self.target_dir = misc.search_path('models')
        self.t5_names = [name for name in os.listdir(self.target_dir) if re.search(model_filter, name)]
        self.device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
        self.logger.info(f'torch: version={torch.__version__} device={self.device}')
        self.tokenizer = T5Tokenizer.from_pretrained('sonoisa/t5-base-japanese-v1.1', legacy=True)
        self.text_wrapper = TextWrapper()
        self.hex_pattern = re.compile(r'<0x([0-9A-Fa-f]+)>')

        self.t5s = []
        for t5_name in self.t5_names:
            full_path = os.path.join(self.target_dir, t5_name)
            self.logger.info(f'load {full_path}')
            t5 = T5ForConditionalGeneration.from_pretrained(full_path)
            t5.to(self.device)
            self.t5s.append(t5)

    def translate(self, message):
        
        try:
            t5_index, input_text, fixed_text, args = self.parse_input_message(message)
            if not input_text: return ''

            t5_outputs = self.t5s[t5_index].generate(
                **args, 
                input_ids = self.tokenizer(input_text, return_tensors='pt').input_ids.to(self.device),
                decoder_input_ids = self.tokenize_fixed_text(fixed_text),
            )
            if args['output_scores'] == True:
                result_message = self.assemble_output_message_with_prob(t5_outputs, t5_index)
            else:        
                result_message = self.assemble_multiple_output_message(t5_outputs)
            self.report(message, result_message)
            return result_message

        except Exception as e:
            self.logger.error(e)
            errstr = str(e).replace('\n', '\\n').replace(':', ';')
            msgstr = message.replace(':', ';')
            return f'ERROR:むこうなこまんどです:{errstr}:{msgstr}'

    def parse_input_message(self, message):    
        list = message.split(':')
        t5_index = int(list[0][1:])

        args = {}
        args['max_length'] = 256

        if list[1][-1] == '+':
            num_return_sequences = int(list[1][:-1])
            args |= {
                'output_scores' : True,
                'return_dict_in_generate' : True,
                'num_return_sequences' : num_return_sequences,
                'num_beams' : num_return_sequences,
            }
        else:    
            num_return_sequences = int(list[1])
            args |= {
                'output_scores' : False,
                'return_dict_in_generate' : False,
                'num_return_sequences' : num_return_sequences,
                'num_beams' : max(4, num_return_sequences),
            }
        input_text = self.text_wrapper.encode(list[2])
        fixed_text = list[3] if len(list) > 3 else '' 

        if len(list) > 4:
            args |= misc.parse_key_value_string(list[4])
            if args['output_scores'] == True:
                args['num_beams'] = args['num_return_sequences']

        return t5_index, input_text, fixed_text, args

    def tokenize_fixed_text(self, fixed_text):
        if not fixed_text:
            return None

        decoder_input_ids_list = self.tokenizer(fixed_text, return_tensors='pt').input_ids.tolist()[0]
        truncated_decoder_input_ids_list = []
        for id in decoder_input_ids_list:
            if id == self.tokenizer.eos_token_id:
                break
            truncated_decoder_input_ids_list.append(id)

        return torch.tensor([truncated_decoder_input_ids_list]).to(self.device)

    def assemble_tokens_with_prob(self, tokens, logps):

        texts = []
        hex_values = []

        for token, logp in zip(tokens, logps):
            hex = self.hex_pattern.search(token)
            if hex:
                hex_values.append(int(hex.group(1), 16))
            else:
                if hex_values:
                    utf8_token = bytes(hex_values).decode('utf-8')
                    texts.append(f'{utf8_token},{1.00}')
                    hex_values.clear()

                sanity_token = token.replace('▁', '').replace('</s>', '')
                if sanity_token:
                    prob = float(torch.exp(torch.tensor(logp)));
                    texts.append(f'{sanity_token},{prob:.2f}')
        
        if hex_values:
            utf8_token = bytes(hex_values).decode('utf-8')
            texts.append(f'{utf8_token},{1.00}')

        return texts            

    def assemble_output_message_with_prob(self, t5_outputs, t5_index):

        transition_scores = self.t5s[t5_index].compute_transition_scores(
            t5_outputs.sequences,
            t5_outputs.scores,
            normalize_logits=True
        )  

        result_texts = []
        for sequence, score in zip(t5_outputs.sequences, transition_scores):
            tokens = self.tokenizer.convert_ids_to_tokens(sequence[1:])  # skip BOS
            logps  = score.tolist()
            texts = self.assemble_tokens_with_prob(tokens, logps)
            result_texts.append(self.text_wrapper.decode(','.join(texts)))

        return ':'.join(result_texts)

    def assemble_multiple_output_message(self, t5_outputs):
        result_text = []
        for t5_output in t5_outputs:
            output_text = self.text_wrapper.decode(
                self.tokenizer.decode(
                    t5_output, skip_special_tokens = True
                )
            )
            result_text.append(output_text)
        return ':'.join(result_text)

    def control(self, message):
        items = message.split(':', 3)
        if items[0] == 'query' and items[1] == 'dict_names':
            output = ':'.join(self.t5_names)
            self.logger.info(f'query {output}')
            return output
        if items[0] == 'set' and items[1] == 'wrapper_pattern':
            self.logger.info(message)
            self.text_wrapper.set_pattern(items[2])
            return 'OK'
        if items[0] == 'set' and items[1] == 'wrapper_replacement':
            self.logger.info(message)
            self.text_wrapper.set_replacement(items[2])
            return 'OK'
        else:
            errstr = f'ERROR:むこうなこまんどです:{message}'
            self.logger.info(errstr)
            return errstr

    def report(self, input_text, output_text):
        replaced_in = input_text.replace('\n', '\\n')
        replaced_out = output_text.replace('\n', '\\n')
        self.logger.info(f"in:  {replaced_in}") # no backslash inside '{}'
        self.logger.info(f"out: {replaced_out}")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        pass




