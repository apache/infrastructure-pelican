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
GIT             = '/usr/bin/git'
SVN             = '/usr/bin/svn'
PELICANFILES    = '/home/buildslave/slave/tools'
SCRATCH_DIR     = '/tmp'

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


def start_build(args):
    """ The actual build steps """

    path = os.path.join(SCRATCH_DIR, args.project)
    
    # Set up virtual environment
    print("Setting up virtual python environment in %s" % path)
    venv.create(path, clear=True, symlinks=True, with_pip=False)

    # Pull in repository data
    sourcepath = os.path.join(path, 'source')
    print("Cloning from git repository %s (branch: %s)" % (args.source, args.sourcebranch))
    subprocess.run((GIT, 'clone', '--branch', args.sourcebranch, args.source, sourcepath),
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
        print("No requirements.txt found, skipping pip")

    # Where are our tools?
    if IS_PRODUCTION:
        tool_dir = PELICANFILES
    else:
        tool_dir = THIS_DIR
    print("TOOLS:", tool_dir)

    pelconf_yaml = os.path.join(sourcepath, AUTO_SETTINGS_YAML)
    if os.path.exists(pelconf_yaml):
        settings_path = os.path.join(path, AUTO_SETTINGS)
        builtin_p_paths = [
            os.path.join(tool_dir, os.pardir, 'plugins'),
            ]
        generate_settings(pelconf_yaml, settings_path, builtin_p_paths, sourcepath)
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
                f'(pelican content --settings {settings_path} -o {buildpath})',
                )
    print("Building web site with:", buildcmd)
    env = os.environ.copy()
    env['LIBCMARKDIR'] = LIBCMARKDIR
    subprocess.run(buildcmd, cwd=path, check=True, env=env)

    count = len(glob.glob(f'{buildpath}/**/*.html', recursive=True))
    message = ''
    if not IS_PRODUCTION:
        message = f' To test output: cd {path}/build; pelican -l'
    print(f"{count} html files.{message}")
    if args.count > 0 and args.count > count:
        print("Not enough html pages in the Web Site. Minimum %s > %s found in the Web Site." % (args.count, count))
        sys.exit(4)

    # Done for now
    print("Web site successfully generated!")

    if not IS_PRODUCTION:
        # We do NOT want to perform commits in a dev/test environment.
        return

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
    

    print("- Committing and pushing to %s" % args.source)
    subprocess.run((GIT, 'commit', '-m', 'Automatic Site Publish by Buildbot'), check=True)
    subprocess.run((GIT, 'push', args.source, args.outputbranch), check=True)

    print("Web site generated and published successfully!")
    

def generate_settings(source_yaml, settings_path, builtin_p_paths=[], sourcepath='.'):
    ydata = yaml.safe_load(open(source_yaml))

    tdata = ydata['site']  # Easy to copy these simple values.
    tdata.update({
        'year': datetime.date.today().year,
        'p_paths': builtin_p_paths + [ os.path.join(sourcepath, p) for p in ydata['plugins']['paths'] ],
        'use': ydata['plugins']['use'],
        'theme': os.path.join(sourcepath, ydata.get('theme', 'theme/apache')),
        })

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
        genid.setbool('debug')
        genid.setdepth('headings_depth')
        genid.setdepth('toc_depth')

        tdata['uses_genid'] = 'yes'  # ezt.boolean()
        tdata['genid'] = genid

        # Add the plugin.
        tdata['use'].append('asfgenid')
    else:
        tdata['uses_genid'] = None

    t = ezt.Template(os.path.join(THIS_DIR, AUTO_SETTINGS_TEMPLATE))
    t.generate(open(settings_path, 'w'), tdata)


def main():
    #os.chdir('/tmp/nowhere')  ### DEBUG: make sure we aren't reliant on cwd

    # Gather CLI args
    parser = argparse.ArgumentParser(description = "This program pulls in pelican sources and generates static web sites, committing the result back to the repository.")
    parser.add_argument("--sourcetype", help = "Source repository type (git/svn)", default = 'git')
    parser.add_argument("--source", required = True, help = "Source repository URL")
    parser.add_argument("--project", required = True, help = "ASF Project")
    parser.add_argument("--sourcebranch", help = "Web site repository branch to build from", default = 'master')
    parser.add_argument("--outputbranch", help = "Web site repository branch to commit output to", default = 'asf-site')
    parser.add_argument("--count", help = "Minimum number of html pages", type = int, default = 0)
    args = parser.parse_args()
    #print(args)

    # Fail fast, if somebody specifies svn.
    assert args.sourcetype == 'git'

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

    
if __name__ == '__main__':
    main()
