# Tips

## Introduction

This document presents practical advices on how to get the best out of Yokadi.

## Completion

Yokadi supports completion of command names, and in many commands it can
complete project names. Do not hesitate to try the `[tab]` key!

## Setting up a project hierarchy

You can set up a project hierarchy by adopting a name convention. For example if
you want to track tasks related to a program which is made of many plugins, you
could have the main project named `fooplayer`, all tasks for the .ogg plugin
stored in `fooplayer_ogg` and all tasks about the .s3m plugin in
`fooplayer_s3m`.

This makes it easy to categorize your tasks and also to have a general overview.
For example to list all `fooplayer` related tasks you can use:

    t_list fooplayer%

## Using keywords

Keywords are great to group tasks in different ways. For example you can create
a keyword named `phone`, and assign it to tasks which you must accomplish on
the phone.

Another useful keyword is `diy_store`: Every time you find that you need to buy
some supply from a do-it-yourself store, add it with this keyword. Next time you
are planning a trip to the store, get the list of what to buy with:

    t_list @diy_store

Or even nicer, directly print your list (from the shell):

    yokadi "t_list @diy_store --format plain" | lp

## Keep track of your meetings

To track my meetings, I like to use a `meeting` keyword together with an
assigned due date. Yokadi ability to add long descriptions to tasks is also
handy to associate address or contact information to a meeting task.

## Keep track of tasks you delegate to people

When you delegate a task to someone, add a keyword with its name to the task.
So you can check that people really do what they promise to do even if they
are not as organized as you are.

To list all tasks assigned to Bob:

    t_list @bob

To check all task that Bob should have done:

    t_list --overdue @bob

## Some useful shortcuts

Yokadi relies on readline library, so you can use very useful readline
shortcuts such as:

- up/down arrows to browse history
- ctrl-r to search backward in Yokadi history
- ctrl-l to clear the screen
- ctrl-t to swap two letters
- ctrl-a to go the begin of the line
- ctrl-e to go the end of the line
- ctrl-w delete last word

<!-- vim: set ts=4 sw=4 et: -->
