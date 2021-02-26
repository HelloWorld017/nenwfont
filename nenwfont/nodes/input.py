from fontTools.ttLib import TTFont
from glob import glob
from nenwfont.font import Font
from nenwfont.node import Node

class InputNode(Node):
    name = 'input'
    updates_fonts = True

    def transform(self, input_fonts, options):
        glob_patterns = options['glob']

        if isinstance(glob_patterns, str):
            glob_patterns = [ glob_patterns ]

        for glob_pattern in glob_patterns:
            for path in glob(glob_pattern):
                input_fonts.append(Font(path, TTFont(path)))

        return input_fonts
