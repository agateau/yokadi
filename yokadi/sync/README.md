## Configuration

- Local configuration in ~/.config/yokadi/yokadi.conf
- Default DB in ~/.local/share/yokadi/gsdump
- Default DB dump in ~/.cache/yokadi/db/
- History in ~/.cache/yokadi/history

Configuration file

    [db ~/.local/share/yokadi/yokadi.db]
    gs_dump_dir=~/.cache/yokadi/gsdump

    [db ~/foo/bar/yokadi.db]
    gs_dump_dir=~/foo/bar/gsdump

## gs.dump

- Make DB read-only
- Check Git repository is clean. If not, warn and propose committing pending changes
- Dump DB
- Commit changes
- Make DB read-write

## gs.pull

- Make DB read-only
- Check Git repository is clean. If not, warn and propose committing pending changes
- git pull. If conflicts, handle them...
- Commit changes
- List all Git changes since `synced` branch
    - for all new files: create task
    - for all modified files: update task
    - for all removed files: remove task
- Make DB read-write
- Updated `synced` branch to HEAD:
    git branch --force synced

## gs.push

- Make DB read-only
- git fetch
- If changes: Merge remote changes and restart
- If no changes: git push
- Make DB read-write

## gs.init

- Dump DB
- Declare a Git remote
- Publish remote
- Make origin/master the upstream branch of master
- Create the `synced` branch

## gs.clone

- git clone DB
- Create empty DB
- gs.pull

## gs.sync

- gs.dump
- gs.pull
- gs.push
