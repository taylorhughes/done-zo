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
    echo
    echo "$1 Can we continue? [y/n]"
    read CONTINUE
  done

  if ! [[ "$CONTINUE" =~ y|Y ]]
  then
    echo "Yikes, aborting."
    exit
  fi
}

if [ "$1" == "staging" ]
then
  STAGING=true
  APP_NAME="dnzo-staging"
  echo "== DEPLOYING DNZO TO STAGING =="
else
  STAGING=false
  APP_NAME="dnzo"
  echo "== DEPLOYING DNZO FOR REALZ =="
fi

echo

if [ $STAGING == false ]
then
  # REAL DEPLOYMENT.
  # verify this shit.
  
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
fi

# Update the _min JS/CSS files
./compile_resources.sh

# Get the current svn revision number.
REV=$(svn info . | grep Revision | sed -E -e s/[^0-9]+//g)

exit_unless_confirmed "Looks like the revision number is $REV."
echo "Great, updating dnzo/app.yaml version to match this revision ..."


# Update dnzo/app.yaml with the correct revision number.
sed -E -e \
    "s/^version:[[:space:]]+[[:digit:]]+/version: $REV/" \
    dnzo/app.yaml > dnzo/app.yaml.new
mv dnzo/app.yaml.new dnzo/app.yaml

# Update dnzo/app.yaml with the correct app name
sed -E -e \
    "s/^application:[[:space:]]+[a-z-]+/application: $APP_NAME/" \
    dnzo/app.yaml > dnzo/app.yaml.new
mv dnzo/app.yaml.new dnzo/app.yaml

if [ $STAGING == false ]
then
  # REAL DEPLOYMENT.
  echo "Commiting the following files for deployment:"

  echo
  svn status
  echo

  svn commit -m "Commit to deploy r$REV at http://$REV.latest.dnzo.appspot.com/"
  if ! [ $? -eq 0 ]
  then
    echo "Subversion commit failed; exiting."
  
    exit
  fi
fi

exit_unless_confirmed "About to commit application \"$APP_NAME\", version $REV to GAE."

echo "Submitting to App Engine ..."

appcfg.py update dnzo

echo "Done!"

