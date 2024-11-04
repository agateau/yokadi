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

[ -d "$DST_DIR" ] || die "Destination dir '$DST_DIR' does not exist"

WORK_DIR=$(mktemp -d "$DST_DIR/yokadi-dist.XXXXXX")

log "Copying source"
cp -a --no-target-directory "$SRC_DIR" "$WORK_DIR"

log "Cleaning"
cd "$WORK_DIR"
git reset --hard HEAD
git clean -q -dxf

log "Building archives"
python3 -m venv create "$WORK_DIR/venv"
(
    . "$WORK_DIR/venv/bin/activate"
    pip install build
    python -m build
)
rm -rf "$WORK_DIR/venv"

log "Installing archive"
cd dist/
YOKADI_TARGZ=$(ls ./*.tar.gz)
tar xf "$YOKADI_TARGZ"

ARCHIVE_DIR="$PWD/${YOKADI_TARGZ%.tar.gz}"

python3 -m venv create "$WORK_DIR/venv"
(
    . "$WORK_DIR/venv/bin/activate"

    # Install Yokadi in the virtualenv and make sure it can be started
    # That ensures dependencies got installed by pip
    log "Smoke test"
    pip install "$ARCHIVE_DIR"
    yokadi exit

    log "Installing extra requirements"
    pip install -r "$ARCHIVE_DIR/extra-requirements.txt"

    log "Running tests"
    "$ARCHIVE_DIR/yokadi/tests/tests.py"
)

log "Moving archives out of work dir"
cd "$WORK_DIR/dist"
mv *.tar.gz *.whl "$DST_DIR"
rm -rf "$WORK_DIR"
log "Done"
