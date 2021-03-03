from nenwfont.nodes import nodes_map

class Program:
    def __init__(self, config):
        self.config = config
        self.pipeline = config['pipeline']
        self.temp_files = []
        self.callbacks = {}
        self.nodes = {
            node_key: nodes_map[node_key](self)

            for node_key in set([ node['name'] for node in self.pipeline ])
        }

    def add_callback(self, name, callback):
        if name not in self.callbacks:
            self.callbacks[name] = []

        self.callbacks[name].append(callback)

    def run_callback(self, name, args=tuple()):
        if name not in self.callbacks:
            return

        for callback in self.callbacks[name]:
            callback(*args)

    def process(self):
        fonts = []
        self.run_callback('before_process')

        for pipe in self.pipeline:
            self.run_callback('before_transform', (pipe, fonts))

            node = self.nodes[pipe['name']]
            fonts = node.transform(fonts, pipe)

            self.run_callback('after_transform', (pipe, fonts))

        self.run_callback('after_process', (fonts, ))

    def cleanup(self):
        for temp_file in self.temp_files:
            print("Removing temporary files: %s" % temp_file)
            os.remove(temp_file)


if __name__ == '__main__':
    from datetime import datetime
    import yaml

    transform_start = 0
    def before_transform_hook(pipe, fonts):
        global transform_start

        index = program.pipeline.index(pipe)
        print("=" * 30 + " (Stage %d / %d, with %d Fonts)" % (index, len(program.pipeline), len(fonts)))

        for key, value in pipe.items():
            print("%s: %s" % (key, repr(value)))

        print()

        transform_start = datetime.now().timestamp()

    def after_transform_hook(pipe, fonts):
        print()
        print("Done in %.3fs" % (datetime.now().timestamp() - transform_start))
        print("Emitted %d fonts" % len(fonts))

    def after_process_hook(fonts):
        print("=" * 30 + " (with %d Fonts)" % len(fonts))
        print("Cleaning Up!")
        for font in fonts:
            font.close()
        
        program.cleanup()

        print("Finished!")

        print("Fonts:")
        for font in fonts:
            print("\t%s" % font['family_name'])

    with open('pipeline.yml') as f:
        config = yaml.load(f, Loader=yaml.SafeLoader)

    program = Program(config)
    program.add_callback('before_transform', before_transform_hook)
    program.add_callback('after_transform', after_transform_hook)
    program.add_callback('after_process', after_process_hook)
    program.process()
