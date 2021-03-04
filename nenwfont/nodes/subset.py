from collections import Counter
from fontTools.subset import Subsetter
from fontTools.ttLib import TTFont
from functools import cmp_to_key
from nenwfont.node import Node
from os import path
import json
import re

def group_ideograph_frequency():
    with open("./assets/unihan/kFrequency.json", "r", encoding="utf-8") as file:
        k_frequency = json.load(file)

    def ideograph_frequency(char):
        if char in k_frequency:
            return k_frequency[char] - 1

        return None

    return ideograph_frequency


def group_ideograph_strokes():
    with open("./assets/unihan/kTotalStrokes.json", "r", encoding="utf-8") as file:
        k_total_strokes = json.load(file)

    def ideograph_strokes(char):
        if char in k_total_strokes and len(k_total_strokes[char]) > 0:
            return min(k_total_strokes[char]) - 1

        return None

    return ideograph_strokes


def group_ideograph_jouyou():
    with open("./assets/unihan/kJoyoKanji.json", "r", encoding="utf-8") as file:
        k_joyo_kanji = json.load(file)

    def ideograph_jouyou(char):
        if char in k_joyo_kanji:
            return 0

        return None

    return ideograph_jouyou


def group_hangul_2350():
    with open("./assets/ksx1001.txt", "r", encoding="utf-8") as file:
        ksx1001 = file.read().strip()

    def hangul_2350(char):
        if char in ksx1001:
            return 0

        if 0xAC00 <= ord(char) <= 0xD7A3:
            return 1

        return None

    return hangul_2350


def group_hangul_2574():
    with open("./assets/ksx1001.txt", "r", encoding="utf-8") as file:
        ksx1001 = file.read().strip()

    with open("./assets/hangul-additional-224.txt", "r", encoding="utf-8") as file:
        additional_224 = file.read().strip()

    def hangul_2574(char):
        if char in ksx1001 or char in additional_224:
            return 0

        if 0xAC00 <= ord(char) <= 0xD7A3:
            return 1

        return None

    return hangul_2574


def group_unicode_blocks(block=None):
    blocks_pattern = re.compile(r"^([0-9A-F]+)..([0-9A-F]+);\s*(.*)$", re.M)

    with open("./assets/blocks.txt", "r", encoding="utf-8") as file:
        blocks_raw = file.read()

    blocks = [
        {
            'start': int(match.group(1), 16),
            'end': int(match.group(2), 16),
            'index': index
        }

        for index, match in enumerate(blocks_pattern.finditer(blocks_raw))
    ]

    def unicode_blocks(char):
        char_point = ord(char)
        for block in blocks:
            if block['start'] <= char_point <= block['end']:
                return block['index']

        return len(blocks)

    return unicode_blocks


def group_all():
    def all(char):
        return 0

    return all


