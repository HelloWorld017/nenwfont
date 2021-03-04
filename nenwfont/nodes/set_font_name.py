from nenwfont.node import Node

class SetFontNameNode(Node):
    name = 'set_font_name'
    updates_fonts = True

    def transform(self, input_fonts, options):
        table_mapping = {
            1: 'family_name',
            2: 'subfamily_name',
            3: 'unique_identifier',
            4: 'full_name',
            5: 'version',
            6: 'postscript_name',
            16: 'typographic_family_name',
            17: 'typographic_subfamily_name'
        }

        attributes = options.get('attributes', table_mapping.values())
        enabled_mapping = {
            key: value
            for key, value in table_mapping.items()
            if value in attributes
        }

        for font_item in input_fonts:
            font = font_item.font
            table = font['name']

            for record in table.names:
                if record.nameID not in enabled_mapping:
                    continue

                key = enabled_mapping[record.nameID]
                if key not in font:
                    continue

                record.string = font[key]

        return input_fonts
