#!/bin/sh
set -e

# This scripts updates the Documentation part of the site from Yokadi master
# branch.

# FIXME: do not hardcode paths!
SRC_DIR=$HOME/src/yokadi/
WWW_DIR=$HOME/src/yokadi-pages/
DOC_FILE=$WWW_DIR/doc.markdown

HEADER="---\ntitle: Documentation\nlayout: default\n---"

echo $HEADER > $DOC_FILE

for src in $SRC_DIR/README.markdown $SRC_DIR/doc/*.markdown ; do
	name=$(basename $src)
	dst=$WWW_DIR/$name
	echo $HEADER > $dst
	cat $src >> $dst

	title=$(echo $name | sed 's/\.markdown//')
	echo "- [$title]($title.html)" >> $DOC_FILE
done
