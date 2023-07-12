#!/bin/bash

set -x

p6="$1"

mkdir plugins
cp "$p6/modules/pelican_asf/files/toc.py" plugins/
cp -r "$p6/modules/pelican_asf/files/pelican-gfm" plugins/
