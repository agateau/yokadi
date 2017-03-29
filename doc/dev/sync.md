# Files

- Default DB in ~/.local/share/yokadi/yokadi.db
- Default DB dump in ~/.local/share/yokadi/db/
- History in ~/.cache/yokadi/history

# Design decisions

## Repository layout

The layout of the repository is designed so that the code using it is reliable
and as simple as possible. It is not designed to be convenient to browse for a
human.

It looks like this:

    repository/
        version
        (contains a single integer representing the repository version, currently 1)
        projects/
            $uuid.json
            $uuid.json
            ...
        tasks/
            $uuid.json
            $uuid.json
            ...
        aliases/
            $uuid.json
            $uuid.json
            ...

`$uuid` matches the `uuid` field of the table.

Each json file contains a dump of a row, excluding the `id` primary key, which
cannot be reliably synchronized since its an auto-increment field.

Rows of tables which have a unique "name" column like Project and Task could
have been represented as $name.json. This would have enforced the uniqueness at
the file system level, but I decided against this because it would have made it
more complicated at import time to "replay" file system changes on database
rows. A rename must be turned into an SQL UPDATE command, but if a file is
renamed and modified it can be shown as a file removal followed by a file
addition which would be turned into an SQL DELETE followed by an SQL INSERT. The
cascading deletes of the Project table would cause the SQL DELETE to delete all
its tasks, which is not what we want.

Using UUIDs for all file names means the file names are immutable: a file can be
created, modified and deleted but never moved or renamed.

## Enforcing database constraints

When files are imported from the repository to the database, we must ensure
database constraints are enforced. This applies to table columns with unique
restrictions such as project.name or alias.name.

Database constraints are enforced right before importing so that even if the
files in the repository are modified by external means, the files are in a
coherent state.

There are some tricky corner cases which must be taken into account. They are
described below.

### Solving conflicts

If two projects with the same name have been created independently, or if an
existing project has been remotely renamed to the name of a local project, we
automatically rename one of the projects.

This is similar for aliases, except that if the two aliases refer to the same
command then we can decide to delete one of them, since they are the same.

### "name swapping"

This happens if for example two projects have swapped names remotely. Given
project p1 (uuid=1234) and p2 (uuid=5678), the user did something like this:

- renamed p1 to tmp
- renamed p2 to p1
- renamed tmp to p2

When the database changes are dumped to the repository, we end up with one
commit which atomically swaps p1 and p2 names.

When importing this commit into another database, we can't simply do this:

    update project set name=p2 where uuid=1234
    update project set name=p1 where uuid=5678

If we try to do so the first update will fail because project with uuid 5678
still uses p2 as a project name.

Instead what we do is that every time we have to rename a project, we first take
note of the new name in a list, then change the name to a unique value (using an
uuid). Once we are done with all the project changes, we go through our list of
pending renames and set the final names. From the SQL side it looks like this:

    update project set name=1234 where uuid=1234
    update project set name=5678 where uuid=5678

    -- And when we are all done:

    update project set name=p2 where uuid=1234
    update project set name=p1 where uuid=5678

This is less efficient, but it supports swaps.

# Detecting local changes

The synchronisation system relies on SQL Alchemy events to detect local
changes: every time a database row is changed, SQL Alchemy emits an event which
is caught by the SyncManager. If the change affects a serialized table, the
corresponding changes are applied on the disk.

This requires all database changes to go through SQL Alchemy ORM and means we
cannot use direct database updates like `session.query(...).update(...)` or
`session.query(...).delete()`, because those updates bypass SQL Alchemy event
system.

# Commands
## s_dump

- Make DB read-only
- sync.dump()
- Make DB read-write

## s_pull

- Make DB read-only
- sync.pull()
- Make DB read-write

## s_push

- Make DB read-only
- sync.push()
- if fails:
    tell the user to run s_pull first
- Make DB read-write

## s_init

- Make DB read-only
- sync.initDumpRepository()
- sync.dump()
- Make DB read-write

## s_clone <url>

- Make DB read-only
- If there is already a dump repository:
    confirm it must be deleted
    delete it
- git clone <url>
- If db was not empty:
    dump db (do this before import all to avoid conflicts on project names)
- sync.importAll()
- Make DB read-write

## s_sync

- s_pull
- s_push

## s_set_remote_url <url>

- Define url as the `origin` remote of the dump repo

# API

## sync.dump()

- Dump all db

## sync.pull()

- Assert Git repository is clean
- git pull. If conflicts, handle them
- Commit changes
- import changes

## sync.importAll

- get all files
- `_importChanges`

## `sync._importChanges`

- for all changes:
    - for all new files: create task
    - for all modified files: update task
    - for all removed files: remove task

# Use cases

## Publishing an existing DB

    s_init
    Create a new git repo somewhere
    s_set_remote_url ssh://[<user>@]<hostname>/<path/to/repo>

## Setting up a new Yokadi DB to track an existing repo

    s_clone ssh://[<user>@]<hostname>/<path/to/repo>

## Merging an existing DB into an existing repo

    s_clone ssh://[<user>@]<hostname>/<path/to/repo>
    s_sync

## Fetching latest changes

    s_sync

# WIP setup

Create a first Yokadi setup

    mkdir ~/sandbox/y1
    isolate-yokadi ~/sandbox/y1
    y> s_init

Create remote repo

    mkdir ~/sandbox/remote
    cd ~/sandbox/remote
    git init --bare

Connect y1 to remote

    cd ~/sandbox/y1/db
    git remote add origin ~/sandbox/remote
    git push -u origin master

    isolate-yokadi ~/sandbox/y1
    y> s_sync

Create a second Yokadi setup

    mkdir -p ~/sandbox/y2
    cd ~/sandbox/y2
    git clone ~/sandbox/remote db

    isolate-yokadi ~/sandbox/y2
    y> _s_import_all
