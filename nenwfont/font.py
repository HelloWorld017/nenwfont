from copy import deepcopy
from fontTools.ttLib import TTFont
import os

class Font:
    def __init__(self, path, font):
        self.font = font
        self.attributes = {
            'path': path,
            'weight': self.get_weight(),
            'unicode_range': None,
            'file_name': os.path.basename(path),
            'family_name': self.get_name(1),
            'subfamily_name': self.get_name(2),
            'full_name': self.get_name(4),
            'postscript_name': self.get_name(6)
        }

    def get_name(self, name_id):
        if 'name' not in self.font:
            return None

        return self.font['name'].getDebugName(name_id)

    def get_weight(self):
        if 'OS/2' not in self.font:
            return None

        return self.font['OS/2'].usWeightClass

    def __contains__(self, key):
        return key in self.attributes

    def __getitem__(self, key):
        return self.attributes[key]

    def __setitem__(self, key, item):
        self.attributes[key] = item

    def clone(self):
        new_font = TTFont(self['path'])
        for modified_key, modified_table in self.font.tables.items():
            new_font[modified_key] = deepcopy(modified_table)

        new_attributes = self.attributes.copy()

        output = Font(new_path, new_attributes)
        output.attributes = new_attributes

        return output
