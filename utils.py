import re
from db import *


gSimplifySpaces = re.compile("  +")
def simplifySpaces(line):
    line = gSimplifySpaces.subn(" ", line)[0]
    line = line.strip()
    return line


def extractProperties(line):
    def popToken():
        token = tokens[0].strip()
        del tokens[0]
        return token
    """Parse line of form:
    bla bla -p property1 -p property2 blob
    returns a tuple of ("bla bla blob", set(property1, property2,...))"""
    textParts = []
    propertySet = set()
    tokens = line.split(" ")
    while len(tokens) > 0:
        token = popToken()
        if token == "-p":
            property = popToken()
            propertySet.add(property)
        else:
            textParts.append(token)
    text = " ".join(textParts)
    return (text, propertySet)


def getOrCreateProperty(propertyName, interactive=True):
    """Returns property associated with propertyName, or prompt to create it if
    it does not exist. If user does not want to create it, returns None."""
    result = Property.selectBy(name=propertyName)
    result = list(result)
    if len(result):
        return result[0]

    while interactive:
        answer = raw_input("Property '%s' does not exist, create it (y/n)? " % propertyName)
        if answer == "n":
            return None
        if answer == "y":
            break
    property = Property(name=propertyName)
    print "Added property '%s'" % propertyName
    return property


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
