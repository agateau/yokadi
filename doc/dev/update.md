# How the update system works

Lets assume current version is x and target version is x+n.

The update process goes like this:

- Copy yokadi.db to work.db
- for each v between x and x + n - 1:
     - run `update<v>to<v+1>.update()`
- Create an empty database in recreated.db
- Fill recreated.db with the content of work.db
- If we are updating the database in place, rename yokadi.db to yokadi-$date.db
  and recreated.db to yokadi.db
- If we are creating a new database (only possible by directly calling
  update/update.py), rename recreated.db to the destination name;

The recreation steps ensure that:

- All fields are created in the same order (when adding a new column, you can't
  specify its position)
- All constraints are in place (when adding a new column, you can't mark it
  'non null')
- The updated database has the exact same structure as a brand new database.
