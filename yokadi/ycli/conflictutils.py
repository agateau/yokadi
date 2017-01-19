"""
Functions to deal with conflicts

@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""
from difflib import Differ


CONFLICT_BEGIN = "<<< LOCAL"
CONFLICT_MIDDLE = "==="
CONFLICT_END = ">>> REMOTE"

_TRANSITIONS = {
    (" ", "-"): [CONFLICT_BEGIN],
    (" ", "+"): [CONFLICT_BEGIN, CONFLICT_MIDDLE],
    ("-", " "): [CONFLICT_MIDDLE, CONFLICT_END],
    ("-", "+"): [CONFLICT_MIDDLE],
    ("+", " "): [CONFLICT_END],
    ("+", "-"): [CONFLICT_END, CONFLICT_BEGIN],
}


def _switchToState(state, newState):
    if state == newState:
        return []
    return [x + "\n" for x in _TRANSITIONS[(state, newState)]]


def prepareConflictText(local, remote):
    differ = Differ()
    diff = differ.compare(local.splitlines(keepends=True),
                          remote.splitlines(keepends=True))
    state = " "
    lines = []
    for line in diff:
        newState = line[0]
        rest = line[2:]
        if rest[-1] != "\n":
            rest += "\n"
        if newState == "?":
            continue
        else:
            lines.extend(_switchToState(state, newState))
            state = newState
            lines.append(rest)
    lines.extend(_switchToState(state, " "))
    return "".join(lines)
