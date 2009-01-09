# Updating your database

To update your Yokadi database to the latest version, run this command:

		update.py <path/to/current.db> <path/to/updated.db>

# How the update system works

Lets assume current version is x and target version is x+n, database version x
is current.db and database version x+n is updated.db.

The update process goes like this:

- Create a copy of current.db in work.db
- for v in range(x, x + n):
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

Updating from v to v+1 is done in separate scripts because these scripts may
define SQLObject tables.  SQLObject can't handle table redefinitions, using
separate scripts solves the problem.

Using separate scripts also makes it possible to write an update script in
shell if needed.
