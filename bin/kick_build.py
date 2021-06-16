#!/usr/bin/env python3

import argparse
import re

import requests

# Where are the credentials stored?
### parameterize this?
CREDS_FNAME = '/x1/buildmaster/master1/kickbuild.txt'
#CREDS_FNAME = 'bb2.txt'

# LDAP to CNAME mappings for some projects
### this should be centralized, not copied
WSMAP = {
    'whimsy': 'whimsical',
    'empire': 'empire-db',
    'webservices': 'ws',
    'infrastructure': 'infra',
    'comdev': 'community',
}

# The schedule/host we need to kick for a rebuild.
### maybe parameterize?
SCHEDULER_NAME = 'pelican_websites'
API_HOST = 'ci2.apache.org'


def main(repo, sourcebranch, outputbranch, theme, notify, min_pages):

    # Never build from asf-site.
    assert sourcebranch != 'asf-site'
    
    # Infer project name from the repository name.
    ### this code and WSMAP should be centralized.
    m = re.match(r"(?:incubator-)?([^-.]+)", repo)
    pname = m.group(1)
    pname = WSMAP.get(pname, pname)

    # Login to BB2, to get an authn cookie.
    bbusr, bbpwd = open(CREDS_FNAME).readline().strip().split(':', 1)
    s = requests.Session()
    s.get(f'https://{API_HOST}/auth/login', auth=(bbusr, bbpwd))

    payload = {
        'method': 'force',
        'jsonrpc': '2.0',
        'id': None,  # Notification to server. We don't need a response.
        'params': {
            'reason': f'Rebuild {repo}, via kick_build.py',
            'source': f'https://gitbox.apache.org/repos/asf/{repo}.git',
            'sourcebranch': sourcebranch,
            'outputbranch': outputbranch,
            'project': pname,
            'theme': theme,
            'notify': notify,
            #'toc': toc,
            'minimum_page_count': min_pages,
        },
    }
    print('Triggering pelican build...')
    s.post(f'https://{API_HOST}/api/v2/forceschedulers/{SCHEDULER_NAME}', json=payload)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Kick of a Pelican build for a repository.')
    parser.add_argument('--repo', required=True,
                        help='Repository name to build.')
    parser.add_argument('--sourcebranch', default='main',
                        help='Branch with source content.')
    parser.add_argument('--outputbranch', default='asf-site',
                        help='Branch where output will be saved.')
    parser.add_argument('--theme', default='theme',
                        help='Subdirectory containing the theme to use.')
    parser.add_argument('--notify', default='private@infra.apache.org',
                        help='Where to email the build result message.')
    parser.add_argument('--min-pages', type=int, default=0,
                        help='Minimum number of generated pages.')

    args = parser.parse_args()
    print('ARGS:', args)
    main(args.repo, args.sourcebranch, args.outputbranch, args.theme,
         args.notify, args.min_pages)
