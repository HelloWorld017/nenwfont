from fontTools.ttLib import newTable
from nenwfont.node import Node
from os import path


class AddGaspNode(Node):
    name = 'add_gasp'
    updates_fonts = True

    def transform(self, input_fonts, options):
        mode = options.get('mode', 'add')

        for font in input_fonts:
            gasp_table = newTable('gasp')
            gasp_table.gaspRange = {
                0xffff: 0xf
            }

            if (
                (mode == 'replace') or \
                (mode == 'add' and 'gasp' not in font.font)
            ):
                print("Adding gasp to %s" % font['file_name'])
                font.font['gasp'] = gasp_table

        return input_fonts
