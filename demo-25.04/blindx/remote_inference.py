# MIT License (c) 2024, 2025 Masakazu Suzuoki, AxTecChare
# See LICENSE.txt for details.

import asyncio
import websockets
import logging
from . import misc

class RemoteInference():

    def __init__(self):

        self.logger = logging.getLogger(__name__)
        self.websocket = None

        args = misc.load_args_from_file('config.txt')
        self.uri = args.get('inference_server_uri')
        self.key = args.get('api_key')

    async def __aenter__(self):
        await self.start_async()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.shutdown_async()

    async def start_async(self):
        self.logger.info('start')
        if not self.uri or not self.key: 
            self.logger.error('conection failed. uri/key not found.')
            return
        try:
            self.websocket = await websockets.connect(self.uri, subprotocols=[self.key])
            connected_message = await self.websocket.recv()
            self.logger.info(connected_message)

        except Exception as e:
            self.logger.error(f'connection failed {e}.')
            self.logger.error(f' ******************************************************** ')
            self.logger.error(f' * 変換サーバの uri または key が違う可能性があります')
            self.logger.error(f' *     uri : {self.uri}')
            self.logger.error(f' *     key : {self.key}')
            self.logger.error(f' ******************************************************** ')
            self.websocket = None
                
    async def shutdown_async(self):
        if self.websocket:
            self.logger.info('shutdown')
            await self.websocket.close()

    async def send_recv_async(self, dict_type, input_text, fixed_text='', aux_args=''):

        trial_count = 0
        while self.websocket and trial_count < 8:
            try:            
                if input_text:
                    message = dict_type + input_text + ':' + fixed_text + ':' + aux_args
                    await self.websocket.send(message)
                    return await self.websocket.recv()
                else:
                    return ''
            except websockets.ConnectionClosed:
                self.logger.info(f'reconnect')
                await self.shutdown_async()
                await self.start_async()
                trial_count += 1

        return input_text
