# Ical support

## Introduction

This document presents how to use Yokadi with a third party calendar/todolist
application that supports the ical format (RFC2445).

To use ical Yokadi features, start the Yokadi daemon with the --icalserver
switch. This daemon also manages alarms for due tasks.

The ical server listens on TCP port 8000. You can choose another TCP port with
the --port switch. For example, to start Yokadi daemon with the icalserver on
TCP port 9000:

    yokadid --icalserver --port=9000

## Read your Yokadi tasks in a third party tool

If your third party tool supports ical format and is able to read it through
HTTP, just set it up to read on localhost:8000 (or whatever port you setup) and
enjoy.

If your calendar/todo tool only supports local files:

* complain to your software broker to include ical over HTTP ;-)
* make a simple shell script that downloads the ical file and put it on your
  crontab. You can use wget for that:

    wget -O yokadi.ical <http://localhost:8000>

Each Yokadi task is defined as an ical VTODO object. Yokadi projects are
represented as special tasks to which included tasks are related.

## Create and update yokadi tasks from a third party tool

On the same TCP socket, you can write tasks with the PUT HTTP method. Only
new and updated tasks will be considered.

## Supported third party ical tool

Yokadi should support any tool which implements RFC2345. But we are not in a
perfect world.

The following tools are known to work properly with Yokadi ical server:

* Kontact/KOrganizer (4.4) from the KDE Software Compilation

If you successfully plugged Yokadi with another calendar/todolist tool, please
let us now in order to complete this list.

## Some security considerations

By default, the ical server only listens on localhost (loopback). You can
bypass this restriction with the --listen switch which makes the ical server
listen on all interfaces.

If you do this, you will be able to access to the ical HTTP stream from another
computer. But this have some security issues if you don't setup a firewall to
restrict who can access to your Yokadi daemon:

* everybody could access to your task list
* even worse, everybody could be able to modify you task list
* the ical server has not been build with strong security as design goals.

You have been warned. That's why listening only to localhost (which is the
default) is strongly recommended.

<!-- vim: set ts=4 sw=4 et: -->
