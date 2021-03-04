from nenwfont.node import Node
import re


class ReplaceAttributeNode(Node):
    name = 'replace_attribute'

    def transform(self, input_fonts, options):
        patterns = options['patterns']
        keys = options.get(
            'keys',
            [] if 'key' not in options else [ options.get('key') ]
        )
        output_keys = options.get(
            'output_keys',
            keys if 'output_key' not in options else [ options['output_key'] ]
        )

        key_mapping = list(zip(keys, output_keys))

        for font in input_fonts:
            for key, output_key in key_mapping:
                if key not in font:
                    continue

                font[output_key] = font[key]

        for pattern_index, pattern_item in enumerate(patterns):
            pattern = re.compile(pattern_item['find'])
            replace = pattern_item['replace']
            count = pattern_item.get('max', 0)
            total_replaced = 0

            for font in input_fonts:
                for key, output_key in key_mapping:
                    if key not in font:
                        continue

                    new_value, replaced = re.subn(pattern, replace, font[output_key], count)
                    font[output_key] = new_value
                    total_replaced += replaced

            print("Replaced %d occurrences with pattern %d" % (total_replaced, pattern_index))

        return input_fonts
