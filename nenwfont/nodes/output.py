from datetime import datetime
from fontTools.ttLib import sfnt
from nenwfont.node import Node
import json
import os
import posixpath


class OutputNode(Node):
    name = 'output'
    updates_fonts = False

    def transform(self, input_fonts, options):
        output_fonts = options['output_fonts']
        output_css = options['output_css']
        output_preview = options.get('output_preview', None)
        with_zopfli = options.get('with_zopfli', True)
        extensions = options.get('extensions', [ 'woff2', 'woff' ])
        family_key = options.get('family_key', 'family_name')

        if with_zopfli:
            sfnt.USE_ZOPFLI = True

        stylesheets = []

        for font in input_fonts:
            print("Exporting %s..." % font['file_name'])

            stylesheet = {
                'font-family': font[family_key],
                'src': []
            }

            self.add_css_rules(font, stylesheet, [
                ('weight', 'font-weight'),
                ('unicode_range', 'unicode-range'),
                ('style', 'font-style'),
                ('display', 'font-display'),
                ('stretch', 'font-stretch'),
                ('variant', 'font-variant'),
                ('feature_settings', 'font-feature-settings'),
                ('variation_settings', 'font-variation-settings')
            ])

            for extension in extensions:
                output_dest = output_fonts.format(
                    **font.attributes,
                    ext=extension,
                    root=os.path.splitext(font['file_name'])[0]
                )

                relative_dest = posixpath.relpath(output_dest, os.path.dirname(output_css))
                self.output_table[extension](output_dest, relative_dest, font.font, stylesheet)

            stylesheets.append(stylesheet)

        print("Exporting stylesheets...")
        self.output_css(output_css, stylesheets)

        if output_preview:
            print("Exporting preview...")
            self.make_preview(output_preview, output_css, input_fonts)

        return input_fonts

    def make_preview(self, path, stylesheet_path, fonts):
        with open("./assets/preview.template.html", encoding="utf-8") as f:
            template = f.read()

        font_items = set([
            (font.attributes.get('family_name'), font.attributes.get('full_name'), font.attributes.get('weight', 400))
            for font in fonts
        ])

        replace_map = {
            'title': "Generated at %s" % datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'stylesheet': posixpath.relpath(stylesheet_path, os.path.dirname(path)),
            'fonts': json.dumps([
                {
                    'familyName': family_name,
                    'name': full_name,
                    'style': "font-family:%s;font-weight:%s;" % (family_name, weight)
                }
                for (family_name, full_name, weight) in font_items
            ])
        }

        for key, value in replace_map.items():
            template = template.replace('((%s))' % key, value)

        with open(path, 'w', encoding="utf-8") as f:
            f.write(template)

    def output_woff2(self, path, relative_path, font, stylesheet):
        font.flavor = 'woff2'
        font.save(path)

        stylesheet['src'].append('url("%s") format("woff2")' % self.escape_css(relative_path))

    def output_woff(self, path, relative_path, font, stylesheet):
        font.flavor = 'woff'
        font.save(path)

        stylesheet['src'].append('url("%s") format("woff")' % self.escape_css(relative_path))

    def output_ttf(self, path, relative_path, font, stylesheet):
        font.flavor = None
        font.save(path)

        stylesheet['src'].append('url("%s") format("truetype")' % self.escape_css(relative_path))

    @property
    def output_table(self):
        return {
            'woff2': self.output_woff2,
            'woff': self.output_woff,
            'ttf': self.output_ttf
        }

    def add_css_rules(self, font, stylesheet, rules):
        for [ key, css_key ] in rules:
            if key in font and font[key]:
                stylesheet[css_key] = font[key]

    def escape_css(self, string):
        return string \
            .replace("\\", "\\\\") \
            .replace('"', '\\"')

    def output_css(self, path, stylesheets):
        stylesheet_text = ''

        for stylesheet in stylesheets:
            stylesheet_text += \
                '@font-face{' + \
                    'font-family:"%s";' % stylesheet['font-family'] + \
                    'src:%s;' % ','.join(stylesheet['src'])

            del stylesheet['font-family']
            del stylesheet['src']

            for property_key, property_value in stylesheet.items():
                stylesheet_text += '%s:%s;' % (property_key, property_value)

            stylesheet_text += '}'

        with open(path, 'w', encoding='utf-8') as cssfile:
            cssfile.write(stylesheet_text)
