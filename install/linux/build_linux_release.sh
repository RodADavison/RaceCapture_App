#!/bin/bash

RELEASE_VERSION=${1}


PLATFORM=""
# figure out platform name
if uname -mrs | grep -q x86_64
then
  PLATFORM="x86_64"
fi

if uname -mrs | grep -q armv7l
then
  PLATFORM="raspberrypi"
fi

if [ $# -eq 0 ] ; then
        MAJOR=$(git describe | cut -d \- -f 1 | cut -d . -f 1)
        MINOR=$(git describe | cut -d \- -f 1 | cut -d . -f 2)
        BUGFIX=$(git describe | cut -d \- -f 1 | cut -d . -f 3)
        VERSION=$(git describe --exact-match HEAD 2>/dev/null)
        HASH=$(git rev-parse --short HEAD)
        
        if [ ! -z "$VERSION" ]; then
                RELEASE_VERSION=${VERSION}
        else
                RELEASE_VERSION=${MAJOR}.${MINOR}.${BUGFIX}_${HASH}
        fi
fi

cd ../..
python -m build_tools.build_default_tracks
python -m build_tools.build_default_mappings
cd -

rm -rf dist build racecapture_linux_*.tar.bz2

pyinstaller --clean -y racecapture_linux.spec

# pyinstaller includes unneeded files from share
# improve the pyinstaller script and this can be removed
rm -rf ./dist/racecapture/share

#package into tar file
tar cjvfC racecapture_linux_${PLATFORM}_${RELEASE_VERSION}.tar.bz2 dist racecapture

