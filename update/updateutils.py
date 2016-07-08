"""
Utilities to handle database schema updates

@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or newer
"""
import sys

import sqlite3


def main(function):
    """
    Runs an update function on a database. Useful as a test main
    """
    dbpath = sys.argv[1]
    with sqlite3.connect(dbpath) as conn:
        function(conn.cursor())
