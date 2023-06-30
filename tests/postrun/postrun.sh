#!/usr/bin/env bash

# Script to test postrun command

cd temp
cp date2.txt date2.tmp

if [ -z "$PELICAN_OUTPUT_PATH" ]
then
    echo "PELICAN_OUTPUT_PATH is not defined!"
    exit 1
fi
