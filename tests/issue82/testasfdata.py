#!/usr/bin/env python3

import pprint
import pelican
import plugins.asfdata as asfdata

settings = { # Keep pelican happy
    'MARKDOWN': {},
    'FORMATTED_FIELDS': [],
    'PATH': '.',
    'OUTPUT_PATH': 'output',
    'THEME': 'simple',
    'IGNORE_FILES': [],
    'DELETE_OUTPUT_DIRECTORY': False,
    'OUTPUT_RETENTION': 0,
    'ASF_DATA': {
        'data': 'TBA',
        'metadata': {
        },
        'debug': False,
    }
}

def test(name):
    input = f"{name}.yaml"
    output = f"out/{name}.out"
    print(f"{input} => {output}")
    settings['ASF_DATA']['data'] = input
    settings['ASF_DATA']['metadata'] = {}
    pc = pelican.Pelican(settings)
    asfdata.config_read_data(pc)
    pp = pprint.PrettyPrinter(indent=2,stream=open(output, 'w'))
    metadata = settings['ASF_DATA']['metadata']
    pp.pprint(metadata)

test('asfdataboth1')
test('asfdataboth2')
test('asfdataci')
