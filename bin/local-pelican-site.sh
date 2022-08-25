#!/bin/bash

# Create a local Pelican build of an infrastructure-pelican-based site
# and deploy it at http://localhost:8000
#
# requires pip3/python3, cmake, and a C compiler
# known to work on linux/osx. probably works under WSL. 
# will not work under basic Windows.

# github prefix for cloning/updating repos
GH="https://github.com/apache"

# site_build directory path. use a /tmp dir by default
SB="$HOME/pelican-local"

# infrastructure-pelican repo
IP="infrastructure-pelican"

# build target site repo minus the .git suffix
REPO=`basename $1 .git`

echo "Using GitHub prefix: $GH"
if [ "$1" = "" ] || [ $# -gt 1 ];
then
  echo "Usage: $0 site-repo"
  echo "Example: $0 infrastructure-website"
  exit -1
fi

echo "Starting build for $REPO"

# make sure our tools exist
echo "Checking dependencies..."
if ! command -v cmake &> /dev/null
then
  echo "cmake not found! you need to install the cmake package"
  exit -1
elif ! command -v python3 &> /dev/null
then
  echo "python3 not found! you need to install the python3 package"
  exit -1
elif ! command -v pip3 &> /dev/null
then
  echo "pip3 not found! you need to insatll the pip3 package"
  exit -1
elif ! command -v pipenv &> /dev/null
then
  echo "pipenv not found! installing it for you..."
  pip3 install pipenv > /dev/null 2>&1
  if [ $? -eq 1 ];
  then 
    echo "pipenv installation failed!" 
    exit -1
  fi
fi

# create our build dir to hold our repos and cmark-gfm 
if [ ! -d $SB ];
then
  mkdir $SB || 'echo "Creation of $SB failed!" && exit -1'
  cd $SB
else
  cd $SB
fi


# clone or update the pelican and site repos as needed
echo "Cloning repos..."

if [ -d $IP ];
then
  echo "$IP exists - updating..."
  cd $IP && git pull > /dev/null && cd .. 
else
  echo "Cloning $IP"
  # Sometimes useful to add -b <branch> for buildsite testing
  git clone $GH/$IP 2>&1 
fi

IP="$SB/$IP"

if [ -d $REPO ];
then
  echo "$REPO exists - not updating in case there are local changes!"
  echo "Perform a manual git pull to sync with upstream $REPO"
  # cd $REPO && git pull > /dev/null && cd ..
else
  echo "Cloning $REPO"
  git clone $GH/$REPO 2>&1
fi
REPO="$SB/$REPO"
# deploy our pipenv if we haven't already
# TBD: check timestamp on $IP/requirements.txt and auto-update pipenv deps
# right now that process is manual

if [ ! -f "Pipfile.lock" ];
then
  echo "Setting up pipenv..."
  pipenv --three install -r $IP/requirements.txt > /dev/null 2>&1 || 'echo "pipenv install failed!" && exit -1'

else
  echo "Pipfile.lock found, assuming pipenv exists."
  echo "Run pipenv install -r $IP/requirements.txt to update dependencies if needed."
fi

# figure out what version of cmark-gfm we need to use
echo "Extracting cmark version..."
VERSION=`grep ^VERSION ./infrastructure-pelican/bin/build-cmark.sh | cut -d '=' -f 2`

# if we already built this version of cmark, don't build it again
if [ $VERSION ];
then
  echo "Found version $VERSION"
else
  echo "cmark-gfm version string not found! this shouldn't happen."
  exit -1
fi

if [ -d "cmark-gfm-$VERSION" ];
then
  echo "Using existing ${PWD}/cmark-gfm-$VERSION/lib"
  export LIBCMARKDIR=${PWD}/cmark-gfm-$VERSION/lib
else
  echo "Building cmark-gfm..."
  eval `./infrastructure-pelican/bin/build-cmark.sh 2>&1 | grep export | grep -v echo `
fi

# run the site build/deploy in our pipenv environment

# Clean
if [ -d "$(realpath $REPO)/site-generated" ] && [ -f "$(realpath $REPO)/pelican.auto.py" ];
then
  echo "Generated local site exists! Removing..."
  rm -rf $(realpath $REPO)/site-generated $(realpath $REPO)/pelican.auto.py
fi

# Build
cd $REPO
pipenv run python3 $(realpath $IP)/bin/buildsite.py dir --yaml-dir $(realpath $REPO) --content-dir "$(realpath $REPO)/content"

# Serve
pipenv run python3 -m pelican content --settings $(realpath $REPO)/pelican.auto.py --o $(realpath $REPO)/site-generated -r -l -b 0.0.0.0

