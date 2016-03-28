# Configuration

- Local configuration in ~/.config/yokadi/yokadi.conf
- Default DB in ~/.local/share/yokadi/yokadi.db
- Default DB dump in ~/.cache/yokadi/db/
- History in ~/.cache/yokadi/history

Configuration file

    [db ~/.local/share/yokadi/yokadi.db]
    gs_dump_dir=~/.cache/yokadi/gsdump

    [db ~/foo/bar/yokadi.db]
    gs_dump_dir=~/foo/bar/gsdump

# Commands
## s_dump

- Make DB read-only
- Check Git repository is clean. If not, warn and propose committing pending changes
- Dump DB
- Commit changes
- Make DB read-write

## s_pull

- Make DB read-only
- Check Git repository is clean. If not, warn and propose committing pending changes
- git pull. If conflicts, handle them
- Commit changes
- List all Git changes since `synced` branch
    - for all new files: create task
    - for all modified files: update task
    - for all removed files: remove task
- Make DB read-write
- Updated `synced` branch to HEAD:
    git branch --force synced

## s_push

- Make DB read-only
- git fetch
- If changes: Merge remote changes and restart
- If no changes: git push
- Make DB read-write

## s_init

- Dump DB
- Declare a Git remote
- Publish remote
- Make origin/master the upstream branch of master
- Create the `synced` branch

## s_clone

- git clone DB
- Create empty DB
- gs.pull

## s_sync

- s_dump
- s_pull
- s_push

## s_create_remote_repo <url>

- Creates a bare repo, url can be either a `file:` or an `ssh:` url
- If url is an ssh url, uploads the created repository using `scp -r` (or `rsync`?)
- Define url as the `origin` remote of the dump repo

## s_set_remote_url <url>

- Define url as the `origin` remote of the dump repo

# Use cases

## Publishing an existing DB

    s_init
    s_create_remote_repo ssh://[<user>@]<hostname>/<path/to/repo>

## Setting up a new Yokadi DB to track an existing repo

    s_clone ssh://[<user>@]<hostname>/<path/to/repo>

## Merging an existing DB into an existing repo

    s_init
    s_set_remote_url ssh://[<user>@]<hostname>/<path/to/repo>
    s_dump
    s_pull
    s_push
