# MIT License (c) 2024, 2025 Masakazu Suzuoki, AxTecChare
# See LICENSE.txt for details.

from blindx.ft_app_base import FtAppBase
from blindx.ft_color_spans import FtColorSpans
from blindx.ft_color_spans import FtColorSpansSimple

import mozcpy
import threading
import flet as ft

class FtApp(FtAppBase):

    async def start_async_internal(self):

        self.mozc = mozcpy.Converter()
        self.is_compare = False
        self.is_color_span = False
        self.lock = threading.Lock()

        top_contaner = ft.Container(
            content=ft.Text(
                'BlindX Compare', 
                size=35,
                weight=ft.FontWeight.BOLD
            ),
            alignment=ft.alignment.center,
            height=120,
        )

        self.input_text = ft.TextField(
            label=self.my_key,
            hint_text='メッセージを入力してください',
            hint_style=ft.TextStyle(italic=True, size=14),
            helper_text='改行で変換されます。バックスペースでいつでも戻れます。 F2 でデモをキャンセルできます',

            multiline=True,
            autofocus=True,
            height=120,
            text_size=20,
            on_change = self.on_change_event_async
        )

        self.output_text = ft.Text(
            width=2048, # magic number
            size=20,
        )

        output_title_container = ft.Container(
            content=ft.Text(
                '変換結果はここに表示されます。比較対象は mozcpy を使用しています', 
                weight=ft.FontWeight.BOLD
            ),
            alignment=ft.alignment.center_left,
        )

        output_text_column = ft.Column(
            controls=[self.output_text],
            scroll="auto", 
            auto_scroll=True,
            expand=True,
        )
        output_text_container = ft.Container(
            content=output_text_column,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=5,
            expand=True,
            padding=10,
        )

        bottom_row = ft.Row(
            [
                ft.Switch(
                    label="比較する", 
                    key='compare', 
                    on_change=self.on_compare_event_async),
                ft.Switch(
                    label="カラー表示", 
                    key='color_span', 
                    value=False, 
                    on_change=self.on_color_span_event_async),
                ft.OutlinedButton(
                    text="自分の投稿を削除", 
                    key='clear_lines', 
                    on_click = self.on_button_event_async),
                ft.OutlinedButton(
                    text="全削除", 
                    key='clear_all_lines', 
                    on_click = self.on_button_event_async),
                ft.IconButton(
                    icon=ft.Icons.SETTINGS,
                    tooltip="詳細設定",
                    key='settings', 
                    on_click = self.on_button_event_async,
                ),
            ],
            wrap=True,
            alignment=ft.MainAxisAlignment.END,
        )
        self.page.horizontal_alignment = ft.CrossAxisAlignment.END
        self.page.add(
            top_contaner,
            self.input_text,
            output_title_container,
            output_text_container,
            bottom_row,
        )

    def update(self):
        self.page.update()
        self.input_text.focus()

    def get_input(self):
        return self.input_text.value

    async def set_input_async(self, text):
        self.input_text.value = text
        self.input_text.update()

    def set_output(self, lines):

        ends_with_return = False
        with self.lock:
            spans=[]
            current_name = None
            for line in lines:
                if line.key == None:
                    continue

                ends_with_return = line.input_text.endswith('\n')

                if current_name != line.key:
                    current_name = line.key
                    spans.append(self.get_greeting_span(current_name, not spans))
                    
                if line.long_output_text == line.output_text and line.input_text == line.stage_input_text:
                    spans += self.get_output_spans_with_compare(line)
                else:
                    spans += FtColorSpans(
                        line.output_text, line.prev_output_text, line.postfix(), self.is_color_span)
            self.output_text.spans = spans

        self.output_text.update()    
            
    def get_greeting_span(self, current_name, is_first):
        return ft.TextSpan(
            f'\n{current_name} さんが参加しました\n',
            style=ft.TextStyle(italic=True, size=14))

    def get_output_spans_with_compare(self, line):
        guide_style = ft.TextStyle(
            size=18, 
            bgcolor=ft.Colors.GREEN_300, 
            color=ft.Colors.WHITE)

        spans=[]
        output_text = line.output_text
        spans.append(ft.TextSpan('BlindX', guide_style))
        spans.append(ft.TextSpan(' '));
        spans.append(ft.TextSpan(output_text))

        if spans and self.is_compare:
            input_text = line.input_text.replace('\n', '\\n')
            mozc_text = self.mozc.convert(input_text).replace('\\n', '\n') + '\n'

            if set(mozc_text) != '\n':
                spans.append(ft.TextSpan('Mozc    ', guide_style))
                spans.append(ft.TextSpan(' '));
                spans += FtColorSpansSimple(mozc_text, output_text)

        return spans        

    async def on_color_span_event_async(self, e):
        self.is_color_span = e.control.value

    async def on_compare_event_async(self, e):
        self.is_compare = True if e.control.value else False
        await self.on_button_event_async(e)    

