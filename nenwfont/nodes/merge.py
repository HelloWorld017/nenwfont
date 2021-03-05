from fontTools import ttLib
from functools import reduce
from fontTools.merge import Merger
from nenwfont.font import Font
from nenwfont.node import Node
import os
import re

class CustomMerger(Merger):
    def merge(self, font_items):
        mega = ttLib.TTFont()
        cloned_font_items = [ font_item.clone() for font_item in font_items ]

        for font_item in font_items:
            font_item.font.close()

        # Settle on a mega glyph order.
        fonts = [ cloned_font_item.font for cloned_font_item in cloned_font_items ]
        glyphOrders = [ font.getGlyphOrder() for font in fonts ]
        megaGlyphOrder = self._mergeGlyphOrders(glyphOrders)

        for font in fonts:
            font.close()

        # Reload fonts
        fonts = [ ttLib.TTFont(font_item['cloned_path']) for font_item in cloned_font_items ]
        font_files = [ font_item['file_name'] for font_item in cloned_font_items ]

        for font, glyphOrder, filename in zip(fonts, glyphOrders, font_files):
            if "CFF " in font:
                print()
                print("Warning! Merging CFF fonts are not supported!")
                print("Please use cff_to_glyf node to transform CFF fonts to Glyf fonts")
                print("Font: %s" % filename)
                print("Tables: %s" % ', '.join(font.keys()))
                print()

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

            clazz = ttLib.getTableClass(tag)
            table = clazz(tag).merge(self, tables)
            if table is not NotImplemented and table is not False:
                mega[tag] = table

            else:
                print("Dropped '%s'." % tag)

        del self.duplicateGlyphsPerFont
        del self.fonts

        self._postMerge(mega)

        for font in fonts:
            font.close()

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
        for fonts in merge_groups.values():
            if isinstance(merge_base, dict):
                pattern = re.compile(merge_base['match'])

                for index, font in enumerate(fonts):
                    if pattern.match(font[merge_base['key']]) is not None:
                        print("Found base: %s" % font['file_name'])
                        fonts.insert(0, fonts.pop(index))
                        break

            base_font = fonts[0]
            base_metrics = read_line_metrics(base_font.font)
            print("Merging %d fonts with base %s" % (len(fonts), base_font['file_name']))

            merger = CustomMerger()
            output_ttfont = merger.merge(fonts)
            output_filename = output_template.format(**base_font.attributes)
            output_path = "%s/%s" % (os.path.dirname(base_font['path']), output_filename)

            if line_metrics == 'override':
                set_line_metrics(output_ttfont, base_metrics)

            output_font = Font(self.program, output_path, output_ttfont)
            output_font.attributes = base_font.attributes.copy()
            output_font['file_name'] = output_filename
            output_font['path'] = output_path
            output_fonts.append(output_font)

        return output_fonts
