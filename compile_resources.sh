#!/usr/bin/env bash

JAVASCRIPTS_DIR="dnzo/resources/javascripts"

# Ensure that these indexes match.
COMBINED_JS_OUTPUT=(
  "ext/combined.js"
)
COMBINE_JS=(
  "ext/prototype.js ext/scriptaculous.js ext/effects.js ext/controls.js"
)

JAVASCRIPTS=" 
  dnzo/application.js
  dnzo/tasks.js
  ext/combined.js
"
CSS_DIR="dnzo/resources/stylesheets"
CSS=" 
  style.css
  public.css
"

# Location of YUI compressor tool
COMPRESSOR="tools/yuicompressor-2.4.1.jar"

for i in ${!COMBINE_JS[@]}
do
  inputs=""
  for file in ${COMBINE_JS[$i]}; do inputs="$inputs $JAVASCRIPTS_DIR/$file"; done
  
  echo "Combining ${COMBINE_JS[$i]} into ${COMBINED_JS_OUTPUT[$i]} ..."
    
  cat $inputs > $JAVASCRIPTS_DIR/${COMBINED_JS_OUTPUT[$i]}
done

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
