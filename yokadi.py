#!/usr/bin/env python
import os
from optparse import OptionParser

from sqlobject import *

import db
from ycmd import YCmd


def main():
    parser = OptionParser()

    # Add an option which takes an argument and is stored in options.filename.
    # 'metavar' is an example of argument and should match the text in 'help'.
    parser.add_option("--db", dest="filename",
                      help="TODO database", metavar="FILE")

    parser.add_option("--no-prompt", dest="interactive",
                      action="store_false", dest="interactive", default=True,
                      help="Do not ask questions")

    (options, args) = parser.parse_args()

    dbFileName = os.path.abspath(options.filename)
    connectionString = 'sqlite:' + dbFileName
    connection = connectionForURI(connectionString)
    sqlhub.processConnection = connection
    if not os.path.exists(dbFileName):
        print "Creating database"
        db.createTables()

    cmd = YCmd()
    cmd.interactive = options.interactive
    if len(args) > 0:
        cmd.onecmd(" ".join(args))
    else:
        cmd.cmdloop()


if __name__=="__main__":
    main()
# vi: ts=4 sw=4 et