def group_generic(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        group_content = file.read()

    def generic(char):
        if char in group_content:
            return 0

        return None

    return generic


def get_group(group_name):
    groups = {
        'ideograph_frequency': group_ideograph_frequency,
        'ideograph_strokes': group_ideograph_strokes,
        'ideograph_jouyou': group_ideograph_jouyou,
        'hangul_2350': group_hangul_2350,
        'hangul_2574': group_hangul_2574,
        'unicode_blocks': group_unicode_blocks,
        'all': group_all
    }

    group_key, group_arg = group_name.split(':')

    if group_key in groups:
        if group_arg:
            return groups[group_key](group_arg)

        return groups[group_key]()

    return group_generic(group_name)


def order_wikipedia_frequency():
    freq_pattern = re.compile(r"^'.*?'\t(\d+)\t(\d+)$", re.M)

    with open("./assets/wikipedia_frequency.txt", 'r', encoding='utf-8') as file:
        freq_raw = file.read()

        frequency = {
            chr(int(match.group(1))): int(match.group(2))
            for index, match in enumerate(freq_pattern.finditer(freq_raw))
        }

    def wikipedia_frequency(char):
        return frequency[char] if char in frequency else 0

    return wikipedia_frequency


def order_default():
    def default(char):
        return char


def order_generic(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        order_content = file.read()

    letter_counter = Counter(order_content)

    def generic(char1, char2):
        if char1 not in letter_counter:
            return 1

        if char2 not in letter_counter:
            return -1

        return letter_counter[char2] - letter_counter[char1]

    return cmp_to_key(generic)


def get_order(order_name):
    orders = {
        'wikipedia_frequency': order_wikipedia_frequency,
        'default': order_default
    }

    if order_name in orders:
        return orders[order_name]()

    return order_generic(order_name)


def build_unicode_range(chars):
    ranges = []
    range_start = ord(chars[0])
    range_end = range_start

    for index in range(1, len(chars) + 1):
        code_point = ord(chars[index]) if index < len(chars) else -1

        if code_point != range_end + 1:
            if range_start == range_end:
                ranges.append('U+%X' % range_start)

            else:
                ranges.append('U+%x-%x' % (range_start, range_end))

            range_start = code_point
            range_end = code_point
        else:
            range_end += 1

    return ','.join(ranges)


class SubsetNode(Node):
    name = 'subset'
    updates_fonts = True

    def transform(self, input_fonts, options):
        group_by = options.get('group_by', [ 'all' ])
        order_by = options.get('order_by', 'default')
        min_chunk_size = options.get('min_chunk_size', 8)
        max_chunk_size = options.get('max_chunk_size', 256)

        if not isinstance(order_by, dict):
            default_order = order_by
            order_by = { group_name: default_order for group_name in group_by }
            order_by['merged_chunks'] = default_order

        group_by = { group_name: get_group(group_name) for group_name in group_by }
        orders = { order_key: get_order(order_key) for order_key in set(order_by.values()) }
        order_by = { group_name: orders[order_key] for group_name, order_key in order_by.items() }
        output_fonts = []

        for font in input_fonts:
            groups = {}

            for char_code, glyph_name in font.font['cmap'].getBestCmap().items():
                char = chr(char_code)

                for group_name, group in group_by.items():
                    inner_index = group(char)
                    if inner_index is None:
                        continue

                    group_key = (group_name, inner_index)
                    if group_key not in groups:
                        groups[group_key] = []

                    groups[group_key].append(char)
                    break

            for group_key, group_chars in list(groups.items()):
                if len(group_chars) >= min_chunk_size:
                    continue

                del groups[group_key]

                if ('merged_chunks', 0) not in groups:
                    groups[('merged_chunks', 0)] = []

                groups[('merged_chunks', 0)].extend(group_chars)

            for (group_name, inner_index), group_chars in list(groups.items()):
                group_chars.sort(key=order_by[group_name])

                i = 0
                while len(group_chars) > max_chunk_size:
                    groups[(group_name, inner_index, i)] = group_chars[:max_chunk_size]
                    i += 1

                    del group_chars[:max_chunk_size]

            basename = path.basename(font['path'])
            dirname = path.dirname(font['path'])
            filename, extname = path.splitext(basename)

            cloned_font = font.clone()
            font.font.close()
            cloned_font.font.close()

            for index, chars in enumerate(groups.values()):
                text = ''.join(chars)
                target_font = font.clone(TTFont(cloned_font['cloned_path']))

                print("Subsetting %s: Chunk %d" % (font['file_name'], index))
                subsetter = Subsetter()
                subsetter.populate(text=text)
                subsetter.subset(target_font.font)

                target_font['original_path'] = target_font['path']
                target_font['original_file_name'] = target_font['file_name']
                target_font['unicode_range'] = build_unicode_range(list(sorted(chars)))
                target_font['group_index'] = str(index)
                target_font['path'] = "%s/%s-%d%s" % (dirname, filename, index, extname)
                target_font['file_name'] = "%s-%d%s" % (filename, index, extname)
                output_fonts.append(target_font)

        return output_fonts
