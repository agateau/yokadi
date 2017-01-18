"""
Functions to deal with conflicts

@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""
from difflib import Differ


LOCAL_PREFIX = "L> "
REMOTE_PREFIX = "R> "


def prepareConflictText(local, remote):
    differ = Differ()
    diff = differ.compare(local.splitlines(keepends=True),
                          remote.splitlines(keepends=True))
    lines = []
    for line in diff:
        code = line[0]
        rest = line[2:]
        if rest[-1] != "\n":
            rest += "\n"
        if code == "?":
            continue
        if code == "-":
            lines.append(LOCAL_PREFIX + rest)
        elif code == "+":
            lines.append(REMOTE_PREFIX + rest)
        else:
            lines.append(rest)
    return "".join(lines)
