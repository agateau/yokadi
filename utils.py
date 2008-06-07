import re
from db import *


gSimplifySpaces = re.compile("  +")
def simplifySpaces(line):
    line = gSimplifySpaces.subn(" ", line)[0]
    line = line.strip()
    return line


def extractKeywords(line):
    def popToken():
        token = tokens[0].strip()
        del tokens[0]
        return token
    """Parse line of form:
    bla bla -k keyword1 -k keyword2 blob
    returns a tuple of ("bla bla blob", set(keyword1, keyword2,...))"""
    textParts = []
    keywordSet = set()
    tokens = line.split(" ")
    while len(tokens) > 0:
        token = popToken()
        if token == "-k":
            keyword = popToken()
            keywordSet.add(keyword)
        else:
            textParts.append(token)
    text = " ".join(textParts)
    return (text, keywordSet)


def getOrCreateKeyword(keywordName, interactive=True):
    """Returns keyword associated with keywordName, or prompt to create it if
    it does not exist. If user does not want to create it, returns None."""
    result = Keyword.selectBy(name=keywordName)
    result = list(result)
    if len(result):
        return result[0]

    while interactive:
        answer = raw_input("Keyword '%s' does not exist, create it (y/n)? " % keywordName)
        if answer == "n":
            return None
        if answer == "y":
            break
    keyword = Keyword(name=keywordName)
    print "Added keyword '%s'" % keywordName
    return keyword


def extractYagtdField(line, field):
    textParts = []
    regExp = re.compile(field + "([^ ]+)")
    lst = regExp.findall(line)
    if len(lst) == 1:
        field = lst[0]
    elif len(lst) == 0:
        field = None
    else:
        raise Exception("Multiple '%s' fields found" % field)

    line = regExp.subn("", line)[0]
    line = simplifySpaces(line)
    return line, field


# vi: ts=4 sw=4 et
