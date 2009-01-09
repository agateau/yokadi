# What is it?

Yokadi is a command-line oriented, SQLite powered, TODO list tool.  It helps
you organize all the things you have to do and you must not forget. It aims to
be simple, intuitive and very efficient.

In Yokadi you manage projects, which contains tasks. At the minimum, a task has
a title, but it can also have a description, a due date, an urgency or
keywords. Keywords can be any word that help you to find and sort your tasks.

# Dependencies

- Unix or Linux system. MacOSX and Windows should work but have not been tested.
- Python 2.4 or higher
- Sqlite module (included in Python since 2.5 release)
- SQLObject 0.9 or 0.10

# Quickstart

Here is an example of a short Yokadi session:

- Start Yokadi:

        ./yokadi
        Using default database (/home/me/.yokadi.db)
        Creating database
        Added keyword 'severity'
        Added keyword 'likelihood'
        Added keyword 'bug'

- Create your first task:

        yokadi> t_add birthday Buy food and drinks
        Project 'birthday' does not exist, create it (y/n)? y
        Added project 'birthday'
        Added task 'Buy food and drinks' (id=1)

- Add two other tasks:

        yokadi> t_add birthday Invite Bob
        Added task 'Invite Bob' (id=2)
        yokadi> t_add birthday Invite Wendy
        Added task 'Invite Wendy' (id=3)

- List tasks for project "birthday":

        yokadi> t_list birthday
                                                 birthday
        ID |Title                                                       |U  |S|Creation date   |Time left
        --------------------------------------------------------------------------------------------------
        1  |Buy food and drinks                                         |0  |N|2009-01-09 08:57|
        2  |Invite Bob                                                  |0  |N|2009-01-09 08:58|
        3  |Invite Wendy                                                |0  |N|2009-01-09 08:58|

- Once you have called Bob, you can mark task 2 as done:

        yokadi> t_mark_done 2
        Task 'Invite Bob' marked as done

        yokadi> t_list birthday
                                                 birthday
        ID |Title                                                       |U  |S|Creation date   |Time left
        --------------------------------------------------------------------------------------------------
        1  |Buy food and drinks                                         |0  |N|2009-01-09 08:57|
        3  |Invite Wendy                                                |0  |N|2009-01-09 08:58|

- Task 2 has not disappeared, but `t_list` skips done tasks by default. To list all tasks use:

        yokadi> t_list birthday --all
                                                 birthday
        ID |Title                                                       |U  |S|Creation date   |Time left
        --------------------------------------------------------------------------------------------------
        1  |Buy food and drinks                                         |0  |N|2009-01-09 08:57|
        2  |Invite Bob                                                  |0  |D|2009-01-09 08:58|
        3  |Invite Wendy                                                |0  |N|2009-01-09 08:58|

- To list only tasks marked as done today:

        yokadi> t_list birthday --done today
                                                 birthday
        ID |Title                                                       |U  |S|Creation date   |Time left
        --------------------------------------------------------------------------------------------------
        2  |Invite Bob                                                  |0  |D|2009-01-09 08:58|

- You may want to attach your grocery list to task 1. This can be done with `t_describe`.

        yokadi> t_describe 1

  This will start the editor specified in $EDITOR (or `vi` if not set) to enter a longer text, attached to the task.

- You can now display details of task 1:

        yokadi> t_show 1
         Project: birthday
           Title: Buy food and drinks
         Created: 2009-01-09 08:57:33
             Due: None
          Status: new
         Urgency: 0
        Keywords:

        - Orange juice
        - Coke
        - Beer
        - Cookies
        - Pizzas

  Note: `t_show` is not mandatory, just entering the task number will display its details.

- `t_list` indicates marks tasks which have a longer description with a '*' character:

        yokadi> t_list birthday
                                                 birthday
        ID |Title                                                       |U  |S|Creation date   |Time left
        --------------------------------------------------------------------------------------------------
        1  |Buy food and drinks                                        *|0  |N|2009-01-09 08:57|
        3  |Invite Wendy                                                |0  |N|2009-01-09 08:58|

There is much more, but this should get you started. You can get a list of all
commands by typing `help` and get the detailed documentation of a command with
`help <command>`.


# Integration

## Database location

By default, Yokadi creates a database in `$HOME/.yokadi.db`, but you can
specify an alternative location with the `--db` option.

A convenient way to start yokadi is by creating an alias in your `.bashrc` file like this:

        alias y='/home/me/yokadi/yokadi.py --db /home/me/travail/yokadi.db'

The single letter `y` will start Yokadi with your favorite database from wherever you are.

## Yokadid, the Yokadid daemon

If you want to be automatically reminded of due tasks, you can use the Yokadi
daemon.

The Yokadi daemon can be launched via desktop autostart services. In KDE, you
must create a shell script in `$HOME/.kde/Autostart/`. Sample script:

        /home/me/yokadi/yokadid.py --db /home/me/work/yokadi.db

<!-- vim: set ts=4 sw=4 et: -->
