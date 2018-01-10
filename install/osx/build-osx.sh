#!/usr/bin/env bash

RELEASE_VERSION=${1}

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


#Cleanup possible previous builds
rm -rf RaceCapture.app
rm -rf Kivy.App
rm RaceCapture*.dmg

#Update latest tracks
cd ../.. 
kivy -m build_tools.build_default_tracks
kivy -m build_tools.build_default_mappings
cd -

DIR=$( cd ../.. && pwd )

#Kivy's build/packaging tools expect the Kivy app here
if [ ! -f "./Kivy.App" ]; then
	cp -a /Applications/Kivy.app ./Kivy.App
fi

./package-app.sh "$DIR/"

#Use Kivy's 'cleanup app' script
./cleanup_app.sh RaceCapture.app

#Cleanup SDL2
find RaceCapture.app/Contents/Frameworks  -name "Current" | xargs rm -rf

#Cleanup source files
echo "-- Remove all py/pyc"
find -E RaceCapture.app -regex ".*pyc?$" -exec rm {} \;

#Customizations and file size savings
rm -rf RaceCapture.app/Contents/Frameworks/GStreamer.framework
rm -rf RaceCapture.app/Contents/Resources/kivy/examples
rm -rf RaceCapture.app/Contents/Resources/kivy/doc
rm -rf RaceCapture.app/Contents/Resources/kivy/.git
rm -rf RaceCapture.app/Contents/Resources/yourapp/.buildozer
rm -rf RaceCapture.app/Contents/Resources/yourapp/bin
rm -rf RaceCapture.app/Contents/Resources/kivy_stable
rm -rf RaceCapture.app/Contents/Resources/venv/lib/python2.7/site-packages/kivy
rm -rf RaceCapture.app//Contents/Resources/venv/share

#We have to customize their theme so checkboxes show up
cp ../../data/images/defaulttheme-0.png RaceCapture.app/Contents/Resources/kivy/kivy/data/images/
cp ../../data/images/defaulttheme.atlas RaceCapture.app/Contents/Resources/kivy/kivy/data/images/

#Custom icon
cp racecapture.icns RaceCapture.app/Contents/Resources/appIcon.icns

#Customize plist so our name and info shows up
cp Info.plist RaceCapture.app/Contents/

./create-osx-dmg.sh RaceCapture.app

#Rename the file to include the version
echo "-- Rename dmg to include provided version number"
mv RaceCapture.dmg RaceCapture_${1}.dmg
