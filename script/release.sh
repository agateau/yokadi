#!/bin/sh
# Release tarballs in various format
cd $(dirname $0)/..
for format in gztar rpm wininst
do
    python setup.py bdist --format=$format
done
rm -rf build
rm MANIFEST
