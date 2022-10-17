#!/usr/bin/env python3
#
# To run this in dev/test, then LIBCMARKDIR must be defined in the
# environment.
#
# $ export LIBCMARKDIR=/path/to/cmark-gfm.0.28.3.gfm.12/lib
#
# ### see build-cmark.sh for building the lib
#

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
GIT             = '/usr/bin/git'
SVN             = '/usr/bin/svn'
PELICANFILES    = '/home/buildslave/slave/tools'
SCRATCH_DIR     = '/tmp'
PLUGINS         = '/opt/infrastructure-pelican/plugins'
VERSION         = '0.28.3.gfm.12'
LIBCMARKDIR     = f'/usr/local/asfpackages/cmark-gfm/cmark-gfm-{VERSION}/lib'
if not os.path.exists(LIBCMARKDIR):
    # Fail, if a path to the CMARK library is not in ENVIRON.
    LIBCMARKDIR = os.environ['LIBCMARKDIR']
THIS_DIR        = os.path.abspath(os.path.dirname(__file__))

IS_PRODUCTION   = os.path.exists(PELICANFILES)

# Automatic settings filenames
AUTO_SETTINGS_YAML = 'pelicanconf.yaml'
AUTO_SETTINGS_TEMPLATE = 'pelican.auto.ezt'
AUTO_SETTINGS = 'pelican.auto.py'
AUTO_SETTINGS_HELP = 'https://github.com/apache/infrastructure-pelican/blob/master/pelicanconf.md'

class _helper:
    def __init__(self, **kw):
        vars(self).update(kw)


def start_build(args):
    """ The actual build steps """

    path = os.path.join(SCRATCH_DIR, args.project)
    
    # Set up virtual environment
    print("Setting up virtual python environment in %s" % path)
    venv.create(path, clear=True, symlinks=True, with_pip=False)

    # Pull in repository data
    sourcepath = os.path.join(path, 'source')
    print("Cloning from git repository %s (branch: %s)" % (args.source, args.sourcebranch))
    subprocess.run((GIT, 'clone', '--branch', args.sourcebranch, '--depth=1', '--no-single-branch', args.source, sourcepath),
                   check=True)

    # Activate venv and install pips if needed. For dev/test, we will
    # assume that all requirements are available at the system level,
    # rather than needing to install them into the venv.
    ### note: this makes it difficult to test requirements.txt, but it
    ### will do for now. Debugging requirements.txt failures on the
    ### production buildbot is not difficult to correct.
    if IS_PRODUCTION and os.path.exists(os.path.join(sourcepath, 'requirements.txt')):
        print("Installing pips")
        subprocess.run(('/bin/bash', '-c',
                        'source bin/activate; pip3 install -r source/requirements.txt'),
                       cwd=path, check=True)
    else:
        print("On dev/test requirements.txt is not processed, skipping pip")

    # Where are our tools?
    if IS_PRODUCTION:
        tool_dir = PELICANFILES
    else:
        tool_dir = THIS_DIR
    print("TOOLS:", tool_dir)

    ### content_dir isn't quite right either. generate_settings() needs a
    ### better definition of its sourcepath. And we need a proper definition
    ### of content_dir to pass to PELICAN.
    ### gonna brute force for now, to validate some thinking, then refine.

    ### content_dir is where the PAGES are located
    ### settings_dir is the root of themes and plugins

    # Where is the content located?
    ### for now, just look for some possibilities. This should come from
    ### the .yaml or something.
    content_dir = os.path.join(sourcepath, 'content')
    settings_dir = sourcepath
    if not os.path.exists(content_dir):
        content_dir = os.path.join(sourcepath, 'site')
        assert os.path.exists(content_dir)
        settings_dir = content_dir

    pelconf_yaml = os.path.join(sourcepath, AUTO_SETTINGS_YAML)
    if os.path.exists(pelconf_yaml):
        settings_path = os.path.join(path, AUTO_SETTINGS)
        if IS_PRODUCTION:
            builtin_plugins = PLUGINS
        else:
            builtin_plugins = os.path.join(tool_dir, os.pardir, 'plugins')
        generate_settings(pelconf_yaml, settings_path, [ builtin_plugins ], settings_dir)
    else:
        # The default name, but we'll pass it explicitly.
        settings_path = os.path.join(sourcepath, 'pelicanconf.py')

        # Set currently supported plugins
        ### this needs to be removed, as it is too indeterminate.
        with open(settings_path, 'a') as f:
            f.write("""
try:
    PLUGINS += ['toc']
except:
    PLUGINS = ['toc', 'gfm']
""")

    # Call pelican
    buildpath = os.path.join(path, 'build/output')
    os.makedirs(buildpath, exist_ok = True)
    buildcmd = ('/bin/bash', '-c',
                'source bin/activate; cd source && '
                ### note: adding --debug can be handy
                f'(pelican {content_dir} --settings {settings_path} -o {buildpath})',
                )
    print("Building web site with:", buildcmd)
    env = os.environ.copy()
    env['LIBCMARKDIR'] = LIBCMARKDIR
    subprocess.run(buildcmd, cwd=path, check=True, env=env)

    count = len(glob.glob(f'{buildpath}/**/*.html', recursive=True))
    print(f"{count} html files.")
    if args.count > 0 and args.count > count:
        print("Not enough html pages in the Web Site. Minimum %s > %s found in the Web Site." % (args.count, count))
        sys.exit(4)

    # Done for now
    print("Web site successfully generated!")

    # It is much easier to do all the below, if we chdir()
    os.chdir(sourcepath)

    # Copy to result branch
    print("Copying web site to branch:", args.outputbranch)

    try:
        subprocess.run((GIT, 'rev-parse', '--verify', "origin/%s" % args.outputbranch),
                       check=True)
        print("- Doing fresh checkout of branch %s" % args.outputbranch)
        subprocess.run((GIT, 'checkout', args.outputbranch, '-f'), check=True)
        subprocess.run((GIT, 'pull'), check=True)
    except:
        print("- Branch %s does not exist (yet), creating it..." % args.outputbranch)
        # If .asf.yaml exists, which it should, make a copy of it in memory for later
        asfyml = os.path.join(sourcepath, '.asf.yaml')
        myyaml = None
        if os.path.exists(asfyml):
            myyaml = open(asfyml).read()
        subprocess.run((GIT, 'checkout', '--orphan', args.outputbranch), check=True)
        subprocess.run((GIT, 'rm', '-rf', '.'), check=True)
        # Add .asf.yaml back in if we found it.
        if myyaml:
            open(asfyml, "w").write(myyaml)
            subprocess.run((GIT, 'add', '.asf.yaml'), check=True)

    print("- Adding new content to branch")
    # RM output dir if it already exists
    outputdir = os.path.join(sourcepath, 'output')
    if os.path.isdir(outputdir):
        print("Removing existing output dir %s" % outputdir)
        shutil.rmtree(outputdir)
    shutil.move(buildpath, outputdir)
    subprocess.run((GIT, 'add', 'output/'), check=True)

    # Check if there are any changes.
    cp = subprocess.run((GIT, 'diff', '--cached', '--quiet'))
    if cp.returncode == 0:
        # There were no differences reported.
        print('Nothing new to commit. Ignoring this build.')
    else:
        print("- Committing to %s" % args.source)
        subprocess.run((GIT, 'commit', '-m', 'Automatic Site Publish by Buildbot'), check=True)

        # If we're not in production, then avoid pushing changes.
        if IS_PRODUCTION:
            print('- Pushing changes, for publishing')
            subprocess.run((GIT, 'push', args.source, args.outputbranch), check=True)

        print('Success. Done.')
    # for dev/test provide viewing instructions
    if not IS_PRODUCTION:
        if args.listen:
            try:
                subprocess.run(('pelican','-l'), check=True)
            except KeyboardInterrupt:
                pass
        else:
            print(f'To test output:\ncd {sourcepath}; pelican -l')


