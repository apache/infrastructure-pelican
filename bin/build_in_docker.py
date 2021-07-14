#!/usr/bin/env python3

import sys

# We want subprocess.run(), which arrived in 3.5
# We also want format-strings (eg. f'abc'), which arrived in 3.6
#  (of course, this file would just throw a syntax error for
#   any lesser version, but let's clarify what we need/want)
assert sys.version_info > (3, 6)

import argparse
import subprocess
import os
import shutil
import time
import fcntl
import venv
import glob
import datetime

import yaml
import ezt


# Command definitions - put into a conf later on?

VERSION         = '0.28.3.gfm.12'
LIBCMARKDIR     = f'/usr/local/asfpackages/cmark-gfm/cmark-gfm-{VERSION}/lib'
if not os.path.exists(LIBCMARKDIR):
    # Fail, if a path to the CMARK library is not in ENVIRON.
    LIBCMARKDIR = os.environ['LIBCMARKDIR']

THIS_DIR        = os.path.abspath(os.path.dirname(__file__))

# Automatic settings filenames
AUTO_SETTINGS_YAML = 'pelicanconf.yaml'
AUTO_SETTINGS_TEMPLATE = 'pelican.auto.ezt'
AUTO_SETTINGS = 'pelican.auto.py'


def build_docker():

    path = sourcepath = '.'

    # Where are our tools?
    tool_dir = THIS_DIR
    print("TOOLS:", tool_dir)

    pelconf_yaml = os.path.join(sourcepath, AUTO_SETTINGS_YAML)
    if os.path.exists(pelconf_yaml):
        settings_path = os.path.join(path, AUTO_SETTINGS)
        builtin_plugins = os.path.join(tool_dir, os.pardir, 'plugins')
        generate_settings(pelconf_yaml, settings_path, [ builtin_plugins ], sourcepath)
    else:
        # The default name, but we'll pass it explicitly.
        settings_path = os.path.join(sourcepath, 'pelicanconf.py')
        print(f'You must convert {settings_path} to {pelconf_yaml}')
        sys.exit(4)

    # Call pelican
    buildcmd = ('/bin/bash', '-c',
                'source bin/activate; '
                ### note: adding --debug can be handy
                f'(pelican content --settings {settings_path} -r -o site-generated -b 0.0.0.0 -l)',
                )
    print("Building web site with:", buildcmd)
    env = os.environ.copy()
    env['LIBCMARKDIR'] = LIBCMARKDIR
    try:
        subprocess.run(buildcmd, cwd=path, check=True, env=env)
    except KeyboardInterrupt:
        pass


def generate_settings(source_yaml, settings_path, builtin_p_paths=[], sourcepath='.'):
    ydata = yaml.safe_load(open(source_yaml))

    tdata = ydata['site']  # Easy to copy these simple values.
    tdata.update({
        'year': datetime.date.today().year,
        'theme': os.path.join(sourcepath, ydata.get('theme', 'theme/apache')),
        'debug': str(ydata.get('debug', False)),
        })
    tdata['p_paths'] = builtin_p_paths
    tdata['use'] = ['gfm']
    if 'plugins' in ydata:
        if 'paths' in ydata['plugins']:
            for p in ydata['plugins']['paths']:
                tdata['p_paths'].append(os.path.join(sourcepath, p))
        if 'use' in ydata['plugins']:
            tdata['use'] = ydata['plugins']['use']

    if 'genid' in ydata:
        class GenIdParams:
            def setbool(self, name):
                setattr(self, name, str(ydata['genid'].get(name, False)))
            def setdepth(self, name):
                setattr(self, name, ydata['genid'].get(name))

        genid = GenIdParams()
        genid.setbool('unsafe')
        genid.setbool('metadata')
        genid.setbool('elements')
        genid.setbool('permalinks')
        genid.setbool('tables')
        genid.setdepth('headings_depth')
        genid.setdepth('toc_depth')

        tdata['uses_genid'] = 'yes'  # ezt.boolean()
        tdata['genid'] = genid

        tdata['use'].append('asfgenid')  # add the plugin
    else:
        tdata['uses_genid'] = None

    tdata['uses_data'] = None
    tdata['uses_run'] = None
    tdata['uses_ignore'] = None
    tdata['uses_copy'] = None
    if 'setup' in ydata:
        sdata = ydata['setup']
        
        # Load data structures into the pelican METADATA.
        if 'data' in sdata:
            tdata['uses_data'] = 'yes'  # ezt.boolean()
            tdata['asfdata'] = sdata['data']
            tdata['use'].append('asfdata')  # add the plugin
        # Run the included scripts with the asfrun plugin.
        if 'run' in sdata:
            tdata['uses_run'] = 'yes'  # ezt.boolean
            tdata['run'] = sdata['run']
            tdata['use'].append('asfrun')  # add the plugin
        # Ignore files avoids copying these files to output.
        if 'ignore' in sdata:
            tdata['uses_ignore'] = 'yes'  # ezt.boolean
            tdata['ignore'] = sdata['ignore']
            # No plugin needed.
        # Copy directories to output.
        if 'copy' in sdata:
            tdata['uses_copy'] = 'yes'  # ezt.boolean
            tdata['copy'] = sdata['copy']
            tdata['use'].append('asfcopy')  # add the plugin

    # if ezmd files are present then use the asfreader plugin
    ezmd_count = len(glob.glob(f'{sourcepath}/**/*.ezmd', recursive=True))
    if ezmd_count > 0:
        tdata['use'].append('asfreader')  # add the plugin

    t = ezt.Template(os.path.join(THIS_DIR, AUTO_SETTINGS_TEMPLATE))
    t.generate(open(settings_path, 'w'), tdata)


def main():
    build_docker()

    
if __name__ == '__main__':
    main()
