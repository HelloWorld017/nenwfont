from nenwfont.node import Node
from fontTools.ttLib.tables.DefaultTable import DefaultTable
import math
import struct
import time


class table__n_e_n_w(DefaultTable):
    version = 1
    pipelines = []

    def decompile(self, data, ttFont):
        version, date = struct.unpack('>HL', data[:6])

        self.version = version
        self.date = date * 24 * 3600

        data = data[6:]

        pipeline_length = struct.unpack('>L', data[:4])
        data = data[4:]

        self.pipelines = data[:pipeline_length].decode().split(',')
        data = data[pipeline_length:]

        assert not data

    def compile(self, ttFont):
        version = self.version
        date = math.floor(time.time() / (24 * 3600))
        pipeline = ','.join(self.pipelines)

        return struct.pack('>HLL', version, date, len(pipeline)) + pipeline.encode()


class AddProgramInfoNode(Node):
    name = 'add_program_info'
    updates_fonts = True

    def transform(self, input_fonts, options):
        add_pipeline = options.get('add_pipeline', False)

        for font in input_fonts:
            font.font['nenw'] = table__n_e_n_w()
            if add_pipeline:
                font.font['nenw'].pipeline = [ node.name for node in self.program.pipeline ]

        return input_fonts
