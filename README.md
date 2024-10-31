[![Build Status](https://travis-ci.org/agateau/yokadi.png?branch=master)](https://travis-ci.org/agateau/yokadi)
[![Coverage Status](https://coveralls.io/repos/agateau/yokadi/badge.png)](https://coveralls.io/r/agateau/yokadi)

# What is it?

Yokadi is a command-line oriented, SQLite powered, TODO list tool.  It helps
you organize all the things you have to do and must not forget. It aims to be
simple, intuitive and very efficient.

In Yokadi you manage projects, which contain tasks. At the minimum, a task has
a title, but it can also have a description, a due date, an urgency or
keywords. Keywords can be any word that help you find and sort your tasks.

# Dependencies

Yokadi should run on any Unix-like systems. There is also some support for
Windows but it is not as tested.

Yokadi requires Python 3.4 or more and a few other modules, which you can install with:

    pip install -r requirements.txt

It can also make use of other modules listed in extra-requirements.txt. You can
install them with:

    pip install -r extra-requirements.txt

These modules are needed for the Yokadi Daemon.

# Quickstart

Here is an example of a short Yokadi session:

Start Yokadi:

    ./bin/yokadi
    Creating database
    Added keyword '_severity'
    Added keyword '_likelihood'
    Added keyword '_bug'
    Added keyword '_note'

Create your first task:

    yokadi> t_add birthday Buy food and drinks
    Project 'birthday' does not exist, create it (y/n)? y
    Added project 'birthday'
    Added task 'Buy food and drinks' (id=1)

Add two other tasks, you can use _ to refer to last project used:

    yokadi> t_add _ Invite Bob
    Added task 'Invite Bob' (id=2)
    yokadi> t_add _ Invite Wendy
    Added task 'Invite Wendy' (id=3)

List tasks for project "birthday":

    yokadi> t_list birthday
                                             birthday
    ID |Title                                                       |U  |S|Age    |Due date
    --------------------------------------------------------------------------------------------------
    1  |Buy food and drinks                                         |0  |N|1m     |
    2  |Invite Bob                                                  |0  |N|0m     |
    3  |Invite Wendy                                                |0  |N|0m     |

Once you have called Bob, you can mark task 2 as done:

    yokadi> t_mark_done 2
    Task 'Invite Bob' marked as done

    yokadi> t_list birthday
                                             birthday
    ID |Title                                                       |U  |S|Age    |Due date
    --------------------------------------------------------------------------------------------------
    1  |Buy food and drinks                                         |0  |N|2m     |
    3  |Invite Wendy                                                |0  |N|1m     |

Task 2 has not disappeared, but `t_list` skips done tasks by default. To list
all tasks use:

    yokadi> t_list birthday --all
                                             birthday
    ID |Title                                                       |U  |S|Age    |Due date
    --------------------------------------------------------------------------------------------------
    1  |Buy food and drinks                                         |0  |N|2m     |
    2  |Invite Bob                                                  |0  |D|1m     |
    3  |Invite Wendy                                                |0  |N|1m     |

To list only tasks marked as done today:

    yokadi> t_list birthday --done today
                                             birthday
    ID |Title                                                       |U  |S|Age    |Due date
    --------------------------------------------------------------------------------------------------
    2  |Invite Bob                                                  |0  |D|1m     |

You may want to attach your grocery list to task 1. This can be done with
`t_describe`.

    yokadi> t_describe 1

This will start the editor specified in $EDITOR (or `vi` if not set) to enter
a longer text, attached to the task.

You can now display details of task 1:

    yokadi> t_show 1
     Project: birthday
       Title: Buy food and drinks
          ID: 1
     Created: 2009-01-09 08:57:33
         Due: None
      Status: new
     Urgency: 0
  Recurrence: None
    Keywords:

    - Orange juice
    - Coke
    - Beer
    - Cookies
    - Pizzas

Note: `t_show` is not mandatory, just entering the task number will display its
details.

`t_list` indicates tasks which have a longer description with a `*` character:

    yokadi> t_list birthday
                                             birthday
    ID |Title                                                       |U  |S|Age    |Due date
    --------------------------------------------------------------------------------------------------
    1  |Buy food and drinks                                        *|0  |N|3m     |
    3  |Invite Wendy                                                |0  |N|2m     |

There is much more, we only scratched the surface, but this should get you
started. You can get a list of all commands by typing `help` and get the
detailed documentation of a command with `help <command>`.

# Advanced stuff

## Quick access to last task

When you execute multiple commands on the same task, you can use `_` as a
shortcut to the last task id. Assuming you created a task like this:

    yokadi> t_add home Buy chocolate
    Added task 'Buy chocolate' (id=1069)

Then the following commands are equivalents (until you work on another task):

    yokadi> t_edit 1069
    yokadi> t_edit _

## Due dates

You can define due dates for your tasks with `t_due`. This can be done with a
relative or absolute date:

    yokadi> t_due 21 +3d
    Due date for task 'Buy chocolate' set to Sat Jul 11 17:16:20 2009

    yokadi> t_due 21 23/07 10:30
    Due date for task 'Buy chocolate' set to Thu Jul 23 10:30:00 2009

Due dates are shown by `t_list`. Due date is colored according to time left. If
you want to be reminded when a task is due, you can use the Yokadi Daemon for
that. See below for details.

## Periodic tasks

If you have periodic tasks, you can tell it to Yokadi with `t_recurs`:

    yokadi> t_recurs 1 weekly monday 21:30
    yokadi> t_recurs 1 monthly 3 11:00
    yokadi> t_recurs 1 monthly last saturday 11:00
    yokadi> t_recurs 1 yearly 23/2 14:00

Type `help t_recurs` to see all possible syntaxes.

## Tasks range and magic __ keyword

`t_apply` is a very powerful function but sometimes you have to use it on
numerous tasks.  First, you can use task range like this:

    yokadi> t_apply 1-3 t_urgency 10
    Executing: t_urgency 1 10
    Executing: t_urgency 2 10
    Executing: t_urgency 3 10
    yokadi>

But sometimes tasks are not consecutive and you would like to use wonderful
`t_list` options to select your tasks.  Here's the trick: each time you display
tasks with `t_list`, Yokadi stores the id list in the magic keyword `__` that
you can give to `t_apply` like this:

    yokadi> t_list @keyword myProject
    (...)
    yokadi> t_apply __ t_urgency 35

Oh, by the way, one Yokadi dev uses the following alias which is quite self
explanatory:

    yokadi> a_list
    procrastinate => t_apply __ t_due +1d

## Mass editing tasks

`t_medit` lets you edit all tasks of a project at once by opening a text editor
with all the tasks and let you editing them, applying the changes when you
quit.  If you are familiar with `git`, this is similar to the way the `git
rebase --interactive` command works.

For example to edit all the tasks of the "birthday" project do the following:

    yokadi> t_medit birthday

Make adjustments to the task list (the syntax is documented as comments in the
text opened in the editor), then save the file and quit to apply the changes.

Yokadi provides Vim syntax highlighting files to make mass edit more
convenient. You can find them in `editors/vim`. To install them, run the
following:

    cd place/to/editors/vim
    mkdir -p ~/.vim/ftdetect
    mkdir -p ~/.vim/syntax
    cp ftdetect/medit.vim ~/.vim/ftdetect
    cp syntax/medit.vim ~/.vim/syntax

If you use another editor and can provide support for highlighting files, your
contribution is very welcome! Get in touch so that we can add your work to the
next version of Yokadi.

# Integration

## Database location

By default, Yokadi creates a database in `$HOME/.local/share/yokadi/yokadi.db`,
but you can specify an alternative directory with the `--datadir` option.

A convenient way to start Yokadi is by creating an alias in your `.bashrc` file
like this:

    alias y=yokadi

The single letter `y` will start Yokadi with your favorite database from
wherever you are.

## History location

By default, Yokadi will store input history in `$HOME/.cache/yokadi/history`.
This file stores commands used in Yokadi for future use and reference.

If you do now want to use the default history file location, you can define
the `YOKADI_HISTORY` environment variable to point to your history file:

    export YOKADI_HISTORY=$HOME/.hist/yokadi_history

## Yokadid, the Yokadid daemon

If you want to be automatically reminded of due tasks, you can use the Yokadi
daemon.

The Yokadi daemon can be launched via desktop autostart services. In most
desktop environments, you just need to create a symbolic link to yokadid (or a
shell script that calls it) in `$HOME/.config/autostart/`:

    ln -s `which yokadid` $HOME/.config/autostart/

# Contact

The project is hosted on <http://yokadi.github.io>.

All discussions happen on Yokadi mailing-list, hosted by our friends from the
Sequanux LUG. To join, visit
<http://sequanux.org/cgi-bin/mailman/listinfo/ml-yokadi>.

You can also find some of us on #yokadi, on the Freenode IRC network.

# Authors

Yokadi has been brought to you by:

- Aurélien Gâteau <mail@agateau.com>: Developer, founder
- Sébastien Renard <sebastien.renard@digitalfox.org>: Developer
- Benjamin Port <benjamin.port@brobase.fr>: Developer

Other people contributed to Yokadi:

- Olivier Hervieu <olivier.hervieu@wallix.com>: first working setup.py release
- Marc-Antoine Gouillart <marsu_pilami@msn.com>: Windows port
- Kartik Mistry <kartik@debian.org>: man pages
- Jonas Christian Drewsen <jdrewsen@gmail.com>: quarterly recurrence feature

<!-- vim: set ts=4 sw=4 et: -->
