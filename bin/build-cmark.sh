#!/bin/bash
#
# Build the cmark-gfm library and extensions within CURRENT DIRECTORY.
#
# USAGE:
#   $ build-cmark.sh [ VERSION [ TARDIR [ OUTPUTDIR ] ] ]
#
#   VERSION: defaults to 0.28.3.gfm.12
#   TARDIR: where to find a downloaded/cached tarball of the cmark
#           code, or where to place a tarball
#   OUTPUTDIR: where to create the lib/ directory. Defaults to within
#              the top-level checkout of the tarfile.
#              If specified, the directory must exist, and must not contain
#              a lib directory (to ensure clean output)
#

# Echo all of our steps
set -x
set -e # fail on error

#VERSION=0.28.3.gfm.20  ### not yet
VERSION=0.28.3.gfm.12
if [ "$1" != "" ]; then VERSION="$1"; fi

# The tarball exists here, or will be downloaded here.
TARDIR="."
if [ "$2" != "" ]; then TARDIR="$2"; fi

# Where to put the lib directory
# this is checked at the start of the build
OUTPUTDIR=${3:-.}

ARCHIVES="https://github.com/github/cmark-gfm/archive/refs/tags"
LOCAL="${TARDIR}/cmark-gfm.$VERSION.orig.tar.gz"

# Follow redirects, and place the result into known name $LOCAL
if [ -f "$LOCAL" ]; then
    echo "Using cached tarball: ${LOCAL}"
else
    echo "Fetching from cmark archives"
    curl -L -o "$LOCAL" "$ARCHIVES/$VERSION.tar.gz" || exit 1
fi

# Extract into temp dir, so can detect tarfile parent directory
TMPDIR=temp.$$
if [ -d "$TMPDIR" ]; then rm -rf "$TMPDIR"; fi
mkdir "$TMPDIR"

# extract into clean work directory
tar -C "$TMPDIR" -xzf "$LOCAL"

# find top-level directory name (assume only one)
EXTRACTED_AS=$(ls $TMPDIR)

# clear out any old build
if [ -d "$EXTRACTED_AS" ]; then rm -rf "$EXTRACTED_AS"; fi

# move extract out of temporary work directory
mv $TMPDIR/$EXTRACTED_AS .
rmdir $TMPDIR

# now build
pushd "$EXTRACTED_AS"
  # OUTPUTDIR must exist; lib must not (to avoid stale files)
  # (do this first, to avoid later disappointment)
  mkdir ${OUTPUTDIR}/lib # do not use -p here!
  # get full name
  LIBPATH=$(realpath ${OUTPUTDIR}/lib)

  mkdir build
  pushd build
    cmake -DCMARK_TESTS=OFF -DCMARK_STATIC=OFF ..
    make
  popd

  cp -Pp build/src/lib* ${LIBPATH}
  cp -Pp build/extensions/lib* ${LIBPATH}
popd

# These files/dir may need a reference with LD_LIBRARY_PATH.
# gfm.py wants this lib/ in LIBCMARKDIR.
ls -laF "$LIBPATH"

# Provide a handy line for copy/paste.
echo "export LIBCMARKDIR='$LIBPATH'"
