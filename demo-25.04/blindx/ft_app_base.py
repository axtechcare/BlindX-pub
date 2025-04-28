# MIT License (c) 2024, 2025 Masakazu Suzuoki, AxTecChare
# See LICENSE.txt for details.


from blindx.frontend import Frontend
from blindx.auto_text import AutoText
from blindx.backend_share import BackendShare
from blindx.ft_settings import FtSettingDrawer

class FtAppBase():

    async def start_async_internal(self):
        pass

    async def set_input_async(self, text):
        pass

    def update(self):
        pass

    def get_input(self):
        pass

    def set_output(self, lines):
        pass

    def __init__(self, page, my_key, active_names, backend):
        self.page = page
        self.my_key = my_key
        self.active_names = active_names
        self.frontend = Frontend(backend)
        self.backend_share = BackendShare(backend)

    def output_callback(self, lines):
        self.set_output(lines)

    async def start_async(self):    

        await self.backend_share.start_async()
        if self.backend_share.my_key:
            self.my_key = self.backend_share.my_key
            self.active_names = self.backend_share.active_names

        self.settings = FtSettingDrawer(self.my_key, self.frontend.backend)
        self.auto_text = AutoText(self.my_key, self.active_names, self)

        self.page.on_keyboard_event = self.on_keyboard_event_async
        self.on_button_event_async = self.on_button_event_async
        await self.start_async_internal()
        await self.connect_async()
        self.update()

    async def connect_async(self):
        self.frontend.set_output_callback(self.output_callback)
        self.frontend.invoke_output_callbacks()
                          
    async def disconnect_async(self):
        await self.auto_text.cancel_async()
        self.frontend.discard_output_callback()

    async def on_button_event_async(self, e):
        key = e.control.key
        if key == 'settings':
            self.page.open(self.settings)
        elif key == 'clear_all_lines':
            await self.set_input_async(self.frontend.clear_all_lines(None))
        elif key == 'clear_lines':
            await self.set_input_async(self.frontend.clear_all_lines(self.my_key)) 
        else:    
            self.frontend.invoke_output_callbacks()    
        self.update()

    async def on_keyboard_event_async(self, e):
        if e.key == 'F1':
            await self.auto_text.start_async(self.settings.sample_text)
            return
        elif e.key == 'F2':
            await self.auto_text.cancel_async()
            return
        elif self.get_input() == '' and e.key == 'Backspace':
            await self.set_input_async(self.frontend.clear_line(self.my_key)) 
            self.frontend.invoke_output_callbacks()

    async def on_change_event_async(self, e):
        input_text, output_lines = self.frontend.update(self.my_key, e.control.value)
        await self.set_input_async(input_text)
        self.frontend.invoke_output_callbacks()
