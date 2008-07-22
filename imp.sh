#!/bin/sh
set -e

log() {
	echo "#### $@"
}

cp ~/doc/todo.db tmp.db

#log "Python upgrading"
#python v1imp.py --db tmp.db

#log "SQL upgrading"
#sqlite3 tmp.db "alter table task add column done_date timestamp"

log "Dumping"
sqlite3 tmp.db <<EOF
.output dump.sql
.dump
EOF

log "Shell upgrading"
sed -i 's/INSERT INTO "task"/&(id,title,creation_date,description,urgency,status,project_id)/' \
	dump.sql
#./prop2kw.sh dump.sql


sed  '/CREATE TABLE/,/);/d' dump.sql > dump-nocreate.sql

log "Creating empty db"
rm -f output.db
python yokadi.py --db output.db --create-only

log "Restoring"
sqlite3 output.db <<EOF
.read dump-nocreate.sql
EOF

log "Done, new db is output.db"
