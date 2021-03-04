from nenwfont.node import Node
import re


class SetAttributeNode(Node):
    name = 'set_attribute'

    def transform(self, input_fonts, options):
        attributes = options['attributes']
        template = options.get('template', True)

        for font in input_fonts:
            for attribute_key, attribute_value in attributes.items():
                if template:
                    font[attribute_key] = attribute_value.format(**font.attributes)

                else:
                    font[attribute_key] = attribute_value

        return input_fonts
