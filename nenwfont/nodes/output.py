from fontTools.ttLib import sfnt
from nenwfont.node import Node


class OutputNode(Node):
    name = 'output'
    updates_fonts = False

    def transform(self, input_fonts, options):
        output_fonts = options['output_fonts']
        output_css = options['output_css']
        output_preview = options.get('output_preview', None)
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

            self.add_css_rules(font, stylesheet, [
                ('weight', 'font-weight'),
                ('unicode_range', 'unicode-range')
                ('style', 'font-style'),
                ('display', 'font-display'),
                ('stretch', 'font-stretch'),
                ('variant', 'font-variant')
                ('feature_settings', 'font-feature-settings'),
                ('variation_settings', 'font-variation-settings'),
            ])

            for extension in extensions:
                output_dest = output_fonts.format(**font.attributes, ext=extension)
                relative_dest = os.path.relpath(output_css, output_dest)

                self.output_table[extension](output_dest, relative_dest, font, stylesheet)
            
            stylesheets.append(stylesheet)
        
        output_css(output_css, stylesheets)
        
        if output_preview:
            self.make_preview(output_preview, input_fonts, stylesheets)

    def make_preview(self, path, fonts, stylesheets):
        pass

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
        return string
            .replace("\\", "\\\\")
            .replace('"', '\\"')
        
    def output_css(self, path, stylesheets):
        stylesheet_text = ''
        
        for stylesheet in stylesheets:
            stylesheet_text += \
                '@font-face{' + \
                    'font-family:"%s";' % stylesheet['font-family'] + \
                    'src:%s;' % stylesheet['src'].join(',')
            
            del stylesheet['font-family']
            del stylesheet['src']
            
            for property_key, property_value in stylesheet:
                stylesheet_text += '%s:%s;' % (property_key, property_value)
            
            stylesheet_text += '}'
        
        with open(path, 'w', encoding='utf-8') as cssfile:
            cssfile.write(stylesheet_text)
        
