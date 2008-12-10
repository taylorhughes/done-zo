#!/usr/bin/env bash

JAVASCRIPTS_DIR="dnzo/resources/javascripts"
JAVASCRIPTS=" 
  dnzo/application.js
  dnzo/tasks.js
  dnzo/signup.js
  ext/prototype.js
  ext/scriptaculous.js
  ext/controls.js
  ext/effects.js
"
CSS_DIR="dnzo/resources/stylesheets"
CSS=" 
  style.css
"

# Location of YUI compressor tool
COMPRESSOR="tools/yuicompressor-2.4.1.jar"


# Update compiled stylesheets
for i in $CSS
do
  compiled=${i/.css/_compiled.css}
  echo "Updating $compiled ..."
  java -jar $COMPRESSOR $CSS_DIR/$i > $CSS_DIR/$compiled
done

# Update compiled scripts
for i in $JAVASCRIPTS
do
  compiled=${i/.js/_compiled.js}
  echo "Updating $compiled ..."
  java -jar $COMPRESSOR \
       $JAVASCRIPTS_DIR/$i > $JAVASCRIPTS_DIR/$compiled
done
