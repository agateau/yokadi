#!/bin/sh
set -e

PROGNAME="$(basename "$0")"

die() {
    echo "$PROGNAME: ERROR: $*" | fold -s -w "${COLUMNS:-80}" >&2
    exit 1
}

log() {
    echo "### $*" >&2
}

[ $# = 2 ] || die "USAGE: $PROGNAME <src/dir> <dst/dir>"

SRC_DIR=$(cd "$1" ; pwd)
DST_DIR=$(cd "$2" ; pwd)

[ -d "$SRC_DIR" ] || die "Source dir '$SRC_DIR' does not exist"
[ -d "$DST_DIR" ] || die "Destination dir '$SRC_DIR' does not exist"

WORK_DIR=$(mktemp -d "$DST_DIR/yokadi-dist.XXXXXX")

log "Copying source"
cp -a --no-target-directory "$SRC_DIR" "$WORK_DIR"

log "Check we are not master"
cd "$WORK_DIR"
BRANCH=$(git branch | awk '$1 == "*" { print $2 }')
[ "$BRANCH" != "master" ] || die "Source dir should point to a release branch checkout, not master!"

log "Cleaning"
git reset --hard HEAD
git clean -q -dxf

log "Building archives"
./setup.py -q sdist --formats=bztar,zip

log "Unpacking .tar.bz2"
cd dist/
YOKADI_TARBZ2=$(ls ./*.tar.bz2)
tar xf "$YOKADI_TARBZ2"

log "Running tests"
cd "${YOKADI_TARBZ2%.tar.bz2}"
python yokadi/tests/tests.py

log "Moving archives out of work dir"
cd "$WORK_DIR/dist"
mv ./*.tar.bz2 ./*.zip "$DST_DIR"
rm -rf "$WORK_DIR"
log "Done"
