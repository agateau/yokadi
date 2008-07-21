#!/bin/sh
set -e

log() {
	echo "#### $@"
}

cp ~/doc/todo.db test0.db

#log "Python upgrading"
#python v1imp.py --db test0.db

log "Dumping"
sqlite3 test0.db <<EOF
.output test.sql
.dump
EOF

log "Shell upgrading"
./prop2kw.sh test.sql

sed  '/CREATE TABLE/,/);/d' test.sql > test-nocreate.sql

log "Creating empty db"
rm -f test1.db
python yokadi.py --db test1.db --create-only

log "Restoring"
sqlite3 test1.db <<EOF
.read test-nocreate.sql
EOF

log "Done, new db is test1.db"
