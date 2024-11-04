# Changelog

## 1.3.0 - 2024-11-05

- Update SQLAlchemy to 2.0.32.
- Use color to for keywords in tables.
- Fix crash handler failing on Windows.

## 1.2.0 - 2019-02-10

### New features

- The new `p_merge` command lets you merge a project into another.
- It is now possible to turn a task into a note with `t_to_note` and a note into a task with `n_to_task`.

### Bug fixes

- The `k_remove` command no longer ignores unused keywords.
- HTML output has been fixed to no longer output strings wrapped in `b""`.
- `t_list` filtering has been fixed so that `t_list --urgency 0` filters out tasks with a negative urgency, as expected.

### Improvements

- HTML output has been refreshed:
    - It looks more modern now.
    - Some fields have been removed (doneDate, creationDate).
    - The title, keywords and description fields have been merged.
    - An ID field has been added (handy to run a command on a task listed in the output).
    - Columns now use human-friendly titles.

### Misc

- The `--db` option is now deprecated and replaced by the `--datadir` option. `--db` will be removed in the next version.
- Similarly, the `YOKADI_DB` environment variable is now deprecated and will be removed in the next version.
- Yokadi no longer supports cryptography: encrypted databases will be decrypted at update.

## 1.1.1 - 2016-11-11

### Improvements

- When listing multiple projects, order them alphabetically.

### Bug fixes

- Fixed parse error if the user sets a time of "17m".
- When the user edits a tasks with t_edit and removes a keyword, remove the keyword from the task.
- Made recurrence code work with dateutil 2.6.0.

## 1.1.0 - 2016-09-03

### New features & Improvements

- A new command has been added: `t_medit`. `t_medit` lets you edit all tasks of a project in one go.
- Aliases can now be modified. The name of the alias can be modified with `a_edit_name` and the command with `a_edit_command`.
- Database format updates are now easier to run: just run `yokadi -u`, no more separate `update.py` command. Updates are also much faster.
- Task lists have been improved:
    - Borders look nicer.
    - Some bugs in the rendering of the title column have been fixed (wrong width, badly cropped text).
- Yokadi now uses standard paths by default: the database is stored in ~/.local/share/yokadi/yokadi.db and non-essential data is in ~/.cache/yokadi/.
- Reviewed and improved documentation. Moved developer documentation to a separate dir (doc/dev).

### Bug fixes

- The code handling recurrences has been made more robust.
- Recurrences are now stored in a more future proof way.
- Fixed `bug_edit` crash.
- Fixed negative keyword filter: A task with two keywords k1 and k2 would not be excluded by a filter !k1.

## 1.0.2 - 2016-03-28

- Use a more portable way to get the terminal size. This makes it possible to use Yokadi inside Android terminal emulators like Termux
- Sometimes the task lock used to prevent editing the same task description from multiple Yokadi instances were not correctly released
- Deleting a keyword from the database caused a crash when a t_list returned tasks which previously contained this keyword

## 1.0.1 - 2015-12-03

### User changes

- Make sure installing via pip installs the required dependencies

### Developer changes

- Improved release process

## 1.0.0 - 2015-11-29

### User changes

- Fixed an issue which caused t_list to fail when filtering by keywords on large lists
- Removed the project keywords feature. It was not very useful and made the searching code more complicated
- Fixed ical support: it now works with ical 3.6 or later
- Improved documentation
- Added Keywords field to yokadi.desktop

### Developer changes

- Yokadi has been ported to Python 3
- The application now uses SQLAlchemy instead of SQLObject to access the SQLite database

## 0.14 - 2014-05-03

### Command changes

- t_add, n_add:
    - Allow creating two tasks with the same title (useful for recurrent tasks, like "buy bread").
    - Allow using _ to select last project, making it possible to do multiple t_add on the same project with `t_add _ <task description>`.
    - Add --describe option to start describing the task right after adding it.
- t_describe, n_describe:
    - Safer task description editing: task is updated each time the editor saves, a lock manager now prevents multiple edits.
    - Use .md suffix instead of .txt for the temporary filename to allow some smart things with editors that understand Markdown.
    - Use project and task name for the temporary filename. Useful when using graphical editors or when your terminal title shows the current running command.
- t_due:
    - When called with a time argument which is before current time, set due date to the day after.
- t_show:
    - Show the task ID.
- t_list:
    - Use month and year for the task age if the task is older than 12 months.
    - Add support for arbitrary minimum date for --done.
    - Fixed broken help.
- n_list:
    - Display creation date instead of age.
    - Notes are now grouped by date.
- p_list:
    - Show task count per project.
- p_remove:
    - Show the number of associated tasks in the prompt.
- p_edit:
    - Handle case where user tries to rename a project using the name of an existing project.

### yokadid

- Add --restart option and --log option.
- Set process name with setproctitle.
- Configuration keys can now be overridden using environment variables.

### Misc

- Date/time commands now support `%d/%m/%y` date format.
- Replaced xyokadi with a desktop file.
- Updated README to match real output.

### Developer specific changes

- Command parser has been ported from optparse to argparse.
- Code is now PEP 8 compliant, with the exception of camelCase usage.
- All imports have been changed to absolute imports (ie `import yokadi.<something>`).
- Code has been reorganized into different sub directories.
- The scripts in bin/ are now smart enough to run the source tree version instead of the installed version if possible.
- We now use Travis for continuous integration.

## 0.13 - 2011-04-09

- cryptographic support to encrypt tasks title and description.
- t_apply now accept id range (x-y).
- Special keyword `__` can used in t_apply to affect all tasks previously select by t_list.

## 0.12 - 2010-07-06

- Negative keyword support. Ex.: `t_list !@home`
- Permanent filters on keyword or project. `t_filter @foo` will filter any further call to t_list on @foo keyword.

## 0.11.1 - 2009-11-02

- yokadi symlink (useful to run yokadi without installing it) was broken

## 0.11 - 2009-11-01

- dynamic display width according to user terminal
- display keywords in t_list
- bugs keywords are prefixed with a `_` to distinguish them from user keywords
- YOKADI_DB environment variable can be defined to set default yokadi database path
- tasks can be grouped by keyword instead of project
- special character `_` can be used to represent last task id
- custom aliases can be defined for all commands with a_add
- switch from GPL 3 to GPL v3 or newer license

## 0.10 - 2009-07-08

- ability to assign keywords to a project
- shortened some commands (old ones still available but deprecated):
    - `t_set_due` => `t_due`
    - `t_set_project` => `t_project`
    - `t_set_urgency` => `t_urgency`
- changed keyword syntax: use `@foo` instead of `-k foo`
- added t_recurs command to define task recursion (weekly, monthly, yearly...)
- added full text search with `t_list -s foo`
- enhanced t_list display
- added purge command (t_purge) to remove old tasks
- added Windows support
- fixed install script to be more friendly to both users and packagers

## 0.9 - 2009-02-07

First public release. Fully usable for home and work.
