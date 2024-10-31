# Bugtracking

## Introduction

Yokadi comes with a set of commands tailored to help you track bugs. These
commands are `bug_add` and `bug_edit`. They are similar to `t_add` and `t_edit`
except they will ask you a few questions to help you decide which bug to fix
next.

## Entering a bug

Enter a new bug like you would enter a new task:

    bug_add fooplayer Fooplayer crashes when opening a .bar file

Before adding the task to the project "fooplayer", `bug_add` will ask you the
severity of the bug:

    1: Documentation
    2: Localization
    3: Aesthetic issues
    4: Balancing: Enables degenerate usage strategies that harm the experience
    5: Minor usability: Impairs usability in secondary scenarios
    6: Major usability: Impairs usability in key scenarios
    7: Crash: Bug causes crash or data loss. Asserts in the Debug release
    Severity: _

Enter 7 here, this is a crash. Now `bug_add` wants to know about the likelihood
of the bug:

    1: Will affect almost no one
    2: Will only affect a few users
    3: Will affect average number of users
    4: Will affect most users
    5: Will affect all users
    Likelihood: _

.bar files are quite uncommon, enter 2 here. We reach the last question:

    bug: _

This last question is optional: `bug_add` wants to know the id of this bug.
This is where you can enter the Bugzilla/Trac/Mantis/... id of the bug. If you
just noticed this bug and have not yet entered it in a centralized bug tracker,
just press Enter. Yokadi will now add a task for your bug:

    Added bug 'Fooplayer crashes when opening a .bar file' (id=12, urgency=40)

If you edit the task with `t_edit 12` you will only be able to fix the task
title. To be asked for severity, likelihood and bug id again, use
`bug_edit 12`.

## What's next?

Based on the severity and likelihood, Yokadi computes the urgency of the bug.
The formula used is:

               likelihood * severity * 100
    urgency = -----------------------------
              max_likelihood * max_severity

This is based on the concept of "User Pain", as described by Danc here:

<http://lostgarden.com/2008/05/improving-bug-triage-with-user-pain.html>

Now, when you list your tasks with `t_list`, the most urgent tasks will be
listed first, making it easy to fix the most important bugs first.

## Behind the scenes

Likelihood, severity and bug are stored as Yokadi keywords (Yokadi keywords can
be associated with an integer value).

The bug urgency is computed from likelihood and severity, then stored in the
task urgency field. Yes, this means there is duplication and you may get
likelihood/severity and urgency out of sync if you manually adjust urgency with
`t_set_urgency`. In practice, I found it was not a problem.

## Tricks

Here are a few tricks I came up with while using Yokadi to do bug tracking:

- List all crashers: `t_list fooplayer -k severity=7`

- Make use of Yokadi keywords. For example I often use:
    - backport: I should backport the fix when done
    - i18n: This bug requires translation changes, better fix it before i18n freeze
    - patch: This bug as an attached patch (You can paste the patch in the bug
      description with `t_describe`)

- Find a bug by id: `t_list fooplayer -k bug=12`

- I often keep two projects in Yokadi, one for the stable release, another for
  development. For example I have `yokadi_stable` and `yokadi_dev`.

<!-- vim: set ts=4 sw=4 et: -->
