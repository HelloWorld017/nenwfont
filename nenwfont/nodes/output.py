from fontTools.ttLib import sfnt
from nenwfont.node import Node


class OutputNode(Node):
    name = 'output'
    updates_fonts = False

    def transform(self, input_fonts, options):
        output_fonts = options['output_fonts']
        output_css = options['output_css']
        make_preview = options.get('make_preview', True)
        with_zopfli = options.get('with_zopfli', True)
        extensions = options.get('extensions', [ 'woff', 'woff2' ])

        if with_zopfli:
            sfnt.USE_ZOPFLI = True

        stylesheets = []

        for font in input_fonts:
            stylesheet = {
                'font-family': font['family_name'],
                'src': []
            }

            if 'weight' in font and font['weight']:
                stylesheet['font-weight'] = font['weight']

            if 'unicode_range' in font and font['unicode_range']:
                stylesheet['unicode-range'] = font['unicode_range']

            for extension in extensions:
                output_dest = output_fonts.format(**font.attributes, ext=extension)
                relative_dest = os.path.relpath(output_css, output_dest)

                self.output_table[extension](output_dest, font, stylesheet)

    def make_preview(self):
        pass

    def output_woff2(self, path, relative_path, font):
        font.flavor = 'woff2'

        pass

    def output_woff(self, path, relative_path, font):
        pass

    def output_ttf(self, path, relative_path, font):
        pass

    @property
    def output_table(self):
        return {
            'woff2': self.output_woff2,
            'woff': self.output_woff,
            'ttf': self.output_ttf
        }
