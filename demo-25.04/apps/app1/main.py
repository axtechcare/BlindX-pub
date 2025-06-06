# MIT License (c) 2024, 2025 Masakazu Suzuoki, AxTecChare
# See LICENSE.txt for details.

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from blindx.backend import Backend
from blindx.login import Login
from blindx.misc import set_logger
from ft_app import FtApp

import flet as ft
import logging

set_logger('app1')
logger = logging.getLogger(__name__)
backend = Backend()
login = Login()

async def main_async(page: ft.Page):

    my_key = await login.login_async()

    app = FtApp(page, my_key, login.active_names, backend)

    async def on_connect_async(e):
        await login.connect_async(my_key)
        await app.connect_async()

    async def on_disconnect_async(e):
        await app.disconnect_async()
        await login.disconnect_async(my_key)

    page.on_connect = on_connect_async
    page.on_disconnect = on_disconnect_async
    await app.start_async()

backend.start()
ft.app(target=main_async)
backend.shutdown()

