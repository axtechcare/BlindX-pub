from blindx.backend import BackendLine
from blindx.ft_color_spans import FtColorSpansSimple2

import flet as ft
import flet_video as ftv
import threading

class FtViewer:
    def start(self, page, on_keyboard_event, video_path):

        self.page = page
        self.lock = threading.Lock()

        self.edit_text = ft.Text(
            size=16, 
            expand=True,
        )

        self.input_listview = ft.ListView(
            auto_scroll=True,
        )

        self.output_listview = ft.ListView(
            auto_scroll=True,
        )

        title_container = ft.Container(
            content=ft.Text(
                spans=[
                    ft.TextSpan(
                        'BlindX Multimodal Speech Caption Editor\n', 
                        style=ft.TextStyle(size=28, weight=ft.FontWeight.BOLD)
                    ),
                ],
                text_align=ft.TextAlign.CENTER,
            ),
            alignment=ft.alignment.center,
            height=50,
        )

        output_container = ft.Container(
            content=self.output_listview,
            border=ft.border.all(3, ft.Colors.OUTLINE),
            border_radius=5,
            padding=5,
            expand=True,
        )

        edit_container = ft.Container(
            content=ft.Row(
                controls=[
                    self.edit_text,
                ],
                spacing=0,
            ),
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=5,
            padding=8,
        )

        right_column = ft.Column(
            controls=[
                ft.Text('かな漢字変換出力', size=16, color=ft.Colors.BLUE),
                output_container,
            ],
            expand=True 
        )

        input_container = ft.Container(
            content=self.input_listview,
            # bgcolor=ft.Colors.BLUE_50,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=5,
            padding=5,
            expand=True,
        )

        left_column = ft.Column(
            controls=[
                ft.Text('ひらがな変換出力', size=16, color=ft.Colors.RED),
                input_container,
            ],
            expand=True 
        )


        main_row = ft.Row(
            controls=[
                left_column,
                ft.Icon(ft.Icons.FORWARD, size=64),
                right_column
            ],
            expand=True
        )

        self.video = ftv.Video(
            # expand=True,
            # height=100,
            height=200,
            playlist=[
                ftv.VideoMedia(video_path)
            ],
            volume=100,
            autoplay=False,
            filter_quality=ft.FilterQuality.HIGH,
            muted=False,
            alignment=ft.alignment.center,
        )

        layout = ft.Column(
            controls=[
                self.video,
                title_container,
                main_row,
                edit_container,
            ],
            expand=True,
        )

        page.on_keyboard_event = on_keyboard_event
        page.add(
            layout
        )


    def set_edit_input(self, before, after):

        if not before and not after:
            self.edit_text.spans = [
                ft.TextSpan(
                    'ひらがなを入力してください',
                    style=ft.TextStyle(
                        color='grey',
                    )
                )
            ]
            ft.TextSpan(after),
            self.edit_text.update()  
            return

        box_len = int(self.page.width / 16) - 10 # heyristic
        before_len = len(before)
        after_len = len(after)
        excess_len = before_len + after_len - box_len
        if excess_len > 0:
            after_len = min(after_len, int(excess_len/2))
            before_len = min(before_len, box_len - after_len)
            after = after[:box_len - before_len]
            before = before[-before_len:]

        self.edit_text.spans = [
            ft.TextSpan(before),
            ft.TextSpan(
                '|',
                style=ft.TextStyle(
                    color='blue',
                    letter_spacing=-2,
                    weight='bold'
                ),
            ),  # 縦棒
            ft.TextSpan(after),
        ]
        self.edit_text.update()  

    def set_input(self, lines, lineno):
        with self.lock:

            self.input_listview.controls.clear()

            for current_lineno, line in enumerate(lines):
                if line.key == None:
                    continue

                # input_text = line.input_text + line.postfix()
                input_text = line.input_text
                input_text = input_text.rstrip()

                prev_input_text = line.input_text
                if hasattr(line, 'prev_input_text'):
                    prev_input_text = line.prev_input_text
                    # print(f'prev_input_text={prev_input_text} : input_text={input_text}')

                prev_input_text = prev_input_text.rstrip()
                # input_spans = FtColorSpansSimple2(input_text, prev_input_text)
                input_spans = [ft.TextSpan(input_text)]

                bgcolor = ft.Colors.BLUE_50 if lineno == current_lineno else None

                ft_container = ft.Container(
                    content=ft.Text(spans=input_spans, size=16),
                    expand=True,
                    bgcolor=bgcolor
                )
                self.input_listview.controls.append(ft_container)

            self.input_listview.update() 

    def set_output(self, lines, lineno):
        with self.lock:
            self.output_listview.controls.clear()
            for current_lineno, line in enumerate(lines):
                if line.key == None:
                    continue

                output_text = line.output_text + line.postfix()
                output_text = output_text.rstrip().replace('`', '')

                prev_output_text = line.prev_output_text
                prev_output_text = prev_output_text.rstrip()

                output_spans = FtColorSpansSimple2(output_text, prev_output_text)
                bgcolor = ft.Colors.BLUE_50 if lineno == current_lineno else None

                ft_container = ft.Container(
                    content=ft.Text(spans=output_spans, size=16),
                    expand=True,
                    bgcolor=bgcolor
                )
                self.output_listview.controls.append(ft_container)

            self.output_listview.update() 

if __name__ == "__main__":

    def main(page):
        viewer = FtViewer()
        viewer.start(page)

        viewer.set_input('Hello world')

        lines = [BackendLine()] * 4
        lines[0].output_text = 'Hello world'
        lines[1].output_text = 'Hello world'
        lines[2].output_text = 'Hello world'
        lines[3].output_text = 'Hello world'

        viewer.set_output(lines, 1)
        page.update()
    ft.app(target=main)
