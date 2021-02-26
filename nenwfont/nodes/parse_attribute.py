import re


class ParseAttributeNode(Node):
    name = 'parse_attribute'

    def transform(self, input_fonts, options):
        key = options['key']
        pattern = re.compile(options['pattern'])

        for font in input_fonts:
            match = pattern.search(font[key])
            if not match:
                continue

            font.attributes.update(match.groupdict())

        return input_fonts
