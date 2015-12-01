# Updating your database

## Summary

To update your Yokadi database to the latest version, run this command:

    <install-prefix>/share/yokadi/update/update.py <path/to/current.db> <path/to/updated.db>

## Technical details: how the update system works

Lets assume current version is x and target version is x+n, database version x
is current.db and database version x+n is updated.db.

The update process goes like this:

- Copy current.db to work.db
- for each v between x and x + n - 1:
     - run `update<v>to<v+1> work.db`
- Create a data-only SQL dump of work.db
- Create an empty database in updated.db
- Restore the dump in updated.db

The final dump/restore steps ensure that:

- All fields are created in the same order (when adding a new column, you can't
  specify its position)
- All constraints are in place (when adding a new column, you can't mark it
  'non null')
- The updated database has the exact same structure as a brand new database.

Each update step is run in a separate process because update scripts may
define tables, but SQLObject (which used to be Yokadi ORM) does not handle
table redefinitions, so it would raise an exception if a table was defined in
`update<x>to<x+1>.py` then redefined in `update<x+1>to<x+2>.py`.
Running update step in its own process avoids this problem.
