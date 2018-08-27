#!/bin/sh

# Build script for debian, automatically submits to launchpad

DIR=$( dirname $0 )

cd $DIR
mkdir debian
cp build_files/* . 
mv python3-battmon.p* debian/
python3 setup.py --command-packages=stdeb.command bdist_deb

mkdir tmp
cd tmp

dpkg-source -x ../deb_dist/battmon*.dsc
cd battmon* 
debuild -S -sa
dput ppa:padiauj/battmon ../battmon_*source.changes

# cleanup 
cd $DIR
rm -rf tmp deb_dist dist battmon.egg-info battmon*.tar.gz debian *.desktop MANIFEST.in stdeb.cfg
