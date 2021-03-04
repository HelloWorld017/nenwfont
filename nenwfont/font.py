from copy import deepcopy
from fontTools.ttLib import TTFont
import os
import uuid

class Font:
    def __init__(self, program, path, font):
        self.program = program
        self.font = font
        self.attributes = {
            'path': path,
            'weight': self.get_weight(),
            'unicode_range': None,
            'file_name': os.path.basename(path),
            'family_name': self.get_name(1),
            'subfamily_name': self.get_name(2),
            'full_name': self.get_name(4),
            'postscript_name': self.get_name(6),
            'typographic_family_name': self.get_name(16),
            'typographic_subfamily_name': self.get_name(17)
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
        return key in self.attributes and self.attributes[key] is not None

    def __getitem__(self, key):
        return self.attributes[key]

    def __setitem__(self, key, item):
        self.attributes[key] = item

    def clone(self, new_font=None):
        new_attributes = self.attributes.copy()

        if new_font is None:
            print("Saving temporary font: %s" % self['file_name'])
            new_path = os.path.join(
                self.program.config.get('clone_directory', 'files/temp'),
                "%s.ttf" % uuid.uuid4()
            )
            self.program.temp_files.append(new_path)

            self.font.flavor = None
            self.font.save(new_path)

            new_font = TTFont(new_path)
            new_attributes['cloned_path'] = new_path

        output = Font(self.program, self['path'], new_font)
        output.attributes = new_attributes

        return output
