from fontTools import ttLib
from functools import reduce
from nenwfont.font import Font
from nenwfont.node import Node

class CustomMerger(Merger):
    def merge(self, font_items):
        mega = ttLib.TTFont()

        # Settle on a mega glyph order.
        fonts = [ font.font for font_item in font_items ]
        glyphOrders = [ font.getGlyphOrder() for font in fonts ]
        megaGlyphOrder = self._mergeGlyphOrders(glyphOrders)

        # Reload fonts
        fonts = [ font_item.clone().font for font_item in font_items ]

        for font, glyphOrder in zip(fonts, glyphOrders):
            font.setGlyphOrder(glyphOrder)

        mega.setGlyphOrder(megaGlyphOrder)

        for font in fonts:
            self._preMerge(font)

        self.fonts = fonts
        self.duplicateGlyphsPerFont = [ {} for _ in fonts ]

        allTags = reduce(set.union, (list(font.keys()) for font in fonts), set())
        allTags.remove('GlyphOrder')

        # Make sure we process cmap before GSUB as we have a dependency there.
        if 'GSUB' in allTags:
            allTags.remove('GSUB')
            allTags = ['GSUB'] + list(allTags)

        if 'cmap' in allTags:
            allTags.remove('cmap')
            allTags = ['cmap'] + list(allTags)

        for tag in allTags:
            tables = [font.get(tag, NotImplemented) for font in fonts]

            print("Merging '%s'.", tag)
            clazz = ttLib.getTableClass(tag)
            table = clazz(tag).merge(self, tables)
                if table is not NotImplemented and table is not False:
                    mega[tag] = table
                    print("Merged '%s'." % tag)

                else:
                    print("Dropped '%s'." % tag)

        del self.duplicateGlyphsPerFont
        del self.fonts

        self._postMerge(mega)

        return mega


def read_line_metrics(font):
    metrics = {
        "ascent": font["hhea"].ascent,
        "descent": font["hhea"].descent,
        "usWinAscent": font["OS/2"].usWinAscent,
        "usWinDescent": font["OS/2"].usWinDescent,
        "sTypoAscender": font["OS/2"].sTypoAscender,
        "sTypoDescender": font["OS/2"].sTypoDescender,
        "sxHeight": font["OS/2"].sxHeight,
        "sCapHeight": font["OS/2"].sCapHeight,
        "sTypoLineGap": font["OS/2"].sTypoLineGap,
    }
    return metrics


def set_line_metrics(font, metrics):
    font["hhea"].ascent = metrics["ascent"]
    font["hhea"].descent = metrics["descent"]
    font["OS/2"].usWinAscent = metrics["usWinAscent"]
    font["OS/2"].usWinDescent = metrics["usWinDescent"]
    font["OS/2"].sTypoAscender = metrics["sTypoAscender"]
    font["OS/2"].sTypoDescender = metrics["sTypoDescender"]
    font["OS/2"].sxHeight = metrics["sxHeight"]
    font["OS/2"].sCapHeight = metrics["sCapHeight"]


class MergeNode(Node):
    name = 'merge'
    updates_fonts = True

    def transform(self, input_fonts, options):
        merge_by = options.get('merge_by', 'group')
        merge_base = options.get('merge_base', None)
        output_template = options.get('output_template', '{group}.ttf')
        line_metrics = options.get('line_metrics', 'override')

        merge_groups = {}
        for input_font in input_fonts:
            group_name = input_font[merge_by]

            if group_name not in merge_groups:
                merge_groups[group_name] = []

            merge_groups[group_name].append(input_font)

        output_fonts = []
        for fonts in merge_groups:
            if isinstance(merge_base, dict):
                pattern = re.compile(merge_base['match'])

                for index, font in enumerate(fonts):
                    if pattern.match(font[merge_base['key']]) is not None:
                        fonts.insert(0, fonts.pop(index))
                        break

            base_font = fonts[0]
            base_metrics = read_line_metrics(base_font)
            print("Merging %d fonts with base %s" % (len(fonts), base_font['file_name']))

            merger = CustomMerger()
            output_ttfont = merger.merge(fonts)
            output_path = output_template.format(**base_font.attributes)

            if line_metrics == 'override':
                set_line_metrics(output_ttfont, base_metrics)

            output_font = Font(output_ttfont, output_path)
            output_font.attributes = base_font.attributes.copy()
            output_fonts.append(output_font)

        return output_fonts
