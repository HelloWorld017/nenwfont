import re


class ReplaceAttributeNode(Node):
    name = 'replace_attribute'

    def transform(self, input_fonts, options):
        key = options['key']
        patterns = options['patterns']
        output_key = options.get('output_key', key)

        for pattern_item in patterns:
            pattern = re.compile(pattern_item['find'])
            replace = pattern_item['replace']
            count = pattern_item.get('max', 0)

            for font in input_fonts:
                font[output_key] = re.sub(pattern, font[key], replace, count)

        return input_fonts