def build_dir(args):

    # Where to place the automatically-generated AUTO_SETTINGS file (pelican.auto.py)
    auto_dir = '.'

    # Where is the YAML file?
    yaml_dir = args.yaml_dir

    # Where is the content located?
    content_dir = args.content_dir

    # Where are our tools?
    tool_dir = THIS_DIR
    print("TOOLS:", tool_dir)

    pelconf_yaml = os.path.join(yaml_dir, AUTO_SETTINGS_YAML)
    if os.path.exists(pelconf_yaml):
        settings_path = os.path.join(auto_dir, AUTO_SETTINGS)
        builtin_plugins = os.path.join(tool_dir, os.pardir, 'plugins')
        generate_settings(pelconf_yaml, settings_path, [ builtin_plugins ])
    elif os.path.exists(os.path.join(yaml_dir, 'pelicanconf.py')):
        settings_path = os.path.join(yaml_dir, 'pelicanconf.py')
    else:
        print(f'ERROR: {pelconf_yaml} is missing')
        print(f'  see: {AUTO_SETTINGS_HELP}')
        sys.exit(4)


    if args.listen:
        pel_options = '-r -l -b 0.0.0.0'
    else:
        pel_options = ''

    # Call pelican
    buildcmd = ('/bin/bash', '-c',
                ### note: adding --debug can be handy
                f'(pelican {content_dir} --settings {settings_path} --o {args.output} {pel_options})',
                )
    print("Building web site with:", buildcmd)
    env = os.environ.copy()
    env['LIBCMARKDIR'] = LIBCMARKDIR
    try:
        ### is the cwd_necessary?
        subprocess.run(buildcmd, cwd=auto_dir, check=True, env=env)
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

    content = ydata.get('content', { })
    tdata['pages'] = content.get('pages')
    tdata['static'] = content.get('static_dirs', [ '.', ])

    tdata['p_paths'] = builtin_p_paths
    tdata['use'] = ['gfm']
    
    tdata['uses_sitemap'] = None
    if 'plugins' in ydata:
        if 'paths' in ydata['plugins']:
            for p in ydata['plugins']['paths']:
                tdata['p_paths'].append(os.path.join(sourcepath, p))

        if 'use' in ydata['plugins']:
            tdata['use'] = ydata['plugins']['use']
        
        if 'sitemap' in ydata['plugins']:
            sm = ydata['plugins']['sitemap']
            sitemap_params =_helper(
                    exclude=str(sm['exclude']),
                    format=sm['format'],
                    priorities=_helper(
                        articles=sm['priorities']['articles'],
                        indexes=sm['priorities']['indexes'],
                        pages=sm['priorities']['pages'],
                        ),
                    changefreqs=_helper(
                        articles=sm['changefreqs']['articles'],
                        indexes=sm['changefreqs']['indexes'],
                        pages=sm['changefreqs']['pages'],
                        ),
                    )

            tdata['uses_sitemap'] = 'yes'  # ezt.boolean
            tdata['sitemap'] = sitemap_params
            tdata['use'].append('sitemap')  # add the plugin

    tdata['uses_index'] = None
    if 'index' in tdata:
        tdata['uses_index'] = 'yes'  # ezt.boolean

    if 'genid' in ydata:
        genid = _helper(
                unsafe=str(ydata['genid'].get('unsafe', False)),
                metadata=str(ydata['genid'].get('metadata', False)),
                elements=str(ydata['genid'].get('elements', False)),
                permalinks=str(ydata['genid'].get('permalinks', False)),
                tables=str(ydata['genid'].get('tables', False)),
                headings_depth=ydata['genid'].get('headings_depth'),
                toc_depth=ydata['genid'].get('toc_depth'),
                )

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


