# Intro

This document presents how to use Yokadi with a third party calendar/todolist
application that support the ical format (RFC2345).

To use ical Yokadi features, you have to start the Yokadi daemon. That daemon
also managed alarms for due tasks. 

By default, the ical server is disabled. To active it, you have to start the
Yokadi daemon with the --icalserver switch.

The ical server will listen on tcp port 8000. You can choose another tcp port
with the --port switch.

Example, to start yokadi daemon with the icalserver on non standard tcp port 9000:

    yokadid --icalserver --port=9000

# Read your yokadi tasks in a third party tool

With a third party tool that support ical format and is able to read it through
http, just set it up to read on localhost:8000 (or whatever port you setup)
and enjoy.

If your calendar/todo tool only support local files:
* complain on your software broker to inclure ical over http ;-)
* make a simple shell script that download the ical file and put it on your crontab.

You can use wget for that:
    wget -O yokadi.ical http://localhost:8000

Each yokadi task is defined as an ical VTODO object. Yokadi project are represented
as special tasks on which included tasks are related.

# Create and update yokadi tasks from a third party tool

On the same tcp socket, you can write tasks with the PUT http method. Only tasks new and
updated tasks will be consided.

# Supported third party ical tool

Yokadi should support any tool that respect RFC2345. But we are not in a perfect
world.
The following tools are known to work properly with Yokadi ical server:
* Kontact/KOrganizer (4.4) from the KDE Software Compilation

If you successfully plugged Yokadi with another calendar/todolist tool, please
let us now in order to complete this list.


# Some security consideration

By default, the ical server only listen on localhost (loopback). You can bypass this
restriction with the --listen switch that make the icalserver listening on all interfaces.

If you do this, you will be able to access to ical http stream from another computer. But this
have some security issues if you don't setup a firewall to restrict who can access to
your yokadi daemon.
* everybody could access to your task list
* even worse, everybody could be able to modify you task list
* the icalserver had not been build with strong security as design goals.

You are warned. That's why listening only to localhost (which is the default) is
strongly recommanded.


<!-- vim: set ts=4 sw=4 et: -->
