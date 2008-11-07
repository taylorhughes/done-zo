#!/usr/bin/env bash

#
#  This script updates the compiled versions of the JS and CSS
#  in DNZO and increments the version number in the app.yaml file.
#

exit_unless_confirmed ()
{
  CONTINUE=""
  while [ "$CONTINUE" = "" ]
  do
    echo ""
    echo "$1 Can we continue? [y/n]"
    read CONTINUE
  done

  if ! [[ "$CONTINUE" =~ y|Y ]]
  then
    echo "Yikes, aborting."
    exit
  fi
}

echo "Updating so we know we're at the head revision ..."
svn up
if ! [ $? -eq 0 ]
then
  echo "Subversion update failed; exiting."
  
  exit
fi

if [ -n "$(svn status)" ]
then
  echo "Subversion shows outstanding changes."
  echo "Please commit those changes before running this script."
  
  exit
fi

# Update compiled stylesheets
for i in dnzo/stylesheets/*.css
do
  # Do not recompile compiled files
  if [ $i = ${i/_compiled/} ]
  then
    compiled=${i/.css/_compiled.css}
    echo "Updating $compiled ..."
    java -jar tools/yuicompressor-2.4.1.jar $i > $compiled
  fi
done

# Update compiled scripts
for i in dnzo/javascripts/*.js
do
  # Do not recompile compiled files or prototype
  if [ $i = ${i/_compiled/} ] && [ $i = ${i/prototype/} ]
  then
    compiled=${i/.js/_compiled.js}
    echo "Updating $compiled ..."
    java -jar tools/yuicompressor-2.4.1.jar $i > $compiled
  fi
done

# Get the current svn revision number.
REV=$(svn info . | grep Revision | sed -E -e s/[^0-9]+//g)

exit_unless_confirmed "Looks like the revision number is $REV. Is that correct?"
echo "Great, updating dnzo/app.yaml version to match this revision ..."

# Update dnzo/app.yaml with the correct revision number.
sed -E -e \
    "s/^version:[[:space:]]+[[:digit:]]+/version: $REV/" \
    dnzo/app.yaml > dnzo/app.yaml.new
mv dnzo/app.yaml.new dnzo/app.yaml

echo "Commiting so we know we we're at the head revision ..."

svn commit
if ! [ $? -eq 0 ]
then
  echo "Subversion commit failed; exiting."
  
  exit
fi

echo "Submitting to App Engine ..."

# TODO: Actually deploy.

echo "Done!"