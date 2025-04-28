import MeCab
import ipadic

from .text_wrapper import TextWrapper

class Kanhira():
    def __init__(self):
        CHASEN_ARGS = r' -F "%m\t%f[7]\t%f[6]\t%F-[0,1,2,3]\t%f[4]\t%f[5]\n"'
        CHASEN_ARGS += r' -U "%m\t%m\t%m\t%F-[0,1,2,3]\t\t\n"'
        self.tagger = MeCab.Tagger(ipadic.MECAB_ARGS + CHASEN_ARGS)
        self.wrapper = TextWrapper()
        self.tagger.parse("")  # bug walkaround (windows)

    def set_pattern_and_replacement(self, pattern, replacement):
        self.wrapper.set_pattern_and_replacement(pattern, replacement)

    def set_pattern(self, pattern):
        self.wrapper.set_pattern(pattern)

    def set_replacement(self, replacement):
        self.wrapper.set_replacement(replacement)

    def convert(self, text):
        encoded_text = self.wrapper.encode(text)
        parsed = self.tagger.parse(encoded_text)
        result = []
        for line in parsed.splitlines():
            if line == "EOS":  # 終端記号
                break
            columns = line.split("\t")
            if len(columns) >= 4:
                reading = columns[1]
                hiragana = self.katakana_to_hiragana(reading)
                result.append(hiragana)
            else:
                result.append(columns[0])  # 未知語などの処理

        return self.wrapper.decode("".join(result))

    def katakana_to_hiragana(self, text):
        return text.translate(str.maketrans(
            "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲンァィゥェォャュョッヴガギグゲゴザジズゼゾダヂヅデドバビブベボパピプペポ",
            "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをんぁぃぅぇぉゃゅょっゔがぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽ"
        ))

