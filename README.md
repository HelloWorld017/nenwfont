# nenwfont
> A webfont generator done right

**THIS PROJECT IS WIP**

## Warning
* This tool is not tested with ligatures, variable fonts, and many other opentype features.
* This tool does not take output css file optimization into consideration.
  * Using this tool may lead to large css files.
* This tool does not support `eot`, `svg` export.
  * As almost every modern browsers support `woff`
* Please use this tool at your own risk!

## Abstract
A tool to make webfont generation pipeline.
It supports frequency-based subsetting, CFF to glyf conversion, gasp table adding.

This example pipeline.yml shows how this tool converts given font into webfonts.

```yml
pipeline:
    -
        name: 'input'
        glob:
            - 'files/input/**/*.ttf'
            - 'files/input/**/*.otf'

    -
        name: 'cff_to_glyf'

    -
        name: 'add_gasp'
        mode: 'replace'

    -
        name: 'parse_attribute'
        key: 'path'
        pattern: "^(?P<group>.*)-.*\\.ttf$"

    -
        name: 'merge'
        merge_by: 'group'
        merge_base:
            key: 'path'
            match: "-base.ttf$"

    -
        name: 'subset'
        group_by:
            - 'hangul_2574'
            - 'ideograph_jouyou'
            - 'unicode_blocks'
            - 'all'

        order_by: 'wikipedia_frequency'
        max_glyphs: 256

    -
        name: 'add_program_info'

    -
        name: 'output'
        extensions:
            - 'woff'
            - 'woff2'

        output_fonts: 'files/output/fonts/{path}'
        output_css: 'files/output/stylesheet.css'
        make_preview: False

```
