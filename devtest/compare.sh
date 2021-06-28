#!/bin/bash
#
# USAGE:
#   ./compare.sh petri ~/src/asf/petri-site master
#   ./compare.sh gora ~/src/asf/gora-site main
#

invoked=`dirname $0`
absdir=`cd $invoked ; pwd`
bindir=`dirname $absdir`/bin
#echo $bindir

project=$1
source=$2  # URL or pathname to a local clone
branch=$3

set -x

export LIBCMARKDIR=/tmp/cm/cmark-gfm-0.28.3.gfm.12/lib

cd $source

# Get the branch where pelicanconf.* lives
git checkout $branch

# Now build the site into /tmp/$project/
$bindir/buildsite.py --project $project --source $source --sourcebranch $branch

# Switch to what the current/prior website looks like
git checkout asf-site

# Give a quick summary of old/new site
diff -rq output /tmp/$project/build/output
