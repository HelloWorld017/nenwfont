class Node:
    name = 'node'
    updates_fonts = False

    def __init__(self, program):
        self.program = program

    def transform(self, input_fonts, options):
        return input_fonts
