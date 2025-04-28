# MIT License (c) 2024, 2025 Masakazu Suzuoki, AxTecChare
# See LICENSE.txt for details.

import flet as ft
from .backend import Backend
from . import misc

import os

class FtSettingDrawer(ft.NavigationDrawer):

    def __init__(self, key, backend):
        super().__init__(position=ft.NavigationDrawerPosition.START)
        self.key = key
        self.backend = backend

        args = misc.load_args_from_file('config.txt')
        sample_text = args.get('sample_text', 'ビジネスチャット１.txt')
        self.sample_text = self.load_sample_text(sample_text)

        sample_text_options = []
        for name in self.get_sample_text_names():
            sample_text_options.append(ft.dropdown.Option(name))

        dict_options = []
        for name in backend.dict_names:
            dict_options.append(ft.dropdown.Option(name))

        dict_name = args.get('dict_name', 'wiki256_small_64_all_-5')
        attr = backend.get_attr(key)
        attr['dict_type'] = self.get_dict_type(dict_name)
        backend.set_attr(key, attr)

        max_concat_options = []
        for item in (32, 64, 96, 128):
            max_concat_options.append(ft.dropdown.Option(item))

        truncate_step_options = []
        for item in (1, 4, 8, 12, 16, 20, 24):
            truncate_step_options.append(ft.dropdown.Option(item))

        self.controls=[
            ft.Container(
                padding=8,
                content=ft.Column(
                    # expand=True,
                    controls = [
                        ft.Text("かな漢字変換の設定", weight=ft.FontWeight.BOLD),
                        ft.Divider(thickness=2),
                        ft.Dropdown(
                            options = sample_text_options,
                            value=sample_text,
                            label="デモに使用するテキストを選択",
                            on_change=self.on_select_sample_text,
                            width=290,

                        ),
                        ft.Dropdown(
                            options = dict_options,
                            value=dict_name,
                            label="辞書を選択",
                            on_change=self.on_select_dict,
                            width=290,
                        ),
                        ft.Dropdown(
                            options = max_concat_options,
                            value=64,
                            label='前方参照する文字数',
                            on_change=self.on_set_max_concat_size,
                            width=290,
                        ),
                        ft.Dropdown(
                            options = truncate_step_options,
                            value=16,
                            label='変換の遅延文字数',
                            on_change=self.on_set_truncate_step,
                            width=290,
                        ),
                    ],
                ),
            ),
        ]
            

    def shutdown(self):
        sefl.backend.remove_attr(self.key)

    def get_sample_text_names(self):
        target_dir = misc.search_path('assets/samples')
        files = os.listdir(target_dir)
        return sorted([file for file in files if file.endswith(".txt")])

    def load_sample_text(self, name):
        target_dir = misc.search_path('assets/samples')
        full_path = os.path.join(target_dir, name)
        return misc.load_string_from_file(full_path)

    def get_dict_type(self, name):
        try:
            index = self.backend.dict_names.index(name)
        except Exception:
            index = 0
        return f'T{index}:1:'    

    def on_select_sample_text(self, e):
        self.sample_text = self.load_sample_text(e.control.value)

    def on_select_dict(self, e):
        attr = self.backend.get_attr(self.key)
        attr['dict_type'] = self.get_dict_type(e.control.value)
        self.backend.set_attr(self.key, attr)

    def on_set_max_concat_size(self, e):
        attr = self.backend.get_attr(self.key)
        attr['max_concat_size'] = int(e.control.value)
        self.backend.set_attr(self.key, attr)
        self.update()


    def on_set_truncate_step(self, e):
        attr = self.backend.get_attr(self.key)
        attr['truncate_step'] = int(e.control.value)
        self.backend.set_attr(self.key, attr)
        self.update()


