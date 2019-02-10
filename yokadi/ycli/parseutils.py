# -*- coding: UTF-8 -*-
"""
Parse utilities. Used to manipulate command line text.

@author: Aurélien Gâteau <mail@agateau.com>
@author: Sébastien Renard <sebastien.renard@digitalfox.org>
@license: GPL v3 or later
"""
from yokadi.ycli import tui
from yokadi.ycli.basicparseutils import simplifySpaces
from yokadi.core import db
from yokadi.core.db import Keyword
from yokadi.core.dbutils import KeywordFilter
from yokadi.core.yokadiexception import YokadiException


def parseLine(line):
    """Parse line of form:
    project some text @keyword1 @keyword2=12 some other text
    @return: a tuple of ("project", "some text some other text", keywordDict"""

    # First extract project name
    line = simplifySpaces(line)
    if line.count(" "):
        project, line = line.split(" ", 1)
    else:
        project = line
        line = ""

    line, keywordFilters = extractKeywords(line)

    return project, line, keywordFiltersToDict(keywordFilters)


def extractKeywords(line):
    """Extract keywords (@k1 @k2=n..) from line
    @param line: line from which keywords are extracted
    @returns: (remaining_text, keywordFilters)"""
    keywordFilters = []
    remainingText = []
    for token in line.split():
        if token.startswith("@") or token.startswith("!@"):
            keywordFilters.append(parseKeyword(token))
        else:
            remainingText.append(token)

    return (" ".join(remainingText), keywordFilters)


def createLine(projectName, title, keywordDict):
    tokens = []
    for keywordName, value in list(keywordDict.items()):
        if value:
            tokens.append("@" + keywordName + "=" + str(value))
        else:
            tokens.append("@" + keywordName)

    if projectName:
        tokens.insert(0, projectName)

    tokens.append(title)
    return " ".join(tokens)


def keywordFiltersToDict(keywordFilters):
    """Convert a list of KeywordFilter instnance to a simple keyword dictionary"""
    keywordDict = {}
    for keywordFilter in keywordFilters:
        keywordDict[keywordFilter.name] = keywordFilter.value
    return keywordDict


def warnIfKeywordDoesNotExist(keywordFilters):
    """Warn user is keyword does not exist
    @return: True if at least one keyword does not exist, else False"""
    session = db.getSession()
    doesNotExist = False
    for keyword in [k.name for k in keywordFilters]:
        if session.query(Keyword).filter(Keyword.name.like(keyword)).count() == 0:
            tui.error("Keyword %s is unknown." % keyword)
            doesNotExist = True
    return doesNotExist


def parseKeyword(line):
    """Parse given line to create a keyword filter
    @return: a KeywordFilter instance"""
    operators = ("!=", "=")
    if " " in line:
        raise YokadiException("Keyword filter should not contain spaces")

    name = None
    negative = False
    value = None
    valueOperator = None

    if line.startswith("!"):
        negative = True
        line = line[1:]

    if not line.startswith("@"):
        raise YokadiException("Keyword name must be prefixed with a @")

    line = line[1:]  # Squash @
    line = line.replace("==", "=")  # Tolerate == syntax
    for operator in operators:
        if operator in line:
            name, value = line.split(operator, 1)
            valueOperator = operator
            try:
                value = int(value)
            except ValueError:
                raise YokadiException("Value of %s keyword must be an integer (got %s)" %
                                      (name, value))
            break
    else:
        # No operator found, only keyword name has been provided
        name = line

    return KeywordFilter(name, negative=negative, value=value, valueOperator=valueOperator)

# vi: ts=4 sw=4 et