def locked_build(args):
    """ Grab an exclusive lock on this project via flock. Try for 2 minutes """
    ### NOTE: we do not delete/clean up this file, as that may interfere
    ###   with other processes. Just leave 'em around. Zero length files.
    with open(f'{SCRATCH_DIR}/{args.project}.lock', 'w') as fp:
        start_time = time.time()

        while (time.time() - start_time) < 120:
            try:
                fcntl.flock(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                print(f'WARNING: Building for "{args.project}" is locked, trying again in 10 seconds.')
                # Pause a bit, then loop.
                time.sleep(10)
                continue
            # Got the lock!

            try:
                start_build(args)
            finally:
                # Done, or errored. Release the lock.
                fcntl.flock(fp, fcntl.LOCK_UN)

            # All done.
            return

        print("ERROR: Could not acquire lock for project directory - is another build taking ages to complete?!")
        sys.exit(-1)

    
def main():
    #os.chdir('/tmp/nowhere')  ### DEBUG: make sure we aren't reliant on cwd

    # Gather CLI args
    parser = argparse.ArgumentParser(description = "This program performs ASF Pelican builds generating static web sites from source content.")
    # The --sourcetype option is present to support legacy command lines
    parser.add_argument("--sourcetype", action = "store_true", help = argparse.SUPPRESS)

    subparsers = parser.add_subparsers(help="Available subcommands.")

    parser_git = subparsers.add_parser("git", help="Retrieve source from git repository, build, and commit the result")
    parser_git.add_argument("--source", required = True, help = "Source repository URL (required)")
    parser_git.add_argument("--project", required = True, help = "ASF Project (required)")
    parser_git.add_argument("--sourcebranch", help = "Web site repository branch to build from (default: %(default)s)", default = "main")
    parser_git.add_argument("--outputbranch", help = "Web site repository branch to commit output to (default: %(default)s)", default = "asf-site")
    parser_git.add_argument("--count", help = "Minimum number of html pages (default: %(default)s)", type = int, default = 0)
    parser_git.add_argument("--listen", help = "Start pelican -l after build (default: %(default)s)", action = "store_true")
    parser_git.set_defaults(func=locked_build)

    parser_dir = subparsers.add_parser("dir", help = "Build source in current directory and optionally serve the result")
    parser_dir.add_argument("--output", help = "Pelican output path (default: %(default)s)", default = "site-generated")
    parser_dir.add_argument("--listen", help = "Pelican build in server mode (default: %(default)s)", action = "store_true")
    parser_dir.add_argument('--yaml-dir', help='Where pelicanconf.yaml is located (default: %(default)s)', default='.')
    parser_dir.add_argument('--content-dir', help='Where is the content located (default: %{default)s)', default='content')
    parser_dir.set_defaults(func=build_dir)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
