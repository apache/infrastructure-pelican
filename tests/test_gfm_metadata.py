#!/usr/bin/env python3

import importlib
import sys
import types


class FakeFunc:
    def __call__(self, *args):
        return 1


class FakeCmark:
    def __getattr__(self, _name):
        return FakeFunc()


def load_gfm(monkeypatch):
    monkeypatch.setenv('LIBCMARKDIR', '.')
    monkeypatch.setattr('ctypes.CDLL', lambda *_args: FakeCmark())

    pelican = types.ModuleType('pelican')
    utils = types.ModuleType('pelican.utils')
    plugins = types.ModuleType('pelican.plugins')
    signals = types.ModuleType('pelican.plugins.signals')
    readers = types.ModuleType('pelican.readers')

    class BaseReader:
        pass

    class Signal:
        def connect(self, _func):
            pass

    utils.get_date = lambda value: value
    readers.BaseReader = BaseReader
    signals.readers_init = Signal()
    plugins.signals = signals
    pelican.utils = utils
    pelican.plugins = plugins
    pelican.readers = readers

    monkeypatch.setitem(sys.modules, 'pelican', pelican)
    monkeypatch.setitem(sys.modules, 'pelican.utils', utils)
    monkeypatch.setitem(sys.modules, 'pelican.plugins', plugins)
    monkeypatch.setitem(sys.modules, 'pelican.plugins.signals', signals)
    monkeypatch.setitem(sys.modules, 'pelican.readers', readers)
    sys.modules.pop('plugins.gfm', None)

    return importlib.import_module('plugins.gfm')


def test_metadata_keys_allow_python_markdown_characters(monkeypatch):
    gfm = load_gfm(monkeypatch)

    text, metadata = gfm.GFMReader._split_metadata(
        'Title2: Example\n'
        'jira_key: INFRA-1\n'
        'page-kind: docs\n'
        '\n'
        'Body',
        {},
    )

    assert text == 'Body'
    assert metadata == {
        'title2': 'Example',
        'jira_key': 'INFRA-1',
        'page-kind': 'docs',
    }


def test_final_metadata_line_without_eol_is_not_body(monkeypatch):
    gfm = load_gfm(monkeypatch)

    text, metadata = gfm.GFMReader._split_metadata('Title: Metadata only', {})

    assert text == ''
    assert metadata == {'title': 'Metadata only'}
