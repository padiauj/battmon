#!/bin/sh

# Build script for debian, automatically submits to launchpad

DIR=$( dirname $0 )

cd $DIR
mkdir debian
cp build_files/* . 
mv battmon.p* debian/
python3 setup.py --command-packages=stdeb.command  sdist_dsc \
 --package3 battmon --copyright-file COPYRIGHT bdist_deb

debsign deb_dist/*source.changes
dput ppa:padiauj/battmon deb_dist/*source.changes

# cleanup 
cd $DIR
rm -rf tmp deb_dist dist battmon.egg-info battmon*.tar.gz debian *.desktop \
 MANIFEST.in stdeb.cfg
