"""
Parse utilities which do not need the db module.

@author: Aurélien Gâteau <mail@agateau.com>
@author: Sébastien Renard <sebastien.renard@digitalfox.org>
@license: GPL v3 or later
"""
import re
from yokadi.core.yokadiexception import YokadiException


gSimplifySpaces = re.compile("  +")


def simplifySpaces(line):
    line = gSimplifySpaces.subn(" ", line)[0]
    line = line.strip()
    return line


def parseParameters(line):
    """Parse line of form -a -b -c some text
    @return: ((a, b, c), some text)
    """
    parameters = []
    text = []
    line = simplifySpaces(line)
    for word in line.split():
        if word.startswith("-") and len(word) == 2:
            parameters.append(word[1])
        else:
            text.append(word)
    return (parameters, " ".join(text))


def parseOneWordName(line):
    """Parse line, check it is a one word project name and return it
    @return: the name
    """
    line = line.strip()
    if " " in line:
        raise YokadiException("Name cannot contain spaces")
    if not line:
        raise YokadiException("Name cannot be empty")
    return line
