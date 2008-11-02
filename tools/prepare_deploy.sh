#!/usr/bin/env bash

#
#  This script updates the compiled versions of the JS and CSS
#  in DNZO and increments the version number in the app.yaml file.
#

# Update compiled stylesheets
for i in ../dnzo/stylesheets/*.css
do
  # Do not recompile compiled files
  if [ $i = ${i/_compiled/} ]
  then
    compiled=${i/.css/_compiled.css}
    echo "Updating $compiled ..."
    java -jar yuicompressor-2.4.1.jar $i > $compiled
  fi
done

# Update compiled scripts
for i in ../dnzo/javascripts/*.js
do
  # Do not recompile compiled files or prototype
  if [ $i = ${i/_compiled/} ] && [ $i = ${i/prototype/} ]
  then
    compiled=${i/.js/_compiled.js}
    echo "Updating $compiled ..."
    java -jar yuicompressor-2.4.1.jar $i > $compiled
  fi
done

# Update the version number in dnzo/app.yaml
echo Updating dnzo/app.yaml version to match this revision ...
REV=$(svn info .. | grep Revision | sed -E -e s/[^0-9]+//g)
sed -E -e "s/^version:[[:space:]]+[[:digit:]]+/version: $REV/" ../dnzo/app.yaml > ../dnzo/app.yaml.new
mv ../dnzo/app.yaml.new ../dnzo/app.yaml

echo Done!