# Coding style

## Naming

Classes use CamelCase. Functions use mixedCase. Here is an example:

    class MyClass(object):
        def myMethod(self, arg1, arg2):
            pass


        def anotherMethod(self, arg1, *args, **kwargs):
            pass

(Why? Because `someLongAndPowerfulMethod` takes less horizontal space than
`some_long_and_powerful_method`.)

Exception: Classes which implement command methods should use underscores,
since the name of the method is used to create the name of the command:

    class MyCmd(object):
        def do_t_cmd1(self, line):
            pass


        def parser_t_cmd1(self):
            return SomeParser


        def someMethod(self):
            pass

Filenames are lowercase. If they contain a class they should match the name of
the class they contain.

Internal functions and methods should be prefixed with `_`.

## Spacing

Indentation is 4 spaces.

Try to keep two blank lines between functions.

One space before and after operators, except in optional arguments.

    a = 12
    if a > 14 or a == 15:
        print a

    myFunction(a, verbose=True)

## Import

Use one import per line:

    import os
    import sys

Avoid polluting the local namespace with `from module import function`.

Good:

    import os
    os.listdir(x)

Bad:

    from os import listdir
    listdir(x)

You should however import classes like this:

    from module import SomeClass

Keep import in blocks, in this order:

1. Standard Python modules
2. Third-party modules
3. Yokadi modules

Keep import blocks sorted. It makes it easier to check if an import line is
already there.

# Command docstrings

All commands are documented either through their parser or using the command
docstring. To ensure consistency all usage string should follow the same
guidelines.

For example assuming your command is named `t_my_command`, which accepts a few
options, two mandatory arguments (a task id and a search text) and an optional
filename argument. The usage string should look like this:

    t_my_command [options] <id> <search_text> [<filename>]

No need to detail the options in the usage string, they will be listed by the
parser below the usage string.

# Database schema changes

If you want to modify the database schema (adding, removing, changing tables or
fields). You should:

- Present the changes on the mailing-list

- Implement your changes in db.py

- Increase the database version number

- Write an update script in update/

- Assuming the current version is x and your new version is x+1, you should tag
  the last commit *before* your changes as "db-vx".
  This way one can checkout the latest version of Yokadi before your changes,
  create a database version x and test your update script.
  The correct way to create the tag is:

        # Note the -a!
        git tag -a db-vx
        git push --tags

<!-- vim: set ts=4 sw=4 et: -->
