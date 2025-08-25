#!/usr/bin/env python3

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
    settings['ASF_DATA']['data'] = f"{name}.yaml"
    settings['ASF_DATA']['metadata'] = {}
    pc = pelican.Pelican(settings)
    asfdata.config_read_data(pc)
    metadata = settings['ASF_DATA']['metadata']
    assert metadata['current_count'] == metadata['current_size']
    assert metadata['graduated_count'] == metadata['graduated_size']
    assert metadata['retired_count'] == metadata['retired_size']
    assert metadata['notretired_size'] == metadata['graduated_size'] + metadata['current_size']
    assert metadata['notinretiredgraduated_size'] == metadata['current_size']
    assert metadata['cttee_count'] == metadata['cttee_size']
    assert metadata['pmc_count'] == metadata['pmc_size']

test('asfdatawhere')
