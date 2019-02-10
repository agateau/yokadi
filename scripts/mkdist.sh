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

[ $# = 1 ] || die "USAGE: $PROGNAME <dst/dir>"

SRC_DIR=$(cd "$(dirname $0)/.." ; pwd)
DST_DIR=$(cd "$1" ; pwd)

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
./setup.py -q sdist --formats=gztar,zip

log "Installing archive"
cd dist/
YOKADI_TARGZ=$(ls ./*.tar.gz)
tar xf "$YOKADI_TARGZ"

ARCHIVE_DIR="$PWD/${YOKADI_TARGZ%.tar.gz}"

virtualenv --python python3 "$WORK_DIR/venv"
(
    . "$WORK_DIR/venv/bin/activate"

    # Install Yokadi in the virtualenv and make sure it can be started
    # That ensures dependencies got installed by pip
    log "Smoke test"
    pip3 install "$ARCHIVE_DIR"
    yokadi exit

    log "Installing extra requirements"
    pip3 install -r "$ARCHIVE_DIR/extra-requirements.txt"

    log "Running tests"
    "$ARCHIVE_DIR/yokadi/tests/tests.py"
)

log "Moving archives out of work dir"
cd "$WORK_DIR/dist"
mv ./*.tar.gz ./*.zip "$DST_DIR"
rm -rf "$WORK_DIR"
log "Done"
