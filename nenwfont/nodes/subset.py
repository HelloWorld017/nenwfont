from collections import Counter
from fontTools.subset import Subsetter
from fontTools.ttLib import TTFont
from functools import cmp_to_key, lru_cache
from nenwfont.node import Node
from os import path
import json
import re

def group_ideograph_frequency(options):
    with open("./assets/unihan/kFrequency.json", "r", encoding="utf-8") as file:
        k_frequency = json.load(file)

    def ideograph_frequency(char):
        if char in k_frequency:
            return k_frequency[char] - 1

        return None

    return ideograph_frequency


def group_ideograph_strokes(options):
    with open("./assets/unihan/kTotalStrokes.json", "r", encoding="utf-8") as file:
        k_total_strokes = json.load(file)

    def ideograph_strokes(char):
        if char in k_total_strokes and len(k_total_strokes[char]) > 0:
            return min(k_total_strokes[char]) - 1

        return None

    return ideograph_strokes


def group_ideograph_jouyou(options):
    with open("./assets/unihan/kJoyoKanji.json", "r", encoding="utf-8") as file:
        k_joyo_kanji = json.load(file)

    def ideograph_jouyou(char):
        if char in k_joyo_kanji:
            return 0

        return None

    return ideograph_jouyou


def group_hangul_2350(options):
    with open("./assets/ksx1001.txt", "r", encoding="utf-8") as file:
        ksx1001 = file.read().strip()

    def hangul_2350(char):
        if char in ksx1001:
            return 0

        if 0xAC00 <= ord(char) <= 0xD7A3:
            return 1

        return None

    return hangul_2350


def group_hangul_2574(options):
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


def group_unicode_blocks(options):
    blocks_pattern = re.compile(r"^([0-9A-F]+)..([0-9A-F]+);\s*(.*)$", re.M)
    excluded = options.get('exclude', [])
    included = options.get('include', None)

    with open("./assets/blocks.txt", "r", encoding="utf-8") as file:
        blocks_raw = file.read()

    all_blocks = [
        {
            'start': int(match.group(1), 16),
            'end': int(match.group(2), 16),
            'name': match.group(3),
            'index': index
        }

        for index, match in enumerate(blocks_pattern.finditer(blocks_raw))
    ]

    if included is not None:
        enabled_blocks = [
            block for block in all_blocks if block['name'] in included
        ]

    else:
        enabled_blocks = [
            block for block in all_blocks if block['name'] not in excluded
        ]

    def unicode_blocks(char):
        char_point = ord(char)
        for block in enabled_blocks:
            if block['start'] <= char_point <= block['end']:
                return block['index']

        return None

    return unicode_blocks


def group_unicode_range(options):
    range_pattern = re.compile(r"^U+([0-9A-F]+)-([0-9A-F]+)$")
    ranges = options.get('ranges', [ options.get('range') ])

    ranges_parsed = [
        {
            'start': int(match.group(1), 16),
            'end': int(match.group(2), 16),
            'index': index
        }

        for index, match in enumerate([
            match for range in ranges for match in range_pattern.finditer(range)
        ])
    ]

    def unicode_range(char):
        char_point = ord(char)
        for range in ranges_parsed:
            if range['start'] <= char_point <= range['end']:
                return range['index']

        return None

    return unicode_range


def group_file(options):
    filename = options['filename']
    with open(filename, 'r', encoding='utf-8') as file:
        group_content = file.read()

    def generic(char):
        if char in group_content:
            return 0

        return None

    return generic


def group_all(options):
    def all(char):
        return 0

    return all


def get_group(group_key, group_args):
    groups = {
        'ideograph_frequency': group_ideograph_frequency,
        'ideograph_strokes': group_ideograph_strokes,
        'ideograph_jouyou': group_ideograph_jouyou,
        'hangul_2350': group_hangul_2350,
        'hangul_2574': group_hangul_2574,
        'unicode_blocks': group_unicode_blocks,
        'file': group_file
    }

    if group_key in groups:
        return groups[group_key](group_args)

    return group_all(group_args)


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


@lru_cache()
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
                ranges.append('U+%X-%X' % (range_start, range_end))

            range_start = code_point
            range_end = code_point
        else:
            range_end += 1

    return ','.join(ranges)


class SubsetNode(Node):
    name = 'subset'
    updates_fonts = True

    def transform(self, input_fonts, options):
        group_by_args = options.get('group_by', [ 'all' ])
        default_order = options.get('order_by', 'default')
        min_chunk_size = options.get('min_chunk_size', 8)
        max_chunk_size = options.get('max_chunk_size', 256)

        group_by = []
        for group in group_by_args:
            is_dict = isinstance(group, dict)
            group_name = group['name'] if is_dict else group
            group_args = group if is_dict else {}
            group_fn = get_group(group_name, group_args)
            group_order = group_args.get('order_by', default_order)
            group_by.append({
                'name': group_name,
                'args': group_args,
                'order': get_order(group_order),
                'function': group_fn
            })

        output_fonts = []

        for font in input_fonts:
            groups = {}

            for char_code, glyph_name in font.font['cmap'].getBestCmap().items():
                char = chr(char_code)

                for group_index, group in enumerate(group_by):
                    inner_index = group['function'](char)
                    if inner_index is None:
                        continue

                    if group['args'].get('merge_blocks', False):
                        inner_index = 0

                    group_key = (group_index, inner_index)
                    if group_key not in groups:
                        groups[group_key] = []

                    groups[group_key].append(char)
                    break

            for group_key, group_chars in list(groups.items()):
                if len(group_chars) >= group['args'].get('min_chunk_size', min_chunk_size):
                    continue

                del groups[group_key]

                if ('merged_chunks', 0) not in groups:
                    groups[('merged_chunks', 0)] = []

                groups[('merged_chunks', 0)].extend(group_chars)

            for (group_index, inner_index), group_chars in list(groups.items()):
                group = group_by[group_index]
                group_chars.sort(key=group['order'])

                i = 0
                group_max_chunk_size = group['args'].get('max_chunk_size', max_chunk_size)
                while len(group_chars) > group_max_chunk_size:
                    groups[(group_index, inner_index, i)] = group_chars[:group_max_chunk_size]
                    i += 1

                    del group_chars[:group_max_chunk_size]

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
