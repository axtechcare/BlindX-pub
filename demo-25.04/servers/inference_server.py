# MIT License (c) 2024, 2025 Masakazu Suzuoki, AxTecChare
# See LICENSE.txt for details.

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from blindx.local_inference import LocalInference
import blindx.misc as misc
import asyncio
import websockets
import logging
import authenticate

async def main():
    misc.set_logger(__file__)
    logger = logging.getLogger(__name__)
    logger.info('start')
    connected_clients = set()
    async with LocalInference() as inference:

        async def handle_client(websocket):
            if not websocket in connected_clients:
                if not await authenticate.verify(logger, websocket):
                    return  
                connected_clients.add(websocket)
            try:
                async for message in websocket:
                    if message[0] == 'T':
                        result = inference.translate(message)
                    else:    
                        result = inference.control(message)
                    await websocket.send(result)

            except websockets.ConnectionClosed:
                logger.info('client disconnected.')
            finally:
                logger.info('client removed.')
                connected_clients.remove(websocket)

        async with websockets.serve(
                handle_client, "localhost", 6789, subprotocols=authenticate.valid_api_keys()):
            await asyncio.Future()  

if __name__ == "__main__":
    asyncio.run(main())
