#!/usr/bin/env bash

if [ -d out ]
then
    rm -f out/*
else
    mkdir out
fi
PYTHONPATH="../.." python testasfdata.py
echo "=========================="
echo "show that CI matches OK when using separate sections"
diff out/asfdataboth2.out out/asfdataci.out
echo "=========================="
echo "Show difference when using the same section"
diff out/asfdataboth1.out out/asfdataci.out
