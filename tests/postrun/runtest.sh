#!/usr/bin/env bash

# Script to set up and run a test

setup() {

    rm -rf site-generated
    rm -f pelicanconf.yaml
    rm -f pelican.auto.py
    rm -rf temp
    mkdir temp
    date >temp/date1.txt
    date >temp/date2.txt

    cp "$1" pelicanconf.yaml

    ../../bin/buildsite.py dir

    grep 'ASF_RUN\|ASF_POSTRUN' pelican.auto.py

}

export LIBCMARKDIR=Dummy # needed even if gfm not loaded

#=============================

setup pelicanconf1.yaml # This tests run script

echo "date1.tmp should exist as copy of date1.txt"
cmp temp/date1.txt temp/date1.tmp
echo "date2.tmp should not exist"
test -f temp/date2.tmp && { echo "date2.tmp is present!"; exit 1; }

#=============================

setup pelicanconf2.yaml # This tests postrun script

echo "date2.tmp should exist as copy of date2.txt"
cmp temp/date2.txt temp/date2.tmp
echo "date1.tmp should not exist"
test -f temp/date1.tmp && { echo "date1.tmp is present!"; exit 1; }

#=============================

setup pelicanconf3.yaml # This tests run and postrun script

echo "date1.tmp should exist as copy of date1.txt"
cmp temp/date1.txt temp/date1.tmp
echo "date2.tmp should exist as copy of date2.txt"
cmp temp/date2.txt temp/date2.tmp

#=============================
