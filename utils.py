import re
from db import *


gSimplifySpaces = re.compile("  +")
def simplifySpaces(line):
    line = gSimplifySpaces.subn(" ", line)[0]
    line = line.strip()
    return line


gPropertyRe=re.compile("-p *([^ =]+)(?:=(\d+))?")
def extractProperties(line):
    """Parse line of form:
    some text -p property1 -p property2=12 some other text
    returns a tuple of ("some text some other text", {property1: None, property2:12})"""
    def fixPropertyValue(value):
        if value != '':
            return int(value)
        else:
            return None

    matches = gPropertyRe.findall(line)
    matches = [(x, fixPropertyValue(y)) for x,y in matches]
    propertyDict = dict(matches)

    line = gPropertyRe.subn("", line)[0]
    line = simplifySpaces(line)
    return line, propertyDict


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


def createMissingProperties(lst):
    """Create all properties from lst which does not exist
    Returns True, if ok, False if user canceled"""
    for propertyName in lst:
        if not getOrCreateProperty(propertyName):
            return False
    return True


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
