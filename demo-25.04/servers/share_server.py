#!/usr/bin/env python3
#
# chat server

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
#
import blindx.misc as misc
import asyncio
import websockets
import logging

misc.set_logger(__file__)
logger = logging.getLogger(__name__)
connected_clients = set()
connected_names = {}
lines = []

available_names = [
    'Alice', 'Bob', 'Charol', 'Charile', 'Dave', 'Eve', 'Ellen', 'Frank', 'Isac', 'IVan', 
    'Justin', 'Marvin', 'Matilda', 'Oscar', 'Peggy', 'Steve', 'Trent', 'Trudy', 'Walter', 'Zoe' 
]

def report():
    print('line:')
    for lineno, line in enumerate(lines):
        replaced_line = line.replace('\n', '\\n')
        print(f"{lineno} : {replace_line}")


async def send_all_async(websocket, message):
    for client in connected_clients:
        if client != websocket:
            await client.send(message)

async def handle_client(websocket):
    global lines
    if not websocket in connected_clients:
        connected_clients.add(websocket)
        name = available_names.pop(0)
        available_names.append(name)
        connected_names[websocket] = name

    try:
        async for message in websocket:
            if message == 'clear:':
                logger.info('recv clear')
                lines = []
                await send_all_async(websocket, 'clear:')

            elif message == 'reload:':
                logger.info('recv reload')
                name_message = 'name' + ':' + connected_names[websocket]

                for key, value in connected_names.items():
                    if key != websocket: 
                        name_message += ':' + value

                await websocket.send(name_message)
                for line in lines:
                    await websocket.send(line)
            else:
                try:
                    lineno = int(message.split(':', 1)[0])
                    lines.extend(['']  * (lineno + 1 - len(lines)))
                    lines[lineno] = message
                    await send_all_async(websocket, message)
                except Exception as e:
                    logger.warning(f'invalid message message={message} except={e}')
                # report()    

    except websockets.ConnectionClosed:
        logger.info('client disconnected')
    finally:
        logger.info('client removed')
        name = connected_names[websocket]
        connected_clients.remove(websocket)
        del connected_names[websocket]

async def main():
    logger.info('start')
    async with websockets.serve(handle_client, "localhost", 6790):
        await asyncio.Future()  

if __name__ == "__main__":
    asyncio.run(main())
